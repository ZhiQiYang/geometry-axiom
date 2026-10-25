`reference_rebuild()` 選用候選中持續存在的求值狀態時，先前仍會清零一份不會使用的 127,584 bytes 區域狀態。本修正將區域 aggregate 初始化移到真正使用 fallback 的分支；候選配置、失敗返回、持續狀態重用及 dispose 順序不變。來源為 F7，供主列車 #338 正常 merge。

| 唯一 current-state 項目 | 來源／結果 |
|---|---|
| Product/test SHA | `2c4635577a8fcb11e88b346547f7bb1c7b739fb7` |
| Evidence head | `74a0a289b48f21f0211c4906808c79138b22b741` |
| 原 LoadResidual suite | 同 Product SHA：14/14，exit 0，零 skip |
| 修正／撤回／恢復語意 | 三階段均 exit 0；包含 fallback、persistent 新建／重用、不同 world、配置失敗與恢復、有序圖 |
| Linux 實際 memset 工作反證 | 同 Product SHA 私有三變體，calls 0/2/0，bytes 0/255168/0，工作判決 exit 0/1/0；撤回 assertion `persistent-reference-local-zero-work` |
| 獨立對抗審查 | 原實測 1777 checks、0 findings；原 169 命令、89 native 記錄、219 source 與 189 retained compiler inputs 綁定；此計數不是新增產品測試數 |
| O2／正式 N16、N64 | 此來源未跑；不能將 O0 反證當 wall 通過。主列車後續固定新 final SHA 跑 R8 |
| 全帳本／架構／完整 native／六 browser／專項 | 本切片未跑；由主代理依影響範圍重產、執行 |
| 允許 skip | 本 focused suite 為 0；未新增任何 skip |
| 已知紅燈 | 歷史 R7 N16/base=1.05190582882169 > 1；原 175/350 exact 的三個 stdout 差仍未解除；CI 帳戶環境也未因此修復 |

驗收原入口為 `python3 -B /tmp/geo337-reference-local-init-draft-20261024/launch_formal.py`，它固定原 runner `tests/_unittest_runner.py tests/test_geo261_load_residual.py`、原 case 90 秒與 compile 300 秒時限；完整 argv、環境、exit 與原流見 `evidence/geo323-reference-local-init-2c463557/` 的 archive、inventory 及外層收據。沒有放寬斷言、golden 或門檻。

封包保存原始 C／Python 輸入、完整輸出及執行時 ELF hashes；原 NativeBuild 已清除的 ELF payload 不在封包，不能據此宣稱可直接重跑同一 ELF。準備好的 uninstrumented O2 工具未執行，明列 UNRUN。

本 PR_BODY 是支線可審查正文檔，供 #338 整合使用；尚不是 READY-TO-MERGE，不取代整列車同 final SHA 的完整驗收，也不自行裁決跨版本 comparator 或 CI 替代接受。
