import argparse, hashlib, json, re, zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--zip', required=True)
args = parser.parse_args()
data = open(args.zip, 'rb').read()
assert len(data) == 33653
assert hashlib.sha256(data).hexdigest() == 'd60f390e02153049812dce492c1e432e72d7f1e9c759f1bd9e29e241ce1a4d94'
observations = []
with zipfile.ZipFile(args.zip) as archive:
    manifest = json.loads(archive.read('manifest.json'))
    assert len(manifest) == 26 and len(archive.namelist()) == 27
    for name, value in manifest.items():
        payload = archive.read(name)
        assert len(payload) == value['bytes']
        assert hashlib.sha256(payload).hexdigest() == value['sha256']
    for name, counts, exit_code in [('natural', (36, 0), 0), ('cpu20', (34, 2), 1), ('restored', (36, 0), 0)]:
        receipt = json.loads(archive.read(name + '/receipt.json'))
        trace = json.loads(archive.read(name + '/trace.json'))
        stdout = archive.read(name + '/stdout').decode()
        assert json.loads(re.search(r'^P3_DIAGNOSTIC (.*)$', stdout, re.M)[1]) == trace
        assert receipt['returncode'] == exit_code
        assert (trace['passed'], trace['failed']) == counts
        second = [event for event in trace['trace']['events']
                  if event['type'] == 'pointerdown' and event.get('previous', {}).get('id') == 20][-1]
        assert second['target'] == 'DIV#' and second['eligible'] is True
        assert 'class' not in second and 'currentContext' not in second
        interval = second['time'] - second['previous']['time']
        assert (interval > 450) == (name == 'cpu20')
        observations.append({'name': name, 'counts': counts, 'exit': exit_code,
                             'target': second['target'], 'eligible': second['eligible'],
                             'observed_interval_ms': interval,
                             'browser_pid': trace['scope']['browserPid'],
                             'profile': trace['scope']['browserProfile']})
    assert len({x['browser_pid'] for x in observations}) == 3
    assert len({x['profile'] for x in observations}) == 3
print(json.dumps({'original_payloads_verified': 26, 'observations': observations,
                  'all_guard_context_viewport_excluded': False,
                  'second_target_proven_inspector': False,
                  'same_chrome_fault_recovery_verified': False,
                  'historical_unique_root_cause_proven': False,
                  'new_product_tests': 0}, ensure_ascii=False, indent=2))
