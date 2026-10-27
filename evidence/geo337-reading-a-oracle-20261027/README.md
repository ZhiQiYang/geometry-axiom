# Recovery F Reading A oracle, reader, RC, and required-eight coverage

All new executions used clean fixed F **cbf0fb621888596aa14ad5f2349b503e23b1b72d**. Product/test bytes and assertions were not changed. Historical L/f64/a4bd executions were not relabelled.

## New completed executions

| Stage | Actual result | Time |
|---|---|---|
| Original golden witness source proof | exit 0; child baseline/withdrawn/restored **0/1/0** | 1.070 s |
| External golden generation | exit 0 | 0.666 s |
| Original byte comparator | exit 0; generated and committed golden identical | 0.032 s |
| `selftest.py --mutants-only` | exit 0 | 22.237 s |
| Complete `selftest.py --quick` | exit 0, no timeout | **391.726 s actual process time** |
| Canonical reader generation | exit 0; output bytes unchanged | 4.080 s |
| Canonical reader `--check` | exit 0 | 1.371 s |
| Original RC builder-whole-face proof | **0/1/0**, actual original assertion kill | all six original method runs completed |
| Original RC checker-whole-face proof | **0/1/0**, actual original assertion kill | no skip/error |

Quick completed at **2026-10-27 03:43:34.939 UTC / 11:43:34 Taipei**. It prints a **368-second internal scan timer** and **39,850 build count** (not all internal builds). Coverage includes rectangle one-dimensional per-mm and two-dimensional scans; 579 concave/alcove/column rooms × 8 layouts; 410 step rooms × 8; 820 mirrored step rooms × 8; 1872 odd-gap runs. Frozen positives: **528 step + 1056 mirrored**, **0 missing, 0 non-buildable**. Scan failures: **0**. Original known-defect classifications remain as printed; no rule, golden, tolerance or acceptance whitelist was loosened.

## Same-F executions reused without rerunning

The complete native receipt at **732ef20e34876379a37eb69693a481becebea43e** binds the actual F execution and passed all 230 suites. Copies of original relevant logs and the native request/result are retained here:

- `test_geo318_reading_a_oracle.py`: **14/14, no skip**. This is reuse of the complete native unittest-module execution; no separate new `-v` invocation is claimed.
- Oracle default/CI selftest: original CI sampling **8137 printed builds**, exit 0. This is distinct from the new complete quick scan.
- Reader unit module: **51/51, no skip**; together with the two new original commands above, the AGENTS.md three-command reader verification is complete on F.
- Exact required-eight scope: **681 passed, 0 failed, 0 skipped** across the original eight native rows. `oracle/required-eight-native-originals/COVERAGE.json` maps every row to its current expected count and original logs. This is complete-native coverage; no new standalone selected-stage wrapper execution is claimed.

## Capture and limits

Each stage retains exact argv, cwd, environment, actual SHA, stdout/stderr bytes, actual exit, times, and source/cleanliness guards. Reused originals retain their native identity. The external golden generator never overwrote the committed golden. Reader generation was byte-idempotent. RC variants were created outside the checkout with exactly the original one-anchor substitutions; the worker SHA is the historical pinned **34baecbd743921179327ec0700c9a3915f0a7f498dcf0850c372343b8edf5d4d** and it verifies current Git blobs before running the unchanged method.

The archived original `run_stage.py` assigns 300s (golden proof/generation/reader), 30s (golden compare), 1200s (mutants-only), and 7200s (quick), but actually calls its reaper with `timeout=None`. The new capture enforces those declared caps explicitly; it does not claim the historical wrapper enforced them. RC's 300s cap is a local conservative collection watchdog, not an invented product/CI requirement. No deadline was reached. Stack remains 16 MiB. The already validated process-local subreaper and exclusive task-owner lock are retained; historical container lock paths were not treated as current shared ownership.

Directory mapping: `oracle/` complete oracle capture and reused-native indexes; `reader/` generator/check and reused 51-method logs; `rc/` six precise proof streams and source variants; `tools/` exact launchers and historical command authority. Publication MANIFEST hashes every file. Source and original receipts remain preserved locally.

## Continuing scope

PF3's full 20-case baseline/restored and 19 semantic-removal controls are not replaced by native. Its original command and child 900-second limits have been verified as the next independent missing scope. Six browser jobs remain owned by the other task. Card/axiom/extra168 are not duplicated here. No P-189 comparator, axiom, main merge, deployment or paid operation was changed.
