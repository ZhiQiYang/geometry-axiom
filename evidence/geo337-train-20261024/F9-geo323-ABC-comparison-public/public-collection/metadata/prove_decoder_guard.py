from pathlib import Path
import hashlib,json,os,subprocess,sys,time

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'encoding-proof';OUT.mkdir()
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None)
rows=[]
for phase,wanted in [('before',0),('withdrawn',1),('restored',0)]:
 command=[sys.executable,'-B',str(ROOT/'test_encoded_profile.py')]
 if phase=='withdrawn':command.append('--withdraw-decoder')
 started=time.time();p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=30)
 row={'phase':phase,'command':command,'cwd':str(ROOT),'environment':{k:env.get(k) for k in ['PATH','LANG','LC_ALL','PYTHONDONTWRITEBYTECODE','PYTHONOPTIMIZE']},
      'started_epoch':started,'ended_epoch':time.time(),'exit_code':p.returncode,'expected_exit':wanted,
      'source_sha256':hashlib.sha256((ROOT/'scan_profile_scope.py').read_bytes()).hexdigest(),
      'test_sha256':hashlib.sha256((ROOT/'test_encoded_profile.py').read_bytes()).hexdigest(),
      'synthetic_only':True,'real_profile_read':False,'product_run':False}
 for stream in ['stdout','stderr']:
  b=getattr(p,stream);(OUT/(phase+'.'+stream)).write_bytes(b);row[stream+'_bytes']=len(b);row[stream+'_sha256']=hashlib.sha256(b).hexdigest()
 (OUT/(phase+'.json')).write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');rows.append(row)
 if p.returncode!=wanted:raise RuntimeError('Unexpected synthetic proof exit in '+phase)
(OUT/'RESULT.json').write_text(json.dumps({'exit_code':0,'actual_exits':[x['exit_code'] for x in rows],
 'method_count_each_phase':1,'synthetic_variant_count':6,'safe_identity_subset_not_classified_as_full_profile':True,
 'real_profile_read':False,'product_run':False},indent=2)+'\n')
print('Synthetic decoder guard 0/1/0; six encoded variants; no real profile read')
