import datetime,fcntl,hashlib,json,os,pathlib,shutil,subprocess,time,traceback

sha='7c8e9cee4ed5b3706ee919e2831a1dac0aa55ea5'
repo=pathlib.Path('/dev/shm/pr348-probe-source-7a0e6dd8')
out=pathlib.Path('/dev/shm/pr348-census-L7c8e9cee-20261029')
durable=pathlib.Path('/tmp/pr348-census-L7c8e9cee-text-20261029')
tool=pathlib.Path('/dev/shm/pr348-native-plan/native_recorder.py')
lockpath=pathlib.Path('/workspace/geo337-comparison-exclusive.lock')
cache=pathlib.Path('/tmp/geometry-tests')
durable.mkdir(exist_ok=False)
def digest(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
report={'source_sha':sha,'started_utc':utc(),'phase':'preflight','errors':[],'mirror':'incremental raw stdout/stderr bytes, fsync; original SHM files retained','product_test_claim':False}
def save():
 target=durable/'LAUNCHER.json';temp=durable/'LAUNCHER.json.writing'
 temp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');temp.replace(target)
def state():
 rows=[]
 for args in [['git','rev-parse','HEAD'],['git','status','--porcelain=v1','--untracked-files=all']]:
  p=subprocess.run(args,cwd=repo,capture_output=True,timeout=30);rows.append({'argv':args,'exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()});p.check_returncode()
 assert rows[0]['stdout'].strip()==sha and rows[1]['stdout']==''
 return rows
def consumers():
 rows=[];roots=[str(repo),str(cache)];observers={os.getpid(),os.getppid()}
 for p in pathlib.Path('/proc').iterdir():
  if not p.name.isdecimal() or int(p.name) in observers:continue
  try:
   f=(p/'stat').read_text().rsplit(')',1)[1].split()
   if f[0]=='Z':continue
   cwd=os.readlink(p/'cwd');cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
   links=[]
   for fd in (p/'fd').iterdir():
    try:t=os.readlink(fd)
    except OSError:continue
    if any(t.startswith(x) for x in roots):links.append(t)
   if links or any(cwd.startswith(x) or x in cmd for x in roots):rows.append({'pid':int(p.name),'cwd':cwd,'command':cmd[:1000],'open_files':links})
  except (FileNotFoundError,ProcessLookupError,PermissionError):pass
 return rows
process=None
try:
 assert digest(tool)=='e1c1fd63bc58f8b7af1b6be28913b86e287101fc1cd3a8908f251bb33bb39445'
 assert not out.exists()
 report['source']=state();report['consumers']=consumers();assert not report['consumers']
 report['space']={str(p):shutil.disk_usage(p)._asdict() for p in [durable,pathlib.Path('/dev/shm'),pathlib.Path('/workspace')]}
 report['budget']={'tmp_original_admission':134217728,'tmp_publication_reserve':67108864,'tmp_text_budget':8388608,'tmp_build_growth_budget':20971520,'shm_temp_archive_budget':1073741824,'not_a_product_limit':True}
 assert report['space'][str(durable)]['free'] >= 134217728+67108864+8388608+20971520
 assert report['space']['/dev/shm']['free'] >= 1073741824+67108864
 old=json.loads(pathlib.Path('/dev/shm/pr348-native-cache-preservation-20261029/MANIFEST.json').read_text());report['cache']=[]
 for row in old:
  p=cache/row['relative'];s=p.stat();m=row['after_metadata']
  actual={'device':s.st_dev,'inode':s.st_ino,'mode':s.st_mode&0o7777,'size':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
  h=digest(p);assert all(v==m[k] for k,v in actual.items()) and h==row['after_sha256']
  report['cache'].append({'path':str(p),'sha256':h,'identity_unchanged':True})
 report['locks']=[]
 for p in [lockpath,cache/'build.lock',cache/'run_all.lock']:
  with p.open('rb') as f:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);report['locks'].append({'path':str(p),'available':True});fcntl.flock(f,fcntl.LOCK_UN)
 command=['python3','-B',str(tool),'--repo',str(repo),'--sha',sha,'--out',str(out),'--heavy-lock',str(lockpath),'--mode','census']
 report['command']=command;report['recorder_sha256']=digest(tool);report['phase']='launching';save()
 for p in [pathlib.Path(__file__),tool]:shutil.copy2(p,durable/p.name)
 with (durable/'launcher.stdout.bin').open('xb',buffering=0) as sout,(durable/'launcher.stderr.bin').open('xb',buffering=0) as serr:
  process=subprocess.Popen(command,cwd=repo,stdin=subprocess.DEVNULL,stdout=sout,stderr=serr,start_new_session=True)
  report.update(recorder_pid=process.pid,phase='running',launched_utc=utc());save()
  offsets={'stdout.bin':0,'stderr.bin':0};streams={name:(durable/name).open('xb',buffering=0) for name in offsets}
  try:
   def mirror():
    for name in offsets:
     source=out/name
     if source.exists():
      with source.open('rb') as src:
       src.seek(offsets[name])
       while chunk:=src.read(65536):streams[name].write(chunk);offsets[name]+=len(chunk)
      os.fsync(streams[name].fileno())
   while process.poll() is None:
    mirror();time.sleep(1)
   mirror()
  finally:
   for f in streams.values():f.close()
  report.update(recorder_exit=process.returncode,phase='finished',ended_utc=utc(),mirror_bytes=offsets)
 for name in ['stdout.bin','stderr.bin']:
  assert (out/name).read_bytes()==(durable/name).read_bytes()
 for name in ['PROCESS.json','RESULT.json','process-events.jsonl','expected-before.json','expected-after.json','binary-before.json','actual-binaries-sidecars-logs-manifest.json','prior-run-all-logs-manifest.json']:
  p=out/name
  if p.exists():shutil.copy2(p,durable/name)
 report['raw_mirror_exact']=True
 report['space_after']={str(p):shutil.disk_usage(p)._asdict() for p in [durable,pathlib.Path('/dev/shm')]}
except BaseException:
 report['errors'].append(traceback.format_exc());report['phase']='launcher-error';report['ended_utc']=utc()
 if process is not None:report['recorder_still_running']=process.poll() is None
finally:save()
print(json.dumps({'phase':report['phase'],'recorder_exit':report.get('recorder_exit'),'errors':report['errors'],'result':str(durable/'LAUNCHER.json')},ensure_ascii=False))
