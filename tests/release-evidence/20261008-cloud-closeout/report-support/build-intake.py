#!/usr/bin/env python3
"""Render the existing finite issue/PR scope; no external calls or dispatch."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
E = Path('/workspace/closure-evidence')
raw = json.loads((E / 'inventory/remote-refresh-environment-return/open-prs.json').read_text())
pins = sorted([{'number': p['number'], 'head_sha': p['head']['sha'],
                'base_branch': p['base']['ref'], 'url': p['html_url']} for p in raw], key=lambda p: p['number'])
prs = {
129: '未納入：PF-0 語義仍待採納；維護者只對最新決策差分，沒有授權就不實作、不改公理。',
134: '已含候選：完成 rule-reader／既有跨面選線及引用的候選 gate；不新增管理器。',
136: '已含候選：保留 Windows birth-time binary 身分修正；Windows QA 補候選啟動／binary 身分與平台回歸。',
137: '已含候選：82／34 現版 gates 已有 raw；更新 PR 內過期 freeze 摘要，並與唯一 app/space writer 收斂完整安全 Resume，不撤安全 guard。',
141: '不重合 head：7 份實作／測試已由 #146 接回；2 份文件另核。完成 standalone controller/browser owner gate，勿把九檔全稱元件。',
143: '已含候選：在候選完成 shared-room-display 及來源 closure／Undo／Redo／ZIP gate。',
144: '已含候選：完成 feedback-resize-observer 正常／真錯誤／人工回報 gate；不忽略非預期 exception。',
146: '已含候選：完成 rule-cases、rule-case-races、standalone owner gates；保留六案例與歷史未核信語義。',
147: '已含候選：#123 G3 按既有矩陣核對刪除对比／間距及 keyboard，綁 5174 screenshot/raw；不全關 #123。',
148: '已含候選：#123 F6 12px 已有來源；用當前 space gate/量測綁定，不重做或推成整份設計已完成。',
152: '已含候選並有 adapter 修复：核剩餘已定義 UI／狀態／鍵盤／保存匯出證據；新 PR metadata 用原工具冪等入私有 ledger，舊 DB 缺件保留。',
153: '已含候選：room-pan 32／0 已得；收 worker／keyboard／acceptance 同候選與完整保存，保持 #54 單房。',
154: '已含候選：沿 full CDP／room-worker 核 PDF cancel/reject 釋放，若觀察真缺陷才修，不以環境中斷當資源漏失。',
155: '已含候選：keyboard原輪中斷保留；room-keyboard-r2完整396／0已得。沿matrix核收原census與正常Enter／取消，不重播不變材料。',
156: '已含候選：在完整 CDP及 drawer/cancel 既有 gates 收 guide／card inspection await 歸屬證據。',
157: '提案未納入：與已授權 #87 session slice 分開；不要將 proposal merge 或當新採納功能。',
158: '已含歷史證據：保持原 Windows/head 綁定及原失敗，#152/#134/#156 當前結果另附；不可改標新版或填回缺失 raw。',
159: '已含候選：model-history 35／0 已得，連同同版 full CDP 和實際 model library keyboard/history 檢查核收。',
160: '已含候選：rule-reader／full CDP 核 exact-cell query 後焦點；保留正常 Tab/Enter，不強制 click。',
161: '已含候選：model-history 35、save-roundtrip 33 已得；補非空 typed drafts 綜合 reopen，歷史 10／155 缺件仍獨立。',
162: '已交付：8b9b6f8 ABC 原證据曾核；保持已完成 oracle 判定，當前候選 gate另列，不重列無人接手。',
165: '已含文件：保留願景非已採納公理的界線；整理 stale 範圍語句，不能由文件量推定產品完成。',
167: '已含候選：Q38 native 有 full-suite證據；完成 UI／18-check fresh-browser producer／13-check 自有服務 restart，來源圖及跨物件影響不省略。',
168: '已含測試修正：保留真卡片位置 commit 等待；已取消的 review comment 不發、不轉貼。原 Windows partial 不當當前 full。',
169: '既有依賴來源：保持未批准 review comment 暫停；新整合 draft清楚列依賴與仍失敗項，不自行 merge main。',
170: '已接回：保留乾淨 GRID 346／0、P88 137 限定證據；ce095 文案/hash修正無需同版重跑，勿擴成全產品通過。',
171: '已接回：I42 ownership 原因與拒絕後完整 dump/assembly-read不變已驗；與候選保存重開結果一起核收，不只看 ok:false。',
172: '來源審查交付：依 #174 實測結果更新引用，來源推導不稱 browser 已失敗。',
173: 'ce74產品已接回、12／4；新181僅四份文件，待凍結後merge。唯一writer修replacement殘值，保留三視圖新8的4個token-only fail與4成功pass；未觀察World污染。確認寫入交接。',
174: '5083 projection已過：同檔唯一 writer修 held-bhit 的 edit世代＋pointer gesture歸屬，重播原bhit/proj；作者原兩例不替此新缺陷。',
175: '命令／文件已接回：交 owner更新 AF_UNIX未執行與九元件檔過期語句；每項結果仍連原受測SHA，不稱新功能。',
}
issues = {
166: '證據 owner 保留來源分歧與未確定項，將每個判定連到 raw；不把跨模型／跨 agent 同意當驗收。',
142: 'QA 完成表列必要 gates及空白→操作→保存→清空→重開；按流程缺口判定，不能以 suite 數量關單。',
128: '維護者將 #129 與最新決策檔逐項對差分；PF-0 精確語義未採納前不改 SSOT或實作。',
123: 'UI owner 按43列來源矩陣先核 C2/C4實測及已定義差距；正常 click/Tab/Enter綁候選，附件僅另阻原稿比較。',
119: 'QA 在 full CDP既有容量診斷核勾選量／實際結果一致；需改容量或新政策時另列決策。',
118: 'QA 收 #154/#156 的 PDF取消／拒絕釋放、guide／card晚回覆結果；只修真可重現失效。',
116: '已合 #125 面內右鍵B不重做；完成 issue116 gate及保存/重開，app.js只交唯一writer修缺陷。',
87: 'QA 完成獨立34項 multiroom gate及共享來源回歸；只核已授權 session slice，不混#54或採納#157。',
85: '保留已跑 mutation --check freshness與舊48筆完整SHA；裁判或native變更才重算實跑，不把check當重跑。',
77: '完成 owner及browser/exit/recovery/remove五入口，核共享來源、獨立Boundary、引用、bytes與既有receipt recovery；必要時補同版ZIP閉環。',
62: '證據 owner 把SR01–SR24逐項連到實際來源/gate原件；未核項保留下一步，不由父suite推成全部pass。',
61: '沿 #133/#134 rule editor/display完成reader、跨面與選線/焦點；不新增平行管理器。',
60: '完成compound非空模型/typed draft與source/capability preflight，再從完整清空經產品Open核同包；不用內部load假充。',
59: '核 full native既有 C按需細分、引用、原子交易契約與其具名結果；僅修已證違约，不建第二core。',
58: '契約 reviewer對採納條文／現行契約列實際差分；矛盾交決策，不由C實作反推新公理。',
57: '將 #58–62 coverage與剩餘流程映到父單；子項有證據才更新，不自動關單。',
54: '限單房；acceptance/pan/worker與keyboard重跑均有matrix原件。核收正常/取消/保存重開覆蓋，效率目標未據此整單完成。',
49: '收 #146 formal/race與standalone owner各gate；六有限案例、過期指紋、ZIP隔離不可由舊#141頭相加。',
48: '完成 evidence-formal/component/browser與既有人工框選/换版路徑；source evidence link不得改幾何。',
47: '核已合雙向定位切片的當前回歸；F4b裁切餘料另列未定案，不順手實作。',
46: '核#137已交checkpoint/Finish/捨棄，協調app/space writer完成durable資格、exact resolve、metadata-only安全Resume；阻擋保留。',
45: '完成grid-raw-provenance gate核已合有限raw grid/F2a入口及拒絕未完成資料；未定組合另列。',
44: '核候選已有source追溯/受控更新與formal evidence gates；不重做foundation。',
43: '對子切片逐項標已實作、待驗、未採納；總單不可因已合幾個PR就自動完成。',
25: '只核 D34/I42/R35有限生成及member-native ownership；以完整native/reopen拒絕不變證據關有界切片，不擴任意拓撲。',
24: '把既有assembly 24項核到當前來源/行為；A24實體裝置交裝置QA，舊數字不關目前head。',
19: '以#24/#25有限範圍彙整實作與端到端待驗；不由子native pass推整體產品完成。',
}
assert len(prs) == len(pins) == 31 and len(issues) == 27
assert set(prs) == {p['number'] for p in pins}
lines = ['# 本階段全部來源的具體下一步', '',
         '這是有限收尾清單，不是派工、批准或關單。最新API核對至2026-10-08T18:39:06.239960+00:00：31PR、27issues；僅#173前進181文件head，issues無delta。完整命令/分頁/hash見latest-remote-final-followup.json，先前17:16 pins仍保留在固定receipt-index.json。gate最新狀態只以../gates/matrix.md為準；已完成同版同範圍核收即可，不重跑或重排審查。', '',
         '## 27 個 issues', '', '| Issue | 下一步 |', '|---|---|']
for n, step in issues.items():
    lines.append(f'| [#{n}](https://github.com/ZhiQiYang/geometry-axiom/issues/{n}) | {step} |')
lines += ['', '## 31 個未合併 PR', '',
          '已包含的 PR 不需再重複合入；除 #141 由後續實作接回、#129/#157 未納入外，原28個heads的包含性沿原審查與後續merge保留。下列「已含」不等於整個PR目前可合併。', '',
          '| PR／完整 head | 來源 base | 下一步 |', '|---|---|---|']
for p in pins:
    n = p['number']
    lines.append(f'| [#{n}]({p["url"]}) `{p["head_sha"]}` | `{p["base_branch"]}` | {prs[n]} |')
lines += ['', '發布順序待 root 在 draft PR 明列：既有 #169 → 包含已審 #170–175 與本輪修正的整合候選；不要再把已含的旧PR逐一重複套入。#137→#143→#146等歷史依賴保持來源追溯，不把舊baseSHA冒稱現在main。', '',
          '作者／metadata不是写入交接：#173仍需明确停止/dirty状态/文件責任，#175文件同理。#168取消及#169未批准review comments保持暫停。']
(OUT / 'intake-next-steps.md').write_text('\n'.join(lines) + '\n')
print(json.dumps({'issues': len(issues), 'prs': len(pins), 'sha256': hashlib.sha256((OUT / 'intake-next-steps.md').read_bytes()).hexdigest()}))
