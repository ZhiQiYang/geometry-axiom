# #318 尚未解決的實際紅燈與待驗疑點

本階段依使用者停止交接指示封存，沒有開始來源修正、沒有放寬斷言或改 golden。

1. 原 selftest 的 rc_through_reflex 負控期待 C8_I19_BOUNDARY_END，現在只有 C8_I22_NON_BOUNDARY_EXTENDS。它仍被 I22 拒絕，不等於原 I19 控制通過。要確認核可政策對此 fixture 的精確影響，保 I22 與獨立 I19 牙齒，不能只刪原預期碼。
2. COLSTEP(3000) 及 FZ9 原房／上下／左右鏡像的 Y 向共各 12 個排法由原 buildable 變 core_limited。這是在補完 sparse 文件後仍可重現的產品／測試語意紅燈；原因尚未以單房實際 core_limits 逐筆診斷，不能改預期為 core_limited 冒修正。真修法若觸及已鎖定決策或額外公理，先列決策問題，其他工作可續行。
3. 真 CLI 初放／loadfile／rebuild 的 13 mm 兩支 boundary 是否存在合法放置順序仍未執行。原生 actual-H fixture 是明確已放 World，不能拿它代替 CLI 可達性或宣稱已實測死結。保已放、I6、有序依賴語意，不擅加 batch 豁免。
4. 最新 #318 設計追蹤 14:47:42Z 明確要求 README 的 custom 範圍由待條文稿改成 v3 已排除；現 source README:136 仍有待確認字樣。這是尚未做的文件修正，不能把 custom 原 I19_PRIORITY 案例改稱已解決。

全局帳本 M140–M150 仍未重產；局部原生 11 組 0/1/0 與 oracle builder/checker 兩組 0/1/0 不能改寫舊帳本 current SHA。全域重產與架構衍生檔依 root 最終共同來源執行一次。

`NATIVE_SUMMARY.json` 是 native 於14:49完成當下的歷史摘要；其 not_executed 內的 oracle13 後來已於14:52正式跑0。本階段唯一 current 狀態以 CURRENT_STATE.json／本次PR_BODY矩陣為準，不回改祖先Ec3c的原件。
