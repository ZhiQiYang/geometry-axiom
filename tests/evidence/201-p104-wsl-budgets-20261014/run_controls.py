import datetime,hashlib,json,os,pathlib,resource,signal,subprocess,time
repo=pathlib.Path('/tmp/geometry-p095-201');out=pathlib.Path('/tmp/geometry-wake25-201/controls');out.mkdir(exist_ok=True)
source=repo/'tests/test_reference_workspace_races.js';fixed=source.read_text()
old=subprocess.check_output(['git','show','a09a90cbd13a13cf223ad4cdb0a1be76253e94e6:tests/test_reference_workspace_races.js'],cwd=repo).decode()
resource.setrlimit(resource.RLIMIT_STACK,(16384*1024,resource.getrlimit(resource.RLIMIT_STACK)[1]))
cases=[('ordinary',130956),('ordinary',131072),('orphan',130955),('orphan',130956)]
def run(phase,text,kind,size):
 label=f'{kind}-{size}-{phase}';wrapper=out/(label+'.cjs')
 wrapped="const Module=require('node:module'),path=require('node:path');const target="+json.dumps(str(source))+";const m=new Module(target,module);m.filename=target;m.paths=Module._nodeModulePaths(path.dirname(target));m._compile("+json.dumps(text)+",target);\n"
 wrapper.write_text(wrapped)
 name=('K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo ' if kind=='ordinary' else 'K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves ')+str(size)+'-byte boundary'
 argv=['node','--test','--test-name-pattern=^'+name+'$',str(wrapper)]
 duty=.12;period=.1;events=[];clock=time.monotonic();started=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
 with (out/(label+'.stdout')).open('wb') as stdout,(out/(label+'.stderr')).open('wb') as stderr:
  child=subprocess.Popen(argv,cwd=repo,env={**os.environ,'GEOMETRY_TEST_BRIDGE':'/tmp/geometry-tests/bridge'},stdout=stdout,stderr=stderr,start_new_session=True)
  assert os.getpgid(child.pid)==child.pid
  try:
   while child.poll() is None:
    time.sleep(period*duty)
    if child.poll() is not None:break
    try:
     os.killpg(child.pid,signal.SIGSTOP);events.append({'t':time.monotonic()-clock,'signal':'STOP'})
     time.sleep(period*(1-duty));os.killpg(child.pid,signal.SIGCONT);events.append({'t':time.monotonic()-clock,'signal':'CONT'})
    except ProcessLookupError:break
  finally:
   if child.poll() is None:
    try:os.killpg(child.pid,signal.SIGCONT)
    except ProcessLookupError:pass
  code=child.wait()
 receipt={'phase':phase,'case':name,'argv':argv,'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo).decode().strip(),'pid':child.pid,'pgid':child.pid,'started_at':started,'seconds':time.monotonic()-clock,'actual_exit':code,'nominal_duty':duty,'period_s':period,'signals':events,'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'wrapper_sha256':hashlib.sha256(wrapped.encode()).hexdigest(),'note':'cloud test-local STOP/CONT control, not WSL timing data; timeout cancellation is not an assertion kill'}
 (out/(label+'.receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
 print(label,code,[l for l in (out/(label+'.stdout')).read_text().splitlines() if 'boundary (' in l or 'timed out' in l],flush=True)
 return code
results=[]
for kind,size in cases:
 codes=[run(p,old if p in ['before','removed'] else fixed,kind,size) for p in ['before','fixed','removed','restored']]
 results.append({'kind':kind,'size':size,'actual_exits':codes})
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 if codes!=[1,0,1,0]:raise RuntimeError((kind,size,codes))
assert source.read_text()==fixed
