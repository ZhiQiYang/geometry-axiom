#!/usr/bin/env python3
"""唯讀解析 browser runner 收據；只在外部證據目錄產生繁中報告。

不匯入產品／測試程式、不呼叫服務、不執行 build、Chrome 或測試。
預設只接受六個 job 的 final 收據；--partial 明列尚未完成項目。
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex


SHA = "e64aa6359d600f43313ec9d7ba1112c465b6a40c"
ROOT = Path("/workspace/geo261-validation-20261018/browser-e64aa635")
CONTRACT = Path("/workspace/geo261-validation-20261018/browser-harness-contract-e64aa635.json")
CONTRACT_SHA256 = "e587f5e4717b6b8fa743fc638b8939202a67d91643d00725a08389b43941d277"
SPECS = (
    ("canvas", 35, 9333, "cdp_test.js", [], "full"),
    ("assembly", 15, 9367, "cdp_test.js", ["GEOMETRY_ASSEMBLY_ONLY"], "partial"),
    ("documents", 10, 9366, "documents_browser_test.js", [], None),
    ("grid", 15, 9334, "cdp_test.js", ["GEOMETRY_GRID_SYSTEM_ONLY"], "partial"),
    ("space", 15, 9347, "space_model_test.js", [], "full-space-suite"),
    ("timber", 20, 9348, "space_model_test.js", ["GEOMETRY_TIMBER_ONLY"], "partial"),
)
LABELS = {"passed": "通過", "failed": "失敗", "timed_out": "逾時，未完整",
          "running": "執行中", "not_started": "尚未開始", "receipt_incomplete": "收據不足，不能宣稱通過"}
LIMITS = {
    "cdp_test.js": "consoleAPICalled 僅列印 [console]，未保留類型，也沒有獨立 console.error gate。非預期例外會增加 failedAssertions；僅 full canvas 的 P38 刻意注入 fb-auto-probe，仍會計入 uncaughtBrowserExceptions，因此該欄不等於非預期例外數。",
    "documents_browser_test.js": "未監聽 consoleAPICalled，不能宣稱 console 無錯；只檢查 Runtime 例外、HTTP >=400 與外部請求，未監聽 Network.loadingFailed。成功 footer 沒有 schema、scope 或 completed，完整性依成功專用 footer、零失敗與正常退出判讀。",
    "space_model_test.js": "原 browser-health 群組要求未捕捉例外及 console.error 都為零；另以固定群組斷言 census 核對完整性。timber 的限定範圍仍會跑 browser-health。",
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def evidence(path, root):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"證據不是一般檔案：{path}")
    data = path.read_bytes()
    return {"relative_path": path.relative_to(root).as_posix(), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def marker_receipts(log, prefix):
    receipts, errors = [], []
    for number, line in enumerate(log.splitlines(), 1):
        if not line.startswith(prefix + " "):
            continue
        try:
            receipts.append({"line": number, "original": line, "value": json.loads(line[len(prefix) + 1:])})
        except ValueError as error:
            errors.append(f"第 {number} 行 {prefix} 無效 JSON：{error}")
    return receipts, errors


def nonnegative_integer(value):
    return type(value) is int and value >= 0


def runtime_valid(record, root):
    issues = []
    server = record.get("server", {})
    for name in ("initial_server_ownership", "final_server_ownership"):
        owner = record.get(name, {})
        runtime = owner.get("runtime", {})
        if not (owner.get("server_running") is True
                and owner.get("expected_pid") == server.get("pid")
                and type(server.get("pid")) is int
                and owner.get("runtime_pid") == server.get("pid")
                and runtime.get("pid") == server.get("pid")
                and runtime.get("fresh") is True
                and runtime.get("schema") == "geometry-runtime/1"
                and runtime.get("root") == "/workspace/geometry-axiom"
                and isinstance(runtime.get("version"), str)
                and len(runtime["version"]) == 64):
            issues.append(f"{name} 缺少完整 freshness／服務所有權收據")
    step = next((s for s in record.get("steps", []) if s.get("label") == "runtime_final_probe"), {})
    if step.get("exit_code") != 0 or step.get("timed_out") is not False:
        issues.append("最後 runtime probe 未正常成功")
    probe = root / record["suite"] / "runtime-final-probe.log"
    if probe.is_file():
        try:
            actual = json.loads(probe.read_text().strip().splitlines()[-1])
            if actual != record.get("final_server_ownership", {}).get("runtime"):
                issues.append("final probe 原文與 result 收據不一致")
        except (ValueError, IndexError):
            issues.append("final probe 原文無法解析")
    else:
        issues.append("缺少 final probe 原文")
    return issues


def collect_job(root, spec, contract):
    name, minutes, port, script, filters, mode = spec
    row = {"job": name, "expected_sha": SHA, "ci_timeout_minutes": minutes,
           "expected_harness_command": ["node", "geometry-web/" + script],
           "expected_scope_filters": filters, "expected_cdp_port": port,
           "console_and_network_limit": LIMITS[script], "status": "not_started",
           "job_finished": False, "harness_completed": False, "verified_pass": False,
           "passed_assertions": None, "failed_assertions": None,
           "evidence_issues": [], "raw_files": []}
    receipt = root / name / "result.json"
    if not receipt.exists():
        return row
    record = read_json(receipt)
    row.update(status=record["status"], started_utc=record["started_utc"],
               job_finished=bool(record.get("ended_utc")))
    if not row["job_finished"]:
        # 不對仍在追加的 log 建立易過時的 hash 或推論通過。
        row["observed_steps"] = record.get("steps", [])
        row["runtime_ready_observed"] = not runtime_valid(record, root)
        return row
    issues = row["evidence_issues"]
    row.update(ended_utc=record["ended_utc"], elapsed_seconds=record.get("elapsed_seconds"),
               work_elapsed_seconds=record.get("work_elapsed_seconds"),
               harness_exit_code=record.get("harness_exit_code"), timed_out=record.get("timed_out"),
               timeout_scope=record.get("timeout_scope"), actual_environment=record.get("environment", {}),
               steps=record.get("steps", []), server=record.get("server"),
               source_before=record.get("source_before"), source_after=record.get("source_after"),
               source_unchanged=record.get("source_unchanged"),
               initial_server_ownership=record.get("initial_server_ownership"),
               final_server_ownership=record.get("final_server_ownership"),
               artifact_archive=record.get("artifact_archive"), runner_error=record.get("error"))
    for path in sorted((root / name).glob("*.log")):
        row["raw_files"].append(evidence(path, root))
    row["raw_files"].append(evidence(receipt, root))
    for basename in ("artifact-manifest.json",):
        path = root / name / basename
        if path.exists():
            row["raw_files"].append(evidence(path, root))
    for stage in ("source_before", "source_after"):
        source = record.get(stage, {})
        if source.get("sha") != SHA or source.get("status") != "" or source.get("tracked_changes") != []:
            issues.append(f"{stage} 不是指定 SHA 的乾淨來源")
    if record.get("source_unchanged") is not True:
        issues.append("未證實來源在 job 期間保持不變")
    if record.get("ci_timeout_minutes") != minutes:
        issues.append("job 時限與 workflow 不符")
    harness = next((s for s in record["steps"] if s["label"] == "browser_harness"), None)
    row["harness_started"] = harness is not None and not harness.get("not_started")
    row["runtime_evidence_issues"] = runtime_valid(record, root)
    if row["harness_started"]:
        issues.extend(row["runtime_evidence_issues"])
        if harness.get("command") != row["expected_harness_command"]:
            issues.append("實際 harness 命令與 workflow 不符")
        if harness.get("exit_code") != record.get("harness_exit_code"):
            issues.append("harness 底層退出碼收據不一致")
        if not harness.get("ended_utc"):
            issues.append("harness 缺少終止時間")
        if record["status"] == "passed":
            required_steps = ["build", "runtime_final_probe", "browser_harness"]
            if name == "canvas":
                required_steps.append("archive_wait_trace_after_cleanup")
            for label in required_steps:
                matches = [s for s in record["steps"] if s.get("label") == label]
                if len(matches) != 1 or matches[0].get("exit_code") != 0 or matches[0].get("timed_out") is not False or not matches[0].get("ended_utc") or matches[0].get("launch_error") or matches[0].get("not_started"):
                    issues.append(f"{label} 缺少正常成功的唯一終止收據")
    env = record["environment"]
    if env.get("GEOMETRY_CDP_PORT") != str(port):
        issues.append("CDP port 與該 job 不符")
    observed_filters = sorted(key for key, value in env.items() if key.startswith("GEOMETRY_") and key.endswith("_ONLY") and value)
    if observed_filters != sorted(filters) or any(env.get(key) != "1" for key in filters):
        issues.append("scope 環境旗標與該 job 不符")
    if "GEOMETRY_CDP_UPDATE_GOLDEN" in env:
        issues.append("出現不可接受的 golden 更新旗標")
    log_path = root / name / "test.log"
    log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    prefix = "CDP_RESULT" if script == "cdp_test.js" else "DOCUMENTS_RESULT" if script == "documents_browser_test.js" else "SPACE_RESULT"
    markers, errors = marker_receipts(log, prefix)
    row["completion_markers"] = markers
    issues.extend(errors)
    if row["harness_started"] and len(markers) != 1:
        issues.append(f"{prefix} 完成收據共 {len(markers)} 筆，預期恰一筆；保留原始退出結果但不能宣稱完整通過")
    if len(markers) == 1 and not isinstance(markers[0]["value"], dict):
        issues.append("完成收據 JSON 不是 object，保留原文但不判讀為通過")
    if len(markers) == 1 and isinstance(markers[0]["value"], dict):
        marker = markers[0]["value"]
        if script == "space_model_test.js":
            passed, failed = marker.get("passed"), marker.get("failed")
        else:
            passed, failed = marker.get("passedAssertions"), marker.get("failedAssertions")
        if not nonnegative_integer(passed) or not nonnegative_integer(failed):
            issues.append("斷言計數格式不合法")
        else:
            row.update(passed_assertions=passed, failed_assertions=failed)
            if record["status"] == "passed" and passed == 0:
                issues.append("通過收據沒有執行任何通過斷言")
        if script == "documents_browser_test.js":
            row["harness_completed"] = (nonnegative_integer(failed) and failed == 0 and nonnegative_integer(passed) and passed > 0
                                        and marker.get("viewport") == [1400, 900, 390, 844]
                                        and isinstance(marker.get("screenshots"), str)
                                        and record.get("harness_exit_code") == 0)
            row["completeness_basis"] = "成功專用 DOCUMENTS_RESULT，非既有 completed 欄位"
        else:
            expected_schema = "geometry-cdp-result/1" if script == "cdp_test.js" else "geometry-space-result/1"
            if marker.get("schema") != expected_schema:
                issues.append("完成收據 schema 不符")
            scope = marker.get("scope", {})
            if not isinstance(scope, dict):
                issues.append("完成收據 scope 不是 object")
                scope = {}
            if scope.get("mode") != mode or scope.get("filters") != filters or scope.get("url") != "http://127.0.0.1:18839/":
                issues.append("完成收據的 scope 與 job 不符")
            row["harness_completed"] = marker.get("completed") is True
            row["scope"] = scope
            if script == "cdp_test.js":
                row["golden_compare"] = marker.get("goldenCompare")
                row["uncaught_browser_exceptions_including_expected"] = marker.get("uncaughtBrowserExceptions")
                row["sections"] = marker.get("sections")
                row["sections_failed"] = marker.get("sectionsFailed", {})
                row["fatal"] = marker.get("fatal")
                row["first_transport_failure"] = marker.get("firstTransportFailure")
                row["first_network_failure"] = marker.get("firstNetworkFailure")
                row["current_section"] = marker.get("currentSection")
                row["expected_exception_lines"] = [line for line in log.splitlines() if line.startswith("[EXPECTED EXCEPTION]")]
                row["unexpected_exception_lines"] = [line for line in log.splitlines() if line.startswith("[UNEXPECTED EXCEPTION]")]
                if scope.get("modifiers") != []:
                    issues.append("CDP scope 出現 workflow 未指定的 modifier")
                expected_golden = "matched" if name == "canvas" else "not compared (partial mode)"
                if row["harness_completed"] and failed == 0 and marker.get("goldenCompare") != expected_golden:
                    issues.append("零失敗 footer 的 golden 狀態與原 CI scope 不符")
                if name == "canvas" and row["harness_completed"] and failed == 0:
                    golden = contract["cdp_golden"]
                    row["golden_sections_match_snapshot"] = marker.get("sections") == golden["sections"]
                    if not row["golden_sections_match_snapshot"] or passed != golden["total"]:
                        issues.append("canvas 逐段斷言數與 e64 golden 快照不符")
            else:
                row["groups"] = marker.get("groups")
                row["completeness_problems"] = marker.get("completenessProblems")
                row["browser_exceptions"] = marker.get("exceptions")
                row["console_errors"] = marker.get("consoleErrors")
                # 沿用 harness 固定 census 收據，不以本次執行學習新的地板。
                if marker.get("completed") is True and (marker.get("completenessProblems") != [] or marker.get("exceptions") != [] or marker.get("consoleErrors") != []):
                    issues.append("宣稱完整的 space footer 仍有 completeness 或 browser-health 問題")
                included = contract[name + "_included"]
                if scope.get("included") != included:
                    issues.append("space/timber included 群組與 workflow 固定 scope 不符")
                selected = ["setup", *included, "browser-health"]
                if marker.get("completed") is True:
                    groups = marker.get("groups", {})
                    if not isinstance(groups, dict):
                        issues.append("space/timber groups 不是 object")
                        groups = {}
                    if set(groups) != set(selected):
                        issues.append("space/timber 群組集合與固定 census 不符")
                    for group in selected:
                        expected = contract["space_expected"][group]
                        if groups.get(group) != {"expected": expected, "passed": expected, "failed": 0, "completed": True}:
                            issues.append(f"{group} 收據與固定 census 不符")
                    if passed != sum(contract["space_expected"][group] for group in selected):
                        issues.append("space/timber 通過總數與固定 census 不符")
                archived = root / name / "artifacts" / "space-results" / "result.json"
                if not archived.is_file():
                    issues.append("space/timber 缺少實體封存的 result.json")
                else:
                    row["raw_files"].append(evidence(archived, root))
                    artifact = read_json(archived)
                    if any(artifact.get(key) != value for key, value in marker.items() if key != "schema"):
                        issues.append("space/timber 實體封存 result 與文字 footer 不一致")
    archive = record.get("artifact_archive", {})
    if archive.get("errors") != [] or archive.get("error"):
        issues.append("artifact 封存未完整成功")
    manifest_path = root / name / "artifact-manifest.json"
    if not manifest_path.is_file():
        issues.append("缺少 artifact manifest")
    else:
        manifest = read_json(manifest_path)
        if manifest.get("errors") != [] or len(manifest.get("files", [])) != archive.get("file_count"):
            issues.append("artifact manifest 與封存收據不一致")
        row["archived_file_count"] = len(manifest.get("files", []))
        row["archive_manifest"] = evidence(manifest_path, root)
        artifact_root = root / name / "artifacts"
        seen = set()
        verified = 0
        for item in manifest.get("files", []):
            relative = Path(item.get("path", ""))
            if not relative.parts or relative.is_absolute() or ".." in relative.parts or item["path"] in seen:
                issues.append("artifact manifest 含非法或重複路徑")
                continue
            seen.add(item["path"])
            path = artifact_root / relative
            if artifact_root.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != root and root in parent.parents):
                issues.append(f"artifact 路徑包含 symlink：{item['path']}")
                continue
            try:
                actual = evidence(path, root)
            except (OSError, ValueError) as error:
                issues.append(f"artifact 實體檔案缺失／不合法：{item['path']}：{error}")
                continue
            if actual["sha256"] != item.get("sha256") or actual["bytes"] != item.get("bytes"):
                issues.append(f"artifact bytes／SHA-256 不符：{item['path']}")
            else:
                verified += 1
        row["archive_files_hash_verified"] = verified
    if name == "canvas":
        trace = root / name / "wait-trace-artifact"
        row["wait_trace_files"] = [evidence(path, root) for path in sorted(trace.rglob("*")) if path.is_file() and not path.is_symlink()] if trace.is_dir() else []
        if not row["wait_trace_files"]:
            issues.append("canvas 缺少 wait trace 封存收據")
        receipt_path = trace / "receipt.json"
        if not receipt_path.is_file() or receipt_path.is_symlink():
            issues.append("canvas 缺少正式 wait trace receipt.json")
        else:
            trace_receipt = read_json(receipt_path)
            row["wait_trace_receipt"] = trace_receipt
            enabled = env.get("GEOMETRY_WAIT_TRACE") == "1"
            expected_status = "archived" if enabled else "trace-disabled-for-this-runner"
            if trace_receipt.get("head") != SHA or trace_receipt.get("status") != expected_status:
                issues.append("canvas wait trace 收據的 SHA／狀態不符")
            trace_env = trace_receipt.get("effectiveEnvironment", {})
            if any(trace_env.get(key) != env.get(key) for key in ("GEOMETRY_WAIT_TRACE", "GEOMETRY_FEEDBACK_DIR", "GEOMETRY_BROWSER_SUITE", "GEOMETRY_WAIT_TRACE_RUN_ID")):
                issues.append("canvas wait trace 環境與該 job 不符")
            if enabled:
                raw_trace = trace / "wait-trace.jsonl"
                if not raw_trace.is_file() or raw_trace.is_symlink():
                    issues.append("啟用的 wait trace 缺少原始 JSONL")
                else:
                    actual_trace = evidence(raw_trace, root)
                    if actual_trace["sha256"] != trace_receipt.get("sha256") or actual_trace["bytes"] != trace_receipt.get("bytes"):
                        issues.append("wait trace 原始檔 bytes／SHA-256 不符")
    row["verified_pass"] = (record["status"] == "passed" and record.get("harness_exit_code") == 0
                            and record.get("timed_out") is False and row["harness_completed"]
                            and row["failed_assertions"] == 0 and not issues)
    if record["status"] == "passed" and not row["verified_pass"]:
        row["status"] = "receipt_incomplete"
    row["failure_classification"] = None if row["verified_pass"] else "待逐項根因分類；不可由退出碼或耗時直接推定產品缺陷"
    return row


def render(doc):
    jobs = doc["jobs"]
    counts = Counter(row["status"] for row in jobs)
    complete = doc["all_jobs_finished"]
    lines = ["# GEO-261 六個瀏覽器 job 基準報告", "",
             f"測試來源固定為 `{SHA}`。報告產生時間：{doc['generated_utc']}。",
             "本報告只適用於這個測試 SHA；報告分支或之後的 integration head 不等於已驗來源。",
             "",
             ("六個 job 已有終止收據。" if complete else "**此為進度報告；六個 job 尚未全部完成，不是最終驗收結論。**"),
             f"可由完整證據確認通過：{sum(r['verified_pass'] for r in jobs)}/6。狀態計數：`{json.dumps(dict(counts), ensure_ascii=False)}`。",
             "", "| job | 工作時限 | 狀態 | harness exit | 工作秒數／含封存秒數 | 通過／失敗斷言 | harness 完整 | 原始 log |",
             "|---|---:|---|---:|---:|---:|---|---|"]
    for row in jobs:
        counts_text = f"{row['passed_assertions']} / {row['failed_assertions']}" if row['passed_assertions'] is not None else "未取得"
        link = f"[{row['job']}/test.log]({row['job']}/test.log)" if any(f['relative_path'] == row['job'] + '/test.log' for f in row['raw_files']) else "尚無 final log 收據"
        lines.append(f"| {row['job']} | {row['ci_timeout_minutes']} 分鐘 | {LABELS.get(row['status'], row['status'])} | {row.get('harness_exit_code', '—')} | {row.get('work_elapsed_seconds', '—')} / {row.get('elapsed_seconds', '—')} | {counts_text} | {'是' if row['harness_completed'] else '否／未取得'} | {link} |")
    lines += ["", "斷言數不是端到端情境數。逾時或 fatal 前的已執行斷言，不能代表未執行範圍通過。",
              "", "## 環境與執行差異", "",
              "Debian GNU/Linux 13.6、Linux 6.18.55 x86_64；GCC 14.2.0、Python 3.12.14、Node 24.19.0；真正 Google Chrome 155.0.8059.84；Noto Sans CJK TC；stack 16 MiB。完整原始版本見 [environment.json](environment.json)。",
              "Chrome 位於 `/workspace/geo261-tools/google-chrome-155.0.8059.84/opt/google/chrome/google-chrome`，由官方 HTTPS／簽章／套件 SHA-256 驗證後解壓。CI 路徑為 `/usr/bin/google-chrome`；本次沒有使用 Chromium 冒稱 Chrome。",
              "各 job 預定流程依序為 `npm run build`、獨立 Linux `start_local.py --port 18839`、fresh runtime probe、原 harness；實際執行到哪一步以該 job 收據為準。CI 時限數值維持 35／15／10／15／15／20 分鐘；本機時限涵蓋 build、服務啟動、probe 與 harness，清理／封存另計。CI 的 checkout、字型安裝與 artifact upload 邊界不同，故不宣稱整個 CI wall-clock 完全相同。",
              "已開始的 job 使用短 `/tmp` 與獨立 XDG/profile、feedback、screenshots、downloads；完成後把實際證據另封存至該 job `artifacts/`，保留來源路徑與 SHA-256 manifest。只清理本 runner 擁有的 process group。所有繼承 GEOMETRY 旗標先清除，不更新 golden，也沒有放寬斷言。",
              "", "## 每個 job 的命令與證據", ""]
    for row in jobs:
        lines += [f"### {row['job']}", "", f"Harness：`{shlex.join(row['expected_harness_command'])}`；scope 旗標：`{','.join(row['expected_scope_filters']) or '(無)'}`。", "", row["console_and_network_limit"], ""]
        if not row["job_finished"]:
            lines += ["尚無終止收據；未宣稱通過。", ""]
            continue
        lines += [f"起迄：{row['started_utc']} → {row['ended_utc']}；測試來源與收據：[result.json]({row['job']}/result.json)。",
                  f"Runtime：{'fresh 與自建服務 PID 均有收據' if not row['runtime_evidence_issues'] else '收據不足：' + '；'.join(row['runtime_evidence_issues'])}。兩次 probe 均在 harness 啟動前，未宣稱另做執行後 probe。",
                  f"原始命令、各步起迄／timeout／底層 exit、server 清理與環境全部保留在 [browser-stage-results.json](browser-stage-results.json) 的此 job row。"]
        if "golden_compare" in row:
            lines.append(f"Golden：`{row['golden_compare']}`。")
        if row.get("fatal"):
            lines += ["", "原始 fatal：", "", "```text", row["fatal"] if isinstance(row["fatal"], str) else json.dumps(row["fatal"], ensure_ascii=False), "```"]
        if row.get("completeness_problems"):
            lines += ["", "完整性問題原文：", "", "```json", json.dumps(row["completeness_problems"], ensure_ascii=False, indent=2), "```"]
        if row["evidence_issues"]:
            lines += ["", "證據限制："] + [f"- {issue}" for issue in row["evidence_issues"]]
        lines += ["", "原始檔案："] + [f"- [{f['relative_path']}]({f['relative_path']})：{f['bytes']} bytes；SHA-256 `{f['sha256']}`。" for f in row["raw_files"]]
        lines += [""]
    unfinished = [row["job"] for row in jobs if not row["job_finished"]]
    unresolved = [row["job"] for row in jobs if row["job_finished"] and not row["verified_pass"]]
    lines += ["## 未驗與修正狀態", "",
              "尚未完成：" + ("、".join(unfinished) if unfinished else "無") + "。",
              "已取得終止收據者中，失敗／收據不足且須逐項分析：" + ("、".join(unresolved) if unresolved else "無") + "。",
              "本輪為原始基準測試；未套用 proposed-fixes，未在此階段建立修正分支。修正後重跑與撤除修正轉紅的突變證據，須另輪記錄。",
              "canvas／assembly／grid／documents 沒有完整 console.error gate，不能由通過推論 console 無錯。space 與 timber 只按其原 scope 及 census 報告。",
              "已取得的原始 footer 與 byte/hash 收據見 [browser-stage-results.json](browser-stage-results.json)；本報告的完整性核對是證據判讀，沒有修改 CI 測試判準。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--partial", action="store_true", help="產生明確標記的進度報告，不宣稱 final")
    args = parser.parse_args()
    root = args.root.resolve()
    if root != ROOT:
        parser.error("此報告器只接受已授權的固定外部 browser baseline 目錄")
    env = read_json(root / "environment.json")
    summary = read_json(root / "summary.json")
    if hashlib.sha256(CONTRACT.read_bytes()).hexdigest() != CONTRACT_SHA256:
        parser.error("固定 harness 契約快照已改變")
    contract = read_json(CONTRACT)
    if summary.get("expected_sha") != SHA or env.get("source", {}).get("sha") != SHA:
        parser.error("來源 SHA 不一致")
    if summary.get("ordered_suites") != [spec[0] for spec in SPECS]:
        parser.error("不是指定六 job 的原順序")
    jobs = [collect_job(root, spec, contract) for spec in SPECS]
    all_finished = all(row["job_finished"] for row in jobs)
    if not args.partial and (not all_finished or not summary.get("ended_utc") or len(summary.get("results", [])) != 6):
        parser.error("六 job 或 runner 尚未全部取得終止收據；只可明示 --partial 產生進度報告")
    if all_finished:
        for spec, receipt in zip(SPECS, summary.get("results", [])):
            if receipt != read_json(root / spec[0] / "result.json"):
                parser.error(f"summary 與 {spec[0]} 原始收據不一致")
    doc = {"schema": "geo261-browser-stage-report/1", "source_sha": SHA,
           "generated_utc": datetime.now(timezone.utc).isoformat(),
           "all_jobs_finished": all_finished, "runner_finished": bool(summary.get("ended_utc")),
           "runner_summary": summary, "environment": env,
           "harness_contract": contract, "harness_contract_sha256": CONTRACT_SHA256,
           "metadata_evidence": [evidence(root / name, root) for name in ("environment.json", "summary.json")],
           "jobs": jobs, "all_verified_passed": all(row["verified_pass"] for row in jobs),
           "failure_analysis": "逐項根因與分類另附；本工具不從耗時或退出碼推定根因"}
    for filename, content in (("browser-stage-results.json", json.dumps(doc, ensure_ascii=False, indent=2) + "\n"),
                              ("browser-stage-report.md", render(doc))):
        temporary = root / (filename + ".pending")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(root / filename)
    print(json.dumps({"report": str(root / "browser-stage-report.md"), "all_jobs_finished": all_finished,
                      "verified_passes": sum(row["verified_pass"] for row in jobs)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
