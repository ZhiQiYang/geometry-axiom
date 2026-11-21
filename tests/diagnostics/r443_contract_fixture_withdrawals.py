#!/usr/bin/env python3
"""R443 named withdrawals for the synthetic-CI fixture isolation (0/1/0).

Review 7070051854 item 1: the two synthetic CI tests of
native_registry_contract_check.py must run in a temporary fixture that holds
only historical sources plus the CI source each test creates itself.  Each
withdrawal below must be green at baseline, red *at its designated assertion*
when withdrawn, and green again when restored; the checkout bytes must not
change.  A final positive check shows that the production full-table
verify_ci_sources() on the real checkout still reaches every real CI original
(the isolation is fixture-only, nobody stops verifying the real receipts).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / 'tests/diagnostics/native_registry_contract_check.py'
sys.path.insert(0, str(ROOT / 'tests'))
import native_registry as registry  # noqa: E402

SYNTHETIC_TESTS = ('test_cost_import_requires_original_archive_and_run_job_identity',
                   'test_live_authentication_rejects_self_filled_or_changed_receipt_bytes')
REAL_CI_KEYERROR = re.compile(r"KeyError: '/actions/runs/(\d+)/attempts/1'")
# withdrawal -> (designated marker each synthetic test must fail at, real run required)
WITHDRAWALS = {
    'R443_NO_ISOLATION': (REAL_CI_KEYERROR, True),
    'R443_LEAK_ONE_CI_SOURCE': (REAL_CI_KEYERROR, True),
    'R443_TAMPER_SYNTHETIC_ZIP': (re.compile(r'R386_NATIVE_LIVE_CI_BYTES'), False),
}


def checkout_state():
    status = subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--untracked-files=all'])
    digest = hashlib.sha256()
    for folder in (registry.SUITES, registry.COSTS, registry.SOURCES):
        for path in sorted((ROOT / folder).glob('*.json')):
            digest.update(path.name.encode() + b'\0' + path.read_bytes() + b'\0')
    return status, digest.hexdigest()


def real_ci_runs():
    runs = {}
    for path in sorted((ROOT / registry.SOURCES).glob('*.json')):
        data = json.loads(path.read_bytes())
        if data.get('schema') == 'geometry-native-ci-receipt/1':
            runs[path.stem] = data['run']['id']
    return runs


def run(withdrawal=None):
    command = [sys.executable, '-B', str(CHECK)] + (['--withdraw-isolation', withdrawal] if withdrawal else [])
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=300)
    text = result.stdout + result.stderr
    ran = re.search(r'^Ran (\d+) tests?', text, re.M)
    blocks = re.split(r'^={20,}$', text, flags=re.M)
    failures = {}
    for block in blocks[1:]:
        head = re.match(r'\s*(ERROR|FAIL): (\w+)', block)
        if head:
            failures[head.group(2)] = block
    return result.returncode, int(ran.group(1)) if ran else None, failures, text


def judge(name, code, ran, failures):
    if ran != 22:
        return 3, 'ran=%r' % ran
    if not failures:
        return (0, 'green') if code == 0 else (3, 'exit %d without failures' % code)
    marker, needs_real = WITHDRAWALS[name]
    if set(failures) != set(SYNTHETIC_TESTS):
        return 3, 'unexpected failing set %r' % sorted(failures)
    real = set(real_ci_runs().values())
    for test, block in failures.items():
        found = marker.search(block)
        if not found:
            return 3, '%s red at a different assertion' % test
        if needs_real and int(found.group(1)) not in real:
            return 3, '%s KeyError names non-real run %s' % (test, found.group(1))
    return 1, 'red at %s' % marker.pattern


def positive_full_table_check():
    """On the real checkout, the unmodified full-table verifier still walks
    every real CI original.  The fetch only echoes each receipt's own record
    so the count can be observed offline; it is not an authentication (CI's
    registry contract job authenticates them online against GitHub)."""
    runs = real_ci_runs()
    costs = {json.loads(p.read_bytes())['source_sha256'] for p in (ROOT / registry.COSTS).glob('*.json')
             if json.loads(p.read_bytes())['kind'] == 'ci-report'}
    assert costs == set(runs), ('R443_POSITIVE_REAL_CI_COSTS_AND_SOURCES', sorted(costs), sorted(runs))
    assert len(runs) >= 2, 'R443_POSITIVE_REAL_CI_ORIGINALS_PRESENT'
    import base64
    served = {}
    for digest in runs:
        source = registry._source(ROOT, digest)
        run, job, artifact = source['run'], source['job'], source['artifact']
        served['/actions/runs/%d/attempts/%d' % (run['id'], run['run_attempt'])] = json.dumps(run).encode()
        served['/actions/jobs/%d' % job['id']] = json.dumps(job).encode()
        served['/actions/artifacts/%d' % artifact['id']] = json.dumps(artifact).encode()
        served['/git/commits/' + source['checkout']['sha']] = json.dumps(source['checkout']).encode()
        served['/actions/artifacts/%d/zip' % artifact['id']] = base64.b64decode(source['archive_base64'])
    asked = []

    def fetch(endpoint):
        asked.append(endpoint)
        return served[endpoint]

    trusted = registry._legacy_catalog(ROOT)['base_sha']
    result = registry.verify_ci_sources(ROOT, fetch=fetch, trusted_ref=trusted)
    asked_runs = {int(m.group(1)) for m in map(re.compile(r'/actions/runs/(\d+)/attempts/').match, asked) if m}
    assert result['verified_online'] == len(runs), ('R443_POSITIVE_FULL_TABLE_COUNT', result)
    assert asked_runs == set(runs.values()), ('R443_POSITIVE_FULL_TABLE_RUNS', sorted(asked_runs))
    return {'real_ci_originals': len(runs), 'runs': sorted(asked_runs),
            'verified_online': result['verified_online'], 'trusted_base': trusted}


def main():
    before = checkout_state()
    report, bad = {}, False
    for name in WITHDRAWALS:
        phases = []
        for withdrawal in (None, name, None):
            code, ran, failures, text = run(withdrawal)
            verdict, detail = judge(name, code, ran, failures)
            phases.append(verdict)
            print('%s %s: %d (%s)' % (name, 'withdrawn' if withdrawal else 'baseline/restored', verdict, detail))
        report[name] = phases
        bad |= phases != [0, 1, 0]
    after = checkout_state()
    print('checkout unchanged:', before == after)
    bad |= before != after
    positive = positive_full_table_check()
    print('positive full-table check on real checkout:', json.dumps(positive, sort_keys=True))
    print(json.dumps(report, sort_keys=True))
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
