"""Compile and exercise all actual product translation units with shared K/W."""
import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_product import SCENE

class NativeEntrypoints(unittest.TestCase):
    def scene(self,text,name):
        path=native().work/name;path.write_text(text,encoding='utf-8');return path
    def snapshot(self,path):
        run=subprocess.run([str(native().model_base()),str(path)],capture_output=True,text=True,encoding='utf-8',timeout=20)
        self.assertEqual(0,run.returncode,run.stderr);data=json.loads(run.stdout);self.assertTrue(data['ok'],data);return data
    def test_real_cli_compiles_and_renders_the_shared_member_scene(self):
        build=native();path=self.scene(SCENE,'entrypoints.scene');svg=build.work/'entrypoints.svg'
        run=subprocess.run([str(build.cli()),'--no-window','--scene',str(path),'--out',str(svg)],capture_output=True,text=True,encoding='utf-8',timeout=20)
        self.assertEqual(0,run.returncode,run.stderr);self.assertTrue(svg.is_file())
        text=svg.read_text(encoding='utf-8');self.assertIn('<svg',text);self.assertIn('角材1',text)
    def test_model_base_preserves_exact_rc_face_walk_and_legacy_shape(self):
        fixture=(ROOT/'_ax_r12_prefix_beam.scene').read_text(encoding='utf-8')
        scene='\n'.join(line for line in fixture.splitlines() if line.startswith(('surface ','space ','column ')))+'\n'
        data=self.snapshot(self.scene(scene,'entrypoints-rc.scene'))
        self.assertEqual({'ok','schema','base_scene','required_capabilities','specs','placements','solids','profile_runs','unplaced_timbers','dependencies'},set(data))
        self.assertEqual('geometry-base-snapshot/1',data['schema']);solid=data['solids'][0]
        self.assertEqual(('column',2),(solid['kind'],solid['id']))
        expected=[
            [[1000,1000,0],[1000,1000,2500],[1000,1400,2500],[1000,1400,0]],
            [[1400,1000,0],[1400,1400,0],[1400,1400,2500],[1400,1000,2500]],
            [[1000,1000,0],[1400,1000,0],[1400,1000,2500],[1000,1000,2500]],
            [[1000,1400,0],[1000,1400,2500],[1400,1400,2500],[1400,1400,0]],
            [[1000,1000,0],[1000,1400,0],[1400,1400,0],[1400,1000,0]],
            [[1000,1000,2500],[1400,1000,2500],[1400,1400,2500],[1000,1400,2500]],
        ]
        self.assertEqual(['-X','+X','-Y','+Y','-Z','+Z'],[face['feature'] for face in solid['faces']])
        self.assertEqual(expected,[face['vertices'] for face in solid['faces']])
    def test_real_bridge_and_model_base_share_identical_canonical_definitions(self):
        path=self.scene(SCENE,'entrypoints-shared.scene');snapshot=self.snapshot(path)
        with _bridge.BridgeSession(native().bridge()) as bridge:
            result=bridge.command('loadfile '+str(path));self.assertTrue(result['ok'],result)
            dump=bridge.command('dump')['text'];canonical='\n'.join(line for line in dump.splitlines() if not line.startswith('#')).rstrip()+'\n'
            self.assertEqual(snapshot['base_scene'],canonical)
            self.assertEqual(6,len(snapshot['solids'][0]['faces']))
            self.assertEqual(1,bridge.command('objects')['timbers'][0]['priority'])
if __name__=='__main__':unittest.main(verbosity=2)
