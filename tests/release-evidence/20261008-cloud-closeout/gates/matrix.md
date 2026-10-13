# Audited gate evidence

Each row covers one executed scope. Counts come from canonical result records; release wrapper success alone is insufficient. Historical gate directories already present before this audit are not overwritten. Missing exit codes remain unknown.

## Integration scopes

| Gate | Head | Observed result | Command / gate exit | Finding |
|---|---|---|---|---|
| [async-original-r2](async-original-r2/audit.json) | 5174a8dafd8c | {"observed": 12, "passed": 12, "failed": 0} | 0 / 0 | bounded-pass |
| [compound-project](compound-project/audit.json) | 5174a8dafd8c | {"viewports": 2, "observed": 22, "passed": 22, "failed": 0} | 0 / 0 | bounded-pass |
| [css-c2-c4-390-r3](css-c2-c4-390-r3/audit.json) | 5174a8dafd8c | {"observed": 2, "passed": 1, "failed": 1} | 1 / 1 | partial-pass-product-entry-defect |
| [css-c2-c4-r2](css-c2-c4-r2/audit.json) | 5174a8dafd8c | {"observed": 3, "passed": 2, "failed": 1} | 1 / 1 | failed-run-observer-limitation |
| [css-c2-c4-slots390-inspector](css-c2-c4-slots390-inspector/audit.json) | 5174a8dafd8c | {"observed": 1, "passed": 1, "failed": 0} | 0 / 0 | bounded-pass |
| [edge-transition-ce74](edge-transition-ce74/audit.json) | 5174a8dafd8c | {"observed": 8, "passed": 4, "failed": 4} | 1 / 1 | failed-ownership-token-assertion |
| [evidence-formal](evidence-formal/audit.json) | 5174a8dafd8c | {"observed": 110, "passed": 110, "failed": 0} | 0 / 0 | bounded-pass |
| [feedback-resize-observer](feedback-resize-observer/audit.json) | 5174a8dafd8c | {"expected": 38, "passed": 38, "failed": 0, "checkmarkLines": 38} | 0 / 0 | bounded-pass |
| [full-cdp-r3](full-cdp-r3/audit.json) | 5174a8dafd8c | {"passed": 2207, "failed": 0, "completed": true, "skippedGroups": 0, "sections": 84, "uncaughtBrowserExceptions": 1} | 0 / 0 | bounded-pass |
| [full-space-r2](full-space-r2/audit.json) | 5174a8dafd8c | {"observed": 228, "passed": 228, "failed": 0} | 0 / 0 | bounded-pass |
| [grid-raw-provenance](grid-raw-provenance/audit.json) | 5174a8dafd8c | {"observed": 207, "passed": 207, "failed": 0} | 0 / 0 | bounded-pass |
| [issue116](issue116/audit.json) | 5174a8dafd8c | {"checks": 87, "logPassLines": 87, "logFailLines": 0, "passed": 87, "failed": 0} | 0 / 0 | bounded-pass |
| [issue77-browser](issue77-browser/audit.json) | 5174a8dafd8c | {"checks": 37, "logPassLines": 37, "logFailLines": 0, "passed": 37, "failed": 0} | 0 / 0 | bounded-pass |
| [issue77-exit](issue77-exit/audit.json) | 5174a8dafd8c | {"checks": 61, "logPassLines": 61, "logFailLines": 0, "passed": 61, "failed": 0} | 0 / 0 | bounded-pass |
| [issue77-owner](issue77-owner/audit.json) | 5174a8dafd8c | {"tests": 5, "pass": 5, "fail": 0, "cancelled": 0, "skipped": 0, "todo": 0, "passed": 5, "failed": 0} | 0 / 0 | bounded-pass |
| [issue77-recovery](issue77-recovery/audit.json) | 5174a8dafd8c | {"checks": 111, "logPassLines": 111, "logFailLines": 0, "passed": 111, "failed": 0} | 0 / 0 | bounded-pass |
| [issue77-remove](issue77-remove/audit.json) | 5174a8dafd8c | {"checks": 46, "logPassLines": 46, "logFailLines": 0, "passed": 46, "failed": 0} | 0 / 0 | bounded-pass |
| [model-history](model-history/audit.json) | 5174a8dafd8c | {"observed": 35, "passed": 35, "failed": 0} | 0 / 0 | bounded-pass |
| [multiroom](multiroom/audit.json) | 5174a8dafd8c | {"observed": 34, "passed": 34, "failed": 0} | 0 / 0 | bounded-pass |
| [q38-save-roundtrip](q38-save-roundtrip/audit.json) | 5174a8dafd8c | {"observed": 18, "passed": 18, "failed": 0} | 0 / 0 | bounded-pass |
| [q38-service-restart](q38-service-restart/audit.json) | 5174a8dafd8c | {"observed": 13, "passed": 13, "failed": 0} | 0 / 0 | bounded-pass |
| [room-acceptance](room-acceptance/audit.json) | 5174a8dafd8c | {"observed": 253, "passed": 253, "failed": 0} | 0 / 0 | bounded-pass |
| [room-keyboard-r2](room-keyboard-r2/audit.json) | 5174a8dafd8c | {"observed": 396, "passed": 396, "failed": 0} | 0 / 0 | bounded-pass |
| [room-keyboard](room-keyboard/audit.json) | 5174a8dafd8c | {"observed": 373, "passed": 372, "failed": 1} | unknown / unknown | incomplete-service-disconnection-exit-unknown |
| [room-pan](room-pan/audit.json) | 5174a8dafd8c | {"observed": 32, "passed": 32, "failed": 0} | 0 / 0 | bounded-pass |
| [room-worker](room-worker/audit.json) | 5174a8dafd8c | {"observed": 78, "passed": 78, "failed": 0} | 0 / 0 | bounded-pass |
| [rule-case-races](rule-case-races/audit.json) | 5174a8dafd8c | {"observed": 30, "passed": 30, "failed": 0} | 0 / 0 | bounded-pass |
| [rule-cases](rule-cases/audit.json) | 5174a8dafd8c | {"observed": 76, "passed": 76, "failed": 0} | 0 / 0 | bounded-pass |
| [rule-reader](rule-reader/audit.json) | 5174a8dafd8c | {"passed": 34, "failed": 0} | 0 / 0 | bounded-pass |
| [save-reopen-synthetic](save-reopen-synthetic/audit.json) | 5174a8dafd8c | {"observed": 24, "passed": 24, "failed": 0} | 0 / 0 | bounded-pass |
| [save-roundtrip](save-roundtrip/audit.json) | 5174a8dafd8c | {"observed": 33, "passed": 33, "failed": 0} | 0 / 0 | bounded-pass |
| [scenario-lifecycle](scenario-lifecycle/audit.json) | 5174a8dafd8c | {"observed": 82, "passed": 82, "failed": 0} | 0 / 0 | bounded-pass |
| [scenario-workflow](scenario-workflow/audit.json) | 5174a8dafd8c | {"observed": 34, "passed": 34, "failed": 0} | 0 / 0 | bounded-pass |
| [section-profile-ui](section-profile-ui/audit.json) | 5174a8dafd8c | {"observed": 68, "passed": 68, "failed": 0} | 0 / 0 | bounded-pass |
| [shared-room-display](shared-room-display/audit.json) | 5174a8dafd8c | {"observed": 89, "passed": 89, "failed": 0} | 0 / 0 | bounded-pass |
| [timber-r2](timber-r2/audit.json) | 5174a8dafd8c | {"observed": 79, "passed": 79, "failed": 0} | 0 / 0 | bounded-pass |

