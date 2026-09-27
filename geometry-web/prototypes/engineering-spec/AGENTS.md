# Prototype Instructions

## User-selected direction — 2026-09-27

The user selected option 2, 畫布內套用. The selected visual truth is `design/reference-selected.png` (1487 × 1058 pixels). Preserve the broad drafting canvas, left layer list, right engineering specification inspector, indigo actions, teal boundary, and source/override distinction. Mobile uses a scrollable settings panel, a separate canvas view, and persistent bottom actions.

This is a UI prototype with a local, editable material and engineering-method catalog, not the production geometry-web application or an axiom reader. Do not edit SSOT or connect production mutations as part of prototype work. GeometryCanvas is a functional numerical visualization, while material images are generated raster assets and icons are Phosphor icons. Explain geometric differences from the illustrative mock; never fake invalid geometry to match image positions.

## Durable user decisions — 2026-09-27

- The user's working panel default is calcium silicate board **915 × 1830 × 6 mm**, in width × length × thickness order. Offer **910 × 1820 mm** as a common alternative and **9 mm** as another thickness choice. All dimensions remain editable; these are defaults, not a fixed whitelist.
- The user reports that 6 mm accounts for almost all ceiling work and most wall work, with occasional 9 mm wall boards; about 15% of their projects use 910 × 1820 mm. These percentages describe the user's practice. Do not present them as independently verified Taiwan market statistics or derive unsupported structural rules from them.
- Do not invent a timber section, brand, or model. The boundary, primary, and secondary roles select their own explicit timber material versions. A missing role material must remain visibly unset.
- Material information must be editable from the workflow. A source dialog with only a close/return action is insufficient. Editing a published material or method creates a new version; it does not silently change existing references.
- Changes follow **material source → material version → engineering-method version → target faces → preview → apply**. Keep old references usable, show effective dimensions, and require a new preview when inputs change.
- Preserve local catalog and face settings across reloads. Provide prototype JSON export/import, validate before replacing state, retain valid data when storage fails, and detect another tab's saved changes before writing over them.
- Preserve unfinished library workflows (including nested material/method forms) in the current tab across dialog dismissal and reload. Clearly distinguish retained drafts from published versions; only explicit discard clears an unfinished draft. On direct current-panel edits, continue into an unsaved next version of the entry method with the new material reference; never auto-apply it to a face.
- Preview prioritizes changed values and version references, with unchanged specifications collapsed and first application explicit. The mobile canvas retains panning controls and supports keyboard viewport movement.
- Panel thickness is specification information and may be a positive decimal. It does not participate in this prototype's 2D grid coordinates. Width, length, timber A/B, and gap obey the existing integer-mm geometric input rules.

Verified manufacturer/brand catalog shortcuts are optional form-fill helpers, separate from the user's common choices. The checked sources are [南亞](https://www.nanya-decoration.com/calcium-silicate-boards.html) and [日建 NIKKEN](https://www.tck.tw/product/19), checked on 2026-09-27. Preserve the selected source URL and actual catalog dimensions. Do not attribute the user's 910 × 1820 mm choice to either source without separate evidence. A catalog entry does not confirm current inventory or approve a construction assembly.

The selected reference image remains the layout reference. The user corrections above supersede its old material dimensions and read-only specification flow. The local catalog design and prototype acceptance cases are in `CATALOG-DESIGN.md`; final test evidence belongs in `design-qa.md`.

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

Build app UI in `src/`. Keep `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, and `tests/sites-worker.test.mjs` intact so the same local prototype can be handed to Sites. Before a Sites handoff, run `npm run build` and `npm run test:sites`; the build must leave `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json`.
