#!/usr/bin/env python3
"""openai-dispatch.yml × openai-worker.yml 的本機重演。

- job 圖、if 條件、env／with／outputs 都照 YAML 原文以 ghexpr 求值（含 workflow_call 時 github context 屬於呼叫端）。
- 真的執行：派工 gate step、claim step（openai_dispatch.py）、worker prepare step、report 兩個 step 的原文 run 腳本；
  worker 模型 step 新增的 end_reason 段落原文；push step 的分支名核對那一行原文。
- 以模擬代替：checkout、artifact 上傳／下載（名稱照 YAML 求值，重名就失敗，與 upload-artifact v4 相同）、
  work job 的隔離與安裝（改為直接以真 openai SDK 3.56.0 跑 openai_agent.py，連假 Responses API）、
  push job 的其他檢查（假模型不 commit，一律視為「沒有 commit」拒推）。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ghexpr  # noqa: E402
import fakes   # noqa: E402

AGENT_PY = "/tmp/claude-0/oaivenv/bin/python"


def load(path):
    with open(path, encoding="utf-8") as f:
        doc = yaml.load(f, Loader=yaml.BaseLoader)  # BaseLoader：全部當字串，避免 on: 被轉成 True
    return doc


def parse_outputs(path):
    out = {}
    if not os.path.exists(path):
        return out
    lines = open(path, encoding="utf-8").read().split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^([A-Za-z0-9_-]+)<<(.+)$", ln)
        if m:
            key, delim, buf = m.group(1), m.group(2), []
            i += 1
            while i < len(lines) and lines[i] != delim:
                buf.append(lines[i]); i += 1
            out[key] = "\n".join(buf)
        elif "=" in ln:
            k, v = ln.split("=", 1)
            out[k] = v
        i += 1
    return out


class Sim:
    def __init__(self, root, dispatch_yml, worker_yml, gh, gh_url, oa, oa_url, log):
        self.root, self.gh, self.gh_url, self.oa, self.oa_url = root, gh, gh_url, oa, oa_url
        self.dispatch = load(dispatch_yml) if dispatch_yml else None
        self.worker = load(worker_yml)
        self.log = log
        self.tmp = tempfile.mkdtemp(prefix="replay-", dir="/tmp/claude-0")

    def say(self, *a):
        msg = " ".join(str(x) for x in a)
        self.log.append(msg)
        print(msg)

    def base_env(self, github, temp):
        env = {k: v for k, v in os.environ.items() if k in ("HOME", "LANG", "LC_ALL", "TERM")}
        env.update(PATH=f"{HERE}/bin:/usr/bin:/bin", RUNNER_TEMP=temp, GITHUB_REPOSITORY=fakes.REPO,
                   GITHUB_RUN_ID=str(github["run_id"]), GITHUB_SERVER_URL="https://github.com",
                   GITHUB_API_URL=self.gh_url, FAKE_GH_URL=self.gh_url, GITHUB_SHA=github["sha"],
                   NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost", LANG="C.UTF-8")
        return env

    def run_bash(self, script, env, cwd, label):
        out_file = os.path.join(env["RUNNER_TEMP"], f"out-{abs(hash(label))}")
        open(out_file, "w").close()
        env = dict(env, GITHUB_OUTPUT=out_file)
        sf = os.path.join(env["RUNNER_TEMP"], "step.sh")
        with open(sf, "w", encoding="utf-8") as f:
            f.write(script)
        p = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", sf], env=env, cwd=cwd,
                           capture_output=True, text=True)
        text = (p.stdout + p.stderr).rstrip()
        self.say(f"  ┌ step {label} → exit {p.returncode}")
        for ln in text.split("\n")[-25:]:
            if ln.strip():
                self.say(f"  │ {ln}")
        return p.returncode, parse_outputs(out_file)

    # ---------- 派工 workflow ----------
    def run_dispatch(self, github, inputs):
        jobs = self.dispatch["jobs"]
        res = {}
        ctx_base = {"github": github, "inputs": inputs, "secrets": {"OPENAI_API_KEY": "sk-fake-replay-key-not-real"}}
        for name, job in jobs.items():
            needs = job.get("needs", [])
            needs = [needs] if isinstance(needs, str) else needs
            needs_ctx = {n: {"result": res[n]["result"], "outputs": res[n]["outputs"]} for n in needs}
            ctx = ghexpr.Ctx(dict(ctx_base, needs=needs_ctx), {"needs": [res[n]["result"] for n in needs]})
            if not ghexpr.eval_if(job.get("if"), ctx):
                res[name] = {"result": "skipped", "outputs": {}}
                continue
            self.say(f"[dispatch] job {name}")
            if "uses" in job:
                with_ = {k: ghexpr.render(v, ctx) for k, v in (job.get("with") or {}).items()}
                secrets = {k: ghexpr.render(v, ctx) for k, v in (job.get("secrets") or {}).items()}
                result, outputs = self.run_worker(github, with_, secrets, called=True)
                res[name] = {"result": result, "outputs": outputs}
                self.say(f"[dispatch] job {name} → {result} outputs={json.dumps(outputs, ensure_ascii=False)}")
                continue
            temp = tempfile.mkdtemp(dir=self.tmp)
            steps_ctx, failed = {}, False
            for st in job["steps"]:
                if "uses" in st:
                    continue  # checkout：重演直接用工作樹
                sctx = ghexpr.Ctx(dict(ctx_base, needs=needs_ctx, steps=steps_ctx, runner={"temp": temp}))
                env = self.base_env(github, temp)
                env.update({k: ghexpr.render(v, sctx) for k, v in (st.get("env") or {}).items()})
                rc, outs = self.run_bash(ghexpr.render(st["run"], sctx), env, self.root, f"{name}/{st.get('name')}")
                if st.get("id"):
                    steps_ctx[st["id"]] = {"outputs": outs, "outcome": "success" if rc == 0 else "failure"}
                if rc != 0:
                    failed = True
                    break
            octx = ghexpr.Ctx(dict(ctx_base, steps=steps_ctx))
            outputs = {k: ghexpr.render(v, octx) for k, v in (job.get("outputs") or {}).items()}
            res[name] = {"result": "failure" if failed else "success", "outputs": outputs}
        return res

    # ---------- worker（workflow_call 或 workflow_dispatch） ----------
    def run_worker(self, github, inputs, secrets, called):
        wf = self.worker
        on = wf.get("on", {})
        if called and "workflow_call" not in on:
            self.say("  worker：沒有 on.workflow_call，GitHub 會拒絕這個呼叫（呼叫端 job 失敗）")
            return "failure", {}
        if called:
            decl = on["workflow_call"].get("inputs", {})
            inputs = {k: inputs.get(k, (v or {}).get("default")) for k, v in decl.items()}
        ctx0 = {"github": github, "inputs": inputs, "secrets": secrets}
        wenv = {k: ghexpr.render(v, ghexpr.Ctx(ctx0)) for k, v in (wf.get("env") or {}).items()}
        self.say(f"  worker inputs={json.dumps(inputs, ensure_ascii=False)} WORKER_BRANCH={wenv.get('WORKER_BRANCH')}")
        run_id = str(github["run_id"])
        arts = self.gh.artifacts.setdefault(run_id, [])
        store = os.path.join(self.tmp, "artifacts", run_id)
        jobs, res = wf["jobs"], {}

        def upload(name, src):
            if any(a["name"] == name for a in arts):
                self.say(f"  ✗ upload-artifact：同一個 run 已有名為 {name} 的 artifact（v4 會失敗）")
                return False
            dst = os.path.join(store, name)
            shutil.rmtree(dst, ignore_errors=True)  # 先前同名的已被刪除（v4 刪除後名稱可再用）
            shutil.copytree(src, dst)
            self.gh.next_id += 1
            arts.append({"id": self.gh.next_id, "name": name})
            self.say(f"  upload-artifact {name}")
            return True

        def download(name, dst):
            src = os.path.join(store, name)
            if not any(a["name"] == name for a in arts) or not os.path.isdir(src):
                self.say(f"  download-artifact {name}：不存在")
                return False
            shutil.copytree(src, dst, dirs_exist_ok=True)
            return True

        for name, job in jobs.items():
            needs = job.get("needs", [])
            needs = [needs] if isinstance(needs, str) else needs
            needs_ctx = {n: {"result": res[n]["result"], "outputs": res[n]["outputs"]} for n in needs}
            ctx = ghexpr.Ctx(dict(ctx0, needs=needs_ctx, env=wenv), {"needs": [res[n]["result"] for n in needs]})
            if not ghexpr.eval_if(job.get("if"), ctx):
                res[name] = {"result": "skipped", "outputs": {}}
                self.say(f"  worker job {name}：skipped")
                continue
            temp = tempfile.mkdtemp(dir=self.tmp)
            jenv = dict(wenv)
            jctx = ghexpr.Ctx(dict(ctx0, needs=needs_ctx, env=wenv, runner={"temp": temp}))
            jenv.update({k: ghexpr.render(v, jctx) for k, v in (job.get("env") or {}).items()})
            steps_ctx, failed = {}, False
            getattr(self, f"job_{name}")(job, ctx0, needs_ctx, jenv, temp, steps_ctx, upload, download)
            failed = any(s.get("outcome") == "failure" and not s.get("continue") for s in steps_ctx.values())
            octx = ghexpr.Ctx(dict(ctx0, steps=steps_ctx))
            outputs = {k: ghexpr.render(v, octx) for k, v in (job.get("outputs") or {}).items()}
            res[name] = {"result": "failure" if failed else "success", "outputs": outputs}
            self.say(f"  worker job {name} → {res[name]['result']}")
        result = "failure" if any(r["result"] == "failure" for r in res.values()) else "success"
        outputs = {}
        if called:
            jobs_ctx = {n: {"result": r["result"], "outputs": r["outputs"]} for n, r in res.items()}
            for k, v in (on["workflow_call"].get("outputs") or {}).items():
                outputs[k] = ghexpr.render(v["value"], ghexpr.Ctx(dict(ctx0, jobs=jobs_ctx)))
        return result, outputs

    def step(self, job, sid=None, name_prefix=None):
        for st in job["steps"]:
            if (sid and st.get("id") == sid) or (name_prefix and str(st.get("name", "")).startswith(name_prefix)):
                return st
        raise KeyError(sid or name_prefix)

    def exec_step(self, st, ctx0, needs_ctx, jenv, temp, steps_ctx, label, script=None, key=None):
        sctx = ghexpr.Ctx(dict(ctx0, needs=needs_ctx, env=jenv, steps=steps_ctx, runner={"temp": temp}))
        github = ctx0["github"]
        env = self.base_env(github, temp)
        env.update(jenv)
        env.update({k: ghexpr.render(v, sctx) for k, v in (st.get("env") or {}).items()})
        rc, outs = self.run_bash(script if script is not None else ghexpr.render(st["run"], sctx), env, temp, label)
        steps_ctx[key or st.get("id") or label] = {"outputs": outs, "outcome": "success" if rc == 0 else "failure"}
        return rc, outs

    def job_prepare(self, job, ctx0, needs_ctx, jenv, temp, steps_ctx, upload, download):
        st = self.step(job, sid="task")
        rc, _ = self.exec_step(st, ctx0, needs_ctx, jenv, temp, steps_ctx, "prepare/validate")
        if rc != 0:
            return
        up = job["steps"][1]
        sctx = ghexpr.Ctx(dict(ctx0, steps=steps_ctx, runner={"temp": temp}))
        ok = upload(ghexpr.render(up["with"]["name"], sctx), os.path.join(temp, "task"))
        steps_ctx["upload"] = {"outputs": {}, "outcome": "success" if ok else "failure"}

    def job_work(self, job, ctx0, needs_ctx, jenv, temp, steps_ctx, upload, download):
        sctx = ghexpr.Ctx(dict(ctx0, needs=needs_ctx, runner={"temp": temp}))
        dl = self.step(job, name_prefix="Receive the validated task")
        if not download(ghexpr.render(dl["with"]["name"], sctx), os.path.join(temp, "task")):
            steps_ctx["download"] = {"outputs": {}, "outcome": "failure"}
            return
        model = needs_ctx["prepare"]["outputs"].get("model")
        budget = needs_ctx["prepare"]["outputs"].get("max_budget_usd")
        out = os.path.join(temp, "worker-out")
        os.makedirs(out)
        wd = tempfile.mkdtemp(dir=temp)
        open(os.path.join(out, "cli-started"), "w").write("2026-11-28T12:00:00Z\n")
        env = {"PATH": "/usr/bin:/bin", "HOME": temp, "LANG": "C.UTF-8", "OPENAI_API_KEY": ctx0["secrets"].get("OPENAI_API_KEY", ""),
               "OPENAI_BASE_URL": self.oa_url + "/v1", "NO_PROXY": "127.0.0.1", "no_proxy": "127.0.0.1"}
        agent = os.path.join(self.root, ".github/scripts/openai_agent.py")
        before = self.oa.requests
        p = subprocess.run([AGENT_PY, "-I", agent, "--mode", "worker", "--workdir", wd, "--model", model, "--effort", "high",
                            "--max-turns", "300", "--max-budget-usd", budget, "--time-limit-sec", "8400"],
                           input="重演任務：不要改檔，直接回報。", env=env, capture_output=True, text=True)
        open(os.path.join(out, "result.json"), "w").write(p.stdout)
        open(os.path.join(out, "cli-exit"), "w").write(f"{p.returncode}\n")
        open(os.path.join(out, "cleanup-ok"), "w").write("ok\n")
        open(os.path.join(out, "bundle-status"), "w").write("no-commits\n")
        try:
            r = json.loads(p.stdout)
        except ValueError:
            r = {}
        self.say(f"  [work] openai_agent.py（真 SDK、假 Responses API）exit {p.returncode} end_reason={r.get('end_reason')} "
                 f"api_calls={r.get('api_calls')} 假 API 本次收到 {self.oa.requests - before} 個請求")
        model_step = self.step(job, sid="model")
        snippet = re.search(r"(?ms)^\s*# 給派工的 end_reason.*?>> \"\$GITHUB_OUTPUT\"\n", model_step["run"])
        if snippet:
            text = "set -euo pipefail\nout=\"$RUNNER_TEMP/worker-out\"\n" + snippet.group(0)
            self.exec_step(model_step, ctx0, needs_ctx, jenv, temp, steps_ctx, "work/end_reason 段落（原文）", script=text, key="model")
        else:
            steps_ctx["model"] = {"outputs": {}, "outcome": "success"}
            self.say("  [work] 模型 step 沒有 end_reason 輸出段落")
        up = job["steps"][-1]
        ok = upload(ghexpr.render(up["with"]["name"], sctx), out)
        steps_ctx["upload"] = {"outputs": {}, "outcome": "success" if ok else "failure"}

    def job_push(self, job, ctx0, needs_ctx, jenv, temp, steps_ctx, upload, download):
        sctx = ghexpr.Ctx(dict(ctx0, needs=needs_ctx, runner={"temp": temp}))
        dl = self.step(job, sid="fetch")
        got = download(ghexpr.render(dl["with"]["name"], sctx), os.path.join(temp, "worker-out"))
        steps_ctx["fetch"] = {"outputs": {}, "outcome": "success" if got else "failure", "continue": True}
        push = self.step(job, sid="push")
        line = next((ln for ln in push["run"].split("\n") if "WORKER_BRANCH" in ln and ("=~" in ln or "case" in ln)), None)
        rc, _ = self.exec_step(push, ctx0, needs_ctx, jenv, temp, {}, "push/分支名核對（原文那一行）",
                               script=f"set -euo pipefail\n{line}\necho branch-ok \"$WORKER_BRANCH\"\n", key="branchcheck")
        steps_ctx["check"] = {"outputs": {"ok": "false", "reasons": json.dumps(["模型沒有 commit（重演：push job 其他檢查以模擬代替）"], ensure_ascii=False),
                                          "commits": "0", "files": "0"}, "outcome": "failure"}
        self.say("  [push] 模擬：假模型沒有 commit → 固定檢查拒推")

    def job_report(self, job, ctx0, needs_ctx, jenv, temp, steps_ctx, upload, download):
        sctx = ghexpr.Ctx(dict(ctx0, needs=needs_ctx, runner={"temp": temp}))
        dl = self.step(job, sid="fetch")
        if needs_ctx["prepare"]["result"] == "success":
            got = download(ghexpr.render(dl["with"]["name"], sctx), os.path.join(temp, "worker-out"))
            steps_ctx["fetch"] = {"outputs": {}, "outcome": "success" if got else "failure", "continue": True}
        post = self.step(job, name_prefix="Post one")
        self.exec_step(post, ctx0, needs_ctx, jenv, temp, steps_ctx, "report/Post one 【OpenAI worker】 comment（原文）", key="post")
        delete = self.step(job, name_prefix="Delete this run")
        self.exec_step(delete, ctx0, needs_ctx, jenv, temp, steps_ctx, "report/Delete artifacts（原文）", key="delete")
        # 留言 step 的 exit 2＝已留言但未推送（job 失敗），與真 runner 相同。
