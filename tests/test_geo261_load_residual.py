"""同候選變更、回滾與跨 consumer 依賴；兩個負控制須由具名斷言偵測。"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import NativeBuild

DEFINITION_DEPEND = ('geo_eval_depend_hint(ctx->sources,wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_MEMBER,id,&key),\n'
                     '            GEO_DEPENDENCY_DEFINITION_REQUIRED,&ctx->member_reads[i].definition_node_hint)')
ANCHOR_DEPEND = ('geo_eval_depend_hint(ctx->sources,wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_PLACEMENT,id,&key),\n'
                 '            GEO_DEPENDENCY_DEFINITION_REQUIRED,&ctx->member_reads[i].placement_node_hint)')
FOOTPRINT_DEPEND = 'geo_eval_depend_hint(ctx->sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&ctx->member_reads[i].footprint_node_hint)'
POSE_DEPEND = 'geo_eval_depend_hint(ctx->sources,ref,relation,&ctx->member_reads[i].footprint_node_hint)'
EARLY_DEFINITION = '        if(!reference_sources_ensure(ctx)||!reference_placement_frame(ctx,id,&actual.frame)||'
CONTACT_HIT = '    if(ctx->member_reads[i].contact_valid&&ctx->member_reads[i].contact_id==id){'
H_CACHE_CONTROLS = (
    ('contact-edge', 'cache-contact', 'contact-cache-second-consumer-edge-and-order', ANCHOR_DEPEND,
     '(residual_second_consumer?GEO_SOURCE_OK:' + ANCHOR_DEPEND + ')'),
    ('contact-kind', 'cache-contact', 'contact-cache-second-consumer-edge-and-order', ANCHOR_DEPEND,
     ANCHOR_DEPEND.replace('GEO_DEPENDENCY_DEFINITION_REQUIRED', '(residual_second_consumer?GEO_DEPENDENCY_EVALUATE_BEFORE:GEO_DEPENDENCY_DEFINITION_REQUIRED)')),
    ('contact-order', 'cache-contact', 'contact-cache-second-consumer-edge-and-order', CONTACT_HIT,
     CONTACT_HIT + '\n        if(residual_second_consumer){GeoSourceRef pose={APP_SOURCE_MEMBER_POSE,&id,sizeof id};'
     'if(geo_eval_depend(ctx->sources,pose,GEO_DEPENDENCY_VALUE_REQUIRED)!=GEO_SOURCE_OK)return false;}'),
    ('definition-edge', 'cache-definition', 'definition-cache-second-consumer-edge-and-order', DEFINITION_DEPEND,
     '(residual_second_consumer?GEO_SOURCE_OK:' + DEFINITION_DEPEND + ')'),
    ('definition-kind', 'cache-definition', 'definition-cache-second-consumer-edge-and-order', DEFINITION_DEPEND,
     DEFINITION_DEPEND.replace('GEO_DEPENDENCY_DEFINITION_REQUIRED', '(residual_second_consumer?GEO_DEPENDENCY_EVALUATE_BEFORE:GEO_DEPENDENCY_DEFINITION_REQUIRED)')),
    ('anchor-edge', 'cache-anchor', 'anchor-cache-second-consumer-edge-and-order', ANCHOR_DEPEND,
     '(residual_second_consumer?GEO_SOURCE_OK:' + ANCHOR_DEPEND + ')'),
    ('anchor-kind', 'cache-anchor', 'anchor-cache-second-consumer-edge-and-order', ANCHOR_DEPEND,
     ANCHOR_DEPEND.replace('GEO_DEPENDENCY_DEFINITION_REQUIRED', '(residual_second_consumer?GEO_DEPENDENCY_EVALUATE_BEFORE:GEO_DEPENDENCY_DEFINITION_REQUIRED)')),
    ('footprint-edge', 'cache-footprint', 'footprint-cache-second-consumer-edge-and-order', FOOTPRINT_DEPEND,
     '(residual_second_consumer?GEO_SOURCE_OK:' + FOOTPRINT_DEPEND + ')'),
    ('footprint-kind', 'cache-footprint', 'footprint-cache-second-consumer-edge-and-order', FOOTPRINT_DEPEND,
     FOOTPRINT_DEPEND.replace('GEO_DEPENDENCY_VALUE_REQUIRED', '(residual_second_consumer?GEO_DEPENDENCY_EVALUATE_BEFORE:GEO_DEPENDENCY_VALUE_REQUIRED)')),
    ('footprint-order', 'cache-footprint', 'footprint-cache-second-consumer-edge-and-order', EARLY_DEFINITION,
     '        if(residual_second_consumer&&!geo_placement_sources_definition_header(ctx->placement_sources,id,&definition))return false;\n' + EARLY_DEFINITION),
    ('pose-edge', 'cache-pose', 'pose-cache-second-consumer-edge-and-order', POSE_DEPEND,
     '(residual_second_consumer?GEO_SOURCE_OK:' + POSE_DEPEND + ')'),
    ('pose-kind', 'cache-pose-kind', 'pose-cache-preserves-requested-dependency-kind', POSE_DEPEND,
     POSE_DEPEND.replace(',relation,', ',(residual_second_consumer?GEO_DEPENDENCY_VALUE_REQUIRED:relation),')),
)
ANCHOR_ID_KEY = "&&ctx->member_reads[i].id==id"
CONTACT_ID_KEY = "&&ctx->member_reads[i].contact_id==id"
ANCHOR_INVALIDATOR = "ctx->member_reads[i].footprint_valid=false;"
PLACEMENT_KEY = "&&ctx->member_reads[i].placement==request->placement_id"


def includes(source, origin):
    return re.sub(r'(^\s*#\s*include\s*)"([^"\n]+)"',
                  lambda m: m[1] + '"' + (origin.parent / m[2]).resolve().as_posix() + '"', source, flags=re.M)


class LoadResidual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = NativeBuild(kernel_only=True)
        cls.exe = cls.compile("baseline")

    @classmethod
    def compile(cls, name, invalidate=True, dependencies=True, collection_state=True, source_change=None, placement_dependency=True):
        build = cls.build
        world_path = ROOT / "geometry-app/native/world_validation.inc"
        world = includes(world_path.read_text(encoding="utf-8"), world_path)
        if not invalidate:
            anchor = ("static void app_footprint_memo_begin(AppFootprintMemo *memo,const World *world)\n"
                      "{\n    memo->world=world;\n    memset(memo->valid,0,sizeof memo->valid);\n}")
            assert world.count(anchor) == 1
            world = world.replace(anchor, anchor.replace(
                "memset(memo->valid,0,sizeof memo->valid);",
                "/* 負控制：保留同一快取儲存的舊值。 */"))
        world_copy = build.work / (name + "-world.inc")
        world_copy.write_text(world, encoding="utf-8")
        sources_path = ROOT / "geometry-app/native/reference_sources.inc"
        sources = includes(sources_path.read_text(encoding="utf-8"), sources_path)
        if not dependencies:
            anchor = "if(geo_eval_depend(ctx->sources,"
            hint_anchor = "if(geo_eval_depend_hint(ctx->sources,"
            assert sources.count(anchor) == 0 and sources.count(hint_anchor) == 3
            sources = sources.replace(anchor, "if(false&&geo_eval_depend(ctx->sources,")
            sources = sources.replace(hint_anchor, "if(false&&geo_eval_depend_hint(ctx->sources,")
        if not placement_dependency:
            assert sources.count(ANCHOR_DEPEND) == 1, "Placement hit boundary must hit exactly once"
            sources = sources.replace(ANCHOR_DEPEND,
                "(residual_second_consumer&&id==3?GEO_SOURCE_OK:" + ANCHOR_DEPEND + ")")
        if source_change:
            changes = (source_change,) if isinstance(source_change[0], str) else source_change
            for before, after in changes:
                assert sources.count(before) == 1, "Control must hit exactly once: " + name
                sources = sources.replace(before, after)
        sources_copy = build.work / (name + "-sources.inc")
        sources_copy.write_text(sources, encoding="utf-8")
        references_path = ROOT / "geometry-core/references.inc"
        references = includes(references_path.read_text(encoding="utf-8"), references_path)
        references = references.replace(sources_path.as_posix(), sources_copy.as_posix())
        references_copy = build.work / (name + "-references.inc")
        references_copy.write_text(references, encoding="utf-8")
        definition_copy = None
        if not placement_dependency:
            definition_path = ROOT / "geometry-templates/woodworking/native/definition_sources.c"
            definition = includes(definition_path.read_text(encoding="utf-8"), definition_path)
            call = "geo_eval_source(s->graph,wood_definition_source_ref(s->token,kind,id,&key),relation,out)"
            assert definition.count(call) == 1, "Placement source control must hit exactly once"
            replacement = ("(kind==WOOD_DEFINITION_PLACEMENT&&id==3?"
                           "residual_placement_source_without_edge(s->graph,wood_definition_source_ref(s->token,kind,id,&key),relation,out):"
                           + call + ")")
            definition = definition.replace(call, replacement)
            helper = """static GeoSourceStatus residual_placement_source_without_edge(GeoEvalContext *graph,GeoSourceRef source,
    GeoDependencyKind relation,GeoSourceValue *out)
{
    /* A deliberately broken typed getter reuses a real VALID source but omits only the current consumer edge. */
    if(residual_second_consumer){
        for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView node;
            if(geo_eval_node_at(graph,i,&node)&&node.source.provider==source.provider&&
               node.source.key_size==source.key_size&&(!source.key_size||!memcmp(node.source.key,source.key,source.key_size))&&
               node.state==GEO_NODE_VALID&&node.value){*out=*node.value;return GEO_SOURCE_OK;}
        }
    }
    return geo_eval_source(graph,source,relation,out);
}
"""
            insertion = "static bool wd_get(WoodDefinitionSources *s,WoodDefinitionKind kind,uint32_t id,GeoDependencyKind relation,GeoSourceValue *out)"
            assert definition.count(insertion) == 1
            definition = definition.replace(insertion, helper + insertion)
            definition_copy = build.work / (name + "-definition.c")
            definition_copy.write_text(definition, encoding="utf-8")
        contact_path = ROOT / "geometry-templates/woodworking/native/contact_sources.c"
        contact = includes(contact_path.read_text(encoding="utf-8"), contact_path)
        if not collection_state:
            start = contact.index("if(q->collection&&geo_eval_node_at(")
            end = contact.index("{", start) + 1
            contact = contact[:start] + "if(q->collection){" + contact[end:]
            contact = contact.replace("collection=*node.value;", "collection=(GeoSourceValue){.kind=GEO_SOURCE_DEFINITION,.as.definition={wood_contact_collection_schema,q->collection,q->collection_size}};")
        contact_copy = build.work / (name + "-contact.c")
        contact_copy.write_text(contact, encoding="utf-8")
        unity_path = ROOT / "geometry-app/native/woodworking_unity.inc"
        unity = includes(unity_path.read_text(encoding="utf-8"), unity_path)
        assert unity.count(contact_path.as_posix()) == 1
        unity = unity.replace(contact_path.as_posix(), contact_copy.as_posix())
        if definition_copy is not None:
            assert unity.count(definition_path.as_posix()) == 1
            unity = unity.replace(definition_path.as_posix(), definition_copy.as_posix())
        unity_copy = build.work / (name + "-woodworking.inc")
        unity_copy.write_text(unity, encoding="utf-8")
        geometry_path = ROOT / "current_geometry.c"
        geometry = includes(geometry_path.read_bytes().decode("utf-8"), geometry_path)
        geometry = geometry.replace(world_path.as_posix(), world_copy.as_posix())
        geometry = geometry.replace(references_path.as_posix(), references_copy.as_posix())
        geometry = geometry.replace(unity_path.as_posix(), unity_copy.as_posix())
        geometry_copy = build.work / (name + "-geometry.c")
        geometry_copy.write_text(geometry, encoding="utf-8")
        harness = (ROOT / "tests/geo261_load_residual_harness.c").read_text(encoding="utf-8")
        harness = harness.replace('../current_geometry.c', geometry_copy.as_posix())
        member_cases = build.work / (name + "-member-reads.inc")
        member_cases.write_bytes((ROOT / "tests/geo261_member_reads_cases.inc").read_bytes())
        harness = harness.replace('"geo261_member_reads_cases.inc"', '"' + member_cases.as_posix() + '"')
        client = build.work / (name + "-client.c")
        client.write_text(harness, encoding="utf-8")
        return build.link("residual-" + name, [build.compile(client, "residual-" + name)])

    def case(self, name, exe=None, *, phase="positive", control=None, expected_assertion=None):
        command = [str(exe or self.exe), name]
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=90)
        log = os.environ.get("GEO261_LOAD_RESIDUAL_EXECUTION_LOG")
        if log:
            path = Path(log)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps({
                    "command": command, "cwd": os.getcwd(), "case": name, "phase": phase,
                    "control": control, "expected_assertion": expected_assertion,
                    "source_sha": os.environ.get("GITHUB_SHA"),
                    "executable_sha256": hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),
                    "environment": {k: os.environ.get(k) for k in ("PATH", "LANG", "LC_ALL", "TMPDIR", "PYTHONOPTIMIZE", "GITHUB_SHA", "GITHUB_WORKSPACE")},
                    "actual_exit": result.returncode, "timeout_expired": False,
                    "stdout": result.stdout, "stderr": result.stderr,
                    "capture_mode": "complete native text output; original subprocess text=True",
                }, ensure_ascii=False) + "\n")
        self.assertIn(result.returncode, (0, 1), "編譯錯誤、崩潰或受阻不算偵測：" + result.stderr)
        return result

    def passes(self, name, exe=None, *, phase="positive", control=None):
        result = self.case(name, exe, phase=phase, control=control)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("PASS " + name + "\n", result.stdout)

    def test_cached_reads_preserve_each_consumer_exact_source_kind_and_order(self):
        for case in ("cache-definition", "cache-anchor", "cache-contact", "cache-footprint", "cache-pose", "cache-pose-kind"):
            with self.subTest(case=case):
                self.passes(case)

    def test_cached_source_footprint_is_not_overwritten_by_deferred_raw_snapshot(self):
        case, control = "cache-footprint-source", "footprint-hit-raw-snapshot"
        marker = "footprint-cache-hit-preserves-source-out"
        self.passes(case, phase="baseline", control=control)
        change = ("if(deferred)raw[i].pending=fact->footprint_valid?0:2;",
                  "/* isolated control leaves the stale raw footprint pending */")
        exe = self.compile(control, source_change=change)
        result = self.case(case, exe, phase="mutant", control=control, expected_assertion=marker)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("ASSERT:" + marker + " ", result.stderr)
        self.assertEqual(1, result.stderr.count("ASSERT:"), result.stderr)
        print("H cache control " + control + ": exit=1; " + result.stderr.strip(), flush=True)
        self.passes(case, phase="restored", control=control)

    def test_each_cached_read_second_consumer_edge_kind_and_order_mutant_is_detected(self):
        for name, case, marker, before, after in H_CACHE_CONTROLS:
            with self.subTest(control=name):
                self.passes(case, phase="baseline", control=name)
                exe = self.compile(name, source_change=(before, after))
                result = self.case(case, exe, phase="mutant", control=name, expected_assertion=marker)
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn("ASSERT:" + marker + " ", result.stderr)
                self.assertEqual(1, result.stderr.count("ASSERT:"), result.stderr)
                print("H cache control " + name + ": exit=1; " + result.stderr.strip(), flush=True)
                self.passes(case, phase="restored", control=name)

    def test_member_anchor_id_key_rejects_same_slot_different_canonical_member(self):
        case, control, marker = "member-anchor-id", "anchor-id-key", "member-anchor-cache-id-must-match"
        self.passes(case, phase="baseline", control=control)
        exe = self.compile(control, source_change=(ANCHOR_ID_KEY, ""))
        result = self.case(case, exe, phase="mutant", control=control, expected_assertion=marker)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("ASSERT:" + marker + " ", result.stderr)
        print("Member cache control " + control + ": exit=1; " + result.stderr.strip(), flush=True)
        self.passes(case, phase="restored", control=control)

        # A separate contact cache key must protect the same natural slot
        # permutation.  This is not inferred from the full-anchor guard above.
        case, control, marker = "member-anchor-miss", "contact-id-key", "member-anchor-miss-invalidates-footprint"
        self.passes(case, phase="baseline", control=control)
        exe = self.compile(control, source_change=(CONTACT_ID_KEY, ""))
        result = self.case(case, exe, phase="mutant", control=control, expected_assertion=marker)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("ASSERT:" + marker + " ", result.stderr)
        self.assertEqual(1, result.stderr.count("ASSERT:"), result.stderr)
        print("Member cache control " + control + ": exit=1; " + result.stderr.strip(), flush=True)
        self.passes(case, phase="restored", control=control)

    def test_member_anchor_miss_invalidates_naturally_warmed_footprint(self):
        case, control, marker = "member-anchor-miss", "anchor-miss-invalidation", "member-anchor-miss-invalidates-footprint"
        self.passes(case, phase="baseline", control=control)
        exe = self.compile(control, source_change=(ANCHOR_INVALIDATOR, "/* isolated invalidator control */"))
        result = self.case(case, exe, phase="mutant", control=control, expected_assertion=marker)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("ASSERT:" + marker + " ", result.stderr)
        print("Member cache control " + control + ": exit=1; " + result.stderr.strip(), flush=True)
        self.passes(case, phase="restored", control=control)

    def test_placement_key_single_fault_equivalence_and_paired_defence_are_distinct(self):
        case, marker = "member-placement-key", "contact-footprint-cache-placement-must-match"
        self.passes(case, phase="baseline", control="placement-key-single")
        single = self.compile("placement-key-only", source_change=(PLACEMENT_KEY, ""))
        # The real immutable graph and intact anchor invalidator already prevent
        # this single fault: preserve its actual green result as equivalent.
        self.passes(case, single, phase="single-mutant-equivalent", control="placement-key-single")
        self.passes(case, phase="restored", control="placement-key-single")
        print("Member cache placement-key single removal: equivalent in this canonical candidate; exit=0", flush=True)
        invalidator = (ANCHOR_INVALIDATOR, "/* paired precondition: anchor invalidator disabled */")
        paired_baseline = self.compile("placement-key-paired-baseline", source_change=invalidator)
        self.passes(case, paired_baseline, phase="baseline-anchor-invalidator-disabled", control="placement-key-paired")
        paired_mutant = self.compile("placement-key-paired-withdrawn", source_change=(invalidator, (PLACEMENT_KEY, "")))
        result = self.case(case, paired_mutant, phase="mutant-anchor-invalidator-disabled", control="placement-key-paired", expected_assertion=marker)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("ASSERT:" + marker + " ", result.stderr)
        print("Member cache placement-key paired defence only: exit=1; " + result.stderr.strip(), flush=True)
        self.passes(case, paired_baseline, phase="restored-anchor-invalidator-disabled", control="placement-key-paired")

    def test_same_candidate_move_delete_failed_read_and_rollback(self):
        self.passes("move-delete")

    def test_same_candidate_parameter_value_change_and_rollback(self):
        self.passes("parameter")

    def test_second_consumer_retains_placement_and_pose_edges_and_sealed_lookup(self):
        self.passes("consumers")

    def test_contact_query_reset_and_re_registration_evaluates_collection_in_order(self):
        self.passes("collection-reset")

    def test_collection_cache_without_node_validation_reports_reset_state(self):
        self.passes("collection-reset")
        exe = self.compile("unvalidated-collection", collection_state=False)
        result = self.case("collection-reset", exe)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("ASSERT:reset-collection-must-be-evaluated ", result.stderr)
        print("集合節點未驗證突變：exit=1；" + next(s for s in result.stderr.splitlines() if "ASSERT:reset-" in s), flush=True)
        self.passes("collection-reset")

    def test_never_invalidate_mutant_reports_stale_footprint(self):
        self.passes("move-delete")
        exe = self.compile("never-invalidate", invalidate=False)
        result = self.case("move-delete", exe)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("ASSERT:stale-footprint-after-move ", result.stderr)
        print("永不失效突變：exit=1；" + next(s for s in result.stderr.splitlines() if "ASSERT:stale-" in s), flush=True)
        result = self.case("parameter", exe)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("ASSERT:stale-footprint-after-parameter ", result.stderr)
        print("永不失效突變（參數）：exit=1；" + next(s for s in result.stderr.splitlines() if "ASSERT:stale-" in s), flush=True)
        self.passes("move-delete")

    def test_cross_consumer_mutant_reports_missing_dependency(self):
        control, marker = "placement-second-consumer-reader-and-hit-edge", "cross-consumer-placement-edge-missing"
        self.passes("consumers", phase="baseline", control=control)
        exe = self.compile("cross-consumer", placement_dependency=False)
        result = self.case("consumers", exe, phase="mutant", control=control, expected_assertion=marker)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("ASSERT:cross-consumer-placement-edge-missing ", result.stderr)
        self.assertEqual(1, result.stderr.count("ASSERT:"), result.stderr)
        print("跨 consumer 共用突變：exit=1；" + next(s for s in result.stderr.splitlines() if "ASSERT:cross-" in s), flush=True)
        self.passes("consumers", phase="restored", control=control)


if __name__ == "__main__":
    unittest.main(verbosity=2)
