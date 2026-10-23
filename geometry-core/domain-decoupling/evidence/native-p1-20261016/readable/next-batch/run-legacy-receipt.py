#!/usr/bin/env python3
"""Run a fixed recipe's legacy registry regression in a private /tmp mount."""
import json
from pathlib import Path
import subprocess
import sys

recipe = Path(sys.argv[1]).resolve()
data = json.loads(recipe.read_text(encoding='utf-8'))
label = data['label']
if any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in label):
    raise RuntimeError('Unsafe receipt label')
temporary = Path('/var/tmp/geo261-baseline-a898ad6e/.git') / (label + '-tmp')
temporary.mkdir(exist_ok=False)
command = ['unshare', '--mount', '--propagation', 'private', 'bash',
           str(Path(__file__).with_name('legacy-receipt-namespace.sh')), str(temporary), str(recipe)]
sys.exit(subprocess.run(command, pass_fds=(7,)).returncode)
