from pathlib import Path
import ast,difflib,hashlib,json
P=Path(__file__).resolve().parent
old=(P/'original_driver.py.txt').read_text()
s=old
def sub(a,b):
 global s
 assert s.count(a)==1,(a[:100],s.count(a))
 s=s.replace(a,b)
sub('The permitted current manifest delta is zero; nine guards use a pinned historical manifest.',
    'The sole manifest delta is the approved cdp exclusion digest; two H inputs changed.\nDefault is plan-only. Execution requires a root-scheduled clean fixed-source run.')
sub('import argparse,collections,copy,datetime,hashlib,importlib.util,json,os,re,resource,sys',
    "import argparse,collections,copy,datetime,hashlib,importlib.util,json,os,re,resource,sys\nif sys.flags.optimize:raise RuntimeError('Python optimization forbidden')")
start="p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--sha',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--prior-source',required=True);p.add_argument('--guard-baseline-source',default='ca7838e0f4950452b9befcf40899d606db9b81fa');a=p.parse_args();R=a.root.resolve();O=a.out.resolve();F=a.sha\nassert re.fullmatch('[0-9a-f]{40}',a.prior_source) and re.fullmatch('[0-9a-f]{40}',a.guard_baseline_source)\nassert re.fullmatch('[0-9a-f]{40}',F) and not O.exists() and not O.is_relative_to(R) and not sys.flags.optimize\nassert resource.getrlimit(resource.RLIMIT_STACK)[0]==16777216"
sub(start,"""p=argparse.ArgumentParser()
p.add_argument('--root',type=Path);p.add_argument('--sha');p.add_argument('--out',type=Path)
p.add_argument('--execute',action='store_true');p.add_argument('--root-scheduled-architecture-run',action='store_true')
p.add_argument('--prior-source',default='e321026fb9bc9bc19c54b8034af6e6eaec2857f9')
p.add_argument('--guard-baseline-source',default='ca7838e0f4950452b9befcf40899d606db9b81fa')
a=p.parse_args()
PLAN={'schema':'geo344-exact-architecture-adapter-plan/1','execution':'UNRUN',
 'default':'plan only; no checkout reads, capture import, output mkdir, or judges',
 'ancestor':'a5ec136baf3909453867b3eed50f1b93b229ca59',
 'source_requirement':'clean resolvable descendant; only one manifest hash patch plus evidence changes from ancestor',
 'prior_execution':'e321026fb9bc9bc19c54b8034af6e6eaec2857f9',
 'expected_inputs':604,'expected_owned':334,'expected_exclusions':270,'expected_edges':798,
 'only_changed_inputs':['geometry-web/app.js','geometry-web/cdp_test.js'],
 'other_602_git_blobs':'must equal prior execution source',
 'manifest_delta':'only exclusions[path=geometry-web/cdp_test.js].sha256; formatting and all other bytes fixed',
 'policy':{'identifiers':937,'strings':55,'new_identifiers':0},
 'original_judges':[['python3','-B','tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json'],['python3','-B','tests/test_architecture_contract.py'],['python3','-B','tests/test_product_architecture.py']],
 'unit_expectations':[205,18],'allowed_skips':0,
 'digest_proof':'same source fixed/withdrawn/restored, actual 0/1/0; sole named EXCLUSION_DIGEST for cdp_test.js',
 'policy_proof':'nine original W guards, exact original historical928 raw preserved; separately derived control changes only same cdp digest',
 'outputs':['product-architecture.json','product-architecture-scan.json','PRODUCT-ARCHITECTURE.md','product-architecture-receipt.json'],
 'not_run':['Node strict9','browser','native','ledger','C build','performance'],
 'resource':'owner must provide complete clean source and fresh outside-source output after resource scheduling; no new acceptance threshold'}
if not a.execute:
 print(json.dumps(PLAN,ensure_ascii=False,indent=2));raise SystemExit(0)
assert not sys.flags.optimize and a.root_scheduled_architecture_run
assert a.root is not None and a.out is not None and a.sha is not None
assert a.prior_source=='e321026fb9bc9bc19c54b8034af6e6eaec2857f9'
assert a.guard_baseline_source=='ca7838e0f4950452b9befcf40899d606db9b81fa'
R=a.root.resolve();O=a.out.resolve();F=a.sha
assert re.fullmatch('[0-9a-f]{40}',F) and not O.exists() and not O.is_relative_to(R)
assert resource.getrlimit(resource.RLIMIT_STACK)[0]==16777216""")
sub("CURRENT_PIN='81882184010b5ddb9aa8e8d45467be788a65a79b378037ba6c99268f99bfa975'", """PREVIOUS_PIN='81882184010b5ddb9aa8e8d45467be788a65a79b378037ba6c99268f99bfa975'
CURRENT_PIN='f0c0b4db4ca01d4825883b73d73bf8644af313cd2bcab4c9b23638b9bbd93d32'
OLD_DIGEST='bb66742aa10b603b84362277f9f2c4275da8904925e75c618f252bd7df42cc3e'
NEW_DIGEST='1f3e2e36283ed7bbf6c4ad2cf3dc12c685667356d186d9fbd47bc5f0520f07ee'
DERIVED_HISTORY_PIN='2661beb6a5223d2aeecd64d708194261d97f0a738c1fc3adb22ff431c07bbbb8'
EXCLUSION_PATH='geometry-web/cdp_test.js'
EXPECTED_CLOSURE='71caf2df36a51b86da3d0553abd7ccebb7542d9dce2ec3f065e8d90a16ebbe0f'
ANCESTOR='a5ec136baf3909453867b3eed50f1b93b229ca59'""")
sub("EXPECTED_CHANGED_INPUT='geometry-core/kernel/source.c'", """EXPECTED_CHANGED_INPUTS=['geometry-web/app.js','geometry-web/cdp_test.js']
EXPECTED_CHANGED={
 'geometry-web/app.js':{'old_oid':'8b557a62cbdc5d315c082a97b6fa0bd7811bdaf8','oid':'e82ff16e7c0a671081cc763ec97a373b9bf9d3eb','lf':'c5f055915a039d90138824248b146552776286beb7544380c279a5586707ab60'},
 'geometry-web/cdp_test.js':{'old_oid':'ef229af148f664cc4a45d488abc8773f65aa2775','oid':'3f632a24935f0c47fcd05f3c9d58fe53089a9185','lf':NEW_DIGEST}}
def refresh_one_exclusion(raw):
 assert raw.count(OLD_DIGEST.encode())==1
 before=json.loads(raw);rows=[x for x in before['exclusions'] if x['path']==EXCLUSION_PATH]
 assert len(rows)==1 and rows[0]['hashMode']=='lf' and rows[0]['sha256']==OLD_DIGEST
 after=raw.replace(OLD_DIGEST.encode(),NEW_DIGEST.encode())
 rows[0]['sha256']=NEW_DIGEST;assert json.loads(after)==before
 return after""")
