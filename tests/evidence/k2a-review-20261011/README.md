本輪回覆 PR #201 的 6109338527／6109639149 六項審查。初版 `../k2a-20261011/` 的全部證據保留。

1. 規則重取：接受後以完整最新 `ruleDraft` 重繪；取消、接受及關閉都保存 ` 5 `／非法 `1e` 的原文。規則被其他交易修改／刪除時，兩方比較列出最新 raw 與現況。I25a 合法整數值相同時略去差異；非法原文仍列出，不修正字串。
2. 格式：依 P-054（PR 留言 6110320283）共用 `/17`。格式選擇及上限依已註冊附件能力，兩方各自 validator 守門；未知其他功能能力整包拒絕，不丟附件。`test_shared_format17.js` 用本線 validator 與 K1-b 的真固定版 validator 組合驗證單獨、共存、巢狀及剝能力／降版反例。K1-b 固定來源 `e35c52384519fae77e6067e7a3305f860b9d3a12:geometry-web/cutting-settings.js`，SHA-256 `23f44ae9717405bbc5bf95ca32f0cda47af0e25104972d0d984ed5b85d94e265`。這是分派契約，兩條實際分支的合併樹與正式 app 共存仍未驗；另一 owner 的 `/17` 專屬必帶判斷仍須按同一裁決整合。未修改決策佇列。
3. 登記：五個必要 browser gates 在 REQUIRED_BROWSER_GATES／BROWSER_GATE_SCOPES／`--list`／完整摘要中正式列出：27／16／14／17／35，共 109 個實際斷言，明示 aggregate 未驗。固定 validator 夾具具名排除，避免算成假通過 test。
4. 身份：壓縮身份 JSON 保留原始 bytes，包含執行前後完整 head／tree／所有來源 SHA-256／乾淨狀態、fresh runtime、隔離服務 session、原生編譯收據、bridge PID／路徑／SHA-256及 Node／瀏覽器 launcher 身份。ZIP 重開要求不同原生 session。`/proc/PID/exe` 此 sandbox 不可讀，明示使用 cmdline 與 launcher 檔案雜湊；不聲稱已核對不可讀的 live-exe inode。
5. 突變：20 JavaScript＋8 Chromium＋2 原生回執＋3 共用格式，共 33 個指定反例都先基準綠、語法／編譯成功、指定 test／assertion 紅、還原綠。各 results.json 指定裁判與雜湊；旁邊保留 baseline／build／red／restored 原始 log。原生回執另保留 restored-build。瀏覽器紅路徑即使提前中止，也有 preflight 身份；baseline／restored 有完整 before／after。不以任意 AssertionError、setup 錯誤或 skip 充數。
6. 修改前反例及失敗紀錄：`rule-equivalence-before.log`、`format-owner-before.log`、`format-nested-before.log` 是測試先行的實際紅。`nonbrowser-registration-failure.log` 是測試 2634 pass／0 fail／1 許可 skip，但 fixture 登記位置錯誤，aggregate exit 1；修正後重跑。`cdp-short-stack-failure.log` 是直接 serve.py 的 8 MiB stack 下 bridge 中止，不能算產品通過；正式重跑使用 start_local.py 的 16 MiB 設定。`cdp-census-interruption.log` 因同時完成 census 自動更新 expected.json，為避免身份混淆主動中止；`cdp-dirty-preflight.log` 拒絕尚未提交 census 的 dirty checkout，兩者都不列通過。正式全量與五個 gates 在 census 提交後的乾淨 head 重跑。沒有改 golden 或條文預期。

M01、M02、M03、M04、M05、M06、M07、M08、M09、M10、M11、M12、M13、M14、M14b、M15：本線 Linux／Chromium／真 ZIP 通過。理由及基本反例沿用初版逐項表；本輪追加 M15 規則 raw／現況兩方比對及格式分派反例。

完整非瀏覽器：83 suites，2634 pass／0 fail／1 具名允許 GDI skip；數量以完整執行的 --update-expected 更新。完整 CDP：84 段，2207 pass／0 fail／0 skip，逐段符合未修改 golden；P38 刻意的例外是回報驗證，不宣稱產品無例外。

`inventory.json` 指定乾淨受測 head／tree 與所有原始收據雜湊。`.gz` 可用 `gzip -dc` 還原逐字原始 JSON／mutant JS；raw_sha256 驗還原 bytes，stored_sha256 驗提交 bytes。之後的證據提交及自動 census 更新與受測 head 的差異會在 PR 的最終 head 回覆中逐檔說明，不能把不同 Git SHA 當成同一 head。

current_geometry.c 未改；原 core ledger 只做隔離 cache 的 --check，40 killed／1 crashed／4 equivalent／3 retired／0 stale。mutate 無新覆蓋；未手改 mutants_results.json。

未驗：正式 exact-head 本機 WSL 7/7、雲端 CI、OS 保存選擇器（真 ZIP 使用記憶體 writable handle）、其他具名獨立 browser owners、K1-b／K2a 真合併樹。PR #199 尚未合併；合併後須用 merge commit 納入。CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供。

GEO-219：無新入口。疊在 axiom/adopt-drafts-topology-k2a-20261011；K2a-B 疊在本分支。保持 draft，不合併、不 force push、不關 PR／issue。
