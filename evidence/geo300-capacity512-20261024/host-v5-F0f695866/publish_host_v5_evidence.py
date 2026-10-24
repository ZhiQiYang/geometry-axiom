"""Publish reviewed v5 raw source/progress evidence and update existing PR body."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,traceback
H=Path(__file__).resolve().parent; R=Path('/workspace/geo300-capacity512-work-20261024')
OUT=H/'host-v5-evidence-publication'; S='0f695866c0ba12d2c70dfd7d40628d0fda0f905f'; BR='codex/geo300-capacity512-20261024'; DBR=BR+'-prbody'; OLD_D='fd206036052bfb4f8c7ea0025c31b1b2a21cc4b8'
BASE='evidence/geo300-capacity512-20261024/'; PREFIX=BASE+'host-v5-F0f695866/'
MIN_FREE=25*1024*1024; MAX_PAYLOAD=1000000; MAX_INDEX=6*1024*1024
P=Path('/workspace/geo300-capacity512-host-v5-peer-20261024'); BODY_PEER=Path('/workspace/train337-canvas-peer-resume/GEO348_HOST_V5_BODY_STATIC_PEER.json')
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
need(not OUT.exists(),'fresh output')
need(shutil.disk_usage(R).free>=MIN_FREE,'original25MiB publication environment guard')
need((R/'.git/index').stat().st_size<=MAX_INDEX,'root authorized6MiB index peak')
pins={P/'REVIEW.json':'7554687f38d886489bc8176049f3560d4dfbb9c3f823248620d234220af135c9',P/'PUBLISHER_REVIEW.json':'8f45127f1376b39931b470089ebc0abb88fffcca24c4f8e8bc9291c7f54b8874',P/'PUBLICATION_REVIEW.json':'586dd431994f055d83cb6525d65b55575d2412c50f51e9b6349fa4a7c8b9273a',BODY_PEER:'e5e565ea0f20121ad7b1f2bf31a8f775dcf266cc27d792a0f9472971b63c0ff7'}
for p,h in pins.items():need(sha(p.read_bytes())==h,'accepted peer '+str(p))
need(sha((H/'PR_BODY.host-v5.template.md').read_bytes())==json.loads(BODY_PEER.read_text())['body_template_sha256'],'accepted body template exact')
files={BASE+'PROGRESS.md':H/'PROGRESS.host-v5.md'}
for n in ['host-v2-draft','host-v3-draft','host-v4-draft','host-v5-draft','host-v5-source-publication']:
 for p in (H/n).rglob('*'):
  if p.is_file():files[PREFIX+str(p.relative_to(H))]=p
for p in P.iterdir():
 if p.is_file():files[PREFIX+'peer/'+p.name]=p
for n in ['DECLARATION_COUNT_FIX.patch','DECLARATION_COUNT_FIX_DESIGN.md','FACE_OBSTACLE_CAPACITY_STATIC_REVIEW.json','FACE_OBSTACLE_CAPACITY_CLARIFICATION.md','FORMAL_H7_W7_F0f695866_PLAN.md','H_PIPE_CAPTURE_PLAN.md','PLACED_512_REPLAY_STACK_PLAN.md','PR_BODY.host-v5.template.md','PROGRESS.host-v5.md','publish_host_v5_source.py','publish_host_v5_evidence.py']:
 files[PREFIX+n]=H/n
files[PREFIX+'peer/'+BODY_PEER.name]=BODY_PEER
payload=sum(p.stat().st_size for p in files.values());need(payload<MAX_PAYLOAD,'root authorized less than1MB payload')
cap=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');need(sha(cap.read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762','original recorder')
spec=importlib.util.spec_from_file_location('c387',cap);c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
OUT.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
for key in ['GIT_INDEX_FILE','GIT_DIR','GIT_WORK_TREE','GIT_COMMON_DIR']:env.pop(key,None)
rec=c.Recorder(OUT,env,S)
def run(args,data=None):return rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=R,data=data,timeout=180,source_sha=S,source_variant='evidence only; all runtime UNRUN')[1]
report={'source_sha':S,'product_code_sha':'400a6d0ca50f3aca104fb569c77c8ef753c93355','old_body_sha':OLD_D,'payload_bytes':payload,'index_peak_limit':MAX_INDEX,'runtime':'UNRUN','evidence_pushed':False,'body_pushed':False,'exit_code':None,'files':{k:{'local':str(v),'bytes':v.stat().st_size,'sha256':sha(v.read_bytes())} for k,v in files.items()}}
try:
 rec.run(['df','-B1','/workspace','/tmp'],cwd=R)
 need(shutil.disk_usage(R).free>=MIN_FREE,'fresh25MiB guard')
 need(run(['rev-parse','HEAD']).decode().strip()==S,'source F exact')
 need(run(['symbolic-ref','--short','HEAD']).decode().strip()==BR,'own branch')
 need(run(['status','--porcelain=v1','--untracked-files=all'])==b'','clean owned source')
 need(run(['ls-remote','--heads','origin','refs/heads/'+BR]).decode().split()==[S,'refs/heads/'+BR],'remote F exact')
 need(run(['ls-remote','--heads','origin','refs/heads/'+DBR]).decode().split()==[OLD_D,'refs/heads/'+DBR],'remote oldD exact')
 index_rows=[]
 for rel,p in files.items():
  oid=run(['hash-object','-w','--stdin'],p.read_bytes()).strip();index_rows.append(b'100644 '+oid+b'\t'+rel.encode()+b'\0')
 run(['update-index','-z','--index-info'],b''.join(index_rows))
 run(['update-index','--skip-worktree','-z','--stdin'],b''.join(p.encode()+b'\0' for p in files))
 names=run(['diff','--cached','--name-only','-z']).rstrip(b'\0').split(b'\0');need(set(names)=={p.encode() for p in files},'exact evidence allowlist, no prior receipts removed')
 run(['diff','--cached','--check'])
 for rel,p in files.items():need(run(['show',':'+rel])==p.read_bytes(),'staged bytes '+rel)
 run(['commit','-m','docs(GEO-300): publish corrected capacity acceptance plan and source evidence'])
 E=run(['rev-parse','HEAD']).decode().strip();report['evidence_sha']=E
 need(run(['show','-s','--format=%P',E]).decode().strip()==S,'ordinary E parentF')
 need(set(run(['diff','--name-only','-z',S,E]).rstrip(b'\0').split(b'\0'))==set(names),'only allowlisted evidence closure')
 run(['push','origin','refs/heads/'+BR+':refs/heads/'+BR]);report['evidence_pushed']=True
 need(run(['ls-remote','--heads','origin','refs/heads/'+BR]).decode().split()==[E,'refs/heads/'+BR],'public E exact')
 template=(H/'PR_BODY.host-v5.template.md').read_bytes();need(template.count(b'__V5_EVIDENCE_HEAD__')==1,'single E placeholder');body=template.replace(b'__V5_EVIDENCE_HEAD__',E.encode());(OUT/'PR_BODY.md').write_bytes(body)
 before_index=sha((R/'.git/index').read_bytes());entries=run(['ls-tree','-z',OLD_D]);tree={}
 for row in entries.rstrip(b'\0').split(b'\0'):
  meta,name=row.split(b'\t',1);tree[name]=meta
 oid=run(['hash-object','-w','--stdin'],body).strip();tree[b'PR_BODY.md']=b'100644 blob '+oid
 treeid=run(['mktree','-z'],b''.join(meta+b'\t'+name+b'\0' for name,meta in sorted(tree.items()))).strip()
 D=run(['commit-tree',treeid.decode(),'-p',OLD_D],b'docs(GEO-300): update capacity draft with corrected host acceptance scope\n').decode().strip();report['body_sha']=D
 need(run(['diff','--name-only','-z',OLD_D,D])==b'PR_BODY.md\0','body-only ordinary descendant')
 need(run(['show','-s','--format=%P',D]).decode().strip()==OLD_D,'body parent preserved')
 run(['update-ref','refs/heads/'+DBR,D,OLD_D]);run(['push','origin','refs/heads/'+DBR+':refs/heads/'+DBR]);report['body_pushed']=True
 need(run(['ls-remote','--heads','origin','refs/heads/'+DBR]).decode().split()==[D,'refs/heads/'+DBR],'public D exact')
 need(run(['show',D+':PR_BODY.md'])==body,'public body exact')
 need(sha((R/'.git/index').read_bytes())==before_index,'body leaves source index unchanged')
 need(run(['status','--porcelain=v1','--untracked-files=all'])==b'','clean final source')
 report.update(exit_code=0,body_sha256=sha(body))
except BaseException:
 report.update(exit_code=1,error=traceback.format_exc());raise
finally:
 report['command_count']=len(rec.rows);(OUT/'RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False))
