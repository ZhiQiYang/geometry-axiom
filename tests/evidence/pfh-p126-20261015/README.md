# P-126：正典同步與完整原生驗證完成

2026-10-15 11:57:46 UTC+8。固定受測head **`f6d128ac90ef0e028b5bf8f56e93847b14dc5c10`**；後續交付commit只封存證據，不冒稱是實際受測SHA。產品最後變更85851559，C／includes／測試／expected／突變收據本輪未改。

| 實際執行 | 結果 | exit |
| --- | --- | --- |
| 官方同步器原位重產 | 7增7刪、84patch markers；完整authored state全等 | 0 |
| `sync_axiom_reader.py --check` | 五道assert／獨立SSOT通過 | 0 |
| 原 `python3 tests/test_axiom_reader.py` | 41／41，無skip，189.723秒 | 0 |
| 固定head完整 `python3 -u tests/run_all.py --build` | **89 suites，2858題：2857過／0失敗／1允許略過** | **0** |

完整native耗時 **982.245369秒**，16MiB stack、Linux-6.18.44-x86_64-with-glibc2.41／GCC14.2／Python3.12.14／Nodev24.19.0。沒有allow-skip、count drift或未登記測試；唯一略過為Linux不具Windows GDI contract harness的具名平台允許項。宿主32／32、原reader41／41、子格31／31及核心143／143在此完整native再次執行通過。這是雲端advisory，不是正式WSL收據；aggregate外的必要owner／browser整合沒有算作已驗。

Claude [P-126／6183800777](https://github.com/ZhiQiYang/geometry-axiom/pull/227#issuecomment-6183800777)明確授權#227不再等#207，用既有官方同步器在包含PF-H來源的本分支原位重產；沒有手套diff、手改HTML或新增第二份閱讀器。
實際生成patch SHA256 **`296192fc7f0410bf4836e8fc768b9d812a482222bdf67593c7f1f3b65b69f8e1`**，提交前後皆與指定推演完全一致（postcommit.json）。唯一正典SHA256為 `15875c5532568f7b976711c0edce44d2134ab2647dcd0356b8baea6233059b40`。SSOT、白話、BACKLOG、決策佇列逐byte不變，整份authored state（條文／blocks／批註／草稿）全等。

依P-126維持前輪11步控制與50筆突變報告：固定48a02205的32綠→八項領域斷言紅＋一項子格堆疊撤回紅→還原32綠；正式突變42killed／1crashed／4equivalent／3retired，47支實際執行檔、三份143／143baseline、check0及48份sidecar。M20與堆疊撤回的原生-11和斷言kill分列。未冒稱本輪重新執行這些控制／突變；本次完整native在起跑前不存在的獨立cache再次驗證既有突變收據有效。
前輪目錄 `../pfh-native-20261015/` 的 420 個manifest檔案逐一SHA核對未變，六紅／等待裁決僅屬當時48a02205的歷史狀態。本輪官方同步改動已使實際正典及完整native全綠。

本輪全部 **15025** 個tracked一般檔案兩端hash相同、未排除任何檔案，head不變，結束工作樹乾淨；這是端點查核，不宣稱連續監視。來源快照在native/tracked-snapshots.tar.gz；204個本輪原日誌逐成員SHA核對，archive SHA `072ede1723b0c9c92adc54f5ee003a5595118d386b4c3f50a922d923fe40e358`。binary／sidecar、reader／GDI／host原JSON與實際exit／耗時均保存。

正式WSL七項未跑／未排，PR保持draft，不宣稱可合併。GitHub同受測head的CI結果與annotation另存native/ci-*.json；環境阻擋與本地測試結果分列，不修改設定。上列車依P-090/P-105在合併樹再次使用官方同步器重產；#207日後合入同樣處理。

#221真宿主／原生板片與D7足跡／source-only保存重開、測試端R43的5／3／3與原純算法3／1／1原件仍見前輪witness-final。PF-3產品support/effectiveSeams仍另案，未冒稱產品R43已接入。完整性以final-manifest.json及delivery-audit.json重查。
