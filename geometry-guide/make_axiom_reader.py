# -*- coding: utf-8 -*-
"""產生公理層閱讀器:`geometry-guide/公理層-閱讀器.html`。

v1 解的是「交叉引用要在腦袋裡同時記住好幾條」:
  實測過這份檔案並不密——63 條條文、65 次交叉引用,平均每條 1.0 次,
  零懸空引用。真正難讀的是**樞紐**:R6 被引用 6 次、I19 與 I22 各 5 次、
  R3 與 I8 各 4 次、D9 3 次,這六條吃掉 65 次引用裡的 27 次。
  讀 R21 的時候要同時記住 R6 的 (b)(c)(d)(e) 四款加 I19 加 D18。

v2 加的是「光看條文還是不懂它在講什麼」:
  1. **每條附真實範例**。範例來源是既有的 `*.scene` 夾具,不是手寫散文——
     夾具是真的跑過的測試,有明確的接受/拒絕與長度數字,永遠不會跟實作漂移。
     接受型直接渲染平面圖;拒絕型把場景截到違規行之前重建「失敗前」的配置。
     做不到就明講「無法單獨渲染」,不拿空框充數(見 axiom_examples.py)。
  2. **白話旁白**。放在可審的 `公理層-白話.md`,顯示時明標「白話,非條文」。
     公理層.md 是 SSOT,這裡只讀不寫回。
  3. 沒有夾具的條文老實標「尚無範例」,不硬湊。

紀律與 make_guide.py 相同:**產生出來的,不是手寫的**。
會過期的閱讀器比沒有更糟,所以解析不到 60 條條文、發現懸空引用、
白話出現公理層沒有的條號,一律非 0 退出。

GEO-113 之後,63 條全部都有範例。其中三條(R1 拾取、R4 dump 往返、R5 拖曳)
的行為根本不在場景 DSL 裡——SCENE_COMMANDS 沒有 pick / dump / drag,
所以它們的範例改用 web bridge 實錄:真的把 bridge 跑起來,
把送出去的指令與收回來的原文貼上(見 axiom_transcripts.py)。

用法:
  python geometry-guide/make_axiom_reader.py              # 含範例圖與實錄
  python geometry-guide/make_axiom_reader.py --no-render   # 不跑 exe,無圖版
  python geometry-guide/make_axiom_reader.py --no-bridge   # 不跑 bridge,無實錄版
  GEO_EXE=/tmp/cg GEO_BRIDGE=/tmp/wb python geometry-guide/make_axiom_reader.py
"""
import ast
import html
import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import axiom_matrix as am                                    # noqa: E402
import axiom_examples as ax                                  # noqa: E402
import axiom_transcripts as tr                               # noqa: E402

ROOT = am.ROOT
# 2026-09-18:正典閱讀器是「批註版」(公理層-閱讀器.html),由批註工具產生、
# 使用者批註後逐版取代。本腳本**不得**再覆寫那個路徑,否則會把正典蓋回舊版面。
# 它現在只產覆蓋率/追溯用的診斷頁,檔名另立。規則見 repo 根目錄 AGENTS.md。
OUT = os.path.join(HERE, "公理層-追溯診斷頁.html")

# 🔴 寫檔閘門(2026-09-20):AGENTS.md 記載過一場事故——同一專案一度同時存在 5 份「公理層閱讀器」,
# 使用者無法分辨哪一份是真的。本腳本產的是**追溯診斷頁,不是正典**,但它只要一跑就會在 repo 裡
# 生出第二份看起來像閱讀器的檔案。文字規則擋不住誤跑,所以改成機制:
#   預設寫到系統暫存目錄;要寫進 repo 必須明示 --in-repo,而且正典存在時一律拒絕。
def resolve_out(argv):
    import tempfile
    if "--out" in argv:
        return argv[argv.index("--out") + 1]
    if "--in-repo" in argv:
        canonical = os.path.join(HERE, "公理層-閱讀器.html")
        if os.path.exists(canonical):
            raise SystemExit(
                "拒絕寫入 repo:正典 %s 已存在。\n"
                "本腳本產的是追溯診斷頁,不是正典(見 AGENTS.md 🔴);\n"
                "要改正典請用 geometry-guide/sync_axiom_reader.py。\n"
                "只是想看診斷頁就別加 --in-repo,會寫到暫存目錄。" % canonical)
        return OUT
    return os.path.join(tempfile.gettempdir(), "公理層-追溯診斷頁.html")
