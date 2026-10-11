# #198 / 看板 C2：矩形與輪廓接觸

基底為 PR #196 `635dd86ee368579aec444fb3ba16e48bccf4877e`。
產品原始碼與新增測試執行 head 為 `bd5715c318ed17a4f9ff4f9263d3dc9ccb75bcbb`；
後續證據／數量表提交不冒充 exact-head WSL 裁判。
公理依據：R7、R8、R12、R14、R15；未改 SSOT、正典、白話、BACKLOG 或決策佇列。

## 修改前後實跑

| 精確輸入 | 修改前 | 修改後 |
|---|---|---|
| A：頂緣凹口，矩形 `[30,70]×[50,80]` | `obstacles` 誤列 hole `[30,50,70,80]`；`apply-proj` 到後續重驗才拒絕，沒有成功提交錯孔 | 明確 R7 退化，查詢不捏造孔或接觸矩形；指定該項立即拒絕、完整 rollback |
| B：尖脊，矩形 `[20,80]×[70,80]` | 清單為空；指定 c1 被 R15 當不存在而拒絕 | split `[40,70,60,80]`；柱及帶 `cut-strip` 的樑皆成功拆片 |
| 真孔、遠離、貼邊 | 通過 | 通過；沒有把所有項目一律改判 |
| A 與另一合法柱共存，只選合法柱 | 初版修正曾整面拒絕，失敗測試見 `before/mixed-item.log` | 退化狀態屬於各項；未選到的退化項不阻擋明確指定的合法柱 |

原始輸入、回應、World dump、head/tree/source/binary hash 在
[`../evidence/geo198/before/probe.json`](../evidence/geo198/before/probe.json) 與
[`../evidence/geo198/after/probe.json`](../evidence/geo198/after/probe.json)。
原有 143 個場景，修改前後均滿足原 oracle，接受／拒絕判定改變 **0**；新增 4 個場景亦通過。
這不宣稱所有 stdout 或任意未登記輸入逐字相同。

## 精確判定與能力界線

依全部輪廓頂點的 v 座標劃分拓撲不變的開 slab，配對所有垂直邊交點，再與足跡區間取交集。
全部使用整數／倍增中線，無角點代理、`+1` 偏移抽樣、浮點誤差或面積乘積。
只有各非空 slab 是同一 u 區間且 v 連續時，才回傳單一精確接觸矩形。
反向 winding、共線頂點、負座標與 1 mm 尺寸有原生釘點；另以獨立佔用格集合驗交集與 bounds，
8 種輪廓變形各超過 100,000 個矩形，並非以新算法重算自己的期望。

精確交集修正限定為 `classify_rect_outline` 的矩形與平面正交外輪廓接觸。
樑初始足跡與立面障礙仍走既有 strip／bbox 路徑；不是所有障礙皆已精確裁切。
現行障礙／鬼影交換契約只容納每項一個矩形。A 的兩塊不連通交集及非矩形交集，
目前明確報 R7 退化，不挑其中一塊、不以包圍矩形冒充、不新增多區交換格式。
障礙清單含這種項目時，`obstacles` 查詢仍整份回明確錯誤；UI 不會取得其餘合法項清單。
「未選到的退化項不阻擋」目前僅保證直接指定合法項的 `apply-proj` 可成功，
不是清單／UI 能忽略退化項的聲明。
零面積相切亦拒絕。此限制與成功處理 B 分別記錄，不宣稱一般多區投影已實作。

三個呼叫點：`world_face_obstacles` 保留退化項身分供 R15；`proj_apply_one` 的 STRIP
以同一精確函式再分類；`apply-proj` 逐片接觸辨識保留 R14 單片／多片拒絕及交易 rollback。
沒有新 UI 入口，也沒有修改產品 JS。

## 拿掉整個修正與突變帳本

`remove_fix.py` 暫時以精確基底的兩份 C 檔取代本次產品修正，測試保持相同；
先要求 native／bridge／scene 三個 runner 均 exit 1，且原生及 bridge 指名 A/B、場景結構結果指名兩個反例，
再逐 byte 還原並要求三個 runner 均 exit 0。finally 保全原檔；勿與其他 build／服務同時執行。
完整 argv、cwd、source/binary hash 與 raw log 在 `../evidence/geo198/remove-fix/`。

M61 忽略 slab 的多段交集，被 A 場景殺死；M62 恢復四角全在外快退，被 B 柱及樑場景殺死。
完整帳本 52 筆：44 killed、1 crashed、4 equivalent、3 retired；survived/invalid/stale/blocked=0。
crashed 沒有冒充 killed；每筆依既有工具保留 baseline／attempt／source／oracle／binary 身分。
四個 worker 使用不同 cache、結果檔與不重疊 mutation id，全部真編譯、真執行，之後才合併帳本。
`initial-mutations/` 是混合案例收斂前的批次；合併裁判不得把它替代最終 `mutations/` 或 versioned 帳本。

## 重現（repo 根目錄；Linux，不是 WSL）

```sh
ulimit -s 16384
python3 tests/binaries.py build
python3 tests/geo198/probe.py /tmp/geo198-probe
python3 tests/geo198/remove_fix.py /tmp/geo198-remove-fix
python3 tests/geo198/refresh_mutations.py /tmp/geo198-mutations
python3 tests/mutate.py --check
python3 tests/run_all.py --build
```

`base_reader.py` 使用暫存 `git archive` 的精確親代來源 fixture，只跑 reader suite，
結束即清除；不是 worktree、第二份產品閱讀器、親代完整驗收或 WSL 收據。
親代 reader 實跑 41 項，36 pass、5 fail、0 skip；原始結果與 source/tree/reader hash 在 `parent-reader/`。

完整非瀏覽器 runner 共 83 個 suite，2705 個有計數項：2699 pass、5 fail、1 個具名允許的 Windows GDI skip，exit 1。
唯一失敗 suite 是 reader；5 個失敗 id 與精確親代實跑相同，正典 hash 也相同。
這僅支持相同失敗名稱及原正典身分；不證明本 PR 沒有增加重建後的追溯差異，
不豁免 5 個失敗。正典同步、最終 head 驗收與正式／代理 WSL 七 job 仍為合併前待辦。
沒有逾時、未跑 suite、非允許 skip 或額外失敗；這不是全綠或可合併聲明。
最終原始總日誌、逐 suite 日誌／JSON、數量表、binary fingerprint、來源身分與證據 SHA-256
另附 `../evidence/geo198/aggregate/`。
本次用了 `--update-expected`，讓完整發現數確認新增檢查後才更新數量表；不削減斷言或豁免失敗。
真瀏覽器／正式 owner 整合、Windows GDI、正式七 job WSL 收據均未驗。
CI 受帳號計費阻擋;正式合併裁判由本機 WSL 收據提供。
