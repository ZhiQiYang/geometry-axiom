"""下角材核心探針的產生器與結果解析。只跑這個檔，不跑核心、不跑 oracle selftest。"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gen_scenes
import parse_results

S1_COMMENT = Path(
    r"C:\Users\Yang\AppData\Local\Temp\claude\D--geometry-axiom"
    r"\f46787ac-6918-4891-81a1-b3d8a9aa653c\scratchpad\s1-probe\scenes-comment.md"
)

P4_MESSAGE = (
    "V_CUT_PRIORITY：角材 6（優先級 2）端面頂到角材 4（優先級 2）側面"
    "——擋面擁有者優先級必須嚴格小於自己"
)
P8_MESSAGE = "V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍"
P4_STDERR = (
    "/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/"
    "f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/s1-probe/"
    "p4_alcove_wall_main_lower_piece.scene:15: " + P4_MESSAGE + "\n"
)
P8_STDERR = (
    "/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/"
    "f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/s1-probe/"
    "p8_f1_main_first.scene:10: " + P8_MESSAGE + "\n"
)


def _lengths(*pairs: tuple[int, int]) -> str:
    return "".join(f"角材 ID：{tid}\n尺寸：L={length}，A=27，B=33 mm\n" for tid, length in pairs)


def _kept_count(golden: dict) -> int:
    return sum(
        1
        for room in golden["rooms"].values()
        for layout in room["layouts"]
        if gen_scenes.layout_kept(layout)
    )


def _s1_scenes(text: str) -> dict[str, str]:
    found = re.findall(r"\*\*(p\d+_[^*]+?\.scene)\*\*\s*```[^\n]*\n(.*?)```", text, re.S)
    return {name: body for name, body in found}


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

    def test_shift_is_detected(self):
        shifted = gen_scenes.build(self.golden, delta=1)
        with self.assertRaises(AssertionError) as caught:
            gen_scenes.assert_member_rects(self.golden, shifted)
        self.assertIn("共 1 支不符", str(caught.exception))
        self.assertIn("[1, 0, 5001, 27]", str(caught.exception))


class ParseResultsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = S1_COMMENT.read_text(encoding="utf-8")
        cls.scenes = _s1_scenes(text)

    def test_comment_file_has_the_four_scenes(self):
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
            stdout=_lengths((1, 4000), (2, 4000), (3, 2946), (4, 1287), (5, 1287)),
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
            stdout=_lengths((1, 5000), (2, 3200), (3, 4746), (4, 2222), (5, 1773)),
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
        scene = "\n".join([
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
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenes = root / "scenes"
            scenes.mkdir()
            (scenes / "synth.scene").write_text(scene, encoding="utf-8", newline="\n")
            bucket = root / "synth"
            bucket.mkdir()
            (bucket / "full.rc").write_text("1\n", encoding="utf-8")
            (bucket / "full.err").write_text("synth.scene:3: V_CUT_PRIORITY：角材 1（優先級 2）端面頂到角材 1\n", encoding="utf-8")
            (bucket / "full.out").write_text("", encoding="utf-8")
            (bucket / "m001.rc").write_text("0\n", encoding="utf-8")
            (bucket / "m001.out").write_text(_lengths((1, 100)), encoding="utf-8")
            (bucket / "m001.err").write_text("", encoding="utf-8")
            (bucket / "m001.omit").write_text("", encoding="utf-8")
            (bucket / "m002.rc").write_text("1\n", encoding="utf-8")
            (bucket / "m002.out").write_text("", encoding="utf-8")
            (bucket / "m002.err").write_text("synth.scene:8: " + P8_MESSAGE.replace("（3）", "（2）") + "\n", encoding="utf-8")
            (bucket / "m002.omit").write_text("\n", encoding="utf-8")
            document = parse_results.parse_run(root, scenes)
        members = document["scenes"][0]["members"]
        self.assertEqual(members[0]["status"], "接受")
        self.assertEqual(members[0]["core_length"], 100)
        self.assertEqual(members[1]["status"], "拒絕")
        self.assertEqual(members[1]["clause"], "I22")
        self.assertEqual(members[1]["message"], P8_MESSAGE.replace("（3）", "（2）"))
        self.assertEqual(document["scenes"][0]["room"], "合成房")
        self.assertEqual(document["scenes"][0]["name"], "合成")


if __name__ == "__main__":
    unittest.main()
