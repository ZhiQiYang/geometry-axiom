from pathlib import Path
import ast,datetime,difflib,hashlib,json,subprocess,sys
sys.dont_write_bytecode=True
P=Path('/tmp/geo337-F8-memo-counterfactual-tools-v2-20261025');V1=Path('/tmp/geo337-F8-memo-counterfactual-tools-20261025');O=Path(__file__).parent
h=lambda b:hashlib.sha256(b).hexdigest();checks=[];errors=[];commands=[]
def ck(n,v):
 checks.append({'id':n,'passed':bool(v)})
 if not v:errors.append(n)
def git(args):
 cmd=['git','-C','/workspace/geometry-axiom']+args;r=subprocess.run(cmd,capture_output=True);i=len(commands);(O/f'git-{i}.stdout').write_bytes(r.stdout);(O/f'git-{i}.stderr').write_bytes(r.stderr);commands.append({'argv':cmd,'exit':r.returncode,'stdout_sha256':h(r.stdout),'stderr_sha256':h(r.stderr)});ck('readonly-Git-'+str(i),r.returncode==0);return r.stdout
prep=json.loads((P/'PREPARATION.json').read_bytes());cf=json.loads((P/'COUNTERFACTUAL.json').read_bytes());bindings=json.loads((P/'R8_ELF_COPY_BINDINGS.json').read_bytes());source=(P/'run.py').read_text();ck('prep-pin',h((P/'PREPARATION.json').read_bytes())=='cee50f54e8c28b059c17a223091a2780b7268406d14474c200869a5fd3ed53bd');ck('run-pin',h(source.encode())=='bb255e134528642cc53629e267f4cf2a35bcf958615b57aa1b0b6ee959b4857b')
for item in prep['files']:
 b=(P/item['path']).read_bytes();ck('prepared-'+item['path'],len(b)==item['bytes'] and h(b)==item['sha256'])
ck('formal-UNRUN',prep['formal_executed'] is False and prep['R8_ELF_payload_read_or_copied'] is False)
F8=cf['source_F8'];F7=cf['historical_fixed_F7'];H=cf['historical_withdrawn_H'];blob={}
for label,sha in [('F8',F8),('F7',F7),('H',H)]:
 for path in cf['changed_source_paths']:
  b=git(['show',sha+':'+path]);blob[label,path]=b;ck('real-Git-source-'+label+'-'+path,b==(P/'metadata'/(label+'-'+path.replace('/','__'))).read_bytes() and h(b)==cf['file_bindings'][path][label+'_sha256'])
m={};exec(compile((P/'memo_variant.py').read_bytes(),str(P/'memo_variant.py'),'exec'),m)
for path in cf['changed_source_paths']:
 fixed=blob['F8',path];withdrawn=m['withdraw_memo'](path,fixed);restored=m['restore_memo'](path,withdrawn);ck('exact-original-withdraw-restore-'+path,h(withdrawn)==cf['file_bindings'][path]['withdrawn_sha256'] and restored==fixed)
 if path=='geometry-core/references.inc':
  def segment(raw):return raw.split(b'static bool reference_rebuild(World *w)\n{\n',1)[1].split(b'    ctx->world=w;',1)[0]
  before=segment(blob['F7',path]);after=segment(fixed);prior=blob['H',path];ck('H-plus-local-init-exact',prior.count(before)==1 and prior.replace(before,after,1)==withdrawn and withdrawn.count(m['LOCAL_INIT'])==1);ck('local-init-only-F7-F8',blob['F7',path].replace(before,after,1)==fixed)
 else:ck('F7-F8-app-identical-and-withdraw-H',blob['F7',path]==fixed and withdrawn==blob['H',path])
ck('exact-four-mechanical-edits',sum(len(x) for x in cf['mechanical_edits'].values())==4 and cf['mechanical_edits']==m['EDITS'])
for name,pin in cf['patches'].items():ck('patch-pin-'+name,h((P/'patches'/name).read_bytes())==pin)
for name in ['memo_variant.py','COUNTERFACTUAL.json','METADATA_PROOF.json']:
 ck('v1-v2-unchanged-'+name,(V1/name).read_bytes()==(P/name).read_bytes())
