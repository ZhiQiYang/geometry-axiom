from pathlib import Path
import hashlib,importlib.util,json,os,sys
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025');OTHER=Path('/dev/shm/geo337-F9-browsers-20261025')
PREP=Path('/workspace/geo337-F9-q38-collection-preparation-20261025');TOOL=PREP/'collect_q38.py'
PEER=Path('/workspace/geo337-F9-q38-collector-static-peer-20261025/REVIEW.json')
SAMPLER=Path('/workspace/geo337-F9-browser-sampler-preparation-20261025/sample_original_browser_v2.py')
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert h(TOOL)=='65a25be44032bff390584123e86740c78e4ff0a5e7709b317b8f9e3fc785f820'
assert h(PEER)=='c969fa0574940e8628b4a76b6dd1401536a3e40ae8a28c490cf1c40225b54314'
assert h(SAMPLER)=='919eafb54f20454ee44a27754ce04f6f63f05f6e1c9b32a5b51652058735af30'
assert h(CAP)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
sp=importlib.util.spec_from_file_location('inventory',SAMPLER);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
inv=m.inventory([OWN,OTHER]);fs=os.statvfs(OWN);free=fs.f_bavail*fs.f_frsize;increment=85315157
assert inv['unique_allocated_bytes']+increment<=2147483648 and free>=increment
q=json.loads((PREP/'COLLECTION_REQUEST.unbound.json').read_bytes());q.update(execute=True,root_execution_lease=True,independent_peer={'path':str(PEER),'sha256':h(PEER)})
q['root_admission'].update(shared_allocated_before_bytes=inv['unique_allocated_bytes'],fresh_out_device_free_bytes=free,fresh_shared_plus_increment_within_ceiling=True,actual_collection_admitted=True)
OUT=OWN/'q38-collection-root-original-20261025';assert not OUT.exists();OUT.mkdir(mode=0o700)
request=OUT/'ROOT_REQUEST.json';request.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');(OUT/'EXECUTOR.py').write_bytes(Path(__file__).read_bytes())
sp=importlib.util.spec_from_file_location('capture',CAP);cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None);rec=cap.Recorder(OUT,env,q['source_sha'])
row,b,e=rec.run([sys.executable,'-B',str(TOOL),'--request',str(request),'--execute'],cwd='/workspace',timeout=None,check=False,source_variant='Collect original completed F9 Q38; no product rerun')
cap.dump(OUT/'RESULT.json',{'exit_code':row['actual_process_returncode'],'source_sha':q['source_sha'],'request_sha256':h(request),'collection_only':True,'original_command':row});sys.stdout.buffer.write(b);sys.stderr.buffer.write(e);raise SystemExit(row['actual_process_returncode'])
