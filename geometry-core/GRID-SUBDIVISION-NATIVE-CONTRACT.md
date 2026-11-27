# Source subdivision native slice — #58 / #59

Merged base: main `d1a161f6b1ed50d100d316a0b90be9d7d34451f6`, 2026-10-04; initial implementation started from `1075058`. Authorization: user accepted the eight explicitly written recommendations; item 7 contains six source subdivision behaviors. Only those behaviors are adopted. Q36 alternatives are design history, not blanket authorization. Formal geometry truth remains `公理層.md` D19a/I25a and related clauses; this file specifies transport and implementation boundaries.

Native owner: this delegated #58/59 worker. Owns `current_geometry.c`, source/binding/subgrid/reference/transaction native integration, native scene serialization, `web_bridge.c` and subdivision bridge transport. Internal parallel workers may contribute new helper modules under this owner. Integration owner `01a100b5-800b-75f2-9a02-71ee53e550ba` owns project-store, project schema/capability preflight and ContextHistory; native capability is `grid-subdivision-rules/1`. #44, #77, #49 modules/tests and #54 are outside this slice.

The original `grid-subdivision-rules/1` slice accepts only two nonstagger REPEAT axes, as mapped in merged PR100's implementation queue. Its scene capability boundary still refuses REPEAT_PANEL rules even when the full pitch divides exactly.

R14's approved extension (issue #57 comment 6688023475; axiom blob `c017aae31e925a166c91b2c5d2d13f9e96c38f5a`) adds native `grid-subdivision-rules/2`. Each source axis may independently be REPEAT or REPEAT_PANEL, and both must exist without D10b stagger. K validates the existing full pitch (step or panel+gap) against the divisions; W derives the original phase, cell and clipping before exact subdivision. Source ownership, stable keys, signed cells, formal references, source parameter/card identities, complete candidate validation and every existing budget remain unchanged. No second panel subdivision formula is introduced.

The original R14 native slice implemented source, query, transaction and `.scene` paths with `grid-subdivision-native/2` in `native_capabilities`, while complete host support remained /1. R14 H1 now connects the existing source-rule editor, complete-project reader and native service: `engineering-read`, validation and prepared-scene receipts advertise both `grid-subdivision-rules/1` and `/2` in `capabilities`. Actual PANEL-rule semantics remain `/2` in required capabilities and `.scene`, never disguised as /1. A service offering only the native profile still cannot admit a /2 project or enable its editor. Candidate-query transport remains separate; H1 displays the authoritative query after confirmation and retains the existing complete candidate change preview.

H1 keeps the existing `geometry-canvas/11` envelope (or a later envelope required by other project content), with capability versioning independent of the container format. The archive scanner tracks only source kinds and keyed-rule presence to require /2 through replay deletion/reset/source conversion; geometry and closure validation remain native. A saved scenario containing /2 also propagates /2 to its enclosing project. Manifest stripping, downgraded scene markers, an older service or mismatched canonical receipt must reject before confirmation, cancelling any prepared token without changing the active project, drafts or history. The model adapter still explicitly refuses both rule versions; unrelated existing models may coexist in the project.

## R14 下一片：確認前候選子線查詢（工作包 P）

本片承接 #57 設計 6436060391 §5.4，提供橋接器的只讀入口；尚未接到 App 預覽畫面，不構成 L4。原有 `grid-rule-query` 的輸出、錯誤、容量與正式場景語意保持不變。

```text
grid-rule-candidate-query reference|engineering TOKEN side before|after system|binding|grid ID rule K cell I J
grid-rule-candidate-query reference|engineering TOKEN side before|after system|binding|grid ID rule K rect U0 V0 U1 V1 mode exact|sample limit N
```

`reference` 只接受目前普通 `line preview` 的有效令牌；`engineering` 只接受 `engineering-preview` 的令牌。組構、斷面、完成面、角材、互頂、PF-6、骨架及匯入候選不代用這兩種令牌。未知種類或目前令牌的種類不符回 `CANDIDATE_KIND`；令牌不符、候選未就緒／無效／已取消／已確認、來源修訂或候選封印失效，以及群組編輯尚未結束，回 `CANDIDATE_STALE`。這些拒絕也不取消或消耗原候選。

成功回覆只有 `ok`、`candidate`、`source`、`metrics`、`query` 五個頂層欄位。`candidate` 是 `{kind,token,side,revision}`，token 為 uint32 JSON 整數，revision 為十進位字串。`source` 使用該側原生 `objects.gridSystems[]` 的完整 DTO，保留卡片、逐欄參數、規則、highwater、配置與套用。`metrics` 是 `{u:{pitch,divisions,innerStep},v:{pitch,divisions,innerStep}}`，由該側已求值的原生軸完整 pitch 與規則計算，並非另一份可編輯來源。`query` 是既有 cell／rect DTO，signed cell 仍傳十進位字串。

查詢借用已封印交易的 `before` 或 `after` World，使用同一 `grid_rule_query_cell/rect` 求值器；不重放 DSL、不建新交易、不改 live World、修訂、歷史、候選令牌或候選內容。兩側獨立查找：新增規則的 before、已刪規則的 after，或該側不存在的目標，回 `QUERY_NOT_FOUND`，不改查 live 或另一側。其他語法、selector、數值與容量錯誤沿用原查詢錯誤及已知 required counts；失敗回覆不夾帶成功幾何。零可見段的合法來源規則仍可查詢。

