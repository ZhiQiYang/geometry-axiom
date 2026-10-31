#!/usr/bin/env python3
"""Actual exit-code controls on copies of freshly captured native streams."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
from exact_p189 import POLICY
ROOT=Path('/tmp/pr338-b3-p189');OUT=ROOT/'controls'
OUT.mkdir(exist_ok=False)
mutations=['wrong_text','wrong_position','fourth_difference','other_dump_byte','returncode','stderr_wrong_text','stderr_wrong_position','scene_input_changed','fourth_unlisted_scene']
rows=[]
for scene in POLICY:
    for label in ['baseline',*mutations,'restored']:
        mutation='none' if label in ('baseline','restored') else label
        folder=OUT/f'{len(rows)+1:03d}';folder.mkdir()
        cmd=['python3','-B',str(ROOT/'tools/replay_exact.py'),'--receipts',str(ROOT/'formal-v2'),'--scene',scene,'--mutation',mutation]
        started=time.time();p=subprocess.run(cmd,capture_output=True,timeout=60)
        (folder/'stdout.bin').write_bytes(p.stdout);(folder/'stderr.bin').write_bytes(p.stderr)
        expected=0 if mutation=='none' else 1
        row={'scene':scene,'control':label,'command':cmd,'cwd':os.getcwd(),'source_sha':'0ae1728c2309e1d670369289a6b8da059fa63a50',
             'started_epoch_utc':started,'seconds':time.time()-started,'actual_process_returncode':p.returncode,'expected_exit':expected,
             'timeout_seconds':60,'timeout_expired':False,
             'environment':{k:os.environ.get(k) for k in ('PATH','LANG','LC_ALL','PYTHONDONTWRITEBYTECODE')},
             'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()}
        (folder/'result.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');rows.append(row)
        print(scene,label,p.returncode,flush=True)
        assert p.returncode==expected,(scene,label,p.stderr)
(OUT/'RESULT.json').write_text(json.dumps({'exit':0,'baseline_count':3,'killed_count':27,'restored_count':3,'rows':rows},ensure_ascii=False,indent=2)+'\n')
