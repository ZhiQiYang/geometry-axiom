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

The current inventory contains 591 executable files: 333 owned sources and 258
individually named exclusions. The five complete roots are `geometry-core`,
`geometry-app`, `geometry-templates`, `geometry-web`, and `geometry-guide`.
`current_geometry.c` is an additional standalone source. The real
`rule_cases.runtime` imports `tests.binaries`, so `tests/__init__.py` and
`tests/binaries.py` are also owned runtime sources despite their directory name.
New executable files anywhere under these roots fail until accounted for.

| Layer | Files | Actual responsibility |
|---|---:|---|
| K | 69 | Public neutral C stores/evaluators/source/transaction APIs and the Python geometry kernel, including their private implementation headers |
| W | 67 | Woodworking policy, material/recipe interpretation, construction, layout, support and presentation; rectangular-grid second-template witness |
| H | 191 | Native World/scene/command/transaction adapters and composition, Python application and compatibility facades, browser/server UI, guide authoring, and workspace tooling |
| vendor | 6 | Individually digest-locked browser PDF and ZIP dependencies, accessible only from H |

The 333 sources contain 190 C/header/include files, 75 Python files, 64 JavaScript
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
declared CRLF-to-LF normalization. There are 120 historical evidence programs,
47 other documentation/reproduction/snapshot/GEO-262 tooling programs, 66 dedicated test drivers,
and 25 engineering-spec prototype files. The prototype's `AGENTS.md` explicitly
states it is not the production application. The manifest has no directory
exemption. An owned dependency on any excluded file fails. Historical evidence
and prototype programs have not been certified as active product dependencies.

The six vendor files have raw-byte digests and an explicit H-only trust bundle.
Their internal code, runtime loaders, WebAssembly and non-source assets are
**trusted, not statically verified**. K/W access to that bundle is rejected.
Only exact existing Windows/process C headers, the optional H-only
`playwright.sync_api` screenshot driver and the H-only Windows file-time stat
import `ctypes` receive external-module allowances.

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

The preceding region-key ledger integration refresh first ran that manifest against
source HEAD `1ee2a890d7a734f381eac8c716910939818315db` and correctly failed with
`SOURCE_UNREGISTERED` for `geometry-core/kernel/region_key_sources.c`.
Independent inventory found exactly two new K files, its implementation and
public header, and no stale exclusion, vendor, driver or router digests. They
own neutral vertex-key ledger serialization and consume typed K region geometry
for coordinates in the same candidate. The refresh adds their individual
responsibilities without changing any previous classification, scanner guard,
test or product source. The final scan and 18-test run require this HEAD and
every source input hash to remain unchanged throughout verification.

The preceding linear-definition/version-source refresh first ran the previous
manifest through the actual CLI against source HEAD
`d371420ec1922adb3df382a6cc2799b39bef7370`. It exited 1 with
`SOURCE_UNREGISTERED` for `geometry-core/kernel/linear_definition_sources.c`.
Independent enumeration found exactly four new K files: the public headers and
implementations for `linear_definition_sources` and `version_sources`. No
exclusion, vendor, driver or router digest was stale. The linear-definition
provider serializes authored datum/guide definitions, preserving expression
mode, completeness, ordered signed terms and complete opaque source keys without
evaluating quantities. The version provider serializes immutable identity,
content, fingerprint, schema and typed fields; field quantities consume the
returned complete definition. Their individually reviewed K responsibilities do
not introduce a W/H dependency. This refresh changes only the manifest and its
derived scan, report and receipt, retaining every previous classification,
exclusion and scanner guard.

