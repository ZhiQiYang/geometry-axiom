# Canvas 分片與原 golden 收據

`GEOMETRY_CDP_SHARD=legacy|extensions` 選擇真正執行的 canvas units。
沒有此變數時，原 full 與各 `*_ONLY` partial 入口保留原路由。
shard 不接受 partial flags、engineering modifiers 或更新 golden；不能先跑整條再隱藏斷言。

legacy 保留原本體的場景、變數作用域、故障注入及順序；extensions 保留原外掛順序、
巢狀 fixtures，以及 P83 producer 到 P86 consumer 的同片依賴。
`tests/helpers/canvas_shards.js` 從當前 golden 與外掛 require/header 閉包推導段的 ownership；
不固定舊來源的段數或 assertion 總數。零 assertion 段也必須實際到訪。

原 `cdp_floor` 的每段精確比較、原 assertion 與 wait timeout 不變。
每片比對其擁有的原 golden 投影，聚合再要求完整 key 聯集無重複、缺漏或額外段。
原獨立 assembly/grid 等 browser jobs 不充當 canvas 分片。

## 原件與核驗

CI 的 `canvas-shard-*` 保存父程序取得的實際 exit、runtime fresh probe、source/plan/golden
雜湊、run/attempt、PR head、實際 checkout SHA/tree、完整 stdout/stderr，以及受控 verdict journal。
一個 console.log 內的多個受控 verdict 逐一記錄；journal 與 shard raw 同步寫出，
不以任意 console 文字的勾號計數。沒有 unit end、截斷或第二個 CDP_RESULT 均拒絕。

`canvas complete coverage` 只接受同一 run/attempt 的兩份成功原件，重新核對 source、raw、
實際 scope、完整 unit/section journal 與原 golden；通過後才產生 `canvas-complete-evidence`。
PR 合成 merge 的 execution SHA 與 PR head 分開記錄，不把任一個改寫成另一個。

跨環境重驗時，先簽出真正的 execution commit，保持乾淨來源；下載該 run 的兩片：

```sh
gh run download <run-id> --repo ZhiQiYang/geometry-axiom --pattern 'canvas-shard-*' --dir <artifacts>
GITHUB_RUN_ID=<run-id> GITHUB_RUN_ATTEMPT=<attempt> PR_HEAD_SHA=<pr-head-sha> \
  python -B .github/scripts/canvas_evidence.py verify --artifacts <artifacts> --out <new-output>
```

此命令只核驗已保存的原輸出，不啟動瀏覽器或重跑原測試。官方 artifact ZIP 的 API digest
仍是外部來源根；自行重寫整份輸出再重算本地 hash 不等於官方原件。

## 純工具控制

```sh
node --test tests/test_canvas_shards.js
python -B tests/test_canvas_evidence.py
```

控制涵蓋缺片、重片、錯 head/tree/run/attempt、raw/golden 改動、zero key 遺失、計數漂移、
假 scope/summary、未擁有的實際執行、false verdict、不完整 journal 和缺 producer。
這些純工具測試不替代真正兩片及同來源原 full 的瀏覽器驗收。
