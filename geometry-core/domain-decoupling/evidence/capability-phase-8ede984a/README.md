# Capability and export phase compatibility repair

Source: `8ede984a4788d7373678af3c565823cdbb344b57`, executed from a frozen Git
archive with `geometry_kernel_receipt.py --suite-set capability-phase`.
The unchanged unittest runner reports **4 tests, zero failures, zero skips**.

Fresh review found that the PY2 controller emitted OPEN_SHELL before CAPABILITY
when `build_package(..., capabilities=[])` requested an open composite-space
clearance. The previous engine evaluated all definitions, then gated
capabilities, then attempted export. PY2 had attempted export before that gate.

K's neutral validation-only mode still evaluates the complete source and
geometry graph, including unused Boolean and inward-interior contradictions.
It returns before selected-grid construction and root output. H merges those
definition diagnostics with its capability diagnostics before any export.
No template callback or legacy capability vocabulary enters K.

The real public `build_package` regression checks complete diagnostics for an
open clearance and a selected-grid capacity case. An unselected inward interior
with missing capabilities must still match the old complete frozen digest.
All 27 existing success/error oracles remain unchanged. A copied production H
source mutation removes the phase guard; the same public regression must fail
with one assertion failure, then pass after restoration. Import and syntax
failures do not count as detection.

Native snapshots are fixtures at the established loader boundary. No compiler,
native binary, WSL process or browser was executed. This repair does not claim
complete native source DTO coverage or final integrated acceptance.
