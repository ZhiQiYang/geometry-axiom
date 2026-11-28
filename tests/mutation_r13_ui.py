#!/usr/bin/env python3
"""Finite R13 UI/entry withdrawals in disposable source copies; no Chromium.

Each case executes one real Node test before, during and after the withdrawal.
Only its designated ERR_ASSERTION and exact 0/1/0 count as killed. Source syntax,
import failures, crashes and skipped tests cannot earn credit. --out must name
an empty directory outside the checkout. No live source or golden is changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = "b3c4b981bb96b118c1c05b7a1bd98062d710c8b2"
UI = "geometry-web/reconstruction-workspace.js"
SPACE = "geometry-web/space-workspace.js"
APP = "geometry-web/app.js"
UI_TEST = "tests/test_r13_reconstruction_ui.js"
SPACE_TEST = "tests/test_r13_space_entry.js"
SOURCES = {UI: "GEOMETRY_R13_UI_SOURCE", SPACE: "GEOMETRY_R13_SPACE_SOURCE", APP: "GEOMETRY_R13_APP_SOURCE"}
FAULTS = (
    ("R13_UI_IMPLICIT_MM_RESTORED", UI,
     "field.unit??''", "field.unit??'mm'", UI_TEST,
     "R13 UI starts with empty values and records each raw input as manual, without 3000/100", "R13_UNIT_UNKNOWN_VISIBLE"),
    ("R13_UI_UNCHANGED_FLUSH_DUPLICATES_OPERATION", UI,
     "if(sameText(action,current)){ui.draft=null;update();return;}", "// Withdrawal: unchanged raw is written again.", UI_TEST,
     "R13 raw edit commits once per changed input and composing save adds no duplicate operation", "R13_ORACLE_RAW_INPUT_HISTORY"),
    ("R13_UI_COMPOSITION_CONFIRM_GUARD_REMOVED", UI,
     "if(binding.composing)throw Error('文字仍在組字，請先完成輸入再確認或帶入 3D。');", "", UI_TEST,
     "R13 IME may save unfinished raw but cannot confirm or adopt during composition", "R13_COMPOSITION_NOT_CONFIRMATION"),
    ("R13_UI_SHARED_ENTRY_REMOVED", APP,
     '  html += `<details class="ref-section rd-source-group"',
     '  if(!window.RoomCollectionWorkspace?.roomForBoundary(bid))html += `<details class="ref-section rd-source-group"', UI_TEST,
     "R13 actual underlay dispatcher mounts and binds the same editor in ordinary and D13 branches", "R13_ONE_EDITOR_PER_ROUTE_true"),
    ("R13_UI_SUBSET_LABELLED_COMPLETE", UI,
     "current:review.completeness==='defined-subset'?", "current:false?", UI_TEST,
     "R13 saved-model status keeps conditional scope and human-only top checks visible", "R13_PARTIAL_MODEL_IS_NOT_FULLY_REVIEWED"),
    ("R13_ENTRY_IMPLICIT_END_PURPOSES_RESTORED", SPACE,
     "wall_thickness:adopted.wallThickness,floor:'',ceiling:'',holes:'none'",
     "wall_thickness:adopted.wallThickness,floor:'none',ceiling:'none',holes:'none'", SPACE_TEST,
     "R13_ENTRY explicit height input uses the real source reader without defaults or a manual draft", "R13_FLOOR_REQUIRES_EXPLICIT_CHOICE"),
    ("R13_ENTRY_SUBSET_CONSENT_GUARD_REMOVED", SPACE,
     "if(checkControls&&plan.completeness==='defined-subset'&&!$('smReconstructionSubset').checked)\n      throw new Error('請明選「只建立已定資料」，逐項核對未納入的欄位；不會把待補資料標為全部已核對。');",
     "// Withdrawal: no consent for a conditional subset.", SPACE_TEST,
     "R13 subset and each unspecified end face block a real preview before any producer call", "R13_SUBSET_REQUIRES_EXPLICIT_ACCEPTANCE"),
    ("R13_ENTRY_END_PURPOSE_GUARD_REMOVED", SPACE,
     "if(checkControls&&['smFloor','smCeiling'].some(id=>!['boundary','calculation-cap','none'].includes($(id).value)))\n      throw new Error('請明確指定底面與頂面用途；未指定不等於不建立。');",
     "// Withdrawal: treat unspecified end purposes as valid.", SPACE_TEST,
     "R13 subset and each unspecified end face block a real preview before any producer call", "R13_UNSPECIFIED_END_FACE"),
    ("R13_ENTRY_OWNER_SCOPE_OMITTED", SPACE,
     "owner.model,{scopeMode:selected.plan.completeness}", "owner.model", SPACE_TEST,
     "R13_CREATE enters the prepared model-plus-review writer exactly once", "R13_ENTRY_SCOPE_MODE_EXPLICIT"),
    ("R13_ENTRY_OWNER_SCOPE_WRONGLY_COMPLETE", SPACE,
     "owner.model,{scopeMode:selected.plan.completeness}", "owner.model,{scopeMode:'selected-scope-reviewed'}", SPACE_TEST,
     "R13_CREATE enters the prepared model-plus-review writer exactly once", "R13_ENTRY_SCOPE_MODE_EXPLICIT"),
    ("R13_ENTRY_SUPPLIED_VALUE_GUARD_REMOVED", SPACE,
     "if(checkControls&&($('smMode').value!=='plan'||String($('smBottom').value)!==String(plan.bottom)||String($('smHeight').value)!==String(plan.height)||\n        $('smWallsEnabled').checked!==(plan.wallThickness!==null)||String($('smThickness').value)!==(plan.wallThickness===null?'':String(plan.wallThickness))))\n      throw new Error('建模供值與已確認高度不相符，未採用；請返回補資料修正並重新確認。');",
     "// Withdrawal: disabled controls have no authoritative value check.", SPACE_TEST,
     "R13_ENTRY disabled controls still have an authoritative value guard against direct DOM writes", "R13_SUPPLY_DOM_GUARD_smThickness"),
    ("R13_ENTRY_CONDITIONAL_PREVIEW_HIDDEN", SPACE,
     "const scopeNotice=state.reconstruction?.plan.completeness==='defined-subset'?", "const scopeNotice=false?", SPACE_TEST,
     "R13 partial model preview and final review summary identify the conditional result before commit", "R13_PARTIAL_PREVIEW_MUST_BE_CONDITIONAL"),
    ("R13_ENTRY_FINAL_SUBSET_RECHECK_REMOVED", SPACE,
     "assertSourceHistory();assertPlanProjection();assertReconstructionEntry(true,record.input);",
     "assertSourceHistory();assertPlanProjection();", SPACE_TEST,
     "R13 withdrawal of subset acknowledgement after a prepared preview cannot commit a model", "R13_SUBSET_RECHECK_BEFORE_COMMIT"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(command: list[str], env: dict, target: Path) -> tuple[dict, str]:
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=45)
    target.with_suffix(".stdout").write_bytes(result.stdout)
    target.with_suffix(".stderr").write_bytes(result.stderr)
    output = (result.stdout + result.stderr).decode("utf-8", "replace")
    counts = {key: int(value) for key, value in re.findall(r"^# (tests|pass|fail|cancelled|skipped|todo) (\d+)$", output, re.M)}
    record = {"command": command, "exit": result.returncode, "counts": counts,
              "stdoutBytes": len(result.stdout), "stdoutSha256": sha(result.stdout),
              "stderrBytes": len(result.stderr), "stderrSha256": sha(result.stderr)}
    target.with_suffix(".json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record, output


def green(result: dict, count: int) -> bool:
    counts = result["counts"]
    return result["exit"] == 0 and counts.get("tests") == count and counts.get("pass") == count and all(
        counts.get(key) == 0 for key in ("fail", "cancelled", "skipped", "todo"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", choices=[row[0] for row in FAULTS])
    args = parser.parse_args()
    out = args.out.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error("--out must be outside the checkout")
    if out.exists() and any(out.iterdir()):
        parser.error("--out must be empty")
    out.mkdir(parents=True, exist_ok=True)
    original = {name: (ROOT / name).read_bytes() for name in SOURCES}
    summary = {"schema": "r13-ui-withdrawals/1", "base": BASE, "level": "Node UI/entry seams; no Chromium or IME-device execution",
               "sources": {name: {"bytes": len((ROOT/name).read_bytes()), "sha256": sha((ROOT/name).read_bytes())}
                           for name in (*SOURCES, UI_TEST, SPACE_TEST, "tests/oracles/r13_e1_contract.json")}, "results": []}
    with tempfile.TemporaryDirectory(prefix="r13-ui-withdrawals-") as directory:
        work = Path(directory)
        env = {**os.environ, "NO_COLOR": "1"}
        for name, variable in SOURCES.items():
            target = work / Path(name).name;target.write_bytes(original[name]);env[variable] = str(target)
        baseline, _ = run(["node", "--test", "--test-reporter=tap", UI_TEST, SPACE_TEST], env, out / "full-baseline")
        summary["baseline"] = baseline
        baseline_count = 19 + 14  # UI（含 T24 的 undo／redo）+ space entry
        if not green(baseline, baseline_count):
            raise RuntimeError(f"baseline must complete exactly {baseline_count}/{baseline_count}; no mutation credit")
        for name, source, before, after, test, case, assertion in FAULTS:
            if args.only and name != args.only:
                continue
            base_bytes = original[source]
            if base_bytes.count(before.encode()) != 1:
                raise RuntimeError(name + ": exact product anchor must occur once")
            destination = out/name;destination.mkdir()
            command = ["node", "--test", "--test-reporter=tap", "--test-name-pattern=^"+re.escape(case)+"$", test]
            control, _ = run(command, env, destination/"baseline")
            if not green(control, 1):
                raise RuntimeError(name + ": named baseline is not one completed green test")
            changed = base_bytes.replace(before.encode(), after.encode(), 1)
            target = work/Path(source).name
            try:
                target.write_bytes(changed)
                fault, output = run(command, env, destination/"fault")
                counts = fault["counts"]
                killed = fault["exit"] == 1 and counts.get("tests") == 1 and counts.get("fail") == 1 and counts.get("pass") == 0 and all(
                    counts.get(key) == 0 for key in ("cancelled", "skipped", "todo")) and "ERR_ASSERTION" in output and assertion in output
            finally:
                target.write_bytes(base_bytes)
            restored, _ = run(command, env, destination/"restored")
            if not killed or not green(restored, 1) or target.read_bytes() != base_bytes:
                raise RuntimeError(name + ": no named assertion kill or exact-byte green restoration")
            summary["results"].append({"name": name, "status": "killed", "source": source, "sourceSha256": sha(base_bytes),
                                       "faultSha256": sha(changed), "test": case, "assertion": assertion,
                                       "exits": [control["exit"], fault["exit"], restored["exit"]],
                                       "baseline": control, "fault": fault, "restored": restored})
            print(name + " 0/1/0", flush=True)
    summary["killed"] = len(summary["results"])
    (out/"summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
