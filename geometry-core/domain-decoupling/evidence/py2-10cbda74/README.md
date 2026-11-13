# PY2 typed evaluator, host/provider and candidate-consumer receipt

Executable source is the frozen Git archive of
`10cbda745bf9692e1108d6da3351d69ddf3a4306`, not the working tree.

```text
python tests/geometry_kernel_receipt.py --suite-set py2 --source 10cbda745bf9692e1108d6da3351d69ddf3a4306 --out <temporary-output-directory>
```

All eight suites pass: **91 tests, zero failures, zero skips**. The unchanged
repository `_unittest_runner.py` supplies each discovery count and raw log.
`summary.json` records source-tree identity, archive file inventory, runner hash,
Python version, commands and each raw result. The working tree contains subsequent
native-host work; the archive explicitly excludes it.

The isolation suite installs only K plus four neutral test modules and runs 78
tests under Python `-I -B` with host/template/legacy imports blocked. Its separate
production-source mutation controls remove hole containment and source-normal
orientation; both the neutral oracle and frozen legacy mesh oracle must detect
each mutation. Candidate-cell tests additionally run their four removed-guard
controls. These failures are behavioral assertions, not import or syntax errors.

The host runtime test pins complete success/error results for 27 cases against
the pre-move engine at `3a9dc84b`, and confirms that the actual product path calls
the public typed K evaluator. Native data is supplied at the loader boundary.
The host world and neutral session both exercise the same CandidateCell.

No compiler, native binary, WSL service or browser ran in this receipt. Complete
same-candidate native source DTOs, native execution pinning and the unchanged
native-backed package/transport suites remain later gates. This receipt is not
a claim that domain decoupling is complete.
