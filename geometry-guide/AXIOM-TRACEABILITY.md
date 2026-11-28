# 公理條文、實作與裁判的對照

此工具讓缺口可見，不產生產品驗收或突變收據。`公理層.md` 仍是唯一條文來源。
基底盤點：`4c4028f8f80f09963f14a46062cbfcf8db76637b`，issue #487 工作包 X4。

## 產生與守門

在 repo 根目錄執行：

```sh
python3 -B geometry-guide/axiom_matrix.py --traceability --check-status
python3 -B geometry-guide/axiom_matrix.py --traceability --format json > /tmp/axiom-triad.json
python3 -B geometry-guide/axiom_matrix.py --traceability --format md > /tmp/axiom-triad.md
python3 -B tests/test_axiom_traceability.py -v
```

`axiom_traceability.py` 也可直接執行，參數相同但不加 `--traceability`。
`--root` 用來檢查一份明示的 checkout 或匯出樹；預設為工具所在 repo。
命令只讀來源、把報告寫到 stdout。缺狀態不會自動補齊。
`--check-status` 成功回傳 0；缺條文狀態、重複、非法格式或過期條文 hash 回傳 1。

原 `axiom_matrix.py` 與 `--strict` 保留原本弱文字追溯契約；`--strict` 的紅燈
只代表缺少連結，並不代表產品完全沒有。本片修正它漏列粗體 I/R 的標題解析，
不將「正文中的裸 D」擴大成新標題，也保留單字母後綴與章節界線。

## 每列如何讀

JSON 的 `rows` 是條文順序的完整集合，每列有條號、原檔起始行、標題與條文 hash。

| 欄位 | 意義 |
|---|---|
| `declared_status` | 狀態來源中明寫的人工判定 |
| `effective_status` | 本次可沿用的判定；已審來源 bytes 改變時退回 `unreviewed` |
| `reviewed_evidence` | 人工核對的位置、獨一錨點、舊／現行 LF SHA-256 及是否仍新鮮 |
| `candidates.implementation` | 產品來源中的條號文字線索，不是語義證明 |
| `candidates.test` | 測試、場景與已登錄場景裁判中的線索；可定位時包含方法或測試名 |
| `candidates.mutation` | 突變文字／靜態定義，明寫 unrun；不宣稱 killed |
| `gaps` | 已確認未實作、部分實作、待語義核對、證據失效或缺少追溯連結 |
| `findings` | 人工核對的不一致、應改哪一邊、已修或待辦狀態 |

五種人工狀態：

- `implemented`：所列範圍已有實作依據；仍需看理由與測試範圍，並非形式證明或 L4/L5。
- `partial`：已有部分產品，理由明列尚未落地的要求。
- `unimplemented`：有具體能力登記／closed schema／拒絕等依據可判定本條新產品尚無實作。
- `unreviewed`：語義核對未完成；不是 L0，也不是已通過。
- `not_applicable`：人工說明此條為何沒有直接產品實作義務；不能省略理由。

已定位一些實作、但只抽驗少數分支時，可以保留 `unreviewed` 並附明確位置與未驗範圍。
新條文有負向 `UNSUPPORTED` 測試，不會因此升成 `implemented`。
同一列有實作與測試文字，不會自動生成 reviewed evidence。

`axiom_without_implementation` 僅由有效的人工 `unimplemented` 判定產生。
`no_implementation_reference`、`no_test_reference` 等只是文字／追溯缺口。
`implementation_without_reviewed_test` 表示已有已審實作，但尚無已審測試連結；
不據此斷言完全沒有測試。

`unbased_implementation_candidates` 列出沒有直接條號的來源檔。一般呈現、網路、
宿主工具可能合理地沒有自己的公理；必須人工核對，不能把整份名單判違規。
例如 cutting 測試中的 R5 是另一份審查的局部編號，與公理 R5 不同；本工具不自動
將同名文字提升成驗證成功，也不重命名既有測試來抹掉原審查脈絡。

## 新條文與狀態來源

`geometry-guide/axiom-status.d/*.json` 是人工維護的來源片段，不是產生的對照表。
初始 baseline 只涵蓋上述固定基底；之後新增條文使用自己的片段，避免多人搶同一張名單。
每條恰好一筆，不支援用後面的片段覆蓋前面的判定。

