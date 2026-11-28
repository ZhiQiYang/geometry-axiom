OWNER = """github.ref == 'refs/heads/main' &&
      github.actor == github.repository_owner &&
      github.triggering_actor == github.repository_owner &&
      (github.event_name == 'schedule' || github.event_name == 'workflow_dispatch') &&
      github.workflow_ref == format('{0}/.github/workflows/openai-dispatch.yml@refs/heads/main', github.repository)"""
head = '''name: OpenAI dispatch

# 排程派工：不依賴任何對話 session，讓 openai-worker.yml 持續消化 issue #455 的任務佇列。
# 每 2 小時（或擁有者從 main 手動觸發）依序認領並執行至多 6 件任務：
#   claimN（不含模型、不帶金鑰）：.github/scripts/openai_dispatch.py 重新讀 #455，挑出下一件
#     「擁有者發的【任務 …】留言、沒有【OpenAI worker】／【API worker】結果、沒有派工標記、沒有執行中的 run」，
#     先貼一則【OpenAI 派工】標記（之後不再派這件；失敗也不重試），再把參數交給 runN。
#   runN：以 workflow_call 呼叫 main 上的 openai-worker.yml（github context 屬於本 run，actor 仍是擁有者）。
#     worker 的 prepare job 照樣從頭驗證留言作者、上限（≤ 30）、起始分支與模型白名單。
# 第 N 件做完才認領第 N+1 件；上一件的 end_reason 是 credit_balance_exhausted（點數用完）時整批停止。
# 留言第一行的參數：「上限 US$N」（必填，≤ 30）、「起始分支 `X`」（沒寫就 main）、「建議模型 X」（選填，只認 OpenAI 白名單）。
# 規則細節見 openai_dispatch.py 檔頭；安全設計見建立本檔的 PR 說明。
#
# 手動觸發（擁有者、main）：
#   gh workflow run openai-dispatch.yml --repo ZhiQiYang/geometry-axiom --ref main [-f max_tasks=6] [-f dry_run=true]

on:
  schedule:
    - cron: "17 */2 * * *"
  workflow_dispatch:
    inputs:
      max_tasks:
        description: 本次最多派幾件（1–6）
        required: false
        default: "6"
        type: choice
        options: ["1", "2", "3", "4", "5", "6"]
      dry_run:
        description: 只列出會派哪一件，不貼標記、不呼叫 worker
        required: false
        default: false
        type: boolean

# workflow 層級不給任何權限；只在各 job 上給最小權限。
permissions: {}

# 同時只有一個派工 run（schedule 與手動共用）；新的一個排隊等前一個整批做完，再重新讀佇列。
concurrency:
  group: openai-dispatch
  cancel-in-progress: false

jobs:
  gate:
    name: Check trigger (owner, main)
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions: {}
    steps:
      - name: Refuse anything but the owner on main
        env:
          EVENT_NAME: ${{ github.event_name }}
          REF: ${{ github.ref }}
          ACTOR: ${{ github.actor }}
          TRIGGERING_ACTOR: ${{ github.triggering_actor }}
          OWNER: ${{ github.repository_owner }}
          WORKFLOW_REF: ${{ github.workflow_ref }}
          OK: ${{ OWNER_EXPR }}
        run: |
          set -euo pipefail
          # schedule 事件的 actor 是最後修改本檔 cron 的使用者；不是擁有者本人就不派（失敗關閉，run 顯示失敗）。
          echo "event=$EVENT_NAME ref=$REF actor=$ACTOR triggering_actor=$TRIGGERING_ACTOR owner=$OWNER"
          echo "workflow_ref=$WORKFLOW_REF"
          if [ "$OK" != true ]; then
            echo "::error::只接受擁有者本人、main 上的本 workflow（schedule 或 workflow_dispatch）；這次不派任何任務" >&2
            exit 1
          fi
          echo "trigger ok"
'''
head = head.replace("${{ OWNER_EXPR }}", "${{ " + OWNER.replace("\n      ", " ") + " }}")

def claim(n):
    if n == 1:
        needs = "[gate]"
        cond = "needs.gate.result == 'success'"
    else:
        needs = f"[gate, claim{n-1}, run{n-1}]"
        cond = (f"!cancelled() &&\n      needs.gate.result == 'success' &&\n"
                f"      needs.claim{n-1}.result == 'success' &&\n      needs.claim{n-1}.outputs.go == 'true' &&\n"
                f"      needs.run{n-1}.outputs.end_reason != 'credit_balance_exhausted'")
    return f'''
  claim{n}:
    name: Claim task {n}
    needs: {needs}
    if: >-
      {cond} &&
      {OWNER}
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
      issues: write
      actions: read
    outputs:
      go: ${{{{ steps.claim.outputs.go }}}}
      stop_reason: ${{{{ steps.claim.outputs.stop_reason }}}}
      task_issue: ${{{{ steps.claim.outputs.task_issue }}}}
      comment_id: ${{{{ steps.claim.outputs.comment_id }}}}
      base_ref: ${{{{ steps.claim.outputs.base_ref }}}}
      max_budget_usd: ${{{{ steps.claim.outputs.max_budget_usd }}}}
      model: ${{{{ steps.claim.outputs.model }}}}
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          persist-credentials: false
          sparse-checkout: .github/scripts/openai_dispatch.py
          sparse-checkout-cone-mode: false
      - name: Pick the next task and post the dispatch marker (no API key, no model)
        id: claim
        env:
          GH_TOKEN: ${{{{ github.token }}}}
          TASK_ISSUE: "455"
          OWNER_LOGIN: ${{{{ github.repository_owner }}}}
          OWNER_ID: ${{{{ github.repository_owner_id }}}}
          EVENT_NAME: ${{{{ github.event_name }}}}
          MAX_TASKS: ${{{{ inputs.max_tasks }}}}
          DRY_RUN: ${{{{ inputs.dry_run }}}}
          RUN_URL: ${{{{ github.server_url }}}}/${{{{ github.repository }}}}/actions/runs/${{{{ github.run_id }}}}
        run: python3 -I .github/scripts/openai_dispatch.py claim --slot {n}
'''

def run(n):
    return f'''
  run{n}:
    name: Task {n}
    needs: [gate, claim{n}]
    if: >-
      !cancelled() &&
      needs.claim{n}.result == 'success' &&
      needs.claim{n}.outputs.go == 'true' &&
      {OWNER}
    # 權限是 openai-worker 四個 job 的聯集；worker 各 job 自己再降到最小。
    permissions:
      contents: write
      issues: write
      pull-requests: write
      actions: write
    uses: ./.github/workflows/openai-worker.yml
    with:
      task_issue: ${{{{ needs.claim{n}.outputs.task_issue }}}}
      task_comment_id: ${{{{ needs.claim{n}.outputs.comment_id }}}}
      base_ref: ${{{{ needs.claim{n}.outputs.base_ref }}}}
      max_budget_usd: ${{{{ needs.claim{n}.outputs.max_budget_usd }}}}
      model: ${{{{ needs.claim{n}.outputs.model }}}}
    secrets:
      OPENAI_API_KEY: ${{{{ secrets.OPENAI_API_KEY }}}}
'''

s = head + "".join(claim(n) + run(n) for n in range(1, 7))
open("/home/user/geometry-axiom/.github/workflows/openai-dispatch.yml", "w", encoding="utf-8").write(s)
