# #49 isolated workbench and host handoff

> Historical standalone-owner handoff for #141. The current app integrates these
> components through #146, including the registered `rule-cases` attachment and
> `geometry-canvas/15`. Statements below about pending host routes or format
> allocation describe that earlier checkpoint. Current formal app, history and
> ZIP acceptance requirements are in [INTEGRATION-GATES.md](../../../tests/INTEGRATION-GATES.md).

Base: actual main `6ee719d0e4ba3740e2f0b93223b323838f6a20f8`.
The branch owns only new `rule-case-workbench*` JS/CSS, `rule_case_workbench*`
Python files, its new tests and this documentation directory. Open #137 owns
app/index/serve/project-store/reference-workspace/feature-attachments/
assembly-workspace and shared registries/floors/BACKLOG; none are edited here.
No C, axioms, security settings, deployment or private source materials change.

## Integration ports

`RuleCaseWorkbench.mount(element, ports)` returns a promise with an immediate
`teardown()` method and resolves to a controller. Keep that pending handle and
call `teardown()` even if initialization is still waiting. Both controller and
mount capture original context and subscribe before their first await; a late
open session is closed precisely. A newer mount in the same element retires the
previous pending/mounted operation and a late mount never paints. Host loads
the scoped CSS and JS, chooses an existing AssemblyWorkspace disclosure/tab,
and calls `teardown()` before close. This component adds no formal app entry.
To satisfy GEO-219, the shared owner must merge its eventual entry into the
existing assembly workspace and record the removed/merged entry in BACKLOG.
This branch is expressly authorized as an independent component/harness.

- `captureContext()` synchronously returns `{projectId,generation,contextToken}`.
  Token is the original host token, not a new token obtained after an await.
- `subscribeContext(invalidate)` returns an unsubscribe function. Notify on
  project switch, generation/source/runtime changes, undo/redo, close and reopen, even
  when restoring equal definitions. A retired controller must be remounted.
- `transport`: `httpPort('/rule-cases/workbench')` or an equivalent scoped port.
  HTTP sessions must be isolated per native/project context by the serve owner.
- `loadCaseData(originalContext)` optionally returns the complete attachment.
- `retainCaseData(data, originalContext, lease)` explicitly validates and atomically
  adds one metadata ContextHistory step, dirty state and detached attachment,
  returning `{ok:true,changed:true|false}`. Host rejects a mismatched ORIGINAL
  context, including after a held write, and MUST check `lease.isCurrent()`
  immediately before atomic metadata commit. It includes the exact original
  payload stamp and operation ownership. Reset/import/edit/refresh/retain are
  serialized through completion, including cancellation cleanup. A no-op
  creates no history step.
- `onClose()` optionally closes the enclosing panel; no assembly invalidate is
  invoked. Host catalog/assets/history routing remains host-owned. Case pins
  are private source definitions, never assetrefs or live World selections.

Controller: `select`, `edit({label,transactionName,jointSide?})`, `reset`, `run`,
`cancel`, `restore`, `retain`, `refresh`, `snapshot`, `data`, `invalidate`, `teardown`.
Editing changes only the selected finite definition. Expectations remain an
independent oracle: changing a joint side can intentionally fail its assertion.
No input is evaluated or rendered as executable code/markup by the UI.

## HTTP contract (unregistered)

Owner imports `RuleCaseWorkbenchAdapter(capture_context=..., binary=...)` and
routes bounded same-origin JSON to `dispatch(method,path,body)`. It returns
`(status, result)`; importing installs no route. Capture port is synchronous
and returns exactly the three host context fields above. Scope/binary/timeout/
output settings never come from payload. Call `adapter.invalidate()` on every
host lifecycle change and `adapter.close()` on host shutdown.

POST `/rule-cases/workbench` envelope has exact `protocol` =
`rule-case-workbench/1`, `action` and the following action fields:

