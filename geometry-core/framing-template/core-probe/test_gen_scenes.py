"""下角材核心探針的產生器與結果解析。只跑這個檔，不跑核心、不跑 oracle selftest。

依 opus／ChatGPT 對 #297 的審查更正，這份測試的原則：
- 驗證者不能和被驗證者共用答案。足跡、角色、放置順序都從「場景檔文字」用 scene_reader
  獨立重算，再對 golden（oracle-golden.json）與 mapping.md；不拿 gen_scenes 內部的表比 gen_scenes。
- 已提交的 scenes/*.scene 與 index.json 要和重新產生的結果逐位元相同，檔名集合也鎖住。
- 每一道檢查都有 mutation_check.py 的「突變 → 紅燈」證據。
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gen_scenes
import parse_results
import scene_reader

FIXTURES = HERE / "fixtures"
SCENES_DIR = HERE / "scenes"
INDEX_JSON = HERE / "index.json"
MAPPING_MD = HERE / "mapping.md"

P4_MESSAGE = (
    "V_CUT_PRIORITY：角材 6（優先級 2）端面頂到角材 4（優先級 2）側面"
    "——擋面擁有者優先級必須嚴格小於自己"
)
P8_MESSAGE = "V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍"
# 真實 stderr 的路徑前綴是當時的本機暫存目錄；測試只需要「檔名:行號: 訊息」的形狀。
P4_STDERR = "scenes/p4_alcove_wall_main_lower_piece.scene:15: " + P4_MESSAGE + "\n"
P8_STDERR = "scenes/p8_f1_main_first.scene:10: " + P8_MESSAGE + "\n"

# 核心對 ex3700-00 的真實 stdout 片段（2026-10-17 WSL 實跑，角材 3，截到 A0 接觸面）。
REAL_CORE_TIMBER_3 = """
=== 已放置的完整角材 ===
角材 ID：3
尺寸：L=1946，A=27，B=33 mm
角材原點：(930, 27, 2500)
長度軸：(0, 1, 0)
A 尺寸軸：(-1, 0, 0)
B 尺寸軸：(0, 0, 1)

=== 從完整角材推導六個面 ===

角材 3 的 A0（接觸面）：
  vertex[0] = (930, 27, 2500)
  vertex[1] = (903, 27, 2500)
  vertex[2] = (903, 1973, 2500)
  vertex[3] = (930, 1973, 2500)

角材 3 的 A1（另一個 A 面）：
  vertex[0] = (930, 27, 2533)
  vertex[1] = (930, 1973, 2533)
  vertex[2] = (903, 1973, 2533)
  vertex[3] = (903, 27, 2533)
"""


def _lengths(*pairs: tuple[int, int]) -> str:
    return "".join(f"角材 ID：{tid}\n尺寸：L={length}，A=27，B=33 mm\n" for tid, length in pairs)


def _core_block(ident: int, length: int, origin=None, footprint=None) -> str:
    """核心 stdout 的一支角材。origin = (x, y)；footprint = [x0, y0, x1, y1]（A0 接觸面）。"""
    text = f"\n=== 已放置的完整角材 ===\n角材 ID：{ident}\n尺寸：L={length}，A=27，B=33 mm\n"
    if origin is not None:
        text += f"角材原點：({origin[0]}, {origin[1]}, 2500)\n"
    if footprint is not None:
        x0, y0, x1, y1 = footprint
        text += (
            f"\n角材 {ident} 的 A0（接觸面）：\n"
            f"  vertex[0] = ({x0}, {y0}, 2500)\n  vertex[1] = ({x0}, {y1}, 2500)\n"
            f"  vertex[2] = ({x1}, {y1}, 2500)\n  vertex[3] = ({x1}, {y0}, 2500)\n"
        )
    return text


def _full_block(ident: int, rect, length: int | None = None, origin=None) -> str:
    """核心 stdout 的一支角材，三項（L、原點、A0 頂點）齊全且與 oracle 矩形一致；可蓋掉 length／origin 製造不符。"""
    x0, y0, x1, y1 = rect
    return _core_block(
        ident,
        max(x1 - x0, y1 - y0) if length is None else length,
        (x0, y0) if origin is None else origin,
        list(rect),
    )


def _loose_blocks(*pairs: tuple[int, int]) -> str:
    """手寫探針場景（沒有 oracle 矩形）用：每支三項齊全，內容不拿來比。"""
    return "".join(_core_block(tid, length, (0, 0), [0, 0, length, 27]) for tid, length in pairs)


def _kept_count(golden: dict) -> int:
    return sum(
        1
        for room in golden["rooms"].values()
        for layout in room["layouts"]
        if gen_scenes.layout_kept(layout)
    )


def _s1_scenes() -> dict[str, str]:
    """#240 的四個探針場景原文（fixtures/，從 PR 留言複製；只有幾何與角色，沒有路徑或帳號）。"""
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(FIXTURES.glob("p*.scene"))}


# 兩支角材的合成場景：id 1 矩形 [0,0,100,27]（長邊 100），id 2 矩形 [73,0,100,80]（長邊 80）。
SYNTH_SCENE = "\n".join([
    '# probe-meta {"layout":0,"name":"合成","room":"合成房"}',
    "surface 1 origin 0 0 2500 u +x v +y outline 0,0 100,0 100,80 0,80",
    '# probe-member {"golden":0,"id":1,"kind":"boundary","pending":null,"priority":null,"rect":[0,0,100,27],"role":"boundary"}',
    "timber 1 27 33 role boundary",
    "place 1 on 1 at-face e0 through 50 +u +n",
    '# probe-member {"golden":1,"id":2,"kind":"rc_parallel","pending":null,"priority":null,"rect":[73,0,100,80],"role":"primary"}',
    "timber 2 27 33 role primary",
    "place 2 on 1 at-face e1 through 40 +v +n",
    "",
])


def _quiet_main(argv: list[str]) -> int:
    with contextlib.redirect_stderr(io.StringIO()):
        return parse_results.main(argv)


def _write_bucket(bucket: Path, files: dict[str, str]) -> None:
    bucket.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (bucket / name).write_text(content, encoding="utf-8", newline="\n")


def mapping_declarations() -> dict[str, set[tuple[str, int | None]]]:
    """從 mapping.md 的「已對上」表讀出 oracle 種類 → {(role, priority)}。這是角色對應的唯一依據。"""
    text = MAPPING_MD.read_text(encoding="utf-8")
    section = text.split("## 已對上", 1)[1].split("\n## ", 1)[0]
    table: dict[str, set[tuple[str, int | None]]] = {}
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4 or not cells[0].startswith("`"):
            continue
        kind = cells[0].strip("`")
        role, _, priority = cells[2].strip("`").partition(" priority ")
        table.setdefault(kind, set()).add((role, int(priority) if priority else None))
    return table


# mapping.md「待 Claude 裁定」第 1 項：孔邊上、golden 種類仍是 boundary 的料，場景暫寫 secondary。
HOLE_BOUNDARY_DECLARATION = ("secondary", None)


# 使用者 2026-10-18 拍板（🔒，決策佇列「凹角沿牆料的排序」，#301）：端面頂到 custom 的副支改宣告 custom 4。
SECONDARY_ON_CUSTOM_DECLARATION = ("custom", 4)
CUSTOM4_SUFFIX = ":custom4"
SECONDARY_BASE_KINDS = ("secondary:mark", "secondary:seam", "secondary:fill")  # fill = 撞掉的記號旁補的那一支（oracle 5610d217）
SECONDARY_KINDS_WITH_CUSTOM4_IN_GOLDEN = ("secondary:mark", "secondary:seam")  # 現行 golden 裡 :custom4 只出現在這兩種


def split_label(kind: str) -> tuple[str, bool]:
    """golden 種類 → (去掉 :custom4 的種類, 是否帶 :custom4 標籤)。"""
    if kind.endswith(CUSTOM4_SUFFIX):
        return kind[: -len(CUSTOM4_SUFFIX)], True
    return kind, False


def is_secondary_like(kind: str, on_hole: bool) -> bool:
    """副支，或孔邊上暫寫 secondary 的 boundary 料。:custom4 只可能出現在這兩類。"""
    base, _ = split_label(kind)
    return base in SECONDARY_BASE_KINDS or (base == "boundary" and on_hole)


