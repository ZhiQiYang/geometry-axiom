# -*- coding: utf-8 -*-
"""檢查導讀頁每個面板的符號與 callout 都能在目前的 current_geometry.c 找到。

範圍定位邏輯與頁內 JS（findFunction / findTypedef / findSection / narrow）一致：
callout 必須落在該面板實際抽出的行範圍內，不是全檔任一處。
"""
import io
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
LINES = io.open(HERE.parent / "current_geometry.c", encoding="utf-8").read().split("\n")
html = io.open(HERE / "current_geometry-導讀.html", encoding="utf-8").read()


def with_leading_comment(start):
    i = start - 1
    if i >= 0 and LINES[i].strip() == "*/":
        while i > 0 and not LINES[i].startswith("/*"):
            i -= 1
        return i
    if i >= 0 and re.match(r"^/\*.*\*/\s*$", LINES[i]):
        return i
    return start


def find_function(name):
    re_sig = re.compile(r"^(static|int)\b[^\n]*\b" + re.escape(name) + r"\(")
    for i, l in enumerate(LINES):
        if not re_sig.match(l):
            continue
        o = i
        while o < len(LINES) and LINES[o] != "{" and not re.search(r";\s*$", LINES[o]):
            o += 1
        if o >= len(LINES) or LINES[o] != "{":
            continue  # 前置宣告，跳過
        c = o + 1
        while c < len(LINES) and LINES[c] != "}":
            c += 1
        return (with_leading_comment(i), c)
    return None


def find_typedef(name):
    for i, l in enumerate(LINES):
        if l == "} " + name + ";":
            t = i
            while t > 0 and not LINES[t].startswith("typedef"):
                t -= 1
            return (with_leading_comment(t), i)
    return None


def find_section(title):
    for k, l in enumerate(LINES):
        if l == " * " + title and k > 0 and LINES[k - 1].startswith("/* ===="):
            s = k + 2
            e = s
            while e < len(LINES) and not LINES[e].startswith("/* ===="):
                e += 1
            e -= 1
            while e > s and LINES[e].strip() == "":
                e -= 1
            while s < e and LINES[s].strip() == "":
                s += 1
            return (s, e)
    return None


def narrow(rng, frm, to):
    if not rng:
        return rng
    s, e = rng
    if frm:
        rf = re.compile(frm)
        for i in range(s, e + 1):
            if rf.search(LINES[i]):
                s = i
                break
    if to:
        rt = re.compile(to)
        for i in range(s + 1, e + 1):
            if rt.search(LINES[i]):
                e = i
                break
    return (s, e)


bad = []
count = 0
for m in re.finditer(r"data-panel='(\{.*?\})'", html):
    count += 1
    cfg = json.loads(m.group(1).replace("&lt;", "<").replace("&gt;", ">"))
    kind = cfg["kind"]
    key = cfg.get("name") or cfg.get("title")
    if kind == "fn":
        rng = find_function(cfg["name"])
    elif kind == "type":
        rng = find_typedef(cfg["name"])
    elif kind == "range":
        rng = (0, len(LINES) - 1)
    else:
        rng = find_section(cfg["title"])
    rng = narrow(rng, cfg.get("from"), cfg.get("to"))
    if not rng:
        bad.append(("panel", key))
        continue
    s, e = rng
    body = LINES[s:e + 1]
    for c in cfg.get("callouts", []):
        if not any(re.search(c["match"], l) for l in body):
            bad.append(("callout", key, "lines %d-%d" % (s + 1, e + 1), c["match"][:50]))

print("panels:", count)
print("unresolved:", bad if bad else "none")
raise SystemExit(1 if bad else 0)
