"""Execute frontend template negative controls against isolated real-source copies.

Does not edit the checkout or run a browser. Logs and the receipt are written to
--out, which must not already exist. The runtime tests can have OS-only skips;
those are recorded, never reported as executed browser or native checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

FILES = (
    'geometry-app/application.js',
    'geometry-templates/woodworking/frontend.js',
    'geometry-web/app.js',
    'geometry-web/engineering-workspace.js',
    'geometry-web/section-profile-workspace.js',
    'geometry-web/grid-system-workspace.js',
    'geometry-web/feature-attachments.js',
    'geometry-web/source-plane.js',
    'geometry-web/reference-display.js',
    'geometry-web/evidence-links.js',
    'geometry-web/rule-case-data.js',
    'geometry-web/runtime_version.py',
    'tests/test_woodworking_frontend.js',
    'tests/test_grid_definition_diagram.js',
    'tests/test_runtime_version.py',
)
SUITES = {
    'recipes': (['node', '--test', 'tests/test_woodworking_frontend.js'], 15),
    'grid': (['node', '--test', 'tests/test_grid_definition_diagram.js'], 13),
    'runtime': ([sys.executable, 'tests/test_runtime_version.py'], 30),
}
MUTATIONS = (
    ('creation-bypasses-provider', 'recipes', 'geometry-web/engineering-workspace.js',
     'state.material=GeometryApplication.woodworking.materialDraft(type);',
     "state.material={type,width:'915',name:'矽酸鈣板'};",
     'actual material creation entry gets its suggestions'),
    ('placement-bypasses-policy', 'recipes', 'geometry-web/app.js',
     'return GeometryApplication.woodworking.primaryAxisInfo(fe.timbers || []);',
     "return {axis:null,conflict:false,src:'none'};",
     'actual host placement controls consume injected policies'),
    ('role-parses-display-text', 'grid', 'geometry-web/grid-system-workspace.js',
     "badge.dataset.role = role || 'sub';",
     "badge.dataset.role = badge.textContent === '主支線' ? 'main' : 'sub';",
     'grid role identity stays semantic even when presentation labels are exchanged'),
    ('runtime-omits-moved-source', 'runtime', 'geometry-web/runtime_version.py',
     "for directory in ('geometry-web', 'geometry-core', 'geometry-app', 'geometry-templates'):",
     "for directory in ('geometry-web', 'geometry-core'):",
     'test_template_native_and_host_source_changes_require_restart'),
    ('runtime-normalizes-public-template', 'runtime', 'geometry-web/runtime_version.py',
     '            or path in application_assets(root).values()\n', '',
     'test_served_template_checkout_line_endings_are_not_normalized'),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run_suite(root, name, out, stem):
    command, expected = SUITES[name]
    run = subprocess.run(command, cwd=root, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, timeout=90)
    text = run.stdout.decode('utf-8', errors='replace')
    log = out / (stem + '.log')
    log.write_bytes(run.stdout)
    if name == 'runtime':
        counts = re.search(r'Ran (\d+) tests?', text)
        error_count = sum(int(n) for n in re.findall(r'errors=(\d+)', text))
        fail_count = sum(int(n) for n in re.findall(r'failures=(\d+)', text))
        skipped = sum(int(n) for n in re.findall(r'skipped=(\d+)', text))
    else:
        counts = re.search(r'(?:#|ℹ) tests (\d+)', text)
        failures = re.search(r'(?:#|ℹ) fail (\d+)', text)
        skips = re.search(r'(?:#|ℹ) skipped (\d+)', text)
        error_count = 0
        fail_count = int(failures.group(1)) if failures else -1
        skipped = int(skips.group(1)) if skips else -1
    count = int(counts.group(1)) if counts else -1
    if count != expected:
        raise RuntimeError(f'{stem}: discovered {count}, expected {expected}; see {log}')
    return {'command': command, 'exit': run.returncode, 'discovered': count,
            'failures': fail_count, 'errors': error_count, 'skipped': skipped,
            'log': log.name, 'logSha256': sha(run.stdout)}, text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    original = {rel: (root / rel).read_bytes() for rel in FILES}
    receipt = {'schema': 'geo261-frontend-mutation/1', 'kind': 'isolated-source-controls',
               'sourceRoot': str(root), 'sourceHashes': {rel: sha(data) for rel, data in original.items()},
               'runnerSha256': sha(Path(__file__).read_bytes()), 'baselines': {}, 'mutations': []}
    try:
        with tempfile.TemporaryDirectory(prefix='geo261-frontend-') as temp:
            target = Path(temp)
            for rel, data in original.items():
                destination = target / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
            for suite in SUITES:
                result, _ = run_suite(target, suite, out, 'baseline-' + suite)
                receipt['baselines'][suite] = result
                if result['exit'] or result['failures'] or result['errors']:
                    raise RuntimeError(f'baseline {suite} did not pass')
            for name, suite, relative, before, after, failure_name in MUTATIONS:
                source = original[relative].replace(b'\r\n', b'\n').decode('utf-8')
                if source.count(before) != 1:
                    raise RuntimeError(f'{name}: expected one mutation anchor')
                path = target / relative
                try:
                    path.write_bytes(source.replace(before, after).encode('utf-8'))
                    # Avoid bytecode timestamps making a rapid same-size edit invisible.
                    for cache in target.rglob('__pycache__'):
                        shutil.rmtree(cache)
                    result, log = run_suite(target, suite, out, name)
                    result.update({'id': name, 'path': relative,
                                   'mutatedSha256': sha(path.read_bytes()),
                                   'before': before, 'after': after,
                                   'requiredFailure': failure_name})
                    result['detected'] = (result['exit'] == 1 and result['failures'] > 0
                                          and result['errors'] == 0 and failure_name in log)
                    receipt['mutations'].append(result)
                    if not result['detected']:
                        raise RuntimeError(f'{name}: missing named assertion failure')
                finally:
                    path.write_bytes(original[relative])
        receipt['tempRemoved'] = not target.exists()
    finally:
        receipt['sourceUnchanged'] = all((root / rel).read_bytes() == data for rel, data in original.items())
        (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not receipt['sourceUnchanged']:
        raise RuntimeError('checkout changed during mutation evidence capture')
    print(json.dumps({'baselines': len(receipt['baselines']), 'detected': len(receipt['mutations']),
                      'sourceUnchanged': True, 'receipt': str(out / 'receipt.json')}))


if __name__ == '__main__':
    main()