```json
{
  "schema": "geometry-axiom-status/1",
  "entries": [
    {
      "id": "I999",
      "body_sha256": "由完整條文 LF bytes 算出的 SHA-256",
      "status": "unreviewed",
      "reason": "新條文已落檔，產品與測試尚待核對。",
      "evidence": []
    }
  ]
}
```

這是格式示意，不能把示例條號或示例 hash 直接放入 repo。
條文 hash 用 `axiom_matrix.parse_clauses()` 回傳的完整 body，以 LF 正規化、
去尾端空白後的 UTF-8 bytes 計算；不得取另一條、摘要或只有標題。
更改條文後必須重讀並重新判定，不是只機械更新 hash。

證據一筆需要 `kind`、`path`、`anchor`、`source_sha256`。
`kind` 為 implementation／test／mutation／unsupported／context；錨點必須在該檔
恰好一次。`source_sha256` 是整個來源檔 CRLF→LF 後的 SHA-256。
`implemented`、`partial` 必須有真正 implementation 證據；用來說明「舊能力不能替代」
的位置要標 context 或 unsupported。`unimplemented` 必須有 scoped absence 證據，
不可同時說該條已有 implementation。

不安全路徑、symlink、未知欄位、重複 JSON key、缺失或不唯一錨點都拒絕。
錨點還在但來源 bytes 改變時，保留原判定作歷史，當次有效判定退回待審。
findings 的已修裁定也使用同樣的來源失效原則，並以 `clause_sha256` 綁定各條文版本；
條文已變時，即使狀態標記已重審，也不能默默沿用舊 finding。報告來源 hash 包含被引用的證據檔，
即使該檔不在自動候選掃描範圍內。

## 掃描範圍與限制

自動掃描 current_geometry.c、根目錄場景、geometry-core、geometry-app、
geometry-templates、geometry-web、tests 的 C／header／inc／Python／JS／HTML／scene。
排除 vendor、node_modules、evidence、release-evidence、cache 與 geometry-web/docs。
排除範圍與實際掃描檔數會寫入報告。人工證據可以指向安全的 repo 內文件，另入來源閉包。

Git checkout 取 tracked 加未忽略的新來源；稀疏 checkout 缺了應掃的來源會紅，
不把缺檔當「沒有實作」。匯出樹按實體檔掃描，報告明寫 `filesystem-export`。
Python 方法名取 AST，JS 名稱只保守辨識字面 test/it 與 braced callback；不明確時
只保留檔案／行號。場景與 `run_tests.TESTS` 的登錄連結由靜態語法解析得到。

不執行產品程式，不讀取憑證，不讀網路，不匯入任意測試模組。
此工具不驗任意自然語言與程式的語義等價、不推斷測試曾執行、不驗 mutation 收據真偽。
正式收據仍由原本 Mutation evidence workflow 產生；既有架構產生物同樣由正式流程重生。

## 本片的測試與採入

新 `py:test_axiom_traceability` 的 suite fragment 由 `tests/native_registry.py --init-suite`
產生。交付時是 `pending-ci-census`，不手填計數或成本。套用者先推候選，再派發
`Native suite measurement`，由可下載官方 artifact 的人用 `--import-suite` 採入原件。
正式六片仍須通過；本機量測不等於 acceptance。

```sh
python3 -B tests/run_all.py --build --measure-suite py:test_axiom_traceability --report /tmp/x4-native-measurement.json
python3 -B tests/diagnostics/x4_axiom_withdrawals.py --out /tmp/x4-withdrawals
```

odd-gap 觀測新增八條引用正式格線的 guide。獨立算式是
`400 + floor(21 / 2) + k * (400 + 21)`，`k = 0..7`；不直接塞座標給 guide。
既有 30 秒場景裁判及接受／拒絕方向不變。幾何撤回 floor→ceil 應在精確端點紅。
三個 scene 說明的條號變動會影響正典 reader 的追溯內容，必須用原 generator 重生：

```sh
python3 geometry-guide/sync_axiom_reader.py
python3 geometry-guide/sync_axiom_reader.py --check
python3 tests/test_axiom_reader.py
```

不建立第二個 reader，也不手改 HTML。首次 source marker／報告不能替代原有 reader gate。
本片修改 `run_tests.py` 及場景，所以既有 core mutation oracle 指紋會變；不能沿用舊 killed
狀態充作本片的正式證據。套用端需重跑 Mutation evidence workflow，並重新產架構原件。
