"""O467 browser inventory/preflight and R16's original 0/1/0 CDP runner.

The 16 R16 rows use the existing P1231 result contract. Three PF4A/R03 rows
remain explicit plans against original full-section/golden judges, never a
fabricated generic per-case protocol. --preflight is not browser evidence.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
from mutation_fragments import _object, _safe


def original():
    path = ROOT / 'tests/diagnostics/r16_height_mutations.py'
    spec = importlib.util.spec_from_file_location('o467_r16_original', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def definitions(root):
    root = Path(root).resolve()
    directory = root / 'tests/browser-mutants.d'
    _safe(root, directory)
    rows, identifiers = [], set()
    for path in sorted(directory.iterdir()):
        _safe(root, path)
        if not path.is_file() or path.suffix != '.json':
            raise ValueError('O467_BROWSER_FRAGMENT_PATH')
        row = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_object)
        required = {'id', 'case', 'assertions', 'meaning', 'changes',
                    'beforeBytes', 'beforeSha256', 'afterBytes', 'afterSha256'}
        if (type(row) is not dict or set(row) - {'legacyPlan'} != required
                or path.name != row['id'] + '.json' or row['id'].casefold() in identifiers
                or len(row['changes']) != 1 or not row['assertions']):
            raise ValueError('O467_BROWSER_FRAGMENT_SHAPE: ' + path.name)
        identifiers.add(row['id'].casefold())
        change = row['changes'][0]
        if set(change) != {'file', 'before', 'after'}:
            raise ValueError('O467_BROWSER_CHANGE_SHAPE')
        rel = change['file']
        if ('\\' in rel or ':' in rel or rel.startswith('/')
                or any(part in ('', '.', '..') for part in rel.split('/'))):
            raise ValueError('O467_BROWSER_SOURCE_PATH')
        target = root / rel
        _safe(root, target)
        raw = target.read_bytes()
        if raw.count(change['before'].encode()) != 1 or change['before'] == change['after']:
            raise ValueError('O467_BROWSER_UNIQUE_ANCHOR: ' + row['id'])
        changed = raw.replace(change['before'].encode(), change['after'].encode(), 1)
        if ((len(raw), hashlib.sha256(raw).hexdigest(), len(changed), hashlib.sha256(changed).hexdigest())
                != tuple(row[key] for key in ('beforeBytes', 'beforeSha256', 'afterBytes', 'afterSha256'))):
            raise ValueError('O467_BROWSER_SOURCE_PIN: ' + row['id'])
        rows.append(row)
    return rows


def main():
    module = original()
    rows = definitions(ROOT)
    syntax = module.syntax_preflight(ROOT, rows, 'node')
    if '--preflight' in sys.argv:
        report = {'schema': 'o467-browser-preflight/1', 'browserExecuted': False,
            'baseHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'counts': {'r16Executable': len([row for row in rows if row['case'] == 'P1231']),
                       'legacyPlans': len([row for row in rows if 'legacyPlan' in row])},
            'syntax': syntax, 'rows': rows}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    # Keep the original runner's fixed-head, original baseline, named failure,
    # 900s ceiling, cleanup and exact restoration rules unchanged.
    r16 = [row for row in rows if row['case'] == 'P1231']
    module.definitions = lambda root: [row for row in definitions(root) if row['case'] == 'P1231']
    old_manifest = module.manifest_for
    def manifest(root, mutations):
        result = old_manifest(root, mutations)
        result['inputs'] += ['tests/diagnostics/o467_browser_mutations.py', 'tests/mutation_fragments.py',
            *['tests/browser-mutants.d/' + row['id'] + '.json' for row in r16]]
        return result
    module.manifest_for = manifest
    module.BASE_SHA = '48d5f3887e8cb8d222307db62dbdea287fda8442'
    return module.main()


if __name__ == '__main__':
    raise SystemExit(main())
