# -*- coding: utf-8 -*-
"""產生公理層閱讀器:`geometry-guide/公理層-閱讀器.html`。

為什麼只做這件事,不做通用閱讀器:
  實測過這份檔案並不密——63 條條文、65 次交叉引用,平均每條 1.0 次,
  零懸空引用。真正難讀的是**樞紐**:R6 被引用 6 次、I19 與 I22 各 5 次、
  R3 與 I8 各 4 次、D9 3 次,這六條吃掉 65 次引用裡的 27 次。
  讀 R21 的時候要同時記住 R6 的 (b)(c)(d)(e) 四款加 I19 加 D18,
  那才是腦袋裝不下的地方。所以這個閱讀器只解三件事:

  1. 交叉引用就地展開,而且 `R6(d)` 只給 (d) 那一款,不是整條 R6。
  2. 反向引用:這條被誰引用,改它會波及哪裡。
  3. 三向連結:條文住在哪個函式、哪些夾具釘它、哪些變異殺得死它
     (資料直接取自 axiom_matrix.py,不另外維護一份)。

紀律與 make_guide.py 相同:**產生出來的,不是手寫的**。
公理層是 SSOT,這頁只是觀察者,絕不寫回。會過期的閱讀器比沒有更糟。

用法:
  python geometry-guide/make_axiom_reader.py
"""
import html
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import axiom_matrix as am                                    # noqa: E402

OUT = os.path.join(HERE, "公理層-閱讀器.html")
SECTION_OF = {"D": "定義（公理）", "I": "構造保證的不變量", "R": "推演規則"}


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

    intro = "\n".join(body_lines[:marks[0][0]]).strip()
    subs = []
    for k, (start, letter, indent) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(body_lines)
        # 後記:最後一段裡縮排比子項淺的行
        chunk = body_lines[start:end]
        if k + 1 == len(marks):
            cut = len(chunk)
            for j in range(1, len(chunk)):
                lead = len(chunk[j]) - len(chunk[j].lstrip())
                if chunk[j].strip() and lead <= indent:
                    cut = j
                    break
            outro = "\n".join(chunk[cut:]).strip()
            chunk = chunk[:cut]
        subs.append((letter, "\n".join(chunk).strip()))

    return intro, subs, outro if len(marks) else ""


