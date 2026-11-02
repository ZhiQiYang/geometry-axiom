import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path

REPO=Path('/tmp/geo300-prerequisites-20261024')
OUT=Path('/tmp/geo300-authority-20261024')
OUT.mkdir(exist_ok=True)
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
spec=importlib.util.spec_from_file_location('geo300_c387',CAP)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
env={k:v for k,v in os.environ.items() if not k.startswith(('GIT_','GEOMETRY_','MUTATE_'))}
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
rec=mod.Recorder(OUT,env,'unfixed-read-only-authority')
def run(args,timeout=300):return rec.run(args,cwd=REPO,timeout=timeout)[1]
run(['git','remote','set-url','origin','https://github.com/ZhiQiYang/geometry-axiom.git'])
run(['git','fetch','--no-tags','origin',
     'refs/heads/codex/train-337-continue-20261024:refs/remotes/origin/codex/train-337-continue-20261024',
     'refs/heads/handoff/codex-takeover-20261021:refs/remotes/origin/handoff/codex-takeover-20261021',
     'refs/heads/main:refs/remotes/origin/main'])
train=run(['git','rev-parse','refs/remotes/origin/codex/train-337-continue-20261024']).decode().strip()
main=run(['git','rev-parse','refs/remotes/origin/main']).decode().strip()
handoff=run(['git','rev-parse','refs/remotes/origin/handoff/codex-takeover-20261021']).decode().strip()
rec.sha=train
run(['git','sparse-checkout','set','--no-cone','/AGENTS.md','/evidence/geo300-prerequisites-20261024/'])
run(['git','-c','core.autocrlf=false','checkout','-b','codex/geo300-prerequisites-20261024',train])
files=[]
for ref,path,label in [(train,'AGENTS.md','AGENTS.md'),(train,'geometry-guide/PRODUCT-VISION.md','PRODUCT-VISION.md'),
                       (main,'決策佇列.md','MAIN-決策佇列.md'),(train,'決策佇列.md','TRAIN-決策佇列.md'),
                       (train,'公理層.md','公理層.md'),(train,'geometry-templates/woodworking/FIELD-RULES.md','FIELD-RULES.md'),
                       (handoff,'handoff/drafts/issue300/DESIGN.md','OLD-DESIGN.md'),
                       (handoff,'handoff/drafts/issue300/TESTS.md','OLD-TESTS.md'),
                       (handoff,'handoff/drafts/issue300/bench/README.md','OLD-BENCH-README.md')]:
    body=run(['git','show',ref+':'+path]);dest=OUT/label;dest.write_bytes(body)
    files.append({'ref':ref,'path':path,'snapshot':str(dest),'bytes':len(body),'raw_sha256':hashlib.sha256(body).hexdigest(),'LF_sha256':hashlib.sha256(body.replace(b'\r\n',b'\n')).hexdigest()})
review_path='handoff/pr-reviews/300.md'
row,body,err=rec.run(['git','show',handoff+':'+review_path],cwd=REPO,timeout=300,check=False)
if row['actual_process_returncode']==0:
    (OUT/'PR300-review.md').write_bytes(body)
result={'schema':'geo300-fresh-authority-read/1','read_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'repo':str(REPO),'branch':'codex/geo300-prerequisites-20261024','published_train_source':train,'main_source':main,'fresh_handoff':handoff,
        'files':files,'PR300_review_exit':row['actual_process_returncode'],'source_or_test_changed':False,'heavy_job_started':False,
        'original_commands':rec.rows,'initial_clone':'git clone --shared --no-checkout /workspace/geometry-axiom /tmp/geo300-prerequisites-20261024 exited0; shared read-only objects, no assets/source tree materialized.'}
(OUT/'AUTHORITY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['repo','branch','published_train_source','main_source','fresh_handoff','PR300_review_exit']},ensure_ascii=False))
