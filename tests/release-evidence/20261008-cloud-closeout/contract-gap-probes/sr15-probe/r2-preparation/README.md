# SR15 parameter and binding-anchor native probe — r2 prepared, not executed

`sr15_probe.py` is a private, single-test harness for the missing combined SR15 path. It does not run the inherited test suite, alter products, build a binary, touch an HTTP service, or perform browser UI steps. Root is the sole runner. One owned bridge process holds a synthetic two-face scene and is stopped in cleanup. The explicit `--repo` argument is resolved before repository test-helper imports; no old workspace location is required.

Sources: SSOT R32 (`公理層.md:1070`), `NativeSubdivisionOracle.test_full_source_edit_retains_rules_and_updates_both_anchored_bindings` (`tests/test_grid_subdivision_oracle.py:351`), its `real_supports` (`:597`), and engineering transaction/parameter helpers in `tests/test_engineering_core.py:43` and `tests/test_parameters_core.py:149`. The probe adds parameter tokens and actual guide/direct references to this one scene; it does not combine unrelated old test passes into SR15 completion.

Expected input and literal output, frozen before execution:

| State | Binding A U lines | Binding B U lines | Rule guides A/B | Direct secondary A/B |
|---|---|---|---|---|
| `param:1:1=600`, V400, U3/V2, A anchor0/1,0/1; B1/2,1/2 | 300, 500 | 0, 200 | 300 / 200 | y400,length540 / y600,length240 |
| Parameter changes600→900 | 400, 700 | -50, 250 | 400 / 250 | same expected y/length |
| Only B U anchor changes1/2→1/3 at U900 | 400, 700 | 100, 400 | 400 / 400 | same expected y/length |

Both boundaries are `100,200 2100,200 2100,1800 100,1800`; their anchor cell is(-2,1). A direct ref uses(-2,1):v0; B direct ref uses(-2,2):v0 so its physical line lies inside the face. Real primary supports are A120/680, B120/380, with proper boundary timbers. V pitch does not change, so the direct line coordinates must remain unchanged; the test instead confirms their exact typed refs, true supports and recomputed parent-cell bounds. Two U guides must move to the independent literal values. Source token, ruleKey/highwater, applications and bindings survive.

Parameter preview reports both formal grids and guide coordinates; preview/cancel leave full native dump, objects, references, engineering state, definition hash and revision unchanged. Confirm changes the definition hash and advances revision. Undo/Redo restore complete World and matching definition hash while revision advances, never rewinds. The one-binding anchor edit preserves the source, A binding and all A grid/guide/timber records. Only B U fraction and resulting translations may change.

Negative parameter input is **902**, not901: 902 has an integral one-half anchor but is not divisible by3, allowing the test to pin `DIVISION_NOT_EXACT`. 901 could fail earlier at B's fractional-anchor guard and would not prove division rejection. An additional B fraction4/3 pins the existing I37 declaration guard. Both must refuse with complete data and revision unchanged; invalid previews cannot be confirmed.

Prepared command (root supplies source checkout, exact clean head, fresh bridge and new output directory; r2 has not been executed by this author):

```sh
ulimit -s 16384
python3 -B PATH_TO_PROBE/sr15_probe.py \
  --repo PATH_TO_GEOMETRY_AXIOM \
  --head FULL_CLEAN_HEAD \
  --bridge PATH_TO_FRESH_BRIDGE \
  --out NEW_SR15_R2_OUTPUT_DIRECTORY
```

Run once under the existing command receipt wrapper with a finite outer timeout. The supplied bridge must already be registry-fresh; the probe checks its loaded `/proc/PID/exe` bytes against the supplied binary and records PID, hash and cleanup exit. It fails on dirty/wrong head and refuses to overwrite an output directory. `wire.jsonl` preserves every native command and exact stdout line; `bridge.stderr`, complete snapshots, parameter request files, named checks and failure tracebacks remain in the selected output. Root must keep wrapper stdout/stderr/exit and bind main/integration head separately. Successful native execution would be bounded SR15 data-contract evidence, not the required formal browser UI or complete product acceptance.

No native API field called a per-source fingerprint is assumed. This probe records the exposed whole-definition SHA, exact source parameter token, resolved owner definition and full references, rather than inventing a fingerprint field or using equal line coordinates as identity proof.

## r1 retained failure and r2 correction

Root ran r1 and preserved its executed script and raw result in `sr15-parameter-anchor-r1`. It reached the anchor-preview assertion after successful600→900 preview/cancel/confirm, both guides/direct refs, Undo/Redo and902 semantic refusal/state preservation, then exited1 because the probe incorrectly required only binding1 in `preview.gridBindings`. Native process exit was0. This is a probe assertion error, not evidence of a product failure.

`geometry-web/grid_binding_bridge.inc:219–237` explicitly iterates every before binding, emits its before/after descriptor, then appends newly created bindings. It does not filter unchanged records. `geometry-web/reference_bridge.inc:123` invokes this serializer for the candidate preview. SSOT I37 (`公理層.md:795–802`) and R32 require complete candidate validation and affected dependency reporting, but do not require transport to omit unchanged objects. Accordingly r2 requires exactly two distinct IDs0/1, verifies A's complete before/after record unchanged and matching the prior live A, and verifies B's old definition matches prior live B. B U fraction must change1/2→1/3, V fraction remain1/2, translation1450,-400→1600,-400; fixed U main-line preview550/1450→700/1600 and complete endpoints are asserted. The V preview and all other identity fields stay identical. These assertions apply to both preview attempts. No subset/superset relaxation or product-derived expected values are used.

R2 also replaces the historical absolute ROOT with the explicit repository argument. This affects portability and identity metadata only. The r1 `executed-probe.py`, exit1 and all raw evidence remain unchanged; root must independently review r2 before the serial run.
