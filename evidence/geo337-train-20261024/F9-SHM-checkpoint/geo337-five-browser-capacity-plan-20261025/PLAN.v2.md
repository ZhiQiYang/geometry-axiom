五項 browser 共同容量計畫 v2（只讀盤點，未執行 SHM 準備）

唯一來源 F9：`4f8a794f4167c3562eb182045102e86e9e37cca9`。原 canvas 已完成；其餘五項仍待正式執行。

既有 SHM 的可用空間為 17,871,880,192 B，mount type 以本次 mountinfo 保留。原 `/tmp` 47,214,592 B、`/workspace` 27,578,368 B 為 12:52 的快照；既有來源、原收據、fixtures、Git objects、dirty 全保留，不預支未執行回收。原分離配置只做下一項 materialize，TMP 尚缺 59,343,671 B（另需新 plan 10,483,982 B），WS 缺 41,771,008 B。

採一次完整 seed（3,759 葉、139,059,750 logical／148,242,432 rounded bytes），五項在同 device 共用唯讀 payload，但各自保有獨立來源根、Git/index、private golden、ports、TMP/build/output。保原每 device 64 MiB materialize reserve；單 device 依原分組公式只算一次，沒有新增 runtime 必保 64 MiB 門檻。

整輪保守配置：seed/Git 192 MiB；五項 metadata 320、runtime/Chrome/build/raw 320、完整 archive 160、新受保護揮發性 Git store 160、遠端完整下載核 hash 160；工具/出版/audit 64；單一活動項暫態餘裕 256；原 reserve 64。總計 **1,696 MiB = 1,778,384,896 B**，距 2 GiB 尚 **352 MiB**。這是配置估算，沒有宣稱已量測動態峰值或保證上界。

F9 canvas 原終態 endpoint：runtime 28,831,744 B；sourceplan/index 23,830,528 B；包含 metadata 12,443,648 B；Git archive objects 11,825,152 B。舊 L 其餘五項 endpoint 合計 78,192,640 B、舊包 32,777,424 B；舊包曾排除 ELF/cache，不能當本次完整包的精確預測。所有原測量與分項見 PLAN.v2.json。

順序 assembly → documents → grid → space → timber；原 workflow/CI/端口/斷言/原始輸出規則不變。各階段紀錄 mount、free、OWN 實際占用與 RAM/cgroup 取樣峰值及間隔，不能把端點當峰值，也不外推為 R8 效能結果。新來源 copier、placement 工具、完整 collector、新 store publisher 各自要受審並有真實收據；本計畫不替它們通過。

SHM 是揮發性 tmpfs。「受保護」表示不可任意清理，並非持久磁碟。每項交付之前需完整封包與 roundtrip、一般 push 真成功、遠端可解析 SHA，再下載完整包核大小與 SHA256。交接記錄遠端重建位置；未驗證不得宣稱交付。遠端下載副本可另按已知 cache 策略收尾，原 raw／封包／Git objects 不刪。舊 TMP／WS object store 與 alternates 均不改。