beg=s.index('def validate_manifests(');end=s.index('\ndef info(p):',beg)
s=s[:beg]+"""def validate_manifests(current_raw,previous_raw,historical_raw):
 assert H(previous_raw)==PREVIOUS_PIN and H(current_raw)==CURRENT_PIN
 assert refresh_one_exclusion(previous_raw)==current_raw
 assert H(historical_raw)==HISTORICAL_PIN
 current,previous,historical=map(json.loads,[current_raw,previous_raw,historical_raw])
 assert current['policy']==previous['policy']
 assert len(current['policy']['forbiddenIdentifiers'])==937 and len(current['policy']['forbiddenStrings'])==55
 assert len(historical['policy']['forbiddenIdentifiers'])==928 and len(historical['policy']['forbiddenStrings'])==55
 assert set(current['policy']['forbiddenIdentifiers'])-set(historical['policy']['forbiddenIdentifiers'])==ADDED
 assert set(historical['policy']['forbiddenIdentifiers'])<=set(current['policy']['forbiddenIdentifiers'])
 check=copy.deepcopy(previous);check['policy']['forbiddenIdentifiers']=historical['policy']['forbiddenIdentifiers'];assert check==historical
 derived=refresh_one_exclusion(historical_raw);assert H(derived)==DERIVED_HISTORY_PIN
 effective=json.loads(derived)
 check=copy.deepcopy(current);check['policy']['forbiddenIdentifiers']=effective['policy']['forbiddenIdentifiers'];assert check==effective
 return effective,derived
"""+s[end:]
sub("assert git('rev-parse','HEAD').decode().strip()==F and not git('status','--porcelain=v1','--untracked-files=all')\nold_four=", """assert git('rev-parse','HEAD').decode().strip()==F and not git('status','--porcelain=v1','--untracked-files=all')
git('merge-base','--is-ancestor',ANCESTOR,F)
assert git('diff','--name-only',ANCESTOR,F,'--','.',':(exclude)evidence/**').decode().splitlines()==[ART+'/'+NAMES[0]]
old_four=""")
sub("historical_manifest=validate_manifests(old_four[NAMES[0]],previous_manifest_raw,historical_raw)", "historical_manifest,effective_historical_raw=validate_manifests(old_four[NAMES[0]],previous_manifest_raw,historical_raw)")
sub("(O/'historical-928-manifest.json').write_bytes(historical_raw)", "(O/'historical-928-manifest.json').write_bytes(historical_raw)\n(O/'historical-928-with-current-cdp-digest.json').write_bytes(effective_historical_raw)")
sub("'usedAsPreviousManifest':False}", "'usedAsPreviousManifest':False,'effectiveControlIsDerived':True,'effectiveControlSha256':DERIVED_HISTORY_PIN,'effectiveControlPath':str(O/'historical-928-with-current-cdp-digest.json'),'onlyDerivation':{'path':EXCLUSION_PATH,'hashMode':'lf','old':OLD_DIGEST,'new':NEW_DIGEST}}")
sub("O.mkdir();(O/'execution-source-originals').mkdir()", "driver_before=Path(__file__).read_bytes()\nO.mkdir();(O/'execution-source-originals').mkdir()")
sub("(O/'tools'/Path(__file__).name).write_bytes(Path(__file__).read_bytes())", "(O/'tools'/Path(__file__).name).write_bytes(driver_before)")
sub("env.update(PYTHONDONTWRITEBYTECODE='1'", "for k in list(env):\n if k.startswith(('GIT_','MUTATE_')):cleared.append(k);env.pop(k)\nenv.update(PYTHONDONTWRITEBYTECODE='1'")
sub('assert sorted(tree)==declared',"""assert sorted(tree)==declared
prior_tree={}
for entry in git('ls-tree','-r','-z',a.prior_source,'--',*manifest['sourceRoots'],*manifest['sourceFiles']).split(b'\\0'):
 if not entry:continue
 meta,name=entry.split(b'\\t',1);mode,kind,oid=meta.split();path=name.decode()
 if Path(path).suffix.lower() in SUFFIXES:
  assert kind==b'blob' and mode!=b'120000';prior_tree[path]=oid.decode()
assert sorted(prior_tree)==declared
assert [n for n in declared if tree[n]!=prior_tree[n]]==EXPECTED_CHANGED_INPUTS
for n,expected in EXPECTED_CHANGED.items():assert prior_tree[n]==expected['old_oid'] and tree[n]==expected['oid']""")
assert s.count("assert [x['path'] for x in changed]==[EXPECTED_CHANGED_INPUT]")==2
s=s.replace("assert [x['path'] for x in changed]==[EXPECTED_CHANGED_INPUT]", "assert [x['path'] for x in changed]==EXPECTED_CHANGED_INPUTS;assert all(x['sha256']==EXPECTED_CHANGED[x['path']]['lf'] for x in changed)")
sub("cap.dump(O/'source-inputs.json',before)", "assert closure==EXPECTED_CLOSURE;cap.dump(O/'source-inputs.json',before)")
sub("scan=json.loads(results[0][1]);assert scan['ok'] and scan['diagnostics']==[] and len(scan['edges'])==798", "scan=json.loads(results[0][1]);assert scan['ok'] is True and scan['diagnostics']==[] and len(scan['edges'])==798 and len(scan['sources'])==334 and len(scan['trustedSourcesNotParsed'])==6")
sub("'allOtherManifestFieldsEqual':True,'historicalGuardIdentifiers'", "'allOtherManifestFieldsExceptSingleExclusionHashEqual':True,'exclusionDigestRefresh':{'path':EXCLUSION_PATH,'old':OLD_DIGEST,'new':NEW_DIGEST},'historicalGuardIdentifiers'")
insert="""# The unique hash withdrawal uses the unchanged original CLI at the same source.
digest_withdrawn=O/'single-cdp-digest-withdrawn.json';digest_withdrawn.write_bytes(previous_manifest_raw)
digest_proof=[];digest_outputs=[]
expected_digest_diagnostic={'path':EXCLUSION_PATH,'line':1,'code':'EXCLUSION_DIGEST','message':'immutable lf digest is absent or mismatched','direction':'','chain':[]}
for phase,path in [('fixed',R/ART/NAMES[0]),('withdrawn',digest_withdrawn),('restored',R/ART/NAMES[0])]:
 row,out,err=run(['python3','-B',JUDGES[0],'--root','.','--manifest',str(path)],check=False,variant='single cdp exclusion LF digest '+phase+'; all executable sources unchanged')
 expected=1 if phase=='withdrawn' else 0
 assert type(row['actual_process_returncode']) is int and row['actual_process_returncode']==expected and row['timeout_expired'] is False and not err
 parsed=json.loads(out)
 if phase=='withdrawn':
  assert parsed=={'ok':False,'sources':[],'trustedSourcesNotParsed':[],'edges':[],'diagnostics':[expected_digest_diagnostic]}
 else:assert out==results[0][1] and parsed['ok'] is True and parsed['diagnostics']==[]
 digest_outputs.append(out)
 digest_proof.append({'phase':phase,'actualExit':expected,'sourceGitSHA':F,'manifestSha256':H(path.read_bytes()),'command':row,'requiredDiagnostic':expected_digest_diagnostic if phase=='withdrawn' else None})
assert digest_outputs[0]==digest_outputs[2]
cap.dump(O/'single-exclusion-digest-proof.json',digest_proof)
"""
sub('# Fresh same-source assertions against the historical 928 baseline, not previous artifact.',insert+'# Fresh same-source assertions against explicitly derived historical928 policy control; original raw preserved.')
sub("withdrawn.write_bytes(historical_raw);proof=[]", "withdrawn.write_bytes(effective_historical_raw);proof=[]")
sub("variant='same-source W guard '+phase+'; withdrawn baseline Git '+a.guard_baseline_source+' raw sha256 '+HISTORICAL_PIN", "variant='same-source W guard '+phase+'; withdrawn DERIVED historical928 control '+DERIVED_HISTORY_PIN+' from original Git '+a.guard_baseline_source+' raw '+HISTORICAL_PIN")
sub("'manifestSourceGitSHA':a.guard_baseline_source if phase=='withdrawn' else F,'manifestRawSha256':HISTORICAL_PIN if phase=='withdrawn' else H(old_four[NAMES[0]])", "'manifestSourceGitSHA':None if phase=='withdrawn' else F,'manifestRawSha256':DERIVED_HISTORY_PIN if phase=='withdrawn' else H(old_four[NAMES[0]]),'manifestIsDerived':phase=='withdrawn','historicalOriginalSourceGitSHA':a.guard_baseline_source if phase=='withdrawn' else None,'historicalOriginalRawSha256':HISTORICAL_PIN if phase=='withdrawn' else None")
sub('本輪 manifest 與前份產物逐 bytes 相同：forbiddenIdentifiers 937→937、forbiddenStrings 55；分類、路徑、exclusion、trust及所有政策不變。完整604輸入相較前份收據僅 `{EXPECTED_CHANGED_INPUT}` 的來源雜湊改變。原完整 W lexer 盤點仍覆蓋全部 W identifiers。九組既有 guard 在本次來源重新實跑0／1／0；撤回用歷史928版 Git `{a.guard_baseline_source}`、原SHA256 `{HISTORICAL_PIN}`，明確不同於上一份937版 manifest。兩個neutral probe亦重新通過，沒有移標歷史判決。',
    '本輪 manifest 唯一變更為 `{EXCLUSION_PATH}` 排除項LF雜湊 `{OLD_DIGEST}` → `{NEW_DIGEST}`；其餘原bytes、forbiddenIdentifiers 937、forbiddenStrings 55、分類與全部政策不變。完整604輸入相較前份收據精確只有 `{EXPECTED_CHANGED_INPUTS}` 變更，其餘602 Git blob相同。唯一hash撤回／恢復真0／1／0，撤回只得 `EXCLUSION_DIGEST`。\n\n原完整W lexer盤點仍覆蓋全部W identifiers。九組既有guard在本次來源真0／1／0、兩neutral綠；歷史928 Git `{a.guard_baseline_source}` 的原raw `{HISTORICAL_PIN}` 原樣保留，實際撤回用另存衍生副本 `{DERIVED_HISTORY_PIN}`，只同步同一cdp排除hash，避免遮住W guard。衍生副本不是原歷史bytes，沒有移標歷史判決。')
