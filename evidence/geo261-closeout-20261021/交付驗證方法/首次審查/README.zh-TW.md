# E 最終來源綁定的外部準備

固定基底 L=`43f85313c32410ac01406ab585846bbacafea278`。**E 尚未建立，`verify_E.py` 尚未執行**；這裡只有一次性只讀驗證器、review 範本與純資料守門自證。不重跑既有 L 快照，不修改 repo，不啟動產品測試／編譯／瀏覽器。

驗證器 SHA-256：`90bc1d7439e9f412be95e6063a6965b8b4dda3ef164e91b6891a709bba5ec4f2`。正式使用前須先完成所有 L 結果、凍結證據與最終 PR 草稿，再一次生成索引。不能以現在仍成長中的 final-bundle 生成成功交付清單。

## 精確允許範圍

L→E 僅允許新增 `evidence/geo261-closeout-20261021/` 內**外部 review 逐檔明列**的證據，以及修改兩份 Git 設定。每次中間提交也只能碰這份清單，不能藏產品修改再於最終撤回。

`.gitignore` 原 bytes 必須完整保留，只附加以下三行；不附加註解或空行：

```text
!/evidence/geo261-closeout-20261021/
!/evidence/geo261-closeout-20261021/**/build.log
!/evidence/geo261-closeout-20261021/**/server.log
```

`.gitattributes` 同樣只附加這一行：

```text
evidence/geo261-closeout-20261021/** -text -whitespace
```

`-text` 保留原始行尾 bytes；`-whitespace` 避免把原 raw 的尾端空白當產品程式空白問題，不改其他路徑。不得清理 raw 使檢查變綠。如果其他檔案仍被 ignore，驗證器失敗，須回報實際路徑，不能自行泛開白名單。

已從 L 的兩份原檔計算精確範本：

| 檔案 | L 原 bytes／SHA-256 | 精確附加後 bytes／SHA-256 |
|---|---|---|
| `.gitignore` | 2387／`97de5e51029ea529db0afc1e3cbfca6a63b2765478c6591ec29d0e4182a414fe` | 2523／`61d14f759d963051fd0791a71a5d614fa6437c0199f02d61b3c0438e446abd93` |
| `.gitattributes` | 636／`c454be3ab8a233d9b95ac973864582d16efd66b17c2dedc19c91035eacfeeff3` | 691／`aa845af5be856d012d6c767aba9837d2b05ab43abc7fa73736b9bc69d8a699f5` |

這只是記憶體計算後的預期值，沒有寫回主樹。

## 索引與外部 review

證據根的總索引固定為 `artifact-index.json`：

```json
{
  "schema": 1,
  "root": "evidence/geo261-closeout-20261021",
  "selfExcluded": "artifact-index.json",
  "entries": [
    {"path": "相對證據根的路徑", "bytes": 123, "sha256": "64位小寫十六進位"}
  ]
}
```

`entries` 依相對 POSIX 路徑字典序排序，必須是除了索引自身以外的完整集合；路徑不能絕對、越界、含反斜線、控制字元或重複。索引不自含 hash，也不寫 E 的 SHA。

`review-template.json` 的 `files` 目前刻意為空，不能通過驗證。待最終外部證據凍結後，先替每份原件計算 bytes／SHA-256，生成上面的索引，再計算索引自身 bytes／SHA-256；將**包括索引自身**的完整清單填入外部 review 的 `files`，同樣排序。`config` 需維持範本中的前後 bytes／hash 與精確 suffix。最後固定整份 review 原 bytes 的 SHA-256，作為驗證命令的獨立參數。

外部 review 應從凍結的原件生成，再核複製後的 E；不能只從已提交 E 回讀所有檔案後自稱它們與實跑原件相同。總索引本身的 hash 放在外部 review，避免自我雜湊循環。驗證器原件及控制器如要交付，保留原 bytes 改以 `.txt` 證據形式保存，不在證據根新增可執行來源。

## E 完成後的一次性命令

下列是待填 E／review 的命令形狀，**尚未實跑**：

