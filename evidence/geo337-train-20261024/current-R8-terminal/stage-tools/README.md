# R8 原正式五階段：僅最小參數模板

新工具 `/tmp/geo323-final-r8-stage-tools-20261024`；未來獨立source `/tmp/geo323-final-r8-source-20261024`、正式OUT `/tmp/g337323R8`，bind/preparation/launch原件皆TMP。現在 `required_product_ancestor=null`、正式source未綁，沒有虛構SHA，source與OUT也未建立。

沿已獨審R7 d3b42工具：prepare_source.py、launch_stages.py逐byte相同；start_five.py只把R7文字換R8。binder唯一行為差異是新增必填 `--required-ancestor`，兩SHA都驗完整40位格式，原`git merge-base --is-ancestor`仍強制執行，真正傳入祖先另存bound request與binding收據。root只會提供combined真正公開的新H source；先前S144不是此次新H必要祖先的替代證明。沒有新增參數鏡像測試或產品門檻。

六原v5工具/pins、175 scenes、36交錯樣本、4 profiles、原時限600、原比較與效能門檻、原clock位置、紅燈後繼續完整五階段、CLI與stage exit分開、兩個非阻塞全域鎖全部不變。磁碟守門仍138MiB整輪＋128MiB native＝278921216B；只依當時TMP真容量入場，沒有以準備時容量保證未來資源。永久TMP Git object store不可刪。

執行順序由root掌握：combined公開新H→一般合流成真M→架構四檔原驗收與採用成公開F8→此處bind/prepare→清空重I/O／fresh容量與兩鎖→正式five。以下只是尚未執行的入口，兩placeholder必須替換成真SHA：

```text
ulimit -s 16384
python3 -B /tmp/geo323-final-r8-stage-tools-20261024/bind_final_request.py --sha ACTUAL_PUBLIC_F8 --required-ancestor ACTUAL_PUBLIC_NEW_H_SOURCE
python3 -B /tmp/geo323-final-r8-stage-tools-20261024/prepare_source.py --sha SAME_F8
python3 -B /tmp/geo323-final-r8-stage-tools-20261024/start_five.py --sha SAME_F8
```

不要重跑prepare_plan.py覆蓋request。原R7 N16紅、三項exact差與所有歷史原收據保持；本工具準備不能算新效能通過。
