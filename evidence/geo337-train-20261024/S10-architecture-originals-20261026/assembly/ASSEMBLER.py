"""Assemble four S10 artifacts from closed original gates; never rerun judges.
Root executes only after the full-ledger lease ends. Old H inventory/hash/schema
is retained; source snapshots are new, original gate execution timestamps are not.
"""
from pathlib import Path
import argparse,collections,contextlib,datetime,fcntl,hashlib,importlib.util,json,os,re,resource,stat,sys

SOURCE='82c922a3941525d3a094ac0158bdc7dea57ea360'
PRIOR='6e50aef65513b7b38f93228919272c6d40d6c196'
ADOPTION='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
ROOT=OWN/'F10-pool'
GATES=OWN/'S10-preledger-checks-original-20261025'
PREP=OWN/'F10-source-preparation-reserve-anchor'
ART='geometry-core/domain-decoupling'
NAMES=['product-architecture.json','product-architecture-scan.json','PRODUCT-ARCHITECTURE.md','product-architecture-receipt.json']
JUDGES=['tests/architecture_contract.py','tests/test_architecture_contract.py','tests/test_product_architecture.py']
SUFFIXES={'.c','.cc','.cjs','.cpp','.cxx','.h','.hh','.hpp','.htm','.html','.inc','.js','.jsx','.mjs','.py','.ts','.tsx'}
OLD=Path('/tmp/geo337-h-architecture-four-20261025')
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_PIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
MANIFEST_PIN='81882184010b5ddb9aa8e8d45467be788a65a79b378037ba6c99268f99bfa975'
SCAN_PIN='18f24f186445928e79159bbd49dc10b586a42ab17ded1cf15f2608de4354a728'
PRIOR_FOUR_PINS=[MANIFEST_PIN,SCAN_PIN,'fa1357b249c19708824d480993a80821b7bfeccb7606be773a000395f28aafd6','00a33c42ca07a9077aa5abf758ed8b0a3650a031cdc8387128f285050b7c13af']
GATES_PIN='0d592b7c18749bf36d162e82be4d586e7aa017b4eca22695402d9d686d4788f3'
GATE_PEER=Path('/workspace/geo337-S10-preledger-actual-peer-20261025/REVIEW.json')
GATE_PEER_PIN='1f945f9e84d04fe74c807388dc95d4076ff6ad814ac35e2fb93ff465efbaafd3'
SOURCE_PEER=Path('/workspace/geo337-S10-source-preparation-actual-peer-20261025/REVIEW.json')
SOURCE_PEER_PIN='c01f6d7337297ad36f617eecf1c9067cbb4bf9ce53ba4dd942930c723d38c1ed'
SOURCE_MANIFEST_PIN='e919aab396841642d093495b6fa7c7f4a20f55e1557929471dd6b2a81065057a'
PRIOR_SNAPSHOT_PIN='ee4eced205432217111ba597f565128ae598f87246c0cc3cc6d9194b52f59618'
PROTECTED_PINS={'公理層.md':'c66c48e50e0caceef42721c79700365f090f5c48d297abba41993eeb40dba9b7','決策佇列.md':'fe822051b5413fb79490b333e23f3c9d6b96959c01f937c274d3246772c15e14'}

def H(b):return hashlib.sha256(b).hexdigest()
def LF(b):return b.replace(b'\r\n',b'\n')
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def info(p):
 b=p.read_bytes();return {'bytes':len(b),'rawSha256':H(b),'lfSha256':H(LF(b))}
