"""Typed native draw metadata and the existing text-only backend contract."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native


class DrawAnnotation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native()
        obj=build.compile(ROOT/'tests/geo261_draw_annotation_harness.c','draw-annotation-client',['GEOMETRY_KERNEL_EXTERNAL=1','GEOMETRY_WOODWORKING_EXTERNAL=1'])
        cls.exe=build.link('draw-annotation-client',[obj,*build.product_objects()])

    def check(self,case):
        run=subprocess.run([str(self.exe),case],capture_output=True,text=True,timeout=10)
        self.assertEqual(0,run.returncode,run.stderr)

    def test_optional_callback_preserves_text_and_dispatches_only_once(self):self.check('fallback')
    def test_svg_backend_preserves_existing_full_text(self):self.check('svg')

    def render(self):
        with _bridge.BridgeSession(native().bridge()) as session:
            self.assertTrue(session.command('default')['ok'])
            rendered=session.command('render');self.assertTrue(rendered['ok'],rendered)
            return rendered['ops']

    def test_real_renderer_provides_identity_without_label_parsing(self):
        items=[op for op in self.render() if 'annotation' in op]
        self.assertTrue(items)
        for op in items:
            annotation=op['annotation']
            self.assertEqual('text',op['op'])
            self.assertEqual({'kind','entityId','faceId','shortLabel'},set(annotation))
            self.assertEqual('member-face',annotation['kind'])
            self.assertIsInstance(annotation['entityId'],int)
            self.assertIn(annotation['faceId'],{'A0','A1','B0','B1','START','END'})
            self.assertEqual('角材'+str(annotation['entityId']),annotation['shortLabel'])
            self.assertEqual(annotation['shortLabel']+' '+annotation['faceId'],op['t'])

    def test_ordinary_draw_operations_have_no_annotation(self):
        ops=self.render()
        plain=[op for op in ops if op['op']=='text' and 'annotation' not in op]
        self.assertTrue(plain)
        for op in ops:
            if op['op']!='text':self.assertNotIn('annotation',op)


if __name__=='__main__':unittest.main(verbosity=2)
