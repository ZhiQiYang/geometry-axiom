"""R443 (PR #443) fragment-format named withdrawals: baseline / withdrawn / restored must be 0 / 1 / 0.

Usage (repo root): python3 -B tests/diagnostics/r443_registry_withdrawals.py
Run from the repo root. Each withdrawal changes one file, runs an isolated probe
that calls main's own guards, restores the exact bytes and re-runs the probe.
"""
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path.cwd()
MAIN = 'e0db7e478f15df4a90ea130ad17d74406db75586'

PROBE_REG = r'''
import sys; sys.path.insert(0, "tests")
import run_all
problems = run_all.check_registry(allow_pending=True)
if problems:
    print("\n".join(problems)); sys.exit(1)
print("registry ok")
'''
PROBE_LEGACY = r'''
import sys; sys.path.insert(0, "tests")
from pathlib import Path
import native_registry as R
try:
    R.load_registry(Path("."), allow_pending=True)
    print(R._verify_legacy_catalog(Path("."), "%s"))
except ValueError as exc:
    print(exc); sys.exit(1)
''' % MAIN


def run(probe):
    r = subprocess.run([sys.executable, '-B', '-c', probe], capture_output=True, text=True, timeout=600)
    return r.returncode, (r.stdout + r.stderr).strip()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))


FACE = 'tests/suites.d/node__face_length_overlay.json'
EXEC = 'tests/registry-evidence/native-legacy-execution.json'
LEGACY = 'tests/registry-evidence/native-legacy.json'
OLD = 'tests/suites.d/node__face_paint_scheduler.json'
SETTLE = 'tests/suites.d/node__cdp_settle.json'


def w_a():  # (a) drop one new suite's fragment registration
    return {FACE: None}


def w_b1():  # (b) new suite claims a legacy order without being sealed
    row = load(FACE); row['order'] = 'legacy/000999'
    row['expected'] = {'count': 7, 'mode': 'count', 'unit': 'node test'}  # isolate the order claim
    return {FACE: canonical(row)}


def w_b2():  # (b) seal the new suite into the frozen legacy execution catalog
    row = load(FACE); row['order'] = 'legacy/000999'
    row['expected'] = {'count': 7, 'mode': 'count', 'unit': 'node test'}
    cat = load(EXEC)
    cat['suites'][row['name']] = {k: row[k] for k in ('order', 'execution', 'files', 'expected')}
    return {FACE: canonical(row), EXEC: canonical(cat)}


def w_b3():  # (b) admit the new suite into the historical cost catalog
    cat = load(LEGACY)
    src = next(s for s in cat['sources'] if s['kind'] == 'historical-added')
    src['suites'] = sorted(set(src['suites']) | {'node:face_length_overlay'})
    raw = (ROOT / LEGACY).read_bytes()
    text = json.dumps(cat, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    return {LEGACY: text.encode('utf-8')}


def w_b4():  # (b) change an existing suite's sealed execution declaration
    row = load(OLD); row['execution']['extra_env'] = {'GEOMETRY_R443_PROBE': '1'}
    return {OLD: canonical(row)}


def w_c():  # (c) drop an existing sealed suite
    return {SETTLE: None}


CASES = [
    ('R443F_DROP_NEW_FRAGMENT', w_a, PROBE_REG, 'tests/test_face_length_overlay.js 沒有登記在 tests/suites.d'),
    ('R443F_NEW_SUITE_CLAIMS_LEGACY_ORDER', w_b1, PROBE_LEGACY,
     'R386_NATIVE_LEGACY_EXECUTION_PIN: node:face_length_overlay claims a legacy order but is not sealed'),
    ('R443F_SEAL_NEW_SUITE_INTO_LEGACY_EXECUTION', w_b2, PROBE_LEGACY,
     'R386_NATIVE_LEGACY_EXECUTION_CATALOG_IS_IMMUTABLE'),
    ('R443F_ADMIT_NEW_SUITE_INTO_HISTORICAL_COSTS', w_b3, PROBE_LEGACY, 'R386_NATIVE_LEGACY_CATALOG_'),
    ('R443F_CHANGE_OLD_SUITE_EXECUTION', w_b4, PROBE_LEGACY,
     'R386_NATIVE_LEGACY_EXECUTION_PIN: node:face_paint_scheduler differs from its sealed declaration in execution'),
    ('R443F_DROP_EXISTING_SUITE', w_c, PROBE_LEGACY,
     "R386_NATIVE_LEGACY_EXECUTION_PIN: sealed suites missing (COVERAGE) ['node:cdp_settle']"),
]

ok = True
for name, make, probe, marker in CASES:
    changes = make()
    saved = {rel: (ROOT / rel).read_bytes() for rel in changes}
    before = {rel: hashlib.sha256(b).hexdigest() for rel, b in saved.items()}
    base_code, _ = run(probe)
    try:
        for rel, data in changes.items():
            if data is None:
                (ROOT / rel).unlink()
            else:
                (ROOT / rel).write_bytes(data)
        mut_code, mut_out = run(probe)
    finally:
        for rel, data in saved.items():
            (ROOT / rel).write_bytes(data)
    after = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in saved}
    rest_code, _ = run(probe)
    hit = marker in mut_out
    good = (base_code, mut_code, rest_code) == (0, 1, 0) and hit and before == after
    ok &= good
    line = next((l for l in mut_out.splitlines() if marker in l), mut_out.splitlines()[-1] if mut_out else '')
    print('%s %d/%d/%d marker=%s restored_bytes=%s :: %s' % (
        name, base_code, mut_code, rest_code, hit, before == after, line[:220]))
print('ALL 0/1/0' if ok else 'FAILED')
sys.exit(0 if ok else 1)
