# Definition source and dependency receipt

Source: `8aa1ef13a62a51ea27b58e601765691c9257d91b`.
All twelve portable suites executed from a Git archive of this fixed commit.
The source worktree was clean when the receipt was recorded.

```text
python tests/geometry_kernel_receipt.py --suite-set definition-sources --source 8aa1ef13a62a51ea27b58e601765691c9257d91b --out <TEMP>/geometry-tests/definition-sources-8aa1ef13
```

All 167 discovered tests passed with zero failures or skips. The receipt retains
the frozen source inventory, exact suite counts, per-suite JSON and raw logs.
It includes the earlier rectangular consumer and source-runtime coverage, plus:

- Native `unevaluated` sources require `value: null`, retain their typed
  descriptors and map to `SourceStatus.INCOMPLETE`. An `ok` source still must
  contain a value; no other status may contain one.
- Definition-required and evaluate-before dependencies preserve unevaluated
  definition and quantity nodes without blocking a complete dependent box.
  Changing either edge to value-required produces `SOURCE_UNAVAILABLE` and no
  partial geometry.
- Neutral `DefinitionValue` preserves the provider's exact schema and opaque
  bytes, including NUL, non-UTF-8 and empty content. Candidate fingerprints
  distinguish schema or content changes. Definition payloads require scalar
  units and canonical standard Base64; invalid schema, shape, units, or
  noncanonical padding bits are rejected.
- Eight executions of copied-production negative controls test transport and
  consumption guards, including status/value mismatch, incorrect unevaluated
  mapping, noncanonical Base64 acceptance and dropped definition bytes. Every
  altered implementation fails its intended oracle; the restored baseline
  passes. The isolated pure-core set now contains 86 tests.

Compared with the preceding 154-test receipt, the manifest deltas are
`test_geometry_host_sources` 17 -> 26, `test_geometry_kernel_graph` 27 -> 30,
and `test_geometry_kernel_session` 4 -> 5. Historical receipt presets remain
unchanged; the final integration manifest is owned by the integration lane.

This command uses synthetic native-result fixtures and executes no native code.
It does not run the two tests in `tests/test_rectangular_bridge.py`, prove
actual C-to-Python transport, or establish complete native graph coverage.
Incomplete coverage still fails closed, the default application loader remains
unchanged, and final combined integration acceptance remains pending in #248.
