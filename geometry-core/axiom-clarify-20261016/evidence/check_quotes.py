#!/usr/bin/env python3
"""Check that PROPOSAL.md's quotes of the current SSOT are verbatim and sit on the cited lines.

PROPOSAL.md quotes the text it wants to change ("改前") and cites where it lives.  Line numbers rot every
time main moves (they already rotted once: a898ad6e -> c144c013, after the K/M/W/H layering).  This script
re-derives the truth from the files instead of trusting the proposal.

Labels it reads from PROPOSAL.md.  For the first three kinds the quote is the block-quote lines right below:

    改前(公理層.md D29 第 625 行):                          text to be replaced; must be on exactly that line
    改前(公理層.md R18 第 2078–2079 行):                    multi-line quote, first line ends / last line starts it
    現況(公理層.md I23 第 1358 行):                         text that stays as it is, cited as evidence; same checks
    新增於(白話版 R18 第 743 行「只看外輪廓…」之後):         insertion anchor: that line must begin with the text
    外部核對(43305271 geometry-core/kernel/grid_store.c 第 228 行「static bool geo_grid_axis_stagger_valid」):
                                                            line N of <path> at <git rev> must contain the text
    外部核對無(43305271 geometry-templates/rectangular-grid 不含「stagger|alternat」):
                                                            `git grep -i -E <regex> <rev> -- <path>` must find nothing
    全檔出現(公理層.md 「cardId」 第 691、2251 行):         the term occurs on exactly these lines of the file (a grep result)
    證據檔計數(s1-probes/errors.txt 「V_EXTENSION」 共 5 行):  a file under evidence/ has exactly N lines containing the term
(a 改後 block whose first line starts with "（刪除" declares that the 改前 span is deleted)
(a label line may carry a leading "- " so it can sit in a bullet list)

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

A multi-line quote is matched with the source's leading indentation ignored on continuation lines, because a
Markdown block quote cannot carry it; the report says which mode matched ("exact" / "indent-stripped").

Usage:
    python check_quotes.py                 check ../PROPOSAL.md against the repo this file lives in
    python check_quotes.py --proposal P    check another proposal text (used by the mutation demo)
    python check_quotes.py --root R        use another repo root
    python check_quotes.py --skip-external do not run the git-based 外部核對 labels (they are reported as SKIP)
    python check_quotes.py --selftest      prove the checks have teeth (each injected defect must be caught)
Exit code 0 only if every check passes.
"""
from __future__ import annotations

import argparse
import hashlib
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

# clause header detection (nearest one above the cited line is "the clause the line belongs to")
HEADER_RE = {
    # D clauses open with bold "**D29 ...**"; I/R clauses open plain.  A plain body line that merely starts with
    # "D64 引用來源卡片..." (inside I38) must not be taken for a header.
    "公理層.md": re.compile(r"^(?:\*\*(D\d+[a-z]?)|([IR]\d+[a-z]?))(?=[ 　（(*:：])"),
    "白話版": re.compile(r"^## ([DIR]\d+[a-z]?)\s*$"),
}
SCOPE_RE = re.compile(r"^[^\n：]{0,24}契約（([KWMH])）：")

