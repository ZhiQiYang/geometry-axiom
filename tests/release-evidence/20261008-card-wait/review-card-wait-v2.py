#!/usr/bin/env python3
"""Independent, read-only addendum audit. Run only after the final tar is ready.
Packaging requires exact clean b822. Publication is a separate documentary audit.
Writes only a new review JSON in its own directory; never extracts or edits inputs.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import argparse, hashlib, io, json, re, stat, subprocess, sys, tarfile, zipfile

OUT = Path(__file__).resolve().parent
ROOT = Path('/workspace/geometry-final')
RAW = Path('/workspace/scratch/geometry-all-closeout')
FREEZE = 'b822a9ff7c0deb74f7d6f05e70aa43d6f00dd8d5'
TREE = 'fb528657190ebdf39733a71bdaea6f908ff72a48'
ARCHIVE = 'geometry-card-wait-evidence-b822a9ff.tar.gz'
GUARD_SHA = 'd9ab1f9d925c15f0df8ad081b2c5acc1fda55fe1ec96092cf6d917bc3ffb04ef'
ALLOWED_ROOTS = [RAW/'pr168-review', RAW/'pr168-independent', RAW/'multiroom/final-card-wait-b822a9f', RAW/'multiroom/final-card-wait-2503260', OUT]
DENY_PARTS = {'.git','node_modules','__pycache__','cache','caches','code cache','gpucache','shadercache','component_crx_cache','chrome-profile','browser-profile','profiles','profile','user-data-dir','indexeddb','local storage','session storage','feedback','user-data','userdata','work-manager','wm','credentials','.ssh','.aws','.config'}
TEXT_EXTENSIONS = {'.json','.jsonl','.log','.txt','.md','.py','.js','.cjs','.mjs','.html','.css','.csv','.scene','.diff','.patch','.stderr','.stdout','.exit'}
SECRET_PATTERNS = {
 'private-key': rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
 'github-token': rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})',
 'openai-key': rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{35,}',
 'aws-access-id': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'credential-bearing-url': rb'https?://[^\s/"<>:@]{2,}:[^\s/"<>@]{2,}@',
}
EXPECTED_PARTIALS = {
 'grid-system': ('GEOMETRY_GRID_SYSTEM_ONLY', {'P70':117,'P71':9,'P78':23,'P87':60,'P88':107}),
 'assembly': ('GEOMETRY_ASSEMBLY_ONLY', {'P77':134,'P82':16}),
 'composition': ('GEOMETRY_COMPOSITION_ONLY', {'P72':52}),
}
EXPECTED_CLAIMS = {'canonicalPartial':{'GRID':316,'ASSEMBLY':150,'COMPOSITION':52},'focusedNode':{'cardPosition':21,'evaluation':9,'total':30},'fourCardBrowser':20,'firstPositionBrowser':5,'independentSourceChecks':23,'independentVM':14,'oldSameVMViolations':7}

def now(): return datetime.now(timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def read_json(path): return json.loads(Path(path).read_bytes())
def at(data,path):
 for key in path.split('.'):
  if not isinstance(data,dict): return None
  data=data.get(key)
 return data

def identity(): return {'head':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'status':git('status','--porcelain')}
def safe_member(name):
 return isinstance(name,str) and bool(name) and '\\' not in name and '\x00' not in name and not name.startswith('/') and not re.match(r'^[A-Za-z]:',name) and all(p not in {'','..','.'} for p in name.rstrip('/').split('/'))
def private_path(name):
 parts=[p.lower() for p in PurePosixPath(name).parts]
 return any(p in DENY_PARTS or p.endswith('-profile') or p.startswith('geometry-final-feedback') for p in parts) or bool(re.search(r'\.(?:sqlite3?|db)(?:-(?:wal|shm|journal))?$',name,re.I))
def regular_source(path):
 return path.is_file() and not path.is_symlink() and not any(p.is_symlink() for p in path.parents)
def stable_bytes(path):
 if not regular_source(path): raise ValueError('nonregular/symlink source: '+str(path))
 before=path.stat();data=path.read_bytes();after=path.stat()
 if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns): raise ValueError('source changed while reading: '+str(path))
 return data

class Review:
 def __init__(self): self.checks=[];self.flags=[];self.projects=[];self.sources={};self.member_payloads={}
 def check(self,name,ok,detail=None):
  self.checks.append({'name':name,'passed':bool(ok),'detail':detail})
 def scan(self,label,data,depth=0):
  if data.startswith((b'\x7fELF',b'MZ',b'SQLite format 3\x00')): self.flags.append({'path':label,'flag':'native-or-sqlite-magic'})
  if Path(label).suffix.lower() in TEXT_EXTENSIONS:
   for kind,pattern in SECRET_PATTERNS.items():
    count=len(re.findall(pattern,data))
    if count:self.flags.append({'path':label,'flag':kind,'count':count,'matchedValuesOmitted':True})
   if re.search(rb'/workspace/scratch/geometry-advance/work-manager/[A-Za-z0-9._-]',data): self.flags.append({'path':label,'flag':'private-WM-execution-path'})
  is_project=Path(label).suffix.lower() in {'.gcanvas','.zip'}
  if not is_project:return
  info={'path':label,'bytes':len(data),'members':0,'validZip':False};self.projects.append(info)
  if depth>=2:self.flags.append({'path':label,'flag':'nested-zip-depth'});return
  try:
   with zipfile.ZipFile(io.BytesIO(data)) as z:
    entries=z.infolist();names=[i.filename for i in entries]
    if len(names)!=len(set(names)):self.flags.append({'path':label,'flag':'duplicate-ZIP-members'})
    if sum(i.file_size for i in entries)>100*1024*1024:raise ValueError('ZIP uncompressed budget exceeded')
    for i in entries:
     if not safe_member(i.filename) or private_path(i.filename):raise ValueError('unsafe/private ZIP member')
     mode=(i.external_attr>>16)&0xffff
     if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in {0,stat.S_IFREG,stat.S_IFDIR}):raise ValueError('nonregular ZIP member')
     if i.flag_bits&1:raise ValueError('encrypted ZIP cannot be audited')
     if i.is_dir():continue
     if i.file_size>50*1024*1024:raise ValueError('ZIP member size budget exceeded')
     self.scan(label+'!/'+i.filename,z.read(i),depth+1)
    info.update(validZip=True,members=len(entries))
  except (ValueError,zipfile.BadZipFile,RuntimeError) as e:
   self.flags.append({'path':label,'flag':'unreadable-or-unsafe-project-ZIP','reason':str(e)})
 def source_json(self,path):
  key=str(path)
  if key not in self.sources:raise ValueError('mandatory proof absent from manifest: '+key)
  return json.loads(self.sources[key])
 def wrapper(self,path):
  d=self.source_json(path)
  return d.get('executionVerified') is True and not d.get('problems') and at(d,'execution.exitCode')==0 and at(d,'before.git.head')==FREEZE and at(d,'after.git.head')==FREEZE and at(d,'before.git.status')=='' and at(d,'after.git.status')==''

def packaging_or_publication_check(review,args,before,receipt,manifest_bytes,archive_bytes):
 if args.phase=='packaging':
  review.check('Packaging review starts at exact clean freeze/tree',before=={'head':FREEZE,'tree':TREE,'status':''},before)
  return
 previous=read_json(OUT/'independent-review.json')
 review.check('Publication preserves successful exact-freeze packaging review',previous.get('phase')=='packaging' and previous.get('passed',0)>0 and previous.get('failed')==0 and previous.get('before')=={'head':FREEZE,'tree':TREE,'status':''} and previous.get('manifestSha256')==sha(manifest_bytes) and previous.get('archiveSha256')==sha(archive_bytes))
 declared=args.publication_path
 changed=git('diff','--name-only',FREEZE,before['head']).splitlines()
 allowed=lambda p: p.startswith('tests/release-evidence/20261008-card-wait/') or (p.endswith('.md') and not p.startswith(('geometry-core/','native/')))
 review.check('Publication is clean with explicit exact documentary path allowlist',before['status']=='' and bool(declared) and len(declared)==len(set(declared)) and all(allowed(p) and safe_member(p) for p in declared) and set(changed)==set(declared),{'actualChangedPaths':changed,'declaredAllowedPaths':declared,'meaning':'Different publication HEAD allowed; original execution freeze remains b822.'})

def audit_fixed_raw_scopes(r):
 for name,(filter_name,sections) in EXPECTED_PARTIALS.items():
  path=RAW/'multiroom/final-card-wait-b822a9f'/name/'release-receipt/receipt.json'
  d=r.source_json(path);c=at(d,'evidence.canonicalResult') or {}
  r.check('Canonical partial '+name+' exact fixed census and identity',r.wrapper(path) and at(d,'evidence.completionVerified') is True and c.get('completed') is True and c.get('sections')==sections and c.get('passedAssertions')==sum(sections.values()) and c.get('failedAssertions')==0 and c.get('skipped')==[] and c.get('uncaughtBrowserExceptions')==0 and at(c,'scope.mode')=='partial' and at(c,'scope.filters')==[filter_name] and at(c,'scope.modifiers')==[],{'expected':sum(sections.values()),'sections':sections,'scope':'partial only; never full2177'})
 p=RAW/'pr168-independent/node30-b822-census.json';d=r.source_json(p)
 counts=d.get('rawCounts',{})
 r.check('Focused Node30 exact census, distinct from aggregate',d.get('completed') is True and d.get('executionHead')==FREEZE and counts.get('tests')==30 and counts.get('pass')==30 and counts.get('fail')==0 and counts.get('cancelled')==0 and counts.get('skipped')==0 and len(d.get('caseNames',[]))==30 and len(set(d.get('caseNames',[])))==30 and r.wrapper(RAW/'pr168-independent/node30-b822-receipt/receipt.json'),{'observedCounts':counts})
 for folder,wrapper_name,count in [('card-drag-b822','card-drag-b822-receipt',20),('first-position-b822','first-position-b822-receipt',5)]:
  d=r.source_json(RAW/'pr168-independent'/folder/'result.json');cases=d.get('cases',[])
  r.check('Real browser '+folder+' exact '+str(count)+' controls',d.get('completed') is True and d.get('expected')==count and d.get('passed')==count and d.get('failed')==0 and d.get('exitCode')==0 and d.get('identityStable') is True and len(cases)==count and len({x.get('name') for x in cases})==count and all(x.get('passed') is True for x in cases) and not d.get('browserErrors') and not d.get('consoleErrors') and r.wrapper(RAW/'pr168-independent'/wrapper_name/'receipt.json'))
 proof=r.source_json(RAW/'pr168-review/strictfix-b822a9f/tail-source-proof-b822a9f.json');checks=proof.get('checks',[])
 r.check('Independent source closure23 binds exact freeze/tree',proof.get('allChecksPassed') is True and len(checks)==23 and all(x.get('pass') is True for x in checks) and at(proof,'source.strictFreeze')==FREEZE and at(proof,'source.tree')==TREE and at(proof,'source.status')=='' and len(at(proof,'source.changes') or {})==8)
 vm=r.source_json(RAW/'pr168-review/strictfix-b822a9f/independent-helper-vm-b822a9f.json')
 r.check('Independent VM14 retains seven same-harness baseline counterexamples',vm.get('finalAllPassed') is True and len(vm.get('scenarios',[]))==14 and len(vm.get('baseline',[]))==14 and len(vm.get('after',[]))==14 and len(vm.get('baselineCounterexamples',[]))==7 and at(vm,'source.finalHead')==FREEZE and vm.get('noBrowserOrNativeExecution') is True)
 matrix=r.source_json(RAW/'pr168-review/followup-validation-matrix.json')
 r.check('Followup matrix sealed without pending entries or release approval',matrix.get('sealed') is True and matrix.get('pending')==[] and matrix.get('releaseApproved') is False)
 old=r.source_json(RAW/'pr168-independent/helper-counterexamples-result.json')
 r.check('Original counterexamples retain real head and four contract failures',old.get('reviewedHead')=='a1b2f785e1bdcf13380c56b3b4c8c95093ea615c' and old.get('contractSatisfied')==4 and old.get('contractViolated')==4 and old.get('executionExitCode')==0 and at(old,'beforeIdentity.head')=='5fddf18d18cb70b3bfc5f3d39ad2684eec97aa39')

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--phase',choices=['packaging','publication'],default='packaging')
 ap.add_argument('--publication-path',action='append',default=[],help='Exact root-approved documentary path; publication phase only')
 ap.add_argument('--output',default=None,help='New basename only, within this review directory')
 args=ap.parse_args();name=args.output or ('independent-review.json' if args.phase=='packaging' else 'independent-publication-review.json')
 if Path(name).name!=name or not name.endswith('.json'):raise SystemExit('output must be a new JSON basename in the review directory')
 output=OUT/name
 if output.exists():raise SystemExit('immutable review exists; refusing overwrite: '+str(output))
 r=Review();started=now();before=identity();archive_bytes=b'';manifest_bytes=b'';records=[];fatal=None
 try:
  manifest_path=OUT/'manifest.json';receipt_path=OUT/'delivery-receipt.json'
  manifest_bytes=stable_bytes(manifest_path);manifest=json.loads(manifest_bytes);receipt=read_json(receipt_path)
  archive_path=OUT/ARCHIVE;archive_bytes=stable_bytes(archive_path);records=manifest.get('files',[])
  packaging_or_publication_check(r,args,before,receipt,manifest_bytes,archive_bytes)
  r.check('Manifest exact declared freeze/tree/archive',manifest.get('freeze')==FREEZE and manifest.get('tree')==TREE and manifest.get('archiveName')==ARCHIVE)
  r.check('Manifest and delivery declare only fixed scoped counts and limited historical Windows',manifest.get('claims')==EXPECTED_CLAIMS and receipt.get('claims')==EXPECTED_CLAIMS and receipt.get('releaseApproved') is False and receipt.get('completed') is True and any('Windows205' in x and 'limited' in x for x in manifest.get('limits',[])) and any('not a new full2177' in x for x in manifest.get('limits',[])))
  r.check('Delivery archive and manifest hashes/sizes match',at(receipt,'archive.name')==ARCHIVE and at(receipt,'archive.bytes')==len(archive_bytes) and at(receipt,'archive.sha256')==sha(archive_bytes) and receipt.get('manifestSha256')==sha(manifest_bytes) and len(archive_bytes)<95*1024*1024)
  r.check('Delivery before/after record exact clean packaging freeze',receipt.get('before')=={'head':FREEZE,'tree':TREE,'status':''} and receipt.get('after')=={'head':FREEZE,'tree':TREE,'status':''},{'before':receipt.get('before'),'after':receipt.get('after')})
  sidecars=receipt.get('sidecars',[]);sidecar_names=[s.get('name') for s in sidecars]
  r.check('Sidecars have exact expected safe local names and hashes',len(sidecar_names)==len(set(sidecar_names)) and set(sidecar_names)=={'manifest.json','followup-validation-matrix.json','source-equivalence.json'} and all(isinstance(n,str) and Path(n).name==n and regular_source(OUT/n) and sha(stable_bytes(OUT/n))==s.get('sha256') and (OUT/n).stat().st_size==s.get('bytes') for s,n in zip(sidecars,sidecar_names)))
  guard_path=OUT/'original-artifacts-guard.json';guard_bytes=stable_bytes(guard_path);guard=json.loads(guard_bytes)
  r.check('Original-artifact guard is unchanged pinned16-entry document',sha(guard_bytes)==GUARD_SHA and len(guard.get('files',[]))==16)
  guard_ok=[]
  for item in guard['files']:
   data=stable_bytes(Path(item['path']));guard_ok.append(len(data)==item['bytes'] and sha(data)==item['sha256'])
  r.check('All original13 public files plus raw matrix/old delivery originals unchanged',all(guard_ok) and len(guard_ok)==16)
  names=[x.get('archivePath') for x in records]
  r.check('Manifest paths unique, traversal-free and nonprivate',bool(records) and len(names)==len(set(names)) and 'manifest.json' not in names and all(safe_member(n) and not private_path(n) for n in names))
  source_ok=True
  for item in records:
   source=Path(item['sourceOriginalPath']);allowed=any(source.is_relative_to(p) for p in ALLOWED_ROOTS)
   if not allowed or private_path(str(source)) or source.name.endswith(('.tar','.tar.gz','.tgz')):source_ok=False;continue
   data=stable_bytes(source);r.sources[str(source)]=data
   if len(data)!=item.get('bytes') or sha(data)!=item.get('sha256'):source_ok=False
   if not item.get('scope') or not item.get('classification'):source_ok=False
   r.scan(item['archivePath'],data)
  r.check('Every selected original stays allowlisted, regular and byte-exact with scope',source_ok and len(r.sources)>0)
  with tarfile.open(fileobj=io.BytesIO(archive_bytes),mode='r:gz') as tar:
   members=tar.getmembers();actual=[m.name for m in members]
   r.check('Tar exact member multiset; no duplicates, extras, traversal or links',len(actual)==len(set(actual)) and set(actual)==set(names)|{'manifest.json'} and len(actual)==len(names)+1 and all(m.isfile() and safe_member(m.name) and not private_path(m.name) for m in members))
   expected={x['archivePath']:x for x in records};payload_ok=True;embedded=False
   for m in members:
    if not m.isfile():payload_ok=False;continue
    stream=tar.extractfile(m);data=stream.read() if stream else b''
    if m.name=='manifest.json':embedded=(data==manifest_bytes);continue
    item=expected.get(m.name)
    if item is None:payload_ok=False;continue
    if m.size!=item['bytes'] or len(data)!=item['bytes'] or sha(data)!=item['sha256'] or data!=r.sources.get(item['sourceOriginalPath']):payload_ok=False
   r.check('Embedded manifest exactly equals external manifest bytes',embedded)
   r.check('Every tar member equals manifest and original source bytes',payload_ok)
  r.check('No private WM, database, native executable, credentials or unsafe nested projects',not r.flags,{'flagCount':len(r.flags),'valuesOmitted':True,'projectArchives':len(r.projects)})
  audit_fixed_raw_scopes(r)
  # Detect mutations while auditing; do not confuse subsequent publication with this phase.
  final_sources=True
  for item in records:
   if sha(stable_bytes(Path(item['sourceOriginalPath'])))!=item['sha256']:final_sources=False
  r.check('Every new original hash remains unchanged after full audit',final_sources)
 except Exception as e:
  fatal={'type':type(e).__name__,'message':str(e)};r.check('Audit completed without missing/malformed inputs',False,fatal)
 after=identity();r.check('Repository identity stable throughout this review',before==after,{'before':before,'after':after})
 if args.phase=='packaging':r.check('Packaging review ends exact clean freeze/tree',after=={'head':FREEZE,'tree':TREE,'status':''})
 result={'schema':'geometry-card-wait-independent-review/1','phase':args.phase,'started':started,'finished':now(),'command':sys.argv,'reviewerSha256':sha(Path(__file__).read_bytes()),'freeze':FREEZE,'before':before,'after':after,'archiveName':ARCHIVE,'archiveSha256':sha(archive_bytes) if archive_bytes else None,'manifestSha256':sha(manifest_bytes) if manifest_bytes else None,'filesReviewed':len(records),'passed':sum(x['passed'] for x in r.checks),'failed':sum(not x['passed'] for x in r.checks),'checks':r.checks,'possibleSensitiveFlags':r.flags,'nestedProjectArchives':r.projects,'fatal':fatal,'releaseApproved':False,'scope':'Read-only artifact/census verification. Packaging is exact clean b822; publication is a separate explicit documentary-diff audit. No tests rerun or original evidence modified.'}
 result['reviewerCorrection']={'priorAttempt':'independent-review-attempt01.json','priorAttemptSha256':'10f566a306ec7eca4e189c0690933b02dfb13ddc1a5e5ae2742b16531a20eb49','originalEmbeddedReviewerSha256':'bc5331d3836786f50a23523c98834d7096e5f6fc02759157f35a8f4d99d95c95','reason':'The first review matched the archived checker regex declaration itself. The corrected predicate requires a concrete WM execution child path. No archive, manifest, delivery receipt, source artifact, census, or other check changed.'}
 with output.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'output':str(output),'sha256':sha(output.read_bytes()),'passed':result['passed'],'failed':result['failed'],'files':len(records)}))
 return 0 if result['failed']==0 else 1

if __name__=='__main__':raise SystemExit(main())
