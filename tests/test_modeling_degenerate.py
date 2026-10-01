"""GEO-170: degenerate-geometry inputs for geometry-core/modeling.

The 18 normative vectors in modeling-cases.json (exercised by
tests/test_modeling_runtime.py) are all well-formed constructions. This file
probes the edges MODELING-CONTRACT.md and modeling-cases.json do not cover:
holes that touch/overlap/contain/escape their outer ring, self-intersecting
outlines, duplicate/collinear vertices, reversed ring winding, zero/negative
extrusion thickness, and coordinate/volume extremes near the D1 range limit
(COORD_LIMIT = 100_000_000 mm, see geometry-core/model_base.c and
geometry-core/modeling/geometry.py's ``_LIMIT``).

Judge (each input gets exactly one of two acceptable outcomes, matching the
GEO-170 work order):
  (a) explicit rejection -- a ``ModelError`` whose ``as_dict()["diagnostics"][0]``
      carries a nonempty ``code`` and ``clause``; or
  (b) legal geometry -- a package whose objects pass
      ``tests.test_modeling_runtime.ModelingAcceptance.assert_mesh``/
      ``assert_package`` (the independent, coordinates-only mesh oracle;
      reused here, not reimplemented) and whose ``geometry_sha256`` is
      reproducible across two independent builds of the same input.

Every construction below was run against the real reference executor (not
guessed): geometry-core/modeling/base.py's C legacy-scene adapter, invoked
through GEOMETRY_MODEL_BASE exactly like test_modeling_runtime.py. Run with:

    GEOMETRY_MODEL_BASE="$TEMP/geometry-tests/model-base.exe" \
        python -m unittest tests.test_modeling_degenerate

On this machine (no system C compiler) omitting GEOMETRY_MODEL_BASE makes
every case fail identically with UNSUPPORTED/BASE_COMPILER before reaching
any of the behaviour under test here -- that is an environment gap, not a
finding (see AGENTS.md's "在 Windows 上跑測試").

Result of this pass (2026-09-21): no violations found. Every construction
below lands cleanly in (a) or (b); none produced an uncaught exception, a
self-contradictory COMPLETE mesh, a timeout, or a nondeterministic
geometry_sha256. Boundary/hole legality is enforced entirely by the C legacy
parser (current_geometry.c's poly_loop_is_valid/boundary_is_valid, D2/D3) --
before any Python modeling code runs -- so most of the requested hole/outer
relationships below are rejected at that layer with BASE_INVALID/I9. Ring
winding direction and superfluous collinear vertices are, by contrast,
accepted and produce correct closed manifolds; that is expected per R29
("exact arrangement induced by source boundary coordinates"), not a bug.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
sys.path.insert(0, str(ROOT))

from modeling import ModelError, build_package  # noqa: E402

import tests.test_modeling_runtime as runtime_suite  # noqa: E402

# Reused, not reimplemented (GEO-170 instruction): assert_mesh/assert_package
# in tests/test_modeling_runtime.py only look at exported coordinates. A bound
# instance is all that is needed to call them; the constructor just requires
# *some* existing method name on the class -- it is never run as that test.
_ORACLE = runtime_suite.ModelingAcceptance("test_hashes_are_reproducible_and_ignore_presentation")


def _extrusion_case(scene, placement_id=1, extrusion_id=50, lo="near", hi="far"):
    definitions = {"base_scene": scene, "extensions": [
        {"kind": "extrusion", "id": extrusion_id, "placement_id": placement_id,
         "lo_spec": lo, "hi_spec": hi},
    ]}
    request = {"roots": [{"kind": "extrusion", "id": extrusion_id}], "role": "geometry",
               "target": "solid-set", "allow_partial": False}
    return definitions, request


class DegenerateGeometryAcceptance(unittest.TestCase):
    """裁判見模組 docstring:每個 case 只准落在 assert_rejected 或
    assert_legal_and_reproducible 兩者之一。

    關於 BASE_INVALID/I9 的覆蓋範圍(2026-10-01 核對 bridge 實回):
    「孔與外環的關係」9 案(孔貼邊/孔頂點在邊上/孔與外角重合/孔等於外環/孔在外面/孔跨出/兩孔貼齊/
    兩孔重疊/孔含孔)加「外環本身病態」3 案(8 字自交/相鄰重複點/非相鄰重複點),共 12 案,
    在 C 解析層一律回同碼同訊息(BASE_INVALID / I9 /「邊界面輪廓不合法：邊要軸平行、不零長、
    不自交；孔要在外輪廓內且互不重疊」,diagnostics 只有這一筆)。這 12 案都在解析層被 I9 擋下,
    彼此不區分原因,屬同一守門(boundary_is_valid / poly_loop_is_valid)的覆蓋;想分辨各案究竟被
    哪一條幾何規則擋,只能改產品碼讓訊息帶原因(不在本檔範圍)。這 12 案都釘住共同訊息
    「邊界面輪廓不合法」,至少擋得住場景字串打錯後換成另一句 I9 訊息仍綠的情況。
    另兩個 BASE_INVALID/I9 案(座標超界 coordinate_exceeds_D1 與 union_of_huge_beams)的訊息是
    「座標或尺寸超出支援範圍」,與輪廓守門可區分,已用 message 參數各自釘住。"""

    def assert_rejected(self, definitions, request, status, code, clause, message=None):
        """`message`: optional substring the first diagnostic's message must contain (pins the cause where the
        code/clause pair is shared by several causes -- see the BASE_INVALID/I9 note in the class docstring)."""
        with self.assertRaises(ModelError) as caught:
            build_package(definitions, request)
        diagnostics = caught.exception.as_dict()["diagnostics"]
        self.assertTrue(diagnostics)
        diag0 = diagnostics[0]
        self.assertTrue(diag0["code"], "diagnostic code must be nonempty")
        self.assertTrue(diag0["clause"], "diagnostic clause must be nonempty")
        self.assertEqual(caught.exception.as_dict()["status"], status)
        self.assertEqual(diag0["code"], code)
        self.assertEqual(diag0["clause"], clause)
        if message is not None:
            self.assertIn(message, diag0["message"])

    def assert_legal_and_reproducible(self, definitions, request):
        package = build_package(definitions, request)
        _ORACLE.assert_package(package)
        again = build_package(definitions, request)
        self.assertEqual(package["manifest"]["geometry_sha256"],
                         again["manifest"]["geometry_sha256"],
                         "same input must yield the same geometry_sha256 twice")
        self.assertEqual(package["manifest"], again["manifest"])
        return package

    # ---- 孔與外環的相接／重疊／包含關係 -----------------------------------
    # 全部在 C legacy 場景解析層被拒(current_geometry.c 的 boundary_is_valid/
    # poly_loop_is_valid,D2/D3),Python modeling 層根本沒機會看到這些構形。
    # 這 9 案加下一節「外環本身的病態構形」3 案,共 12 案都在解析層被 I9 擋下,彼此不區分原因
    # (同碼同訊息「邊界面輪廓不合法…」),屬同一守門的覆蓋——見本類別 docstring。

    def test_hole_edge_collinear_touches_outer_edge(self):
        """孔邊與外環邊共線相接(貼齊、不重疊)。

        最小輸入:外環 4000x2800,孔 0,800 1000,800 1000,2000 0,2000
        (孔的左邊與外環左邊重合)。
        實測:INVALID / BASE_INVALID / I9。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation "
                 "hole 0,800 1000,800 1000,2000 0,2000\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "邊界面輪廓不合法")

    def test_hole_vertex_on_outer_edge(self):
        """孔頂點落在外環邊上(不共線,只有一點貼齊)。

        最小輸入:孔 0,800 2200,800 2200,2000 0,2000(左邊兩點的 u=0 落在外環左邊上)。
        實測:INVALID / BASE_INVALID / I9。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation "
                 "hole 0,800 2200,800 2200,2000 0,2000\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "邊界面輪廓不合法")

    def test_hole_shares_vertex_with_outer_corner(self):
        """孔頂點與外環角點完全重合。

        最小輸入:孔 0,0 2200,0 2200,2000 0,2000(左下角與外環左下角 0,0 重合)。
        實測:INVALID / BASE_INVALID / I9。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation "
                 "hole 0,0 2200,0 2200,2000 0,2000\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "邊界面輪廓不合法")

    def test_hole_equals_outer_outline(self):
        """孔的座標與外環完全相同(整面挖空)。

        實測:INVALID / BASE_INVALID / I9(每個孔頂點都落在外環邊上,先被 D3 擋下)。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation "
                 "hole 0,0 4000,0 4000,2800 0,2800\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "邊界面輪廓不合法")

    def test_hole_entirely_outside_outer_outline(self):
        """孔完全在外環之外。

        最小輸入:外環 x∈[0,4000],孔 x∈[5000,6000]。
        實測:INVALID / BASE_INVALID / I9。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation "
                 "hole 5000,800 6000,800 6000,2000 5000,2000\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "邊界面輪廓不合法")

    def test_hole_straddles_outer_outline(self):
        """孔跨出外環邊界(一部分在內、一部分在外)。

        最小輸入:外環 x∈[0,4000],孔 x∈[3500,4500](右邊界跨出 500)。
        實測:INVALID / BASE_INVALID / I9。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation "
                 "hole 3500,800 4500,800 4500,2000 3500,2000\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "邊界面輪廓不合法")

    def test_two_holes_touching_along_shared_edge(self):
        """兩孔沿共同邊貼齊(不重疊,只接觸)。

        最小輸入:孔 A 500,500..1500,1500,孔 B 1500,500..2500,1500(共用 u=1500 那條邊)。
        實測:INVALID / BASE_INVALID / I9
        (poly_contains_point 把邊上的點也算 contains,貼齊的頂點被當成互相落在對方內部)。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation "
                 "hole 500,500 1500,500 1500,1500 500,1500 "
                 "hole 1500,500 2500,500 2500,1500 1500,1500\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "邊界面輪廓不合法")

    def test_two_holes_overlapping(self):
        """兩孔互相重疊。

        最小輸入:孔 A 500,500..1500,1500,孔 B 1000,700..2000,1700(交集非空)。
        實測:INVALID / BASE_INVALID / I9。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation "
                 "hole 500,500 1500,500 1500,1500 500,1500 "
                 "hole 1000,700 2000,700 2000,1700 1000,1700\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "邊界面輪廓不合法")

    def test_hole_contains_another_hole(self):
        """一個孔完整包住另一個孔(孔含孔)。

        最小輸入:大孔 500,500..3000,2000,小孔 1000,900..1500,1400(完全落在大孔內)。
        實測:INVALID / BASE_INVALID / I9。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation "
                 "hole 500,500 3000,500 3000,2000 500,2000 "
                 "hole 1000,900 1500,900 1500,1400 1000,1400\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "邊界面輪廓不合法")

    # ---- 外環本身的病態構形 -------------------------------------------------
    # (這 3 案與上一節 9 案同屬「同一守門、同碼同訊息、彼此不區分原因」的 12 案。)

    def test_outer_outline_self_intersecting_figure_eight(self):
        """外環自交成 8 字形(頂點依 0,0 → 4000,2800 → 4000,0 → 0,2800 連接)。

        兩條對角邊在中心交叉,poly_loop_is_valid 的非相鄰邊相交檢查會抓到。
        實測:INVALID / BASE_INVALID / I9。
        """
        scene = ("boundary 1 outline 0,0 4000,2800 4000,0 0,2800 kind wall_elevation\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "邊界面輪廓不合法")

    def test_outer_outline_immediate_duplicate_vertex(self):
        """外環相鄰兩點重複(產生零長邊)。

        最小輸入:0,0 4000,0 4000,0 4000,2800 0,2800(4000,0 連續出現兩次)。
        實測:INVALID / BASE_INVALID / I9。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,0 4000,2800 0,2800 kind wall_elevation\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "邊界面輪廓不合法")

    def test_outer_outline_nonadjacent_duplicate_vertex_pinch(self):
        """外環非相鄰兩點座標相同,形成捏合(bowtie)。

        最小輸入:0,0 2000,0 2000,1400 2000,0 4000,0 4000,2800 0,2800
        (第 2 點與第 4 點都是 2000,0,中間先探進去再退回原點)。
        實測:INVALID / BASE_INVALID / I9。
        """
        scene = ("boundary 1 outline 0,0 2000,0 2000,1400 2000,0 4000,0 4000,2800 0,2800 "
                 "kind wall_elevation\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "邊界面輪廓不合法")

    # ---- 擠出厚度:零與負 ----------------------------------------------------

    def test_extrusion_zero_thickness(self):
        """擠出 lo_spec == hi_spec(自建向量,不動 modeling-cases.json 既有案例)。

        實測:INVALID / NON_POSITIVE_SPAN / I26。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 50\nspec far 50\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "NON_POSITIVE_SPAN", "I26")

    def test_extrusion_negative_thickness(self):
        """擠出 hi_spec < lo_spec(遠面規格值反而比近面小)。

        實測:INVALID / NON_POSITIVE_SPAN / I26(與零厚度走同一條檢查:``lo >= hi``)。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 200\nspec far 50\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "NON_POSITIVE_SPAN", "I26")

    # ---- 座標極值 / 體積溢位 --------------------------------------------------

    def test_coordinate_exceeds_D1_range_by_one(self):
        """外環頂點座標超過 COORD_LIMIT(1e8)一個單位。

        實測:INVALID / BASE_INVALID / I9,訊息含「座標或尺寸超出支援範圍」。
        """
        scene = ("boundary 1 outline 0,0 100000001,0 100000001,2800 0,2800 kind wall_elevation\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "BASE_INVALID", "I9", "座標或尺寸超出支援範圍")

    def test_extrusion_span_exceeds_D1_range(self):
        """擠出跨距本身超過 D1 支援範圍(near=-1e8, far=+1e8,跨距 2e8)。

        實測:INVALID / COORD_RANGE / I26(在 Python 層的 geometry.py 擋下,
        C 場景解析先放行,因為 near/far 各自都在 [-1e8,1e8] 內)。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\n"
                 "spec near -99000000\nspec far 99000000\n")
        self.assert_rejected(*_extrusion_case(scene), "INVALID", "COORD_RANGE", "I26")

    def test_union_of_huge_beams_exceeding_coordinate_range(self):
        """composition/UNION 的原始體座標超出 D1 範圍(top=198000000)。

        走的是 beam DSL 而非 boundary/hole,用來確認座標範圍檢查對 composition
        路徑一樣生效,不是只擋 extrusion。
        實測:INVALID / BASE_INVALID / I9。
        """
        scene = ("beam 1 along x from -99000000 to 99000000 at 0 "
                 "width 198000000 depth 198000000 top 198000000\n"
                 "beam 2 along x from -50000000 to 50000000 at 0 "
                 "width 100000000 depth 100000000 top 100000000\n")
        definitions = {"base_scene": scene, "extensions": [
            {"kind": "composition", "id": 90, "op": "UNION",
             "inputs": [{"kind": "beam", "id": 1}, {"kind": "beam", "id": 2}]},
        ]}
        request = {"roots": [{"kind": "composition", "id": 90}], "role": "geometry",
                   "target": "solid-set", "allow_partial": False}
        self.assert_rejected(definitions, request, "INVALID", "BASE_INVALID", "I9", "座標或尺寸超出支援範圍")

    # ---- 合法但反直覺的構形(裁判甲/乙的乙那一側) -----------------------------

    def test_outer_outline_collinear_extra_vertex_is_legal(self):
        """外環多一個共線頂點(5 點而非 4 點,中點與相鄰邊共線但非重複)。

        最小輸入:0,0 2000,0 4000,0 4000,2800 0,2800(2000,0 是下邊的共線中點)。
        實測:COMPLETE,mesh 通過獨立 oracle。R29 用整條環的座標建精確網格,
        多出的共線頂點會多切一條網格線,triangles 從 12 變 20、vertices 從 8 變 12,
        但體積、封閉性與雙次建置的 geometry_sha256 都與不加中點時一致
        (體積皆為 1344000000mm^3)。這是預期行為,不是缺陷。
        """
        scene = ("boundary 1 outline 0,0 2000,0 4000,0 4000,2800 0,2800 kind wall_elevation\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        package = self.assert_legal_and_reproducible(*_extrusion_case(scene))
        obj = package["derived"]["objects"][0]
        self.assertEqual(obj["closure"], "closed")
        self.assertEqual(obj["volume_mm3"], "1344000000")
        self.assertEqual(len(obj["triangles"]), 20)
        self.assertEqual(len(obj["vertices_mm"]), 12)

    def test_outer_outline_reversed_winding_is_legal(self):
        """外環頂點採順時針(而非慣例的逆時針)列出。

        最小輸入:0,0 0,2800 4000,2800 4000,0(與慣例的 0,0 4000,0 4000,2800 0,2800 反向)。
        實測:COMPLETE,mesh 通過獨立 oracle,體積與慣例繞向相同(1344000000mm^3、
        12 triangles、8 vertices)。geometry.py 的 extrusion_geometry 用
        ``_area2(ring)`` 的正負號自行正規化繞向,不論輸入順逆時針都能出正確法向。
        """
        scene = ("boundary 1 outline 0,0 0,2800 4000,2800 4000,0 kind wall_elevation\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        package = self.assert_legal_and_reproducible(*_extrusion_case(scene))
        obj = package["derived"]["objects"][0]
        self.assertEqual(obj["closure"], "closed")
        self.assertEqual(obj["volume_mm3"], "1344000000")
        self.assertEqual(len(obj["triangles"]), 12)
        self.assertEqual(len(obj["vertices_mm"]), 8)

    def test_hole_reversed_winding_is_legal(self):
        """孔的頂點採順時針列出(外環仍是慣例逆時針)。

        最小輸入取自 wall_through_hole 向量的孔座標,只把列出順序反過來
        (1000,800 1000,2000 2200,2000 2200,800)。
        實測:COMPLETE,mesh 通過獨立 oracle,體積與 modeling-cases.json 裡
        wall_through_hole 向量(慣例繞向)的預期值相同:1171200000mm^3。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation "
                 "hole 1000,800 1000,2000 2200,2000 2200,800\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        package = self.assert_legal_and_reproducible(*_extrusion_case(scene))
        obj = package["derived"]["objects"][0]
        self.assertEqual(obj["closure"], "closed")
        self.assertEqual(obj["volume_mm3"], "1171200000")

    def test_hole_with_collinear_extra_vertex_is_legal(self):
        """孔多一個共線頂點(6 點而非 4 點)。

        最小輸入:孔 1000,800 1600,800 2200,800 2200,2000 1000,2000
        (1600,800 是頂邊上的共線中點)。
        實測:COMPLETE,mesh 通過獨立 oracle,體積仍是 1171200000mm^3
        (與不加中點的 wall_through_hole 向量相同)。
        """
        scene = ("boundary 1 outline 0,0 4000,0 4000,2800 0,2800 kind wall_elevation "
                 "hole 1000,800 1600,800 2200,800 2200,2000 1000,2000\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        package = self.assert_legal_and_reproducible(*_extrusion_case(scene))
        obj = package["derived"]["objects"][0]
        self.assertEqual(obj["closure"], "closed")
        self.assertEqual(obj["volume_mm3"], "1171200000")

    def test_coordinate_extremes_positive_near_D1_limit_volume_is_string(self):
        """座標貼近 D1 上限(99000000mm)的巨大擠出,體積遠超 int64 範圍。

        最小輸入:外環 99000000 x 99000000,擠出到 99000000。
        實測:COMPLETE,mesh 通過獨立 oracle;volume_mm3 =
        "970299000000000000000000"(24 位數,遠超 int64 上限 ~9.2e18),
        以十進位字串精確表示、兩次建置一致,沒有被截斷或轉成浮點數。
        """
        scene = ("boundary 1 outline 0,0 99000000,0 99000000,99000000 0,99000000 "
                 "kind wall_elevation\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\n"
                 "spec near 0\nspec far 99000000\n")
        package = self.assert_legal_and_reproducible(*_extrusion_case(scene))
        obj = package["derived"]["objects"][0]
        self.assertEqual(obj["closure"], "closed")
        self.assertIsInstance(obj["volume_mm3"], str)
        self.assertEqual(obj["volume_mm3"], "970299000000000000000000")

    def test_coordinate_extremes_negative_near_D1_limit_volume_is_string(self):
        """座標貼近 D1 下限(-99000000mm)鏡像版本,確認負側對稱處理正確。

        實測:COMPLETE,mesh 通過獨立 oracle,體積與正側鏡像案例完全相同
        (970299000000000000000000mm^3),字串表示、可重現。
        """
        scene = ("boundary 1 outline -99000000,-99000000 0,-99000000 0,0 -99000000,0 "
                 "kind wall_elevation\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\n"
                 "spec near -99000000\nspec far 0\n")
        package = self.assert_legal_and_reproducible(*_extrusion_case(scene))
        obj = package["derived"]["objects"][0]
        self.assertEqual(obj["closure"], "closed")
        self.assertEqual(obj["volume_mm3"], "970299000000000000000000")

    def test_coordinate_exactly_at_D1_limit_is_legal(self):
        """外環頂點恰好落在 COORD_LIMIT(1e8)上(邊界值本身合法,超過才拒絕)。

        對照 test_coordinate_exceeds_D1_range_by_one(1e8+1 被拒):
        1e8 本身仍是合法輸入。
        實測:COMPLETE,mesh 通過獨立 oracle,體積 33600000000000mm^3。
        """
        scene = ("boundary 1 outline 0,0 100000000,0 100000000,2800 0,2800 "
                 "kind wall_elevation\n"
                 "placement 1 on boundary 1 origin 0 0 0 u +x v +z\nspec near 0\nspec far 120\n")
        package = self.assert_legal_and_reproducible(*_extrusion_case(scene))
        obj = package["derived"]["objects"][0]
        self.assertEqual(obj["closure"], "closed")
        self.assertEqual(obj["volume_mm3"], "33600000000000")


if __name__ == "__main__":
    unittest.main(verbosity=2)
