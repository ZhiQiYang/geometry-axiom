# -*- coding: utf-8 -*-
"""公理層見證圖(witness):一條條文 ↔ 一個夾具 ↔ 一張由引擎推導、commit 進 repo 的 SVG。

定性(使用者 2026-09-20 拍板,BACKLOG GEO-131):
  示意圖不是文件,是條文的**見證**。條文為真 ⇒ 圖不變,所以圖沒有版本問題;
  圖變了 ⇒ 不是「重出一張」,而是**警報**——某個依賴項(夾具、引擎、條文)動了,
  必須交由使用者確認要改哪一邊。本工具因此只做兩件事,而且第二件永遠不寫檔:

  --build   依 manifest 跑引擎、裁出指定視圖、寫進 witness/<條號>.svg。
            只在「第一次建立」或「使用者看過 diff 後明示重建」時用。
  --check   重跑一次,與 commit 的圖**逐位元**比對。任何不同 → 印 diff、非 0 退出,
            **絕不覆寫**。CI / 交付前跑這個。

圖為什麼不手繪:手繪的圖跟白話一樣是人寫的,會跟條文一起錯,偵測不到漂移
(`公理層-白話.md` 已經整份落後過一次)。引擎推導的圖才有「變了就是有事」的性質。
執行路徑沿用 `axiom_examples.py` 的 run_scene / crop_bottom / before_failure,
不另做一套幾何或裁切。

SVG 內嵌兩個雜湊(夾具內容、引擎 exe)只是**診斷線索**,讓 --check 失敗時能說
「是夾具動了」還是「夾具沒動、引擎輸出變了」;它們不參與比對——比對的是整個檔案。
引擎 exe 的雜湊會隨重新編譯而變,所以只印在報告,不寫進 SVG。

manifest(`witness/manifest.json`)一條一項:
  { "I19": { "scene": "_role_rc_boundary_ok.scene", "expect": "accept",
             "view": "bottom", "gist": "boundary 頂外輪廓邊是合法的" } }
  expect=reject 的夾具走 before_failure 取「違規前一刻」當圖(與閱讀器例圖同一規矩)。
  view ∈ bottom(仰視)/front(前視)/side(側視)/all(整張三視圖,跨面條文用)。

用法:
  python geometry-guide/witness.py --build [條號 ...]     # 建立/重建(需 GEO_EXE 或 tests/cg_new.exe)
  python geometry-guide/witness.py --check [條號 ...]     # 比對;有差即非 0
  python geometry-guide/witness.py --list                 # 印 manifest 與每條狀態
"""
import argparse
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import axiom_examples as ax  # noqa: E402
import axiom_matrix as am    # noqa: E402

WITNESS_DIR = os.path.join(HERE, "witness")
MANIFEST = os.path.join(WITNESS_DIR, "manifest.json")

_STYLE = re.compile(r"<style>.*?</style>", re.S)

# 三視圖在 SVG 裡的順序與標題(current_geometry.c 的 VIEW_FRAMES:前/側/仰);
# "all" = 不裁,整張三視圖當見證(跨面條文如 D6c 需要同時看到兩個面)。
VIEWS = {"front": (0, "前視圖"), "side": (1, "側視圖"), "bottom": (2, "仰視圖"), "all": None}


def crop_view(svg, view):
    """回傳 (viewBox, 完整 viewBox, 去掉 <style> 的內文)。view=bottom 時等同 ax.crop_bottom。"""
    if view == "bottom":
        return ax.crop_bottom(svg)
    m = re.search(r'<svg[^>]*viewBox="([^"]+)"[^>]*>', svg)
    end = svg.rfind("</svg>")
    if not m or end < 0:
        raise WitnessError("SVG 沒有 viewBox 或結尾標籤")
    full = m.group(1)
    body = _STYLE.sub("", svg[m.end():end]).strip()
    if view == "all":
        return full, full, body
    idx, title = VIEWS[view]
    gs = list(ax._G.finditer(svg))
    if len(gs) != 3 or title not in gs[idx].group(7):
        raise WitnessError("SVG 版面與預期不符(找到 %d 個視圖,第 %d 個標題 %r)"
                           % (len(gs), idx + 1, gs[idx].group(7) if len(gs) > idx else None))
    tx, ty, x, y, w, h = (int(gs[idx].group(i)) for i in range(1, 7))
    return "%d %d %d %d" % (tx + x, ty + y, w, h), full, body


_CLAUSE_ID = re.compile(r"^[DIR]\d+[a-z]?$")


class WitnessError(Exception):
    pass


