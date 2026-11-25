#!/usr/bin/env python3
"""OpenAI worker／審查的模型迴圈：用官方 openai Python SDK 直接呼叫 Responses API。

由 .github/workflows/openai-worker.yml（mode=worker）與 .github/workflows/openai-adversarial-review.yml
（mode=review）使用；兩者都取觸發 run 的 main commit 上的本檔，不取受審或工作分支裡的版本。
不使用 Codex CLI、codex exec 或 Codex GitHub Action：ChatGPT 訂閱附的 API 點數不涵蓋經 API 金鑰使用 Codex。

輸入：提示詞從 stdin 讀；金鑰從環境變數 OPENAI_API_KEY 讀（讀後立刻自本行程環境移除，子行程一律不帶）。
輸出：stdout 只印一個 JSON 物件（結果），進度與每輪 usage 印到 stderr。
  - 相容 api-worker.yml 留言步驟的欄位：result、is_error、subtype、num_turns、total_cost_usd。
  - 另有：started（是否已送出過 API 請求）、end_reason（結束原因）、cost_is_estimate（恆為 true）、
    usage（累計）、turns（每輪 usage 與估算花費）、error（API 錯誤摘要）、pricing（估算用價格與來源）。

模式：
  worker：工具 run_shell（工作樹內跑 bash，單次逾時、輸出截斷）、read_file、write_file（只限工作樹內）。
  review：工具 read_file、search（只讀、只限工作目錄內；沒有 shell）。
  --list-tools：不連網、不需金鑰，印出本模式實際提供給模型的工具名稱（workflow 用來預檢）。

結束條件（end_reason）：
  completed                 模型不再呼叫工具並給出最終報告（唯一 is_error=false 的情況）
  budget_exceeded           估算花費達上限；停止執行工具，要求模型輸出最終報告
  max_turns                 達到最大輪數；同上
  time_limit                達到總時限；同上（時間仍夠時）
  credit_balance_exhausted  API 回 HTTP 429、錯誤碼 credit_balance_exhausted（點數用完）
  quota_or_spend_limit      其他額度／花費上限類 429（insufficient_quota、*spend_limit* 等）
  api_error                 其他無法重試或重試後仍失敗的 API 錯誤
  usage_missing             回應沒有 usage，無法估算花費，為守住上限而停止
  unexpected_service_tier   回應的 service tier 不在價格表範圍，無法可靠估算
  incomplete                回應狀態 incomplete 且沒有可用報告
  interrupted               收到 SIGTERM／SIGINT（例如 step 逾時或取消）
"""
import argparse
import fnmatch
import json
import os
import re
import signal
import subprocess
import sys
import time

SCHEMA = "openai-agent-result/1"

# ---- 價格表（美元／每 100 萬 token，Standard 層級）。花費一律是「估算」。
# 來源（2026-11-25 查核）：
#   https://developers.openai.com/api/docs/pricing
#   https://developers.openai.com/api/docs/models/gpt-6.2-astra
#   https://developers.openai.com/api/docs/models/gpt-6.2-sol
# 長脈絡：單次請求 input 超過 272K token 時，整個請求的 input／cache 單價 ×2、output 單價 ×1.5。
PRICING_SOURCES = [
    "https://developers.openai.com/api/docs/pricing",
    "https://developers.openai.com/api/docs/models/gpt-6.2-astra",
    "https://developers.openai.com/api/docs/models/gpt-6.2-sol",
]
PRICING = {
    "gpt-6.2-astra": {"input": 8.00, "cached_input": 0.40, "cache_write_30m": 10.00,
                      "cache_write_12h": 20.00, "output": 40.00},
    "gpt-6.2-sol": {"input": 2.00, "cached_input": 0.10, "cache_write_30m": 2.50,
                    "cache_write_12h": 5.00, "output": 10.00},
}
MODELS = tuple(PRICING)  # 模型白名單＝有價格的模型
DEFAULT_MODEL = "gpt-6.2-astra"
LONG_CONTEXT_TOKENS = 272_000
# 回應的 service tier → 價格倍率。不在表內就停止（無法可靠估算）。
TIER_MULTIPLIER = {None: 1.0, "default": 1.0, "flex": 1.0, "priority": 2.0, "fast": 2.0}

