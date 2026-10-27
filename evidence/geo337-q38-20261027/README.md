# Fixed-F Q38 complete mutation acceptance

Execution source `cbf0fb621888596aa14ad5f2349b503e23b1b72d`; original complete Q38 producer exit **0**. All 44 original cases SPM01–SPM44 executed with no selector, group filter or explore mode. Summary: `{"equivalent": 1, "killed": 43}`. Both original baselines passed with zero skips.

Exact commands, UTC start/end, actual exit codes, explicit environment and streams are preserved per stage. The private bridge and model-base prerequisites were freshly built from F. The acceptance command was `python3 -B -u tests/section_profile_mutation_check.py --receipt <OUT>/q38/receipt.json --logs <OUT>/q38/logs --jobs 1`. Stack 16 MiB; original native-compile limit 600 seconds, test/model-adapter limits 900 seconds; no new overall time limit. Total prerequisite plus producer elapsed 855.233 seconds. Original source hashes remain unchanged and checkout clean.

The original equivalent classification is retained. Cause-labelled ModelError outcomes remain ERROR; they are not relabelled AssertionError failures. The independent collection pass reapplies the unmodified original verdict function to every original exception receipt, checks the complete registry and binary-difference requirements, and compares every archived source byte with the original snapshot. No tests are rerun during collection. See VERIFICATION.json for per-case classifications and baseline counts.

Complete original persistent raw logs, exception evidence, compile receipts, final receipt and outer streams are included. The unmodified producer itself removes its disposable mutant trees and binaries; no claim is made that those discarded temporary files were retained. The exact original source snapshot, original full case definitions and retained prerequisite ELF/fingerprint files are included. This source snapshot and the unmodified producer define every patch; no replacement judge or weaker assertion was introduced.

Operational changes are private output/TMPDIR and private prerequisite bridge paths, an exclusive owner lock, and the same process-local child subreaper used for accepted native validation. No shared /tmp/geometry-tests writes, mounts, product edits, main merge or deployment. No remaining process in the original producer's process group was found.

This result is bound to F, not the historical L/F9 receipts. It does not re-run valid native, oracle, reader, required-eight or another task's browser scopes. P189 exact comparison rules remain unchanged.
