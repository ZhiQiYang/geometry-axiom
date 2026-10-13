import argparse, hashlib, json, zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--zip', required=True)
args = parser.parse_args()
data = open(args.zip, 'rb').read()
assert len(data) == 222289
assert hashlib.sha256(data).hexdigest() == '3b8be9cc3961f58c7324d9076944f08a63b5c88cd971864014a54b1677a44993'
with zipfile.ZipFile(args.zip) as archive:
    manifest = json.loads(archive.read('manifest.json'))
    assert len(manifest) == 32 and len(archive.namelist()) == 33
    for name, value in manifest.items():
        payload = archive.read(name)
        assert len(payload) == value['bytes']
        assert hashlib.sha256(payload).hexdigest() == value['sha256']
    driver = archive.read('driver.cjs').decode()
    assert "before=(await apiRequest('dump')).text,history=ReferenceWorkspace.history.undo.length" in driver
    assert "dumpUnchanged:(await apiRequest('dump')).text===before" in driver
    assert 'historyUnchanged:ReferenceWorkspace.history.undo.length===history' in driver
    observations = []
    exits = {}
    for name, expected in [('natural', 0), ('old-refresh', 1), ('candidate-refresh', 0), ('revert-refresh', 1), ('restore-refresh', 0)]:
        receipt = json.loads(archive.read(name + '/receipt.json'))
        assert receipt['returncode'] == expected
        exits[name] = receipt['returncode']
        if name != 'natural':
            refresh = json.loads(archive.read(name + '/result.json'))['refresh']
            assert refresh['nodeReplaced'] is True and refresh['hit'] is False
            assert refresh['dumpUnchanged'] is True and refresh['historyUnchanged'] is True
            assert 'scrollTop' not in refresh
            observations.append({'name': name, 'fields': sorted(refresh), 'scope': 'recorded text equality and undo length equality only'})
print(json.dumps({'zip_bytes': len(data), 'payloads_verified': 32, 'historical_exits': exits,
                  'controlled_observations': observations, 'new_product_tests': 0,
                  'complete_world_history_zero_write_proven': False,
                  'scroll_top_measured': False, 'wrapper_and_census_delivered': False}, ensure_ascii=False, indent=2))
