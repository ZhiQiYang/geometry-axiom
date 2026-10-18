"""GEO-261 adopted-source gate: approved delta plus independently adopted main.

Historical proposal bytes stay immutable. No before text is rebuilt from the
proposal itself, and an upstream merge cannot silently discard either contract.
Later SSOT adoptions are listed in POST_APPROVAL_REVISIONS and applied on top
of the frozen approved result as exact, clause-scoped replacements, each with
its own human approval record; the current SSOT must equal that, byte for byte.
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
# Later adoptions, approved after GEO-261, applied in order to the frozen
# approved result above (ADOPTED_HASH stays its fingerprint).  Each edit is
# (clause, exact before, exact after): the before text must occur exactly once
# in the whole document and inside that clause; no edit may add, drop, reorder
# or rename clauses, or touch the preamble, chapter headings or exclusions.
# "proposal" and "approval" record the reviewed bytes (not in this tree) and the
# human answer.  "decision" must point at that answer in 決策佇列.md: a heading
# that occurs exactly once and each answer quoted verbatim as its own "> ..."
# line inside that section (REVISION_APPROVAL).  A revision whose answer is not
# recorded there keeps the actual-SSOT test red: it is not adopted yet.
POST_APPROVAL_REVISIONS = (
    {
        "id": "pr260-ab",
        "proposal": "PR #260 head ba7b60236d29061711edd5fb873acedebb2a4a87, geometry-core/axiom-clarify-20261016/PROPOSAL.md, LF SHA-256 833710a170a98583d112b1590de4117ac49b4654ea54679ca8749ebe8aa0da8c: A1-A4 (one staggered axis per grid system), B1-B2 (I5, R18 wording)",
        "approval": "決策佇列.md「2026-10-18 #260 條文稿第一批回覆 🔒」: 第 1 題 A 區「同意」；"
                    "第 2 題依 10-16 所選說明寫成定義推論；第 3 題「改回選項一(建議)」；"
                    "第 4 題 B 區「同意(建議)」",
        "decision": {"heading": "### 2026-10-18 #260 條文稿第一批回覆 🔒",
                     "answers": ("> 同意", "> 改回選項一(建議)", "> 同意(建議)")},
        "edits": (
            ("D29",
                "未設相位差時，格線身分為（系統、軸、signed k）。設了 D10b 相位差時，段的身分是（系統、軸、signed k、另一軸 cell 索引）。"
                "未設相位差時，cell(i,j) 由 u_i/u_(i+1)、v_j/v_(j+1) 圍成；"
                "有相位差時，圍成格子的線座標依 D10b，格子仍由未錯開的相鄰線切開。",
                "未設相位差時，格線身分為（系統、軸、signed k）。設了 D10b 相位差時，段的身分是（系統、軸、signed k、另一軸 cell 索引）。"
                "未設相位差時，cell(i,j) 由 u_i/u_(i+1)、v_j/v_(j+1) 圍成；"
                "有相位差時（同一系統至多一軸，D10b），圍成格子的線座標依 D10b，格子仍由未錯開的相鄰線切開。"),
            ("D10b",
                "相鄰單位是另一軸既有的帶符號 cell 索引，DSL 稱 band。不另建「排」或第二條軸。"
                "另一軸必須存在，且同為無限排法。兩軸可各自有相位差。",
                "相鄰單位是另一軸既有的帶符號 cell 索引，DSL 稱 band。不另建「排」或第二條軸。"
                "另一軸必須存在，且同為無限排法。同一份網格系統至多一軸有相位差（2026-10-16 使用者拍板）。"
                "兩軸同時錯開時，有些 cell 的四邊不是畫出的格線段，圍不成封閉的區域；板子以同一方向平行鋪滿一個面時，板縫也只能在一個方向錯開。"),
            ("D10b",
                "band 的切開用另一軸未加相位差的格線。u 線（常數 u、沿 v 延伸）在 band j 的沿線範圍是未錯開的 v(j)…v(j+1)；"
                "v 線同理。因此 cell(i,j) 仍是軸對齊矩形：它在某一軸上的兩條邊界，共用該軸對另一軸索引的同一個 δ。"
                "矩形邊長仍是兩軸間距。",
                "band 的切開用另一軸未加相位差的格線。u 線（常數 u、沿 v 延伸）在 band j 的沿線範圍是未錯開的 v(j)…v(j+1)；"
                "v 線同理。因此 cell(i,j) 仍是軸對齊矩形：它在某一軸上的兩條邊界，共用該軸對另一軸索引的同一個 δ。"
                "矩形邊長仍是兩軸間距。\n"
                "\n"
                "相容例外：相位差軸數的比較只在提交（R56）時做。整體取代（D61：開新、恢復內建場景、載入場景檔、確認場景匯入、恢復資料、載入方案快照）、隔離重放（R46 重開、I31 交換包重建）及復原／重做（D60）不是提交，不做此比較，其中兩軸都已有相位差的系統照舊成立，求值、dump 與存回行為不變。"
                "兩軸系統上，提交後仍為兩軸而相位差值不變的編輯（例如改名稱、改間距）照常，移除一軸的編輯照常；"
                "提交後仍為兩軸而任一軸的相位差值有變者拒絕，要改須在同一筆編輯裡先移除一軸，再改剩下那軸的值。"
                "此時有些 cell 的四邊不全是畫出的格線段，相鄰 cell 可重疊或留空；不得把 cell 一律當成格線圍出的區域。"),
            ("I24",
                "相位差守門：相位差只接受 D29 無限軸上的一個整數毫米。省略為貫通線。另一軸不存在、不是無限排法，或本軸不是 REPEAT／REPEAT_PANEL，一律拒絕。",
                "相位差守門：相位差只接受 D29 無限軸上的一個整數毫米。省略為貫通線。另一軸不存在、不是無限排法，或本軸不是 REPEAT／REPEAT_PANEL，一律拒絕。"
                "每一筆提交（R56）比較提交前後同一網格系統的相位差：由不足兩軸變為兩軸（含新建時兩軸都填、一軸已有再加另一軸）→ 拒絕，訊息說明同一份網格只能有一軸錯開；"
                "提交後仍為兩軸而任一軸的相位差值有變 → 拒絕，訊息說明要先在同一筆編輯裡移除一軸；"
                "要改成錯開另一個方向，請在同一筆編輯裡移除這一軸的相位差、再設另一軸。提交後仍為兩軸而相位差值不變（改名稱、改間距等）、以及移除一軸，照常。"
                "整體取代、隔離重放及復原／重做不是提交，不做此比較。相位差值以該系統自己的相位差欄位求出的值為準；"
                "相位差若引用參數欄位，改那張參數卡的值不算改相位差值。"),
            ("R22",
                "相位差求值：未錯開座標 c(k) 沿用 D29。已設相位差時，band 最低位元為 1 的段座標為 c(k)+δ，最低位元為 0 的段座標為 c(k)。"
                "另一軸的 band 邊界用該軸未加相位差的格線，即使該軸自己也有相位差。",
                "相位差求值：未錯開座標 c(k) 沿用 D29。已設相位差時，band 最低位元為 1 的段座標為 c(k)+δ，最低位元為 0 的段座標為 c(k)。"
                "另一軸的 band 邊界用該軸未加相位差的格線，即使該軸自己也有相位差（只會出現在 D10b 相容例外的舊系統）。"),
            ("I5",
                "（多邊形下不再是「兩角點」捷徑——矩形四邊不得與輪廓/孔邊相交。）",
                "（多邊形下不再是「兩角點」捷徑——角材整支要在界內：有效範圍是外環內部與邊界、扣掉孔內部（D3），所以任何部分都不得在外輪廓之外（含輪廓上的凹口），也不得進入孔。"
                "RC 牆面在輪廓之外，不能穿過；柱子要先投影進這個面（apply-proj，R8），之後它的範圍不在有效範圍內，才同樣不能穿過。"
                "貼著邊、切齊仍在界內。貼上去合不合法（端面能不能頂、哪種角色可以頂）另依 I6、I19、I20。"
                "與已放角材之間同樣不能互相穿過，見 I11。）"),
            ("R18",
                "`primary` 的 onBoundary 可真可假\n"
                "    （邊界主支為真）但 coversEdge 恆為假（兩端被層級 1 佔掉料寬，I11 不重疊）；",
                "`primary` 的 onBoundary 可真可假（邊界主支為真）但 coversEdge 恆為假：凸角處兩端被層級 1 佔掉料寬（I11 不重疊）；"
                "凹角處 primary 不得超出它貼的外牆（I22），延伸段側面以優先級 2 計、primary 端面不得頂它（I22、I19）；"),
        ),
    },
)
CURRENT_HASH = "f10ef7ca8a4c1e5154fc705116f30be31e7d9374dd963b9f99d9c2268d34981c"


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


def apply_post_approval_revisions(adopted, revisions):
    """The frozen approved result plus the listed later revisions, and nothing else."""
    clauses, sections, headings = source_layout(adopted)
    result, seen = adopted, set()
    for revision in revisions:
        require(revision["id"] not in seen and bool(revision["approval"]) and bool(revision["edits"]),
                "REVISION_RECORD", f"{revision['id']}: needs a unique id, its approval record and its edits")
        seen.add(revision["id"])
        for clause, before, after in revision["edits"]:
            rows = {row.id: row for row in source_layout(result)[0]}
            require(clause in rows, "REVISION_CLAUSE", f"{revision['id']}: no clause {clause}")
            row = rows[clause]
            require(bool(before) and before != after and result.count(before) == 1
                    and row.before.count(before) == 1, "REVISION_ANCHOR",
                    f"{revision['id']} {clause}: before text must occur exactly once, inside {clause}")
            at = row.start + row.before.index(before)
            result = result[:at] + after + result[at + len(before):]
    new_clauses, new_sections, new_headings = source_layout(result)
    require([row.id for row in new_clauses] == [row.id for row in clauses]
            and [title for title, _ in new_headings] == [title for title, _ in headings]
            and result[slice(*new_sections["preamble"])] == adopted[slice(*sections["preamble"])]
            and result[slice(*new_sections["exclusions"])] == adopted[slice(*sections["exclusions"])],
            "REVISION_LAYOUT", "a later revision may only rewrite text inside existing clauses")
    return result


def verify_revision_decisions(queue_bytes, revisions):
    """Each later revision must point at the user's own recorded answers in 決策佇列.md."""
    lines = normalized(queue_bytes).split("\n")
    for revision in revisions:
        decision = revision.get("decision")
        heading = decision.get("heading", "") if isinstance(decision, dict) else ""
        answers = decision.get("answers", ()) if isinstance(decision, dict) else ()
        starts = [index for index, line in enumerate(lines) if line == heading]
        section = set()
        if heading.startswith("### ") and len(starts) == 1:
            end = next((index for index in range(starts[0] + 1, len(lines))
                        if lines[index].startswith(("### ", "## "))), len(lines))
            section = {line.strip() for line in lines[starts[0] + 1:end]}
        require(bool(section) and bool(answers)
                and all(answer.startswith("> ") and answer in section for answer in answers),
                "REVISION_APPROVAL",
                f"{revision['id']}: 決策佇列.md must hold exactly one section {heading!r} "
                f"quoting each of the user's answers {answers!r}")


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
        cls.current = apply_post_approval_revisions(cls.expected, POST_APPROVAL_REVISIONS)

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
        verify_revision_decisions((ROOT / "決策佇列.md").read_bytes(), POST_APPROVAL_REVISIONS)
        actual = (ROOT / "公理層.md").read_bytes()
        validate_current_document(actual, self.current)
        self.assertEqual(CURRENT_HASH, sha(actual))
        self.assertEqual(ADOPTED_HASH, hashlib.sha256(self.expected.encode("utf-8")).hexdigest())

    def test_current_source_tamper_deletion_and_layout_drift_are_rejected(self):
        original = self.current.encode("utf-8")
        validate_current_document(original, self.current)
        # dropping any later revision, or the GEO-261 result alone, is not the current document
        dropped = [apply_post_approval_revisions(self.expected, POST_APPROVAL_REVISIONS[:count]).encode("utf-8")
                   for count in range(len(POST_APPROVAL_REVISIONS))]
        last = POST_APPROVAL_REVISIONS[-1]
        earlier = POST_APPROVAL_REVISIONS[:-1]
        clause, before, after = last["edits"][0]
        retouched = apply_post_approval_revisions(
            self.expected, earlier + (last | {"edits": ((clause, before, after + "x"),) + last["edits"][1:]},))
        for altered in (original + b"\n", original.replace(b"100,000,000", b"100,000,001", 1),
                        original.replace("## 三、推演規則".encode(), "## 篡改章節".encode(), 1),
                        *dropped, retouched.encode("utf-8")):
            self.reject("ADOPTED_SOURCE", validate_current_document, altered, self.current)
        # a later revision is only the exact, clause-scoped replacement it records
        other = next(row.id for row in source_layout(self.expected)[0] if before not in row.before)
        for code, fields in (
                ("REVISION_RECORD", {"approval": ""}),
                ("REVISION_RECORD", {"edits": ()}),
                ("REVISION_CLAUSE", {"edits": (("X99", before, after),)}),
                ("REVISION_ANCHOR", {"edits": ((clause, before + "\u3000", after),)}),
                ("REVISION_ANCHOR", {"edits": ((other, before, after),)}),
                ("REVISION_ANCHOR", {"edits": ((clause, "", after),)}),
                ("REVISION_ANCHOR", {"edits": ((clause, "（分層契約）：", after),)}),
                ("REVISION_LAYOUT", {"edits": ((clause, before, after + "\nR99 偷渡條文（分層契約）："),)}),
                ("REVISION_LAYOUT", {"edits": ((clause, before, after + "\n## 偷渡章節"),)})):
            with self.subTest(code=code, fields=sorted(fields)):
                self.reject(code, apply_post_approval_revisions, self.expected, earlier + (last | fields,))
        self.reject("REVISION_RECORD", apply_post_approval_revisions, self.expected,
                    POST_APPROVAL_REVISIONS + (last,))
        first = source_layout(self.expected)[0][0]
        header = first.before.split("\n", 1)[0]
        for code, edits in (("REVISION_ANCHOR", ((clause, before, before),)),
                            ("REVISION_LAYOUT", ((first.id, header, "偷渡前言\n\n" + header),))):
            with self.subTest(code=code, edit=edits[0][0]):
                self.reject(code, apply_post_approval_revisions, self.expected,
                            earlier + (last | {"edits": edits},))
        # the approval must be the user's answer recorded in the decision queue
        queue = (ROOT / "決策佇列.md").read_bytes()
        approved = POST_APPROVAL_REVISIONS[0]
        verify_revision_decisions(queue, (approved,))
        decision = approved["decision"]
        elsewhere = "> 只准一軸(建議)"
        self.assertIn(elsewhere, normalized(queue))
        for case, revision, record in (
                ("no decision", {k: v for k, v in approved.items() if k != "decision"}, queue),
                ("unknown heading", approved | {"decision": decision | {"heading": decision["heading"] + "x"}}, queue),
                ("not a section heading", approved | {"decision": decision | {"heading": decision["heading"][4:]}}, queue),
                ("no answers", approved | {"decision": decision | {"answers": ()}}, queue),
                ("answer not given", approved | {"decision": decision | {"answers": decision["answers"] + ("> 不同意",)}}, queue),
                ("answer from another section", approved | {"decision": decision | {"answers": (elsewhere,)}}, queue),
                ("answer not quoted", approved | {"decision": decision | {"answers": (decision["answers"][0][2:],)}}, queue),
                ("section duplicated", approved,
                 queue + ("\n" + decision["heading"] + "\n\n" + decision["answers"][0] + "\n").encode("utf-8")),
                ("answer removed from the record", approved,
                 normalized(queue).replace("  " + decision["answers"][1] + "\n", "\n", 1).encode("utf-8"))):
            with self.subTest(case=case):
                self.reject("REVISION_APPROVAL", verify_revision_decisions, record, (revision,))

    def test_crlf_is_the_only_ignored_source_difference(self):
        validate_current_document(self.current.replace("\n", "\r\n").encode(), self.current)
        self.reject("ADOPTED_SOURCE", validate_current_document, self.current.replace("\n", "\r\r\n").encode(), self.current)


if __name__ == "__main__":
    unittest.main(verbosity=2)
