目前只保存不帶木工模板建置測試的準備證據，正式測試檔尚未修改、動態驗收尚未跑。現有獨立建置已只取 K＋矩形格網模板＋測試共 11 檔；候選補明確 geometry_woodworking／geometry_app 匯入阻擋自證與 K→W 引用反證，原功能與斷言保留。

| Current state | SHA／原 exit | 限制 |
|---|---|---|
| 產品底本 | 13d02c1db7022145a52ee063286a558e595eb212 | 本分支尚未變更產品或測試 |
| 分支準備 evidence head | 07b7df9bd21be51dd718c9bf9e16dba1b425a231 | 僅新增 evidence/kernel-no-wood-prep-20261023/ |
| 隔離建置 13 項 | 未跑 | 既有 11 項＋候選新增 2 項，未冒稱通過 |
| import blocker／K→W 守門反證 | 未跑 | 原始 0/1/0 driver 已備，未執行 |
| 靜態對抗審 | 無確立 blocker | #318 owner 只讀候選與 driver；正式收據仍待再審 |
| 全域帳本 | 未重產 | 只由 root 在共同最終 SHA 整份產一次 |
| Native 全清單／其他工作流 | 未以本子項重跑 | 不把隔離範圍冒稱全專案驗收 |

共用順序 #323→#314→combined→#318→本子項；#318 正式交棒後普通 merge 前棒，再更新共用 count registry。現在尚未建立正式 worktree，雲端重工作槽由 #288 使用中。所有尚未跑項都保留，不 force push、不合併 PR、不修改決策佇列或公理層。這份正文是準備狀態，不是完成宣告。
