# #338 R8 精確可重現建置

2026-11-02 使用者新指示取代先前「不得重建」限制：原雲端 `/tmp/g337323R8` 已消失，按原件遺失處理；可在 GitHub CI 以原來源、編譯器、旗標、角色與路徑重建。若三支完整 SHA256 與原 pin 完全相同，即同份 bytes，可用來執行既定 whole-memo；不同時須明列差異，交 ChatGPT／dot 判斷替代結案方式，不能冒稱原件或自行解除 B1。[本機 Claude 技術協調留言](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6561758863)。

工作流程限定 helper branch `codex/pr338-r8-repro-20261102` 的 push，不新增 PR、不取消 #338 正在跑的七項。所有 build 僅在 GitHub CI，禁止本機 build／ELF 執行／WSL；腳本也檢查 `GITHUB_ACTIONS=true`。

原 R8 `receipt.json` 與三份 `work/*/build.json` 已封存在原 tar：gcc `Debian 14.2.0-19`、binutils／gprof `2.44`、平台標籤 `glibc2.41`。原件沒有完整 libc／CRT／libgcc／ld 的 package 版本或檔案 hash，因此不能先保證重建相同；本 CI 會補記實際 package、compiler specs、CRT 等檔案 hash 與 Docker image digest。Debian trixie 是首輪重現環境，結果以完整三 hash 為準。

來源 bytes／行尾直接從核過 hash 的原 R8 tar 還原：base-pg 使用原固定 BASE `b74f9a2ae7ade1555b9be45283adecc097fb76e3`，fix 與 trace 使用 F8 `75a1e93811a52b69385cbdaf6a09d773ed9052ad` 及其原 trace overlay。三個 lexical quoted-include closure 先驗 184／185／185 檔與獨立靜態雜湊，再按原 `build.json` 命令與絕對 cwd 建置。

`RESULT.json` 保存三組原期望與完整重建 bytes／SHA256／mode、真 compile exit 及原流。`REPRODUCED_ELFS.tar` 保留重建 ELF 與 mode；只有三支 bytes、SHA 與完整 mode 全符，重現程式才真 exit 0。不同為真 exit 1，前提／環境失敗為真 exit 2。此工作不執行重建 ELF、不重抽 R8、不執行 whole-memo；正式反證及 B1 最後解除仍另列，原 R8 overall exit 1 保留。

## 已取得精確 bytes，接續正式反證

首輪完整 helper `4fd903cde1f591f927baa44c15ccf0eab0f81a02` 的 [run 41335297693](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41335297693) 已真 exit 0；三 ELF 的原完整 SHA／bytes／mode 全符。[artifact 13094439575](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41335297693/artifacts/13094439575) 為 3,520,689 bytes，ZIP SHA256 `d8a74b21a3466e2d463fec354ea03856410e108f7af64e412289e701e2da70b3`。第二位 agent 靜態讀回三 ELF 及 manifest 72 項，零差異，沒有執行 ELF。

後續 `whole-memo-formal` 以重現 job 成功為前提，取其精確 hash artifact、恢復原 R8 receipt／streams／scene inputs，另建乾淨可寫 F8 Git checkout，執行**逐 byte 未改**的原 `memo-copy-v2/tools/run.py --phase all`。原六份工具硬 pin 先逐一驗明。V3 `verify_linux.py` 由已封存 V4 逆回原 scene 列舉的一行，**完整 SHA 精確命中原 pin** `ccbce3a5d32bee81f22be31a31c1f771ca05c54f53f21e4d94b11b4a08b4534d`（11,227 bytes），保存在 `frozen-tools/verify_linux.v3.py`；沒有產生新的裁判行為。

隨後又從真正舊原件找回相同 V3 bytes：`geo323-full-originals/geo323-F64-completed-raw.part-001.tar.gz` 的 `v3-original-scene-guard/tools-frozen/verify_linux.py`。該原 tar 為 11,489,504 bytes、SHA256 `32585561cd7bc639f083aa85b648ac9e66d7d67f55399f28a7e48fe911906585`，工具 bytes 與上述逆回結果全等；`FROZEN_TOOL_PROVENANCE.json` 保存來源。因此正式用的是可對回原封存工具的同份 bytes。

原 driver 的 baseline 是既有 R8 profile exit 0／原有效 criterion，之後實跑 withdrawn=1、restored=0、isolated 175／350 ABC=0；不能把缺件查核或 metadata proof 當這三 phase 的終態。本工作保留原 R8 overall 1，不重抽 36 timing 樣本。`CI_RESULT.json` 保存正式 driver 真 process exit、原 phase 終態及來源；`CURRENT_PRODUCT_INPUT_CLOSURE.json` 逐 byte 核 F8／目前 #338 `9230a3dc04233e50c0bf97141a7fbe692828b2ca` 的 185 編譯輸入與原場景，並列實際非 evidence 差異及原工具 hash。是否正式完成以新 CI 原流為準；B1 最後解除仍由審查方判斷。
