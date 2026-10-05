# -*- coding: utf-8 -*-
"""QA 環境建置:從 QA worktree 原始碼用 MSVC 編出 bridge / model-base(/ core)到
%TEMP%\\geometry-qa\\bin\\,依「來源雜湊」快取:雜湊沒變就不重編。

用法:
    python build_qa.py [--repo D:/geometry-axiom-qa] [--core] [--force] [--no-verify]
輸出:
    %TEMP%\\geometry-qa\\bin\\bridge-<h12>.exe      (web_bridge.c + include 閉包 + current_geometry.c)
    %TEMP%\\geometry-qa\\bin\\model-base-<h12>.exe  (geometry-core/model_base.c + 閉包)
    %TEMP%\\geometry-qa\\bin\\core-<h12>.exe        (--core 時;current_geometry.c)
    %TEMP%\\geometry-qa\\bin\\paths.json            (給 start_server.* 與驗收 agent 讀)
設計:
  * exe 檔名帶雜湊,永不覆寫已存在的檔 -> 別的 agent 正在跑也不會 LNK1104 鎖檔,
    也不需要殺任何行程。
  * 同時只允許一個 build_qa 在編(bin\\.build.lock),其他的等它,然後走快取。
  * 雜湊 = 閉包內每個檔的位元組(CRLF 原樣,不正規化) + cl 指令列。
  * 編完驗:新檔存在、大小>0、含來源閉包裡的字串字面量(證明是這份原始碼編的)、
    行為驗(bridge 回 dump JSON;model-base 吃一個最小 scene)。被 SAC 擋(WinError 4551 /
    Permission denied / 啟動失敗)時間隔 12 秒重試 5 次;仍擋 -> 退出碼 3 並標「環境阻擋」。
退出碼:0 成功;2 編譯失敗(程式/工具鏈);3 環境阻擋(SAC);4 其他。
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

VCVARS = r"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
QA_ROOT = Path(os.environ.get("TEMP", tempfile.gettempdir())) / "geometry-qa"
BIN = QA_ROOT / "bin"
OBJ = QA_ROOT / "obj"
INCLUDE_RE = re.compile(rb'^\s*#\s*include\s+"([^"]+)"', re.M)
LITERAL_RE = re.compile(rb'"((?:[A-Za-z0-9 _:./=,\-\[\]{}%]){24,60})"')


def closure(entry: Path):
    """include "..." 遞迴閉包(相對於含 #include 的檔)。回傳排序後絕對路徑列表。"""
    seen, todo = {}, [entry.resolve()]
    while todo:
        p = todo.pop()
        if p in seen:
            continue
        data = p.read_bytes()
        seen[p] = data
        for m in INCLUDE_RE.finditer(data):
            q = (p.parent / m.group(1).decode("utf-8")).resolve()
            if q.is_file() and q not in seen:
                todo.append(q)
            elif not q.is_file():
                raise SystemExit(f"include 找不到:{q}(被 {p} 引用)")
    return sorted(seen), seen


TARGETS = {
    "bridge": ("geometry-web/web_bridge.c", "bridge"),
    "model-base": ("geometry-core/model_base.c", "model-base"),
    "core": ("current_geometry.c", "core"),
}


def cl_args(src: Path, exe: Path, obj: Path):
    return ["cl", "/nologo", "/utf-8", "/O2", "/W3", "/U_WIN32", f"/Fe:{exe}", f"/Fo:{obj}", str(src),
            "/link", "/STACK:16777216"]


def source_hash(repo: Path, name: str):
    rel, _ = TARGETS[name]
    src = repo / rel
    files, contents = closure(src)
    h = hashlib.sha256()
    for f in files:
        h.update(f.relative_to(repo).as_posix().encode("utf-8") + b"\0")
        h.update(hashlib.sha256(contents[f]).digest())
    h.update(" ".join(cl_args(Path("S"), Path("E"), Path("O"))).encode())
    return h.hexdigest(), src, files, contents


def blocked_text(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in ("4551", "permission denied", "拒絕存取", "access is denied", "winerror 5",
                                "橋接器連線中斷"))


def verify_behavior(name: str, exe: Path):
    """回 (ok, blocked, detail)。"""
    try:
        if name == "bridge":
            r = subprocess.run([str(exe)], input=b"dump\n", capture_output=True, timeout=30)
            out = r.stdout.decode("utf-8", "replace")
            ok = r.returncode == 0 and out.strip().startswith("{") and '"ok"' in out
            return ok, False, out[:120].replace("\n", " ")
        if name == "model-base":
            with tempfile.TemporaryDirectory(prefix="qa-mb-") as d:
                s = Path(d) / "in.scene"
                s.write_text("boundary 1 outline 0,0 1000,0 1000,1000 0,1000\n", encoding="utf-8")
                r = subprocess.run([str(exe), str(s)], capture_output=True, timeout=30)
            out = r.stdout.decode("utf-8", "replace")
            ok = r.returncode == 0 and out.strip().startswith("{")
            return ok, False, out[:120].replace("\n", " ")
        # core 預設把 current_geometry.svg 寫在「原始碼旁」(會寫進 repo 被忽略檔),必須 --out 導到暫存
        with tempfile.TemporaryDirectory(prefix="qa-core-") as d:
            r = subprocess.run([str(exe), "--out", str(Path(d) / "o.svg")], capture_output=True, timeout=30, cwd=d)
        return r.returncode == 0, False, f"exit={r.returncode}"
    except PermissionError as e:
        return False, True, f"PermissionError {e}"
    except OSError as e:
        return False, blocked_text(str(e)) or getattr(e, "winerror", 0) in (4551, 5), f"OSError {e}"
    except subprocess.TimeoutExpired:
        return False, False, "timeout"


def binary_has_source_string(exe: Path, contents: dict) -> tuple:
    data = exe.read_bytes()
    cands = []
    for blob in contents.values():
        for m in LITERAL_RE.finditer(blob):
            cands.append(m.group(1))
    cands = sorted(set(cands), key=len, reverse=True)[:60]
    hit = [c for c in cands if c in data]
    return (len(hit) >= 3 if len(cands) >= 3 else len(hit) >= 1), f"{len(hit)}/{len(cands)} 個來源字串字面量出現在 exe"


def acquire_lock(timeout=900):
    BIN.mkdir(parents=True, exist_ok=True)
    lock = BIN / ".build.lock"
    t0 = time.time()
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return lock
        except FileExistsError:
            # 過期鎖(>20 分鐘)才清;不殺任何行程
            try:
                if time.time() - lock.stat().st_mtime > 1200:
                    lock.unlink()
                    continue
            except OSError:
                pass
            if time.time() - t0 > timeout:
                raise SystemExit("等 build lock 逾時")
            time.sleep(2)


def build_one(repo: Path, name: str, force: bool, verify: bool, log):
    h, src, files, contents = source_hash(repo, name)
    h12 = h[:12]
    exe = BIN / f"{name}-{h12}.exe"
    meta = BIN / f"{name}-{h12}.json"
    rebuilt = False
    verified = False
    if exe.exists() and meta.exists() and not force:
        try:
            verified = json.loads(meta.read_text(encoding="utf-8")).get("verified", False)
        except (OSError, ValueError):
            verified = False
        log(f"[{name}] 快取命中 {exe.name}(來源雜湊 {h12},未重編;verified={verified})")
    else:
        if exe.exists() and force:
            exe = BIN / f"{name}-{h12}-f{int(time.time())}.exe"
        obj = OBJ / f"{name}-{h12}"
        obj.mkdir(parents=True, exist_ok=True)
        bat = obj / "build.bat"
        cmd = " ".join(f'"{a}"' if " " in a or "\\" in a else a for a in cl_args(src, exe, obj / (name + ".obj")))
        bat.write_text(f'@echo off\r\ncall "{VCVARS}" >nul 2>&1\r\ncd /d "{repo}"\r\n{cmd}\r\n', encoding="utf-8")
        t0 = time.time()
        log(f"[{name}] 編譯 -> {exe.name}")
        r = subprocess.run(["cmd", "/c", str(bat)], capture_output=True)
        out = (r.stdout + r.stderr).decode("utf-8", "replace")
        if r.returncode != 0 or not exe.exists() or "fatal error" in out:
            log(out[-3000:])
            raise SystemExit(2)
        if exe.stat().st_mtime < t0 - 2:
            log(f"[{name}] exe 時間戳早於本次編譯開始,不是新檔")
            raise SystemExit(2)
        rebuilt = True
        meta.write_text(json.dumps({"name": name, "source_hash": h, "exe": str(exe), "verified": False,
                                    "rebuilt_this_run": True, "built_at": time.strftime("%F %T")}, indent=1), encoding="utf-8")
    ok_str, str_detail = binary_has_source_string(exe, contents)
    log(f"[{name}] 二進位新舊驗證:{'OK' if ok_str else 'FAIL'}({str_detail});sha256={hashlib.sha256(exe.read_bytes()).hexdigest()[:16]};"
        f"size={exe.stat().st_size};mtime={time.strftime('%F %T', time.localtime(exe.stat().st_mtime))}")
    if not ok_str:
        raise SystemExit(2)
    blocked = False
    if verify and not verified:
        for attempt in range(1, 6):
            ok, blocked, detail = verify_behavior(name, exe)
            if ok:
                log(f"[{name}] 行為驗 OK:{detail}")
                blocked = False
                break
            log(f"[{name}] 行為驗未過(第{attempt}次;blocked={blocked}):{detail}")
            if attempt < 5:
                time.sleep(12)
        else:
            if blocked:
                log(f"[{name}] 環境阻擋(Smart App Control 疑似封鎖新 exe);請稍後重跑 build_qa.py,不要當成程式失敗")
                raise SystemExit(3)
            raise SystemExit(2)
    meta.write_text(json.dumps({"name": name, "source_hash": h, "exe": str(exe), "rebuilt_this_run": rebuilt, "verified": bool(verify and not blocked) or verified,
                                "closure": [f.relative_to(repo).as_posix() for f in files],
                                "built_at": time.strftime("%F %T")}, ensure_ascii=False, indent=1), encoding="utf-8")
    return str(exe), h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="D:/geometry-axiom-qa")
    ap.add_argument("--core", action="store_true", help="另外編 core.exe(feedback_cli replay 用)")
    ap.add_argument("--force", action="store_true", help="忽略快取強制重編(新檔名,不覆寫舊檔)")
    ap.add_argument("--no-verify", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    log = lambda s: print(s, flush=True)
    log(f"repo={repo}  HEAD={subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()}")
    lock = acquire_lock()
    try:
        paths = {"repo": str(repo)}
        names = ["bridge", "model-base"] + (["core"] if args.core else [])
        hashes = {}
        for n in names:
            paths[n], hashes[n] = build_one(repo, n, args.force, not args.no_verify, log)
        paths["hashes"] = hashes
        (BIN / "paths.json").write_text(json.dumps(paths, ensure_ascii=False, indent=1), encoding="utf-8")
        log("paths.json:" + json.dumps(paths, ensure_ascii=False))
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    main()
