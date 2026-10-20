"""引文逐字檢查:文件與程式裡引用使用者的話、決策佇列標題、佇列原文的引號,必須逐字(位元組相同)出現在受測這棵樹自己的
`決策佇列.md`(repo 根目錄)裡對的地方。驗受測的那份:不讀任何 remote ref,也不用 git;讀不到就失敗,不略過
(#251 下角材列車 cd4da2fd:WSL 的乾淨 clone 裡 origin/main 指向過時的本機 main,讀 origin/main 會整批誤判)。

引號:「」、『』、“”;.md 與內建樣本另認 ASCII "…"(.py 檔裡 ASCII 引號是程式字串,不認,列為已知限制)。
每一段引號先分種類(看開引號前 10 個字;「這一行」指整行,拿掉所有引號內文之後的文字):
- 標題:前面有「決策佇列」→ 要出現在佇列的標題行(# 開頭)。
- 佇列原文:前面有「逐字」→ 要出現在佇列的任一行。
- 緊接在另一段後面(」「)的,與前一段同種類。
- 使用者的話:下列任一成立 → 要出現在佇列的使用者原話行(去掉行首空白後以 > 開頭的引用行)。協調 agent 整理的要點、題目文字都不算。
  - 前面有 原話、原文、拍板;或開引號前 4 個字內有說、講、回答、表示、寫道這類引述動詞;
  - 這一行提到使用者(使用者、Yang);這一行以引號開頭時,上一行提到使用者或有上述標記也算;
  - 這一行是 > 開頭的引用區塊;或在 README「使用者講過的規則」那張表的第一欄。
- 寫了 不是使用者原話 之類的字樣也不豁免。
另外兩種寫法直接報錯:引號跨行(同一行開、關引號數目不同);「原話」後面接括號或冒號、卻不是引號(轉述冒充原話)。

比對:引文裡的「…」(U+2026)代表省略,切開的各段要依序出現在同一行;切成兩段以上時每段至少 MIN_FRAG 個字;
只有一段的引文至少 MIN_SINGLE(4)個字(不計空白)才算逐字比對,更短的(例 使用者說「不用」)一律報錯,即使它真的出現在某行原話裡。
其他字元(含全形/半形、空白個數、半形 ...)都要一模一樣。
**本檢查是輔助,不是保證**:它只擋得住下面列出的寫法,擋不住有意繞過的人,使用者原話的把關最後仍靠審查。
先正規化再查:HTML 實體(&#12300;、&lcorner; 這類)換成真的字;<q>…</q> 當引號;.py 裡的 \\u、\\U、\\N{名稱}、\\x 跳脫換成真的字。
標記詞(原話、原文,以及使用者或 Yang 加說、講、回答、表示、寫道)後面可以夾 Unicode 空白(全形空白、tab、nbsp)、零寬字元、
括號說明、冒號、破折號、〈是、為、如下〉這類連接詞;夾完之後下一個字若不是引號,而是括號類(〈《‘'`[<*_ 等)就報錯(轉述冒充原話)。
已知限制(查不到的寫法;README 也列了同一份):
- 真的原話配上錯的時間或出處:只要逐字出現在佇列任一行 > 原話行就過,不驗是哪一天哪一題說的。
- 沒有任何標記詞、也沒有引號的轉述;標記詞離引號太遠(超過上面列的夾法,或不在同一行、上一行);其他語言的標記詞(例 User said)。
- 沒列入的括號與引號形狀(例 ‹›、零寬字元夾在引號字元中間)、圖片與截圖裡的字、程式碼區塊裡的字。
- 只有一段的引文至少 4 個字:2、3 個字的詞(例 一律、副支)不能用引號引,會報錯(要引一個詞請用〈〉,那不是使用者的話;
  要引使用者的話請引更長的一段)。反過來,4 個字以上的常見片語(例 只在對牆)只要出現在任一行原話就過,不驗上下文。
- .py 檔的 ASCII 引號是程式字串,不認(只有緊接在原話、原文後面時報錯)。
- 佇列自我引用:比對的是受測這棵樹自己的佇列,同一個 PR 往佇列加一行 > 原話行就能讓引文過關(要比對 merge-base 那一份才能擋,
  但 merge-base 取決於 remote ref,在 WSL 的乾淨 clone 裡不可靠,本版不做;靠審查看佇列的 diff)。

用法:python quote_check.py [--queue 檔案];不給 --queue 時讀 repo 根目錄的 `決策佇列.md`(本檔往上三層)。
原始碼突變在 repo 外的副本裡跑,由環境變數 FRAMING_QUOTE_QUEUE 指定一份事先從受測工作樹複製出來的同一個檔。"""
import html
import os
import pathlib
import re
import sys
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent
TPL = HERE.parent  # geometry-core/framing-template
FILES = [TPL / "oracle" / "README.md", TPL / "PROPOSAL.md", TPL / "oracle" / "framing_oracle.py", TPL / "oracle" / "selftest.py"]
USER_MARKERS = ("原話", "原文", "拍板")
USER_WORDS = ("使用者", "Yang")
SPEECH = ("說", "講", "回答", "表示", "寫道")
TITLE_MARKER = "決策佇列"
QUEUE_MARKER = "逐字"
USER_TABLE = "## 使用者講過的規則"
CJK = {"「": "」", "『": "』", "“": "”", "｢": "｣", "⌜": "⌝", "⌞": "⌟", "〝": "〞", "﹁": "﹂", "﹃": "﹄", "«": "»", "❝": "❞"}
FULLQ = "＂"  # 全形雙引號 U+FF02:前後同一個字,和 ASCII " 一樣兩兩配對(.py 裡也認,它不會是程式字串的引號)
NONSTD = "〈《‘'`[<*_&\""  # 原話、原文後面接這些(而不是上面的引號),判成轉述冒充原話;& 是解不開的 HTML 實體(例 &lcorner;)
DASHES = "—―─-"  # 標記詞後面的破折號:夾完還不是引號就算轉述
CONNECT = ("就是", "如下", "是", "為", "即")  # 標記詞後面的連接詞:原話是〈…〉
MIN_FRAG = 6
MIN_SINGLE = 4  # 只有一段的引文(沒有 … 切開)至少這麼多個字(不計空白)才逐字比對;更短的(例〈不用〉)在好幾行原話裡都找得到,查了等於沒查


