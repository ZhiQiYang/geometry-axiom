"""The extracted ordered W contact evaluator and its actual bridge consumer.

Numeric witnesses use public same-candidate facts and actual K predicates.
Each control must pass baseline, fail one named assertion, then pass baseline;
compiler errors and crashes are never counted as detected semantic changes.
"""
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_contacts import record_native_execution

MODULE = ROOT / "geometry-templates/woodworking/native"


def product_sources():
    """Manifest C sources and their conservative quoted-include closure (LF-normalised)."""
    manifest = json.loads((ROOT / "geometry-core/domain-decoupling/product-architecture.json").read_text(encoding="utf-8"))
    pending = [ROOT / item["path"] for item in manifest["sources"] if item["language"] == "c"]
    pending += [ROOT / "current_geometry.c", ROOT / "geometry-web/web_bridge.c"]
    seen, texts = set(), {}
    while pending:
        path = pending.pop().resolve()
        if path in seen:
            continue
        seen.add(path)
        try:
            relative = path.relative_to(ROOT).as_posix()
        except ValueError as error:
            raise AssertionError("Product include escapes repository: " + str(path)) from error
        if not path.is_file():
            raise AssertionError("Missing manifest/include source: " + relative)
        text = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
        texts[relative] = text
        # Keep string/character literals intact while masking comments, including
        # newlines. All conditional branches are explored; this is not a C preprocessor.
        includes = re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                          lambda match: re.sub(r'[^\n]', ' ', match[0]) if match[0].startswith('/') else match[0],
                          text, flags=re.S)
        for name in re.findall(r'^[ \t]*#[ \t]*include[ \t]+"([^"]+)"', includes, flags=re.M):
            candidates = (path.parent / name, ROOT / name, ROOT / "geometry-core/kernel" / name)
            resolved = next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)
            if resolved is None:
                raise AssertionError("Unresolved product include: " + relative + " -> " + name)
            pending.append(resolved)
    return texts


def without_comments_and_strings(text):
    return re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\\n])*"', "", text, flags=re.S)


def call_sites(texts, name):
    """Calls of `name`, i.e. matches that are not preceded by a type word (definition or declaration)."""
    count = 0
    for text in texts.values():
        code = without_comments_and_strings(text)
        for match in re.finditer(r"\b" + re.escape(name) + r"\s*\(", code):
            word = re.search(r"([A-Za-z_]\w*)\s*\**$", code[:match.start()].rstrip())
            if not word or word.group(1) in ("return", "else", "case"):
                count += 1
    return count


def mentions(texts, name):
    return sum(len(re.findall(r"\b" + re.escape(name) + r"\b", without_comments_and_strings(text))) for text in texts.values())


# Host functions that once claimed to be W consumers but have had no caller since GEO-261 51e9045b/#316.
RETIRED_DEAD_HOSTS = ("world_footprint_collides", "boundary_edge_interval", "stop_in_owner_extension")
RETIRED_DEAD_W_APIS = ("wood_contact_footprint_collides",)


def function(source, name):
    match = re.search(r"\b" + re.escape(name) + r"\([^;]*?\)\s*\{", source)
    if not match:
        raise AssertionError("Missing function definition: " + name)
    begin = source.index("{", match.start())
    level = 1
    for end in range(begin + 1, len(source)):
        level += (source[end] == "{") - (source[end] == "}")
        if level == 0:
            return source[begin + 1:end]
    raise AssertionError("Unclosed function: " + name)


