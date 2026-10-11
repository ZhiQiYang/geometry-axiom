"""Capture #198 native/bridge counterexamples and the existing scene oracle."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
from tests import _bridge
import run_tests


def capture(directory):
    directory.mkdir(parents=True, exist_ok=True)
    records = []
    for name, outline, column in [
        ('A', '0,0 100,0 100,100 60,100 60,40 40,40 40,100 0,100', '30 50 size 40 30'),
        ('B', '0,0 100,0 100,50 60,50 60,90 40,90 40,50 0,50', '20 70 size 60 10')]:
        with _bridge.BridgeSession() as session:
            commands = ['reset', 'line surface 1 origin 0 0 0 u +x v +y outline ' + outline,
                        'line column 1 at ' + column + ' z 0 100', 'dump', 'obstacles 1',
                        'line apply-proj 1 c1', 'dump']
            records.append({'name': name, 'commands': [
                {'input': cmd, 'output': session.send(cmd)} for cmd in commands]})
    core = _bridge.binaries.require_fresh('core', _bridge.binaries.BY_NAME['core'].path)
    identity = {'head': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
                'tree': subprocess.check_output(['git','rev-parse','HEAD^{tree}'], cwd=ROOT, text=True).strip(),
                'source_sha256': hashlib.sha256((ROOT/'current_geometry.c').read_bytes()).hexdigest(),
                'core_sha256': hashlib.sha256(Path(core).read_bytes()).hexdigest(),
                'bridge_sha256': hashlib.sha256(Path(_bridge.find_bridge()).read_bytes()).hexdigest(),
                'platform': sys.platform, 'note': 'Source and test edits may be uncommitted; hashes and raw inputs bind this run.'}
    (directory / 'probe.json').write_text(json.dumps({'identity':identity,'cases':records}, ensure_ascii=False, indent=2)+'\n')
    scenes = {spec['scene']: run_tests.run_one(str(core), spec) for spec in run_tests.TESTS}
    (directory / 'scenes.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'identity':identity, 'scene_count':len(scenes), 'failed_scenes':{
        n:v for n,v in scenes.items() if v != 'ok'}}, ensure_ascii=False))


if __name__ == '__main__':
    capture(Path(sys.argv[1]))
