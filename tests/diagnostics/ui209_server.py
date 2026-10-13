#!/usr/bin/env python3
"""Reuse the archived P78 I/O observer for a one-shot, explicitly tagged objects hold.

This starts only the diagnostic server, never the P78 browser test. The executed
adaptation is archived so reviewers can verify every change to that observer.
"""
from pathlib import Path
import hashlib
import os
import sys

original = Path(__file__).with_name('p78_server.py').read_text()
source = original
replacements = {
    "'P78_SOURCE_ROOT'": "'UI209_SOURCE_ROOT'",
    "value.startswith(b'grid-trial-query ')": "getattr(local, 'hold', False) and value == b'objects\\n'",
    "self.headers.get('X-P78-Request-ID')": "self.headers.get('X-UI209-Request-ID')\n        local.hold = self.headers.get('X-UI209-Hold') == '1'",
}
for before, after in replacements.items():
    if source.count(before) != 1:
        raise RuntimeError('Server observation anchor changed: '+before)
    source = source.replace(before, after)
out = Path(sys.argv[2])
(out/'executed-server.py').write_text(source)
(out/'server-adaptation.json').write_text(__import__('json').dumps({
    'originalSha256':hashlib.sha256(original.encode()).hexdigest(),
    'executedSha256':hashlib.sha256(source.encode()).hexdigest(),
    'replacements':replacements},indent=2)+'\n')
exec(compile(source, str(out/'executed-server.py'), 'exec'))