PLAIN = os.path.join(HERE, "公理層-白話.md")
SECTION_OF = {"D": "定義（公理）", "I": "構造保證的不變量", "R": "推演規則"}


# ------------------------------------------------------------------
# 條文與子項
# ------------------------------------------------------------------
def split_subitems(body_lines):
    """把條文切成 (前言, [(字母, 文字)], 後記)。

    子項長這樣:`   (a) 切點 = …`,續行縮更深。後記是最後一個子項之後
    又回到條文層級的說明(例如 I23 結尾那句「幾何本身由 R6(e) 的凍結保護」)。
    """
    marks = []
    for i, ln in enumerate(body_lines):
        m = re.match(r"^(\s+)\(([a-z])\)\s", ln)
        if m:
            marks.append((i, m.group(2), len(m.group(1))))

    if not marks:
        return "\n".join(body_lines).strip(), [], ""

    subs = []
    for k, (start, letter, indent) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(body_lines)
        chunk = body_lines[start:end]
        if k + 1 == len(marks):
            cut = len(chunk)
            for j in range(1, len(chunk)):
                lead = len(chunk[j]) - len(chunk[j].lstrip())
                if chunk[j].strip() and lead <= indent:
                    cut = j
                    break
            chunk = chunk[:cut]
        subs.append((letter, "\n".join(chunk).strip()))

    return "", subs, ""


