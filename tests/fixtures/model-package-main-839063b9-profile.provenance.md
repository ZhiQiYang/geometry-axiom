# 整卡引用採納前 main 的斷面建模交換包

產生者固定為 main `839063b9eecbd3592f48cab5ea74f306cacc5fa3` 的
`git archive` 獨立目錄；使用該版未修改的 `modeling.build_package`、
`tests.test_section_profile_modeling.scene()` 與 `request()`。
definitions 為 `{"base_scene": scene(), "extensions": []}`，與既有
`model-package-main-d1db88ae-profile.json` 的產生方式相同。
來源包含一個 L 斷面、三支角材構件及一個 2400 mm 拉伸件；結果為三個材料網格與一個參考包絡。

產生者用自己的 C adapter 與 `verify_package` 重驗整包相等後，直接寫入
`modeling.common.canonical_bytes(package)`。未改寫任何 manifest 欄位或幾何。
adapter 由該獨立目錄的原始 `modeling.base._build_adapter` 以
`cc -std=c11 -O2 geometry-core/model_base.c -lm` 編到私人暫存目錄；
不借用其他分支的 adapter。執行前設 `ulimit -s 16384`。

- 產生者 head：`839063b9eecbd3592f48cab5ea74f306cacc5fa3`。
- 產生者公理 revision：`651c661b2c4c224c58bb4a2ed0a42ed929a16aa6`。
- 產生者 LF 公理 SHA-256：`ab31dc36d5416762ac44932940a94f6142b72e831ceb62c0bc67375512109004`。
- 夾具大小：35777 bytes。
- 夾具 SHA-256：`c83643807a10bf580998508ffff0dd45a99d594a97183242ea30bb56359e34aa`。
- 產生與同版整包重驗：exit 0。

在上述固定版本的獨立目錄重現（將輸出路徑指定為夾具路徑）：

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / "geometry-core"))
from modeling import build_package, verify_package
from modeling.common import canonical_bytes
from tests.test_section_profile_modeling import scene, request

package = build_package({"base_scene": scene(), "extensions": []}, request())
assert verify_package(package) == package
Path("model-package-main-839063b9-profile.json").write_bytes(canonical_bytes(package))
```

## 提交 B 的相容驗證

`AXIOM_REVISION` 指向已提交條文來源 A
`b3c79615d0cde89bbdca72c1223d214324bc5f8f`；它實際包含新條文，符合
MODELING-CONTRACT 的來源 Git SHA 定義，也沿用 Q38j 後續 pin 到已提交來源的做法。
新 LF SHA-256 為 `e5e43ec5da2030669c9ecd7a67f8b250cfb7290cf663365b2b66c51814bb77b9`。
本次版本更新不宣告執行器已實作 `grid-card-reference/1`。

- 新具名重開測試在修正前失敗：`UNSUPPORTED/AXIOM_VERSION (I32)`，exit 1。
- 修正後相容 suite：31 tests，OK，exit 0。既有 29 題均保留。
- 重建以整包相等斷言證明只有 `manifest.axiom_revision` 與
  `manifest.axiom_sha256` 改變；原輸入包保持不變。
- 新拒絕測試涵蓋 7 組未知／混搭 revision 與 hash，均要求 `AXIOM_VERSION`。
- 實際撤去 `PRE_CARD_REFERENCE_AXIOM_VERSIONS` 的唯一配對，保留其餘實作，
  重開測試具名轉紅：`released pre-card-reference package must reopen and rebuild:
  UNSUPPORTED/AXIOM_VERSION (I32)`，exit 1。
  然後逐 byte 還原原始碼，同一測試恢復綠燈，exit 0。

完整雲端驗證（2026-10-15 UTC）：

- `ulimit -s 16384; python tests/run_all.py --build`：88 suites，
  2828 個有計數項目，2827 pass / 0 fail / 1 skip，exit 0；
  suite 耗時合計 440.2 秒，全部數量與 expected 相符。
  唯一 skip 是既有具名允許清單的 Windows GDI harness，沒有新增 skip。
- 同次完整跑的相容 suite：31/31，2.64 秒；原閱讀器 suite：41/41，118.37 秒。
- `python geometry-guide/sync_axiom_reader.py --check`：exit 0，207 條，
  five_asserts / independent_ssot pass，patches 0。
- 範圍機械核對：提交 A 的全部 9 個檔案逐 byte 未變；
  `verify_package` 新表恰好用於 7 處判斷；expected 只改相容 suite 29→31。
- 環境：Linux 6.18.44、GCC 14.2.0、Python 3.12.14、Node 24.19.0，
  native stack 16384 KiB。

雲端 native,非正式 WSL 收據。正式 WSL 七項與真瀏覽器／owner 整合未驗，
由本機列車另驗。請 Claude 核對。
