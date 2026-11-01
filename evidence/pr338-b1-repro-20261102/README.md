# #338 R8 精確可重現建置

2026-11-02 使用者新指示取代先前「不得重建」限制：原雲端 `/tmp/g337323R8` 已消失，按原件遺失處理；可在 GitHub CI 以原來源、編譯器、旗標、角色與路徑重建。若三支完整 SHA256 與原 pin 完全相同，即同份 bytes，可用來執行既定 whole-memo；不同時須明列差異，交 ChatGPT／dot 判斷替代結案方式，不能冒稱原件或自行解除 B1。[本機 Claude 技術協調留言](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6561758863)。

工作流程限定 helper branch `codex/pr338-r8-repro-20261102` 的 push，不新增 PR、不取消 #338 正在跑的七項。所有 build 僅在 GitHub CI，禁止本機 build／ELF 執行／WSL；腳本也檢查 `GITHUB_ACTIONS=true`。

原 R8 `receipt.json` 與三份 `work/*/build.json` 已封存在原 tar：gcc `Debian 14.2.0-19`、binutils／gprof `2.44`、平台標籤 `glibc2.41`。原件沒有完整 libc／CRT／libgcc／ld 的 package 版本或檔案 hash，因此不能先保證重建相同；本 CI 會補記實際 package、compiler specs、CRT 等檔案 hash 與 Docker image digest。Debian trixie 是首輪重現環境，結果以完整三 hash 為準。

來源 bytes／行尾直接從核過 hash 的原 R8 tar 還原：base-pg 使用原固定 BASE `b74f9a2ae7ade1555b9be45283adecc097fb76e3`，fix 與 trace 使用 F8 `75a1e93811a52b69385cbdaf6a09d773ed9052ad` 及其原 trace overlay。三個 lexical quoted-include closure 先驗 184／185／185 檔與獨立靜態雜湊，再按原 `build.json` 命令與絕對 cwd 建置。

`RESULT.json` 保存三組原期望與完整重建 bytes／SHA256／mode、真 compile exit 及原流。`REPRODUCED_ELFS.tar` 保留重建 ELF 與 mode；只有三支 bytes、SHA 與完整 mode 全符，重現程式才真 exit 0。不同為真 exit 1，前提／環境失敗為真 exit 2。此工作不執行重建 ELF、不重抽 R8、不執行 whole-memo；正式反證及 B1 最後解除仍另列，原 R8 overall exit 1 保留。
