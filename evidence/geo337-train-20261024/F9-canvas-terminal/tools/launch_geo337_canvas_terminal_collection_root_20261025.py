import hashlib, importlib.util, json, os
from pathlib import Path

src = Path('/workspace/geo337-F9-canvas-terminal-output-device-delta-20261025/COLLECTION_REQUEST.unbound.json')
q = json.loads(src.read_bytes())
q['execute'] = True
q['root_execution_lease'] = True
q['independent_peer'] = {'path':'/workspace/geo337-F9-canvas-terminal-collector-v2-static-peer-20261025/REVIEW.json','sha256':'6c0c3656cdb4c526e729b159260f0afb4111a22f9613bfd3ddcfc874b3f84a02'}
req = Path('/workspace/geo337-F9-canvas-terminal-collection-root-request-20261025.json')
with req.open('x') as f: f.write(json.dumps(q, ensure_ascii=False, indent=2)+'\n')
tool = Path('/workspace/collect_geo337_F9_canvas_terminal_parts_v2_20261025.py')
assert hashlib.sha256(tool.read_bytes()).hexdigest() == q['collector_sha256']
cap = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert hashlib.sha256(cap.read_bytes()).hexdigest() == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
s = importlib.util.spec_from_file_location('capture',cap);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
out=Path('/workspace/geo337-F9-canvas-terminal-root-collection-20261025');out.mkdir()
r=m.Recorder(out, dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),q['source_sha'])
row,_,_=r.run(['python3','-B',str(tool),'--request',str(req),'--execute'],cwd='/workspace',timeout=None,check=False)
m.dump(out/'RESULT.json',{'original_exit':row['actual_process_returncode'],'capture_result':row,'package_result':q['out']+'/RESULT.json','subject_rerun':False})
print(json.dumps({'original_exit':row['actual_process_returncode'],'package_result':q['out']+'/RESULT.json'}))
raise SystemExit(row['actual_process_returncode'])
