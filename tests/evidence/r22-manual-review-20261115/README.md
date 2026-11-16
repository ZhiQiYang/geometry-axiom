# R22 manual correction: 2026-11-15 component/native receipt

At test source commit `c5b5a5f9bb9601c5e53b04764bb11d6e8872d905`, based on main
`fd96b8bf7094bd57e74e3226aeba1f24a73b74fc`:

| Check | UTC start | Exit | Result |
| --- | --- | --- | --- |
| Normal Linux launcher build | 19:55:43 | 0 | core, bridge, model-base built and source-verified; build source was unchanged main |
| Original three room suites | 20:05:42 | 0 | 45 passed, 0 failed/skipped |
| `keep-reviewed-after-edit` | 20:05:42 | 1 | failed exactly at `applying vertices clears acknowledgement` |
| `allow-unapplied-row` | 20:05:42 | 1 | failed exactly at `unapplied invalid row cannot be reviewed` |
| Restored unmodified component/native run | 20:05:55 | 0 | 362 assertions, 6 complete paths, 12 native processes exited 0 |

The mutation failures are expected assertion-sensitivity checks, not product
regressions. Both modify only the VM source in memory. The baseline products,
test assertions and native binary are identical before and after those runs.
No product file changed, so no product fix or product red-to-green is claimed.

Exact command arguments, source SHA, UTC timestamps, exits and stdout/stderr
hashes are in [`commands/`](commands/). Full assertions, source hashes, binary
fingerprint receipt and child exits are in [`baseline/result.json`](baseline/result.json).
The complete command/reply stream is [`baseline/native-transcript.json`](baseline/native-transcript.json).
The six `.gcanvas` archives contain only generated public PDF/PNG fixtures;
their geometry and archive hashes are recorded in the result. [`SHA256.json`](SHA256.json)
was generated from the copied original receipts without rewriting them.

The [diagnostic contract and replay commands](../../diagnostics/ROOM-MANUAL-REVIEW.md)
describe the layer precisely. It checks actual bound workspace input handlers,
native preview/confirm/cancel, full geometry and hole/fixity preservation,
source review history, real ZIP writing/reading and fresh native-process replay.
It does **not** run the App or a browser, and does not replace #405's earlier
browser evidence. The final saved shapes contain explicit manual corrections:
an inserted notch, an extended L leg and a deeper notch, each with every edge
dimension entered before review/confirmation.

## Remaining App evidence

The browser slice was **not started** this round. Read-only preflight found
`/usr/lib/chromium/chrome-sandbox` owned by UID/GID 65534, mode 4755; the previously
recorded sandbox launch failure required root ownership. Playwright's configured
`/home/agent/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome` was absent.
The existing standalone room browser scripts still specify sandbox/proxy-disabling
flags, so they were not run in this task. No security setting was changed and no
browser installation, alternate environment or refused transport was attempted.

A permitted browser environment must still establish actual manual correction,
edge-entry/focus, impact dialog, Save → blank App Open → source/projection
continuation. Actual PDF/image decoding and render alignment, physical phones,
IME/OS pickers, private PDFs and human operation time remain unverified here.
R22's ledger remains unchanged; this evidence alone is not L4 App acceptance.

The original worktree was preserved. No service was started. Work-manager CLI
source exists, but its original `.local` SQLite directory is absent in both
the original and isolated checkouts; no replacement database or queue observation
was created and `reconcile/list-ready/list-alerts` were not run.
