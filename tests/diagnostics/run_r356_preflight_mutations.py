#!/usr/bin/env python3
"""R356 cancellation/confirmation handoff: exact assertion kills, no ledger writes.

Every named withdrawal is syntax checked, exercised between an unchanged
baseline and restoration, and rejected if it times out, crashes, is incomplete,
or does not fail its declared assertion. Only isolated source copies are edited.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
APP = 'geometry-web/app.js'
TIMBER = 'geometry-web/timber-edit.js'
CANVAS = 'tests/test_canvas_creation_owner.cjs'
PROBE = 'tests/diagnostics/r356_timber_preflight.cjs'

FIXED_PREFLIGHT = '''    try {
      // Idle UI preflight must not move synchronous confirmation ownership to
      // a later microtask. A real cancellation keeps its lease until this
      // continuation immediately hands ownership to the original command.
      const pending = window.TimberEdit?.beforeWorldMutation();
      if (pending) { const release = await pending; release(); }
    }'''

CANCEL_PROOF = '''        if (!result || result.ok !== true || result.transport)
          throw Error(result?.error || '角材候選取消結果尚未確認；請重新連線後再取消。');
        // cancelled:false is also definitive: this exact token is no longer
        // pending, including after a lost cancellation response and retry.
        if (typeof result.cancelled !== 'boolean') throw Error('角材候選取消回應不完整，未開放其他修改。');
        revision(result.revision);'''

MUTATIONS = [
    dict(name='R356-PF-01-withdraw-idle-fastpath', file=APP, before=FIXED_PREFLIGHT,
         after='    try { await window.TimberEdit?.beforeWorldMutation(); }', judge='original',
         assertions=['R365_STACK_NATIVE_CONFIRM_LEASE_definition-import', 'R365_NOOP_METADATA_HISTORY'], failures=2),
    dict(name='R356-PF-02-return-idle-promise', file=TIMBER, before='  function beforeWorldMutation() {',
         after='  async function beforeWorldMutation() {', judge='idle',
         assertions=['R356_IDLE_PREFLIGHT_NO_PROMISE']),
    dict(name='R356-PF-03-release-before-caller-handoff', file=TIMBER,
         before='      if (mutationPreflight?.value !== value) releaseCandidate(value);',
         after='      releaseCandidate(value);', judge='delayed',
         assertions=['R356_CANCEL_HANDOFF_NO_MICROTASK_GAP']),
    dict(name='R356-PF-04-release-before-first-await', file=TIMBER,
         before='      const token = value.preview?.token;',
         after='      releaseCandidate(value);\n      const token = value.preview?.token;', judge='delayed',
         assertions=['R356_CANCEL_FIRST_AWAIT_LOCKED']),
    dict(name='R356-PF-05-ignore-native-cancel-rejection', file=TIMBER,
         before=CANCEL_PROOF, after='        /* mutation: accept an unproven cancellation */', judge='rejection',
         assertions=['R356_CANCEL_FAILURE_REFUSES_MUTATION']),
    dict(name='R356-PF-06-release-after-transport-failure', file=TIMBER,
         before='    },error=>{preflight.pending=false;throw error;});',
         after='    },error=>{preflight.pending=false;releaseCandidate(value);mutationPreflight=null;throw error;});',
         judge='transport', assertions=['R356_CANCEL_TRANSPORT_RETAINS_LEASE']),
    dict(name='R356-PF-07-forget-rejected-cancel-token', file=TIMBER,
         before="        if (!result || result.ok !== true || result.transport)\n          throw Error(result?.error || '角材候選取消結果尚未確認；請重新連線後再取消。');",
         after="        if (!result || result.ok !== true || result.transport) {\n          value.preview = null;\n          throw Error(result?.error || '角材候選取消結果尚未確認；請重新連線後再取消。');\n        }",
         judge='rejection', assertions=['R356_CANCEL_RETRY_SAME_TOKEN']),
    dict(name='R356-PF-08-allow-replaced-owner-command', file=TIMBER,
         before="      if(!current)throw Error('取消期間專案或服務已變更，未送出原修改。');",
         after='      /* mutation: continue the retired owner command */', judge='replacedOwner',
         assertions=['R356_CANCEL_REPLACED_OWNER_RETIRES_COMMAND']),
    dict(name='R356-PF-09-remove-canvas-lease-state', file=CANVAS,
         before='assemblyConfirmation:null,timberPreview:null,roomTransaction:null,',
         after='assemblyConfirmation:null,roomTransaction:null,', judge='canvas',
         assertions=['R356_CANVAS_OWNER_FIXTURE_LOADS_ALL_LEASE_STATE'], failures=22),
    dict(name='R356-PF-10-forget-unknown-preview', file=TIMBER,
         before='    value.previewUncertain = true;', after='    value.previewUncertain = false;',
         judge='unknownMalformed', assertions=['R356_UNKNOWN_PREVIEW_REFUSES_MUTATION_malformed']),
    dict(name='R356-PF-11-trust-bridge-error-as-rejection', file=TIMBER,
         before="      if (path === '/timber-edit/preview' && response.ok && result?.ok === false &&\n          /^(TIMBER_(INPUT|ENCODING|JSON|SCHEMA)|HISTORY_GROUP|STALE|CAPACITY|MEMORY)$/.test(result.code)) error.timberPreviewRejected = true;",
         after="      if (path === '/timber-edit/preview' && response.ok && result?.ok === false) error.timberPreviewRejected = true;",
         judge='unknownBridge', assertions=['R356_UNKNOWN_PREVIEW_REFUSES_MUTATION_bridge']),
    dict(name='R356-PF-12-trust-missing-preview-session', file=TIMBER,
         before="    if (path === '/timber-edit/preview' && (!session || response.headers.get('X-Geometry-Session') !== session || connection.session !== session))\n      throw Error('角材預覽未回傳原服務識別；請重新載入，未開放其他修改。');",
         after='    /* mutation: accept an unidentified preview response */',
         judge='missingSuccessSession', assertions=['R356_UNKNOWN_PREVIEW_REFUSES_MUTATION_missingSuccessSession']),
    dict(name='R356-PF-13-send-old-token-to-new-session', file=TIMBER,
         before="        if (session !== connection.session) throw Error('角材候選屬於先前的服務；請重新載入，未送出取消或原修改。');",
         after='        /* mutation: ignore candidate session */', judge='changedSession',
         assertions=['R356_OLD_CANCEL_TOKEN_NEVER_SENT_TO_NEW_SESSION']),
    dict(name='R356-PF-14-remove-cancel-request-id', file=APP,
         before='|timber-edit-confirm |timber-edit-cancel )/.test(cmd) ? crypto.randomUUID() : null;',
         after='|timber-edit-confirm )/.test(cmd) ? crypto.randomUUID() : null;', judge='recoveredCancellation',
         assertions=['R356_CANCEL_LOST_RESPONSE_RECOVERED']),
    dict(name='R356-PF-15-lock-known-rejected-preview', file=TIMBER,
         before='      if (error.timberPreviewRejected === true) value.previewUncertain = false;',
         after='      /* mutation: retain uncertainty after definitive native rejection */', judge='knownRejection',
         assertions=['R356_KNOWN_PREVIEW_REJECTION_RELEASES_OWNER']),
    dict(name='R356-PF-16-reject-already-absent-token', file=TIMBER,
         before="        if (typeof result.cancelled !== 'boolean') throw Error('角材候選取消回應不完整，未開放其他修改。');",
         after="        if (result.cancelled !== true) throw Error('角材候選取消回應不完整，未開放其他修改。');",
         judge='rejection', assertions=['R356_CANCEL_RETRY_CAN_COMPLETE']),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(command, env, directory, label):
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=45)
    (directory / (label + '.stdout')).write_bytes(result.stdout)
    (directory / (label + '.stderr')).write_bytes(result.stderr)
    output = (result.stdout + result.stderr).decode('utf-8')
    summary = {key: int(count) for key, count in re.findall(r'^# (tests|pass|fail|cancelled|skipped) (\d+)$', output, re.M)}
    return result, output, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error('refusing to overwrite previous evidence')
    output = args.output or Path(tempfile.mkdtemp(prefix='r356-preflight-'))
    if args.output:
        output.mkdir(parents=True)
    sources = {name: (ROOT / name).read_bytes() for name in [APP, TIMBER, CANVAS]}
    inputs = [*sources, PROBE, 'tests/fixtures/evidence_adoption_host.cjs',
              'tests/test_evidence_stack_merge.js', 'tests/test_evidence_adoption_transport.cjs',
              'geometry-web/reference-workspace.js', 'geometry-web/project-store.js',
              'tests/diagnostics/run_r356_preflight_mutations.py']
    receipt = {'schema': 'r356-preflight-withdrawals/1', 'kind': 'actual-module-vm',
               'inputs': {name: sha((ROOT / name).read_bytes()) for name in inputs}, 'mutations': []}
    try:
        for definition in MUTATIONS:
            case = output / definition['name']
            case.mkdir()
            target = case / Path(definition['file']).name
            original = sources[definition['file']]
            before, after = definition['before'].encode(), definition['after'].encode()
            assert original.count(before) == 1, definition['name'] + ': anchor is not unique'
            mutated = original.replace(before, after)
            env = dict(os.environ)
            if definition['file'] == APP:
                env['GEOMETRY_TEST_APP'] = str(target)
            elif definition['file'] == TIMBER:
                env['GEOMETRY_TEST_TIMBER_EDIT'] = str(target)
            else:
                env['GEOMETRY_REVIEW_ROOT'] = str(ROOT)
            if definition['judge'] == 'original':
                command = ['node', '--test', '--test-reporter=tap', 'tests/test_evidence_stack_merge.js',
                           'tests/test_evidence_adoption_transport.cjs']
            elif definition['judge'] == 'canvas':
                command = ['node', '--test', '--test-reporter=tap', str(target)]
            else:
                command = ['node', PROBE, definition['judge']]
            record = {**{key: definition[key] for key in ['name', 'file', 'judge', 'assertions']},
                      'command': command, 'runs': []}
            receipt['mutations'].append(record)
            baseline_summary = None
            for phase, source in [('baseline', original), ('mutant', mutated), ('restored', original)]:
                target.write_bytes(source)
                syntax, syntax_text, _ = run(['node', '--check', str(target)], env, case, phase + '-syntax')
                assert syntax.returncode == 0, definition['name'] + ': syntax errors are not kills'
                result, text, summary = run(command, env, case, phase)
                record['runs'].append({'phase': phase, 'exit_code': result.returncode,
                                      'source_sha256': sha(source), 'syntax_exit': syntax.returncode,
                                      'summary': summary, 'stdout_sha256': sha(result.stdout),
                                      'stderr_sha256': sha(result.stderr)})
                assert 'R356_PREFLIGHT_INCOMPLETE' not in text, 'incomplete probe is not evidence'
                if summary:
                    assert summary.get('cancelled') == 0 and summary.get('skipped') == 0, 'cancelled/skipped is not evidence'
                if phase == 'mutant':
                    assert result.returncode == 1, definition['name'] + ': crash or success is not a kill'
                    assert 'ERR_ASSERTION' in text, definition['name'] + ': must fail an assertion'
                    for assertion in definition['assertions']:
                        assert assertion in text, definition['name'] + ': missing named assertion ' + assertion
                    if summary:
                        assert summary['tests'] == baseline_summary['tests'], 'mutant changed discovered count'
                        assert summary['fail'] == definition.get('failures', 1), 'unexpected failed case count'
                        assert summary['pass'] + summary['fail'] == summary['tests'], 'incomplete mutant execution'
                    assert 'R356_PREFLIGHT_PASS' not in text, 'failed probe claimed success'
                else:
                    assert result.returncode == 0, definition['name'] + ': baseline/restore failed'
                    if summary:
                        assert summary.get('fail') == 0 and summary.get('tests', 0) == summary.get('pass'), 'not all baseline cases passed'
                        if baseline_summary is None:
                            baseline_summary = summary
                        else:
                            assert summary == baseline_summary, 'restored summary differs'
                    else:
                        assert 'R356_PREFLIGHT_PASS' in text, 'missing completion marker'
            record['verdict'] = 'killed-by-named-assertion-and-restored'
        for name, content in sources.items():
            assert (ROOT / name).read_bytes() == content, 'runner changed worktree source'
        receipt['status'] = 'pass'
    except BaseException as error:
        receipt['status'] = 'failed'
        receipt['error'] = str(error)
        raise
    finally:
        (output / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(output / 'receipt.json')


if __name__ == '__main__':
    main()
