# PR130 independent cloud QA — synthetic review evidence

The original PR130 head is `e06ff2a136fccc42d55a5b86f6bb2873ff146a4a`, based on frozen main `8d134fcb08041708ac174c11185f175cfa369c4a`. The isolated repair is **`0b2cbe34c571605f3c62aa652ee42815f747c96e`**. Its only production change is definition-diagram presentation; it also corrects the axis-card selector documentation and adds eight independent geometric expectation tests.

Review the repair independently: [code commit](https://github.com/ZhiQiYang/geometry-axiom/commit/0b2cbe34c571605f3c62aa652ee42815f747c96e), [diff from delivered head](https://github.com/ZhiQiYang/geometry-axiom/compare/e06ff2a136fccc42d55a5b86f6bb2873ff146a4a...0b2cbe34c571605f3c62aa652ee42815f747c96e). This evidence is a separate documentation commit; it does not alter the tested repair or its runtime assets.

Only synthetic QA parameters/grids/Worlds and repository-authored test fixtures are included. No user Downloads HTML, private case data, browser profiles, or original project attachments were uploaded. The existing design reference PNG was inspected in place and was not duplicated. Local comprehensive evidence remains outside this repository.

**Authorized CSS follow-up:** `b824c0f7985ae5b245b4f06679966cd7737d2e79` adds the one-rule P3 positioning fix. [P3-acceptance.md](P3-acceptance.md) records its new exact runtime, desktop/touch-390 mode matrix and affected grid gate. It also retains a newly reproduced pre-existing first-click defect; the earlier full-mode counts below belong to `0b2cbe3` and were not rerun for the CSS-only change.

## Verified repairs

- **Panel zero-line coordinate:** panel 400, gap 5, raw anchor -100 produces effective phase 302 under D29. The original diagram labels raw `u -100` under “第 0 線”, while the main plot shows 302mm. The repair labels `shape.phase`, preserving the anchor field and ParameterRef/click target.
- **Large signed stagger:** u600/v400 with u stagger -60001 originally draws zero u segments in the schematic; +60001 draws four instead of six. The transposed v-axis cases draw zero/six instead of ten. Eight desktop/390px cases are native-accepted. The repair selects visible indices per band's signed shift; all eight diagrams now have the expected six/ten segments. Native formulas and legal signed values are unchanged.
- **DOM contract:** documentation now uses `.ig-axis[data-ig-axis]` instead of an obsolete fieldset selector.

## Raw terminal receipts

| Verification | Delivered head | Repair head |
|---|---:|---:|
| Composition CDP | 52 pass / 0 fail / 0 skip | 52 / 0 / 0 |
| Grid CDP | 145 / 0 / 0 | 145 / 0 / 0 |
| True ZIP portable browser gate | 91 / 0 | 91 / 0 |
| Raw provenance browser gate | 113 / 0 | 113 / 0 |
| Full CDP | 1994 / 0 / 0, 82 sections matched | 1994 / 0 / 0, 82 sections matched |
| New independent geometry tests | 1 pass / 7 fail | 8 pass / 0 fail |
| Normal UI/panel checks, 1400×1000 and 390×844 | 61 pass / 2 fail | 63 pass / 0 fail |

Both full-mode receipts have **one exception event**: the intentionally injected P38 `Error: fb-auto-probe`. Both log it as `[EXPECTED EXCEPTION]`, exit 0, and have no unexpected exception. Short gates and normal browser flows have zero exceptions. Do not rewrite the full-mode exception counter as zero.

The full-CDP terminal files preserve the expected-exception line and the verbatim terminal block beginning at `CDP_SECTIONS`; the other logs are verbatim complete gate outputs. Logs use lossless gzip compression to preserve terminal whitespace; inspect them with `gzip -cd logs/<name>.log.gz`. The manifest records both compressed and decoded SHA-256 hashes. [gate-receipts.json](gate-receipts.json) indexes them. Counts are assertions, not end-to-end scenario counts. No floor, golden, or existing oracle was reduced; no final run skipped any group. Composition/grid/trial drag checks executed against the latest source.

The normal flow uses real controls to create `(915,1830)` parameter fields, bind grid u/v sources, click definition chips and axis titles, preview/cancel/confirm, modify grid phase and upstream parameter, remove/reopen stagger without losing the saved native source, download a true ZIP, open it in a fresh context, and undo/redo a new native transaction. Both source refs remain explicit. Ordinary final ZIPs use the supported `geometry-canvas/6`; raw/PDF portable gates use v10. ZIPs do not claim to preserve undo history.

[fresh-zip-results.json](fresh-zip-results.json) adds four fresh-context cases (original/fix × desktop/390px): use the actual File → New Project command, prove the native dump is empty, then File → Open Project's chooser loads the previously downloaded ZIP. Eight blank/restore checks pass, and the restored dump equals `world.scene` byte-for-byte. Source definitions in these records are synthetic QA data.

Runtime, binary hashes, trees and clean worktree states are recorded in [identity.json](identity.json). Linux Chromium 151, Node 24, Python 3.12, GCC 14.2; isolated native C/Python services. This is responsive Chromium validation, not a physical phone, OS chooser, IME, Safari or Firefox certification.

## Remaining scoped findings

- The P3 dimension-chip positioning issue in `0b2cbe3` is fixed by the authorized CSS follow-up `b824c0f`; [P3-proposal.md](P3-proposal.md) retains the historical browser-only prototype. An existing input-change redraw can swallow the first chip click after editing; its before/after reproduction and bounded CSS validation are in [P3-acceptance.md](P3-acceptance.md).
- At 390px, the feedback button covers the center of the create-grid menu item after editing a parameter. Base `8d134fc` and delivered PR130 have the same hit rectangles; this is a pre-existing issue. The normal flow used the unobscured lower edge, without hiding the feedback UI or forcing clicks. It is outside this diagram repair.
- CI run `37229673271` has seven failed jobs with no runner steps, so it supplies no product execution evidence. Local gates above ran independently.
- PR130's original author short-gate raw receipts were not present in the delivered files. The four claimed counts were independently reproduced here.
- PR126 store/reference/native interfaces and PR125 were not modified. This does not claim completion of the #61 source-subrule editor. Advanced trial remains presentation-only; `space_model_test.js` is outside full CDP and was not additionally certified.

The remote review branch contains the diagram repair, its evidence, the separately authorized one-rule CSS repair and CSS evidence. Neither main nor the original PR130 branch was changed or force-pushed. Root should independently review the code commits before arranging a safe return to PR130.
