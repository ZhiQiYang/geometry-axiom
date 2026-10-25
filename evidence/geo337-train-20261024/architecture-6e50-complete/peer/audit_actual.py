from pathlib import Path
import collections, datetime, hashlib, json, re, subprocess

ROOT = Path('/workspace/geometry-axiom')
OUT = Path('/tmp/geo337-h-architecture-resume-peer-20261025')
ACT = Path('/tmp/geo337-h-architecture-four-20261025')
LAUNCH = Path('/tmp/geo337-h-architecture-four-launch-20261025')
MERGE = Path('/tmp/geo337-h-local-init-integration-20261025')
M = '6e50aef65513b7b38f93228919272c6d40d6c196'
S = '2c4635577a8fcb11e88b346547f7bb1c7b739fb7'
E = '5f27125c950162d9232c22bd966aad9a77e33dbd'
PRIOR = 'e321026fb9bc9bc19c54b8034af6e6eaec2857f9'
ART = 'geometry-core/domain-decoupling/'
NAMES = ['product-architecture.json', 'product-architecture-scan.json', 'PRODUCT-ARCHITECTURE.md', 'product-architecture-receipt.json']
def H(b): return hashlib.sha256(b).hexdigest()
def LF(b): return b.replace(b'\r\n', b'\n')
def J(p): return json.loads(Path(p).read_bytes())
def git(*args):
    r = subprocess.run(['git', *args], cwd=ROOT, capture_output=True)
    assert r.returncode == 0, (args, r.stderr)
    return r.stdout
def verify_commands(base, sha):
    rows = J(base/'subcommands.json')
    for row in rows:
        d = Path(row['directory'])
        assert d.parent == base/'subcommands'
        assert J(d/'result.json') == row
        request = J(d/'request.json')
        for key in ['command','cwd','acceptance_sha','source_sha','source_variant','environment','started_epoch','stdin_provided','stdin_sha256','directory']:
            assert row[key] == request[key], (d,key)
        assert row['source_sha'] == row['acceptance_sha'] == sha
        assert row['timeout_expired'] is False and row['ended_epoch'] >= row['started_epoch']
        assert row['environment']['PYTHONOPTIMIZE'] is None
        for stream in ['stdout','stderr']:
            b = (d/(stream+'.bin')).read_bytes()
            assert H(b) == row[stream+'_sha256'] and len(b) == row[stream+'_bytes']
        assert H((d/'stdin.bin').read_bytes()) == row['stdin_sha256']
    return rows

assert not (OUT/'REVIEW.json').exists()
commands = verify_commands(ACT,M)
outer = verify_commands(LAUNCH,M)
merge = verify_commands(MERGE,S)
assert len(commands) == 51 and collections.Counter(r['actual_process_returncode'] for r in commands) == {0:42,1:9}
assert len(outer) == 2 and all(r['actual_process_returncode']==0 for r in outer)
assert len(merge) == 16 and all(r['actual_process_returncode']==0 for r in merge)
assert J(LAUNCH/'RESULT.json')['exit'] == 0 and J(LAUNCH/'RESULT.json')['source_sha'] == M
assert git('show','-s','--format=%P',M).decode().strip().split() == [E,S]
assert git('diff','--name-only',S,M,'--','.',':(exclude)evidence') == b''
assert git('diff','--name-only',E,M).decode().splitlines() == ['geometry-core/references.inc','tests/geo337_reference_local_init_harness.c','tests/run_all.expected.json','tests/test_geo261_load_residual.py']
remote_rows = [r for r in merge if 'ls-remote' in r['command']]
assert len(remote_rows)==2
assert (Path(remote_rows[0]['directory'])/'stdout.bin').read_text().split()[0]==S
assert (Path(remote_rows[1]['directory'])/'stdout.bin').read_text().split()[0]==M

