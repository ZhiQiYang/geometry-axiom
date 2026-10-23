# -*- coding: utf-8 -*-
"""變異測試:對 C 原始碼做單點替換 -> 編譯 -> 跑真實裁判。

變異定義 = (id, 說明, old, new[, file]);old 必須在目標檔中恰好出現一次。
  file   預設 current_geometry.c;邏輯搬到 K/W/H 實作時指名實際檔案。
         暫存複本只展開主檔到目標的唯一 include 路徑(例如 main→unity→target)，
         其餘 include 保留並改為 repo 根相對路徑；重複、缺失或越界路徑拒絕。
  equivalent  等價變異(理由文字),每輪仍編譯並跑完整 oracle;錨點須存在。
  retired     邏輯已從產品整個移除(寫明依據),不編譯;舊錨點若又出現會被判 invalid。
  binary="bridge" 使用獨立的已提交稀疏 checkout、官方 binaries.py 編譯及 tests 指定的
         真 bridge unittest 方法。先跑基準，變異後只以完成的行為斷言判 killed；每筆還原
         來源、重新編譯並跑共用回歸。錯誤、略過、逾時與不完整方法清單都算 blocked。
         bridge 行程在測試中死亡(tests/_bridge.py 的 BridgeClosed,帶結束碼)不是斷言失敗。
         crashed 判準同核心:同一測試連續 RUN_RETRIES 次都以存取違規(is_access_violation_code)
         結束、且沒有任何斷言失敗;重跑範圍較窄,只重跑存取違規(核心則重跑所有 blocked)。
         其他結束碼(含外部 kill、OOM)、不足次數、前後不一致、或與斷言失敗並存 -> blocked,
         不重跑、不算偵測。
         死亡不只看最外層例外:例外鏈任一層的 BridgeClosed(含 BridgeSession.stop() 發現 bridge
         讀到 EOF 後以非 0 結束)、run_once 的非 0 結束碼、測試啟動的 bridge 行程(程式 = oracle 的
         bridge 二進位)以非 0 結束(oracle 的 ChildWatch,最多等 5 秒取得結束碼,與
         BridgeSession 一致)都算;無關子行程當機不算;只有文字說 bridge closed 而沒有結束碼
         -> blocked。tests 指定的方法必須在基準線 mutation_bridge.RESTORED 內,否則 invalid。

結果: killed(某測試失敗) / crashed(基準通過後,同一夾具連續存取違規;
      算被偵測到,但不是斷言殺死) / survived(全過) / equivalent / retired /
      invalid(編譯失敗或錨點不在、不唯一) / blocked(啟動失敗、WinError 4551、
      逾時或其他非存取違規的異常結束,不算 killed) /
      stale(紀錄的來源雜湊、變異定義雜湊與現況不符,不計入 killed)。

誠實性規則(審查 2026-10-01 後立):
  - 錨點找不到或不唯一 -> invalid,覆蓋任何舊判決。
  - 每筆結果帶 source_file / source_sha256(被變異那個檔)/ closure_sha256(整個
    core + bridge 的 #include 聯集閉包)/ oracle_sha256(裁判)/ mutant_sha256(定義)/ date。
  - oracle_sha256 = sha256(tests/run_tests.py + 依檔名排序、被 TESTS 引用的每個 .scene
    內容;全部 CRLF->LF)。它取代舊的 runner_sha256:裁判 = 判定邏輯 + 夾具,
    兩者任一改了,killed / survived 就不再是「這個裁判」下的判決。
    (equivalent 不是靠跑裁判得來的,不受 oracle 約束;retired 不帶來源類雜湊。)
    bridge 裁判另外涵蓋指定方法、共用還原方法、tests/*.py、tests/*.c、
    tests/fixtures/**/*.scene 與根目錄場景；任何共用
    harness 變更都使其過期，不能借核心場景裁判替預覽序列化背書。
  - 載入與彙總時,source_sha256、closure_sha256、mutant_sha256 任一與現況不符,
    killed / survived 的 oracle_sha256 與現行裁判不符,或根本沒帶雜湊 -> stale;
    stale 會寫回結果檔(原判決存 stale_from),原因消失(例如還原原始碼 / 夾具)後自動復原。
  - killed 紀錄帶 killed_by:讓它失敗的夾具名(前 5 個),日後看得到牙齒在哪。
  - crashed 紀錄帶 crashed_on:連續存取違規的夾具名。來源或裁判變了同樣標 stale。
  - 結束碼:blocked -> 2;否則 survived / invalid / stale(完整跑與 --check 另含 unrun)
    任一存在 -> 1;否則 0。crashed 算被偵測到,不占 1 也不占 2。

exe 指紋快取(治本:Smart App Control 會擋「新出現」的未簽章 exe,沒改就不重編):
  %TEMP%\\geometry-tests\\mutants\\<id>\\_mut.exe 旁邊放 _mut.exe.fingerprint.json:
  mutant_sha256 + closure_sha256 + generated_source_sha256(實際注入後的原始碼)
  + compile_sha256(Windows 的 _cl.bat 內容或 Linux 的 cc 參數)+ exe 自身雜湊。
  全部相符 -> 沿用、不呼叫 cl;任一不符(含 exe 被動過)-> 重編。
  沒有 sidecar 的 exe 一律重編：結果檔的來源雜湊不能證明磁碟上這支 exe 的內容或編譯指令。
  baseline(未變異原始碼)的 exe 同樣以 closure + 編譯指令快取在 mutants\\_baseline\\。

用法:
  python tests/mutate.py            # 全部變異
  python tests/mutate.py M03 M14    # 只跑指定 id(結束碼只看這幾個)
  python tests/mutate.py --check    # 不編譯、不跑,只依現行來源核對結果檔並彙總
  python tests/mutate.py --check --killers   # 同上,另列每個 killed 的 killed_by
  python tests/mutate.py --selftest # 對誠實性規則與快取本身的自我測試(不編譯)
"""
import contextlib
import datetime
import hashlib
import io
import json
import os
import pathlib
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import time
import types
import binaries
from run_tests import TESTS

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
MAIN_REL = "current_geometry.c"
SRC = ROOT / MAIN_REL
# 每個變異一個獨立目錄,放在 %TEMP%:
#   - repo 目錄的新編 exe 會被 Smart App Control 擋(WinError 4551),%TEMP% 不會(或機率低很多)
#   - 平行跑兩個 mutate.py 不會互相覆蓋同一個 _mut.exe
MUT_ROOT = pathlib.Path(os.environ.get("MUTATE_CACHE", str(pathlib.Path(tempfile.gettempdir()) / "geometry-tests" / "mutants")))
# 結果檔:平行執行時各自寫到 MUTATE_RESULTS 指定的檔,由指揮官事後合併,避免競態。
RESULTS = pathlib.Path(os.environ.get("MUTATE_RESULTS", str(HERE / "mutants_results.json")))

# 環境失敗(SAC 間歇封鎖新編譯的 exe)時重跑幾次才放棄
RUN_RETRIES = 3

VERDICTS = ("killed", "crashed", "survived", "equivalent", "invalid", "stale", "blocked", "retired")

