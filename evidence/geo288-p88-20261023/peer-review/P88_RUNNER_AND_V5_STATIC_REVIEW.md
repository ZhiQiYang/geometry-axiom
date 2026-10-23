# P88 runner／局部 v5 候選：獨立靜態對抗審

固定原來源 F：`13d02c1db7022145a52ee063286a558e595eb212`。已讀 handoff `9e44ea94e891270d49d7432f25ebb55cf5709ec6` 收錄的最新【ChatGPT 審查】（head `22ad28f`）。這份審查沒有跑測試、編譯、profile 或瀏覽器，沒有修改正在執行的 source／index／HEAD／session。

## 原紅燈與分類

原精確 fatal 是 `document.activeElement===document.querySelector("#refGuideMode")`，位於 P88 `grid_rule_lines_test.js` 的 `focusedCtl`／`choose`，390px 流程建立真 gridrule guide 後切 advanced。原 footer completed=false、1502 pass／0 fail、golden 未完成比較，不能因 failedAssertions=0 當綠；P73尚未執行。既有 FATAL_UI 的最後真 click 落在 ratio label／最終 active refGuideRatio，支持輸入座標與布局間存在時序窗口，尚不能單憑它確定產品或 harness 的自然根因。

P38 預期例外與 P53／P57 受控 API 故障不能改判成本次紅燈；原 network failures 空，最後 API 成功。F2／F13 的同 Chrome156 與相關 source 身分相同，也不足以把本次歸為版本環境故障。原 cdp_test 另有 browserEndpoint／`json/version` 完整 pathname ownership 核對，沒有 mismatch 證據時不能推稱附到了舊 Chrome。

## 三次純原 workflow runner

已獨立核對原 driver `6a3e3c327687ee6fdafb1044e4c4036f4d2f881a75498af97bd1e1af861e1310`、綁定 driver `8a4e69c915ae770afc59829f3658639af0febbd2b16c20495f7ecee7f62685fb` 與 `driver-binding.diff` 逐bytes相合。改動只有必填 HTTP／CDP port、獨立 profile 及相應 receipt 環境欄；原 workflow、assertions、golden、CI limit 未改。HTTP／CDP／profile 的隔離由原 harness 支援。

driver 繼承的 watchdog 為原 CI 的3倍，但正式 canvas 仍是35分鐘；每輪必須另核 `over_ci_timeout=false`，不能只以 driver0 當正式綠。driver自己的鎖僅在 scratch，R3全域獨占由外層／root排程保證。三次原件都須保留，不能挑綠、抹原紅或僅憑自然三綠宣告已證自然根因。

owner已明列第1輪 NODE_OPTIONS 的當時值未在原 wrapper receipt 單列；當前 shell 為null不能回填當時值，對自有proc的唯讀補查受到PermissionError13也未繞過。後兩輪將在argv明列 `env -u NODE_OPTIONS -u PYTHONOPTIMIZE`，保持 runner本體凍結。這個觀測限制須保留。

## v5 候選核對

目前選定 repo 外單檔候選 SHA256：`8106476b6eb2271111caa835a863b72eced4bab3b2ef77244f28534d83ca0a52`，路徑 `p88-priority/candidate-local-v5/grid_rule_lines_test.js`。原 P88 module hash為 `c47259607a3299d49e1044f3d4d6e5561c0601e0f2295fb7ec5f2255261f4e8c`，與manifest相符。v4 `31058245b58086816ebd54335d26d8f76b5b1ec203c94fa9470b1a3687931c1a` 保留；v5唯一增量是在實際mouse action callback內再驗deadline。

**目前未找到可由靜態證據確立的斷言／golden／attempt／timeout放寬阻擋。**

- 只由 P88 focused 輸入啟用既有 `makeCtl(probe=...)`，shared helper原檔與普通ctl路徑未改。只發一次原 trusted click，不錯點後重點、不用 DOM.focus／DOM.click、不直接改 select值。
- 初hit後使用既有 opportunistic idle，再查目前node／scroll，對原雙rAF逐frame核相同node／rect，最後仍以原 hit／尺寸／disabled 判可點。12是原attempt數；每attempt增加rect觀測，不能聲稱rect只讀12次。精確相等無新epsilon；抖動會保守拒絕，不是放寬。
- 原25s焦點等待上限改由前置與焦點檢查共用，沒有增加額度；這比原「先ctl後另等25s」更緊，文案宜寫「原上限未增加、共用」，而非暗示原來已有相同total deadline。
- 原全部 `check(...)` 行、精確 focus predicate 均保留；input adapter後到檔尾的原 bytes 完全相同。同步log不含新判決，不降低golden計數。
- v5在mouse action開始前追加deadline檢查，避免已排的action直接晚啟動；Promise.race仍不能取消已發CDP eval／mouse。不得宣稱deadline後沒有任何既有動作繼續或mouseReleased一定不晚。

## 動態反證的必要界線

既有單次真scroll控制可以證「measure命中後布局改變仍用舊座標」的通用能力缺口；它不能獨自證明自然P88由真query觸發。真query方案需hold原request及原回覆bytes，依因果事件釋放，留下實際 paint／scroll／node／mousePressed／mouseReleased／focus的時序，證明原位移確在原measure→press（或press→release）窗口。不能為固定／撤回選不同排程或改回覆內容。

撤回須是原具名 `refGuideMode` focus fatal的正常1，不可拿loader／crash／prepare deadline／其他assert紅充數；fixed／restored須原P88完整計數及原scope完成。held query超過 opportunistic idle上限時仍可能在穩定兩frame之後返回；stable不是「未來不會再刷新」的保證，這個限制已由owner承認。

這份報告接受v5作待驗的窄候選；不宣告已修自然故障或正式canvas通過。若採用而改裁判closure，必須固定新的可解析F，依最新審查執行受影響正式項與列定反證，原F13紅與三輪自然結果照留。

小型獨立核對欄位見 `P88_V5_STATIC_REVIEW.json`；候選目前仍是repo外準備，未安裝或動態執行。

既有兩檔診斷loader的 `candidate-local-v5/PROOF_MANIFEST.json` 也已核：hash `5993efea` 開頭，兩份source／candidate／patch hash全合；cdp_helpers候選與原件逐bytes相同且patch為空，唯一實際changed檔是P88 v5，沒有混入舊v3 helper。正式呼叫須明傳此manifest，既有 `run_proof.py` 的預設仍指v3；兩檔loader報告不代表兩個產品檔均有修改。
