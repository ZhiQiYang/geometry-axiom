# #345 E formal CI accepted

Source E `79cf0f16bca9ce55b2b19e793650d5e4e2e2c5e6`; actual integration checkout
`058f793590301e1e58074be072d0296d432e184b`; tree
`c05e281326b3fe9b959e9ea8d59fcac28c067137` is exactly E's tree. Real merge
parents are main `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d` and E.

| Automatic workflow | Run / attempt | Terminal result |
| --- | --- | --- |
| Geometry integration | [41387497096](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41387497096) / 1 | success, 10 jobs |
| Mutation evidence | [41387497118](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41387497118) / 1 | success, 10 jobs |

21 official ZIP digests match; all 20 direct job logs equal the official run ZIPs
byte for byte. Original native reaggregation exits 0 and exactly reproduces the
official summary: 230 suites, 5340 counted = 5339 passed + one specifically allowed
Windows GDI skip, no counted failures. Official registry control is real 0/1/0.
All six browser groups passed; full canvas is 85 sections / 2267 assertions,
exactly matching current golden. E has none of M's appended BrokenPipe diagnostic.

The unchanged original Mutation verifier exits 0 against fresh E artifacts;
its summary and ledger equal the official aggregate byte for byte. All 123 rows /
120 active are 114 killed / 1 crashed / 5 equivalent / 3 retired; all remaining
categories zero. Seven official cache controls are real strict 0/1/0; original
binary/sidecar/source/tool/closure checks and 159 independent bridge raw parses
pass. The original architecture three command receipts and raw/source hashes pass.

- Newly generated E CI ledger SHA256:
  `8af0fb4ab26d997a4b9f11e8552388277f167c20c08e60966631af3c97bf773d`.
- E CI summary SHA256:
  `90b760258bc6870ec517838cf413b28011d54a67d13152ee3eae111cc96764ba`.
- The already adopted source ledger remains byte-identical to the earlier M
  artifact (`0be90a297b4f4b4fd5a2e60d528886845cc2c8d823e912ef3b0763ba68f7eb1c`);
  this collection does not replace it or rewrite execution identities.

The last mutation job, bridge-2 `125092244692`, was created 04:18:48 UTC, started
04:30:23 and completed successfully 04:51:12. Waiting was 11m35s; actual job runtime
was 20m49s, within its original 45-minute timeout. The mutation step itself ran
04:31:21–04:51:07 (19m46s); the final `Complete job` step succeeded. The run's
04:16:05 creation time is not the mutation job's execution start.

M integration `41382891799` retains its two original stale failures and M source
identity. Its 5340 counted assertions were 5339 pass + one allowed GDI skip, with
one additional uncounted freshness failure; the reviewed current PR body describes
that correctly. No old raw evidence is relabelled as E.

No blocker remains for this E CI receipt. This collection only downloaded and
validated original receipts/bytes; it ran no local product, Chrome, compiler,
build or negative-control unittest and started no CI. Source is clean; source,
PR body/base/comments were not changed here. All raw files remain outside this
small publishable subset; exact commands, exits, hashes and artifact identities
are recorded in `receipt.json`.
