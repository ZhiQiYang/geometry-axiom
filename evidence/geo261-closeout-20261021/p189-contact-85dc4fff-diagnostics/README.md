# 85dc contact 候選與診斷證據

候選分支 `codex/geo261-p189-contact-trial-20261021`，完整 SHA `85dc4fff44ce49b27f831b21cbdcb662c863302c`。P-189 原門檻仍為紅：N64 `2.5566509200233782`，正式 `check` 結束碼 1；36 筆樣本沒有重抽。既有完整 P-189 包由 [雜湊連結](linked-p189-bundle.json) 綁定，本包不改其原件。候選尚未完成整份帳本／架構與全套正式驗收，不能宣稱可合併。

`contact-targeted/v1` 保留早期未採用結果，包括兩個 BridgeClosed 錯誤及後續發現的指標結合律問題；不把它們算成 killed。`v2` 的原收據記 38 定向測試、原／新各 8 數值案、8 sanitizer 案及 24 個具名 baseline 0／mutant 1／restored 0 控制；原 7ad collector 也通過數值契約。獨立審查在 `contact-peer`。定向工具收據屬 commit 前的精確 source hash，`local-commit.json` 將相同 bytes 綁到候選 SHA。

`diagnostics/pg` 保留一次 loadfile + EOF 的 -pg 診斷、完整 nm/objdump/gprof 與 gmon 明示 base64（可解碼回原 bytes）。未執行的 load+dump 草稿及更正收據也保留。44 個 gmon histogram 點只有 41 可由完整地址區間歸屬，3 個跨界／gap 保留未知；不能用 gprof 的 clone 錯名或 0.44 秒 histogram 取代牆鐘。

`diagnostics/time-preflight-failed` 記 GNU time 不存在，前置結束碼 1、零次 load。`wait4` 是既有 O2 main/final 各一次診斷，真 wait4 均 0；不是新增 P-189 樣本。main 的 user/system 為 0.390615/0.193923 秒；final 為 1.238211/0.040890 秒。

`pc-build-failed` 是首輪外部 header 引入 signal.h 的 si_value 巨集碰撞：archive 0、build 1、driver 2，零次 load。`pc-success` 是 root 建立的新兄弟 out，header 僅尾端加 `#undef si_value`；driver 原 bytes 相同。archive/build/load/nm/driver 全 0，唯一一次 load，stdout 與正式 N64 原件相同。取樣 284 點：libc 163、exe 121，無容量丟棄。libc 保留 module + ELF offset；exe 僅報非零 size 的真符號範圍，沒有 call stack。1ms 是要求間隔，不能把 284 點當成完整 CPU 毫秒或精確總成本。

`copy-callsite` 是 root 執行的同 SHA 外部連結包裝診斷；archive/build/load/nm/ELF 與 driver 真碼 0，stdout 與正式原件相同。`-no-pie` 與 memcpy/memmove/memset 包裝僅用於外部呼叫點與 bytes 計數，不能當正式 P-189 成績；未計 inline 操作或 libc 內部呼叫，tail call 的 return_pc 可能屬上一層。方法、原 calls.tsv、nm 與收據原件完整保留。

最不確定的是 libc 內樣本的確切呼叫來源及單次取樣代表性。這些診斷不能代替性能門檻、不能單獨證明某修正足以解除 2x。沒有執行 contact 精確撤回性能負控制，因候選仍紅。

`artifact-mapping.json` 逐項記原件位置、bytes、SHA256、純文字來源快照或明示編碼。ELF、來源 archive／整樹及 pycache 不進包；它們留外部。每份 `.py.txt`／`.h.txt` 等是 0644 原 bytes 資料，不是新的 active 入口。`peer-transport-transcription.json` 明示對話轉錄與真原收據的區別。`SHA256SUMS` 涵蓋除自身外全部檔案。
