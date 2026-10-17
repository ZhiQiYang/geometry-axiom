#!/usr/bin/env python3
"""Check that PROPOSAL.md's quotes of the current SSOT are verbatim and sit on the cited lines, and that its
"改後" text applies cleanly.

PROPOSAL.md quotes the text it wants to change ("改前") and cites where it lives.  Line numbers rot every
time main moves (they already rotted once: a898ad6e -> c144c013, after the K/M/W/H layering).  This script
re-derives the truth from the files instead of trusting the proposal.

Labels it reads from PROPOSAL.md.  For the first three kinds the quote is the block-quote lines right below:

    改前(公理層.md D29 第 625 行):                          text to be replaced; must be on exactly that line
    改前(公理層.md R18 第 2078–2079 行):                    multi-line quote, first line ends / last line starts it
    現況(公理層.md I23 第 1358 行):                         text that stays as it is, cited as evidence; same checks
    現況(公理層.md 分層前言 第 65 行):                      a line of the layering preface (above the first clause)
    新增於(白話版 R18 第 743 行「只看外輪廓…」之後):         insertion anchor: that line must begin with the text;
                                                            the block below is inserted as a new line after it
    新增於(白話版 R4 第 641 行「啟用身分帳後…」之後另起一段): the same, inserted as a new paragraph (blank line first)
    改前(公理層.md I38 第 1540 行；案甲):                    a variant: applied only when that variant is chosen
    外部核對(43305271 geometry-core/kernel/grid_store.c 第 228 行「static bool geo_grid_axis_stagger_valid」):
                                                            line N of <path> at <git rev> must contain the text
    外部核對無(43305271 geometry-templates/rectangular-grid 不含「stagger|alternat」):
                                                            `git grep -i -E <regex> <rev> -- <path>` must find nothing
    全檔出現(公理層.md 「cardId」 第 691、2251 行):         the term occurs on exactly these lines of the file (a grep result)
(a 改後 block whose first line starts with "（刪除" declares that the 改前 span is deleted)
(a label line may carry a leading "- " or an indented "  - " so it can sit in a (nested) bullet list)

Variants.  The proposal offers alternatives the user has not chosen yet: D2 案甲／案乙, and the old-file definition
選項一／選項二／選項三.  A tagged 改前 / 新增於 belongs to one alternative; untagged ones always apply.

Per 改前 / 現況 quote it asserts
  1. the quote is a substring of the LF-normalised file   (公理層.md is stored CRLF on Windows: AGENTS.md)
  2. its first/last line are the cited line numbers; a 改前 quote must also occur exactly once in the file (a
     replacement span that occurs twice cannot be applied unambiguously); a 現況 quote may repeat elsewhere
  3. the nearest clause header above that line is the cited clause (D29, I24, ...); the report shows whether the
     line sits in the K (core) or W (wood template) block
  4. (改前 only) the 改後 block under it opens with the same text as the 改前 (same replacement span)
and globally
  5. every label is parseable, every 改前/現況 has a quote, and no "第 N 行" citation lives outside a label
     (an unchecked citation is exactly how stale line numbers survive).
  6. for every combination of variants, applying all 改前→改後 and 新增於 edits to both files succeeds: each span is
     still found exactly once when it is applied, edits never collide, the clause headers survive unchanged in
     number and order, and every 改後 / inserted text is present in the result.  `--emit-after DIR` writes the
     resulting files; scan_k_pointers.py --after scans their K text.

A multi-line quote is matched with the source's leading indentation ignored on continuation lines, because a
Markdown block quote cannot carry it; the report says which mode matched ("exact" / "indent-stripped").

Usage:
    python check_quotes.py                 check ../PROPOSAL.md against the repo this file lives in
    python check_quotes.py --proposal P    check another proposal text (used by the mutation demo)
    python check_quotes.py --root R        use another repo root
    python check_quotes.py --skip-external do not run the git-based 外部核對 labels (they are reported as SKIP)
    python check_quotes.py --emit-after D  also write the post-edit files of every variant combination into D
    python check_quotes.py --selftest      prove the checks have teeth (each injected defect must be caught)
Exit code 0 only if every check passes.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parents[2]           # evidence -> axiom-clarify-20261016 -> geometry-core -> repo root
DEFAULT_PROPOSAL = HERE.parent / "PROPOSAL.md"

SSOT_FILES = {
    "公理層.md": "公理層.md",
    "白話版": "geometry-guide/公理層-白話.md",
}

# Alternatives the user still has to choose between.  RECOMMENDED is what the proposal recommends, not a decision.
VARIANT_GROUPS = (("案甲", "案乙"), ("選項一", "選項二", "選項三"))
ALL_TAGS = {t for g in VARIANT_GROUPS for t in g}
RECOMMENDED = ("案乙", "選項一")
PREFACE = "分層前言"
PREFACE_HEADING = "### 分層契約（GEO-261）"

# clause header detection (nearest one above the cited line is "the clause the line belongs to")
HEADER_RE = {
    # D clauses open with bold "**D29 ...**"; I/R clauses open plain.  A plain body line that merely starts with
    # "D64 引用來源卡片..." (inside I38) must not be taken for a header.
    "公理層.md": re.compile(r"^(?:\*\*(D\d+[a-z]?)|([IR]\d+[a-z]?))(?=[ 　（(*:：])"),
    "白話版": re.compile(r"^## ([DIR]\d+[a-z]?)\s*$"),
}
SCOPE_RE = re.compile(r"^[^\n：]{0,24}契約（([KWMH])）：")

LABEL_START_RE = re.compile(r"^(?: *- )?(?:改前|現況|新增於|外部核對|全檔出現)")
LABEL_RE = re.compile(
    r"^(改前|現況|新增於)\((公理層\.md|白話版) ([DIR]\d+[a-z]?|" + PREFACE + r") 第 (\d+)(?:[–-](\d+))? 行"
    r"(?:「([^」]*)」之後(另起一段)?)?(?:；([^)]+))?\):$"
)
EXT_LINE_RE = re.compile(r"^外部核對\(([0-9a-f]{7,40}) (\S+) 第 (\d+) 行「([^」]+)」\):$")
GREP_RE = re.compile(r"^全檔出現\((公理層\.md|白話版) 「([^」]+)」 第 ([\d、]+) 行\):$")
EXT_NONE_RE = re.compile(r"^外部核對無\(([0-9a-f]{7,40}) (\S+) 不含「([^」]+)」\):$")
LINE_CITATION_RE = re.compile(r"第\s*\d+\s*(?:[–-]\s*\d+\s*)?行")
QUOTE_KINDS = ("改前", "現況")


def norm(raw: bytes) -> str:
    text = raw.decode("utf-8").replace("\r\n", "\n")
    if "\r" in text:
        raise SystemExit("lone CR left after CRLF normalisation: unexpected line endings")
    return text


def load_ssot(root: Path) -> dict[str, str]:
    out = {}
    for key, rel in SSOT_FILES.items():
        out[key] = norm((root / rel).read_bytes())
    return out


def parse_quote_block(lines: list[str], start: int) -> tuple[list[str], int]:
    """Block-quote lines starting at index `start`; returns (quote lines without '> ', next index)."""
    out = []
    i = start
    while i < len(lines) and lines[i].startswith(">"):
        out.append(re.sub(r"^>\s?", "", lines[i]))
        i += 1
    return out, i


def parse_proposal(text: str):
    """-> (items, problems).  item = dict(kind,...) ; kinds: 改前 現況 新增於 外部行 外部無 全檔出現"""
    lines = text.split("\n")
    items, problems = [], []
    label_line_idx = set()
    for idx, raw in enumerate(lines):
        if not LABEL_START_RE.match(raw):
            continue
        line = re.sub(r"^ *- ", "", raw)
        m = LABEL_RE.match(line)
        if m:
            kind, f, clause, a, b, prefix, para, tag = m.groups()
            a = int(a)
            b = int(b) if b else a
            label_line_idx.add(idx)
            qlines, nxt = parse_quote_block(lines, idx + 1)
            item = dict(kind=kind, file=f, clause=clause, a=a, b=b, prefix=prefix, para=bool(para), tag=tag,
                        quote=qlines, after=None, label_line=idx + 1, label=line)
            if tag is not None and tag not in ALL_TAGS:
                problems.append(f"PROPOSAL.md:{idx + 1}: unknown variant tag {tag!r} (known: {sorted(ALL_TAGS)})")
            if tag is not None and kind == "現況":
                problems.append(f"PROPOSAL.md:{idx + 1}: a 現況 quote is evidence, it cannot belong to a variant")
            if kind in QUOTE_KINDS or kind == "新增於":
                if not qlines or not any(q.strip() for q in qlines):
                    problems.append(f"PROPOSAL.md:{idx + 1}: {kind} label has no block-quote below it")
            if kind == "改前":
                # the 改後 block that belongs to it: next '改後:' before the next label / heading
                j = nxt
                while j < len(lines):
                    if lines[j] == "改後:":
                        item["after"], _ = parse_quote_block(lines, j + 1)
                        break
                    if LABEL_START_RE.match(lines[j]) or lines[j].startswith("#"):
                        break
                    j += 1
                if item["after"] is None:
                    problems.append(f"PROPOSAL.md:{idx + 1}: 改前 label has no 改後 block")
            if kind == "新增於" and prefix is None:
                problems.append(f"PROPOSAL.md:{idx + 1}: 新增於 label needs 「anchor text…」之後")
            if kind != "新增於" and (prefix is not None or para):
                problems.append(f"PROPOSAL.md:{idx + 1}: only a 新增於 label takes 「…」之後")
            items.append(item)
            continue
        m = EXT_LINE_RE.match(line)
        if m:
            label_line_idx.add(idx)
            items.append(dict(kind="外部行", rev=m.group(1), path=m.group(2), a=int(m.group(3)), text=m.group(4),
                              label_line=idx + 1, label=line))
            continue
        m = GREP_RE.match(line)
        if m:
            label_line_idx.add(idx)
            items.append(dict(kind="全檔出現", file=m.group(1), term=m.group(2),
                              lines=sorted({int(x) for x in m.group(3).split("、") if x}),
                              label_line=idx + 1, label=line))
            continue
        m = EXT_NONE_RE.match(line)
        if m:
            label_line_idx.add(idx)
            items.append(dict(kind="外部無", rev=m.group(1), path=m.group(2), rx=m.group(3),
                              label_line=idx + 1, label=line))
            continue
        problems.append(f"PROPOSAL.md:{idx + 1}: unparseable label {raw!r}")
    for idx, line in enumerate(lines):
        if idx in label_line_idx:
            continue
        for m in LINE_CITATION_RE.finditer(line):
            problems.append(
                f"PROPOSAL.md:{idx + 1}: line citation {m.group(0)!r} outside a label is never checked; "
                f"move it into a label (改前/現況/新增於/外部核對) or drop the number"
            )
    return items, problems


def locate(src_lines: list[str], qlines: list[str], strip: bool) -> list[tuple[int, int]]:
    """All (first_line, last_line) 1-based spans where the quote matches."""
    n = len(qlines)
    f = (lambda s: s.lstrip(" \t")) if strip else (lambda s: s)
    hits: list[tuple[int, int]] = []
    for i in range(len(src_lines) - n + 1):
        if n == 1:
            hits.extend([(i + 1, i + 1)] * src_lines[i].count(qlines[0]))
            continue
        if not src_lines[i].endswith(qlines[0]):
            continue
        if all(f(src_lines[i + k]) == qlines[k] for k in range(1, n - 1)) and f(src_lines[i + n - 1]).startswith(qlines[-1]):
            hits.append((i + 1, i + n))
    return hits


def clause_above(src_lines: list[str], file_key: str, line_no: int) -> tuple[str | None, int | None]:
    rx = HEADER_RE[file_key]
    for i in range(line_no - 1, -1, -1):
        m = rx.match(src_lines[i])
        if m:
            return next(g for g in m.groups() if g), i + 1
    return None, None


def preface_range(src_lines: list[str]) -> tuple[int, int] | None:
    """1-based (first, last) line of the layering preface: below its heading, above the next heading."""
    try:
        start = src_lines.index(PREFACE_HEADING) + 1
    except ValueError:
        return None
    end = start
    while end < len(src_lines) and not src_lines[end].startswith("#"):
        end += 1
    return start + 1, end


def scope_above(src_lines: list[str], line_no: int, header_line: int | None) -> str:
    lo = (header_line or 1) - 1
    for i in range(line_no - 1, lo - 1, -1):
        m = SCOPE_RE.match(src_lines[i])
        if m:
            return m.group(1)
    return "-"


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True)


_EXT_CACHE: dict[tuple, tuple[bool, str]] = {}


def check_external(it: dict, root: Path) -> tuple[bool, str]:
    # memoised: --selftest re-checks the same unchanged labels once per injected defect, and each is a git process
    key = (str(root), it["rev"], it["path"], it["kind"], it.get("a"), it.get("text"), it.get("rx"))
    if key not in _EXT_CACHE:
        _EXT_CACHE[key] = _check_external(it, root)
    return _EXT_CACHE[key]


def _check_external(it: dict, root: Path) -> tuple[bool, str]:
    rev, path = it["rev"], it["path"]
    if git(root, "cat-file", "-e", rev + "^{commit}").returncode != 0:
        return False, f"cannot resolve {rev} in {root} (run `git fetch origin` first)"
    if it["kind"] == "外部行":
        p = git(root, "show", f"{rev}:{path}")
        if p.returncode != 0:
            return False, f"git show {rev}:{path} failed: {p.stderr.decode('utf-8', 'replace').strip()[:120]}"
        lines = norm(p.stdout).split("\n")
        n = it["a"]
        if not (1 <= n <= len(lines)):
            return False, f"line {n} is outside {path} at {rev} ({len(lines)} lines)"
        if it["text"] not in lines[n - 1]:
            return False, f"line {n} of {path} at {rev} does not contain {it['text']!r} (it is {lines[n - 1][:60]!r})"
        return True, f"{path}:{n} at {rev} contains the cited text"
    p = git(root, "grep", "-n", "-i", "-E", it["rx"], rev, "--", path)
    if p.returncode == 1:
        return True, f"git grep -i -E found nothing under {path} at {rev}"
    if p.returncode == 0:
        hits = p.stdout.decode("utf-8", "replace").strip().split("\n")
        return False, f"{len(hits)} hit(s) under {path} at {rev}, first: {hits[0][:100]!r}"
    return False, f"git grep failed: {p.stderr.decode('utf-8', 'replace').strip()[:120]}"


# ----------------------------------------------------------------------------------------------- applying the edits

def variant_combinations() -> list[tuple[str, ...]]:
    return list(itertools.product(*VARIANT_GROUPS))


def applies(it: dict, chosen: tuple[str, ...]) -> bool:
    return it.get("tag") is None or it["tag"] in chosen


def apply_edits(items: list[dict], ssot: dict[str, str], chosen: tuple[str, ...]):
    """-> ({file: post-edit text}, problems).  Edits are applied bottom-up by their cited line so that every edit's
    line numbers still refer to the current SSOT; each 改前 span is searched again at the moment it is applied."""
    problems: list[str] = []
    out: dict[str, str] = {}
    for fkey, text in ssot.items():
        lines = text.split("\n")
        edits = [it for it in items if it["kind"] in ("改前", "新增於") and it["file"] == fkey and applies(it, chosen)]
        # same line: insert-after first (it does not touch the line itself), then the in-place replacement
        edits.sort(key=lambda it: (it["a"], 0 if it["kind"] == "改前" else 1), reverse=True)
        touched: dict[int, str] = {}
        for it in edits:
            where = f"PROPOSAL.md:{it['label_line']} ({it['kind']} {fkey} {it['clause']} L{it['a']})"
            a, b = it["a"], it["b"]
            if not (1 <= a <= b <= len(lines)):
                problems.append(f"{where}: span outside the file")
                continue
            if it["kind"] == "新增於":
                key = -a                       # insertions after the same line would land in an arbitrary order
                if key in touched:
                    problems.append(f"{where}: a second insertion after line {a} (also {touched[key]})")
                touched[key] = where
                anchor = lines[a - 1]
                indent = anchor[: len(anchor) - len(anchor.lstrip(" \t"))]
                new = [("" if not l else indent + l) for l in it["quote"]]
                lines[a:a] = ([""] + new) if it["para"] else new
                continue
            for ln in range(a, b + 1):
                if ln in touched and touched[ln] != where:
                    problems.append(f"{where}: collides with {touched[ln]} on line {ln}")
                touched[ln] = where
            q, after = it["quote"], it["after"] or []
            span = lines[a - 1:b]
            strip = len(q) > 1
            seg = span[0] + "".join("\n" + (s.lstrip(" \t") if strip else s) for s in span[1:])
            quote = "\n".join(q)
            if seg.count(quote) != 1:
                problems.append(f"{where}: 改前 span found {seg.count(quote)} times on lines {a}-{b} when applied")
                continue
            deleting = bool(after) and after[0].startswith("（刪除")
            seg = seg.replace(quote, "" if deleting else "\n".join(after), 1)
            new_lines = seg.split("\n")
            if deleting:
                new_lines = [l for l in new_lines if l.strip()]
            lines[a - 1:b] = new_lines
        out[fkey] = "\n".join(lines)
        # structural sanity: same clause headers, same order
        rx = HEADER_RE[fkey]
        before_h = [rx.match(l).group(0) for l in text.split("\n") if rx.match(l)]
        after_h = [rx.match(l).group(0) for l in out[fkey].split("\n") if rx.match(l)]
        if before_h != after_h:
            problems.append(f"{fkey}: clause headers changed by the edits ({len(before_h)} -> {len(after_h)})")
        for it in edits:
            body = it["quote"] if it["kind"] == "新增於" else it["after"]
            if body and not (it["kind"] == "改前" and body[0].startswith("（刪除")) and "\n".join(body) not in out[fkey]:
                problems.append(f"PROPOSAL.md:{it['label_line']}: its new text is not in the post-edit {fkey}")
    return out, problems


def check_apply(items: list[dict], ssot: dict[str, str]):
    results = []
    for combo in variant_combinations():
        texts, problems = apply_edits(items, ssot, combo)
        name = "apply " + "+".join(combo) + (" (recommended)" if combo == RECOMMENDED else "")
        n = sum(1 for it in items if it["kind"] in ("改前", "新增於") and applies(it, combo))
        if problems:
            results.append(("FAIL", name, "; ".join(problems)))
        else:
            delta = {k: len(texts[k].split("\n")) - len(ssot[k].split("\n")) for k in ssot}
            results.append(("PASS", name, f"{n} edits applied; line count change {delta}"))
    used = {it.get("tag") for it in items if it.get("tag")}
    for group in VARIANT_GROUPS:
        if used & set(group) and not set(group) <= used:
            results.append(("FAIL", "variants", f"group {group}: only {sorted(used & set(group))} have text"))
    return results


# ---------------------------------------------------------------------------------------------------------- checks

def check(proposal_text: str, ssot: dict[str, str], root: Path = DEFAULT_ROOT, skip_external: bool = False):
    """-> (list of (status, name, detail), items); status is PASS / FAIL / SKIP"""
    results: list[tuple[str, str, str]] = []
    items, problems = parse_proposal(proposal_text)
    for p in problems:
        results.append(("FAIL", "structure", p))
    if not items:
        results.append(("FAIL", "structure", "no label found in PROPOSAL.md"))
    src_lines_by_file = {k: v.split("\n") for k, v in ssot.items()}
    for it in items:
        if it["kind"] == "全檔出現":
            sl = src_lines_by_file[it["file"]]
            found = [i + 1 for i, l in enumerate(sl) if it["term"] in l]
            name = f"全檔出現 {it['file']} 「{it['term']}」"
            if found == it["lines"]:
                results.append(("PASS", name, f"occurs on exactly lines {found}"))
            else:
                results.append(("FAIL", name, f"occurs on lines {found}, label says {it['lines']}"))
            continue
        if it["kind"] in ("外部行", "外部無"):
            name = f"{it['kind'].replace('外部', '外部核對')} {it['rev']} {it['path']}" + (f":{it['a']}" if it["kind"] == "外部行" else "")
            if skip_external:
                results.append(("SKIP", name, "--skip-external"))
                continue
            ok, detail = check_external(it, root)
            results.append(("PASS" if ok else "FAIL", name, detail))
            continue
        name = (f"{it['kind']} {it['file']} {it['clause']} L{it['a']}" + (f"-{it['b']}" if it["b"] != it["a"] else "")
                + (f" [{it['tag']}]" if it.get("tag") else ""))
        text = ssot[it["file"]]
        sl = src_lines_by_file[it["file"]]
        problems_here: list[str] = []
        detail = ""
        if it["kind"] in QUOTE_KINDS:
            q = it["quote"]
            quote = "\n".join(q)
            multi = len(q) > 1
            mode = None
            if quote in text:
                mode = "exact"
            elif multi and quote in re.sub(r"\n[ \t]+", "\n", text):
                mode = "indent-stripped"
            if mode is None:
                problems_here.append("quote is NOT a substring of the current file (LF-normalised)")
            else:
                hits = locate(sl, q, strip=(mode == "indent-stripped"))
                cited = (it["a"], it["b"])
                if it["kind"] == "改前" and len(hits) != 1:
                    # a replacement span that occurs twice cannot be applied unambiguously
                    problems_here.append(f"quote must occur exactly once, found {len(hits)} at {hits}")
                elif cited not in hits:
                    where = ", ".join(f"{h[0]}-{h[1]}" for h in hits)
                    problems_here.append(f"quote is at lines {where}, label says {it['a']}-{it['b']}")
                else:
                    others = [h for h in hits if h != cited]
                    detail = f"mode={mode}" + (f" (evidence quote; also occurs at {others})" if others else "")
            if it["kind"] == "改前" and it["after"] is not None and q and it["after"]:
                if it["after"][0].startswith("（刪除"):
                    detail += " (改後 deletes the span)"
                elif q[0][:6] != it["after"][0][:6]:
                    problems_here.append(f"改後 opens {it['after'][0][:6]!r} but 改前 opens {q[0][:6]!r}: not the same replacement span")
        else:  # 新增於 anchor
            prefix = (it["prefix"] or "").rstrip("…")
            if not prefix:
                problems_here.append("empty anchor text")
            elif it["a"] != it["b"]:
                problems_here.append("anchor must be a single line")
            elif not (1 <= it["a"] <= len(sl)) or not sl[it["a"] - 1].lstrip(" \t").startswith(prefix):
                got = sl[it["a"] - 1][:30] if 1 <= it["a"] <= len(sl) else "<past EOF>"
                problems_here.append(f"line {it['a']} does not begin with {prefix!r} (begins {got!r})")
            else:
                detail = "anchor line begins with the cited text" + (" (new paragraph)" if it["para"] else "")
        # clause identity (only meaningful when the line number is in range)
        if not 1 <= it["a"] <= len(sl):
            problems_here.append(f"line {it['a']} is outside the file ({len(sl)} lines)")
        elif it["clause"] == PREFACE:
            rng = preface_range(sl) if it["file"] == "公理層.md" else None
            if rng is None or not (rng[0] <= it["a"] and it["b"] <= rng[1]):
                problems_here.append(f"line {it['a']} is not in the layering preface {rng}")
            else:
                detail += f" clause={PREFACE}(L{rng[0]}-{rng[1]})"
        else:
            cl, hdr = clause_above(sl, it["file"], it["a"])
            if cl != it["clause"]:
                problems_here.append(f"line {it['a']} belongs to clause {cl} (header at line {hdr}), label says {it['clause']}")
            else:
                detail += f" clause={cl}(header L{hdr}) scope={scope_above(sl, it['a'], hdr)}"
        if problems_here:
            results.append(("FAIL", name, "; ".join(problems_here)))
        else:
            results.append(("PASS", name, detail.strip()))
    if not problems:
        results.extend(check_apply(items, ssot))
    return results, items


def report(results, items, ssot, out=sys.stdout) -> bool:
    for key in ssot:
        h = hashlib.sha256(ssot[key].encode("utf-8")).hexdigest()[:16]
        print(f"# {key}: {len(ssot[key].split(chr(10)))} lines (LF-normalised), sha256 {h}...", file=out)
    ok_all = True
    for status, name, detail in results:
        ok_all &= status != "FAIL"
        print(f"{status}  {name}  {detail}", file=out)
    kinds = {}
    for i in items:
        kinds[i["kind"]] = kinds.get(i["kind"], 0) + 1
    bad = sum(1 for r in results if r[0] == "FAIL")
    skipped = sum(1 for r in results if r[0] == "SKIP")
    print(f"# checked {', '.join(f'{v} {k}' for k, v in kinds.items())}, {len(variant_combinations())} variant "
          f"combinations applied; {bad} failure(s)" + (f", {skipped} skipped" if skipped else ""), file=out)
    return ok_all


def emit_after(proposal_text: str, ssot: dict[str, str], out_dir: Path) -> list[Path]:
    items, problems = parse_proposal(proposal_text)
    if problems:
        raise SystemExit("cannot emit: " + "; ".join(problems))
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for combo in variant_combinations():
        texts, probs = apply_edits(items, ssot, combo)
        if probs:
            raise SystemExit("cannot emit " + "+".join(combo) + ": " + "; ".join(probs))
        for key, text in texts.items():
            stem = "公理層" if key == "公理層.md" else "公理層-白話"
            p = out_dir / f"{stem}.after-{'-'.join(combo)}.md"
            p.write_text(text, encoding="utf-8")
            written.append(p)
    return written


def selftest(proposal_text: str, ssot: dict[str, str], root: Path) -> bool:
    base, _ = check(proposal_text, ssot, root)
    if any(r[0] != "PASS" for r in base):
        print("selftest: baseline is not green, fix that first")
        return False

    def mutate(old: str, new: str) -> str:
        # first occurrence only: a 改前 quote always precedes the 改後 that repeats part of it
        assert old in proposal_text, f"mutation anchor {old!r} not found in PROPOSAL.md"
        return proposal_text.replace(old, new, 1)

    cases = [
        ("one char of a 公理層.md quote changed (D29)", mutate("格線身分為（系統", "格線身份為（系統"), "改前 公理層.md D29"),
        ("one char of a 白話版 quote changed (I5)", mutate("矩形的四條邊也不能跟", "矩形的四條邊也不可跟"), "改前 白話版 I5"),
        ("second line of the two-line R18 quote changed", mutate("（邊界主支為真）但 coversEdge 恆為假（兩端", "（邊界主支為真）但 coversEdge 恆為假（雙端"), "改前 公理層.md R18"),
        ("one char of a K-block quote changed (D10b K)", mutate("> cell、band、全線及分段引用須分別保存；沒有 band 的單一位置若不唯一即拒絕。", "> cell、band、全線及分段引用須分別保存；沒有 band 的單一位置若不唯一即拒決。"), "改前 公理層.md D10b"),
        ("one char of a clause-title quote changed (I23)", mutate("> I23 網格引用的追溯與重算（2026-09-18 目的翻轉（分層契約）：", "> I23 網格引用的追溯與重算（2026-09-18 目的翻轉（分層合約）："), "改前 公理層.md I23"),
        ("one char of a 現況 quote changed (R13 W lines)", mutate("「資料跟材料走」):", "「資料跟材料走」)；"), "現況 公理層.md R13"),
        ("line number off by one (I24 1385 -> 1386)", mutate("I24 第 1385 行", "I24 第 1386 行"), "改前 公理層.md I24"),
        ("right line, wrong clause (R22 cited as I24)", mutate("R22 第 2128 行", "I24 第 2128 行"), "改前 公理層.md I24 L2128"),
        ("insertion anchor text wrong", mutate("「band 的切開用另一軸未加相位差的格線…」", "「band 的切開用另一軸未加相位差的格網…」"), "新增於 公理層.md D10b"),
        ("unchecked line citation smuggled in", proposal_text + "\n(見公理層.md 第 625 行)\n", "structure"),
        ("改後 no longer opens like 改前 (prefix drift)", mutate("改後:\n> 相位差守門：", "改後:\n> I24 相位差守門："), "改前 公理層.md I24"),
        ("外部核對 cited text wrong (kernel grid_store)", mutate("「static bool geo_grid_axis_stagger_valid」", "「static bool geo_grid_axis_stagger_validx」"), "外部核對行 43305271"),
        ("外部核對無 regex made to match something real", mutate("不含「stagger|", "不含「geo_interval_subdivide|stagger|"), "外部核對無 43305271"),
        ("全檔出現 grep result goes stale (cardId line list)", mutate("「cardId」 第 691、2251 行", "「cardId」 第 691、2252 行"), "全檔出現 公理層.md 「cardId」"),
        ("one char of a D31 K-block quote changed", mutate("> 參數卡保存獨立 id、顯示名稱、欄位及順序；每欄以 (cardId,fieldId) 為身分", "> 參數卡保存獨立 id、顯示名稱、欄位及順序；每欄以 (cardId,fieldId) 為身份"), "改前 公理層.md D31"),
        ("clause label wrong where a body line starts with 'D64 ' (I38 cited as D64)", mutate("現況(公理層.md I38 第 1537 行)", "現況(公理層.md D64 第 1537 行)"), "現況 公理層.md D64 L1537"),
        ("deletion 改後 loses its （刪除 marker", mutate("（刪除此句，內容移到 R53）", "刪除此句，內容移到 R53"), "改前 公理層.md I38 L1540"),
        ("insertion anchor on an indented line wrong (R53)", mutate("「配號只依目標候選 World、來源閉包", "「配號只依目標候選 Worldx、來源閉包"), "新增於 公理層.md R53"),
        ("one char of a 白話版 K-summary quote changed (I24)", mutate("核心先精確算相位差，再驗非零", "核心先精確算相位差，再驗非賃"), "改前 白話版 I24"),
        ("quoted decision-queue text wrong (Q-A option)", mutate("第 484 行「只准一軸(建議)」", "第 484 行「只准兩軸(建議)」"), "外部核對行 02baea2c 決策佇列.md:484"),
        ("D3 sweep list goes stale (依以下 line list)", mutate("「依以下」 第 615、1403 行", "「依以下」 第 615、1404 行"), "全檔出現 公理層.md 「依以下」"),
        ("one char of the D29 K quote changed", mutate("> 來源引用、容量與首版組合限制依以下相容契約，無限", "> 來源引用、容量與首版組合限制依以下相容契約，無線"), "公理層.md D29 L615"),
        ("one char of an I74 quote changed", mutate("同候選刪除並以 put 或匯入重建來源卡片／欄位鍵時，每個", "同候選刪除並以 put 或匯入重建來源卡片／欄位件時，每個"), "現況 公理層.md I74"),
        ("approved K text (17a25e92) no longer on the cited line (D10b K)", mutate("第 1593 行「cell、band", "第 1594 行「cell、band"), "AXIOM-PROPOSAL.md:1594"),
        ("approved-proposal text no longer on the cited line", mutate("第 1535 行「來源引用、容量與首版組合限制依以下相容契約", "第 1535 行「來源引用、容量與首版組合限制依以下相容契約x"), "AXIOM-PROPOSAL.md:1535"),
        # 2026-10-17 additions: variants, preface labels and the applier
        ("unknown variant tag", mutate("；選項二):", "；選項貳):"), "structure"),
        ("a variant group loses one alternative's text", proposal_text.replace("；選項三):", "):"), "variants"),
        ("preface label points below the preface", mutate("現況(公理層.md 分層前言 第 75 行)", "現況(公理層.md 分層前言 第 1927 行)"), "現況 公理層.md 分層前言"),
        ("one char of a preface quote changed", mutate("> 完整專案、附件、草稿、畫布／相機、互動確認、公開 parser／序列化", "> 完整專案、附件、草稿、畫布／相機、互動確認、公開 parser/序列化"), "現況 公理層.md 分層前言"),
        ("two edits replace the same span (A1's D29 W edit duplicated)",
         proposal_text + "\n\n改前(公理層.md D29 第 625 行):\n> 未設相位差時，格線身分為（系統、軸、signed k）。\n\n改後:\n> 未設相位差時，格線身分為（系統、軸）。\n",
         "apply"),
        ("an untagged 改前 that only one variant could apply (I74 案乙 tag dropped)",
         mutate("改前(公理層.md I74 第 1908 行；案乙):", "改前(公理層.md I74 第 1908 行):"), "apply 案甲"),
    ]
    all_caught = True
    for desc, mutated, expect in cases:
        res, _ = check(mutated, ssot, root)
        failed = [r for r in res if r[0] == "FAIL"]
        caught = any(expect in r[1] for r in failed)
        all_caught &= caught
        print(f"{'CAUGHT ' if caught else 'MISSED '} {desc}")
        for r in failed[:4]:
            print(f"          FAIL  {r[1]}  {r[2][:200]}")
    print("selftest: " + ("every injected defect was caught" if all_caught else "SOME DEFECTS WERE MISSED"))
    return all_caught


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--proposal", type=Path, default=DEFAULT_PROPOSAL)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--skip-external", action="store_true")
    ap.add_argument("--emit-after", type=Path)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    ssot = load_ssot(args.root)
    proposal_text = norm(args.proposal.read_bytes())
    if args.selftest:
        return 0 if selftest(proposal_text, ssot, args.root) else 1
    results, items = check(proposal_text, ssot, args.root, args.skip_external)
    ok = report(results, items, ssot)
    if args.emit_after:
        for p in emit_after(proposal_text, ssot, args.emit_after):
            print(f"# wrote {p}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
