# GEO-261 修正 06：工程未放材的負控制

最終修正分支 `codex/geo261-fix-engineering-unplaced-oracle-20261018`，來源提交 `285c37445e951d68420ec321d4ea661e780d14cc`，基底為最新整合提交 `ea9d235a35536753f041ad3213206da1ae242ae5`。該來源的完整 suite **15／15 通過，零 skip**；這份證據只涵蓋本題，不宣稱 PR #288 全量驗收完成。發布本證據前的四輪修前／修後／撤回／恢復記錄保留原 SHA，沒有回寫成最新來源的結果。

分類為**測試寫錯**。原測試單獨拿掉 W 的 D28「只能綁定已放置角材」守門，就期待完整 bridge 接受未放材；但 H 的 I9 終態守門仍須拒絕。`bd82985fff5acad912069dad7a7de922cef81215` 已同時有兩道守門（當時 `engineering_commands.inc:25`、`engineering_bridge.inc:85`）；新增此測試的 `1906eae1a0f8a03f16f4ca54e8fc5c1f4232db7a` 也保有 I9。不是近期產品退化，也不需要新條文裁定。

依 SSOT 的 D28、I8、I9，候選只有全部守門通過才能提交。因此修正保留單點 W mutation、原具名 native kill，改驗「D28 已被穿過、候選來源確已寫入、I9 仍精確拒絕且 live state 不變」。原 `assertTrue(accepted)` 與確認後的五項來源斷言移到合法已放置角材，原物件與 mutant 各實跑一次。產品 guard 一行未改。

只有 `tests/test_geo261_wood_engineering_operations.py` 改動：15 個方法同名同序；原 24 個 assert calls 全保留，增加為 50。`case()`／`mutant()` helper 的 AST 完全不變，原 exact-count、真 W object、完整 bridge 連結、具名 marker 及 crash 拒絕規則都保留。未放材原 fixture 也保留；新正控制是真 `loadfile` 的 1000×1000 surface、boundary timber、`place ... at-face e0 +u +n`，不是偽造 placed fact。

## 真執行結果

| 階段 | 測試來源 SHA | 結果 | unittest 秒 | 專題旁錄秒 | 外層 child 秒 |
|---|---|---:|---:|---:|---:|
| 修前 | `1987af507c6f387d7986325da6c29b2ec6246944` | 15 run／14 pass／1 failure | 14.415 | 14.438418 | 14.667661 |
| 修後 | `ca3badecceace47587aefcfdc2361f5ffdb7daa3` | 15／15 pass | 31.346 | 31.375975 | 31.586731 |
| 撤回測試修正 | `5f83239dcfe4bbcbba0766c70025e125bf64cf3b` | 15 run／14 pass／1 failure | 14.017 | 14.045081 | 14.264441 |
| 恢復修正 | `ca3badecceace47587aefcfdc2361f5ffdb7daa3` | 15／15 pass | 27.170 | 27.198797 | 27.361351 |
| 最新 integration 基底重跑 | `285c37445e951d68420ec321d4ea661e780d14cc` | 15／15 pass | 42.091 | 42.144428 | 42.342092 |

五輪都是 0 error、0 skip、無 timeout／interruption，來源、HEAD、status／diff 在命令期間穩定。時間有三層，表中分開列，不把旁錄時間冒充 unittest 時間；本題不是效能比較。

修前與撤回都在原第 157 行 `self.assertTrue(accepted, response)` 失敗，完整原文見 [修前輸出](protocol-before/unittest.stderr) 與 [撤回輸出](protocol-withdraw/unittest.stderr)：

```text
AssertionError: False is not true
I9: candidate still contains an unplaced timber
Ran 15 tests ...
FAILED (failures=1)
```

上段只摘錄定位文字；完整 response／traceback／精確時間以原檔為準。`withdraw.patch` 與 `withdraw-commit.txt` 保留實際控制：只將該測試檔還原，bytes 等於 1987；沒有撤掉 I9 或任何產品守門。這個「測試修正撤回後轉紅」與下列真正產品 mutation kill 分開陳述。

## 真 bridge 與具名 mutation 證據

修後、恢復及 latest-base 每輪都實跑五個獨立 bridge session；三輪各有 48 個 bridge commands；逐筆比較的是命令種類與順序、request file bytes／fixture bytes及完整 response，這些全部一致。原始命令中的隨機暫存路徑各不相同，原 argv／命令文字仍分別保存在各輪 protocol，不宣稱命令 raw bytes 相同：

