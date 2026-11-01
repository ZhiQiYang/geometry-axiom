from pathlib import Path
import collections
import hashlib
import json

D = Path(__file__).parent
MAIN = '405f8c5e1a637a16cbe47470faf5ae1fa02b8676'
F = 'cbf0fb621888596aa14ad5f2349b503e23b1b72d'
def read(name):
    return json.loads((D / name / 'stdout.bin').read_bytes())

pages = [read(f'open-issues-page{i}') for i in range(1, 4)]
issues = [x for page in pages for x in page['items']]
assert all(page['total_count'] == 46 and not page['incomplete_results'] for page in pages)
assert len(issues) == len({x['number'] for x in issues}) == 46
assert not any('pull_request' in x for x in issues)
prs = read('responsible-pr-status')['data']['repository']
assert prs['defaultBranchRef']['target']['oid'] == MAIN
comments = read('responsible-latest-comments')['data']['repository']
historical = read('historical-and-grok-status-corrected')['data']['repository']

reasons = {
    198: '#202 head 137427563de2e94e41d067282266c232f176f0d8 已是目前 main 祖先（exit 0）；#291 已合入，BACKLOG 第 25、44 行也記載納入 #202。僅列候選：尚未逐項核對 issue 全部原始反例與最新回歸，不直接關閉。',
    335: 'issue 明列 13 mm 薄牆階的相互頂靠邊界為另案；Reading A 已批准部分不等於批次交易／共求值設計已批准。核實原始批准邊界後才可變更該依賴。',
    203: '舊 issue 要求決定間距上限、整除與 PF-0；2026-10-22～24 的鎖定決策可能已有回答。本輪未核對原始批准，不宣稱仍未拍板，也不自行採納舊提案。',
    204: '舊 issue 的 I19／端面固定提案須與後續已批准 Reading A、RC 面量法逐條對照；本輪只盤點，不新增木工語意。',
    205: '#333 FIELD-RULES 已合入 main，但完整下角材模式的提案與批准範圍仍須對照；文件落地不代表整個模板功能已驗收。',
    230: '舊 E1／P103 的 R43 單元輸入與合法 D7 場景區別須對照最新 SSOT 與原始裁決；相關 PF-H 已合入不足以單獨判定此 issue 可關閉。',
    233: '舊 E1／PF23 場景與 SSOT 衝突屬語意邊界核對項；本輪未驗證後續批准是否已完整解除，不自行更新 golden。',
    318: '#338 Reading A 列車仍 open；final native、六 browser、閱讀 A oracle 的正式缺口以最新審查與主代理新 F 收據逐項銜接。',
    248: '#288 已合入 main（API + 祖先 exit 0），但 GEO-261 總工單不能僅憑其中一張 PR 關閉；仍須對照無木工模板建置、後續列車與總範圍。',
    316: '#338 列車仍 open；已實作的 I11 覆蓋不能代替該新來源的完整驗收。',
    314: '#338 列車仍 open；題 3 比較器與禁止本功能修改 K 的反證需沿主代理既有修補來源核對。',
    322: '#324 原 Grok 分支仍 open；主代理接手的 successor 需完成整合驗收，原分支不由本工作修改。',
    300: '#348 仍 open；原 N512 兩次全 batch 600 s 超時保留，不能定位為單一 loadfile 失敗；#341/#346/#347 鏈及正式整合缺口仍在。',
    320: '#344 仍 open 且 API mergeable=CONFLICTING；strict aggregate 九項通過不等於完整 canvas／六 browser／native 通過。',
    299: '#338 列車仍 open；I22 診斷改動與跨版本 exact 的批准邊界須沿原始裁決核對，不能把舊 stdout 差異默認放行。',
    209: '#237 等待追蹤已合入的歷史紀錄不等於 P78 慢機器根因已修；保留原 issue 所需重現與回歸缺口。',
    128: '#347 空列修補仍 open；這也不是整個面材鋪滿／R10／PF 專項的完成證明。',
    61: '#133 已 merged，但 BACKLOG 明列只是第一片；跨面、手機及完整來源工作區範圍不能據此關閉。',
    62: '#133 的第一片不能替代 SGR-05 全部 24 項與完整回歸。',
    252: '歷史平行工作窗口的部分列車已合入；尚未對照所有工作項，僅可日後提出行政歸檔候選，不能整單宣告完成。',
    232: '研究工作佇列屬進度紀錄；本輪未取得完整交付與歸檔依據，先保留。',
    166: '跨模型主張對帳是流程工單；未取得範圍完成／歸檔依據，不能把沒有新留言當完成。',
    239: '證據發布流程需核對現有原件與交付制度；本輪沒有逐包審查，因此保留驗收缺口。',
}
decision_ids = {335, 203, 204, 205, 230, 233}
rows = []
for item in issues:
    n = item['number']
    category = '已合入可候選關閉' if n == 198 else ('待核實使用者決定' if n in decision_ids else '仍驗收缺口')
    rows.append({
        'number': n, 'title': item['title'], 'url': item['html_url'],
        'state': item['state'], 'updated_at': item['updated_at'],
        'category': category,
        'basis': reasons.get(n, '本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。'),
        'raw_source': next(f'open-issues-page{i}/stdout.bin' for i, page in enumerate(pages, 1) if any(x['number'] == n for x in page['items'])),
    })

