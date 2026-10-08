#!/usr/bin/env python3
"""CLI for the orthogonal-model/1 reference executor (Python standard library)."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

from modeling import (CAPABILITIES, PROFILE, ModelError, build_package,
                      canonical_bytes, strict_json_loads, verify_package)


def atomic_write(path, data):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".model-", delete=False) as stream:
            temporary = stream.name
            stream.write(data)
        os.replace(temporary, destination)
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)


def obj_bytes(package):
    """Exact integer XYZ geometry in millimetres; the JSON package retains semantics."""
    objects = package["derived"]["objects"]
    spaces = set()
    for item in objects:
        profile = item.get("section_profile", {})
        spaces.add(("local", profile["run_id"]) if profile.get("coordinate_space") == "local" else ("world",))
    if len(spaces) > 1:
        raise ModelError("UNSUPPORTED", "OBJ_COORDINATE_SPACE", "I48", "OBJ cannot combine independent local and world frames; export the JSON package or select one frame")
    coordinate = ("# coordinates: local (u,v,w) of profile-run " + str(next(iter(spaces))[1]) + "; no world position or world up"
                  if spaces and next(iter(spaces))[0] == "local" else "# coordinates: world XYZ; up: +Z")
    lines = ["# geometry-axiom orthogonal-model/1", "# units: millimetres; right handed", coordinate,
             "# Definitions, references and partial status are in the companion JSON package.",
             "# status: " + package["derived"]["status"]]
    offset = 1
    for index, item in enumerate(objects):
        if "section_profile" in item:
            profile = item["section_profile"]
            lines.append("# profile-run %s; member %s; kind %s; material-volume-mm3 %s" %
                         (profile["run_id"], profile["member_id"], profile["kind"], profile["material_volume_mm3"]))
        lines.append("o model_" + str(index))
        for xyz in item["vertices_mm"]:
            lines.append("v " + " ".join(str(n) for n in xyz))
        for triangle in item["triangles"]:
            lines.append("f " + " ".join(str(offset + n) for n in triangle))
        offset += len(item["vertices_mm"])
    return ("\n".join(lines) + "\n").encode("utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("capabilities", help="Print supported profile and runtime capabilities")
    build = commands.add_parser("build", help="Build {definitions, request} into a model package")
    build.add_argument("input", help="Input JSON file, or - for stdin")
    example = commands.add_parser("example", help="Build one committed acceptance example")
    example.add_argument("name", help="Case id, or list")
    verify = commands.add_parser("verify", help="Reconstruct and verify a model package")
    verify.add_argument("input", help="Package JSON file, or - for stdin")
    for command in (build, example, verify):
        command.add_argument("-o", "--output", help="Package output path; default stdout")
        command.add_argument("--obj", help="Also export exact millimetre OBJ geometry")
        command.add_argument("--max-cells", type=int, default=200000)
        command.add_argument("--base-executable", help="Path to a prebuilt authoritative C adapter")
    args = parser.parse_args(argv)
    try:
        if args.command == "capabilities":
            print(json.dumps({"profile": PROFILE, "capabilities": CAPABILITIES,
                              "executor": "C scene validation + Python exact integer modeling",
                              "default_max_cells": 200000}))
            return 0
        options = {"max_cells": args.max_cells, "base_executable": args.base_executable}
        if args.command == "example":
            vectors = strict_json_loads((Path(__file__).parent / "modeling-cases.json").read_bytes())["cases"]
            if args.name == "list":
                print("\n".join(item["id"] for item in vectors))
                return 0
            matches = [item for item in vectors if item["id"] == args.name]
            if not matches:
                raise ModelError("INVALID", "EXAMPLE", "R30", "Unknown example id")
            data = matches[0]
            if "executor_capabilities" in data:
                options["capabilities"] = data["executor_capabilities"]
        else:
            content = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
            data = strict_json_loads(content)
        if args.command == "verify":
            package = verify_package(data, **options)
        else:
            if not isinstance(data, dict) or "definitions" not in data or "request" not in data:
                raise ModelError("INVALID", "INPUT_SCHEMA", "D25", "Input must include definitions and request")
            if args.command == "build" and set(data) - {"definitions", "request", "presentation"}:
                raise ModelError("INVALID", "INPUT_SCHEMA", "D25", "Unknown input fields")
            package = build_package(data["definitions"], data["request"],
                                    presentation=data.get("presentation"), **options)
        payload = canonical_bytes(package) + b"\n"
        mesh = obj_bytes(package) if args.obj else None
        if args.output:
            atomic_write(args.output, payload)
        else:
            sys.stdout.buffer.write(payload)
        if args.obj:
            atomic_write(args.obj, mesh)
        return 0
    except ModelError as exc:
        sys.stderr.buffer.write(canonical_bytes(exc.as_dict()) + b"\n")
        return {"INVALID": 2, "INCOMPLETE": 3, "UNSUPPORTED": 4}.get(exc.status, 2)
    except (OSError, ValueError) as exc:
        sys.stderr.write(json.dumps({"status": "ERROR", "message": str(exc)}) + "\n")
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
