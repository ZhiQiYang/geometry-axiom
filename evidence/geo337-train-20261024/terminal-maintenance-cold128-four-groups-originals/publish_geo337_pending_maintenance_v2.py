"""Root-only publication of two immutable maintenance packages, with an exact parent guard."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,re,shutil,sys

p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--expected-parent',required=True);a=p.parse_args()
R=Path('/workspace/geometry-axiom');B=Path('evidence/geo337-train-20261024')
T=B/'terminal-maintenance-cold128-four-groups-originals'
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db';BRANCH='codex/train-337-continue-20261024'
KINDS={'cold128','four-groups'}
ROOTS=[Path('/workspace/cold128-originals-20261024'),Path('/workspace/four-archive-groups-originals-20261024'),
       Path('/workspace/cold128-originals-collection-launch-20261024'),Path('/workspace/four-archive-groups-originals-collection-launch-20261024'),
       Path('/workspace/train337-canvas-peer-resume')]
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())

assert not sys.flags.optimize and 'PYTHONOPTIMIZE' not in os.environ
assert digest(a.manifest)==a.manifest_sha256
m=read(a.manifest);assert m['historical_maintenance_source_sha']==L and m['maintenance_only'] is True
assert re.fullmatch('[0-9a-f]{40}',a.expected_parent) and m['branch']==BRANCH
assert digest(__file__)==m['publisher_sha256']
files=m['files'];assert len({x['destination'] for x in files})==len(files)
archives={};raw_pins={}
for x in files:
 source,target=Path(x['source_path']),Path(x['destination'])
 assert source.resolve(strict=True)==source and any(source.is_relative_to(root) for root in ROOTS)
 assert not any(q.is_symlink() for q in [source,*source.parents]) and source.is_file()
 assert source.stat().st_size==x['bytes'] and digest(source)==x['sha256']
 assert x['kind'] in KINDS and not target.is_absolute() and '..' not in target.parts and target.is_relative_to(T/x['kind'])
 assert x['role'] in ['archive','metadata']
 if x['role']=='archive':
  assert x['kind'] not in archives and source.name.endswith('.tar.gz') and target.name==source.name
  archives[x['kind']]=x
 raw_pins[str(target)]=x['sha256']
assert set(archives)==set(m['packages'])==KINDS
for kind,x in archives.items():
 pack=read(Path(x['source_path']).parent/'PACKAGE.json');spec=m['packages'][kind]
 assert pack['exit_code']==0 and pack['roundtrip_original_bytes'] is True
 assert pack['archive']==x['source_path'] and pack['archive_sha256']==x['sha256']==spec['archive_sha256']
 assert pack['archive_bytes']==x['bytes']==spec['archive_bytes'] and pack['member_count']==spec['members']
 for key in ['static_peer','actual_peer']:
  item=spec[key];assert digest(item['path'])==item['sha256'];peer=read(item['path'])
  assert peer['exit_code']==0 and peer['findings']==[]
 assert read(spec['actual_peer']['path'])['archive_sha256']==x['sha256']
 outer=read(spec['outer_result']);assert outer['actual_process_returncode']==0 and outer['source_sha']==L and outer['ended_epoch']
O=Path('/workspace')/('geo337-pending-maintenance-publication-'+a.expected_parent[:8])
assert not O.exists()
capture=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert digest(capture)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec=importlib.util.spec_from_file_location('cap',capture);c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
O.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0');env.pop('PYTHONOPTIMIZE',None)
rec=c.Recorder(O,env,L)
def git(*args):
 row,out,err=rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=R,timeout=None,check=False,
                     source_variant='evidence-only historical maintenance publication; no product rerun')
 assert row['actual_process_returncode']==0,(args,err)
 return out.decode().strip()
free_before=shutil.disk_usage(R).free
minimum=2*sum(x['bytes'] for x in files if x['role']=='archive')+sum(x['bytes'] for x in files if x['role']=='metadata')+16*1024*1024
c.dump(O/'SPACE_PREFLIGHT.json',dict(free_before=free_before,required_free=minimum,archive_worktree_copies_created=False))
assert free_before>=minimum
assert git('rev-parse','HEAD')==a.expected_parent and git('branch','--show-current')==BRANCH
assert not git('status','--porcelain=v1','--untracked-files=all')
assert git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]==a.expected_parent
assert not (R/T).exists()
original=(R/B/'PROGRESS.md').read_bytes();before_progress_sha=hashlib.sha256(original).hexdigest()
assert m['progress_append_template'].count('{timestamp_utc}')==1
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
append=m['progress_append_template'].replace('{timestamp_utc}',stamp).encode()
progress=O/'PROGRESS.APPENDED.md';progress.write_bytes(original+append)
(O/'PROGRESS.BEFORE.md').write_bytes(original)
c.dump(O/'PROGRESS_APPEND_SCOPE.json',dict(expected_parent=a.expected_parent,before_sha256=before_progress_sha,after_sha256=digest(progress),before_bytes=len(original),append_bytes=len(append),append_only=True))
plain=[];allowed=set(raw_pins)
for x in files:
 source,target=Path(x['source_path']),Path(x['destination']);assert not (R/target).exists()
 (R/target).parent.mkdir(parents=True,exist_ok=True)
 if x['role']=='archive':
  blob=git('hash-object','-w','--',str(source));assert re.fullmatch('[0-9a-f]{40}',blob)
  git('update-index','--add','--cacheinfo','100644',blob,str(target));git('update-index','--skip-worktree',str(target))
  assert not (R/target).exists() and digest(source)==x['sha256']
 else:
  shutil.copyfile(source,R/target);assert digest(R/target)==x['sha256'];plain.append(str(target))
for source,target in [(a.manifest,T/'PUBLICATION_MANIFEST.json'),(Path(__file__),T/Path(__file__).name),(progress,B/'PROGRESS.md')]:
 if target==B/'PROGRESS.md':assert digest(R/target)==before_progress_sha
 shutil.copyfile(source,R/target);plain.append(str(target));allowed.add(str(target))
assert git('rev-parse','HEAD')==a.expected_parent
git('add','-f','--sparse','--',*plain)
assert set(git('diff','--cached','--name-only').splitlines())==allowed
row,out,err=rec.run(['git','diff','--cached','--check'],cwd=R,timeout=None,check=False,source_variant='verbatim-original-format-check')
if row['actual_process_returncode']:
 assert row['actual_process_returncode']==2 and not err;excluded=set()
 for line in out.decode().splitlines():
  match=re.match(r'(.+):\d+: (.+)',line)
  if not match:continue
  name,message=match.groups();assert name in raw_pins and message in ['trailing whitespace.','new blank line at EOF.']
  assert digest(R/name)==raw_pins[name];excluded.add(name)
 assert excluded
 c.dump(O/'VERBATIM_ORIGINAL_FORMAT_EXCLUSIONS.json',dict(original_exit=2,paths={n:raw_pins[n] for n in sorted(excluded)}))
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in sorted(excluded)])
assert git('rev-parse','HEAD')==a.expected_parent
git('commit','-m','docs: publish preserved maintenance receipts and alias reservations')
head=git('rev-parse','HEAD');git('push','origin','HEAD:'+BRANCH)
assert git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]==head
assert not git('status','--porcelain=v1','--untracked-files=all')
result=dict(historical_maintenance_source_sha=L,previous_evidence_head=a.expected_parent,evidence_head=head,published=True,push_exit=0,
            maintenance_only=True,product_gates_changed=False,product_tests_executed=0,prbody_changed=False,
            publication_manifest_sha256=a.manifest_sha256,archives_published=sorted(KINDS),
            separate_alias_reservations={'sealed_cold_groups':423,'cardref_elf_groups':2,'geo339_six_alias_group':1,'large_historical_archive_groups':3},
            free_before=free_before,free_after=shutil.disk_usage(R).free)
c.dump(O/'RESULT.json',result);print(json.dumps(result))