QUEUE_PATH = TPL.parent.parent / "決策佇列.md"  # repo 根目錄:oracle → framing-template → geometry-core → 根


def queue_path():
    return pathlib.Path(os.environ["FRAMING_QUOTE_QUEUE"]) if os.environ.get("FRAMING_QUOTE_QUEUE") else QUEUE_PATH


def queue_source():
    return ("FRAMING_QUOTE_QUEUE=" if os.environ.get("FRAMING_QUOTE_QUEUE") else "工作樹 ") + str(queue_path())


def queue_from_tree():
    """讀受測這棵樹的 決策佇列.md;沒有這個檔就丟例外(呼叫端要當成失敗)。"""
    return queue_path().read_text(encoding="utf-8")


def sources(queue):
    """佇列分三組行:使用者原話行(> 引用行)、標題行(# 開頭)、全部。"""
    lines = queue.splitlines()
    return dict(user=[l for l in lines if l.lstrip().startswith(">")],
                title=[l for l in lines if l.lstrip().startswith("#")],
                queue=lines)


def pairs(line, ascii_quotes=True):
    """同一行裡配對好的引號(「」『』“” 可巢狀;ASCII " 兩兩配對),回傳 (開, 關),依開的位置排序;另回傳沒配上的開引號數。"""
    st, out = [], []
    for i, ch in enumerate(line):
        if ch in CJK:
            st.append((i, CJK[ch]))
        elif st and ch == st[-1][1]:
            out.append((st.pop()[0], i))
    if ascii_quotes:
        qs = [i for i, ch in enumerate(line) if ch == '"']
        out += [(qs[k], qs[k + 1]) for k in range(0, len(qs) - 1, 2)]
    fw = [i for i, ch in enumerate(line) if ch == FULLQ]  # 全形雙引號:.py 裡也認
    out += [(fw[k], fw[k + 1]) for k in range(0, len(fw) - 1, 2)]
    return sorted(out), len(st) + len(fw) % 2


def unquoted(line, prs):
    """這一行拿掉所有引號內文之後的文字。"""
    keep = [True] * len(line)
    for j, i in prs:
        for k in range(j + 1, i):
            keep[k] = False
    return "".join(ch for ch, k in zip(line, keep) if k)


MARK_RE = re.compile(r"原話|原文|(?:使用者|Yang)\s*(?:說|講|回答|表示|寫道)")  # 標記詞:原話、原文,以及使用者(或 Yang)加引述動詞


