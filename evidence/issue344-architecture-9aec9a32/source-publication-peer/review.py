from pathlib import Path
import hashlib,json,subprocess,datetime
O=Path(__file__).parent;P=Path('/tmp/geo344-manifest-source-publication-20261025');G='/workspace/geometry-axiom'
B='a5ec136baf3909453867b3eed50f1b93b229ca59';S='9aec9a32630fc65f94c53d49e99969e546574d6e';L='geometry-core/domain-decoupling/product-architecture.json';BR='codex/issue320-connection-recovery-20261024'
N=0;failed=[]
def h(b):return hashlib.sha256(b).hexdigest()
def ck(v,msg):
 global N
 N+=1
 if not v:failed.append(msg)
def git(*a):
 r=subprocess.run(['git','-C',G,*a],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 ck(r.returncode==0,'readonly Git '+str(a));return r.stdout
q=json.loads((P/'RESULT.json').read_bytes());rows=json.loads((P/'subcommands.json').read_bytes())
ck(q['exit_code']==0 and q['source_sha']==S and q['parent']==B and q['branch']==BR,'result source bindings')
ck(q['formal_architecture']=='UNRUN' and q['strict9']=='not rerun' and q['browser']=='not rerun','no formal claim')
ck(len(rows)==21==q['commands'],'21 original CLI')
for i,r in enumerate(rows,1):
 d=P/'subcommands'/f'{i:06d}'
 ck(Path(r['directory'])==d,'command directory')
 ck(r['actual_process_returncode']==0 and not r['timeout_expired'],'original command exit')
 ck(r['cwd']=='/workspace/issue320-work-20261024','owned root')
 ck(json.loads((d/'result.json').read_bytes())==r,'result exact row')
 req=json.loads((d/'request.json').read_bytes());ck(req['command']==r['command'],'request original argv')
 for kind in ['stdin','stdout','stderr']:
  b=(d/(kind+'.bin')).read_bytes();ck(h(b)==r[kind+'_sha256'],'raw stream hash '+kind)
  if kind!='stdin':ck(len(b)==r[kind+'_bytes'],'stream size '+kind)
 ck(r['environment']['PYTHONOPTIMIZE'] is None,'subprocess no Python optimize')
def stdout(i):return (P/'subcommands'/f'{i:06d}'/'stdout.bin').read_bytes()
ck(stdout(1).decode().strip()==B and stdout(2).decode().strip()==BR,'initial identity')
ck(stdout(4).decode().split()==[B,'refs/heads/'+BR],'old remote')
ck(stdout(21).decode().split()==[S,'refs/heads/'+BR],'new remote original')
ck(all(stdout(i)==b'' for i in [3,8,19]),'three original clean status')
ck(stdout(16).decode().strip()==S and stdout(17).decode().strip()==B,'new commit and parent original')
ck(stdout(12).decode().splitlines()==[L] and stdout(18).decode().splitlines()==[L],'only manifest original')
ck(rows[19]['command']==['git','push','origin','HEAD:refs/heads/'+BR],'normal push no force')
ck(rows[14]['command']==['git','commit','-m','fix(architecture): refresh recovery test exclusion digest'],'English commit')
ck((P/'sparse-after.bin').read_bytes().splitlines()!=[],'sparse captured')
ck(set((P/'sparse-after.bin').read_bytes().splitlines())==set((P/'sparse-before.bin').read_bytes().splitlines())|{('/'+L).encode()},'only sparse manifest materialized')
old=git('show',B+':'+L);new=git('show',S+':'+L)
ck(h(old)=='81882184010b5ddb9aa8e8d45467be788a65a79b378037ba6c99268f99bfa975','old manifest hash')
ck(h(new)=='f0c0b4db4ca01d4825883b73d73bf8644af313cd2bcab4c9b23638b9bbd93d32'==q['manifest_sha256'],'committed new manifest hash')
a=b'bb66742aa10b603b84362277f9f2c4275da8904925e75c618f252bd7df42cc3e';b=b'1f3e2e36283ed7bbf6c4ad2cf3dc12c685667356d186d9fbd47bc5f0520f07ee'
ck(old.count(a)==1 and old.replace(a,b)==new,'exact single LF digest substitution')
cdp=git('show',S+':geometry-web/cdp_test.js');ck(h(cdp.replace(b'\r\n',b'\n'))==b.decode(),'actual source CDP LF digest')
ck(git('diff-tree','--no-commit-id','--name-only','-r',S).decode().splitlines()==[L],'current object exact only leaf')
ck(git('rev-parse',S+'^').decode().strip()==B,'current object parent')
ck(h((P/'capture.py').read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762','original recorder')
ck(h((P/'fix-exclusion-digest.patch').read_bytes())=='73c0379d0860a84032257092d8c46d5eb7702b7f0400ccfcd3ab9e4ec91f236f','original reviewed patch')
r={'exit_code':0 if not failed else 1,'checks':N,'failed_checks':failed,'source_sha':S,'parent_sha':B,'original_commands':21,'normal_push_verified_from_original':True,'changed_paths':[L],'manifest_sha256':h(new),'original_result_sha256':h((P/'RESULT.json').read_bytes()),'recorded_driver_sha256':h((P/'PREPARER.py').read_bytes()),'formal_architecture':'UNRUN','tests_rerun':False,'limitations':['Source publication review only; does not replace #344 architecture judges/counterfactual/browser gates.','Captured original ls-remote proves the pushed head at publication time; no new network request or branch mutation performed.','Original driver is assertion-based; reported root startup was python3 -B without -O. Child command environments preserve PYTHONOPTIMIZE=None. Startup claim is not independently inferred from child environments.','Existing absolute git-path outputs were used. No claim about portability to a relative git-path layout.'],'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(O/'REVIEW.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False));assert r['exit_code']==0
