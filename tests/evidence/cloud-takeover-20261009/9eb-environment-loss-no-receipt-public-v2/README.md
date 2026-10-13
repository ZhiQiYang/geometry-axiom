# 9eb 環境失聯後的兩份 incomplete 原始流

ROOT宣告兩次候選為 frozen clean `9eb670110379ec0d726914f3e5b2d8e7237f2b9c`。原服務／unifiedexec sessions於環境恢復後消失，兩個原輸出目錄只保raw及synthetic artifacts，**沒有gate receipt**。本包只封既有原件，不執行產品、不建立冒充原wrapper的收據，不以現在/proc或新版收據倒填。

| 原模式 | raw自報結果與缺口 |
|---|---|
| unfiltered full CDP | 742／0、completed:false，fatal GEO-197 wait；FATAL_UI明載connection phase:error及Failed to fetch。golden未比。這不是完整通過；actual wrapper／Node退出碼、遺失observer身分、before／after dirty attestations均unknown |
| 五declared groups full Space | 168／2、completed:false，font-layout setup因transport失敗；font-layout／space-flow／browser-health未完成，兩timber模組仍omitted。actual wrapper／Node退出碼与observer均unknown，不借raw count宣稱exit1 |

原raw完整保留，CDP SHA `a837c3c956d9347fdd69e9fb88db9aaff235028fdfdee6f5e21c3bb93811f033`，Space SHA `375da6c8bbf5b971965e6992c5fb5e5e28685ab7e7b620249f14378f5c29235b`。derived-canonical JSON是原stream中那一筆結果的公開投影，不是新增產品收據；數字分列、不相加、不補green。原source身份缺口仍未知；另附exact git9eb來源只是候選來源參考，不能當遺失的actual executed-byte／exe證據。

當時四session Unknown process id／服務消失的實際清理原因未核，不能歸因OOM或產品。後來ROOT18:10 current observation中cgroup oom／oom_kill均0，只描述後來觀測，dmesg EPERM亦不證明事件原因。本包的current-selected診斷保原完整hash與所選值，明示省略無關/private環境control／profile process列；不冒充事件時raw或回填oldexit。

ROOT診斷恢復後改用單一owned-lifecycle、服務stdout／runtime／實際gate退出／stop終端全部封存，串行重驗必要full CDP及同版standaloneSpace。只有新gate receipt與lifecycle terminal均存在才另包核新結果；本包兩個原incomplete與unknown永久保原。不以環境失聯當永久外部阻塞。

manifest逐檔保original／publichash及size，decodedJSON／JSONL／trace pathlabel投影保持key／value association。公共副本未執行；privatequeue／feedback／profile payload、nativebinary bytes及大張單獨截圖不公開。先前caption329／0及正式SIX198／0各有完整有效原收據，兩次失聯不改綁或抹去它們。

歷史Windows#173 1692／2 exit1 false／雲端七原件未核收，以及完整CDP2207／0／0只屬clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`保持。這份無receipt包不宣稱完整CDP／Space／43項／golden或物理OS驗收。
