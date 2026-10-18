"""把原生核心的接受/拒絕輸出轉成 results.json 與 RESULTS.md。

整份場景失敗會回滾，不能把沒被點名的角材記成接受。
有逐支前綴（mNNN.rc）時，前綴結果優先於整場結果。

依 opus／ChatGPT 對 #297 的審查更正：
- 結束碼只有 0（接受）與核心明確的拒絕碼 1（CORE_REJECT_RC）有意義；其他非 0（崩潰、訊號、
  逾時、沒有結束碼檔）標成「錯誤」，不得算拒絕。
- 結束碼 0 的列，若有 oracle 矩形（# probe-member 的 rect），核心輸出的 L 必須等於矩形長邊；
  stdout 有印角材原點與 A0 接觸面頂點時一併比對。對不上標「幾何不符」，不得算接受。
- 有「錯誤」或「幾何不符」列時 main() 回 3，run_probe.sh 原樣傳出。
- 每列記探測方式：原場景，或先前被拒的料已省略後再試。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
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
ORIGIN = re.compile(r"角材原點：\((-?\d+), (-?\d+), (-?\d+)\)")
A0_FACE = re.compile(
    r"角材 (\d+) 的 A0[^\n]*：\n((?:[ \t]+vertex\[\d+\] = \(-?\d+, -?\d+, -?\d+\)\n?){4})"
)
VERTEX = re.compile(r"vertex\[\d+\] = \((-?\d+), (-?\d+), (-?\d+)\)")
CAPACITY_MARK = "數量超過上限"  # WORLD_MAX_TIMBERS 的拒絕訊息；是容量，不是放置規則
PREFIX = re.compile(r"^(.*?):(\d+):\s*(.*)$")
TIMBER = re.compile(
    r"^timber (\d+) \d+ \d+ role (boundary|primary|secondary|custom)(?: priority (\d+))?\s*$"
)

ACCEPT = "接受"
REJECT = "拒絕"
ERROR = "錯誤"
MISMATCH = "幾何不符"  # 核心接受了，但核心算出的 L／足跡／原點和 oracle 矩形對不上
UNSUBMITTED = "同場未提交"
MODE_ORIGINAL = "原場景"  # 這一列的結果來自整場原樣，或前面沒有任何被省略的料
MODE_OMITTED = "省略後探測"  # 前面被拒的料已拿掉再試，擋面可能和原場景不同

# current_geometry.c 的 main()：成功 return 0；場景被拒、參數錯、讀檔失敗一律 return 1，
# 沒有其他回傳值（2026-10-18 讀 main 的每個 return 核對）。所以只有 1 是「核心明確的拒絕」。
# 其他非 0（崩潰 139／134、逾時 124、找不到執行檔 127、其他）不是規則拒絕，標成「錯誤」。
CORE_REJECT_RC = 1
EXIT_PROBE_ERRORS = 3  # 有任何「錯誤」或「幾何不符」列時，parse_results 的結束碼；run_probe.sh 會原樣傳出


def classify_rc(rc) -> str:
    if rc == 0:
        return ACCEPT
    if rc == CORE_REJECT_RC:
        return REJECT
    return ERROR


def describe_error_rc(rc) -> str:
    if rc is None:
        return "沒有結束碼檔"
    if rc == 124:
        return "結束碼 124，逾時"
    if rc > 128:
        return f"結束碼 {rc}，被訊號 {rc - 128} 終止"
    return f"結束碼 {rc}，不是核心的拒絕碼 {CORE_REJECT_RC}"


def error_message(rc, stderr: str) -> str:
    first = first_diagnostic(stderr or "")
    text = f"（{describe_error_rc(rc)}；核心異常，不是規則拒絕）"
    return f"{text} {first}" if first else text


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


def core_timbers(stdout: str) -> dict[int, dict]:
    """核心 stdout 裡每支已放置角材的 L、角材原點、A0 接觸面四個頂點的 x/y 外框。

    原點和足跡只在 stdout 有印時才有值；沒印就是 None，不拿來比。
    """
    found: dict[int, dict] = {}
    text = (stdout or "").replace("\r\n", "\n")
    for part in re.split(r"(?=角材 ID：\d+\n)", text):
        head = LENGTH.match(part)
        if not head:
            continue
        ident = int(head.group(1))
        info = {"length": int(head.group(2)), "origin": None, "footprint": None}
        origin = ORIGIN.search(part)
        if origin:
            info["origin"] = (int(origin.group(1)), int(origin.group(2)))
        for face in A0_FACE.finditer(part):
            if int(face.group(1)) != ident:
                continue
            points = [(int(a), int(b)) for a, b, _c in VERTEX.findall(face.group(2))]
            xs = [pt[0] for pt in points]
            ys = [pt[1] for pt in points]
            info["footprint"] = [min(xs), min(ys), max(xs), max(ys)]
            break
        found[ident] = info
    return found


def lengths_of(stdout: str) -> dict[int, int]:
    return {ident: info["length"] for ident, info in core_timbers(stdout).items()}


def geometry_problems(rect, info: dict) -> tuple[list[str], list[str]]:
    """核心輸出對 oracle 矩形 [x0,y0,x1,y1]：回傳 (不符清單, 實際比對了哪些項目)。"""
    x0, y0, x1, y1 = rect
    problems = []
    checked = ["L"]
    long_side = max(x1 - x0, y1 - y0)
    if info["length"] != long_side:
        problems.append(f"核心 L={info['length']}，oracle 矩形 {list(rect)} 長邊 {long_side}")
    if info["footprint"] is not None:
        checked.append("足跡")
        if list(info["footprint"]) != list(rect):
            problems.append(f"核心足跡 {info['footprint']} ≠ oracle 矩形 {list(rect)}")
    if info["origin"] is not None:
        checked.append("原點")
        if info["origin"] not in {(x0, y0), (x0, y1), (x1, y0), (x1, y1)}:
            problems.append(f"核心角材原點 {list(info['origin'])} 不在 oracle 矩形 {list(rect)} 的四個角上")
    return problems, checked


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


def _row(member: dict, status: str, clause: str, message: str, length, omitted: list[int],
         checked: list[str] | None = None) -> dict:
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
        "mode": MODE_OMITTED if omitted else MODE_ORIGINAL,
        "geometry_checked": list(checked or []),
    }


def _accepted_row(member: dict, found: dict, omitted: list[int]) -> dict:
    """結束碼 0 還不夠：有 oracle 矩形的列，核心輸出必須和它對得上，否則不是「接受」。"""
    info = found.get(member["id"])
    rect = member.get("rect")
    if rect is None:
        # 沒有 oracle 矩形（手寫的探針場景）：只記核心長度，不比對。
        return _row(member, ACCEPT, "—", "", info["length"] if info else None, omitted)
    if info is None:
        return _row(
            member, MISMATCH, "—",
            "核心結束碼 0，但 stdout 沒有這支角材的輸出，無法比對 oracle 矩形",
            None, omitted,
        )
    problems, checked = geometry_problems(rect, info)
    if problems:
        return _row(member, MISMATCH, "—", "；".join(problems), info["length"], omitted, checked)
    return _row(member, ACCEPT, "—", "", info["length"], omitted, checked)


def interpret_scene(scene_name: str, scene_text: str, stdout: str = "", stderr: str = "",
                    rc: int | None = None, attempts: dict | None = None) -> dict:
    meta, members = scene_members(scene_name, scene_text)
    rows = []
    if attempts is not None:
        for member in members:
            attempt = attempts.get(member["id"])
            if attempt is None:
                row = _row(member, "未跑", "—", "", None, [])
                row["mode"] = "—"
                rows.append(row)
                continue
            omitted = list(attempt.get("omit") or [])
            verdict = classify_rc(attempt["rc"])
            if verdict == ACCEPT:
                found = core_timbers(attempt.get("out") or "")
                rows.append(_accepted_row(member, found, omitted))
            elif verdict == REJECT:
                message = first_diagnostic(attempt.get("err") or "")
                if not message:
                    message = f"（無 stderr，結束碼 {attempt['rc']}）"
                rows.append(_row(member, REJECT, clause_of(message), message, None, omitted))
            else:
                message = error_message(attempt["rc"], attempt.get("err") or "")
                rows.append(_row(member, ERROR, "—", message, None, omitted))
    elif classify_rc(rc) == ACCEPT:
        found = core_timbers(stdout or "")
        for member in members:
            rows.append(_accepted_row(member, found, []))
    elif classify_rc(rc) == ERROR:
        # 整場異常結束又沒有逐支前綴：無法歸到哪一支，每一列都是「錯誤」，不是拒絕。
        message = error_message(rc, stderr or "")
        for member in members:
            rows.append(_row(member, ERROR, "—", message, None, []))
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
                rc=full_rc,  # 缺 full.rc 就是 None，解讀成「錯誤」，不當成拒絕
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
        f"「拒絕」只指核心明確的拒絕碼（結束碼 {CORE_REJECT_RC}）。其他非 0（崩潰、訊號、逾時、沒有結束碼檔）是「錯誤」，不是規則拒絕。",
        "",
        f"「{MISMATCH}」= 結束碼 0，但核心輸出的 L／足跡／原點和 oracle 矩形對不上；不計成接受，整體結束碼非 0。",
        f"「{MODE_ORIGINAL}」= 這一列前面沒有被省略的料；「{MODE_OMITTED}」= 先前被拒（或異常）的料已拿掉再試。",
        f"「拒絕（容量）」= 訊息含「{CAPACITY_MARK}」，根本沒進放置規則；「拒絕（規則）」才是放置規則的拒絕。兩者不合計。",
        "",
        "狀態統計（括號內依探測方式拆開）：",
        *summary_lines(document),
        "",
        "| 房間 | 排法 | 角材編號 | 種類 | 核心角色 | 接受/拒絕 | 探測 | 條號 | 訊息 |",
        "|---|---|---|---|---|---|---|---|---|",
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
                _cell(member.get("mode")),
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


def status_label(member: dict) -> str:
    if member["status"] == REJECT:
        return "拒絕（容量）" if CAPACITY_MARK in (member.get("message") or "") else "拒絕（規則）"
    return member["status"]


def status_counts(document: dict) -> dict[str, dict[str, int]]:
    """{狀態標籤: {探測方式: 支數}}。拒絕拆成容量與規則；探測方式分原場景與省略後。"""
    counts: dict[str, dict[str, int]] = {}
    for scene in document["scenes"]:
        for member in scene["members"]:
            bucket = counts.setdefault(status_label(member), {})
            mode = member.get("mode") or MODE_ORIGINAL
            bucket[mode] = bucket.get(mode, 0) + 1
    return counts


def summary_lines(document: dict) -> list[str]:
    lines = []
    for label, modes in status_counts(document).items():
        detail = "／".join(f"{mode} {count}" for mode, count in sorted(modes.items()))
        lines.append(f"- {label} {sum(modes.values())}（{detail}）")
    return lines


def probe_failures(document: dict) -> int:
    """探針本身失敗的列數：核心異常結束（錯誤）加上接受了卻對不上 oracle（幾何不符）。"""
    counts = status_counts(document)
    return sum(sum(counts.get(name, {}).values()) for name in (ERROR, MISMATCH))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="彙整原生核心探針輸出")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--scenes", type=Path, default=None)
    args = parser.parse_args(argv)
    scenes = args.scenes or (args.run_dir / "scenes")
    document = parse_run(args.run_dir, scenes)
    write_outputs(document, args.run_dir)
    failures = probe_failures(document)
    if failures:
        print(
            f"{failures} 列是探針失敗（「{ERROR}」＝核心異常結束，不是規則拒絕；"
            f"「{MISMATCH}」＝接受了卻和 oracle 矩形對不上）；這次探針不完整。",
            file=sys.stderr,
        )
        return EXIT_PROBE_ERRORS
    return 0


if __name__ == "__main__":
    sys.exit(main())
