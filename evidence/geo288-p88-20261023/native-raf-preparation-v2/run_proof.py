#!/usr/bin/env python3
"""P88 repo 外受控／自然 trace 草案；須由 root 等原輪收齊後才執行。"""
from __future__ import annotations

import argparse
import ast
import datetime
import difflib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import traceback

import yaml
import capture

HERE = Path(__file__).resolve().parent
FINAL = '3d681636902371ecc528b20f51eea33e272581c9'
CAPTURE = 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
ROUND = Path('/workspace/geo261-environment/run_workflow_round.py')
ROUND_SHA = '6a3e3c327687ee6fdafb1044e4c4036f4d2f881a75498af97bd1e1af861e1310'
REAPER = Path('/workspace/geo261-environment/reap_children.py')
REAPER_SHA = '7d848d6c135b7f329852d16c6da5743effde8b29ccbbc6e70092b6ba25877760'
FAILURE = 'UI condition timed out at === P88. 原生來源子線顯示、完整引用、兩面及正式重開 ===: document.activeElement===document.querySelector("#refGuideMode")'


def h(raw):
    return hashlib.sha256(raw).hexdigest()


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def once(text, old, new):
    need(text.count(old) == 1, '原 round 綁定 anchor 不唯一：' + repr(old))
    return text.replace(old, new, 1)


