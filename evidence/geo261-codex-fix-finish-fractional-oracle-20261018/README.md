# 07 面材分數厚度：修正測試對兩層守門的過時預期

四輪已完成：修前 11／1、修後 12／0、只撤回測試修正後 11／1、復原附旁錄 12／0。這是本題完整 12 methods 的證據，不代表 PR #288 全量通過；本 publication 準備時尚未發布。

自有分支為 `codex/geo261-fix-finish-fractional-oracle-20261018`，基底 `e9c1509cf89e6f35d298743ec5e3368370316cf7`，測試修正 `cca0654f4d74920c7661827f6e197f3fd05f2311`。只改 `tests/geo261_finish_harness.c`、`tests/test_geo261_wood_finish.py`；產品來源、SSOT、時限與所有既有拒絕條件未改。

分類是「預期過時」。正常產品仍以 I52 拒絕 9.5 mm 幾何厚度；單點移除 K integer-reader 守門後，另一條真 typed version field 路徑仍保留 19/2 mm 並以 I35 拒絕。舊測試卻要求 mutant 全交易接受、取整成 9 mm，且所有拒絕都須含 I52 原子字串。

## 原始執行結果

以下都是同一完整 suite 的 12 個 methods；不是 C assertion 或子程序數。所有已完成輪 `source_stable=true`、無外層 timeout、無 error／skip。完整失敗原文保留於各輪 `command.stderr`。

| 輪次 | 測試 SHA | methods 通過／失敗 | unittest 秒 | 外層 child 秒 | exit |
|---|---|---:|---:|---:|---:|
| before | e9c1509cf89e6f35d298743ec5e3368370316cf7 | 11／1 | 8.339 | 8.512637422 | 1 |
| after | cca0654f4d74920c7661827f6e197f3fd05f2311 | 12／0 | 10.470 | 10.654845020 | 0 |
| withdrawn：只撤回測試修正 | ee6b58b113b107dbf68cf62f0fa50585e9d56c3b | 11／1 | 11.289 | 11.453909324 | 1 |
| restored：同一修正，附旁錄 | cca0654f4d74920c7661827f6e197f3fd05f2311 | 12／0 | 9.445 | 9.670181126 | 0 |

前三輪實際命令為 `python3 -B -m unittest -v tests.test_geo261_wood_finish`，由外部 recorder 設 16 MiB stack、600 秒外層上限並保留 SHA／工具版本／程序起迄／原退出。復原輪由 `record_07_finish_fractional_oracle.py` 載入同一原 suite 完整跑 12 methods，只旁錄 `WoodFinish.case` 與 `BridgeSession.command`；不改斷言、逾時、夾具或回傳物件。這一命令差異明列，旁錄新增 I/O 耗時不當成效能比較。

before 與 withdrawn 的同一原紅：

```text
AssertionError: 'thickness must be explicitly set positive integer mm in D1; no rounding' not found in 'I35: effective dimension violates its positive/nonnegative integer mm range'
```

這是測試預期被撤回後復現的失敗；本題沒有產品修正，不能稱「移除產品修正後轉紅」。

## 逐項預期遷移及條文依據

| 舊預期 | 修正後的精確約束 | 理由與保留項 |
|---|---|---|
| 所有拒絕都須含同一 I52 子字串 | 正常／復原 bridge 的 message 精確等於原 I52 完整文字；只在指定 K mutant bridge 精確等於 I35 完整文字，另核 clause | 不是接受 I52／I35 任選。D26 明定來源小數合法與整數幾何使用是兩層判斷；I35 不豁免完整使用處驗證 |
| K integer-reader 突變後 9.5 必須 valid | 同一 mutant 的 9.5 必須 invalid；仍核 INVALID、PANEL_FILL_INVALID、confirm 拒絕及 dump／revision 不變 | I52 明列 9.5／12.5 交易必須拒絕、不取整；第二道 typed quantity 分母守門不可為測試綠而刪除 |
| mutant 確認成功、厚度 9、九片 | 原成功提交與幾何斷言全部移到同一 mutant bridge 的合法 `9.000` 正控制 | 保留接受合法輸入能力，防止「全部拒絕」假綠；250×250、100×100、gap=3、九片 oracle 不變 |
| helper 依實際 valid 分支確認 | 先核本次呼叫的預期 valid，再進原分支 | 非整數若意外 valid 會先失敗，不能混入合法正控制 |
| 單點 K guard-removal 負控制 | 原獨立 native client 的 exit 1 與 `ASSERT:thickness-no-fractional-rounding` 完整保留 | 真正 K 突變 kill 與測試提案撤回紅分列；不是刪除原負控制 |

條文來源為基底 `公理層.md` 的 D26（正十進位型錄厚度與幾何整數分層）、I35（完整使用處驗證）、I52（正整數 mm、非整數不得取整），另保留 I8／I8a 的預覽唯讀與原子拒絕。未改 SSOT，沒有新增條文決策。