1. 原物件＋未放材：首違規精確為 `ENGINEERING_INVALID / I8/I35 / D28: bind only an already placed timber`，候選 `after.sources=[]`。
2. 單獨移除 W D28 guard 的 mutant＋同一未放材：首違規精確改為 `ENGINEERING_INVALID / I8/I35 / I9: candidate still contains an unplaced timber`；response 不含原 D28 訊息。`before.sources=[]`，`after.sources` 恰有 timber 1／A，literal 55、effective 55、override null，證明真的穿過 D28 並寫到候選。
3. 原物件＋合法已放材：真 loadfile 成功、preview 有已放置 geometry、`valid=true`；confirm 成功，`history_changed=true`、revision 12→13，live read 恰有前述來源 55。
4. 同一 mutant bridge＋同一合法已放材：同樣接受並真確認，完整結果與原物件一致。原接受斷言不再是死碼，也防止「一律拒絕」假綠。
5. 恢復原物件＋未放材：重新得到 D28 與空候選來源。

三個未放材 session 的 preview 與 invalid confirm 前後，完整 live `engineering-read`（含 revision／definition hash／sources）及 dump 均不變；invalid confirm 都回 `ok=false, code=TOKEN`。兩個合法正控制也先證明 preview 不改 live，只有成功 confirm 後才改來源和 revision。

同一單點 W mutant 的獨立 native client 真回 `exit 1`，原始 stderr 精確為：

```text
ASSERT:engineering-operations-unplaced-source
```

原及恢復 client 均 exit 0。完整 suite 的其餘五個具名 guard controls 也保留，詳見 [最新 protocol](protocol-latest-base/protocol.jsonl)。這份旁錄存 native client 的真 argv／exit／stdout／stderr；**沒有替每支 transient native client 額外保存 binary SHA**。bridge 則在每次啟動記錄 executable SHA，原／mutant 分別為：

- 原：`978a4d840edea12562ba700445ea00464e9a26cf7b761cc673344091425a719e`
- mutant：`b462cbe9bf23ce4a09106ec20915ff16cc19679685066772c0c7cc651d352339`

`SECTION_PROFILE_INVALID` 的同文訊息是既有 profile diagnostics 對上游拒絕的重述，本題沒有為消掉它而更改產品。

## 最新基底與證據邊界

四輪完成後 integration 前進至 `ea9d235a`，合入 scenario bounds 修正 11。尚未推送的 06 自有提交移植到該基底後，另跑第五輪；最終 test bytes 與 `ca3badec` 相同。`source-boundary/1987-to-ea9-closure.json` 對照兩個 integration SHA 的 199 個路徑：產品根的非 vendor C／H／INC、`current_geometry.c` 及 06 真 oracle／native build helpers，逐 path 的 Git blob／mode 相等，另保存 raw bytes SHA。這是有界來源對照，不是全 repo 無變更或全量重新驗證；另外的變動是 `.gitignore`、scenario 的兩個 Python 檔及其 evidence。

原始四輪仍分屬表中各 SHA；最新 15／15 的聲明只屬 `285c3744`。未跑這個最終來源的全量 `run_all`、完整 mutation ledger 或六個 browser jobs；也未以這份結果替代最終所有修正合流後的同來源驗收。此測試檔屬 mutation oracle 指紋輸入，最終收據刷新仍必須按正式工具要求真跑。

環境：Debian `13.6`，Linux `6.18.55-x86_64`／glibc 2.41；GCC `14.2.0`；Python `3.12.14`；Node `24.19.0`；Google Chrome `155.0.8059.84`；五輪 child stack 均為 `16 MiB`（16,777,216 bytes）。Chrome／Node 只記版本，本題沒有執行瀏覽器測試。

每輪 `before`／`after`／`withdraw`／`restored`／`latest-base` 保存通用旁錄 receipt、process、原 stdout／stderr 及 binary sidecar；對應 `protocol-*` 保存完整 unittest 輸出、真 bridge/native JSONL、專題 result 與工作樹 diff。最外層 stdout／stderr 為空，是因專題旁錄將 unittest 原文寫入自己的檔案，不能據空輸出宣稱沒跑。來源大清單的 aggregate hash 在旁錄中只作轉錄；本目錄整理器不重新推論 pass／kill，人工判讀結果與原始證據一起保存。

獨立唯讀二審核對五輪完成記錄、固定 SHA 來源、精確 terminal 原文、完整 bridge 原子性、控制 patch，以及 raw hashes；沒有另外跑產品測試或修改證據。沒有刪除／放寬原斷言、變更 SSOT／正典閱讀器、碰 `.codex/`／`feedback/` 或處理 #213／#194。