## Native lifecycle

| Gate | Head | Observed result | Command / gate exit | Finding |
|---|---|---|---|---|
| [native-context-300](native-context-300/audit.json) | 5174a8dafd8c | {"observed": 9, "passed": 9, "failed": 0, "cycles": 300} | 0 / 0 | bounded-pass |

## Owner and component scopes

| Gate | Head | Observed result | Command / gate exit | Finding |
|---|---|---|---|---|
| [owner-r1-create-feedback-ui](owner-r1-create-feedback-ui/audit.json) | 5174a8dafd8c | {"passed": 138, "failed": 0, "completed": true} | 0 / 0 | component-scope-pass |
| [owner-r1-evidence-component-browser](owner-r1-evidence-component-browser/audit.json) | 5174a8dafd8c | {"passed": 67, "failed": 0} | 0 / 0 | component-scope-pass |
| [owner-r1-rule-case-standalone-browser](owner-r1-rule-case-standalone-browser/audit.json) | 5174a8dafd8c | {"passed": 91, "failed": 0, "viewportRecords": 2} | 0 / 0 | component-scope-pass |
| [owner-r1-rule-case-standalone-controller](owner-r1-rule-case-standalone-controller/audit.json) | 5174a8dafd8c | {"tests": 17, "pass": 17, "fail": 0, "cancelled": 0, "skipped": 0, "todo": 0, "passed": 17, "failed": 0} | 0 / 0 | component-scope-pass |
| [owner-r1-scenario-grid-owner](owner-r1-scenario-grid-owner/audit.json) | 5174a8dafd8c | {"tests": 1, "pass": 1, "fail": 0, "cancelled": 0, "skipped": 0, "todo": 0, "passed": 1, "failed": 0} | 0 / 0 | component-scope-pass |
| [owner-r1-scenario-module-browser](owner-r1-scenario-module-browser/audit.json) | 5174a8dafd8c | {"viewportRecords": 2, "namedPropertiesPerViewport": 8, "passedViewportRecords": 2, "failed": 0, "nativeCalls": 12, "forbiddenCalls": 0} | 0 / 0 | component-scope-pass |

