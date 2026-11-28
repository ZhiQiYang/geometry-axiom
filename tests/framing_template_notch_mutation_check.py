#!/usr/bin/env python3
"""R03B real W-header withdrawals, compiled and run in an isolated directory.

The unchanged Python reference is an expected-output oracle only.  Every accepted
C result is also checked by the independent true-region/board-edge checker.  This
runner proves W generator source behavior; it does not claim bridge, history, or
Chrome execution.  Compiler errors, abnormal exits, and timeouts are blocked,
never kills.  No-argument execution first checks out-of-range input under UBSan,
then performs all baseline/withdrawn/restored runs.  The range regression is an
ordinary product test; a sanitizer failure is never counted as a mutant kill.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "geometry-templates/woodworking/native"
HEADER = "flat_ceiling_notch.h"
HEADERS = (HEADER, "flat_ceiling_jig.h", "flat_ceiling.h")
CHECKER_PATH = ROOT / "tests/diagnostics/r03_notch_oracle.py"
REFERENCE_PATH = ROOT / "geometry-core/framing-template/oracle/framing_oracle.py"
COMPILE_TIMEOUT = 60
EXECUTION_TIMEOUT = 15
JUDGE_TIMEOUT = 60


DRIVER = r'''#include <stdio.h>
#include <inttypes.h>
#include "flat_ceiling_notch.h"
static void ints(const int64_t *v,size_t n){putchar('[');for(size_t i=0;i<n;++i){if(i)putchar(',');printf("%" PRId64,v[i]);}putchar(']');}
static void base(const WoodFlatPlan *p){
    printf("{\"count\":%zu,\"origin\":",p->count);ints(p->origin,2);
    printf(",\"seams\":[");ints(p->seams[0],p->seam_count[0]);putchar(',');ints(p->seams[1],p->seam_count[1]);
    printf("],\"marks\":");ints(p->marks,p->mark_count);printf(",\"members\":[");
    for(size_t i=0;i<p->count&&i<WOOD_FLAT_MEMBERS;++i){const WoodFlatMember *m=&p->members[i];if(i)putchar(',');
        printf("{\"kind\":%d,\"axis\":%d,\"rect\":",m->kind,m->axis);ints(m->rect,4);printf(",\"center\":%" PRId64 "}",m->center);}
    printf("]}");
}
int main(void){
    int64_t points[8][2];size_t n;WoodFlatParameters v={0};int sx,sy;int64_t xn,xd;
    if(scanf("%zu",&n)!=1||n>8)return 2;
    for(size_t i=0;i<n;++i)if(scanf("%" SCNd64 " %" SCNd64,&points[i][0],&points[i][1])!=2)return 2;
    if(scanf("%" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %" SCNd64 " %d %d %d %" SCNd64 " %" SCNd64,
             &v.panel[0],&v.panel[1],&v.gap,&v.width,&v.depth,&v.maximum,&v.length_axis,&sx,&sy,&xn,&xd)!=11)return 2;
    v.start_max[0]=sx!=0;v.start_max[1]=sy!=0;
    WoodNotchRegion region;bool valid=wood_notch_region(points,n,&region);WoodNotchInterval iv={0,0};bool band=false;
    if(valid&&region.is_l)band=wood_notch_band(&region,1,region.notch[0]+1,region.notch[2]-1,&iv);
    WoodNotchPlan plan;bool ok=wood_notch_build(points,n,&v,xn,xd,&plan);
    printf("{\"ok\":%s,\"code\":\"%s\",\"band\":",ok?"true":"false",plan.base.code?plan.base.code:"");
    if(band){int64_t values[2]={iv.lo,iv.hi};ints(values,2);}else printf("null");
    printf(",\"base\":");base(&plan.base);printf(",\"sources\":[");
    for(size_t i=0;i<plan.base.count&&i<WOOD_FLAT_MEMBERS;++i){const WoodNotchSource *s=&plan.source[i];if(i)putchar(',');
        printf("{\"edge\":%d,\"role\":%d,\"priority\":%d,\"stop_kind\":[%d,%d],\"stop_index\":[%d,%d],\"extension\":[%s,%s]}",
               s->anchor_edge,s->role,s->priority,s->stop_kind[0],s->stop_kind[1],s->stop_index[0],s->stop_index[1],s->extension[0]?"true":"false",s->extension[1]?"true":"false");}
    printf("],\"order\":[");for(size_t i=0;i<plan.base.count&&i<WOOD_FLAT_MEMBERS;++i){if(i)putchar(',');printf("%zu",plan.order[i]);}putchar(']');
    if(valid&&!region.is_l){WoodFlatPlan old;bool oldok=wood_flat_jig_build(region.bounds,&v,&old);printf(",\"v2_ok\":%s,\"v2\":",oldok?"true":"false");base(&old);}
    puts("}");return 0;
}
'''


# A single, byte-exact source replacement is required for each withdrawal.
FAULTS = (
    ("R03B_W_SOURCE_ORIGIN_SHIFT", "R03B_W_GLOBAL_ORIGIN",
     "p->origin[k]=v->start_max[k]?hi-size:lo;",
     "p->origin[k]=(v->start_max[k]?hi-size:lo)+20;"),
    ("R03B_W_BBOX_FOR_TRUE_REGION", "R03B_W_TRUE_REGION_BAND",
     "if(r->is_l&&cross_lo<r->notch[q+2]&&r->notch[q]<cross_hi){",
     "if(false&&r->is_l&&cross_lo<r->notch[q+2]&&r->notch[q]<cross_hi){"),
    ("R03B_W_WITHDRAW_CUSTOM3", "R03B_W_L_CANDIDATE_REQUIRED",
     "p->source[i].role=3;p->source[i].priority=3;",
     "p->source[i].role=1;p->source[i].priority=2;"),
    ("R03B_W_WITHDRAW_CUSTOM4", "R03B_W_L_CANDIDATE_REQUIRED",
     "p->source[i].role=3;p->source[i].priority=4;",
     "p->source[i].role=2;p->source[i].priority=3;"),
    ("R03B_W_WITHDRAW_DEPENDENCY_ORDER", "R03B_W_DEPENDENCY_ORDER",
     "done[pick]=true;p->order[at]=pick;",
     "done[pick]=true;p->order[at]=at;"),
    ("R03B_W_KEEP_PARTIAL_ROWS_ON_FAILURE", "R03B_W_CAPACITY_ZERO_ROWS",
     "{memset(p,0,sizeof *p);p->base.code=code;p->base.reason=why;return false;}",
     "{p->base.code=code;p->base.reason=why;return false;}"),
)


class Blocked(RuntimeError):
    """Unavailable or invalid execution cannot establish a killed mutant."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command(args, *, cwd, stdin=None, timeout, directory, label):
    start = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.run(args, cwd=cwd, input=stdin, capture_output=True, timeout=timeout)
        stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout, stderr, exit_code = exc.stdout or b"", exc.stderr or b"", None
    except OSError as exc:
        stdout, stderr, exit_code = b"", str(exc).encode("utf-8"), None
    duration = time.monotonic() - start
    directory.mkdir(parents=True, exist_ok=True)
    stdout_path, stderr_path = directory / (label + ".stdout"), directory / (label + ".stderr")
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    receipt = dict(command=[str(v) for v in args], cwd=str(cwd), exit=exit_code,
                   timed_out=timed_out, seconds=duration,
                   stdout=dict(path=stdout_path.name, bytes=len(stdout), sha256=sha(stdout)),
                   stderr=dict(path=stderr_path.name, bytes=len(stderr), sha256=sha(stderr)))
    if stdin is not None:
        (directory / (label + ".stdin")).write_bytes(stdin)
        receipt["stdin"] = dict(bytes=len(stdin), sha256=sha(stdin))
    write_json(directory / (label + ".execution.json"), receipt)
    return receipt, stdout, stderr


