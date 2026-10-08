"""Native grid/rule/timber save-reset-reopen closure, with a no-op load control.

Uses the existing legal NativeSubdivisionOracle fixture. This does not claim
browser product-open or .gcanvas acceptance. The no-op control changes only the
probe's load callback, never the product or its native binary.

python tests/integration/grid_rule_reopen_probe.py --out /tmp/unique-run
"""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--bridge', type=Path, help='Registry-fresh bridge; never built by this probe')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / 'tests'))
    import binaries
    from tests import _bridge
    from tests import test_grid_subdivision_oracle as grid
    from tests.integration.assembly_ownership_probe import capture_cleanup_errors, recording_sessions, sha

    git_records = []

    def git(*words):
        result = subprocess.run(['git', *words], cwd=root, capture_output=True)
        stem = f'git-{len(git_records):02}'
        (out / (stem + '.stdout')).write_bytes(result.stdout)
        (out / (stem + '.stderr')).write_bytes(result.stderr)
        git_records.append({'argv': ['git', *words], 'exit_code': result.returncode,
                            'stdout': stem + '.stdout', 'stderr': stem + '.stderr'})
        if result.returncode:
            raise RuntimeError(f'git {words} exited {result.returncode}')
        return result.stdout.decode()

    metadata = {'started': datetime.now(timezone.utc).isoformat(), 'argv': sys.argv,
                'cwd': os.getcwd(), 'repo': str(root), 'python': sys.version,
                'platform': platform.platform(), 'probe_sha256': sha(__file__),
                'recorder_sha256': sha(root / 'tests/integration/assembly_ownership_probe.py'),
                'head': git('rev-parse', 'HEAD').strip(),
                'main': git('rev-parse', 'origin/main').strip(),
                'pr171_head': git('rev-parse', 'origin/docs/save-reopen-contract-20261008').strip(),
                'dirty_status': git('status', '--short'),
                'fixture_sha256': sha(root / 'tests/test_grid_subdivision_oracle.py'),
                'fixture_vectors_sha256': sha(grid.FIXTURE),
                'bridge_harness_sha256': sha(root / 'tests/_bridge.py')}
    (out / 'dirty.diff').write_text(git('diff', '--binary'))
    metadata['dirty_diff_sha256'] = sha(out / 'dirty.diff')
    override = str(args.bridge.resolve()) if args.bridge else os.environ.get('GEOMETRY_TEST_BRIDGE')
    info = binaries.inspect_one(binaries.BY_NAME['bridge'], path=override) if override else binaries.inspect_one(binaries.BY_NAME['bridge'])
    metadata['binary_registry'] = dict(info.as_dict(), fingerprint=info.fingerprint)
    if info.state != 'fresh':
        metadata.update(exit_code=2, blocked='No verified fresh bridge; build separately.')
        (out / 'result.json').write_text(json.dumps(metadata, indent=2, default=str) + '\n')
        return 2
    metadata['bridge_sha256'] = sha(info.path)
    (out / 'bridge.fingerprint.json').write_bytes(info.path.with_name(info.path.name + binaries.SIDECAR_SUFFIX).read_bytes())
    original_session = _bridge.BridgeSession
    RecordedSession, sessions = recording_sessions(original_session, out)
    _bridge.BridgeSession = RecordedSession
    fixture = grid.NativeSubdivisionOracle('test_direct_line_needs_real_support_and_complete_cell_scope_while_guide_is_coordinate_only')
    fixture.bridge = str(info.path)
    cleanup_errors = []
    capture_cleanup_errors(fixture, cleanup_errors)
    try:
        fixture.setUp()
        empty = fixture.snapshot()
        fixture.commit(fixture.source())
        fixture.commit(fixture.rule())
        fixture.boundary()
        fixture.binding()
        fixture.apply_grid()
        fixture.real_supports()
        fixture.commit('timber 10 20 20 role secondary')
        before_place = fixture.snapshot()
        fixture.commit('place 10 on 1 at-line rule 10 0 1 -2 1 v 0 between t1 t2 +u +n')
        placed = fixture.snapshot()
        fixture.assertEqual(400, fixture.timber(10)['geometry']['centerline'])
        fixture.assertEqual(540, fixture.timber(10)['geometry']['length'])
        fixture.assertIn('at-line rule 10 0 1 -2 1 v 0', placed[0])
        fixture.commit('undo')
        fixture.assertEqual(before_place, fixture.snapshot(), 'Placement undo lost definitions/references')
        fixture.commit('redo')
        fixture.assertEqual(placed, fixture.snapshot(), 'Placement redo lost definitions/references')

        # Existing anchor stays at (100,200); v cell pitch 600 puts its half-line
        # at 500. The same two real primary supports preserve length 540.
        fixture.commit(fixture.source(v='repeat 0 600'))
        modified = fixture.snapshot()
        fixture.assertNotEqual(placed, modified)
        fixture.assertEqual(500, fixture.timber(10)['geometry']['centerline'])
        fixture.assertEqual(540, fixture.timber(10)['geometry']['length'])
        fixture.assertIn('at-line rule 10 0 1 -2 1 v 0', modified[0])
        fixture.commit('undo')
        fixture.assertEqual(placed, fixture.snapshot(), 'Source undo lost definitions/references')
        fixture.commit('redo')
        fixture.assertEqual(modified, fixture.snapshot(), 'Source redo lost definitions/references')
        saved = out / 'grid-rule-timber.scene'
        saved.write_text(modified[0], encoding='utf-8')
        metadata['scene_sha256'] = sha(saved)
        metadata['snapshots'] = {'empty': empty, 'placed': placed, 'modified': modified}
        fixture.assertTrue(fixture.command('reset')['ok'])
        fixture.assertEqual(empty, fixture.snapshot(), 'Reset did not restore genuinely empty world')

        def reopen(load):
            loaded = load('loadfile ' + str(saved))
            fixture.assertTrue(loaded['ok'], loaded)
            fixture.assertEqual(modified, fixture.snapshot(), 'Reopen lost definitions/references')

        control = {'kind': 'observer callback substitution; not product mutation',
                   'skipped_command': 'loadfile ' + str(saved)}
        try:
            reopen(lambda command: {'ok': True, 'control': 'load deliberately skipped'})
        except AssertionError as error:
            control.update(detected=True, failure=str(error))
        else:
            raise AssertionError('No-op load control escaped the reopen oracle')
        metadata['no_op_load_control'] = control
        fixture.assertEqual(empty, fixture.snapshot(), 'Observer control changed native world')
        reopen(fixture.command)
        metadata['passed'] = True
    except BaseException:
        metadata.update(passed=False, error=traceback.format_exc())
    finally:
        if not fixture.doCleanups():
            metadata['passed'] = False
            if not cleanup_errors:
                cleanup_errors.append('fixture.doCleanups() returned False without an exception traceback')
        metadata['cleanup_errors'] = cleanup_errors
        for session in sessions:
            session.stop()
        _bridge.BridgeSession = original_session
        metadata['sessions'] = [s.details for s in sessions]
        if any(s.details['exit_code'] != 0 for s in sessions):
            metadata['passed'] = False
        metadata['head_after'] = git('rev-parse', 'HEAD').strip()
        if metadata['head_after'] != metadata['head']:
            metadata.update(passed=False, error='Integration HEAD moved during the probe')
        metadata['finished'] = datetime.now(timezone.utc).isoformat()
        metadata['exit_code'] = 0 if metadata['passed'] else 1
        metadata['git_commands'] = git_records
        (out / 'result.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2, default=str) + '\n')
    print(json.dumps({k: metadata[k] for k in ('passed', 'head', 'exit_code')}))
    return metadata['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
