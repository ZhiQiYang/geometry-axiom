#!/usr/bin/env python3
"""Named R13 product withdrawals in disposable module copies: Node, not Chrome.

Every withdrawal must be a completed named assertion failure between two green
executions of that exact test. Syntax errors, missing modules and crashes earn
no kill. Shared checkout, suite counts, golden and official evidence are never
edited. Run after applying T and P, with --out pointing outside the checkout.
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
DATA = "geometry-web/reconstruction-data.js"
VALUES = "geometry-core/reconstruction-values.js"
RUNTIME = "geometry-web/runtime_version.py"
INDEX = "geometry-web/index.html"
TEST = "tests/test_r13_reconstruction.js"
ORACLE = "tests/oracles/r13_height_oracle.py"
TABLE = "tests/oracles/r13_e1_contract.json"
BASE = "b3c4b981bb96b118c1c05b7a1bd98062d710c8b2"
FAULTS = (
    ("R13_EXACT_MM_REMAINDER_REMOVED", VALUES,
     "if(numerator%scale!==0n)fail('EXACT_INTEGER_MM','換算結果不是整數 mm；不會四捨五入或截斷。');",
     "// Withdrawal: silently truncate fractional millimetres.", "R13_DECIMAL", "R13_EXACT_REJECTION"),
    ("R13_CM_SCALE_DOUBLED", VALUES,
     "(unit==='cm'?10n:1n)", "(unit==='cm'?20n:1n)", "R13_DECIMAL", "R13_EXACT_DECIMAL"),
    ("R13_DERIVED_SUM_SIGN_REVERSED", VALUES,
     "BigInt(c)-BigInt(a):BigInt(a)+BigInt(b)", "BigInt(c)-BigInt(a):BigInt(a)-BigInt(b)",
     "R13_ORACLE", "R13_ORACLE_EXACT_VALUE"),
    ("R13_UNCONFIRMED_INPUT_DERIVED", DATA,
     "if(others.some(key=>record.fields[key].confirmation?.kind!=='direct'))return null;",
     "// Withdrawal: entered numbers are treated as confirmed evidence.",
     "R13_DERIVE", "R13_UNCONFIRMED_INPUT_NOT_DERIVED"),
    ("R13_CONFLICTING_THIRD_INPUT_IGNORED", DATA,
     "if(values.every(value=>value!==null)&&['bottom','top'].every(key=>record.fields[key].basis.kind==='world-z'))K.solve(...values);",
     "// Withdrawal: ignore an entered third observation.", "R13_DERIVE", "R13_CONFLICT_BLOCKS_PLAN"),
    ("R13_POSITION_DATUM_GUARD_REMOVED", DATA,
     "if((key==='bottom'||key==='top')&&field.basis.kind!=='world-z')\n      fail('R13_DATUM_ADOPTION','位置採用或推導須明選世界 Z；觀察確認及說明文字不建立座標轉換。');",
     "// Withdrawal: an unknown position datum is accepted.", "R13_DATUM", "R13_DATUM_REQUIRED"),
    ("R13_HISTORY_HIGHWATER_REMOVED", DATA,
     "if(water){next.nextId=Math.max(next.nextId,water.nextId);next.nextRevision=Math.max(next.nextRevision,water.nextRevision);}",
     "// Withdrawal: an undo branch reuses issued identities and revisions.",
     "R13_HIGHWATER", "R13_ID_HIGHWATER"),
    ("R13_DELETE_MISSING_MARK_REMOVED", DATA,
     "for(const review of next.reviews)for(const scope of review.scope)if(scope.recordId===action.id)scope.missing=true;",
     "// Withdrawal: deleting data forgets the historical loss mark.", "R13_MISSING", "R13_DELETE_MISSING_SAME_STEP"),
    ("R13_MODEL_PINS_REMOVED", DATA,
     "if(review.sourceSha256!==await digest(sourceBasis(model))||review.inputSha256!==await digest(model.input)||review.resultSha256!==await digest(model.result))\n        fail('R13_REVIEW_MODEL_PIN','核對與保存模型的完整來源、輸入或結果不相符，未載入專案。');",
     "// Withdrawal: hash-shaped text is trusted without recomputation.", "R13_REVIEW_FORGERY", "R13_REVIEW_RECOMPUTED"),
    ("R13_REVIEW_STALENESS_REMOVED", DATA,
     "return record.revision===scope.revision&&same(record.fields,scope.snapshot.fields)?'current':'stale';",
     "return 'current';", "R13_REVIEW_STALE", "R13_CHANGED_REVIEW_STALE"),
    ("R13_MODEL_RELEASE_GUARD_REMOVED", DATA,
     "if(!same(before.get(review.modelId),after.get(review.modelId)))fail('R13_REVIEW_RELEASE_REQUIRED','模型已有補資料核對；請在這次修改中明選解除，或重新建立完整核對。');",
     "// Withdrawal: changed models silently retain a historical review.",
     "R13_MODEL_WRITERS", "R13_MODEL_CHANGE_REQUIRES_RELEASE"),
    ("R13_E1_IMPLICIT_MM_RESTORED", DATA,
     "for(const key of FIELD_NAMES)fields[key]={raw:'',unit:null,",
     "for(const key of FIELD_NAMES)fields[key]={raw:'',unit:'mm',",
     "R13_E1_UNITS", "R13_E1_NO_IMPLICIT_MM"),
    ("R13_E1_UNKNOWN_BASIS_CONFIRMATION_REJECTED", DATA,
     "function directValue(field,key){return K.decimal(",
     "function directValue(field,key){assertDatum(field,key);return K.decimal(",
     "R13_DATUM", "R13_UNKNOWN_BASIS_OBSERVATION_CONFIRMABLE"),
    ("R13_E1_WORLD_BASIS_NOTE_REQUIRED", DATA,
     "if((key==='bottom'||key==='top')&&field.basis.kind!=='world-z')",
     "if((key==='bottom'||key==='top')&&(field.basis.kind!=='world-z'||!field.basis.note.trim()))",
     "R13_DATUM", "R13_TYPED_WORLD_BASIS_SUFFICIENT"),
    ("R13_E1_DERIVED_UNIT_GUESSED", DATA,
     "if(targetField.unit===null)fail('R13_DERIVED_UNIT','推導目標仍須明選 mm 或 cm；精確結果以整數 mm 保存。');",
     "// Withdrawal: silently choose a unit for the empty target.",
     "R13_E1_UNITS", "R13_E1_DERIVED_UNIT_EXPLICIT"),
    ("R13_E1_DERIVATION_SOURCE_DATUM_IGNORED", DATA,
     "for(const key of others)assertDatum(record.fields[key],key);",
     "// Withdrawal: compare an unknown position with a World coordinate.",
     "R13_E1_UNITS", "R13_E1_DERIVATION_BASIS_bottom-from-top"),
    ("R13_E1_SUBSET_MARKED_COMPLETE", DATA,
     "completeness:omitted.length?'defined-subset':'selected-scope-reviewed'",
     "completeness:'selected-scope-reviewed'",
     "R13_E1_SCOPE", "R13_E1_SUBSET_NOT_FULL_REVIEW"),
    ("R13_E1_TOP_CHECK_DROPPED", DATA,
     "if(top.confirmation&&top.basis.kind==='world-z')checks.push(",
     "if(false)checks.push(",
     "R13_E1_SCOPE", "R13_E1_ALL_CONFIRMATIONS_REQUIRED"),
    ("R13_E1_COMPLETENESS_VALIDATION_REMOVED", DATA,
     "if(review.completeness!==expected.completeness||!same(scope.omitted,expected.omitted))",
     "if(!same(scope.omitted,expected.omitted))",
     "R13_E1_SCOPE_FORGERY", "R13_E1_SCOPE_RECOMPUTED"),
    ("R13_E1_OMITTED_REASONS_VALIDATION_REMOVED", DATA,
     "if(review.completeness!==expected.completeness||!same(scope.omitted,expected.omitted))",
     "if(review.completeness!==expected.completeness)",
     "R13_E1_SCOPE_FORGERY", "R13_E1_SCOPE_RECOMPUTED"),
    ("R13_E1_TOP_CHECK_HASH_TRUSTED", DATA,
     "for(const check of scope.checks)if(check.confirmationSha256!==await digest(scope.snapshot.fields[check.field].confirmation))\n        fail('R13_REVIEW_CONFIRMATION_PIN','人工核對確認內容指紋不相符，不能視為有效核對。');",
     "// Withdrawal: trust a hash-shaped top-check pin without recomputation.",
     "R13_E1_SCOPE_FORGERY", "R13_E1_TOP_CHECK_RECOMPUTED"),
    ("R13_E1_INVALID_UNICODE_SCALAR_ACCEPTED", DATA,
     "if(point>=0xd800&&point<=0xdfff)return -1;",
     "// Withdrawal: treat an unpaired surrogate as a Unicode scalar.\n",
     "R13_CAPACITY", "R13_LONE_HIGH_SURROGATE_REJECTED"),
    ("R13_CORE_ROUTE_REMOVED", RUNTIME,
     "        '/kernel/reconstruction-values.js': root / 'geometry-core/reconstruction-values.js',\n",
     "        # Withdrawal: omit the explicitly served core arithmetic module.\n",
     "R13_OWNER", "R13_CORE_ROUTE"),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(command: list[str], env: dict, target: Path) -> tuple[dict, str]:
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=60)
    target.with_suffix(".stdout").write_bytes(result.stdout)
    target.with_suffix(".stderr").write_bytes(result.stderr)
    output = result.stdout.decode("utf-8") + result.stderr.decode("utf-8")
    counts = {key: int(value) for key, value in
              re.findall(r"^# (tests|pass|fail|cancelled|skipped|todo) (\d+)$", output, re.M)}
    record = {"command": command, "exit": result.returncode, "counts": counts,
              "stdoutBytes": len(result.stdout), "stdoutSha256": digest(result.stdout),
              "stderrBytes": len(result.stderr), "stderrSha256": digest(result.stderr)}
    target.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record, output


def green(result: dict, count: int) -> bool:
    counts = result["counts"]
    return result["exit"] == 0 and counts.get("tests") == count and counts.get("pass") == count and all(
        counts.get(key) == 0 for key in ("fail", "cancelled", "skipped", "todo"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", choices=[fault[0] for fault in FAULTS])
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error("--out must be empty")
    out.mkdir(parents=True, exist_ok=True)
    original = {name: (ROOT / name).read_bytes() for name in (DATA, VALUES, RUNTIME)}
    faults = [fault for fault in FAULTS if not args.only or fault[0] == args.only]
    summary = {"schema": "r13-reconstruction-withdrawals/1", "base": BASE,
               "level": "Node product modules + independent Python Fraction oracle; no browser execution",
               "sources": {name: {"bytes": len((ROOT / name).read_bytes()), "sha256": digest((ROOT / name).read_bytes())}
                           for name in (DATA, VALUES, RUNTIME, INDEX, TEST, ORACLE, TABLE, "geometry-web/project-store.js", "geometry-web/feature-attachments.js")},
               "results": []}
    with tempfile.TemporaryDirectory(prefix="r13-withdrawals-") as directory:
        work = Path(directory)
        for name, contents in original.items():
            destination = work / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(contents)
        env = {**os.environ, "NO_COLOR": "1", "GEOMETRY_R13_DATA_SOURCE": str(work / DATA),
               "GEOMETRY_R13_VALUES_SOURCE": str(work / VALUES),
               "GEOMETRY_R13_RUNTIME_SOURCE": str(work / RUNTIME)}
        normal, _ = run(["node", "--test", "--test-reporter=tap", TEST], env, out / "full-baseline")
        summary["baseline"] = normal
        if not green(normal, 22):
            raise RuntimeError("baseline must complete exactly 22/22; no mutation credit")
        for name, source, before, after, case, assertion in faults:
            base_bytes = original[source]
            if base_bytes.count(before.encode()) != 1:
                raise RuntimeError(name + ": expected exactly one unchanged product anchor")
            destination = out / name
            destination.mkdir()
            command = ["node", "--test", "--test-reporter=tap", "--test-name-pattern=^" + case + " ", TEST]
            baseline, _ = run(command, env, destination / "baseline")
            if not green(baseline, 1):
                raise RuntimeError(name + ": named control is not one real green test")
            target = work / source
            changed = base_bytes.replace(before.encode(), after.encode(), 1)
            try:
                target.write_bytes(changed)
                fault, output = run(command, env, destination / "fault")
                counts = fault["counts"]
                killed = fault["exit"] == 1 and counts.get("tests") == 1 and counts.get("fail") == 1 and counts.get("pass") == 0 and all(
                    counts.get(key) == 0 for key in ("cancelled", "skipped", "todo")) and "ERR_ASSERTION" in output and assertion in output
            finally:
                target.write_bytes(base_bytes)
            restored, _ = run(command, env, destination / "restored")
            if not killed or not green(restored, 1) or target.read_bytes() != base_bytes:
                raise RuntimeError(name + ": no completed named assertion kill and exact-byte restoration")
            summary["results"].append({"name": name, "status": "killed", "source": source,
                                       "sourceSha256": digest(base_bytes), "faultSha256": digest(changed),
                                       "test": case, "assertion": assertion, "exits": [baseline["exit"], fault["exit"], restored["exit"]],
                                       "baseline": baseline, "fault": fault, "restored": restored})
            print(name + " 0/1/0", flush=True)
    summary["killed"] = len(summary["results"])
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
