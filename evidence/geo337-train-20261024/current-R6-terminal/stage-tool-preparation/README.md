# R6 五 stage：只完成參數準備

以已跑過 R5 的工具為基準，`prepare_source.py` 與 `launch_stages.py` 逐 bytes 不變。`bind_final_request.py` 只把必要祖先改成修正來源 `df66452e7a514032453bea93b8b18ab74d7b1457`；`start_five.py` 只將固定的 R5 SHA 改為必要 `--sha`，仍需與真正 `REQUEST.json` 已物化來源一致。

新來源 SHA 尚未綁定。root 應先合入產品、用下一版架構工具重新生成並採用四檔，再以採用後的真公開 SHA 作 R6。不得拿產品來源 DF 的結果移標成採用後來源。

```bash
ulimit -s 16384
python3 -B /workspace/geo323-final-r6-stage-tools-20261024/bind_final_request.py --sha <root-selected-full-source-sha>
python3 -B /workspace/geo323-final-r6-stage-tools-20261024/prepare_source.py --sha <same-source-sha>
python3 -B /workspace/geo323-final-r6-stage-tools-20261024/start_five.py --sha <same-source-sha>
```

上述均未執行。第一步僅綁定；第二步完整原 source closure 稽核與新獨立 inode checkout；第三步才正式獨占 prepare/build/compare/perf/profile。重測仍是新產品的一次完整五階段，沒有抽樣重試或挑選結果。

保留原 v5 六工具精確 pin、PIPE/延期序列化、base/main、175 scenes/36 次交錯樣本/4 個 profile 點、判準、計時邊界與時限。兩個全域非阻塞鎖和新私有 stage.lock 原樣；compare 紅仍繼續剩餘 stage。CLI 累積 exit 與各 stage execution exit 分開收，不宣稱此五段等於八段全驗收；audit 在 compare 斷言後未達時也不得算通過。原 R5 與更早 U 的紅燈及原件保持不動。

新 source `/workspace/geo323-final-r6-source-20261024`，新 OUT `/workspace/g337323R6`，工具目錄的 `preparation/`、`launch-five/`、`outer-five/` 都必須尚未存在。source 預算20 MiB、最低40 MiB只是原物化 admission；不代表足夠完成全套原件。root 開跑前另外確認當下磁碟與 exclusive 租約，不改產品效能門檻。
