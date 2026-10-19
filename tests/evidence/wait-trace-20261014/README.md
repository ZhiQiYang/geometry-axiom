# #209 wait trace cloud evidence

Product tested head: 4039ccc4e665448e4a20fd01c7483f3e1bf06f1e.
See native.json for the actual full parent exit and duration; raw stdout/stderr
and all native suite artifacts are preserved. Archive members have byte/SHA
inventory; binary hashes/sidecars are supplied without executable bytes.

mutations.json records actual OS exits: fixed Python/Node green; default-on,
overwrite-first and remove-bridge-hook each red, restoration green. These are
diagnostic/product hooks, not new C mutants and not tests/mutate.py execution.
initial-missing-module.log is an earlier 3-error test-first log; its shell ended
with cat and did not retain the test OS exit, so it is not a parent exit receipt.

smoke.json and smoke-trace.jsonl came from a real isolated fresh bridge service.
The unit HTTP comparison uses a mocked native process with real HTTP sockets.
The Node observer unit uses controlled CDP messages, not a full browser run.
Unverified: active external WSL runner deployment, formal seven jobs, complete
canvas and the historical timeout cause. This is cloud evidence, not WSL.
Source files were temporarily changed only during pre-native mutation controls,
then restored. An assertion line was briefly added/reverted while the native
reader suite was running; no commit or lasting change resulted. No continuous
source-monitoring claim is made; native head before/after is identical.
