本機性能診斷候選已建立；沒有推送，也沒有宣告 P-189 修復或完整驗收完成。

分支：`codex/geo261-p189-codec-trial-20261021`。
完整 trial SHA：`7ad3216ac3ea00bec0adac7b38c3a3daf0a39d09`。
parent L：`43f85313c32410ac01406ab585846bbacafea278`。
隔離 worktree：`/workspace/geo261-wd-read-candidate`，提交後 clean；主分支 `codex/geo261-closeout-20261021` 仍固定 L／clean。

唯一產品變更是 `geometry-templates/woodworking/native/definition_sources.c` 的 `wd_read`：1／4／8 bytes 以可攜 C11 的 unsigned 大端位移組合，守門原字面、失敗 `ok/at`、零寬及 default 舊迴圈、`wd_signed` 保持；未增加 memo 或改 consumer／dependency／P-177 流量。prefix 與 `wd_signed` 起全部 suffix 逐 bytes 比對相同。獨立只讀審查未發現語義缺口。

完整補丁 `candidate.patch` 為 1,672 bytes，SHA-256 `4d2a3ef87a3d663b1c1b08ebc659bf94c6c962c57f15a69f27f137a4e1b6c5ee`。前 C 原件為 `f22fe0aac839b4269a9c06f2ea0b266207cc8ef5a6c4031b35be3e0796505645`；候選 C 為 17,026 bytes，`5d52a836bb1178ff050f725d5b089f4765cbd58033931647f02e50369ea9e347`。兩份來源以 `*-code.txt` 原 bytes 保存。

指定功能驗收命令：

```text
env -u CC -u PYTHONOPTIMIZE python3 -B /workspace/geo261-evidence/wd-read-candidate/run_targeted.py
```

實際子命令為 `timeout 900 python3 -B /workspace/geo261-evidence/wd-read-candidate/targeted_tests.py`，cwd 是隔離 worktree、stack 16 MiB、CC unset，建置使用 `/usr/bin/cc` 及既有 NativeBuild 的 `-std=c11 -O0`。完整環境、時間與 argv 在 `targeted/command.json`；真實 raw wait／child exit／外層結束碼均為 0，耗時 `9.15574672299772` 秒。原 stdout／stderr、14 個實際 test id、88 次建置／連結命令及其原 stdout／stderr／exit 均已保存。

實跑範圍：`tests.test_geo261_definition_sources`、`tests.test_geo261_definition_graph_product` 全模組，以及 `HostFactsAuthority.test_rc_actual_definitions_and_rebound_room_reach_final_validator` 與 `HostFactsAuthority.test_malformed_rc_or_room_rejects_atomically_and_fails_closed`。合計 14／14 通過，failure／error／skip 皆 0；88 次建置／連結全 0。測試真正編入的 isolated `definition_sources.c` 原 bytes 與上述候選完全相同。

這 14 項是在 **detached L 加候選 patch** 時執行，收據保持真實 HEAD 與 dirty 狀態；功能綠後才依授權將同一 bytes 單檔提交成 trial SHA。沒有回填 execution HEAD，也沒有冒稱已在提交後重跑。`commit-receipt.json` 保存自查、明列單一路徑 stage、英文 commit、parent／總 diff 與兩樹狀態的實際命令及結束碼。

本輪沿用既有五個 definition 具名負控制、四個 H 返回值控制與 quantity 變異案例；沒有新增 decoder 專屬負控制。撤回快速路徑回舊 loop 應維持功能綠，效能撤回須另以固定 P-189 裁判真實判斷。全 prefix 截斷、尾隨 byte、sticky failure／bounds 的最小補測建議已在包外 `wd-read-readonly/只讀可行性.md` 提出，本輪沒有擅加測試或收緊 wire 規則。

未跑性能、未刷新 ledger／架構四檔、未執行七項完整整合；現有 metadata／帳本不能認證此新 C 候選。最大不確定是實際載入收益及撤回性能是否可重現，交由後續獨占比較決定是否選案。
