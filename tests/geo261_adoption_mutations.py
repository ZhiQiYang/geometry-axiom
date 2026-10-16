#!/usr/bin/env python3
"""Reproduce GEO-261 adoption gate guard-removal evidence without editing the repo.

Formal run (the adoption suite must already be registered and fully green):
    python geo261_adoption_mutations.py --root /path/to/repo --out /path/to/new-receipts --expected-tests 15

Explicitly partial preflight before aggregate-suite registration:
    python geo261_adoption_mutations.py --root /path/to/repo --out /path/to/new-preflight --expected-tests 13 --skip-registration

The official baseline must pass every expected test, without errors or skips,
before any mutant runs. Five mutations replace only AST-selected require(...)
statements in disposable system-TEMP copies. The imported proposal helper is
also copied unchanged into TEMP. No source, approval, test, or fixture in the
repository is rewritten, and Python bytecode writes are disabled.

--skip-registration is ONLY a preflight option. Its receipt explicitly has
formalEvidence=false and status=preflight-passed; it can never establish the
registered adoption gate's formal result. It does not skip approval checks or
modify an approval answer. Formal mode checks both the aggregate runner's
registration and its expected-count manifest.

Receipts retain raw logs, exact failed test names, mutation diffs, before/after
input hashes, runner/helper fingerprints, and cleanup status. --out must be an
empty directory outside the repository. Exit 0 means baseline green and all
five mutants red in exactly the expected tests; mutant child exit 1 is expected.
Runner exit 1 means an evidence/contract failure; exit 2 means an environment
block. Passing here proves rejection witnesses, not implementation decoupling,
human authorization by itself, or product compatibility.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


SUITE_NAME = "py:test_domain_decoupling_adoption"
REGISTRY_NAME = "test_domain_decoupling_adoption"
GUARDS = (
    ("APPROVED_MARKDOWN", 1, [
        "test_joint_review_and_map_change_cannot_reuse_approval",
    ]),
    ("UPSTREAM_HASH", 1, [
        "test_upstream_source_is_independent_and_pinned",
    ]),
    ("ADDENDUM_AFTER", 1, [
        "test_scope_addendum_is_only_count_and_three_reviewed_entries",
    ]),
    ("ADOPTED_SOURCE", 1, [
        "test_current_source_tamper_deletion_and_layout_drift_are_rejected",
        "test_crlf_is_the_only_ignored_source_difference",
    ]),
    ("ADDENDUM_APPROVAL", 1, [
        "test_original_approval_alone_never_authorizes_added_scopes",
    ]),
)
INPUTS = {
    "test": "tests/test_domain_decoupling_adoption.py",
    "proposalHelper": "tests/test_domain_decoupling_proposal.py",
    "baseFixture": "tests/fixtures/geo261-axiom-base.txt",
    "upstreamFixture": "tests/fixtures/geo261-axiom-train17.txt",
    "approvedMap": "geometry-core/domain-decoupling/clause-map.json",
    "approvedMarkdown": "geometry-core/domain-decoupling/AXIOM-PROPOSAL.md",
    "approval": "geometry-core/domain-decoupling/APPROVAL.json",
    "addendumMap": "geometry-core/domain-decoupling/merge-addendum.json",
    "addendumMarkdown": "geometry-core/domain-decoupling/MERGE-ADDENDUM.md",
    "ssot": "公理層.md",
    "expected": "tests/run_all.expected.json",
    "aggregateRunner": "tests/run_all.py",
}


class EvidenceFailure(Exception):
    pass


def check(condition, message):
    if not condition:
        raise EvidenceFailure(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(data):
    return {
        "bytes": len(data),
        "sha256": sha256(data),
        "lfSha256": sha256(data.replace(b"\r\n", b"\n")),
    }


def is_within(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def remove_guard(source, code, expected_guard_count):
    """Locate exact require error codes using AST, leaving test bodies untouched."""
    tree = ast.parse(source)
    guards = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if (isinstance(call.func, ast.Name) and call.func.id == "require"
                and len(call.args) > 1 and isinstance(call.args[1], ast.Constant)
                and call.args[1].value == code):
            guards.append(node)
    check(len(guards) == expected_guard_count,
          f"{code}: expected {expected_guard_count} guard statements, found {len(guards)}")
    original_tests = {
        node.name: ast.dump(node, include_attributes=False)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }
    lines = source.splitlines(keepends=True)
    for guard in sorted(guards, key=lambda node: node.lineno, reverse=True):
        indent = lines[guard.lineno - 1][:guard.col_offset]
        lines[guard.lineno - 1:guard.end_lineno] = [
            indent + f"pass  # TEMP MUTANT: removed {code} guard\n"
        ]
    mutant = "".join(lines)
    mutated_tests = {
        node.name: ast.dump(node, include_attributes=False)
        for node in ast.walk(ast.parse(mutant))
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }
    check(mutated_tests == original_tests, f"{code}: a test body was altered")
    return mutant.encode("utf-8"), [
        {"startLine": node.lineno, "endLine": node.end_lineno}
        for node in sorted(guards, key=lambda node: node.lineno)
    ]


def check_registration(snapshots, expected_tests):
    expected = json.loads(snapshots["expected"])["suites"].get(SUITE_NAME)
    required = {"mode": "count", "count": expected_tests, "unit": "test"}
    check(expected == required,
          f"expected-count registration differs: expected {required!r}, found {expected!r}")
    assignments = []
    for node in ast.parse(snapshots["aggregateRunner"].decode("utf-8")).body:
        if (isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "PY_NEEDS" for target in node.targets)):
            assignments.append(node.value)
    check(len(assignments) == 1, "aggregate runner must have one literal PY_NEEDS registration")
    registry = ast.literal_eval(assignments[0])
    check(REGISTRY_NAME in registry and registry[REGISTRY_NAME] == [],
          "adoption gate must be registered as a deliberate native-binary-free suite")
    return {"checked": True, "expectedManifest": expected, "nativeBinaryNeeds": registry[REGISTRY_NAME]}


def run_suite(python, target, root, out, name, timeout):
    env = dict(os.environ)
    env.update(GEOMETRY_PROPOSAL_ROOT=str(root), PYTHONIOENCODING="utf-8",
               PYTHONDONTWRITEBYTECODE="1", PYTHONPATH="")
    command = [python, "-B", str(target)]
    log_path = out / (name + ".log")
    try:
        process = subprocess.run(command, cwd=root, env=env,
                                 capture_output=True, timeout=timeout)
        raw_log = process.stdout + process.stderr
    except subprocess.TimeoutExpired as error:
        raw_log = (error.stdout or b"") + (error.stderr or b"")
        log_path.write_bytes(raw_log)
        raise
    log_path.write_bytes(raw_log)
    log = raw_log.decode("utf-8").replace("\r\n", "\n")
    counts = re.findall(r"^Ran (\d+) tests? in ", log, re.MULTILINE)
    failed_cases = re.findall(r"^FAIL: ([^ \n]+)", log, re.MULTILINE)
    error_cases = re.findall(r"^ERROR: ([^ \n]+)", log, re.MULTILINE)
    return {
        "command": command,
        "exit": process.returncode,
        "testsRun": int(counts[-1]) if len(counts) == 1 else None,
        "failedCases": failed_cases,
        "failures": len(failed_cases),
        "errorCases": error_cases,
        "errors": len(error_cases),
        "skips": len(re.findall(r"^.* \.\.\. skipped ", log, re.MULTILINE)),
        "cleanOK": bool(re.search(r"^OK$", log, re.MULTILINE)),
        "hasUnexpectedStatus": bool(re.search(r"\b(?:skipped=|expected failures=|unexpected successes=)", log)),
        "log": log_path.name,
        "logSha256": sha256(raw_log),
        "logLfSha256": sha256(raw_log.replace(b"\r\n", b"\n")),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, required=True, help="Repository containing the adoption gate and original inputs")
    parser.add_argument("--out", type=Path, required=True, help="Empty receipt directory outside the repository")
    parser.add_argument("--expected-tests", type=int, required=True, help="Exact official baseline test count for this stage")
    parser.add_argument("--skip-registration", action="store_true", help="PREFLIGHT ONLY: skip aggregate registration, never approval checks")
    parser.add_argument("--python", default=sys.executable, help="Child Python executable (default: this interpreter)")
    parser.add_argument("--timeout", type=float, default=60, help="Maximum seconds per test run (default: 60)")
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    if not root.is_dir() or args.timeout <= 0 or args.expected_tests <= 0:
        parser.error("--root must be a directory, and --timeout/--expected-tests must be positive")
    if is_within(out, root):
        parser.error("--out must be outside the repository; repository writes are forbidden")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error("--out must be a new or empty directory; existing evidence is never overwritten")
    for relative in INPUTS.values():
        if not (root / relative).is_file():
            parser.error(f"required input missing: {root / relative}")
    out.mkdir(parents=True, exist_ok=True)
    snapshots = {name: (root / relative).read_bytes() for name, relative in INPUTS.items()}
    report = {
        "schema": "geo261-adoption-mutation-evidence/1",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "phase": "preflight" if args.skip_registration else "formal",
        "formalEvidence": not args.skip_registration,
        "scope": "adoption-integrity guard-removal witnesses only; not product or implementation validation",
        "pythonExecutable": args.python,
        "runnerInterpreter": sys.version,
        "runnerScript": fingerprint(Path(__file__).read_bytes()),
        "expectedTests": args.expected_tests,
        "registration": {
            "checked": False,
            "reason": "explicit --skip-registration: PREFLIGHT ONLY" if args.skip_registration else "not checked yet",
        },
        "hashNormalization": "lfSha256 replaces CRLF with LF only; raw SHA-256 and byte counts are also retained.",
        "inputFilesBefore": {name: {"path": INPUTS[name], **fingerprint(data)} for name, data in snapshots.items()},
        "repositoryPolicy": "Read-only inputs. No approval answer or fixture is rewritten; Python bytecode writes disabled.",
        "temporaryPolicy": "Only AST guard statements in TEMP adoption-test copies are removed; proposal helper copied unchanged.",
        "temporaryCopiesDeleted": False,
        "baseline": None,
        "mutants": [],
    }
    exit_code = 0
    temp_root = None
    try:
        if not args.skip_registration:
            report["registration"] = check_registration(snapshots, args.expected_tests)
        source = snapshots["test"].decode("utf-8")
        baseline = run_suite(args.python, root / INPUTS["test"], root, out, "baseline", args.timeout)
        report["baseline"] = baseline
        check(baseline["exit"] == 0 and baseline["testsRun"] == args.expected_tests
              and baseline["cleanOK"] and not baseline["failedCases"] and baseline["errors"] == 0
              and baseline["skips"] == 0 and not baseline["hasUnexpectedStatus"],
              f"official baseline did not pass exactly {args.expected_tests} tests without skips; no mutants were run")
        check(not is_within(Path(tempfile.gettempdir()).resolve(), root),
              "system TEMP must be outside the repository before any temporary copy is created")
        with tempfile.TemporaryDirectory(prefix="geo261-adoption-mutants-") as temporary:
            temp_root = Path(temporary).resolve()
            check(temp_root.parent == Path(tempfile.gettempdir()).resolve()
                  and temp_root.name.startswith("geo261-adoption-mutants-")
                  and not is_within(temp_root, root),
                  "temporary cleanup path must stay in system TEMP outside the repository")
            for code, expected_guard_count, expected_failures in GUARDS:
                mutant, removed_lines = remove_guard(source, code, expected_guard_count)
                case_dir = temp_root / code.lower()
                case_dir.mkdir()
                target = case_dir / "test_domain_decoupling_adoption.py"
                target.write_bytes(mutant)
                helper = case_dir / "test_domain_decoupling_proposal.py"
                helper.write_bytes(snapshots["proposalHelper"])
                check(helper.read_bytes() == snapshots["proposalHelper"], f"{code}: copied proposal helper changed")
                diff_bytes = "".join(difflib.unified_diff(
                    source.replace("\r\n", "\n").splitlines(keepends=True),
                    mutant.decode("utf-8").replace("\r\n", "\n").splitlines(keepends=True),
                    fromfile=INPUTS["test"], tofile="TEMP/" + code.lower() + "/test_domain_decoupling_adoption.py",
                )).encode("utf-8")
                diff_name = code.lower() + ".diff"
                (out / diff_name).write_bytes(diff_bytes)
                result = run_suite(args.python, target, root, out, code.lower(), args.timeout)
                result.update(
                    guard=code, removedStatements=expected_guard_count, removedLines=removed_lines,
                    expectedFailedCases=expected_failures, mutant=fingerprint(mutant),
                    proposalHelper=fingerprint(snapshots["proposalHelper"]),
                    diff=diff_name, diffSha256=sha256(diff_bytes), testBodiesUnchanged=True,
                )
                report["mutants"].append(result)
                check(result["exit"] == 1 and result["testsRun"] == args.expected_tests
                      and result["errors"] == 0 and result["skips"] == 0
                      and not result["cleanOK"] and not result["hasUnexpectedStatus"]
                      and Counter(result["failedCases"]) == Counter(expected_failures),
                      f"{code}: expected named rejection witnesses did not fail exactly as specified")
        report["temporaryCopiesDeleted"] = not temp_root.exists()
        check(report["temporaryCopiesDeleted"], "TEMP mutant directory was not removed")
    except EvidenceFailure as error:
        report["failure"] = str(error)
        exit_code = 1
    except (KeyError, ValueError, SyntaxError, TypeError) as error:
        report["failure"] = f"evidence contract error: {type(error).__name__}: {error}"
        exit_code = 1
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as error:
        report["failure"] = f"environment block: {type(error).__name__}: {error}"
        exit_code = 2
    finally:
        report["temporaryCopiesDeleted"] = temp_root is None or not temp_root.exists()
        after = {}
        unchanged = {}
        for name, original in snapshots.items():
            try:
                current = (root / INPUTS[name]).read_bytes()
                after[name] = {"path": INPUTS[name], **fingerprint(current)}
                unchanged[name] = current == original
            except OSError as error:
                after[name] = {"path": INPUTS[name], "readError": f"{type(error).__name__}: {error}"}
                unchanged[name] = False
        report["inputFilesAfter"] = after
        report["inputsUnchanged"] = unchanged
        if not all(unchanged.values()):
            report["failure"] = "official inputs changed during the run; receipts are not a frozen-version result"
            exit_code = 1
        if not report["temporaryCopiesDeleted"]:
            report["failure"] = "TEMP mutant directory was not removed"
            exit_code = 1
        report["runnerExit"] = exit_code
        report["status"] = (("preflight-passed" if args.skip_registration else "passed") if exit_code == 0
                            else ("failed" if exit_code == 1 else "blocked"))
        (out / "mutation-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"], "phase": report["phase"], "formalEvidence": report["formalEvidence"],
        "runnerExit": exit_code,
        "baselineTests": report["baseline"]["testsRun"] if report["baseline"] else None,
        "mutants": [{"guard": result["guard"], "exit": result["exit"], "testsRun": result["testsRun"],
                     "failedCases": result["failedCases"], "errors": result["errors"]} for result in report["mutants"]],
        "inputsUnchanged": all(report["inputsUnchanged"].values()),
        "temporaryCopiesDeleted": report["temporaryCopiesDeleted"],
        "result": str(out / "mutation-results.json"), "failure": report.get("failure"),
    }, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
