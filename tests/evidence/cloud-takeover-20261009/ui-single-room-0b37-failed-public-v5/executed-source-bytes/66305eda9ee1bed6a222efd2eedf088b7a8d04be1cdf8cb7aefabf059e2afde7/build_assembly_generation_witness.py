"""Native witnesses for the proposed AR-06 contract, NOT an assembly generator.

This uses only existing scene/place/reference operations in isolated processes.
No AssemblyInstance, generation capability or production API is implemented.
Run: GEOMETRY_TEST_BRIDGE=/fresh/bridge python3 tests/build_assembly_generation_witness.py
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests._bridge import BridgeSession,find_bridge


def build_case(width,depth,right,missing_support=False):
    with tempfile.TemporaryDirectory(prefix="ar06-native-witness-") as directory:
        with BridgeSession(find_bridge(),cwd=directory) as bridge:
            def line(command):
                result=bridge.command("line "+command)
                if result.get("preview",{}).get("valid"):
                    result=bridge.command("line confirm "+str(result["preview"]["token"]))
                assert result.get("ok"),result
            line("reset")
            line("surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")
            for gid,axis,position in [(1,"v",500),(2,"v",right),(3,"u",1500)]:
                line(f"spec position{gid} {position}")
                line(f"guide {gid} 1 {axis} spec:position{gid}")
            if not missing_support:
                for tid,edge in [(90,"e0"),(91,"e2")]:
                    line(f"timber {tid} 20 20 role boundary")
                    line(f"place {tid} on 1 at-face {edge} +u +n")
            line(f"timber 1 {width} {depth} role primary")
            if missing_support:
                before=bridge.command("dump")["text"]
                response=bridge.command("line place 1 on 1 at-line guide 1 +v +n")
                assert not response.get("ok"),response
                assert before==bridge.command("dump")["text"]
                assert "V_CUT_PRIORITY" in response.get("error","") and "只有 boundary" in response["error"],response
                return {"input":{"A":width,"B":depth,"right":right},"operation":"place primary without boundary support","accepted":False,"diagnostic":response["error"],"worldUnchanged":True}
            line("place 1 on 1 at-line guide 1 +v +n")
            line(f"timber 2 {width} {depth} role primary")
            line("place 2 on 1 at-line guide 2 +v +n")
            line(f"timber 3 {width} {depth} role secondary")
            line("place 3 on 1 at-line guide 3 between t1 t2 +u +n")
            records=bridge.command("references")["timbers"]
            geometry={t["id"]:t["geometry"] for t in records}
            # Independent expected lengths: boundary support strips are 20 each;
            # cross member contacts the inward faces of the two primary members.
            assert [geometry[i]["length"] for i in [1,2]]==[2960,2960],geometry
            assert geometry[3]["length"]==right-500-width,geometry
            scene=bridge.command("dump")["text"]
            path=Path(directory)/"witness.scene";path.write_text(scene,encoding="utf-8")
            with BridgeSession(find_bridge(),cwd=directory) as fresh:
                assert fresh.command("loadfile "+str(path))["ok"]
                assert fresh.command("dump")["text"]==scene
                assert fresh.command("references")["timbers"]==records
            return {"input":{"A":width,"B":depth,"left":500,"right":right,"cross":1500},"accepted":True,
                    "lengthsMm":{"primaryLeft":2960,"primaryRight":2960,"secondary":right-500-width},
                    "nativeGeometry":{str(i):geometry[i] for i in [1,2,3]},"sceneRoundTrip":True,
                    "sceneSha256":hashlib.sha256(scene.encode()).hexdigest()}


def build():
    return {"schema":"assembly-generation-proposal-witness/1","scope":"existing native placement only; generator not implemented",
            "cases":[build_case(27,33,2500),build_case(40,50,2800),build_case(27,33,2500,True)]}


if __name__=="__main__":
    print(json.dumps(build(),ensure_ascii=False,indent=2))
