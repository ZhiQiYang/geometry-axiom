"""Copy the evidence module and require each named removal to go red.

The workspace source is never modified. Node's spec reporter prints the named
failure with operator strictEqual; this probe does not look for TAP.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "geometry-web" / "evidence-links.js"
TEST = ROOT / "tests" / "test_evidence_ledger_links.js"
CASES = (
    {
        "needle": "/* ledger 不看租約 */",
        "mutant": "if(!options.identityKnown)return {status:'needs-reassociation',canConfirm:false}; /* 身分改回租約 */",
        "name": "撤掉實作：身分改回租約",
    },
    {
        "needle": "||current.target.valuePin!==link.target.valuePin",
        "mutant": "",
        "name": "撤掉實作：忽略有效值內容指紋",
    },
    {
        "needle": "if(!receipt||receipt.previewed!==true||receipt.confirmed!==true)fail('ADOPTION_PREVIEW','採用必須先預覽並確認。');",
        "mutant": "if(false)fail('ADOPTION_PREVIEW','採用必須先預覽並確認。');",
        "name": "撤掉實作：採用跳過預覽",
    },
    {
        "needle": "if(unit==='cm'){/* cm 精確乘十 */num*=10n;}",
        "mutant": "if(unit==='cm'){const n=Number(num)/Number(den)*10;return {num:String(n),den:'1'};}",
        "name": "撤掉實作：cm 用浮點",
    },
    {
        "needle": "await ledger.ensureActive(); /* 有預覽仍啟用 */",
        "mutant": "if(!ledger.previewPending)await ledger.ensureActive(); /* 有預覽仍啟用 */",
        "name": "撤掉實作：有預覽就拒絕啟用",
    },
)


def killed(combined: str, name: str) -> bool:
    section = combined.split("failing tests:", 1)[-1]
    start = section.find(name)
    if start < 0:
        return False
    nxt = section.find("\ntest at ", start + 1)
    chunk = section[start:] if nxt < 0 else section[start:nxt]
    return "operator: 'strictEqual'" in chunk


def run(copy: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["EVIDENCE_LINKS_MODULE"] = str(copy)
    return subprocess.run(
        ["node", "--test", str(TEST)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    text = SOURCE.read_text(encoding="utf-8")
    for case in CASES:
        if text.count(case["needle"]) != 1 or case["mutant"] and case["mutant"] in text:
            print("needle count", case["name"], text.count(case["needle"]))
            return 2
    with tempfile.TemporaryDirectory(prefix="geometry-evidence-ledger-mutation-") as directory:
        copy = Path(directory) / "evidence-links.js"
        copy.write_text(text, encoding="utf-8", newline="\n")
        baseline = run(copy)
        if baseline.returncode != 0:
            print(baseline.stdout)
            print(baseline.stderr, file=sys.stderr)
            print("baseline", baseline.returncode)
            return 1
        print("baseline", baseline.returncode)
        for case in CASES:
            copy.write_text(text.replace(case["needle"], case["mutant"], 1), encoding="utf-8", newline="\n")
            mutant = run(copy)
            combined = mutant.stdout + mutant.stderr
            if mutant.returncode == 0 or not killed(combined, case["name"]):
                print(mutant.stdout)
                print(mutant.stderr, file=sys.stderr)
                print("mutant", case["name"], mutant.returncode)
                return 1
            print("killed", case["name"])
        copy.write_text(text, encoding="utf-8", newline="\n")
        restored = run(copy)
        if restored.returncode != 0:
            print(restored.stdout)
            print(restored.stderr, file=sys.stderr)
            print("restore", restored.returncode)
            return 1
        print("restore", restored.returncode)
    print("PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
