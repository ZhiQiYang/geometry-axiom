#!/usr/bin/env python3
"""Check every X7 operation sample against a reviewed, explicit budget.

This verifies local measurement metadata and its raw artifacts. Hash equality
does not make these files trusted CI evidence. No costs, budgets, receipts or
missing samples are invented. The budget is a source document supplied after
baseline/P measurement, never a number inferred by this checker to obtain green.

Budget shape:
  {"schema":"x7-operation-budgets/1", "unit":"ms",
   "measurement_method": <the exact METHOD below>,
   "cases": {"room53": {"count":53,"roomCount":1,
     "batchKind":"framing-template-confirm",
     "operations":{"native_load":{"upper_ms":NUMBER,"basis":"evidence + margin"}, ...}}, ...}}

check_report(report, budget, report_dir) returns a small verdict or raises
BudgetFailure with a stable X7_BUDGET_* marker. The companion selftest fabricates
only labelled checker inputs; it is not a native performance receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys

METHOD = {
    "wire": "write+flush through complete JSON line; JSON parsing separately recorded",
    "native_save_as": "dump + UTF-8 write + flush + fsync; not gcanvas",
    "schedule": "real F4a module, all native hosts; startup/I/O/JSON parse excluded",
    "cold": "first sample retained, no warmup sample removed",
    "F1": "111 current members; whole-scene import-confirm, R03 unsupported",
}
CASE_SPECS = {
    "room53": (53, 1, "framing-template-confirm"),
    "f1_111": (111, 1, "load-confirm"),
    "house500": (500, 5, "framing-template-confirm"),
}
COMMON = {"native_load", "bridge_dump", "bridge_objects", "bridge_references",
          "native_save_as", "undo", "redo", "schedule_derive", "schedule_csv"}
COMMAND_HEADS = {"native_load": "loadfile", "bridge_dump": "dump", "bridge_objects": "objects",
                 "bridge_references": "references", "framing_preview": "framing-template-preview",
                 "framing_confirm": "framing-template-confirm", "import_prepare": "load-prepare",
                 "import_confirm": "load-confirm"}
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024


class BudgetFailure(AssertionError):
    def __init__(self, marker, detail=None):
        self.marker, self.detail = marker, detail
        super().__init__(marker + (": " + repr(detail) if detail is not None else ""))


def need(condition, marker, detail=None):
    if not condition:
        raise BudgetFailure(marker, detail)


def fields(value, names, marker):
    need(isinstance(value, dict) and set(value) == set(names), marker,
         sorted(value) if isinstance(value, dict) else type(value).__name__)


def integer(value, marker, minimum=0):
    need(type(value) is int and value >= minimum, marker, value)
    return value


def number(value, marker):
    # A JSON integer can exceed float range; reject it with the same named
    # marker as NaN/Infinity instead of leaking OverflowError from isfinite.
    try:
        finite = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        finite = False
    need(finite and value >= 0, marker, value)
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def hash_value(value, marker):
    need(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None, marker, value)
    return value


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, "X7_BUDGET_DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


def parse_json(data):
    def forbidden(value):
        raise BudgetFailure("X7_BUDGET_NONFINITE_JSON", value)
    try:
        return json.loads(data, object_pairs_hook=object_pairs, parse_constant=forbidden)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BudgetFailure("X7_BUDGET_JSON", str(error)) from error


def artifact(root, relative):
    need(isinstance(relative, str) and relative, "X7_BUDGET_ARTIFACT_PATH", relative)
    path = Path(relative)
    need(not path.is_absolute() and all(part not in ("", ".", "..") for part in relative.split("/")),
         "X7_BUDGET_ARTIFACT_PATH", relative)
    root = Path(root).resolve()
    cursor = root
    for part in path.parts:
        cursor = cursor / part
        need(not cursor.is_symlink(), "X7_BUDGET_ARTIFACT_SYMLINK", relative)
    need(cursor.resolve().is_relative_to(root) and cursor.is_file(), "X7_BUDGET_ARTIFACT_MISSING", relative)
    need(cursor.stat().st_size <= MAX_ARTIFACT_BYTES, "X7_BUDGET_ARTIFACT_SIZE", relative)
    return cursor.read_bytes()


def original_output_root(report):
    args = report.get("argv")
    need(isinstance(args, list) and all(isinstance(value, str) for value in args), "X7_BUDGET_ARGV")
    need(args.count("--out") == 1, "X7_BUDGET_OUTPUT_ARGUMENT")
    at = args.index("--out")
    need(at + 1 < len(args), "X7_BUDGET_OUTPUT_ARGUMENT")
    output = Path(args[at + 1])
    cwd = report.get("cwd")
    need(isinstance(cwd, str) and Path(cwd).is_absolute(), "X7_BUDGET_CWD")
    need(".." not in output.parts, "X7_BUDGET_OUTPUT_PATH", str(output))
    return output if output.is_absolute() else Path(cwd) / output


def recorded_path(value, original_root, expected_relative):
    need(isinstance(value, str), "X7_BUDGET_RECORDED_PATH", value)
    path = Path(value)
    need(".." not in path.parts and path.is_absolute(), "X7_BUDGET_RECORDED_PATH", value)
    need(path == original_root / expected_relative, "X7_BUDGET_RECORDED_PATH", value)


def expected_operations(case_key):
    return COMMON | ({"import_prepare", "import_confirm"} if case_key == "f1_111"
                     else {"framing_preview", "framing_confirm"})


def validate_budget(budget):
    fields(budget, {"schema", "unit", "measurement_method", "cases"}, "X7_BUDGET_SCHEMA")
    need(budget["schema"] == "x7-operation-budgets/1" and budget["unit"] == "ms", "X7_BUDGET_SCHEMA")
    need(budget["measurement_method"] == METHOD, "X7_BUDGET_MEASUREMENT_METHOD")
    need(isinstance(budget["cases"], dict) and set(budget["cases"]) == set(CASE_SPECS), "X7_BUDGET_CASES")
    for key, (count, rooms, batch) in CASE_SPECS.items():
        case = budget["cases"][key]
        fields(case, {"count", "roomCount", "batchKind", "operations"}, "X7_BUDGET_CASE_SCHEMA")
        need(type(case["count"]) is int and type(case["roomCount"]) is int and
             (case["count"], case["roomCount"], case["batchKind"]) == (count, rooms, batch), "X7_BUDGET_CASE_IDENTITY", key)
        need(isinstance(case["operations"], dict) and set(case["operations"]) == expected_operations(key), "X7_BUDGET_OPERATIONS", key)
        for operation, value in case["operations"].items():
            fields(value, {"upper_ms", "basis"}, "X7_BUDGET_OPERATION_SCHEMA")
            need(number(value["upper_ms"], "X7_BUDGET_LIMIT") > 0, "X7_BUDGET_LIMIT")
            need(isinstance(value["basis"], str) and bool(value["basis"].strip()), "X7_BUDGET_BASIS", (key, operation))


def checked_statistics(record, values, key, operation, limit):
    fields(record, {"samples", "count", "min_ms", "median_ms", "p95_nearest_rank_ms", "max_ms"}, "X7_BUDGET_STATISTICS_FIELDS")
    need(isinstance(record["samples"], list) and record["samples"] == values,
         "X7_BUDGET_SAMPLE_SOURCE", (key, operation))
    for sample in record["samples"]:
        number(sample, "X7_BUDGET_SAMPLE_VALUE")
    need(type(record["count"]) is int and record["count"] == len(values) and len(values) > 0,
         "X7_BUDGET_SAMPLE_COUNT", (key, operation))
    for index, value in enumerate(values):
        number(value, "X7_BUDGET_SAMPLE_VALUE")
        need(value <= limit, "X7_BUDGET_EXCEEDED", {"case": key, "operation": operation,
             "sample": index, "actual_ms": value, "upper_ms": limit})
    ordered = sorted(values)
    exact = {"min_ms": min(values), "median_ms": statistics.median(values),
             "p95_nearest_rank_ms": ordered[math.ceil(len(values) * .95) - 1], "max_ms": max(values)}
    for field, expected in exact.items():
        number(record[field], "X7_BUDGET_STATISTIC_VALUE")
        need(record[field] == expected, "X7_BUDGET_STATISTIC_RECOMPUTED", (key, operation, field))


def native_sample(sample, root, key, index, original_root, binary_hashes):
    prefix = f"raw/{key}-{index}"
    need(isinstance(sample, dict), "X7_BUDGET_SAMPLE_SCHEMA", (key, index))
    need(sample.get("iteration") == index and type(sample.get("iteration")) is int,
         "X7_BUDGET_SAMPLE_ORDER", (key, index))
    need(sample.get("raw_prefix") == prefix, "X7_BUDGET_RAW_PREFIX", sample.get("raw_prefix"))
    need(type(sample.get("child_exit")) is int and sample["child_exit"] == 0,
         "X7_BUDGET_CHILD_EXIT", (key, index))
    need(type(sample.get("stderr_bytes")) is int and sample["stderr_bytes"] == 0,
         "X7_BUDGET_STDERR", (key, index))
    need(artifact(root, prefix + ".stderr") == b"", "X7_BUDGET_RAW_STDERR", (key, index))
    raw_metrics = parse_json(artifact(root, prefix + ".metrics.json"))
    need(isinstance(raw_metrics, dict) and raw_metrics.get("schema") == "x7-dialogue/1" and raw_metrics.get("acceptance") is False,
         "X7_BUDGET_RAW_METADATA_SCHEMA")
    need(raw_metrics.get("label") == f"{key}-{index}" and raw_metrics.get("child_exit") == 0
         and type(raw_metrics.get("child_exit")) is int and raw_metrics.get("stderr_bytes") == 0
         and type(raw_metrics.get("stderr_bytes")) is int, "X7_BUDGET_RAW_CHILD_RESULT")
    binary_hash = hash_value(sample.get("binary_sha256"), "X7_BUDGET_BINARY_HASH")
    need(raw_metrics.get("binary_sha256") == binary_hash, "X7_BUDGET_RAW_BINARY_HASH")
    binary_hashes.add(binary_hash)
    need(isinstance(raw_metrics.get("command"), list) and len(raw_metrics["command"]) == 1
         and isinstance(raw_metrics["command"][0], str), "X7_BUDGET_NATIVE_COMMAND")
    rows = sample.get("rows")
    need(isinstance(rows, list) and bool(rows) and rows == raw_metrics.get("rows"), "X7_BUDGET_RAW_TIMINGS", (key, index))
    for row in raw_metrics["rows"]:
        need(isinstance(row, dict), "X7_BUDGET_RAW_ROW_SCHEMA")
        number(row.get("wire_ms"), "X7_BUDGET_RAW_TIMING_VALUE")
        number(row.get("json_parse_ms"), "X7_BUDGET_RAW_PARSE_VALUE")
    stdin = artifact(root, prefix + ".stdin")
    stdout = artifact(root, prefix + ".stdout")
    lines = stdout.splitlines(keepends=True)
    need(len(lines) == len(rows), "X7_BUDGET_RAW_REPLY_COUNT")
    commands = []
    observed = {}
    for row, raw in zip(rows, lines):
        fields(row, {"command", "operation", "wire_ms", "json_parse_ms", "reply_bytes",
                     "reply_sha256", "ok", "timeout_seconds"}, "X7_BUDGET_RAW_ROW_SCHEMA")
        command = row.get("command")
        need(isinstance(command, str) and "\n" not in command and "\r" not in command,
             "X7_BUDGET_NATIVE_COMMAND")
        commands.append((command + "\n").encode())
        need(raw.endswith(b"\n"), "X7_BUDGET_RAW_REPLY_COMPLETE")
        need(type(row.get("reply_bytes")) is int and row["reply_bytes"] == len(raw)
             and row.get("reply_sha256") == digest(raw), "X7_BUDGET_RAW_REPLY_HASH")
        reply = parse_json(raw)
        need(isinstance(reply, dict) and reply.get("ok") is True and row.get("ok") is True,
             "X7_BUDGET_NATIVE_OPERATION_FAILED")
        number(row.get("wire_ms"), "X7_BUDGET_RAW_TIMING_VALUE")
        number(row.get("json_parse_ms"), "X7_BUDGET_RAW_PARSE_VALUE")
        need(type(row.get("timeout_seconds")) in (int, float) and row["timeout_seconds"] == 60,
             "X7_BUDGET_COMMAND_DEADLINE")
        operation = row.get("operation")
        if operation is not None:
            need(isinstance(operation, str) and operation in expected_operations(key) - {"native_save_as", "schedule_derive", "schedule_csv"},
                 "X7_BUDGET_NATIVE_OPERATION_NAME", operation)
            need(operation not in observed, "X7_BUDGET_NATIVE_OPERATION_DUPLICATE", operation)
            need(command == "line " + operation if operation in ("undo", "redo")
                 else command.split(" ", 1)[0] == COMMAND_HEADS[operation],
                 "X7_BUDGET_MEASUREMENT_BOUNDARY", (operation, command))
            observed[operation] = row["wire_ms"]
    need(stdin == b"".join(commands), "X7_BUDGET_RAW_COMMANDS")
    expected = expected_operations(key) - {"native_save_as", "schedule_derive", "schedule_csv"}
    need(set(observed) == expected, "X7_BUDGET_NATIVE_OPERATION_MISSING", key)
    observed["native_save_as"] = number(sample.get("native_save_as_ms"), "X7_BUDGET_SAVE_VALUE")
    scene_hash = hash_value(sample.get("completed_scene_sha256"), "X7_BUDGET_SCENE_HASH")
    need(digest(artifact(root, f"{key}-{index}.saved.scene")) == scene_hash, "X7_BUDGET_SAVED_SCENE_BYTES")
    references_name = f"{key}-{index}.references.json"
    recorded_path(sample.get("references_path"), original_root, references_name)
    references = parse_json(artifact(root, references_name))
    need(isinstance(references, dict) and references.get("ok") is True and isinstance(references.get("timbers"), list)
         and len(references["timbers"]) == CASE_SPECS[key][0], "X7_BUDGET_REFERENCES_COUNT")
    reference_replies = [parse_json(raw) for row, raw in zip(rows, lines) if row["operation"] == "bridge_references"]
    need(reference_replies == [references], "X7_BUDGET_REFERENCES_RAW_SOURCE")
    return observed


def schedule_samples(case, root, key, repeats, original_root):
    need(type(case.get("schedule_exit")) is int and case["schedule_exit"] == 0,
         "X7_BUDGET_SCHEDULE_EXIT")
    need(artifact(root, key + ".schedule.stderr") == b"", "X7_BUDGET_SCHEDULE_STDERR")
    data = artifact(root, key + ".schedule.json")
    schedule = parse_json(data)
    need(schedule == case.get("schedule") and parse_json(artifact(root, key + ".schedule.stdout")) == schedule,
         "X7_BUDGET_SCHEDULE_RAW_SOURCE")
    need(isinstance(schedule, dict) and schedule.get("schema") == "x7-schedule-measurement/1" and schedule.get("acceptance") is False,
         "X7_BUDGET_SCHEDULE_SCHEMA")
    need(type(schedule.get("count")) is int and schedule["count"] == CASE_SPECS[key][0]
         and type(schedule.get("surfaces")) is int and schedule["surfaces"] == CASE_SPECS[key][1],
         "X7_BUDGET_SCHEDULE_SCOPE")
    command = case.get("schedule_command")
    need(isinstance(command, list) and len(command) == 5 and all(isinstance(v, str) for v in command),
         "X7_BUDGET_SCHEDULE_COMMAND")
    need(Path(command[1]).as_posix().endswith("/tests/diagnostics/x7_schedule_benchmark.cjs")
         and command[3] == str(repeats), "X7_BUDGET_SCHEDULE_COMMAND")
    references_name = f"{key}-{repeats - 1}.references.json"
    recorded_path(command[2], original_root, references_name)
    recorded_path(command[4], original_root, key + ".schedule.json")
    need(schedule.get("references_sha256") == digest(artifact(root, references_name)), "X7_BUDGET_SCHEDULE_REFERENCE_HASH")
    csv = artifact(root, key + ".schedule.json.csv-array.json")
    need(type(schedule.get("csv_bytes")) is int and schedule["csv_bytes"] == len(csv)
         and schedule.get("csv_sha256") == digest(csv), "X7_BUDGET_SCHEDULE_CSV_BYTES")
    rows = schedule.get("rows")
    need(isinstance(rows, list) and len(rows) == repeats, "X7_BUDGET_SCHEDULE_SAMPLE_COUNT")
    for index, row in enumerate(rows):
        fields(row, {"iteration", "derive_ms", "csv_ms", "cold_module_sample"}, "X7_BUDGET_SCHEDULE_ROW")
        need(type(row["iteration"]) is int and row["iteration"] == index
             and row["cold_module_sample"] is (index == 0), "X7_BUDGET_SCHEDULE_SAMPLE_ORDER")
        number(row["derive_ms"], "X7_BUDGET_SCHEDULE_SAMPLE_VALUE")
        number(row["csv_ms"], "X7_BUDGET_SCHEDULE_SAMPLE_VALUE")
    return {"schedule_derive": [row["derive_ms"] for row in rows], "schedule_csv": [row["csv_ms"] for row in rows]}


def check_report(report, budget, report_dir):
    validate_budget(budget)
    need(isinstance(report, dict) and report.get("schema") == "x7-performance-report/1"
         and report.get("acceptance") is False, "X7_BUDGET_REPORT_SCHEMA")
    need(type(report.get("exit_code")) is int and report["exit_code"] == 0 and "failure" not in report,
         "X7_BUDGET_REPORT_FAILURE")
    need(report.get("method") == METHOD and report.get("clock") == "perf_counter_ns",
         "X7_BUDGET_MEASUREMENT_METHOD")
    repeats = integer(report.get("repeats"), "X7_BUDGET_REPEATS", 1)
    need(repeats <= 30, "X7_BUDGET_REPEATS")
    original_root = original_output_root(report)
    cases = report.get("cases")
    need(isinstance(cases, list) and len(cases) == 3 and all(isinstance(case, dict) for case in cases)
         and [case.get("key") for case in cases] == list(CASE_SPECS),
         "X7_BUDGET_REPORT_CASES")
    binary_hashes, results = set(), []
    for case in cases:
        key = case["key"]
        count, rooms, batch = CASE_SPECS[key]
        need(type(case.get("count")) is int and type(case.get("roomCount")) is int and
             (case["count"], case["roomCount"], case.get("batchKind")) == (count, rooms, batch),
             "X7_BUDGET_REPORT_CASE_IDENTITY", key)
        samples = case.get("samples")
        need(isinstance(samples, list) and len(samples) == repeats, "X7_BUDGET_REPORT_SAMPLE_COUNT", key)
        observed = [native_sample(sample, report_dir, key, index, original_root, binary_hashes)
                    for index, sample in enumerate(samples)]
        values = {operation: [sample[operation] for sample in observed] for operation in observed[0]}
        values.update(schedule_samples(case, report_dir, key, repeats, original_root))
        operations = case.get("operations")
        need(isinstance(operations, dict) and set(operations) == expected_operations(key),
             "X7_BUDGET_REPORT_OPERATIONS", key)
        for operation in sorted(values):
            limit = budget["cases"][key]["operations"][operation]["upper_ms"]
            checked_statistics(operations[operation], values[operation], key, operation, limit)
            results.append({"case": key, "operation": operation, "samples": repeats,
                            "max_ms": max(values[operation]), "upper_ms": limit})
    need(len(binary_hashes) == 1, "X7_BUDGET_ONE_BINARY_PER_REPORT", sorted(binary_hashes))
    return {"schema": "x7-budget-verdict/1", "acceptance": False, "ok": True,
            "scope": "Local measurement metadata/raw consistency and every-sample budget; not a trusted CI receipt.",
            "binary_sha256": next(iter(binary_hashes)), "checks": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--budget", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = check_report(parse_json(args.report.read_bytes()), parse_json(args.budget.read_bytes()), args.report.parent)
        code = 0
    except BudgetFailure as error:
        result = {"schema": "x7-budget-verdict/1", "acceptance": False, "ok": False,
                  "marker": error.marker, "detail": safe_detail(error.detail)}
        code = 1
    except OSError as error:
        result = {"schema": "x7-budget-verdict/1", "acceptance": False, "ok": False,
                  "marker": "X7_BUDGET_IO", "detail": str(error)}
        code = 1
    data = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.out:
        # A verdict must not overwrite the measurements it claims to inspect.
        with args.out.open("x", encoding="utf-8") as handle:
            handle.write(data)
    print(data, end="")
    return code


def safe_detail(value):
    """Keep a failure machine-readable even when its offending value is NaN."""
    if type(value) is float and not math.isfinite(value):
        return repr(value)
    if isinstance(value, dict):
        return {str(key): safe_detail(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [safe_detail(item) for item in value]
    return value


if __name__ == "__main__":
    sys.exit(main())
