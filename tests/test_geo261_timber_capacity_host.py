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
from tests import geo300_scene_generator as scene_generator
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_world_validation import copy_product_closure,PRODUCT_DEFINES

CAPACITY_ERROR="角材的數量超過上限"
GRAMMAR_ERROR="欄位數不對"
# Four fields cross the dispatcher, but the handler rejects count<5 before
# append after its capacity guard is withdrawn. Never send a valid 513th
# append to the withdrawn fixed-size storage.
INCOMPLETE_DECLARATION="timber 513 27 33"


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
        self.assertTrue(response["ok"],response)
        # objects intentionally lists placed members only. This helper is
        # for unplaced fixtures; canonical dump preserves every declaration.
        self.assertEqual([],response["timbers"],"capacity-fixture-must-remain-unplaced")
        dumped=bridge.command("dump")
        self.assertTrue(dumped["ok"],dumped)
        lines=dumped["text"].splitlines()
        identifiers=[int(line.split()[1]) for line in lines if line.startswith("timber ")]
        self.assertEqual(list(range(1,count+1)),identifiers,"capacity-declaration-ids-order-and-uniqueness")
        self.assertFalse(any(line.startswith("place ") for line in lines),"capacity-fixture-has-no-placement")

    def populate_full(self,bridge):
        self.assertTrue(bridge.command("reset")["ok"])
        for identifier in range(1,513):
            response=bridge.line(f"timber {identifier} 27 33 role primary")
            self.assertTrue(response["ok"],{"identifier":identifier,"response":response})
        self.assert_count(bridge,512)

    def reject_unchanged(self,bridge,line,before):
        response=bridge.line(line)
        self.assertFalse(response["ok"],response)
        self.assertIn(CAPACITY_ERROR,response["error"])
        # Complete dump reply includes revision and definition_sha256 as
        # well as source text; rejection must change none of them.
        self.assertEqual(before,bridge.command("dump"))
        self.assert_count(bridge,512)

    def reject_missing_id_unchanged(self,bridge,before):
        response=bridge.line("timber")
        self.assertFalse(response["ok"],response)
        self.assertIn(GRAMMAR_ERROR,response["error"],"dispatcher-rejects-before-capacity")
        self.assertNotIn(CAPACITY_ERROR,response["error"])
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
            self.reject_unchanged(bridge,INCOMPLETE_DECLARATION,before)
            self.reject_missing_id_unchanged(bridge,before)

    def test_full_capacity_redeclaration_replay_and_rejected_edit_preserve_history(self):
        with _bridge.BridgeSession(self.bridge) as bridge:
            initial=bridge.command("dump")
            refused=bridge.command("loadfile "+str(self.scene))
            self.assertFalse(refused["ok"],refused)
            self.assertIn("I9",refused["error"])
            self.assertEqual(initial,bridge.command("dump"),"unplaced-load-must-rollback")
            self.populate_full(bridge)
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
            # Both the handler capacity refusal and dispatcher grammar refusal
            # must preserve the pending redo and complete dump identity.
            before_redo=bridge.command("dump")
            self.reject_unchanged(bridge,INCOMPLETE_DECLARATION,before_redo)
            self.reject_missing_id_unchanged(bridge,before_redo)
            self.assertTrue(bridge.line("redo")["ok"])
            self.assertEqual(changed["text"],bridge.command("dump")["text"])
            replay=native().work/"timber-capacity-512-replay.scene"
            replay.write_text(changed["text"],encoding="utf-8")
            with _bridge.BridgeSession(self.bridge) as restored:
                initial=restored.command("dump")
                refused=restored.command("loadfile "+str(replay))
                self.assertFalse(refused["ok"],refused)
                self.assertIn("I9",refused["error"])
                self.assertEqual(initial,restored.command("dump"),"unplaced-replay-load-must-rollback")
                self.assertTrue(restored.command("reset")["ok"])
                for line in changed["text"].splitlines():
                    if not line.strip() or line.lstrip().startswith("#"):continue
                    response=restored.line(line)
                    self.assertTrue(response["ok"],{"line":line,"response":response})
                    self.assertNotIn("preview",response)
                replayed=restored.command("dump")
                self.assertEqual(changed["text"].encode("utf-8"),replayed["text"].encode("utf-8"))
                self.assertEqual(changed["definition_sha256"],replayed["definition_sha256"])
                self.assert_count(restored,512)

    def placed_fixture(self,count):
        # The original P-189 generator is preserved byte-for-byte. Its Python
        # self-check is not accepted as proof that the real bridge placed it.
        text,meta=scene_generator.build(count,"single")
        path=native().work/f"timber-capacity-{count}-placed.scene"
        path.write_bytes(text.encode("utf-8"))
        return path,text,meta

    def placed_batch(self,commands,label):
        payload="".join(command+"\n" for _,command in commands)
        result=_bridge.run_once(payload.encode("utf-8"),text=False,bridge=self.bridge,timeout=600)
        self.assertEqual(0,result.returncode,result.stderr)
        rows=[json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(commands),len(rows),label)
        self.assertEqual(len(commands),len({name for name,_ in commands}),label)
        return dict(zip((name for name,_ in commands),rows)),result.stdout

    def assert_placed_geometry(self,count,text,dumped,objects,references):
        for response in (dumped,objects,references):self.assertTrue(response["ok"],response)
        wanted=list(range(1,count+1))
        self.assertEqual(wanted,[item["id"] for item in objects["timbers"]])
        self.assertEqual(wanted,[item["id"] for item in references["timbers"]])
        declarations={};rectangles={};roles={};directions={};grid={};box=None
        # Independent expectation from the emitted DSL, not generator rects
        # or product geometry. This intentionally accepts only this fixture's
        # one rectangular surface, one grid and literal 27x33 members.
        for line in text.splitlines():
            words=line.split()
            if not words or words[0].startswith("#"):continue
            if words[0]=="surface":
                self.assertIsNone(box)
                self.assertEqual(["surface","1","origin","0","0","2500","u","+x","v","+y","outline"],words[:11])
                vertices=[tuple(map(int,word.split(","))) for word in words[11:]]
                self.assertEqual(4,len(vertices));width,height=vertices[2]
                self.assertEqual([(0,0),(width,0),(width,height),(0,height)],vertices)
                box=(0,0,width,height)
            elif words[0]=="grid":
                self.assertEqual(["grid","1","on","1","u"],words[:5])
                split=words.index("v");grid={"u":list(map(int,words[5:split])),"v":list(map(int,words[split+1:]))}
            elif words[0]=="timber":
                identifier=int(words[1]);self.assertNotIn(identifier,declarations)
                self.assertEqual(["27","33","role"],words[2:5]);self.assertEqual(6,len(words))
                declarations[identifier]=(27,33);roles[identifier]=words[5]
            elif words[0]=="place":
                identifier=int(words[1]);self.assertNotIn(identifier,rectangles)
                self.assertEqual(["on","1"],words[2:4]);self.assertEqual("+n",words[-1])
                directions[identifier]=words[-2]
                self.assertIn(identifier,declarations);self.assertIsNotNone(box)
                if words[4]=="at-face":
                    edge=words[5]
                    if roles[identifier]=="boundary":
                        self.assertIn(edge,("e0","e2"));self.assertEqual(["between","e3","e1"],words[6:9])
                        rect=(0,0,width,27) if edge=="e0" else (0,height-27,width,height)
                    else:
                        self.assertEqual("primary",roles[identifier]);self.assertIn(edge,("e3","e1"))
                        self.assertEqual(["between","t1","t2"],words[6:9])
                        rect=(0,27,27,height-27) if edge=="e3" else (width-27,27,width,height-27)
                else:
                    self.assertEqual(["at-line","grid","1"],words[4:7])
                    axis,index=words[7],int(words[8]);center=grid[axis][index]
                    self.assertEqual("between",words[9])
                    left,right=words[10:12]
                    if roles[identifier]=="primary":
                        self.assertEqual("u",axis);self.assertEqual(["t1","t2"],[left,right])
                        rect=(center-13,27,center+14,height-27)
                    else:
                        self.assertEqual("secondary",roles[identifier]);self.assertEqual("v",axis)
                        self.assertTrue(left.startswith("t") and right.startswith("t"))
                        lhs,rhs=rectangles[int(left[1:])],rectangles[int(right[1:])]
                        rect=(lhs[2],center-13,rhs[0],center+14)
                self.assertLess(rect[0],rect[2]);self.assertLess(rect[1],rect[3])
                self.assertGreaterEqual(rect[0],0);self.assertGreaterEqual(rect[1],0)
                self.assertLessEqual(rect[2],width);self.assertLessEqual(rect[3],height)
                rectangles[identifier]=rect
            else:self.fail("Unexpected placed fixture statement: "+line)
        self.assertEqual(wanted,list(declarations));self.assertEqual(wanted,list(rectangles))
        for i,left in enumerate(rectangles.values()):
            for right in list(rectangles.values())[i+1:]:
                self.assertFalse(left[0]<right[2] and right[0]<left[2] and left[1]<right[3] and right[1]<left[3])
        for item in references["timbers"]:
            identifier=item["id"];geometry=item["geometry"];self.assertIsInstance(geometry,dict)
            self.assertEqual(roles[identifier],item["role"])
            self.assertEqual((1,27,33),(geometry["surface"],geometry["A"],geometry["B"]))
            direction=directions[identifier];self.assertEqual(direction,geometry["dir"])
            self.assertEqual({"+u":[1,0,0],"-u":[-1,0,0],"+v":[0,1,0],"-v":[0,-1,0]}[direction],geometry["axes"][0])
            self.assertEqual({"+u":[0,1,0],"-u":[0,-1,0],"+v":[-1,0,0],"-v":[1,0,0]}[direction],geometry["axes"][1])
            expected=rectangles[identifier]
            self.assertEqual(expected[2]-expected[0] if direction.endswith("u") else expected[3]-expected[1],geometry["length"])
            self.assertEqual("+n",geometry["side"]);self.assertEqual([0,0,1],geometry["axes"][2])
            origin=geometry["origin"];self.assertEqual(2500,origin[2]);self.assertGreater(geometry["length"],0)
            length_axis,width_axis=geometry["axes"][:2]
            corners=[tuple(origin[k]+along*geometry["length"]*length_axis[k]+across*27*width_axis[k] for k in range(3)) for along in (0,1) for across in (0,1)]
            actual=(min(p[0] for p in corners),min(p[1] for p in corners),max(p[0] for p in corners),max(p[1] for p in corners))
            self.assertEqual(rectangles[identifier],actual,{"id":identifier,"geometry":geometry})
            self.assertEqual({2500},{point[2] for point in corners})
        canonical=dumped["text"].splitlines()
        for verb in ("timber","place"):
            self.assertEqual(wanted,[int(line.split()[1]) for line in canonical if line.startswith(verb+" ")])
        self.assertEqual(dumped["definition_sha256"],references["sourceFingerprint"])

    def test_real_placed_64_and_512_load_dump_and_canonical_replay(self):
        for count in (64,512):
            with self.subTest(count=count):
                scene,text,_=self.placed_fixture(count)
                commands=[("load","loadfile "+str(scene)),("dump","dump"),("objects","objects"),("references","references")]
                rows,_=self.placed_batch(commands,f"placed-{count}")
                self.assertTrue(rows["load"]["ok"],rows["load"])
                self.assert_placed_geometry(count,text,rows["dump"],rows["objects"],rows["references"])
                replay=native().work/f"timber-capacity-{count}-placed-replay.scene"
                replay.write_bytes(rows["dump"]["text"].encode("utf-8"))
                replay_commands=[("load","loadfile "+str(replay)),("dump","dump"),("objects","objects"),("references","references")]
                first,first_raw=self.placed_batch(replay_commands,f"replay-{count}-first")
                second,second_raw=self.placed_batch(replay_commands,f"replay-{count}-second")
                self.assertEqual(first_raw,second_raw,"identical fresh protocol must retain all reply bytes")
                self.assertTrue(first["load"]["ok"],first["load"])
                self.assertEqual(rows["dump"]["text"].encode("utf-8"),first["dump"]["text"].encode("utf-8"))
                self.assertEqual(rows["dump"]["definition_sha256"],first["dump"]["definition_sha256"])
                self.assertEqual(rows["references"],first["references"])
                self.assert_placed_geometry(count,text,second["dump"],second["objects"],second["references"])

    def test_real_placed_512_sequential_replay_and_safe_513_history(self):
        scene,text,meta=self.placed_fixture(512)
        loaded,_=self.placed_batch([("load","loadfile "+str(scene)),("dump","dump"),("objects","objects"),("references","references")],"placed-512-load")
        self.assertTrue(loaded["load"]["ok"],loaded["load"])
        statements=[line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
        commands=[("reset","reset")]+[(f"statement-{index}","line "+line) for index,line in enumerate(statements)]
        commands += [("dump","dump"),("objects","objects"),("references","references"),
            ("reject-513","line timber 513 27 33 role primary"),("after-513","dump"),
            ("reject-incomplete","line "+INCOMPLETE_DECLARATION),("after-incomplete","dump"),
            ("reject-missing","line timber"),("after-missing","dump"),
            ("delete","line "+meta["leaf"]["delete"]),("deleted","dump"),
            ("undo","line undo"),("undone","dump"),
            ("reject-pending-redo","line timber 513 27 33 role primary"),("after-pending-redo","dump"),
            ("redo","line redo"),("redone","dump"),("final-undo","line undo"),("final-dump","dump"),
            ("final-objects","objects"),("final-references","references")]
        rows,_=self.placed_batch(commands,"placed-512-sequential-history")
        refused={"reject-513":CAPACITY_ERROR,"reject-incomplete":CAPACITY_ERROR,
            "reject-missing":GRAMMAR_ERROR,"reject-pending-redo":CAPACITY_ERROR}
        for name,_ in commands:
            if name in refused:
                self.assertFalse(rows[name]["ok"],{name:rows[name]});self.assertIn(refused[name],rows[name]["error"])
                if name=="reject-missing":self.assertNotIn(CAPACITY_ERROR,rows[name]["error"])
            else:
                self.assertTrue(rows[name]["ok"],{name:rows[name]});self.assertNotIn("preview",rows[name],name)
        self.assert_placed_geometry(512,text,rows["dump"],rows["objects"],rows["references"])
        self.assertEqual(loaded["dump"]["text"].encode("utf-8"),rows["dump"]["text"].encode("utf-8"))
        self.assertEqual(loaded["dump"]["definition_sha256"],rows["dump"]["definition_sha256"])
        self.assertEqual(loaded["references"],rows["references"])
        self.assertEqual(rows["dump"],rows["after-513"]);self.assertEqual(rows["dump"],rows["after-missing"])
        self.assertEqual(rows["dump"],rows["after-incomplete"])
        leaf=meta["leaf"]["id"]
        canonical_lines=rows["dump"]["text"].splitlines(keepends=True)
        leaf_comment=f"# R18 角材 {leaf}:"
        self.assertEqual(1,sum(line.startswith(leaf_comment) for line in canonical_lines))
        remaining="".join(line for line in canonical_lines if not (line.startswith(("timber ","place ")) and int(line.split()[1])==leaf) and not line.startswith(leaf_comment))
        self.assertEqual(remaining,rows["deleted"]["text"])
        self.assertEqual(rows["dump"]["text"],rows["undone"]["text"])
        self.assertEqual(rows["undone"],rows["after-pending-redo"])
        self.assertEqual(rows["deleted"]["text"],rows["redone"]["text"])
        self.assertEqual(rows["dump"]["text"],rows["final-dump"]["text"])
        self.assertEqual(rows["references"],rows["final-references"])
        self.assert_placed_geometry(512,text,rows["final-dump"],rows["final-objects"],rows["final-references"])

    def capacity_first_sentinel(self,exe):
        with _bridge.BridgeSession(exe) as bridge:
            # Exactly 512 valid inputs are safe even with the guard withdrawn.
            # No valid 513th append is ever sent to the withdrawn executable.
            self.populate_full(bridge);before=bridge.command("dump")
            response=bridge.line(INCOMPLETE_DECLARATION)
            self.assertFalse(response["ok"],response)
            self.assertIn(CAPACITY_ERROR,response["error"],"host-capacity-first-incomplete-declaration")
            self.assertEqual(before,bridge.command("dump"))

    def test_real_bridge_guard_withdrawal_uses_safe_incomplete_declaration_then_restores(self):
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
        with self.assertRaisesRegex(AssertionError,"host-capacity-first-incomplete-declaration") as failure:
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
