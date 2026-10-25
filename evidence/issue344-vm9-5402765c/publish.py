from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,re,shutil,traceback
P=Path(__file__).resolve().parent;O=Path('/tmp/geo344-S540-vm9-publication-20261024');R=Path('/workspace/issue320-work-20261024');DROOT=Path('/workspace/issue320-prbody-work-20261024')
S='5402765c795769a77a7b249de1e3db80045a41de';E0='c9303843208a9e4f90085075acec920a3da1e856';F='2bbe54f19b2d19e8a816530f0c4edca950629a34';D0='a710224cd488ceee5d0dd7a4d4f3d4f2201db5b4';BR='codex/issue320-connection-recovery-20261024';PREFIX='evidence/issue344-vm9-5402765c';URL='https://github.com/ZhiQiYang/geometry-axiom.git'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');H=lambda b:hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
parser=argparse.ArgumentParser();parser.add_argument('--manifest-sha256',required=True);args=parser.parse_args()
need(re.fullmatch(r'[0-9a-f]{64}',args.manifest_sha256) is not None,'exact manifest CLI pin syntax')
manifest_bytes=(P/'PUBLICATION_FILES.json').read_bytes();need(H(manifest_bytes)==args.manifest_sha256,'exact external manifest binding');manifest=json.loads(manifest_bytes);need(manifest['source_sha']==S,'exact source manifest binding');need(not O.exists(),'fresh publication output');need(H(CAP.read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762','original capture')
for x in manifest['files']:
 raw=Path(x['source']).read_bytes();need(len(raw)==x['bytes']and H(raw)==x['sha256'],'frozen payload '+x['name'])
need(H((P/'PR_BODY.template.md').read_bytes())==manifest['body_sha256'],'frozen body');need(H(Path(__file__).read_bytes())==manifest['publisher_sha256'],'frozen publisher')
need(shutil.disk_usage('/workspace').free>=20*1024*1024 and shutil.disk_usage('/tmp').free>=16*1024*1024,'20MiBWS/16MiBTMP metadata publication guard')
O.mkdir();env={k:v for k,v in os.environ.items()if not k.startswith('GIT_') and k not in ('PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','LD_PRELOAD')};env.update(PYTHONDONTWRITEBYTECODE='1',LC_ALL='C.UTF-8',GIT_OPTIONAL_LOCKS='0',GIT_NO_LAZY_FETCH='1')
sp=importlib.util.spec_from_file_location('cap',CAP);cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap);rec=cap.Recorder(O,env,S)
report={'source_sha':S,'source_branch':BR,'prior_evidence_remote':E0,'evidence_parent':E0,'body_parent':D0,'exit':None,'pushed':{},'new_formal_executions':0,'ledger_regenerated':False,'architecture_regenerated':False}
def g(*args,cwd=R):
 row,out,err=rec.run(['git','--no-optional-locks','-c','gc.auto=0','-c','maintenance.auto=false','-c','remote.origin.url='+URL,*args],cwd=cwd,timeout=None,check=False,source_variant='owned evidence/body publication only; no subject execution');need(row['actual_process_returncode']==0,'original Git exit '+row['directory']);return out
def remote(b):
 rows=g('ls-remote','--heads','origin','refs/heads/'+b).decode().splitlines();need(len(rows)==1 and rows[0].split('\t')[1]=='refs/heads/'+b,'exact one remote ref');return rows[0].split('\t')[0]
def clean(root,head,branch):
 need(g('rev-parse','HEAD',cwd=root).decode().strip()==head,'owned expected head');need(g('symbolic-ref','--short','HEAD',cwd=root).decode().strip()==branch,'owned branch');need(g('status','--porcelain=v1','--untracked-files=all',cwd=root)==b'' and g('diff','--cached','--name-status',cwd=root)==b'','original clean index and worktree')
try:
 clean(R,E0,BR);clean(DROOT,D0,BR+'-prbody');need(g('show','-s','--format=%P',S).decode().split()==['42790be40eee56efada08de84ab2acb1681df981',F],'normal source merge parents')
 need(all(p.startswith('evidence/')for p in g('diff','--name-only',S,E0).decode().splitlines()),'priorE source closure still exactS');need(remote(BR)==E0 and remote(BR+'-prbody')==D0,'fresh remote parents exact; never force');dest=R/PREFIX;need(not dest.exists() and g('ls-tree',S,'--',PREFIX)==b'','new evidence prefix only');dest.mkdir(parents=True)
 names=[]
 for x in manifest['files']:
  need('/' not in x['name'] and x['name'] not in ('','.','..'),'safe exact leaf');target=dest/x['name'];target.write_bytes(Path(x['source']).read_bytes());names.append(PREFIX+'/'+x['name'])
 dump(dest/'PUBLICATION_INDEX.json',manifest);names.append(PREFIX+'/PUBLICATION_INDEX.json');g('add','--force','--sparse','--',*names)
 need(sorted(g('diff','--cached','--name-status').decode().splitlines())==sorted('A\t'+n for n in names),'exact additions only; original omitted receipts/index blobs preserved');g('diff','--cached','--check');g('commit','-m','Record same-source recovery VM controls and strict selected row')
 E=g('rev-parse','HEAD').decode().strip();need(g('show','-s','--format=%P',E).decode().strip()==E0,'normal evidence parent');need(sorted(g('diff','--name-only',E0,E).decode().splitlines())==sorted(names),'only expected evidence source delta');report['evidence_sha']=E;dump(O/'LIVE.json',report)
 need(remote(BR)==E0,'remote unchanged before normal push');g('push','origin',E+':refs/heads/'+BR);need(remote(BR)==E,'exact published E');report['pushed']['evidence']=True;dump(O/'LIVE.json',report)
 template=(P/'PR_BODY.template.md').read_text();need(template.count('__EVIDENCE_HEAD__')==1,'one evidence placeholder');body=template.replace('__EVIDENCE_HEAD__',E).encode();(O/'PR_BODY.md').write_bytes(body);(DROOT/'PR_BODY.md').write_bytes(body);g('add','--force','--sparse','--','PR_BODY.md',cwd=DROOT)
 need(g('diff','--cached','--name-status',cwd=DROOT).decode().splitlines()==['M\tPR_BODY.md'],'body only');g('diff','--cached','--check',cwd=DROOT);g('commit','-m','Update connection recovery current state with original nine-case evidence',cwd=DROOT);D=g('rev-parse','HEAD',cwd=DROOT).decode().strip();need(g('show','-s','--format=%P',D,cwd=DROOT).decode().strip()==D0,'normal body parent');report.update(body_sha=D,body_sha256=H(body));dump(O/'LIVE.json',report)
 need(remote(BR+'-prbody')==D0,'remote body unchanged');g('push','origin',D+':refs/heads/'+BR+'-prbody',cwd=DROOT);need(remote(BR+'-prbody')==D,'exact published D');report['pushed']['body']=True;clean(R,E,BR);clean(DROOT,D,BR+'-prbody');report['exit']=0
except BaseException:report.update(exit=1,error=traceback.format_exc())
finally:report['commands']=rec.rows;report['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(O/'RESULT.json',report);print(json.dumps({k:v for k,v in report.items()if k!='commands'},ensure_ascii=False))
raise SystemExit(report['exit'])
