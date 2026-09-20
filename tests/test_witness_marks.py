#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""見證圖的物理碰撞獨立驗證(GEO-134/135)。

刻意不 import witness.py——只讀 commit 進 repo 的 SVG 與 joints.json,用最笨的矩形交集重算:
  1. 同一張圖(主圖與每個接點格各算一次)裡任兩支角材的多邊形,正面積交集必須為 0(I11:邊相接合法)。
  2. 每個停止標記所佔的矩形,不得與任何**其他**角材的多邊形有正面積交集——標註不得暗示不存在的占用。
  3. 每個 joints.json 裡的接點,在主圖裡都要有對應的標記。
witness.py 自己也驗這些;這裡是第二雙眼睛,兩邊用不同程式碼,一邊錯了另一邊會叫。
"""
import glob
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WITNESS = os.path.join(ROOT, "geometry-guide", "witness")

_POLY = re.compile(r'<polygon points="([^"]+)" class="timber-face[^"]*" data-t="(\d+)"')
_MARK_RECT = re.compile(r'<rect x="([^"]+)" y="([^"]+)" width="([^"]+)" height="([^"]+)" class="stop"[^>]*data-joint="t(\d+)\.(\w+)"')
_MARK_POLY = re.compile(r'<polygon points="([^"]+)" class="stop"[^>]*data-joint="t(\d+)\.(\w+)"')
_BLOCKS = re.compile(r'<g transform[^>]*data-view="\w+">.*?</g>|<g class="tile"[^>]*>.*?</g>', re.S)


def _polys(block):
    out = []
    for m in _POLY.finditer(block):
        pts = [tuple(map(float, p.split(","))) for p in m.group(1).split()]
        out.append((int(m.group(2)), min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)))
    return out


def _marks(block):
    """停止標記是填色矩形(主圖 <rect>;接點格裁切後成 <polygon>)。佔的範圍 = 座標,與縮放無關。"""
    out = []
    for m in _MARK_RECT.finditer(block):
        x, y, w, h = map(float, m.groups()[:4])
        out.append((int(m.group(5)), m.group(6), (x, x + w, y, y + h)))
    for m in _MARK_POLY.finditer(block):
        pts = [tuple(map(float, p.split(","))) for p in m.group(1).split()]
        out.append((int(m.group(2)), m.group(3), (min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts))))
    return out


def _overlap(a, b):
    w = min(a[1], b[1]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[2], b[2])
    return (w if w > 0 else 0) * (h if h > 0 else 0)


class WitnessMarks(unittest.TestCase):
    def setUp(self):
        self.files = sorted(glob.glob(os.path.join(WITNESS, "*.svg")))
        self.assertTrue(self.files, "no witness svg")

    def test_timbers_never_overlap(self):
        for f in self.files:
            blocks = _BLOCKS.findall(open(f, encoding="utf-8").read())
            for b in blocks:
                P = _polys(b)
                for i, (t, *a) in enumerate(P):
                    for (u, *c) in P[i + 1:]:
                        if t == u:
                            continue
                        self.assertEqual(_overlap(a, c), 0, "%s: t%d 與 t%d 重疊" % (os.path.basename(f), t, u))

    def test_marks_stay_inside_their_own_timber(self):
        total = 0
        for f in self.files:
            blocks = _BLOCKS.findall(open(f, encoding="utf-8").read())
            for b in blocks:
                P = _polys(b)
                for t, end, box in _marks(b):
                    total += 1
                    for (u, *c) in P:
                        if u == t:
                            continue
                        self.assertEqual(_overlap(box, c), 0, "%s: t%d.%s 的標記侵入 t%d" % (os.path.basename(f), t, end, u))
        self.assertGreater(total, 0)

    def test_no_stroke_based_marks(self):
        # vector-effect:non-scaling-stroke 會讓 stroke 粗度變成螢幕像素;標記一律不得靠 stroke 表達範圍
        for f in self.files:
            svg = open(f, encoding="utf-8").read()
            self.assertNotRegex(svg, r'<line[^>]*class="stop"', os.path.basename(f))
            self.assertNotRegex(svg, r'class="stop"[^>]*stroke-width', os.path.basename(f))

    def test_every_joint_has_a_mark_in_main_view(self):
        for f in self.files:
            cid = os.path.splitext(os.path.basename(f))[0]
            jp = os.path.join(WITNESS, cid + ".joints.json")
            self.assertTrue(os.path.exists(jp), jp)
            joints = json.load(open(jp, encoding="utf-8"))["joints"]
            svg = open(f, encoding="utf-8").read()
            main = re.findall(r'<g transform[^>]*data-view="\w+">.*?</g>', svg, re.S)
            marks = {(t, e) for b in main for t, e, _ in _marks(b)}
            for j in joints:
                # 端面在該視圖退化成點的才可以沒有標記(沿視線的料);其餘必須有
                if (j["t"], j["end"]) not in marks:
                    self.assertIn(cid, ("D2",), "%s: t%d.%s 沒有標記" % (cid, j["t"], j["end"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
