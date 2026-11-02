# 固定來源後一次採入衍生資料

產品／測試來源固定 `9829461187ff5fb5bfeb87ca0bc0a4b5a00645a2`。#367已用此head觸發真兩Chrome shards；不是等expected之後才第一次跑browser。

1. #344恢復完整full原終態收回後，才執行canvas架構三原CLI及完整native producer，保16MiB／2100秒／原斷言與skip，使用已經0/1/0驗證的同一task-local reaper。架構四產物先存checkout外，不先改source。
2. 原full-only producer成功後，expected-after原bytes與完整raw封存；只有已知唯一expected變動，才能以before/after精確hash守門恢復原expected-before，讓同一固定source回到clean。這不是丟棄產物；成功產物另存並稍後逐byte一次採入。若有未知修改或原producer紅，停止該採入而保留所有原件，不以失敗expected當依據。
3. 在同一fixed source維持原無shard入口，跑原完整canvas，與官方兩片原structured/journal逐段比較。官方實際合成merge execution與PR head分開，需核tree精確相等。
4. 真harness撤回在隔離clean control副本；只能讓一個原具名assert判false，原golden／timeout不變，必須由實際Chrome原harness產紅，不以手造摘要冒真控制。已保存綠baseline、恢復綠才閉環。
5. 原兩片artifact下載後，在其精確execution來源副本跑原verify；再用副本作缺片／run/attempt／raw錯誤等負例，原官方ZIP不可變。這是收據裁判實測，與真Chrome反證分列。
6. 同源驗收收齊後，才一次採完整producer expected與Linux canonical四檔，記唯一衍生資料diff與product/test/judge/plan/runtime閉包；不追逐每個receipt head重抽已有效樣本，final required CI必須依真head保存。

這是排程與來源保全計畫，不是已執行證據。未新開工具框架，不啟動第二個local重測，未手填expected或改斷言。
