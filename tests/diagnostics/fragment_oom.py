"""Run against a bridge with a one-shot allocation fault at the fragment allocator."""
import json, os, pathlib, resource, subprocess, sys, tempfile
if not __debug__:
    raise RuntimeError('Verification requires assertions; Python optimization mode is not supported')
root = pathlib.Path(__file__).resolve().parents[2]
source = (root / '_ax_r13_anchor_follows.scene').read_text().replace('guide 1 5 u spec:', 'guide 1 5 v spec:')
with tempfile.TemporaryDirectory() as tmp:
    before = pathlib.Path(tmp) / 'before.scene'
    after = pathlib.Path(tmp) / 'after.scene'
    before.write_text(source.replace('apply-proj 5 c1', ''))
    after.write_text(source)
    def bounds():
        _, hard = resource.getrlimit(resource.RLIMIT_STACK)
        resource.setrlimit(resource.RLIMIT_STACK, (16384*1024, hard))
    for fail_at in (1, 2):
        env = dict(os.environ, FRAGMENT_OOM_AT=str(fail_at))
        result = subprocess.run([sys.argv[1]], input=f'loadfile {before}\ndump\nloadfile {after}\ndump\n'.encode(), capture_output=True, env=env, preexec_fn=bounds, timeout=30)
        print(json.dumps({'fail_at':fail_at,'exit':result.returncode,'stdout':result.stdout.decode(),'stderr':result.stderr.decode()},ensure_ascii=False))
        assert result.returncode == 0, result.stderr
        replies = [json.loads(line) for line in result.stdout.splitlines()]
        assert len(replies) == 4 and replies[0]['ok'] and replies[1]['ok'] and replies[3]['ok'], replies
        assert replies[2]['ok'] is False, 'OOM must reject the transaction instead of selecting the other fragment'
        assert replies[1]['text'] == replies[3]['text'], 'OOM must preserve the complete World dump'
        assert replies[1]['definition_sha256'] == replies[3]['definition_sha256'], 'OOM must preserve the World definition fingerprint'
print('PASS: either fragment allocation failure rejects and preserves the exact World')
