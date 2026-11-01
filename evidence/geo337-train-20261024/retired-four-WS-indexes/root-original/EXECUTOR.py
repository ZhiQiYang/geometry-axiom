from pathlib import Path
import hashlib,importlib.util,json,os,sys
ROOT=Path('/dev/shm/geometry-axiom-geo337-20261025');OTHER=Path('/dev/shm/geo337-F9-browsers-20261025')
PREP=Path('/workspace/geo337-four-retired-WS-index-preservation-20261025');TOOL=PREP/'archive_indexes.py'
REQ=Path('/workspace/geo337-four-WS-index-ROOT_REQUEST-20261025.json')
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
SAMPLER=Path('/workspace/geo337-F9-browser-sampler-preparation-20261025/sample_original_browser_v2.py')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert h(TOOL)=='b7e3f6c5c1f5ad18c1ea9db697c035d01a439991819ad160ae502374c15663ab'
assert h(CAP)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
assert h(SAMPLER)=='919eafb54f20454ee44a27754ce04f6f63f05f6e1c9b32a5b51652058735af30'
req=json.loads(REQ.read_bytes());assert all(req[k]is True for k in ['root_four_sources_no_reuse_lease','root_no_active_consumers_lease','root_shared_shm_capacity_admitted'])
sp=importlib.util.spec_from_file_location('inventory',SAMPLER);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
inv=m.inventory([ROOT,OTHER]);increment=23400448+32*1024*1024;assert inv['unique_allocated_bytes']+increment<=2147483648
OUT=ROOT/'four-WS-index-archive-root-original-20261025';assert not OUT.exists();OUT.mkdir(mode=0o700)
sp=importlib.util.spec_from_file_location('capture',CAP);cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap)
cap.dump(OUT/'ADMISSION.json',{'shared_allocated_before':inv['unique_allocated_bytes'],'incremental_plan_bytes':increment,'planning_ceiling_bytes':2147483648,'only_archive':True,'unlink_performed':False})
(OUT/'ROOT_REQUEST.json').write_bytes(REQ.read_bytes());(OUT/'EXECUTOR.py').write_bytes(Path(__file__).read_bytes())
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None);rec=cap.Recorder(OUT,env,'82c922a3941525d3a094ac0158bdc7dea57ea360')
row,b,e=rec.run([sys.executable,'-B',str(TOOL),'--request',str(REQ),'--request-sha256',h(REQ),'--execute-archive'],cwd='/workspace',timeout=None,check=False,source_variant='lossless archive of four inactive own index caches; no unlink')
cap.dump(OUT/'RESULT.json',{'exit_code':row['actual_process_returncode'],'archive_only':True,'index_removed':False,'request_sha256':h(REQ),'original_command':row})
sys.stdout.buffer.write(b);sys.stderr.buffer.write(e);raise SystemExit(row['actual_process_returncode'])
