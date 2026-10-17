# GEO-261 採納前 main 的模型包原件

這組原件由 main `a898ad6e12707104568679591fe1b21804bfc3df` 的獨立
`git archive` 目錄產生。使用該版本自己的未修改 `modeling.build_package`、
`verify_package`、C model-base adapter 與測試來源 helper。
沒有改寫包內 manifest、來源、能力、幾何或 diagnostics。

- Producer 的公理 revision：`b3c79615d0cde89bbdca72c1223d214324bc5f8f`。
- 公理 LF SHA-256：`e5e43ec5da2030669c9ecd7a67f8b250cfb7290cf663365b2b66c51814bb77b9`。
- Producer script SHA-256：`c25f6f2cee855800a0d7fccffcd8e3ef11923fcf6cd68235570373fc1a21a7f3`。
- Producer adapter SHA-256：`b0daf7d6136365f04f6b6ff5074e7ba91679c4fb3e8748d3ebaedde082cdb7a1`。
- `producer-receipt.json` 原始 SHA-256：`4660414637141df3cfa8da3c392bb17ae33b7c96ff1c35eb8b86827d0eb707e1`。

`producer.py` 是實際執行的 script 原件。每個成功包先由同版真執行器
`verify_package(package) == package` 重驗，再直接保存 `canonical_bytes(package)`。
同時保留該次輸入的 `.input.json`。收據列出每份原件的 bytes、SHA-256
及 producer 使用的來源模組 SHA-256。此目錄的 `.gitattributes` 停用
Git 行尾轉換，避免 Windows 簽出改寫收據或 script 的原始 bytes。

## 覆蓋範圍

| 原件 | 實際來源／獨立幾何預期 |
|---|---|
| `profile.json` | L 斷面、三支材料構件、2400 mm 拉伸件；三份材料體積各 2138400 mm³，參考包絡 84960000 mm³ |
| `finite-grid.json` | 保留有限網格來源及 `from-system` 引用；有孔牆體拉伸體積 1171200000 mm³ |
| `infinite-grid.json` | 保留孔與頂點鍵、負格索引 `-2,1`、分數錨點及 `from-binding` 引用；同一有孔牆體體積 |
| `stagger.json` | 保留相位差 400、負 band `-1` 及實際角材引用；材料體積 1746360 mm³，Y 範圍 1817–1844 |
| `parameter.json` | `v repeat 0 param:1:1` 保留參數卡及精確 1830 mm 定義，該參數實際決定角材線位；同上材料體積及 Y 範圍 |
| `subdivision-rejected.json` | 原始含來源子規則的 input，以及同版真實 `UNSUPPORTED / CAPABILITY / I32` 拒絕；不是成功模型包 |

來源子規則雖有正式條文，這個模型執行器並未實作
`grid-subdivision-rules/1`。GEO-261 必須保留此拒絕，不能為了讓相容性
案例通過而新增能力、刪來源或保存沒有求值的成功包。

`historical-versions.json` 凍結 producer 的 16 個歷史集合、19 組精確
revision/hash 配對，包括 `PRE_CARD_REFERENCE_AXIOM_VERSIONS`。
`model-contract.json` 凍結原 SCHEMA、PROFILE、GENERATOR、CAPABILITIES。
這兩份只是版本／能力基準資料，不是幾何驗證的替代品。

## 生產驗證

2026-10-16 00:37:08–00:37:20 UTC，在既有 WSL shared lock 內執行。
producer exit 0；五個 build 與五個同版 verify 均成功；來源子規則依
既有能力拒絕。baseline 的 model-base 與 bridge 在執行前後均為 fresh。
獨立 baseline 的 15784 檔案來源清冊執行前後相同，SHA-256 為
`cdc20cc15d7885ac9b11c7c68963ab56a0b45f221fd9483e19a89c380ec99fb3`。

原始 log：`D:/geometry-axiom-work/geo261-evidence/p1/producer-retry-v2/producer.log`，
SHA-256 `d374318e8e5a896d79fd2794bcc6ac0b2a116eb557d74a84a1f70eff5248ab52`。
同目錄 `summary.json` 保存執行命令、來源清冊與 adapter freshness 收據。

前一次 v3 執行已成功生成及重驗所有模型，最後寫歷史版本收據時，
Python tuple 被只接受 JSON array 的 canonicalizer 拒絕。v4 只把
歷史配對轉為 JSON arrays，另用全新輸出目錄重跑；五個模型包、五個
輸入與來源子規則拒絕原件共 11 檔均與 v3 逐 byte 相等。
v3 半成品與失敗 log 保存在 repo 外，沒有覆寫或冒充完整收據。

## 重現與候選驗證

在上述固定 baseline、其自身 fresh adapter 及既有共享鎖內執行：

```text
python3 producer.py --root <a898ad6e-baseline> --base <baseline-model-base> --out <new-directory>
```

輸出目錄必須不存在；不能用新 writer 重建後覆蓋這些舊原件。
`tests/test_domain_decoupling_compatibility.py` 以原件進行新 executor 的
真重建，只准新回傳包的兩個公理版本欄位改變；輸入包 bytes 及其餘
整包欄位均須保持。另驗六道年代閘門、未知／混搭版本拒絕、所有既有
歷史配對，以及重算 hash 仍不可通過的來源／幾何造假。

本節的 producer 成功不等於候選版本驗證完成。候選 suite 與七道
guard-removal 突變證據須在正式採納 A/B 提交完成後另跑並記錄；
此組模型包也不宣稱涵蓋所有 `.gcanvas` 或真瀏覽器重開流程。
