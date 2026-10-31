"""Collect the already-terminal original full native F9 run; never launch it.

Old preserved cache is excluded as a whole; its original before/preserved manifests
remain. Only registry ordinary ELF payloads are omitted, with live terminal hashes
and sidecars retained. Unknown/counterfactual ELF files are included by default.
"""
from pathlib import Path
import ast,datetime,hashlib,json,os,stat,subprocess,tarfile,importlib.util
SHA='4f8a794f4167c3562eb182045102e86e9e37cca9';ROOT=Path('/tmp/train337-323-f64d638f-source');OUT=Path('/tmp/geo337-F9-native-4f8a794f-20261025');OUTER=Path('/tmp/geo337-F9-native-launch-20261025');CACHE=Path('/tmp/geometry-tests');DEST=Path('/tmp/geo337-F9-native-terminal-package-20261025')
H=lambda b:hashlib.sha256(b).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def walk(root,prune=()):
 for d,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=[n for n in dirs if Path(d)/n not in prune]
  for name in sorted(files):yield Path(d)/name
  for name in list(dirs):
   p=Path(d)/name
   if p.is_symlink():dirs.remove(name);yield p

GUARD_PATH=Path(__file__).with_name('terminal_guard.py')
GUARD_PIN='226015a2722a447ec3fceb5b18eaa5c918f7b0befd730cf2925fdf96aaef1834'
def main():
 assert H(GUARD_PATH.read_bytes())==GUARD_PIN,'terminal guard exact source'
 spec=importlib.util.spec_from_file_location('native_terminal_guard',GUARD_PATH);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
 terminal=guard.begin()
 assert not DEST.exists(),'fresh completed output required; never overwrite a previous attempt'
 # Root-bound original exec FINAL, outer RESULT, native RECEIPT and workflow receipt are all terminal.
 outer=terminal['outer'];r=terminal['native']
 DEST.mkdir();files={};excluded=[];special=[]
 def add(name,p):assert name not in files;files[name]=p
 for prefix,root in [('outer',OUTER),('native',OUT)]:
  for p in walk(root,(OUT/'preserved-global-geometry-tests',)):
   if p.is_file() or p.is_symlink():add(prefix+'/'+str(p.relative_to(root)),p)
 # Original registry source comes from exact F9 Git objects, never mutable ROOT.
 argv=['git','--git-dir=/workspace/geometry-axiom/.git','show',SHA+':tests/binaries.py'];proc=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE);assert proc.returncode==0
 (DEST/'registry-original-Git.stdout.bin').write_bytes(proc.stdout);(DEST/'registry-original-Git.stderr.bin').write_bytes(proc.stderr);tree=ast.parse(proc.stdout);reg=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REGISTRY' for t in n.targets));ordinary={ast.literal_eval(n.args[1]) for n in reg.elts if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Binary'}
 for p in walk(CACHE):
  info=p.lstat();rel=p.relative_to(CACHE)
  if stat.S_ISREG(info.st_mode):
   with p.open('rb') as f:magic=f.read(4)
   if magic==b'\x7fELF' and len(rel.parts)==1 and p.name in ordinary and p.with_name(p.name+'.fingerprint.json').is_file():
    try:
     side=json.loads(p.with_name(p.name+'.fingerprint.json').read_bytes());raw=p.read_bytes();valid=isinstance(side,dict) and side.get('exe')==p.name and side.get('exe_size')==len(raw) and side.get('exe_sha256')==H(raw)
    except (ValueError,TypeError,KeyError) as error:
     valid=False;special.append({'originalPath':str(p),'reason':'Invalid ordinary ELF sidecar; both raw payload and sidecar remain included','detail':repr(error)})
    if valid:
     excluded.append({'originalPath':str(p),'bytes':len(raw),'sha256':H(raw),'reason':'original registry ordinary executable payload; sidecar included; no deletion'});continue
    special.append({'originalPath':str(p),'reason':'Ordinary ELF not excluded because its terminal sidecar was not valid; full payload retained'})
  if stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):add('new-runtime-cache/'+str(rel),p)
  else:special.append({'originalPath':str(p),'mode':oct(info.st_mode),'reason':'non-regular node, no serializable file payload; not deleted'})
 for p in [Path(__file__),Path('/tmp/launch_geo337_F9_native_20261025.py'),Path('/tmp/native-final-executable-preparation/run_full_native_workflow_v2.py'),Path('/workspace/geo261-environment/run_workflow_round.py'),Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py'),Path('/workspace/geo261-environment/reap_children.py')]:add('tools/'+p.name,p)
 for name,proof in terminal['bindings'].items():
  if name=='exec_final':add('original-exec-FINAL.json',Path(proof['path']))
 add('collection/BOUND_REQUEST.json',Path(terminal['request']['path']));add('tools/terminal_guard.py',GUARD_PATH)
 summary={'schema':'geo337.F9-original-native-terminal-collection/1','sourceSHA':SHA,'createdUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalExecFinalExit':terminal['exec_final']['exit_code'],'originalTerminalBindingIssues':terminal['issues'],'originalFormalCandidate':terminal['formal_candidate'],'formalAcceptanceRequiresActualPeer':True,'onlyOriginalAllowedSkip':'Windows-only GDI unavailable on Linux; strict registry and all other original assertions unchanged','outerExit':outer['actual_exit'],'workflowExit':r.get('original_workflow_exit'),'CI35MinuteGateExit':r.get('ci_35_minute_gate_exit'),'originalDriverExit':r['actual_exit'],'passed':r['passed'],'metadataErrors':r['metadata_errors'],'sourceBefore':r.get('source_before'),'sourceAfter':r.get('source_after'),'expectedFullRows':230,'fullRowsNotInferredFromNames':'Independent actual peer must parse original final230 rows/count/allowed skips, including original errors or timeout; collector does not change judge.','ordinaryRegistryExeNames':sorted(ordinary),'excludedOrdinaryELFs':excluded,'excludedOldCache':{'exactPath':str(OUT/'preserved-global-geometry-tests'),'payloadNotTraversed':True,'originalManifestsIncluded':['native/GLOBAL_CACHE_BEFORE.json','native/GLOBAL_CACHE_PRESERVED.json'],'meaning':'historical cache preserved in place, not claimed as new native outputs'},'nonRegularNodes':special,'rawLimits':r['original_internal_pipe_limit'],'nativeCacheModifiedByCollector':False,'ROOTModifiedByCollector':False,'noFilesDeleted':True,'noSubjectRerun':True,'originalRegistryGitRead':{'argv':argv,'exit':proc.returncode,'stdoutSHA256':H(proc.stdout),'stderrSHA256':H(proc.stderr)}}
 save(DEST/'SUMMARY.json',summary)
 for p in [DEST/'SUMMARY.json',DEST/'registry-original-Git.stdout.bin',DEST/'registry-original-Git.stderr.bin']:add(p.name,p)
 inv={}
 for name,p in files.items():
  if p.is_symlink():b=os.readlink(p).encode();inv[name]={'originalPath':str(p),'kind':'symlink','target':os.readlink(p),'bytes':len(b),'sha256':H(b)}
  else:b=p.read_bytes();inv[name]={'originalPath':str(p),'kind':'regular','bytes':len(b),'sha256':H(b)}
 guard.stable(terminal);budget=guard.budget(terminal,inv);save(DEST/'RAW_INVENTORY.json',inv);save(DEST/'BUDGET.json',dict(budget,oldCachePayloadNotRead=True,noSecondSourceCheckout=True))
 arc=DEST/'ORIGINAL_FULL_NATIVE_WORKFLOW_LOGS_AND_RUNTIME_SIDECARS.tar.gz'
 with tarfile.open(arc,'w:gz',compresslevel=6,dereference=False) as t:
  for name,p in files.items():t.add(p,arcname=name,recursive=False)
  t.add(DEST/'RAW_INVENTORY.json',arcname='RAW_INVENTORY.json',recursive=False);t.add(DEST/'BUDGET.json',arcname='BUDGET.json',recursive=False)
 seen=set()
 with tarfile.open(arc,'r:gz') as t:
  for m in t:
   assert m.name not in seen;seen.add(m.name)
   if m.name in ('RAW_INVENTORY.json','BUDGET.json'):assert t.extractfile(m).read()==(DEST/m.name).read_bytes();continue
   row=inv[m.name]
   if row['kind']=='symlink':assert m.issym() and m.linkname==row['target']
   else:
    b=t.extractfile(m).read();assert len(b)==row['bytes'] and H(b)==row['sha256'] and Path(row['originalPath']).read_bytes()==b
 assert seen==set(inv)|{'RAW_INVENTORY.json','BUDGET.json'};guard.stable(terminal);pkg={'collectionExit':0,'originalExecFinalExit':terminal['exec_final']['exit_code'],'originalTerminalBindingIssues':terminal['issues'],'originalFormalCandidate':terminal['formal_candidate'],'formalAcceptanceRequiresActualPeer':True,'sourceSHA':SHA,'archive':str(arc),'archiveBytes':arc.stat().st_size,'archiveSHA256':H(arc.read_bytes()),'memberCount':len(seen),'selectedOriginalLogicalBytes':sum(r['bytes'] for r in inv.values()),'rawInventorySHA256':H((DEST/'RAW_INVENTORY.json').read_bytes()),'roundtripAllSelectedOriginalBytes':True,'originalNativeExit':r['actual_exit'],'workflowExit':r.get('original_workflow_exit'),'CI35GateExit':r.get('ci_35_minute_gate_exit'),'outerExit':outer['actual_exit'],'noFilesDeleted':True,'subjectRerun':False};save(DEST/'PACKAGE.json',pkg);print(json.dumps(pkg))
if __name__=='__main__':main()
