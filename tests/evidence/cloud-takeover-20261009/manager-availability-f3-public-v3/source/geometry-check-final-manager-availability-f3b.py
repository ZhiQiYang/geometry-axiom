"""Read historical availability plus new directories; never construct Store."""
from pathlib import Path
import datetime, hashlib, json, os, shutil, sqlite3, subprocess, sys

ROOT=Path('<workspace-path>')
EXPECTED='f3b8285729b42cd22451c98cba1e2ec4514517f3'
OLD=Path('<workspace-path>')
OUT=Path('<workspace-path>')
OUT.mkdir(mode=0o700,exist_ok=False)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,data):
    p=OUT/name;p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');p.chmod(0o600);return {'path':str(p),'sha256':sha(p)}
commands=[]
def command(label,args,cwd=ROOT):
    start=now();r=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},check=False)
    logs=[]
    for stream,content in [('stdout',r.stdout),('stderr',r.stderr)]:
        p=OUT/(label+'.'+stream+'.log');p.write_bytes(content);p.chmod(0o600);logs.append({'stream':stream,'path':str(p),'bytes':len(content),'sha256':sha(p)})
    rec={'command':args,'cwd':str(cwd),'startedAt':start,'finishedAt':now(),'exitCode':r.returncode,'logs':logs};commands.append(rec);write(label+'.command.json',rec);return r
def identity(label):
    h=command(label+'-head',['git','rev-parse','HEAD']);d=command(label+'-dirty',['git','status','--short']);p=command(label+'-pwd',['pwd'])
    return {'head':h.stdout.decode().strip(),'dirty':d.stdout.decode().strip(),'pwd':p.stdout.decode().strip(),'at':now()}
before=identity('before');assert before['head']==EXPECTED and before['dirty']==''
old=json.loads((OLD/'availability-private.json').read_text());oldPublic=json.loads((OLD/'availability-public-summary.json').read_text());cut=datetime.datetime.fromisoformat(old['after']['checkedAt']).timestamp()
oldProof=[OLD/'availability-private.json',OLD/'availability-public-summary.json',OLD/'existing-database-path-search.stdout.log',OLD/'existing-work-manager-export-search.stdout.log',ROOT/'tests/evidence/cloud-takeover-20261009/work-manager/availability.json',ROOT/'tests/release-evidence/20261008-cloud-closeout/work-manager-summary.md',ROOT/'tests/release-evidence/20261008-cloud-closeout/work-manager-private-receipt-hashes.json']
oldHash={str(p):sha(p) for p in oldProof}
tool=ROOT/'geometry-web/work-manager';names=['AGENTS.md','README.md','cli.py','store.py','adapter.py'];toolHash={n:sha(tool/n) for n in names}
cli=(tool/'cli.py').read_text();store=(tool/'store.py').read_text();checks=[]
def check(name,ok,detail=None):checks.append({'name':name,'ok':ok is True,**({} if detail is None else {'detail':detail})})
check('tool sources match preserved availability hashes exactly',toolHash==oldPublic['toolSourceHashes'])
check('actual documented default and Store constructor still initialize missing ledger',"default=Path(__file__).resolve().parent / \".local\"" in cli and 'store = Store(args.data_dir)' in cli and 'self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)' in store and 'os.O_CREAT | os.O_EXCL | os.O_WRONLY' in store and 'CREATE TABLE IF NOT EXISTS sources' in store)
helpResult=command('existing-cli-help-only',[sys.executable,'-B',str(tool/'cli.py'),'--help'])
check('actual existing CLI help completed exit0 without Store construction',helpResult.returncode==0 and all(n.encode() in helpResult.stdout for n in ['reconcile','list-ready','list-alerts']))
knownDefaults={v['path'] for v in old['knownOriginalAndDefaultLocations'] if 'default' in v['source']}
currentCheckouts=[p for p in Path('/workspace').glob('geometry-*') if p.is_dir() and (p/'geometry-web/work-manager/cli.py').is_file()]
locations=[v['path'] for v in old['knownOriginalAndDefaultLocations'] if 'default' not in v['source']]+[str(p/'geometry-web/work-manager/.local') for p in currentCheckouts]
config=[]
for value in sorted(set(locations)):
    p=Path(value)
    try:
        s=p.stat();config.append({'path':value,'exists':True,'readable':os.access(p,os.R_OK),'directory':p.is_dir(),'defaultDataDir':value.endswith('/work-manager/.local')})
    except OSError as e:config.append({'path':value,'exists':False,'error':{'type':type(e).__name__,'errno':e.errno}})
