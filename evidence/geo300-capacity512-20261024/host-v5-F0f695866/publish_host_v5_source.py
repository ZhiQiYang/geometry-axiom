"""Publish only the peer-reviewed three test leaves; no test/build or ledger."""
from pathlib import Path
import hashlib,json,os,shutil,sys,traceback
HERE=Path(__file__).resolve().parent
ROOT=Path('/workspace/geo300-capacity512-work-20261024')
DRAFT=HERE/'host-v5-draft'
OUT=HERE/'host-v5-source-publication'
START='391f44da1c3e37e50c7a25a8a855b93c2865062c'
BRANCH='codex/geo300-capacity512-20261024'
EXPECTED_PATCH='d4a745e6f2d101bcd65166617eacc75a3d095d8dc4bee9aa320532438ab25ca1'
PEER=Path('/workspace/geo300-capacity512-host-v5-peer-20261024/REVIEW.json')
MIN_FREE=25*1024*1024
def sha(data):return hashlib.sha256(data).hexdigest()
if OUT.exists():raise SystemExit('Refusing to reuse publication output')
if shutil.disk_usage(ROOT).free<MIN_FREE:raise SystemExit('Environment blocked: original 25 MiB publication guard')
assert sha((DRAFT/'HOST_V2.patch').read_bytes())==EXPECTED_PATCH
assert sha(PEER.read_bytes())=='7554687f38d886489bc8176049f3560d4dfbb9c3f823248620d234220af135c9'
manifest=json.loads((DRAFT/'MANIFEST.json').read_text())
paths=sorted(manifest['files'])
assert paths==['tests/geo300_scene_generator.py','tests/run_all.expected.json','tests/test_geo261_timber_capacity_host.py']
for name in paths:
    assert (ROOT/name).read_bytes()==(DRAFT/'candidate'/name).read_bytes(),name
    assert sha((ROOT/name).read_bytes())==manifest['files'][name]['after_sha256'],name
sys.path.insert(0,'/workspace/geo261-environment/final-f-contact-checker-proof-tools')
from capture import Recorder,dump
OUT.mkdir()
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
rec=Recorder(OUT,env,START)
report={'kind':'source-publication-only','formal_acceptance':False,'product_before':'400a6d0ca50f3aca104fb569c77c8ef753c93355','head_before':START,'branch':BRANCH,'minimum_workspace_free_bytes':MIN_FREE,'peer_sha256':sha(PEER.read_bytes()),'patch_sha256':EXPECTED_PATCH,'files':manifest['files'],'committed':False,'pushed':False,'remote_verified':False,'C_executed':False,'generator_executed':False}
def git(*args,check=True):return rec.run(['git',*args],cwd=ROOT,check=check)[1]
try:
    rec.run(['df','-B1','/workspace','/tmp'],cwd=ROOT)
    assert shutil.disk_usage(ROOT).free>=MIN_FREE
    assert git('rev-parse','HEAD').decode().strip()==START
    assert git('symbolic-ref','--short','HEAD').decode().strip()==BRANCH
    git('status','--porcelain=v1','--untracked-files=all')
    assert git('diff','--cached','--name-only')==b''
    changed=set(git('diff','--name-only').decode().splitlines())
    assert changed=={'tests/run_all.expected.json','tests/test_geo261_timber_capacity_host.py'},changed
    remote=git('ls-remote','--refs','origin','refs/heads/'+BRANCH).decode().split()
    assert remote==[START,'refs/heads/'+BRANCH],remote
    # The new test helper is outside this owned sparse pattern. Stage only the
    # explicit allowlist; do not broaden the checkout or scan other evidence.
    git('add','--sparse','-f','--',*paths)
    assert git('diff','--cached','--name-only').decode().splitlines()==paths
    git('diff','--cached','--check')
    for name in paths:assert sha(git('show',':'+name))==manifest['files'][name]['after_sha256']
    git('commit','-m','Fix capacity acceptance for unplaced and placed timber worlds')
    final=git('rev-parse','HEAD').decode().strip();report.update(source_sha=final,committed=True)
    assert git('show','-s','--format=%P','HEAD').decode().strip()==START
    assert git('diff-tree','--no-commit-id','--name-only','-r',final).decode().splitlines()==paths
    assert git('status','--porcelain=v1','--untracked-files=all')==b''
    dump(OUT/'RESULT.json',report)
    git('push','origin','refs/heads/'+BRANCH+':refs/heads/'+BRANCH)
    report['pushed']=True
    assert git('ls-remote','--refs','origin','refs/heads/'+BRANCH).decode().split()==[final,'refs/heads/'+BRANCH]
    report['remote_verified']=True
    assert git('status','--porcelain=v1','--untracked-files=all')==b''
    report['success']=True
except BaseException:
    report['success']=False;report['error']=traceback.format_exc();raise
finally:
    report['commands']=len(rec.rows);dump(OUT/'RESULT.json',report)
print(json.dumps({key:report[key] for key in ('source_sha','committed','pushed','remote_verified','C_executed','generator_executed')},ensure_ascii=False))
