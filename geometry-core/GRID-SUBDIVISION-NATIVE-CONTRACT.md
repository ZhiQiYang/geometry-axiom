# Source subdivision native slice — #58 / #59

Base: main `1075058`, 2026-10-04. Authorization: user accepted the eight explicitly written recommendations; item 7 contains six source subdivision behaviors. Only those behaviors are adopted. Q36 alternatives are design history, not blanket authorization. Formal geometry truth remains `公理層.md` D19a/I25a and related clauses; this file specifies transport and implementation boundaries.

Native owner: this delegated #58/59 worker. Owns `current_geometry.c`, source/binding/subgrid/reference/transaction native integration, native scene serialization, `web_bridge.c` and subdivision bridge transport. Internal parallel workers may contribute new helper modules under this owner. Integration owner `01a100b5-800b-75f2-9a02-71ee53e550ba` owns project-store, project schema/capability preflight and ContextHistory; native capability is `grid-subdivision-rules/1`. #44, #77, #49 modules/tests and #54 are outside this slice.

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
guide ID on PLACEMENT along u|v at gridrule:G:SID:K:I:J:u|v:INDEX
place T on P at-line rule G SID K I J u|v INDEX +u|+v|-u|-v +n|-n
```

`create` allocates the source-local next key only inside the candidate; only confirmation commits it. Keyed declarations edit existing rules interactively and restore rules during file replay. Highwater declarations are replay-only; they cannot reset live identity history. Nonzero uint32 rule keys; next=0 means exhausted. Delete never lowers highwater. Undo/redo restores the complete World including keys/highwater; abandoned branches have no permanent nonreuse guarantee. Delayed UI references must use existing context/revision/fingerprint gates. No draft reservations or persistent cross-project incarnation is added.

Ordinary legacy `grid-system` redeclaration preserves rules and highwater, then validates the complete candidate. Canonical dump emits all keys and highwater, with `requires grid-subdivision-rules/1`; incomplete rule closure or unknown capability fails before replacing live World. The integration owner must infer capability from `grid-source-rule`, `grid-source-rule-highwater`, `gridrule:` and `at-line rule` syntax, so stripped manifest markers cannot discard data. No project format number is assigned by native.

`objects.gridSystems[]` adds `rules` and `nextRuleKey`. Each rule has `ruleKey`, `name`, `selector:{kind:"all-cells"}` or `{kind:"cell",cell:[decimal-string,decimal-string]}`, and `divisions:[U,V]`. No expanded cells enter `World.grids`.

Cell query returns `systemId`, `ruleKey`, decimal-string `cell`, `bounds:[minU,minV,maxU,maxV]`, and `lines:[{axis,innerIndex,coordinate,segments,ref}]`. Each segment is `[[u,v],[u,v]]`. Only a real applied grid target has a placed `ref` with `kind:"grid-rule-line",appliedGridId,systemId,ruleKey,cellI,cellJ,axis,innerIndex`; system/binding queries return `ref:null`. Rectangular responses state completeness, required cell count and stride; capacity failures do not change World/history/pending preview. Native does all clipping and coordinates.

Rule use protects divisions/selector/delete whenever any formal guide or timber references it. Guide expressions take coordinates only; direct anchors also enforce whole footprint inside parent cell and retain real support checks. Every source candidate validates every configuration, application, manual conflict and finite reference atomically. Existing manual subgrid behavior remains separate.

## Integration and verification boundaries

Project store must save the native dump and actual required capabilities; grid drafts remain one raw unsubmitted project attachment under the integration owner's approved #45 scope. It must not save preview tokens, formal rule reservations or a second geometric definition. One confirmation plus associated attachment update belongs to one ContextHistory transaction; undo restores the previous complete context. Scene alone is not a complete `.gcanvas` draft deliverable.

Initial independent vectors live in `tests/fixtures/grid_subdivision_vectors.json`; production oracle is `tests/test_grid_subdivision_oracle.py`. Native regression, ASan/UBSan, bounded query/stack checks, malformed fixtures, fresh strict regression and independent review are required before handoff. Cloud checks do not claim #61 full UI or physical iOS/Windows acceptance. Draft PR only; no merge/deploy.
