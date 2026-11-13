"""Actual K clipping / W panel evaluators, with an archive-local old judge.

The isolated native client receives only explicit geometry and dimensions. It
checks independent cases before differential checks against the frozen original
algorithm. Product PF-2/PF-3 suites retain the real transactions and diagnostics.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native

FIXTURE = ROOT / "tests/geo261_panel_legacy_fixture.txt"
FIXTURE_SHA256 = "43e7124b819b26292379deb04ce6a14f416b34a78ce76957e19c2c0cf9642a5b"
BASELINE = "99eeabe11875f4d18b1bc35607cd3601a0ac3b4b"
WOOD = ROOT / "geometry-templates/woodworking/native"
KERNEL = ROOT / "geometry-core/kernel"


@lru_cache(maxsize=1)
def fixture():
    raw = FIXTURE.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise AssertionError("Frozen PF judge integrity mismatch")
    text = raw.decode("utf-8")
    if BASELINE not in text:
        raise AssertionError("Frozen PF judge lost its original provenance")
    return text


def without_comments(source):
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)


def definition(source, name):
    source = without_comments(source)
    match = re.search(r"^[\w *]+\b" + re.escape(name) + r"\s*\([^;]*?\)\s*\{", source, re.M | re.S)
    if match is None:
        raise AssertionError("Missing PF function " + name)
    depth, end = 1, match.end()
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


def frozen_translation_unit():
    """Retain the original algorithm bodies; adapt only their input carriers.

    The World stub supplies the one boundary lookup and pf_values copies the
    resolved inputs. It cannot select, validate or reconstruct any geometry.
    Public array element types are aliases, so result transfer does not depend
    on layout casts or strict-aliasing exceptions.
    """
    old = fixture()
    prefix = r'''#include "panel_support.h"
#include "grid.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>
typedef GeoCoord Coord;
typedef GeoPoint2 SurfacePoint2;
typedef GeoPoint3 Point3;
typedef GeoFrame SurfaceFrame;
typedef GeoLoop2View PolygonLoop2;
typedef struct {PolygonLoop2 outline,holes[GEO_REGION_MAX_HOLES];size_t hole_count;} SpaceBoundarySurface;
typedef struct {SurfaceFrame frame;uint32_t boundary_id,obstacle_count;} FinishSurface;
typedef struct {Coord rect[4];} FsObstacleView;
#define FS_OBSTACLE_MAX 1024
#define WORLD_MAX_TIMBERS 64
#define PF_TILE_MAX 1024
#define PF_AXIS_MAX 128
#define PF_EDGE_MAX 4096
#define PF_VERTEX_MAX 32768
#define PF_SUPPORT_MAX 32768
#define PF_SUPPORT_WORK_MAX 1048576
typedef WoodPanelLoop PfLoop;
typedef WoodPanelFragment PfFragment;
typedef WoodPanelTile PfTile;
typedef WoodPanelSeamLine PfSeamLine;
typedef struct {
    PfTile *tiles;size_t count,fragments,vertices,whole;
    PfSeamLine *seams;size_t seam_count;
    Coord size[2],gap,stagger,t;const FinishSurface *finish;
    FsObstacleView obstacles[FS_OBSTACLE_MAX];bool cuts[FS_OBSTACLE_MAX];bool keep_collinear;
} PfLayout;
typedef WoodPanelFootprint PfFootprint;
typedef WoodPanelEffectiveSeam PfEffectiveSeam;
typedef WoodPanelSupportPart PfSupportPart;
typedef struct {Coord lo,hi;} PfInterval;
typedef WoodPanelSupport PfSupport;
typedef struct {SpaceBoundarySurface boundary;FinishSurface finish;const WoodPanelLayoutInput *input;} World;
typedef struct {Coord origin[2];int stagger_axis;} PanelFill;
static char frozen_error[256];
static bool fs_error(const char *format,...)
{va_list args;va_start(args,format);vsnprintf(frozen_error,sizeof frozen_error,format,args);va_end(args);return false;}
#define fs_capacity_error fs_error
static Coord coord_min(Coord a,Coord b){return a<b?a:b;}
static Coord coord_max(Coord a,Coord b){return a>b?a:b;}
static bool coord_in_range(Coord a){return -INT64_C(100000000)<=a&&a<=INT64_C(100000000);}
static int sp_coord_compare(const void *a,const void *b){Coord x=*(const Coord*)a,y=*(const Coord*)b;return x<y?-1:x>y?1:0;}
#define grid_floor_div geo_floor_div
#define grid_ceil_div geo_ceil_div
#define panel_layout_pitch geo_period_pitch
#define panel_layout_body geo_period_body
#define panel_layout_center geo_period_center
#define panel_layout_shift geo_alternating_shift
static const SpaceBoundarySurface *world_find_boundary(const World *w,uint32_t id){(void)id;return &w->boundary;}
static bool pf_values(const World *w,const PanelFill *p,PfLayout *d)
{(void)p;d->finish=&w->finish;d->size[0]=w->input->size[0];d->size[1]=w->input->size[1];d->gap=w->input->gap;d->stagger=w->input->stagger;
 for(size_t i=0;i<w->input->cut_count;++i){GeoRect2 r=w->input->cuts[i];d->obstacles[i]=(FsObstacleView){{r.min_u,r.min_v,r.max_u,r.max_v}};d->cuts[i]=true;}return true;}
'''
    algorithms = definition(old, "pf_free") + "\n"
    algorithms += old[old.index("static bool pf_inside_loop"):old.index("static bool pf_rebuild")]
    algorithms += old[old.index("static void pf_support_free"):old.index("static bool pf_support_footprints")]
    algorithms += old[old.index("/* A cross section"):old.index("static bool pf_support_build")]
    suffix = r'''
static void frozen_world(const WoodPanelLayoutInput *p,World *w)
{memset(w,0,sizeof *w);w->input=p;w->boundary.outline=p->region.outline;w->boundary.hole_count=p->region.hole_count;
 for(size_t i=0;i<p->region.hole_count;++i)w->boundary.holes[i]=p->region.holes[i];w->finish.frame=p->frame;w->finish.obstacle_count=(uint32_t)p->cut_count;}
static void frozen_transfer(const PfLayout *d,WoodPanelLayout *out)
{*out=(WoodPanelLayout){d->tiles,d->count,d->fragments,d->vertices,d->whole,d->seams,d->seam_count,{d->size[0],d->size[1]},d->gap,d->stagger};}
bool frozen_panel_build(const WoodPanelLayoutInput *input,WoodPanelLayout *out)
{World w;frozen_world(input,&w);PanelFill p={{input->origin[0],input->origin[1]},input->stagger_axis};PfLayout d;
 frozen_error[0]=0;bool ok=pf_build(&w,&p,&d);frozen_transfer(&d,out);return ok;}
bool frozen_panel_clip(const GeoRegionView *region,const GeoRect2 *body,const GeoRect2 *cuts,size_t count,bool keep,size_t *vertices,GeoClipResult *out)
{WoodPanelLayoutInput input={0};input.region=*region;input.cuts=cuts;input.cut_count=count;World w;frozen_world(&input,&w);
 PfLayout d={0};PanelFill p={0};pf_values(&w,&p,&d);d.keep_collinear=keep;d.vertices=*vertices;PfTile t={0};
 t.body[0]=body->min_u;t.body[1]=body->min_v;t.body[2]=body->max_u;t.body[3]=body->max_v;
 frozen_error[0]=0;bool ok=pf_clip(&w,&d,&t);*vertices=d.vertices;*out=(GeoClipResult){t.fragments,t.count,t.area};return ok;}
bool frozen_panel_support(const WoodPanelLayout *layout,const WoodPanelFootprint *rects,size_t count,GeoQuantity x,WoodPanelSupport *out)
{PfLayout d={0};d.tiles=layout->tiles;d.count=layout->count;d.vertices=layout->vertices;d.seams=layout->seams;d.seam_count=layout->seam_count;d.gap=layout->gap;
 frozen_error[0]=0;return pf_support_evaluate(&d,rects,count,x,out);}
'''
    return prefix + algorithms + suffix


class PanelNativeSource(unittest.TestCase):
    def test_frozen_judge_is_archive_local_and_hash_verified(self):
        fixture.cache_clear()
        with patch("subprocess.check_output", side_effect=AssertionError("No Git dependency")):
            judge = frozen_translation_unit()
        self.assertIn("pf_clip(&w,&d,&t)", judge)
        self.assertIn("pf_support_evaluate(&d,rects,count,x,out)", judge)

    def test_public_modules_have_no_host_storage_or_policy_dependency(self):
        for directory, files in ((KERNEL, ("clip.h", "clip.c")), (WOOD, ("panel_layout.h", "panel_layout.c", "panel_support.h", "panel_support.c"))):
            for name in files:
                with self.subTest(file=name):
                    source = without_comments((directory / name).read_text(encoding="utf-8"))
                    self.assertNotRegex(source, r"\b(?:World|FinishSurface|PanelFill|PlacementSurface|FsObstacleView|TimberAnchor)\b")
                    self.assertNotRegex(source, r'#include\s+".*(?:internal/|app_state|current_geometry|\.\./)')

    def test_original_support_geometry_and_exact_comparison_bodies_are_preserved(self):
        current = (WOOD / "panel_support.c").read_text(encoding="utf-8")
        renames = {"Coord": "GeoCoord", "SurfacePoint2": "GeoPoint2", "PfFragment": "WoodPanelFragment", "PfLoop": "WoodPanelLoop", "PfFootprint": "WoodPanelFootprint", "PfInterval": "PanelInterval", "coord_min": "support_min", "coord_max": "support_max", "sp_coord_compare": "support_coord_compare"}
        def tokens(source):
            return [renames.get(t, t) for t in re.findall(r"[A-Za-z_]\w*|\d+|[^\s]", source)]
        for name in ("pf_component", "pf_interval_compare", "pf_support_enough", "pf_support_section", "pf_support_union", "pf_support_width"):
            with self.subTest(function=name):
                self.assertEqual(tokens(definition(fixture(), name)), tokens(definition(current, name)))

    def test_host_and_real_p103_client_use_the_extracted_evaluator(self):
        layout = (ROOT / "geometry-core/panel_fill_layout.inc").read_text(encoding="utf-8")
        finish = (WOOD / "finish.c").read_text(encoding="utf-8")
        support = (ROOT / "geometry-core/panel_fill_support.inc").read_text(encoding="utf-8")
        self.assertIn("wood_pf_build(&c,p,d)", layout)
        self.assertIn("wood_pf_clip(&c,d,t)", layout)
        self.assertIn("wood_panel_layout_build(&input,&d->layout", finish)
        self.assertIn("geo_region_clip_rect_minus_rects(&region,&body", finish)
        self.assertNotIn("int neighbors[4]", layout)
        self.assertIn("wood_panel_support_evaluate(&d->layout", support)
        self.assertNotIn("pf_support_union", support)
        self.assertIn("pf_support_evaluate(&d,rects,nr,x,&s)", (ROOT / "tests/pf3_algorithm.c").read_text(encoding="utf-8"))


class PanelNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        client = build.woodworking / "panel-native-client.c"
        shutil.copy2(ROOT / "tests/geo261_panel_harness.c", client)
        judge = build.woodworking / "panel-native-frozen.c"
        judge.write_text(frozen_translation_unit(), encoding="utf-8")
        cls.client = build.compile(client, "panel-native-client")
        cls.judge = build.compile(judge, "panel-native-frozen")
        cls.exe = build.link("panel-native-client", cls.objects())

    @classmethod
    def objects(cls, replace=None, obj=None):
        build = native()
        names = ("clip_object", "wood_panel_layout_object", "wood_panel_support_object", "geometry_object", "grid_object")
        return [cls.client, cls.judge, *[obj if name == replace else getattr(build, name) for name in names]]

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=60)
        self.assertIn(result.returncode, (0, 1), "Crash/setup failure is not a panel verdict: " + result.stderr)
        if result.returncode == 1:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        return result

    def test_clip_components_holes_orientation_order_and_empty(self):
        self.assertEqual(0, self.case("clip").returncode)

    def test_clip_collinear_provenance_and_cumulative_capacity(self):
        self.assertEqual(0, self.case("capacity").returncode)

    def test_layout_signed_stagger_identity_odd_gap_and_frame_range(self):
        self.assertEqual(0, self.case("layout").returncode)

    def test_support_actual_widths_fragment_vertices_union_and_rational_threshold(self):
        self.assertEqual(0, self.case("support").returncode)

    def test_original_clipping_layout_and_support_equivalence(self):
        self.assertEqual(0, self.case("equivalence").returncode)

    def test_single_guard_mutations_fail_independent_assertions(self):
        build = native()
        controls = (
            ("clip-hole", "clip", "if(clip_inside_loop(&b->holes[h],u2,v2))", "if(false)", "clip", "clip-hole-area"),
            ("clip-cut", "clip", "if(2*r->min_u<u2&&u2<2*r->max_u&&2*r->min_v<v2&&v2<2*r->max_v)", "if(false)", "clip", "clip-point-touch-components"),
            ("clip-keep", "clip", "if(keep_collinear||", "if(false||", "capacity", "clip-keeps-subdivision"),
            ("clip-budget", "clip", "if(*vertex_count+count>vertex_limit)", "if(false)", "capacity", "clip-cumulative-budget"),
            ("layout-odd", "panel_layout", "geo_alternating_shift(p->stagger_axis>=0,d->stagger,r)", "0", "layout", "layout-negative-odd-shift"),
            ("layout-frame", "panel_layout", "!geo_coord_in_range(world.x)||!geo_coord_in_range(world.y)||!geo_coord_in_range(world.z)", "false", "layout", "layout-world-range"),
            ("support-hole-cuts", "panel_support", "cuts[nc++]=pf_component(frag->loops[l].points[v],other);", "if(l==0)cuts[nc++]=pf_component(frag->loops[l].points[v],other);", "support", "support-fragment-vertices"),
            ("support-union", "panel_support", "out[i].lo<=out[used-1].hi", "out[i].lo<out[used-1].hi", "support", "support-touching-union"),
            ("support-round", "panel_support", "return d>x.num/x.den||(d==x.num/x.den&&x.num%x.den==0);", "return d>=x.num/x.den;", "support", "support-rational-not-rounded"),
            ("support-merge", "panel_support", "last->left==left&&last->right==right", "last->supported==(pf_support_enough(left,threshold)&&pf_support_enough(right,threshold))", "support", "support-widths-not-colours"),
        )
        for name, module, before, after, case, marker in controls:
            with self.subTest(mutation=name):
                directory = build.kernel if module == "clip" else build.woodworking
                original = (directory / (module + ".c")).read_text(encoding="utf-8")
                self.assertEqual(1, original.count(before), "Mutation must hit exactly once: " + name)
                source = directory / (name + ".c")
                source.write_text(original.replace(before, after), encoding="utf-8")
                obj = build.compile(source, name)
                attribute = "clip_object" if module == "clip" else "wood_" + module + "_object"
                exe = build.link(name, self.objects(attribute, obj))
                result = self.case(case, exe)
                self.assertEqual(1, result.returncode, "Surviving semantic guard: " + name)
                self.assertIn("ASSERT:" + marker, result.stderr)


    def test_empty_body_axis_keeps_raw_seams_and_other_parity(self):
        self.assertEqual(0,self.case("empty-axis").returncode)

    def empty_axis_instrumented(self,source,name):
        build=native();path=build.woodworking/(name+".c")
        path.write_text(source,encoding="utf-8")
        obj=build.compile(path,name,["geo_alternating_shift=pf_probe_alternating_shift"])
        return build.link(name,self.objects("wood_panel_layout_object",obj))

    def test_empty_axis_work_withdrawal_and_restoration(self):
        source=(native().woodworking/"panel_layout.c").read_text(encoding="utf-8")
        begin="    /* The alternating lattice has at most two row phases."
        end="    for(int64_t r=first;body_axis_intersects&&r<=last;++r)"
        self.assertEqual(1,source.count(begin));self.assertEqual(1,source.count(end))
        # Withdraw the whole optimization, not merely a part of its guard.
        start=source.index(begin);stop=source.index(end,start)
        original=source[:start]+source[stop:].replace("body_axis_intersects&&","",1)
        fixed=self.empty_axis_instrumented(source,"empty-axis-work-fixed")
        self.assertEqual(0,self.case("empty-axis",fixed).returncode)
        result=self.case("empty-axis-work",fixed)
        print("empty-axis-work phase=fixed\n"+result.stdout,end="")
        self.assertEqual(0,result.returncode)
        withdrawn=self.empty_axis_instrumented(original,"empty-axis-work-withdrawn")
        self.assertEqual(0,self.case("empty-axis",withdrawn).returncode)
        result=self.case("empty-axis-work",withdrawn)
        print("empty-axis-work phase=withdrawn\n"+result.stdout,end="")
        self.assertEqual(1,result.returncode)
        self.assertEqual("ASSERT:empty-axis-work-independent-of-empty-row-count\n",result.stderr)
        # Compile the restored original candidate bytes, independently of the
        # first executable, and recheck semantic output plus operation counts.
        restored=self.empty_axis_instrumented(source,"empty-axis-work-restored")
        self.assertEqual(0,self.case("empty-axis",restored).returncode)
        result=self.case("empty-axis-work",restored)
        print("empty-axis-work phase=restored\n"+result.stdout,end="")
        self.assertEqual(0,result.returncode)

    def test_empty_axis_semantic_controls_are_normal_assertion_failures(self):
        build=native();source=(build.woodworking/"panel_layout.c").read_text(encoding="utf-8")
        controls=(
            ("one-phase","phase<2","phase<1","empty-first-phase-keeps-other-parity"),
            ("drop-seams","    for(int64_t r=first;body_axis_intersects&&r<=last;++r)",
             "    if(!body_axis_intersects)return WOOD_PANEL_OK;\n    for(int64_t r=first;body_axis_intersects&&r<=last;++r)",
             "empty-axis-zero-pieces-with-raw-seams"),
            ("reject-empty","    for(int64_t r=first;body_axis_intersects&&r<=last;++r)",
             "    if(!body_axis_intersects){wood_panel_layout_free(d);return WOOD_PANEL_ENUM_LIMIT;}\n    for(int64_t r=first;body_axis_intersects&&r<=last;++r)",
             "empty-axis-legal"),
        )
        for name,before,after,marker in controls:
            with self.subTest(control=name):
                self.assertEqual(0,self.case("empty-axis").returncode)
                self.assertEqual(1,source.count(before))
                path=build.woodworking/("empty-axis-"+name+".c")
                path.write_text(source.replace(before,after),encoding="utf-8")
                obj=build.compile(path,"empty-axis-"+name)
                exe=build.link("empty-axis-"+name,self.objects("wood_panel_layout_object",obj))
                result=self.case("empty-axis",exe)
                self.assertEqual(1,result.returncode)
                self.assertEqual("ASSERT:"+marker+"\n",result.stderr)
                self.assertEqual(0,self.case("empty-axis").returncode)


if __name__ == "__main__":
    unittest.main()
