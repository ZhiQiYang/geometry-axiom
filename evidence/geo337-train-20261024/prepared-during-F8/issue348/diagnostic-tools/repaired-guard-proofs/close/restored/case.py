import copy,json,os,subprocess,sys
from pathlib import Path
import sidecar,launch_diagnostic as launcher,selftest_protocol as original
control=sys.argv[1];detail={};passed=False
if control=='fixture':
 try:launcher.validate_fixture(b'synthetic smaller64 replacement\n')
 except ValueError:passed=True
elif control in ('flush_entry','flags'):
 e=copy.deepcopy(original.sequence())
 if control=='flush_entry':e[1]['rc']=-1
 else:e[-1]['feof']=-1
 row=sidecar.inspect_events(*original.packet(e),original.PAYLOAD,completed=True);passed=not row['valid'];detail=row
elif control=='close':
 expired=subprocess.TimeoutExpired(['synthetic-never-launched'],600,output=b'partial',stderr=b'original')
 def fake(*args,**kwargs):
  raw,status=original.packet(original.sequence()[:4]);os.write(int(kwargs['env']['GEO348_DIAG_EVENT_FD']),raw);os.pwrite(int(kwargs['env']['GEO348_DIAG_STATUS_FD']),status,0);raise expired
 realclose=launcher.os.close
 def badclose(fd):realclose(fd);raise OSError('synthetic-close-failure')
 launcher.os.close=badclose;caught=None
 try:launcher.capture(['synthetic-never-launched'],original.PAYLOAD,Path('execution'),env={},source_sha='synthetic',bindings={},runner=fake,synthetic=True)
 except BaseException as e:caught=e
 finally:launcher.os.close=realclose
 passed=caught is expired;detail={'caught_type':type(caught).__name__,'original_timeout_identity_preserved':passed}
row={'control':control,'passed':passed,'exit':0 if passed else 1,'detail':detail,'synthetic':True,'product_executed':False,'wrapper_compiled':False}
Path('TEST_RESULT.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'control':control,'exit':row['exit'],'passed':passed}));raise SystemExit(row['exit'])