newRoots=[]
for parent in [Path('/workspace'),Path('<workspace-path>'),Path('/tmp'),Path('/home/agent')]:
    for p in parent.iterdir():
        if not p.is_dir() or p==OUT or p==Path('<workspace-path>'):continue
        if p.stat().st_ctime>=cut:newRoots.append(p)
for p in currentCheckouts:
    if str(p/'geometry-web/work-manager/.local') not in knownDefaults and p not in newRoots:newRoots.append(p)
newRoots=sorted(set(newRoots));write('incremental-root-inventory.json',{'oldFullScanEndedAt':old['after']['checkedAt'],'directorySelection':'Top-level current checkouts, scratch, TEMP and home directories created or directory entries changed since the prior full scan. Existing default/private locations are always checked separately.','roots':[{'path':str(p),'ctimeUtc':datetime.datetime.fromtimestamp(p.stat().st_ctime,datetime.timezone.utc).isoformat()} for p in newRoots]})
oldDb={r['path']:r for r in old['existingDatabases']};oldExports={r['path']:r for r in old['existingExportCandidates']}
oldRelevant=[r for r in old['existingDatabases'] if r.get('isWorkManagerLedger')]+list(oldExports.values());oldRelevantBefore={r['path']:sha(r['path']) for r in oldRelevant if Path(r['path']).is_file()}
args=['rg','--files','--hidden','--no-ignore','-g','*.db','-g','*.sqlite*',*[str(p) for p in newRoots]]
dbResult=command('incremental-database-file-paths',args)
check('new-directory database filename search has no read errors',dbResult.returncode in [0,1] and dbResult.stderr==b'')
newDb=[]
for value in dbResult.stdout.decode().splitlines():
    p=Path(value)
    if value in oldDb or not p.is_file():continue
    rec={'path':value,'bytes':p.stat().st_size,'isWorkManagerLedger':False}
    try:
        # Explicit read-only immutable SQLite handle: no Store, create or WAL writes.
        with p.open('rb') as stream:header=stream.read(16)
        if header!=b'SQLite format 3\x00':rec['notSQLite']=True
        else:
            connection=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
            try:
                tables={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")};rec['isWorkManagerLedger']={'sources','snapshots','events'}<=tables
                if rec['isWorkManagerLedger']:
                    rec['sha256Before']=sha(p);rec['sourceIds']=[r[0] for r in connection.execute('SELECT id FROM sources ORDER BY id')];rec['eventCount']=connection.execute('SELECT COUNT(*) FROM events').fetchone()[0];rec['taskIds']=[r[0] for r in connection.execute('SELECT DISTINCT task_id FROM events ORDER BY task_id')];rec['syntheticOnly']=all(s.startswith('synthetic') for s in rec['sourceIds']) and all(t in ['DONE','FUTURE','GROUP','NO-SCOPE','READY'] or t.startswith('DEMO-') for t in rec['taskIds']);rec['sha256After']=sha(p);rec['bytesUnchanged']=rec['sha256Before']==rec['sha256After']
            finally:connection.close()
    except (OSError,sqlite3.Error,ValueError) as e:rec['readError']={'type':type(e).__name__,'message':str(e)}
    newDb.append(rec)
exportArgs=['rg','--hidden','--no-ignore','-l','-g','*.json','-g','!node_modules/**','"format"\\s*:\\s*"geometry-work-manager-export"',*[str(p) for p in newRoots]]
exportResult=command('incremental-export-paths',exportArgs)
check('new-directory exact export search has no read errors',exportResult.returncode in [0,1] and exportResult.stderr==b'')
newExports=[]
for value in exportResult.stdout.decode().splitlines():
    p=Path(value)
    if value in oldExports or not p.is_file():continue
    rec={'path':value,'sha256':sha(p)}
    try:
        d=json.loads(p.read_text());rec['isExactExport']=type(d) is dict and d.get('format')=='geometry-work-manager-export'
        if rec['isExactExport']:
            rec['checksum']=d.get('checksum');rec['snapshotCount']=len(d.get('snapshots',[]));rec['sourceIds']=[s.get('source',{}).get('id') for s in d.get('snapshots',[])];rec['taskIds']=sorted({e.get('task_id') for s in d.get('snapshots',[]) for e in s.get('events',[])});rec['syntheticOnly']=all(isinstance(s,str) and s.startswith('synthetic') for s in rec['sourceIds'])
    except (OSError,ValueError,TypeError) as e:rec['readError']={'type':type(e).__name__,'message':str(e)}
    newExports.append(rec)
oldPreserved=all(Path(p).is_file() and sha(p)==h for p,h in oldRelevantBefore.items())
check('all previously found14synthetic1empty ledgers and8export bytes preserved',len(oldRelevantBefore)==23 and oldPreserved)
check('original fullscan historical receipts and current committed availability preserved',all(sha(p)==h for p,h in oldHash.items()))
after=identity('after');check('current fullHEAD clean before after exactf3b',before['head']==after['head']==EXPECTED and before['dirty']==after['dirty']=='')
realDb=[r for r in newDb if r.get('isWorkManagerLedger') and not r.get('syntheticOnly')];realExport=[r for r in newExports if r.get('isExactExport') and not r.get('syntheticOnly')]
summary={'schema':'geometry-work-manager-incremental-availability-public/1','checkedAt':now(),'candidateFullSHA':EXPECTED,'dirtyBefore':before['dirty'],'dirtyAfter':after['dirty'],'toolAvailable':helpResult.returncode==0,'toolSourceHashes':toolHash,'currentRealQueueStatus':'unknown','originalRealLedgerOrValidCompleteExportAccessible':False,'historicalAsOf':old['after']['checkedAt'],'historicalQaCandidates':oldPublic['historicalQaCandidates'],'qaCandidatesNotUsedAsRecovery':True,'historicalPublicV5':oldPublic['historicalPublicV5'],'incrementalScope':{'newOrDirectoryEntryChangedRoots':len(newRoots),'newDatabaseFiles':len(newDb),'newWorkManagerLedgerCandidates':len(realDb),'newExactNonSyntheticExportCandidates':len(realExport),'existingDefaultOrKnownOriginalLocationsPresent':sum(x['exists'] for x in config)},'reconcile':'not executed: existing real ledger unavailable','listReady':'not executed: existing real ledger unavailable','listAlerts':'not executed: existing real ledger unavailable','oldDataPreserved':oldPreserved,'newEmptyDatabaseCreated':False,'storeConstructed':False,'importsAssignmentsApprovalsReviewsGitOrProductWrites':False,'nextStep':'Make the preserved original real ledger or complete validated portable export available in this execution environment; verify provenance and checksum, then use the existing CLI against that explicit existing private store. Completed writer handoffs and product verification proceed independently.','limits':['Incremental availability check reuses the prior fullscan; it does not assert a second exhaustive sweep of all old directories.','Historical v5 59read_only/0write/374alerts are preserved historical facts, not current ready counts.','No current owner, review, approval, task completion or queue restoration inferred from synthetic or missing private data.']}
check('no original/default location or new non-synthetic candidate became available',not any(x['exists'] for x in config) and not realDb and not realExport)
public=write('availability.public.json',summary)
private={'schema':'geometry-work-manager-incremental-availability-private/1','before':before,'after':after,'executor':{'agent':'/root','python':sys.executable,'resolved':str(Path(sys.executable).resolve()),'sha256':sha(sys.executable),'version':sys.version,'script':str(Path(__file__).resolve()),'scriptSHA256':sha(__file__),'command':[sys.executable,*sys.argv]},'toolCommands':[{'name':n,'executed':False,'reason':'real ledger unavailable and constructor would initialize missing database'} for n in ['reconcile','list-ready','list-alerts']],'currentConfigPaths':config,'incrementalRoots':[str(p) for p in newRoots],'newDatabaseCandidates':newDb,'newExportCandidates':newExports,'oldRelevantFilesPreserved':[{'path':p,'sha256Before':h,'sha256After':sha(p),'unchanged':sha(p)==h} for p,h in oldRelevantBefore.items()],'oldEvidence':[{'path':p,'sha256':h,'unchanged':sha(p)==h} for p,h in oldHash.items()],'commands':commands,'checks':checks,'ok':all(r['ok'] for r in checks),'publicSummary':public,'repoWritten':False,'storeConstructed':False,'browserExecuted':False,'databaseWrites':False}
receipt=write('receipt.private.json',private)
print(json.dumps({'receipt':receipt,'public':public,'checks':len(checks),'ok':private['ok'],'newDatabaseFiles':len(newDb),'newRealLedgerCandidates':len(realDb),'newExportCandidates':len(newExports),'failedChecks':[r for r in checks if not r['ok']]},ensure_ascii=False))
sys.exit(0 if private['ok'] else 1)
