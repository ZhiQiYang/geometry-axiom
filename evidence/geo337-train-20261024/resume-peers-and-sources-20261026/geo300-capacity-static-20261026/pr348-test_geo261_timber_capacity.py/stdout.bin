"""GEO-300 capacity witnesses; normal assertion exits, no crash-as-kill controls."""
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests.test_geo261_native_kernel import native


class TimberCapacity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();source=build.woodworking/"timber-capacity-client.c"
        shutil.copy2(ROOT/"tests/geo261_timber_capacity_harness.c",source)
        cls.source=source;cls.client=build.compile(source,"timber-capacity-client")
        cls.exe=build.link("timber-capacity-client",[cls.client,*build.product_objects()])

    def case(self,name,exe=None,marker=None):
        result=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,encoding="utf-8",timeout=10)
        self.assertEqual(1 if marker else 0,result.returncode,result.stderr)
        self.assertEqual("ASSERT:"+marker+"\n" if marker else "",result.stderr)

    def test_independent_capacity_storage_and_scratch_values(self):self.case("values")
    def test_report_full_capacity_order_own_copy_and_atomic_rejection(self):self.case("report")
    def test_contact_full_capacity_stable_order_pair_atomicity_and_public_fallback(self):self.case("contact")
    def test_validation_full_capacity_visits_and_overflow_before_callback(self):self.case("validation")
    def test_full_declaration_refuses_new_identity_and_accepts_existing_identity(self):self.case("admission")

    def test_safe_removed_guards_fail_named_assertions_then_restore(self):
        build=native()
        controls=[
            ("world_validation",build.wood_world_validation_object,"capacity-validation-guard",
             "if(context->member_count>WOOD_CONTACT_MEMBER_CAPACITY)","if(false)",
             "validation","capacity-validation-513-before-callback"),
            ("member_declaration",build.wood_member_declaration_object,"capacity-declaration-guard",
             "if(*context->count==context->capacity)","if(false)",
             "admission","capacity-declaration-513-refused"),
            ("member_declaration",build.wood_member_declaration_object,"capacity-declaration-existing",
             "if(supplied)for(size_t i=0;i<*context->count;++i)","if(false)for(size_t i=0;i<*context->count;++i)",
             "admission","capacity-declaration-existing-full-admitted"),
        ]
        for module,original,name,before,after,case,marker in controls:
            with self.subTest(control=name):
                self.case(case)
                source=(build.woodworking/(module+".c")).read_text(encoding="utf-8")
                self.assertEqual(1,source.count(before),"Control must replace exactly one production expression")
                path=build.woodworking/(name+".c");path.write_text(source.replace(before,after),encoding="utf-8")
                obj=build.compile(path,name);objects=build.product_objects()
                self.assertEqual(1,objects.count(original))
                exe=build.link(name,[self.client,*[obj if item==original else item for item in objects]])
                self.case(case,exe,marker);self.case(case)

    def test_reverting_sole_value_fails_independent_runtime_constant(self):
        build=native();header=build.woodworking/"members.h";original=header.read_bytes()
        before=b"#define WOOD_MEMBER_CAPACITY 512";after=b"#define WOOD_MEMBER_CAPACITY 64"
        self.assertEqual(1,original.count(before))
        self.case("values")
        try:
            header.write_bytes(original.replace(before,after))
            client=build.compile(self.source,"timber-capacity-values-64",["CAPACITY_VALUES_ONLY=1"])
            exe=build.link("timber-capacity-values-64",[client])
            self.case("values",exe,"capacity-value-512")
        finally:header.write_bytes(original)
        self.assertEqual(original,header.read_bytes())
        # Recompile the only affected translation unit: this values-only
        # executable has no W/H object and therefore cannot mix an ABI.
        client=build.compile(self.source,"timber-capacity-values-restored",["CAPACITY_VALUES_ONLY=1"])
        self.case("values",build.link("timber-capacity-values-restored",[client]))


if __name__=="__main__":unittest.main(verbosity=2)
