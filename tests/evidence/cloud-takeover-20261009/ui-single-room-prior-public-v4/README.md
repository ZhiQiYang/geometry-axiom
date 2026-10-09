# #123／#54 與投影歸屬：歷史實跑、失敗與控制證據

本包僅公開已完成的歷史原件與路徑投影，不是重新執行、不綁後續文件 head，也不將不同 SHA 或不同 scope 通過相加成完整驗收。後續凍結候選有新收據時另列新輪次。

| 範圍 | 完整受測 SHA | 原結果 |
|---|---|---|
| #123 原六組 | `2703e4738ae308b2a268096f666f326f1e9a9b2f` | 85／5；probe completed true 僅指六組均嘗試，acceptance completed false，actual exit1 |
| #123 六組 | `f98078dc150c22960cbe2d212afb3ded61954bb9` | 194／0，completed true，actual exit0 |
| #54 原十場景＋negative | `f98078dc150c22960cbe2d212afb3ded61954bb9` | 208／1，completed false，actual exit1；八正常場景達成後 mobile 中斷 |
| #123 六組 | `c0f05baade2424482fab94c72f0592f7b02326ae` | 174／1；probe completed true 僅指六組均嘗試，acceptance completed false，actual exit1；header 測試前提錯誤保留，600／390 後段未到 |
| 既有 GRID_SYSTEM_ONLY | `c0f05baade2424482fab94c72f0592f7b02326ae` | 99／1，completed false，exit1；partial 未比 golden |
| 原投影十案 | `f98078dc150c22960cbe2d212afb3ded61954bb9` | 3／7，completed true，exit1 |
| 原投影十案 | `c0f05baade2424482fab94c72f0592f7b02326ae` | 8／2，completed true，exit1；舊 guessed hole order 失敗保留 |
| 另跑 same-owner 控制 | f980 全 SHA 如上 | 0／2，exit1 |
| 另跑 same-owner 控制 | c0 全 SHA 如上 | 2／0，exit0 |
| 另跑 normal-hole 控制 | f980／c0 全 SHA 如上，各自收據 | 同固定座標、無 held reply 的完整 native World 有序輸出 proof；不修改原十案 |
| 同 session 明確 Resume 四段 | c0 全 SHA 如上 | 4／0，56 assertions，completed true，actual exit0；不宣稱 abrupt/cross-session |
| 四 Node unit | c0 全 SHA 如上 | 132 tests＝131／0／1 原具名略過，actual Node exit0；原 wrapper exit1 是 metadata matcher，原件及 byte 身分補件保留 |

#123 六組只含明示 adopted UI contract，不代表全43 checklist、ZIP pixel、完整CDP或完整Space。首次2703有測試前提／產品差距混合失敗；原script、正常trusted events、fixture與各組細節全保留。f980194／0 的 header oracle 尚未加後續真 hit 控制，不能反推後來所有版面都通過。

c0 的唯一 header failure 發生於900px：`assertHeaderActions(900)`的可見性／hit斷言錯誤要求已隱藏的右侧toggle也可見且命中，原helper僅在width>900時允許toggle隱藏，但原右面板常駐契約斷點是680px；不是先click隱藏toggle而timeout。這是測試前提錯誤，不能當作產品仍有 header hit 缺陷。該組因此未到600／390後段。原174／1、probe completed true、outer acceptance completed false與exit1全保留；後續修正 helper 的 source／mock proof及新候選實跑另列新包，不能改寫本輪結果。

#54 使用同一已校準來源、camera、snap=false、review、草稿、起終點，以及包含真尺寸改正和全邊輸入的 direct-row 協定。六測量案例中 candidate12／14／16、manual16／20／24 各 PDF／PNG 有實跑證據，但該 f980 十場景命令未完成，不能宣稱整套成功或合併較短P79協定。機器 wall time 不是使用者操作時間；Save/New/Open及校準被明示排除於成本計数。

## 原投影失敗與新 oracle 的界限

原十案 f9803／7、c08／2 與原完整有序World比對保留。`normal-hole-historical-order-proof.json` 另跑 f980 與c0無 held reply、同真指標座標，證明既有 native hole ordered bytes 一直從800,800開始；原expected從500,500開始是沒有被baseline失敗到達的猜測。此控制證據沒有修改原十案結果；若採用 expected-only 新版，仍須新source hash、新候選完整run，不用循環容忍、排序或放寬幾何判準來取得通過。

最初 registry API 誤名造成的 projection preflight failure 也保留，未launch browser、無case，不列產品紅。實際執行r2的Python／instrumentation／fixture source快照完整封存。

## Node 實跑與 metadata matcher 補件

c0四檔unit實際完成131 pass／0 fail／1具名skip、Node exit0；原wrapper exit1源於新增matcher只認registrypath，而原rule case executor會在private case directory執行 byte-identical bridge copy。`native-process-identity-review.json` 唯讀核對當時 `/proc` exe bytes、parent、spawnargs與Python hash；native bytes符合原trustedbridge，補件accepted，沒有重跑、刪除原receipt或將wrapper exit改0。首次wrapper1及spawnlog均公開路径投影。

## 公開內容與 provenance

[manifest](manifest.json)逐輪記完整受測SHA／dirty、來源和實際執行檔身分、命令、退出碼、原始log／receipt／results的路徑標籤、大小及原SHA-256；publicFiles逐檔列發布hash。完整受測commit的產品／test source可讀，Git原bytes hash與路徑投影hash分開，公開副本未被當作當輪執行檔。

每個World dump保逐byte原件；每個synthetic trace保原zip hash，若entry含machine/root/profile/隔離feedback路徑則只做明示public projection，另記原／發布entry hash。binary screenshot/resource保持原bytes。trace不是重新執行或實體裝置验收。大張單獨截圖、native binary/sidecar bytes、private queueDB/events/ownerthreads、真使用者feedback及來源文件未收入。小PNG/PDF與gcanvas來自合成fixture，不是使用者原件。

缺少的歷史interpreter身分維持unknown，不倒填現在exe。原完整CDP2207／0／0只綁clean`5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；#173Windows1692／2exit1completedfalse仍未核收，dot正在核七份原始日誌；P74/P75不相加、不宣稱核golden。privatequeuev6缺失保歷史v5/currentunknown，不建空DB。

本包沒有合併、部署、新公理、帳務／安全設定或#87多房擴張。下一步按新凍結候選的實際completed收據加入UI／#54／projection／完整CDP與獨立Space結果；未完成的後段仍列未驗，不能用計畫取代。
