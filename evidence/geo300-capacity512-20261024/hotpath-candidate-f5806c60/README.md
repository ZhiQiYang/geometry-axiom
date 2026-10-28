# #348 第二輪熱點候選：已實跑控制，尚未採入正式產品

候選分支 `codex/geo300-hotpath-candidate-20261028`，完整來源 `f5806c60c6067a64776f979f77981e4aba087df3`，一般push可解析。PR348產品仍F2 b595e55952d5d66de95024432e1b29bec7525e9b，history正式來源C75481194f3b85a6b07e11896403633d7d0fa0d6f；既有512每批600秒通過原件不移標候選。

候選只追加三種省工：W在原facts配置、callback與驗證後重用完全相同的純collector結果；K重用新node已查到的空槽；W對完整uint64非遞減facts略過排序。新增必要失敗/巢狀callback/借用值/具名撤回測試，三套新suite已登錄run_all；沒有更新expected census或全帳本，不能宣告全native通過。

## 實跑範圍與真execution

| 原件目錄 | execution | 真終態 |
|---|---|---|
| memo-original | 1c4bf857b378e21a373e9ca2a21c9ecb081a22ed | 原contact15＋新memo6，共21、exit0；5組具名0/1/0 |
| k-first-red | f78fb041ed2fb46d1b7c38adc186dfe2b8ecbfba | 原K29全過；新suite因fixture目錄和ELF同名link失敗，整體exit1保留 |
| kw-red | 8efcc265c69aecf802854d1d80eba1893df7b8c0 | 新K6、新W7、Wcapacity7通過；原W14中的duplicate-id控制存活，34項整體exit1保留 |
| w-restored | 8197fde41d7596e0686309623b3a83505d7f0e11 | 只追加同義非單調duplicate fixture，保留原assert；原W14 exit0，原具名紅恢復 |
| memo-extra | c1679057c02f0ba1c320220f19db7291bdb4a854 | memo10 exit0；原5＋nested/FEATURE failure/borrowed miss共8組具名0/1/0 |
| contact-final | f5806c60c6067a64776f979f77981e4aba087df3 | K/W組合後重跑原contact15，exit0 |

每份REQUEST/RESULT、原stdout/stderr、編譯完整命令與執行command、來源SHA均在RAW。沒有把不同execution加總成一次最終整套實跑。K29到候選K leaf不變；新K6/W7/capacity7到候選產品不變；後續只補fixture/memo測試與catalog。原collector callback、allocation failure及FEATURE來源仍實跑，沒有用memo略過失敗。

## 一次有界N128診斷

保留原O0分離K/W/H建置、16MiB stack；新候選每child600秒。baseline C既有原ELF一次6.691757846秒/RSS83132KiB；候選6.037951393秒/RSS83244KiB，約9.8%改善，stdout/stderr全等。第三次只為aggregate診斷，6.388219150秒不能當性能樣本；兩條唯一具名診斷行精確分離後，其餘stderr與完整stdout相同。不是正式性能驗收，不追加抽樣到通過，也不足以證明H7原1200秒或native35分鐘。

診斷顯示50382次collector請求、16796次純結果命中；未命中主要32687次exclude不同（first failure），不是facts相同便可跳callback。每筆有序source edges仍維護：全量index維護比真正backward查找多很多，將沿consumer生命週期評估更有意義的省工；未採任何新演算法或語意。

`instrument_memo.py` 執行記錄SHA為fd5e580a30d2d044c0d814fb1a818a1686b2eea393080fbb08ebaf1167bf7471；先前預檢28b80a只是舊註解版本，不冒同檔。原輸出C、build、binary及腳本均封存。

仍未完成：候選172場景完整圖比較、正式512/H7、全census expected、完整mutation ledger、架構四檔/三裁判、native/browser；上游343→346→347仍未閉合，禁止合PR/main，不改公理或時限。候選未READY。
