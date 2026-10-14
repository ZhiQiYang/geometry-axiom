# 既有集合保存路徑的容量修補

回覆 ChatGPT 6114245355、dot 6114479324。受測產品／測試及兩份前版 ZIP 提交
`580a8cf6abb14cc1dff59045114dcbaebc74feeb`；其後交付只加自動 expected 與本輪證據。

## 更正前輪宣稱

前輪 ba77565 的 /13 歷史單份相容及共用 P2 修正仍有效，但「B1 已修」不能涵蓋
既有 /17 集合的 manifest／pack 路徑。舊 L13 只驗 Features.validate，未走真正保存入口。
本輪保留全部舊原件，原位將它接到真正 pack/unpack，另補 writer／observer 全流程與前版 ZIP。

## 反例與修補

原 ba77565 上，130955-byte draft 的假想單份 envelope=131072 是正控制；130956 的
假想單份 envelope=131073，僅超一 byte。實際孤兒集合 record=131086，仍遠低於 1 MiB。
原 writer 接收兩份、觀察 base=1 刪除後補孤兒，再移除 other 都成功，剩餘草稿卻在
manifest／pack 拒容量。before-capacity 是真指定 AssertionError，before-writer 是原保存
入口實際容量拒絕，不是 mock 回覆；DOM／API 仍為 VM seam，未冒稱 Native E2E。

feature-attachments.js 的 gridUnmarkedEnvelope 在折算前，以 boundedJSON 驗完整假想
舊單份 envelope（含 record），滿足 128 KiB 及原有限 JSON／字串／深度限制才折算；
否則用未折疊集合。它只改 byte oracle，不改保存內容。project-store.js 呼叫同一 helper
後仍會從保留集合推導 /17、集合能力及上限。七新增行／一移除行（淨增六行），沒有改
project-store.js／reference-workspace.js／app.js／C。原結構、lost=true、orphan 對應、
128 KiB draft／1 MiB collection／8 MiB manifest、原始 manifest 守門及新接納預留仍驗。
沒有任意舊檔旗標、檔名、年代或一般 payload 的擴容。

## 前版真 ZIP

用精確 `6a3d37a31a43130b5398376031c70915956eb7d0` 的原 writer／observer、pack、unpack
產生並讀回 /17 孤兒集合：draft 131072、ZIP 133167 bytes。這個 head 支援集合；
沒有把不支援集合的 base49 當 /17 來源。ba77565 原 unpack 對此真容量 AssertionError 紅。
現 head cold unpack→pack→cold unpack 後 raw／ruleDraft／draftId／baseRef／refs／orphan
完整相同，格式與集合能力保留。old-reader-actual-fixtures 綁定兩份實際提交 ZIP 的 SHA、
manifest 與 6a3 原 reader cold 讀回；oldWriterSources 對 Git blob 逐 bytes 核對。

legacy6a.gcanvas 是空 world.scene 的 reader 見證；不拿它當原生／PDF E2E。
legacy6a-with-scene.gcanvas（133210 bytes）另由前版保存一個有效 boundary 1 場景，供
原 importBytes VM 路徑；PDF 解碼與原生 transport 明示為既有 fixture 替身，prepare seam
返回該輸入的 canonical final_scene。兩份由不同 producer run 產生，project UUID 不同；
legacy6a-proof 是第二次 producer 的資料，精確檔案對位以 old-reader-actual-fixtures 為準。
沒有手改 ZIP 預期或冒稱 fake PDF 為真 PDF worker。

## 原生保存與冷開

在 clean 580a8cf 上，兩個獨立 fresh native sessions／實際 bridge PID、exe、SHA 與 source
sidecar 通過 preflight。登記 ZIP gate 在兩個 130955／130956 邊界走完整原 w.setGridDraft／
native delete／observer／移除 other／真保存／另一 native session 原 importBytes 冷開：
兩份、兩份孤兒、單份孤兒各有真 ZIP；最後 raw、refs、baseRef、ruleDraft、orphan 及
World dump 相同，/17／grid-editor-drafts/1 不遺失。單份保存 ZIP 分別 131811／131812 bytes。
picker 僅接收真保存 bytes，原 backend／workspace／pack/unpack 未替換。
舊 6a3 包在瀏覽器也經原 pack/unpack cold 讀回，但沒有把它冒稱 native/PDF 匯入。

Native lifecycle 42＋ZIP 58＝100 assertions，冷 session 0 不加總；兩個登記 gates 的
父程序 subprocess.run 都 returncode=0、腳本與 stdout SHA 留存。各 gate before/after
head/tree/status/來源表相同、runtime fresh／version/session 同、bridge SHA 同。
舊 /13 131575-byte ZIP→補標→131907-byte ZIP 的原生保存／冷開與永久 lost／同 id 不復活
再次過；本輪不是完整 CDP、正式整合 owner 或 WSL 七 jobs。

