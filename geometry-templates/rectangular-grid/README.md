# rectangular-grid/1

An immutable, headless second template that consumes the actual public native
kernel. It is a program API witness under GEO-261 §8, with no application
registration, UI, scene syntax, saved format or material policy.

`rectangular_grid_evaluate` takes four typed source references: width, height,
column count and row count. Each supplied source retains its owner, field key,
field kind and revision. The result preserves the four resolved sources and
their exact normalized values. Reordering the source array does not change
references. Editing a source value/revision and evaluating the same definition
recomputes the dependent cells.

The recipe uses these public K operations:

| Operation | Actual shared implementation |
|---|---|
| Normalize exact values and calculate diagnostic fractions | `geo_quantity_normalize`, `geo_quantity_binary` in `exact.c` |
| Check definition coordinate bounds | `geo_coord_in_range` in `geometry.c` |
| Derive both axes' exact internal grid lines | `geo_interval_subdivide` in `grid.c` |
| Validate the rectangle and each cell's closed containment | `geo_region_is_valid`, `geo_region_contains_rect` in `geometry.c` |

There is no second subdivision formula in the recipe. Its loops only assemble
cells from consecutive lines returned by K. The source binder supplies this
fixed recipe's length/count schema; count has scalar arithmetic units but is
not interchangeable with a length field. Dimensions must normalize to positive
integer coordinates. This bounded example supports at most 32 divisions per
axis and 256 cells; exceeding either limit explicitly rejects.

For width 1000, height 600, columns 5 and rows 3, the output is 15 exact 200×200
cells. Changing columns to 3 returns `FRACTIONAL_CELL`, with the width source
key, value 1000/1, divisions 3, core status `GEO_GRID_NOT_DIVISIBLE` and exact
`required_step = {1000, 3, GEO_UNIT_LENGTH}`. No rounding or remainder
distribution is performed. Every failure leaves the caller's old result
byte-for-byte untouched, including a failure on the second axis.

This result-level replacement is a local value API guarantee. It does **not**
implement or prove the later shared dependency graph, expression evaluation,
preview freshness, source lifecycle, allocation or complete K/W/H candidate
transaction boundary. Sources are supplied explicitly; the template does not
load legacy definitions or claim D31/D64 source-graph support. Those remain
separate GEO-261 work. The recipe contains no Python geometry reimplementation.

## Verification

Run the registered suite with a C compiler:

```text
python tests/test_rectangular_template.py -v
python tests/run_all.py --only rectangular_template
```

The suite has **11 tests**: one source-closure test and ten native tests. It
copies only the seven required K source/header files, this recipe and its tests
to a temporary installation under the system temporary directory. Neither the
first template nor the application is present. All native cases build and run
against those copied sources, with no repository include/link search path or
prebuilt product binary. The Python driver also blocks known application and
first-template imports while those tests run. MSVC and POSIX C compilers are
supported; unavailable compilers are explicit skips, not passes.

One negative control removes the real K divisibility guard in that temporary
copy. It must compile successfully, execute normally, and cause the ordinary
fractional-rejection test to fail with `FRACTIONAL_CELL_ACCEPTED`; the unchanged
core is then tested again. A separate dependency assertion omits `grid.o` and
requires the link diagnostic to identify `geo_interval_subdivide`. That link
failure proves the required dependency and is **not** counted as a killed
semantic mutant.

Set `GEO261_RECTANGULAR_EVIDENCE` to a JSON output path to retain
the exact compiler/link commands, native case exits and output. The ordinary
test runner's source SHA and discovery-count receipt should accompany it.
This test-only destination survives `run_all.py` clearing inherited `GEOMETRY_*`
inputs; it does not alter compiler selection, product behavior or test results.