# ============================================================
# 變異表:針對核心幾何 / 座標 / 碰撞 / 驗證
# ============================================================
MUTANTS = [
    # ---- poly_point_on_edge:邊上判定 ----
    dict(id="M01", desc="I5：邊上判定:含端點改嚴格(端點不在邊上)",
         file='geometry-core/kernel/geometry.c',
         old='p.v >= geo_coord_min(a.v, b.v) && p.v <= geo_coord_max(a.v, b.v)',
         new='p.v > geo_coord_min(a.v, b.v) && p.v < geo_coord_max(a.v, b.v)'),
    # ---- poly_contains_point:射線法 ----
    dict(id="M02", desc="I5：射線半開區間 [v_min,v_max) 改 (v_min,v_max)",
         file='geometry-core/kernel/geometry.c',
         old="p.v >= v_min && p.v < v_max && p.u < a.u",
         new="p.v > v_min && p.v < v_max && p.u < a.u"),
    dict(id="M03", desc="I5：射線只數直立邊 -> 改數水平邊",
         file='geometry-core/kernel/geometry.c',
         old="        if (a.u != b.u) {\n            continue;   /* 水平邊不與水平射線交叉 */",
         new="        if (a.u == b.u) {\n            continue;   /* 水平邊不與水平射線交叉 */"),
    dict(id="M04", desc="I5：奇偶判定反轉(內外互換)",
         file='geometry-core/kernel/geometry.c',
         old="return crossings % 2 == 1;",
         new="return crossings % 2 == 0;"),
    # ---- segment2_crosses_rect_interior:邊穿矩形內部 ----
    dict(id="M05", desc="I5：直立邊在矩形邊界上也算穿入(<= 改 <)",
         file='geometry-core/kernel/geometry.c',
         old="if (a.u <= min_u || a.u >= max_u) {\n            return false;",
         new="if (a.u < min_u || a.u > max_u) {\n            return false;"),
    dict(id="M06", desc="I5：水平邊在矩形邊界上也算穿入(<= 改 <)",
         file='geometry-core/kernel/geometry.c',
         old="if (a.v <= min_v || a.v >= max_v) {\n        return false;",
         new="if (a.v < min_v || a.v > max_v) {\n        return false;"),
    dict(id="M07", desc="I5：直立邊 v 區間零長度接觸也算穿入(< 改 <=)",
         file='geometry-core/kernel/geometry.c',
         old='        GeoCoord lo = geo_coord_max(geo_coord_min(a.v, b.v), min_v);\n        GeoCoord hi = geo_coord_min(geo_coord_max(a.v, b.v), max_v);\n        return lo < hi;',
         new='        GeoCoord lo = geo_coord_max(geo_coord_min(a.v, b.v), min_v);\n        GeoCoord hi = geo_coord_min(geo_coord_max(a.v, b.v), max_v);\n        return lo <= hi;'),
    # ---- poly_contains_rect:矩形 ⊆ 環 ----
    dict(id="M08", desc="I5：拿掉「環邊不得穿矩形內部」檢查",
         file='geometry-core/kernel/geometry.c',
         old='        if (geo_segment_crosses_rect_interior(\n                loop->v[i], loop->v[(i + 1) % loop->count],\n                min_u, min_v, max_u, max_v)) {\n            return false;\n        }\n    }\n\n    return true;\n}',
         new='        if (0 && geo_segment_crosses_rect_interior(\n                loop->v[i], loop->v[(i + 1) % loop->count],\n                min_u, min_v, max_u, max_v)) {\n            return false;\n        }\n    }\n\n    return true;\n}'),
    # ---- poly_contains_rect:矩形中心必須在環內(GEO-257)----
    dict(id="M59", desc="I5：拿掉「矩形中心必須在環內」檢查(凹槽內四角貼壁的矩形放行)",
         file='geometry-core/kernel/geometry.c',
         old='    if (!geo_loop_rect_center_inside(loop, min_u, min_v, max_u, max_v)) {\n        return false;\n    }',
         new='    if (0 && !geo_loop_rect_center_inside(loop, min_u, min_v, max_u, max_v)) {\n        return false;\n    }'),
    dict(id="M60", desc="I5：矩形中心的奇偶判定反轉(環內外互換)",
         file='geometry-core/kernel/geometry.c',
         old="    return (crossings & 1) != 0;",
         new="    return (crossings & 1) == 0;"),
    # ---- boundary_contains_rect:孔干涉 ----
    dict(id="M09", desc="I5：孔 bbox 邊界相接也當相交(<= 改 <)",
         equivalent="等價變異(GEO-172 實證):bbox 恰好相切時孔的所有點都在 u<=min_u(或對稱軸)一側,後續三道細查(頂點嚴格在內/邊穿過內部/孔罩住矩形)都不可能成立,快退與細查得到同一答案。",
         file='geometry-core/kernel/geometry.c',
         old="if (h_max_u <= min_u || h_min_u >= max_u ||\n            h_max_v <= min_v || h_min_v >= max_v) {",
         new="if (h_max_u < min_u || h_min_u > max_u ||\n            h_max_v < min_v || h_min_v > max_v) {"),
    dict(id="M10", desc="I5：孔頂點嚴格在矩形內 -> 含邊界(> 改 >=)",
         file='geometry-core/kernel/geometry.c',
         old="if (p.u > min_u && p.u < max_u &&\n                p.v > min_v && p.v < max_v) {",
         new="if (p.u >= min_u && p.u <= max_u &&\n                p.v >= min_v && p.v <= max_v) {"),
    dict(id="M11", desc="I5：停用孔完全罩住矩形的精確中心檢查（孔內矩形錯誤放行）",
         file='geometry-core/kernel/geometry.c',
         old="        if (geo_loop_rect_center_inside(hole, min_u, min_v, max_u, max_v)) {\n            return false; /* GEO261_HOLE_RECT_CENTER */",
         new="        if (0 && geo_loop_rect_center_inside(hole, min_u, min_v, max_u, max_v)) {\n            return false; /* GEO261_HOLE_RECT_CENTER */"),
    # ---- geo_rect_overlap_positive / resolve_auto_span 的碰撞障礙:碰撞 ----
    dict(id="M12", desc="I11：正面積重疊:端點相接也算重疊(> 改 >=)",
         file='geometry-core/kernel/geometry.c',
         old='return geo_coord_min(a->max_u,b->max_u)>geo_coord_max(a->min_u,b->min_u)&&\n        geo_coord_min(a->max_v,b->max_v)>geo_coord_max(a->min_v,b->min_v);',
         new='return geo_coord_min(a->max_u,b->max_u)>=geo_coord_max(a->min_u,b->min_u)&&\n        geo_coord_min(a->max_v,b->max_v)>=geo_coord_max(a->min_v,b->min_v);'),
    # M13 打在 resolve_auto_span 收障礙物的同承載面過濾(放置當下)。GEO-261 51e9045b 把逐 cell 檢查移到
    # K geo_strip_intervals 之後,原本的 world_footprint_collides(→ W wood_contact_footprint_collides)
    # 沒有呼叫點,已於 #316 移除。I11 另外兩個「只比同承載面」的過濾是 M97(references.inc 的 reference_check_all)
    # 與 M98(W world_validation.c 的最終世界重驗):單一承載面的場景全都無感,由
    # _i11_two_surfaces_same_uv_accept.scene 殺。
    dict(id="M13", desc="I11：auto 跨距的碰撞障礙只收同承載面已放角材 -> 改收不同承載面(!= 改 ==)",
         old='        if(!t->placed||a->placement_id!=placement->id)continue;\n        if(timber_a0_footprint_uv(placement,t,a,&obstacles[obstacle_count]))++obstacle_count;',
         new='        if(!t->placed||a->placement_id==placement->id)continue;\n        if(timber_a0_footprint_uv(placement,t,a,&obstacles[obstacle_count]))++obstacle_count;'),
    dict(id="M97", desc="I11：reference_check_all 的兩兩檢查拿掉「只比同承載面」過濾(references.inc)；兩片承載面各有一支角材的 _i11_two_surfaces_same_uv_accept 必轉紅",
         file="geometry-core/references.inc",
         old='if(other_anchor.placement_id!=a->placement_id)continue;',
         new='if(0&&other_anchor.placement_id!=a->placement_id)continue;'),
    dict(id="M98", desc="I11：W 最終世界重驗的兩兩檢查拿掉「只比同承載面」過濾(world_validation.c)；同上場景必轉紅",
         file="geometry-templates/woodworking/native/world_validation.c",
         old='if(!b.member->placed||a.placement_id!=b.placement_id)continue;',
         new='if(!b.member->placed)continue;'),
    # ---- collect_stop_faces:擋面枚舉 ----
    dict(id="M14", desc="D11：只收垂直邊 -> 只收平行邊(along_v 分支)",
         file='geometry-templates/woodworking/native/contact_world.c',
         old='if(along_v&&a.v!=b.v)continue;',
         new='if(along_v&&a.v==b.v)continue;'),
    dict(id="M15", desc="D11：角材側面涵蓋範圍用錯軸(u 範圍改成 v 範圍)",
         file='geometry-templates/woodworking/native/contact_world.c',
         old='            out[count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,member->id,-1,0,WOOD_STOP_FIXED,f->min_v,f->min_u,f->max_u};\n            out[count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,member->id,-1,1,WOOD_STOP_FIXED,f->max_v,f->min_u,f->max_u};',
         new='            out[count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,member->id,-1,0,WOOD_STOP_FIXED,f->min_v,f->min_v,f->max_v};\n            out[count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,member->id,-1,1,WOOD_STOP_FIXED,f->max_v,f->min_v,f->max_v};'),
    # ---- pick_stop:唯一全寬擋面 ----
    dict(id="M16", desc="D11：擋面涵蓋檢查:丟掉 hi 側檢查(半寬也算涵蓋)",
         file='geometry-templates/woodworking/native/supports.c',
         old='if (f->fixed != at || f->lo > lo || f->hi < hi || wood_stop_shadowed(faces, i, lo, hi)) {',
         new='if (f->fixed != at || f->lo > lo || wood_stop_shadowed(faces, i, lo, hi)) {'),
    dict(id="M17", desc="D11：擋面涵蓋檢查:邊界相等不算涵蓋(> 改 >=)",
         file='geometry-templates/woodworking/native/supports.c',
         old='if (f->fixed != at || f->lo > lo || f->hi < hi || wood_stop_shadowed(faces, i, lo, hi)) {',
         new='if (f->fixed != at || f->lo >= lo || f->hi <= hi || wood_stop_shadowed(faces, i, lo, hi)) {'),
    # ---- count_legal_stops:重驗用 ----
    dict(id="M18", desc="D11：重驗擋面:FREE 邊也算合法(!= 改 ==)",
         file='geometry-templates/woodworking/native/supports.c',
         old='f->fixity != WOOD_STOP_FREE && !wood_stop_shadowed(faces, i, lo, hi)) {',
         new='f->fixity == WOOD_STOP_FREE && !wood_stop_shadowed(faces, i, lo, hi)) {'),
    # ---- resolve_auto_span ----
    dict(id="M19", desc="R6(c)：through 選段:邊界座標不算在區間內(<= 改 <)",
         file='geometry-templates/woodworking/native/member_reference.c',
         old="if (through >= intervals[i].start &&\n                through <= intervals[i].end) {",
         new="if (through > intervals[i].start &&\n                through < intervals[i].end) {"),
    dict(id="M20", desc="R6(d)：拿掉「起點必須有擋面」檢查(懸空端放行)",
         file='geometry-templates/woodworking/native/member_reference.c',
         old="    if (hits == 0) {\n        snprintf(err, err_cap, \"跨距起點沒有擋面（端面懸空）\");",
         new="    if (0) {\n        snprintf(err, err_cap, \"跨距起點沒有擋面（端面懸空）\");"),
    dict(id="M21", desc="R6(d)：拿掉「終點必須有擋面」檢查",
         file='geometry-templates/woodworking/native/member_reference.c',
         old="    if (hits == 0) {\n        snprintf(err, err_cap, \"跨距終點沒有擋面（端面懸空）\");",
         new="    if (0) {\n        snprintf(err, err_cap, \"跨距終點沒有擋面（端面懸空）\");"),
    dict(id="M22", desc="R6(d)：拿掉 FREE 擋面拒絕",
         file='geometry-templates/woodworking/native/member_reference.c',
         old='    if (stop->fixity == WOOD_STOP_FREE) {\n        snprintf(err, err_cap, "跨距終點頂到自由邊");',
         new="    if (0) {\n        snprintf(err, err_cap, \"跨距終點頂到自由邊\");"),
    dict(id="M23", desc="R6(d)：擋面歧義放行(hits>1 不拒絕)",
         equivalent="等價變異(GEO-172 實證):hits>1 需要兩個邊類擋面在同一座標且都涵蓋角材全寬。輪廓邊+孔邊 → 孔要貼輪廓,核心拒絕;兩孔共邊/共角 → 核心拒絕(兩孔分開才接受);任一為角材側面 → stop_face_shadowed 只留一個;同一簡單多邊形不可能兩邊同座標又涵蓋同段。該分支在合法輸入下不可達,改掉不改變行為。",
         file='geometry-templates/woodworking/native/member_reference.c',
         old="    if (hits > 1) {\n        snprintf(err, err_cap, \"跨距起點擋面歧義\");",
         new="    if (0) {\n        snprintf(err, err_cap, \"跨距起點擋面歧義\");"),
    dict(id="M24", desc="R6(c)：at-edge 接觸範圍:端點相接也算重疊(< 改 <=)",
         file='geometry-templates/woodworking/native/member_reference.c',
         old="if (intervals[i].start < contact_hi &&\n                intervals[i].end > contact_lo) {",
         new="if (intervals[i].start <= contact_hi &&\n                intervals[i].end >= contact_lo) {"),
    dict(id="M25", desc="R6(c)：跨距歧義放行:多區間自動選第一段",
         file='geometry-templates/woodworking/native/member_reference.c',
         old="    } else if (interval_count > 1) {",
         new="    } else if (0 && interval_count > 1) {"),
    # ---- anchor_corner_from_rect:矩形 -> 錨角 ----
    dict(id="M26", desc="I13：錨角選錯邊(min/max 對調)",
         file='geometry-templates/woodworking/native/member_reference.c',
         old='return (GeoPoint2){du>0?rect->min_u:rect->max_u,dv>0?rect->min_v:rect->max_v};',
         new='return (GeoPoint2){du>0?rect->max_u:rect->min_u,dv>0?rect->max_v:rect->min_v};'),
    # ---- a0_rect_uv:深度側 ----
    dict(id="M27", desc="深度側反轉:角材往面下長",
         old='    Vector3 axis_b =\n        depth_side == SURFACE_DEPTH_POSITIVE_NORMAL\n            ? surface->frame.normal\n            : vector_negate(surface->frame.normal);\n\n    Vector3 axis_a = vector_cross(axis_b, axis_length);',
         new='    Vector3 axis_b =\n        depth_side == SURFACE_DEPTH_POSITIVE_NORMAL\n            ? vector_negate(surface->frame.normal)\n            : surface->frame.normal;\n\n    Vector3 axis_a = vector_cross(axis_b, axis_length);'),
    # ---- at-grid 中線:奇數寬拆分 ----
    dict(id="M28", desc="I13：奇數寬多的 1mm 改放 -cross 側",
         file='geometry-templates/woodworking/native/member_reference.c',
         old="widths[0][0]=center-t->size_a/2;",
         new="widths[0][0]=center-(t->size_a+1)/2;"),
    # ---- at-edge 材料側 ----
    dict(id="M29", desc="I13：外輪廓材料側反轉(footprint 長到面外)",
         file='geometry-templates/woodworking/native/member_reference.c',
         old='GeoCoord inward=(along?e.outward.u:e.outward.v)*(e.hole<0?-1:1);',
         new='GeoCoord inward=(along?e.outward.u:e.outward.v)*(e.hole<0?(along?1:-1):1);'),
    dict(id="M30", desc="I13：孔邊材料側反轉(footprint 長進孔裡)",
         file='geometry-templates/woodworking/native/member_reference.c',
         old='GeoCoord inward=(along?e.outward.u:e.outward.v)*(e.hole<0?-1:1);',
         new='GeoCoord inward=(along?e.outward.u:e.outward.v)*(e.hole<0?-1:(along?1:-1));'),
    # ---- grid ----
    dict(id="M31", desc="I10：格線座標遞增改非嚴格(<= 改 <)",
         file='geometry-core/kernel/grid.c',
         old="        if (i > 0 && coords[i] <= coords[i - 1]) {",
         new="        if (i > 0 && coords[i] < coords[i - 1]) {"),
    dict(id="M32", desc="I10：格線座標上下界改成嚴格(壓邊界的格線拒絕)",
         file='geometry-core/kernel/grid.c',
         old="        if (out[k] < lo || out[k] > hi) {",
         new="        if (out[k] <= lo || out[k] >= hi) {"),
    # ---- GEO-101:between 明寫兩端（R21）----
    dict(id="M57", desc="R21：between 的 FREE 邊檢查反轉(明寫就放行自由邊)",
         file='geometry-templates/woodworking/native/supports.c',
         old='        if (f->fixity == WOOD_STOP_FREE) {',
         new='        if (f->fixity == WOOD_STOP_FIXED) {'),
    dict(id="M58", desc="R21：between 不再要求跨距落在合法區間內(可穿過實體)",
         file='geometry-templates/woodworking/native/member_reference.c',
         old="                bool inside = false;",
         new="                bool inside = true;"),
    # ---- GEO-099:網格引用鎖（I23）----
    dict(id="M51", desc="I23：I23(a) 拿掉座標比對(移動已錨定的線也放行)",
         retired="GEO-125(commit bc87d02,2026-09-18)解除 I23(a) 引用鎖:apply_grid_line 已無 was/now 座標比對區塊(整段刪除);公理層 I23(a) 改為「不再直接拒絕,重新推導引用它的角材並走 I8a 影響預覽」。取代它的是重算 + 預覽機制,不是同一判定的新寫法,故退役。",
         old="            if (!had || !has || was != now) {",
         new="            if (!had || !has) {"),
    dict(id="M52", desc="I10：重宣告改成疊加而非整軸換掉",
         old="            grid->axis[axis] = blank;   /* 重宣告 = 整軸換掉，不是疊加 */",
         new="            (void)blank;   /* 重宣告 = 整軸換掉，不是疊加 */"),
    # ---- GEO-100:I23(b) 重驗時的索引存在性 ----
    dict(id="M56", desc="I23：I23(b) 不再檢查被錨定的索引是否仍推導得出",
         equivalent="等價變異(GEO-173 實證,更正 GEO-100 的舊結論):world_validate_derived 只在 reference_rebuild 成功後才跑,而 reference_rebuild → reference_place_geometry 對每個 AT_GRID 角材已先跑同一個 grid_anchor_line_coord(同 grids/count/grid/placement/axis/index/has_band/band;boundary 若為自帶 rect 的合成輪廓,其 bounds/area 與 NULL boundary 的 rect 路徑相同),索引消失會先在那裡失敗;被變異那行在現行語意(2026-09-18 反轉為重算)下永遠是 no-op。夾具 M56_grid_index_vanish(面縮到索引 7 消失)原始版與變異版輸出逐字相同。",
         file='geometry-templates/woodworking/native/world_validation.c',
         old='                !wood_grid_anchor_line_coord(grids->items,grids->count,grid,&anchor_host,fact.grid_axis,fact.grid_index,',
         new='                (false) && wood_grid_anchor_line_coord(grids->items,grids->count,grid,&anchor_host,fact.grid_axis,fact.grid_index,'),
    # ---- GEO-100:面材推導（D10a）----
    dict(id="M53", desc="D10a：縫中心線改成縫起點(少加 gap/2)",
         file='geometry-core/kernel/grid.c',
         old='{ return geo_period_body(anchor,body,gap,k)+body+gap/2; }',
         new='{ return geo_period_body(anchor,body,gap,k)+body; }'),
    dict(id="M54", desc="D10a：產生條件由嚴格小於放寬成小於等於(多出尾端一條)",
         file='geometry-core/kernel/grid.c',
         old="            if (gap_hi >= hi) {",
         new="            if (gap_hi > hi) {"),
    dict(id="M55", desc="D10a：縫寬奇數不再拒絕(改成只擋負數)",
         retired="GEO-122 / GEO-125(commit bc87d02,2026-09-18)刪除奇數縫寬拒絕:apply_grid_line 的 `p_gap % 2 != 0` 檢查已移除(只剩一行過期註解),公理層 D10a「gap 為奇數不拒絕」,縫中心線取下界(錨點在 current_geometry.c:1495 `def->anchor + k*T + def->panel + def->gap / 2`,該公式仍由 M53 變異)。被變異的拒絕已不屬於產品。",
         old="            if (p_gap % 2 != 0) {",
         new="            if (p_gap < 0) {"),
    dict(id="M33", desc="I13：at-grid 軸向守門員反轉",
         file='geometry-templates/woodworking/native/member_reference.c',
         old='g.placement_id!=p.id||(a->ref_grid_axis==0)!=along)',
         new='g.placement_id!=p.id||(a->ref_grid_axis==0)==along)'),
    # ---- at-edge 方向守門員 ----
    dict(id="M34", desc="I13：at-edge 平行守門員反轉",
         file='geometry-templates/woodworking/native/member_reference.c',
         old='if((e.segment.start.u==e.segment.end.u)!=along)',
         new='if((e.segment.start.u==e.segment.end.u)==along)'),
    # ---- timber_construct ----
    dict(id="M35", desc="明寫長度允許 L=0(<= 改 <)",
         retired="GEO-125(commit bc87d02,2026-09-18)廢除明寫長度:timber_construct 現在以 `!auto_length ||` 一律拒絕明寫長度(current_geometry.c timber_construct),`(!auto_length && length <= 0)` 這條判定隨整個分支消失;apply_timber_line 的訊息亦改為「明寫長度已廢除」,公理層 D7/I18/R4 同。沒有可對應的現行判定,不另編變異湊數。",
         old="        (!auto_length && length <= 0) ||",
         new="        (!auto_length && length < 0) ||"),
    # ---- world_revalidate ----
    dict(id="M36", desc="R6(e)：重驗跳過端點擋面檢查",
         equivalent='等價變異(冗餘檢查,2026-10-01 實證):被變異的是 world_validate_derived 內的 R6(d)/R21 端面唯一擋面檢查,它唯一的呼叫者是 world_revalidate,而 world_revalidate 在它之前(同一個 candidate、reference_rebuild 之後)先跑 reference_check_all(references.inc:485-491),對每支已放角材算同一個 collect_stop_faces / count_legal_stops / 同一個 hits==0||(!has_between&&hits!=1) 條件,不過就 return false、根本到不了 world_validate_derived;兩處輸入(candidate 的 timbers/anchors/placements/boundaries)逐項相同,中間只改 candidate.spaces,不影響擋面。差分測試:基準 exe 與 M36 變異 exe 對 7143 個輸入(根目錄 143 個 .scene + tests/fuzz_scene.py 語料 3000 案 seed 1 + 4000 個 surface/grid 重宣告擾動,其中基準接受 362、重驗拒絕 612)比 exit code / stdout / stderr,零分歧;基準輸出從未出現 world_validate_derived 的專屬訊息「R6(d): 端面需要恰好一個涵蓋全寬的合法擋面」。另:同時拿掉兩處檢查 136/136 仍全過(前一輪探針)。此塊是 reference_check_all 的重複防線,不是獨立判定。',
         file='geometry-templates/woodworking/native/world_validation.c',
         old='        WoodStopFace faces[WOOD_CONTACT_FACE_CAPACITY];\n        size_t count=context->stops(context->user,fact.placement_id,&footprint,along_v,member,faces,WOOD_CONTACT_FACE_CAPACITY);\n        GeoCoord ends[2]={along_v?footprint.min_v:footprint.min_u,along_v?footprint.max_v:footprint.max_u};\n        GeoCoord lo=along_v?footprint.min_u:footprint.min_v,hi=along_v?footprint.max_u:footprint.max_v;\n        for(size_t end=0;end<2;++end){size_t hits=wood_stop_count_legal(faces,count,ends[end],lo,hi);\n            WoodBoundaryEndAdmission admission=WOOD_BOUNDARY_END_ORDINARY;\n            if(member->role==WOOD_MEMBER_ROLE_BOUNDARY&&context->boundary_end){\n                if(!context->boundary_end(context->user,fact.placement_id,&footprint,member,along_v,(int)end,faces,count,&admission))return false;\n                if(admission==WOOD_BOUNDARY_END_PARTIAL)continue;\n                if(admission==WOOD_BOUNDARY_END_BARE_RC)return validation_refuse(error,capacity,"V_CUT_PRIORITY：固定段端點有裸露的可放料 RC 面，必須先貼角材");\n            }\n            if(!hits||(!fact.has_between&&hits!=1))\n                return validation_refuse(error,capacity,"R6(d): 端面需要恰好一個涵蓋全寬的合法擋面");\n        }',
         new='        if(0){\n        WoodStopFace faces[WOOD_CONTACT_FACE_CAPACITY];\n        size_t count=context->stops(context->user,fact.placement_id,&footprint,along_v,member,faces,WOOD_CONTACT_FACE_CAPACITY);\n        GeoCoord ends[2]={along_v?footprint.min_v:footprint.min_u,along_v?footprint.max_v:footprint.max_u};\n        GeoCoord lo=along_v?footprint.min_u:footprint.min_v,hi=along_v?footprint.max_u:footprint.max_v;\n        for(size_t end=0;end<2;++end){size_t hits=wood_stop_count_legal(faces,count,ends[end],lo,hi);\n            WoodBoundaryEndAdmission admission=WOOD_BOUNDARY_END_ORDINARY;\n            if(member->role==WOOD_MEMBER_ROLE_BOUNDARY&&context->boundary_end){\n                if(!context->boundary_end(context->user,fact.placement_id,&footprint,member,along_v,(int)end,faces,count,&admission))return false;\n                if(admission==WOOD_BOUNDARY_END_PARTIAL)continue;\n                if(admission==WOOD_BOUNDARY_END_BARE_RC)return validation_refuse(error,capacity,"V_CUT_PRIORITY：固定段端點有裸露的可放料 RC 面，必須先貼角材");\n            }\n            if(!hits||(!fact.has_between&&hits!=1))\n                return validation_refuse(error,capacity,"R6(d): 端面需要恰好一個涵蓋全寬的合法擋面");\n        }\n        }'),
    dict(id="M37", desc="I11：碰撞兩兩檢查變成自己也算(j=i+1 改 j=i)",
         file='geometry-templates/woodworking/native/world_validation.c',
         old='for(size_t j=i+1;j<context->member_count;++j)',
         new='for(size_t j=i;j<context->member_count;++j)'),
    # ---- parse_edge_ref ----
    dict(id="M38", desc="I13：at-edge 邊參照:孔索引 <0 也放行(hole<0 檢查拿掉)",
         old="        if (!parse_i64(buf, &hole) || hole < 0) {",
         new="        if (!parse_i64(buf, &hole) || hole < -99) {"),
    # ---- span cell:零長 cell 處理 ----
    dict(id="M39", desc="R6(a)：切點去重用 < 不去重(零長 cell 出現)",
         file='geometry-core/kernel/geometry.c',
         old='for(size_t i=0;i<count;++i)if(!unique||cuts[i]!=cuts[unique-1])cuts[unique++]=cuts[i];',
         new='for(size_t i=0;i<count;++i)if(!unique||cuts[i]<cuts[unique-1])cuts[unique++]=cuts[i];'),
    # ---- span:選段後端點檢查順序 ----
    dict(id="M40", desc="R6(b)：有效 cell 判定拿掉碰撞(只查包含)",
         file='geometry-core/kernel/geometry.c',
         old='        ok=geo_region_set_contains_rect(domain,&cell);\n        for(size_t k=0;ok&&k<obstacle_count;++k)if(geo_rect_overlap_positive(&cell,&obstacles[k]))ok=false;',
         new='        ok=geo_region_set_contains_rect(domain,&cell);'),
    dict(id="M71", desc="R7/#198 A：以 bbox 冒充單 slab 的多段交集",
         old="            if (++intervals > 1) return -1;\n            left = l; right = r;",
         new="            if (++intervals == 1) { left = l; right = r; }\n            else { left = coord_min(left,l); right = coord_max(right,r); }"),
    dict(id="M72", desc="R7/#198 B：恢復四角全在外就丟棄的錯誤快退",
         old="    Coord cuts[POLY_MAX_VERTICES + 2] = { in_v0, in_v1 };",
         new="    SurfacePoint2 legacy_corners[4] = {{in_u0,in_v0},{in_u1,in_v0},{in_u1,in_v1},{in_u0,in_v1}};\n    int legacy_inside = 0;\n    for (int i=0; i<4; ++i) legacy_inside += poly_contains_point(loop, legacy_corners[i]);\n    if (!legacy_inside) return 0;\n    Coord cuts[POLY_MAX_VERTICES + 2] = { in_v0, in_v1 };"),
    dict(id="M73", desc="R7/#202：丟棄正面積矩形外的孤立線／點接觸",
         old="                (l < u0 || r > u1 || bottom < v0 || top > v1)) return -1;",
         new="                (l < u0 || r > u1 || bottom < v0 || top > v1)) { /* discard closed contact */ }"),
    dict(id="M74", desc="R12/#202：未 cut-strip 仍要求單矩形切削分類",
         old="                if (items[i].cls == OBSTACLE_STRIP && !cut_strip) {",
         new="                if (false) {"),
    dict(id="M75", desc="R14/R15/#202：未裁切 strip 提前成功、忽略其餘項及選片",
         old="            matched = true;\n            /* 選片:矩形應只與一片接觸;橫跨拆分線=無法歸屬,拒絕。 */",
         new="            matched = true;\n            if (items[i].cls == OBSTACLE_STRIP && !cut_strip) return true;\n            /* 選片:矩形應只與一片接觸;橫跨拆分線=無法歸屬,拒絕。 */"),
    dict(id="M76", desc="R3/R4/R8/#202：第三段覆蓋弧循環接回第一片",
         old="            if (++covered_runs > 2) return false;",
         new="            ++covered_runs; /* incorrectly reconnect third residue */"),
    dict(id="M77", desc="R7/#202：以同側遠處貼邊豁免純角點接觸",
         old="        if (!local_flush && poly_point_on_edge(loop, corners[i])) return -1;",
         new="        if (!f[(i==0||i==3)?0:1] && !f[i<2?2:3] && poly_point_on_edge(loop, corners[i])) return -1;"),
    # ---- #240 P-143(看板任務 29):S7 / S1 核心場景的牙齒 ----
    # GEO-261: the predicate is K geo_segment_crosses_rect_interior (same text, Geo* names).
    dict(id="M86", desc="I5/S7：開內部判定拿掉——邊落在矩形邊上、或與矩形只零長度接觸，也算穿入內部(兩軸的嚴格不等號與 lo<hi 全改含邊界)；貼齊的場景 _s7a 必轉紅(被 M05/M06 涵蓋，只作回歸)",
         file="geometry-core/kernel/geometry.c",
         old="        if (a.u <= min_u || a.u >= max_u) {\n            return false;\n        }\n        GeoCoord lo = geo_coord_max(geo_coord_min(a.v, b.v), min_v);\n        GeoCoord hi = geo_coord_min(geo_coord_max(a.v, b.v), max_v);\n        return lo < hi;\n    }\n\n    if (a.v <= min_v || a.v >= max_v) {\n        return false;\n    }\n    GeoCoord lo = geo_coord_max(geo_coord_min(a.u, b.u), min_u);\n    GeoCoord hi = geo_coord_min(geo_coord_max(a.u, b.u), max_u);\n    return lo < hi;",
         new="        if (a.u < min_u || a.u > max_u) {\n            return false;\n        }\n        GeoCoord lo = geo_coord_max(geo_coord_min(a.v, b.v), min_v);\n        GeoCoord hi = geo_coord_min(geo_coord_max(a.v, b.v), max_v);\n        return lo <= hi;\n    }\n\n    if (a.v < min_v || a.v > max_v) {\n        return false;\n    }\n    GeoCoord lo = geo_coord_max(geo_coord_min(a.u, b.u), min_u);\n    GeoCoord hi = geo_coord_min(geo_coord_max(a.u, b.u), max_u);\n    return lo <= hi;"),
    # GEO-261: the V_EXTENSION span check is W wood_member_span_extension_check.
    dict(id="M87", desc="I22/S1：拿掉「非 boundary 角材的 footprint 不得超出定位邊」的拒絕(V_EXTENSION)；primary 整支穿過凹角的 _s1_p8 必轉紅",
         file="geometry-templates/woodworking/native/contacts.c",
         old="    if (has_edge && self->role != WOOD_MEMBER_ROLE_BOUNDARY &&\n        (span_lo < edge_lo || span_hi > edge_hi)) {",
         new="    if (0 && has_edge && self->role != WOOD_MEMBER_ROLE_BOUNDARY &&\n        (span_lo < edge_lo || span_hi > edge_hi)) {"),
    dict(id="M88", desc="I22/S1(#295 審查須改 2):V_EXTENSION 只驗「超出起點」,拿掉「超出終點」那一半;凹角在定位邊高端的 _s1_p8b 必轉紅",
         file="geometry-templates/woodworking/native/contacts.c",
         old="        (span_lo < edge_lo || span_hi > edge_hi)) {",
         new="        (span_lo < edge_lo)) {"),
    # I22/#299：V_EXTENSION 訊息逐欄位的牙齒。contacts.c 的 snprintf 與兩段 clause 各拿掉一個欄位，
    # contact_world.c 的定位邊編號回報一個；判定在 run_tests.py 的 p8、p8b(error 清單 + error_not)。
    dict(id="M89", desc="I22/#299：V_EXTENSION 訊息的料件欄位拿掉(角材編號固定印成 0)；p8、p8b、_role_priority_mutant 必轉紅",
         file="geometry-templates/woodworking/native/contacts.c",
         old='(unsigned)self->id, edge_index,',
         new='0u, edge_index,'),
    dict(id="M90", desc="I22/#299：V_EXTENSION 訊息拿掉定位邊編號 e<i>；p8、p8b 必轉紅",
         file="geometry-templates/woodworking/native/contacts.c",
         old='"——定位邊 e%d [%lld,%lld] mm%s%s",\n                     (unsigned)self->id, edge_index,',
         new='"——定位邊 [%lld,%lld] mm%s%s",\n                     (unsigned)self->id,'),
    dict(id="M91", desc="I22/#299：V_EXTENSION 訊息拿掉定位邊區間 [edge_lo,edge_hi] mm；p8、p8b 必轉紅",
         file="geometry-templates/woodworking/native/contacts.c",
         old='"——定位邊 e%d [%lld,%lld] mm%s%s",\n                     (unsigned)self->id, edge_index,\n                     (long long)edge_lo, (long long)edge_hi, low_note, high_note);',
         new='"——定位邊 e%d%s%s",\n                     (unsigned)self->id, edge_index,\n                     low_note, high_note);'),
    dict(id="M92", desc="I22/#299：V_EXTENSION 訊息拿掉「低端超出」區間；凹角在定位邊低端的 _s1_p8 必轉紅",
         file="geometry-templates/woodworking/native/contacts.c",
         old='if (edge_lo > span_lo) {',
         new='if (0) {'),
    dict(id="M93", desc="I22/#299：V_EXTENSION 訊息拿掉「高端超出」區間；凹角在定位邊高端的 _s1_p8b 必轉紅",
         file="geometry-templates/woodworking/native/contacts.c",
         old='if (edge_hi < span_hi) {',
         new='if (0) {'),
    dict(id="M94", desc="I22/#299：V_EXTENSION 訊息的「低端超出」不論有沒有超出都印(多印一段假區間)；_s1_p8b 的 error_not 必轉紅",
         file="geometry-templates/woodworking/native/contacts.c",
         old='if (edge_lo > span_lo) {',
         new='if (1) {'),
    dict(id="M95", desc="I22/#299：V_EXTENSION 訊息的「高端超出」不論有沒有超出都印(多印一段假區間)；_s1_p8 的 error_not 必轉紅",
         file="geometry-templates/woodworking/native/contacts.c",
         old='if (edge_hi < span_hi) {',
         new='if (1) {'),
    dict(id="M96", desc="I22/#299：W 的 wood_contact_boundary_edge 不回報定位邊編號(訊息印成 e-1)；p8、p8b 必轉紅",
         file="geometry-templates/woodworking/native/contact_world.c",
         old='if(out_edge)*out_edge=edge;',
         new='(void)edge;'),
]


