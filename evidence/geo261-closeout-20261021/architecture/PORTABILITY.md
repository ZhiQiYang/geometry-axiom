# 收尾工具可攜性與實跑版本

可攜性檢查只讀七支現用工具、兩支 P-189 歷史工具及現有收據，不執行編譯或瀏覽器，也不更動已實跑的工具 bytes。來源 commit `4fe18b8b2afe79c44f8a293dcbeb119c43f0e22c` 已納入九支正式工具；架構 gate 的實際執行結果另由 `run-4fe18b8b/` 收據記錄。

| 正式檔名 | 路徑假設 | 在其他 Linux 工作區重現 |
|---|---|---|
| `p52_probe.js` | 第一個參數預設 `/workspace/geometry-axiom`；其餘沿用 CDP 的明示隔離 URL、feedback 與 Chrome 設定 | 第一個參數傳入完整 repository 路徑，設定 `GEOMETRY_TEST_URL`、`GEOMETRY_FEEDBACK_DIR`、`GEOMETRY_CHROME` 等原始收據參數。從 `probe.cjs` 改成正式檔名不需改 bytes。 |
| `p72_probe.js` | 第一個參數預設從正式工具位置向上三層取得 repo；其餘使用 CDP 的隔離環境變數 | 第一個參數明示完整 repo 路徑，避免外部副本所在位置影響預設值。注入模式與第二服務 URL 依收據明示；工具會拒絕不相容的組合。 |
| `p189_verify.py` | `--repo`、`--work`、`--out`、`--gen` 預設本次 `/workspace` 路徑；三方版本及 GCC／bash／Linux `/proc` 量測方式為本驗收契約 | 四個路徑皆明示傳絕對路徑，`--final` 指完整來源 SHA。`--work` 與 `--out` 使用新的專用外部目錄。產生器須由下列固定交接 commit 擷取，再以 `--gen` 指定。 |
| `p189_verify_build.py`、`p189_verify_equivalence.py` | 保留各自歷史實跑版本的預設路徑與完整 bytes；路徑同樣由參數覆寫 | 只供指定階段歷史收據溯源與重現。新版正式量測使用 `p189_verify.py`，不得把歷史工具稱為目前正式 runner。 |
| `run_gates.py` | `--root` 預設 `/workspace/geo261-gates`；`--out` 必填；binary 暫存放在輸出目錄同層的 `bin/` | 明示 `--root` 與 `--out`；Q38、card、axiom 共用同一隔離來源，輸出放 `/tmp` 的專用目錄；保留收據中的 `--jobs`。 |
| `run_controls.py` | `--root`、`--out`、`--model-base`、`--controls` 全部必填 | 明示四條絕對路徑；程式會以指定 repo 為 cwd，因此下列 controls 的 cwd 匯入規則成立。 |
| `q38_controls.py` | 從 cwd 的 `tests/` 匯入真正 Q38 裁判；保留原始交接 CRLF bytes | 經 `run_controls.py --root … --controls …` 執行，或先切換到目標 repo 根目錄。檔頭「never committed」為歷史文字，本次依使用者授權正式登記為測試工具，保留原 bytes 以維持證據對照。 |
| `refresh_receipt.py` | `--root`、`--out`、`--source-head`、`--review-file` 全部必填；固定五個產品根目錄及三個獨立來源是既有架構契約 | 傳入四個明示參數。`--out` 必須是尚不存在且位於 repo 外的專用目錄。不修改來源根目錄或獨立來源範圍。 |

以上 `/workspace` 字串是可覆寫的預設值，並非無法替換的內部路徑。為保留實跑雜湊，本次不另改可攜版；重現指令必須明示參數。

P-189 場景產生器取自固定交接 commit，可在持有該 commit 的 repo 執行：

```sh
git show 59796b1af9259eb23d30134c2ce5a56317a06091:handoff/drafts/issue300/bench/gen_scene.py > /tmp/geo261-gen-scene.py
```

之後將 `/tmp/geo261-gen-scene.py` 傳給 `p189_verify.py --gen`。這只讀取交接 blob，不合併交接分支。原始產生器 SHA-256 應與 P-189 `environment.json`／`timing-environment.json` 記錄一致。

本次只讀檢查時觀察到的工具 raw SHA-256：

