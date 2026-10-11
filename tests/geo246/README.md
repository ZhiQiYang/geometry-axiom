GEO-246 的可重現入口。以下在 WSL 的乾淨 exact-head checkout 執行；不修改公理或閱讀器，不停用 SAC，不替換使用者服務。這是 Codex 實作驗證，不能冒充另一位 agent 的【WSL 裁判】核准。

```bash
head=$(git rev-parse HEAD)
checkout=/tmp/geo246-review-source
# 在本工單自己的 Linux clone 上建立 detached checkout；不要 checkout 他人的分支。
git worktree add --detach "$checkout" "$head"
wrapper="$checkout/tests/geo246/isolated_wsl.sh"
output=/tmp/geo246-review-native
unshare --mount --propagation private bash "$wrapper" "$checkout" "$output" python3 tests/binaries.py build
unshare --mount --propagation private bash "$wrapper" "$checkout" "$output" python3 tests/geo246/message_mutation.py --out "$output/audit"
```

`generic_messages.json` 是四個訊息出口的完整退化 patch。字串使用 LF 表示；apply 程式以二進位讀寫，依每個檔案的既有 LF／CRLF 精確替換，要求每個錨點只出現一次。突變只在 `git archive HEAD` 的 disposable source 內進行，原 checkout 不被 patch；四份 archive 來源也在執行 generic bridge 前逐位元組還原。compile argv/cwd、archive head/tree/SHA、patch SHA、binary 與原 checkout 前後身分全記入 audit。原 32 筆及新增 panel 7 筆分別驗 baseline／generic／restored。

archive 只匯出 `current_geometry.c`、`geometry-core/` 與 `geometry-web/web_bridge.c` 的 exact-HEAD blob，編譯器會驗證 include 可完整解析；不複製無關的大型閱讀器及媒體。匯出路徑明記於 compile receipt。

原生變異帳本使用原工具，分組只為避免結果檔互撞：

```bash
unshare --mount --propagation private bash "$wrapper" "$checkout" "$output" python3 tests/geo246/refresh_mutants.py --out "$output/mutation-batches"
# 完成後以原 mutate.py --check 核對；此命令會重寫該隔離 checkout 的帳本。
```

帳本產生後，將結果回存本工單分支並提交，再建立新 final head 的乾淨 checkout 跑以下七 job；不得將已改帳本的髒 checkout 冒充 exact head。

七個 workflow job 的本機入口（各 job 使用不同 output，browser 最多同時兩個）：

```bash
for job in native assembly documents grid canvas space timber; do
  output="/tmp/geo246-review-$job"
  unshare --mount --propagation private bash "$wrapper" "$checkout" "$output" python3 tests/geo246/ci_job.py "$job" --out "$output/receipt"
done
```

wrapper 預設 stack 16384 KiB，與 workflow 相同。`python` 是各 job 暫存 PATH 內指向 `/usr/bin/python3` 的別名。output/native 只在 private mount namespace 映射到 `/tmp/geometry-tests`；Chrome、服務、回報、screenshots 都使用 job 自己的暫存目錄與空閒 port。沒有 pytest/test scope 放行、沒有調低 expected、沒有把局部結果相加成完整 pass。

WSL 本機 native wall-time 預設容許 1800 秒，以便保留完整失敗收據；CI budget 為 900 秒，`job.json` 明記是否超過，超過不得宣稱 CI pass。browser budget 與 matrix 的 10／15／20／35 分鐘相同。Chrome 與 CJK fonts 必須已存在，缺少即失敗，不修改系統套件或安全設定。

`identity.py` 分開記錄 raw checkout bytes、Git blob bytes 與各自 CRLF→LF 正規化 SHA-256，並記錄 HEAD、tree、checkout、tracked diff、executor 與 binary fingerprint sidecar。raw hash 不直接冒充 Git blob hash；特別是 Windows 簽出的 `.inc` 可能為 CRLF，Git blob 為 LF。`current_geometry.c` 必須保持原本統一 CRLF。

對親代閱讀器的比較只可聲稱實際收據所證明的範圍：例如失敗名稱相同。reader suite 不需要 native binary，身分收據必須明記此範圍；不得稱為全文逐位元組相同或完整 base/head 產品驗收。

```bash
python3 tests/geo246/parent_reader.py --checkout /tmp/geo246-parent --head 7b603b4dc34bbbf41731f0e7845d0519dd876c71 --out /tmp/geo246-parent-review
```

親代 checkout 必須是自己的 detached worktree；腳本會要求指定完整 HEAD、乾淨 tracked diff，記錄 tree、來源與執行器 SHA，並驗證執行前後身分相同。
