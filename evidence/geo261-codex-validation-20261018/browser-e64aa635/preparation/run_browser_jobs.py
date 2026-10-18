#!/usr/bin/env python3
"""依固定 SHA 的 CI 流程循序執行六組瀏覽器驗收，所有產物留在 checkout 外。

此腳本不安裝工具、不更新 golden，也不修改 repository。
預設只接受 GEO-261 e64aa635；執行前請確認 native 階段已完成。
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shlex
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time


EXPECTED_SHA = "e64aa6359d600f43313ec9d7ba1112c465b6a40c"
DEFAULT_CHROME = Path("/workspace/geo261-tools/google-chrome-155.0.8059.84/opt/google/chrome/google-chrome")
SUITES = (
    ("canvas", 35, 9333, "cdp_test.js", {}),
    ("assembly", 15, 9367, "cdp_test.js", {"GEOMETRY_ASSEMBLY_ONLY": "1"}),
    ("documents", 10, 9366, "documents_browser_test.js", {}),
    ("grid", 15, 9334, "cdp_test.js", {"GEOMETRY_GRID_SYSTEM_ONLY": "1"}),
    ("space", 15, 9347, "space_model_test.js", {}),
    ("timber", 20, 9348, "space_model_test.js", {"GEOMETRY_TIMBER_ONLY": "1"}),
)
SCREEN_DIRECTORIES = (
    "GEOMETRY_ASSEMBLY_CONTEXT_SCREENSHOTS",
    "GEOMETRY_COMPOSITION_SCREENSHOT_DIR",
    "GEOMETRY_DOCUMENT_SCREENSHOT_DIR",
    "GEOMETRY_ENGINEERING_SCREENSHOT_DIR",
    "GEOMETRY_GRID_RENAME_SCREENSHOT_DIR",
    "GEOMETRY_GRID_RULE_SCREENSHOT_DIR",
    "GEOMETRY_GRID_SCREENSHOT_DIR",
    "GEOMETRY_GRID_SYSTEM_SCREENSHOT_DIR",
    "GEOMETRY_MARQUEE_SCREENSHOT_DIR",
    "GEOMETRY_MODEL_SNAPSHOT_SCREENSHOTS",
    "GEOMETRY_PROJECT_AUDIT_SCREENSHOT_DIR",
    "GEOMETRY_REPAIR_SCREENSHOT_DIR",
    "GEOMETRY_ROOM_SCREENSHOT_DIR",
    "GEOMETRY_SCHEDULE_SCREENSHOT_DIR",
    "GEOMETRY_SELECTION_CURSOR_SCREENSHOT_DIR",
    "GEOMETRY_SOURCE_NAVIGATION_SCREENSHOT_DIR",
    "GEOMETRY_SUPPORT_SCREENSHOT_DIR",
    "GEOMETRY_UIUX_SCREENSHOT_DIR",
    "GEOMETRY_UX_REFINEMENT_SCREENSHOT_DIR",
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    temporary = path.with_name(path.name + ".pending")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def capture(command, *, cwd, env=None):
    result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=20, check=False)
    return {"command": command, "exit_code": result.returncode,
            "output": result.stdout.decode("utf-8", errors="replace")}


def source_state(repo):
    head = capture(["git", "rev-parse", "HEAD"], cwd=repo)
    status = capture(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=repo)
    changed = capture(["git", "diff", "--no-ext-diff", "--name-only", "HEAD"], cwd=repo)
    if head["exit_code"] or status["exit_code"] or changed["exit_code"]:
        raise RuntimeError("無法取得 repository SHA 或狀態")
    return {"sha": head["output"].strip(), "status": status["output"],
            "tracked_changes": changed["output"].splitlines()}


def stop_owned_group(process):
    """只處理由本 runner 以 start_new_session 建立的 process group。"""
    original = process.poll()
    cleanup = {"pid": process.pid, "pgid": process.pid,
               "exit_code_before_cleanup": original, "signals": []}
    try:
        os.killpg(process.pid, signal.SIGTERM)
        cleanup["signals"].append("SIGTERM")
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        process.poll()
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            cleanup["signals"].append("SIGKILL")
        except ProcessLookupError:
            pass
    try:
        cleanup["exit_code_after_cleanup"] = process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        cleanup["exit_code_after_cleanup"] = None
        cleanup["cleanup_error"] = "主行程在 SIGKILL 後仍未結束"
    return cleanup


def command_step(command, *, repo, env, log_path, deadline, steps, label, timeout=None):
    record = {"label": label, "command": command, "shell_display": shlex.join(command),
              "cwd": str(repo), "log": str(log_path), "started_utc": utc_now(),
              "timed_out": False, "exit_code": None}
    steps.append(record)
    started = time.monotonic()
    remaining = deadline - started
    if timeout is not None:
        remaining = min(remaining, timeout)
    if remaining <= 0:
        record.update(timed_out=True, not_started=True, ended_utc=utc_now(), elapsed_seconds=0)
        return record
    record["timeout_seconds"] = remaining
    process = None
    try:
        with log_path.open("ab") as output:
            process = subprocess.Popen(command, cwd=repo, env=env, stdout=output,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            record["pid"] = process.pid
            record["pgid"] = process.pid
            try:
                record["exit_code"] = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                record["timed_out"] = True
    except OSError as error:
        record["launch_error"] = str(error)
    finally:
        if process is not None:
            record["cleanup"] = stop_owned_group(process)
            if record["exit_code"] is None:
                record["exit_code"] = process.returncode
        record.update(ended_utc=utc_now(), elapsed_seconds=round(time.monotonic() - started, 3))
    return record


def succeeded(step):
    return step["exit_code"] == 0 and not step["timed_out"] and not step.get("launch_error")


def check_unoccupied_port(port, label):
    """只建立後立即關閉 TCP 探查；不送 API、不停止或替換既有 listener。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(1)
        error = probe.connect_ex(("127.0.0.1", port))
    observation = {"label": label, "utc": utc_now(), "host": "127.0.0.1", "port": port,
                   "connect_errno": error, "no_listener_observed": error == errno.ECONNREFUSED}
    if error == 0:
        raise RuntimeError(f"port {port} 已有 listener；未停止既有服務，也未啟動 harness")
    if error != errno.ECONNREFUSED:
        raise RuntimeError(f"port {port} 無法確認未佔用（errno={error}）；未啟動 harness")
    return observation


