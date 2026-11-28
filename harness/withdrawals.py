#!/usr/bin/env python3
"""具名撤回：把某一道防線從原文拿掉（複製一份 root 再改），跑對應情境，預期該情境轉紅。"""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(sys.argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
D = ".github/scripts/openai_dispatch.py"
DY = ".github/workflows/openai-dispatch.yml"
W = ".github/workflows/openai-worker.yml"

WREF_CLAUSE = """      ((github.event_name == 'workflow_dispatch' &&
        github.workflow_ref == format('{0}/.github/workflows/openai-worker.yml@refs/heads/main', github.repository)) ||
       ((github.event_name == 'schedule' || github.event_name == 'workflow_dispatch') &&
        github.workflow_ref == format('{0}/.github/workflows/openai-dispatch.yml@refs/heads/main', github.repository)))"""

W_LIST = [
    ("DISPATCH_OWNER_TASK_CHECK_REMOVED", [(D, "            if is_owner(user):\n                tasks.append(c)", "            if True:\n                tasks.append(c)", 1)], ["non-owner"]),
    ("DISPATCH_TRUSTED_RESULT_AUTHOR_REMOVED", [(D, "if m and (is_bot(user) or is_owner(user)):", "if m:", 1),
                                                (D, "if m and is_bot(user):\n            handled", "if m:\n            handled", 1)], ["non-owner"]),
    ("DISPATCH_CAP30_REMOVED", [(D, "not (0 < float(cap) <= 30)", "not (0 < float(cap))", 1),
                                (D, 'r"[0-9]{1,2}(\\.[0-9]{1,2})?"', 'r"[0-9]{1,4}(\\.[0-9]{1,2})?"', 1)], ["cap"]),
    ("DISPATCH_HANDLED_REMOVED", [(D, "        if cid in handled:\n            continue\n", "", 1)], ["all-done"]),
    ("DISPATCH_CREDIT_HALT_REMOVED", [(D, "        if event != \"workflow_dispatch\" or args.slot > 1:", "        if False:", 1)], ["credit"]),
    ("DISPATCH_CREDIT_HALT_AND_YAML_STOP_REMOVED", [(D, "        if event != \"workflow_dispatch\" or args.slot > 1:", "        if False:", 1)]
     + [(DY, f" &&\n      needs.run{n}.outputs.end_reason != 'credit_balance_exhausted'", "", 1) for n in range(1, 6)], ["credit"]),
    ("WORKER_WORKFLOW_REF_CHECK_REMOVED", [(W, WREF_CLAUSE, "      (github.event_name == 'workflow_dispatch' || github.event_name == 'schedule')", 4)], ["triggers"]),
    ("WORKER_OWNER_IF_LEFT_AS_DISPATCH_ONLY", [(W, WREF_CLAUSE, "      github.event_name == 'workflow_dispatch'", 4)], ["pending"]),
    ("WORKER_BRANCH_AND_ARTIFACT_SUFFIX_REMOVED", [
        (W, "${{ contains(github.workflow_ref, '/.github/workflows/openai-dispatch.yml@') && format('openaiworker/{0}-{1}', github.run_id, inputs.task_comment_id) || format('openaiworker/{0}', github.run_id) }}",
         "openaiworker/${{ github.run_id }}", 1),
        (W, "openai-worker-task-${{ steps.task.outputs.comment_id }}", "openai-worker-task", 1),
        (W, "openai-worker-task-${{ needs.prepare.outputs.comment_id }}", "openai-worker-task", 2),
        (W, "openai-worker-output-${{ needs.prepare.outputs.comment_id }}", "openai-worker-output", 4)], ["pending"]),
    ("WORKER_END_REASON_OUTPUT_REMOVED_ALONE（預期仍綠：claim 端的留言檢查補上）", [
        (W, "          [[ \"$reason\" =~ ^[a-z_]{1,40}$ ]] || reason=\"\"\n", "          reason=\"\"\n", 1)], ["credit"]),
    ("WORKER_END_REASON_OUTPUT_REMOVED_AND_DISPATCH_CREDIT_HALT_REMOVED", [
        (W, "          [[ \"$reason\" =~ ^[a-z_]{1,40}$ ]] || reason=\"\"\n", "          reason=\"\"\n", 1),
        (D, "        if event != \"workflow_dispatch\" or args.slot > 1:", "        if False:", 1)], ["credit"]),
]

only = sys.argv[2:]
for name, edits, scen in W_LIST:
    if only and name not in only:
        continue
    tmp = tempfile.mkdtemp(prefix="wd-", dir="/tmp/claude-0")
    shutil.copytree(os.path.join(ROOT, ".github"), os.path.join(tmp, ".github"))
    for path, old, new, count in edits:
        p = os.path.join(tmp, path)
        s = open(p, encoding="utf-8").read()
        n = s.count(old)
        assert n == count, f"{name}: {path} 的替換目標出現 {n} 次（預期 {count}）"
        open(p, "w", encoding="utf-8").write(s.replace(old, new))
    env = {k: v for k, v in os.environ.items() if k.lower() not in ("https_proxy", "http_proxy")}
    p = subprocess.run([sys.executable, os.path.join(HERE, "scenarios.py"), tmp] + scen, capture_output=True, text=True, env=env)
    log = os.path.join("/tmp/claude-0/withdrawals", f"{name}.log")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    open(log, "w").write(p.stdout + p.stderr)
    fails = [ln for ln in p.stdout.split("\n") if ln.startswith("FAIL")]
    summ = [ln for ln in p.stdout.split("\n") if ln.startswith("PASS ") and "／" in ln]
    print(f"=== {name}（情境 {', '.join(scen)}）exit {p.returncode}；{summ[-1] if summ else '無摘要'}")
    for ln in fails:
        print("   " + ln)
    shutil.rmtree(tmp)
