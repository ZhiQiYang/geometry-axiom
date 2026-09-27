"""Semantic persistence and malformed-input regression tests.

GEOMETRY_TEST_BRIDGE=/absolute/path/to/bridge python tests/test_bridge_integrity.py
The bridge runs only against temporary worlds; no running server is used.
"""
import json
import os
import pathlib
import re
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BRIDGE = os.environ.get("GEOMETRY_TEST_BRIDGE", str(ROOT / "geometry-web/web_bridge.exe"))


class IntegrityTests(unittest.TestCase):
    def assert_same_definitions(self, expected, actual, message=None):
        # Revision identifies an editing session/ABA, not persisted geometry.
        # Keep checking every other field, including canonical text and hash.
        self.assertIsInstance(expected.get('revision'), int)
        self.assertIsInstance(actual.get('revision'), int)
        self.assertEqual({k:v for k,v in expected.items() if k != 'revision'},
                         {k:v for k,v in actual.items() if k != 'revision'}, message)

    def bridge(self, commands):
        p = subprocess.run([BRIDGE], input="\n".join(commands) + "\n",
                           capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = [json.loads(line) for line in p.stdout.splitlines()]
        self.assertEqual(len(rows), len(commands), p.stdout)
        return rows

    def bridge_bytes(self, commands):
        """同 bridge(),但整條路都是位元組:給故意含無效 UTF-8 的輸入用,
        回傳每行原始位元組,由測試自己決定怎麼解碼(嚴格解碼失敗就是 bug)。"""
        p = subprocess.run([BRIDGE], input=b"\n".join(commands) + b"\n",
                           capture_output=True, timeout=20)
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = [line for line in p.stdout.splitlines() if line.strip()]
        self.assertEqual(len(rows), len(commands), p.stdout)
        return rows

    def test_newid_never_hands_out_an_id_already_in_use(self):
        """GEO-156:max + 1 在 uint32 上界回繞成 0,而 0 對參考線是合法 id。

        畫布拿到一個已被占用的 id,宣告出去就是交易式重宣告——既有物件被覆寫。
        修好之前這個場景會讓 newid 回 "guide":0,而 guide 0 就在場景裡。
        """
        scene_text = ("surface 1 origin 0 0 2500 u +x v +y "
                      "outline 0,0 4000,0 4000,3000 0,3000\n"
                      "spec 低 300\n"
                      "spec 高 2900\n"
                      "guide 0 1 u spec:低\n"
                      "guide 4294967295 1 u spec:高\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "id-wrap.scene"
            path.write_text(scene_text, encoding="utf-8")
            rows = self.bridge(["loadfile " + str(path), "newid", "dump"])
        self.assertTrue(rows[0]["ok"], rows[0])
        used = {int(m) for m in re.findall(r"^guide (\d+) ", rows[2]["text"], re.M)}
        self.assertEqual(used, {0, 4294967295}, "場景沒照預期把上界與 0 都占住")
        self.assertNotIn(rows[1]["guide"], used)
        # 其餘八種在這個場景裡都是空的,新 id 一律從 1 起算。
        for kind in ("boundary", "placement", "grid", "timber",
                     "space", "column", "beam", "datum"):
            with self.subTest(kind=kind):
                self.assertGreaterEqual(rows[1][kind], 1)

    # 這個世界是特地建來讓畫布的舊算法撞上的:
    #   boundary = {1, 2, 3, MAX}、placement = {4, MAX}
    #   → newid.boundary  = 4(0 是 D4 保留值跳過,1/2/3 已占用)
    #     newid.placement = 0(placement 的 0 合法且未被占用)
    #   → 舊算法 max(4, 0) = 4,而 placement 4 已經存在。
    # 夾具換過一次:GEO-159 讓 newid.boundary 跳過 0 之後,原本的
    # boundary{1,2,MAX} / placement{0,MAX} 就不再讓 max() 撞上了。
    ID_WRAP_WORLD = [
        "reset",
        "line surface 4294967295 origin 0 0 200 u +x v +y "
        "outline 0,0 100,0 100,100 0,100",
        "line boundary 1 outline 0,0 50,0 50,50 0,50",
        "line boundary 2 outline 0,0 60,0 60,60 0,60",
        "line boundary 3 outline 0,0 70,0 70,70 0,70",
        "line placement 4 on boundary 1 origin 0 0 700 u +x v +y",
    ]

    def used_ids(self, dump_text):
        used = {"boundary": set(), "placement": set()}
        for line in dump_text.splitlines():
            word = line.split()
            if len(word) > 1 and word[0] in used:
                used[word[0]].add(int(word[1]))
        return used

    def test_newid_surface_ids_are_free_in_both_id_spaces(self):
        """GEO-157:`surface N` 一行同時宣告 boundary N 與 placement N。

        所以它要的 id 必須在**兩個** id 空間裡都空。畫布原本自己用
        max(newid.boundary, newid.placement) 湊——那只在沒有回繞時成立。
        撞到既有 id 時 `surface` 是交易式重宣告,會**靜默覆寫**(回應仍是 ok:true)。
        """
        rows = self.bridge(self.ID_WRAP_WORLD + ["newid 6", "dump"])
        for command, row in zip(self.ID_WRAP_WORLD, rows):
            self.assertTrue(row["ok"], (command, row))
        fresh, used = rows[-2], self.used_ids(rows[-1]["text"])
        self.assertEqual(used["boundary"], {1, 2, 3, 4294967295})
        self.assertEqual(used["placement"], {4, 4294967295})

        ids = fresh["surfaces"]
        self.assertEqual(len(ids), 6)
        self.assertEqual(len(set(ids)), 6, "六個 id 必須彼此相異")
        for sid in ids:
            with self.subTest(sid=sid):
                self.assertNotIn(sid, used["boundary"])
                self.assertNotIn(sid, used["placement"])

        # 夾具要保有牙齒:舊算法在這個世界確實會撞上既有物件。
        # 這一條失敗代表夾具不再對抗(而不是不變式壞了)——換世界,別刪斷言。
        legacy = max(fresh["boundary"], fresh["placement"])
        self.assertIn(legacy, used["boundary"] | used["placement"],
                      "這個世界本來就是為了讓 max() 撞上才建的")

    def test_newid_surface_ids_skip_zero_and_can_be_created_after_wrap(self):
        """D4:boundary_id=0 是自帶矩形的標記,不能用來建立合體 surface。

        同時涵蓋第一個候選與同批後續候選回繞,以及回繞後要避開兩邊既有 id。
        """
        for maximum in (4294967295, 4294967294):
            for count in (1, 6):
                for occupied in (False, True):
                    with self.subTest(maximum=maximum, count=count, occupied=occupied):
                        setup = ["reset", f"line surface {maximum} origin 0 0 200 u +x v +y "
                                 "outline 0,0 100,0 100,100 0,100"]
                        if occupied:
                            setup += ["line boundary 1 outline 0,0 50,0 50,50 0,50",
                                      "line placement 2 on boundary 1 origin 0 0 700 u +x v +y"]
                        command = "newid" if count == 1 else f"newid {count}"
                        rows = self.bridge(setup + ["dump", command, "dump"])
                        self.assertTrue(all(row["ok"] for row in rows), rows)
                        self.assertEqual(rows[-3], rows[-1], "取編號不得改動世界")
                        before = rows[-1]["text"]
                        used = self.used_ids(before)
                        self.assertNotIn(0, used["boundary"] | used["placement"])
                        ids = rows[-2]["surfaces"]
                        self.assertEqual(len(ids), count)
                        self.assertEqual(len(set(ids)), count)
                        self.assertNotIn(0, ids, "surface 不得引用保留的 boundary_id=0")
                        self.assertTrue(set(ids).isdisjoint(used["boundary"] | used["placement"]))

                        # 實際宣告回傳的每個 surface,而不只是檢查 JSON 數字。
                        create = [f"line surface {sid} origin 0 0 300 u +x v +y "
                                  "outline 0,0 80,0 80,80 0,80" for sid in ids]
                        created = self.bridge(setup + create + ["dump"])
                        self.assertTrue(all(row["ok"] for row in created), created)
                        after = created[-1]["text"]
                        self.assertTrue(set(before.splitlines()).issubset(after.splitlines()),
                                        "既有物件的定義必須保留")
                        for kind, old_ids in used.items():
                            self.assertEqual(self.used_ids(after)[kind], old_ids | set(ids))

    # 柱 1 貼著牆 5 → apply-proj 走 SPLIT 分支,在同一筆交易裡配兩次新面編號。
    # 只有第六個面的編號不同:對照組 6、實驗組 uint32 上界。
    SPLIT_SCENE = """surface 1 origin 0    0    2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000
surface 2 origin 0    0    0    u +y v +x outline 0,0 3000,0 3000,4000 0,4000
surface 3 origin 0    0    0    u +x v +z outline 0,0 4000,0 4000,2500 0,2500
surface 4 origin 0    3000 0    u +z v +x outline 0,0 2500,0 2500,4000 0,4000
surface 5 origin 0    0    0    u +z v +y outline 0,0 2500,0 2500,3000 0,3000
surface {sixth} origin 4000 0    0    u +y v +z outline 0,0 3000,0 3000,2500 0,2500
space 1 boundary 1 2 3 4 5 {sixth}
column 1 in 1 at 0 1500 size 400 400
apply-proj 5 c1
"""

    def test_projection_split_ids_survive_a_save_and_reload(self):
        """GEO-158:投影拆面的配號原本是裸 max + 1,回繞會追加**重複**的 id 0。

        後果不是報錯而是資料遺失:dump 出兩行 `boundary 0`,再 loadfile 時
        後者靜默蓋掉前者——少一個面,而兩次載入都回 ok:true。
        對照組(一般編號)用來證明差異來自回繞,不是這個場景本身有問題。
        """
        for label, sixth in (("一般編號", 6), ("uint32 上界", 4294967295)):
            with self.subTest(sixth=label), tempfile.TemporaryDirectory() as tmp:
                first = pathlib.Path(tmp) / "split.scene"
                first.write_text(self.SPLIT_SCENE.format(sixth=sixth), encoding="utf-8")
                rows = self.bridge(["loadfile " + str(first), "dump"])
                self.assertTrue(rows[0]["ok"], rows[0])
                dumped = rows[1]["text"]

                used = self.used_ids(dumped)
                for kind in ("boundary", "placement"):
                    ids = [l.split()[1] for l in dumped.splitlines()
                           if l.startswith(kind + " ")]
                    self.assertEqual(len(ids), len(set(ids)), "%s 出現重複 id" % kind)
                    self.assertNotIn(0, used[kind], "%s 用到保留的 0" % kind)

                # 真正的傷害在往返:存檔再載回來必須一模一樣。
                again = pathlib.Path(tmp) / "reloaded.scene"
                again.write_text(dumped, encoding="utf-8")
                back = self.bridge(["loadfile " + str(again), "dump"])
                self.assertTrue(back[0]["ok"], back[0])
                self.assertEqual(back[1]["text"], dumped, "存檔重載後內容變了")

    def test_newid_boundary_can_actually_carry_a_placement(self):
        """GEO-159:boundary 0 建得起來,卻永遠掛不上承載面。

        D4 用 boundary_id == 0 表示「不掛邊界面、自帶矩形」,所以 0 是保留值。
        回繞時 newid.boundary 會發出 0,而 app.js 的 objEmitFace() 直接用這個欄位——
        使用者拿到成功訊息和一個死面。
        這裡不只檢查數字,而是拿它真的建一個面再掛承載面上去。
        """
        seed = ["reset", "line boundary 4294967295 outline 0,0 400,0 400,300 0,300"]
        rows = self.bridge(seed + ["newid"])
        self.assertTrue(all(row["ok"] for row in rows), rows)
        fresh = rows[-1]["boundary"]
        self.assertNotEqual(fresh, 0, "newid.boundary 發出了 D4 的保留值 0")

        used = self.bridge(seed + [
            "line boundary %d outline 0,0 200,0 200,200 0,200" % fresh,
            "line placement 5 on boundary %d origin 0 0 0 u +x v +y" % fresh])
        self.assertTrue(used[-2]["ok"], used[-2])
        self.assertTrue(used[-1]["ok"], ("newid 發出的面掛不上承載面", used[-1]))

        # 對照:0 是解析器層就拒絕的保留值(GEO-163)——證明上面那條斷言有牙齒。
        # (這個對照組原本寫「boundary 0 建得起來但掛不上承載面」,
        #  GEO-163 把它改成建都建不起來,所以前提跟著改。)
        dead = self.bridge(seed + ["line boundary 0 outline 0,0 200,0 200,200 0,200"])
        self.assertFalse(dead[-1]["ok"], "boundary 0 竟然建得起來了,這條測試需要重寫")
        self.assertIn("保留值", dead[-1]["error"])

    def test_loadfile_is_refused_inside_an_open_history_group(self):
        """GEO-160:歷史群組是行程層狀態,不在 World 裡,loadfile 的快照救不到它。

        原本 loadfile 直接跨過去:群組還開著,而 base 停在**載入前**的世界,
        之後 history-end 會把那個舊世界推進 undo 疊——按一次 undo,
        loadfile 與其後所有編輯一起消失。成功路徑也會踩到。
        規則跟 undo / redo 一致:整個世界被換掉的操作,群組進行中一律拒絕。
        """
        with tempfile.TemporaryDirectory() as tmp:
            scene = pathlib.Path(tmp) / "loaded.scene"
            scene.write_text(
                "surface 1 origin 0 0 0 u +x v +y outline 0,0 400,0 400,300 0,300\n",
                encoding="utf-8")

            # 群組進行中:拒絕,而且群組本身要維持原狀(不靜默中止)。
            rows = self.bridge(["default", "line history-begin",
                                "loadfile " + str(scene), "line history-begin"])
            self.assertTrue(rows[1]["ok"])
            self.assertFalse(rows[2]["ok"], rows[2])
            self.assertIn("歷史群組", rows[2]["error"])
            self.assertFalse(rows[3]["ok"], "群組被 loadfile 靜默關掉了")

            # abort 之後就能載入——恢復路徑必須存在,否則卡住的群組會讓開檔永久失效。
            rows = self.bridge(["default", "line history-begin",
                                "line history-abort", "loadfile " + str(scene)])
            self.assertTrue(all(row["ok"] for row in rows), rows)

            # 正常順序下,undo 必須回到「載入的世界」,不是載入前的世界。
            rows = self.bridge([
                "loadfile " + str(scene), "dump",
                "line history-begin",
                "line boundary 9 outline 0,0 50,0 50,50 0,50",
                "line history-end", "line undo", "dump"])
            self.assertTrue(all(row["ok"] for row in rows), rows)
            self.assertEqual(rows[-1]["text"], rows[1]["text"],
                             "undo 沒有回到載入的世界")

    def test_reserved_boundary_id_zero_is_refused_with_a_useful_message(self):
        """GEO-163(🔒 2026-09-21 拍板選項 B):0 在邊界面 id 空間是保留值。

        承載面用 boundary_id == 0 表示「不掛邊界面、自帶矩形」。
        原本靠哨兵撞值意外報錯,訊息答非所問:
          `surface 0 … outline …` → 「重宣告後有物件失效」(其實是首次宣告)
          `placement N on boundary 0` → 「不掛邊界面的承載面需要 rect」(其實寫了 on)
        每一條都帶對照組:換成非 0 的 id 必須成功,否則是我的指令寫錯,不是 0 的問題。
        """
        outline = "outline 0,0 400,0 400,300 0,300"
        frame = "origin 0 0 0 u +x v +y"
        for label, zero, control in (
            ("boundary 宣告",
             "line boundary 0 " + outline,
             "line boundary 7 " + outline),
            ("surface 合體宣告",
             "line surface 0 %s %s" % (frame, outline),
             "line surface 7 %s %s" % (frame, outline)),
        ):
            with self.subTest(case=label):
                bad = self.bridge(["reset", zero])[1]
                good = self.bridge(["reset", control])[1]
                self.assertTrue(good["ok"], ("對照組也失敗 → 指令寫錯", good))
                self.assertFalse(bad["ok"], bad)
                self.assertIn("保留值", bad["error"])

        # on boundary 0 是「引用」而不是宣告,也要擋,而且要講對理由。
        seed = ["reset", "line boundary 3 outline 0,0 400,0 400,300 0,300"]
        bad = self.bridge(seed + ["line placement 5 on boundary 0 " + frame])[-1]
        good = self.bridge(seed + ["line placement 5 on boundary 3 " + frame])[-1]
        self.assertTrue(good["ok"], ("對照組也失敗 → 指令寫錯", good))
        self.assertFalse(bad["ok"], bad)
        self.assertIn("保留值", bad["error"])

        # 沒有 outline 的 `surface 0` 只宣告承載面,0 對它合法——不得被誤擋。
        alive = self.bridge(["reset", "line surface 0 %s rect 0 0 400 300" % frame])[1]
        self.assertTrue(alive["ok"], ("純 placement 的 surface 0 被誤擋了", alive))

    def room_commands(self, space_id):
        room = self.SPLIT_SCENE.split("column 1", 1)[0].format(sixth=6)
        room = room.replace("space 1 boundary", f"space {space_id} boundary")
        return ["line " + line for line in room.splitlines()]

    def test_newid_space_can_own_rc_after_wrap(self):
        """GEO-164:配出的空間必須真的能擁有柱樑,並保留範圍檢查與存檔關係。"""
        for occupied in (False, True):
            with self.subTest(occupied=occupied), tempfile.TemporaryDirectory() as tmp:
                seed = ["reset", "line space 4294967295 boundary"]
                if occupied:
                    seed.append("line space 1 boundary")
                rows = self.bridge(seed + ["dump", "newid", "dump"])
                self.assertTrue(all(row["ok"] for row in rows), rows)
                self.assertEqual(rows[-3], rows[-1], "配號不得更動世界")
                fresh = rows[-2]["space"]
                self.assertGreater(fresh, 0, "space_id=0 是游離柱樑的標記")
                self.assertNotIn(fresh, {4294967295, 1} if occupied else {4294967295})

                setup = seed + self.room_commands(fresh) + [
                    f"line column 0 in {fresh} at 1000 1000 size 100 100",
                    f"line beam 0 in {fresh} along x from 500 to 1500 at 500 width 100 depth 100",
                ]
                rows = self.bridge(setup + ["dump",
                    f"line column 9 in {fresh} at 9000 9000 size 100 100 z 0 2500",
                    f"line beam 9 in {fresh} along x from 9000 to 10000 at 9000 width 100 depth 100 top 2500",
                    "dump"])
                self.assertTrue(all(row["ok"] for row in rows[:len(setup)]), rows)
                self.assertFalse(rows[-3]["ok"], "柱不得越出所屬空間")
                self.assertFalse(rows[-2]["ok"], "樑不得越出所屬空間")
                self.assertEqual(rows[-4], rows[-1], "拒絕後必須保留完整世界")
                dumped = rows[-1]["text"]
                self.assertIn(f"column 0 in {fresh} ", dumped)
                self.assertIn(f"beam 0 in {fresh} ", dumped)
                self.assertIn(" z 0 2500", dumped)
                self.assertIn(" top 2500", dumped)
                saved = pathlib.Path(tmp) / "space-wrap.scene"
                saved.write_text(dumped, encoding="utf-8")
                back = self.bridge(["loadfile " + str(saved), "dump"])
                self.assertTrue(back[0]["ok"], back[0])
                self.assertEqual(back[1]["text"], dumped)

    def test_reserved_space_zero_is_refused_without_changing_world(self):
        """明寫 in 0 不能被當成沒寫 in;各入口都有有效指令對照及載入檔案驗證。"""
        seed = ["reset"] + self.room_commands(77)
        for bad, good in (
            ("space 0 boundary", "space 88 boundary"),
            ("space 0 boundary 1 2 3 4 5 6", "space 77 boundary 1 2 3 4 5 6"),
            ("column 0 in 0 at 1000 1000 size 100 100", "column 0 in 77 at 1000 1000 size 100 100"),
            ("column 0 in 0 at 1000 1000 size 100 100 z 0 2500", "column 0 in 77 at 1000 1000 size 100 100 z 0 2500"),
            ("beam 0 in 0 along x from 500 to 1500 at 500 width 100 depth 100", "beam 0 in 77 along x from 500 to 1500 at 500 width 100 depth 100"),
            ("beam 0 in 0 along x from 500 to 1500 at 500 width 100 depth 100 top 2500", "beam 0 in 77 along x from 500 to 1500 at 500 width 100 depth 100 top 2500"),
        ):
            with self.subTest(command=bad), tempfile.TemporaryDirectory() as tmp:
                path = pathlib.Path(tmp) / "reserved-space.scene"
                path.write_text("\n".join(c[5:] for c in seed[1:]) + "\n" + bad + "\n", encoding="utf-8")
                rows = self.bridge(seed + ["dump", "line " + bad, "dump",
                                          "loadfile " + str(path), "dump", "line " + good])
                self.assertTrue(all(row["ok"] for row in rows[:len(seed)]), rows)
                before = rows[-6]
                for result, after in ((rows[-5], rows[-4]), (rows[-3], rows[-2])):
                    self.assertFalse(result["ok"], result)
                    self.assertIn("保留值", result["error"])
                    self.assertEqual(after, before)
                self.assertTrue(rows[-1]["ok"], ("有效對照組不可被誤擋", rows[-1]))

    def test_free_rc_zero_ids_and_space_deletion_still_work(self):
        """保留的是所屬空間 0,不是柱樑自己的 id 0;刪除空間仍讓柱樑游離。"""
        free = ["reset", "line column 0 at 9000 9000 size 100 100 z 0 2500",
                "line beam 0 along x from 9000 to 10000 at 9000 width 100 depth 100 top 2500", "dump"]
        rows = self.bridge(free)
        self.assertTrue(all(row["ok"] for row in rows), rows)
        self.assertIn("column 0 at ", rows[-1]["text"])
        self.assertIn("beam 0 along ", rows[-1]["text"])
        rows = self.bridge(["reset"] + self.room_commands(77) + [
            "line column 0 in 77 at 1000 1000 size 100 100",
            "line beam 0 in 77 along x from 500 to 1500 at 500 width 100 depth 100",
            "line delete space 77", "dump"])
        self.assertTrue(all(row["ok"] for row in rows), rows)
        self.assertIn("column 0 at ", rows[-1]["text"])
        self.assertIn("beam 0 along ", rows[-1]["text"])
        self.assertNotIn("space 77 ", rows[-1]["text"])

    def test_newid_rejects_a_count_it_cannot_honour(self):
        """不帶參數 = 1 個(舊行為);數量不合法一律擋掉,不得回半套。"""
        rows = self.bridge(["reset", "newid"])
        self.assertEqual(len(rows[1]["surfaces"]), 1)
        for bad in ["newid 0", "newid 17", "newid abc", "newid -1", "newid 6 7"]:
            with self.subTest(cmd=bad):
                row = self.bridge(["reset", bad])[1]
                self.assertFalse(row["ok"], row)
                self.assertNotIn("surfaces", row)

    def test_truncated_beam_preserves_world_and_connection(self):
        seeds = ["beam 1 in 1 along x from 0 to 1000 at 500 width 100 depth 100 top 2000",
                 "beam 1 along y from 0 to 1000 at 500 width 100 depth 100 top 2000"]
        for seed in seeds:
            words = seed.split()
            for n in range(1, len(words)):
                command = " ".join(words[:n])
                with self.subTest(command=command):
                    r = self.bridge(["default", "dump", "line " + command, "dump", "objects"])
                    self.assertFalse(r[2]["ok"])
                    self.assertEqual(r[1], r[3])
                    self.assertTrue(r[4]["ok"])

    def test_removed_frozen_metadata_is_rejected_atomically(self):
        for cmd in ['span-auto 3', 'place 3 on 1 at 514 27 +v +n grid-ref 1 u 0',
                    'timber 9 1000 27 33 role primary']:
            r = self.bridge(['default', 'dump', 'line ' + cmd, 'dump'])
            self.assertFalse(r[2]['ok'])
            self.assertEqual(r[1], r[3])

    def test_auto_support_and_reference_roundtrip(self):
        before = self.bridge(['loadfile ' + str(ROOT / '_role_ext_stop_primary.scene'), 'dump',
                              'line delete timber 3', 'dump'])
        self.assertTrue(before[0]['ok'], before[0])
        self.assertFalse(before[2]['ok'])
        self.assertIn('preview', before[2])
        self.assertEqual(before[1], before[3])
        self.assertIn('at-face', before[1]['text'])
        self.assertNotIn('span-auto', before[1]['text'])
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / 'edge.scene'
            path.write_text(before[1]['text'], encoding='utf-8')
            after = self.bridge(['loadfile ' + str(path), 'dump', 'line delete timber 3', 'dump'])
        self.assertTrue(after[0]['ok'], after[0])
        self.assertEqual(before[1], after[1])
        self.assertFalse(after[2]['ok'])
        self.assertEqual(after[1], after[3])

    def test_beam_centers_survive_repeated_reload(self):
        lines = []
        for axis in ['x', 'y']:
            for center in [-100, -1, 0, 100]:
                for width in [1, 2, 300, 301]:
                    lines.append(f'line beam {len(lines)+1} along {axis} from -1000 to 1000 at {center} width {width} depth 100 top 2500')
        before = self.bridge(['reset'] + lines + ['objects', 'dump', 'render'])
        self.assertTrue(all(r['ok'] for r in before))
        expected = before[-3:]
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / 'beams.scene'
            for _ in range(3):
                path.write_text(before[-2]['text'], encoding='utf-8')
                before = self.bridge(['loadfile ' + str(path), 'objects', 'dump', 'render'])
                self.assertTrue(before[0]['ok'], before[0])
                self.assertEqual(expected[0], before[-3])
                self.assert_same_definitions(expected[1], before[-2])
                self.assertEqual(expected[2], before[-1])

    def test_boundary_kind_survives_reload(self):
        for kind in ['room_plan', 'wall_elevation', 'unspecified']:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                r = self.bridge(['reset', f'line boundary 1 outline 0,0 4000,0 4000,3000 0,3000 kind {kind}', 'dump'])
                self.assertTrue(r[1]['ok'])
                if kind != 'unspecified':
                    self.assertIn('kind ' + kind, r[-1]['text'])
                path = pathlib.Path(tmp) / 'kind.scene'
                path.write_text(r[-1]['text'], encoding='utf-8')
                after = self.bridge(['loadfile ' + str(path), 'dump'])
                self.assertTrue(after[0]['ok'])
                self.assert_same_definitions(r[-1], after[-1])

    def test_failed_auto_place_restores_draft_and_redo(self):
        lines = [l for l in (ROOT / '_role_priority_primary_rc.scene').read_text(encoding='utf-8').splitlines()
                 if l.strip() and not l.startswith('#')]
        setup = ['reset'] + ['line ' + l for l in lines[:-1]]
        r = self.bridge(setup + ['line guide 90 1 u 1/2*edge:e2:v', 'line undo', 'dump',
                                 'line ' + lines[-1], 'dump', 'line redo', 'dump'])
        self.assertFalse(r[-4]['ok'])
        self.assertIn('V_CUT_PRIORITY', r[-4]['error'])
        self.assertEqual(r[-5], r[-3], 'a rejected placement must leave the draft unchanged')
        self.assertTrue(r[-2]['ok'], 'rejection must preserve redo history')
        self.assertIn('guide 90 1 u 1/2*edge:e2:v', r[-1]['text'])

    def test_drag_history_group_and_cancel(self):
        # View 2 maps ceiling u,v directly to x,y.
        setup = ['reset', 'line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
                 'line spec start 300', 'line spec middle 600', 'line spec end 900', 'line spec cancel 1200', 'line guide 1 1 u spec:start']
        r = self.bridge(setup + ['dump', 'line history-begin', 'drag 0 2 2500 600',
                                'drag 0 2 2500 900', 'line history-end', 'dump',
                                'line undo', 'dump', 'line redo', 'dump',
                                'line history-begin', 'drag 0 2 2500 1200',
                                'line history-abort', 'dump'])
        self.assertTrue(all(x['ok'] for x in r), r)
        self.assertIn('guide 1 1 u spec:end', r[-9]['text'])
        self.assert_same_definitions(r[len(setup)], r[-7], 'one undo must restore the entire gesture')
        self.assert_same_definitions(r[-9], r[-5])
        self.assert_same_definitions(r[-5], r[-1], 'cancel must restore the gesture start')
        self.assertGreater(r[-7]['revision'], r[-9]['revision'], 'undo invalidates an earlier preview')
        self.assertGreater(r[-5]['revision'], r[-7]['revision'], 'redo cannot revive an ABA preview')
        self.assertGreater(r[-1]['revision'], r[-5]['revision'], 'cancelled edits also invalidate old previews')

    def test_large_coordinates_rejected_without_mutation(self):
        commands = [
            'line boundary 8 outline 0,0 4000000000,0 4000000000,4000000000 0,4000000000',
            'line boundary 8 outline 0,0 9223372036854775807,0 9223372036854775807,3000 0,3000',
            'line placement 1 on boundary 1 origin -9223372036854775808 0 0 u +x v +y',
            'line guide 8 1 u 100000001', 'line timber 8 100000001 27 33 role primary',
            'line column 8 at 100000001 0 size 100 100 z 0 2500',
            'line beam 8 along x from 0 to 1000 at 0 width 100000001 depth 100 top 2500',
            'line grid 8 on 1 u series 0 9223372036854775807 2',
            'pick 2 9223372036854775807 0 10', 'drag 0 2 0 -9223372036854775808',
            'uv 2 4000000000 0 1', 'proj 2 4000000000 0 1', 'bhit 1 0 0 4000000000']
        for command in commands:
            with self.subTest(command=command):
                r = self.bridge(['default', 'dump', command, 'dump', 'render'])
                self.assertFalse(r[2]['ok'], command)
                self.assertEqual(r[1], r[3])
                self.assertTrue(r[4]['ok'])
        # The maximum supported definitions and full uint32 IDs remain accepted.
        r = self.bridge(['reset', 'line boundary 4294967295 outline -100000000,-100000000 100000000,-100000000 100000000,100000000 -100000000,100000000',
                         'line placement 1 on boundary 4294967295 origin 100000000 100000000 100000000 u +x v +y',
                         'render', 'dump', 'proj 2 100000000 100000000 1',
                         'uv 2 200000000 200000000 1', 'pick 2 200000000 200000000 10'])
        self.assertTrue(all(x['ok'] for x in r), r)
        self.assertEqual((r[-2]['u'], r[-2]['v']), (100000000, 100000000))

    # ---- GEO-174:fuzz(GEO-169)找到的三個「拒絕沒理由 / JSON 壞掉」 ----

    def test_loadfile_of_unplaced_timber_says_why(self):
        """收尾仍有未放置角材 → I9 整份拒絕是對的;但 parse_scene_file 那道檢查
        只印 stderr、沒記進錯誤緩衝,bridge 的 loadfile 回 {"ok":false,"error":""}。
        拒絕要有理由,而且世界不能動。"""
        scene_text = ("surface 1 origin 0 0 2500 u +x v +y "
                      "outline 0,0 4000,0 4000,3000 0,3000\n"
                      "timber 1 20 20 role primary\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "unplaced.scene"
            path.write_text(scene_text, encoding="utf-8")
            rows = self.bridge(["dump", "loadfile " + str(path), "dump"])
        self.assertFalse(rows[1]["ok"], rows[1])
        self.assertIn("沒有 place", rows[1].get("error", ""), rows[1])
        self.assertEqual(rows[0]["text"], rows[2]["text"], "loadfile 失敗卻動了世界")

    def test_bridge_json_stays_valid_utf8_when_input_is_not(self):
        """js_string 原樣吐出位元組:輸入含無效 UTF-8,JSON 串流跟著壞,
        serve.py 的 json.loads(resp.decode("utf-8")) 直接炸。輸出層要驗 UTF-8,
        本測試守的是:不論哪一層擋下,回應都必須是**嚴格合法 UTF-8** 的 JSON、而且講理由。
        修法分兩層:輸入閘門(parse_scene_file / feed_line 拒絕含壞位元組的行,見下一個測試)先擋;
        js_string 的 U+FFFD 取代是第二道防線(截斷切半個字那款由後面的測試守)。"""
        rows = self.bridge_bytes([b"line timber 1 20 20 role prim\xffary"])
        text = rows[0].decode("utf-8")          # 嚴格解碼:有無效位元組就在這裡炸
        payload = json.loads(text)
        self.assertFalse(payload["ok"], payload)
        self.assertIn("UTF-8", payload["error"], payload)   # 講理由:哪一層擋的都要說

    def test_truncated_error_never_splits_a_utf8_character(self):
        """錯誤訊息經 %.190s / 固定緩衝截斷時可能切在多位元組字元中間——
        完全合法的長中文規格名也會讓 bridge 吐出無效 UTF-8。截斷要退到字元邊界。"""
        name = "測" * 44          # 132 bytes,超過訊息截斷長度
        scene_text = ("surface 1 origin 0 0 2500 u +x v +y "
                      "outline 0,0 4000,0 4000,3000 0,3000\n"
                      "guide 1 1 u spec:" + name + "\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "longname.scene"
            path.write_text(scene_text, encoding="utf-8")
            rows = self.bridge_bytes([("loadfile " + str(path)).encode("utf-8")])
        text = rows[0].decode("utf-8")          # 嚴格解碼
        payload = json.loads(text)
        self.assertFalse(payload["ok"], payload)
        self.assertNotIn("\ufffd", payload["error"],
                         "合法輸入不該出現替代字元:截斷切在字元中間")
        self.assertIn("spec:測", payload["error"], payload)

    def test_line_with_invalid_utf8_is_rejected_before_it_enters_the_world(self):
        """fuzz seed 2 案例 301:`spec 主支2中\xff\xfe線 1500` 回 ok:true,名字帶著壞位元組
        進了世界,接著 dump 把它原樣吐進 JSON,整條串流壞掉。
        場景 DSL 是 UTF-8 文字格式:一行不是合法 UTF-8 就在解析前拒絕、講理由、世界不動。
        不能只靠輸出層換 U+FFFD——畫布看到的名字會跟世界裡的位元組不一樣,存回去就對不上(R4)。"""
        rows = self.bridge_bytes([b"reset", b"dump",
                                  b"line spec \xe4\xb8\xbb\xff\xfe\xe6\x94\xaf 500",
                                  b"dump"])
        decoded = [json.loads(r.decode("utf-8")) for r in rows]   # 嚴格解碼,四行都要是合法 JSON
        self.assertFalse(decoded[2]["ok"], decoded[2])
        self.assertIn("UTF-8", decoded[2].get("error", ""), decoded[2])
        self.assertEqual(decoded[1]["text"], decoded[3]["text"], "被拒的行不該動到世界")
        # 同一道閘門也要守場景檔:loadfile 一份含壞位元組的檔,整份拒絕、講理由、世界不動。
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "bad-utf8.scene"
            path.write_bytes(b"surface 1 origin 0 0 2500 u +x v +y "
                             b"outline 0,0 4000,0 4000,3000 0,3000\n"
                             b"spec \xe4\xb8\xbb\xff\xfe\xe6\x94\xaf 500\n")
            rows = self.bridge_bytes([b"reset", b"dump",
                                      ("loadfile " + str(path)).encode("utf-8"), b"dump"])
        decoded = [json.loads(r.decode("utf-8")) for r in rows]
        self.assertFalse(decoded[2]["ok"], decoded[2])
        self.assertIn("UTF-8", decoded[2].get("error", ""), decoded[2])
        self.assertEqual(decoded[1]["text"], decoded[3]["text"], "loadfile 失敗卻動了世界")

    def test_all_accepted_scenes_keep_geometry_and_canonical_dump(self):
        # Use the repository's accepted fixtures, including role/grid/projection combinations.
        from run_tests import TESTS
        for spec in TESTS:
            if spec["expect"] != "accept":
                continue
            with self.subTest(scene=spec["scene"]), tempfile.TemporaryDirectory() as tmp:
                before = self.bridge(["loadfile " + str(ROOT / spec["scene"]), "dump", "render"])
                self.assertTrue(before[0]["ok"], before[0])
                path = pathlib.Path(tmp) / "saved.scene"
                path.write_text(before[1]["text"], encoding="utf-8")
                after = self.bridge(["loadfile " + str(path), "dump", "render"])
                self.assertTrue(after[0]["ok"], after[0])
                self.assertEqual(before[1:], after[1:])


if __name__ == "__main__":
    unittest.main()
