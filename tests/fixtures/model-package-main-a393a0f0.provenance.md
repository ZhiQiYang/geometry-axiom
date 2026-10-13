# Released main model package fixture

Produced on 2026-10-13 by the unchanged `modeling.build_package` implementation
at main `2004c6c8bebe1bbff2df142630b630e1ee5115b8`, using the first normative
`geometry-core/modeling-cases.json` case (`wall_through_hole`). Its definitions
and request are passed unchanged. The producer also verifies the package with
that same main version, then writes `modeling.common.canonical_bytes(package)`.
No manifest field or geometry was rewritten for this fixture.

- Axiom revision: `a393a0f01284433ca20fe8b10d9f21111026e7f1`
- LF axiom SHA-256: `b06ffecf4f3b7a907a50d329f2073799d9514daa26b9056380f62ad37e5725ee`
- Fixture bytes: 14317
- Fixture SHA-256: `5c4ba0cf7c74087c2735aa7a87e392ae7a137440306d3528de8d756887a4a607`
- Producer adapter: `cc -std=c11 -O2 geometry-core/model_base.c -lm -o <main-model-base>`
- `GEOMETRY_MODEL_BASE` points to that main adapter during production.

The regression first fails on #200 `e8da54d2c20406da045aa04b2c0f2883afae9829` with
`UNSUPPORTED/AXIOM_VERSION (I32)`. With the one additional accepted version pair,
the compatibility suite passes 28 tests. Removing only that pair makes the
same named regression fail; restoring it passes all 28 again. The original
modeling runtime suite passes 46 tests. Existing test methods and capability
guards are unchanged. These are targeted checks, not final merge-train results.

Full frozen producer, sources, binaries, stdout/stderr, commands and receipts
are delivered with PR #200's B1 evidence packet.
