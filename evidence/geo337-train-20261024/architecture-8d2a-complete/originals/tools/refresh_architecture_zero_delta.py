"""Regenerate the original four architecture artifacts from an exact clean source.
The permitted current manifest delta is zero; nine guards use a pinned historical manifest.
"""
from pathlib import Path
import argparse,collections,copy,datetime,hashlib,importlib.util,json,os,re,resource,sys
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--sha',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--prior-source',required=True);p.add_argument('--guard-baseline-source',default='ca7838e0f4950452b9befcf40899d606db9b81fa');a=p.parse_args();R=a.root.resolve();O=a.out.resolve();F=a.sha
assert re.fullmatch('[0-9a-f]{40}',a.prior_source) and re.fullmatch('[0-9a-f]{40}',a.guard_baseline_source)
assert re.fullmatch('[0-9a-f]{40}',F) and not O.exists() and not O.is_relative_to(R) and not sys.flags.optimize
assert resource.getrlimit(resource.RLIMIT_STACK)[0]==16777216
ART='geometry-core/domain-decoupling';NAMES=['product-architecture.json','product-architecture-scan.json','PRODUCT-ARCHITECTURE.md','product-architecture-receipt.json'];JUDGES=['tests/architecture_contract.py','tests/test_architecture_contract.py','tests/test_product_architecture.py']
ADDED={'WOOD_BOUNDARY_END_BARE_RC','WOOD_BOUNDARY_END_ORDINARY','WOOD_BOUNDARY_END_PARTIAL','WoodBoundaryEndAdmission','wood_contact_boundary_end_admission','wood_contact_boundary_end_uses_member_facts','wood_contact_end_support_check','wood_reference_boundary_end','wood_reference_partial_ref_candidates'}
SUFFIXES={'.c','.cc','.cjs','.cpp','.cxx','.h','.hh','.hpp','.htm','.html','.inc','.js','.jsx','.mjs','.py','.ts','.tsx'}
def H(b):return hashlib.sha256(b).hexdigest()
def LF(b):return b.replace(b'\r\n',b'\n')
HISTORICAL_PIN='80f44b8c870e097413e395d30ba029199ba66b7302985c0f325d4f446d0ce525'
CURRENT_PIN='81882184010b5ddb9aa8e8d45467be788a65a79b378037ba6c99268f99bfa975'
PROBE_PIN='350fc09a16660d33144fe7b7a8198032e8251e37a67a61179ec96eba39e1e739'
EXPECTED_CHANGED_INPUT='geometry-templates/woodworking/native/contact_world.c'
def validate_manifests(current_raw,previous_raw,historical_raw):
 assert current_raw==previous_raw and H(LF(current_raw))==CURRENT_PIN
 assert H(historical_raw)==HISTORICAL_PIN
 current,previous,historical=map(json.loads,[current_raw,previous_raw,historical_raw])
 assert current==previous
 assert len(current['policy']['forbiddenIdentifiers'])==937 and len(current['policy']['forbiddenStrings'])==55
 assert len(historical['policy']['forbiddenIdentifiers'])==928 and len(historical['policy']['forbiddenStrings'])==55
 assert set(current['policy']['forbiddenIdentifiers'])-set(historical['policy']['forbiddenIdentifiers'])==ADDED
 assert set(historical['policy']['forbiddenIdentifiers'])<=set(current['policy']['forbiddenIdentifiers'])
 check=copy.deepcopy(current);check['policy']['forbiddenIdentifiers']=historical['policy']['forbiddenIdentifiers'];assert check==historical
 return historical
