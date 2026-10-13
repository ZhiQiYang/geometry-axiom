import hashlib,importlib.util,json,pathlib,re,shutil,subprocess
root=pathlib.Path.cwd();scratch=pathlib.Path('/tmp/geometry-182-cause');out=root/'tests/release-evidence/20261011-pr182-exception-evidence'
spec=importlib.util.spec_from_file_location('gate',root/'tests/section_profile_mutation_check.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
full=scratch/'full-gate';run=json.loads((full/'run.json').read_text());ledger=json.loads((full/'mutations.json').read_text())
before=json.loads((full/'checkout-before.json').read_text());after=json.loads((full/'checkout-after.json').read_text())
assert run['returncode']==0 and before==after and before['status']==[] and before['head']=='151da30ff2da765dd1cfff0a4c0d4a3307a028c0'
assert ledger['summary']=={'killed':41,'equivalent':1} and len(ledger['results'])==42
assert {r['id'] for r in ledger['results']}=={c['id'] for c in gate.CASES}
native=ledger['baselines']['native'];model=ledger['baselines']['model']
assert (native['exception_evidence']['tests_run'],model['exception_evidence']['tests_run'])==(25,19)
assert native['exit']==model['exit']==0 and not native['exception_evidence']['skipped'] and not model['exception_evidence']['skipped']
compiles=list((full/'logs').glob('*.compile.json'));assert len(compiles)==38
assert all(json.loads(p.read_text())['exit']==0 for p in compiles)
native_cases=[r for r in ledger['results'] if r['group']=='native'];assert len(native_cases)==37
for r in ledger['results']:
    assert gate.evidence_problem(r['exit'],r['exception_evidence']) is None
    if r['group']=='native':
        build=json.loads((full/'logs'/('bridge-'+r['id']+'.compile.json')).read_text())
        assert r['binary_sha256']==build['binary_sha256']!=native['binary_sha256']
assert json.loads((full/'logs/bridge-baseline.compile.json').read_text())['binary_sha256']==native['binary_sha256']
assert model['adapter_sha256']==before['binaries']['model-base']['sha256']
old_probe=json.loads((scratch/'before/receipt.json').read_text());new_probe=json.loads((scratch/'after-final/receipt.json').read_text())
assert old_probe['verdict']['verdict']=='killed' and new_probe['verdict']['verdict']!='killed'
assert new_probe['head']==before['head'] and new_probe['status']==[]
assert hashlib.sha256((scratch/'before/test_section_profile_mutation_check.py').read_bytes()).hexdigest()==old_probe['sources']['tests/test_section_profile_mutation_check.py']
old_ref='f2d332be37eb9c4d66d5c2c82edd72e966f91f5a'
assert hashlib.sha256(subprocess.check_output(['git','show',old_ref+':tests/section_profile_mutation_check.py'])).hexdigest()==old_probe['sources']['tests/section_profile_mutation_check.py']
assert subprocess.check_output(['git','diff',old_ref,'--','tests/release-evidence'])==b''
assert not out.exists();out.mkdir(parents=True)
for folder in ('before','after-final','matcher-proofs','checks','full-gate'):
    shutil.copytree(scratch/folder,out/folder)
shutil.copyfile('/tmp/geometry-182-cause-before-guard.log',out/'before/guard-before.log')
shutil.copyfile('/tmp/geometry-182-cause-build.log',out/'before/registry-build.log')
(out/'before/observed-checks.json').write_text(json.dumps({'guard_argv':['python3','tests/test_section_profile_mutation_check.py'],'guard_exit_observed_from_exec_tool':1,'guard_methods':24,'guard_assertion_failures':12,'registry_build_argv':['python3','tests/binaries.py','build','bridge','model-base'],'registry_build_exit_observed_from_exec_tool':0,'scope':'Observed shell tool exits; not retroactively labelled Popen receipts'},indent=2)+'\n')
(out/'executors').mkdir()
for name in ('probe','matcher-proofs','full','checks','package'):
    p=pathlib.Path('/tmp/geometry-182-cause-'+name+'.py');shutil.copyfile(p,out/'executors'/p.name)
closure={'tested_head':before['head'],'previous_head':old_ref,'native_compiles':38,'native_mutants':37,'model_mutants':5,
         'guard_methods':29,'matched_same_exception_cases':41,'equivalent_cases':1,'source_and_binaries_before_after_equal':True,
         'historical_evidence_git_diff_empty':True,'baseline_native_hash':native['binary_sha256'],'model_adapter_hash':model['adapter_sha256'],
         'source_sha256':before['sources'],'scope':'Cloud standalone mutation gate, not WSL/seven jobs/full AC16/full aggregate'}
(out/'closure.json').write_text(json.dumps(closure,ensure_ascii=False,indent=2)+'\n')
sentence=f"原完整 42 案閘門重跑：41 killed／1 equivalent，直接 returncode 0、{run['seconds']:.2f} 秒；native 基準 25/25、model 基準 19/19，零 skip。"
for name in ('README','body','reply'):
    p=pathlib.Path('/tmp/geometry-182-cause-'+name+'.md');text=p.read_text();assert text.count('FULL_GATE_RESULT')==1
    p.write_text(text.replace('FULL_GATE_RESULT',sentence))
shutil.copyfile('/tmp/geometry-182-cause-README.md',out/'README.md')
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file())
(out/'SHA256SUMS').write_text(manifest)
print(json.dumps({'payloads':len(manifest.splitlines()),'bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'full_gate_exit':run['returncode']}))
