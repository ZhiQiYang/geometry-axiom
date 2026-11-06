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
    'geometry-core/interval-allocation.js',
    'geometry-app/application.js',
    'geometry-templates/woodworking/cutting.js',
    'geometry-templates/woodworking/frontend.js',
    'geometry-web/app.js',
    'geometry-web/engineering-workspace.js',
    'geometry-web/section-profile-workspace.js',
    'geometry-web/assembly-workspace.js',
    'geometry-web/project-store.js',
    'geometry-web/scenario-catalog.js',
    'geometry-web/context-operations.js',
    'geometry-web/vendor/fflate/umd/index.js',
    'geometry-web/grid-system-workspace.js',
    'geometry-web/feature-attachments.js',
    'geometry-web/cutting-settings.js',
    'geometry-web/source-plane.js',
    'geometry-web/reference-display.js',
    'geometry-web/evidence-links.js',
    'geometry-web/rule-case-data.js',
    'geometry-web/runtime_version.py',
    'tests/test_woodworking_frontend.js',
    'tests/test_grid_definition_diagram.js',
    'tests/test_runtime_version.py',
    'tests/test_assembly_workspace.js',
    'tests/test_draw_annotation.js',
)
SUITES = {
    'recipes': (['node', '--test', '--test-reporter=tap', 'tests/test_woodworking_frontend.js'], 17),
    'assembly': (['node', '--test', '--test-reporter=tap', 'tests/test_assembly_workspace.js'], 52),
    'annotation': (['node', '--test', '--test-reporter=tap', 'tests/test_draw_annotation.js'], 7),
    'grid': (['node', '--test', '--test-reporter=tap', 'tests/test_grid_definition_diagram.js'], 13),
    'runtime': ([sys.executable, 'tests/test_runtime_version.py'], 31),
}
MUTATIONS = (
    ('annotation-parses-label', 'annotation', 'geometry-web/app.js',
     'annotation = o.annotation;',
     "annotation = (()=>{const m=String(o.t).match(/^(角材\\s*(\\d+))\\s+(A[01]|B[01]|START|END)$/);return m?{kind:'member-face',entityId:Number(m[2]),faceId:m[3],shortLabel:m[1]}:null;})();",
     'member identity survives translated labels'),
    ('instance-bypasses-recipe', 'assembly', 'geometry-web/assembly-workspace.js',
     'GeometryApplication.woodworking.assemblyInstanceMembers(rule.value)',
     "((r)=>{if(r.members.length!==3||r.joints.length!==2||r.joints.some(j=>j.kind!=='end-to-side')||r.joints[0].terminatedMember!==r.joints[1].terminatedMember)throw Error('首版只支援兩支主支與一支端接副支。');const sec=r.joints[0].terminatedMember,start=r.joints.find(j=>j.end==='start'),finish=r.joints.find(j=>j.end==='finish');if(!start||!finish)throw Error('副支必須有起端與末端接合。');return r.members.map(m=>({memberId:m.id,role:m.id===sec?'secondary':'primary',guideId:0,dir:m.id===sec?'+u':'+v',depthSide:'+n',ends:m.id===sec?{start:{kind:'member',memberId:start.targetMember},finish:{kind:'member',memberId:finish.targetMember}}:{start:{kind:'timber',id:0},finish:{kind:'timber',id:0}}}));})(rule.value)",
     'actual instance creation consumes the template before ID allocation'),
    ('retarget-bypasses-endpoint-policy', 'assembly', 'geometry-web/assembly-workspace.js',
     'GeometryApplication.woodworking.assemblyInstanceEnd(r.value,k)',
     "({kind:'member',memberId:r.value.joints.find(j=>j.end===k).targetMember})",
     'actual binding switch consumes injected compatibility and endpoint policies'),
    ('instance-secondary-direction-changed', 'recipes', 'geometry-templates/woodworking/frontend.js',
     "dir: member.id === secondary ? '+u' : '+v'", "dir: member.id === secondary ? '+v' : '+v'",
     'assembly creation preserves typed roles, directions and endpoint sources'),
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
     "for directory in ('geometry-web', 'geometry-core', 'geometry-kernel', 'geometry-app', 'geometry-templates'):",
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
        failed_names = re.findall(r'^FAIL: (.+)$', text, re.MULTILINE)
    else:
        counts = re.search(r'(?:#|ℹ) tests (\d+)', text)
        failures = re.search(r'(?:#|ℹ) fail (\d+)', text)
        skips = re.search(r'(?:#|ℹ) skipped (\d+)', text)
        fail_count = int(failures.group(1)) if failures else -1
        assertion_count = len(re.findall(r"^\s+code: 'ERR_ASSERTION'\s*$", text, re.MULTILINE))
        error_count = max(0, fail_count - assertion_count)
        skipped = int(skips.group(1)) if skips else -1
        failed_names = re.findall(r'^not ok \d+ - (.+)$', text, re.MULTILINE)
    count = int(counts.group(1)) if counts else -1
    if count != expected:
        raise RuntimeError(f'{stem}: discovered {count}, expected {expected}; see {log}')
    return {'command': command, 'exit': run.returncode, 'discovered': count,
            'failures': fail_count, 'errors': error_count, 'skipped': skipped,
            'failedTests': failed_names,
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
                                          and result['errors'] == 0
                                          and any(failure_name in name for name in result['failedTests']))
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
