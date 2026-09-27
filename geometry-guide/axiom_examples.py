# -*- coding: utf-8 -*-
"""公理層閱讀器的範例渲染:跑夾具、裁出平面圖、拒絕型的「失敗前」重建。

為什麼範例用既有的 *.scene 夾具而不是手寫散文:
  夾具是真的跑過的測試,有明確的接受/拒絕與長度數字,永遠不會跟實作漂移。
  手寫的「例如⋯」只是轉述,會模糊、會過期、沒人驗。

三件事,都拒絕靜默失敗:
  run_scene      跑一個夾具,一律把 SVG 導到暫存目錄(不准碰 repo 裡的
                 current_geometry.svg——run_tests.py 沒傳 --out,每跑一次就蓋一次)。
  crop_bottom    把三視圖 SVG 的 viewBox 換成仰視圖那一塊。只換 viewBox、
                 不刪內容,所以「展開三視圖」只是把屬性換回去。版面一變就 assert 炸掉。
  before_failure 拒絕型夾具在違規那行就 return 1,沒有圖。這裡把場景截到
                 報錯行之前重跑,拿「違規前一刻」的配置當圖。截完自己也不合法的
                 一律回 None + 理由,絕不拿空框充數。
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SMOKE_SCENE = "ceiling-a.scene"

# 三視圖 SVG 的版面:每個頂層 <g> = translate + frame rect + title。
# 第三個必是仰視圖(current_geometry.c 的 VIEW_FRAMES 順序:前/側/仰)。
_G = re.compile(
    r'<g transform="translate\((-?\d+),(-?\d+)\)">\s*'
    r'<rect class="frame" x="(-?\d+)" y="(-?\d+)" '
    r'width="(\d+)" height="(\d+)"/>\s*'
    r'<text[^>]*class="title">([^<]*)</text>')

_LINE_NO = re.compile(r":(\d+): ")
_ORPHAN = re.compile(r"角材 (\d+) 沒有 place")

# SVG 自帶的 <style> 是全域選擇器(.title/.label/.frame…),內嵌進閱讀器會
# 汙染卡片樣式。抽掉它,改由頁面 CSS 提供同內容的 scoped 版本。
_STYLE = re.compile(r"<style>.*?</style>\s*", re.S)


class RenderError(Exception):
    pass


def resolve_exe(explicit=None):
    """GEO_EXE > --exe > 預設。找不到就講清楚怎麼辦,不預設一個不存在的路徑。"""
    cand = explicit or os.environ.get("GEO_EXE") or \
        os.path.join(ROOT, "tests", "cg_new.exe")
    if not os.path.exists(cand):
        raise RenderError(
            "找不到 geometry 執行檔:%s\n"
            "先建置(tests/_cl.bat current_geometry.c tests/cg_new.exe),"
            "或用 GEO_EXE 指定。" % cand)
    return cand


def run_scene(exe, scene_path, tmpdir, timeout=30):
    """跑一個場景。回傳 dict(rc, out, err, svg)。svg 失敗時為 None。

    一律傳 --out 到 tmpdir:不傳的話 current_geometry.c 會寫到原始碼旁邊的
    current_geometry.svg,把 repo 弄髒。
    """
    out_svg = os.path.join(tmpdir, "render.svg")
    if os.path.exists(out_svg):
        os.remove(out_svg)

    try:
        p = subprocess.run(
            [exe, "--scene", str(scene_path), "--no-window", "--out", out_svg],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout)
    except OSError as exc:
        # SAC / Device Guard 會在這裡擋下來,執行檔根本沒啟動。
        raise RenderError(
            "執行檔啟動失敗:%s\n"
            "本機 Smart App Control 會封鎖新編譯的未簽章 exe。"
            "備援:在 WSL 裡 gcc -O2 -w -o /tmp/cg current_geometry.c -lm,"
            "再用 GEO_EXE=/tmp/cg 重跑。" % exc)

    svg = None
    if os.path.exists(out_svg):
        svg = open(out_svg, "rb").read().decode("utf-8", "replace")

    return {"rc": p.returncode, "out": p.stdout, "err": p.stderr, "svg": svg}


def resolve_bridge(explicit=None):
    """web_bridge 的位置:GEO_BRIDGE > 參數 > repo 內預設。

    有三條公理(R1 拾取、R4 dump 往返、R5 拖曳 clamp)的行為不存在於場景 DSL——
    SCENE_COMMANDS 裡沒有對應動詞,只有 bridge 的 pick / dump / drag 看得到。
    """
    cand = explicit or os.environ.get("GEO_BRIDGE") or \
        os.path.join(ROOT, "geometry-web", "web_bridge.exe")
    if not os.path.exists(cand):
        raise RenderError(
            "找不到 web_bridge:%s\n"
            "先建置(geometry-web\\build.bat),或用 GEO_BRIDGE 指定。" % cand)
    return cand


def run_bridge(bridge, commands, timeout=60):
    """一次餵完指令,回傳 [(指令, 回應原文)]。

    協定:stdin 一行一個指令,stdout 一行回一個 JSON 物件。
    行數對不上就是協定變了,直接炸掉——回應錯位比沒有更糟。
    """
    body = "\n".join(commands) + "\n"
    try:
        p = subprocess.run(
            [bridge], input=body, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout)
    except OSError as exc:
        raise RenderError(
            "web_bridge 啟動失敗:%s\n"
            "本機 Smart App Control 會封鎖新編譯的未簽章 exe。"
            "備援:在 WSL 裡編出 bridge 後用 GEO_BRIDGE 指定。" % exc)

    out = [ln for ln in (p.stdout or "").splitlines() if ln.strip()]
    if len(out) != len(commands):
        raise RenderError(
            "bridge 回應行數與指令數不符(送 %d 收 %d),協定可能變了。"
            "第一行 stderr:%s"
            % (len(commands), len(out),
               (p.stderr or "").strip().splitlines()[:1]))
    return list(zip(commands, out))


def smoke(exe, tmpdir):
    """開跑前確認 exe 真的能執行。擋住就整份失敗,不要跑五十幾次才發現。"""
    r = run_scene(exe, os.path.join(ROOT, SMOKE_SCENE), tmpdir)
    if r["rc"] != 0 or not r["svg"]:
        raise RenderError(
            "smoke run 失敗(%s):rc=%d\n%s"
            % (SMOKE_SCENE, r["rc"], (r["err"] or "")[:300]))
    crop_bottom(r["svg"])          # 版面假設也在這裡先驗一次
    return True


def crop_bottom(svg):
    """回傳 (仰視 viewBox, 完整 viewBox, 去掉 <style> 的 SVG 內文)。"""
    gs = list(_G.finditer(svg))
    if len(gs) != 3 or "仰視圖" not in gs[2].group(7):
        raise RenderError(
            "SVG 版面與預期不符(找到 %d 個視圖,第三個標題 %r)——"
            "emit_svg_three_views 可能改了,裁切邏輯要跟著改。"
            % (len(gs), gs[2].group(7) if len(gs) > 2 else None))

    tx, ty, x, y, w, h = (int(gs[2].group(i)) for i in range(1, 7))
    crop = "%d %d %d %d" % (tx + x, ty + y, w, h)

    m = re.search(r'<svg[^>]*viewBox="([^"]+)"[^>]*>', svg)
    if not m:
        raise RenderError("SVG 沒有 viewBox,無法裁切")
    full = m.group(1)

    # 只取 <svg> 裡面的內容。把整個 <svg …> 一起帶進去會變成巢狀 SVG,
    # 內層的 viewBox 會把外層的裁切整個蓋掉——圖看起來仍是三視圖。
    end = svg.rfind("</svg>")
    if end < 0:
        raise RenderError("SVG 沒有結尾標籤")
    body = svg[m.end():end]
    body = _STYLE.sub("", body)
    return crop, full, body.strip()


def bottom_has_surface(svg):
    """仰視圖裡至少要有一片承載面。

    專殺一種假綠燈:場景被截到只剩註解時 parse 仍會成功,
    scene_compute_layout 走空版面分支,產出一張什麼都沒有的白框。
    """
    parts = svg.split('<g transform="translate(')
    if len(parts) < 4:
        return False
    return 'class="surface"' in parts[3]


def _timber_decl_line(lines, tid):
    """找 `timber <id> …` 的宣告行 index,找不到回 -1。"""
    pat = re.compile(r"^\s*timber\s+%d\b" % tid)
    for i, ln in enumerate(lines):
        if pat.match(ln):
            return i
    return -1


def before_failure(exe, scene_path, stderr, tmpdir):
    """拒絕型夾具的「失敗前」重建。

    回傳 (svg or None, note, reason):
      svg    成功時是截斷版的三視圖 SVG
      note   給頁面看的旁白(第幾行之前、是否移除了孤兒 timber)
      reason 失敗時的人話理由;成功時為空字串
    """
    # Revalidation can emit an internal diagnostic such as engineering:0
    # before the parser reports the real scene line. Prefer the exact input
    # path; an internal line zero cannot locate the failed source command.
    m = re.search(re.escape(str(scene_path)) + r":(\d+): ", stderr or "")
    if not m:
        m = next((item for item in _LINE_NO.finditer(stderr or "") if int(item.group(1)) > 0), None)
    if not m:
        return None, "", "錯誤訊息沒有行號(%s),無法決定要截到哪裡" % \
            (stderr or "").strip()[:80]

    n = int(m.group(1))
    if n <= 1:
        return None, "", "違規就在第 1 行,截斷後沒有任何內容可畫"

    src = open(scene_path, "rb").read().decode("utf-8", "replace")
    lines = src.replace("\r\n", "\n").split("\n")
    kept = lines[:n - 1]

    removed = []
    tmp_scene = os.path.join(tmpdir, "_before.scene")

    # I9:砍掉 place 之後,它的 timber 宣告會變成孤兒(EOF 檢查,訊息沒有行號)。
    # 迴圈把孤兒宣告也移掉,並如實記錄移掉了哪幾支。
    for _ in range(len(kept) + 1):
        open(tmp_scene, "wb").write(("\n".join(kept) + "\n").encode("utf-8"))
        r = run_scene(exe, tmp_scene, tmpdir)

        if r["rc"] == 0:
            break

        om = _ORPHAN.search(r["err"] or "")
        if not om:
            return None, "", "截斷版自己也被拒:%s" % \
                (r["err"] or "").strip().splitlines()[0][:120]

        tid = int(om.group(1))
        idx = _timber_decl_line(kept, tid)
        if idx < 0:
            return None, "", "截斷後角材 %d 沒有 place,但找不到它的宣告行" % tid
        kept.pop(idx)
        removed.append(tid)
    else:
        return None, "", "移除孤兒角材宣告的次數超過上限,放棄"

    if not r["svg"]:
        return None, "", "截斷版跑成功但沒有輸出 SVG"

    if not bottom_has_surface(r["svg"]):
        return None, "", "截斷後場景是空的(沒有任何承載面),畫出來會是一張空框"

    note = "失敗前狀態(第 %d 行之前)" % n
    if removed:
        note += ";已移除因截斷而孤立的 timber %s 宣告" % \
            "、".join(str(t) for t in removed)
    return r["svg"], note, ""


# ---------------------------------------------------------------
# 自我檢查:python geometry-guide/axiom_examples.py
# 把 32 個拒絕夾具跑一遍,印出「有圖 / 無法渲染」分類表。
# ---------------------------------------------------------------
def _selftest():
    import ast
    import io

    sys.path.insert(0, HERE)
    import axiom_matrix as am

    ids = [c[0] for c in am.parse_clauses(am.read_text(am.AXIOM))]
    used = sorted({f for v in am.scene_hits(ids).values() for f in v})

    s = io.open(os.path.join(ROOT, "tests", "run_tests.py"),
                encoding="utf-8").read()
    tests = {t["scene"]: t for t in ast.literal_eval(
        re.search(r"TESTS = (\[.*?\n\])\n", s, re.S).group(1))}

    exe = resolve_exe()
    tmp = tempfile.mkdtemp(prefix="axiomdoc_")
    try:
        smoke(exe, tmp)
        print("smoke ok:%s\n" % exe)

        ok_acc = ok_rej = no_rej = 0
        fails = []

        for name in used:
            path = os.path.join(ROOT, name)
            r = run_scene(exe, path, tmp)
            expect = tests[name]["expect"]

            if expect == "accept":
                if r["rc"] == 0 and r["svg"] and bottom_has_surface(r["svg"]):
                    crop_bottom(r["svg"])
                    ok_acc += 1
                else:
                    fails.append((name, "accept 卻沒產出可用的圖"))
                continue

            if r["rc"] == 0:
                fails.append((name, "TESTS 標 reject 但實際 rc=0"))
                continue

            svg, note, why = before_failure(exe, path, r["err"], tmp)
            if svg:
                crop_bottom(svg)
                ok_rej += 1
                print("  有圖   %-34s %s" % (name, note))
            else:
                no_rej += 1
                print("  無法   %-34s %s" % (name, why))

        print("\n接受有圖 %d / 拒絕有圖 %d / 拒絕無法渲染 %d / 異常 %d"
              % (ok_acc, ok_rej, no_rej, len(fails)))
        for n, w in fails:
            print("  異常 %s:%s" % (n, w))
        return 1 if fails else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(_selftest())
    except RenderError as exc:
        print("FAIL:%s" % exc)
        sys.exit(2)
