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
CLAUSE_START = re.compile(r"^(?:\*\*)?([DIR]\d+[a-z]?)\s+", re.M)
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
# 改用批註版正典時整組掉了(全檔 grep 為 0)。定義沿用專案原本的 make_axiom_reader.py:431-433,
# 不自己發明門檻——綠=原始碼且夾具、黃=其一、紅=皆無;樞紐=被引用數 >= 3。
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


def apply_color_tokens(template: str) -> str:
    """把 token 定義併進 :root / :root[data-theme=dark],再把規則裡寫死的色碼換成 token。"""
    light = "".join("%s:%s;" % (k, v[0]) for k, v in COLOR_TOKENS.items() if v[0])
    dark = "".join("%s:%s;" % (k, v[1]) for k, v in COLOR_TOKENS.items() if v[1])
    template = force(template, "--bar:68px}", "--bar:68px;" + light.rstrip(";") + "}", "淺色 token")
    template = force(template, "--code:#293640}", "--code:#293640;" + dark.rstrip(";") + "}", "深色 token")
    for old_css, new_css in COLOR_REWRITES:
        template = force(template, old_css, new_css, "色碼→token: " + new_css[:40])
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

    def data_uri(view_box: str) -> str:
        doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" data-full="{full}" '
               f'preserveAspectRatio="xMidYMid meet">{WITNESS_STYLE}{body}</svg>')
        return "data:image/svg+xml;base64," + base64.b64encode(doc.encode("utf-8")).decode("ascii")

    view = entry["view"]
    label = VIEW_LABEL.get(view, view)
    alt = html.escape(f"{cid} 見證圖:{label}", quote=True)
    out = '<section class="witness-section"><h3>見證圖 <small>GEO-131 · 由夾具經引擎推導,非條文</small></h3>'
    out += f'<figure><img alt="{alt}" class="scene-diagram witness-diagram" decoding="async" loading="lazy" src="{data_uri(crop)}">'
    out += ('<figcaption>夾具 <code>' + html.escape(entry["scene"]) + '</code>(' + html.escape(entry["expect"]) + ',' + label + ')· '
            + html.escape(entry["gist"]) + '<br>條文為真則此圖不變;圖變即警報,由 <code>witness.py --check</code> 逐位元守住,同步器不重跑引擎。</figcaption>')
    if view != "all" and crop != full:
        out += f'<details><summary>展開三視圖</summary><img alt="{html.escape(cid + " 見證圖:三視圖", quote=True)}" class="scene-diagram witness-diagram" decoding="async" loading="lazy" src="{data_uri(full)}"></details>'
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
    assert ".review-block>.block-tools{opacity:0" in source, "GEO-145 段落工具又變成常駐了"
    assert "pressTimer" in script_text(source, "reader-script"), "GEO-145 觸控長按沒了"
    assert not geo120_regressions(source), "GEO-139 違反 GEO-120 拍板: " + "; ".join(geo120_regressions(source))
    counts = json.loads(script_text(source, COUNTS_ID))
    assert counts == reader_counts(source, clauses, data), "GEO-140 計數來源與資料不符"
    assert not stale_counts(source, counts), "GEO-140 殘留硬編碼計數: " + "; ".join(stale_counts(source, counts))
    assert not re.search(r"https?://|<link\b|<script\b[^>]*\bsrc\s*=|@import", source, re.I), "external reader resource"
    return {"clauses": len(clauses), "blocks": len(data["blocks"]), "comments": len(data["comments"]), "witness": counts["witness"], "examples": counts["examples"], "textRevision": counts["textRevision"], "five_asserts": "pass", "independent_ssot": "pass", "counts_single_source": "pass", "geo120": "pass", "search": "pass", "color_tokens": "pass", "documentHash": data["documentHash"]}


def inject_css(template: str, css: str, marker: str) -> str:
    """把一段 CSS 併進既有的第一個 </style>。

    marker 必須是這段 css 裡確實存在的字串,否則守衛永遠不成立、每重建一次就再插一次。
    這個 bug 在 GEO-147 與 GEO-139 各踩過一次(守衛寫 `.plain-section>h3{`、
    實際插的是 `.plain-section>h3,.original-section>h3{`),所以改成由函式自己檢查。
    """
    if marker not in css:
        raise ValueError("inject_css:守衛字串不在 css 裡,守衛會失效 → " + marker)
    if marker in template:
        return template
    return template.replace("</style>", css + "</style>", 1)


def force(text: str, old: str, new: str, label: str) -> str:
    """冪等模板補丁:先找 old 換成 new;已經是 new 就不動;兩者都找不到 = 模板漂移,失敗不靜默略過。

    old 與 new 都必須在全文唯一。GEO-142 施工時踩過:new 的尾巴
    (`…sideNavigation());sync();`)剛好也出現在 changeMode() 裡,於是被誤判成「已套用」,
    補丁整個被跳過而沒有任何人知道。不唯一就是判準有問題,寧可失敗。
    """
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
        "resetSearch 與狀態列渲染")

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
    """每條的追溯資料。定義沿用 make_axiom_reader.py:431-433,不得在此另立門檻。"""
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
    template = inject_css(template, REF_PREVIEW_CSS, "#ref-preview{position:fixed")
    template = inject_css(template, BLOCK_TOOLS_CSS, ".review-block>.block-tools{opacity:0")
    template = inject_css(template, TRACE_CSS, "--trace-ok:")
    template = inject_css(template, CLAUSE_LABEL_CSS, ".plain-section>h3,.original-section>h3{")
    trace = clause_trace(clauses, incoming)
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
                    f'data-ex="{ex}" data-wit="{wit}" data-hub="{1 if t["hub"] else 0}" href="#{cid_}">'
                    f'<span class="clause-no">{cid_}</span>'
                    f'<span class="toc-title">{html.escape(c["title"])}</span>'
                    + (f'<span class="toc-evidence">{" · ".join(evidence)}</span>' if evidence else "")
                    + '</a>')
        toc += "".join(toc_item(c) for c in items) + '</section>'
        template, count = re.subn(r'<section class="toc-group" id="toc-' + group + r'">.*?</section>', lambda _: toc, template, count=1, flags=re.S)
        if count != 1:
            raise ValueError("TOC group missing")
    # Reader edits must rebuild subclauses from the canonical source block, not old originalSub.
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
    return head + tail


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
