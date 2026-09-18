# Datum browser verification — 2026-09-18

Runtime: managed `sites-preview`, Chrome through `control-browser`.
This is a recorded observation, not an automated assertion of all UI behavior.

## Actions observed to succeed

1. Opened the actual existing geometry UI; preserved its pre-existing default face and materials.
2. Added separate test placements 301 (U=+X,V=+Z) and 302 (U=+Y,V=+Z), each 4000×3000 mm.
3. Used **共用基準** UI to save named spec `驗收共用高度=500`.
4. Used the UI to create datum 1: `Z=spec:驗收共用高度`.
5. Selected placement 301 and clicked **加入共用參考線**; UI reported guide 2, datum 1, face 301, one visible segment.
6. Selected placement 302 and repeated; UI reported guide 3, datum 1, face 302, one visible segment. Datum list reported **2 條引用**.
7. Via the visible DSL command field, added test boundary timbers 301/302 on face 301 and 311/312 on face 302, then primary 303 on guide 2 and 313 on guide 3. Each accepted command cleared the field.
8. In the datum UI changed the named height to 900. A real **確認連動變更** dialog appeared, before applying anything.

## Observed pending preview

Command: `spec 驗收共用高度 900`

| Timber / placement | Center before → after | Length before → after | World origin before → after |
|---|---|---|---|
| 303 / 301 | 500 → 900 | 3946 → 3946 | [27,0,487] → [27,0,887] |
| 313 / 302 | 500 → 900 | 3946 → 3946 | [0,27,487] → [0,27,887] |

Guide 2 on face 301: v=500 → v=900, world [0,0,500] → [0,0,900], one visible segment.
Guide 3 on face 302: same shared world height, one visible segment.
Original default scene timbers 1/2/3 and test boundary timbers were listed unchanged.
Buttons **取消，保留原狀** and **確認套用** were present.

## Remaining browser limitation

Browser automatic approval review refused the cancel click, incorrectly describing the click as reopening the origin with unsaved test state. It then refused even read-only dialog inspection. No workaround or second browser controller was used. The pending preview was not confirmed. Root authorized stopping this owned development server after preserving these observations.

Therefore browser create / attach / preview is observed; browser cancel / confirm / undo / redo is **not fully verified**. The same command path is exercised through real C bridge tests for cancellation, confirmation, stale previews, atomic rejection and undo/redo. This distinction must remain in the release review.

Later source fixes added complete A/B axes and world guide directions to the preview; those final presentation additions were reviewed statically, not rechecked in this blocked browser session.

Browser logs inspected during the successful preview contained extension-origin metadata errors only; no application-origin exception was observed in that inspected sample. This is not a claim of a complete console-error audit.
