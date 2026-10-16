# Native kernel extraction

The public C API in this directory is independent of application and template
headers. Compile `exact.c`, `codec.c`, and `geometry.c` as separate translation
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

This is an intermediate extraction of shared primitives. The document stores,
typed source graph and complete candidate transaction boundary still require
the later GEO-261 slices; this directory alone is not a claim of full decoupling.