The preceding grid-codec and historical-evidence refresh froze source HEAD
`4a13551cc8aac3e116b53486fe44637c07374d49`. The previous manifest's actual CLI
run exited 1 with `SOURCE_UNREGISTERED` for the new sealed evidence pack's
`extract_evidence.py`. Independent enumeration found exactly two new W sources,
`grid_definition_codec.c` and `.h`, plus four historical Python publication
helpers. The codec owns woodworking grid authored/value wire formats for
systems, bindings, applications and rules; its W schemas and cache semantics
remain outside K. Each historical helper receives an individual exclusion,
purpose and LF-normalized hash, checked against its sealed package's raw-byte
digest. No directory exemption was added. The new closure also captures 29
changed previously sealed inputs; every existing exclusion, vendor and embedded
route digest remains current.

The same refresh inventories concrete W guards from the actual W-owned native
C/header/include files. It preserves all 751 prior forbidden identifiers and
10 prior forbidden strings, adding 162 `Wood*`/`WOOD_*`/`wood_*` executable
identifiers and 45 `wood`/`woodworking` namespaced string literals, for totals of
913 and 55. These include all eight public codec functions, its three schema/
capacity macros, `wood_grid_decode_system`, and
`woodworking.face-application-check/1`. Neutral `Geo*`/`GEO_*` and generic names
were not added. The receipt records the exact additions and their source-file
provenance. Separate static probes pass the actual K `geometry.c` text with one
added identifier or string at a time through the unchanged scanner: all 207 are
rejected with the expected guard, while a neutral identifier remains accepted.
These in-memory probes neither modify source/test files nor increase the
18-test product-suite count.

The preceding host-authority and train19-evidence refresh froze source HEAD
`47d3bb4bcccddeeb034dd5899a7aa15c9cab0768`. The previous manifest's actual CLI
run exits 1 with `EXCLUSION_DIGEST` for
`geometry-web/cdp_test.js`. Independent
enumeration finds exactly three new historical Python evidence drivers:
`geometry-web/docs/evidence/geo263-20261016/compile_probe.py`, that directory's
`verify.py`, and
`geometry-web/docs/evidence/geo263-p153-20261016/verify.py`. Each receives an
exact path, purpose and LF-normalized digest; the receipt also records its raw
digest and the matching blob at the frozen Git head. These scripts were read,
not executed. No directory or filename-pattern exclusion is introduced.

The updated H reference adapter composes placement definitions and returned
geometry, member facts, enclosure/obstacle facts and candidate version inventory
through the registered K/W providers. The model adapter obtains parameter
semantics and section-profile definitions through the same source graph. The
world-validation callbacks consume those composed facts while W retains its
policy role. These remain existing H sources; this audit does not prove all H
behavior or native acceptance. The W section-profile provider adds three
definition-copy accessors: `wood_sp_sources_profile_definition`,
`wood_sp_sources_member_definition` and `wood_sp_sources_run_definition`.
All 913 previous forbidden identifiers and 55 strings are preserved, and the
three accessors raise the identifier total to 916. A fresh lexical inventory of
all W-native sources finds no additional W-namespaced string guard. Three
separate in-memory K-source probes reject those identifiers, and a neutral
probe passes; they do not increase the 18-test suite count. No source is
reclassified and no scanner or product test changes in this audit.

This refresh captures 11 changed previously sealed executable inputs,
including the newly merged H/W accessors and train19 browser sources. Two
existing test-driver exclusions, `geometry-web/cdp_test.js` and
`geometry-web/grid_system_test.js`, require reviewed hash updates for train19's
double-click/hit checks and stagger-rename coverage. Their exact paths and
test-only responsibilities remain unchanged; the receipt records old/new LF
digests, raw digests and current Git blobs. All other exclusion, vendor and
embed-route digests remain current. The Python default
change in #289 was not part of that 47d3bb4 frozen source and was not certified by that historical audit.

