| Gate | 產品 SHA | 正式結果／完整原件 | 交付狀態（推送後由 root 更新） |
|---|---|---|---|
| #323 核可精確差異 comparison | F9 `4f8a794f4167c3562eb182045102e86e9e37cca9`（原 ELF build F8） | 原 stage / wrapper / 後段 audit 0；175 scenes／350 base-fix rows／700 O2+trace commands＋12 Git commands，三名共六處 suffix；原 comparison actual17231/0、peer10144/0。PUBLIC 精確移除唯一2795B輔助 GET/user full profile，formal comparison 全原件保留；四原安全包 byte 相同、只重封第4包，collection0、actual159/0。 | 五個PUBLIC logical包待普通push及remotehash；原私有完整五包保留。原R8 outer1／原perf樣本不改標、不重抽。 |
| §7 axiom mutations | 同一 F9 | 原 gate / host 0，baseline與五次恢復各44tests，V01–V05各紅；原actual peer428/0。原189檔＋工具/host/peer共206members收為一包，collection0、actualpeer1475/0。 | 完整包待普通push及remotehash；不替代card-reference或其他專項。 |

PUBLIC 只排除與產品測試無關的完整輔助帳戶profile；安全身份subset、原API argv／exit／stdout hash與具名批准來源仍保留。不得寫成「所有API raw公開」；私有authority完整輸入無法單靠PUBLIC包自足重播。這項限制不刪除700次正式comparison CLI任何原stream。

事後讀取稽核首輪因工具錯取host JSON頂層exit_code而退出1，完整原失敗保存；v2固定綁原host雜湊與actual_tool_result.exit_code解析，重新唯讀稽核159/0。沒有重跑collector或產品、沒有放寬正式gate。

以上只是兩個gate的可貼入內容，交付前仍為volatile cloud-only。由root合併四browser／native等為唯一current-state矩陣；不得以此二項推論列車全部通過或READY-TO-MERGE。
