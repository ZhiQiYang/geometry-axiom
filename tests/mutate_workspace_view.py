"""H-116-VIEW/1 named withdrawals: real green -> tagged red -> restored green.

Each native variant is compiled from an isolated compiler-discovered include
closure. Compilation failures, crashes, skips and unrelated failures are not
kills. Builds and raw receipts are kept under --output outside the repository.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = 'geometry-web/workspace_view_bridge.inc'
TEST = 'tests/test_workspace_view.py'
sys.path.insert(0, str(ROOT))
from tests.test_timber_edit import Session


def case(name):
    return 'WorkspaceViewNative.test_' + name


MUTATIONS = [
    ('R11-V01-typed-owner', BRIDGE, '.root={wv_kind(kind),id}', '.root={wv_kind(kind),0}',
     case('native_typed_roots_owner_and_holes'), 'typed_root_ids'),
    ('R11-V02-top-frame', BRIDGE, '{1,0,0},{0,-1,0}', '{1,0,0},{0,1,0}',
     case('top_bottom_and_degenerate_face_use_same_native_frames'), 'top_is_not_bottom'),
    ('R11-V03-single-root-mask', BRIDGE,
     'if(wv_same(out->owner.root,out->config->hidden[i]))return false;',
     'if(false&&wv_same(out->owner.root,out->config->hidden[i]))return false;',
     case('hide_one_root_filters_drawing_and_pick_without_hiding_class_or_dependencies'), 'hidden_drawing'),
    ('R11-V04-hole-pick', BRIDGE,
     'if(wv_contains(points,count,out->point,true)&&wv_same(out->hit.root,out->owner.root))',
     'if(false&&wv_contains(points,count,out->point,true)&&wv_same(out->hit.root,out->owner.root))',
     case('native_typed_roots_owner_and_holes'), 'hole_not_bbox'),
    ('R11-V05-revision-key', BRIDGE,
     'if(revision!=g_definition_revision||!key||key->revision!=g_definition_revision)', 'if(!key)',
     case('key_scope_session_revision_and_readonly'), 'revision_pick_guard'),
    ('R11-V06-outline-bbox', BRIDGE,
     'if(count>POLY_MAX_VERTICES)return false;',
     'if(count>POLY_MAX_VERTICES)return false;ViewBounds box={0};for(size_t i=0;i<count;++i)view_bounds_add(&box,points[i]);return point.x>=box.min_x&&point.x<=box.max_x&&point.y>=box.min_y&&point.y<=box.max_y;',
     case('concave_outline_is_not_its_projected_bounding_box'), 'outline_not_bbox'),
    ('R11-V07-session-key', BRIDGE,
     'if(!g_workspace_view_nonce[0]&&!timber_edit_random_key(g_workspace_view_nonce))return NULL;',
     'if(!g_workspace_view_nonce[0]){memset(g_workspace_view_nonce,\'0\',64);g_workspace_view_nonce[64]=0;}',
     case('key_scope_session_revision_and_readonly'), 'session_key_guard'),
    ('R11-V08-transport-schema', 'geometry-web/workspace_view_transport.py',
     '        _validate(data, pick)', '        pass  # deliberate withdrawal of schema validation',
     'WorkspaceViewTransport.test_bounded_closed_server_generated_path_and_cleanup', 'transport_reject_before_bridge'),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, cwd, log, env=None):
    try:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=180)
        record = {'command': command, 'cwd': str(cwd), 'returncode': result.returncode,
                  'stdout': result.stdout, 'stderr': result.stderr}
    except (OSError, subprocess.TimeoutExpired) as error:
        record = {'command': command, 'cwd': str(cwd), 'returncode': None, 'error': str(error)}
    log.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return record


def capacity_probe(binary, directory):
    """A declared one-op service must reject even a complete empty three-view."""
    session = Session(binary)
    try:
        assert session.command('reset')['ok']
        before = session.command('dump')
        assert session.command('view-capabilities')['workspace_view']['maxOps'] == 1
        request = {'schema': 'workspace-view/1', 'expectedRevision': str(before['revision']),
                   'scope': {'kind': 'project'}, 'presentation': {'mode': 'three', 'focus': None},
                   'layers': [], 'hidden': []}
        path = directory / 'capacity-request.json'; path.write_text(json.dumps(request), encoding='utf-8')
        reply = session.command('view-read ' + str(path))
        assert reply['status'] == 'CAPACITY' and reply['viewKey'] is None, 'KILLER[ops_capacity]'
        assert reply['layout'] is None and reply['ops'] == [], 'KILLER[no_truncated_ready]'
        assert session.command('dump') == before, 'KILLER[capacity_readonly]'
        (directory / 'capacity-receipts.json').write_text(json.dumps({
            'binary_sha256': sha(binary), 'receipts': session.receipts}, ensure_ascii=False, indent=2), encoding='utf-8')
    finally:
        session.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--only', action='append', choices=[item[0] for item in MUTATIONS])
    args = parser.parse_args()
    output = (args.output or Path(tempfile.mkdtemp(prefix='geometry-view-mutations-'))).resolve()
    if output == ROOT or ROOT in output.parents:
        raise SystemExit('Mutation output must stay outside the repository')
    output.mkdir(parents=True, exist_ok=True)
    source = output / 'source'
    if source.exists():
        raise SystemExit('Use a new output directory; evidence is never overwritten')
    compiler = shlex.split(os.environ.get('CC', 'cc'))
    dependencies = subprocess.run(compiler + ['-std=c11', '-MM', 'geometry-web/web_bridge.c'], cwd=ROOT,
                                  capture_output=True, text=True, check=True).stdout
    names = set(shlex.split(dependencies.replace('\\\n', ' ').split(':', 1)[1]))
    names.update({TEST, 'tests/test_timber_edit.py', 'tests/__init__.py', 'geometry-web/workspace_view_transport.py'})
    for name in sorted(names):
        target = source / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    closure = {name: sha(source / name) for name in sorted(names)}
    (output / 'closure.json').write_text(json.dumps(closure, indent=2), encoding='utf-8')
    def build(binary, log, flags=()):
        return run(compiler + ['-std=c11', '-O0', *flags, 'geometry-web/web_bridge.c', '-lm', '-o', str(binary)], source, log)
    baseline = output / ('baseline.exe' if os.name == 'nt' else 'baseline')
    if build(baseline, output / 'baseline-build.json')['returncode'] != 0:
        raise SystemExit('Baseline compilation blocked')
    env = dict(os.environ, GEOMETRY_TEST_BRIDGE=str(baseline), GEOMETRY_VIEW_ORACLES=str(output / 'baseline-oracles.json'))
    env.pop('GEOMETRY_VIEW_RECEIPTS', None)
    baseline_run = run([sys.executable, TEST], source, output / 'baseline-tests.json', env)
    observed = json.loads((output / 'baseline-oracles.json').read_text())
    if baseline_run['returncode'] != 0 or observed['skipped'] or observed['errors']:
        raise SystemExit('Baseline tests failed or skipped; no mutations counted')
    capacity = output / ('capacity.exe' if os.name == 'nt' else 'capacity')
    if build(capacity, output / 'capacity-build.json', ['-DWV_OP_MAX=1'])['returncode'] != 0:
        raise SystemExit('Capacity build blocked')
    capacity_probe(capacity, output)
    results = []
    summary = {'schema': 'workspace-view-native-mutations/1', 'baseline_binary_sha256': sha(baseline),
               'closure_sha256': hashlib.sha256(json.dumps(closure, sort_keys=True).encode()).hexdigest(),
               'test_sha256': sha(source / TEST), 'capacity_verified': True, 'results': results}
    for name, filename, old, new, test, tag in MUTATIONS:
        if args.only and name not in args.only:
            continue
        directory = output / name; directory.mkdir()
        path = source / filename; original = path.read_bytes(); text = original.decode('utf-8')
        if text.count(old) != 1:
            raise SystemExit(name + ': mutation anchor must be unique')
        path.write_bytes(text.replace(old, new, 1).encode('utf-8'))
        binary = directory / ('mutant.exe' if os.name == 'nt' else 'mutant')
        record = {'name': name, 'test': test, 'oracle': tag, 'file': filename,
                  'before_sha256': hashlib.sha256(original).hexdigest(), 'mutant_source_sha256': sha(path),
                  'replacement': {'old': old, 'new': new}}
        try:
            compiled = build(binary, directory / 'build.json')
            if compiled['returncode'] != 0:
                record['status'] = 'blocked-compile'
            else:
                record['binary_sha256'] = sha(binary)
                oracle = directory / 'oracles.json'
                mutant_env = dict(env, GEOMETRY_TEST_BRIDGE=str(binary), GEOMETRY_VIEW_ORACLES=str(oracle))
                red = run([sys.executable, TEST, test], source, directory / 'red.json', mutant_env)
                counts = json.loads(oracle.read_text()) if oracle.is_file() else {}
                killed = (red['returncode'] == 1 and counts == {'tests': 1, 'failures': 1, 'errors': 0, 'skipped': 0} and
                          'KILLER[' + tag + ']' in red.get('stderr', ''))
                record['status'] = 'killed' if killed else 'survived-or-unrelated'
        finally:
            path.write_bytes(original); record['restored_source_sha256'] = sha(path)
        restored = directory / ('restored.exe' if os.name == 'nt' else 'restored')
        if build(restored, directory / 'restored-build.json')['returncode'] == 0:
            record['restored_binary_sha256'] = sha(restored)
            restored_env = dict(env, GEOMETRY_TEST_BRIDGE=str(restored), GEOMETRY_VIEW_ORACLES=str(directory / 'restored-oracles.json'))
            green = run([sys.executable, TEST, test], source, directory / 'restored-green.json', restored_env)
            record['restored_green'] = green['returncode'] == 0
        else:
            record['restored_green'] = False
        if not record['restored_green']:
            record['status'] = 'blocked-restore'
        results.append(record)
        (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print(name, record['status'], 'restore=' + str(record['restored_green']), flush=True)
    return 0 if all(item['status'] == 'killed' and item['restored_green'] for item in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
