import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

out = Path('/tmp/geometry-pr182-review/gate-cli')
out.mkdir(parents=True, exist_ok=True)
command = [sys.executable, 'tests/section_profile_mutation_check.py', '--only', 'SPM41', '--group', 'native',
           '--receipt', str(out/'mutations.json'), '--logs', str(out/'logs')]
start = time.monotonic()
run = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
(out/'console.log').write_bytes(run.stdout)
receipt = {'command': command, 'exit': run.returncode, 'seconds': time.monotonic()-start,
           'head': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
           'status': subprocess.check_output(['git','status','--porcelain'], text=True),
           'gate_sha256': hashlib.sha256(Path('tests/section_profile_mutation_check.py').read_bytes()).hexdigest(),
           'console_sha256': hashlib.sha256(run.stdout).hexdigest()}
(out/'receipt.json').write_text(json.dumps(receipt, indent=2))
print(run.stdout.decode())
assert run.returncode == 0