# ------------------------------------------------------------------
# manifest
# ------------------------------------------------------------------
def load_manifest():
    if not os.path.exists(MANIFEST):
        raise WitnessError("找不到 manifest:%s" % MANIFEST)
    with io.open(MANIFEST, encoding="utf-8") as f:
        m = json.load(f)
    if not isinstance(m, dict) or not m:
        raise WitnessError("manifest 必須是非空物件 {條號: {...}}")

    clause_ids = {c[0] for c in am.parse_clauses(am.read_text(am.AXIOM))}
    for cid, ent in m.items():
        if not _CLAUSE_ID.match(cid):
            raise WitnessError("manifest 條號格式不合:%r" % cid)
        if cid not in clause_ids:
            raise WitnessError("manifest 條號 %s 不存在於 公理層.md——條文被改號或刪除,先確認" % cid)
        for k in ("scene", "expect", "view", "gist"):
            if k not in ent:
                raise WitnessError("manifest %s 缺欄位 %s" % (cid, k))
        if ent["expect"] not in ("accept", "reject"):
            raise WitnessError("manifest %s 的 expect 只能是 accept / reject" % cid)
        if ent["view"] not in VIEWS:
            raise WitnessError("manifest %s 的 view=%r 不在 %s" % (cid, ent["view"], sorted(VIEWS)))
        scene = os.path.join(ROOT, ent["scene"])
        if not os.path.exists(scene):
            raise WitnessError("manifest %s 指的夾具不存在:%s" % (cid, ent["scene"]))
        # 沿用 axiom_matrix 的追溯判準:夾具註解必須提到這個條號,否則連結只存在於 manifest。
        text = io.open(scene, encoding="utf-8", errors="replace").read()
        if not re.search(r"(?<![A-Za-z0-9])%s(?![0-9a-z])" % re.escape(cid), text):
            raise WitnessError(
                "夾具 %s 的註解沒有提到 %s——先在夾具裡把連結寫下來(axiom_matrix 的判準),"
                "不要只靠 manifest" % (ent["scene"], cid))
    return m


def svg_path(cid):
    return os.path.join(WITNESS_DIR, "%s.svg" % cid)


# ------------------------------------------------------------------
# render
# ------------------------------------------------------------------
def _sha(data):
    return hashlib.sha256(data).hexdigest()[:16]


def render_one(exe, cid, ent, tmpdir):
    """回傳 (svg_bytes, info)。任何一步不成立就 raise,不產空圖。"""
    scene = os.path.join(ROOT, ent["scene"])
    scene_bytes = open(scene, "rb").read()
    r = ax.run_scene(exe, scene, tmpdir)

    if ent["expect"] == "accept":
        if r["rc"] != 0:
            raise WitnessError("%s:夾具 %s 標 accept 但引擎拒絕(rc=%d):%s"
                               % (cid, ent["scene"], r["rc"], (r["err"] or "").strip()[:200]))
        full_svg, note = r["svg"], ""
    else:
        if r["rc"] == 0:
            raise WitnessError("%s:夾具 %s 標 reject 但引擎接受(rc=0)——夾具或引擎變了,先確認"
                               % (cid, ent["scene"]))
        full_svg, note, why = ax.before_failure(exe, scene, r["err"], tmpdir)
        if not full_svg:
            raise WitnessError("%s:拒絕型夾具無法重建失敗前狀態:%s" % (cid, why))

    if not full_svg or 'class="surface"' not in full_svg:
        raise WitnessError("%s:引擎輸出沒有任何承載面(空框)" % cid)
    if ent["view"] == "bottom" and not ax.bottom_has_surface(full_svg):
        raise WitnessError("%s:仰視圖是空的" % cid)

    crop, full, body = crop_view(full_svg, ent["view"])
    style = _STYLE.search(full_svg)
    style = style.group(0) if style else ""

    # 見證圖是獨立檔,保留引擎自帶的 <style> 才看得出邊/參考線/角材的區別;
    # 閱讀器嵌入時會自己抽掉它(axiom_examples 的既有行為)。
    head = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!-- witness %s <- %s (%s, view=%s) scene-sha256=%s -->\n'
        '<!-- %s -->\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="100%%" viewBox="%s" data-full="%s">\n'
        % (cid, ent["scene"], ent["expect"], ent["view"], _sha(scene_bytes),
           (note or ent["gist"]).replace("--", "- -"), crop, full))
    out = head + style + "\n" + body + "\n</svg>\n"
    return out.encode("utf-8"), {"scene_sha": _sha(scene_bytes), "note": note}