def owned_runtime(step, server):
    """e64 start_local 用 execve 替換為 serve，/runtime.pid 必須保留 launcher PID。"""
    lines = Path(step["log"]).read_text(encoding="utf-8").splitlines()
    try:
        state = json.loads(next(line for line in reversed(lines) if line.strip()))
    except (ValueError, StopIteration) as error:
        raise RuntimeError("freshness probe 未輸出有效的 runtime JSON") from error
    if server.poll() is not None:
        raise RuntimeError("本次 launcher／server 已結束；拒絕沿用其他服務")
    if type(state.get("pid")) is not int or state["pid"] != server.pid:
        raise RuntimeError(f"runtime PID {state.get('pid')} 不屬於本次 server PID {server.pid}；未啟動 harness")
    return {"verified_utc": utc_now(), "expected_pid": server.pid, "runtime_pid": state["pid"],
            "launcher_uses_execve": True, "server_running": True, "runtime": state}


def archive_artifacts(source, directory):
    """把實際測試產物複製進 /workspace 證據，避免只依賴 /tmp symlink。"""
    destination = directory / "artifacts"
    destination.mkdir(mode=0o700)
    manifest = {"source_tmp_directory": str(source), "destination": str(destination),
                "started_utc": utc_now(), "files": [], "omitted": [], "errors": []}
    root_omissions = {"cache", "config", "data", "chrome-profile"}
    profile_prefixes = ("geometry-documents-chrome-", "geometry-cdp-", "com.google.Chrome.", ".com.google.Chrome.")
    for current, subdirectories, filenames in os.walk(source, followlinks=False):
        current_path = Path(current)
        relative_directory = current_path.relative_to(source)
        retained = []
        for name in subdirectories:
            path = current_path / name
            relative = path.relative_to(source).as_posix()
            if ((current_path == source and name in root_omissions) or name == "chrome-profile" or
                    name.startswith(profile_prefixes) or path.is_symlink()):
                manifest["omitted"].append({"path": relative, "reason": "瀏覽器 profile/cache、暫存 socket 或 symlink 目錄"})
            else:
                retained.append(name)
        subdirectories[:] = retained
        (destination / relative_directory).mkdir(parents=True, exist_ok=True)
        for name in filenames:
            path = current_path / name
            relative = path.relative_to(source)
            target = destination / relative
            try:
                mode = path.lstat().st_mode
                if not stat.S_ISREG(mode):
                    manifest["omitted"].append({"path": relative.as_posix(), "reason": "非一般檔案；不解引用 symlink 或 socket"})
                    continue
                shutil.copy2(path, target)
                with target.open("rb") as stream:
                    checksum = hashlib.file_digest(stream, "sha256").hexdigest()
                manifest["files"].append({"path": relative.as_posix(), "bytes": target.stat().st_size, "sha256": checksum})
            except OSError as error:
                manifest["errors"].append({"path": relative.as_posix(), "error": str(error)})
    manifest["ended_utc"] = utc_now()
    write_json(directory / "artifact-manifest.json", manifest)
    return {"path": str(destination), "manifest": str(directory / "artifact-manifest.json"),
            "source_tmp_directory": str(source), "file_count": len(manifest["files"]),
            "bytes": sum(item["bytes"] for item in manifest["files"]), "errors": manifest["errors"]}