diff=''.join(difflib.unified_diff((V1/'run.py').read_text().splitlines(True),source.splitlines(True),fromfile=str(V1/'run.py'),tofile=str(P/'run.py')));ck('exact-copy-only-diff',diff==(P/'V1_TO_V2_COPY_ONLY.diff').read_text())
ck('same-F8-guard-kept',"assert a.sha==memo_variant.F8" in source and "formal['source_sha']==a.sha" in source and cf['formal_receipt_sha256'] in source)
ck('unchanged-original-numeric-criteria',"target='<=4.5',target_met=ratio<=4.5,criterion_exit=0 if ratio<=4.5 else 1" in source and "expected={'withdrawn':1,'restored':0,'abc':0}" in source and "v3.build(source,work/'fix-pg',profile=True)" in source and 'bound.Session.compare(session)' in source)
ck('no-original-ELF-link-now','os.link(' not in source and "elf_copy.copy_r8_binary('base-pg',src,dst)" in source and "elf_copy.copy_r8_binary(label,src,dst)" in source)
formalpath=Path(cf['formal_out'])/'receipt.json';fraw=formalpath.read_bytes();formal=json.loads(fraw);ck('true-R8-receipt-pin',h(fraw)==cf['formal_receipt_sha256']==prep['formal_receipt_sha256']);ck('actual-R8-same-F8-profile-green-exact-red',formal['source_sha']==F8 and formal['stages']['profile']['execution_exit']==0 and formal['stages']['compare']['execution_exit']==1 and 'ABC_result' not in formal and formal['quantitative_targets']['geo_eval_source_64_32']['actual']==cf['formal_profile_ratio'])
manifest=Path(bindings['original_manifest']).read_bytes();ck('original-ELF-hash-only-manifest-pin',h(manifest)==bindings['original_manifest_sha256']);manifest=json.loads(manifest);entries=manifest if isinstance(manifest,list) else manifest.get('files',manifest.get('excluded',[]))
# SourcePins derive from the existing manifest; do not open any real ELF body.
copy_scope={};exec(compile((P/'copy_r8_elf.py').read_bytes(),str(P/'copy_r8_elf.py'),'exec'),copy_scope)
ck('ELF-role-pins-equal',copy_scope['SOURCE_PINS']==bindings['selected_original_ELF'])
for label,want in bindings['selected_original_ELF'].items():ck('original-ELF-role-'+label,want in entries)
roles=bindings['selected_original_ELF'];total=roles['base-pg']['bytes']*2+roles['fix']['bytes']+roles['fix-trace']['bytes'];round4=lambda x:((x+4095)//4096)*4096;ck('copy-only-increment-not-total-budget',total==bindings['total_private_copy_bytes_two_basepg_plus_fix_trace']==4340968 and round4(roles['base-pg']['bytes'])*2+round4(roles['fix']['bytes'])+round4(roles['fix-trace']['bytes'])==bindings['allocated_4KiB_floor_bytes']==4349952)
for name,prefix in [('METADATA_PROOF.json',''),('COPY_METADATA_PROOF.json','copy-')]:
 j=json.loads((P/name).read_bytes());ck('proof-010-'+name,j['actual_exits']==[0,1,0] and not j['formal_executed'] and j['exit']==0)
 for i,row in enumerate(j['rows']):
  phase=row['phase'];out=(P/'metadata'/(prefix+phase+'.stdout.bin')).read_bytes();err=(P/'metadata'/(prefix+phase+'.stderr.bin')).read_bytes();ck('proof-original-streams-'+name+'-'+phase,h(out)==row['stdout_sha256'] and h(err)==row['stderr_sha256'] and row['actual_exit']==[0,1,0][i])
  if prefix and i!=1:
   z=json.loads(out.splitlines()[-1])['result'];ck('copy-fixed-distinct-original-preserved-'+phase,z['source_before']==z['source_after'] and z['different_inode'] and z['destination_nlink']==1 and z['bytes']==504 and z['original_bytes_preserved'])
ck('exact-local-init-negative-assertion',b'AssertionError: ASSERT:memo-counterfactual-retains-H-local-init' in (P/'metadata/withdraw-local-init-preservation.stderr.bin').read_bytes());ck('true-copy-negative-is-source-nlink-guard',b'RuntimeError: original R8 ELF metadata/bytes changed during copy' in (P/'metadata/copy-withdraw-copy-to-hardlink.stderr.bin').read_bytes())
# Metadata fixture lstat only. Original R8 ELF lstat/body deliberately not read.
for phase,want in [('fixed',False),('withdraw-copy-to-hardlink',True),('restored',False)]:
 d=P/'metadata'/('copy-fixture-'+phase);a=(d/'synthetic-original').stat();b=(d/'synthetic-copy').stat();ck('tiny-fixture-alias-state-'+phase,((a.st_dev,a.st_ino)==(b.st_dev,b.st_ino))==want and a.st_nlink==b.st_nlink==(2 if want else 1))
report={'schema':'F8-memo-copy-v2-static-and-metadata-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'subject':str(P),'preparation_sha256':h((P/'PREPARATION.json').read_bytes()),'checks':checks,'commands':commands,'passed':not errors,'exit':int(bool(errors)),'errors':errors,'formal_executed':False,'scope':'只審精確四處memo撤回/local-init保留、v2copy隔離、固定F8原Git bytes與既有小metadata原0/1/0；沒有編譯、profile、175ABC或原ELF payload讀取。','limits':['正式memo全部UNRUN，原R8跨版本exact三紅/compare1/ABC缺席不改。','root須另備獨立可寫cleanF8來源、原來源lease、完整source/build/profile/ABC空間與獨占排程；4.34MB僅copy增量。','保持原3phase預期1/0/0與4.5門檻，metadata綠不代正式反證。','若copy失敗，部分私有copy留原OUT記錄；不回寫或清除原ELF。']};(O/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(O/'REVIEW.json'),'sha256':h((O/'REVIEW.json').read_bytes()),'checks':len(checks),'exit':report['exit'],'errors':errors},ensure_ascii=False))
