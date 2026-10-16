# Typed box source and opaque context receipt

Source: `d4f6a8aeaf2cad89c80aea3fe1897153f1fac8b1`.
All nine suites executed from a Git archive of this fixed commit.

```text
python tests/geometry_kernel_receipt.py --suite-set typed-sources --source d4f6a8aeaf2cad89c80aea3fe1897153f1fac8b1 --out <TEMP>/geometry-tests/geo261-typed-sources-d4f6a8ae
```

All 119 discovered tests passed, with no failures or skips: geometry 20, graph
27, legacy geometry compatibility 1, isolation 2, product runtime 4, candidate
transactions 31, neutral program session 4, host world 8 and native host 22.
The isolation suite executes 82 pure tests with only K and its neutral tests
installed; it also exercises the existing production-source mutation controls.

The new box-source cases use the real K evaluator for a source-bound Boolean
result, a same-identity source update, source dependency closure, missing/type
and coordinate-domain rejection, atomic partial roots and owner-context
matching. The declared opaque owner is independent of coordinate domain.
These are executable typed geometry consumers, not DTO shape-only tests.

The aggregate also retains the frozen old-wire oracles and actual guard-removal
controls added in earlier slices. Native-host tests mock the process boundary;
no native compiler, adapter, WSL or browser was executed. The product host has
not yet been switched to the new same-candidate native source DTO. Native graph
coverage, real native replay and final domain-decoupling acceptance remain open.

The older `py2` preset deliberately retains its historical 91 expected cases
for the original `10cbda745bf9692e1108d6da3351d69ddf3a4306` receipt. Use this
`typed-sources` preset for this source commit's actual aggregate counts.
