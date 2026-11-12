# #297 原 probe 外層與完整 raw 唯讀審核

結論：本輪未找到錯誤判綠或缺原始場景／結果的阻擋。原 probe 已真實完成，沒有重跑、重新生成場景或修改工具。審查範圍是原 64 場景，不代替 #348 的 512 placed／history／H7 或完整 native。

## 固定身分與真終態

- execution SHA：`7a0e6dd81c54066995981393925fa46a815de2f8`。
- clean checkout：`/dev/shm/pr348-probe-source-7a0e6dd8`；前後原 `git rev-parse`／`status` 的指令與退出碼已收件，沒有自行跑 Git。
- 外層 `/dev/shm/pr348-run-probe297.py` SHA-256：`570b9086ecbd104eeea55a7ba95c02a071a89111ee3590058db646bba4b30ea9`，與已存 `tools/pr348-run-probe297.py` 一致。
- 原 registry core build exit **0**，15.145 秒；sidecar 原 command：`cc -std=c11 -O2 current_geometry.c -lm -> core`。
- 原 probe：`bash geometry-core/framing-template/core-probe/run_probe.sh /dev/shm/pr348-probe297-7a0e6dd8/run`，exit **0**，62.550101 秒。
- 外層開始 `2026-10-29T03:46:09.495139+00:00`，結束 `2026-10-29T03:47:27.635255+00:00`，exit **0**；launcher 原 subreaper 記 primary **0** 且「完成」。
- stack 16 MiB；`cpu.max = 400000 100000`。這是與帳本並行的功能 probe，**不是效能取樣**。

## 完整原件核對

審查程式 `audit_raw.py` 只讀現成原件，不 import／呼叫原 probe、parser、generator 或產品；0.061 秒，exit **0**。`RAW_MANIFEST.json` 包含讀取的 311 份原件之 bytes 與 SHA-256，`RAW_AUDIT.json` 保存逐場景核對結果。

1. 原 `index.json` 64 個 unique scene、實際 `scenes/*.scene` 集合與 `results.json` 64 場景集合完全相同；`skipped=[]`。
2. 每場 `# probe-member`、實際 timber 宣告、parsed member ID 與完整 stdout member ID 集合相同，沒有重複／遺漏／截斷。
3. **64 份 `full.rc` 都是原 bytes `0\n`**；全部 full stdout／stderr 已完整讀入、雜湊。沒有使用部分 prefix 的通過結果取代整場。
4. **2936 支全部「接受／原場景」，omitted=[]**。容量拒絕、規則拒絕、錯誤、幾何不符、未跑各 **0**。
5. 逐支從 raw stdout 獨立取出 L、完整 XYZ 原點與 A0 四個 XYZ 頂點；2936 支欄位齊全。依原裁判範圍比較 L＝輸入矩形長邊、XY 原點在矩形角、A0 XY 外框等於輸入矩形，全部一致。parsed `geometry_checked` 每筆都是原 `['L','足跡','原點']`，parsed 長度／矩形與 raw／輸入一致。
6. 原每個外層 subcommand 的 request、stdin、stdout、stderr、result 都存在；真 exit 全 0，原 stream SHA-256 全吻合，不只讀摘要。
7. 原 ELF bytes／mtime／SHA-256 對 sidecar 與外層 binary receipt 一致。另核 sidecar **195** 個來源項目與 captured include closure **185** 項，當前唯讀來源 LF-normalized hashes 全相符；詳 `SOURCE_IDENTITY_AUDIT.json`，exit **0**。

## F1 與第 65 支以後

| 場景 | 原排法 | 接受支數 | 接受 ID 65 以上 |
|---|---|---:|---:|
| f1-00 | 左上起鋪，板長沿 Y | 95 | 31（65–95） |
| f1-01 | 左下起鋪，板長沿 Y | 97 | 33（65–97） |
| f1-02 | 右上起鋪，板長沿 Y | 96 | 32（65–96） |
| f1-03 | 右下起鋪，板長沿 Y | 98 | 34（65–98） |
| f1-04 | 左上起鋪，板長沿 X | 108 | 44（65–108） |
| f1-05 | 右上起鋪，板長沿 X | 110 | 46（65–110） |
| f1-06 | 左下起鋪，板長沿 X | 109 | 45（65–109） |
| f1-07 | 右下起鋪，板長沿 X | 111 | 47（65–111） |

這裡所有 65 以上 member 都在整場原始輸出裡有完整 L／原點／A0，不是只宣告或分批重試。這批最高 111，不能改寫成已驗 116 或 512。

## 工具接線與已知限制

- `capture.Recorder.__init__` 保留同一 `env` dict；外層設定 `env['CORE_BIN']` 後，原 `Popen(..., env=self.env)` 真的會取得該值。`run/build.log` 原文為 `使用 CORE_BIN=/dev/shm/pr348-probe297-7a0e6dd8/build/core，沒有編譯`，證明走原腳本支援的現成 binary 分支。沒有落入過時只複製 K 的編譯路徑。
- capture 的 safe environment 欄沒有 `CORE_BIN`，屬環境呈現缺項；本輪用固定外層程式、原 build.log、ELF／sidecar 閉合補證。不要事後改寫原 request.json 或為此重跑。
- `CORE_TIMEOUT`、`PROBE_SCENES_DIR`、`PYTHON` 與編譯覆寫環境都先清除；原 generator／parser 未替換。`run_probe.sh` 保留原 `timeout -k 2 120` 路徑；此環境 `/usr/bin/timeout` 存在，summary 沒有「沒有 timeout 指令」降級訊息。所有 full calls 已結束，不以 inProgress 當結果。
- 外層 recorder 的整支 probe `timeout=None`，沒有 aggregate deadline；原要求是每次 core 120 秒，本輪沒有擴大它。不能把本工具拿去取代 formal native 的 2100 秒守門。capture 沒有自己的 subreaper，但本輪 launcher 有既有 reaper，且真終態已完整。
- 原 `gen_scenes.py::CORE_MAX_TIMBERS=64` 只寫 `# probe-capacity`／`over_core_cap` 歷史 metadata，沒有裁掉 members；本輪已以完整宣告與輸出逐支核實。不能把該過時註記當成核心目前仍 64，也沒有為本次修改生成器。
- 原 parser 的一般退出碼只計「錯誤／幾何不符」；不能僅憑 exit 0 推定沒有「未跑／同場未提交」。本輪另外明確核對全 64／2936 raw，兩者均 0，故此潛在誤讀沒有出現。
- 原件目前在 SHM，後續仍由 root 一次封存、持久化、核遠端 hash；本報告沒有 Git／API／push，也不宣稱外部交付已完成。

無修改建議阻擋本輪核收；保留以上範圍即可採用原結果，**不要重跑**。
