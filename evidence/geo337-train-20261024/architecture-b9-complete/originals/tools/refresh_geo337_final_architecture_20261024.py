"""Regenerate the original four architecture artifacts from an exact clean source.
The only permitted manifest policy delta is the nine measured Reading A guards.
"""
from pathlib import Path
import argparse,collections,copy,datetime,hashlib,importlib.util,json,os,re,resource,sys
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--sha',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();R=a.root.resolve();O=a.out.resolve();F=a.sha
assert re.fullmatch('[0-9a-f]{40}',F) and not O.exists() and not O.is_relative_to(R) and not sys.flags.optimize
assert resource.getrlimit(resource.RLIMIT_STACK)[0]==16777216
ART='geometry-core/domain-decoupling';NAMES=['product-architecture.json','product-architecture-scan.json','PRODUCT-ARCHITECTURE.md','product-architecture-receipt.json'];JUDGES=['tests/architecture_contract.py','tests/test_architecture_contract.py','tests/test_product_architecture.py']
ADDED={'WOOD_BOUNDARY_END_BARE_RC','WOOD_BOUNDARY_END_ORDINARY','WOOD_BOUNDARY_END_PARTIAL','WoodBoundaryEndAdmission','wood_contact_boundary_end_admission','wood_contact_boundary_end_uses_member_facts','wood_contact_end_support_check','wood_reference_boundary_end','wood_reference_partial_ref_candidates'}
SUFFIXES={'.c','.cc','.cjs','.cpp','.cxx','.h','.hh','.hpp','.htm','.html','.inc','.js','.jsx','.mjs','.py','.ts','.tsx'}
def H(b):return hashlib.sha256(b).hexdigest()
def LF(b):return b.replace(b'\r\n',b'\n')
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
old_commit=git('log','-1','--format=%H','--',ART+'/'+NAMES[3]).decode().strip();git('merge-base','--is-ancestor',prior['sourceBaseHead'],F)
previous_manifest_raw=git('show',old_commit+':'+ART+'/'+NAMES[0]);previous_manifest=json.loads(previous_manifest_raw);assert H(LF(previous_manifest_raw))==prior['manifestSha256']
(O/'previous-artifact'/NAMES[0]).write_bytes(previous_manifest_raw)
assert set(manifest['policy']['forbiddenIdentifiers'])-set(previous_manifest['policy']['forbiddenIdentifiers'])==ADDED
check=copy.deepcopy(manifest);check['policy']['forbiddenIdentifiers']=previous_manifest['policy']['forbiddenIdentifiers'];assert check==previous_manifest
assert set(previous_manifest['policy']['forbiddenIdentifiers'])<=set(manifest['policy']['forbiddenIdentifiers']) and len(manifest['policy']['forbiddenIdentifiers'])==937 and len(manifest['policy']['forbiddenStrings'])==55
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
before=snapshot();inputs=[{'path':x['path'],'sha256':x['lfSha256']} for x in before];closure=H(json.dumps(inputs,ensure_ascii=False,separators=(',',':')).encode());cap.dump(O/'source-inputs.json',before)
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
assert words<=set(manifest['policy']['forbiddenIdentifiers']);assert words-set(previous_manifest['policy']['forbiddenIdentifiers'])==ADDED
cap.dump(O/'policy-guard-inventory.json',{'addedIdentifiers':[{'identifier':n,'origins':origins[n]} for n in sorted(ADDED)],'removedIdentifiers':[],'oldCount':928,'newCount':937,'stringCount':55,'allOtherManifestFieldsEqual':True})
results=[]
for argv in [['python3','-B',JUDGES[0],'--root','.','--manifest',ART+'/'+NAMES[0]],['python3','-B',JUDGES[1]],['python3','-B',JUDGES[2]]]:results.append(run(argv))
scan=json.loads(results[0][1]);assert scan['ok'] and scan['diagnostics']==[] and len(scan['edges'])==798
validations=[]
for (row,out,err),expected in zip(results[1:],[205,18]):
 text=(out+b'\n'+err).decode();counts=re.findall(r'^Ran (\d+) tests? in ([0-9.]+)s$',text,re.M);assert len(counts)==1 and int(counts[0][0])==expected and text.rstrip().endswith('OK')
 validations.append({**row,'exitCode':0,'tests':expected,'passed':expected,'failed':0,'skipped':0,'unittestSeconds':float(counts[0][1])})
# Same-source, normal assertion proof of the exact nine strengthened guards.
probe=Path('/workspace/geo337-U-architecture-policy-proof-20261024/probe.py').read_text();(O/'tools'/'policy_probe.py').write_text(probe);withdrawn=O/'withdrawn-manifest.json';withdrawn.write_bytes(previous_manifest_raw);proof=[]
for name in sorted(ADDED):
 for phase,path in [('fixed',R/ART/NAMES[0]),('withdrawn',withdrawn),('restored',R/ART/NAMES[0])]:
  row,out,err=run(['python3','-B','-c',probe,str(R),str(path),name,'protected'],check=False,variant='same-source exact W guard '+phase);expected=1 if phase=='withdrawn' else 0;assert row['actual_process_returncode']==expected
  if phase=='withdrawn':assert b'AssertionError: new W identifier must be rejected from K:' in err and json.loads(out)['diagnostics']==[]
  else:assert not err
  proof.append({'identifier':name,'phase':phase,'exit':expected,'directory':row['directory']})
