# -*- coding: utf-8 -*-
"""Edits for issue #316 (dead world_footprint_collides and I11 same-surface filter mutation coverage)."""
import re

NATIVE = "geometry-templates/woodworking/native/"
CG = "current_geometry.c"

SCENE_PATH = "_i11_two_surfaces_same_uv_accept.scene"
SCENE = '''# 公理:I11(同一承載面上,任兩支已放角材的足跡正面積不得相交;不同承載面不互比)、D2(承載面各有自己的 frame)。#316。
# 兩片承載面各放一支 boundary:
#   天花板 surface 1(z=2500、u +x v +y、4000×3000):timber 1 貼 e0,足跡 u∈[0,4000]、v∈[0,20];
#   牆 surface 3(y=0、u +x v +z、3000×2500):timber 2 貼 e0,足跡 u∈[0,3000]、v∈[0,20]。
# 兩支在各自局部座標下的足跡正面積重疊(u∈[0,3000]、v∈[0,20]),但分屬不同承載面,I11 不互比 → 接受,長度 4000、3000。
# 單一承載面的場景分不出「只比同承載面」這道過濾有沒有被拿掉。本場景是 M97(geometry-core/references.inc 的
# reference_check_all 兩兩檢查)與 M98(W world_validation.c 的最終世界兩兩檢查)拿掉過濾後會轉紅的場景:
# 跨面配對被拿去比,整個世界被拒(那是預期的紅,不是本場景的瑕疵)。
surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000
surface 3 origin 0 0 0 u +x v +z outline 0,0 3000,0 3000,2500 0,2500
timber 1 20 20 role boundary
timber 2 20 20 role boundary
place 1 on 1 at-face e0 +u +n
place 2 on 3 at-face e0 +u +n
'''

CONSUMERS_OLD = None  # filled from the file at edit time

HELPERS_NEW = '''def product_sources():
    """Texts of every quoted-include file reachable from the two real entry points (LF-normalised)."""
    pending = [ROOT / "current_geometry.c", ROOT / "geometry-web/web_bridge.c"]
    seen, texts = set(), {}
    while pending:
        path = pending.pop()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        try:
            relative = path.relative_to(ROOT).as_posix()
        except ValueError:
            continue
        text = path.read_bytes().decode("utf-8").replace("\\r\\n", "\\n")
        texts[relative] = text
        for name in re.findall(r'^[ \\t]*#[ \\t]*include[ \\t]+"([^"]+)"', text, flags=re.M):
            pending.append((path.parent / name).resolve())
    return texts


def without_comments_and_strings(text):
    return re.sub(r'/\\*.*?\\*/|//[^\\n]*|"(?:\\\\.|[^"\\\\\\n])*"', "", text, flags=re.S)


def call_sites(texts, name):
    """Calls of `name`, i.e. matches that are not preceded by a type word (definition or declaration)."""
    count = 0
    for text in texts.values():
        code = without_comments_and_strings(text)
        for match in re.finditer(r"\\b" + re.escape(name) + r"\\s*\\(", code):
            word = re.search(r"([A-Za-z_]\\w*)\\s*\\**$", code[:match.start()].rstrip())
            if not word or word.group(1) in ("return", "else", "case"):
                count += 1
    return count


def mentions(texts, name):
    return sum(len(re.findall(r"\\b" + re.escape(name) + r"\\b", without_comments_and_strings(text))) for text in texts.values())


# Host functions that once claimed to be W consumers but have had no caller since GEO-261 51e9045b/#316.
RETIRED_DEAD_HOSTS = ("world_footprint_collides", "boundary_edge_interval", "stop_in_owner_extension")


'''

CONSUMERS_NEW = '''    def test_main_consumers_have_callers_delegate_and_keep_original_member_identity(self):
        source = (ROOT / "current_geometry.c").read_bytes().decode("utf-8").replace("\\r\\n", "\\n")
        texts = product_sources()
        pairs = (("collect_stop_faces", "app_contact_resolve_stops"),
                 ("timber_end_face_check", "wood_contact_end_faces_with_sources"))
        for host, evaluator in pairs:
            with self.subTest(host=host):
                body = function(source, host)
                self.assertIn(evaluator + "(", body)
                self.assertNotRegex(body, r"\\b(?:for|while)\\s*\\(")
                self.assertGreaterEqual(call_sites(texts, host), 1,
                                        host + " is claimed as a real main consumer but nothing calls it")
        for name in RETIRED_DEAD_HOSTS:
            with self.subTest(retired=name):
                self.assertEqual(0, mentions(texts, name), name + " was removed as dead code; a revival needs a caller and an entry in the pairs above")
        adapter = function(source, "app_contact_facts")
        self.assertRegex(adapter, r"(?:&world->wood.timbers\\[i\\]|const Timber \\*t\\s*=\\s*&world->wood.timbers\\[i\\])")
        self.assertIn("placement_effective_boundary(", adapter)
        resolver = function(source, "app_contact_resolve_stops")
        self.assertIn("app_contact_sources_collect(", resolver)
        self.assertIn("if(handled)return ok;", resolver)
        self.assertIn("wood_contact_collect_stops(", resolver)
'''


