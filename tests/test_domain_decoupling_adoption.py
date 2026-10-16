"""GEO-261 adopted-source gate: approved delta plus independently adopted main.

Historical proposal bytes stay immutable. No before text is rebuilt from the
proposal itself, and an upstream merge cannot silently discard either contract.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest

from test_domain_decoupling_proposal import (
    ROOT, PROPOSAL_DIR, BASE_SOURCE_SHA256, LEGACY_MARKERS,
    ProposalContractError, normalized, require, source_layout,
    source_legacy_body, preamble_scope_lists, validate_proposal,
)

PROPOSAL_COMMIT = "17a25e92c75e8c89063e36ca329729980d8ea6a9"
PROPOSAL_HASH = "905e49111b5bb8c4fadecb46c89c0d9ff59deb7d3064b602ae23bfc72ca6b609"
MAP_HASH = "51841370641ea38d45d4d46a1767f8c4fd4b4fb4c47c0deb4ce82d0476fa5ca4"
UPSTREAM_REVISION = "a898ad6e12707104568679591fe1b21804bfc3df"
UPSTREAM_HASH = "e5e43ec5da2030669c9ecd7a67f8b250cfb7290cf663365b2b66c51814bb77b9"
UPSTREAM_CHANGED = {"D9", "D25", "D29", "D31", "I8a", "I37", "I38", "I39", "R32", "R33"}
UPSTREAM_NEW = {"D64": "K", "I74": "K", "R60": "H"}
ADDENDUM_MARKDOWN_HASH = "d9e6717e9d7312b8eeb3783e7b6014c064abf7b221ada4d7a1820780563f2249"
ADDENDUM_MAP_HASH = "6f17044c3b554595268ba5fa63499b3e9c691a102a6bbe4dba8d758a415a8511"
ADDENDUM_COMMIT = "c8ce964be623084af957dc2ff662abfdaf670c87"
ADDENDUM_APPROVED_AT = "2026-10-16T15:23:52.328994Z"
ADOPTED_HASH = "18a9a75bcf4a5d5fed28c6c5f5cb9702d173198d7d0cd198ffad9936a4b94fa5"


def sha(raw):
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def verify_original_approval(approval, map_bytes, markdown_bytes):
    require(isinstance(approval, dict), "APPROVAL", "missing human approval receipt")
    require(approval.get("schema") == "geo261-approval/1"
            and approval.get("proposalCommit") == PROPOSAL_COMMIT
            and approval.get("axiomAnswer") == "批准此版本的逐條提案",
            "APPROVAL", "the exact proposal requires its human approval")
    require(approval.get("proposalMarkdownSha256LF") == PROPOSAL_HASH == sha(markdown_bytes),
            "APPROVED_MARKDOWN", "approved review payload changed")
    require(approval.get("clauseMapSha256LF") == MAP_HASH == sha(map_bytes),
            "APPROVED_MAP", "approved before/after map changed")


def merged_proposal(base_bytes, upstream_bytes, proposal, markdown):
    """Construct the approved delta on train 17, before the scope addendum.

