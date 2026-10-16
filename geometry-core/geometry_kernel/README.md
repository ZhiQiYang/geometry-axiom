# Pure exact geometry — PY1 boundary

This package uses only the Python standard library. It does not load a template,
interpret legacy source kinds, read a repository, or start a native process.

`types.py` exposes immutable validated `FrameDef`, `RegionDef`, `RegionSetDef`,
`BoxDef`, exact `Quantity`, stable `SourceKey`, and opaque `Provenance` records.
Region validation checks complete loops and holes; a box is constructed from
positive extents and a right-handed frame. Private evaluated geometry retains
an inside predicate; it is not a public template input.

`geometry.py` owns the single product implementation of region extrusion,
exact arrangements, shell topology, regularized Boolean operations, source
coverage, canonical triangle ordering, components, cavities and volume.
`modeling.geometry` translates legacy input/output and diagnostics to this
implementation. Opaque provenance ordering preserves legacy mesh ordering.

This is the first extraction slice. The legacy engine still owns definition
graph traversal and request policy. Typed source snapshots, a neutral graph
evaluator, host/provider assembly, and final source closure gates remain later
slices. PY1 does not establish complete domain decoupling.

Lightweight validation (no native compiler or binary):

```text
python -m unittest tests.test_geometry_kernel_geometry tests.test_geometry_kernel_compatibility tests.test_geometry_kernel_isolation -v
```

The 21 tests include 18 geometry tests, a frozen pre-extraction wire digest
oracle, and two isolation/control tests. The no-template test copies only this
package and the neutral test module into a new temporary directory, then runs
Python with `-I -B` and a blocking import finder for host/template/legacy names.
It checks actual loaded module paths. The control test edits copied production
source for hole containment and source normal sign; each mutation must fail
both its pure geometry oracle and the legacy facade's frozen mesh oracle, and
restoration must make both pass. Native fixture replays are not claimed by this
lightweight suite.

The frozen wire digests were captured from base commit
`cdaa2010ca27ba011b5e21fabccbab93a574c7b4` before extraction. They cover a through
hole, reversed source winding, a Boolean cavity, split components and EMPTY.
