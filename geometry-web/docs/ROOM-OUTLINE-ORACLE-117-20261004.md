# P79 independent rotation oracle (#117)

The existing page-4 CropBox/rotation checks calculated expected points through
the same `feUlImgToMm` used to create the room candidate. A shared conversion
error could therefore pass both sides. Expected now uses four fixed arrays
derived from the unchanged public PDF fixture, without a product mapping helper.

Page 4 has viewport dimensions 190×280 after its CropBox and inherent 90°
rotation. The authored inside corners become (158,32), (158,228), (42,228),
(42,32). At 10 mm per viewport unit, offset (−200,150), the centre is
(750,1550). Hand-calculated quarter turns supply the checked coordinates.
Crop, PDF parser, actual candidate extraction, native confirmation, all existing
assertions and the P84 invocation remain unchanged. No registration or floor
changes were made.

## Focused validation

Linux cloud, Chromium, isolated service on 127.0.0.1:18850; runtime probe reported
`fresh:true`. Bridge and model-base were compiled from main e09d78d. The actual
unchanged `cdp_test.js` runner used `GEOMETRY_ROOM_OUTLINE_ONLY=1`.

| Actual browser run | Outcome |
|---|---|
| Changed test, good product | Exit 0; completed; P79 84 + P84 33 = 117 pass, 0 fail, 0 skipped, 0 uncaught browser exceptions |
| Original e09d78d test, +17 mm helper mutation | Exit 0; completed; same 117/0, all four rotation assertions passed |
| Changed test, same +17 mm helper mutation | Exit 1; stopped at existing 0° rotation assertion; 53 prior passes, 1 expected failure |

The mutation ran only in the isolated browser's live `feUlImgToMm`, scoped to
page 4 / viewport 190×280 / offset (−200,150) / scale 10. Native code, real PDF
parser and candidate extraction still ran. Original test source was loaded from
immutable e09d78d into the Node module in memory; no product source was reverted
or mutated on disk. The old oracle made 36 live mutation hits across the four
rotations and still passed. Its helper was restored before the next native reset;
the failing changed-test browser was closed. Separate fresh profiles were used.

For example the helper moved (220,470) to (237,470), to integer-mm precision.
The original expected accepted the same shift; the fixed expected rejected it.
This is actual browser sensitivity evidence, beyond the earlier VM-only probe.

Raw logs, mutation preload, independent arithmetic/review and `run-results.json`
are retained at `/workspace/quality-audit-117-118/implementation/` in the saved
cloud task workspace. Mutation log names are `p79-before-mutant.log` and
`p79-after-mutant.log`; the good log is `p79-good.log`.

This is the focused mixed-input P79/P84 regression scope. Full CDP, Windows/WSL
and the complete formal PDF→space→save/reopen journey were not validated here.
No direction semantics, capacity, app/space product code or external local work
were changed. This PR addresses only the circular expected portion of #117.
