"""Draft only until READY_MANIFEST is frozen after the exclusive performance run.

Reuse the existing owner repository/index and the existing body branch parent.
Keep archives in their original paths; hash-object reads them directly, so the
recorder never writes another full archive into a stdin/stdout capture.
"""
from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess,sys,traceback
HERE=Path(__file__).resolve().parent;ROOT=Path('/workspace/geo300-capacity512-work-20261024')
OUT=Path('/tmp/geo348-F73-evidence-publication-20261024');BR='codex/geo300-capacity512-20261024';DBR=BR+'-prbody'
S='73b21e64dce72f0d16ca29e18559c51815b9724d';OLD_D='9cca9a4d7ea5992366c8ef5df7ef639a455544c7'
PREFIX='evidence/geo300-capacity512-20261024/formal-F73b21e64/'
PROGRESS='evidence/geo300-capacity512-20261024/PROGRESS.md'
READY_MANIFEST_SHA256='32aa455dd8a65d1f6aa8c2027ffd5a3ded166439969c97104046578c7d0f9ba2'
report={'source_sha':S,'branch':BR,'body_branch':DBR,'old_body_sha':OLD_D,'evidence_pushed':False,'body_pushed':False,'evidence_sha':None,'body_sha':None,'commands':[],'exit':None}
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def git(*args,data=None):
 env={k:v for k,v in os.environ.items()if not k.startswith('GIT_')};argv=['git','-c','gc.auto=0','-c','maintenance.auto=false',*args]
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(argv,cwd=ROOT,input=data,capture_output=True,env=env)
 d=OUT/'commands'/f'{len(report["commands"])+1:03d}';d.mkdir(parents=True);(d/'stdout').write_bytes(r.stdout);(d/'stderr').write_bytes(r.stderr)
 row={'argv':argv,'cwd':str(ROOT),'started_utc':start,'actual_exit':r.returncode,'stdout_sha256':sha(r.stdout),'stderr_sha256':sha(r.stderr)}
 if data is not None:(d/'stdin').write_bytes(data);row['stdin_sha256']=sha(data)
 dump(d/'result.json',row);report['commands'].append(row);need(r.returncode==0,'original Git failure '+str(d));return r.stdout
