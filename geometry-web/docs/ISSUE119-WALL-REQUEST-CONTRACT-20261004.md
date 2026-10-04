# #119：材料牆要求、容量與歷史重播

本項在獨立分支 `fix/space-wall-completeness-119-20261004` 處理，draft PR124 交 root 審查，未合併、未部署。起點 main `06086aba3ab9b243ded53b1953cdc295723ffa35`；其後正常 merge `861b65e9e2281192dd41a068fdd87866617b638d`（PR114/#77）並取得有限歷史 verification 呼叫的移交。產品 executable source 為 `b22c4fd1f124000a86be3ac82c73a485507aeed9`；root 另授權 P79 測試契約修正，exact `2dda7dbe529f5a3ca7209e987040b13e6ec43329` 獲獨審 source approve。最後完整 CDP 在此凍結 source 完成，才記錄 golden。

## 重現及共同根因

以自行製作的非對稱十邊 PDF，經正式匯入、校準、描面、水平放置、確認平面投影、從面建立空間入口，保留預設勾選的 100 mm 材料牆。原 producer 回 `ok:true`、`closed:true`、`walls:null`、I33 `SPACE_CAPACITY`；普通建立及真實保存／重開都成功，保存輸入仍要求 100 mm 材料，實際沒有牆材料包。封閉只描述空間 enclosure，不能證明明選材料要求已完成。

共同根因是 producer 把材料牆求值錯誤降級為可建立的成功，workspace 又接受此成功；後續重開與新 generation 共用嚴格 preview 也會造成舊檔相容退化。因此必須分開新要求與歷史驗證，不能只補 UI `if`。

十邊局部輪廓（mm）：`(0,0) (6000,0) (6000,2500) (4800,2500) (4800,4000) (3500,4000) (3500,5000) (2200,5000) (2200,4200) (0,4200)`。PDF 800×700，自定義圖形位移 (100,150)、比例 0.09；以頁面 (100,550)→(640,550) 校準 6000 mm，使用實際編輯器點擊及長度／方向鍵描面。PDF SHA256：`3a87c8d7705c15b6a269207c0add8771c1dfa68ad9c33807f109c88a3c76c110`，1498 bytes。面放置 z=2500，明選牆底 0／牆高 3000。

## 已採納契約與有界修復

- 新 preview／create／height update／source replacement：明選牆厚即要求材料完整。沿既有 D24、I31、I33 回傳原 UNSUPPORTED／INVALID；前置容量檢查在宣告或套件求值前拒絕，不取消勾選、不改 input、不保存部分結果。若明確取消材料牆並重新預覽，輸入 `wall_thickness:null` 與結果一致。
- 空間與材料容量分別計算既有 boundary、placement、spec 命名空間；上限仍 16／16／64。十邊案例：既有 2 面＋12 enclosure 面＋7 凸角 carrier＋1 clipping carrier＝22；boundary 和 placement 都需 22/16，spec 需 4/64。
- `replay_stored(input,result)`／`/model/space-replay` 只驗證現存結果：以原壁面演算法實際重播原失敗，逐個 present package 使用既有 `verify_package` 驗證版本、provenance、hash 與實際 native geometry，精確比 definitions/request/derived 及頂層 package presence/source/summary/diagnostics。允許驗證器列舉的合法舊版本／generator，回傳原記錄、不改 metadata；不能 walls:null 就跳過驗證。
- shared `reference-workspace.js` 只改歷史 verification 的 URL 與 body（2 行）；原 package verification、assets closure、native pins、匯入原子性、undo/recovery 保留。`model_update.py` 的 OLD record 改用歷史驗證，new replacement 仍 strict preview。`app.js`、`project-store.js`、`project-ui.js` 與 native C、公理均沒有 PR124 的修改。
- 已載入歷史缺牆模型在 library／3D／review 明示未滿足要求，牆材料匯出不可用；仍完整保留已有 enclosure、原要求與失敗診斷。既有 archive schema 不變。

有界 carrier reuse 已評估而未採納：無孔且有可用封口時重用 clipping carrier 最多省 1 面，22→21 仍超限；共用凸角 boundary 不能減少 placement 消耗。滾動重宣告 carrier 會改變 earlier extrusion 的自含定義及 D25 重建結果。單一 offset footprint 或其他較大算法需另案評估選邊、孔、凹角與重建契約，未擴大容量或新增公理。

