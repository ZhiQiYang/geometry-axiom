#!/usr/bin/env python3
"""Rebuild canonical reader content from SSOT while retaining its UI and review history.

Python 3 standard library + Node.js; no network, npm packages or alternate reader.
The existing canonical HTML is the versioned UI/illustration/review template.
Only 公理層-閱讀器.html is ever written. --check validates without writing.
GEO-131 witness figures (geometry-guide/witness/*.svg) are embedded read-only; the
engine is never run here — byte drift of those figures is witness.py --check's job.
--review-json optionally merges an exported axiom-review/v1 review backup.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(HERE))
import axiom_matrix  # 追溯資料的唯一來源(燈號/三向連結/樞紐都由它算)
ROOT = HERE.parent
CANONICAL = HERE / "公理層-閱讀器.html"
AXIOM = ROOT / "公理層.md"
PLAIN = HERE / "公理層-白話.md"
COUNTS_ID = "reader-counts"
# D headings are bold in the SSOT; plain leading D references remain body text.
# Match the established grammar used by axiom_matrix instead of splitting those references.
CLAUSE_START = re.compile(r"^(?:\*\*|(?=[IR]))([DIR]\d+[a-z]?)\s+", re.M)
CLAUSE_REF = re.compile(r"\b([DIR]\d+[a-z]?)(?:\(([a-z])\))?")
SUB_START = re.compile(r"^( +)\(([a-z])\) +", re.M)
GROUPS = {"D": "定義", "I": "不變量", "R": "推演規則"}
WITNESS_DIR = HERE / "witness"
WITNESS_MANIFEST = WITNESS_DIR / "manifest.json"
# 見證圖(GEO-131)嵌入閱讀器時套用的深色配色,與既有歷史例圖相同;引擎自帶的淺色 <style> 被整段替換。
WITNESS_STYLE = (
    "<style>svg{background:#181e24} .frame{fill:#181e24;stroke:none}\n"
    "polygon,line,rect{vector-effect:non-scaling-stroke}\n"
    ".title{font:bold 150px sans-serif;fill:#d7dfe6}\n"
    ".label{font:110px sans-serif;fill:#c5cfd8;text-anchor:middle;dominant-baseline:middle}\n"
    ".guide-label{text-anchor:start;fill:#ed9494}\n"
    ".timber-label{fill:#efba69;font-weight:bold}\n"
    ".guide-label,.timber-label{paint-order:stroke;stroke:#181e24;stroke-width:30px;stroke-linejoin:round}\n"
    ".surface{fill:#304557;fill-opacity:.7;stroke:#84c8f6;stroke-width:1.5px}\n"
    ".hole{fill:#181e24;stroke:#84c8f6;stroke-width:1.5px}\n"
    ".edge{stroke:#84c8f6;stroke-width:1.5px}\n"
    ".edge-free{stroke:#efba69;stroke-width:1.5px;stroke-dasharray:30 15}\n"
    ".guide{stroke:#ed9494;stroke-width:1px;stroke-dasharray:60 30}\n"
    ".timber-face{fill:#edb365;fill-opacity:.5;stroke:#edb365;stroke-width:1.5px}\n"
    ".timber-face-near{fill-opacity:.85}</style>"
)
# GEO-139(4):追溯燈號 / 三向連結 / 樞紐徽章。GEO-120 的連帶約束明列這三項「不得丟失」,
# 改用批註版正典時整組掉了(全檔 grep 為 0)。**判準寫在這裡就是它的出處**:
#   綠 = 原始碼且夾具、黃 = 其一、紅 = 皆無;樞紐 = 被引用數 >= 3。
# 不自己發明門檻。這組定義承襲自已退役的 make_axiom_reader.py(GEO-165 刪除),
# 考古見 `git show 1498bc4:geometry-guide/make_axiom_reader.py` 的 464-466 行
# (GEO-167:原註解引的 431-433 在刪檔前就已過期,差了三十幾行)。
TRACE_CSS = (
    ":root{--trace-ok:#2f855a;--trace-partial:#b7791f;--trace-none:#c53030}"
    ":root[data-theme=dark]{--trace-ok:#68d391;--trace-partial:#f6c177;--trace-none:#fc8181}"
    ".toc-item{position:relative;padding-left:14px}"
    ".toc-item::before{content:'';position:absolute;left:5px;top:50%;transform:translateY(-50%);"
    "width:4px;height:18px;border-radius:2px;background:var(--trace-dot,transparent)}"
    ".toc-item[data-trace=ok]{--trace-dot:var(--trace-ok)}"
    ".toc-item[data-trace=partial]{--trace-dot:var(--trace-partial)}"
    ".toc-item[data-trace=none]{--trace-dot:var(--trace-none)}"
    ".toc-evidence{margin-left:auto;font-size:10.5px;color:var(--muted);white-space:nowrap;padding-left:6px}"
    ".clause-badges{display:inline-flex;gap:6px;align-items:center;margin-left:8px;vertical-align:middle}"
    ".badge-trace{font-size:10.5px;padding:1px 7px;border-radius:999px;border:1px solid currentColor;font-weight:600}"
    ".badge-trace[data-trace=ok]{color:var(--trace-ok)}"
    ".badge-trace[data-trace=partial]{color:var(--trace-partial)}"
    ".badge-trace[data-trace=none]{color:var(--trace-none)}"
    ".badge-hub{font-size:10.5px;padding:1px 7px;border-radius:999px;background:var(--accent);color:var(--bg);font-weight:600}"
    ".trace-section{margin-top:18px;border-top:1px solid var(--line);padding-top:10px}"
    ".trace-section>summary{cursor:pointer;color:var(--muted);font-size:12px;letter-spacing:.06em}"
    ".trace-row{margin:8px 0;font-size:12.5px;display:flex;gap:8px;flex-wrap:wrap;align-items:baseline}"
    ".trace-row>b{font-weight:600;color:var(--muted);font-size:11px;letter-spacing:.08em;min-width:4.5em}"
    ".trace-row code{font-size:11.5px}"
    ".trace-row .muted{color:var(--muted)}"
)
# GEO-141(🔒 Q1 2026-09-20):批註系統整套色與圖面底色原本散在 CSS 規則裡寫死(head 內 44 個色碼),
# 深色模式靠逐條選擇器補丁救回來,任何新增顏色都得再補一次。收成 token,深色只改 token 值。
# 淺色值沿用原本就在用的那幾個,不自己換色;深色值取專案既有的同族色(--trace-* 用過的)。
COLOR_TOKENS = {
    "--note":        ("#c68d2a", "#eac076"),   # 批註琥珀:左邊條、引文邊框、復原橫幅
    "--note-strong": ("#9a5200", "#f6c177"),   # 未存檔 / 引文已過期的字
    "--danger":      ("#ad3424", "#fc8181"),   # 批註錯誤訊息
    "--proposal":    ("#bb6c59", "#e0a08e"),   # 提案前後對照的左邊條
    "--figure-bg":   ("#eef2f5", "#181e24"),   # 圖卡底色(淺色主題不再是黑方塊)
    "--reject-bg":   ("#faeeeb", "#422f2b"),   # 範例「拒絕」徽章與預期輸出
    "--reject-ink":  ("#a74739", "#f3b3a4"),
    "--transcript-bg": ("#edf1fa", "#253243"), # 範例「實錄」徽章
    "--transcript-ink": ("#405f96", "#9db6e0"),
    "--hit-bg":      ("#fff0e9", "#453329"),   # DSL 命中行
    "--hit-line":    ("#d17e5d", "#d17e5d"),
    "--link-underline": ("#97bdbb", "#4e7f76"),
    "--sheet-ref-ink": (None, "#132b25"),      # 只有深色有的既有微調,保留原值
}
# 規則裡寫死的色碼 → token。只換這幾個,不動 :root 既有的 --bg/--ink/… 定義。
COLOR_REWRITES = [
    ("a:focus-visible,button:focus-visible,summary:focus-visible,input:focus-visible{outline:3px solid #288b9c;outline-offset:3px}",
     "a:focus-visible,button:focus-visible,summary:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:4px}"),
    (".review-save-state.dirty{color:#9a5200}", ".review-save-state.dirty{color:var(--note-strong)}"),
    (".stale-note{font-size:12px;color:#9a5200;", ".stale-note{font-size:12px;color:var(--note-strong);"),
    (".review-block.has-comments>.review-target{border-left:3px solid #c68d2a;",
     ".review-block.has-comments>.review-target{border-left:3px solid var(--note);"),
    (".review-block.target-flash{outline:2px solid #c68d2a;", ".review-block.target-flash{outline:2px solid var(--note);"),
    ("border-left:3px solid #c68d2a;border-radius:0 7px 7px 0;", "border-left:3px solid var(--note);border-radius:0 7px 7px 0;"),
    (".recovery-banner{padding:12px;border:1px solid #c68d2a;", ".recovery-banner{padding:12px;border:1px solid var(--note);"),
    (".review-error{color:#ad3424;", ".review-error{color:var(--danger);"),
    (".proposal-before{border-left:3px solid #bb6c59;", ".proposal-before{border-left:3px solid var(--proposal);"),
    (".ex figure img{display:block;width:100%;height:auto;background:#181e24;",
     ".ex figure img{display:block;width:100%;height:auto;background:var(--figure-bg);"),
    (".witness-section figure img{display:block;width:100%;height:auto;background:#181e24;",
     ".witness-section figure img{display:block;width:100%;height:auto;background:var(--figure-bg);"),
    (".image-viewport{overflow:auto;flex:1;min-height:0;padding:10px;background:#181e24;",
     ".image-viewport{overflow:auto;flex:1;min-height:0;padding:10px;background:var(--figure-bg);"),
    (".ex.no .badge{background:#faeeeb;color:#a74739}", ".ex.no .badge{background:var(--reject-bg);color:var(--reject-ink)}"),
    (".ex.no .expect{background:#faeeeb}", ".ex.no .expect{background:var(--reject-bg)}"),
    (".ex.tr .badge{background:#edf1fa;color:#405f96}", ".ex.tr .badge{background:var(--transcript-bg);color:var(--transcript-ink)}"),
    (".dsl>span.hit{background:#fff0e9;border-left:2px solid #d17e5d}",
     ".dsl>span.hit{background:var(--hit-bg);border-left:2px solid var(--hit-line)}"),
    ("text-decoration-color:#97bdbb;", "text-decoration-color:var(--link-underline);"),
    # 深色的逐條選擇器補丁刪掉,值已移進 :root[data-theme=dark] 的 token。
    (":root[data-theme=dark] .ex.no .badge,:root[data-theme=dark] .ex.no .expect{background:#422f2b;color:#f3b3a4}", ""),
    (":root[data-theme=dark] .dsl>span.hit{background:#453329}", ""),
    (":root[data-theme=dark] .sheet .full-ref{color:#132b25}",
     ":root[data-theme=dark] .sheet .full-ref{color:var(--sheet-ref-ink)}"),
]

# Completed color migrations remain compatible with exact historical input,
# but current CSS is guarded by declarations, not historical full-rule spelling.
COLOR_CONTRACTS = [
    ("a:focus-visible,button:focus-visible,summary:focus-visible,input:focus-visible", {"outline": "2px solid var(--accent)", "outline-offset": "4px"}),
    (".review-save-state.dirty", {"color": "var(--note-strong)"}),
    (".stale-note", {"color": "var(--note-strong)"}),
    (".review-block.has-comments>.review-target", {"border-left": "3px solid var(--note)"}),
    (".review-block.target-flash", {"outline": "2px solid var(--note)"}),
    (".inline-note", {"border-left": "3px solid var(--note)"}),
    (".recovery-banner", {"border": "1px solid var(--note)"}),
    (".review-error", {"color": "var(--danger)"}),
    (".proposal-before", {"border-left": "3px solid var(--proposal)"}),
    (".ex figure img", {"background": "var(--figure-bg)"}),
    (".witness-section figure img", {"background": "var(--figure-bg)"}),
    (".image-viewport", {"background": "var(--figure-bg)"}),
    (".ex.no .badge", {"background": "var(--reject-bg)", "color": "var(--reject-ink)"}),
    (".ex.no .expect", {"background": "var(--reject-bg)"}),
    (".ex.tr .badge", {"background": "var(--transcript-bg)", "color": "var(--transcript-ink)"}),
    (".dsl>span.hit", {"background": "var(--hit-bg)", "border-left": "2px solid var(--hit-line)"}),
    (".copy .reference-link", {"text-decoration-color": "var(--link-underline)"}),
    (":root[data-theme=dark] .ex.no .badge,:root[data-theme=dark] .ex.no .expect", None),
    (":root[data-theme=dark] .dsl>span.hit", None),
    (":root[data-theme=dark] .sheet .full-ref", {"color": "var(--sheet-ref-ink)"}),
]


def color_contract_regressions(template: str) -> list[str]:
    def selector_key(selector):
        return re.sub(r"\s*([>,])\s*", r"\1", " ".join(selector.split()))

    def value_key(value):
        value = " ".join(value.strip().split())
        return re.sub(r"var\(\s*(--[\w-]+)\s*\)", r"var(\1)", value)

    css = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", template, re.S))
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules = {}
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        declarations = {}
        for declaration in match[2].split(";"):
            if ":" in declaration:
                key, value = declaration.split(":", 1)
                declarations[key.strip()] = value_key(value)
        for selector in match[1].split(","):
            rules.setdefault(selector_key(selector), {}).update(declarations)
    bad = []
    for selectors, required in COLOR_CONTRACTS:
        for selector in selectors.split(","):
            actual = rules.get(selector_key(selector))
            if required is None:
                if actual is not None:
                    bad.append("retired dark override: " + selector)
            elif actual is None or any(actual.get(key) != value_key(value) for key, value in required.items()):
                bad.append("color declaration contract: " + selector)
    return bad


def apply_color_tokens(template: str) -> str:
    """把 token 定義併進 :root / :root[data-theme=dark],再把規則裡寫死的色碼換成 token。"""
    every = dict(COLOR_TOKENS)
    every.update(WITNESS_TOKENS)     # GEO-141 Q8:圖面色與其他 token 同一組,深色只改值

    def write_tokens(block: str, index: int) -> str:
        """把本表的 token 寫進一個 :root 區塊。先移除既有同名 token 再寫入當前集合——
        token 集合日後會增減,用「改前/改後」判定會在集合一變就卡住(GEO-141 Q8 實際踩到)。"""
        head, inner = block.split("{", 1)
        inner = inner.rsplit("}", 1)[0]
        for name in every:
            inner = re.sub(re.escape(name) + r":[^;}]*;?", "", inner)
        inner = inner.rstrip(";")
        add = "".join("%s:%s;" % (k, v[index]) for k, v in every.items() if v[index])
        return head + "{" + inner + ";" + add.rstrip(";") + "}"

    for pattern, index in ((r":root\{[^}]*\}", 0), (r":root\[data-theme=dark\]\{[^}]*\}", 1)):
        m = re.search(pattern, template)
        if not m:
            raise ValueError("reader template drift:找不到 :root token 區塊 " + pattern)
        template = template[:m.start()] + write_tokens(m[0], index) + template[m.end():]
        for name, pair in every.items():
            if pair[index]:
                PATCHES.expect_present("色彩 token " + name,
                                       "%s:%s" % (name, pair[index]))
    for old_css, new_css in COLOR_REWRITES:
        if old_css in template:
            template = force(template, old_css, new_css, "歷史色碼相容: " + new_css[:40])
    regressions = color_contract_regressions(template)
    if regressions:
        raise ValueError("reader color contract: " + "; ".join(regressions))
    return template


def hardcoded_colors(template: str) -> list[str]:
    """回傳 CSS 規則裡仍寫死的色碼(token 定義區與 <meta theme-color> 除外)。"""
    head = template[:template.index('<script id="reader-counts"')]
    print_at = head.find("@media print{")
    bad = []
    for m in re.finditer(r"#[0-9a-fA-F]{6}\b", head):
        if print_at >= 0 and m.start() > print_at:
            continue          # 列印樣式沒有主題,固定色是刻意的
        before = head.rfind("}", 0, m.start())
        rule = head[before + 1:m.start()]
        if "--" in rule.split("{")[-1] or "theme-color" in head[max(0, m.start() - 120):m.start()]:
            continue          # token 定義本身,或 <meta name=theme-color>
        bad.append(m.group(0) + " @ " + rule.split("{")[0].strip()[-60:])
    return bad


TRACE_LABEL = {"ok": "原始碼＋夾具", "partial": "僅其一", "none": "無追溯"}

# 每次重建都重新產生的區塊。保留「歷史範例」時必須以它們為終點,否則會把上一輪的產物
# 一起留下來、然後再產一份。順序無所謂,取最早出現者。
GENERATED_SECTIONS = (
    '<section class="witness-section">',
    '<details class="trace-section">',
    '<section class="relation-section"',
)

OLD_STALE = 'if(a!==\'exact\')html+=\'<div class="stale-note">\'+(a===\'missing\'?\'原段落不存在\':\'段落已改版\')+\'：以下引文仍是批註當時的快照，不自動重新配對。</div>\';'
NEW_STALE = 'if(a!==\'exact\')html+=\'<div class="stale-note">\'+(a===\'missing\'?\'原段落不存在\':\'段落已改版\')+\'：以下引文仍是批註當時的快照，不自動重新配對。</div>\';\n /* GEO-144(🔒 Q2):過期批註就地給下一步,不再只留一行小字。 */\n if(a!==\'exact\')html+=\'<div class="stale-actions review-only"><button type="button" class="review-primary" data-review-action="reanchor" data-id="\'+esc(c.id)+\'">重新綁定這段</button><button type="button" data-review-action="jump" data-id="\'+esc(c.id)+\'">回到段落</button></div>\';\n if((c.anchorHistory||[]).length)html+=\'<div class="stale-actions review-only"><button type="button" data-review-action="undo-reanchor" data-id="\'+esc(c.id)+\'">復原綁定(回到上一個定位)</button></div>\';'
OLD_REANCHOR = "function reanchor(c){if(!confirm('將這則批註重新綁定到「目前版本的整個段落」？舊引文仍保留在定位歷史中；原本的局部選文不會自動猜測新位置。'))return;c.anchorHistory.push(clone(c.target));c.target=currentTarget(c.target.blockId,null);c.events.push({at:stamp(),type:'user-reanchored-whole-block'});c.updatedAt=stamp();persist();renderNotes();commentList();}"
NEW_REANCHOR = '/* GEO-144(🔒 Q2):原本是一個 confirm(),看不到綁定前後差多少,等於叫使用者盲簽。\n   改成面板內的前後對照 + 主鈕;綁定後 anchorHistory 留著,可復原一次。 */\nfunction reanchor(c){\n const t=c.target,now=blocks[t.blockId];\n const before=esc((t.selector&&t.selector.exact)||\'\'),after=now?esc(now.source):\'\';\n dialog(\'重新綁定 \'+esc(t.clauseId)+\' · \'+esc(t.label),\n  \'<p class="hint">重新綁定會把這則批註指到<strong>目前版本的整個段落</strong>。\'\n  +\'舊引文保留在定位歷史裡,原本的局部選文<strong>不會</strong>自動猜測新位置。</p>\'\n  +\'<div class="reanchor-diff"><section><h4>批註當時的引文</h4><blockquote class="note-quote">\'\n  +(before||\'(沒有記錄引文)\')+\'</blockquote></section>\'\n  +\'<section><h4>目前的段落</h4><blockquote class="note-quote">\'\n  +(after||\'(這個段落在目前版本裡已經不存在,無法重新綁定)\')+\'</blockquote></section></div>\'\n  +(now?\'<button type="button" class="review-primary" data-review-action="reanchor-confirm" data-id="\'+esc(c.id)+\'">確定重新綁定</button>\':\'\')\n  +\'<button type="button" data-review-action="list">取消</button>\',\'reanchor\');\n}\nfunction reanchorConfirm(c){\n if(!blocks[c.target.blockId])return;\n c.anchorHistory=c.anchorHistory||[];c.anchorHistory.push(clone(c.target));\n c.target=currentTarget(c.target.blockId,null);\n c.events.push({at:stamp(),type:\'user-reanchored-whole-block\'});\n c.updatedAt=stamp();persist();renderNotes();commentList();\n notify(\'已重新綁定。這則批註上有「復原綁定」可以還原。\');\n}\nfunction undoReanchor(c){\n const prev=(c.anchorHistory||[]).pop();if(!prev)return;\n c.target=prev;c.events.push({at:stamp(),type:\'user-undo-reanchor\'});\n c.updatedAt=stamp();persist();renderNotes();commentList();\n notify(\'已復原到上一個定位。\');\n}'
OLD_DISPATCH = "else if(act==='reanchor'&&c)reanchor(c);"
NEW_DISPATCH = "else if(act==='reanchor'&&c)reanchor(c);  else if(act==='reanchor-confirm'&&c)reanchorConfirm(c);  else if(act==='undo-reanchor'&&c)undoReanchor(c);"

# GEO-144(🔒 Q2 2026-09-20):過期批註就地重新綁定的樣式。
REANCHOR_CSS = (
    ".stale-actions{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 2px}"
    ".stale-actions button{font-size:12.5px;min-height:38px;padding:6px 12px;border:1px solid var(--line);"
    "border-radius:7px;background:var(--paper);color:var(--accent)}"
    ".stale-actions button.review-primary{background:var(--note);color:var(--bg);border-color:var(--note);font-weight:600}"
    ".reanchor-diff{display:grid;gap:12px;margin:12px 0}"
    "@media (min-width:640px){.reanchor-diff{grid-template-columns:1fr 1fr}}"
    ".reanchor-diff h4{font-size:11px;letter-spacing:.08em;color:var(--muted);margin:0 0 6px;font-weight:600}"
    ".reanchor-diff blockquote{margin:0}"
)

# GEO-141 最後一段(🔒 Q8 2026-09-20):見證圖改 inline <svg>,顏色由頁面 CSS 控。
# 原本樣式燒在 SVG 裡(<img> 看不到頁面變數與 data-theme),淺色主題下是一塊黑方塊。
# 內聯後全部改吃 token;**角色色維持字面值不動**(🔒 Q1:屬 witness/規範.md v1、與條文語意綁定)。
# 選擇器一律 scoped 在 .witness-diagram 之下——.title/.label/.frame 名字太通用,直接內聯會汙染全域。
WITNESS_TOKENS = {
    "--wit-ink":       ("#222222", "#d7dfe6"),
    "--wit-ink-soft":  ("#333333", "#c5cfd8"),
    "--wit-line":      ("#bbbbbb", "#5a6b7a"),
    "--wit-edge":      ("#3366cc", "#84c8f6"),
    "--wit-surface":   ("#dbe9ff", "#304557"),
    "--wit-guide":     ("#cc3333", "#ed9494"),
    "--wit-free":      ("#e08020", "#efba69"),
    "--wit-timber":    ("#ffd27f", "#edb365"),
    "--wit-timber-ln": ("#a06000", "#edb365"),
    "--wit-timber-tx": ("#7a4a00", "#efba69"),
}
WITNESS_DIAGRAM_CSS = (
    ".witness-diagram{display:block;width:100%;height:auto;background:var(--figure-bg);border-radius:6px}"
    ".witness-diagram polygon,.witness-diagram line,.witness-diagram rect{vector-effect:non-scaling-stroke}"
    ".witness-diagram .frame{fill:var(--figure-bg);stroke:none}"
    ".witness-diagram .title{font:bold 150px sans-serif;fill:var(--wit-ink)}"
    ".witness-diagram .label{font:110px sans-serif;fill:var(--wit-ink-soft);text-anchor:middle;dominant-baseline:middle}"
    ".witness-diagram .guide-label{text-anchor:start;fill:var(--wit-guide)}"
    ".witness-diagram .timber-label{fill:var(--wit-timber-tx);font-weight:bold}"
    ".witness-diagram .guide-label,.witness-diagram .timber-label"
    "{paint-order:stroke;stroke:var(--figure-bg);stroke-width:30px;stroke-linejoin:round}"
    ".witness-diagram .surface{fill:var(--wit-surface);fill-opacity:.7;stroke:var(--wit-edge);stroke-width:1.5px}"
    ".witness-diagram .hole{fill:var(--figure-bg);stroke:var(--wit-edge);stroke-width:1.5px}"
    ".witness-diagram .edge{stroke:var(--wit-edge);stroke-width:1.5px}"
    ".witness-diagram .edge-free{stroke:var(--wit-free);stroke-width:1.5px;stroke-dasharray:30 15}"
    ".witness-diagram .guide{stroke:var(--wit-guide);stroke-width:1px;stroke-dasharray:60 30}"
    ".witness-diagram .timber-face{fill:var(--wit-timber);fill-opacity:.5;stroke:var(--wit-timber-ln);stroke-width:1.5px}"
    ".witness-diagram .timber-face-near{fill-opacity:.85}"
    ".witness-diagram .role-boundary{fill:#e2a24a;stroke:#e2a24a}"
    ".witness-diagram .role-primary{fill:#63b3ed;stroke:#63b3ed}"
    ".witness-diagram .role-secondary{fill:#9ae6b4;stroke:#9ae6b4}"
    ".witness-diagram .role-custom{fill:#d6bcfa;stroke:#d6bcfa}"
    ".witness-diagram .stop{stroke:none}"
    ".witness-diagram .stop-label{font:bold 110px sans-serif;dominant-baseline:middle;"
    "paint-order:stroke;stroke:var(--figure-bg);stroke-width:30px;stroke-linejoin:round}"
    ".witness-diagram .tile-frame{fill:var(--figure-bg);stroke:var(--wit-line);stroke-width:1px}"
    ".witness-diagram .tile-title{font:bold 72px sans-serif;fill:var(--wit-ink)}"
    ".witness-diagram .tile line.edge,.witness-diagram .tile line.guide,"
    ".witness-diagram .tile line.edge-free{stroke-width:2px}"
    ".witness-diagram .legend-title{font:bold 110px sans-serif;fill:var(--wit-ink)}"
    ".witness-diagram .legend-text{font:95px sans-serif;fill:var(--wit-ink-soft);dominant-baseline:middle}"
    ".witness-diagram .legend-box{fill:var(--figure-bg);stroke:var(--wit-line);stroke-width:1px}"
    ".witness-diagram .section-title{font:bold 120px sans-serif;fill:var(--wit-ink)}"
)

# GEO-148(🔒 Q6 2026-09-20):
#  (a) 960–1279px:左欄已是固定導覽、右欄還沒出現,點條號原本走 showModal() 把正文整個蓋掉,
#      與右欄文案「對照引用,不離開正文」矛盾。改成底部半高 sheet,而且用 show() 而非 showModal()
#      ——非模態,正文同時看得見**也仍可操作**。
#  (b) ≤959px:底部列擠 5 個控制、字級被壓到 13px/11px。只留「目錄·上條·位置·下條」四鍵,
#      字級回 14px;批註入口移到頂列(條文內本來就有琥珀左邊條與徽章)。
SHEET_CSS = (
    "@media (min-width:960px) and (max-width:1279px){"
    "body.half-sheet-open{padding-bottom:52dvh}"
    "dialog#reference-sheet[open],dialog#review-dialog[open]{position:fixed;inset:auto 0 0 0;margin:0;"
    "width:100%;max-width:100%;height:50dvh;max-height:50dvh;border:0;border-top:1px solid var(--line);"
    "border-radius:14px 14px 0 0;box-shadow:0 -12px 34px rgba(0,0,0,.2);overflow:auto;display:block}"
    "dialog#reference-sheet[open]::backdrop,dialog#review-dialog[open]::backdrop{background:transparent}"
    "}"
    "@media (max-width:959px){"
    ".bottom-bar .bottom-inner>[data-review-action=\"list\"]{display:none}"
    ".bottom-bar .bottom-inner{gap:8px}"
    ".bottom-bar .bottom-inner button{font-size:14px;padding:6px 8px}"
    ".bottom-bar .bottom-inner .position{font-size:12px;min-width:48px}"
    ".masthead .header-inner .workspace-toolbar{display:flex;align-items:center;gap:6px;margin-left:auto}"
    ".masthead .header-inner .workspace-toolbar>.workspace-current,"
    ".masthead .header-inner .workspace-toolbar>.workspace-step,"
    ".masthead .header-inner .workspace-toolbar>[data-review-action=\"export\"]{display:none}"
    ".masthead .header-inner .workspace-toolbar>[data-review-action=\"list\"]"
    "{font-size:13px;padding:6px 10px;min-height:40px;white-space:nowrap}"
    "}"
)

# GEO-138(🔒 Q4):右欄上半的見證圖面板。只在 dock 寬度出現;窄螢幕維持卡片內 inline。
WITNESS_PANE_CSS = (
    "#workspace-witness{display:none}"
    "@media (min-width:1280px){body.workspace-ready #workspace-witness{display:block;"
    "border-bottom:1px solid var(--line);padding:10px 12px;max-height:38vh;overflow:auto}}"
    "#workspace-witness h3{font-size:11px;letter-spacing:.08em;color:var(--muted);margin:0 0 6px;font-weight:600}"
    "#workspace-witness h3 small{color:var(--accent);font-weight:700;margin-left:6px;letter-spacing:0}"
    "#workspace-witness figure{margin:0}"
    "#workspace-witness img{display:block;width:100%;height:auto;background:var(--figure-bg);border-radius:6px}"
    "#workspace-witness .hint{font-size:12px;color:var(--muted);margin:0;line-height:1.7}"
)

# GEO-149:篩選 chip 的樣式,沿用分類篩選(.group-jumps a)的視覺語言。
FACET_CSS = (
    ".toc-facets{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 2px}"
    ".toc-facets a{font-size:11.5px;padding:4px 10px;border:1px solid var(--line);border-radius:999px;"
    "color:var(--muted);min-height:32px;display:inline-flex;align-items:center;text-decoration:none}"
    ".toc-facets a.active{border-color:var(--accent);color:var(--accent);background:var(--soft);font-weight:600}"
    ".toc-facets a>b{font-weight:600;margin-left:5px;font-size:10.5px;opacity:.75}"
)

# GEO-139(2/4):hover 快速預覽的樣式。只在有 hover 的裝置出現(@media hover:hover),
# 觸控裝置本來就沒有 hover,與長按叫出段落工具不衝突(GEO-120 拍板二原文)。
REF_PREVIEW_CSS = (
    "#ref-preview{position:fixed;z-index:60;max-width:min(420px,calc(100vw - 16px));"
    "background:var(--paper);color:var(--ink);border:1px solid var(--line);border-left:3px solid var(--accent);"
    "border-radius:8px;box-shadow:0 10px 28px rgba(0,0,0,.18);padding:10px 12px;font-size:13px;line-height:1.7;"
    "pointer-events:none}"
    "#ref-preview b{display:block;font-size:12px;color:var(--accent);margin-bottom:4px}"
    "#ref-preview[hidden]{display:none}"
    "@media (hover:none){#ref-preview{display:none!important}}"
)

# GEO-145(🔒 Q3 2026-09-20):段落工具列改成非常駐。閱讀是常態、校對是階段性;
# 452 組每段固定掛一列 34–44px 的控制列會把正文切碎。height:0 讓它不佔版面,
# hover / 鍵盤 focus / 觸控長按才展開;**已有批註的段落仍常駐**,不會漏看。
BLOCK_TOOLS_CSS = (
    ".review-block>.block-tools{opacity:0;visibility:hidden;height:0;margin-top:0;overflow:hidden;"
    "transition:opacity .12s ease}"
    ".review-block:hover>.block-tools,.review-block:focus-within>.block-tools,"
    ".review-block.show-tools>.block-tools,.review-block.has-comments>.block-tools,"
    ".review-block.is-reviewing>.block-tools"
    "{opacity:1;visibility:visible;height:auto;margin-top:8px;overflow:visible}"
    "@media print{.review-block>.block-tools{display:none!important}}"
)

# GEO-147:區塊標籤把視覺重量讓給內容——12px、寬字距、muted,不再與內容同重。
CLAUSE_LABEL_CSS = (
    ".plain-section>h3,.original-section>h3{font-size:12px;letter-spacing:.08em;"
    "color:var(--muted);font-weight:600;margin:0 0 8px}"
    ".plain-section>h3 small,.original-section>h3 small{letter-spacing:0}"
)
WITNESS_CSS = (
    ".witness-section{margin-top:22px}.witness-section h3{font-size:13px;color:var(--accent);margin:0 0 8px}"
    ".witness-section h3 small{font-weight:400;color:var(--muted);margin-left:6px}"
    ".witness-section figure{margin:0;min-width:0}.witness-section figure img{display:block;width:100%;height:auto;background:#181e24;border-radius:6px}"
    ".witness-section figcaption{font-size:11px;color:var(--muted);line-height:1.65;margin-top:8px}"
    ".witness-section details{margin-top:8px}.witness-section summary{font-size:12px;color:var(--accent);cursor:pointer}"
)
VIEW_LABEL = {"bottom": "仰視圖", "front": "前視圖", "side": "側視圖", "all": "三視圖"}


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compact(value) -> str:
    # Same representation as JSON.stringify for this string/array/object schema.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def safe_json(value) -> str:
    return compact(value).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def script_text(source: str, identifier: str) -> str:
    m = re.search(r'<script\b[^>]*(?<![\w-])id="' + re.escape(identifier) + r'"[^>]*>(.*?)</script>', source, re.S)
    if not m:
        raise ValueError("Missing script: " + identifier)
    return m.group(1)


def replace_script(source: str, identifier: str, value: str) -> str:
    pattern = r'(<script\b[^>]*(?<![\w-])id="' + re.escape(identifier) + r'"[^>]*>).*?(</script>)'
    source, count = re.subn(pattern, lambda m: m[1] + value + m[2], source, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Missing script: " + identifier)
    return source


def source_clauses(text: str) -> list[dict]:
    # Only normative sections I–III. Section IV deliberately mentions reserved IDs.
    text = text.split("## 四、", 1)[0]
    starts = list(CLAUSE_START.finditer(text))
    result = []
    for index, m in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        body = text[m.start():end].split("\n## ", 1)[0].rstrip("\n")
        first = body.splitlines()[0]
        label = re.sub(r"^\*\*|\*\*", "", first)
        label = re.sub(r"^[DIR]\d+[a-z]?\s+", "", label)
        title = re.split(r"[：:]", label, 1)[0]
        title = re.split(r"[（(]", title, 1)[0].strip()
        if len(title) > 38:
            title = title[:38] + "…"
        result.append({"id": m[1], "title": title, "line": text.count("\n", 0, m.start()) + 1, "body": body})
    ids = {item["id"] for item in result}
    if len(result) < 60 or len(ids) != len(result):
        raise ValueError("Missing or duplicate SSOT clauses; refusing to write")
    for item in result:
        for ref in CLAUSE_REF.finditer(item["body"]):
            if ref[1] not in ids:
                raise ValueError(f"Dangling SSOT reference {item['id']} -> {ref[1]}")
    return result


def source_plain(text: str, known: set[str]) -> dict[str, str]:
    starts = list(re.finditer(r"^## ([DIR]\d+[a-z]?)\s*$", text, re.M))
    result = {}
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        if match[1] in result or match[1] not in known:
            raise ValueError("Unknown/duplicate plain clause: " + match[1])
        result[match[1]] = text[match.end():end].strip()
    if known != set(result):
        raise ValueError("Missing plain explanations: " + ", ".join(sorted(known - set(result))))
    return result


def body_parts(body: str) -> list[tuple[str | None, str, str]]:
    """Disjoint source slices; exact separators retained, no duplicated subclauses."""
    marks = list(SUB_START.finditer(body))
    spans = []
    if not marks:
        spans = [(None, 0, len(body))]
    else:
        if marks[0].start():
            spans.append((None, 0, marks[0].start()))
        for index, mark in enumerate(marks):
            end = marks[index + 1].start() if index + 1 < len(marks) else len(body)
            # The final clause-level paragraph is not part of the last subclause.
            if index + 1 == len(marks):
                cursor = body.find("\n", mark.start()) + 1
                while cursor > 0 and cursor < end:
                    line_end = body.find("\n", cursor)
                    if line_end < 0:
                        line_end = end
                    line = body[cursor:line_end]
                    if line.strip() and len(line) - len(line.lstrip(" ")) <= len(mark[1]):
                        spans.append((mark[2], mark.start(), cursor))
                        spans.append((None, cursor, end))
                        break
                    cursor = line_end + 1
                else:
                    spans.append((mark[2], mark.start(), end))
            else:
                spans.append((mark[2], mark.start(), end))
    result = []
    for sub, start, end in spans:
        raw = body[start:end]
        # A subclause is one stable semantic block; ordinary text splits at blank lines.
        chunks = [raw] if sub else re.split(r"(?<=\n)(?=\n)", raw)
        if not sub:
            chunks = []
            pos = 0
            for gap in re.finditer(r"\n\n+", raw):
                chunks.append(raw[pos:gap.end()])
                pos = gap.end()
            if pos < len(raw):
                chunks.append(raw[pos:])
        for chunk in chunks:
            source = chunk.rstrip("\n")
            separator = chunk[len(source):]
            if source:
                result.append((sub, source, separator))
            elif result:
                letter, prior, sep = result[-1]
                result[-1] = (letter, prior, sep + chunk)
    if "".join(source + sep for _, source, sep in result) != body:
        raise ValueError("Source partition changed original whitespace")
    return result


def subs_for(body: str) -> dict[str, str]:
    return {sub: re.sub(r"^\s*\([a-z]\)\s*", "", source) for sub, source, _ in body_parts(body) if sub}


def new_blocks(item: dict, section: str, old: list[dict]) -> list[dict]:
    parts = body_parts(item[section]) if section == "body" else body_parts(item[section])
    # Plain text does not own normative subclauses.
    if section == "plain":
        parts = [(None, text, sep) for _, text, sep in parts]
    old_section = [b for b in old if b["clauseId"] == item["id"] and b["section"] == section]
    old_by_id = {b["id"]: b for b in old_section}
    exact_reserved = {b["id"] for b in old_section if any(b["source"] == source and b.get("sub") == sub for sub, source, _ in parts)}
    used = set()
    result = []
    paragraph = 0
    for ordinal, (sub, source, separator) in enumerate(parts, 1):
        if not sub:
            paragraph += 1
        desired = f"{item['id']}.{section}." + (sub or f"p{paragraph:02}")
        # Preserve exact-source block identity first, even after a paragraph insertion.
        match = next((b for b in old_section if b["source"] == source and b["id"] not in used and b.get("sub") == sub), None)
        if not match:
            match = old_by_id.get(desired) if desired not in used and desired not in exact_reserved else None
        identifier = match["id"] if match else desired
        suffix = paragraph
        while identifier in used or (not match and identifier in exact_reserved):
            suffix += 1
            identifier = f"{item['id']}.{section}.p{suffix:02}"
        used.add(identifier)
        b = copy.deepcopy(match) if match else {}
        b.update(id=identifier, clauseId=item["id"], section=section,
                 label=("原文" if section == "body" else "白話") + (f" ({sub})" if sub else f" 第{paragraph}段"),
                 ordinal=ordinal, sourceLine=item["line"], sub=sub, source=source,
                 separator=separator, editable=True, sourceHash=digest(source))
        b.setdefault("originalSource", source)
        b.setdefault("originalHash", digest(b["originalSource"]))
        b.setdefault("originalSub", item["subs"].get(sub) if sub else None)
        result.append(b)
    return result


def render_inline_with_reader(source: str, texts: list[str], clauses: list[dict]) -> list[str]:
    reader = script_text(source, "reader-script")
    safe = re.search(r"    function safeText\(s\)\{.*?\}\n", reader).group()
    inline = reader[reader.index("    function inline(text)"):reader.index("    function renderReference(ref)")]
    node = os.environ.get("CODEX_PRIMARY_RUNTIME_NODE") or shutil.which("node")
    if not node:
        raise ValueError("Node.js is required to use the reader's exact inline() renderer")
    js = "const fs=require('fs');const x=JSON.parse(fs.readFileSync(0,'utf8'));const byId=Object.fromEntries(x.ids.map(id=>[id,true]));\n" + safe + inline + "\nprocess.stdout.write(JSON.stringify(x.texts.map(inline)));"
    run = subprocess.run([node, "-e", js], input=compact({"ids": [x["id"] for x in clauses], "texts": texts}), text=True, capture_output=True, check=True)
    return json.loads(run.stdout)


def static_note(comment: dict, block: dict) -> str:
    target = comment["target"]
    stale = '<p class="stale-note">段落已改版；以下引文保留批註當時的快照，不自動重新配對。</p>' if target["sourceSnapshot"] != block["source"] else ""
    return ('<div class="inline-note" data-comment-id="' + html.escape(comment["id"], quote=True) + '">' +
            '<div class="note-heading"><strong>使用者批註 · ' + html.escape(comment["status"]) + '</strong></div>' + stale +
            '<blockquote class="note-quote">' + html.escape(target["selector"]["exact"]) + '</blockquote>' +
            '<div class="note-copy"><strong>我的意思</strong>\n' + html.escape(comment["userIntent"]) + '</div>' +
            ('<div class="note-copy"><strong>不能改掉的條件</strong>\n' + html.escape(comment["mustPreserve"]) + '</div>' if comment.get("mustPreserve") else '') +
            ('<div class="note-copy"><strong>建議改法（尚未套用）</strong>\n' + html.escape(comment["suggestedText"]) + '</div>' if comment.get("suggestedText") else '') + '</div>')


def load_witness_manifest() -> dict:
    if not WITNESS_MANIFEST.exists():
        return {}
    return json.loads(WITNESS_MANIFEST.read_text(encoding="utf-8"))


def witness_figure(cid: str, manifest: dict) -> str:
    """把 GEO-131 的見證圖嵌進條文卡。只讀檔、只換配色;幾何位元組來自 witness/,由 witness.py --check 守。"""
    entry = manifest.get(cid)
    path = WITNESS_DIR / f"{cid}.svg"
    if not entry or not path.exists():
        return ""
    svg = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    m = re.search(r'<svg[^>]*viewBox="([^"]+)"[^>]*data-full="([^"]+)"[^>]*>', svg)
    if not m:
        raise ValueError("Witness SVG missing viewBox/data-full: " + cid)
    crop, full = m[1], m[2]
    body = svg[m.end():svg.rfind("</svg>")]
    body = re.sub(r"<style>.*?</style>\s*", "", body, count=1, flags=re.S).strip()
    # 規範 v1 的見證圖自帶 <style id="witness">(角色色、接點格、圖例);只把它的底/字色換成閱讀器深色,角色色不動。
    for light, dark in (("#ffffff", "#181e24"), ("#222222", "#d7dfe6"), ("#333333", "#c5cfd8"), ("#888888", "#5a6b7a"), ("#bbbbbb", "#5a6b7a")):
        body = re.sub(r'(<style id="witness">.*?</style>)', lambda mm: mm[1].replace(light, dark), body, count=1, flags=re.S)

    # GEO-141(🔒 Q8):改內聯。圖自帶的 <style> 全部拿掉——.title/.label/.frame 名字太通用,
    # 內聯後會變成全域規則汙染整份文件;改由 WITNESS_DIAGRAM_CSS 以 .witness-diagram 作用域提供。
    body = re.sub(r"<style[^>]*>.*?</style>\s*", "", body, flags=re.S).strip()
    view = entry["view"]
    label = VIEW_LABEL.get(view, view)
    alt = html.escape(f"{cid} 見證圖:{label}", quote=True)
    out = '<section class="witness-section"><h3>見證圖 <small>GEO-131 · 由夾具經引擎推導,非條文</small></h3>'
    out += (f'<figure><svg class="witness-diagram" viewBox="{crop}" data-crop="{crop}" data-full="{full}" '
            # HTML 裡的內聯 SVG 不需要 xmlns(HTML 解析器自動放進 SVG 命名空間);
            # 寫了反而會踩到「零外部引用」那道 assert 的 https?:// 比對。
            f'preserveAspectRatio="xMidYMid meet" role="img" aria-label="{alt}">{body}</svg>')
    out += ('<figcaption>夾具 <code>' + html.escape(entry["scene"]) + '</code>(' + html.escape(entry["expect"]) + ',' + label + ')· '
            + html.escape(entry["gist"]) + '<br>條文為真則此圖不變;圖變即警報,由 <code>witness.py --check</code> 逐位元守住,同步器不重跑引擎。</figcaption>')
    if view != "all" and crop != full:
        # 內聯之後不必再放第二份圖:同一個 <svg> 換 viewBox 即可(省一半位元組)。
        out += ('<details class="three-views"><summary>展開三視圖</summary>'
                '<p class="hint">展開後上方的圖會切換成完整三視圖,收合即還原。</p></details>')
    out += '</figure></section>'
    return out


def render_block(block: dict, inline: str, comments: list[dict]) -> str:
    bid = html.escape(block["id"], quote=True)
    label = html.escape(block["label"])
    notes = "".join(static_note(c, block) for c in comments if c["target"]["blockId"] == block["id"])
    return (f'<div class="review-block" data-block-id="{bid}" id="block-{bid}"><p class="review-target">{inline}</p>'
            f'<div class="block-tools review-only" hidden=""><span>{label}</span><button aria-label="批註 {block["clauseId"]} {label}" '
            f'data-review-action="new" data-target="{bid}" type="button">＋ 批註這段<span class="block-count"></span></button></div>'
            f'<div class="inline-comments" data-notes-for="{bid}">{notes}</div></div>')


class TargetText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.targets = {}
        self.current_block = None
        self.target = None
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise ValueError("Duplicate DOM id: " + attrs["id"])
            self.ids.add(attrs["id"])
        if attrs.get("data-block-id"):
            self.current_block = attrs["data-block-id"]
        if "review-target" in attrs.get("class", "").split():
            self.target = self.current_block
            if self.target in self.targets:
                raise ValueError("Duplicate review target: " + self.target)
            self.targets[self.target] = ""
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append((tag, self.target))

    def handle_endtag(self, tag):
        if self.stack:
            popped = self.stack.pop()
            if popped[0] != tag:
                raise ValueError(f"Unbalanced HTML: {popped[0]} / {tag}")
            if self.target and not any(t == self.target for _, t in self.stack):
                self.target = None

    def handle_data(self, data):
        if self.target:
            self.targets[self.target] += data


def visible_text(source: str) -> str:
    class Text(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts = []
        def handle_data(self, value):
            self.parts.append(value)
    parser = Text()
    parser.feed(source)
    return "".join(parser.parts)


def validate(source: str, axiom: str, plain: str) -> dict:
    data = json.loads(script_text(source, "axiom-review-data"))
    clauses = json.loads(script_text(source, "clause-data"))
    normative = source_clauses(axiom)  # Read SSOT, never derive expected clauses from blocks.
    expected_plain = source_plain(plain, {c["id"] for c in normative})
    assert data["documentHash"] == digest(compact([[b["id"], b["source"], b["separator"]] for b in data["blocks"]])), "assert 1 documentHash"
    assert clauses == data["clauses"], "assert 2 dual JSON"
    assert [c["id"] for c in clauses] == [c["id"] for c in normative], "SSOT clause order"
    assert data["sourceFileSha256"] == digest(axiom), "SSOT file hash"
    assert data["plainFileSha256"] == digest(plain), "plain file hash"
    assert len({b["id"] for b in data["blocks"]}) == len(data["blocks"]), "unique block ids"
    by_id = {b["id"]: b for b in data["blocks"]}
    for actual, expected in zip(clauses, normative):
        assert actual["body"] == expected["body"], "SSOT full body: " + actual["id"]
        assert actual["plain"] == expected_plain[actual["id"]], "SSOT plain: " + actual["id"]
        assert actual["subs"] == subs_for(expected["body"]), "SSOT subclauses: " + actual["id"]
        assert actual["line"] == expected["line"], "SSOT line: " + actual["id"]
        for section in ("body", "plain"):
            blocks = [b for b in data["blocks"] if b["clauseId"] == actual["id"] and b["section"] == section]
            assert "".join(b["source"] + b["separator"] for b in blocks) == actual[section], "assert 3 blocks: " + actual["id"]
            assert blocks[-1]["separator"] == "", "final separator"
    parser = TargetText()
    parser.feed(source)
    editable = [b for b in data["blocks"] if b["editable"]]
    rendered = render_inline_with_reader(source, [b["source"] for b in editable], clauses)
    for block in data["blocks"]:
        assert "block-" + block["id"] in parser.ids, "Missing visible block: " + block["id"]
        assert digest(block["source"]) == block["sourceHash"], "assert 4 sourceHash: " + block["id"]
        assert digest(block["originalSource"]) == block["originalHash"], "original snapshot hash"
    for block, markup in zip(editable, rendered):
        assert parser.targets.get(block["id"]) == visible_text(markup), "assert 5 DOM: " + block["id"]
    for comment in data["comments"]:
        target = comment["target"]
        assert target["blockId"] in by_id, "comment anchor removed"
        assert target["section"] == by_id[target["blockId"]]["section"], "comment section changed"
        assert digest(target["sourceSnapshot"]) == target["sourceHash"], "comment snapshot changed"
    for cid in [c["id"] for c in clauses]:
        art = re.search(r'<article\b[^>]*(?<![\w-])id="' + re.escape(cid) + r'"[^>]*>.*?</article>', source, re.S)
        assert art, "missing article " + cid
        body_at, plain_at = art[0].find("original-section"), art[0].find("plain-section")
        assert 0 <= body_at < plain_at, "GEO-147 原文必須排在白話之前: " + cid
    assert not search_regressions(source), "GEO-142 搜尋行為: " + "; ".join(search_regressions(source))
    for mark in ('badge-trace', 'badge-hub', 'trace-section', 'data-trace='):
        assert mark in source, "GEO-139 追溯類功能又丟失了(GEO-120 連帶約束): " + mark
    assert not hardcoded_colors(source), "GEO-141 規則裡仍有寫死的色碼: " + "; ".join(hardcoded_colors(source)[:6])
    assert not color_contract_regressions(source), "reader color contract: " + "; ".join(color_contract_regressions(source))
    assert ".review-block>.block-tools{opacity:0" in source, "GEO-145 段落工具又變成常駐了"
    assert "pressTimer" in script_text(source, "reader-script"), "GEO-145 觸控長按沒了"
    assert 'class="toc-facets' in source, "GEO-149 篩選 chip 不見了"
    assert "facetMatch" in script_text(source, "reader-script"), "GEO-149 篩選條件沒接上 filterToc"
    assert 'id="workspace-witness"' in source, "GEO-138 右欄見證圖面板不見了"
    workspace_js = script_text(source, "workspace-script")
    assert len(re.findall(r"\bfunction\s+renderWitness\s*\(", workspace_js)) == 1, "QR5 見證圖函式必須唯一"
    assert len(re.findall(r"e\s*=>\s*renderWitness\s*\(e\.detail\s*&&\s*e\.detail\.id\)", workspace_js)) == 1, "QR5 見證圖 event handler 必須唯一"
    assert "草稿已保留" in script_text(source, "workspace-script"), "GEO-146 切分頁沒有保留草稿"
    assert "halfSheet()" in script_text(source, "workspace-script"), "GEO-148 中間寬度仍走全螢幕 modal"
    assert "body.half-sheet-open" in source, "GEO-148 半高 sheet 樣式不見了"
    review_js = script_text(source, "review-script")
    assert "reanchorConfirm" in review_js, "GEO-144 重新綁定沒有前後對照"
    assert "stale-actions" in review_js, "GEO-144 過期批註沒有就地動作"
    assert "將這則批註重新綁定到" not in review_js, "GEO-144 confirm() 還在"
    assert not geo120_regressions(source), "GEO-139 違反 GEO-120 拍板: " + "; ".join(geo120_regressions(source))
    counts = json.loads(script_text(source, COUNTS_ID))
    assert counts == reader_counts(source, clauses, data), "GEO-140 計數來源與資料不符"
    assert source.count('<svg class="witness-diagram"') == counts["witness"], "GEO-141 Q8 見證圖不是 inline svg"
    for sec in re.findall(r'<section class="witness-section">.*?</section>', source, re.S):
        assert "base64" not in sec, "GEO-141 Q8 見證圖還有 base64 酬載"
        assert "<style" not in sec, "GEO-141 Q8 圖的樣式內聯了,會汙染全域"
    assert not stale_counts(source, counts), "GEO-140 殘留硬編碼計數: " + "; ".join(stale_counts(source, counts))
    assert not re.search(r"https?://|<link\b|<script\b[^>]*\bsrc\s*=|@import", source, re.I), "external reader resource"
    return {"clauses": len(clauses), "blocks": len(data["blocks"]), "comments": len(data["comments"]), "witness": counts["witness"], "examples": counts["examples"], "textRevision": counts["textRevision"], "five_asserts": "pass", "independent_ssot": "pass", "patches": len(PATCHES), "counts_single_source": "pass", "geo120": "pass", "search": "pass", "color_tokens": "pass", "documentHash": data["documentHash"]}


def _patch_snippet(text: str, limit: int = 70) -> str:
    """把標記壓成一行,方便在錯誤訊息裡指名是哪一個補丁。"""
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[:limit] + "…"


class PatchLog:
    """這次同步套用了哪些補丁,以及每個補丁「套用後一定存在 / 一定不存在」的標記。

    為什麼需要它:補丁是對一份會演化的產物做文字替換,而「有沒有套用過」是用
    改前/改後的樣子判定的——被改的內容自己一變,判定就失效,補丁被**靜默跳過**。
    2026-09-20/21 這類失效發生了四次(CSS 注入兩次、見證圖 17→33、三向連結 89→136、
    `force()` 把 `changeMode()` 的同形尾巴誤判成「已套用」而整個跳過)。
    前三次靠冪等檢查接住,第四次靠人眼。冪等檢查只說「結果不對」,不說「哪個補丁失效」——
    登記簿補的正是後者。
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.present: list[tuple[str, str]] = []
        self.absent: list[tuple[str, str]] = []

    def expect_present(self, label: str, marker: str):
        if marker:
            self.present.append((label, marker))

    def expect_absent(self, label: str, marker: str):
        if marker:
            self.absent.append((label, marker))

    def verify(self, source: str) -> list[str]:
        bad = []
        for label, marker in self.present:
            if marker not in source:
                bad.append("補丁「%s」套用後應該看得到的內容不見了 → %s"
                           % (label, _patch_snippet(marker)))
        for label, marker in self.absent:
            if marker in source:
                bad.append("補丁「%s」應該刪掉的內容還在 → %s"
                           % (label, _patch_snippet(marker)))
        return bad

    def __len__(self):
        return len(self.present) + len(self.absent)


