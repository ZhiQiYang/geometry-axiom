from pathlib import Path
import hashlib, importlib.util, json, os, sys

SHA='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
BASE=Path('/tmp/geo337-F8-full123-terminal-preparation-v2-20261025')
OUT=Path('/tmp/geo337-F8-full123-terminal-collection-authorized-launch-20261025')
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
PREP='45058091b308950ee18af616f6add2e4fe6535dc130cd5dc390f57f175d3369f'
def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert h(CAP)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
assert h(BASE/'PREPARATION.json')==PREP
assert not OUT.exists()
OUT.mkdir()
request=json.loads((BASE/'REQUEST.unbound.json').read_text())
request['binding_status']='BOUND_AFTER_REAL_TERMINAL'
bindings=request['terminal_bindings']
bindings['original_tool_final']['path']='/tmp/geo337-full123-F8-EXEC_FINAL-20261025.json'
pins={'job_receipt':'4c953c9b9a2cec30afde2d8ac06a4a2b9edb5b9a1ab1083234506bde79052595','outer_result':'7b14875e0c4fe496e099fa4d3c4782fdf9f3b4a39c2f2c0357265689891a6934','original_tool_final':'7a6454bb04ecb7cbe3d8646b90655c54d79ff9220d0f43799e052be543cd4461'}
for key,binding in bindings.items():
    binding['sha256']=h(binding['path'])
    assert binding['sha256']==pins[key]
request_path=OUT/'BOUND_REQUEST.json'
request_path.write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',LANG='C.UTF-8',LC_ALL='C.UTF-8',PYTHONIOENCODING='utf-8')
env.pop('PYTHONOPTIMIZE',None)
rec=cap.Recorder(OUT,env,SHA)
common=['--request',str(request_path),'--request-sha256',h(request_path),'--preparation-sha256',PREP,'--root-terminal-lease']
commands=[('verify_terminal.py','/tmp/geo337-F8-full123-terminal-verified-20261025',[]),('collect_terminal.py','/tmp/geo337-F8-full123-terminal-package-20261025',['--reserve-bytes',str(64*1024*1024)])]
cap.dump(OUT/'REQUEST.json',{'source_sha':SHA,'request_sha256':h(request_path),'preparation_sha256':PREP,'reserve_bytes':64*1024*1024,'root_reason':'64 MiB reserve after conservative full-uncompressed collection admission on TMP; original payloads preserved; no rerun or adoption','commands':commands})
status=0
for tool,target,extra in commands:
    row,stdout,stderr=rec.run([sys.executable,'-B',str(BASE/tool),*common,'--out',target,*extra],cwd='/workspace',timeout=None,check=False,source_variant='original-F8-terminal-collection-no-formal-rerun')
    status=row['actual_process_returncode']
    print(tool,status,stdout.decode(errors='replace'),stderr.decode(errors='replace'),flush=True)
    if status:break
cap.dump(OUT/'RESULT.json',{'source_sha':SHA,'collection_driver_exit':status,'commands':rec.rows,'adoption_performed':False})
sys.exit(status)