def expected_declaration(kind: str, on_hole: bool, table: dict) -> tuple[str, int | None]:
    """某支角材在場景裡該宣告的 (role, priority)。依 golden 種類（含 :custom4 標籤）與 mapping.md 的表。"""
    base, labelled = split_label(kind)
    if labelled:
        # :custom4 只能加在副支上（含孔邊暫寫 secondary 的料）；任何副支種類加上去都是 custom 4。
        # mapping.md 若為這個帶標籤的種類列了一行，那一行必須就是 custom 4。
        if not is_secondary_like(kind, on_hole):
            raise AssertionError(f"{kind}：:custom4 只能加在副支上")
        if kind in table and table[kind] != {SECONDARY_ON_CUSTOM_DECLARATION}:
            raise AssertionError(f"mapping.md 對 {kind} 列的角色不是 custom 4：{sorted(table[kind], key=str)}")
        return SECONDARY_ON_CUSTOM_DECLARATION
    if base == "boundary" and on_hole:
        return HOLE_BOUNDARY_DECLARATION
    declared = table[kind]
    if len(declared) != 1:
        raise AssertionError(f"mapping.md 對 {kind} 列了不只一種角色：{sorted(declared, key=str)}")
    return next(iter(declared))


def tier_of(member: scene_reader.Member, rect, scene: scene_reader.Scene) -> int:
    """mapping.md「放置順序」表的階：0 不延伸的外輪廓 boundary、1 primary、2 有延伸的 boundary、
    3 custom 3（沿牆料）、4 secondary 與 custom 4（端面頂到 custom 的副支）。"""
    if member.role == "primary":
        return 1
    if member.role == "custom":
        if member.priority == 3:  # 沿牆料
            return 3
        if member.priority == 4:  # 端面頂到 custom 的副支，仍是副支那一階
            return 4
        raise AssertionError(f"角材 {member.id}：custom priority {member.priority} 不在 mapping.md 裡")
    if member.role == "secondary":
        return 4
    if member.role == "boundary":
        edge = scene.edges[member.ref]
        lo, hi = (rect[0], rect[2]) if edge.axis == "x" else (rect[1], rect[3])
        return 2 if (lo < edge.lo or hi > edge.hi) else 0
    raise AssertionError(f"不認得的角色 {member.role}")


class Analysis:
    """一份場景檔文字的獨立分析：足跡、golden 配對、階、擋面。"""

    def __init__(self, name: str, text: str, golden: dict):
        self.name = name
        self.scene = scene_reader.parse_scene(text)
        self.rects = scene_reader.derive_footprints(self.scene)
        room = self.scene.meta["room"]
        layout = self.scene.meta["layout"]
        timbers = golden["rooms"][room]["layouts"][layout]["timbers"]
        by_rect = {}
        for index, (kind, raw) in enumerate(timbers):
            by_rect[tuple(raw)] = (index, kind)
        if len(by_rect) != len(timbers):
            raise AssertionError(f"{name}：golden 有重複的矩形，無法用矩形配對")
        self.golden_of = {}  # 場景角材 id -> (golden 序號, golden 種類)
        for member in self.scene.members:
            rect = self.rects[member.id]
            self.golden_of[member.id] = by_rect.get(tuple(rect)) if rect else None
        self.order = [member.id for member in self.scene.members]
        self.by_id = {member.id: member for member in self.scene.members}
        self.axes = {member.id: member.length_axis for member in self.scene.members}

    def on_hole(self, member) -> bool:
        return member.place_kind == scene_reader.PLACE_AT_FACE and member.ref.startswith("h")

    def key(self, ident: int) -> tuple[int, int]:
        member = self.by_id[ident]
        return tier_of(member, self.rects[ident], self.scene), self.golden_of[ident][0]

    def blocking_stoppers(self, ident: int) -> set[int]:
        """頂住本支兩端的角材。兩支都是 boundary 的轉角互頂不算依賴（I19 例外一、mapping.md「放置順序」）。"""
        found = set()
        for end in ("lo", "hi"):
            for other in scene_reader.end_stoppers(self.rects, self.axes, ident, end):
                if self.by_id[ident].role == "boundary" and self.by_id[other].role == "boundary":
                    continue
                found.add(other)
        return found

    def stops_on_custom(self, ident: int) -> bool:
        """本支任一端頂到的角材，在 golden 裡是 rc_parallel:custom（沿牆料或 F1 併料）。看 golden 種類，不看宣告。"""
        for end in ("lo", "hi"):
            for other in scene_reader.end_stoppers(self.rects, self.axes, ident, end):
                if self.golden_of[other][1] == "rc_parallel:custom":
                    return True
        return False

    def stopper_violations(self) -> list[str]:
        position = {ident: n for n, ident in enumerate(self.order)}
        lines = []
        for ident in self.order:
            for other in sorted(self.blocking_stoppers(ident)):
                if position[other] > position[ident]:
                    lines.append(f"{self.name}：角材 {ident} 的擋面角材 {other} 在它之後才放置")
        return lines

    def order_violations(self) -> list[str]:
        """每一步放下的那支，必須是「擋面都已放置」的未放角材裡 (階, golden 序號) 最小的。"""
        keys = {ident: self.key(ident) for ident in self.order}
        stoppers = {ident: self.blocking_stoppers(ident) for ident in self.order}
        placed: set[int] = set()
        lines = []
        for step, ident in enumerate(self.order, start=1):
            ready = [other for other in self.order if other not in placed and stoppers[other] <= placed]
            best = min(ready, key=lambda other: keys[other])
            if keys[ident] != keys[best]:
                lines.append(
                    f"{self.name}：第 {step} 步放了角材 {ident}（階,golden序號 = {keys[ident]}），"
                    f"但角材 {best} 也能放而且更前面（{keys[best]}）"
                )
                break
            placed.add(ident)
        return lines


def committed_texts() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(SCENES_DIR.glob("*.scene"))}


def committed_build(texts: dict[str, str]) -> gen_scenes.Build:
    scenes = []
    for name, text in texts.items():
        meta = scene_reader.parse_scene(text).meta
        scenes.append(gen_scenes.Scene(
            room=meta["room"], layout=meta["layout"], name=meta["name"], filename=name,
            text=text, members=[], cycles=0, pending=0, over_cap=False,
        ))
    return gen_scenes.Build(scenes, [])


def swap_first_two_blocks(text: str) -> str:
    """把第 1、2 支角材的區塊（# probe-member … place）對調，其餘不動。"""
    lines = text.split("\n")
    starts = [i for i, line in enumerate(lines) if line.startswith("# probe-member ")]
    first, second, third = starts[0], starts[1], starts[2]
    return "\n".join(lines[:first] + lines[second:third] + lines[first:second] + lines[third:])


class GenScenesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.golden = gen_scenes.load_golden()
        cls.built = gen_scenes.build(cls.golden)

    def test_scene_count_matches_buildable(self):
        kept = _kept_count(self.golden)
        self.assertEqual(kept, 64)
        self.assertEqual(len(self.built.scenes), kept)
        self.assertEqual(self.built.skipped, [])

    def test_member_rects_match_oracle(self):
        gen_scenes.assert_member_rects(self.golden, self.built)

    def test_place_matches_comment_rect(self):
        for scene in self.built.scenes:
            gen_scenes.audit_scene(scene.text)

    def test_f1_is_not_truncated_at_core_cap(self):
        for scene in self.built.scenes:
            if scene.room != "F1客廳":
                continue
            golden_count = len(self.golden["rooms"][scene.room]["layouts"][scene.layout]["timbers"])
            self.assertGreater(golden_count, gen_scenes.CORE_MAX_TIMBERS)
            self.assertEqual(len(scene.members), golden_count)
            self.assertIn(f"timbers={golden_count} core_max=64", scene.text)

    def test_rebuild_text_is_identical(self):
        again = gen_scenes.build(self.golden)
        self.assertEqual(
            [scene.text for scene in self.built.scenes],
            [scene.text for scene in again.scenes],
        )

    def test_conflict_layout_is_skipped(self):
        golden = {
            "params": {"w": 27, "L": 1, "M": 1, "P": 1, "X": 1, "gap": 1},
            "rooms": {
                "Box": {
                    "room": {"outer": [[0, 0], [200, 0], [200, 100], [0, 100]]},
                    "layouts": [
                        {
                            "buildable": True,
                            "conflict_codes": [],
                            "name": "可施工",
                            "timbers": [
                                ["boundary", [0, 0, 200, 27]],
                                ["boundary", [0, 73, 200, 100]],
                                ["main", [40, 27, 67, 73]],
                            ],
                        },
                        {
                            "buildable": False,
                            "conflict_codes": ["SYN"],
                            "name": "有衝突",
                            "timbers": [["boundary", [0, 0, 200, 27]]],
                        },
                        {
                            "buildable": True,
                            "conflict_codes": ["ALSO"],
                            "name": "旗標仍可施工但有衝突碼",
                            "timbers": [["boundary", [0, 0, 200, 27]]],
                        },
                    ],
                }
            },
        }
        built = gen_scenes.build(golden)
        self.assertEqual(len(built.scenes), 1)
        self.assertEqual([row["name"] for row in built.skipped], ["有衝突", "旗標仍可施工但有衝突碼"])
        gen_scenes.assert_member_rects(golden, built)
        gen_scenes.audit_scene(built.scenes[0].text)

    # ---- golden 的 :custom4 標籤與產生器依實際擋面的獨立判定互相核對 ----

    def _golden_with_label_edit(self, edit):
        """複製 golden，對 F2 第 0 種排法的 timbers 套 edit(timbers)，其餘不動。"""
        import copy

        golden = copy.deepcopy(self.golden)
        edit(golden["rooms"]["F2主臥"]["layouts"][0]["timbers"])
        return golden

    def test_cross_check_is_quiet_on_the_real_golden(self):
        self.assertEqual(self.built.disagreements, [])
        labelled = sum(1 for s in self.built.scenes for m in s.members if m.custom4_label)
        self.assertGreater(labelled, 0)

    def test_missing_custom4_label_is_detected(self):
        def edit(timbers):
            at = next(i for i, (kind, _r) in enumerate(timbers) if kind.endswith(":custom4"))
            timbers[at][0] = timbers[at][0][: -len(":custom4")]

        built = gen_scenes.build(self._golden_with_label_edit(edit))
        self.assertEqual(len(built.disagreements), 1)
        self.assertIn("golden 沒有 :custom4 標籤，但依實際擋面有頂到 custom", built.disagreements[0])

    def test_custom4_label_without_a_custom_stop_face_is_detected(self):
        def edit(timbers):
            # 沒標 :custom4 的 secondary:mark，真實 golden 裡它的端面都沒有頂到 custom（上一個測試證明兩邊一致）
            at = next(i for i, (kind, _r) in enumerate(timbers) if kind == "secondary:mark")
            timbers[at][0] = "secondary:mark:custom4"

        built = gen_scenes.build(self._golden_with_label_edit(edit))
        self.assertEqual(len(built.disagreements), 1)
        self.assertIn("golden 有 :custom4 標籤，但依實際擋面沒有頂到 custom", built.disagreements[0])

    def test_secondary_fill_follows_the_same_custom4_rule(self):
        """secondary:fill 也是副支：端面頂到 custom 3 時，標 :custom4 才對；沒標或標錯，交叉核對都要報。"""
        # 把一支真的頂到 custom 的 mark 改名成 fill，標籤照舊 → 角色 custom 4，沒有分歧
        def as_fill_labelled(timbers):
            at = next(i for i, (kind, _r) in enumerate(timbers) if kind.endswith(":custom4"))
            timbers[at][0] = "secondary:fill:custom4"

        built = gen_scenes.build(self._golden_with_label_edit(as_fill_labelled))
        self.assertEqual(built.disagreements, [])
        fills = [m for s in built.scenes for m in s.members if m.kind == "secondary:fill:custom4" and s.room == "F2主臥" and s.layout == 0]
        self.assertEqual(len(fills), 1)
        self.assertEqual((fills[0].role, fills[0].priority), ("custom", 4))

        # 同一支改名成 fill 且拿掉標籤 → 實際擋面頂到 custom，卻沒有標籤 → 報分歧
        def as_fill_unlabelled(timbers):
            at = next(i for i, (kind, _r) in enumerate(timbers) if kind.endswith(":custom4"))
            timbers[at][0] = "secondary:fill"

        built = gen_scenes.build(self._golden_with_label_edit(as_fill_unlabelled))
        self.assertEqual(len(built.disagreements), 1)
        self.assertIn("secondary:fill", built.disagreements[0])
        self.assertIn("沒有 :custom4 標籤，但依實際擋面有頂到 custom", built.disagreements[0])

        # 真實 golden 的 fill 沒有一支頂到 custom，也沒有標籤
        real = [m for s in self.built.scenes for m in s.members if m.kind.startswith("secondary:fill")]
        self.assertEqual(len(real), 16)
        self.assertTrue(all(m.role == "secondary" and not m.custom4_label for m in real))

    def test_custom4_label_on_a_non_secondary_is_rejected(self):
        def edit(timbers):
            at = next(i for i, (kind, _r) in enumerate(timbers) if kind == "main")
            timbers[at][0] = "main:custom4"

        with self.assertRaises(gen_scenes.ProbeError) as caught:
            gen_scenes.build(self._golden_with_label_edit(edit))
        self.assertIn(":custom4 只能加在副支上", str(caught.exception))

    def test_cli_refuses_to_write_scenes_when_labels_disagree(self):
        def edit(timbers):
            at = next(i for i, (kind, _r) in enumerate(timbers) if kind.endswith(":custom4"))
            timbers[at][0] = timbers[at][0][: -len(":custom4")]

        golden = self._golden_with_label_edit(edit)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "g.json").write_text(json.dumps(golden, ensure_ascii=False), encoding="utf-8")
            done = subprocess.run(
                [sys.executable, str(HERE / "gen_scenes.py"), "--golden", str(root / "g.json"),
                 "--out", str(root / "scenes"), "--index", str(root / "index.json")],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
            )
            wrote = (root / "scenes").exists() or (root / "index.json").exists()
        self.assertEqual(done.returncode, 2)
        self.assertIn("不產生場景", done.stderr)
        self.assertFalse(wrote)

    def test_shifted_golden_is_detected(self):
        shifted = gen_scenes.build(self.golden, delta=1)
        with self.assertRaises(AssertionError) as caught:
            gen_scenes.assert_member_rects(self.golden, shifted)
        message = str(caught.exception)
        self.assertIn("oracle [0, 0, 5000, 27]", message)
        self.assertIn("場景文字沒有算出這個矩形", message)