PATCHES = PatchLog()


def inject_css(template: str, css: str, marker: str) -> str:
    """把一段 CSS 併進既有的第一個 </style>。

    marker 必須是這段 css 裡確實存在的字串,否則守衛永遠不成立、每重建一次就再插一次。
    這個 bug 在 GEO-147 與 GEO-139 各踩過一次(守衛寫 `.plain-section>h3{`、
    實際插的是 `.plain-section>h3,.original-section>h3{`),所以改成由函式自己檢查。
    """
    if marker not in css:
        raise ValueError("inject_css:守衛字串不在 css 裡,守衛會失效 → " + marker)
    PATCHES.expect_present("CSS " + _patch_snippet(marker, 40), marker)
    if marker in template:
        return template
    return template.replace("</style>", css + "</style>", 1)


def force(text: str, old: str, new: str, label: str, marker: str | None = None) -> str:
    result = _force_result(text, old, new, label, marker)
    # All successful paths, including marker no-ops, share the same registration.
    if new == "":
        PATCHES.expect_absent(label, old)
    else:
        PATCHES.expect_present(label, marker if marker is not None else new)
    return result


def _force_result(text: str, old: str, new: str, label: str, marker: str | None) -> str:
    """冪等模板補丁:先找 old 換成 new;已經是 new 就不動;兩者都找不到 = 模板漂移,失敗不靜默略過。

    old 與 new 都必須在全文唯一。GEO-142 施工時踩過:new 的尾巴
    (`…sideNavigation());sync();`)剛好也出現在 changeMode() 裡,於是被誤判成「已套用」,
    補丁整個被跳過而沒有任何人知道。不唯一就是判準有問題,寧可失敗。
    """
    if marker is not None:
        if not marker or new.count(marker) != 1:
            raise ValueError("reader template patch (%s): 標記必須在改後字串中唯一" % label)
        # 同一段會被多個補丁先後修改時,old/new 都判定不了狀態(第二個補丁會把第一個的 new 改掉)。
        # 這時由呼叫端給一個「只要套用過就一定在」的標記。GEO-149 的 resetSearch 實際踩到:
        # apply_search_fixes 先加 keyboardIndex、apply_facets 再加 activeFacet,重建時兩邊都認不得。
        if marker in text:
            if text.count(marker) != 1:
                raise ValueError("reader template patch (%s): 已套用標記不唯一" % label)
            return text
        if old not in text:
            raise ValueError("reader template drift (%s): 找不到改前字串,也沒有已套用標記" % label)
        if not old or text.count(old) != 1:
            raise ValueError("reader template patch (%s): 改前字串不唯一" % label)
        return text.replace(old, new, 1)

    if new == "":
        # 刪除型:空字串在任何文字裡都「存在」,不能走下面的判定。
        # 刪不到就當作已經刪過(冪等);但仍要求存在時必須唯一,避免誤刪同形內容。
        if old in text:
            if text.count(old) != 1:
                raise ValueError("reader template patch (%s): 待刪字串出現 %d 次,不唯一" % (label, text.count(old)))
            return text.replace(old, "", 1)
        return text
    if old in new:
        # 追加式補丁(new 只是在 old 上加東西):old 永遠仍在 new 裡,只能用 new 判定是否已套用,
        # 否則每重建一次就再追加一次(GEO-142 的 renderSearchStatus() 實際踩到)。
        if new in text:
            if text.count(new) != 1:
                raise ValueError("reader template patch (%s): 改後字串出現 %d 次" % (label, text.count(new)))
            return text
        if text.count(old) != 1:
            raise ValueError("reader template patch (%s): 改前字串出現 %d 次,不唯一" % (label, text.count(old)))
        return text.replace(old, new, 1)
    if old in text:
        if text.count(old) != 1:
            raise ValueError("reader template patch (%s): 改前字串出現 %d 次,不唯一" % (label, text.count(old)))
        return text.replace(old, new, 1)
    if new in text:
        if text.count(new) != 1:
            raise ValueError("reader template patch (%s): 改後字串出現 %d 次,無法判定是否已套用" % (label, text.count(new)))
        return text
    raise ValueError("reader template drift (%s): 既不是改前也不是改後的樣子" % label)


