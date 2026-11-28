#!/usr/bin/env python3
"""Bounded X7 operation measurements using regenerated, verified fixtures.

Native .scene save-as is dump + UTF-8 write + flush + fsync. It is not a claim
about complete .gcanvas serialization or OS downloads. Those are measured by
the browser companion. F1 batch confirmation is explicitly the product's
whole-scene load-confirm; the current main R03 template cannot generate F1.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import time
import traceback

from x7_scenarios import (ROOT, SCHEMA, Dialogue, framing_preview, framing_confirm,
                          new_output_directory, read_file, require, sha, validate_references, write_json)


def statistics_ms(values):
    ordered = sorted(values)
    require(bool(ordered), "X7_MEASUREMENT_NOT_EMPTY")
    return {"samples": values, "count": len(values), "min_ms": min(values),
            "median_ms": statistics.median(values), "p95_nearest_rank_ms": ordered[math.ceil(len(values) * .95) - 1],
            "max_ms": max(values)}


def cpu_description():
    if Path("/proc/cpuinfo").is_file():
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor()


def validate_bundle(path):
    root = path.resolve().parent
    bundle = json.loads(path.read_bytes())
    require(bundle.get("schema") == SCHEMA, "X7_BUNDLE_SCHEMA")
    require([(c["key"], c["count"]) for c in bundle["cases"]] ==
            [("room53", 53), ("f1_111", 111), ("house500", 500)], "X7_THREE_REPRESENTATIVE_SCENES")
    for case in bundle["cases"]:
        for key in ("completedScene", "beforeScene", "expectedGeometry"):
            read_file(case[key], root)
    return bundle, root


def run_sample(case, fixture_root, out, iteration, bridge):
    final_bytes = read_file(case["completedScene"], fixture_root)
    before_bytes = read_file(case["beforeScene"], fixture_root)
    expected = json.loads(read_file(case["expectedGeometry"], fixture_root))
    final_path = fixture_root / case["completedScene"]["path"]
    before_path = fixture_root / case["beforeScene"]["path"]
    label = case["key"] + "-" + str(iteration)
    save_ms = None
    with Dialogue(out / "raw", label, bridge) as d:
        # Startup/reset are recorded, but excluded from the operation budget.
        d.command("reset")
        d.command("loadfile " + str(final_path), operation="native_load")
        dumped = d.command("dump", operation="bridge_dump")
        require(dumped["text"].encode() == final_bytes, "X7_LOAD_CANONICAL_BYTES", case["key"])
        objects = d.command("objects", operation="bridge_objects")
        require([row["id"] for row in objects["timbers"]] == [row["id"] for row in expected], "X7_OBJECT_QUERY_ALL_IDS")
        references = d.command("references", operation="bridge_references")
        validate_references(references, expected)
        references_path = out / (label + ".references.json")
        write_json(references_path, references)
        save_path = out / (label + ".saved.scene")
        started = time.perf_counter_ns()
        saved = d.command("dump")
        payload = saved["text"].encode("utf-8")
        with save_path.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        save_ms = (time.perf_counter_ns() - started) / 1e6
        require(payload == final_bytes and save_path.read_bytes() == final_bytes, "X7_NATIVE_SAVE_EXACT_BYTES")
        d.command("loadfile " + str(before_path))
        before_dump = d.command("dump")
        require(before_dump["text"].encode() == before_bytes, "X7_BEFORE_BATCH_CANONICAL_BYTES")
        if case["batchKind"] == "framing-template-confirm":
            pending = framing_preview(d, case["currentBoundary"], operation="framing_preview")
            require(len(pending["preview"]["members"]) == case["expectedAddedCount"], "X7_BATCH_HAS_ALL_MEMBERS")
            require(d.command("dump") == before_dump, "X7_PREVIEW_ZERO_WRITE")
            framing_confirm(d, pending, operation="framing_confirm")
        else:
            require(case["batchKind"] == "load-confirm" and case["templateAvailable"] is False,
                    "X7_F1_SCOPE_IS_IMPORT_NOT_TEMPLATE")
            pending = d.command("load-prepare " + str(final_path), operation="import_prepare")
            require(pending["final_scene"].encode() == final_bytes, "X7_F1_PREPARED_CANONICAL_BYTES")
            require(d.command("dump") == before_dump, "X7_IMPORT_PREVIEW_ZERO_WRITE")
            d.command("load-confirm " + str(pending["token"]), operation="import_confirm")
        require(d.command("dump")["text"].encode() == final_bytes, "X7_BATCH_EXACT_RESULT_BYTES")
        d.command("line undo", operation="undo")
        require(d.command("dump")["text"].encode() == before_bytes, "X7_UNDO_EXACT_ONE_BATCH")
        d.command("line redo", operation="redo")
        require(d.command("dump")["text"].encode() == final_bytes, "X7_REDO_EXACT_ONE_BATCH")
        validate_references(d.command("references"), expected)
    return {"iteration": iteration, "raw_prefix": "raw/" + label,
            "child_exit": d.process.returncode, "stderr_bytes": d.stderr_path.stat().st_size,
            "binary_sha256": d.binary_sha256, "rows": d.rows,
            "native_save_as_ms": save_ms, "references_path": str(references_path),
            "completed_scene_sha256": sha(final_bytes)}


def run(bundle_path, out, repeats, bridge=None, cases=None):
    bundle, fixture_root = validate_bundle(bundle_path)
    out = new_output_directory(out, "X7_NEW_BENCHMARK_OUTPUT")
    require(1 <= repeats <= 30, "X7_BOUNDED_REPEATS")
    report = {"schema": "x7-performance-report/1", "acceptance": False,
              "argv": sys.argv, "cwd": str(Path.cwd()), "platform": platform.platform(),
              "cpu": cpu_description(), "python": sys.version, "clock": "perf_counter_ns",
              "repeats": repeats, "bundle_sha256": sha(bundle_path.read_bytes()),
              "method": {"wire": "write+flush through complete JSON line; JSON parsing separately recorded",
                         "native_save_as": "dump + UTF-8 write + flush + fsync; not gcanvas",
                         "schedule": "real F4a module, all native hosts; startup/I/O/JSON parse excluded",
                         "cold": "first sample retained, no warmup sample removed",
                         "F1": "111 current members; whole-scene import-confirm, R03 unsupported"},
              "cases": []}
    try:
        for case in bundle["cases"]:
            if cases and case["key"] not in cases:
                continue
            row = {"key": case["key"], "count": case["count"], "roomCount": case["roomCount"],
                   "batchKind": case["batchKind"], "samples": [], "operations": {}}
            report["cases"].append(row)
            for iteration in range(repeats):
                sample = run_sample(case, fixture_root, out, iteration, bridge)
                row["samples"].append(sample)
                write_json(out / "partial-report.json", report)
                print("X7_NATIVE_SAMPLE", case["key"], iteration, "child_exit=0 stderr=0 all_bytes=PASS", flush=True)
            operations = sorted({item["operation"] for sample in row["samples"] for item in sample["rows"] if item["operation"]})
            for operation in operations:
                values = [item["wire_ms"] for sample in row["samples"] for item in sample["rows"] if item["operation"] == operation]
                require(len(values) == repeats, "X7_EXACT_OPERATION_SAMPLE_COUNT", operation)
                row["operations"][operation] = statistics_ms(values)
            row["operations"]["native_save_as"] = statistics_ms([sample["native_save_as_ms"] for sample in row["samples"]])
            node = shutil.which("node")
            require(node is not None, "X7_NODE_REQUIRED_FOR_REAL_SCHEDULE")
            schedule_path = out / (case["key"] + ".schedule.json")
            command = [node, str(ROOT / "tests/diagnostics/x7_schedule_benchmark.cjs"),
                       row["samples"][-1]["references_path"], str(repeats), str(schedule_path)]
            result = subprocess.run(command, capture_output=True, timeout=30)
            (out / (case["key"] + ".schedule.stdout")).write_bytes(result.stdout)
            (out / (case["key"] + ".schedule.stderr")).write_bytes(result.stderr)
            row["schedule_command"] = command
            row["schedule_exit"] = result.returncode
            require(result.returncode == 0 and not result.stderr, "X7_SCHEDULE_CHILD_SUCCESS", result.stderr.decode(errors="replace"))
            schedule = json.loads(schedule_path.read_bytes())
            require(schedule["count"] == case["count"], "X7_SCHEDULE_ALL_ROOM_MEMBERS")
            row["schedule"] = schedule
            row["operations"]["schedule_derive"] = statistics_ms([item["derive_ms"] for item in schedule["rows"]])
            row["operations"]["schedule_csv"] = statistics_ms([item["csv_ms"] for item in schedule["rows"]])
            print("X7_OPERATION_TIMINGS", case["key"], json.dumps({key: value["median_ms"] for key, value in row["operations"].items()}, sort_keys=True), flush=True)
        report["exit_code"] = 0
    except BaseException as error:
        report["exit_code"] = 1
        report["failure"] = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
        raise
    finally:
        write_json(out / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True, help="browser-bundle.json from x7_scenarios.py")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--bridge")
    parser.add_argument("--case", action="append", choices=["room53", "f1_111", "house500"])
    args = parser.parse_args()
    run(args.fixtures, args.out, args.repeats, args.bridge, args.case)


if __name__ == "__main__":
    main()