result=J(ACT/'RESULT.json'); receipt=J(ACT/'new'/NAMES[3]); manifest=J(ACT/'new'/NAMES[0]); scan=J(ACT/'new'/NAMES[1])
assert result['sourceSHA']==receipt['sourceBaseHead']==receipt['headObservedBefore']==receipt['headObservedAfter']==M
assert result['originalGateExits']==[0,0,0] and result['newGuardProofExits']==[0,1,0]
assert result['sourceBeforeAfterClean'] and not result['sourceCheckoutModified'] and not result['ledgerRegenerated']
assert receipt['manifestRefresh']['previousSource']==PRIOR
assert receipt['manifestRefresh']['changedPriorInputs']==result['changedPriorReceiptInputs']
assert [x['path'] for x in result['changedPriorReceiptInputs']]==['geometry-core/references.inc']
assert len(manifest['sources'])==334 and len(manifest['exclusions'])==270
assert len(manifest['policy']['forbiddenIdentifiers'])==937 and len(manifest['policy']['forbiddenStrings'])==55
assert scan['ok'] is True and scan['diagnostics']==[] and len(scan['edges'])==798
for name in NAMES:
    b=(ACT/'new'/name).read_bytes(); expected=result['outputs'][name]
    assert len(b)==expected['bytes'] and H(b)==expected['rawSha256'] and H(LF(b))==expected['lfSha256']
    assert (ACT/'execution-source-originals'/name).read_bytes()==git('show',M+':'+ART+name)
    assert (ACT/'previous-artifact'/name).read_bytes()==(ACT/'execution-source-originals'/name).read_bytes()
assert (ACT/'new'/NAMES[0]).read_bytes()==(ACT/'execution-source-originals'/NAMES[0]).read_bytes()
assert (ACT/'new'/NAMES[1]).read_bytes()==(ACT/'execution-source-originals'/NAMES[1]).read_bytes()
assert receipt['manifestSha256']==H(LF((ACT/'new'/NAMES[0]).read_bytes()))
assert receipt['scanSha256']==H(LF((ACT/'new'/NAMES[1]).read_bytes()))
assert receipt['reportSha256']==H(LF((ACT/'new'/NAMES[2]).read_bytes()))

inputs=J(ACT/'source-inputs.json')
assert len(inputs)==604 and len({x['path'] for x in inputs})==604
assert [x['path'] for x in inputs]==sorted(x['path'] for key in ['sources','exclusions'] for x in manifest[key])
request=''.join(M+':'+x['path']+'\n' for x in inputs).encode()
raw=subprocess.run(['git','cat-file','--batch'],cwd=ROOT,input=request,capture_output=True,check=True).stdout
offset=0
for item in inputs:
    end=raw.index(b'\n',offset); oid,kind,size=raw[offset:end].split(); size=int(size)
    b=raw[end+1:end+1+size]; assert raw[end+1+size:end+2+size]==b'\n'; offset=end+2+size
    assert kind==b'blob' and oid.decode()==item['gitBlobOid'] and size==item['bytes']
    assert H(b)==item['rawSha256'] and H(LF(b))==item['lfSha256']
    assert (ROOT/item['path']).read_bytes()==b
assert offset==len(raw)
closure_items=[{'path':x['path'],'sha256':x['lfSha256']} for x in inputs]
closure=H(json.dumps(closure_items,ensure_ascii=False,separators=(',',':')).encode())
assert receipt['inputs']==closure_items and result['inputClosureSHA256']==receipt['inputClosureSha256']==closure
old_inputs={x['path']:x['sha256'] for x in J(ACT/'previous-artifact'/NAMES[3])['inputs']}
assert [x['path'] for x in closure_items if old_inputs[x['path']]!=x['sha256']]==['geometry-core/references.inc']
inventory=receipt['completeInventoryVerification']
assert inventory['protectedSsotBefore']==inventory['protectedSsotAfter'] and inventory['toolHashesBefore']==inventory['toolHashesAfter']
for name, info in inventory['protectedSsotBefore'].items():
    b=git('show',M+':'+name)
    assert info['rawSha256']==H(b) and info['lfSha256']==H(LF(b)) and info['bytes']==len(b)
    assert (ROOT/name).read_bytes()==b
for name,pin in inventory['toolHashesBefore'].items(): assert H(LF(git('show',M+':'+name)))==pin

gate_argv=[['python3','-B','tests/architecture_contract.py','--root','.','--manifest',ART+NAMES[0]],['python3','-B','tests/test_architecture_contract.py'],['python3','-B','tests/test_product_architecture.py']]
gates=[]
for argv in gate_argv:
    found=[r for r in commands if r['command']==argv]; assert len(found)==1 and found[0]['actual_process_returncode']==0; gates+=found
