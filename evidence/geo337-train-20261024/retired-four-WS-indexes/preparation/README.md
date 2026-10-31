# 四份退役 WS index cache 的完整保全（尚未執行）

只限 PLAN.json 中 R5、R6、L reading-A、已退役 F9 reader 四個獨立 OWN checkout 的 `.git/index`。現有四份完整內容共 23,386,440 B、實體配置 23,400,448 B；原 16 條唯讀 Git 命令已保存，HEAD 各自固定、cached diff 全空、三棵樹 clean、reader 只保先前已批准的三個 D。四個 gitdir 與 index inode 均獨立，nlink=1。只列候選，尚未回收任何 bytes。

`archive_indexes.py` **沒有 unlink／移除功能**。預設只讀固定 PLAN/request 後列未執行狀態；只有 root 於 request 綁定三個 true 租約和獨立 peer，並加 `--execute-archive`，才在既有 OWN SHM root 下建立新 archive 目錄。原 helper c387/c51 精確 pin，所有真正 SHM 操作只由 root 的正式 require_escalated 執行。

真執前／逐檔／結束均檢原四個 index bytes/hash/regular/nlink1、gitdir inode、HEAD、空 staged diff、精確原 worktree status（含 reader 三 D）、refs 與其餘 Git metadata。不得有 Git lock；原 consumer helper 只檢可讀 cwd/exe/cmdline/fd，限制照錄，root 的無活躍使用租約補足排程責任。任何變動即拒絕，既有 index 仍完整留在原處。

每份完整 index 以 deterministic gzip 保存到 SHM，檔案 fsync、解壓逐 byte 和 SHA256 roundtrip、目錄 fsync；記 uid/gid/mode/mtime/atime/ctime/inode/nlink/xattrs、原 Git 流與完整來源/原終態收據 pins。index inode/bytes、sources、dirty、fixtures、receipts、refs、objects全部原地保留。預估 gzip 輸出不足原 23.4MB，但不是已測壓縮率；root 將原大小＋小 metadata 納共同 SHM 2GiB/freshRAM 准入，不新增產品門檻。

## root 的具體後續動作

1. 獨立 peer 接受精確 executor 後，複製 `REQUEST.root-lease-false.json` 至新 root request；只綁三 true、peer path/hash 與唯一新 out，不改 PLAN/工具。
2. 以原 capture 包 `python3 -B .../archive_indexes.py --request ROOT_REQUEST --request-sha256 EXACT --execute-archive`，require_escalated 執行。此步只完整封存，不回收空間。
3. 收 `RESULT.json exit_code=0`、四 gzip 完整 roundtrip 和前後原 metadata；正常 push 所有 gzip 與完整 archive manifest／request／Git/consumer原流，再逐遠端 blob 下載核完整 size/SHA256/GitOID。SHM 是揮發性，不以本地 gzip 宣稱持久交付。
4. **只有上述遠端真0後**，root 才另授權、另綁精確四檔解除。該獨立一步必重新核原 index 身分/bytes/完整原 worktree差異、無新 staged/refs/consumer/lock，journal before→unlink→actual-after。任何失敗保留已發生狀態，不覆寫或回滾其他檔。本工具不能執行這一步。
5. 四根改標 `INACTIVE_REQUIRE_INDEX_RESTORE`，禁止任何剩餘 gate 或普通 Git status 直接使用；branch refs、objects、其餘 Git metadata 與所有工作樹保持。原 25MiB WS source guard 不降，真解除後 fresh df 再判斷；23.4MB 是候選實體量，尚非實際淨回收。

## 有需要時如何恢復

只由 root 另授權恢復，不是本輪自動動作：先從已驗遠端完整 gzip 取回、驗其 blob SHA256/size 及 index 原 SHA256。確認四根仍 inactive、index 不存在、無 consumer/Git locks、HEAD/refs/其他 Git metadata 和原差異沒有改變。解壓到同 `.git` 下唯一新檔（O_EXCL，不能覆蓋），驗原 bytes/hash，恢復可還原 uid/gid/mode/xattrs/mtime/atime，fsync。以不覆蓋既有目的地的原子建立方式恢復 `index`，fsync gitdir；再以 GIT_OPTIONAL_LOCKS=0 驗 HEAD/空 staged/精確原 status（reader 三個 D 仍要存在）和 refs。inode/ctime 會重新產生，必記新 metadata，**不得宣稱原物理身分完全恢復**。未全部恢復驗證前不可解除 inactive 標記。
