# LAN 安全審查承接紀錄

## P-048 原裁決與範圍

下文逐字摘自本機交接 `handoff/CODEX-LOCAL-W-B-fix.md` 的 S6；由任務看板指定本線照該交接實作。
該完整交接檔 SHA-256（原 bytes）：`bdd5932130d9525f08756090498f75996f05d61b3665e29051a0329f06bf539b`。
這是既有主迴圈裁決的公開原文，不是新採政策，也不以 P-050 代替它：

````text
- **S6(主迴圈裁決 P-048,不照審查的修法)**:缺少 `Sec-Fetch-Site` 照樣放行,以相容 iOS 16.4 以前的 Safari;cookie 已是 SameSite=Strict,另有 Host 檢查。
  - 重複出現、或值不是 same-origin 或 none 的,一律拒絕。
  - 測試要明確涵蓋三種情況:缺席(放行,附理由註解)、重複(拒絕)、非法值(拒絕)。
  - 成功案例的測試要明確帶 `Sec-Fetch-Site: same-origin`。
  - DESIGN 或 README 寫明這個取捨。
````

適用範圍為本 LAN 模式的請求守門：缺席 Fetch Metadata 仍須通過 Host、既有 Origin 規則和（除配對頁外）唯一有效配對 cookie；cookie 使用 SameSite=Strict。成功測例明帶 same-origin，另以具名案例核對缺席、重複與非法值。
既有裁決的取捨是相容舊 Safari，並保留其他驗證；此文件不宣稱已跑 iOS 實機。若改採「缺席一律拒絕」，須先由裁決者推翻 P-048，再同步守門、相容範圍與測試，不能只改測試期望。

## 完整 subject 白名單與根信任界線

CA subject 只能是單一 CN `geometry-web LAN test CA <指定 IPv4>`；leaf subject 只能是單一 CN `geometry-web LAN test`。簽發模板與驗證共用這個完整結構，額外欄位、重複 CN、萬用 CN、不同 CN 與空 subject 都不能持久化或重用。其餘效期、簽章、私鑰、BC／KU／EKU／SAN／NameConstraints 仍照原政策驗證。

這項本機白名單不等於手機的信任根只可驗證指定 IP。現有 CA 約束針對 IP、DNS、email、URI 名稱形式；若 CA 錯簽出帶萬用 CN、只帶正確 IP SAN 的葉，允許 CN fallback 的 OpenSSL 客戶端仍可能把它視為某個 DNS 主機的有效憑證，含正常 CN 後追加萬用 CN 的情況。回歸測試保留此反例，不用本機驗證已拒絕來掩蓋外部客戶端的信任界線。關閉 CN fallback 的對照須拒絕，同一 CA 的正 IP／錯 DNS 對照也保留。

因此只宣稱：本服務簽發、保存、重用的材料經完整政策驗證；**尚未證明 iOS 根信任的指定 IP 隔離，也未證明任意錯簽葉都被平台拒絕**。iOS 版本、根約束與 CN fallback 實機結果仍待人工驗證，B1 的目標平台部分尚未解除。測試只使用暫存合成材料，不更改信任庫或安全設定。

## M19／M23 裁判修正

M19 沿用同一 closed／expired 突變，改由既有 09a 判斷；09d 舊裁判的實跑結果獨立保留。M23 保留舊 04b 的平台觀測，另觀測拒絕回應到達後，真實 socket 收到並排空延後 body，且 body 沒送進 native bridge；新裁判不依 RST 對已收資料的作業系統差異。拿掉 lingering close 必須令新裁判失敗。這不是用「Linux 舊測例存活」推論 Windows 不需要 linger。

本輪驗證收據完成後在 PR 回覆列出；未完成的排隊工作、Windows 純測及前一 head 均不能當成最終七 job 通過。
