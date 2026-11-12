# 有序依賴索引候選：作用域提示與失敗保全

候選來源 `3949deb9e565a9e5aeca5bc475ec646e77cc6546`，已一般推送 `codex/geo300-consumer-scope-20261028`。PR348 正式產品仍 b595e55952d5d66de95024432e1b29bec7525e9b，history 裁判來源仍 75481194f3b85a6b07e11896403633d7d0fa0d6f；沒有採入或移標。

本輪 K 在真正 provider evaluate 的生命週期保存 dependency membership，巢狀離開時還原父提示；所有 ordered nodes/edges、必要配置、provider callback 與 FEATURE 呼叫保留。可選配置失敗退原完整查找；原 stale index 表遺留造成的 allocation 控制紅燈，已修為首次 scoped append 後釋放過期可選表。不是新增幾何演算法或容量豁免。

| 收據 | 原 execution SHA | 實跑終態 |
|---|---|---|
| first-red | 057e56ea97067f3f6cbcd1139c4c6f009129790e | 原 K29：28過1敗，`index-allocation-was-rejected`，exit1，原件保留 |
| restored-k48 | f84c3532685fd1a7f7e2cc7ddf9e205d48e0c0b9 | 原 K29＋slot6＋scope13，48過0敗0skip，exit0，10.334832秒 |
| kw52 | 48c588ada6563ba1a300a5942802fc2d79098b3b | memo/contact/validation/W/capacity 共52過0敗0skip，exit0，26.405145秒 |
| exit17 | 3949deb9e565a9e5aeca5bc475ec646e77cc6546 | 原 scope13加 heap realloc、invalid child、512層巢狀及具名撤回，共17過0敗0skip，exit0，5.543110秒 |

命令與所有編譯、stdout、stderr、exit、stack、真執行來源在各 REQUEST/RESULT；7項 scope 撤回均由指定 assertion 呈現0/1/0，沒有將存活控制說成被殺。3949 相對48只增加測試；source.c SHA256 `93b952992de5d344c8bb3efd582fd7f85318551cb12350dab95554d3e694057e` 不變。不同execution不加總冒一次完整套件。

一次 N128 配對：f580原ELF 6.389608秒/RSS83216KiB，48候選5.588449秒/RSS81692KiB，完整stdout/stderr相同。只有約12.5%改善，不能推稱512或H7已通過。3949的O0 -pg診斷8.644050秒/exit0，stdout同原件；帶profile開銷，不當性能樣本。profile顯示新剩餘成本在node查找及contact派生索引，不追加取樣到通過。

候選正式512、整套H7 1200秒、有序圖、帳本/census/架構/native/browser尚未完成；原F2/C各600秒綠項保持原來源。上游343→346→347未閉合，未達合併條件。
