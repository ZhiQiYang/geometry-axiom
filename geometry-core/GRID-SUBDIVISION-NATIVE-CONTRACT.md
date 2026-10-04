# Source subdivision native slice — #58 / #59

Merged base: main `d1a161f6b1ed50d100d316a0b90be9d7d34451f6`, 2026-10-04; initial implementation started from `1075058`. Authorization: user accepted the eight explicitly written recommendations; item 7 contains six source subdivision behaviors. Only those behaviors are adopted. Q36 alternatives are design history, not blanket authorization. Formal geometry truth remains `公理層.md` D19a/I25a and related clauses; this file specifies transport and implementation boundaries.

Native owner: this delegated #58/59 worker. Owns `current_geometry.c`, source/binding/subgrid/reference/transaction native integration, native scene serialization, `web_bridge.c` and subdivision bridge transport. Internal parallel workers may contribute new helper modules under this owner. Integration owner `01a100b5-800b-75f2-9a02-71ee53e550ba` owns project-store, project schema/capability preflight and ContextHistory; native capability is `grid-subdivision-rules/1`. #44, #77, #49 modules/tests and #54 are outside this slice.

The first source-rule slice accepts only two nonstagger REPEAT axes, as mapped in merged PR100's implementation queue. Either axis using REPEAT_PANEL refuses new or retained source rules, even when its pitch divides exactly. Existing REPEAT_PANEL source/binding/grid capabilities retain their original behavior; this restriction belongs only to the new source-rule feature. The earlier draft's broader acceptance is superseded, and Q36/proposal panel examples remain unadopted.

## Frozen native interface

All CRUD goes through existing `line` / `preview` / `confirm TOKEN` / `cancel` and the same candidate World, revision and history. No second solver, token or history.

```text
grid-source-rule SID create name-hex HEX selector all-cells divide U V
grid-source-rule SID create name-hex HEX selector cell I J divide U V
grid-source-rule SID key K name-hex HEX selector ... divide U V
grid-source-rule SID delete K
grid-source-rule-highwater SID next K|exhausted
grid-rule-query system|binding|grid ID rule K cell I J
grid-rule-query system|binding|grid ID rule K rect U0 V0 U1 V1 mode exact|sample limit N
guide ID PLACEMENT u|v gridrule:G:SID:K:I:J:u|v:INDEX
place T on P at-line rule G SID K I J u|v INDEX +u|+v|-u|-v +n|-n
```

`create` allocates the source-local next key only inside the candidate; only confirmation commits it. Keyed declarations edit existing rules interactively and restore rules during file replay. Highwater declarations are replay-only; they cannot reset live identity history. Nonzero uint32 rule keys; next=0 means exhausted. Delete never lowers highwater. Undo/redo restores the complete World including keys/highwater; abandoned branches have no permanent nonreuse guarantee. Delayed UI references must use existing context/revision/fingerprint gates. No draft reservations or persistent cross-project incarnation is added.

Ordinary legacy `grid-system` redeclaration preserves rules and highwater, then validates the complete candidate. Canonical dump emits all keys and highwater, with `requires grid-subdivision-rules/1`; incomplete rule closure or unknown capability fails before replacing live World. Encountering new rule/highwater syntax requires the marker independently of final World usage, including a default-only `next 1` declaration or a source later removed during replay. A default-only allocator has no extra semantic data to preserve in a canonical dump, but its input syntax cannot masquerade as a legacy scene. The integration owner must infer capability from `grid-source-rule`, `grid-source-rule-highwater`, `gridrule:` and `at-line rule` syntax, so stripped manifest markers cannot discard data. No project format number is assigned by native.

`objects.gridSystems[]` adds `rules` and `nextRuleKey`. Each rule has `ruleKey`, `name`, `selector:{kind:"all-cells"}` or `{kind:"cell",cell:[decimal-string,decimal-string]}`, and `divisions:[U,V]`. No expanded cells enter `World.grids`.

Cell query returns `systemId`, `ruleKey`, decimal-string `cell`, `bounds:[minU,minV,maxU,maxV]`, and `lines:[{axis,innerIndex,coordinate,segments,ref}]`. Each segment is `[[u,v],[u,v]]`. Only a real applied grid target has a placed `ref` with `kind:"grid-rule-line",appliedGridId,systemId,ruleKey,cellI,cellJ,axis,innerIndex`; system/binding queries return `ref:null`. Rectangular responses state completeness, required cell count and stride; capacity failures do not change World/history/pending preview. Native does all clipping and coordinates.

Engineering budgets are 32 rules per source, 1024 returned cells and 4096 emitted segments per query. Exact mode refuses excess rather than truncating. Sample mode returns whole cells at a stated row-major stride and validates only those returned cells; it never presents omitted cells as verified. When one indivisible selected cell itself exceeds the segment budget, sampling refuses `QUERY_CAPACITY` with the known required counts instead of increasing the stride until overflow. Stride growth stops at the first-cell-only selection and cannot loop indefinitely or thin inner lines. A query budget failure does not invalidate an otherwise legal source. Direct anchors may retain existing `through` or `between` placement clauses; the rule line remains a position reference and contributes no support.

The existing guide clipper is shared by rule queries and formal guides. Its temporary segment storage covers the outline and all eight allowed 32-vertex holes (conservative bound 288); a legal 41-segment line is returned in full. This storage belongs to temporary query/clip buffers, does not grow World/history, and does not raise the source query's 4096-segment budget.

Rule use protects divisions/selector/delete whenever any formal guide or timber references it. Guide expressions take coordinates only; direct anchors also enforce whole footprint inside parent cell and retain real support checks. Every source candidate validates every configuration, application, manual conflict and finite reference atomically. Existing manual subgrid behavior remains separate.

## Integration and verification boundaries

Project store must save the native dump and actual required capabilities; grid drafts remain one raw unsubmitted project attachment under the integration owner's approved #45 scope. It must not save preview tokens, formal rule reservations or a second geometric definition. One confirmation plus associated attachment update belongs to one ContextHistory transaction; undo restores the previous complete context. Scene alone is not a complete `.gcanvas` draft deliverable.

Initial independent vectors live in `tests/fixtures/grid_subdivision_vectors.json`; production oracle is `tests/test_grid_subdivision_oracle.py`. Native regression, ASan/UBSan, bounded query/stack checks, malformed fixtures, fresh strict regression and independent review are required before handoff. Cloud checks do not claim #61 full UI or physical iOS/Windows acceptance. Draft PR only; no merge/deploy.
