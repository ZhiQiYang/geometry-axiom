from pathlib import Path
import ast,hashlib,json,subprocess,datetime
HERE=Path(__file__).parent
OLD=Path('/tmp/geo337-recover-evidence-publisher-20261026.py')
NEW=HERE/'publish_append.py'
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=ast.parse(OLD.read_bytes());new=ast.parse(NEW.read_bytes())
om=next(n for n in old.body if isinstance(n,ast.FunctionDef)and n.name=='main');nm=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name=='main')
def fun(m,name):return next(n for n in ast.walk(m)if isinstance(n,ast.FunctionDef)and n.name==name)
unchanged={n:ast.dump(fun(om,n))==ast.dump(fun(nm,n))for n in ['run','git','oid','snapshot','readtree']};assert all(unchanged.values())
oldsrc=OLD.read_text();newsrc=NEW.read_text();checks=[]
def ok(value,msg):assert value,msg;checks.append(msg)
ok(H(OLD)=='c6a44de7ada360b6017a0e578507b81867471f583d8e9b6b591d56581ba41368','original reviewed publisher pin unchanged')
for exact in ["total=sum(x['bytes'] for x in files);budget=total*3+len(files)*65536+len(raw)*8+64*1024*1024","need(used+budget<=2*1024**3,'combined original 2GiB planning bound')","need(shutil.disk_usage(OWN).free>budget,'actual mount capacity')","need(not git('diff','--name-only',a.expected_parent,commit,'--','.',':(exclude)evidence'),'product changed')","git('update-ref','refs/heads/'+BRANCH,commit,a.expected_parent)","git('push','https://github.com/ZhiQiYang/geometry-axiom.git','refs/heads/'+BRANCH+':refs/heads/'+BRANCH)","need(snapshot()==before,'existing writer changed after push')"]:ok(exact in newsrc,'required guard '+exact)
start="  checked={}\n";end="  need(snapshot()==before,'existing writer changed after push')"
ok(oldsrc[oldsrc.index(start):oldsrc.index(end)]==newsrc[newsrc.index(start):newsrc.index(end)],'entire remote full-bytes hash/OID verifier unchanged')
ok("HEAD='3e4f2560aa11ed2a626db98ba5ed6f129e791052'"in newsrc and "BRANCH='codex/train337-recovered-evidence-20261026'"in newsrc,'fixed writer and recovery branch')
ok("BASE='cbf0fb621888596aa14ad5f2349b503e23b1b72d'"in newsrc and "need(not git('diff','--name-only',BASE,a.expected_parent,'--','.',':(exclude)evidence'),'recovery parent contains product changes')"in newsrc,'exact adopted F anchor; F-to-parent product-zero guard unchanged')
ok("PROGRESS=PREFIX+'resume-20261026/PROGRESS.md'"in newsrc,'one exact overwrite destination')
ok("source_execution_sha':None"in newsrc,'publication source not falsely relabelled')
ok(not any(s in newsrc for s in ['--force','--force-with-lease','git(\'merge\'','git(\'rebase\'','.unlink(','.rmdir(','rmtree(']),'no force/merge/rebase/delete implementation')
prior=Path('/tmp/geo337-recovery-publisher-list-peer-20261026/REVIEW.json');ok(H(prior)=='34dc74d4ebd91c0f7bf24e30da7e95633a227211c553a7d4d3f07cb952853796','original independent list peer preserved')
rows=[];expected={'fixed':0,'withdrawn-unlisted-overwrite':1,'restored':0,'stale-progress':1,'unbound-progress':1,'other-progress':1,'new-only':0,'stale-parent':1,'parent-restored':0,'product-path':1}
for case,code in expected.items():
 argv=['python3','-B',str(HERE/'scope_probe.py'),case];p=subprocess.run(argv,capture_output=True,text=True);ok(p.returncode==code,'memory proof '+case);rows.append({'argv':argv,'actual_process_returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
(HERE/'MEMORY_PROOF.json').write_text(json.dumps({'subject_sha256':H(NEW),'memory_only':True,'formal_git_executed':False,'commands':rows},ensure_ascii=False,indent=2)+'\n')
argv=['python3','-B',str(NEW)];p=subprocess.run(argv,capture_output=True,text=True);ok(p.returncode==0 and p.stdout.startswith('PLAN_ONLY:'),'default no execution')
(HERE/'DEFAULT_PLAN_RESULT.json').write_text(json.dumps({'argv':argv,'actual_process_returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
report={'schema':'recovery-evidence-append-author-static-preparation/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'blocking_findings':[],'checks':len(checks),'accepted_checks':checks,'unchanged_helper_ast':unchanged,'subject_sha256':H(NEW),'old_subject_sha256':H(OLD),'original_independent_peer_sha256':H(prior),'independent_append_review':'PENDING','formal_git_or_network_executed':False,'cleanup_executed':False,'source_or_SHM_modified':False,'original_expected_parent_required':True,'memory_counterproof_exits':[r['actual_process_returncode']for r in rows]}
(HERE/'AUTHOR_PREPARATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
pins={p.name:H(p)for p in sorted(HERE.iterdir())if p.is_file()and p.name!='PINS.json'}
(HERE/'PINS.json').write_text(json.dumps({'files':pins,'actual_execution':False,'independent_review':'PENDING'},indent=2)+'\n')
print(json.dumps({'exit_code':0,'checks':len(checks),'subject_sha256':H(NEW),'pins_sha256':H(HERE/'PINS.json'),'new_bytes':sum(p.stat().st_size for p in HERE.iterdir()if p.is_file()),'counterproof_exits':report['memory_counterproof_exits']}))
