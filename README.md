# openai-dispatch 本機重演證據（PR #465）

- `harness/`：重演器原始碼。`replay.py` 照 YAML 原文求值 job 圖與 if（`ghexpr.py`），真的執行派工 gate／claim step、
  worker prepare step、report 兩個 step、模型 step 新增的 end_reason 段落、push step 的分支名核對那一行；
  其他（checkout、artifact、work job 的隔離與安裝、push 的其他檢查）以模擬代替，細節見 `replay.py` 檔頭。
  `fakes.py`：假 GitHub REST API 與假 OpenAI Responses API；`bin/gh`：gh 替身；`openai_agent.py` 用真 openai SDK 3.56.0。
  `gen_dispatch_yml.py`：產生 `.github/workflows/openai-dispatch.yml` 的一次性產生器（產物已提交在 PR，產生器不進 PR）。
- `runs/green-<head>.out`：新 head 全部情境。`runs/red-old-worker-c12862c0.out`：同樣情境配原 head 的 worker（先紅）。
- `runs/withdrawals-<head>.out` 與 `runs/withdrawals/*.log`：具名撤回。
- 執行：`python3 harness/scenarios.py <repo root>`、`python3 harness/withdrawals.py <repo root>`（需 PyYAML、jq，`AGENT_PY` 指向裝了 openai==3.56.0 的 python）。
