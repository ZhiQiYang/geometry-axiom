"""Named R03 withdrawals against actual C product sources, in isolated copies.

Four generation properties execute the production W header without a mock.
The cancel property executes the complete bridge and real World/history test.
Each case must be 0/1/0. Compiler errors, process errors and timeouts are blocked
evidence, never a kill. No source, golden, SSOT or registry binary is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
HEADER = 'geometry-templates/woodworking/native/flat_ceiling.h'
BRIDGE = 'geometry-web/framing_template_bridge.inc'
PROBE = r'''
#include <stdio.h>
#include "flat_ceiling.h"
int main(int argc,char **argv) {
    int64_t width=argc>1?strtoll(argv[1],NULL,10):3740;
    int64_t height=argc>2?strtoll(argv[2],NULL,10):2000;
    int64_t bounds[4]={0,0,width,height};
    WoodFlatParameters params={{915,1830},2,27,33,367,1,{false,false}};
    WoodFlatPlan plan;bool ok=wood_flat_build(bounds,&params,&plan);
    printf("{\"ok\":%s,\"code\":\"%s\",\"seams\":[",ok?"true":"false",plan.code?plan.code:"");
    for(int axis=0;axis<2;++axis) {
        printf("%s[",axis?",":"");
        for(size_t k=0;k<plan.seam_count[axis];++k)printf("%s%lld",k?",":"",(long long)plan.seams[axis][k]);
        putchar(']');
    }
    printf("],\"marks\":[");
    for(size_t k=0;k<plan.mark_count;++k)printf("%s%lld",k?",":"",(long long)plan.marks[k]);
    printf("],\"members\":[");
    for(size_t k=0;k<plan.count;++k) {
        const WoodFlatMember *m=&plan.members[k];
        printf("%s[%d,%d,%lld,%lld,%lld,%lld]",k?",":"",m->kind,m->axis,
            (long long)m->rect[0],(long long)m->rect[1],(long long)m->rect[2],(long long)m->rect[3]);
    }
    puts("]}");return 0;
}
'''

CASES = {
    'R03_MAIN_CONTINUOUS': {
        'file': HEADER,
        'old': 'wood_flat_add_ab(p,1,b,a,low,B0+w,high,B1-w,c)',
        'new': 'wood_flat_add_ab(p,1,b,a,low,B0+w,high,(B0+B1)/2,c)',
        'scope': 'production C generation: a main ends midway instead of reaching the opposite boundary member'},
    'R03_NOT_CENTERED': {
        'file': HEADER,
        'old': 'p->origin[axis]=v->start_max[axis]?hi-size:lo;',
        'new': 'p->origin[axis]=v->start_max[axis]?hi-size:lo; lo+=(D%pitch)/2; hi+=(D%pitch)/2;',
        'scope': 'production C generation: translate the starting edge by half the panel remainder'},
    'R03_ONLY_OPPOSITE_WALL_TRIM': {
        'file': HEADER,
        'old': 'return wood_flat_fail(p,"POLICY_RULE_CONFLICT","此起鋪需要退最後板縫，會裁切不在對牆的板；未套用舊 oracle 退縫");',
        'new': 'distance=(2*D-3*w)/2;',
        'scope': 'production C generation: adopt historical last-seam retreat, cutting the penultimate panel'},
    'R03_CEIL_MARKS': {
        'file': HEADER,
        'old': 'int64_t n=(L+v->maximum-1)/v->maximum; /* R03_CEIL_N */',
        'new': 'int64_t n=L/v->maximum; /* withdrawn ceil: floor_n */',
        'scope': 'production C generation: floor cell count changes/removes required marks'},
    'R03_CANCEL_ZERO_WRITE': {
        'file': BRIDGE,
        'old': 'if(cancel){ /* R03_CANCEL_ZERO_WRITE */',
        'new': 'if(cancel){ /* withdrawn cancel isolation */\n'
               '        history_record(&g_world);\n'
               '        if(app_world_candidate_revalidate(g_preview.transaction,&g_world) && app_world_candidate_publish(g_preview.transaction,&g_world,true)){identity_commit_serials();++g_definition_revision;}',
        'scope': 'complete native bridge: cancel publishes the candidate and records history'},
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(command, *, env=None, timeout=60, cwd=None):
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=cwd or ROOT, env=env, capture_output=True,
                                text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError) as error:
        raise RuntimeError(f'BLOCKED, not killed: {command!r}: {error}') from error
    return {'command': list(map(str, command)), 'exit': result.returncode,
            'seconds': round(time.monotonic() - started, 6),
            'stdout': result.stdout, 'stderr': result.stderr}


def check_case(name, binary):
    width = '3700' if name == 'R03_ONLY_OPPOSITE_WALL_TRIM' else '3740'
    result = run([str(binary), width, '2000'])
    if result['exit']:
        raise RuntimeError('BLOCKED C probe: ' + json.dumps(result))
    output = json.loads(result['stdout'])
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    if name == 'R03_ONLY_OPPOSITE_WALL_TRIM':
        assert not output['ok'] and output['code'] == 'POLICY_RULE_CONFLICT', name
        return
    assert output['ok'], name + ': a legal complete baseline may not be discarded'
    if name == 'R03_MAIN_CONTINUOUS':
        mains = [r for r in output['members'] if r[0] == 1]
        assert len(mains) == 4 and all(r[3] == 27 and r[5] == 1973 for r in mains), name
    elif name == 'R03_NOT_CENTERED':
        assert output['seams'] == [[916, 1833, 2750, 3667], [1831]], name
    elif name == 'R03_CEIL_MARKS':
        assert output['marks'] == [363, 730, 1097, 1464], name


def compile_probe(directory, output):
    probe = directory / 'probe.c'
    probe.write_text(PROBE, encoding='ascii')
    command = [os.environ.get('CC', 'cc'), '-std=c11', '-O2', '-I', str(directory), str(probe), '-o', str(output)]
    report = run(command, timeout=60)
    if report['exit'] or not output.exists():
        raise RuntimeError('BLOCKED compile, not killed: ' + json.dumps(report))
    return report


def compile_bridge(directory, output):
    # This standalone evidence build intentionally uses -O0 for all three
    # phases. The registry -O2 binary is separately exercised by the full suite.
    command = [os.environ.get('CC', 'cc'), '-std=c11', '-O0',
               str(directory / 'geometry-web/web_bridge.c'), '-o', str(output), '-lm']
    report = run(command, timeout=900, cwd=directory)
    if report['exit'] or not output.exists():
        raise RuntimeError('BLOCKED compile, not killed: ' + json.dumps(report))
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path)
    parser.add_argument('--only', choices=tuple(CASES))
    parser.add_argument('--check-case', choices=tuple(CASES))
    parser.add_argument('--binary', type=Path)
    args = parser.parse_args()
    if args.check_case:
        check_case(args.check_case, args.binary)
        return
    if args.out is None:
        parser.error('--out is required for immutable evidence')
    args.out.mkdir(parents=True, exist_ok=True)
    import binaries
    _, closure, compile_identity = binaries.compute_fingerprint(binaries.BY_NAME['bridge'])
    # Read actual include closure and input bytes; gitignore cannot omit W.
    source_bytes = {name: (ROOT / name).read_bytes() for name in closure}
    source_bytes[HEADER] = (ROOT / HEADER).read_bytes()
    source_bytes[BRIDGE] = (ROOT / BRIDGE).read_bytes()
    for rel in ('tests/test_framing_template.py', 'tests/test_timber_edit.py',
                'geometry-core/framing-template/oracle/framing_oracle.py'):
        source_bytes[rel] = (ROOT / rel).read_bytes()
    report = {'schema': 'r03-native-withdrawals/1',
              'base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'test_sha256': digest((ROOT / 'tests/test_framing_template.py').read_bytes()),
              'driver_sha256': digest(Path(__file__).read_bytes()),
              'registry_compile_identity': compile_identity,
              'source_sha256': {name: digest(data) for name, data in sorted(source_bytes.items())},
              'cases': []}
    for name, case in CASES.items():
        if args.only and name != args.only:
            continue
        original = source_bytes[case['file']]
        old, new = case['old'].encode(), case['new'].encode()
        if original.count(old) != 1:
            raise RuntimeError(f'BLOCKED: mutation target {name} does not match exactly once')
        row = {'name': name, 'scope': case['scope'], 'file': case['file'],
               'baseline_source_sha256': digest(original), 'mutant_source_sha256': digest(original.replace(old, new)),
               'phases': []}
        with tempfile.TemporaryDirectory(prefix='r03-withdraw-') as scratch:
            directory = Path(scratch)
            if name == 'R03_CANCEL_ZERO_WRITE':
                for rel, data in source_bytes.items():
                    target = directory / rel; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
                target = directory / case['file']
            else:
                target = directory / 'flat_ceiling.h'
            for phase in ('baseline', 'withdrawn', 'restored'):
                target.write_bytes(original.replace(old, new) if phase == 'withdrawn' else original)
                binary = directory / f'{phase}-bridge'
                compile_report = (compile_bridge if name == 'R03_CANCEL_ZERO_WRITE' else compile_probe)(directory, binary)
                env = dict(os.environ)
                if name == 'R03_CANCEL_ZERO_WRITE':
                    env['GEOMETRY_TEST_BRIDGE'] = str(binary)
                    env['GEOMETRY_FRAMING_RECEIPTS'] = str((args.out / name / phase).resolve())
                    result = run([sys.executable, str(ROOT / 'tests/test_framing_template.py'),
                                  'FramingTemplateNative.test_N03_cancel_leaves_every_formal_value_unchanged', '-v'], env=env)
                else:
                    result = run([sys.executable, str(Path(__file__).resolve()), '--check-case', name, '--binary', str(binary)])
                expected = 1 if phase == 'withdrawn' else 0
                if result['exit'] != expected or phase == 'withdrawn' and name not in result['stderr']:
                    raise RuntimeError('NOT 0/1/0: ' + name + ' ' + phase + ' ' + json.dumps(result))
                row['phases'].append({'phase': phase, 'source_sha256': digest(target.read_bytes()),
                    'binary_sha256': digest(binary.read_bytes()), 'compile': compile_report, 'test': result})
            assert target.read_bytes() == original
        row['result'] = [p['test']['exit'] for p in row['phases']]
        report['cases'].append(row)
        (args.out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(name + ': 0 / 1 / 0', flush=True)
    for rel, data in source_bytes.items():
        if (ROOT / rel).read_bytes() != data:
            raise RuntimeError('BLOCKED: source changed during proof: ' + rel)
    print('No source was mutated in the working tree.', flush=True)


if __name__ == '__main__':
    main()
