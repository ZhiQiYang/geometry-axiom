#!/usr/bin/env python3
"""Package eight freshly produced fact cases; never invent native models."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from native_reproduce import BASE, verify_base_sources


def digest_bytes(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args()
    repo, artifacts, fixture = args.repo.resolve(), args.artifacts.resolve(), args.fixture.resolve()
    observed_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, timeout=10, text=True).strip()
    existing = set(verify_base_sources(repo))
    build = read(artifacts / "build.json")
    assert build["base"] == BASE
    inputs = {"tests/binaries.py"}
    for binary in build["binaries"]:
        assert binary["result"]["status"] in ("built", "reused")
        inputs.update(binary["fingerprint"]["files"])
    # Conservative source closure: all existing producer/model-host Python and
    # existing runtime JS in the relevant layers, plus the exact native registry.
    for name in existing:
        path = Path(name)
        if path.suffix == ".py" and (name.startswith(("geometry-core/modeling/", "geometry-app/", "geometry-templates/")) or name.startswith("geometry-web/") and len(path.parts) == 2):
            inputs.add(name)
        if path.suffix == ".js" and (name.startswith(("geometry-app/", "geometry-templates/")) or name.startswith(("geometry-core/", "geometry-web/")) and len(path.parts) == 2 and not path.name.endswith("_test.js")):
            inputs.add(name)
    inputs.add("geometry-web/vendor/fflate/umd/index.js")
    source_inputs = {}
    for name in sorted(inputs):
        assert name in existing, ("U476_INPUT_NOT_AT_BASE", name)
        source_inputs[name] = digest_bytes((repo / name).read_bytes().replace(b"\r\n", b"\n"))
    for binary in build["binaries"]:
        for name, expected in binary["fingerprint"]["files"].items():
            assert source_inputs[name]["sha256"] == expected, ("U476_NATIVE_INPUT_CHANGED_SINCE_BUILD", name)
    summary = read(artifacts / "facts/summary.json")
    cases = []
    for case in summary["cases"]:
        raw = artifacts / "facts" / (case["name"] + ".input.json")
        assert digest_bytes(raw.read_bytes())["sha256"] == case["inputSha256"]
        data = read(raw)
        assert data["studySchema"] == "U476-facts/1"
        complete = case["expectedStatus"] == "COMPLETE"
        cases.append({"name": case["name"], "input": data, "expected": {
            "status": case["expectedStatus"], "itemCount": case["physicalSources"] if complete else None,
            "physicalItemLengthMm": 4000 * case["physicalSources"] if complete else None,
            "rawRows": case["representations"]}, "rawInput": digest_bytes(raw.read_bytes())})
    assert len(cases) == 8
    scripts = {path.name: digest_bytes(path.read_bytes()) for path in sorted(Path(__file__).parent.iterdir())
               if path.name in ("native_reproduce.py", "native_consume.cjs", "native_projection.py", "native_cutting_projection.cjs", "native_root_probe.py", "native_root_withdrawal.py", "native_fixture.py")}
    receipt_names = ["build.receipt.json", "native-run.receipt.json", "consume.receipt.json", "projection.receipt.json", "native-root-probe.receipt.json"]
    receipts = {}
    for name in receipt_names:
        value = read(artifacts / name)
        assert value["exit"] == 0 and value["timedOut"] is False
        receipts[name] = {"receipt": digest_bytes((artifacts / name).read_bytes()),
                          "command": value["command"], "exit": value["exit"],
                          "stdout": value["stdout"], "stderr": value["stderr"]}
    value = {"schema": "U476-native-fixture/1", "base": BASE, "observedHead": observed_head, "researchOnly": True,
             "sourceInputNormalization": "CRLF-to-LF; bytes and SHA-256 are both over normalized source bytes",
             "sourceInputs": source_inputs, "generatorScripts": scripts, "nativeReceipts": receipts,
             "limits": {"ownerContext": summary["contextLimit"], "nativeSources": summary["sourceLimit"],
                        "formalCuttingPlan2": False, "formalProjectTakeoffAttachment": False,
                        "newHostEpochOnEachRun": True, "candidateReplayMarksUsed": False},
             "cases": cases}
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    info = digest_bytes(fixture.read_bytes())
    provenance = fixture.with_suffix(".provenance.md")
    lines = ["# U476 真 native 研究夾具來源", "", f"固定來源基底：`{BASE}`；本次觀察 HEAD：`{observed_head}`。", "",
             f"夾具：`{fixture.name}`；{info['bytes']} bytes；SHA-256 `{info['sha256']}`。", "",
             "此八例由新編 bridge/model-base、真 space_modeling.preview、每包 verify_package、整筆 replay_stored、input/result 雙端 source-inspect-file、既有普通模型 pack/unpack 產生。沒有手寫模型成功結果，沒有改 source-inspector.js。", "",
             "每次重播由宿主新配隨機 epoch，故 incarnation 和夾具 bytes 可改；模型 pins 來自原 live graph，不取去身分 candidate 的記號。", "",
             "owner/project/scenario 是明示離線研究條件，不是正式 owner service；僅 literal A/B 普通已放置 D7 正例。新附件與 /2 未接線；既有 /1 的 saved-model/union 仍回 WORLD_KIND。", "",
             "## 從 repository 根重播", "", "```sh",
             "python geometry-core/timber-takeoff/research/native_reproduce.py --repo . --out /tmp/u476-native-fresh --candidate geometry-core/timber-takeoff/research/candidate.cjs --fixture tests/fixtures/r05_takeoff_native.json",
             "python geometry-core/timber-takeoff/research/native_root_withdrawal.py --native-artifacts /tmp/u476-native-fresh --out /tmp/u476-raw-root-withdrawal", "```", "",
             "sourceInputs 包含原 binary registry 的 C 閉包與 producer/host JS/Python 保守閉包，全部取自固定基底已有檔案；新增研究檔不免除任何既有來源變更。sourceInputNormalization 明示跨平台行尾處理，不能只核對 fixture 自己的 JSON。", "",
             "BASE 物件必須可讀。套用研究 T/P 後 HEAD 可以前進，但 pinned BASE inventory 中每個既有檔案仍須完全通過 git diff BASE；再核 binary fingerprint 與 source byte pins。若 #472 改變任何既有來源，重播即拒絕，不得只刷新 pin 續綠。", "",
             "## 本次原始命令與輸出", ""]
    for name in receipt_names:
        receipt = read(artifacts / name)
        stem = name.removesuffix(".receipt.json")
        output = (artifacts / (stem + ".stdout.txt")).read_text(encoding="utf-8")
        lines.extend([f"### {stem}", "", "```text", json.dumps(receipt["command"], ensure_ascii=False),
                      f"exit={receipt['exit']}; timeout={receipt['timeoutSeconds']} seconds; timedOut={receipt['timedOut']}",
                      output.rstrip(), "```", ""])
    provenance.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"fixture": str(fixture), **info, "cases": len(cases), "sourceInputs": len(source_inputs),
                      "generatorScripts": len(scripts), "provenance": str(provenance)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
