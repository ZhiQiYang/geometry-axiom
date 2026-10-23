# #314 固定來源驗收準備

受驗 source 為已公開 `3b0b634feb54266700cc61f26c34d7aeac4c0314`。目前 own branch head `ed1ab195aa5cd6a7d03de708ff63724404fcbbf6` 只多證據，不能把它冒充此 source SHA 的實跑。這份準備尚未建立 checkout、編譯、測試或執行 mutation。

等 root 明確提供磁碟與第二個 heavy 時槽後，執行：

```sh
env -u PYTHONOPTIMIZE -u NODE_OPTIONS -u PYTHONPATH -u PYTHONSTARTUP \
  python3 -B /workspace/geo314-owner-20261023/fixed-source-tools-v2/run_fixed_source_acceptance.py \
  --repo /tmp/g261-next314 \
  --out /workspace/geo314-acceptance-3b0b634f \
  --heavy-lock /tmp/g261r3/heavy.lock
```

原 R3 以 nonblocking 排他取得；不移除、不改 root 的鎖。若 root 指定另一把已建立的驗收鎖，只透過該原參數傳入，事前明列實際路徑，不偷偷變更排他範圍。全程 16MiB stack；外部 c387 recorder 保存每項完整 argv、cwd、環境、SHA、退出碼與 stdin/stdout/stderr bytes/hash。各原 gate 的非零與 timeout 不會因 collector 完成變成綠，也不會讓其它獨立項目被略過。

## 受驗 checkout 與容量

以 own repo 作唯讀 object source，兩個 `git clone --shared --no-checkout` 建立獨立 Git index：外部 source 及原 mutation runner 的固定 scratch 位置。兩者都 sparse 排除根 `evidence/`、`tests/evidence/`、`tests/release-evidence/`，再 `core.autocrlf=false` detached checkout 到真 S；所有產品 C/H/INC、頂層 tests、`tests/fixtures/`、root scene、現有文件與資產保留。不是以工作目錄覆蓋舊 SHA。

單份 materialized Git tree：3746 files／138,511,198 bytes；排除的三個歷史 evidence prefix：22073 files／1,934,772,291 bytes。兩份 source 合計至少 277,022,396 bytes，另有 Git index、compiler 暫存、原 NativeBuild、partial mutation binaries／receipts 與完整輸出。實際高水位尚未知，先估需 0.6–1.2GB 可用工作空間供排程；這是資源估算，不是產品判準。準備當時 `/tmp` 125MB、`/workspace` 430MB，故未搶先建立 checkout。

`tests/mutation_bridge.py` 原 source closure、oracle closure、byte restoration、binary freshness 守門保留。其 oracle closure 實際讀 `tests/*.py`、`tests/*.c`、`tests/fixtures/**/*.scene`、root `*.scene`；選定六 suite 與 inspector 實際來源未讀排除的 evidence prefix。這個省略範圍不能外推到完整 native／reader 等其它 suites。

## 原裁判與執行順序

1. 原 `tests/run_all.py --build` 加六個原 `--only` selector：
   `py:test_geo314_stagger_commit`、`py:test_geo314_commit_paths`、
   `py:test_geo314_ordered_facts`、`py:test_geo261_wood_grid_application`、
   `py:test_geo261_native_grid_product`、`py:test_grid_inspector_contract`。
   原 expected 為 47／11／14／23／5／3，合計 103；這是目前登記值，未當成實跑結果。
   aggregate 自己逐 suite 跑完及核 expected，保原每項 1200s 限制，不改 assertions。
2. 原完整 standalone `node --test --test-reporter=spec tests/test_grid_inspector_stagger.cjs`，使用本 source 原 registry 新建、fresh 的 bridge。此檔是 native bridge＋VM；不稱為 HTTP、Chrome 或完整 node:tests-js。原 whole node aggregate 時限 900s 套在此原檔，沒有擴大原限時。
3. 原 `python3 -B tests/mutate.py M99 M100 M101 M102 M103 M104 M105 M106 M107 M108 M109 M110 M111 M112 M113 M114 M115 M116 M117 M118 M119 M120 M121`，以全新外部 `MUTATE_CACHE` 與 `MUTATE_RESULTS` 封存本 subgroup。保原整份 RESTORED baseline／restoration；不改 runner 或其裁判。

Linux `tests/binaries.py` 的 `OUT_DIR` 原預設固定 `/tmp/geometry-tests`，不隨 TMPDIR 改。為避免碰 #323 同時驗收的 binary cache，外部 Python launcher 只先將原 module 的現有 `binaries.OUT_DIR` 指到專有 `native-binaries/`，再呼叫原 `run_all.main` 及上述原參數。這是輸出位置 binding，產品碼、registry、fingerprints、build 指令、原 suite、expected、timeouts 均不改。真 wrapper argv 仍整筆封存，不寫成直接 shell CLI 曾實跑。

