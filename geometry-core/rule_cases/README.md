# Finite native rule cases — #49

Standalone first slice under the user's adopted item 6: six finite authoring
cases, native isolation, retained receipts and honest freshness. It does not
register an archive format or capability, add app entry points, or change
`project-store`, ContextHistory, the native core, the bridge or #85's framework.
The `rule-case/1` token identifies this module's bounded input contract only.

Read [AGENTS](../../AGENTS.md), [D32/D33/I40/I41/R34](../../公理層.md),
[Q35](../../geometry-guide/CONTINUATION-DECISIONS-20261003.md#q35) and
[WP49](../../geometry-guide/CONTINUATION-WORK-PACKAGES-20261003.md#wp49).
This implementation uses only the user-approved six examples; it does not
adopt the additional future behaviors in the broader issue proposal.

## Run and verify

From the repository root:

```sh
python tests/binaries.py build bridge
PYTHONPATH=geometry-core python -m rule_cases --output /tmp/rule-case-receipts.json
python -m unittest tests.test_rule_case_definition tests.test_rule_case_catalog tests.test_rule_case_executor
```

The CLI returns 0 only if all selected cases pass; otherwise 2. On the current
native diagnostic contract the complete set deliberately returns 2: four
positive cases pass and two exact negative expectations remain blocked.
Use repeated `--case <built-in-id>` to select the three-case first slice or
an individual built-in. It does not accept uploaded programs or scene scripts.
The output path and binary path are host CLI options, never case fields.

| Case | Expected behavior | Current precise diagnostic gap |
| --- | --- | --- |
| `same-role-distinct-members` | Members 11 and 37 both use role 7; joints target each exact member | None |
| `one-local-joint-new-version` | Publish version 2, change joint 101 only; joint 203, version 1 and binding 29 stay fixed | None |
| `wrong-type-dimension-reference` | Reject parameter 41 field 9 changing dimension to count; preserve World | Native only returns generic `ASSEMBLY_INVALID / I40/I41` |
| `legal-rule` | Publish a rule without materials or geometry | None |
| `legal-incomplete-binding` | Store unset material/face/orientation with native completeness false | None |
| `fixed-version-immutable` | Reject rename/reorder under fixed version 17@1; preserve World and binding | Same generic diagnostic |

Names and list order never select an observed record. Joint comparison includes
the complete typed joint tuple, rather than checking merely that a joint exists.

## Interfaces for root and the shared integration owner

```python
from rule_cases.catalog import cases
from rule_cases import NativeExecutor, validate_case, refresh_receipt
from rule_cases.runtime import runtime_identity

definition = validate_case(cases()[0])
receipt = NativeExecutor(binary_path).run(
    definition, project_id=project_identity, generation=case_generation)
identity, _ = runtime_identity(binary_path)
display_receipt = refresh_receipt(receipt, current_definition, identity,
    project_id=current_project_identity, generation=current_case_generation)
```

`validate_case` accepts typed `setup` and `transaction` operation arrays, exact
source pins, required capabilities, an author expectation and finite predicates.
`decode_case` additionally rejects duplicate JSON keys, nonfinite values and
oversized UTF-8 input. `validate_cases` rejects duplicate case IDs and sets over
six. Source pins cover every setup record; all referenced source records and
fields must be present. Native validation remains authoritative for rule
legality, parameter types and fixed versions. Labels are part of definitionHash:
renaming a case makes a retained receipt stale, without altering its evidence.

Setup must close on its own sources; a source added only by the later
transaction cannot make setup valid. Exact native rule/binding read-back
comparison permits only identity-array canonicalization (order is not identity).
Parameter/material pins attest the submitted payload, not a comprehensive
native read-back audit of those records in this first slice.

The host must preserve the full definition separately from receipts and own the
actual project attachment/schema/legacy gate. No formal capability or project
format number is reserved by this slice. The integration owner also owns
async project/generation matching, cancellation, UI, history, dirty state and
save/reopen. The module neither reads nor writes those contexts; scope is echoed
in each receipt and the freshness helper checks it before reuse. Actual
save/reopen and browser context switching remain integration acceptance work.
`refresh_receipt` bounds retained host JSON to 4 MiB, depth 32 and 65536 nodes
before copying. A retained green also requires complete native evidence,
successful finite assertions and matching rule/binding pins for the same
definition. Malformed data raises `ReceiptValidationError`; the integration
owner preserves its original blob and decides import policy. The helper checks
consistency and freshness; it is not a signature proving a receipt's authenticity.

Required native-owner interface, **reported rather than implemented here**:

- Wrong dimension type: a specific typed code and clause, source
  `{kind:"parameter", id:41, fieldId:9}`, ideally also the binding slot/axis.
  Built-in expected token is `DIMENSION_TYPE / D33`; root/native owner must
  agree the final code naming before wiring or changing this expectation.
- Immutable rule: `RULE_VERSION_IMMUTABLE / D32` and
  `{kind:"rule", id:17, version:1}`.

Only exact `code`, `clause` and `ref` equality can satisfy a negative diagnostic.
Raw native human messages are retained but never parsed. A generic native
rejection remains `blocked` with `reason:"diagnostic-unavailable"`, while actual
outcome and independent World/pin assertions remain visible. Any other error,
setup failure, outcome mismatch or assertion mismatch cannot satisfy a negative.

## Isolation, limits and receipt identity

Each run verifies the existing registry's source closure and binary SHA, copies
that verified binary into a private TEMP directory, starts a fresh native
process, resets **only that private World**, then uses native authoring
preview/confirm/read/dump. No HTTP service, formal World, user token, feedback
or history path is passed into the executor. Private transaction paths are
generated by the host. Rejected preview confirmation is exercised, and the
complete native read, revision and dump must stay unchanged.

Limits: 64 KiB/case, depth 16, 4096 JSON nodes, 32 operations per stage,
32 predicates, six definitions/set, two concurrent runs per Python host, 2 MiB combined
stdout/stderr and 5 seconds native wall time by default (host maximum 30).
Cancellation, output and concurrency capacity are explicit non-pass results.
POSIX cleanup kills the private process group even if its leader exited.
Windows cleanup is limited to the verified bridge process, which launches no
children; the forked-descendant boundary test is POSIX-only. Native code is
trusted application code here, not a general executable sandbox.

Receipts retain authorExpected separately from actualOutcome/actualDiagnostics,
finite assertion results, before/after typed states and dump hashes, project
identity/generation, private native PID, cleanup and execution conditions.
They include exact definition/source hashes, native binary/source identity,
normalized axiom hash, validator module hash and predicate-schema hash. Unknown
binary identity is `unknown-runtime`, never green; source/definition/runtime
drift turns a copied historical receipt `stale` and retains recordedStatus and
evidence. Editing loaded validator files requires a fresh Python process.

Tests use real fresh native binaries for the six-case results and for isolation
from a separate World with a pending native preview. Small test-owned process
controls verify crash/timeout/output cleanup; those are never accepted as
product case passes. Existing #85 mutation inventory/runner remains its owner's
responsibility. No deployment or merge is performed by this module.

## Validation evidence for this draft slice

Module/test code head `26854b1fe257b32a808a123bd2ca36f10d940010`, based on main
`1075058be37d37b98a2a910f4f67b87583be85b3` (including the #85 owner's PR).
This section is documentation only; the implementation/test blobs at that head
identify the verified code. No existing app/native/serializer/test-runner file
is modified by this slice.

- Independent review: all 76 tests in the three new suites passed (exit 0,
  2.272 seconds); `git diff --check` passed. The review's malformed-green receipt,
  cleanup and bool/integer diagnostic findings were corrected and rechecked.
- Existing native regression: `python -m unittest tests.test_assembly_rules
  tests.test_assembly_capacity tests.test_assembly_parameter_refs` passed all
  43 tests (exit 0). These are source-compatible authoring checks, not browser
  integration acceptance.
- Six-case CLI on the same code returned exit 2, with four passed and two
  blocked/diagnostic-unavailable. Six distinct native PIDs were observed and
  all private directories removed. Cloud receipts are in
  `/tmp/geometry-rule-cases-49/receipts-26854b1.json` for root inspection; the
  command above regenerates them without a live user service.
- Native source fingerprint:
  `605b584465fa835b205c21a0ae4ac584c2d3f667e694d20ca4a590ad2fa7ff5b`.
  Native binary SHA-256:
  `13725afc9d7cbfbd49874727c9e26f7c8c076bd7b3021f2192debeaa5ba53854`.

Remaining integration work belongs to root/shared owners: final attachment
envelope/schema/capability, bounded background transport to this executor,
contextToken-based attachment writes, formal save/reopen and browser/late-result
acceptance, plus registration of these suites/count floors in the shared runner.
No new app API, archive capability or UI is claimed complete here. Both exact
negative diagnostics need the native owner interface listed above.

The later [PR100 draft comparison](INTEGRATION-PR100.md) records the remaining
bundle-validator/reference/generation seams and the unregistered
`run_case_request` helper for the shared serve owner. Its five focused tests
are `python -m unittest tests.test_rule_case_request`; changing this helper
also changes validatorVersion, so previous receipts are rechecked as history.
