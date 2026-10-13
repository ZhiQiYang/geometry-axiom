# #123 available-source audit at clean 640a81443b3d070dba3d8a0aa52adb2d64cebe0b

This is a read-only source audit, not browser acceptance or a private ZIP comparison. The source was clean when inspected. Authority is the portable original issue body (`issue123-original.json`), the existing handoff README/C-review, and current native/DOM contracts. The historical A-43-map supplies IDs and self-authored summaries, not the exact private attachment instructions. Its historical 0-fixed/30-unknown counts remain historical.

The complete available-source pass found these concrete remaining adopted corrections, together rather than serially:

1. **G3**: `geometry-web/grid-inspector.js:48` still places `#gridObjectDelete` next to `#gridObjectOpen/#gridObjectNewBinding`. S2 explicitly adopts delete isolation; C-review says the existing native `confirmReferenceImpact` is already the confirmation. Move the existing node into closed footer `.gi-delete-section`, preserve exact onclick/current/busy/native semantics. The normal caller at `grid_rule_editor_test.js:151` must open the summary once before its original click/assertions. Scratch `compact-delete-640/compact-delete.patch` implements only this source/style/formal-navigation/DOM change; apply-check passed against clean640. This is not a second confirm.
2. **D3**: `geometry-web/index.html:243,245,263` says `檢視/挖孔`, while the same selection/opening tool concepts in the face toolbar say `選取/開口` (`:379,:388`). S4 explicitly adopts shared tool terminology. Rename visible labels/title/accessibility text using the existing source words, preserving `data-v3-tool=view/hole`, native select values, IDs and handlers. Do not equate the different rect/redraw operations. Any old tests which assert only old wording require contract reconciliation, not removal of behavior assertions.
3. **B7**: `index.html:384` includes `[data-shape-action="hole"]` under the shape operations, while `:388` already has `[data-face-tool="hole"]` and R. `app.js:10305` confirms the shape entry does only `feSetTool("hole")`, exactly the same action as the standalone/R entry. S3 explicitly adopts tool deduplication while preserving R/current contracts. The minimal merge is to remove this duplicate shape-menu choice while retaining the standalone hole button, `feSetTool("hole")`, shortcut R and all native hole semantics. Other shape operations remain. This is the only confirmed identical-command duplicate; guide/timber/grid placement versus forms are distinct actions.
4. **X5/E6 clear icon portion only**: S1 adopts shared icons. `grid-system-workspace.js:311` renders grid zoom `−/＋` and return `←` as text; other workspaces use the already shared `icon('minus')/icon('plus')/icon('arrowLeft')` (`app.js:197–239`). Reuse those existing icons without changing IDs, aria labels, handlers or spacing/pixel readout. The grid `1格600×400mm · Npx` readout is an existing tested native/display identity and must stay, not be replaced by a percent. No private pixel policy is inferred from this icon merge.
5. **Compact keyboard continuity**, a consistency bug within already adopted S2's accessible common nine-point/vertex controls: `grid-inspector.js:127,141` calls `replaceChildren()` after real Enter/Space and loses current focused SVG node. Preserve focused `data-gi-vertex` / `data-gi-anchor` identity and focus the replacement matching node with preventScroll, as root already does for full `drawBoundary`. Keep keyboard/pointer/native semantics unchanged; verify real Tab→Enter/Space→next Tab in both sizes.

All 43 IDs were examined against available authority and current source:

