"""Independent #171 probe, deliberately separate from the owner's canonical test.

Run: python tests/integration/assembly_ownership_probe.py --out /tmp/unique-run
     [--root /path/to/repo] [--bridge /path/to/fresh/bridge]

Uses the candidate's existing Generation fixture, then tests all three reopened
members against I42's ownership diagnostic and complete state preservation.
No browser/product-open claim is made by this native-only probe.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capture_cleanup_errors(fixture, errors):
    """Retain exceptions that TestCase.doCleanups records instead of raising."""
    add_cleanup = fixture.addCleanup

    def record_cleanup(function, *args, **kwargs):
        def cleanup():
            try:
                return function(*args, **kwargs)
            except BaseException:
                errors.append(traceback.format_exc())
                raise
        add_cleanup(cleanup)

    fixture.addCleanup = record_cleanup


def recording_sessions(BridgeSession, out):
    sessions = []

    class RecordedSession(BridgeSession):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.index = len(sessions)
            self.events = []
            self.details = {'index': self.index, 'pid': self.process.pid,
                            'bridge': str(self.bridge), 'cwd': str(kw.get('cwd'))}
            sessions.append(self)

        def command(self, text):
            event = {'command': text, 'time': datetime.now(timezone.utc).isoformat()}
            if text.startswith(('assembly-preview ', 'assembly-generation-preview ')):
                event['transaction'] = Path(text.split(' ', 1)[1]).read_text()
            self.process.stdin.write(text + '\n')
            self.process.stdin.flush()
            raw = self.process.stdout.readline()
            event['stdout'] = raw
            self.events.append(event)
            (out / f'bridge-{self.index}.jsonl').write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in self.events))
            if not raw:
                raise AssertionError('bridge closed: ' + self.stderr_text())
            return json.loads(raw)

        def stop(self):
            if self._stopped:
                return
            self._stopped = True
            self.process.stdin.close()
            try:
                self.process.wait(timeout=self.stop_timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
                self.details['forced_stop'] = True
            self.details['exit_code'] = self.process.returncode
            (out / f'bridge-{self.index}.stderr').write_text(self.stderr_text())
            self.process.stdout.close()
            self.stderr.close()

    return RecordedSession, sessions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', '--repo', dest='repo', type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument('--bridge', type=Path, help='Registry-fresh native bridge; never built by this probe')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / 'tests'))
    import binaries
    from tests import _bridge
    from tests import test_assembly_generation as generation

    def git(*words):
        result = subprocess.run(['git', *words], cwd=root, capture_output=True)
        (out / ('git-' + '-'.join(words).replace('/', '_') + '.stdout')).write_bytes(result.stdout)
        (out / ('git-' + '-'.join(words).replace('/', '_') + '.stderr')).write_bytes(result.stderr)
        if result.returncode:
            raise RuntimeError(f'git {words} exited {result.returncode}')
        return result.stdout.decode()

    metadata = {'started': datetime.now(timezone.utc).isoformat(), 'argv': sys.argv,
                'cwd': os.getcwd(), 'repo': str(root), 'python': sys.version,
                'platform': platform.platform(), 'probe_sha256': sha(__file__),
                'head': git('rev-parse', 'HEAD').strip(),
                'main': git('rev-parse', 'origin/main').strip(),
                'pr171_head': git('rev-parse', 'origin/docs/save-reopen-contract-20261008').strip(),
                'dirty_status': git('status', '--short'),
                'fixture_sha256': sha(root / 'tests/test_assembly_generation.py'),
                'bridge_harness_sha256': sha(root / 'tests/_bridge.py')}
    dirty = git('diff', '--binary')
    (out / 'dirty.diff').write_text(dirty)
    metadata['dirty_diff_sha256'] = sha(out / 'dirty.diff')
    override = str(args.bridge.resolve()) if args.bridge else os.environ.get('GEOMETRY_TEST_BRIDGE')
    if override:
        os.environ['GEOMETRY_TEST_BRIDGE'] = override
    info = binaries.inspect_one(binaries.BY_NAME['bridge'], path=override) if override else binaries.inspect_one(binaries.BY_NAME['bridge'])
    metadata['binary_registry'] = dict(info.as_dict(), fingerprint=info.fingerprint)
    # Read-only freshness check: never compile implicitly inside this probe.
    if info.state != 'fresh':
        metadata['exit_code'] = 2
        metadata['blocked'] = 'No verified fresh bridge; ask the integration test owner to build it.'
        (out / 'result.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2, default=str) + '\n')
        return 2
    metadata['bridge_sha256'] = sha(info.path)
    sidecar = info.path.with_name(info.path.name + binaries.SIDECAR_SUFFIX)
    (out / 'bridge.fingerprint.json').write_bytes(sidecar.read_bytes())
    RecordedSession, sessions = recording_sessions(_bridge.BridgeSession, out)

    generation.BridgeSession = RecordedSession
    fixture = generation.Generation('test_roundtrip_preserves_sources_mapping_and_geometry_in_fresh_process')
    errors = []
    cleanup_errors = []
    capture_cleanup_errors(fixture, cleanup_errors)
    try:
        fixture.setUp()
        fixture.apply([fixture.create()])
        original_state = fixture.read()['state']
        instance = original_state['instances'][0]
        members = instance['members']
        assert len(members) == 3, members
        scene = fixture.dump()
        saved = out / 'reopened-owned.scene'
        saved.write_text(scene)
        metadata['scene_sha256'] = sha(saved)
        with RecordedSession(str(info.path), cwd=fixture.directory) as fresh:
            initial = fresh.command('assembly-read')
            assert initial['state']['instances'] == [], initial
            loaded = fresh.command('loadfile ' + str(saved))
            assert loaded['ok'], loaded
            before_dump = fresh.command('dump')
            before_read = fresh.command('assembly-read')
            assert before_dump['text'] == scene, 'Fresh load did not restore exact dump'
            assert before_read['state'] == original_state, 'Fresh load changed assembly state'
            metadata['members'] = []
            for member in members:
                tid = member['timberId']
                refused = fresh.command(f'line delete timber {tid}')
                assert refused['ok'] is False, refused
                # reference_stage preserves the native reason under actual;
                # its top-level error is the generic I8a preview wrapper.
                preview = refused['preview']
                assert preview['valid'] is False, refused
                reasons = [v.get('actual', '') for v in preview['violations']]
                assert any('I42: delete the owning assembly instance' in reason for reason in reasons), refused
                after_dump = fresh.command('dump')
                after_read = fresh.command('assembly-read')
                assert after_dump == before_dump, f'Dump changed after rejecting member {member["memberId"]}'
                assert after_read == before_read, f'Assembly/revision changed after rejecting member {member["memberId"]}'
                metadata['members'].append({'member_id': member['memberId'], 'timber_id': tid,
                                            'refusal': refused, 'dump_unchanged': True,
                                            'assembly_read_unchanged': True})
        metadata['passed'] = True
    except BaseException:
        errors.append(traceback.format_exc())
        metadata['passed'] = False
    finally:
        if not fixture.doCleanups():
            metadata['passed'] = False
            if not cleanup_errors:
                cleanup_errors.append('fixture.doCleanups() returned False without an exception traceback')
        metadata['cleanup_errors'] = cleanup_errors
        for session in sessions:
            try:
                session.stop()
            except BaseException:
                cleanup_errors.append(traceback.format_exc())
                metadata['passed'] = False
        metadata['sessions'] = [s.details for s in sessions]
        if any(s.details.get('exit_code') != 0 for s in sessions):
            metadata['passed'] = False
        metadata['errors'] = errors
        metadata['finished'] = datetime.now(timezone.utc).isoformat()
        metadata['exit_code'] = 0 if metadata['passed'] else 1
        metadata['head_after'] = git('rev-parse', 'HEAD').strip()
        if metadata['head_after'] != metadata['head']:
            metadata['passed'] = False
            metadata['exit_code'] = 1
            metadata['errors'].append('Integration HEAD moved while this probe ran')
        (out / 'result.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2, default=str) + '\n')
    print(json.dumps({'passed': metadata['passed'], 'exit_code': metadata['exit_code'],
                      'head': metadata['head'], 'out': str(out)}, ensure_ascii=False))
    return metadata['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())

