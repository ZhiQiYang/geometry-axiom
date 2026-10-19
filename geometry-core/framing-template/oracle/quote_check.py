"""引文逐字檢查:文件與程式裡引用使用者的話、決策佇列標題、佇列原文的「…」,必須逐字(位元組相同)出現在 origin/main 的
`決策佇列.md` 裡對的地方。

每一段「」先分種類(看引號前 10 個字;句子 = 同一行裡以 。;；| 切開的一段):
- 標題:前面有「決策佇列」(例:決策佇列「2026-10-16 縫上副支撞到邊界角材」)→ 要出現在佇列的標題行(# 開頭)。
- 佇列原文:前面有「逐字」(例:第 3 題記的是(逐字):「…」)→ 要出現在佇列的任一行。
- 使用者的話:前面有 原話、原文、拍板,或這一句(拿掉所有引號內文之後)提到「使用者」,或在 README「使用者講過的規則」
  那張表的第一欄 → 要出現在佇列的使用者原話行(去掉行首空白後以 > 開頭的引用行)。協調 agent 整理的要點、題目文字都不算。
- 緊接在另一段後面(」「)的,與前一段同種類。
- 「不是使用者原話」之類的字樣不會讓引號免檢:只要句子提到使用者,引號裡就必須是逐字的原話(或改用別的寫法)。

比對:引文裡的「…」(U+2026)代表省略,切開的各段要依序出現在同一行;切成兩段以上時每段至少 MIN_FRAG 個字
(防止「主…支…斷」這種碎片)。其他字元(含全形/半形、空白個數、半形 ...)都要一模一樣。
同一行「與」數目不同(引文跨行),而這一行有上述標記或提到使用者時也報錯:引文要寫在同一行。

用法:python quote_check.py [--queue 檔案];不給 --queue 時用 `git show origin/main:決策佇列.md`。
原始碼突變在 repo 外的副本裡跑(沒有 git),由環境變數 FRAMING_QUOTE_QUEUE 指定一份事先從 origin/main 取出的同一個檔。"""
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TPL = HERE.parent  # geometry-core/framing-template
FILES = [TPL / "oracle" / "README.md", TPL / "PROPOSAL.md", TPL / "oracle" / "framing_oracle.py", TPL / "oracle" / "selftest.py"]
USER_MARKERS = ("原話", "原文", "拍板")
TITLE_MARKER = "決策佇列"
QUEUE_MARKER = "逐字"
USER_TABLE = "## 使用者講過的規則"
SEP = "。;；|"
MIN_FRAG = 6


def queue_source():
    return ("FRAMING_QUOTE_QUEUE=" + os.environ["FRAMING_QUOTE_QUEUE"]) if os.environ.get("FRAMING_QUOTE_QUEUE") else "origin/main"