def pinned(p,pin):
 b=p.read_bytes();need(H(b)==pin,'fixed original bytes: '+str(p));return b
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def validate_gate(row,rawout,rawerr,number):
 expected=[['tests/architecture_contract.py','--root','.','--manifest',ART+'/'+NAMES[0]],['tests/test_architecture_contract.py'],['tests/test_product_architecture.py']][number]
 need(row['command'][1:]==['-B',*expected],'original exact judge argv')
 need(row['source_sha']==row['acceptance_sha']==SOURCE and row['cwd']==str(ROOT),'original gate execution source and cwd')
 need(row['actual_process_returncode']==0 and row['timeout_expired'] is False,'original gate must have real zero exit')
 need(row['stdout_sha256']==H(rawout)and row['stderr_sha256']==H(rawerr),'original full gate stream hashes')
 need(row['stdout_bytes']==len(rawout)and row['stderr_bytes']==len(rawerr),'original full gate stream sizes')
 need(row['ended_epoch']>=row['started_epoch'],'original gate times')
 if number==0:
  scan=json.loads(rawout);need(scan['ok']and scan['diagnostics']==[]and len(scan['edges'])==798,'original scan complete798/zero diagnostics');return scan
 text=(rawout+b'\n'+rawerr).decode();counts=re.findall(r'^Ran (\d+) tests? in ([0-9.]+)s$',text,re.M)
 expected_count=[205,18][number-1]
 need(len(counts)==1 and int(counts[0][0])==expected_count and text.rstrip().endswith('OK'),'original complete unittest count and zero skip')
 return {**row,'exitCode':0,'tests':expected_count,'passed':expected_count,'failed':0,'skipped':0,'unittestSeconds':float(counts[0][1])}

def validate_inputs(before,prior,inputs):
 need(len(before)==len(prior)==len(inputs)==604,'complete604 snapshots')
 need(len({x['path']for x in before})==604 and before==prior,'S10 must have zero raw/LF/Git604 input changes')
 need(inputs==[{'path':x['path'],'sha256':x['lfSha256']}for x in before],'complete ordered604 LF inputs')

def historical_probes(prior):
 need(prior['sourceBaseHead']==PRIOR,'historical actual execution M6e50')
 return {'executedAtCurrentHead':False,'newIdentifiers':0,'guardIdentifiersRetested':0,'neutralCases':0,'legacyWindowsSupplementalExecuted':False,
         'historicalExecutionSource':PRIOR,'historicalAdoptionCommit':ADOPTION,'historicalReceiptRawSha256':PRIOR_FOUR_PINS[3],
         'historicalSupplementalStaticGuardProbes':prior['supplementalStaticGuardProbes'],
         'note':'Nine0/1/0 and two neutral controls are historical actual M6e50 results, not rerun or relabelled at S10.'}

def snapshot(R,manifest,declared,tree):
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

