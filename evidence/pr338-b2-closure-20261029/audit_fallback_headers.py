"""Classify inactive relative-header fallbacks without compiling any product."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GIT = Path('/tmp/r02-ui1')
report = json.loads((ROOT / 'B2_CLOSURE.json').read_text())
result = {'schema': 'pr338-b2-fallback-header-audit/1', 'references': {},
          'limitation': 'This is source guard classification, not a fresh preprocessor run. '
                        'Original successful builds and unchanged source/binary inputs are the reuse evidence.'}
for ref, closure in report['source_closures'].items():
    rows = []
    if not closure['missing_quoted_includes']:
        result['references'][ref] = rows
        continue
    blobs = {}
    definitions = {}
    for path, expected in closure['files'].items():
        data = subprocess.check_output(['git', '--no-optional-locks', '-C', str(GIT), 'show', ref + ':' + path])
        assert hashlib.sha256(data).hexdigest() == expected['sha256'], path
        blobs[path] = data
        for line, raw in enumerate(data.splitlines(), 1):
            match = re.match(rb'^\s*#\s*define\s+(\w+)', raw)
            if match:
                definitions.setdefault(match[1].decode(), []).append({'path': path, 'line': line})
    for item in closure['missing_quoted_includes']:
        data = blobs[item['including']]
        pattern = rb'#ifndef\s+(\w+)\s*\r?\n\s*#include\s+"' + re.escape(item['operand'].encode()) + rb'"\s*\r?\n\s*#endif'
        matches = list(re.finditer(pattern, data))
        assert len(matches) == 1, item
        guard = matches[0].group(1).decode()
        assert guard in definitions, (item, guard)
        rows.append(dict(item, guard=guard,
                         line=data[:matches[0].start()].count(b'\n') + 1,
                         guard_definition_in_pinned_closure=definitions[guard]))
    result['references'][ref] = rows
out = ROOT / 'B2_FALLBACK_HEADERS.json'
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print('PASS: all 30 relative fallbacks are individually #ifndef guarded; corresponding guard definitions are in pinned closure')
print('Original base/F8/F9/F/M build-source identity retained; main has 0 missing quoted includes')
print('Output SHA-256:', hashlib.sha256(out.read_bytes()).hexdigest())
