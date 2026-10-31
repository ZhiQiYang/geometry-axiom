from pathlib import Path
import datetime, hashlib, importlib.util, json, os, re, shutil

R=Path('/workspace/geometry-axiom')
P=Path('/workspace/geo337-all-terminal-status-preparation-20261024')
O=Path('/workspace/geo337-all-terminal-status-publication')
B=Path('evidence/geo337-train-20261024')
T=B/'final-L-all-terminal-status-only'
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
BEFORE='537b4d9c647648f8cdc8d45db3fc0bf5b9386911'
BRANCH='codex/train-337-continue-20261024'
PINS={'MANIFEST.json':'84b3a7b671809230c24868e9ef6f7a379a07dcc59fd1e821c74d4d1245427b06',
      'PROGRESS.draft.md':'befb3abb78b8bbda7586c0dc5e02f1b0edefe2e0d0371283d4fc10e7fc8b065c',
      'QUESTIONS.draft.md':'a23e704b4dc943e2a24d8cd783540f9ab95d02197a3ef412350d3b3908db779f',
      'PR_BODY.compact-final.md':'e5295462a07739f3a478065aae9fb7a0d7211b6d38ba736296531f60f3afa97f'}
def sha(data): return hashlib.sha256(data).hexdigest()
for name,pin in PINS.items(): assert sha((P/name).read_bytes())==pin,name
m=json.loads((P/'MANIFEST.json').read_text())
assert m['source_sha']==L and m['expected_evidence_head']==BEFORE
assert m['original_bytes']==2936868 and len(m['files'])==28 and m['complete_raw_archives_published'] is False
assert m['all_L_specials_terminal'] is True
raw_pins={}
for row in m['files']:
    n=row['name'];assert not Path(n).is_absolute() and '..' not in Path(n).parts and not n.endswith('.tar.gz')
    p=P/'frozen-originals'/n;assert p.is_file() and not p.is_symlink()
    data=p.read_bytes();assert len(data)==row['bytes'] and len(data)<3000000 and sha(data)==row['sha256']
    raw_pins[str(T/n)]=row['sha256']
cp=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert sha(cp.read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec=importlib.util.spec_from_file_location('cap',cp);c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
O.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0');env.pop('PYTHONOPTIMIZE',None)
rec=c.Recorder(O,env,L)
def git(*args):
    row,out,err=rec.run(['git',*args],cwd=R,timeout=None,check=False,source_variant='all-final-L-terminal-status-only')
    assert row['actual_process_returncode']==0,(args,err)
    return out.decode().strip()
assert git('rev-parse','HEAD')==BEFORE and git('branch','--show-current')==BRANCH
assert not git('status','--porcelain=v1','--untracked-files=all')
for name in ('PROGRESS','QUESTIONS'):assert (R/B/(name+'.md')).read_bytes()==(P/(name+'.original.md')).read_bytes()
target=R/T;target.mkdir()
for row in m['files']:
    p=target/row['name'];p.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(P/'frozen-originals'/row['name'],p);assert sha(p.read_bytes())==row['sha256']
shutil.copyfile(P/'MANIFEST.json',target/'STATUS_MANIFEST.json')
shutil.copyfile('/workspace/prepare_geo337_all_terminal_status.py',target/'prepare_geo337_all_terminal_status.py')
shutil.copyfile(__file__,target/Path(__file__).name)
for name in ('PROGRESS','QUESTIONS'):
    text=(P/(name+'.draft.md')).read_text()
    if name=='PROGRESS':
        now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        text=re.sub(r'## 唯一 current-state（[^\n]+）','## 唯一 current-state（'+now+'）',text,count=1)
    (R/B/(name+'.md')).write_text(text)
git('add','-f','--sparse',str(T),str(B/'PROGRESS.md'),str(B/'QUESTIONS.md'))
assert all(n.startswith(str(T)+'/') or n in {str(B/'PROGRESS.md'),str(B/'QUESTIONS.md')} for n in git('diff','--cached','--name-only').splitlines())
row,out,err=rec.run(['git','diff','--cached','--check'],cwd=R,timeout=None,check=False,source_variant='verbatim-original-terminal-format-check')
if row['actual_process_returncode']:
    assert row['actual_process_returncode']==2 and not err
    excluded=set()
    for line in out.decode().splitlines():
        match=re.match(r'(.+):\d+: (.+)',line)
        if not match:continue
        name,message=match.groups();assert name in raw_pins and message in ('trailing whitespace.','new blank line at EOF.'),line
        assert sha((R/name).read_bytes())==raw_pins[name];excluded.add(name)
    assert excluded
    c.dump(O/'VERBATIM_ORIGINAL_FORMAT_EXCLUSIONS.json',{'original_exit':2,'paths':{n:raw_pins[n] for n in sorted(excluded)}})
    git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in sorted(excluded)])
git('commit','-m','docs: record all final acceptance outcomes and remaining blockers')
E=git('rev-parse','HEAD');git('push','origin','HEAD:'+BRANCH)
assert git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]==E
result={'source_sha':L,'previous_evidence_head':BEFORE,'evidence_head':E,'published':True,'push_exit':0,
        'stage_exits':m['stage_exits'],'memo_phase_exits':m['memo_phase_exits'],
        'original_outer_exits':m['original_outer_exits'],'remaining_red':m['remaining_red'],
        'complete_raw_archives_published':False,'prbody_candidate':str(P/'PR_BODY.compact-final.md'),'prbody_unchanged':True}
c.dump(O/'RESULT.json',result);print(json.dumps(result))
