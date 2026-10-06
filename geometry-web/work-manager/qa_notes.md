# Independent acceptance verification

Scope: the work-manager tool only. All committed tests use synthetic records;
they do not read product feedback, credentials, actual task transcripts, or
private queue snapshots. Product files and product runtime tests are untouched.

## Execution record

Executed against the current tool implementation:

```sh
python3 -m unittest discover -s geometry-web/work-manager -p test_acceptance.py -v
```

Exit **0**: **46 tests passed** (latest rerun: `Ran 46 tests in 1.164s`, `OK`). This includes
real subprocess CLI calls, a temporary loopback HTTP server, and a real SQLite
concurrent writer. Test clocks use relative UTC times so source freshness does
not make the CLI tests expire after a fixed calendar date.

Python compilation of the acceptance suite and `node --check` on the dashboard
JavaScript both exited **0**.

An independent Chromium/Playwright smoke run with a **mocked synthetic API** at
390 px exited **0**: the HTML attack string remained text, no image element or
script execution appeared, document width was exactly 390 px, page errors were
empty, and a subsequent HTTP 503 preserved the previously rendered rows and
state hash. This smoke run is not evidence of a real queue synchronization.
The integration owner separately verifies actual-state desktop/390 px captures.

## Findings addressed during review

- Reconciliation now opens an explicit read transaction. A concurrent import
  cannot combine old source rows with newer event rows.
- Malformed CI `steps: [{}]` previously produced a false `done` result in both
  evidence and PR-job paths. The failing regression was reproduced; the final
  suite passes with malformed/unexecuted steps unable to certify completion.
- Subsecond event times previously lost precision and could let an older
  independent source replace a newer head. The failing regression was
  reproduced; replay now preserves original timestamp precision.
- A later valid failed verification is exposed as the last verified result;
  an older passing attempt cannot hide that failure or certify completion.
- Stale server code returns 503 until restart. The test changes only the
  fingerprint function via a mock and verifies normal reads recover afterward.
- UI review identified missing PR-only references, criterion/timestamp field
  mismatches, and raw pass badges on expired evidence. The UI owner aligned
  these with the store projection and effective evidence/CI results.
- Follow-up review verified `pr.effective_review_state` distinguishes current
  head validity from the original imported review claim. The focused
  `test_new_head_exposes_old_review_as_expired` test exited **0**. An independent
  synthetic store query returned current head B, imported PR head A, raw
  `approved`, effective `stale`, evidence result `unknown`, delivery
  `verification_pending`, and next action `verify_acceptance`. The UI reads the
  derived field under “目前 head 的審查” and labels the original claim separately.

## Seven later review regressions: red before fixes

The initial suite did not cover seven further cases reported during review.
They were reproduced before their repairs, using only valid legacy input shapes
and synthetic data. Baseline commit:
`00e348bf62f575d63b5df4f081759699a77d6d2c`.

```sh
python3 -m unittest discover -s geometry-web/work-manager -p test_review_regressions.py -v
```

Initial **red** result: exit **1**, **9 tests / 13 failures**, reproducing the
first six issues. The seventh freshness case was then added and independently
ran **red** with exit **1**, one test / one failure, before its repair.

The repaired contract and the later negative-review case are covered by **25
passing cases** (exit **0**, `Ran 25 tests in 0.170s`, `OK`):

1. Unscoped approval constraints default to completion gates and cannot release
   dependent work. Explicit action-only publication holds preserve already
   accepted historical merges without granting permission to publish.
2. Completed actions have structured receipts keyed by task, action and input
   pin. The same input stays out of `ready`; relevant head, owner, acceptance,
   constraints or dependency changes invalidate the receipt. Active executors
   with pending PRs are not offered as duplicate review work. Source refreshes
   and unrelated old-head proofs do not requeue a completed action.
3. Nested malformed CI fields are rejected before commit. Both evidence-CI and
   PR-CI paths retain the previous state hash and remain readable after reopen.
