"""Synthetic result fixtures for the K-only second-template Python consumer.

Actual C producer integration is separately exercised by test_rectangular_bridge.
No Python subdivision implementation is used by the production adapter.
"""
from copy import deepcopy
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if importlib.util.find_spec("geometry_kernel") is None:
    sys.path.insert(0, str(ROOT / "geometry-core"))
if importlib.util.find_spec("geometry_rectangular") is None:
    sys.path.insert(0, str(ROOT / "geometry-templates/rectangular-grid"))
import geometry_kernel as kernel
from geometry_rectangular import RejectedView, build_mesh, compile_view, decode_view


def fixture(updated=False):
    # Fixed native-result examples, intentionally not a second grid algorithm.
    u = (0,240,480,720,960,1200) if updated else (0,200,400,600,800,1000)
    v = (0,200,400,600)
    names, values = ("width","height","columns","rows","thickness"), (u[-1],600,5,3,10)
    sources, bindings = [], {}
    for index, (name, value) in enumerate(zip(names,values), 1):
        kind = "count" if name in ("columns","rows") else "length"
        key = {"owner":"71", "field":str(index), "kind":kind}
        bindings[name] = key
        sources.append({"key":key, "revision":"2" if updated and name=="width" else "1",
                        "value":{"num":str(value),"den":"1","unit":"scalar" if kind=="count" else "length"}})
    cells = [{"column":column,"row":row,"region":{"outer":[[u[column],v[row]], [u[column+1],v[row]],
              [u[column+1],v[row+1]], [u[column],v[row+1]]], "holes":[]}}
             for row in range(3) for column in range(5)]
    return {"schema":"rectangular-grid-native-view/1", "status":"OK", "recipe":"rectangular-grid/1",
        "sources":sources,"bindings":bindings,"frame":{"origin":[0,0,0],"u":[1,0,0],"v":[0,1,0],"n":[0,0,1]},"cells":cells}


def view(updated=False):
    return decode_view(json.dumps(fixture(updated)), execution_identity=("synthetic-result",))


