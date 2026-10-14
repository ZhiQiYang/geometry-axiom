import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time
repo=pathlib.Path('/tmp/geometry-p095-201');root=pathlib.Path('/tmp/geometry-wake25-201/native');root.mkdir(exist_ok=True)
tz=datetime.timezone(datetime.timedelta(hours=8))
def git(*args):return subprocess.check_output(['git',*args],cwd=repo).decode().strip()
head=git('rev-parse','HEAD');base_main=git('rev-parse','caf49852a4b40d4e61bdf76480c79b43bb5a3676')
assert not git('status','--porcelain')
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=repo).decode().rstrip('\0').split('\0')
def sources():return {p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in tracked}
before=sources();(root/'sources-before.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n')
start=datetime.datetime.now(tz).isoformat();clock=time.monotonic();argv=['bash','-c','set -e; ulimit -s 16384; exec python3 -u tests/run_all.py --build']
env={**os.environ,'MUTATE_CACHE':'/tmp/geometry-wake25-201/native-mutant-cache'}
with (root/'native.stdout').open('wb') as out,(root/'native.stderr').open('wb') as err:
 child=subprocess.Popen(argv,cwd=repo,stdout=out,stderr=err,env=env)
 (root/'native-start.json').write_text(json.dumps({'head':head,'base_main':base_main,'argv':argv,'pid':child.pid,'started_at':start,'MUTATE_CACHE':env['MUTATE_CACHE']},indent=2)+'\n')
 code=child.wait()
 ended=datetime.datetime.now(tz).isoformat();duration=time.monotonic()-clock
 (root/'native-actual-exit.json').write_text(json.dumps({'pid':child.pid,'exit':code,'ended_at':ended,'seconds':duration},indent=2)+'\n')
after=sources();(root/'sources-after.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
shutil.copytree('/tmp/geometry-tests/run_all-logs',root/'run_all-logs')
binary_dir=root/'binaries';binary_dir.mkdir(exist_ok=True)
for name in ['core','bridge','integrity','model-base','engineering-json-test']:
 p=pathlib.Path('/tmp/geometry-tests')/name
 if p.is_file():
  shutil.copy2(p,binary_dir/p.name)
  for sidecar in p.parent.glob(p.name+'.*.json'):shutil.copy2(sidecar,binary_dir/sidecar.name)
receipt={'head':head,'base_main':base_main,'argv':argv,'MUTATE_CACHE':env['MUTATE_CACHE'],'mutation_scope':'historical main execution receipt/source freshness only, no new core mutant runs; isolated cache contains no foreign PF2 executables','pid':child.pid,'started_at':start,'ended_at':ended,'seconds':duration,'exit':code,'sources_unchanged':before==after,'git_status':git('status','--porcelain')}
(root/'native-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False),flush=True);sys.exit(code)
