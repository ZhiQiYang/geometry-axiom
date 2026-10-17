#!/usr/bin/env python3
"""Run the native-core probes behind PROPOSAL.md B2 (s1-probes/) and blocking item 1 (stagger-probes/).

Each probe is a .scene file fed to the native core (`core --no-window --scene ...`).  The core is compiled from this
repo's current_geometry.c (POSIX: `$CC -std=c11 -O2 current_geometry.c -lm`, the same flags as tests/binaries.py),
or taken from --core.

Stack: several probes (p3, p4, p9 and the q_collinear_* / q_notch_* ones) overflow the default 8 MiB stack of a Linux
shell and die with SIGSEGV before printing anything.  That is the recursion depth of the scene pipeline, not a verdict
on the scene.  Every probe is therefore run with a 64 MiB stack (the same as `ulimit -s 65536`), and once more with an
8 MiB stack only to record which ones need the larger stack.  The Windows build links with /STACK:16777216.

Writes, next to each probe directory:
  summary.txt   commit / blob of current_geometry.c, build command, per probe: exit codes at 64 MiB and 8 MiB,
                the expected verdict, and for accepted probes the cut list (下料清單) lines
  errors.txt    the first stderr line of every probe at 64 MiB (the core's own rejection message)
Exit code 0 only if every probe matches its expectation at 64 MiB.

Usage:
    python3 run_probes.py                 build the core into a temp dir and run every probe
    python3 run_probes.py --core PATH     use an existing core binary
"""
from __future__ import annotations

import argparse
import os
import resource
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DIRS = ["s1-probes", "stagger-probes"]
BIG, SMALL = 64 * 1024 * 1024, 8 * 1024 * 1024

# expected verdict at 64 MiB: (exit code, text that must appear in stderr; None = accepted)
EXPECT = {
    "p1_alcove_wall_primary": (1, "V_EXTENSION"),
    "p2_two_alcoves_middle_edge": (1, "V_EXTENSION"),
    "p3_alcove_side_boundary_then_main": (0, None),
    "p4_alcove_wall_main_lower_piece": (1, "V_CUT_PRIORITY"),
    "p5_wall_main_first_then_side_boundary": (1, "V_EXTENSION"),
    "p6_r14_notch": (1, "V_EXTENSION"),
    "p7_f1_boundary_first": (1, "V_CUT_PRIORITY"),
    "p8_f1_main_first": (1, "V_EXTENSION"),
    "p9_f1_custom_inner_wall": (0, None),
    "q_rect_primary_no_boundary": (1, "只有 boundary 可頂 RC"),
    "q_rect_with_boundaries": (0, None),
    "q_collinear_mid_edge_13": (1, "V_EXTENSION"),
    "q_collinear_mid_edge_14": (0, None),
    "q_collinear_mid_atface_e1": (1, "V_EXTENSION"),
    "q_collinear_mid_two_holes": (1, "跨距起點沒有擋面"),
    "q_hole_1mm_off_wall_through": (1, "跨距起點沒有擋面"),
    "q_notch_atline_113": (1, "V_EXTENSION"),
    "q_notch_atline_114": (0, None),
    "q_hole_touch_outer": (1, "邊界面輪廓不合法"),
    "q_custom_p1_along_e0": (1, "V_EXTENSION"),
    "q_custom_p1_across_wall": (1, "只有 boundary 可頂 RC"),
    "q_one_axis": (0, None),
    "q_two_axis": (0, None),
}


def git(*args: str) -> str:
    p = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else "?"


def run(core: Path, scene: Path, stack: int, out_dir: Path):
    def limit():
        resource.setrlimit(resource.RLIMIT_STACK, (stack, resource.getrlimit(resource.RLIMIT_STACK)[1]))
    svg = out_dir / (scene.stem + ".svg")
    p = subprocess.run([str(core), "--no-window", "--scene", scene.name, "--out", str(svg)],
                       cwd=scene.parent, capture_output=True, preexec_fn=limit, timeout=300)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--core", type=Path)
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        build = f"{os.environ.get('CC', 'cc')} -std=c11 -O2 current_geometry.c -lm -o <tmp>/core"
        if args.core:
            core, build = args.core.resolve(), f"--core {args.core}"
        else:
            core = tmp / "core"
            b = subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-O2", str(ROOT / "current_geometry.c"),
                                "-lm", "-o", str(core)], capture_output=True)
            if b.returncode != 0:
                print(b.stderr.decode("utf-8", "replace")[-2000:])
                return 2
        head = [f"head={git('rev-parse', 'HEAD')} current_geometry.c blob={git('rev-parse', 'HEAD:current_geometry.c')}",
                f"build: {build}",
                "stack: verdicts at 64 MiB (ulimit -s 65536); rc@8MiB only shows which probes need the larger stack "
                "(-11 = SIGSEGV before any output)"]
        all_ok = True
        for d in DIRS:
            summary, errors = list(head), []
            for scene in sorted((HERE / d).glob("*.scene")):
                rc, out, err = run(core, scene, BIG, tmp)
                rc_small = run(core, scene, SMALL, tmp)[0]
                first = err.strip().split("\n")[0] if err.strip() else ""
                exp = EXPECT.get(scene.stem)
                ok = exp is not None and rc == exp[0] and (exp[1] is None or exp[1] in first)
                all_ok &= ok
                cut = [l for l in out.split("\n") if "x27x33" in l or l.startswith("合計")]
                want = "missing expectation" if exp is None else (f"expect rc={exp[0]}" + (f" 「{exp[1]}」" if exp[1] else " accepted"))
                summary.append(f"{'OK ' if ok else 'BAD'} {scene.stem} rc@64MiB={rc} rc@8MiB={rc_small} ({want})"
                               + ("".join(f"\n      {l}" for l in cut) if rc == 0 else ""))
                errors.append(f"{scene.stem}: {first}")
                print(summary[-1])
            (HERE / d / "summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
            (HERE / d / "errors.txt").write_text("\n".join(errors) + "\n", encoding="utf-8")
    print("ALL PROBES AS EXPECTED" if all_ok else "SOME PROBES DIFFER FROM EXPECTATION")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
