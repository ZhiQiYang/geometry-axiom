"""Independent source43 v3 public census and inverse byte review. No product execution."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,sys
B=Path('<workspace-path>');P=B/'source-authority-43-public-v3';R=Path('<workspace-path>')
O=Path('<workspace-path>')
OUT=Path('<workspace-path>');assert not OUT.exists();OUT.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest()
def pairs(rows):
 out={}
 for k,v in rows:
  if k in out:raise ValueError('duplicate JSON key '+k)
  out[k]=v
 return out
def load(b):return json.loads(b,object_pairs_hook=pairs)
TOKEN=re.compile(r'/workspace/[A-Za-z0-9._~%+@:=/\-]+|/tmp/geometry-[A-Za-z0-9._~%+@:=/\-]+|/opt/codex/[A-Za-z0-9._~%+@:=/\-]+|/tmp/playwright_chromiumdev_profile-[A-Za-z0-9._~%+@:=/\-]+')
PREFIX={
 '<workspace-path>':'<original-evidence-root>',
 '<workspace-path>':'<independent-review-root>',
 str(B):'<delivery-closeout-root>','<workspace-path>':'<takeover-repository-root>',
 '<workspace-path>':'<baseline-repository-root>','<workspace-path>':'<frozen-cb8-repository-root>',
 '<workspace-path>':'<resume-repository-root>','<isolated-test-directory>':'<configured-native-directory>',
 '<execution-runtime-path>':'<node-runtime>',
 '<execution-runtime-path>':'<python-runtime>',
 '<workspace-path>':'<unit-evidence-root>',
 '<workspace-path>':'<old-unit-evidence-root>'}
def choices(token):
 label='<workspace-path>' if token.startswith('/workspace/') else '<execution-runtime-path>' if token.startswith('/opt/') else '<isolated-browser-profile>' if token.startswith('/tmp/playwright') else '<isolated-test-directory>'
 return sorted({token,label,*[v+token[len(k):] for k,v in PREFIX.items() if token.startswith(k)]},key=len,reverse=True)
inverse_records=[]
def inverse_text(old,new,location,record=True):
 last=cursor=0;rebuilt=[];segments=[]
 for m in TOKEN.finditer(old):
  unchanged=old[last:m.start()]
  if not new.startswith(unchanged,cursor):return False
  segment=new[cursor:cursor+len(unchanged)]
  rebuilt.append(segment);segments.append({'bytes':len(segment.encode()),'sha256':sha(segment.encode())})
  cursor+=len(unchanged)
  projected=next((v for v in choices(m.group()) if new.startswith(v,cursor)),None)
  if projected is None:return False
  cursor+=len(projected);rebuilt.append(m.group());last=m.end()
 tail=old[last:]
 if new[cursor:]!=tail:return False
 rebuilt.append(new[cursor:])
 if ''.join(rebuilt)!=old:return False
 segments.append({'bytes':len(tail.encode()),'sha256':sha(tail.encode())})
 if record:inverse_records.append({'location':location,'originalStringSHA256':sha(old.encode()),'publicStringSHA256':sha(new.encode()),'machineTokens':len(list(TOKEN.finditer(old))),'allNonTokenSegmentsExact':True,'unchangedSegments':segments})
 return True
def inverse_value(old,new,location='$'):
 if type(old) is not type(new):return False
 if isinstance(old,dict):
  if len(old)!=len(new):return False
  used=set();recovered={}
  for k,v in old.items():
   matches=[]
   for publick in new:
    if publick in used:continue
    base=publick
    if '|originalKeySha256=' in publick:
     base,hashpart=publick.rsplit('|originalKeySha256=',1)
     if hashpart!=sha(k.encode()) or not base.endswith('|basename='+Path(k).name):continue
     base=base.removesuffix('|basename='+Path(k).name)
    if inverse_text(k,base,location+'.<key>',False):matches.append(publick)
   if len(matches)!=1:return False
   pk=matches[0];used.add(pk)
   if not inverse_text(k,pk.split('|basename=',1)[0] if '|originalKeySha256=' in pk else pk,location+'.<key>'):return False
   if not inverse_value(v,new[pk],location+'.'+k):return False
   recovered[k]=v
  return recovered==old and len(used)==len(new)
 if isinstance(old,list):return len(old)==len(new) and all(inverse_value(a,b,location+'['+str(i)+']') for i,(a,b) in enumerate(zip(old,new)))
 if isinstance(old,str):return inverse_text(old,new,location)
 return old==new
checks=[]
def ck(name,ok,detail=None):checks.append({'name':name,'ok':bool(ok),'detail':detail})
before={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=R,text=True)}
mb=(P/'manifest.json').read_bytes();m=load(mb)
ck('exact manifest immutable',sha(mb)=='d00a9335f86367d71df62132e6674c5ce0280340997225847500b5e9a5f80d46')
files=m['publicFiles'];listed=[x['path'] for x in files];actual=[p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file() and p!=P/'manifest.json']
ck('exact56 listed plus root manifest57 no extras',len(listed)==56 and len(set(listed))==56 and set(listed)==set(actual))
for x in files:
 p=P/x['path'];data=p.read_bytes();rel=Path(x['path'])
 ck('safe listed path',not rel.is_absolute() and '..' not in rel.parts and not p.is_symlink() and p.resolve().is_relative_to(P),x['path'])
 ck('public byte hash size',sha(data)==x['sha256'] and len(data)==x['bytes'],x['path'])
 if p.suffix=='.json':
  try:load(data);ck('structured JSON duplicate-key rejected parse',True,x['path'])
  except Exception as e:ck('structured JSON duplicate-key rejected parse',False,{'path':x['path'],'error':str(e)})
 try:text=data.decode()
 except UnicodeDecodeError:continue
 ck('no actual private machine token or queue payload',not TOKEN.search(text) and not any(v in text for v in ['"owner_thread_id":','PRIVATE_QUEUE_DATABASE','closure-evidence/queue/']),x['path'])
refs=m['historyReviewsAndExecutorSources']+m['fullTestedCommitSourceCopies']
accounted={x['path'] for x in refs}|{'README.md','prose-token-projection-correction.json'}
ck('every public file accounted by explicit original or derived prose',set(listed)==accounted)
extras=load((B/'source-authority-43-extra-v2.json').read_bytes())
candidates=set()
for x in extras:
 p=Path(x['path'])
 if p.is_file():candidates.add(p)
 elif p.is_dir():candidates.update(v for v in p.rglob('*') if v.is_file())
wanted={x['originalSha256'] for x in refs};sizes={x['originalBytes'] for x in refs};originals={}
for p in candidates:
 if p.stat().st_size in sizes:
  digest=sha(p.read_bytes())
  if digest in wanted:originals.setdefault(digest,[]).append(p)
bindings=[]
for ref in refs:
 matches=originals.get(ref['originalSha256'],[])
 ck('original hash resolves from exact original source roots',bool(matches),ref['path'])
 if not matches:continue
 raw=matches[0].read_bytes();public=(P/ref['path']).read_bytes()
 ck('original and public declared hash size',len(raw)==ref['originalBytes'] and sha(raw)==ref['originalSha256'] and len(public)==ref['bytes'] and sha(public)==ref['sha256'],ref['path'])
 ck('projection and original-identity flags honest',ref['byteIdenticalOriginal']==(raw==public) and ref['publicProjection']==(raw!=public),ref['path'])
 if (P/ref['path']).suffix=='.json':
  ok=inverse_value(load(raw),load(public),ref['path'])
 else:ok=inverse_text(raw.decode(),public.decode(),ref['path'])
 ck('inverse preserves every non-token byte or decoded value and key association',ok,ref['path'])
 bindings.append({'publicPath':ref['path'],'originalSHA256':sha(raw),'publicSHA256':sha(public),'originalPaths':[str(p) for p in matches],'inverseExact':ok})
source_refs=[x for x in refs if x.get('artifactRelativePath','').startswith('source/')]
ck('29 source identities exactly27 byteidentical and2 explicit doc projections',len(source_refs)==29 and sum(x['byteIdenticalOriginal'] for x in source_refs)==27 and {x['artifactRelativePath'] for x in source_refs if not x['byteIdenticalOriginal']}=={'source/geometry-web/docs/DOM-CONTRACT.md','source/tests/INTEGRATION-GATES.md'})
for x in source_refs:
 rel=x['artifactRelativePath'].removeprefix('source/')
 raw=subprocess.check_output(['git','show','243326b512896ace70e068f62c8f3d6397f6000d:'+rel],cwd=R)
 ck('exact historical243 Git source hash',sha(raw)==x['originalSha256'],rel)
 correction=m['proseCorrection']
 if not x['byteIdenticalOriginal']:
  row=next(z for z in correction['documents'] if z['publicPath']==x['path'])
  ck('doc public/original hash and non-token metadata',row['originalSHA256']==sha(raw) and row['correctedPublicSHA256']==sha((P/x['path']).read_bytes()) and row['allNonTokenBytesRetained'] is True,rel)
inventory=load((O/'source-followup.json').read_bytes())
ck('43 original unique IDs and every item not full accepted',len(inventory['items'])==len({x['id'] for x in inventory['items']})==43 and inventory['all43ProductAccepted'] is False and all(x['browserAcceptanceAt243']['entireItemAccepted'] is False for x in inventory['items']))
ck('source-only authority and privateZIP qualification',m['rounds']==[] and m['sourceAuthority']['all43ProductAccepted'] is False and m['sourceAuthority']['originalPrivateZIPReceived'] is False and m['releaseApproved'] is False and m['productTestsExecuted'] is False)
ck('decision sources preserved no added policy',any('C5/C7' in x and 'C6' in x for x in m['decisions']) and any('B8/G1/G2' in x for x in m['decisions']))
# Meaningful inverse counterexamples independently reject non-token losses.
for label,old,new,want in [('valid bounded Unicode prose','prefix <workspace-path> 後文','prefix <workspace-path> 後文',True),('lost Unicode rejects','prefix <workspace-path> 後文','prefix <workspace-path>',False),('backtick retained','x <workspace-path>'+chr(96)+' y','x <workspace-path>'+chr(96)+' y',True),('lost backtick rejects','x <workspace-path>'+chr(96)+' y','x <workspace-path> y',False),('code changed rejects',"p='<workspace-path>';assert ok","p='<workspace-path>';assert false",False)]:
 ck('inverse counterexample '+label,inverse_text(old,new,'mock',False)==want)
ck('collision key value swap rejects',not inverse_value({'<workspace-path>':1,'<workspace-path>':2},{'<workspace-path>|basename=a|originalKeySha256='+sha(b'<workspace-path>'):2,'<workspace-path>|basename=b|originalKeySha256='+sha(b'<workspace-path>'):1},'mock'))
after={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=R,text=True)}
ck('frozen repo unchanged and clean',before==after=={'head':'f3b8285729b42cd22451c98cba1e2ec4514517f3','dirty':''})
ck('manifest bytes unchanged after reviewer',(P/'manifest.json').read_bytes()==mb)
log=OUT/'review.raw.log';log.write_text('\n'.join(('PASS ' if x['ok'] else 'FAIL ')+x['name']+' '+str(x['detail']) for x in checks)+'\n')
record={'schema':'geometry-source43-v3-independent-inverse-public-review/1','actor':'/root/ui_tail_contract','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actualCommand':sys.orig_argv,'actualPython':str(Path('/proc/self/exe').resolve()),'actualPythonSHA256':sha(Path('/proc/self/exe').read_bytes()),'scriptSHA256':sha(Path(__file__).read_bytes()),'testedRepoBefore':before,'testedRepoAfter':after,'manifestSHA256':sha(mb),'checks':checks,'checksPassed':sum(x['ok'] for x in checks),'checksFailed':sum(not x['ok'] for x in checks),'publicReferences':bindings,'inverseStringRecords':inverse_records,'rawReviewLogSHA256':sha(log),'accepted':all(x['ok'] for x in checks),'exitCode':0 if all(x['ok'] for x in checks) else 1,'productExecuted':False,'limits':['Public evidence/source packet only; no browser/native/service/repo/GitHub mutations.','Inverse proof compares all non-token text bytes and decoded JSON key/value associations; standalone formatting changes in serialized JSON are permitted.','Source43 inventory29 files and43IDs is historical source authority; no all43 product, privateZIP or full CDP acceptance claim.']}
j=OUT/'receipt.json';j.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'proof':str(j),'sha256':sha(j.read_bytes()),'pass':record['checksPassed'],'fail':record['checksFailed'],'failures':[x for x in checks if not x['ok']]}));sys.exit(record['exitCode'])

