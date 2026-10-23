#!/usr/bin/env python3
"""Freeze seven legacy scenes using an explicitly supplied unmodified bridge.

This script never builds, imports repository test helpers, discovers a bridge,
edits the source checkout, or copies fixtures into it.  Its output directory is
an execution artifact: receipts are written only for commands actually run.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import selectors
import shutil
import subprocess
import sys
import time
import traceback


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_file(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def external(argv, cwd, raw_dir, name, timeout=20):
    """Run only read-only metadata commands, preserving their exact bytes."""
    started = utc()
    result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout)
    (raw_dir / (name + ".stdout.raw")).write_bytes(result.stdout)
    (raw_dir / (name + ".stderr.raw")).write_bytes(result.stderr)
    receipt = {"argv": argv, "cwd": str(cwd), "started_utc": started,
        "finished_utc": utc(), "exit_code": result.returncode,
        "stdout_file": name + ".stdout.raw", "stderr_file": name + ".stderr.raw"}
    json_file(raw_dir / (name + ".json"), receipt)
    if result.returncode:
        raise RuntimeError("metadata command failed: " + repr(argv))
    return result.stdout


def source_identity(root, requested_sha, bridge, sidecar, raw_dir):
    resolved = external(["git", "rev-parse", requested_sha + "^{commit}"], root, raw_dir,
        "git-requested-sha").decode("ascii").strip()
    head = external(["git", "rev-parse", "HEAD"], root, raw_dir, "git-head").decode("ascii").strip()
    if head != resolved:
        raise RuntimeError("source-root HEAD differs from --source-sha")
    dirty = external(["git", "diff", "--name-only", "HEAD", "--"], root, raw_dir, "git-tracked-diff")
    if dirty.strip():
        raise RuntimeError("source-root has tracked changes; require the unmodified pre-patch checkout")
    tracked = set(external(["git", "ls-files", "-z"], root, raw_dir,
        "git-tracked-files").decode("utf-8").split("\0"))
    binary_bytes, sidecar_bytes = bridge.read_bytes(), sidecar.read_bytes()
    metadata = json.loads(sidecar_bytes)
    if metadata.get("name") != "bridge" or not isinstance(metadata.get("files"), dict) or not metadata["files"]:
        raise RuntimeError("require an official bridge .fingerprint.json sidecar with source files")
    binary_sha = sha(binary_bytes)
    if metadata.get("exe_sha256") != binary_sha:
        raise RuntimeError("bridge bytes differ from the official sidecar SHA-256")
    if metadata.get("exe_size") != len(binary_bytes):
        raise RuntimeError("bridge size differs from the official sidecar")
    if metadata.get("exe_mtime_ns") != bridge.stat().st_mtime_ns:
        raise RuntimeError("bridge mtime differs from the official sidecar")
    checked = {}
    for relative, expected in sorted(metadata["files"].items()):
        target = (root / relative).resolve()
        if relative not in tracked or not target.is_relative_to(root) or not target.is_file():
            raise RuntimeError("sidecar source is not a tracked checkout file: " + relative)
        actual = sha(target.read_bytes().replace(b"\r\n", b"\n"))
        if actual != expected:
            raise RuntimeError("sidecar source differs from unmodified checkout: " + relative)
        checked[relative] = actual
    fingerprint = hashlib.sha256()
    fingerprint.update(metadata["command"].encode("utf-8"))
    fingerprint.update(b"\0")
    for relative, actual in sorted(checked.items()):
        fingerprint.update((relative + "\0" + actual + "\n").encode("utf-8"))
    if fingerprint.hexdigest() != metadata.get("fingerprint"):
        raise RuntimeError("official sidecar fingerprint does not match its command/source list")
    return {"source_root": str(root), "source_sha": resolved, "source_tree_sha":
        external(["git", "rev-parse", "HEAD^{tree}"], root, raw_dir, "git-tree").decode("ascii").strip(),
        "bridge": str(bridge), "bridge_sha256": binary_sha, "bridge_size": len(binary_bytes),
        "sidecar": str(sidecar), "sidecar_sha256": sha(sidecar_bytes),
        "sidecar_fingerprint": metadata["fingerprint"], "build_command": metadata["command"],
        "source_files_checked": checked}


class Bridge:
    def __init__(self, executable, root, directory):
        self.directory = directory
        self.stdin_file = (directory / "bridge.stdin.raw").open("wb")
        self.stdout_file = (directory / "bridge.stdout.raw").open("wb")
        self.stderr_file = (directory / "bridge.stderr.raw").open("wb")
        self.started = utc()
        self.process = subprocess.Popen([str(executable)], cwd=root, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=self.stderr_file, bufsize=0)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.pending = b""
        self.rows = []
        self.closed = False

    def response_line(self, timeout=60):
        deadline = time.monotonic() + timeout
        while b"\n" not in self.pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise TimeoutError("native response exceeded " + str(timeout) + " seconds")
            chunk = os.read(self.process.stdout.fileno(), 65536)
            self.stdout_file.write(chunk); self.stdout_file.flush()
            self.pending += chunk
            if not chunk:
                result, self.pending = self.pending, b""
                return result
        line, self.pending = self.pending.split(b"\n", 1)
        return line + b"\n"

    def command(self, text):
        if "\n" in text or "\r" in text:
            raise ValueError("one native command per JSON protocol line")
        index = len(self.rows) + 1
        started, monotonic = utc(), time.monotonic()
        encoded = (text + "\n").encode("utf-8")
        row = {"index": index, "command": text, "started_utc": started,
            "stdin_file": f"command-{index:03d}.stdin.raw",
            "stdout_file": f"command-{index:03d}.stdout.raw"}
        self.rows.append(row)
        (self.directory / f"command-{index:03d}.stdin.raw").write_bytes(encoded)
        json_file(self.directory / "commands.json", self.rows)
        self.stdin_file.write(encoded); self.stdin_file.flush()
        self.process.stdin.write(encoded); self.process.stdin.flush()
        try:
            output = self.response_line()
        except Exception as error:
            row.update({"finished_utc": utc(), "elapsed_seconds": time.monotonic() - monotonic,
                "error": repr(error)})
            (self.directory / f"command-{index:03d}.stdout.raw").write_bytes(self.pending)
            json_file(self.directory / "commands.json", self.rows)
            raise
        (self.directory / f"command-{index:03d}.stdout.raw").write_bytes(output)
        row.update({"finished_utc": utc(), "elapsed_seconds": time.monotonic() - monotonic})
        json_file(self.directory / "commands.json", self.rows)
        if not output:
            raise RuntimeError("native bridge closed before command response; process code=" + str(self.process.poll()))
        value = json.loads(output.decode("utf-8"))
        if not isinstance(value, dict):
            raise RuntimeError("native response was not a JSON object")
        row["response"] = value
        json_file(self.directory / "commands.json", self.rows)
        return value

    def ok(self, text):
        value = self.command(text)
        if not value.get("ok"):
            raise AssertionError((text, value))
        return value

    def commit(self, text):
        value = self.command("line " + text)
        if "preview" in value:
            preview = value["preview"]
            if not preview.get("valid"):
                raise AssertionError(("pre-patch seed preview invalid", text, value))
            value = self.command("line confirm " + str(preview["token"]))
        if not value.get("ok"):
            raise AssertionError(("pre-patch seed did not commit", text, value))
        return value

    def apply(self, operations):
        revision = self.ok("engineering-read")["revision"]
        path = self.directory / ("request-" + str(len(self.rows) + 1) + ".json")
        json_file(path, {"schema": "engineering-transaction/1", "expectedRevision": revision,
            "operations": operations})
        preview = self.ok("engineering-preview " + str(path))["preview"]
        if not preview.get("valid"):
            raise AssertionError(("pre-patch engineering seed preview invalid", preview))
        self.ok("engineering-confirm " + str(preview["token"]))

    def close(self):
        if self.closed:
            return self.process.returncode
        self.closed = True
        self.selector.close()
        # communicate drains all trailing output and preserves an abnormal exit.
        self.process.stdin.close()
        self.process.stdin = None
        timed_out = False
        try:
            trailing, _ = self.process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            timed_out = True
            self.process.kill()
            trailing, _ = self.process.communicate()
        self.stdout_file.write(trailing)
        self.stdin_file.close(); self.stdout_file.close(); self.stderr_file.close()
        for row in self.rows:
            row["process_exit_code"] = self.process.returncode
            row["process_stderr_file"] = "bridge.stderr.raw"
        json_file(self.directory / "commands.json", self.rows)
        json_file(self.directory / "process.json", {"argv": self.process.args,
            "started_utc": self.started, "finished_utc": utc(), "exit_code": self.process.returncode,
            "timed_out": timed_out, "stdin_file": "bridge.stdin.raw", "stdout_file": "bridge.stdout.raw",
            "stderr_file": "bridge.stderr.raw", "commands_file": "commands.json"})
        return self.process.returncode


def field(identifier, value, name=None):
    return {"id": identifier, "name": name or str(identifier), "type": "dimension", "input": str(value)}


def parameter(identifier=901, u=400, v=300, inspector=False):
    return {"op": "put-parameter", "value": {"id": identifier,
        "name": "相位來源" if inspector else "offset",
        "fields": [field(1, u, "正" if inspector else "1"), field(2, v, "負" if inspector else "2")]}}


def system(identifier=0, name="G", main="none", u="repeat 0 2000 stagger 400", v="repeat 0 1830 stagger 300"):
    return f"grid-system {identifier} name-hex {name.encode('utf-8').hex()} main-along {main} u {u} v {v}"


def seed(bridge, kind):
    bridge.ok("reset")
    if kind == "direct":
        declaration = system()
    elif kind == "param":
        bridge.apply([parameter()])
        declaration = system(u="repeat 0 2000 stagger param:901:1", v="repeat 0 1830 stagger param:901:2")
    elif kind == "card":
        bridge.apply([{"op": "put-parameter", "value": {"id": 10, "name": "P",
            "fields": [field(3, 12, "a"), field(8, 30, "b")]}}])
        operation = {"op": "put-grid-system", "value": {"id": 4, "name": "G", "mainAlong": "none",
            "u": "repeat -5 card stagger 6", "v": "repeat 7 card stagger 4",
            "cardReference": {"parameterId": 10, "uFieldId": 3, "vFieldId": 8}}}
        bridge.apply([operation])
        return None
    elif kind == "panel":
        declaration = system(u="repeat-panel 400 gap 5 from -100 stagger 200", v="repeat 0 600 stagger -400")
    elif kind == "bound":
        bridge.commit("boundary 71 outline 400,500 1600,500 1600,1300 400,1300")
        fingerprint = bridge.ok("boundary 71")["geometryFingerprint"]
        declaration = system(5, "grid store", "u", "repeat 7 120 stagger 13", "repeat -11 80 stagger -7")
        bridge.commit(declaration)
        bridge.commit("grid-binding 1 on-boundary 71 from-system 5 vertex outer 0 geometry-hash " +
            fingerprint + " cell -2 -3 anchor 2 4 2 8")
        bridge.commit("placement 1 on boundary 71 origin 0 0 0 u +x v +y")
        bridge.commit("grid 1 on 1 from-binding 1")
        objects = bridge.ok("objects")
        if objects["gridBindings"][0]["translation"] != [560, 731]:
            raise AssertionError(("independent bound translation", objects))
        return declaration
    elif kind == "inspector-direct":
        declaration = system(name="Before", u="repeat 0 600 stagger -400",
            v="repeat-panel 400 gap 5 from -100 stagger 200")
    elif kind == "inspector-parameter":
        bridge.apply([parameter(v=-400, inspector=True)])
        declaration = system(name="Before", u="repeat-panel 400 gap 5 from -100 stagger param:901:1",
            v="repeat 0 600 stagger param:901:2")
    else:
        raise ValueError(kind)
    bridge.commit(declaration)
    return declaration


def freeze(kind, args, identity, environment):
    directory = args.outdir / "raw" / kind
    directory.mkdir(parents=True)
    bridge = Bridge(args.bridge, args.source_root, directory)
    result = {"kind": kind, "started_utc": utc(), "source_sha": identity["source_sha"],
        "bridge_sha256": identity["bridge_sha256"], "sidecar_sha256": identity["sidecar_sha256"],
        "environment_file": "environment.json", "raw_directory": str(directory)}
    path = args.outdir / ("legacy-two-axis-stagger-" + kind + ".scene")
    try:
        declaration = seed(bridge, kind)
        original = bridge.ok("dump")["text"].encode("utf-8")
        rows = [line for line in original.decode("utf-8").splitlines() if line.startswith("grid-system ")]
        if len(rows) != 1 or (declaration is not None and rows != [declaration]):
            raise AssertionError(("exactly one unchanged expected legacy declaration", rows, declaration))
        path.write_bytes(original)
        bridge.ok("loadfile " + str(path))
        reopened = bridge.ok("dump")["text"].encode("utf-8")
        (directory / "reopened.scene").write_bytes(reopened)
        if reopened != original:
            raise AssertionError("pre-patch loadfile/dump differs from the frozen bytes")
        objects = bridge.ok("objects")
        systems = objects["gridSystems"]
        if len(systems) != 1 or any("stagger" not in systems[0][axis + "Definition"] for axis in ("u", "v")):
            raise AssertionError(("reopen lost the existing two-axis definition", systems))
        if kind == "bound" and objects["gridBindings"][0]["translation"] != [560, 731]:
            raise AssertionError(("reopen changed independent bound translation", objects))
        result.update({"status": "passed", "fixture": path.name, "fixture_sha256": sha(original),
            "fixture_bytes": len(original), "reopened_sha256": sha(reopened), "byte_identical": True,
            "grid_system_declaration": rows[0]})
    except Exception as error:
        result.update({"status": "failed", "error": repr(error), "traceback": traceback.format_exc()})
    finally:
        exit_code = bridge.close()
        result["exit_code"] = exit_code
        if exit_code:
            result["status"] = "failed"
            result.setdefault("error", "native process exited abnormally")
        result["finished_utc"] = utc()
        result["raw_sha256"] = {entry.name: sha(entry.read_bytes()) for entry in sorted(directory.iterdir()) if entry.is_file()}
        json_file(args.outdir / (path.stem + ".receipt.json"), result)
        lines = ["# #314 舊雙軸場景產製收據", "", "以下為本次實際執行結果；完整指令與原始輸出在 raw 目錄。", "",
            "- 結果：`" + result["status"] + "`。",
            "- 來源 SHA：`" + identity["source_sha"] + "`。",
            "- bridge SHA-256：`" + identity["bridge_sha256"] + "`。",
            "- sidecar SHA-256：`" + identity["sidecar_sha256"] + "`。",
            "- process exit：`" + str(exit_code) + "`。",
            "- fixture SHA-256：`" + str(result.get("fixture_sha256", "未產出成功收據")) + "`。",
            "- loadfile/dump 位元組相同：`" + str(result.get("byte_identical", False)) + "`。",
            "- 環境：`environment.json`；來源與編法：`source-identity.json`。",
            "- 逐項收據：`" + path.stem + ".receipt.json`。", ""]
        if result.get("error"):
            lines.extend(["實際失敗原因：", "", "```text", result["error"], "```", ""])
        (args.outdir / (path.stem + ".provenance.md")).write_text("\n".join(lines), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge", required=True, type=Path)
    parser.add_argument("--sidecar", type=Path, help="default: <bridge>.fingerprint.json")
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args()
    args.bridge = args.bridge.resolve(strict=True)
    args.source_root = args.source_root.resolve(strict=True)
    args.outdir = args.outdir.resolve()
    args.sidecar = (args.sidecar or Path(str(args.bridge) + ".fingerprint.json")).resolve(strict=True)
    if args.outdir.is_relative_to(args.source_root):
        parser.error("--outdir must be outside the unmodified source checkout")
    if args.outdir.exists() and any(args.outdir.iterdir()):
        parser.error("--outdir must be new or empty; existing receipts are never overwritten")
    args.outdir.mkdir(parents=True, exist_ok=True)
    raw_meta = args.outdir / "raw" / "metadata"
    raw_meta.mkdir(parents=True)
    summary = {"schema": "geo314-legacy-fixtures/1", "started_utc": utc(),
        "invocation": [sys.executable, *sys.argv], "script_sha256": sha(Path(__file__).read_bytes())}
    try:
        old_stack = resource.getrlimit(resource.RLIMIT_STACK)
        required_stack = 16384 * 1024
        if old_stack[1] != resource.RLIM_INFINITY and old_stack[1] < required_stack:
            raise RuntimeError("hard stack limit is below 16384 KiB")
        resource.setrlimit(resource.RLIMIT_STACK, (required_stack, old_stack[1]))
        allowed = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "CC", "CFLAGS", "TMPDIR",
            "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "GEOMETRY_TEST_BRIDGE", "GEOMETRY_MODEL_BASE")
        environment = {"platform": platform.platform(), "python": sys.version,
            "cwd": str(Path.cwd()), "environment": {key: os.environ[key] for key in allowed if key in os.environ},
            "proxy_variables_present": sorted(key for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY") if key in os.environ),
            "stack_before": old_stack, "stack_during": resource.getrlimit(resource.RLIMIT_STACK)}
        json_file(args.outdir / "environment.json", environment)
        for command in ("google-chrome", "node", "cc"):
            executable = shutil.which(command)
            if executable:
                external([executable, "--version"], args.source_root, raw_meta, "version-" + command)
        identity = source_identity(args.source_root, args.source_sha, args.bridge, args.sidecar, raw_meta)
        json_file(args.outdir / "source-identity.json", identity)
        shutil.copyfile(args.sidecar, args.outdir / "bridge.fingerprint.json")
        results = [freeze(kind, args, identity, environment) for kind in
            ("direct", "param", "card", "panel", "bound", "inspector-direct", "inspector-parameter")]
        # Recheck the same checkout and binary after every seed/reopen process.
        final_meta = args.outdir / "raw" / "metadata-final"
        final_meta.mkdir()
        final_identity = source_identity(args.source_root, args.source_sha, args.bridge, args.sidecar, final_meta)
        if final_identity != identity:
            raise RuntimeError("source/binary/sidecar identity changed during fixture generation")
        summary.update({"status": "passed" if all(row["status"] == "passed" for row in results) else "failed",
            "source_sha": identity["source_sha"], "fixtures": results})
    except Exception as error:
        summary.update({"status": "failed", "error": repr(error), "traceback": traceback.format_exc()})
    summary["finished_utc"] = utc()
    json_file(args.outdir / "generation.json", summary)
    print(json.dumps({"status": summary["status"], "receipt": str(args.outdir / "generation.json")}, ensure_ascii=False))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