def bind_round(text, port, cdp_port):
    text = once(text, '    port = 19080 + ORDER.index(args.job)\n', '    port = ' + str(port) + '\n')
    text = once(text, "    return re.sub(r'(?<!\\d)18839(?!\\d)', str(port), value)\n",
                "    value = re.sub(r'(?<!\\d)18839(?!\\d)', str(port), value)\n"
                "    return re.sub(r'(?<!\\d)9334(?!\\d)', '" + str(cdp_port) + "', value)\n")
    text = once(text, "        env['GEOMETRY_CHROME'] = str(CHROME)\n",
                "        env['GEOMETRY_CHROME'] = str(CHROME)\n        env['GEOMETRY_CDP_PORT'] = '" + str(cdp_port) + "'\n")
    text = once(text, "    safe_names = {'PATH', 'LANG', 'LC_ALL', 'PYTHONIOENCODING', 'PYTHONDONTWRITEBYTECODE', 'TMPDIR',\n",
                "    safe_names = {'PATH', 'LANG', 'LC_ALL', 'PYTHONIOENCODING', 'PYTHONDONTWRITEBYTECODE', 'TMPDIR',\n                  'GEOMETRY_CDP_PORT', 'NODE_OPTIONS', 'P88_PROOF_MODE', 'P88_PROOF_VARIANT', 'P88_TRACE_OUT', 'P88_PATCH_MANIFEST', 'P88_PATCH_REPORT', 'P88_SOURCE_REPO', 'P88_SOURCE_SHA256',\n")
    ast.parse(text)
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--sha', required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--heavy-lock', type=Path, required=True)
    p.add_argument('--mode', choices=['natural', 'controlled'], required=True)
    p.add_argument('--job', choices=['canvas', 'grid'], required=True)
    p.add_argument('--candidate', type=Path, required=True)
    a = p.parse_args()
    repo, out = a.repo.resolve(), a.out.resolve()
    need(a.sha == FINAL and not sys.flags.optimize and os.environ.get('PYTHONOPTIMIZE') in (None, '', '0'),
         '此診斷草案只綁定原失敗 F；禁止 optimize')
    need(repo.is_dir() and not out.exists() and out.parent.is_dir() and out.is_relative_to(Path('/tmp')),
         '需要既有來源與 fresh、短 /tmp 輸出')
    need(not out.is_relative_to(repo) and not repo.is_relative_to(out) and a.heavy_lock.is_file(),
         '輸出須在來源外並沿用 R3 共用鎖')
    need(a.job == 'grid', '受控反證草案只用原 grid partial；不是完整 canvas gate')
    need(Path(capture.__file__).resolve() == HERE / 'capture.py'
         and h((HERE / 'capture.py').read_bytes()) == CAPTURE, '原 recorder hash／來源不符')
    need(h(ROUND.read_bytes()) == ROUND_SHA and h(REAPER.read_bytes()) == REAPER_SHA, '原 round／reaper hash 不符')
    out.mkdir()
    tools = out / 'tools'
    tools.mkdir()
    frozen = {}
    generated_frozen = {}

    def pin_generated(path):
        generated_frozen[str(path)] = h(path.read_bytes())

    for path in [Path(__file__).resolve(), HERE / 'capture.py', HERE / 'trace-tools/preload.cjs',
                 HERE / 'trace-tools/patch-loader.cjs', HERE / 'only-p88.cjs', ROUND, REAPER]:
        raw = path.read_bytes()
        target = tools / path.name
        need(not target.exists(), '凍結工具檔名撞名')
        target.write_bytes(raw)
        frozen[str(path)] = {'sha256': h(raw), 'snapshot': str(target)}
    candidate_path = a.candidate.resolve()
    candidate_raw = candidate_path.read_bytes()
    candidate = json.loads(candidate_raw)
    need(Path(candidate['repo']).resolve() == repo, '候選原 source repo 不符')
    need(len(candidate['files']) == 1 and {row['source_relative'] for row in candidate['files']} ==
         {'geometry-web/grid_rule_lines_test.js'}, '候選替換範圍不是固定 F 的 P88 單檔')
    need(candidate['sha']==a.sha and candidate['files'][0]['original_sha256']=='8106476b6eb2271111caa835a863b72eced4bab3b2ef77244f28534d83ca0a52'
         and candidate['files'][0]['withdrawn_sha256']=='c47259607a3299d49e1044f3d4d6e5561c0601e0f2295fb7ec5f2255261f4e8c', 'F 原件／撤回唯一 bytes 不符')
    candidate_frozen = dict(candidate, files=[])
    for entry in candidate['files']:
        source = repo / entry['source_relative']
        need(h(source.read_bytes()) == entry['original_sha256'], '原 source 已不同於候選前提')
        target = tools / ('candidate-' + Path(entry['candidate']).name)
        raw = Path(entry['candidate']).read_bytes()
        need(h(raw) == entry['candidate_sha256'], '候選 source bytes 變動')
        target.write_bytes(raw)
        frozen[str(Path(entry['candidate']).resolve())] = {'sha256': h(raw), 'snapshot': str(target)}
        patch = Path(entry['patch'])
        need(h(patch.read_bytes()) == entry['patch_sha256'], '候選 diff bytes 變動')
        patch_target = tools / patch.name
        patch_target.write_bytes(patch.read_bytes())
        frozen[str(patch.resolve())] = {'sha256': h(patch.read_bytes()), 'snapshot': str(patch_target)}
        withdrawn_source=Path(entry['withdrawn'])
        withdrawn_target=tools / ('withdrawn-' + withdrawn_source.name)
        need(h(withdrawn_source.read_bytes())==entry['withdrawn_sha256'], '撤回 bytes 變動')
        withdrawn_target.write_bytes(withdrawn_source.read_bytes())
        frozen[str(withdrawn_source.resolve())]={'sha256':h(withdrawn_source.read_bytes()),'snapshot':str(withdrawn_target)}
        candidate_frozen['files'].append(dict(entry, candidate=str(target), withdrawn=str(withdrawn_target), patch=str(patch_target)))
    save(tools / 'CANDIDATE.json', candidate_frozen)
    (tools / 'CANDIDATE.original.json').write_bytes(candidate_raw)
    frozen[str(candidate_path)] = {'sha256': h(candidate_raw), 'snapshot': str(tools / 'CANDIDATE.original.json')}
    pin_generated(tools / 'CANDIDATE.json')
    env = dict(os.environ)
    cleared = []
    for key in list(env):
        if key.startswith(('GEOMETRY_', 'P88_')) or key in ('NODE_OPTIONS', 'PYTHONOPTIMIZE', 'PYTHONPATH', 'PYTHONSTARTUP', 'LD_PRELOAD'):
            cleared.append(key)
            env.pop(key)
    env.update(LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONIOENCODING='utf-8',
               PYTHONDONTWRITEBYTECODE='1', GITHUB_SHA=a.sha, GITHUB_WORKSPACE=str(repo))
    recorder = capture.Recorder(out, env, a.sha)
    phases = []
    report = {'schema': 'geo288-p88-controlled-input-candidate-proof/1', 'sha': a.sha,
              'mode': a.mode, 'job': a.job, 'repo': str(repo),
              'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'source_files_modified': False, 'candidate_application': '記憶體載入明列 source variant；不寫 source/index/HEAD，不是新 final SHA 的正式 gate。',
              'scope': 'DIAGNOSTIC ONLY: original grid bootstrap and complete P88 module; two other grid modules are explicitly omitted by an external loader. This is never a formal grid or canvas gate.',
              'natural_case_root_cause_confirmed': False, 'tool_hashes': frozen,
              'candidate_manifest_original_sha256': h(candidate_raw), 'generated_tool_hashes': generated_frozen,
              'cleared_environment_names': sorted(cleared), 'phases': phases, 'errors': [], 'commands': recorder.rows,
              'passed': False, 'actual_driver_exit_code': None}

    def cmd(argv, *, cwd=repo, child=None, check=True, variant='source-identity'):
        old = recorder.env
        recorder.env = env if child is None else child
        try:
            return recorder.run(list(map(str, argv)), cwd=cwd, timeout=None, check=check,
                                source_sha=a.sha, source_variant=variant)
        finally:
            recorder.env = old

    def git(*parts):
        return cmd(['git', *parts])[1]

    def guard(label):
        head = git('rev-parse', 'HEAD').decode().strip()
        status = git('status', '--porcelain=v1', '--untracked-files=all').decode()
        index = git('ls-files', '--stage', '-z')
        need(head == a.sha and not status, label + '：固定乾淨 SHA 不符')
        return {'label': label, 'head': head, 'status': status, 'index_sha256': h(index),
                'p88_source_sha256': h((repo / 'geometry-web/grid_rule_lines_test.js').read_bytes()),
                'helper_source_sha256': h((repo / 'geometry-web/cdp_helpers.js').read_bytes()),
                'app_source_sha256': h((repo / 'geometry-web/app.js').read_bytes())}

    code = 2
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    need(hard == resource.RLIM_INFINITY or hard >= 16777216, '原 16MiB stack 不足')
    resource.setrlimit(resource.RLIMIT_STACK, (16777216, hard))
    lock = a.heavy_lock.open('a+b')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report['source_before'] = guard('before')
        workflow = yaml.safe_load((repo / '.github/workflows/integration-tests.yml').read_text())
        matrix = next(row for row in workflow['jobs']['browser']['strategy']['matrix']['include'] if row['suite'] == a.job)
        report['original_ci_minutes'] = matrix['timeout']
        golden_p88 = json.loads((repo / 'geometry-web/cdp_sections.golden.json').read_text())['sections']['P88']
        sequence = ['natural'] if a.mode == 'natural' else ['fixed', 'withdrawn', 'restored']
        for index, variant in enumerate(sequence):
            phase = out / variant
            phase.mkdir()
            trace = phase / 'trace.json'
            memory_report = phase / 'memory-source-variants.json'
            selection_report = phase / 'diagnostic-scope.json'
            bound = bind_round(ROUND.read_text(), 19801 + index, 9720 + index)
            bound_path = phase / 'run_workflow_round.py'
            bound_path.write_text(bound)
            (phase / 'round.binding.patch').write_text(''.join(difflib.unified_diff(
                ROUND.read_text().splitlines(keepends=True), bound.splitlines(keepends=True),
                fromfile=str(ROUND), tofile=str(bound_path))))
            pin_generated(bound_path)
            pin_generated(phase / 'round.binding.patch')
            child = dict(env, P88_SOURCE_REPO=str(repo), P88_PROOF_MODE=a.mode, P88_PROOF_VARIANT=variant,
                         P88_TRACE_OUT=str(trace), P88_ONLY_REPORT=str(selection_report), P88_PATCH_MANIFEST=str(tools / 'CANDIDATE.json'),
                         P88_PATCH_REPORT=str(memory_report),
                         P88_SOURCE_SHA256=h((repo / 'geometry-web/grid_rule_lines_test.js').read_bytes()),
                         GEO261_REAPER_LOG=str(phase / 'round-reaper.jsonl'))
            preload = str(tools / 'preload.cjs')
            patch_loader = str(tools / 'patch-loader.cjs')
            need(not any(c.isspace() or c in '\"\'' for c in preload + patch_loader), 'NODE_OPTIONS 綁定路徑不得含空白或引號')
            child['NODE_OPTIONS'] = ('--require=' + patch_loader + ' ' if a.mode == 'controlled' else '') + '--require=' + preload + ' --require=' + str(tools / 'only-p88.cjs')
            row = {'variant': variant, 'expected_original_test_exit': None if variant == 'natural' else (1 if variant == 'withdrawn' else 0),
                   'environment': {k: v for k, v in child.items() if k.startswith(('P88_', 'GEOMETRY_')) or k in ('NODE_OPTIONS', 'PATH', 'LANG', 'LC_ALL', 'GITHUB_SHA', 'GITHUB_WORKSPACE', 'PYTHONDONTWRITEBYTECODE')},
                   'service_port': 19801 + index, 'cdp_port': 9720 + index,
                   'binding_diff': str(phase / 'round.binding.patch'), 'passed': False}
            phases.append(row)
            save(out / 'receipt.json', report)
            try:
                before = guard(variant + '-before')
                command, stdout, stderr = cmd([sys.executable, '-B', tools / 'reap_children.py', sys.executable, '-B', bound_path,
                                               '--repo', repo, '--sha', a.sha, '--job', a.job, '--out-root', phase / 'workflow'],
                                              child=child, check=False, variant='P88-' + variant + '-memory-tool-variant')
                row['command_result'] = command
                original = json.loads((phase / 'workflow' / a.job / 'receipt.json').read_text())
                node = json.loads((phase / 'workflow' / a.job / 'steps/03.command.json').read_text())
                raw_stdout = (phase / 'workflow' / a.job / 'steps/03.stdout').read_text()
                results = [json.loads(line[len('CDP_RESULT '):]) for line in raw_stdout.splitlines() if line.startswith('CDP_RESULT ')]
                need(len(results) == 1, '原唯一 CDP_RESULT 缺件；不能當有效焦點反證')
                result = results[0]
                observed = json.loads(trace.read_text())
                selection = json.loads(selection_report.read_text())
                need(selection['diagnostic_only'] is True and selection['p88_module_bytes_changed_by_scope_selection'] is False and sorted(Path(item['source']).name for item in selection['omitted']) == ['grid_rule_editor_test.js', 'grid_system_test.js'], 'P88-only diagnostic scope does not match its explicit two omissions')
                row['diagnostic_scope'] = selection
                row.update(outer_actual_exit=command['actual_process_returncode'],
                           original_workflow_exit=original['exit_code'], original_test_exit=node['actual_process_returncode'],
                           original_workflow_receipt_sha256=h((phase / 'workflow' / a.job / 'receipt.json').read_bytes()),
                           original_test_stdout_sha256=h((phase / 'workflow' / a.job / 'steps/03.stdout').read_bytes()),
                           cdp_result=result, trace_sha256=h(trace.read_bytes()),
                           injection=observed.get('injection'), trace_final_snapshot=observed.get('finalSnapshot'))
                need(not original['over_ci_timeout'] and not node['watchdog_expired'] and not command['timeout_expired']
                     and not command.get('exception'),
                     '超原正式時限或真 timeout，不算有效反證')
                need(command['actual_process_returncode'] == original['exit_code'] == node['actual_process_returncode'],
                     '外層 reaper、原 workflow 與原 node 退出不一致；屬工具／環境未完成')
                need(observed['target_invocations'] == 1 and observed['source_bytes_unchanged'] is True and not observed['errors'],
                     '原 P88 trace 完整性不符')
                need(observed['browser_trace']['stopped'] is True and not observed['browser_trace']['errors'],
                     'P88 browser trace cleanup or held-query integrity failed')
                transport = observed['websocket_observation']
                need(transport['enabled'] is True and transport['error'] is None
                     and not transport['pending_mouse_acknowledgements'], '真 CDP mouse transport 觀測不完整')
                if a.mode == 'controlled':
                    memory = json.loads(memory_report.read_text())
                    expected_files = {str(repo / entry['source_relative']): entry for entry in candidate_frozen['files']}
                    need(memory['source_files_modified'] is False and len(memory['files']) == 1
                         and memory['variant'] == variant and Path(memory['source_repo']).resolve() == repo
                         and {entry['source'] for entry in memory['files']} == set(expected_files),
                         '記憶體候選明細／variant／source 範圍不符')
                    for executed in memory['files']:
                        expected = expected_files[executed['source']]
                        fixed = variant != 'withdrawn'
                        need(executed['original_sha256'] == expected['original_sha256']
                             and executed['executed_sha256'] == expected['original_sha256' if fixed else 'withdrawn_sha256']
                             and executed['variant'] == variant and executed['memory_only'] is True
                             and executed['source_file_modified'] is False
                             and executed['candidate'] == (None if fixed else expected['withdrawn']),
                             '實際記憶體執行 bytes 不符指定 source variant')
                    row['memory_variants'] = memory
                    injection = observed['injection']
                    need(injection['applied'] is True and injection['count'] == 1, '單次真布局位移未成立，不能假叫反證')
                    native=injection['native_callback']
                    need(native['native_dispatch_count']==1 and native['original_measure_evaluations']==1
                         and native['this_is_window'] is True and native['callback_completed'] is True
                         and native['callback_source_matches'] is True and native['cancelled'] is False
                         and native['original_request_animation_frame_native'] is True
                         and native['original_cancel_animation_frame_native'] is True
                         and injection['parsed_json_unchanged'] is True,
                         '原 native callback／原單次量測／parsed JSON 守門不符')
                    scroll_events = [event for event in observed['events'] if event['kind'] == 'controlled-native-raf-measurement']
                    need(len(scroll_events) == 1, '具名真布局位移事件不唯一')
                    native_rows={kind:[e for e in observed['events'] if e['kind']==kind] for kind in ('native-restore-registered','native-restore-entry','native-restore-return')}
                    need(all(len(events)==1 for events in native_rows.values()), '原 native callback 登錄／進出事件不唯一')
                    reg,entry,returned=[native_rows[k][0] for k in ('native-restore-registered','native-restore-entry','native-restore-return')]
                    measured=[e for e in observed['events'] if e['kind']=='measure' and e.get('inside_native_restore_before_original') is True]
                    need(len(measured)==1 and reg['serial']<entry['serial']<measured[0]['serial']<returned['serial']<scroll_events[0]['serial']
                         and all(e['native_id']==native['native_id'] for e in (reg,entry,returned))
                         and returned['original_threw'] is False and measured[0]['original_measure']==injection['original_measure'], '原量測／native callback 時序或原值不符')
                    node_returns=[e for e in observed['node_events'] if e['kind']=='measure-return' and e.get('measurement_id')==injection['measurement_id']]
                    need(len(node_returns)==1 and node_returns[0]['selector']=='#refGuideMode' and node_returns[0]['original_measure']==injection['original_measure'], '原量測 CDP 回傳值或身份不符')
                    pressed=[e for e in observed['node_events'] if e['kind']=='cdp-mouse-request' and e['params']['type']=='mousePressed'
                             and int(e['monotonic_ns'])>int(node_returns[0]['monotonic_ns'])]
                    need(pressed, '原量測 CDP 回覆後缺真 mousePressed')
                    row['first_post_measure_mouse_request']=pressed[0]
                    if variant=='withdrawn':
                        need(pressed[0]['params']['x']==injection['original_measure']['x'] and pressed[0]['params']['y']==injection['original_measure']['y'], '撤回的真 CDP mousePressed 並未使用原舊座標')
                    clicks = [event for event in observed['events'] if event['serial'] > scroll_events[0]['serial']
                              and event['kind'] == 'dom-mousedown' and event['phase'] == 'capture']
                    need(clicks and clicks[0]['trusted'] is True, '布局位移後沒有真受信任的原 mouse 輸入')
                    first_mouse = clicks[0]
                    row['first_post_injection_mouse'] = first_mouse
                    if variant == 'withdrawn':
                        need(first_mouse['target']['token'] == injection['target_label']['token']
                             or first_mouse['target']['id'] == 'refGuideRatio', '撤修第一個真 mouse 未落到比例列')
                    else:
                        need(first_mouse['target']['id'] == 'refGuideMode', '修復第一個真 mouse 未落到模式控制項')
                    need(command['actual_process_returncode'] == row['expected_original_test_exit']
                         and node['actual_process_returncode'] == row['expected_original_test_exit']
                         and original['exit_code'] == row['expected_original_test_exit'], '原退出不符三態預期')
                    need(result['failedAssertions'] == 0, '有其他原斷言失敗，不能只歸焦點位移')
                    if variant == 'withdrawn':
                        need(result['completed'] is False and result.get('fatal') == FAILURE,
                             '撤修不是原具名精確焦點逾時紅')
                        need(observed['finalSnapshot']['active']['id'] == 'refGuideRatio', '撤修最後真焦點不是相鄰比例')
                    else:
                        need(result['completed'] is True and result['sections'].get('P88') == golden_p88,
                             '原完整 P88／原 golden 段數未齊')
                        need(observed['completed'] is True, '原 P88 module 沒有完整完成')
                    row['passed'] = True
                else:
                    row['natural_diagnostic_only'] = True
                    row['passed'] = None
                after = guard(variant + '-after')
                need(before['index_sha256'] == after['index_sha256'], '執行中 index 身分改變')
                row['source_before'], row['source_after'] = before, after
            except BaseException:
                row['error'] = traceback.format_exc()
                report['errors'].append(variant + ': ' + row['error'])
            save(out / 'receipt.json', report)
        if a.mode == 'controlled':
            report['passed'] = len(phases) == 3 and all(row['passed'] for row in phases) and not report['errors']
            code = 0 if report['passed'] else 2
        else:
            code = phases[0].get('original_test_exit', 2) if not report['errors'] else 2
    except BaseException:
        report['errors'].append(traceback.format_exc())
        code = 2
    finally:
        try:
            report['source_after'] = guard('after')
            need(report['source_before']['index_sha256'] == report['source_after']['index_sha256'], '來源 index 改變')
        except BaseException:
            report['errors'].append(traceback.format_exc())
        for path, identity in frozen.items():
            if h(Path(path).read_bytes()) != identity['sha256'] or h(Path(identity['snapshot']).read_bytes()) != identity['sha256']:
                report['errors'].append('工具／snapshot bytes 改變：' + path)
        for path, expected in generated_frozen.items():
            if h(Path(path).read_bytes()) != expected:
                report['errors'].append('產生的綁定／候選 manifest bytes 改變：' + path)
        if report['errors']:
            report['passed'] = False
            code = 2
        report.update(ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), actual_driver_exit_code=code)
        save(out / 'receipt.json', report)
        resource.setrlimit(resource.RLIMIT_STACK, (soft, hard))
        lock.close()
    print(json.dumps({'sha': a.sha, 'mode': a.mode, 'passed': report['passed'],
                      'actual_driver_exit_code': code, 'receipt': str(out / 'receipt.json'),
                      'errors': report['errors']}, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