for path in [withdrawn,R/ART/NAMES[0]]:run(['python3','-B','-c',probe,str(R),str(path),'geo261_architecture_neutral_probe','neutral'])
assert snapshot()==before and protected=={n:info(R/n) for n in protected} and tools=={n:info(R/n)['lfSha256'] for n in JUDGES}
assert all((R/ART/n).read_bytes()==old_four[n] for n in NAMES);assert git('rev-parse','HEAD').decode().strip()==F and not git('status','--porcelain=v1','--untracked-files=all')
old_inputs={x['path']:x['sha256'] for x in prior['inputs']};assert set(old_inputs)==set(declared);changed=[x for x in inputs if old_inputs[x['path']]!=x['sha256']]
counts={'executableFiles':604,'ownedSources':334,'exclusions':270,'edges':798,'diagnostics':0,'layers':dict(sorted(collections.Counter(x['layer'] for x in manifest['sources']).items())),'languages':dict(sorted(collections.Counter(x['language'] for x in manifest['sources']).items())),'forbiddenIdentifiers':937,'forbiddenStrings':55}
report=f'''# Product architecture — integration train fixed-source receipt

產品／裁判實際來源 `{F}`。三條原命令 exit 0／0／0；generic 205、product 18，零 skip。完整604 inputs、334 owned／270 exclusions、798 edges／0 diagnostics。LF closure `{closure}`。來源 HEAD、604個Git blob／raw／LF、三個裁判及兩份 SSOT 前後不變。

原完整 W lexer 盤點補9個已存在的 Reading A identifiers：forbiddenIdentifiers 928→937，forbiddenStrings維持55；舊guard全留，其餘manifest分類、路徑、exclusion、trust及政策全部相同。九組原scanner guard assertion在同一來源各0／1／0，兩個neutral probe通過；沒有用舊來源結果移標。

前份收據 source `{prior['sourceBaseHead']}`，產物提交 `{old_commit}`；本次完整輸入差異在 receipt／source-inputs.json，歷史報告保於該Git提交。四檔寫至來源外，receipt不hash自己。原native／browser／mutation ledger／效能需各自原收據，本四檔不代稱它們通過。
'''
new=O/'new';(new/NAMES[0]).write_bytes(old_four[NAMES[0]]);(new/NAMES[1]).write_bytes(results[0][1]);(new/NAMES[2]).write_text(report)
receipt={k:prior[k] for k in ['schema','hashMode','inputClosureHashSerialization','inputClosureExcludes','inputClosureExclusionReason','notClaimed']}
receipt.update(headBinding='All commands executed at the same clean source SHA; four derived outputs written outside source and excluded from executable closure.',createdUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),basis='Original Linux receipt schema, full Git/blob inventory and original judges; nine additive W guards only.',sourceBaseHead=F,headObservedBefore=F,headObservedAfter=F,manifestSha256=H(LF(old_four[NAMES[0]])),scannerSha256=tools[JUDGES[0]],scanSha256=H(LF(results[0][1])),reportSha256=H(LF((new/NAMES[2]).read_bytes())),inputClosureSha256=closure,counts=counts,scanPassed=True,actualCliScan={**results[0][0],'exitCode':0},validation=validations,inputs=inputs)
receipt['manifestRefresh']={'manifestByteUnchangedFromExecutionSource':True,'allPolicyFieldsEqualToPrevious':False,'onlyPolicyDelta':{'addedIdentifiers':sorted(ADDED),'removedIdentifiers':[],'otherManifestFieldsEqual':True},'sourceClassificationsUnchanged':True,'previousSource':prior['sourceBaseHead'],'previousArtifactCommit':old_commit,'previousOutputs':{n:info(O/'previous-artifact'/n) for n in NAMES},'executionSourceOutputs':{n:info(O/'execution-source-originals'/n) for n in NAMES},'changedPriorInputs':changed,'sourceReceiptEvidenceDirectory':str(O),'originalThreeGateExits':[0,0,0],'manifestProof':proof,'note':'No inherited proof relabeled. Nine controls execute at this source; original policy is withdrawn outside source.'}
receipt['completeInventoryVerification']={'sourceRoots':manifest['sourceRoots'],'sourceFiles':manifest['sourceFiles'],'filesBefore':604,'filesAfter':604,'allRawAndLfInputsUnchanged':True,'toolHashesBefore':tools,'toolHashesAfter':tools,'inputClosureSha256Before':closure,'inputClosureSha256After':closure,'protectedSsotBefore':protected,'protectedSsotAfter':protected}
receipt['supplementalStaticGuardProbes']={'executedAtCurrentHead':True,'newIdentifiers':9,'fixedWithdrawnRestored':[0,1,0],'neutralCases':2,'legacyWindowsSupplementalExecuted':False};receipt['nativeAcceptance']='Separate original receipts required; this architecture receipt does not certify runtime behavior.'
receipt['refreshDriver']={**info(Path(__file__)),'path':str(Path(__file__)),'argv':sys.argv,'recorderSha256':CAP_PIN,'runDirectory':str(O)};receipt['environment']={'safeVariables':results[0][0]['environment'],'clearedInheritedEnvironmentNames':cleared,'python':sys.version};receipt['uncertainties']=['Full native/browser/ledger and performance results are separate gates.','Generated outputs remain external until separately committed and pushed.']
cap.dump(new/NAMES[3],receipt);cap.dump(O/'RESULT.json',{'sourceSHA':F,'sourceBeforeAfterClean':True,'originalGateExits':[0,0,0],'newGuardProofExits':[0,1,0],'newGuardCases':9,'inputCount':604,'changedPriorReceiptInputs':changed,'inputClosureSHA256':closure,'outputs':{n:info(new/n) for n in NAMES},'sourceCheckoutModified':False,'ledgerRegenerated':False});print(json.dumps({'source':F,'gates':[0,0,0],'proofs':9,'result':str(O/'RESULT.json')}))
