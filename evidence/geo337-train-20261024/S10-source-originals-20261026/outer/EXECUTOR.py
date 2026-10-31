import json,os,sys,hashlib,shutil,fcntl
from pathlib import Path
sys.path.insert(0,'/workspace/geo261-environment/final-f-contact-checker-proof-tools')
from capture import Recorder,dump
own=Path('/dev/shm/geometry-axiom-geo337-20261025');out=own/'S10-closed-collection-root-original-20261026'
prep=Path('/tmp/geo337-S10-closed-original-collection-preparation-20261025')
need=lambda c,m: None if c else (_ for _ in ()).throw(RuntimeError(m))
need(not out.exists(),'fresh output');raw=(prep/'COLLECTION_REQUEST.peer-bound-inactive.json').read_bytes()
need(hashlib.sha256(raw).hexdigest()=='569cc3642feec0b5537a706fc663231b9b79862ab36bddafbc993a0e25f062d2','request template pin')
request=json.loads(raw);seen=set();used=0
for root in [own,Path('/dev/shm/geo337-F9-browsers-20261025')]:
 for p in root.rglob('*'):
  st=p.lstat();key=(st.st_dev,st.st_ino)
  if key not in seen:seen.add(key);used+=st.st_blocks*512
# Publication is not yet running; retain its entire conservative reservation as well.
need(used+request['required_fresh_bytes']+200*1024*1024<request['shared_ceiling_bytes'],'shared original ceiling')
need(shutil.disk_usage(own).free>request['required_fresh_bytes'],'real mount reserve')
locks=[]
for name in ['heavy.lock','secondary.lock']:
 f=open('/tmp/g261r3/'+name,'r');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
out.mkdir();(out/'EXECUTOR.py').write_bytes(Path(__file__).read_bytes())
request.update(root_execution_lease=True,execute=True,current_execution_admitted=True,out=str(own/'geo337-S10-closed-original-package-20261026'))
dump(out/'ROOT_REQUEST.json',request);dump(out/'RESOURCE_PLAN.json',{'combined_used_before':used,'collection_increment_bound':request['required_fresh_bytes'],'concurrent_publication_reserved':200*1024*1024,'shared_ceiling':request['shared_ceiling_bytes']})
rec=Recorder(out,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),request['source_sha'])
row,stdout,stderr=rec.run(['python3','-B',str(prep/'collect_s10_closed.py'),'--request',str(out/'ROOT_REQUEST.json'),'--execute'],cwd='/workspace',timeout=300,check=False)
dump(out/'RESULT.json',{'exit_code':row['actual_process_returncode'],'collection_out':request['out'],'source_sha':request['source_sha'],'product_tests_rerun':False})
print(json.dumps({'exit_code':row['actual_process_returncode'],'stdout':stdout.decode(),'stderr':stderr.decode()}));sys.exit(row['actual_process_returncode'])