HOVER_PREVIEW_JS = "\n    /* GEO-120 拍板二:hover 快速預覽與點擊固定參照欄並存。只在真的有 hover 的裝置上啟用。 */\n    (function(){\n      if(!(window.matchMedia&&window.matchMedia('(hover:hover)').matches))return;\n      var card=null,hideTimer=null;\n      function ensure(){\n        if(card)return card;\n        card=document.createElement('div');card.id='ref-preview';card.hidden=true;\n        card.setAttribute('role','tooltip');document.body.appendChild(card);return card;\n      }\n      function hide(){if(card)card.hidden=true;}\n      function show(a){\n        var id=a.dataset.ref.replace(/\\([a-z]\\)$/,'');var item=byId[id];if(!item)return;\n        var c=ensure();c.textContent='';\n        var head=document.createElement('b');head.textContent=id+' '+(item.title||'');\n        var body=String(item.body||'').replace(/\\*\\*/g,'').replace(/`/g,'').replace(/\\s+/g,' ').slice(0,150);\n        var text=document.createElement('span');text.textContent=body+(body.length>=150?'…':'');\n        c.appendChild(head);c.appendChild(text);c.hidden=false;\n        var r=a.getBoundingClientRect();\n        var left=Math.min(Math.max(8,r.left),Math.max(8,window.innerWidth-c.offsetWidth-8));\n        var top=r.bottom+8;\n        if(top+c.offsetHeight>window.innerHeight-8)top=Math.max(8,r.top-c.offsetHeight-8);\n        c.style.left=left+'px';c.style.top=top+'px';\n      }\n      document.addEventListener('mouseover',function(e){\n        var a=e.target&&e.target.closest?e.target.closest('a[data-ref]'):null;\n        clearTimeout(hideTimer);\n        if(!a){hideTimer=setTimeout(hide,150);return;}\n        show(a);\n      });\n      window.addEventListener('scroll',hide,{passive:true});\n      document.addEventListener('keydown',function(e){if(e.key==='Escape')hide();});\n    })();"