def info(p):
 b=p.read_bytes();return {'bytes':len(b),'rawSha256':H(b),'lfSha256':H(LF(b))}
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');CAP_PIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762';assert H(CAP.read_bytes())==CAP_PIN
sp=importlib.util.spec_from_file_location('cap',CAP);cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap)
O.mkdir();(O/'execution-source-originals').mkdir();(O/'previous-artifact').mkdir();(O/'new').mkdir();(O/'tmp').mkdir();(O/'tools').mkdir();(O/'tools'/Path(__file__).name).write_bytes(Path(__file__).read_bytes());(O/'tools'/'capture.py').write_bytes(CAP.read_bytes())
env=dict(os.environ);cleared=[]
for k in ('PYTHONOPTIMIZE','PYTHONPATH','PYTHONSTARTUP','NODE_OPTIONS'):
 if k in env:cleared.append(k);env.pop(k)
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',LANG='C.UTF-8',LC_ALL='C.UTF-8',TMPDIR=str(O/'tmp'),GITHUB_SHA=F,GITHUB_WORKSPACE=str(R));rec=cap.Recorder(O,env,F)
def run(argv,check=True,variant='original architecture gate at fixed clean source'):return rec.run(argv,cwd=R,timeout=None,check=check,source_sha=F,source_variant=variant)
def git(*args):return run(['git',*args])[1]
assert git('rev-parse','HEAD').decode().strip()==F and not git('status','--porcelain=v1','--untracked-files=all')
old_four={n:(R/ART/n).read_bytes() for n in NAMES}
for n,b in old_four.items():(O/'execution-source-originals'/n).write_bytes(b)
manifest=json.loads(old_four[NAMES[0]]);prior=json.loads(old_four[NAMES[3]]);assert prior['schema']=='geometry-product-architecture-receipt/1'
assert prior['sourceBaseHead']==a.prior_source
old_commit=git('log','-1','--format=%H','--',ART+'/'+NAMES[3]).decode().strip();git('merge-base','--is-ancestor',prior['sourceBaseHead'],F)
previous_manifest_raw=git('show',old_commit+':'+ART+'/'+NAMES[0]);previous_manifest=json.loads(previous_manifest_raw);assert H(LF(previous_manifest_raw))==prior['manifestSha256']
(O/'previous-artifact'/NAMES[0]).write_bytes(previous_manifest_raw)
assert git('rev-parse',a.guard_baseline_source+'^{commit}').decode().strip()==a.guard_baseline_source
git('merge-base','--is-ancestor',a.guard_baseline_source,F)
historical_row,historical_raw,_=run(['git','show',a.guard_baseline_source+':'+ART+'/'+NAMES[0]],variant='Read pinned historical 928-identifier manifest; not the previous 937-identifier artifact')
historical_manifest=validate_manifests(old_four[NAMES[0]],previous_manifest_raw,historical_raw)
(O/'historical-928-manifest.json').write_bytes(historical_raw)
historical_binding={'sourceGitSHA':a.guard_baseline_source,'manifestRawSha256':HISTORICAL_PIN,'manifestLfSha256':H(LF(historical_raw)),'identifiers':928,'strings':55,'readCommand':historical_row,'usedAsPreviousManifest':False}
cap.dump(O/'historical-guard-baseline.json',historical_binding)
assert len(manifest['sources'])==334 and len(manifest['exclusions'])==270
for n in NAMES[1:]:
 assert git('show',old_commit+':'+ART+'/'+n)==old_four[n];(O/'previous-artifact'/n).write_bytes(old_four[n])
declared=sorted(x['path'] for key in ['sources','exclusions'] for x in manifest[key]);assert len(declared)==len(set(declared))==604
rawtree=git('ls-tree','-r','-z',F,'--',*manifest['sourceRoots'],*manifest['sourceFiles']);tree={}
for entry in rawtree.split(b'\0'):
 if not entry:continue
 meta,name=entry.split(b'\t',1);mode,kind,oid=meta.split();path=name.decode()
 if Path(path).suffix.lower() in SUFFIXES:assert kind==b'blob' and mode!=b'120000';tree[path]=oid.decode()
assert sorted(tree)==declared

