# #341 F8 fallback 實績獨立複核

4,416 checks，review exit 0。546 原始 CLI、24 原正例執行、378 完整樣本（42 diagnostic／42 warmup／294 scored）、95 source files 與9 ELF 完整核對。未重跑產品或效能。

固定 F8：`75a1e93811a52b69385cbdaf6a09d773ed9052ad`。所有14 cases保留一輪warmup與7輪計分，fixed/withdrawn/restored確定交錯順序、相同inputs、完整FACE九欄與輸出順序均一致。診斷WORK與未插樁CPU/wall分開核對；不把WORK當成實際記憶體流量。

| Case | N | fixed CPU/wall ns | withdrawn CPU/wall ns | restored CPU/wall ns | fixed/withdrawn wall |
|---|---:|---:|---:|---:|---:|
| none | 8 | 1813/2574 | 1763/2554 | 2053/2634 | 1.007831 |
| none | 32 | 7581/8223 | 7020/7722 | 7311/7972 | 1.064880 |
| none | 64 | 23184/23846 | 21612/22334 | 23114/23866 | 1.067699 |
| few | 8 | 2374/3035 | 4467/5187 | 2423/3305 | 0.585117 |
| few | 32 | 7932/8603 | 9213/9975 | 7592/8463 | 0.862456 |
| few | 64 | 23274/24197 | 24747/25428 | 23154/23785 | 0.951589 |
| dense | 8 | 2063/2714 | 4877/5578 | 2333/2995 | 0.486554 |
| dense | 32 | 3896/4607 | 5898/6570 | 3646/4426 | 0.701218 |
| dense | 64 | 6820/7601 | 10145/10816 | 7471/8292 | 0.702755 |
| fallback-none | 1217 | 17115527/17122465 | 16956472/16965788 | 16913718/16915273 | 1.009235 |
| fallback-dense | 1217 | 11667490/11742146 | 12085189/12093196 | 12060923/12070331 | 0.970971 |
| unique-none | 64 | 12849/13540 | 13550/14472 | 14342/15033 | 0.935600 |
| unique-few | 64 | 14301/15313 | 14802/15533 | 13741/14461 | 0.985837 |
| unique-dense | 64 | 15923/16756 | 14962/15734 | 15573/16294 | 1.064955 |

N64 none wall 增加約6.8%，dense則減少約29.7%；fixed/restored相同原碼亦有短時間樣本波動。完整七次原值與兩個對withdrawn的比率保留在REVIEW.json。沒有刪樣、調時限或新增效能門檻。

none64仍做16,384次shadow iterations，新增16,512次active reads。dense64移除126次memmove（390,096 B），但shadow iterations由382增到8,509；這是工作量取捨，不是所有工作量皆下降。超出固定容量的fallback兩組保留原算法與工作量；unique controls保留#343索引路徑，不冒充fallback收益。

`semantic_passed=true`；`performance_acceptance_decided=false`；歷史Sc493整體#341 B1尚未解除。此收據不代替列車其他未驗項，也不標READY。
