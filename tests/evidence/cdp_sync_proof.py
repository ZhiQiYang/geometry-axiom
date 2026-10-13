#!/usr/bin/env python3
"""Run the PR #197 browser delay/no-op evidence in two disposable Linux clones.

Run only under the project's WSL queue lock. Requires --work below /root,
--out for receipts, --runner-tools pointing at scratchpad/wsl-ci, and a full
--head SHA. --source is read-only. Every mutation is saved as a patch and
restored in finally; no test oracle, golden, or product worktree is edited.
The scopes stop after section 7/P80 or select P88, so these are NOT CI jobs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import urllib.request

BASE = 'e50e8d18c79e95fc72d5e92af74419f8e3282483'
# Exact, single-occurrence source substitutions.
EDITS = {'H_P88ONLY': [('geometry-web/cdp_test.js',
                "  if (scope.mode==='full' || process.env.GEOMETRY_GRID_SYSTEM_ONLY)\n"
                "    await require('./grid_system_test.js')",
                "  if ((scope.mode==='full' || process.env.GEOMETRY_GRID_SYSTEM_ONLY) && "
                '!process.env.GEOMETRY_P88_ONLY)\n'
                "    await require('./grid_system_test.js')"),
               ('geometry-web/cdp_test.js',
                "  if (scope.mode==='full' || process.env.GEOMETRY_GRID_SYSTEM_ONLY)\n"
                "    await require('./grid_rule_editor_test.js')",
                "  if ((scope.mode==='full' || process.env.GEOMETRY_GRID_SYSTEM_ONLY) && "
                '!process.env.GEOMETRY_P88_ONLY)\n'
                "    await require('./grid_rule_editor_test.js')")],
 'H_STOP7': [('geometry-web/cdp_test.js',
              '  console.log("=== 8. Esc 返回世界 ===");',
              "  if(process.env.GEOMETRY_STOP_AFTER_S7){chrome.kill();_log('CDP_RESULT "
              "'+JSON.stringify({schema:'geometry-cdp-result/1',scope,completed:true,stoppedAfterSection7:true,passedAssertions:passN,failedAssertions:failN}));process.exit(failN>0?1:0);}\n"
              '  console.log("=== 8. Esc 返回世界 ===");')],
 'H_STOP80': [('geometry-web/cdp_test.js',
               "  if(scope.mode==='full'||process.env.GEOMETRY_TIMBER_SCHEDULE_ONLY)await "
               "require('./timber_schedule_test.js')({send,eval_,sleep,click,waitForUI,exceptionCount:()=>excN});\n",
               "  if(scope.mode==='full'||process.env.GEOMETRY_TIMBER_SCHEDULE_ONLY)await "
               "require('./timber_schedule_test.js')({send,eval_,sleep,click,waitForUI,exceptionCount:()=>excN});\n"
               "  if(process.env.GEOMETRY_STOP_AFTER_P80){chrome.kill();_log('CDP_RESULT "
               "'+JSON.stringify({schema:'geometry-cdp-result/1',scope,completed:true,stoppedAfterP80:true,passedAssertions:passN,failedAssertions:failN}));process.exit(failN>0?1:0);}\n")],
 'M80a': [('geometry-web/app.js',
           '  return res;\n  } finally { releaseNativeOperation?.(); }',
           '  if (cmd === "references" && JSON.stringify(res).includes("schedule_stale")) await new '
           'Promise(r => setTimeout(r, 800));\n'
           '  return res;\n'
           '  } finally { releaseNativeOperation?.(); }')],
 'M80b': [('geometry-web/app.js',
           '      await feLoadGuides(); renderFaceLayers();\n'
           '      throw new Error("原生來源已變更，料單已更新；請核對後再匯出。");',
           '      renderFaceLayers();\n      throw new Error("原生來源已變更，料單已更新；請核對後再匯出。");')],
 'M80c': [('geometry-web/app.js',
           '    if (latest.sourceFingerprint !== snapshot.sourceFingerprint) {\n',
           '    if (false && latest.sourceFingerprint !== snapshot.sourceFingerprint) {\n')],
 'M7a': [('geometry-web/app.js',
          '  if (await emitBoundary(e.bid, work)) await feAfterChange();\n  else drawFaceEditor();\n}',
          '  window.__mutDelay = true;\n'
          '  if (await emitBoundary(e.bid, work)) await feAfterChange();\n'
          '  else drawFaceEditor();\n'
          '}'),
         ('geometry-web/app.js',
          '    boundaries[f.id] = b.loops;\n'
          '  }\n'
          '  if (seq !== ocSeq || !current() || connection.phase === "error") return false;',
          '    boundaries[f.id] = b.loops;\n'
          '  }\n'
          '  if (window.__mutDelay) { window.__mutDelay = false; await new Promise(r => setTimeout(r, '
          '2500)); }\n'
          '  if (seq !== ocSeq || !current() || connection.phase === "error") return false;')],
 'M7b': [('geometry-web/app.js',
          '  if (await emitBoundary(e.bid, work)) await feAfterChange();\n  else drawFaceEditor();\n}',
          '  window.__mutFreeze = true;\n'
          '  if (await emitBoundary(e.bid, work)) await feAfterChange();\n'
          '  else drawFaceEditor();\n'
          '}'),
         ('geometry-web/app.js',
          '  oc.surfs = sf.surfaces; oc.bmap = boundaries;',
          '  oc.surfs = sf.surfaces; if (!window.__mutFreeze) oc.bmap = boundaries;'),
         ('geometry-web/app.js',
          '    if (b.ok) oc.bmap[bid] = b.loops;\n  }\n  await feLoadGuides();',
          '    if (b.ok && !window.__mutFreeze) oc.bmap[bid] = b.loops;\n  }\n  await feLoadGuides();')],
 'M88a': [('geometry-web/grid-system-workspace.js',
           "const references=await apiRequest('references');if(!ownsEntry())return;",
           "const references=await apiRequest('references');if(options.mode==='binding')await new "
           'Promise(r=>setTimeout(r,1500));if(!ownsEntry())return;')],
 'M88a_all': [('geometry-web/grid-system-workspace.js',
               "const references=await apiRequest('references');if(!ownsEntry())return;",
               "const references=await apiRequest('references');await new "
               'Promise(r=>setTimeout(r,1500));if(!ownsEntry())return;')],
 'M88b': [('geometry-web/grid-system-workspace.js',
           "$('igEditSource').onclick = () => {if(s.source)return open({system: s.source.id, "
           'expectedSource:sourceKey(s.source)});};',
           "$('igEditSource').onclick = () => {if(s.source){window.__mutSwap=true;return open({system: "
           's.source.id, expectedSource:sourceKey(s.source)});}};'),
          ('geometry-web/grid-system-workspace.js',
           "$('igNewBinding')?.addEventListener('click', () => open({system: s.source.id, mode: 'binding', "
           'expectedSource:sourceKey(s.source)}));',
           "$('igNewBinding')?.addEventListener('click', () => {window.__mutSwap=true;return open({system: "
           "s.source.id, mode: 'binding', expectedSource:sourceKey(s.source)});});"),
          ('geometry-web/grid-system-workspace.js',
           'if(!dialog.open)dialog.showModal();await render(state);if(!ownsEntry())return;',
           'if(!dialog.open)dialog.showModal();if(window.__mutSwap){window.__mutSwap=false;await new '
           'Promise(res=>{const t=setTimeout(done,600);function '
           "done(){clearTimeout(t);dialog.removeEventListener('scroll',done,true);res();}dialog.addEventListener('scroll',done,true);});if(!ownsEntry())return;}await "
           'render(state);if(!ownsEntry())return;')],
 'M88c': [('geometry-web/grid-system-workspace.js',
           '<button id="igNewBinding" class="btn" type="button">',
           '<button id="igNewBinding" class="btn" type="button" hidden style="display:none">')],
 'M88d': [('geometry-web/grid-system-workspace.js',
           '<select id="igBoundary">',
           '<select id="igBoundary" style="display:none">')],
 'M7late': [('geometry-web/app.js',
             '  if (await emitBoundary(e.bid, work)) await feAfterChange();\n  else drawFaceEditor();\n}',
             '  window.__mutDelay = true;\n'
             '  if (await emitBoundary(e.bid, work)) await feAfterChange();\n'
             '  else drawFaceEditor();\n'
             '}'),
            ('geometry-web/app.js',
             '    boundaries[f.id] = b.loops;\n'
             '  }\n'
             '  if (seq !== ocSeq || !current() || connection.phase === "error") return false;',
             '    boundaries[f.id] = b.loops;\n'
             '  }\n'
             '  if (window.__mutDelay) { window.__mutDelay = false; await new Promise(r => setTimeout(r, '
             '18000)); }\n'
             '  if (seq !== ocSeq || !current() || connection.phase === "error") return false;')]}


def command(args, cwd, env, log, timeout=600):
    started = time.monotonic()
    with log.open('wb') as output:
        process = subprocess.Popen(args, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            code = 124
        finally:
            stop_group(process)
    return {'command': args, 'exit': code, 'seconds': round(time.monotonic() - started, 3),
            'log': str(log), 'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest()}


def stop_group(process):
    # Only process groups created by this runner are targeted, including their
    # remaining children if the original process has already exited.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def output(args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def apply(root, variants):
    originals = {}
    try:
        for name in variants:
            for relative, old, new in EDITS[name]:
                path = root / relative
                originals.setdefault(path, path.read_bytes())
                source = path.read_bytes().decode('utf-8')
                assert source.count(old) == 1, (name, relative, 'anchor count', source.count(old))
                path.write_bytes(source.replace(old, new).encode('utf-8'))
    except BaseException:
        for path, data in originals.items():
            path.write_bytes(data)
        raise
    return originals


def cases():
    # Expected failures must name the actual site. A startup/other test failure
    # cannot count as killing a mutation.
    return [
        ('s7-old-baseline', 'old', ['H_STOP7'], {}, True, '✓ 頂點編輯有效'),
        ('s7-new-baseline', 'new', ['H_STOP7'], {}, True, '✓ 頂點編輯有效'),
        ('s7-old-delay', 'old', ['H_STOP7', 'M7a'], {}, False, '✗ 頂點編輯無效'),
        ('s7-new-delay', 'new', ['H_STOP7', 'M7a'], {}, True, '✓ 頂點編輯有效'),
        ('s7-new-noop', 'new', ['H_STOP7', 'M7b'], {}, False, 'SYNC_TIMEOUT'),
        ('s7-new-late', 'new', ['H_STOP7', 'M7late'], {}, False, 'SYNC_TIMEOUT'),
        ('p80-old-baseline', 'old', ['H_STOP80'], {'GEOMETRY_TIMBER_SCHEDULE_ONLY': '1'}, True, 'P80 來源改動先更新且拒絕匯出過期料單 ✓'),
        ('p80-new-baseline', 'new', ['H_STOP80'], {'GEOMETRY_TIMBER_SCHEDULE_ONLY': '1'}, True, 'P80 來源改動先更新且拒絕匯出過期料單 ✓'),
        ('p80-old-delay', 'old', ['H_STOP80', 'M80a'], {'GEOMETRY_TIMBER_SCHEDULE_ONLY': '1'}, False, 'P80 來源改動先更新且拒絕匯出過期料單 ✗'),
        ('p80-new-delay', 'new', ['H_STOP80', 'M80a'], {'GEOMETRY_TIMBER_SCHEDULE_ONLY': '1'}, True, 'P80 來源改動先更新且拒絕匯出過期料單 ✓'),
        ('p80-new-noop', 'new', ['H_STOP80', 'M80b'], {'GEOMETRY_TIMBER_SCHEDULE_ONLY': '1'}, False, 'P80 條件等待逾時'),
        ('p80-new-wrong-export', 'new', ['H_STOP80', 'M80c'], {'GEOMETRY_TIMBER_SCHEDULE_ONLY': '1'}, False, 'P80 來源改動先更新且拒絕匯出過期料單 ✗'),
        ('p88-old-baseline', 'old', ['H_P88ONLY'], {'GEOMETRY_GRID_SYSTEM_ONLY': '1'}, True, None),
        ('p88-new-baseline', 'new', ['H_P88ONLY'], {'GEOMETRY_GRID_SYSTEM_ONLY': '1'}, True, None),
        ('p88-old-delay', 'old', ['H_P88ONLY', 'M88a'], {'GEOMETRY_GRID_SYSTEM_ONLY': '1'}, False, 'Rule line control unreachable #igBoundary'),
        ('p88-new-delay', 'new', ['H_P88ONLY', 'M88a'], {'GEOMETRY_GRID_SYSTEM_ONLY': '1'}, True, None),
        ('p88-old-swap', 'old', ['H_P88ONLY', 'M88b'], {'GEOMETRY_GRID_SYSTEM_ONLY': '1'}, False, 'Rule line control unreachable'),
        ('p88-new-swap', 'new', ['H_P88ONLY', 'M88b'], {'GEOMETRY_GRID_SYSTEM_ONLY': '1'}, True, None),
        ('p88-new-noop', 'new', ['H_P88ONLY', 'M88d'], {'GEOMETRY_GRID_SYSTEM_ONLY': '1'}, False, 'P88 條件等待逾時'),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--head', required=True)
    parser.add_argument('--source', type=Path, default=Path('/mnt/d/geometry-axiom'))
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--runner-tools', type=Path, required=True)
    args = parser.parse_args()
    assert sys.platform.startswith('linux') and re.fullmatch('[0-9a-f]{40}', args.head)
    work = args.work.resolve()
    assert Path('/root') in work.parents and not work.exists(), 'fresh owned directory below /root required'
    work.mkdir(parents=True)
    args.out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PATH='/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
               LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONIOENCODING='utf-8',
               WSL_CI_JOB_TAG='board-pr197-' + args.head[:8])
    # The shared sampler identifies our descendants using this inherited tag.
    os.environ['WSL_CI_JOB_TAG'] = env['WSL_CI_JOB_TAG']
    spec = importlib.util.spec_from_file_location('proof_ci_run', args.runner_tools / 'ci_run.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    report = {'head': args.head, 'old_test_head': BASE, 'cases': {}, 'completed': False,
              'scope': 'actual CDP browser/native; intentionally scoped, not seven CI jobs'}
    report['exclusivity'] = {'before': runner.quiesce(max_s=60)}
    assert report['exclusivity']['before']['exclusive_at_start'], 'foreign heavy processes at start'
    sampler = runner.ForeignSampler()
    sampler.start()
    clones = {}
    try:
        for name, sha in [('old', BASE), ('new', args.head)]:
            root = work / name
            step = command(['git', 'clone', '--no-checkout', '--shared', str(args.source), str(root)], work, env,
                           args.out / (name + '-clone.log'))
            assert step['exit'] == 0, step
            step = command(['git', 'checkout', '--detach', sha], root, env, args.out / (name + '-checkout.log'))
            assert step['exit'] == 0 and output(['git', 'rev-parse', 'HEAD'], root) == sha, step
            assert not output(['git', 'status', '--porcelain'], root)
            clones[name] = root
        assert not output(['git', 'diff', BASE, args.head, '--', 'geometry-web/app.js',
                           'geometry-web/grid-system-workspace.js', 'current_geometry.c', 'geometry-core'], clones['new'])
        for name, clone, variants, scope, expected_green, reason in cases():
            root = clones[clone]
            out = args.out / name
            out.mkdir()
            originals = apply(root, variants)
            server = None
            try:
                patch = output(['git', 'diff', '--no-ext-diff'], root)
                (out / 'mutation.patch').write_text(patch + '\n', encoding='utf-8')
                temp = work / 'tmp' / name
                temp.mkdir(parents=True)
                case_env = dict(env, **scope, TMPDIR=str(temp), GEOMETRY_TEST_URL='http://127.0.0.1:18961/',
                                GEOMETRY_FEEDBACK_DIR=str(temp / 'feedback'), GEOMETRY_CHROME='/usr/bin/google-chrome',
                                GEOMETRY_CHROME_FLAGS='--no-sandbox', GEOMETRY_CDP_PORT='9472',
                                GEOMETRY_STOP_AFTER_S7='1', GEOMETRY_STOP_AFTER_P80='1', GEOMETRY_P88_ONLY='1',
                                CI='true', GITHUB_ACTIONS='true', RUNNER_OS='Linux')
                # A private runtime cache per source clone; build receipts still
                # verify the exact closure on every start. No global binary path.
                runtime_temp = work / 'runtime'
                runtime_temp.mkdir(exist_ok=True)
                server_env = dict(case_env, TMPDIR=str(runtime_temp))
                server_log = (out / 'server.log').open('wb')
                server = subprocess.Popen(['python3', '-u', 'geometry-web/start_local.py', '--port', '18961'],
                                          cwd=root, env=server_env, stdout=server_log, stderr=subprocess.STDOUT,
                                          start_new_session=True)
                ready_until = time.monotonic() + 180
                runtime = None
                while time.monotonic() < ready_until:
                    if server.poll() is not None:
                        break
                    try:
                        with urllib.request.urlopen('http://127.0.0.1:18961/runtime', timeout=2) as response:
                            runtime = json.load(response)
                        if runtime.get('fresh') is True and runtime.get('root') == str(root):
                            break
                    except (OSError, ValueError):
                        pass
                    time.sleep(1)
                assert runtime and runtime.get('fresh') is True and runtime.get('root') == str(root), ('runtime', name, runtime)
                probe = command(['python3', 'geometry-web/runtime_version.py', '--probe', '18961'],
                                root, server_env, out / 'runtime-probe.log', timeout=30)
                assert probe['exit'] == 0, ('current source fingerprint mismatch', name, probe)
                (out / 'runtime.json').write_text(json.dumps(runtime, indent=2) + '\n')
                step = command(['node', 'geometry-web/cdp_test.js'], root, case_env, out / 'run.log', timeout=1200)
                text = (out / 'run.log').read_text(encoding='utf-8', errors='replace')
                step.update(variants=variants, expected_green=expected_green, expected_reason=reason,
                            runtime=runtime, patch_sha256=hashlib.sha256((out / 'mutation.patch').read_bytes()).hexdigest(),
                            site_lines=[{'line': i, 'text': line} for i, line in enumerate(text.splitlines(), 1)
                                        if any(mark in line for mark in ('SYNC_WAIT', 'SYNC_TIMEOUT', 'vert0:', 'FATAL:', '✗', 'CDP_RESULT'))])
                report['cases'][name] = step
                assert step['exit'] != 124, ('harness watchdog expired; not a mutation kill', name)
                assert (step['exit'] == 0) == expected_green, ('unexpected verdict', name, step)
                if reason:
                    assert reason in text, ('wrong failure/site', name, reason)
                if expected_green:
                    assert 'CDP_RESULT' in text and 'FATAL:' not in text, ('incomplete scoped run', name)
                if name.startswith('s7-new-') and not expected_green:
                    assert '✗ 頂點編輯無效' in text and '"tag":"§7"' in text
                print(name, step['exit'], step['seconds'], flush=True)
            finally:
                if server is not None:
                    stop_group(server)
                    server_log.close()
                for path, data in originals.items():
                    path.write_bytes(data)
                assert all(path.read_bytes() == data for path, data in originals.items())
                assert not output(['git', 'diff', '--name-only'], root), 'mutation restoration failed'
                (args.out / 'receipt.partial.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        report['completed'] = True
    finally:
        report['exclusivity']['during_run'] = sampler.report()
        report['restored_clones'] = {name: output(['git', 'diff', '--name-only'], root) == '' for name, root in clones.items()}
        (args.out / 'receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert not report['exclusivity']['during_run']['foreign_processes_seen_during_run'], 'foreign activity invalidates evidence'


if __name__ == '__main__':
    main()
