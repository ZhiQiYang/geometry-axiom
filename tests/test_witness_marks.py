#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""見證圖的物理碰撞獨立驗證(GEO-134/135)。

刻意不 import witness.py——只讀 commit 進 repo 的 SVG 與 joints.json,用最笨的矩形交集重算:
  1. 同一張圖(主圖與每個接點格各算一次)裡任兩支角材的多邊形,正面積交集必須為 0(I11:邊相接合法)。
  2. 每個停止標記必須在自身角材內,且不得與任何**其他**角材的多邊形有正面積交集。
  3. 每個 joints.json 裡的接點,在主圖裡都要有對應的標記。
witness.py 自己也驗這些;這裡是第二雙眼睛,兩邊用不同程式碼,一邊錯了另一邊會叫。
"""
import glob
import json
import math
import os
from pathlib import Path
import re
import unittest
from collections import Counter
from unittest import mock
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WITNESS = os.path.join(ROOT, "geometry-guide", "witness")

def _tag(element):
    return element.tag.rsplit("}", 1)[-1]


def _classes(element):
    return set(element.get("class", "").split())


def _is_timber(element):
    return "timber-face" in _classes(element) or "data-t" in element.attrib


def _is_mark(element):
    return "stop" in _classes(element) or (_tag(element) != "g" and "data-joint" in element.attrib)


def _rect_box(element):
    x, y, w, h = (float(element.attrib[k]) for k in ("x", "y", "width", "height"))
    if not all(map(math.isfinite, (x, y, w, h))) or w <= 0 or h <= 0:
        raise AssertionError("invalid rectangle")
    return x, x + w, y, y + h


def _drawing(svg):
    """Use the XML tree, not serialization order or a regex ending at the first </g>."""
    root = ET.fromstring(svg)
    blocks = [e for e in root.iter() if _tag(e) == "g" and
              ("data-view" in e.attrib or "tile" in _classes(e))]
    for block in blocks:
        for element in block.iter():
            # Shared group transforms preserve relative containment. A local
            # transform changes rendered geometry but not the coordinates this
            # oracle checks; fail rather than pretend to evaluate its matrix.
            if (element is not block and "transform" in element.attrib and
                    (_tag(element) == "g" or _is_timber(element) or _is_mark(element))):
                raise AssertionError("local geometry transform is unsupported by this oracle")
    # The fixed legend has one unbound stop swatch. Account for it explicitly:
    # only a direct root rect without a joint, inside the declared legend box,
    # followed by legend text can be the sample (規範 §1, §2).
    children = list(root)
    legend_boxes = [_rect_box(e) for e in children if _tag(e) == "rect" and "legend-box" in _classes(e)]
    samples = set()
    for index, element in enumerate(children[:-1]):
        if (_tag(element) == "rect" and _is_mark(element) and "data-joint" not in element.attrib
                and "legend-text" in _classes(children[index + 1])):
            box = _rect_box(element)
            if any(c[0] <= box[0] <= box[1] <= c[1] and c[2] <= box[2] <= box[3] <= c[3]
                   for c in legend_boxes):
                samples.add(element)
    if len(samples) > 1:
        raise AssertionError("more than one legend stop sample")
    for name, predicate in (("timber", _is_timber), ("stop", _is_mark)):
        # Inventory actual nodes before decoding their geometry. Unknown shapes,
        # orphan nodes and nodes included by two groups must not disappear.
        all_nodes = Counter(e for e in root.iter() if predicate(e) and e not in samples)
        grouped_nodes = Counter(e for b in blocks for e in b.iter() if predicate(e))
        if all_nodes != grouped_nodes:
            raise AssertionError(name + " geometry must belong to exactly one main/tile group")
    return root, blocks


def _point_box(element):
    coords = [float(n) for n in re.split(r"[\s,]+", element.attrib["points"].strip())]
    if len(coords) < 6 or len(coords) % 2 or not all(map(math.isfinite, coords)):
        raise AssertionError("invalid polygon coordinates")
    return min(coords[::2]), max(coords[::2]), min(coords[1::2]), max(coords[1::2])


def _polys(block):
    out = []
    for element in block.iter():
        if not _is_timber(element):
            continue
        if _tag(element) != "polygon" or "timber-face" not in _classes(element):
            raise AssertionError("unsupported timber geometry: " + _tag(element))
        out.append((int(element.attrib["data-t"]), *_point_box(element)))
    return out


def _marks(block):
    """停止標記是填色矩形(主圖 <rect>;接點格裁切後成 <polygon>)。佔的範圍 = 座標,與縮放無關。"""
    out = []
    for element in block.iter():
        if not _is_mark(element):
            continue
        joint = re.fullmatch(r"t(\d+)\.(START|END)", element.get("data-joint", ""))
        if "stop" not in _classes(element) or joint is None:
            raise AssertionError("invalid stop mark identity")
        if _tag(element) == "rect":
            box = _rect_box(element)
        elif _tag(element) == "polygon":
            box = _point_box(element)
        else:
            raise AssertionError("unsupported stop geometry: " + _tag(element))
        out.append((int(joint.group(1)), joint.group(2), box))
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
        parsed = 0
        for f in self.files:
            svg = Path(f).read_text(encoding="utf-8")
            _, blocks = _drawing(svg)
            for b in blocks:
                P = _polys(b)
                parsed += len(P)
                for i, (t, *a) in enumerate(P):
                    for (u, *c) in P[i + 1:]:
                        if t == u:
                            continue
                        self.assertEqual(_overlap(a, c), 0, "%s: t%d 與 t%d 重疊" % (os.path.basename(f), t, u))
        self.assertGreater(parsed, 0, "no timber geometry was inspected")

    def test_marks_stay_inside_their_own_timber(self):
        total = 0
        for f in self.files:
            svg = Path(f).read_text(encoding="utf-8")
            _, blocks = _drawing(svg)
            for b in blocks:
                P = _polys(b)
                for t, end, box in _marks(b):
                    total += 1
                    owners = [c for u, *c in P if u == t]
                    self.assertTrue(owners, "%s: t%d.%s 標記沒有對應角材" % (os.path.basename(f), t, end))
                    self.assertTrue(any(c[0] <= box[0] <= box[1] <= c[1] and
                                        c[2] <= box[2] <= box[3] <= c[3] for c in owners),
                                    "%s: t%d.%s 標記超出自身角材" % (os.path.basename(f), t, end))
                    for (u, *c) in P:
                        if u == t:
                            continue
                        self.assertEqual(_overlap(box, c), 0, "%s: t%d.%s 的標記侵入 t%d" % (os.path.basename(f), t, end, u))
        self.assertGreater(total, 0)

    def test_no_stroke_based_marks(self):
        # vector-effect:non-scaling-stroke 會讓 stroke 粗度變成螢幕像素;標記一律不得靠 stroke 表達範圍
        for f in self.files:
            svg = Path(f).read_text(encoding="utf-8")
            root, _ = _drawing(svg)
            for mark in (e for e in root.iter() if _is_mark(e)):
                self.assertIn(_tag(mark), ("rect", "polygon"), os.path.basename(f))
                self.assertNotIn("stroke-width", mark.attrib, os.path.basename(f))
                self.assertNotRegex(mark.get("style", ""), r"(?:^|;)\s*stroke-width\s*:", os.path.basename(f))

    def test_every_joint_has_a_mark_in_main_view(self):
        for f in self.files:
            cid = os.path.splitext(os.path.basename(f))[0]
            jp = os.path.join(WITNESS, cid + ".joints.json")
            self.assertTrue(os.path.exists(jp), jp)
            joints = json.loads(Path(jp).read_text(encoding="utf-8"))["joints"]
            svg = Path(f).read_text(encoding="utf-8")
            _, blocks = _drawing(svg)
            main = [b for b in blocks if "data-view" in b.attrib]
            marks = {(t, e) for b in main for t, e, _ in _marks(b)}
            for j in joints:
                # Current fixtures have a visible main-view mark for every joint,
                # including D2's wall frame. A filename is not a degeneracy proof.
                self.assertIn((j["t"], j["end"]), marks,
                              "%s: t%d.%s 沒有標記" % (cid, j["t"], j["end"]))


class WitnessParsingControls(unittest.TestCase):
    def test_real_tile_mark_cannot_escape_by_reordering_svg_attributes(self):
        path = Path(WITNESS) / "D10a.svg"
        source = path.read_text(encoding="utf-8")

        def check(svg):
            case = WitnessMarks("test_marks_stay_inside_their_own_timber")
            case.files = [str(path)]
            with mock.patch.object(Path, "read_text", return_value=svg):
                case.test_marks_stay_inside_their_own_timber()

        root, blocks = _drawing(source)
        tile = next(b for b in blocks if "tile" in _classes(b))
        mark = next(e for e in tile.iter() if _is_mark(e))
        original = dict(mark.attrib)
        # A nested harmless g and arbitrary attribute order are valid SVG.
        tile.remove(mark)
        nested = ET.SubElement(tile, "g")
        nested.append(mark)
        mark.attrib.clear()
        mark.attrib.update({"class": original["class"], "data-joint": original["data-joint"],
                            "points": original["points"]})
        check(ET.tostring(root, encoding="unicode"))
        # Translating a whole view preserves this oracle's relative geometry;
        # translating just one mark, timber or nested group must never pass.
        tile.set("transform", "translate(1000000 1000000)")
        check(ET.tostring(root, encoding="unicode"))
        del tile.attrib["transform"]
        timber = next(e for e in tile.iter() if _is_timber(e))
        for target in (mark, timber, nested):
            with self.subTest(local_transform=_tag(target)):
                target.set("transform", "translate(1000000 1000000)")
                with self.assertRaisesRegex(AssertionError, "local geometry transform is unsupported"):
                    check(ET.tostring(root, encoding="unicode"))
                del target.attrib["transform"]
        for reordered in (False, True):
            with self.subTest(reordered=reordered):
                bad_points = "999990,999990 999999,999990 999999,999999 999990,999999"
                mark.attrib.clear()
                if reordered:
                    mark.attrib.update({"class": "stop", "points": bad_points,
                                        "data-joint": original["data-joint"]})
                else:
                    mark.attrib.update({**original, "points": bad_points})
                with self.assertRaisesRegex(AssertionError, "標記超出自身角材"):
                    check(ET.tostring(root, encoding="unicode"))

    def test_geometry_outside_main_or_tile_is_not_silently_ignored(self):
        for kind, element in (("timber", '<polygon class="timber-face" data-t="1" points="0,0 1,0 1,1"/>'),
                              ("stop", '<rect class="stop" data-joint="t1.START" x="0" y="0" width="1" height="1"/>')):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(AssertionError, kind + " geometry must belong"):
                    _drawing('<svg xmlns="http://www.w3.org/2000/svg">' + element + '</svg>')


if __name__ == "__main__":
    unittest.main(verbosity=2)
