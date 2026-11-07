# R17 採納前 main 的真實建模交換包

三份 JSON 都由乾淨的固定 main `343a8abe83029dd883e5e5b1b8e3112411fefe81`
自行產生；不是修改舊夾具的 manifest 冒充新來源。

產生者執行器宣告的公理配對為：

- revision：`0fd8cacf799ed6ddf0fa7588243aa4e4bbb94c18`。
- 公理 LF SHA-256：`c66c48e50e0caceef42721c79700365f090f5c48d297abba41993eeb40dba9b7`。
- 該版公理 blob：`bac4c5ef1fa7d64e54d1aa81ecdf8efd1636cdff`。

`generate.py` 先核對產生者 HEAD 及全部已追蹤檔未變，再清除外部
`GEOMETRY_MODEL_BASE` 覆寫，呼叫產生者自己的 `_build_adapter()`。
adapter 使用產生者自己的原始碼與 include 閉包，以其原來的編譯入口建立。
三份包都先經同版 `verify_package` 真實重建，斷言輸入未變且重建結果整包相等，
才把 `canonical_bytes(package)` 原樣寫出；沒有手改任何版本、來源、幾何或能力欄位。
最後再次核對產生者的已追蹤檔未變。

| 夾具 | 輸入來源 | bytes | SHA-256 |
|---|---|---:|---|
| `profile.json` | 同版 `tests.test_section_profile_modeling.scene()`／`request()`；L 斷面、三構件與 2400 mm 拉伸件 | 35777 | `fdb8bac718acb0534ec37fa30b4c86ec8a0336d430f9984bb9993ce65a0e84fb` |
| `stagger.json` | 同版 `StaggerModelCompatibility().build()`；v 軸 `stagger 400`、band 0、來源網格與角材 | 3962 | `aea91c046bee429c4b04fef724c3f27754949059bc1ef58c2f74f73a25fabf66` |
| `card.json` | 同版 `EngineeringModelCompatibility().card_reference_package()`；參數卡 10、欄位 3／8 與整卡引用 | 14935 | `98a0b5b927ff56afe06d722ffd932ca193db9f81b1c24b8dce1d627f4e370952` |

重現方式：將固定來源 checkout 到獨立乾淨目錄，從採納工作樹執行以下命令。
輸出目錄須指定新的空目錄，以免覆蓋本組已釘住的夾具。

```sh
ulimit -s 16384
python3 -B tests/fixtures/r17-main-343a8abe/generate.py /path/to/clean-main-343a8abe /path/to/new-output
```

2026-11-06 實際產生與同版重驗：exit 0，最後輸出
`producer verify: all checks passed`。實際環境與原始產生收據在
`producer-receipt.json`；Python 3.12.14、GCC 13.3.0、Linux、stack 16 MiB。
這是雲端 Linux 實測，不冒稱 GitHub CI 或本機 WSL 收據。

用途：R17 只採納規範，模型執行器的支援能力與套件格式不升級。
舊包重開必須保留完整定義、來源引用、幾何、能力與診斷，僅輸出包的兩個公理
版本欄位換成已核可新配對；輸入包本身不得改寫。未知或交叉配對仍拒絕，
新 `boundary-pair/1` 能力及未支援語法仍拒絕，不能把條文採納當作產品完成。