# P-135/P-141: the preview-only guards require the actual bridge, not core.exe.
MUTANTS += [
    dict(id="M61", desc="D60/K2a：恢復已刪卡片鍵保留，令無引用同鍵重建轉紅", binary="bridge",
         file="geometry-core/parameters.inc", old="    ParameterSet card;geo_parameters_begin_definition(&w->geo.parameters,id,&card);",
         new='    {const ParameterCandidateLedger *ledger=parameter_ledger(w);for(size_t r=0;ledger&&r<ledger->field_retirement_count;++r)if(ledger->field_retirements[r].parameter_id==id)return parameter_fail("I38 DUPLICATE: a deleted identity cannot be declared again");}\n    ParameterSet card;geo_parameters_begin_definition(&w->geo.parameters,id,&card);',
         tests=["tests.test_grid_system_contract.GridSystemContract.test_k2a_parameter_confirmation_receipt_includes_intermediate_deletion"]),
    dict(id="M62", desc="I38：同鍵卡片已重建就跳過未處理引用", binary="bridge",
         file="geometry-core/parameters.inc",
         old="        if(r->at!=parameter_field_generation(w,id,r->field_id))continue; /* last actual deletion */",
         new="        if(parameter_find(w,id))continue;\n        if(r->at!=parameter_field_generation(w,id,r->field_id))continue; /* last actual deletion */",
         tests=["tests.test_parameters_core.ParametersCore.test_delete_then_import_or_redeclare_keeps_the_deletion_receipt",
                "tests.test_parameters_core.ParametersCore.test_referenced_card_rebuild_without_referrer_declaration_rejects"]),
    dict(id="M63", desc="I38：欄位鍵已重建就跳過省略重建的引用保護", binary="bridge",
         file="geometry-core/parameters.inc",
         old="        if(r->at!=parameter_field_generation(w,id,r->field_id))continue; /* last actual deletion */",
         new="        if(parameter_field_index(w,id,r->field_id)>=0)continue;\n        if(r->at!=parameter_field_generation(w,id,r->field_id))continue; /* last actual deletion */",
         tests=["tests.test_parameters_core.ParametersCore.test_referenced_field_omission_and_rebuild_requires_declaration"]),
    dict(id="M64", desc="I38：引用處理錯看第一次而非最後一次欄位刪除", binary="bridge",
         file="geometry-core/parameters.inc",
         old="if(r->parameter_id==id&&r->field_id==field&&r->at>at)at=r->at;",
         new="if(r->parameter_id==id&&r->field_id==field&&!at)at=r->at;",
         tests=["tests.test_parameters_core.ParametersCore.test_referrer_must_be_declared_after_the_last_card_deletion"]),
    dict(id="M65", desc="I38/P129：grid單軸宣告錯誤涵蓋未宣告軸", binary="bridge",
         file="geometry-core/parameters.inc", old="d->kind==kind&&d->id==id&&d->slot==slot",
         new="d->kind==kind&&d->id==id&&(kind==PARAM_OWNER_ENG_GRID||d->slot==slot)",
         tests=["tests.test_parameters_core.ParametersCore.test_direct_grid_axis_redeclaration_is_local"]),
    dict(id="M66", desc="I8a/P129：預覽隱藏刪除後明確重新宣告的引用者", binary="bridge",
         file="geometry-web/engineering_bridge.inc",
         old="if(p)for(size_t i=0;i<p->retirement_count;++i)",
         new="if(0&&p)for(size_t i=0;i<p->retirement_count;++i)",
         tests=["tests.test_parameters_core.ParametersCore.test_preview_discloses_only_last_deletion_redeclarations"]),
    dict(id="M67", desc="I8a/P129：預覽誤用第一次刪除的處理資訊", binary="bridge",
         file="geometry-web/engineering_bridge.inc",
         old="for(size_t k=i+1;k<p->retirement_count;++k)", new="for(size_t k=0;k<i;++k)",
         tests=["tests.test_parameters_core.ParametersCore.test_preview_discloses_only_last_deletion_redeclarations"]),
    dict(id="M68", desc="I38/D44/P141：漏列面材試排gap/stagger/threshold參數引用", binary="bridge",
         file="geometry-core/parameters.inc",
         old="for(size_t i=0;i<w->wood.finish_surfaces.fill_count;++i)",
         new="for(size_t i=0;false&&i<w->wood.finish_surfaces.fill_count;++i)",
         tests=["tests.test_parameters_core.ParametersCore.test_panel_fill_gap_rebuild_requires_prior_reference_change",
                "tests.test_parameters_core.ParametersCore.test_panel_fill_stagger_rebuild_requires_prior_reference_change",
                "tests.test_parameters_core.ParametersCore.test_panel_fill_threshold_rebuild_requires_prior_reference_change"]),
    dict(id="M69", desc="P065/P141：重建後解除來源錯用刪除前快取而非當下99", binary="bridge",
         file="geometry-core/parameters.inc",
         old="    if(parameter_field_index(w,ref.parameter_id,ref.field_id)>=0)return false;",
         new="    /* mutation: let an old retirement override the currently present source */",
         tests=["tests.test_parameters_core.ParametersCore.test_delete_rebuild_then_unbind_reads_current_99_instead_of_deleted_cache"]),
    dict(id="M70", desc="P142/P150：來源只刪未重建時停用最後有效27快取", binary="bridge",
         file="geometry-core/parameters.inc",
         old="    if(parameter_field_index(w,ref.parameter_id,ref.field_id)>=0)return false;",
         new="    /* mutation: never consume an ended-generation value */ return false;",
         tests=["tests.test_parameters_deleted_unbind.DeletedSourceUnbind.test_delete_then_unbind_has_identical_dump_to_legal_order"]),
]


# GEO-262 / P-142 B2: whole-card grid owners share parameter_uses and the I38
# rejection with the D44 panel-fill owners (bridge-backed, like P-141 above).
B2_TESTS = ["tests.test_grid_card_reference.GridCardReference.test_P142_B2_CARD_AND_PANEL_FILL_%s_SHARE_I38_REJECTION" % slot
            for slot in ("GAP", "STAGGER", "THRESHOLD")]
MUTANTS += [
    dict(id="M78", desc="I38/I74 P142-B2：原生擁有者領頭的拒絕只計數、不指名同欄可改綁的引用者", binary="bridge",
         file="geometry-core/parameters.inc",
         old='parameter_names_fit(other,used<limit?limit-used:0,uses.other_text,uses.other_count,": ");',
         new='parameter_names_fit(other,used<limit?limit-used:0,uses.other_text,0,": ");',
         tests=B2_TESTS),
    dict(id="M84", desc="I38/P142-B2：引用者名單不檢查剩餘長度，名稱在255位元組處被截斷", binary="bridge",
         file="geometry-core/parameters.inc",
         old="        if(need>room)continue;",
         new="        if(false)continue;",
         tests=["tests.test_grid_card_reference.GridCardReference.test_P142_B2_LONG_OWNER_LIST_KEEPS_COMPLETE_NAMES"]),
    dict(id="M79", desc="I38/P142-B2：整卡網格引用者不列入共用 parameter_uses", binary="bridge",
         file="geometry-core/parameters.inc",
         old="if(r->set&&r->parameter_id==id&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_GRID_CARD,s->id,0))",
         new="if(false&&r->set&&r->parameter_id==id&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_GRID_CARD,s->id,0))",
         tests=B2_TESTS[:1]),
]

# GEO-262 / P-142 S1: grid-system field references are redeclared by put-grid-system,
# so they are no longer native-only owners of the separate-transaction guidance.
S1_TEST = "tests.test_grid_card_reference.GridCardReference.test_P142_S1_GRID_SYSTEM_FIELD_REBIND_IN_SAME_CANDIDATE"
MUTANTS += [
    dict(id="M80", desc="I38/P142-S1：網格系統逐欄引用仍歸為無法同候選改綁的原生擁有者", binary="bridge",
         file="geometry-core/parameters.inc",
         old='parameter_use(u,"grid-system %u %c %s",',
         new='parameter_native_use(u,"grid-system %u %c %s",',
         tests=[S1_TEST, "tests.test_parameters_core.ParametersCore.test_native_consumers_require_explicit_rebinding_after_parameter_rebuild"]),
    dict(id="M81", desc="I38/P129/P142-S1：put-grid-system 未宣告其逐欄來源，刪後重建同鍵無法改綁", binary="bridge",
         file="geometry-core/card_reference.inc",
         old="return parameter_declare(w,PARAM_OWNER_GRID_CARD,s.id,0)&&parameter_declare(w,PARAM_OWNER_GRID_SYSTEM,s.id,0);",
         new="return parameter_declare(w,PARAM_OWNER_GRID_CARD,s.id,0);",
         tests=[S1_TEST]),
    # GEO-261: main 4b975a3d skipped parameter_coord only when the referenced card
    # no longer exists (grid_systems.inc rebuild loop). The same single cause now sits
    # in the H coordinate resolver every K grid evaluation calls: a deleted card
    # reports success and leaves the cached length untouched; missing field, unit and
    # D1 failures still reject. The candidate's source graph re-reads the parameter
    # source (W wood_grid_coordinate_source) and still rejects, but without the
    # I38 MISSING diagnostic and its grid/card/field identity, which is what the
    # named test asserts (Windows/MSVC: "grid-system 4 u: " instead of I38 MISSING).
    dict(id="M85", desc="I38/D29/P142-S1：網格系統引用的參數卡片已刪除時，H 座標解析器回報成功並保留快取長度（病因只限卡片不存在；缺欄位、單位、座標範圍超限仍拒絕）。來源圖對參數來源的二次檢查仍會拒絕，但診斷失去 I38 MISSING 與 grid／card／field 身分", binary="bridge",
         file="geometry-core/grid_systems.inc",
         old="{ return parameter_coord((const World *)state,ref,out); }",
         new="{ if(!parameter_find((const World *)state,ref.parameter_id))return true; return parameter_coord((const World *)state,ref,out); }",
         tests=["tests.test_grid_card_reference.GridCardReference.test_P142_S1_REDECLARATION_WITHOUT_REBUILD_REJECTS"]),
]

# GEO-262 / P-142 S2 after #193: the merged source rebuilds a card and unbinds a
# field source and a whole-card grid in one ordered candidate (both must read 99).
S2_TEST = "tests.test_grid_card_reference.GridCardReference.test_P142_S2_INTEGRATED_FIELD_AND_CARD_REBUILD_READS_99"
MUTANTS += [
    dict(id="M82", desc="P065/P142-S2：同候選曾刪除的欄位即使已重建仍走刪除前快取（整合後逐欄得27非99）", binary="bridge",
         file="geometry-core/parameters.inc",
         old="    if(parameter_field_index(w,ref.parameter_id,ref.field_id)>=0)return false;",
         new="    if(parameter_field_index(w,ref.parameter_id,ref.field_id)>=0&&!parameter_field_generation(w,ref.parameter_id,ref.field_id))return false;",
         tests=[S2_TEST]),
    dict(id="M83", desc="R60/P142-S2：整卡轉直接值因同候選曾刪除一律拒絕，不讀已重建的當步值", binary="bridge",
         file="geometry-core/card_reference.inc",
         old="                char error[512];",
         new='                char error[512];for(int a=0;a<2;++a)if(parameter_field_generation(w,s->card_reference.parameter_id,s->card_reference.fields[a]))return grid_card_fail("R60 capture grid-system %u parameter %u: deleted earlier in this candidate",id,s->card_reference.parameter_id);',
         tests=[S2_TEST]),
]


