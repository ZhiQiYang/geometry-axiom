# PR #202：遠端同側接觸遮蔽角點相切

回覆 ChatGPT `6113915701` 與 dot `6113958081`。產品提交 `adfb5d87eb174cc19ffd15be7bbfdbf1ad607aa6`；完整 57 筆帳本提交／乾淨 aggregate 受測 head `1b5919787df1124c0eb6122a886d4403ada21fd2`。交付提交另加本證據及原 runner 發現的數量表，沒有再改產品或裁判來源。

## 原始錯存與修正

柱場景 `_ax_r7_remote_flush_corner.scene` 的外輪廓面積 600 mm²，投影切除 200 mm²，應餘四個 100 mm² 分量。精確 base `635dd86ee368579aec444fb3ba16e48bccf4877e` 與前 head `851530708fee6373b95e45e28a784c627d970da6` 都錯誤成功，保存 400＋100＝500 mm²，仍包含應刪的 (15,15)；redo／重開延續污染。先合法切 4×4 孔的交易錯存 384＋100＝484，而應為 384。這是 base 已有、仍須修復的 R7 漏洞。

整側 `f[left/right]` 被 y=20..30 的遠端接觸設為 true，掩蓋 y=10 的點相切。`classify_rect_outline` 改為逐角驗證：同側輪廓邊必須包含該角點，且其裁切區間具有正長度，才允許局部貼合。無偏移取樣、不開四分量成功政策；正長度從角點開始的合法兩片案例仍成功。原 covered-run guard 與三分量拒絕測試保留。

產品只改原授權分類函式：16 新行／5 移除行。C 保留 13,192 CRLF、零 bare LF／NUL。SSOT、正典、白話、BACKLOG、決策佇列、產品 JS 未改。

## 測試先行與交易完整性

- `before/`：前 head 8515307 加新裁判，產品未修；native 416/432、reference 51 methods／64 subcase 失敗、scene 155/157，三支實際 exit 1。它是有明示 dirty 測試的來源，不能稱乾淨 8515307。
- `after/`：工作樹產品修正、尚未提交；432/432、51/51、157/157，三支實際 exit 0。來源、裁判及三支 native binary 的實際 SHA／sidecar 在各自 before／after checkout 中保存。
- 16 種反向環、換軸、環尾起點、負座標組合 × 柱／cut-strip × 無先前孔／先合法孔＝64 筆。拒絕後 dump、參照、redo 與重開保持交易前世界。拒絕未建立新 undo 記錄，因此立即 undo 會撤銷先前成功的物件定義；再 redo 才回到拒絕前 dump，沒有聲稱 undo 本身等於原 dump。
- `world-cmp/results.json` 是原生 `-O2` 全 2,904,880-byte World 的 memcmp，包含上述 64 筆：前版接受 64／相等 0；修正版拒絕 64／相等 64，compile 均 0，probe 原碼 1／0。先套合法孔再失敗也整份還原。
- `comparison/` 保存精確 base／前版／修正版的實際 query、dump、boundary、undo、redo、reopen 與二進位來源綁定。修正版拒絕後仍保留原 600 mm² 及 (15,15)，這是交易拒絕的正確結果；其幾何欄位的 hypothetical difference unequal 不能當成成功差集判定。
- 正例增加完整整數格差集 oracle：餘 500 mm²，聯集相等、無重疊、應刪點移除，apply／undo／redo／重開都驗證。原 base 143、ed877f5 153、8515307 155 場景規格及接受拒絕改動 0。

原生 World driver 首次把 stderr 合入緩衝 stdout，造成 JSON 解析失敗；原 merged log 與 parser note 保留。修正 logging driver 分開兩流後完整重跑，沒有把首次執行宣称為綠。

## 全帳本刷新

57＝49 killed＋1 crashed＋4 equivalent＋3 retired。54 個非 retired 真正重編重跑、3 個驗退休依據，seed＋四個互斥 worker 均 exit 0。`mutations/verification.json` 與各 worker 原 log／JSON、完整 ledger 保存；原 `--check` exit 0。

M67 精確恢復舊 whole-side flush guard，被兩個新增具名 R7 柱／cut-strip 場景殺死；baseline 157/157、compile 0，變異 155 pass／2 fail、無環境阻擋。M20 的 SIGSEGV 仍列 crashed，沒有改算 killed。M61–M66 及歷史 raw 未刪。

## 原完整 aggregate

原完整 83-suite aggregate：2994 項＝2987 pass／6 fail／1 個具名允許 Windows GDI skip，直接 returncode 1、608.63 秒；六紅全屬 reader。Node 全 36 檔 651/651、零 fail／cancel／skip。

原命令 `python3 tests/run_all.py --build --update-expected`，直接 Popen returncode 見 `aggregate/run.json`，沒有 preload、放寬 5 秒上限或改 concurrency。開始乾淨、結束只改原數量表；五支實際 binary／sidecar、來源與所有保存的裁判 hash 前後相同。`aggregate/log-index.json` 明示哪些檔案在本次開始後更新；其餘快取檔不是新執行證據。一秒 PID／PPID／comm 觀察可能漏短行程，也沒有強制隔離，不能當正式 WSL 裁判。

歷史四個 Node timeout 的根因仍未定位；本次綠燈不構成 flaky 豁免。舊 2721/9/1、2856/6/1、space 13/2、BrokenPipe raw 與探針限制保留在先前證據，前版 space 228/228 不是本版七 job。

## 尚未解除的合併阻擋

原 canonical reader 六紅不能豁免。`reader-diagnostic/` 只在記憶體重建：相對精確 base +1108 字元，R3／R4／R7／R8／R12／R14／R15 追溯改動，R4 partial→ok 燈號在 trace-details 外，非追溯內容與 parent 不全相同。五道 assert、獨立 SSOT、冪等、documentId／baseDocumentHash／comments／proposals／revisions／draft 身分在記憶體通過；正典 bytes 不變，沒有第二份 HTML。

唯一原同步 owner #192 交付仍為 `e37c06826d3ed5503117a47d6e3699908e2804b6`，其 41/41 對應舊產品 `02c20374a7f2798794a5237072b2216ceba2af5c`。既定整合 owner 須納入本線後在最終整合 head 原位 sync → check → 原 41 tests，保存生成物與精確 SHA 原收據。沒有把舊 HTML 搬入本線。正式同一最終 SHA 七 job、Windows GDI、強制隔離及歷史 timeout 根因仍待；維持 draft、不合併。

精確化仍只處理平面外環；樑初始 STRIP／bbox、立面障礙、帶孔包含、cut-strip 後 bbox 鬼影限制仍在。退化障礙使整份清單出錯，直接指定合法 c2 成功，未宣稱 UI 能由錯誤清單選 c2；沒有新 UI 入口。

## 可核對閉包

`closure.json` 綁定乾淨受測 head、產品 raw hash、版本化精確 base bridge compiler receipt 與 ledger；`executors/` 保存實際執行器、原 reader diagnostic 及 identity helper。腳本是各歷史階段的原件，部分會編譯／改測試工作樹，不能任意在最終 head 逐一執行並冒充原先階段。未提交執行檔、完整 source 快照或 HTML。

`SHA256SUMS` 包含所有 payload（不自雜湊）。核對：`sha256sum -c SHA256SUMS`。歷史目錄保持原樣。
