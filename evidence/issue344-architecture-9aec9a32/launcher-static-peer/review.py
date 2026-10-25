from pathlib import Path
import ast,hashlib,json,datetime
O=Path(__file__).parent;P=Path('/tmp/launch_geo344_architecture_20261025.py');b=P.read_bytes();s=b.decode();h=lambda x:hashlib.sha256(x).hexdigest();checks=[]
def ck(v,n):checks.append({'check':n,'passed':bool(v)})
ck(h(b)=='1dc3e7ee783dda593a4ab539e09b12903dd88193fd49b732d5cf4dbb261aa3d6','exact launcher bytes');ast.parse(s);ck(True,'Python AST parse without execution')
D=Path('/workspace/geo344-architecture-adapter-preparation-20261025/refresh_architecture_cdp_exclusion.py');C=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
ck(h(D.read_bytes())=='71cb2e314a3d3e7c3419bbe436f2c308a702d6b3be5f9668594fe729248de2de','original reviewed adapter unchanged');ck(h(C.read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762','original capture unchanged')
for n,t in [
('optimization hard reject before outputs',"if sys.flags.optimize: raise RuntimeError('Python optimization forbidden')"),
('fixed public S344',"F='9aec9a32630fc65f94c53d49e99969e546574d6e'"),
('own branch',"BRANCH='codex/issue320-connection-recovery-20261024'"),
('fresh output and run',"assert not OUT.exists() and not RUN.exists()"),
('before executed launcher copy',"(OUT/'LAUNCHER.py').write_bytes(Path(__file__).read_bytes())"),
('captured adapter copy',"(OUT/'ADAPTER.py').write_bytes(DRIVER.read_bytes())"),
('relative gitpath resolved',"return p if p.is_absolute() else ROOT/p"),
('HEAD source guard',"assert git('rev-parse','HEAD').decode().strip()==F"),
('branch guard',"assert git('branch','--show-current').decode().strip()==BRANCH"),
('initial clean guard',"assert not git('status','--porcelain=v1','--untracked-files=all')"),
('remote exact head',"assert git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()==[F,'refs/heads/'+BRANCH]"),
('604/613 counts',"assert len(sources)==604 and len(needed)==613"),
('source exact ls-tree',"raw=git('ls-tree','-r','-l','-z',F,'--',*needed)"),
('no tree symlink',"assert kind==b'blob' and mode!=b'120000'"),
('exact tree coverage',"assert [x['path'] for x in rows]==needed"),
('root 60MB admission',"assert budget['workspace_free']>=60000000"),
('WS materialization and index budget',"assert budget['workspace_free']>missing_alloc+index.stat().st_size+len(dirs)*4096+8*1024*1024"),
('fresh TMP estimated bound',"assert budget['tmp_free']>tmp_estimate"),
('sparse exact union',"assert set(after.splitlines())==set(before.splitlines())|{('/'+n).encode() for n in needed}"),
('regular physical leaf',"p=ROOT/row['path'];assert p.is_file() and not p.is_symlink()"),
('all byte Gitblob guards',"b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\\0'+b).hexdigest()==row['oid']"),
('16MiB stack',"resource.setrlimit(resource.RLIMIT_STACK,(16777216,old_stack[1]))"),
('original driver flags',"argv=['python3','-B',str(DRIVER),'--execute','--root-scheduled-architecture-run','--root',str(ROOT),'--sha',F,'--out',str(RUN)]"),
('original captured no new deadline',"row,out,err=rec.run(argv,cwd=ROOT,timeout=None,check=False,source_sha=F,"),
('formal exit propagated',"raise SystemExit(code if isinstance(code,int) and code>=0 else 1)")]: ck(t in s,n)
ck(s.index("assert budget['tmp_free']>tmp_estimate")<s.index("git('sparse-checkout','add'"),'budget before materialization')
ck(s.index("cap.dump(OUT/'MATERIALIZED.json'")<s.index("row,out,err=rec.run(argv"),'materialization guards before formal')
ck("git('push'" not in s and "git('commit'" not in s,'launcher no Git commit or push')
r={'schema':'geo344-exact-architecture-launcher-static-peer/1','exit_code':0 if all(x['passed'] for x in checks) else 1,'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'launcher_sha256':h(b),'adapter_sha256':h(D.read_bytes()),'source_sha':'9aec9a32630fc65f94c53d49e99969e546574d6e','assessment':['Read full6764B launcher control flow against unchanged original adapter. Source admission/materialization are narrow to604 closure+9 required metadata/judges and followed by adapter original closure judges.','Original parser, assertions, golden and timeouts were not modified. Parent optimize forbidden explicitly before outputs; original subprocess environment removes optimization override.','Initial clean/published source, exact sparse union and all613 Gitblob bytes are checked before formal; root-owned scheduling flag is explicit.','Original formal nonzero is preserved in original c387 streams/result and propagated; this review is not a successful formal run.'],'launch_conditions':['Root must grant exclusive Git metadata/source and formal architecture scheduling window; this launcher does not acquire global heavy/cache locks itself.','Fresh WS60,000,000B and further source/index/metadata guard plus fresh TMP estimate including16MiB reserve must pass. The tool must fail without expansion if those checks fail.','Use exact default Python launcher pin; no -O or edited adapter. Root/source/outputs remain the fixed owned paths.'],'limits':['Static review only; no source expansion, locks, C/browser/tests, Git mutations, source snapshot or live payload scan performed.','Resource plan is an explicit estimate with allowances, not a measured peak or guaranteed worst-case product output size.','Formal original architecture three judges, one-digest0/1/0 and nine controls remain UNRUN until actual original terminal receipts are received.'],'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(O/'REVIEW.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False));assert r['exit_code']==0
