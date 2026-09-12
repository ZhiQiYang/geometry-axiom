# -*- coding: utf-8 -*-
"""輕量變異測試:對 current_geometry.c 做單點替換 -> 編譯 -> 跑測試套件。

變異定義 = (id, 說明, old, new);old 必須在原始碼中恰好出現一次。
結果: killed(某測試失敗) / survived(全過) / invalid(編譯失敗或錨點不唯一)。

用法:
  python tests/mutate.py            # 全部變異
  python tests/mutate.py M03 M14    # 只跑指定 id
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "current_geometry.c"
MUT_SRC = HERE / "_mutant.c"
MUT_EXE = HERE / "_mut.exe"
RESULTS = HERE / "mutants_results.json"

# ============================================================
# 變異表:針對核心幾何 / 座標 / 碰撞 / 驗證
# ============================================================
MUTANTS = [
    # ---- poly_point_on_edge:邊上判定 ----
    dict(id="M01", desc="邊上判定:含端點改嚴格(端點不在邊上)",
         old="p.v >= coord_min(a.v, b.v) && p.v <= coord_max(a.v, b.v)",
         new="p.v > coord_min(a.v, b.v) && p.v < coord_max(a.v, b.v)"),
    # ---- poly_contains_point:射線法 ----
    dict(id="M02", desc="射線半開區間 [v_min,v_max) 改 (v_min,v_max)",
         old="p.v >= v_min && p.v < v_max && p.u < a.u",
         new="p.v > v_min && p.v < v_max && p.u < a.u"),
    dict(id="M03", desc="射線只數直立邊 -> 改數水平邊",
         old="        if (a.u != b.u) {\n            continue;   /* 水平邊不與水平射線交叉 */",
         new="        if (a.u == b.u) {\n            continue;   /* 水平邊不與水平射線交叉 */"),
    dict(id="M04", desc="奇偶判定反轉(內外互換)",
         old="return crossings % 2 == 1;",
         new="return crossings % 2 == 0;"),
    # ---- segment2_crosses_rect_interior:邊穿矩形內部 ----
    dict(id="M05", desc="直立邊在矩形邊界上也算穿入(<= 改 <)",
         old="if (a.u <= min_u || a.u >= max_u) {\n            return false;",
         new="if (a.u < min_u || a.u > max_u) {\n            return false;"),
    dict(id="M06", desc="水平邊在矩形邊界上也算穿入(<= 改 <)",
         old="if (a.v <= min_v || a.v >= max_v) {\n        return false;",
         new="if (a.v < min_v || a.v > max_v) {\n        return false;"),
    dict(id="M07", desc="直立邊 v 區間零長度接觸也算穿入(< 改 <=)",
         old="        Coord lo = coord_max(coord_min(a.v, b.v), min_v);\n        Coord hi = coord_min(coord_max(a.v, b.v), max_v);\n        return lo < hi;",
         new="        Coord lo = coord_max(coord_min(a.v, b.v), min_v);\n        Coord hi = coord_min(coord_max(a.v, b.v), max_v);\n        return lo <= hi;"),
    # ---- poly_contains_rect:矩形 ⊆ 環 ----
    dict(id="M08", desc="拿掉「環邊不得穿矩形內部」檢查",
         old="        if (segment2_crosses_rect_interior(\n                loop->v[i], loop->v[(i + 1) % loop->count],\n                min_u, min_v, max_u, max_v)) {\n            return false;\n        }\n    }\n\n    return true;\n}",
         new="        if (0 && segment2_crosses_rect_interior(\n                loop->v[i], loop->v[(i + 1) % loop->count],\n                min_u, min_v, max_u, max_v)) {\n            return false;\n        }\n    }\n\n    return true;\n}"),
    # ---- boundary_contains_rect:孔干涉 ----
    dict(id="M09", desc="孔 bbox 邊界相接也當相交(<= 改 <)",
         old="if (h_max_u <= min_u || h_min_u >= max_u ||\n            h_max_v <= min_v || h_min_v >= max_v) {",
         new="if (h_max_u < min_u || h_min_u > max_u ||\n            h_max_v < min_v || h_min_v > max_v) {"),
    dict(id="M10", desc="孔頂點嚴格在矩形內 -> 含邊界(> 改 >=)",
         old="if (p.u > min_u && p.u < max_u &&\n                p.v > min_v && p.v < max_v) {",
         new="if (p.u >= min_u && p.u <= max_u &&\n                p.v >= min_v && p.v <= max_v) {"),
    dict(id="M11", desc="孔罩住矩形判定:inside==4 改 inside==0(罩住反而放行)",
         old="            if (inside == 4) {\n                return false;",
         new="            if (inside == 0) {\n                return false;"),
    # ---- uv_rects_overlap / world_footprint_collides:碰撞 ----
    dict(id="M12", desc="正面積重疊:端點相接也算重疊(> 改 >=)",
         old="return coord_min(a_max_u, b_max_u) > coord_max(a_min_u, b_min_u) &&\n           coord_min(a_max_v, b_max_v) > coord_max(a_min_v, b_min_v);",
         new="return coord_min(a_max_u, b_max_u) >= coord_max(a_min_u, b_min_u) &&\n           coord_min(a_max_v, b_max_v) >= coord_max(a_min_v, b_min_v);"),
    dict(id="M13", desc="碰撞只看同承載面 -> 看不同承載面(!= 改 ==)",
         old="SurfaceRegion2 other;\n\n        if (!t->placed || t == exclude ||\n            a->placement_id != placement->id) {",
         new="SurfaceRegion2 other;\n\n        if (!t->placed || t == exclude ||\n            a->placement_id == placement->id) {"),
    # ---- collect_stop_faces:擋面枚舉 ----
    dict(id="M14", desc="只收垂直邊 -> 只收平行邊(along_v 分支)",
         old="if (along_v && a.v != b.v) {",
         new="if (along_v && a.v == b.v) {"),
    dict(id="M15", desc="角材側面涵蓋範圍用錯軸(u 範圍改成 v 範圍)",
         old="f.min_v, f.min_u, f.max_u\n            };\n            out[count++] = (StopFace){\n                STOP_TIMBER_SIDE, 0, t->id, -1, 1, EDGE_FIXED,\n                f.max_v, f.min_u, f.max_u",
         new="f.min_v, f.min_v, f.max_v\n            };\n            out[count++] = (StopFace){\n                STOP_TIMBER_SIDE, 0, t->id, -1, 1, EDGE_FIXED,\n                f.max_v, f.min_v, f.max_v"),
    # ---- pick_stop:唯一全寬擋面 ----
    dict(id="M16", desc="擋面涵蓋檢查:丟掉 hi 側檢查(半寬也算涵蓋)",
         old="if (f->fixed != at || f->lo > lo || f->hi < hi) {\n            continue;",
         new="if (f->fixed != at || f->lo > lo) {\n            continue;"),
    dict(id="M17", desc="擋面涵蓋檢查:邊界相等不算涵蓋(> 改 >=)",
         old="if (f->fixed != at || f->lo > lo || f->hi < hi) {\n            continue;",
         new="if (f->fixed != at || f->lo >= lo || f->hi <= hi) {\n            continue;"),
    # ---- count_legal_stops:重驗用 ----
    dict(id="M18", desc="重驗擋面:FREE 邊也算合法(!= 改 ==)",
         old="f->fixity != EDGE_FREE) {",
         new="f->fixity == EDGE_FREE) {"),
    # ---- resolve_auto_span ----
    dict(id="M19", desc="through 選段:邊界座標不算在區間內(<= 改 <)",
         old="if (through >= intervals[i].start &&\n                through <= intervals[i].end) {",
         new="if (through > intervals[i].start &&\n                through < intervals[i].end) {"),
    dict(id="M20", desc="拿掉「起點必須有擋面」檢查(懸空端放行)",
         old="    if (hits == 0) {\n        snprintf(err, err_cap, \"跨距起點沒有擋面（端面懸空）\");",
         new="    if (0) {\n        snprintf(err, err_cap, \"跨距起點沒有擋面（端面懸空）\");"),
    dict(id="M21", desc="拿掉「終點必須有擋面」檢查",
         old="    if (hits == 0) {\n        snprintf(err, err_cap, \"跨距終點沒有擋面（端面懸空）\");",
         new="    if (0) {\n        snprintf(err, err_cap, \"跨距終點沒有擋面（端面懸空）\");"),
    dict(id="M22", desc="拿掉 FREE 擋面拒絕",
         old="    if (stop->fixity == EDGE_FREE) {\n        snprintf(err, err_cap, \"跨距終點頂到自由邊\");",
         new="    if (0) {\n        snprintf(err, err_cap, \"跨距終點頂到自由邊\");"),
    dict(id="M23", desc="擋面歧義放行(hits>1 不拒絕)",
         old="    if (hits > 1) {\n        snprintf(err, err_cap, \"跨距起點擋面歧義\");",
         new="    if (0) {\n        snprintf(err, err_cap, \"跨距起點擋面歧義\");"),
    dict(id="M24", desc="at-edge 接觸範圍:端點相接也算重疊(< 改 <=)",
         old="if (intervals[i].start < contact_hi &&\n                intervals[i].end > contact_lo) {",
         new="if (intervals[i].start <= contact_hi &&\n                intervals[i].end >= contact_lo) {"),
    dict(id="M25", desc="跨距歧義放行:多區間自動選第一段",
         old="    } else if (interval_count > 1) {",
         new="    } else if (0 && interval_count > 1) {"),
    # ---- anchor_corner_from_rect:矩形 -> 錨角 ----
    dict(id="M26", desc="錨角選錯邊(min/max 對調)",
         old="        du > 0 ? rect->min_u : rect->max_u,\n        dv > 0 ? rect->min_v : rect->max_v",
         new="        du > 0 ? rect->max_u : rect->min_u,\n        dv > 0 ? rect->max_v : rect->min_v"),
    # ---- a0_rect_uv:深度側 ----
    dict(id="M27", desc="深度側反轉:角材往面下長",
         old="    Vector3 axis_b =\n        depth_side == SURFACE_DEPTH_POSITIVE_NORMAL\n            ? surface->frame.normal\n            : vector_negate(surface->frame.normal);\n\n    Vector3 axis_a = vector_cross(axis_b, axis_length);\n\n    SurfacePoint2 far_pt = {",
         new="    Vector3 axis_b =\n        depth_side == SURFACE_DEPTH_POSITIVE_NORMAL\n            ? vector_negate(surface->frame.normal)\n            : surface->frame.normal;\n\n    Vector3 axis_a = vector_cross(axis_b, axis_length);\n\n    SurfacePoint2 far_pt = {"),
    # ---- at-grid 中線:奇數寬拆分 ----
    dict(id="M28", desc="奇數寬多的 1mm 改放 -cross 側",
         old="            cross_lo = centerline - w / 2;\n            cross_hi = cross_lo + w;",
         new="            cross_lo = centerline - (w + 1) / 2;\n            cross_hi = cross_lo + w;"),
    # ---- at-edge 材料側 ----
    dict(id="M29", desc="外輪廓材料側反轉(footprint 長到面外)",
         old="                Coord in = ref_hole < 0 ? -outward.u : outward.u;",
         new="                Coord in = ref_hole < 0 ? outward.u : outward.u;"),
    dict(id="M30", desc="孔邊材料側反轉(footprint 長進孔裡)",
         old="                Coord in = ref_hole < 0 ? -outward.v : outward.v;",
         new="                Coord in = ref_hole < 0 ? -outward.v : -outward.v;"),
    # ---- grid ----
    dict(id="M31", desc="格線座標遞增改非嚴格(<= 改 <)",
         old="        if (i > 0 && coords[i] <= coords[i - 1]) {",
         new="        if (i > 0 && coords[i] < coords[i - 1]) {"),
    dict(id="M32", desc="格線座標上界改成嚴格(壓邊界的格線拒絕)",
         old="        if (grid->u_coords[i] < bounds.min_u ||\n            grid->u_coords[i] > bounds.max_u) {",
         new="        if (grid->u_coords[i] <= bounds.min_u ||\n            grid->u_coords[i] >= bounds.max_u) {"),
    dict(id="M33", desc="at-grid 軸向守門員反轉",
         old="            if ((ref_grid_axis == 0) != along_v) {",
         new="            if ((ref_grid_axis == 0) == along_v) {"),
    # ---- at-edge 方向守門員 ----
    dict(id="M34", desc="at-edge 平行守門員反轉",
         old="            if (edge_runs_v != along_v) {",
         new="            if (edge_runs_v == along_v) {"),
    # ---- timber_construct ----
    dict(id="M35", desc="明寫長度允許 L=0(<= 改 <)",
         old="        (!auto_length && length <= 0) ||",
         new="        (!auto_length && length < 0) ||"),
    # ---- world_revalidate ----
    dict(id="M36", desc="重驗跳過 auto 端點擋面檢查",
         old="        if (a->span_mode == SPAN_AUTO) {",
         new="        if (0 && a->span_mode == SPAN_AUTO) {"),
    dict(id="M37", desc="碰撞兩兩檢查變成自己也算(j=i+1 改 j=i)",
         old="        for (size_t j = i + 1; j < world->timber_count; ++j) {",
         new="        for (size_t j = i; j < world->timber_count; ++j) {"),
    # ---- parse_edge_ref ----
    dict(id="M38", desc="at-edge 邊參照:孔索引 <0 也放行(hole<0 檢查拿掉)",
         old="        if (!parse_i64(buf, &hole) || hole < 0) {",
         new="        if (!parse_i64(buf, &hole) || hole < -99) {"),
    # ---- span cell:零長 cell 處理 ----
    dict(id="M39", desc="切點去重用 < 不去重(零長 cell 出現)",
         old="        if (unique == 0 || cuts[i] != cuts[unique - 1]) {",
         new="        if (unique == 0 || cuts[i] < cuts[unique - 1]) {"),
    # ---- span:選段後端點檢查順序 ----
    dict(id="M40", desc="有效 cell 判定拿掉碰撞(只查包含)",
         old="        bool ok =\n            surface_contains_rect(\n                placement, boundary,\n                cell.min_u, cell.min_v, cell.max_u, cell.max_v) &&\n            !world_footprint_collides(world, placement, &cell, NULL);",
         new="        bool ok =\n            surface_contains_rect(\n                placement, boundary,\n                cell.min_u, cell.min_v, cell.max_u, cell.max_v);"),
]


def run_cmd(cmd, cwd, timeout=120):
    return subprocess.run(cmd, cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    only = set(sys.argv[1:])
    results = {}

    for m in MUTANTS:
        if only and m["id"] not in only:
            continue

        n = src.count(m["old"])
        if n != 1:
            results[m["id"]] = {
                "desc": m["desc"], "verdict": "invalid",
                "why": f"錨點出現 {n} 次(需要 1)"
            }
            print(f"{m['id']}  INVALID  錨點×{n}  {m['desc']}")
            continue

        MUT_SRC.write_text(src.replace(m["old"], m["new"], 1),
                           encoding="utf-8", newline="\n")

        build = run_cmd(["cmd", "/c",
                         str(HERE / "_cl.bat") + " _mutant.c _mut.exe"],
                        cwd=HERE, timeout=180)
        if not MUT_EXE.exists() or build.returncode != 0:
            results[m["id"]] = {
                "desc": m["desc"], "verdict": "invalid",
                "why": "編譯失敗: " + (build.stderr or build.stdout)[-200:]
            }
            print(f"{m['id']}  INVALID  編譯失敗  {m['desc']}")
            MUT_EXE.unlink(missing_ok=True)
            continue

        test = run_cmd([sys.executable, str(HERE / "run_tests.py"),
                        str(MUT_EXE)], cwd=ROOT, timeout=600)
        verdict = "killed" if test.returncode != 0 else "survived"
        # 抓第一個 FAIL 行當死因
        why = ""
        if verdict == "killed":
            for ln in test.stdout.splitlines():
                if "FAIL" in ln:
                    why = ln.strip()
                    break
        results[m["id"]] = {"desc": m["desc"], "verdict": verdict, "why": why}
        print(f"{m['id']}  {verdict.upper():<9} {m['desc']}"
              + (f"  <- {why}" if why else ""))

    RESULTS.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8")
    k = sum(1 for r in results.values() if r["verdict"] == "killed")
    s = sum(1 for r in results.values() if r["verdict"] == "survived")
    i = sum(1 for r in results.values() if r["verdict"] == "invalid")
    print(f"\n合計 {len(results)}:殺死 {k} / 存活 {s} / 無效 {i}")
    return 0


if __name__ == "__main__":
    main()
