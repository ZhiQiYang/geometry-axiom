from pathlib import Path
import hashlib,importlib.util,json,os,resource,sys,time,traceback
S='e321026fb9bc9bc19c54b8034af6e6eaec2857f9';ROOT=Path('/workspace/geometry-axiom');OUT=Path('/tmp/geo337-e321-architecture-four-20261024');OUTER=Path('/tmp/geo337-e321-architecture-four-launch-20261024')
TOOL=Path('/workspace/geo337-architecture-k-source-delta-tool-20261024/refresh_architecture_k_source_delta.py');CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert hashlib.sha256(TOOL.read_bytes()).hexdigest()=='5b76f54d810a736e1008450eb2822f8c0d5a427cbd3e7d3138a578909203a7fb'
assert hashlib.sha256(CAP.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
assert not OUT.exists() and not OUTER.exists();OUTER.mkdir()
(OUTER/'launcher.py').write_bytes(Path(__file__).read_bytes())
sp=importlib.util.spec_from_file_location('original_c387',CAP);cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap)
env=dict(os.environ)
for key in ('PYTHONOPTIMIZE','PYTHONPATH','PYTHONSTARTUP','NODE_OPTIONS'):env.pop(key,None)
env.update(PYTHONDONTWRITEBYTECODE='1',LANG='C.UTF-8',LC_ALL='C.UTF-8',PYTHONIOENCODING='utf-8')
soft,hard=resource.getrlimit(resource.RLIMIT_STACK);resource.setrlimit(resource.RLIMIT_STACK,(16777216,hard));rec=cap.Recorder(OUTER,env,S);result={'source_sha':S,'exit':None,'started_epoch':time.time(),'command':None}
try:
 rec.run(['df','-B1','/workspace','/tmp'],cwd=ROOT,check=True,source_sha=S,source_variant='architecture source and output storage admission snapshot')
 command=[sys.executable,'-B',str(TOOL),'--root',str(ROOT),'--sha',S,'--out',str(OUT),'--prior-source','8d2a69421560b83c0b69f3e82db8f5e97ccc037b'];result['command']=command
 row,stdout,stderr=rec.run(command,cwd=ROOT,check=False,source_sha=S,source_variant='original three architecture judges and nine fresh historical-policy guard proofs at clean M')
 result.update(exit=row['actual_process_returncode'],original_command=row,tool_sha256=hashlib.sha256(TOOL.read_bytes()).hexdigest())
except BaseException:result.update(exit=1,error=traceback.format_exc())
finally:
 result['ended_epoch']=time.time();cap.dump(OUTER/'RESULT.json',result);print(json.dumps({'source':S,'exit':result['exit'],'result':str(OUTER/'RESULT.json')}),flush=True)
sys.exit(result['exit'])
