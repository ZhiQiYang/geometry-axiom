# -*- coding: utf-8 -*-
"""公理層覆蓋率矩陣:每條條文 → 實作在哪、哪個夾具釘它、哪個變異殺得死它。

為什麼要有這個:公理層是驗收基準,但「條文」與「守衛它的東西」之間
目前沒有任何機器查得動的連結,只有註解裡的散文。三個已知的條文/實作
不一致(I22 的「副支可以」、I19 漏掉的 RC 款、dump 丟失放法記錄)
都是靠手工逐條比對才撞到的。

判準(刻意用最笨的方式,好讓它不會說謊):
  實作 = `current_geometry.c` 及其本地 include 來源的某處出現這個條號
  夾具 = 某個 `*.scene` 的註解出現這個條號
  變異 = `tests/mutate.py` 的 desc 出現這個條號

這是**弱代理**,會高估缺口:像 I1 承載面框架合法,每個場景都在跑它,
只是沒人寫下條號。所以紅燈的意思是「這條沒有留下可追溯的連結」,
不等於「這條沒被測到」。要消紅燈的正確做法是補註解把連結寫下來,
不是去改條文。

用法:
  python geometry-guide/axiom_matrix.py            # 報告
  python geometry-guide/axiom_matrix.py --strict   # 有紅燈就以非 0 退出
"""
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

AXIOM = os.path.join(ROOT, "公理層.md")
SRC = os.path.join(ROOT, "current_geometry.c")
MUTATE = os.path.join(ROOT, "tests", "mutate.py")


def read_text(path):
    """current_geometry.c 是 CRLF 且含一個合法的嵌入 NUL byte,
    所以一律以二進位讀進來再寬鬆解碼,不讓工具鏈自作主張。"""
    with open(path, "rb") as f:
        return f.read().decode("utf-8", "replace")


# ------------------------------------------------------------------
# 1. 抽條文
# ------------------------------------------------------------------
def parse_clauses(text):
    """回傳 [(條號, 起始行, 標題摘要, 內文)]，依檔案順序。"""
    lines = text.split("\n")
    marks = []

    for i, ln in enumerate(lines):
        # I/R 類原本沒開字母後綴,導致 I8a 這種子條文被整條漏掉(D 類一直有)。
        # 2026-09-18 補齊,兩邊一致。
        m = re.match(r"\*\*(D\d+[a-z]?)\s", ln) or re.match(r"^([IR]\d+[a-z]?)\s", ln)
        if m:
            marks.append((m.group(1), i))
        elif re.match(r"^## ", ln) and marks:
            marks.append((None, i))          # 章節界線:結束前一條

    out = []
    for k, (cid, start) in enumerate(marks):
        if cid is None:
            continue
        end = marks[k + 1][1] if k + 1 < len(marks) else len(lines)
        body = "\n".join(lines[start:end]).rstrip()
        head = re.sub(r"\*\*", "", lines[start]).strip()
        head = re.sub(r"^" + re.escape(cid) + r"\s*", "", head)
        head = head.split("：")[0].split(":")[0].strip()
        out.append((cid, start + 1, head[:26], body))
    return out


# ------------------------------------------------------------------
# 2. 原始碼:條號出現在哪個函式裡
# ------------------------------------------------------------------
def _strip_code(line, in_block, keep_literals=False):
    """去掉註解與字串;讀 include 指令時保留字串,不把註解當指令。"""
    out = []
    j = 0
    while j < len(line):
        if in_block:
            k = line.find("*/", j)
            if k < 0:
                return "".join(out), True
            in_block = False
            out.append(" ")
            j = k + 2
            continue
        if line.startswith("/*", j):
            in_block = True
            j += 2
            continue
        if line.startswith("//", j):
            break
        if line[j] in "\"'":
            start = j
            q = line[j]
            j += 1
            while j < len(line):
                if line[j] == "\\":
                    j += 2
                    continue
                if line[j] == q:
                    j += 1
                    break
                j += 1
            if keep_literals:
                out.append(line[start:j])
            continue
        out.append(line[j])
        j += 1
    return "".join(out), in_block


