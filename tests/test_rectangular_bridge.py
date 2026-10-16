"""Real C K -> second-template result -> real Python K integration.

Requires the PR275 rectangular recipe source closure. Both compiled C and Python
installations exclude the application and woodworking template. This suite is
native work and must run in the repository's shared compiler queue.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))


class RectangularBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT/"tests/test_rectangular_template.py").is_file():
            raise unittest.SkipTest("PR275 native rectangular recipe is not installed in this source tree")
        from tests.test_rectangular_template import IsolatedNativeBuild
        cls.build=IsolatedNativeBuild()
        try:
            harness=cls.build.source_root/"tests/rectangular_python_harness.c"
            shutil.copyfile(ROOT/"tests/rectangular_python_harness.c",harness)
            cls.exporter_object=cls.build.compile(harness,"python-view-exporter")
            cls.objects=[cls.build.objects[name] for name in ("exact","geometry","grid","recipe")]
            cls.exe=cls.build.link("rectangular-python-view",[*cls.objects,cls.exporter_object])
            cls.library=cls.build.source_root/"python"
            for package,source in (("geometry_kernel","geometry-core/geometry_kernel"),
                                   ("geometry_rectangular","geometry-templates/rectangular-grid/geometry_rectangular")):
                shutil.copytree(ROOT/source,cls.library/package,ignore=shutil.ignore_patterns("__pycache__"))
            cls.consumer=cls.build.source_root/"tests/rectangular_python_consumer.py"
            shutil.copyfile(ROOT/"tests/rectangular_python_consumer.py",cls.consumer)
            cls.inventory=[{"path":str(path.relative_to(cls.build.source_root)).replace("\\","/"),
                            "sha256":sha256(path.read_bytes()).hexdigest()}
                           for path in sorted(cls.build.source_root.rglob("*")) if path.is_file()]
        except BaseException:
            cls.build.close()
            raise

    @classmethod
    def tearDownClass(cls):
        destination=os.environ.get("GEO261_RECTANGULAR_BRIDGE_EVIDENCE")
        if destination:
            path=Path(destination);path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps({"inventory":cls.inventory,"commands":cls.build.logs,
                "binary_sha256":sha256(cls.exe.read_bytes()).hexdigest()},indent=2),encoding="utf-8")
        cls.build.close()

    def native(self,executable=None):
        executable=executable or self.exe
        result=subprocess.run([str(executable)],cwd=self.build.source_root,env=self.build.env,
                              capture_output=True,text=True,timeout=30)
        self.build.logs.append({"kind":"native-export","executable":str(executable),
            "binary_sha256":sha256(executable.read_bytes()).hexdigest(),"exit":result.returncode,
            "stdout":result.stdout,"stderr":result.stderr})
        self.assertIn(result.returncode,(0,1),"A crash or environment block is not a semantic test verdict")
        return result

    def complete_sequence(self):
        native=self.native()
        self.assertEqual(0,native.returncode,native.stdout+native.stderr)
        events=[json.loads(line) for line in native.stdout.splitlines()]
        self.assertEqual(["OK","OK","FRACTIONAL_CELL"],[event["status"] for event in events])
        self.assertIs(events[2]["previousUnchanged"],True)
        self.assertEqual({"num":"1000","den":"3","unit":"length"},events[2]["diagnostic"]["requiredStep"])
        path=self.build.work/"native-events.jsonl";path.write_text(native.stdout,encoding="utf-8")
        command=[sys.executable,"-I","-B",str(self.consumer),"--library",str(self.library),"--events",str(path),
                 "--binary-sha256",sha256(self.exe.read_bytes()).hexdigest()]
        environment={key:value for key,value in os.environ.items() if not key.startswith("GEOMETRY_") and key!="PYTHONPATH"}
        python=subprocess.run(command,cwd=self.build.source_root,env=environment,capture_output=True,text=True,timeout=60)
        self.build.logs.append({"kind":"isolated-python-consumer","command":command,"exit":python.returncode,
                               "stdout":python.stdout,"stderr":python.stderr})
        self.assertEqual(0,python.returncode,python.stdout+python.stderr)
        receipt=json.loads(python.stdout)
        self.assertEqual([15,15],receipt["member_counts"])
        self.assertEqual(["6000000","7200000"],receipt["total_volumes_mm3"])
        self.assertTrue(receipt["source_keys_stable"])
        self.assertEqual(1,receipt["revision_after_rejection"])
        return receipt

    def test_real_native_results_drive_isolated_python_geometry_and_rejection_preserves_state(self):
        self.complete_sequence()

    def test_removing_real_native_divisibility_guard_breaks_the_same_sequence(self):
        self.complete_sequence()
        original=(self.build.kernel/"grid.c").read_text(encoding="utf-8")
        target="if((hi-lo)%n)return GEO_GRID_NOT_DIVISIBLE;"
        self.assertEqual(1,original.count(target))
        path=self.build.work/"rectangular-bridge-grid-mutant.c"
        path.write_text(original.replace(target,"/* negative control: remove exact divisibility */"),encoding="utf-8")
        mutant=self.build.compile(path,"rectangular-bridge-grid-mutant")
        objects=[mutant if obj==self.build.objects["grid"] else obj for obj in self.objects]
        executable=self.build.link("rectangular-bridge-divisibility-mutant",[*objects,self.exporter_object])
        result=self.native(executable)
        self.assertEqual(1,result.returncode,result.stdout+result.stderr)
        self.assertIn("FRACTIONAL_CELL_ACCEPTED",result.stderr)
        self.complete_sequence()


if __name__=="__main__":
    unittest.main(verbosity=2)