def snapshot():
 paths=set(manifest['sourceFiles'])
 for root in manifest['sourceRoots']:
  for parent,dirs,files in os.walk(R/root,followlinks=False):
   assert all(not (Path(parent)/n).is_symlink() for n in dirs)
   for n in files:
    f=Path(parent)/n
    if f.suffix.lower() in SUFFIXES:assert f.is_file() and not f.is_symlink();paths.add(f.relative_to(R).as_posix())
 assert sorted(paths)==declared
 rows=[]
 for path in declared:
  b=(R/path).read_bytes();oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert oid==tree[path];rows.append({'path':path,'bytes':len(b),'rawSha256':H(b),'lfSha256':H(LF(b)),'gitBlobOid':oid})
 return rows
before=snapshot();inputs=[{'path':x['path'],'sha256':x['lfSha256']} for x in before];old_inputs={x['path']:x['sha256'] for x in prior['inputs']};assert set(old_inputs)==set(declared);changed=[x for x in inputs if old_inputs[x['path']]!=x['sha256']];assert [x['path'] for x in changed]==[EXPECTED_CHANGED_INPUT];closure=H(json.dumps(inputs,ensure_ascii=False,separators=(',',':')).encode());cap.dump(O/'source-inputs.json',before)
protected={n:info(R/n) for n in ['公理層.md','決策佇列.md']};tools={n:info(R/n)['lfSha256'] for n in JUDGES}
for n in JUDGES:assert H(LF(git('show',F+':'+n)))==tools[n]
for n in protected:assert H(git('show',F+':'+n))==protected[n]['rawSha256']
# Full lexical inventory uses the unchanged original lexer, never a handwritten generation list.
sp=importlib.util.spec_from_file_location('original_arch_scanner',R/JUDGES[0]);sc=importlib.util.module_from_spec(sp);sys.modules[sp.name]=sc;sp.loader.exec_module(sc)
words=set();origins=collections.defaultdict(list)
for x in manifest['sources']:
 if x['layer']=='W' and x['language']=='c':
  _,_,tokens=sc.lex((R/x['path']).read_text(encoding='utf-8-sig'),x['path'],c=True)
  for t in tokens:
   if t.kind=='identifier' and t.value.startswith(('Wood','WOOD_','wood_')):words.add(t.value);origins[t.value].append({'path':x['path'],'line':t.line})
assert words<=set(manifest['policy']['forbiddenIdentifiers']);assert not words-set(previous_manifest['policy']['forbiddenIdentifiers']);assert words-set(historical_manifest['policy']['forbiddenIdentifiers'])==ADDED
cap.dump(O/'policy-guard-inventory.json',{'addedIdentifiers':[],'removedIdentifiers':[],'oldCount':937,'newCount':937,'stringCount':55,'allOtherManifestFieldsEqual':True,'historicalGuardIdentifiers':[{'identifier':n,'origins':origins[n]} for n in sorted(ADDED)],'historicalGuardBaseline':historical_binding})
results=[]
for argv in [['python3','-B',JUDGES[0],'--root','.','--manifest',ART+'/'+NAMES[0]],['python3','-B',JUDGES[1]],['python3','-B',JUDGES[2]]]:results.append(run(argv))
scan=json.loads(results[0][1]);assert scan['ok'] and scan['diagnostics']==[] and len(scan['edges'])==798
validations=[]
for (row,out,err),expected in zip(results[1:],[205,18]):
 text=(out+b'\n'+err).decode();counts=re.findall(r'^Ran (\d+) tests? in ([0-9.]+)s$',text,re.M);assert len(counts)==1 and int(counts[0][0])==expected and text.rstrip().endswith('OK')
 validations.append({**row,'exitCode':0,'tests':expected,'passed':expected,'failed':0,'skipped':0,'unittestSeconds':float(counts[0][1])})