FACET_HELPER_JS = "\n    /* GEO-149:篩選 chip。與搜尋、分類篩選疊加,條件全部讀 toc-item 的 data-*(由資料算)。 */\n    function facetMatch(link){\n      if(!activeFacet)return true;\n      if(activeFacet==='note')return Number(link.dataset.note||0)>0;\n      if(activeFacet==='ex')return Number(link.dataset.ex||0)>0;\n      if(activeFacet==='wit')return Number(link.dataset.wit||0)>0;\n      if(activeFacet==='none')return link.dataset.trace==='none';\n      return true;\n    }"


WITNESS_PANE_JS = "\n /* GEO-138(🔒 Q4):右欄上半固定顯示「目前這一條」的見證圖,不與參照/批註互斥。\n    GEO-141(🔒 Q8):見證圖已是 inline <svg>,直接複製節點,不另存第二份酬載。 */\n function toast(text){\n  const t=document.getElementById('toast');if(!t)return;\n  t.textContent=text;t.hidden=false;\n  clearTimeout(toast._timer);toast._timer=setTimeout(()=>{t.hidden=true;},2200);\n }\n function renderWitness(id){\n  const pane=document.getElementById('workspace-witness');if(!pane)return;\n  const label=document.getElementById('workspace-witness-clause');\n  const holder=document.getElementById('workspace-witness-img');\n  const none=document.getElementById('workspace-witness-none');\n  const article=id?document.getElementById(id):null;\n  const source=article?article.querySelector('.witness-diagram'):null;\n  if(label)label.textContent=id||'';\n  holder.textContent='';\n  if(source){\n   const copy=source.cloneNode(true);copy.removeAttribute('id');\n   copy.setAttribute('viewBox',copy.dataset.crop||copy.getAttribute('viewBox'));\n   holder.appendChild(copy);holder.hidden=false;none.hidden=true;\n  }else{\n   holder.hidden=true;none.hidden=false;\n  }\n }\n document.addEventListener('axiom:current',e=>renderWitness(e.detail&&e.detail.id));\n /* GEO-141(Q8):展開三視圖 = 同一個 <svg> 換 viewBox,不放第二份圖。 */\n document.addEventListener('toggle',e=>{\n  const d=e.target;if(!d||!d.classList||!d.classList.contains('three-views'))return;\n  const fig=d.closest('figure');const svg=fig?fig.querySelector('.witness-diagram'):null;\n  if(!svg)return;\n  svg.setAttribute('viewBox',d.open?svg.dataset.full:svg.dataset.crop);\n },true);"


