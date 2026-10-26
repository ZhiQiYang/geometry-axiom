# recovery evidence append 最小適配

此目錄只備工具，尚未執行 Git 寫入、網路、SHM mutation 或推送。先交另一代理對抗審查，再由 root 以原 c387 recorder 包裝執行。

固定 branch：`codex/train337-recovered-evidence-20261026`。原 canonical writer 的 HEAD／index／train branch 均必須保持 `3e4f2560aa11ed2a626db98ba5ed6f129e791052`。

Root 命令格式：

`python3 -B publish_append.py --execute --manifest <manifest.json> --sha256 <manifest-sha256> --out <fresh-direct-OWN-child> --expected-parent <remote-and-local-full-SHA> --expected-progress-blob <old-progress-Git-blob-OID>`

`--expected-parent` 必須同時等於已存在 recovery 分支的本地與遠端 ref，並是固定 final F `cbf0fb621888596aa14ad5f2349b503e23b1b72d` 的後代；F→parent 不得有非 evidence 改動。這個 anchor 是主代理已採入的確切提交，沒有新增產品差異 allowlist。新 commit 的唯一父提交是該 expected parent。更新本地 ref 採 `git update-ref <ref> <new> <expected-parent>` CAS，遠端採一般 push，不含 force、force-with-lease、rebase 或 main 操作。推送前再驗一次遠端 parent。

所有新檔仍限 `evidence/geo337-train-20261024/`。既有檔案只能覆寫這一個確切路徑：

`evidence/geo337-train-20261024/resume-20261026/PROGRESS.md`

覆寫須明給 `--expected-progress-blob`，並和原 tree 中該檔的 `100644 blob <OID>` 完全相同。未給該 flag 就不能覆寫；其他 PROGRESS、QUESTIONS、收據與任何既有路徑一律拒絕。既有 PROGRESS 的歷史 bytes 保留在 expected-parent 提交；root 另確認正文內容未錯稱驗收通過。只增新證據時可省略該 flag。

保留原 helpers、容量公式（兩 OWN 去重 2 GiB 上限與實際掛載／64 MiB 餘裕）、manifest hash、來源 hash、scope diff、原 writer 快照、全量 remote bytes／SHA256／Git OID 驗證。REMOTE_BLOBS 維持已審 list schema。此次發布可能同含 S10 與 a6 原件，結果明示逐收據來源，不把 publication parent 冒作執行 SHA。

本工具完全不含清理、unlink、rmdir、搬移或任何繞過刪除拒絕的流程。Native 清理被 auto-review 拒絕不影響此工具的邊界；不得以本工具處理任何刪除。
