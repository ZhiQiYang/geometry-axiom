# Native host boundary: frozen source and mocked process receipt

Executable Python source is the Git archive of
`c9e84b629231c96177712e6504859ada703a8399`.

```text
python tests/geometry_kernel_receipt.py --suite-set native-host --source c9e84b629231c96177712e6504859ada703a8399 --out <temporary-output-directory>
```

The unchanged `_unittest_runner.py` reports **22 tests, zero failures, zero
skips**. Raw discovery, output, source inventory and runner identity are included.

The tests write real temporary compiler, executable, source and recursively
included file bytes. They replace the subprocess boundary with a deterministic
fixture. They verify cache invalidation for source, include, compiler, command,
environment and executable changes; stale loaded sources; pre/post execution
checks; publication refusal on drift; and explicit source capability policy.
Nonliteral project includes fail closed instead of disappearing from cache keys.

One test copies the production implementation and removes five guards in turn:
cached output hashing, post-execution identity equality, loaded-source freshness,
post-compilation input equality, and project include closure. Each same behavioral
oracle must fail with exactly one assertion failure, not an import/syntax error;
the complete 21-case baseline must pass before mutation and after restoration.

Nine existing transport/protocol tests also passed in the working tree. Their
dummy subprocess fixtures now supply a dummy binary identity at the same mocked
boundary; their original argument and protocol assertions are unchanged. That
separate result is not included in the frozen 22 count.

No compiler, native binary, WSL process or browser was executed. This validates
Python host boundaries only. The same-candidate native source DTO serializer,
real native replay, and final integrated domain-decoupling gate remain pending.