def cg_lines(text):
    return text.split("\r\n")


def find_line(lines, predicate, start=0):
    for i in range(start, len(lines)):
        if predicate(lines[i]):
            return i
    raise AssertionError("line not found")


def e316(t):
    # ---- H: current_geometry.c (CRLF) ----------------------------------------------------------
    lines = cg_lines(t.get(CG))
    # 1. orphan comment above the contact_world.h include (it described the function below it long ago)
    inc = find_line(lines, lambda s: s == '#include "geometry-templates/woodworking/native/contact_world.h"')
    assert lines[inc - 3].startswith("/* 候選矩形是否與同承載面上任何已放角材正面積重疊")
    assert lines[inc - 2].startswith("/* 公理 I11：同面任兩支已放角材的 footprint 正面積不得相交")
    assert lines[inc - 1].startswith(" *（端點/邊相接 = 零面積 = 合法接觸）。 */")
    del lines[inc - 3:inc]
    # 2. world_footprint_collides: no caller since 51e9045b
    i = find_line(lines, lambda s: s.startswith("static bool world_footprint_collides("))
    assert lines[i + 6] == "}" and "wood_contact_footprint_collides" in lines[i + 5]
    assert lines[i + 7] == ""
    del lines[i:i + 7]
    # 3. boundary_edge_interval + its comment: no caller (prose moves to contact_world.h)
    start = find_line(lines, lambda s: s == " * 定位邊在角材長度軸上的區間（D16 的固定段/延伸段切分要用它）。") - 1
    assert lines[start] == "/*"
    end = find_line(lines, lambda s: s.startswith("{return wood_contact_boundary_interval(boundary,along_v,span_lo,span_hi,cross_lo,cross_hi,out_lo,out_hi);}"))
    assert lines[end + 1] == "" and lines[end + 2] == "/*" and "I20 邊界材整條覆蓋" in lines[end + 3]
    del lines[start:end + 2]
    # 4. stop_in_owner_extension + its comment: no caller (prose moves to contact_world.h)
    start = find_line(lines, lambda s: s.startswith(" * 擋面接觸範圍 [lo,hi]（擋面擁有者長度軸上的座標）是否落在")) - 1
    assert lines[start] == "/*"
    end = find_line(lines, lambda s: s.startswith("{AppContactFacts facts;app_contact_facts(world,placement,boundary,&facts);return wood_contact_owner_extension("))
    assert lines[end + 1] == "" and lines[end + 2] == "/*" and "I19/I22 端面檢查" in lines[end + 3]
    del lines[start:end + 2]
    # 5. say where the live I11 filters are, inside the live function (axiom_matrix attributes it there)
    obstacles = find_line(lines, lambda s: s.startswith("    GeoRect2 obstacles[WORLD_MAX_TIMBERS];size_t obstacle_count=0;"))
    lines[obstacles:obstacles] = [
        "    /* I11 的同承載面過濾（放置當下）：只有同一承載面上已放的角材才是障礙物（M13）；正面積判式在 K",
        "     * （geo_strip_intervals → geo_rect_overlap_positive，M12）。同一條公理在全量重驗另有兩個檢查點，",
        "     * 各有自己的同承載面過濾：reference_check_all（geometry-core/references.inc，M97）與",
        "     * W wood_world_validate_members（world_validation.c，M98）。 */",
    ]
    t.put(CG, "\r\n".join(lines))

    # ---- W: contact world ----------------------------------------------------------------------
    cw = NATIVE + "contact_world.c"
    t.sub(cw, '''bool wood_contact_footprint_collides(const WoodContactWorld *world,const GeoRect2 *rect,const WoodMember *exclude)
{
    if(!world||!rect)return true;
    for(size_t i=0;i<world->member_count;++i){const WoodContactMemberFact *fact=&world->members[i];
        const WoodMember *member=fact->member;
        if(!member->placed||member==exclude||fact->placement_id!=world->placement_id||!fact->footprint_valid)continue;
        if(geo_rect_overlap_positive(rect,&fact->footprint))return true;
    }
    return false;
}
''', '')
    ch = NATIVE + "contact_world.h"
    t.sub(ch, "bool wood_contact_footprint_collides(const WoodContactWorld *,const GeoRect2 *,const WoodMember *);\n", "")
    t.sub(ch, "size_t wood_contact_collect_stops(const WoodContactWorld *,bool,const WoodMember *,WoodStopFace *,size_t);\n",
          "size_t wood_contact_collect_stops(const WoodContactWorld *,bool,const WoodMember *,WoodStopFace *,size_t);\n"
          "/* Positioning edge of a footprint (D16/R18): pure geometry. The interval on the length axis comes from the\n"
          " * footprint alone and never from how the member was placed (at-face, at or through give the same fixed\n"
          " * segment for the same footprint); the dump keeps references and placement order (R4) but not the method.\n"
          " * Only the outer loop counts: hole edges are column stop faces without extension semantics (I20/I21). */\n")
    t.sub(ch, "bool wood_contact_owner_extension(const WoodContactWorld *,const WoodMember *,GeoCoord,GeoCoord);\n",
          "/* True when the contact range [lo,hi] (on the owner's length axis) lies on the owner's extension part (I22:\n"
          " * an extension side counts as priority 2 when used as a stop). Only a boundary member located by an outline\n"
          " * edge has a fixed part and an extension part; every other owner returns false. */\n"
          "bool wood_contact_owner_extension(const WoodContactWorld *,const WoodMember *,GeoCoord,GeoCoord);\n")

    # ---- W unit harness: drop the dead API's case ------------------------------------------------
    hw = "tests/geo261_contact_world_harness.c"
    text = t.get(hw)
    a = text.index("static int collisions(void)\n")
    b = text.index("static int ordering(void)\n")
    t.put(hw, text[:a] + text[b:])
    t.sub(hw, 'if(!strcmp(argv[1],"collisions"))return collisions();', '')

    # ---- python guards ----------------------------------------------------------------------------
    cwp = "tests/test_geo261_wood_contact_world.py"
    text = t.get(cwp)
    a = text.index("    def test_five_real_main_consumers_delegate_and_keep_original_member_identity(self):\n")
    b = text.index("\n\nCOLLISION_FILTER = ")
    t.put(cwp, text[:a] + CONSUMERS_NEW + text[b:])
    t.sub(cwp, '''MODULE = ROOT / "geometry-templates/woodworking/native"

''', '''MODULE = ROOT / "geometry-templates/woodworking/native"


''' + HELPERS_NEW.rstrip("\n") + "\n\n")
    t.sub(cwp, '''COLLISION_FILTER = "if(!member->placed||member==exclude||fact->placement_id!=world->placement_id||!fact->footprint_valid)continue;\\n        if(geo_rect_overlap_positive"
''', '')
    t.sub(cwp, '''    ("positive-area", "if(geo_rect_overlap_positive(rect,&fact->footprint))return true;", "if(true)return true;", "collisions", "collision-touch-is-clear"),
    ("collision-identity", COLLISION_FILTER, COLLISION_FILTER.replace("member==exclude", "(exclude&&member->id==exclude->id)"), "collisions", "collision-other-candidate-same-id-not-excluded"),
    ("collision-placement", COLLISION_FILTER, COLLISION_FILTER.replace("fact->placement_id!=world->placement_id||", ""), "collisions", "collision-same-placement-only"),
''', '')
    t.sub(cwp, '''    def test_collision_positive_area_pointer_identity_candidate_placement_and_eligibility(self):
        result = self.case("collisions")
        self.assertEqual(0, result.returncode, result.stderr)

''', '')
    if "    def test_twenty_actual_guard_controls_fail_the_named_numeric_assertions(self):" in t.get(cwp):
        t.sub(cwp, "    def test_twenty_actual_guard_controls_fail_the_named_numeric_assertions(self):",
              "    def test_actual_guard_controls_fail_the_named_numeric_assertions(self):")

    wv = "tests/test_geo261_wood_world_validation.py"
    t.sub(wv, '''            ("validation-axis","if(!wood_member_primary_axis_check(","if(false&&!wood_member_primary_axis_check(","axis","validation-primary-axis"),
''', '''            ("validation-same-host","||a.placement_id!=b.placement_id","","collision","validation-separate-hosts"),
            ("validation-pair-placed","if(!b.member->placed||","if(","collision","validation-unplaced-no-collision"),
            ("validation-axis","if(!wood_member_primary_axis_check(","if(false&&!wood_member_primary_axis_check(","axis","validation-primary-axis"),
''')

    # ---- core oracle ------------------------------------------------------------------------------
    t.sub("tests/run_tests.py", ''' {'scene': '_s1_p9_l_room_custom_inner_wall_accept.scene', 'expect': 'accept',
  'lengths': [5000, 3200, 4746, 2236, 1773]},
]
''', ''' {'scene': '_s1_p9_l_room_custom_inner_wall_accept.scene', 'expect': 'accept',
  'lengths': [5000, 3200, 4746, 2236, 1773]},
 # #316:I11 的「只比同承載面」過濾。天花板與牆各一支 boundary,局部座標下足跡正面積重疊(u∈[0,3000]、v∈[0,20])
 # 但不在同一面 → 接受。單一承載面的場景分不出這道過濾在不在;M97(references.inc 的 reference_check_all 兩兩檢查)與
 # M98(world_validation.c 的最終世界兩兩檢查)拿掉過濾後,跨面配對被拿去比,整個世界被拒,由本場景殺。
 # 放在最後的理由同上:不擠掉舊突變 killed_by 裡的舊夾具。
 {'scene': '_i11_two_surfaces_same_uv_accept.scene', 'expect': 'accept', 'lengths': [4000, 3000]},
]
''')
    t.sub("tests/run_all.expected.json", '''    "core:run_tests": {
      "mode": "count",
      "count": 165,''', '''    "core:run_tests": {
      "mode": "count",
      "count": 166,''')
    t.sub("tests/run_all.expected.json", '''    "py:test_geo261_wood_contact_world": {
      "mode": "count",
      "count": 10,''', '''    "py:test_geo261_wood_contact_world": {
      "mode": "count",
      "count": 9,''')
    t.add(SCENE_PATH, SCENE)

    # ---- mutation table ------------------------------------------------------------------------------
    mu = "tests/mutate.py"
    t.sub(mu, '''    # main 的 M13 打在 world_footprint_collides,它唯一的呼叫點是 resolve_auto_span 的逐 cell 碰撞。
    # GEO-261 51e9045b 把逐 cell 檢查移到 K geo_strip_intervals,同承載面過濾改在 resolve_auto_span
    # 收 obstacles 的這一行;world_footprint_collides(→ W wood_contact_footprint_collides)從此沒有呼叫點,
    # 打在那裡的突變不會被執行。
''', '''    # M13 打在 resolve_auto_span 收障礙物的同承載面過濾(放置當下)。GEO-261 51e9045b 把逐 cell 檢查移到
    # K geo_strip_intervals 之後,原本的 world_footprint_collides(→ W wood_contact_footprint_collides)
    # 沒有呼叫點,已於 #316 移除。I11 另外兩個「只比同承載面」的過濾是 M97(references.inc 的 reference_check_all)
    # 與 M98(W world_validation.c 的最終世界重驗):單一承載面的場景全都無感,由
    # _i11_two_surfaces_same_uv_accept.scene 殺。
''')
    refs = t.get("geometry-core/references.inc")
    wvc = t.get(NATIVE + "world_validation.c")
    m97_old = "if(other_anchor.placement_id!=a->placement_id)continue;"
    m97_new = "if(0&&other_anchor.placement_id!=a->placement_id)continue;"
    m98_old = "if(!b.member->placed||a.placement_id!=b.placement_id)continue;"
    m98_new = "if(!b.member->placed)continue;"
    assert refs.count(m97_old) == 1 and wvc.count(m98_old) == 1

    def pyq(s):
        return "'" + s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"

    t.sub(mu, '''         new='        if(!t->placed||a->placement_id==placement->id)continue;\\n        if(timber_a0_footprint_uv(placement,t,a,&obstacles[obstacle_count]))++obstacle_count;'),
''', '''         new='        if(!t->placed||a->placement_id==placement->id)continue;\\n        if(timber_a0_footprint_uv(placement,t,a,&obstacles[obstacle_count]))++obstacle_count;'),
    dict(id="M97", desc="I11：reference_check_all 的兩兩檢查拿掉「只比同承載面」過濾(references.inc)；兩片承載面各有一支角材的 _i11_two_surfaces_same_uv_accept 必轉紅",
         file="geometry-core/references.inc",
         old=''' + pyq(m97_old) + ''',
         new=''' + pyq(m97_new) + '''),
    dict(id="M98", desc="I11：W 最終世界重驗的兩兩檢查拿掉「只比同承載面」過濾(world_validation.c)；同上場景必轉紅",
         file="geometry-templates/woodworking/native/world_validation.c",
         old=''' + pyq(m98_old) + ''',
         new=''' + pyq(m98_new) + '''),
''')
    text = t.get("tests/test_geo261_mutation_migration.py")
    m = list(re.finditer(r"        self\.assertEqual\((\d+), len\(added\)\)\n", text))[-1]
    n = int(m.group(1))
    t.sub("tests/test_geo261_mutation_migration.py", m.group(0),
          '''        # #316 (the two remaining I11 same-surface filters): M97 in H references.inc, M98 in W world_validation.c.
        added.update({"M97": "geometry-core/references.inc",
                      "M98": "geometry-templates/woodworking/native/world_validation.c"})
        self.assertEqual(%d, len(added))
''' % (n + 2))
    # ---- architecture inventory ------------------------------------------------------------------------
    t.sub("geometry-core/domain-decoupling/product-architecture.json", '      "wood_contact_footprint_collides",\n', '')
    return t
