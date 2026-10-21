# footprint 正向與精確撤回證據

正向分支 `codex/geo261-p189-host-copy-trial-20261021`，完整 SHA `6c6937708fa31790586d6c31c2984070e6bf885a`，parent `75f587a5e96dbd1460cf1d9be781ca6fa06fd993`。負控制分支 `codex/geo261-p189-footprint-revert-control-20261021`，完整 SHA `4bd19f91c434417f1c4431128c55285f4b11d3c3`，parent 為正向 commit；只將 reference_sources.inc、world_validation.inc、placement_sources.c 三個產品檔精確還原為 85dc4fff44ce49b27f831b21cbdcb662c863302c 原 bytes。全部新 tests 的 Git tree 與正向相同。

兩輪皆用固定 main/base、原 runner/gen/calibration、16MiB、900 秒與原 ≤2x 門檻；每輪一套 36 樣本。正向 check 0；負控 gen、16 controls、build、175 equivalence、timing 全 0，只有 N64 ratio=2.5145334005684763 使 check／supervisor／頂層真碼 1。因此此次精確撤回性能負控 killed，沒有用歷史紅取代，也沒有補抽。每輪 175 列含 75 成功 load 和 100 歷史受控拒絕；實際三方 stdout 均相同。完整兩包由 linked-bundles 綁定，原 bytes 及兩包 manifest 已再次核對。

正向 ratios：N16 0.9535009546275699、N32 1.1888327560162852、N48 1.59489983989876、N64 1.557847502710642。兩輪依序執行，主線 median 也有波動；此證據自證門檻能偵測精確撤回，不據跨輪差值宣稱精確改善百分比或個別 H/K/footprint 歸因。負控未跑新 tests（private 錨點預期不相容），只跑上述原 P-189。候選仍非正式 L2/full7／全量帳本／架構驗收。

targeted 保存 footprint 的 56 個定向測試、20 個 H 具名控制、299 命令／598 原流與 peer。這個來源沒有新 sanitizer 收據，不將 75f 的四個局部 sanitizer 案冒稱為本次實跑。詳見 outer-receipts/footprint-package-source-review.json。

摘要首敗 ae4781/1 的原碼在 summarize-first-attempt.txt，traceback 僅在完成紀錄中事後轉錄；提交預檢格式誤判 accb1f/1 及後續非 Git 樹錯誤 f0e91a/128 由 JSON 記錄，沒有獨立完整 raw transport。它們均保留，不造出缺少的原流。成功 local-commit.json 的九個命令含 stdout/stderr 且皆 0；提交前摘要與後來固定 commit 的時間差依原文保留。

pair-preparation 保留兩來源準備、負控 restore／commit 的實際 argv、真碼、原 bytes/hash 與 clean 核對。未執行待命計畫亦保留，不能將計畫冒稱執行。外層保存只讀核對與封包碼；各層的事後頂層工具轉錄都維持其分類。ELF/archive/來源整樹不進此包；.py.txt 等僅是原 bytes 純文字資料，不新增正式入口。

最不確定的是後續正式來源／環境的性能代表性及完整驗收狀態。本包封裝沒有新增產品執行，原有 L／75f／更早紅綠子包均未改。SHA256SUMS 涵蓋除自身外全部檔案。
