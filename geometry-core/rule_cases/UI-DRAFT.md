# #49 case preview and results — integration draft

This is a reviewable UI/adapter plan, not an implemented screen. It follows the
six accepted cases only. It adds no app/store/serve entry, saved schema,
capability, arbitrary program or geometry producer. Candidate placement is an
on-demand case panel inside the existing
[assembly workspace](../../geometry-web/assembly-workspace.js).

The standalone slice was independently reviewed and merged at main
`069ee772764f355201b580bfac3c0d7653258862`; its tree equals reviewed PR101
`10513586a214b66517ee8c433135b39e65aaba76` (`35f0fa5175fdb92e472f1ebb92acbee8af7410ab`).
Postmerge checks: 86 focused tests passed, exit 0 (3.348s). No new six-case run
was needed for this document: retained receipts from `46c9a9d` were rechecked
against the verified current runtime/scope and remain four passed plus two
blocked/diagnostic-unavailable. No private case executable was left running;
this worker started no persistent HTTP service. #49 remains open.

## Minimal native adapter handoff

Root's explicit unique native writer is thread
`01a1050d-60bf-7207-844c-08bf99a520b0`: deliver the precise #49 diagnostics
first, then subdivision. Formal transport/save and shared runner registration
remain the integration owner's work. No assembly/bridge change is made here.

