## K3 r4 第 5 輪審查(opus):AXIOM-DIFF 條文本身沒有問題,剩 4 項在 PROPOSAL/decisions 的實作段須先改,外加 6 項僅記錄 → r5 裁決(2026-10-10)

K3 提案 r4(#44/#48 共用身分帳)經 opus 第 5 輪聚焦審查:**AXIOM-DIFF 條文本身沒有問題**,剩 4 項在 PROPOSAL/decisions 的實作段須先改,外加 6 項僅記錄。依裁決修成 r5,完成即定稿。(以下審查要點與裁決原樣保存。)

## 須先改 → 裁決(全部標「暫定(依 2026-10-09 授權 L)」)
- **S1 去身分 dump 在連線階段被前端擋掉**:app.js main :612-613(基準 :539)連線未就緒時只放行 `^(objects|surfaces|boundary|references|obstacles|render|pick|bhit|dump)(\s|$)`,獨立指令 `dump-deidentified` 比不到;初次載入(:481)與重連(:559)的握手(:565)和 restoreSession(rw :293/:303)都會被擋,頁面一律連不上。→ 把該指令加進這條白名單;§2.5、§4、K3-Q30/Q35 補列;L-20 加突變「拿掉白名單項 → 兩案都紅」。
- **S2 ③「舊紀錄以 sceneHash 代用」前提不成立**:restoreSession 要求 `record.session===connection.session`(rw main :294),session 是每行程 uuid,K3 之前的紀錄永遠出局;真正缺 probeHash 的是 K3 之後試改 Finish 寫的紀錄(rw main :1572-1573,recoveryKey 與 receiptKey 兩處),:285-291 會把它當 saved 恢復,用去身分 dump 對完整 sceneHash 比必不符,Finish 中斷恢復永久失效。→ 裁決採**本地剝除**:恢復時解開 `record.bytes` 的場景,依 I⟨K3-3⟩ 刪掉 `requires identity-ledger/1` 與 `identity` 行後在本地算探測指紋,不另存 probeHash、不做第二次 dump;刪掉「寫於 K3 之前」那句理由;同時消除僅記錄 R1(revision 相等不保證同一快照)。
- **S3 L-23 在測試環境跑不起來**:`interactive_apply_line`(:4831)與 `gdi_show_three_views`(:5935)都在 `#ifdef _WIN32`(:4151–:6171)內,CI 只有 ubuntu、橋接測試在 WSL,照字面要新編 Windows exe 會撞 SAC。→ 閘門寫成 `_WIN32` 外的純判定函式(參數:宿主模式、World、tokens),`interactive_apply_line` 只呼叫它;L-23 在 Linux 測此函式,保留 L-07 對照與兩個突變;GDI 接線只做 read-back 確認;註明測試接縫可設旗標,「只由 GDI 宿主設定」限於產品路徑。
- **S4 能力集合寫法會放寬模型輸入守門**:scenario_verify.py:149 `_capabilities` 預設 `supported=NATIVE_CAPABILITIES`,:576 用它驗模型 `requiredCapabilities`,:44-45 註明模型輸入維持較窄契約;只加 NATIVE 會讓帶記號的模型 base_scene 也通過。另 `json_engineering_capabilities` 固定清單(engineering_bridge.inc:19)須無條件加 `identity-ledger/1`,否則 :557 `required - available` 失敗;:150 檢查清單長度,固定清單與 BRIDGE 須一起加。→ 只加 BRIDGE;固定清單無條件加;`required_capabilities` 只在已啟用時加;補斷言「模型 base_scene 帶 `requires identity-ledger/1` 時被拒」。

## 僅記錄(一併處理)
- R2:補寫「`/api` 送來的 reset/default/loadfile(app.js:606)與 `/upload*` 之後,由宿主在 bridge_lock 內重設區段」;`recorded_api` 目前直接轉送無後續動作,列入 K3-L 工作。
- R3:L-24 加一個未啟用 World 的對照組(完全相同的 put-parameter 冪等)。
- R4:更正行號——rw 1413→1416、1451→1546、1772→1867、1824→1919、198-199→201-202(main);main 的 :1824 是 `fetch("/upload/prepare")`;§2.5 清單把基準與 main 行號分欄標明,不要混寫。
- R5:L-20 寫明「app.js main :4457 帳不完整時拿到 `dump.text||""`,網格引用清空」是預期的降級。
- R6:L-23 的「經 interactive_apply_line 載入已啟用場景」改為「經 gdi_load_scene_file 載入」。
- R1 由 S2 一併消除,在對照表註明。

## 交付要求
P 開頭加「r5 對照表」;Dp 補對應條目;A 若有改需在對照表標明理由。只改 scratchpad,不改 repo、不 commit、不 push、不跑測試、不碰 WSL。
