# Native source catalog to modeling templates receipt

Source: `0c6c585a125575ba981778fc7895bd1419eae60f`.
All eleven suites executed from a Git archive of this fixed commit.

```text
python tests/geometry_kernel_receipt.py --suite-set source-runtime --source 0c6c585a125575ba981778fc7895bd1419eae60f --out <TEMP>/geometry-tests/geo261-source-runtime-0c6c585a
```

All 146 discovered tests passed, with no failures or skips. The previous 136
geometry, graph, transaction, host, transport and compatibility tests remain;
the new source-runtime suite adds ten cases.

The explicit `source_graph=True` runtime compiles placement frame/region, box,
quantity and profile member/envelope inputs as source references. The W binder
requires complete, correctly typed root associations and retains named native
parameter fields, including exact ratio values. K receives every source node
and all three dependency edge kinds, including unselected definitions.

Synthetic native envelopes exercise the actual H/W/K path and retain all 27
frozen old-wire success/error digests. Source updates change the actual box or
extrusion mesh; rotated local box faces preserve old provenance on output,
while their opaque identities remain in K. Every component of a region reaches
K. Unsupported legacy output feature identities are rejected explicitly.

Three copied-production controls remove actual source consumption or binding:
replace a source box with the old literal box, replace a source region with the
old single outline, and remove the unbound-root check. Each must make exactly
one test fail by assertion, then restore to green. Import, syntax, compiler or
process failures do not count as these negative detections.

This receipt executes no native compiler, adapter, WSL or browser. The product
loader still uses the earlier explicit snapshot path until native coverage and
source-matched replay are complete. Source graph mode never falls back to it.
No new product source capability or legacy wire field is introduced here.
