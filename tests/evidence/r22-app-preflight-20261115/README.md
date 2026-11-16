# R22 App follow-up: prepared, not started

**No App assertions ran.** This folder contains the actual preflight and syntax
receipts for the new real-App diagnostic, plus read-only preservation/ownership
observations. No product defect was reproduced, no product file was changed,
and no browser or native service was launched in this follow-up. It is not a
replacement for the component/native results in the preceding evidence folder.

Source commit: `ae2d943817879c3096d7b23106c3f55122dea606`.
Baseline main: `fd96b8bf7094bd57e74e3226aeba1f24a73b74fc`.
The checkout was clean before and after both commands.

| UTC start → end (2026-11-15) | Exact command from the isolated checkout | Exit / actual result |
| --- | --- | --- |
| 21:35:27.922009 → 21:35:28.142289 | `node --check tests/diagnostics/r22_app_manual_review.cjs` | 0; syntax only |
| 21:35:27.929515 → 21:35:28.706341 | `node tests/diagnostics/r22_app_manual_review.cjs /tmp/r22-app-20261115-preflight --preflight-only` | 2; not_started, 0 App assertions, 0 browser launch attempts, services=[] |

Exact stderr:

```text
NOT_STARTED ENOENT: browser executable unavailable: /home/agent/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome
```

The command wrapper's JSON files contain complete argv/cwd, UTC, full SHA,
worktree states, exit and raw stdout/stderr hashes. `preflight.receipt.json`
additionally pins the diagnostic and product-source bytes. Diagnostic SHA-256:
`25741c60233ab47e00413da80e24da6b04e7867e5caeb9bf6475bee6220f53c7`.
`SHA256.json` covers the raw receipts and observations byte-for-byte. The
evidence commit adds these files without changing the diagnostic's bytes.

Read [the replay protocol](../../diagnostics/R22-APP-MANUAL-REVIEW.md) for the six
prepared PDF/image scenarios and exact UI controls. The new scenario retains
the manually changed outline through dimensions/review/confirmation, actual
download, cold Open and projection. It is not registered in the old P scope
or in CI; even a future green Geometry check does not prove it ran.

The follow-up checked all current supported entry points. There is no Browser
tool in this environment. Existing standalone scripts contain sandbox/proxy
overrides and were not run or edited. More precisely, the older acceptance
script disables sandbox and proxy; the direct-row script sets
`chromiumSandbox:true` but still supplies `--no-proxy-server`. The new
diagnostic has no extra browser arguments and keeps sandbox enabled.

The manually dispatchable R11 workflow cannot substitute for this new scenario:
its runner invokes only registered `cdp_test.js` scopes, and its sandbox `keep`
setup changes helper ownership/mode. Neither that setup nor its disable option
is authorized here. No workflow was manually dispatched. No shared canvas,
golden, shard, registry or #396/#417/#419/#420 branch was changed to force CI.

`preservation.json` records the two existing worktrees, original HEAD
`797575db351719290504b1bf64e7f0e632b9f152`, zero product diff, no owned App/service
processes, and system Chromium helper UID/GID 65534, mode 4755. That metadata
matches the earlier reported helper configuration failure; it is not a new
launch error. The earlier denied `/root/.cache/ms-playwright` read and sandbox
launch were not retried. Prior receipts were not rewritten.

At the final ownership read #420 advanced to
`a63ed964302c16c964a294baecd6155626116294`; its current changed-file list still
does not intersect this delivery. Main remained unchanged. The old #421
approval and Geometry run `43756680091` apply to `53ca798...` only (nine actual
jobs passed, browser matrix skipped). A new PR head needs its own review/checks.

Minimum prerequisite for the App run: the **same authorized cloud environment**
must be provisioned with a supported browser and functioning sandbox by its
authorized maintainer, without this task changing security/network settings or
switching executor. Only then execute the full replay command into a new output
directory. Do not call this slice L4, mark #54 complete, or interpret preparation
as a successful browser execution. Private PDF, physical devices/IME, OS picker
and human operation time remain outside this evidence.