def render_inline(text, known, link=True):
    """條文內文 → HTML。行結構有意義,原樣保留。

    link=False 時條號不做成 chip——白話裡的條號是純文字,做成連結會讓人
    以為那是條文的一部分。
    """
    out = html.escape(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", out)

    if not link:
        return out

    def rep(m):
        cid, sub = m.group(1), m.group(2) or ""
        if cid not in known:
            return m.group(0)
        return ('<a class="ref" href="#c-%s" data-ref="%s">%s</a>'
                % (cid, html.escape(cid + sub), html.escape(cid + sub)))

    return re.sub(r"\b(D\d+[a-z]?|I\d+|R\d+)(\([a-z]\))?", rep, out)


# ------------------------------------------------------------------
# 白話附檔
# ------------------------------------------------------------------
def parse_plain(known):
    """讀 公理層-白話.md。檔案不在就回空 dict(不炸);出現公理層沒有的條號就停手。"""
    if not os.path.exists(PLAIN):
        return {}

    text = io.open(PLAIN, encoding="utf-8").read()
    out = {}
    cur = None
    buf = []

    for ln in text.split("\n"):
        m = re.match(r"^## ([DIR]\d+[a-z]?)\s*$", ln)
        if m:
            if cur:
                out[cur] = "\n".join(buf).strip()
            cur = m.group(1)
            buf = []
        elif cur is not None:
            buf.append(ln)
    if cur:
        out[cur] = "\n".join(buf).strip()

    unknown = sorted(set(out) - set(known))
    if unknown:
        sys.exit("公理層-白話.md 有公理層不存在的條號:%s\n"
                 "白話追不上條文的重構就是過期,先修白話再產。" % unknown)

    return {k: v for k, v in out.items() if v}


# ------------------------------------------------------------------
# 夾具:旁白、DSL、預期結果
# ------------------------------------------------------------------
def load_tests():
    s = io.open(os.path.join(ROOT, "tests", "run_tests.py"),
                encoding="utf-8").read()
    m = re.search(r"TESTS = (\[.*?\n\])\n", s, re.S)
    if not m:
        sys.exit("讀不到 tests/run_tests.py 的 TESTS,格式可能變了")
    return {t["scene"]: t for t in ast.literal_eval(m.group(1))}


def split_scene(name):
    """回傳 (旁白行, DSL 行)。檔頭連續的 # 區塊是旁白,原樣呈現不改寫。"""
    raw = open(os.path.join(ROOT, name), "rb").read().decode("utf-8", "replace")
    lines = raw.replace("\r\n", "\n").rstrip("\n").split("\n")

    gist = []
    i = 0
    while i < len(lines) and (lines[i].lstrip().startswith("#") or
                              not lines[i].strip()):
        if lines[i].lstrip().startswith("#"):
            t = lines[i].lstrip()[1:].strip()
            # 跳過分隔線那種沒有內容的註解(例如 ==== 或 ----)
            if t and t.strip("=-—─ *"):
                gist.append(t)
        i += 1
    return gist, lines


def expect_text(spec):
    if spec["expect"] == "accept":
        bits = ["接受"]
        if spec.get("lengths"):
            bits.append("長度 " + "、".join(str(x) for x in spec["lengths"]))
        if spec.get("contains"):
            bits.append("輸出含「%s」" % spec["contains"][0])
        return " · ".join(bits)
    return "拒絕 · 訊息含「%s」" % spec.get("error", "")


# ------------------------------------------------------------------
# 範例區塊
# ------------------------------------------------------------------
def build_transcript(entry):
    """web bridge 實錄的 HTML。entry 來自 axiom_transcripts.build_all()。

    R1 / R4 / R5 的行為不在場景 DSL 裡(SCENE_COMMANDS 沒有 pick/dump/drag),
    所以這三條的範例是真的把 bridge 跑起來、把來回原文收下來貼上。
    """
    if entry.get("error"):
        return ('<section class="ex-wrap"><h4>實錄</h4>'
                '<details class="ex tr trbad" open><summary>'
                '<span class="badge">實錄失敗</span><code>web bridge</code>'
                '<span class="gist">這條的範例沒有產生出來</span></summary>'
                '<div class="tr-body"><div class="tr-why">%s</div></div>'
                '</details></section>' % html.escape(entry["error"]))

    steps = []
    for cmd, resp, note in entry["steps"]:
        out = ('<pre class="io out"><b>回應</b>%s</pre>'
               % html.escape(resp)) if resp else ""
        steps.append('<div class="step"><pre class="io"><b>送出</b>%s</pre>%s'
                     '<p class="note">%s</p></div>'
                     % (html.escape(cmd), out, html.escape(note)))

    bad = "" if entry["ok"] else " trbad"
    why = ("" if entry["ok"] else
           '<div class="tr-why">斷言不成立:%s</div>'
           % html.escape(entry["why"]))

    return ('<section class="ex-wrap"><h4>實錄 <span class="n">1</span></h4>'
            '<details class="ex tr%s" open><summary>'
            '<span class="badge">實錄</span><code>web bridge</code>'
            '<span class="gist">%s</span></summary>'
            '<div class="tr-body">%s%s<div class="expect">預期:%s</div></div>'
            '</details></section>'
            % (bad, html.escape(entry["title"]), "".join(steps), why,
               html.escape(entry["expect"])))


def build_examples(scenes, tests, rendered, has_transcript=False):
    """單一條文的範例 HTML。rendered[name] = dict(svg, crop, full, note, why)。"""
    if not scenes:
        if has_transcript:
            return ""       # 這條的範例是實錄,不是夾具,別再說「尚無範例」
        # GEO-113 之後 63 條都有範例,正常情況下這段不會被用到。
        # 留著是為了「之後新增條文卻忘了補夾具」時會在頁面上大聲說出來。
        return ('<div class="no-ex">尚無範例——這條還沒有夾具指名它。'
                '注意這不等於「沒被測到」,可能只是沒有夾具寫下條號。'
                '正確做法是逐條判斷:真的缺覆蓋就寫新夾具,'
                '已有覆蓋只是沒標就在夾具檔頭補上條號。不在這頁硬湊。</div>')

    cards = []
    for k, name in enumerate(sorted(scenes)):
        spec = tests.get(name)
        if spec is None:
            continue
        gist, lines = split_scene(name)
        r = rendered.get(name, {})
        acc = spec["expect"] == "accept"

        # 違規行:拒絕型從 note 裡的行號推回去(note 形如「失敗前狀態(第 9 行之前)」)
        bad = -1
        if not acc:
            m = re.search(r"第 (\d+) 行之前", r.get("note", ""))
            if m:
                bad = int(m.group(1))

        dsl = []
        for i, ln in enumerate(lines, 1):
            cls = " class=hit" if i == bad else ""
            dsl.append('<span%s><i>%3d</i>%s</span>'
                       % (cls, i, html.escape(ln) or "&nbsp;"))

        if r.get("svg"):
            fig = ('<figure><svg viewBox="%s" data-full="%s" '
                   'preserveAspectRatio="xMidYMid meet">%s</svg>'
                   '<figcaption><button class="v3" type="button">三視圖</button>'
                   '%s</figcaption></figure>'
                   % (r["crop"], r["full"], r["svg"],
                      ('<span class=note>%s</span>' % html.escape(r["note"]))
                      if r.get("note") else ""))
        else:
            why = r.get("why") or "未渲染"
            fig = ('<figure class="nofig"><div class="nofig-box">'
                   '失敗前狀態無法單獨渲染</div>'
                   '<figcaption><span class=note>%s</span></figcaption>'
                   '</figure>' % html.escape(why))

        cards.append(
            '<details class="ex %s"%s>'
            '<summary><span class="badge">%s</span>'
            '<code>%s</code><span class="gist">%s</span></summary>'
            '<div class="ex-body">%s'
            '<div class="ex-side"><pre class="dsl">%s</pre>'
            '<div class="expect">預期:%s</div></div></div></details>'
            % ("ok" if acc else "no",
               " open" if k == 0 else "",
               "接受" if acc else "拒絕",
               html.escape(name.replace(".scene", "")),
               html.escape(gist[0] if gist else ""),
               # <pre> 會把 span 之間的換行也算成一行,所以不能用換行串接
               fig, "".join(dsl), html.escape(expect_text(spec))))

    return ('<section class="ex-wrap"><h4>範例 <span class="n">%d</span>'
            '<button class="ex-all" type="button">全部展開</button></h4>%s</section>'
            % (len(cards), "".join(cards)))


# ------------------------------------------------------------------
def main():
    no_render = "--no-render" in sys.argv
    no_bridge = "--no-bridge" in sys.argv

    axiom = am.read_text(am.AXIOM)
    src = am.read_text(am.SRC)
    clauses = am.parse_clauses(axiom)
    ids = [c[0] for c in clauses]
    known = set(ids)

    if len(clauses) < 60:
        sys.exit("只解析到 %d 條條文,格式可能變了,停手" % len(clauses))

    code = am.code_sites(src, ids)
    scenes = am.scene_hits(ids)
    mutants = am.mutant_hits(ids)
    plain = parse_plain(known)
    tests = load_tests()

    # 交叉引用(含反向)
    ref_re = re.compile(r"\b(D\d+[a-z]?|I\d+|R\d+)(\([a-z]\))?")
    incoming = {c: set() for c in ids}
    dangling = []
    for cid, _, _, body in clauses:
        for m in ref_re.finditer(body):
            tgt = m.group(1)
            if tgt == cid:
                continue
            if tgt not in known:
                dangling.append((cid, m.group(0)))
            else:
                incoming[tgt].add(cid)
    if dangling:
        sys.exit("有懸空引用,先修公理層:%s" % dangling[:5])

    # ---- 渲染 ----
    used = sorted({f for v in scenes.values() for f in v})
    rendered = {}
    fails = []

    if no_render:
        for n in used:
            rendered[n] = {"why": "未渲染(--no-render)"}
    else:
        exe = ax.resolve_exe()
        tmp = tempfile.mkdtemp(prefix="axiomdoc_")
        try:
            ax.smoke(exe, tmp)
            for i, name in enumerate(used, 1):
                sys.stdout.write("\r  渲染 %d/%d %-36s" % (i, len(used), name))
                sys.stdout.flush()
                path = os.path.join(ROOT, name)
                r = ax.run_scene(exe, path, tmp)
                spec = tests.get(name, {})

                if spec.get("expect") == "accept":
                    if r["rc"] == 0 and r["svg"] and ax.bottom_has_surface(r["svg"]):
                        crop, full, body = ax.crop_bottom(r["svg"])
                        rendered[name] = {"svg": body, "crop": crop,
                                          "full": full, "note": ""}
                    else:
                        rendered[name] = {"why": "渲染失敗:rc=%d %s"
                                          % (r["rc"], (r["err"] or "")[:100])}
                        fails.append(name)
                    continue

                svg, note, why = ax.before_failure(exe, path, r["err"], tmp)
                if svg:
                    crop, full, body = ax.crop_bottom(svg)
                    rendered[name] = {"svg": body, "crop": crop,
                                      "full": full, "note": note}
                else:
                    rendered[name] = {"why": why}
            sys.stdout.write("\r" + " " * 60 + "\r")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    pics = sum(1 for v in rendered.values() if v.get("svg"))

    # ---- web bridge 實錄(R1 / R4 / R5)----
    # 這三條的行為不在場景 DSL 裡,只有 bridge 的 pick / dump / drag 看得到。
    # bridge 建不起來或被 SAC 擋:頁面照樣產生(那三條標紅說明原因),
    # 但 main() 回非 0,不讓它靜悄悄地缺三條。
    trans = {}
    if no_bridge:
        for cid in tr.TRANSCRIPTS:
            title = tr.TRANSCRIPTS[cid][0]
            trans[cid] = {"title": title, "error": "未實錄(--no-bridge)"}
    else:
        tmp = tempfile.mkdtemp(prefix="axiomtrans_")
        try:
            trans = tr.build_all(ax.resolve_bridge(), tmp)
        except ax.RenderError as exc:
            for cid, (title, _) in tr.TRANSCRIPTS.items():
                trans[cid] = {"title": title, "error": str(exc)}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    trans_bad = [c for c, v in trans.items()
                 if v.get("error") or not v.get("ok")]

    # ---- 卡片 ----
    data = {}
    cards = []
    index = {"D": [], "I": [], "R": []}

    for cid, line, head, body in clauses:
        body_lines = body.split("\n")
        _, subs, _ = split_subitems(body_lines[1:])

        light = ("green" if (code[cid] and scenes[cid])
                 else ("yellow" if (code[cid] or scenes[cid]) else "red"))
        hub = len(incoming[cid]) >= 3

        data[cid] = {"head": head, "text": body.strip()}
        for letter, txt in subs:
            data["%s(%s)" % (cid, letter)] = {
                "head": "%s(%s)" % (head, letter), "text": txt}

        fns = sorted({f for f, _ in code[cid]})
        foot = []
        if fns:
            foot.append("<div><span class=k>原始碼</span>" + " ".join(
                "<code>%s</code>" % html.escape(f) for f in fns[:6]) + "</div>")
        if scenes[cid]:
            foot.append("<div><span class=k>夾具</span>" + " ".join(
                "<code>%s</code>" % html.escape(s.replace(".scene", ""))
                for s in scenes[cid][:12]) + "</div>")
        if mutants[cid]:
            foot.append("<div><span class=k>變異</span>" + " ".join(
                "<code>%s</code>" % m for m in mutants[cid]) + "</div>")
        if not foot:
            foot.append('<div class="warn">沒有任何可追溯的連結——'
                        '這不代表沒被測到,代表沒人寫下條號。</div>')

        back = ""
        if incoming[cid]:
            back = ('<div class=back><span class=k>被引用</span>' + " ".join(
                '<a class="ref" href="#c-%s" data-ref="%s">%s</a>'
                % (o, o, o) for o in sorted(incoming[cid])) + "</div>")

        pl = plain.get(cid)
        plain_html = ('<div class="plain"><span class="tag">白話,非條文</span>'
                      '<div class="pbody">%s</div></div>'
                      % render_inline(pl, known, link=False)) if pl else \
                     '<div class="plain none">(尚無白話)</div>'

        cards.append(
            '<article class="card %s" id="c-%s">'
            '<h3>%s<span class="cid">%s</span>%s'
            '<span class="ln">公理層.md:%d</span></h3>'
            '<div class=body>%s</div>%s%s%s'
            '<details class=trace><summary>三向連結</summary>%s</details>'
            '</article>'
            % (light, cid, html.escape(head) or cid, cid,
               ('<span class="hub" title="樞紐:被 %d 條引用">樞紐</span>'
                % len(incoming[cid])) if hub else "",
               line, render_inline(body.strip(), known), plain_html, back,
               build_examples(scenes[cid], tests, rendered, cid in trans)
               + (build_transcript(trans[cid]) if cid in trans else ""),
               "".join(foot)))

        index[cid[0]].append(
            '<a href="#c-%s" class="%s" data-q="%s">'
            '<span class=cid>%s</span>%s</a>'
            % (cid, light, html.escape((cid + " " + head).lower()), cid,
               html.escape(head)))

    nav = "".join('<div class=grp><h4>%s</h4>%s</div>'
                  % (SECTION_OF[k], "".join(index[k])) for k in "DIR")

    bits = []
    if no_render:
        bits.append("本頁未含任何範例圖(--no-render)")
    elif fails:
        bits.append("有 %d 個範例渲染失敗,該區塊會標明原因" % len(fails))
    if trans_bad:
        bits.append("web bridge 實錄有 %d 條沒有產生(%s)"
                    % (len(trans_bad), "、".join(sorted(trans_bad))))
    banner = ('<div class="banner">%s。</div>' % "；".join(bits)) if bits else ""

    no_ex = sum(1 for c in ids if not scenes[c] and c not in trans)
    stats = ("%d 條條文・%d 次交叉引用・綠 %d／紅 %d・白話 %d/%d・"
             "圖 %d/%d 個夾具・實錄 %d/%d・尚無範例 %d 條"
             % (len(ids), sum(len(v) for v in incoming.values()),
                sum(1 for c in ids if code[c] and scenes[c]),
                sum(1 for c in ids if not code[c] and not scenes[c]),
                len(plain), len(ids), pics, len(used),
                len(trans) - len(trans_bad), len(tr.TRANSCRIPTS), no_ex))

    page = (TEMPLATE.replace("__NAV__", nav)
            .replace("__CARDS__", "".join(cards))
            .replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__BANNER__", banner)
            .replace("__STATS__", stats))

    out = resolve_out(sys.argv)
    io.open(out, "w", encoding="utf-8", newline="\n").write(page)
    print("已輸出:%s" % out)
    if out != OUT:
        print("  (預設寫到暫存目錄;本腳本不是正典閱讀器的產生器,見 AGENTS.md)")
    print("  %s" % stats)
    if fails:
        print("  渲染失敗:%s" % "、".join(fails))
    for cid in sorted(trans_bad):
        print("  實錄未成立 %s:%s"
              % (cid, trans[cid].get("error") or trans[cid].get("why")))
    # --no-bridge 是明講的選擇,跟 --no-render 一樣回 0;
    # 沒明講卻產不出實錄(bridge 找不到、被 SAC 擋、斷言不成立)才回非 0。
    return 1 if (fails or (trans_bad and not no_bridge)) else 0


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>公理層閱讀器</title>
<style>
:root{--bg:#fbfbfa;--fg:#1a1a18;--dim:#6b6b66;--line:#e2e1dd;--card:#fff;
--g:#2f855a;--y:#b7791f;--r:#c53030;--acc:#2b6cb0;--hi:#fff6d8;--plain:#f4f1e8}
@media(prefers-color-scheme:dark){:root{--bg:#16171a;--fg:#e6e6e3;--dim:#9a9a94;
--line:#2c2e33;--card:#1d1f23;--g:#68d391;--y:#f6ad55;--r:#fc8181;--acc:#90cdf4;
--hi:#3a3520;--plain:#22242a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.75 "Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--bg);
border-bottom:1px solid var(--line);padding:10px 18px;display:flex;gap:14px;
align-items:center;flex-wrap:wrap}
header h1{font-size:15px;margin:0;font-weight:700}
header .stats{color:var(--dim);font-size:12.5px}
#q{margin-left:auto;padding:6px 10px;border:1px solid var(--line);border-radius:7px;
background:var(--card);color:var(--fg);font:inherit;font-size:13px;width:200px}
.banner{background:var(--r);color:#fff;padding:7px 18px;font-size:13px}
.wrap{display:grid;grid-template-columns:232px 1fr;gap:22px;
max-width:1180px;margin:0 auto;padding:18px}
nav{position:sticky;top:56px;align-self:start;max-height:calc(100vh - 76px);overflow:auto}
nav .grp h4{margin:14px 0 6px;font-size:11.5px;color:var(--dim);letter-spacing:.06em}
nav a{display:block;padding:2px 7px;border-radius:5px;text-decoration:none;
color:var(--fg);font-size:12.5px;white-space:nowrap;overflow:hidden;
text-overflow:ellipsis;border-left:3px solid transparent}
nav a:hover{background:var(--card)}
nav a.green{border-left-color:var(--g)}nav a.yellow{border-left-color:var(--y)}
nav a.red{border-left-color:var(--r)}
nav a .cid{color:var(--dim);margin-right:6px;font-variant-numeric:tabular-nums}
.card{background:var(--card);border:1px solid var(--line);border-left-width:3px;
border-radius:9px;padding:14px 16px;margin:0 0 14px}
.card.green{border-left-color:var(--g)}.card.yellow{border-left-color:var(--y)}
.card.red{border-left-color:var(--r)}
.card:target{box-shadow:0 0 0 2px var(--acc)}
.card h3{margin:0 0 9px;font-size:14.5px;display:flex;gap:9px;align-items:baseline;
flex-wrap:wrap}
.card h3 .cid{color:var(--dim);font-weight:600;font-size:12.5px}
.card h3 .ln{margin-left:auto;color:var(--dim);font-size:11.5px;font-weight:400}
.hub{background:var(--acc);color:var(--bg);font-size:10.5px;padding:1px 6px;
border-radius:9px}
.body{white-space:pre-wrap;font-size:14px}
code{font:12.8px/1.5 ui-monospace,Consolas,monospace;background:var(--bg);
padding:1px 5px;border-radius:4px}
a.ref{color:var(--acc);text-decoration:none;border-bottom:1px dashed var(--acc);
cursor:help}
.plain{margin:11px 0 0;background:var(--plain);border-radius:7px;padding:9px 12px;
font-size:13.5px}
.plain .tag{display:inline-block;font-size:10.5px;color:var(--dim);
border:1px solid var(--line);border-radius:9px;padding:0 7px;margin-bottom:5px}
.plain .pbody{white-space:pre-wrap}
.plain.none{color:var(--dim);font-size:12.5px;background:none;padding:6px 0}
.back{margin-top:10px;font-size:12.5px;color:var(--dim);display:flex;gap:7px;
flex-wrap:wrap}
.k{color:var(--dim);font-size:11.5px;margin-right:7px}
.trace{margin-top:10px;border-top:1px solid var(--line);padding-top:8px}
.trace summary{cursor:pointer;color:var(--dim);font-size:12.5px}
.trace>div{margin:7px 0;font-size:12.5px}
.warn{color:var(--y)}
/* ---- 範例 ---- */
.ex-wrap{margin-top:13px;border-top:1px solid var(--line);padding-top:10px}
.ex-wrap h4{margin:0 0 7px;font-size:12.5px;color:var(--dim);
display:flex;align-items:center;gap:8px}
.ex-wrap h4 .n{background:var(--line);border-radius:9px;padding:0 7px;font-size:11px}
.ex-all,.v3{font:inherit;font-size:11.5px;padding:1px 9px;border-radius:6px;
border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
.ex-all{margin-left:auto}
.no-ex{color:var(--dim);font-size:12.5px;padding:4px 0}
details.ex{border:1px solid var(--line);border-radius:7px;margin:0 0 7px;
overflow:hidden}
details.ex>summary{cursor:pointer;padding:6px 10px;font-size:12.5px;
display:flex;gap:8px;align-items:center;flex-wrap:wrap}
details.ex.ok>summary{border-left:3px solid var(--g)}
details.ex.no>summary{border-left:3px solid var(--r)}
.badge{font-size:10.5px;padding:0 6px;border-radius:9px;border:1px solid var(--line)}
.ex.ok .badge{color:var(--g)}.ex.no .badge{color:var(--r)}
.gist{color:var(--dim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
flex:1;min-width:0}
.ex-body{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);
gap:12px;padding:4px 10px 11px}
.ex-body figure{margin:0}
.ex-body svg{width:100%;height:auto;background:#fff;border:1px solid var(--line);
border-radius:5px}
figcaption{margin-top:5px;font-size:11.5px;color:var(--dim);display:flex;
gap:8px;align-items:center;flex-wrap:wrap}
.nofig-box{border:1px dashed var(--line);border-radius:5px;padding:20px 12px;
text-align:center;color:var(--dim);font-size:12.5px}
pre.dsl{margin:0;background:var(--bg);border:1px solid var(--line);border-radius:5px;
padding:7px 2px 7px 0;font:11.8px/1.65 ui-monospace,Consolas,monospace;
overflow:auto;max-height:290px}
pre.dsl span{display:block;padding:0 8px 0 0}
pre.dsl i{display:inline-block;width:34px;text-align:right;margin-right:9px;
color:var(--dim);font-style:normal;user-select:none}
pre.dsl span.hit{background:var(--hi)}
.expect{margin-top:6px;font-size:11.8px;color:var(--dim)}
/* web bridge 實錄:單欄,沒有圖,內容是真的送出去與收回來的原文 */
details.ex.tr>summary{border-left:3px solid var(--acc)}
.ex.tr .badge{color:var(--acc)}
details.ex.trbad>summary{border-left:3px solid var(--r)}
.tr-body{padding:4px 10px 11px}
.tr-why{color:var(--r);font-size:12.3px;padding:4px 0}
.step{border-top:1px solid var(--line);padding:7px 0 5px}
.step:first-child{border-top:0}
pre.io{margin:0 0 3px;background:var(--bg);border:1px solid var(--line);
border-radius:5px;padding:5px 8px;white-space:pre-wrap;word-break:break-all;
font:11.8px/1.6 ui-monospace,Consolas,monospace}
pre.io b{color:var(--dim);font-weight:400;user-select:none;margin-right:7px}
pre.io.out{background:transparent}
.step .note{margin:2px 0 0;font-size:11.8px;color:var(--dim)}
/* 內嵌 SVG 的樣式:原本是全域選擇器,會汙染卡片,所以 scoped 在這裡 */
.ex-body svg polygon,.ex-body svg line,.ex-body svg rect{vector-effect:non-scaling-stroke}
.ex-body svg .frame{fill:#fff;stroke:#bbb;stroke-width:1px}
.ex-body svg .title{font:bold 150px sans-serif;fill:#222}
.ex-body svg .label{font:110px sans-serif;fill:#333;text-anchor:middle;
dominant-baseline:middle}
.ex-body svg .guide-label{text-anchor:start;fill:#b03030}
.ex-body svg .timber-label{fill:#7a4a00;font-weight:bold}
.ex-body svg .guide-label,.ex-body svg .timber-label{paint-order:stroke;
stroke:#fff;stroke-width:30px;stroke-linejoin:round}
.ex-body svg .surface{fill:#dbe9ff;fill-opacity:.6;stroke:#36c;stroke-width:1.5px}
.ex-body svg .hole{fill:#fff;stroke:#36c;stroke-width:1.5px}
.ex-body svg .edge{stroke:#36c;stroke-width:1.5px}
.ex-body svg .edge-free{stroke:#e08020;stroke-width:1.5px;stroke-dasharray:30 15}
.ex-body svg .guide{stroke:#c33;stroke-width:1px;stroke-dasharray:60 30}
.ex-body svg .timber-face{fill:#ffd27f;fill-opacity:.5;stroke:#a06000;
stroke-width:1.5px}
.ex-body svg .timber-face-near{fill-opacity:.85}
#pop{position:absolute;z-index:20;max-width:560px;background:var(--card);
border:1px solid var(--acc);border-radius:9px;padding:11px 13px;display:none;
box-shadow:0 10px 30px rgba(0,0,0,.22);white-space:pre-wrap;font-size:13px}
#pop b.h{display:block;color:var(--acc);margin-bottom:6px;font-size:12px}
.flash{animation:f 1.4s}@keyframes f{from{background:var(--hi)}to{background:transparent}}
@media(max-width:820px){.wrap{grid-template-columns:1fr}
nav{position:static;max-height:none}
.ex-body{grid-template-columns:1fr}}
</style></head><body>
<header><h1>公理層閱讀器</h1><span class="stats">__STATS__</span>
<input id="q" placeholder="搜尋條號或標題"></header>
__BANNER__
<div class="wrap"><nav>__NAV__</nav><main>__CARDS__</main></div>
<div id="pop"></div>
<script>
const DATA = __DATA__;
const pop = document.getElementById('pop');

function show(a){
  const d = DATA[a.dataset.ref] || DATA[a.dataset.ref.replace(/\\([a-z]\\)$/,'')];
  if(!d) return;
  pop.innerHTML = '<b class="h">' + a.dataset.ref + ' ' + d.head + '</b>' + d.text;
  pop.style.display = 'block';
  const r = a.getBoundingClientRect();
  let left = r.left + scrollX;
  left = Math.min(left, scrollX + innerWidth - pop.offsetWidth - 14);
  pop.style.top = (r.bottom + scrollY + 7) + 'px';
  pop.style.left = Math.max(8, left) + 'px';
}
document.addEventListener('mouseover', e => {
  const a = e.target.closest('a.ref'); if(a) show(a);
});
document.addEventListener('mouseout', e => {
  if(e.target.closest('a.ref') && !e.relatedTarget?.closest('#pop'))
    pop.style.display = 'none';
});
pop.addEventListener('mouseleave', () => pop.style.display = 'none');

document.addEventListener('click', e => {
  const v3 = e.target.closest('button.v3');
  if(v3){
    const svg = v3.closest('figure').querySelector('svg');
    const full = svg.dataset.full, cur = svg.getAttribute('viewBox');
    if(!svg.dataset.crop) svg.dataset.crop = cur;
    const showFull = cur !== full;
    svg.setAttribute('viewBox', showFull ? full : svg.dataset.crop);
    v3.textContent = showFull ? '只看平面' : '三視圖';
    return;
  }
  const all = e.target.closest('button.ex-all');
  if(all){
    const ds = all.closest('.ex-wrap').querySelectorAll('details.ex');
    const open = all.textContent === '全部展開';
    ds.forEach(d => d.open = open);
    all.textContent = open ? '全部收合' : '全部展開';
    return;
  }
  const a = e.target.closest('a.ref'); if(!a) return;
  pop.style.display = 'none';
  const t = document.querySelector(a.getAttribute('href'));
  if(t){ t.classList.remove('flash'); void t.offsetWidth; t.classList.add('flash'); }
});

document.getElementById('q').addEventListener('input', e => {
  const v = e.target.value.trim().toLowerCase();
  document.querySelectorAll('nav a').forEach(a => {
    a.style.display = !v || a.dataset.q.includes(v) ? '' : 'none';
  });
});
</script></body></html>
"""

if __name__ == "__main__":
    try:
        sys.exit(main())
    except ax.RenderError as exc:
        print("FAIL:%s" % exc)
        sys.exit(2)
