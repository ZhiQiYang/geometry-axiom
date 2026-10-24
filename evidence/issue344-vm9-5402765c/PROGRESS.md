# #344 S540 原 NodeVM9 與 strict row9

產品固定 `5402765c795769a77a7b249de1e3db80045a41de`，沒有產品或測試改動。私有 TMP 648 source／registry leaves 真 Git bytes，原 VM 三相 exit0/1/0；每相9案，pass9/6/9，零skip。撤回只有成功ready轉移的error清除一行；三個原具名ERR_ASSERTION確實出現；恢復後app／HEAD／stage／clean全同。原300秒與測試斷言不變。

原 `python3 -B tests/run_all.py --only node:connection_recovery` 真exit0，完整registry檢查0、strict expected9、needs=[]、9/9／零skip。沒有--build或新增allow-skip。原run_all鎖與build排他守門完成後釋放；原global binary／sidecar逐hash與stablemetadata前後相同。原該rowlogs不存在，新log保原globalpath與私有收據，不刪原件。獨立actual318/0核上述原命令／完整streams／SHA／來源復原。

完整canvas fixed/withdrawn/restored、其他browser、完整native、帳本與架構仍UNRUN。本次結果僅VM及原selected row，不能代真P53/P61恢復或完整驗收，不標READY。下一步root若有新產品來源，先一般merge並判斷closure；root排到完整canvas獨占窗口後，依原35分鐘、golden及三具名正常assert跑完整S/V/S。
