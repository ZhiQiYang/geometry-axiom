# PR #201：存量草稿普通捨棄回歸

依審查 6143996420 的 B1、SSOT I68/R54 和既有 P-059/P-064，只讓純移除中的逐字未變剩餘草稿使用 stored 判準；完整候選/manifest 仍驗，新接納與內容修改仍保留自動缺失補標容量。

正式 writer 9e136db5479b685bc0ad5699a7650f429736df14 的八份原始 CommonJS 相依檔由 Git blob 逐 bytes 取得，未改 writer；native bridge 在新 session reset 後建立邊界1與系統1/2，objects/dump 原件在此。fixture 為131072-byte內層、base系統1、唯一live inputRef系統2、另一份other的舊集合。源檔清單/hash與 frozen ZIP hash 在 fixtures/*.json；make-legacy.cjs.txt 是實際生成工具（工作區絕對路徑須依重現 checkout 替換）。它使用現行測試資料builder，實際驗證/pack/unpack皆是未修改的歷史 writer。

VM regression 執行原 ReferenceWorkspace/Features/P.pack/P.unpack；DOM/PDF與API為既有fixture替身，非正式匯入/瀏覽器/E2E。先冷讀 frozen ZIP，再延續原workspace。普通丟other保留全部raw/base/liveRef，局部UndoRedo逐份還原，真ZIP保存冷讀保留scene與collection。零API呼叫、幾何模型及scene不變；新增與+1真內容仍以具名容量訊息拒絕，未借用過期token或欄位形狀錯誤冒充容量守門。

修前 red 為原容量訊息；修後與還原 green 各1/1，完整撤修 red 1個具名assertion。另四個局部撤修（draft-value、projected-record、projected-manifest、final-feature-proposal）各exit1，均由同一B1容量斷言偵測；source SHA/命令/exit/耗時在JSON。四項周邊子集4/4 exit0，含完整manifest超限仍拒絕、舊P064以及孤兒保存；不把子集當完整native。

早期新增測試的oracle另曾錯把sync重建的underlays視為World、在UndoRedo後沿用舊context token、選到已填滿的raw表單；這些測試工具錯誤及原件保留在本機 /tmp/geometry-wake19/b1-after-invalid-* 等，未計入產品缺陷或green證據。最終測試明確核幾何/零API/同scene，用現行token、合法未填滿rule欄位驗真正容量拒絕。

工程preview衝突以一般merge保留finish_batch和deleted_fields_token兩句；expected按三方增量，保留新main PF22/transport7/serve51和本PR ownership13/grid15/Node701（一個新回歸）。protected SSOT/白話/唯一正典皆只承接main，不手改、不重建第二閱讀器。最終完整native及七項列車狀態另附PR；此目錄只有定向原件，不是WSL收據。
