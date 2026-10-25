# F9 assembly 兩次終態完整收件準備

固定來源 `4f8a794f4167c3562eb182045102e86e9e37cca9`。首次 host 73905 真 exit 1；重跑 host 3123 真 exit 0。只準備工具；尚未執行收件、未重跑任何產品。

root 使用正式 `require_escalated` 執行 `launch_collection.py --peer <獨審REVIEW.json> --peer-sha256 <pin> --execute-root-approved`。工具預設只輸出 PLAN；命令列旗標不能代替 OS 批准。主代理必須先確認兩次均已終態、共用 assembly sourceplan 不再新增 guard。外層用原 c387 記錄真 argv／exit／完整 stdout、stderr、環境與 SHA。靜審收據須帶 `exit_code: 0`、`collector_sha256`、`launcher_sha256`。

來源為兩次完整 launch、storage、sampler 目錄，共用 sourceplan、原 host plan/materialize 全流、原工具及既有獨審；所有 regular bytes、symlink targets 全收，不排 ELF／cache／profile／screens／diagnostic。Unix socket 只記 metadata（沒有可序列化 regular payload），不跟隨 symlink。sourceplan 的 Gitdir metadata 及 mutable GUARD_LATEST 只封存身分雜湊；完整已結束 guard logs 仍收。seed/source payload 不拷貝、不刪除。原 host FINAL 的原始 bytes 一起入包。

沿既有 canvas collector 的 16 MiB 分組、gzip level 1、header／deflate 保守上界、每包 fresh 64 MiB reserve、來源前中後 hash/stat 與全 tar member roundtrip。單一大於 16 MiB 的原件獨占一包，仍以完整未壓縮大小計算准入，不截斷或省略；16 MiB 是封包大小規劃，沒有新產品門檻。每包都保存實際 budget。另檢查原目錄 leaf set 沒有新增或消失。固定 2 MiB metadata reserve，超額會如實失敗，原件和部分封包全保。

收件驗證兩次 host→sampler→launcher→workflow 的原始 exit 鏈、原 15 分鐘 gate／3 倍 watchdog、原 before/after guards、reaper 真終態、source/request/tool 身分；接受首次真紅作歷史，不把它改綠。這是既有結果的封存，不重新判產品 assertion／golden；需要另一位代理獨立核實真正封包後才出版。

輸出只在既有 task SHM root 的兩個 fresh OWN 目錄。SHM volatile，所有檔案受保護，不刪 raw／fixtures／Git objects。`delivered` 固定 false：一般 push 以及 GitHub API 原始 blob 逐 bytes/hash 驗證成功以前，不算持久交付。此工具不操作任何 Git refs、index、branch 或 API。