def apply_reanchor(template: str) -> str:
    """GEO-144(🔒 Q2):過期批註就地給「重新綁定這段」;confirm() 換成面板內前後對照 + 主鈕。"""
    js = script_text(template, "review-script")
    js = force(js, OLD_STALE, NEW_STALE, "過期批註就地動作")
    js = force(js, OLD_REANCHOR, NEW_REANCHOR, "重新綁定改前後對照")
    js = force(js, OLD_DISPATCH, NEW_DISPATCH, "重新綁定的 action 分派")
    return replace_script(template, "review-script", js)


def apply_half_sheet(template: str) -> str:
    """GEO-148(a):960–1279px 用非模態的底部半高 sheet 取代全螢幕 modal。"""
    js = script_text(template, "workspace-script")
    js = force(js,
               "const navQuery=window.matchMedia('(min-width:960px)'),dockQuery=window.matchMedia('(min-width:1280px)');",
               "const navQuery=window.matchMedia('(min-width:960px)'),dockQuery=window.matchMedia('(min-width:1280px)');\n"
               " /* GEO-148(🔒 Q6):中間寬度用非模態底部半高 sheet,正文同時可見也可操作。 */\n"
               " const halfQuery=window.matchMedia('(min-width:960px) and (max-width:1279px)');\n"
               " const halfSheet=()=>ready&&halfQuery.matches;",
               "halfQuery 宣告")
    js = force(js,
               " }else{if(!el.open)el.showModal();if(id==='review-dialog')document.body.classList.add('review-panel-open');}",
               " }else if(halfSheet()&&dialogs.includes(id)){\n"
               "  if(el.open&&el.matches(':modal'))el.close();\n"
               "  if(!el.open)el.show();\n"
               "  document.body.classList.add('half-sheet-open');\n"
               "  if(id==='review-dialog')document.body.classList.add('review-panel-open');\n"
               " }else{if(!el.open)el.showModal();if(id==='review-dialog')document.body.classList.add('review-panel-open');}",
               "底部半高 sheet")
    js = force(js, "\nfunction start(){",
               "\n /* sheet 關閉時把 body 的讓位 padding 收回來。 */\n"
               " dialogs.forEach(id=>{const d=document.getElementById(id);\n"
               "  if(d)d.addEventListener('close',()=>{\n"
               "   if(!dialogs.some(x=>{const o=document.getElementById(x);return o&&o.open;}))\n"
               "    document.body.classList.remove('half-sheet-open');});});\nfunction start(){",
               "sheet 關閉收回 padding", marker="half-sheet-open');});});")
    return replace_script(template, "workspace-script", js)


