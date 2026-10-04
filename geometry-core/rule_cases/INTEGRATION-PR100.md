# PR100 draft interface comparison — #49

Compared against `geometry-guide/IMPLEMENTATION-QUEUE-20261004.md` at exact draft
head `0230e436870ec3ba06fcb0735ffabc3b7427979d`. The draft is not a main API.
Its single writer, bounded JSON, isolated execution, fixed six-case scope and
context-token write rules agree with this module. No archive format/capability
or app route is registered by this comparison.

Rechecked merged main `b3c210791d128dc84c3222078df2472b70cc0e60`: the owner
and shared seams are unchanged, and its added known/capable native runtime
fingerprint freshness requirement is already covered by exact executor identity.
That main has no new typed assembly diagnostics. Root's explicit 2026-10-04
04:14 assignment designates thread `01a1050d-60bf-7207-844c-08bf99a520b0` as the
unique native writer, with the precise #49 diagnostic slice before subdivision.
This module owns only its finite cases/executor/tests; transport/save/app remain
the shared integration owner's scope.

## Required shared-owner decisions

| Draft seam | Current module / precise remaining interface |
| --- | --- |
| `records[{kind,schema,value}]` | Target kind `rule-cases`; shared owner assigns outer feature schema/capability. Singular `rule-case/1` describes one definition, not the attachment or a native capability. The saved value needs both a bounded `definitions` collection and a bounded `receipts` collection; CLI receipts alone cannot reproduce cases. These field names are a proposed mapping for owner review, not a registered saved format. |
| `validate(value)` | `validate_cases(definitions)` validates at most six unique complete definitions. `refresh_receipt` checks consumed context/freshness/runtime/stale-history field shapes for every status and validates bounded evidence/freshness, but is **not** a persistence validator: well-formed nonpass host receipts can retain unrecognized metadata. Before registration, the feature adapter must reject unknown persisted fields, pair each receipt with its definition, specify receipt/history count and aggregate byte limit, and reject unknown bundle/receipt schema. |
| `references(value)` | Draft has not fixed its return shape. All six fixtures' rule/binding/parameter/material identities belong to their private case World. The formal World and asset-reference collection is empty. Never translate `sourcePins.ref` to a live reference by ID/name. The feature adapter can return the agreed empty reference collection after validating the local case closure. |
| fixtures | `catalog.cases()` / `case(id)` return independent editable copies of the fixed six fixtures. No shared context or mutable fixture is held. |
| run transport | Shared serve owner can call `run_case_request(body, project_id=..., generation=..., binary=..., cancel=...)`. Body is one bounded UTF-8 `rule-case/1` JSON definition. Scope, verified executable path and cancellation are host arguments. The helper registers no HTTP endpoint, creates no attachment and touches no live bridge. |
| run response | Plain JSON receipt has `caseId`, `definitionHash`, `sourceHash`, `executor`, `context:{projectId,generation}`, `status`, `authorExpected`, `actualOutcome`, `actualDiagnostics`, `assertionResults`, `conditions`; runs reaching the before/after observation stage also have `observations`. Failure-specific fields and stale history remain separate. Root decides the strict saved receipt representation. |
| context/history | Caller captures contextToken before read/run; rechecks active project and per-case generation, then uses the **original** token with `setFeatureAttachment`. Python project/generation echo does not replace history-frame, busy, no-op or dirty gates. Never persist contextToken or a native preview token. |
| generation/history | Owner must define whether generation is edit/request epoch and how concurrent reruns, reopen and A/B restoration allocate it. An old response must not overwrite a newer request just because definition hashes match. Retained history may keep original scope; it must not be relabeled as a newly executed result. |
| source freshness | Current checks cover the exact embedded definition/local source closure and validator/native identity. Changes to unrelated live same-numbered objects do not affect a fixture. A future explicitly selected live-source case needs a captured source snapshot and an authoritative current-pin adapter; missing/ambiguous origin stays nonpass/stale, without an incarnation ledger or name/ID fallback. |

Per-case `requiredCapabilities` are native execution requirements. They are
distinct from the attachment-reading capability that the shared owner allocates;
understanding stored case data does not imply the native executor can run it.

Bounds currently implemented: six definitions; 64 KiB, depth 16, 4096 nodes per
definition; retained host receipt guard 4 MiB, depth 32, 65536 nodes per receipt.
The shared attachment needs its own aggregate/count gate; the per-receipt guard
must not be used as an unlimited history allowance. Host `reason`/`detail` can
contain environment paths; the saved representation needs a whitelist of
portable fields while retaining honest failure status/evidence. No human message
is parsed to decide a verdict.

## Runnable backend seam

```python
from rule_cases import run_case_request

# The shared owner supplies scope and binary from its own request/runtime gate.
# Case JSON cannot supply paths, scope overrides, context tokens or programs.
receipt = run_case_request(case_json_bytes,
    project_id=captured_project_id, generation=captured_case_generation,
    binary=verified_bridge_path, cancel=cancellation_event)
# Only the shared attachment adapter may persist after original-token checks.
```

Definition errors raise `CaseDefinitionError` before runtime lookup or process
creation. Valid definitions return native receipts, including unknown-runtime,
missing-capability, cancellation and precise-negative diagnostic gaps. The new
focused tests use the real registry-verified native bridge; they never install
a route or manipulate a shared project context.

Remaining native-owner gap is unchanged: specific wrong dimension-type
code/clause/parameter+field ref, and immutable code/clause/rule+version ref.
Both negative built-ins remain blocked while the current bridge supplies only
`ASSEMBLY_INVALID / I40/I41`.
