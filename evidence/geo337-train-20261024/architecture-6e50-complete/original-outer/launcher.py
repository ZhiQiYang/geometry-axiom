from pathlib import Path
import hashlib,importlib.util,json,os,resource,sys,time,traceback
S='6e50aef65513b7b38f93228919272c6d40d6c196';ROOT=Path('/workspace/geometry-axiom');OUT=Path('/tmp/geo337-h-architecture-four-20261025');OUTER=Path('/tmp/geo337-h-architecture-four-launch-20261025')
TOOL=Path('/tmp/geo337-architecture-h-local-init-tool-20261024/refresh_architecture_h_local_init.py');CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert hashlib.sha256(TOOL.read_bytes()).hexdigest()=='94574f72984c26d72a88eac3536c6c2b316b67a63529c50835a9d6d988a194dc'
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
 command=[sys.executable,'-B',str(TOOL),'--root',str(ROOT),'--sha',S,'--out',str(OUT),'--prior-source','e321026fb9bc9bc19c54b8034af6e6eaec2857f9'];result['command']=command
 row,stdout,stderr=rec.run(command,cwd=ROOT,check=False,source_sha=S,source_variant='original three architecture judges and nine fresh historical-policy guard proofs at clean M')
 result.update(exit=row['actual_process_returncode'],original_command=row,tool_sha256=hashlib.sha256(TOOL.read_bytes()).hexdigest())
except BaseException:result.update(exit=1,error=traceback.format_exc())
finally:
 result['ended_epoch']=time.time();cap.dump(OUTER/'RESULT.json',result);print(json.dumps({'source':S,'exit':result['exit'],'result':str(OUTER/'RESULT.json')}),flush=True)
sys.exit(result['exit'])