def require(value, name, detail=None):
    if not value:
        raise AssertionError(name + (": " + json.dumps(detail, ensure_ascii=False) if detail is not None else ""))


def checker_module():
    spec = importlib.util.spec_from_file_location("r03b_independent_checker", CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request(points, gap=2, length_axis=1, start=(False, False)):
    panels = [915, 1830] if length_axis == 1 else [1830, 915]
    values = [len(points)] + [x for p in points for x in p]
    values += panels + [gap, 27, 27, 367, length_axis, *map(int, start), 8, 1]
    return (" ".join(map(str, values)) + "\n").encode("ascii")


def execute(binary, name, points, directory, gap=2, length_axis=1, start=(False, False)):
    receipt, stdout, _ = command([str(binary)], cwd=binary.parent,
                                 stdin=request(points, gap, length_axis, start),
                                 timeout=EXECUTION_TIMEOUT, directory=directory, label=name)
    if receipt["exit"] != 0 or receipt["timed_out"]:
        raise Blocked("R03B_W_DRIVER_EXECUTION: " + json.dumps(receipt))
    try:
        return json.loads(stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Blocked("R03B_W_DRIVER_JSON: " + name) from exc


def actual_result(data, room, length_axis):
    """Convert real C rows, not reference rows, for independent physical checks."""
    a, b = 1 - length_axis, length_axis
    kinds = ("boundary", "main", "rc_parallel", "secondary", "secondary")
    result = dict(a=a, b=b, seams_a=data["base"]["seams"][a],
                  seams_b=data["base"]["seams"][b], timbers=[])
    for i, (m, source) in enumerate(zip(data["base"]["members"], data["sources"])):
        t = dict(id=i, kind=kinds[m["kind"]], rect=m["rect"])
        if m["kind"] >= 3:
            t["role"] = "mark" if m["kind"] == 3 else "seam"
        if source["role"] == 3:
            t.update(core_role="custom", priority=source["priority"])
        if m["kind"] == 1:
            t["seam"] = m["center"]
        if m["kind"] == 0:
            edge = source["edge"]
            require(0 <= edge < len(room["outer"]), "R03B_W_RC_EDGE_SOURCE", source)
            p, q = room["outer"][edge], room["outer"][(edge + 1) % len(room["outer"])]
            t["edge"] = sorted((p[a], q[a]))
        result["timbers"].append(t)
    return result


def verify_positive(checker, data, points, *, gap=2, length_axis=1, start=(False, False)):
    room = dict(outer=points)
    _, shape = checker.normalize_room(room)
    if shape["shape"] == "L":
        bounds, notch = shape["bbox"], shape["notch"]
        expected_band = [notch[3], bounds[3]] if notch[1] == bounds[1] else [bounds[1], notch[1]]
        require(data["band"] == expected_band, "R03B_W_TRUE_REGION_BAND", data["band"])
    require(data["ok"], "R03B_W_L_CANDIDATE_REQUIRED", dict(shape=shape, code=data["code"]))
    base, sources = data["base"], data["sources"]
    require(0 < base["count"] <= 512 and len(base["members"]) == len(sources) == base["count"],
            "R03B_W_COMPLETE_ROWS", base["count"])
    a, b = 1 - length_axis, length_axis
    panels = [915, 1830] if b == 1 else [1830, 915]
    expected_origin = [shape["bbox"][axis + 2] - panels[axis] if start[axis] else shape["bbox"][axis]
                       for axis in (0, 1)]
    require(base["origin"] == expected_origin, "R03B_W_GLOBAL_ORIGIN", base["origin"])
    layout = dict(A="xy"[a], a_start="max" if start[a] else "min", b_start="max" if start[b] else "min")
    params = dict(checker.PARAMS, gap=gap)
    expected = checker.REFERENCE.build(room, layout, params)
    require(not expected["conflicts"] and not expected["core_limits"] and not checker.REFERENCE.check(expected, params),
            "R03B_W_REFERENCE_FIXTURE_VALID")
    result = actual_result(data, room, b)
    actual_rows = []
    for m, source in zip(base["members"], sources):
        actual_rows.append((m["kind"], tuple(m["rect"]), m["axis"],
                            m["rect"][m["axis"] + 2] - m["rect"][m["axis"]],
                            source["role"], source["priority"]))
    expected_rows = []
    for t in expected["timbers"]:
        kind = {"boundary": 0, "main": 1, "rc_parallel": 2, "secondary": 3}[t["kind"]]
        if kind == 3 and t["role"] == "seam":
            kind = 4
        role_name, priority = checker.role(t)
        axis = b if kind in (1, 2) else a
        expected_rows.append((kind, tuple(t["rect"]), axis, t["rect"][axis + 2] - t["rect"][axis],
                              {"boundary": 0, "primary": 1, "secondary": 2, "custom": 3}[role_name], priority))
    require(sorted(actual_rows) == sorted(expected_rows), "R03B_W_ORACLE_EVERY_MEMBER")
    require(base["seams"][a] == sorted(expected["seams_a"]) and base["seams"][b] == sorted(expected["seams_b"]),
            "R03B_W_GLOBAL_SEAMS")
    failures, boards = checker.independent_check(room, result, params, layout)
    require(not failures, "R03B_W_INDEPENDENT_PHYSICS", failures)
    require(sorted(data["order"]) == list(range(base["count"])), "R03B_W_DEPENDENCY_ORDER")
    position = {member: at for at, member in enumerate(data["order"])}
    for i, source in enumerate(sources):
        for kind, target in zip(source["stop_kind"], source["stop_index"]):
            require(kind in (0, 1), "R03B_W_STOP_SOURCE")
            if kind == 1:
                require(target in position and position[target] < position[i], "R03B_W_DEPENDENCY_ORDER",
                        dict(member=i, stop=target, order=data["order"]))
            else:
                require(0 <= target < len(points), "R03B_W_STOP_SOURCE")
    if shape["shape"] == "L":
        require(any(s["role"] == 3 and s["priority"] == 3 for s in sources), "R03B_W_CUSTOM3")
        require(any(s["role"] == 3 and s["priority"] == 4 for s in sources), "R03B_W_CUSTOM4")
    else:
        require(data["v2_ok"] and data["v2"] == base, "R03B_W_RECTANGLE_EXACT_V2")
    return dict(members=base["count"], boards=len(boards), independent_failures=len(failures))


def judge(binary, directory):
    checker = checker_module()
    l_points = checker.L_ROOM["outer"]
    cases = (
        ("L_gap2", l_points, 2),
        ("L_gap3", l_points, 3),
        ("L_translated", [[x + 127, y - 202] for x, y in l_points], 2),
        ("L_reversed", list(reversed(l_points)), 2),
        ("rectangle", [[0, 0], [3740, 0], [3740, 3301], [0, 3301]], 2),
    )
    result = {}
    for name, points, gap in cases:
        data = execute(binary, name, points, directory, gap=gap)
        result[name] = verify_positive(checker, data, points, gap=gap)
    negative = (
        ("capacity", [[0, 0], [19000, 0], [19000, 19000], [0, 19000]], "CAPACITY", "R03B_W_CAPACITY_ZERO_ROWS"),
        ("unsupported_U", checker.U_ROOM["outer"], "UNSUPPORTED_SCOPE", "R03B_W_UNSUPPORTED_ZERO_ROWS"),
    )
    for name, points, code, marker in negative:
        data = execute(binary, name, points, directory)
        require(not data["ok"] and data["code"] == code, marker, dict(ok=data["ok"], code=data["code"]))
        require(data["base"]["count"] == 0 and not data["base"]["members"] and not data["sources"], marker,
                dict(count=data["base"]["count"]))
        result[name] = dict(code=code, rows=0)
    print(json.dumps(dict(status="passed", layer="compiled-W-header", cases=result), ensure_ascii=False))


def phase(source, original, directory, isolated):
    directory.mkdir(parents=True, exist_ok=True)
    for header, data in original.items():
        (isolated / header).write_bytes(source if header == HEADER else data)
    (isolated / "driver.c").write_text(DRIVER, encoding="utf-8")
    sources = {header: (isolated / header).read_bytes() for header in HEADERS}
    # Retain the actual compiled source, not just the replacement recipe.
    (directory / HEADER).write_bytes(sources[HEADER])
    executable = isolated / ("driver.exe" if os.name == "nt" else "driver")
    if executable.exists():
        executable.unlink()
    cc = shlex.split(os.environ.get("CC", "cc"))
    args = cc + ["-std=c11", "-O1", "-Wall", "-Wextra", "-Wno-unused-function", str(isolated / "driver.c"), "-o", str(executable)]
    build, _, _ = command(args, cwd=isolated, timeout=COMPILE_TIMEOUT, directory=directory, label="compile")
    info = dict(source_sha256=sha(sources[HEADER]), source_bytes=len(sources[HEADER]), source_path=HEADER,
                closure_sha256={key: sha(value) for key, value in sources.items()}, build=build)
    if build["exit"] != 0 or build["timed_out"] or not executable.is_file():
        info.update(status="blocked", reason="compile")
        write_json(directory / "phase.json", info)
        return info
    info["binary_sha256"] = sha(executable.read_bytes())
    run, _, stderr = command([sys.executable, "-B", str(Path(__file__).resolve()), "--judge", str(executable),
                              "--case-dir", str(directory / "cases")], cwd=ROOT,
                             timeout=JUDGE_TIMEOUT, directory=directory, label="judge")
    unchanged = all((isolated / key).read_bytes() == value for key, value in sources.items())
    info.update(run=run, source_unchanged_through_run=unchanged,
                assertion=re.findall(r"^AssertionError: ([A-Z0-9_]+)(?::|$)", stderr.decode("utf-8", "replace"), re.M))
    info["status"] = "complete" if run["exit"] in (0, 1) and not run["timed_out"] and unchanged else "blocked"
    write_json(directory / "phase.json", info)
    return info


def range_regression(directory):
    """D1: reject every input coordinate before evaluating any shoelace term."""
    directory.mkdir(parents=True, exist_ok=True)
    originals = {header: (SOURCE_DIR / header).read_bytes() for header in HEADERS}
    info = dict(schema="r03b-w-range-regression/1", layer="compiled-W-header",
                assertion="R03B_W_D1_RANGE_SAFE_REJECTION", mutation_kill=False,
                closure_sha256={key: sha(value) for key, value in originals.items()},
                judge_sha256=sha(Path(__file__).read_bytes()), driver_sha256=sha(DRIVER.encode("utf-8")))
    with tempfile.TemporaryDirectory(prefix="r03b-w-range-") as isolated_name:
        isolated = Path(isolated_name)
        for header, data in originals.items():
            (isolated / header).write_bytes(data)
        (directory / HEADER).write_bytes(originals[HEADER])
        (isolated / "driver.c").write_text(DRIVER, encoding="utf-8")
        binary = isolated / ("driver.exe" if os.name == "nt" else "driver")
        cc = shlex.split(os.environ.get("CC", "cc"))
        args = cc + ["-std=c11", "-O1", "-fsanitize=undefined", "-fno-sanitize-recover=all",
                     "-Wall", "-Wextra", "-Wno-unused-function", str(isolated / "driver.c"), "-o", str(binary)]
        build, _, _ = command(args, cwd=isolated, timeout=COMPILE_TIMEOUT, directory=directory, label="compile")
        info["build"] = build
        if build["exit"] != 0 or build["timed_out"] or not binary.is_file():
            info.update(status="blocked", reason="compile")
            exit_code = 2
        else:
            # p is in range, but the next q is not.  Checking only p inside the
            # arithmetic loop allows p.x * q.y to overflow before q is checked.
            maximum = 9223372036854775807
            points = [[100000000, 100000000], [100000000, maximum],
                      [0, maximum], [0, 100000000]]
            info["binary_sha256"] = sha(binary.read_bytes())
            run, stdout, stderr = command([str(binary)], cwd=isolated, stdin=request(points),
                                          timeout=EXECUTION_TIMEOUT, directory=directory, label="D1_next_vertex_int64_max")
            info["run"] = run
            if run["timed_out"] or run["exit"] is None or run["exit"] < 0:
                info.update(status="blocked", reason="execution")
                exit_code = 2
            elif run["exit"] != 0:
                if b"runtime error:" in stderr:
                    info.update(status="failed", reason="undefined-behavior-before-range-rejection")
                    exit_code = 1
                else:
                    info.update(status="blocked", reason="unexpected-driver-exit")
                    exit_code = 2
            else:
                try:
                    data = json.loads(stdout)
                    passed = (data["ok"] is False and data["code"] == "UNSUPPORTED_SCOPE"
                              and data["base"]["count"] == 0 and not data["base"]["members"]
                              and not data["sources"] and not stderr)
                    info.update(status="passed" if passed else "failed", observed=data)
                    exit_code = 0 if passed else 1
                except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
                    info.update(status="blocked", reason="driver-json")
                    exit_code = 2
    info["worktree_unchanged"] = all((SOURCE_DIR / key).read_bytes() == value for key, value in originals.items())
    if not info["worktree_unchanged"]:
        info.update(status="blocked", reason="source-changed-during-regression")
        exit_code = 2
    info["exit"] = exit_code
    write_json(directory / "receipt.json", info)
    print(json.dumps({key: info[key] for key in ("assertion", "status", "mutation_kill", "exit")}), flush=True)
    if exit_code:
        print(info["assertion"] + ": " + info.get("reason", "unsafe rejection"), file=sys.stderr)
    return exit_code


def run_withdrawals(directory):
    directory.mkdir(parents=True, exist_ok=True)
    regression_exit = range_regression(directory / "D1_range_regression")
    if regression_exit:
        return regression_exit
    originals = {header: (SOURCE_DIR / header).read_bytes() for header in HEADERS}
    original = originals[HEADER]
    inputs = dict(headers={k: dict(bytes=len(v), sha256=sha(v)) for k, v in originals.items()},
                  judge=dict(path=str(Path(__file__).relative_to(ROOT)), sha256=sha(Path(__file__).read_bytes())),
                  checker_sha256=sha(CHECKER_PATH.read_bytes()), reference_sha256=sha(REFERENCE_PATH.read_bytes()),
                  driver_sha256=sha(DRIVER.encode("utf-8")))
    rows = []
    blocked = False
    for name, assertion, before, after in FAULTS:
        old, new = before.encode("utf-8"), after.encode("utf-8")
        if original.count(old) != 1:
            rows.append(dict(id=name, status="blocked", reason="anchor", found=original.count(old)))
            blocked = True
            continue
        mutant = original.replace(old, new, 1)
        case_dir = directory / name
        phases = []
        with tempfile.TemporaryDirectory(prefix="r03b-w-") as isolated_name:
            isolated = Path(isolated_name)
            for phase_name, source in (("baseline", original), ("withdrawn", mutant), ("restored", original)):
                phases.append(phase(source, originals, case_dir / phase_name, isolated))
            restored_bytes = (isolated / HEADER).read_bytes() == original
        exit_codes = [p.get("run", {}).get("exit") for p in phases]
        exact = phases[1].get("assertion") == [assertion]
        restored_bytes = restored_bytes and phases[0]["source_sha256"] == phases[2]["source_sha256"] == sha(original)
        worktree_unchanged = all((SOURCE_DIR / key).read_bytes() == value for key, value in originals.items())
        if any(p["status"] == "blocked" for p in phases):
            status = "blocked"
            blocked = True
        elif exit_codes == [0, 1, 0] and exact and restored_bytes and worktree_unchanged:
            status = "killed"
        else:
            status = "invalid" if exit_codes[0] != 0 or exit_codes[2] != 0 or not worktree_unchanged else "survived"
        row = dict(id=name, expected_assertion=assertion, status=status, exits=exit_codes,
                   exact_assertion=exact, isolated_source_restored=restored_bytes,
                   worktree_unchanged=worktree_unchanged, mutant_sha256=sha(mutant),
                   phase_paths=[str(case_dir.relative_to(directory) / key / "phase.json")
                                for key in ("baseline", "withdrawn", "restored")])
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    summary = dict(schema="r03b-w-source-withdrawals/1", layer="compiled-W-header",
                   inputs=inputs, records=rows, killed=sum(r["status"] == "killed" for r in rows),
                   total=len(FAULTS), range_regression="D1_range_regression/receipt.json",
                   official_workflow=False, bridge_or_browser_executed=False)
    write_json(directory / "receipt.json", summary)
    return 2 if blocked else 0 if all(r["status"] == "killed" for r in rows) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--probe-range", action="store_true", help="run only the UBSan D1 range regression")
    parser.add_argument("--judge", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--case-dir", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.judge:
        if args.case_dir is None:
            parser.error("--judge requires --case-dir")
        judge(args.judge, args.case_dir)
        return 0
    run = range_regression if args.probe_range else run_withdrawals
    if args.out:
        return run(args.out.resolve())
    with tempfile.TemporaryDirectory(prefix="r03b-w-withdrawals-") as name:
        return run(Path(name))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Blocked as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
