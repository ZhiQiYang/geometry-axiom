保留核心K＋矩形格網的有限建置與木工include具名反證，將來源以一般merge收斂最新main。

完整current head：**edf556eedc204bb285fb4504e246e4310f4e1e88**。base **main**；已一般merge精確 e02057b4c725d6f03ae52c3bc30776bf9442b0cf，再採正式重產原件。**VALIDATED-WAITING-REVIEW：當前F驗收齊，待最新獨立審查；沒有合併批准**；只一般merge與快轉推送，Codex未合main。

| 唯一current-state gate | 真結果／execution與界線 |
|---|---|
| 最新main合流source M | aca3d2a5f604848b159a0e5cdd3d3f55fcad190f；root與獨立peer記錄parent／逐leaf閉包，main產品與新回歸完整保留。不是rebase／force |
| #366整份重產 | [run41430549123](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41430549123)，event workflow_dispatch／attempt1、10/10success；9原ZIP/cache byte校驗，原verifier真exit0、official ledger與summary逐byte相同，下載ELF執行0 |
| 本次正式ledger | **已採入tracked tests/mutants_results.json**，SHA256 140c09ce899cb5b35df82b9b3f854e4a01f3557a8d06b3f41d37c891d37b72ef；123＝114killed／1crashed／5equivalent／3retired，其餘stale/blocked/survived/invalid/unrun全0；七個badcache負控各strict1。120個active execution.head仍全部M，不改標F；M20仍crashed而不是assert-killed |
| 架構正式產物 | 採該run原scan/report/receipt，manifest保持原policy input；scan本來就與原件相同。M→F實際只ledger、PRODUCT-ARCHITECTURE.md、receipt三leaf改變；C/H/JS/Python tests、expected、judge、policy全同M |
| F新原帳本check | **已實跑**`python3 -B tests/mutate.py --check`，exit0，無stale／blocked／survived。此為正式新ledger的check，不拿舊有效檢查代新採入 |
| F架構三條原裁判 | **已實跑全0**：`python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`；`python3 -B tests/test_architecture_contract.py`；`python3 -B tests/test_product_architecture.py`。新receipt真execution仍M，未改stamp |
| 前輪正式結果 | M正式integration41430557786十項全success，真checkout afa52541ef2bcdd00e184e0f5d0d5e33874610ed與M同tree；237native／5420pass／1原GDI，fullcanvas2286/86golden、5其他browser全綠。原native CLI原件復驗0／summary逐byte等官方；明確是M的執行，不冒F已跑。 |
| 新F正式integration | **已實跑10/10 success**：[41438184818](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41438184818)，真正checkout **27feb429dd4690097bb3d330b2fbbc62c3619636** 與F同tree；12ZIP/API digest、10完整log全核，原native CLI復驗0且summary逐byte同官方。237/237 suites、5421counted/5420pass/1原GDI；fullcanvas2286pass/0fail/0skip、86golden精確全等，5其他browser成功；P38原預期例外1，不稱所有assertion為trusted-input E2E場景 |
| 重產與重跑界線 | M→F只有ledger/report/receipt三個derived leaf，產品碼、測試/裁判原始碼、expected與policy同M。刻意更新的derived資料在F以原check與架構三條重驗全0；不是宣稱其bytes同M舊檔。120execution仍M，沒有第二輪123或改stamp |
| 合併判斷 | **驗收齊、交當前F最新獨立審查**；目前舊ChatGPT審查仍綁049，不冒稱已批准F。待新審查可合才READY-TO-MERGE，由本機Claude合main。#339已merged，340合後下一張341；Codex不合main |

[已發布證據總索引與歷史原紅](https://github.com/ZhiQiYang/geometry-axiom/tree/8a1bd9245ee3cda589f81dcf872b6e10caa299ff/evidence/cloud-resume-20261102)。新sourceM/F的整份原ZIP/cache、全量ledger、三條架構stdout/stderr及F真正10CI原件已在這個固定E持久交付，push與remote SHA已核；沒有用SHM本機路徑冒充已推送。

#339已合main；#340合後按341→342→343→346→347→348推進，不把來源祖先已在main當成缺的效能／whole-opt驗收完成。未放寬斷言、golden、時限、允許skip；未改公理層、閱讀器、決策佇列。

[當前F原件](https://github.com/ZhiQiYang/geometry-axiom/blob/8a1bd9245ee3cda589f81dcf872b6e10caa299ff/evidence/cloud-resume-20261102/pr340/integration-final-F/FINAL_ACCEPTANCE.json)；[獨立完整M/F peer](https://github.com/ZhiQiYang/geometry-axiom/blob/8a1bd9245ee3cda589f81dcf872b6e10caa299ff/evidence/cloud-resume-20261102/pr340/main354-final-peer/REVIEW.json)；[七組原badcache log補核](https://github.com/ZhiQiYang/geometry-axiom/blob/8a1bd9245ee3cda589f81dcf872b6e10caa299ff/evidence/cloud-resume-20261102/pr340/main354-final-peer/BADCACHE_ORIGINAL_LOG_SUPPLEMENT.json)。peer全讀9ZIP98.7MB及905innercache195.6MB，未抽樣或exec。架構是205＋22/610inputs/339owned/271exclude/812edges。原receipt adoptedMain=8f82b207e87c086705a1d8b7a00e2f215c07cbcf為工具歷史錨點；本次Git main=e020、sourceHead=M、產品head=F，原欄值不改寫。Canonical current-state在此E的PROGRESS.md；舊evidence/geo340-convergence-175cee44/只是歷史。
