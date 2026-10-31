"""I24 host route inventory and retained ordered-evidence wiring.

These source contracts complement the real-bridge behavior cases.  The route
tables below are reviewed literals, never inferred from mutation receipts or
another registry.  A new publication/validation route requires classification
before it may join this list.  Default text is a change alarm for today's closed
replay program; it does not make stagger illegal in replacement worlds.
"""
import ast
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_BASE = "4b665fae21ab63aaffb7d84f6a32d5a469ba1675"
# The original I24 implementation must remain kernel-neutral. Later train
# work may adopt separately reviewed generic K changes; pin its complete K
# tree instead of exempting source.c or accepting arbitrary future edits.
I24_IMPLEMENTATION_HEAD = "32f42e3d991c7d2d916d21bfe8ac5d3dd0f9b131"
# 9430bae568feb98805072930c92f9a03a1250d4e: reuse a missing edge's slot.
# 81b6c388f8b73e9aaf885b1d948e5f306b77bafd: generic provider hint bucket.
GENERIC_SOURCE_INDEX_KERNEL_HEAD = "81b6c388f8b73e9aaf885b1d948e5f306b77bafd"

# Common scene/validation helpers serve both interactive submissions and file
# replay.  Their classification therefore explicitly retains both contexts;
# the H baseline/replay guard below distinguishes them at runtime.
PUBLISH_SITES = (
    ("current_geometry.c", "world_revalidate", 1, "submission/replay helper"),
    ("geometry-core/transactions.inc", "apply_scene_line_candidate", 2, "submission/replay lines"),
    ("geometry-web/engineering_bridge.inc", "batch_confirm", 1, "submission"),
    ("geometry-web/web_bridge.c", "app_replace_world", 1, "replacement"),
    ("geometry-web/web_bridge.c", "cmd_loadfile", 1, "replacement"),
    ("geometry-web/scene-import-bridge.inc", "cmd_load_confirm", 1, "replacement"),
    ("geometry-core/model_base.c", "model_parse_scene", 1, "isolated replay"),
)
REVALIDATE_SITES = (
    ("current_geometry.c", "world_replace_object", 1),
    ("current_geometry.c", "app_boundary_replace", 1),
    ("current_geometry.c", "app_placement_replace", 1),
    ("current_geometry.c", "app_world_revalidate_staged", 2),
    ("current_geometry.c", "apply_placement_line", 1),
    ("current_geometry.c", "apply_surface_combined_line", 2),
    ("current_geometry.c", "apply_grid_line", 1),
    ("current_geometry.c", "apply_column_line", 1),
    ("current_geometry.c", "apply_beam_line", 1),
    ("current_geometry.c", "apply_applyproj_line", 1),
    ("current_geometry.c", "apply_delete_line", 1),
    ("current_geometry.c", "apply_space_line", 1),
    ("current_geometry.c", "parse_scene_file", 1),
    ("geometry-core/references.inc", "reference_checked", 1),
    ("geometry-core/references.inc", "reference_snap", 1),
    ("geometry-core/subgrid_commands.inc", "apply_subgrid_line", 1),
    ("geometry-web/engineering_bridge.inc", "app_batch_candidate_apply", 1),
    ("geometry-web/web_bridge.c", "app_replace_evaluate", 1),
)
STAGED_SITES = (
    ("geometry-core/boundary_vertex_keys.inc", "apply_boundary_keys_line", 1),
    ("geometry-core/boundary_vertex_keys.inc", "apply_boundary_keyed_line", 1),
    ("geometry-core/grid_bindings.inc", "apply_grid_binding_line", 1),
    ("geometry-core/grid_bindings.inc", "apply_grid_binding_application", 1),
    ("geometry-core/grid_subdivision.inc", "apply_grid_source_rule", 1),
    ("geometry-core/grid_systems.inc", "apply_grid_system_line", 1),
    ("geometry-core/grid_systems.inc", "apply_grid_system_application", 1),
)
BASELINE_ASSIGNMENTS = (
    ("current_geometry.c", "app_world_revalidate_staged", "staged"),
    ("current_geometry.c", "app_world_revalidate_staged", "previous"),
    ("current_geometry.c", "app_world_candidate_revalidate", "&candidate->before"),
    ("current_geometry.c", "app_world_candidate_revalidate", "previous"),
    ("geometry-core/boundary_vertex_keys.inc", "apply_boundary_keyed_line", "world"),
    ("geometry-core/boundary_vertex_keys.inc", "apply_boundary_keyed_line", "previous_baseline"),
    ("geometry-core/grid_bindings.inc", "apply_grid_binding_application", "w"),
    ("geometry-core/grid_bindings.inc", "apply_grid_binding_application", "baseline"),
    ("geometry-core/grid_systems.inc", "apply_grid_system_application", "w"),
    ("geometry-core/grid_systems.inc", "apply_grid_system_application", "previous_baseline"),
    ("geometry-core/transactions.inc", "app_scene_candidate_apply", "call->before"),
    ("geometry-core/transactions.inc", "app_scene_candidate_apply", "previous_baseline"),
    ("geometry-web/engineering_bridge.inc", "app_batch_candidate_apply", "call->before"),
    ("geometry-web/engineering_bridge.inc", "app_batch_candidate_apply", "previous"),
    ("geometry-web/web_bridge.c", "app_scene_load_evaluate", "NULL"),
    ("geometry-web/web_bridge.c", "app_scene_load_evaluate", "previous"),
    ("geometry-web/source-inspector-bridge.inc", "cmd_source_inspect_file", "NULL"),
    ("geometry-web/source-inspector-bridge.inc", "cmd_source_inspect_file", "previous"),
    ("geometry-core/model_base.c", "model_load_evaluate", "NULL"),
    ("geometry-core/model_base.c", "model_load_evaluate", "previous"),
)
DEFAULT_LINES = (
    "surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
    "timber 1 27 33 role boundary", "place 1 on 1 at-face e0 +u +n",
    "timber 2 27 33 role boundary", "place 2 on 1 at-face e2 +u +n",
    "spec 主支中線 500", "guide 1 1 v spec:主支中線",
    "timber 3 27 33 role primary", "place 3 on 1 at-line guide 1 +v +n",
)