system／binding 的線 `ref` 仍為 null。候選 applied-grid 的 tuple 只作該候選內的差異識別；不因 tuple 在回覆內就成為正式 World 的可用引用。App 後續接線須保留候選 envelope 並禁止候選線建立正式依賴；確認後再查 live exact query 取得正式引用。此 transport 不增加幾何能力或保存格式，候選、令牌、指標與展開線不寫進場景。

## Frozen native interface

All CRUD goes through existing `line` / `preview` / `confirm TOKEN` / `cancel-preview` and the same candidate World, revision and history. No second solver, token or history.

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

Ordinary legacy `grid-system` redeclaration preserves rules and highwater, then validates the complete candidate. Canonical dump emits all keys and highwater with the minimum required capability: `grid-subdivision-rules/2` when an active rule's source has either REPEAT_PANEL axis, otherwise `grid-subdivision-rules/1`. Version /2 includes the /1 syntax and closure. A PANEL source without active rules, including a source retaining only highwater, does not require /2. Incomplete rule closure or unknown capability fails before replacing live World. Encountering new rule/highwater syntax requires the marker independently of final World usage, including a default-only `next 1` declaration or a source later removed during replay. Replay independently accumulates PANEL-rule semantics after each accepted line; later deletion, reset or source-kind conversion back to REPEAT cannot erase the /2 requirement. A default-only allocator has no extra semantic data to preserve in a canonical dump, but its input syntax cannot masquerade as a legacy scene. The integration owner must infer capability from `grid-source-rule`, `grid-source-rule-highwater`, `gridrule:` and `at-line rule` syntax and source semantics, so stripped or downgraded manifest markers cannot discard data. No project format number is assigned by native.

`objects.gridSystems[]` adds `rules` and `nextRuleKey`. Each rule has `ruleKey`, `name`, `selector:{kind:"all-cells"}` or `{kind:"cell",cell:[decimal-string,decimal-string]}`, and `divisions:[U,V]`. No expanded cells enter `World.grids`.

Cell query returns `systemId`, `ruleKey`, decimal-string `cell`, `bounds:[minU,minV,maxU,maxV]`, and `lines:[{axis,innerIndex,coordinate,segments,ref}]`. Each segment is `[[u,v],[u,v]]`. Only a real applied grid target has a placed `ref` with `kind:"grid-rule-line",appliedGridId,systemId,ruleKey,cellI,cellJ,axis,innerIndex`; system/binding queries return `ref:null`. Rectangular responses state completeness, required cell count and stride; capacity failures do not change World/history/pending preview. Native does all clipping and coordinates.

Engineering budgets are 32 rules per source, 1024 returned cells and 4096 emitted segments per query. Exact mode refuses excess rather than truncating. Sample mode returns whole cells at a stated row-major stride and validates only those returned cells; it never presents omitted cells as verified. When one indivisible selected cell itself exceeds the segment budget, sampling refuses `QUERY_CAPACITY` with the known required counts instead of increasing the stride until overflow. Stride growth stops at the first-cell-only selection and cannot loop indefinitely or thin inner lines. A query budget failure does not invalidate an otherwise legal source. Direct anchors may retain existing `through` or `between` placement clauses; the rule line remains a position reference and contributes no support.

The existing guide clipper is shared by rule queries and formal guides. Its temporary segment storage covers the outline and all eight allowed 32-vertex holes (conservative bound 288); a legal 41-segment line is returned in full. This storage belongs to temporary query/clip buffers, does not grow World/history, and does not raise the source query's 4096-segment budget.

Rule use protects divisions/selector/delete whenever any formal guide or timber references it. Guide expressions take coordinates only; direct anchors also enforce whole footprint inside parent cell and retain real support checks. Every source candidate validates every configuration, application, manual conflict and finite reference atomically. Existing manual subgrid behavior remains separate.

## Integration and verification boundaries

Project store must save the native dump and actual required capabilities; grid drafts remain one raw unsubmitted project attachment under the integration owner's approved #45 scope. It must not save preview tokens, formal rule reservations or a second geometric definition. One confirmation plus associated attachment update belongs to one ContextHistory transaction; undo restores the previous complete context. Scene alone is not a complete `.gcanvas` draft deliverable.

Initial independent vectors live in `tests/fixtures/grid_subdivision_vectors.json`; production oracle is `tests/test_grid_subdivision_oracle.py`. Native regression, ASan/UBSan, bounded query/stack checks, malformed fixtures, fresh strict regression and independent review are required before handoff. Cloud checks do not claim #61 full UI or physical iOS/Windows acceptance. Draft PR only; no merge/deploy.

R14 adds the independently authored literal vectors in `tests/fixtures/r14_repeat_panel_candidate.json` and `tests/test_r14_repeat_panel.py`. Its named native mutation protocol is baseline green, one specific product fault red without setup errors/skips/crashes, then restored green. The /1 oracle retains its PANEL refusal, geometry and atomicity assertions at an explicitly declared /1 scene boundary; /2 positive behavior is checked separately.