# ------------------------------------------------------------------
# commands
# ------------------------------------------------------------------
def _select(manifest, ids):
    if not ids:
        return list(manifest.items())
    missing = [i for i in ids if i not in manifest]
    if missing:
        raise WitnessError("manifest 沒有這些條號:%s" % ", ".join(missing))
    return [(i, manifest[i]) for i in ids]


def cmd_build(exe, manifest, ids, force):
    os.makedirs(WITNESS_DIR, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="witness_")
    try:
        ax.smoke(exe, tmp)
        for cid, ent in _select(manifest, ids):
            path = svg_path(cid)
            data, info = render_one(exe, cid, ent, tmp)
            if os.path.exists(path) and not force:
                old = open(path, "rb").read()
                if old == data:
                    print("  不變   %-5s %s" % (cid, ent["scene"]))
                    continue
                # 已有 golden 且不同:這正是警報,不准在 --build 裡順手蓋掉。
                raise WitnessError(
                    "%s 已有見證圖且與重跑結果不同。這是警報不是待更新:先跑 --check 看 diff,"
                    "確認是夾具/引擎/條文哪一邊該改;確定要以新圖為準時再加 --force。" % cid)
            open(path, "wb").write(data)
            print("  寫入   %-5s %s  (夾具 sha %s%s)"
                  % (cid, os.path.relpath(path, ROOT), info["scene_sha"],
                     ";" + info["note"] if info["note"] else ""))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


def _scene_sha_in(svg_bytes):
    m = re.search(rb"scene-sha256=([0-9a-f]{16})", svg_bytes)
    return m.group(1).decode() if m else None


def cmd_check(exe, manifest, ids):
    tmp = tempfile.mkdtemp(prefix="witness_")
    bad = 0
    try:
        ax.smoke(exe, tmp)
        print("引擎 exe sha256=%s" % _sha(open(exe, "rb").read()))
        for cid, ent in _select(manifest, ids):
            path = svg_path(cid)
            if not os.path.exists(path):
                print("  缺圖   %-5s 尚未 --build" % cid)
                bad += 1
                continue
            old = open(path, "rb").read()
            try:
                new, info = render_one(exe, cid, ent, tmp)
            except WitnessError as exc:
                print("  失敗   %-5s %s" % (cid, exc))
                bad += 1
                continue
            if old == new:
                print("  一致   %-5s %s" % (cid, ent["scene"]))
                continue

            bad += 1
            old_sha = _scene_sha_in(old)
            if old_sha and old_sha != info["scene_sha"]:
                cause = "夾具 %s 內容變了(sha %s → %s)" % (ent["scene"], old_sha, info["scene_sha"])
            else:
                cause = "夾具沒變,引擎對同一夾具的輸出變了(引擎或其依賴的條文實作動了)"
            print("  ⚠ 警報 %-5s %s" % (cid, cause))
            diff = difflib.unified_diff(
                old.decode("utf-8", "replace").splitlines(),
                new.decode("utf-8", "replace").splitlines(),
                "witness/%s.svg (commit)" % cid, "witness/%s.svg (重跑)" % cid, lineterm="", n=1)
            lines = list(diff)
            for ln in lines[:40]:
                print("      " + ln)
            if len(lines) > 40:
                print("      … 共 %d 行差異" % len(lines))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if bad:
        print("\n%d 條見證不成立。本工具不覆寫;請確認是夾具、引擎還是條文該改,"
              "確定後才以 --build --force 重建。" % bad)
        return 1
    print("\n全部 %d 條見證一致。" % len(_select(manifest, ids)))
    return 0


def cmd_list(manifest):
    for cid, ent in manifest.items():
        state = "有圖" if os.path.exists(svg_path(cid)) else "缺圖"
        print("  %-5s %s  %-32s %s  %s" % (cid, state, ent["scene"], ent["expect"], ent["gist"]))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--build", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--list", action="store_true")
    p.add_argument("--force", action="store_true", help="--build 時允許覆蓋已存在且不同的見證圖")
    p.add_argument("--exe", help="geometry 執行檔;預設 GEO_EXE 或 tests/cg_new.exe")
    p.add_argument("ids", nargs="*", help="只處理這些條號;不給 = 全部")
    a = p.parse_args(argv)

    manifest = load_manifest()
    if a.list:
        return cmd_list(manifest)
    exe = ax.resolve_exe(a.exe)
    if a.build:
        return cmd_build(exe, manifest, a.ids, a.force)
    return cmd_check(exe, manifest, a.ids)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (WitnessError, ax.RenderError) as exc:
        print("FAIL:%s" % exc)
        sys.exit(2)