# #314: M89-M98 remain reserved for the #299/#316 combined patch. These
# submission guards run real bridge/native judges; M110 is preview-masked and
# is deliberately equivalent alone (the paired MP1+MP3 witness is separate).
STAGGER_TEST = "tests.test_geo314_stagger_commit.StaggerCommit."
STAGGER_TABLE = "tests.test_geo261_wood_grid_application.WoodGridApplication.test_stagger_commit_decision_table_and_ordered_sources"
MUTANTS += [
    dict(id="M99", desc="I24/#314 MS1：移除整份提交比較，互動新雙軸應由具名拒絕斷言抓住", binary="bridge",
         file="current_geometry.c", old="if (!grid_stagger_submission_valid(candidate,grid_error,sizeof grid_error)) {",
         new="if (false && !grid_stagger_submission_valid(candidate,grid_error,sizeof grid_error)) {",
         tests=[STAGGER_TEST + "test_C1_new_direct_and_repeat_panel_dual_axes_reject_M1"]),
    dict(id="M100", desc="I24/#314 MS2：移除隔離重放豁免，舊雙軸場景必須仍能讀回", binary="bridge",
         file="geometry-core/subgrid_world.inc", old="if(g_parsing_scene_file||!g_subgrid_before)return true;",
         new="if(!g_subgrid_before)return true;",
         tests=[STAGGER_TEST + "test_L1_all_frozen_legacy_modes_load_and_dump_byte_identically"]),
    dict(id="M101", desc="I24/#314 MS3：移除新建／新增第二軸M1拒絕", binary="bridge",
         file="geometry-templates/woodworking/native/grid_application.c",
         old="if(!old||!(old->axis[0].stagger_set&&old->axis[1].stagger_set))", new="if(0)", tests=[STAGGER_TABLE]),
    dict(id="M102", desc="I24/#314 MS4：移除舊雙軸改值M2拒絕", binary="bridge",
         file="geometry-templates/woodworking/native/grid_application.c",
         old="if(wood_grid_stagger_value_changed(&old->axis[axis],&now->axis[axis],now->id,(unsigned)axis,facts,count))", new="if(0)", tests=[STAGGER_TABLE]),
    dict(id="M103", desc="I24/#314 MS5：移除同ParameterRef改卡例外", binary="bridge",
         file="geometry-templates/woodworking/native/grid_application.c",
         old="if(prior->set&&current->set&&prior->parameter_id==current->parameter_id&&prior->field_id==current->field_id)return false;",
         new="if(0)return false;", tests=[STAGGER_TABLE]),
    dict(id="M104", desc="I24/#314 MS6：把一軸誤判為雙軸，合法換方向必轉紅", binary="bridge",
         file="geometry-templates/woodworking/native/grid_application.c",
         old="if(!(now->axis[0].stagger_set&&now->axis[1].stagger_set))continue;",
         new="if(!(now->axis[0].stagger_set||now->axis[1].stagger_set))continue;", tests=[STAGGER_TABLE]),
    dict(id="M105", desc="I24/#314 MS7：只比較u而漏驗v改值", binary="bridge",
         file="geometry-templates/woodworking/native/grid_application.c",
         old="for(int axis=0;axis<2;++axis)if(wood_grid_stagger_value_changed",
         new="for(int axis=0;axis<1;++axis)if(wood_grid_stagger_value_changed", tests=[STAGGER_TABLE]),
    dict(id="M106", desc="I24/#314 MS8：來源變更不再比較有效值", binary="bridge",
         file="geometry-templates/woodworking/native/grid_application.c",
         old="return old->stagger!=now->stagger;", new="return 0;", tests=[STAGGER_TABLE]),
    dict(id="M107", desc="I24/#314 MS9：移除缺store的fail-closed拒絕；正常ASSERT而非NULL crash", binary="bridge",
         file="geometry-templates/woodworking/native/grid_application.c",
         old="if(!after||!before||(!facts&&count))return wood_grid_error", new="if(0)return wood_grid_error", tests=[STAGGER_TABLE]),
    dict(id="M108", desc="I24/#314 MP1：漏接互動archive提交前基線，預覽必須先擋新雙軸", binary="bridge",
         file="geometry-core/transactions.inc", old="const World *previous_baseline=g_subgrid_before;g_subgrid_before=call->before;",
         new="const World *previous_baseline=g_subgrid_before;g_subgrid_before=NULL;",
         tests=[STAGGER_TEST + "test_C3_archive_new_and_existing_second_axes_reject_M1"]),
    dict(id="M109", desc="I24/#314 MP2：漏接batch提交前基線，整批新增第二軸必拒絕", binary="bridge",
         file="geometry-web/engineering_bridge.inc", old="g_subgrid_before=call->before;ok=world_revalidate(candidate);",
         new="g_subgrid_before=NULL;ok=world_revalidate(candidate);",
         tests=[STAGGER_TEST + "test_C4_batch_new_and_added_second_axes_reject_M1"]),
    dict(id="M110", desc="I24/#314 MP3：漏接confirm基線，單獨被preview遮蔽", binary="bridge",
         file="current_geometry.c", old="const World *previous=g_subgrid_before;g_subgrid_before=&candidate->before;",
         new="const World *previous=g_subgrid_before;g_subgrid_before=NULL;",
         equivalent="單獨移除confirm基線不能越過原preview的新雙軸拒絕；MP1+MP3配對見證另以真候選證明confirm縱深，不冒稱此單突變killed。",
         tests=[STAGGER_TEST + "test_C3_archive_new_and_existing_second_axes_reject_M1"]),
    dict(id="M111", desc="I24/#314 MP4：固定default程式加入雙軸定義，原靜態變更警報必轉紅", binary="bridge",
         file="geometry-core/transactions.inc", old="static const char *const app_default_replay_lines[]={",
         new='static const char *const app_default_replay_lines[]={\n    "grid-system 314 name-hex 47 main-along none u repeat 0 100 stagger 40 v repeat 0 100 stagger 30",',
         tests=["tests.test_geo314_commit_paths.Geo314CommitPaths.test_default_fixed_lines_change_alarm_preserves_the_owned_replay_route"]),
    dict(id="M112", desc="I24/#314 ordered：換來源整批豁免會錯放450反例", binary="bridge",
         file="geometry-templates/woodworking/native/grid_application.c",
         old="if(!card_edit&&prior->value!=f->after.value)return false;", new="if(0)return false;", tests=[STAGGER_TABLE]),
    dict(id="M113", desc="I24/#314 ordered：丟掉相鄰事實的來源和值連續性", binary="bridge",
         file="geometry-templates/woodworking/native/grid_application.c",
         old="if(f->order<=order||!wood_grid_stagger_same_point(&state,&f->before))return false;",
         new="if(f->order<=order)return false;", tests=[STAGGER_TABLE]),
    dict(id="M114", desc="I24/#314 ordered：丟掉操作順序不能從final store猜例外", binary="bridge",
         file="geometry-templates/woodworking/native/grid_application.c",
         old="if(f->order<=order||!wood_grid_stagger_same_point(&state,&f->before))return false;",
         new="if(!wood_grid_stagger_same_point(&state,&f->before))return false;", tests=[STAGGER_TABLE]),
    dict(id="M115", desc="I24/#314 ordered：有序事實必須綁定最終來源和值", binary="bridge",
         file="geometry-templates/woodworking/native/grid_application.c",
         old="return found&&wood_grid_stagger_same_point(&state,&final);", new="return found;", tests=[STAGGER_TABLE]),
    dict(id="M116", desc="I24/#314 ordered：只留最終store丟失原操作事實，500正例應轉紅", binary="bridge",
         file="geometry-web/engineering_bridge.inc",
         old="if(ok&&!app_stagger_record_step(candidate,&stagger_before))ok=eng_fail(\"UNSUPPORTED/CAPACITY: ordered stagger evidence memory\");",
         new="if(false)ok=eng_fail(\"UNSUPPORTED/CAPACITY: ordered stagger evidence memory\");",
         tests=[STAGGER_TEST + "test_Q3_parameter_then_same_value_unbind_survives_preview_and_confirmation"]),
    dict(id="M117", desc="I24/#314 ordered：confirm重驗丟掉retainedfacts，500正例應轉紅", binary="bridge",
         file="current_geometry.c",
         old="g_boundary_keyed_update=candidate->operation.boundary_keyed;g_boundary_keyed_id=candidate->operation.boundary_id;",
         new="g_boundary_keyed_update=candidate->operation.boundary_keyed;g_boundary_keyed_id=candidate->operation.boundary_id;app_world_candidate_clear_stagger(candidate);",
         tests=[STAGGER_TEST + "test_Q3_parameter_then_same_value_unbind_survives_preview_and_confirmation"]),
    dict(id="M118", desc="I24/#314 ordered：當下來源值誤讀axis快取，先改卡再保值解除的正例應轉紅", binary="bridge",
         file="geometry-app/native/stagger_facts.inc",
         old="geo_parameter_evaluation_field(evaluation,point->source,&value)",
         new="(value=(GeoQuantity){definition->stagger,1,1},true)",
         tests=[STAGGER_TEST + "test_Q3_parameter_then_same_value_unbind_survives_preview_and_confirmation"]),
    dict(id="M119", desc="I24/#314 ordered：移除facts內容封存檢查，正常tamper ASSERT必轉紅", binary="bridge",
         file="geometry-app/native/world_candidate.inc",
         old="return !strcmp(hash,candidate->operation.stagger_seal);", new="return true;",
         tests=["tests.test_geo314_ordered_facts.OrderedStaggerFacts.test_fact_bytes_order_count_revision_and_provider_tampering_are_rejected"]),
    dict(id="M120", desc="I24/#314 ordered：失敗preview未清除候選有序證據，正常ownership ASSERT必轉紅", binary="bridge",
         file="geometry-web/engineering_bridge.inc",
         old="if(!ok)app_world_candidate_clear_stagger(transaction);", new="if(0)app_world_candidate_clear_stagger(transaction);",
         tests=["tests.test_geo314_ordered_facts.OrderedStaggerFacts.test_failed_preview_clears_evidence_and_keeps_definition_and_revision"]),
    dict(id="M121", desc="I24/#314 ordered：final同參數引用不能遮掉非保值換來源", binary="bridge",
         file="geometry-templates/woodworking/native/grid_application.c",
         old="if(facts[i].system_id==system_id&&facts[i].axis==axis)return true;",
         new="if(0)return true;",
         tests=[STAGGER_TEST + "test_Q3_same_final_reference_preserves_card_then_unbind_and_rebind_order",
                STAGGER_TEST + "test_Q3_same_final_reference_cannot_exempt_value_changing_rebind"]),
]


# #318 Reading A: M122-M139 remain untouched. Native source controls use
# independent numeric W/caller judges; formal 0/1/0 is still pending until run.
MUTANTS += [
    dict(id="M140", desc="I19/R6/#318 閱讀A：partial-admission；撤回須抓到 positive-contact-without-new-minimum", binary="bridge",
         file='geometry-templates/woodworking/native/contact_world.c',
         old='    return WOOD_BOUNDARY_END_PARTIAL;', new='    return WOOD_BOUNDARY_END_ORDINARY;',
         tests=['tests.test_geo318_reading_a_native.ReadingANative.test_fixed_whole_positioning_edge_endpoint_placed_contact_and_roles']),
    dict(id="M141", desc="I19/R6/#318 閱讀A：real-rc-width；撤回須抓到 exact-width-rc-feature-refused", binary="bridge",
         file='geometry-templates/woodworking/native/contact_world.c',
         old='if(hi-lo>=width&&visible_lo<visible_hi&&', new='if(hi-lo>width&&visible_lo<visible_hi&&',
         tests=['tests.test_geo318_reading_a_native.ReadingANative.test_returned_features_real_rc_span_exact_width_and_collinear_faces']),
    dict(id="M142", desc="I19/R6/#318 閱讀A：real-rc-plane；撤回須抓到 collinear-rc-subdivision-joined", binary="bridge",
         file='geometry-templates/woodworking/native/contact_world.c',
         old='if(!contact_same_rc_plane(face,other)||', new='if(true||',
         tests=['tests.test_geo318_reading_a_native.ReadingANative.test_returned_features_real_rc_span_exact_width_and_collinear_faces']),
    dict(id="M143", desc="I19/R6/#318 閱讀A：contact-side；撤回須抓到 wrong-side-feature-not-contact", binary="bridge",
         file='geometry-templates/woodworking/native/contact_world.c',
         old='face->edge_index!=(end==0?1:0)', new='false',
         tests=['tests.test_geo318_reading_a_native.ReadingANative.test_returned_features_real_rc_span_exact_width_and_collinear_faces']),
    dict(id="M144", desc="I19/R6/#318 閱讀A：collector-partial；撤回須抓到 collector-partial-without-fullwidth", binary="bridge",
         file='geometry-templates/woodworking/native/contact_world.c',
         old='if(admission==WOOD_BOUNDARY_END_PARTIAL)return true;', new='if(false)return true;',
         tests=['tests.test_geo318_reading_a_native.ReadingANative.test_actual_span_between_named_source_bare_rc_and_source_failure']),
    dict(id="M145", desc="I19/R6/#318 閱讀A：span-partial；撤回須抓到 span-accepts-partial-end", binary="bridge",
         file='geometry-templates/woodworking/native/member_reference.c',
         old='if(admission==WOOD_BOUNDARY_END_PARTIAL)goto supported_end;', new='if(false)goto supported_end;',
         tests=['tests.test_geo318_reading_a_native.ReadingANative.test_actual_span_between_named_source_bare_rc_and_source_failure']),
    dict(id="M146", desc="I19/R6/#318 閱讀A：between-required-source；撤回須抓到 between-required-face-must-itself-contact", binary="bridge",
         file='geometry-templates/woodworking/native/member_reference.c',
         old='s,e,face->fixed==s?0:1,face,&admission)', new='s,e,face->fixed==s?0:1,NULL,&admission)',
         tests=['tests.test_geo318_reading_a_native.ReadingANative.test_actual_span_between_named_source_bare_rc_and_source_failure']),
    dict(id="M147", desc="I19/R6/#318 閱讀A：revalidate-partial；撤回須抓到 r6e-accepts-partial-without-fullwidth-recheck", binary="bridge",
         file='geometry-templates/woodworking/native/world_validation.c',
         old='if(admission==WOOD_BOUNDARY_END_PARTIAL)continue;', new='if(false)continue;',
         tests=['tests.test_geo318_reading_a_native.ReadingANative.test_r6e_partial_single_full_rc_source_failure_and_collision']),
    dict(id="M148", desc="I19/R6/#318 閱讀A：revalidate-still-collides；撤回須抓到 partial-does-not-skip-world-collision", binary="bridge",
         file='geometry-templates/woodworking/native/world_validation.c',
         old='if(admission==WOOD_BOUNDARY_END_PARTIAL)continue;', new='if(admission==WOOD_BOUNDARY_END_PARTIAL)return true;',
         tests=['tests.test_geo318_reading_a_native.ReadingANative.test_r6e_partial_single_full_rc_source_failure_and_collision']),
]

# H collector wiring is distinct from the W typed-fact controls above. This
# witness evaluates an explicit already-placed World, not CLI reachability.
MUTANTS += [
    dict(id="M149", desc="R6(e)/#318：真H collector重套舊全寬規則，部分接觸見證須正常拒絕斷言轉紅", binary="bridge",
         file="geometry-core/references.inc",
         old="if(!wood_contact_end_support_check(admission,hits,a->has_between,detail,sizeof detail))",
         new="if(!hits || (!a->has_between && hits!=1))",
         tests=["tests.test_geo318_reading_a_native.ReadingANative.test_actual_host_collector_partial_and_i11_wiring_on_explicit_world"]),
]

MUTANTS += [
    dict(id="M150", desc="I19/#318：裸RC拒絕不用既有V_CUT_PRIORITY碼會誤歸I20，具名I19診斷斷言須轉紅", binary="bridge",
         file="geometry-templates/woodworking/native/member_reference.c",
         old='"V_CUT_PRIORITY：固定段終點有裸露',
         new='"V_BOUNDARY_END_RC：固定段終點有裸露',
         tests=["tests.test_geo318_reading_a_native.ReadingANative.test_actual_span_between_named_source_bare_rc_and_source_failure"]),
]


def run_cmd(cmd, cwd, timeout=120):
    return subprocess.run(cmd, cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)


KILLED_BY_MAX = 5


def classify_test_run(proc):
    """Only a complete, structured assertion run can kill a mutation.

    Tracebacks, shell errors and incomplete runs never become 'killed' merely
    because their process exit code is nonzero.  Returns (verdict, why); use
    failed_scenes(proc) for the fixtures that made the run fail.
    """
    rows = [line.removeprefix("GEOMETRY_TEST_RESULT ") for line in proc.stdout.splitlines()
            if line.startswith("GEOMETRY_TEST_RESULT ")]
    if len(rows) != 1:
        return "blocked", "runner did not emit exactly one complete structured result"
    try:
        result = json.loads(rows[0])
        cases = result["cases"]
        if result["schema"] != "geometry-native-tests/1" or result["total"] != len(TESTS):
            raise ValueError("runner schema/count mismatch")
        if [case["scene"] for case in cases] != [spec["scene"] for spec in TESTS]:
            raise ValueError("missing, duplicate or reordered test cases")
        counts = {key: sum(case["status"] == key for case in cases) for key in ("pass", "fail", "infrastructure")}
        if sum(counts.values()) != len(TESTS) or counts != result["counts"]:
            raise ValueError("invalid case status/counts")
        if counts["infrastructure"]:
            return "blocked", next(case["detail"] for case in cases if case["status"] == "infrastructure")
        expected_exit = 1 if counts["fail"] else 0
        if proc.returncode != expected_exit:
            raise ValueError("exit code contradicts assertion result")
        if counts["fail"]:
            return "killed", next(case["scene"] + ": " + case["detail"] for case in cases if case["status"] == "fail")
        return "survived", f"all {len(TESTS)} declared assertions passed"
    except (ValueError, TypeError, KeyError) as exc:
        return "blocked", "invalid runner result: " + str(exc)