# Fresh same-source assertions against the historical 928 baseline, not previous artifact.
probe_raw=Path('/workspace/geo337-U-architecture-policy-proof-20261024/probe.py').read_bytes();assert H(probe_raw)==PROBE_PIN;probe=probe_raw.decode();(O/'tools'/'policy_probe.py').write_bytes(probe_raw);withdrawn=O/'withdrawn-manifest.json';withdrawn.write_bytes(historical_raw);proof=[]
for name in sorted(ADDED):
 for phase,path in [('fixed',R/ART/NAMES[0]),('withdrawn',withdrawn),('restored',R/ART/NAMES[0])]:
  row,out,err=run(['python3','-B','-c',probe,str(R),str(path),name,'protected'],check=False,variant='same-source W guard '+phase+'; withdrawn baseline Git '+a.guard_baseline_source+' raw sha256 '+HISTORICAL_PIN);expected=1 if phase=='withdrawn' else 0;assert row['actual_process_returncode']==expected
  if phase=='withdrawn':assert b'AssertionError: new W identifier must be rejected from K:' in err and json.loads(out)['diagnostics']==[]
  else:assert not err
  proof.append({'identifier':name,'phase':phase,'exit':expected,'directory':row['directory'],'executionSourceSHA':F,'manifestSourceGitSHA':a.guard_baseline_source if phase=='withdrawn' else F,'manifestRawSha256':HISTORICAL_PIN if phase=='withdrawn' else H(old_four[NAMES[0]])})
