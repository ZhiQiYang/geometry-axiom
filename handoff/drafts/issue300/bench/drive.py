#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""issue #300 微基準的量測驅動程式(由 bench.sh 呼叫;也可單獨用)。

只用標準函式庫。它對「已經編好的 bridge」說話(stdin 一行一個指令、stdout 一行一個 JSON,見 geometry-web/web_bridge.c),
在用戶端量每個指令的牆鐘時間;bridge 的 CPU 時間與峰值 RSS 另從 /proc/<pid> 盡力讀取。

子指令:
  worldbytes  各容量的 bridge 回報的 sizeof(World)(section-profile-read 的 nativeBytes.world)
  sanity      先驗證:已知良好場景、產生器場景、容量 64 拒第 65 支 / 容量 512 收第 65 支。失敗回 3,不該繼續量。
  run         主量測:每個 (家族, N, 容量) 一個 unit;每個 unit 重複 reps 次,每次一個新的 bridge 行程:
                loadfile 整份場景 -> line-grid x3 -> (line-delete, line-timber, line-place) x2
              可續跑(TSV 已有的 unit 不重做)、有預算(超過就延後)、有逾時。
  stack       堆疊上限階梯:對各工作負載以 ulimit -S -s <KiB> 由大到小跑,找最小可通過的堆疊
  status      列出 TSV 目前涵蓋的 unit
  selftest    用內建的假 bridge 驗證本程式自己(秒級,純 Python)

TSV 欄位(前五欄即題目要求的 N、容量、指令類型、秒數、rc):
  N  cap  kind  seconds  rc  family  rep  cpu_s  rss_kb  stack_kib  note
  rc: 0 成功;1 bridge 回 ok:false(被拒);2 協定錯誤(輸出不是 JSON / 提早 EOF 但不是訊號);
      124 單一指令超過 --run-timeout;125 被本次預算的硬期限打斷(下次會重做,不算完成);3 sanity 結果與預期不符;
      負數 = 行程被該訊號殺死(-11 = SIGSEGV,堆疊不夠時的典型症狀);126 = ulimit 設不上去。
