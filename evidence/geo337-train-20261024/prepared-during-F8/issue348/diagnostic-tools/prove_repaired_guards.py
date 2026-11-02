"""Additional per-fix withdrawal proofs. Python fake runner only."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'repaired-guard-proofs'
if OUT.exists():raise SystemExit('Fresh output required')
OUT.mkdir()
sources={n:(ROOT/n).read_bytes() for n in ['sidecar.py','launch_diagnostic.py','selftest_protocol.py']}
cases={
 'fixture':('launch_diagnostic.py',b"if len(raw) != ORIGINAL_FIXTURE_BYTES or sha(raw) != ORIGINAL_FIXTURE_SHA256:",b'if False:'),
 'close':('launch_diagnostic.py',b"                try:\n                    os.close(fd)\n                except OSError as close_error:\n                    close_errors.append(repr(close_error))",b'                os.close(fd)'),
 'flush_entry':('sidecar.py',b"event['length'] == 0 and event['rc'] == 0, 'flush-entry-fields'",b"event['length'] == 0, 'flush-entry-fields'"),
 'flags':('sidecar.py',b"must(event['feof'] >= 0 and event['ferror'] >= 0 and event['length'] >= 0, 'negative-libc-flag-or-length')",b"pass  # deliberately omit original nonnegative field guard")}
test=r'''import copy,json,os,subprocess,sys
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
'''
records=[];env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None);env['PYTHONDONTWRITEBYTECODE']='1'
for control,(file,before,after) in cases.items():
 if sources[file].count(before)!=1:raise SystemExit('Anchor drift '+control)
 for phase in ['fixed','withdrawn','restored']:
  p=OUT/control/phase;p.mkdir(parents=True)
  for name,body in sources.items():
   if phase=='withdrawn' and name==file:body=body.replace(before,after)
   (p/name).write_bytes(body)
  (p/'case.py').write_text(test)
  argv=[sys.executable,'-B',str(p/'case.py'),control];r=subprocess.run(argv,cwd=p,env=env,capture_output=True)
  (p/'stdout.bin').write_bytes(r.stdout);(p/'stderr.bin').write_bytes(r.stderr)
  row={'control':control,'phase':phase,'argv':argv,'cwd':str(p),'exit':r.returncode,
       'source_sha256':{name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in sources},
       'case_sha256':hashlib.sha256((p/'case.py').read_bytes()).hexdigest(),
       'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest(),
       'synthetic':True,'product_executed':False,'wrapper_compiled':False}
  (p/'COMMAND_RESULT.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');records.append(row)
groups={name:[row['exit'] for row in records if row['control']==name] for name in cases}
exit_code=int(any(v!=[0,1,0] for v in groups.values()))
result={'schema':'geo348-repaired-tool-guards-proof/1','exit':exit_code,'groups':groups,'commands':records,'scope':'Each repaired guard withdrawn independently; only Python synthetic counterexamples, no product or C.'}
(OUT/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'exit':exit_code,'groups':groups}));raise SystemExit(exit_code)
