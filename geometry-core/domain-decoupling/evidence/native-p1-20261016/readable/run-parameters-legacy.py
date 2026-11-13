#!/usr/bin/env python3
"""Keep same-SHA legacy registry builds in their own nested mount namespace."""
from pathlib import Path
import subprocess
import sys

script = Path(__file__).with_name('parameters-legacy-namespace.sh')
sys.exit(subprocess.run(['bash', str(script)], pass_fds=(7,)).returncode)
