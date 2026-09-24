#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回報收件匣儲存層與 CLI(GEO-183)。不需要 bridge;寫進暫存目錄,不碰 repo 的 feedback/。"""
import base64
import datetime
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-web"))
import feedback_store as store  # noqa: E402
import feedback_cli as cli  # noqa: E402

PNG = "data:image/png;base64," + base64.b64encode(
    bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                  "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")).decode()


def payload(**kw):
    p = {"kind": "bug", "note": "放不上去", "t_mark": 2000,
         "target": {"el": "button#btnUndo", "text": "復原", "rect": [1, 2, 3, 4]},
         "context": {"view": "主畫布(工具 select)", "scene": "room_a.scene", "viewport": "1382×900",
                     "state": {"oc": {"focus": None}}},
         "events": [{"k": "click", "el": "button#btnUndo", "t": 1000},
                    {"k": "api", "cmd": "line place 3 on 1 at-line guide 1", "ok": False, "error": "I19: 那條邊還沒鋪邊界材", "t": 1500},
                    {"k": "api", "cmd": "boundary 1", "ok": True, "t": 1600}],
         "world": "spec 主支中線 500\n", "page": "<!doctype html><html></html>", "screenshot": PNG}
    p.update(kw)
    return p


class FeedbackStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["GEOMETRY_FEEDBACK_DIR"] = self.tmp.name

    def tearDown(self):
        os.environ.pop("GEOMETRY_FEEDBACK_DIR", None)
        self.tmp.cleanup()

    def run_cli(self, *argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.main(list(argv))
        return code, buf.getvalue()

    def test_save_writes_all_artifacts_and_inbox(self):
        r = store.save(payload(), now=datetime.datetime(2026, 9, 24, 14, 3, 22))
        self.assertEqual(r["id"], "F-20260924-001")
        d = pathlib.Path(r["path"])
        for f in ("meta.json", "report.md", "events.jsonl", "world.scene", "page.html", "screenshot.png"):
            self.assertTrue((d / f).exists(), f)
        self.assertEqual((d / "screenshot.png").read_bytes()[:4], b"\x89PNG")
        report = (d / "report.md").read_text(encoding="utf-8")
        for s in ("放不上去", "button#btnUndo", "I19: 那條邊還沒鋪邊界材", "-1.0s", "room_a.scene", "world.scene"):
            self.assertIn(s, report)
        inbox = (pathlib.Path(self.tmp.name) / "INBOX.md").read_text(encoding="utf-8")
        self.assertIn("F-20260924-001", inbox)
        self.assertIn("open", inbox)

    def test_ids_increment_per_day(self):
        t = datetime.datetime(2026, 9, 24, 9)
        ids = [store.save(payload(), now=t)["id"] for _ in range(3)]
        self.assertEqual(ids, ["F-20260924-001", "F-20260924-002", "F-20260924-003"])
        self.assertEqual(store.save(payload(), now=t + datetime.timedelta(days=1))["id"], "F-20260925-001")

    def test_rejects_bad_payloads(self):
        for bad in (None, [], {"kind": "nope"}, {"kind": "bug", "events": "x"}):
            with self.assertRaises(store.FeedbackError):
                store.save(bad)
        self.assertEqual(list(pathlib.Path(self.tmp.name).glob("F-*")), [])

    def test_non_png_screenshot_and_missing_world_are_skipped(self):
        r = store.save(payload(screenshot="data:text/html;base64,PHA+", world=""))
        d = pathlib.Path(r["path"])
        self.assertFalse((d / "screenshot.png").exists())
        self.assertFalse((d / "world.scene").exists())

    def test_cli_list_show_close_roundtrip(self):
        fid = store.save(payload())["id"]
        code, out = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertIn(fid, out)
        self.assertIn("button#btnUndo", out)
        code, out = self.run_cli("show", fid)
        self.assertIn("I19", out)
        code, out = self.run_cli("close", fid, "已修 abc1234")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((pathlib.Path(self.tmp.name) / fid / "meta.json").read_text(encoding="utf-8"))["status"], "closed")
        self.assertIn("已修 abc1234", (pathlib.Path(self.tmp.name) / fid / "report.md").read_text(encoding="utf-8"))
        code, out = self.run_cli("list")
        self.assertIn("沒有未處理", out)
        code, out = self.run_cli("list", "--all")
        self.assertIn(fid, out)

    def test_cli_replay_lists_only_mutating_commands(self):
        fid = store.save(payload())["id"]
        os.environ["GEOMETRY_CORE"] = str(pathlib.Path(self.tmp.name) / "no-core.exe")
        try:
            code, out = self.run_cli("replay", fid)
        finally:
            os.environ.pop("GEOMETRY_CORE", None)
        self.assertIn("✗ line place 3 on 1 at-line guide 1", out)
        self.assertNotIn("boundary 1", out.split("==")[2])
        self.assertIn("找不到 core.exe", out)

    def test_cli_rejects_bad_ids(self):
        code, out = self.run_cli("show", "../etc")
        self.assertEqual(code, 1)
        self.assertIn("格式不對", out)


if __name__ == "__main__":
    unittest.main()
