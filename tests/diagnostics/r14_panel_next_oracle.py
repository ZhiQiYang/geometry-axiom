#!/usr/bin/env python3
"""R14 P467: exact one-cell source-rule oracle, independent of native code.

Recovery revision: rebuilt from the byte-verified V1, with a new source hash
and new executions. This is not the unavailable previous 25538-byte revision.

Input (millimetres):
  {u: {kind: panel, panel: 915, gap: 2, anchor: 0},
   v: {kind: repeat, step: 400, phase: 0},
   divisions: [7, 2], cell: ["-1", "0"], offset: [0, 0]}

JSON strings above are illustrative; use quoted keys/strings in actual JSON.
All axis fields are explicit integers; booleans/floats are not dimensions.
Cell indices are decimal strings in signed int64. Optional offset is an exact
integer translation, not a saved D30 origin or a validation of D30's anchors.
No clipping is done: lines describe the entire source cell before C intersect F.
No material, support, reference identity, capability or transaction is created.

build() uses Fraction and the D29 phase/pitch construction. check() never calls
build(), never reads construction intermediates and never trusts output bounds:
it uses independent seam endpoint equations plus integer remainder, interval
conservation and index/completeness tests. Shared parsing is syntactic only.
phase_bands() is a separate D10b diagnostic, NOT support for staggered subgrids.
The oracle models a newly proposed source/rule: the legacy two-stagger replay
exception in D10b is outside this input contract; any stagger forbids D19a.

  python -B tests/diagnostics/r14_panel_next_oracle.py --self-test
  python -B tests/diagnostics/r14_panel_next_oracle.py --scan [--jsonl PATH]
  python -B tests/diagnostics/r14_panel_next_oracle.py --input CASE.json
  python -B tests/diagnostics/r14_panel_next_oracle.py --check CASE.json RESULT.json
  python -B tests/diagnostics/r14_panel_next_oracle.py --mutations [--out NEW_DIR]

--check exit 0 means the result agrees with the specification; exit 1 means it
does not. A correctly reported geometric refusal is an agreeing result.
--mutations starts 33 actual --check subprocesses, saves their inputs/results,
stdout, stderr and exit codes, and requires 11 baseline/withdrawn/restored
sequences of 0/1/0. This is output-data sensitivity, not product C mutation.
"""
import argparse
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from itertools import product
import json
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile


COORD_LIMIT = 100_000_000  # D1, not a product-derived limit.
I64_MIN, I64_MAX = -(1 << 63), (1 << 63) - 1
AXES = ("u", "v")


class InputError(ValueError):
    pass


def _integer(value):
    if type(value) is not int:
        raise InputError("integer required")
    return value


def _index(value):
    if not isinstance(value, str) or re.fullmatch(r"[+-]?[0-9]+", value) is None:
        raise InputError("signed decimal string required")
    parsed = int(value)
    if not I64_MIN <= parsed <= I64_MAX:
        raise InputError("signed int64 required")
    return parsed


def _syntax(case):
    """Share grammar/type parsing only; no geometry or validity decisions."""
    if not isinstance(case, dict) or set(case) - {"u", "v", "divisions", "cell", "offset"}:
        raise InputError("unknown case field")
    axes = []
    for name in AXES:
        axis = case.get(name)
        if not isinstance(axis, dict):
            raise InputError("two explicit axes required")
        kind = axis.get("kind")
        fields = {"repeat": {"phase", "step"}, "panel": {"anchor", "panel", "gap"}}.get(kind)
        if fields is None or set(axis) - (fields | {"kind", "stagger"}) or not fields <= set(axis):
            raise InputError("axis kind/fields")
        axes.append({key: value if key == "kind" else _integer(value) for key, value in axis.items()})
    divisions, cell, offset = case.get("divisions"), case.get("cell"), case.get("offset", [0, 0])
    if any(not isinstance(value, list) or len(value) != 2 for value in (divisions, cell, offset)):
        raise InputError("two entries required")
    return axes, [_integer(n) for n in divisions], [_index(i) for i in cell], [_integer(o) for o in offset]