class ContactWorldBoundary(unittest.TestCase):
    def test_public_contact_policy_uses_only_explicit_geometry_and_member_facts(self):
        for name in ("contact_world.h", "contact_world.c"):
            source = (MODULE / name).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|TimberAnchor|PlacementSurface|SpaceBoundarySurface|ReferenceEval|g_engineering_error)\b")
            self.assertNotIn("internal/", source)
            self.assertNotIn("geometry-app", source)
        header = (MODULE / "contact_world.h").read_text(encoding="utf-8")
        self.assertIn("const WoodMember *member;", header)
        self.assertIn("const WoodBoundaryRegion *role_boundary;", header)

    def test_main_consumers_have_callers_delegate_and_keep_original_member_identity(self):
        source = (ROOT / "current_geometry.c").read_bytes().decode("utf-8").replace("\r\n", "\n")
        texts = product_sources()
        pairs = (("collect_stop_faces", "app_contact_resolve_stops"),
                 ("timber_end_face_check", "wood_contact_end_faces_with_sources"))
        for host, evaluator in pairs:
            with self.subTest(host=host):
                body = function(source, host)
                self.assertIn(evaluator + "(", body)
                self.assertNotRegex(body, r"\b(?:for|while)\s*\(")
                self.assertGreaterEqual(call_sites(texts, host), 1,
                                        host + " is claimed as a real main consumer but nothing calls it")
        for name in RETIRED_DEAD_HOSTS + RETIRED_DEAD_W_APIS:
            with self.subTest(retired=name):
                self.assertEqual(0, mentions(texts, name), name + " was removed as dead code; a revival needs a caller and an entry in the pairs above")
        wrapper = function(source, "app_contact_facts")
        self.assertEqual("app_contact_facts_prepare(world,placement,boundary,facts,NULL);", wrapper.strip())
        adapter = function(source, "app_contact_facts_prepare")
        self.assertRegex(adapter, r"(?:&world->wood.timbers\[i\]|const Timber \*t\s*=\s*&world->wood.timbers\[i\])")
        self.assertIn("placement_effective_boundary(", adapter)
        resolver = function(source, "app_contact_resolve_stops")
        self.assertIn("app_contact_sources_collect(", resolver)
        self.assertIn("if(handled)return ok;", resolver)
        self.assertIn("wood_contact_collect_stops(", resolver)


