"""突變檢查：證明 test_gen_scenes.py 有牙齒。純 Python，不跑核心、不碰 WSL、不改 repo。

做法：把 core-probe 與 oracle-golden.json 複製到暫存目錄，每次只套一個突變，
在複本裡跑 test_gen_scenes.py。對照組（不突變）必須全綠，每個突變都必須轉紅。
用法：python mutation_check.py [突變名稱 ...]    （不給名稱 = 全跑；加 --list 列出）

依 opus 審查（m1～m5）與 ChatGPT 審查（結束碼、幾何等值、已提交產物）補的牙齒都在這裡。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRAMING = HERE.parent  # framing-template


def replace_once(rel: str, old: str, new: str):
    def apply(root: Path) -> None:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"突變沒套上：{rel} 裡 {old!r} 出現 {text.count(old)} 次（要剛好 1 次）")
        path.write_bytes(text.replace(old, new).encode("utf-8"))

    return apply


def delete_file(rel: str):
    def apply(root: Path) -> None:
        (root / rel).unlink()

    return apply


def copy_file(src_rel: str, dst_rel: str):
    def apply(root: Path) -> None:
        shutil.copyfile(root / src_rel, root / dst_rel)

    return apply


def edit_bytes(rel: str, old: bytes, new: bytes):
    def apply(root: Path) -> None:
        path = root / rel
        data = path.read_bytes()
        if data.count(old) < 1:
            raise SystemExit(f"突變沒套上：{rel} 裡找不到 {old!r}")
        path.write_bytes(data.replace(old, new, 1))

    return apply


GEN = "gen_scenes.py"
PARSE = "parse_results.py"
SH = "run_probe.sh"

# (名稱, 說明, 套用函式, 是否要跑假核心腳本測試)
MUTATIONS = [
    ("m1", "custom priority 3→4（gen_scenes.assign_role）",
     replace_once(GEN, 'return "custom", 3, None, 3', 'return "custom", 4, None, 3'), False),
    ("m2", "格線中線 +1 mm（_grid_for）",
     replace_once(GEN, "center = wlo + width // 2\n", "center = wlo + width // 2 + 1\n"), False),
    ("m3", "孔邊料改成 primary（assign_role）",
     replace_once(GEN, 'return "secondary", None, "hole-perpendicular", 4',
                  'return "primary", None, "hole-perpendicular", 1'), False),
    ("m4", "拓撲排序取 min→max，副支先放（order_members）",
     replace_once(GEN, "pick = min(ready, key=lambda g: (by_golden[g].tier, g))",
                  "pick = max(ready, key=lambda g: (by_golden[g].tier, g))"), False),
    ("m5a", "刪掉已提交的 scenes/f1-00.scene",
     delete_file("scenes/f1-00.scene"), False),
    ("m5b", "改動已提交的 scenes/f2-00.scene（一個方向字元）",
     edit_bytes("scenes/f2-00.scene", b"-u +n", b"+u +n"), False),
    ("m5c", "index.json 過期（scene_count 64→63）",
     replace_once("index.json", '"scene_count": 64', '"scene_count": 63'), False),
    ("m5d", "scenes/ 多出一個不是產生的檔",
     copy_file("scenes/f1-00.scene", "scenes/zz-extra.scene"), False),
    ("m6", "跨距一律退成 through（長度不再由擋面決定）",
     replace_once(GEN, "if refs is not None and len(refs) == 2:", "if False and refs is not None and len(refs) == 2:"), False),
    ("m7", "擋面角材指錯一支（id+1）",
     replace_once(GEN, 'refs.append(f"t{timbers[0].id}")', 'refs.append(f"t{timbers[0].id + 1}")'), False),
    ("m8", "任何非 0 結束碼都算拒絕（parse_results.classify_rc）",
     replace_once(PARSE, 'if rc == CORE_REJECT_RC and is_rule_diagnostic(first_diagnostic(stderr or "")):', "if rc != 0:"), False),
    ("m9", "不比對核心 L 與 oracle 長邊（geometry_problems）",
     replace_once(PARSE, 'if info["length"] != long_side:', "if False:"), False),
    ("m10", "run_probe.sh 把任何非 0 都計成拒絕",
     replace_once(SH, 'elif [ "$one" -eq "$core_reject_rc" ] && rule_diag "$d/$k.err"; then', 'elif [ "$one" -ne 0 ]; then'), True),
    ("m11", "parse_results.main 有錯誤列也回 0",
     replace_once(PARSE, "        return EXIT_PROBE_ERRORS", "        return 0"), False),
    ("m12", "產生器忽略 golden 的 :custom4 標籤（副支一律 secondary）",
     replace_once(GEN, "base_kind, labelled = split_custom4(kind)", "base_kind, labelled = split_custom4(kind)[0], False"), False),
    ("m13", "升格過頭：所有副支都改 custom 4",
     replace_once(GEN, "        if labelled:\n", '        if labelled or role == "secondary":\n'), False),
    ("m14", "關掉標籤與實際擋面的交叉核對（custom4_disagreements 永遠不報）",
     replace_once(GEN, "if on_custom != member.custom4_label:", "if False:"), False),
    ("m15", "升格後的優先級寫成 5",
     replace_once(GEN, "SECONDARY_ON_CUSTOM_PRIORITY = 4", "SECONDARY_ON_CUSTOM_PRIORITY = 5"), False),
    ("m16", "golden 少標一個 :custom4（標籤與實際擋面不一致）",
     edit_bytes("../oracle/oracle-golden.json", b'"secondary:mark:custom4"', b'"secondary:mark"'), False),
    ("m17", "golden 多標一個 :custom4（該支端面沒有頂到 custom）",
     edit_bytes("../oracle/oracle-golden.json", b'"secondary:seam"', b'"secondary:seam:custom4"'), False),
    ("m18", "結束碼 1 一律算規則拒絕，不看 stderr 有沒有規則診斷（parse_results.classify_rc）",
     replace_once(PARSE, 'if rc == CORE_REJECT_RC and is_rule_diagnostic(first_diagnostic(stderr or "")):',
                  "if rc == CORE_REJECT_RC:"), False),
    ("m19", "接受列缺 L／原點／A0 頂點也靜默接受（有 oracle 矩形的列）",
     replace_once(PARSE, "    if missing:\n        problems.append(", "    if False:\n        problems.append("), False),
    ("m20", "沒有 oracle 矩形的接受列缺欄也靜默接受",
     replace_once(PARSE, "        if missing:\n            return _row(", "        if False:\n            return _row("), False),
    ("m21", "run_probe.sh 把結束碼 1 一律計成拒絕，不看 stderr",
     replace_once(SH, 'elif [ "$one" -eq "$core_reject_rc" ] && rule_diag "$d/$k.err"; then',
                  'elif [ "$one" -eq "$core_reject_rc" ]; then'), True),
    ("m22", "run_probe.sh 的規則診斷判定式漏掉 D 編號（與 parse_results 不一致）",
     replace_once(SH, "[IRD][0-9]+", "[IR][0-9]+"), True),
    ("m23", "parse_results 的規則診斷判定式漏掉 D 編號",
     replace_once(PARSE, r"(?<![A-Za-z0-9])[IRD]\d+", r"(?<![A-Za-z0-9])[IR]\d+"), False),
]


def copy_tree(dest: Path) -> Path:
    root = dest / "framing-template" / "core-probe"
    shutil.copytree(HERE, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (dest / "framing-template" / "oracle").mkdir(parents=True)
    shutil.copyfile(FRAMING / "oracle" / "oracle-golden.json", dest / "framing-template" / "oracle" / "oracle-golden.json")
    return root


def run_suite(root: Path, with_fake_core: bool) -> tuple[int, list[str], str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if not with_fake_core:
        env["PROBE_SKIP_FAKE_CORE"] = "1"
    done = subprocess.run(
        [sys.executable, "test_gen_scenes.py"], cwd=root, env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600,
    )
    failed = re.findall(r"^(?:FAIL|ERROR): (\w+) \(([\w.]+)\)", done.stderr, re.M)
    names = set()
    for name, where in failed:
        parts = where.split(".")
        owner = parts[-2] if parts[-1] == name else parts[-1]  # setUpClass 的括號裡只有類別名
        names.add(f"{owner}.{name}")
    names = sorted(names)
    tail = [line for line in done.stderr.splitlines() if line.startswith(("Ran ", "FAILED", "OK"))]
    return done.returncode, names, " / ".join(tail)


def main(argv: list[str]) -> int:
    if "--list" in argv:
        for name, text, _apply, _fake in MUTATIONS:
            print(f"{name}\t{text}")
        return 0
    wanted = [a for a in argv if not a.startswith("-")]
    chosen = [m for m in MUTATIONS if not wanted or m[0] in wanted]
    unknown = set(wanted) - {m[0] for m in MUTATIONS}
    if unknown:
        print(f"沒有這些突變：{sorted(unknown)}", file=sys.stderr)
        return 2
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        control_root = copy_tree(Path(tmp) / "control")
        code, names, tail = run_suite(control_root, with_fake_core=any(m[3] for m in chosen))
        print(f"對照組（不突變）：{'綠燈' if code == 0 else '紅燈（不該紅）'}  {tail}")
        if code != 0:
            print("  失敗的測試：" + ", ".join(names))
            return 1
        for name, text, apply, fake in chosen:
            root = copy_tree(Path(tmp) / name)
            apply(root)
            code, names, tail = run_suite(root, with_fake_core=fake)
            if code == 0:
                bad += 1
                print(f"{name} {text}\n  突變存活：測試全綠，沒有牙齒  {tail}")
            else:
                print(f"{name} {text}\n  紅燈：{tail}\n  轉紅的測試：{', '.join(names) or '（載入就失敗）'}")
    if bad:
        print(f"\n{bad} 個突變存活。")
        return 1
    print(f"\n{len(chosen)} 個突變全部轉紅。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
