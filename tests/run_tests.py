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
    {"scene": "_test_hole_auto.scene", "expect": "accept",
     "lengths": [4000, 1180]},
    {"scene": "_test_ambiguous.scene", "expect": "reject", "error": "跨距歧義"},
    {"scene": "_test_collide.scene", "expect": "reject", "error": "正面積重疊"},
    # GEO-090 角色遷移:e1/e3 沿主支軸的料是邊界主支(primary),層級 1 先落地
    # 整條蓋到牆(R19(d)),層級 2 被兩端層級 1 佔掉的料寬裁短(R19(c))。
    {"scene": "_demo_ceiling.scene", "expect": "accept",
     "lengths": [4000, 2946, 4000, 2946, 2946, 2946, 1173]},

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
     "lengths": [4000, 4000, 2960, 2960, 1973]},
    {"scene": "_edge_hole_anchor.scene", "expect": "accept",
     "lengths": [4000, 4000, 2960, 2960, 2763]},
    {"scene": "_edge_hole_bottom.scene", "expect": "accept",
     "lengths": [3960, 3000, 3000]},
    {"scene": "_edge_rect_only.scene", "expect": "reject", "error": "端面懸空"},
    {"scene": "_edge_rect_stops.scene", "expect": "accept",
     "lengths": [3000, 3000, 980]},
    {"scene": "_edge_stop_ambiguous.scene", "expect": "accept",
     "lengths": [1000, 1960, 3000, 2000, 3946]},
    {"scene": "_edge_straddle.scene", "expect": "reject", "error": "端面懸空"},
    {"scene": "_edge_two_holes.scene", "expect": "reject",
     "error": "邊界面輪廓不合法"},
    {"scene": "_edge_upper_seg.scene", "expect": "accept",
     "lengths": [4000, 4000, 1173]},

    # ---- 變異測試殺手(對應 tests/mutate.py 的存活變異) ----
    # M08:輪廓邊穿矩形內部,四角皆在內、頂點在邊上 → 只剩邊穿入檢查能擋
    {"scene": "_mut_notch_straddle.scene", "expect": "reject",
     "error": "放不上去"},
    # M18/M36:重宣告把 auto 兩端的孔邊擋面翻 FREE → 重驗應退
    {"scene": "_mut_reval_free_hole.scene", "expect": "reject",
     "error": "重宣告後有物件失效"},
    # M19:through 恰落在區間端點(閉區間才算選中)
    {"scene": "_mut_through_boundary.scene", "expect": "accept",
     "lengths": [4000, 1180]},
    # M22:auto 終點頂到 FREE 孔邊(放置路徑只查外輪廓,擋不住的)
    {"scene": "_mut_free_hole_end.scene", "expect": "reject",
     "error": "自由邊"},
    # M24:at-edge 唯一合法區間與邊範圍只有端點相接 → 不算接觸
    {"scene": "_mut_edge_touch_only.scene", "expect": "reject",
     "error": "不接觸引用的邊"},
    # M31:格線座標重複 → 嚴格遞增檢查
    {"scene": "_mut_grid_dup.scene", "expect": "reject",
     "error": "嚴格遞增"},
    # M35:明寫 L=0 → 宣告時拒絕(訊息與下游「放不上去」不同)
    {"scene": "_mut_zero_len.scene", "expect": "reject",
     "error": "大於 0"},
    # M38:負孔索引 -1 是外輪廓哨兵,放行會被當 e0 誤放
    {"scene": "_mut_neg_hole_ref.scene", "expect": "reject",
     "error": "邊參照"},

    # ---- 角色主支軸(GEO-091、D17/I21)----
    # 同面第二支 primary 換軸 → V_PRIMARY_AXIS
    {"scene": "_role_axis_second_primary.scene", "expect": "reject",
     "error": "V_PRIMARY_AXIS"},
    # boundary 先落地定軸(⊥),再放與它平行的 primary → V_PRIMARY_AXIS
    {"scene": "_role_axis_boundary_first.scene", "expect": "reject",
     "error": "V_PRIMARY_AXIS"},
    # 刪掉唯一 primary 後軸由 boundary 推得(不回未定義)→ V_PRIMARY_AXIS
    {"scene": "_role_axis_fallback.scene", "expect": "reject",
     "error": "V_PRIMARY_AXIS"},

    # ---- GEO-092 延伸段與角色優先級(D16/I19/I22)----
    # I22:凸角處 boundary 延伸使 footprint 跨出外輪廓 → 走 I5 出界(不需新碼)
    {"scene": "_role_priority_convex.scene", "expect": "reject",
     "error": "錨點在有效範圍外"},
    # I22:延伸段側面以優先級 2 計;主支也是 2,2 未嚴格小於 2 → 拒絕
    {"scene": "_role_priority_ext_primary.scene", "expect": "reject",
     "error": "角材 5（優先級 2）端面頂到角材 4（優先級 2）"},
    # D16/I22:延伸段是 boundary 專屬,primary 有超出定位邊的段 → 拒絕
    {"scene": "_role_priority_mutant.scene", "expect": "reject",
     "error": "V_EXTENSION：非 boundary 角材（1）"},
    # I19:邊界材是 RC 錨定層,主支端面不得直接頂外輪廓邊
    {"scene": "_role_priority_primary_rc.scene", "expect": "reject",
     "error": "端面頂到外輪廓邊（RC）"},
    # I19:副支端面同樣不得直接頂 RC(該處無邊界材可當擋面)
    {"scene": "_role_priority_secondary_rc.scene", "expect": "reject",
     "error": "端面頂到外輪廓邊（RC）"},
    # I19:主支(2)端面頂副支(3)側面,3 未嚴格小於 2 → 拒絕
    {"scene": "_role_priority_primary_secondary.scene", "expect": "reject",
     "error": "角材 4（優先級 2）端面頂到角材 3（優先級 3）"},
    # I22 正向:延伸段側面以 2 計,被 custom(priority 3)頂 → 接受。
    # 唯一的接受路徑——secondary 由 D17 必平行延伸段頂不到、primary 同為 2 被 I19 擋。
    {"scene": "_role_priority_ext_custom.scene", "expect": "accept",
     "lengths": [4000, 4000, 1946]},

    # ---- RC 柱/樑(D13/D14、I15–I17、R11)----
    # 柱-柱面積相交 → I15 重驗拒絕
    {"scene": "_mut_col_overlap.scene", "expect": "reject",
     "error": "柱宣告後有物件失效"},
    # 柱足跡越出空間平面範圍 → I15
    {"scene": "_mut_col_outside.scene", "expect": "reject",
     "error": "柱宣告後有物件失效"},
    # 樑走向軸非水平 → D14 解析層拒絕
    {"scene": "_mut_beam_diag.scene", "expect": "reject",
     "error": "走向軸"},
    # 游離柱不明寫 z → R11 不猜
    {"scene": "_mut_col_noz.scene", "expect": "reject",
     "error": "游離柱"},

    # ---- RC 障礙物投影夾具(R7 五種接觸;分類由 bridge obstacles 驗)----
    {"scene": "_rc_col_free.scene", "expect": "accept"},
    {"scene": "_rc_col_wall.scene", "expect": "accept"},
    {"scene": "_rc_col_corner.scene", "expect": "accept"},
    {"scene": "_rc_beam_cross.scene", "expect": "accept"},
    {"scene": "_rc_beam_edge.scene", "expect": "accept"},
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