"""
from __future__ import print_function

import argparse
import hashlib
import json
import math
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import gen_scene  # noqa: E402

COLS = ["N", "cap", "kind", "seconds", "rc", "family", "rep", "cpu_s", "rss_kb", "stack_kib", "note"]
T0 = time.time()
RC_TIMEOUT, RC_HARD, RC_SANITY = 124, 125, 3
LF = chr(10)
LINE_KINDS = ("line-grid", "line-delete", "line-timber", "line-place")


def log(msg):
    print("[drive +%4ds] %s" % (time.time() - T0, msg), file=sys.stderr)
    sys.stderr.flush()


# --------------------------------------------------------------------------------------- TSV

def _clean(text):
    return re.sub(r"[\t\r\n]+", " ", str(text))[:300]


class Tsv(object):
    def __init__(self, path):
        self.path = path
        d = os.path.dirname(os.path.abspath(path))
        if d:
            os.makedirs(d, exist_ok=True)
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\t".join(COLS) + "\n")

    def append(self, **row):
        vals = []
        for c in COLS:
            v = row.get(c, "")
            if v is None:
                v = ""
            if c in ("seconds", "cpu_s") and v != "":
                v = "%.6f" % float(v)
            vals.append(_clean(v))
        with open(self.path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\t".join(vals) + "\n")
            fh.flush()

    def rows(self):
        out = []
        if not os.path.exists(self.path):
            return out
        with open(self.path, "r", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.rstrip("\n")
                if not ln or ln.startswith("#") or ln.startswith("N\t"):
                    continue
                parts = ln.split("\t")
                parts += [""] * (len(COLS) - len(parts))
                d = dict(zip(COLS, parts))
                try:
                    d["N"] = int(d["N"])
                    d["cap"] = int(d["cap"])
                    d["seconds"] = float(d["seconds"]) if d["seconds"] != "" else 0.0
                    d["rc"] = int(d["rc"])
                    d["rep"] = int(d["rep"]) if d["rep"] != "" else 0
                    d["stack_kib"] = int(d["stack_kib"]) if d["stack_kib"] != "" else 0
                except ValueError:
                    continue
                out.append(d)
        return out


# --------------------------------------------------------------------------------------- bridge 行程

_SETPRIV = []


def _setpriv_prefix():
    """setpriv --pdeathsig KILL:父行程(本程式)死掉時 bridge 跟著死,避免殘留行程。可用才用。"""
    if not _SETPRIV:
        ok = False
        if os.name == "posix" and shutil.which("setpriv"):
            try:
                ok = subprocess.call(["setpriv", "--pdeathsig", "KILL", "true"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
            except OSError:
                ok = False
        _SETPRIV.append(["setpriv", "--pdeathsig", "KILL"] if ok else [])
    return _SETPRIV[0]


class Bridge(object):
    """一個 bridge 行程。argv 是 list;stack_kib 不為 None 時用 `ulimit -S -s` 包起來(與 CI 的 ulimit -s 16384 同義)。"""

    def __init__(self, argv, env=None, stack_kib=None, cpu=None):
        full = []
        if os.name == "posix":
            full += _setpriv_prefix()
            if cpu is not None and shutil.which("taskset"):
                full += ["taskset", "-c", str(cpu)]
            if stack_kib is not None:
                # ulimit -c 0:堆疊不夠時 bridge 會 SIGSEGV,別讓它在 WSL 留下大型 core 檔。
                full += ["bash", "-c", 'ulimit -c 0 2>/dev/null; ulimit -S -s "$1" || exit 126; shift; exec "$@"',
                         "bench", str(stack_kib)]
        full += list(argv)
        e = dict(os.environ)
        e.update(env or {})
        if stack_kib is not None:
            e["BENCH_STACK_KIB"] = str(stack_kib)
        self.err = tempfile.TemporaryFile()
        self.p = subprocess.Popen(full, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.err, env=e)
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._pump, daemon=True)
        self.t.start()
        self.pid = self.p.pid

    def _pump(self):
        try:
            for line in iter(self.p.stdout.readline, b""):
                self.q.put(line)
        finally:
            self.q.put(None)

    def _cpu_ns(self):
        try:
            with open("/proc/%d/schedstat" % self.pid, "r") as fh:
                return int(fh.read().split()[0])
        except (OSError, ValueError, IndexError):
            return None

    def rss_kb(self):
        try:
            with open("/proc/%d/status" % self.pid, "r") as fh:
                for ln in fh:
                    if ln.startswith("VmHWM:"):
                        return int(ln.split()[1])
        except (OSError, ValueError, IndexError):
            pass
        return None

    def cmd(self, text, timeout):
        """送一行,等一行 JSON。回傳 (status, seconds, resp, cpu_s);status in ok|timeout|eof|badjson。"""
        cpu0 = self._cpu_ns()
        t0 = time.perf_counter()
        try:
            self.p.stdin.write(text.encode("utf-8") + b"\n")
            self.p.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            return "eof", time.perf_counter() - t0, None, None
        try:
            line = self.q.get(timeout=max(0.001, timeout))
        except queue.Empty:
            return "timeout", time.perf_counter() - t0, None, None
        dt = time.perf_counter() - t0
        cpu1 = self._cpu_ns()
        cpu = (cpu1 - cpu0) / 1e9 if (cpu0 is not None and cpu1 is not None) else None
        if line is None:
            return "eof", dt, None, None
        try:
            return "ok", dt, json.loads(line.decode("utf-8", "replace")), cpu
        except ValueError:
            return "badjson", dt, None, cpu

    def exit_code(self, wait=3.0):
        try:
            return self.p.wait(timeout=wait)
        except subprocess.TimeoutExpired:
            return None

    def kill(self):
        try:
            self.p.kill()
        except OSError:
            pass
        try:
            self.p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass

    def stderr_tail(self):
        try:
            self.err.seek(0)
            return self.err.read().decode("utf-8", "replace")[-200:]
        except (OSError, ValueError):
            return ""

    def close(self):
        """關 stdin 讓 bridge 正常結束;回傳結束碼(None = 逾時被殺)。"""
        try:
            self.p.stdin.close()
        except (OSError, ValueError):
            pass
        rc = self.exit_code(30.0)
        if rc is None:
            self.kill()
        try:
            self.err.close()
        except OSError:
            pass
        return rc


# --------------------------------------------------------------------------------------- 執行環境

class Ctx(object):
    def __init__(self, a):
        self.a = a
        self.tsv = Tsv(a.tsv)
        self.fake = bool(a.fake)
        self.caps = [int(x) for x in a.caps.split(",") if x]
        self.run_timeout = float(getattr(a, "run_timeout", 900.0))
        self.until = float(getattr(a, "budget_until", 0) or 0)
        self.hard_extra = float(getattr(a, "hard_extra", 240.0))
        self.cpu = getattr(a, "cpu", None)
        self.force = bool(getattr(a, "force", False))
        self.retry_to = bool(getattr(a, "retry_timeouts", False))
        self.pred_exp = float(getattr(a, "pred_exp", 4.0))

    # 預算
    def soft_left(self):
        return float("inf") if not self.until else self.until - time.time()

    def hard_left(self):
        return float("inf") if not self.until else self.until + self.hard_extra - time.time()

    def cmd_timeout(self):
        return min(self.run_timeout, self.hard_left())

    # 路徑
    def exe(self, cap, name="bridge"):
        if self.fake:
            return [sys.executable, os.path.abspath(__file__), "_fake-bridge"]
        return [os.path.join(self.a.bin_root, "cap%d" % cap, name)]

    def env(self, cap):
        return {"FAKE_CAP": str(cap)} if self.fake else {}

    def scene(self, family, n):
        return gen_scene.write(n, family, self.a.scene_dir)

    def emit(self, n, cap, kind, seconds, rc, family="", rep="", cpu=None, rss=None, stack=None, note=""):
        self.tsv.append(N=n, cap=cap, kind=kind, seconds=seconds, rc=rc, family=family, rep=rep,
                        cpu_s=cpu, rss_kb=rss, stack_kib=stack, note=note)
        log("%-7s N=%-4d cap=%-3d rep=%-2s %-12s %10.4fs rc=%-4s%s%s" % (
            family or "-", n, cap, rep, kind, seconds, rc,
            (" stack=%s" % stack) if stack else "", (" " + note) if note else ""))


def classify(status, resp, bridge, soft_hard_limited):
    """把一次 cmd 的結果換成 rc。"""
    if status == "timeout":
        return RC_HARD if soft_hard_limited else RC_TIMEOUT
    if status == "eof":
        code = bridge.exit_code(2.0)
        return code if (code is not None and code != 0) else 2
    if status == "badjson":
        return 2
    return 0 if resp.get("ok") else 1


def err_note(resp):
    if isinstance(resp, dict) and not resp.get("ok"):
        return "error=" + str(resp.get("error", resp.get("message", "")))[:160]
    return ""


# --------------------------------------------------------------------------------------- worldbytes / sanity

def world_bytes(ctx, cap):
    b = Bridge(ctx.exe(cap), env=ctx.env(cap))
    try:
        st, dt, resp, _ = b.cmd("section-profile-read", 60)
    finally:
        b.close()
    try:
        return int(resp["nativeBytes"]["world"])
    except (TypeError, KeyError, ValueError):
        return None


def cmd_worldbytes(ctx, a):
    rows = ctx.tsv.rows()
    for cap in ctx.caps:
        if any(r["kind"] == "worldbytes" and r["cap"] == cap and r["rc"] == 0 for r in rows):
            continue
        w = world_bytes(ctx, cap)
        ctx.emit(0, cap, "worldbytes", 0, 0 if w else 2, note=("world=%d" % w) if w else "unreadable")
    return 0


def _load_probe(ctx, cap, scene, timeout=300.0):
    b = Bridge(ctx.exe(cap), env=ctx.env(cap))
    st, dt, resp, rss = "eof", 0.0, None, None
    try:
        st, dt, resp, _cpu = b.cmd("loadfile " + scene, timeout)
        rss = b.rss_kb()
    finally:
        if st == "timeout":
            b.kill()
        else:
            b.close()
    return st, dt, resp, rss


def cmd_sanity(ctx, a):
    """回傳 0 全部符合預期;3 有不符(最重要的訊息:產生器場景被核心拒絕)。"""
    bad = []
    calib = os.path.abspath(a.calib)

    def expect(label, n, cap, scene, want_ok, fam="calib", reject_substr="超過上限"):
        st, dt, resp, rss = _load_probe(ctx, cap, scene)
        got_ok = st == "ok" and bool(resp.get("ok"))
        if want_ok:
            good = got_ok
            note = "expect=ok got=%s %s" % ("ok" if got_ok else st, err_note(resp))
        else:
            err = str(resp.get("error", "")) if (st == "ok" and isinstance(resp, dict)) else ""
            good = (st == "ok") and (not got_ok) and (reject_substr in err)
            note = "expect=reject(%s) got=%s %s" % (reject_substr, "ok" if got_ok else st, err_note(resp))
        rc = 0 if good else RC_SANITY
        ctx.emit(n, cap, label, dt, rc, family=fam, rep=0, rss=rss, note=note)
        if not good:
            bad.append("%s cap=%d N=%d: %s" % (label, cap, n, note))

    for cap in ctx.caps:
        expect("sanity-calib", 48, cap, calib, True, fam="calib")
    for n in (16, 32, 48, 64):
        path, _ = ctx.scene("single", n)
        for cap in ctx.caps:
            if n <= cap:
                expect("sanity-gen", n, cap, path, True, fam="single")
    hn = 128
    path, _ = ctx.scene("house", hn)
    for cap in ctx.caps:
        if hn <= cap:
            expect("sanity-gen", hn, cap, path, True, fam="house")
    path, _ = ctx.scene("single", 65)
    for cap in ctx.caps:
        expect("sanity-cap65", 65, cap, path, cap >= 65, fam="single")
    if bad:
        log("SANITY FAILED:")
        for line in bad:
            log("  " + line)
        calib_ok = not any(x.startswith("sanity-calib") for x in bad)
        if calib_ok:
            log("已知良好的 calib 場景通過但產生器場景失敗 => 產生器(gen_scene.py)寫出了核心不接受的句型,不要繼續量。")
        else:
            log("連已知良好的 calib 場景都失敗 => 建置/環境有問題(看 build-cap*.log),不要繼續量。")
        return RC_SANITY
    log("sanity OK (%d checks)" % len([r for r in ctx.tsv.rows() if r["kind"].startswith("sanity")]))
    return 0


# --------------------------------------------------------------------------------------- run

def unit_state(rows, fam, n, cap, reps, cutoff, retry_timeouts=False):
    skip_rc = (RC_HARD, RC_TIMEOUT) if retry_timeouts else (RC_HARD,)     # --retry-timeouts:舊的逾時列保留在 TSV,但不再當作已完成
    loads = [r for r in rows if r["kind"] == "load" and r["family"] == fam and r["N"] == n and r["cap"] == cap
             and r["rc"] not in skip_rc]
    done = len(set(r["rep"] for r in loads))
    if any(r["rc"] in (1, RC_TIMEOUT) or r["rc"] < 0 or r["rc"] == 2 for r in loads):
        return done, True, True        # 場景被拒/逾時/崩潰:確定性結果,不重做
    target = reps
    if any(r["rc"] == 0 and r["seconds"] > cutoff for r in loads):
        target = 1
    return done, done >= target, False


def predict_rep_seconds(rows, fam, cap, n, exp):
    best = None
    for r in rows:
        if r["kind"] == "load" and r["family"] == fam and r["cap"] == cap and r["rc"] == 0 and r["N"] < n:
            if best is None or r["N"] > best["N"] or (r["N"] == best["N"] and r["seconds"] > best["seconds"]):
                best = r
    if best is None:
        return 0.0
    return best["seconds"] * (float(n) / best["N"]) ** exp * 1.15


def run_process(ctx, cap, scene, meta, fam, n, rep):
    """一個 bridge 行程:load + 一組單條指令。回傳 (load_rc, wall_seconds_of_process)。"""
    t_proc = time.perf_counter()
    b = Bridge(ctx.exe(cap), env=ctx.env(cap), cpu=ctx.cpu)
    leaf = meta["leaf"]
    interrupted = False

    def step(kind, text):
        nonlocal interrupted
        left = ctx.hard_left()
        if left <= 1.0:
            interrupted = True
            ctx.emit(n, cap, kind, 0, RC_HARD, family=fam, rep=rep, note="skipped: hard deadline")
            return RC_HARD
        timeout = min(ctx.run_timeout, left)
        limited = left < ctx.run_timeout
        st, dt, resp, cpu = b.cmd(text, timeout)
        rc = classify(st, resp, b, limited)
        ctx.emit(n, cap, kind, dt, rc, family=fam, rep=rep, cpu=cpu, rss=b.rss_kb(), note=err_note(resp) or (
            "sha=" + meta["scene_sha256"][:8] if kind == "load" else ""))
        if rc in (RC_TIMEOUT, RC_HARD):
            b.kill()
            interrupted = True
        return rc

    load_rc = RC_HARD
    try:
        load_rc = step("load", "loadfile " + scene)
        if load_rc == 0:
            for _ in range(3):
                if step("line-grid", "line " + meta["grid_command"]) != 0:
                    break
            if not interrupted:
                for _ in range(2):
                    if step("line-delete", "line " + leaf["delete"]) != 0:
                        break
                    if step("line-timber", "line " + leaf["timber"]) != 0:
                        break
                    if step("line-place", "line " + leaf["place"]) != 0:
                        break
    finally:
        if interrupted:
            b.kill()
            try:
                b.err.close()
            except OSError:
                pass
            code = None
        else:
            code = b.close()
        if code not in (0, None) and not interrupted:
            ctx.emit(n, cap, "exit", 0, code if code else 2, family=fam, rep=rep, note="bridge exit status at EOF")
    return load_rc, time.perf_counter() - t_proc


def run_modelbase(ctx, cap, scene, fam, n, rep):
    exe = ctx.exe(cap, "model-base")
    if not ctx.fake and not os.path.exists(exe[0]):
        ctx.emit(n, cap, "load-modelbase", 0, 2, family=fam, rep=rep, note="model-base binary missing (BENCH_MODEL_BASE=1 at build)")
        return
    timeout = max(1.0, ctx.cmd_timeout())
    t0 = time.perf_counter()
    try:
        p = subprocess.run(exe + [scene], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
                           env=dict(os.environ, **ctx.env(cap)))
        rc = p.returncode
        ok = rc == 0 and b'"ok":true' in p.stdout[:200].replace(b" ", b"")
        rc = 0 if ok else (rc if rc else 1)
    except subprocess.TimeoutExpired:
        rc = RC_TIMEOUT
    ctx.emit(n, cap, "load-modelbase", time.perf_counter() - t0, rc, family=fam, rep=rep)


def cmd_run(ctx, a):
    fams = [x for x in a.families.split(",") if x]
    ns = {"single": sorted(set(int(x) for x in a.ns.split(",") if x)),
          "house": sorted(set(int(x) for x in a.house_ns.split(",") if x))}
    units = []
    for n in sorted(set(ns["single"]) | set(ns["house"])):
        for fam in fams:
            if n not in ns.get(fam, []):
                continue
            for cap in ctx.caps:
                if n <= cap:
                    units.append((fam, n, cap))
    deferred, complete, interrupted = [], 0, False
    for fam, n, cap in units:
        rows = ctx.tsv.rows()
        done, finished, _ = unit_state(rows, fam, n, cap, a.reps, a.rep_cutoff, ctx.retry_to)
        if finished:
            complete += 1
            continue
        scene, meta = ctx.scene(fam, n)
        last_rep_seconds = None
        while True:
            rows = ctx.tsv.rows()
            done, finished, _ = unit_state(rows, fam, n, cap, a.reps, a.rep_cutoff, ctx.retry_to)
            if finished:
                complete += 1
                break
            pred = last_rep_seconds * 1.1 if last_rep_seconds else predict_rep_seconds(rows, fam, cap, n, ctx.pred_exp)
            if not ctx.force and pred > ctx.soft_left():
                log("DEFER %s N=%d cap=%d rep=%d: predicted %.0fs > %.0fs left in this slot" % (
                    fam, n, cap, done + 1, pred, max(0.0, ctx.soft_left())))
                deferred.append((fam, n, cap))
                break
            if ctx.hard_left() <= 1.0:
                interrupted = True
                deferred.append((fam, n, cap))
                break
            rep = done + 1
            load_rc, wall = run_process(ctx, cap, scene, meta, fam, n, rep)
            last_rep_seconds = wall
            if a.model_base and load_rc == 0:
                run_modelbase(ctx, cap, scene, fam, n, rep)
            if load_rc == RC_HARD:
                interrupted = True
                deferred.append((fam, n, cap))
                break
        if interrupted:
            break
    pending = len(deferred)
    log("run finished: %d unit(s) complete, %d deferred%s" % (complete, pending, ", hard deadline hit" if interrupted else ""))
    return 10 if (pending or interrupted) else 0


# --------------------------------------------------------------------------------------- stack

def stack_workloads(ctx, a):
    root = ctx.a.src_root
    wl = {}
    for key, name in (("ax_r13", "_ax_r13_anchor_follows.scene"), ("ax_r10", "_ax_r10_hole_follows_piece.scene"),
                      ("ax_r17", "_ax_r17_wall_column_face.scene")):
        wl[key] = dict(n=0, cmds=[("loadfile " + os.path.join(root, name), True), ("dump", True)])
    path, meta = ctx.scene("single", 64)
    leaf = meta["leaf"]
    wl["gen64"] = dict(n=64, cmds=[
        ("loadfile " + path, True), ("line " + meta["grid_command"], True),
        ("line " + leaf["delete"], True), ("line " + leaf["timber"], True), ("line " + leaf["place"], True),
        ("snap 1 u 0 930 8", False),     # reference_snap 的單一大框架;沒有合法引用時回 ok:false 是正常的,只看有沒有崩潰
        ("dump", True)])
    return wl


def stack_probe(ctx, cap, key, wl, kib, timeout=300.0):
    b = Bridge(ctx.exe(cap), env=ctx.env(cap), stack_kib=kib)
    h = hashlib.sha256()
    rc, note, t0 = 0, "", time.perf_counter()
    killed = False
    try:
        for text, must_ok in wl["cmds"]:
            st, dt, resp, _ = b.cmd(text, timeout)
            if st != "ok":
                rc = classify(st, resp, b, False)
                note = "no reply to: " + text.split(" ")[0] + " " + b.stderr_tail().strip().replace("\n", " ")[:100]
                killed = st == "timeout"
                break
            h.update(json.dumps(resp, sort_keys=True).encode("utf-8"))
            if must_ok and not resp.get("ok"):
                rc, note = 1, err_note(resp)
                break
    finally:
        if killed:
            b.kill()
            code = None
        else:
            code = b.close()
    if rc == 0 and code not in (0,):
        rc = code if code else 1
        note = "exit status %s at EOF" % code
    return rc, time.perf_counter() - t0, (note or "out=" + h.hexdigest()[:10])


class OutOfTime(Exception):
    pass


def cmd_stack(ctx, a):
    try:
        return _cmd_stack(ctx, a)
    except OutOfTime:
        log("stack ladder stopped: not enough time left in this slot (hard deadline); run again to continue")
        return 10


def _cmd_stack(ctx, a):
    rungs = sorted(set(int(x) for x in a.rungs.split(",") if x), reverse=True)
    res = int(a.resolution)
    wls = stack_workloads(ctx, a)
    only = [x for x in a.workloads.split(",") if x] if a.workloads else list(wls)
    summary = []
    for cap in ctx.caps:
        for key in only:
            wl = wls[key]
            known = {}
            for r in ctx.tsv.rows():
                if r["kind"] == "stack:" + key and r["cap"] == cap and r["stack_kib"]:
                    known[r["stack_kib"]] = r["rc"]

            def probe(kib):
                if kib in known:
                    return known[kib]
                left = ctx.hard_left()
                if left < 30:
                    raise OutOfTime()
                rc, dt, note = stack_probe(ctx, cap, key, wl, kib, timeout=min(300.0, left - 10))
                ctx.emit(wl["n"], cap, "stack:" + key, dt, rc, family="stack", rep=0, stack=kib, note=note)
                known[kib] = rc
                return rc

            last_pass, first_fail = None, None
            invalid = False
            for kib in rungs:
                rc = probe(kib)
                if rc == 0:
                    last_pass = kib
                elif rc == 1 and last_pass is None:
                    invalid = True          # 最大堆疊下就回 ok:false:工作負載本身不成立,不是堆疊問題
                    break
                else:
                    first_fail = kib
                    break
            if invalid:
                log("stack workload %s cap=%d answers ok:false even at %d KiB: the workload itself is invalid, not a stack result" % (
                    key, cap, rungs[0]))
                summary.append((cap, key, None, None))
                continue
            if last_pass and first_fail:
                lo, hi = first_fail, last_pass
                while hi - lo > res:
                    mid = ((lo + hi) // 2 // 64) * 64
                    if mid <= lo or mid >= hi:
                        break
                    if probe(mid) == 0:
                        hi = mid
                    else:
                        lo = mid
                summary.append((cap, key, hi, lo))
            elif last_pass:
                summary.append((cap, key, last_pass, None))
            else:
                summary.append((cap, key, None, first_fail))
    log("stack summary (KiB; min pass / max fail):")
    for cap, key, p, f in summary:
        log("  cap=%-3d %-7s min_pass=%s max_fail=%s" % (cap, key, p, f))
    return 0


# --------------------------------------------------------------------------------------- status

def cmd_status(ctx, a):
    rows = ctx.tsv.rows()
    print("%-7s %5s %4s %5s %10s %s" % ("family", "N", "cap", "reps", "med load s", "flags"))
    seen = sorted(set((r["family"], r["N"], r["cap"]) for r in rows if r["kind"] == "load"),
                  key=lambda k: (k[1], k[0], k[2]))
    for fam, n, cap in seen:
        loads = [r for r in rows if r["kind"] == "load" and (r["family"], r["N"], r["cap"]) == (fam, n, cap)]
        good = sorted(r["seconds"] for r in loads if r["rc"] == 0)
        med = good[len(good) // 2] if good else float("nan")
        flags = ",".join(sorted(set("rc%d" % r["rc"] for r in loads if r["rc"] != 0)))
        print("%-7s %5d %4d %5d %10.3f %s" % (fam, n, cap, len(good), med, flags))
    sk = sorted(set((r["cap"], r["kind"]) for r in rows if r["kind"].startswith("stack:")))
    print("stack rows:", ", ".join("cap%d %s" % k for k in sk) or "(none)")
    return 0


# --------------------------------------------------------------------------------------- 假 bridge + selftest

def fake_bridge():
    cap = int(os.environ.get("FAKE_CAP", "512"))
    need = int(os.environ.get("FAKE_NEED_KIB", "11000" if cap > 64 else "5000"))
    kib = os.environ.get("BENCH_STACK_KIB")
    if kib and int(kib) < need:
        os._exit(139)
    load_sleep = float(os.environ.get("FAKE_LOAD_SLEEP", "0"))
    count = 0
    for stream, kw in ((sys.stdin, dict(encoding="utf-8")), (sys.stdout, dict(encoding="utf-8", newline=LF))):
        try:
            stream.reconfigure(**kw)
        except (AttributeError, ValueError):
            pass
    out = sys.stdout
    for line in sys.stdin:
        cmd, _, arg = line.rstrip("\n").partition(" ")
        if cmd == "loadfile":
            try:
                with open(arg, "r", encoding="utf-8") as fh:
                    count = sum(1 for ln in fh if ln.startswith("timber "))
            except OSError:
                out.write('{"ok":false,"error":"cannot read"}\n')
                out.flush()
                continue
            if count > cap:
                count = 0
                out.write('{"ok":false,"error":"角材的數量超過上限"}\n')
            else:
                time.sleep(load_sleep + 2e-11 * count ** 4)
                out.write('{"ok":true,"revision":1}\n')
        elif cmd == "line":
            time.sleep(1e-12 * count ** 3)
            out.write('{"ok":true,"deletedObjects":[]}\n')
        elif cmd == "snap":
            out.write('{"ok":false,"error":"R5: nothing to snap to"}\n')
        elif cmd == "dump":
            out.write('{"ok":true,"text":"dump %d"}\n' % count)
        elif cmd == "section-profile-read":
            out.write('{"ok":true,"nativeBytes":{"world":%d,"sectionProfiles":1}}\n' % (5605272 if cap > 64 else 4759448))
        else:
            out.write('{"ok":false,"error":"unknown"}\n')
        out.flush()
    return 0


def cmd_selftest(a):
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "src")
        os.makedirs(src)
        for name in ("_ax_r13_anchor_follows.scene", "_ax_r10_hole_follows_piece.scene", "_ax_r17_wall_column_face.scene"):
            with open(os.path.join(src, name), "w") as fh:
                fh.write("# dummy\n")
        base = argparse.Namespace(
            tsv=os.path.join(tmp, "t.tsv"), fake=True, caps="64,512", bin_root=tmp, scene_dir=os.path.join(tmp, "scenes"),
            src_root=src, calib=os.path.join(HERE, "calib", "f3-00.scene"), run_timeout=30.0, budget_until=0,
            hard_extra=240.0, cpu=None, force=False, pred_exp=4.0)
        ctx = Ctx(base)
        if cmd_worldbytes(ctx, base) != 0:
            problems.append("worldbytes failed")
        wb = {r["cap"]: r["note"] for r in ctx.tsv.rows() if r["kind"] == "worldbytes"}
        if wb.get(64) != "world=4759448" or wb.get(512) != "world=5605272":
            problems.append("worldbytes wrong: %r" % wb)
        if cmd_sanity(ctx, base) != 0:
            problems.append("sanity failed against the fake bridge")
        ra = argparse.Namespace(families="single,house", ns="16,32,64,128", house_ns="128", reps=2, rep_cutoff=20.0, model_base=False)
        rc = cmd_run(ctx, ra)
        rows = ctx.tsv.rows()
        loads = [r for r in rows if r["kind"] == "load"]
        want = {("single", 16, 64), ("single", 16, 512), ("single", 32, 64), ("single", 32, 512), ("single", 64, 64),
                ("single", 64, 512), ("single", 128, 512), ("house", 128, 512)}
        got = set((r["family"], r["N"], r["cap"]) for r in loads)
        if rc != 0 or got != want:
            problems.append("run units wrong rc=%s missing=%s extra=%s" % (rc, want - got, got - want))
        if len(loads) != 2 * len(want):
            problems.append("expected 2 load reps per unit, got %d rows" % len(loads))
        for kind, per_proc in (("line-grid", 3), ("line-delete", 2), ("line-timber", 2), ("line-place", 2)):
            cnt = len([r for r in rows if r["kind"] == kind and r["rc"] == 0])
            if cnt != per_proc * len(loads):
                problems.append("%s rows %d != %d" % (kind, cnt, per_proc * len(loads)))
        rc2 = cmd_run(ctx, ra)       # 續跑:不該再多任何列
        if rc2 != 0 or len(ctx.tsv.rows()) != len(rows):
            problems.append("resume re-ran finished units")
        # 容量 64 收不下 128:unit 根本不排
        if any(r["cap"] == 64 and r["N"] > 64 for r in loads):
            problems.append("cap 64 was asked for N>64")
        # stack 階梯
        sa = argparse.Namespace(rungs="16384,14336,12288,11264,10240,9216,8192,7168,6144,5120,4096", resolution=256,
                                workloads="gen64,ax_r13")
        cmd_stack(ctx, sa)
        for cap, need in ((512, 11000), (64, 5000)):
            for key in ("gen64", "ax_r13"):
                rs = [r for r in ctx.tsv.rows() if r["kind"] == "stack:" + key and r["cap"] == cap]
                passes = [r["stack_kib"] for r in rs if r["rc"] == 0]
                fails = [r["stack_kib"] for r in rs if r["rc"] != 0]
                if not passes or not fails or not (0 <= min(passes) - need <= 256) or max(fails) >= need:
                    problems.append("stack ladder cap=%d %s: pass=%s fail=%s need=%d" % (cap, key, sorted(passes)[:3], sorted(fails)[-3:], need))
        # 逾時:--run-timeout 小於假 load 的睡眠
        tctx = Ctx(argparse.Namespace(**dict(vars(base), tsv=os.path.join(tmp, "to.tsv"), run_timeout=0.3, caps="512")))
        os.environ["FAKE_LOAD_SLEEP"] = "1.0"
        try:
            cmd_run(tctx, argparse.Namespace(families="single", ns="16", house_ns="", reps=3, rep_cutoff=20.0, model_base=False))
        finally:
            del os.environ["FAKE_LOAD_SLEEP"]
        trows = [r for r in tctx.tsv.rows() if r["kind"] == "load"]
        if len(trows) != 1 or trows[0]["rc"] != RC_TIMEOUT:
            problems.append("timeout handling wrong: %r" % [(r["rc"], r["rep"]) for r in trows])
        # 硬期限:until 已過 => 不啟動、回 10
        dctx = Ctx(argparse.Namespace(**dict(vars(base), tsv=os.path.join(tmp, "dl.tsv"), caps="512",
                                             budget_until=time.time() - 1000, hard_extra=1.0)))
        rc3 = cmd_run(dctx, argparse.Namespace(families="single", ns="16", house_ns="", reps=1, rep_cutoff=20.0, model_base=False))
        if rc3 != 10 or [r for r in dctx.tsv.rows() if r["kind"] == "load" and r["rc"] == 0]:
            problems.append("deadline handling wrong (rc=%s)" % rc3)
    if problems:
        print("drive selftest FAILED:", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 1
    print("drive selftest OK")
    return 0


# --------------------------------------------------------------------------------------- main

def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--tsv", default=os.environ.get("BENCH_TSV", "bench.tsv"))
    ap.add_argument("--bin-root", default=os.environ.get("BENCH_BIN", ""))
    ap.add_argument("--scene-dir", default=os.environ.get("BENCH_SCENES", "scenes"))
    ap.add_argument("--src-root", default=os.environ.get("BENCH_SRC64", ""))
    ap.add_argument("--calib", default=os.path.join(HERE, "calib", "f3-00.scene"))
    ap.add_argument("--caps", default="64,512")
    ap.add_argument("--fake", action="store_true", help="use the built-in fake bridge (selftest only)")
    ap.add_argument("--run-timeout", type=float, default=900.0, dest="run_timeout")
    ap.add_argument("--budget-until", type=float, default=0.0, dest="budget_until",
                    help="epoch seconds; do not start work predicted to end after this")
    ap.add_argument("--hard-extra", type=float, default=240.0, dest="hard_extra")
    ap.add_argument("--cpu", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--retry-timeouts", action="store_true", dest="retry_timeouts",
                    help="treat earlier rc=124 load rows as not done (use after raising --run-timeout)")
    ap.add_argument("--pred-exp", type=float, default=4.0, dest="pred_exp")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("worldbytes")
    sub.add_parser("sanity")
    sub.add_parser("status")
    sub.add_parser("selftest")
    sub.add_parser("_fake-bridge")
    r = sub.add_parser("run")
    r.add_argument("--ns", default="16,32,64,128,256,512")
    r.add_argument("--house-ns", default="128,256,512", dest="house_ns")
    r.add_argument("--families", default="single,house")
    r.add_argument("--reps", type=int, default=3)
    r.add_argument("--rep-cutoff", type=float, default=20.0, dest="rep_cutoff")
    r.add_argument("--model-base", action="store_true", dest="model_base")
    s = sub.add_parser("stack")
    s.add_argument("--rungs", default="16384,14336,12288,11264,10240,9216,8192,7168,6144,5120,4096")
    s.add_argument("--resolution", type=int, default=256)
    s.add_argument("--workloads", default="")
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.command == "_fake-bridge":
        return fake_bridge()
    if a.command == "selftest":
        return cmd_selftest(a)
    if not a.fake and not a.bin_root and a.command != "status":
        print("--bin-root (or BENCH_BIN) is required", file=sys.stderr)
        return 64
    ctx = Ctx(a)
    return {"worldbytes": cmd_worldbytes, "sanity": cmd_sanity, "run": cmd_run, "stack": cmd_stack,
            "status": cmd_status}[a.command](ctx, a)


if __name__ == "__main__":
    sys.exit(main())
