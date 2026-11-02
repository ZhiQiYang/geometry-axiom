# GEO-323 edge probe 專項進度

產品來源分支：`codex/train337-edge-probe-20261024`。這是root審合用的同列車子分支，未merge PR、未force push。

目前source SHA：`a543eef67b81f8d8800f32d5dc4a5641840d2943`；產品變更起於`9430bae568feb98805072930c92f9a03a1250d4e`，父為公開列車evidence `b621a4fbc3cdea359b3676fb22dc8ef566968b8a`。兩次source都已一般push並核remote。

產品只重用edge lookup已找到的空槽，成功rebuild時丟棄slot，index配置失敗沿原線性降級。nodehint、公開API、graph列舉順序與既定時限不變。

| 步驟 | 結果 | 下一步 |
|---|---|---|
| 最小產品與精確3leaf外稿 | 產品31/0、companion124/0靜審；新17方法AST與原14/helpers保持 | 正式C驗證 |
| S9430 全17第一輪 | 真exit1；16方法綠，whole3subphase同名目錄/ELF造成ld錯 | 只修test work目錄前綴 |
| 測試路徑修正 | source單leaf一行，普通push至Sa543；同行13/0 | 原全17重跑 |
| Sa543 全17第二輪 | 真exit0；17/0skip、56compile/link0、43native，specials獨立actual peer1427/0 | 封存R1/R2完整原件與獨立審查 |

第一輪完整stdout/stderr、編譯輸入、binary snapshots與實際退出碼都保留。連結錯誤不算有效突變；root、combined及specials的先前靜態審查漏掉這個Linux目錄/執行檔撞名，已記入`R1_TEST_PATH_FAILURE.json`。

原性能N64/main1.4283紅仍是歷史受驗L的結果；本修正未跑性能，不宣稱已達1.3。新F的175/350有序graph+guards、效能、native/browser、帳本與架構由root整合後驗收。本子分支目前不是READY-TO-MERGE。

第二輪的10個語意控制均有實際相鄰baseline0／具名assert1／原baseline再執行0。整段probe撤回另用三版獨立編譯：完整有序圖皆0，hash操作次數21／31／21，成本斷言0／1／0；撤回compiled source去除診斷計數後逐byte等於L，恢復等於Sa543產品。這是確定性算法操作數，不是新的效能門檻。

完整原收據已經同行核對，現在封存出版；本節不能代替root在合流後固定F執行的原175/350、guards、perf、帳本與架構。

獨立原件審查：source兩次出版390/0（combined），C17第二輪原流1427/0（specials）。specials在查核準備時兩個helper假設錯誤都另保原helper/report，改讀真compiler argv後通過，subject未修改；不把這些審查工具錯誤冒產品失敗。