## 突變與完整回歸

一個「強制折疊」變異分別以四個指定測試驗證：邊界、writer 保存、前版 reader、前版
importBytes。各有 baseline 綠、node --check 0、具名 ERR_ASSERTION 紅、還原綠且 0 skip。
後三者紅燈是容量；沒有用語法錯、逾時或 setup fail 充當 killed。
十二個前輪不同容量／writer 變異在本輪來源上重驗，48 log 亦各綠→紅→綠，0 skip。
共 16 組指定反證收據，不把同一強制折疊稱作四個不同邏輯變異；64 原 log 與 driver 封存。

完整非瀏覽器 83 suites：2654＝2653 pass／0 fail／1 允許 Windows GDI skip，exit 0，
530.9 秒；Node 688/688。四個新增測試放在原已登記檔；expected 由原 --build
--update-expected 只改 Node 684→688。before clean 580a8cf、after 只 expected，來源、
兩份 fixture、C／核心帳本、五支 binary／sidecar 前後 SHA 相同；父實際 returncode 0。
局部兩檔 Node 回歸為 86 pass／0 fail／1 原生條件 skip，不能寫成局部零 skip。

current_geometry.c／mutants_results.json 未改，mutate 無新覆蓋。原 --check 使用獨立
MUTATE_CACHE 的保存收據 metadata 模式：40 killed／1 crashed／4 equivalent／3 retired、
0 stale，exit 0；沒有重新執行 48 核心變異，也沒有手編帳本。

開發時的未補 final_scene VM transport 失敗（含最早空場景嘗試／一輪局部 JS fail）、
browser parent 漏 GEOMETRY_EXPECTED_SHA 的身份拒絕全保留。補正 fixture canonical reply
與 parent expected head 後才取得通過原件；這些 setup 失敗不算變異，也沒有拿未跑 gate
當 pass。舊的 legacy、boundary、lifecycle、整合證據未修改。

| 驗收 | 本輪狀態 |
|---|---|
| M01 | 過：兩份原生並存／三階段真 ZIP |
| M02 | 過：raw 真 ZIP cold roundtrip；兩個近限集合、前版 /17 與舊 /13 |
| M03 | 過：完整非瀏覽器同 draftId 續開回歸 |
| M04 | 過：Native 確認／Undo，原 handler VM Undo/Redo |
| M05 | 非瀏覽器 pin 過；專項 UI 本輪未驗 |
| M06 | 過：原生刪除／Undo/Redo、雙份→孤兒觀察 |
| M07 | 過：完整非瀏覽器同目標整份拒例 |
| M08 | 過：第 17 份拒例 |
| M09 | 過：草稿引用拒例 |
| M10 | 過：三格式；既有單份孤兒集合保留 /17／能力；前版 cold read |
| M11 | 過：格式／能力／型別／容量負例及十二舊變異 |
| M12 | 過：晚到／抹 lost／純移除／same-id／changed legacy flush 拒例；P2 共用回歸 |
| M13 | 舊 1280/390 收據保留；此 gate 本輪未驗 |
| M14 | 過：Native 同 ID 不復活 |
| M14b | 過：舊 /13 與一般 lost 原生冷開；舊 /17 flags／orphan 保存 |
| M15 | 非瀏覽器 repin 過；專項兩方 UI 本輪未驗 |

B1／M1 本輪限於上述已實跑保存缺口；B2 仍未解除。唯一整合 owner 回收 K1 bundle 的
merge-resolution／terminal 修正；#199 仍 open、未合併，head e837a9308642a54ba55d7d399eb66805e1d5984e，
既有最新 diff 已讀，合併後按使用者指示用 merge commit 納入。凍結最終整合 SHA 再跑完整
CDP／完整非瀏覽器／正式或代理 WSL 七項，不借本輪局部原生 gates 或舊整合收據。
GEO-219：無新入口。SSOT／白話／正典／BACKLOG／決策佇列未改；維持 draft，base
axiom/adopt-drafts-topology-k2a-20261011，K2a-B 疊本分支、PF／新任務依看板暫停。
CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供。未合併、force push、關 PR／issue，未跑 WSL。

inventory.json 含 gzip 原件與 tar 全成員 SHA。TEMP .txt driver 是歷史執行器原件，
依其歷史來源／phase 理解，不任意在最終 head 全部執行而改檔。舊 producer 隨機產生
project UUID，重跑 bytes 不須相同；原 immutable fixture 及 raw／byte 邊界不修改。
