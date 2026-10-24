# #348 H 待套用稿 v5

`HOST_V2.patch` 沿用草稿檔名；其內容為本目錄 MANIFEST 所釘 v5，SHA `d4a745e6f2d101bcd65166617eacc75a3d095d8dc4bee9aa320532438ab25ca1`。三個候選來源在 candidate/tests。只做 AST／bytes／git apply --check（0），未執行 generator、C 或任何正式測試。

完整目的／撤回方式見 `../host-v3-draft/DESIGN.md`。v4 額外鎖定 width axis=normal×length axis，避免同 bbox 的左手 frame 漏檢；v5 依真 serializer 保留所有原 bytes，只把被刪 leaf 自己的 timber/place 與恰一條具名 R18 注解移除，不能濾掉整批注解。v1～v4 原稿不刪。

外部生成器 `build_host_v2_static.py` 目前產生本目錄。它不 import generator/tests，只讀原 S400 的 H/expected、AST parse、做精確文字置換。原 generator 原 bytes 取自 root 固定 `/tmp/train337-final-p52-p189-prep/p189/gen_scene.py`，本次未執行它。

公開 source 仍 S400、E391、Dfd206；方法數仍是公開 H5，本稿套用後才是 H7、局部AST75。沒有真 formal PASS 或 READY；正式 counterfactual 須分開 count／population／unplaced replay，不能早紅遮蔽另一刀。root 已授性能獨占結束後正常提交本線，先由 backlog 完成對抗審，執行與出版仍保存真 SHA／exit／原 streams。
