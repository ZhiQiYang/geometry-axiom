"""把已採納的 GEO-262 提案(#250 f3f99a29)寫入 公理層.md 與 公理層-白話.md。
所有條文與白話文字都從 PROPOSAL.md 以程式取出,只做三種替換:D-CR1→D64、I-CR1→I74、R-CR1→R60。
用法: python apply.py <worktree>
"""
import re
import sys
from pathlib import Path

W = Path(sys.argv[1])
PROP = (W / "geometry-core/card-reference/PROPOSAL.md").read_text(encoding="utf-8")
RENUM = (("D-CR1", "D64"), ("I-CR1", "I74"), ("R-CR1", "R60"))


def renum(s):
    for a, b in RENUM:
        s = s.replace(a, b)
    return s


def section(title_prefix):
    start = PROP.index("\n### " + title_prefix)
    nxt = [i for i in (PROP.find("\n### ", start + 5), PROP.find("\n## ", start + 5)) if i != -1]
    return PROP[start:min(nxt)]


def code_blocks(sec):
    return re.findall(r"```text\n(.*?)\n```", sec, re.S)


def white_text(sec):
    """取出「白話 …」段的新增文字:行內「後增「…」」/「新增「…」」,或冒號後接的 > 引文。"""
    lines = sec.split("\n")
    for i, line in enumerate(lines):
        if not line.startswith("白話"):
            continue
        for key in ("後增「", "新增「"):
            if key in line and line.rstrip().endswith("」"):
                k = line.index(key) + len(key)
                return line[k:line.rstrip().rindex("」")]
        if line.rstrip().endswith(("後增：", "新增：", "後增:", "新增:")):
            out = []
            for nxt in lines[i + 1:]:
                if nxt.startswith("> "):
                    out.append(nxt[2:])
                elif out:
                    break
            assert out, line
            return "\n".join(out)
    raise AssertionError("no white text in " + sec[:40])


def new_white(sec):
    lines = sec.split("\n")
    i = lines.index("白話新增段：")
    out = []
    for nxt in lines[i + 1:]:
        if nxt.startswith("> "):
            out.append(nxt[2:])
        elif out:
            break
    return "\n".join(out)


# ---------------------------------------------------------------- 公理層.md
ssot_path = W / "公理層.md"
raw = ssot_path.read_bytes()
crlf = b"\r\n" in raw
S = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
original_S = list(S)


def find_block(block):
    want = [l.strip() for l in block.split("\n")]
    hits = [i for i in range(len(S) - len(want) + 1) if all(S[i + k].strip() == want[k] for k in range(len(want)))]
    assert len(hits) == 1, (block[:30], hits)
    return hits[0], len(want)


def find_line(text):
    hits = [i for i, l in enumerate(S) if text in l]
    assert len(hits) == 1, (text[:30], hits)
    return hits[0]


ops = {  # E 編號 -> 動作
    "E1": "append", "E2": "replace", "E3": "replace", "E4": "append", "E5": "replace",
    "E6": "append", "E7": "append", "E8": "replace", "E9": "append", "E10": "append",
}
extra_anchor = {
    "E2": "解除參數引用須明示轉為當下有效整數，經 I8a 預覽；不在網格內保存第二份可獨立編輯的有效值。",
    "E8": "其中 D29 允許的尺寸 token 可為既有整數或 `param:<卡片id>:<欄位id>`，dump 保留來源 token。",
}
log = []
# 先找全部位置,再由下往上改,避免行號位移
edits = []
for e, op in ops.items():
    bs = code_blocks(section(e + "："))
    i, n = find_block(bs[0])
    new = renum(bs[1]).split("\n")
    edits.append((i, n, op, new, e))
    if e in extra_anchor:
        j = find_line(extra_anchor[e])
        edits.append((j, 1, "append", renum(bs[2]).split("\n"), e + "+"))
# 新條文:D64 接在 D63 區塊後、I74 接在 I73 區塊後、R60 接在 R59 區塊後(下一個章節標題前的空行之前)
def block_end(head_regex, next_heading):
    i = [k for k, l in enumerate(S) if re.match(head_regex, l)]
    assert len(i) == 1, head_regex
    j = next(k for k in range(i[0] + 1, len(S)) if S[k].startswith(next_heading))
    while S[j - 1].strip() == "":
        j -= 1
    return j  # 插入點(在此行之前插入)

