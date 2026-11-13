# Python geometry consumer for rectangular-grid/1

`geometry_rectangular` composes the native recipe's successful cell regions
using the public `geometry_kernel` graph API. Each cell becomes a placed region
and source-bound extrusion; an ordered KEEP assembly retains its internal faces.
The package imports no host, modeling facade or woodworking template.

The native exporter is `tests/rectangular_python_harness.c`. It calls the existing
`rectangular_grid_evaluate` recipe, which calls the same public C K subdivision
implementation used by the first template. The exporter has no grid formula.
It emits all resolved source keys, kinds, revisions and exact values, explicit
field bindings, a frame, and every derived cell region. The Python decoder
validates these typed results and never divides a dimension into cells.

The recipe-view protocol is deliberately bounded. It does not claim to be the
application's complete native source graph. Changing width requires a new
successful native result; Python does not recalculate native cell sources.
Changing the bound thickness quantity uses the shared Python K evaluator.
Source keys exclude revision and remain stable across native recomputation.
The result identity includes all source revisions, result content and the
caller's execution identity. This protocol is not a scene or saved project file.

The sequence is width 1000, height 600, 5 columns, 3 rows and thickness 10:
15 members of 400000 mm³, total 6000000 mm³. Width 1200 yields 15 members of
480000 mm³, total 7200000 mm³. A subsequent width 1000 with 3 columns is rejected
by native K as an exact 1000/3 step. The native recipe leaves its prior result
bytes unchanged, and no new Python view is produced. The Python `ProgramSession`
therefore retains its committed program, source keys, result and revision.
This is result-level native replacement plus the shared Python candidate cell;
it does not prove the later application's complete native transaction boundary.

`tests/test_rectangular_python.py` has eight portable tests. Five run again in an
isolated installation containing only Python K and this second template. A
blocking import finder rejects the host and first template, and actual loaded
module paths must remain inside that installation. A separate copied-production
mutation removes shared K extrusion occupancy: both the second template's volume
oracle and the old woodworking extrusion wire digest must fail, then restore.

`tests/test_rectangular_bridge.py` has two native tests and requires the PR275 C
recipe source. It builds only C K exact/geometry/grid, the recipe and exporter
inside an isolated installation, then executes the real Python consumer in
isolated mode with only Python K and this template. Removing the real native
divisibility guard must break the same sequence. No application or woodworking
object is linked or imported. Run it through the shared compiler queue:

```text
python tests/test_rectangular_bridge.py -v
```

Set `GEO261_RECTANGULAR_BRIDGE_EVIDENCE` to retain exact build commands, source
hashes, executable hash, native JSON events and isolated Python outputs. Compiler
absence is an explicit skip; compiler failures, crashes or environment blocks
do not count as negative detections. The portable receipt does not claim these
native tests ran. Actual C→Python evidence is recorded separately after the
combined sources are frozen and executed by the validation owner.
