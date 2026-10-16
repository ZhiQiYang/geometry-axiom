# GEO-261 actual-product dependency contract

`product-architecture.json` is the executable inventory for the current product.
Run it with the conservative scanner; a zero exit status requires every owned
source and every dependency to pass:

```powershell
python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json
python -B tests/test_architecture_contract.py
python -B tests/test_product_architecture.py
```

This replaces the earlier synthetic-fixture-only evidence for the dependency
gate. It does not replace algorithm ownership review, native no-template builds,
runtime import blocking, mutation receipts, browser acceptance, or SSOT checks.

## Complete inventory and responsibilities

The current inventory contains 563 executable files: 326 owned sources and 237
individually named exclusions. The five complete roots are `geometry-core`,
`geometry-app`, `geometry-templates`, `geometry-web`, and `geometry-guide`.
`current_geometry.c` is an additional standalone source. The real
`rule_cases.runtime` imports `tests.binaries`, so `tests/__init__.py` and
`tests/binaries.py` are also owned runtime sources despite their directory name.
New executable files anywhere under these roots fail until accounted for.

| Layer | Files | Actual responsibility |
|---|---:|---|
| K | 65 | Public neutral C stores/evaluators/source/transaction APIs and the Python geometry kernel, including their private implementation headers |
| W | 65 | Woodworking policy, material/recipe interpretation, construction, layout, support and presentation; rectangular-grid second-template witness |
| H | 190 | Native World/scene/command/transaction adapters and composition, Python application and compatibility facades, browser/server UI, guide authoring, and workspace tooling |
| vendor | 6 | Individually digest-locked browser PDF and ZIP dependencies, accessible only from H |

The 326 sources contain 183 C/header/include files, 75 Python files, 64 JavaScript
files, and 4 HTML files. The canonical self-contained axiom reader and its
generator are included. The separate work-manager is included as H tooling,
although its own instructions distinguish it from the Geometry product UI.

Legacy `geometry-core/*.inc` paths are **not** automatically labeled K. Their
manifest purposes record concrete host duties such as scene parsing, candidate
scheduling, serialization, source/provider composition, and compatibility names.
Conversely, the neutral native implementation is owned by K even when H includes
it in a unity build. This classification is a reviewed responsibility claim;
dependency scanning alone cannot prove that every remaining H function is free
of misplaced domain policy. It must not be cited as that stronger result.

All exclusions have an exact path, individual reason, and SHA-256 using explicitly
declared CRLF-to-LF normalization. There are 108 historical evidence programs,
38 other documentation/reproduction/snapshot programs, 66 dedicated test drivers,
and 25 engineering-spec prototype files. The prototype's `AGENTS.md` explicitly
states it is not the production application. The manifest has no directory
exemption. An owned dependency on any excluded file fails. Historical evidence
and prototype programs have not been certified as active product dependencies.

The six vendor files have raw-byte digests and an explicit H-only trust bundle.
Their internal code, runtime loaders, WebAssembly and non-source assets are
**trusted, not statically verified**. K/W access to that bundle is rejected.
Only exact existing Windows/process C headers and the optional H-only
`playwright.sync_api` screenshot driver receive external-module allowances.

## Audited host routes

The ordinary browser module routes explicitly map `templates/woodworking.js` to
the W frontend and `application.js` to H composition. The work-manager's root
`/app.js` resolves to its own static app. The two literal PDF module imports map
to the pinned PDF vendor source. These mappings create normal graph edges.

The existing scenario iframe is the single `scenarioEditorFrame` element in
`geometry-web/index.html`. `scenario-workspace.js` binds it with
`frame:$('scenarioEditorFrame')`, assigns
`owner.frame.src='/?scenario='+context` once, and resets to `about:blank` at two
sites. The fixed prefix keeps all suffix text in the same-origin root URL's
query/fragment portion. The actual host first applies `urlsplit(self.path)`,
uses `route.path` for routing, parses the scenario query, and serves the existing
index document for `/`. No alternate HTML document is created.

