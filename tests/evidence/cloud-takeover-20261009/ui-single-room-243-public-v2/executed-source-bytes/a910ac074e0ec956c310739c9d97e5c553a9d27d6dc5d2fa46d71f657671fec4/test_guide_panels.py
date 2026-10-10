#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""導讀頁面板守門(GEO-175)。

`geometry-guide/check_panels.py` 對目前的 current_geometry.c 逐面板找符號與 callout;
GEO-100 起就規定「改 C 要同步 make_guide.py 的 callout」,但沒有測試守門,
於是從 2026-09-18 一路飄到 8 個 unresolved 才被發現。這裡讓它會紅。
修法:改 make_guide.py 的面板設定 → `python geometry-guide/make_guide.py` 重產 → 本測試綠。
"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class GuidePanels(unittest.TestCase):
    def test_every_panel_and_callout_resolves(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "geometry-guide", "check_panels.py")],
            capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("unresolved: none", proc.stdout)


if __name__ == "__main__":
    unittest.main()