def failed_scenes(proc, limit=KILLED_BY_MAX):
    """classify_test_run 判 killed 時,失敗的夾具名(依 TESTS 順序,最多 limit 個)。"""
    rows = [line.removeprefix("GEOMETRY_TEST_RESULT ") for line in proc.stdout.splitlines()
            if line.startswith("GEOMETRY_TEST_RESULT ")]
    try:
        return [case["scene"] for case in json.loads(rows[0])["cases"] if case["status"] == "fail"][:limit]
    except (IndexError, ValueError, TypeError, KeyError):
        return []


# Python 在 POSIX 以負信號碼回報 SIGSEGV。Windows 的 STATUS_ACCESS_VIOLATION
# 是 0xC0000005;GetExitCodeProcess 給無號 3221225477,有的包裝會收成有號。
_AV_DETAIL = re.compile(r"^INFRA abnormal executable exit (-?\d+):")


def is_access_violation_code(code):
    """程序結束碼是不是存取違規(POSIX -11,或 Windows 0xC0000005 的有號/無號形式)。

    核心 exe 與 bridge 兩條路徑共用這一個判定;其他結束碼(含 1、-9、abort)都不是。"""
    if type(code) is not int:
        return False
    if code == -11:
        return True
    return (code & 0xFFFFFFFF) == 0xC0000005


def is_access_violation_detail(detail):
    match = _AV_DETAIL.match(detail or "")
    return bool(match) and is_access_violation_code(int(match.group(1)))


def access_violation_scenes(proc):
    """完整結果裡唯一的問題是存取違規時,回傳夾具名(TESTS 順序);否則 None。

    斷言失敗、逾時、缺檔、其他異常結束碼、結果不完整,都不是這個型態。
    單次存取違規仍由 classify_test_run 記成 blocked;要連續同一組夾具才升級。
    """
    rows = [line.removeprefix("GEOMETRY_TEST_RESULT ") for line in proc.stdout.splitlines()
            if line.startswith("GEOMETRY_TEST_RESULT ")]
    if len(rows) != 1 or getattr(proc, "returncode", None) != 2:
        return None
    try:
        result = json.loads(rows[0])
        cases = result["cases"]
        if result["schema"] != "geometry-native-tests/1" or result["total"] != len(TESTS):
            return None
        if [case["scene"] for case in cases] != [spec["scene"] for spec in TESTS]:
            return None
        counts = {key: sum(case["status"] == key for case in cases)
                  for key in ("pass", "fail", "infrastructure")}
        if sum(counts.values()) != len(TESTS) or counts != result["counts"]:
            return None
        if counts["fail"] or not counts["infrastructure"]:
            return None
        scenes = []
        for case in cases:
            if case["status"] != "infrastructure":
                continue
            if not is_access_violation_detail(case.get("detail")):
                return None
            scenes.append(case["scene"])
        return tuple(scenes)
    except (ValueError, TypeError, KeyError):
        return None


def verdict_from_attempts(attempts):
    """attempts: (outcome, why, crash_scenes 或 None, killers)。

    最後一次已是 killed / survived 就採用它。否則只有跑滿 RUN_RETRIES、
    每次都是同一組非空的存取違規夾具,才記 crashed。其餘維持 blocked。
    """
    if not attempts:
        return "blocked", "沒有任何一次執行結果", [], []
    outcome, why, _scenes, killers = attempts[-1]
    if outcome in ("killed", "survived"):
        return outcome, why, list(killers), []
    signatures = [item[2] for item in attempts]
    if (len(attempts) == RUN_RETRIES and signatures[0]
            and all(sig == signatures[0] for sig in signatures)):
        names = list(signatures[0])
        shown = ", ".join(names[:KILLED_BY_MAX])
        return (
            "crashed",
            f"基準線已通過；連跑 {RUN_RETRIES} 次都在同一夾具以存取違規結束"
            f"（{shown}；{why}）。算被偵測到，但不是斷言殺死。",
            [],
            names,
        )
    blocked_why = f"連跑 {RUN_RETRIES} 次都是環境失敗,結果不可信 <- {why}"
    if "abnormal executable exit" in why:
        blocked_why += "(有異常結束碼，但不是連續相同夾具上的存取違規；仍算環境阻擋，不算 killed)"
    elif "4551" in why or "啟動失敗" in why:
        blocked_why += "(啟動失敗或 Smart App Control，不是變異崩潰)"
    return "blocked", blocked_why, [], []


# ============================================================
# 來源模型與 provenance
# ============================================================
INCLUDE_RE = re.compile(r'^[ \t]*#[ \t]*include[ \t]+"([^"]+)"', re.M)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Sources:
    """Core 與 bridge 的 #include "…" 聯集閉包(LF 正規化後的文字與雜湊)。

    這份 CRLF 原始碼只能用二進位模式讀;雜湊算在 CRLF->LF 之後,與舊 provenance 相容。
    """

    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()
        self.texts = {}
        self.hashes = {}
        self._visit(self.root / MAIN_REL)
        bridge = self.root / "geometry-web/web_bridge.c"
        if bridge.is_file():
            self._visit(bridge)
        self.closure = _sha("\n".join(f"{r} {self.hashes[r]}" for r in sorted(self.hashes)).encode("utf-8"))

    def _visit(self, path):
        path = path.resolve()
        try:
            rel = path.relative_to(self.root).as_posix()
        except ValueError:
            return
        if rel in self.texts:
            return
        data = path.read_bytes().replace(b"\r\n", b"\n")
        self.texts[rel] = data.decode("utf-8")
        self.hashes[rel] = _sha(data)
        for name in INCLUDE_RE.findall(self.texts[rel]):
            target = path.parent / name
            if target.is_file():
                self._visit(target)


def oracle_hash(runner_path=None, scene_root=None, tests=None):
    """裁判的雜湊:run_tests.py 內容 + 依檔名排序、被 TESTS 引用的每個 .scene 內容(CRLF->LF)。

    夾具被改壞(例如 M24 的舊殺手在 GEO-125 被改成別的用途)或判定邏輯改了,
    舊的 killed / survived 就不再是同一個裁判下的判決。缺檔以固定標記入雜湊
    (run_tests 自己會把缺檔記成 INFRA,這裡只需要讓雜湊跟著變)。
    """
    runner_path = pathlib.Path(runner_path or HERE / "run_tests.py")
    scene_root = pathlib.Path(scene_root or ROOT)
    names = sorted({spec["scene"] for spec in (TESTS if tests is None else tests)})
    lines = []
    for name in names:
        f = scene_root / name
        lines.append(f"{name} " + (_sha(f.read_bytes().replace(b"\r\n", b"\n")) if f.is_file() else "MISSING"))
    body = _sha(runner_path.read_bytes().replace(b"\r\n", b"\n")) + "\n" + "\n".join(lines)
    return _sha(body.encode("utf-8"))


def compile_hash():
    """編譯指令的雜湊：Windows 用 _cl.bat 內容，Linux 用實際 cc 參數。"""
    if os.name != "nt":
        return _sha(json.dumps(compile_command("<source>", "<output>"), ensure_ascii=False).encode("utf-8"))
    return _sha((HERE / "_cl.bat").read_bytes().replace(b"\r\n", b"\n"))


def compile_command(source, output):
    """Keep native Windows builds and the documented WSL/GCC fallback reproducible."""
    if os.name == "nt":
        return ["cmd", "/c", str(HERE / "_cl.bat"), str(source), str(output)]
    return [os.environ.get("CC", "cc"), "-std=c11", "-O2", str(source), "-o", str(output), "-lm"]


# ============================================================
# exe 指紋快取
# ============================================================
SIDECAR_SUFFIX = ".fingerprint.json"


def _file_sha(path):
    return binaries._binary_identity(pathlib.Path(path))["exe_sha256"]


def sidecar_path(exe):
    exe = pathlib.Path(exe)
    return exe.with_name(exe.name + SIDECAR_SUFFIX)


def mutant_fingerprint(m, src, compile_sha=None):
    """原始來源/變異/編譯指紋之外，實際注入內容也必須相同才能沿用。"""
    return {"mutant_sha256": mutant_key(m), "closure_sha256": src.closure,
            "generated_source_sha256": _sha(build_mutant_source(m, src).encode("utf-8")),
            "compile_sha256": compile_sha or compile_hash()}


def baseline_fingerprint(src, compile_sha=None):
    return {"kind": "baseline", "closure_sha256": src.closure,
            "compile_sha256": compile_sha or compile_hash()}


