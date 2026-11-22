#!/usr/bin/env python3
"""U123-H:A named browser withdrawals, using the existing isolated CDP runner.

This is an external execution tool, not a claim that Chromium ran here. It
starts a fresh server and profile for every baseline/mutant/restored phase;
only the existing browser_mutation_check.py owns processes and native probes.
The live checkout is never edited. Neither goldens nor evidence registries are
rewritten. A timeout, syntax error, incomplete CDP result or cleanup failure
cannot count as killed. --preflight performs no browser execution.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


BASE_SHA = "883e68688f6480a5f1de6e86e6a056cc20339cb9"
CASE = "P1231"
MAX_TIMEOUT = 900  # Existing browser_mutation_check.py budget, never extended.


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode("utf-8").strip()


def original_runner(root: Path):
    filename = root / "geometry-web/browser_mutation_check.py"
    spec = importlib.util.spec_from_file_location("r16_original_browser_mutations", filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def block(source: str, name: str) -> str:
    matches = re.findall(r"/\* " + re.escape(name) + r"_BEGIN\b.*?/\* " +
                         re.escape(name) + r"_END \*/", source, flags=re.DOTALL)
    if len(matches) != 1:
        raise ValueError(f"Expected one {name} marker pair, got {len(matches)}")
    return matches[0]


def definitions(root: Path):
    css = "geometry-web/workspace-height.css"
    dialogs = "geometry-web/workspace-height-dialogs.css"
    js = "geometry-web/workspace-height.js"
    texts = {name: (root / name).read_text(encoding="utf-8") for name in (css, dialogs, js)}
    result = []

    def add(name, target, before, after, assertion, meaning):
        if not before or texts[target].count(before) != 1 or before == after:
            raise ValueError(f"{name}: exact product anchor is absent or ambiguous")
        source = (root / target).read_bytes()
        if b"\r" in source:
            raise ValueError(f"{name}: use the LF source checkout used by Linux CI")
        changed = source.replace(before.encode("utf-8"), after.encode("utf-8"), 1)
        result.append({"id": name, "case": CASE, "assertions": [assertion],
                       "meaning": meaning, "changes": [{"file": target, "before": before, "after": after}],
                       "beforeBytes": len(source), "beforeSha256": sha(source),
                       "afterBytes": len(changed), "afterSha256": sha(changed)})

    add("R123H_RESTORE_GRID_340PX", dialogs,
        "  flex: 1 0 calc(var(--r123h-layout-height, 100vh) - var(--r123h-dialog-header));",
        "  flex: 0 0 340px;", "R123H_HEIGHT",
        "Restore the pre-slice mobile grid drawing height; retain the real flex-item resize stimulus.")
    model = block(texts[dialogs], "R123H_MODEL_HEIGHT")
    add("R123H_WITHDRAW_MODEL_HEIGHT", dialogs, model,
        "/* R123H_WITHDRAW_MODEL_HEIGHT: original model layout declarations apply. */",
        "R123H_HEIGHT", "Withdraw only the new full-height 3D stage declarations.")
    breakpoint = block(texts[css], "R123H_BREAKPOINT")
    if breakpoint.count("max-width: 560px") != 1:
        raise ValueError("R123H breakpoint no longer has exactly one adopted 560px boundary")
    add("R123H_MOBILE_AT_768", css, breakpoint, breakpoint.replace("max-width: 560px", "max-width: 768px"),
        "R123H_HEIGHT", "Incorrectly apply the 96px mobile header budget at the requested 768px desktop width.")
    add("R123H_DOCK_BACK_OVER_CANVAS", css,
        "#faceCanvasDock { left: 100%; }", "#faceCanvasDock { left: 0; }",
        "R123H_UNOBSCURED", "Withdraw the physical separation of face controls from the drawable rectangle.")
    add("R123H_VISUAL_VIEWPORT_DENOMINATOR", js,
        "document.documentElement.style.setProperty('--r123h-layout-height', window.innerHeight+'px');",
        "document.documentElement.style.setProperty('--r123h-layout-height', window.visualViewport.height+'px');",
        "R123H_DENOMINATOR", "Use visualViewport for V; the real page-scale/resize probe must expose the mismatch.")
    add("R123H_WITHDRAW_DOCK_WHEEL_OWNER", js,
        "['pointerdown', 'pointermove', 'pointerup', 'wheel', 'contextmenu']",
        "['pointerdown', 'pointermove', 'pointerup', 'contextmenu']",
        "R123H_DOCK_SCROLL", "Let dock wheel events bubble into face-canvas zoom; the camera must change and fail.")
    length = block(texts[css], "R123H_LENGTH_PAINT")
    add("R123H_WITHDRAW_LENGTH_PAINT", css, length,
        "/* R123H_WITHDRAW_LENGTH_PAINT: original readonly-buffer stacking applies. */",
        "R123H_LENGTH_DISPLAY", "Restore the old readonly segment-buffer stacking below the decorative cursor layer.")
    clearance = block(texts[css], "R123H_SIDEBAR_CLEARANCE")
    add("R123H_RESTORE_SIDEBAR_DOCK_OCCLUSION", css, clearance,
        clearance.replace("margin-inline-end: var(--r123h-dock)", "padding-inline-end: var(--r123h-dock)"),
        "R123H_ENTRY_CONTROL_REACH", "Restore the sidebar's painted padding over the dock; the initial 1400px five-point audit must fail before any fit click.")
    scroll = block(texts[css], "R123H_THREE_VIEW_SCROLL_CLEARANCE")
    add("R123H_WITHDRAW_THREE_VIEW_SCROLL_CLEARANCE", css, scroll,
        "/* R123H_WITHDRAW_THREE_VIEW_SCROLL_CLEARANCE: old 44px clipped row applies. */",
        "R123H_CONTROLS", "Restore the old three-view toolbar row that also has to contain its horizontal scrollbar.")
    gutter = block(texts[css], "R123H_FACE_TOOL_END_GUTTER")
    add("R123H_WITHDRAW_FACE_TOOL_END_GUTTER", css, gutter,
        "/* R123H_WITHDRAW_FACE_TOOL_END_GUTTER: old end-of-scroll extent applies. */",
        "R123H_CONTROLS", "Remove the physical trailing scroll extent; retain all five hit points and the original narrow face-tool controls.")
    return result


def manifest_for(root: Path, mutations):
    fragmented = (root / "geometry-web/canvas_registry.js").is_file()
    return {
        "schema": "geometry-browser-mutations/1", "suite": "r16-u123-height",
        "scope": "GEOMETRY_CANVAS_MODULE_ONLY" if fragmented else "GEOMETRY_WORKSPACE_HEIGHT_ONLY",
        # The original runner can pass the generic module selector as its
        # caseFilter. The P1231 test always runs its whole independent matrix.
        "caseFilter": "GEOMETRY_CANVAS_MODULE" if fragmented else "GEOMETRY_WORKSPACE_HEIGHT_CASE",
        "resultPrefix": "P1231_SUITE_RESULT ", "cases": [CASE],
        "inputs": [
            "geometry-web/cdp_test.js",
            "geometry-web/browser_mutation_check.py", "geometry-web/workspace-height.js",
            "geometry-web/workspace-height.css", "geometry-web/workspace-height-dialogs.css",
            "tests/diagnostics/r16_height_mutations.py", "tests/diagnostics/r16_control_probe.cjs"
        ] + (["geometry-web/canvas_sections/P1231.js", "geometry-web/cdp_sections.d/P1231.json"]
             if fragmented else ["geometry-web/workspace_height_test.js"]),
        "mutations": mutations,
        "registryFormat": "fragmented" if fragmented else "single-file"
    }


def syntax_preflight(root, mutations, node):
    receipts = []
    with tempfile.TemporaryDirectory(prefix="geometry-r16-height-syntax-") as directory:
        temporary = Path(directory)
        for item in mutations:
            for change in item["changes"]:
                if not change["file"].endswith(".js"):
                    continue
                raw = (root / change["file"]).read_bytes()
                raw = raw.replace(change["before"].encode(), change["after"].encode(), 1)
                target = temporary / (item["id"] + ".js")
                target.write_bytes(raw)
                command = subprocess.run([node, "--check", str(target)], text=True,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                if command.returncode != 0:
                    raise ValueError(item["id"] + ": syntax failure: " + command.stderr)
                receipts.append({"id": item["id"], "exitCode": command.returncode, "sha256": sha(raw)})
    return receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--bridge", type=Path)
    parser.add_argument("--model-base", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--node", default="node")
    parser.add_argument("--timeout", type=int, default=MAX_TIMEOUT)
    parser.add_argument("--preflight", action="store_true")
    options = parser.parse_args()
    root = options.repo.resolve()
    if not 0 < options.timeout <= MAX_TIMEOUT:
        parser.error("--timeout must remain within the existing 900-second browser-mutation budget")
    mutations = definitions(root)
    manifest = manifest_for(root, mutations)
    syntax = syntax_preflight(root, mutations, options.node)
    preflight = {"schema": "r16-height-withdrawal-preflight/1", "base": BASE_SHA,
                 "sourceHead": git(root, "rev-parse", "HEAD"), "browserExecuted": False,
                 "registryFormat": manifest["registryFormat"], "scope": manifest["scope"],
                 "caseFilter": manifest["caseFilter"], "case": CASE,
                 "syntax": syntax,
                 "withdrawals": [{key: value for key, value in row.items() if key != "changes"}
                                 for row in mutations]}
    if options.preflight:
        print(encode(preflight), end="")
        return 0
    if not options.bridge or not options.bridge.is_file() or not options.model_base or not options.model_base.is_file():
        parser.error("Pass the existing CI-built --bridge and --model-base executables")
    if not options.output_dir:
        parser.error("Pass a new --output-dir outside the repository")
    output = options.output_dir.resolve()
    if output.exists() or output.is_relative_to(root):
        parser.error("--output-dir must be new and outside the repository")
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        parser.error("Commit the complete T+P source before browser evidence; dirty/untracked sources are not a fixed head")
    original = original_runner(root)
    original.require_process_namespace()
    output.mkdir(parents=True)
    (output / "preflight.json").write_text(encode(preflight), encoding="utf-8")
    (output / "manifest.json").write_text(encode(manifest), encoding="utf-8")
    report = {"schema": "r16-height-browser-withdrawals/1", "base": BASE_SHA,
              "sourceHead": preflight["sourceHead"], "registryFormat": manifest["registryFormat"],
              "status": "blocked", "browserExecuted": False, "browserExecutionAttempted": True, "mutations": [],
              "timeoutSeconds": options.timeout,
              "bridge": {"bytes": options.bridge.stat().st_size, "sha256": sha(options.bridge.read_bytes())},
              "modelBase": {"bytes": options.model_base.stat().st_size, "sha256": sha(options.model_base.read_bytes())}}
    code = 2
    try:
        with tempfile.TemporaryDirectory(prefix="geometry-r16-height-browser-") as directory:
            temporary = Path(directory)
            baseline = temporary / "baseline"
            baseline.mkdir()
            report["files"] = original.snapshot(root, baseline, manifest["inputs"])
            report["sourceHash"] = sha(json.dumps(report["files"], sort_keys=True).encode())
            # Always pass P1231, including baseline. That is also the ordinary
            # generic-module selector after #434, rather than silently running
            # the old full suite when the former one-off flag no longer exists.
            report["baseline"] = original.run_cdp(baseline, manifest, options, output, "baseline", CASE)
            report["browserExecuted"] = report["baseline"]["complete"]
            if not report["baseline"]["green"]:
                raise RuntimeError("Baseline is not green; no withdrawal counts as killed")
            for mutation in mutations:
                row = {"id": mutation["id"], "assertions": mutation["assertions"], "status": "blocked"}
                report["mutations"].append(row)
                work = temporary / mutation["id"]
                shutil.copytree(baseline, work)
                originals = {}
                try:
                    for change in mutation["changes"]:
                        target = original.safe_path(work, change["file"])
                        data = target.read_bytes()
                        originals[target] = data
                        before, after = change["before"].encode(), change["after"].encode()
                        if data.count(before) != 1:
                            raise ValueError("Exact source anchor drifted: " + change["file"])
                        target.write_bytes(data.replace(before, after, 1))
                    row["mutant"] = original.run_cdp(work, manifest, options, output, mutation["id"] + "-mutant", CASE)
                finally:
                    for target, data in originals.items():
                        target.write_bytes(data)
                    row["sourceRestoredExactly"] = all(target.read_bytes() == data for target, data in originals.items())
                row["restored"] = original.run_cdp(work, manifest, options, output, mutation["id"] + "-restored", CASE)
                mutant = row["mutant"]
                row["baselineMutantRestoredExit"] = [report["baseline"].get("exitCode"), mutant.get("exitCode"), row["restored"].get("exitCode")]
                if not row["sourceRestoredExactly"] or not row["restored"]["green"]:
                    row["reason"] = "Restored control is not green or the source bytes did not restore exactly"
                elif mutant["green"]:
                    row["status"] = "survived"
                elif (mutant["complete"] and not mutant["errors"] and mutant.get("exitCode") == 1
                      and mutant["footer"][0].get("failedAssertions", 0) > 0
                      and set(mutant["assertions"]).intersection(mutation["assertions"])
                      and row["baselineMutantRestoredExit"] == [0, 1, 0]):
                    row["status"] = "killed"
                else:
                    row["reason"] = "No completed named assertion failure; startup, fixture, timeout and cleanup errors do not kill"
                shutil.rmtree(work)
            statuses = [row["status"] for row in report["mutations"]]
            report["status"] = "passed" if all(status == "killed" for status in statuses) else "blocked" if "blocked" in statuses else "failed"
            code = 0 if report["status"] == "passed" else 2 if report["status"] == "blocked" else 1
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        report["reason"] = type(error).__name__ + ": " + str(error)
    finally:
        if git(root, "rev-parse", "HEAD") != report["sourceHead"] or git(root, "status", "--porcelain", "--untracked-files=all"):
            report["status"] = "blocked"
            report["reason"] = "The live source head changed while its independent snapshots were running"
            code = 2
        (output / "receipt.json").write_text(encode(report), encoding="utf-8")
        print(encode({"status": report["status"], "receipt": str(output / "receipt.json")}), end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