def environment(directory, suite, cdp_port, flags, chrome):
    # 清除繼承的所有 GEOMETRY 覆寫，包括篩選、故障注入、golden 更新與舊 binary。
    # 只記錄變數名稱，不輸出繼承的值或任何其他 process 環境。
    removed_names = sorted(key for key in os.environ if key.startswith("GEOMETRY_"))
    env = {key: value for key, value in os.environ.items() if not key.startswith("GEOMETRY_")}
    # Chrome 的 SingletonSocket 路徑需短於 Unix domain socket 上限。
    # 每 job 使用短的專屬 /tmp，並在證據目錄保留可追蹤連結。
    temp = Path(tempfile.mkdtemp(prefix="g261-" + suite + "-", dir="/tmp"))
    (directory / "tmp").symlink_to(temp, target_is_directory=True)
    settings = {
        "TMPDIR": str(temp), "TMP": str(temp), "TEMP": str(temp),
        "XDG_CACHE_HOME": str(temp / "cache"),
        "XDG_CONFIG_HOME": str(temp / "config"),
        "XDG_DATA_HOME": str(temp / "data"),
        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1",
        "GEOMETRY_TEST_URL": "http://127.0.0.1:18839/",
        "GEOMETRY_FEEDBACK_DIR": str(temp / "feedback"),
        "GEOMETRY_CHROME": str(chrome), "GEOMETRY_CHROME_FLAGS": "--no-sandbox",
        "GEOMETRY_CHROME_PROFILE": str(temp / "chrome-profile"),
        "GEOMETRY_BROWSER_SUITE": suite, "GEOMETRY_CDP_PORT": str(cdp_port),
        "GEOMETRY_TEST_SERVER_PATH_STYLE": "native",
        "GEOMETRY_TEST_SCREENSHOT": str(temp / "screens" / "phase1-shell.png"),
        "GEOMETRY_SPACE_TEST_DIR": str(temp / "space-results"),
        "GEOMETRY_EVIDENCE_TEST_DIR": str(temp / "evidence-results"),
        "GEOMETRY_ENGINEERING_DOWNLOAD_DIR": str(temp / "downloads"),
        **flags,
    }
    for name in SCREEN_DIRECTORIES:
        settings[name] = str(temp / "screens" / name.removeprefix("GEOMETRY_").lower())
    for path in (temp, temp / "cache", temp / "config", temp / "data", temp / "screens", temp / "downloads",
                 temp / "geometry-tests"):
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    env.update(settings)
    return env, settings, removed_names


