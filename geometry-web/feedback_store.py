# -*- coding: utf-8 -*-
"""使用者回報收件匣(GEO-183)的儲存層:serve.py 寫入、feedback_cli.py 讀取／關單共用。

一筆回報 = 一個資料夾 feedback/<id>/:
    meta.json       機器讀的全部欄位(狀態、分類、指到的元素、畫面狀態、版本)
    report.md       給人與 agent 直接讀的摘要(由 meta.json + events 產生)
    events.jsonl    回報前的操作黑盒子(api 指令與回應、點擊、按鍵、toast、錯誤)
    world.scene     回報當下的世界(bridge dump,可以直接 loadfile 重現)
    page.html       回報當下的畫面 DOM 快照(內嵌 app.css、拿掉 script,雙擊即可看)
    screenshot.png  使用者貼上的截圖(選填)
feedback/INBOX.md 由所有 meta.json 重新產生,不做增量追加——多個寫入者不會互相踩。
"""
import base64
import datetime
import json
import os
import pathlib
import re
import subprocess
import threading

REPO = pathlib.Path(__file__).resolve().parent.parent
KINDS = {"bug": "問題", "unexpected": "不符預期", "idea": "建議", "good": "好用", "auto": "自動擷取"}
MAX_EVENTS = 2000
MAX_TEXT = 8 * 1024 * 1024
_lock = threading.Lock()


class FeedbackError(ValueError):
    pass


def feedback_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("GEOMETRY_FEEDBACK_DIR") or (REPO / "feedback"))


def _git(*args):
    try:
        return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True,
                              encoding="utf-8", timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _version():
    head = _git("rev-parse", "--short", "HEAD")
    dirty = bool(_git("status", "--porcelain", "--untracked-files=no"))
    return {"commit": head or "unknown", "dirty": dirty}


def _str(v, limit=4000):
    return v[:limit] if isinstance(v, str) else ""


def _next_id(root: pathlib.Path, now: datetime.datetime) -> str:
    day = now.strftime("%Y%m%d")
    seqs = [int(m.group(1)) for p in root.glob(f"F-{day}-*")
            if (m := re.fullmatch(rf"F-{day}-(\d+)", p.name))]
    return f"F-{day}-{max(seqs, default=0) + 1:03d}"


def _fmt_event(ev, t0):
    dt = (ev.get("t", t0) - t0) / 1000.0
    k = ev.get("k")
    if k == "api":
        mark = "✓" if ev.get("ok") else "✗"
        tail = "" if ev.get("ok") else f" → {ev.get('error', '')}"
        return f"{dt:+7.1f}s api {mark} `{ev.get('cmd', '')}`{tail}"
    if k == "click":
        return f"{dt:+7.1f}s 點 {ev.get('el', '')}"
    if k == "key":
        return f"{dt:+7.1f}s 鍵 {ev.get('key', '')}（{ev.get('el', '')}）"
    if k == "change":
        return f"{dt:+7.1f}s 改值 {ev.get('el', '')} = {json.dumps(ev.get('value'), ensure_ascii=False)}"
    if k == "toast":
        return f"{dt:+7.1f}s toast[{ev.get('type', '')}] {ev.get('msg', '')}"
    if k == "status":
        return f"{dt:+7.1f}s 狀態列 {ev.get('msg', '')}"
    if k in ("error", "console"):
        return f"{dt:+7.1f}s **{'錯誤' if k == 'error' else 'console.error'}** {ev.get('msg', '')[:300]}"
    return f"{dt:+7.1f}s {k} {json.dumps(ev, ensure_ascii=False)[:200]}"


def render_report(meta, events, folder=None) -> str:
    folder = folder or feedback_dir() / meta["id"]
    ctx = meta.get("context") or {}
    target = meta.get("target") or {}
    lines = [
        f"# {meta['id']} · {KINDS.get(meta['kind'], meta['kind'])} · {meta['created']}",
        "",
        f"- 狀態:**{meta['status']}**" + (f"({meta['resolution']})" if meta.get("resolution") else ""),
        f"- 使用者說:{meta.get('note') or '(沒寫,看下面的操作紀錄與指到的元素)'}",
    ]
    if target:
        lines.append(f"- 指到的元素:`{target.get('el', '')}`"
                     + (f" 「{target['text']}」" if target.get("text") else "")
                     + (f" 位置 {target['rect']}" if target.get("rect") else "")
                     + "(元素用途查 geometry-web/docs/DOM-CONTRACT.md)")
    lines += [
        f"- 畫面:{ctx.get('view', '')}",
        f"- 狀態快照:`{json.dumps(ctx.get('state', {}), ensure_ascii=False)}`",
        f"- 視窗:{ctx.get('viewport', '')};場景:{ctx.get('scene', '')}",
        f"- 程式版本:{meta['version']['commit']}" + ("(工作區有未提交修改)" if meta['version']['dirty'] else ""),
        "",
        "## 回報前的操作(最後 40 筆,時間相對於按下回報)",
        "",
    ]
    t0 = meta.get("t_mark") or (events[-1].get("t", 0) if events else 0)
    tail = events[-40:]
    lines += [f"- {_fmt_event(e, t0)}" for e in tail] or ["- (沒有紀錄)"]
    errs = [e for e in events if e.get("k") == "error"]
    if errs:
        lines += ["", "## 錯誤", ""] + [f"- {e.get('msg', '')}\n  ```\n  {e.get('stack', '')}\n  ```" for e in errs[-5:]]
    files = [f for f in ("world.scene", "events.jsonl", "page.html", "screenshot.png")
             if (folder / f).exists()]
    lines += ["", "## 附件", "", "、".join(f"`{f}`" for f in files),
              "", f"重現:`python geometry-web/feedback_cli.py replay {meta['id']}`", ""]
    return "\n".join(lines)


