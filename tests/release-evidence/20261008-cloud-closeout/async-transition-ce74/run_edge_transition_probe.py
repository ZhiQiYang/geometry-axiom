"""Run only after the integration owner grants the exclusive browser slot."""
import datetime
import json
import pathlib
import subprocess
import sys

base = pathlib.Path(__file__).resolve().parent
label = sys.argv[1]
if pathlib.Path(label).name != label or label in ['.', '..']:
    raise SystemExit('Use a new single-directory evidence label')
for suffix in ['', '.stdout', '.stderr', '.command.json']:
    if (base/(label+suffix)).exists():
        raise SystemExit('Refusing to overwrite existing evidence: '+label+suffix)
cmd = [sys.executable, str(base/'edge_transition_probe.py'), '--out', str(base/label), *sys.argv[2:]]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (base/(label+'.stdout')).open('w') as stdout, (base/(label+'.stderr')).open('w') as stderr:
    result = subprocess.run(cmd, stdout=stdout, stderr=stderr, text=True)
(base/(label+'.command.json')).write_text(json.dumps({'startedUtc':started,
    'finishedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'argv':cmd, 'cwd':str(pathlib.Path.cwd()), 'exitCode':result.returncode}, indent=2)+'\n')
print((base/(label+'.stdout')).read_text(), end='')
print((base/(label+'.stderr')).read_text(), end='', file=sys.stderr)
sys.exit(result.returncode)
