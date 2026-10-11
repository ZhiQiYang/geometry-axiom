"""Remove the whole #198 production fix, require named failures, then restore.

Run only without concurrent tests/builds/services in this checkout.
The two source files are always restored byte-for-byte in finally; builds and
logs are kept under TEMP, and neither tests nor their assertions are changed.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
import binaries

BASE = '635dd86ee368579aec444fb3ba16e48bccf4877e'
FILES = ('current_geometry.c', 'geometry-web/web_bridge.c')
TARGETS = ['tests.test_reference_contract.ReferenceContract.' + name for name in (
    'test_rect_outline_counterexample_A_rejects_disconnected_contact',
    'test_rect_outline_counterexample_B_clips_ridge_and_applies_split',
    'test_rect_outline_strip_reclassification_uses_exact_contact',
    'test_rect_outline_real_hole_no_contact_and_notch_controls',
    'test_rect_outline_unselected_complex_column_does_not_block_valid_item')]


def main():
    directory = Path(sys.argv[1]).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    saved = {name:(ROOT/name).read_bytes() for name in FILES}
    results = {}
    original_out = binaries.OUT_DIR
    try:
        for phase in ('removed', 'restored'):
            for name in FILES:
                data = subprocess.check_output(['git','show',BASE+':'+name], cwd=ROOT) if phase=='removed' else saved[name]
                (ROOT/name).write_bytes(data)
            binaries.OUT_DIR = Path('/tmp/geometry-198-remove-fix') / phase
            with (directory/(phase+'-build.log')).open('w') as log:
                with binaries.ProcessLock('build'):
                    built = binaries.build(('core','bridge','integrity'), log=lambda line: print(line,file=log))
            assert all(result.ok for result in built.values()), built
            env = dict(os.environ, GEOMETRY_TEST_BRIDGE=str(binaries.BY_NAME['bridge'].path))
            commands = {'native':[str(binaries.BY_NAME['integrity'].path)],
                        'bridge':[sys.executable,'-m','unittest',*TARGETS],
                        'scenes':[sys.executable,'tests/run_tests.py',str(binaries.BY_NAME['core'].path)]}
            results[phase] = {'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in FILES},
                              'binary_sha256':{n:hashlib.sha256(binaries.BY_NAME[n].path.read_bytes()).hexdigest()
                                               for n in ('core','bridge','integrity')},
                              'base':BASE, 'runs':{}}
            for kind, cmd in commands.items():
                proc = subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=300)
                (directory/(phase+'-'+kind+'.log')).write_text(proc.stdout+proc.stderr)
                results[phase]['runs'][kind] = {'argv':cmd,'cwd':str(ROOT),'exit':proc.returncode}
                assert proc.returncode == (1 if phase=='removed' else 0), (phase,kind,proc.returncode)
            if phase=='removed':
                native = (directory/'removed-native.log').read_text()
                bridge = (directory/'removed-bridge.log').read_text()
                scenes = (directory/'removed-scenes.log').read_text()
                assert 'counterexample_A < 0' in native and 'counterexample_B > 0' in native
                assert 'FAIL: test_rect_outline_counterexample_A' in bridge and 'FAIL: test_rect_outline_counterexample_B' in bridge
                rows = [line.removeprefix('GEOMETRY_TEST_RESULT ') for line in scenes.splitlines()
                        if line.startswith('GEOMETRY_TEST_RESULT ')]
                outcomes = {case['scene']:case['status'] for case in json.loads(rows[0])['cases']}
                assert outcomes['_ax_r7_notch_disconnected.scene']=='fail' and outcomes['_ax_r7_ridge_crossing.scene']=='fail'
    finally:
        for name,data in saved.items():
            (ROOT/name).write_bytes(data)
        binaries.OUT_DIR = original_out
        (directory/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print('Whole-fix removal: native/bridge/scene assertions red; restored: all three green.')


if __name__ == '__main__':
    main()