## 最終 source 的正常流程與內容

| 流程 | 保存要求與實際結果 |
| --- | --- |
| 十邊預設 100 mm | UNSUPPORTED 22/16；不能建立；勾選、draft、原世界及歷史保持 |
| 明確取消十邊材料 | 23.94 m² × 3000 mm＝71.82 m³；input=null，walls=null，診斷空；真實 save/reopen |
| 同一十邊模型更新 3200 mm | 同一 id，76.608 m³；仍明確不要求材料；save/reopen |
| 4×3 m 矩形 100 mm、3000 mm 高 | 36 m³ enclosure、4.32 m³ COMPLETE 牆材料；create/save/reopen |
| 矩形更新 3400 mm | 40.8 m³ enclosure、4.896 m³ 材料；同一 id、100 mm 要求保留；模型匯出、undo/redo、save/reopen |
| baseline 缺牆＋完整矩形＋原 PDF 的舊檔 | 真正舊版 UI 產生；open warning→save→reopen 保留兩個完整原 record、world、PDF、projection |
| 歷史缺牆模型採用合法矩形來源 | 真 UI 明選／核對；取消不改；確認同一 id 產生完整 100 mm 材料，保留另一模型／PDF；undo 恢復完整舊 record、redo 恢復新 record，再 save/reopen |
| 合法舊公理版本／不同 generator | 只變更 manifest 的契約相容變體，present packages 均通過 native verify；實際 open/save/reopen 保留其 metadata |
| 竄改 | 高度、diagnostic、mesh、偽造缺牆、非法公理 revision/hash 均原子拒絕，沒有 scene upload，原 project/history/assets 不改 |

已提交真舊檔 fixture：[issue119-legacy-missing-walls.gcanvas](../../tests/fixtures/issue119-legacy-missing-walls.gcanvas)。它由 baseline 正式 UI 保存，包含兩個模型和 PDF；不是用新 producer 編造的舊結果。材料量是材料模型包及網格的量，沒有把牆材料冒充既有角材 CSV。

遠端可直接審查的[結果及 SHA256](evidence/issue119-20261004/results.json)、[完整66-suite日誌](evidence/issue119-20261004/run-all.log)、[最終完整CDP日誌](evidence/issue119-20261004/cdp.log)、[focused P79/P84日誌](evidence/issue119-20261004/focused-p79-p84.log)、[先前P79阻塞日誌](evidence/issue119-20261004/cdp-prior-p79-blocked.log)、[P79同輸入兩版回應](evidence/issue119-20261004/p79-capacity-diagnosis.json)。真實下載檔包括 [舊檔保存](evidence/issue119-20261004/legacy-preserved.gcanvas)、[合法替換後保存](evidence/issue119-20261004/legacy-repaired.gcanvas)、[舊provenance保存](evidence/issue119-20261004/legacy-provenance-preserved.gcanvas)、[完整100mm材料更新](evidence/issue119-20261004/updated-material.gcanvas)、[十邊明確只建邊界](evidence/issue119-20261004/boundary-only.gcanvas)、[十邊＋完整矩形](evidence/issue119-20261004/two-models.gcanvas)；[ZIP/input/material audit](evidence/issue119-20261004/archive-audit.json) 列出實際內容及原PDF摘要。

最終 source 實測：正式 PDF journey 17/17；legacy/provenance/tamper/replacement journey 20/20；材料更新、匯出、取消與手機尺寸 guards 11/11；獨立 ZIP、signed tetrahedron mesh volume、點佔有及 PDF byte 檢查 40/40。producer/model_update native 61/61；相關 metadata／工程交付／replacement native JS 53/53；store 20/20。

完整非瀏覽器 66-suite：2090 discovered、2089 pass、0 fail、1 具名 Windows GDI skip，exit 0。SPACE 完整 suite 原樣重跑 202/202、所有 groups completed；另 timber profile 79/79（明確 partial profile）。第一次最終 source SPACE 的一個像素量測失敗，當時 screenshot 顯示正確輪廓；失敗日誌保留，沒有降低 assertion 或 floor。project-switch regression 使用真正 `newProject()`，不再把 raw core reset 當成專案身分切換；斷言不變。

