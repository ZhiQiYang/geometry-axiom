# Product architecture — a6 original-gate receipt assembly

產品／裁判實際來源 `a6f4013364e21bcb7239b5dcc25caac0f6d61f77`。使用本輪已封閉三原命令exit0／0／0（generic205、product18、零skip），本組裝階段沒有再次執行三裁判。完整604 inputs、334 owned／270 exclusions、798 edges／0 diagnostics；LF closure `8d47b6202e793aa5755a887ea2cbb6b90506c68ca4270e0c0df0716142ca3b89`。manifest與原scan逐byte不變，937 identifiers／55 strings政策不變。

604輸入相對真正前次執行 `6e50aef65513b7b38f93228919272c6d40d6c196` 零差異；前四檔採入提交 `75a1e93811a52b69385cbdaf6a09d773ed9052ad`。相對前次執行的test_geo314_commit_paths.py與決策不在604inputs；全帳本保留S10實際重產原件，其於a6有效性由獨立--check判定，本架構收據不認證帳本。公理層快照不變；決策新快照SHA256 `e6f2aee291850d9aaf8cc0026994f6c86894bb2a7849798ddd11cd63c5558740`，為a6既有檔案的逐byte快照，不以其內容自行擴張授權。

原三judge執行時間/環境完整保留於receipt，604/raw/LF/Git/tool/SSOT快照是在本組裝階段重新採集並前後比對，不能冒作同時點快照。歷史9組0／1／0及2 neutral controls仍屬M6e50，未在a6重跑或移標。四檔寫於來源外，receipt不hash自己；native、browser、全帳本與performance各需獨立原收據。
