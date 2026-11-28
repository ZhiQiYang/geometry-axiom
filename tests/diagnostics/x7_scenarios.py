#!/usr/bin/env python3
"""Regenerate X7's 53/111/500-member scenes through the actual product.

All large files go to --out, never to the repository. F1 is the real concave,
holed oracle room, translated by the existing core-probe generator into public
DSL and accepted by the product loader. Main does not have an F1 R03 generator.
The 500-member house uses three complete F1 rooms plus two complete rectangles;
no generated frame is truncated to hit the requested population.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge

SCHEMA = "x7-large-scenes/1"
POLICY = "3641dec4060cfcf062e2f1d55f341ecb5ae5023da4a4d8a3aba2c3c4110b6d58"
TEMPLATE = {"id": "flat-ceiling", "version": 2, "policyFingerprint": POLICY}
PARAMETERS = {"panelWidth": 915, "panelLength": 1830, "gap": 2,
              "timberWidth": 27, "timberDepth": 33, "maxSecondarySpacing": 367}
SOURCES = {"panel": {"id": "x7-panel", "version": 1},
           "threshold": {"parameterId": 90, "fieldId": 1}}
ORACLE_PARAMETERS = {"P": 915, "L": 1830, "gap": 2, "w": 27, "M": 367,
                     "X": 8, "min_piece": 27}


def require(condition, marker, detail=None):
    if not condition:
        raise AssertionError(marker + (": " + repr(detail) if detail is not None else ""))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value, *, exclusive=False):
    with path.open("x" if exclusive else "w", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def new_output_directory(path, marker):
    path = Path(path)
    require(not path.is_symlink() and ".." not in path.parts, marker, str(path))
    path = path.resolve()
    require(not path.exists() or path.is_dir(), marker, str(path))
    path.mkdir(parents=True, exist_ok=True)
    # A failed run's raw files remain evidence; retry with a different output.
    require(not any(path.iterdir()), marker, str(path))
    return path


def file_record(path, directory):
    data = path.read_bytes()
    return {"path": path.relative_to(directory).as_posix(), "bytes": len(data), "sha256": sha(data)}


def read_file(record, directory):
    require(isinstance(record, dict) and set(record) == {"path", "bytes", "sha256"}, "X7_ARTIFACT_FIELDS")
    relative = record["path"]
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute()
            and all(part not in ("", ".", "..") for part in relative.split("/")), "X7_ARTIFACT_PATH")
    require(type(record["bytes"]) is int and 0 <= record["bytes"] <= 64 * 1024 * 1024
            and isinstance(record["sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", record["sha256"]),
            "X7_ARTIFACT_METADATA")
    directory = Path(directory).resolve()
    path = directory
    for part in Path(relative).parts:
        path = path / part
        require(not path.is_symlink(), "X7_ARTIFACT_PATH")
    require(path.resolve().is_relative_to(directory) and path.is_file(), "X7_ARTIFACT_PATH")
    require(path.stat().st_size == record["bytes"], "X7_ARTIFACT_BYTES", record)
    data = path.read_bytes()
    require(len(data) == record["bytes"] and sha(data) == record["sha256"], "X7_ARTIFACT_BYTES", record)
    return data


class Dialogue:
    """One real child, bounded commands, raw stdin/stdout/stderr preserved.

    wire_ms measures write+flush through the complete JSON line. It includes
    native execution and pipe transfer, but excludes JSON decoding and log I/O.
    json_parse_ms is recorded separately. A timeout or child failure is never
    an accepted timing sample.
    """
    def __init__(self, directory, label, bridge=None, timeout=60):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        require(isinstance(label, str) and re.fullmatch(r"[A-Za-z0-9_-]+", label), "X7_RAW_LABEL")
        require(not any(self.directory.glob(label + ".*")), "X7_NEW_RAW_PREFIX", label)
        self.label, self.timeout = label, timeout
        self.rows, self.counter, self.closed = [], 0, False
        self.stderr_path = self.directory / (label + ".stderr")
        self.stdin_path = self.directory / (label + ".stdin")
        self.stdout_path = self.directory / (label + ".stdout")
        self.stderr = self.stderr_path.open("xb")
        self.stdin_log = self.stdin_path.open("xb")
        self.stdout_log = self.stdout_path.open("xb")
        self.exe = _bridge._checked_explicit(bridge) if bridge else _bridge.find_bridge()
        self.binary_sha256 = sha(Path(self.exe).read_bytes())
        self.stack_bytes = None
        if os.name != "nt":
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            # Same pre-existing 16 MiB prerequisite as the R03 native harness.
            needed = 16 * 1024 * 1024
            if soft != resource.RLIM_INFINITY and soft < needed:
                require(hard == resource.RLIM_INFINITY or hard >= needed, "X7_STACK_ENVIRONMENT")
                resource.setrlimit(resource.RLIMIT_STACK, (needed, hard))
            self.stack_bytes = resource.getrlimit(resource.RLIMIT_STACK)[0]
        self.process = subprocess.Popen([self.exe], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self.stderr)

    def command(self, command, *, operation=None, expect_ok=True):
        require(isinstance(command, str) and "\n" not in command and "\r" not in command,
                "X7_ONE_COMMAND_PER_LINE")
        payload = (command + "\n").encode("utf-8")
        self.stdin_log.write(payload)
        expired = threading.Event()
        def expire():
            expired.set()
            if self.process.poll() is None:
                self.process.kill()
        timer = threading.Timer(self.timeout, expire)
        timer.daemon = True
        timer.start()
        started = time.perf_counter_ns()
        try:
            self.process.stdin.write(payload)
            self.process.stdin.flush()
            raw = self.process.stdout.readline()
            elapsed = time.perf_counter_ns() - started
        finally:
            timer.cancel()
            timer.join()
        self.stdout_log.write(raw)
        require(not expired.is_set(), "X7_COMMAND_TIMEOUT", command)
        require(raw.endswith(b"\n"), "X7_CHILD_CLOSED", command)
        parse_started = time.perf_counter_ns()
        reply = json.loads(raw)
        parse_ns = time.perf_counter_ns() - parse_started
        row = {"command": command, "operation": operation, "wire_ms": elapsed / 1e6,
               "json_parse_ms": parse_ns / 1e6, "reply_bytes": len(raw),
               "reply_sha256": sha(raw), "ok": reply.get("ok"),
               "timeout_seconds": self.timeout}
        self.rows.append(row)
        if expect_ok:
            require(reply.get("ok") is True, "X7_PRODUCT_COMMAND_ACCEPTED", {"command": command, "reply": reply})
        return reply

    def packet(self, command, value, **kwargs):
        self.counter += 1
        path = self.directory / (self.label + f".packet-{self.counter}.json")
        write_json(path, value, exclusive=True)
        return self.command(command + " " + str(path), **kwargs)

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.process.stdin.close()
            self.process.wait(timeout=10)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            self.process.kill()
            self.process.wait(timeout=10)
        finally:
            self.process.stdout.close()
            self.stderr.close()
            self.stdin_log.close()
            self.stdout_log.close()
        receipt = {"schema": "x7-dialogue/1", "acceptance": False, "label": self.label,
                   "command": [self.exe], "binary_sha256": self.binary_sha256,
                   "stack_bytes": self.stack_bytes, "child_exit": self.process.returncode,
                   "stderr_bytes": self.stderr_path.stat().st_size, "rows": self.rows}
        write_json(self.directory / (self.label + ".metrics.json"), receipt, exclusive=True)
        require(self.process.returncode == 0, "X7_CHILD_EXIT_ZERO", receipt)
        require(self.stderr_path.stat().st_size == 0, "X7_STDERR_EMPTY", self.stderr_path.read_text(errors="replace"))

    def __enter__(self):
        return self

    def __exit__(self, kind, value, tb):
        self.close()
        return False


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def f1_definition():
    probe = module(ROOT / "geometry-core/framing-template/core-probe/gen_scenes.py", "x7_core_probe")
    golden = probe.load_golden()
    golden["rooms"] = {"F1客廳": golden["rooms"]["F1客廳"]}
    built = probe.build(golden)
    require(not built.disagreements, "X7_F1_EXISTING_GENERATOR_AGREEMENT", built.disagreements)
    counts = [len(scene.members) for scene in built.scenes]
    require(counts == [95, 97, 96, 98, 108, 110, 109, 111], "X7_CURRENT_F1_EIGHT_LAYOUTS", counts)
    scene = next(scene for scene in built.scenes if scene.layout == 7)
    probe.audit_scene(scene.text)
    lines = [line for line in scene.text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    return scene, lines, counts


def f1_copy(lines, surface, grid, offset, x):
    """Only rename DSL identities and translate the placement frame.

    Local outline, hole, grid values, anchors, selectors and member dimensions
    are preserved. Native geometry is later compared to the original golden.
    """
    result = []
    for line in lines:
        words = line.split()
        if words[0] == "surface":
            require(words[2:6] == ["origin", "0", "0", "2500"], "X7_F1_FRAME_INPUT")
            words[1], words[3] = str(surface), str(x)
        elif words[0] == "grid":
            words[1], words[3] = str(grid), str(surface)
        elif words[0] == "timber":
            words[1] = str(int(words[1]) + offset)
        elif words[0] == "place":
            words[1], words[3] = str(int(words[1]) + offset), str(surface)
            if "grid" in words:
                words[words.index("grid") + 1] = str(grid)
            words = [re.sub(r"^t(\d+)$", lambda m: "t" + str(int(m.group(1)) + offset), word) for word in words]
        else:
            raise AssertionError("X7_F1_UNEXPECTED_DSL: " + line)
        result.append(" ".join(words))
    return "\n".join(result) + "\n"


def seed_sources(dialogue):
    revision = dialogue.command("engineering-read")["revision"]
    preview = dialogue.packet("engineering-preview", {
        "schema": "engineering-transaction/1", "expectedRevision": revision,
        "operations": [
            {"op": "publish-material", "value": {"id": "x7-panel", "version": 1,
                "kind": "panel", "name": "X7 明選 915×1830×6", "width": 915, "length": 1830, "thickness": "6"}},
            {"op": "put-parameter", "value": {"id": 90, "name": "X7 承接", "fields": [
                {"id": 1, "name": "X", "type": "dimension", "input": "8"}]}}]})
    require(preview["preview"]["valid"], "X7_SOURCE_PREVIEW_VALID")
    dialogue.command("engineering-confirm " + str(preview["preview"]["token"]))


def framing_preview(dialogue, boundary, *, operation=None, expect_ok=True):
    read = dialogue.packet("framing-template-read", {
        "schema": "framing-template-read/2", "boundaryId": boundary, "template": TEMPLATE})
    return dialogue.packet("framing-template-preview", {
        "schema": "framing-template-generate/1", "expectedRevision": read["revision"],
        "contextKey": read["contextKey"], "definitionFingerprint": read["definitionFingerprint"],
        "boundaryId": boundary, "on": boundary, "template": TEMPLATE,
        "parameters": PARAMETERS, "sources": SOURCES,
        "layout": {"corner": "min-min", "lengthAlong": "v"},
        "material": {"boundary": "rc", "timber": "literal"}}, operation=operation, expect_ok=expect_ok)


def framing_confirm(dialogue, preview, *, operation=None):
    require(preview["preview"]["valid"], "X7_FRAMING_VALID")
    return dialogue.command("framing-template-confirm " + str(preview["preview"]["token"]) + " " + preview["ownerKey"], operation=operation)


def rectangle_oracle(width, height):
    oracle = module(ROOT / "geometry-core/framing-template/oracle/framing_oracle.py", "x7_independent_framing_oracle")
    room = {"outer": [[0, 0], [width, 0], [width, height], [0, height]]}
    result = oracle.build(room, {"A": "x", "a_start": "min", "b_start": "min"}, ORACLE_PARAMETERS)
    require(not result["conflicts"] and not result["core_limits"], "X7_ORACLE_ACCEPTS_FULL_FRAME")
    require(oracle.check(result, ORACLE_PARAMETERS) == [], "X7_INDEPENDENT_ORACLE_CHECK")
    return result


def validate_preview(preview, width, height, count):
    expected = rectangle_oracle(width, height)
    rows = [(r["kind"] + (":" + r["role"] if r["kind"] == "secondary" else ""), tuple(r["rect"]))
            for r in expected["timbers"]]
    actual = [(r["kind"], tuple(r["rect"])) for r in preview["preview"]["members"]]
    require(len(rows) == count, "X7_COMPLETE_RECTANGLE_COUNT", len(rows))
    require(sorted(rows) == sorted(actual), "X7_EVERY_RECTANGLE_MEMBER_EQUALS_ORACLE")
    require(preview["preview"]["supportComplete"] is True, "X7_NATIVE_SUPPORT_COMPLETE")
    return expected


def expected_f1(scene, surface, offset, x):
    return [{"id": m.id + offset, "surface": surface, "role": m.role,
             "bounds": [m.rect[0] + x, m.rect[1], 2500, m.rect[2] + x, m.rect[3], 2533],
             "length": max(m.rect[2] - m.rect[0], m.rect[3] - m.rect[1])} for m in scene.members]


def expected_rectangle(oracle, preview, x, references, existing_ids):
    # Preview handles are intentionally not allocated IDs. Geometry comes from
    # the independent oracle; only the committed product owns ID allocation.
    lookup = {(m["kind"] + (":" + m["role"] if m["kind"] == "secondary" else ""), tuple(m["rect"])): m for m in oracle["timbers"]}
    rows = []
    committed = [row for row in references["timbers"] if row["id"] not in existing_ids]
    require(len(committed) == len(preview["preview"]["members"]), "X7_ALL_AND_ONLY_NEW_MEMBERS")
    for row, actual in zip(preview["preview"]["members"], committed):
        expected = lookup[(row["kind"], tuple(row["rect"]))]
        rect = expected["rect"]
        role = "boundary" if expected["kind"] == "boundary" else "secondary" if expected["kind"] == "secondary" else "primary"
        rows.append({"id": actual["id"], "surface": row["geometry"]["surface"], "role": role,
                     "bounds": [rect[0] + x, rect[1], 2506, rect[2] + x, rect[3], 2539],
                     "length": max(rect[2] - rect[0], rect[3] - rect[1])})
    return rows


def validate_references(references, expected):
    require(references.get("ok") is True, "X7_REFERENCES_ACCEPTED")
    actual = {row["id"]: row for row in references["timbers"]}
    wanted = {row["id"]: row for row in expected}
    require(len(actual) == len(references["timbers"]) == len(wanted), "X7_MEMBER_IDS_UNIQUE")
    require(set(actual) == set(wanted), "X7_EVERY_MEMBER_ID")
    boxes = []
    for identifier, target in wanted.items():
        row = actual[identifier]
        geometry = row["geometry"]
        require(row["role"] == target["role"], "X7_MEMBER_ROLE", identifier)
        require((geometry["A"], geometry["B"], geometry["length"], geometry["surface"], geometry["side"]) ==
                (27, 33, target["length"], target["surface"], "+n"), "X7_MEMBER_DIMENSIONS_AND_HOST", identifier)
        origin, axes = geometry["origin"], geometry["axes"]
        vertices = [[origin[d] + i * geometry["length"] * axes[0][d] + j * 27 * axes[1][d] + k * 33 * axes[2][d]
                     for d in range(3)] for i in (0, 1) for j in (0, 1) for k in (0, 1)]
        box = [min(p[d] for p in vertices) for d in range(3)] + [max(p[d] for p in vertices) for d in range(3)]
        require(box == target["bounds"], "X7_EIGHT_VERTICES_MATCH_INDEPENDENT_GEOMETRY", {"id": identifier, "actual": box, "expected": target["bounds"]})
        boxes.append((identifier, box))
    for index, (left_id, left) in enumerate(boxes):
        for right_id, right in boxes[index + 1:]:
            require(not all(left[d] < right[d + 3] and right[d] < left[d + 3] for d in range(3)),
                    "X7_NO_SOLID_OVERLAP", (left_id, right_id))


def save_scene(dialogue, path):
    text = dialogue.command("dump")["text"]
    path.write_bytes(text.encode("utf-8"))
    return text


def build_all(out, bridge=None):
    out = new_output_directory(out, "X7_NEW_OUTPUT_DIRECTORY")
    probe, f1_lines, counts = f1_definition()
    cases = []
    for key, count in (("room53", 53), ("f1_111", 111), ("house500", 500)):
        expected, rooms = [], []
        before = out / (key + ".before.scene")
        complete = out / (key + ".scene")
        with Dialogue(out / "generation-raw", key, bridge) as d:
            d.command("reset")
            if key == "f1_111":
                save_scene(d, before)
                source = out / (key + ".source.scene")
                source.write_text(f1_copy(f1_lines, 1, 1, 0, 0), encoding="utf-8")
                d.command("loadfile " + str(source))
                expected = expected_f1(probe, 1, 0, 0)
                rooms = [{"boundaryId": 1, "x": 0, "width": 5000, "height": 4800, "kind": "F1-concave-with-hole", "count": 111}]
                boundary, added, kind = 1, 111, "load-confirm"
            else:
                if key == "house500":
                    source = out / (key + ".source.scene")
                    source.write_text("".join(f1_copy(f1_lines, i + 1, i + 1, 111 * i, 7000 * i) for i in range(3)), encoding="utf-8")
                    d.command("loadfile " + str(source))
                    for i in range(3):
                        expected += expected_f1(probe, i + 1, 111 * i, 7000 * i)
                        rooms.append({"boundaryId": i + 1, "x": 7000 * i, "width": 5000, "height": 4800,
                                      "kind": "F1-concave-with-hole", "count": 111})
                    sizes = [(21000, 7000, 3301, 83), (30000, 8000, 3000, 84)]
                else:
                    sizes = [(0, 3740, 3301, 53)]
                seed_sources(d)
                identifiers = d.command("newid " + str(len(sizes)))["surfaces"]
                require(len(set(identifiers)) == len(sizes), "X7_BRIDGE_ALLOCATED_SURFACE_IDS")
                for sid, (x, width, height, members) in zip(identifiers, sizes):
                    d.command(f"line surface {sid} origin {x} 0 2500 u +x v +y outline 0,0 {width},0 {width},{height} 0,{height}")
                    rooms.append({"boundaryId": sid, "x": x, "width": width, "height": height, "kind": "rectangle", "count": members})
                for index, (sid, (x, width, height, members)) in enumerate(zip(identifiers, sizes)):
                    if index == len(sizes) - 1:
                        save_scene(d, before)
                    pending = framing_preview(d, sid)
                    oracle = validate_preview(pending, width, height, members)
                    framing_confirm(d, pending)
                    expected += expected_rectangle(oracle, pending, x, d.command("references"), {row["id"] for row in expected})
                boundary, added, kind = identifiers[-1], sizes[-1][-1], "framing-template-confirm"
            require(len(expected) == count, "X7_SCENE_FULL_MEMBER_COUNT")
            validate_references(d.command("references"), expected)
            completed_text = save_scene(d, complete)
            # Cold load is not allowed to invoke a generator or alter any bytes.
            d.command("loadfile " + str(complete))
            require(d.command("dump")["text"] == completed_text, "X7_CANONICAL_COLD_ROUNDTRIP_BYTES")
            validate_references(d.command("references"), expected)
            if key == "f1_111":
                seed_sources(d)
                refusal = framing_preview(d, 1, expect_ok=False)
                require(refusal.get("ok") is False and refusal.get("code") == "UNSUPPORTED_SCOPE", "X7_F1_TEMPLATE_UNAVAILABLE_HONESTLY", refusal)
        expected_path = out / (key + ".expected.json")
        write_json(expected_path, sorted(expected, key=lambda row: row["id"]))
        cases.append({"key": key, "count": count, "roomCount": len(rooms), "currentBoundary": boundary,
                      "expectedAddedCount": added, "batchKind": kind, "templateAvailable": kind == "framing-template-confirm",
                      "completedScene": file_record(complete, out), "beforeScene": file_record(before, out),
                      "expectedGeometry": file_record(expected_path, out), "rooms": rooms})
        print(f"X7_GENERATED {key} count={count} rooms={len(rooms)} independent_geometry=PASS cold_bytes=PASS", flush=True)
    bundle = {"schema": SCHEMA, "acceptance": False, "template": TEMPLATE, "parameters": PARAMETERS,
              "sources": SOURCES, "currentF1LayoutCounts": counts, "cases": cases,
              "scope": {"F1": "Existing oracle to public DSL; current main R03 template refuses concave/holed F1.",
                        "save": "Canonical native .scene only; complete .gcanvas attachments are a separate browser measurement."}}
    write_json(out / "browser-bundle.json", bundle)
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--bridge")
    args = parser.parse_args()
    build_all(args.out, args.bridge)


if __name__ == "__main__":
    main()
