# -*- coding: utf-8 -*-
"""回報收件匣(GEO-183)的 agent 端入口。

    python geometry-web/feedback_cli.py list [--all]     未處理的回報(--all 含已關)
    python geometry-web/feedback_cli.py show <id>        印 report.md(摘要 + 最後 40 筆操作)
    python geometry-web/feedback_cli.py events <id> [-n 100]   印更多原始操作紀錄
    python geometry-web/feedback_cli.py replay <id>      用 core.exe 載回當下世界、列出改動世界的指令序列
    python geometry-web/feedback_cli.py close <id> "<處理結果,例如 已修 abc1234>" [--status wontfix|cannot-reproduce]

core.exe 路徑:GEOMETRY_CORE,預設 %TEMP%/geometry-tests/core.exe。回報目錄:GEOMETRY_FEEDBACK_DIR,預設 repo 的 feedback/。
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import feedback_store as store  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# web_bridge.c 會改世界的指令;其餘(dump/boundary/objects/pick/bhit/newid/render/surfaces/references/proj/snap/uv/obstacles)唯讀
MUTATING = ("line ", "drag ", "default", "loadfile ", "reset")


def _events(fid):
    p = store.feedback_dir() / fid / "events.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def cmd_list(a):
    metas = store.load_all()
    rows = [m for m in metas if a.all or m["status"] == "open"]
    if not rows:
        print("(沒有未處理的回報)" if not a.all else "(收件匣是空的)")
        return 0
    for m in sorted(rows, key=lambda m: m["id"]):
        el = (m.get("target") or {}).get("el") or ""
        note = (m.get("note") or m.get("auto_reason") or "").replace("\n", " ")[:70]
        print(f"{m['id']}  [{m['status']}] {store.KINDS.get(m['kind'], m['kind'])}  {(m.get('context') or {}).get('view', '')}")
        print(f"    {note}" + (f"\n    指到:{el}" if el else ""))
    return 0


def cmd_show(a):
    store.load(a.id)
    print((store.feedback_dir() / a.id / "report.md").read_text(encoding="utf-8"))
    return 0


def cmd_events(a):
    store.load(a.id)
    for e in _events(a.id)[-a.n:]:
        print(json.dumps(e, ensure_ascii=False))
    return 0


def cmd_replay(a):
    meta = store.load(a.id)
    d = store.feedback_dir() / a.id
    muts = [("  " if e.get("ok") else "✗ ") + e["cmd"] + ("" if e.get("ok") else f"  → {e.get('error', '')}")
            for e in _events(a.id) if e.get("k") == "api" and e.get("cmd")
            and e["cmd"].startswith(MUTATING)]
    print(f"== {a.id} 回報前送出、會改世界的指令({len(muts)} 筆,依時間序;✗ 表示被拒)==")
    for c in muts:
        print(c)
    world = d / "world.scene"
    if not world.exists():
        print("\n(這筆回報沒有 world.scene——當時橋接器可能已斷線)")
        return 1
    core = pathlib.Path(os.environ.get("GEOMETRY_CORE") or pathlib.Path(tempfile.gettempdir()) / "geometry-tests" / "core.exe")
    print(f"\n== 用 {core} 載回回報當下的世界 ==")
    if not core.exists():
        print("找不到 core.exe;設定 GEOMETRY_CORE 或先依 AGENTS.md 編到 %TEMP%\\geometry-tests\\")
        return 1
    out = pathlib.Path(tempfile.gettempdir()) / f"feedback-{a.id}.svg"
    p = subprocess.run([str(core), "--scene", str(world), "--no-window", "--out", str(out)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(f"exit {p.returncode}" + (f";三視圖:{out}" if p.returncode == 0 else ""))
    if p.returncode:
        print(p.stderr.strip()[-2000:])
        print("(提醒:世界含未 place 的角材時,loadfile 依 I9 收尾檢查拒絕是條文要求,見決策佇列 Q12)")
    print(f"\n畫面快照:{d / 'page.html'}" if (d / "page.html").exists() else "")
    if meta.get("target"):
        print(f"使用者指到:{meta['target'].get('el')}")
    return p.returncode


def cmd_close(a):
    m = store.close(a.id, a.resolution, a.status)
    print(f"{m['id']} → {m['status']}:{m['resolution']}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="geometry-web 回報收件匣")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--all", action="store_true"); p.set_defaults(fn=cmd_list)
    p = sub.add_parser("show"); p.add_argument("id"); p.set_defaults(fn=cmd_show)
    p = sub.add_parser("events"); p.add_argument("id"); p.add_argument("-n", type=int, default=100); p.set_defaults(fn=cmd_events)
    p = sub.add_parser("replay"); p.add_argument("id"); p.set_defaults(fn=cmd_replay)
    p = sub.add_parser("close"); p.add_argument("id"); p.add_argument("resolution")
    p.add_argument("--status", default="closed", choices=["closed", "wontfix", "cannot-reproduce", "open"])
    p.set_defaults(fn=cmd_close)
    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except store.FeedbackError as e:
        print("✗ " + str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
