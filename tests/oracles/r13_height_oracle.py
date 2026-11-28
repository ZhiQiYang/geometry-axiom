#!/usr/bin/env python3
"""R13 independent exact-height oracle; no product imports or floating point.

Construction starts with integer coordinates. The independent checker parses
the rendered decimal observations through Fraction and checks the missing
coordinate by a signed residual, not by the product's derivation function.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import re
from pathlib import Path

LIMIT = 100_000_000
DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)\Z")
FIELDS = ("bottom", "height", "top")


def exact_mm(raw: str, unit: str, *, positive: bool = False) -> int:
    if not isinstance(raw, str) or not DECIMAL.fullmatch(raw) or unit not in ("mm", "cm"):
        raise ValueError("R13_ORACLE_DECIMAL")
    value = Fraction(raw) * (10 if unit == "cm" else 1)
    if value.denominator != 1 or not -LIMIT <= value <= LIMIT or positive and value <= 0:
        raise ValueError("R13_ORACLE_DOMAIN")
    return value.numerator


def classify_decimal(raw, unit, positive: bool) -> dict:
    """Independent lexical and Fraction result, including absolute end-of-input."""
    if not isinstance(raw, str) or not DECIMAL.fullmatch(raw):
        return {"accepted": False, "error": "EXACT_DECIMAL_LITERAL"}
    if unit not in ("mm", "cm"):
        return {"accepted": False, "error": "EXACT_DECIMAL_UNIT"}
    value = Fraction(raw) * (10 if unit == "cm" else 1)
    if value.denominator != 1:
        return {"accepted": False, "error": "EXACT_INTEGER_MM"}
    if not -LIMIT <= value <= LIMIT or positive and value <= 0:
        return {"accepted": False, "error": "EXACT_DOMAIN"}
    return {"accepted": True, "value": value.numerator}


def contract_report() -> dict:
    table_path = Path(__file__).with_name("r13_e1_contract.json")
    raw = table_path.read_bytes()
    table = json.loads(raw)
    if table.get("schema") != "r13-e1-contract-oracle/2":
        raise AssertionError("R13_E1_ORACLE_SCHEMA")
    rows = table["decimalCases"]
    def check_decimal(row):
        return classify_decimal(row["raw"], row["unit"], row["positive"]) == row["expected"]
    failures = [row["id"] for row in rows if not check_decimal(row)]
    survived = []
    for row in rows:
        false_expected = ({"accepted": True, "value": row["expected"]["value"] + 1}
                          if row["expected"]["accepted"] else {"accepted": True, "value": 0})
        if check_decimal({**row, "expected": false_expected}):
            survived.append(row["id"])
    derivations = table["derivationBasisCases"]
    for row in derivations:
        expected = row["expected"]
        if row["unknown"] is not None:
            if expected != {"accepted": False, "error": "R13_DATUM_ADOPTION"}:
                failures.append(row["id"])
            continue
        witness = {"missing": row["missing"], "unit": row["unit"], "raw": row["raw"], "expected": expected["value"]}
        if not expected["accepted"] or not check(witness):
            failures.append(row["id"])
    return {"schema": "r13-e1-contract-scan/2", "decimalCases": len(rows),
            "derivationBasisCases": len(derivations), "stateCases": len(table["stateCases"]),
            "stateCaseExecution": "Node product/state/host suites; this Python checker verifies decimal and relation witnesses",
            "violations": failures, "checkerMutation": {"name": "R13_E1_ORACLE_FORGE_EXPECTED",
            "tested": len(rows), "rejected": len(rows) - len(survived), "survived": survived},
            "oracleTableSha256": hashlib.sha256(raw).hexdigest(), "browserExecuted": False}


def spell(mm: int, unit: str) -> str:
    if unit == "mm":
        return str(mm)
    magnitude = abs(mm)
    return ("-" if mm < 0 else "") + str(magnitude // 10) + "." + str(magnitude % 10)


def construct(bottom: int, height: int, missing: str, unit: str) -> dict:
    values = {"bottom": bottom, "height": height, "top": bottom + height}
    return {"missing": missing, "unit": unit,
            "raw": {key: "" if key == missing else spell(value, unit) for key, value in values.items()},
            "expected": values[missing]}


def check(vector: dict) -> bool:
    """Accept only a complete independently checked witness for a missing value."""
    if set(vector) != {"missing", "unit", "raw", "expected"} or vector["missing"] not in FIELDS:
        return False
    raw, missing = vector["raw"], vector["missing"]
    if set(raw) != set(FIELDS) or raw[missing] != "" or type(vector["expected"]) is not int:
        return False
    try:
        values = {key: vector["expected"] if key == missing else exact_mm(raw[key], vector["unit"], positive=key == "height")
                  for key in FIELDS}
    except (ValueError, TypeError):
        return False
    if any(not -LIMIT <= value <= LIMIT for value in values.values()) or values["height"] <= 0:
        return False
    # An oriented coordinate difference must equal the positive distance.
    return values["top"] - values["bottom"] - values["height"] == 0


def vectors() -> list[dict]:
    return [construct(bottom, height, missing, unit)
            for bottom in range(-8, 9) for height in range(1, 18)
            for missing in FIELDS for unit in ("mm", "cm")]


def plan_cases() -> list[dict]:
    """Independent rectangular-solid expectations, including a nonzero datum."""
    cases = [
        {"bottom": {"raw": "-10", "unit": "cm"}, "height": {"raw": "270.0", "unit": "cm"}, "wallThickness": None},
        {"bottom": {"raw": "12.5", "unit": "cm"}, "height": {"raw": "10", "unit": "mm"}, "wallThickness": {"raw": "0.1", "unit": "cm"}},
        {"bottom": {"raw": "-0.1", "unit": "cm"}, "height": {"raw": "0.1", "unit": "cm"}, "wallThickness": None},
    ]
    output = []
    for fields in cases:
        bottom = exact_mm(**fields["bottom"])
        height = exact_mm(**fields["height"], positive=True)
        wall = fields["wallThickness"]
        thickness = None if wall is None else exact_mm(**wall, positive=True)
        output.append({"fields": fields, "expected": {"bottom": bottom, "height": height,
                       "top": bottom + height, "wallThickness": thickness,
                       "verticesZ": [bottom, bottom + height], "volumeMm3": str(Fraction(4000) * 3000 * height)}})
    return output


def report(rows: list[dict]) -> dict:
    failures = [row for row in rows if not check(row)]
    mutants = [{**row, "expected": row["expected"] + 1} for row in rows]
    escaped = [row for row in mutants if check(row)]
    decimal_cases = [("0.1", "cm", False, 1), ("27.0", "cm", True, 270),
                     ("-0.1", "cm", False, -1), ("10000000.0", "cm", False, LIMIT),
                     ("-100000000", "mm", False, -LIMIT)]
    for raw, unit, positive, expected in decimal_cases:
        if exact_mm(raw, unit, positive=positive) != expected:
            raise AssertionError("R13_ORACLE_EXACT_DECIMAL")
    refused = [("0.01", "cm", False), ("1.1", "mm", False), ("1e3", "mm", False),
               ("1,000", "mm", False), ("1/2", "cm", False), ("", "mm", False),
               ("-", "mm", False), ("0", "mm", True), ("-1", "mm", True),
               ("100000000.1", "cm", False), ("100000001", "mm", False)]
    for raw, unit, positive in refused:
        try:
            exact_mm(raw, unit, positive=positive)
        except ValueError:
            continue
        raise AssertionError("R13_ORACLE_REQUIRED_REJECTION")
    raw = (json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return {"schema": "r13-height-oracle/1", "construction": "integer bottom -8..8; height 1..17; three missing fields; mm/cm",
            "vectors": len(rows), "checked": len(rows), "violations": failures,
            "checkerMutation": {"name": "R13_ORACLE_CHANGE_MISSING_VALUE_BY_ONE", "tested": len(mutants),
                                "rejected": len(mutants) - len(escaped), "survived": escaped},
            "decimalCases": len(decimal_cases), "rejectedDecimalCases": len(refused),
            "vectorsSha256": hashlib.sha256(raw).hexdigest(), "browserExecuted": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vectors", action="store_true")
    parser.add_argument("--plan-cases", action="store_true")
    parser.add_argument("--contract", action="store_true")
    args = parser.parse_args()
    if args.contract:
        result = contract_report()
        if result["violations"] or result["checkerMutation"]["survived"]:
            raise AssertionError("R13_E1_ORACLE_CONTRACT")
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return
    if args.plan_cases:
        print(json.dumps({"schema": "r13-plan-oracle/1", "cases": plan_cases()}, ensure_ascii=False, separators=(",", ":")))
        return
    rows = vectors()
    result = report(rows)
    if result["violations"] or result["checkerMutation"]["survived"]:
        raise AssertionError("R13_ORACLE_SCAN")
    print(json.dumps({"report": result, "cases": rows} if args.vectors else result,
                     ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