LEGACY_WITNESS_PANE_JS = """
 /* GEO-138(🔒 Q4):右欄上半固定顯示「目前這一條」的見證圖,不與參照/批註互斥。
    圖直接取自條文卡裡那張(同一個 data URI),不另存第二份。 */
 function toast(text){
  const t=document.getElementById('toast');if(!t)return;
  t.textContent=text;t.hidden=false;
  clearTimeout(toast._timer);toast._timer=setTimeout(()=>{t.hidden=true;},2200);
 }
 function renderWitness(id){
  const pane=document.getElementById('workspace-witness');if(!pane)return;
  const label=document.getElementById('workspace-witness-clause');
  const img=document.getElementById('workspace-witness-img');
  const none=document.getElementById('workspace-witness-none');
  const article=id?document.getElementById(id):null;
  const source=article?article.querySelector('.witness-section figure img'):null;
  if(label)label.textContent=id||'';
  if(source){
   img.src=source.getAttribute('src');img.alt=source.getAttribute('alt')||'';
   img.hidden=false;none.hidden=true;
  }else{
   img.removeAttribute('src');img.hidden=true;none.hidden=false;
  }
 }
 document.addEventListener('axiom:current',e=>renderWitness(e.detail&&e.detail.id));"""


def apply_witness_pane(template: str) -> str:
    """GEO-138 + GEO-146(🔒 Q4):右欄上半固定見證圖;下半維持 tab,但切換前先保留草稿。"""
    # 面板內容日後還會改,所以不用「改前/改後」判定(那會在內容一變就卡住,GEO-141 Q8 實際踩到)。
    # 改成:先把既有面板整段移除,再插一份當前版本——永遠冪等,也永遠是最新的。
    PATCHES.expect_present("見證圖面板(移除後重插)", 'id="workspace-witness"')
    template = re.sub(r'<section[^>]*id="workspace-witness"[^>]*>.*?</section>\n?', "", template, flags=re.S)
    anchor = '<div id="dock-hub"></div>\n<div aria-label="校對工作區" class="workspace-tabs" role="tablist">'
    if anchor not in template:
        raise ValueError("reader template drift:找不到右欄的 dock-hub / workspace-tabs 錨點")
    pane = ('<section aria-label="目前條文的見證圖" class="js-only" id="workspace-witness" hidden="">'
            '<h3>見證圖 <small id="workspace-witness-clause"></small></h3>'
            '<figure id="workspace-witness-img" hidden=""></figure>'
            '<p class="hint" id="workspace-witness-none" hidden="">'
            '這一條沒有見證圖。' +
            '</p></section>')
    template = template.replace(
        anchor,
        '<div id="dock-hub"></div>\n' + pane + '\n<div aria-label="校對工作區" class="workspace-tabs" role="tablist">',
        1)

    js = script_text(template, "workspace-script")
    # Retire only the known image/data-URI pane migration. Its function is dead
    # (shadowed by the SVG function), but its listener invokes the live function.
    js = force(js, LEGACY_WITNESS_PANE_JS, "", "退役 data URI 見證圖 handler")
    if ".witness-section figure img" in js:
        raise ValueError("reader template drift:歷史見證圖面板無法唯一退役")
    js = force(js, "\nfunction reflectTabs(){", WITNESS_PANE_JS.rstrip("\n") + "\nfunction reflectTabs(){",
               "見證圖面板腳本")
    # GEO-146:切走批註分頁前先保留草稿,並明確告知——否則寫到一半點條號就沒了。
    js = force(js,
               "function present(id){\n const el=$(id);el.hidden=false;\n if(docked()&&dialogs.includes(id)){\n",
               "function present(id){\n const el=$(id);el.hidden=false;\n if(docked()&&dialogs.includes(id)){\n"
               "  if(active==='review-dialog'&&id!=='review-dialog'&&window.axiomReviewUI&&window.axiomReviewUI.flushDraft){\n"
               "   window.axiomReviewUI.flushDraft();toast('草稿已保留');\n  }\n",
               "切分頁前保留草稿")
    js = force(js, "\nfunction start(){", "\nrenderWitness(document.body.dataset.currentClause||'D1');\nfunction start(){",
               "見證圖面板初始化", marker="renderWitness(document.body.dataset.currentClause")
    return replace_script(template, "workspace-script", js)


def apply_facets(template: str, clauses: list[dict], trace: dict, note_counts: dict,
                 example_counts: dict, witness_ids: set) -> str:
    """GEO-149:導覽頂端的篩選 chip。數量由資料算,與 GEO-140 的計數同一個來源精神。"""
    n_note = sum(1 for c in clauses if note_counts.get(c["id"], 0) > 0)
    n_ex = sum(1 for c in clauses if example_counts.get(c["id"], 0) > 0)
    n_wit = sum(1 for c in clauses if c["id"] in witness_ids)
    n_none = sum(1 for c in clauses if trace[c["id"]]["light"] == "none")
    chips = "".join(
        '<a data-facet="{k}" href="#{first}">{label}<b>{n}</b></a>'.format(
            k=key, first=clauses[0]["id"], label=label, n=count)
        for key, label, count in (("note", "有批註", n_note), ("ex", "有例圖", n_ex),
                                  ("wit", "有見證圖", n_wit), ("none", "無追溯", n_none)))
    markup = '<nav aria-label="依證據篩選" class="toc-facets js-only" hidden="">' + chips + "</nav>"
    anchor = '<a data-group="R" href="#R1">R 推演</a></nav>'
    # chip 上的數字是算出來的,會隨資料變。用 force() 判定「已套用」會看到舊的 markup 還在
    # 就直接返回,數字從此凍結在第一次建置的值(2026-09-21 被 test_facet_chips_are_data_driven 抓到:
    # 追溯資料變了,chip 仍寫 22、實際 21)。凡是內容會變的標記,一律先移除再插入。
    template = re.sub(r'<nav[^>]*class="toc-facets[^"]*"[^>]*>.*?</nav>', "", template, flags=re.S)
    if anchor not in template:
        raise ValueError("reader template drift:找不到分類篩選 nav 的錨點,無法放篩選 chip")
    PATCHES.expect_present("篩選 chip 標記", 'class="toc-facets')
    template = template.replace(anchor, anchor + markup, 1)

    js = script_text(template, "reader-script")
    js = force(js, "var activeGroup = '', visibleResults = [], keyboardIndex = -1;",
               "var activeGroup = '', activeFacet = '', visibleResults = [], keyboardIndex = -1;",
               "activeFacet 宣告")
    js = force(js, "function filterToc() {",
               FACET_HELPER_JS.strip("\n") + "\n    function filterToc() {",
               "facetMatch()")
    js = force(js,
               "var match=(!activeGroup||id.charAt(0)===activeGroup)&&index[id].indexOf(query)!==-1;",
               "var match=(!activeGroup||id.charAt(0)===activeGroup)&&facetMatch(link)&&index[id].indexOf(query)!==-1;",
               "篩選條件疊加")
    js = force(js,
               "groupLinks.forEach(function (link) {link.classList.toggle('active',link.dataset.group===activeGroup);});",
               "groupLinks.forEach(function (link) {link.classList.toggle('active',link.dataset.group===activeGroup);});"
               "Array.prototype.forEach.call(document.querySelectorAll('a[data-facet]'),"
               "function(link){link.classList.toggle('active',link.dataset.facet===activeFacet);});",
               "chip 選取態")
    js = force(js,
               "if(group){event.preventDefault();activeGroup=activeGroup===group.dataset.group?'':group.dataset.group;search.value='';filterToc();return;}",
               "if(group){event.preventDefault();activeGroup=activeGroup===group.dataset.group?'':group.dataset.group;search.value='';filterToc();return;}"
               "var facet=el.closest('a[data-facet]');"
               "if(facet){event.preventDefault();activeFacet=activeFacet===facet.dataset.facet?'':facet.dataset.facet;filterToc();return;}",
               "chip 點擊")
    js = force(js, "function resetSearch(){search.value='';activeGroup='';keyboardIndex=-1;filterToc();}",
               "function resetSearch(){search.value='';activeGroup='';activeFacet='';keyboardIndex=-1;filterToc();}",
               "重設也清掉 chip", marker="activeFacet='';keyboardIndex=-1;filterToc();}")
    return replace_script(template, "reader-script", js)


def apply_hover_preview(template: str) -> str:
    """GEO-139(2/4):還原 GEO-120 拍板二的 hover 快速預覽。接在長按處理之後。"""
    anchor = ("      ['touchend','touchmove','touchcancel'].forEach(function(ev){\n"
              "        document.addEventListener(ev,clearPress,{passive:true});});\n"
              "    })();")
    js = force(script_text(template, "reader-script"), anchor, anchor + HOVER_PREVIEW_JS, "hover 預覽")
    return replace_script(template, "reader-script", js)


def apply_long_press(template: str) -> str:
    """GEO-145:觸控裝置沒有 hover,用長按叫出段落工具。

    刻意**不** preventDefault——長按同時仍是瀏覽器的原生選字手勢,兩者並存;
    手指一移動就取消,避免捲動時誤觸。
    """
    anchor = ("document.addEventListener('keydown',function(e){if((e.ctrlKey||e.metaKey)"
              "&&e.key.toLowerCase()==='k'){e.preventDefault();openDirectory();search.focus();}});")
    handler = (anchor +
               "\n    /* GEO-145:觸控長按叫出段落工具(不攔截原生選字)。 */\n"
               "    (function(){var pressTimer=null,pressTarget=null;\n"
               "      function clearPress(){if(pressTimer){clearTimeout(pressTimer);pressTimer=null;}}\n"
               "      document.addEventListener('touchstart',function(e){\n"
               "        var block=e.target&&e.target.closest?e.target.closest('.review-block'):null;\n"
               "        if(!block)return;pressTarget=block;clearPress();\n"
               "        pressTimer=setTimeout(function(){\n"
               "          Array.prototype.forEach.call(document.querySelectorAll('.review-block.show-tools'),\n"
               "            function(n){if(n!==pressTarget)n.classList.remove('show-tools');});\n"
               "          if(pressTarget)pressTarget.classList.add('show-tools');\n"
               "        },500);\n"
               "      },{passive:true});\n"
               "      ['touchend','touchmove','touchcancel'].forEach(function(ev){\n"
               "        document.addEventListener(ev,clearPress,{passive:true});});\n"
               "    })();")
    js = force(script_text(template, "reader-script"), anchor, handler, "觸控長按")
    return replace_script(template, "reader-script", js)


def apply_search_fixes(template: str) -> str:
    """GEO-142:搜尋跳轉後保留查詢與命中清單;Enter 連續跳下一筆;狀態列顯示第 n / m 筆;
    Esc 第一下清查詢、第二下關閉。原本 navigate() 一進來就 resetSearch(),
    導致「搜尋 → 點第 2 筆 → 想看第 3 筆」必須重打整串關鍵字。"""
    js = script_text(template, "reader-script")

    js = force(
        js,
        "$('search-status').textContent=query?'找到 '+visibleResults.length+' 條 · 全部列出':(activeGroup?activeGroup+' 類別 · ':'全部 ')+visibleResults.length+' 條';",
        "searchStatusBase=query?'找到 '+visibleResults.length+' 條 · 全部列出':(activeGroup?activeGroup+' 類別 · ':'全部 ')+visibleResults.length+' 條';renderSearchStatus();",
        "搜尋狀態列")

    js = force(
        js,
        "function resetSearch(){search.value='';activeGroup='';filterToc();}",
        "var searchStatusBase='';\n"
        "    function renderSearchStatus(){"
        "$('search-status').textContent=searchStatusBase+"
        "((visibleResults.length&&keyboardIndex>=0)?' · 第 '+(keyboardIndex+1)+' / '+visibleResults.length+' 筆':'');}\n"
        "    function resetSearch(){search.value='';activeGroup='';keyboardIndex=-1;filterToc();}",
        "resetSearch 與狀態列渲染", marker="keyboardIndex=-1;filterToc();}")

    js = force(
        js,
        "closeDialogs();current=id;directory.open=!!(window.axiomWorkspace&&window.axiomWorkspace.sideNavigation());resetSearch();sync();",
        "closeDialogs();current=id;directory.open=!!(window.axiomWorkspace&&window.axiomWorkspace.sideNavigation());sync();",
        "navigate 不再清空搜尋")

    js = force(
        js,
        "var selected=visibleResults[keyboardIndex];selected.classList.add('key-active');",
        "var selected=visibleResults[keyboardIndex];selected.classList.add('key-active');renderSearchStatus();",
        "方向鍵更新第 n 筆")

    js = force(
        js,
        "if(e.key==='Enter'&&visibleResults.length){e.preventDefault();navigate(visibleResults[Math.max(0,keyboardIndex)].dataset.clause,true);search.blur();}",
        "if(e.key==='Enter'&&visibleResults.length){e.preventDefault();"
        "if(keyboardIndex<0)keyboardIndex=0;"
        "navigate(visibleResults[keyboardIndex].dataset.clause,true);"
        "keyboardIndex=(keyboardIndex+1)%visibleResults.length;"
        "tocLinks.forEach(function(l){l.classList.remove('key-active');});"
        "var nextHit=visibleResults[keyboardIndex];"
        "if(nextHit){nextHit.classList.add('key-active');nextHit.scrollIntoView({block:'nearest'});}"
        "renderSearchStatus();}",
        "Enter 連續跳下一筆")

    js = force(
        js,
        "if(e.key==='Escape'){e.preventDefault();directory.open=!!(window.axiomWorkspace&&window.axiomWorkspace.sideNavigation());search.blur();return;}",
        "if(e.key==='Escape'){e.preventDefault();"
        "if(search.value){resetSearch();return;}"
        "directory.open=!!(window.axiomWorkspace&&window.axiomWorkspace.sideNavigation());search.blur();return;}",
        "Esc 先清查詢再關閉")

    return replace_script(template, "reader-script", js)


