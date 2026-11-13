# GEO-261 assembly guide 上游修正的回歸守門（Topic 03）

**產品缺陷已由上游 `1987af50` 修正；本分支只強化既有測試。** fresh基底e9的原四方法已全過，不能把這輪before綠稱為產品修前紅。保持強化測試、只撤上游七行，四個TestCase都在讀取真bridge references後的近因斷言轉紅；恢復相同產品與測試後四方法全過。

分支：`codex/geo261-fix-assembly-guide-regression-20261018`；基底 `e9c1509cf89e6f35d298743ec5e3368370316cf7`；唯一測試修正 `97bc7c0cf612b7bbbb4362e27441579a97aa3a00`；本地撤回控制 `6360f8e5f0b81bd99e3b149281219b4a7aba58b4`。正式修正只有 `tests/test_assembly_candidate_impact.py` 增19行，不再加入舊03替代產品patch，也不推撤回控制。

## 根因與回歸要求

同一candidate graph中，assembly先讀guide後已有memoized值；`reference_rebuild`重設resolved flag，再讀guide時K直接回cache，provider沒有再次執行寫回，於是JSON曾輸出null。上游七行在`reference_guide_position`取到合法position後，只於非current-values模式、stored尚未resolved且stored offset等於回傳coordinate時恢復flag，保留其他cache與唯讀模式。`geometry-core/references.inc`本輪完全不變。

新增斷言要求load後四guide是dict，精確座標為1:v500、2:v2500、3:u1500、4:u1000；preview before等於live guides，preview after完整可解析，confirm後仍精確對上。四個原test方法AST逐一相同，原41個assert*呼叫的多重集合全保留，增加至48（包含assertion helper呼叫，**不是runtime斷言執行次數**）。原取消、stale、非法候選、undo/redo、生成與移除的斷言沒有放寬。

[固定Git／AST／來源核對](readonly-review/source-review.json)；[測試增補patch](readonly-review/test-strengthening.patch)；[上游原七行](readonly-review/upstream-1987-seven-lines.patch)；[本地撤回patch](readonly-review/withdraw-upstream-seven-lines.patch)。原／恢復產品檔raw SHA為`3695ab9844a80cf0041d2a6a67e2be96bf6ecbcd59709759d1add4822b70077c`；撤回後該檔等於e64的`93792ba864200a88d723fd5fa93d6464ce17e17b6ab0165ea80897d35f7dd094`，但**整個撤回提交不等於e64**。

## 四輪真結果

四輪均使用同一argv：`python3 -B -u tests/run_all.py --build --only py:test_assembly_candidate_impact`，stack16MiB。只選此suite，不是全量驗收。

| 階段與原件 | SHA | 結果 | unittest／suite JSON秒數 | outer秒數 |
|---|---|---|---:|---:|
| [before原套](before/suite-logs/py_test_assembly_candidate_impact.unittest.log) | e9c1509c | 4/4通過，零skip/error | 3.593／3.70 | 29.873039 |
| [after強化](after/suite-logs/py_test_assembly_candidate_impact.unittest.log) | 97bc7c0c | 4/4通過，零skip/error | 3.987／4.11 | 4.654592 |
| [withdrawn只撤七行](withdrawn/suite-logs/py_test_assembly_candidate_impact.unittest.log) | 6360f8e5 | 4個setUp assertion FAIL；body0，零error/skip | 3.234／3.35 | 32.683293 |
| [restored相同97bc](restored/suite-logs/py_test_assembly_candidate_impact.unittest.log) | 97bc7c0c | 4/4通過，零skip/error | 3.607／3.72 | 32.088665 |

撤回四個原文皆為`AssertionError: False is not true : GUIDE_SOURCE_CACHE_MUST_SURVIVE_REBUILD:`，後接完整真列表：前三個guide是`None`，第四個仍為id4／u1000的完整dict。每次trace都是`setUp → assert_resolved_guides`；unittest計testsRun=4並歸FAIL，但四個方法本體尚未開始，不能說四個完整功能流程跑完才紅。這是有效的近因產品撤回控制，並非setUpClass/import error、編譯失敗或timeout。

四輪command/process、完整三份suite logs及runner JSON均保存；三log皆由本輪stdout宣告且mtime落在當輪，沒有拿前次綠檔冒充。來源／HEAD／status-diff穩定，退出碼分別0/0/1/0。詳見[人工台帳](readonly-review/manual-ledger.json)。時間只作功能收據，outer包含建置；after可重用同C binary，前後秒數不能作效能倍率。

## 歷史e64與G07邊界

歷史 `e64aa6359d600f43313ec9d7ba1112c465b6a40c` 原suite為4run、1pass／3ERROR，unittest20.738s（JSON21.37s）：三個`TypeError: 'NoneType' object is not subscriptable`在方法本體後段確認時讀`g['id']`，原取消方法通過。[歷史原log](readonly-review/historical-e64/py_test_assembly_candidate_impact.unittest.log)與[原JSON](readonly-review/historical-e64/py_test_assembly_candidate_impact.json)逐bytes複自封存baseline；它們是歷史證據，不是本輪重跑。新setUp守門故意更早定位，因此四個新FAIL不能與舊三個TypeError合稱同一收據。

G07相同上游機制的真browser因果已另行發布於[既有獨立報告](https://github.com/ZhiQiYang/geometry-axiom/blob/eb74dbce4ff42830a47a0da02f898b18e939f69a/evidence/geo261-codex-g07-upstream-cause-20261018/README.md)。本題沒有重跑browser，也不把該既有報告改標97bc來源。

## Binary、環境與公開範圍

每輪after registry的bridge均fresh；before／after／restored的bridge SHA相同：`3e7ee9ec03f04c9238330e45320adae27ca109667e17842825b98cd677561f03`（1078840 bytes）；撤回為`1a3e5775b1a66567c1debe639842eb78c2e2e240e1e5e7b80a8a5d3c636fee76`（1078840 bytes）。withdrawn與restored真重建對應C來源，不能沿用控制binary。其他未使用core/model-base可能stale，不拿它們當本suite執行身分。

環境為Debian GNU/Linux13.6、Linux6.18.55 x86_64／glibc2.41，gcc14.2.0、Python3.12.14、Node24.19.0、Google Chrome155.0.8059.84（Chromium154.0.8037.57亦安裝），stack16MiB。各輪工具版本原文保留；Chrome版本不代表本輪browser執行。

公開資料含外層raw、每輪suite原始三logs、版本、持久binary資訊／sidecar與固定Git差異。沒有另外旁錄全部bridge protocol，也不發布ELF；不能把suite assertions當額外公開的子程序raw。大型before/after.source.json與recorder原碼保留外部，公開receipt只轉錄原身份，公開包不能自行重算未公開的完整來源清單。共用collector只核原件身份、不自行判pass／kill。

## 未驗項

本題未額外跑較廣current-cache／world-cache-decoy與candidate專套（`test_assembly_generation`、`test_reference_contract`、`test_geo261_native_guides`、`test_geo261_host_candidate`、`test_geo261_staged_candidate_graph`、`test_geo261_native_sources`、`test_geo261_linear_definition_graph_product`）；也未跑全量run_all／全部browser／完整mutation。四方法數不變，不需本題修改expected census。最終合流若採用不同產品／測試bytes，仍須同來源驗收。