def queue_from_origin_main():
    if os.environ.get("FRAMING_QUOTE_QUEUE"):
        return pathlib.Path(os.environ["FRAMING_QUOTE_QUEUE"]).read_text(encoding="utf-8")
    top = subprocess.run(["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
                         capture_output=True, check=True).stdout.decode("utf-8").strip()
    out = subprocess.run(["git", "-C", top, "show", "origin/main:決策佇列.md"], capture_output=True, check=True).stdout
    return out.decode("utf-8")


def sources(queue):
    """佇列分三組行:使用者原話行(> 引用行)、標題行(# 開頭)、全部。"""
    lines = queue.splitlines()
    return dict(user=[l for l in lines if l.lstrip().startswith(">")],
                title=[l for l in lines if l.lstrip().startswith("#")],
                queue=lines)


def pairs(line):
    """同一行裡配對好的「」(可巢狀),回傳 (開, 關) 的位置,依開的位置排序。"""
    st, out = [], []
    for i, ch in enumerate(line):
        if ch == "「":
            st.append(i)
        elif ch == "」" and st:
            out.append((st.pop(), i))
    return sorted(out)


def unquoted(seg):
    """句子拿掉所有「」內文(含巢狀)之後的文字。"""
    out, depth = [], 0
    for ch in seg:
        if ch == "「":
            depth += 1
        elif ch == "」" and depth:
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def segment(line, j):
    lo = max([line.rfind(c, 0, j) for c in SEP]) + 1
    his = [k for k in (line.find(c, j) for c in SEP) if k >= 0]
    return line[lo:min(his) if his else len(line)]


def claimed(text, user_table=False):
    """回傳 [(行號, 種類, 引文)] 與跨行的可疑行 [(行號, 該行)]。"""
    out, split = [], []
    in_table = False
    for ln, line in enumerate(text.splitlines(), 1):
        if user_table and line.startswith("## "):
            in_table = line.startswith(USER_TABLE)
        cell_end = line.find("|", 1) if (in_table and line.startswith("|")) else -1
        kinds = {}  # 關引號位置 → 種類(給緊接的下一段)
        for j, i in pairs(line):
            pre = line[max(0, j - 10):j]
            kind = None
            if TITLE_MARKER in pre:
                kind = "title"
            elif QUEUE_MARKER in pre:
                kind = "queue"
            elif (j - 1) in kinds:
                kind = kinds[j - 1]
            elif any(m in pre for m in USER_MARKERS) or "使用者" in unquoted(segment(line, j)) or 0 < j < cell_end:
                kind = "user"
            if kind:
                out.append((ln, kind, line[j + 1:i]))
                kinds[i] = kind
        if line.count("「") != line.count("」") and (any(m in line for m in USER_MARKERS + (TITLE_MARKER, QUEUE_MARKER)) or "使用者" in line):
            split.append((ln, line))
    return out, split


def found(q, lines):
    frags = [f for f in q.split("…") if f]
    if not frags:
        return False
    if len(frags) > 1 and any(len(f) < MIN_FRAG for f in frags):
        return False
    for ql in lines:
        pos, ok = 0, True
        for f in frags:
            k = ql.find(f, pos)
            if k < 0:
                ok = False
                break
            pos = k + len(f)
        if ok:
            return True
    return False


WHERE = dict(user="使用者原話行(> 引用行)", title="佇列標題行", queue="佇列")


def scan_text(name, text, queue, user_table=False):
    """回傳 (檢查的引文數, 問題清單 [(檔名:行號, 原因, 引文)])。"""
    src = sources(queue)
    qs, split = claimed(text, user_table)
    bad = [(f"{name}:{ln}", f"不在{WHERE[k]}裡(要逐字)", q) for ln, k, q in qs if not found(q, src[k])]
    bad += [(f"{name}:{ln}", "引文跨行(要寫在同一行)", line[:60]) for ln, line in split]
    return len(qs), bad


def scan(queue, files=FILES):
    n, bad = 0, []
    for f in files:
        k, b = scan_text(f.name, f.read_text(encoding="utf-8"), queue, user_table=f.name == "README.md")
        n += k
        bad += b
    return n, bad


# 反例與正例(用真的佇列內容)。反例:空白個數不同、錯一個字、改寫、引用協調 agent 整理的要點、用 … 切碎片、
# 沒有標記詞但句子提到使用者、前面寫「不是使用者原話」想豁免、緊接的第二段捏造、標記詞離得遠、標題不存在。
SAMPLES = [
    ("原話「端面頂的是角材才能固定 ...那你讓」", True),   # 佇列是兩個空白
    ("原話「端面頂的是角材才能固定  ...那你讓」", False),
    ("原話講的「連接角材正交/平行」", True),            # 佇列是「連接角材 才會正交/平行」
    ("原話講的「…連接角材 才會正交/平行」", False),
    ("使用者原話(兩行):「??? 主支為什麼要斷開 ?」「不能斷開啊」", True),  # 第二段錯一個字(阿→啊)
    ("使用者原話(兩行):「??? 主支為什麼要斷開 ?」「不能斷開阿」", False),
    ("| 「間隔差了1~2mm 影響不大」(台北 10-15 05:51) | x |", True),   # 使用者規則表第一欄,多一個空白
    ("使用者原話「封板裁切只在對牆，不置中」", True),       # 佇列裡是協調 agent 整理的要點,不是 > 原話行
    ("使用者回答「對,只在對牆、不置中」", False),          # 這才是 > 原話行
    ("使用者原話「主…支…斷」", True),                      # 用 … 切成單字碎片
    ("使用者 10-15 說「只在對牆就好不用置中」", True),     # 沒有標記詞,但句子提到使用者
    ("(前句不是使用者原話)原話「完全捏造的一句話」", True),  # 「不是使用者原話」不豁免
    ("使用者原話「可能最後一步 會有點誤差」「完全捏造」", True),  # 緊接的第二段捏造
    ("原話「可能最後一步 會有點誤差」「完全捏造」", True),  # 同上,句子沒提使用者:只靠「緊接」那條規則
    ("使用者的意思,寫在很前面的這一句,後來才引用「完全捏造的一句話」", True),  # 標記詞離得遠也要查
    ("決策佇列「不存在的標題」", True),
    ("決策佇列「2026-10-16 縫上副支撞到邊界角材」", False),
    ("推論原則「支撐能調整就調整」", False),               # 沒提使用者、沒有標記:不是引用使用者
]


def self_check(queue):
    """回傳判錯的樣本;空的代表反例都抓到、正例都過。"""
    wrong = []
    for s, want_bad in SAMPLES:
        text = USER_TABLE + "\n" + s if s.startswith("|") else s
        _, bad = scan_text("sample", text, queue, user_table=True)
        if bool(bad) != want_bad:
            wrong.append((s, "應報錯" if want_bad else "不應報錯", bad))
    return wrong


if __name__ == "__main__":
    if "--queue" in sys.argv:
        queue = pathlib.Path(sys.argv[sys.argv.index("--queue") + 1]).read_text(encoding="utf-8")
    else:
        queue = queue_from_origin_main()
    n, bad = scan(queue)
    wrong = self_check(queue)
    print(f"檢查的引文 {n} 段,不在 origin/main 決策佇列.md 對應位置的 {len(bad)} 段;反例/正例判錯 {len(wrong)} 個")
    for x in bad + wrong:
        print("   ", x)
    sys.exit(1 if bad or wrong else 0)
