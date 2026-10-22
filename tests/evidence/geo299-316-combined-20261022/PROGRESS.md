# #299＋#316 combined 雲端進度

本分支獨立基於整合公開 E `4b665fae21ab63aaffb7d84f6a32d5a469ba1675`（#288 code F2），不帶 #323，也不疊 #314。工作樹 `/tmp/g261-next299316`，分支 `codex/geo299-316-combined-20261022`；沒有 merge 或 force push。

## 唯一補丁來源與靜態移植

使用 handoff `804afbb4c5fa38b6023087d6dcb150f40c5978e6` 的完整 `handoff/drafts/combined/rebased-546e2eb2/patch.diff`；原 SHA256 `422946025137ba719ef4e42da1a527ba5bc07bbf8e52b28e687392061074fef6`。沒有先後套用兩個 individual 補丁。已讀根 AGENTS／PRODUCT-VISION、HANDOFF 第0／2節與兩案 DESIGN／TESTS。

原 `git apply --check` 真退出1，`--reject` 真退出1；已知衝突為 contact_world.c 一個hunk與test_geo261_wood_contact_world.py兩個hunk，完整指令／退出碼／stdout／stderr／rejected hunks都保留。manifest刻意不套舊稿，沒有覆寫F2四檔。

手解後保留 F2 `ContactOrderIndex` 的 last／minimum／重複id最後排序與最早遮蓋、equal-order穩定與容量fallback；從index宣告到完整collect-stops原bytes逐字相同。Python保留`app_contact_facts`→prepare wrapper檢查、原prepare裡member身分斷言，以及`index->minimum[slot]<order`→`<=`的具名負控。host facts harness只更換一處#299診斷全文，F2 raw callback snapshots及所有時序／partial-output斷言均保留。current_geometry.c仍統一CRLF。

#299新增定位邊e<i>、定位邊區間與實際低／高超出區間，保留原V_EXTENSION前綴與原裁決；#316移除三個無caller的H wrappers及僅被死wrapper呼叫的W footprint API。完整190個既有manifest C sources的唯讀盤點未發現額外caller；190是此次清單結果，不是新增數值門檻。新增的caller測試依實際manifest動態seed，保兩入口與relative／root／publicK include規則、探索全部conditional分支、缺檔fail closed；也要求退役W名稱零引用。

刪除範圍只包含死footprint API專屬的9個collision checks、一個測試方法與3個控制項；詳見closure-review.md的逐項對照。活I11放置／H重驗／W最終重驗、M12／M13與新增M97／M98、W邊接觸／跨承載面／未放置、contact-stop／owner原pointer identity各有對應，不能把死API單元測試冒稱產品守衛。新雙承載面正例仍待實跑，不靠調低expected消產品紅燈。

AST／diff靜態核驗通過：原78個mutant定義除M13說明外不變，只新增M89–M98（由AST得到此次88個，不寫死未來總數，M99+保留#314）；新增10個anchor均唯一。core場景AST166與expected相符，wood contact world原10減退役1為9，其他expected全保。這是靜態盤點，不是runtime通過。

manifest仍為原F2 920個policy identifiers；只列`+wood_contact_boundary_edge`／`-wood_contact_footprint_collides`待機械重算，scan／report／receipt未動。未改公理層.md、決策佇列.md、閱讀器或BACKLOG。

## 下一步與限制

父agent僅放行兩套W診斷：`python3 -B tests/test_geo261_wood_contacts.py`與`python3 -B tests/test_geo261_wood_contact_world.py`。先固定公開P，再使用全新私有TMPDIR、保完整原child0／1／0文字streams與可選GEO299316_EXECUTION_LOG，atexit清理前封compiler inputs／buildlog／ELF／objects。可選logger只錄原subprocess結果，不改oracle；此階段尚未執行兩套。

其餘compile／測試／架構scan／ledger／browser／bench均未啟動。待兩套全部收齊後分類紅燈；每個產品／測試修正仍須具名baseline0／mutant1／restored0，不能以編譯失敗／timeout假稱killed。完整帳本、架構四檔、三條原裁判、全native／六browser／受影響專項由後續最終SHA另驗，不能將本段靜態準備當完成驗收。

最不確定處仍是草稿推導的p8／p8b診斷數值與新雙承載面正例的真動態行為；後續原工具將裁定，尚未聲稱全綠。沒有新增公理語意或數值門檻待代決。

原patch與兩份rejects現置於original-patch-and-rejects.raw.tar.gz，三members逐bytes/hash核同；不改原CRLF或空白。初版直接文字入Git時diffcheck報原輸入空白，純封存格式改為archive後仍保原raw；產品/tests未再改，後繼證據E會另列受驗SHA。

## 私有W診斷原結果

- `diagnostic-contacts-01`，受驗SHA `2bd45fc9413397637cd0c56c39ac2b6704806d72`，原exit0；75次native，原退出碼分布`{0: 52, 1: 23}`，完整原輸出與compiler inputs／ELF／objects／buildlog已封存。
- `diagnostic-contact-world-01`，受驗SHA `2bd45fc9413397637cd0c56c39ac2b6704806d72`，原exit1；59次native，原退出碼分布`{0: 40, 1: 19}`，完整原輸出與compiler inputs／ELF／objects／buildlog已封存。

contacts原10/10 tests綠，23個控制各原0／1／0。contact-world原9方法執行完、唯一失敗是complete-footprint控制：舊oracle要求`ASSERT:i5-notched-footprint-deferred`，新草稿卻把`ASSERT:boundary-edge-failure-leaves-outputs`插到前面，撤contact_contains後先命中新斷言。這是fixture順序缺陷；原native正常退出1，不是compiler／crash／環境問題，不能把本suite原1寫成綠。原subtest中途斷言失敗使該控制的restored呼叫尚未執行，因此本輪59次native；原數量照留。

下一步保留全部新舊斷言，把新增failure-output檢查移到原I5判準之後並重設sentinels，固定新公開來源；須證撤這個fixture修正仍回同具名紅，恢復後兩套全綠。其餘18controls都照原迴圈跑完，不遇紅停等人。新的雙承載面場景／M97／M98仍待完整native與後續真突變裁定，不冒稱已通過。
