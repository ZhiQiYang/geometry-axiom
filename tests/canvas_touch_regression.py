#!/usr/bin/env python3
"""R11 real-CDP red first and named withdrawal, without editing the checkout.

Each run gets a separate runtime source snapshot, feedback directory, native
server and Chrome profile. All browser assertions remain in canvas_touch_test.
The baseline is the exact pre-product commit plus the identical new test driver.
Then fixed / R11_WITHDRAW_TOUCH_REGISTRATION / restored must exit 0 / 1 / 0.
A startup failure, timeout, no CDP, different assertion or missing input proof
never counts as the required red. No generated golden or ledger is written.

  GEOMETRY_CHROME=/usr/bin/chromium GEOMETRY_CHROME_FLAGS=--no-sandbox \\
    python3 tests/canvas_touch_regression.py --out /tmp/r11-touch-proof

The output must be a new directory under TEMP. --binary-dir may point to a
TEMP native cache; the original registry still checks every receipt and byte.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = '11eddfdb4d7b1f76aedfe001e084a3840790bedc'
MUTANT = 'R11_WITHDRAW_TOUCH_REGISTRATION'
ANCHOR = b'window.CanvasTouchGestures.attach({'
REPLACEMENT = b'if (false) window.CanvasTouchGestures.attach({'
FAILURE = 'LONG_PRESS_OPENS_MENU'
DIRECTORIES = ('.github', 'geometry-app', 'geometry-core', 'geometry-kernel',
               'geometry-templates', 'geometry-web', 'geometry-guide', 'tests')
ROOT_FILES = ('current_geometry.c', '公理層.md')
OMIT = {'.git', '__pycache__', 'node_modules', 'evidence', 'release-evidence', 'prototypes'}
TEST_OVERLAY = ('geometry-web/cdp_test.js', 'geometry-web/canvas_touch_test.js')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def fingerprint(root):
    files = {}
    for directory, names, filenames in os.walk(root):
        names[:] = sorted(name for name in names if name not in OMIT)
        for filename in sorted(filenames):
            path = Path(directory) / filename
            if path.suffix == '.pyc':
                continue
            data = path.read_bytes()
            files[path.relative_to(root).as_posix()] = {'bytes': len(data), 'blob': blob(data), 'sha256': sha(data)}
    return files


def wanted(relative):
    return not any(part in OMIT for part in Path(relative).parts) and not relative.endswith('.pyc')


def candidate(target):
    target.mkdir()
    for name in DIRECTORIES:
        source = ROOT / name
        if source.is_dir():
            shutil.copytree(source, target / name, ignore=lambda _path, names: [name for name in names if name in OMIT or name.endswith('.pyc')])
    for path in ROOT.iterdir():
        if path.is_file() and (path.name in ROOT_FILES or path.suffix in {'.h', '.inc'}):
            shutil.copyfile(path, target / path.name)


def baseline(target, reference):
    target.mkdir()
    tree = subprocess.run(['git', 'ls-tree', '-rz', '--full-tree', reference], cwd=ROOT,
                          capture_output=True, check=True).stdout
    entries = []
    for entry in tree.split(b'\0'):
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        mode, kind, object_id = metadata.decode().split()
        name = raw_name.decode()
        if not wanted(name) or not (name.split('/')[0] in DIRECTORIES or name in ROOT_FILES
                                    or '/' not in name and Path(name).suffix in {'.h', '.inc'}):
            continue
        if kind != 'blob' or mode not in {'100644', '100755'}:
            raise RuntimeError('Unsupported source entry: ' + name)
        entries.append((name, object_id, mode))
    batch = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT,
                           input=''.join(oid+'\n' for _, oid, _ in entries).encode(), capture_output=True, check=True)
    stream = io.BytesIO(batch.stdout)
    for name, object_id, mode in entries:
        header = stream.readline().decode().strip().split()
        if len(header) != 3 or header[:2] != [object_id, 'blob']:
            raise RuntimeError('Exact baseline source unavailable: ' + name + ' ' + ' '.join(header))
        size = int(header[2]); data = stream.read(size)
        if len(data) != size or stream.read(1) != b'\n' or blob(data) != object_id:
            raise RuntimeError('Invalid baseline object bytes: ' + name)
        path = target / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data); path.chmod(int(mode, 8) & 0o777)
    # T only: identical harness/early observer, all product files stay at BASE.
    for name in TEST_OVERLAY:
        (target / name).write_bytes((ROOT / name).read_bytes())


def unused_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def tagged(stdout, tag):
    result = []
    for line in stdout.splitlines():
        if line.startswith(tag + ' '):
            result.append(json.loads(line[len(tag)+1:]))
    return result


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def environment(feedback):
    allowed = {'GEOMETRY_CHROME', 'GEOMETRY_CHROME_FLAGS'}
    env = {name: value for name, value in os.environ.items() if not name.startswith('GEOMETRY_') or name in allowed}
    env['GEOMETRY_FEEDBACK_DIR'] = str(feedback)
    return env


def stop_owned(process):
    """Terminate only the fresh session created by this runner, including Chrome."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def run(label, root, output, binaries):
    output.mkdir(); feedback = output / 'feedback'; feedback.mkdir()
    env = environment(feedback)
    before = fingerprint(root); save(output / 'source-before.json', before)
    started = time.monotonic()
    report = {'label': label, 'root': str(root), 'runtime': None, 'status': 'infra', 'exit': None}
    server = None; reader = None
    try:
        build = subprocess.Popen([sys.executable, 'geometry-web/start_local.py', '--build-only', '--binary-dir', str(binaries)],
                                 cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            build_stdout, build_stderr = build.communicate(timeout=300)
        except subprocess.TimeoutExpired:
            stop_owned(build)
            build_stdout, build_stderr = build.communicate()
            (output / 'build.stdout').write_bytes(build_stdout); (output / 'build.stderr').write_bytes(build_stderr)
            raise RuntimeError('Native build exceeded its 300 s regression budget; not a product assertion red')
        finally:
            stop_owned(build)
        (output / 'build.stdout').write_bytes(build_stdout); (output / 'build.stderr').write_bytes(build_stderr)
        require(build.returncode == 0, 'Original native registry/build did not complete: ' + str(build.returncode))
        port, cdp_port = unused_port(), unused_port()
        require(port != cdp_port, 'Service/CDP port collision; no existing process was touched')
        env.update(GEOMETRY_TEST_URL=f'http://127.0.0.1:{port}/', GEOMETRY_CDP_PORT=str(cdp_port), GEOMETRY_CANVAS_TOUCH_ONLY='1')
        server = subprocess.Popen([sys.executable, '-u', 'geometry-web/start_local.py', '--port', str(port), '--binary-dir', str(binaries)],
                                  cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        ready = threading.Event(); startup = {'ready': False}

        def drain():
            with (output / 'server.log').open('wb') as log:
                for line in iter(server.stdout.readline, b''):
                    log.write(line); log.flush()
                    if f'http://localhost:{port}'.encode() in line:
                        startup['ready'] = True; ready.set()
            ready.set()

        reader = threading.Thread(target=drain, daemon=True); reader.start()
        require(ready.wait(30) and startup['ready'], 'Isolated server did not report readiness')
        spec = importlib.util.spec_from_file_location('canvas_touch_runtime', root / 'geometry-web/runtime_version.py')
        runtime = importlib.util.module_from_spec(spec); spec.loader.exec_module(runtime)
        report['runtime'] = runtime.probe(port, root)
        process = subprocess.Popen(['node', 'geometry-web/cdp_test.js'], cwd=root, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            raw_stdout, raw_stderr = process.communicate(timeout=300)
        except subprocess.TimeoutExpired:
            stop_owned(process)
            raw_stdout, raw_stderr = process.communicate()
            (output / 'stdout.log').write_bytes(raw_stdout); (output / 'stderr.log').write_bytes(raw_stderr)
            raise RuntimeError('CDP exceeded its 300 s regression budget; not a product assertion red')
        finally:
            stop_owned(process)
        (output / 'stdout.log').write_bytes(raw_stdout); (output / 'stderr.log').write_bytes(raw_stderr)
        stdout = raw_stdout.decode('utf-8', errors='replace')
        report.update(exit=process.returncode, cases=tagged(stdout, 'P1162_CASE_RESULT'),
                      touch=tagged(stdout, 'P1162_RESULT'), cdp=tagged(stdout, 'CDP_RESULT'),
                      failed=[line for line in stdout.splitlines() if line.startswith('P1162 ') and ' ✗ ' in line],
                      fatal=[line for line in stdout.splitlines() if line.startswith('FATAL:')])
        # Reaching a named failed assertion is required. Infrastructure cannot
        # become a successful withdrawal just because its process was nonzero.
        require(not report['fatal'] and len(report['cdp']) == 1 and len(report['touch']) == 1,
                'No complete real CDP result; infrastructure/crash is not regression red')
        result, touch = report['cdp'][0], report['touch'][0]
        require(result.get('completed') is True and result.get('unexpectedBrowserExceptions') == 0,
                'CDP did not complete cleanly through its original result path')
        require(result.get('scope', {}).get('mode') == 'partial' and result['scope'].get('filters') == ['GEOMETRY_CANVAS_TOUCH_ONLY'],
                'Unexpected CDP scope')
        require(result.get('goldenCompare') == 'not compared (partial mode)', 'Unexpected golden operation')
        require(touch.get('input') == 'Input.dispatchTouchEvent' and touch.get('scope') == 'object-canvas', 'Missing touch scope proof')
        report['status'] = 'assertions'
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
    finally:
        if server is not None:
            stop_owned(server)
        if reader is not None:
            reader.join(timeout=10)
        after = fingerprint(root); save(output / 'source-after.json', after)
        if before != after:
            report['status'] = 'infra'; report['error'] = 'Runtime/harness source changed during this run'
        report['seconds'] = round(time.monotonic()-started, 3)
        save(output / 'result.json', report)
        print('R11_TOUCH_RUN ' + json.dumps({key: report.get(key) for key in ('label','status','exit','seconds','error')}, ensure_ascii=False), flush=True)
    return report


def green(row):
    if row['status'] != 'assertions':
        return False
    cdp, touch = row['cdp'][0], row['touch'][0]
    return (row['exit'] == 0 and cdp.get('failedAssertions') == 0 and not row['failed']
            and touch.get('completed') is True and touch.get('failed') == []
            and touch.get('passed') == touch.get('expectedCases') and len(touch.get('passed', [])) == 16
            and set(cdp.get('sections', {})) == {'P1162'} and cdp['sections']['P1162'] > 0)


def red(row):
    if row['status'] != 'assertions':
        return False
    cdp, touch = row['cdp'][0], row['touch'][0]
    failed = touch.get('firstFailure') or {}
    events = failed.get('detail', {}).get('state', {}).get('events', [])
    return (row['exit'] == 1 and cdp.get('failedAssertions') == 1
            and len(row['failed']) == 1 and row['failed'][0].startswith('P1162 '+FAILURE+' ✗')
            and failed.get('assertion') == FAILURE and failed.get('kind') == 'assertion'
            and any(event.get('type') == 'pointerdown' and event.get('pointerType') == 'touch' and event.get('trusted') is True for event in events)
            and any(event.get('type') == 'touchstart' and event.get('trusted') is True for event in events)
            and touch.get('failed') == ['LONG_PRESS'] and touch.get('completed') is False
            and cdp.get('sectionsFailed') == {'P1162': 1})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--before-base', default=BASE)
    parser.add_argument('--binary-dir', type=Path)
    args = parser.parse_args()
    out = args.out.resolve(); temp = Path(tempfile.gettempdir()).resolve()
    require(temp in out.parents and not out.exists() and ROOT not in out.parents, '--out must be a new directory under TEMP, outside the repository')
    require(len(args.before_base) == 40 and all(c in '0123456789abcdef' for c in args.before_base), '--before-base requires a full commit SHA')
    binaries = (args.binary_dir or out / 'binaries').resolve()
    require(temp in binaries.parents and ROOT not in binaries.parents, '--binary-dir must be under TEMP, outside the repository')
    out.mkdir(parents=True)
    original = fingerprint(ROOT / 'geometry-web')
    report = {'schema': 'geometry-r11-touch-withdrawal/1', 'base': args.before_base, 'mutant': MUTANT,
              'requiredFirstFailure': FAILURE, 'status': 'blocked', 'runs': [], 'problems': []}
    save(out / 'checkout-web-before.json', original)
    try:
        roots = {name: out / ('source-'+name) for name in ('baseline','fixed-before','withdrawn','fixed-after')}
        baseline(roots['baseline'], args.before_base)
        for name in ('fixed-before','withdrawn','fixed-after'):
            candidate(roots[name])
        app = roots['withdrawn'] / 'geometry-web/app.js'; data = app.read_bytes()
        require(data.count(ANCHOR) == 1, 'Named withdrawal requires exactly one touch registration anchor')
        app.write_bytes(data.replace(ANCHOR, REPLACEMENT, 1))
        report['withdrawal'] = {'path': 'geometry-web/app.js', 'anchor': ANCHOR.decode(), 'replacement': REPLACEMENT.decode(),
                                'before': {'bytes':len(data),'blob':blob(data),'sha256':sha(data)},
                                'after': {'bytes':app.stat().st_size,'blob':blob(app.read_bytes()),'sha256':sha(app.read_bytes())}}
        for name in ('baseline','fixed-before','withdrawn','fixed-after'):
            row = run(name, roots[name], out / ('run-'+name), binaries); report['runs'].append(row)
            # Infrastructure blocks the experiment. Do not keep retrying Chrome.
            if row['status'] != 'assertions':
                report['problems'].append(name+' is infrastructure, not a product assertion result'); break
        rows = report['runs']
        if len(rows) == 4 and red(rows[0]) and green(rows[1]) and red(rows[2]) and green(rows[3]):
            report['status'] = 'pass'; report['sequence'] = [row['exit'] for row in rows]
        else:
            report['problems'].append('Required baseline red and fixed/withdrawn/restored 0/1/0 are not all proven')
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        report['problems'].append(str(error))
    finally:
        after = fingerprint(ROOT / 'geometry-web'); save(out / 'checkout-web-after.json', after)
        if after != original:
            report['status'] = 'blocked'; report['problems'].append('Source checkout changed during the proof')
        save(out / 'summary.json', report)
    print('R11_TOUCH_REGRESSION ' + json.dumps({key:report.get(key) for key in ('status','base','mutant','sequence','problems')}, ensure_ascii=False))
    if report['status'] == 'pass':
        return 0
    return 2 if any(row.get('status') == 'infra' for row in report['runs']) or not report['runs'] else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print('R11_TOUCH_REGRESSION_SETUP ' + str(error), file=sys.stderr)
        sys.exit(2)
