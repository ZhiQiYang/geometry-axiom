"""Linux 8 MiB regression; supply separately built core and bridge paths."""
import json, pathlib, resource, subprocess, sys
root = pathlib.Path(__file__).resolve().parents[2]
def set_stack_soft(limit):
    _, hard = resource.getrlimit(resource.RLIMIT_STACK)
    resource.setrlimit(resource.RLIMIT_STACK, (limit, hard))
_, hard = resource.getrlimit(resource.RLIMIT_STACK)
if hard != resource.RLIM_INFINITY and hard < 16384 * 1024:
    print('ENVIRONMENT BLOCKED: inherited hard stack limit is below 16 MiB', file=sys.stderr)
    sys.exit(2)
def bounded():
    set_stack_soft(8192 * 1024)
def core_bounds():
    set_stack_soft(16384 * 1024)
core, bridge = sys.argv[1:]
scene = root / '_ax_r13_anchor_follows.scene'
result = subprocess.run([core, '--scene', str(scene), '--no-window', '--out', '/tmp/fragment-stack.svg'], cwd=root, capture_output=True, preexec_fn=core_bounds, timeout=30)
assert result.returncode == 0, f'core reference-fragment exit {result.returncode}: {result.stderr!r}'
result = subprocess.run([bridge], input=f'loadfile {scene}\ndump\n'.encode(), cwd=root, capture_output=True, preexec_fn=bounded, timeout=30)
assert result.returncode == 0, f'bridge reference-fragment exit {result.returncode}: {result.stderr!r}'
replies = [json.loads(line) for line in result.stdout.splitlines()]
assert len(replies) == 2 and all(r.get('ok') is True for r in replies), replies
assert replies[1]['definition_sha256'] == '42011d47a987a2cb035943b3c2602462ed118e93074202ef015472a608966d07', replies[1]
assert 'guide 1 5 u spec:掛線位置\n' in replies[1]['text'], replies[1]
print('PASS: core at 16 MiB and bridge at 8 MiB preserve the exact expected definition')
