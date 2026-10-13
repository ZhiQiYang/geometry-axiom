# #225 B1 / M1 審查修正

審查 comment 6149474381，原產品 source `077165010377cca974bece7fcda930cd005490a9`。
修正 source `c5512928b03731042e6454ae254d975519ea8b26`。

D43 band r 是 [c_Y(r−1), c_Y(r)]，以正長度交集枚舉：first=floor((lo−c_Y(0))/T_Y)+1，last=ceil((hi−c_Y(0))/T_Y)。板本體列舉、奇偶、signed k、原中心公式、裁切、容量限制均保留。僅點接觸不列 band。g=3、兩個錯開軸、正負 delta、band −2/−1/0/1/2、上下半縫及剛好中心端點皆用獨立 Python oracle 核對完整 (k,band,coordinate,range)，含 review 的 F=[0,200]×[100,104]。

## 正／撤修／還原

先加兩個測試但未改產品時：actual exit1、2 tests、20個具名 D43 assertion failures（非 error / compile failure）。修正後 PF-2 17 + PF-1 22 = 39/39、actual exit0。expected 只由15增加至17，沒有刪舊斷言或降計數。

定向 controls baseline17/17、restored17/17，原7個實作破壞各有具名 assertion 紅；新增下半縫撤修6個失敗、上半縫撤修4個失敗，沒有 test errors。cache control 真正修改 C dump，把 fragments/seamLines 先加入 JSON 再 hex 編碼；原 assertNotIn 仍保留，新解碼 D42 白名單與精確來源比較抓到它。receipt 記錄 source head、oracle SHA、compile argv / exit、binary SHA、test exit與每份原始日誌。

ASan/UBSan PF-2 + PF-1：39/39、compile exit0、test exit0，見 sanitizer receipt 與 raw。

完整 core mutation 按新 C closure 全部重編執行：baseline139/139；48筆=40 killed / 1 crashed / 4 equivalent / 3 retired，0 stale / blocked / survived / invalid，actual exit0；ledger 由官方 mutate 工具重產。crashed 與 assertion killed 分列，沒有沿用舊 killed。兩個 raw archive 包含所有實際 executable、source與sidecar bytes，index提供SHA；不是把新 PF-2 controls加進既有核心帳本。

## 完整 native 與正式列車

完整 native 收據後續加入；不拿定向/sanitizer或舊head native拼出綠燈。產品正式七項由既定合併列車跑，仍 pending；雲端不排WSL。本片沒有接入PF-H宿主或新增UI；P-098後續順序已更新PF2-NATIVE.md，PF23/24僅列後續補充驗收、未冒稱此片實跑。