Use the existing [README diagnostic expectations](README.md#interfaces-for-root-and-the-shared-integration-owner),
[catalog negative cases](catalog.py) and
[`_diagnostic_matches`](executor.py), rather than a second diagnostic vocabulary.
The two minimal expectations are `DIMENSION_TYPE / D33` with parameter 41,
field 9, and `RULE_VERSION_IMMUTABLE / D32` with rule 17, version 1. Final naming
is coordinated with root. `code`/`clause` are exact strings; the `ref` object
must match exact JSON keys/types. Additional slot/axis information can be a
separate diagnostic detail; adding keys to the expected `ref` breaks exact
matching. Human `message` text never supplies code, clause or a missing ref.

Source-checked [draft PR103](https://github.com/ZhiQiYang/geometry-axiom/pull/103)
at `610ded0498a1a227a16d76843375399f9830fa67`: its
`preview.violations[]` emits exactly those existing string code/clause and
integer parameter id/fieldId or rule id/version refs. No catalog rename or
diagnostic mapping is needed. Root reports the native owner's six cases passed
on that head; this worker checked the interface rather than repeating its run.
PR103 is under root review and is not the `main069ee` runtime used above.
After its review/merge and fresh runtime verification, the live six-case list
may show six passed while retaining four accepted and two exactly rejected
actual outcomes. Old blocked receipts remain unchanged and become stale when
the runtime fingerprint changes.

When that native head is available:

1. Verify/build its bridge through the existing registry, record its exact
   source/binary fingerprints, then run the two selected negative built-ins
   and the six-case set. Setup success, exact diagnostic, unchanged native
   read/revision/dump and all predicates are required together for pass.
2. Adapt live-native assertions in
   `RuleCaseCatalogNative.test_six_true_native_runs_keep_precise_negative_diagnostic_gaps_nonpass`
   (the four-pass/two-blocked count) and
   `test_native_negative_rejections_keep_world_and_revision_and_dump_unchanged`
   (the generic diagnostic assertion), plus
   `TrueNativeExecutor.test_blocked_negative_diagnostic_evidence_remains_blocked_when_staled`
   and `NativeRequestSeam.test_negative_capability_and_cancellation_keep_nonpass_results`
   to the newly supported exact negative result. Retain a separate old/generic
   blocked receipt check; never rewrite an old blocked record into passed.
3. In `test_generic_or_wrong_typed_diagnostics_cannot_promote_native_negative_to_green`,
   use an explicit generic diagnostic as the wrong control: its current first
   alternative is the live generic diagnostic, which will cease to be wrong
   after the native change. Keep `TypedDiagnosticControls` wrong code/clause,
   wrong typed ref, bool/float ID and missing-ref controls.
4. Recheck old receipts with the new runtime identity: even a known/capable
   replacement makes them stale. Coordinate any final token-name adjustment
   with the catalog's independent literal oracle, not with parsed native text.

The existing raw JSON seam is `run_case_request`; the integration owner supplies
host scope, verified binary and cancel event. No new endpoint is proposed here.

## Preview and list layout

Default desktop layout has a six-row list and a selected-case detail pane.
At 390px the list precedes the detail; selecting a row moves focus to its
heading, with a visible way back. Result states have text as well as color.

```text
規則案例                         [隔離執行所選案例]
4 通過 · 2 待精確核對             本次執行與正式場景分開

案例                         預期       原生實際       驗證狀態
同角色不同構件               接受       已接受         通過
只改一處接合                 接受       已接受         通過
尺寸引用拒絕計數型別         拒絕       已拒絕         待精確核對
合法規則可獨立發布           接受       已接受         通過
合法未完成配置               接受       已接受         通過
固定版本不可變               拒絕       已拒絕         待精確核對

所選案例：尺寸引用拒絕計數型別
案例輸入       parameter 41 / field 9：dimension → count
案例預期       特定型別診斷 + 精確來源；拒絕後資料不變
原生實際       已拒絕；ASSEMBLY_INVALID / I40/I41
驗證狀態       待精確核對：目前沒有可核對的 typed 來源
核對項目       拒絕後資料不變 ✓ · 引用仍相同 ✓
[查看案例來源] [查看診斷與核對明細] [歷史結果]
```

This is the rechecked `46c9a9d` example, not a fabricated future six-green
screen. The summary counts only current validated results; stale historical
passes are excluded. Source preview and observations remain separate panes.

| Case ID | Finite preview and native observation to verify |
| --- | --- |
| `same-role-distinct-members` | Role 7 has separate members 11/37. Joint 101 targets 11; joint 203 targets 37. Never group them into one member by role/name. |
| `one-local-joint-new-version` | Candidate version 2 changes joint 101 side `+u→-u`. Show the complete tuples for joint 203, version 1 and binding 29 as preserved checks. Candidate and fixed old version are distinct. |
| `wrong-type-dimension-reference` | Input changes parameter 41/field 9 from dimension to count; binding 29/slot 7/A keeps its exact typed reference. Parameter/material payloads are labeled case input; this slice does not claim comprehensive native read-back for them. |
| `legal-rule` | Independent published rule, with member/joint observations. Do not draw generated construction members or inferred lengths. |
| `legal-incomplete-binding` | Slot 13's absent dimensions/contact face/orientation show “未選定”; native `complete=false` is a legitimate accepted incomplete configuration. |
| `fixed-version-immutable` | Separate the attempted rename/reorder of rule 17@1 from the unchanged native rule/binding after rejection. |

Every source action opens the selected case's private data. It does not select
or navigate to a formal World object with the same ID/name. Use typed identity
to select members/joints and compare full tuples; list order is presentation
only. Labels/messages/JSON are text nodes, never executable markup. A relation
sketch is optional and describes authoring relationships, not construction
geometry or a native verdict.

## State and interaction rules

| Receipt/view state | Visible behavior |
| --- | --- |
| No receipt / `not-run` | “尚未執行”; actual and assertion evidence remain empty. |
| Running | Ephemeral “執行中” with a case-run cancel action. A previous result is labeled previous/history and does not cover the current state. Running is not a saved native result. |
| `passed` | “通過” only after authoritative current definition/source/runtime/scope freshness validation. Frontend does not compute pass from `accepted`/`rejected` or assertion counts. |
| `blocked` | Explain its exact reason; diagnostic-unavailable shows “待精確核對” even when actual=rejected and all existing predicates passed. |
| `failed` | “驗證失敗”; retain actual/expected and the failed check or native-contract failure. |
| `timeout` / `crashed` | “執行逾時” / “執行中止”, both nonpass. Do not label either as a proven geometry rejection. |
| `missing-capability` / `unknown-runtime` | “缺少執行能力” / “驗證版本未確認”; retain the definition and show no green result. |
| `stale` | “已過期” plus a plain-language reason and neutral “上次結果”. Preserve original scope/evidence/recordedStatus; do not count the old pass. |
| Malformed receipt | “結果資料無法核對”; preserve its original blob via the integration owner's policy. Do not render it as passed or silently discard it. |

Actual observations are optional. If the run stopped before their stage, show
“未取得原生觀察”; never fill that pane with the author input. Native text can be
shown as evidence, while only typed diagnostics drive a source action. Missing
typed ref means no source link is invented from human text.

Selection, opening a preview, and refreshing display are read-only. The case
cancel action only cancels that independent run; it must not reuse the existing
assembly workspace invalidation path that cancels a formal preview token.

Shared-owner adapters supply validated definitions/results as detached copies,
authoritative freshness, scoped execution/cancellation and token-gated result
attachment writes. These are seams, not route or persistence field definitions.
Capture the original project/history contextToken plus case identity, exact
definition hash and request generation before run. Accept a completion only
through the shared matching gate; a response after project switch, definition
edit, cancellation or a newer run cannot replace the currently shown result.
Retained history keeps its original scope, without relabeling it as a new run.

Formal native World/undo/history/pending token remain untouched throughout.
A valid completed result may change project attachment metadata/ContextHistory/
dirty only through the shared owner and the original context-token gate. No
such write occurs merely by selection/display. Receipt history count and
aggregate capacity remain the shared attachment owner's bounded contract;
this draft adds no unlimited log.

## Next-stage acceptance, not yet executed

| Check | Observable evidence required after integration |
| --- | --- |
| Six-case baseline | All six definitions are selectable; member/joint/input previews match exact typed fixtures. Native results populate distinct expected/actual/status columns. |
| Generic negative | Actual=rejected with generic/missing/wrong code/clause/ref remains nonpass; no message parsing creates a link or green verdict. |
| Typed negative | On the designated native owner's verified head, exact negative diagnostic plus unchanged World/pins/assertions can pass. Old blocked evidence remains historical. |
| Definition/source/runtime drift | Change one relevant exact domain, including known/capable native runtime: old pass becomes stale, evidence remains inspectable, current pass count decreases. |
| Scope and race | Project A run completes after switch to B, a new request, case edit or cancellation: B/current request is not overwritten; late/foreign write is rejected. |
| Cancel/isolation | Seed formal history and a pending preview token; opening/running/cancelling cases preserves them. Private processes/TEMP are reclaimed. |
| Failure states | Timeout/crash/output/concurrency/missing-capability/unknown-runtime display nonpass; absent observations stay absent. |
| Malformed retained data | List/null/string context and bad consumed fields produce the defined error view with the original blob preserved; no uncaught view exception or green card. |
| Read-only and metadata history | Selection/display makes no dirty/history step. Valid result attachment writes use the original token; no-op adds no history, rejected write leaves the current project intact. |
| Bounded/save/reopen | Shared strict bundle/receipt/count/aggregate gates reject unknown or oversized saved data before replacement; reopen restores definitions/results and authoritative freshness. |
| Text and private refs | HTML-like labels/messages render as text; same-numbered formal objects are never selected by a case source action. |
| Desktop/390px | Keyboard can select cases, reach details/cancel/history and return; text statuses and long typed refs wrap without losing their identity. Real iOS OS behavior remains separate manual acceptance. |

The native/definition/executor tests already cover their standalone portions;
these browser/save/late-response checks await the shared owner's actual adapters.
No UI acceptance pass, screenshot, save/reopen or live transport is claimed by
this draft. Source data and outcomes come from the finite native slice; the
screen is not a second validator.
