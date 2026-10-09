# Geometry 現有工作段落：2026-10-09 交付索引

本次交付由雲端唯一產品修正者接管，既有本地交接已解除。產品提交 `6784b6e0b74949bb7b425d13d1a3ad1c5a433127` 已推送 draft #179。下方歷史執行與最新追加結果分列；文件發布 SHA 與受測 SHA 分開，不把歷史收據改綁。

## 102ff 追加核收與剩餘產品缺陷

乾淨受測完整 SHA `102ff28ecb005a85b42a8ae9cd7f22fdcf8cf01c` 的正式 UI 六組為 198／0、exit 0、completed:true。獨立七寬度 caption 為 27／1、exit 1、acceptance completed:false：第一個 1382px 的第七次 Tab 到 PAN 時，按鈕取得焦點卻被工具列裁切；其他六寬度與逆向 Tab 後段未到。另一次只讀、單 1382px 診斷也為 27／1，不當七寬度驗收；實測 pointer PAN 使 nav.scrollLeft=50，但 Tab 到 PAN 時仍為 0，按鈕中心命中 HEADER。外層 scrollWidth 等於 clientWidth，不能把兩層 overflow 配置宣稱為兩層實際滾動。

同版必要完整 CDP 已終止：1800 通過／1 失敗、actual exit 1、completed:false，尚未比對 golden。P32、P64 與正式 P75 的 37 項均已通過；唯一停止點為 P76 的 390px 參數面板使可見畫布只剩 137px，原下限為 150px。這兩項是待修產品缺陷，下一步在新乾淨候選保持原命中／焦點／尺寸斷言重驗；完整 CDP 原件另包追加，不覆寫下列 scope 包。

- [102ff 正式六組、caption 原失敗與單次只讀診斷](ui-102ff-three-scopes-public-v4/README.md)：manifest `ce537c7dc4a2b04bfee905d7b83cab7dfe8a1b43b027409d775cfb74f73ea394`；含當次 exact CI／來源核對及工作管理可用性，current ledger unknown，未建空資料庫。
- [P75 原導航失敗與保斷言診斷](p75-route-diagnosis-public-v1/README.md)：manifest `a736a07546caeff7d3f40dffa3bec6fbe1e0bbdafb5dcb774bc90249759f0e18`；原 243 full 失敗不改，scratch moduleOverride 37／0 不冒充正式 full。
- [公開證據投影與獨立核對](ui-publication-reviews-public-v3/README.md)：manifest `2236c2f60c3b19d5834d9067e14d07e81873638679d904266e587d3b0be963f8`；證據 QA 不加到產品測試數。

## 已修並驗證

完整受測 SHA `243326b512896ace70e068f62c8f3d6397f6000d`，各份 before／after 均 clean：

| 範圍 | 實際結果；各 scope 分列，不相加成完整驗收 |
|---|---|
| replacement／Cross-B／held-bhit／held-proj／390px card／正式 race | 各 16／0、8／0、2／0、2／0、4／0、20／0，exit 0、completed:true |
| 獨立既有完整 Space | 228／0、exit 0、completed:true；五個 declared groups，明示未包括 timber-material／timber-source-guards |
| 明示 strict-v5 四組 plan／BOM／row-blur／S2 | 327／0、exit 0、完整桌面及 390px；保原 row/native/owner 強斷言，Cancel 只允兩種 exact readonly schema及成功回應，完整原生場景不變 |
| 正式 #54 原十正常案例、六拒絕案例、六成本測量 | 273／0、exit 0、completed:true；PDF／PNG 矩形、L、缺口各為 12／14／16 操作，原手動為 16／20／24，同起點／精確同終點；不把機器等待當人類工時 |

