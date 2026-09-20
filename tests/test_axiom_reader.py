#!/usr/bin/env python3
"""Targeted regression checks for canonical SSOT reader synchronization."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("reader_sync", ROOT / "geometry-guide/sync_axiom_reader.py")
reader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reader)


class CanonicalReader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = reader.CANONICAL.read_text(encoding="utf-8")
        cls.axiom = reader.AXIOM.read_text(encoding="utf-8")
        cls.plain = reader.PLAIN.read_text(encoding="utf-8")
        cls.state = json.loads(reader.script_text(cls.html, "axiom-review-data"))

    def test_five_asserts_and_ssot(self):
        result = reader.validate(self.html, self.axiom, self.plain)
        self.assertEqual(result["five_asserts"], "pass")
        self.assertEqual(result["independent_ssot"], "pass")

    def test_independent_line_scanner_matches_full_source_once(self):
        # Independent line scanner, not the generator's regular-expression parser.
        found, current, lines = {}, None, []
        for line in self.axiom.splitlines():
            if line.startswith("## "):
                if current:
                    found[current] = "\n".join(lines).rstrip("\n")
                    current, lines = None, []
                if line.startswith("## 四、"):
                    break
                continue
            first = line.removeprefix("**").split(" ", 1)[0]
            if re.fullmatch(r"[DIR][0-9]+[a-z]?", first):
                if current:
                    found[current] = "\n".join(lines).rstrip("\n")
                current, lines = first, [line]
            elif current:
                lines.append(line)
        self.assertEqual({c["id"]: c["body"] for c in self.state["clauses"]}, found)
        self.assertEqual(len(found), len(self.state["clauses"]))

    def test_rebuild_is_byte_idempotent_and_keeps_reviews(self):
        regenerated = reader.rebuild(self.html, self.axiom, self.plain)
        self.assertEqual(self.html, regenerated)
        state = json.loads(reader.script_text(regenerated, "axiom-review-data"))
        for key in ("documentId", "baseDocumentHash", "comments", "proposals", "revisions", "draft"):
            self.assertEqual(state[key], self.state[key], key)

    def test_self_consistent_wrong_source_is_rejected(self):
        state = copy.deepcopy(self.state)
        target = next(b for b in state["blocks"] if b["id"] == "D1.body.p01")
        target["source"] += "錯誤的額外條文"
        target["sourceHash"] = reader.digest(target["source"])
        clause = next(c for c in state["clauses"] if c["id"] == "D1")
        clause["body"] = "".join(b["source"] + b["separator"] for b in state["blocks"] if b["clauseId"] == "D1" and b["section"] == "body")
        state["documentHash"] = reader.digest(reader.compact([[b["id"], b["source"], b["separator"]] for b in state["blocks"]]))
        corrupted = reader.replace_script(self.html, "clause-data", reader.safe_json(state["clauses"]))
        corrupted = reader.replace_script(corrupted, "axiom-review-data", reader.safe_json(state))
        with self.assertRaisesRegex(AssertionError, "SSOT full body"):
            reader.validate(corrupted, self.axiom, self.plain)

    def test_wrong_visible_text_is_rejected(self):
        corrupted = self.html.replace('<p class="review-target">', '<p class="review-target">錯字', 1)
        with self.assertRaisesRegex(AssertionError, "assert 5 DOM"):
            reader.validate(corrupted, self.axiom, self.plain)

    def test_paragraph_insertion_retains_unchanged_block_ids(self):
        item = copy.deepcopy(next(c for c in self.state["clauses"] if c["id"] == "D1"))
        item["plain"] = "新加入的一段。\n\n" + item["plain"]
        blocks = reader.new_blocks(item, "plain", self.state["blocks"])
        old = [b for b in self.state["blocks"] if b["clauseId"] == "D1" and b["section"] == "plain"]
        for b in old:
            self.assertEqual(next(n for n in blocks if n["source"] == b["source"])["id"], b["id"])
        self.assertEqual(len(blocks), len(old) + 1)

    def test_review_merge_preserves_snapshots_and_rejects_conflicts(self):
        backup = copy.deepcopy(self.state)
        added = copy.deepcopy(backup["comments"][0])
        added["id"] = "C-test-import"
        added["userIntent"] = "驗證匯入保留原始定位快照。"
        backup["comments"].append(added)
        merged = reader.rebuild(self.html, self.axiom, self.plain, backup)
        reader.validate(merged, self.axiom, self.plain)
        state = json.loads(reader.script_text(merged, "axiom-review-data"))
        self.assertEqual(state["comments"][-1], added)
        self.assertNotEqual(state["snapshotId"], self.state["snapshotId"])
        self.assertEqual(state["comments"][:-1], self.state["comments"])
        backup["comments"][0]["userIntent"] = "同 ID 不同內容不可偷偷蓋過。"
        with self.assertRaisesRegex(ValueError, "Conflicting review record"):
            reader.rebuild(self.html, self.axiom, self.plain, backup)

    def test_original_text_precedes_plain(self):
        # GEO-147(🔒):頁尾寫「原文為準」,版面順序必須一致;89 條皆然。
        for clause in self.state["clauses"]:
            art = re.search(r'<article\b[^>]*(?<![\w-])id="' + clause["id"] + r'"[^>]*>.*?</article>',
                            self.html, re.S)
            self.assertIsNotNone(art, clause["id"])
            self.assertLess(art[0].find("original-section"), art[0].find("plain-section"), clause["id"])
            self.assertGreater(art[0].find("original-section"), 0, clause["id"])

    def test_geo120_decisions_are_not_regressed(self):
        # GEO-139:GEO-120 是 🔒 已拍板且未作廢,這幾項不得再被改掉。
        self.assertEqual(reader.geo120_regressions(self.html), [])
        self.assertIn('data-theme="dark"', re.search(r"<html[^>]*>", self.html)[0])
        js = reader.script_text(self.html, "reader-script")
        self.assertRegex(js, r"mode\s*=\s*'all'")
        self.assertIn("prefers-color-scheme", js)

    def test_counts_have_a_single_source(self):
        # GEO-140:HTML 裡出現的每個計數都必須等於由資料算出的值,且與 #reader-counts 一致。
        counts = json.loads(reader.script_text(self.html, reader.COUNTS_ID))
        self.assertEqual(counts, reader.reader_counts(self.html, self.state["clauses"], self.state))
        self.assertEqual(counts["clauses"], len(self.state["clauses"]))
        self.assertEqual(counts["comments"], len(self.state["comments"]))
        self.assertEqual(reader.stale_counts(self.html, counts), [])
        # 過期的硬編碼字樣不得再出現(這幾個是 2026-09-20 審查 R2 實際抓到的)
        for ghost in ("66 條", "1 / 63", "12 / 63", "文字 r1"):
            self.assertNotIn(ghost, self.html, ghost)

    def test_witness_figures_match_manifest_and_files(self):
        # GEO-132:manifest 裡每條有 svg 的條文,閱讀器都嵌一張;嵌的內容必須是同步器由當前檔案算出的那一張(讀檔,不跑引擎)。
        manifest = reader.load_witness_manifest()
        expected = {cid for cid in manifest if (reader.WITNESS_DIR / f"{cid}.svg").exists()}
        self.assertTrue(expected, "witness manifest has no figures")
        self.assertEqual(self.html.count('<section class="witness-section">'), len(expected))
        for cid in sorted(expected):
            article = re.search(r'<article\b[^>]*(?<![\w-])id="' + cid + r'"[^>]*>.*?</article>', self.html, re.S)[0]
            self.assertIn(reader.witness_figure(cid, manifest), article, cid)
        self.assertEqual(reader.validate(self.html, self.axiom, self.plain)["witness"], len(expected))

    def test_subclauses_are_disjoint_and_suffix_links_supported(self):
        clause = next(c for c in self.state["clauses"] if c["id"] == "I23")
        self.assertEqual(clause["body"].count("(a) 網格重宣告"), 1)
        self.assertNotIn("本條保護的是", clause["subs"]["c"])
        rendered = reader.render_inline_with_reader(self.html, ["I7a I8a D6c R6(e)"], self.state["clauses"])[0]
        for target in ("I7a", "I8a", "D6c", "R6"):
            self.assertIn(f'href="#{target}"', rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
