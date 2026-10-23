#!/usr/bin/env python3
"""只包裝真實 argv 的外部證據紀錄器；不套 patch、建分支或判定測試紅綠。"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import resource
import shutil
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
SAFE_ENV = (
    'PATH', 'CC', 'CXX', 'CFLAGS', 'CXXFLAGS', 'LDFLAGS', 'LANG', 'LC_ALL', 'TZ',
    'TMPDIR', 'PYTHONUTF8', 'PYTHONIOENCODING', 'PYTHONUNBUFFERED', 'PYTHONOPTIMIZE',
    'PYTHONDONTWRITEBYTECODE', 'MUTATE_RESULTS', 'MUTATE_CACHE',
    'GEOMETRY_TEST_CORE', 'GEOMETRY_TEST_BRIDGE', 'GEOMETRY_ENGINEERING_BRIDGE',
    'GEOMETRY_MODEL_BASE', 'GEOMETRY_TEST_PF3_ALGORITHM', 'GEOMETRY_TEST_ENGINEERING_JSON',
)
SOURCE_SUFFIXES = {'.c', '.h', '.inc', '.py', '.js', '.mjs', '.cjs', '.json',
                   '.scene', '.html', '.css', '.yml', '.yaml', '.sh', '.bat', '.md'}
EXCLUDED_PARTS = {'.codex', 'feedback', '.git', 'node_modules', '__pycache__'}
DEFAULT_BINARY_NAMES = ('core', 'bridge', 'model-base')


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def identity(st):
    return dict(device=st.st_dev, inode=st.st_ino, bytes=st.st_size,
                mtime_ns=st.st_mtime_ns, ctime_ns=st.st_ctime_ns)


def read_stable(path):
    """原始 bytes，不正規化 CRLF；拒絕讀取期間被替換的檔案。"""
    before = identity(path.stat())
    data = path.read_bytes()
    after = identity(path.stat())
    if before != after or len(data) != before['bytes']:
        raise RuntimeError('讀取期間檔案改變：' + str(path))
    return data, dict(after, sha256=sha(data))


def file_info(path):
    if not path.exists():
        return {'exists': False}
    _, info = read_stable(path)
    return dict(info, exists=True)


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.PIPE)


def repo_snapshot(root, output, label, extra_sources):
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    scope = ['--', '.', ':(exclude).codex', ':(exclude)feedback']
    status = git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all', *scope)
    diff = git(root, 'diff', '--no-ext-diff', '--binary', 'HEAD', *scope)
    (output / (label + '.status.raw')).write_bytes(status)
    (output / (label + '.diff.patch')).write_bytes(diff)
    paths = git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z', *scope)
    names = {os.fsdecode(item) for item in paths.split(b'\0') if item}
    names = {name for name in names if not (set(Path(name).parts) & EXCLUDED_PARTS)
             and Path(name).suffix in SOURCE_SUFFIXES
             and name != 'tests/mutants_results.json' and not name.startswith('tests/evidence/')}
    for name in extra_sources:
        path = (root / name).resolve()
        if not path.is_relative_to(root) or set(path.relative_to(root).parts) & EXCLUDED_PARTS:
            raise ValueError('--source 必須位於 checkout 內且不屬受排除目錄：' + name)
        names.add(path.relative_to(root).as_posix())
    files = {}
    for name in sorted(names):
        path = root / name
        if path.is_symlink():
            # 不跟隨 checkout 外的 symlink；儲存 link 原文的雜湊。
            target = os.fsencode(os.readlink(path))
            files[name] = dict(kind='symlink', sha256=sha(target), bytes=len(target))
        elif path.is_file():
            files[name] = file_info(path)
        else:
            files[name] = {'exists': False}
    content = {name: {key: value[key] for key in ('sha256', 'bytes', 'exists', 'kind') if key in value}
               for name, value in files.items()}
    aggregate = sha(json.dumps(content, ensure_ascii=True, sort_keys=True).encode())
    result = dict(head=head, branch=git(root, 'branch', '--show-current').decode().strip(),
                  status_sha256=sha(status), diff_sha256=sha(diff), source_bytes_sha256=aggregate,
                  source_files=files, captured_utc=utc(),
                  scope_note='tracked+未忽略 source 副檔名；排除 .codex/feedback、ledger、tests/evidence；這不是 mutation closure 演算法')
    write_json(output / (label + '.source.json'), result)
    return result


def load_binaries(root):
    spec = importlib.util.spec_from_file_location('geo261_evidence_binaries', root / 'tests/binaries.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def binary_snapshot(module, output, label, names, paths):
    receipts = []
    for name in names:
        item = module.BY_NAME[name]
        info = module.inspect_one(item)
        receipts.append(dict(kind='registry', name=name, path=str(info.path),
                             inspection=info.as_dict(), source_fingerprint=info.fingerprint))
    receipts.extend(dict(kind='explicit-persistent', path=str(path.resolve())) for path in paths)
    for index, row in enumerate(receipts):
        path = Path(row['path'])
        row['binary'] = file_info(path)
        sidecar = path.with_name(path.name + module.SIDECAR_SUFFIX)
        row['sidecar'] = file_info(sidecar)
        if sidecar.exists():
            data, _ = read_stable(sidecar)
            copy_name = '%s.binary-%02d.sidecar.json' % (label, index)
            (output / copy_name).write_bytes(data)
            row['sidecar_copy'] = copy_name
    result = dict(receipts=receipts, captured_utc=utc(),
                  coverage='僅前後可讀的持久 binary；不宣稱含 child 已清除的 transient mutant binary')
    write_json(output / (label + '.binaries.json'), result)
    return result


def selected_run_all_logs(root, command, explicit_suites):
    candidates = [arg for arg in command if arg.endswith('run_all.py')]
    is_run_all = any((root / arg).resolve() == root / 'tests/run_all.py' for arg in candidates)
    if not is_run_all:
        if explicit_suites:
            raise ValueError('--suite 只能搭配 tests/run_all.py')
        return {}
    only = []
    for index, arg in enumerate(command):
        if arg == '--only':
            only.append(command[index + 1])
        elif arg.startswith('--only='):
            only.append(arg.split('=', 1)[1])
    registry = json.loads((root / 'tests/run_all.expected.json').read_bytes())['suites']
    suites = sorted(name for name in registry if not only or any(part in name for part in only))
    if explicit_suites and set(explicit_suites) != set(suites):
        raise ValueError('--suite 與目前 --only/expected 登錄推得的範圍不同；先審查新登錄')
    if not suites:
        raise ValueError('找不到所選 suite；不採用舊 log')
    log_dir = Path('/tmp/geometry-tests/run_all-logs')
    paths = {}
    for name in suites:
        suffixes = ('.log', '.unittest.log', '.json') if name.startswith('py:') else ('.log',)
        for suffix in suffixes:
            path = log_dir / (name.replace(':', '_') + suffix)
            paths[str(path)] = dict(suite=name, before=file_info(path))
    return paths


def tool_versions(root, output):
    # Chrome 以已驗證的獨立安裝執行，不要求寫入系統 PATH。
    chrome = os.environ.get('GEOMETRY_CHROME') or shutil.which('google-chrome')
    if not chrome:
        installed = Path('/workspace/geo261-tools/google-chrome-155.0.8059.84/opt/google/chrome/google-chrome')
        if installed.is_file():
            chrome = str(installed)
    probes = [('gcc', ['gcc', '--version']), ('python', [sys.executable, '--version']),
              ('node', ['node', '--version']), ('chrome', [chrome or 'google-chrome', '--version']),
              ('chromium', ['chromium', '--version'])]
    found = {}
    for name, command in probes:
        if not shutil.which(command[0]):
            found[name] = {'available': False}
            continue
        try:
            result = subprocess.run(command, cwd=root, capture_output=True, timeout=10, check=False)
            for suffix, data in (('stdout', result.stdout), ('stderr', result.stderr)):
                (output / ('tool-' + name + '.' + suffix)).write_bytes(data)
            found[name] = dict(command=command, returncode=result.returncode,
                               executable=str(Path(shutil.which(command[0])).resolve()))
        except (OSError, subprocess.TimeoutExpired) as error:
            found[name] = {'error': str(error)}
    return found


def execute(root, output, command, timeout):
    process = None
    record = dict(argv=command, shell=False, cwd=str(root), started_utc=utc(),
                  started_ns=time.time_ns(), timeout_seconds=timeout, timed_out=False,
                  interrupted=False, returncode=None, launch_error=None)
    clock = time.monotonic()
    with (output / 'command.stdout').open('xb') as stdout, (output / 'command.stderr').open('xb') as stderr:
        try:
            process = subprocess.Popen(command, cwd=root, stdout=stdout, stderr=stderr,
                                       start_new_session=True)
            record['pid'] = process.pid
            process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            record['timed_out'] = isinstance(error, subprocess.TimeoutExpired)
            record['interrupted'] = not record['timed_out']
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=20)
        except OSError as error:
            record['launch_error'] = repr(error)
        finally:
            record.update(ended_utc=utc(), ended_ns=time.time_ns(), seconds=time.monotonic() - clock,
                          returncode=process.returncode if process is not None else None)
    record['streams'] = {suffix: file_info(output / ('command.' + suffix)) for suffix in ('stdout', 'stderr')}
    write_json(output / 'command.process.json', record)
    return record


def collect_logs(output, planned, process):
    results = []
    observed_stdout = (output / 'command.stdout').read_bytes().decode('utf-8', errors='replace')
    target = output / 'suite-logs'
    target.mkdir()
    for name, expected in planned.items():
        path = Path(name)
        item = dict(path=name, suite=expected['suite'], before=expected['before'], copied=False)
        try:
            item['after'] = file_info(path)
            announced = bool(re.search(r'^\[\d+/\d+\] ' + re.escape(expected['suite']) + r' …\s*$', observed_stdout, re.M))
            item['own_stdout_announced_suite'] = announced
            if not item['after'].get('exists'):
                item['reason'] = '本次未產生檔案'
            elif not (process['started_ns'] <= item['after']['mtime_ns'] <= process['ended_ns']):
                item['reason'] = 'mtime 不在本次 child 起迄內；拒用前次／後次檔案'
            elif item['before'] == item['after']:
                item['reason'] = '與執行前完全相同；拒用舊檔'
            elif not announced:
                item['reason'] = '本命令 stdout 未宣告執行此 suite；拒用其他 invocation 的收據'
            else:
                data, stable = read_stable(path)
                if stable != {key: value for key, value in item['after'].items() if key != 'exists'}:
                    raise RuntimeError('複製前 log 身分已變')
                with (target / path.name).open('xb') as saved:
                    saved.write(data)
                item.update(copied=True, copy=str(Path('suite-logs') / path.name))
                if path.suffix == '.json':
                    try:
                        result = json.loads(data)
                        item['reported_fields_only'] = {key: result[key] for key in (
                            'total', 'run', 'passed', 'failed', 'skipped', 'blocked_by_error',
                            'import_error', 'extra_errors', 'expected_failed') if key in result}
                    except (ValueError, TypeError):
                        item['parse_note'] = '原始 JSON 無法解析；未加工仍完整保存'
        except (OSError, RuntimeError) as error:
            item['reason'] = repr(error)
        results.append(item)
    write_json(output / 'suite-logs.manifest.json', results)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', required=True, type=Path)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--stage', required=True)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--timeout', type=float, default=7200)
    parser.add_argument('--stack-kib', type=int, default=16384)
    parser.add_argument('--source', action='append', default=[])
    parser.add_argument('--suite', action='append', default=[])
    parser.add_argument('--registry-binary', action='append')
    parser.add_argument('--binary', action='append', type=Path, default=[])
    parser.add_argument('--artifact', action='append', type=Path, default=[])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or args.timeout <= 0:
        parser.error('請以 -- 後提供完整 argv，且 timeout > 0')
    root, output = args.checkout.resolve(), args.out.resolve()
    if output.is_relative_to(root):
        parser.error('--out 必須在 checkout 外且不存在')
    if not re.fullmatch(r'[0-9a-f]{40}', args.expected_head):
        parser.error('--expected-head 必須為完整 40 位 SHA')
    # mkdir 原子拒絕既有 stage；任何失敗都不清空、不覆寫舊證據。
    output.mkdir(parents=True, exist_ok=False)
    record = dict(stage=args.stage, checkout=str(root), recorder_started_utc=utc(),
                  expected_head=args.expected_head, invocation=sys.argv,
                  helper_sha256=sha(Path(__file__).read_bytes()),
                  status='擷取尚未完成', test_verdict='未判定；必須依原始 suite／具名 assertion 人工核對',
                  environment={name: os.environ[name] for name in SAFE_ENV if name in os.environ},
                  environment_scope='只存固定非機密白名單；child 繼承原環境，未注入 hook 或改寫 PYTHONPATH',
                  platform=platform.platform(), python=sys.version,
                  limitations=['未擷取已清除 transient native mutant binary；持久 binary hash 不冒充其身分',
                              '外部流程必須串行；mtime+本命令 stdout 宣告排除舊檔，但不是完整跨行程 provenance 系統',
                              'timeout／compile error／import error／crash／setup error 都不能當有效 mutation kill'])
    result_code = 125
    def stop(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    try:
        (output / 'recorder.py').write_bytes(Path(__file__).read_bytes())
        before = repo_snapshot(root, output, 'before', args.source)
        if before['head'] != args.expected_head:
            raise RuntimeError('目前 HEAD 不等於 expected-head；未執行命令')
        executable = ((root / command[0]).resolve() if '/' in command[0]
                      else Path(shutil.which(command[0]) or command[0]).resolve())
        record['command_executable'] = dict(path=str(executable), identity=file_info(executable))
        record['tools'] = tool_versions(root, output)
        module = load_binaries(root)
        names = args.registry_binary if args.registry_binary is not None else list(DEFAULT_BINARY_NAMES)
        binary_paths = [(root / path).resolve() for path in args.binary]
        binary_snapshot(module, output, 'before', names, binary_paths)
        planned = selected_run_all_logs(root, command, args.suite)
        artifacts = {str((root / path).resolve()): file_info((root / path).resolve()) for path in args.artifact}
        soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
        record['stack_before_bytes'] = dict(soft=soft, hard=hard)
        resource.setrlimit(resource.RLIMIT_STACK, (args.stack_kib * 1024, hard))
        record['stack_child_bytes'] = resource.getrlimit(resource.RLIMIT_STACK)[0]
        process = execute(root, output, command, args.timeout)
        record['process'] = process
        logs = collect_logs(output, planned, process)
        record['run_all_logs_complete'] = all(item['copied'] for item in logs) if planned else None
        collected = []
        for index, (name, previous) in enumerate(artifacts.items()):
            path = Path(name)
            item = dict(path=name, before=previous, after=file_info(path), copied=False)
            if item['after'].get('exists'):
                data, stable = read_stable(path)
                copy = 'artifact-%02d-%s' % (index, path.name)
                with (output / copy).open('xb') as stream:
                    stream.write(data)
                item.update(copy=copy, copied=True, captured=stable,
                            changed=previous != item['after'],
                            note='原始外部 artifact；是否 fresh receipt 必須由其正式 checker 判定')
            collected.append(item)
        record['artifacts'] = collected
        binary_snapshot(module, output, 'after', names, binary_paths)
        after = repo_snapshot(root, output, 'after', args.source)
        record['source_stable'] = before['source_bytes_sha256'] == after['source_bytes_sha256']
        record['head_stable'] = before['head'] == after['head']
        record['status_and_diff_stable'] = all(before[key] == after[key] for key in ('status_sha256', 'diff_sha256'))
        record['status'] = '擷取完成；不代表測試通過或突變有效'
        result_code = process['returncode']
        if process['timed_out']:
            result_code = 124
        elif process['interrupted']:
            result_code = 130
        elif result_code is None:
            result_code = 125
        elif result_code < 0:
            result_code = 128 - result_code
        if not record['source_stable'] or not record['head_stable'] or (planned and not record['run_all_logs_complete']):
            record['status'] = '擷取有缺項或執行期間來源改變；不可作完成驗證證據'
            result_code = 125
    except (Exception, KeyboardInterrupt) as error:
        record['status'] = '擷取受阻或中斷；不得當作 mutation red'
        record['recorder_error'] = type(error).__name__ + ': ' + str(error)
        result_code = 130 if isinstance(error, KeyboardInterrupt) else 125
    finally:
        record['recorder_ended_utc'] = utc()
        record['recorder_exit_code'] = result_code
        record['evidence_files'] = {path.relative_to(output).as_posix(): file_info(path)
                                    for path in sorted(output.rglob('*')) if path.is_file()}
        write_json(output / 'receipt.json', record)
        print(json.dumps(dict(stage=args.stage, status=record['status'], output=str(output),
                              recorder_exit_code=result_code), ensure_ascii=False))
    return result_code


if __name__ == '__main__':
    raise SystemExit(main())
