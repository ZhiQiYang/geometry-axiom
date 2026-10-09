# Geometry 243326b5: supplemental v4 actual attempt

Product: clean `243326b512896ace70e068f62c8f3d6397f6000d`, `<workspace-path> Runtime before/after: `545f021b8cbb26b6afaabde19b73fa82d30a8a138b99d8c721a35fb54f73999b`, PID 132256, session `755d0e4171ce4fc8b5960e656a0ff714`, isolated port 19180. Product tracked bytes remained unchanged. Native execution/configured binaries and source closure matched; actual Node and sandbox-enabled Chromium executable bytes and command lines were observed and matched configured identities. The operating system sandbox internals were not independently inspected.

The explicitly approved scratch v4 source `a62999473b6ff6076e414a48d5950135998f49f653fbcfbc70c20b25aa61bd24` executed `plan,bom,row-blur,s2` as a separate supplemental scope. It is not execution of the different formal six-group test source.

Actual result: **185 passed / 2 failed, exit 1**. All four groups were attempted, but acceptance `completed:false`, `probeVerified:false`. Canonical probe `completed:true` records all attempted groups, not passing acceptance. No retry, forced click, product edit, or assertion change was used during this attempt. Owned Node 146865 and Chromium 146903 were closed and checked absent after completion.

## Findings

- Plan: 16/0; desktop and 390px passed.
- BOM: 44/0; desktop and 390px passed. Required native delete previews and ordinary Confirm, exact independent dimensions/world endpoints/source cells, CSV, ID ordering, cleanup and native Undo baseline were checked.
- Row blur: 32/1 on desktop. Pending raw and dirty marker survived invalid blur; disabled Confirm had one real trusted pointer attempt with zero API requests. New immediate invalid-input-to-Cancel produced exactly one trusted pointerdown/pointerup/click and did not lose its button target. The new all-API-zero assertion failed because Cancel redraw sent two legitimate reads: exact `source-inspect` and `engineering-read`. The later immediate-Cancel native-after/retired-row/fresh-candidate assertions and row-blur 390px were not reached. The failure is retained; these later checks are not declared passed.
- S2: 86/1. Desktop compact keyboard continuation/delete-preview Cancel and old-owner same-ID import interruption, retired compact callback zero API writes, old discard callback isolation and B continuation passed. At 390px, the new fixture rendered its selected composition inspector and full-workspace action visibly. The inherited `mainInspector` helper instead clicked `#toggleRight`, which composition CSS hides. The actual screenshot is retained. Remaining 390px S2 checks were not reached.

The two harness preconditions require a separately reviewed source version: only the new immediate-Cancel request census may admit the two exact inspector-read payloads with actual response and full native equality evidence; original disabled Confirm and retired-callback API-zero assertions remain unchanged. The S2 route may skip its drawer opener only after positively proving the selected fixed inspector and original full-workspace target visible, inside, contained and hit-testable.

## Immutable evidence

- Gate: `supplement-243326b5-gate/receipt.json`, SHA256 `d7829a3d798c7ca3e4817407963310820691fdd1e3f0e7abb240280d9fa99d17`.
- Raw log: `supplement-243326b5-gate/command.log`, 88,679 bytes, SHA256 `c6485429e80119ae6f2c8ddf85a457e35cd002ef540f987b07344337a4009910`.
- Probe: `<isolated-test-directory> SHA256 `1d2126a9cc62bc50015de3aa409f23a1cbb60d903b8edc756cc33593d33061b1`.
- Executed-source archive: `supplement-243326b5-gate/executed-sources/manifest.json`, 305 entries, SHA256 `d99b27039c5c713fb31ba983571c7d74dd409c5b602983aeca390efff02596e6`.
- Independent read-only census: `supplementary-validation-243-supplement-v4.json`, 28/28 evidence checks, SHA256 `72314c2a9ff61d77cd6e7f1073e5cd1f5da94b7c1b0613ebeb4b67dfbbfb4074`. Evidence consistency does not change acceptance failure.

Full #54 and formal six groups were not executed on this head after the failing prerequisite. They remain distinct future scopes. Prior 640 formal six 198/0 and #54 273/0 stay bound to 640, not this head. This supplemental command does not cover full CDP, full Space, all #123 items, physical phone/touch/IME, operating-system dialogs or golden/private ZIP comparison.