def search_regressions(template: str) -> list[str]:
    """回傳搜尋行為仍不成立的項目;空清單才算通過。"""
    js = script_text(template, "reader-script")
    bad = []
    if "current=id;directory.open=!!(window.axiomWorkspace&&window.axiomWorkspace.sideNavigation());resetSearch();sync();" in js:
        bad.append("navigate() 仍會清空查詢字串(R7)")
    if "renderSearchStatus" not in js:
        bad.append("狀態列沒有第 n / m 筆")
    if "keyboardIndex=(keyboardIndex+1)%visibleResults.length" not in js:
        bad.append("Enter 不會連續跳下一筆")
    if "e.key.toLowerCase()==='k'" not in js:
        bad.append("沒有 Ctrl/⌘K 聚焦搜尋")
    return bad


def apply_geo120(template: str) -> str:
    """GEO-139:回歸 GEO-120(🔒 已拍板)被改掉的預設值。

    拍板一:單頁長捲,Ctrl+F 搜得到全文 → 預設 mode='all',不得首屏 hidden 掉其他條文。
    拍板三:雙主題、**深色為預設**,且保留 prefers-color-scheme 跟隨系統。
    """
    template = force(
        template,
        '<html lang="zh-Hant" data-theme="light"',
        '<html lang="zh-Hant" data-theme="dark"',
        "html data-theme 預設")

    js = script_text(template, "reader-script")
    js = force(
        js,
        "var current = 'D1', mode = 'single', fontSize = 18, theme = 'light';",
        "var current = 'D1', mode = 'all', fontSize = 18,\n"
        "        /* GEO-120 拍板三:深色為預設,系統明確偏好淺色時才跟著淺色。 */\n"
        "        theme = (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) ? 'light' : 'dark';",
        "mode/theme 初值")
    js = force(
        js,
        "if (saved.theme === 'dark') theme = 'dark';",
        "if (saved.theme === 'dark' || saved.theme === 'light') theme = saved.theme;",
        "已存主題的還原")
    template = replace_script(template, "reader-script", js)

    # 首屏靜態值要與 JS 初始化後一致,否則慢裝置會先閃一次錯的狀態(審查 R14)。
    template = re.sub(r'(id="reader-state"[^>]*>)[^<]*(<)',
                      lambda m: m[1] + "全文連續閱讀" + m[2], template, count=1)
    return template


def geo120_regressions(template: str) -> list[str]:
    """回傳仍違反 GEO-120 的項目;空清單才算通過(validate 與測試共用)。"""
    bad = []
    if 'data-theme="dark"' not in template.split(">", 1)[0] + ">":
        m = re.search(r"<html[^>]*>", template)
        if not m or 'data-theme="dark"' not in m[0]:
            bad.append("拍板三:預設主題不是深色")
    js = script_text(template, "reader-script")
    if not re.search(r"mode\s*=\s*'all'", js):
        bad.append("拍板一:mode 初值不是 'all',首屏會 hidden 掉其他條文,Ctrl+F 搜不到全文")
    if "prefers-color-scheme" not in js:
        bad.append("拍板三:沒有 prefers-color-scheme,不跟隨系統")
    if "ref-preview" not in js:
        bad.append("拍板二:沒有 hover 快速預覽(原文:砍掉 hover 是淨損失)")
    return bad


def clause_trace(clauses: list[dict], incoming: dict) -> dict:
    """每條的追溯資料:綠 = 原始碼且夾具、黃 = 其一、紅 = 皆無;樞紐 = 被引用數 >= 3。

    不得在此另立門檻。判準與出處見本檔 TRACE_CSS 上方的註解(GEO-167)。
    """
    ids = [c["id"] for c in clauses]
    code = axiom_matrix.code_sites(axiom_matrix.read_text(axiom_matrix.SRC), ids)
    scenes = axiom_matrix.scene_hits(ids)
    mutants = axiom_matrix.mutant_hits(ids)
    trace = {}
    for cid in ids:
        has_code, has_scene = bool(code[cid]), bool(scenes[cid])
        trace[cid] = {
            "light": "ok" if (has_code and has_scene) else ("partial" if (has_code or has_scene) else "none"),
            "functions": sorted({fn for fn, _ in code[cid]}),
            "scenes": sorted(scenes[cid]),
            "mutants": sorted(mutants[cid]),
            "incoming": len(incoming.get(cid, [])),
            "hub": len(incoming.get(cid, [])) >= 3,
        }
    return trace


def trace_section(cid: str, t: dict) -> str:
    """卡片底部的三向連結:原始碼 / 夾具 / 變異。內容全部由 axiom_matrix 推導,不手寫。"""
    rows = []
    if t["functions"]:
        rows.append("<div class=\"trace-row\"><b>原始碼</b>" + " ".join(
            "<code>%s</code>" % html.escape(fn) for fn in t["functions"][:6])
            + ("<span class=\"muted\">…共 %d 處</span>" % len(t["functions"]) if len(t["functions"]) > 6 else "")
            + "</div>")
    if t["scenes"]:
        rows.append("<div class=\"trace-row\"><b>夾具</b>" + " ".join(
            "<code>%s</code>" % html.escape(sc) for sc in t["scenes"][:6])
            + ("<span class=\"muted\">…共 %d 個</span>" % len(t["scenes"]) if len(t["scenes"]) > 6 else "")
            + "</div>")
    if t["mutants"]:
        rows.append("<div class=\"trace-row\"><b>變異</b><span>" + "、".join(t["mutants"]) + "</span></div>")
    if not rows:
        rows.append('<div class="trace-row"><span class="muted">這一條在原始碼與夾具裡都沒有留下可追溯的連結。'
                    '紅燈的意思是「沒有連結」,不等於「沒被測到」——補連結的做法是在夾具註解寫上條號,'
                    '不是去改條文(判準同 axiom_matrix.py)。</span></div>')
    return ('<details class="trace-section"><summary>三向連結 · 原始碼 / 夾具 / 變異</summary>'
            + "".join(rows) + "</details>")


def reader_counts(template: str, clauses: list[dict], state: dict) -> dict:
    """GEO-140:所有對讀者顯示的計數,只在這裡算一次。禁止任何地方再寫死數字。"""
    return {
        "clauses": len(clauses),
        "comments": len(state["comments"]),
        "blocks": len(state["blocks"]),
        "examples": template.count('<details class="examples'),
        "witness": template.count('<section class="witness-section">'),
        "textRevision": state["textRevision"],
    }


def apply_counts(template: str, counts: dict) -> str:
    """把 counts 寫進 #reader-counts,並用它填掉 HTML 靜態值與腳本裡的每一個計數。"""
    payload = safe_json(counts)
    if 'id="%s"' % COUNTS_ID in template:
        template = replace_script(template, COUNTS_ID, payload)
    else:
        tag = '<script id="%s" type="application/json">%s</script>\n' % (COUNTS_ID, payload)
        template = template.replace('<script id="clause-data"', tag + '<script id="clause-data"', 1)

    n, c = counts["clauses"], counts["comments"]
    rev = "文字 r%d" % counts["textRevision"]

    # 腳本內的計數:逐一取出該腳本再寫回,不對整份 template 做正則,避免動到 JSON 資料。
    reader_js = script_text(template, "reader-script")
    reader_js = re.sub(r"(已顯示全部 )\d+( 條)", lambda m: m[1] + str(n) + m[2], reader_js)
    template = replace_script(template, "reader-script", reader_js)

    ws_js = script_text(template, "workspace-script")
    ws_js = re.sub(r"(#workspace-position'\)\.textContent=')\d+ / \d+(')",
                   lambda m: m[1] + "1 / %d" % n + m[2], ws_js)
    template = replace_script(template, "workspace-script", ws_js)

    # HTML 靜態值:只動 <script id="clause-data"> 之前的顯示區。
    cut = template.index('<script id="%s"' % COUNTS_ID)
    head, tail = template[:cut], template[cut:]
    subs = [
        (r'(id="workspace-witness-none"[^>]*>)[^<]*(<)',
         lambda m: m[1] + "這一條沒有見證圖(%d 條中有 %d 條有)。" % (n, counts["witness"]) + m[2]),
        (r"<title>[^<]*</title>", "<title>公理層 · %s · %d 條 · %d 則批註</title>" % (rev, n, c)),
        (r'(id="review-revision">)[^<]*(<)', lambda m: m[1] + rev + m[2]),
        (r'(id="review-count">)\d+(<)', lambda m: m[1] + str(c) + m[2]),
        (r'(id="workspace-position">)[^<]*(<)', lambda m: m[1] + "1 / %d" % n + m[2]),
        (r'(id="read-position">)[^<]*(<)', lambda m: m[1] + "1 / %d" % n + m[2]),
        (r"文字 r\d+ 也不是專案的正式版號", "%s 也不是專案的正式版號" % rev),
        (r"\b\d+ 條規範", "%d 條規範" % n),
        (r"全部 \d+ 條", "全部 %d 條" % n),
        (r'(class="directory-count">)\d+ 條', lambda m: m[1] + "%d 條" % n),
        (r"此檔內含 \d+ 則批註", "此檔內含 %d 則批註" % c),
    ]
    for pattern, value in subs:
        head = re.sub(pattern, value, head)
    return head + tail


def stale_counts(template: str, counts: dict) -> list[str]:
    """回傳仍與資料不符的計數字樣;空清單才算通過(validate 與測試共用)。"""
    n, c = counts["clauses"], counts["comments"]
    bad = []
    title = re.search(r"<title>([^<]*)</title>", template)
    want = "公理層 · 文字 r%d · %d 條 · %d 則批註" % (counts["textRevision"], n, c)
    if not title or title[1] != want:
        bad.append("title=%r 應為 %r" % (title[1] if title else None, want))
    for label, pattern, expect in [
        ("workspace-witness-none", r'id="workspace-witness-none"[^>]*>([^<]*)<',
         "這一條沒有見證圖(%d 條中有 %d 條有)。" % (n, counts["witness"])),
        ("read-position", r'id="read-position">([^<]*)<', "1 / %d" % n),
        ("workspace-position", r'id="workspace-position">([^<]*)<', "1 / %d" % n),
        ("review-count", r'id="review-count">([^<]*)<', str(c)),
        ("review-revision", r'id="review-revision">([^<]*)<', "文字 r%d" % counts["textRevision"]),
    ]:
        m = re.search(pattern, template)
        if not m or m[1].strip() != expect:
            bad.append("%s=%r 應為 %r" % (label, m[1] if m else None, expect))
    for label, script, pattern, expect in [
        ("toast", "reader-script", r"已顯示全部 (\d+) 條", str(n)),
        ("ws-init", "workspace-script", r"#workspace-position'\)\.textContent='\d+ / (\d+)'", str(n)),
    ]:
        m = re.search(pattern, script_text(template, script))
        if not m or m[1] != expect:
            bad.append("%s=%r 應為 %r" % (label, m[1] if m else None, expect))
    return bad


