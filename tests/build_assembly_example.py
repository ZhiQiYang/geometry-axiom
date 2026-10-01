"""Rebuild the portable example through native preview/confirm, never hand-written DSL."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests._bridge import BridgeSession,find_bridge


def build():
    with tempfile.TemporaryDirectory(prefix="assembly-example-") as directory:
        with BridgeSession(find_bridge(),cwd=directory) as bridge:
            def command(text):
                result=bridge.command(text)
                if not result.get("ok"):raise RuntimeError(result)
                return result
            command("reset")
            rule={"id":1,"version":1,"name":"雙框與中支","slots":[{"id":1,"name":"外框"},{"id":2,"name":"中支"}],
                  "members":[{"id":1,"slotId":1},{"id":2,"slotId":1},{"id":3,"slotId":2}],
                  "joints":[{"id":i,"kind":"end-to-side","scope":"frame-"+str(i),"terminatedMember":3,"targetMember":i,"end":"start" if i==1 else "finish","side":"+u" if i==1 else "-u","dir":"u"} for i in [1,2]]}
            newer=deepcopy(rule);newer["version"]=2;newer["name"]="雙框與中支（新版名稱）";newer["slots"].reverse()
            binding={"id":1,"name":"松木配置","rule":{"id":1,"version":1},"slots":[{"slotId":i,"A":{"kind":"parameter","parameterId":1,"fieldId":1},"B":{"kind":"material","id":"pine","version":1,"field":"B"},"contactFace":"A","orientation":"B"} for i in [1,2]]}
            incomplete=deepcopy(binding);incomplete["id"]=2;incomplete["name"]="待選材料";incomplete["slots"][1].update(A=None,B=None,contactFace=None,orientation=None)
            operations=[{"op":"publish-material","value":{"id":"pine","version":1,"kind":"timber","name":"松木角材","A":27,"B":33}},
                        {"op":"put-parameter","value":{"id":1,"name":"角材截面","fields":[{"id":1,"name":"A","type":"dimension","input":"27"}]}},
                        *[{"op":"publish-rule","value":r} for r in [rule,newer]],
                        {"op":"put-binding","value":binding},{"op":"put-binding","value":incomplete}]
            path=Path(directory)/"transaction.json"
            path.write_text(json.dumps({"schema":"assembly-transaction/1","expectedRevision":command("assembly-read")["revision"],"operations":operations},ensure_ascii=False),encoding="utf-8")
            preview=command("assembly-preview "+str(path))["preview"]
            if not preview["valid"]:raise RuntimeError(preview)
            command("assembly-confirm "+str(preview["token"]))
            for kind,id,x,y in [("parameter",1,40,40),("assembly-rule",1,400,40),("assembly-binding",1,760,40),("assembly-binding",2,760,380)]:command(f"line canvas-pos {kind} {id} {x} {y}")
            scene=command("dump")["text"].replace("\r\n","\n").encode()
    draft={"id":"assembly-unfinished-example","kind":"rule","base_ref":None,"data":{"id":2,"version":1,"name":"下一個自訂接合","slots":[{"id":1,"name":"主支"}],"members":[],"joints":[]},"updated_at":"2026-10-01T00:00:00Z"}
    manifest={"format":"geometry-canvas/7","projectId":"assembly-rules-v1","name":"組構規則範例","sceneHash":hashlib.sha256(scene).hexdigest(),"sources":[],"faces":[],"models":[],"faceProjections":[],"requiredCapabilities":["assembly-rule-authoring/1","engineering-spec/1","parameters/1"],"assemblyDrafts":{"schema":"assembly-drafts/1","records":[draft]}}
    return scene,json.dumps(manifest,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--check",action="store_true");args=parser.parse_args()
    target=ROOT/"geometry-web/examples/assembly-rules-v1.gcanvas"
    scene,manifest=build()
    if args.check:
        with zipfile.ZipFile(target) as archive:
            assert archive.read("world.scene")==scene
            assert archive.read("manifest.json")==manifest
        print("assembly example matches native rebuild")
    else:
        with zipfile.ZipFile(target,"w") as archive:
            for name,content in [("world.scene",scene),("manifest.json",manifest)]:
                info=zipfile.ZipInfo(name,date_time=(2026,10,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,content)
        print(target)
