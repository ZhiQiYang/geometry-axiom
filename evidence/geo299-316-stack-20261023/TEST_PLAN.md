# combined 合流後的精確驗證計畫

本檔僅是未執行命令計畫。測試槽由主代理排程，執行時持有 `/tmp/g261r3/heavy.lock`，同時最多兩個一般工作、canvas 單跑。現階段不取得鎖或等待重工作。

先一般 merge #314 已推送分支（該分支含 #323），保留本 combined 原分支。確認 `公理層.md`、`決策佇列.md` 只有前棒已授權／main 合入的 bytes；本棒不改字。`current_geometry.c` 以 bytes 驗 CRLF。ID 聯集保留 M89–98 與 #314 M99 起既有編號，不能重排成撞號或讓新 guards 靜默消失。

合流後固定 source SHA、記錄 clean status、所有 commands/environment/版本/完整 top-level stdout/stderr/exit。私有 TMPDIR/TMP/TEMP 與 cache 路徑以唯一 label 建立，不使用其他 agent 的暫存。可沿原 `test_entry_full.py` 跑 unchanged 原 entry，保 NativeBuild build-log 與生成來源／原 subprocess 紀錄；若有原 inner stream 未捕獲，據實列出，不以 hash 冒原 bytes。舊 runner 沒有新 R3 鎖，不能直接無鎖啟動。

第一組必要原 suites（依原入口、不改 assertion）：

```text
python3 -B tests/test_geo261_wood_contacts.py
python3 -B tests/test_geo261_wood_contact_world.py
python3 -B tests/test_geo261_wood_world_validation.py
python3 -B tests/test_geo261_host_facts_authority.py
python3 -B tests/test_geo261_contact_sources.py
```

contacts 的具名 controls 原本即 baseline 0 → mutant 正常 ASSERT/exit1 → restored0；contact-world 同樣包含 `edge-index-output`、owner-extension 真 product 路徑與 I5 precedence；world-validation 包含 same-host／placed 篩選與真 host selector 反證。只統計原實際採樣到的 controls，不稱這些等同整份帳本重產。

core 場景需由原 scene runner 驗 `_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`、`_role_priority_mutant.scene` 及 `_i11_two_surfaces_same_uv_accept.scene`（實際入口依合流後 registry 原 keys）。M89–M96 對診斷欄位有牙齒，M97／98 對 H／W 同承載面篩選有牙齒；如合流新修正影響其中任一 closure，附同一 source 的精確撤回／恢復 0／1／0，測試正常斷言失敗才算反證，編譯／啟動失敗不算 killed。

架構先跑原三條，原紅保留。manifest／scan／report／receipt 的真 sourceBaseHead 不能改成較後保存提交；有新來源／derived 改動由共同棒序協調，不能把一側舊 receipt 當新 closure 完整證明：

```text
python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json
python3 -B tests/test_architecture_contract.py
python3 -B tests/test_product_architecture.py
```

本棒若 registry／追溯已合併，僅以原同步器更新唯一正典，再跑 rebuild／check／完整 reader tests；不改 SSOT，不手工重寫 HTML 資料：

```text
python3 -B geometry-guide/sync_axiom_reader.py
python3 -B geometry-guide/sync_axiom_reader.py --check
python3 -B tests/test_axiom_reader.py
```

`python3 -B tests/mutate.py --check` 只驗 freshness，若 stale 就記原結果與原因；本代理不產新全帳本。完整 native／六 browser 與其他正式清單由最終堆疊閉包及主代理排程確認，不把歷史 F5bf 或 #288 F13 收據改標為新 source。