def _gap(ch):
    """標記詞和引號之間可以夾的空白類字元:Unicode 空白(全形空白 U+3000、tab、nbsp)與零寬字元(類別 Cf)。"""
    return ch.isspace() or unicodedata.category(ch) == "Cf"


def _skip(line, j):
    """從 j 起跳過標記詞後面可以夾的東西:空白類字元、括號說明、冒號、破折號、連接詞(是、為、如下…)。
    回傳 (新位置, 夾了括號/冒號/破折號嗎, 夾了連接詞嗎)。"""
    strict = soft = False
    while True:
        j0 = j
        while j < len(line) and _gap(line[j]):
            j += 1
        if j < len(line) and line[j] in "(（":
            close = min([x for x in (line.find(")", j), line.find("）", j)) if x >= 0], default=-1)
            if close >= 0:
                j, strict = close + 1, True
        if j < len(line) and line[j] in ":：":
            j, strict = j + 1, True
        while j < len(line) and line[j] in DASHES:
            j, strict = j + 1, True
        for c in CONNECT:
            if line.startswith(c, j):
                j, soft = j + len(c), True
                break
        if j == j0:
            return j, strict, soft


def bad_paraphrase(line, ascii_ok=True):
    """標記詞(原話、原文;使用者或 Yang 加說、講、回答、表示、寫道)後面夾完空白類字元、連接詞之後,下一個字是〈〉、《》、‘’、ASCII 引號(.py 裡)、
    反引號、[、<、*、_ 這類括號,而不是引號:轉述冒充原話。原話、原文後面夾了括號說明、冒號或破折號、卻不是引號,也算(說了要引、沒有引)。
    前面是「不是」「非」的不算(那是在說不是原話)。"""
    out = []
    for m in MARK_RE.finditer(line):
        pre = line[max(0, m.start() - 6):m.start()]
        j, strict, soft = _skip(line, m.end())
        nxt = line[j] if j < len(line) else ""
        valid = nxt in CJK or nxt == FULLQ or (ascii_ok and nxt == '"')
        is_word = m.group(0) in ("原話", "原文")  # 說、講…那一類只在下一個字是括號類時報(「使用者說:」常見於正常敘述)
        if "不是" not in pre and "非" not in pre and not valid and ((is_word and strict) or nxt in NONSTD):
            out.append(line[m.start():m.start() + 30])
    return out


def _chr(code):
    try:
        return chr(int(code, 16))
    except (ValueError, OverflowError):
        return None


def _py_unescape(line):
    """.py 裡的跳脫換成真的字:\\uXXXX、\\UXXXXXXXX、\\N{名稱}、連續的 \\xHH(當成 UTF-8 位元組解,解不開就當 Latin-1)。"""
    line = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: _chr(m.group(1)) or m.group(0), line)
    line = re.sub(r"\\U([0-9a-fA-F]{8})", lambda m: _chr(m.group(1)) or m.group(0), line)

    def named(m):
        try:
            return unicodedata.lookup(m.group(1))
        except KeyError:
            return m.group(0)

    def xs(m):
        b = bytes(int(h, 16) for h in re.findall(r"\\x([0-9a-fA-F]{2})", m.group(0)))
        try:
            return b.decode("utf-8")
        except UnicodeDecodeError:
            return b.decode("latin-1")

    line = re.sub(r"\\N\{([^}]+)\}", named, line)
    return re.sub(r"(?:\\x[0-9a-fA-F]{2})+", xs, line)


def normalize(line, is_py):
    """先把寫法換成真的字再查:HTML 實體(&#12300;、&lcorner; 這類)、<q>…</q>(當成引號);.py 裡的 \\u300c、\\U0000300c、\\N{LEFT CORNER BRACKET}、\\xe3\\x80\\x8c 這類跳脫。"""
    line = html.unescape(line)
    line = line.replace("<q>", "「").replace("</q>", "」")
    if is_py:
        line = _py_unescape(line)
    return line


