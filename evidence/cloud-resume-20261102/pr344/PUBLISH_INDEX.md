# PR344 compact original evidence

This is a selection of existing receipts for one audit-branch adoption. It does
not add a test execution or modify a source branch. `PUBLISH_MANIFEST.json` lists
each selected local-relative path, byte count and SHA-256.

Actual Node, architecture and saved-ledger-check execution source:
`eccebabc85acf74e30274b8ea8e24db863d8843b` (S).

Canonical artifact adoption source:
`503cfc59354893859ae9e6e4a6ab7c11d7972517` (E), parent S. E changes only the
architecture report and receipt; all four canonical artifact bytes equal the
peer-reviewed originals. The manifest identifies the already-published canonical
files by Git blob and raw hash rather than copying them into this packet again.

The selected original evidence covers:

- source/main/tool merge commands and the two derived-file conflict resolution;
- original Node command fixed/withdrawn/restored, exits0/1/0 with pass9/6/9,
  fail0/3/0 and skip0; all three phase requests/results and raw streams are kept;
- original architecture CLI, generic205 and product18 commands and raw streams,
  exits0/0/0, zero skip, 798edges and zero diagnostics;
- one complete604-input identity inventory, exact before/after duplicate hashes,
  original source collector and source Git identities;
- saved `mutate.py --check` exit1 with53bridge stale, unmodified ledger identity,
  and M20 retained as crashed rather than killed;
- canonical adoption before/after hashes and independent peer conclusions.

The Node withdrawal is the existing original test against a private full app
copy with only its successful-ready `connection.error` clear operation removed.
The packet retains the unchanged control driver and all app/test hashes. Large
private app copies can be reconstructed from pinned source S and that single
explicit transformation; they are not duplicated here.

`ARCHITECTURE_INPUTS_AFTER.json` is byte-for-byte identical to BEFORE. Only one
physical inventory is selected; the manifest records the other original path
as a verified duplicate alias. Likewise the original scanner stdout is selected
once and its identical canonical scan blob is a source reference. Per-command
empty stdout/stderr channels remain separate semantic records, even though they
share the empty-file hash.

The original failed main merge and evidence-collector KeyError are retained
with their successful resolution/correction. These are not hidden or relabelled
as test failures. The two collector versions are retained because they were
actually executed; neither changed a judge, source, ledger or expected count.

Not covered by this packet: true-browser P53/P61 fixed/withdrawn/restored, full
canvas, the other browser gates, full native census, fresh full123 mutation
regeneration, or final remote required-CI acceptance. The browser file is a
preflight plan, not an execution receipt. No server, Chrome or native build was
started by this packet preparation. Later root-run remote CI/publication state
must be reported separately.

No ELF, runtime binary, historical evidence archive, full Git-tree dump, private
app copy, or duplicate canonical artifact payload is selected. Historical574
evidence paths are identified in the source record and remain in their original
Git history; their payloads are excluded.