SHELL_DEFAULT_TIMEOUT = 300
SHELL_MAX_TIMEOUT = 1800
TOOL_OUTPUT_LIMIT = 30_000      # 單次工具輸出回給模型的字元上限（頭尾各留一半）
READ_LIMIT_BYTES = 400_000      # read_file 單次最多讀的 bytes
WRITE_LIMIT_BYTES = 5_000_000   # write_file 單次最多寫的 bytes
SEARCH_MAX_MATCHES = 400
SEARCH_MAX_FILES = 5000
WRAPUP_RESERVE = 0.15           # 估算花費達上限的 85% 時就收尾，留 15% 給「輸出最終報告」那一次請求
WRAPUP_MAX_OUTPUT_TOKENS = 12_000
TURN_MAX_OUTPUT_TOKENS = 32_000   # 一般輪次的單次輸出上限（含 reasoning），讓單輪花費有上界
RETRY_DELAYS = (2, 5, 15, 30)
SECRET_ENV = ("OPENAI_API_KEY",)

QUOTA_CODES = ("insufficient_quota", "billing_hard_limit_reached")


class Interrupted(BaseException):
    """收到 SIGTERM／SIGINT。用 BaseException，避免被 SDK 內部的 except Exception 吞成連線錯誤。"""


def log(msg):
    print(f"[openai-agent] {msg}", file=sys.stderr, flush=True)


def clip(text, limit=TOOL_OUTPUT_LIMIT):
    if len(text) <= limit:
        return text
    half = limit // 2
    return (text[:half] + f"\n…（輸出過長，已截去中間 {len(text) - 2 * half} 字元）…\n" + text[-half:])


# ---------------------------------------------------------------- 路徑限制
def resolve_inside(roots, path, *, must_exist=True):
    """把 path（相對於第一個 root，或絕對路徑）解析成真實路徑，必須落在某個 root 之內。"""
    if not isinstance(path, str) or not path or "\0" in path:
        raise ValueError("路徑不合法")
    base = roots[0]
    cand = path if os.path.isabs(path) else os.path.join(base, path)
    real = os.path.realpath(cand)
    if must_exist and not os.path.exists(real):
        raise ValueError(f"檔案不存在：{path}")
    for r in roots:
        if real == r or real.startswith(r.rstrip("/") + "/"):
            return real
    raise ValueError(f"路徑不在允許範圍內：{path}（允許：{', '.join(roots)}）")


