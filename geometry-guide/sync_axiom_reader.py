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
ROOT = HERE.parent
CANONICAL = HERE / "公理層-閱讀器.html"
AXIOM = ROOT / "公理層.md"
PLAIN = HERE / "公理層-白話.md"
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
    assert not re.search(r"https?://|<link\b|<script\b[^>]*\bsrc\s*=|@import", source, re.I), "external reader resource"
    return {"clauses": len(clauses), "blocks": len(data["blocks"]), "comments": len(data["comments"]), "witness": source.count('<section class="witness-section">'), "five_asserts": "pass", "independent_ssot": "pass", "documentHash": data["documentHash"]}


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
    if ".witness-section{" not in template:
        template = template.replace("</style>", WITNESS_CSS + "</style>", 1)
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
            end = prior.find('<section class="relation-section"')
            if start >= 0 and end > start:
                examples = prior[start:end]
        if examples:
            examples = '<p class="hint history-example-note">以下為保留的歷史範例與例圖，未依本次條文重新執行，不作為本次功能驗收證據。</p>' + examples
        title = html.escape(c["title"])
        article = f'<article aria-labelledby="title-{cid}" class="clause" data-clause-id="{cid}" data-position="{index + 1}" data-source-line="{c["line"]}" data-title="{html.escape(c["title"], quote=True)}" id="{cid}">'
        article += f'<header class="clause-header"><div class="clause-meta"><span class="clause-id">{cid} / {GROUPS[group]}</span><span>{index + 1} / {len(clauses)}</span></div><h2 id="title-{cid}">{title}</h2></header>'
        for section, klass, heading, small in [("plain", "plain", "白話解釋", "輔助閱讀，非條文"), ("body", "original", "條文原文", f"公理層.md · L{c['line']}")]:
            article += f'<section class="{klass}-section"><h3>{heading} <small>{small}</small></h3><div class="copy {klass}-copy">'
            article += "".join(render_block(b, markup[b["id"]], state["comments"]) for b in blocks if b["clauseId"] == cid and b["section"] == section)
            article += '</div></section>'
        article += witness_figure(cid, witness_manifest)
        article += examples or '<p class="hint">本條尚無閱讀器內建執行範例；實作驗收另見專案測試記錄。</p>'
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
        toc += "".join(f'<a class="toc-item" data-clause="{c["id"]}" href="#{c["id"]}"><span class="clause-no">{c["id"]}</span><span class="toc-title">{html.escape(c["title"])}</span></a>' for c in items) + '</section>'
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
    # Update only display text outside scripts: source strings and review history remain exact.
    script_start = template.index('<script id="clause-data"')
    head, tail = template[:script_start], template[script_start:]
    head = re.sub(r"\b\d+ 條規範", f"{len(clauses)} 條規範", head)
    head = re.sub(r"全部 \d+ 條", f"全部 {len(clauses)} 條", head)
    head = re.sub(r'(class="directory-count">)\d+ 條', lambda m: m[1] + f"{len(clauses)} 條", head)
    head = re.sub(r"此檔內含 \d+ 則批註", f"此檔內含 {len(state['comments'])} 則批註", head)
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
