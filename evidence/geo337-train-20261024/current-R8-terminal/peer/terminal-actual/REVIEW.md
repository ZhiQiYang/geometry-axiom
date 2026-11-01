# R8 正式終態、CI 與帳本檢查的獨立核對

受測來源 F8：`75a1e93811a52b69385cbdaf6a09d773ed9052ad`。唯讀對抗審查完成，8209 項核對、0 發現、exit 0；此數字不是產品測試數。未改分支、裁判或來源，未重跑產品及效能。

- 六份原始 binding 的 SHA／大小與摘要一致；原 stage execution 為 **0/0/1/0/0**，累積 CLI 為 **0/0/1/1/1**，outer **1**。四份真正工具物件確認 session 62076，最後 chunk `2aff4e` 為 exit 1。
- 全部 36 個原樣本、固定交錯順序、原執行檔／stdin／stdout／stderr／exit 均核對，重新計算中位數與比例一致。N16/base=`0.9834192453688345`、N32/base=`0.9007932884873169`、N48/base=`0.7392862448969592`、N64/main=`1.2846970752586067`，全符合原門檻。未重抽、刪除或正規化樣本。
- 四個 gprof 原始輸出與實際 flat calls 一致；fix 的 N32/N64 source calls 為 82668/364369，比值 `4.407618425509266`，符合原 ≤4.5 門檻。
- 175 場景、350 個 ordinary 與350個 trace 命令的完整原流皆核對，程序 exit 均0、原時限均600秒；350份完整有序圖解壓後的長度／hash一致。逐對原 bytes 重算仍只有 role_priority、P8低／高凹角三個 stdout 差。原精確 assertion 為 `verify_linux.py:156 assert not failures,failures`，不能將程序0或效能綠當作 exact 通過。
- `ABC_result` 原欄缺席、`all_required_stages_completed=false`、`full_acceptance_passed=null` 均未改寫；compare 後段未到的 audit 不宣稱通過。
- F8 run `40170221039`／證據 E815 run `40170692505` 的18次原 API讀皆0；各七 job 均 failure、runner_id0、steps空。原 failure annotation 是付款失敗或支出上限，並非產品測試執行失敗；Ubuntu migration notice 另列。未修復付費設定，未取得替代驗收裁決。
- 原 tracked `python3 tests/mutate.py --check` 實際於F8 exit1，120 stale／3 retired／0 invalid；前後 HEAD與來源保持乾淨，wrapper完成0不冒check0，未重產帳本。

限制：各場景的 guard 計數核對原 equivalence report 及 base/fix 配對一致；recorder 原流未獨立保留每個場景覆寫前的 guard 檔，不能聲稱已從全部原 guard 檔重新計數。完整包 roundtrip、全部 build／source preparation 原件及尚未執行的正式 gates 另行審查。本次僅核既有原件，沒有新增產品通過裁決。

指令：`python3 -B /tmp/geo337-r8-terminal-actual-peer-20261025/audit.py`，exit0。

`REVIEW.json` SHA256：`17ea298086d5f29c3b940debb426c949bc411ba7b25ab673d09c798a5412020b`。