def require_full_index(raw):
    """Validate SHA-1 DIRC bytes, refusing the mandatory split-index link.

    rev-parse --shared-index-path depends on core.splitIndex and cannot prove
    that copied bytes have no link extension. Parse only to locate extensions.
    """
    need(len(raw)>=32 and raw[:4]==b'DIRC','complete native Git index header')
    need(hashlib.sha1(raw[:-20]).digest()==raw[-20:],'native index checksum')
    version=int.from_bytes(raw[4:8],'big');count=int.from_bytes(raw[8:12],'big')
    need(version in (2,3,4),'supported full index version')
    end=len(raw)-20;off=12
    for unused in range(count):
        start=off
        need(off+62<=end,'complete index entry')
        flags=int.from_bytes(raw[off+60:off+62],'big');off+=62
        if flags&0x4000:
            need(version>=3 and off+2<=end,'valid extended index flags');off+=2
        if version==4:
            while True:
                need(off<end,'complete index v4 prefix varint')
                byte=raw[off];off+=1
                if not byte&0x80:break
        nul=raw.find(b'\0',off,end);need(nul>=off,'complete index path');off=nul+1
        if version in (2,3):
            padded=off+(-(off-start)%8)
            need(padded<=end and raw[off:padded]==b'\0'*(padded-off),'index entry padding');off=padded
    extensions=[]
    while off<end:
        need(off+8<=end,'complete index extension header')
        signature=raw[off:off+4];size=int.from_bytes(raw[off+4:off+8],'big');off+=8
        need(off+size<=end,'complete index extension payload')
        need(signature!=b'link','original split index is unsupported; never convert it in place')
        extensions.append(signature.hex());off+=size
    need(off==end,'index extension boundary')
    return dict(version=version,entries=count,extensions=extensions,sha256=H(raw))

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--sha',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--root-execution-lease',action='store_true');a=p.parse_args()
 need(a.root_execution_lease,'root must schedule after full123 lease ends')
 need(not sys.flags.optimize and a.sha==SOURCE and a.root==ROOT,'fixed S10 original source only')
 O=a.out;R=a.root
 need(O.is_absolute()and O==O.resolve()and O.parent==OWN and not O.exists(),'fresh direct OWN output child')
 need(O not in [ROOT,OWN/'F10-cache']and not R.is_relative_to(O),'output must not overlap source/cache')
 need(resource.getrlimit(resource.RLIMIT_STACK)[0]==16777216,'original16MiB stack')
 with contextlib.ExitStack()as stack:
  for path in ['/tmp/g261r3/heavy.lock','/tmp/g261r3/secondary.lock']:
   f=Path(path);st=f.lstat();need(stat.S_ISREG(st.st_mode)and st.st_uid==os.getuid(),'existing owned scheduler lock')
   fd=stack.enter_context(f.open('r+b'));need((os.fstat(fd.fileno()).st_dev,os.fstat(fd.fileno()).st_ino)==(st.st_dev,st.st_ino),'lock identity');fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  # No source read precedes the explicit lease and both nonblocking locks.
  O.mkdir();(O/'new').mkdir();(O/'previous-artifact').mkdir();(O/'original-gates').mkdir();(O/'tmp').mkdir()
  (O/'ASSEMBLER.py').write_bytes(Path(__file__).read_bytes())
  result={'sourceSHA':SOURCE,'exit_code':1,'originalJudgesRerun':False,'formalLedgerOrNativeExecuted':False,'sourceCheckoutModified':False}
  try:
   pinned(CAP,CAP_PIN);sp=importlib.util.spec_from_file_location('original_capture',CAP);cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap)
   env={k:v for k,v in os.environ.items()if not k.startswith(('GIT_','GEOMETRY_','MUTATE_'))and k not in ('PYTHONOPTIMIZE','PYTHONPATH','PYTHONSTARTUP','NODE_OPTIONS')}
   env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',LANG='C.UTF-8',LC_ALL='C.UTF-8',TMPDIR=str(O/'tmp'),TMP=str(O/'tmp'),TEMP=str(O/'tmp'),GIT_OPTIONAL_LOCKS='0')
   rec=cap.Recorder(O,env,SOURCE)
   def git(*args):return rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=R,timeout=None,check=True,source_sha=SOURCE,source_variant='architecture assembly identity; no judge rerun')[1]
   # Real index stays unchanged: status uses a private exact full-index copy.
   index=Path(git('rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute()else R/index
   index_before=index.read_bytes();index_stat=index.stat();require_full_index(index_before)
   (O/'private-index').write_bytes(index_before)
   env.update(GIT_INDEX_FILE=str(O/'private-index'),GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='core.splitIndex',GIT_CONFIG_VALUE_0='false')
   dump(O/'GIT_ENVIRONMENT.json',{k:v for k,v in env.items()if k.startswith('GIT_')})
   need(git('rev-parse','HEAD').decode().strip()==SOURCE and not git('status','--porcelain=v1','--untracked-files=all'),'current source exact clean S10')
   gate_peer=json.loads(pinned(GATE_PEER,GATE_PEER_PIN));source_peer=json.loads(pinned(SOURCE_PEER,SOURCE_PEER_PIN));need(gate_peer['exit_code']==source_peer['exit_code']==0,'closed source/gate actual peers')
   gate_raw=pinned(GATES/'RESULT.json',GATES_PIN);batch=json.loads(gate_raw);(O/'original-gates'/'batch-RESULT.json').write_bytes(gate_raw)
   need(batch['source_sha']==SOURCE and batch['before']==batch['after']and batch['before']['head']==SOURCE and not batch['before']['status'],'closed original batch clean source identity')
   need([x['exit_code']for x in batch['gates']]==[1,0,0,0,0,0]and not batch['all_gates_passed'],'original stale check preserved separately')
   original=[]
   for number,g in enumerate(batch['gates'][1:4]):
    c=g['command'];d=GATES/'subcommands'/f'{number+5:06d}';need(c['directory']==str(d),'fixed closed gate directory')
    payload={n:(d/n).read_bytes()for n in ['request.json','result.json','stdin.bin','stdout.bin','stderr.bin']}
    row=json.loads(payload['result.json']);request=json.loads(payload['request.json']);need(row==c,'original subcommand result matches batch')
    for key,value in request.items():
     if key=='actual_process_returncode':need(value is None,'request records prelaunch state')
     else:need(row[key]==value,'request/result original binding '+key)
    need(H(payload['stdin.bin'])==row['stdin_sha256'],'full original stdin')
    observed=validate_gate(row,payload['stdout.bin'],payload['stderr.bin'],number)
    copied=O/'original-gates'/d.name;copied.mkdir()
    for n,b in payload.items():(copied/n).write_bytes(b)
    original.append((row,payload['stdout.bin'],payload['stderr.bin'],observed))
   old_four={n:(R/ART/n).read_bytes()for n in NAMES}
   for n,pin in zip(NAMES,PRIOR_FOUR_PINS):
    need(H(old_four[n])==pin,'prior four exact bytes '+n);(O/'previous-artifact'/n).write_bytes(old_four[n])
    need(git('show',ADOPTION+':'+ART+'/'+n)==old_four[n],'prior adoption Git bytes '+n)
   prior=json.loads(old_four[NAMES[3]]);manifest=json.loads(old_four[NAMES[0]])
   need(prior['schema']=='geometry-product-architecture-receipt/1'and prior['sourceBaseHead']==PRIOR,'original receipt schema and actual prior execution')
   git('merge-base','--is-ancestor',ADOPTION,SOURCE)
   source_manifest=json.loads(pinned(PREP/'SOURCE_MANIFEST.json',SOURCE_MANIFEST_PIN));need(source_manifest['source_sha']==SOURCE,'source preparation exact SHA')
   declared=sorted(x['path']for key in ['sources','exclusions']for x in manifest[key]);need(len(declared)==len(set(declared))==604 and set(declared)==set(source_manifest['architecture_paths']),'complete manifest/sourceprep604')
   need(len(manifest['sources'])==334 and len(manifest['exclusions'])==270 and len(manifest['policy']['forbiddenIdentifiers'])==937 and len(manifest['policy']['forbiddenStrings'])==55,'unchanged classifications/policy counts')
   rawtree=git('ls-tree','-r','-z',SOURCE,'--',*manifest['sourceRoots'],*manifest['sourceFiles']);tree={}
   for entry in rawtree.split(b'\0'):
    if not entry:continue
    meta,name=entry.split(b'\t',1);mode,kind,oid=meta.split();path=name.decode()
    if Path(path).suffix.lower()in SUFFIXES:need(kind==b'blob'and mode in (b'100644',b'100755'),'regular inventory blob');tree[path]=oid.decode()
   need(sorted(tree)==declared and all(source_manifest['files'][n]['oid']==tree[n]for n in declared),'independent Git tree/declared/sourceprep exact closure')
   before=snapshot(R,manifest,declared,tree);inputs=[{'path':x['path'],'sha256':x['lfSha256']}for x in before]
   prior_snapshot=json.loads(pinned(OLD/'source-inputs.json',PRIOR_SNAPSHOT_PIN));validate_inputs(before,prior_snapshot,inputs)
   need(inputs==prior['inputs'],'prior receipt complete604 LF inputs');closure=H(json.dumps(inputs,ensure_ascii=False,separators=(',',':')).encode());need(closure==prior['inputClosureSha256'],'unchanged604 LF closure');dump(O/'source-inputs.json',before)
   protected={n:info(R/n)for n in PROTECTED_PINS};tools={n:info(R/n)['lfSha256']for n in JUDGES}
   for n in protected:need(protected[n]['rawSha256']==PROTECTED_PINS[n]and H(git('show',SOURCE+':'+n))==PROTECTED_PINS[n],'protected S10 SSOT bytes')
   for n in JUDGES:need(H(LF(git('show',SOURCE+':'+n)))==tools[n]==prior['completeInventoryVerification']['toolHashesBefore'][n],'unchanged original judge bytes')
   scan=original[0][3];scan_raw=original[0][1];need(H(scan_raw)==SCAN_PIN and scan_raw==old_four[NAMES[1]],'original scan bytes unchanged; never reformat')
   probes=historical_probes(prior);new=O/'new'
   report=f'''# Product architecture — S10 original-gate receipt assembly

產品／裁判實際來源 `{SOURCE}`。使用本輪已封閉三原命令exit0／0／0（generic205、product18、零skip），沒有重跑三裁判。完整604 inputs、334 owned／270 exclusions、798 edges／0 diagnostics；LF closure `{closure}`。manifest與原scan逐byte不變，937 identifiers／55 strings政策不變。

604輸入相對真正前次執行 `{PRIOR}` 零差異；前四檔採入提交 `{ADOPTION}`。本次改動的test_geo314_commit_paths.py與決策不在604inputs，帳本仍須另完整重產。公理層快照不變；決策新快照SHA256 `{PROTECTED_PINS['決策佇列.md']}`，為已授權normal merge逐字合入。

原三judge執行時間/環境完整保留於receipt，604/raw/LF/Git/tool/SSOT快照是在本組裝階段重新採集並前後比對，不能冒作同時點快照。歷史9組0／1／0及2 neutral controls仍屬M6e50，未在S10重跑或移標。四檔寫於來源外，receipt不hash自己；native、browser、全帳本與performance各需獨立原收據。
'''
   (new/NAMES[0]).write_bytes(old_four[NAMES[0]]);(new/NAMES[1]).write_bytes(scan_raw);(new/NAMES[2]).write_text(report)
   counts={'executableFiles':604,'ownedSources':334,'exclusions':270,'edges':798,'diagnostics':0,'layers':dict(sorted(collections.Counter(x['layer']for x in manifest['sources']).items())),'languages':dict(sorted(collections.Counter(x['language']for x in manifest['sources']).items())),'forbiddenIdentifiers':937,'forbiddenStrings':55}
   receipt={k:prior[k]for k in ['schema','hashMode','inputClosureHashSerialization','inputClosureExcludes','inputClosureExclusionReason','notClaimed']}
   receipt.update(headBinding='Original three judges executed at S10; later same-source snapshot and four-file assembly are explicitly separate; no rerun or source relabelling.',createdUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),basis='Original Linux inventory/hash/schema; closed S10 original gates; unchanged937 manifest and scan.',sourceBaseHead=SOURCE,headObservedBefore=SOURCE,headObservedAfter=SOURCE,manifestSha256=H(LF(old_four[NAMES[0]])),scannerSha256=tools[JUDGES[0]],scanSha256=H(LF(scan_raw)),reportSha256=H(LF((new/NAMES[2]).read_bytes())),inputClosureSha256=closure,counts=counts,scanPassed=True,actualCliScan={**original[0][0],'exitCode':0},validation=[x[3]for x in original[1:]],inputs=inputs)
   receipt['manifestRefresh']={'manifestByteUnchangedFromExecutionSource':True,'scanByteUnchangedFromExecutionSource':True,'allPolicyFieldsEqualToPrevious':True,'onlyPolicyDelta':{'addedIdentifiers':[],'removedIdentifiers':[],'otherManifestFieldsEqual':True},'sourceClassificationsUnchanged':True,'previousSource':PRIOR,'previousArtifactCommit':ADOPTION,'previousOutputs':{n:info(O/'previous-artifact'/n)for n in NAMES},'changedPriorInputs':[],'sourceReceiptEvidenceDirectory':str(O),'originalThreeGateExits':[0,0,0],'manifestProof':[],'historicalGuardEvidence':{'source':PRIOR,'artifactCommit':ADOPTION,'receiptRawSha256':PRIOR_FOUR_PINS[3]},'note':'No inherited proof relabelled; current three gate records are original S10 executions; supplemental proofs remain historical.'}
   receipt['completeInventoryVerification']={'sourceRoots':manifest['sourceRoots'],'sourceFiles':manifest['sourceFiles'],'filesBefore':604,'filesAfter':604,'allRawAndLfInputsUnchanged':True,'toolHashesBefore':tools,'toolHashesAfter':tools,'inputClosureSha256Before':closure,'inputClosureSha256After':closure,'protectedSsotBefore':protected,'protectedSsotAfter':protected,'snapshotTiming':'Fresh assembly before/after, after original gate terminal; not concurrent with original three gate execution.'}
   receipt['supplementalStaticGuardProbes']=probes;receipt['nativeAcceptance']=prior['nativeAcceptance']
   receipt['refreshDriver']={**info(Path(__file__)),'path':str(Path(__file__)),'argv':sys.argv,'recorderSha256':CAP_PIN,'runDirectory':str(O),'originalThreeGateBatch':str(GATES),'originalThreeGateBatchSha256':GATES_PIN,'originalGatePeerSha256':GATE_PEER_PIN,'sourcePrepPeerSha256':SOURCE_PEER_PIN,'originalJudgesRerun':False}
   receipt['environment']={'originalGateEnvironment':original[0][0]['environment'],'assemblyPython':sys.version,'assemblyGitEnvironment':{k:v for k,v in env.items()if k.startswith('GIT_')}}
   receipt['uncertainties']=['Original gates and assembly snapshots are separate execution times at the same source SHA.','Nine controls and two neutral probes remain historical actual M6e50.','Full native/browser/ledger/performance are separate gates; generated outputs require separate normal commit/push.']
   need(snapshot(R,manifest,declared,tree)==before and protected=={n:info(R/n)for n in protected}and tools=={n:info(R/n)['lfSha256']for n in JUDGES},'all assembly source/tool/SSOT snapshots unchanged')
   need(all((R/ART/n).read_bytes()==old_four[n]for n in NAMES),'source four artifacts untouched')
   need(git('rev-parse','HEAD').decode().strip()==SOURCE and not git('status','--porcelain=v1','--untracked-files=all'),'source remains clean exactS10')
   st=index.stat();need(index.read_bytes()==index_before and (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(index_stat.st_dev,index_stat.st_ino,index_stat.st_size,index_stat.st_mtime_ns),'real source index unchanged')
   dump(new/NAMES[3],receipt)
   result.update(exit_code=0,originalGateExits=[0,0,0],inputCount=604,changedPriorReceiptInputs=[],historicalProbesReexecuted=False,inputClosureSHA256=closure,originalGateBatchSha256=GATES_PIN,sourceBeforeAfterClean=True,outputs={n:info(new/n)for n in NAMES},changedArtifacts=[n for n in NAMES if(new/n).read_bytes()!=old_four[n]])
   need(result['changedArtifacts']==NAMES[2:],'only report/receipt changed');dump(O/'RESULT.json',result);return 0
  except BaseException as e:
   result['exit_code']=1;result['error']=repr(e);dump(O/'RESULT.json',result);raise

if __name__=='__main__':raise SystemExit(main())
