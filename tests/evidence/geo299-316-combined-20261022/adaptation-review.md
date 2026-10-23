# combined 固定來源的有界純文字覆核

覆核來源為產品／tests P `6366304eb787b2a50282e4132f45e51eb7d21290`，對照整合 F2 base `4b665fae21ab63aaffb7d84f6a32d5a469ba1675` 及 handoff 的原完整 combined `patch.diff`（SHA256 `422946025137ba719ef4e42da1a527ba5bc07bbf8e52b28e687392061074fef6`）。另讀 `closure-review.md` 與 `static-inspection.json` 作既有盤點的交叉參照。

本子任務只有固定 Git blobs、差異與文字檢視；沒有編譯、測試、架構掃描、效能量測、Git 寫入，沒有修改 repo，也沒有操作正在跑的 native。唯一輸出是本檔。parent 已回報的 core166／新雙面正例真綠屬原 native 的結果，這裡沒有重跑或另立動態結論。

## API 與呼叫者

`wood_member_span_extension_check` 的宣告 `contacts.h:16`、定義 `contacts.c:8` 均是9參數，新增 `int edge_index` 在第三參數。唯一產品呼叫 `contact_world.c:145` 也是9參數，第三參數為從 `wood_contact_boundary_edge` 得到的 `edge_index`。找不到仍按舊8參數呼叫的產品接點。

`tests/geo261_contacts_harness.c` 的12個呼叫在 P 的41、44、46、47、48、51、52、54、57、166、186、219行，均為9參數，第三參數皆為 `EDGE`。凍結裁判仍名為 `frozen_span_extension_check`、維持其原簽名，不是漏更新的新 API caller。

`wood_contact_boundary_edge` 將舊 interval 本體保留，只在成功寫完兩個既有輸出後，於非 NULL 的 `out_edge` 寫入定位邊。失敗路徑仍在寫輸出前返回；舊 `wood_contact_boundary_interval` 是以 `out_edge=NULL` 轉呼叫的薄包裝。owner-extension 仍有真內部 caller，沒有被誤退役。新 span 的 has-edge／role／範圍裁決守衛沒有改；新增低／高 note 各依真正超出條件列印，沒有把錯誤訊息變更混成裁決放寬。

## F2 增量保真

在固定 blobs 逐字比較（CRLF→LF規則只用於文字同一性）得到：

| 區塊 | 實際比較 |
|---|---|
| `contact_world.c` 的 `ContactOrderIndex` 起點，至整個 `wood_contact_collect_stops` 結束 | 5,634 bytes 全等；SHA256 `40572086a532ecfedd80d64b7980def9d3138bc3c0727e1e7cb73c92f45984b0` |
| `current_geometry.c` 的 `app_contact_facts_prepare`、raw callback snapshot與wrapper，到resolver定義前 | 2,506 bytes 全等；SHA256 `d1a9d30e076a21a0dae2e778445031f3f77207c8fb8555ed60c25cdfab53de20` |
| `geo261_host_facts_authority_harness.c` | 僅一個 V_EXTENSION 完整字串增補定位邊與超出區間，其他 bytes 正規化後全等 |

因此 last／minimum、重複 ID 的最後排序／最早遮蓋、equal-order穩定與容量 fallback，及 F2 raw snapshot／prepare／wrapper 都沒有被原草稿覆回舊版本。Python 仍保留 wrapper 精確轉呼叫 prepare、實際 member 身分斷言，以及 `index->minimum[slot]<order`→`<=` 的原 `equal-order-not-deduplicated` 控制。

`current_geometry.c` 的其他實作差異只有三個死 H wrappers 的移除，以及放置時 I11 三檢查點的說明搬移／補充；沒有看到新的守門呼叫或調整其時點。W 死 footprint API 的移除範圍，與先前完整190個既有 manifest C sources及quoted include盤點得到的零活 caller 證據一致；不把該靜態證據冒稱為 C preprocessor或link-time證明。

原完整 combined 的 manifest hunk沒有套回來。P 保留 F2 四檔，新增／退役識別字留待實際完整 W 來源機械重算；這是尚待完成的衍生產物工作，不能由本次文字覆核宣稱架構收據已更新。

## 唯一已知測試順序缺陷與最小修法

P 的 `geo261_contact_world_harness.c:72` 新增 `boundary-edge-failure-leaves-outputs`，放在原 `i5-notched-footprint-deferred` 前面。`complete-footprint` 控制撤 `contact_contains` 後，新斷言先正常轉紅；Python仍要求原 I5 marker，所以整個控制的 marker 斷言失敗。這是已觀測且 parent 已保存 raw 的問題，不是新增的純文字推測。

建議只把下面一條 failure-output 檢查搬到原 I5 CHECK **之後**，其三個輸出 sentinel 在新小區塊內重新設定；水平／垂直 index與NULL-index成功檢查維持原位置。示意位置如下，全部原斷言與判式均保留：

```c
    /* 原成功的 horizontal／vertical／NULL-index CHECK 保留於此。 */
    lo=-999;hi=-888;CHECK("i5-notched-footprint-deferred",!wood_contact_boundary_interval(&b,false,0,100,50,60,&lo,&hi)&&lo==-999&&hi==-888);
    {int edge=-7;lo=-999;hi=-888;
        CHECK("boundary-edge-failure-leaves-outputs",!wood_contact_boundary_edge(&b,false,0,100,50,60,&lo,&hi,&edge)&&edge==-7&&lo==-999&&hi==-888);}
    CHECK("interior-has-no-positioning-edge",!wood_contact_boundary_interval(&b,false,10,40,10,20,&lo,&hi));
```

這樣原 I5 控制仍先命中原具名 oracle；新增 failure-output 合約並未刪除。原 I5 行自己會重設 `lo`／`hi`，所以仍放在它前面的 NULL-index成功呼叫不會污染它。相反地，若把整個新增 block 搬到 I5後面，必須在成功呼叫之後再將 `lo`／`hi` 重設為 `-999/-888`，否則後面的 `null-boundary-output-preserved` 會因fixture已變成 `50/100` 產生假紅；只搬一條比較不容易改到既有fixture生命期。

修復後仍須保存原完整 W suite／負控的真輸出，並做「撤這個順序修正→同一正常具名紅，恢復→綠」的自證。不能用更改 Python預期marker、刪 CHECK、放寬結果或編譯失敗代替。M97／M98兩個產品突變仍須各自真跑，不能從新雙面正例已接受就推為 killed。

## 覆核結論與邊界

在上述有界範圍，沒有找到已知 fixture 順序問題之外、可由固定文字直接證成的新移植缺陷。新增訊息長度、derived-fill診斷的既有 edge-index慣例、完整 native其他項與負控牙齒仍由原動態裁判及既定設計邊界判定；本檔不設定新門檻、不改公理，也不替尚未完成的執行填綠。