原 UI v4 185／2 與完整 CDP 1713／6、exit 1、completed:false 均保留。CDP 未比 golden；P32 inactive host、P64 新 R 後誤用 Escape 的四項連鎖失敗，以及 P75 拖框起點實際命中回報鈕分開記錄。後續已提交實際 active host／原 R→V、正向 SVG 空白起點、同 crossing 矩形與正常 grid 分段路徑，所有原斷言及 golden／floor 保留；243 產品配明示 scratch module 的 P75 37／0 只屬該目的驗證，不當正式完整模式。

`640a81443b3d070dba3d8a0aa52adb2d64cebe0b` 的正式 UI 六組 198／0、正式單房 273／0、EDGE 38／0、投影十案 10／0與同 owner 兩案 2／0各自保留。GRID partial 346／0 的實際 Chromium ELF 身分未核收，不能補填或宣稱完整執行檔證明。

## 原始收據、log、來源與身分

各包的 manifest 列每檔 byte count／SHA-256，原件與公開路徑投影的 hash 分別保存；原始失敗及所有版本、命令、exit、runtime、actual interpreter／Chromium／native 身分不回寫。

- [2703／c0／f980 歷史紅綠及 Resume](ui-single-room-prior-public-v4/README.md)：manifest `3f2abb29f759de73c6e4c72323ead0c42aab763ca4e6391f63d41f9802ae8e9d`。
- [640 各自有效結果及身分限制](ui-single-room-640-public-v4/README.md)：manifest `64a0d10728631d4e9ccdac5c4051f666a95e9104a6159e43eac72950884f0522`。
- [0b37 原始失敗](ui-single-room-0b37-failed-public-v5/README.md)：manifest `389b1fdf3e0d8639bf192f2087f0d49de5a565799229598dc958132bdbcdaa97`。
- [243 的十一個獨立範圍](ui-single-room-243-public-v2/README.md)：manifest `60379e618ef5863cfe661bf215584caa9a64f36dbe7ac35174ccf3b3686961c1`。

以上公開包已由獨立 actor 及 ROOT 核對檔案雜湊、所有 JSON／JSONL／trace 可讀性、無重複 key、來源與值的一對一關係；證據 QA／靜態／mock 數字不加到產品測試數。

## 真正外部條件與下一步

- CI：243 的七個 jobs 皆 runner_id:0、steps:[]，沒有執行。需帳戶管理者解除 runner 啟動條件後，再核當次完整 SHA 的實際 steps；不重跑零步驟工作，不改帳務或安全設定。
- Windows：dot 唯讀核收七份原始日誌，雲端原件未核收。#173 完整 Windows 仍為 1692／2、exit 1、completed:false；後續 P74／P75 局部結果不相加，不宣稱 golden 比對。無需已停止作者再做釋放或重測。
- 工作管理：真實 ledger／完整可驗證 export 不可讀，current unknown，歷史 v5 保留。reconcile／list-ready／list-alerts 未執行；恢復原資料後沿既有 CLI 調和，不建空資料庫。
- #123 原私人 ZIP／稿件衝突與像素對照未核收；43 項來源 inventory不等於43項瀏覽器結案。恢復原稿後逐項比對；C5／C7 精確移除、C6 nearby 與其他未定案政策保留決策點，明確採納項目繼續。
- 必要後段：新乾淨候選跑正式 UI 六組、七寬度 caption／正常 pointer／Tab，以及完整 CDP；原 Space 228／0及單房成本均保持原受測 SHA，不重綁。
- 未驗實體範圍：真手機／touch／IME／OS picker，Resume 的 crash／abrupt reload／BFCache／跨 session／profile／origin不在本輪有效驗收範圍。明確 Pause、同 parent／同 native session 的 Resume 後 Finish／Cancel 依 draft #178 的獨立原收據核。

歷史完整 CDP 2207／0／0只屬乾淨 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`，`9029a8f6bc00a9ff8de1d2b0deb844f331e032e3`是後续文件／證據提交。不合併、不部署、不擴 #87；#168 已取消及 #169 尚待批准的審查留言保持原狀。
