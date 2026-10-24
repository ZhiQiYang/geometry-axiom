from pathlib import Path
import hashlib,json,os,stat,tarfile
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
class Review:
 def __init__(self,gate,archive_pin,version='v2'):
  self.gate=gate;self.B=Path('/workspace/train337-final-performance-collection-preparation')/(gate+'-'+version);self.checks=0;self.findings=[];self.capture_records={}
  self.p=self.j(self.B/'PACKAGE.json');self.s=self.j(self.B/'SUMMARY.json');self.iv=self.j(self.B/'RAW_INVENTORY.json');self.im={x['name']:x for x in self.iv['members']};self.paths={x['source_path'] for x in self.im.values()}
  self.ck(self.h(self.p['archive']['path'])==self.p['archive']['sha256']==archive_pin,'pinned archive')
  self.ck(self.h(self.B/'RAW_INVENTORY.json')==self.p['inventory']['sha256'],'inventory pin')
  self.ck(self.p['source_sha']==self.s['source_sha']==self.iv['source_sha']==L,'fixed L package')
  self.ck(self.p['gate']==self.s['gate']==self.iv['gate']==gate,'gate identities')
  self.ck(len(self.im)==len(self.iv['members'])==self.iv['regular_file_count'],'unique inventory')
  self.ck(sum(x['bytes'] for x in self.im.values())==self.iv['logical_original_bytes'],'logical bytes')
  seen=set()
  with tarfile.open(self.p['archive']['path'],'r:gz') as t:
   for m in t:
    self.ck(m.isfile() and m.name not in seen and not m.name.startswith('/') and '..' not in Path(m.name).parts,'safe unique member '+m.name);seen.add(m.name)
    body=t.extractfile(m).read()
    if m.name=='RAW_INVENTORY.json':self.ck(body==(self.B/'RAW_INVENTORY.json').read_bytes(),'embedded inventory');continue
    z=self.im[m.name];self.ck(len(body)==m.size==z['bytes'] and self.sh(body)==z['sha256'],'member bytes '+m.name)
    f=Path(z['source_path']);self.ck(f.is_file() and not f.is_symlink() and body==f.read_bytes(),'original byte equality '+m.name)
    self.ck(not body.startswith(b'\x7fELF'),'no ELF payload '+m.name)
  self.ck(seen==set(self.im)|{'RAW_INVENTORY.json'} and len(seen)==self.p['archive']['members'],'exact full coverage')
  self.root=Path({'p52':'/tmp/g337p52L','p189':'/workspace/g337p189L','p189-timing':'/workspace/g337p189L-timing'}[gate])
  self.outer=Path('/workspace/train337-L-'+gate+'-original-launch-20261024')
  self.r=self.j(self.root/'receipt.json');self.o=self.j(self.outer/'RESULT.json')
  self.ck(self.r['source_sha']==self.o['source_sha']==L and self.r['gate']==self.o['gate']==gate,'original gate binding')
  self.ck(self.r['launcher_exit_code']==self.o['actual_exit']==self.o['command']['actual_process_returncode']==self.s['original_driver_exit']==self.s['original_outer_exits'][gate],'real exit identity')
  self.ck(self.r['ended_utc'] and self.o['command']['ended_epoch'] and not self.r['errors'],'closed terminal originals')
  before=self.j(self.root/'before-source.json');after=self.j(self.root/'after-source.json')
  self.ck(before==after==self.s['source_before']==self.s['source_after'] and before['head']==L and before['status']=='','historical same-L clean guards')
  self.ck(self.r['original_timeouts_and_thresholds_changed'] is False,'original thresholds/timeouts unchanged')
  roots=[self.root,self.outer]
  if gate=='p52':roots.extend([self.B.parent/'p52-collection-launch',self.B.parent/'p52-v2-collection-launch'])
  for root in roots:
   for name in ['subcommands.json','commands.json']:
    for p in root.rglob(name):
     for row in self.j(p):self.capture(row,root)
  for phase in self.r['phases']:
   row=phase['outer_command'];self.capture(row,self.root)
   self.ck(self.h(phase['reaper_log'])==phase['reaper_sha256'],'phase reaper hash '+phase['name'])
   events=[json.loads(x) for x in Path(phase['reaper_log']).read_text().splitlines()]
   self.ck(events[-1]['event']=='完成' and events[-1]['primary_returncode']==phase['primary_returncode']==row['actual_process_returncode'],'phase actual primary/reaper exit '+phase['name'])
  self.excluded=self.j(self.B/'EXCLUDED_ELF_PAYLOADS.json');self.ipc=self.j(self.B/'EXCLUDED_CHROME_IPC_METADATA.json')
  self.ck(len(self.excluded)==self.s['elf_payload_excluded_count'],'ELF exclusion count')
  for x in self.excluded:
   p=Path(x['source_path']);self.ck(p.is_file() and not p.is_symlink() and p.stat().st_size==x['bytes'] and self.h(p)==x['sha256'],'retained ELF '+x['name'])
   with p.open('rb') as f:self.ck(f.read(4)==b'\x7fELF','actual ELF '+x['name'])
  self.ck(len(self.ipc)==self.s['terminal_chrome_ipc_metadata_count'],'IPC count')
  for x in self.ipc:
   p=Path(x['source_path']);q=p.relative_to(self.root).parts;s=p.lstat()
   self.ck(gate=='p52' and len(q)==5 and q[:3]==('formal','work','tmp') and (q[3].startswith('chrome-') or q[3].startswith('com.google.Chrome.')) and q[4] in ['SingletonCookie','SingletonLock','SingletonSocket'],'exact terminal IPC scope')
   self.ck(all(getattr(s,'st_ino' if k=='inode' else 'st_'+k)==x[k] for k in ['mode','size','dev','inode','uid','gid','nlink','mtime_ns']),'unchanged IPC lstat')
   if x['kind']=='symlink':
    target=os.readlink(p);body=os.fsencode(target);self.ck(stat.S_ISLNK(s.st_mode) and target==x['link_target'] and body.hex()==x['link_target_bytes_hex'] and self.sh(body)==x['link_target_sha256'],'readlink bytes only')
   else:self.ck(x['kind']=='unix-socket' and stat.S_ISSOCK(s.st_mode) and q[4]=='SingletonSocket','exact socket metadata only')
  excluded_paths={x['source_path'] for x in self.excluded+self.ipc}
  for root in roots:
   actual={str(p) for p in root.rglob('*') if not stat.S_ISDIR(p.lstat().st_mode)}
   self.ck(actual<=self.paths|excluded_paths,'all original paths represented '+str(root))
  self.ck(self.p['subject_executions']==0 and self.p['elf_payloads_included'] is False and self.p['original_elf_files_retained'] is True,'collection limitations explicit')
 def ck(self,v,n):
  self.checks+=1
  if not v:self.findings.append(n)
 @staticmethod
 def sh(b):return hashlib.sha256(b).hexdigest()
 @classmethod
 def h(cls,p):
  z=hashlib.sha256()
  with Path(p).open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):z.update(b)
  return z.hexdigest()
 @staticmethod
 def j(p):return json.loads(Path(p).read_text())
 def capture(self,row,root=None):
  d=Path(row['directory'])
  if str(d) in self.capture_records:self.ck(self.capture_records[str(d)]==row,'duplicate capture same exact original');return
  self.capture_records[str(d)]=row
  self.ck(root is None or d.is_relative_to(root),'capture containment '+str(d))
  saved=self.j(d/'result.json');extras=set(row)-set(saved)
  annotated=(self.gate=='p52' and d.parent==self.root/'formal/subcommands' and bool(extras) and extras<={'effective_environment','legacy_probe_log'} and set(saved)<=set(row) and all(row[k]==x for k,x in saved.items()))
  self.ck(saved==row or annotated,'capture OS result exact and any annotation exact scope '+str(d))
  req=self.j(d/'request.json');self.ck(req['command']==row['command'] and req['cwd']==row['cwd'],'capture argv/cwd '+str(d))
  self.ck(type(row['actual_process_returncode']) is int and row['ended_epoch']>=row['started_epoch'],'terminal capture exact exit '+str(d))
  for stream in ['stdout','stderr']:
   p=d/(stream+'.bin');self.ck(p.stat().st_size==row[stream+'_bytes'] and self.h(p)==row[stream+'_sha256'],'complete original stream '+str(p))
  p=d/'stdin.bin'
  if p.exists():self.ck(self.h(p)==row['stdin_sha256'],'complete stdin '+str(d))
  else:self.ck(row['stdin_provided'] is False and row['stdin_sha256']==self.sh(b''),'original explicit absent stdin '+str(d))
 def finish(self,extra):
  result={'schema':'independent-original-performance-package-peer-v1','source_sha':L,'gate':self.gate,'checks':self.checks,'exit_code':int(bool(self.findings)),'findings':self.findings,'archive_sha256':self.p['archive']['sha256'],'archive_members':self.p['archive']['members'],'original_bytes':self.iv['logical_original_bytes'],'original_driver_exit':self.r['launcher_exit_code'],'original_outer_exit':self.o['actual_exit'],'capture_records':len(self.capture_records),'excluded_retained_elf_count':len(self.excluded),'metadata_only_chrome_ipc_count':len(self.ipc),'no_subject_executed':True,'limitations':['This peer verifies original evidence; exit 0 here does not override any original product red.','Only historical source guards were read; no current shared ROOT/cache inspection or modification.','Excluded executable payloads remain at original paths with complete hashes; no deletion.'],**extra}
  out=Path('/workspace/train337-canvas-peer-resume')/(self.gate.upper().replace('-','_')+'_ACTUAL_PACKAGE_PEER.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out),'sha256':self.h(out),'checks':self.checks,'exit_code':result['exit_code'],'findings':self.findings}));return result['exit_code']
