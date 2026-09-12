# -*- coding: utf-8 -*-
"""current_geometry 測試執行器。

每個測試 = 一份 .scene + 預期:
  expect: "accept" | "reject"
  lengths: accept 時,依序比對輸出中所有「尺寸:L=…」的值
  error:   reject 時,stderr 第一行必須包含此子字串
  contains: accept 時,stdout 必須包含此子字串(可多條)

用法:
  python tests/run_tests.py [exe 路徑]      # 預設 ../cg_new.exe
"""
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

TESTS = [
    # ---- 舊有場景(回歸) ----
    {"scene": "ceiling-a.scene", "expect": "accept", "lengths": [1800]},
    {"scene": "demo-two-timbers.scene", "expect": "accept", "lengths": [2000, 1500]},
    {"scene": "room_a.scene", "expect": "accept", "lengths": [1800]},
    {"scene": "room_box.scene", "expect": "accept", "lengths": [1800, 1600]},
    {"scene": "room_full.scene", "expect": "accept", "lengths": [1800]},
    {"scene": "_test_fixed.scene", "expect": "accept", "lengths": [4000]},
    {"scene": "_test_free.scene", "expect": "reject", "error": "自由邊"},
    {"scene": "_test_hole.scene", "expect": "accept",
     "contains": ["參考線 1（段 0）", "孔 #0"]},
    {"scene": "_test_tx.scene", "expect": "reject", "error": "重宣告後有物件失效"},
    {"scene": "_test_tx2.scene", "expect": "accept", "lengths": [1000]},

    # ---- auto 跨距 / 網格 / 邊錨 ----
    {"scene": "_test_grid.scene", "expect": "accept",
     "lengths": [4000, 4000, 2960]},
    {"scene": "_test_lshape.scene", "expect": "reject", "error": "沒有擋面"},
    {"scene": "_test_hole_auto.scene", "expect": "accept", "lengths": [1200]},
    {"scene": "_test_ambiguous.scene", "expect": "reject", "error": "跨距歧義"},
    {"scene": "_test_collide.scene", "expect": "reject", "error": "正面積重疊"},
    {"scene": "_demo_ceiling.scene", "expect": "accept",
     "lengths": [4000, 2973, 3973, 2946, 2946, 2946, 1173]},

    # ---- 邊界條件案例 ----
    {"scene": "_edge_axis_violation.scene", "expect": "reject", "error": "垂直"},
    {"scene": "_edge_concave.scene", "expect": "accept", "lengths": [4000]},
    {"scene": "_edge_dir_violation.scene", "expect": "reject", "error": "平行"},
    {"scene": "_edge_free.scene", "expect": "reject", "error": "自由邊"},
    {"scene": "_edge_freeze.scene", "expect": "accept",
     "lengths": [1800], "contains": ["角材原點：(500, 300, 2500)"]},
    {"scene": "_edge_grid_at_border.scene", "expect": "reject",
     "error": "沒有任何合法跨距"},
    {"scene": "_edge_grid_twoline.scene", "expect": "accept",
     "lengths": [3000, 2986]},
    {"scene": "_edge_hole_anchor.scene", "expect": "accept",
     "lengths": [3000, 2790]},
    {"scene": "_edge_hole_bottom.scene", "expect": "accept", "lengths": [4000]},
    {"scene": "_edge_rect_only.scene", "expect": "reject", "error": "端面懸空"},
    {"scene": "_edge_rect_stops.scene", "expect": "accept",
     "lengths": [3000, 3000, 980]},
    {"scene": "_edge_stop_ambiguous.scene", "expect": "accept",
     "lengths": [1000, 1980]},
    {"scene": "_edge_straddle.scene", "expect": "reject", "error": "端面懸空"},
    {"scene": "_edge_two_holes.scene", "expect": "reject",
     "error": "邊界面輪廓不合法"},
    {"scene": "_edge_upper_seg.scene", "expect": "accept",
     "lengths": [4000, 4000, 1173]},
]

LEN_RE = re.compile(r"L=(\d+)")


def run_one(exe: str, spec: dict) -> str:
    scene = ROOT / spec["scene"]
    proc = subprocess.run(
        [exe, "--scene", str(scene), "--no-window"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=30,
    )
    out, err = proc.stdout, proc.stderr
    ok = proc.returncode == 0

    if spec["expect"] == "accept":
        if not ok:
            first = err.strip().splitlines()[0] if err.strip() else "(無錯誤訊息)"
            return f"FAIL 應接受但拒絕: {first}"
        lengths = [int(m) for m in LEN_RE.findall(out)]
        if "lengths" in spec and lengths != spec["lengths"]:
            return f"FAIL 長度不符: 期望 {spec['lengths']} 實得 {lengths}"
        for needle in spec.get("contains", []):
            if needle not in out:
                return f"FAIL 輸出缺少「{needle}」"
        return "ok"

    # expect == reject
    if ok:
        lengths = LEN_RE.findall(out)
        return f"FAIL 應拒絕但接受 (L={lengths})"
    if "error" in spec and spec["error"] not in err:
        first = err.strip().splitlines()[0] if err.strip() else "(無錯誤訊息)"
        return f"FAIL 錯誤不符: 期望含「{spec['error']}」實得「{first}」"
    return "ok"


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "cg_new.exe")
    failures = []
    for spec in TESTS:
        try:
            verdict = run_one(exe, spec)
        except subprocess.TimeoutExpired:
            verdict = "FAIL 逾時"
        except Exception as exc:  # noqa: BLE001
            verdict = f"FAIL 例外 {exc}"
        status = "PASS" if verdict == "ok" else verdict
        print(f"{spec['scene']:<34} {status}")
        if verdict != "ok":
            failures.append(spec["scene"])
    print(f"\n{len(TESTS) - len(failures)}/{len(TESTS)} 通過")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
