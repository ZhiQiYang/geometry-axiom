from pathlib import Path
import datetime,hashlib,importlib.util,json,os,stat,subprocess
O=Path(__file__).parent;D=O/'inventory';D.mkdir();CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');assert hashlib.sha256(CAP.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec=importlib.util.spec_from_file_location('index_inventory_capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env={k:v for k,v in os.environ.items()if not k.startswith('GIT_')};env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None);rec=cap.Recorder(D,env,'4f8a794f4167c3562eb182045102e86e9e37cca9')
subjects=[('R5','/workspace/geo323-final-r5-source-20261024','a22df116c7e9f6b7d074451f1c8052d59e7e4f3e','/workspace/g337323R5/receipt.json'),('R6','/workspace/geo323-final-r6-source-20261024','2bbe54f19b2d19e8a816530f0c4edca950629a34','/workspace/g337323R6/receipt.json'),('readingL','/workspace/train337-L-reading-a-source','7af8c5d80d34cb4f49d01ba67deb78a3a6d725db','/workspace/train337-L-reading-a-results-7af8c5d8-r2/RESULT.json'),('readerF9','/workspace/geo337-F9-readers-actual-urce1nqh/source','4f8a794f4167c3562eb182045102e86e9e37cca9','/workspace/geo337-F9-readers-actual-urce1nqh/environment-retry1/RESULT.json')]
def h(b):return hashlib.sha256(b).hexdigest()
def meta(p):
 s=p.lstat();return dict(dev=s.st_dev,inode=s.st_ino,nlink=s.st_nlink,mode=s.st_mode,uid=s.st_uid,gid=s.st_gid,bytes=s.st_size,allocated=s.st_blocks*512,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,atime_ns=s.st_atime_ns)
def exact(p):
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME)
 with os.fdopen(fd,'rb')as f:return f.read()
rows=[]
for name,root,head,terminal in subjects:
 r=Path(root);g=r/'.git';p=g/'index';assert r.resolve()==r and g.resolve()==g and g.is_dir() and not g.is_symlink();m0=meta(p);assert stat.S_ISREG(m0['mode']) and m0['nlink']==1
 values={};commands=[]
 for label,args in [('head',['rev-parse','HEAD']),('staged',['diff','--cached','--no-ext-diff','--raw','-z']),('status',['status','--porcelain=v1','-z','--untracked-files=all']),('refs',['for-each-ref','--format=%(refname) %(objectname)'])]:
  row,so,se=rec.run(['git','--no-optional-locks','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=r,timeout=None,check=True,source_sha=head,source_variant='Read-only retired OWN index-cache preservation inventory; no product acceptance');assert not se;values[label]=so;commands.append(row)
 assert values['head'].decode().strip()==head and not values['staged']
 want=b'' if name!='readerF9' else b' D current_geometry.c\0 D geometry-guide/current_geometry-\xe5\xb0\x8e\xe8\xae\x80.html\0 D geometry-guide/\xe5\x85\xac\xe7\x90\x86\xe5\xb1\xa4-\xe9\x96\xb1\xe8\xae\x80\xe5\x99\xa8.html\0'
 assert values['status']==want,(name,values['status'])
 locks=list(g.glob('*.lock'))+list((g/'refs').rglob('*.lock'));assert not locks
 raw=exact(p);m1=meta(p);assert all(m0[k]==m1[k]for k in m0 if k!='atime_ns');assert raw[:4]==b'DIRC'
 terminalraw=Path(terminal).read_bytes();tr=json.loads(terminalraw);assert tr.get('source_sha',tr.get('sha'))==head
 if name in ('R5','R6'):assert tr['wrapper_exit']==1 and tr['status'].startswith('完成')
 elif name=='readingL':assert tr['passed'] and tr.get('endedUTC')
 else:assert tr['exit']==0 and tr['all_three_passed'] and tr.get('ended_epoch')
 preserve={}
 for q in [g/'HEAD',g/'config',g/'packed-refs',g/'info/sparse-checkout']:
  if q.exists():assert q.is_file() and not q.is_symlink();preserve[str(q)]={'bytes':q.stat().st_size,'sha256':h(exact(q))}
 rows.append({'role':name,'root':root,'head':head,'gitdir':str(g),'gitdir_device_inode':[g.stat().st_dev,g.stat().st_ino],'index':str(p),'index_metadata':m1,'index_sha256':h(raw),'git_status_hex':values['status'].hex(),'git_status_sha256':h(values['status']),'git_refs_sha256':h(values['refs']),'staged_diff_empty':True,'other_git_metadata':preserve,'terminal':{'path':terminal,'sha256':h(terminalraw),'bytes':len(terminalraw)},'original_commands':commands})
assert len({tuple(x['gitdir_device_inode'])for x in rows})==4 and len({(x['index_metadata']['dev'],x['index_metadata']['inode'])for x in rows})==4
plan={'schema':'geo337-four-retired-WS-index-preservation/1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'subjects':rows,'index_allocated_total':sum(x['index_metadata']['allocated']for x in rows),'archive_destination':'/dev/shm/geometry-axiom-geo337-20261025/retired-four-WS-indexes-20261025','archive_only':True,'unlink_implemented':False,'guard_policy':'Root lease plus fresh consumer/locks, HEAD/staged/status/refs/index exact identity; archive complete original bytes in SHM then normal publish and remote full blob validation before any separate root-authorized cache removal.','forbidden':['source leaves','dirty worktree changes','fixtures','receipts','refs','objects','active NATIVE/cache'],'restore_contract':'Four roots INACTIVE_REQUIRE_INDEX_RESTORE only after later removal; exact gzip bytes and original mode/uid/gid/mtime/atime restore to a fresh index with no clobber; inode/ctime cannot be reproduced. Original source D status remains unchanged.'}
q=O/'PLAN.json';q.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q.read_bytes()),'allocated_bytes':plan['index_allocated_total'],'commands':len(rec.rows),'index_unlinked':False}))
