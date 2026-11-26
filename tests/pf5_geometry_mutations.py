"""Replay named PF-5 diagnostic source mutations in isolated temporary copies.

Writes local raw 0/1/0 evidence, never the project's official mutation ledger.
Neither source output tampering nor import/setup errors count as a killed source
mutation. Repository inputs are read only. No C build or browser is invoked.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
FILES = ("test_pf5_geometry_oracle.py", "pf5_geometry_oracle.py", "pf5_geometry_check.py")


def mutation(name, module, before, after, test):
    return {"name": name, "file": module, "before": before, "after": after,
            "test": "PF5GeometryOracle."+test}


MUTATIONS = [
    mutation("PF5_CONTACT_IS_COLLISION", "pf5_geometry_oracle.py",
             "return max(interval[0], layer[0]) < min(interval[1], layer[1])",
             "return max(interval[0], layer[0]) <= min(interval[1], layer[1])",
             "test_Q47_three_heights_and_exact_touch_are_separate_layers"),
    mutation("PF5_COLLAPSE_TWO_LAYERS", "pf5_geometry_oracle.py",
             'intervals = {"panel": (0, t), "timber": (t, t+h)}',
             'intervals = {"panel": (0, t+h), "timber": (0, t+h)}',
             "test_Q47_three_heights_and_exact_touch_are_separate_layers"),
    mutation("PF5_WORLD_Z_INSTEAD_OF_NORMAL", "pf5_geometry_oracle.py",
             'axes = [frame["u"], frame["v"], [f["side"]*x for x in frame["n"]]]',
             'axes = [frame["u"], frame["v"], [0, 0, 1]]',
             "test_vertical_normal_and_negative_side_board_back"),
    mutation("PF5_FORGET_SIDE_IN_BOARD_BACK_FRAME", "pf5_geometry_oracle.py",
             '"v": [side*x for x in frame["v"]], "n": [side*x for x in frame["n"]]}',
             '"v": list(frame["v"]), "n": [side*x for x in frame["n"]]}',
             "test_vertical_normal_and_negative_side_board_back"),
    mutation("PF5_FORGET_HOST_REGION_REFLECTION", "pf5_geometry_oracle.py",
             'host_rectangles = [(r[0], min(side*r[1], side*r[3]), r[2], max(side*r[1], side*r[3])) for r in layers["timber"]]',
             'host_rectangles = list(layers["timber"])',
             "test_vertical_normal_and_negative_side_board_back"),
    mutation("PF5_DROP_LATER_COMPONENTS", "pf5_geometry_oracle.py",
             '"components": components}', '"components": components[:1]}',
             "test_hole_and_disconnected_components_are_retained"),
    mutation("PF5_AUTO_INCLUDE_UNSELECTED_OBSTACLES", "pf5_geometry_oracle.py",
             'selected = f["obstacles"]', 'selected = list(objects)',
             "test_selected_obstacles_only_and_no_automatic_wrap_faces"),
    mutation("PF5_AUTO_CHOOSE_JOINT_POLICY", "pf5_geometry_oracle.py",
             '"joinPolicy": "unselected"', '"joinPolicy": "ceiling-over-wall"',
             "test_explicit_high_ceiling_low_beam_bottom_and_side_closure"),
    mutation("PF5_CHECKER_BLIND_TO_ALL_CORRUPTION", "pf5_geometry_check.py",
             "    return errors\n\n\ndef main", "    return []\n\n\ndef main",
             "test_independent_checker_rejects_corrupt_outputs"),
    mutation("PF5_CHECKER_IGNORES_WINDING", "pf5_geometry_check.py",
             "if oriented and (signed_area2 <= 0 if index == 0 else signed_area2 >= 0):",
             "if False and oriented and (signed_area2 <= 0 if index == 0 else signed_area2 >= 0):",
             "test_independent_checker_rejects_corrupt_outputs"),
    mutation("PF5_CHECKER_IGNORES_RIGHT_HANDED_SOURCE", "pf5_geometry_check.py",
             'if u[0]*(v[1]*n[2]-v[2]*n[1])-u[1]*(v[0]*n[2]-v[2]*n[0])+u[2]*(v[0]*n[1]-v[1]*n[0]) != 1:',
             'if u[0]*(v[1]*n[2]-v[2]*n[1])-u[1]*(v[0]*n[2]-v[2]*n[0])+u[2]*(v[0]*n[1]-v[1]*n[0]) == 0:',
             "test_checker_independently_rejects_left_handed_source_even_if_output_agrees"),
    mutation("PF5_CHECKER_ACCEPTS_UNDECLARED_POLICY_FIELDS", "pf5_geometry_check.py",
             "if type(value) is not dict or set(value) != set(expected.split()):",
             "if False and (type(value) is not dict or set(value) != set(expected.split())):",
             "test_checker_rejects_unknown_joint_policies_and_missing_relationships"),
]


def fingerprint(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def run(directory, log, test=None):
    command = [sys.executable, "-B", str(directory/FILES[0]), "-v"] + ([test] if test else [])
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, cwd=directory, env=environment, capture_output=True, text=True)
    raw = result.stdout+result.stderr
    log.write_bytes((raw+"\nexit="+str(result.returncode)+"\n").encode("utf-8"))
    return {"exit": result.returncode, "command": command, "log": log.name,
            "assertionFailure": "AssertionError" in raw and "FAIL:" in raw,
            "setupOrExecutionError": "ERROR:" in raw or "ImportError" in raw or "SyntaxError" in raw,
            **fingerprint(log.read_bytes())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="full 40-character repository HEAD SHA")
    parser.add_argument("--out", required=True, type=Path, help="new evidence directory; existing directory is never overwritten")
    args = parser.parse_args()
    if not re.fullmatch("[0-9a-f]{40}", args.base):
        parser.error("--base must be a full lowercase SHA")
    head = subprocess.run(["git", "-C", str(HERE.parent), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    if head != args.base:
        parser.error("--base differs from the actual repository HEAD")
    args.out.mkdir(parents=True, exist_ok=False)
    sources = {name: (HERE/name).read_bytes() for name in FILES}
    for name, raw in sources.items():
        if b"\r" in raw:
            raise ValueError("PF5 sources must use pure LF: "+name)
    report = {"schema": "pf5-diagnostic-mutation-evidence/1", "base": head,
              "scope": "local diagnostic source mutations; not official mutation:check evidence or product acceptance",
              "python": sys.version, "platform": platform.platform(),
              "sources": {name: fingerprint(raw) for name, raw in sources.items()},
              "runner": fingerprint(Path(__file__).read_bytes()), "mutations": []}
    with tempfile.TemporaryDirectory(prefix="pf5-t-only-") as temp:
        directory = Path(temp)
        (directory/FILES[0]).write_bytes(sources[FILES[0]])
        report["TOnly"] = run(directory, args.out/"T-only-availability-red.log")
        report["TOnly"]["meaning"] = "one missing-tool contract assertion; geometry tests explicitly skipped, not geometry reds"
    report["fullSuite"] = run(HERE, args.out/"P-full-suite.log")
    report["oneMillimetreScan"] = run(HERE, args.out/"scan-one-mm.log", "PF5GeometryOracle.test_integer_mm_scans_depth_plan_position_and_junction_gap")
    report["oneMillimetreScan"]["cases"] = 388
    for item in MUTATIONS:
        original = sources[item["file"]]
        before, after = item["before"].encode("utf-8"), item["after"].encode("utf-8")
        if original.count(before) != 1:
            raise ValueError(item["name"]+": expected exactly one mutation target")
        modified = original.replace(before, after)
        with tempfile.TemporaryDirectory(prefix="pf5-source-mutation-") as temp:
            directory = Path(temp)
            for name, raw in sources.items():
                (directory/name).write_bytes(raw)
            baseline = run(directory, args.out/(item["name"]+"-baseline.log"), item["test"])
            (directory/item["file"]).write_bytes(modified)
            mutant = run(directory, args.out/(item["name"]+"-mutant.log"), item["test"])
            (directory/item["file"]).write_bytes(original)
            restored = run(directory, args.out/(item["name"]+"-restored.log"), item["test"])
            restored_bytes = (directory/item["file"]).read_bytes() == original
        killed = (baseline["exit"], mutant["exit"], restored["exit"]) == (0, 1, 0) and mutant["assertionFailure"] and not mutant["setupOrExecutionError"] and restored_bytes
        report["mutations"].append({**item, "original": fingerprint(original), "mutated": fingerprint(modified),
                                    "baseline": baseline, "mutant": mutant, "restored": restored,
                                    "restoredBytesMatch": restored_bytes, "killed": killed})
        print(item["name"], baseline["exit"], mutant["exit"], restored["exit"], "PASS" if killed else "FAIL", flush=True)
    report["ok"] = (report["TOnly"]["exit"] == 1 and report["TOnly"]["assertionFailure"]
                    and not report["TOnly"]["setupOrExecutionError"] and report["fullSuite"]["exit"] == 0
                    and report["oneMillimetreScan"]["exit"] == 0 and all(item["killed"] for item in report["mutations"]))
    (args.out/"manifest.json").write_bytes((json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+"\n").encode("utf-8"))
    print("manifest:", args.out/"manifest.json", "ok="+str(report["ok"]))
    return int(not report["ok"])


if __name__ == "__main__":
    sys.exit(main())
