# PR #345 current-main convergence

The local candidate is `577b2e81967b3019352f65df5ffe6dc48eb6202f` on
`codex/issue214-main-convergence-20261102`, checked out at
`/tmp/geometry-pr345-20261102`.

The latest ordinary merge commit has parents:

- previous main-converged candidate and actual selected19 execution
  `c8db6777819c844064aa79baf089ff1ce58d5e5f`;
- approved tool dependency #366
  `502a64ff6214dd6060927b7f14643a533536f20d`.

The first ordinary main convergence remains `c8db6777`, with parents:

- original remote #345 head `99646d418bc5e886a92bfdabe33e68780e88fe3b`;
- current main `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d`.

Relative to that main, the candidate retains only the original
`tests/test_rule_case_workbench_http.py` change adding
`kwargs={"poll_interval": 0.05}` to the fixture's `serve_forever` thread and
13 historical evidence files, plus the four original #366 tool files listed in
`TOOLS_MERGE_IDENTITY.json`. The historical evidence Git mode/type/blob entries
and the complete target test blob equal the original #345 head. No product,
assertion, timeout, expected count, registry, SSOT, reader, or CI implementation
was changed relative to main except that original polling line. The four tool
files retain exactly #366's original mode/type/blob entries; no other source
changed from `c8db6777` to this candidate. `STATIC_CLOSURE.json`, `MAIN_DELTA.patch`,
`STATIC_SUBCOMMANDS.json`, and the compressed raw Git outputs establish this
scope. The bridge's 195 source inputs also equal main by exact Git entry.

The selected-suite execution remains the first main-converged source, and has
not been relabelled as the later tool-only merge:

```text
cwd=/tmp/geometry-pr345-20261102
HEAD=c8db6777819c844064aa79baf089ff1ce58d5e5f
python -B tests/run_all.py --build --only test_rule_case_workbench_http
aggregate exit=0
outer elapsed=47.28468623300432 seconds (including a fresh bridge build)
original unittest result=19 passed / 0 failed / 0 skipped, 27.48 seconds
original aggregate strict expected count=19
original suite timeout=1200 seconds
```

Original command/exit/raw streams are in `commands/09-selected19/`; the original
suite JSON and both raw row logs are preserved in `shared-after/`. The original
aggregate printed its partial-execution boundary and returned exit 0 without
`--update-expected`, `--allow-skip`, altered assertions, or altered deadlines.
This execution covers one selected suite; full native, browser, and required CI
were not run by this task. `TOOLS_MERGE_IDENTITY.json` and
`TOOLS_IDENTITY_SUBCOMMANDS.json` establish exact equality of product/test
sources and the 195-input bridge build closure from that execution to the new
tool-only merge. The selected suite was not rerun after the tool merge.

The root granted a short shared-cache window after #363 moved to private runtime
binaries. `RUNTIME_BEFORE.json` and `RUNTIME_AFTER.json` preserve every registered
shared binary/sidecar identity. This run rebuilt only bridge for the current
main-equivalent C closure. The new bridge and exact sidecar were copied with
metadata into `runtime/`, and the original freshness oracle accepted the private
copy. Protected source hashes/inodes/mtimes remained identical before and after
the run. The three new selected-row artifacts were saved, and previous shared
row-log bytes were restored. The worktree remains clean at the merge commit.

The earlier six-phase timing/correctness evidence remains execution
`2199cda8896b47c7ad2b6c10479e5e0cbdb67c83`; it has not been relabelled as this
candidate's execution. Its polling withdrawal is a correctness-equivalent
control: all six phases exited 0, and withdrawal restored extra waiting rather
than killing a correctness mutant. This task did not rerun that historical A/B
timing experiment or claim a new speed comparison from the single fixed-source
selected run.

At `577b2e81`, the original `python -B tests/mutate.py --check` returned exit 1
in 5.384694 seconds: 123 definitions/123 records, 62 killed, 1 crashed, 4 equivalent,
53 stale, 3 retired, and zero survived/invalid/blocked. Every stale entry is a
bridge source/oracle-restoration record whose judge source changed; this is the
expected freshness consequence of the fixture test change. M20 remains crashed,
not assertion-killed. The saved ledger bytes, Git blob, and mtime are unchanged;
see `commands/16-mutation-check/`, `TOOLS_MERGE_AFTER.json`. No empty-cache run was
treated as fresh evidence, and no ledger, expected counts, or source hashes were
edited.

The stale-reason detail is 52 ordinary judge-source changes and M110's one
`equivalence audit oracle changed` record. The first local postcheck collector
incorrectly required the Chinese ordinary-judge message on all 53 and exited 1;
its raw command 17 failure is preserved. Correcting that evidence-only predicate
to recognise the original M110 equivalence reason produced command 18 exit 0.
No product, judge, ledger, or original mutation-check output changed.

#366 remains an unmerged dependency; the intended #345 PR target remains main,
not the tool branch. After root publishes the candidate, its Mutation evidence
workflow must execute the full 123 and deliver a fresh ledger, and required CI
must reach a reviewable terminal state. Neither the new ledger nor that CI is
complete at this handoff, and the PR remains draft.

No push, PR base edit, PR body edit, comment, approve, merge to main, rebase, or
force push was performed. Root can review this merge and peer report, confirm
the original remote source ref is still the recorded parent, then fast-forward
the original source branch and set its PR base to main under the authorized
workflow. Required CI and the current PR matrix must bind the resulting published
head; this selected result alone does not mark #345 ready to merge.
