# 取件前置失敗原件界線

最初root對synthetic ea163 source使用 git ls-tree -rlz，-l查詢全歷史blob長度觸發promisor lazy-fetch，exec原流顯示 `fatal: sha1 file .git/objects/pack/tmp_idx_5yMatl write error. Out of diskspace`、`fatal: index-pack failed`、`fatal: could not fetch 0bbadec8992b58a73ff01a5a26eb9cf3a9438341 from promisor remote`，subprocess Git exit128、外層Python exit1。這段是從本任務exec工具輸出轉錄，並非另存的原始OS pipe檔；不得描述成產品測試失敗或完整原始log已封存。

當時另一peer F的record工具遭ENOSPC，0assertion且無完整manifest／receipt；其原流由peer保留，不能當mutant被殺。root沒有刪Git objects或不完整pack。修復只停止已退出取件、禁lazyfetch並改不含-l的樹清單、僅materialize已存在必要來源。新replay工作樹初始no-checkout空index另曾被clean guard拒絕，未跑任何產品；以原git read-tree -mu HEAD補完明確sparse index後clean，原裁判全數通過。

後續所有原官方ZIP與三native／兩canvas原CLI本地復驗不跑native／ELF／Chrome；actual原件未更改，詳REPLAY_RESULT與獨立peer報告。