class SceneTextCheckerTeethTest(unittest.TestCase):
    """檢查器自己要有牙齒：手改場景文字，assert_member_rects 與順序檢查必須報錯。"""

    @classmethod
    def setUpClass(cls):
        cls.golden = gen_scenes.load_golden()
        cls.built = gen_scenes.build(cls.golden)
        cls.f2 = next(s for s in cls.built.scenes if s.room == "F2主臥" and s.layout == 0)
        # 只含 F2 第 0 種排法的小 golden，讓單一場景可以對它比。
        room = cls.golden["rooms"]["F2主臥"]
        cls.mini = {"params": cls.golden["params"], "rooms": {"F2主臥": {"room": room["room"], "layouts": [room["layouts"][0]]}}}

    def _assert_text_detected(self, text: str) -> str:
        scene = gen_scenes.Scene("F2主臥", 0, self.f2.name, "f2-00.scene", text, [], 0, 0, False)
        with self.assertRaises(AssertionError) as caught:
            gen_scenes.assert_member_rects(self.mini, gen_scenes.Build([scene], []))
        return str(caught.exception)

    def test_control_unmodified_text_passes(self):
        scene = gen_scenes.Scene("F2主臥", 0, self.f2.name, "f2-00.scene", self.f2.text, [], 0, 0, False)
        gen_scenes.assert_member_rects(self.mini, gen_scenes.Build([scene], []))

    def test_width_direction_error_is_detected(self):
        text = re.sub(r"(grid 1 on 1 u )(\d+)", lambda m: m.group(1) + str(int(m.group(2)) + 1), self.f2.text, count=1)
        self.assertNotEqual(text, self.f2.text)
        message = self._assert_text_detected(text)
        self.assertIn("oracle [6023, 27, 6050, 3573]", message)  # 格線 u0 上的主支，寬向被推走 1 mm
        self.assertIn("場景文字算出 [6024, 27, 6051, 3573]", message)

    def test_length_direction_error_is_detected(self):
        # 角材 9 貼 e1，原本夾在 t1 與 t7（長度 27..1473）；改成夾 t1 與 t2，長度變成 27..3573。
        old = "place 9 on 1 at-face e1 between t1 t7 +v +n"
        self.assertIn(old, self.f2.text)
        text = self.f2.text.replace(old, "place 9 on 1 at-face e1 between t1 t2 +v +n")
        message = self._assert_text_detected(text)
        self.assertIn("oracle [8973, 27, 9000, 1473]", message)
        self.assertIn("場景文字算出 [8973, 27, 9000, 3573]", message)

    def test_through_is_reported_as_unverifiable_length(self):
        text = self.f2.text.replace("between t1 t7 +v +n", "through 750 +v +n")
        self.assertIn("through 750", text)
        message = self._assert_text_detected(text)
        self.assertIn("長度無法由場景文字推出", message)

    def test_stop_face_placed_after_member_is_detected(self):
        lines = self.f2.text.split("\n")
        starts = [i for i, line in enumerate(lines) if line.startswith("# probe-member ")]
        first_block = lines[starts[0]:starts[1]]
        moved = "\n".join(lines[:starts[0]] + lines[starts[1]:] + first_block)  # 角材 1 搬到最後放
        with self.assertRaises(scene_reader.SceneError) as caught:
            scene_reader.derive_footprints(scene_reader.parse_scene(moved))
        self.assertIn("在它之後才放置", str(caught.exception))

    def test_order_rule_violation_is_detected(self):
        analysis = Analysis("f2-00", self.f2.text, self.golden)
        self.assertEqual(analysis.order_violations(), [])
        swapped = Analysis("f2-00-swapped", swap_first_two_blocks(self.f2.text), self.golden)
        self.assertEqual(swapped.stopper_violations(), [])  # 擋面順序沒壞，壞的是同階的 golden 序
        found = swapped.order_violations()
        self.assertEqual(len(found), 1)
        self.assertIn("第 1 步", found[0])


