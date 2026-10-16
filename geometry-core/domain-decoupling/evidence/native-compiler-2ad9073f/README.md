# Native compiler diagnostic compatibility receipt

Source: `2ad9073f9b070105dfc512399d5e5d9bc6555efc`.
The executable test input was a frozen Git archive of that commit, not the
working tree's later typed-source changes.

```text
python tests/geometry_kernel_receipt.py --suite-set native-host --source 2ad9073f9b070105dfc512399d5e5d9bc6555efc --out <TEMP>/geometry-tests/geo261-native-compiler-2ad9073f
```

All 22 native-host tests passed, with no failures or skips. Ordinary compiler
failure keeps the historical message; a compiler-input change has a separate
diagnostic. Both fail without publishing a cached adapter. Existing source,
binary, compiler and loaded-module guards retain their removal controls.

These tests use real temporary file contents and a mocked process boundary.
No native compiler, adapter, WSL command or browser ran. This receipt does not
establish native DTO completeness or the final domain-decoupling gate.