def claimed(text, user_table=False, ascii_quotes=True):
    """回傳 [(行號, 種類, 引文)] 與其他問題 [(行號, 原因, 文字)]。"""
    out, other = [], []
    in_table = False
    lines = [normalize(l, not ascii_quotes) for l in text.splitlines()]
    for ln, line in enumerate(lines, 1):
        if user_table and line.startswith("## "):
            in_table = line.startswith(USER_TABLE)
        cell_end = line.find("|", 1) if (in_table and line.startswith("|")) else -1
        prs, open_left = pairs(line, ascii_quotes)
        if open_left or sum(line.count(c) for c in CJK.values()) > sum(line.count(c) for c in CJK):
            other.append((ln, "引號跨行(要寫在同一行)", line[:60]))
        for para in bad_paraphrase(line, ascii_quotes):
            other.append((ln, "原話後面不是引號(轉述冒充原話)", para))
        ctx = unquoted(line, prs)
        prev = lines[ln - 2] if ln >= 2 else ""
        body = line.lstrip(" >-*|0123456789.")
        starts_with_quote = bool(body) and (body[0] in CJK or body[0] in ('"', FULLQ))
        user_ctx = (any(u in ctx for u in USER_WORDS) or line.lstrip().startswith(">")
                    or (starts_with_quote and any(u in prev for u in USER_WORDS + USER_MARKERS)))
        kinds = {}
        for j, i in prs:
            pre = line[max(0, j - 10):j]
            kind = None
            if TITLE_MARKER in pre:
                kind = "title"
            elif QUEUE_MARKER in pre:
                kind = "queue"
            elif (j - 1) in kinds:
                kind = kinds[j - 1]
            elif (any(m in pre for m in USER_MARKERS) or any(v in line[max(0, j - 4):j] for v in SPEECH)
                  or user_ctx or 0 < j < cell_end):
                kind = "user"
            if kind:
                out.append((ln, kind, line[j + 1:i]))
                kinds[i] = kind
    return out, other


def found(q, lines):
    frags = [f for f in q.split("…") if f]
    if not frags:
        return False
    if len(frags) > 1 and any(len(f) < MIN_FRAG for f in frags):
        return False
    if len(frags) == 1 and len("".join(frags[0].split())) < MIN_SINGLE:
        return False  # 只有一段又太短:不當成逐字比對,一律報錯(2 字的詞要引用請用〈〉,那不是使用者的話)
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


WHY = dict(user="不在使用者原話行(> 引用行)裡(要逐字)", title="佇列裡沒有這一節(標題行找不到,要逐字)", queue="不在佇列裡(要逐字)")


def scan_text(name, text, queue, user_table=False):
    """回傳 (檢查的引文數, 問題清單 [(檔名:行號, 原因, 引文)])。.py 檔不認 ASCII 引號。"""
    src = sources(queue)
    qs, other = claimed(text, user_table, ascii_quotes=not name.endswith(".py"))
    bad = [(f"{name}:{ln}", WHY[k], q) for ln, k, q in qs if not found(q, src[k])]
    bad += [(f"{name}:{ln}", why, t) for ln, why, t in other]
    return len(qs), bad


def scan(queue, files=FILES):
    n, bad = 0, []
    for f in files:
        k, b = scan_text(f.name, f.read_text(encoding="utf-8"), queue, user_table=f.name == "README.md")
        n += k
        bad += b
    return n, bad


