# #318 Caller 整合備忘（尚未改產品）

本文件供取得 combined 真交棒後實作，不代表已完成。固定閱讀來源為 integration `22ad28f3`／#323 `5c29eba3`，之後必先普通 merge 前棒並重新讀衝突處。

## Contact policy

`native_boundary_end_candidate.c` 是 `contact_world.c` 的 repo 外候選，需加公開 tri-state enum/API 到 `contact_world.h`。保留原 pointer identity 與 ordered-fact 語義，不新設 duplicate-ID 全域假設。接觸面位置來自返回 FEATURE，owner 的 placed/placement/有效性來自既有具型別 member facts。

在 `wood_contact_end_faces_with_sources` 的原 source resolver 成功之後，每端依完整 span/width 呼叫此 policy：PARTIAL 僅略過該端的 full-width/priority 判斷，BARE_RC 明確拒絕，ORDINARY 完整保原路。原 extension check 必先跑，不能以早回傳蓋掉 combined M89–96 的 V_EXTENSION／V_CUT_PRIORITY 診斷。兩端處理完成後仍須呼叫原 I5/I6、I20、碰撞與全世界驗證。

## 自動跨距

`member_reference.h` 的 `WoodMemberSpanRequest` 可追加 typed self pointer（原 positional initializer 預設 NULL，舊 isolation callers 保原規則）；`WoodMemberSpanFacts` 可追加 typed contact facts。W place 對新 request 傳 self，H adapter 只傳既有事實，K 的 interval primitive 不動。

H 現有 `resolve_auto_span` 多處舊 caller／測試沒有 self。可保留其完整簽章為 wrapper，另抽 request 版內部 adapter：舊 wrapper 建普通 request；`app_member_reference_span` 傳完整 request。collect stops 保原時點、原有來源操作與順序，新增 contact facts 不自行重新求值或偷偷讀另一個 World。對 derived 多 component，先依候選完整 footprint 找既有相同有效 component，再對該 component 做定位邊判斷；不能任意改 `role_boundary` 的既有 caller-selected 語意。

正常區間兩端在原 stop_pick 前查 tri-state。PARTIAL 合法端可免 full-width 唯一，BARE_RC 不得 fallback，ORDINARY 留原所有 hit/free/error 判法。只允許原 interval 內候選，不延伸越界，scope 仍只選完整區間。

`between` 要維持 source identity、指名來源、原順序與完整 pair 歧義判斷。針對 boundary 可額外收集有正寬度、非 FREE 的被指名 member 面，再對每一 pair 的實際 span 跑完整例外 policy；裸 RC 不可作新增的接觸來源。不能在 normal full-width candidate 存在時漏掉另一個合法 partial pair 而默選第一個；也不能把沒有整邊覆蓋的 partial pair 算合法。非 boundary 的 candidate／診斷仍原路。

## R6(e) 世界驗證

`world_validation.c` 現在會在 `context->end_faces` 之前，直接用 `wood_stop_count_legal` 要 full-width；只改 contact_end_faces 必被這裡擋回。需在對缺失／歧義 full-width 端點套同一 W admission。可用 H callback 只轉接 typed facts 到 W，或由既有 W host/member facts 建 contact world；不得把 policy 寫入 H。

保留正常 full-width 路徑的原來源順序與第一錯誤。新增 policy 若需 refresh 真 source facts，僅在確實是 boundary 固定段端點候選時做；來源失敗不可當空集合／允許。原 `end_faces` 後仍需完整 `boundary_role` 與 collision loop。正常 full-width 端仍會進 contact_end_faces，其明確 BARE_RC 拒絕不能被前面的合法 full-width count 蓋掉。

## 應固定的整合負例

- 真 FEATURE 接觸面移開或縮成零：raw member footprint 不變仍失去例外；不得靠 raw 補回。
- 真 RC FEATURE 26→27：raw outline 不變仍成 BARE_RC。
- 目標從錯側跨入、正面積重疊但某 face 共座標：最終依 I11 拒絕，不得因 PARTIAL 早回傳越過 collision。
- place probe 是 self copy、原自身未 placed；final validate 傳原 candidate member pointer。兩條都不能把自己算接觸。
- ordinary 全寬 RC boundary 角落維持原接受；無木接觸的 partial/open endpoint 仍 unsupported，不能把兩者混成例外允許零接觸。
- RC 來源更新 26→27、接觸唯一料刪除／移動會重新算且原子回滾，不能把新例外資格存成跨候選快取。
- 原 combined 的兩端 V_EXTENSION／主支頂延伸側面與同 host M97/M98 全保，不隨 528/1056 翻轉放掉。
