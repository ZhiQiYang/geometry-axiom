"""GEO-261 P0: independently check the unapproved proposal against the SSOT.

This is a proposal-integrity gate, not evidence that domain decoupling exists.
P0 compares current SSOT with ``before``. After explicit approval, P1 must
deliberately migrate this gate to compare adopted ``after`` with the SSOT while
preserving ``before`` and its provenance. Never edit historical ``before`` or
remove this gate merely to make an adopted revision pass.

GEOMETRY_PROPOSAL_ROOT permits running a temporary mutant of this test file
against the same repository, without modifying the official source or tests.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import unittest


ROOT = Path(os.environ.get("GEOMETRY_PROPOSAL_ROOT", Path(__file__).resolve().parents[1]))
PROPOSAL_DIR = ROOT / "geometry-core" / "domain-decoupling"
BASE_REVISION = "1c80751150d0767ba52509537caf8d5542769ccb"
BASE_SOURCE_SHA256 = "ab31dc36d5416762ac44932940a94f6142b72e831ceb62c0bc67375512109004"
SCHEMA = "geo261-clause-proposal/1"
CLAUSE_HEADER = re.compile(r"^(?:\*\*(D[0-9]+[a-z]?) |([IR][0-9]+[a-z]?) )")
OMISSIONS = {"略", "（略）", "(略)", "同上", "同前", "同原文", "其餘同原文", "...", "…", "TODO", "TBD"}
LEGACY_MARKERS = tuple(
    "\n\n" + label + "：以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。\n\n"
    for label in ("固定木工模板契約（W）", "宿主及相容契約（H）")
)


class ProposalContractError(AssertionError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__(f"{code}: {detail}")


def require(condition, code, detail):
    if not condition:
        raise ProposalContractError(code, detail)


def normalized(raw):
    """Only checkout CRLF is insignificant; all other bytes remain evidence."""
    return raw.replace(b"\r\n", b"\n").decode("utf-8")


def clause_id(line):
    match = CLAUSE_HEADER.match(line)
    return (match.group(1) or match.group(2)) if match else None


@dataclass(frozen=True)
class SourceClause:
    id: str
    before: str
    start: int
    end: int


def source_layout(source):
    """Independent line walk; does not import the proposal/reader generators."""
    starts, boundaries, headings = [], [], []
    offset = 0
    for line in source.splitlines(keepends=True):
        cid = clause_id(line)
        if cid:
            starts.append((cid, offset))
            boundaries.append(offset)
        if line.startswith("## "):
            boundaries.append(offset)
            headings.append((line.rstrip("\n"), offset))
        offset += len(line)
    boundaries.append(len(source))
    clauses = []
    for cid, start in starts:
        end = next(boundary for boundary in boundaries if boundary > start)
        text = source[start:end].rstrip("\n")
        clauses.append(SourceClause(cid, text, start, start + len(text)))
    require(bool(clauses), "SOURCE_LAYOUT", "SSOT has no clause headers")
    tails = [offset for title, offset in headings if title.startswith("## 四、")]
    require(len(tails) == 1, "SOURCE_LAYOUT", "SSOT needs exactly one exclusions section")
    sections = {"preamble": (0, clauses[0].start), "exclusions": (tails[0], len(source))}
    return clauses, sections, headings


def source_legacy_body(clause):
    """Remove only the source header wrapper, never a substantive source line."""
    if clause.id.startswith("D"):
        header_end = clause.before.find("**", 2)
        require(header_end != -1, "SOURCE_LAYOUT", f"{clause.id}: missing definition header end")
        body = clause.before[header_end + 2:]
        if body[:1] in ("：", ":"):
            body = body[1:]
        return body.lstrip("\n")
    return clause.before[len(clause.id) + 1:]


def preamble_scope_lists(preamble):
    return re.findall(r"^- \*\*([KMWH]) [^*\n]+\*\*：([^\n]+)。$", preamble, re.MULTILINE)


def markdown_blocks(markdown):
    """Locate review headings outside fences, retaining literal payload newlines."""
    starts = []
    offset = 0
    fenced = False
    for line in markdown.splitlines(keepends=True):
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("### "):
            starts.append((line[4:].rstrip("\n"), offset, offset + len(line)))
        offset += len(line)
    require(not fenced, "MARKDOWN_BLOCK", "unclosed fenced text")
    blocks = []
    for index, (key, start, payload_start) in enumerate(starts):
        end = starts[index + 1][1] if index + 1 < len(starts) else len(markdown)
        blocks.append((key, markdown[payload_start:end], start, end))
    intro = markdown[:starts[0][1]] if starts else markdown
    return intro, blocks


def block_payload(block, key):
    # The single LF directly before each closing fence is a wrapper, not payload.
    # A section ending in LF therefore has TWO LFs before the closing fence.
    pattern = (r"\n*#### 修改前\n\n?```text\n(.*?)\n```\n\n+"
               r"#### 修改後\n\n?```text\n(.*?)\n```\n\n+"
               r"#### 理由\n\n?([^\n]+)\n*")
    match = re.fullmatch(pattern, block, re.DOTALL)
    require(match is not None, "MARKDOWN_BLOCK", f"{key}: before/after/reason block is incomplete")
    return match.groups()


def validate_proposal(source_bytes, proposal, markdown):
    """Return an in-memory proposed document; never write or adopt the proposal."""
    source = normalized(source_bytes)
    source_clauses, source_sections, headings = source_layout(source)
    require(type(proposal) is dict and set(proposal) == {
        "schema", "status", "baseRevision", "sourceSha256", "clauses", "sections"
    }, "SCHEMA", "unexpected top-level proposal fields")
    require(proposal["schema"] == SCHEMA, "SCHEMA", "unsupported proposal schema")
    require(proposal["status"] == "proposed-not-approved", "STATUS", "P0 cannot declare adoption")
    require(proposal["baseRevision"] == BASE_REVISION, "BASE_REVISION", "proposal base revision changed")
    require(proposal["sourceSha256"] == BASE_SOURCE_SHA256 == hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "SOURCE_HASH", "proposal and independently read SSOT must match the pinned P0 baseline")
    rows = proposal["clauses"]
    require(type(rows) is list and all(type(row) is dict for row in rows), "CLAUSE_IDS", "clauses must be an ordered list")
    ids = [row.get("id") for row in rows]
    source_ids = [row.id for row in source_clauses]
    require(len(source_ids) == 204 and len(set(source_ids)) == 204,
            "SOURCE_LAYOUT", "P0 baseline must have exactly 204 unique clauses")
    require(ids == source_ids, "CLAUSE_IDS", "missing, duplicate, unknown, or reordered clause")
    replacements = []
    for row, original in zip(rows, source_clauses):
        key = original.id
        require(set(row) == {"id", "scope", "before", "after", "reason", "changed"}, "CLAUSE_FIELDS", key)
        require(row["before"] == original.before, "CLAUSE_BEFORE", f"{key}: before differs from independently read SSOT")
        require(row["scope"] in ("K", "M", "W", "H"), "SCOPE", f"{key}: invalid scope")
        require(type(row["reason"]) is str and bool(row["reason"].strip()) and "\n" not in row["reason"] and "\r" not in row["reason"],
                "REASON", f"{key}: a nonempty single-paragraph reason is required")
        after = row["after"]
        require(type(after) is str and bool(after.strip()) and "\r" not in after,
                "CLAUSE_AFTER", f"{key}: after must contain LF-normalized full text")
        require([clause_id(line) for line in after.splitlines() if clause_id(line)] == [key]
                and clause_id(after.split("\n", 1)[0]) == key
                and re.fullmatch(r"\*\*D[0-9]+[a-z]? [^\n]*\*\*", after.strip()) is None
                and not any(line.strip() in OMISSIONS for line in after.splitlines()),
                "CLAUSE_AFTER", f"{key}: after must retain its sole header and cannot use omission placeholders")
        require(type(row["changed"]) is bool and row["changed"] == (row["before"] != after),
                "CHANGED", f"{key}: changed flag differs from literal before/after equality")
        if row["scope"] == "M":
            markers = [marker for marker in LEGACY_MARKERS if marker in after]
            require(len(markers) == 1 and after.count(markers[0]) == 1,
                    "MIXED_LEGACY", f"{key}: exactly one W/H legacy boundary is required")
            require(after.split(markers[0], 1)[1] == source_legacy_body(original),
                    "MIXED_LEGACY", f"{key}: W/H legacy body differs from the independent SSOT")
        replacements.append((original.start, original.end, after))
    sections = proposal["sections"]
    require(type(sections) is list and all(type(row) is dict for row in sections)
            and [row.get("id") for row in sections] == ["preamble", "exclusions"],
            "SECTION_IDS", "preamble and exclusions must each occur once in source order")
    for row in sections:
        key = row["id"]
        require(set(row) == {"id", "before", "after", "reason", "changed"}, "SECTION_FIELDS", key)
        start, end = source_sections[key]
        require(row["before"] == source[start:end], "SECTION_BEFORE", f"{key}: non-clause text differs from SSOT")
        require(type(row["reason"]) is str and bool(row["reason"].strip()) and "\n" not in row["reason"] and "\r" not in row["reason"],
                "REASON", f"{key}: a nonempty single-paragraph reason is required")
        after = row["after"]
        require(type(after) is str and bool(after.strip()) and "\r" not in after,
                "SECTION_AFTER", f"{key}: full non-clause text is required")
        require(not any(clause_id(line) for line in after.splitlines()),
                "SECTION_AFTER", f"{key}: section cannot smuggle in a clause")
        require(type(row["changed"]) is bool and row["changed"] == (row["before"] != after),
                "CHANGED", f"{key}: changed flag differs from literal before/after equality")
        replacements.append((start, end, after))
    expected_scopes = [(scope, "、".join(row["id"] for row in rows if row["scope"] == scope)) for scope in "KMWH"]
    require(preamble_scope_lists(sections[0]["after"]) == expected_scopes,
            "PREAMBLE_SCOPES", "adoption preamble scope lists differ from map membership or source order")
    intro, blocks = markdown_blocks(markdown)
    require(re.findall(r"基準 commit：`([^`]+)`", intro) == [proposal["baseRevision"]]
            and re.findall(r"SSOT 的 LF 正規化 SHA-256：`([^`]+)`", intro) == [proposal["sourceSha256"]],
            "MARKDOWN_METADATA", "review base revision or source hash differs from JSON")
    summary = re.findall(r"完整涵蓋現行 (\d+) 條（D (\d+)、I (\d+)、R (\d+)），其中 (\d+) 條有逐字差異、(\d+) 條保留原文", intro)
    changed_count = sum(row["changed"] for row in rows)
    expected_summary = (len(rows), *(sum(row["id"].startswith(kind) for row in rows) for kind in "DIR"),
                        changed_count, len(rows) - changed_count)
    require(len(summary) == 1 and tuple(map(int, summary[0])) == expected_summary,
            "MARKDOWN_SUMMARY", "review counts differ from clause map")
    scopes = re.findall(r"作用域總數：K (\d+), M (\d+), W (\d+), H (\d+)", intro)
    require(len(scopes) == 1 and tuple(map(int, scopes[0])) == tuple(sum(row["scope"] == scope for row in rows) for scope in "KMWH"),
            "MARKDOWN_SUMMARY", "review scope counts differ from clause map")
    table_start = intro.splitlines().count("| 條號 | 作用域 | 狀態 |")
    require(table_start == 1, "MARKDOWN_TABLE", "exactly one scope table is required")
    table_lines = intro.split("| 條號 | 作用域 | 狀態 |\n", 1)[1].splitlines()
    require(table_lines and re.fullmatch(r"\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|", table_lines[0]),
            "MARKDOWN_TABLE", "scope table separator is missing")
    table = []
    for line in table_lines[1:]:
        if not line.startswith("|"):
            break
        table.append([cell.strip() for cell in line.split("|")[1:-1]])
    expected_table = [[row["id"], row["scope"], "修改" if row["changed"] else "不變"] for row in rows]
    require(table == expected_table, "MARKDOWN_TABLE", "scope table differs from clause map or original order")
    changed = {row["id"]: row for row in rows + sections if row["changed"]}
    block_ids = [key for key, _, _, _ in blocks]
    require(len(block_ids) == len(set(block_ids)) and set(block_ids) == set(changed),
            "MARKDOWN_IDS", "changed block missing, duplicated, or unknown")
    require([key for key in block_ids if key in ids] == [row["id"] for row in rows if row["changed"]]
            and [key for key in block_ids if key in source_sections] == [row["id"] for row in sections if row["changed"]],
            "MARKDOWN_IDS", "changed clauses or sections are not in source order")
    for key, block, _, _ in blocks:
        before, after, reason = block_payload(block, key)
        require(before == changed[key]["before"], "MARKDOWN_BEFORE", f"{key}: review before differs from JSON")
        require(after == changed[key]["after"], "MARKDOWN_AFTER", f"{key}: review after differs from JSON")
        require(reason == changed[key]["reason"], "MARKDOWN_REASON", f"{key}: review reason differs from JSON")
    result, cursor = [], 0
    for start, end, after in sorted(replacements):
        require(start >= cursor, "PROPOSED_LAYOUT", "overlapping proposal spans")
        result.extend((source[cursor:start], after))
        cursor = end
    result.append(source[cursor:])
    result = "".join(result)
    require([clause_id(line) for line in result.splitlines() if clause_id(line)] == source_ids,
            "PROPOSED_LAYOUT", "proposed text must retain every clause exactly once")
    for title, offset in headings:
        if source_clauses[0].start < offset < source_sections["exclusions"][0]:
            require(result.splitlines().count(title) == 1, "PROPOSED_LAYOUT", f"unchanged section heading lost: {title}")
    return result


class ProposalContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "公理層.md").read_bytes()
        cls.proposal = json.loads((PROPOSAL_DIR / "clause-map.json").read_bytes())
        cls.markdown = normalized((PROPOSAL_DIR / "AXIOM-PROPOSAL.md").read_bytes())

    def setUp(self):
        self.data = deepcopy(self.proposal)

    def reject(self, code, data=None, markdown=None, source=None):
        with self.assertRaises(ProposalContractError, msg=f"missing {code} rejection") as caught:
            validate_proposal(self.source if source is None else source,
                              self.data if data is None else data,
                              self.markdown if markdown is None else markdown)
        self.assertEqual(code, caught.exception.code, str(caught.exception))

    def first_changed(self):
        return next(row for row in self.data["clauses"] if row["changed"])

    def replace_review_value(self, field, value, record_id=None):
        row = next(row for row in self.data["clauses"] + self.data["sections"] if row["id"] == record_id) if record_id else self.first_changed()
        _, blocks = markdown_blocks(self.markdown)
        key, block, start, end = next(item for item in blocks if item[0] == row["id"])
        before, after, reason = block_payload(block, key)
        old = {"before": before, "after": after, "reason": reason}[field]
        label = {"before": "修改前", "after": "修改後", "reason": "理由"}[field]
        field_start = block.index("#### " + label)
        value_start = block.index(old, field_start)
        altered = block[:value_start] + value + block[value_start + len(old):]
        heading_end = self.markdown.index("\n", start) + 1
        return self.markdown[:heading_end] + altered + self.markdown[end:]

    def test_proposal_matches_independently_read_ssot(self):
        untouched = deepcopy(self.data)
        proposed = validate_proposal(self.source, self.data, self.markdown)
        self.assertEqual(untouched, self.data, "validation must not rewrite evidence")
        self.assertNotEqual(normalized(self.source), proposed, "P0 must contain a concrete proposed change")

    def test_original_clause_order_and_nonclause_layout(self):
        clauses, sections, headings = source_layout(normalized(self.source))
        self.assertEqual({kind: sum(row.id.startswith(kind) for row in clauses) for kind in "DIR"},
                         {"D": 69, "I": 76, "R": 59})
        ids = [row.id for row in clauses]
        self.assertLess(ids.index("D12"), ids.index("D6"), "source order is not numeric order")
        self.assertEqual(["preamble", "exclusions"], list(sections))
        self.assertEqual(4, len(headings))

    def test_checkout_crlf_is_not_a_semantic_change(self):
        lf = self.source.replace(b"\r\n", b"\n")
        self.assertEqual(validate_proposal(lf, self.data, self.markdown),
                         validate_proposal(lf.replace(b"\n", b"\r\n"), self.data, self.markdown))

    def test_mixed_clauses_preserve_complete_legacy_body(self):
        originals = {row.id: row for row in source_layout(normalized(self.source))[0]}
        mixed = [row for row in self.data["clauses"] if row["scope"] == "M"]
        self.assertTrue(mixed, "proposal must actually expose its mixed contracts")
        for row in mixed:
            with self.subTest(clause=row["id"]):
                marker = next(marker for marker in LEGACY_MARKERS if marker in row["after"])
                self.assertEqual(source_legacy_body(originals[row["id"]]), row["after"].split(marker, 1)[1])

    def test_rejects_joint_map_and_review_legacy_deletion(self):
        row = next(row for row in self.data["clauses"] if row["id"] == "D7")
        self.assertEqual("M", row["scope"])
        removed_line = next(line for line in row["after"].splitlines(keepends=True) if line.startswith("**長度不宣告**"))
        row["after"] = row["after"].replace(removed_line, "", 1)
        markdown = self.replace_review_value("after", row["after"], record_id="D7")
        # Both artifacts agree and changed/scope/count/hash metadata remain valid.
        # Only comparison with the independently read SSOT catches this weakening.
        self.reject("MIXED_LEGACY", markdown=markdown)

    def test_adoption_preamble_scopes_match_map_membership_and_order(self):
        scopes = preamble_scope_lists(self.data["sections"][0]["after"])
        self.assertEqual(list("KMWH"), [scope for scope, _ in scopes])
        for scope, ids in scopes:
            with self.subTest(scope=scope):
                self.assertEqual([row["id"] for row in self.data["clauses"] if row["scope"] == scope], ids.split("、"))

    def test_rejects_joint_map_and_review_preamble_scope_drift(self):
        row = self.data["sections"][0]
        original = row["after"]
        scope, original_ids = preamble_scope_lists(original)[0]
        ids = original_ids.split("、")
        for changed_ids in (["D999", *ids[1:]], [ids[1], ids[0], *ids[2:]], [ids[1], *ids[1:]]):
            with self.subTest(scope=scope, first_ids=changed_ids[:2]):
                row["after"] = original.replace(original_ids, "、".join(changed_ids), 1)
                markdown = self.replace_review_value("after", row["after"], record_id="preamble")
                self.reject("PREAMBLE_SCOPES", markdown=markdown)

    def test_rejects_clause_before_drift(self):
        self.first_changed()["before"] += "\n未經授權的修改"
        self.reject("CLAUSE_BEFORE")

    def test_rejects_missing_duplicate_unknown_or_reordered_clauses(self):
        for mode in ("missing", "duplicate", "unknown", "reordered"):
            with self.subTest(mode=mode):
                data = deepcopy(self.proposal)
                rows = data["clauses"]
                if mode == "missing":
                    rows.pop()
                elif mode == "duplicate":
                    rows[-1] = deepcopy(rows[0])
                elif mode == "unknown":
                    rows[0]["id"] = "D999"
                else:
                    rows[0], rows[1] = rows[1], rows[0]
                self.reject("CLAUSE_IDS", data=data)

    def test_rejects_invalid_scope(self):
        self.data["clauses"][0]["scope"] = "UNKNOWN"
        self.reject("SCOPE")

    def test_rejects_empty_reason(self):
        self.data["clauses"][0]["reason"] = "  "
        self.reject("REASON")

    def test_rejects_empty_omitted_wrong_or_extra_after_clause(self):
        row = self.data["clauses"][0]
        for after in ("", "**D1 只有標題**", row["after"].split("\n")[0] + "\n同上", "**D999 錯誤條號**：錯誤。",
                      row["after"] + "\nI999 另一條：錯誤。"):
            with self.subTest(after=after[:30]):
                data = deepcopy(self.proposal)
                data["clauses"][0]["after"] = after
                self.reject("CLAUSE_AFTER", data=data)

    def test_rejects_inaccurate_or_nonboolean_changed(self):
        for flag in (not self.data["clauses"][0]["changed"], 1):
            with self.subTest(flag=flag):
                self.data["clauses"][0]["changed"] = flag
                self.reject("CHANGED")

    def test_rejects_source_hash_drift(self):
        self.data["sourceSha256"] = "0" * 64
        self.reject("SOURCE_HASH")

    def test_rejects_changed_ssot_even_if_manifest_stays_self_consistent(self):
        self.reject("SOURCE_HASH", source=self.source + b"\n")

    def test_rejects_joint_ssot_map_and_review_baseline_rewrite(self):
        source = self.source + b"\n"
        new_hash = hashlib.sha256(source.replace(b"\r\n", b"\n")).hexdigest()
        self.data["sourceSha256"] = new_hash
        exclusions = self.data["sections"][1]
        exclusions["before"] += "\n"
        markdown = self.replace_review_value("before", exclusions["before"], record_id="exclusions")
        markdown = markdown.replace(self.proposal["sourceSha256"], new_hash, 1)
        # Every mutable artifact agrees; the pinned baseline prevents rewriting
        # historical before evidence while still claiming the same base commit.
        self.reject("SOURCE_HASH", source=source, markdown=markdown)

    def test_rejects_wrong_schema_status_or_base(self):
        for field, value, code in (("schema", "other/1", "SCHEMA"), ("status", "approved", "STATUS"),
                                   ("baseRevision", "0" * 40, "BASE_REVISION")):
            with self.subTest(field=field):
                data = deepcopy(self.proposal)
                data[field] = value
                self.reject(code, data=data)

    def test_rejects_missing_or_reordered_nonclause_sections(self):
        for sections in (self.data["sections"][:1], list(reversed(self.data["sections"]))):
            with self.subTest(ids=[row["id"] for row in sections]):
                self.data["sections"] = sections
                self.reject("SECTION_IDS")

    def test_rejects_nonclause_before_drift(self):
        for index in (0, 1):
            with self.subTest(section=index):
                data = deepcopy(self.proposal)
                data["sections"][index]["before"] += "\n不同內容"
                self.reject("SECTION_BEFORE", data=data)

    def test_rejects_empty_or_clause_smuggling_section_after(self):
        for after in ("", "I999 偽裝條文：不允許。"):
            with self.subTest(after=after):
                data = deepcopy(self.proposal)
                data["sections"][0]["after"] = after
                self.reject("SECTION_AFTER", data=data)

    def test_rejects_review_before_drift(self):
        self.reject("MARKDOWN_BEFORE", markdown=self.replace_review_value("before", self.first_changed()["before"] + " "))

    def test_rejects_review_after_drift(self):
        self.reject("MARKDOWN_AFTER", markdown=self.replace_review_value("after", self.first_changed()["after"] + " "))

    def test_rejects_review_reason_drift(self):
        self.reject("MARKDOWN_REASON", markdown=self.replace_review_value("reason", "此理由沒有登記在 JSON。"))

    def test_rejects_scope_table_drift(self):
        row = self.data["clauses"][0]
        old = f"| {row['id']} | {row['scope']} |"
        self.assertIn(old, self.markdown)
        self.reject("MARKDOWN_TABLE", markdown=self.markdown.replace(old, f"| {row['id']} | UNKNOWN |", 1))

    def test_rejects_review_metadata_drift(self):
        for field in ("baseRevision", "sourceSha256"):
            with self.subTest(field=field):
                value = self.data[field]
                self.reject("MARKDOWN_METADATA", markdown=self.markdown.replace(value, "0" * len(value), 1))

    def test_rejects_review_summary_count_drift(self):
        for old, new in (("204 條（D", "203 條（D"), ("作用域總數：K ", "作用域總數：K 9")):
            with self.subTest(summary=old):
                self.assertIn(old, self.markdown)
                self.reject("MARKDOWN_SUMMARY", markdown=self.markdown.replace(old, new, 1))

    def test_rejects_missing_duplicate_or_unknown_review_block(self):
        _, blocks = markdown_blocks(self.markdown)
        key, _, start, end = blocks[0]
        for markdown in (self.markdown[:start] + self.markdown[end:],
                         self.markdown + "\n" + self.markdown[start:end],
                         self.markdown[:start] + self.markdown[start:].replace("### " + key, "### unknown", 1)):
            with self.subTest(size=len(markdown)):
                self.reject("MARKDOWN_IDS", markdown=markdown)

    def test_review_preserves_section_trailing_newlines(self):
        _, blocks = markdown_blocks(self.markdown)
        for row in self.data["sections"]:
            if row["changed"]:
                with self.subTest(section=row["id"]):
                    block = next(block for key, block, _, _ in blocks if key == row["id"])
                    before, after, _ = block_payload(block, row["id"])
                    self.assertEqual(row["before"], before)
                    self.assertEqual(row["after"], after)
                    self.assertTrue(before.endswith("\n"), "source section trailing LF is evidence")

    def test_rejects_review_section_trailing_newline_loss(self):
        _, blocks = markdown_blocks(self.markdown)
        row = next(row for row in self.data["sections"] if row["changed"] and row["before"].endswith("\n"))
        _, block, start, end = next(item for item in blocks if item[0] == row["id"])
        target = row["before"] + "\n```"
        self.assertIn(target, block)
        altered = block.replace(target, row["before"].rstrip("\n") + "\n```", 1)
        heading_end = self.markdown.index("\n", start) + 1
        self.reject("MARKDOWN_BEFORE", markdown=self.markdown[:heading_end] + altered + self.markdown[end:])


if __name__ == "__main__":
    unittest.main(verbosity=2)
