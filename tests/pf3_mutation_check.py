"""Execute PF-3 removals in disposable source copies, with fresh native receipts.

python tests/pf3_mutation_check.py --out /tmp/pf3-mutations
Each negative must fail an assertion with the named cause, never an import,
compile error, skip, crash or timeout. No repository source is edited in place.
A case lists one patch per enforcement layer. GEO-261 checks some rules in more than one place, so
removing a single layer leaves the other standing and the fault survives; where that is so (host-identity)
the case removes every layer and reproduces the fault main had. Per-case table, with main's line, the line
used now and the single-layer controls: geometry-core/panel-fill/PF3-NATIVE.md.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
HOST="geometry-core/panel_fill_support.inc"
REFERENCE="geometry-app/native/reference_sources.inc"
SOURCE="geometry-templates/woodworking/native/panel_support.c"
CASES=[
    ("effective-merge",[(SOURCE,"if(*count&&out[*count-1].line==line&&out[*count-1].range[1]==lo)","if(false&&*count&&out[*count-1].line==line&&out[*count-1].range[1]==lo)")],"test_D43_stagger_band_identity_signed_and_T_point","D43_T_POINT"),
    ("unplaced",[(HOST,"if(!w->wood.timbers[i].placed)continue;uint32_t placement=w->wood.anchors[i].placement_id;","uint32_t placement=w->wood.anchors[i].placement_id;")],"test_R43_unplaced_timbers_on_zero_id_host_do_not_count","PF3_UNPLACED"),
    ("two-sides",[(SOURCE,"if(!present[0]||!present[1])","if(!present[0]&&!present[1])")],"test_D43_holes_notches_and_obstacles_remove_only_one_sided_seams","D43_TWO_SIDES"),
    ("board-vertices",[(SOURCE,"cuts[nc++]=pf_component(frag->loops[l].points[v],other);","if(l==0)cuts[nc++]=pf_component(frag->loops[l].points[v],other);")],"test_PF23_original_algorithm_three_segments_and_same_input_equivalence","PF23_ORIGINAL"),
    ("footprint-vertices",[(SOURCE,"cuts[nc++]=rects[r].lo[other];cuts[nc++]=rects[r].hi[other];","/* removed footprint cuts */")],"test_PF23_E1_legal_five_actual_widths_and_threshold_only","PF23_LEGAL"),
    ("maximal-merge",[(SOURCE,"if(last->seam==seam&&last->range[1]==lo&&last->left==left&&last->right==right)","if(false&&last->seam==seam&&last->range[1]==lo&&last->left==left&&last->right==right)")],"test_PF24_E2_E3_legal_merge_identical_widths","PF24"),
    ("merge-colours",[(SOURCE,"last->left==left&&last->right==right","last->supported==(pf_support_enough(left,threshold)&&pf_support_enough(right,threshold))")],"test_PF23_E1_legal_five_actual_widths_and_threshold_only","PF23_LEGAL"),
    ("open-sample",[(SOURCE,"y2=lo+hi;","y2=2*lo;")],"test_PF23_E1_legal_five_actual_widths_and_threshold_only","PF23_LEGAL"),
    ("footprint-union",[(SOURCE,"out[i].lo<=out[used-1].hi","out[i].lo<out[used-1].hi")],"test_R43_union_continuity_and_ignore_isolated_cut_values","R43_UNION"),
    ("continuous-width",[(SOURCE,"left&&un[i].lo<edge&&edge<=un[i].hi","left&&un[i].lo<edge")],"test_R43_union_continuity_and_ignore_isolated_cut_values","R43_GAP"),
    ("host-identity",[(HOST,"if(placement!=host->id)continue;",""),(REFERENCE,"!reference_member_anchor_read(ctx,index,id,&anchor)||anchor.placement_id!=placement_id||","!reference_member_anchor_read(ctx,index,id,&anchor)||")],"test_R43_no_host_and_other_coplanar_host_do_not_support","PF3_HOST_FILTER"),
    ("finish-reflection",[(HOST,"r->lo[1]=coord_min(finish->side*f.min_v,finish->side*f.max_v);","r->lo[1]=f.min_v;"),(HOST,"r->hi[1]=coord_max(finish->side*f.min_v,finish->side*f.max_v);","r->hi[1]=f.max_v;")],"test_R43_negative_structure_side_and_vertical_frame_real_footprints","R43_FRAME"),
    ("hidden-threshold",[(SOURCE,"return d>x.num/x.den||(d==x.num/x.den&&x.num%x.den==0);","return d>=8;")],"test_PF06_positive_rational_comparison_and_rename_reorder","PF06_RATIONAL"),
    ("rounded-threshold",[(SOURCE,"return d>x.num/x.den||(d==x.num/x.den&&x.num%x.den==0);","return d>=x.num/x.den;")],"test_PF06_positive_rational_comparison_and_rename_reorder","PF06_RATIONAL"),
    ("overflow-comparison",[(SOURCE,"return d>x.num/x.den||(d==x.num/x.den&&x.num%x.den==0);","return (uint64_t)d*(uint64_t)x.den>=(uint64_t)x.num;")],"test_PF06_extreme_rational_does_not_overflow_comparison","PF06_OVERFLOW"),
    ("odd-gap-edges",[(SOURCE,"sl->coordinate-d->gap/2,sl->coordinate+(d->gap-d->gap/2)","sl->coordinate,sl->coordinate")],"test_D43_positive_odd_gap_uses_board_edges_and_both_axes","D43_ODD_GAP"),
    ("band-range",[(SOURCE,"if(sl->staggered&&(lo<sl->range[0]||hi>sl->range[1]))continue;","/* removed band clipping */")],"test_D43_stagger_band_identity_signed_and_T_point","D43_NEGATIVE_BAND"),
    ("capacity-early",[(SOURCE,"if(*count==WOOD_PANEL_SUPPORT_MAX)return (*status=WOOD_PANEL_SUPPORT_SEAM_LIMIT,false)","if(*count==WOOD_PANEL_SUPPORT_MAX-1)return (*status=WOOD_PANEL_SUPPORT_SEAM_LIMIT,false)")],"test_PF13_capacity_N_N1_is_complete_or_explicit_rejection","PF3_CAPACITY_N"),
    ("capacity-truncate",[(SOURCE,"if(*count==WOOD_PANEL_SUPPORT_MAX)return (*status=WOOD_PANEL_SUPPORT_SEAM_LIMIT,false);","if(*count==WOOD_PANEL_SUPPORT_MAX)return true;"),
                          (SOURCE,"if(s->part_count==WOOD_PANEL_SUPPORT_MAX){status=WOOD_PANEL_SUPPORT_PART_LIMIT;goto done;}","if(s->part_count==WOOD_PANEL_SUPPORT_MAX)continue;")],"test_PF13_capacity_N_N1_is_complete_or_explicit_rejection","PF3_CAPACITY_N1"),
]


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def run(out,argv,cwd,env):
    started=time.monotonic()
    with (out/"stdout").open("wb") as so,(out/"stderr").open("wb") as se:
        p=subprocess.run(argv,cwd=cwd,env=env,stdout=so,stderr=se,timeout=900)
    write(out/"execution.json",dict(argv=argv,cwd=str(cwd),exit=p.returncode,seconds=time.monotonic()-started))
    return p.returncode


def child_main(binary_dir,selection):
    # Standard unittest execution plus structured counts, so import/compile
    # errors and skips cannot be mislabeled as semantic kills.
    import unittest
    sys.path.insert(0,str(Path.cwd()))
    from tests import test_panel_fill_support as module
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(module.PanelFillSupport) if selection=="all" else unittest.defaultTestLoader.loadTestsFromName(selection,module.PanelFillSupport)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    write(Path(binary_dir)/"tests.json",dict(run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped)))
    return 0 if result.wasSuccessful() else 1


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--out",type=Path,required=True);parser.add_argument("--jobs",type=int,default=2)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    if os.name!="nt":
        import resource
        resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
    paths=[ROOT/"current_geometry.c"]
    for directory in ("geometry-core","geometry-web","geometry-app","geometry-templates"):
        paths.extend(p for p in (ROOT/directory).rglob("*") if p.suffix in (".c",".h",".inc") and not any(x in p.parts for x in ("vendor","node_modules")))
    paths.extend(p for p in (ROOT/"tests").glob("*") if p.name in ("__init__.py","binaries.py","_bridge.py","pfh_oracle.py","pf3_algorithm.c","pf3_mutation_check.py") or p.name.startswith("test_panel_fill_"))
    original={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
    write(out/"sources.json",{p:hashlib.sha256(b).hexdigest() for p,b in original.items()})

    def execute(case):
        name,changes,selection,marker=case;directory=out/name;repo=directory/"source";repo.mkdir(parents=True)
        for rel,contents in original.items():
            target=repo/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(contents)
        for rel,old,new in changes:
            target=repo/rel;data=target.read_bytes();old=old.encode();new=new.encode();assert data.count(old)==1,(name,rel,old);target.write_bytes(data.replace(old,new))
        binaries=directory/"binaries";env={**os.environ,"GEOMETRY_TEST_BRIDGE":str(binaries/("bridge.exe" if os.name=="nt" else "bridge")),"GEOMETRY_TEST_PF3_ALGORITHM":str(binaries/("pf3-algorithm.exe" if os.name=="nt" else "pf3-algorithm"))}
        build=directory/"build";build.mkdir()
        code="import sys;from pathlib import Path;sys.path.insert(0,'tests');import binaries;binaries.OUT_DIR=Path(sys.argv[1]);raise SystemExit(binaries.main(['build','bridge','pf3-algorithm']))"
        build_exit=run(build,[sys.executable,"-c",code,str(binaries)],repo,env)
        if build_exit:return dict(id=name,verdict="invalid",buildExit=build_exit)
        tests=directory/"tests";tests.mkdir()
        argv=[sys.executable,"tests/pf3_mutation_check.py","--child",str(binaries),selection]
        actual=run(tests,argv,repo,env);counts=json.loads((binaries/"tests.json").read_text())
        stderr=(tests/"stderr").read_text();good=(actual==0 and counts==dict(run=20,failures=0,errors=0,skipped=0)) if name in ("baseline","restored") else (actual==1 and counts==dict(run=1,failures=1,errors=0,skipped=0) and marker in stderr)
        hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in binaries.iterdir() if p.is_file()}
        record=dict(id=name,verdict="pass" if name in ("baseline","restored") and good else "killed" if good else "not-killed",exit=actual,counts=counts,requiredMarker=marker,artifacts=hashes)
        write(directory/"result.json",record);print(json.dumps(record),flush=True);return record

    baseline=execute(("baseline",[],"all",""))
    if baseline["verdict"]!="pass":write(out/"summary.json",[baseline]);return 2
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:records=list(pool.map(execute,CASES))
    restored=execute(("restored",[],"all",""))
    unchanged=all((ROOT/p).read_bytes()==b for p,b in original.items())
    for record in records:
        if record.get("artifacts",{}).get("bridge")==baseline["artifacts"].get("bridge"):record["verdict"]="identical-binary"
    write(out/"summary.json",dict(baseline=baseline,mutations=records,restored=restored,originalSourcesUnchanged=unchanged))
    return 0 if unchanged and restored["verdict"]=="pass" and all(r["verdict"]=="killed" for r in records) else 1


if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="--child":raise SystemExit(child_main(sys.argv[2],sys.argv[3]))
    raise SystemExit(main())
