# P52／P72 證據包

本包收錄 P52-5 等待修正、P72B 導航等待修正，以及支持調查的原版失敗、基準量測、正負控制和獨立審查。來源為 `/workspace/geo261-evidence/p52`，共複製 **77 份原件、1,448,300 bytes**，每份內容逐位元組保留，沒有重寫歷史 SHA、路徑、錯誤或結果。

主分支為 `codex/geo261-closeout-20261021`。整理時主代理的最終受測版本為 `366ef501b78105d1f7242dc1f4f4752cac9086b5`；本包的各個既有測試仍依各自收據記錄實際受測版本。**本包不宣稱該最終版本的完整 canvas 或 native 驗收已完成**，其進度與結果由主代理另外封存。

## 先讀哪些

- `來源對照.md`：每一層證據對應的來源、工具與能支持的結論，包含早期工具追溯缺口。
- `正式來源撤回自證.md`：P52 正式已修來源的正常與6000ms延遲通過，以及精確撤回等待後唯一 P52-5 轉紅。
- `P72B控制v2說明.md`：P72 正常跨服務、v2 受控重載、精確撤回與具名期限控制；明確區分初版無效控制。
- `獨占量測結論.md`：main／原 final 各三輪的獨占交錯基準，全為43/43；final 可見局部耗時增加，沒有重現空 geometry。
- `canvas-original-command.json` 與 `canvas-final-original.log`：原版完整 canvas 中途失敗；1638通過、0一般失敗斷言仍然是 exit1、completed=false，不能宣告完整通過。

## 結論與必須保留的失敗

P52 正式來源正常與真 fetch 延遲6000ms各通過43/43、0例外。撤回組只在記憶體撤回等待修正，在相同延遲下42/43、唯一原 P52-5 因 `{}` 失敗；後續確實取得足跡1987..2014的 geometry並解除busy。該負控制的 exit1是具名且有後續資料支持的預期結果。

P52 正常組期間 HEAD 從 `4fe18b8b2afe79c44f8a293dcbeb119c43f0e22c` 變為 `c87c6d90bd06552b7b7b04e0d2aa42fd56f65eb3`，只提交三份架構 metadata。探針完成43/43、exit0，外層driver因HEAD檢查exit1。`committed-controls-driver.log`、原receipt及`committed-normal-acceptance.json`全部保留；不能把它改稱新SHA下重跑的正常組。

P72 初版 `p72-fixed-stale-first` 沒有成功建立控制前置，屬無效控制。它的exit1、兩層逾時與專屬瀏覽器手動清理收據全部保留，不能當產品紅燈或突變成功。v2控制改為明示控制導航排程；只有符合舊頁真值、新頁marker與oc未宣告、原settle具名ReferenceError等條件的撤回組才列為有效自證。

歷史候選v1、早期smoke、v2必要負控制也完整保留。兩個`v2-repeats-*`拒絕檢查、references永不回應、錯誤geometry、API失敗等紅燈都沒有因為不是通過紀錄而刪除。

## 原件與核對

- `原件清單.json`：77份複製原件的來源相對路徑、分類、bytes、SHA-256與原件位元組核對。
- `SHA256SUMS`：本包所有其他檔案的雜湊，可在本目錄執行 `sha256sum -c SHA256SUMS`；它不列自身。
- `未收錄清單.json`：逐項列出20份未複製檔案及理由。沒有刪除來源目錄原件。
- `正式工具來源.json`：直接讀取最終受測Git提交的九個正式工具blob計算bytes與hash；本包不附任何`.py`、`.js`或`.cjs`可執行副本。

未收錄外部工具／runner、兩份候選組裝用暫存字串，以及可持續追加的服務操作log。候選字串已有v1／v2 patch；所有測試原始log、receipt、建置與runtime快照、小型P72保存檔都保留。沒有收錄大量截圖、bin或臨時草稿。

原始說明與審查文章也逐bytes保留，所以早期文章中的「尚未完成」或「將移入正式工具」代表撰寫當時的狀態。後續實際結果請依本README、來源對照、對應原始log與receipt閱讀，不能回寫舊文章使它看似在當時已知後續結果。

## 能力界線

本包沒有重現原WSL／USB HDD當次P52-5或P68故障，缺失的原始wait trace也沒有補造。`wait-trace-original/receipt.json`是`trace-disabled-for-this-runner`，不是成功取得零筆trace。由使用者交接的WSL原log在主代理的相鄰`inherited-wsl`證據包，本處不重複複製。

最不確定仍是原交接失敗當下的確切阻塞階段，以及P72原次逐次CDP回覆時序。Linux基準、故障注入與精確撤回能支持等待修正的必要性與判定有效性，不能替代原環境的完整重演。