完整 unfiltered CDP 最終：2026-10-04 16:34:42–16:59:45 UTC，1973 assertion pass、0 assertion fail、0 skipped，82 段、`completed:true`、exit 0。P79=87、P84=33；full 執行完成後 golden 僅 total 1970→1973、P79 84→87，其餘 81 段完全相同，沒有 min 或降低 floor；既有 `cdp_floor.compare` 再對 raw full result 逐段 matched，floor unit 13/13。聚合 exception count=1 是原有 P38 明確注入並驗收的 `[EXPECTED EXCEPTION] Error: fb-auto-probe`（log 525），不是新增產品例外；focused P79/P84 count=0。

先前 b22 full 在 P79 等待 preview 逾時（1879 assertion pass、0 assertion fail、`completed:false`、golden 未比），原始負面結果另存，沒有算為通過。其實際 native scene：八邊 notch、100 mm 要求需既有 1＋10 enclosure＋7 material carrier＝18/16；新 producer 回 I33 UNSUPPORTED。完全相同輸入在 baseline06086aba 回 ok=true、walls=null／SPACE_CAPACITY，確認原測試依賴 #119 的部分成功。明確 wall_thickness=null 後新 producer 完成 enclosure（6,292,800,000 mm³）。精確輸入與兩版回應在 [診斷](evidence/issue119-20261004/p79-capacity-diagnosis.json)。

root 因此只授權 `room_outline_test.js` 的最小 fixture 流程修正，不改 #54 product implementation。先保留 100 mm 並實測 SPACE_CAPACITY 18/16、create disabled、模型／來源／undo／redo 無變；實際點擊取消材料牆仍不能建立，必須重新預覽。之後保留原 shape／inside-corner／membership／receipt／cancel／undo／save／reopen oracle，驗收 closed、10 faces、原精確 volume／notch，並核對真實 saved ZIP 的 input=null、walls=null、wall volume=null、diagnostics=[]、source exact。新增三個實際斷言；focused terminal 120/120（P79 87、P84 33），再以上述完整 run 驗證，未為通過而默默缺材料或擴大 native16。[容量拒絕畫面](evidence/issue119-20261004/notch-material-capacity-refusal.png)與[明選只建邊界預覽](evidence/issue119-20261004/notch-space-preview.png)可核對。

產品 b22 正常檔案 journeys 的 runtime `0fe60fc3fe17893be08e9d7e65afebdbdbd853250465b3768264659afa881c65`；最後 2dda CDP runtime `4c60396ca8f1acd357d92872a02fbe9e8ce082e76e192b129326db6ca332a2e6`，啟動及完成後 probe 均 fresh，產品 blobs 與 b22 相同，使用當前 registry fresh bridge/model-base。source、binary hashes 與完整 commands/logs/截圖/實際檔案在 `/workspace/handoffs/geometry-axiom-20261004/119-wall-completeness/`。完整 registry 保留 main 的 census，只把 space_modeling 28→35、model_update 23→26。

## 限制及審查狀態

歷史重播兩個 P1（舊缺牆檔不能重開、合法舊 package provenance 被過度拒絕）已按 root 移交範圍修復；root 獨審對 exact product source b22c4fd1 與 P79 fixture 2dda7dbe 給 source approve；執行結果以上述 terminal logs 為準。PR 仍 draft，由 root 審查合併。

Hosted b22 run [37213856344](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/37213856344) 與 2dda run [37217044846](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/37217044846) 的七個 jobs 均 failure、steps=[]（各自逐一查證），不是 CI green；[2dda讀取證據](evidence/issue119-20261004/hosted-ci-2dda.json)。沒有改 CI 權限／付費或手動重跑。原私人 PDF、Windows/WSL 啟動器、真手機多點觸控未測；本次完整 CDP 既有 P83/P86 等 owner cases 確有執行，但沒有宣稱未包含的其他獨立 gates 通過。使用者 PC、#54 product、PR114 原工作樹沒有動；`project-store.js` 留給 #60 owner，本項沒有新增其接點。

初次 source5ae 的 full CDP 在 P77 assembly review wait timeout（1689 assertion pass、0 assertion fail、completed=false、golden 未比）；中途 source 修訂的測試不作最終 gate。所有負面結果保留在 handoff，沒有用更多 assertion 取代上述正常檔案流程。