def code_sites(src_text, clause_ids):
    """條號在原始碼裡出現的位置。

    區段橫幅註解位在檔案層(大括號深度 0),它講的是**後面**那個函式,
    所以這種位置要往後找、不是往前找——往前找會把「擋面(StopFace)」
    的橫幅歸給上一個毫不相干的函式。
    """
    lines = src_text.split("\n")
    depth = 0
    in_block = False
    line_depth = []
    defs = []                                  # (行index, 函式名)

    for i, raw in enumerate(lines):
        line_depth.append(depth)
        code, in_block = _strip_code(raw, in_block)

        if depth == 0 and not code.lstrip().startswith("#") \
                and not code.rstrip().endswith(";"):
            m = re.match(r"^[A-Za-z_][\w\s\*]*?(\w+)\s*\(", code)
            if m:
                defs.append((i, m.group(1)))

        depth += code.count("{") - code.count("}")

    def owner_of(i):
        if line_depth[i] > 0:                  # 在函式內:往前找
            best = None
            for di, name in defs:
                if di <= i:
                    best = name
                else:
                    break
            return best or "(檔案層)"
        for di, name in defs:                  # 在檔案層:往後找
            if di >= i:
                return name
        return "(檔案層)"

    hits = {c: [] for c in clause_ids}
    if not hits:
        return hits
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(c) for c in hits) + r")\b")

    for i, ln in enumerate(lines):
        seen = set()
        for match in pattern.finditer(ln):
            cid = match.group()
            if cid not in seen:
                hits[cid].append((owner_of(i), i + 1))
                seen.add(cid)
    return hits


def source_texts(entry=None):
    """沿引號 include 收集本地來源,以入口所在目錄為邊界,每檔只讀一次。

    這是文字追溯,不求值 #if 或編譯器 -I。相對路徑可解析的 .h 也可能有
    inline 實作;未解析的標頭可屬條件分支或外部搜尋路徑,不猜替代檔案。
    缺少 .inc/.c 實作片段則報錯,不能靜默變成「無追溯」。
    不展平來源:各檔保留自己的行號與函式作用域,也不改寫 CRLF bytes。
    """
    entry = os.path.realpath(entry or SRC)
    root = os.path.dirname(entry)
    seen, sources = set(), []

    def visit(path):
        path = os.path.realpath(path)
        if path in seen:
            return
        seen.add(path)
        text = read_text(path)
        name = os.path.relpath(path, root).replace(os.sep, "/")
        sources.append((name, text))
        in_block = False
        # C line splicing precedes comment removal; original text stays intact.
        for line in re.sub(r"\\\r?\n", "", text).splitlines():
            directive, in_block = _strip_code(line, in_block, keep_literals=True)
            match = re.fullmatch(r'\s*#\s*include\s*"([^"\n]+)"\s*', directive)
            if not match:
                continue
            child = os.path.realpath(os.path.join(os.path.dirname(path), match[1]))
            if os.path.commonpath([root, child]) != root:
                raise ValueError("include outside source root: %s -> %s" % (name, match[1]))
            if not os.path.isfile(child):
                if os.path.splitext(child)[1] in (".inc", ".c"):
                    raise FileNotFoundError("missing source include: %s -> %s" % (name, match[1]))
                continue
            visit(child)

    visit(entry)
    return sources


def source_code_sites(clause_ids, sources=None):
    """條號 → [(入口相對檔名, 函式名, 該檔 1-based 行號)]。"""
    if sources is None:
        sources = source_texts()
    hits = {cid: [] for cid in clause_ids}
    for path, text in sources:
        for cid, sites in code_sites(text, clause_ids).items():
            hits[cid].extend((path, function, line) for function, line in sites)
    return hits


# ------------------------------------------------------------------
# 3. 夾具與變異
# ------------------------------------------------------------------
def scene_hits(clause_ids):
    hits = {c: [] for c in clause_ids}
    pats = {c: re.compile(r"\b" + re.escape(c) + r"\b") for c in clause_ids}

    for path in sorted(glob.glob(os.path.join(ROOT, "*.scene"))):
        body = io.open(path, encoding="utf-8", errors="replace").read()
        name = os.path.basename(path)
        for c, p in pats.items():
            if p.search(body):
                hits[c].append(name)
    return hits