d_body = renum(code_blocks(section("D-CR1："))[0]).split("\n")
i_body = renum(code_blocks(section("I-CR1："))[0]).split("\n")
r_body = renum(code_blocks(section("R-CR1："))[0]).split("\n")
new_clauses = [
    # 比照最近新增的 D63/I73/R59:新條文前空一行
    (block_end(r"^\*\*D63 ", "## 二、"), ["", "**D64 網格卡片引用（GridCardReference）**：" + d_body[0]] + d_body[1:], "D64"),
    (block_end(r"^I73 ", "## 三、"), ["", "I74 完整、唯一且合法的整組來源："] + ["    " + l for l in i_body], "I74"),
    (block_end(r"^R59 ", "## 四、"), ["", "R60 整卡交易、求值及保存："] + ["    " + l for l in r_body], "R60"),
]
banner_anchor = [k for k, l in enumerate(S) if l.startswith("> **空間模型納入拉伸件已採納（2026-10-11，Q38j／GEO-256）**")]
assert len(banner_anchor) == 1
k = banner_anchor[0]
while S[k + 1].startswith("> "):
    k += 1
banner = [
    "",
    "> **整卡參數引用已採納（2026-10-15，GEO-262）**：依使用者 2026-10-15 選擇「採納,開始實作」及兩輪對抗審查（#250 的 P-120／P-124／P-130），",
    "> 依 `geometry-core/card-reference/PROPOSAL.md` 新增 D64 / I74 / R60（`grid-card-reference/1`），並修訂 D9、D25、D29、D31、I8a、I37、I38、I39、R32、R33。",
    "> I38 新增的「刪除後同鍵重建，引用者須在最後一次刪除之後明示重新宣告」同時適用於既有逐欄引用。條文採納不等於功能已完成；未實作前不得宣稱支援。",
]
for pos, n, op, new, e in sorted(edits + [(p, 0, "insert", body, name) for p, body, name in new_clauses]
                                 + [(k + 1, 0, "insert", banner, "banner")], key=lambda x: -x[0]):
    if op == "replace":
        S[pos:pos + n] = new
    elif op == "append":
        S[pos + n:pos + n] = new
    else:
        S[pos:pos] = new
    log.append((e, op, pos + 1, len(new)))
out = "\n".join(S)
ssot_path.write_bytes((out.replace("\n", "\r\n") if crlf else out).encode("utf-8"))

# ---------------------------------------------------------------- 公理層-白話.md
wp = W / "geometry-guide/公理層-白話.md"
wraw = wp.read_bytes()
wcrlf = b"\r\n" in wraw
WL = wraw.decode("utf-8").replace("\r\n", "\n").split("\n")
white_map = {"E1": "D9", "E2": "D29", "E3": "D31", "E4": "I8a", "E5": "I37", "E6": "I38",
             "E7": "I39", "E8": "R32", "E9": "R33", "E10": "D25"}


def white_section_end(code):
    i = [k for k, l in enumerate(WL) if l == "## " + code]
    assert len(i) == 1, code
    j = next((k for k in range(i[0] + 1, len(WL)) if WL[k].startswith("## ")), len(WL))
    while WL[j - 1].strip() == "":
        j -= 1
    return j


wedits = []
for e, code in white_map.items():
    txt = renum(white_text(section(e + "：")))
    wedits.append((white_section_end(code), [""] + txt.split("\n"), code))
for title, code, after in (("D-CR1：", "D64", "D63"), ("I-CR1：", "I74", "I73"), ("R-CR1：", "R60", "R59")):
    txt = renum(new_white(section(title)))
    pos = white_section_end(after)
    wedits.append((pos, ["", "## " + code] + txt.split("\n"), code))
for pos, new, code in sorted(wedits, key=lambda x: -x[0]):
    WL[pos:pos] = new
    log.append(("white " + code, "insert", pos + 1, len(new)))
wout = "\n".join(WL)
wp.write_bytes((wout.replace("\n", "\r\n") if wcrlf else wout).encode("utf-8"))
for row in sorted(log, key=lambda x: x[2]):
    print(row)