# 反例與正例(用真的佇列內容)。反例:空白個數不同、錯一個字、改寫、引用協調 agent 整理的要點、用 … 切碎片、
# 沒有標記詞但句子提到使用者、前面寫「不是使用者原話」想豁免、緊接的第二段捏造、標記詞離得遠、標題不存在;
# 另加 1b6b34f9 審查的 7 種寫法:『』、ASCII 引號、彎引號、標記在上一行且引號拆兩行、標記與引文在表格兩欄、主詞換成人名、句號切開;
# 以及 > 引用區塊偽裝、轉述冒充原話。
SAMPLES = [
    ("原話「端面頂的是角材才能固定 ...那你讓」", True),   # 佇列是兩個空白
    ("原話「端面頂的是角材才能固定  ...那你讓」", False),
    ("原話講的「連接角材正交/平行」", True),            # 佇列是「連接角材 才會正交/平行」
    ("原話講的「…連接角材 才會正交/平行」", False),
    ("使用者原話(兩行):「??? 主支為什麼要斷開 ?」「不能斷開啊」", True),  # 第二段錯一個字(阿→啊)
    ("使用者原話(兩行):「??? 主支為什麼要斷開 ?」「不能斷開阿」", False),
    ("| 「間隔差了1~2mm 影響不大」(台北 10-15 05:51) | x |", True),   # 使用者規則表第一欄,多一個空白
    ("| 第一欄 「間隔差了1~2mm 影響不大」 | x |", True),   # 同上,引號不在行首:只靠「使用者規則表第一欄」那條規則
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
    ("使用者原話『完全捏造的一句話』", True),
    ('使用者原話"完全捏造的一句話"', True),
    ("使用者原話“完全捏造的一句話”", True),
    ("使用者原話如下:\n「完全捏造\n的一句話」", True),     # 標記在上一行、引號拆兩行
    ("使用者原話如下:\n「完全捏造的一句話」", True),       # 標記在上一行、引號在下一行開頭
    ("| 使用者 10-15 05:51 講的 | 「完全捏造的一句話」 |", True),  # 標記與引文在表格兩欄
    ("Yang 在 10-15 說「完全捏造的一句話」", True),        # 主詞換成人名
    ("Yang 的意思是「完全捏造的一句話」", True),           # 人名,沒有引述動詞
    ("他在 10-15 回答「完全捏造的一句話」", True),        # 引述動詞,沒有人名
    ("這是使用者講的。「完全捏造的一句話」是他的意思", True),  # 句號切開
    ("> 「完全捏造的一句話」", True),                      # > 引用區塊偽裝成原話
    ("依使用者台北 10-16 01:29 原話(副支位置可以調整,在副支間距上限之下就好)挪到貼著擋料", True),  # 轉述冒充原話
    # 718cc9a3 審查的新假綠寫法
    ("使用者原話&#12300;完全捏造的一句話&#12301;", True),     # HTML 數字實體
    ("使用者原話&lcorner;完全捏造的一句話&rcorner;", True),   # HTML 具名實體
    ("使用者原話〈完全捏造的一句話〉", True),                  # 〈〉冒充原話
    ("使用者原話｢完全捏造的一句話｣", True),                   # 半形角括號
    ("使用者原話 `完全捏造的一句話`", True),                   # 反引號內文
    ('why = "使用者原話\\u300c完全捏造的一句話\\u300d"', True, "py"),  # .py 字串裡的 \u 跳脫
    ("why = \"使用者原話 '完全捏造的一句話'\"", True, "py"),  # .py 字串裡的 ASCII 單引號
    ('# 使用者原話 "完全捏造的一句話"', True, "py"),          # .py 註解裡的 ASCII 雙引號
    ("原話見 `決策佇列.md` 的那一節", False),                  # 指出處、沒有引用:不算
    ('Yang 說 "完全捏造的一句話"', True),                       # ASCII 引號、不緊接原話:只靠 .md 認 ASCII 引號那條規則
    ("Yang 說&#12300;完全捏造的一句話&#12301;", True),          # HTML 實體、不緊接原話:只靠先解 HTML 實體那條規則
    # 4e1f1161 審查(q6)的繞法:標記詞和引號之間夾 Unicode 空白、連接詞、破折號;其他括號形狀;.py 的其他跳脫
    ("使用者原話　〈完全捏造的一句話〉", True),               # 全形空白(U+3000)
    ("使用者原話\t`完全捏造的一句話`", True),                     # tab
    ("使用者原話 〈完全捏造的一句話〉", True),               # nbsp
    ("使用者原話​〈完全捏造的一句話〉", True),               # 零寬空白(類別 Cf)
    ("使用者原話＂完全捏造的一句話＂", True),                     # 全形雙引號(U+FF02)
    ("使用者原話是〈完全捏造的一句話〉", True),                   # 連接詞「是」
    ("使用者原話如下〈完全捏造的一句話〉", True),                 # 連接詞「如下」
    ("使用者說〈完全捏造的一句話〉", True),                       # 使用者加引述動詞,直接接〈
    ("使用者說 `完全捏造的一句話`", True),                        # 同上,反引號
    ("使用者原話<q>完全捏造的一句話</q>", True),                  # <q> 標籤
    ("使用者原話*完全捏造的一句話*", True),                       # markdown 強調
    ("使用者原話_完全捏造的一句話_", True),
    ("使用者原話——完全捏造的一句話", True),                       # 破折號,沒有引號
    ('why = "使用者原話\\U0000300c完全捏造的一句話\\U0000300d"', True, "py"),   # .py 的 \U 跳脫
    ('why = "使用者原話\\N{LEFT CORNER BRACKET}完全捏造的一句話\\N{RIGHT CORNER BRACKET}"', True, "py"),  # .py 的 \N{名稱}
    ('why = "使用者原話\\xe3\\x80\\x8c完全捏造的一句話"', True, "py"),          # .py 的 \x 位元組(UTF-8 的「),引號沒關
    ('Yang 在 10-15 說 "完全捏造的一句話"', True),                # ASCII 引號,標記詞不緊接:只靠 .md 認 ASCII 引號(新的標記詞規則看不到)
    ("使用者在 10-15 說\n「完全捏造的一句話」", True),             # 標記在上一行、引號在下一行開頭:只靠上一行規則(行尾沒有原話加冒號,新的連接詞規則看不到)
    ("Yang 在 10-15 說&#12300;完全捏造的一句話&#12301;", True),   # HTML 實體,標記詞不緊接:只靠先解 HTML 實體
    ("Yang 在 10-15 說<q>完全捏造的一句話</q>", True),            # q 標籤,標記詞不緊接:只靠 q 標籤正規化
    ("使用者原話　「間隔差了1~2mm影響不大」", False),         # 正例:夾全形空白但接的是真的引號,內文在佇列裡
    ("使用者原話是「間隔差了1~2mm影響不大」", False),             # 正例:連接詞加真的引號
    ("使用者說明了做法,沒有引用任何話", False),                  # 正例:說明、不是引述動詞加括號
    # 92e64028 審查(第 21 輪):只有一段的引文太短,在好幾行原話裡都找得到,逐字比對形同虛設
    ("使用者說「不用」", True),                                    # 2 個字:佇列的原話行裡有 2 行含有〈不用〉,以前會過
    ("使用者說「不置中」", True),                                  # 3 個字:邊界(MIN_SINGLE 少 1 就會放行)
    ("使用者說「只在對牆」", False),                               # 正例:剛好 4 個字,逐字出現在佇列的原話行(邊界:MIN_SINGLE 多 1 就會擋掉)
    ("使用者說「記號 下」", True),                                 # 含空白共 4 個字、不計空白只有 3 個:逐字出現在佇列的原話行,但不計空白不到 4 個字,要擋
]


