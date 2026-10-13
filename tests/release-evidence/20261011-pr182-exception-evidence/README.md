# PR #182：cause 必須來自同一筆具名終端例外

回覆 ChatGPT `6114278460` 與 dot `6114484589`。裁判與測試提交／乾淨受測 head：`151da30ff2da765dd1cfff0a4c0d4a3307a028c0`。交付後續提交只加原件／導讀，未再改裁判、產品或測試来源。

## 真實負例與測試先行

`before/receipt.json` 綁定前版 `f2d332be37eb9c4d66d5c2c82edd72e966f91f5a` 加未提交對抗測試的來源；不能稱乾淨 f2d 實跑。真基準 bridge 的原 `test_panel_strict_width_fixed_spec_and_long_run` 僅被對抗探針攔截 read 回覆並移除 `rect`，原方法因此得到 `KeyError: 'rect'`、child exit 1／ERROR 1；板厚 cause 只出現在 traceback 顯示的 assert 原碼。舊 `verdict` 卻判 killed。沒有修改產品或宣稱真 SPM08 當時誤報。

`after-final/` 在乾淨 151da30 重跑同一探針：同樣 KeyError／exit 1，結構化終端訊息只有 `'rect'`，裁判不再判 killed。它的 `crashed` 標籤沿用 gate 的「無允許例外」分類，並非宣稱 binary SIGSEGV。

首批 24 方法（原選集 9＋新 matcher 15）先在舊產品裁判實跑，12 個斷言失敗，exit 1；原 log 和實際測試 bytes 保存在 `before/guard-before.log`／`test_section_profile_mutation_check.py`。後續另加完整方法身分負例及四項真 child collector 檢查，最終為 29 方法。`checks/` 在乾淨 151da30 實跑 29/29、exit 0；原 `run_all.py --only py:test_section_profile_mutation_check` 同樣 29/29、exit 0。expected 只增加該 suite 9→29，沒有改原 83 suites 期望或冒充新完整 aggregate。

## 結構化裁判

新增 `section_profile_mutation_runner.py`，使用 unittest 的 `addFailure`／`addError`／`addSubTest` 保存完整 parent test_id、subtest_id、kind、module-qualified exception_type 及未截斷的 `str(exception)`。原 stdout／traceback 另外保存，無法供 cause。SPM38／SPM40 明列允許 `modeling.common.ModelError`；其餘 ERROR、stdout／traceback source／其他方法、分散在多筆子例的 cause 都不能算 killed。

檢查 requested／executed／passed 身分、實際 testsRun／failures／errors、子例歸屬、缺漏／重複事件、JSON 重複 key、型別與 code=0／1 的一致性。缺漏、格式錯、skip／expected failure／unexpected success、實際 exit 與計數不符都受阻，無舊 log fallback。完整多行 AssertionError（cause 超過 300 字元）仍能偵測；first_failure 的 300 字元只是顯示，不參與裁判。

`matcher-proofs/` 在子行程對真正 gate 函式做單點故障注入，未改 checkout：

| 狀態 | 16 方法的 failures／errors／skip | child exit |
|---|---|---|
| 現行 | 0／0／0 | 0 |
| 恢復 f2d 原整份 log matcher | 13／0／0 | 1 |
| 只把 cause 改回搜尋 log | 3／0／0 | 1 |
| 只拿掉完整方法綁定 | 3／0／0 | 1 |
| 還原 | 0／0／0 | 0 |

`child.py`／driver／精確 matcher 和測試 hash、全部 stdout／stderr／直接 exit 收據保留。真 ModelError 的完整型別、多行訊息及子例各自事件另由實際 Python child fixture 驗證。

## 原完整 42 案閘門重跑

原完整 42 案閘門重跑：41 killed／1 equivalent，直接 returncode 0、196.82 秒；native 基準 25/25、model 基準 19/19，零 skip。

原 `python3 tests/section_profile_mutation_check.py --receipt … --logs …`，default jobs=4、原時限、原 native／model 方法及 cause 都維持；native 37 個 C 故障、model 5 個 Python 故障，未刪案例。結果 JSON 使用 `section-profile-mutations/2`，保存完整例外記錄及基準線；原 traceback 和每次編譯指令／實際 exit／stdout／stderr／source tree／binary hash 都在 `full-gate/logs/`。model 使用 fresh 未變異 model-base；沒有變異 adapter 比較。

SPM41 仍用丟掉恰一片正面積差集的故障，保留 I44 精確 outsideRegions／繞向／材料側貼緣裁判。SPM08 真 AssertionError、SPM38／40 真 ModelError 及 SPM41 真 AssertionError 的新例外與 raw 独立保存。來源／判定／binary／adapter／sidecar 在 checkout before／after 同一，開始與結束乾淨。這只是雲端獨立突變閘門；不稱 WSL、強制排他、正式七 job、完整 AC16 或 full aggregate。

## 保留的歷史與未完成項

前輪 SPM41 原 #182／僅覆疊 #192 兩函式的 0／1／0，與舊故障整合後 0／0／0，都保持原件；共享函式探針不是 #192／#202 完整整合树。舊 39 FAIL＋2 ModelError ERROR＋1 equivalent 只是歷史原件的分類，沒有用這次新裁判替歷史全部 log 補證；新 42 案是不同版本的獨立執行。

歷史所有 raw／JSON／tgz、舊導讀與清冊保持原 bytes。aa4067b 的正式 WSL 6/7 綠、canvas `Rule line control unreachable #igNewBinding` 首紅仍有效；尚無同 head／main 合格根因對照，不宣稱 flaky。native 歷史 1202 秒超原 CI 900 秒的界線保留；正式驗收依 CI×3／排他規則，由原本機 owner 交最終完整 SHA 七組收據。本輪沒排七 job、不合併。

AC23 仍被原閘門排除，AC04–06／AC24 是相似數值，完整面材上限移除仍缺獨立案例；不宣稱完整提案 AC16 已結案。Windows／MSVC、最終整合 SHA 的 native／browser／GDI／七 job 未驗。

產品 C、INC、原 native／model 方法、公理／白話／正典／🔒、產品 UI 與核心 `mutants_results.json` 未改。C 13,047 CRLF、零 bare LF／NUL。核心帳本來源鮮度再核 exit 0、40 killed／1 crashed／4 equivalent／3 retired、stale 0；用工具既有 MUTATE_CACHE 指向不存在的獨立 cache，未刪共用 cache、未重跑核心 48 案。前輪共用 cache 45 stale 首紅保持，不拼成全量綠。

`SHA256SUMS` 列出全部 payload（不自雜湊）；`closure.json` 綁定實際源碼、受測 head 與歷史不變的驗證。`executors/` 保留實際 driver；不提交執行檔、產品 C 快照或 HTML。託管 CI 受帳號計費阻擋；正式合併仍由本機 WSL 收據裁判。無新 UI 入口，維持 draft。
