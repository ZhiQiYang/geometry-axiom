#!/usr/bin/env python3
"""更新已審閱排除檔雜湊、明列登記收尾工具，重跑 Linux 架構驗收並封存四檔收據。"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


ROOTS = ("geometry-core", "geometry-app", "geometry-templates", "geometry-web", "geometry-guide")
STANDALONE = ("current_geometry.c", "tests/__init__.py", "tests/binaries.py")
SUFFIXES = {".c", ".cc", ".cjs", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".htm", ".html", ".inc", ".js", ".jsx", ".mjs", ".py", ".ts", ".tsx"}
DIRECTORY = Path("geometry-core/domain-decoupling")
OUTPUTS = tuple(str(DIRECTORY / name) for name in (
    "product-architecture.json", "product-architecture-scan.json", "PRODUCT-ARCHITECTURE.md", "product-architecture-receipt.json"))
TOOLS = ("tests/architecture_contract.py", "tests/test_architecture_contract.py", "tests/test_product_architecture.py")
ADDED_DIRECTORY = "geometry-core/domain-decoupling/closeout-tools"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def hashes(raw):
    return {"rawSha256": sha(raw), "lfSha256": sha(raw.replace(b"\r\n", b"\n")), "bytes": len(raw)}


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def independent_inventory(root):
    paths = set(STANDALONE)
    for directory in ROOTS:
        for folder, dirs, names in os.walk(root / directory):
            if any((Path(folder) / name).is_symlink() for name in dirs + names):
                raise RuntimeError("來源根目錄內含符號連結，須另行審閱")
            for name in names:
                path = Path(folder) / name
                if path.suffix.lower() in SUFFIXES:
                    paths.add(path.relative_to(root).as_posix())
    return sorted(paths)


def snapshot(root):
    paths = independent_inventory(root)
    return {"paths": paths, "sources": {p: hashes((root / p).read_bytes()) for p in paths},
            "tools": {p: hashes((root / p).read_bytes()) for p in TOOLS}}


def closure(records, mode="lfSha256"):
    values = [{"path": p, "sha256": value[mode]} for p, value in sorted(records.items())]
    return values, sha(json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode())


def assert_git_source(root, head, before):
    tree = git(root, "ls-tree", "-r", "--full-tree", "-z", head).split(b"\0")
    objects = {}
    for row in filter(None, tree):
        metadata, path = row.split(b"\t", 1)
        mode, kind, object_id = metadata.split()
        objects[path.decode()] = (mode.decode(), kind.decode(), object_id.decode())
    expected = sorted(p for p in objects if p in STANDALONE or
                      (p.split("/", 1)[0] in ROOTS and Path(p).suffix.lower() in SUFFIXES))
    if expected != before["paths"]:
        raise RuntimeError("磁碟獨立枚舉與指定 commit 的完整來源集合不同")
    paths = before["paths"] + list(TOOLS)
    if any(objects[p][0] not in {"100644", "100755"} or objects[p][1] != "blob" for p in paths):
        raise RuntimeError("來源或裁判不是一般 Git blob")
    result = subprocess.run(["git", "-C", str(root), "cat-file", "--batch"],
                            input="".join(objects[p][2] + "\n" for p in paths).encode(),
                            capture_output=True, check=True).stdout
    offset = 0
    for p in paths:
        end = result.index(b"\n", offset)
        object_id, kind, size = result[offset:end].split()
        start, size = end + 1, int(size)
        raw = result[start:start + size]
        offset = start + size + 1
        if kind != b"blob" or sha(raw.replace(b"\r\n", b"\n")) != hashes((root / p).read_bytes())["lfSha256"]:
            raise RuntimeError("來源與指定 commit 不符: " + p)
    if offset != len(result):
        raise RuntimeError("Git blob 解析未完整消耗資料")


def test_counts(stdout, stderr):
    text = (stdout + stderr).decode("utf-8", "replace")
    ran = re.search(r"^Ran (\d+) tests? in ([\d.]+)s$", text, re.M)
    ok = re.search(r"^OK(?: \(skipped=(\d+)\))?$", text, re.M)
    if not ran or not ok:
        raise RuntimeError("unittest 未提供完整成功摘要")
    total, skipped = int(ran.group(1)), int(ok.group(1) or 0)
    return {"tests": total, "passed": total - skipped, "failed": 0, "skipped": skipped,
            "unittestSeconds": float(ran.group(2)),
            "skipLines": [line for line in text.splitlines() if "... skipped " in line]}


def parse_review(value):
    if not isinstance(value, dict) or not value:
        raise RuntimeError("審閱檔須為非空 JSON 物件")
    if set(value) <= {"updatedExclusions", "addedExclusions"}:
        updated, added = value.get("updatedExclusions", {}), value.get("addedExclusions", {})
    else:
        updated, added = value, {}
    for entries in (updated, added):
        if not isinstance(entries, dict) or not all(isinstance(p, str) and isinstance(reason, str) and reason.strip()
                                                  for p, reason in entries.items()):
            raise RuntimeError("每個審閱欄位須明列路徑及非空理由")
    if not updated and not added:
        raise RuntimeError("沒有指定任何刷新項目")
    if set(updated) & set(added):
        raise RuntimeError("同一路徑不能同時是既有與新增排除項目")
    for p in added:
        path = Path(p)
        if path.as_posix() != p or path.parent.as_posix() != ADDED_DIRECTORY or path.suffix.lower() not in SUFFIXES:
            raise RuntimeError("新增排除項目只准指定收尾工具目錄的直接可執行子檔: " + p)
        if not re.search(r"[\u3400-\u9fff]", added[p]):
            raise RuntimeError("新增排除項目需要繁中審閱理由: " + p)
    return updated, added


def dependency_probe(root, manifest_path, target):
    """只在記憶體補一條具體 H 依賴，要求 scanner 拒絕排除檔；不執行該依賴。"""
    root = Path(root).resolve()
    spec = importlib.util.spec_from_file_location("geo261_architecture_probe_scanner", root / TOOLS[0])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    manifest = module.load_manifest(manifest_path)
    source = "geometry-app/application.js"
    entry = next(row for row in manifest["sources"] if row["path"] == source)
    if entry["layer"] != "H" or entry["language"] != "javascript":
        raise RuntimeError("依賴負控制的實際 H 來源分類已變")
    scanner = module.Scanner(root, manifest)
    try:
        scanner.validate_manifest()
        original = (root / source).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        scanner.scan_javascript(source, original + "\nrequire(" + json.dumps("../" + target) + ");\n")
    except module.ContractError as error:
        scanner.result.diagnostics.append(error.diagnostic)
    print(json.dumps(scanner.result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if scanner.result.ok else 1


class AuditOutputs:
    """鎖住每階段的稽核 bytes；失敗時只還原仍由本次 driver 持有的變更。"""
    def __init__(self, root, out):
        self.root, self.out = root, out
        self.prior = {p: (root / p).read_bytes() for p in OUTPUTS}
        self.expected = dict(self.prior)
        self.active = False

    def __enter__(self):
        return self

    def verify(self):
        for p, raw in self.expected.items():
            if (self.root / p).read_bytes() != raw:
                raise RuntimeError("稽核產物被外部改變: " + p)

    def write(self, p, raw):
        self.verify()
        (self.root / p).write_bytes(raw)
        self.expected[p] = raw

    def write_json(self, p, value):
        self.write(p, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())

    def __exit__(self, kind, error, traceback):
        if error is not None and self.active:
            restored, externally_changed = [], []
            for p, raw in self.prior.items():
                try:
                    current = (self.root / p).read_bytes()
                except OSError:
                    externally_changed.append(p)
                    continue
                if current == self.expected[p]:
                    if current != raw:
                        try:
                            (self.root / p).write_bytes(raw)
                            restored.append(p)
                        except OSError:
                            externally_changed.append(p)
                elif current != raw:
                    externally_changed.append(p)
            dump(self.out / "failure.json", {"complete": False, "error": str(error),
                 "restoredOutputs": restored, "externalChangesNotOverwritten": externally_changed,
                 "note": "失敗日誌保留；只還原仍與本次 driver 預期 bytes 相同的產物，外部更動不覆寫。"})
        return False


def main():
    if len(sys.argv) == 5 and sys.argv[1] == "--probe-owned-dependency":
        return dependency_probe(*sys.argv[2:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--review-file", type=Path, required=True,
                        help="JSON 含 updatedExclusions／addedExclusions；各為明列路徑對繁中審閱理由")
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    if out == root or root in out.parents:
        raise RuntimeError("證據目錄必須在 repository 外")
    with AuditOutputs(root, out) as guard:
        return refresh(args, root, out, guard)


def refresh(args, root, out, guard):
    out.mkdir(parents=True, exist_ok=False)
    guard.active = True
    head = git(root, "rev-parse", "HEAD").decode().strip()
    if head != args.source_head or not re.fullmatch(r"[0-9a-f]{40}", head):
        raise RuntimeError("必須指定目前完整 HEAD；不能在驗證中切換版本")
    prior = guard.prior
    for p, raw in prior.items():
        committed = git(root, "show", head + ":" + p)
        if hashes(raw)["lfSha256"] != hashes(committed)["lfSha256"]:
            raise RuntimeError("起始稽核產物與指定 HEAD 不同，需先提交及審閱: " + p)
        (out / "previous").mkdir(exist_ok=True)
        (out / "previous" / Path(p).name).write_bytes(raw)
    previous_receipt = json.loads(prior[OUTPUTS[3]])
    manifest = json.loads(prior[OUTPUTS[0]])
    if set(manifest["sourceRoots"]) != set(ROOTS) or set(manifest["sourceFiles"]) != set(STANDALONE):
        raise RuntimeError("來源範圍已變，需要重新審閱 driver")
    review = json.loads(args.review_file.read_bytes())
    reviewed_updates, reviewed_additions = parse_review(review)
    dump(out / "review.json", review)
    before = snapshot(root)
    assert_git_source(root, head, before)
    declared = sorted(entry["path"] for entry in manifest["sources"] + manifest["exclusions"])
    if len(set(declared)) != len(declared):
        raise RuntimeError("既有來源清單有重複路徑")
    missing = set(declared) - set(before["paths"])
    unregistered = set(before["paths"]) - set(declared)
    if missing or unregistered != set(reviewed_additions):
        raise RuntimeError("來源新增／遺漏與明列新增項目不同: " + json.dumps({"missing": sorted(missing), "unregistered": sorted(unregistered)}, ensure_ascii=False))
    exclusions = {entry["path"]: entry for entry in manifest["exclusions"]}
    changed = []
    for p, reason in reviewed_updates.items():
        if p not in exclusions or exclusions[p].get("hashMode") != "lf":
            raise RuntimeError("只接受既有且明示 LF 雜湊的 exclusion: " + p)
        current = before["sources"][p]["lfSha256"]
        if current == exclusions[p]["sha256"]:
            raise RuntimeError("指定項目的 digest 未變，不需刷新: " + p)
        changed.append({"path": p, "previousSha256": exclusions[p]["sha256"],
                        "currentSha256": current, "reviewReason": reason})
    for p, entry in exclusions.items():
        mode = "lfSha256" if entry.get("hashMode") == "lf" else "rawSha256"
        if entry["sha256"] != before["sources"][p][mode] and p not in reviewed_updates:
            raise RuntimeError("另有未審閱的 exclusion digest 變更: " + p)
    added = [{"path": p, "reason": reason, "sha256": before["sources"][p]["lfSha256"], "hashMode": "lf"}
             for p, reason in sorted(reviewed_additions.items())]
    inputs, closure_sha = closure(before["sources"])
    _, raw_closure_sha = closure(before["sources"], "rawSha256")
    previous_inputs = {row["path"]: row["sha256"] for row in previous_receipt["inputs"]}
    changed_since_seal = [{"path": p, "previousSha256": previous_inputs.get(p),
                          "currentSha256": value["lfSha256"]} for p, value in before["sources"].items()
                         if previous_inputs.get(p) != value["lfSha256"]]

    def assert_frozen():
        guard.verify()
        if git(root, "rev-parse", "HEAD").decode().strip() != head or snapshot(root) != before:
            raise RuntimeError("驗證期間 HEAD、來源集合、來源或裁判 bytes 改變")

    def execute(name, argv):
        assert_frozen()
        folder = out / name
        folder.mkdir()
        start, start_time = time.monotonic(), utc()
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        with (folder / "stdout.log").open("wb") as stdout, (folder / "stderr.log").open("wb") as stderr:
            try:
                proc = subprocess.run(argv, cwd=root, env=env, stdout=stdout, stderr=stderr, timeout=900)
                code, complete = proc.returncode, True
            except subprocess.TimeoutExpired:
                code, complete = 124, False
        raw_stdout, raw_stderr = (folder / "stdout.log").read_bytes(), (folder / "stderr.log").read_bytes()
        record = {"command": shlex.join(argv), "argv": argv, "cwd": str(root), "sourceBaseHead": head,
                  "startedUtc": start_time, "finishedUtc": utc(), "seconds": round(time.monotonic() - start, 3),
                  "complete": complete, "exitCode": code,
                  "stdout": {"path": f"{name}/stdout.log", **hashes(raw_stdout)},
                  "stderr": {"path": f"{name}/stderr.log", **hashes(raw_stderr)}}
        dump(folder / "result.json", record)
        assert_frozen()
        print(json.dumps({"項目": name, "結束碼": code, "秒數": record["seconds"]}, ensure_ascii=False), flush=True)
        return record, raw_stdout, raw_stderr

    cli = [sys.executable, "-B", TOOLS[0], "--root", ".", "--manifest", OUTPUTS[0]]
    prior_check, prior_stdout, _ = execute("prior-manifest", cli)
    prior_scan = json.loads(prior_stdout)
    expected_causes = {("EXCLUSION_DIGEST", p) for p in reviewed_updates} | {("SOURCE_UNREGISTERED", p) for p in reviewed_additions}
    if prior_check["exitCode"] != 1 or not any((d["code"], d["path"]) in expected_causes for d in prior_scan["diagnostics"]):
        raise RuntimeError("舊 manifest 未以明列 digest 失配或來源缺登記轉紅，不能宣稱負控制成功")
    for row in changed:
        exclusions[row["path"]]["sha256"] = row["currentSha256"]
    manifest["exclusions"].extend(added)
    exclusions.update({entry["path"]: entry for entry in added})
    guard.write_json(OUTPUTS[0], manifest)
    scan_record, scan_stdout, _ = execute("actual-cli-scan", cli)
    scanned = json.loads(scan_stdout)
    if scan_record["exitCode"] != 0 or not scanned.get("ok") or scanned["diagnostics"]:
        raise RuntimeError("新版 manifest 架構掃描未通過")
    guard.write(OUTPUTS[1], scan_stdout)
    validation = []
    for name, tool in (("generic-tests", TOOLS[1]), ("product-tests", TOOLS[2])):
        record, stdout, stderr = execute(name, [sys.executable, "-B", tool])
        if record["exitCode"] != 0:
            raise RuntimeError(name + " 未通過")
        record.update(test_counts(stdout, stderr), sha256=before["tools"][tool]["lfSha256"], executedAtCurrentHead=True)
        dump(out / name / "result.json", record)
        validation.append(record)
    controls = []
    for index, row in enumerate(changed):
        mutant = json.loads(json.dumps(manifest))
        next(entry for entry in mutant["exclusions"] if entry["path"] == row["path"])["sha256"] = row["previousSha256"]
        mutant_path = out / f"withdraw-digest-{index}.json"
        dump(mutant_path, mutant)
        record, stdout, _ = execute(f"withdraw-digest-{index}", cli[:-1] + [str(mutant_path)])
        diagnostics = json.loads(stdout)["diagnostics"]
        if record["exitCode"] != 1 or not any(d["path"] == row["path"] and d["code"] == "EXCLUSION_DIGEST" for d in diagnostics):
            raise RuntimeError("撤回 digest 修正未以正確病因轉紅: " + row["path"])
        controls.append({**record, "target": row["path"], "expectedExitCode": 1, "diagnostics": diagnostics, "killed": True})
    for index, row in enumerate(added):
        mutant = json.loads(json.dumps(manifest))
        mutant["exclusions"] = [entry for entry in mutant["exclusions"] if entry["path"] != row["path"]]
        mutant_path = out / f"withdraw-registration-{index}.json"
        dump(mutant_path, mutant)
        record, stdout, _ = execute(f"withdraw-registration-{index}", cli[:-1] + [str(mutant_path)])
        diagnostics = json.loads(stdout)["diagnostics"]
        if record["exitCode"] != 1 or not any(d["path"] == row["path"] and d["code"] == "SOURCE_UNREGISTERED" for d in diagnostics):
            raise RuntimeError("撤回新工具登記未以正確病因轉紅: " + row["path"])
        controls.append({**record, "target": row["path"], "expectedExitCode": 1, "diagnostics": diagnostics, "killed": True})
        mutant = json.loads(json.dumps(manifest))
        entry = next(entry for entry in mutant["exclusions"] if entry["path"] == row["path"])
        entry["sha256"] = ("1" if entry["sha256"][0] == "0" else "0") + entry["sha256"][1:]
        mutant_path = out / f"corrupt-new-digest-{index}.json"
        dump(mutant_path, mutant)
        record, stdout, _ = execute(f"corrupt-new-digest-{index}", cli[:-1] + [str(mutant_path)])
        diagnostics = json.loads(stdout)["diagnostics"]
        if record["exitCode"] != 1 or not any(d["path"] == row["path"] and d["code"] == "EXCLUSION_DIGEST" for d in diagnostics):
            raise RuntimeError("破壞新工具 digest 未以正確病因轉紅: " + row["path"])
        controls.append({**record, "target": row["path"], "expectedExitCode": 1, "diagnostics": diagnostics, "killed": True})
        record, stdout, _ = execute(f"owned-dependency-{index}", [sys.executable, "-B", str(Path(__file__).resolve()),
                                           "--probe-owned-dependency", str(root), str(root / OUTPUTS[0]), row["path"]])
        diagnostics = json.loads(stdout)["diagnostics"]
        if record["exitCode"] != 1 or not any(d["code"] == "DEPENDENCY_EXCLUDED" and d.get("chain") == ["geometry-app/application.js", row["path"]] for d in diagnostics):
            raise RuntimeError("具體 H 來源依賴新排除工具時未被拒絕: " + row["path"])
        controls.append({**record, "target": row["path"], "expectedExitCode": 1, "diagnostics": diagnostics, "killed": True,
                         "scope": "實際 H 來源文字加上記憶體內靜態 require；不寫回產品，不聲稱該跨語言依賴可於執行期載入。"})
    counts = {"executableFiles": len(inputs), "ownedSources": len(manifest["sources"]),
              "exclusions": len(exclusions), "edges": len(scanned["edges"]), "diagnostics": len(scanned["diagnostics"]),
              "layers": dict(sorted(Counter(e["layer"] for e in manifest["sources"]).items())),
              "languages": dict(sorted(Counter(e["language"] for e in manifest["sources"]).items())),
              "forbiddenIdentifiers": len(manifest["policy"]["forbiddenIdentifiers"]),
              "forbiddenStrings": len(manifest["policy"]["forbiddenStrings"])}
    report = prior[OUTPUTS[2]].decode("utf-8").replace("\r\n", "\n")
    old_summary = re.compile(r"At the latest sealed source HEAD `[^`]+`, the\n.*?finite refresh\.\n|本次最新封存來源為 `[^`]+`。.*?封存前均保持一致。\n", re.S)
    generic, product = validation
    summary = (f"本次最新封存來源為 `{head}`。實際 CLI 掃描結束碼為 0，"
               f"含 {counts['ownedSources']} 個登記來源、{counts['edges']} 條依賴邊及 0 項診斷。\n"
               f"通用掃描器測試 {generic['tests']} 項：通過 {generic['passed']}、略過 {generic['skipped']}；"
               f"產品架構測試 {product['tests']} 項：通過 {product['passed']}、略過 {product['skipped']}。\n"
               f"獨立枚舉核對全部 {len(inputs)} 個來源的 LF 雜湊與指定 Git commit；"
               "來源集合、來源／裁判 bytes 及 HEAD 在每條命令後和封存前均保持一致。\n")
    report, replacements = old_summary.subn(lambda _: summary, report)
    if replacements != 1:
        raise RuntimeError("舊報告的最新來源段落錨點不唯一，請人工審閱")
    inventory_sentence = re.compile(r"The current inventory contains \d+ executable files: \d+ owned sources and \d+\nindividually named exclusions\.|目前清單含 \d+ 個可執行檔案：\d+ 個登記來源與 \d+ 個逐檔排除項目。")
    report, replacements = inventory_sentence.subn(
        f"目前清單含 {counts['executableFiles']} 個可執行檔案：{counts['ownedSources']} 個登記來源與 {counts['exclusions']} 個逐檔排除項目。", report)
    if replacements != 1:
        raise RuntimeError("舊報告的現行檔案數量段落錨點不唯一，請人工審閱")
    if added:
        report = report.replace("There are 120 historical evidence programs,\n57 other documentation/reproduction/snapshot/GEO-262/framing-template tooling programs, 66 dedicated test drivers,\nand 25 engineering-spec prototype files.",
                                "前次封存清單的分類為 120 個歷史證據程式、57 個其他文件／重現／快照／GEO-262／framing 工具、66 個專用測試驅動器及 25 個工程規格原型檔；後續明列新增的收尾工具見本報告末尾各次刷新紀錄。")
    listed = [f"- 既有 digest 更新 `{r['path']}`：{r['reviewReason']}" for r in changed]
    listed += [f"- 新增逐檔工具排除 `{r['path']}`：{r['reason']}" for r in added]
    prior_diagnostics = "、".join(sorted({d["code"] for d in prior_scan["diagnostics"]}))
    appendix = ("\n## 2026-10-21 Linux 有限刷新\n\n"
                f"來源 SHA：`{head}`。本次 manifest 刷新只更新以下已審閱的既有排除項目雜湊，以及逐檔明列的收尾驗證工具；"
                "實際來源變化由收據 `inputsChangedSincePreviousSeal` 逐項列出。"
                "既有來源責任分類、來源根目錄、獨立來源名單及守門政策維持既有內容。\n\n" +
                "\n".join(listed) +
                f"\n\n舊 manifest 以 `{prior_diagnostics}` 轉紅；新版掃描及兩套測試均實際重跑。"
                "既有 digest 更新逐項撤回時須以目標檔案的 `EXCLUSION_DIGEST`、結束碼 1 拒絕。"
                "新增工具逐項移除登記時須以 `SOURCE_UNREGISTERED`、結束碼 1 拒絕；"
                "逐項破壞新工具 digest 時須以 `EXCLUSION_DIGEST`、結束碼 1 拒絕；"
                "再以實際 H 來源文字於記憶體加入對每個新工具的靜態依賴，須以 `DEPENDENCY_EXCLUDED`、結束碼 1 拒絕。"
                "上述是架構清單的突變自證，不冒充產品修正的行為突變自證。\n\n"
                "四份舊產物逐位元組保存在外部證據目錄的 `previous/`；新收據記錄舊產物雜湊、原來源 SHA、"
                "本次完整輸入閉包、命令、結束碼、略過項及原始日誌雜湊。此處只驗靜態依賴；"
                "未執行原生、瀏覽器、Q38、卡片參照或 P-189 驗收，不能由本收據推定那些關卡通過。\n")
    guard.write(OUTPUTS[2], (report.rstrip() + "\n" + appendix).encode())
    assert_frozen()
    receipt = {
        "schema": "geometry-product-architecture-receipt/1",
        "headBinding": "來源閉包排除四份衍生稽核產物；後續只提交稽核產物不會遞迴改變已驗證的產品輸入。",
        "hashMode": "sha256 after CRLF-to-LF normalization",
        "inputClosureHashSerialization": "依 path 排序的 inputs 陣列，以 UTF-8 JSON、ensure_ascii=false、separators=(comma,colon)、無尾端換行計算 SHA-256；欄位順序為 path、sha256。",
        "inputClosureExcludes": list(OUTPUTS),
        "inputClosureExclusionReason": "四檔是非可執行稽核產物；manifest、scan、report 另記雜湊，收據不雜湊自身。",
        "notClaimed": ["原生編譯或執行", "執行期匯入阻擋", "一般 JavaScript 別名／資料流證明", "vendor 內部驗證", "全部 H 函式皆無錯放政策的獨立證明", "未來變更後的來源樹", "Q38、§7、P-189 或瀏覽器驗收"],
        "createdUtc": utc(), "basis": "已提交指定來源 HEAD，加上本次有限 manifest／scan／report／receipt 刷新。",
        "sourceBaseHead": head, "headObservedBefore": head, "headObservedAfter": head,
        "manifestSha256": hashes((root / OUTPUTS[0]).read_bytes())["lfSha256"],
        "scannerSha256": before["tools"][TOOLS[0]]["lfSha256"],
        "scanSha256": hashes((root / OUTPUTS[1]).read_bytes())["lfSha256"],
        "reportSha256": hashes((root / OUTPUTS[2]).read_bytes())["lfSha256"],
        "inputClosureSha256": closure_sha, "counts": counts,
        "manifestRefresh": {"previousOutputs": {p: {"preservedPath": "previous/" + Path(p).name, **hashes(raw)} for p, raw in prior.items()},
                            "previousSourceBaseHead": previous_receipt["sourceBaseHead"], "previousReceiptCreatedUtc": previous_receipt["createdUtc"],
                            "updatedExclusions": changed, "addedSources": [], "addedExclusions": added, "priorManifestCheck": prior_check,
                            "inputsChangedSincePreviousSeal": changed_since_seal},
        "scanPassed": True, "actualCliScan": scan_record, "validation": validation,
        "supplementalStaticGuardProbes": controls,
        "nativeAcceptance": "本次只執行靜態架構掃描及其測試；沒有執行原生、瀏覽器或效能驗收。",
        "inputs": inputs,
        "completeInventoryVerification": {"method": "獨立 os.walk 枚舉固定五個來源根目錄及三個獨立檔案，再與 git ls-tree／cat-file 的指定 commit 逐項核對；每條命令後重算所有來源與裁判 raw／LF bytes 雜湊。",
                                          "sourceRoots": list(ROOTS), "sourceFiles": list(STANDALONE), "executableSuffixes": sorted(SUFFIXES),
                                          "filesBefore": len(inputs), "filesAfter": len(inputs), "unregisteredAfter": [], "missingAfter": [], "changedInputs": [],
                                          "inputClosureSha256Before": closure_sha, "inputClosureSha256After": closure_sha,
                                          "rawInputClosureSha256Before": raw_closure_sha, "rawInputClosureSha256After": raw_closure_sha,
                                          "toolHashesBeforeAndAfter": before["tools"], "sourceHashesBeforeAndAfter": before["sources"],
                                          "headObservedAfterIndependentAudit": head, "checkedUtc": utc()},
        "refreshDriver": {"path": str(Path(__file__).resolve()), **hashes(Path(__file__).read_bytes()),
                          "argv": sys.argv, "evidenceDirectory": str(out), "reviewFile": str(args.review_file.resolve())}}
    guard.write_json(OUTPUTS[3], receipt)
    assert_frozen()
    for p in OUTPUTS:
        (out / "final").mkdir(exist_ok=True)
        (out / "final" / Path(p).name).write_bytes((root / p).read_bytes())
    dump(out / "summary.json", {"sourceHead": head, "exitCode": 0, "counts": counts,
                               "outputs": {p: hashes((root / p).read_bytes()) for p in OUTPUTS},
                               "validation": validation, "controls": controls})
    print(json.dumps({"完成": True, "來源SHA": head, "證據目錄": str(out)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