sub("basis='Original Linux receipt schema and original judges; unchanged 937-identifier manifest, full 604-source inventory, and fresh assertions against pinned historical 928 baseline.'", "basis='Original Linux schema/judges; sole cdp exclusion LF digest refresh, exactly two changed H inputs, full604 inventory, unique digest0/1/0 and nine W guards against explicitly derived historical928 control.'")
sub("'onlyPolicyDelta':{'addedIdentifiers':[],'removedIdentifiers':[],'otherManifestFieldsEqual':True}", "'onlyPolicyDelta':{'addedIdentifiers':[],'removedIdentifiers':[]},'onlyManifestDelta':{'path':EXCLUSION_PATH,'field':'sha256','hashMode':'lf','old':OLD_DIGEST,'new':NEW_DIGEST,'allOtherBytesEqual':True}")
sub("'manifestProof':proof,'historicalGuardBaseline'", "'manifestProof':proof,'exclusionDigestProof':digest_proof,'historicalGuardBaseline'")
sub("'note':'No inherited proof relabeled. Current/previous manifests are byte-identical (937). Nine controls execute freshly at this source against the separately pinned historical 928 manifest outside source.'", "'note':'No inherited proof relabeled. Current/previous manifests differ only in the exact cdp exclusion digest; policy937/55 unchanged. Historical928 original raw remains intact; nine controls use a separately hashed derived copy with the same current cdp digest, outside source.'")
sub("'inputClosureSha256After':closure,'protectedSsotBefore'", "'inputClosureSha256After':closure,'unchangedPriorGitBlobCount':602,'changedPriorGitBlobPaths':EXPECTED_CHANGED_INPUTS,'protectedSsotBefore'")
sub("'historicalBaselineRawSha256':HISTORICAL_PIN,'fixedWithdrawnRestored'", "'historicalBaselineRawSha256':HISTORICAL_PIN,'effectiveWithdrawnControlSha256':DERIVED_HISTORY_PIN,'controlIsDerived':True,'fixedWithdrawnRestored'")
sub("'manifestDelta':'unchanged-937-to-937'", "'manifestDelta':'single-cdp-exclusion-lf-digest','exclusionDigestProofExits':[0,1,0],'effectiveHistoricalControlSha256':DERIVED_HISTORY_PIN")
sub("new=O/'new';(new/NAMES[0]).write_bytes(old_four[NAMES[0]])", "assert Path(__file__).read_bytes()==driver_before and H(CAP.read_bytes())==CAP_PIN\nnew=O/'new';(new/NAMES[0]).write_bytes(old_four[NAMES[0]])")
ast.parse(s)
(P/'refresh_architecture_cdp_exclusion.py').write_text(s)
(P/'ORIGINAL_TO_ADAPTER.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='original_driver.py',tofile='refresh_architecture_cdp_exclusion.py')))
print(json.dumps({'driver_bytes':len(s.encode()),'driver_sha256':hashlib.sha256(s.encode()).hexdigest(),'diff_bytes':(P/'ORIGINAL_TO_ADAPTER.diff').stat().st_size,'product_or_judge_executed':False}))