```sh
python -B /workspace/geo261-evidence/source-binding-E-preparation/verify_E.py \
  --root /workspace/geometry-axiom \
  --expected-e <E的完整SHA> \
  --snapshot-l /workspace/geo261-evidence/source-binding-L-preparation/snapshot-L.json \
  --review-file <已凍結的外部review.json> \
  --review-sha256 <該review原bytes的SHA256>
```

由外部調度器保存完整 argv、開始／結束 UTC、stdout、stderr、真正退出碼；stdout 是成功綁定 JSON。輸出也留 repo 外，不把 E 的自我綁定塞回 E。若日後再提交綁定文件，那是另一個交付 commit，須另列差異，不能把 E 事後改寫成自含的成功收據。

驗證器會：

1. 要求實際 HEAD 等於指定 E，前後沒有非忽略的工作樹變更，L 是祖先；讀取所有中間 commit 及完整 diff，拒絕 merge、刪除、改名、產品／帳本或其他路徑變更。
2. 固定 L 快照原 hash `72283a36e47831867884f9682684267eddaf5d208acaf3891a0abeb9b3774455`，並用獨立參數固定外部 review hash；不重產 L 快照。
3. 檢查 E 證據實際路徑集合、總索引集合、外部 review 集合完全對應，逐檔驗原 bytes／hash 與 E Git blob；證據須為 100644 一般檔，無 symlink 或執行權限，拒絕可執行來源／主動文件副檔名及巢狀 Git 規則。
4. 核兩份設定是 L 原 bytes 加指定 suffix，實際用只讀 `check-ignore --no-index` 確認證據皆未被忽略，用 `check-attr --cached` 確認每份證據的 text、whitespace 都為 unset。
5. 核 L 的 1010 檔來源聯集在 E 全部同 bytes／Git blob／mode，包括帳本；611 架構 inputs 逐筆 LF hash 與 input closure 同 L、四 metadata 同 bytes。
6. 在新 Python 程序只載正式 hash 函式，重新算 include closure、core oracle、bridge 各 oracle、mutant 定義與 tool hash；不呼叫正式 CLI、編譯、測試、架構掃描或 mutation 執行。帳本必須仍為 `868a80700c9d058e208684631e799a91659e7820b06c31c246b8af96c670a731`。

Git 使用 `GIT_OPTIONAL_LOCKS=0` 並停用 fsmonitor；Python 關閉 pyc。程式只讀 repo，結果只印到 stdout。既有產品來源保留 L 的原 mode；證據新增檔才要求不可執行，不把新證據政策套回舊產品腳本。

## 已完成的低成本自證

兩支外部腳本的 AST 語法檢查退出 0。`guard_controls.py` 只從驗證器 AST 取出明列的純資料函式與常數，不載入 `main`、正式產品模組、Git 或任何 repo 檔案；在記憶體小夾具上驗前後合法資料均通過，**31 個負控制全部拒絕**：路徑越界、畸形 review、重複／漏檔／含自身／未排序索引、JSON 重複欄位及錯誤型別、產品／帳本／其他根 diff、刪除／漏檔／重複路徑、泛開 ignore、缺 whitespace 屬性、竄改原設定前綴。

實跑命令：

```sh
python -B /workspace/geo261-evidence/source-binding-E-preparation/guard_controls.py /workspace/geo261-evidence/source-binding-E-preparation/verify_E.py
```

退出 **0**，stderr 空，原件為 `guard-controls.json`，SHA-256 `9818c0c956ebaa9236229afb26d04db873ffaf07018237187dad49b3d003f185`；argv／時間見 `guard-command.json`。控制器 SHA-256 `6cd01265b84e13b7119d8f6b7d3117c2fdad1d9edd288e9632d9fb3c4ee46e68`。這些是驗證器純資料守門自證，不是產品突變或 E 完整驗證。

尚未驗：真 E 的 Git 路徑／blob／屬性、最終證據集合、來源 hash 重算與 E 遠端公開狀態；沒有以空範本或目前 L 冒充 E。最大不確定是尚未凍結的實際證據集合，而非驗證器已允許其他路徑。即使 E 綁定通過，也不能宣稱產品測試在 E 重跑、PR 審查已解除阻擋或可合併。
