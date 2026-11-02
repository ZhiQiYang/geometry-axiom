from pathlib import Path
import hashlib,json,datetime
out=Path(__file__).parent
def need(v,m):
 if not v:raise RuntimeError(m)
rows={};metadata=[]
for job in ['documents','grid','space','timber']:
 rows[job]={}
 for phase,key in [('', 'final_sha256'),('-plan','plan_final_sha256'),('-materialize','materialize_final_sha256')]:
  p=Path('/workspace')/('geo337-F9-'+job+'-SHM'+phase+'-EXEC_FINAL-20261025.json');b=p.read_bytes();j=json.loads(b);pin=hashlib.sha256(b).hexdigest()
  if phase:
   if 'actual_tool_result' in j:
    need(set(j)=={'session_id','actual_tool_result'}and type(j['session_id'])is int,'yielded preparation host envelope');t=j['actual_tool_result']
   else:t=j
   s=json.loads(t['output']);need(type(t['exit_code'])is int and t['exit_code']==0,'preparation true host exit0')
   need(s['job']==job and s['phase']==phase[1:] and s['original_exit']==0 and s['result']==f'/dev/shm/geo337-F9-browsers-20261025/host/{job}{phase}/RESULT.json','original preparation identity');observed=t['exit_code']
  else:
   t=j['actual_tool_result'];s=json.loads(t['output'])
   need(j['source_sha']==s['source_sha']=='4f8a794f4167c3562eb182045102e86e9e37cca9'and s['job']==job,'formal source/job identity')
   need(t['exit_code']==s['wrapper_exit']==s['original_process_returncode'],'formal actual exit agreement');observed=t['exit_code']
  rows[job][key]=pin;metadata.append({'job':job,'phase':phase or 'formal','path':str(p),'sha256':pin,'bytes':len(b),'actual_exit':observed})
p=out/'TERMINAL_PINS.json';need(not p.exists(),'fresh terminal binding');p.write_text(json.dumps(rows,indent=2)+'\n')
r={'state':'BOUND_METADATA_ONLY','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':'4f8a794f4167c3562eb182045102e86e9e37cca9','terminal_pins_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'originals':metadata,'collector_executed':False,'source_or_SHM_access':False,'formal_exits':[r['actual_exit']for r in metadata if r['phase']=='formal']}
(out/'BINDING.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'terminal_pins_path':str(p),'sha256':r['terminal_pins_sha256'],'formal_exits':r['formal_exits'],'originals':len(metadata)}))
