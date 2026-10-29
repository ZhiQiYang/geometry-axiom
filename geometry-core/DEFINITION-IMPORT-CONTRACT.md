# Definition import contract (definition-import/1)

Refs D54, D55, I66, I67, R53. This operation copies enumerated definitions from another project into the current world. It is not an assembly transaction and not a scene or project capability.

## Identity classes

- (b) world-local ids — assembly rules, bindings, and parameter cards — are always assigned new ids. Rule versions of one source id share one new rule id and are renumbered from 1 in source-version order. Parameter cards use the same free-id walk as `parameter_import`, which may use 0.
- (a) content-global materials are shared only when id, version, and a recomputed content fingerprint all match. A different fingerprint rejects the whole import. The same bytes under another id stay two identities.
- (d) spec names collide by name. Each colliding closure spec needs an explicit `rename` or `map-existing` choice. A rename must pass the named-value grammar: ASCII hyphen is illegal, so a label such as `柱寬-匯入` cannot be stored. The axiom's grammar wins over any hyphenated example.
- (e) whole projects are not an import root.
- (f) existence-period marks are not allocated or copied here.
- Identities D54 does not enumerate, including assembly instances, panel materials, and engineering applications, do not enter the import.

## Protocol

`definition-import-read <server-owned scene file>` lists rules, bindings, parameters, specs, and materials. It does not change the live world.

`definition-import-preview <server-owned directory>` reads `request.json` and `source.scene`. The request keys are exactly `schema`, `expectedRevision`, `sourceSceneSha256`, `roots`, and `names`. The scene text is not embedded in that JSON. A valid preview stages one candidate and returns a token. Policy failures (`IMPORT_RENAME_REQUIRED`, `IMPORT_RENAME_UNNEEDED`, `IMPORT_RENAME_GRAMMAR`, `IMPORT_RENAME_COLLISION`, `IMPORT_FINGERPRINT`) return `ok: true` and `preview.valid: false` with no token. A second preview is refused while any preview token is still open.

`definition-import-confirm <token>` publishes that candidate as one undo step. `definition-import-cancel <token>` discards it. `line confirm` cannot apply this token.

The HTTP routes `/definition-import/read` and `/definition-import/preview` are the only REST entry. Confirm and cancel go through `/api`. The capability string is advertised by `engineering-read` and is rejected if a scene or project lists it as required.

## Relation to parameter-pack import

Parameter-pack import reassigns parameter-card ids inside one package. It does not classify D54, preview colliding specs, or rewrite rule and binding references. Definition import uses that same card allocator for cards, and additionally reassigns rule and binding ids, shares materials only on an equal fingerprint, and requires an explicit name choice before confirm.
