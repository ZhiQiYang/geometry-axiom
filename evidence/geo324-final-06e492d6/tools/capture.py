"""完整原始子命令錄製；此模組不執行任何驗收。"""
import hashlib,json,os,signal,subprocess,time
from pathlib import Path
def digest(data):return hashlib.sha256(data).hexdigest()
def filehash(path):return digest(Path(path).read_bytes())
def dump(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
class Recorder:
 def __init__(self,out,env,sha):self.out=Path(out);self.env=env;self.sha=sha;self.rows=[]
 def run(self,args,*,cwd,data=None,timeout=1200,check=True,source_sha=None,source_variant=None):
  target=self.out/'subcommands'/f'{len(self.rows)+1:06d}';target.mkdir(parents=True)
  payload=data if data is not None else b'';(target/'stdin.bin').write_bytes(payload)
  row={'command':list(map(str,args)),'cwd':str(Path(cwd).resolve()),'acceptance_sha':self.sha,
   'source_sha':source_sha or self.sha,'source_variant':source_variant,
   'environment':{k:self.env.get(k) for k in ('PATH','LANG','LC_ALL','PYTHONIOENCODING','PYTHONDONTWRITEBYTECODE','PYTHONOPTIMIZE','TMPDIR',
    'CC','CFLAGS','CPPFLAGS','LDFLAGS','C_INCLUDE_PATH','CPATH','LIBRARY_PATH','LD_LIBRARY_PATH','GCC_EXEC_PREFIX','COMPILER_PATH')},
   'started_epoch':time.time(),'stdin_provided':data is not None,'stdin_sha256':digest(payload),
   'actual_process_returncode':None,'timeout_expired':False,'directory':str(target)}
  self.rows.append(row);dump(target/'request.json',row);process=None;out=err=b'';failure=None
  try:
   process=subprocess.Popen(args,cwd=cwd,env=self.env,stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
      stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
   out,err=process.communicate(data,timeout=timeout)
  except BaseException as error:
   failure=error;row['exception']=repr(error);row['timeout_expired']=isinstance(error,subprocess.TimeoutExpired)
   if isinstance(error,subprocess.TimeoutExpired):
    for name,value in [('timeout-partial.stdout.bin',error.stdout),('timeout-partial.stderr.bin',error.stderr)]:
     (target/name).write_bytes(value if value is not None else b'')
   if process is not None:
    if process.poll() is None:
     try:os.killpg(process.pid,signal.SIGKILL)
     except ProcessLookupError:pass
    out,err=process.communicate()
  finally:
   (target/'stdout.bin').write_bytes(out);(target/'stderr.bin').write_bytes(err)
   row.update(actual_process_returncode=process.returncode if process is not None else None,ended_epoch=time.time(),
     stdout_sha256=digest(out),stderr_sha256=digest(err),stdout_bytes=len(out),stderr_bytes=len(err))
   dump(target/'result.json',row);dump(self.out/'subcommands.json',self.rows)
  if failure:raise failure
  if check and row['actual_process_returncode']!=0:raise RuntimeError('子命令非零；完整原輸出已保存：'+str(target))
  return row,out,err
