#!/usr/bin/env python3
"""openai-dispatch.yml 的認領步驟：從任務 issue 挑出下一件待派的任務留言。

只用標準函式庫；不帶 API 金鑰、不呼叫模型。由 openai-dispatch.yml 的每個 claim job 執行一次：

  python3 -I .github/scripts/openai_dispatch.py claim --slot N

規則（設計理由見建立本檔的 PR 說明）：
- 任務：擁有者本人（id、login、type=User 三者都對）發、第一行以「【任務」開頭的留言。非擁有者的同形留言只記 id 與作者，不讀內文、不派。
- 已處理：有對應結果留言（擁有者或 github-actions[bot] 發、第一行是「【OpenAI worker】任務留言 <id>（#N）」
  或「【API worker】任務留言 <id>（#N）」），或有派工標記（github-actions[bot] 發、第一行是「【OpenAI 派工】任務留言 <id>（#N）」）。
  失敗、拒推的結果也算已處理；本腳本不重試。
- 執行中：openai-worker.yml／api-worker.yml 有 queued／in_progress 等狀態的 run。openai-worker 的 run 標題
  帶任務留言 id，該任務跳過；標題看不出 id 的 run、或任何 api-worker run，整輪不派（無法排除重複）。
- 參數只取第一行：「上限 US$N」（必填，0 < N ≤ 30）、「起始分支 `X`」（沒寫就 main）、「建議模型 X」（沒寫就預設；
  寫了白名單外的模型就留給其他 worker，不派、不標記）。上限缺漏或超過 30、起始分支格式不符：貼一則「不派工」標記，之後不再看。
- 點數用完：最新一則 OpenAI worker 結果寫著 end_reason credit_balance_exhausted 時，schedule 觸發一律不派；
  擁有者手動觸發時只有第 1 件可越過（當作「點數已恢復」的確認），第 2 件起照樣停止。
- 認領：先貼派工標記（貼不出就失敗，不派），再把參數寫進 GITHUB_OUTPUT 交給 workflow_call。
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

MODELS = ("gpt-6.2-astra", "gpt-6.2-sol")
DEFAULT_MODEL = "gpt-6.2-astra"
MAX_SLOTS = 6
BOT_LOGIN = "github-actions[bot]"
BOT_ID = "41898282"
ACTIVE = ("queued", "in_progress", "waiting", "requested", "pending")
CREDIT_LINE = re.compile(r"^- 結束原因：`credit_balance_exhausted`", re.M)
BASE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}")
CAP_RE = re.compile(r"上限\s*US\$\s*([0-9]+(?:\.[0-9]+)?)")
BASE_IN_LINE = re.compile(r"起始分支(?:是)?\s*`([^`\n]*)`")
MODEL_IN_LINE = re.compile(r"建議模型\s*([A-Za-z0-9][A-Za-z0-9._-]{0,63})")


class ApiError(Exception):
    pass


def api(method, path, body=None):
    base = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    req.add_header("Authorization", "Bearer " + os.environ["GH_TOKEN"])
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "openai-dispatch")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        raise ApiError(f"{method} {path} → HTTP {e.code}") from None
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise ApiError(f"{method} {path} → {type(e).__name__}") from None


def list_all(path, key=None):
    out = []
    for page in range(1, 101):
        sep = "&" if "?" in path else "?"
        _, data = api("GET", f"{path}{sep}per_page=100&page={page}")
        items = data.get(key) if key else data
        if not isinstance(items, list):
            raise ApiError(f"GET {path} 回應格式不符")
        out += items
        if len(items) < 100:
            return out
    raise ApiError(f"GET {path} 超過 100 頁")


def first_line(body):
    return (body or "").split("\n", 1)[0].strip()


def output(key, value):
    value = str(value)
    if "\n" in value or "\r" in value:
        raise SystemExit("::error::output 不得含換行")
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")
    print(f"output {key}={value}")


def stop(reason):
    print(f"不派：{reason}")
    output("go", "false")
    output("stop_reason", reason)
    return 0


def parse_task(line):
    """回傳 (params, invalid_reason, foreign_model)；只看第一行。"""
    caps = CAP_RE.findall(line)
    if not caps:
        return None, "第一行沒有「上限 US$N」", None
    cap = caps[0]
    if len(set(caps)) > 1:
        return None, f"第一行有多個不同的上限（{'、'.join(caps)}）", None
    if not re.fullmatch(r"[0-9]{1,2}(\.[0-9]{1,2})?", cap) or not (0 < float(cap) <= 30):
        return None, f"上限 US${cap} 不在 0 到 30 之間（派工的上限不得超過 US$30）", None
    m = BASE_IN_LINE.search(line)
    base = m.group(1).strip() if m else "main"
    if (not BASE_RE.fullmatch(base) or ".." in base or "//" in base
            or base.endswith(("/", ".lock", "."))):
        return None, "起始分支的格式不是本 repo 的分支名", None
    m = MODEL_IN_LINE.search(line)
    model = DEFAULT_MODEL
    if m:
        if m.group(1) not in MODELS:
            return None, None, m.group(1)
        model = m.group(1)
    return {"max_budget_usd": cap, "base_ref": base, "model": model}, None, None


def claim(args):
    env = os.environ
    repo, issue = env["GITHUB_REPOSITORY"], env["TASK_ISSUE"]
    if not re.fullmatch(r"[1-9][0-9]{0,6}", issue):
        print("::error::TASK_ISSUE 必須是正整數", file=sys.stderr)
        return 1
    if not 1 <= args.slot <= MAX_SLOTS:
        print("::error::slot 超出 1–6", file=sys.stderr)
        return 1
    max_tasks = (env.get("MAX_TASKS") or str(MAX_SLOTS)).strip()
    if not re.fullmatch(r"[1-6]", max_tasks):
        print("::error::max_tasks 必須是 1 到 6", file=sys.stderr)
        return 1
    event = env.get("EVENT_NAME", "")
    dry = (env.get("DRY_RUN") or "").lower() == "true"
    output("task_issue", issue)
    if args.slot > int(max_tasks):
        return stop(f"已達本次上限 {max_tasks} 件")

    owner_login, owner_id = env["OWNER_LOGIN"].lower(), env["OWNER_ID"]

    def is_owner(u):
        u = u or {}
        return (str(u.get("id")) == owner_id and str(u.get("login", "")).lower() == owner_login
                and u.get("type") == "User")

    def is_bot(u):
        u = u or {}
        return u.get("login") == BOT_LOGIN and str(u.get("id")) == BOT_ID and u.get("type") == "Bot"

    comments = list_all(f"/repos/{repo}/issues/{issue}/comments")
    result_re = re.compile(r"^【(OpenAI|API) worker】任務留言 ([1-9][0-9]{0,12})（#" + issue + r"）")
    marker_re = re.compile(r"^【OpenAI 派工】任務留言 ([1-9][0-9]{0,12})（#" + issue + r"）")
    handled, tasks, latest_openai = {}, [], None
    for c in comments:
        line, user = first_line(c.get("body")), c.get("user")
        m = result_re.match(line)
        if m and (is_bot(user) or is_owner(user)):
            handled.setdefault(m.group(2), f"已有【{m.group(1)} worker】結果 {c.get('id')}")
            if m.group(1) == "OpenAI" and is_bot(user):
                key = (str(c.get("created_at", "")), int(c.get("id") or 0))
                if latest_openai is None or key > latest_openai[0]:
                    latest_openai = (key, c)
            continue
        m = marker_re.match(line)
        if m and is_bot(user):
            handled.setdefault(m.group(1), f"已有派工標記 {c.get('id')}")
            continue
        if line.startswith("【任務"):
            if is_owner(user):
                tasks.append(c)
            else:
                print(f"略過非擁有者的任務形留言 {c.get('id')}（作者 {(user or {}).get('login', '未知')}，未讀內文）")

    # 點數用完：schedule 一律停；手動觸發只有第 1 件可越過。
    if latest_openai and CREDIT_LINE.search(latest_openai[1].get("body") or ""):
        cid = latest_openai[1].get("id")
        if event != "workflow_dispatch" or args.slot > 1:
            return stop(f"最新的 OpenAI worker 結果 {cid} 是點數用完（credit_balance_exhausted），整批停止")
        print(f"最新的 OpenAI worker 結果 {cid} 是點數用完；擁有者手動觸發，第 1 件照派（視為點數已恢復）")

    busy = set()
    for wf in ("openai-worker.yml", "api-worker.yml"):
        for status in ACTIVE:
            runs = list_all(f"/repos/{repo}/actions/workflows/{wf}/runs?status={status}", "workflow_runs")
            for r in runs:
                title = str(r.get("display_title") or "")
                m = re.fullmatch(r"OpenAI worker 任務留言 ([1-9][0-9]{0,12})", title)
                if wf == "openai-worker.yml" and m:
                    busy.add(m.group(1))
                    continue
                return stop(f"{wf} 有執行中的 run {r.get('id')}（{status}），看不出是哪件任務，這輪不派以免重複")

    tasks.sort(key=lambda c: int(c.get("id") or 0))
    pending = []
    for c in tasks:
        cid = str(c.get("id"))
        if cid in handled:
            continue
        if cid in busy:
            print(f"任務 {cid} 的 openai-worker run 正在執行，跳過")
            continue
        pending.append(c)
    print(f"任務 {len(tasks)} 件；已處理 {sum(1 for c in tasks if str(c.get('id')) in handled)} 件；"
          f"執行中 {len(busy)} 件；待派 {len(pending)} 件")

    run_url = env.get("RUN_URL", "")
    for c in pending:
        cid, line = str(c.get("id")), first_line(c.get("body"))
        params, invalid, foreign = parse_task(line)
        if foreign:
            print(f"任務 {cid} 指定模型 {foreign}（不在 OpenAI worker 白名單），留給其他 worker，不派")
            continue
        if invalid:
            print(f"任務 {cid} 不派工：{invalid}")
            if dry:
                continue
            body = (f"【OpenAI 派工】任務留言 {cid}（#{issue}）\n\n"
                    f"**不派工**：{invalid}。\n\n"
                    f"排程派工之後不會再看這則任務；要執行請改好第一行後另發一則任務留言，或手動觸發 openai-worker。\n\n"
                    f"派工 run：{run_url}")
            api("POST", f"/repos/{repo}/issues/{issue}/comments", {"body": body})
            continue
        if dry:
            print(f"（試跑）第 {args.slot} 件會派任務 {cid}：{json.dumps(params, ensure_ascii=False)}")
            return stop("試跑（dry_run），不貼標記、不派")
        body = (f"【OpenAI 派工】任務留言 {cid}（#{issue}）\n\n"
                f"排程派工已把這則任務交給 OpenAI worker（本批第 {args.slot} 件）："
                f"上限 US${params['max_budget_usd']}、起始分支 `{params['base_ref']}`、模型 `{params['model']}`。\n"
                f"結果會以【OpenAI worker】留言貼回。這則標記表示任務已派出：之後不會再自動派，"
                f"失敗或未推送也不重試；要重做請另發任務留言或手動觸發 openai-worker。\n\n"
                f"派工 run：{run_url}")
        status, _ = api("POST", f"/repos/{repo}/issues/{issue}/comments", {"body": body})
        if status != 201:
            raise ApiError(f"派工標記回應 HTTP {status}")
        print(f"第 {args.slot} 件：派任務 {cid}")
        output("go", "true")
        output("comment_id", cid)
        output("base_ref", params["base_ref"])
        output("max_budget_usd", params["max_budget_usd"])
        output("model", params["model"])
        return 0
    return stop("沒有待派的任務")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("claim")
    c.add_argument("--slot", type=int, required=True)
    args = ap.parse_args()
    try:
        return claim(args)
    except ApiError as e:
        print(f"::error::GitHub API 失敗，這件不派：{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
