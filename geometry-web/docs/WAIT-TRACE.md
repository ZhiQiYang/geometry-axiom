# #209 opt-in wait diagnostics (P-107 / board task 13)

Only `GEOMETRY_WAIT_TRACE=1` enables tracing. Supply the isolated test service's
`GEOMETRY_FEEDBACK_DIR`; events append to `wait-trace.jsonl`. Without that directory
there is no output. No default feedback location is used, avoiding user reports.
An unwritable sink does not change command results or trigger a retry.

Each event has a diagnostic UUID distinct from the business request/receipt ID,
route, command, process/thread, wall time and monotonic time. Stages include
source_lock, receipt_lock, bridge_lock, stdin_write, stdin_flush, response_queue,
http_write and request begin/end. Lock begin events report the holder's request,
command/thread and elapsed hold time observed when waiting begins; completion
events report acquisition duration and success. Hold time is an observation,
not a claim that the same holder persisted throughout the wait. Reentrant locks
retain the outer acquisition's identity. Durations use one process's monotonic
clock; do not subtract browser and server timestamps from each other.

The canvas CDP harness records `firstTransportFailure` in both completed and fatal
CDP_RESULT records. It retains the first same-origin /api or Fetch/XHR network
failure or HTTP5xx, including posted request, step and timestamps; later failures cannot replace
it. API-level geometric rejection and errors blocked before fetch are not network
failures. HTTP timing covers headers and body, including send_error and broken
headers, and rethrows the original exception. This diagnostic does not alter
assertions, waits, retries or deadlines.

## WSL train workflow change (shared file; not run under WSL here)

`.github/workflows/integration-tests.yml` clears an inherited trace flag, then
enables it only for the canvas browser job on a Microsoft WSL kernel, **before**
starting start_local.py/serve.py. The cloud shell test substitutes Linux/WSL
kernel strings across canvas/grid/space; this is not WSL execution.
Nonstandard WSL kernels without the Microsoft marker require an explicit
local runner override. Native and other browser jobs do not enable tracing.

The active local WSL runner is external to this cloud checkout. Historical
runner copies under `tests/release-evidence/` are not modified. Its archived
ci_job.py executes the checked-out workflow, so the shared workflow is the
reviewable insertion point. If the active train does not execute that step,
its owner must apply the equivalent per-job environment conditional:

```python
env.pop('GEOMETRY_WAIT_TRACE', None)
if a.job == 'canvas':
    env['GEOMETRY_WAIT_TRACE'] = '1'
```

This must affect the **serve.py process**, not merely the later Node command.
Keep the existing private GEOMETRY_FEEDBACK_DIR unchanged and archive its
wait-trace.jsonl together with CDP_RESULT/stdout. All other jobs must leave the
variable unset. Add this key to the runner's recorded effective environment.
The active runner update, canvas output under WSL, and formal seven jobs remain
unverified here; the local train owner must apply and report that shared change.

GEO-219: 無新入口. No core C change or new core mutation coverage.