def _rejected(code):
    return {"status": "rejected", "code": code, "bounds": None, "lines": []}


def build(case):
    """Construct one un-clipped source cell using rational subdivision."""
    try:
        axes, divisions, cell, offset = _syntax(case)
    except (InputError, TypeError, ValueError):
        return _rejected("INPUT_SCHEMA")
    period, phase = [], []
    for axis in axes:
        if any(abs(value) > COORD_LIMIT for key, value in axis.items() if key != "kind"):
            return _rejected("SOURCE_RANGE")
        if axis["kind"] == "repeat":
            if axis["step"] <= 0:
                return _rejected("SOURCE_SIZE")
            period.append(axis["step"])
            phase.append(axis["phase"])
        else:
            if axis["panel"] <= 0 or axis["gap"] < 0:
                return _rejected("SOURCE_SIZE")
            period.append(axis["panel"] + axis["gap"])
            phase.append(axis["anchor"] + axis["panel"] + axis["gap"] // 2)
    # Explicit zero and an integer-pitch shift are invalid before subdivision.
    for axis, pitch in zip(axes, period):
        if "stagger" in axis:
            if axis["stagger"] == 0:
                return _rejected("STAGGER_ZERO")
            if axis["stagger"] % pitch == 0:
                return _rejected("STAGGER_MULTIPLE")
    if all("stagger" in axis for axis in axes):
        return _rejected("DOUBLE_STAGGER")
    if any("stagger" in axis for axis in axes):
        return _rejected("STAGGER_NOT_SUPPORTED")
    if any(not 1 <= n <= 65 for n in divisions) or divisions == [1, 1]:
        return _rejected("DIVISIONS")
    step = [Fraction(pitch, n) for pitch, n in zip(period, divisions)]
    if any(value.denominator != 1 for value in step):
        return _rejected("DIVISION_NOT_EXACT")
    if I64_MAX in cell:
        return _rejected("QUERY_OVERFLOW")
    starts = [p + index * pitch + delta for p, index, pitch, delta in zip(phase, cell, period, offset)]
    ends = [start + pitch for start, pitch in zip(starts, period)]
    if any(abs(value) > COORD_LIMIT for value in starts + ends):
        return _rejected("QUERY_OVERFLOW")
    lines = []
    for a, name in enumerate(AXES):
        for k in range(1, divisions[a]):
            coordinate = int(Fraction(starts[a]) + k * step[a])
            lines.append([name, k - 1, coordinate, starts[1 - a], ends[1 - a]])
    return {"status": "ok", "code": None,
            "bounds": [starts[0], starts[1], ends[0], ends[1]], "lines": lines}


def check(case, result):
    """Return independent violations; [] is an agreeing oracle result."""
    try:
        axes, divisions, cells, translation = _syntax(case)
    except (InputError, TypeError, ValueError):
        return [] if result == _rejected("INPUT_SCHEMA") else ["INPUT_SCHEMA_REQUIRED"]

    # Independent endpoint form: the panel's right edge after i full panels and
    # gaps, plus the lower half-gap. This does not consume build's phase/pitch.
    endpoints, spans = [], []
    code = None
    for a, axis in enumerate(axes):
        if any(not -COORD_LIMIT <= v <= COORD_LIMIT for k, v in axis.items() if k != "kind"):
            code = "SOURCE_RANGE"
            break
        if axis["kind"] == "repeat":
            if axis["step"] < 1:
                code = "SOURCE_SIZE"
                break
            lo = axis["phase"] + cells[a] * axis["step"] + translation[a]
            hi = axis["phase"] + (cells[a] + 1) * axis["step"] + translation[a]
        else:
            body, gap = axis["panel"], axis["gap"]
            if body < 1 or gap < 0:
                code = "SOURCE_SIZE"
                break
            half_gap, _ = divmod(gap, 2)
            lo = axis["anchor"] + (cells[a] + 1) * body + cells[a] * gap + half_gap + translation[a]
            hi = axis["anchor"] + (cells[a] + 2) * body + (cells[a] + 1) * gap + half_gap + translation[a]
        endpoints.append((lo, hi))
        spans.append(hi - lo)
    if code is None:
        shifts = [(a, axis["stagger"]) for a, axis in enumerate(axes) if "stagger" in axis]
        for a, shift in shifts:
            if shift == 0:
                code = "STAGGER_ZERO"
                break
            _, remainder = divmod(shift, spans[a])
            if remainder == 0:
                code = "STAGGER_MULTIPLE"
                break
        if code is None and shifts:
            code = "DOUBLE_STAGGER" if len(shifts) == 2 else "STAGGER_NOT_SUPPORTED"
    if code is None and (any(n < 1 or n > 65 for n in divisions) or sum(divisions) == 2):
        code = "DIVISIONS"
    if code is None and any(divmod(length, count)[1] for length, count in zip(spans, divisions)):
        code = "DIVISION_NOT_EXACT"
    if code is None and (any(c + 1 > I64_MAX for c in cells) or
                         any(v < -COORD_LIMIT or v > COORD_LIMIT for pair in endpoints for v in pair)):
        code = "QUERY_OVERFLOW"
    if code is not None:
        return [] if result == _rejected(code) else [code + "_REQUIRED_WITHOUT_LINES"]

    if not isinstance(result, dict) or set(result) != {"status", "code", "bounds", "lines"}:
        return ["RESULT_SCHEMA"]
    failures = []
    if result["status"] != "ok" or result["code"] is not None:
        failures.append("EXACT_RULE_MUST_SUCCEED")
    expected_bounds = [endpoints[0][0], endpoints[1][0], endpoints[0][1], endpoints[1][1]]
    bounds = result["bounds"]
    if (not isinstance(bounds, list) or len(bounds) != 4 or
            any(type(value) is not int for value in bounds)):
        failures.append("BOUNDS_SCHEMA")
    elif bounds != expected_bounds:
        failures.append("SOURCE_PARENT_BOUNDARIES")
    lines = result.get("lines")
    if not isinstance(lines, list) or any(not isinstance(row, list) or len(row) != 5 or
                                        row[0] not in AXES or any(type(x) is not int for x in row[1:])
                                        for row in lines):
        return failures + ["LINE_SCHEMA"]
    if len(lines) != sum(divisions) - 2:
        failures.append("NO_MISSING_OR_PARENT_LINES")
    expected_ids = [(name, index) for name, count in zip(AXES, divisions) for index in range(count - 1)]
    if [(row[0], row[1]) for row in lines] != expected_ids:
        failures.append("EXACT_ORDERED_INNER_IDENTITIES")
    for a, name in enumerate(AXES):
        rows = [row for row in lines if row[0] == name]
        lo, hi = endpoints[a]
        points = [lo] + [row[2] for row in rows] + [hi]
        # Every consecutive interval must conserve exactly 1/n of the input
        # span. No rounded expected-coordinate list is generated here.
        if any((right - left) * divisions[a] != spans[a] for left, right in zip(points, points[1:])):
            failures.append(name + ":EXACT_EQUAL_INTERVALS")
        for _, index, coordinate, begin, end in rows:
            if not lo < coordinate < hi:
                failures.append(name + ":INTERIOR_ONLY")
            if (coordinate - lo) * divisions[a] != (index + 1) * spans[a]:
                failures.append(name + ":INDEX_LOCATION")
            if (begin, end) != endpoints[1 - a]:
                failures.append(name + ":FULL_PARENT_SPAN")
    return failures


def phase_bands(axis, indices, bands):
    """D10b diagnostic only. Raises InputError for an invalid axis or index."""
    probe = {"u": axis, "v": {"kind": "repeat", "step": 1, "phase": 0},
             "divisions": [2, 1], "cell": ["0", "0"]}
    parsed = _syntax(probe)[0][0]
    if any(abs(v) > COORD_LIMIT for k, v in parsed.items() if k != "kind"):
        raise InputError("D1 source range")
    if parsed["kind"] == "repeat":
        pitch, phase = parsed["step"], parsed["phase"]
    else:
        if parsed["panel"] <= 0 or parsed["gap"] < 0:
            raise InputError("D29 source size")
        pitch = parsed["panel"] + parsed["gap"]
        phase = parsed["anchor"] + parsed["panel"] + parsed["gap"] // 2
    if pitch <= 0:
        raise InputError("D29 pitch")
    delta = parsed.get("stagger")
    if delta is not None and (delta == 0 or delta % pitch == 0):
        raise InputError("D10b zero or full-pitch stagger")
    rows = []
    for band in bands:
        b = _index(band)
        shift = (delta or 0) if b % 2 else 0
        for index in indices:
            k = _index(index)
            coordinate = phase + k * pitch + shift
            if not -COORD_LIMIT <= coordinate <= COORD_LIMIT:
                raise InputError("D1 query range")
            rows.append({"band": str(b), "index": str(k), "coordinate": coordinate})
    return rows


def example_cases():
    base = {"u": {"kind": "panel", "panel": 915, "gap": 2, "anchor": 0},
            "v": {"kind": "repeat", "step": 400, "phase": 0},
            "divisions": [7, 2], "cell": ["-1", "0"]}
    yield "915_plus_2_div7", deepcopy(base)
    for gap in (0, 2):
        c = deepcopy(base)
        c["u"] = {"kind": "panel", "panel": 1830, "gap": gap, "anchor": 0}
        c["divisions"][0] = 5
        yield "1830_plus_%s_div5" % gap, c
    odd = deepcopy(base)
    odd["u"] = {"kind": "panel", "panel": 914, "gap": 3, "anchor": 0}
    yield "odd_gap_floor", odd
    shifted = deepcopy(base)
    shifted["u"]["anchor"] = -916
    shifted["v"]["phase"] = -37
    shifted["cell"] = ["0", "-2"]
    shifted["offset"] = [17, 29]
    yield "nonzero_phase_and_translation", shifted


def self_test():
    cases = dict(example_cases())
    base = cases["915_plus_2_div7"]
    good = build(base)
    assert good["bounds"] == [-1, 0, 916, 400], "R14P_ORACLE_PANEL_BOUNDS"
    assert [row[2] for row in good["lines"] if row[0] == "u"] == [130, 261, 392, 523, 654, 785], "R14P_ORACLE_PANEL_LINES"
    assert build(cases["1830_plus_0_div5"])["lines"][0][2] == 366, "R14P_ORACLE_1830_5"
    assert build(cases["1830_plus_2_div5"])["code"] == "DIVISION_NOT_EXACT", "R14P_ORACLE_GAP_NOT_DROPPED"
    assert build(cases["odd_gap_floor"])["bounds"] == [-2, 0, 915, 400], "R14P_ORACLE_ODD_GAP"
    for name, case in cases.items():
        assert check(case, build(case)) == [], (name, "R14P_ORACLE_AGREEMENT")
    for axis in AXES:
        for delta, expected in ((0, "STAGGER_ZERO"), (1, "STAGGER_NOT_SUPPORTED")):
            case = deepcopy(base)
            case[axis]["stagger"] = delta
            actual = build(case)
            assert actual["code"] == expected and check(case, actual) == [], "R14P_ORACLE_STAGGER_REFUSAL"
    bands = [str(i) for i in range(-3, 4)]
    diag = phase_bands({"kind": "repeat", "phase": 0, "step": 1830, "stagger": 400}, ["0", "1"], bands)
    expected = [400, 2230, 0, 1830, 400, 2230, 0, 1830, 400, 2230, 0, 1830, 400, 2230]
    assert [row["coordinate"] for row in diag] == expected, "R14P_D10B_NEGATIVE_ODD_PHASE"
    negative = phase_bands({"kind": "panel", "anchor": 0, "panel": 914, "gap": 3, "stagger": -100}, ["-1"], bands)
    assert [row["coordinate"] for row in negative] == [-102, -2, -102, -2, -102, -2, -102], "R14P_D10B_NEGATIVE_DELTA"

    records = []
    for name, (case, wrong) in checker_mutation_cases().items():
        checks = [check(case, build(case)), check(case, wrong), check(case, build(case))]
        verdict = [int(bool(failures)) for failures in checks]
        assert verdict == [0, 1, 0], ("R14P_CHECKER_SENSITIVITY", name, checks)
        records.append({"mutation": name, "checker_verdict": verdict, "violation": checks[1]})
    malformed = []
    for name, wrong in malformed_result_cases(good):
        failures = check(base, wrong)
        assert failures, ("R14P_MALFORMED_RESULT_REJECTED", name)
        malformed.append({"case": name, "violations": failures})
    assert len(malformed) == 26, "R14P_MALFORMED_CASE_COUNT"
    return {"schema": "r14-panel-oracle-self-test/1", "examples": len(cases),
            "phase_rows": len(diag) + len(negative), "checker_mutations": records,
            "revision": "recovery-1", "malformed_results": malformed}


def malformed_result_cases(good):
    """JSON-output shape faults must yield violations, never a TypeError."""
    bounds = [None, False, True, 0, 1, "0", {}, [], [0], [0, 0], [0, 0, 0],
              [0, 0, 0, 0, 0], [True, 0, 916, 400], [0.0, 0, 916, 400]]
    lines = [None, True, 0, "", {}, [None], [True], [1], [["u", 0, 130]],
             [["u", 0, 130, 0, 400, 400]], [["u", 0, None, 0, 400]],
             [{"axis": "u", "segments": None}]]
    for field, values in (("bounds", bounds), ("lines", lines)):
        for index, value in enumerate(values):
            wrong = deepcopy(good)
            wrong[field] = value
            yield "%s_%02d" % (field, index + 1), wrong


def checker_mutation_cases():
    """Faulty output fixtures for independent CLI checks; no native mutation."""
    cases = dict(example_cases())
    base = cases["915_plus_2_div7"]
    good = build(base)
    mutated = {}
    wrong = deepcopy(good); wrong["lines"][0][2] += 1
    mutated["ONE_LINE_OFF_BY_ONE"] = (base, wrong)
    wrong = deepcopy(good); wrong["lines"][0][1] = 1
    mutated["WRONG_INNER_INDEX"] = (base, wrong)
    wrong = deepcopy(good); wrong["lines"].pop()
    mutated["DROP_LINE"] = (base, wrong)
    wrong = deepcopy(good); wrong["lines"].append(["u", 6, 916, 0, 400])
    mutated["INCLUDE_PARENT_EDGE"] = (base, wrong)
    wrong = deepcopy(good); wrong["lines"][0][4] -= 1
    mutated["SHORTEN_PARENT_SPAN"] = (base, wrong)
    wrong = deepcopy(good)
    wrong["bounds"][0] += 1; wrong["bounds"][2] += 1
    for line in wrong["lines"]:
        if line[0] == "u": line[2] += 1
        else: line[3] += 1; line[4] += 1
    mutated["CONSISTENT_BUT_WRONG_PARENT"] = (base, wrong)
    wrong = deepcopy(good); wrong["bounds"] = [0, 0, 915, 400]
    mutated["PANEL_INSTEAD_OF_PITCH"] = (base, wrong)
    odd = cases["odd_gap_floor"]; wrong = deepcopy(build(odd))
    wrong["bounds"][0] += 1; wrong["bounds"][2] += 1
    for line in wrong["lines"]:
        if line[0] == "u": line[2] += 1
        else: line[3] += 1; line[4] += 1
    mutated["ODD_GAP_ROUNDED_UP"] = (odd, wrong)
    inexact = cases["1830_plus_2_div5"]
    mutated["ROUND_NONINTEGRAL_DIVISION"] = (inexact, build(cases["1830_plus_0_div5"]))
    staggered = deepcopy(base); staggered["v"]["stagger"] = 1
    mutated["ALLOW_STAGGERED_RULE"] = (staggered, good)
    mutated["REJECT_VALID_NEGATIVE_CELL"] = (base, _rejected("QUERY_OVERFLOW"))
    return mutated


def scan_cases():
    """Explicit finite Cartesian families; no random sampling."""
    # All two-axis source kinds/small dimensions/gaps, both divisors and signed
    # neighbouring cells. This is NOT a sweep over all D1/int64 possibilities.
    axes = ([{"kind": "repeat", "step": size, "phase": 0} for size in range(1, 7)] +
            [{"kind": "panel", "panel": size, "gap": gap, "anchor": 0}
             for size, gap in product(range(1, 7), range(2))])
    for u, v, nu, nv, i, j in product(axes, axes, range(1, 5), range(1, 5), range(-1, 2), range(-1, 2)):
        yield "small", {"u": u, "v": v, "divisions": [nu, nv], "cell": [str(i), str(j)]}
    # Windows around the two physical dimensions, with nonzero origin and
    # negative cells. The v dimension stays explicit at 400/2 in this family.
    for center, gap, nu, anchor, i, displacement in product((915, 1830), range(5), range(1, 10), (-17, 0, 23), range(-1, 2), range(-5, 6)):
        yield "physical", {"u": {"kind": "panel", "panel": center + displacement, "gap": gap, "anchor": anchor},
                           "v": {"kind": "repeat", "step": 400, "phase": -37},
                           "divisions": [nu, 2], "cell": [str(i), "-1"]}
    base = dict(example_cases())["915_plus_2_div7"]
    for axis, delta in product(AXES, (-917, -400, -1, 0, 1, 400, 917)):
        case = deepcopy(base); case[axis]["stagger"] = delta
        yield "stagger_refusal", case
    both = deepcopy(base); both["u"]["stagger"] = 1; both["v"]["stagger"] = -1
    yield "stagger_refusal", both


def scan(jsonl=None):
    counts, families, failures, total = Counter(), Counter(), [], 0
    stream = Path(jsonl).open("w", encoding="utf-8", newline="\n") if jsonl else None
    try:
        for family, case in scan_cases():
            result = build(case)
            errors = check(case, result)
            total += 1
            families[family] += 1
            counts[result["code"] or "EXACT"] += 1
            if errors:
                failures.append({"ordinal": total, "input": case, "errors": errors})
            if stream:
                stream.write(json.dumps({"ordinal": total, "family": family, "input": case,
                                         "result": result, "violations": errors}, ensure_ascii=False,
                                        sort_keys=True, separators=(",", ":")) + "\n")
    finally:
        if stream:
            stream.close()
    return {"schema": "r14-panel-oracle-scan/1", "cases": total,
            "families": dict(sorted(families.items())), "outcomes": dict(sorted(counts.items())),
            "independent_failures": failures}


def replay_mutations(out=None):
    """Real --check processes; neither crashes nor internal booleans are kills."""
    if out is None:
        directory = Path(tempfile.mkdtemp(prefix="r14-oracle-mutations-"))
    else:
        directory = Path(out).resolve()
        directory.mkdir(parents=True, exist_ok=False)
    program = Path(__file__).resolve()
    records = []

    def save_json(path, value):
        path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")

    def output_text(value):
        return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else (value or "")

    for name, (case, wrong) in checker_mutation_cases().items():
        target = directory / name
        target.mkdir()
        case_path = target / "case.json"
        save_json(case_path, case)
        phases = []
        for phase, result, expected in (("baseline", build(case), 0),
                                        ("withdrawn", wrong, 1),
                                        ("restored", build(case), 0)):
            result_path = target / (phase + ".result.json")
            save_json(result_path, result)
            command = [sys.executable, "-B", str(program), "--check", str(case_path), str(result_path)]
            returncode, issue = None, None
            try:
                completed = subprocess.run(command, capture_output=True, text=True,
                                           encoding="utf-8", errors="replace", timeout=30)
                returncode, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
            except subprocess.TimeoutExpired as exc:
                stdout, stderr, issue = output_text(exc.stdout), output_text(exc.stderr), "timeout"
            except OSError as exc:
                stdout, stderr, issue = "", str(exc), "launch-error"
            (target / (phase + ".stdout.log")).write_text(stdout, encoding="utf-8")
            (target / (phase + ".stderr.log")).write_text(stderr, encoding="utf-8")
            try:
                response = json.loads(stdout)
            except (TypeError, ValueError):
                response = None
            valid_response = (isinstance(response, dict) and set(response) == {"violations"} and
                              isinstance(response["violations"], list) and
                              all(isinstance(item, str) for item in response["violations"]))
            expected_response = (valid_response and
                                 bool(response["violations"]) == (expected == 1))
            phase_record = {"phase": phase, "command": command, "exit_code": returncode,
                            "expected_exit_code": expected, "response": response,
                            "execution_error": issue,
                            "passed": (issue is None and returncode == expected and
                                       stderr == "" and expected_response)}
            save_json(target / (phase + ".process.json"), phase_record)
            phases.append(phase_record)
        record = {"mutation": name, "exit_codes": [phase["exit_code"] for phase in phases],
                  "passed": all(phase["passed"] for phase in phases), "phases": phases}
        save_json(target / "report.json", record)
        records.append(record)
    summary = {"schema": "r14-panel-oracle-process-mutations/1", "revision": "recovery-1",
               "kind": "oracle-output-mutations-not-product-source", "directory": str(directory),
               "source_sha256": hashlib.sha256(program.read_bytes()).hexdigest(),
               "process_count": sum(len(record["phases"]) for record in records),
               "passed": all(record["passed"] for record in records), "mutations": records}
    save_json(directory / "report.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--self-test", action="store_true")
    action.add_argument("--scan", action="store_true")
    action.add_argument("--input", type=Path)
    action.add_argument("--check", nargs=2, type=Path, metavar=("CASE", "RESULT"))
    action.add_argument("--mutations", action="store_true")
    parser.add_argument("--jsonl", type=Path, help="optional full scan rows; only with --scan")
    parser.add_argument("--out", type=Path, help="new directory for --mutations raw artifacts")
    args = parser.parse_args()
    if args.jsonl and not args.scan:
        parser.error("--jsonl requires --scan")
    if args.out and not args.mutations:
        parser.error("--out requires --mutations")
    if args.self_test:
        result = self_test()
    elif args.scan:
        result = scan(args.jsonl)
    elif args.mutations:
        result = replay_mutations(args.out)
    elif args.check:
        case, proposed = [json.loads(path.read_text(encoding="utf-8")) for path in args.check]
        violations = check(case, proposed)
        result = {"violations": violations}
    else:
        case = json.loads(args.input.read_text(encoding="utf-8"))
        result = build(case)
        violations = check(case, result)
        if violations:
            raise AssertionError(violations)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if args.mutations:
        return 0 if result["passed"] else 1
    return int(bool(result.get("independent_failures") or result.get("violations")))


if __name__ == "__main__":
    raise SystemExit(main())
