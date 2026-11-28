#!/usr/bin/env python3
"""X4 axiom index/status contracts; no new product module import in T."""
from contextlib import contextmanager
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "geometry-guide/axiom_matrix.py"
_spec = importlib.util.spec_from_file_location("x4_existing_axiom_matrix", MATRIX_PATH)
matrix = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(matrix)


def sha_lf(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


class AxiomTraceabilityContracts(unittest.TestCase):
    BODIES = {
        "D1": "**D1 精確值**：只保存明示資料。",
        "I1": "I1 候選提交：驗證同一候選。\n    本文不可被後一條吞入。",
        "R5": "R5 規則：名稱相同不是已核對的證據。",
    }

    @contextmanager
    def fixture(self):
        with tempfile.TemporaryDirectory(prefix="x4-triad-") as folder:
            root = Path(folder) / "repo"
            root.mkdir()
            (root / "公理層.md").write_text(
                "## 一、定義\n" + self.BODIES["D1"] + "\n\n## 二、不變量\n"
                + self.BODIES["I1"] + "\n\n## 三、推演規則\n" + self.BODIES["R5"] + "\n",
                encoding="utf-8", newline="\n")
            self.write_markers(root, [
                {"id": cid, "body_sha256": sha_lf(body.rstrip()), "status": "unreviewed",
                 "reason": "尚未完成語義核對；文字候選不構成實作證據。", "evidence": []}
                for cid, body in self.BODIES.items()
            ])
            yield root

    def write(self, root, relative, body):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8", newline="\n")
        return path

    def write_markers(self, root, entries, name="base.json"):
        return self.write(root, "geometry-guide/axiom-status.d/" + name,
                          json.dumps({"schema": "geometry-axiom-status/1", "entries": entries},
                                     ensure_ascii=False, sort_keys=True, indent=2) + "\n")

    def markers(self, root):
        return json.loads((root / "geometry-guide/axiom-status.d/base.json").read_text(encoding="utf-8"))["entries"]

    def set_entry(self, root, clause_id, **changes):
        entries = self.markers(root)
        for entry in entries:
            if entry["id"] == clause_id:
                entry.update(changes)
        self.write_markers(root, entries)

    def link(self, root, kind="implementation", path="geometry-core/guard.c", anchor="x4_guard"):
        content = "/* I1: explicit reviewed guard */\nint x4_guard(void) { return 1; }\n"
        self.write(root, path, content)
        return {"kind": kind, "path": path, "anchor": anchor, "source_sha256": sha_lf(content)}

    def invoke(self, root, check=False):
        command = [sys.executable, "-B", str(MATRIX_PATH), "--traceability", "--root", str(root), "--format", "json"]
        if check:
            command.append("--check-status")
        return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)

    def success(self, root, check=False):
        proc = self.invoke(root, check)
        self.assertEqual(proc.returncode, 0, "X4_VALID_INPUT_ACCEPTED: " + proc.stderr)
        self.assertTrue(proc.stdout.lstrip().startswith("{"), "X4_JSON_REPORT_REQUIRED: " + proc.stdout[:160])
        data = json.loads(proc.stdout)
        self.assertEqual(data["schema"], "geometry-axiom-status-check/1" if check else "geometry-axiom-triad/1",
                         "X4_REPORT_SCHEMA")
        return data, proc.stdout

    def rejection(self, root, code, check=True):
        proc = self.invoke(root, check)
        self.assertEqual(proc.returncode, 1, code + ": invalid input must exit 1")
        self.assertIn(code, proc.stderr, "X4_NAMED_DIAGNOSTIC: " + proc.stderr)
        self.assertFalse(proc.stdout.strip(), "X4_REJECT_MUST_NOT_EMIT_REPORT")

    def tree_bytes(self, root):
        return {path.relative_to(root).as_posix(): path.read_bytes()
                for path in sorted(root.rglob("*")) if path.is_file()}

    def test_json_is_deterministic_and_report_does_not_write_files(self):
        with self.fixture() as root:
            before = self.tree_bytes(root)
            first, raw = self.success(root)
            second, again = self.success(root)
            self.assertEqual(raw, again, "X4_DETERMINISTIC_REPORT_BYTES")
            self.assertEqual(first, second, "X4_DETERMINISTIC_REPORT_DATA")
            self.assertEqual([row["id"] for row in first["rows"]], ["D1", "I1", "R5"], "X4_EXACT_ORDERED_CLAUSES")
            self.assertRegex(first["source_digest"], r"^[0-9a-f]{64}$", "X4_SOURCE_DIGEST")
            self.assertEqual(first["scan_scope"]["inventory"], "filesystem-export", "X4_EXPORTED_TREE_SCOPE")
            self.assertIn("findings", first, "X4_FINDINGS_ARE_VISIBLE")
            self.assertEqual(before, self.tree_bytes(root), "X4_REPORT_IS_READ_ONLY")

    def test_status_only_guard_reports_exact_summary_and_does_not_write(self):
        with self.fixture() as root:
            before = self.tree_bytes(root)
            data, _ = self.success(root, check=True)
            self.assertEqual(data, {"schema": "geometry-axiom-status-check/1", "clauses": 3, "markers": 3, "missing": []},
                             "X4_EXACT_STATUS_SUMMARY")
            self.assertEqual(before, self.tree_bytes(root), "X4_STATUS_GUARD_IS_READ_ONLY")

    def test_current_ssot_has_one_status_marker_for_every_clause(self):
        data, _ = self.success(ROOT, check=True)
        source = (ROOT / "公理層.md").read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        ids = [row[0] for row in matrix.parse_clauses(source)]
        self.assertGreaterEqual(len(ids), 225, "X4_CURRENT_225_CLAUSES_MUST_NOT_SHRINK")
        self.assertEqual(len(ids), len(set(ids)), "X4_CURRENT_CLAUSES_UNIQUE")
        self.assertEqual((data["clauses"], data["markers"], data["missing"]), (len(ids), len(ids), []),
                         "X4_STATUS_COVERS_EVERY_CURRENT_CLAUSE")

    def test_new_clause_without_marker_is_rejected(self):
        with self.fixture() as root:
            with (root / "公理層.md").open("a", encoding="utf-8") as output:
                output.write("\n**R5a 新採納規則**：必須明列實作狀態。\n")
            self.rejection(root, "X4_STATUS_MISSING")

    def test_changed_clause_body_invalidates_old_marker(self):
        with self.fixture() as root:
            path = root / "公理層.md"
            path.write_text(path.read_text(encoding="utf-8").replace("驗證同一候選。", "驗證同一候選並核其來源。"), encoding="utf-8")
            self.rejection(root, "X4_STATUS_STALE_CLAUSE")

    def test_duplicate_marker_is_rejected_across_fragments(self):
        with self.fixture() as root:
            self.write_markers(root, [self.markers(root)[1]], name="duplicate.json")
            self.rejection(root, "X4_STATUS_DUPLICATE")

    def test_marker_for_unknown_clause_is_rejected(self):
        with self.fixture() as root:
            extra = dict(self.markers(root)[1], id="I999")
            self.write_markers(root, [extra], name="orphan.json")
            self.rejection(root, "X4_STATUS_UNKNOWN_CLAUSE")

    def test_invalid_status_schema_keys_and_state_are_rejected(self):
        with self.fixture() as root:
            path = root / "geometry-guide/axiom-status.d/base.json"
            original = json.loads(path.read_text(encoding="utf-8"))
            valid_evidence = self.link(root)
            changes = [
                ("schema", lambda doc: doc.update(schema="geometry-axiom-status/999")),
                ("top-level key", lambda doc: doc.update(extra=True)),
                ("entry key", lambda doc: doc["entries"][0].update(extra=True)),
                ("unknown state", lambda doc: doc["entries"][0].update(status="complete")),
                ("empty reason", lambda doc: doc["entries"][0].update(reason="  ")),
                ("wrong entries shape", lambda doc: doc.update(entries={})),
                ("wrong evidence shape", lambda doc: doc["entries"][0].update(evidence={})),
                ("non-string evidence kind", lambda doc: doc["entries"][1].update(evidence=[dict(valid_evidence, kind=[])])),
                ("unknown evidence key", lambda doc: doc["entries"][1].update(evidence=[dict(valid_evidence, extra=True)])),
                ("empty evidence anchor", lambda doc: doc["entries"][1].update(evidence=[dict(valid_evidence, anchor="  ")])),
                ("invalid evidence hash", lambda doc: doc["entries"][1].update(evidence=[dict(valid_evidence, source_sha256="bad")])),
            ]
            for name, change in changes:
                with self.subTest(case=name):
                    doc = copy.deepcopy(original)
                    change(doc)
                    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
                    self.rejection(root, "X4_STATUS_SCHEMA")
            path.write_text('{"schema":"geometry-axiom-status/1","schema":"geometry-axiom-status/1","entries":[]}', encoding="utf-8")
            self.rejection(root, "X4_STATUS_SCHEMA")

    def test_implemented_and_partial_require_reviewed_implementation(self):
        with self.fixture() as root:
            for state in ("implemented", "partial"):
                with self.subTest(state=state):
                    self.set_entry(root, "I1", status=state, evidence=[])
                    self.rejection(root, "X4_STATUS_SCHEMA")

    def test_unimplemented_needs_scoped_absence_evidence_and_rejects_implementation(self):
        with self.fixture() as root:
            self.set_entry(root, "I1", status="unimplemented", evidence=[])
            self.rejection(root, "X4_STATUS_SCHEMA")
            context = self.link(root, kind="context")
            self.set_entry(root, "I1", status="unimplemented", evidence=[context])
            data, _ = self.success(root)
            row = next(row for row in data["rows"] if row["id"] == "I1")
            self.assertEqual(row["effective_status"], "unimplemented", "X4_EXPLICIT_ABSENCE_STATUS")
            self.assertIn("axiom_without_implementation", row["gaps"], "X4_ABSENCE_GAP_VISIBLE")
            self.set_entry(root, "I1", evidence=[context, dict(context, kind="implementation")])
            self.rejection(root, "X4_STATUS_SCHEMA")

    def test_reviewed_implementation_does_not_invent_reviewed_tests(self):
        with self.fixture() as root:
            evidence = self.link(root)
            self.set_entry(root, "I1", status="implemented", evidence=[evidence])
            self.write(root, "tests/test_guess.py", "def test_guess():\n    assert 'I1'\n")
            data, _ = self.success(root)
            row = next(row for row in data["rows"] if row["id"] == "I1")
            self.assertEqual(row["declared_status"], "implemented", "X4_DECLARED_STATUS_PRESERVED")
            self.assertEqual(row["effective_status"], "implemented", "X4_FRESH_REVIEW_RETAINED")
            self.assertIs(row["reviewed_evidence"][0]["fresh"], True, "X4_REVIEW_FINGERPRINT_FRESH")
            self.assertIn("implementation_without_reviewed_test", row["gaps"], "X4_TEST_REFERENCE_IS_NOT_TEST_REVIEW")
            self.assertTrue(row["candidates"]["test"], "X4_TEST_CANDIDATE_EXISTS")

    def test_changed_evidence_downgrades_effective_status_without_rejecting_guard(self):
        with self.fixture() as root:
            evidence = self.link(root)
            self.set_entry(root, "I1", status="implemented", evidence=[evidence])
            before, _ = self.success(root)
            with (root / evidence["path"]).open("a", encoding="utf-8") as output:
                output.write("/* implementation changed; review must be repeated */\n")
            after, _ = self.success(root)
            self.success(root, check=True)
            row = next(row for row in after["rows"] if row["id"] == "I1")
            self.assertEqual(row["declared_status"], "implemented", "X4_HISTORY_IS_NOT_REWRITTEN")
            self.assertEqual(row["effective_status"], "unreviewed", "X4_STALE_REVIEW_CANNOT_ASSERT_IMPLEMENTED")
            self.assertIs(row["reviewed_evidence"][0]["fresh"], False, "X4_STALE_SOURCE_FINGERPRINT")
            self.assertIn("stale_review_evidence", row["gaps"], "X4_STALE_REVIEW_GAP")
            self.assertNotEqual(before["source_digest"], after["source_digest"], "X4_CHANGED_SOURCE_DIGEST")

    def test_findings_with_stale_sources_require_review(self):
        with self.fixture() as root:
            path = "tests/test_fixed.py"
            body = "def x4_fixed_judge():\n    assert True  # I1\n"
            self.write(root, path, body)
            finding = {
                "id": "X4_STALE_FINDING", "clauses": ["I1"],
                "clause_sha256": {"I1": sha_lf(self.BODIES["I1"].rstrip())},
                "kind": "test_spec_mismatch", "decision": "change_test",
                "state": "fixed_in_this_slice", "reason": "已核對這個裁判的修正。",
                "evidence": [{"kind": "test", "path": path, "anchor": "def x4_fixed_judge():",
                              "source_sha256": sha_lf(body)}],
            }
            self.write(root, "geometry-guide/axiom-review-findings.json",
                       json.dumps({"schema": "geometry-axiom-findings/1", "findings": [finding]},
                                  ensure_ascii=False) + "\n")
            before, _ = self.success(root)
            self.assertEqual(before["findings"][0]["state"], "fixed_in_this_slice",
                             "X4_FRESH_FINDING_RETAINS_REVIEWED_STATE")
            with (root / path).open("a", encoding="utf-8") as output:
                output.write("# The judged source changed after the recorded review.\n")
            after, _ = self.success(root)
            changed = after["findings"][0]
            self.assertEqual(changed["state"], "review_required",
                             "X4_STALE_FINDING_CANNOT_REMAIN_FIXED")
            self.assertEqual(changed.get("declared_state"), "fixed_in_this_slice",
                             "X4_FINDING_ORIGINAL_REVIEW_IS_PRESERVED")
            self.assertIs(changed["evidence"][0]["fresh"], False,
                          "X4_FINDING_SOURCE_CHANGE_IS_VISIBLE")
            clause = next(row for row in after["rows"] if row["id"] == "I1")
            self.assertIn("test_spec_mismatch", clause["gaps"],
                          "X4_STALE_FINDING_MISMATCH_RETURNS_TO_REVIEW")
            command = [sys.executable, "-B", str(MATRIX_PATH), "--traceability",
                       "--root", str(root), "--format", "md"]
            markdown = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
            self.assertEqual(markdown.returncode, 0, markdown.stderr)
            self.assertIn("來源已變", markdown.stdout,
                          "X4_MARKDOWN_STALE_FINDING_EVIDENCE_IS_VISIBLE")

    def test_findings_track_clause_versions(self):
        with self.fixture() as root:
            path = "tests/test_clause_judge.py"
            body = "def x4_clause_judge():\n    assert True  # I1\n"
            self.write(root, path, body)
            finding = {
                "id": "X4_CLAUSE_VERSION_FINDING", "clauses": ["I1"],
                "clause_sha256": {"I1": sha_lf(self.BODIES["I1"].rstrip())},
                "kind": "test_spec_mismatch", "decision": "change_test",
                "state": "fixed_in_this_slice", "reason": "已依當時 I1 文字核對裁判。",
                "evidence": [{"kind": "test", "path": path, "anchor": "def x4_clause_judge():",
                              "source_sha256": sha_lf(body)}],
            }
            self.write(root, "geometry-guide/axiom-review-findings.json",
                       json.dumps({"schema": "geometry-axiom-findings/1", "findings": [finding]},
                                  ensure_ascii=False) + "\n")
            before, _ = self.success(root)
            self.assertEqual(before["findings"][0]["state"], "fixed_in_this_slice",
                             "X4_SAME_CLAUSE_VERSION_RETAINS_FINDING")
            changed_body = self.BODIES["I1"] + "\n    新增條文要求必須重新核對既有裁定。"
            source = root / "公理層.md"
            source.write_text(source.read_text(encoding="utf-8").replace(self.BODIES["I1"], changed_body),
                              encoding="utf-8")
            self.set_entry(root, "I1", body_sha256=sha_lf(changed_body.rstrip()), status="unreviewed",
                           reason="新條文已有狀態標記，先前裁定仍待按新版本核對。")
            after, _ = self.success(root)
            changed = after["findings"][0]
            self.assertEqual(changed["state"], "review_required",
                             "X4_CHANGED_CLAUSE_CANNOT_KEEP_OLD_FINDING_FIXED")
            self.assertIs(changed.get("clause_fresh"), False,
                          "X4_FINDING_EXPOSES_CHANGED_CLAUSE_VERSION")
            self.assertEqual(changed.get("declared_state"), "fixed_in_this_slice",
                             "X4_CLAUSE_CHANGE_PRESERVES_DECLARED_FINDING")
            self.assertIs(changed["evidence"][0]["fresh"], True,
                          "X4_CLAUSE_ONLY_CHANGE_HAS_UNCHANGED_EVIDENCE_SOURCE")
            clause = next(row for row in after["rows"] if row["id"] == "I1")
            self.assertIn("test_spec_mismatch", clause["gaps"],
                          "X4_CLAUSE_CHANGE_REOPENS_REVIEW_GAP")

    def test_missing_or_nonunique_evidence_anchor_is_rejected(self):
        with self.fixture() as root:
            evidence = self.link(root)
            self.set_entry(root, "I1", status="implemented", evidence=[dict(evidence, anchor="absent_anchor")])
            self.rejection(root, "X4_EVIDENCE_ANCHOR")
            path = root / evidence["path"]
            path.write_text(path.read_text(encoding="utf-8") + "/* x4_guard */\n", encoding="utf-8")
            evidence["source_sha256"] = sha_lf(path.read_bytes())
            self.set_entry(root, "I1", evidence=[evidence])
            self.rejection(root, "X4_EVIDENCE_ANCHOR")

    def test_unsafe_evidence_paths_are_rejected(self):
        with self.fixture() as root:
            evidence = self.link(root)
            for path in ("../outside.c", str(root / evidence["path"]), "geometry-core/../guard.c", "geometry-core\\guard.c"):
                with self.subTest(path=path):
                    self.set_entry(root, "I1", status="implemented", evidence=[dict(evidence, path=path)])
                    self.rejection(root, "X4_PATH_UNSAFE")

    def test_symlink_evidence_is_rejected(self):
        with self.fixture() as root:
            evidence = self.link(root)
            target = root / evidence["path"]
            link = root / "geometry-core/alias.c"
            link.symlink_to(target)
            self.set_entry(root, "I1", status="implemented", evidence=[dict(evidence, path="geometry-core/alias.c")])
            self.rejection(root, "X4_PATH_UNSAFE")

    def test_browser_judges_are_test_candidates(self):
        with self.fixture() as root:
            paths = [
                "geometry-web/assembly_binding_source_browser_check.js",
                "geometry-web/evidence_links_browser_check.js",
                "geometry-web/grid_definition_interaction_browser_test.py",
                "geometry-web/grid_portable_browser_test.py",
                "geometry-web/grid_raw_provenance_browser_test.py",
                "geometry-web/model_update_browser_check.js",
                "geometry-web/native_reader_browser_test.py",
                "geometry-web/source_inspector_browser_check.js",
            ]
            for path in paths:
                body = ("def check_browser():\n    assert True  # I1\n" if path.endswith(".py")
                        else "test('I1 browser ownership', () => { assert.equal(true, true); });\n")
                self.write(root, path, body)
            data, _ = self.success(root)
            row = next(item for item in data["rows"] if item["id"] == "I1")
            self.assertEqual({item["path"] for item in row["candidates"]["test"]}, set(paths),
                             "X4_BROWSER_JUDGES_STAY_IN_TEST_COLUMN")
            self.assertEqual(row["candidates"]["implementation"], [],
                             "X4_BROWSER_JUDGES_ARE_NOT_PRODUCT_IMPLEMENTATIONS")
            self.assertFalse(set(paths) & {item["path"] for item in data["unbased_implementation_candidates"]},
                             "X4_BROWSER_JUDGES_ARE_NOT_UNBASED_PRODUCT_FILES")
            for path in paths:
                body = ("def check_browser():\n    assert True\n" if path.endswith(".py")
                        else "test('browser ownership', () => { assert.equal(true, true); });\n")
                self.write(root, path, body)
            unreferenced, _ = self.success(root)
            self.assertEqual(unreferenced["unbased_implementation_candidates"], [],
                             "X4_BROWSER_JUDGES_WITHOUT_CLAUSE_TOKENS_STAY_OUT_OF_UNBASED")

    def test_cross_layer_candidates_keep_named_judges_and_do_not_promote_status(self):
        with self.fixture() as root:
            sources = {
                "geometry-core/domain/guard.inc": "/* I1 */\nint core_guard(void) { return 1; }\n",
                "geometry-app/host.py": "def host_commit():\n    # I1\n    return True\n",
                "geometry-templates/spec.py": "def template_guard():\n    # I1\n    return True\n",
                "geometry-web/feature.js": "function preview() { return true; } // I1\n",
                "tests/fixtures/nested/case.scene": "# I1 nested fixture\n",
                "tests/test_named.py": "class Contract:\n    def test_i1_rejects_stale(self):\n        assert 'I1'\n",
                "tests/bridge_probe.c": "/* I1 real bridge assertion candidate */\nint probe(void) { return 1; }\n",
                "geometry-web/feature_test.js": "test('I1 rejects stale preview', () => {\n  assert.equal(actual, false); // I1\n});\n",
                "geometry-web/canvas_sections/PX4.js": "it('I1 canvas keeps candidate ownership', () => {\n  assert.equal(actual, false); // I1\n});\n",
                "geometry-web/review-label.js": "const label = 'R5 reviewed';\n",
            }
            for path, body in sources.items():
                self.write(root, path, body)
            data, _ = self.success(root)
            rows = {row["id"]: row for row in data["rows"]}
            implementation = rows["I1"]["candidates"]["implementation"]
            tests = rows["I1"]["candidates"]["test"]
            self.assertEqual({item["path"] for item in implementation}, {
                "geometry-core/domain/guard.inc", "geometry-app/host.py", "geometry-templates/spec.py", "geometry-web/feature.js",
            }, "X4_ALL_IMPLEMENTATION_LAYERS_AND_NO_TEST_MISCLASSIFICATION")
            self.assertEqual({item["path"] for item in tests}, {
                "tests/fixtures/nested/case.scene", "tests/test_named.py", "tests/bridge_probe.c",
                "geometry-web/feature_test.js", "geometry-web/canvas_sections/PX4.js",
            }, "X4_NESTED_SCENE_NATIVE_AND_BROWSER_TEST_SOURCES")
            self.assertTrue(any(item["path"] == "tests/test_named.py" and item["symbol"] == "test_i1_rejects_stale" for item in tests),
                            "X4_PYTHON_ASSERTION_NAME")
            self.assertTrue(any(item["path"] == "geometry-web/feature_test.js" and item["symbol"] == "I1 rejects stale preview" for item in tests),
                            "X4_JAVASCRIPT_ASSERTION_NAME")
            self.assertTrue(any(item["path"] == "geometry-web/canvas_sections/PX4.js" and item["symbol"] == "I1 canvas keeps candidate ownership" for item in tests),
                            "X4_CANVAS_ASSERTION_NAME")
            self.assertTrue(all(item["line"] > 0 and item["basis"] == "token-reference-unreviewed" for item in implementation + tests),
                            "X4_CANDIDATE_BASIS_AND_SOURCE_LINE")
            for clause_id in ("I1", "R5"):
                self.assertEqual(rows[clause_id]["effective_status"], "unreviewed", "X4_REFERENCE_AND_REVIEW_LABEL_DO_NOT_PROMOTE")
                self.assertEqual(rows[clause_id]["reviewed_evidence"], [], "X4_CANDIDATES_NEVER_BECOME_REVIEWED_EVIDENCE")

    def test_mutation_definition_is_named_but_not_an_execution_receipt(self):
        for relative in ("tests/mutation_cases.py", "tests/mutate.py", "tests/mutate_app.py"):
            with self.subTest(path=relative), self.fixture() as root:
                self.write(root, relative,
                           "CASES = [dict(id='WX4_STALE', desc='I1 stale confirmation guard', file='geometry-web/feature.js', old='guard', new='bypass')]\n")
                data, _ = self.success(root)
                row = next(row for row in data["rows"] if row["id"] == "I1")
                definitions = [item for item in row["candidates"]["mutation"] if item["basis"] == "mutation-definition-unrun"]
                self.assertEqual(len(definitions), 1, "X4_SINGLE_QUOTED_NAMED_MUTATION_DEFINITION")
                self.assertEqual((definitions[0]["symbol"], definitions[0]["target"]), ("WX4_STALE", "geometry-web/feature.js"),
                                 "X4_MUTATION_ID_AND_PRODUCT_TARGET")
                self.assertNotIn("killed", definitions[0], "X4_NO_INVENTED_MUTATION_RESULT")
                self.assertEqual(row["effective_status"], "unreviewed", "X4_DEFINITION_IS_NOT_EXECUTION")
                self.assertEqual(row["reviewed_evidence"], [], "X4_NO_INVENTED_MUTATION_RECEIPT")
                self.assertEqual(row["candidates"]["test"], [], "X4_MUTATOR_IS_NOT_TEST_JUDGE")
                self.assertIn("no_test_reference", row["gaps"], "X4_MUTATOR_DOES_NOT_HIDE_MISSING_JUDGE")

    def test_clause_tokens_do_not_match_prefixes_or_identifier_substrings(self):
        with self.fixture() as root:
            path = self.write(root, "geometry-core/token.c", "/* I10 xI1 I1z _I1 I1_ */\n")
            data, _ = self.success(root)
            row = next(row for row in data["rows"] if row["id"] == "I1")
            self.assertEqual(row["candidates"]["implementation"], [], "X4_EXACT_CLAUSE_TOKEN_BOUNDARY")
            path.write_text(path.read_text(encoding="utf-8") + "/* I1 */\n", encoding="utf-8")
            data, _ = self.success(root)
            row = next(row for row in data["rows"] if row["id"] == "I1")
            self.assertEqual([(item["path"], item["line"]) for item in row["candidates"]["implementation"]],
                             [("geometry-core/token.c", 2)], "X4_EXACT_REFERENCE_LOCATION")

    def test_source_without_direct_clause_reference_stays_a_review_candidate(self):
        with self.fixture() as root:
            self.write(root, "geometry-web/utility.js", "const usefulHelper = () => true;\n")
            self.write(root, "tests/test_utility.py", "def test_helper():\n    assert True\n")
            data, _ = self.success(root)
            candidates = data["unbased_implementation_candidates"]
            self.assertEqual([item["path"] for item in candidates], ["geometry-web/utility.js"], "X4_UNBASED_LIST_EXCLUDES_TESTS")
            self.assertIs(candidates[0]["review_required"], True, "X4_UNBASED_NEEDS_REVIEW")
            self.assertEqual(candidates[0]["classification"], "no-direct-axiom-reference", "X4_UNBASED_IS_NOT_SPEC_VIOLATION")

    def test_lf_and_crlf_sources_have_identical_semantic_fingerprints(self):
        with self.fixture() as root:
            evidence = self.link(root)
            self.set_entry(root, "I1", status="implemented", evidence=[evidence])
            before, _ = self.success(root)
            for relative in ("公理層.md", evidence["path"]):
                path = root / relative
                path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
            after, _ = self.success(root)
            self.assertEqual(before["source_digest"], after["source_digest"], "X4_LINE_ENDINGS_ARE_NOT_SOURCE_CHANGES")
            self.assertEqual(before["rows"], after["rows"], "X4_LF_NORMALIZED_CLAUSE_AND_EVIDENCE_HASHES")

    def test_accepted_scene_specs_do_not_carry_ignored_rejection_fields(self):
        tree = ast.parse((ROOT / "tests/run_tests.py").read_text(encoding="utf-8"))
        assignments = [node for node in tree.body if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == "TESTS" for target in node.targets)]
        self.assertEqual(len(assignments), 1, "X4_SCENE_ORACLE_TABLE_HAS_ONE_SOURCE")
        specs = ast.literal_eval(assignments[0].value)
        ignored = [(item["scene"], key) for item in specs if item.get("expect") == "accept"
                   for key in ("error", "error_not") if key in item]
        self.assertEqual(ignored, [], "X4_ACCEPT_HAS_NO_REJECTION_ERROR")

    def test_scene_reference_links_to_the_registered_judge_without_claiming_execution(self):
        with self.fixture() as root:
            self.write(root, "_x4.scene", "# I1 scenario\n")
            self.write(root, "tests/run_tests.py", "TESTS = [{'scene': '_x4.scene', 'expect': 'accept'}]\n")
            data, _ = self.success(root)
            row = next(item for item in data["rows"] if item["id"] == "I1")
            judges = [item for item in row["candidates"]["test"] if item["basis"] == "registered-scene-judge-unrun"]
            self.assertEqual(judges, [{"path": "tests/run_tests.py", "line": 1,
                                      "symbol": "run_one(_x4.scene)", "basis": "registered-scene-judge-unrun",
                                      "expected": "accept"}], "X4_SCENE_LINKS_TO_ITS_REAL_JUDGE")
            self.assertEqual(row["effective_status"], "unreviewed", "X4_SCENE_JUDGE_NOT_AN_EXECUTION_RECEIPT")

    def test_reviewed_evidence_outside_inventory_changes_source_digest(self):
        with self.fixture() as root:
            status_path = "docs/status-context.md"
            finding_path = "docs/finding-context.md"
            status_text = "status_scope: this operation is outside the implemented scope.\n"
            finding_text = "finding_scope: the scene comment contradicts its registered expectation.\n"
            self.write(root, status_path, status_text)
            self.write(root, finding_path, finding_text)
            self.set_entry(root, "I1", status="unimplemented", evidence=[{
                "kind": "context", "path": status_path, "anchor": "status_scope",
                "source_sha256": sha_lf(status_text),
            }])
            self.write(root, "geometry-guide/axiom-review-findings.json", json.dumps({
                "schema": "geometry-axiom-findings/1", "findings": [{
                    "id": "X4_HASH_REPRO", "clauses": ["I1"], "kind": "test_spec_mismatch",
                    "clause_sha256": {"I1": sha_lf(self.BODIES["I1"].rstrip())},
                    "decision": "change_test", "state": "open", "reason": "核對來源必須納入來源閉包。",
                    "evidence": [{"kind": "context", "path": finding_path, "anchor": "finding_scope",
                                  "source_sha256": sha_lf(finding_text)}],
                }],
            }, ensure_ascii=False))
            before, _ = self.success(root)
            self.assertIn(status_path, before["input_sha256"], "X4_INCLUDE_REVIEWED_STATUS_SOURCE")
            self.assertIn(finding_path, before["input_sha256"], "X4_INCLUDE_REVIEWED_FINDING_SOURCE")
            for relative in (status_path, finding_path):
                with self.subTest(path=relative):
                    path = root / relative
                    path.write_text(path.read_text(encoding="utf-8") + "Source changed after review.\n", encoding="utf-8")
                    after, _ = self.success(root)
                    self.assertEqual(after["input_sha256"][relative], sha_lf(path.read_bytes()), "X4_CURRENT_REVIEWED_SOURCE_HASH")
                    self.assertNotEqual(before["source_digest"], after["source_digest"], "X4_REVIEWED_SOURCE_CHANGE_INVALIDATES_DIGEST")
                    before = after