for path in [withdrawn,R/ART/NAMES[0]]:run(['python3','-B','-c',probe,str(R),str(path),'geo261_architecture_neutral_probe','neutral'])
assert snapshot()==before and protected=={n:info(R/n) for n in protected} and tools=={n:info(R/n)['lfSha256'] for n in JUDGES}
assert all((R/ART/n).read_bytes()==old_four[n] for n in NAMES);assert git('rev-parse','HEAD').decode().strip()==F and not git('status','--porcelain=v1','--untracked-files=all')
assert [x['path'] for x in changed]==[EXPECTED_CHANGED_INPUT]
counts={'executableFiles':604,'ownedSources':334,'exclusions':270,'edges':798,'diagnostics':0,'layers':dict(sorted(collections.Counter(x['layer'] for x in manifest['sources']).items())),'languages':dict(sorted(collections.Counter(x['language'] for x in manifest['sources']).items())),'forbiddenIdentifiers':937,'forbiddenStrings':55}
report=f'''# Product architecture — integration train fixed-source receipt

產品／裁判實際來源 `{F}`。三條原命令 exit 0／0／0；generic 205、product 18，零 skip。完整604 inputs、334 owned／270 exclusions、798 edges／0 diagnostics。LF closure `{closure}`。來源 HEAD、604個Git blob／raw／LF、三個裁判及兩份 SSOT 前後不變。

本輪 manifest 與前份產物逐 bytes 相同：forbiddenIdentifiers 937→937、forbiddenStrings 55；分類、路徑、exclusion、trust及所有政策不變。完整604輸入相較前份收據僅 `{EXPECTED_CHANGED_INPUT}` 的來源雜湊改變。原完整 W lexer 盤點仍覆蓋全部 W identifiers。九組既有 guard 在本次來源重新實跑0／1／0；撤回用歷史928版 Git `{a.guard_baseline_source}`、原SHA256 `{HISTORICAL_PIN}`，明確不同於上一份937版 manifest。兩個neutral probe亦重新通過，沒有移標歷史判決。

前份收據 source `{prior['sourceBaseHead']}`，產物提交 `{old_commit}`；本次完整輸入差異在 receipt／source-inputs.json，歷史報告保於該Git提交。四檔寫至來源外，receipt不hash自己。原native／browser／mutation ledger／效能需各自原收據，本四檔不代稱它們通過。
'''
new=O/'new';(new/NAMES[0]).write_bytes(old_four[NAMES[0]]);(new/NAMES[1]).write_bytes(results[0][1]);(new/NAMES[2]).write_text(report)
receipt={k:prior[k] for k in ['schema','hashMode','inputClosureHashSerialization','inputClosureExcludes','inputClosureExclusionReason','notClaimed']}
receipt.update(headBinding='All commands executed at the same clean source SHA; four derived outputs written outside source and excluded from executable closure.',createdUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),basis='Original Linux receipt schema and original judges; unchanged 937-identifier manifest, full 604-source inventory, and fresh assertions against pinned historical 928 baseline.',sourceBaseHead=F,headObservedBefore=F,headObservedAfter=F,manifestSha256=H(LF(old_four[NAMES[0]])),scannerSha256=tools[JUDGES[0]],scanSha256=H(LF(results[0][1])),reportSha256=H(LF((new/NAMES[2]).read_bytes())),inputClosureSha256=closure,counts=counts,scanPassed=True,actualCliScan={**results[0][0],'exitCode':0},validation=validations,inputs=inputs)
receipt['manifestRefresh']={'manifestByteUnchangedFromExecutionSource':True,'allPolicyFieldsEqualToPrevious':True,'onlyPolicyDelta':{'addedIdentifiers':[],'removedIdentifiers':[],'otherManifestFieldsEqual':True},'sourceClassificationsUnchanged':True,'previousSource':prior['sourceBaseHead'],'previousArtifactCommit':old_commit,'previousOutputs':{n:info(O/'previous-artifact'/n) for n in NAMES},'executionSourceOutputs':{n:info(O/'execution-source-originals'/n) for n in NAMES},'changedPriorInputs':changed,'sourceReceiptEvidenceDirectory':str(O),'originalThreeGateExits':[0,0,0],'manifestProof':proof,'historicalGuardBaseline':historical_binding,'note':'No inherited proof relabeled. Current/previous manifests are byte-identical (937). Nine controls execute freshly at this source against the separately pinned historical 928 manifest outside source.'}
receipt['completeInventoryVerification']={'sourceRoots':manifest['sourceRoots'],'sourceFiles':manifest['sourceFiles'],'filesBefore':604,'filesAfter':604,'allRawAndLfInputsUnchanged':True,'toolHashesBefore':tools,'toolHashesAfter':tools,'inputClosureSha256Before':closure,'inputClosureSha256After':closure,'protectedSsotBefore':protected,'protectedSsotAfter':protected}
receipt['supplementalStaticGuardProbes']={'executedAtCurrentHead':True,'newIdentifiers':0,'guardIdentifiersRetested':9,'historicalBaselineSource':a.guard_baseline_source,'historicalBaselineRawSha256':HISTORICAL_PIN,'fixedWithdrawnRestored':[0,1,0],'neutralCases':2,'legacyWindowsSupplementalExecuted':False};receipt['nativeAcceptance']='Separate original receipts required; this architecture receipt does not certify runtime behavior.'
receipt['refreshDriver']={**info(Path(__file__)),'path':str(Path(__file__)),'argv':sys.argv,'recorderSha256':CAP_PIN,'runDirectory':str(O)};receipt['environment']={'safeVariables':results[0][0]['environment'],'clearedInheritedEnvironmentNames':cleared,'python':sys.version};receipt['uncertainties']=['Full native/browser/ledger and performance results are separate gates.','Generated outputs remain external until separately committed and pushed.']
cap.dump(new/NAMES[3],receipt);cap.dump(O/'RESULT.json',{'sourceSHA':F,'sourceBeforeAfterClean':True,'originalGateExits':[0,0,0],'newGuardProofExits':[0,1,0],'newGuardCases':0,'existingGuardCasesRetested':9,'historicalGuardBaseline':historical_binding,'manifestDelta':'unchanged-937-to-937','inputCount':604,'changedPriorReceiptInputs':changed,'inputClosureSHA256':closure,'outputs':{n:info(new/n) for n in NAMES},'sourceCheckoutModified':False,'ledgerRegenerated':False});print(json.dumps({'source':F,'gates':[0,0,0],'proofs':9,'result':str(O/'RESULT.json')}))
