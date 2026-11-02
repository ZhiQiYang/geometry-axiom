# R7 全部新 raw 放 TMP：只備參數，尚未綁定或執行

工具目錄 `/tmp/geo323-final-r7-stage-tools-20261024`；新source `/tmp/geo323-final-r7-source-20261024`，新正式OUT `/tmp/g337323R7`。bind/preparation/outer-five/launch-five原件全部隨工具目錄留TMP。已存在的v5工具仍用原固定位置及六個精確pin；正式run會按原工具把frozen副本寫入新TMP OUT，不再複製一份新的v5框架。

R6→R7只有以下必要變更：

- `launch_stages.py` 逐byte不變；原175scenes/36交錯樣本/4profiles、600秒/其他原時限、判準、兩非阻塞全域鎖、private stage.lock、累積CLI與各stage exit保原。
- binder必要祖先只改為K產品 `1449d430d1c4734bb1bc3a9f91f3851c845cc0f3`。真正source須等root合流及採用新架構四檔後提供，必須包含已推送的S144見證修正版，不能先以S81測完冒成後續來源。
- prepare_source原WS statvfs改為`target.parent`真filesystem；原C/fixture closure、447級物化規則、nlink1/readonly/index/clean守門不變。
- source/output/tool新path皆TMP；source準備前及正式outer啟動前都用當下真正TMP free判定。以保守138MiB整輪估算＋128MiB native餘量＝278,921,216B入場；root所說138MB在此保守按MiB計，僅磁碟資源，不是任何產品/測時threshold。outer另核新source/OUT/tools全部在TMP同device；缺空間就不啟正式項，不改原紅結果。

依序原入口（目前未執行；不要重跑prepare_plan.py覆蓋已綁request）：

```text
ulimit -s 16384
python3 -B /tmp/geo323-final-r7-stage-tools-20261024/bind_final_request.py --sha NEW_ROOT_PUBLIC_FINAL_SHA
python3 -B /tmp/geo323-final-r7-stage-tools-20261024/prepare_source.py --sha SAME_SHA
python3 -B /tmp/geo323-final-r7-stage-tools-20261024/start_five.py --sha SAME_SHA
```

一輪正式仍完整收五stage；compare紅不阻其餘樣本收齊；沒有重抽樣或選較佳結果。原R5/R6及舊U原件完全不動，R6雙性能紅與原三stdout差保留。正式前root仍須與source/包/archive/objectstore等寫入者協調獨占，不能靠這份準備時的容量保證未來free。