def main():
 need(READY_MANIFEST_SHA256!='UNBOUND_DO_NOT_EXECUTE','Draft is not authorized for runtime; freeze reviewed manifest after R6')
 path=HERE/'READY_MANIFEST.json';need(sha(path.read_bytes())==READY_MANIFEST_SHA256,'frozen publication allowlist/pins');m=json.loads(path.read_bytes())
 need(m['source_sha']==S and m['old_body_sha']==OLD_D,'fixed original source/body')
 need(not OUT.exists(),'fresh publication output');OUT.mkdir()
 try:
  actual_payload=sum(Path(item['local']).stat().st_size for item in m['files'])
  need(actual_payload==sum(item['bytes']for item in m['files'])==m['payload_bytes'],'actual allowlist bytes match frozen payload budget')
  free=shutil.disk_usage(ROOT).free;report.update(free_before=free,payload_bytes=m['payload_bytes'],actual_payload_bytes=actual_payload,publication_min_free_bytes=m['publication_min_free_bytes'])
  need(free>=m['publication_min_free_bytes'],'publication budget only; formal100MiB unchanged')
  preloads=m['preloaded_archives'];need(len(preloads)==2,'two exact original archives preloaded')
  need(sha(Path(m['permanent_store_lease']['path']).read_bytes())==m['permanent_store_lease']['sha256'],'permanent Git object store lease unchanged')
  need(sha(Path(m['root_alternates']['path']).read_bytes())==m['root_alternates']['sha256'],'root ordinary-reader alternate unchanged')
  need({x['relative']for x in m['files']if x['archive_preload_required']}==set(preloads),'preloads match exact two archive leaves')
  need(git('rev-parse','HEAD').decode().strip()==S,'fixed clean source');need(git('symbolic-ref','--short','HEAD').decode().strip()==BR,'only owned branch')
  need(git('status','--porcelain=v1','--untracked-files=all')==b'','clean original source');need(not(ROOT/'.git/index.lock').exists(),'no concurrent source index writer')
  need(git('ls-remote','--heads','origin','refs/heads/'+BR).decode().split()==[S,'refs/heads/'+BR],'original source resolves')
  need(git('ls-remote','--heads','origin','refs/heads/'+DBR).decode().split()==[OLD_D,'refs/heads/'+DBR],'original body resolves')
  need(git('rev-parse','refs/heads/'+DBR).decode().strip()==OLD_D,'local body exact parent')
  rows=[];allow=[];oids={}
  for item in m['files']:
   rel=item['relative'];p=Path(item['local']);need((rel==PROGRESS or rel.startswith(PREFIX))and '..'not in Path(rel).parts,'owned exact prefix')
   need(p.is_file()and not p.is_symlink(),'regular original evidence');need(p.stat().st_size==item['bytes']and sha(p.read_bytes())==item['sha256'],'unchanged original bytes '+rel)
   if item['archive_preload_required']:
    pre=preloads[rel];need(pre['bytes']==item['bytes'] and pre['sha256']==item['sha256'],'preload exact original archive identity')
    need(git('cat-file','-t',pre['oid'])==b'blob\n' and git('cat-file','-s',pre['oid'])==(str(item['bytes'])+'\n').encode(),'ordinary fifth-hop reader resolves preloaded blob')
    primary=ROOT/'.git/objects'/pre['oid'][:2]/pre['oid'][2:];need(not primary.exists(),'no primary duplicate before default writer')
   oid=git('hash-object','-w','--no-filters','--',str(p)).strip()
   if item['archive_preload_required']:
    need(oid.decode()==pre['oid'] and not primary.exists(),'default writer reuses alternate blob without primary copy')
   oids[rel]=oid;rows.append(b'100644 '+oid+b'\t'+rel.encode()+b'\0');allow.append(rel)
  # The externally pinned manifest does not hash itself or its bound publisher.
  # Publish both as two explicit additional metadata leaves after validation.
  for local,name in [(path,'PUBLICATION_MANIFEST.json'),(Path(__file__),'publish_bound.py')]:
   rel=PREFIX+name;oid=git('hash-object','-w','--no-filters','--',str(local)).strip()
   oids[rel]=oid;rows.append(b'100644 '+oid+b'\t'+rel.encode()+b'\0');allow.append(rel)
  need(len(allow)==len(set(allow)),'unique publication paths')
  git('update-index','-z','--index-info',data=b''.join(rows));git('update-index','--skip-worktree','-z','--stdin',data=b''.join(x.encode()+b'\0'for x in allow))
  need(set(git('diff','--cached','--name-only','-z').rstrip(b'\0').decode().split('\0'))==set(allow),'only explicit evidence/progress changed; prior receipts preserved')
  git('diff','--cached','--check')
  for rel,oid in oids.items():need(git('rev-parse',':'+rel).strip()==oid,'staged original blob '+rel)
  git('commit','-m','Record capacity512 original failures and safe sentinel validation')
  E=git('rev-parse','HEAD').decode().strip();report['evidence_sha']=E
  need(git('show','-s','--format=%P',E).decode().strip()==S,'ordinary evidence parent')
  need(set(git('diff','--name-only','-z',S,E).rstrip(b'\0').decode().split('\0'))==set(allow),'evidence-only commit')
  for rel,oid in oids.items():need(git('rev-parse',E+':'+rel).strip()==oid,'committed original blob '+rel)
  git('push','origin','refs/heads/'+BR+':refs/heads/'+BR)
  need(git('ls-remote','--heads','origin','refs/heads/'+BR).decode().split()==[E,'refs/heads/'+BR],'public evidence exact');report['evidence_pushed']=True
  template=(HERE/'PR_BODY.template.md').read_bytes();need(sha(template)==m['body_template_sha256']and template.count(b'__EVIDENCE_HEAD__')==1,'accepted single evidence placeholder')
  body=template.replace(b'__EVIDENCE_HEAD__',E.encode());(OUT/'PR_BODY.md').write_bytes(body)
  before_index=sha((ROOT/'.git/index').read_bytes());tree={}
  for row in git('ls-tree','-z',OLD_D).rstrip(b'\0').split(b'\0'):
   meta,name=row.split(b'\t',1);tree[name]=meta
  oid=git('hash-object','-w','--stdin',data=body).strip();tree[b'PR_BODY.md']=b'100644 blob '+oid
  tree_id=git('mktree','-z',data=b''.join(meta+b'\t'+name+b'\0'for name,meta in sorted(tree.items()))).strip()
  D=git('commit-tree',tree_id.decode(),'-p',OLD_D,data=b'Describe capacity512 targeted validation and remaining placed timeouts\n').decode().strip();report['body_sha']=D
  need(git('show','-s','--format=%P',D).decode().strip()==OLD_D,'ordinary existing body parent');need(git('diff','--name-only','-z',OLD_D,D)==b'PR_BODY.md\0','only body changed')
  need(git('show',D+':PR_BODY.md')==body,'exact published body bytes')
  git('update-ref','refs/heads/'+DBR,D,OLD_D);git('push','origin','refs/heads/'+DBR+':refs/heads/'+DBR)
  need(git('ls-remote','--heads','origin','refs/heads/'+DBR).decode().split()==[D,'refs/heads/'+DBR],'public body exact');report['body_pushed']=True
  need(sha((ROOT/'.git/index').read_bytes())==before_index,'body publication preserves source index');need(git('status','--porcelain=v1','--untracked-files=all')==b'','source clean after publication')
  report['exit']=0
 except BaseException:report.update(exit=1,error=traceback.format_exc())
 finally:dump(OUT/'RESULT.json',report);print(json.dumps({k:report.get(k)for k in ['evidence_sha','body_sha','evidence_pushed','body_pushed','exit','error']}),flush=True)
 return report['exit']
if __name__=='__main__':sys.exit(main())