STOP_FILTER = "if(!member->placed||member==exclude||fact->placement_id!=world->placement_id||!fact->footprint_valid)continue;\n        const GeoRect2 *f=&fact->footprint;"
CONTROLS = (
    ("placement-order", "return left<=right;", "return true;", "ordering", "placement-order-before-declaration"),
    ("stable-ties", "return left<=right;", "return left<right;", "ordering", "placement-stable-equal-order-sides"),
    ("equal-order-dedup", "index->minimum[slot]<order", "index->minimum[slot]<=order", "ordering", "equal-order-not-deduplicated"),
    ('partial-shadow', 'static bool contact_prefix_lo(GeoCoord a,const WoodStopFace *face)\n{return a<=face->lo&&a<face->hi;}\nstatic bool contact_prefix_hi(GeoCoord a,const WoodStopFace *face)\n{return a>=face->hi&&a>face->lo;}', 'static bool contact_prefix_lo(GeoCoord a,const WoodStopFace *face)\n{return a<face->hi;}\nstatic bool contact_prefix_hi(GeoCoord a,const WoodStopFace *face)\n{return a>face->lo;}', 'ordering', 'partial-shadow-retains-exposed-face'),
    ("outline-component-index", "(int)(component*GEO_LOOP_MAX_VERTICES+i)", "(int)i", "regions", "region-outline-index-encoded"),
    ("hole-component-index", "(int)(component*GEO_REGION_MAX_HOLES)+hole_of[li]", "hole_of[li]", "regions", "region-hole-index-encoded"),
    ("paired-capacity", "count+2<=cap", "count<cap", "regions", "member-capacity-pair-atomic"),
    ("complete-footprint", "if(!contact_contains(boundary,&rect))return false;", "if(false)return false;", "intervals", "i5-notched-footprint-deferred"),
    ("owner-identity", "if(fact->member!=owner)continue;", "if(fact->member->id!=owner->id)continue;", "extensions", "owner-pointer-not-id"),
    ("owner-extension", "return !(lo>=fix_lo&&hi<=fix_hi);", "return false;", "extensions", "owner-extension-outside-fixed-part"),
    ("fixed-inclusive", "return !(lo>=fix_lo&&hi<=fix_hi);", "return !(lo>fix_lo&&hi<fix_hi);", "extensions", "owner-fixed-interval-inclusive"),
    ("free-end", "||face->lo>cross_lo||face->hi<cross_hi||face->fixity==WOOD_STOP_FREE", "||face->lo>cross_lo||face->hi<cross_hi", "ends", "free-end-faces-ignored"),
    ("full-contact-width", "||face->lo>cross_lo||face->hi<cross_hi", "", "ends", "narrow-end-face-ignored"),
    ("contact-shadow", "||wood_stop_shadowed(faces,i,cross_lo,cross_hi)", "", "ends", "partial-earlier-face-shadows-only-contact"),
    ("end-order", "for(int end=0;end<2;++end)", "for(int end=1;end>=0;--end)", "ends", "start-end-before-global-placement-order"),
    ("stop-identity", STOP_FILTER, STOP_FILTER.replace("member==exclude", "(exclude&&member->id==exclude->id)"), "ordering", "stop-exclusion-keeps-candidate-identity"),
    ("extension-end", "||ext_end[end]", "", "ends", "self-boundary-extension-end-exempt"),
    ("edge-index-output", "if(out_edge)*out_edge=edge;", "(void)edge;", "intervals", "boundary-edge-index-horizontal"),
    ("inactive-shadow", "if(compact&&!active[j])continue;", "if(false)continue;", "active-dedup", "dedup-mutual-duplicate-id-leaves-final-pair"),
    ("compact-active-only", "if(active[i]){if(write!=i)out[write]=out[i];++write;}", "if(!active[i]){if(write!=i)out[write]=out[i];++write;}", "ordering", "earlier-full-cover-deduplicates"),
    ("compact-survivor-count", "active[i]=false;--remaining;++i;", "active[i]=false;++i;", "active-dedup", "dedup-mutual-duplicate-id-leaves-final-pair"),
    ("dedup-strict-overlap", "out[i].lo>=out[j].hi||out[j].lo>=out[i].hi", "false", "active-dedup", "dedup-zero-span-strict-overlap-preserved"),
    ("dedup-full-coordinate", "out[i].fixed!=out[j].fixed", "(uint32_t)out[i].fixed!=(uint32_t)out[j].fixed", "active-dedup", "dedup-full-width-planes-preserved"),
    ('indexed-unique-facts', 'if(index->last[slot])index->unique=false;', 'if(false)index->unique=false;', 'indexed-dedup', 'indexed-filtered-duplicate-order'),
    ('indexed-rc-free-prefix', 'for(size_t i=0;i<first;++i)contact_face_index_insert(&index,out,count,i);', 'for(size_t i=0;i<first;++i)if(out[i].fixity!=WOOD_STOP_FREE)contact_face_index_insert(&index,out,count,i);', 'ordering', 'boundary-even-free-owns-coincident-face'),
    ('indexed-strict-lo', 'return a<=face->lo&&a<face->hi;', 'return a<=face->lo;', 'indexed-dedup', 'indexed-zero-lower-strict'),
    ('indexed-strict-hi', 'return a>=face->hi&&a>face->lo;', 'return a>=face->hi;', 'indexed-dedup', 'indexed-zero-upper-strict'),
    ('indexed-plane-coordinate', 'return (a>b)-(a<b);', 'return ((int32_t)a>(int32_t)b)-((int32_t)a<(int32_t)b);', 'indexed-dedup', 'indexed-full-coordinate-plane'),
    ('indexed-plane-offset', 'size_t value=index->maximum[begin+at-1];', 'size_t value=index->maximum[at-1];', 'indexed-dedup', 'indexed-full-coordinate-plane'),
    ('indexed-single-witness', 'return witness&&contact_prefix_hi(out[witness-1].hi,face);', 'return witness!=0;', 'indexed-dedup', 'indexed-two-halves-not-one-cover'),
    ('indexed-survivor-count', 'active[i]=false;--*remaining;', 'active[i]=false;', 'ordering', 'earlier-full-cover-deduplicates'),
    ('indexed-reversed-skip', 'size_t begin,end;contact_face_plane_range(index,out,count,face->fixed,&begin,&end);', 'if(face->hi<face->lo)return false;size_t begin,end;contact_face_plane_range(index,out,count,face->fixed,&begin,&end);', 'indexed-dedup', 'indexed-enclosed-reversed-span'),
    ('legacy-partial-shadow', 'if(earlier&&out[j].lo<=out[i].lo&&out[j].hi>=out[i].hi)duplicate=true;', 'if(earlier)duplicate=true;', 'indexed-dedup', 'indexed-duplicate-fallback-keeps-partial-shadow'),
    ('legacy-placement-order', 'if(previous<=order)break;', 'if(true)break;', 'indexed-sort', 'sort-legacy-last-order'),
    ('legacy-stable-ties', 'if(previous<=order)break;', 'if(previous<order)break;', 'indexed-sort', 'sort-legacy-stable-fields'),
    ('sort-rc-prefix', 'size_t members=count-first;', 'first=0;size_t members=count-first;', 'indexed-sort', 'sort-rc-prefix-preserved'),
    ('sort-cycle-close', 'out[at]=value;index->sorted[at]=at;', '(void)value;index->sorted[at]=at;', 'indexed-sort', 'sort-cycle-every-field'),
    ('sort-cycle-step', 'out[at]=out[from];index->sorted[at]=at;at=from;', 'out[at]=out[at];index->sorted[at]=at;at=from;', 'indexed-sort', 'sort-cycle-every-field'),
    ('sort-full-order', 'return left<=right;', 'return (uint32_t)left<=(uint32_t)right;', 'indexed-sort', 'sort-full-uint64-order'),
    ('sort-duplicate-sort-guard', 'if(!(count<=WOOD_CONTACT_FACE_CAPACITY&&orders.indexed&&orders.unique)){', 'if(!(count<=WOOD_CONTACT_FACE_CAPACITY&&orders.indexed)){', 'indexed-sort', 'sort-legacy-last-order'),
    ('sort-overflow-sort-guard', 'if(!(count<=WOOD_CONTACT_FACE_CAPACITY&&orders.indexed&&orders.unique)){', 'if(!(count<=WOOD_CONTACT_FACE_CAPACITY&&orders.unique)){', 'indexed-sort', 'sort-overflow-linear-last-order'),
)


