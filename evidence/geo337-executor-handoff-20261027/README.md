# Native/special executor final handoff

Fixed F: `cbf0fb621888596aa14ad5f2349b503e23b1b72d`. This is an executor scope index, not a replacement for the coordinator’s release matrix. Existing raw packages are referenced, not repacked.

| Scope | Verified actual result | Existing raw |
|---|---|---|
| native | 230 suites; 5328 pass, 0 fail, one original GDI skip; exit 0 within 2100 seconds | [732ef20e](https://github.com/ZhiQiYang/geometry-axiom/tree/732ef20e34876379a37eb69693a481becebea43e/evidence/geo337-native-validation-20261027/F-complete/) |
| oracle/reader | oracle unit 14/14 and default CI reused from F native; original golden 0/1/0, generation/compare, mutants-only and full quick exit 0; reader generation/check 0 and unit 51/51 reused | [7886f2ea](https://github.com/ZhiQiYang/geometry-axiom/tree/7886f2eaa3da7f9f4855104ca4b028d2d06ce6da/evidence/geo337-reading-a-oracle-20261027/) |
| RC | builder/checker original proofs each 0/1/0, original assertion failures, no errors/skips | [7886f2ea](https://github.com/ZhiQiYang/geometry-axiom/tree/7886f2eaa3da7f9f4855104ca4b028d2d06ce6da/evidence/geo337-reading-a-oracle-20261027/rc/) |
| required-eight | same-F native reuse; exact eight rows, 681 counted passes, zero fail/skip; no separate selected-wrapper run claimed | [7886f2ea](https://github.com/ZhiQiYang/geometry-axiom/tree/7886f2eaa3da7f9f4855104ca4b028d2d06ce6da/evidence/geo337-reading-a-oracle-20261027/oracle/required-eight-native-originals/) |
| PF3 | original exit 0; baseline 20/20, 19 semantic kills, restored 20/20; all 21 source/binary variants retained | [1d9b980d](https://github.com/ZhiQiYang/geometry-axiom/tree/1d9b980defec2659d7b08ee0a3ac782e00354780/evidence/geo337-pf3-20261027/) |
| Q38 | original exit 0; 43 killed + SPM24 equivalent; baselines native 29/model 20; original ModelError outcomes retained | [dd2cbf6a](https://github.com/ZhiQiYang/geometry-axiom/tree/dd2cbf6a558b4af240ab4702cc8402621380881b/evidence/geo337-q38-20261027/) |
| P52 | formal/verifier/outer 0; fixed main adbaebf9c73ea6801d7b4d5214e4b846b132923b; 16+16 samples, ratio 0.849147775; controls 0/0/1/1/1 | [a08a036d](https://github.com/ZhiQiYang/geometry-axiom/tree/a08a036db335e88608ead761539d3e60b75e8e5d/evidence/geo337-p52-20261027/) |
| #314 | same-F six native suites 103/103 and inspector 12/12; M121 original execution 82c922a3941525d3a094ac0158bdc7dea57ea360, 0/1/0 streams verified; no rerun or SHA relabelling | [cbf8df4f](https://github.com/ZhiQiYang/geometry-axiom/tree/cbf8df4facf87b40db0fe46581c0b20131afada2/evidence/geo337-followup-scope-20261027/geo314/) |

## Only new execution in this closeout

The original Reading A CLI-order probe was not in native and had not been collected at F. It now completed with real exit 0 and complete protocols using the unchanged fresh F bridge from accepted P52. No compile was repeated. Both orders `(1,2)` and `(2,1)` have `both_place_accepted=false`: timber 1 is rejected respectively for a free span endpoint and for no legal span on its centerline. **This is diagnostic completion, not construction acceptance.** The original historical stage criterion `diagnostic_completed and construction_route_observed` evaluates false; that evaluation is derived, not a fabricated execution exit of the historical wrapper. Original probe, 30-second child deadlines, raw stdin/stdout/stderr in the receipt, and source/binary hashes are retained. No #335 rule or axiom changed.

## Ownership and release

- Browser/card/axiom/extra168 and whole-memo remain with the existing browser/recovery owner. The coordinator has sent whole-memo to the environment holding the original R8 ELF payloads; do not duplicate or rebuild them here.
- Reading A initial construction/#335 remains a specification/route question with actual negative observations now preserved. No unplaced-contact or batch exception is introduced.
- P189 comparison-policy approval and remote CI remain coordinator items. Original comparison rules and red receipts are unchanged; valid R8 samples are not redrawn.
- Architecture original F checks were already present in recovery handoff; native/oracle/reader/required-eight/PF3/Q38/P52/#314 are not rerun. No other unowned, independently executable original acceptance gap was found in the original command plan.

All inspected checkouts are clean, original raw remains retained, no Chrome/Node/compiler remains, and the owner lock is available. This executor releases execution after publication of this small index plus the new CLI diagnostic; it does not wait or start duplicate same-SHA work.
