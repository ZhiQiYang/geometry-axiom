# #341：F8 fallback 四類成本與既有全刀的接續準備

本目錄沒有跑 C、性能、Chrome 或產品測試；沒有修改 repository 或分支。固定候選來源為公開 F8 `75a1e93811a52b69385cbdaf6a09d773ed9052ad`。這是可執行外部診斷草稿，仍需獨立審查及 root 的性能獨占時槽；不宣稱 #341 B1 已解除。

## 已讀來源與原件

- `origin/handoff/codex-takeover-20261021:handoff/pr-reviews/341.md`（目前 handoff `7a31dc436c78f16979b8f4cb97550118355f6d3a`），最後審查 2026-10-24T02:38:34Z，head `823729b`：四類 work／CPU／wall 未量測；無收益或倒退必如實裁決。原 native／timber／CI／strict aggregate 仍缺。
- 已有 `/workspace/geo341-c493-whole-cost-draft-20261024/`：Sc493 `c493b7315d0cd3b16014add96af969c49ebf4660` 的整刀撤回，withdrawn leaf 逐 byte 等 pre341 `a6072dde8eac809e93ccd9373946dea98fa5c362`。harness 與插樁已有77項靜審 exit0，但 C／成本量測未執行。此來源與本次 F8 不混用。
- 已有 `/workspace/geo341-active-compaction-cost-plan-20261024/`：F0f `0f695866c0ba12d2c70dfd7d40628d0fda0f905f` 的狹義 fallback 撤回草稿。本次只復用精確 before／after 區塊；F8 原葉由真 `git show` 重新讀取，完整 raw／exit／argv 存 `source-read.*`。沒有重跑上述既有語意證據。
- `cost_harness.c` 是既有 Sc493 小 harness 的明示改版，加入重複 ID fallback 及實際路徑觀察；舊77項審查不自動適用此新稿。原 `tests/geo261_contact_world_harness.c` 的8個正例在正式執行時按 F8 Git bytes 讀取，不改原斷言。

## 因果範圍與尚缺的對照

F8 已有 #343 unique-ID plane index、member sort 及 plane-range 改善，後者本身使用 active bitmap。把整個函式恢復到 pre341 會同時撤回 #343；不可以稱為單獨 #341 成本。

本稿的 fixed／withdrawn／restored 都用 F8 closure，唯一因果刀是把 **legacy fallback** 的 active bitmap／stable compaction 恢復為原逐項 memmove。後續 indexed path 完整保留，且另用 unique-ID 正例驗證。三版語意應 0／0／0；完整優化撤回不是功能錯誤，不強造「語意 kill」。恢復來源須逐 byte 等 fixed。

因此，即使本稿將來數據完整，也只能證 F8 fallback 的因果成本。**舊 Sc493 的全刀四類仍未跑；通常 unique-ID 路徑的整個 #341＋#343 家族成本也未獨立撤回。** 最保守建議是分欄交付：Sc493 原整刀（若仍需歷史 B1 證據），F8 fallback 狹義因果，本列車 R8 既定整體性能。R8 已有效完成，不重跑、不移標，亦不代這兩個微基準。最終是否足以解除 #341 B1 由審查判定，本工具不自行裁決。

## 四類與控制

F8 原 macro：member capacity64，face capacity `8*32*(8+1)+64*2=2432`；超容量 N=1217。這是公開 caller buffer fallback，並非 host 擴充容量。所有 heap 成員、fact、face 陣列均實配；cap外保 sentinel，cap內淘汰 scratch 不當公開承諾。

| 類別 | 輸入 | 來源獨立的語意預期 |
|---|---|---|
| 無重複面 | N=8/32/64；同 ID42，多筆 fact，u每次距200、寬100，v0..27 | 2N faces原順序完整保留 |
| 少量重複面 | 同上，只有最後兩筆 footprint 相同 | 去掉一對，保完整逐欄順序；同ID最小／最後order沿既有契約 |
| 密集重複面 | 同ID42，所有 footprint相同 | 原活集合依序刪除，保最後一對；序列化值與原末對一致 |
| >capacity fallback | N1217，cap2434；互離與密集各一點 | compact=false；原逐刪 fallback；超capacity只是 caller-owned view |
| 非主樣本控制 | unique-none／unique-few／unique-dense，N64 | actual indexed_calls=1；三版逐欄同序列，不當 #341 狹義收益樣本 |

