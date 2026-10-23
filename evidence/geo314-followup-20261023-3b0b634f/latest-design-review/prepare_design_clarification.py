"""Prepare a review-only handoff draft clarification; never modify a repository."""
from pathlib import Path
import difflib, hashlib, json

ROOT=Path(__file__).resolve().parent
source=ROOT/'DESIGN.original.md'
raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='4241c4c08fe5e9f096bc8b3d0e7ee05fa2d838d2fd72502afd959f0288b24901'
line_end=b'\r\n' if b'\r\n' in raw else b'\n'
before=raw.replace(b'\r\n',b'\n').decode()
after=before
edits=[(
 '   - K（`geometry-core/kernel/`）**一個字都不改**：K 沒有「提交」的概念，也不該替別的模板決定「一軸」。',
 '   - K（`geometry-core/kernel/`）提供通用候選交易、依賴求值及共同驗證／提交機制；本題的一軸相位差政策由 W 提供，R56 操作分類及比較基線由 H 供應。本次方案不修改 K 程式碼，是實作範圍的描述，不代表 K 沒有提交概念。'),(
 '3. 同一筆既改參數值又換來源：先套用改卡例外，再看換來源。換來源只有在改卡之後的當下有效值不變時才算保值。',
 '3. 當同一筆候選的原操作順序為先改該相位差欄位當時引用的參數卡、再換該欄位的來源時，前一步依改卡例外處理；後一步只有在換來源前後的有效值相同時才算保值。本款不重排候選的原操作順序。'),(
 '5. 將來明示刪除網格之後以同一 id 重建，依新建驗證，雙軸例外不延續。一般重新宣告仍是修改。現在沒有刪除網格的指令，本款不新增該指令。\n',
 '5. 將來明示刪除網格之後以同一 id 重建，依新建驗證，雙軸例外不延續。一般重新宣告仍是修改。現在沒有刪除網格的指令，本款不新增該指令。\n\n'
 '設計層的反序對照（非已執行的產品案例）：初始 u 引用 A=400，先保值解除為整數 400，再把 A 改為 500；u 已是直接值，仍為 400。依 D29 的單一來源與保值解除，不重排成先改卡，再誤判 500→400。這不是新增待拍板題；是否已有具體入口提交這組操作，仍由實際收據證明。\n')]
for old,new in edits:
    assert after.count(old)==1
    after=after.replace(old,new)
target=ROOT/'DESIGN.clarified-review-only.md'
target.write_bytes(after.encode().replace(b'\n',line_end))
patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
  fromfile='a/handoff/drafts/issue314/DESIGN.md',tofile='b/handoff/drafts/issue314/DESIGN.md'))
(ROOT/'DESIGN_CLARIFICATION.patch').write_text(patch)
summary=dict(schema='geo314-design-clarification-review-candidate/1',
 authorityHandoffSHA='b7e23a2579c5bdcf057d3ad6d04b064ac098a5c6',
 originalSHA256=hashlib.sha256(raw).hexdigest(),
 candidateSHA256=hashlib.sha256(target.read_bytes()).hexdigest(),
 patchSHA256=hashlib.sha256(patch.encode()).hexdigest(),
 edits=len(edits),originalLineEnd='CRLF' if line_end==b'\r\n' else 'LF',
 productOrTestsChanged=False,SSOTOrDecisionQueueChanged=False,
 handoffBranchChanged=False,acceptanceExecuted=False,
 exactClauseDiffApprovalClaimed=False,
 currentSourceSHA='3b0b634feb54266700cc61f26c34d7aeac4c0314',
 pending='Review-only draft candidate. Implementation authorization comes from the current user instruction, not from the prior agent draft. This does not declare precise SSOT wording approved or any dynamic case passed.')
(ROOT/'DESIGN_CANDIDATE.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
