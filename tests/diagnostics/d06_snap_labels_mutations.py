"""Run the bounded D06 shipped-function judge, keeping every 0/1/0 raw output.

These are local Node/VM withdrawals, not Chromium or the official mutation
ledger. The live source is always restored byte-for-byte in a finally block.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
APP = "geometry-web/app.js"
CURSOR = "geometry-web/cursor-v2.js"
MUTATIONS = [
    ("D06-W01-source-routing", APP,
     "CursorV2.snap(m.k,m.x,m.y,{source:m.source})", "CursorV2.snap(m.k,m.x,m.y)", "D06_PDF_ENDPOINT"),
    ("D06-W02-pdf-endpoint", CURSOR,
     '"pdf-endpoint":"PDF 端點"', '"pdf-endpoint":"格點"', "D06_PDF_ENDPOINT"),
    ("D06-W03-pdf-intersection", APP,
     '`pdf-${sample.target.kind}`', '"pdf-endpoint"', "D06_PDF_INTERSECTION"),
    ("D06-W04-draft-alignment", APP,
     'fe.draftPreview.guides.length ? "draft-alignment"',
     'fe.draftPreview.guides.length ? "grid"', "D06_DRAFT_ALIGNMENT"),
    ("D06-W05-free-point", APP,
     'sample.opts.snapOn ? "grid" : null', '"grid"', "D06_FREE"),
    ("D06-W06-stale-basis", APP,
     '(page === pv.pdfPage && fePdfSnapBasis(page) === pv.pdfBasis)',
     '(page === pv.pdfPage)', "D06_STALE_SOURCE"),
    ("D06-W07-edge-alignment", APP,
     'source:aligned ? "vertex-alignment" : "grid"',
     'source:"grid"', "D06_EDGE_ALIGNMENT"),
    ("D06-W08-pan", APP,
     'const drawing = !fe.spaceDown && fe.tool !== "pan" && d?.kind !== "pan";',
     'const drawing = true;', "D06_PAN"),
    ("D06-W09-changed-draft", APP,
     'pv.snapDraft === fe.draft.pts && pv.snapOn', 'pv.snapOn', "D06_CHANGED_DRAFT"),
    ("D06-W10-pinch-fixed-grid", APP,
     '"guideNew", "holeRect", "vertex", "edge", "guide"',
     '"guideNew", "holeRect", "vertex", "edge", "guide", "pinch"', "D06_PINCH_GRID_SOURCE"),
    ("D06-W11-shape-handle-fixed-grid", APP,
     '"guideNew", "holeRect", "vertex", "edge", "guide"',
     '"guideNew", "holeRect", "vertex", "edge", "guide", "opHandle"', "D06_SHAPE_HANDLE_GRID_SOURCE"),
    ("D06-W12-unknown-gesture", APP,
     'drawing && fixedGridGesture && (snapOn',
     'drawing && (snapOn', "D06_UNKNOWN_DRAG_SOURCE"),
    ("D06-W13-uncapped-screen-stroke", APP,
     'Math.min(14, Math.max(10, 14 / z))', 'Math.max(10, 14 / z)', "D06_HANDLE_SCREEN_HIT"),
    ("D06-W14-fixed-fourteen-at-high-zoom", APP,
     'Math.min(14, Math.max(10, 14 / z))', '14', "D06_HANDLE_HIGH_ZOOM"),
]

def named_failure(output, judge):
    for title,body in re.findall(r'^not ok \d+ - ([^\n]+)\n(  ---\n.*?^  \.\.\.)',output,re.M|re.S):
        if title.startswith(judge+':') and "  code: 'ERR_ASSERTION'" in body and "  name: 'AssertionError'" in body:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    command = ["node", "--test", "--test-reporter=tap", "tests/test_d06_snap_labels.js"]
    report = {"schema": "geometry-d06-local-withdrawals/1", "browserExecuted": False,
              "command": command, "sourceHead": subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "mutations": []}

    def run(name):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=60)
        (args.out / (name + ".stdout.log")).write_bytes(result.stdout)
        (args.out / (name + ".stderr.log")).write_bytes(result.stderr)
        return result.returncode, (result.stdout + result.stderr).decode("utf-8", errors="replace")

    for name, relative, old, new, judge in MUTATIONS:
        file = ROOT / relative
        original = file.read_bytes()
        old, new = old.encode(), new.encode()
        if original.count(old) != 1:
            raise SystemExit(name + ": expected exactly one source anchor")
        baseline, _ = run(name + ".baseline")
        if baseline != 0:
            raise SystemExit(name + ": baseline is not green")
        try:
            mutated = original.replace(old, new)
            file.write_bytes(mutated)
            mutant, output = run(name + ".mutant")
        finally:
            file.write_bytes(original)
        restored, _ = run(name + ".restored")
        raw_restored = file.read_bytes() == original
        assertion_killed = mutant == 1 and named_failure(output, judge)
        row = {"id": name, "judge": judge, "file": relative,
               "baselineMutantRestoredExit": [baseline, mutant, restored],
               "sourceRestoredExactly": raw_restored,
               "beforeSha256": hashlib.sha256(original).hexdigest(),
               "mutantSha256": hashlib.sha256(mutated).hexdigest(),
               "status": "killed" if assertion_killed and restored == 0 and raw_restored else "failed"}
        report["mutations"].append(row)
        print(json.dumps(row, ensure_ascii=False))
        if row["status"] != "killed":
            break
    report["status"] = "passed" if len(report["mutations"]) == len(MUTATIONS) and all(
        row["status"] == "killed" for row in report["mutations"]) else "failed"
    (args.out / "receipt.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if report["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
