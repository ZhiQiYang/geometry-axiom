#!/usr/bin/env python3
"""List the places where a K (core) text points at W / H text.

Layering rule behind this: dependencies run one way (template -> core).  A K text that says "依以下相容契約"
or names an H clause is the core depending on a layer above it.

What is scanned (公理層.md, CRLF normalised):
  * every clause the file's scope list puts under K, whole body
  * the "核心契約（K）：" block of every clause the list puts under M
What is looked for:
  1. wording that points at the contract written below / at a template or host contract:
       以下…契約 / 以下…schema,  以下限制,  模板契約驗證|指定|選取
  2. a clause id (D/I/R number) that the scope list puts under W or H alone
Not counted: "宿主" as a geometry word (host region, host hole ...), and "由以下任一來源求值" (an enumeration
inside the same K sentence).  A keyword sweep proves nothing about wording it does not contain.

Usage:  python scan_k_pointers.py [--root R]       prints the table, exit code 0
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEAD = re.compile(r"^(?:\*\*(D\d+[a-z]?)|([IR]\d+[a-z]?))(?=[ 　（(*:：])")
SCOPE_LINE = re.compile(r"^([^\n：]{0,24})契約（([KWMH])）：")
POINTER = re.compile(r"以下[^，；。：（）]{0,10}?(?:契約|schema)|以下限制|模板契約(?:驗證|指定|選取)")
CLAUSE_ID = re.compile(r"(?<![A-Za-z0-9])([DIR]\d+[a-z]?)(?![A-Za-z0-9])")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=HERE.parents[2])
    args = ap.parse_args()
    L = (args.root / "公理層.md").read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")

    scope_lists = {}
    for i, l in enumerate(L):
        m = re.match(r"^- \*\*([KMWH])[ 　]", l)
        if m and m.group(1) not in scope_lists and "、" in l:
            scope_lists[m.group(1)] = set(CLAUSE_ID.findall(l.split("：", 1)[1]))
    assert set(scope_lists) == set("KMWH"), scope_lists.keys()
    scope = {c: s for s, cs in scope_lists.items() for c in cs}

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
    print(f"scope list: K {len(scope_lists['K'])}, M {len(scope_lists['M'])}, W {len(scope_lists['W'])}, H {len(scope_lists['H'])}")
    print(f"K text scanned: {len(ktext)} lines in {len({c for _, c, _ in ktext})} clauses\n")

    print("== 1. wording that points at W/H text")
    rows = []
    for i, c, t in ktext:
        for m in POINTER.finditer(t):
            rows.append((i, c, m.group(0), next_block.get(c, "-")))
    for i, c, w, tgt in rows:
        print(f"  L{i:<5} {c:<5} -> {tgt}  「{w}」")
    print(f"  = {len(rows)} hits in {len({c for _, c, _, _ in rows})} clauses\n")

    print("== 2. clause ids that sit under W or H alone")
    refs = []
    for i, c, t in ktext:
        for m in CLAUSE_ID.finditer(t):
            r = m.group(1)
            if r != c and scope.get(r) in ("W", "H"):
                refs.append((i, c, r, scope[r]))
    for i, c, r, s in refs:
        print(f"  L{i:<5} {c:<5} -> {r}({s})")
    print(f"  = {len(refs)} references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
