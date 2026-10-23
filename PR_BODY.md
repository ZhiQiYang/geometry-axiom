# #318 閱讀 A：實作中

依 issue 留言 6357744513 第 3 版及 2026-10-23 核可閱讀 A，boundary 固定段在定位外輪廓邊端點可有正長度的部分角材接觸；仍拒絕零角材接觸、裸露可放下料寬的 RC 面與借用此款的其他角色／延伸段。

已落核可 SSOT 四處差異及 oracle 建構／C8 各自重算的三態政策，新增 12 個專有測試與固定 528／1056 正向見證。已普通 merge #323→#314→combined 的正式 stack。原生 W/caller、canonical、既有 oracle 見證遷移與正式驗收持續進行；這份正文不宣稱全綠。

| 項目 | 唯一 current state |
|---|---|
| 目前來源／evidence head | `ce4a8ad89e8ae3ce69043e9bd91ce4dad519710d` |
| 閱讀 A 第一批產品提交 | `41cf5594011d9d13f401319ccf676c741263dbcc` |
| 普通合入前棒 | `15a735951a36b6fe52e0291152f335139e6921ad`，內含 #314／#323 |
| 授權 SSOT 差異 | 已套 D11 一句、I19 例外三、R6(d)(e)；其餘公理與決策佇列不改 |
| AST／JSON／hash 靜態檢查 | exit 0；僅來源解析，不是產品／測試執行 |
| 原生 W／span／between／revalidate | 尚待實作與動態驗收 |
| 正典閱讀器同步及三條檢查 | 尚未跑；剛取得 common/canonical source baton |
| oracle 既有 selftest／golden 預期遷移 | 尚待；現有舊 core_limited 見證不能冒綠 |
| 新 oracle 12 方法及正式 quick 掃描 | 尚未跑 |
| 528／1056 改判、矩形逐毫米／凹角 579 掃描 | 尚未跑；固定正向 ID 已保留，防止清空拒絕清單後漏掃假綠 |
| 突變 0/1/0 | 尚未跑；M140+ 預留，未寫全域 registry |
| 架構裁判／收據 | 尚未跑／重產 |
| 完整突變帳本 | 不由子代理產生；主代理在共同最終 SHA 整份重產一次 |
| 本輪允許 skip | 無宣告；尚未驗收不計通過 |

證據位於 `evidence/issue318-reading-a-20261023/`。source phase 記錄清楚區分先前準備文件與已落產品來源；原生／oracle 新綠燈尚無收據。root 的 #288 canvas 診斷目前獨占雲端 heavy，未並跑編譯、Chrome、bench 或 scan。

最不確定處是實際 caller 整合：不能讓 R6(e) 的舊 full-width gate 蓋回新例外，不能讓 BARE_RC 回到舊 C8 的 indoor-only 分支被誤放，也不能以 PARTIAL 早回傳跳過 I5/I20/I22／碰撞。這些都會有專項負例與對抗審；正式結果到齊前不得視為完成。

不 force push、不合併 PR。#288 尚未進 main，後續改 base 由主代理依整體順序處理。
