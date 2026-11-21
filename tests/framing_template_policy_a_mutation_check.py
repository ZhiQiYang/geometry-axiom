"""Named policy A withdrawals over real native C and the actual bridge.

Each fresh baseline, withdrawn and restored executable is compiled from its
recorded include closure. Only a normal assertion failure with the named
killer is a kill; compiler errors, crashes and timeouts are blocked.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import binaries
from framing_template_mutation_check import compile_bridge, run

ROOT = Path(__file__).resolve().parents[1]
HEADER = 'geometry-templates/woodworking/native/flat_ceiling_jig.h'
BRIDGE = 'geometry-web/framing_template_bridge.inc'
CASES = {
    'R03A_FIXED_JIG': {
        'file': HEADER,
        'old': 'int64_t requested=anchor+dir*distance; /* R03A_LAST_TWO_STEPS_SPLIT */',
        'new': 'int64_t requested=anchor+dir*((L+n-1)/n)*j; /* withdrawn: per-cell equal split */',
        'test': 'test_A03_same_jig_and_last_two_step_collision_split',
        'marker': 'R03A_FIXED_JIG',
        'scope': 'Replace the ratified fixed jig with the old per-cell ceil split.'},
    'R03A_LAST_TWO_STEPS_SPLIT': {
        'file': HEADER,
        'old': 'distance=v->maximum*(n-2)+(v->maximum+remainder+1)/2;',
        'new': 'distance=v->maximum*(n-1); /* withdrawn: keep colliding last mark */',
        'test': 'test_A03_same_jig_and_last_two_step_collision_split',
        'marker': 'R03A_FIXED_JIG',
        'scope': 'Omit the existing oracle merge/split when the last jig mark intersects the end member.'},
    'R03A_REJECT_WRITES': {
        'file': BRIDGE,
        'old': 'if(!valid){eng_bridge_error("NATIVE_INVALID",',
        'new': 'if(!valid){ /* withdrawn rejection isolation: real World write */\n'
               '        history_record(&g_world);char write[]="spec r03a_rejected_write 1";\n'
               '        framing_template_line(&g_world,write);++g_definition_revision;\n'
               '        eng_bridge_error("NATIVE_INVALID",',
        'test': 'test_A04_rejected_candidate_cannot_write_any_formal_state',
        'marker': 'R03A_REJECT_WRITES',
        'scope': 'Write an ordinary spec and a history frame after the full native candidate has been rejected.'},
    'R03A_CONFIRM_DIFFERENT_CANDIDATE': {
        'file': BRIDGE,
        'old': 'identity_commit_serials();++g_definition_revision;g_preview.ready=false;g_framing_token=0;app_world_candidate_clear_stagger(g_preview.transaction);',
        'new': 'identity_commit_serials();++g_definition_revision;g_preview.ready=false;g_framing_token=0;app_world_candidate_clear_stagger(g_preview.transaction);\n'
               '    char unpreviewed[]="spec r03a_unpreviewed 9";framing_template_line(&g_world,unpreviewed);',
        'test': 'test_A05_cancel_exact_commit_one_history_and_cold_load',
        'marker': 'R03A_CONFIRM_DIFFERENT_CANDIDATE',
        'scope': 'Publish an unpreviewed ordinary definition during confirm; the preview/committed canonical fingerprints must differ.'},
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def assertion_kill(result, marker):
    """Require a completed unittest assertion failure, never an execution error."""
    stderr = result['stderr']
    if result['exit'] != 1 or marker not in stderr:
        return False
    if re.search(r'^ERROR:|\berrors=|\bskipped\b|NameError|TypeError|SyntaxError|ImportError|ModuleNotFoundError', stderr, re.MULTILINE):
        return False
    return (re.search(r'^AssertionError(?:\s*\[.*?\])?:', stderr, re.MULTILINE) is not None
            and re.search(r'^FAILED \(failures=[1-9][0-9]*\)\s*$', stderr, re.MULTILINE) is not None)


def successful_unittest(result):
    return (result['exit'] == 0
            and re.search(r'^Ran 1 test in ', result['stderr'], re.MULTILINE) is not None
            and re.search(r'^OK\s*$', result['stderr'], re.MULTILINE) is not None
            and not re.search(r'^ERROR:|\bskipped\b|\berrors=', result['stderr'], re.MULTILINE))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--only', choices=tuple(CASES))
    args = parser.parse_args()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    _, closure, compile_identity = binaries.compute_fingerprint(binaries.BY_NAME['bridge'])
    source_bytes = {name: (ROOT / name).read_bytes() for name in closure}
    for name in (HEADER, BRIDGE, 'tests/test_framing_template.py',
                 'tests/test_timber_edit.py', 'tests/framing_template_mutation_check.py',
                 'tests/framing_template_policy_a_mutation_check.py',
                 'geometry-core/framing-template/oracle/framing_oracle.py'):
        source_bytes[name] = (ROOT / name).read_bytes()
    report = {'schema': 'r03-policy-a-native-withdrawals/1',
              'checkoutHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'sourceSha256': {name: digest(data) for name, data in sorted(source_bytes.items())},
              'registryCompileIdentity': compile_identity,
              'cases': []}
    for name, case in CASES.items():
        if args.only and args.only != name:
            continue
        original = source_bytes[case['file']]
        old, new = case['old'].encode(), case['new'].encode()
        if original.count(old) != 1:
            raise RuntimeError('BLOCKED: mutation anchor must occur exactly once: ' + name)
        row = {'name': name, 'scope': case['scope'], 'file': case['file'],
               'killer': case['marker'], 'phases': []}
        with tempfile.TemporaryDirectory(prefix='r03a-native-withdraw-') as scratch:
            directory = Path(scratch)
            for rel, data in source_bytes.items():
                target = directory / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            target = directory / case['file']
            for phase in ('baseline', 'withdrawn', 'restored'):
                target.write_bytes(original.replace(old, new) if phase == 'withdrawn' else original)
                binary = directory / (phase + '-bridge')
                compilation = compile_bridge(directory, binary)
                env = dict(os.environ, GEOMETRY_TEST_BRIDGE=str(binary),
                           GEOMETRY_FRAMING_RECEIPTS=str(args.out / name / phase))
                command = [sys.executable, str(ROOT / 'tests/test_framing_template.py'),
                           'FramingTemplatePolicyA.' + case['test'], '-v']
                result = run(command, env=env)
                accepted = assertion_kill(result, case['marker']) if phase == 'withdrawn' else successful_unittest(result)
                if not accepted:
                    raise RuntimeError('NOT 0/1/0: ' + name + ' ' + phase + ' ' + json.dumps(result))
                row['phases'].append({'phase': phase, 'sourceSha256': digest(target.read_bytes()),
                                      'binarySha256': digest(binary.read_bytes()),
                                      'compile': compilation, 'test': result})
            if target.read_bytes() != original:
                raise RuntimeError('BLOCKED: restored source differs: ' + name)
        row['result'] = [p['test']['exit'] for p in row['phases']]
        report['cases'].append(row)
        (args.out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(name + ': 0 / 1 / 0', flush=True)
    for rel, data in source_bytes.items():
        if (ROOT / rel).read_bytes() != data:
            raise RuntimeError('BLOCKED: source changed during proof: ' + rel)
    print('Actual native executions complete; working-tree sources unchanged.', flush=True)


if __name__ == '__main__':
    main()