def mutant_hits(clause_ids):
    hits = {c: [] for c in clause_ids}
    if not os.path.exists(MUTATE):
        return hits

    body = io.open(MUTATE, encoding="utf-8", errors="replace").read()
    entries = re.findall(r'dict\(id="(M\d+)",\s*desc="([^"]*)"', body)
    pats = {c: re.compile(r"\b" + re.escape(c) + r"\b") for c in clause_ids}

    for mid, desc in entries:
        for c, p in pats.items():
            if p.search(desc):
                hits[c].append(mid)
    return hits


# ------------------------------------------------------------------
# 4. 錯誤碼:條文宣告的 V_* 必須在原始碼裡找得到
# ------------------------------------------------------------------
def error_codes(clauses, src_text):
    bad = []
    for cid, _, _, body in clauses:
        for code in sorted(set(re.findall(r"\bV_[A-Z_]+\b", body))):
            if code not in src_text:
                bad.append((cid, code))
    return bad


def main():
    strict = "--strict" in sys.argv

    axiom_text = read_text(AXIOM)
    sources = source_texts()
    src_text = "\n".join(text for _, text in sources)

    clauses = parse_clauses(axiom_text)
    ids = [c[0] for c in clauses]

    code = source_code_sites(ids, sources)
    scenes = scene_hits(ids)
    mutants = mutant_hits(ids)

    red, yellow, green = [], [], []
    for cid, line, head, _ in clauses:
        has_code = bool(code[cid])
        has_fix = bool(scenes[cid])
        row = (cid, line, head, code[cid], scenes[cid], mutants[cid])
        if not has_code and not has_fix:
            red.append(row)
        elif not (has_code and has_fix):
            yellow.append(row)
        else:
            green.append(row)

    print("公理層覆蓋率矩陣")
    print("=" * 74)
    print("條文 %d 條  |  綠 %d  黃 %d  紅 %d"
          % (len(clauses), len(green), len(yellow), len(red)))
    print("  綠 = 原始碼與夾具都留下了條號")
    print("  黃 = 只有一邊留下條號")
    print("  紅 = 兩邊都沒有,這條完全沒有可追溯的連結")
    print("  註:量的是「條號在哪裡被提到」,不是「哪裡實作了它」。")
    print("     紅燈代表沒有可追溯的連結,不代表沒被測到。")
    print("     掃描入口與可解析的本地 include (%d 檔);不求值 #if / -I,未解析標頭不計。" % len(sources))
    print()

    print("── 紅燈 %d 條 ──" % len(red))
    for cid, line, head, _, _, _ in red:
        print("  %-5s L%-4d %s" % (cid, line, head))
    print()

    print("── 黃燈 %d 條 ──" % len(yellow))
    for cid, line, head, cs, ss, ms in yellow:
        where = ("原始碼 " + ", ".join(sorted({f for _, f, _ in cs})[:2])) if cs \
                else ("夾具 " + ", ".join(ss[:2]))
        print("  %-5s L%-4d %-24s 缺%s  有%s"
              % (cid, line, head[:24], "夾具" if cs else "原始碼", where[:38]))
    print()

    print("── 綠燈 %d 條 ──" % len(green))
    for cid, line, head, cs, ss, ms in green:
        fn = ", ".join(sorted({f for _, f, _ in cs})[:2])
        print("  %-5s %-24s 原始碼 %-32s 夾具 %d  變異 %s"
              % (cid, head[:24], fn[:32], len(ss), ",".join(ms) if ms else "無"))
    print()

    bad = error_codes(clauses, src_text)
    print("── 錯誤碼對照 ──")
    if bad:
        for cid, c in bad:
            print("  %s 宣告的 %s 在原始碼裡找不到" % (cid, c))
    else:
        print("  條文宣告的 V_* 錯誤碼全部在原始碼裡找得到")

    if strict and red:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
