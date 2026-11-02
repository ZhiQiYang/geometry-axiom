"""Root binds an original prepared job; unchanged reviewed launcher and sampler."""
from pathlib import Path
import argparse,hashlib,json,os,sys
F9='4f8a794f4167c3562eb182045102e86e9e37cca9'
OWN=Path('/dev/shm/geo337-F9-browsers-20261025')
SAMPLER=Path('/workspace/geo337-F9-browser-sampler-preparation-20261025/sample_original_browser_v2.py')
LAUNCHER=Path('/workspace/geo337-F9-five-browser-shm-preparation-20261025/launch_F9_browser_shm_v2.py')
STATIC={str(SAMPLER):'919eafb54f20454ee44a27754ce04f6f63f05f6e1c9b32a5b51652058735af30',str(LAUNCHER):'58106e23496c9ee67c7c2162817283464e7af011e758658283139060b797fc3b',
'/workspace/geo337-F9-browser-sampler-static-peer-z23i2u7p/REVIEW.json':'c93e09b10dfd949792077b9aed794db4ab92859844213d78ad23caae7d9a938b',
'/workspace/geo337-F9-five-browser-shm-placement-peer-20261025/REVIEW.json':'90f7a2c0387c69f41f0a457ac26dae159fe98e63a8c0ce124e5db3c5ad6508a2'}
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,j):
 with p.open('x') as f:f.write(json.dumps(j,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
p=argparse.ArgumentParser();p.add_argument('--job',choices=['documents','grid','space','timber'],required=True);a=p.parse_args();job=a.job
for name,pin in STATIC.items():need(sha(name)==pin,'PIN:'+name)
prep=OWN/('host/'+job+'-materialize/subcommands/000001/result.json')
plan=OWN/('plans/'+job+'/PLAN.json')
for item in [prep,plan]:need(item.is_file() and not any(x.is_symlink()for x in [item,*item.parents]),'ORIGINAL_REGULAR_PREPARATION')
j=json.loads(prep.read_bytes());need(j['actual_process_returncode']==0 and j['timeout_expired'] is False and j['source_sha']==F9,'TRUE_MATERIALIZE_EXIT_ZERO')
planj=json.loads(plan.read_bytes());need(planj['sha']==F9 and planj['suites']==[job],'EXACT_JOB_PLAN')
for name in ['requests','launches','r','sampled']:
 d=OWN/name;need(not d.is_symlink(),'NO_ALIAS');d.mkdir(exist_ok=True)
short={'documents':'d','grid':'g','space':'s','timber':'t'}[job]
storage=OWN/('r/'+short)
socket=str(storage/'tmp/original'/job/'com.google.Chrome.ABCDEF/SingletonSocket')
need(len(socket.encode())+1<=108,'UNIX_SOCKET_PATH_CAPACITY')
req=OWN/('requests/'+job+'.json')
q=dict(schema='geo337-F9-single-browser-launch/1',source_sha=F9,root_scheduled_single_browser=True,root_execution_lease=True,job=job,resource_lock='heavy',plan_dir=str(plan.parent),source_layout=str(OWN/('sources/'+job)),out=str(OWN/('launches/'+job)),storage=str(storage),plan_sha256=sha(plan),source_preparation=dict(path=str(prep),sha256=sha(prep)),root_tool_pins=STATIC,unix_socket_path_bytes_including_nul=len(socket.encode())+1)
put(req,q);rp=sha(req)
sample=OWN/('requests/'+job+'-sampled.json')
s=dict(schema='geo337-F9-browser-sampled-launch/1',source_sha=F9,job=job,root_execution_lease=True,root_single_job_shared_SHM_budget_window=True,launch_request=dict(path=str(req),sha256=rp),launch_argv=['python3','-B',str(LAUNCHER),'--request',str(req),'--request-sha256',rp],out=str(OWN/('sampled/'+job)),root_tool_pins=STATIC)
put(sample,s);sp=sha(sample)
print(json.dumps(dict(job=job,source_sha=F9,request=str(req),request_sha256=rp,sampled_request=str(sample),sampled_request_sha256=sp,source_preparation_sha256=sha(prep),plan_sha256=sha(plan))),flush=True)
os.execv(sys.executable,[sys.executable,'-B',str(SAMPLER),'--request',str(sample),'--request-sha256',sp])