def drop_section(queue, title_part):
    """把佇列裡標題含 title_part 的那一節(到下一個同級或更高的標題為止)整節拿掉。"""
    lines = queue.splitlines(keepends=True)
    out, skip, level = [], False, 0
    for l in lines:
        st = l.lstrip()
        if st.startswith("#"):
            lv = len(st) - len(st.lstrip("#"))
            if skip and lv <= level:
                skip = False
            if not skip and title_part in st:
                skip, level = True, lv
                continue
        if not skip:
            out.append(l)
    return "".join(out)


MISSING_SECTION = "2026-10-16 縫上副支撞到邊界角材"


def missing_section_check(queue, files=FILES):
    """反例:給一份缺了「2026-10-16 縫上副支撞到邊界角材」那一節的佇列,檢查必須紅,而且訊息要指出缺的是這一節
    (引用這個標題的地方報「佇列裡沒有這一節」)。回傳判錯的說明;空的代表抓到了。"""
    cut = drop_section(queue, MISSING_SECTION)
    if cut == queue:
        return ["佇列裡本來就沒有這一節,反例做不出來"]
    _, bad = scan(cut, files)
    named = [b for b in bad if "沒有這一節" in b[1] and MISSING_SECTION in b[2]]
    return [] if named else [f"拿掉「{MISSING_SECTION}」那一節後,沒有一筆問題指出缺了這一節(共 {len(bad)} 筆問題)"]


def self_check(queue):
    """回傳判錯的樣本;空的代表反例都抓到、正例都過。"""
    wrong = []
    for s, want_bad, *kind in SAMPLES:
        text = USER_TABLE + "\n" + s if s.startswith("|") else s
        _, bad = scan_text("sample.py" if kind == ["py"] else "sample", text, queue, user_table=True)
        if bool(bad) != want_bad:
            wrong.append((s, "應報錯" if want_bad else "不應報錯", bad))
    return wrong


if __name__ == "__main__":
    if "--queue" in sys.argv:
        queue = pathlib.Path(sys.argv[sys.argv.index("--queue") + 1]).read_text(encoding="utf-8")
    else:
        queue = queue_from_tree()
    n, bad = scan(queue)
    wrong = self_check(queue) + missing_section_check(queue)
    print(f"檢查的引文 {n} 段,不在 {queue_source()} 對應位置的 {len(bad)} 段;反例/正例判錯 {len(wrong)} 個")
    for x in bad + wrong:
        print("   ", x)
    sys.exit(1 if bad or wrong else 0)
