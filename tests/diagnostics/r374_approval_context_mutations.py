#!/usr/bin/env python3
"""Run the three R374 approval-context removal tests in isolated modules.

Run after applying the incremental patch to 4b21dd6:
  python3 -B tests/diagnostics/r374_approval_context_mutations.py --out /tmp/r374-context-run
The output directory must be new and outside this repository. Only named
assertion failures count as kills; errors, skips and crashes cannot pass.
Every case restores and reruns the unchanged 15-test suite. The SSOT, queue,
approved P and mutation ledger are never edited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SUBJECT = "tests/test_domain_decoupling_adoption.py"
INPUTS = (
    SUBJECT, "tests/test_domain_decoupling_proposal.py",
    "tests/fixtures/geo261-axiom-base.txt", "tests/fixtures/geo261-axiom-train17.txt",
    "tests/fixtures/r14-approved-axiom.patch", "公理層.md", "決策佇列.md",
    "geometry-core/domain-decoupling/clause-map.json",
    "geometry-core/domain-decoupling/AXIOM-PROPOSAL.md",
    "geometry-core/domain-decoupling/APPROVAL.json",
    "geometry-core/domain-decoupling/merge-addendum.json",
    "geometry-core/domain-decoupling/MERGE-ADDENDUM.md",
)
CONTEXT = "AdoptionIntegrity.check_r14_approval_context"
SECTION = "AdoptionIntegrity.check_r14_approval_section"

HARNESS = r'''
import importlib.util, json, os, pathlib, sys, unittest
root, subject, name, receipt = map(str, sys.argv[1:])
os.environ["GEOMETRY_PROPOSAL_ROOT"] = root
sys.path.insert(0, str(pathlib.Path(root) / "tests"))
spec = importlib.util.spec_from_file_location("r374_context_subject", subject)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
loader = unittest.defaultTestLoader
suite = loader.loadTestsFromModule(module) if name == "ALL" else loader.loadTestsFromName(name, module)
result = unittest.TextTestRunner(verbosity=2).run(suite)
payload = {"tests_run": result.testsRun, "failures": [[str(t), text] for t, text in result.failures],
           "errors": [[str(t), text] for t, text in result.errors],
           "skipped": [[str(t), why] for t, why in result.skipped],
           "unexpected_successes": [str(t) for t in result.unexpectedSuccesses],
           "expected_failures": [[str(t), text] for t, text in result.expectedFailures]}
pathlib.Path(receipt).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
sys.exit(0 if result.wasSuccessful() else 1)
'''


def replace_once(source, before, after):
    if source.count(before) != 1 or before == after:
        raise AssertionError("R374_CONTEXT_MUTATION_ANCHOR: expected one nonempty edit")
    return source.replace(before, after, 1)


def inputs():
    return {name: {"bytes": len(raw := (ROOT / name).read_bytes()),
                   "sha256": hashlib.sha256(raw).hexdigest()} for name in INPUTS}


def run(out, label, subject, selected):
    directory = out / label
    directory.mkdir()
    receipt = directory / "unittest.json"
    command = [sys.executable, "-B", "-c", HARNESS, str(ROOT), str(subject), selected, str(receipt)]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GEOMETRY_PROPOSAL_ROOT=str(ROOT))
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True,
                            encoding="utf-8", timeout=60)
    (directory / "stdout.log").write_text(result.stdout, encoding="utf-8")
    (directory / "stderr.log").write_text(result.stderr, encoding="utf-8")
    record = {"command": command, "returncode": result.returncode,
              "subject_sha256": hashlib.sha256(subject.read_bytes()).hexdigest(),
              "result": json.loads(receipt.read_text(encoding="utf-8")) if receipt.is_file() else None}
    (directory / "command.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def clean(record):
    value = record["result"]
    return (record["returncode"] == 0 and value is not None and value["tests_run"] == 15
            and not any(value[key] for key in ("failures", "errors", "skipped", "unexpected_successes", "expected_failures")))


def killed(record, code):
    value = record["result"]
    if (record["returncode"] != 1 or value is None or value["tests_run"] != 1 or not value["failures"]
            or any(value[key] for key in ("errors", "skipped", "unexpected_successes", "expected_failures"))):
        return False
    for _, trace in value["failures"]:
        assertions = [line for line in trace.splitlines()
                      if re.match(r"^(?:[A-Za-z_][\w.]*\.)?(?:AssertionError|ProposalContractError):", line)]
        if not assertions or not any(re.search(r"\b" + re.escape(code) + r"\b", line) for line in assertions):
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents:
        parser.error("--out must be a new directory outside the repository")
    out.mkdir(parents=True)
    original = (ROOT / SUBJECT).read_text(encoding="utf-8")
    before_inputs = inputs()
    baseline = run(out, "baseline", ROOT / SUBJECT, "ALL")
    if not clean(baseline):
        raise AssertionError("R374_CONTEXT_BASELINE: the unmodified suite must pass without errors or skips")
    cases = (
        ("R374_CONTEXT_01_REMOVE_CONTAINER_GATE", CONTEXT, "R14_APPROVAL_CONTEXT",
         '    require(starts[0] in heads, "R14_APPROVAL_CONTEXT", "R14 approval must be outside Markdown containers")\n',
         '    # container gate removed by this diagnostic mutant\n'),
        ("R374_CONTEXT_02_REMOVE_SECTION_PIN", SECTION, "R14_APPROVAL_SECTION",
         '    require("\\n".join(lines[starts[0]:end]) + ("\\n" if end < len(lines) else "") == R14_DECISION_SECTION,\n'
         '            "R14_APPROVAL_SECTION", "the complete recorded R14 section must remain verbatim")\n',
         '    # complete section pin removed by this diagnostic mutant\n'),
        ("R374_CONTEXT_03_REPLACE_SCANNER_WITH_RAW_HEADS", CONTEXT, "R14_APPROVAL_CONTEXT",
         '    heads = r14_section_heads(lines)\n',
         '    heads = [index for index, line in enumerate(lines) if line.startswith(("### ", "## "))]\n'),
    )
    results = []
    for name, selected, code, before, after in cases:
        subject = out / (name + ".py")
        subject.write_text(replace_once(original, before, after), encoding="utf-8", newline="\n")
        mutation = run(out, name, subject, selected)
        restoration = run(out, name + "-restored", ROOT / SUBJECT, "ALL")
        value = {"name": name, "assertion": code, "killed": killed(mutation, code),
                 "failures": len(mutation["result"]["failures"]) if mutation["result"] else None,
                 "restored": clean(restoration)}
        results.append(value)
        print(json.dumps(value, ensure_ascii=False))
        if not value["killed"] or not value["restored"] or inputs() != before_inputs:
            raise AssertionError("R374_CONTEXT_MUTATION: named failure, full restoration and unchanged inputs required")
    report = {"schema": "r374-context-removal-receipt/1",
              "base": "4b21dd629d93fce128b89e6cfcc0728a5b5c33e4", "inputs": before_inputs,
              "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "approved_P_LF": {
                  "bytes": len(raw := (ROOT / "tests/fixtures/r14-approved-axiom.patch").read_bytes().replace(b"\r\n", b"\n")),
                  "sha256": hashlib.sha256(raw).hexdigest()},
              "baseline": "15/15", "mutations": results,
              "summary": {"killed": len(results), "restored": len(results), "errors": 0, "skipped": 0}}
    (out / "receipt.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    main()