def _write_inbox(root: pathlib.Path):
    metas = load_all(root)
    rows = ["# 回報收件匣", "",
            "> 由 geometry-web 的回報面板(F8)寫入;本檔自動產生,不要手改。",
            "> agent:`python geometry-web/feedback_cli.py list` 看未處理,`show <id>` 看細節。", "",
            "| id | 狀態 | 分類 | 使用者說 | 指到的元素 | 畫面 |", "|---|---|---|---|---|---|"]
    for m in sorted(metas, key=lambda m: m["id"], reverse=True):
        note = (m.get("note") or "").replace("|", "／").replace("\n", " ")[:60]
        el = ((m.get("target") or {}).get("el") or "").replace("|", "／")
        rows.append(f"| [{m['id']}]({m['id']}/report.md) | {m['status']} | {KINDS.get(m['kind'], m['kind'])} "
                    f"| {note} | `{el}` | {(m.get('context') or {}).get('view', '')} |")
    (root / "INBOX.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def load_all(root=None):
    root = root or feedback_dir()
    out = []
    for p in sorted(root.glob("F-*/meta.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return out


def load(fid: str):
    if not re.fullmatch(r"F-\d{8}-\d{3,}", fid or ""):
        raise FeedbackError("回報 id 格式不對")
    p = feedback_dir() / fid / "meta.json"
    if not p.exists():
        raise FeedbackError(f"找不到回報 {fid}")
    return json.loads(p.read_text(encoding="utf-8"))


def save(payload, now=None) -> dict:
    if not isinstance(payload, dict):
        raise FeedbackError("回報內容必須是 JSON 物件")
    kind = payload.get("kind")
    if kind not in KINDS:
        raise FeedbackError("不認得的回報分類")
    events = payload.get("events") or []
    if not isinstance(events, list):
        raise FeedbackError("events 必須是陣列")
    events = [e for e in events if isinstance(e, dict)][-MAX_EVENTS:]
    now = now or datetime.datetime.now()
    root = feedback_dir()
    with _lock:
        root.mkdir(parents=True, exist_ok=True)
        fid = _next_id(root, now)
        final = root / fid
        d = root / (".tmp-" + fid)
        d.mkdir()
        target = payload.get("target") if isinstance(payload.get("target"), dict) else None
        context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
        meta = {
            "id": fid, "kind": kind, "status": "open", "resolution": "",
            "created": now.strftime("%Y-%m-%d %H:%M:%S"),
            "note": _str(payload.get("note")),
            "auto_reason": _str(payload.get("auto_reason"), 500),
            "target": target, "context": context,
            "t_mark": payload.get("t_mark") if isinstance(payload.get("t_mark"), (int, float)) else None,
            "version": _version(),
        }
        with open(d / "events.jsonl", "w", encoding="utf-8", newline="\n") as f:
            for e in events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        world = _str(payload.get("world"), MAX_TEXT)
        if world:
            (d / "world.scene").write_text(world, encoding="utf-8", newline="\n")
        page = _str(payload.get("page"), MAX_TEXT)
        if page:
            (d / "page.html").write_text(page, encoding="utf-8", newline="\n")
        shot = _str(payload.get("screenshot"), MAX_TEXT)
        m = re.fullmatch(r"data:image/png;base64,([A-Za-z0-9+/=]+)", shot)
        if m:
            (d / "screenshot.png").write_bytes(base64.b64decode(m.group(1)))
        (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        (d / "report.md").write_text(render_report(meta, events, d), encoding="utf-8")
        d.rename(final)  # 讀的人(CLI、測試)只會看到完整的一筆,不會讀到寫一半的資料夾
        _write_inbox(root)
    return {"ok": True, "id": fid, "path": str(final)}


def close(fid: str, resolution: str, status="closed") -> dict:
    if status not in ("open", "closed", "wontfix", "cannot-reproduce"):
        raise FeedbackError("狀態只能是 open / closed / wontfix / cannot-reproduce")
    with _lock:
        meta = load(fid)
        meta["status"], meta["resolution"] = status, resolution
        d = feedback_dir() / fid
        (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        events = [json.loads(l) for l in (d / "events.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        (d / "report.md").write_text(render_report(meta, events), encoding="utf-8")
        _write_inbox(feedback_dir())
    return meta
