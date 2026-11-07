"""GEO-261 adopted-source gate: approved delta plus independently adopted main.

Historical proposal bytes stay immutable. No before text is rebuilt from the
proposal itself, and an upstream merge cannot silently discard either contract.
Later clause-only adoptions are listed in POST_APPROVAL_REVISIONS and applied
on top of the frozen result, each with its own human approval record.  R14 is
a separate, exactly pinned extension of that result, including its approved
preamble and exclusions changes; current SSOT must equal the full reconstruction.
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
# human answer.  "decision" must point at that answer in 決策佇列.md
# (REVISION_APPROVAL): a section heading that occurs exactly once and backs no
# other revision; each answer names its bullet by the bullet's full head line,
# which occurs once among the section's top-level bullets, quotes the user's
# reply as a "> ..." line of that bullet's body, the reply being one of
# APPROVAL_REPLIES, and lists the clauses it authorizes, each named in that
# head line (never in the body, where question stems and narration live); a
# revision cites a bullet at most once and every edited clause must be
# authorized.  One revision per decision section.  This ties a revision to a
# recorded approval of those very clauses; it cannot stop a coordinated edit of
# this file, the SSOT and the queue, nor a changed edit inside an approved
# revision.  An unrecorded approval keeps the actual-SSOT test red.
# Only replies some existing binding uses are approvals; add one only together
# with the binding that needs it.
APPROVAL_REPLIES = ("> 同意", "> 同意(建議)", "> 同意 #318 照閱讀 A", "> 照這兩句寫入 (建議)")
POST_APPROVAL_REVISIONS = (
    {
        "id": "pr260-b",
        "proposal": "PR #260 head ba7b60236d29061711edd5fb873acedebb2a4a87, geometry-core/axiom-clarify-20261016/PROPOSAL.md, LF SHA-256 833710a170a98583d112b1590de4117ac49b4654ea54679ca8749ebe8aa0da8c: B1-B2 (I5, R18 wording)",
        "approval": "決策佇列.md「2026-10-18 #260 條文稿第一批回覆 🔒」第 4 題 B 區「同意(建議)」",
        "decision": {"heading": "### 2026-10-18 #260 條文稿第一批回覆 🔒",
                     # (bullet head line, the user's quoted reply in it, clauses it names and authorizes)
                     "answers": (
                         ("- **第 4 題 B 區措辭澄清(I5 界內/界外與貼上去是否合法分開寫;R18 補凹角處由哪些規則管)**:所選",
                          "> 同意(建議)", ("I5", "R18")),
                     )},
        "edits": (
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
    {
        "id": "pr260-final",
        "proposal": "PR #260 head ba7b60236d29061711edd5fb873acedebb2a4a87, geometry-core/axiom-clarify-20261016/PROPOSAL.md, LF SHA-256 833710a170a98583d112b1590de4117ac49b4654ea54679ca8749ebe8aa0da8c: A1-A4 (one staggered axis per grid system), C1-C2 (I23, R13 title parentheses), D1 (D31, R33 parameterId)",
        "approval": "決策佇列.md「2026-10-18 #260 最終文字確認、標題與用詞修正、短格記號治具 🔒」第 1 題「同意」(A2、A3、A5 最終全文，連同先前已同意的 D29、R22)。"
                    "D29、R22 與 D10b 首句的出處是「2026-10-18 #260 條文稿第一批回覆」第 1 題的「> 同意」：這幾段從選項二版(9f80f113)到最終版(ba7b6023)逐字未變。"
                    "第 2 題的定義推論與第 3 題「改回選項一(建議)」也見該節；第 2 題「同意」(I23、R13、D31、R33)",
        "decision": {"heading": "### 2026-10-18 #260 最終文字確認、標題與用詞修正、短格記號治具 🔒",
                     # (bullet head line, the user's quoted reply in it, clauses it names and authorizes)
                     "answers": (
                         ("- **第 1 題「上面 A2、A3、A5 三段最終文字，可以寫進公理層嗎?」**(條號 D10b、I24;連同先前已同意的 D29、R22 與白話 D10b、R22)",
                          "> 同意", ("D10b", "I24", "D29", "R22")),
                         ("- **第 2 題「補右括號、cardId 改 parameterId 這兩處小修正，可以寫進公理層嗎?」**(條號 I23、R13、D31、R33)",
                          "> 同意", ("I23", "R13", "D31", "R33")),
                     )},
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
            ("I23",
                "I23 網格引用的追溯與重算（2026-09-18 目的翻轉（分層契約）：",
                "I23 網格引用的追溯與重算（2026-09-18 目的翻轉）（分層契約）："),
            ("R13",
                "R13 拆分時承載面輔助資料跟著含錨點的那片走（與 R10 同一條（分層契約）：",
                "R13 拆分時承載面輔助資料跟著含錨點的那片走（與 R10 同一條「資料跟材料走」）（分層契約）："),
            ("D31",
                "參數卡保存獨立 id、顯示名稱、欄位及順序；每欄以 (cardId,fieldId) 為身分",
                "參數卡保存獨立 id、顯示名稱、欄位及順序；每欄以 (parameterId,fieldId) 為身分"),
            ("R33",
                "核心契約（K）：參數候選以 (cardId,fieldId) 建立欄位依賴圖",
                "核心契約（K）：參數候選以 (parameterId,fieldId) 建立欄位依賴圖"),
        ),
    },
    {
        "id": "pr318-reading-a",
        "proposal": "Issue #318 comment 6357744513 (條文修改稿第 3 版), reading A: D11 (K) sentence, I19 exception three (W), R6(d)(e) (W)",
        "approval": "決策佇列.md「2026-10-23 #318 柱跨牆階條文：核可「閱讀 A」🔒」使用者原話「同意 #318 照閱讀 A」;條號綁定見同節協調 agent 2026-10-24 補記條目",
        "decision": {"heading": "### 2026-10-23 #318 柱跨牆階條文：核可「閱讀 A」🔒",
                     # (bullet head line, the user's quoted reply in it, clauses it names and authorizes)
                     "answers": (
                         ('- **條文寫入綁定（條號 D11、I19、R6；協調 agent 2026-10-24 補記，不改上文）**：使用者回覆即上文原話',
                          "> 同意 #318 照閱讀 A", ("D11", "I19", "R6")),
                     )},
        "edits": (
            ('D11',
                '核心契約（K）：接觸候選為具型別來源鍵的有向平面及其實際有限佔用區域。對一條有寬度的軸向掃掠帶，側向定位驗整條接觸邊共線，端向裁切驗垂直端面且覆蓋完整帶寬；相等比較精確，不以單點接觸、部分覆蓋或兩個不同平面拼湊成同一完整端面。候選是否可用、允許何種來源及優先關係由固定策略明列，核心只依傳入候選及策略結果求幾何，不從來源類名或角色字串自行放行。\n',
                '核心契約（K）：接觸候選為具型別來源鍵的有向平面及其實際有限佔用區域。對一條有寬度的軸向掃掠帶，側向定位驗整條接觸邊共線，端向裁切驗垂直端面且覆蓋完整帶寬；相等比較精確，不以單點接觸、部分覆蓋或兩個不同平面拼湊成同一完整端面。這句只管被策略當成一個完整端面的候選。部分接觸、其餘不接觸，不是一個完整端面；要不要接受由模板策略另列。核心仍不從角色字串自行放行。候選是否可用、允許何種來源及優先關係由固定策略明列，核心只依傳入候選及策略結果求幾何，不從來源類名或角色字串自行放行。\n'),
            ('I19',
                '    違反 → 拒絕（V_CUT_PRIORITY），訊息指名兩支料與各自優先級。',
                '    例外三：只給 `boundary` 的固定段、在它所覆蓋那條外輪廓邊的端點：\n    端面可以頂一支或多支已放角材的側面。不要求這幾支併成一個平面，也不要求涵蓋全寬。\n    這個端點不使用「優先級必須嚴格小於自己」。至少要有一段頂到角材。完全沒頂到角材仍拒絕。\n    放得下料寬的 RC 面必須先貼角材，端面頂的是那支角材。短於料寬、放不了自己的角材的 RC 面，\n    端面沒被角材蓋到的那一段可以對著它。那段不計入角材接觸，也不另設長度上限。\n    `primary`、`secondary`、`custom` 不適用。延伸段端面不適用，仍走 I22。\n    違反 → 拒絕（V_CUT_PRIORITY），訊息指名兩支料與各自優先級。'),
            ('R6',
                '   (e) 推導出的中線與長度**不凍結**（2026-09-18 拍板反轉）：存的是位置引用（I13），\n       被引用的線或邊移動 → 重新推導中線與長度，先走 I8a 影響預覽，\n       零違規且使用者確認才提交；仍失敗整筆回滾（I8 同軌）。\n       依賴鏈取遞移閉包——A 的側面是 B 的擋面，A 動則 B 一併重算。\n       world_revalidate 仍重驗 footprint 合法 + 兩端各有恰好一個涵蓋全寬的擋面。',
                '       I19 例外三那個端面改依以下條件判定：\n       擋面必須是已放角材的側面，可以是一支或多支。不要求恰好一個，不要求這幾支共面，\n       不要求涵蓋全寬，也不要求對方優先級嚴格小於自己。完全沒有角材接觸仍是懸空拒絕。\n       不設懸空長度上限。短於料寬、放不下自己的角材的 RC 面，可以留在端面沒被角材蓋到的那一段，\n       那段不計入接觸。放得下料寬的 RC 面必須先貼角材，不得把端面直接留在裸 RC 上。\n       `primary`、`secondary`、`custom` 的端面，以及延伸段端面，仍用恰好一個全寬擋面。\n   (e) 推導出的中線與長度**不凍結**（2026-09-18 拍板反轉）：存的是位置引用（I13），\n       被引用的線或邊移動 → 重新推導中線與長度，先走 I8a 影響預覽，\n       零違規且使用者確認才提交；仍失敗整筆回滾（I8 同軌）。\n       依賴鏈取遞移閉包——A 的側面是 B 的擋面，A 動則 B 一併重算。\n       world_revalidate 仍重驗 footprint 合法 + 兩端各有恰好一個涵蓋全寬的擋面。\n       I19 例外三那個端面改驗「至少接觸一支已放角材」，其餘端面仍驗恰好一個全寬擋面。'),
        ),
    },
    {
        "id": "pr318-rc-run",
        "proposal": "Claude Code 選項題附逐字差異 (2026-10-24): I19 例外三、R6(d) 各補一句 RC 面放不放得下料寬的量法",
        "approval": "決策佇列.md「2026-10-24 #318 閱讀 A：放不放得下料寬，量 RC 面上還沒貼料的那段 🔒」條文補句條目「照這兩句寫入 (建議)」",
        "decision": {"heading": "### 2026-10-24 #318 閱讀 A：放不放得下料寬，量 RC 面上還沒貼料的那段 🔒",
                     # (bullet head line, the user's quoted reply in it, clauses it names and authorizes)
                     "answers": (
                         ('- **條文補句（條號 I19、R6；I19 例外三第 1333 行之後、R6(d) 第 1985 行之後各加一句）**：題目「要不要在 公理層.md 寫明你選的 RC 面量法？」，選項附逐字差異；使用者所選',
                          "> 照這兩句寫入 (建議)", ("I19", "R6")),
                     )},
        "edits": (
            ('I19',
                '    放得下料寬的 RC 面必須先貼角材，端面頂的是那支角材。短於料寬、放不了自己的角材的 RC 面，\n',
                '    放得下料寬的 RC 面必須先貼角材，端面頂的是那支角材。RC 面放不放得下料寬，量的是端面裸露那一段所在、\n    還沒貼角材的連續部分；同一面其餘已貼角材的部分不算進去。短於料寬、放不了自己的角材的 RC 面，\n'),
            ('R6',
                '       那段不計入接觸。放得下料寬的 RC 面必須先貼角材，不得把端面直接留在裸 RC 上。\n',
                '       那段不計入接觸。放得下料寬的 RC 面必須先貼角材，不得把端面直接留在裸 RC 上。放不放得下的量法同 I19 例外三。\n'),
        ),
    },
)
# R14 is a separate, one-shot extension of the result above.  Its approved P
# also changes the preamble and one exclusions bullet; neither is a permission
# to relax REVISION_LAYOUT or to invent a quoted answer for REVISION_APPROVAL.
# The fixture is the verbatim LF patch from #57 comment 6677737650, approved by
# #57 comment 6688023475.  It supplies every before/after byte independently of
# the current SSOT, including the final exclusions hunk (Delta 6).
R14_BEFORE_HASH = "c66c48e50e0caceef42721c79700365f090f5c48d297abba41993eeb40dba9b7"
R14_PATCH_SHA256 = "22565f314f9edbbe028a2d8a029dc071ff807b34787eb54bc10d453473230a6a"
R14_PATCH_HEADER = (
    "diff --git a/公理層.md b/公理層.md\n"
    "index bac4c5ef1fa7d64e54d1aa81ecdf8efd1636cdff..c017aae31e925a166c91b2c5d2d13f9e96c38f5a 100644\n"
    "--- a/公理層.md\n+++ b/公理層.md\n"
)
R14_HUNK_SCOPES = ("preamble", "D19a", "D19a", "I25a", "R32", "R32", "exclusions")
R14_DECISION_HEADING = "### 2026-10-27 ChatGPT 對話 9 題全部照建議 🔒"
R14_DECISION_ANCHOR = (
    "各題題意、選項與採用結果，見 #335、#128、#205、#47、#116、#57、#248、#123 各自的【ChatGPT 決策回報】;"
    "需求帳 R02、R03、R05、R11、R14、R15、R16、R17 各列已引用對應留言。"
    "涉及公理差異的項目仍沿各自正式條文採納流程。如何推翻：使用者另行指示。"
)
# This is the queue's narration, not a new > user quote.  Preserve it verbatim.
R14_DECISION_RECORD = (
    "R14 條文全文核可（🔒 2026-11-06）：使用者原話「還有 R14 可以」；"
    "範圍＝#57 留言 6677736760 全文＝P 補丁 SHA-256 "
    "22565f314f9edbbe028a2d8a029dc071ff807b34787eb54bc10d453473230a6a；"
    "紀錄見 #57 留言 6688023475。"
)
# Pin the complete recorded section as LF text, including the quoted direction
# approval and its later full-text narrative; neither can be moved into a quote.
R14_DECISION_SECTION = (
    "### 2026-10-27 ChatGPT 對話 9 題全部照建議 🔒\n\n"
    "使用者在 ChatGPT 對話的原話(ChatGPT 記錄時間台北 2026-10-27 15:21:40):\n\n"
    "> 這9題全部按照你的建議\n\n"
    + R14_DECISION_ANCHOR + "\n\n" + R14_DECISION_RECORD + "\n\n"
)
CURRENT_HASH = "5eee5c3be825cbba7b2c6ecd9ef8784d82826855a75961c1b53fb187b0f02a79"


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
    """Bind each later revision to its own recorded approvals in 決策佇列.md, bullet by bullet."""
    lines = normalized(queue_bytes).split("\n")
    used = set()
    for revision in revisions:
        decision = revision.get("decision")
        heading = decision.get("heading", "") if isinstance(decision, dict) else ""
        answers = tuple(decision.get("answers", ())) if isinstance(decision, dict) else ()
        starts = [index for index, line in enumerate(lines) if line == heading]
        bullets = []
        if heading.startswith("### ") and len(starts) == 1:
            end = next((index for index in range(starts[0] + 1, len(lines))
                        if lines[index].startswith(("### ", "## "))), len(lines))
            for line in lines[starts[0] + 1:end]:
                if line.startswith("- "):
                    bullets.append([line])
                elif bullets:
                    bullets[-1].append(line)
        heads = [bullet[0] for bullet in bullets]
        cited = [answer[0] for answer in answers if isinstance(answer, tuple) and answer]
        answered = (bool(bullets) and bool(answers) and heading not in used
                    and len(cited) == len(set(cited)) == len(answers))
        authorized = set()
        for answer in answers:
            ok_shape = (isinstance(answer, tuple) and len(answer) == 3 and isinstance(answer[0], str)
                        and isinstance(answer[1], str) and isinstance(answer[2], tuple))
            head, quote, clauses = answer if ok_shape else ("", "", ())
            if ok_shape and quote.startswith("> "):
                require(quote in APPROVAL_REPLIES, "REVISION_APPROVAL",
                        f"{revision['id']}: 原話不是同意: {quote!r} is not one of the approval replies {APPROVAL_REPLIES!r}")
            bullet = bullets[heads.index(head)] if heads.count(head) == 1 else []
            answered = answered and ok_shape and head.startswith("- ") and quote.startswith("> ") and bool(bullet) \
                and quote in {line.strip() for line in bullet[1:]} and all(
                    re.search(r"(?<![0-9A-Za-z])" + re.escape(clause) + r"(?![0-9a-z])", head) for clause in clauses)
            authorized |= set(clauses)
        edited = {edit[0] for edit in revision.get("edits", ())}
        require(answered and bool(edited) and edited <= authorized, "REVISION_APPROVAL",
                f"{revision['id']}: needs its own section {heading!r} in 決策佇列.md, each answer citing one "
                f"bullet that quotes the approval and names in its head line the clauses it authorizes, and every "
                f"edited clause {sorted(edited)} authorized (authorized: {sorted(authorized)})")
        used.add(heading)


def r14_section_heads(lines):
    """Only real Markdown section heads may anchor this narrative approval."""
    heads, fence, raw_html, literal_end, comment, html_block = [], None, None, None, False, False
    for index, line in enumerate(lines):
        if fence:
            close = re.fullmatch(r" {0,3}(`{3,}|~{3,})[ \t]*\n?", line)
            if close and close[1][0] == fence[0] and len(close[1]) >= fence[1]:
                fence = None
            continue
        if literal_end:
            if literal_end in line:
                literal_end = None
            continue
        if raw_html:
            if re.search(r"</" + raw_html + r"\s*>", line, re.IGNORECASE):
                raw_html = None
            continue
        if html_block:
            if not line.strip(" \t\n"):
                html_block = False
            continue
        if not comment:
            opened = re.match(r" {0,3}(`{3,}|~{3,})([^\n]*)\n?$", line)
            if opened and (opened[1][0] != "`" or "`" not in opened[2]):
                fence = (opened[1][0], len(opened[1]))
                continue
            opened = re.match(r" {0,3}(<\?|<!\[CDATA\[)", line)
            if opened:
                ending = "?>" if opened[1] == "<?" else "]]>"
                if ending not in line:
                    literal_end = ending
                continue
            opened = re.match(r" {0,3}<(pre|script|style|textarea)(?=[ \t>\n])", line, re.IGNORECASE)
            if opened:
                tag = opened[1].lower()
                if not re.search(r"</" + tag + r"\s*>", line, re.IGNORECASE):
                    raw_html = tag
                continue
            # Ordinary HTML blocks may have text on the opening line; a
            # following blank line ends this block, unlike the raw-text tags.
            if re.match(r" {0,3}</?[A-Za-z][A-Za-z0-9-]*(?=[ \t>/])", line):
                html_block = True
                continue
        began_in_comment, rest = comment, line
        while True:
            if comment:
                end = rest.find("-->")
                if end < 0:
                    break
                rest, comment = rest[end + 3:], False
            begin = rest.find("<!--")
            if begin < 0:
                break
            rest, comment = rest[begin + 4:], True
        if not began_in_comment and line.startswith(("### ", "## ")):
            heads.append(index)
    return heads


def verify_r14_approval(queue_bytes, patch_bytes):
    """Bind the exact P to the unique recorded full-text approval, not direction approval."""
    lines = normalized(queue_bytes).split("\n")
    starts = [index for index, line in enumerate(lines) if line == R14_DECISION_HEADING]
    require(len(starts) == 1, "R14_APPROVAL_ANCHOR", "the R14 decision section must occur exactly once")
    heads = r14_section_heads(lines)
    require(starts[0] in heads, "R14_APPROVAL_CONTEXT", "R14 approval must be outside Markdown containers")
    end = next((index for index in heads if index > starts[0]), len(lines))
    section = "\n".join(lines[starts[0] + 1:end])
    require(lines.count(R14_DECISION_RECORD) == lines.count(R14_DECISION_ANCHOR) == 1
            and R14_DECISION_ANCHOR + "\n\n" + R14_DECISION_RECORD + "\n" in section,
            "R14_APPROVAL_RECORD", "R14 needs the exact narrative at its fixed decision anchor")
    require("P 補丁 SHA-256 " + R14_PATCH_SHA256 + "；紀錄見 #57 留言 6688023475。"
            in R14_DECISION_RECORD and sha(patch_bytes) == R14_PATCH_SHA256,
            "R14_PATCH_SHA256", "the full-text approval authorizes only the reviewed P bytes")
    require("\n".join(lines[starts[0]:end]) + ("\n" if end < len(lines) else "") == R14_DECISION_SECTION,
            "R14_APPROVAL_SECTION", "the complete recorded R14 section must remain verbatim")


def apply_r14_extension(adopted, queue_bytes, patch_bytes):
    """Apply only the seven approved P hunks, once, after the unchanged older gates."""
    verify_r14_approval(queue_bytes, patch_bytes)
    require(sha(adopted.encode("utf-8")) == R14_BEFORE_HASH,
            "R14_BEFORE", "R14 requires the exact pre-R14 adoption and cannot be applied twice")
    patch = normalized(patch_bytes)
    require(patch.startswith(R14_PATCH_HEADER), "R14_PATCH_HEADER", "P must target its fixed SSOT blobs")
    hunks = []
    for line in patch[len(R14_PATCH_HEADER):].splitlines(keepends=True):
        if line.startswith("@@ "):
            match = re.fullmatch(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@\n", line)
            require(match is not None, "R14_PATCH_LAYOUT", "P has an invalid hunk header")
            hunks.append((tuple(map(int, match.groups())), []))
        else:
            require(bool(hunks) and line[:1] in (" ", "-", "+"),
                    "R14_PATCH_LAYOUT", "P has an invalid hunk line")
            hunks[-1][1].append(line)
    require(len(hunks) == len(R14_HUNK_SCOPES), "R14_PATCH_LAYOUT", "P must retain all seven reviewed hunks")
    clauses, _, headings = source_layout(adopted)
    source_lines = adopted.splitlines(keepends=True)
    result = adopted
    for scope, ((old_start, old_count, new_start, new_count), lines) in zip(R14_HUNK_SCOPES, hunks):
        before_lines = [line[1:] for line in lines if line[0] in " -"]
        after_lines = [line[1:] for line in lines if line[0] in " +"]
        before, after = "".join(before_lines), "".join(after_lines)
        changed = [index for index, line in enumerate(lines) if line[0] in "-+"]
        require(len(before_lines) == old_count and len(after_lines) == new_count
                and bool(changed) and all(lines[index][0] in "-+"
                                         for index in range(changed[0], changed[-1] + 1)),
                "R14_PATCH_LAYOUT", f"{scope}: P must retain one complete replacement per hunk")
        require(before != after and result.count(before) == 1
                and source_lines[old_start - 1:old_start - 1 + old_count] == before_lines
                and result.splitlines(keepends=True)[new_start - 1:new_start - 1 + old_count] == before_lines,
                "R14_ANCHOR", f"{scope}: the full before text must match its unique fixed anchor")
        at = result.index(before)
        change_at = at + sum(len(line) - 1 for line in lines[:changed[0]])
        removed = sum(len(line) - 1 for line in lines if line.startswith("-"))
        rows, sections, _ = source_layout(result)
        bounds = sections | {row.id: (row.start, row.end) for row in rows}
        require(scope in bounds and bounds[scope][0] <= change_at
                and change_at + removed <= bounds[scope][1],
                "R14_SCOPE", f"{scope}: P may change only its explicitly reviewed section or clause")
        result = result[:at] + after + result[at + len(before):]
    new_clauses, _, new_headings = source_layout(result)
    require([row.id for row in new_clauses] == [row.id for row in clauses]
            and [title for title, _ in new_headings] == [title for title, _ in headings]
            and {old.id for old, new in zip(clauses, new_clauses) if old.before != new.before}
            == {"D19a", "I25a", "R32"},
            "R14_LAYOUT", "R14 must retain all clause ids, chapter order and every other clause verbatim")
    return result


def validate_current_document(current_bytes, expected):
    require(normalized(current_bytes) == expected, "ADOPTED_SOURCE", "current SSOT differs from the approved, upstream-preserving result")
    clauses, _, _ = source_layout(expected)
    require(len(clauses) == len({row.id for row in clauses}) == 207,
            "ADOPTED_LAYOUT", "the adopted document must preserve all 207 clauses")


# R14 follows R17 in released main. R17's own full-text approval binds its
# exact historical bytes, not the later combined document.
R14_ON_R17_SHA256 = "41bb139fdb4767327e542eb96912437c8060c1ad84f044a7d2a30ecdb13ab4ad"
R17_ONLY_SHA256 = "13ff6cec70900b55271d9350ca31119f31ad9b20245204d67f49576ca5219712"


def restore_pre_r14_source(current_bytes):
    """Peel only the exact separately approved R14 P from a R14-on-R17 source."""
    current = normalized(current_bytes)
    # normalized() has already performed the one allowed CRLF conversion.
    # A second conversion would incorrectly accept CRCRLF source tampering.
    if hashlib.sha256(current.encode("utf-8")).hexdigest() != R14_ON_R17_SHA256:
        return current  # R17-only or a tamper; the following R17 hash gate judges it.
    patch_bytes = (ROOT / "tests/fixtures/r14-approved-axiom.patch").read_bytes()
    require(sha(patch_bytes.replace(b"\r\n", b"\n")) == R14_PATCH_SHA256,
            "R14_PATCH_SHA256", "R14 overlay requires the exact approved P bytes")
    patch = normalized(patch_bytes)
    require(patch.startswith(R14_PATCH_HEADER), "R14_PATCH_HEADER",
            "R14 overlay must use the pinned SSOT source and destination")
    hunks = [hunk for hunk in re.split(r"(?=^@@ -)", patch[len(R14_PATCH_HEADER):], flags=re.M) if hunk]
    require(len(hunks) == len(R14_HUNK_SCOPES)
            and all(re.match(r"^@@ -\d+,\d+ \+\d+,\d+ @@\n", hunk) for hunk in hunks),
            "R14_PATCH_LAYOUT", "all seven approved R14 hunks must be present")
    for scope, hunk in zip(R14_HUNK_SCOPES, hunks):
        lines = hunk.splitlines(keepends=True)[1:]
        removed = "".join(line[1:] for line in lines if line.startswith("-"))
        added = "".join(line[1:] for line in lines if line.startswith("+"))
        require(bool(added) and current.count(added) == 1,
                "R14_REVERSE_ANCHOR", f"{scope}: exact approved addition must occur once")
        current = current.replace(added, removed, 1)
    require(sha(current.encode("utf-8")) == R17_ONLY_SHA256,
            "R14_REVERSE_SOURCE", "reversing R14 must recover exact R17-approved bytes")
    return current


def restore_pre_r17_source(current_bytes, queue_bytes, delta_bytes=None):
    """Remove only the separately approved R17 delta, then use the original gate.

    GEO-261's 207-clause source/layout/decision assertions remain unchanged.
    R17's exact approved blob, fixed delta and scoped full-text approval are
    additional obligations; a direction decision cannot stand in for them.
    """
    heading = "### 2026-11-02 #335 R17 W1：成組在 World 放置順序中的位置，採 A 🔒"
    approval = "R17 條文全文核可（🔒 2026-11-06）：使用者原話「可以」；範圍＝#335 留言 6639554297 全文＝公理層.md blob 9d713b77d63df78cf5371a398c92f9536f5b6d5f；紀錄見 #371 留言 6677269286。"
    lines = normalized(queue_bytes).split("\n")
    starts = [index for index, line in enumerate(lines) if line == heading]
    section = []
    if len(starts) == 1:
        end = next((index for index in range(starts[0] + 1, len(lines))
                    if lines[index].startswith(("### ", "## "))), len(lines))
        section = lines[starts[0] + 1:end]
    require(len(starts) == 1 and lines.count(approval) == 1 and section.count(approval) == 1,
            "R17_APPROVAL", "R17 requires its exact scoped full-text approval; W1-A is only a direction decision")
    current = restore_pre_r14_source(current_bytes).encode("utf-8")
    require(sha(current) == R17_ONLY_SHA256
            and hashlib.sha1(b"blob " + str(len(current)).encode() + bytes([0]) + current).hexdigest()
                == "9d713b77d63df78cf5371a398c92f9536f5b6d5f",
            "R17_APPROVED_SOURCE", "R17 bytes differ from the user-approved full text; obtain new approval")
    if delta_bytes is None:
        delta_bytes = (ROOT / "tests/fixtures/r17-approved-delta.json").read_bytes()
    require(sha(delta_bytes) == "43738777e6d553c20aaf777fd507c802092dcdaaedcc3d9facdbf7fb11c66fb8",
            "R17_FROZEN_DELTA", "the delta derived from fixed main and the approved blob must not change")
    delta = json.loads(delta_bytes)
    require(delta["schema"] == "r17-approved-delta/1"
            and delta["beforeCommit"] == "343a8abe83029dd883e5e5b1b8e3112411fefe81"
            and delta["approvedCommit"] == "347bb01d411c9a656cae213d5cec81409445cf14"
            and delta["changedClauses"] == ["D7", "D9", "D11", "D60", "I8", "I8a", "I9", "I19", "I32", "R4", "R6", "R56"]
            and delta["addedClauses"] == ["D16a"],
            "R17_DELTA_SCOPE", "only the reviewed twelve clauses, D16a and scope census are adopted")
    restored = current.decode("utf-8").splitlines(keepends=True)
    for change in reversed(delta["changes"]):
        at, after, before = change["newStart"], change["after"], change["before"]
        require(restored[at:at + len(after)] == after, "R17_DELTA_ANCHOR", "approved after-text no longer matches")
        restored[at:at + len(after)] = before
    previous = "".join(restored).encode("utf-8")
    require(sha(previous) == "c66c48e50e0caceef42721c79700365f090f5c48d297abba41993eeb40dba9b7",
            "R17_PREVIOUS_SOURCE", "removing the exact approved delta must restore the unchanged previous main")
    return previous


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
        # Keep this legacy stage intact for all its existing negative controls.
        # The actual-SSOT gate adds R14 only after those independent old gates.
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
        queue = (ROOT / "決策佇列.md").read_bytes()
        verify_revision_decisions(queue, POST_APPROVAL_REVISIONS)
        patch = (ROOT / "tests/fixtures/r14-approved-axiom.patch").read_bytes()
        current = apply_r14_extension(self.current, queue, patch)
        actual = (ROOT / "公理層.md").read_bytes()
        actual = restore_pre_r17_source(actual, queue)
        actual = apply_r14_extension(normalized(actual), queue, patch)
        validate_current_document(actual.encode("utf-8"), current)
        self.assertEqual(CURRENT_HASH, sha(actual.encode("utf-8")))
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
        # the approval must be the user's own recorded answer about the edited clauses
        queue = (ROOT / "決策佇列.md").read_bytes()
        verify_revision_decisions(queue, POST_APPROVAL_REVISIONS)
        # the attacks below need the final-confirmation section, whose "> 同意" sits under several
        # bullets; later revisions (#318) are appended after it, so name it instead of taking the last
        approved = POST_APPROVAL_REVISIONS[0]
        final = next(revision for revision in POST_APPROVAL_REVISIONS if revision["id"] == "pr260-final")
        decision = approved["decision"]
        (head, reply, clauses), = decision["answers"]
        final_head, final_reply, final_clauses = final["decision"]["answers"][0]
        elsewhere = "> 只准一軸(建議)"
        other_heading = "### 2026-10-16 #240 S6:網格只准一軸相位差 🔒；措辭澄清待使用者看稿"
        other_head = "- **1. 同一份網格系統只准一軸有相位差 🔒**"
        text = normalized(queue)
        for line in ("\n  " + elsewhere + "\n", "\n" + other_heading + "\n", "\n" + other_head + "\n",
                     "\n" + head + "\n", "\n" + final_head + "\n"):
            self.assertIn(line, text)
        # the final-confirmation section quotes "> 同意" under several bullets: the bullet must be named
        self.assertGreater(text.split(final["decision"]["heading"], 1)[1].split("\n### ", 1)[0].count("\n  " + final_reply + "\n"), 1)
        sibling_heads = [line for line in text.split(final["decision"]["heading"], 1)[1].split("\n### ", 1)[0].split("\n")
                         if line.startswith("- ") and line != final_head]
        # opus review of #309: a second revision reusing a decision to rewrite I5 passed 44/44
        sneak = {"id": "sneak", "proposal": "x", "approval": "x", "decision": decision,
                 "edits": (("I5", "角材整支要在界內", "角材大致在界內"),)}
        unrelated = sneak | {"decision": {"heading": other_heading, "answers": ((other_head, elsewhere, ("I5",)),)}}
        # valid in every respect except that the section already backs pr260-final
        second_on_final = {"id": "second", "proposal": "x", "approval": "x",
                           "decision": final["decision"] | {"answers": ((sibling_heads[0], final_reply, ("I23",)),)},
                           "edits": (("I23", "x", "y"),)}
        verify_revision_decisions(queue, (second_on_final,))
        with_decision = lambda revision, **fields: revision | {"decision": revision["decision"] | fields}
        # opus re-review of #309/#310: attack D (a bullet that names I5, reply "> 先給我看稿再說") passed 44/44,
        # and attack C (a clause named only in a bullet's body) was accepted
        first_a_head = "- **第 1 題 A 區條文文字：同意 🔒**(同日)"
        s6_bullet2 = next(line for line in text.split(other_heading, 1)[1].split("\n### ", 1)[0].split("\n")
                          if line.startswith("- **2. 條文措辭澄清"))
        self.assertIn("I5", s6_bullet2)
        self.assertIn("\n  > 先給我看稿再說\n", text)
        self.assertIn("A3 I24", text.split(decision["heading"], 1)[1].split("\n### ", 1)[0])
        attack_d = {"id": "sneak", "proposal": "x", "approval": "x",
                    "decision": {"heading": other_heading, "answers": ((s6_bullet2, "> 先給我看稿再說", ("I5",)),)},
                    "edits": (("I5", "只有 Q 的點落在 F 之外才失敗。", "只有 Q 的點落在 F 之外才失敗，但端點相接一律算越界。"),)}
        with self.assertRaises(ProposalContractError) as caught:
            verify_revision_decisions(queue, (attack_d,))
        self.assertEqual("REVISION_APPROVAL", caught.exception.code)
        self.assertIn("原話不是同意", str(caught.exception))
        # attack C alone: the section is otherwise unused, so only the body-only clause is wrong
        attack_c = {"id": "body-only", "proposal": "x", "approval": "x",
                    "decision": {"heading": decision["heading"], "answers": ((first_a_head, "> 同意", ("I24",)),)},
                    "edits": (("I24", "x", "y"),)}
        self.reject("REVISION_APPROVAL", verify_revision_decisions, queue, (attack_c,))
        for case, revisions, record in (
                ("no decision", ({k: v for k, v in approved.items() if k != "decision"},), queue),
                ("unknown heading", (with_decision(approved, heading=decision["heading"] + "x"),), queue),
                ("not a section heading", (with_decision(approved, heading=decision["heading"][4:]),), queue),
                ("no answers", (with_decision(approved, answers=()),), queue),
                ("old two-field answer", (with_decision(approved, answers=((reply, clauses),)),), queue),
                ("reply not given", (with_decision(approved, answers=((head, "> 不同意", clauses),)),), queue),
                ("reply not an approval (another section's)", (with_decision(approved, answers=((head, elsewhere, clauses),)),), queue),
                ("approval reply that is not in this bullet", (with_decision(approved, answers=((head, "> 同意", clauses),)),), queue),
                ("C: clause named only in the bullet body",
                 (with_decision(approved, answers=decision["answers"] + ((first_a_head, "> 同意", ("I24",)),)),), queue),
                ("D: reply that is not an approval", (approved, attack_d), queue),
                ("bullet from another section", (with_decision(approved, answers=((other_head, elsewhere, clauses),)),), queue),
                ("reply not quoted", (with_decision(approved, answers=((head, reply[2:], clauses),)),), queue),
                ("bullet not named by its head line", (with_decision(approved, answers=((head[2:], reply, clauses),)),), queue),
                ("same bullet cited twice", (with_decision(approved, answers=((head, reply, clauses[:1]), (head, reply, clauses[1:]))),), queue),
                ("clause named in no bullet", (with_decision(approved, answers=((head, reply, clauses + ("D31",)),)),), queue),
                ("duplicated reply, clause only in a sibling bullet",
                 (approved, with_decision(final, answers=((final_head, final_reply, final_clauses + ("I23",)),) + final["decision"]["answers"][1:])), queue),
                ("duplicated reply, sibling bullet cited for these clauses",
                 (approved, with_decision(final, answers=tuple((sibling, final_reply, final_clauses) for sibling in sibling_heads[:1]))), queue),
                ("edited clause not authorized", (approved | {"edits": approved["edits"] + (("D31", "x", "y"),)},), queue),
                ("answer authorizing nothing", (with_decision(approved, answers=((head, reply, ()),)),), queue),
                ("sneak revision shares a decision", (approved, sneak), queue),
                ("sneak revision borrows an unrelated answer", (approved, unrelated), queue),
                ("second revision on the final-confirmation section", (approved, final, second_on_final), queue),
                ("bullet head duplicated in the section", (approved,),
                 text.replace("\n" + head + "\n", "\n" + head + "\n\n  x\n\n" + head + "\n", 1).encode("utf-8")),
                ("section duplicated", (approved,),
                 queue + ("\n" + decision["heading"] + "\n\n" + head + "\n\n  " + reply + "\n").encode("utf-8")),
                ("reply removed from the record", (approved,),
                 text.replace("\n  " + reply + "\n", "\n\n", 1).encode("utf-8"))):
            with self.subTest(case=case):
                self.reject("REVISION_APPROVAL", verify_revision_decisions, record, revisions)

        # The approved R14 P is independent of current SSOT and of the old
        # clause-only approval format.  Keep the original negative controls
        # above; exercise the separate extension here without changing census.
        patch = (ROOT / "tests/fixtures/r14-approved-axiom.patch").read_bytes()
        self.assertEqual(13646, len(patch.replace(b"\r\n", b"\n")))
        r14 = apply_r14_extension(self.current, queue, patch)
        historical = restore_pre_r17_source((ROOT / "公理層.md").read_bytes(), queue)
        self.assertEqual(apply_r14_extension(normalized(historical), queue, patch), r14)
        for case, predecessor in (("second application", r14), ("changed predecessor", self.current + "\n")):
            with self.subTest(r14=case):
                self.reject("R14_BEFORE", apply_r14_extension, predecessor, queue, patch)
        for case, code, altered in (
                ("decision heading", "R14_APPROVAL_ANCHOR", text.replace(R14_DECISION_HEADING, R14_DECISION_HEADING + "x", 1)),
                ("duplicate decision heading", "R14_APPROVAL_ANCHOR", text + "\n" + R14_DECISION_HEADING + "\n"),
                ("decision anchor", "R14_APPROVAL_RECORD", text.replace(R14_DECISION_ANCHOR, R14_DECISION_ANCHOR + "x", 1)),
                ("direction approval only", "R14_APPROVAL_RECORD", text.replace(R14_DECISION_RECORD, "", 1)),
                ("full-text approval comment", "R14_APPROVAL_RECORD", text.replace("紀錄見 #57 留言 6688023475。", "紀錄見 #57 留言 6688023476。", 1)),
                ("approved P fingerprint", "R14_APPROVAL_RECORD", text.replace(R14_PATCH_SHA256, "0" * 64, 1)),
                ("duplicate approval record", "R14_APPROVAL_RECORD", text + "\n" + R14_DECISION_RECORD + "\n"),
                ("approval moved outside its section", "R14_APPROVAL_RECORD", text.replace(R14_DECISION_RECORD, "", 1) + "\n" + R14_DECISION_RECORD + "\n")):
            with self.subTest(r14=case):
                self.reject(code, apply_r14_extension, self.current, altered.encode("utf-8"), patch)
        with self.subTest(r14="approved P bytes"):
            self.reject("R14_PATCH_SHA256", apply_r14_extension, self.current, queue, patch + b"\n")
        preamble_line, = [line for line in r14.splitlines(keepends=True)
                          if line.startswith("> **REPEAT_PANEL 一層來源子規則擴充（R14）**")]
        exclusion_line, = [line for line in r14.splitlines(keepends=True)
                           if line.startswith("- 單一父格、雙軸固定等分的手動子網格")]
        altered_sources = [("missing preamble addition", r14.replace(preamble_line, "", 1)),
                           ("missing Delta 6 exclusions", r14.replace(exclusion_line, "", 1))]
        rows = {row.id: row for row in source_layout(r14)[0]}
        for key in ("D19a", "I25a", "R32"):
            row = rows[key]
            self.assertIn("REPEAT_PANEL", row.before)
            changed = row.before.replace("REPEAT_PANEL", "REPEAT_PANEX", 1)
            altered_sources.append(("changed " + key, r14[:row.start] + changed + r14[row.end:]))
        for case, altered in altered_sources:
            with self.subTest(r14=case):
                self.reject("ADOPTED_SOURCE", validate_current_document, altered.encode("utf-8"), r14)

        self.check_r14_approval_context()
        self.check_r14_approval_section()

    def check_r14_approval_context(self):
        queue = normalized((ROOT / "決策佇列.md").read_bytes())
        patch = (ROOT / "tests/fixtures/r14-approved-axiom.patch").read_bytes()
        self.assertEqual(1, queue.count(R14_DECISION_SECTION))
        verify_r14_approval(queue.encode("utf-8"), patch)
        containers = (
            ("backtick fence", "```text\n", "```\n"),
            ("tilde fence", "~~~text\n", "~~~\n"),
            ("short close leaves long fence open", "````text\n```\n", "````\n"),
            ("HTML comment", "<!--\n", "-->\n"),
            ("pre raw text", "<pre>\n", "</pre>\n"),
            ("script raw text", "<script>\n", "</script>\n"),
            ("style raw text", "<style>\n", "</style>\n"),
            ("textarea raw text", "<textarea>\n", "</textarea>\n"),
            ("HTML block", "<div>\n", "</div>\n"),
            ("HTML block with opening text", "<div>quoted text\n", "</div>\n"),
            ("CDATA", "<![CDATA[\n", "]]>\n"),
            ("processing instruction", "<?xml\n", "?>\n"),
        )
        for case, opening, closing in containers:
            altered = queue.replace(R14_DECISION_SECTION,
                                    opening + R14_DECISION_SECTION
                                    + "## faux boundary inside container\n" + closing, 1)
            with self.subTest(r14_context=case):
                with self.assertRaises(ProposalContractError, msg="R14_APPROVAL_CONTEXT") as caught:
                    verify_r14_approval(altered.encode("utf-8"), patch)
                self.assertEqual("R14_APPROVAL_CONTEXT", caught.exception.code)
        for case, altered in (
                ("duplicate raw heading in code", queue + "\n```text\n" + R14_DECISION_HEADING + "\n```\n"),
                ("bare CR before anchor", queue.replace("\n" + R14_DECISION_HEADING, "\r" + R14_DECISION_HEADING, 1)),
                ("Unicode separator before anchor", queue.replace("\n" + R14_DECISION_HEADING, "\u2028" + R14_DECISION_HEADING, 1))):
            with self.subTest(r14_context=case):
                self.reject("R14_APPROVAL_ANCHOR", verify_r14_approval, altered.encode("utf-8"), patch)
        for case, prefix in (
                ("longer closing fence", "```text\n## quoted heading\n````\n\n"),
                ("closed tilde fence", "~~~text\n## quoted heading\n~~~\n\n"),
                ("closed comment with fence", "<!--\n```\n## commented heading\n-->\n\n"),
                ("closed mixed-case raw text", "<PRE class='quote'>\n## raw heading\n</pRe>\n\n"),
                ("HTML block ended by blank", "<div>quoted text\n## raw heading\n\n"),
                ("closed CDATA", "<![CDATA[\n## raw heading\n]]>\n\n"),
                ("closed processing instruction", "<?xml\n## raw heading\n?>\n\n")):
            with self.subTest(r14_context=case):
                altered = queue.replace(R14_DECISION_SECTION, prefix + R14_DECISION_SECTION, 1)
                verify_r14_approval(altered.encode("utf-8"), patch)

    def check_r14_approval_section(self):
        queue = normalized((ROOT / "決策佇列.md").read_bytes())
        patch = (ROOT / "tests/fixtures/r14-approved-axiom.patch").read_bytes()
        for case, section in (
                ("changed preceding narrative", R14_DECISION_SECTION.replace("15:21:40", "15:21:41", 1)),
                ("extra text inside approval section", R14_DECISION_SECTION + "unapproved extra paragraph\n\n")):
            with self.subTest(r14_section=case):
                altered = queue.replace(R14_DECISION_SECTION, section, 1)
                with self.assertRaises(ProposalContractError, msg="R14_APPROVAL_SECTION") as caught:
                    verify_r14_approval(altered.encode("utf-8"), patch)
                self.assertEqual("R14_APPROVAL_SECTION", caught.exception.code)

    def test_crlf_is_the_only_ignored_source_difference(self):
        validate_current_document(self.current.replace("\n", "\r\n").encode(), self.current)
        self.reject("ADOPTED_SOURCE", validate_current_document, self.current.replace("\n", "\r\r\n").encode(), self.current)
        queue = (ROOT / "決策佇列.md").read_bytes().replace(b"\r\n", b"\n")
        patch = (ROOT / "tests/fixtures/r14-approved-axiom.patch").read_bytes().replace(b"\r\n", b"\n")
        r14 = apply_r14_extension(self.current, queue, patch)
        self.assertEqual(r14, apply_r14_extension(self.current, queue.replace(b"\n", b"\r\n"),
                                                 patch.replace(b"\n", b"\r\n")))
        validate_current_document(r14.replace("\n", "\r\n").encode(), r14)
        self.reject("ADOPTED_SOURCE", validate_current_document, r14.replace("\n", "\r\r\n").encode(), r14)


class BoundaryPairAdoptionIntegrity(unittest.TestCase):
    APPROVAL_LINE = "R17 條文全文核可（🔒 2026-11-06）：使用者原話「可以」；範圍＝#335 留言 6639554297 全文＝公理層.md blob 9d713b77d63df78cf5371a398c92f9536f5b6d5f；紀錄見 #371 留言 6677269286。"
    HEADING = "### 2026-11-02 #335 R17 W1：成組在 World 放置順序中的位置，採 A 🔒"

    def restore(self, actual, queue, delta=None):
        function = globals().get("restore_pre_r17_source")
        self.assertTrue(callable(function), "R17_EXACT_ADOPTION_GATE_REQUIRED")
        return function(actual, queue, delta)

    def approved_queue(self):
        # Synthetic positive control for the approval guard only; the actual
        # adoption test below separately reads the real decision queue.
        return (self.HEADING + "\n\n" + self.APPROVAL_LINE + "\n").encode()

    def reject(self, code, *args):
        with self.assertRaises(ProposalContractError) as caught:
            self.restore(*args)
        self.assertEqual(code, caught.exception.code, str(caught.exception))

    def test_r17_full_text_approval_and_exact_delta_restore_the_frozen_previous_adoption(self):
        AdoptionIntegrity.setUpClass()
        actual = (ROOT / "公理層.md").read_bytes()
        restored = self.restore(actual, (ROOT / "決策佇列.md").read_bytes())
        validate_current_document(restored, AdoptionIntegrity.current)
        # The frozen 207-clause CURRENT_HASH is the R14-only result, whereas
        # restore_pre_r17_source returns its exact pre-R14 predecessor.
        # Reapply the approved P to retain the original oracle unchanged.
        replay = apply_r14_extension(
            normalized(restored), (ROOT / "決策佇列.md").read_bytes(),
            (ROOT / "tests/fixtures/r14-approved-axiom.patch").read_bytes())
        self.assertEqual(CURRENT_HASH, sha(replay.encode("utf-8")),
                         "R17_OLD_207_CLAUSE_ORACLE_UNCHANGED")
        self.assertEqual(len(source_layout(AdoptionIntegrity.current)[0]), 207)
        rows = source_layout(normalized(actual))[0]
        self.assertEqual(len(rows), 208)
        ids = [row.id for row in rows]
        self.assertEqual(ids[ids.index("D16"):ids.index("D17") + 1], ["D16", "D16a", "D17"])

    def test_r17_direction_approval_or_misplaced_full_text_record_cannot_authorize_the_text(self):
        actual = (ROOT / "公理層.md").read_bytes()
        approved = self.approved_queue()
        self.restore(actual, approved)
        for queue in (
                (self.HEADING + "\n\n> A 好 沒人做的也派出去\n").encode(),
                approved + ("\n" + self.APPROVAL_LINE + "\n").encode(),
                (self.HEADING + "\n\n### 另一個決策\n\n" + self.APPROVAL_LINE + "\n").encode(),
                approved.replace(b"6639554297", b"6639554298"),
                approved.replace(b"9d713b77", b"00000000"),
                approved.replace(b"6677269286", b"6677269287"),
                approved + approved):
            with self.subTest(queue=hashlib.sha256(queue).hexdigest()):
                self.reject("R17_APPROVAL", actual, queue)

    def test_r17_approved_blob_rejects_byte_changes_omission_and_unapproved_new_clauses(self):
        actual = (ROOT / "公理層.md").read_bytes().replace(b"\r\n", b"\n")
        approved = self.approved_queue()
        restored = self.restore(actual, approved)
        for changed in (actual + b"\n", actual.replace("成組".encode(), "群組".encode(), 1),
                        actual.replace("不提供解除成組".encode(), "提供解除成組".encode(), 1),
                        actual.replace(b"\n", b"\r\r\n"), restored,
                        actual + "\nD99 未經核可的新條文\n".encode()):
            with self.subTest(sha256=hashlib.sha256(changed).hexdigest()):
                self.reject("R17_APPROVED_SOURCE", changed, approved)
        self.assertEqual(restored, self.restore(actual.replace(b"\n", b"\r\n"), approved),
                         "R17_ONLY_CRLF_NORMALIZATION_IS_ALLOWED")

    def test_r17_delta_cannot_be_rewritten_with_the_current_document(self):
        actual = (ROOT / "公理層.md").read_bytes()
        delta = (ROOT / "tests/fixtures/r17-approved-delta.json").read_bytes()
        self.assertEqual(sha(delta),
                         "43738777e6d553c20aaf777fd507c802092dcdaaedcc3d9facdbf7fb11c66fb8")
        changed = json.loads(delta)
        changed["changes"][0]["before"] = changed["changes"][0]["after"]
        for mutated in (delta + b"\n", json.dumps(changed, ensure_ascii=False).encode()):
            self.reject("R17_FROZEN_DELTA", actual, self.approved_queue(), mutated)

    def test_r17_plain_explanation_covers_the_complete_adopted_scope(self):
        text = normalized((ROOT / "geometry-guide/公理層-白話.md").read_bytes())
        matches = list(re.finditer(r"^## ([DIR][0-9]+[a-z]?)\n", text, re.M))
        rows = {match.group(1): text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)]
                for index, match in enumerate(matches)}
        requirements = {
            "D7": ("D16a", "整條", "不保存"),
            "D9": ("成組關係", "定義", "第三個"),
            "D11": ("D16a", "START", "END", "相反", "正長度"),
            "D16a": ("boundary-pair/1", "兩支", "FIXED", "e<i>", "來源閉包", "同向", "反向", "深度側", "無序對",
                      "序列末端", "保留原組位置", "不提供解除", "下游", "安裝", "拉力"),
            "D60": ("boundary-pair delete", "定義輸入行", "不是"),
            "I8": ("D16a", "候選", "確認"),
            "I8a": ("D16a", "沒有", "來源", "身分帳未啟用"),
            "I9": ("boundary-pair begin", "兩份", "循環", "下游"),
            "I19": ("D16a", "相向實體端面", "正長度", "全寬"),
            "I32": ("boundary-pair/1", "能力", "拒絕", "不會自動啟用"),
            "R4": ("boundary-pair begin", "boundary-pair end", "confirm", "cancel", "delete", "四份", "token", "尚未保存"),
            "R6": ("D16a", "J_i=E_i", "完整合法區間", "不回寫", "不同幾何候選", "下游"),
            "R56": ("D16a", "begin／body／end", "至多一次", "原樣確認", "未啟用"),
        }
        for clause, phrases in requirements.items():
            with self.subTest(clause=clause):
                self.assertIn(clause, rows, "R17_PLAIN_CLAUSE_REQUIRED")
                for phrase in phrases:
                    self.assertIn(phrase, rows[clause], "R17_PLAIN_COMPLETE: " + clause + ": " + phrase)


if __name__ == "__main__":
    unittest.main(verbosity=2)