4. Aggregate `approved` claims require an explicit matching `reviewed_sha`.
   Missing pins are unknown; old-head pins are stale even when the PR's current
   head matches the task. Neither can certify current approval or completion.
5. Evidence IDs are immutable within each task. Conflicting content is rejected
   atomically within an event, across events and across batches. Identical
   duplicates remain idempotent, and different tasks may use the same ID.
6. A later old-head proof cannot replace a valid current-head acceptance result.
   It remains in history. A newer failure on the current head still supersedes
   the earlier pass and invalidates the completed action receipt. This also
   covers an entirely missing current-head proof: adding only an old-head proof
   must not change the action pin or requeue a completed verification receipt.
7. A successful repeated observation refreshes the task's verification watermark
   without adding an event or rewriting its timestamp. Partial observations do
   not refresh other tasks; failed fetches preserve the last successful
   watermark. `payload_hash` stays stable while freshness changes `state_hash`.

After the initial red run, positive review fixtures were updated to provide
`reviewed_sha`, and the legacy summary-only completion repro was migrated to the
new explicit receipt format. Distinct synthetic CI attempts now use distinct
evidence IDs. Existing assertions were not weakened.

The missing-current-proof boundary was added as a further focused regression
before its fix. `-k no_current_proof` exited **1** with one failure: acceptance
remained unknown but the input pin changed. After the pin used only applicable
current-head evidence, the full 24-case review suite exited **0**; old-head proof
history was retained and the existing completed receipt stayed effective.

## Negative review pins and legacy-ledger upgrade

Both later findings were reproduced before their fixes. The negative-review
case exited **1** with two failing subcases: `changes_requested` incorrectly
remained current with an old or missing `reviewed_sha`. It now becomes stale or
unknown respectively; a matching current-head pin still preserves the valid
negative conclusion and its raw historical claim.

The initial synthetic legacy-ledger suite exited **1** with **5 tests, 4 failures
and 3 errors**. Nested CI shapes crashed reads, CLI commands produced tracebacks,
the API returned a generic 503, and conflicting historical proof IDs could gain
completion from a newly pinned review. Fixtures directly construct the earlier
SQLite schema; they do not require git history or read a real database.

```sh
python3 -m unittest discover -s geometry-web/work-manager -p test_legacy_upgrade.py -v
```

After the repair, **6 tests passed**, exit **0** (`Ran 6 tests in 0.592s`, `OK`):

- Invalid legacy stores return a readable `store_health` diagnostic through
  reconciliation, `list-ready` and the loopback API, with no ready/done claims.
- Import, assignment, result and restore attempts are rejected without changing
  the original database bytes or removing conflicting rows.
- An exact-byte private backup has the expected checksum and 0600 permissions;
  API diagnostics do not expose its local path.
- A healthy legacy store remains readable without a rewrite and can accept a
  valid new review pin. The guard does not freeze all older databases.

## Inventory and umbrella coverage

```sh
python3 -m unittest discover -s geometry-web/work-manager -p test_coverage.py -v
```

**9 tests passed**, exit **0** (`Ran 9 tests in 0.147s`, `OK`). All repositories,
issue numbers, PR numbers and task mappings in these checks are synthetic.

- A 26-issue fixture across two repositories counts repository/issue identities
  correctly; multiple tasks or repeated observations do not inflate counts.
- Umbrella nodes preserve their own historical facts but stay unknown and
  unassignable; parent relationships do not become execution dependencies.
- Missing scope, uncaptured issues and umbrella-only mappings remain visible.
- New, older and failed inventory observations preserve leaf completion,
  owners, proofs and completed-action pins. Partial and complete inventory
  updates change coverage without deleting work records.
- PR references deduplicate across task refs, PR facts and inventory mappings.
  No mapping is inferred from a task ID that resembles an issue or PR number.