歷史依據：`1e437e12` 新增 typed `wood_source_version_field` 的 `den == 1` 驗證；`138595e0` 使 `wood_finish_panel_value` 真正使用該來源路徑；`37d30873` 曾把突變目標移到 K integer reader，仍沿用 mutant 全交易接受的舊預期。正常路徑仍先命中 I52，不是正常產品診斷改變。

## 保留的斷言與實際證據界線

已從 e9／cca Git 原件確認：原 101 個 C `REQUIRE` 呼叫所在整行全部保留，新增 5 個來源觀測，共 106 個；Python methods 維持 12，只有該分數厚度方法改名。修正前後檔案 SHA 與外部提案 manifest 相同，沒有隱藏產品變更。

新增來源觀測經公開 K provider 讀同一 `board@3`：quantity unit 為 LENGTH、num=19／den=2，圖為 FIELD 與 DEFINITION 兩節點、一條 DEFINITION_REQUIRED 邊，精確核 opaque key/provider 與 schema。這是獨立公開 provider 的來源觀測，不是 bridge 私有 candidate graph。

after 與 restored 都真正完成 12／12。復原輪由原始 [protocol.jsonl](protocol-restored/protocol.jsonl) 保留 174 筆事件，另有 [逐欄核對](protocol-review.json)：

- sequence 26／80 兩次真正 K fractional mutant 都 exit 1、stdout 空，stderr 精確為 `ASSERT:thickness-no-fractional-rounding line=174 error=\n`，ELF SHA 同為 `849520b455fea5c9c96d80f187b20e5ccdfdc99d1e3990acfe8f7af9bd03d185`。前者是 14 控制之一，後者是實際 bridge 路徑前的獨立 client 見證；不算兩個獨立產品缺陷。
- 正常 bridge sequence 74 與復原 bridge 167 都是 I52 invalid；mutant bridge 106 是精確 I35 invalid。sequence 77／109／170 的 confirm 均拒絕；各自前後完整 dump 相等、revision 都是 14、正式 `panelFills` 為空。**mutant invalid preview 的候選 `after` 雖有 derived thickness=9，整筆仍拒絕，不能稱已提交或幾何已放行。**
- 同一 mutant bridge binary 在 sequence 119 的材料輸入為合法 `9.000`；137 preview valid、140 confirm 成功、141 正式 read 得 thickness=9／tileCount=9、revision=15。這保留正向提交能力，沒有以「全部拒絕」取代原成功斷言。
- [withdrawn 原紅](withdrawn/command.stderr) 是只撤回測試修正的舊預期復現；[精確撤回 patch](withdrawn-commit.patch) 可重建本地 `ee6b58b1…` 的差異，不能冒稱移除產品 fix。真正產品突變是上列 K guard removal。

新增 provider 的 19/2、兩節點／一邊及完整 key／schema 由真 `materials` C case 的 REQUIRE 執行核對；protocol 沒有另外輸出 quantity JSON，不把 provider 觀測說成 bridge 私有圖。bridge 旁錄是原方法解析後 response，不是原 stdout JSON line，亦未收一般 bridge stderr；native stdout／stderr 是原 text=True 解碼結果。編譯／import／crash／timeout 不當成 mutation kill，本輪沒有這些異常。

原始結果：[before](before/command.stderr)、[after](after/command.stderr)、[withdrawn](withdrawn/command.stderr)、[restored unittest](protocol-restored/unittest.stderr)。各輪命令、UTC、原 exit 與環境見 [results.json](results.json)；旁錄執行 metadata 見 [protocol-restored/result.json](protocol-restored/result.json)。

## 環境與未驗

Linux 6.18.55 x86_64／glibc 2.41、GCC 14.2.0、Python 3.12.14、Node 24.19.0、Google Chrome 155.0.8059.84，stack 16 MiB。工具版本另存各輪 stdout；列 Chrome 版本不代表本題啟動瀏覽器。

此 suite 用 NativeBuild 在隔離目錄重編真 objects／client／bridge；recorder 的持久 registry binaries sidecars 只作環境背景，不能冒充已清除的 transient mutant 身分。旁錄只在仍存在時記 native ELF SHA，不公開 ELF。

未驗：最終組合完整 strict 非瀏覽器驗收、六 browser jobs、Windows／GDI、舊包真 UI、效能與其他架構驗收。既有 e64 全量／browser 結果維持原 SHA；本題 12 methods 不能代替 PR #288 全部驗收。

公開前綴：`evidence/geo261-codex-fix-finish-fractional-oracle-20261018/`。四輪終態原件與 protocol 已齊備並人工核對；以固定 `prepare_topic_evidence.py` 整理原件身份與精確 inventory。collector 不自行判讀測試紅綠；公開檔案不含 ELF、巨量 source inventories、秘密或整包工作區。
