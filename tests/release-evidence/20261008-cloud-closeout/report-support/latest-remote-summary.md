# 環境回復後一次性最終遠端快照

觀測 2026-10-08T18:38:55.397798+00:00 → 2026-10-08T18:39:06.239960+00:00；main `5cc1ffa1ee85120eca14258b86b715151cad274f` 未變。31 個 open PR、27 個 open issue；兩份完整清單皆 page 1 返回少於 100，無缺頁。候選 clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`。

唯一新 head 是 #173 `181fc76049b2b2d001957d2ee0008448bbf5b024`。它是已包含的 ce74 的單一直接子提交，僅新增 full-ui 四份收據文件，產品與可執行測試完全等價；可接文件而不重跑同版同 scope。原 534908 bytes full log 僅本機 SHA，這裡仍 unknown，不能把作者 1692/2 中止輪當獨立已驗或完成。

#173 issue comments/reviews/review comments 均 0；正文沒有明確 writer 釋放。服務這一輪已停不等於寫入責任已交接。root 不搶改 app/space。

新 #173 exact-head CI run 37818800592 七 job 全部 runner_id=0、runner_name 空、steps=[]；七筆帳務未啟動 annotation，另七筆 Ubuntu notice，判為未執行。候選 5174 在 18:40:59Z 推送後單次查詢 runs=0/check-runs=0；不輪詢、不触發CI。

| PR | 最新完整 head | 5174 提交包含關係 |
|---|---|---|
| #175 | `1127531f3aab472e01a4a99c03ef7b739b1b8ae5` | 祖先已含 |
| #174 | `5083a456b1caff33fbc56c5fa10927582432a283` | 祖先已含 |
| #173 | `181fc76049b2b2d001957d2ee0008448bbf5b024` | 新tip本機物件未fetch；父ce74已含，僅新文件未含 |
| #172 | `f8225f767d969e30683a7de99270bbaff4535b5e` | 祖先已含 |
| #171 | `fd5b8c8c2ca65111bdc1cc33a2b9e6bb0a1ff44d` | 祖先已含 |
| #170 | `ce0958ca700753172338fe291a17e781da89465a` | 祖先已含 |
| #169 | `a7bff8f4c7a0d61a3133b6e42d0d513dfe96367e` | 祖先已含 |
| #168 | `a1b2f785e1bdcf13380c56b3b4c8c95093ea615c` | 祖先已含 |
| #167 | `fb6ef45cf651235250523aa88a7fa89d0e6acb34` | 祖先已含 |
| #165 | `354bad248180c6bb1c69735830b75827ab30b70e` | 祖先已含 |
| #162 | `8b9b6f80078c17238286e43da54b751e8d3b5b23` | 祖先已含 |
| #161 | `92ded635e01aa42ea8a999e70da41b736c8b5a92` | 祖先已含 |
| #160 | `2228da155b49d349a616b1e2737074f299e1d57d` | 祖先已含 |
| #159 | `e3ddd74e5a17b55b97c164cf7f69b6f0aeedab41` | 祖先已含 |
| #158 | `06343d8c0d7d195c30cc34832cd092cf980e1d50` | 祖先已含 |
| #157 | `52d0c9e7942ff6d8a1b62d10e23f25a6bc0f6049` | 非祖先；既有排除項，見下文 |
| #156 | `2a7d9cba8d199a33f703e721553034400c0c5764` | 祖先已含 |
| #155 | `f1e020cba5051a331dd150d567698060bf1642b1` | 祖先已含 |
| #154 | `83769b9baef0ba23d3fd41f1058de90cf1f360ac` | 祖先已含 |
| #153 | `349e2a590f98ab783b7d3eeb952e95151db8e39e` | 祖先已含 |
| #152 | `43bf0566546e61ceb9a002ee4f511d9591ce86e9` | 祖先已含 |
| #148 | `aa91cd25c62a67e2587e7ddd0cb0a6f96dd55d21` | 祖先已含 |
| #147 | `fb321eb1a998db47a9cd808b6df9ee36f68b3d15` | 祖先已含 |
| #146 | `d0c5671c5cb009e2549c0c4829dd4ca2a5a21369` | 祖先已含 |
| #144 | `7cfa1a87082e04908f10628485f975125dd8df9b` | 祖先已含 |
| #143 | `6ae8e11d74b12f21fc4294e3bd068fbbc539a209` | 祖先已含 |
| #141 | `823fc91754bd3dbb7cb9fd2b27c045a739d3b14f` | 非祖先；既有排除項，見下文 |
| #137 | `38975775cf42e9dc454aab2e25fc186d9fbd759d` | 祖先已含 |
| #136 | `cc3c1c40e3fcfccfca35b305b0cbf5fab700c81e` | 祖先已含 |
| #134 | `b88545e00c13ccf5e238d4caec1c7b0d78cdc639` | 祖先已含 |
| #129 | `1269e6bcc5d6928c6f51da5148a44c89d068cf7d` | 非祖先；既有排除項，見下文 |

非祖先的 #129 是過期決策差分、#141 已被 #146 整合取代、#157 是未採納的獨立 #87 提案；沿用已有來源判定，不重做／重合／擴功能。此表的 ancestry 本身不宣稱 patch 等價，#173 的文件等價另以 GitHub 完整 compare 證明。

其餘 30 個 PR head 與 27 個 issue metadata 無新 delta。全部 PR 本次只補淺層 exact-head check-runs；未變 head 的 runner/steps 深度收據保留原觀測時間。沒有刷新舊資料庫、派工或重發 #168/#169 留言。

原始 API、命令、stdout/stderr、退出碼與各頁皆在此目錄。`final-followup.json` 綁定原快照、候選包含關係、新文件 hashes、CI 與 unknown；工作管理工具尚未匯入本次快照，不假稱同步。