def render_inline(text, known):
    """條文內文 → HTML。行結構有意義,原樣保留;引用變成可展開的 chip。"""
    out = html.escape(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", out)

    def link(m):
        cid, sub = m.group(1), m.group(2) or ""
        if cid not in known:
            return m.group(0)
        key = cid + sub
        return ('<a class="ref" href="#c-%s" data-ref="%s">%s</a>'
                % (cid, html.escape(key), html.escape(cid + sub)))

    return re.sub(r"\b(D\d+[a-z]?|I\d+|R\d+)(\([a-z]\))?", link, out)


def main():
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
                continue
            incoming[tgt].add(cid)

    if dangling:
        sys.exit("有懸空引用,先修公理層:%s" % dangling[:5])

    data = {}
    cards = []
    index = {"D": [], "I": [], "R": []}

    for cid, line, head, body in clauses:
        body_lines = body.split("\n")
        intro, subs, outro = split_subitems(body_lines[1:])
        first = body_lines[0]

        has_code = bool(code[cid])
        has_fix = bool(scenes[cid])
        light = "green" if (has_code and has_fix) else \
                ("yellow" if (has_code or has_fix) else "red")
        hub = len(incoming[cid]) >= 3

        # 給 popover 用的資料:整條 + 每個子項
        data[cid] = {"head": head, "text": body.strip()}
        for letter, txt in subs:
            data[cid + "(" + letter + ")"] = {
                "head": "%s(%s)" % (head, letter), "text": txt}

        fns = sorted({f for f, _ in code[cid]})
        foot = []
        if fns:
            foot.append("<div><span class=k>原始碼</span>" + " ".join(
                '<code>%s</code>' % html.escape(f) for f in fns[:6]) + "</div>")
        if scenes[cid]:
            foot.append("<div><span class=k>夾具</span>" + " ".join(
                '<code>%s</code>' % html.escape(s.replace(".scene", ""))
                for s in scenes[cid][:10]) + "</div>")
        if mutants[cid]:
            foot.append("<div><span class=k>變異</span>" + " ".join(
                '<code>%s</code>' % m for m in mutants[cid]) + "</div>")
        if not foot:
            foot.append('<div class="warn">沒有任何可追溯的連結——'
                        '這不代表沒被測到,代表沒人寫下條號。</div>')

        back = ""
        if incoming[cid]:
            back = ('<div class=back><span class=k>被引用</span>' + " ".join(
                '<a class="ref" href="#c-%s" data-ref="%s">%s</a>'
                % (o, o, o) for o in sorted(incoming[cid])) + "</div>")

        cards.append(
            '<article class="card %s" id="c-%s">'
            '<h3>%s<span class="cid">%s</span>%s'
            '<span class="ln">公理層.md:%d</span></h3>'
            '<div class=body>%s</div>%s'
            '<details class=trace><summary>三向連結</summary>%s</details>'
            '</article>'
            % (light, cid,
               html.escape(head) or cid, cid,
               '<span class="hub" title="樞紐:被 %d 條引用">樞紐</span>'
               % len(incoming[cid]) if hub else "",
               line,
               render_inline(body.strip(), known),
               back, "".join(foot)))

        index[cid[0]].append(
            '<a href="#c-%s" class="%s" data-q="%s">'
            '<span class=cid>%s</span>%s</a>'
            % (cid, light, html.escape((cid + " " + head).lower()),
               cid, html.escape(head)))

    nav = "".join(
        '<div class=grp><h4>%s</h4>%s</div>' % (SECTION_OF[k], "".join(index[k]))
        for k in ("D", "I", "R"))

    green = sum(1 for c in ids if code[c] and scenes[c])
    red = sum(1 for c in ids if not code[c] and not scenes[c])

    page = TEMPLATE.replace("__NAV__", nav) \
                   .replace("__CARDS__", "".join(cards)) \
                   .replace("__DATA__", json.dumps(data, ensure_ascii=False)) \
                   .replace("__STATS__", "%d 條條文・%d 次交叉引用・綠 %d／紅 %d"
                            % (len(ids), sum(len(v) for v in incoming.values()),
                               green, red))

    io.open(OUT, "w", encoding="utf-8", newline="\n").write(page)
    print("已輸出:%s(%d 條條文,%d bytes)" % (OUT, len(ids), len(page)))
    return 0


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>公理層閱讀器</title>
<style>
:root{--bg:#fbfbfa;--fg:#1a1a18;--dim:#6b6b66;--line:#e2e1dd;--card:#fff;
--g:#2f855a;--y:#b7791f;--r:#c53030;--acc:#2b6cb0;--hi:#fff6d8}
@media(prefers-color-scheme:dark){:root{--bg:#16171a;--fg:#e6e6e3;--dim:#9a9a94;
--line:#2c2e33;--card:#1d1f23;--g:#68d391;--y:#f6ad55;--r:#fc8181;--acc:#90cdf4;--hi:#3a3520}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.75 "Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);
padding:10px 18px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
header h1{font-size:15px;margin:0;font-weight:700}
header .stats{color:var(--dim);font-size:12.5px}
#q{margin-left:auto;padding:6px 10px;border:1px solid var(--line);border-radius:7px;
background:var(--card);color:var(--fg);font:inherit;font-size:13px;width:200px}
.wrap{display:grid;grid-template-columns:232px 1fr;gap:22px;
max-width:1180px;margin:0 auto;padding:18px}
nav{position:sticky;top:56px;align-self:start;max-height:calc(100vh - 76px);overflow:auto}
nav .grp h4{margin:14px 0 6px;font-size:11.5px;color:var(--dim);letter-spacing:.06em}
nav a{display:block;padding:2px 7px;border-radius:5px;text-decoration:none;color:var(--fg);
font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border-left:3px solid transparent}
nav a:hover{background:var(--card)}
nav a.green{border-left-color:var(--g)}nav a.yellow{border-left-color:var(--y)}
nav a.red{border-left-color:var(--r)}
nav a .cid{color:var(--dim);margin-right:6px;font-variant-numeric:tabular-nums}
.card{background:var(--card);border:1px solid var(--line);border-left-width:3px;
border-radius:9px;padding:14px 16px;margin:0 0 14px}
.card.green{border-left-color:var(--g)}.card.yellow{border-left-color:var(--y)}
.card.red{border-left-color:var(--r)}
.card:target{box-shadow:0 0 0 2px var(--acc)}
.card h3{margin:0 0 9px;font-size:14.5px;display:flex;gap:9px;align-items:baseline;flex-wrap:wrap}
.card h3 .cid{color:var(--dim);font-weight:600;font-size:12.5px}
.card h3 .ln{margin-left:auto;color:var(--dim);font-size:11.5px;font-weight:400}
.hub{background:var(--acc);color:var(--bg);font-size:10.5px;padding:1px 6px;border-radius:9px}
.body{white-space:pre-wrap;font-size:14px}
code{font:12.8px/1.5 ui-monospace,Consolas,monospace;background:var(--bg);
padding:1px 5px;border-radius:4px}
a.ref{color:var(--acc);text-decoration:none;border-bottom:1px dashed var(--acc);cursor:help}
.back{margin-top:10px;font-size:12.5px;color:var(--dim);display:flex;gap:7px;flex-wrap:wrap}
.k{color:var(--dim);font-size:11.5px;margin-right:7px}
.trace{margin-top:10px;border-top:1px solid var(--line);padding-top:8px}
.trace summary{cursor:pointer;color:var(--dim);font-size:12.5px}
.trace>div{margin:7px 0;font-size:12.5px}
.warn{color:var(--y)}
#pop{position:absolute;z-index:20;max-width:560px;background:var(--card);
border:1px solid var(--acc);border-radius:9px;padding:11px 13px;display:none;
box-shadow:0 10px 30px rgba(0,0,0,.22);white-space:pre-wrap;font-size:13px}
#pop b.h{display:block;color:var(--acc);margin-bottom:6px;font-size:12px}
.flash{animation:f 1.4s}@keyframes f{from{background:var(--hi)}to{background:transparent}}
@media(max-width:820px){.wrap{grid-template-columns:1fr}nav{position:static;max-height:none}}
</style></head><body>
<header><h1>公理層閱讀器</h1><span class="stats">__STATS__</span>
<input id="q" placeholder="搜尋條號或標題"></header>
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
  const top = r.bottom + scrollY + 7;
  let left = r.left + scrollX;
  left = Math.min(left, scrollX + innerWidth - pop.offsetWidth - 14);
  pop.style.top = top + 'px'; pop.style.left = Math.max(8, left) + 'px';
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
    sys.exit(main())
