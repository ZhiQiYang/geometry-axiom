"""Unused authored grids and actual typed vertex consumption in the product."""
import base64
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests.test_geo261_native_kernel import native
from tests import test_geo261_model_sources as model_sources

SCENE=('surface 1 origin 0 0 0 u +x v +y outline 10,20 510,20 510,520 10,520\n'
       'boundary-vertex-keys 1 outer 1 2 3 4 next-key 5\n'
       'grid-system 2 name-hex 6c617474696365 main-along none u repeat 0 100 v repeat 0 100\n'
       'grid-binding 3 on-boundary 1 from-system 2 vertex-key 1 cell 0 0 anchor 0 1 0 1\n'
       'grid 4 on 1 from-binding 3\n'
       'placement 7 on boundary 1 origin 0 0 100 u +x v +y\n'
       'grid 5 on 7 main-along none u 100 200 300 v 100 200 300\n'
       'subgrid 6 parent 5 cell u min line:0 v min line:0 divisions u 2 v 2\n')

class GridDefinitionsProduct(unittest.TestCase):
    execute=model_sources.ModelSources.execute
    ref=staticmethod(model_sources.ModelSources.ref)
    nodes=model_sources.ModelSources.nodes

    @staticmethod
    def grid(kind,identifier):return 'wood.grid',bytes([kind])+struct.pack('>I',identifier)+bytes(59)

    def test_unused_direct_and_manual_child_definitions_are_in_the_actual_model_graph(self):
        envelope=self.execute(SCENE);nodes=self.nodes(envelope)
        for kind,identifier,schema in ((1,2,'wood.grid.system/1'),(3,3,'wood.grid.binding/1'),
                (5,4,'wood.grid.application/1'),(5,5,'wood.grid.application/1'),(5,6,'wood.grid.application/1')):
            node=nodes[self.grid(kind,identifier)]
            self.assertEqual(schema,node['value']['schema'])
            self.assertEqual(struct.pack('>Q',identifier),base64.b64decode(node['value']['contentBase64'],validate=True)[:8])
        self.assertNotIn(self.grid(6,5),nodes,'Unused direct grid must not gain an application value evaluation')
        self.assertNotIn(self.grid(6,6),nodes,'Unused child must not gain an application value evaluation')
        edges={(self.ref(e['consumer']),self.ref(e['source']),e['kind']) for e in envelope['neutralSources']['edges']}
        self.assertIn((self.grid(5,6),self.grid(5,5),'definition-required'),edges)

    def test_actual_binding_uses_both_vertex_quantities_and_full_key_ledger(self):
        envelope=self.execute(SCENE);nodes=self.nodes(envelope)
        ledger=('core.region-key',struct.pack('>4I',1,1,0,0))
        self.assertEqual(struct.pack('>8I',1,5,1,4,1,2,3,4),
            base64.b64decode(nodes[ledger]['value']['contentBase64'],validate=True))
        edges={(self.ref(e['consumer']),self.ref(e['source']),e['kind']) for e in envelope['neutralSources']['edges']}
        self.assertIn((self.grid(3,3),ledger,'definition-required'),edges)
        for axis,value in enumerate((10,20)):
            coordinate=('core.region-key',struct.pack('>4I',2,1,1,axis))
            self.assertEqual(str(value),nodes[coordinate]['value']['num'])
            self.assertIn((self.grid(4,3),coordinate,'value-required'),edges)
            self.assertIn((coordinate,ledger,'definition-required'),edges)
            self.assertIn((coordinate,('core.region',struct.pack('>I',1)),'value-required'),edges)

    def client(self):
        build=native();client=build.compile(ROOT/'tests/geo261_grid_key_product_harness.c','grid-key-product',
            ['GEOMETRY_KERNEL_EXTERNAL=1','GEOMETRY_WOODWORKING_EXTERNAL=1',
             'GEOMETRY_HOST_HISTORY_EXTERNAL=1','GEOMETRY_HOST_CANDIDATE_EXTERNAL=1'])
        scene=build.work/'grid-key-product.scene';scene.write_text(SCENE,encoding='utf-8')
        return build,client,scene

    def run_client(self,exe,scene,marker=None):
        result=subprocess.run([str(exe),str(scene)],capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(1 if marker else 0,result.returncode,result.stdout+'\n'+result.stderr)
        assertions=[line for line in result.stderr.splitlines() if line.startswith('ASSERT:')]
        self.assertEqual(['ASSERT:'+marker] if marker else [],assertions,result.stderr)

    def test_preview_confirm_and_undo_keep_the_actual_shared_key_graph(self):
        build,client,scene=self.client()
        self.run_client(build.link('grid-key-product',[client,*build.product_objects()]),scene)

    def test_changed_kernel_coordinate_is_observed_by_the_real_grid_cache(self):
        build,client,scene=self.client()
        baseline=build.link('grid-key-product-baseline',[client,*build.product_objects()]);self.run_client(baseline,scene)
        source=(build.kernel/'region_key_sources.c').read_text(encoding='utf-8')
        before='(GeoQuantity){axis?point.v:point.u,1,GEO_UNIT_LENGTH}'
        self.assertEqual(1,source.count(before))
        path=build.kernel/'grid-key-product-control.c'
        path.write_text(source.replace(before,'(GeoQuantity){(axis?point.v:point.u)+1,1,GEO_UNIT_LENGTH}'),encoding='utf-8')
        changed=build.compile(path,'grid-key-product-control')
        executable=build.link('grid-key-product-control',[client,*[changed if obj==build.kernel_region_key_sources_object else obj
            for obj in build.product_objects()]])
        self.run_client(executable,scene,'grid-key-returned-quantities-drive-actual-cache')
        self.run_client(baseline,scene)

if __name__=='__main__':unittest.main(verbosity=2)
