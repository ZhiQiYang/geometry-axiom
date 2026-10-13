# PF-2 progress, cloud native only

Base `2004c6c8bebe1bbff2df142630b630e1ee5115b8`, claim `bea36ea4`.
No UI, SSOT, whitepaper, canonical reader or timber definitions are changed.

All commands: `ulimit -s 16384; python3 -m unittest ...`, actual exits below.
The first baseline imported the PF-1 test class directly, so unittest also discovered
its original 22 tests. Later the harness is imported as a module, avoiding accidental
duplicate registration in the standalone PF-2 suite. The baseline raw is retained.

| Run | Suites | Actual exit | Result |
|---|---|---:|---|
| baseline | new layout, with accidentally discovered PF-1 | 1 | 34 tests; 16 failing subcases, unsupported put-panel-fill |
| fixed-1 | layout | 1 | 12 tests; negative origin incorrectly rejected; test sent undo without line prefix |
| fixed-2 | layout + PF-1 | 1 | 34 tests; old unknown-command diagnostic changed because panel-fill is now a registered record |
| fixed-3 | layout + PF-1 | 1 | 36 tests; touching holes emitted a figure-eight |
| fixed-4 | layout + PF-1 | 0 | 36/36; right-branch traversal splits touching holes into simple rings |

The undo test was corrected to use the documented `line undo`/`line redo` bridge protocol;
the old invalid-record assertion now expects the registered command's arity error.
No original assertion or fixture was removed. Full native and mutation receipts follow.

This is not a WSL or browser receipt. PF-3 effective seams/support, PF-5 derived placement
and timber layer, PF-4 grids, PF-6 timber suggestions and browser project reopening remain pending.