LEXICAL = re.compile(r'/\*.*?\*/|//[^\r\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)
SIGNATURE = re.compile(r"\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{")


def masked(source):
    """Remove comments/literals while retaining offsets and newlines."""
    return LEXICAL.sub(lambda m: "".join("\n" if c == "\n" else " " for c in m.group()), source)


def compact(source):
    return re.sub(r"\s+", "", source)


@dataclass(frozen=True)
class Function:
    name: str
    signature: int
    start: int
    end: int


class CSource:
    def __init__(self, path):
        self.path = path
        # current_geometry.c is intentionally CRLF. Read bytes and normalize
        # only this in-memory view; source contracts must never rewrite it.
        self.text = (ROOT / path).read_bytes().decode("utf-8").replace("\r\n", "\n")
        self.code = masked(self.text)
        stack, opening_depth, closing = [], {}, {}
        for offset, value in enumerate(self.code):
            if value == "{":
                opening_depth[offset] = len(stack)
                stack.append(offset)
            elif value == "}" and stack:
                closing[stack.pop()] = offset + 1
        self.functions = []
        for match in SIGNATURE.finditer(self.code):
            opening = match.end() - 1
            if match.group(1) in {"if", "for", "while", "switch"} or opening_depth.get(opening) != 0:
                continue
            if opening in closing:
                self.functions.append(Function(match.group(1), match.start(), opening + 1, closing[opening] - 1))

    def function(self, name):
        found = [f for f in self.functions if f.name == name]
        if len(found) != 1:
            raise AssertionError(f"{self.path}: expected one definition of {name}, got {len(found)}")
        return self.text[found[0].start:found[0].end]

    def sites(self, symbol):
        result = Counter()
        for function in self.functions:
            body = self.code[function.start:function.end]
            count = len(re.findall(r"\b" + re.escape(symbol) + r"\s*\(", body))
            if count:
                result[self.path, function.name] += count
        return result

    def assignments(self):
        result = Counter()
        for function in self.functions:
            body = self.code[function.start:function.end]
            for match in re.finditer(r"\bg_subgrid_before\s*=(?!=)\s*([^;]+);", body):
                result[self.path, function.name, compact(match.group(1))] += 1
        return result


def source_paths():
    paths = {Path("current_geometry.c"), Path("geometry-web/web_bridge.c"), Path("geometry-core/model_base.c")}
    paths.update(path.relative_to(ROOT) for path in (ROOT / "geometry-core").glob("*.inc"))
    paths.update(path.relative_to(ROOT) for path in (ROOT / "geometry-web").glob("*.inc"))
    paths.update(path.relative_to(ROOT) for path in (ROOT / "geometry-app/native").rglob("*")
                 if path.suffix in {".c", ".h", ".inc"})
    return sorted(map(str, paths))


def block_after(body, marker):
    """Return the braced branch following one exact, reviewed condition."""
    if body.count(marker) != 1:
        raise AssertionError(f"expected one condition {marker!r}")
    code = masked(body)
    opening = code.find("{", body.index(marker) + len(marker))
    if opening < 0:
        raise AssertionError(f"missing branch for {marker!r}")
    depth = 1
    for offset in range(opening + 1, len(code)):
        depth += (code[offset] == "{") - (code[offset] == "}")
        if not depth:
            return body[opening + 1:offset]
    raise AssertionError(f"unterminated branch for {marker!r}")


class Geo314CommitPaths(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {path: CSource(path) for path in source_paths()}

    def inventory(self, symbol):
        result = Counter()
        for source in self.sources.values():
            result.update(source.sites(symbol))
        return result

    def body(self, path, function):
        return self.sources[path].function(function)

    def test_publication_routes_have_reviewed_submission_or_replacement_classification(self):
        self.assertTrue(all(classification in {"submission", "replacement", "isolated replay",
            "submission/replay helper", "submission/replay lines"} for *_, classification in PUBLISH_SITES))
        expected = Counter({(path, function): count for path, function, count, _ in PUBLISH_SITES})
        self.assertEqual(expected, self.inventory("app_world_candidate_publish"),
                         "I24 publication route added/removed: classify its submission/replacement boundary")

    def test_revalidation_and_staged_routes_are_an_exact_reviewed_inventory(self):
        self.assertEqual(Counter({(path, function): count for path, function, count in REVALIDATE_SITES}),
                         self.inventory("world_revalidate"), "I24 world validation route changed")
        self.assertEqual(Counter({(path, function): count for path, function, count in STAGED_SITES}),
                         self.inventory("app_world_revalidate_staged"), "I24 staged validation route changed")

    def test_submission_baselines_and_replay_restoration_are_exact(self):
        actual = Counter()
        for source in self.sources.values():
            actual.update(source.assignments())
        self.assertEqual(Counter(BASELINE_ASSIGNMENTS), actual,
                         "I24 baseline setup/restore changed; a true submission cannot silently bypass W")

    def test_single_submission_guard_runs_after_axis_validation_before_bindings(self):
        body = masked(self.body("current_geometry.c", "world_revalidate_candidate"))
        self.assertEqual(1, len(re.findall(r"\bgrid_stagger_submission_valid\s*\(", body)))
        self.assertLess(body.index("grid_systems_rebuild("), body.index("grid_stagger_submission_valid("))
        self.assertLess(body.index("grid_stagger_submission_valid("), body.index("grid_bindings_rebuild("))
        self.assertEqual(Counter({("current_geometry.c", "world_revalidate_candidate"): 1}),
                         self.inventory("grid_stagger_submission_valid"))

    def test_replay_bypass_and_retained_candidate_evidence_feed_the_pure_rule(self):
        body = compact(masked(self.body("geometry-core/subgrid_world.inc", "grid_stagger_submission_valid")))
        self.assertRegex(body, r"if\((?:g_parsing_scene_file\|\|!g_subgrid_before|!g_subgrid_before\|\|g_parsing_scene_file)\)returntrue;")
        self.assertEqual(1, body.count("returntrue;"), "only replacement/replay may bypass the W submission rule")
        self.assertIn("candidate&&world==&candidate->after", body)
        self.assertIn("facts=candidate->stagger_facts;count=candidate->operation.stagger_count;", body)
        self.assertIn("wood_grid_stagger_commit_valid(&world->geo.grid_store,&g_subgrid_before->geo.grid_store,facts,count,err,cap)", body)

    def test_default_fixed_lines_change_alarm_preserves_the_owned_replay_route(self):
        source = self.sources["geometry-core/transactions.inc"]
        tables = [source.text[source.text.index("app_default_replay_lines[]="):],
                  self.body("geometry-core/transactions.inc", "reference_default_world")]
        for table in tables:
            literals = table[table.index("{") + 1:table.index("};")]
            rows = tuple(ast.literal_eval(match.group()) for match in re.finditer(r'"(?:\\.|[^"\\])*"', literals))
            self.assertEqual(DEFAULT_LINES, rows, "default-fixed-lines-changed: re-review this replacement program")
            self.assertFalse(any(re.search(r"\b(?:grid-system|stagger)\b", row) for row in rows),
                             "default-fixed-lines-changed: current text now reaches I24; classify the new route")
        self.assertRegex(masked(source.text), r"\}\s*AppDefaultReplay\s*;")
        self.assertIn("reference_default_world(world)", self.body("geometry-core/transactions.inc", "reference_default_world_owned"))
        self.assertIn("app_default_replay_line(", self.body("geometry-core/transactions.inc", "reference_default_world"))
        replay = self.body("geometry-core/transactions.inc", "app_default_replay_line")
        self.assertIn("app_scene_candidate_apply(", replay)
        self.assertIn("apply_scene_line(", replay)

    def test_wood_rule_does_not_depend_on_host_state_or_aliases(self):
        code = masked((ROOT / "geometry-templates/woodworking/native/grid_application.c").read_text(encoding="utf-8"))
        self.assertEqual([], re.findall(r"\b(?:World|Coord|scene_error|g_subgrid_before|g_parsing_scene_file)\b", code),
                         "I24 rule belongs to W; host context and submission classification remain in H")

    def test_kernel_has_no_changes_against_the_fixed_integration_base(self):
        introduced = subprocess.run(
            ["git", "diff", "--name-only", "--no-renames", INTEGRATION_BASE,
             I24_IMPLEMENTATION_HEAD, "--", "geometry-core/kernel"],
            cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual("", introduced.stdout, "original I24 implementation must not change K files")
        changed = subprocess.run(
            ["git", "diff", "--name-only", "--no-renames", GENERIC_SOURCE_INDEX_KERNEL_HEAD,
             "--", "geometry-core/kernel"],
            cwd=ROOT, capture_output=True, text=True, check=True)
        added = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "--", "geometry-core/kernel"],
                               cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual("", changed.stdout + added.stdout,
                         "I24 submission policy must not change K files outside the exact reviewed generic K tree")

    def test_ordered_facts_capture_step_values_without_extra_candidate_or_validation_work(self):
        path = "geometry-app/native/stagger_facts.inc"
        snapshot = compact(masked(self.body(path, "app_stagger_snapshot")))
        self.assertIn("geo_parameter_evaluation_create(&world->geo.parameters,NULL,NULL)", snapshot)
        self.assertIn("geo_parameter_evaluation_field(evaluation,point->source,&value)", snapshot)
        self.assertIn("geo_parameter_evaluation_destroy(evaluation)", snapshot)
        record = compact(masked(self.body(path, "app_stagger_record_step")))
        self.assertIn("!candidate||world!=&candidate->after", record)
        self.assertIn("++candidate->operation.stagger_steps", record)
        append = compact(masked(self.body(path, "app_stagger_append")))
        self.assertIn("fact->before=*before;fact->after=*after;", append)
        collector = self.sources[path].code
        self.assertNotRegex(collector, r"\b(?:app_world_candidate_(?:create|evaluate|seal|publish)|world_revalidate|app_world_revalidate_staged)\s*\(")
        batch = compact(masked(self.body("geometry-web/engineering_bridge.inc", "app_batch_candidate_apply")))
        self.assertEqual(1, batch.count("app_stagger_snapshot("))
        self.assertEqual(1, batch.count("app_stagger_record_step("))
        self.assertLess(batch.index("app_stagger_snapshot("), batch.index("call->operation("))
        self.assertLess(batch.index("call->operation("), batch.index("app_stagger_record_step("))
        self.assertLess(batch.index("app_stagger_record_step("), batch.index("world_revalidate("))
        self.assertEqual(1, batch.count("world_revalidate("), "ordered facts must not add per-operation full validation")

    def test_retained_evidence_hash_and_existing_revision_seal_cover_confirmation(self):
        path = "geometry-app/native/world_candidate.inc"
        raw = self.sources[path].code
        self.assertRegex(raw, r"WoodGridStaggerFact\s*\*\s*stagger_facts\s*;")
        self.assertRegex(raw, r"char\s+stagger_seal\s*\[65\]\s*;")
        # Evidence fields belong only to the H sidecar, its collector and the
        # consuming guard.  World/dump/history sources cannot acquire them.
        evidence_sources = {source.path for source in self.sources.values() if re.search(
            r"\b(?:stagger_facts|stagger_capacity|stagger_count|stagger_steps|stagger_seal)\b", source.code)}
        self.assertEqual({path, "geometry-app/native/stagger_facts.inc", "geometry-core/subgrid_world.inc"},
                         evidence_sources, "ordered evidence must not enter World definitions, dump, or history")
        create = compact(masked(self.body(path, "app_world_candidate_create")))
        self.assertIn("&candidate->before,&candidate->after,live,sizeof(World)", create)
        self.assertIn("g_definition_revision,app_world_provider_stamp()", create)
        evidence_hash = compact(masked(self.body(path, "app_world_stagger_hash")))
        self.assertIn("candidate->operation.stagger_count*sizeof(WoodGridStaggerFact)", evidence_hash)
        seal = compact(masked(self.body(path, "app_world_candidate_seal")))
        self.assertIn("app_world_stagger_hash(candidate,candidate->operation.stagger_seal)", seal)
        self.assertIn("geo_sha256(&candidate->operation,sizeofcandidate->operation,candidate->operation_seal)", seal)
        for function in ("app_world_candidate_current", "app_world_candidate_publish"):
            body = compact(masked(self.body(path, function)))
            self.assertIn("app_world_stagger_current(candidate)", body)
            self.assertIn("candidate->operation_seal", body)
            self.assertIn("g_definition_revision", body)
            self.assertIn("app_world_provider_stamp()", body)
        confirm = compact(masked(self.body("current_geometry.c", "app_world_candidate_revalidate")))
        self.assertLess(confirm.index("app_world_candidate_current("), confirm.index("app_candidate_reopen("))
        self.assertLess(confirm.index("app_candidate_reopen("), confirm.index("app_world_candidate_evaluate("))
        self.assertLess(confirm.index("app_world_candidate_evaluate("), confirm.index("app_world_candidate_seal("))
        self.assertEqual(1, confirm.count("app_world_candidate_evaluate("))
        self.assertEqual(1, confirm.count("app_world_candidate_seal("))
        self.assertNotIn("app_world_candidate_clear_stagger(", confirm,
                         "confirmation must revalidate with the same sealed facts before releasing them")

    def test_cancel_failure_stale_success_and_disposal_release_ordered_evidence(self):
        path = "geometry-app/native/world_candidate.inc"
        clear = compact(masked(self.body(path, "app_world_candidate_clear_stagger")))
        for statement in ("free(candidate->stagger_facts)", "candidate->stagger_facts=NULL", "candidate->stagger_capacity=0",
                          "candidate->operation.stagger_count=0", "candidate->operation.stagger_steps=0"):
            self.assertIn(statement, clear)
        for function in ("app_world_candidate_discard", "app_world_candidate_destroy"):
            self.assertIn("app_world_candidate_clear_stagger(candidate)", compact(masked(self.body(path, function))))
        self.assertIn("app_world_candidate_destroy(g_preview.transaction)",
                      compact(masked(self.body("geometry-core/transactions.inc", "reference_stage"))))
        scene = self.body("geometry-core/transactions.inc", "apply_scene_line_candidate")
        cancel = block_after(scene, '!strcmp(tokens[0],"cancel-preview")')
        self.assertIn("app_world_candidate_discard(g_preview.transaction)", compact(masked(cancel)))
        confirm = block_after(scene, '!strcmp(tokens[0],"confirm")')
        for marker in ("g_preview.revision!=g_definition_revision", "!app_world_candidate_revalidate(", "!app_world_candidate_publish("):
            self.assertIn("app_world_candidate_discard(g_preview.transaction)", compact(masked(block_after(confirm, marker))),
                          "failed/stale DSL confirmation must release facts as well as invalidate the token")
        self.assertIn("app_world_candidate_clear_stagger(g_preview.transaction)", compact(masked(confirm)))
        batch = self.body("geometry-web/engineering_bridge.inc", "batch_confirm")
        for marker in ("g_history.grouping||", "!assembly_versions_immutable(", "!app_world_candidate_revalidate(", "!app_world_candidate_publish("):
            self.assertIn("app_world_candidate_discard(g_preview.transaction)", compact(masked(block_after(batch, marker))))
        self.assertIn("app_world_candidate_clear_stagger(g_preview.transaction)", compact(masked(batch)))
        self.assertIn("app_world_candidate_discard(g_preview.transaction)",
                      compact(masked(self.body("geometry-web/engineering_bridge.inc", "batch_cancel"))))
        preview = compact(masked(self.body("geometry-web/engineering_bridge.inc", "batch_preview")))
        self.assertLess(preview.index("app_world_candidate_seal("), preview.index("if(!ok)app_world_candidate_clear_stagger("),
                        "seal failure must clear facts before the invalid preview is retained")
        self.assertLess(preview.index("if(!ok)app_world_candidate_clear_stagger("), preview.index("reference_stage("))


if __name__ == "__main__":
    unittest.main(verbosity=2)
