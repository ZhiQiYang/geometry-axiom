"""引文逐字檢查:文件與程式裡標成使用者原話的「…」,必須逐字(位元組相同)出現在 origin/main 的 `決策佇列.md`。

哪些「」算是「標成原話」:
- 「 前面 10 個字內出現 原話、原文、逐字、拍板、決策佇列 其中之一(例:原話「…」、選項原文「…」、拍板「乙 同一治具 367」、
  決策佇列「2026-10-16 縫上副支撞到邊界角材」);前面 16 個字內出現「非使用者原話」「不是使用者原話」的不算;
- 緊接在另一段算數的引文後面(」「,例:原話(兩行):「…」「…」);
- README「使用者講過的規則」那張表的第一欄(那一欄就是使用者的話)。

比對:引文裡的「…」(U+2026)代表省略,切開的各段要依序出現在佇列的同一行;其他字元(含全形/半形、空白個數、半形 ...)
都要一模一樣。引文跨行(同一行「與」數目不同)也報錯:原話要寫在同一行。

用法:python quote_check.py [--queue 檔案];不給 --queue 時用 `git show origin/main:決策佇列.md`。
原始碼突變在 repo 外的副本裡跑(沒有 git),由環境變數 FRAMING_QUOTE_QUEUE 指定一份事先從 origin/main 取出的同一個檔。"""
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TPL = HERE.parent  # geometry-core/framing-template
FILES = [TPL / "oracle" / "README.md", TPL / "PROPOSAL.md", TPL / "oracle" / "framing_oracle.py", TPL / "oracle" / "selftest.py"]
MARKERS = ("原話", "原文", "逐字", "拍板", "決策佇列")
NOT_CLAIM = ("非使用者原話", "不是使用者原話")
USER_TABLE = "## 使用者講過的規則"


def queue_source():
    return ("FRAMING_QUOTE_QUEUE=" + os.environ["FRAMING_QUOTE_QUEUE"]) if os.environ.get("FRAMING_QUOTE_QUEUE") else "origin/main"


def queue_from_origin_main():
    if os.environ.get("FRAMING_QUOTE_QUEUE"):
        return pathlib.Path(os.environ["FRAMING_QUOTE_QUEUE"]).read_text(encoding="utf-8")
    top = subprocess.run(["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
                         capture_output=True, check=True).stdout.decode("utf-8").strip()
    out = subprocess.run(["git", "-C", top, "show", "origin/main:決策佇列.md"], capture_output=True, check=True).stdout
    return out.decode("utf-8")


def pairs(line):
    """同一行裡配對好的「」(可巢狀),回傳 (開, 關) 的位置,依開的位置排序。"""
    st, out = [], []
    for i, ch in enumerate(line):
        if ch == "「":
            st.append(i)
        elif ch == "」" and st:
            out.append((st.pop(), i))
    return sorted(out)


def claimed(text, user_table=False):
    """回傳 [(行號, 引文)]:標成原話的引文;另回傳跨行的可疑行 [(行號, 該行)]。"""
    out, split = [], []
    in_table = False
    for ln, line in enumerate(text.splitlines(), 1):
        if user_table and line.startswith("## "):
            in_table = line.startswith(USER_TABLE)
        cell_end = line.find("|", 1) if (in_table and line.startswith("|")) else -1
        ends = set()
        for j, i in pairs(line):
            pre, pre16 = line[max(0, j - 10):j], line[max(0, j - 16):j]
            is_claim = ((any(m in pre for m in MARKERS) and not any(n in pre16 for n in NOT_CLAIM))
                        or (j - 1) in ends or (0 < j < cell_end))
            if is_claim:
                out.append((ln, line[j + 1:i]))
                ends.add(i)
        if line.count("「") != line.count("」") and any(m in line for m in MARKERS):
            split.append((ln, line))
    return out, split


def found(q, qlines):
    frags = [f for f in q.split("…") if f]
    if not frags:
        return True
    for ql in qlines:
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


def scan_text(name, text, queue, user_table=False):
    """回傳 (檢查的引文數, 問題清單 [(檔名:行號, 原因, 引文)])。"""
    qlines = queue.splitlines()
    qs, split = claimed(text, user_table)
    bad = [(f"{name}:{ln}", "不在佇列裡(要逐字)", q) for ln, q in qs if not found(q, qlines)]
    bad += [(f"{name}:{ln}", "引文跨行(原話要寫在同一行)", line[:60]) for ln, line in split]
    return len(qs), bad


def scan(queue, files=FILES):
    n, bad = 0, []
    for f in files:
        k, b = scan_text(f.name, f.read_text(encoding="utf-8"), queue, user_table=f.name == "README.md")
        n += k
        bad += b
    return n, bad


# 反例與正例(用真的佇列內容):空白個數不同、少一個字、改寫都要抓到;逐字、用 … 省略的要過。
SAMPLES = [
    ("原話「端面頂的是角材才能固定 ...那你讓」", True),   # 佇列是兩個空白
    ("原話「端面頂的是角材才能固定  ...那你讓」", False),
    ("原話講的「連接角材正交/平行」", True),            # 佇列是「連接角材 才會正交/平行」
    ("原話講的「…連接角材 才會正交/平行」", False),
    ("使用者原話(兩行):「??? 主支為什麼要斷開 ?」「不能斷開啊」", True),  # 第二段錯一個字(阿→啊)
    ("使用者原話(兩行):「??? 主支為什麼要斷開 ?」「不能斷開阿」", False),
    ("| 「間隔差了1~2mm 影響不大」(台北 10-15 05:51) | x |", True),   # 使用者規則表第一欄,多一個空白
    ("協調 agent 的推論(非使用者原話)「支撐能調整就調整」", False),   # 標明不是原話的不檢查
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
    print(f"標成原話的引文 {n} 段,不在 origin/main 決策佇列.md 裡的 {len(bad)} 段;反例/正例判錯 {len(wrong)} 個")
    for x in bad + wrong:
        print("   ", x)
    sys.exit(1 if bad or wrong else 0)
