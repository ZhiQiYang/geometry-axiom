# #318 source c264f4ee：第二次靜態對抗審

被審 source：`c264f4eea40493133e3d3409dd834d68c861e8d5`。這次只讀 Git 不可變 blobs、解析 AST／JSON、比較 bytes 與變更範圍；**未編譯、未執行 oracle/native/CLI/架構裁判或掃描**。metadata 收據 `review318-source-c264f4ee-r2/receipt.json` exit 0，不是產品驗收 exit 0。

先前 `0df78e9f` 的實際 H 漏線已在本 source 補入：`references.inc::reference_check_all` 每個端點呼叫 app adapter 取得 W admission，再交 `wood_contact_end_support_check`。H 保留 I8 取值失敗的逐項記錄與其後 end_faces／boundary／collision 檢查，不在 H 重造 partial／RC 判準，沒有把 K 真 full-width hits 捏成 1。adapter 的非 boundary 早回 ordinary 由 W 公開 predicate 決定。此結論只驗來源接線，未驗執行結果。

M140–M148 九個 native 控制已登記；oracle／native 新測試分別 13／5 methods 與正式 runner count 相符。九個正常失敗控制針對 W helper、span、between、W revalidation；其中 M144 `collector-partial` 撤回的是 W 共用判官，獨立 W harness 沒有連到真正 H `references.inc`。**不能由這九個 typed 控制宣稱已完成 H 漏線的撤回反證**；尚需真 CLI／bridge 路徑證據，或另有明確標示的 actual H 接線控制。

expected 遷移逐筆比較：只有舊 `step_core` 528 與 `step_mirror_core` 1056 清空；舊兩族所有代碼均為 `CORE_LIMIT_BOUNDARY_END_FREE`，凍結新正例的 `(room,layout)` 身份與兩舊族逐筆完全相同，其餘 expected JSON 內容相同。新 full/quick coverage 不依 observed keys 篩掉缺房；只有 CI 可依明確 sample 篩選。這是清單與檢查接線證據，仍不是 528／1056 筆實際 buildable 結果。

selftest 保留 STEP20 手算十支副支、seams `[1831,3639]`，改驗當前 buildable；FZ107/FZ114 當前第一可行候選以顯式數值另驗。通用 core matcher／P182 fallback／三個 C7 trace 偽造被侷限在具名 withdrawn-policy context，finally 還原 builder/checker，沒有套住當前 sweep/golden。FZ120 原 I22 extension-end 期待及其 no-ext-end 反例仍留在當前政策。這些仍待原始動態輸出，不能照本靜讀直接稱綠。

尚未驗到：golden 非空 I22 見證的當前政策遷移、三條 reader／架構、native 九組 0/1/0、builder/checker 各自撤回、逐毫米／579 掃描、所有凍結正例、真 CLI 初放／load/revalidate。雙 boundary 互相需要已放 contact 的初放次序仍是有來源依據的靜態風險，**不是已觀察到的 runtime 死結**；保持 QUESTIONS，不新增未放可作擋面或批次豁免語意。

附記：第一版 metadata collector 將 recorder 回傳 row 誤當退出碼而自行 exit 1；其中 Git show 原程序 exit 0，沒有產品測試。該原件保留 `review318-source-c264f4ee/receipt.json`，修正 collector 介面使用後另存 r2，不覆寫失敗。