- Unknown mappings and failed-source inventory payloads reject atomically.

## Observation adapter review

The adapter was reviewed independently using synthetic repositories and private
temporary ledgers. Before any adapter repair, four regressions failed in one
run (`Ran 4 tests in 0.025s`, **4 failures**, exit **1**): cross-repository numeric
task ID collisions, same-name jobs from different runs hiding a failure, runs
without jobs becoming an empty successful CI set, and failed run metadata being
overridden by passing job details.

A fifth focused regression then failed (`Ran 1 test in 0.010s`, exit **1**): a
new poll of an unchanged older remote PR head rolled a newer task head backward,
reviving the old review. The poll timestamp is not a new PR revision.

Two further focused runs were red: a later independently recorded review
changed the event generated from an unchanged observation (**1 failure**, exit
**1**), and two issue aliases referring to one existing task produced duplicate
event IDs (**1 error**, exit **1**).

The same collision guard was also tested with an existing PR-only reference
in the same repository (**1 failure** before repair). A newer remote metadata
timestamp was tested separately and likewise could overwrite an explicitly
recorded work head (**1 failure** before repair).

Four independent positive cases also pass: unchanged observations reuse
events and preserve completed receipts, aliases retain owner/review/approval and
scope, partial observations retain unseen work, and malformed inputs leave the
database bytes unchanged.

```sh
python3 -m unittest discover -s geometry-web/work-manager -p test_adapter_independent.py -v
```

After repair, all **13 tests passed**, exit **0** (`Ran 13 tests in 0.129s`,
`OK`). CI run failures and missing execution detail remain in derived
`ci_runs`; no fake job is required. Explicit work-head provenance remains
separate from the PR's published head even when remote metadata is newer.
Metadata events do not copy independently recorded review facts.

Two existing review/receipt fixtures now supply explicit `head_sha` when
intentionally advancing the work head. Their original approval, readiness and
receipt invalidation assertions were preserved; an observed PR head alone no
longer overwrites an explicit work-head record.

## Required checks

- Idempotent imports; conflicting IDs; older source and event versions.
- Transactional batch rejection, close/reopen persistence, checksum restoration.
- Exact-head acceptance and merge proof; changed-head stale evidence.
- Empty/no-runner CI is unexecuted; blocked is never complete.
- Stopped executors retain the delivery gap; a submitted PR remains pending review.
- File ownership conflicts, directory overlap, dependency cycles.
- Missing owners, future schedules, approval gates, failed/unknown sources.
- CLI/API/UI state hash consistency; loopback read-only API; XSS-safe rendering.
- Actual desktop and 390 px browser verification and screenshots are owned by the parent.

All **99 independent automated cases pass**. No remaining blocker was found in
this test scope. Private live inputs, final actual-state screenshots, commit
identity, and draft PR delivery remain the integration owner's deliverables.

The pre-adapter combined tool suite also passed, including the implementation owner's
23 focused tests:

```sh
python3 -m unittest discover -s geometry-web/work-manager -p 'test_*.py' -v
```

Exit **0**: `Ran 109 tests in 2.158s`, `OK`. This run used synthetic temporary
stores only and did not modify the live queue.

After the adapter and explicit work-head provenance changes, the final combined
suite includes the 99 independent cases and 43 implementation-owner cases:

```sh
python3 -m unittest discover -s geometry-web/work-manager -p 'test_*.py'
```

Exit **0**: `Ran 142 tests in 2.456s`, `OK`. The new review and receipt fixtures
retain their original assertions with an explicitly supplied work head. All
adapter checks and the previously passing legacy/coverage checks are included.

## Environment evidence

- Chromium is available in the cloud environment.
- Node resolves `playwright` from the preinstalled runtime dependency tree.
- Repository `AGENTS.md` and `geometry-guide/PRODUCT-VISION.md` were read.
- The workspace `.agents` directory is empty. No local skill instructions were present there.
