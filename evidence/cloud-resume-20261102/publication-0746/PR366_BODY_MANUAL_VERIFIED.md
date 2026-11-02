驗收 head：**`502a64ff6214dd6060927b7f14643a533536f20d`**；base：**main `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d`**。本 PR 原樣抽出 dot 的四個突變／架構收據工具檔，讓後續疊層分支能生成與下載新來源證據；沒有帶入產品、帳本、架構衍生資料，也沒有放寬裁判、斷言、timeout 或 expected。

**已由本機Claude合併至main，merge commit `df7eb43af3389ff2afc1a73aaf4e57580ae612fc`。整tree與已驗502同為 `910665aa55b5be4830de2f729a7aca5db1cbe8cc`；Codex沒有merge main。** 未將舊 df347 的收據改標到新 head。

| 唯一 current-state 項目 | 真實來源與結果 |
|---|---|
| 來源／合流 | 普通 merge parents `df347537c920b5a51ca157d7886857a7d0547d5b`＋`5775a9e9e46bca801a9a70aaeafcdab9f597bc4d`；相對 main 精確四檔、517 insertions；四份 blob 逐 byte 等於指定 #357 固定來源 `15ec7f12a46e6b2f5e4046af3f3826c08ebf5955`。沒有 rebase／force。 |
| 正式整合 CI | [41376852060](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41376852060)，10／10 jobs success。真 execution 是合成 merge **`7d2a1927e15d3c0d59b20fa6618005f19c4a6c56`**，parents 為 main＋PR head，tree 與 head 都是 `910665aa55b5be4830de2f729a7aca5db1cbe8cc`。 |
| native 三片與完整覆蓋 | 77／76／77，共230 suites，真子行程退出碼全為0、無漏列／重疊；**5339 pass／0 fail／1 原具名允許 Windows GDI skip**。下載真 artifact 後重跑原 `native_shard_receipts.py` exit0，與官方聚合逐 byte 相同。移除 `c:integrity` 的原覆蓋測試反證在 CI 與雲端重驗均0／1／0，紅為具名 AssertionError、1 failure／0 error／0 skip。 |
| 六個 browser | canvas full **2267／0／0 skip，85段 golden matched**；assembly150、documents47、grid356、space242、timber79，均零失敗。保留各組 partial/full-space 範圍，不把重複覆蓋相加成唯一案例數。P38唯一預期 fb-auto-probe 例外及P53／P61受控故障注入保留；unexpected例外為0。 |
| 完整突變 CI | [41376852056](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41376852056)，10／10 jobs success；原 execution head為本PR完整502a64ff。七片精確聯集 **123 records／120 active＝114 killed／1 crashed／5 equivalent／3 retired**；stale／blocked／survived／invalid／unrun均0。七個bad-cache原strict均0→1→0，未把crashed/equivalent混成killed。 |
| 架構 | 原三命令exit0，205＋18 tests，604 inputs＝334 owned＋270 excluded，798 edges、零診斷；原raw、工具及來源closure已核。 |
| 原件復驗 | 21個官方artifact ZIP逐一符合GitHub API digest；20個job log與整run原log ZIP逐byte相同。下載binary／sidecar／bridge raw後跑原 `mutation_evidence.py verify` **exit0**；本地ledger與summary均逐byte等於官方聚合，沒有執行下載ELF或重跑產品suite。 |
| 手動入口真實核收 | [workflow_dispatch41397499686](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41397499686)，attempt1／真head`76d311cf1507708bc63bba2ab6e4f0c3f68cabb0`，10/10success、9ZIP API digest全核；原未改動verifier真exit0/25.500秒、123=114k/1crashed/5eq/3ret，其餘0，七cache負控strict1，聚合ledger／summary逐byte等官方。實際需要fresh的canvas分支，不重抽已驗main／R8；未執行下載ELF |

固定原件：

- [完整突變聚合 artifact 13113345761](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41376852056/artifacts/13113345761)：ZIP SHA256 `3b9d5450d2179a6db94b9b1ea3f46c3d10de6e39456b27a251b30b090380d605`；ledger SHA256 **`102c541d59a82e18ba44c6fc0d1ed8116bc581baf759837f734e6fff1d17a5cc`**。新帳本只在CI artifact，本PR仍精確四個工具檔。
- [原架構 artifact 13111561782](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41376852056/artifacts/13111561782)：ZIP SHA256 `63d2660c3a657df77b0aef56f85eeaeb49bfd971d0fbb98cf73b260aae2f51f0`。
- [原native coverage artifact 13112406351](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41376852060/artifacts/13112406351)：ZIP SHA256 `75695112e4bc62e82b8adb079372e50d4bc844926f2f66c9ed0a01731b810c6f`。

可重現雲端復驗指令（各命令完整cwd／env／raw hash保留在核收收據）：

```sh
python3 -B tests/native_shard_receipts.py --input <下載的三片原JSON> --parts 3 --output <新輸出.json>
python3 -B tests/native_sharding_mutation_check.py --output <新負控制目錄>
python3 -B .github/scripts/mutation_evidence.py verify --artifacts <七片下載目錄> --out <新輸出目錄>
```

[完整核收紀錄與PROGRESS](https://github.com/ZhiQiYang/geometry-axiom/tree/6cd080a6e1404c7370afd5e31c543040c62fe930/evidence/cloud-resume-20261102) 已普通推送，保留正式head、合成execution與各原件身份。原df347及更早來源僅為歷史，見既有完成留言，不作本矩陣的新head證據。

依GitHub官方事件規則，`workflow_dispatch`須workflow先存在default branch；本機Claude已正常採入。現已實際觸發[手動run41397499686](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41397499686)，ref `codex/canvas-validation-20261102`／head76d311cf，原POST與讀回紀錄已保存。完整結果已核，收據見[固定E](https://github.com/ZhiQiYang/geometry-axiom/tree/e9152ea6c0ef8ab57611a6a86edf0416b464074a/evidence/cloud-resume-20261102/canvas-sharding/manual-mutation-S)；本輪沒有修改default branch／安全政策，原PR事件驗收的execution不改標。