| Action | Fields | Result |
| --- | --- | --- |
| open | none | sessionId, original context, runtime, six definitions and hashes |
| validate | sessionId, definition | existing core-validated definition and hash |
| run | sessionId, runId, definition | original context, definitionHash, controlled-run receipt |
| cancel | sessionId, runId | retire that ID even before a late run arrives |
| close | sessionId | idempotently retire session; reopen gets a different session |
| import / assess | sessionId, data | unchanged data, freshness views, historical-unverified trust |

No arbitrary commands/scripts, host overrides or unknown fields are accepted.
Finite definitions reuse `rule_cases.request.run_case_request`, catalog,
definition validation, runtime registry and receipt refresh. One selected run
is serialized per adapter. Native executor retains its global two-run bound,
5-second default/30-second maximum and 2 MiB maximum output. Transport is
bounded to 8 MiB, 16 sessions, 300-second session TTL, 64 IDs per session;
reopen after exhaustion. Cancelled/used IDs never start again. Cancel and close
set native cancel events; final original-scope gates discard late results.
Transport errors are nonpass `{ok:false,code,error}`, without manufacturing an
engine receipt. Native receipts retain their original scope and runtime facts.

## Proposed attachment data; formal allocation is pending

`{schema:'rule-case-workbench-data/1', definitions:[six complete rule-case/1
definitions], receipts:[{definition:complete original run definition,
receipt:original bounded native receipt}]}`.

This is an internal proposed payload schema, not geometry-canvas/14 or /15,
not a registered attachment kind/capability or ZIP manifest allocation. `/14`
belongs to #137. The shared owner allocates those formal identifiers and strict
root format/capability gates. Definitions retain all input/setup/transaction,
sourcePins, requiredCapabilities, author expectations and assertions. At most
24 receipts and 8 MiB aggregate; each receipt has core's 4 MiB/node/depth bound.
Portable receipt/context/executor/conditions/diagnostics/assertion/observation
fields are finite whitelists for every status, including nonpass. Existing core
receipt bounds/evidence checks run first; existing typed operation validation
checks observed record data without adding a geometry engine. Each receipt's
definitionHash/sourceHash/authorExpected must match its ORIGINAL accompanying
definition; different CURRENT definitions legitimately produce stale views.
Unknown fields/schema, wrong closure/pins, unknown case IDs and malformed
receipts reject before replacement. No implicit eviction truncates history.

Original definition/receipt bytes remain data-equivalent on freshness refresh.
A separate view checks exact definition/source/runtime/project/generation.
No serialized trust flag can promote an import. Every imported result is
historical-unverified even if fully self-consistent. Only the in-session
controlled run can display current; edits/reset/context retirement remove that
trust permanently. No signing axiom is invented. Selecting/displaying/running
does not write native World, host attachment, dirty state or history. Explicit
retain is the only host metadata-write port.

## Independent harness and evidence plan

`python3 geometry-web/rule_case_workbench_standalone.py --port 8879` serves only
loopback, this component and the same handler. Build/verify bridge beforehand
through `tests/binaries.py`, never pass an unverified fallback executable.
The page's retain/restore buttons use a clearly labeled in-memory port; these
are not evidence of formal .gcanvas/ZIP saving or AssemblyWorkspace integration.

Required evidence: true HTTP/native six cases (4 accepted + 2 precise rejected),
unchanged negative worlds/pins and child/TEMP cleanup; edits/precise diagnostics;
cancel before/while running, close/reopen, old context/generation and delayed
response fences; forged/malformed import and unsupported format/capacity gates;
real browser flows at 1280 and 390 with screenshots and no unexpected console.
Raw runtime logs/screenshots remain TEMP unless separately reviewed for release.
Final evidence and exact test commands are recorded in `VALIDATION.md`.

Remaining shared work: parent independent review, formal format/kind/capability
allocation, existing root catalog/asset/history ports, serve route scope and
lifecycle wiring, AssemblyWorkspace mounting, real ZIP save/reopen/undo/redo,
shared test registration and complete app acceptance. Do not merge or close #49
on the basis of the independent component tests alone.
