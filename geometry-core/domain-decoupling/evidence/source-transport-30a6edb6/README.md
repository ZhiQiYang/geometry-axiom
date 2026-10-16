# Same-candidate native source transport receipt

Source: `30a6edb6b463d281b724b37f271e88fb5747f412`.
All ten suites executed from a Git archive of this fixed commit.

```text
python tests/geometry_kernel_receipt.py --suite-set source-transport --source 30a6edb6b463d281b724b37f271e88fb5747f412 --out <TEMP>/geometry-tests/geo261-source-transport-30a6edb6
```

All 136 discovered tests passed with zero failures or skips: geometry 20,
graph 27, legacy geometry compatibility 1, isolation 2, product runtime 4,
candidate transactions 31, neutral program session 4, host world 8, native
host 22 and same-candidate source transport 17.

The source transport tests decode the frozen native schema through the real H
decoder, pass its typed descriptors to K and verify exact holed extrusion and
box Boolean results. They also cover opaque byte keys, provider fingerprints,
full source dependency closure, contexts, candidate and scene identity,
strict exact JSON, incomplete coverage and one-process transport pinning.
Three copied-production guard removals are required to make the corresponding
tests fail: coverage enforcement, canonical candidate hash enforcement and
source dependency insertion. Each negative run discovers exactly one test,
fails by assertion, and restores to green.

Process-boundary tests use mock adapters. No native compiler, actual adapter,
WSL or browser was executed. The new loader is opt-in; the product compile
path has not yet adopted native source references. Native coverage currently
reports incomplete and is explicitly rejected, without a legacy fallback.
Real native replay and final domain-decoupling acceptance remain open.
