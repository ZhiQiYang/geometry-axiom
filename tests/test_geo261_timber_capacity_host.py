"""GEO-300 actual bridge admission, replay and compile-time H/W storage binding.

Compile-contract controls are intentionally separate from runtime assertion
kills: a compiler error is accepted only with the intended named typedef.
"""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_world_validation import copy_product_closure,PRODUCT_DEFINES

CAPACITY_ERROR="角材的數量超過上限"


class TimberCapacityHost(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();cls.bridge=build.bridge()
        cls.harness=ROOT/"tests/geo261_timber_capacity_host_harness.c"
        client=build.compile(cls.harness,"timber-capacity-host-client",PRODUCT_DEFINES)
        cls.exe=build.link("timber-capacity-host-client",[client,*build.product_objects()])
        cls.scene=build.work/"timber-capacity-512-unplaced.scene"
        cls.scene.write_text("".join(f"timber {i} 27 33 role primary\n" for i in range(1,513)),encoding="utf-8")

    def assert_count(self,bridge,count):
        response=bridge.command("objects")
        self.assertEqual(list(range(1,count+1)),[item["id"] for item in response["timbers"]])

    def load_full(self,bridge):
        response=bridge.command("loadfile "+str(self.scene))
        self.assertTrue(response["ok"],response)
        self.assert_count(bridge,512)

    def reject_unchanged(self,bridge,line,before):
        response=bridge.line(line)
        self.assertFalse(response["ok"],response)
        self.assertIn(CAPACITY_ERROR,response["error"])
        # Complete dump reply includes revision and definition_sha256 as
        # well as source text; rejection must change none of them.
        self.assertEqual(before,bridge.command("dump"))
        self.assert_count(bridge,512)

    def test_actual_host_independent_admission_storage_and_scratch_values(self):
        result=subprocess.run([str(self.exe),"values"],capture_output=True,text=True,encoding="utf-8",timeout=10)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertEqual("",result.stderr)

    def test_each_real_declaration_retains_legacy_64_and_admits_up_to_512(self):
        with _bridge.BridgeSession(self.bridge) as bridge:
            self.assertTrue(bridge.command("reset")["ok"])
            for identifier in range(1,513):
                response=bridge.line(f"timber {identifier} 27 33 role primary")
                self.assertTrue(response["ok"],{"identifier":identifier,"response":response})
                if identifier in (64,65,511,512):self.assert_count(bridge,identifier)
            before=bridge.command("dump")
            self.reject_unchanged(bridge,"timber 513 27 33 role primary",before)
            self.reject_unchanged(bridge,"timber",before)

    def test_full_capacity_redeclaration_replay_and_rejected_edit_preserve_history(self):
        with _bridge.BridgeSession(self.bridge) as bridge:
            self.load_full(bridge)
            original=bridge.command("dump")
            self.assertTrue(bridge.line("timber 512 28 33 role primary")["ok"])
            changed=bridge.command("dump")
            self.assertNotEqual(original["text"],changed["text"])
            self.assertGreater(changed["revision"],original["revision"])
            self.assert_count(bridge,512)
            self.reject_unchanged(bridge,"timber 513 27 33 role primary",changed)
            self.assertTrue(bridge.line("undo")["ok"])
            self.assertEqual(original["text"],bridge.command("dump")["text"])
            self.assert_count(bridge,512)
            # A syntax-less capacity refusal must also preserve a pending redo.
            before_redo=bridge.command("dump")
            self.reject_unchanged(bridge,"timber",before_redo)
            self.assertTrue(bridge.line("redo")["ok"])
            self.assertEqual(changed["text"],bridge.command("dump")["text"])
            replay=native().work/"timber-capacity-512-replay.scene"
            replay.write_text(changed["text"],encoding="utf-8")
            with _bridge.BridgeSession(self.bridge) as restored:
                self.assertTrue(restored.command("loadfile "+str(replay))["ok"])
                self.assertEqual(changed["text"].encode("utf-8"),restored.command("dump")["text"].encode("utf-8"))
                self.assert_count(restored,512)

    def capacity_first_sentinel(self,exe):
        with _bridge.BridgeSession(exe) as bridge:
            # Exactly 512 valid inputs are safe even with the guard withdrawn.
            # No valid 513th append is ever sent to the withdrawn executable.
            self.load_full(bridge);before=bridge.command("dump")
            response=bridge.line("timber")
            self.assertFalse(response["ok"],response)
            self.assertIn(CAPACITY_ERROR,response["error"],"host-capacity-first-missing-id")
            self.assertEqual(before,bridge.command("dump"))

    def test_real_bridge_guard_withdrawal_uses_safe_missing_id_then_restores(self):
        build=native();self.capacity_first_sentinel(self.bridge)
        source=(build.woodworking/"member_declaration.c").read_text(encoding="utf-8")
        before="if(*context->count==context->capacity){"
        self.assertEqual(1,source.count(before))
        changed=build.woodworking/"capacity-host-withdrawn-declaration.c"
        changed.write_text(source.replace(before,"if(false){"),encoding="utf-8")
        obj=build.compile(changed,"capacity-host-withdrawn-declaration")
        objects=build.product_objects();self.assertEqual(1,objects.count(build.wood_member_declaration_object))
        withdrawn=build.link("capacity-host-withdrawn-bridge",[build.bridge_object,
            *[obj if item==build.wood_member_declaration_object else item for item in objects]])
        with self.assertRaisesRegex(AssertionError,"host-capacity-first-missing-id") as failure:
            self.capacity_first_sentinel(withdrawn)
        print("capacity-host phase=withdrawn framework-assertion="+str(failure.exception))
        restored_source=build.woodworking/"capacity-host-restored-declaration.c"
        restored_source.write_text(source,encoding="utf-8")
        restored_obj=build.compile(restored_source,"capacity-host-restored-declaration")
        restored=build.link("capacity-host-restored-bridge",[build.bridge_object,
            *[restored_obj if item==build.wood_member_declaration_object else item for item in objects]])
        self.capacity_first_sentinel(restored)

    def test_real_host_compile_contract_rejects_each_drifted_capacity(self):
        build=native();destination=build.work/"capacity-host-abi-closure"
        destination.mkdir()
        harness=copy_product_closure(self.harness,destination)
        build.compile(harness,"capacity-host-abi-fixed",PRODUCT_DEFINES)
        controls=(
            ("host","current_geometry.c",b"#define WORLD_MAX_TIMBERS     WOOD_MEMBER_CAPACITY",b"#define WORLD_MAX_TIMBERS     64","app_timber_capacity_world_check"),
            ("timbers","geometry-templates/woodworking/native/document.h",b"WoodMember timbers[WOOD_MEMBER_CAPACITY];",b"WoodMember timbers[64];","app_timber_capacity_timbers_check"),
            ("anchors","geometry-templates/woodworking/native/document.h",b"WoodMemberPlacement anchors[WOOD_MEMBER_CAPACITY];",b"WoodMemberPlacement anchors[64];","app_timber_capacity_anchors_check"),
            ("contact","geometry-templates/woodworking/native/contact_world.h",b"#define WOOD_CONTACT_MEMBER_CAPACITY WOOD_MEMBER_CAPACITY",b"#define WOOD_CONTACT_MEMBER_CAPACITY 64","app_timber_capacity_contact_check"),
            ("report","geometry-templates/woodworking/native/cut_list.h",b"#define WOOD_CUT_LIST_MEMBER_CAPACITY WOOD_MEMBER_CAPACITY",b"#define WOOD_CUT_LIST_MEMBER_CAPACITY 64","app_timber_capacity_cut_list_check"),
            ("span","geometry-templates/woodworking/native/member_reference.h",b"#define WOOD_MEMBER_SPAN_MEMBER_CAPACITY WOOD_MEMBER_CAPACITY",b"#define WOOD_MEMBER_SPAN_MEMBER_CAPACITY 64","app_timber_capacity_span_check"),
            ("faces","geometry-templates/woodworking/native/contact_world.h",b"+WOOD_CONTACT_MEMBER_CAPACITY*2)",b"+WOOD_CONTACT_MEMBER_CAPACITY*2-1)","app_timber_capacity_stop_face_check"),
        )
        for name,path,before,after,marker in controls:
            with self.subTest(contract=name):
                target=destination/path;original=target.read_bytes();self.assertEqual(1,original.count(before))
                count=len(build.logs)
                try:
                    target.write_bytes(original.replace(before,after))
                    try:build.compile(harness,"capacity-host-abi-"+name,PRODUCT_DEFINES)
                    except AssertionError:
                        self.assertEqual(count+1,len(build.logs),"Expected one actual compiler invocation")
                        row=build.logs[-1]
                        self.assertNotEqual(0,row["exit"])
                        self.assertIn(marker,row["stdout"]+row["stderr"])
                        print("capacity-compile-contract "+json.dumps({"name":name,"diagnostic":marker,"compiler":row},ensure_ascii=False))
                    else:self.fail("Capacity ABI guard survived: "+name)
                finally:target.write_bytes(original)
                self.assertEqual(original,target.read_bytes())
                # These deliberate compiler failures are never linked or run;
                # all real bridge objects keep the same 512 header closure.
                build.compile(harness,"capacity-host-abi-restored-"+name,PRODUCT_DEFINES)


if __name__=="__main__":unittest.main(verbosity=2)