def run_suite(spec, *, repo, output, chrome, expected_sha):
    suite, minutes, cdp_port, script, flags = spec
    directory = output / suite
    directory.mkdir(mode=0o700)
    env, explicit_env, removed_names = environment(directory, suite, cdp_port, flags, chrome)
    started = time.monotonic()
    deadline = started + minutes * 60
    result = {"suite": suite, "started_utc": utc_now(), "ci_timeout_minutes": minutes,
              "timeout_scope": "建置、啟動、runtime probe 與 harness 共用 CI job 時限；清理及封存另記",
              "status": "running", "steps": [], "environment": explicit_env,
              "cleared_inherited_geometry_variable_names": removed_names,
              "source_before": source_state(repo), "browser": str(chrome),
              "browser_difference": "CI 指定 /usr/bin/google-chrome；本次使用明列的瀏覽器，版本見 environment.json",
              "timed_out": False, "harness_exit_code": None}
    receipt = directory / "result.json"
    server = None
    server_output = None
    write_json(receipt, result)
    print(f"[{utc_now()}] 開始 {suite}，上限 {minutes} 分鐘", flush=True)
    try:
        if result["source_before"]["sha"] != expected_sha:
            raise RuntimeError("來源 HEAD 已改變，拒絕以不同 SHA 執行")
        if result["source_before"]["tracked_changes"]:
            raise RuntimeError("tracked 來源有未提交變更，拒絕把工作目錄結果歸於指定 SHA")
        result["port_checks"] = [check_unoccupied_port(18839, "before_build")]
        build = command_step(["npm", "run", "build"], repo=repo, env=env,
                             log_path=directory / "build.log", deadline=deadline,
                             steps=result["steps"], label="build")
        write_json(receipt, result)
        if not succeeded(build):
            result["status"] = "build_failed"
            return result
        # 保留 workflow 的 WSL-only trace 條件；一般 Linux 不開 trace。
        if suite == "canvas" and "microsoft" in platform.release().lower():
            env["GEOMETRY_WAIT_TRACE"] = explicit_env["GEOMETRY_WAIT_TRACE"] = "1"
            trace = command_step(["python3", "geometry-web/prepare_wait_trace.py"], repo=repo, env=env,
                                 log_path=directory / "prepare-wait-trace.log", deadline=deadline,
                                 steps=result["steps"], label="prepare_wait_trace")
            if not succeeded(trace):
                result["status"] = "trace_prepare_failed"
                return result
            run_id = (directory / "prepare-wait-trace.log").read_text(encoding="utf-8").strip()
            env["GEOMETRY_WAIT_TRACE_RUN_ID"] = explicit_env["GEOMETRY_WAIT_TRACE_RUN_ID"] = run_id
        server_command = ["python3", "-u", "geometry-web/start_local.py", "--port", "18839"]
        result["port_checks"].append(check_unoccupied_port(18839, "before_start"))
        server_output = (directory / "server.log").open("ab")
        server = subprocess.Popen(server_command, cwd=repo, env=env, stdout=server_output,
                                  stderr=subprocess.STDOUT, start_new_session=True)
        result["server"] = {"command": server_command, "shell_display": shlex.join(server_command),
                            "pid": server.pid, "pgid": server.pid, "started_utc": utc_now(),
                            "log": str(directory / "server.log")}
        ready = False
        for attempt in range(1, 31):
            if server.poll() is not None:
                result["status"] = "server_exited_before_ready"
                break
            probe = command_step(["python3", "geometry-web/runtime_version.py", "--probe", "18839"],
                                 repo=repo, env=env, log_path=directory / "runtime-probe.log",
                                 deadline=deadline, steps=result["steps"], label=f"runtime_probe_{attempt}")
            if succeeded(probe):
                result["initial_server_ownership"] = owned_runtime(probe, server)
                ready = True
                break
            if probe["timed_out"] or time.monotonic() >= deadline:
                break
            time.sleep(min(1, max(0, deadline - time.monotonic())))
        if not ready:
            if result["status"] == "running":
                result["status"] = "runtime_not_ready"
            return result
        final_probe = command_step(["python3", "geometry-web/runtime_version.py", "--probe", "18839"],
                                   repo=repo, env=env, log_path=directory / "runtime-final-probe.log",
                                   deadline=deadline, steps=result["steps"], label="runtime_final_probe")
        if not succeeded(final_probe):
            result["status"] = "runtime_final_probe_failed"
            return result
        result["final_server_ownership"] = owned_runtime(final_probe, server)
        write_json(receipt, result)
        harness = command_step(["node", "geometry-web/" + script], repo=repo, env=env,
                               log_path=directory / "test.log", deadline=deadline,
                               steps=result["steps"], label="browser_harness")
        result["harness_exit_code"] = harness["exit_code"]
        result["status"] = "passed" if succeeded(harness) else "failed"
        return result
    except (OSError, RuntimeError) as error:
        result["status"] = "runner_error"
        result["error"] = str(error)
        return result
    except KeyboardInterrupt:
        result["status"] = "interrupted"
        raise
    finally:
        work_ended = time.monotonic()
        result["timed_out"] = any(step["timed_out"] for step in result["steps"])
        if result["timed_out"]:
            result["status"] = "timed_out"
        result["work_elapsed_seconds"] = round(work_ended - started, 3)
        if server is not None:
            result["server"]["cleanup"] = stop_owned_group(server)
            result["server"]["exit_code"] = server.returncode
            result["server"]["ended_utc"] = utc_now()
        if server_output is not None:
            server_output.close()
        if suite == "canvas":
            archive = command_step(["python3", "geometry-web/archive_wait_trace.py",
                                    str(directory / "wait-trace-artifact")],
                                   repo=repo, env=env, log_path=directory / "archive-wait-trace.log",
                                   deadline=time.monotonic() + 20, steps=result["steps"],
                                   label="archive_wait_trace_after_cleanup")
            if not succeeded(archive) and result["status"] == "passed":
                result["status"] = "trace_archive_failed"
        try:
            result["artifact_archive"] = archive_artifacts(Path(env["TMPDIR"]), directory)
            if result["artifact_archive"]["errors"] and result["status"] == "passed":
                result["status"] = "artifact_archive_failed"
        except OSError as error:
            result["artifact_archive"] = {"error": str(error), "source_tmp_directory": env["TMPDIR"]}
            if result["status"] == "passed":
                result["status"] = "artifact_archive_failed"
        result["source_after"] = source_state(repo)
        result["source_unchanged"] = result["source_before"] == result["source_after"]
        if not result["source_unchanged"] and result["status"] == "passed":
            result["status"] = "source_changed_during_run"
        result.update(ended_utc=utc_now(), elapsed_seconds=round(time.monotonic() - started, 3))
        write_json(receipt, result)
        print(f"[{utc_now()}] 結束 {suite}：{result['status']}，"
              f"harness exit={result['harness_exit_code']}，{result['elapsed_seconds']} 秒", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("/workspace/geometry-axiom"))
    parser.add_argument("--output", type=Path, help="新目錄；存在時拒絕覆寫")
    parser.add_argument("--chrome", type=Path, default=DEFAULT_CHROME)
    parser.add_argument("--expected-sha", default=EXPECTED_SHA)
    parser.add_argument("--only", nargs="+", choices=[spec[0] for spec in SUITES],
                        help="選擇分批項目；仍保留固定順序與原有每 job 時限")
    args = parser.parse_args()
    repo = args.repo.resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (args.output or Path(__file__).resolve().parent / ("browser-" + args.expected_sha[:8] + "-" + stamp)).resolve()
    if output == repo or repo in output.parents:
        parser.error("輸出必須在 repository 外")
    if not args.chrome.is_file() or not os.access(args.chrome, os.X_OK):
        parser.error("指定瀏覽器不存在或不可執行")
    initial_source = source_state(repo)
    if initial_source["sha"] != args.expected_sha:
        parser.error("repository HEAD 與 --expected-sha 不同")
    if initial_source["tracked_changes"]:
        parser.error("tracked 來源有未提交變更")
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    if hard != resource.RLIM_INFINITY and hard < 16384 * 1024:
        parser.error("stack 硬上限不足 16384 KiB")
    resource.setrlimit(resource.RLIMIT_STACK, (16384 * 1024, hard))
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    metadata = {"started_utc": utc_now(), "source": source_state(repo), "repo": str(repo),
                "workflow": ".github/workflows/integration-tests.yml", "kernel": platform.release(),
                "platform": platform.platform(), "stack_bytes": resource.getrlimit(resource.RLIMIT_STACK)[0],
                "browser_difference": "CI 使用 /usr/bin/google-chrome；本 runner 預設使用官方簽章及 SHA-256 驗證後解壓至 checkout 外的 Google Chrome stable。實際產品及版本見 versions.browser。",
                "chrome_install_evidence": "/workspace/geo261-tools/chrome-install-20261018",
                "validation_limit": "瀏覽器證據僅適用於 versions.browser 的實際產品與版本；未安裝套件，也未更改斷言或 golden。",
                "versions": {}}
    version_env = os.environ.copy()
    for name in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "TMPDIR"):
        directory = output / "metadata-tmp" / name.lower()
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        version_env[name] = str(directory)
    for name, command in (("os", ["cat", "/etc/os-release"]), ("gcc", ["gcc", "--version"]),
                          ("cc", ["cc", "--version"]), ("python", ["python3", "--version"]),
                          ("node", ["node", "--version"]), ("browser", [str(args.chrome), "--version"]),
                          ("cjk_font", ["fc-match", "Noto Sans CJK TC"])):
        try:
            metadata["versions"][name] = capture(command, cwd=repo, env=version_env)
        except (OSError, subprocess.TimeoutExpired) as error:
            metadata["versions"][name] = {"command": command, "error": str(error)}
    write_json(output / "environment.json", metadata)
    selected = [spec for spec in SUITES if not args.only or spec[0] in args.only]
    summary = {"expected_sha": args.expected_sha, "started_utc": utc_now(),
               "ordered_suites": [spec[0] for spec in selected], "results": []}
    write_json(output / "summary.json", summary)
    try:
        for spec in selected:
            result = run_suite(spec, repo=repo, output=output, chrome=args.chrome,
                               expected_sha=args.expected_sha)
            summary["results"].append(result)
            write_json(output / "summary.json", summary)
    except KeyboardInterrupt:
        summary["interrupted"] = True
    finally:
        summary["ended_utc"] = utc_now()
        summary["all_passed"] = (len(summary["results"]) == len(selected) and
                                 all(item["status"] == "passed" for item in summary["results"]))
        write_json(output / "summary.json", summary)
    print(f"證據目錄：{output}", flush=True)
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
