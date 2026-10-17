#!/usr/bin/env python3
"""Check that PROPOSAL.md's quotes of the current SSOT are verbatim and sit on the cited lines.

PROPOSAL.md quotes the text it wants to change ("改前") and cites where it lives.  Line numbers rot every
time main moves (they already rotted once: a898ad6e -> c144c013, after the K/M/W/H layering).  This script
re-derives the truth from the files instead of trusting the proposal.

Labels it reads from PROPOSAL.md (one per quote, the quote is the block-quote lines right below it):

    改前(公理層.md D29 第 625 行):                          quote must be on exactly that line
    改前(公理層.md R18 第 2078–2079 行):                    multi-line quote, first line ends / last line starts it
    新增於(白話版 R18 第 743 行「只看外輪廓…」之後):         insertion anchor: that line must begin with the text

Per label it asserts
  1. the quote is a substring of the LF-normalised file   (公理層.md is stored CRLF on Windows: AGENTS.md)
  2. the quote occurs exactly once, and its first/last line are the cited line numbers
  3. the nearest clause header above that line is the cited clause (D29, I24, ...)
  4. the 改後 block under a 改前 opens with the same text as the 改前 (same replacement span)
and globally
  5. every label is parseable, every 改前 has a quote, and no "第 N 行" citation lives outside a label
     (an unchecked citation is exactly how stale line numbers survive).

A multi-line quote is matched with the source's leading indentation ignored on continuation lines, because a
Markdown block quote cannot carry it; the report says which mode matched ("exact" / "indent-stripped").

Usage:
    python check_quotes.py                 check ../PROPOSAL.md against the repo this file lives in
    python check_quotes.py --proposal P    check another proposal text (used by the mutation demo)
    python check_quotes.py --root R        use another repo root
    python check_quotes.py --selftest      prove the checks have teeth (each injected defect must be caught)
Exit code 0 only if every check passes.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parents[2]           # evidence -> axiom-clarify-20261016 -> geometry-core -> repo root
DEFAULT_PROPOSAL = HERE.parent / "PROPOSAL.md"

SSOT_FILES = {
    "公理層.md": "公理層.md",
    "白話版": "geometry-guide/公理層-白話.md",
}

# clause header detection (nearest one above the cited line is "the clause the line belongs to")
HEADER_RE = {
    "公理層.md": re.compile(r"^(?:\*\*)?([DIR]\d+[a-z]?)(?=[ 　（(*:：])"),
    "白話版": re.compile(r"^## ([DIR]\d+[a-z]?)\s*$"),
}
SCOPE_RE = re.compile(r"^[^\n：]{0,24}契約（([KWMH])）：")

LABEL_RE = re.compile(
    r"^(改前|新增於)\((公理層\.md|白話版) ([DIR]\d+[a-z]?) 第 (\d+)(?:[–-](\d+))? 行(?:「([^」]*)」之後)?\):$"
)
LINE_CITATION_RE = re.compile(r"第\s*\d+\s*(?:[–-]\s*\d+\s*)?行")


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
    """-> (items, problems).  item = dict(kind,file,clause,a,b,prefix,quote,after,label_line)"""
    lines = text.split("\n")
    items, problems = [], []
    label_line_idx = set()
    for idx, line in enumerate(lines):
        if not re.match(r"^(改前|新增於)", line):
            continue
        m = LABEL_RE.match(line)
        if not m:
            problems.append(f"PROPOSAL.md:{idx + 1}: unparseable label {line!r}")
            continue
        kind, f, clause, a, b, prefix = m.groups()
        a = int(a)
        b = int(b) if b else a
        label_line_idx.add(idx)
        qlines, nxt = parse_quote_block(lines, idx + 1)
        item = dict(kind=kind, file=f, clause=clause, a=a, b=b, prefix=prefix, quote=qlines,
                    after=None, label_line=idx + 1, label=line)
        if kind == "改前":
            if not qlines or not any(q.strip() for q in qlines):
                problems.append(f"PROPOSAL.md:{idx + 1}: 改前 label has no block-quote below it")
            # the 改後 block that belongs to it: next '改後:' before the next label / heading
            j = nxt
            while j < len(lines):
                if lines[j] == "改後:":
                    item["after"], _ = parse_quote_block(lines, j + 1)
                    break
                if re.match(r"^(改前|新增於)\(", lines[j]) or lines[j].startswith("#"):
                    break
                j += 1
            if item["after"] is None:
                problems.append(f"PROPOSAL.md:{idx + 1}: 改前 label has no 改後 block")
        else:
            if prefix is None:
                problems.append(f"PROPOSAL.md:{idx + 1}: 新增於 label needs 「anchor text…」之後")
        items.append(item)
    for idx, line in enumerate(lines):
        if idx in label_line_idx:
            continue
        for m in LINE_CITATION_RE.finditer(line):
            problems.append(
                f"PROPOSAL.md:{idx + 1}: line citation {m.group(0)!r} outside a label is never checked; "
                f"move it into a 改前(...)/新增於(...) label or drop the number"
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
            return m.group(1), i + 1
    return None, None


def scope_above(src_lines: list[str], line_no: int, header_line: int | None) -> str:
    lo = (header_line or 1) - 1
    for i in range(line_no - 1, lo - 1, -1):
        m = SCOPE_RE.match(src_lines[i])
        if m:
            return m.group(1)
    return "-"


def check(proposal_text: str, ssot: dict[str, str]):
    """-> list of (ok, name, detail)"""
    results: list[tuple[bool, str, str]] = []
    items, problems = parse_proposal(proposal_text)
    for p in problems:
        results.append((False, "structure", p))
    if not items:
        results.append((False, "structure", "no 改前/新增於 label found in PROPOSAL.md"))
    src_lines_by_file = {k: v.split("\n") for k, v in ssot.items()}
    for it in items:
        name = f"{it['kind']} {it['file']} {it['clause']} L{it['a']}" + (f"-{it['b']}" if it["b"] != it["a"] else "")
        text = ssot[it["file"]]
        sl = src_lines_by_file[it["file"]]
        problems_here: list[str] = []
        detail = ""
        if it["kind"] == "改前":
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
                if len(hits) != 1:
                    problems_here.append(f"quote must occur exactly once, found {len(hits)} at {hits}")
                elif hits[0] != (it["a"], it["b"]):
                    problems_here.append(f"quote is at lines {hits[0][0]}-{hits[0][1]}, label says {it['a']}-{it['b']}")
                else:
                    detail = f"mode={mode}"
            if it["after"] is not None and q and it["after"]:
                if q[0][:8] != it["after"][0][:8]:
                    problems_here.append(f"改後 opens {it['after'][0][:8]!r} but 改前 opens {q[0][:8]!r}: not the same replacement span")
        else:  # 新增於 anchor
            prefix = (it["prefix"] or "").rstrip("…")
            if not prefix:
                problems_here.append("empty anchor text")
            elif it["a"] != it["b"]:
                problems_here.append("anchor must be a single line")
            elif not (1 <= it["a"] <= len(sl)) or not sl[it["a"] - 1].startswith(prefix):
                got = sl[it["a"] - 1][:30] if 1 <= it["a"] <= len(sl) else "<past EOF>"
                problems_here.append(f"line {it['a']} does not begin with {prefix!r} (begins {got!r})")
            else:
                detail = "anchor line begins with the cited text"
        # clause identity (only meaningful when the line number is in range)
        if 1 <= it["a"] <= len(sl):
            cl, hdr = clause_above(sl, it["file"], it["a"])
            if cl != it["clause"]:
                problems_here.append(f"line {it['a']} belongs to clause {cl} (header at line {hdr}), label says {it['clause']}")
            else:
                detail += f" clause={cl}(header L{hdr}) scope={scope_above(sl, it['a'], hdr)}"
        else:
            problems_here.append(f"line {it['a']} is outside the file ({len(sl)} lines)")
        if problems_here:
            results.append((False, name, "; ".join(problems_here)))
        else:
            results.append((True, name, detail.strip()))
    return results, items


def report(results, items, ssot, out=sys.stdout) -> bool:
    for key in ssot:
        h = hashlib.sha256(ssot[key].encode("utf-8")).hexdigest()[:16]
        print(f"# {key}: {len(ssot[key].split(chr(10)))} lines (LF-normalised), sha256 {h}...", file=out)
    ok_all = True
    for ok, name, detail in results:
        ok_all &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}", file=out)
    n_q = sum(1 for i in items if i["kind"] == "改前")
    n_a = sum(1 for i in items if i["kind"] == "新增於")
    bad = sum(1 for r in results if not r[0])
    print(f"# {n_q} quotes + {n_a} anchors checked, {bad} failure(s)", file=out)
    return ok_all


def selftest(proposal_text: str, ssot: dict[str, str]) -> bool:
    base, _ = check(proposal_text, ssot)
    if not all(r[0] for r in base):
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
        ("line number off by one (I24 1385 -> 1386)", mutate("I24 第 1385 行", "I24 第 1386 行"), "改前 公理層.md I24"),
        ("right line, wrong clause (R22 cited as I24)", mutate("R22 第 2128 行", "I24 第 2128 行"), "改前 公理層.md I24 L2128"),
        ("insertion anchor text wrong", mutate("「band 的切開用另一軸未加相位差的格線…」", "「band 的切開用另一軸未加相位差的格網…」"), "新增於 公理層.md D10b"),
        ("unchecked line citation smuggled in", proposal_text + "\n(見公理層.md 第 625 行)\n", "structure"),
        ("改後 no longer opens like 改前 (prefix drift)", mutate("改後:\n> 相位差守門：", "改後:\n> I24 相位差守門："), "改前 公理層.md I24"),
    ]
    all_caught = True
    for desc, mutated, expect in cases:
        res, _ = check(mutated, ssot)
        failed = [r for r in res if not r[0]]
        caught = any(expect in r[1] for r in failed)
        all_caught &= caught
        print(f"{'CAUGHT ' if caught else 'MISSED '} {desc}")
        for r in failed:
            print(f"          FAIL  {r[1]}  {r[2]}")
    print("selftest: " + ("every injected defect was caught" if all_caught else "SOME DEFECTS WERE MISSED"))
    return all_caught


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--proposal", type=Path, default=DEFAULT_PROPOSAL)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    ssot = load_ssot(args.root)
    proposal_text = norm(args.proposal.read_bytes())
    if args.selftest:
        return 0 if selftest(proposal_text, ssot) else 1
    results, items = check(proposal_text, ssot)
    return 0 if report(results, items, ssot) else 1


if __name__ == "__main__":
    sys.exit(main())
