"""Compile the unmodified native bridge and save its actual build receipt."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
binary = Path('/tmp/geometry-task31-bridge')
argv = ['gcc', '-std=c11', '-O2', 'geometry-web/web_bridge.c', '-lm', '-o', str(binary)]
started = time.monotonic()
result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=300)
(OUT / 'compile.stdout').write_bytes(result.stdout)
(OUT / 'compile.stderr').write_bytes(result.stderr)
receipt = {'argv': argv, 'actual_exit': result.returncode, 'seconds': time.monotonic() - started,
           'compiler': subprocess.run(['gcc', '--version'], capture_output=True, text=True).stdout,
           'bridge_sha256': hashlib.sha256(binary.read_bytes()).hexdigest() if result.returncode == 0 else None}
(OUT / 'compile-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
raise SystemExit(result.returncode)
