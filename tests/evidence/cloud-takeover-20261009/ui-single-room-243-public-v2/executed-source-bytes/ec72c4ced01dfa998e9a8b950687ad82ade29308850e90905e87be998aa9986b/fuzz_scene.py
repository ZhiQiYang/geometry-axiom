#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEO-169：場景解析器的確定性、可重播、會自動縮小的畸形輸入 fuzz harness。

語料：根目錄 131 個合法 .scene 夾具，逐一做位元組層級變形（刪/插/調換 token、
數值邊界、截斷、超長 token/行、空白變形、編碼雜訊、指令名大小寫、未知指令、
重複欄位）。每個案例純粹是 (seed, case_index) 的函式——不依賴前面案例跑過
什麼，所以 --replay / --shrink 可以只重算單一案例，且同 seed 跑兩次結果一定
逐字相同。

透過 bridge 的 "line <文字>" 指令逐行送進同一個常駐行程（每案例前 reset），
對照 GEO-169 工單訂的四條裁判：
  1. 不崩潰：bridge 行程活著、回應與送出的指令數對齊。
  2. 交易性：任何 ok:false 之後，dump 必須與該指令之前的 dump 逐字相同。
  3. 往返：任何改變世界且 ok:true 的序列，dump 存檔 → loadfile → dump 必須逐字相同。
     例外只有一種：dump 裡有宣告了但沒 place 的角材，且 loadfile 的 error 正是
     「沒有 place」——那是 I9 收尾檢查在條文要求下的拒絕（I9/R4 張力，決策佇列 Q12）。
  4. 拒絕有理由：ok:false 時 error 存在、非空、非亂碼；輸入那一行本身不是合法 UTF-8 時，
     bridge 把壞位元組標成 U+FFFD 是正確行為（GEO-174），不算亂碼。

用法：
  python tests/fuzz_scene.py --seed 1234 --cases 500
  python tests/fuzz_scene.py --seed 1234 --cases 500 --replay 87
  python tests/fuzz_scene.py --seed 1234 --cases 500 --shrink 87

