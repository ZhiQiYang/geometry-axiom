"""Independently re-check a #352 browser mutation receipt against the exact run inputs.

The runner's own exit code stays the primary verdict. This check refuses a receipt
that is incomplete, belongs to another head/manifest/binary, or whose mutants were
not killed by one of the manifest's named assertions with a green restored control.
It writes summary.json next to the receipt and exits 1 on any problem.
"""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError as error:
        return 'unreadable: ' + str(error)


def case_ids(run):
    return [row.get('case', row.get('id')) for row in run.get('cases', [])]


def check_run(problems, label, run, expected_cases, case_filter, want_green):
    if not isinstance(run, dict):
        problems.append(label + ': missing run')
        return
    if run.get('complete') is not True:
        problems.append(label + ': incomplete')
    if run.get('errors'):
        problems.append(label + ': errors ' + json.dumps(run['errors'], ensure_ascii=False)[:500])
    if run.get('caseFilter') != case_filter:
        problems.append(label + ': caseFilter %r, expected %r' % (run.get('caseFilter'), case_filter))
    if sorted(case_ids(run)) != sorted(expected_cases):
        problems.append(label + ': cases %s, expected %s' % (case_ids(run), expected_cases))
    footer = run.get('footer') or [{}]
    if len(run.get('footer') or []) != 1 or footer[0].get('completed') is not True:
        problems.append(label + ': CDP footer is not a single completed result')
    for cleanup in run.get('cleanup', []):
        if cleanup.get('completed') is not True or cleanup.get('liveMembers') != 0:
            problems.append(label + ': cleanup incomplete')
    if want_green:
        if run.get('green') is not True or run.get('exitCode') != 0 or run.get('assertions'):
            problems.append(label + ': not green')
    elif run.get('green') is not False or run.get('exitCode') != 1:
        problems.append(label + ': mutant is not a completed red run')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--bridge', type=Path, required=True)
    parser.add_argument('--model-base', type=Path)
    parser.add_argument('--summary', type=Path, required=True)
    options = parser.parse_args()
    problems = []
    summary = {'schema': 'geometry-r11-mutation-receipt-check/1', 'receipt': str(options.receipt),
               'expectedHead': options.head, 'mutations': []}
    try:
        receipt = json.loads(options.receipt.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        receipt = {}
        problems.append('receipt unreadable: ' + str(error))
    manifest = json.loads(options.manifest.read_text(encoding='utf-8'))
    expected = {
        'schema': 'geometry-browser-mutation-receipt/1',
        'suite': manifest['suite'],
        'manifestHash': digest(options.manifest),
        'head': options.head,
        'bridgeHash': digest(options.bridge),
        'status': 'passed',
    }
    if options.model_base:
        expected['modelBaseHash'] = digest(options.model_base)
    for key, value in expected.items():
        if receipt.get(key) != value:
            problems.append('%s: %r, expected %r' % (key, receipt.get(key), value))
    summary.update({key: receipt.get(key) for key in ['status', 'head', 'manifestHash', 'bridgeHash',
                                                      'modelBaseHash', 'sourceHash', 'reason']})
    if receipt:
        check_run(problems, 'baseline', receipt.get('baseline'), manifest['cases'], None, True)
        summary['baseline'] = {key: (receipt.get('baseline') or {}).get(key)
                               for key in ['complete', 'green', 'exitCode', 'elapsedSeconds']}
        summary['baseline']['cases'] = len(case_ids(receipt.get('baseline') or {}))
        rows = receipt.get('mutations', [])
        if [row.get('id') for row in rows] != [m['id'] for m in manifest['mutations']]:
            problems.append('mutation ids %s, expected %s' % ([row.get('id') for row in rows],
                                                             [m['id'] for m in manifest['mutations']]))
        for mutation, row in zip(manifest['mutations'], rows):
            label = mutation['id']
            if row.get('status') != 'killed':
                problems.append(label + ': status ' + str(row.get('status')) + ' ' + str(row.get('reason', '')))
            changes = row.get('changes', [])
            if len(changes) != len(mutation['changes']) or any(c.get('beforeHash') == c.get('afterHash') for c in changes):
                problems.append(label + ': mutation site was not changed exactly as declared')
            check_run(problems, label + ' mutant', row.get('mutant'), [mutation['case']], mutation['case'], False)
            check_run(problems, label + ' restored', row.get('restored'), [mutation['case']], mutation['case'], True)
            killed = sorted(set((row.get('mutant') or {}).get('assertions', [])) & set(mutation['assertions']))
            if not killed:
                problems.append(label + ': no named manifest assertion failed in the mutant')
            summary['mutations'].append({
                'id': label, 'case': mutation['case'], 'status': row.get('status'),
                'namedKillingAssertions': killed,
                'mutantElapsedSeconds': (row.get('mutant') or {}).get('elapsedSeconds'),
                'restoredElapsedSeconds': (row.get('restored') or {}).get('elapsedSeconds'),
                'restoredGreen': (row.get('restored') or {}).get('green')})
    summary['problems'] = problems
    summary['verified'] = not problems
    options.summary.parent.mkdir(parents=True, exist_ok=True)
    options.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'verified': not problems, 'problems': problems}, ensure_ascii=False, indent=2))
    return 0 if not problems else 1


if __name__ == '__main__':
    raise SystemExit(main())