MONOTONIC_SORT_BLOCK = '    /* Placement order commonly already matches the admitted sequence.\n     * Equal orders keep their original member and side order. */\n    if(members<2)return;\n    uint64_t previous=contact_order(world,orders,out[first].timber_id);\n    bool ordered=true;\n    for(size_t i=first+1;i<count;++i){\n        uint64_t current=contact_order(world,orders,out[i].timber_id);\n        if(previous>current){ordered=false;break;}\n        previous=current;\n    }\n    if(ordered)return;\n'
MONOTONIC_SORT_ANCHOR = '    size_t members=count-first;\n    for(size_t i=first;i<count;++i)index->sorted[i]=i;\n'

class WoodContactWorld(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.woodworking / "contact-world-client.c"
        shutil.copy2(ROOT / "tests/geo261_contact_world_harness.c", source)
        cls.client = build.compile(source, "contact-world-client")
        cls.exe = build.link("contact-world-client", cls.objects(build))

    @classmethod
    def objects(cls, build, changed=None):
        return [cls.client, changed or build.wood_contact_world_object, build.wood_contacts_object,
                build.wood_supports_object, *build.kernel_objects()]

    def case(self, name, executable=None, *, phase="positive", control=None, assertion=None):
        command = [str(executable or self.exe), name]
        result = subprocess.run(command, capture_output=True,
                                text=True, encoding="utf-8", timeout=20)
        record_native_execution(self.id(), command, result, case=name, phase=phase, control=control, assertion=assertion)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a contact verdict: " + result.stderr)
        if result.returncode:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        return result

    def test_d11_placement_order_stable_ties_dedup_and_partial_contact_shadow(self):
        result = self.case("ordering")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_multiple_regions_outline_hole_ids_fixities_and_atomic_capacity_pairs(self):
        result = self.case("regions")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_live_set_duplicate_ids_strict_overlap_and_large_buffer_fallback(self):
        result = self.case("active-dedup")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_positioning_interval_real_geometry_notch_hole_and_i5_precedence(self):
        result = self.case("intervals")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_owner_extension_fixed_segment_axis_role_and_original_candidate_pointer(self):
        result = self.case("extensions")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_end_face_first_error_free_width_shadow_priority_and_extension_exemption(self):
        result = self.case("ends")
        self.assertEqual(0, result.returncode, result.stderr)

    def mutant(self, control):
        name, before, after, _, _ = control
        build = native()
        source = (build.woodworking / "contact_world.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Control must change one actual site: " + name)
        path = build.woodworking / ("contact-world-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        return build.compile(path, "contact-world-" + name)

    def test_actual_guard_controls_fail_the_named_numeric_assertions(self):
        build = native()
        for control in CONTROLS:
            with self.subTest(control=control[0]):
                baseline = self.case(control[3], phase="baseline", control=control[0], assertion=control[4])
                self.assertEqual(0, baseline.returncode, baseline.stderr)
                changed = self.mutant(control)
                executable = build.link("contact-world-mutant-" + control[0], self.objects(build, changed))
                result = self.case(control[3], executable, phase="mutant", control=control[0], assertion=control[4])
                self.assertEqual(1, result.returncode, "Guard survived: " + control[0])
                self.assertIn("ASSERT:" + control[4], result.stderr)
                restored = self.case(control[3], phase="restored", control=control[0], assertion=control[4])
                self.assertEqual(0, restored.returncode, restored.stderr)

    def test_unique_id_prefix_query_keeps_public_degenerate_and_filtered_facts(self):
        self.assertEqual(0, self.case("indexed-dedup").returncode)

    def test_stable_index_merge_preserves_complete_sequence_and_fallback(self):
        self.assertEqual(0, self.case("indexed-sort").returncode)


    def monotonic_executable(self,source,label):
        build=native()
        anchor="static uint64_t contact_order(const WoodContactWorld *world,const ContactOrderIndex *index,uint32_t id)\n{"
        counted="static size_t geo_test_sort_order_calls;\n"+anchor+"\n    ++geo_test_sort_order_calls;"
        self.assertEqual(1,source.count(anchor),"One original contact_order definition")
        instrumented=source.replace(anchor,counted)
        self.assertEqual(source,instrumented.replace(counted,anchor),"Counter removal preserves actual product bytes")
        subject=build.woodworking/("contact-monotonic-"+label+"-source.c")
        subject.write_text(instrumented,encoding="utf-8")
        harness=(ROOT/"tests/geo343_monotonic_sort_harness.c").read_text(encoding="utf-8")
        include='#include "contact-monotonic-subject.c"'
        self.assertEqual(1,harness.count(include))
        client=build.woodworking/("contact-monotonic-"+label+"-client.c")
        client.write_text(harness.replace(include,'#include "'+subject.name+'"'),encoding="utf-8")
        obj=build.compile(client,"contact-monotonic-"+label+"-client")
        return build.link("contact-monotonic-"+label+"-exe",
            [obj,build.wood_contacts_object,build.wood_supports_object,*build.kernel_objects()])

    def test_monotonic_sort_preserves_full_fields_and_linear_sorted_lookup_work(self):
        source=(native().woodworking/"contact_world.c").read_text(encoding="utf-8")
        self.assertEqual(1,source.count(MONOTONIC_SORT_BLOCK))
        self.assertEqual(1,source.count(MONOTONIC_SORT_ANCHOR))
        withdrawn=source.replace(MONOTONIC_SORT_BLOCK,"")
        restored=withdrawn.replace(MONOTONIC_SORT_ANCHOR,MONOTONIC_SORT_ANCHOR+MONOTONIC_SORT_BLOCK)
        self.assertEqual(source,restored,"Complete sort optimization restoration is exact")
        cases=("sorted","reverse","ties","all-ties","prefix","no-member","one-member","last-inversion","middle-inversion","full-uint64")
        fixed=None
        for phase,variant,expected in (("fixed",source,0),("withdrawn",withdrawn,1),("restored",restored,0)):
            with self.subTest(whole_phase=phase):
                executable=self.monotonic_executable(variant,phase)
                if phase=="fixed":fixed=executable
                for case in cases:
                    result=self.case(case,executable,phase=phase,control="monotonic-whole")
                    self.assertEqual(0,result.returncode,result.stderr)
                result=self.case("work",executable,phase=phase,control="monotonic-whole",
                    assertion="monotonic-linear-order-lookups")
                print("monotonic-whole phase="+phase+" "+result.stdout,end="")
                self.assertEqual(expected,result.returncode,result.stderr)
                if expected:self.assertIn("ASSERT:monotonic-linear-order-lookups",result.stderr)
        self.assertIsNotNone(fixed)
        controls=(
            ("missed-inversion","if(previous>current){ordered=false;break;}","if(previous>current){ordered=true;break;}","last-inversion","monotonic-last-inversion-full-fields"),
            ("missed-last-face","for(size_t i=first+1;i<count;++i){","for(size_t i=first+1;i+1<count;++i){","last-inversion","monotonic-last-inversion-full-fields"),
            ("truncated-previous","uint64_t previous=contact_order(world,orders,out[first].timber_id);","uint32_t previous=contact_order(world,orders,out[first].timber_id);","full-uint64","monotonic-full-uint64-fields"),
            ("missed-previous-update","previous=current;","(void)current;","middle-inversion","monotonic-middle-inversion-full-fields"),
        )
        for label,before,after,case,marker in controls:
            with self.subTest(monotonic_control=label):
                baseline=self.case(case,fixed,phase="baseline",control=label,assertion=marker)
                self.assertEqual(0,baseline.returncode,baseline.stderr)
                self.assertEqual(1,source.count(before),"One actual monotonic guard")
                executable=self.monotonic_executable(source.replace(before,after),label)
                result=self.case(case,executable,phase="mutant",control=label,assertion=marker)
                self.assertEqual(1,result.returncode,result.stderr);self.assertIn("ASSERT:"+marker,result.stderr)
                result=self.case(case,fixed,phase="restored",control=label,assertion=marker)
                self.assertEqual(0,result.returncode,result.stderr)

    def extension_transaction(self, executable):
        with _bridge.BridgeSession(executable) as bridge:
            self.assertTrue(bridge.command("reset")["ok"])
            commands = (
                "surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,2000 2000,2000 2000,3000 0,3000",
                "grid 1 on 1 v 1500 1600", "timber 1 20 20 role boundary", "timber 2 20 20 role boundary",
                "timber 3 27 33 role primary", "timber 4 27 33 role boundary", "timber 5 27 33 role primary",
                "place 1 on 1 at-face e5 +v +n", "place 2 on 1 at-face e1 +v +n",
                "place 3 on 1 at-line grid 1 v 0 +u +n", "place 4 on 1 at-face e3 +v +n")
            for command in commands:
                response = bridge.line(command)
                self.assertTrue(response["ok"], (command, response))
            before = bridge.command("dump")["text"]
            response = bridge.line("place 5 on 1 at-line grid 1 v 1 through 3000 +u +n")
            after = bridge.command("dump")["text"]
            ids = [m["id"] for m in bridge.command("objects")["timbers"]]
            if response["ok"]:
                self.assertNotEqual(before, after)
                self.assertIn(5, ids)
            else:
                self.assertIn("V_CUT_PRIORITY", response["error"])
                self.assertIn("優先級 2", response["error"])
                self.assertEqual(before, after)
                self.assertNotIn(5, ids)
            return response["ok"]

    def test_same_owner_extension_guard_controls_the_actual_atomic_bridge_placement(self):
        build = native()
        baseline = build.bridge()
        self.assertFalse(self.extension_transaction(baseline))
        control = next(item for item in CONTROLS if item[0] == "owner-extension")
        changed = self.mutant(control)
        client = build.link("contact-world-product-mutant-client", self.objects(build, changed))
        result = self.case("extensions", client, phase="product-mutant-client", control=control[0], assertion=control[4])
        self.assertEqual(1, result.returncode)
        self.assertIn("ASSERT:owner-extension-outside-fixed-part", result.stderr)
        objects = build.product_objects()
        self.assertEqual(1, objects.count(build.wood_contact_world_object))
        bridge = build.link("contact-world-product-mutant-bridge", [build.bridge_object,
            *[changed if item == build.wood_contact_world_object else item for item in objects]])
        self.assertTrue(self.extension_transaction(bridge))
        self.assertFalse(self.extension_transaction(baseline))


if __name__ == "__main__":
    unittest.main(verbosity=2)
