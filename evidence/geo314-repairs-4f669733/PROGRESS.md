# #314 集中修復診斷

產品／測試 P3：`4f669733282613a6f1e4a627c448374716496daa`；實際 checkout E：`c0a2007898f544e658efa72b9b51528a03f7ce51`。P3→E只有evidence新增，實際測試／編譯來源逐blob核驗相同。本輪是受影響診斷，非最終SHA完整驗收。環境缺料retry另綁P2，不混標P3。

| 項目 | 真結果／控制 |
|---|---|
| candidate 原26 | 26/26、exit0，原全部成本／ASSERT不變。68次compile/link全0；414真輸入逐bytes等P3。 |
| candidate：原replay-operation | 只撤新增語義欄初始化（count/steps/seal），0→1→0；原 `ASSERT:file-replay-frame-final-seal`，無crash。 |
| candidate：原default-cost | 同樣只撤新欄初始化，0→1→0；原 `ASSERT:default-evaluation-succeeded`。原固定9行與P177數字未改；不是另撤memcpy的控制。 |
| candidate：原default-scratch-oom | 同樣只撤新欄初始化，0→1→0；原 `ASSERT:default-final-seal`。 |
| reader 原51 | baseline51/51、恢復後51/51，全exit0無skip；原同步器check前後0。 |
| reader撤回／恢復 | 唯一canonical換回舊bytes，原 `test_rebuild_is_byte_idempotent_and_keeps_reviews` 正常AssertionError：0→1→0；恢復後完整原51再綠。 |
| Node環境retry（P2） | 三份既有ZIP由P2 exactblob補齊；原兩檔94/94、exit0無skip，原reaper完整回收。 |
| ASM原完整tool、unit12、anchors3 | 三項原裁判全exit0；原3cases真exact-assertion killed、6controls正確not-killed、restored與baseline binary相同。外部錄製driver因同時更新tracked evidence/PROGRESS觸發寬clean guard真exit1，原1保留不改綠。另readonly classification真0：2187個archive原bytes／manifest／P3 blob／當下source完全相同，原raw hash核同；這不是外封裝整體通過。 |
| graph5環境retry（P2） | 原完整5/5、exit0、fail/error/skip皆0；原contact負控真baseline→mutant拒→restore綠，64compile/link全0、191個實際build檔保存，contract與ledger都不變。 |
| 架構三條 | 原scanner exit0、原test_architecture_contract 205/205 exit0、原test_product_architecture18/18 exit0；完整五roots／三standalone不縮，真P3 manifest使用於實際checkout E9f634cd0。四檔receipt重產仍屬ledger後續。 |

## 修正範圍與原raw

candidate witness仍先把operation全填A5，保真正padding、boundary id91與26原ASSERT／成本，只初始化新增且有語義的空facts欄。沒有改產品fail-closed判準。此證明不包含額外default operation memcpy撤回：固定9行本來不改operation的情境可等價，不能冒算killed。

首次candidate-repair-001在額外版本採集階段，Python Popen因PATH缺google-chrome拋ENOENT，沒有啟動Chrome、沒有Chrome的127退出碼、未compile或執行產品tests；外層driver／reaper真exit1原收據保留。002只在launcher PATH加既有env/bin後另跑，Chrome156.0.8078.47／Node24.19.0真版本0；另以絕對 `/workspace/geo261-environment/bin/google-chrome --version`真0補錄，未開瀏覽器。001與002分開，沒有改舊收據。

所有有子程序／負控制都包原 `/workspace/geo261-environment/reap_children.py`；本輪root明確允許與323非量測native並行，使用外部私鎖 `/workspace/geo314-work/private-diagnostic.lock`，不是R3正式量測鎖。canonical只經原同步器機械更新唯一檔，公理層／guide白話／決策佇列／BACKLOG bytes都逐P3 blob核驗不變。原指令、完整raw、環境、rc、真checkout／product SHA、來源／objects／binary／buildlog都在對應tar；PUBLICATION.json列逐包hash。

本輪所有原裁判診斷已終態；ASM外封裝1明確保留，最終F另有正式驗證。最後只補mutate.py總說明精確列出已實作的tests/*.c與巢狀scene oracle閉包，沒有改函式、判準或測試數；與本輪全證據一次固定乾淨source S並普通push，再以此完整40碼SHA整份原mutation ledger。S在ledger全終態前包含evidence都完全凍結。完整native／browser／專項／效能仍屬root最終SHA驗收，不以本輪診斷取代。不force push、不合併。

主worktree四既有fixture已於E9f634cd0逐exactblob驗同（本來就存在），skipflags與trackedstatus完全未變；最終F仍需對最終blob重核，不借P2環境retry當正式F結果。新docstring只準確描述既有實際oracle，不放寬C／nestedfixture freshness。