| 工具 | 目前 bytes SHA-256 |
|---|---|
| 正式 `p52_probe.js` | `1b1fb5e55f83be15d0a082fb4c32ea3d6526cc8dc7c73b4aeb0bac9bbbc9f083` |
| 正式 `p72_probe.js` | `11f85b9f10e296ea4864d7a8d9a8e460a1fe9a2070b6ab5271756b1f13f230ae` |
| `p189/p189_verify.py` | `fb42a801ce350e64444fcb2db433e59f8c2228546b4b594298581bdb365d0c44` |
| `p189/runner-history/p189_verify_build.py` | `0ed8674c90dc670b37a63a91187f633d7cf11190bb9584a7081dd6a5358dbc7c` |
| `p189/runner-history/p189_verify_equivalence.py` | `c10eea2b116f2595a0a5dcab2dbdbd76d09c5e41e5339102ab109bc1e32049d2` |
| `gates/run_gates.py` | `8dc2e7372da70a22e7f28506270a9709e2f0c3e53419a5043165c2cfe4afcfb3` |
| `gates/run_controls.py` | `b7e7430e53d157f6a82050417be7a9f8d77bd50c1fb5f2f3a34a1ba44de8363f` |
| `gates/q38_controls.py` | `64a76303d825d931736f10bef43b23e56e751a79433bd4aeed895c352b740fe2` |
| `architecture/refresh_receipt.py` | `80ecea0cd2d1189f244552d3e92ffc1a81335424410cf4557bac68cd25d15e86` |

這張表是來源 commit `4fe18b8b` 的工具指紋，不將未執行版本冒充實跑證據。Q38／card／axiom 的 `run-receipt.json` 已記錄相同 `run_gates.py` 雜湊；controls 的收據已記錄相同 `run_controls.py` 與原始 `q38_controls.py` 雜湊。P52／P72 每份紀錄由 `probeSha256` 指明實跑版本。較早可攜性檢查讀到的 P52 hash 為 `c532f49e70cbdb5c6d6bfc5bc72935b4beaf07b5de2311becfe72eb7ade83629`，後續 busy-before 等控制已使正式版本改變；較早日誌不得追認為正式版本實跑。

P-189 初始建置 `environment.json` 的 runner 雜湊是 `0ed8674c90dc670b37a63a91187f633d7cf11190bb9584a7081dd6a5358dbc7c`，與目前工具不同；等價階段的舊版為 `c10eea2b116f2595a0a5dcab2dbdbd76d09c5e41e5339102ab109bc1e32049d2`。兩份完整歷史 bytes 已各自還原並核對精確 raw 雜湊。它們將以明示歷史來源封存的逐檔 exclusion 登記；逐階段保留各自 runner 雜湊，不能把早期建置／等價重新標成新版本腳本實跑。最終封存前應再次核對欲提交工具 bytes 與實跑收據。

## P72 工具第二版補記

上表保留第一輪 `4fe18b8b` 的指紋。工具來源 commit `7afacf656912edccc7eb84cb9590990bccae1166` 只更新正式 `p72_probe.js`，新版 raw SHA-256 為 `6884e80a843834630b777d2add24e1c07c12ccc33f075a18f02403256d0dfcbc`；其餘八支工具 bytes 相同。後續 `55623598f23e4b630987bb27bbb3f55c10815ea9` 只更正 manifest 的穩定用途描述，工具 bytes 不變。

新版保留相同 repo 位置參數及隔離環境變數。`P72B_NAV_CONTROL` 接受 `none`、`stale-first`、`hold-navigation`；舊 `hold-document` 模式停用。新版透過明示驅動器排程延後送出真正 `Page.reload`，使瀏覽器先實讀舊頁條件；`stale-first` 再送出 reload 並控制真正 `app.js` 請求，`hold-navigation` 則驗證候選的導航就緒等待期限。此補記只描述已讀取的工具內容；各瀏覽器控制是否有效，仍以各份原始日誌中的 `probeSha256`、條件值及結束碼為準，不把舊版失效控制追認為新版證據。

## R3 第十支工具與架構 driver 補記

來源 S `ab6869b86a4ad82345359b72397fc055280d8308` 新增 `closeout-tools/p73_probe.js`，raw SHA-256 為 `f12ab05083a0b2f994b34ee78b3990c8873aa749309ea132267ecfd599f32faf`。第一個參數是 repo 路徑，預設從正式工具位置向上三層取得；外部副本或其他位置重現時應明示此參數。P73 的 `minimal`／`full`／`transition` 模式、來源替換、callback 控制及隔離 CDP 環境變數由各次原始收據指定，不把診斷模式與完整驗收混稱。

同一來源只修改 `refresh_receipt.py` 的報告文字，將「變更」範圍明確限制於 manifest 並指出完整來源差異欄位；正式新 raw SHA-256 為 `b0b80afbdbbbb451ab29e774ffbdd1699f0438619b5f84280ef954c8b72fc5a3`。命令列參數與驗收邏輯不變。原版與候選對照記於 `r3/driver-review.json`；外部 `r3/refresh_receipt.candidate.py` 不收入證據包。R3 metadata A `7159530c0e494d3211e6ab1764eb691137211707` 與 S 的十支正式工具 bytes 相同。
