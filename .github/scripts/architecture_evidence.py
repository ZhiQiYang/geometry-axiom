"""在 CI 記錄原架構三命令，產出新來源的衍生資料；不改 scanner。"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "geometry-core/domain-decoupling/product-architecture.json"
MAIN = "8f82b207e87c086705a1d8b7a00e2f215c07cbcf"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT, check=True)
    commands = [
        ("architecture-cli", [sys.executable, "-B", "tests/architecture_contract.py", "--root", ".", "--manifest", MANIFEST]),
        ("architecture-unit", [sys.executable, "-B", "tests/test_architecture_contract.py"]),
        ("architecture-product", [sys.executable, "-B", "tests/test_product_architecture.py"]),
    ]
    receipt = {"schema": "geometry-architecture-ci-receipt/1", "sourceHead": head,
               "adoptedMain": MAIN, "runId": os.environ.get("GITHUB_RUN_ID"),
               "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT"), "complete": False, "commands": []}
    for label, command in commands:
        stdout, stderr = out / (label + ".stdout"), out / (label + ".stderr")
        with stdout.open("wb") as output, stderr.open("wb") as errors:
            process = subprocess.run(command, cwd=ROOT, stdout=output, stderr=errors)
        raw_out, raw_err = stdout.read_bytes(), stderr.read_bytes()
        print(raw_out.decode("utf-8", errors="replace"), end="", flush=True)
        print(raw_err.decode("utf-8", errors="replace"), end="", file=sys.stderr, flush=True)
        row = {"label": label, "command": ["<python>", *command[1:]], "cwd": "<repo>",
               "exitCode": process.returncode, "stdout": stdout.name, "stderr": stderr.name,
               "stdoutSha256": digest(raw_out), "stderrSha256": digest(raw_err)}
        if label != "architecture-cli":
            match = re.search(rb"Ran (\d+) tests? in ", raw_err)
            if match is None or int(match[1]) == 0 or re.search(rb"\bskipped=[1-9]\d*", raw_err):
                row["completenessProblem"] = "未找到完整非零 unittest 計數，或含 skip"
            else:
                row["testsRun"] = int(match[1])
        receipt["commands"].append(row)
        save(out / "product-architecture-receipt.json", receipt)
        if process.returncode != 0 or "completenessProblem" in row:
            raise RuntimeError("原架構命令未完整通過：" + label)

    scan_bytes = (out / "architecture-cli.stdout").read_bytes()
    subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT, check=True)
    scan = json.loads(scan_bytes)
    if scan.get("ok") is not True or scan.get("diagnostics") != []:
        raise RuntimeError("原 scanner 未回報零 diagnostics")
    (out / "product-architecture-scan.json").write_bytes(scan_bytes)
    manifest_bytes = (ROOT / MANIFEST).read_bytes().replace(b"\r\n", b"\n")
    manifest = json.loads(manifest_bytes)
    inputs = []
    for entry in manifest["sources"] + manifest["exclusions"]:
        path = entry["path"]
        inputs.append({"path": path, "lfSha256": digest((ROOT / path).read_bytes().replace(b"\r\n", b"\n"))})
    inputs.sort(key=lambda entry: entry["path"])
    receipt.update({"complete": True, "manifestLfSha256": digest(manifest_bytes),
                    "scannerLfSha256": digest((ROOT / "tests/architecture_contract.py").read_bytes().replace(b"\r\n", b"\n")),
                    "testScriptsLfSha256": {command[2]: digest((ROOT / command[2]).read_bytes().replace(b"\r\n", b"\n"))
                                            for _, command in commands[1:]},
                    "scanSha256": digest(scan_bytes), "ownedCount": len(manifest["sources"]),
                    "exclusionCount": len(manifest["exclusions"]), "edgeCount": len(scan["edges"]),
                    "diagnosticCount": 0, "inputs": inputs,
                    "inputLfClosureSha256": digest("\n".join(entry["path"] + " " + entry["lfSha256"] for entry in inputs).encode("utf-8"))})
    save(out / "product-architecture-receipt.json", receipt)
    layers = Counter(entry["layer"] for entry in manifest["sources"])
    rows = "\n".join("| " + layer + " | " + str(count) + " |" for layer, count in sorted(layers.items()))
    tests = "、".join(row["label"] + "=" + str(row["testsRun"]) for row in receipt["commands"] if "testsRun" in row)
    report = (
        "# Product architecture — GitHub 新來源收據\n\n"
        f"來源 `{head}`；採入 main `{MAIN}`；Actions run `{receipt['runId']}`。\n\n"
        "這份衍生資料來自原 scanner CLI 與原兩支 unittest 的實際執行；三命令均 exit 0、零 skip。"
        "它只證明靜態依賴契約，不能替代演算法責任審查、原生／突變／瀏覽器或 SSOT 驗證。\n\n"
        f"本次 {len(inputs)} inputs、{receipt['ownedCount']} owned、{receipt['exclusionCount']} exclusions、"
        f"{receipt['edgeCount']} edges、0 diagnostics；{tests}。完整命令、原始輸出與雜湊在同 artifact。\n\n"
        "| Layer | Sources |\n|---|---:|\n" + rows + "\n\n"
        f"main 的歷史收據保留在 Git `{MAIN}`，本次沒有改寫其來源或沿用其綠燈。\n"
    )
    (out / "PRODUCT-ARCHITECTURE.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out.resolve())
