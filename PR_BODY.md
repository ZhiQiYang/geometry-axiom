本分支封存 #288 新 final F 的 P73 受控反證，以及 Chromium154 固定版原 P73 子集。撤回 app.js 的 SVG hidden attribute guard 後，原具名 P73 斷言真轉紅；恢復後轉綠。產品與測試檔未在本分支變動。

- Product／tested SHA：`3d681636902371ecc528b20f51eea33e272581c9`。
- Evidence head：`77d1e3438d7e952230ce501bf3dddbd9a4e18580`，分支 `codex/geo288-p73-final-20261023`；本 head 相對 F 只有 `evidence/geo261-final-3d681636/`。
- 最新審查：handoff `acd1289228d490c68a139cf17e02fdc1f3cb247c` 的 `handoff/pr-reviews/288.md`，最後一則 2026-10-23 12:35:32Z／head `ee28481`。本兩項回應該則列出的 P73／Chromium154 未跑項；#288 其餘 gates 由整合分支的唯一 current-state 結案。

| Current gate | 實際執行 SHA | 原 exit／結果 | 原時限與允許 scope／skip | 獨立審查 |
|---|---|---|---|---|
| P73 controlled | `3d681636902371ecc528b20f51eea33e272581c9` | fixed／withdrawn／restored Node `0/1/0`；driver／outer／top `0`；原 predicate `true/false/true` | 各 before predicate=true、callback=1、例外=0；只跑單次真 callback 與原 P73 predicate，沒有跳過該反證斷言；這不是完整 P73 workflow | actual 與 immutable Git 公開封包 roundtrip 皆已由318獨立接受 |
| Chromium154 固定原 P73 子集 | `3d681636902371ecc528b20f51eea33e272581c9` | 原 workflow／Node／outer／top `0`；`proof_expectation_matches=true`；`69/0` | 84.124749832秒 < 原35分鐘；唯一 filter `GEOMETRY_UIUX_FIX_ONLY`、partial，完整golden不比較；本地 checkout/upload actions具名未執行，fonts以已安裝檢查完成 | actual 與 immutable Git 公開封包 roundtrip 皆已由318獨立接受 |

獨立審查原件已封入 evidence：`PEER_ACCEPTANCE.json` SHA256 `d9781bca3e2f73ba1429914ce3f7e80cab827b5fa80333b989d4df645a4ceea1`；公開包報告 SHA256 `51f888887a790eb5168d051ff52c0ddc64ed01fd93bca180cf61499420a10c2b`。其2783項證據核對、972個tar成員逐bytes/hash、770原件coverage皆相符；這些是證據核對數，不是產品斷言數。

P73 原收據 SHA256 `9fee99803279168c071257133f68d20fef11befe3a8d057d194bbabb367c670f`。三態唯一受控 callback 的 before 都是原 SVG hidden attribute=true、hidden IDL=undefined；撤回時才生成假 grid rect，且失敗精確為 `P73 assertion failed: 空空間不畫假邊界，提供加入成員入口 false`，沒有用 crash、timeout 或 setup error 代替反證。原 app bytes、P73 test、probe、斷言不動；731 個原 RuntimeSnapshot 輸入在來源、隔離 clone 與來源執行後皆完整相同，來源與隔離 clone 最終還原 clean F。

Chromium154 原收據 SHA256 `17114e471ddfd48187f08bb6aca1737f83e0f3f30ed28a5a7823f1f2fa04f8d4`，原 footer completed=true、P73=69、failed=0、skips=[]、exception=0、golden=`not compared (partial mode)`。只驗固定 F 的69子集，沒有做154撤回／恢復，也不證明舊原產品曾在154通過。

環境原輸出為 Google Chrome 156.0.8078.47、Chromium 154.0.8037.57、Node v24.19.0、Python3.12.14、GCC14.2；fonts-noto-cjk 為 `install ok installed 1:20240730+repack1-1`。P73 driver 自持原R3鎖，legacy外層持同一flock，兩項串行；原c387、reaper、16MiB stack、timeout與判官未改。probe clone 放workspace；scratch/profile/埠獨立。完整最外層 env-u argv、真環境、原命令與 stdout/stderr、終態後7／2份reaper事件均在封包。

原執行命令（完整 argv 另在 launch request）：

```sh
env -u NODE_OPTIONS -u PYTHONOPTIMIZE -u GEO261_P73_UNDER_REAPER python3 -B /workspace/geo261-environment/execute_f_extra.py --label p73-controlled-final-3d681636 --sha 3d681636902371ecc528b20f51eea33e272581c9 --repo /workspace/geo288-p73-owner-20261023/source-3d681636 --outer-root /workspace/geo288-main-merge-20261023/p73-final-outers -- python3 -B /workspace/geo288-main-merge-20261023/bound-3d681636/p73/run.py --repo /workspace/geo288-p73-owner-20261023/source-3d681636 --sha 3d681636902371ecc528b20f51eea33e272581c9 --scratch /tmp/gp7-3d681636 --heavy-lock /tmp/g261r3/heavy.lock --clone-dir /workspace/geo288-p73-owner-20261023/probe-source-3d681636 --service-port 19960 --cdp-port 9600
env -u NODE_OPTIONS -u PYTHONOPTIMIZE -u GEO261_P73_UNDER_REAPER python3 -B /workspace/geo261-environment/execute_f_extra.py --label chromium154-p73-final-3d681636 --sha 3d681636902371ecc528b20f51eea33e272581c9 --repo /workspace/geo288-p73-owner-20261023/source-3d681636 --outer-root /workspace/geo288-main-merge-20261023/p73-final-outers -- flock -n /tmp/g261r3/heavy.lock python3 -B /workspace/geo288-main-merge-20261023/bound-3d681636/legacy/run_p73_subset_chromium154.py --repo /workspace/geo288-p73-owner-20261023/source-3d681636 --sha 3d681636902371ecc528b20f51eea33e272581c9 --scratch /tmp/gl7-3d681636 --label c154-fixed --port 19964 --cdp-port 9604 --expected-exit 0
```

公開封包與逐檔 inventory 都在 `evidence/geo261-final-3d681636/raw/`：P73 `p73-controlled-final-3d681636-01.tar.gz`（5,509,309 bytes，SHA256 `91a1a7904d03c018e31450ee27866a5b23dbb4c1d78e5135ba35c049ecc3e8e7`，831成員）；154 `chromium154-p73-final-3d681636-01.tar.gz`（2,336,559 bytes，SHA256 `983dd9aecf51e814f4ff5821c2b439c2f57aadcfb89345f0a420536ede960812`，141成員）。原命令輸出全保存；可重建 Chrome profiles／ELF 明列排除或只保hash。初次封存 staging 跨/tmp→workspace硬連結因EXDEV exit1，原版本與分類保留，改為跨掛載copy並核bytes/hash後兩次publication均0；產品測試沒有重跑或改判。

本分支沒有重產帳本、架構收據或重跑 #288 其餘項目；沒有 force push、PR merge 或修改SSOT／決策佇列。最不確定的界線是 controlled callback 不代表自然完整P73事件時序，154只是固定69子集；#288整體可合併判斷仍依root整合矩陣與最新審查要求。