Raw JSON, command logs, receipts and scripts are public copies. Screenshots/traces/archives are generally hash-indexed with originals local; browser profiles and compiled native binaries are excluded. No private queue, credentials or user drawings are included.

Named limitations:
- **async-original-r2**: Eight owner-delivered async assertions plus setup/health; does not settle the separate held-bhit finding.
- **compound-project**: Two viewport cases / 22 assertions: API-seeded nonempty model + unpublished rule draft + native assembly instance; true Save/New/full empty/fresh-profile Open and scene-only Export/New/Open. No UI authoring, cross-project merge, or service restart claim.
- **css-c2-c4-390-r3**: 390 beam passes; 390 slots does not reach the workspace because selection relocates #btnZoom under the second trusted down. Independently diagnosed product entry defect, not a slot-CSS verdict. No all-green run claim.
- **css-c2-c4-r2**: Original failed run retained: desktop beam/slots pass; 390 beam stopped at an observer incorrectly requiring both downs to remain on the card. Independent diagnosis is complete; mobile CSS is not certified by this run and 390 slots were not executed.
- **css-c2-c4-slots390-inspector**: Only the 390 empty-slot flow, using the already-supported inspector #inspEnter route: normal pointer plus Tab/Enter and full data preservation pass. Does not repair or retest the failed card-double-click route.
- **edge-transition-ce74**: Independent diagnosis: four success controls pass; four held transitions fail only the ownership-token assertion (B editToken 2→3). B handles/model/full World remain unchanged. Late continuation refresh is observed; effect on an active B drag/draft remains unverified. Original exit1 retained.
- **evidence-formal**: Formal evidence disclosure, source/field association, historical review, source retention and /12 true archive reopen; synthetic PDF only.
- **feedback-resize-observer**: G1 real trusted ResizeObserver notifications versus deliberately injected genuine errors and manual F8 feedback; own isolated service/profile, not the outer shared service.
- **full-cdp-r3**: Complete Linux CDP regression on clean 5174a8d: full mode, zero filters/modifiers/skips, 84 section floors matched. Exactly one intentionally injected P38 fb-auto-probe exception; not zero browser exceptions. Mixed trusted/DOM/native assertions do not replace independent race findings or Windows/physical-device acceptance.
- **full-space-r2**: Full space suite; excludes timber, dedicated async and synthetic save/reopen scopes. Assertions are not end-to-end scenario counts.
- **grid-raw-provenance**: Raw grid draft provenance failures, explicit reselection, detached preview and publish/Undo/Redo; API fixture and history setup are declared.
- **issue116**: Only this named gate scope; no whole-product release conclusion.
- **issue77-browser**: Only this named gate scope; no whole-product release conclusion.
- **issue77-exit**: Only this named gate scope; no whole-product release conclusion.
- **issue77-owner**: Only this named gate scope; no whole-product release conclusion.
- **issue77-recovery**: Only this named gate scope; no whole-product release conclusion.
- **issue77-remove**: Only this named gate scope; no whole-product release conclusion.
- **model-history**: Bounded 35-assertion history/lease suite; does not reconstruct missing historical 10/155 evidence.
- **multiroom**: Separately authorized #87 multiroom candidate flow, kept distinct from #54 single-room scope; includes labelled detached-input/late-callback injections.
- **native-context-300**: 300 distinct native context create/edit/retire cycles, summarized by nine named assertions. No browser flow or full interrupted Resume claim.
- **owner-r1-create-feedback-ui**: Focused formal Create/feedback overlap and draft/preview/history UI across default mouse/touch viewports. No whole #123 layout/attachment/physical phone completion claim.
- **owner-r1-evidence-component-browser**: Formal rendered page with an injected in-memory attachment backend. Its component checks do not replace the separate formal evidence/ZIP gate.
- **owner-r1-rule-case-standalone-browser**: Standalone rendered rule-case component on an owned temporary server. 91 fail-fast assertions accumulated across two viewports; no formal app adoption/ZIP claim.
- **owner-r1-rule-case-standalone-controller**: Standalone controller/HTTP/native scope on an owned temporary server, with injected host ports. No formal app owner or ZIP acceptance claim.
- **owner-r1-scenario-grid-owner**: Actual project-store owner validator + disposable native verifier. One Node test; no formal product UI/save claim.
- **owner-r1-scenario-module-browser**: Ephemeral module page with direct component calls and ZIP/file-input reopen. Two viewport records each assert eight named properties; these are not sixteen independent product scenarios. No app adoption/history/UI claim.
- **q38-save-roundtrip**: Eighteen Q38 archive/mesh/World/history assertions across true Save/New/fresh-profile Open; service is unchanged, so not a service restart claim.
- **q38-service-restart**: Exactly the original 13 Q38 restart recovery assertions, consuming the current same-head 18-check producer. Only owned port 18973 service and bridge restarted; no assembly draft/live placement-host/OS picker coverage.
- **room-acceptance**: Single-room authored fixtures, PDF/image calibration and save/reopen; not private missing attachment visual comparison.
- **room-keyboard-r2**: Only this named gate scope; no whole-product release conclusion.
- **room-keyboard**: Interrupted/incomplete original run: service connection failures precede fatal checkbox click timeout. Missing release receipt means command and gate exit unknown; 373 observed assertions do not mean suite completion.
- **room-pan**: Gesture and exact native/state preservation on synthetic single-room fixture.
- **room-worker**: Real Worker computation plus explicitly injected retained callback after genuine terminate; not an uninjected browser race claim.
- **rule-case-races**: Held GET/late allocation/detached retain and retired B safety; no claim of full interrupted Resume.
- **rule-cases**: Six bounded formal rule cases, retained historical receipts and /15 ZIP root/A/B restore; authors defined expectations remain independent of native output.
- **rule-reader**: Only this named gate scope; no whole-product release conclusion.
- **save-reopen-synthetic**: Synthetic grid fixture only; explicit partial space scope; no complete product certification.
- **save-roundtrip**: Actual download and fresh-profile chooser; injected cancel/write failure; not native OS picker. Nonempty reference images/PDF/drafts excluded.
- **scenario-lifecycle**: Existing safe checkpoint/retirement/discard/Finish lifecycle; does not claim complete interrupted Resume.
- **scenario-workflow**: Existing isolated A/B scenario/save/reopen flow; no undefined cross-project nonempty collision policy.
- **section-profile-ui**: Typed section profiles and native frames/material bounds, /16 Save/New/Undo/Redo/chooser reopen; real download fallback, not OS picker.
- **shared-room-display**: Separate per-room crop/opacity/lock with shared source basis; exact /14 root/A/B payload and negative schema/capability/capacity cases.
- **timber-r2**: Explicit partial timber/material/source-guard/font scope.