class AxiomMatrixClauseParsingTests(unittest.TestCase):
    def test_heading_forms_suffixes_and_plain_d_references(self):
        source = "\n".join([
            "## 一、定義",                  # 1
            "**D1 定義一**：正文",          # 2
            "D91 這是正文中的定義參照。",    # 3: not a heading
            "**D2a 定義後綴**：正文",        # 4
            "## 二、不變量",               # 5
            "I3 普通不變量：正文",           # 6
            "**I4 粗體不變量**：正文",       # 7
            "I5a 普通不變量後綴：正文",       # 8
            "**I6a 粗體不變量後綴**：正文",   # 9
            "I6ab 不是合法條號標題。",        # 10: not a heading
            "## 三、推演規則",             # 11
            "R7 普通規則：正文",             # 12
            "**R8 粗體規則**：正文",         # 13
            "R9a 普通規則後綴：正文",         # 14
            "**R10a 粗體規則後綴**：正文",    # 15
        ])
        parsed = matrix.parse_clauses(source)
        self.assertEqual([(row[0], row[1]) for row in parsed], [
            ("D1", 2), ("D2a", 4), ("I3", 6), ("I4", 7),
            ("I5a", 8), ("I6a", 9), ("R7", 12), ("R8", 13),
            ("R9a", 14), ("R10a", 15),
        ], "X4_PARSER_HEADING_FORMS_AND_SUFFIXES")
        by_id = {row[0]: row for row in parsed}
        self.assertIn("D91 這是正文中的定義參照。", by_id["D1"][3], "X4_PARSER_PLAIN_D_IS_BODY")
        self.assertIn("I6ab 不是合法條號標題。", by_id["I6a"][3], "X4_PARSER_REJECTS_LONG_SUFFIX")
        self.assertEqual(by_id["I4"][2], "粗體不變量", "X4_PARSER_BOLD_I_TITLE")
        self.assertEqual(by_id["R10a"][2], "粗體規則後綴", "X4_PARSER_BOLD_R_SUFFIX_TITLE")

    def test_bodies_stop_at_next_clause_or_section(self):
        source = "\n".join([
            "I1 第一條：前文", "第一條自己的內容提到 I2 與 R2。", "",
            "**I1a 第一條的後綴**：後綴正文", "D91 仍是本條正文。", "",
            "## 三、推演規則", "本章說明不屬於任何條文。", "",
            "**R2 新章規則**：規則正文", "    R2 的延續行以縮排表示如下：", "    R2 附加段", "",
            "## 四、不做什麼", "不做事項不屬於前面的 R2。", "",
        ])
        parsed = matrix.parse_clauses(source)
        self.assertEqual([row[0] for row in parsed], ["I1", "I1a", "R2"], "X4_PARSER_EXACT_BODY_OWNERS")
        by_id = {row[0]: row for row in parsed}
        self.assertEqual(by_id["I1"][3], "I1 第一條：前文\n第一條自己的內容提到 I2 與 R2。", "X4_PARSER_NEXT_CLAUSE_BOUNDARY")
        self.assertEqual(by_id["I1a"][3], "**I1a 第一條的後綴**：後綴正文\nD91 仍是本條正文。", "X4_PARSER_SECTION_BOUNDARY")
        self.assertEqual(by_id["R2"][3], "**R2 新章規則**：規則正文\n    R2 的延續行以縮排表示如下：\n    R2 附加段", "X4_PARSER_FINAL_SECTION_BOUNDARY")

    def test_current_ssot_keeps_five_bold_ir_clauses_separate(self):
        source = (ROOT / "公理層.md").read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        parsed = matrix.parse_clauses(source)
        by_id = {row[0]: row for row in parsed}
        self.assertEqual(len(parsed), len(by_id), "X4_PARSER_CURRENT_IDS_UNIQUE")
        self.assertTrue({"I63a", "I63b", "I63c", "R58a", "R58b"}.issubset(by_id), "X4_PARSER_CURRENT_FIVE_BOLD_IR")
        for clause_id, following in [
            ("I63a", "**I63b "), ("I63b", "**I63c "), ("I63c", "I64 "),
            ("R58a", "**R58b "), ("R58b", "R59 "),
        ]:
            with self.subTest(clause=clause_id):
                start = source.index("\n**" + clause_id + " ") + 1
                end = source.index("\n" + following, start)
                self.assertEqual(by_id[clause_id][1], source.count("\n", 0, start) + 1, "X4_PARSER_CURRENT_SOURCE_LINE")
                self.assertEqual(by_id[clause_id][3], source[start:end].rstrip(), "X4_PARSER_CURRENT_EXACT_BODY")
        self.assertNotIn("\n**I63a ", by_id["I63"][3], "X4_PARSER_I63_DOES_NOT_SWALLOW")
        self.assertNotIn("\n**R58a ", by_id["R58"][3], "X4_PARSER_R58_DOES_NOT_SWALLOW")



if __name__ == "__main__":
    unittest.main(verbosity=2)