Mixed clauses retain the approved K prefix, followed by the *complete* upstream
body. New upstream clauses are copied verbatim. All changes have pinned sources.
"""
    validate_proposal(base_bytes, proposal, markdown)
    require(sha(upstream_bytes) == UPSTREAM_HASH, "UPSTREAM_HASH", "train 17 source changed")
    base, upstream = normalized(base_bytes), normalized(upstream_bytes)
    old_clauses, old_sections, _ = source_layout(base)
    new_clauses, new_sections, _ = source_layout(upstream)
    originals = {row.id: row for row in old_clauses}
    current = {row.id: row for row in new_clauses}
    require(set(current) - set(originals) == set(UPSTREAM_NEW)
            and set(originals) <= set(current), "UPSTREAM_IDS", "unexpected upstream clause delta")
    require({key for key in originals if originals[key].before != current[key].before} == UPSTREAM_CHANGED,
            "UPSTREAM_DELTA", "unexpected upstream body changes")
    replacements = []
    for row in proposal["clauses"]:
        original, latest = originals[row["id"]], current[row["id"]]
        if not row["changed"]:
            continue
        after = row["after"]
        if row["scope"] == "M":
            marker = next(marker for marker in LEGACY_MARKERS if marker in after)
            after = after.split(marker, 1)[0] + marker + source_legacy_body(latest)
        else:
            require(latest.before == original.before, "DIRECT_CONFLICT", f"{row['id']}: direct rewrite overlaps main")
        replacements.append((latest.start, latest.end, after))

    approved_sections = {row["id"]: row for row in proposal["sections"]}
    a, b = new_sections["exclusions"]
    oa, ob = old_sections["exclusions"]
    require(upstream[a:b] == base[oa:ob], "EXCLUSIONS_CONFLICT", "upstream exclusions changed")
    replacements.append((a, b, approved_sections["exclusions"]["after"]))

    pa, pb = new_sections["preamble"]
    preamble = upstream[pa:pb]
    approved_preamble = approved_sections["preamble"]["after"]
    old_title = base.split("\n", 1)[0]
    new_title = approved_preamble.split("\n", 1)[0]
    require(preamble.startswith(old_title + "\n"), "PREAMBLE_TITLE", "upstream title changed")
    split = "### 分層契約（GEO-261）\n"
    require(approved_preamble.count(split) == 1 and split not in preamble,
            "PREAMBLE_MERGE", "layering must be inserted exactly once")
    chapter = "## 一、定義（公理）\n\n"
    require(preamble.endswith(chapter) and approved_preamble.endswith(chapter),
            "PREAMBLE_MERGE", "chapter boundary changed")
    combined_preamble = new_title + preamble[len(old_title):-len(chapter)]
    combined_preamble += split + approved_preamble.split(split, 1)[1]
    replacements.append((pa, pb, combined_preamble))
    result = upstream
    for start, end, after in sorted(replacements, reverse=True):
        result = result[:start] + after + result[end:]
    return result


def expected_addendum_before_and_after(merged, proposal):
    clauses, sections, _ = source_layout(merged)
    start, end = sections["preamble"]
    before = merged[start:end]
    scopes = {row["id"]: row["scope"] for row in proposal["clauses"]} | UPSTREAM_NEW
    after = before.replace("204 條的規範作用域如下", "207 條的規範作用域如下", 1)
    for scope, old_ids in preamble_scope_lists(before):
        new_ids = "、".join(row.id for row in clauses if scopes[row.id] == scope)
        after = after.replace(old_ids + "。", new_ids + "。", 1)
    require(after != before, "ADDENDUM_DELTA", "scope addition is missing")
    return before, after


def apply_scope_addendum(merged, proposal, before, after):
    expected_before, expected_after = expected_addendum_before_and_after(merged, proposal)
    require(before == expected_before, "ADDENDUM_BEFORE", "review before differs from independently merged source")
    require(after == expected_after, "ADDENDUM_AFTER", "only the reviewed three scope entries and count may change")
    _, sections, _ = source_layout(merged)
    start, end = sections["preamble"]
    return merged[:start] + after + merged[end:]


def verify_addendum_review(map_bytes, markdown_bytes, merged, proposal):
    require(sha(map_bytes) == ADDENDUM_MAP_HASH, "ADDENDUM_MAP", "reviewed scope addendum map changed")
    require(sha(markdown_bytes) == ADDENDUM_MARKDOWN_HASH, "ADDENDUM_MARKDOWN", "reviewed scope addendum text changed")
    data = json.loads(map_bytes)
    require(data["schema"] == "geo261-merge-addendum/1"
            and data["status"] == "proposed-not-approved"
            and data["approvedProposalRevision"] == PROPOSAL_COMMIT
            and data["upstreamRevision"] == UPSTREAM_REVISION
            and data["upstreamSourceSha256"] == UPSTREAM_HASH,
            "ADDENDUM_PROVENANCE", "scope addendum must retain its reviewed provenance")
    require(len(data["sections"]) == 1 and data["sections"][0]["id"] == "preamble",
            "ADDENDUM_PROVENANCE", "only the full preamble was proposed")
    section = data["sections"][0]
    payloads = re.findall(r"```text\n(.*?)\n```", normalized(markdown_bytes), re.DOTALL)
    require(payloads == [section["before"], section["after"]],
            "ADDENDUM_PAYLOAD", "human review and machine source disagree")
    return apply_scope_addendum(merged, proposal, section["before"], section["after"])


def verify_addendum_approval(approval):
    require(isinstance(approval, dict) and approval.get("scopeAddendumAnswer") == "批准此追加分層提案"
            and approval.get("scopeAddendumCommit") == ADDENDUM_COMMIT
            and approval.get("scopeAddendumApprovedAt") == ADDENDUM_APPROVED_AT
            and approval.get("scopeAddendumMarkdownSha256LF") == ADDENDUM_MARKDOWN_HASH
            and approval.get("scopeAddendumMapSha256LF") == ADDENDUM_MAP_HASH,
            "ADDENDUM_APPROVAL", "three new scope assignments require their exact human approval")


def validate_current_document(current_bytes, expected):
    require(normalized(current_bytes) == expected, "ADOPTED_SOURCE", "current SSOT differs from the approved, upstream-preserving result")
    clauses, _, _ = source_layout(expected)
    require(len(clauses) == len({row.id for row in clauses}) == 207,
            "ADOPTED_LAYOUT", "the adopted document must preserve all 207 clauses")


class AdoptionIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (ROOT / "tests/fixtures/geo261-axiom-base.txt").read_bytes()
        cls.upstream = (ROOT / "tests/fixtures/geo261-axiom-train17.txt").read_bytes()
        cls.map_bytes = (PROPOSAL_DIR / "clause-map.json").read_bytes()
        cls.markdown_bytes = (PROPOSAL_DIR / "AXIOM-PROPOSAL.md").read_bytes()
        cls.proposal = json.loads(cls.map_bytes)
        cls.markdown = normalized(cls.markdown_bytes)
        cls.approval = json.loads((PROPOSAL_DIR / "APPROVAL.json").read_bytes())
        cls.addendum_map_bytes = (PROPOSAL_DIR / "merge-addendum.json").read_bytes()
        cls.addendum_markdown_bytes = (PROPOSAL_DIR / "MERGE-ADDENDUM.md").read_bytes()
        cls.merged = merged_proposal(cls.base, cls.upstream, cls.proposal, cls.markdown)
        cls.before, cls.after = expected_addendum_before_and_after(cls.merged, cls.proposal)
        cls.expected = apply_scope_addendum(cls.merged, cls.proposal, cls.before, cls.after)

    def reject(self, code, function, *args):
        with self.assertRaises(ProposalContractError) as caught:
            function(*args)
        self.assertEqual(code, caught.exception.code, str(caught.exception))

    def test_original_approval_is_bound_to_exact_reviewed_bytes(self):
        verify_original_approval(self.approval, self.map_bytes, self.markdown_bytes)

    def test_missing_or_other_proposal_approval_is_rejected(self):
        for receipt in (None, {}, self.approval | {"proposalCommit": "0" * 40},
                        self.approval | {"axiomAnswer": ""}):
            self.reject("APPROVAL", verify_original_approval, receipt, self.map_bytes, self.markdown_bytes)

    def test_joint_review_and_map_change_cannot_reuse_approval(self):
        self.reject("APPROVED_MARKDOWN", verify_original_approval, self.approval, self.map_bytes, self.markdown_bytes + b"\n")
        self.reject("APPROVED_MAP", verify_original_approval, self.approval, self.map_bytes + b"\n", self.markdown_bytes)

    def test_joint_fixture_and_manifest_cannot_rewrite_old_ssot(self):
        changed = deepcopy(self.proposal)
        changed["sourceSha256"] = sha(self.base + b"\n")
        self.reject("SOURCE_HASH", merged_proposal, self.base + b"\n", self.upstream, changed, self.markdown)

    def test_upstream_source_is_independent_and_pinned(self):
        self.assertEqual(BASE_SOURCE_SHA256, sha(self.base))
        self.assertEqual(UPSTREAM_HASH, sha(self.upstream))
        self.reject("UPSTREAM_HASH", merged_proposal, self.base, self.upstream + b"\n", self.proposal, self.markdown)

    def test_all_upstream_new_clauses_remain_verbatim(self):
        upstream = {row.id: row.before for row in source_layout(normalized(self.upstream))[0]}
        adopted = {row.id: row.before for row in source_layout(self.expected)[0]}
        for key in UPSTREAM_NEW:
            with self.subTest(clause=key):
                self.assertEqual(upstream[key], adopted[key])

    def test_all_95_mixed_bodies_preserve_complete_upstream_contract(self):
        upstream = {row.id: row for row in source_layout(normalized(self.upstream))[0]}
        adopted = {row.id: row.before for row in source_layout(self.expected)[0]}
        mixed = [row for row in self.proposal["clauses"] if row["scope"] == "M"]
        self.assertEqual(95, len(mixed))
        for row in mixed:
            with self.subTest(clause=row["id"]):
                marker = next(marker for marker in LEGACY_MARKERS if marker in row["after"])
                prefix, body = adopted[row["id"]].split(marker)
                self.assertEqual(row["after"].split(marker)[0], prefix)
                self.assertEqual(source_legacy_body(upstream[row["id"]]), body)

    def test_scope_addendum_is_only_count_and_three_reviewed_entries(self):
        self.assertEqual(self.expected, apply_scope_addendum(self.merged, self.proposal, self.before, self.after))
        self.reject("ADDENDUM_BEFORE", apply_scope_addendum, self.merged, self.proposal, self.before + " ", self.after)
        self.reject("ADDENDUM_AFTER", apply_scope_addendum, self.merged, self.proposal, self.before, self.after + " ")

    def test_frozen_addendum_review_matches_independent_merge(self):
        self.assertEqual(self.expected, verify_addendum_review(self.addendum_map_bytes,
                         self.addendum_markdown_bytes, self.merged, self.proposal))
        self.assertEqual(ADOPTED_HASH, hashlib.sha256(self.expected.encode("utf-8")).hexdigest())

    def test_changed_addendum_cannot_reuse_review_receipt(self):
        self.reject("ADDENDUM_MAP", verify_addendum_review, self.addendum_map_bytes + b"\n",
                    self.addendum_markdown_bytes, self.merged, self.proposal)
        self.reject("ADDENDUM_MARKDOWN", verify_addendum_review, self.addendum_map_bytes,
                    self.addendum_markdown_bytes + b"\n", self.merged, self.proposal)

    def test_original_approval_alone_never_authorizes_added_scopes(self):
        original_only = {key: value for key, value in self.approval.items() if not key.startswith("scopeAddendum")}
        self.reject("ADDENDUM_APPROVAL", verify_addendum_approval, original_only)
        for field, wrong in (("scopeAddendumAnswer", "批准三條的作用域補充（建議）"),
                             ("scopeAddendumMarkdownSha256LF", "0" * 64),
                             ("scopeAddendumMapSha256LF", "0" * 64),
                             ("scopeAddendumCommit", "0" * 40),
                             ("scopeAddendumApprovedAt", "2026-10-15T00:00:00Z")):
            with self.subTest(field=field):
                self.reject("ADDENDUM_APPROVAL", verify_addendum_approval,
                            self.approval | {field: wrong})

    def test_actual_addendum_approval_matches_human_answer_and_frozen_review(self):
        verify_addendum_approval(self.approval)

    def test_actual_ssot_is_the_full_approved_upstream_preserving_adoption(self):
        actual = (ROOT / "公理層.md").read_bytes()
        validate_current_document(actual, self.expected)
        self.assertEqual(ADOPTED_HASH, sha(actual))

    def test_current_source_tamper_deletion_and_layout_drift_are_rejected(self):
        original = self.expected.encode("utf-8")
        validate_current_document(original, self.expected)
        for altered in (original + b"\n", original.replace(b"100,000,000", b"100,000,001", 1),
                        original.replace("## 三、推演規則".encode(), "## 篡改章節".encode(), 1)):
            self.reject("ADOPTED_SOURCE", validate_current_document, altered, self.expected)

    def test_crlf_is_the_only_ignored_source_difference(self):
        validate_current_document(self.expected.replace("\n", "\r\n").encode(), self.expected)
        self.reject("ADOPTED_SOURCE", validate_current_document, self.expected.replace("\n", "\r\r\n").encode(), self.expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