pr_gaps = {
    338: '最新審查以 a6 為 checkpoint，列 S10／架構／final F、完整 native、六 browser、閱讀 A oracle 缺口。主代理已另推進新候選 F；本快照不把兩者視為同一受測來源，也不覆蓋已回收的新收據。',
    344: '完整實際 canvas 撤回／恢復與具名 P53-3/P61-10/P61-11、其他五 browser、native、帳本仍待；strict aggregate 九項不是整合通過。當前 API 顯示衝突。',
    341: '最佳化整組撤回與 none/few/dense/overflow 成本／CPU／wall 證據、final native／受影響 timber browser 仍缺；語意反證不是效能驗收。',
    346: '與上游 #343 來源鏈須收斂；完整 native、六 browser、效能、帳本與架構尚缺。歷史 11 methods／9 controls／83 builds 不移作新 final。',
    347: '先收斂 #346 來源鏈；PF1/PF2/PF3、native/browser、帳本與架構缺口。先前 empty-row 修補不代表整體面材完成。',
    348: '先收斂 #343→#346→#347→#348；兩次 N512 全 batch 600 s 原失敗保留，無 partial bytes 不能分派至四命令中的某一命令；完整七項、#297、帳本／架構仍缺。',
    323: '2026-10-23 審查所列舊 head 的 N32/base、source calls 比例、負控制與帳本紅燈需與新列車 R8／exact 證據逐一銜接。API 現在 baseRefName=main，舊 retarget 要求不可再記為現況未做。',
    324: '最新留言是承接前一則 ChatGPT 審查的回覆；五 public paths／45 tests 是舊收據。正式 native、六 browser、importers／帳本整合缺口仍轉交 successor；不修改 grok 分支。',
}
pr_rows = []
for n in [338, 344, 341, 346, 347, 348, 323, 324]:
    x = prs['p' + str(n)]
    c = comments['p' + str(n)]['comments']['nodes'][-1]
    pr_rows.append({**x, 'category': '仍驗收缺口', 'latest_comment_url': c['url'],
                    'latest_comment_created_at': c['createdAt'], 'gap_summary': pr_gaps[n]})

backlog_file = Path('/tmp/geo300-capacity-static-20261026/backlog/stdout.bin')
backlog_bytes = backlog_file.read_bytes()
assert hashlib.sha256(backlog_bytes).hexdigest() == 'ecfa7d3e3fa9895792f26ad47c51cafb6e2a95425b041205bc69983f2d50de50'
blob_ids = (D / 'backlog-blob-identity/stdout.bin').read_text().splitlines()
assert blob_ids == ['610cd00186e7a11e1401f8c39dd7ab187dd80870'] * 2
selected_lines = {3, 5, 7, 8, 9, 19, 21, 25, 44, 46, 442, 444, 445, 446, 447}
excerpt = '\n'.join(f'{i}: {line}' for i, line in enumerate(backlog_bytes.decode().splitlines(), 1) if i in selected_lines) + '\n'
(D / 'BACKLOG_EXCERPTS.txt').write_text(excerpt)

snapshot = {
    'scope': '唯讀小型 API 現況快照；不關閉 issue、不宣告產品完成、不改分支或 BACKLOG',
    'main_sha': MAIN, 'root_candidate_sha_for_context_only': F,
    'issue_total': 46, 'unique_issue_count': len(rows),
    'issue_category_counts': dict(collections.Counter(x['category'] for x in rows)),
    'issues': rows, 'responsible_prs': pr_rows,
    'grok_ownership': [{**historical['p' + str(n)], 'category': 'Grok負責不碰'} for n in [325, 331, 333]],
    'backlog': {'git_blob': blob_ids[0], 'same_at_main_and_candidate': True,
                'source_sha': F, 'path': 'BACKLOG.md', 'sha256': hashlib.sha256(backlog_bytes).hexdigest(),
                'raw_existing_packet_path': str(backlog_file), 'snapshot_date_in_document': '2026-10-19',
                'handling': '保留 2026-10-19 歷史內容；建議由 #325 負責人新增 2026-10-26 日期快照，不能直接抹除舊文。'},
    'limitations': [
        'API 是 2026-10-26 10:53:57～11:00:35 UTC 的非原子快照；沒有逐 issue 下載全部留言，故不得宣稱完整語意／批准審核。',
        'latest-comment 只取各指定 PR 最後一則；#324 是回覆，並非本輪直接重新取得它引用的較舊完整審查。',
        'API mergeable 只代表機械可合併性，reviewDecision=null 不是批准，也不等同 READY-TO-MERGE。',
        'GitHub PR baseRefOid 原樣保存；它可落後於 baseRefName 現在的分支 head，不把舊 baseOid 誤稱當前 main。',
        'API 留言作者欄與同步文字不自動構成新的使用者批准；本快照不裁決 exact／P-189 白名單。',
        'main 祖先判定不是該 issue 全部驗收；只有 #198 列為供負責人複核的關閉候選。',
        '未執行編譯、重測試、清理、fetch、push、PR 或 issue mutation；只讀 API 與既有 Git objects。',
        '第一次 historical-and-grok-status 因把 issue #230 當 PR 查而 API exit 1；保留原失敗與修正後 exit 0，這是盤點查詢錯誤而非產品失敗。',
    ],
}
(D / 'SNAPSHOT.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')