def rebuild(template: str, axiom: str, plain: str, review=None) -> str:
    PATCHES.reset()
    state = json.loads(script_text(template, "axiom-review-data"))
    old = copy.deepcopy(state)
    if review is not None:
        if review.get("schema") != state["schema"] or review.get("documentId") != state["documentId"] or review.get("baseDocumentHash") != state["baseDocumentHash"]:
            raise ValueError("Review backup belongs to a different document/base")
        # Conflicting edits require an explicit decision; never discard a review version.
        for field in ("comments", "proposals", "revisions"):
            known = {x["id"]: x for x in state[field]}
            for value in review.get(field, []):
                if value["id"] in known and value != known[value["id"]]:
                    raise ValueError("Conflicting review record: " + value["id"])
                if value["id"] not in known:
                    state[field].append(copy.deepcopy(value))
                    # GEO-155:剛收下的紀錄也要記進 known。
                    # 不更新的話,同一份備份裡兩筆同 ID 異內容會**兩筆都被收下**——
                    # 閱讀器出現兩則同 ID 批註,而五道完整性 assert 不檢查批註集合的唯一性。
                    known[value["id"]] = value
        if review.get("draft"):
            if state.get("draft") and state["draft"] != review["draft"]:
                raise ValueError("Conflicting unsent review drafts; export both before merging")
            state["draft"] = copy.deepcopy(review["draft"])
    clauses = source_clauses(axiom)
    plain_by_id = source_plain(plain, {x["id"] for x in clauses})
    for c in clauses:
        c["plain"] = plain_by_id[c["id"]]
        c["subs"] = subs_for(c["body"])
    # All clause families support suffixes: I7a and I8a must not link to I7 / I8.
    template = template.replace(r"D\d+[a-z]?|I\d+|R\d+", r"[DIR]\d+[a-z]?")
    blocks = []
    for c in clauses:
        blocks += new_blocks(c, "plain", old["blocks"])
        blocks += new_blocks(c, "body", old["blocks"])
        blocks += [copy.deepcopy(b) for b in old["blocks"] if b["clauseId"] == c["id"] and b["section"] == "example"]
    state["blocks"] = blocks
    state["clauses"] = clauses
    state["documentHash"] = digest(compact([[b["id"], b["source"], b["separator"]] for b in blocks]))
    state["sourceFileSha256"] = digest(axiom)
    state["plainFileSha256"] = digest(plain)
    state["baseFileName"] = CANONICAL.name
    state["baseLabel"] = "桌面 / 手機共用 · 語意校對"
    state["generator"] = {"name": "sync_axiom_reader.py", "version": 1, "source": "公理層.md", "plain": "geometry-guide/公理層-白話.md"}
    review_changed = any(state[field] != old[field] for field in ("comments", "proposals", "revisions", "draft"))
    text_changed = state["documentHash"] != old["documentHash"]
    if text_changed:
        state["textRevision"] = old["textRevision"] + 1
    if text_changed or review_changed:
        state["parentSnapshotId"] = old["snapshotId"]
        state["snapshotId"] = "ssot-" + digest(state["documentHash"] + compact([state[field] for field in ("comments", "proposals", "revisions", "draft")]))[:20]
        state["reviewSequence"] = old["reviewSequence"] + int(review_changed)
        # Deterministic metadata: keep prior review event dates, don't invent approval events.
    editable = [b for b in blocks if b["editable"]]
    markup = dict(zip([b["id"] for b in editable], render_inline_with_reader(template, [b["source"] for b in editable], clauses)))
    old_articles = {m[1]: m[0] for m in re.finditer(r'<article\b[^>]*(?<![\w-])id="([DIR]\d+[a-z]?)"[^>]*>.*?</article>', template, re.S)}
    incoming = {c["id"]: [] for c in clauses}
    for c in clauses:
        for ref in sorted({m[1] for m in CLAUSE_REF.finditer(c["body"]) if m[1] != c["id"]}):
            incoming[ref].append(c["id"])
    witness_manifest = load_witness_manifest()
    template = inject_css(template, WITNESS_CSS, ".witness-section{")
    template = inject_css(template, REANCHOR_CSS, ".stale-actions{display:flex")
    template = inject_css(template, WITNESS_DIAGRAM_CSS, ".witness-diagram .role-boundary{")
    template = inject_css(template, SHEET_CSS, "body.half-sheet-open{padding-bottom:52dvh}")
    template = inject_css(template, WITNESS_PANE_CSS, "#workspace-witness{display:none}")
    template = inject_css(template, FACET_CSS, ".toc-facets{display:flex")
    template = inject_css(template, REF_PREVIEW_CSS, "#ref-preview{position:fixed")
    template = inject_css(template, BLOCK_TOOLS_CSS, ".review-block>.block-tools{opacity:0")
    template = inject_css(template, TRACE_CSS, "--trace-ok:")
    template = inject_css(template, CLAUSE_LABEL_CSS, ".plain-section>h3,.original-section>h3{")
    trace = clause_trace(clauses, incoming)
    note_counts = {}
    for note in state["comments"]:
        owner = str(note.get("target", {}).get("blockId", "")).split(".")[0]
        note_counts[owner] = note_counts.get(owner, 0) + 1
    example_counts = {m[1]: len(re.findall(r'<details class="ex ', m[0]))
                      for m in ((art, cid_) for cid_, art in old_articles.items())}

    articles = []
    previous_group = None
    for index, c in enumerate(clauses):
        cid = c["id"]
        group = cid[0]
        if group != previous_group:
            articles.append(f'<h2 class="group-heading" id="group-{group}">{group} / {GROUPS[group]}</h2>')
            previous_group = group
        prior = old_articles.get(cid, "")
        # Preserve old example markup, images and identities verbatim; explicitly not proof.
        examples = ""
        if prior:
            start = prior.find('<details class="examples')
            # 終點取 GENERATED_SECTIONS 裡最早出現者。那些區塊每次重建都重新產生,
            # 絕不能被當成「歷史範例」保留下來——否則每重建一次就多一份。
            # 踩過兩次:GEO-147(見證圖 17→33)、GEO-139(三向連結 89→136)。
            # 新增任何每次重新產生的區塊時,務必同步加進 GENERATED_SECTIONS。
            ends = [e for e in (prior.find(mark) for mark in GENERATED_SECTIONS) if e > start]
            end = min(ends) if ends else -1
            if start >= 0 and end > start:
                examples = prior[start:end]
        if examples:
            examples = '<p class="hint history-example-note">以下為保留的歷史範例與例圖，未依本次條文重新執行，不作為本次功能驗收證據。</p>' + examples
        title = html.escape(c["title"])
        article = f'<article aria-labelledby="title-{cid}" class="clause" data-clause-id="{cid}" data-position="{index + 1}" data-source-line="{c["line"]}" data-title="{html.escape(c["title"], quote=True)}" id="{cid}">'
        t = trace[cid]
        badges = (f'<span class="clause-badges">'
                  f'<span class="badge-trace" data-trace="{t["light"]}" title="追溯燈號:{TRACE_LABEL[t["light"]]}">{TRACE_LABEL[t["light"]]}</span>'
                  + (f'<span class="badge-hub" title="樞紐:被 {t["incoming"]} 條引用">樞紐</span>' if t["hub"] else "")
                  + '</span>')
        article += f'<header class="clause-header"><div class="clause-meta"><span class="clause-id">{cid} / {GROUPS[group]}</span>{badges}<span>{index + 1} / {len(clauses)}</span></div><h2 id="title-{cid}">{title}</h2></header>'
        # GEO-147(🔒 2026-09-20):原文在前。理由不是舊設計規格(已作廢),而是頁尾自己寫「原文為準」、
        # 公理層.md 是 SSOT、白話明標非條文——版面順序必須與這個事實一致。
        # 只改這裡的呈現順序;blocks 陣列順序(plain 先)不動,否則 documentHash 與批註錨點會無故失效。
        for section, klass, heading, small in [("body", "original", "條文原文", f"公理層.md · L{c['line']}"), ("plain", "plain", "白話解釋", "輔助閱讀，非條文")]:
            article += f'<section class="{klass}-section"><h3>{heading} <small>{small}</small></h3><div class="copy {klass}-copy">'
            article += "".join(render_block(b, markup[b["id"]], state["comments"]) for b in blocks if b["clauseId"] == cid and b["section"] == section)
            article += '</div></section>'
        article += examples or '<p class="hint">本條尚無閱讀器內建執行範例；實作驗收另見專案測試記錄。</p>'
        article += witness_figure(cid, witness_manifest)
        article += trace_section(cid, t)
        links = "".join(f'<a class="reference-link" data-ref="{ref}" href="#{ref}">{ref}</a>' for ref in incoming[cid])
        article += '<section class="relation-section"><h3>被哪些條文引用</h3><div class="relation-links">' + (links or '<span class="muted">目前沒有其他條文引用。</span>') + '</div></section>'
        footer = (f'<a href="#{clauses[index - 1]["id"]}">上條 {clauses[index - 1]["id"]}</a>' if index else "") + '<a href="#contents">回目錄</a>'
        if index + 1 < len(clauses):
            footer += f'<a href="#{clauses[index + 1]["id"]}">下條 {clauses[index + 1]["id"]}</a>'
        article += '<footer class="clause-footer">' + footer + '</footer></article>'
        articles.append(article)
    template, count = re.subn(r'(<main\b[^>]*(?<![\w-])id="document"[^>]*>).*?(</main>)', lambda m: m[1] + "\n".join(articles) + m[2], template, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Canonical document container missing")
    for group, label in GROUPS.items():
        items = [c for c in clauses if c["id"].startswith(group)]
        toc = f'<section class="toc-group" id="toc-{group}"><h2>{group} · {label} / {len(items)} 條</h2>'
        # GEO-139(4)+GEO-149:左邊 4px 追溯燈號;右邊標出這一條有幾個範例、有沒有見證圖。
        # data-* 全部由資料算,不得出現硬編碼條號白名單。
        def toc_item(c):
            t, cid_ = trace[c["id"]], c["id"]
            ex = example_counts.get(cid_, 0)
            wit = 1 if cid_ in witness_manifest and (WITNESS_DIR / f"{cid_}.svg").exists() else 0
            evidence = []
            if ex:
                evidence.append(f"例 {ex}")
            if wit:
                evidence.append("見證圖")
            return (f'<a class="toc-item" data-clause="{cid_}" data-trace="{t["light"]}" '
                    f'data-ex="{ex}" data-wit="{wit}" data-hub="{1 if t["hub"] else 0}" '
                    f'data-note="{note_counts.get(cid_, 0)}" href="#{cid_}">'
                    f'<span class="clause-no">{cid_}</span>'
                    f'<span class="toc-title">{html.escape(c["title"])}</span>'
                    + (f'<span class="toc-evidence">{" · ".join(evidence)}</span>' if evidence else "")
                    + '</a>')
        toc += "".join(toc_item(c) for c in items) + '</section>'
        template, count = re.subn(r'<section class="toc-group" id="toc-' + group + r'">.*?</section>', lambda _: toc, template, count=1, flags=re.S)
        if count != 1:
            raise ValueError("TOC group missing")
    # Reader edits must rebuild subclauses from the canonical source block, not old originalSub.
    template = apply_witness_pane(template)
    # GEO-148:中間寬度的底部半高 sheet。
    template = apply_half_sheet(template)
    # GEO-144:過期批註就地重新綁定。
    template = apply_reanchor(template)
    template = apply_facets(template, clauses, trace, note_counts, example_counts,
                           {wid for wid in witness_manifest
                            if (WITNESS_DIR / f"{wid}.svg").exists()})
    review_script = script_text(template, "review-script")
    old_sub_sync = "for(const b of state.blocks.filter(b=>b.clauseId===item.id&&b.section==='body'&&b.sub)){if(b.source===b.originalSource&&b.originalSub!==null){item.subs[b.sub]=b.originalSub;}else if(b.source!==b.originalSource){item.subs[b.sub]=b.source.replace(/^\\s*\\([a-z]\\)\\s*/,'');}}"
    new_sub_sync = "item.subs={};for(const b of state.blocks.filter(b=>b.clauseId===item.id&&b.section==='body'&&b.sub)){item.subs[b.sub]=b.source.replace(/^\\s*\\([a-z]\\)\\s*/,'');}"
    review_script = review_script.replace(old_sub_sync, new_sub_sync)
    template = replace_script(template, "review-script", review_script)
    template = replace_script(template, "clause-data", safe_json(clauses))
    template = replace_script(template, "axiom-review-data", safe_json(state))
    # GEO-139:先回歸 GEO-120 的拍板預設值,再算計數(兩者都會動 reader-script)。
    template = apply_geo120(template)
    # GEO-141:色彩 token 化(批註四色、圖面底色、焦點環)。
    template = apply_color_tokens(template)
    # GEO-142:搜尋跳轉不清空查詢;Enter 連跳下一筆。
    template = apply_search_fixes(template)
    # GEO-145:觸控長按叫出段落工具。
    template = apply_long_press(template)
    # GEO-139(2/4):hover 快速預覽(GEO-120 拍板二)。
    template = apply_hover_preview(template)
    # GEO-140:所有計數由 reader_counts() 算一次,apply_counts() 填進 HTML 與腳本;此處不再寫死數字。
    template = apply_counts(template, reader_counts(template, clauses, state))
    script_start = template.index('<script id="clause-data"')
    head, tail = template[:script_start], template[script_start:]
    status = "本分支的跨面共用基準條文仍為審閱提案，尚未合併正式版本。" if "跨面共用基準分支提案" in axiom else "條文與白話已由目前專案來源同步；歷史批註保留原始快照。"
    banner = '<p class="hint" id="reader-source-status">' + status + '</p>'
    if 'id="reader-source-status"' in head:
        head = re.sub(r'<p class="hint" id="reader-source-status">.*?</p>', lambda _: banner, head)
    else:
        head = head.replace('<main aria-label="公理層完整條文"', banner + '<main aria-label="公理層完整條文"', 1)
    result = head + tail
    drifted = PATCHES.verify(result)
    if drifted:
        raise ValueError(
            "同步套用了 %d 個補丁,其中 %d 個沒有生效(補丁被靜默跳過是這個管線最常見的失效):\n  - %s"
            % (len(PATCHES), len(drifted), "\n  - ".join(drifted)))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify existing canonical reader against current source")
    parser.add_argument("--review-json", type=Path, help="Merge a same-base exported review backup; conflicting records reject")
    args = parser.parse_args()
    source = CANONICAL.read_text(encoding="utf-8")
    axiom = AXIOM.read_text(encoding="utf-8")
    plain = PLAIN.read_text(encoding="utf-8")
    if not args.check:
        review = json.loads(args.review_json.read_text(encoding="utf-8")) if args.review_json else None
        source = rebuild(source, axiom, plain, review)
        report = validate(source, axiom, plain)
        # Validate first; replace only the one canonical artifact.
        temporary = CANONICAL.with_suffix(".tmp")
        temporary.write_text(source, encoding="utf-8")
        temporary.replace(CANONICAL)
    else:
        report = validate(source, axiom, plain)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
