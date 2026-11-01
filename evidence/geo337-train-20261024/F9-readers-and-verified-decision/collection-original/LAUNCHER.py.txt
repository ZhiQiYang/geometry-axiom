from pathlib import Path
import hashlib,importlib.util,json,os,platform,sys,time,traceback
OUT=Path('/workspace/geo337-F9-readers-and-identity-two-part-collection-20261025')
TOOL=Path('/workspace/collect_geo337_F9_readers_and_identity_v2_20261025.py')
TPIN='2427df3bcf99364eb148a0b356c091337436c567332a8bde06a7b915205aa368'
CAP=Path('/workspace/geo261-environment/final-f2-p73-controlled-tools/capture.py')
CPIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
F='4f8a794f4167c3562eb182045102e86e9e37cca9'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if OUT.exists():raise RuntimeError('fresh launch output required')
if h(TOOL)!=TPIN or h(CAP)!=CPIN:raise RuntimeError('exact collector/capture pin mismatch')
OUT.mkdir();(OUT/'COLLECTOR.py.txt').write_bytes(TOOL.read_bytes());(OUT/'ORIGINAL_CAPTURE.py.txt').write_bytes(CAP.read_bytes());(OUT/'LAUNCHER.py.txt').write_bytes(Path(__file__).read_bytes())
env=dict(os.environ);env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',LANG='C.UTF-8',LC_ALL='C.UTF-8')
spec=importlib.util.spec_from_file_location('original_c387',CAP);capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
rec=capture.Recorder(OUT,env,F);argv=[sys.executable,'-B',str(TOOL)]
result={'schema':'geo337-readers-api-two-part-collection-launch/1','source_sha':F,'command':argv,'cwd':'/workspace','collector_sha256':TPIN,'capture_sha256':CPIN,'python':sys.version,'platform':platform.platform(),'started_epoch':time.time(),'collection_only':True,'product_rerun':False,'actual_exit':None}
try:
 row,out,err=rec.run(argv,cwd='/workspace',timeout=180,check=False,source_sha=F,source_variant='existing immutable reader/API evidence only; no product samples')
 result['actual_exit']=row['actual_process_returncode'];result['original_result']=row;result['collector_unchanged']=h(TOOL)==TPIN
 if not result['collector_unchanged']:result['actual_exit']=1
except BaseException:
 result['actual_exit']=1;result['error']=traceback.format_exc();traceback.print_exc()
finally:
 result['ended_epoch']=time.time();(OUT/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False),flush=True)
sys.exit(result['actual_exit'])