assert receipt['actualCliScan']['command']==gates[0]['command']
assert receipt['actualCliScan']['stdout_sha256']==gates[0]['stdout_sha256']
for row, expected, recorded in zip(gates[1:],[205,18],receipt['validation']):
    text=(Path(row['directory'])/'stdout.bin').read_text()+'\n'+(Path(row['directory'])/'stderr.bin').read_text()
    assert re.findall(r'^Ran (\d+) tests? in [0-9.]+s$',text,re.M)==[str(expected)] and text.rstrip().endswith('OK')
    assert recorded['tests']==recorded['passed']==expected and recorded['failed']==recorded['skipped']==0
proofs=receipt['manifestRefresh']['manifestProof']
assert len(proofs)==27 and len({p['identifier'] for p in proofs})==9
bydir={r['directory']:r for r in commands}
for p in proofs:
    row=bydir[p['directory']]; expected=1 if p['phase']=='withdrawn' else 0
    assert p['executionSourceSHA']==M and p['exit']==row['actual_process_returncode']==expected
    argv=row['command']; assert argv[-2:]==[p['identifier'],'protected']
    assert H(Path(argv[-3]).read_bytes())==p['manifestRawSha256']
    output=(Path(row['directory'])/'stdout.bin').read_bytes(); error=(Path(row['directory'])/'stderr.bin').read_bytes()
    if expected: assert b'AssertionError: new W identifier must be rejected from K:' in error and json.loads(output)['diagnostics']==[]
    else: assert error==b'' and json.loads(output)['diagnostics']
for identifier in {p['identifier'] for p in proofs}:
    selected=[p for p in proofs if p['identifier']==identifier]
    assert [p['phase'] for p in selected]==['fixed','withdrawn','restored'] and [p['exit'] for p in selected]==[0,1,0]
assert len([r for r in commands if r['command'][-1:] == ['neutral'] and r['actual_process_returncode']==0])==2
assert git('rev-parse','HEAD').decode().strip()==M and git('status','--porcelain=v1')==b''

report={'schema':'geo337-h-architecture-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'findings':[],
    'source_sha':M,'child_source':S,'prior_actual_architecture_source':PRIOR,'original_gate_exits':[0,0,0],'original_unittest_counts':[205,18],
    'architecture_commands':len(commands),'architecture_exit_histogram':{'0':42,'1_intentional_withdrawn':9},'outer_commands':len(outer),'merge_commands':len(merge),
    'input_count':604,'input_closure_sha256':closure,'changed_prior_input':['geometry-core/references.inc'],'fresh_guard_triples':9,'guard_exits':[0,1,0],'neutral_cases':2,
    'manifest_and_scan_unchanged':True,'new_artifact_changed_paths':[ART+NAMES[2],ART+NAMES[3]],
    'bindings':{str(p):H(p.read_bytes()) for p in [ACT/'RESULT.json',LAUNCH/'RESULT.json',MERGE/'RESULT.json',Path('/tmp/merge_geo337_h_local_init_20261025.py'),OUT/'audit_actual.py']},
    'advisories':['Merge script did not assert child ls-remote tip, but the preserved premerge remote stdout is exactly public S; verified independently here. No history or raw output rewritten.'],
    'limits':['Read-only audit of actual receipts; no product gates rerun.','M is the actual architecture execution SHA; later adoption SHA must remain separate.','No full native, ledger, browsers, or N16/O2 performance acceptance is implied.']}
(OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'REVIEW.md').write_text(f'架構與合流原件對抗審查通過。實際來源 `{M}`；三條原裁判 exit 0/0/0，205 與18測試零skip；604來源逐Git/raw/LF核對，唯一變動references.inc。九組原guard重新0/1/0，兩neutral通過。51條原架構命令、2條outer與16條merge命令之原始流、環境、SHA及exit逐筆核對。manifest/scan不變，只有report/receipt衍生檔變更。\n\n合流腳本對child remote tip未加assert，但保留stdout本次確為S2c463；此靜態缺口已揭露，沒有改寫原件或重跑合流。實際架構執行M不可改標後續採用SHA；不宣稱runtime/performance/ledger完成。\n')
print(json.dumps({'exit_code':0,'source_sha':M,'review':str(OUT/'REVIEW.json'),'sha256':H((OUT/'REVIEW.json').read_bytes())}))
