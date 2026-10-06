# Read-only cost review for #118

Source baseline: `11dc339152e05ea811972b8c0c15ff29520207cd`.
Historical timing run: `3019c036c74633a0379714180fa6d68af067d88e`, proven by
`/workspace/pr136-3019c036-review/receipts/16-test-final-state.log`.
No suite, build or service was launched during this review.

## Measured historical times

| Suite | Aggregate process row (s, rounded) | Reporter total (s) | unittest run (s) |
|---|---:|---:|---:|
| py:test_axiom_reader | 87.7 | 87.60 | 87.465 |
| py:test_model_update | 58.7 | 58.65 | 58.522 |
| py:test_serve | 13.1 | 13.01 | 12.883 |

The outer aggregate receipt measured 363.113 seconds. Its suite sum was
332.1 seconds. The approximate 31.013-second gap is outside the suite clocks,
not measured build-only time, idle time, or waiting time. The log shows five
cold native builds, but does not contain a separate build duration.

The unittest clock measures TextTestRunner.run, including suite fixtures,
test setUp/tearDown/cleanup and body work. The three Python suites have no
per-test, native-child, reader-rebuild, sleep, shutdown or stop-wait timing.
Their differences across the three clocks are also rounded and cannot be
attributed to one activity.

Other recorded process rows include node:tests-js 50.0 seconds,
py:test_space_modeling 22.0, py:test_scenario_verify 18.2,
py:test_bridge_integrity 11.7 and py:test_timber_support_projection 10.3.
Node's log has per-test durations, including a 14.916-second portable-format
parent case and an 11.412-second native missing-support case. Node file
parallelism and inclusive parent/subtest timings prevent summing all such
entries as suite wall time.

## Source paths and unmeasured activities

* Reader: tests/test_axiom_reader.py repeatedly calls full rebuild and validate,
  including corruption families and SSOT/DOM checks. sync_axiom_reader.py:668
  invokes the real reader inline renderer in a Node subprocess; rebuild:1454
  performs block identity/review preservation, witness embedding, trace
  reconstruction and patch checks. validate:823 also uses the real renderer.
  These sources contain no explicit sleep. Their individual durations remain
  unmeasured; 87.7 seconds must not be labelled "reader CPU" or "rebuild time".
* Model update: prepare_update:367 performs native old-record replay, new-scene
  load, two fresh native graph reads, new preview, and runtime checks before
  and after. tests/test_model_update.py:448 also builds an isolated C projection
  fault oracle. No fixed sleep was found in this suite or producer. Native
  execution, compilation, Python validation and cleanup shares are unmeasured.
* Bridge cleanup: tests/_bridge.py:146 closes stdin and waits for exit, with
  a ten-second default kill deadline. wait(timeout=10) is a bound, not an
  unconditional ten-second delay. No elapsed cleanup receipt exists.
* Serve: tests/test_serve.py has two server thread construction sites (:177,
  :723) using BaseServer.serve_forever's default 0.5-second shutdown poll.
  Ten helper call sites include one two-route loop, plus one direct server;
  the successful source path therefore creates twelve server lifecycles.
  Actual shutdown waits were not measured. Event.wait(2/3), thread.join(2/3)
  and urllib timeouts are deadlines that may complete early. Negative
  Event.wait(0.05) assertions protect concurrency ordering; preserve them.
* Scenario timeout fixtures deliberately contain child time.sleep(10), but
  their timeout/output-cap oracles terminate the child early. Do not sum the
  literal ten-second sleeps as measured waiting time.

## Minimal actionable improvement

In both tests/test_serve.py thread construction sites, use:

```python
thread = threading.Thread(target=server.serve_forever,
                          kwargs={"poll_interval": 0.01})
```

This changes only test-server shutdown polling. Preserve every HTTP assertion,
the 0.1-second BRIDGE_TIMEOUT, request timeout, explicit concurrency guard,
shutdown call, join deadline and server_close call. The configured polling
envelope for twelve successful lifecycles changes from approximately 6.0 to
0.12 seconds, excluding scheduling overhead. This is an unmeasured candidate;
it is not evidence of a 5.88-second historical saving.

## Source identity

Historical git-show bytes equal baseline working-tree bytes for all seven
reviewed files: tests/test_axiom_reader.py, tests/test_model_update.py,
tests/test_serve.py, tests/_bridge.py, geometry-guide/sync_axiom_reader.py,
geometry-web/model_update.py and geometry-web/runtime_version.py.
The source-path interpretation is applicable to the historical run, while the
timings remain evidence from that run rather than a new baseline measurement.