def cache_state(exe, fp):
    """hit / missing / nosidecar / stale / tampered。只有 hit 可以沿用。"""
    exe = pathlib.Path(exe)
    if not exe.is_file():
        return "missing"
    sc = sidecar_path(exe)
    if not sc.is_file():
        return "nosidecar"
    try:
        data = json.loads(sc.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return "stale"
        if str(data.get("note", "")).startswith("adopted:"):
            return "stale"  # Legacy metadata was inferred from results, not from this build.
        if data.get("fingerprint") != fp:
            return "stale"
        if not isinstance(data.get("exe_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", data["exe_sha256"]):
            return "stale"
        if data.get("exe_sha256") != _file_sha(exe):
            return "tampered"
    except (OSError, ValueError):
        return "stale"
    return "hit"


def write_sidecar(exe, fp, note=""):
    exe = pathlib.Path(exe)
    data = {"fingerprint": fp, "exe_sha256": _file_sha(exe), "note": note,
            "written": datetime.datetime.now().isoformat(timespec="seconds")}
    sc = sidecar_path(exe)
    binaries._write_json_atomic(sc, data)


def prepare_mutant_exe(m, src, mut_dir, compile_fn, rec=None, compile_sha=None):
    """讓 mut_dir/_mut.exe 處於可用狀態。回傳 (status, exe, message)。

    status: cached(沿用)/ built(重編)/ invalid(編譯失敗)/ blocked(來源變更或身分發布失敗)。
    compile_fn(m, exe) -> (ok, message) 只在非 cached 時被呼叫。
    rec 是舊呼叫端的相容參數；結果紀錄不作為採用未驗證 exe 的證據。
    """
    mut_dir = pathlib.Path(mut_dir)
    exe = mut_dir / "_mut.exe"
    try:
        fp = mutant_fingerprint(m, src, compile_sha)
    except ValueError as exc:
        return "invalid", exe, str(exc)
    state = cache_state(exe, fp)
    if state == "hit":
        return "cached", exe, ""
    mut_dir.mkdir(parents=True, exist_ok=True)
    exe.unlink(missing_ok=True)                    # 舊二進位不得冒充這次的編譯結果
    sidecar_path(exe).unlink(missing_ok=True)
    ok, msg = compile_fn(m, exe)
    if not ok or not exe.exists():
        exe.unlink(missing_ok=True)
        return "blocked" if msg.startswith("INFRA ") else "invalid", exe, msg
    try:
        write_sidecar(exe, fp, "built")
    except OSError as exc:
        sidecar_path(exe).unlink(missing_ok=True)
        return "blocked", exe, "cannot publish binary identity: " + str(exc)
    return "built", exe, msg


def prepare_baseline_exe(src, base_dir, compile_fn, compile_sha=None):
    """未變異原始碼的 exe:來源閉包與編譯指令沒變就沿用。回傳 (cached|built|invalid, exe, message)。

    先編到 baseline.<pid>.exe 再換名,兩個 mutate.py 同時跑時不會在同一個檔上互踩。
    """
    base_dir = pathlib.Path(base_dir)
    exe = base_dir / "baseline.exe"
    fp = baseline_fingerprint(src, compile_sha)
    if cache_state(exe, fp) == "hit":
        return "cached", exe, ""
    base_dir.mkdir(parents=True, exist_ok=True)
    tmp = base_dir / f"baseline.{os.getpid()}.exe"
    tmp.unlink(missing_ok=True)
    ok, msg = compile_fn(tmp)
    if not ok or not tmp.exists():
        tmp.unlink(missing_ok=True)
        return "invalid", exe, msg
    sidecar_path(exe).unlink(missing_ok=True)
    os.replace(tmp, exe)
    try:
        write_sidecar(exe, fp, "built")
    except OSError as exc:
        sidecar_path(exe).unlink(missing_ok=True)
        return "blocked", exe, "cannot publish baseline identity: " + str(exc)
    return "built", exe, msg


def sweep_old_baseline_dirs(mut_root, max_age_s=3600):
    """舊版每輪 mkdtemp 一個 baseline-* 目錄,異常中斷會留下;清掉超過一小時的。"""
    now = time.time()
    for d in pathlib.Path(mut_root).glob("baseline-*"):
        try:
            if d.is_dir() and now - d.stat().st_mtime > max_age_s:
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass


def mutant_file(m):
    return m.get("file", MAIN_REL)


def mutant_key(m):
    """變異定義本身的雜湊:改了 file/old/new 就不能沿用舊判決。"""
    parts = [mutant_file(m), m["old"], m["new"]]
    if m.get("binary") == "bridge":
        parts += ["bridge", m["tests"]]
    return _sha(json.dumps(parts, ensure_ascii=False).encode("utf-8"))


def definition_kind(m, src):
    """回傳 (kind, why);kind 為 run / equivalent / retired / invalid。

    不編譯、不跑測試,只看錨點在現行來源的狀況。等價與退役的變異也要過這一關:
    等價變異的錨點不在了,「等價」的說法就沒有對象;退役變異的舊錨點若又出現,
    「邏輯已移除」的依據就失效。
    """
    f = mutant_file(m)
    text = src.texts.get(f)
    if text is None:
        return "invalid", f"目標檔 {f} 不在 core/bridge 的 #include 聯集閉包內"
    if m.get("binary") == "bridge":
        methods = m.get("tests")
        if (not isinstance(methods, list) or not methods
                or any(not isinstance(name, str) or not re.fullmatch(r"tests\.\w+\.\w+\.test_\w+", name) for name in methods)
                or len(set(methods)) != len(methods)):
            return "invalid", "bridge 變異需要互異的具名 unittest 方法"
        # killed 與 crashed 都以「基準線先通過」為前提:基準線只跑 RESTORED,且必須全部通過
        # (mutation_bridge.execution_problems 驗基準線收據)。不在 RESTORED 的方法基準線根本沒跑過。
        import mutation_bridge
        unproven = [name for name in methods if name not in mutation_bridge.RESTORED]
        if unproven:
            return "invalid", ("bridge 變異的測試方法不在基準線 mutation_bridge.RESTORED 內(基準線沒跑過、"
                               "沒證明它先通過,killed/crashed 都不成立):" + ", ".join(unproven))
    n = text.count(m["old"])
    if m.get("retired"):
        if n:
            return "invalid", f"已標 retired,但舊錨點在 {f} 又出現 {n} 次——退役依據失效,請重新判斷"
        return "retired", m["retired"]
    if n != 1:
        return "invalid", f"錨點在 {f} 出現 {n} 次(需要 1)"
    if m.get("equivalent"):
        return "equivalent", m["equivalent"]
    return "run", ""


def _include_relative(src, containing, name):
    """Resolve a quoted include without reading beyond the captured source map."""
    name = name.replace("\\", "/")
    if posixpath.isabs(name) or pathlib.PureWindowsPath(name).drive:
        raise ValueError(f"include escapes repository: {containing} -> {name}")
    path = (src.root / posixpath.dirname(containing) / name).resolve()
    try:
        return path.relative_to(src.root).as_posix()
    except ValueError as exc:
        raise ValueError(f"include escapes repository: {containing} -> {name}") from exc


def build_mutant_source(m, src):
    """Expand only the unique main-to-target include chain; mutate exactly once.

    Quoted includes in emitted files are rebased to the repository root. Other
    files stay includes, with their original internal include resolution intact.
    Source text/hash maps remain the original, unmodified closure snapshot.
    """
    kind, why = definition_kind(m, src)
    if kind not in ("run", "equivalent"):
        raise ValueError(why or "mutation target is not active")
    target = mutant_file(m)
    edges = {}
    parents = {}
    for rel, text in src.texts.items():
        edges[rel] = []
        for name in INCLUDE_RE.findall(text):
            child = _include_relative(src, rel, name)
            # External-build header aliases may not resolve beside an unexpanded
            # file. They are not include edges in this captured unity closure.
            if child in src.texts:
                edges[rel].append(child)
                parents.setdefault(child, set()).add(rel)
    ancestors = {target}
    pending = [target]
    while pending:
        for parent in parents.get(pending.pop(), ()):
            if parent not in ancestors:
                ancestors.add(parent)
                pending.append(parent)
    paths = []

    def find_path(rel, trail):
        if rel in trail:
            raise ValueError("include cycle on mutation path: " + " -> ".join((*trail, rel)))
        trail = (*trail, rel)
        if rel == target:
            paths.append(trail)
            if len(paths) > 1:
                raise ValueError(f"mutation target {target} included more than once")
        for child in edges.get(rel, ()):
            if child in ancestors:
                find_path(child, trail)

    find_path(MAIN_REL, ())
    if len(paths) != 1:
        raise ValueError(f"mutation target {target} is not reachable from {MAIN_REL}")
    path = paths[0]

    def emit(index):
        rel = path[index]
        text = src.texts[rel]
        if rel == target:
            text = text.replace(m["old"], m["new"], 1)

        def include(match):
            child = _include_relative(src, rel, match.group(1))
            if child not in src.texts:
                raise ValueError(f"include missing from source closure: {rel} -> {child}")
            if index + 1 < len(path) and child == path[index + 1]:
                body = emit(index + 1)
                return body if body.endswith("\n") else body + "\n"
            # Preserve indentation, spelling and trailing comments; replace only
            # the path bytes, and never rebase text already emitted by a child.
            start, end = match.start(1) - match.start(), match.end(1) - match.start()
            return match.group(0)[:start] + child + match.group(0)[end:]

        return INCLUDE_RE.sub(include, text)

    return emit(0)


def record_hash(rec):
    """Integrity of the saved result; transient stale annotations preserve its original verdict.

    This detects accidental edits, not an attacker who can rewrite the checksum.
    """
    body = {k: v for k, v in rec.items() if k not in ("record_sha256", "stale_from", "stale_why")}
    if body.get("verdict") == "stale" and rec.get("stale_from"):
        body["verdict"] = rec["stale_from"]
    return _sha(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode())


def attempt_receipt(proc, root):
    """Keep the exact structured oracle outcome and raw output hashes without publishing cloud paths."""
    rows = [s.removeprefix("GEOMETRY_TEST_RESULT ") for s in proc.stdout.splitlines()
            if s.startswith("GEOMETRY_TEST_RESULT ")]
    result = None
    if len(rows) == 1:
        try:
            result = json.loads(rows[0].replace(str(pathlib.Path(root).resolve()), "<repo>"))
        except ValueError:
            pass
    return {"exit_code": proc.returncode, "result": result,
            "stdout_sha256": _sha(proc.stdout.encode()), "stderr_sha256": _sha(proc.stderr.encode())}


def receipt_process(receipt):
    return types.SimpleNamespace(returncode=receipt["exit_code"], stderr="",
                                 stdout="GEOMETRY_TEST_RESULT " + json.dumps(receipt["result"]))


def execution_problems(m, rec, verdict, src):
    if m.get("binary") == "bridge":
        import mutation_bridge
        return mutation_bridge.execution_problems(sys.modules[__name__], m, rec, verdict, src)
    evidence = rec.get("execution")
    if not isinstance(evidence, dict):
        return ["missing execution receipt (binary/command/exit/oracle)"]
    try:
        if evidence["schema"] != "geometry-mutation-execution/1":
            raise ValueError("execution schema")
        for key in ("exe_sha256", "baseline_exe_sha256", "compile_sha256", "tool_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", evidence[key]):
                raise ValueError(key)
        if evidence["tool_sha256"] != tool_hash():
            raise ValueError("mutation tool changed")
        if not re.fullmatch(r"[0-9a-f]{40}", evidence["head"]):
            raise ValueError("execution head")
        if evidence["compile_command"] != portable_compile_command():
            # Commands are portable receipts. Other OS/compiler runs stay explicit, not recertified locally.
            if evidence["platform"] == os.name:
                raise ValueError("compile command changed")
        if evidence["platform"] == os.name and evidence["compile_sha256"] != compile_hash():
            raise ValueError("compile fingerprint changed")
        if evidence["test_command"] != ["<python>", "tests/run_tests.py", "<binary>"]:
            raise ValueError("oracle command")
        if evidence["compile_exit_code"] != 0:
            raise ValueError("binary compilation did not succeed")
        if classify_test_run(receipt_process(evidence["baseline"]))[0] != "survived":
            raise ValueError("baseline did not pass all declared assertions")
        attempts = []
        for item in evidence["attempts"]:
            for key in ("stdout_sha256", "stderr_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", item[key]):
                    raise ValueError(key)
            proc = receipt_process(item)
            outcome, why = classify_test_run(proc)
            attempts.append((outcome, why, access_violation_scenes(proc), failed_scenes(proc)))
        actual, _, killers, crashes = verdict_from_attempts(attempts)
        if actual != ("survived" if verdict == "equivalent" else verdict):
            raise ValueError("saved verdict contradicts complete execution results")
        if verdict == "killed" and rec.get("killed_by") != killers:
            raise ValueError("killed_by contradicts assertion failures")
        if verdict == "crashed" and rec.get("crashed_on") != crashes:
            raise ValueError("crashed_on contradicts repeated access violations")
        # Results remain usable on a clean checkout: executables are TEMP artifacts, not committed.
        # If this platform's artifact exists, it must still be precisely the recorded executable.
        if evidence["platform"] == os.name:
            exe = MUT_ROOT / m["id"] / "_mut.exe"
            if exe.exists() and (cache_state(exe, mutant_fingerprint(m, src)) != "hit"
                                 or _file_sha(exe) != evidence["exe_sha256"]):
                raise ValueError("cached binary differs from executed receipt")
            baseline = MUT_ROOT / "_baseline" / "baseline.exe"
            if baseline.exists() and (cache_state(baseline, baseline_fingerprint(src)) != "hit"
                                      or _file_sha(baseline) != evidence["baseline_exe_sha256"]):
                raise ValueError("cached baseline differs from executed receipt")
    except (KeyError, TypeError, ValueError, OSError) as exc:
        return ["execution receipt invalid: " + str(exc)]
    return []


def tool_hash():
    body = (HERE / "mutate.py").read_bytes().replace(b"\r\n", b"\n")
    backend = HERE / "mutation_bridge.py"
    if backend.is_file():
        body += b"\0mutation_bridge.py\0" + backend.read_bytes().replace(b"\r\n", b"\n")
    return _sha(body)


def portable_compile_command():
    return [s.replace(str(ROOT), "<repo>") for s in compile_command("<source>", "<output>")]


def make_record(m, src, verdict, why, today, oracle_sha, killed_by=None, crashed_on=None, execution=None):
    rec = {"desc": m["desc"], "verdict": verdict, "why": why}
    if verdict == "killed" and killed_by:
        rec["killed_by"] = list(killed_by)
    if verdict == "crashed" and crashed_on:
        rec["crashed_on"] = list(crashed_on)
    if verdict == "invalid" and m.get("equivalent"):
        rec["equivalent_why"] = m["equivalent"]
    f = mutant_file(m)
    rec["date"] = today
    rec["source_file"] = f
    if verdict != "retired":
        rec["source_sha256"] = src.hashes.get(f)
        rec["closure_sha256"] = src.closure
        rec["oracle_sha256"] = oracle_sha
    rec["mutant_sha256"] = mutant_key(m)
    if execution is not None:
        rec["execution"] = execution
    rec["record_sha256"] = record_hash(rec)
    return rec


def effective_record(m, rec, src, today, oracle_sha, require_execution=False):
    """把一筆既有紀錄對照現行來源與變異定義,必要時標 stale。"""
    if m.get("binary") == "bridge":
        import mutation_bridge
        oracle_sha = mutation_bridge.oracle_hash(m, src.root)
    kind, why = definition_kind(m, src)
    if kind == "invalid":
        # 錨點現在就壞了:不論舊判決是什麼,都以 invalid 覆蓋。
        return make_record(m, src, "invalid", why, today, oracle_sha)
    verdict = rec.get("verdict")
    base = rec.get("stale_from") if verdict == "stale" else verdict
    if base not in ("killed", "survived", "crashed", "equivalent", "retired"):
        return rec                       # invalid / blocked / 不認得的值:不因雜湊翻案
    want = ("killed", "survived", "crashed") if kind == "run" else (kind,)
    problems = []
    if rec.get("record_sha256") != record_hash(rec):
        problems.append("result checksum missing or changed")
    if rec.get("desc") != m["desc"] or (kind in ("equivalent", "retired") and rec.get("why") != m[kind]):
        problems.append("definition description/proof changed")
    if base not in want:
        problems.append(f"變異表現在把它定為 {kind},紀錄卻是 {base}")
    if rec.get("mutant_sha256") != mutant_key(m):
        problems.append("變異定義(file/old/new)與紀錄不符或紀錄沒有 mutant_sha256")
    if base != "retired":
        f = mutant_file(m)
        if not rec.get("source_sha256"):
            problems.append("沒有來源雜湊(provenance)")
        elif rec["source_sha256"] != src.hashes.get(f):
            problems.append(f"{f} 已變(紀錄 {rec['source_sha256'][:10]} / 現行 {str(src.hashes.get(f))[:10]})")
        if not rec.get("closure_sha256"):
            problems.append("沒有 include 閉包雜湊")
        elif rec["closure_sha256"] != src.closure:
            problems.append("#include 閉包內有檔案已變")
        if base in ("killed", "survived", "crashed"):
            # 判決是「跑裁判」得來的:裁判(run_tests.py 或它引用的夾具)變了就不能沿用。
            if not rec.get("oracle_sha256"):
                problems.append("沒有裁判雜湊(oracle_sha256)")
            elif rec["oracle_sha256"] != oracle_sha:
                problems.append("裁判已變(run_tests.py 或被 TESTS 引用的夾具內容不同)")
        if require_execution:
            if base == "equivalent" and rec.get("oracle_sha256") != oracle_sha:
                problems.append("equivalence audit oracle changed")
            problems.extend(execution_problems(m, rec, base, src))
    if problems:
        out = dict(rec)
        out.update(verdict="stale", stale_from=base, stale_why=";".join(problems))
        return out
    if verdict == "stale":               # 來源還原了:復原成原判決
        out = dict(rec)
        out["verdict"] = base
        out.pop("stale_from", None)
        out.pop("stale_why", None)
        return out
    return rec


def evaluate_table(mutants, records, src, today, oracle_sha, require_execution=False):
    """每個 id 的有效紀錄;沒有紀錄的 id 是 None(unrun);不在變異表的紀錄一律 stale。"""
    table = {}
    known = set()
    for m in mutants:
        known.add(m["id"])
        rec = records.get(m["id"])
        table[m["id"]] = effective_record(m, rec, src, today, oracle_sha, require_execution) if isinstance(rec, dict) else None
    for rid, rec in records.items():
        if rid in known or not isinstance(rec, dict):
            continue
        out = dict(rec)
        out.update(verdict="stale", stale_from=rec.get("stale_from") or rec.get("verdict"),
                   stale_why="這個 id 已不在變異表")
        table[rid] = out
    return table


def tally(table, ids=None):
    counts = {v: 0 for v in VERDICTS}
    counts["unrun"] = 0
    for rid, rec in table.items():
        if ids is not None and rid not in ids:
            continue
        if rec is None:
            counts["unrun"] += 1
        else:
            counts[rec["verdict"] if rec.get("verdict") in VERDICTS else "invalid"] += 1
    return counts


def exit_code(counts, strict):
    """blocked -> 2(結果不完整,先於其他);survived / invalid / stale -> 1;
    strict(完整跑、--check)時沒跑到的 id(unrun)也算不及格。
    crashed 與 killed 一樣算被偵測到,不改變結束碼。"""
    if counts["blocked"]:
        return 2
    bad = counts["survived"] + counts["invalid"] + counts["stale"] + (counts["unrun"] if strict else 0)
    return 1 if bad else 0


def format_counts(counts):
    text = " / ".join(f"{name} {counts[key]}" for name, key in (
        ("殺死 killed", "killed"), ("崩潰 crashed", "crashed"),
        ("存活 survived", "survived"), ("等價 equivalent", "equivalent"),
        ("無效 invalid", "invalid"), ("過期 stale", "stale"), ("受阻 blocked", "blocked"),
        ("退役 retired", "retired")))
    return text + (f" / 未跑 unrun {counts['unrun']}" if counts["unrun"] else "")


def load_records(path):
    path = pathlib.Path(path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("top level is not an object")
        return data
    except (OSError, ValueError) as exc:
        print(f"⚠ 結果檔讀不了({exc}),視為空白:{path}")
        return {}


def save_records(path, records):
    path = pathlib.Path(path)
    binaries._write_json_atomic(path, dict(sorted(records.items())))


def print_stale(table, ids=None):
    for rid, rec in table.items():
        if rec is not None and rec.get("verdict") == "stale" and (ids is None or rid in ids):
            print(f"  STALE {rid}(原 {rec.get('stale_from')}):{rec.get('stale_why')}")


# ============================================================
# 主流程
# ============================================================
def _run_core_pass(mutants, only, root=ROOT, results_path=RESULTS, today=None, oracle=None, audit_equivalents=True):
    today = today or datetime.date.today().isoformat()
    root = pathlib.Path(root)
    src = Sources(root)
    oracle_sha = oracle or oracle_hash()
    selected = [m for m in mutants if not only or m["id"] in only]
    print("Mutation scope: " + ("partial " if only else "full ") + ", ".join(m["id"] for m in selected))

    results = {}
    runnable = []
    for m in selected:
        kind, why = definition_kind(m, src)
        if kind == "run" or (kind == "equivalent" and audit_equivalents):
            runnable.append(m)
            continue
        results[m["id"]] = make_record(m, src, kind, why, today, oracle_sha)
        label = {"equivalent": "EQUIVALENT", "retired": "RETIRED", "invalid": "INVALID"}[kind]
        print(f"{m['id']}  {label:<10} {m['desc']}" + (f"  <- {why}" if kind == "invalid" else ""))

    existing = load_records(results_path)

    def persist(final):
        merged = dict(existing)
        merged.update(results)
        if final:
            merged = {rid: rec for rid, rec in
                      evaluate_table(mutants, merged, src, today, oracle_sha,
                                     require_execution=audit_equivalents).items() if rec is not None}
        save_records(results_path, merged)
        return merged

    compile_sha = compile_hash()
    execution_tool_sha = tool_hash()
    head_proc = run_cmd(["git", "rev-parse", "HEAD"], cwd=root)
    execution_head = head_proc.stdout.strip() if head_proc.returncode == 0 else ""
    baseline_receipt = None
    baseline_hash = None

    def inputs_unchanged(exe, fp, exe_hash):
        return (tool_hash() == execution_tool_sha and compile_hash() == compile_sha
                and Sources(root).closure == src.closure and (oracle or oracle_hash()) == oracle_sha
                and cache_state(exe, fp) == "hit" and _file_sha(exe) == exe_hash)

    def compile_baseline(exe):
        """編未變異的原始碼到 exe(參數分開傳:_cl.bat 用 %~1 %~2 剝引號)。"""
        try:
            build = run_cmd(compile_command(root / MAIN_REL, exe),
                            cwd=exe.parent, timeout=300)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, str(exc)
        if build.returncode != 0 or not exe.exists():
            return False, "unmodified source could not be compiled"
        if Sources(root).closure != src.closure:
            return False, "INFRA source changed during baseline compilation"
        return True, ""

    def compile_mutant(m, exe):
        # .c 必須跟 current_geometry.c 同目錄:它的 #include "geometry-core/…" 是相對於
        # 被包含檔所在目錄解析的。每個變異用自己的檔名,平行跑不互撞;允許清單制的
        # .gitignore 會忽略它,而且編完就刪。exe 才放 %TEMP%(SAC 在意的是 exe 的位置)。
        mut_src = root / f"_mutant_{m['id']}.c"
        try:
            mut_src.write_text(build_mutant_source(m, src), encoding="utf-8", newline="\n")
        except ValueError as exc:
            return False, str(exc)
        try:
            build = run_cmd(compile_command(mut_src, exe),
                            cwd=exe.parent, timeout=300)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, "INFRA compiler launch/timeout: " + str(exc)
        finally:
            mut_src.unlink(missing_ok=True)      # 成敗都清掉,不在 repo 留暫存
        if not exe.exists() or build.returncode != 0:
            return False, "編譯失敗: " + (build.stderr or build.stdout)[-200:]
        if Sources(root).closure != src.closure:
            return False, "INFRA source changed during mutant compilation"
        return True, ""

    if runnable:
        MUT_ROOT.mkdir(parents=True, exist_ok=True)
        sweep_old_baseline_dirs(MUT_ROOT)
        try:
            b_status, baseline_exe, b_msg = prepare_baseline_exe(
                src, MUT_ROOT / "_baseline", compile_baseline, compile_sha)
            if b_status in ("invalid", "blocked"):
                print("BASELINE BLOCKED: " + b_msg)
                return 2
            print("BASELINE exe " + {"cached": "沿用快取(來源與編譯指令沒變)", "built": "已重編"}[b_status])
            baseline_hash = _file_sha(baseline_exe)
            baseline_verdict, baseline_reason = "blocked", "not executed"
            for attempt in range(RUN_RETRIES):
                if not inputs_unchanged(baseline_exe, baseline_fingerprint(src, compile_sha), baseline_hash):
                    print("BASELINE BLOCKED: source/oracle/binary changed before launch")
                    return 2
                result = run_cmd([sys.executable, str(HERE / "run_tests.py"), str(baseline_exe)],
                                 cwd=root, timeout=600)
                if not inputs_unchanged(baseline_exe, baseline_fingerprint(src, compile_sha), baseline_hash):
                    print("BASELINE BLOCKED: source/oracle/binary changed during oracle run")
                    return 2
                baseline_verdict, baseline_reason = classify_test_run(result)
                baseline_receipt = attempt_receipt(result, root)
                if baseline_verdict != "blocked":
                    break
                if attempt + 1 < RUN_RETRIES:
                    time.sleep(12)
            if baseline_verdict != "survived":
                print("BASELINE BLOCKED: unmodified source must pass first: " + baseline_reason)
                return 2
            print(f"BASELINE OK: {len(TESTS)}/{len(TESTS)} 全過(未變異原始碼)")
        except (OSError, subprocess.TimeoutExpired) as exc:
            print("BASELINE BLOCKED: " + str(exc))
            return 2

    for m in runnable:
        status, MUT_EXE, msg = prepare_mutant_exe(
            m, src, MUT_ROOT / m["id"], compile_mutant, existing.get(m["id"]), compile_sha)
        if status in ("invalid", "blocked"):
            results[m["id"]] = make_record(m, src, status, msg, today, oracle_sha)
            print(f"{m['id']}  {status.upper()}  {msg}")
            persist(False)
            continue
        print(f"{m['id']}  exe " + {"cached": "沿用快取",
                                   "built": "已重編"}[status])

        # 啟動失敗、逾時、WinError 4551 重跑後仍是 blocked,絕不計入 killed。
        # 基準線已通過時,同一夾具連續存取違規則是 crashed:算被偵測到,但與斷言分開。
        # 存取違規不等 SAC,不必空等 12 秒;其他受阻仍等,讓新 exe 有機會被放行。
        attempts = []
        receipts = []
        executed_hash = _file_sha(MUT_EXE)
        for attempt in range(1, RUN_RETRIES + 1):
            try:
                if not inputs_unchanged(MUT_EXE, mutant_fingerprint(m, src, compile_sha), executed_hash):
                    attempts.append(("blocked", "source/oracle/binary changed before launch", None, []))
                    break
                test = run_cmd([sys.executable, str(HERE / "run_tests.py"),
                                str(MUT_EXE)], cwd=root, timeout=600)
                receipts.append(attempt_receipt(test, root))
                if not inputs_unchanged(MUT_EXE, mutant_fingerprint(m, src, compile_sha), executed_hash):
                    attempts.append(("blocked", "source/oracle/binary changed during oracle run", None, []))
                    break
            except (OSError, subprocess.TimeoutExpired) as exc:
                attempts.append(("blocked", f"啟動失敗: {exc}", None, []))
                if attempt < RUN_RETRIES:
                    time.sleep(12)
                continue

            outcome, why = classify_test_run(test)
            scenes = access_violation_scenes(test)
            killers = failed_scenes(test) if outcome == "killed" else []
            attempts.append((outcome, why, scenes, killers))
            if outcome in ("killed", "survived"):
                break
            if attempt < RUN_RETRIES and scenes is None:
                time.sleep(12)

        verdict, why, killers, crashed_on = verdict_from_attempts(attempts)
        if m.get("equivalent") and verdict == "survived":
            verdict, why = "equivalent", m["equivalent"]
        elif m.get("equivalent") and verdict != "blocked":
            verdict, why = "invalid", "current execution contradicts equivalence proof: " + why
        why = why.replace(str(root.resolve()), "<repo>")
        execution = {"schema": "geometry-mutation-execution/1", "head": execution_head,
                     "platform": os.name, "tool_sha256": execution_tool_sha,
                     "compile_exit_code": 0,
                     "compile_sha256": compile_sha, "compile_command": portable_compile_command(),
                     "test_command": ["<python>", "tests/run_tests.py", "<binary>"],
                     "exe_sha256": executed_hash, "baseline_exe_sha256": baseline_hash,
                     "baseline": baseline_receipt, "attempts": receipts}
        results[m["id"]] = make_record(
            m, src, verdict, why, today, oracle_sha, killed_by=killers, crashed_on=crashed_on,
            execution=execution)
        print(f"{m['id']}  {verdict.upper():<9} {m['desc']}"
              + (f"  <- {why}" if why else ""))
        persist(False)

    # 跑子集時把結果「併回」既有紀錄,不是整份覆寫——直接覆寫會把沒跑到的判決清掉。
    # 併回後整張表再對照一次現行來源:不符的標 stale 寫回去,不讓舊 killed 原樣留著。
    merged = persist(True)
    table = {rid: merged.get(rid) for rid in [m["id"] for m in mutants]}
    table.update({rid: rec for rid, rec in merged.items() if rid not in table})
    ids_run = {m["id"] for m in selected}
    counts = tally(table, ids_run)
    print("\n本次 " + str(len(ids_run)) + ":" + format_counts(counts))
    if set(table) != ids_run:
        print("歷次紀錄(不是本次覆蓋)" + str(len([r for r in table.values() if r is not None])) + ":"
              + format_counts(tally(table)))
        print("  (過期明細用 --check 列出)")

    if counts["crashed"]:
        print("崩潰（crashed）已算被偵測到，與斷言殺死分開計，不影響結束碼。")
    if counts["blocked"]:
        print("⚠ 有受阻的變異,這一輪的結果不完整——受阻的沒有被驗證過,"
              "不要當成殺死。等環境穩定後只重跑那幾個。")
    return exit_code(counts, strict=not only)


def run_pass(mutants, only, root=ROOT, results_path=RESULTS, today=None, oracle=None, audit_equivalents=True):
    bridge = [m for m in mutants if m.get("binary") == "bridge"]
    if not bridge:
        return _run_core_pass(mutants, only, root, results_path, today, oracle, audit_equivalents)
    core = [m for m in mutants if m.get("binary") != "bridge"]
    selected = {m["id"] for m in mutants if not only or m["id"] in only}
    core_ids = selected & {m["id"] for m in core}
    # The legacy core writer evaluates exactly its table. Preserve bridge rows
    # around it so a core-only subset never silently deletes other receipts.
    previous = {k: v for k, v in load_records(results_path).items() if k in {m["id"] for m in bridge}}
    if core_ids:
        code = _run_core_pass(core, None if not only else core_ids, root, results_path, today, oracle, audit_equivalents)
        records = load_records(results_path); records.update(previous); save_records(results_path, records)
        if code == 2:
            return 2
    wanted = [m for m in bridge if m["id"] in selected]
    if wanted:
        import mutation_bridge
        try:
            mutation_bridge.run_pass(sys.modules[__name__], wanted, root, results_path, today)
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            print("BRIDGE BASELINE BLOCKED:", str(exc)); return 2
    src = Sources(root)
    table = evaluate_table(mutants, load_records(results_path), src, today or datetime.date.today().isoformat(),
                           oracle or oracle_hash(), require_execution=audit_equivalents)
    save_records(results_path, {k: v for k, v in table.items() if v is not None})
    counts = tally(table, selected)
    print("本次 " + str(len(selected)) + ":" + format_counts(counts))
    return exit_code(counts, strict=not only)


def check_pass(mutants, root=ROOT, results_path=RESULTS, killers=False, oracle=None, require_execution=True):
    """不編譯、不跑:把結果檔對照現行來源與變異表,彙總並給結束碼。"""
    src = Sources(root)
    today = datetime.date.today().isoformat()
    table = evaluate_table(mutants, load_records(results_path), src, today, oracle or oracle_hash(), require_execution)
    counts = tally(table)
    print(f"結果檔 {results_path}")
    print(f"變異表 {len(mutants)} 筆,紀錄 {len([r for r in table.values() if r is not None])} 筆")
    print(format_counts(counts))
    print_stale(table)
    for rid, rec in table.items():
        if rec is not None and rec.get("verdict") in ("survived", "invalid", "blocked", "crashed"):
            where = ""
            if rec.get("verdict") == "crashed" and rec.get("crashed_on"):
                where = " [" + ", ".join(rec["crashed_on"]) + "]"
            print(f"  {rec['verdict'].upper()} {rid}{where}  {rec.get('desc')}  <- {rec.get('why')}")
    if killers:
        for rid, rec in table.items():
            if rec is not None and rec.get("verdict") == "killed":
                print(f"  KILLED {rid}  <- {', '.join(rec.get('killed_by') or ['(舊紀錄,沒有 killed_by)'])}")
    return exit_code(counts, strict=True)


# ============================================================
# 誠實性規則的自我測試(不編譯、不碰 repo 的檔案)
# ============================================================
def selftest():
    checks = 0

    def quiet(fn, *args, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return fn(*args, **kwargs)

    def ok(cond, msg):
        nonlocal checks
        checks += 1
        if not cond:
            print("SELFTEST FAIL: " + msg)
            raise SystemExit(1)

    with tempfile.TemporaryDirectory(prefix="mutate-selftest-") as tmp:
        root = pathlib.Path(tmp)
        (root / "geometry-core").mkdir()
        main_path = root / MAIN_REL
        inc_path = root / "geometry-core" / "a.inc"
        other_path = root / "geometry-core" / "b.inc"
        # 故意用 CRLF:雜湊與錨點都必須在 LF 正規化後計算
        main_path.write_bytes(b'#include "geometry-core/a.inc"\r\n#include "geometry-core/b.inc"\r\n'
                              b'int main_v = 1;\r\nint keep = 2;\r\n')
        inc_path.write_bytes(b'#include "b_helper.h"\r\nint a_v = 10;\r\n')
        (root / "geometry-core" / "b_helper.h").write_bytes(b'int helper = 0;\r\n')
        other_path.write_bytes(b'int b_v = 20;\r\n')
        results = root / "results.json"
        oracle = "r" * 64
        today = "2026-01-01"

        def defs(**over):
            base = {
                "MA": dict(id="MA", desc="main", old="main_v = 1", new="main_v = 2"),
                "MB": dict(id="MB", desc="inc", file="geometry-core/a.inc", old="a_v = 10", new="a_v = 11"),
                "ME": dict(id="ME", desc="equiv", old="keep = 2", new="keep = 3", equivalent="等價理由原文"),
                "MR": dict(id="MR", desc="retired", old="gone_token", new="x", retired="退役依據原文"),
            }
            base.update(over)
            return list(base.values())

        # 1) 定義分類與暫存複本
        src = Sources(root)
        ms = defs()
        ok([definition_kind(m, src)[0] for m in ms] == ["run", "run", "equivalent", "retired"], "definition_kind 分類")
        ok(set(src.texts) == {MAIN_REL, "geometry-core/a.inc", "geometry-core/b.inc", "geometry-core/b_helper.h"},
           "include 閉包(含巢狀)")
        built = build_mutant_source(ms[1], src)
        ok("a_v = 11" in built and "a_v = 10" not in built and '#include "geometry-core/a.inc"' not in built,
           "對 .inc 的變異必須把 #include 行原地換掉")
        ok('#include "geometry-core/b_helper.h"' in built, "內嵌檔的相對 include 要改成相對 repo 根")
        ok(build_mutant_source(ms[0], src).count("main_v = 2") == 1, "對主檔的單點替換")

        # 2) 新紀錄 -> 帶雜湊,且對現況有效
        recs = {m["id"]: make_record(m, src, v, m.get(v, "w"), today, oracle)
                for m, v in zip(ms, ("killed", "survived", "equivalent", "retired"))}
        ok(all(recs[i].get("source_sha256") for i in ("MA", "MB", "ME")), "非 retired 紀錄帶 source_sha256")
        ok("source_sha256" not in recs["MR"], "retired 紀錄不帶來源雜湊")
        ok(recs["MB"]["source_file"] == "geometry-core/a.inc"
           and recs["MB"]["source_sha256"] == src.hashes["geometry-core/a.inc"], "雜湊是被變異那個檔的")
        table = evaluate_table(ms, recs, src, today, oracle)
        ok([table[i]["verdict"] for i in ("MA", "MB", "ME", "MR")] == ["killed", "survived", "equivalent", "retired"],
           "來源未變時判決原樣保留")
        counts = tally(table)
        ok(counts["killed"] == 1 and counts["stale"] == 0, "彙總 killed=1 stale=0")

        # 3) 牙:原本 killed,現在錨點找不到 -> 必須是 invalid,不是 killed(走完整 run_pass 寫檔路徑)
        save_records(results, {"MA": recs["MA"], "MB": recs["MB"]})
        broken = defs(MA=dict(id="MA", desc="main", old="main_v = 1 /*不存在*/", new="main_v = 2"))
        code = quiet(run_pass, broken, {"MA"}, root=root, results_path=results, today=today, oracle=oracle, audit_equivalents=False)
        saved = json.loads(results.read_text(encoding="utf-8"))
        ok(saved["MA"]["verdict"] == "invalid", "錨點壞掉的舊 killed 必須被 invalid 覆蓋,實得 " + saved["MA"]["verdict"])
        ok("錨點" in saved["MA"]["why"], "invalid 的理由要講錨點")
        ok(code == 1, "含 invalid 的結束碼非零,實得 " + str(code))
        ok(saved["MB"]["verdict"] == "survived", "沒選到的 id 的有效紀錄原樣保留")

        # 3b) 錨點不唯一同樣 invalid
        dup = defs(MA=dict(id="MA", desc="main", old="int", new="long"))
        save_records(results, {"MA": recs["MA"]})
        quiet(run_pass, dup, {"MA"}, root=root, results_path=results, today=today, oracle=oracle, audit_equivalents=False)
        saved = json.loads(results.read_text(encoding="utf-8"))
        ok(saved["MA"]["verdict"] == "invalid" and "出現" in saved["MA"]["why"], "錨點不唯一 -> invalid")

        # 4) 等價變異:錨點在 -> 保留理由;不在 -> invalid 且理由文字另存
        gone = defs(ME=dict(id="ME", desc="equiv", old="keep = 99", new="keep = 3", equivalent="等價理由原文"))
        save_records(results, {})
        quiet(run_pass, gone, {"ME"}, root=root, results_path=results, today=today, oracle=oracle, audit_equivalents=False)
        saved = json.loads(results.read_text(encoding="utf-8"))
        ok(saved["ME"]["verdict"] == "invalid" and saved["ME"]["equivalent_why"] == "等價理由原文",
           "等價變異錨點不在 -> invalid,且保留等價理由文字")
        quiet(run_pass, ms, {"ME"}, root=root, results_path=results, today=today, oracle=oracle, audit_equivalents=False)
        saved = json.loads(results.read_text(encoding="utf-8"))
        ok(saved["ME"]["verdict"] == "equivalent" and saved["ME"]["why"] == "等價理由原文", "等價變異錨點在 -> 理由原文")

        # 5) 退役:舊錨點又出現 -> invalid
        revived = defs(MR=dict(id="MR", desc="retired", old="keep = 2", new="x", retired="退役依據原文"))
        ok(definition_kind(revived[3], src)[0] == "invalid", "退役變異的舊錨點又出現 -> invalid")

        # 6) stale:被變異檔改了、沒帶雜湊、變異定義改了、閉包內別的檔改了、id 不在表內
        old_main = main_path.read_bytes()
        main_path.write_bytes(old_main + b"/* edit */\r\n")
        src2 = Sources(root)
        t2 = evaluate_table(ms, recs, src2, today, oracle)
        ok(t2["MA"]["verdict"] == "stale" and t2["MA"]["stale_from"] == "killed", "主檔改了 -> killed 變 stale")
        ok(t2["MB"]["verdict"] == "stale", "閉包內的檔(主檔)改了 -> 連目標檔沒變的 .inc 變異也 stale")
        ok(tally(t2)["killed"] == 0, "stale 不計入 killed")
        main_path.write_bytes(old_main)
        t3 = evaluate_table(ms, recs, Sources(root), today, oracle)
        ok(t3["MA"]["verdict"] == "killed", "還原來源後 stale 不是單向的,純來源還原要復原")
        # 把 stale 寫回再還原
        save_records(results, {k: v for k, v in t2.items() if v})
        back = evaluate_table(ms, load_records(results), Sources(root), today, oracle)
        ok(back["MA"]["verdict"] == "killed" and "stale_from" not in back["MA"], "寫回的 stale 紀錄可在來源還原後復原")

        other_path.write_bytes(other_path.read_bytes() + b"/* edit */\r\n")
        t4 = evaluate_table(ms, recs, Sources(root), today, oracle)
        ok(t4["MA"]["verdict"] == "stale" and "閉包" in t4["MA"]["stale_why"], "別的 include 檔改了 -> stale(閉包雜湊)")
        other_path.write_bytes(b"int b_v = 20;\r\n")

        naked = {k: {kk: vv for kk, vv in v.items() if kk not in ("source_sha256", "closure_sha256", "oracle_sha256")}
                 for k, v in recs.items()}
        t5 = evaluate_table(ms, naked, Sources(root), today, oracle)
        ok(t5["MA"]["verdict"] == "stale" and "provenance" in t5["MA"]["stale_why"], "沒有雜湊的舊紀錄 -> stale")
        ok(t5["ME"]["verdict"] == "stale", "沒有雜湊的 equivalent 也 stale")

        edited = defs(MA=dict(id="MA", desc="main", old="main_v = 1", new="main_v = 3"))
        t6 = evaluate_table(edited, recs, Sources(root), today, oracle)
        ok(t6["MA"]["verdict"] == "stale" and "變異定義" in t6["MA"]["stale_why"], "改了變異的 new -> 不能沿用舊判決")

        t7 = evaluate_table(ms[:1], recs, Sources(root), today, oracle)
        ok(t7["MB"]["verdict"] == "stale" and "不在變異表" in t7["MB"]["stale_why"], "孤兒紀錄 -> stale")

        # 7) 表與結束碼
        c = tally(table)
        ok(c["survived"] == 1 and exit_code(c, True) == 1, "表裡有 survived -> 1")
        c["survived"] = 0
        ok(exit_code(c, True) == 0, "全乾淨 -> 0")
        c = tally(table)
        c["survived"] = 1
        ok(exit_code(c, False) == 1, "survived -> 1")
        c = tally(table)
        c["invalid"] = 1
        ok(exit_code(c, False) == 1, "invalid -> 1")
        c = tally(table)
        c["stale"] = 1
        ok(exit_code(c, False) == 1, "stale -> 1")
        c = tally(table)
        c["blocked"] = 1
        c["survived"] = 1
        ok(exit_code(c, False) == 2, "blocked 先於 survived -> 2")
        c = tally(evaluate_table(ms, {}, Sources(root), today, oracle))
        ok(c["unrun"] == 4 and exit_code(c, True) == 1 and exit_code(c, False) == 0, "unrun 只在完整跑/--check 才算不及格")

        # 8) check_pass 端到端:killed 但沒帶雜湊的舊檔 -> 非零
        save_records(results, {"MA": {"desc": "main", "verdict": "killed", "why": "x"}})
        ok(quiet(check_pass, ms, root=root, results_path=results, oracle=oracle) != 0, "--check:舊式無雜湊 killed 不得放行")

        # 9) 裁判雜湊:run_tests.py 或被引用的夾具變了 -> killed / survived 變 stale
        fake_runner = root / "fake_run_tests.py"
        fake_runner.write_bytes(b"TESTS = []\r\n")
        (root / "a.scene").write_bytes(b"surface 1\r\ntimber 1\r\n")
        (root / "b.scene").write_bytes(b"surface 2\r\n")
        (root / "unused.scene").write_bytes(b"not referenced\r\n")
        fake_tests = [{"scene": "b.scene"}, {"scene": "a.scene"}]

        def oh(tests=fake_tests):
            return oracle_hash(fake_runner, root, tests)

        h0 = oh()
        ok(len(h0) == 64 and oh() == h0, "oracle_hash 決定性")
        ok(oracle_hash(fake_runner, root, list(reversed(fake_tests))) == h0, "oracle_hash 與 TESTS 順序無關(依檔名排序)")
        (root / "a.scene").write_bytes(b"surface 1\ntimber 1\n")
        ok(oh() == h0, "夾具 CRLF/LF 不影響裁判雜湊")
        (root / "unused.scene").write_bytes(b"edited but not referenced\n")
        ok(oh() == h0, "沒被 TESTS 引用的 .scene 不影響裁判雜湊")
        (root / "a.scene").write_bytes(b"surface 1\ntimber 2\n")
        h_fixture = oh()
        ok(h_fixture != h0, "改了被引用的夾具內容 -> 裁判雜湊改變")
        (root / "a.scene").write_bytes(b"surface 1\ntimber 1\n")
        fake_runner.write_bytes(b"TESTS = []  # edited\r\n")
        h_runner = oh()
        ok(h_runner != h0 and h_runner != h_fixture, "改了 run_tests.py -> 裁判雜湊改變")
        fake_runner.write_bytes(b"TESTS = []\r\n")
        ok(oh() == h0, "還原後雜湊復原")
        (root / "b.scene").unlink()
        ok(oh() != h0, "被引用的夾具不見 -> 裁判雜湊改變")
        (root / "b.scene").write_bytes(b"surface 2\r\n")
        ok(oh() == h0, "夾具補回 -> 雜湊復原")
        ok(oracle_hash() == oracle_hash() and all((ROOT / spec["scene"]).is_file() for spec in TESTS),
           "真正的 TESTS 引用的夾具都在(裁判雜湊沒有 MISSING 標記)")

        orecs = {m["id"]: make_record(m, src, v, m.get(v, "w"), today, h0, killed_by=["a.scene"] if v == "killed" else None)
                 for m, v in zip(ms, ("killed", "survived", "equivalent", "retired"))}
        ok(orecs["MA"]["oracle_sha256"] == h0 and "runner_sha256" not in orecs["MA"], "新紀錄帶 oracle_sha256(沒有 runner_sha256)")
        ok(evaluate_table(ms, orecs, src, today, h0)["MA"]["verdict"] == "killed", "裁判沒變 -> killed 保留")
        t_or = evaluate_table(ms, orecs, src, today, h_fixture)
        ok(t_or["MA"]["verdict"] == "stale" and "裁判" in t_or["MA"]["stale_why"] and t_or["MA"]["stale_from"] == "killed",
           "夾具內容改了 -> killed 變 stale")
        ok(t_or["MB"]["verdict"] == "stale", "裁判變了 -> survived 也 stale")
        ok(t_or["ME"]["verdict"] == "equivalent" and t_or["MR"]["verdict"] == "retired", "equivalent / retired 不受裁判雜湊約束")
        ok(tally(t_or)["killed"] == 0 and tally(t_or)["stale"] == 2, "stale 不計入 killed")
        t_rn = evaluate_table(ms, orecs, src, today, h_runner)
        ok(t_rn["MA"]["verdict"] == "stale", "run_tests.py 改了 -> killed 變 stale")
        save_records(results, {k: v for k, v in t_or.items() if v})
        ok(evaluate_table(ms, load_records(results), src, today, h0)["MA"]["verdict"] == "killed", "裁判還原後 stale 自動復原")
        ok(quiet(check_pass, ms, root=root, results_path=results, oracle=h_fixture) != 0, "--check:裁判變了 -> 結束碼非零")
        old_style = {k: {kk: vv for kk, vv in v.items() if kk != "oracle_sha256"} for k, v in orecs.items()}
        for v in old_style.values():
            v["runner_sha256"] = "x" * 64
        t_old = evaluate_table(ms, old_style, src, today, h0)
        ok(t_old["MA"]["verdict"] == "stale" and "裁判雜湊" in t_old["MA"]["stale_why"], "只有舊 runner_sha256 的 killed -> stale")

        # 10) killed_by
        ok(orecs["MA"]["killed_by"] == ["a.scene"] and "killed_by" not in orecs["MB"], "killed 紀錄帶 killed_by,其他不帶")
        cases = [{"scene": spec["scene"], "status": "pass", "detail": "ok", "oracle": "x"} for spec in TESTS]
        for idx in (3, 7, 9, 11, 13, 15, 17):
            cases[idx]["status"] = "fail"
            cases[idx]["detail"] = "FAIL x"
        row = {"schema": "geometry-native-tests/1", "total": len(TESTS),
               "counts": {"pass": len(TESTS) - 7, "fail": 7, "infrastructure": 0}, "cases": cases}
        fake_proc = types.SimpleNamespace(stdout="noise\nGEOMETRY_TEST_RESULT " + json.dumps(row) + "\n", returncode=1)
        ok(classify_test_run(fake_proc)[0] == "killed", "classify_test_run 判 killed")
        fb = failed_scenes(fake_proc)
        ok(fb == [TESTS[i]["scene"] for i in (3, 7, 9, 11, 13)] and len(fb) == KILLED_BY_MAX, "failed_scenes 依 TESTS 順序取前 5 個")
        ok(failed_scenes(types.SimpleNamespace(stdout="garbage", returncode=1)) == [], "failed_scenes 遇到壞輸出回空")
        save_records(results, {"MA": orecs["MA"]})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            check_pass(ms, root=root, results_path=results, killers=True, oracle=h0, require_execution=False)
        ok("KILLED MA  <- a.scene" in buf.getvalue(), "--check --killers 列出 killed_by")

        # 10b) crashed：連續同一夾具的存取違規，與 SAC / 其他異常結束分開
        ok(is_access_violation_detail("INFRA abnormal executable exit -11: "), "Linux SIGSEGV -11 是存取違規")
        ok(is_access_violation_detail("INFRA abnormal executable exit 3221225477: "), "Windows 0xC0000005 無號是存取違規")
        ok(is_access_violation_detail("INFRA abnormal executable exit -1073741819: "), "Windows 0xC0000005 有號是存取違規")
        ok(not is_access_violation_detail("INFRA abnormal executable exit -6: "), "SIGABRT 不是存取違規")
        ok(not is_access_violation_detail("啟動失敗: [WinError 4551]"), "WinError 4551 不是存取違規結束碼")

        def structured(overrides, returncode):
            cases = [{"scene": spec["scene"], "status": "pass", "detail": "ok", "oracle": "x"}
                     for spec in TESTS]
            for idx, status, detail in overrides:
                cases[idx]["status"] = status
                cases[idx]["detail"] = detail
            counts = {key: sum(case["status"] == key for case in cases)
                      for key in ("pass", "fail", "infrastructure")}
            payload = {"schema": "geometry-native-tests/1", "total": len(TESTS),
                       "counts": counts, "cases": cases}
            return types.SimpleNamespace(
                stdout="GEOMETRY_TEST_RESULT " + json.dumps(payload, ensure_ascii=False) + "\n",
                returncode=returncode)

        scene_a = TESTS[0]["scene"]
        scene_b = TESTS[1]["scene"]
        av_proc = structured([(0, "infrastructure", "INFRA abnormal executable exit -11: ")], 2)
        ok(access_violation_scenes(av_proc) == (scene_a,), "單次 -11 能抽出夾具")
        ok(classify_test_run(av_proc)[0] == "blocked", "單次存取違規仍是 blocked，不直接變 crashed")
        win_proc = structured([(0, "infrastructure", "INFRA abnormal executable exit 3221225477: ")], 2)
        ok(access_violation_scenes(win_proc) == (scene_a,), "Windows 無號存取違規能抽出夾具")
        signed_proc = structured([(0, "infrastructure", "INFRA abnormal executable exit -1073741819: ")], 2)
        ok(access_violation_scenes(signed_proc) == (scene_a,), "Windows 有號存取違規能抽出夾具")
        abort_proc = structured([(0, "infrastructure", "INFRA abnormal executable exit -6: ")], 2)
        ok(access_violation_scenes(abort_proc) is None, "其他異常結束碼不抽出夾具")
        mixed = structured([
            (0, "infrastructure", "INFRA abnormal executable exit -11: "),
            (1, "fail", "FAIL x"),
        ], 2)
        ok(access_violation_scenes(mixed) is None, "夾雜斷言失敗就不是純崩潰")
        two = structured([
            (0, "infrastructure", "INFRA abnormal executable exit -11: "),
            (1, "infrastructure", "INFRA abnormal executable exit -11: "),
        ], 2)
        ok(access_violation_scenes(two) == (scene_a, scene_b), "多個存取違規依 TESTS 順序保留")

        av = ("blocked", "INFRA abnormal executable exit -11: ", (scene_a,), [])
        verdict, why, killers, crashed_on = verdict_from_attempts([av, av, av])
        ok(verdict == "crashed" and crashed_on == [scene_a] and killers == [], "三次同一夾具 -> crashed")
        ok(scene_a in why and "不是斷言殺死" in why, "crashed 理由寫明夾具且與 killed 分開")
        ok(verdict_from_attempts([av, av])[0] == "blocked", "少於三次不算 crashed")
        other = ("blocked", "INFRA abnormal executable exit -11: ", (scene_b,), [])
        ok(verdict_from_attempts([av, other, av])[0] == "blocked", "夾具不一致仍是 blocked")
        pair = ("blocked", "INFRA abnormal executable exit 3221225477: ", (scene_a, scene_b), [])
        pair_verdict = verdict_from_attempts([pair, pair, pair])
        ok(pair_verdict[0] == "crashed" and pair_verdict[3] == [scene_a, scene_b], "同一組多夾具也算 crashed")
        startup = ("blocked", "啟動失敗: [WinError 4551] Application Control", None, [])
        startup_verdict, startup_why, _, _ = verdict_from_attempts([startup, startup, startup])
        ok(startup_verdict == "blocked" and "4551" in startup_why, "連續 WinError 4551 仍是 blocked")
        abort_attempt = ("blocked", "INFRA abnormal executable exit -6: ", None, [])
        abort_verdict, abort_why, _, _ = verdict_from_attempts([abort_attempt, abort_attempt, abort_attempt])
        ok(abort_verdict == "blocked" and "異常結束碼" in abort_why, "連續非存取違規的異常結束仍是 blocked")
        killed_attempt = ("killed", "scene: FAIL", None, ["a.scene"])
        ok(verdict_from_attempts([av, killed_attempt])[0] == "killed", "後一次被斷言抓住就記 killed")
        ok(verdict_from_attempts([("survived", "all passed", None, [])])[0] == "survived", "全過不等於 crashed")

        blank = {key: 0 for key in list(VERDICTS) + ["unrun"]}
        blank["killed"] = 1
        blank["crashed"] = 1
        ok(exit_code(blank, True) == 0, "只有 killed 與 crashed -> 0")
        ok("崩潰 crashed 1" in format_counts(blank), "彙總分開顯示 crashed")
        blank["blocked"] = 1
        ok(exit_code(blank, True) == 2, "blocked 仍先於 crashed -> 2")
        blank["blocked"] = 0
        blank["survived"] = 1
        ok(exit_code(blank, False) == 1, "survived 不因 crashed 被抵消")

        crec = make_record(ms[0], src, "crashed", "存取違規", today, h0, crashed_on=[scene_a])
        ok(crec.get("crashed_on") == [scene_a] and "killed_by" not in crec, "crashed 帶 crashed_on，不帶 killed_by")
        ok(evaluate_table(ms, {"MA": crec}, src, today, h0)["MA"]["verdict"] == "crashed", "裁判沒變 -> crashed 保留")
        stale_c = evaluate_table(ms, {"MA": crec}, src, today, h_fixture)["MA"]
        ok(stale_c["verdict"] == "stale" and stale_c["stale_from"] == "crashed", "裁判變了 -> crashed 變 stale")
        restored = evaluate_table(ms, {"MA": stale_c}, src, today, h0)["MA"]
        ok(restored["verdict"] == "crashed" and "stale_from" not in restored, "裁判還原 -> crashed 復原")
        ok(evaluate_table(ms, {"MA": crec}, src2, today, h0)["MA"]["verdict"] == "stale", "來源變了 -> crashed 變 stale")
        crash_counts = tally({"MA": {"verdict": "crashed"}})
        ok(crash_counts["killed"] == 0 and crash_counts["crashed"] == 1, "crashed 不計入 killed")
        save_records(results, {"MA": crec})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            check_pass(ms, root=root, results_path=results, oracle=h0, require_execution=False)
        ok(f"CRASHED MA [{scene_a}]" in buf.getvalue(), "--check 列出 crashed_on")

        # 11) exe 指紋快取
        calls = []

        def fake_compile(m, exe):
            calls.append(m["id"])
            pathlib.Path(exe).write_bytes(("EXE:" + m["new"] + ":" + src.closure).encode("utf-8"))
            return True, ""

        csha = "c" * 64
        mdir = root / "mutants" / "MA"
        st, exe, _ = prepare_mutant_exe(ms[0], src, mdir, fake_compile, None, csha)
        ok(st == "built" and exe.is_file() and sidecar_path(exe).is_file() and len(calls) == 1, "第一次:編譯並寫 sidecar")
        mtime0 = exe.stat().st_mtime_ns
        st, exe, _ = prepare_mutant_exe(ms[0], src, mdir, fake_compile, None, csha)
        ok(st == "cached" and len(calls) == 1 and exe.stat().st_mtime_ns == mtime0, "第二次:沿用,不呼叫編譯、exe 沒被動")
        changed = dict(ms[0], new="main_v = 7")
        st, _, _ = prepare_mutant_exe(changed, src, mdir, fake_compile, None, csha)
        ok(st == "built" and len(calls) == 2, "改了變異的替換字串 -> 重編")
        st, _, _ = prepare_mutant_exe(ms[0], src, mdir, fake_compile, None, csha)
        ok(st == "built" and len(calls) == 3, "變異定義換回原本那份(與 sidecar 不同)也要重編")
        other_path.write_bytes(other_path.read_bytes() + b"/* edit */\r\n")
        src_b = Sources(root)
        st, _, _ = prepare_mutant_exe(ms[0], src_b, mdir, fake_compile, None, csha)
        ok(st == "built" and len(calls) == 4, "include 閉包內別的檔改了 -> 重編")
        other_path.write_bytes(b"int b_v = 20;\r\n")
        st, _, _ = prepare_mutant_exe(ms[0], src, mdir, fake_compile, None, csha)
        ok(st == "built" and len(calls) == 5, "來源還原後,指紋與上一次(已改來源)的 exe 不同 -> 重編")
        st, _, _ = prepare_mutant_exe(ms[0], src, mdir, fake_compile, None, "d" * 64)
        ok(st == "built" and len(calls) == 6, "編譯指令(_cl.bat)變了 -> 重編")
        st, exe, _ = prepare_mutant_exe(ms[0], src, mdir, fake_compile, None, "d" * 64)
        ok(st == "cached" and len(calls) == 6, "指紋都相符 -> 沿用")
        exe.write_bytes(b"tampered")
        st, _, _ = prepare_mutant_exe(ms[0], src, mdir, fake_compile, None, "d" * 64)
        ok(st == "built" and len(calls) == 7, "exe 內容被動過(與 sidecar 的 exe 雜湊不符)-> 重編")
        # 結果紀錄相符也不能證明一支缺失 sidecar 的 exe；以被替換的檔案驗證。
        sidecar_path(exe).unlink()
        exe.write_bytes(b"unverified replacement")
        good_rec = {"closure_sha256": src.closure, "mutant_sha256": mutant_key(ms[0])}
        st, _, _ = prepare_mutant_exe(ms[0], src, mdir, fake_compile, good_rec, "d" * 64)
        ok(st == "built" and len(calls) == 8 and sidecar_path(exe).is_file()
           and exe.read_bytes() != b"unverified replacement", "沒有 sidecar，即使結果檔雜湊相符仍須重編")
        st, _, _ = prepare_mutant_exe(ms[0], src, mdir, fake_compile, good_rec, "d" * 64)
        ok(st == "cached" and len(calls) == 8, "重編建立可信 sidecar 後，下一輪沿用")
        write_sidecar(exe, mutant_fingerprint(ms[0], src, "d" * 64), "adopted: legacy migration")
        st, _, _ = prepare_mutant_exe(ms[0], src, mdir, fake_compile, good_rec, "d" * 64)
        ok(st == "built" and len(calls) == 9, "舊版憑結果紀錄補發的 adopted sidecar 也必須重編")
        sidecar_path(exe).unlink()
        for bad in (None, dict(good_rec, closure_sha256="0" * 64), dict(good_rec, mutant_sha256="0" * 64), {}):
            sidecar_path(exe).unlink(missing_ok=True)
            n = len(calls)
            st, _, _ = prepare_mutant_exe(ms[0], src, mdir, fake_compile, bad, "d" * 64)
            ok(st == "built" and len(calls) == n + 1, "沒有 sidecar 且結果檔沒有相符雜湊 -> 不採用,重編 " + repr(bad)[:30])

        def failing_compile(m, exe):
            return False, "編譯失敗: boom"

        bad_dir = root / "mutants" / "MB"
        st, exe_b, msg = prepare_mutant_exe(ms[1], src, bad_dir, failing_compile, None, csha)
        ok(st == "invalid" and "boom" in msg and not exe_b.exists() and not sidecar_path(exe_b).exists(), "編譯失敗 -> invalid,不留 exe / sidecar")

        bcalls = []

        def base_compile(exe):
            bcalls.append(1)
            pathlib.Path(exe).write_bytes(b"BASE" + src.closure.encode("utf-8"))
            return True, ""

        bdir = root / "mutants" / "_baseline"
        st, bexe, _ = prepare_baseline_exe(src, bdir, base_compile, csha)
        ok(st == "built" and bexe.name == "baseline.exe" and bexe.is_file() and len(bcalls) == 1
           and not list(bdir.glob("baseline.*.exe")), "baseline 第一次編譯(pid 暫名已換成正名)")
        st, _, _ = prepare_baseline_exe(src, bdir, base_compile, csha)
        ok(st == "cached" and len(bcalls) == 1, "baseline 沿用快取")
        other_path.write_bytes(other_path.read_bytes() + b"/* edit */\r\n")
        st, _, _ = prepare_baseline_exe(Sources(root), bdir, base_compile, csha)
        ok(st == "built" and len(bcalls) == 2, "baseline:來源變了 -> 重編")
        other_path.write_bytes(b"int b_v = 20;\r\n")

    print(f"SELFTEST OK ({checks} checks)")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if args == ["--selftest"]:
        return selftest()
    if args == ["--check"]:
        return check_pass(MUTANTS)
    if args == ["--check", "--killers"]:
        return check_pass(MUTANTS, killers=True)
    only = set(args)
    unknown = only - {m["id"] for m in MUTANTS}
    if unknown:
        print("Unknown mutant IDs: " + ", ".join(sorted(unknown)))
        return 2
    return run_pass(MUTANTS, only)


if __name__ == "__main__":
    sys.exit(main())
