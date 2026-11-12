"""PRIVATE UNRUN draft: real K/W post-facts memo semantics and work-count controls.

Run only after this draft and the product patch are adopted into one clean
source closure. No wall-clock assertion, compiler error, crash, timeout or skip
is accepted as a killed mutation. Existing contact-source tests stay unchanged.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native

MODULE = ROOT / "geometry-templates/woodworking/native/contact_sources.c"
DECLARATIONS = '''#include "contact_sources.h"
#include <stdlib.h>
extern bool contact_test_disable_memo;
void *contact_test_malloc(const char *,size_t);
void *contact_test_calloc(const char *,size_t,size_t);
size_t contact_test_collect(const WoodContactWorld *,bool,const WoodMember *,WoodStopFace *,size_t);
void contact_test_transform_feature(GeoSegment3 *);
bool contact_test_reject_feature(void);
'''
FEATURE_RETURN = "out->kind=GEO_SOURCE_FEATURE;out->as.feature=(GeoFeatureValue){record,WOOD_CONTACT_SOURCE_METADATA_SIZE,segment};return true;"
HOOKS = (
    ("if(!memo||!memo->collection||memo->count>q->cap||", "if(contact_test_disable_memo||!memo||!memo->collection||memo->count>q->cap||"),
    ("calloc(1,sizeof *facts)", 'contact_test_calloc("facts",1,sizeof *facts)'),
    ("malloc(q->cap*sizeof *faces)", 'contact_test_malloc("faces",q->cap*sizeof *faces)'),
    ("unsigned char *bytes=malloc(size)", 'unsigned char *bytes=contact_test_malloc("collection",size)'),
    ("memo=malloc(sizeof *memo)", 'memo=contact_test_malloc("memo",sizeof *memo)'),
    ("wood_contact_collect_stops(&world,q->request.along_v,q->request.exclude,faces,q->cap)", "contact_test_collect(&world,q->request.along_v,q->request.exclude,faces,q->cap)"),
    (FEATURE_RETURN, "if(contact_test_reject_feature())return false;contact_test_transform_feature(&segment);" + FEATURE_RETURN),
)
CONTROLS = (
    ("withdraw", "repeat", "result-memo-repeat-computes-once",
     "bool reused=wood_contact_result_matches(s->result_memo,q,facts);", "bool reused=false;"),
    ("member-id", "key-member-id", "result-memo-key-member-id-is-fresh",
     "memo->member_id[i]!=facts->members[i].member->id||", "false||"),
    ("member-placed", "key-member-placed", "result-memo-key-member-placed-is-fresh",
     "memo->member_placed[i]!=facts->members[i].member->placed", "false"),
    ("cap", "key-cap-room", "result-memo-key-cap-room-is-fresh",
     "memo->cap!=q->cap||", "false||"),
    ("skip-callback", "repeat", "result-memo-callback-runs-each-query",
     "if(!s->facts(s->user,s->graph,&q->request,facts)||!wood_contact_source_facts_valid(facts)){",
     "if(s->result_memo)memcpy(facts,&s->result_memo->facts,sizeof *facts);\n"
     "        if((!s->result_memo&&!s->facts(s->user,s->graph,&q->request,facts))||!wood_contact_source_facts_valid(facts)){"),
)

# Separate additional failure modes; the original five controls are unchanged.
EXTRA_CONTROLS = (
    ("nested-premature-match", "nested", "result-memo-nested-outer-result-matches-reference", (
        ("        if(!s->facts(s->user,s->graph,&q->request,facts)||!wood_contact_source_facts_valid(facts)){",
         "        bool premature_match=s->result_memo&&s->result_memo->request.placement_id==q->request.placement_id&&"
         "s->result_memo->request.along_v==q->request.along_v&&s->result_memo->request.exclude==q->request.exclude;\n"
         "        if(!s->facts(s->user,s->graph,&q->request,facts)||!wood_contact_source_facts_valid(facts)){"),
        ("bool reused=wood_contact_result_matches(s->result_memo,q,facts);",
         "bool reused=premature_match||wood_contact_result_matches(s->result_memo,q,facts);"),
    )),
    ("feature-failure-success", "feature-failure", "result-memo-feature-failure-keeps-output", (
        ("            free(result);return false;", "            free(result);return true;"),
    )),
    ("overwrite-borrowed-on-miss", "borrowed-miss", "result-memo-miss-keeps-prior-borrowed-value", (
        ("    memo->collection=q->collection;memo->collection_size=q->collection_size;",
         "    if(s->result_memo&&memo->collection&&memo->collection_size==q->collection_size)"
         "memcpy((unsigned char *)memo->collection,q->collection,q->collection_size);\n"
         "    memo->collection=q->collection;memo->collection_size=q->collection_size;"),
    )),
)


def once(source, before, after):
    if source.count(before) != 1:
        raise AssertionError(f"Instrumentation/mutation anchor not unique: {before!r}")
    return source.replace(before, after)


def instrument(source):
    for before, after in HOOKS:
        source = once(source, before, after)
    return DECLARATIONS + source


class ContactResultMemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        client = build.woodworking / "contact-result-memo-client.c"
        shutil.copy2(ROOT / "tests/geo300_contact_result_memo_harness.c", client)
        cls.client = build.compile(client, "contact-result-memo-client")
        cls.raw = MODULE.read_text(encoding="utf-8")
        cls.source = instrument(cls.raw)
        cls.exe = cls.build_provider("positive", cls.source)

    @classmethod
    def build_provider(cls, label, source):
        build = native()
        path = build.woodworking / ("contact-result-memo-" + label + ".c")
        path.write_text(source, encoding="utf-8")
        provider = build.compile(path, "contact-result-memo-" + label)
        return build.link("contact-result-memo-" + label, [cls.client, provider,
            build.wood_contact_world_object, build.wood_contacts_object,
            build.wood_supports_object, build.source_object, build.geometry_object])

    def run_case(self, case, *, exe=None, phase="positive", control=None, marker=None):
        command = [str(exe or self.exe), case]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        log = os.environ.get("GEO300_CONTACT_RESULT_LOG")
        if log:
            path = Path(log)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps({"command": command, "cwd": os.getcwd(),
                    "phase": phase, "control": control, "expected_assertion": marker,
                    "source_sha": os.environ.get("GITHUB_SHA"),
                    "product_sha256": hashlib.sha256(MODULE.read_bytes()).hexdigest(),
                    "executable_sha256": hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),
                    "actual_exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
                    "environment": {k: os.environ.get(k) for k in ("PATH", "LANG", "LC_ALL", "TMPDIR", "GITHUB_SHA")}},
                    ensure_ascii=False) + "\n")
        self.assertIn(result.returncode, (0, 1), "Crash/setup failure is not a verdict: " + result.stdout + result.stderr)
        return result

    def pass_case(self, case, **kwargs):
        result = self.run_case(case, **kwargs)
        self.assertEqual((0, "PASS " + case + "\n", ""), (result.returncode, result.stdout, result.stderr))

    def test_identical_queries_keep_callback_allocations_own_bytes_and_exact_ordered_graph(self):
        self.pass_case("repeat")

    def test_all_request_fields_fact_bytes_and_mutable_pointees_invalidate_hint(self):
        for key in ("placement", "axis", "exclude", "cap", "cap-room", "member-id", "member-placed", "footprint",
                    "footprint-valid", "member-order", "member-placement", "member-count", "region-id",
                    "region-count", "region-coordinate", "region-fixity", "facts-unused"):
            with self.subTest(key=key):
                self.pass_case("key-" + key)

    def test_warm_hint_keeps_real_callback_validation_and_required_allocation_failures(self):
        for role in ("callback", "invalid", "facts", "faces", "collection"):
            with self.subTest(role=role):
                self.pass_case("failure-" + role)

    def test_optional_memo_allocation_failure_preserves_success_then_recovers(self):
        self.pass_case("optional")

    def test_new_feature_results_are_consumed_after_collection_hint_hit(self):
        self.pass_case("feature")

    def test_withdrawal_and_alias_safeguard_controls_fail_named_assertions(self):
        for name, case, marker, before, after in CONTROLS:
            with self.subTest(control=name):
                self.pass_case(case, phase="baseline", control=name)
                changed = once(self.source, before, after)
                exe = self.build_provider(name, changed)
                result = self.run_case(case, exe=exe, phase="mutant", control=name, marker=marker)
                self.assertEqual((1, "", "ASSERT:" + marker + "\n"),
                                 (result.returncode, result.stdout, result.stderr))
                self.pass_case(case, phase="restored", control=name)

    def test_nested_facts_callback_memo_update_keeps_outer_values_and_ordered_graph(self):
        self.pass_case("nested")

    def test_feature_failure_is_atomic_and_a_later_query_rechecks_every_feature(self):
        self.pass_case("feature-failure")

    def test_two_memo_misses_preserve_prior_borrowed_collection_and_feature_bytes(self):
        self.pass_case("borrowed-miss")

    def test_nested_feature_failure_and_borrowed_miss_controls_fail_distinct_assertions(self):
        for name, case, marker, replacements in EXTRA_CONTROLS:
            with self.subTest(control=name):
                self.pass_case(case, phase="baseline", control=name)
                changed = self.source
                for before, after in replacements:
                    changed = once(changed, before, after)
                exe = self.build_provider(name, changed)
                result = self.run_case(case, exe=exe, phase="mutant", control=name, marker=marker)
                self.assertEqual((1, "", "ASSERT:" + marker + "\n"),
                                 (result.returncode, result.stdout, result.stderr))
                self.pass_case(case, phase="restored", control=name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
