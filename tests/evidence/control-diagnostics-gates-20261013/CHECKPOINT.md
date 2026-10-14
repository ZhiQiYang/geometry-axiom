# Gate progress checkpoint (not a final acceptance receipt)

Source head before this evidence-only checkpoint: 028fe4a01d73e0d5d1472105b3323d160e71db88. No product/test source, assertions, expected counts, C, ledger or protected files changed during these runs.

Native completed:2672 pass/0 fail/1 named allowed GDI skip, original aggregate parent exit0,712.426s. Grid completed:346 assertions/0 failed/0 skipped, completed=true, parent exit0,484.676s; CI-defined partial grid scope, no full canvas golden comparison.

Full canvas is still running; its completed/golden/exit verdict is pending. No passing canvas verdict is claimed here. All raw logs and parent receipts will be committed together after it ends. The live source/binary hashes captured in identity-during.json stay frozen; this checkpoint changes only evidence metadata and Git HEAD, not executed source or runtime fingerprint.

Per the board's every-20-minute progress rule, this checkpoint is pushed while the full canvas command continues. The temporary parent wrapper's tested_head field is a Git HEAD observation at command return; the final report must distinguish that value from the source head frozen at launch and show source/binary identity equality. No WSL or seven-job run is claimed.
