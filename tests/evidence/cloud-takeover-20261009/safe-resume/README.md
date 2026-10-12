# 安全 Resume：同 session 明確 Pause／Resume 的限定交付

本包綁乾淨受測產品 `128afbec9240f36ae149682830e6b3a96ea02101`，保留此前 unit、fixture、身分 preflight 失敗，不合併或改標。它不是完整 CDP、完整 Space、Windows／golden 或任意 crash 恢復驗收。

## 實際命令與不同範圍

| 實跑範圍 | 完整受測 SHA | 實際結果 |
|---|---|---|
| Python Handler 全檔 unit | `05e59392e7c933c16268c711b450c5970aef7270` | 46 項、exit 0、completed true，mocked native |
| Python Handler 全檔 unit | `f5638ec4288eeec4e014c5618eed3fd1886080ea` | 46 項、exit 0、completed true，mocked native |
| 原三份 Node unit | `f5638ec4288eeec4e014c5618eed3fd1886080ea` | 117 tests，113 pass／3 fail／1 named skip，exit 1 |
| 正式四份 Node unit | `128afbec9240f36ae149682830e6b3a96ea02101` | 132 tests，131 pass／0 fail／1 named skip，exit 0、completed true |
| 新 Resume15 控制 | enclosing clean 128afbec 的同一 132-test 命令 | 15／0，是上述 131 pass 的子集，沒有另造一次命令或相加 |
| 真瀏覽器 r4：1280／390px × Finish／Cancel | `128afbec9240f36ae149682830e6b3a96ea02101` | 4／0，14 斷言各案例、共 56，actual exit 0、completed true、identity problems [] |

所有 unit 原具名略過保留，不能報成132通過。Python Popen 在原單元中 mocked，不假裝實跑 native；部分 Node 原 unit 有真正 native caller-mutation backend，並不因此代表整個瀏覽器／native 整合完成。

## 安全機制與正向案例

Exact resolve 只讀完整 ticket tuple，找現有 native B，不配置、重播、close 或寫高水位。明確「暫存並離開」先沿用已有 scene/snapshot freeze，再以 strict transaction 存完整最新包、來源 bytes、校準／版面、engineering／assembly 草稿、dirty/saved/downloaded/provenance 及唯一 eligible sidecar。原 v1 eligible:false ticket 不會被解釋為 Resume 授權。

Resume 在尚不能編輯時 reacquire 同 B 的 editor／recovery locks，核 native／package／metadata 指紋，以 strict CAS 消耗 eligible journal，核第二次 dump 及最終 ticket，然後只 metadata attach；不重送 scene，不混回 A。損壞、reserved-null、錯 hash、storage abort、缺來源或 owner/ticket 漂移拒絕且保留資料；unknown acknowledgement 保持凍結。

四個真瀏覽器 positive 案用相同 session 明確 Pause→Resume，檢查完整最新 package／source closure、兩個 B locks、A 不變、B context 不重建、Resume exact resolve 只送一次且無 upload/create/close/reset/loadfile/native mutation。Resume 後正常參數輸入可再次提交。Finish 保存最新完整 B 一次後退休 B；Cancel 保住 A 後退休 B。

Browser r4 原 log SHA-256 `5dff7a4fcc68e71f986ab001ac9ae569bbb95994524f7e97ac5a5c7ef3afe288`，原 results SHA-256 `70f6f8c5c35eed22634513877edf9e05b637a0c8589e6afa6a5d19f5f969c08a`。每輪 receipt、原 log 路徑標籤／大小／hash、命令／exit、before/after SHA/dirty/source/runtime、當次 live Node／Chromium／native 身分在 [manifest](manifest.json)，不僅依 runtime 推 native。

## 失敗沒有刪除

舊 f563 source-override unit 的 driver 與 fixtures 首輪 setup、package oracle 修正過程分開保留，最終15項舊產品為13 pass／2 fail、exit1：reserved-null journal 與 project metadata 指紋反例。Immutable product source 在 f563乾淨capture，但每輪 execution checkout dirty 未捕捉，明示 unknown；不冒充完整 clean formal gate。後續 clean128 的15成功是正式四檔命令內子集。

Browser r1 因不可見的 return selector 逾時，r2 因 calibration fixture 與 mmPerPx 不一致於 Pause／Resume 前失敗；r3 因 identity adapter 錯把既有 retained NativeContexts 當只准一個而 preflight reject，actual execution 未開始、0 cases。有效 r4 保持原產品 assertions，只修 fixture／正常操作入口與身分核對前提，允許同服務存在具相同 exe/hash 且確實為直屬 child 的合法 context；原 root／retained B 不殺、不改設定。

Executor 的 byte review 仍標同一 executor，不當独立 actor；公開 source／runner 路徑投影副本沒有代替当次執行檔。若某個歷史 receipt 不記錄 interpreter hash，保持 unknown，不拿目前檔案倒填。

## 公開內容與範圍限制

本包僅將 machine/executable、隔離 test／feedback／browser profile 路徑換標籤；原件在 scratch 保留，original hash 與 public projection hash 分開。保存的 `.gcanvas` 為本次合成 fixture，內含程式生成 `resume-synthetic.pdf`；有核 archive entries／manifest／World，不是使用者原件。沒有私人 feedback、真使用者文件、trace/profile、圖片、native binary/sidecar bytes 或私人 queue DB。

校準／draft setters 是合成 fixture preparation，沒有實體校準／IME／手機硬體的宣稱。只涵蓋同 parent、同 native session 的明確 Pause／Resume，不承諾 abrupt reload、crash、服务重啟、跨 session／profile／origin、old Undo transport 或未確認 transient 工具恢復。

歷史完整 CDP2207／0／0只綁clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；原#173 Windows1692／2、exit1、completedfalse未改，七份Windows原件雲端未收到，dot唯讀核收中。P74/P75不相加、不宣稱核golden。私人queue v6缺失保歷史v5與currentunknown，reconcile/list-ready/list-alerts未執行，不建空DB。

下一步是當輪最終產品候選必要整合、#123已採納UI、#54同協定單房成本，root繼續既有授權範圍；未定公理／非空跨專案政策列決策點，不擴#87多房，未合併部署。
