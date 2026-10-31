"""Read and package one already-terminal original final-L browser job. Never runs it."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,stat,tarfile
H=lambda b:hashlib.sha256(b).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
p=argparse.ArgumentParser();p.add_argument('--job',choices=('canvas','assembly','documents','grid','space','timber'),required=True);a=p.parse_args();job=a.job;sha='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
base=Path('/workspace/train337-browser-L-'+job);launch=Path(str(base)+'-launch');orig=base/'original'/job;pool=Path('/workspace/train337-browser-pool-L-7af8c5d8');dest=Path('/workspace/train337-browser-terminal-collection')/job;dest.mkdir();wr=json.loads((launch/'receipt.json').read_text());r=json.loads((orig/'receipt.json').read_text());assert wr['source_sha']==r['sha']==sha and wr['job']==r['job']==job and r.get('ended') and r.get('exit_code') is not None and wr.get('wrapper_exit') is not None
assert H((orig/'receipt.json').read_bytes())==wr['original_receipt_sha256'];files={};excluded=[];special=[]
def add(name,path):
 assert name not in files;files[name]=path
for prefix,root in [('launch',launch),('original',base/'original')]:
 for path in sorted(root.rglob('*')):
  if path.is_file() or path.is_symlink():add(prefix+'/'+str(path.relative_to(root)),path)
cacheparts={'Cache','Code Cache','GPUCache','DawnGraphiteCache','DawnWebGPUCache','ShaderCache','GrShaderCache','GraphiteDawnCache'}
for path in sorted((base/'tmp').rglob('*')):
 info=path.lstat();rel=path.relative_to(base/'tmp');parts=set(rel.parts)
 if stat.S_ISDIR(info.st_mode):continue
 if parts&cacheparts:
  excluded.append({'path':str(path),'bytes':info.st_size,'reason':'rebuildable Chrome cache leaf; not removed','sha256':None});continue
 if stat.S_ISREG(info.st_mode):
  with path.open('rb') as f:magic=f.read(4)
  if magic==b'\x7fELF':excluded.append({'path':str(path),'bytes':info.st_size,'reason':'rebuildable ELF payload only; original file retained; fingerprint sidecar included','sha256':H(path.read_bytes())});continue
 if stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):add('temporary/'+str(rel),path)
 else:special.append({'path':str(path),'mode':oct(info.st_mode),'bytes':info.st_size,'reason':'non-regular IPC node; no serializable file payload, retained in place'})
for path in sorted(pool.iterdir()):
 if path.is_file():add('pool-preparation/'+path.name,path)
layout=pool/'layout'
for path in sorted(layout.iterdir()):
 if path.is_file() and path.name!='GUARD_LATEST.json':add('pool-preparation/layout/'+path.name,path)
guardlogs=[]
for label in ('before_guard','after_guard'):
 cmd=wr[label];matches=[]
 for d in sorted((layout/'guard-logs').iterdir()):
  if d.is_dir() and (d/'COMMANDS.json').is_file() and cmd['started_epoch']<=d.stat().st_mtime<=cmd['ended_epoch']:matches.append(d)
 assert len(matches)==1,(label,matches)
 d=matches[0];guardlogs.append({'phase':label,'directory':str(d),'selection':'unique completed directory mtime within original guard command interval; no later guard/later GUARD_LATEST relabeled'})
 for path in sorted(d.rglob('*')):
  if path.is_file():add('original-pool-guards/'+label+'/'+str(path.relative_to(d)),path)
for path in [Path('/workspace/launch_geo337_L_browser.py'),Path('/tmp/browser_readonly_pool_preparer_v3_seed.py'),Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py'),Path('/workspace/geo261-environment/reap_children.py'),Path(__file__)]:add('tools/'+path.name,path)
summary={'schema':'geo337-final-L-original-browser-terminal-collection/1','sourceSHA':sha,'job':job,'createdUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalExit':r['exit_code'],'wrapperExit':wr['wrapper_exit'],'passed':wr['passed'],'overOriginalCITimeout':r['over_ci_timeout'],'originalCITimeoutMinutes':r['ci_timeout_minutes'],'elapsedSeconds':r['seconds'],'sourceBefore':r['checkout_before'],'sourceAfter':r['checkout_after'],'versions':[{'argv':x['command'],'exit':x['actual_process_returncode'],'stdout':Path(x['stdout']).read_text()} for x in r['versions']],'originalPoolGuardLogs':guardlogs,'excluded':excluded,'nonRegularNodes':special,'noExistingFileDeleted':True,'noSubjectRerun':True,'limits':['Original exposed command stdout/stderr only; no hidden compiler/test pipe interception or files already removed by original cleanup are reconstructed.','No ROOT/SEED/pool/Git/source payload copied; pool immutable plan/tree/raw preparation and original completed guard command streams are included.','GUARD_LATEST.json is shared mutable state and may already have been replaced by later jobs; it is not relabeled as the documents original. Original per-guard closed Git logs and actual guard argv/exit/fullstreams are retained.','Terminal profile non-cache files/symlinks retained; Chrome cache payloads excluded with inventory, no removal. ELF payloads excluded with actual hashes; original fingerprint sidecars retained.','GitHub artifact upload actions are preserved as original local artifact saves, not claimed uploaded to GitHub.','No independently predecoded host API launcher pipe is invented.']}
save(dest/'SUMMARY.json',summary);add('SUMMARY.json',dest/'SUMMARY.json');idx={}
for name,path in files.items():
 s=path.lstat()
 if path.is_symlink():b=os.readlink(path).encode();idx[name]={'originalPath':str(path),'type':'symlink','target':os.readlink(path),'bytes':len(b),'sha256':H(b)}
 else:b=path.read_bytes();idx[name]={'originalPath':str(path),'type':'regular','bytes':len(b),'sha256':H(b)}
save(dest/'RAW_INVENTORY.json',idx);archive=dest/'ORIGINAL_BROWSER_JOB_AND_TEMP_OUTPUTS.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=6,dereference=False) as t:
 for name,path in files.items():t.add(path,arcname=name,recursive=False)
 t.add(dest/'RAW_INVENTORY.json',arcname='RAW_INVENTORY.json',recursive=False)
seen=set()
with tarfile.open(archive,'r:gz') as t:
 for m in t:
  assert m.name not in seen;seen.add(m.name)
  if m.name=='RAW_INVENTORY.json':assert t.extractfile(m).read()==(dest/'RAW_INVENTORY.json').read_bytes();continue
  x=idx[m.name]
  if x['type']=='symlink':assert m.issym() and m.linkname==x['target']
  else:
   b=t.extractfile(m).read();assert len(b)==x['bytes'] and H(b)==x['sha256'] and Path(x['originalPath']).read_bytes()==b,m.name
assert seen==set(idx)|{'RAW_INVENTORY.json'}
package={'sourceSHA':sha,'job':job,'archive':str(archive),'archiveBytes':archive.stat().st_size,'archiveSHA256':H(archive.read_bytes()),'memberCount':len(seen),'originalLogicalBytes':sum(x['bytes'] for x in idx.values()),'rawInventorySHA256':H((dest/'RAW_INVENTORY.json').read_bytes()),'producerRoundtripComplete':True,'originalExit':r['exit_code'],'wrapperExit':wr['wrapper_exit'],'excludedELFs':sum(x['sha256'] is not None for x in excluded),'excludedCacheFiles':sum(x['sha256'] is None for x in excluded),'noFilesDeleted':True,'subjectRerun':False};save(dest/'PACKAGE.json',package);print(json.dumps(package))
