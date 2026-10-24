# #339：固定 F 的 importer 與三組反證已完成

2026-10-24：在可解析的產品 SHA `38da31bcac91db631e6325e40b228f8604810e82`，重新執行指定九個原 importer module：45＋10＋10＋9＋8＋1＋16＋30＋13＝142，全部實跑／通過、零失敗、零略過。三個 predicate（list、dict、feature）各自完成原 `0/1/0`；撤回時都是具名正常 AssertionError，恢復後逐位元組回到原產品碼。五個原執行工具皆退出 0；這是指定局部驗收，沒有合成完整 native／expected 的退出碼。

來源物化先確認原 M=`1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` 與空 porcelain／diff，再普通 detached checkout 到 F 並物化原 493 inputs 加既有 5 個 Markdown。原十個 Git 命令全部退出 0，初末 guard 均完整保存；沒有 reset／clean、未移除收據或 fixtures。最後 native43 的 493 inputs、Git logical stage、HEAD 與乾淨狀態均保持。原 60／900／1200 秒等內層限制沒有改動，native43 使用私有 binaries 與 secondary lock，未碰主線 native 的共享快取。

完整原始命令、stdout／stderr、退出碼、環境、原測試／反證工具、來源 Git blobs 與兩支私有 ELF 的 sidecar／hash，收在 `raw/ORIGINAL_F38DA_IMPORTERS_142_AND_PREDICATE_PROOFS.tar.gz`：4,716,492 bytes、1,469 members、SHA-256 `c2d2c75b39536d7e801cb31af2cc49d0de3aafd130a0a0cdd27b6701b8abc435`。ELF payload 未入此包、原檔仍保留；原程式未公開的內部 pipe 不另補造。獨立實績審查 6,636 項／0 finding；原件均逐 member 對照 bytes／hash。

最新已讀審查是 fresh fetch 的 handoff `1ddb1bb73b9bc0958cf488280412ba116c880a5e` 中 `handoff/pr-reviews/339.md`，2026-10-24 00:39:36 UTC、head `e9ee6d0`。B3 的 142 importer／三 predicate 部分已有 F 的新實績；aggregate native 仍未跑，B3 尚未全部解除。

**正式 11 列仍為 3 PASS／1 RED／7 UNRUN。** 原架構三條 PASS 與 mutation check RED 仍保留 execution M，沒有冒稱本輪在 F 重跑。帳本原結果為 123 定義／110 紀錄、107 stale、3 retired、13 unrun；完整 native／expected 與六 browser 仍未驗收。本輪未修改產品、測試、帳本或架構產物，也不借用 #338 的 L 收據填綠。

B2 的新 Actions run `40040764499` 依最新審查仍七 required jobs failure、runner 空、steps 空；沒有宣稱 CI 環境已修復或重新執行。C1 仍須完成 #324→#339 的可見正式接替；C2 的 base #340 仍為未驗收 draft。本線維持 draft，未標 READY-TO-MERGE。下一步依主代理排程完成最終來源的帳本、完整 native／expected、六 browser，並在 base 收斂後重核受影響 closure。
