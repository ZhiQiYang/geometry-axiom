#!/usr/bin/env python3
"""Rebuild U476 native evidence from pinned base sources; no stored successes.

The native setup and real producer flow derive from L467/reproduce.py. This
version is self-contained with native_consume.cjs and native_projection.py,
uses fresh host epochs, bounds each subprocess, and records new raw receipts.
The output is research evidence, never a formal owner-service attestation.
"""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import secrets
import subprocess
import sys
import threading
import time

BASE = "19c00180228f6dfdff65684b47160736d2fae7e9"
HERE = Path(__file__).resolve().parent


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def digest(path):
    data = Path(path).read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def verify_base_sources(repo):
    """Allow new isolated research files; do not waive any existing input."""
    paths = ["current_geometry.c", "geometry-core", "geometry-web", "geometry-app", "geometry-templates", "tests/binaries.py"]
    names = subprocess.check_output(["git", "ls-tree", "-r", "-z", "--name-only", BASE, "--", *paths],
                                    cwd=repo, timeout=15).split(b"\0")
    existing = [name.decode("utf-8") for name in names if name]
    assert existing, "U476_EXISTING_NATIVE_INPUTS_EMPTY"
    # Passing the exact pinned BASE inventory excludes only files that did not exist
    # at this base. Existing source changes/deletions remain an error.
    diff = subprocess.run(["git", "diff", "--name-only", "--exit-code", BASE, "--", *existing], cwd=repo,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if diff.returncode:
        detail = (diff.stdout or diff.stderr).decode("utf-8", errors="replace")[:2000]
        raise RuntimeError("U476_PINNED_BASE_SOURCE_CHANGED: " + detail)
    return existing


def registry(repo, out):
    spec = importlib.util.spec_from_file_location("u476_binaries", repo / "tests/binaries.py")
    binaries = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = binaries
    spec.loader.exec_module(binaries)
    binaries.OUT_DIR = out / "binaries"
    binaries.OUT_DIR.mkdir(parents=True, exist_ok=True)
    return binaries


def build(repo, out):
    binaries = registry(repo, out)
    with binaries.ProcessLock("build"):
        results = binaries.build(["bridge", "model-base"])
    assert all(item.ok for item in results.values()), {k: vars(v) for k, v in results.items()}
    entries = []
    for name in ("bridge", "model-base"):
        binary = binaries.BY_NAME[name]
        entries.append({"name": name, "path": str(binary.path), "command": binary.command_string(),
                        "result": vars(results[name]), "fingerprint": json.loads(binary.sidecar.read_text()),
                        **digest(binary.path)})
    save(out / "build.json", {"base": BASE, "binaries": entries})
    print(json.dumps({"stage": "build", "ok": True, "binaries": [e["name"] for e in entries]}))


class Native:
    """One real bridge. The line reader cannot hang beyond COMMAND_TIMEOUT."""
    COMMAND_TIMEOUT = 30

    def __init__(self, bridge, out):
        self.commands = (out / "native.commands.txt").open("w", encoding="utf-8", newline="\n")
        self.stdout = (out / "native.stdout.jsonl").open("w", encoding="utf-8", newline="\n")
        self.stderr = (out / "native.stderr.txt").open("w", encoding="utf-8", newline="\n")
        self.process = subprocess.Popen([str(bridge)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=self.stderr, text=True, encoding="utf-8", cwd=out)
        self.replies = queue.Queue()
        def read_lines():
            try:
                for line in self.process.stdout:
                    self.replies.put(line)
            finally:
                self.replies.put(None)
        self.reader = threading.Thread(target=read_lines, daemon=True)
        self.reader.start()

    def command(self, command, allow_preview=False):
        self.commands.write(command + "\n")
        self.commands.flush()
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
        try:
            line = self.replies.get(timeout=self.COMMAND_TIMEOUT)
        except queue.Empty:
            self.process.kill()
            raise TimeoutError("Native command timed out: " + command)
        assert line, "Native bridge closed"
        self.stdout.write(line)
        self.stdout.flush()
        result = json.loads(line)
        assert result.get("ok") is True or (allow_preview and result.get("preview", {}).get("valid") is True), (command, result)
        return result

    def line(self, command):
        result = self.command("line " + command, allow_preview=True)
        if result.get("preview", {}).get("valid"):
            result = self.command("line confirm " + str(result["preview"]["token"]))
        assert result.get("ok") is True, result
        return result

    def close(self):
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            code = self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
            raise
        finally:
            self.reader.join(timeout=2)
            self.process.stdout.close()
            self.commands.close()
            self.stdout.close()
            self.stderr.close()
        assert code == 0, code


def native_run(repo, out):
    sys.path.insert(0, str(repo))
    sys.path.insert(0, str(repo / "geometry-web"))
    binaries = registry(repo, out)
    bridge = binaries.BY_NAME["bridge"].path
    model_base = binaries.BY_NAME["model-base"].path
    import space_modeling as sm
    from modeling import verify_package

    def scenario(native, name, selected):
        folder = out / name
        folder.mkdir(parents=True, exist_ok=True)
        full, bare = native.command("dump"), native.command("dump-deidentified")
        (folder / "live.scene").write_text(full["text"], encoding="utf-8", newline="\n")
        (folder / "model-input.scene").write_text(bare["text"], encoding="utf-8", newline="\n")
        graph = native.command("source-inspect")
        references = native.command("references")
        save(folder / "live-graph.json", graph)
        save(folder / "live-references.json", references)
        save(folder / "identity-read.json", native.command("identity-read"))
        data = {"mode": "plan", "base_scene": bare["text"], "placement_id": 0,
                "settings": {"bottom": 0, "height": 3000, "edges": [0, 1, 2, 3],
                             "floor": "boundary", "ceiling": "boundary", "holes": "none", "wall_thickness": None},
                "obstacles": [], "timbers": [{"kind": "timber", "id": v} for v in selected]}
        save(folder / "producer-input.json", data)
        start = time.monotonic()
        with (folder / "producer.stdout.txt").open("w", encoding="utf-8", newline="\n") as stdout, \
             (folder / "producer.stderr.txt").open("w", encoding="utf-8", newline="\n") as stderr:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = sm.preview(data, base_executable=str(model_base))
                verified = []
                for key in ("space", "volume", "clearance", "walls", "timbers"):
                    if result[key] is not None:
                        verify_package(result[key], base_executable=str(model_base))
                        verified.append(key)
                assert sm.replay_stored(data, result, base_executable=str(model_base)) == result
        save(folder / "producer-result.json", result)
        save(folder / "producer-proof.json", {"producer": "space_modeling.preview", "real_native": str(model_base),
             "independently_rebuilt_packages": verified, "historical_replay_equal": True,
             "elapsed_seconds": time.monotonic() - start})
        package_scene = folder / "package-base.scene"
        package_scene.write_text(result["timbers"]["definitions"]["base_scene"], encoding="utf-8", newline="\n")
        save(folder / "snapshot.json", native.command("source-inspect-file " + str(folder / "model-input.scene")))
        save(folder / "package-snapshot.json", native.command("source-inspect-file " + str(package_scene)))
        after, after_dump = native.command("source-inspect"), native.command("dump")
        save(folder / "live-graph-after-snapshots.json", after)
        assert after == graph and after_dump == full, "U476_NATIVE_READONLY"
        save(folder / "native-readonly-proof.json", {"graph_equal_including_revision": True, "dump_equal": True})
        print(json.dumps({"scenario": name, "producer": "space_modeling.preview", "replay": "equal",
                          "native_readonly": True, "selected": selected}), flush=True)

    native = Native(bridge, out)
    epoch = secrets.token_hex(16)
    try:
        native.command("reset")
        native.command("identity-epoch " + epoch)
        for line in ("boundary 1 outline 0,0 4000,0 4000,3000 0,3000 kind room_plan",
                     "placement 0 on boundary 1 origin 0 0 2500 u +x v +y", "timber 0 27 33 role boundary",
                     "place 0 on 0 at-face e0 +u +n", "identity-ledger activate"):
            native.line(line)
        scenario(native, "single", [0])
        native.line("timber 4 27 33 role boundary")
        native.line("place 4 on 0 at-face e2 +u +n")
        scenario(native, "independent-control", [0, 4])
    finally:
        native.close()
    save(out / "native-run.json", {"base": BASE, "nativeIdentityEpoch": epoch,
         "freshRandomHostEpoch": True, "modelPinsComeFromOriginalLiveGraph": True,
         "candidateIncarnationsNotUsed": True, "literalDimensionsOnly": True})


def bounded(command, repo, out, name, timeout):
    start = time.monotonic()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"}
    with (out / (name + ".stdout.txt")).open("w", encoding="utf-8", newline="\n") as stdout, \
         (out / (name + ".stderr.txt")).open("w", encoding="utf-8", newline="\n") as stderr:
        process = subprocess.Popen(command, cwd=repo, env=env, stdout=stdout, stderr=stderr,
                                   start_new_session=os.name != "nt")
        timed_out = False
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name != "nt":
                import signal
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.wait(timeout=10)
            code = 124
    receipt = {"command": command, "cwd": str(repo), "timeoutSeconds": timeout, "exit": code,
               "timedOut": timed_out, "elapsedSeconds": time.monotonic() - start,
               "stdout": digest(out / (name + ".stdout.txt")), "stderr": digest(out / (name + ".stderr.txt"))}
    save(out / (name + ".receipt.json"), receipt)
    print(json.dumps({"stage": name, "exit": code, "timedOut": timed_out}), flush=True)
    assert code == 0, f"{name} exited {code}; see {out}/{name}.stderr.txt"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, help="optional U476 research candidate.cjs for history and K1 projection")
    parser.add_argument("--fixture", type=Path, help="write the eight generated U476 facts and provenance as a portable fixture")
    parser.add_argument("--stage", choices=("all", "build", "native"), default="all")
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True, timeout=10).strip()
    inventory = verify_base_sources(repo)
    save(out / "source-state.json", {"base": BASE, "observedHead": head,
         "existingBaseFilesVerified": len(inventory), "onlyAdditiveResearchHeadAllowed": True})
    if args.stage == "build":
        build(repo, out)
        return
    if args.stage == "native":
        native_run(repo, out)
        return
    script = str(Path(__file__).resolve())
    common = [sys.executable, script, "--repo", str(repo), "--out", str(out)]
    bounded([*common, "--stage", "build"], repo, out, "build", 240)
    bounded([*common, "--stage", "native"], repo, out, "native-run", 240)
    bounded(["node", str(HERE / "native_consume.cjs"), str(repo), str(out)], repo, out, "consume", 90)
    bounded([sys.executable, str(HERE / "native_projection.py"), "--native-artifacts", str(out),
             "--out", str(out / "facts")], repo, out, "projection", 90)
    bounded([sys.executable, str(HERE / "native_root_probe.py"), "--native-artifacts", str(out)],
            repo, out, "native-root-probe", 90)
    if args.candidate:
        bounded(["node", str(HERE / "native_cutting_projection.cjs"), str(repo), str(out), str(args.candidate.resolve())],
                repo, out, "cutting-projection", 90)
    if args.fixture:
        bounded([sys.executable, str(HERE / "native_fixture.py"), "--repo", str(repo), "--artifacts", str(out),
                 "--fixture", str(args.fixture.resolve())], repo, out, "fixture-pack", 90)
    files = {str(p.relative_to(out)): digest(p) for p in sorted(out.rglob("*"))
             if p.is_file() and "binaries" not in p.relative_to(out).parts and p.name != "artifact-manifest.json"}
    save(out / "artifact-manifest.json", {"base": BASE, "observedHead": head, "researchOnly": True, "files": files})
    print(json.dumps({"ok": True, "base": BASE, "observedHead": head, "output": str(out), "freshNative": True,
                      "ownerScope": "explicit offline research, not a product owner service",
                      "formalTakeoffCapability": False, "browserRun": False}), flush=True)


if __name__ == "__main__":
    main()
