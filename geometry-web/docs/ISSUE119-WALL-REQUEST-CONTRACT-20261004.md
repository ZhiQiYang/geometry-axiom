# #119：材料牆要求、容量與歷史重播

本項在獨立分支 `fix/space-wall-completeness-119-20261004` 處理，draft PR124 交 root 審查，未合併、未部署。起點 main `06086aba3ab9b243ded53b1953cdc295723ffa35`；其後正常 merge `861b65e9e2281192dd41a068fdd87866617b638d`（PR114/#77）並取得有限歷史 verification 呼叫的移交。最終 executable source 為 `b22c4fd1f124000a86be3ac82c73a485507aeed9`；後續文件提交不改 executable blobs。

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

最終 source 實測：正式 PDF journey 17/17；legacy/provenance/tamper/replacement journey 20/20；材料更新、匯出、取消與手機尺寸 guards 11/11；獨立 ZIP、signed tetrahedron mesh volume、點佔有及 PDF byte 檢查 40/40。producer/model_update native 61/61；相關 metadata／工程交付／replacement native JS 53/53；store 20/20。

完整非瀏覽器 66-suite：2090 discovered、2089 pass、0 fail、1 具名 Windows GDI skip，exit 0。SPACE 完整 suite 原樣重跑 202/202、所有 groups completed；另 timber profile 79/79（明確 partial profile）。第一次最終 source SPACE 的一個像素量測失敗，當時 screenshot 顯示正確輪廓；失敗日誌保留，沒有降低 assertion 或 floor。project-switch regression 使用真正 `newProject()`，不再把 raw core reset 當成專案身分切換；斷言不變。

完整 unfiltered CDP 最終：1879 assertion pass、0 assertion fail，但 P79「房間輪廓候選與核對（#54）」等待 space preview 逾時，`completed:false`，golden 未比。不能當作完整通過。

已對其最終實際 native scene 與原測試輸入作讀取／stateless producer 診斷：八邊 notch、100 mm 要求需既有 1＋10 enclosure＋7 material carrier＝18/16；新 producer 回 I33 UNSUPPORTED。完全相同輸入送到 baseline06086aba 回 ok=true、walls=null／SPACE_CAPACITY，確認原測試依赖 #119 的部分成功。明確 wall_thickness=null 後新 producer 完成 enclosure（6,292,800,000 mm³）。沒有改 #54 或其測試；root／#54 owner 需決定並更新此 gate 的期待，不能為通過 gate 恢復默默缺材料或擴大 native16。精確輸入與兩版回應在 `cdp-p79-capacity-diagnosis.json`。

最終 source 服務 runtime `0fe60fc3fe17893be08e9d7e65afebdbdbd853250465b3768264659afa881c65`，啟動及測試後 probe 均 fresh，使用當前 registry fresh bridge/model-base。source、binary hashes 與完整 commands/logs/截圖/實际檔案在 `/workspace/handoffs/geometry-axiom-20261004/119-wall-completeness/`。完整 registry 保留 main 的 census，只把 space_modeling 28→35、model_update 23→26。

## 限制及審查狀態

歷史重播兩個 P1（舊缺牆檔不能重開、合法舊 package provenance 被過度拒絕）已按 root 移交範圍修復；root 獨審對 exact executable source b22c4fd1 給 source approve，並未等同 execution pass 或 merge 授權。

Hosted b22 workflow run [37213856344](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/37213856344) 的七個 jobs 均 failure、steps=[]（逐一查證），不是 CI green。沒有改 CI 權限／付費或手動重跑。原私人 PDF、Windows/WSL 啟動器、真手機多點觸控未測；#77 其他獨立 owner/browser gates 沒有因本報告被算為通過。使用者 PC、#54、PR114 原工作樹沒有動。

初次 source5ae 的 full CDP 在 P77 assembly review wait timeout（1689 assertion pass、0 assertion fail、completed=false、golden 未比）；中途 source 修訂的測試不作最終 gate。所有負面結果保留在 handoff，沒有用更多 assertion 取代上述正常檔案流程。
