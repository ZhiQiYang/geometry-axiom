"""Local re-creation of Codex's original outer launcher for the architecture refresh.

Original: evidence/geo337-train-20261024/architecture-6e50-complete/original-outer/launcher.py
(sha256 abbccdd81aff9bfa01d908c30f8e01aaac15f39fa1ffb2b725ba8d058e86ca9d).
Same flow: pin-check tool and recorder, cleaned environment, 16 MiB stack, one `df` admission
snapshot, then the tool with exactly --root/--sha/--out/--prior-source. Only the hard-coded
/workspace and /tmp paths became arguments.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import resource
import sys
import time
import traceback

parser = argparse.ArgumentParser()
parser.add_argument('--sha', required=True)
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True, help='tool output dir (must not exist)')
parser.add_argument('--outer', type=Path, required=True, help='launcher record dir (must not exist)')
parser.add_argument('--tool', type=Path, required=True)
parser.add_argument('--tool-sha256', required=True)
parser.add_argument('--cap', type=Path, required=True)
parser.add_argument('--cap-sha256', required=True)
parser.add_argument('--prior-source', required=True)
parser.add_argument('--df-path', action='append', default=[])
args = parser.parse_args()

S = args.sha
ROOT, OUT, OUTER, TOOL, CAP = args.root, args.out, args.outer, args.tool, args.cap
assert hashlib.sha256(TOOL.read_bytes()).hexdigest() == args.tool_sha256
assert hashlib.sha256(CAP.read_bytes()).hexdigest() == args.cap_sha256
assert not OUT.exists() and not OUTER.exists()
OUTER.mkdir(parents=True)
(OUTER / 'launcher.py').write_bytes(Path(__file__).read_bytes())
spec = importlib.util.spec_from_file_location('original_c387', CAP)
cap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cap)
env = dict(os.environ)
for key in ('PYTHONOPTIMIZE', 'PYTHONPATH', 'PYTHONSTARTUP', 'NODE_OPTIONS'):
    env.pop(key, None)
env.update(PYTHONDONTWRITEBYTECODE='1', LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONIOENCODING='utf-8')
soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
resource.setrlimit(resource.RLIMIT_STACK, (16777216, hard))
rec = cap.Recorder(OUTER, env, S)
result = {'source_sha': S, 'exit': None, 'started_epoch': time.time(), 'command': None}
try:
    rec.run(['df', '-B1', *args.df_path], cwd=ROOT, check=True, source_sha=S,
            source_variant='architecture source and output storage admission snapshot')
    command = [sys.executable, '-B', str(TOOL), '--root', str(ROOT), '--sha', S, '--out', str(OUT),
               '--prior-source', args.prior_source]
    result['command'] = command
    row, stdout, stderr = rec.run(
        command, cwd=ROOT, check=False, source_sha=S,
        source_variant='original three architecture judges and nine fresh historical-policy guard proofs at clean F')
    result.update(exit=row['actual_process_returncode'], original_command=row,
                  tool_sha256=hashlib.sha256(TOOL.read_bytes()).hexdigest())
except BaseException:
    result.update(exit=1, error=traceback.format_exc())
finally:
    result['ended_epoch'] = time.time()
    cap.dump(OUTER / 'RESULT.json', result)
    print(json.dumps({'source': S, 'exit': result['exit'], 'result': str(OUTER / 'RESULT.json')}), flush=True)
sys.exit(result['exit'])