The exact embed declaration names the HTML element, driver, receiver, query
value, root-query prefix, target document and occurrence counts. Both the driver
and HTTP router have LF-normalized digests requiring review when changed. The
scanner checks the finite assignment spelling, normalizes explicit iframe URLs,
and adds HTML-to-driver/target and driver-to-target edges. Only H endpoints can
declare this route. Unregistered iframe elements, `srcdoc`, external or other
unmapped URLs, extra static query keys, and other embedded-document/plugin tags
remain rejected. This is a digest-locked audited H route, **not** a general
JavaScript alias/dataflow or server-routing proof; arbitrary host runtime effects
remain outside the static graph.

## Findings and executable controls

The first whole-product run reported 28 diagnostics. Exact module/routes and
ordered Python package search roots resolved manifest mistakes. Actual source
changes expanded the neutral document getter token-paste macro and made two
sets of include paths unambiguous. No existing token-paste, include-ambiguity,
dynamic-import, embedded-document, or layer guard was removed. The final scan
is stored in `product-architecture-scan.json`; its source/manifest/scanner
fingerprints belong in the accompanying receipt, not an implied future version.

The earlier enclosure/definition integration refresh ran its previous manifest against the merged
product and correctly failed with `SOURCE_UNREGISTERED` for the new H enclosure
adapter. Independent inventory found exactly five new files and no stale
exclusion, vendor, driver or router digests. The refresh adds the H enclosure
adapter, the K enclosure source header/implementation, and the W authored
definition source header/implementation. Each has an explicit responsibility;
new W identities and canonical schema strings are forbidden in K. No source was
reclassified to hide a dependency. Scanning these entries also exposed an
ambiguous W `document.h` include; the source owner changed it to
`../native/document.h` and merged that fix normally. The refreshed verification
used integration source HEAD `47160841738e38c24ef4ee05c291467c760d1e99`.

The latest region-key ledger integration refresh first ran that manifest against
source HEAD `1ee2a890d7a734f381eac8c716910939818315db` and correctly failed with
`SOURCE_UNREGISTERED` for `geometry-core/kernel/region_key_sources.c`.
Independent inventory found exactly two new K files, its implementation and
public header, and no stale exclusion, vendor, driver or router digests. They
own neutral vertex-key ledger serialization and consume typed K region geometry
for coordinates in the same candidate. The refresh adds their individual
responsibilities without changing any previous classification, scanner guard,
test or product source. The final scan and 18-test run require this HEAD and
every source input hash to remain unchanged throughout verification.

The manifest, scan, report and receipt are excluded from the product
input closure because they are derived audit artifacts. Manifest and scan are
hashed separately; the receipt never hashes itself. Audit-only commits therefore
do not create a self-referential fingerprint loop.

`test_product_architecture.py` contains 18 portable tests. Its shared setup first
validates the actual repository roots, so a new unlisted file cannot disappear
when the snapshot is built. A temporary input-tree control invokes that same
setup path with an unregistered executable and requires rejection before any
copy. It then copies the actual owned/excluded product files byte-for-byte and
runs the full graph once. Controls
then reparse modified real files while retaining edges only from unchanged
snapshot files. They require rejection for a concrete C identifier, direct and
transitive C template dependencies, a direct Python template import, a transitive
Python host import (including the package initializer), an unlisted source and a
changed exclusion. The iframe controls cover external/unmapped source URLs,
extra queries, `srcdoc`, unregistered element IDs, non-H routes, driver/router
digest changes, and an external assignment even after updating its digest.

The removal check creates a separate tree containing **all 65 actual K files**
and no `geometry-app` or `geometry-templates` directory, then scans that complete
K tree. This is static missing-template evidence only. It neither compiles C nor
executes Python product modules, and must not be reported as native/runtime
no-template validation. Native execution remains in the serialized P1 queue.

At the latest sealed source HEAD, the full scan passes with 326 owned sources,
776 dependency edges and no diagnostics; all 18 product tests pass with no
skips. Independent enumeration after the run matches every one of the 563
sealed source hashes. The generic scanner's previous 205-test result (204 pass,
one Windows symlink-permission skip) is reused only because both its scanner
and test source hashes remain unchanged; the receipt records that provenance.

When new provider files are integrated, the root inventory must first fail
closed, then receive individually reviewed source entries. Re-run the product
scan and product tests and regenerate the receipt; rerun the generic scanner
suite if its scanner or test sources changed. Old fingerprints do not certify
new files or changed sources.