LABEL_START_RE = re.compile(r"^(?:- )?(?:改前|現況|新增於|外部核對|全檔出現|證據檔計數)")
LABEL_RE = re.compile(
    r"^(改前|現況|新增於)\((公理層\.md|白話版) ([DIR]\d+[a-z]?) 第 (\d+)(?:[–-](\d+))? 行(?:「([^」]*)」之後)?\):$"
)
EXT_LINE_RE = re.compile(r"^外部核對\(([0-9a-f]{7,40}) (\S+) 第 (\d+) 行「([^」]+)」\):$")
FILE_COUNT_RE = re.compile(r"^證據檔計數\((\S+) 「([^」]+)」 共 (\d+) 行\):$")
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
    """-> (items, problems).  item = dict(kind,...) ; kinds: 改前 現況 新增於 外部行 外部無"""
    lines = text.split("\n")
    items, problems = [], []
    label_line_idx = set()
    for idx, raw in enumerate(lines):
        if not LABEL_START_RE.match(raw):
            continue
        line = raw[2:] if raw.startswith("- ") else raw
        m = LABEL_RE.match(line)
        if m:
            kind, f, clause, a, b, prefix = m.groups()
            a = int(a)
            b = int(b) if b else a
            label_line_idx.add(idx)
            qlines, nxt = parse_quote_block(lines, idx + 1)
            item = dict(kind=kind, file=f, clause=clause, a=a, b=b, prefix=prefix, quote=qlines,
                        after=None, label_line=idx + 1, label=line)
            if kind in QUOTE_KINDS:
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
            items.append(item)
            continue
        m = EXT_LINE_RE.match(line)
        if m:
            label_line_idx.add(idx)
            items.append(dict(kind="外部行", rev=m.group(1), path=m.group(2), a=int(m.group(3)), text=m.group(4),
                              label_line=idx + 1, label=line))
            continue
        m = FILE_COUNT_RE.match(line)
        if m:
            label_line_idx.add(idx)
            items.append(dict(kind="證據檔計數", path=m.group(1), term=m.group(2), count=int(m.group(3)),
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
        if it["kind"] == "證據檔計數":
            name = f"證據檔計數 {it['path']} 「{it['term']}」"
            f = HERE / it["path"]
            if not f.is_file():
                results.append(("FAIL", name, f"{f} does not exist"))
                continue
            n = sum(1 for l in norm(f.read_bytes()).split("\n") if it["term"] in l)
            results.append(("PASS" if n == it["count"] else "FAIL", name,
                            f"{n} line(s) contain it" + ("" if n == it["count"] else f", label says {it['count']}")))
            continue
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
        name = f"{it['kind']} {it['file']} {it['clause']} L{it['a']}" + (f"-{it['b']}" if it["b"] != it["a"] else "")
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
            results.append(("FAIL", name, "; ".join(problems_here)))
        else:
            results.append(("PASS", name, detail.strip()))
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
    print(f"# checked {', '.join(f'{v} {k}' for k, v in kinds.items())}; {bad} failure(s)"
          + (f", {skipped} skipped" if skipped else ""), file=out)
    return ok_all


def selftest(proposal_text: str, ssot: dict[str, str], root: Path) -> bool:
    base, _ = check(proposal_text, ssot, root)
    if any(r[0] != "PASS" for r in base):
        print("selftest: baseline is not green, fix that first")
        return False

    def mutate(old: str, new: str) -> str:
        # first occurrence only: a 改前 quote always precedes the 改後 that repeats part of it
        assert old in proposal_text, f"mutation anchor {old!r} not found in PROPOSAL.md"
        return proposal_text.replace(old, new, 1)

    synthetic_ok = (
        proposal_text
        + "\n現況(公理層.md I38 第 1537 行):\n> 同一候選刪除後經 put 或匯入重建相同卡片／欄位鍵，不能單靠重建滿足刪除保護。\n"
        + "\n新增於(公理層.md R53 第 2486 行「配號只依目標候選 World…」之後):\n> x\n"
    )
    cases = [
        ("one char of a 公理層.md quote changed (D29)", mutate("格線身分為（系統", "格線身份為（系統"), "改前 公理層.md D29"),
        ("one char of a 白話版 quote changed (I5)", mutate("矩形的四條邊也不能跟", "矩形的四條邊也不可跟"), "改前 白話版 I5"),
        ("second line of the two-line R18 quote changed", mutate("（邊界主支為真）但 coversEdge 恆為假（兩端", "（邊界主支為真）但 coversEdge 恆為假（雙端"), "改前 公理層.md R18"),
        ("one char of a clause-title quote changed (I23)", mutate("> I23 網格引用的追溯與重算（2026-09-18 目的翻轉（分層契約）：", "> I23 網格引用的追溯與重算（2026-09-18 目的翻轉（分層合約）："), "改前 公理層.md I23"),
        ("one char of a 現況 quote changed (R13 W lines)", mutate("「資料跟材料走」):", "「資料跟材料走」)；"), "現況 公理層.md R13"),
        ("one char of a 現況 quote changed (R46)", mutate("先驗能力與來源閉包，再在隔離候選重播定義", "先驗能力與來源閉包，再在隔離候選重播定意"), "現況 公理層.md R46"),
        ("one char of a D31 K-block quote changed", mutate("每欄以 (cardId,fieldId) 為身分", "每欄以 (cardId,fieldId) 為身份"), "改前 公理層.md D31"),
        ("line number off by one (I24 1385 -> 1386)", mutate("I24 第 1385 行", "I24 第 1386 行"), "改前 公理層.md I24"),
        ("right line, wrong clause (R22 cited as I24)", mutate("R22 第 2128 行", "I24 第 2128 行"), "改前 公理層.md I24 L2128"),
        ("insertion anchor text wrong", mutate("「band 的切開用另一軸未加相位差的格線…」", "「band 的切開用另一軸未加相位差的格網…」"), "新增於 公理層.md D10b"),
        ("unchecked line citation smuggled in", proposal_text + "\n(見公理層.md 第 625 行)\n", "structure"),
        ("改後 no longer opens like 改前 (prefix drift)", mutate("改後:\n> 相位差守門：", "改後:\n> I24 相位差守門："), "改前 公理層.md I24"),
        ("clause confusion: I38 body line starts with 'D64 ' and is cited as D64", synthetic_ok.replace("現況(公理層.md I38 第 1537 行)", "現況(公理層.md D64 第 1537 行)"), "現況 公理層.md D64 L1537"),
        ("indented insertion anchor wrong (R53)", synthetic_ok.replace("「配號只依目標候選 World…」", "「配號只依目標候選 Worldx…」"), "新增於 公理層.md R53"),
        ("外部核對 cited text wrong (kernel grid_store)", mutate("「static bool geo_grid_axis_stagger_valid」", "「static bool geo_grid_axis_stagger_validx」"), "外部核對行 43305271"),
        ("外部核對無 regex made to match something real", mutate("不含「stagger|", "不含「geo_interval_subdivide|stagger|"), "外部核對無 43305271"),
        ("quoted decision-queue text wrong (Q-A option)", mutate("第 484 行「只准一軸(建議)」", "第 484 行「只准兩軸(建議)」"), "外部核對行 02baea2c"),
        ("全檔出現 grep result goes stale (cardId line list)", mutate("「cardId」 第 691、2251 行", "「cardId」 第 691、2252 行"), "全檔出現 公理層.md 「cardId」"),
        ("cleanup-list sweep goes stale (依以下 line list)", mutate("「依以下」 第 615、1403 行", "「依以下」 第 615、1404 行"), "全檔出現 公理層.md 「依以下」"),
        ("證據檔計數 goes stale (probe results)", mutate("「V_EXTENSION」 共 5 行", "「V_EXTENSION」 共 6 行"), "證據檔計數 s1-probes/errors.txt 「V_EXTENSION」"),
        ("H insertion anchor text wrong (R4)", mutate("「重放只還原記號、不配發…」", "「重放只還原記號、不配法…」"), "新增於 公理層.md R4"),
        ("白話版 insertion anchor text wrong (R4)", mutate("「啟用身分帳後…」", "「啟用身份帳後…」"), "新增於 白話版 R4"),
        ("one char of a 現況 quote changed (R56 提交 definition)", mutate("提交是成功改變既有正式 World 的一筆", "提交是成功改變既有正式 World 的一比"), "現況 公理層.md R56"),
        ("one char of a 現況 quote changed (D29 W, parameter unlink)", mutate("解除參數引用須明示轉為當下有效整數", "解除參數引用須明示轉為當下有效整樹"), "現況 公理層.md D29 L636"),
        ("two-axis search made to match (drop the v half of the regex)", mutate("stagger[^\"]* v repeat[a-z-]*[^\"]*stagger」", "stagger」"), "外部核對無 02baea2c ."),
        ("oracle output count stale (25/81)", mutate("「25/81 cells still enclosed」 共 1 行", "「25/81 cells still enclosed」 共 2 行"), "證據檔計數 s6_stagger_oracle.out"),
        ("cellAtPoint line number off by one", mutate("第 764 行「function cellAtPoint(s, event)」", "第 765 行「function cellAtPoint(s, event)」"), "geometry-web/grid-system-workspace.js:765"),
        ("decision-queue answer text wrong (option two, main 12b25f91)", mutate("第 610 行「選項二 全面版本制」", "第 610 行「選項一 全面版本制」"), "外部核對行 12b25f91 決策佇列.md:610"),
        ("line number of 'unsupported required scene capability' off by one", mutate("第 194 行「I32: unsupported required scene capability」", "第 195 行「I32: unsupported required scene capability」"), "engineering_commands.inc:195"),
        ("project-format rejection message quoted wrong", mutate("第 33 行「專案版本不支援，請使用相容版本開啟。」", "第 33 行「專案版本不支援，請使用相容版本開起。」"), "geometry-web/project-store.js:33"),
        ("one char of a 現況 quote changed (I39 unknown capability)", mutate("未知新能力或缺少必要宣告須在替換現有 World／專案前拒絕", "未知新能力或缺少必要宣告須在替換現有 World／專案後拒絕"), "現況 公理層.md I39"),
        ("one char of a 現況 quote changed (D25 manifest)", mutate("manifest 明寫 schema 版本、公理版本／內容摘要", "manifest 明寫 schema 版本、公理版本／內容摘要x"), "現況 公理層.md D25"),
        ("positive control: the synthetic I38 / R53 labels alone must pass", synthetic_ok, None),
    ]
    all_caught = True
    for desc, mutated, expect in cases:
        res, _ = check(mutated, ssot, root)
        failed = [r for r in res if r[0] == "FAIL"]
        caught = (not failed) if expect is None else any(expect in r[1] for r in failed)
        all_caught &= caught
        print(f"{('PASSED' if expect is None else 'CAUGHT') if caught else 'MISSED'}  {desc}")
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
    ap.add_argument("--skip-external", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    ssot = load_ssot(args.root)
    proposal_text = norm(args.proposal.read_bytes())
    if args.selftest:
        return 0 if selftest(proposal_text, ssot, args.root) else 1
    results, items = check(proposal_text, ssot, args.root, args.skip_external)
    return 0 if report(results, items, ssot) else 1


if __name__ == "__main__":
    sys.exit(main())