class CommittedScenesTest(unittest.TestCase):
    """檢查 repo 內已提交的 scenes/ 與 index.json，並對重新產生的結果做同樣的獨立檢查。"""

    @classmethod
    def setUpClass(cls):
        cls.golden = gen_scenes.load_golden()
        cls.built = gen_scenes.build(cls.golden)
        cls.committed = committed_texts()
        cls.regenerated = {scene.filename: scene.text for scene in cls.built.scenes}
        cls.table = mapping_declarations()
        cls.analyses = {}
        for source, texts in (("已提交", cls.committed), ("重新產生", cls.regenerated)):
            cls.analyses[source] = {name: Analysis(f"{source}/{name}", text, cls.golden) for name, text in texts.items()}

    def _problems(self, check) -> list[str]:
        """對已提交與重新產生的每份場景跑一個檢查；回傳所有問題（不在第一個就停）。"""
        found = []
        for items in self.analyses.values():
            for analysis in items.values():
                found.extend(check(analysis))
        return found

    def _assert_clean(self, problems: list[str]) -> None:
        self.assertEqual(problems, [], "\n".join(problems[:6]) + f"\n共 {len(problems)} 筆")

    # ---- 已提交產物逐位元鎖住（m5） ----

    def test_committed_artifacts_are_bit_identical_to_regeneration(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "scenes"
            index = Path(tmp) / "index.json"
            gen_scenes.write_build(self.built, out, index, gen_scenes.DEFAULT_GOLDEN.name)
            fresh = {path.name: path.read_bytes() for path in out.glob("*.scene")}
            fresh["index.json"] = index.read_bytes()
        committed = {path.name: path.read_bytes() for path in SCENES_DIR.glob("*.scene")}
        committed["index.json"] = INDEX_JSON.read_bytes()
        problems = []
        for name in sorted(set(fresh) | set(committed)):
            if name not in committed:
                problems.append(f"已提交的產物缺 {name}（重新產生會有）")
            elif name not in fresh:
                problems.append(f"已提交的 {name} 不是重新產生的結果（多出來的檔）")
            elif committed[name] != fresh[name]:
                if committed[name].replace(b"\r\n", b"\n") == fresh[name]:
                    problems.append(f"{name} 只差行尾（CRLF）；檢查 core-probe/.gitattributes 與 core.autocrlf")
                else:
                    problems.append(f"{name} 與重新產生的結果內容不同")
        self.assertEqual(problems, [], "\n".join(problems))
        self.assertEqual(len([n for n in fresh if n.endswith(".scene")]), 64)

    def test_committed_scenes_cover_every_buildable_layout(self):
        """不看檔名：已提交場景自己宣告的 (房間, 排法) 必須剛好是 golden 的可施工排法。"""
        wanted = {
            (room_name, index)
            for room_name, room in self.golden["rooms"].items()
            for index, layout in enumerate(room["layouts"])
            if gen_scenes.layout_kept(layout)
        }
        got = [(a.scene.meta["room"], a.scene.meta["layout"]) for a in self.analyses["已提交"].values()]
        self.assertEqual(len(got), len(set(got)), "已提交的場景有重複的 (房間, 排法)")
        self.assertEqual(set(got), wanted)
        for analysis in self.analyses["已提交"].values():
            room, layout = analysis.scene.meta["room"], analysis.scene.meta["layout"]
            self.assertEqual(analysis.scene.meta["name"], self.golden["rooms"][room]["layouts"][layout]["name"])

    # ---- 足跡：只讀場景文字，寬向與長度方向都比 ----

    def test_footprints_recomputed_from_scene_text_match_golden(self):
        gen_scenes.assert_member_rects(self.golden, self.built)
        gen_scenes.assert_member_rects(self.golden, committed_build(self.committed))

        def check(analysis):
            lines = []
            for ident in analysis.order:
                if analysis.rects[ident] is None:
                    lines.append(f"{analysis.name}：角材 {ident} 長度推不出來")
                elif analysis.golden_of[ident] is None:
                    lines.append(f"{analysis.name}：角材 {ident} 的足跡 {analysis.rects[ident]} 不在 golden")
            return lines

        self._assert_clean(self._problems(check))

    # ---- 角色與優先級：以 mapping.md 為準（m1、m3） ----

    def test_mapping_md_table_has_the_expected_kinds(self):
        self.assertEqual(
            self.table,
            {
                "boundary": {("boundary", None)},
                "main": {("primary", None)},
                "rc_parallel": {("primary", None)},
                "rc_parallel:custom": {("custom", 3)},
                "secondary:mark": {("secondary", None)},
                "secondary:seam": {("secondary", None)},
                "secondary:fill": {("secondary", None)},
                "secondary:mark:custom4": {("custom", 4)},
                "secondary:seam:custom4": {("custom", 4)},
            },
        )
        self.assertIn("場景暫寫 `secondary`", MAPPING_MD.read_text(encoding="utf-8"))

    def test_declared_roles_and_priorities_follow_mapping_md(self):
        """三方一致：場景宣告 = mapping.md 對 golden 種類（含 :custom4）的對應 = 從足跡幾何獨立算出的擋面。"""

        def check(analysis):
            lines = []
            for member in analysis.scene.members:
                index, kind = analysis.golden_of[member.id]
                on_hole = analysis.on_hole(member)
                where = "，孔邊" if on_hole else ""
                want = expected_declaration(kind, on_hole, self.table)
                have = (member.role, member.priority)
                if have != want:
                    lines.append(
                        f"{analysis.name}：角材 {member.id}（golden {index} {kind}{where}）"
                        f"場景寫 role {have[0]} priority {have[1]}，mapping.md 要 role {want[0]} priority {want[1]}"
                    )
                if is_secondary_like(kind, on_hole):
                    geometric = SECONDARY_ON_CUSTOM_DECLARATION if analysis.stops_on_custom(member.id) else ("secondary", None)
                    if have != geometric:
                        lines.append(
                            f"{analysis.name}：角材 {member.id}（golden {index} {kind}{where}）"
                            f"場景寫 role {have[0]} priority {have[1]}，但從足跡算出的實際擋面要 {geometric}"
                        )
                marker = (member.meta or {}).get("custom4")
                if (marker == "golden-label") != (have == SECONDARY_ON_CUSTOM_DECLARATION):
                    lines.append(f"{analysis.name}：角材 {member.id} 的 custom4 註解 {marker!r} 與宣告 {have} 不一致")
            return lines

        self._assert_clean(self._problems(check))

    def test_golden_custom4_labels_agree_with_actual_stop_faces(self):
        """golden 的 :custom4 標籤 vs 場景文字算出的實際擋面。不一致就紅（oracle 與探針各算各的，互相核對）。"""

        def check(analysis):
            lines = []
            for member in analysis.scene.members:
                index, kind = analysis.golden_of[member.id]
                _base, labelled = split_label(kind)
                if not is_secondary_like(kind, analysis.on_hole(member)):
                    if labelled:
                        lines.append(f"{analysis.name}：角材 {member.id}（golden {index} {kind}）不是副支卻帶 :custom4")
                    continue
                if labelled != analysis.stops_on_custom(member.id):
                    lines.append(
                        f"{analysis.name}：角材 {member.id}（golden {index} {kind}）golden "
                        f"{'有' if labelled else '沒有'} :custom4，但實際擋面{'沒有' if labelled else '有'}頂到 custom"
                    )
            return lines

        self._assert_clean(self._problems(check))

    def test_generator_cross_check_reports_no_disagreement(self):
        self.assertEqual(self.built.disagreements, [], "\n".join(self.built.disagreements[:6]))

    def test_secondaries_on_custom_are_custom_4_and_other_secondaries_stay_secondary(self):
        """使用者 2026-10-18 拍板：同一個基底種類，頂到 custom 的是 custom 4，沒頂到的仍是 secondary。"""
        seen = {}
        for analysis in self.analyses["已提交"].values():
            for member in analysis.scene.members:
                _index, kind = analysis.golden_of[member.id]
                base, labelled = split_label(kind)
                if base in SECONDARY_BASE_KINDS:
                    key = (base, analysis.stops_on_custom(member.id), (member.role, member.priority))
                    seen[key] = seen.get(key, 0) + 1
        for base in SECONDARY_BASE_KINDS:  # 含 secondary:fill：頂到 custom 的一律 custom 4，沒頂到的一律 secondary
            self.assertGreater(seen.get((base, False, ("secondary", None)), 0), 0, f"{base} 沒頂到 custom 的應仍是 secondary")
            self.assertEqual(seen.get((base, True, ("secondary", None)), 0), 0)
            self.assertEqual(seen.get((base, False, ("custom", 4)), 0), 0)
        for base in SECONDARY_KINDS_WITH_CUSTOM4_IN_GOLDEN:  # 這兩種在現行 golden 裡兩邊都有實例，確認測試沒有空轉
            self.assertGreater(seen.get((base, True, ("custom", 4)), 0), 0, f"{base} 頂到 custom 的沒有改寫 custom 4")
        for analysis in self.analyses["已提交"].values():
            for member in analysis.scene.members:
                if analysis.golden_of[member.id][1] == "rc_parallel:custom":
                    self.assertEqual((member.role, member.priority), ("custom", 3), "沿牆料本身維持 custom 3")

    def test_every_mapped_kind_occurs_in_the_scenes(self):
        """防止上一個測試空轉：每種 oracle 種類、孔邊 boundary 都真的出現在場景裡。"""
        seen = set()
        for analysis in self.analyses["已提交"].values():
            for member in analysis.scene.members:
                _index, kind = analysis.golden_of[member.id]
                seen.add((kind, analysis.on_hole(member)))
        for kind in self.table:
            self.assertTrue(any(k == kind for k, _ in seen), f"場景裡沒有 {kind}")
        self.assertTrue(any(k == "secondary:mark:custom4" for k, _ in seen))
        self.assertTrue(any(k == "secondary:seam:custom4" for k, _ in seen))
        self.assertIn(("boundary", True), seen)
        self.assertIn(("rc_parallel", True), seen)

    # ---- 放置順序（m4） ----

    def test_stop_faces_are_placed_before_the_member(self):
        self._assert_clean(self._problems(lambda analysis: analysis.stopper_violations()))

    def test_placement_follows_tier_then_oracle_order(self):
        self._assert_clean(self._problems(lambda analysis: analysis.order_violations()))


class ParseResultsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes = _s1_scenes()

    def test_fixture_has_the_four_scenes(self):
        self.assertEqual(
            set(self.scenes),
            {
                "p3_alcove_side_boundary_then_main.scene",
                "p4_alcove_wall_main_lower_piece.scene",
                "p8_f1_main_first.scene",
                "p9_f1_custom_inner_wall.scene",
            },
        )

    def test_p3_and_p9_accepted_lengths(self):
        p3 = parse_results.interpret_scene(
            "p3_alcove_side_boundary_then_main",
            self.scenes["p3_alcove_side_boundary_then_main.scene"],
            stdout=_loose_blocks((1, 4000), (2, 4000), (3, 2946), (4, 1287), (5, 1287)),
            stderr="",
            rc=0,
        )
        self.assertEqual(
            [(row["status"], row["core_length"], parse_results.core_role_text(row["role"], row["priority"], row["pending"]))
             for row in p3["members"]],
            [
                ("接受", 4000, "boundary"),
                ("接受", 4000, "boundary"),
                ("接受", 2946, "primary"),
                ("接受", 1287, "boundary"),
                ("接受", 1287, "boundary"),
            ],
        )
        p9 = parse_results.interpret_scene(
            "p9_f1_custom_inner_wall",
            self.scenes["p9_f1_custom_inner_wall.scene"],
            stdout=_loose_blocks((1, 5000), (2, 3200), (3, 4746), (4, 2222), (5, 1773)),
            stderr="",
            rc=0,
        )
        self.assertEqual(
            [(row["core_length"], parse_results.core_role_text(row["role"], row["priority"], row["pending"]))
             for row in p9["members"]],
            [
                (5000, "boundary"),
                (3200, "boundary"),
                (4746, "primary"),
                (2222, "boundary"),
                (1773, "custom priority 3"),
            ],
        )
        self.assertTrue(all(row["status"] == "接受" for row in p9["members"]))

    def test_p4_and_p8_name_one_reject(self):
        p4 = parse_results.interpret_scene(
            "p4_alcove_wall_main_lower_piece",
            self.scenes["p4_alcove_wall_main_lower_piece.scene"],
            stdout="",
            stderr=P4_STDERR,
            rc=1,
        )
        by_id = {row["id"]: row for row in p4["members"]}
        self.assertEqual(by_id[6]["status"], "拒絕")
        self.assertEqual(by_id[6]["clause"], "I19")
        self.assertEqual(by_id[6]["message"], P4_MESSAGE)
        for number in range(1, 6):
            self.assertEqual(by_id[number]["status"], "同場未提交")
            self.assertEqual(by_id[number]["message"], "")
        p8 = parse_results.interpret_scene(
            "p8_f1_main_first",
            self.scenes["p8_f1_main_first.scene"],
            stdout="",
            stderr=P8_STDERR,
            rc=1,
        )
        by_id = {row["id"]: row for row in p8["members"]}
        self.assertEqual(by_id[3]["status"], "拒絕")
        self.assertEqual(by_id[3]["clause"], "I22")
        self.assertEqual(by_id[3]["message"], P8_MESSAGE)
        for number in (1, 2, 4):
            self.assertEqual(by_id[number]["status"], "同場未提交")

    def test_prefix_overrides_full_scene(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenes = root / "scenes"
            scenes.mkdir()
            (scenes / "synth.scene").write_text(SYNTH_SCENE, encoding="utf-8", newline="\n")
            _write_bucket(root / "synth", {
                "full.rc": "1\n",
                "full.err": "synth.scene:3: V_CUT_PRIORITY：角材 1（優先級 2）端面頂到角材 1\n",
                "full.out": "",
                "m001.rc": "0\n",
                "m001.out": _full_block(1, [0, 0, 100, 27]),
                "m001.err": "",
                "m001.omit": "",
                "m002.rc": "1\n",
                "m002.out": "",
                "m002.err": "synth.scene:8: " + P8_MESSAGE.replace("（3）", "（2）") + "\n",
                "m002.omit": "\n",
            })
            document = parse_results.parse_run(root, scenes)
        members = document["scenes"][0]["members"]
        self.assertEqual(members[0]["status"], "接受")
        self.assertEqual(members[0]["core_length"], 100)
        self.assertEqual(members[1]["status"], "拒絕")
        self.assertEqual(members[1]["clause"], "I22")
        self.assertEqual(members[1]["message"], P8_MESSAGE.replace("（3）", "（2）"))
        self.assertEqual(document["scenes"][0]["room"], "合成房")
        self.assertEqual(document["scenes"][0]["name"], "合成")

    # ---- 結束碼分類：rc=1 且 stderr 帶核心規則診斷才算拒絕 ----

    def test_only_the_core_reject_code_is_a_rejection(self):
        self.assertEqual(parse_results.CORE_REJECT_RC, 1)
        attempts = {
            1: {"rc": 0, "out": _full_block(1, [0, 0, 100, 27]), "err": "", "omit": []},
            2: {"rc": 1, "out": "", "err": "synth.scene:8: " + P8_MESSAGE + "\n", "omit": [1]},
        }
        item = parse_results.interpret_scene("synth", SYNTH_SCENE, rc=1, attempts=attempts)
        self.assertEqual([row["status"] for row in item["members"]], ["接受", "拒絕"])
        for bad_rc, expect in ((139, "訊號 11"), (134, "訊號 6"), (2, "不是核心的拒絕碼"), (124, "逾時"), (127, "不是核心的拒絕碼"), (None, "沒有結束碼檔")):
            with self.subTest(rc=bad_rc):
                attempts[2] = {"rc": bad_rc, "out": "", "err": "Segmentation fault (fake)\n", "omit": [1]}
                item = parse_results.interpret_scene("synth", SYNTH_SCENE, rc=1, attempts=attempts)
                row = item["members"][1]
                self.assertEqual(row["status"], "錯誤")
                self.assertNotEqual(row["status"], "拒絕")
                self.assertEqual(row["clause"], "—")
                self.assertIn(expect, row["message"])
                self.assertIn("不是規則拒絕", row["message"])

    # 取自 current_geometry.c／references.inc 的真實訊息形狀。rc=1 的 stderr 第一行（去掉「路徑:行號:」）
    # 帶 V_* 代碼、I／R／D 編號或「超過上限」才是規則診斷。
    RULE_DIAGNOSTICS = (
        "scenes/x.scene:15: " + P4_MESSAGE,
        "scenes/x.scene:10: " + P8_MESSAGE,
        "scenes/x.scene:9: R6(d): 端面需要恰好一個涵蓋全寬的合法擋面",
        "scenes/x.scene:9: D7/I18: timber id A尺寸 B尺寸 role 必填",
        "scenes/x.scene:9: D4: placement variant cannot change",  # 只有 D 編號，沒有 I／R／V_
        "scenes/x.scene:9: I25a: source rule capability/highwater closure missing",
        "scenes/x.scene:9: I13/R6：子格 [0,100] 內沒有兩端獲得支撐的完整跨距",
        "scenes/x.scene:65: 角材的數量超過上限",
        "scenes/x.scene:7: grid u 座標超過上限",
    )
    NON_RULE_DIAGNOSTICS = (
        "scenes/x.scene:3: timber 行有多餘欄位",
        "scenes/x.scene:4: 不認得的指令（boundary placement surface space guide timber place move column beam delete reset canvas-pos）",
        "scenes/x.scene:5: outline 後面要接至少四個 u,v 頂點",
        "/var/tmp/D1/I22/x.scene:0: 無法開啟場景檔",  # 路徑裡的 D1／I22 不算
        "場景裡沒有任何物件。",
        "--scene 後面要接場景檔路徑。",
        "不認得的參數：--bogus；請用 --help 查看用法。",
        "scenes/x.scene:8: 這支角材不存在",  # 沒有記號的語意訊息保守歸「錯誤」
        "",
    )

    def test_rc1_with_a_parse_or_usage_error_is_an_error_not_a_rejection(self):
        for text in self.NON_RULE_DIAGNOSTICS:
            with self.subTest(stderr=text):
                self.assertEqual(parse_results.classify_rc(1, text + "\n"), "錯誤")
                attempts = {
                    1: {"rc": 0, "out": _full_block(1, [0, 0, 100, 27]), "err": "", "omit": []},
                    2: {"rc": 1, "out": "", "err": text + "\n", "omit": [1]},
                }
                row = parse_results.interpret_scene("synth", SYNTH_SCENE, rc=1, attempts=attempts)["members"][1]
                self.assertEqual(row["status"], "錯誤")
                self.assertEqual(row["clause"], "—")
                self.assertIn("沒有核心規則診斷", row["message"])
                self.assertIn("不是規則拒絕", row["message"])

    def test_rc1_with_a_rule_diagnostic_is_a_rejection(self):
        for text in self.RULE_DIAGNOSTICS:
            with self.subTest(stderr=text):
                self.assertEqual(parse_results.classify_rc(1, text + "\n"), "拒絕")
                self.assertEqual(parse_results.classify_rc(2, text + "\n"), "錯誤")  # 規則記號救不了錯的結束碼
                self.assertEqual(parse_results.classify_rc(139, text + "\n"), "錯誤")

    def test_whole_scene_rc1_parse_error_without_prefix_is_error(self):
        item = parse_results.interpret_scene("synth", SYNTH_SCENE, stdout="", stderr="synth.scene:3: timber 行有多餘欄位\n", rc=1)
        self.assertEqual([row["status"] for row in item["members"]], ["錯誤", "錯誤"])
        item = parse_results.interpret_scene("synth", SYNTH_SCENE, stdout="", stderr="", rc=1)
        self.assertEqual([row["status"] for row in item["members"]], ["錯誤", "錯誤"])

    def test_whole_scene_crash_without_prefix_is_error_not_rejection(self):
        for bad_rc in (139, 2, 124, None):
            with self.subTest(rc=bad_rc):
                item = parse_results.interpret_scene("synth", SYNTH_SCENE, stdout="", stderr="", rc=bad_rc)
                self.assertEqual([row["status"] for row in item["members"]], ["錯誤", "錯誤"])

    def test_parse_run_exit_code_is_nonzero_for_core_errors(self):
        parse_error = "synth.scene:8: timber 行有多餘欄位\n"
        rule_error = "synth.scene:8: " + P8_MESSAGE + "\n"
        for label, rc_text, err_text, expect_failure in (
            ("segv", "139\n", rule_error, True),
            ("usage", "2\n", rule_error, True),
            ("timeout", "124\n", rule_error, True),
            ("rc1-parse-error", "1\n", parse_error, True),
            ("rc1-no-stderr", "1\n", "", True),
            ("reject", "1\n", rule_error, False),
        ):
            with self.subTest(core=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                scenes = root / "scenes"
                scenes.mkdir()
                (scenes / "synth.scene").write_text(SYNTH_SCENE, encoding="utf-8", newline="\n")
                _write_bucket(root / "synth", {
                    "full.rc": rc_text, "full.out": "", "full.err": "boom\n",
                    "m001.rc": "0\n", "m001.out": _full_block(1, [0, 0, 100, 27]), "m001.err": "", "m001.omit": "",
                    "m002.rc": rc_text, "m002.out": "", "m002.err": err_text, "m002.omit": "\n",
                })
                code = _quiet_main(["--run-dir", str(root), "--scenes", str(scenes)])
                results = json.loads((root / "results.json").read_text(encoding="utf-8"))
                statuses = [row["status"] for row in results["scenes"][0]["members"]]
                markdown = (root / "RESULTS.md").read_text(encoding="utf-8")
            if expect_failure:
                self.assertEqual(code, parse_results.EXIT_PROBE_ERRORS)
                self.assertEqual(statuses, ["接受", "錯誤"])
                self.assertIn("- 錯誤 1", markdown)
            else:
                self.assertEqual(code, 0)
                self.assertEqual(statuses, ["接受", "拒絕"])

    def test_missing_full_rc_is_error_not_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenes = root / "scenes"
            scenes.mkdir()
            (scenes / "synth.scene").write_text(SYNTH_SCENE, encoding="utf-8", newline="\n")
            (root / "synth").mkdir()
            document = parse_results.parse_run(root, scenes)
        self.assertEqual([row["status"] for row in document["scenes"][0]["members"]], ["錯誤", "錯誤"])

    # ---- 接受列的幾何等值：合法但長度錯不能算接受 ----

    def _accepted(self, stdout: str, rc: int = 0):
        return parse_results.interpret_scene("synth", SYNTH_SCENE, stdout=stdout, stderr="", rc=rc)["members"]

    def test_real_core_stdout_format_is_parsed(self):
        found = parse_results.core_timbers(REAL_CORE_TIMBER_3)
        self.assertEqual(found, {3: {"length": 1946, "origin": (930, 27), "footprint": [903, 27, 930, 1973]}})
        problems, checked = parse_results.geometry_problems([903, 27, 930, 1973], found[3])
        self.assertEqual((problems, checked), ([], ["L", "足跡", "原點"]))

    R1 = [0, 0, 100, 27]  # SYNTH_SCENE 的兩支 oracle 矩形
    R2 = [73, 0, 100, 80]

    def test_accepted_rows_match_oracle_rect(self):
        rows = self._accepted(_full_block(1, self.R1) + _full_block(2, self.R2, origin=(100, 0)))
        self.assertEqual([row["status"] for row in rows], ["接受", "接受"])
        self.assertEqual(rows[0]["geometry_checked"], ["L", "足跡", "原點"])

    def test_legal_but_wrong_length_is_not_accepted(self):
        # 核心結束碼 0、輸出看起來合法，只是 L 差 1 mm：必須是「幾何不符」。
        rows = self._accepted(_full_block(1, self.R1) + _full_block(2, self.R2, length=79))
        self.assertEqual([row["status"] for row in rows], ["接受", "幾何不符"])
        self.assertIn("核心 L=79", rows[1]["message"])
        self.assertIn("長邊 80", rows[1]["message"])

    def test_wrong_footprint_or_origin_is_not_accepted(self):
        rows = self._accepted(_core_block(1, 100, (0, 0), [0, 0, 99, 27]) + _full_block(2, self.R2))
        self.assertEqual(rows[0]["status"], "幾何不符")
        self.assertIn("核心足跡 [0, 0, 99, 27]", rows[0]["message"])
        rows = self._accepted(_core_block(1, 100, (5, 5), self.R1) + _full_block(2, self.R2))
        self.assertEqual(rows[0]["status"], "幾何不符")
        self.assertIn("不在 oracle 矩形", rows[0]["message"])

    def test_accepted_member_missing_from_core_output_is_not_accepted(self):
        rows = self._accepted(_full_block(1, self.R1))
        self.assertEqual([row["status"] for row in rows], ["接受", "幾何不符"])
        self.assertIn("沒有這支角材的輸出", rows[1]["message"])

    def test_accepted_rows_must_have_length_origin_and_footprint(self):
        """缺任何一項都不算接受（ChatGPT 複審：缺欄不得被靜默接受）。反轉舊測試「只有 L 也接受」。"""
        good2 = _full_block(2, self.R2)
        cases = {
            "只有 L": (_core_block(1, 100), ["角材原點", "A0 接觸面頂點"]),
            "缺原點": (_core_block(1, 100, None, self.R1), ["角材原點"]),
            "缺 A0 頂點": (_core_block(1, 100, (0, 0), None), ["A0 接觸面頂點"]),
        }
        for label, (block1, missing) in cases.items():
            with self.subTest(case=label):
                rows = self._accepted(block1 + good2)
                self.assertEqual([row["status"] for row in rows], ["幾何不符", "接受"])
                self.assertIn("缺欄", rows[0]["message"])
                for name in missing:
                    self.assertIn(name, rows[0]["message"])
                self.assertEqual(parse_results.status_label(rows[0]), "幾何不符")

    def test_missing_fields_are_also_rejected_without_an_oracle_rect(self):
        scene = self.scenes["p3_alcove_side_boundary_then_main.scene"]
        pairs = ((1, 4000), (2, 4000), (3, 2946), (4, 1287), (5, 1287))
        loose = parse_results.interpret_scene("p3", scene, stdout=_lengths(*pairs), rc=0)
        self.assertEqual([row["status"] for row in loose["members"]], ["幾何不符"] * 5)
        full = parse_results.interpret_scene("p3", scene, stdout=_loose_blocks(*pairs), rc=0)
        self.assertEqual([row["status"] for row in full["members"]], ["接受"] * 5)
        self.assertEqual(full["members"][0]["geometry_checked"], [])  # 沒有 oracle 矩形：欄位齊全但沒比

    def test_geometry_mismatch_makes_the_exit_code_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenes = root / "scenes"
            scenes.mkdir()
            (scenes / "synth.scene").write_text(SYNTH_SCENE, encoding="utf-8", newline="\n")
            _write_bucket(root / "synth", {
                "full.rc": "0\n",
                "full.out": _full_block(1, self.R1) + _full_block(2, self.R2, length=79),
                "full.err": "",
            })
            code = _quiet_main(["--run-dir", str(root), "--scenes", str(scenes)])
        self.assertEqual(code, parse_results.EXIT_PROBE_ERRORS)

    # ---- 總結：容量與規則分開、原場景與省略後探測分開 ----

    def test_summary_separates_capacity_from_rules_and_original_from_omitted(self):
        capacity = "V_TIMBER_CAP：角材的數量超過上限（64）"
        attempts = {
            1: {"rc": 1, "out": "", "err": "synth.scene:3: " + P4_MESSAGE + "\n", "omit": []},
            2: {"rc": 1, "out": "", "err": "synth.scene:8: " + capacity + "\n", "omit": [1]},
        }
        item = parse_results.interpret_scene("synth", SYNTH_SCENE, rc=1, attempts=attempts)
        document = {"scenes": [item]}
        self.assertEqual([row["mode"] for row in item["members"]], ["原場景", "省略後探測"])
        counts = parse_results.status_counts(document)
        self.assertEqual(counts, {"拒絕（規則）": {"原場景": 1}, "拒絕（容量）": {"省略後探測": 1}})
        markdown = parse_results.render_markdown(document)
        self.assertIn("- 拒絕（規則） 1（原場景 1）", markdown)
        self.assertIn("- 拒絕（容量） 1（省略後探測 1）", markdown)


def _find_git_or_posix_bash() -> str | None:
    """找一個真的 bash。Windows 的 System32\\bash.exe 是 WSL 的啟動器，絕不使用。"""
    candidates = []
    found = shutil.which("bash")
    if found:
        candidates.append(found)
    if os.name == "nt":
        candidates += [r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"]
    for candidate in candidates:
        lowered = candidate.lower().replace("/", "\\")
        if "\\windows\\" in lowered or "windowsapps" in lowered:
            continue
        if Path(candidate).exists():
            return candidate
    return None


FAKE_CORE = r"""#!/bin/bash
# 假核心：行為由 FAKE_MODE 決定，用來測 run_probe.sh 的結束碼分類。不是原生核心。
# 對 ONE_MEMBER_SCENE 的角材 1（oracle 矩形 [0,0,100,27]）印出核心 stdout 的三項：L、角材原點、A0 接觸面頂點。
block_l()      { printf '\n=== 已放置的完整角材 ===\n角材 ID：1\n尺寸：L=%s，A=27，B=33 mm\n' "$1"; }
block_origin() { printf '角材原點：(0, 0, 2500)\n'; }
block_a0()     { printf '\n角材 1 的 A0（接觸面）：\n  vertex[0] = (0, 0, 2500)\n  vertex[1] = (0, 27, 2500)\n  vertex[2] = (100, 27, 2500)\n  vertex[3] = (100, 0, 2500)\n'; }
case "${FAKE_MODE:-}" in
  segv)     echo "Segmentation fault (fake)" >&2; exit 139 ;;
  usage)    echo "usage: core [options] (fake)" >&2; exit 2 ;;
  hang)     exec sleep 30 ;;
  reject)   echo "fake.scene:5: V_CUT_PRIORITY：角材 1（優先級 2）端面頂到角材 1（優先級 2）側面" >&2; exit 1 ;;
  capacity) echo "fake.scene:5: 角材的數量超過上限" >&2; exit 1 ;;
  parseerr) echo "fake.scene:3: timber 行有多餘欄位" >&2; exit 1 ;;
  nofile)   echo "fake.scene:0: 無法開啟場景檔" >&2; exit 1 ;;
  silent1)  exit 1 ;;
  accept)   block_l 100; block_origin; block_a0; exit 0 ;;
  wrongL)   block_l 99; block_origin; block_a0; exit 0 ;;
  onlyL)    block_l 100; exit 0 ;;
  noorigin) block_l 100; block_a0; exit 0 ;;
  nofoot)   block_l 100; block_origin; exit 0 ;;
esac
exit 99
"""

ONE_MEMBER_SCENE = "\n".join([
    '# probe-meta {"layout":0,"name":"一支","room":"假核心房"}',
    "surface 1 origin 0 0 2500 u +x v +y outline 0,0 100,0 100,80 0,80",
    '# probe-member {"golden":0,"id":1,"kind":"boundary","pending":null,"priority":null,"rect":[0,0,100,27],"role":"boundary"}',
    "timber 1 27 33 role boundary",
    "place 1 on 1 at-face e0 through 50 +u +n",
    "",
])


@unittest.skipUnless(
    _find_git_or_posix_bash() and not os.environ.get("PROBE_SKIP_FAKE_CORE"),
    "沒有 bash（或只有 WSL 啟動器），或設了 PROBE_SKIP_FAKE_CORE；跳過 run_probe.sh 的假核心回歸",
)
class RunProbeFakeCoreTest(unittest.TestCase):
    """用假核心（bash 腳本，不編譯、不跑原生程式、不碰 WSL）端到端跑 run_probe.sh。"""

    @classmethod
    def setUpClass(cls):
        cls.bash = _find_git_or_posix_bash()
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.core = root / "fake_core.sh"
        cls.core.write_text(FAKE_CORE, encoding="utf-8", newline="\n")
        cls.scenes = root / "in_scenes"
        cls.scenes.mkdir()
        (cls.scenes / "one.scene").write_text(ONE_MEMBER_SCENE, encoding="utf-8", newline="\n")
        cls.root = root

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _run(self, mode: str):
        out = self.root / f"out_{mode}"
        work_tmp = self.root / "work"
        work_tmp.mkdir(exist_ok=True)
        env = dict(os.environ)
        env.update({
            "CORE_BIN": self.core.as_posix(),
            "PROBE_SCENES_DIR": self.scenes.as_posix(),
            "PYTHON": Path(sys.executable).as_posix(),
            "CORE_TIMEOUT": "2",
            "TMPDIR": work_tmp.as_posix(),
            "FAKE_MODE": mode,
        })
        done = subprocess.run(
            [self.bash, (HERE / "run_probe.sh").as_posix(), out.as_posix()],
            env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
        )
        results = json.loads((out / "results.json").read_text(encoding="utf-8"))
        statuses = [row["status"] for scene in results["scenes"] for row in scene["members"]]
        messages = " ".join(row["message"] for scene in results["scenes"] for row in scene["members"])
        return done.returncode, statuses, messages, (out / "summary.txt").read_text(encoding="utf-8")

    def test_segfault_139_is_an_error_and_the_run_fails(self):
        rc, statuses, messages, summary = self._run("segv")
        self.assertEqual(statuses, ["錯誤"])
        self.assertIn("訊號 11", messages)
        self.assertEqual(rc, parse_results.EXIT_PROBE_ERRORS)
        self.assertIn("errors=1", summary)

    def test_usage_error_2_is_an_error_and_the_run_fails(self):
        rc, statuses, _messages, _summary = self._run("usage")
        self.assertEqual(statuses, ["錯誤"])
        self.assertEqual(rc, parse_results.EXIT_PROBE_ERRORS)

    def test_timeout_is_an_error_and_the_run_fails(self):
        rc, statuses, messages, _summary = self._run("hang")
        self.assertEqual(statuses, ["錯誤"])
        self.assertIn("逾時", messages)
        self.assertEqual(rc, parse_results.EXIT_PROBE_ERRORS)

    def test_core_reject_code_1_is_a_rejection_and_the_run_succeeds(self):
        rc, statuses, _messages, summary = self._run("reject")
        self.assertEqual(statuses, ["拒絕"])
        self.assertEqual(rc, 0)
        self.assertIn("rejected=1 errors=0", summary)

    def test_accept_with_matching_length_succeeds(self):
        rc, statuses, _messages, _summary = self._run("accept")
        self.assertEqual((rc, statuses), (0, ["接受"]))

    def test_accept_with_wrong_length_fails_the_run(self):
        rc, statuses, messages, _summary = self._run("wrongL")
        self.assertEqual(statuses, ["幾何不符"])
        self.assertIn("長邊 100", messages)
        self.assertEqual(rc, parse_results.EXIT_PROBE_ERRORS)

    def test_accept_with_missing_fields_fails_the_run(self):
        for mode in ("onlyL", "noorigin", "nofoot"):
            with self.subTest(mode=mode):
                rc, statuses, messages, _summary = self._run(mode)
                self.assertEqual(statuses, ["幾何不符"])
                self.assertIn("缺欄", messages)
                self.assertEqual(rc, parse_results.EXIT_PROBE_ERRORS)

    def test_rc1_with_a_parse_error_is_an_error_not_a_rejection(self):
        for mode in ("parseerr", "nofile", "silent1"):
            with self.subTest(mode=mode):
                rc, statuses, messages, summary = self._run(mode)
                self.assertEqual(statuses, ["錯誤"])
                self.assertIn("沒有核心規則診斷", messages)
                self.assertEqual(rc, parse_results.EXIT_PROBE_ERRORS)
                self.assertIn("rejected=0 errors=1", summary)  # run_probe.sh 的計數與 parse_results 一致

    def test_rc1_with_a_capacity_message_is_a_rejection_not_an_error(self):
        rc, statuses, messages, summary = self._run("capacity")
        self.assertEqual(statuses, ["拒絕"])
        self.assertIn("超過上限", messages)
        self.assertEqual(rc, 0)
        self.assertIn("rejected=1 errors=0", summary)

    def test_shell_and_python_rule_predicates_agree(self):
        """run_probe.sh 的 rule_diag 與 parse_results.is_rule_diagnostic 對同一批真實訊息的判斷必須相同。"""
        text = (HERE / "run_probe.sh").read_text(encoding="utf-8")
        match = re.search(r"^rule_diag\(\) \{\n.*?^\}\n", text, re.M | re.S)
        self.assertIsNotNone(match, "找不到 run_probe.sh 的 rule_diag 函式")
        samples = ParseResultsTest.RULE_DIAGNOSTICS + ParseResultsTest.NON_RULE_DIAGNOSTICS
        for sample in samples:
            with self.subTest(stderr=sample):
                path = self.root / "diag.err"
                path.write_text(sample + "\n", encoding="utf-8", newline="\n")
                done = subprocess.run(
                    [self.bash, "-c", match.group(0) + f'\nrule_diag "{path.as_posix()}"'],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                )
                shell_says = done.returncode == 0
                python_says = parse_results.classify_rc(1, sample + "\n") == "拒絕"
                self.assertEqual(shell_says, python_says, f"shell {shell_says} / python {python_says}：{sample!r}")


if __name__ == "__main__":
    unittest.main()
