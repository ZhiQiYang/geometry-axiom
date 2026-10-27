from pathlib import Path
import hashlib
import json
import tarfile

D = Path(__file__).parent
def sha(b):
    return hashlib.sha256(b).hexdigest()
def load(n):
    return json.loads((D/n/'stdout.bin').read_bytes())

receipt = load('geo288-f13-native')
assert receipt['sha'] == '13d02c1db7022145a52ee063286a558e595eb212'
assert receipt['exit_code'] == 0
step = receipt['steps'][1]['result']
assert step['actual_process_returncode'] == step['exit_code'] == 0
assert not step['watchdog_expired'] and not receipt['over_ci_timeout']
selected = ['run_all-logs/c_integrity.log', 'run_all-logs/core_run_tests.log',
            'run_all-logs/py_test_reference_contract.json',
            'run_all-logs/py_test_reference_contract.unittest.log', 'steps/01.stdout']
out = D/'f13-selected-originals'
out.mkdir(exist_ok=True)
members = []
with tarfile.open(D/'geo288-f13-native-archive/stdout.bin', 'r:gz') as archive:
    for path in selected:
        member = archive.getmember('job/'+path)
        assert member.isfile()
        raw = archive.extractfile(member).read()
        expected = receipt['files'][path]
        assert len(raw) == expected['bytes'] and sha(raw) == expected['sha256'], path
        target = out / path.replace('/', '__')
        target.write_bytes(raw)
        members.append({'archive_path': member.name, 'saved_path': str(target.relative_to(D)),
                        'bytes': len(raw), 'sha256': sha(raw), 'receipt_hash_matches': True})
ref_result = json.loads((out/'run_all-logs__py_test_reference_contract.json').read_bytes())
core = (out/'run_all-logs__c_integrity.log').read_text()
scene = (out/'run_all-logs__core_run_tests.log').read_text()
summary = (out/'steps__01.stdout').read_text()
assert '432/432 integrity checks passed' in core
for name in ['_ax_r7_notch_disconnected.scene', '_ax_r7_ridge_crossing.scene', '_ax_r7_ridge_strip.scene']:
    row = next(line for line in scene.splitlines() if line.startswith(name))
    assert 'PASS' in row, row

withdrawal = load('original-withdrawal-results')
for phase, expected in [('removed',1), ('restored',0)]:
    assert all(v['exit'] == expected for v in withdrawal[phase]['runs'].values())
    text = (D/f'withdrawal-{phase}-scenes/stdout.bin').read_text()
    for name in ['_ax_r7_notch_disconnected.scene', '_ax_r7_ridge_crossing.scene', '_ax_r7_ridge_strip.scene']:
        row = next(line for line in text.splitlines() if line.startswith(name))
        assert ('FAIL' if phase == 'removed' else 'PASS') in row, row
removed_native = (D/'withdrawal-removed-native/stdout.bin').read_text()
assert 'counterexample_A < 0' in removed_native and 'counterexample_B > 0' in removed_native
removed_bridge = (D/'withdrawal-removed-bridge/stdout.bin').read_text()
assert 'FAIL: test_rect_outline_counterexample_A_' in removed_bridge
assert 'FAIL: test_rect_outline_counterexample_B_' in removed_bridge

probes = {}
for phase in ['before','after']:
    p = load('original-'+phase+'-probe')
    cases = {c['name']: c['commands'] for c in p['cases']}
    a, b = cases['A'], cases['B']
    assert a[1]['input'] == 'line surface 1 origin 0 0 0 u +x v +y outline 0,0 100,0 100,100 60,100 60,40 40,40 40,100 0,100'
    assert a[2]['input'] == 'line column 1 at 30 50 size 40 30 z 0 100'
    assert b[1]['input'] == 'line surface 1 origin 0 0 0 u +x v +y outline 0,0 100,0 100,50 60,50 60,90 40,90 40,50 0,50'
    assert b[2]['input'] == 'line column 1 at 20 70 size 60 10 z 0 100'
    assert a[3]['output']['text'] == a[6]['output']['text']
    assert not a[5]['output']['ok']
    if phase == 'before':
        assert a[4]['output']['items'] == [{'id':1,'type':'column','cls':'hole','rect':[30,50,70,80]}]
        assert b[4]['output']['items'] == [] and not b[5]['output']['ok']
    else:
        assert not a[4]['output']['ok'] and 'R7' in a[4]['output']['error']
        assert b[4]['output']['items'] == [{'id':1,'type':'column','cls':'split','rect':[40,70,60,80]}]
        assert b[5]['output']['ok']
    probes[phase] = {'identity': p['identity'], 'A_query': a[4]['output'], 'A_apply': a[5]['output'],
                     'A_dump_unchanged': True, 'B_query': b[4]['output'], 'B_apply': b[5]['output']}

result = {'exit_code': 0, 'scope': 'verify existing historical bytes only; no product or test execution',
          'f13_source_sha': receipt['sha'], 'f13_original_step': step,
          'selected_members': members, 'reference_contract_result': ref_result,
          'native_log_first_line': core.splitlines()[0],
          'aggregate_relevant_lines': [l for l in summary.splitlines() if any(k in l for k in ['c:integrity','core:run_tests','py:test_reference_contract','TOTAL','總計'])],
          'historical_withdrawal_exit_matrix': {phase:{k:v['exit'] for k,v in x['runs'].items()} for phase,x in withdrawal.items()},
          'historical_probes': probes,
          'limitations': ['F13 is historical source, not current main or root candidate F.',
                         'probe head fields alone do not prove clean checkout; their own identity note allows uncommitted edits.',
                         'new selected-member recovery proves exactly five hashes, not every archive member or whole test closure.',
                         'PR291 seven-job evidence remains an API body report; its D: original certificate was not read here.']}
(D/'HISTORICAL_RECEIPT_CHECK.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'exit_code':0, 'selected_originals_hashes_verified':len(members),
                  'f13_source_sha':receipt['sha'], 'reference_contract_result':ref_result,
                  'native_log_first_line':core.splitlines()[0],
                  'historical_withdrawal_exit_matrix':result['historical_withdrawal_exit_matrix']},ensure_ascii=False))
