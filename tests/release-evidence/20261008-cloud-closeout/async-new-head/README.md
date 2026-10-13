# Async ownership evidence on integration 458779f

These independent sandboxed-browser runs apply to clean integration candidate **`458779f003e1f57fdc0f4420564a0b295227843e`**, containing PR #174 head **`5083a456b1caff33fbc56c5fa10927582432a283`**. Main was `5cc1ffa1ee85120eca14258b86b715151cad274f`.

| Scenario | 1400 px and 390 px result | Meaning |
| --- | --- | --- |
| Hold A's native projection → view → B edit fully draws → release A | **PASS**, exit 0; B handles remain 5, edit owner/state unchanged; full World unchanged | The narrow expired `drawEditHandles` cleanup fix resolves the independently reproduced held-proj case. |
| Trusted pointer down on A's vertex → hold its native `bhit` → trusted pointer up completes → view → B edit fully draws → release A | **FAIL**, exit 1; B handles 5 → 0 and `editDrag:null` becomes a stale vertex drag; full World unchanged | An unchecked `canvasDown` continuation still writes/clears newer work and revives an already-released pointer gesture. |

The new bhit failure does **not** mean the 5083a456 draw fix failed. The overall #174/async ownership closeout is **not ready**. Both cases have genuine native replies held unchanged, actual caller-promise completion, no setup/harness errors and no browser page errors. Synthetic fixtures are created through API; subsequent controls and pointer gestures use the rendered product. The 390 px run is a viewport test, not physical-phone or IME acceptance.

## Evidence and exact execution

Each run folder contains original per-width JSON, complete before/after World `.scene` dumps, browser/exit receipts and selected synthetic screenshots. The sibling `.command.json`, `.stdout` and `.stderr` are original command records. The files listed in `binding.json.copiedOriginals` are byte-identical copies, not rewritten results. Full native dumps were recovered verbatim from the private original traces; the binding gives their trace call IDs and trace hashes.

`binding.json` is an explicitly derived index. It retains both exact HEADs, empty git status/dirty diff outputs, product/probe hashes, fresh runtime versions and the hash of every private original identity receipt. Operational session/pid/root fields and four complete trace archives remain private. The archive files are **not included** in this public package. The independent bhit review is an explicitly labeled extraction from the independent original, omitting only its runtime operational fields.

Both runs used runtime `5f7efb63220523dd481660f8dc092ca9f40f35e896cbe172d7694e61f308eb66`, Chromium `151.0.7922.173` with sandbox enabled, app SHA-256 `698ec7948e8cad9b310290d559c1cbe58b9d04c44c05a3ec9db8883b9f588d8d`, and space-workspace SHA-256 `a735338f5cc14f3ae743578986750ace3c7389e0d73fd44c21773d82c2503868`. The same still-running service's native bridge was independently hashed after the runs: `b76a6da590512722d6eda64cfc946392ccc2636f82ab187ef822c1e1606d68b5`. This post-run check links the original service-owner restart/build receipts; it is not presented as a pre-run observation.

Actual browser JS requests returned HTTP 200 with the matching runtime/session, but the traces did not retain their JS bodies. A separate post-run HTTP capture for held-proj matched the before/after filesystem hashes; its private-file hashes are recorded. It is not relabeled as the original browser-loaded response body.

The exact executed Python source was recovered from both traces for each run. The bundled helper/instrumentation files match the recorded hashes. Held-proj uses the earlier finalized probe unchanged; compared with its historical failing handles run, only the already-recorded right-inline-inspector precondition accommodation differs, unused by this left-drawer scenario. Its `handle_test` function and oracle are unchanged. The bhit probe received independent source review before execution and raw trace/state/identity review afterward.

Reproduction requires the managed cloud workspace `/workspace/geometry-axiom`, its approved fresh isolated service on `127.0.0.1:18971`, and exclusive browser ownership. These probes intentionally reset that isolated service's World; do not aim them at a user's active project. The recorded commands were:

```sh
python /workspace/closure-evidence/async-review/run_browser.py browser-handles-integration-5083 --only handles
python /workspace/closure-evidence/async-review/run_bhit_probe.py browser-bhit-integration-5083
```

For a new authorized run, use the bundled wrapper at its actual location and a **new output folder label**. The scripts refuse an existing output folder and a stale runtime. `environment-versions.json` records the available Python/Playwright versions after these runs; that is a post-run environment observation.

## Product owner release conditions

Bind the pending `canvasDown` operation to both the edit generation/work surface and the live pointer gesture. Check ownership after each awaited mapping/hit reply before assigning drag state or touching global preview. `tool === "edit"` alone accepts edit → view → edit; an edit-token check alone does not protect pointer-up within the same edit generation.

Replay the unchanged bhit probe at both widths after the fix and preserve the passing held-proj regression. Add a same-edit early-pointer-up control if the fix claims gesture-lifetime protection. Adjacent `canvasMove`, `canvasUp`/`emitLine`, and shared affine-cache continuations still require bounded ownership review/verification; this package does not label them additional observed browser failures. No product code was changed by these probes or this evidence assembly.

The oracles compare handle count and key edit state, not full handle DOM identity/coordinates or affine-cache contents. World corruption was not observed or induced after the stale drag appeared. This package is neither complete CDP/Space acceptance nor an overall product completion claim. Historical bdd-version failures remain in the separate `async` evidence package unchanged.
