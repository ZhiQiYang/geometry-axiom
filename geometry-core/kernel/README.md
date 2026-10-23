# Native kernel extraction

The public C API in this directory is independent of application and template
headers. Compile `exact.c`, `codec.c`, `geometry.c`, `grid.c`, and `parameters.c` as separate translation
units for a standalone client. The legacy application normally includes
`kernel_unity.inc` once; defining `GEOMETRY_KERNEL_EXTERNAL` makes that entry
include declarations only, so the application can link the same separate K
objects. Never compile both forms into one executable.

- `types.h` / `exact.h`: exact scalar and length quantities. Count and ratio
  remain distinct parameter field kinds in the application; both use scalar
  arithmetic. Failure statuses are neutral. The host maps them to the existing
  command diagnostics.
- `codec.h`: integer-only strict JSON, canonical UTF-8 serialization, SHA-256,
  base64 and read-only token access. Parsed values own their token strings and
  borrow the original input. `geo_json_free` is required after failed parses
  too. Sorted-key arrays are caller-owned. The old include facade contains no
  parser or arithmetic implementation.
- `geometry.h`: bounded orthogonal primitives, borrowed vertex/region views,
  frames, boxes, containment, line clipping and complete strip intervals.
  View predicates consume validated loops/regions. Validation entry points
  check shape/storage bounds before computing. Vector arithmetic takes
  components within the coordinate bound; frame transforms use valid cardinal
  frames and bounded input coordinates. Intermediate transformed coordinates
  need not themselves be definition coordinates.

Geometry views carry no edge fixation, object kind, role or source-language
token. Strip callers supply the selected obstacles; policy concerning contacts,
supports, selected intervals and source identities stays with the caller.
Region sets retain all components, including an empty set. Line clipping and
strip capacity failures are explicit; callers cannot interpret partial output
as complete geometry.

`tests/test_geo261_native_kernel.py` and `tests/test_geo261_native_geometry.py`
compile isolated K sources with no repository include search path. Production
negative controls link the real bridge object against exactly those K objects,
then replace one K object and require both the standalone and bridge witnesses
to change. Compilation failures and crashes are not successful negative controls.

This is an intermediate extraction. The remaining document stores, typed source
graph and complete candidate transaction boundary still require later GEO-261
slices; this directory alone is not a claim of full decoupling.
# Exact coordinate sequences

`grid.h` owns body/gap formulas, alternating shifts, finite sequence expansion,
signed lattice coordinate/window evaluation and exact equal subdivision.
The host maps its historical source variants and diagnostics onto this neutral
API; placement, role preferences, stored source identities and rule ownership
remain outside this primitive slice. A derived lattice base can exceed the
output coordinate range: arbitrary signed indices are checked when evaluated.

`geo_loop_rect_area2` and `geo_region_set_intersects_rect_positive` provide the
exact clipped-area predicate used by real subgrid cells, including holes and
all region components. Neither bounding boxes nor sampled display lines stand
in for a cell's geometry.

`parameters.h` provides an opaque parameter store, typed card/field views,
identity/high-water mutation operations, exact dependency evaluation and clone
ownership. `parameters.c` owns definitions and derived values; it takes no
World, template or host state. Its neutral errors retain exact source identities
and an ordered field trace. The host maps them to the existing diagnostics and
owns input text, scene/package encoding, atomic-load flags and canvas cleanup.

During the whole-document POD transition only the private H aggregate includes
`kernel/internal/parameter_store.h`. That preserves complete history/preview
value copies without adding a shallow heap pointer to World. Template consumers
use public const views and operations; standalone clients need only the public
header and create/clone/destroy APIs. This transitional aggregate is not the
completed document/candidate boundary.
