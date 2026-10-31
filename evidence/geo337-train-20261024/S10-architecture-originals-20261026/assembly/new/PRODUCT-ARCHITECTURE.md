# Product architecture — S10 original-gate receipt assembly

產品／裁判實際來源 `82c922a3941525d3a094ac0158bdc7dea57ea360`。使用本輪已封閉三原命令exit0／0／0（generic205、product18、零skip），沒有重跑三裁判。完整604 inputs、334 owned／270 exclusions、798 edges／0 diagnostics；LF closure `8d47b6202e793aa5755a887ea2cbb6b90506c68ca4270e0c0df0716142ca3b89`。manifest與原scan逐byte不變，937 identifiers／55 strings政策不變。

604輸入相對真正前次執行 `6e50aef65513b7b38f93228919272c6d40d6c196` 零差異；前四檔採入提交 `75a1e93811a52b69385cbdaf6a09d773ed9052ad`。本次改動的test_geo314_commit_paths.py與決策不在604inputs，帳本仍須另完整重產。公理層快照不變；決策新快照SHA256 `fe822051b5413fb79490b333e23f3c9d6b96959c01f937c274d3246772c15e14`，為已授權normal merge逐字合入。

原三judge執行時間/環境完整保留於receipt，604/raw/LF/Git/tool/SSOT快照是在本組裝階段重新採集並前後比對，不能冒作同時點快照。歷史9組0／1／0及2 neutral controls仍屬M6e50，未在S10重跑或移標。四檔寫於來源外，receipt不hash自己；native、browser、全帳本與performance各需獨立原收據。
