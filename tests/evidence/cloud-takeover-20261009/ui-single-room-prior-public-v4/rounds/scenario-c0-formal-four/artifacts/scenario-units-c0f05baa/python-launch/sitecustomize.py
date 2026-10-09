import sys,pathlib,resource,subprocess,json,os,hashlib,datetime
sys.path.insert(0,'<workspace-path>')
import binaries
binaries.OUT_DIR=pathlib.Path('<isolated-test-directory>')
soft,hard=resource.getrlimit(resource.RLIMIT_STACK)
resource.setrlimit(resource.RLIMIT_STACK,(max(soft,16777216) if soft!=-1 else soft,hard))
_log=pathlib.Path('<unit-evidence-root>/scenario-units-c0f05baa/python-backend-spawns.jsonl')
_original_popen=subprocess.Popen
class _RecordedPopen(_original_popen):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        record={'pid':self.pid,'parentPythonPid':os.getpid(),'requestedArgv':self.args,'cwd':str(kwargs.get('cwd') or pathlib.Path.cwd()),'observedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pythonExecutable':sys.executable,'pythonExecutableSha256':hashlib.sha256(pathlib.Path(sys.executable).resolve().read_bytes()).hexdigest()}
        try:
            executable=pathlib.Path('/proc')/str(self.pid)/'exe'
            record['runningExecutable']=str(executable.resolve(strict=True))
            record['runningExecutableSha256']=hashlib.sha256(executable.read_bytes()).hexdigest()
            record['procStat']=(pathlib.Path('/proc')/str(self.pid)/'stat').read_text()
        except Exception as error:
            record['processIdentityError']=type(error).__name__+': '+str(error)
        try:
            descriptor=os.open(_log,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
            try:os.write(descriptor,(json.dumps(record,ensure_ascii=False)+'\n').encode())
            finally:os.close(descriptor)
        except Exception:
            pass
subprocess.Popen=_RecordedPopen
