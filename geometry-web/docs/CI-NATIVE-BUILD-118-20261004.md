# Native CI unused prebuild removal (#118)

Base: `7414cfd2fe340408406b806c2e74eb011ef3383b`, savedcloud Linux,
2026-10-04. This slice removes one native-job setup command. It removes three
unused compilations; it does not establish a shorter full product journey.

## Before / after commands

```sh
# Before: native job
ulimit -s 16384
npm run build
python3 tests/run_all.py --build

# After: native job
ulimit -s 16384
python3 tests/run_all.py --build
```

The browser job still runs `npm run build` and exports `.build/web_bridge` and
`.build/model_base` to its own server. The native job has only checkout and the
native step: no later artifact/cache step or cross-job binary transfer.

## Product and executable dependency proof

`package.json:7` has no prebuild/postbuild hooks. Its only effects are
`mkdir -p .build` and these three commands:

```sh
gcc -std=c11 -O2 current_geometry.c -lm -o .build/core
gcc -std=c11 -O2 geometry-web/web_bridge.c -lm -o .build/web_bridge
gcc -std=c11 -O2 geometry-core/model_base.c -lm -o .build/model_base
```

The actual runner uses the different registry at `tests/binaries.py:46,107`:

| Unused native-job output | Actual registry output | Consumers |
|---|---|---|
| `.build/core` | `/tmp/geometry-tests/core` | core CLI, scene runner, polydraft |
| `.build/web_bridge` | `/tmp/geometry-tests/bridge` | declared Python/Node native suites, HTTP hooks, canvas direct shim |
| `.build/model_base` | `/tmp/geometry-tests/model-base` | declared model suites and Node native modeling |

`run_all.py:790` derives all selected `Suite.needs`; `:796` builds stale/missing
registry entries; `:803` inspects them. Full inventory has 66 suites and no
registry errors. The full Linux command also needs integrity and engjson, which
npm did not supply; GDI remains Windows-only. No registration or floor changes.

`run_all.py:278` clears inherited `GEOMETRY_*` and injects only fresh canonical
registry paths. `binaries.py:284` checks source/command fingerprint plus actual
binary SHA256/size/mtime; `:539` reuses fresh files, otherwise verifies compile
and launch identity before issuing the receipt. This freshness chain is retained.
The npm outputs have no registry receipt and are not candidates for reuse.

Special consumers were checked: canvas direct's hard-coded exe is redirected
with a required marker (`run_all.py:291,438,540`); polydraft uses the supplied
core (`polydraft_test.js:987`); real HTTP hooks explicitly select the registry
bridge (`test_modeling_transport.py:26`, `test_reference_workspace_races.js:423`).
Model-base fallback builds in its own TemporaryDirectory (`modeling/base.py:29`).
Room-collection and fault-injection tests compile private temporary native binaries;
those builds remain separate and untouched. Checkout's pinned post action only
cleans Git/auth configuration; it consumes none of these outputs.

## Timing provenance

Earlier e09 source measurement copied the three gcc commands above, preserving
flags/order/source and changing only `-o` into an isolated `compile-probe/`.
Each was executed once: core **6.554319 s**, bridge **10.004559 s**, model-base
**7.693913 s**, all exit 0; sum **24.252791 s**. Compiler was GCC 14.2.0.
Those C sources, package flags and registry/runner bytes are identical at this
base. This is a historical savedcloud compile measurement, not measured GitHub
Actions savings or an end-to-end before/after comparison. Other costs remain.

## Actual minimal validation

Preflight recorded `.build` absent and `/tmp/geometry-tests` absent. Without any
npm build, the unchanged formal CLI ran:

```sh
ulimit -s 16384
PYTHONDONTWRITEBYTECODE=1 python tests/run_all.py --build \
  --only py:test_bridge_integrity --only py:test_cli_args \
  --only py:test_modeling_runtime --only py:test_binaries
```

Exit 0, explicitly partial: bridge/core/model-base were built into the registry
and reported fresh. Existing counts: binaries 27/27, bridge integrity 24/24,
CLI args 6/6, modeling runtime 40/40; total **97 passed, 0 failed, 0 skipped**.
No `.build` directory was created. Raw cold-log SHA256 is recorded below.

```text
bridge     built          建好 /tmp/geometry-tests/bridge
core       built          建好 /tmp/geometry-tests/core
model-base built          建好 /tmp/geometry-tests/model-base
bridge     fresh    來源與 binary SHA-256 相符（建於 2026-10-04T13:03:19+00:00）
core       fresh    來源與 binary SHA-256 相符（建於 2026-10-04T13:03:27+00:00）
model-base fresh    來源與 binary SHA-256 相符（建於 2026-10-04T13:03:34+00:00）
py:test_binaries              27    27     0     0   0.3
py:test_bridge_integrity      24    24     0     0  14.4
py:test_cli_args               6     6     0     0   0.7
py:test_modeling_runtime      40    40     0     0   2.0
合計(已執行、有計數者)        97    97     0     0  17.4
==== 部分／示範執行，不可當完整驗收 ====
```

Complete cold-log SHA256:
`584b3210e8a6d2fd1ed73ad5b936668c305a464784f4cca7112b4166351a4545`.

```sh
PYTHONDONTWRITEBYTECODE=1 python tests/binaries.py build bridge core model-base
```

Exit 0: all three reused. Binary SHA256/mtime and receipt SHA256 stayed identical
before/after this reuse check. No compile or smoke was needed for fresh entries.
Complete reuse-log SHA256:
`5642360d4be5915dedea2118f3639c5fe8b065f9af7c48eae27bf8ee83c885c4`.
`run_all.py --list` exited 0; YAML parsed with PyYAML BaseLoader and its complete
before/after structure differs only by deleting native's `npm run build`.
All protected source hashes and browser-job settings remain identical.
Full native coverage remains the existing CI command; no full CDP rerun here.

## Output-directory handoff

No replacement `.build` mkdir is needed in native: registry process locks create
`OUT_DIR` (`binaries.py:147`), builds own obj/src/smoke directories, and suites
create runner logs (`run_all.py:413`). The absent-directory cold run verified it.

For a separate manual browser/P76 invocation, preflight its own screenshot
parents before running. On this Linux configuration use
`mkdir -p /tmp/geometry-tests`; also create parents of any explicit screenshot override.
P76 writes `parameter-mobile.png` and `parameter-desktop.png` there
(`parameter_workflow_test.js:71,108`). Normal CDP creates its default screenshot
parent (`cdp_test.js:459`), but a different override parent can leave the P76
parent absent. This handoff does not change or claim to fix the browser runner.
Native and browser jobs have separate filesystems; native npm's `.build` mkdir
could never prepare P76's directory in another job.
