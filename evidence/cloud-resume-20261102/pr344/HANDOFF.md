# PR #344 main convergence handoff

Publication candidate **E**: `503cfc59354893859ae9e6e4a6ab7c11d7972517`.

Actual Node/architecture/mutation-check execution source **S** remains
`eccebabc85acf74e30274b8ea8e24db863d8843b`; those executions are not relabelled E.

Local branch: `codex/issue320-main-convergence-20261102` at
`/tmp/geometry-pr344-20261102`. The worktree/index are clean. No push, PR base/body
edit, comment, approve, merge to main, rebase, or force push was performed.

## Ordinary merges and exact scope

1. Main convergence `a9731b7cd80db440d2c5e297ce1c8d8fd78ba453`, parents original
   #344 `df39d1933402c76b2f8b35ca013412daf16ed4c9` and accepted main
   `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d`.
2. Tool dependency convergence S, parents `a9731b7c` and #366 tool head
   `502a64ff6214dd6060927b7f14643a533536f20d`. The four tool files retain exact
   original mode/type/blob entries. #366 is still an unmerged dependency; the
   intended PR merge target remains main.
3. Artifact-only adoption E, parent S. Four canonical paths exactly equal the
   peer-reviewed external artifact bytes. Manifest and scan were already equal,
   so only the report and receipt actually changed. Product/test bytes remain S.

Relative to that main, exactly six original implementation/test paths differ:

- `geometry-web/app.js`: clear `connection.error` only after complete successful recovery;
- `geometry-web/cdp_test.js`: original P53/P61 recovery observations and three named assertions;
- `geometry-core/domain-decoupling/product-architecture.json`: only the original CDP exclusion LF digest;
- `tests/test_connection_recovery.js`: original nine tests, with explicitly declared DOM/transport substitutes;
- `tests/run_all.py`: original Node9 mapping added to the current-main registry;
- `tests/run_all.expected.json`: original `node:connection_recovery` count9 entry;
  every pre-existing expected entry remains exactly main's value.

The four #366 files, two newly adopted derived reports, and574 historical
evidence paths are additional to those six paths. Every historical evidence mode/type/blob entry remains the original
#344 entry. Current-main golden bytes and the integration workflow's 35-minute
limit remain unchanged. All 195 bridge build inputs equal main by Git entry;
this phase did not compile or use default/shared native cache.

Only two merge conflicts occurred, both derived historical architecture files:
`PRODUCT-ARCHITECTURE.md` and `product-architecture-receipt.json`. All three
original Git stages were saved in `merge-conflicts/`; resolution retained the
exact current-main historical entries at S. E then adopted the newly generated
local receipts; their execution remains S, not E. The historical a6 entries
remain preserved in Git and are not presented as S's execution receipts.
No executable app/CDP/registry/golden file was replaced wholesale with an old
branch version. `SOURCE_IDENTITY.json`, `SOURCE_DELTA.patch`, and raw compressed
Git subcommand streams establish the exact scope.

## New execution evidence at S

| Gate | Original command/result |
|---|---|
| Node fixed/withdrawn/restored | `node --test --test-reporter=spec tests/test_connection_recovery.js`; exits **0/1/0**, pass **9/6/9**, fail **0/3/0**, skip0 throughout; original300-second registry limit |
| Architecture scanner | `python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`; exit0, 798edges/0diagnostics |
| Generic architecture tests | `python -B tests/test_architecture_contract.py`; exit0, 205tests, zero skip |
| Product architecture tests | `python -B tests/test_product_architecture.py`; exit0, 18tests, zero skip |
| Saved mutation freshness | `python -B tests/mutate.py --check`; exit1, 123definitions/123records; 62killed/1crashed/4equivalent/53stale/3retired, zero survived/invalid/blocked |

Node withdrawal runs an isolated copy containing the exact original test bytes
and full S app bytes with only the successful-ready error-clear operation
removed. The three expected named failures are `successful recovery kept stale
error`, `completed retry kept stale error`, and `loading echoed stale error`.
Restored app bytes equal S. Actual source and index never changed. These are
Node/VM controls with the original declared substitutes; they do not prove true
browser P53/P61 behavior.

The architecture manifest retains all main policies, including 937 forbidden
identifiers and55 forbidden strings. Only the CDP exclusion digest differs from
main, and its actual LF hash is
`1f3e2e36283ed7bbf6c4ad2cf3dc12c685667356d186d9fbd47bc5f0520f07ee`.
All604 inputs are identical before and after the three original commands by
raw/LF hash, size, mode, mtime and Git entry. LF closure:
`d7da9f09b7c6acc910ce7760a825bcf8594e57bc708d69e5e2c3144eadf3c991`.

`architecture/` contains four newly assembled **external** artifacts using the
existing `geometry-product-architecture-receipt/1` schema, exact S manifest and
original scan output. They bind S, actual adopted main5775, and local cloud Linux;
they do not invent a GitHub run id or use the #366 helper's hard-coded adopted
main8f82 provenance. E adopted these exact original bytes into canonical paths;
`ADOPTION_BEFORE_AFTER.json` and `ADOPTION_COMPLETE.json` prove four raw/Git
identities, the two-path artifact-only diff, S execution binding and clean source.
No architecture or Node gate was rerun for this adoption. The original
gate requests/results/streams remain under `commands/15-*` through `17-*`.

`commands/19-close-receipts` records an evidence-collector-only KeyError from
reading two policy keys at the wrong JSON nesting level. Its V0 script/raw
failure are retained. `20-close-receipts-corrected` fixes only those external
collector key paths and exits0; original judge/source/ledger bytes are unchanged.

All53 mutation stale entries are bridge source/oracle-restoration records:
52 ordinary judge-source changes plus M110's equivalence-audit oracle change.
M20 remains crashed, not assertion-killed. The ledger's raw bytes/hash/mtime and
Git blob remain unchanged. No full123 rerun, ledger regeneration/adoption,
manual expected edit, manual source-hash edit or empty-cache freshness claim
was performed. Publication can trigger the original Mutation evidence workflow
for new complete evidence.

## Remaining gates and publication boundary

Independent peer review PASS covers the source merges, Node controls, original
architecture streams, 604-input before/after identity, external artifacts and
honest mutation-stale classification. It does not mark the PR ready to merge.

The existing true-browser fixed/app-only-withdrawn/restored requirement remains
**UNRUN** on E, including named P53-3/P61-10/P61-11 failures. Full canvas,
the other browser gates, full native, fresh full123 mutation ledger and final
required CI remain **UNRUN**. No browser, server, Chrome, C build or shared-cache
operation was started in this phase; #363's real UI work was left undisturbed.
Root reserved the current window for #363's census. `BROWSER_PREFLIGHT.md` now
records the governing review's original full-canvas fixed/only-app-withdrawn/
restored commands, serially with2100seconds per phase, unchanged golden and zero
added skips. It requires a fresh root source pin after official ledger adoption.
FLOW_REPAIR_ONLY is retained only as an optional diagnostic and cannot substitute
for any formal full phase. No browser/server/native-build command was started;
root must schedule the window after census and official ledger verification.

Root may review E and the peer report, verify the original remote head remains
df39d193, and fast-forward the original source branch while setting the PR base
to main. The PR must remain draft with a current-state matrix that separates
these new S executions from historical receipts and pending browser/CI/ledger
gates. Nothing in this handoff merges a PR or main.
