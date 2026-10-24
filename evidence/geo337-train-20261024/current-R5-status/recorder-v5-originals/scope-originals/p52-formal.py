#!/usr/bin/env python3
"""在新受驗 SHA 綁定原 P52 正式 body；原四區塊、五控制與判官 AST 不變。"""
from __future__ import annotations

import argparse
import ast
import datetime
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import resource
import shutil
import subprocess
import sys
import time
import traceback
import types

from runtime_inventory import complete_runtime_inventory, same_runtime_identity

MAIN = 'adbaebf9c73ea6801d7b4d5214e4b846b132923b'
CAPTURE = 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
REAPER = '7d848d6c135b7f329852d16c6da5743effde8b29ccbbc6e70092b6ba25877760'
PROTOCOL = {
    'postfix_validate.py': 'b9fbcca0eb12e2e25fb5d84eda01038bf8406d1c3a533fa5dfd842e330cf8c5f',
    'p52_measure.py': '738a36b0417e7f5cfa1dcf57fc0d14664650b8285484f866b8ceb0d3a2c8f1a4',
    'p52_probe.cjs': '8c3b4b14ad35082679e4faf229bd66d65a500bd53669c13d8f41e0603e066970',
    'p52_cases.cjs': '6ca75996223e94be0a503e646d58ed928b046854eb0102af309482dc4ac60f66',
}
SAFE = ('PATH', 'LANG', 'LC_ALL', 'TMPDIR', 'GITHUB_SHA', 'GITHUB_WORKSPACE',
        'PYTHONDONTWRITEBYTECODE', 'PYTHONIOENCODING', 'GEOMETRY_FEEDBACK_DIR',
        'GEOMETRY_TEST_URL', 'GEOMETRY_CHROME', 'GEOMETRY_CHROME_FLAGS',
        'GEOMETRY_CDP_PORT', 'GEOMETRY_CDP_FROM_P31', 'GEOMETRY_CHROME_PROFILE',
        'P52_OUT', 'P52_SHA', 'P52_CASE_MODE', 'P52_REPS', 'GEO261_REAPER_LOG',
        'CC', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS')


def h(raw):
    return hashlib.sha256(raw).hexdigest()


def need(condition, message):
    if not condition:
        raise RuntimeError(message)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'main-repo', 'out', 'heavy-lock'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--sha', required=True)
    p.add_argument('--protocol-dir', type=Path,
                   default=Path(__file__).resolve().parent / 'protocol')
    p.add_argument('--capture', type=Path,
                   default=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py'))
    p.add_argument('--reaper', type=Path,
                   default=Path('/workspace/geo261-environment/reap_children.py'))
    a = p.parse_args()
    repo, main_repo, out = a.repo.resolve(), a.main_repo.resolve(), a.out.resolve()
    need(len(a.sha) == 40 and all(c in '0123456789abcdef' for c in a.sha), '須提供完整 SHA')
    need(a.sha != MAIN and not sys.flags.optimize and os.environ.get('PYTHONOPTIMIZE') in (None, '', '0'),
         '禁止把 main 當 fix，且不得啟用 optimize')
    need(repo.is_dir() and main_repo.is_dir() and main_repo.name == 'main',
         '需要既有來源與 basename 為 main 的固定比較樹')
    need(repo != main_repo and not out.exists() and out.parent.is_dir(), '來源須獨立，out 須全新且父目錄存在')
    need(out.is_relative_to(Path('/tmp')) and not out.is_relative_to(repo) and not out.is_relative_to(main_repo),
         'out 須位於 /tmp 並在兩來源之外')
    need(not repo.is_relative_to(out) and not main_repo.is_relative_to(out), '來源不可位於 out 之內')
    need(a.heavy_lock.is_file(), '須沿用既有共用 heavy lock，不另開一把鎖')
    need(h(a.capture.read_bytes()) == CAPTURE and h(a.reaper.read_bytes()) == REAPER, '原 recorder/reaper hash 不符')
    runtime_helper = Path(__file__).resolve().parent / 'runtime_inventory.py'
    need(Path(complete_runtime_inventory.__code__.co_filename).resolve() == runtime_helper,
         'runtime inventory helper 必須來自同一工具目錄')
    for name, digest in PROTOCOL.items():
        need(h((a.protocol_dir / name).read_bytes()) == digest, '原 protocol bytes 不符：' + name)
    out.mkdir()
    tools = out / 'tools'
    protocol = tools / 'protocol'
    protocol.mkdir(parents=True)
    (out / 'work' / 'tmp').mkdir(parents=True)
    frozen = {}
    for path in [Path(__file__).resolve(), runtime_helper, a.capture.resolve(), a.reaper.resolve(),
                 *[a.protocol_dir.resolve() / name for name in PROTOCOL]]:
        raw = path.read_bytes()
        target = protocol / path.name if path.name in PROTOCOL else tools / path.name
        need(not target.exists(), '工具 snapshot 撞名')
        target.write_bytes(raw)
        frozen[str(path)] = {'sha256': h(raw), 'snapshot': str(target)}
    spec = importlib.util.spec_from_file_location('p52_formal_capture', tools / a.capture.name)
    capture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(capture)
    env = dict(os.environ)
    cleared = []
    for key in list(env):
        if key.startswith(('GEOMETRY_', 'P52_')) or key in ('PYTHONOPTIMIZE', 'PYTHONPATH', 'PYTHONSTARTUP', 'NODE_OPTIONS', 'LD_PRELOAD'):
            cleared.append(key)
            env.pop(key)
    env.update(PATH='/workspace/geo261-environment/bin:/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
               LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1',
               TMPDIR=str(out / 'work' / 'tmp'), GITHUB_SHA=a.sha, GITHUB_WORKSPACE=str(repo))
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    need(hard == resource.RLIM_INFINITY or hard >= 16384 * 1024, 'stack hard limit 不足 16 MiB')
    resource.setrlimit(resource.RLIMIT_STACK, (16384 * 1024, hard))
    recorder = capture.Recorder(out, env, a.sha)
    servers, server_processes, node_commands, guards, errors = [], [], [], [], []
    report = {'schema': 'geo261-main-merge-P52-formal-binding/1', 'sha': a.sha, 'main': MAIN,
              'repo': str(repo), 'main_repo': str(main_repo),
              'scope': '原 postfix_validate.one 與 main 從 records=[] 到原 SystemExit 的完整 AST；只替換已預備 checkout 與輸出綁定',
              'original_hardcoded_clone_preamble_executed': False,
              'prepared_checkout_binding': {'fix': str(repo), 'main': str(main_repo)},
              'original_protocol': PROTOCOL, 'tool_hashes': frozen,
              'environment': {k: env.get(k) for k in SAFE}, 'cleared_environment_names': sorted(cleared),
              'platform': platform.platform(), 'python': sys.version, 'python_executable': sys.executable,
              'stack_before': [soft, hard], 'stack_during': [16384 * 1024, hard],
              'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'servers': servers, 'node_commands': node_commands, 'guards': guards, 'errors': errors,
              'original_body_system_exit': None, 'original_body_completed': False, 'passed': False}

    def run(argv, *, cwd=repo, child_env=None, timeout=1200, check=True, source_sha=None, variant=None):
        child_env = env if child_env is None else child_env
        old_env = recorder.env
        recorder.env = child_env
        try:
            row, stdout, stderr = recorder.run(list(map(str, argv)), cwd=cwd, timeout=timeout, check=check,
                                              source_sha=source_sha or child_env.get('P52_SHA', a.sha),
                                              source_variant=variant or ('main-reference' if child_env.get('P52_SHA') == MAIN else 'fixed-final-source'))
            row['effective_environment'] = {k: child_env.get(k) for k in SAFE}
            return row, stdout, stderr
        finally:
            recorder.env = old_env

    def git(path, *parts):
        return run(['git', *parts], cwd=path, timeout=120,
                   source_sha=MAIN if path == main_repo else a.sha, variant='source-integrity')[1]

    def guard(path, label, sha):
        head = git(path, 'rev-parse', 'HEAD').decode().strip()
        status = git(path, 'status', '--porcelain=v1', '--untracked-files=all').decode()
        staged = git(path, 'diff', '--cached', '--name-only')
        diff = git(path, 'diff', '--binary', '--full-index', '--no-ext-diff', '--no-color', 'HEAD')
        index = git(path, 'ls-files', '--stage', '-z')
        (out / (label + '.patch')).write_bytes(diff)
        row = {'label': label, 'path': str(path), 'head': head, 'status': status,
               'diff_sha256': h(diff), 'tree_index_sha256': h(index)}
        guards.append(row)
        need(head == sha and status == '' and staged == b'' and diff == b'', label + '：來源不是指定乾淨 SHA')
        inventory = complete_runtime_inventory(path, sha, lambda *parts: git(path, *parts))
        inventory_path = out / (label + '-runtime-inputs.json')
        save(inventory_path, inventory)
        identities = [(entry['path'], entry['runtime_identity_sha256']) for entry in inventory['inputs']]
        row['runtime_inputs'] = {'path': str(inventory_path), 'sha256': h(inventory_path.read_bytes()),
                                 'source_version': inventory['source_version'],
                                 'source_set_complete': inventory['source_set_complete'],
                                 'expected_count': inventory['expected_count'], 'actual_count': inventory['actual_count'],
                                 'runtime_identities_sha256': h(json.dumps(identities, ensure_ascii=False,
                                                                          separators=(',', ':')).encode())}
        return row

    def recorded_command(argv, log, *, cwd=None, env=env, timeout=1200):
        row, stdout, stderr = run(argv, cwd=cwd, child_env=env, timeout=timeout, check=False)
        Path(log).write_bytes(stdout + stderr)
        row['legacy_probe_log'] = {'path': str(log), 'format': 'stdout bytes followed by stderr bytes; separate original streams retained by c387'}
        node_commands.append(row)
        # 與原 shared.command 一樣，非零由原 one 捕捉為 1；另保真 rc，收尾不接受 crash/timeout 充當有效負控。
        if row['actual_process_returncode'] != 0:
            raise RuntimeError('原 Node 真退出碼非零；原 one 會依原流程讀取結果')

    def ready(argv, *, cwd, env, capture_output):
        # 原 one 的 subprocess.run 未指定 timeout；保留，不另立產品時間門檻。
        row, stdout, stderr = run(argv, cwd=cwd, child_env=env, timeout=None, check=False)
        return subprocess.CompletedProcess(argv, row['actual_process_returncode'], stdout, stderr)

    def server(argv, *, cwd, env, stdout, stderr, start_new_session):
        child = dict(env, GEO261_REAPER_LOG=str(Path(stdout.name).with_suffix('.reaper.jsonl')))
        actual = [sys.executable, '-B', str(tools / a.reaper.name), *map(str, argv)]
        row = {'original_command': list(map(str, argv)), 'command': actual, 'cwd': str(cwd),
               'source_sha': child['P52_SHA'], 'acceptance_sha': a.sha,
               'source_variant': 'main-reference' if child['P52_SHA'] == MAIN else 'fixed-final-source',
               'environment': {k: child.get(k) for k in SAFE}, 'started_epoch': time.time(),
               'stdout': str(stdout.name), 'stderr_redirected_to_stdout': stderr == subprocess.STDOUT,
               'start_new_session': start_new_session}
        process = subprocess.Popen(actual, cwd=cwd, env=child, stdout=stdout, stderr=stderr,
                                   start_new_session=start_new_session)
        row['pid'] = process.pid
        servers.append(row)
        server_processes.append((row, process))
        return process

    code = 2
    lock = a.heavy_lock.open('a+b')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before_fix = guard(repo, 'fix-before', a.sha)
        before_main = guard(main_repo, 'main-before', MAIN)
        for argv in (['/workspace/geo261-environment/bin/google-chrome', '--version'], ['node', '--version'],
                     [sys.executable, '--version'], ['cc', '--version'],
                     ['dpkg-query', '-W', '-f=${Status} ${Version}\n', 'fonts-noto-cjk']):
            run(argv, timeout=30)
        original = (protocol / 'postfix_validate.py').read_text()
        tree = ast.parse(original)
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        starts = [i for i, n in enumerate(function.body) if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'records' for t in n.targets)]
        need(len(starts) == 1, '原 records AST anchor 改變')
        nodes = function.body[starts[0]:]
        need(isinstance(nodes[-1], ast.Raise) and isinstance(nodes[-1].exc, ast.Call)
             and isinstance(nodes[-1].exc.func, ast.Name) and nodes[-1].exc.func.id == 'SystemExit',
             '原 main 最後 SystemExit 改變')
        body = ast.Module(body=nodes, type_ignores=[])
        source = ''.join(original.splitlines(keepends=True)[nodes[0].lineno - 1:nodes[-1].end_lineno])
        need("medians['fix']<=medians['main']" in source and "['main','fix','fix','main']" in source
             and "['normal','delay','revert-delay','wrong','missing']" in source, '原正式 protocol body 改變')
        (out / 'original-executed-main-tail.py.txt').write_text(source)
        report['original_body_ast_sha256'] = h(ast.dump(body, include_attributes=False).encode())
        report['original_body_source_sha256'] = h(source.encode())
        old_argv = sys.argv
        old_path = list(sys.path)
        try:
            sys.path.insert(0, str(protocol))
            sys.argv = [str(protocol / 'postfix_validate.py'), a.sha]
            spec = importlib.util.spec_from_file_location('p52_unmodified_original_postfix', protocol / 'postfix_validate.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.argv = old_argv
            sys.path[:] = old_path
        need(Path(module.shared.__file__).resolve() == protocol / 'p52_measure.py', 'p52_measure import 不是 frozen snapshot')
        need(module.shared.SHAS['main'] == MAIN, '原 main 比較 SHA 改變')
        module.OUT = out
        module.WORK = out / 'work'
        module.ENV = env
        module.SHA = a.sha
        module.shared.WORK = main_repo.parent
        module.shared.command = recorded_command
        module.subprocess = types.SimpleNamespace(Popen=server, run=ready, STDOUT=subprocess.STDOUT,
                                                  TimeoutExpired=subprocess.TimeoutExpired)
        module.__dict__['repo'] = repo
        main_build_env = dict(env, GITHUB_SHA=MAIN, GITHUB_WORKSPACE=str(main_repo), P52_SHA=MAIN)
        report['main_preparation_build'] = run(['npm', 'run', 'build'], cwd=main_repo,
                                               child_env=main_build_env, timeout=1200, source_sha=MAIN,
                                               variant='main-reference-preparation')[0]
        report['fix_build'] = run(['npm', 'run', 'build'], cwd=repo, timeout=1200)[0]
        try:
            exec(compile(body, str(protocol / 'postfix_validate.py'), 'exec'), module.__dict__)
        except SystemExit as error:
            need(isinstance(error.code, int) and error.code in (0, 1), '原 body 非預期 SystemExit')
            report['original_body_system_exit'] = error.code
            report['original_body_completed'] = True
        need(report['original_body_completed'], '原 main body 沒有執行到原 SystemExit')
        original_receipt = json.loads((out / 'receipt.json').read_text())
        need(original_receipt['sha'] == a.sha and original_receipt['drivers_sha256'] == PROTOCOL,
             '原正式收據來源或 protocol hash 不符')
        need(len(original_receipt['records']) == 4 and len(original_receipt['controls']) == 5,
             '原四區塊或五控制不完整')
        modes = ['measure'] * 4 + ['normal', 'delay', 'revert-delay', 'wrong', 'missing']
        expected = [0] * 6 + [1] * 3
        need(len(node_commands) == 9, '原 Node 命令不是九個')
        for row, mode, rc in zip(node_commands, modes, expected):
            need(row['effective_environment']['P52_CASE_MODE'] == mode,
                 'Node mode/order 與原 protocol 不符')
            need(row['actual_process_returncode'] == rc and not row['timeout_expired'],
                 'Node 真退出碼不符；crash/timeout 不得當有效負控或 timing 紅')
        for row in original_receipt['records']:
            samples = row['result']['samples']
            need(len(samples) == 8 and [s['trial'] for s in samples] == list(range(8)),
                 '每區塊原八筆不完整，不可挑樣本')
            need(all(isinstance(s.get('appearedMs'), (int, float)) and math.isfinite(s['appearedMs'])
                     and s['appearedMs'] >= 0 for s in samples), '樣本缺漏或非有限數')
        need(original_receipt['timing']['count'] == {'main': 16, 'fix': 16}, '原 main/fix 各十六筆不符')
        need(all(row['expected_behavior_proved'] for row in original_receipt['controls']), '原控制未全符合判準')
        need(report['original_body_system_exit'] == (0 if original_receipt['timing']['no_regression'] else 1),
             '原 SystemExit 與原 timing gate 不符')
        report['original_receipt'] = {'path': str(out / 'receipt.json'), 'sha256': h((out / 'receipt.json').read_bytes())}
        report['timing'] = original_receipt['timing']
        report['passed'] = report['original_body_system_exit'] == 0
        code = report['original_body_system_exit']
    except BaseException as error:
        errors.append(traceback.format_exc())
        report['exception_type'] = type(error).__name__
        code = 1 if isinstance(error, AssertionError) else 2
    finally:
        for row, process in server_processes:
            row['actual_process_returncode'] = process.poll()
            row['ended_epoch'] = time.time()
            path = Path(row['stdout'])
            if path.is_file():
                row.update(stdout_bytes=path.stat().st_size, stdout_sha256=h(path.read_bytes()))
            events_path = Path(row['environment']['GEO261_REAPER_LOG'])
            if events_path.is_file():
                row['reaper_log'] = {'path': str(events_path), 'sha256': h(events_path.read_bytes())}
                try:
                    events = [json.loads(line) for line in events_path.read_text().splitlines()]
                    need(events and events[-1].get('event') == '完成' and process.poll() is not None,
                         'server subreaper 未完整回收')
                except BaseException:
                    errors.append(traceback.format_exc())
            else:
                errors.append('server reaper log 不存在：' + str(events_path))
        for path, label, sha, before in ((repo, 'fix-after', a.sha, locals().get('before_fix')),
                                         (main_repo, 'main-after', MAIN, locals().get('before_main'))):
            try:
                after = guard(path, label, sha)
                if before is not None:
                    need(after['tree_index_sha256'] == before['tree_index_sha256'], label + '：index 身分改變')
                    before_runtime_path = Path(before['runtime_inputs']['path'])
                    after_runtime_path = Path(after['runtime_inputs']['path'])
                    before_runtime_bytes = before_runtime_path.read_bytes()
                    after_runtime_bytes = after_runtime_path.read_bytes()
                    need(h(before_runtime_bytes) == before['runtime_inputs']['sha256']
                         and h(after_runtime_bytes) == after['runtime_inputs']['sha256'],
                         label + '：原完整 runtime inventory 被改寫')
                    need(same_runtime_identity(json.loads(before_runtime_bytes), json.loads(after_runtime_bytes)),
                         label + '：RuntimeSnapshot 完整輸入身分或 sourceVersion 改變')
            except BaseException:
                errors.append(traceback.format_exc())
        for path, row in frozen.items():
            if h(Path(path).read_bytes()) != row['sha256'] or h(Path(row['snapshot']).read_bytes()) != row['sha256']:
                errors.append('工具或 snapshot 執行中變動：' + path)
        if errors:
            report['passed'] = False
            if code == 0:
                code = 2
        report.update(ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      actual_driver_exit_code=code, commands=recorder.rows)
        save(out / 'execution-receipt.json', report)
        resource.setrlimit(resource.RLIMIT_STACK, (soft, hard))
        lock.close()
    print(json.dumps({'sha': a.sha, 'main': MAIN, 'passed': report['passed'],
                      'original_body_system_exit': report['original_body_system_exit'],
                      'actual_driver_exit_code': code, 'receipt': str(out / 'execution-receipt.json'),
                      'errors': errors}, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
