#!/usr/bin/env python3
"""Build and start the complete local Linux runtime, including A/B verification.

    python3 geometry-web/start_local.py --port 8765
    python3 geometry-web/start_local.py --build-only

Uses the existing native registry and its build receipts. No other service is
stopped. Windows users should continue using start.ps1 and its documented limits.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NATIVE_NAMES = ("core", "bridge", "model-base")
MIN_STACK = 16 * 1024 * 1024


def binary_directory(value=None, *, root=ROOT, temp=None):
    temp = Path(temp or tempfile.gettempdir()).resolve()
    if value is None:
        key = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:20]
        target = temp / "geometry-runtime" / key
    else:
        target = Path(value)
        if not target.is_absolute():
            raise ValueError("--binary-dir 必須是 TEMP 內的絕對路徑。")
    target = target.resolve()
    if (target == temp or temp not in target.parents or target == root.resolve()
            or root.resolve() in target.parents):
        raise ValueError("執行檔目錄必須是 TEMP 下的專用目錄，不能放在 repository 內。")
    return target


def ensure_stack(limits=None):
    if limits is None:
        import resource
        limits = resource
    soft, hard = limits.getrlimit(limits.RLIMIT_STACK)
    if soft == limits.RLIM_INFINITY or soft >= MIN_STACK:
        return
    if hard != limits.RLIM_INFINITY and hard < MIN_STACK:
        raise RuntimeError("目前 stack 硬上限低於 16 MiB，服務未啟動。")
    limits.setrlimit(limits.RLIMIT_STACK, (MIN_STACK, hard))
    if limits.getrlimit(limits.RLIMIT_STACK)[0] < MIN_STACK:
        raise RuntimeError("無法設定 16 MiB stack，服務未啟動。")


def check_port(port, *, managed=False):
    # Check before building and again immediately before exec. A bind race is
    # still possible; serve.py's own bind remains authoritative and fail-closed.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("0.0.0.0" if managed else "127.0.0.1", port))
        except OSError as error:
            raise RuntimeError(f"連接埠 {port} 無法使用；未停止或替換任何既有服務。請指定空閒連接埠。") from error


def load_registry(root=ROOT):
    spec = importlib.util.spec_from_file_location("geometry_local_binaries", root / "tests/binaries.py")
    registry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registry)
    return registry


def prepare_binaries(directory, registry=None):
    registry = registry or load_registry()
    registry.OUT_DIR = directory
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        lock = registry.ProcessLock("build")
        lock.__enter__()
    except registry.LockBusy as error:
        raise RuntimeError(str(error)) from error
    try:
        built = registry.build(NATIVE_NAMES)
        for name in NATIVE_NAMES:
            result = built[name]
            print(f"{name}: {result.status}" + (f" — {result.detail}" if result.detail else ""), flush=True)
            if not result.ok:
                raise RuntimeError(f"{name} 建置未完成：{result.status}；服務未啟動。")
        paths = {}
        for name in NATIVE_NAMES:
            binary = registry.BY_NAME[name]
            # Never infer freshness from successful compilation, file presence,
            # or a previous command's receipt. Re-read current source and bytes.
            paths[name] = registry.require_fresh(name, binary.path)
    finally:
        lock.__exit__(None, None, None)
    return paths


def runtime_environment(paths, *, managed=False, environ=None):
    env = dict(os.environ if environ is None else environ)
    bridge, base = paths["bridge"], paths["model-base"]
    env.update(GEOMETRY_BRIDGE=bridge, GEOMETRY_TEST_BRIDGE=bridge,
               GEOMETRY_MODEL_UPDATE_BRIDGE=bridge, GEOMETRY_SCENARIO_BRIDGE=bridge,
               GEOMETRY_MODEL_BASE=base, GEOMETRY_SCENARIO_BASE=base,
               GEOMETRY_TEST_CORE=paths["core"])
    # Overrides from a previous Windows/WSL or managed-preview session must not
    # change native path translation or unexpectedly expose a local service.
    for name in ("GEOMETRY_BRIDGE_WSL", "GEOMETRY_MODEL_BASE_WSL_DISTRO", "GEOMETRY_MANAGED_PREVIEW"):
        env.pop(name, None)
    if managed:
        env["GEOMETRY_MANAGED_PREVIEW"] = "1"
    return env


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, help="本機預設 8765；managed preview 固定 4173")
    parser.add_argument("--build-only", action="store_true", help="只建置並驗證核心、bridge 與 model-base")
    parser.add_argument("--managed-preview", action="store_true", help="沿用受管開發入口 4173")
    parser.add_argument("--binary-dir", type=Path, help="TEMP 下專用的執行檔與收據目錄")
    args = parser.parse_args(argv)
    port = args.port if args.port is not None else 4173 if args.managed_preview else 8765
    if not 1024 <= port <= 65535 or args.managed_preview and port != 4173:
        parser.error("連接埠須為 1024–65535；managed preview 必須使用 4173。")
    if not sys.platform.startswith("linux"):
        parser.error("此入口用於 Linux。Windows 請使用 geometry-web/start.ps1。")
    try:
        directory = binary_directory(args.binary_dir)
        ensure_stack()
        if not args.build_only:
            check_port(port, managed=args.managed_preview)
        paths = prepare_binaries(directory)
        print("LOCAL_RUNTIME " + json.dumps({"root": str(ROOT), "binaryDirectory": str(directory),
                                              "executables": paths, "port": None if args.build_only else port,
                                              "managedPreview": args.managed_preview}, ensure_ascii=False), flush=True)
        if args.build_only:
            return 0
        check_port(port, managed=args.managed_preview)
        env = runtime_environment(paths, managed=args.managed_preview)
        os.chdir(ROOT)
        # Replacing this process keeps the service's established Ctrl+C/finally
        # cleanup; the launcher does not leave a detached server behind.
        os.execve(sys.executable, [sys.executable, "-u", str(ROOT / "geometry-web/serve.py"), str(port)], env)
        raise RuntimeError("exec 未替換啟動程序。")
    except (OSError, RuntimeError, ValueError) as error:
        print("啟動失敗：" + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
