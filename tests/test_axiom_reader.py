#!/usr/bin/env python3
"""Targeted regression checks for canonical SSOT reader synchronization."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest import mock

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
            if re.fullmatch(r"[DIR][0-9]+[a-z]?", first) and (line.startswith("**") or first[0] in "IR"):
                if current:
                    found[current] = "\n".join(lines).rstrip("\n")
                current, lines = first, [line]
            elif current:
                lines.append(line)
        self.assertEqual({c["id"]: c["body"] for c in self.state["clauses"]}, found)
        self.assertEqual(len(found), len(self.state["clauses"]))

    def test_plain_leading_definition_reference_stays_in_body(self):
        clauses=reader.source_clauses(self.axiom)
        self.assertEqual(1,sum(c['id']=='D31' for c in clauses))
        self.assertIn('D31 的參數值',next(c['body'] for c in clauses if c['id']=='D1'))

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

    def test_review_merge_rejects_conflicts_inside_one_backup(self):
        """GEO-155:衝突不只發生在「備份 vs 現況」,也發生在備份自己內部。"""
        backup = copy.deepcopy(self.state)
        first = copy.deepcopy(backup["comments"][0])
        first["id"] = "C-test-duplicate"
        first["userIntent"] = "第一筆。"
        second = copy.deepcopy(first)
        second["userIntent"] = "同 ID、不同內容的第二筆。"
        backup["comments"] += [first, second]
        with self.assertRaisesRegex(ValueError, "Conflicting review record"):
            reader.rebuild(self.html, self.axiom, self.plain, backup)

    def test_review_merge_takes_an_exact_repeat_only_once(self):
        """一字不差的重複只是冗餘,不是衝突——但也只能收一次。

        修好之前這裡會收下兩筆同 ID 的批註。
        """
        backup = copy.deepcopy(self.state)
        added = copy.deepcopy(backup["comments"][0])
        added["id"] = "C-test-repeat"
        backup["comments"] += [added, copy.deepcopy(added)]
        merged = reader.rebuild(self.html, self.axiom, self.plain, backup)
        reader.validate(merged, self.axiom, self.plain)
        state = json.loads(reader.script_text(merged, "axiom-review-data"))
        ids = [c["id"] for c in state["comments"]]
        self.assertEqual(ids.count("C-test-repeat"), 1)
        self.assertEqual(len(ids), len(set(ids)), "批註 ID 必須唯一")

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

    def test_stale_comments_can_be_reanchored_in_place(self):
        # GEO-144(🔒 Q2):過期批註要就地給下一步,且不得再用 confirm() 叫使用者盲簽。
        js = reader.script_text(self.html, "review-script")
        self.assertIn("stale-actions", js)
        self.assertIn("reanchorConfirm", js)
        self.assertIn("undoReanchor", js)
        self.assertNotIn("將這則批註重新綁定到", js)      # 舊的 confirm() 文案
        self.assertIn(".stale-actions{display:flex", self.html)
        self.assertIn(".reanchor-diff{display:grid", self.html)

    def test_witness_figures_are_inline_and_themed(self):
        # GEO-141 最後一段(🔒 Q8):見證圖改 inline svg 由頁面 CSS 控色;範例圖維持 base64。
        counts = json.loads(reader.script_text(self.html, reader.COUNTS_ID))
        self.assertEqual(self.html.count('<svg class="witness-diagram"'), counts["witness"])
        sections = re.findall(r'<section class="witness-section">.*?</section>', self.html, re.S)
        self.assertEqual(len(sections), counts["witness"])
        for sec in sections:
            self.assertNotIn("base64", sec)
            self.assertNotIn("<style", sec)
        for token, (light, dark) in reader.WITNESS_TOKENS.items():
            self.assertIn("%s:%s" % (token, light), self.html, token)
            self.assertIn("%s:%s" % (token, dark), self.html, token)
        # 角色色是 🔒 Q1 定案的字面值,不得被 token 化
        self.assertIn(".witness-diagram .role-boundary{fill:#e2a24a", self.html)

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

    def test_retired_color_migrations_keep_each_historical_input_compatible(self):
        for old, new in reader.COLOR_REWRITES:
            with self.subTest(old=old):
                if new:
                    self.assertIn(new, self.html)
                    historical = self.html.replace(new, old, 1)
                else:
                    historical = self.html.replace("</style>", old + "</style>", 1)
                reader.PATCHES.reset()
                current = reader.apply_color_tokens(historical)
                self.assertEqual(current, self.html)
                self.assertEqual(reader.PATCHES.verify(current), [])
                self.assertTrue(any(label.startswith("歷史色碼相容:") for label, _ in reader.PATCHES.present + reader.PATCHES.absent))

    def test_retired_color_migrations_allow_format_and_unrelated_layout_changes(self):
        formatted = self.html
        for old, new in reader.COLOR_REWRITES:
            if not new:
                continue
            # Format declarations only. Whitespace in a descendant selector has
            # meaning and must not be blindly stripped or introduced.
            if "{" in new:
                selector, declarations = new.split("{", 1)
                replacement = selector + "{ /* formatted declarations */ " + declarations.replace(":", ": ").replace(";", "; ")
            else:
                replacement = new.replace(":", ": ").replace(";", "; ")
            self.assertIn(new, formatted)
            formatted = formatted.replace(new, replacement, 1)
        formatted = formatted.replace(".stale-note{ font-size: 12px;", ".stale-note{ font-size: 13px;", 1)
        rebuilt = reader.rebuild(formatted, self.axiom, self.plain)
        self.assertEqual(formatted, rebuilt)
        self.assertEqual(reader.validate(rebuilt, self.axiom, self.plain)["five_asserts"], "pass")
        self.assertFalse(any(label.startswith("歷史色碼相容:") for label, _ in reader.PATCHES.present + reader.PATCHES.absent))

    def test_retired_color_contracts_reject_each_lost_or_wrong_declaration(self):
        for selector, required in reader.COLOR_CONTRACTS:
            if required is None:
                addition = selector + "{color:var(--ink)}"
            else:
                property_name = next(iter(required))
                addition = selector + "{" + property_name + ":var(--ink)}"
            broken = self.html.replace('<script id="reader-counts"', '<style>' + addition + '</style><script id="reader-counts"', 1)
            with self.subTest(selector=selector):
                self.assertTrue(reader.color_contract_regressions(broken))
                with self.assertRaisesRegex(ValueError, "reader color contract"):
                    reader.rebuild(broken, self.axiom, self.plain)
                with self.assertRaisesRegex(AssertionError, "reader color contract"):
                    reader.validate(broken, self.axiom, self.plain)

    def test_traceability_lights_and_hub_badges_exist(self):
        # GEO-139(4):GEO-120 的連帶約束明列「追溯燈號 / 三向連結 / 樞紐徽章」不得丟失。
        # 判準:綠 = 原始碼且夾具、黃 = 其一、紅 = 皆無;樞紐 = 被引用數 >= 3。
        # 不得另立門檻;出處見 sync_axiom_reader.py 的 TRACE_CSS 註解(GEO-167)。
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

    def test_every_patch_actually_lands(self):
        # 這個管線最常見的失效不是「補丁做錯」,而是「補丁被靜默跳過」——
        # 補丁對一份會演化的產物做文字替換,而「有沒有套用過」是用改前/改後的樣子判定的,
        # 被改的內容一變,判定就失效。登記簿在同步結束時一次驗完,並指名是哪一個補丁。
        reader.PATCHES.reset()
        regenerated = reader.rebuild(self.html, self.axiom, self.plain)
        self.assertGreater(len(reader.PATCHES), 50)          # 有真的登記,不是空跑
        self.assertEqual(reader.PATCHES.verify(regenerated), [])

    def test_force_marker_registers_new_applied_and_evolved_paths(self):
        for source in ("OLD", "NEW MARK", "later UI MARK"):
            with self.subTest(source=source), mock.patch.object(reader, "PATCHES", reader.PatchLog()):
                out = reader.force(source, "OLD", "NEW MARK", "QR4", marker="MARK")
                self.assertEqual(reader.PATCHES.present, [("QR4", "MARK")])
                self.assertEqual(reader.PATCHES.verify(out), [])
                self.assertTrue(reader.PATCHES.verify(out.replace("MARK", "")))
                self.assertEqual(reader.force(out, "OLD", "NEW MARK", "QR4", marker="MARK"), out)

    def test_force_marker_rejects_ambiguity_and_drift_before_registering(self):
        cases = [("OLD OLD", "NEW MARK", "MARK"), ("MARK MARK", "NEW MARK", "MARK"),
                 ("neither", "NEW MARK", "MARK"), ("OLD", "NEW", "MARK"),
                 ("OLD", "NEW MARK MARK", "MARK"), ("OLD", "NEW", "")]
        for source, new, marker in cases:
            with self.subTest(source=source, new=new, marker=marker), mock.patch.object(reader, "PATCHES", reader.PatchLog()):
                with self.assertRaisesRegex(ValueError, "reader template"):
                    reader.force(source, "OLD", new, "QR4", marker=marker)
                self.assertEqual(len(reader.PATCHES), 0)

    def test_force_unmarked_success_paths_keep_registry_and_uniqueness(self):
        for source, old, new, expected in [("OLD", "OLD", "NEW", "NEW"),
                ("NEW", "OLD", "NEW", "NEW"), ("OLD", "OLD", "OLD PLUS", "OLD PLUS"),
                ("OLD PLUS", "OLD", "OLD PLUS", "OLD PLUS"),
                ("OLD", "OLD", "", ""), ("gone", "OLD", "", "gone")]:
            with self.subTest(source=source, new=new), mock.patch.object(reader, "PATCHES", reader.PatchLog()):
                out = reader.force(source, old, new, "QR4")
                self.assertEqual(out, expected)
                self.assertEqual(len(reader.PATCHES), 1)
                self.assertEqual(reader.PATCHES.verify(out), [])
                broken = out + old if not new else out.replace(new, "")
                self.assertTrue(reader.PATCHES.verify(broken))
        for source in ("OLD OLD", "NEW NEW", "neither"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                reader.force(source, "OLD", "NEW", "QR4")

    def test_visible_witness_counts_reject_independent_tampering(self):
        counts = json.loads(reader.script_text(self.html, reader.COUNTS_ID))
        for n, w in [(counts["clauses"] + 1, counts["witness"]),
                     (counts["clauses"], counts["witness"] + 1)]:
            corrupted = re.sub(r'(id="workspace-witness-none"[^>]*>)[^<]*',
                lambda m: m[1] + f"這一條沒有見證圖({n} 條中有 {w} 條有)。", self.html)
            with self.subTest(n=n, w=w), self.assertRaisesRegex(AssertionError, "workspace-witness-none"):
                reader.validate(corrupted, self.axiom, self.plain)

    def test_clause_and_witness_fixture_add_remove_updates_visible_counts(self):
        # In-memory source/manifest fixtures only; never edit SSOT or witness files.
        axiom = self.axiom.replace("## 四、", "R900 測試計數：本條僅為同步測試夾具。\n\n## 四、", 1)
        plain = self.plain + "\n\n## R900\n僅為同步測試夾具。\n"
        manifest = reader.load_witness_manifest()
        witness = next(cid for cid in manifest if (reader.WITNESS_DIR / f"{cid}.svg").exists())
        reduced = {cid: entry for cid, entry in manifest.items() if cid != witness}
        with mock.patch.object(reader, "load_witness_manifest", return_value=reduced):
            added = reader.rebuild(self.html, axiom, plain)
            report = reader.validate(added, axiom, plain)
        self.assertEqual(report["clauses"], len(self.state["clauses"]) + 1)
        counts = json.loads(reader.script_text(self.html, reader.COUNTS_ID))
        self.assertEqual(report["witness"], counts["witness"] - 1)
        self.assertIn(f'這一條沒有見證圖({report["clauses"]} 條中有 {report["witness"]} 條有)。', added)
        restored = reader.rebuild(added, self.axiom, self.plain)
        restored_report = reader.validate(restored, self.axiom, self.plain)
        self.assertEqual(restored_report["clauses"], counts["clauses"])
        self.assertEqual(restored_report["witness"], counts["witness"])
        restored_counts = json.loads(reader.script_text(restored, reader.COUNTS_ID))
        self.assertEqual(reader.stale_counts(restored, restored_counts), [])
        for output in (added, restored):
            state = json.loads(reader.script_text(output, "axiom-review-data"))
            for key in ("documentId", "baseDocumentHash", "comments", "proposals", "revisions", "draft"):
                self.assertEqual(state[key], self.state[key], key)

    def test_workspace_has_one_witness_function_and_event_handler(self):
        js = reader.script_text(self.html, "workspace-script")
        self.assertEqual(js.count("function renderWitness("), 1)
        self.assertEqual(js.count("function toast("), 1)
        self.assertEqual(js.count("e=>renderWitness(e.detail&&e.detail.id)"), 1)
        self.assertIn("source.cloneNode(true)", js)
        self.assertNotIn("article.querySelector('.witness-section figure img')", js)
        for extra in ("function renderWitness(id){}", "document.addEventListener('axiom:current',e=>renderWitness(e.detail&&e.detail.id));"):
            corrupted = reader.replace_script(self.html, "workspace-script", js + extra)
            with self.subTest(extra=extra), self.assertRaisesRegex(AssertionError, "QR5"):
                reader.validate(corrupted, self.axiom, self.plain)

    def test_legacy_image_handler_retires_without_changing_live_svg_handler(self):
        legacy = reader.LEGACY_WITNESS_PANE_JS
        js = reader.script_text(self.html, "workspace-script")
        historical = reader.replace_script(self.html, "workspace-script", legacy + js)
        updated = reader.rebuild(historical, self.axiom, self.plain)
        self.assertEqual(updated, self.html)
        malformed = reader.replace_script(self.html, "workspace-script", js + "article.querySelector('.witness-section figure img');")
        with self.assertRaisesRegex(ValueError, "歷史見證圖面板"):
            reader.rebuild(malformed, self.axiom, self.plain)

    def test_counts_have_a_single_source(self):
        # GEO-140:HTML 裡出現的每個計數都必須等於由資料算出的值,且與 #reader-counts 一致。
        counts = json.loads(reader.script_text(self.html, reader.COUNTS_ID))
        self.assertEqual(counts, reader.reader_counts(self.html, self.state["clauses"], self.state))
        self.assertEqual(counts["clauses"], len(self.state["clauses"]))
        self.assertEqual(counts["comments"], len(self.state["comments"]))
        self.assertEqual(reader.stale_counts(self.html, counts), [])
        # 過期的硬編碼字樣不得再出現(這幾個是 2026-09-20 審查 R2 實際抓到的)。
        # 要帶數字邊界:textRevision 走到 r10 之後,「文字 r1」變成真值的子字串,
        # 純子字串比對會誤判(GEO-168 實際踩到);「1 / 63」對「11 / 63」同理。
        for ghost in ("66 條", "1 / 63", "12 / 63", "文字 r1"):
            self.assertIsNone(
                re.search(r"(?<!\d)" + re.escape(ghost) + r"(?!\d)", self.html), ghost)

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