主樣本 diagnostic 要求 actual indexed_calls=0；有界主樣本 orders.indexed=true、unique=false；超容量要求 indexed=false，不誤斷 unique 必false。每個樣本配置 placed、footprint_valid、同placement；沒有新增木工規則或 RC／端頭判決。

## 實際收件工具

`run_costs.py` 預設只輸出 metadata 計畫。`--execute` 才啟動。它先核全部 pins、固定 F8 可解析、原 c387 Recorder pin、獨占兩把原鎖、實際可用空間與16MiB stack，再從 **F8 Git object** 物化必要 K/W/header 原件及8-case原harness；不是修改 live full123 ROOT/cache，也不自稱完整checkout。所有讀取、編譯、link、ELF與case保 argv／exit／stdout／stderr／環境／source SHA。

編譯物件清單與 include 結構復用原 NativeBuild 的24個K及 contacts/supports依賴。原 native compile/link timeout300s，case timeout20s保持。成本編譯統一使用明列 `-std=c11 -O2 -Werror=implicit-function-declaration`；這是外部O2成本/語意樣本，不冒原NativeBuild的O0正式aggregate。所有變體、common dependencies及harness flags一致。

診斷 ELF 與未插樁 ELF 分開。診斷插樁記：shadow iterations、active初始化／讀取／刪除、memmove呼叫與bytes、compaction copies、實際indexed呼叫及orders狀態。轉換逐 byte 可逆；診斷 TIME 明標非性能樣本，數字不是硬體 memory-traffic 量測。未插樁 ELF 用 process CPU／monotonic wall 記完整collect，fixture與序列化在計時外。

每點一次不計分 warmup三版，接7個三版交錯輪，奇偶輪反序；每樣本1次collect。完整原值／順序／時計解析度保留，沒有適應性迴圈、剔慢樣本或新速度門檻；時間低於解析度須如實解讀。語意退出、完整FACE序列、恢復WORK必符合；CPU/wall只是完整量測，收益零或倒退仍保存，`performance_acceptance_decided=false`。沒有用微基準代正式 native／browser／CI。

## 精確下一步命令（目前尚未執行）

1. 保持 root full123 完成前不啟動此重工作。先由 cost_tool_adversarial 審本v2稿；檢查當時disk，128MiB額外資源守門是儲存預算，不是產品門檻。不要刪原件、fixtures或Gitobjects。
2. 由 root 在獨占性能時槽呼叫：

```sh
python3 -B /tmp/geo341-cost-preparation-v2-20261025/run_costs.py --owner /workspace/geometry-axiom --out /tmp/geo341-F8-fallback-cost-run-20261025 --execute --root-exclusive-lease --minimum-free-bytes 134217728
```

所有檔案會保留於fresh OUT；若同名OUT已存在，拒絕覆寫。沒有任何已完成的這輪測量可以安全復用；可復用的是原harness／capture／已凍結的工具。三版 source、所有編譯ELF與完整raw均保，不在末尾cleanup。

3. 原Sc493整刀仍需獨立source／工具／獨占排程；不能把上述命令當其執行收據。若F8較後只採帳本的F9要沿用本輪，須另外給精確closure證明，execution SHA仍保F8。

## 已做的低CPU自驗

`prepare_instrumentation.py` 只產生外部C字串，三版轉換全部可逆，沒有編譯。`test_metadata_guards.py` 14項 metadata/protocol checks；只撤回source identity守門，原／撤回／恢復 process exit為0／1／0，唯一紅是wrong-source。原輸出在 `metadata-proof/`。這是收件工具的自證，不是產品突變證據，也不是任何性能結果。

完整 metadata 原收件另在 `metadata-original-capture/`：使用既有 c387 Recorder 記三次真 argv／UTC／exit／stdout／stderr／環境，三phase仍0／1／0，唯一撤回紅仍wrong-source。先前短收據保在 metadata-proof/，這次只補收件完整度；沒有C或性能重跑。

## v2 收件修正（外部工具；未執行C或性能）

初稿獨審發現完整16列FACE被截成1列仍可接受。v2向parser傳入實際case/n，精確核對META、原harness公式導出的FACE列數、9整數欄、唯一MODE/KEY與完整行。所有C候選/原harness/插樁逐byte未改；未新增效能門檻、未變取樣或時限。原初稿與失敗反例保留，v2 supersedes原啟動稿。五組純metadata/protocol固定／撤回／恢復均0／1／0（source、count、identity、numeric、duplicates），完整原命令在protocol-original-capture；每次14或45檢查，不是產品驗收。由root接手v2以免子代理thread limit重試；未開替代任務。