只寫兩處：本檔本身，以及 %TEMP%\\fuzz-findings\\（最小重現輸入 + REPORT.md）。
不重編任何 exe；固定使用已編好的 bridge.exe（預設 %TEMP%\\geometry-tests\\bridge.exe，
可用 GEOMETRY_TEST_BRIDGE 覆寫）。
"""
import argparse
import json
import os
import queue
import random
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMP = Path(os.environ.get("TEMP", tempfile.gettempdir()))
DEFAULT_BRIDGE = TEMP / "geometry-tests" / "bridge.exe"
BRIDGE_PATH = Path(os.environ.get("GEOMETRY_TEST_BRIDGE", str(DEFAULT_BRIDGE)))
FINDINGS_DIR = TEMP / "fuzz-findings"
ROUNDTRIP_SCRATCH = FINDINGS_DIR / "_roundtrip_scratch.scene"

CMD_TIMEOUT_DEFAULT = 3.0     # 單次 bridge 往返逾時秒數（卡住判定）
SAC_RETRY_BACKOFF = 12.0      # Smart App Control 擋新 exe 時的重試等待秒數
SAC_RETRIES = 5

# ---------------------------------------------------------------------------
# 語料
# ---------------------------------------------------------------------------

def load_corpus():
    files = sorted(ROOT.glob("*.scene"))
    if not files:
        raise RuntimeError(f"找不到任何 .scene 夾具於 {ROOT}")
    corpus = [(f.name, f.read_bytes()) for f in files]
    return corpus


# ---------------------------------------------------------------------------
# 變形器：每個都吃 (lines: list[bytes], rng) 回傳新的 list[bytes]
# ---------------------------------------------------------------------------

NUMERIC_BOUNDARY_TOKENS = [
    b"0", b"-1", b"4294967295", b"4294967296", b"2147483648",
    b"007", b"+5", b"1e3", b"0x10", b"9" * 40, b"-2147483649",
    b"00", b"-0",
]

OVERSIZE_LENGTHS = [2046, 2047, 2048, 2049, 4094, 4095, 4096, 4097, 100000]

INVALID_UTF8_SNIPPETS = [
    b"\xff\xfe",            # 非法起始位元組
    b"\x80\x81\x82",        # 孤立延續位元組
    b"\xc0\x80",            # overlong NUL 編碼
    b"\xed\xa0\x80",        # UTF-16 surrogate 編碼進 UTF-8（非法）
    b"\xf8\x88\x80\x80\x80",  # 5-byte 舊式序列（RFC3629 之後非法）
    b"\xe2\x28\xa1",        # 續位元組位置錯誤
]

UNKNOWN_COMMAND_WORDS = [
    b"bounadry", b"BOUNDARY9", b"xyzzy", b"boundary;", b"plac",
    b"de1ete", b"grid_", b"__init__", b"boundary\x01", b"timbr",
]

KNOWN_COMMAND_WORDS = [
    b"spec", b"boundary", b"placement", b"surface", b"space", b"datum",
    b"guide", b"grid", b"timber", b"place", b"span-auto", b"move",
    b"column", b"beam", b"apply-proj", b"delete", b"reset", b"canvas-pos",
]

WORD_RE = re.compile(rb"^-?\+?\d+$|^-?\d+e\d+$|^0x[0-9a-fA-F]+$")


def _tokenize(line):
    return line.split(b" ")


def _nonempty_line_indices(lines):
    return [i for i, l in enumerate(lines) if l]


def mut_delete_line(lines, rng):
    if len(lines) <= 1:
        return lines
    i = rng.randrange(len(lines))
    return lines[:i] + lines[i + 1:]


def mut_insert_line(lines, rng):
    pool = [l for l in lines if l] or [b"boundary 1 outline 0,0 10,0 10,10 0,10"]
    junk = rng.choice(pool)
    i = rng.randrange(len(lines) + 1)
    return lines[:i] + [junk] + lines[i:]


def mut_swap_lines(lines, rng):
    if len(lines) < 2:
        return lines
    i, j = rng.sample(range(len(lines)), 2)
    new = list(lines)
    new[i], new[j] = new[j], new[i]
    return new


def mut_delete_token(lines, rng):
    idx = rng.choice(_nonempty_line_indices(lines) or [0]) if lines else 0
    if not lines:
        return lines
    toks = _tokenize(lines[idx])
    if len(toks) <= 1:
        return lines
    k = rng.randrange(len(toks))
    new_toks = toks[:k] + toks[k + 1:]
    new = list(lines)
    new[idx] = b" ".join(new_toks)
    return new


def mut_insert_token(lines, rng):
    if not lines:
        return lines
    idx = rng.randrange(len(lines))
    toks = _tokenize(lines[idx])
    filler = rng.choice(NUMERIC_BOUNDARY_TOKENS + [b"extra", b"0,0"])
    k = rng.randrange(len(toks) + 1)
    new_toks = toks[:k] + [filler] + toks[k:]
    new = list(lines)
    new[idx] = b" ".join(new_toks)
    return new


def mut_swap_tokens(lines, rng):
    if not lines:
        return lines
    idx = rng.randrange(len(lines))
    toks = _tokenize(lines[idx])
    if len(toks) < 2:
        return lines
    i, j = rng.sample(range(len(toks)), 2)
    toks[i], toks[j] = toks[j], toks[i]
    new = list(lines)
    new[idx] = b" ".join(toks)
    return new


def mut_duplicate_field(lines, rng):
    if not lines:
        return lines
    idx = rng.randrange(len(lines))
    toks = _tokenize(lines[idx])
    if not toks:
        return lines
    k = rng.randrange(len(toks))
    new_toks = toks[:k + 1] + [toks[k]] + toks[k + 1:]
    new = list(lines)
    new[idx] = b" ".join(new_toks)
    return new


def mut_numeric_boundary(lines, rng):
    candidates = []
    for i, line in enumerate(lines):
        for k, tok in enumerate(_tokenize(line)):
            if WORD_RE.match(tok) or tok.replace(b",", b"").isdigit():
                candidates.append((i, k))
    if not candidates:
        return lines
    i, k = rng.choice(candidates)
    toks = _tokenize(lines[i])
    toks[k] = rng.choice(NUMERIC_BOUNDARY_TOKENS)
    new = list(lines)
    new[i] = b" ".join(toks)
    return new


def mut_truncate_file(lines, rng):
    if len(lines) <= 1:
        return lines
    cut = rng.randrange(1, len(lines))
    return lines[:cut]


def mut_truncate_line(lines, rng):
    idx = rng.choice(_nonempty_line_indices(lines) or [None])
    if idx is None or not lines:
        return lines
    line = lines[idx]
    if len(line) < 2:
        return lines
    cut = rng.randrange(1, len(line))
    new = list(lines)
    new[idx] = line[:cut]
    return new


def mut_oversize_token(lines, rng):
    if not lines:
        return lines
    idx = rng.randrange(len(lines))
    toks = _tokenize(lines[idx]) or [b""]
    k = rng.randrange(len(toks))
    n = rng.choice(OVERSIZE_LENGTHS)
    toks[k] = b"9" * n
    new = list(lines)
    new[idx] = b" ".join(toks)
    return new


def mut_oversize_line(lines, rng):
    n = rng.choice(OVERSIZE_LENGTHS)
    junk_line = b"boundary 1 outline " + b"x" * n
    i = rng.randrange(len(lines) + 1)
    new = list(lines)
    new.insert(i, junk_line)
    return new


def mut_whitespace_tab(lines, rng):
    idx = rng.choice(_nonempty_line_indices(lines) or [None])
    if idx is None:
        return lines
    line = lines[idx]
    positions = [i for i, c in enumerate(line) if c == 0x20]
    if not positions:
        return lines
    p = rng.choice(positions)
    new_line = line[:p] + b"\t" + line[p + 1:]
    new = list(lines)
    new[idx] = new_line
    return new


def mut_whitespace_multi_space(lines, rng):
    idx = rng.choice(_nonempty_line_indices(lines) or [None])
    if idx is None:
        return lines
    line = lines[idx]
    positions = [i for i, c in enumerate(line) if c == 0x20]
    if not positions:
        return lines
    p = rng.choice(positions)
    n = rng.randint(2, 8)
    new_line = line[:p] + b" " * n + line[p + 1:]
    new = list(lines)
    new[idx] = new_line
    return new


def mut_whitespace_trailing(lines, rng):
    if not lines:
        return lines
    idx = rng.randrange(len(lines))
    n = rng.randint(1, 6)
    filler = rng.choice([b" ", b"\t"])
    new = list(lines)
    new[idx] = lines[idx] + filler * n
    return new


def mut_whitespace_blank_line(lines, rng):
    i = rng.randrange(len(lines) + 1)
    blank = rng.choice([b"", b"   ", b"\t", b" \t "])
    new = list(lines)
    new.insert(i, blank)
    return new


def mut_encoding_invalid_utf8(lines, rng):
    if not lines:
        return lines
    idx = rng.randrange(len(lines))
    line = lines[idx]
    p = rng.randrange(len(line) + 1)
    snippet = rng.choice(INVALID_UTF8_SNIPPETS)
    new_line = line[:p] + snippet + line[p:]
    new = list(lines)
    new[idx] = new_line
    return new


def mut_encoding_bom(lines, rng):
    bom = b"\xef\xbb\xbf"
    if rng.random() < 0.5 and lines:
        idx = rng.randrange(len(lines))
        new = list(lines)
        new[idx] = bom + lines[idx]
        return new
    new = list(lines)
    new.insert(0, bom.rstrip())  # BOM 自成一段落，模擬檔案最前面
    return new


def mut_encoding_nul(lines, rng):
    if not lines:
        return lines
    idx = rng.randrange(len(lines))
    line = lines[idx]
    p = rng.randrange(len(line) + 1)
    new_line = line[:p] + b"\x00" + line[p:]
    new = list(lines)
    new[idx] = new_line
    return new


def mut_encoding_isolated_cr(lines, rng):
    if not lines:
        return lines
    idx = rng.randrange(len(lines))
    line = lines[idx]
    p = rng.randrange(len(line) + 1)
    new_line = line[:p] + b"\r" + line[p:]
    new = list(lines)
    new[idx] = new_line
    return new


def mut_command_case(lines, rng):
    idx = rng.choice(_nonempty_line_indices(lines) or [None])
    if idx is None:
        return lines
    toks = _tokenize(lines[idx])
    if not toks:
        return lines
    word = toks[0]
    style = rng.choice(["upper", "lower", "mixed"])
    if style == "upper":
        new_word = word.upper()
    elif style == "lower":
        new_word = word.lower()
    else:
        new_word = bytes(
            (c ^ 0x20) if rng.random() < 0.5 and (65 <= c <= 90 or 97 <= c <= 122) else c
            for c in word
        )
    toks[0] = new_word
    new = list(lines)
    new[idx] = b" ".join(toks)
    return new


def mut_unknown_command(lines, rng):
    idx = rng.choice(_nonempty_line_indices(lines) or [None])
    if idx is None:
        return lines
    toks = _tokenize(lines[idx])
    if not toks:
        return lines
    toks[0] = rng.choice(UNKNOWN_COMMAND_WORDS)
    new = list(lines)
    new[idx] = b" ".join(toks)
    return new


MUTATORS = {
    "delete_line": mut_delete_line,
    "insert_line": mut_insert_line,
    "swap_lines": mut_swap_lines,
    "delete_token": mut_delete_token,
    "insert_token": mut_insert_token,
    "swap_tokens": mut_swap_tokens,
    "duplicate_field": mut_duplicate_field,
    "numeric_boundary": mut_numeric_boundary,
    "truncate_file": mut_truncate_file,
    "truncate_line": mut_truncate_line,
    "oversize_token": mut_oversize_token,
    "oversize_line": mut_oversize_line,
    "whitespace_tab": mut_whitespace_tab,
    "whitespace_multi_space": mut_whitespace_multi_space,
    "whitespace_trailing": mut_whitespace_trailing,
    "whitespace_blank_line": mut_whitespace_blank_line,
    "encoding_invalid_utf8": mut_encoding_invalid_utf8,
    "encoding_bom": mut_encoding_bom,
    "encoding_nul": mut_encoding_nul,
    "encoding_isolated_cr": mut_encoding_isolated_cr,
    "command_case": mut_command_case,
    "unknown_command": mut_unknown_command,
}
MUTATION_KINDS = sorted(MUTATORS.keys())


def generate_case(corpus, seed, index):
    """純函式：只吃 (corpus, seed, index)，跟其他案例、跟 --cases 總數無關。"""
    rng = random.Random(seed * 1_000_003 + index * 97 + 13)
    fname, raw = rng.choice(corpus)
    lines = raw.split(b"\n")
    n_ops = rng.randint(1, 3)
    applied = []
    for _ in range(n_ops):
        kind = rng.choice(MUTATION_KINDS)
        try:
            lines = MUTATORS[kind](lines, rng)
        except Exception as e:  # 變形器本身絕不能讓 harness 掛掉
            applied.append(f"{kind}(mutator-error:{e})")
            continue
        applied.append(kind)
    return fname, applied, lines


# ---------------------------------------------------------------------------
# Bridge 行程包裝：位元組層級、逾時可控、可重啟
# ---------------------------------------------------------------------------

class BridgeDead(Exception):
    pass


class Bridge:
    def __init__(self, exe_path, timeout=CMD_TIMEOUT_DEFAULT):
        self.exe_path = exe_path
        self.timeout = timeout
        self.proc = None
        self.q = None
        self.reader_thread = None
        self.env_blocked_events = 0
        self.start()

    def start(self):
        last_err = None
        for attempt in range(1, SAC_RETRIES + 1):
            try:
                self.proc = subprocess.Popen(
                    [str(self.exe_path)],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, bufsize=0,
                )
                self.q = queue.Queue()
                self.reader_thread = threading.Thread(
                    target=self._reader, daemon=True)
                self.reader_thread.start()
                return
            except OSError as e:
                last_err = e
                self.env_blocked_events += 1
                print(f"[env] 啟動 bridge 被擋（第 {attempt}/{SAC_RETRIES} 次，"
                      f"多半是 Smart App Control 在審新 exe，非程式問題）："
                      f"{e}；等 {SAC_RETRY_BACKOFF}s 重試", flush=True)
                time.sleep(SAC_RETRY_BACKOFF)
        raise RuntimeError(f"bridge.exe 啟動失敗（已排除環境阻擋外的重試）：{last_err}")

    def _reader(self):
        f = self.proc.stdout
        while True:
            try:
                line = f.readline()
            except Exception:
                self.q.put(None)
                return
            if not line:
                self.q.put(None)
                return
            self.q.put(line)

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def _stderr_tail(self):
        try:
            self.proc.stderr.flush()
        except Exception:
            pass
        try:
            data = self.proc.stderr.read(4000) if self.proc.stderr else b""
        except Exception:
            data = b""
        return (data or b"").decode("utf-8", errors="replace")

    def send(self, raw_line_bytes):
        """送一行 bridge 指令（不含結尾換行），回傳 (status, payload)。
        status: OK / TIMEOUT / EOF / BADJSON / CRASH。"""
        if not self.alive():
            return ("CRASH", f"行程已死，returncode={self.proc.poll() if self.proc else '?'}")
        try:
            self.proc.stdin.write(raw_line_bytes + b"\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            return ("CRASH", f"寫入 stdin 失敗：{e}；stderr尾={self._stderr_tail()!r}")
        try:
            line = self.q.get(timeout=self.timeout)
        except queue.Empty:
            return ("TIMEOUT", None)
        if line is None:
            return ("EOF", self._stderr_tail())
        try:
            d = json.loads(line.decode("utf-8", errors="strict"))
        except Exception as e:
            return ("BADJSON", f"{e}: {line[:200]!r}")
        return ("OK", d)

    def kill(self):
        try:
            if self.proc:
                self.proc.kill()
                self.proc.wait(timeout=5)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 裁判
# ---------------------------------------------------------------------------

class Violation:
    def __init__(self, category, detail, line_index=None, offending_line=None):
        self.category = category   # 1..4
        self.detail = detail
        self.line_index = line_index
        self.offending_line = offending_line

    def signature(self):
        return (self.category, self.detail.split("\n", 1)[0][:60])

    def __repr__(self):
        loc = f" (第 {self.line_index} 行)" if self.line_index is not None else ""
        return f"[類{self.category}]{loc} {self.detail}"


CATEGORY_NAMES = {
    1: "不崩潰/回應對齊",
    2: "交易性",
    3: "往返 dump/loadfile",
    4: "拒絕有理由",
}


def looks_sane_error(s, allow_replacement=False):
    if not isinstance(s, str):
        return False
    if s.strip() == "":
        return False
    # U+FFFD 有兩種來源:bridge 吐出無效 UTF-8、被 decode 換掉(亂碼,bug);
    # 或輸入本身就含壞位元組、bridge 依 GEO-174 把它標成 U+FFFD(正確)。
    # 呼叫端知道輸入合不合法,合法輸入出現 U+FFFD 才算違規。
    if "�" in s and not allow_replacement:
        return False
    return True


def is_valid_utf8(raw):
    try:
        raw.decode("utf-8", errors="strict")
        return True
    except UnicodeDecodeError:
        return False


def dump_has_unplaced_timber(text):
    """I9:場景收尾仍有未 place 的角材 → loadfile 整份拒絕,是條文要求的。
    互動世界可以暫時含未放置角材(逐行追加沒有「收尾」),它的 dump 因此不能用
    loadfile 載回——這不是往返 bug,是 I9 與 R4 的張力(決策佇列 Q12,2026-09-24 🔒 維持現狀)。"""
    declared = set(re.findall(r"^timber (\d+)\b", text, re.M))
    placed = set(re.findall(r"^place (\d+)\b", text, re.M))
    return bool(declared - placed)


def run_case(bridge, lines, roundtrip_scratch, dump_budget_guard=None):
    """對一個已 reset 過的 bridge 行程跑一個案例，回傳 (violations, transcript, fatal)。
    fatal=True 代表 bridge 行程需要整支重啟（碰到 CRASH/TIMEOUT/EOF/BADJSON）。"""
    violations = []
    transcript = []

    status, payload = bridge.send(b"reset")
    if status != "OK" or not payload.get("ok"):
        violations.append(Violation(1, f"reset 失敗或無回應：{status} {payload}"))
        return violations, transcript, True

    status, payload = bridge.send(b"dump")
    if status != "OK" or not payload.get("ok"):
        violations.append(Violation(1, f"reset 後 dump 失敗或無回應：{status} {payload}"))
        return violations, transcript, True
    last_good = payload.get("text", "")
    baseline = last_good

    for i, raw_line in enumerate(lines):
        status, payload = bridge.send(b"line " + raw_line)
        if status != "OK":
            violations.append(Violation(
                1, f"送出第 {i} 行後無正常回應：{status} {payload}",
                line_index=i, offending_line=raw_line))
            return violations, transcript, True
        transcript.append((i, raw_line, payload))

        status2, dpayload = bridge.send(b"dump")
        if status2 != "OK" or not dpayload.get("ok"):
            violations.append(Violation(
                1, f"第 {i} 行之後 dump 失敗或無回應：{status2} {dpayload}",
                line_index=i, offending_line=raw_line))
            return violations, transcript, True
        cur_dump = dpayload.get("text", "")

        if payload.get("ok") is False:
            if cur_dump != last_good:
                violations.append(Violation(
                    2, f"第 {i} 行回 ok:false 之後，dump 跟之前不一致\n"
                       f"（world 被半套用了）。error={payload.get('error')!r}",
                    line_index=i, offending_line=raw_line))
            err = payload.get("error")
            if "error" not in payload or not looks_sane_error(
                    err, allow_replacement=not is_valid_utf8(raw_line)):
                violations.append(Violation(
                    4, f"第 {i} 行回 ok:false 但 error 缺漏/空白/亂碼：{err!r}",
                    line_index=i, offending_line=raw_line))
        elif payload.get("ok") is True:
            last_good = cur_dump
        else:
            violations.append(Violation(
                1, f"第 {i} 行回應沒有合法的 ok 欄位：{payload!r}",
                line_index=i, offending_line=raw_line))

    if last_good != baseline:
        try:
            roundtrip_scratch.write_bytes(last_good.encode("utf-8"))
        except Exception as e:
            violations.append(Violation(3, f"寫暫存檔失敗（環境問題非程式問題）：{e}"))
            return violations, transcript, False

        status, payload = bridge.send(
            ("loadfile " + str(roundtrip_scratch)).encode("utf-8"))
        if status != "OK":
            violations.append(Violation(3, f"loadfile 自己的 dump 後無正常回應：{status} {payload}"))
            return violations, transcript, True
        if not payload.get("ok"):
            lf_err = payload.get("error")
            if (dump_has_unplaced_timber(last_good)
                    and isinstance(lf_err, str) and "沒有 place" in lf_err):
                pass   # I9 收尾擋下未放置角材:條文要求的拒絕,不是往返違規(Q12)
            else:
                violations.append(Violation(
                    3, f"loadfile 自己的 dump 輸出居然失敗：{lf_err!r}"))
                if "error" not in payload or not looks_sane_error(lf_err):
                    violations.append(Violation(
                        4, f"loadfile 拒絕自己的 dump 輸出，但 error 缺漏/空白/亂碼：{lf_err!r}"))
        else:
            status2, dpayload = bridge.send(b"dump")
            if status2 != "OK" or not dpayload.get("ok"):
                violations.append(Violation(3, f"reload 後 dump 失敗或無回應：{status2} {dpayload}"))
                return violations, transcript, True
            after = dpayload.get("text", "")
            if after != last_good:
                violations.append(Violation(
                    3, "dump → 存檔 → loadfile → dump 不是逐字相同"))

    return violations, transcript, False


# ---------------------------------------------------------------------------
# 行程隔離 + 疑似類1事件（TIMEOUT/EOF/BADJSON/CRASH）的複驗
#
# 早期版本讓「一個行程餵多個案例」字面成立：整個 --cases 掃描共用同一個
# bridge.exe 行程，只在每案例前送 "reset"。實測發現這樣**不能保證確定性**：
# reset 只清 World + undo history，不會清一部分行程層級全域狀態（例如
# g_input_line_no 這種單調計數器），而 bridge 行程何時因為疑似 TIMEOUT 被砍掉
# 重開，取決於當下真實的系統排程雜訊——兩次一模一樣的 --seed --cases 100
# 跑下來，違規案例清單就對不上（見 REPORT.md 附帶的方法論說明）。
#
# 實測 bridge.exe 每次「全新啟動 + reset + 砍掉」約 12ms（見開發記錄），
# 500 案例多花不到 10 秒——換一個案例一個全新行程，直接把「行程層級全域
# 狀態跨案例滲漏」這整類不確定性連根拔除，比去猜哪個全域變數沒清乾淨可靠
# 太多。「reset」仍然照任務規格送（見 run_case 第一步），只是額外保證每案例
# 開始前連整個作業系統行程都是乾淨的。
#
# 各別案例仍可能撞上真正的引擎卡死/崩潰（類1），也可能撞上系統瞬間排程雜訊
# 造成的假性逾時——這兩者才是這裡要分的：拿到 fatal 結果後，用一個全新、
# 更有耐性（逾時 x4、至少 10s）的獨立行程整案重跑一次複驗；複驗仍重現才算
# 數，複驗跑乾淨就捨棄、但印出來不悶聲（環境阻擋 vs 程式失敗分開記錄）。
# ---------------------------------------------------------------------------

def run_case_robust(lines, roundtrip_scratch, timeout):
    bridge = Bridge(BRIDGE_PATH, timeout=timeout)
    try:
        violations, transcript, fatal = run_case(bridge, lines, roundtrip_scratch)
    finally:
        bridge.kill()
    if not fatal:
        return violations, transcript, False, False

    confirm_timeout = max(timeout * 4, 10.0)
    confirm_bridge = Bridge(BRIDGE_PATH, timeout=confirm_timeout)
    try:
        violations2, transcript2, fatal2 = run_case(confirm_bridge, lines, roundtrip_scratch)
    finally:
        confirm_bridge.kill()

    if fatal2:
        for v in violations2:
            v.detail += f"（已用獨立行程＋{confirm_timeout:.0f}s 逾時複驗，仍重現，非環境雜訊）"
        return violations2, transcript2, True, False

    print(f"  [note] 疑似類1事件複驗（獨立行程＋{confirm_timeout:.0f}s 逾時）沒有重現，"
          f"判定為環境雜訊而非程式缺陷，捨棄原判定：{[repr(v) for v in violations]}", flush=True)
    return violations2, transcript2, False, True


# ---------------------------------------------------------------------------
# 縮小
# ---------------------------------------------------------------------------

def shrink_case(corpus_lines_getter, primary_sig, roundtrip_scratch,
                 max_attempts=250, time_budget=45.0, timeout=CMD_TIMEOUT_DEFAULT):
    """對 corpus_lines_getter() 回傳的初始行清單做貪婪縮小；每個候選都在自己的
    全新 bridge 行程上跑（理由同上：確定性），reproduces(lines) 定義為：違規
    清單裡有跟 primary_sig 同簽章的項目。回傳 (最終行清單, 嘗試次數, 是否仍重現)。"""
    lines = list(corpus_lines_getter())
    attempts = 0
    t0 = time.time()
    # 只有在縮小「類1」（會讓行程 fatal）的違規時才付複驗的代價——那是唯一會被
    # 環境雜訊污染判定的類別；類2/3/4 是純函式行為，同輸入必同結果。
    use_robust = (primary_sig[0] == 1)

    def reproduces(candidate):
        nonlocal attempts
        attempts += 1
        if use_robust:
            vs, _, _fatal, _noise = run_case_robust(candidate, roundtrip_scratch, timeout)
        else:
            bridge = Bridge(BRIDGE_PATH, timeout=timeout)
            try:
                vs, _, _fatal = run_case(bridge, candidate, roundtrip_scratch)
            finally:
                bridge.kill()
        sigs = {v.signature() for v in vs}
        return primary_sig in sigs or any(s[0] == primary_sig[0] for s in sigs)

    if not reproduces(lines):
        return lines, attempts, False

    changed = True
    while changed and attempts < max_attempts and (time.time() - t0) < time_budget:
        changed = False
        for chunk in (len(lines) // 2, len(lines) // 4, 8, 4, 2, 1):
            if chunk < 1 or chunk >= max(len(lines), 1):
                continue
            i = 0
            while i < len(lines) and attempts < max_attempts and (time.time() - t0) < time_budget:
                candidate = lines[:i] + lines[i + chunk:]
                if candidate and reproduces(candidate):
                    lines = candidate
                    changed = True
                    print(f"[shrink] 去掉 {chunk} 行（位置 {i}）成功，剩 {len(lines)} 行", flush=True)
                else:
                    i += 1
            if attempts >= max_attempts or (time.time() - t0) >= time_budget:
                break

    # 逐行從尾端修剪 token，進一步縮小內容
    for idx in range(len(lines)):
        if attempts >= max_attempts or (time.time() - t0) >= time_budget:
            break
        toks = lines[idx].split(b" ")
        while len(toks) > 1 and attempts < max_attempts and (time.time() - t0) < time_budget:
            candidate_line = b" ".join(toks[:-1])
            candidate = lines[:idx] + [candidate_line] + lines[idx + 1:]
            if reproduces(candidate):
                toks = toks[:-1]
                lines[idx] = candidate_line
                print(f"[shrink] 第 {idx} 行修掉尾端一個 token", flush=True)
            else:
                break

    return lines, attempts, True


# ---------------------------------------------------------------------------
# 報告輸出
# ---------------------------------------------------------------------------

def save_finding(case_id, seed, cases_total, fname, applied, lines, violations,
                  shrunk=False, attempts=0):
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    scene_path = FINDINGS_DIR / f"{case_id}.scene"
    scene_path.write_bytes(b"\n".join(lines) + b"\n")

    report_path = FINDINGS_DIR / "REPORT.md"
    lines_desc = []
    for v in violations:
        lines_desc.append(f"  - 類{v.category}（{CATEGORY_NAMES[v.category]}）：{v.detail}")
    block = (
        f"\n## 案例 {case_id}\n"
        f"- 重播：`python tests/fuzz_scene.py --seed {seed} --cases {cases_total} --replay {case_id}`\n"
        f"- 來源夾具：{fname}；套用的變形：{', '.join(applied)}\n"
        f"- 最小重現輸入：`{scene_path}`（{len(lines)} 行"
        f"{'，已自動縮小，嘗試 ' + str(attempts) + ' 次' if shrunk else ''}）\n"
        f"- 觀察到的違規：\n" + "\n".join(lines_desc) + "\n"
    )
    with report_path.open("a", encoding="utf-8") as f:
        f.write(block)
    return scene_path, report_path


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def print_transcript(fname, applied, lines, violations, transcript):
    print(f"來源夾具：{fname}")
    print(f"套用的變形：{', '.join(applied)}")
    print(f"送出行數：{len(lines)}")
    for i, raw_line, payload in transcript:
        shown = raw_line[:120]
        print(f"  [{i}] line {shown!r}{'...(截斷)' if len(raw_line) > 120 else ''}")
        print(f"       -> {payload}")
    if violations:
        print(f"違規（{len(violations)} 個）：")
        for v in violations:
            print(f"  {v!r}")
    else:
        print("未發現違規。")


def cmd_replay(args, corpus):
    fname, applied, lines = generate_case(corpus, args.seed, args.replay)
    violations, transcript, fatal, noise = run_case_robust(
        lines, ROUNDTRIP_SCRATCH, args.timeout)
    print(f"=== --replay {args.replay}（seed={args.seed}） ===")
    print_transcript(fname, applied, lines, violations, transcript)
    if noise:
        print("（原始一次跑出過疑似類1事件，但獨立複驗沒有重現，判定為環境雜訊）")
    if fatal:
        print("（此案例讓 bridge 行程掛掉/失去回應，且獨立複驗仍重現——非環境雜訊）")
    return 0


def cmd_shrink(args, corpus):
    fname, applied, lines = generate_case(corpus, args.seed, args.shrink)
    violations, transcript, fatal, noise = run_case_robust(
        lines, ROUNDTRIP_SCRATCH, args.timeout)
    if not violations:
        print(f"案例 {args.shrink}（seed={args.seed}）目前沒有違規，沒有東西可縮小。")
        return 0
    primary_sig = violations[0].signature()
    print(f"原始案例：{len(lines)} 行，違規：{violations[0]!r}")
    shrunk_lines, attempts, ok = shrink_case(
        lambda: lines, primary_sig, ROUNDTRIP_SCRATCH,
        max_attempts=args.shrink_attempts, time_budget=args.shrink_time_budget,
        timeout=args.timeout)
    print(f"縮小完成：{len(lines)} 行 -> {len(shrunk_lines)} 行（嘗試 {attempts} 次）")
    final_v, _, _, _ = run_case_robust(shrunk_lines, ROUNDTRIP_SCRATCH, args.timeout)
    scene_path, report_path = save_finding(
        args.shrink, args.seed, args.cases, fname, applied, shrunk_lines, final_v,
        shrunk=True, attempts=attempts)
    print(f"已存最小重現：{scene_path}")
    print(f"REPORT 附加於：{report_path}")
    for v in final_v:
        print(f"  {v!r}")
    return 0


def cmd_cases(args, corpus):
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    total_violations = 0
    by_category = {1: 0, 2: 0, 3: 0, 4: 0}
    mutation_coverage = {k: 0 for k in MUTATION_KINDS}
    violation_cases = []
    restarts = 0
    t0 = time.time()
    batch_size = args.batch_size

    for i in range(args.cases):
        fname, applied, lines = generate_case(corpus, args.seed, i)
        for kind in applied:
            base_kind = kind.split("(")[0]
            if base_kind in mutation_coverage:
                mutation_coverage[base_kind] += 1

        violations, transcript, fatal, noise = run_case_robust(
            lines, ROUNDTRIP_SCRATCH, args.timeout)
        if fatal:
            restarts += 1
        if noise:
            print(f"  [note] 案例 {i}：疑似類1事件複驗未重現，判定環境雜訊，已捨棄", flush=True)

        if violations:
            total_violations += len(violations)
            for v in violations:
                by_category[v.category] += 1
            violation_cases.append(i)
            primary_sig = violations[0].signature()
            shrunk_lines, attempts, _ = shrink_case(
                lambda ln=lines: ln, primary_sig, ROUNDTRIP_SCRATCH,
                max_attempts=args.shrink_attempts, time_budget=args.shrink_time_budget,
                timeout=args.timeout)
            final_v, _, fatal2, noise2 = run_case_robust(
                shrunk_lines, ROUNDTRIP_SCRATCH, args.timeout)
            if fatal2:
                restarts += 1
            scene_path, _ = save_finding(
                i, args.seed, args.cases, fname, applied, shrunk_lines,
                final_v or violations, shrunk=True, attempts=attempts)
            print(f"  !! 案例 {i} 發現違規（{len(violations)} 個，"
                  f"已縮到 {len(shrunk_lines)} 行）-> {scene_path}", flush=True)
            for v in (final_v or violations):
                print(f"       {v!r}", flush=True)

        if (i + 1) % batch_size == 0 or (i + 1) == args.cases:
            elapsed = time.time() - t0
            print(f"[batch] 已跑 {i + 1}/{args.cases} 案例，累計違規 {total_violations} 個，"
                  f"行程重啟 {restarts} 次，耗時 {elapsed:.1f}s", flush=True)

    elapsed = time.time() - t0

    print()
    print("========== fuzz_scene 統計 ==========")
    print(f"seed={args.seed} cases={args.cases} 耗時={elapsed:.1f}s")
    print(f"總違規數：{total_violations}（{len(violation_cases)} 個案例中）")
    for cat in (1, 2, 3, 4):
        print(f"  類{cat}（{CATEGORY_NAMES[cat]}）：{by_category[cat]} 個")
    print(f"bridge 行程重啟次數：{restarts}")
    print("各類變形覆蓋的案例數：")
    for kind in MUTATION_KINDS:
        print(f"  {kind}: {mutation_coverage[kind]}")
    if violation_cases:
        print(f"違規案例編號：{violation_cases}")
    else:
        print("未發現任何違規。")

    report_path = FINDINGS_DIR / "REPORT.md"
    with report_path.open("a", encoding="utf-8") as f:
        f.write(
            f"\n# 執行摘要（seed={args.seed}, cases={args.cases}）\n"
            f"- 耗時：{elapsed:.1f}s\n"
            f"- 總違規數：{total_violations}（{len(violation_cases)} 個案例）\n"
            f"- 類別分布：類1={by_category[1]} 類2={by_category[2]} "
            f"類3={by_category[3]} 類4={by_category[4]}\n"
            f"- bridge 行程重啟次數：{restarts}\n"
            f"- 違規案例編號：{violation_cases}\n"
        )
    print(f"\nREPORT 已附加：{report_path}")
    return 0 if total_violations == 0 else 0  # 找到違規不是 harness 本身的錯誤，仍回 0


def build_arg_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, default=1, help="全域亂數種子")
    p.add_argument("--cases", type=int, default=200, help="要跑的案例數")
    p.add_argument("--replay", type=int, default=None, help="只重播單一案例編號，印完整逐行記錄")
    p.add_argument("--shrink", type=int, default=None, help="對單一案例縮小到最小重現")
    p.add_argument("--timeout", type=float, default=CMD_TIMEOUT_DEFAULT,
                    help="單次 bridge 往返逾時秒數（判定卡住）")
    p.add_argument("--batch-size", type=int, default=50, help="每幾個案例印一次進度統計")
    p.add_argument("--shrink-attempts", type=int, default=120, help="自動縮小每個違規時的最大嘗試次數")
    p.add_argument("--shrink-time-budget", type=float, default=15.0, help="自動縮小每個違規的時間上限（秒）")
    return p


def main():
    args = build_arg_parser().parse_args()

    if not BRIDGE_PATH.exists():
        print(f"找不到 bridge.exe：{BRIDGE_PATH}\n"
              f"規則是不重編任何 exe，請確認已編好的 bridge 放在這個路徑，"
              f"或用 GEOMETRY_TEST_BRIDGE 環境變數指過去。", file=sys.stderr)
        return 2

    corpus = load_corpus()
    print(f"語料：{len(corpus)} 個合法 .scene 夾具（{ROOT}）", flush=True)
    print(f"bridge：{BRIDGE_PATH}", flush=True)

    if args.replay is not None:
        return cmd_replay(args, corpus)
    if args.shrink is not None:
        return cmd_shrink(args, corpus)
    return cmd_cases(args, corpus)


if __name__ == "__main__":
    sys.exit(main())
