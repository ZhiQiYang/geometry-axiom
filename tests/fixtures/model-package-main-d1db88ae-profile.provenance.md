# Released K3 main section-profile model package

Produced by the unchanged `modeling.build_package` implementation at main
`caf49852a4b40d4e61bdf76480c79b43bb5a3676`, using that checkout's unchanged
`tests.test_section_profile_modeling.scene()` and `request()`. The definitions
are `{"base_scene": scene(), "extensions": []}`. The source contains one
L section profile, three timber members and one 2400 mm run; the package has
three material meshes and one reference envelope. The producer verifies the
whole package with that same main executor, then writes
`modeling.common.canonical_bytes(package)`. No manifest field or geometry is
rewritten.

- Producer axiom revision: `d1db88ae99ca9b6858b0ada34d082e902f00c9f9`.
- Producer LF axiom SHA-256: `9d4f90aacbc863941c1065a6b962f760e7e842c4d7dda55a56c4dc321f9a0f93`.
- Fixture bytes: 35777.
- Fixture SHA-256: `a9cd87240320c8e67ba1aa5f06429829e67089449ff8ab141f62e8b447297a61`.
- Adapter: the producer checkout's `tests.binaries` model-base registry,
  built in a private directory, then inspected as fresh with its original
  sidecar. `GEOMETRY_MODEL_BASE` points to that exact adapter.

At private integration baseline `6c05f8d253e38f6d6f656c6d6791c51e2570163e`, the new regression fails with
`UNSUPPORTED/AXIOM_VERSION (I32)`. Adding only the released K3 version pair
to `PRE_SPACE_MERGE_AXIOM_VERSIONS` passes the full compatibility suite (29).
Removing the pair or its existing section-profile gate exemption produces the
same named regression failure. Changing the local axiom bytes also fails.
Restoring the fixed source passes 29 again. The original profile/Q23 suite
passes 20 and modeling runtime 46. The initial model-store Node run is 20 pass / 1 fail because the private harness PATH lacks python (spawnSync python ENOENT); initial WSL/tool exit 1 remains unchanged. An independent continuation at the same baseline, with identical fixed-init/fixture/original adapter, adds a private python-to-python3 shim and TAP output format, then passes the original model-store Node suite 21 with no skips.
All old test methods and the old Q38 five-package fixtures are preserved.

The continuation then runs the previously unexecuted original sync, check and reader suite (41 tests), all green with WSL exit 0; the original outer tool exit was not observed. A separate readback observer exit 0 does not replace that unknown status. This is targeted
proof against the frozen baseline plus the explicit one-pair source change
and true fixture; it is not a final-head native or seven-job result.

The full producer, frozen sources, actual adapters/sidecars, separate red and
green stdout/stderr, execution metadata and both original receipts are retained for the PR #206 evidence handoff.
