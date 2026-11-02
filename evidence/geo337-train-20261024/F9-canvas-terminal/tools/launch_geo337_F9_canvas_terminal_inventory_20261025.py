from pathlib import Path
import hashlib,importlib.util,json,os,sys,time,traceback
O=Path('/workspace/geo337-F9-canvas-terminal-inventory-launch-20261025');T=Path('/workspace/prepare_geo337_F9_canvas_terminal_inventory_20261025.py');TP='0529e37827cf8dfa3e7e5b02b9ac27e96937e2d2c3fff71af9f09d725c7bad20';CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');CP='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762';F='4f8a794f4167c3562eb182045102e86e9e37cca9'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if O.exists() or h(T)!=TP or h(CAP)!=CP:raise RuntimeError('fresh output and exact tools required')
O.mkdir();(O/'INVENTORY_TOOL.py.txt').write_bytes(T.read_bytes());(O/'ORIGINAL_CAPTURE.py.txt').write_bytes(CAP.read_bytes());(O/'LAUNCHER.py.txt').write_bytes(Path(__file__).read_bytes())
sp=importlib.util.spec_from_file_location('cap',CAP);cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap);env=dict(os.environ);env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',LANG='C.UTF-8',LC_ALL='C.UTF-8');rec=cap.Recorder(O,env,F)
r={'schema':'geo337-canvas-terminal-inventory-launch/1','source_sha':F,'inventory_only':True,'archive_execution_authorized':False,'product_rerun':False,'tool_sha256':TP,'capture_sha256':CP,'actual_exit':None,'started_epoch':time.time()}
try:
 row,out,err=rec.run([sys.executable,'-B',str(T)],cwd='/workspace',timeout=120,check=False,source_sha=F,source_variant='terminal evidence inventory only; no archive or product execution');r['original_result']=row;r['actual_exit']=row['actual_process_returncode'];r['tool_unchanged']=h(T)==TP
 if not r['tool_unchanged']:r['actual_exit']=1
except BaseException:r['actual_exit']=1;r['error']=traceback.format_exc();traceback.print_exc()
finally:r['ended_epoch']=time.time();(O/'RESULT.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False),flush=True)
sys.exit(r['actual_exit'])