class RectangularPythonTests(unittest.TestCase):
    def test_fifteen_keep_members_preserve_internal_faces_and_exact_volumes(self):
        result = build_mesh(view())
        self.assertEqual(15, len(result.records))
        self.assertEqual({"400000"}, {record.mesh["volume_mm3"] for record in result.records})
        self.assertEqual(6000000, sum(int(record.mesh["volume_mm3"]) for record in result.records))
        self.assertEqual({12}, {len(record.mesh["triangles"]) for record in result.records})
        self.assertEqual(180, sum(len(record.mesh["triangles"]) for record in result.records))
        self.assertEqual({(f"{column}:{row}",) for row in range(3) for column in range(5)},
                         {record.member_path for record in result.records})
        self.assertEqual("COMPLETE", result.status)

    def test_native_recomputed_cells_retain_source_keys_and_change_committed_mesh(self):
        initial, updated = view(), view(True)
        self.assertEqual([s.key for s in initial.sources], [s.key for s in updated.sources])
        program, request = compile_view(initial)
        session = kernel.ProgramSession(program, request)
        replacement, request = compile_view(updated)
        token, candidate = session.preview(replacement, request, evaluator_stamp=("fixture",1))
        self.assertEqual({"480000"}, {record.mesh["volume_mm3"] for record in candidate.result.records})
        self.assertEqual({"400000"}, {record.mesh["volume_mm3"] for record in session.snapshot.result.records})
        accepted = session.confirm(token, evaluator_stamp=("fixture",1))
        self.assertEqual(7200000, sum(int(record.mesh["volume_mm3"]) for record in accepted.result.records))
        self.assertEqual(1, session.revision)
        before = session.snapshot
        with self.assertRaises(RejectedView) as error:
            decode_view(json.dumps({"schema":"rectangular-grid-native-view/1", "status":"FRACTIONAL_CELL",
                "previousUnchanged":True, "diagnostic":{"requiredStep":{"num":"1000","den":"3","unit":"length"}}}))
        self.assertEqual("FRACTIONAL_CELL", error.exception.code)
        self.assertEqual(before, session.snapshot)
        self.assertEqual(1, session.revision)

    def test_thickness_is_a_source_reference_and_cell_dependencies_remain_complete(self):
        original = view()
        program, request = compile_view(original)
        self.assertTrue(all(isinstance(node.definition.upper, kernel.SourceRef)
            for node in program.nodes if isinstance(node.definition,kernel.ExtrusionDef)))
        closure = kernel.source_closure(program,(request.roots[0].node,))
        self.assertEqual({source.key for source in original.sources}, {source.key for source in closure})
        sources = tuple(replace(source,value=replace(source.value,numerator=15)) if source.key==original.thickness.key else source
                        for source in original.sources)
        result = build_mesh(replace(original,sources=sources))
        self.assertEqual({"600000"}, {record.mesh["volume_mm3"] for record in result.records})

    def test_protocol_rejects_missing_duplicate_and_inexact_result_data(self):
        variants = []
        value=fixture();value["cells"].pop();variants.append(value)
        value=fixture();value["cells"][-1]=deepcopy(value["cells"][0]);variants.append(value)
        value=fixture();value["sources"][0]["value"]["num"]="1000.0";variants.append(value)
        value=fixture();value["sources"][0]["value"]["den"]="3";variants.append(value)
        value=fixture();value["sources"][2]["key"]["kind"]="length";variants.append(value)
        value=fixture();value["sources"][0]["revision"]="0";variants.append(value)
        value=fixture();value["cells"][0]["column"]=True;variants.append(value)
        for value in variants:
            with self.subTest(value=value), self.assertRaises(RejectedView):
                decode_view(json.dumps(value))
        with self.assertRaises(RejectedView):
            decode_view('{"schema":"rectangular-grid-native-view/1","schema":"again"}')
        with self.assertRaises(RejectedView):
            decode_view('{"number":1.0}')

    def test_input_array_order_does_not_change_source_binding_or_geometry(self):
        value=fixture();value["sources"].reverse();value["cells"].reverse()
        result=build_mesh(decode_view(json.dumps(value)))
        expected=build_mesh(view())
        self.assertEqual([r.mesh for r in expected.records],[r.mesh for r in result.records])
        self.assertEqual([r.member_path for r in expected.records],[r.member_path for r in result.records])
        # The native recipe permits two fields to bind the same typed source.
        aliased=fixture()
        aliased["sources"][0]["value"]["num"]="600"
        aliased["sources"][1]=deepcopy(aliased["sources"][0])
        aliased["bindings"]["height"]=deepcopy(aliased["bindings"]["width"])
        coordinates=(0,120,240,360,480,600)
        for cell in aliased["cells"]:
            c,r=cell["column"],cell["row"]
            old=cell["region"]["outer"]
            cell["region"]["outer"]=[[coordinates[c],old[0][1]],[coordinates[c+1],old[1][1]],
                [coordinates[c+1],old[2][1]],[coordinates[c],old[3][1]]]
        result=build_mesh(decode_view(json.dumps(aliased)))
        self.assertEqual({"240000"},{record.mesh["volume_mm3"] for record in result.records})
        self.assertEqual(20,len(result.sources))
        aliased["sources"][1]["revision"]="2"
        with self.assertRaises(RejectedView):
            decode_view(json.dumps(aliased))


