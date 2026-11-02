# #341 private readiness v2 — envelope only

This directory is new. All v1 sources,36 executions and receipts stay unchanged.
There is no geometry/build/performance CLI here and no formal B1 claim.

The immutable-input reference is `SEAL.json` with its externally recorded full
SHA256. The seal inventories all v1 files (including precise C/Rf/Rj source,
patches, complete copied headers/fixtures, exact compiler/link arguments,
objects, six executable hashes and original results), original NativeBuild and
its imported repo modules, the unchanged Python judges, original `run_logged`,
this adapter, explicit future runtime environment, compiler/interpreter and
primary loader/libc/libm identities. `FIXTURES.json` binds the four existing
recipes to nine fields, ordered counts and uncollected-tail semantics.
Kernel/machine/Python context is recorded; this is not a hermetic machine image.

Commands (use the full hash printed by seal, then held in the root receipt):

```text
python -B readiness.py seal
python -B readiness.py check --expected FULL_SEAL_SHA256
python -B readiness.py synthetic --expected FULL_SEAL_SHA256
```

`seal` and synthetic output directories refuse overwrite. `check` requires a
caller-supplied expected digest, validates the complete manifest before any
child starts, and rejects changed input bytes, size or resolved path. Reading a
locally changed sidecar is not a substitute for the externally held digest.
The environment is explicitly sealed for a future run; it does not retroactively
claim v1 had a fully inventoried pre-execution environment.

The thin `capture_logged` adapter invokes the exact original
`tests/assembly_mutation_check.py:495` function. That function writes raw stdout
and stderr directly to files, kills its process group on timeout, waits, then
records original `exit:null` and `timedOut:true`. A private module-local Popen
observer preserves the real process returncode separately (POSIX SIGKILL is
normally−9). It never overwrites original `execution.json`, changes global
subprocess.Popen, changes product source, or converts timeout into success.
The original module namespace and caller stack limit are restored in finally.
All inputs are checked again after the call; any change invalidates the attempt.

Subject20 seconds, build300 seconds and16MiB stack remain fixed. The optional
`logged_native_build` hook can be bound externally to one original NativeBuild
instance's run_build dispatch: original compile/link methods still generate
their exact flags; raw is persisted through the original run_logged with300s
before any failure is raised. This hook is not executed in v2. No claim is made
that original NativeBuild.run_build itself changed or that its historical
capture_output timeout behavior was repaired.

Only three tiny synthetic shell children are permitted by the CLI: normal0,
timeout, restored0. Each uses a40ms synthetic-only deadline; the timeout child
prints both raw markers then execs an80ms sleep. Actual returncode, timeout bit,
both exact raw streams and the original process-group record are required.
Scheduling can cause a true failure; preserve it and do not retry to obtain green.
No geometry binary is executed. Unflushed userspace output cannot be recovered.
Synthetic timing is supervision diagnostics, never a performance sample or a
product mutation kill.

Future instrumentation or binaries change the inputs and require a new seal
before their first execution. Do not edit this seal after an attempt to accept
new bytes. Formal #341 remains blocked on genuine #340 merge/final freeze and
root review. Cost/work/CPU/wall/RSS, geometry timeouts, whole14/41 controls and
restored-C remain UNRUN here.
