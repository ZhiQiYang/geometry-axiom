from pathlib import Path
import hashlib,json,os,sys
F9='4f8a794f4167c3562eb182045102e86e9e37cca9'
ROOT=Path('/dev/shm/geo337-F9-browsers-20261025')
SAMPLER=Path('/workspace/geo337-F9-browser-sampler-preparation-20261025/sample_original_browser_v2.py')
PINS={str(SAMPLER):'919eafb54f20454ee44a27754ce04f6f63f05f6e1c9b32a5b51652058735af30',
'/workspace/geo337-F9-browser-sampler-static-peer-z23i2u7p/REVIEW.json':'c93e09b10dfd949792077b9aed794db4ab92859844213d78ad23caae7d9a938b',
'/workspace/geo337-F9-assembly-SHM-materialize-actual-peer-20261025/REVIEW.json':'ff2c1aa7b409754573238cd47d43350e10618c2ce4ab410e2e0256467e8c7aae',
str(ROOT/'plans/assembly/PLAN.json'):'99b8b854486994b0d6e6c239d1c7e33150f46b6cff458c18eadcf081ba098f1c'}
PREP=ROOT/'host/assembly-materialize/subcommands/000001/result.json'
PINS[str(PREP)]='bfe8be47067b7ce7ad30fc9bc875b14b8e53cd8142bac7ecf126ed939df64b01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def put(p,v):
 with p.open('x') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
for p,h in PINS.items():
 p=Path(p);need(not any(x.is_symlink() for x in [p,*p.parents]),'NO_ALIAS');need(sha(p)==h,'PIN:'+str(p))
for name in ['requests','launches','runs','sampled']:
 p=ROOT/name;need(not p.is_symlink(),'NO_PARENT_ALIAS');p.mkdir(exist_ok=True)
request=ROOT/'requests/assembly.json'
q=dict(schema='geo337-F9-single-browser-launch/1',source_sha=F9,root_scheduled_single_browser=True,root_execution_lease=True,job='assembly',resource_lock='heavy',plan_dir=str(ROOT/'plans/assembly'),source_layout=str(ROOT/'sources/assembly'),out=str(ROOT/'launches/assembly'),storage=str(ROOT/'runs/assembly'),plan_sha256=PINS[str(ROOT/'plans/assembly/PLAN.json')],source_preparation=dict(path=str(PREP),sha256=PINS[str(PREP)]),root_pins=PINS)
put(request,q);pin=sha(request)
sample=ROOT/'requests/assembly-sampled.json'
s=dict(schema='geo337-F9-browser-sampled-launch/1',source_sha=F9,job='assembly',root_execution_lease=True,root_single_job_shared_SHM_budget_window=True,launch_request=dict(path=str(request),sha256=pin),launch_argv=['python3','-B','/workspace/geo337-F9-five-browser-shm-preparation-20261025/launch_F9_browser_shm_v2.py','--request',str(request),'--request-sha256',pin],out=str(ROOT/'sampled/assembly'),root_pins=PINS)
put(sample,s);sp=sha(sample)
print(json.dumps(dict(request=str(request),request_sha256=pin,sampled_request=str(sample),sampled_request_sha256=sp,sampler_sha256=PINS[str(SAMPLER)])),flush=True)
os.execv(sys.executable,[sys.executable,'-B',str(SAMPLER),'--request',str(sample),'--request-sha256',sp])