class RectangularPythonIsolationTests(unittest.TestCase):
    def test_clean_install_runs_without_application_or_first_template(self):
        with tempfile.TemporaryDirectory(prefix="rectangular-python-only-") as directory:
            copied=Path(directory)
            shutil.copytree(ROOT/"geometry-core/geometry_kernel",copied/"geometry_kernel",ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(ROOT/"geometry-templates/rectangular-grid/geometry_rectangular",copied/"geometry_rectangular",ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copyfile(__file__,copied/"test_rectangular_python.py")
            script=("import sys,importlib.abc,pathlib,unittest\n"
                "class Reject(importlib.abc.MetaPathFinder):\n"
                " def find_spec(self,fullname,path=None,target=None):\n"
                "  if fullname.split('.')[0] in ('modeling','geometry_app','geometry_woodworking'): raise AssertionError(fullname)\n"
                "sys.meta_path.insert(0,Reject());sys.path.insert(0,sys.argv.pop(1))\n"
                "suite=unittest.defaultTestLoader.loadTestsFromName('test_rectangular_python.RectangularPythonTests')\n"
                "result=unittest.TextTestRunner(verbosity=2).run(suite)\n"
                "assert result.testsRun==5 and not result.skipped\n"
                "root=pathlib.Path(sys.path[0]).resolve()\n"
                "assert all(pathlib.Path(m.__file__).resolve().is_relative_to(root) for n,m in sys.modules.items() if n.startswith(('geometry_kernel','geometry_rectangular')))\n"
                "assert not any(n.split('.')[0] in ('modeling','geometry_app','geometry_woodworking') for n in sys.modules)\n"
                "raise SystemExit(not result.wasSuccessful())")
            result=subprocess.run([sys.executable,"-I","-B","-c",script,str(copied)],capture_output=True,text=True,timeout=60)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)
            self.assertIn("Ran 5 tests",result.stderr)
            consumer=copied/"rectangular_python_consumer.py"
            shutil.copyfile(ROOT/"tests/rectangular_python_consumer.py",consumer)
            events=copied/"synthetic-events.jsonl"
            rejected={"schema":"rectangular-grid-native-view/1","status":"FRACTIONAL_CELL",
                      "previousUnchanged":True,"diagnostic":{"requiredStep":{"num":"1000","den":"3","unit":"length"}}}
            events.write_text("\n".join(json.dumps(item) for item in (fixture(),fixture(True),rejected))+"\n",encoding="utf-8")
            result=subprocess.run([sys.executable,"-I","-B",str(consumer),"--library",str(copied),
                "--events",str(events),"--binary-sha256","synthetic-not-a-native-binary"],
                capture_output=True,text=True,timeout=60)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)
            self.assertEqual(["6000000","7200000"],json.loads(result.stdout)["total_volumes_mm3"])


class RectangularSharedEngineTests(unittest.TestCase):
    def test_woodworking_frozen_extrusion_oracle(self):
        from tests.test_geometry_kernel_runtime import FROZEN_DIGESTS,cases,execute
        from modeling.engine import evaluate
        self.assertEqual(FROZEN_DIGESTS["extrusion"],kernel.digest(execute(evaluate,cases()["extrusion"])))

    def test_removing_shared_extrusion_occupancy_breaks_both_templates(self):
        with tempfile.TemporaryDirectory(prefix="rectangular-shared-extrusion-") as directory:
            copied=Path(directory)
            for package in ("geometry-core/geometry_kernel","geometry-core/modeling","geometry-app/geometry_app",
                            "geometry-templates/woodworking/geometry_woodworking","geometry-templates/rectangular-grid/geometry_rectangular"):
                shutil.copytree(ROOT/package,copied/package,ignore=shutil.ignore_patterns("__pycache__"))
            (copied/"tests").mkdir();(copied/"tests/__init__.py").write_text("",encoding="utf-8")
            for name in ("test_rectangular_python.py","test_geometry_kernel_runtime.py","test_geometry_source_runtime.py"):
                shutil.copyfile(ROOT/"tests"/name,copied/"tests"/name)
            source=copied/"geometry-core/geometry_kernel/geometry.py"
            original=source.read_text(encoding="utf-8")
            before="return lo < h < hi and region.location(uv) == 2"
            self.assertEqual(1,original.count(before))
            tests=("RectangularPythonTests.test_fifteen_keep_members_preserve_internal_faces_and_exact_volumes",
                   "RectangularSharedEngineTests.test_woodworking_frozen_extrusion_oracle")
            def run(test):
                return subprocess.run([sys.executable,"-I","-B","-c",
                    "import sys,unittest;sys.path.insert(0,sys.argv.pop(1));unittest.main(module=None)",str(copied),
                    "tests.test_rectangular_python."+test],cwd=copied,capture_output=True,text=True,timeout=30)
            for test in tests:
                result=run(test);self.assertEqual(0,result.returncode,result.stdout+result.stderr)
            source.write_text(original.replace(before,"return False"),encoding="utf-8")
            for test in tests:
                result=run(test);details=result.stdout+result.stderr
                self.assertEqual(1,result.returncode,details);self.assertIn("FAILED (failures=1)",details)
                self.assertIn("Ran 1 test",details);self.assertNotIn("ImportError",details);self.assertNotIn("SyntaxError",details)
            source.write_text(original,encoding="utf-8")
            for test in tests:
                result=run(test);self.assertEqual(0,result.returncode,result.stdout+result.stderr)


if __name__=="__main__":
    unittest.main()
