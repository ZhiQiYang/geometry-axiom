#!/usr/bin/env python3
"""List the places where a K (core) text points at W / H text, or uses a host (H) notion.

Layering rule behind this: dependencies run one way (template -> core).  A K text that says "依以下相容契約"
or names an H clause is the core depending on a layer above it.  The layering preface also gives the public
parser / serialisation, canvas and model exchange to the host (公理層.md, 分層前言 "H：宿主與相容契約"), so a K text
that says "讀入", "畫出的", "put" or "匯入" leans on a host notion just the same.

What is scanned (公理層.md, CRLF normalised):
  * every clause the file's scope list puts under K, whole body
  * the "核心契約（K）：" block of every clause the list puts under M
What is looked for:
  1. wording that points at the contract written below / at a template or host contract:
       以下…契約 / 以下…schema,  以下限制,  模板契約驗證|指定|選取
  2. a clause id (D/I/R number) that the scope list puts under W or H alone
  3. host vocabulary (H_VOCAB below): reading / saving files, drawing, the UI, put / import / export, DSL, dump
Not counted: "宿主" as a geometry word (host region, host hole ...), and "由以下任一來源求值" (an enumeration
inside the same K sentence).  A keyword sweep proves nothing about wording it does not contain.

Two modes:
  python scan_k_pointers.py [--root R]     the table for the current 公理層.md (main); exit code 0
  python scan_k_pointers.py --after        the same scan on the post-edit 公理層.md of every variant combination of
                                           ../PROPOSAL.md (built by check_quotes.py), compared clause by clause with
                                           main.  Exit code 1 if a 案乙 combination ADDS any hit to the K text
                                           (案甲 keeps "見 H（R53、I67）" in K by design and is reported only).
  python scan_k_pointers.py --selftest     inject K pointers / host words into the proposal's K edits; each must be
                                           reported as an added hit by --after
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_quotes  # noqa: E402  (same directory; builds the post-edit text)

HEAD = re.compile(r"^(?:\*\*(D\d+[a-z]?)|([IR]\d+[a-z]?))(?=[ 　（(*:：])")
SCOPE_LINE = re.compile(r"^([^\n：]{0,24})契約（([KWMH])）：")
POINTER = re.compile(r"以下[^，；。：（）]{0,10}?(?:契約|schema)|以下限制|模板契約(?:驗證|指定|選取)")
CLAUSE_ID = re.compile(r"(?<![A-Za-z0-9])([DIR]\d+[a-z]?)(?![A-Za-z0-9])")
H_VOCAB = re.compile(r"讀入|載入|讀檔|存回|存檔|開檔|舊檔|檔案|場景檔|畫出|畫布|介面|點選|匯入|匯出|序列化"
                     r"|(?<![A-Za-z])(?:put|parser|dump|DSL)(?![A-Za-z])")


def scope_map(L: list[str]) -> dict[str, str]:
    scope_lists = {}
    for l in L:
        m = re.match(r"^- \*\*([KMWH])[ 　]", l)
        if m and m.group(1) not in scope_lists and "、" in l:
            scope_lists[m.group(1)] = set(CLAUSE_ID.findall(l.split("：", 1)[1]))
    assert set(scope_lists) == set("KMWH"), scope_lists.keys()
    return {c: s for s, cs in scope_lists.items() for c in cs}


def k_text(L: list[str], scope: dict[str, str]):
    """-> (list of (line no, clause, text), {clause: first W/H block after K})"""
    heads = [(i, next(g for g in HEAD.match(l).groups() if g)) for i, l in enumerate(L, 1) if HEAD.match(l)]
    ktext, next_block = [], {}
    for n, (a, c) in enumerate(heads):
        b = heads[n + 1][0] - 1 if n + 1 < len(heads) else len(L)
        sc = scope.get(c)
        cur = None
        for i in range(a, b + 1):
            m = SCOPE_LINE.match(L[i - 1])
            if m:
                cur = m.group(2)
                if cur in "WH" and c not in next_block:
                    next_block[c] = cur
            if sc == "K" or (sc == "M" and cur == "K"):
                ktext.append((i, c, L[i - 1]))
    return ktext, next_block


def hits(ktext, scope):
    """-> list of (line, clause, category, matched text)"""
    out = []
    for i, c, t in ktext:
        for m in POINTER.finditer(t):
            out.append((i, c, "1 pointer", m.group(0)))
        for m in CLAUSE_ID.finditer(t):
            r = m.group(1)
            if r != c and scope.get(r) in ("W", "H"):
                out.append((i, c, "2 clause", f"{r}({scope[r]})"))
        for m in H_VOCAB.finditer(t):
            out.append((i, c, "3 host word", m.group(0)))
    return out


def load(root: Path) -> list[str]:
    return check_quotes.norm((root / "公理層.md").read_bytes()).split("\n")


def table(L: list[str]) -> int:
    scope = scope_map(L)
    ktext, next_block = k_text(L, scope)
    found = hits(ktext, scope)
    n = Counter(s for s in scope.values())
    print(f"scope list: K {n['K']}, M {n['M']}, W {n['W']}, H {n['H']}")
    print(f"K text scanned: {len(ktext)} lines in {len({c for _, c, _ in ktext})} clauses\n")
    titles = {"1 pointer": "wording that points at W/H text", "2 clause": "clause ids that sit under W or H alone",
              "3 host word": "host (H) vocabulary in K text"}
    for cat, title in titles.items():
        rows = [h for h in found if h[2] == cat]
        print(f"== {cat[0]}. {title}")
        for i, c, _, w in rows:
            tgt = f" -> {next_block.get(c, '-')}" if cat == "1 pointer" else ""
            print(f"  L{i:<5} {c:<5}{tgt}  「{w}」")
        print(f"  = {len(rows)} hits in {len({h[1] for h in rows})} clauses\n")
    return 0


def added_hits(main_L: list[str], after_L: list[str]):
    """Per clause, hits in the post-edit K text minus hits in main's K text (a multiset difference, so a hit that
    was already in an edited line is not counted again).  -> (added, removed) as Counters of (clause, cat, word)."""
    def bag(L):
        scope = scope_map(L)
        return Counter((c, cat, w) for _, c, cat, w in hits(k_text(L, scope)[0], scope))
    before, after = bag(main_L), bag(after_L)
    return after - before, before - after


def after_mode(root: Path, proposal: Path, quiet: bool = False) -> int:
    ssot = check_quotes.load_ssot(root)
    text = check_quotes.norm(proposal.read_bytes())
    items, problems = check_quotes.parse_proposal(text)
    if problems:
        print("proposal does not parse: " + "; ".join(problems))
        return 2
    main_L = ssot["公理層.md"].split("\n")
    status = 0
    for combo in check_quotes.variant_combinations():
        texts, probs = check_quotes.apply_edits(items, ssot, combo)
        if probs:
            print(f"{'+'.join(combo)}: edits do not apply: {'; '.join(probs)}")
            status = 1
            continue
        added, removed = added_hits(main_L, texts["公理層.md"].split("\n"))
        enforced = "案乙" in combo
        verdict = ("CLEAN" if not added else ("ADDED" if enforced else "ADDED (案甲, reported only)"))
        if added and enforced:
            status = 1
        if not quiet:
            print(f"== after {'+'.join(combo)}{' (recommended)' if combo == check_quotes.RECOMMENDED else ''}: {verdict}")
            for (c, cat, w), k in sorted(added.items()):
                print(f"  + {c:<5} {cat:<11} 「{w}」" + (f" x{k}" if k > 1 else ""))
            for (c, cat, w), k in sorted(removed.items()):
                print(f"  - {c:<5} {cat:<11} 「{w}」" + (f" x{k}" if k > 1 else ""))
    if not quiet:
        print("K text after the edits adds no pointer / W-H clause id / host word in any 案乙 combination"
              if status == 0 else "SOME 案乙 COMBINATION ADDS A K POINTER OR HOST WORD")
    return status


def selftest(root: Path, proposal: Path) -> int:
    import tempfile
    text = check_quotes.norm(proposal.read_bytes())
    if after_mode(root, proposal, quiet=True) != 0:
        print("selftest: baseline --after is not clean, fix that first")
        return 1
    k_after = "，cell 只是定位矩形，不是線段圍出的區域。"   # the end of the D10b K sentence the proposal adds
    cases = [
        ("host word 讀入 in the D10b K addition", k_after, "，cell 只是定位矩形，讀入時照舊，不是線段圍出的區域。"),
        ("host word 畫出 in the D10b K addition", k_after, "，cell 只是定位矩形，不是畫出的線段圍出的區域。"),
        ("pointer 依以下相容契約 in the D10b K addition", k_after, "，cell 只是定位矩形，依以下相容契約處理。"),
        ("H clause id R4 in the D10b K addition", k_after, "，cell 只是定位矩形（R4），不是線段圍出的區域。"),
    ]
    ok_all = True
    with tempfile.TemporaryDirectory() as tmp:
        for desc, old, new in cases:
            assert text.count(old) >= 1, f"selftest anchor {old!r} missing from PROPOSAL.md"
            p = Path(tmp) / "PROPOSAL.md"
            p.write_text(text.replace(old, new), encoding="utf-8")
            caught = after_mode(root, p, quiet=True) == 1
            ok_all &= caught
            print(f"{'CAUGHT ' if caught else 'MISSED '} {desc}")
    print("selftest: " + ("every injected K pointer / host word was caught" if ok_all else "SOME WERE MISSED"))
    return 0 if ok_all else 1


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=HERE.parents[2])
    ap.add_argument("--proposal", type=Path, default=check_quotes.DEFAULT_PROPOSAL)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--after", action="store_true")
    mode.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.after:
        return after_mode(args.root, args.proposal)
    if args.selftest:
        return selftest(args.root, args.proposal)
    return table(load(args.root))


if __name__ == "__main__":
    sys.exit(main())
