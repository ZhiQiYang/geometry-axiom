# Follow-up scope review after fixed-F P52

No new product test was run in this review. P52 original formal/verifier passed and was published at `a08a036db335e88608ead761539d3e60b75e8e5d`.

## #314 existing acceptance coverage

Fixed F `cbf0fb621888596aa14ad5f2349b503e23b1b72d` already ran all six requested native suites: **103 passed, zero fail/skip**, and all **12 GEO263 inspector subtests** inside the original Node run (**737 passed, zero fail/skip** overall). Complete original suite/Node stdout was extracted byte-for-byte from the accepted native archive, not regenerated.

M121 remains **killed**, with original execution SHA `82c922a3941525d3a094ac0158bdc7dea57ea360`. Its original build/test/restoration streams and sidecars match the hashes in F's adopted ledger; baseline/mutant/restored test exits are **0/1/0**, test counts **43/2/43**, and source byte restoration is true. The two original named methods are indexed in geo314/COVERAGE.json. The existing accepted F native mutation freshness check establishes the adopted ledger's current validity; no targeted mutation rerun was performed and no historical SHA was relabelled.

The native invocation did not request the optional GEOMETRY_263_TRANSCRIPT sidecar. Its absence is explicit; this review supplies actual original Node stdout, not an invented standalone protocol transcript. Test assertion coverage is already present and is not duplicated.

## Whole-memo specific missing original inputs

The original prepared v2 tool is fixed to actual **F8 `75a1e93811a52b69385cbdaf6a09d773ed9052ad`**, and pins the exact original R8 formal receipt. That original receipt and the excluded-ELF inventory were recovered and verified byte-for-byte from the published archive. F8-to-F comparison of the complete product directories and current_geometry.c shows only the two architecture documentation/receipt changes; product code is unchanged. Any future memo execution must still report actual F8 identity. The valid R8 performance samples are not rerun, and its original outer red remains red.

The three required original ELF bodies at `/tmp/g337323R8/work/{base-pg,fix,fix-trace}/bridge` are absent here and expressly excluded from the published archive. A local workspace/tmp search hashed 25 same-size candidates and found no exact payload match. Exact hashes, sizes and modes are in whole-memo/STATUS.json. This is a missing-original-artifact prerequisite, not a product failure, resource-budget restriction or request to relax the test. A request for the preserving environment/readable original location is pending while other coverage review completes. No binary was rebuilt as a substitute, no original R8 sample was redrawn, and no P189 comparison rule changed.
