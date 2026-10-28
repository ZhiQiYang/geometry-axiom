#!/usr/bin/env python3
"""UI13 source retractions with named real-CDP failures and restored controls.

The command after ``--`` must start/stop its own isolated server and invoke the
repository cdp_test.js with GEOMETRY_PANEL_FILL_ONLY=1. It receives
GEOMETRY_PANEL_FILL_MUTATION_CASE and must not reuse a running source/server.
This tool neither changes a golden nor interprets a timeout as a killed mutant.
It never runs on an uncommitted source tree. Evidence goes to the explicit
output directory; stdout/stderr are streamed to gzip, not held only in memory.
"""
from __future__ import annotations
import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def replace_once(source: bytes, old: bytes, new: bytes) -> bytes:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"Expected one mutation anchor, found {count}: {old!r}")
    return source.replace(old, new, 1)


def variants(root: Path):
    app = root / "geometry-web/app.js"
    adapter = root / "geometry-web/panel-fill-adapter.js"
    app_bytes, adapter_bytes = app.read_bytes(), adapter.read_bytes()
    entry = b"if (fill) { window.PanelFillWorkspace?.open(Number(fill.dataset.panelFillOpen),fill); return; }"
    request_line = re.findall(rb"^  const requestId = connection\.session[^\n]+", app_bytes, re.MULTILINE)
    if len(request_line) != 1 or request_line[0].count(b"panel-fill-confirm ") != 1:
        raise ValueError("Expected one exact requestId declaration including panel-fill-confirm")
    return [
        ("entry-handler", "UI13_ENTRY_HANDLER", app, app_bytes,
         replace_once(app_bytes, entry, b"if (fill) { return; }")),
        ("preview-http", "UI13_PREVIEW_HTTP", adapter, adapter_bytes,
         replace_once(adapter_bytes, b"fetch('/panel-fill/preview',",
                      b"((...args)=>Promise.reject(new Error('UI13 removed preview HTTP')))('/panel-fill/preview',")),
        ("confirm-receipt", "UI13_CONFIRM_RECEIPT", app, app_bytes,
         replace_once(app_bytes, request_line[0], request_line[0].replace(b"panel-fill-confirm ", b"", 1))),
    ]


def execute(root: Path, out: Path, label: str, command: list[str], timeout: int, source_sha: str):
    directory = out / label
    directory.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, GEOMETRY_PANEL_FILL_ONLY="1", GEOMETRY_PANEL_FILL_MUTATION_CASE=label)
    began, started = time.monotonic(), utc()
    receipt = {"schema": "panel-fill-ui-mutation-run/1", "sourceCommit": source_sha,
               "command": command, "cwd": str(root), "startedUtc": started,
               "timeoutSeconds": timeout, "environment": {k: v for k, v in env.items()
                   if k.startswith("GEOMETRY_") and not any(s in k for s in ("TOKEN", "SECRET", "PASSWORD"))},
               "sourceFiles": {str(p.relative_to(root)): sha(p.read_bytes()) for p in (
                   root / "geometry-web/app.js", root / "geometry-web/panel-fill-adapter.js",
                   root / "geometry-web/panel_fill_workflow_test.js", root / "geometry-web/cdp_test.js")}}
    (directory / "started.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n")
    child = subprocess.Popen(command, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=os.name != "nt")
    errors = []

    def copy(pipe, destination):
        try:
            with gzip.open(destination, "wb") as output:
                while data := pipe.read(65536):
                    output.write(data)
        except BaseException as exc:
            errors.append(str(exc))

    threads = [threading.Thread(target=copy, args=(child.stdout, directory / "stdout.gz")),
               threading.Thread(target=copy, args=(child.stderr, directory / "stderr.gz"))]
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        code = child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name != "nt":
            os.killpg(child.pid, signal.SIGTERM)
        else:
            child.terminate()
        try:
            code = child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if os.name != "nt":
                os.killpg(child.pid, signal.SIGKILL)
            else:
                child.kill()
            code = child.wait()
    for thread in threads:
        thread.join()
    receipt.update(endedUtc=utc(), elapsedSeconds=time.monotonic()-began, exitCode=code,
                   timedOut=timed_out, captureErrors=errors)
    receipt["files"] = {name: {"sha256": sha((directory/name).read_bytes()), "bytes": (directory/name).stat().st_size}
                        for name in ("stdout.gz", "stderr.gz")}
    (directory / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"case": label, "exitCode": code, "timedOut": timed_out, "receipt": str(directory/"receipt.json")}), flush=True)
    return receipt, gzip.open(directory / "stdout.gz", "rt", errors="replace").read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--timeout", type=int, default=2100)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.output.resolve()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    selected = variants(root)
    source_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    print(json.dumps({"sourceCommit": source_sha, "anchors": [{"id": v[0], "assertion": v[1],
        "file": str(v[2].relative_to(root)), "originalSha256": sha(v[3]), "mutantSha256": sha(v[4])}
        for v in selected]}, ensure_ascii=False), flush=True)
    if args.preflight:
        return 0
    if not command:
        parser.error("Provide an isolated runner command after --; no test was started")
    if args.timeout <= 0 or args.timeout > 2100:
        parser.error("Timeout must stay within the original 35-minute canvas limit")
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root, text=True)
    if dirty:
        raise RuntimeError("Commit the source before mutation execution; tracked changes exist: "+dirty)
    baseline, text = execute(root, out, "baseline", command, args.timeout, source_sha)
    if baseline["exitCode"] != 0 or baseline["timedOut"] or baseline["captureErrors"]:
        raise RuntimeError("Baseline did not pass; no mutant was run")
    results = []
    originals = out / "originals"
    originals.mkdir(exist_ok=False)
    for source in {item[2] for item in selected}:
        with gzip.open(originals / (source.name+".gz"), "wb") as backup:
            backup.write(source.read_bytes())
    for identifier, assertion, source, original, changed in selected:
        if source.read_bytes() != original:
            raise RuntimeError("Source changed concurrently; refusing to overwrite "+str(source))
        try:
            source.write_bytes(changed)
            receipt, text = execute(root, out, identifier, command, args.timeout, source_sha)
            # A named failed assertion must be emitted by the real UI test. A
            # connection failure, unrelated exception, or timeout is not killed.
            killed = receipt["exitCode"] == 1 and not receipt["timedOut"] and not receipt["captureErrors"] and bool(
                re.search(r"^P128 "+re.escape(assertion)+r"[^\n]*✗", text, re.MULTILINE))
        finally:
            if source.read_bytes() != changed:
                raise RuntimeError("Mutation source changed concurrently; original preserved in memory, refusing overwrite "+str(source))
            source.write_bytes(original)
        restored, _ = execute(root, out, identifier+"-restored", command, args.timeout, source_sha)
        green = restored["exitCode"] == 0 and not restored["timedOut"] and not restored["captureErrors"]
        results.append({"id": identifier, "namedAssertion": assertion, "killed": killed, "restored": green})
        (out / "summary.json").write_text(json.dumps({"sourceCommit": source_sha, "results": results}, ensure_ascii=False, indent=2)+"\n")
        if not green:
            raise RuntimeError("Restored source did not pass; stop before the next mutant")
    return 0 if all(r["killed"] and r["restored"] for r in results) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("PF_UI_MUTATION_BLOCKED: "+str(error), file=sys.stderr)
        sys.exit(2)
