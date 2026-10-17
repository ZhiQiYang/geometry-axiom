"""把原生核心的接受/拒絕輸出轉成 results.json 與 RESULTS.md。

整份場景失敗會回滾，不能把沒被點名的角材記成接受。
有逐支前綴（mNNN.rc）時，前綴結果優先於整場結果。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

V_MAP = {
    "V_EXTENSION": "I22",
    "V_CUT_PRIORITY": "I19",
    "V_BOUNDARY_ROLE": "I20",
    "V_PRIMARY_AXIS": "I21",
    "V_FREE_EDGE_END": "I6",
    "V_GRID_LOCKED": "I23",
}

EXPLICIT = re.compile(r"(?<![A-Za-z0-9])(R\d+(?:\([a-z]\))?|I\d+)(?![A-Za-z0-9])")
VCODE = re.compile(r"V_[A-Z0-9_]+")
NAMED = re.compile(r"角材(?:\s*|（)(\d+)")
LENGTH = re.compile(r"角材 ID：(\d+)\n尺寸：L=(\d+)")
PREFIX = re.compile(r"^(.*?):(\d+):\s*(.*)$")
TIMBER = re.compile(
    r"^timber (\d+) \d+ \d+ role (boundary|primary|secondary|custom)(?: priority (\d+))?\s*$"
)

ACCEPT = "接受"
REJECT = "拒絕"
UNSUBMITTED = "同場未提交"


def strip_location(line: str) -> str:
    match = PREFIX.match(line.strip())
    if match and match.group(3):
        return match.group(3).strip()
    return line.strip()


def clause_of(message: str) -> str:
    explicit = EXPLICIT.search(message)
    if explicit:
        return explicit.group(1)
    code = VCODE.search(message)
    if code and code.group(0) in V_MAP:
        return V_MAP[code.group(0)]
    return "—"


def first_diagnostic(stderr: str) -> str:
    for line in stderr.replace("\r\n", "\n").splitlines():
        if line.strip():
            return strip_location(line)
    return ""


def lengths_of(stdout: str) -> dict[int, int]:
    found = {}
    for match in LENGTH.finditer(stdout.replace("\r\n", "\n")):
        found[int(match.group(1))] = int(match.group(2))
    return found


def core_role_text(role: str, priority, pending) -> str:
    if pending:
        return f"{role}（待裁定）"
    if role == "custom" and priority is not None:
        return f"custom priority {priority}"
    return role


def scene_members(scene_name: str, scene_text: str) -> tuple[dict, list[dict]]:
    meta = {"room": scene_name, "layout": None, "name": None}
    members = []
    for line in scene_text.replace("\r\n", "\n").splitlines():
        if line.startswith("# probe-meta "):
            meta.update(json.loads(line[len("# probe-meta "):]))
        elif line.startswith("# probe-member "):
            item = json.loads(line[len("# probe-member "):])
            members.append(item)
    if members:
        return meta, members
    for line in scene_text.replace("\r\n", "\n").splitlines():
        match = TIMBER.match(line.strip())
        if not match:
            continue
        priority = int(match.group(3)) if match.group(3) else None
        members.append({
            "id": int(match.group(1)),
            "kind": "—",
            "role": match.group(2),
            "priority": priority,
            "rect": None,
            "pending": None,
        })
    return meta, members


def _row(member: dict, status: str, clause: str, message: str, length, omitted: list[int]) -> dict:
    return {
        "id": member["id"],
        "kind": member.get("kind") or "—",
        "role": member.get("role"),
        "priority": member.get("priority"),
        "rect": member.get("rect"),
        "pending": member.get("pending"),
        "status": status,
        "clause": clause,
        "message": message,
        "core_length": length,
        "omitted": list(omitted),
    }


def interpret_scene(scene_name: str, scene_text: str, stdout: str = "", stderr: str = "",
                    rc: int | None = None, attempts: dict | None = None) -> dict:
    meta, members = scene_members(scene_name, scene_text)
    rows = []
    if attempts is not None:
        for member in members:
            attempt = attempts.get(member["id"])
            if attempt is None:
                rows.append(_row(member, "未跑", "—", "", None, []))
                continue
            omitted = list(attempt.get("omit") or [])
            if attempt["rc"] == 0:
                found = lengths_of(attempt.get("out") or "")
                rows.append(_row(member, ACCEPT, "—", "", found.get(member["id"]), omitted))
            else:
                message = first_diagnostic(attempt.get("err") or "")
                if not message:
                    message = f"（無 stderr，結束碼 {attempt['rc']}）"
                rows.append(_row(member, REJECT, clause_of(message), message, None, omitted))
    elif rc == 0:
        found = lengths_of(stdout or "")
        for member in members:
            rows.append(_row(member, ACCEPT, "—", "", found.get(member["id"]), []))
    else:
        message = first_diagnostic(stderr or "")
        if not message:
            message = f"（無 stderr，結束碼 {rc}）"
        named = NAMED.search(message)
        named_id = int(named.group(1)) if named else None
        clause = clause_of(message)
        for member in members:
            if named_id is not None and member["id"] == named_id:
                rows.append(_row(member, REJECT, clause, message, None, []))
            else:
                # 沒被點名的不記成接受：整場失敗時世界已回滾。
                # 訊息沒有點名任何一支時，同一則場景錯誤附在每一列，狀態仍是未提交。
                attached = message if named_id is None else ""
                attached_clause = clause if named_id is None else "—"
                rows.append(_row(member, UNSUBMITTED, attached_clause, attached, None, []))
    return {
        "scene": scene_name,
        "room": meta.get("room") or scene_name,
        "layout": meta.get("layout"),
        "name": meta.get("name"),
        "full_rc": rc,
        "members": rows,
    }


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _read_rc(path: Path) -> int | None:
    if not path.is_file():
        return None
    return int(path.read_text(encoding="utf-8").strip())


def _read_omit(path: Path) -> list[int]:
    text = _read_text(path).strip()
    if not text:
        return []
    return [int(part) for part in text.split()]


def parse_run(run_dir: Path, scenes_dir: Path) -> dict:
    scenes = []
    for scene_path in sorted(scenes_dir.glob("*.scene")):
        text = scene_path.read_text(encoding="utf-8")
        bucket = run_dir / scene_path.stem
        full_rc = _read_rc(bucket / "full.rc")
        prefix = sorted(bucket.glob("m*.rc"))
        if prefix:
            attempts = {}
            for rc_path in prefix:
                number = int(rc_path.stem[1:])
                attempts[number] = {
                    "rc": _read_rc(rc_path),
                    "out": _read_text(rc_path.with_suffix(".out")),
                    "err": _read_text(rc_path.with_suffix(".err")),
                    "omit": _read_omit(rc_path.with_suffix(".omit")),
                }
            item = interpret_scene(scene_path.stem, text, rc=full_rc, attempts=attempts)
        else:
            item = interpret_scene(
                scene_path.stem,
                text,
                stdout=_read_text(bucket / "full.out"),
                stderr=_read_text(bucket / "full.err"),
                rc=full_rc if full_rc is not None else 1,
            )
        scenes.append(item)
    return {"source": str(run_dir), "scenes": scenes}


def _cell(value) -> str:
    if value is None or value == "":
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(document: dict) -> str:
    lines = [
        "# 核心探針結果",
        "",
        "每一列是一支角材。整場失敗且沒有逐支前綴時，沒被錯誤訊息點名的列是「同場未提交」，不是接受。",
        "有 mNNN 前綴時，以該前綴的結束碼為準。省略先前被拒的料會改變後面的擋面。",
        "",
        "| 房間 | 排法 | 角材編號 | 種類 | 核心角色 | 接受/拒絕 | 條號 | 訊息 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for scene in document["scenes"]:
        layout = scene.get("name") or "—"
        for member in scene["members"]:
            role = core_role_text(member.get("role"), member.get("priority"), member.get("pending"))
            lines.append("| " + " | ".join([
                _cell(scene.get("room")),
                _cell(layout),
                _cell(member.get("id")),
                _cell(member.get("kind")),
                _cell(role),
                _cell(member.get("status")),
                _cell(member.get("clause")),
                _cell(member.get("message")),
            ]) + " |")
    lines.append("")
    return "\n".join(lines)


def write_outputs(document: dict, run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "results.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (run_dir / "RESULTS.md").write_text(render_markdown(document), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="彙整原生核心探針輸出")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--scenes", type=Path, default=None)
    args = parser.parse_args()
    scenes = args.scenes or (args.run_dir / "scenes")
    document = parse_run(args.run_dir, scenes)
    write_outputs(document, args.run_dir)


if __name__ == "__main__":
    main()
