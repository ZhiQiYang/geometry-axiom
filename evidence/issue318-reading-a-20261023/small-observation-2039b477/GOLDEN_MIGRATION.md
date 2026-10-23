# 閱讀 A 當前非空 golden 見證遷移

本次小型觀察固定在乾淨來源 `2039b477a9669a9e3fcaad740283605b8de8a8f4`，只在主代理指定診斷終態後取得 R3 非阻塞獨占鎖；8 build、timeout 15 秒、CPU 10 秒。真 exit 0，0.668 秒。完整 argv、原 stdout/stderr、環境、來源與工具 hash 見 receipt.json；這不是正式 generator/selftest/scan 驗收。

原 STEP20 左上 Y 的逐支種類／矩形、兩軸縫與原 golden 完全相同；閱讀 A 只解除它的固定段 I19 限制，現在 buildable。不能再用它要求非空 core_limits，也不能把非空斷言改成允許空。

改用既有手算 FZ120 左上 Y，定位幾何不變：

- 固定段 id 3 的矩形 `[0,3648,1000,3675]` 在 x=1000 與 id 1 正接觸 24 mm，僅餘 3 mm；這個定位邊端點的 I19 限制符合閱讀 A 而解除。
- id 1 的矩形 `[1000,3645,4100,3672]` 定位邊為 x=1450..4100，延伸段為 x=1000..1450；x=1000 不是其定位邊端點，仍有 y=3645..3648 的延伸端面懸空。I22 未獲准改動，因此必保 `CORE_LIMIT_EXTENSION_END_FREE`，建構 id 1、端面 1000、該矩形。
- 同一次 observer 中，current 與具名 withdrawn 政策的全部 60 支料、縫、conflicts、problems、p182 完全相同；唯一宣告差異是移除固定段 id 3 的 I19 限制。這是政策變更，沒有重畫幾何或改 I22。
- 排序後 index 1 是 `[0,3648,1000,3675]`，真正 id 1 在 index 2。原 id≠index、四元組矩形綁定、舊三元組必報 UNBOUND 的牙齒保留；generator 另要求唯一精確 I22 紀錄。

只更新 `core_limit_witness`；從 `params` 起至檔尾（含原 8 房 64 排法）原 bytes 完全不變。沒有把見證房加入 rooms，也沒有用 withdrawn context 包整份當前 snapshot。GOLDEN_MIGRATION_REVIEW.json 保存完整新舊見證與逐欄身份核對。

另修正先前尚未驗過的 P182 新預期：FZ114 左上 X 的 3656 候選實際仍有 CORE_LIMIT_MAIN_ON_EXTENSION／C8_MAIN_ON_EXTENSION，3604 仍有 MAIN_HITS_RC_TIMBER；所以原第一可行 3544 與 trace [(3656,false,true),(3604,false,false),(3544,true,false)] 必保。FZ107 左上 Y 和 FZ114 右上 Y 才分別按既有第一可行規則選 3667／491。未改候選、數值門檻或偏好規則。

本次是從封存觀察人工覆核後的來源遷移；正式 generator/selftest、其 source 撤回 0/1/0，以及所有原生／掃描／reader 裁判均仍待資源槽，沒有標成通過。CLI 已放次序仍見 QUESTIONS.md。
