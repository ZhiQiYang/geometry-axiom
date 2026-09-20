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

    def test_mid_width_uses_half_sheet_and_mobile_bar_has_four_keys(self):
        # GEO-148(🔒 Q6):960–1279px 不得再用全螢幕 modal 蓋住正文;手機底部列只留四鍵。
        ws = reader.script_text(self.html, "workspace-script")
        self.assertIn("min-width:960px) and (max-width:1279px", ws)
        self.assertIn("halfSheet()", ws)
        self.assertIn("body.half-sheet-open{padding-bottom:52dvh}", self.html)
        self.assertIn('.bottom-bar .bottom-inner>[data-review-action="list"]{display:none}', self.html)
        self.assertIn(".bottom-bar .bottom-inner button{font-size:14px", self.html)

    def test_workspace_shows_witness_and_keeps_draft(self):
        # GEO-138 + GEO-146(🔒 Q4):右欄上半固定見證圖;切分頁前先保留草稿並告知。
        self.assertIn('id="workspace-witness"', self.html)
        self.assertIn('id="workspace-witness-img"', self.html)
        ws = reader.script_text(self.html, "workspace-script")
        self.assertIn("renderWitness", ws)
        self.assertIn("axiom:current", ws)
        self.assertIn("flushDraft();toast('草稿已保留')", ws)
        # 面板必須排在分頁列之前(上半固定、下半 tab)
        self.assertLess(self.html.index('id="workspace-witness"'),
                        self.html.index('class="workspace-tabs"'))

    def test_facet_chips_are_data_driven(self):
        # GEO-149:chip 的數量必須等於實際資料,且不得有硬編碼條號白名單
        # (被作廢的第 3 版原型正是寫死 ['R6','R18','R19','R20','R21'])。
        self.assertIn('class="toc-facets', self.html)
        counts = dict(re.findall(r'data-facet="(\w+)" href="#[^"]+">[^<]*<b>(\d+)</b>', self.html))
        items = re.findall(r'<a class="toc-item"[^>]*>', self.html)
        self.assertEqual(len(items), len(self.state["clauses"]))

        def positive(attr):
            return sum(1 for it in items
                       if int((re.search(attr + r'="(\d+)"', it) or [0, "0"])[1]) > 0)

        self.assertEqual(int(counts["ex"]), positive("data-ex"))
        self.assertEqual(int(counts["wit"]), positive("data-wit"))
        self.assertEqual(int(counts["note"]), positive("data-note"))
        self.assertEqual(int(counts["none"]), sum(1 for it in items if 'data-trace="none"' in it))
        self.assertIn("facetMatch", reader.script_text(self.html, "reader-script"))

    def test_block_tools_are_not_always_on(self):
        # GEO-145(🔒 Q3):正文不得被 452 組控制列切碎;已有批註的段落仍常駐。
        self.assertIn(".review-block>.block-tools{opacity:0", self.html)
        self.assertIn(".review-block.has-comments>.block-tools", self.html)
        self.assertIn(".review-block:focus-within>.block-tools", self.html)
        self.assertIn("pressTimer", reader.script_text(self.html, "reader-script"))

    def test_colors_are_tokenised(self):
        # GEO-141(🔒 Q1):批註四色與圖面底色收成 token,深色只改 token 值,不再逐條選擇器補丁。
        self.assertEqual(reader.hardcoded_colors(self.html), [])
        for token, (light, dark) in reader.COLOR_TOKENS.items():
            if light:
                self.assertIn("%s:%s" % (token, light), self.html, token)
            if dark:
                self.assertIn("%s:%s" % (token, dark), self.html, token)
        # 深色不得再靠逐條選擇器補丁救色
        for patched in (":root[data-theme=dark] .ex.no .badge", ":root[data-theme=dark] .dsl>span.hit"):
            self.assertNotIn(patched, self.html, patched)
        self.assertIn("outline:2px solid var(--accent);outline-offset:4px", self.html)
        self.assertNotIn("#288b9c", self.html)

    def test_traceability_lights_and_hub_badges_exist(self):
        # GEO-139(4):GEO-120 的連帶約束明列「追溯燈號 / 三向連結 / 樞紐徽章」不得丟失。
        # 定義沿用 make_axiom_reader.py 原本的那一組,不得另立門檻。
        incoming = {c["id"]: [] for c in self.state["clauses"]}
        for c in self.state["clauses"]:
            for ref in sorted({m[1] for m in reader.CLAUSE_REF.finditer(c["body"]) if m[1] != c["id"]}):
                if ref in incoming:
                    incoming[ref].append(c["id"])
        trace = reader.clause_trace(self.state["clauses"], incoming)
        self.assertEqual(len(trace), len(self.state["clauses"]))
        for cid, t in trace.items():
            self.assertIn(t["light"], ("ok", "partial", "none"))
            self.assertEqual(t["hub"], t["incoming"] >= 3)          # 門檻與舊產生器一致
            self.assertEqual(t["light"], "ok" if (t["functions"] and t["scenes"])
                             else ("partial" if (t["functions"] or t["scenes"]) else "none"))
            self.assertIn('data-clause="%s" data-trace="%s"' % (cid, t["light"]), self.html, cid)
        self.assertEqual(self.html.count('<details class="trace-section">'), len(trace))
        self.assertEqual(self.html.count('class="badge-hub"'), sum(1 for t in trace.values() if t["hub"]))

    def test_search_keeps_query_after_navigating(self):
        # GEO-142(審查 R7):跳轉不得清空查詢;Enter 連跳下一筆;狀態列顯示第 n / m 筆。
        self.assertEqual(reader.search_regressions(self.html), [])
        js = reader.script_text(self.html, "reader-script")
        self.assertNotIn("resetSearch();sync();", js)
        self.assertIn("' · 第 '+(keyboardIndex+1)+' / '+visibleResults.length+' 筆'", js)

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
        self.assertIn("ref-preview", js)                      # 拍板二:hover 預覽與固定面板並存
        self.assertIn("#ref-preview{position:fixed", self.html)

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