同時清除 inherited GEOMETRY_/MUTATE_/GIT_ overrides、PYTHONOPTIMIZE、NODE_OPTIONS、PYTHONPATH、PYTHONSTARTUP，record cleared 值。Node 明列 fresh bridge 與原測試支援的 transcript 路徑。所有輸出與 binary 在 source 外；前後檢 source 與 scratch clean/同 S，repo 原 `tests/mutants_results.json` hash 不變。

## 正反例與自證範圍

47 方法完整保留。新增 M121 綁兩個原方法：

- 正例 `test_Q3_same_final_reference_preserves_card_then_unbind_and_rebind_order`：先改卡 A500（引用仍在）、保值解除 500、保值綁回 A500。
- 反例 `test_Q3_same_final_reference_cannot_exempt_value_changing_rebind`：保值解除 400、改卡 A500、再綁回 A500 時 400→500，應依已鎖定 Q3B 拒絕。

新 M121 精確撤回 ordered-facts guard；預期原 baseline／mutant／restored 為 0／1／0，且唯一反例為正常 assertion，正例仍綠。這是待實證要求，現在不能稱 killed。M102 同時驗已維護的 6-arg legacy-value anchor；原 W suite 的 11 個 source controls 與原 ordered-facts 的控制輸出亦完整保留。

M99–M120 不改號、不刪；M110 原為 equivalent／preview-masked，不能宣稱 22 個舊 killed。M121 加入後共 23 個 ID；本輪一律照真結果逐筆保存，沒有預填 verdict。M110 單撤原 0／0／0 與配對 MP1+MP3 的 0／1／0 由原測試區分，不能將 paired 證據偷換成單撤 killed。

## 紅燈及後續

先讓本輪所有獨立項目完成，再據原 stdout/stderr 分環境、產品／測試、需鎖定決策拍板三類；不放寬斷言、不刪測試。若原 bridge mutation baseline 紅，原 runner 會整組 blocked，不能當 23 個變異已測。source identity 失真則停止在環境／受驗來源錯誤，不繼續冒 SHA。

本輪是 partial native＋subgroup mutation，**不是**完整 `ulimit -s 16384; python3 tests/run_all.py --build`。完整 native、全 ledger freshness／整份重產與架構最終收據仍列 root 全 stack 最終 SHA 的範圍，不能用這些 partial 結果冒稱全綠。repo 全 ledger 不重產；global `--check` 若於其它正式項跑而 stale，按原輸出記錄，不把它略去後聲稱有效。

目前不反向 merge downstream。等 #323 的真正 final source，再照 #323→#314→combined→#318→kernel 順序一般 merge；若 source/judge closure 改變，依真 diff 重跑受影響項，保原 S 的執行身份。禁止 force push、合併 PR、修改決策佇列／公理條文。

## v2 範圍追加（原 v1 保留）

fresh handoff `acd1289228d490c68a139cf17e02fdc1f3cb247c` 的 #314 review 與先前 ea274824 同 bytes（SHA256 `0d4861ae1740e13c2d929f6f54938a45419ce344c5ad90d2f00721a87aeddb17`）。逐條核對時，v1 遺漏了既有 native-grid-product 5 方法與 inspector-contract 3 方法；v2 加兩個原 selector，保兩檔所有數值／歷史／完整載回 assertions。這是執行範圍補正，未改產品、測試或任何已產動態結果。

瀏覽器 `geometry-web/grid_inspector_rename_test.js` 的 P72B 50 屬已遷移舊雙軸 browser fixture，必須在真正 Chrome／HTTP 驗，不由 standalone native inspector 取代。此 driver 不啟動 browser；該項明列 UNRUN，待 root 另外排 browser 槽後用原 CDP gate 實跑。原 golden P72B=50 不改；若只跑原 P72B section，照原 runner 明列 partial／golden未整體比較，不冒 full canvas。本 source 的完整七項不以此 partial 補跑代替。

v1 保留但不執行。combined 的獨立靜審指出：原 `mutate.py` 對 `crashed` 也可能回 0，單靠 CLI exit 0 不能代表使用者要求的正常 0／1／0 自證。v2 不改該原裁判或 verdict，另將原件完整性／自證範圍記為 `mutationProofAccepted` 與 `mutationProofProblems`：23 個 ID 必須齊、原 executionHead 是 S、bytes 已還原，M110 保 equivalent／0-0-0，其餘保原 killed 與 baseline/mutant/restored 0-1-0、正常具名 assertion；M121 精確兩方法且只有既定反例失敗。缺件、crash 或不符仍封存原 CLI exit／原 verdict，但不會讓外層 collector 0 或正文冒綠。這是對已要求自證的證據核對，不是新增產品條件、數值門檻或替換原裁判。

