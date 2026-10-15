"""Capture PF-H's actual native D4/D7/save/reopen witness for P-098/P-116.

Usage: python3 tests/pfh_witness.py --out /tmp/pfh-witness
No UI, PF-3 runtime claim, external service or repository writes are involved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.test_panel_fill_host import PanelFillHost,fill
from tests.pfh_oracle import footprint,support


def capture(out):
    out.mkdir(parents=True,exist_ok=True)
    PanelFillHost.setUpClass()
    records=[]
    for name,x in [("E1",105),("E2",125),("E3",120)]:
        case=PanelFillHost();case.setUp();transcript=[];native_command=case.command
        def command(text):
            entry={"command":text}
            if text.startswith(("loadfile ","engineering-preview ","panel-fill-preview ")):
                entry["input"]=Path(text.split(" ",1)[1]).read_text()
            reply=native_command(text);entry["reply"]=reply;transcript.append(entry);return reply
        case.command=command
        try:
            case.seed(width=915,length=1830,outline="0,0 1000,0 1000,300 0,300",
                      extra=f"column 1 at {x} 50 size {200-x} 50 z -2400 9\n",obstacles=["c1"])
            case.apply([fill(origin=[-815,-100],gap=0),dict(op="put-derived-placement",value=dict(id=10,fillId=1,h=30))])
            case.timbers();state=case.read()["state"];refs=case.command("references")
            rectangles=[footprint(t["geometry"]) for t in refs["timbers"]]
            assert rectangles==[(0,0,1000,27),(0,273,1000,300),(90,27,120,273)],rectangles
            scene=case.command("dump")["text"]
            assert "derived-placement 10 definition-hex " in scene and "placement 10 origin" not in scene
            assert state["derivedPlacements"][0]["definition"]==dict(id=10,fillId=1,h=30)
            widths=support(state["panelFills"][0]["derived"],rectangles)
            expected=[[0,27,100,900],[27,50,10,20],[50,100,10,5],[100,273,10,20],[273,300,100,900]] if x==105 else [[0,27,100,900],[27,273,10,20],[273,300,100,900]]
            assert widths==expected,(name,widths)
            cold=PanelFillHost();cold.setUp()
            try:
                cold.load_text(scene,"cold.scene")
                cold_state=cold.read()["state"];cold_scene=cold.command("dump")["text"]
                assert state==cold_state and scene==cold_scene
            finally:cold.doCleanups()
            (out/(name+".scene")).write_text(scene)
            value=dict(name=name,obstacleLeft=x,nativeState=state,nativeReferences=refs,
                       actualD7Footprints=rectangles,independentR43Oracle=widths,
                       coldProcessState=cold_state,coldProcessDumpSha256=hashlib.sha256(cold_scene.encode()).hexdigest(),
                       transcript=transcript)
            (out/(name+".json")).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
            records.append(dict(case=name,segments=len(widths),coldReopen=True,sourceOnlyHost=True))
        finally:case.doCleanups()
    summary=dict(scope="PF-H native D4/D7 and independent test-only R43 consumer; PF-3 runtime remains pending",
                 head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                 binarySha256=hashlib.sha256(Path(PanelFillHost.binary).read_bytes()).hexdigest(),records=records)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(summary,ensure_ascii=False))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--out",type=Path,required=True)
    capture(parser.parse_args().out)