| IDs | Available adopted slice and actual source | Current status / limit |
|---|---|---|
| X1 | Common accent/ink/muted/border tokens in app.css; four-primary consistency in formal six | Implemented clear four-primary slice; exact every private label/palette pixel unknown |
| X2 | Shared WorkspaceShell/header/project bar, left return and right actions | Implemented, formal six640 actual receipt reported198/0, independent receipt pending when audit prepared |
| X3 | Common control rules and 44px mobile workspace/header controls | Implemented clear portable rules; issue explicitly records 32/36/44 vs40 ambiguity, not every private size proven |
| X4 | Face component switch, current shared tab/segment styling, one active form | Implemented common visible control slice; replacing every internal implementation is not required by source contract |
| X5 | Existing shared SVG icon library, grid text icon exceptions | Clear remaining icon merge above; no wholesale icon redesign |
| X6 | Zoom controls within all actual viewports, mobile full workspace targets | Implemented reachable controls; preserve meaningful grid spacing/pixel readout |
| X7 | Shared column/beam/grid type variables; actual beam renderers use common token | Implemented source slice |
| B1 | Desktop single 56px workspace header and original viewport requirement | Implemented; original formal six responsive geometry source oracle retained |
| B2 | Pure left face layers, BOM and projection form moved to right | Implemented; projection rows preserve real nodes and handlers |
| B3 | Five persistent layer groups and real empty-group entry buttons | Preserve existing contract: cdp_test.js:3753 requires five groups and >=3 .fl-empty; :3771 actually clicks an empty entry. Portable S3 does not adopt hide-all-empty groups. No new policy |
| B4 | [data-component-tab] guide/timber/grid shows one form; BOM under timber | Implemented; supplemental BOM normal confirmation precondition still under verification |
| B5 | Global desktop >=28px and mobile44 workspace rules | Implemented clear token slice; private unspecified controls need original visuals, not invented blanket dimensions |
| B6 | Existing GEO216 first-visit dismissible hint and state-specific summary | Implemented relevant-state behavior; C-review explicitly rejects conflating unrelated main/face selection state |
| B7 | Duplicate same feSetTool('hole') menu vs R toolbar | Clear remaining merge above; retain R and all existing distinct operation contracts |
| B8 | Existing decorative origin strokes; no permanent origin caption | Source is already uncluttered. A-map summary supplies no adopted exact decorative-contrast target; no invented geometry/style policy |
| C1 | spacePlanReadout, independently derived world dimensions, stable screen-font labels/grid | Implemented clear source slice; normal supplemental plan actual result requires its own receipt |
| C2 | Shared --type-beam across cards and plan | Already implemented, do not rework |
| C3 | Column/beam placement + actual size fields in single spacePlanToolbar | Implemented source slice |
| C4 | Permanent slot action, differentiated slot-name/axis/action | Already implemented, do not rework |
| C5 | spaceAddMembers and spEditMembers both call same openMemberDialog; RC hover has focus-within and hover:none visibility | A-map reports duplicate; portable S4 does not adopt exact removal of these member-edit locations or always-visible mouse RC policy. Report source fact/decision, not unambiguously missing adopted fix |
| C6 | Free RC list is all unowned project members | Nearby filtering requires new spatial policy; not adopted portable scope |
| C7 | Inspector shows title ID/closed tag and explicit ID/status rows | A-map reports repetition; portable S4 gives no adopted exact row-removal. Source fact/decision, not private attachment reproduction |
| D1 | Hidden compatible workSurf; v3ToolbarSurf in rect-only v3PlaneControls | Implemented while preserving original ID/native values |
| D2 | v3 right pane constant240px + empty state | Implemented; no selection-induced width jump |
| D3 | Visible view/hole vocabulary differs | Clear remaining terminology above |
| D4 | Entire actual labels clickable with mobile44 | Implemented, exact unchanged native view/layer checks in original formal six |
| E1 | Exact original igBoundarySection/diagram moved into right step2, no duplicated node | Implemented; normal S2 extra scope verifies pointer/keyboard/dropdown identity |
| E2 | Main action right, original discard left; actual same-workspace confirmation | Implemented, pending/busy/owner guard source unchanged |
| E3 | Primary source-save accent, native scene-vs-full-project save hints | Implemented source slice |
| E4 | Shared left return/header styling | Implemented clear position slice; icon merge above |
| E5 | Shared GridAnchorPositions exact nine names/fractions and custom1/3 preservation | Implemented; compact keyboard-continuity fix above still required |
| E6 | Reachable zoom with meaningful native grid scale | Clear shared-icon part remains; percentage replacement is explicitly excluded |
| G1 | Actual labels using current readable compact stylesheet | Exact private contrast target unknown; issue four-primary contract does not claim all labels identical |
| G2 | Compact vs full have distinct density, common primary accent/focus/native editing | Portable issue records height ambiguity; cannot declare unspecified compact40 wrong by inventing44 for every context |
| G3 | Compact delete still adjacent to navigation | Confirmed adopted remaining; minimal patch ready |
| G4 | Actual source vs binding terminology retained, shared nine-point names | Implemented clear source/context distinction; do not rename native source and binding into one concept |
| F1 | Welcome contained in stage, genuine preview controls gated | Implemented source slice and formal six normal preview |
| F2 | Shared header, right three-step form, viewport-based stage and short-height900 | Implemented; preserve original #119 integrity/results |
| F3 | One main welcome example, other original examples in disclosure | Implemented without deleting original examples |
| F4 | One three-step number sequence; section duplicate numbers removed | Implemented |
| F5 | Shared accents/focus/control styles | Implemented clear primary slice; no private pixel-perfect claim |
| F6 | Existing guide/help/direction text final computed source override12px | Implemented, historic11px evidence retained |
| F7 | Actual smClose relocated left | Implemented |

The report has not compared the private ZIP or declared all43 browser-accepted. The precise remaining available adopted product changes are the five corrections listed at top. C5/C7/B3/B8/G1/G2 exact private presentation or new policy cannot be invented; the available source facts above allow root to classify each explicitly, without blocking other adopted work.