lines = [
    '# 2026-10-26 專案現況唯讀盤點', '',
    'API 快照共 46 個 open issues，無 PR 混入、無重複；指定 8 張 PR 全部仍 OPEN。這是分流與後續核對清單，不是完成報告，也沒有關閉任何 issue。', '',
    f'目前 main：`{MAIN}`。主代理候選 F：`{F}`（只作銜接資訊；遠端 #338 的 head 仍是下表 a6）。', '',
    'API 原件、完整 argv、exit、UTC、stdout/stderr hash 在每個查詢目錄的 RESULT.json；輸出原件為 stdout.bin / stderr.bin。總查詢分三頁，每頁上限 20；只取指定 PR 的最後一則留言。首次 historical 查詢誤把 issue #230 當 PR，exit 1 原件保留；修正查詢 exit 0。', '',
    '## 可候選關閉與決定邊界', '',
    '- **#198 是唯一已找到可供負責人核對的關閉候選**：#202 head 已是 main 祖先、#291 已 merged。這僅證明來源入 main，尚需對照原始反例與現有回歸後由負責人處理。',
    '- 「待核實使用者決定」表示舊提案需對照後續原始批准；不能解讀成使用者一定尚未決定。本輪沒有木工規則推理，也沒有新語意決策。',
    '- 其餘標為驗收缺口，含尚未取得整單完成證據的歷史總工單；不是宣告每一項目前都存在產品 bug。', '',
    '## 指定 PR 目前狀態', '',
    '| PR | Head／base 名稱 | API 狀態 | 最新留言時間 | 尚需核對／完成 |',
    '|---|---|---|---|---|',
]
for x in pr_rows:
    lines.append(f"| [#{x['number']}]({x['url']}) | `{x['headRefOid']}` / `{x['baseRefName']}` | {x['state']}；draft={str(x['isDraft']).lower()}；{x['mergeable']} | [{x['latest_comment_created_at']}]({x['latest_comment_url']}) | {x['gap_summary']} |")
lines += [
    '', '完整 baseRefOid 保存在 SNAPSHOT.json，並非保證該值就是 base 分支最新 tip。#323 的 base 名稱現在是 main；其舊審查中的 retarget 要求已不能當成目前未做。#338 的舊審查缺口與主代理新 F 收件分開，不重跑已有效證據，也不提前把 F 稱為全綠。', '',
    '## Open issues 分流', '',
    '| Issue | 分類 | 核對依據／下一步 |', '|---|---|---|',
]
for x in sorted(rows, key=lambda x: x['number']):
    lines.append(f"| [#{x['number']} {x['title']}]({x['url']}) | {x['category']} | {x['basis']} |")
lines += ['', '分類數：' + '；'.join(f'{k} {v}' for k, v in snapshot['issue_category_counts'].items()) + '。', '',
    '## Grok 工作範圍', '',
    '| PR | API 狀態 | 處理 |', '|---|---|---|',
]
for n in [325, 331, 333]:
    x = historical['p' + str(n)]
    extra = '已合入 main，祖先檢查 exit 0；FIELD-RULES 文件落地不等於 #205 完整功能已完成。' if n == 333 else '仍由 Grok 負責；本工作不改其分支或代為結案。'
    lines.append(f"| [#{n}]({x['url']}) | {x['state']}；head `{x['headRefOid']}` | {extra} |")
lines += ['', '## BACKLOG 日期與可接續小步驟', '',
    f'目前 main 與候選 F 的 BACKLOG.md 是同一 blob `{blob_ids[0]}`，內容 SHA-256 `{hashlib.sha256(backlog_bytes).hexdigest()}`。頂端是 **2026-10-19 歷史快照**，當時 #288 尚未合入、#300 尚未開始的文字有日期上下文，不能直接抹除。第 9 行也明定該輪只新增、不改舊文。', '',
    '可把本快照交給 #325 的負責人，新增「2026-10-26 現況核對」節，連結本 API 原件，記錄 #288/#333 已合入與 #338 等待完成的現況；保留 10-19 原節與歷史失敗。這是建議，尚未修改 BACKLOG。另可在不跑重測試的情況下，逐一對照 #198 原始凹口／尖脊案例與 main 既有測試，再提出帶來源的關閉候選說明。', '',
    '## 邊界', '',
]
lines.extend('- ' + item for item in snapshot['limitations'])
(D / 'REPORT.md').write_text('\n'.join(lines) + '\n')
print(json.dumps({'exit_code': 0, 'issues': len(rows), 'categories': snapshot['issue_category_counts'], 'responsible_prs': len(pr_rows), 'backlog_blob': blob_ids[0]}, ensure_ascii=False))
