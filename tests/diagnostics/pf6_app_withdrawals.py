#!/usr/bin/env python3
"""PF-6 renderer / strict-module withdrawals in disposable source copies.

Node and true Chromium are separate modes and receipts. Browser mode delegates
process ownership, runtime probes, scope and footer validation to the unchanged
browser_mutation_check.py. A missing named AssertionError, timeout, transport,
syntax or cleanup failure cannot be called killed. No official ledger is edited.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE = "b3c4b981bb96b118c1c05b7a1bd98062d710c8b2"
UI = "geometry-web/panel-fill-builder-workspace.js"
TEST = "tests/test_panel_fill_builder_ui.js"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def definitions(root, mode):
    items = []

    def add(identifier, file, before, after, assertion):
        raw = (root / file).read_bytes()
        if b"\r" in raw or raw.count(before.encode()) != 1:
            raise ValueError(identifier + ": exact LF anchor is absent or ambiguous")
        changed = raw.replace(before.encode(), after.encode(), 1)
        items.append({"id": identifier, "case": "P1286", "assertions": [assertion],
                      "changes": [{"file": file, "before": before, "after": after}],
                      "beforeBytes": len(raw), "beforeSha256": sha(raw),
                      "afterBytes": len(changed), "afterSha256": sha(changed)})

    add("PF6_APP_AUTO_SELECT_ALL", UI,
        "list(s.selected).includes(e.key)?' checked':''",
        "e.selectable&&e.valid?' checked':''",
        "PF6_DOM_EXPLICIT_SET" if mode == "browser" else "PF6_APP_EXPLICIT_SET")
    add("PF6_APP_USE_SUGGEST_GEOMETRY", UI,
        "const p=s.candidate;if(!p)return '';",
        "const p=s.candidate?{...s.candidate,entries:s.suggestions.entries.map(e=>({...e,selected:s.selected.includes(e.key)}))}:null;if(!p)return '';",
        "PF6_DOM_READABLE_VALUES" if mode == "browser" else "PF6_APP_SELECTED_REBUILD")
    if mode == "browser":
        add("PF6_APP_DROP_ENTRY", "geometry-web/panel-fill-workspace.js",
            "if(action==='suggest-timbers'){", "if(action==='pf6-disabled-entry'){",
            "PF6_DOM_ENTRY")
    else:
        add("PF6_APP_RENDERER_ACCEPTS_ZERO_TOKEN", UI,
            "const positiveToken=value=>Number.isInteger(value)&&value>0&&value<=4294967295;",
            "const positiveToken=value=>Number.isInteger(value)&&value>=0&&value<=4294967295;",
            "PF6_APP_ZERO_TOKEN_REJECTED")
        add("PF6_APP_RENDERER_TOKEN_MEANS_VALID", UI,
            "!s.confirmable||p?.valid!==true||p.phase!=='SELECTED'",
            "!s.confirmable||!p||p.phase!=='SELECTED'", "PF6_APP_INVALID_TOKEN_NOT_AUTHORITY")
        add("PF6_APP_RENDERER_UNESCAPED_SOURCE", UI,
            "esc(dimensionText(view?.input.A))", "dimensionText(view?.input.A)",
            "PF6_APP_SOURCE_NAME_NOT_HTML")
        add("PF6_APP_INVALID_PREFIX_SELECTABLE", UI,
            "const enabled=r.valid===true&&r.appView?.completeForScope===true&&",
            "const enabled=", "PF6_APP_INVALID_PREFIX_LOCKED")
        add("PF6_APP_OMISSIONS_MISLABELLED_AS_SEAMS", UI,
            "['boundary','edge-primary','free-edge','covered-edge','hole-edge'].includes(e.phase)",
            "['boundary','edge-primary'].includes(e.phase)", "PF6_APP_OMITTED_EDGE_NOT_SEAM")
        add("PF6_APP_TEMPORARY_ID_AS_FORMAL", UI,
            "候選暫號 #${esc(id)}（尚未正式建立）", "正式 #${esc(id)}",
            "PF6_APP_TEMPORARY_LABEL_REQUIRED")
        add("PF6_APP_PREVIEW_ACCEPTS_FORMAL_ID", UI,
            "||!temporaryCandidate(p)", "", "PF6_APP_TEMPORARY_SHAPE_REQUIRED")
        add("PF6_APP_RECEIPT_USES_CANDIDATE_ID", UI,
            '${rows.map(row=>`<tr data-pf6-formal=',
            '${rows.map(row=>({...row,id:expected.find(before=>before.tempKey===row.tempKey).candidateId})).map(row=>`<tr data-pf6-formal=',
            "PF6_APP_RECEIPT_ID_EXACT")
        add("PF6_APP_RECEIPT_MISSING_MAPPING", UI,
            "rows.length===expected.length", "rows.length<=expected.length",
            "PF6_APP_MALFORMED_RECEIPT_NO_FORMAL_IDS")
        add("PF6_APP_SUPPORT_COPIES_LEFT_TO_RIGHT", UI,
            "右 ${esc(p.right)} mm", "右 ${esc(p.left)} mm", "PF6_APP_BOTH_SUPPORT_WIDTHS")
        add("PF6_UI14_ACTIONS_AS_UNORDERED_SET", "geometry-web/panel-fill-adapter.js",
            "value.every((action,index)=>action===ACTIONS[index])",
            "value.every(action=>ACTIONS.includes(action))", "PF6_UI14_EXACT_ORDER_REQUIRED")
        add("PF6_UI14_DROP_SIXTH_CAPABILITY", "geometry-web/panel-fill-adapter.js",
            "'create-from-fill-grid','suggest-timbers'", "'create-from-fill-grid'",
            "PF6_UI14_SUPPORTED_ACTIONS_EXECUTABLE")
        add("PF6_UI14_LEGACY_EXPOSES_BUILDER", "geometry-web/panel-fill-workspace.js",
            "const builderSupported=s=>s.contract?.supportedActions.includes('suggest-timbers')===true;",
            "const builderSupported=s=>true;", "PF6_UI14_LEGACY_NO_BUILDER")
        add("PF6_UI14_DROP_FORMAL_DISPATCH", "geometry-web/panel-fill-workspace.js",
            "if(action==='suggest-timbers'){", "if(action==='pf6-disabled-entry'){",
            "PF6_UI14_FORMAL_ACTION_REACHES_BUILDER")
    return items


def syntax_check(root, rows, node):
    results = []
    with tempfile.TemporaryDirectory(prefix="pf6-ui-syntax-") as directory:
        for row in rows:
            change = row["changes"][0]
            raw = (root / change["file"]).read_bytes().replace(change["before"].encode(), change["after"].encode(), 1)
            target = Path(directory) / (row["id"] + ".js")
            target.write_bytes(raw)
            result = subprocess.run([node, "--check", str(target)], capture_output=True, timeout=30)
            if result.returncode:
                raise ValueError(row["id"] + ": withdrawn source does not parse")
            results.append({"id": row["id"], "syntaxExit": result.returncode, "sha256": sha(raw)})
    return results


def original_browser(root):
    filename = root / "geometry-web/browser_mutation_check.py"
    spec = importlib.util.spec_from_file_location("pf6_original_browser_mutation", filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_node(work, node, output, label):
    command = [node, "--test", TEST]
    result = subprocess.run(command, cwd=work, capture_output=True, timeout=60)
    stdout, stderr = output / (label + ".stdout"), output / (label + ".stderr")
    stdout.write_bytes(result.stdout)
    stderr.write_bytes(result.stderr)
    return {"command": command, "exitCode": result.returncode,
            "stdout": str(stdout), "stdoutSha256": sha(result.stdout),
            "stderr": str(stderr), "stderrSha256": sha(result.stderr)}


def node_execution(root, rows, options, output):
    files = [TEST, UI, "geometry-web/panel-fill-adapter.js", "geometry-web/panel-fill-builder-session.js",
             "geometry-web/panel-fill-workspace.js"]
    report = {"schema": "pf6-app-renderer-withdrawals/1", "base": BASE,
              "browserExecuted": False, "officialLedger": False, "mutations": [],
              "sources": {name: {"bytes": len((root / name).read_bytes()), "sha256": sha((root / name).read_bytes())} for name in files}}
    with tempfile.TemporaryDirectory(prefix="pf6-ui-withdraw-") as directory:
        work = Path(directory)
        for name in files:
            target = work / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((root / name).read_bytes())
        report["baseline"] = run_node(work, options.node, output, "baseline")
        if report["baseline"]["exitCode"] != 0:
            raise RuntimeError("PF6 Node baseline is not green; no withdrawal counts as killed")
        for row in rows:
            change = row["changes"][0]
            target = work / change["file"]
            raw = target.read_bytes()
            try:
                target.write_bytes(raw.replace(change["before"].encode(), change["after"].encode(), 1))
                mutant = run_node(work, options.node, output, row["id"] + "-withdrawn")
            finally:
                target.write_bytes(raw)
            restored = run_node(work, options.node, output, row["id"] + "-restored")
            log = Path(mutant["stdout"]).read_text() + Path(mutant["stderr"]).read_text()
            exits = [report["baseline"]["exitCode"], mutant["exitCode"], restored["exitCode"]]
            killed = exits == [0, 1, 0] and "AssertionError" in log and all(marker in log for marker in row["assertions"])
            report["mutations"].append({**row, "baselineMutantRestoredExit": exits, "sourceRestoredExactly": target.read_bytes() == raw,
                                        "mutant": mutant, "restored": restored, "status": "killed" if killed else "blocked"})
    report["status"] = "passed" if all(row["status"] == "killed" for row in report["mutations"]) else "blocked"
    return report


def browser_execution(root, rows, options, output):
    if not options.bridge or not options.bridge.is_file() or not options.model_base or not options.model_base.is_file():
        raise ValueError("Browser mode requires existing --bridge and --model-base from this source")
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, capture_output=True, check=True)
    if dirty.stdout:
        raise ValueError("Browser evidence requires a committed clean source; local T/P drafts are not an official head")
    original = original_browser(root)
    original.require_process_namespace()
    manifest = {"schema": "geometry-browser-mutations/1", "suite": "pf6-app-first-slice",
                "scope": "GEOMETRY_CANVAS_MODULE_ONLY", "caseFilter": "GEOMETRY_CANVAS_MODULE",
                "resultPrefix": "P1286_SUITE_RESULT ", "cases": ["P1286"], "mutations": rows,
                "inputs": [UI, "geometry-web/panel-fill-builder-session.js", "geometry-web/panel-fill-workspace.js",
                           "geometry-web/canvas_sections/P1286.js", "geometry-web/cdp_sections.d/P1286.json",
                           "geometry-web/cdp_test.js", "geometry-web/browser_mutation_check.py",
                           "tests/diagnostics/pf6_app_withdrawals.py"]}
    save(output / "manifest.json", manifest)
    report = {"schema": "pf6-app-browser-withdrawals/1", "base": BASE, "browserExecuted": False,
              "officialLedger": False, "mutations": [], "status": "blocked", "timeoutSeconds": options.timeout}
    with tempfile.TemporaryDirectory(prefix="pf6-browser-withdraw-") as directory:
        temporary = Path(directory)
        baseline = temporary / "baseline"
        baseline.mkdir()
        report["files"] = original.snapshot(root, baseline, manifest["inputs"])
        # Always pass the module ID, including baseline. The generic module
        # scope is intentionally invalid without GEOMETRY_CANVAS_MODULE.
        report["baseline"] = original.run_cdp(baseline, manifest, options, output, "baseline", "P1286")
        report["browserExecuted"] = report["baseline"]["complete"]
        if not report["baseline"]["green"]:
            report["reason"] = "Baseline is not green; no withdrawal counts as killed"
            return report
        for row in rows:
            work = temporary / row["id"]
            shutil.copytree(baseline, work)
            change = row["changes"][0]
            target = original.safe_path(work, change["file"])
            raw = target.read_bytes()
            try:
                if raw.count(change["before"].encode()) != 1:
                    raise ValueError(row["id"] + ": source anchor drifted")
                target.write_bytes(raw.replace(change["before"].encode(), change["after"].encode(), 1))
                mutant = original.run_cdp(work, manifest, options, output, row["id"] + "-withdrawn", "P1286")
            finally:
                target.write_bytes(raw)
            restored = original.run_cdp(work, manifest, options, output, row["id"] + "-restored", "P1286")
            exits = [report["baseline"].get("exitCode"), mutant.get("exitCode"), restored.get("exitCode")]
            killed = (exits == [0, 1, 0] and restored["green"] and mutant["complete"] and not mutant["errors"]
                      and mutant["footer"][0].get("failedAssertions", 0) > 0
                      and set(mutant["assertions"]).intersection(row["assertions"]))
            report["mutations"].append({**row, "baselineMutantRestoredExit": exits, "sourceRestoredExactly": target.read_bytes() == raw,
                                        "mutant": mutant, "restored": restored, "status": "killed" if killed else "blocked"})
            shutil.rmtree(work)
    report["status"] = "passed" if all(row["status"] == "killed" for row in report["mutations"]) else "blocked"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["node", "browser"], default="node")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--node", default="node")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--bridge", type=Path)
    parser.add_argument("--model-base", type=Path)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    if not 0 < args.timeout <= 900:
        parser.error("Keep the existing browser mutation limit at or below 900 seconds")
    root = args.root.resolve()
    rows = definitions(root, args.kind)
    syntax = syntax_check(root, rows, args.node)
    if args.preflight:
        print(json.dumps({"base": BASE, "kind": args.kind, "browserExecuted": False, "syntax": syntax, "mutations": rows}, ensure_ascii=False, indent=2))
        return 0
    if not args.output or args.output.exists() or args.output.resolve().is_relative_to(root):
        parser.error("--output must be a new directory outside the repository")
    output = args.output.resolve()
    output.mkdir(parents=True)
    report = {"status": "blocked", "browserExecuted": False, "officialLedger": False}
    try:
        report = (node_execution if args.kind == "node" else browser_execution)(root, rows, args, output)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        report["status"] = "blocked"
        report["reason"] = type(error).__name__ + ": " + str(error)
    finally:
        save(output / "receipt.json", report)
    print(json.dumps({"status": report["status"], "receipt": str(output / "receipt.json")}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
