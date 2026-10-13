"""Real isolated native context lifecycle, on the owned idle test service only."""
import urllib.request,urllib.error,json,uuid,pathlib,subprocess,datetime,os
url=os.environ['GEOMETRY_TEST_URL'].rstrip('/');out=pathlib.Path(os.environ['GEOMETRY_SCENARIO_OUT']);root=pathlib.Path(__file__).resolve().parents[2]
assert url.startswith('http://127.0.0.1:') and not url.endswith(':8765')
assert str(out.resolve()).startswith('/tmp/');out.mkdir(parents=True,exist_ok=True)
def request(route,data=None,context=None):
 headers={'Content-Type':'application/json'}
 if context:headers['X-Geometry-Scenario']=context
 req=urllib.request.Request(url+route,data=None if data is None else json.dumps(data).encode(),headers=headers)
 try:
  with urllib.request.urlopen(req,timeout=10) as r:return r.status,json.load(r),r.headers.get('X-Geometry-Session')
 except urllib.error.HTTPError as e:return e.code,json.load(e),e.headers.get('X-Geometry-Session')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=root,text=True).strip()
if os.environ.get('GEOMETRY_REQUIRE_CLEAN')=='1':assert subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True)==''
runtime=request('/runtime')[1];assert runtime['fresh'] and pathlib.Path(runtime['root'])==root
def children():
 return subprocess.check_output(['ps','--ppid',str(runtime['pid']),'-o','pid=,args='],text=True).strip().splitlines()
before=request('/api',{'cmd':'dump'})[1];before_children=children();assert len(before_children)==1,'Owned idle service must have only its root bridge'
contexts=[];checks=[];owned=[]
def check(label,condition):
 checks.append({'label':label,'passed':bool(condition)});assert condition,label
def creation():
 status=request('/scenarios/editor')[1]
 return {'action':'create','requestId':str(uuid.uuid4()),'sequence':status['sequence'],'session':status['session']}
try:
 for n in range(300):
  data=creation();status,result,_=request('/scenarios/editor',data);assert status==200 and result['ok']
  owned.append(data);context=result['context'];contexts.append(context)
  if n==0:
   first=data;retry=request('/scenarios/editor',data)[1];check('real lost-create replay names the same native context',retry==result)
  status,native,session=request('/api',{'cmd':f'line spec isolatedCycle {n}'},context)
  assert status==200 and native['ok'] and session==context and context!=runtime['session']
  close={**data,'action':'close'};terminal=request('/scenarios/editor',close)[1]
  assert terminal=={'ok':True,'state':'retired'};owned.remove(data)
  if n==0:check('real lost-close replay returns the same retired terminal',request('/scenarios/editor',close)[1]==terminal)
  assert request('/api',{'cmd':'dump'},context)[0]==410
  if (n+1)%30==0:print(f'TERMINAL {n+1}/300 real native edit / exact retirement',flush=True)
 check('300 independent native sessions executed and retired',len(set(contexts))==300)
 check('300 cycles leave only the original owned native child',children()==before_children)
 check('ancient retired create cannot recreate after more than 256 normal edits',request('/scenarios/editor',first)[1]['ok'] is False)
 check('ancient close can still retrieve its retired terminal',request('/scenarios/editor',{**first,'action':'close'})[1]=={'ok':True,'state':'retired'})
 for _ in range(8):
  data=creation();created=request('/scenarios/editor',data)[1];assert created['ok'];owned.append(data)
 ninth=creation();check('real ninth active context refuses before creation',request('/scenarios/editor',ninth)[1]['ok'] is False)
 for data in owned[:]:assert request('/scenarios/editor',{**data,'action':'close'})[1]['ok'];owned.remove(data)
 after=request('/api',{'cmd':'dump'})[1]
 check('real capacity test and 300 private mutations preserve root native bytes and revision',after==before)
 check('all private native children are reaped after capacity test',children()==before_children)
finally:
 for data in owned:request('/scenarios/editor',{**data,'action':'close'})
 (out/'native-context-300-results.json').write_text(json.dumps({'schema':'geometry-native-context-lifecycle/1','head':head,'tree':tree,'runtime':runtime,'completedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cycles':len(contexts),'contexts':contexts,'checks':checks},indent=2))
print('NATIVE_CONTEXT_RESULT '+json.dumps({'head':head,'cycles':300,'passed':len(checks),'failed':0}),flush=True)
