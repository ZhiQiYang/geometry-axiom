"""Exercise the real GEO314 source-contract judge in an isolated source copy.

This is an inventory/host-wiring proof, not a native-behavior mutation receipt.
Only the selected AssertionError counts as detection. Errors, skips, crashes,
timeouts and unrelated failures do not. No mutation ledger is read or written.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
JUDGE = "tests/test_geo314_commit_paths.py"
BRIDGE = "geometry-web/timber_edit_bridge.inc"
PUBLICATION = "test_publication_routes_have_reviewed_submission_or_replacement_classification"
REVALIDATION = "test_revalidation_and_staged_routes_are_an_exact_reviewed_inventory"
BASELINE = "test_submission_baselines_and_replay_restoration_are_exact"
TESTS = (PUBLICATION, REVALIDATION, BASELINE)
PUBLISH_ROW = '    ("geometry-web/timber_edit_bridge.inc", "cmd_timber_edit_confirm", 1, "submission"),\n'
REVALIDATE_ROW = '    ("geometry-web/timber_edit_bridge.inc", "timber_edit_evaluate", 1),\n'
BASELINE_ROW = '    ("geometry-web/timber_edit_bridge.inc", "timber_edit_evaluate", "call->before"),\n'

# All anchors are exact literals independently chosen for one reviewed fault.
# Tuples: name, file, before, after, test method, required assertion message.
MUTATIONS = (
    ("G314_R356_PUBLICATION_UNREGISTERED", JUDGE, PUBLISH_ROW, "", PUBLICATION,
     "I24 publication route added/removed"),
    ("G314_R356_PUBLICATION_WRONG_CLASS", JUDGE, PUBLISH_ROW,
     PUBLISH_ROW.replace('"submission"', '"isolated replay"'), PUBLICATION,
     "R356_G314_TIMBER_IS_SUBMISSION"),
    ("G314_R356_PUBLICATION_DUPLICATE", JUDGE, PUBLISH_ROW, PUBLISH_ROW * 2,
     PUBLICATION, "I24 publication inventory: duplicate route declaration"),
    ("G314_R356_REVALIDATION_UNREGISTERED", JUDGE, REVALIDATE_ROW, "", REVALIDATION,
     "I24 world validation route changed"),
    ("G314_R356_REVALIDATION_DUPLICATE", JUDGE, REVALIDATE_ROW, REVALIDATE_ROW * 2,
     REVALIDATION, "I24 revalidation inventory: duplicate route declaration"),
    ("G314_R356_BASELINE_UNREGISTERED", JUDGE, BASELINE_ROW, "", BASELINE,
     "I24 baseline setup/restore changed"),
    ("G314_R356_BASELINE_FALSE_REPLAY", BRIDGE, "g_subgrid_before=call->before;",
     "g_subgrid_before=NULL;", BASELINE, "I24 baseline setup/restore changed"),
    ("G314_R356_PREVIEW_FALSE_REPLAY", BRIDGE, "call.before=&transaction->before;",
     "call.before=NULL;", BASELINE, "R356_G314_PREVIEW_RETAINS_PRE_SUBMISSION_WORLD"),
    ("G314_R356_BASELINE_RESTORED_TOO_EARLY", BRIDGE,
     ("g_subgrid_before=call->before;g_reference_capturing=true;",
      "g_subgrid_before=previous;g_reference_capturing=capturing;"),
     ("g_subgrid_before=call->before;g_reference_capturing=true;g_subgrid_before=previous;",
      "g_reference_capturing=capturing;"),
     BASELINE, "R356_G314_BASELINE_RESTORED_AFTER_BOTH_PATHS"),
    ("G314_R356_BASELINE_REPLAY_FLAG", BRIDGE,
     "g_subgrid_before=call->before;g_reference_capturing=true;",
     "g_subgrid_before=call->before;g_reference_capturing=true;g_parsing_scene_file=true;",
     BASELINE, "R356_G314_TIMBER_CANNOT_BORROW_REPLAY_BYPASS"),
    ("G314_R356_REVALIDATION_REMOVED", BRIDGE, "if(ok)ok=world_revalidate(candidate);",
     "if(ok)ok=true;", REVALIDATION, "I24 world validation route changed"),
    ("G314_R356_REVALIDATION_DUPLICATED", BRIDGE, "if(ok)ok=world_revalidate(candidate);",
     "if(ok)ok=world_revalidate(candidate)&&world_revalidate(candidate);",
     REVALIDATION, "I24 world validation route changed"),
    ("G314_R356_CONFIRM_REVALIDATION_REMOVED", BRIDGE,
     "if(!app_world_candidate_revalidate(g_preview.transaction,&g_world)){", "if(false){",
     PUBLICATION, "R356_G314_CONFIRM_REVALIDATES_RETAINED_CANDIDATE"),
    ("G314_R356_INVALID_CONFIRM_FALLTHROUGH", BRIDGE,
     'g_preview.ready=false;app_world_candidate_discard(g_preview.transaction);eng_bridge_error("INVALID",g_revalidate_error);return;',
     'g_preview.ready=false;app_world_candidate_discard(g_preview.transaction);eng_bridge_error("INVALID",g_revalidate_error);',
     PUBLICATION, "R356_G314_INVALID_CANDIDATE_CANNOT_PUBLISH"),
    ("G314_R356_PUBLICATION_FALSE_REPLAY", BRIDGE,
     "if(!app_world_candidate_publish(g_preview.transaction,&g_world,true)){",
     "if(!app_world_candidate_publish(g_preview.transaction,&g_world,false)){",
     PUBLICATION, "R356_G314_CONFIRM_PUBLISHES_SUBMISSION"),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_judge(root):
    spec = importlib.util.spec_from_file_location("r356_geo314_judge", root / JUDGE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def worker(root, names):
    module = load_judge(root)
    suite = unittest.TestSuite(module.Geo314CommitPaths(name) for name in names)
    result = unittest.TestResult()
    suite.run(result)
    value = {
        "testsRun": result.testsRun,
        "failures": [{"test": case._testMethodName, "trace": trace} for case, trace in result.failures],
        "errors": [{"test": str(case), "trace": trace} for case, trace in result.errors],
        "skipped": [{"test": str(case), "reason": reason} for case, reason in result.skipped],
    }
    print(json.dumps(value, ensure_ascii=False))
    return 0 if result.wasSuccessful() and not result.skipped else 1


def run_judge(source, names, destination):
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker-root", str(source)]
    for name in names:
        command.extend(["--test", name])
    record = {"command": command, "cwd": str(ROOT)}
    try:
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=30)
        record.update(returncode=run.returncode, stdout=run.stdout, stderr=run.stderr)
        try:
            record["result"] = json.loads(run.stdout)
        except ValueError:
            record["error"] = "judge did not return a structured unittest result"
    except (OSError, subprocess.TimeoutExpired) as error:
        record.update(returncode=None, error=str(error))
    destination.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def green(record, count):
    result = record.get("result", {})
    return (record.get("returncode") == 0 and result.get("testsRun") == count
            and not result.get("failures") and not result.get("errors") and not result.get("skipped"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--only", action="append", choices=[row[0] for row in MUTATIONS])
    parser.add_argument("--worker-root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--test", action="append", choices=TESTS, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker_root:
        return worker(args.worker_root.resolve(), args.test or TESTS)

    output = (args.output or Path(tempfile.mkdtemp(prefix="geometry-r356-geo314-"))).resolve()
    output.mkdir(parents=True, exist_ok=True)
    source = output / "source"
    if source.exists() or (output / "summary.json").exists():
        raise SystemExit("Use a new output directory; existing evidence is never overwritten")
    judge = load_judge(ROOT)
    inputs = sorted({JUDGE, *judge.source_paths()})
    originals = {path: (ROOT / path).read_bytes() for path in inputs}
    for path, data in originals.items():
        destination = source / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    hashes = {path: sha(data) for path, data in originals.items()}
    (output / "inputs.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
    baseline = run_judge(source, TESTS, output / "baseline.json")
    if not green(baseline, len(TESTS)):
        raise SystemExit("Baseline failed; no mutation receives detection credit (see baseline.json)")

    records = []
    for name, path, before, after, test, assertion in MUTATIONS:
        if args.only and name not in args.only:
            continue
        old = originals[path]
        anchors = ((before, after),) if isinstance(before, str) else tuple(zip(before, after))
        changed = old
        for original, replacement in anchors:
            if changed.count(original.encode()) != 1:
                raise SystemExit(name + ": exact source anchor must occur once")
            changed = changed.replace(original.encode(), replacement.encode(), 1)
        result = {"name": name, "path": path, "test": test, "assertion": assertion,
                  "originalSha256": sha(old), "mutatedSha256": sha(changed)}
        destination = source / path
        try:
            destination.write_bytes(changed)
            mutant = run_judge(source, (test,), output / (name + ".json"))
        finally:
            destination.write_bytes(old)
        restored = run_judge(source, TESTS, output / (name + ".restored.json"))
        verdict = mutant.get("result", {})
        failures = verdict.get("failures", [])
        detected = (mutant.get("returncode") == 1 and verdict.get("testsRun") == 1
                    and not verdict.get("errors") and not verdict.get("skipped")
                    and len(failures) == 1 and failures[0]["test"] == test
                    and "AssertionError:" in failures[0]["trace"]
                    and assertion in failures[0]["trace"])
        result.update(detected=detected, restored=green(restored, len(TESTS)),
                      sourceRestored=destination.read_bytes() == old)
        records.append(result)
        print(name + ": " + ("assertion detected; restored green" if all(
            result[key] for key in ("detected", "restored", "sourceRestored")) else "FAILED"))
    same = all((source / path).read_bytes() == data for path, data in originals.items())
    passed = same and all(all(row[key] for key in ("detected", "restored", "sourceRestored")) for row in records)
    summary = {"schema": "r356-geo314-source-contract-mutations/1", "judge": JUDGE,
               "judgeSha256": hashes[JUDGE], "runnerSha256": sha(Path(__file__).read_bytes()),
               "inputCount": len(inputs), "baselineTests": len(TESTS), "sourceRestored": same,
               "mutations": records, "passed": passed}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Source-contract proof: " + str(len(records)) + " named mutations; " + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
