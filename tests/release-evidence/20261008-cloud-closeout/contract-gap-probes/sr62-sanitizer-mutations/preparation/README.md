# #62 native sanitizer and five required mutations — prepared, not executed

Source snapshot: `d8642b2e684038cbb8e24aba057c44e7aac1b231`, clean at preparation. `plan.json` binds 54 copied source/test/fixture files with exact byte hashes. The C subset is the recursively resolved quoted-include closure of `geometry-web/web_bridge.c`; the copied tests and modeling imports remain unchanged. Product source is the previously tested `5174a8dafd8c48329d7166abbd3d104e3c28c0c4` product state, with the later documentation merge recorded separately.

The documented old ASan/UBSan 152 receipt at `/tmp/subdivision-repeat-only-sanitizers-valid.log` is unavailable. All regular members of five tracked release archives were hashed; none matches its published SHA `00766856e9148ff432cf7826e4b9958f29c48d30f1cd9b7aad3a38b54bf0c430`, and none has a sanitizer/ASan/UBSan filename. This bounded search is recorded in `prior-evidence-audit.json`; it does not claim the original run failed or never happened. The tracked 48 general-scene mutation definitions contain current 9357d0b9 execution provenance rather than the document's older f0 narrative. They do not replace these five subdivision-specific faults.

The new scope is 41 unchanged subdivision oracle methods plus 13 unchanged grid-system contract methods under ASan/UBSan. This is a new 54-test native scope, never a relabeling of the missing historical 152. Five mutants each run only their original targeted method, then the same method runs again after the private active binary path is restored to retained pristine bytes. The pristine source tree is never mutated; a second identical full 54 run is deliberately unnecessary.

| Fault | Single mutation | Original semantic failure required |
| --- | --- | --- |
| M62-1 | Disable only exact pitch divisibility guard | `600/7` accepted instead of DIVISION_NOT_EXACT in the existing rejection helper |
| M62-2 | Skip only serialized rule records, retain highwater | Original native dump is missing `grid-source-rule 0 key 1` |
| M62-3 | Omit only systemId comparison at formal line dereference | Source 1 with same key wrongly accepts a guide referring to source 0 |
| M62-4 | Skip only face/hole clipping, retain parent-cell bounds | Literal hole-split segment endpoints mismatch |
| M62-5 | Skip only lexical capability encounter guard | Default-highwater syntax without capability marker wrongly replaces existing World |

M62-4 selects #62's permitted clipping alternative; M62-5 selects its permitted capability-preflight alternative. These do not claim sample-index or second-face mutation coverage. The original tests, fixtures, registered counts and expected values are not changed.

`SEMANTIC_ASSERTION_KILL` requires exit 1, the named original method, an `AssertionError` at its pinned existing assertion line, no unittest errors/skips/expected failures, healthy native exit, and no sanitizer diagnostic. Compile failures, crashes, timeout, wrong assertions, unrelated refusal and infrastructure failures are not kills. Full transport transcripts and loaded scene bytes permit independent inspection of the observed failure reason. The oracle adapter changes binary discovery to the hash-pinned isolated executable and names transport files; it never substitutes answers. Native stderr is written directly to a named file from process creation so a timeout preserves it. Unexpected nonzero native exits, leak/ASan/UBSan diagnostics, stdout tail or cleanup errors fail the run.

Compile flags are `-std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -fno-pie -no-pie`, linked with `-lm`. Each oracle process and its native children receive a 64 MiB stack. `ASAN_OPTIONS=detect_leaks=1:halt_on_error=1:abort_on_error=1` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1` are mandatory. No suppression, registry sidecar, official binary replacement, service restart, browser launch or process outside the driver's own groups is involved.

Root is the sole authorized serial runner. When that slot is granted:

```sh
python3 /workspace/closure-evidence/final-contract-probes/native-sanitizer-mutations/run.py \
  --execute \
  --out /workspace/closure-evidence/final-contract-probes/native-sanitizer-mutations/run-01
```

The output directory must not exist. Six sanitizer unity builds and eleven oracle subprocesses run serially. Each compile and each oracle has a 300-second deadline. No runtime estimate has been measured; the sum of these explicit maxima is 5,100 seconds plus bounded setup/version/cleanup overhead. A supervising timeout should exceed that total (for example 6,000 seconds), rather than killing the driver before it can reap its own process groups. The driver handles SIGTERM/interrupt by killing and reaping its own in-flight group before restoring private binary bytes; it records interruption as incomplete, not a mutation result. Tool calls may yield frequently while execution continues.

Preparation only copied/read files and parsed Python syntax. The first static preparation attempt rejected a repeated assertion string; it was corrected to resolve that string within the original named method's AST range. This changed provenance selection, not a product precondition or oracle. `prepare-01-failure.json` retains that failed attempt as a tool-output transcription; subsequent preparation commands/stdout/stderr and their exits are raw files. Actual native compile/test commands, complete stdout/stderr, exits, durations, source/mutation/test/binary hashes and restoration results will be created only by the execution driver.