# ---------------------------------------------------------------- 工具
class Tools:
    def __init__(self, mode, workdir, read_roots, deadline, reserve_sec=0):
        self.mode = mode
        self.reserve_sec = reserve_sec  # 總時限前保留給收尾的秒數；shell 命令不得吃掉這段
        self.workdir = os.path.realpath(workdir)
        self.read_roots = [self.workdir] + [os.path.realpath(r) for r in read_roots if r]
        self.deadline = deadline

    # 工具定義（Responses API 的 function 工具）
    def definitions(self):
        read_file = {
            "type": "function", "name": "read_file",
            "description": ("讀一個文字檔，回傳帶行號的內容。path 可為相對於工作目錄的路徑，或允許範圍內的絕對路徑"
                            f"（{', '.join(self.read_roots)}）。大檔用 offset／limit 分段讀。"),
            "parameters": {"type": "object", "additionalProperties": False,
                           "properties": {"path": {"type": "string"},
                                          "offset": {"type": ["integer", "null"], "description": "從第幾行開始（1 起算）"},
                                          "limit": {"type": ["integer", "null"], "description": "最多讀幾行（預設 2000）"}},
                           "required": ["path", "offset", "limit"]},
            "strict": True,
        }
        if self.mode == "review":
            search = {
                "type": "function", "name": "search",
                "description": ("在允許範圍內搜尋。pattern 為 Python 正規表示式；pattern 為空字串時只列出符合 glob 的檔名。"
                                "path 是搜尋起點（檔案或目錄），glob 篩選檔名（例如 **/*.py）。"),
                "parameters": {"type": "object", "additionalProperties": False,
                               "properties": {"pattern": {"type": "string"},
                                              "path": {"type": ["string", "null"]},
                                              "glob": {"type": ["string", "null"]},
                                              "ignore_case": {"type": ["boolean", "null"]}},
                               "required": ["pattern", "path", "glob", "ignore_case"]},
                "strict": True,
            }
            return [read_file, search]
        run_shell = {
            "type": "function", "name": "run_shell",
            "description": (f"在工作目錄 {self.workdir} 以 bash 執行一段命令，回傳結束碼與合併的 stdout／stderr"
                            f"（超過 {TOOL_OUTPUT_LIMIT} 字元會截去中間）。timeout_sec 預設 {SHELL_DEFAULT_TIMEOUT}、"
                            f"上限 {SHELL_MAX_TIMEOUT}；逾時會整組行程被終止。不會帶任何金鑰或 token。"),
            "parameters": {"type": "object", "additionalProperties": False,
                           "properties": {"command": {"type": "string"},
                                          "timeout_sec": {"type": ["integer", "null"]}},
                           "required": ["command", "timeout_sec"]},
            "strict": True,
        }
        write_file = {
            "type": "function", "name": "write_file",
            "description": "把 content 原樣（UTF-8）寫進工作目錄內的檔案；檔案存在就整個覆寫，父目錄不存在會建立。",
            "parameters": {"type": "object", "additionalProperties": False,
                           "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                           "required": ["path", "content"]},
            "strict": True,
        }
        return [run_shell, read_file, write_file]

    def names(self):
        return sorted(d["name"] for d in self.definitions())

    def call(self, name, raw_args):
        try:
            args = json.loads(raw_args or "{}")
            if not isinstance(args, dict):
                raise ValueError("參數必須是 JSON 物件")
        except ValueError as e:
            return f"錯誤：參數不是合法 JSON（{e}）"
        if name not in self.names():
            return f"錯誤：沒有這個工具：{name}"
        try:
            return getattr(self, "t_" + name)(**args)
        except TypeError as e:
            return f"錯誤：參數不符（{e}）"
        except ValueError as e:
            return f"錯誤：{e}"
        except OSError as e:
            return f"錯誤：{e.strerror or e}"

    def t_read_file(self, path, offset=None, limit=None):
        real = resolve_inside(self.read_roots, path)
        if os.path.isdir(real):
            entries = sorted(os.listdir(real))
            return clip(f"（{path} 是目錄，共 {len(entries)} 項）\n" + "\n".join(entries))
        offset = max(int(offset or 1), 1)
        limit = min(max(int(limit or 2000), 1), 20000)
        with open(real, "rb") as f:
            data = f.read(READ_LIMIT_BYTES + 1)
        truncated = len(data) > READ_LIMIT_BYTES
        text = data[:READ_LIMIT_BYTES].decode("utf-8", "replace")
        lines = text.splitlines()
        sel = lines[offset - 1: offset - 1 + limit]
        body = "\n".join(f"{i:6d}\t{l}" for i, l in enumerate(sel, start=offset))
        note = []
        if offset - 1 + limit < len(lines):
            note.append(f"（還有後續行，可用 offset={offset + limit} 繼續）")
        if truncated:
            note.append(f"（檔案超過 {READ_LIMIT_BYTES} bytes，只讀了開頭；後段請用 run_shell 或分檔處理）")
        return clip(body + ("\n" + "\n".join(note) if note else ""))

    def t_write_file(self, path, content):
        if self.mode != "worker":
            raise ValueError("唯讀模式不能寫檔")
        data = content.encode("utf-8")
        if len(data) > WRITE_LIMIT_BYTES:
            raise ValueError(f"內容超過 {WRITE_LIMIT_BYTES} bytes")
        parent = os.path.dirname(path if os.path.isabs(path) else os.path.join(self.workdir, path))
        os.makedirs(resolve_inside([self.workdir], parent, must_exist=False), exist_ok=True)
        real = resolve_inside([self.workdir], path, must_exist=False)
        if real == self.workdir or os.path.isdir(real):
            raise ValueError("不能寫入目錄")
        with open(real, "wb") as f:
            f.write(data)
        return f"已寫入 {os.path.relpath(real, self.workdir)}（{len(data)} bytes）"

    def t_run_shell(self, command, timeout_sec=None):
        if self.mode != "worker":
            raise ValueError("唯讀模式沒有 shell")
        # 收尾時點 T＝總時限－保留秒數；命令必須在 T 之前結束（limit_reason 在 T−3 秒起就會收尾）。
        remaining = self.deadline - self.reserve_sec - time.monotonic()
        if remaining < 3:
            return "錯誤：總時限將到，不再執行命令"
        t = int(timeout_sec or SHELL_DEFAULT_TIMEOUT)
        t = max(1, min(t, SHELL_MAX_TIMEOUT, int(remaining - 1)))
        env = {k: v for k, v in os.environ.items() if k not in SECRET_ENV}
        start = time.monotonic()
        p = subprocess.Popen(["bash", "-c", command], cwd=self.workdir, env=env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            out, _ = p.communicate(timeout=t)
            status = f"結束碼 {p.returncode}"
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
            out, _ = p.communicate()
            status = f"逾時（{t} 秒）已終止整組行程"
        except BaseException:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
            raise
        text = (out or b"").decode("utf-8", "replace")
        return clip(f"[{status}；耗時 {time.monotonic() - start:.1f} 秒]\n{text}")

    def t_search(self, pattern, path=None, glob=None, ignore_case=None):
        if self.mode != "review":
            raise ValueError("本模式沒有 search 工具")
        start = resolve_inside(self.read_roots, path or ".")
        rx = None
        if pattern:
            try:
                rx = re.compile(pattern, re.IGNORECASE if ignore_case else 0)
            except re.error as e:
                raise ValueError(f"正規表示式錯誤：{e}")
        files = []
        if os.path.isfile(start):
            files = [start]
        else:
            for dp, dns, fns in os.walk(start):
                dns[:] = sorted(d for d in dns if d != ".git")
                for fn in sorted(fns):
                    full = os.path.join(dp, fn)
                    rel = os.path.relpath(full, start)
                    if glob and not (fnmatch.fnmatch(rel, glob) or fnmatch.fnmatch(fn, glob)):
                        continue
                    if os.path.islink(full):
                        continue
                    files.append(full)
                    if len(files) >= SEARCH_MAX_FILES:
                        break
                if len(files) >= SEARCH_MAX_FILES:
                    break
        if rx is None:
            return clip(f"（{len(files)} 個檔案{'，已達上限' if len(files) >= SEARCH_MAX_FILES else ''}）\n" + "\n".join(files))
        hits = []
        for full in files:
            try:
                with open(full, "rb") as f:
                    data = f.read(READ_LIMIT_BYTES * 5)
            except OSError:
                continue
            if b"\0" in data[:8192]:
                continue
            for i, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{full}:{i}:{line[:400]}")
                    if len(hits) >= SEARCH_MAX_MATCHES:
                        break
            if len(hits) >= SEARCH_MAX_MATCHES:
                break
        more = "（已達上限，請縮小範圍）" if len(hits) >= SEARCH_MAX_MATCHES else ""
        return clip(f"（{len(hits)} 筆符合{more}）\n" + "\n".join(hits))


# ---------------------------------------------------------------- 花費估算
def _get(obj, *names, default=0):
    for n in names:
        if obj is None:
            return default
        obj = obj.get(n) if isinstance(obj, dict) else getattr(obj, n, None)
    return default if obj is None else obj


def estimate_cost(model, usage, service_tier):
    """回傳 (花費美元估算, usage 摘要)。沒有 usage 回 (None, None)。

    保守（偏高）估算：未命中快取的 input 以「input − cached」計，不扣除 cache write token；
    cache write 另依 30 分鐘／12 小時的單價加計。
    """
    if usage is None:
        return None, None
    p = PRICING[model]
    inp = int(_get(usage, "input_tokens"))
    out = int(_get(usage, "output_tokens"))
    cached = int(_get(usage, "input_tokens_details", "cached_tokens"))
    cw = int(_get(usage, "input_tokens_details", "cache_write_tokens"))
    cw12 = int(_get(usage, "input_tokens_details", "cache_write_tokens_details", "ttl_12h_tokens"))
    cw30 = max(cw - cw12, int(_get(usage, "input_tokens_details", "cache_write_tokens_details", "ttl_30m_tokens")))
    reasoning = int(_get(usage, "output_tokens_details", "reasoning_tokens"))
    long_ctx = inp > LONG_CONTEXT_TOKENS
    in_mult = 2.0 if long_ctx else 1.0
    out_mult = 1.5 if long_ctx else 1.0
    tier = TIER_MULTIPLIER[service_tier]
    cost = ((max(inp - cached, 0) * p["input"] + cached * p["cached_input"]
             + cw30 * p["cache_write_30m"] + cw12 * p["cache_write_12h"]) * in_mult
            + out * p["output"] * out_mult) * tier / 1_000_000
    return cost, {"input_tokens": inp, "cached_tokens": cached, "cache_write_tokens": cw,
                  "cache_write_12h_tokens": cw12, "output_tokens": out, "reasoning_tokens": reasoning,
                  "long_context": long_ctx, "service_tier": service_tier}


# ---------------------------------------------------------------- 主迴圈
class Agent:
    def __init__(self, a, prompt, client, tools):
        self.a, self.prompt, self.client, self.tools = a, prompt, client, tools
        self.items = [{"role": "user", "content": prompt}]
        self.turns = []
        self.cost = 0.0
        self.api_calls = 0
        self.started = False
        self.error = None
        self.totals = {"input_tokens": 0, "cached_tokens": 0, "cache_write_tokens": 0,
                       "output_tokens": 0, "reasoning_tokens": 0}
        self.last_input_tokens = 0

    def instructions(self):
        if self.a.mode == "review":
            return ("你是唯讀審查者，只能用 read_file 與 search 工具。依使用者訊息中的規則工作，"
                    "完成後直接輸出最終審查報告（Markdown），不要再呼叫工具。")
        return ("你是在 GitHub Actions 上執行的 worker，只能用 run_shell、read_file、write_file 工具。"
                "依使用者訊息中的規則工作；完成後直接輸出最終報告（Markdown），不要再呼叫工具。")

    def request(self, *, tool_choice="auto", max_output_tokens=None):
        """送一次 Responses API 請求；可重試的錯誤自己重試（SDK 內建重試已關）。回傳 response 或 None（已記錄 error）。"""
        import openai  # 延後匯入：--list-tools 不需要 SDK
        kwargs = dict(model=self.a.model, instructions=self.instructions(), input=self.items,
                      tools=self.tools.definitions(), tool_choice=tool_choice, parallel_tool_calls=True,
                      reasoning={"effort": self.a.effort}, store=False,
                      include=["reasoning.encrypted_content"], service_tier="default")
        if max_output_tokens:
            kwargs["max_output_tokens"] = max_output_tokens
        attempt = 0
        while True:
            remaining = self.a.deadline - time.monotonic()
            if remaining < 10:
                self.error = {"kind": "time", "message": "總時限已到，未送出請求"}
                return None
            self.started = True
            self.api_calls += 1
            try:
                return self.client.responses.create(timeout=min(900.0, remaining), **kwargs)
            except openai.APIStatusError as e:
                code = getattr(e, "code", None)
                err = {"kind": "status", "status": e.status_code, "code": code,
                       "type": getattr(e, "type", None), "message": str(getattr(e, "message", e))[:500],
                       "request_id": getattr(e, "request_id", None)}
                if e.status_code == 429 and code == "credit_balance_exhausted":
                    err["end_reason"] = "credit_balance_exhausted"
                    self.error = err
                    return None
                if e.status_code == 429 and code and (code in QUOTA_CODES or "spend_limit" in code or "quota" in code):
                    err["end_reason"] = "quota_or_spend_limit"
                    self.error = err
                    return None
                retryable = e.status_code in (408, 409, 429) or e.status_code >= 500
                if not retryable or attempt >= len(RETRY_DELAYS):
                    err["end_reason"] = "api_error"
                    self.error = err
                    return None
                log(f"API {e.status_code} {code}，{RETRY_DELAYS[attempt]} 秒後重試")
            except (openai.APIConnectionError, openai.APITimeoutError) as e:
                if attempt >= len(RETRY_DELAYS):
                    self.error = {"kind": "connection", "message": str(e)[:500], "end_reason": "api_error"}
                    return None
                log(f"連線錯誤（{type(e).__name__}），{RETRY_DELAYS[attempt]} 秒後重試")
            except openai.OpenAIError as e:
                self.error = {"kind": type(e).__name__, "message": str(e)[:500], "end_reason": "api_error"}
                return None
            time.sleep(min(RETRY_DELAYS[attempt], max(self.a.deadline - time.monotonic() - 10, 0)))
            attempt += 1

    def account(self, resp):
        """記錄一輪 usage 與估算花費。回傳 None 表示可繼續，否則回傳應停止的 end_reason。"""
        tier = getattr(resp, "service_tier", None)
        if tier not in TIER_MULTIPLIER:
            self.turns.append({"turn": len(self.turns) + 1, "service_tier": tier, "cost_estimate_usd": None})
            return "unexpected_service_tier"
        cost, u = estimate_cost(self.a.model, getattr(resp, "usage", None), tier)
        if cost is None:
            self.turns.append({"turn": len(self.turns) + 1, "usage": None, "cost_estimate_usd": None})
            return "usage_missing"
        self.cost += cost
        for k in self.totals:
            self.totals[k] += u.get(k, 0)
        self.last_input_tokens = u["input_tokens"]
        self.turns.append({"turn": len(self.turns) + 1, "response_id": getattr(resp, "id", None),
                           "status": getattr(resp, "status", None), "usage": u,
                           "cost_estimate_usd": round(cost, 6), "cumulative_cost_estimate_usd": round(self.cost, 6)})
        log(f"第 {len(self.turns)} 輪：input {u['input_tokens']}（cached {u['cached_tokens']}）"
            f" output {u['output_tokens']}（reasoning {u['reasoning_tokens']}）"
            f" 估算 US${cost:.4f}，累計 US${self.cost:.4f}／上限 US${self.a.max_budget_usd}")
        return None

    def projected_next_cost(self):
        # 下一輪的預估：取上一輪估算花費的 1.5 倍（脈絡只會變長）。
        last = self.turns[-1].get("cost_estimate_usd") if self.turns else 0
        return 1.5 * (last or 0)

    def limit_reason(self):
        if self.cost >= self.a.max_budget_usd * (1 - WRAPUP_RESERVE):
            return "budget_exceeded"
        # 再做一輪之後，還要留得下收尾那一輪：兩輪的預估都要放得進上限。
        if self.cost + 2 * self.projected_next_cost() > self.a.max_budget_usd:
            return "budget_exceeded"
        if len(self.turns) >= self.a.max_turns:
            return "max_turns"
        if time.monotonic() >= self.a.deadline - self.a.wrapup_seconds - 3:
            return "time_limit"
        return None

    def wrapup(self, reason):
        """達到上限：不再執行工具；要求模型不呼叫工具、直接輸出最終報告。回傳報告文字（可能為空）。"""
        if self.cost + self.projected_next_cost() > self.a.max_budget_usd:
            log("估算花費加上收尾預估會超過上限，不再送出任何請求（沒有模型報告）")
            return ""
        if time.monotonic() >= self.a.deadline - 10:
            log("總時限已到，不再送出任何請求（沒有模型報告）")
            return ""
        msg = {"budget_exceeded": "估算花費已接近本次上限", "max_turns": "已達最大輪數",
               "time_limit": "已接近總時限"}[reason]
        self.items.append({"role": "user", "content":
                           f"【workflow 通知】{msg}，工作到此為止：不要再呼叫任何工具，"
                           "立刻依提示詞規定的格式輸出最終報告，並在「未驗項」寫明哪些工作因此沒有完成。"})
        resp = self.request(tool_choice="none", max_output_tokens=WRAPUP_MAX_OUTPUT_TOKENS)
        if resp is None:
            return ""
        self.account(resp)
        return (getattr(resp, "output_text", "") or "").strip()

    def run(self):
        while True:
            reason = self.limit_reason()
            if reason:
                return reason, self.wrapup(reason)
            resp = self.request(max_output_tokens=TURN_MAX_OUTPUT_TOKENS)
            if resp is None:
                return self.error.get("end_reason", "api_error"), ""
            stop = self.account(resp)
            if stop:
                return stop, ""
            output = list(getattr(resp, "output", None) or [])
            calls = [o for o in output if getattr(o, "type", None) == "function_call"]
            self.items.extend(output)
            if not calls:
                text = (getattr(resp, "output_text", "") or "").strip()
                if getattr(resp, "status", None) == "incomplete" or not text:
                    detail = getattr(getattr(resp, "incomplete_details", None), "reason", None)
                    self.error = {"kind": "incomplete", "message": f"回應狀態 {getattr(resp, 'status', None)}（{detail}），沒有可用報告"}
                    return "incomplete", text
                return "completed", text
            for c in calls:
                log(f"工具 {c.name}（call {c.call_id}）")
                out = self.tools.call(c.name, c.arguments)
                self.items.append({"type": "function_call_output", "call_id": c.call_id, "output": out})


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=("worker", "review"), required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--read-root", action="append", default=[], help="額外允許讀取的目錄（唯讀）")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--effort", default="high", choices=("low", "medium", "high", "xhigh", "max"))
    ap.add_argument("--max-turns", type=int, default=200)
    ap.add_argument("--max-budget-usd", type=float, default=10.0)
    ap.add_argument("--time-limit-sec", type=int, default=7200)
    ap.add_argument("--wrapup-seconds", type=int, default=300, help="距總時限多少秒時開始收尾")
    ap.add_argument("--list-tools", action="store_true")
    a = ap.parse_args(argv)
    if a.model not in MODELS:
        ap.error(f"model 不在白名單：{', '.join(MODELS)}")
    if not (0 < a.max_budget_usd <= 30):
        ap.error("max-budget-usd 必須在 (0, 30]")
    if not (1 <= a.max_turns <= 2000):
        ap.error("max-turns 必須在 1..2000")
    if not (60 <= a.time_limit_sec <= 6 * 3600):
        ap.error("time-limit-sec 必須在 60..21600")
    if not os.path.isdir(a.workdir):
        ap.error("workdir 不存在")
    return a


def main(argv=None):
    a = parse_args(sys.argv[1:] if argv is None else argv)
    t0 = time.monotonic()
    a.deadline = t0 + a.time_limit_sec
    a.wrapup_seconds = min(a.wrapup_seconds, a.time_limit_sec // 4)
    tools = Tools(a.mode, a.workdir, a.read_root, a.deadline, reserve_sec=a.wrapup_seconds)
    if a.list_tools:
        print(json.dumps({"mode": a.mode, "tools": tools.names()}, ensure_ascii=False))
        return 0

    key = os.environ.pop("OPENAI_API_KEY", "")
    for k in SECRET_ENV:
        os.environ.pop(k, None)
    prompt = sys.stdin.read()
    result = {"schema": SCHEMA, "mode": a.mode, "model": a.model, "effort": a.effort, "started": False,
              "end_reason": None, "subtype": None, "is_error": True, "num_turns": 0, "api_calls": 0,
              "total_cost_usd": 0.0, "cost_is_estimate": True,
              "cost_note": "依文件價格表與每輪 usage 估算（保守、偏高），不是帳單金額；實際以 OpenAI 用量頁為準",
              "max_budget_usd": a.max_budget_usd, "max_turns": a.max_turns, "time_limit_sec": a.time_limit_sec,
              "usage": None, "turns": [], "error": None, "result": "",
              "pricing": {"model": a.model, "usd_per_1m_tokens": PRICING[a.model], "sources": PRICING_SOURCES,
                          "long_context_over_tokens": LONG_CONTEXT_TOKENS}}
    agent = None

    def on_signal(signum, frame):
        raise Interrupted(signal.Signals(signum).name)

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)
    try:
        if not prompt.strip():
            result.update(end_reason="empty_prompt", error={"kind": "input", "message": "stdin 沒有提示詞"})
        elif not key:
            result.update(end_reason="missing_api_key", error={"kind": "input", "message": "沒有 OPENAI_API_KEY"})
        else:
            import openai
            client = openai.OpenAI(api_key=key, max_retries=0)
            del key
            agent = Agent(a, prompt, client, tools)
            reason, text = agent.run()
            result.update(end_reason=reason, result=text, is_error=(reason != "completed"), error=agent.error)
    except Interrupted as e:
        result.update(end_reason="interrupted", error={"kind": "signal", "message": f"收到 {e}，中斷"})
    except Exception as e:  # 任何未預期錯誤都照實記錄，仍輸出 JSON
        result.update(end_reason="agent_error", error={"kind": type(e).__name__, "message": str(e)[:500]})
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if agent is not None:
            result.update(started=agent.started, api_calls=agent.api_calls, num_turns=len(agent.turns),
                          total_cost_usd=round(agent.cost, 6), usage=agent.totals, turns=agent.turns)
        result["subtype"] = result["end_reason"]
        result["elapsed_sec"] = round(time.monotonic() - t0, 1)
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
        sys.stdout.flush()
    return 0 if result["end_reason"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