The final GEO-261 integration refresh freezes source HEAD
`8394ef601c3d2407f51191339fad261929c1769a`. The merge of main `4b975a3d` (train
#312, GEO-262) and the GEO-262 re-anchor had already registered every new
executable file in the manifest, so independent enumeration finds 591 files,
none unregistered, none missing and no stale exclusion, vendor, driver or router
digest. Compared with the previous sealed manifest those commits added one H
source, `geometry-core/card_reference.inc`, 14 individually named exclusions
(nine GEO-262 tooling files under `geometry-core/card-reference/` and five
retained native-P1 evidence helpers) and updated five pinned digests:

- `geometry-web/assembly_generation_test.js` (exclusion LF digest)
- `geometry-web/cdp_test.js` (exclusion LF digest)
- `geometry-web/feedback_resize_observer_test.js` (exclusion LF digest)
- `geometry-web/marquee_test.js` (exclusion LF digest)
- `geometry-web/serve.py` (pinned scenario-route router digest)

The reviewed reason for each is recorded in the receipt. The router change
touches only `recorded_api` receipt handling; the scenario iframe route the
digest protects is not in that diff, and the iframe controls still pass against
the new digest.

Running that manifest through the actual CLI nevertheless exits 1 with one
`DEPENDENCY_UNRESOLVED`: `geometry-app/geometry_app/source_closure.py:40`
imports `ctypes` (and `ctypes.wintypes`) under `os.name == "nt"` for the
stat-signature source-inventory memo introduced by `c8de5a40`. The product suite
failed its complete-graph test for the same reason. This audit resolves it with
an exact **H-only** external-module allowance for `ctypes`, not the all-layer
standard-library list, because `ctypes` can load native libraries and K/W must
not gain that capability. In-memory probes append `import ctypes` to an actual K
and an actual W Python source and both are rejected; the actual H file is
accepted. This is a policy decision recorded for review, not a change to any
product source.

A fresh lexical inventory of all 60 W-owned native C files finds two W
identifiers added by the GEO-262 card reference, `wood_grid_card_definitions`
and `wood_grid_card_error`, and no new string guard. All 916 previous forbidden
identifiers and 55 strings are retained (9 identifiers and 3 strings no longer
occur in current W sources and are kept anyway), for totals of 918 and 55. Two
in-memory K-source probes reject the new identifiers and a neutral probe passes;
the HEAD manifest accepted the same text, so the new guards are what reject it.

69 previously sealed executable inputs changed (45 H, 6 K, 14 W and 4 excluded
test drivers), and 15 executable files are new. The Python default source commit
`8f36f1a0dd7e1244c92aca926c0a80079451e7f0` that the previous report left outside
its frozen source is now an ancestor of this HEAD (`git merge-base
--is-ancestor` exit 0); its runtime behavior and native coverage still require
their independent execution receipts, which this audit does not certify. No
scanner, product test or product source changes in this audit.

The previous four audit outputs are preserved byte-for-byte in the external run
directory and the previous sealed outputs were re-read from Git commit
`277bfdd3`. The new receipt links their raw/LF digests, the previous receipt
creation time and source head.

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

The removal check creates a separate tree containing **all 69 actual K files**
and no `geometry-app` or `geometry-templates` directory, then scans that complete
K tree. This is static missing-template evidence only. It neither compiles C nor
executes Python product modules, and must not be reported as native/runtime
no-template validation. Native execution remains in the serialized P1 queue.

At the latest sealed source HEAD `8394ef601c3d2407f51191339fad261929c1769a`, the
actual CLI scan exits 0 with 333 owned sources, 796 dependency edges and no
diagnostics. All 18 actual product tests pass with no skips. Independent
enumeration matches all 591 input hashes, both raw and LF-normalized. The
generic scanner suite was executed at this HEAD: 205 tests, 204 passed, 0 failed
and 1 skipped (a skip is not a pass). HEAD and all product, scanner and test raw
and LF hashes remain fixed throughout this finite refresh.

When new provider files are integrated, the root inventory must first fail
closed, then receive individually reviewed source entries. Re-run the product
scan and product tests and regenerate the receipt; rerun the generic scanner
suite if its scanner or test sources changed. Old fingerprints do not certify
new files or changed sources.
