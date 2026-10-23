import json,hashlib,tarfile,os,sys,datetime,subprocess
from pathlib import Path
import yaml
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db';B=Path('/workspace/train337-browser-terminal-collection/documents');J=Path('/workspace/train337-browser-L-documents/original/documents');A=Path('/workspace/train337-browser-L-documents-launch');O=Path('/tmp/train337-adversarial')
checks=0;findings=[]
def ck(ok,label):
 global checks
 checks+=1
 if not ok:findings.append(label)
def sha(b):return hashlib.sha256(b).hexdigest()
def h(p):return sha(Path(p).read_bytes())
def read(p):return json.loads(Path(p).read_text())
s=read(B/'SUMMARY.json');p=read(B/'PACKAGE.json');inv=read(B/'RAW_INVENTORY.json');r=read(J/'receipt.json');a=read(A/'receipt.json');cmds=read(A/'subcommands.json')
ck(h(B/'ORIGINAL_BROWSER_JOB_AND_TEMP_OUTPUTS.tar.gz')==p['archiveSHA256']=='a6f641498d86dcdaafce9fe07e45a9e0873c9ee63940eaffcee09f0e743bae85','archive pin')
ck(h(B/'RAW_INVENTORY.json')==p['rawInventorySHA256']=='8b92b417d29bcc2999fe49782565853d34153335788c753a173bae21f6725621','inventory pin')
ck(len(inv)==669 and p['memberCount']==670 and p['originalLogicalBytes']==sum(v['bytes'] for v in inv.values()),'inventory exact count/bytes')
with tarfile.open(B/'ORIGINAL_BROWSER_JOB_AND_TEMP_OUTPUTS.tar.gz','r:gz') as t:
 ms=t.getmembers();ck(len(ms)==670 and {m.name for m in ms}==set(inv)|{'RAW_INVENTORY.json'},'archive exact member set')
 ck(t.extractfile('RAW_INVENTORY.json').read()==(B/'RAW_INVENTORY.json').read_bytes(),'embedded inventory exact')
 for m in ms:
  if m.name=='RAW_INVENTORY.json':continue
  x=inv[m.name];path=Path(x['originalPath']);ck(not m.name.startswith('/') and '..' not in Path(m.name).parts,'safe name '+m.name)
  if x['type']=='symlink':
   ck(m.issym() and m.linkname==x['target']==os.readlink(path),'symlink exact '+m.name);data=m.linkname.encode();ck(len(data)==x['bytes'] and sha(data)==x['sha256'],'symlink hash '+m.name)
  else:
   ck(m.isfile(),'regular type '+m.name);data=t.extractfile(m).read();ck(len(data)==m.size==x['bytes'] and sha(data)==x['sha256'],'tar bytes '+m.name);ck(data==path.read_bytes(),'original bytes '+m.name)
source=J # raw receipts below only; never demand current shared GUARD_LATEST stay old
ck(s['sourceSHA']==p['sourceSHA']==r['sha']==a['source_sha']==L,'same L SHA')
ck(r['checkout_before']==r['checkout_after']==s['sourceBefore']==s['sourceAfter'] and r['checkout_before']['head']==L and r['checkout_before']['status']=='','original source clean binding')
ck(r['exit_code']==s['originalExit']==p['originalExit']==a['original_primary_exit']==0 and r['status']=='完成' and bool(r['ended']),'original job terminal0')
ck(a['wrapper_exit']==s['wrapperExit']==p['wrapperExit']==0 and a['passed'] and not a['errors'],'outer accepted0')
ck(r['ci_timeout_minutes']==10 and r['seconds']==s['elapsedSeconds'] and r['seconds']<600 and not r['over_ci_timeout'],'original CI10 unrelaxed')
ck(len(cmds)==3 and cmds==[a['before_guard'],a['original_command'],a['after_guard']],'exact three original launcher commands')
for c in cmds:
 d=Path(c['directory']);ck(c['source_sha']==L and c['acceptance_sha']==L and c['actual_process_returncode']==0 and not c['timeout_expired'] and c['ended_epoch']>c['started_epoch'],'launcher execution '+str(d))
 for name in ('stdout','stderr'):
  raw=(d/(name+'.bin')).read_bytes();ck(len(raw)==c[name+'_bytes'] and sha(raw)==c[name+'_sha256'],'launcher raw '+str(d/name))
ck(a['original_command']['command'][-6:]==['--sha',L,'--job','documents','--out-root','/workspace/train337-browser-L-documents/original'],'exact driver binding argv')
reapers=[json.loads(x) for x in (A/'reaper.jsonl').read_text().splitlines()];ck(reapers[-1]['event']=='完成' and reapers[-1]['primary_returncode']==0 and any(x.get('primary') and x.get('returncode')==0 for x in reapers),'reaper actual primary0')
for pin,digest in a['driver_pins'].items():
 matching=[v for v in inv.values() if v['sha256']==digest];ck(bool(matching),'frozen runtime tool '+pin)
ck(r['driver_sha256']=='2a42523fee66c7947313f567716b81f25c1cf50b965698ff5913216695cd1c98'==h(J/'driver.py.txt'),'accepted storage driver exact')
wf=subprocess.run(['git','-C','/workspace/geometry-axiom','show',L+':.github/workflows/integration-tests.yml'],capture_output=True)
ck(wf.returncode==0 and wf.stdout==(J/'workflow.yml.txt').read_bytes() and sha(wf.stdout)==r['workflow_sha256'],'workflow original fixed Git L')
y=yaml.safe_load(wf.stdout);browser=y['jobs']['browser'];ck(browser['strategy']['matrix']['include'][next(n for n,x in enumerate(browser['strategy']['matrix']['include']) if x['suite']=='documents')]['timeout']==10,'workflow documents10')
ck([x['original_step'] for x in r['steps']]==browser['steps'],'every original workflow step retained')
for step in r['steps']:
 if 'result' in step:
  rr=step['result'];ck(rr['actual_process_returncode']==rr['exit_code']==0 and not rr['watchdog_expired'],'actual workflow step '+str(step['index']))
  ck((J/'steps'/('%02d.executed.sh'%step['index'])).read_text()==(step['executed_run'] if step['executed_run'].endswith('\n') else step['executed_run']+'\n') and h(J/'steps'/('%02d.executed.sh'%step['index']))==step['script_sha256'],'executed script exact '+str(step['index']))
  for stream in ('stdout','stderr'):ck(str(Path(rr[stream])) in {v['originalPath'] for v in inv.values()},'step full stream included')
for rel,x in r['files'].items():
 q=J/rel;ck(q.stat().st_size==x['bytes'] and h(q)==x['sha256'],'original driver file '+rel)
stdout=(J/'steps/03.stdout').read_text();lines=[x for x in stdout.splitlines() if x.startswith('DOCUMENTS_RESULT ')];ck(len(lines)==1,'one original documents marker');result=json.loads(lines[0].split(' ',1)[1]);ck(result['passedAssertions']==47 and result['failedAssertions']==0 and sum(x.startswith('PASS ') for x in stdout.splitlines())==47,'47 real assertions no failure')
ck((J/'steps/03.stderr').read_bytes()==b'','browser original stderr empty')
pngs=[x for x in r['files'] if x.startswith('artifacts/07/') and x.endswith('.png')];ck(len(pngs)==8,'8 screenshot originals')
env=r['environment'];ck(env['GITHUB_SHA']==L and env['GEOMETRY_TEST_URL']=='http://127.0.0.1:19083/' and 'GEOMETRY_CDP_UPDATE_GOLDEN' not in env and 'PYTHONOPTIMIZE' not in env,'actual isolated job environment')
ck(s['versions'][0]['exit']==0 and '156.0.8078.47' in s['versions'][0]['stdout'] and s['versions'][1]['exit']==0 and 'v24.19.0' in s['versions'][1]['stdout'],'Chrome156 Node24 original commands')
ck(s['versions'][-1]['exit']==0 and 'install ok installed' in s['versions'][-1]['stdout'],'CJK installed proof')
for g in s['originalPoolGuardLogs']:
 phase=g['phase'];gr=Path(g['directory']);rows=read(gr/'COMMANDS.json');c=a[phase];ck(len(rows)==14,'guard14 '+phase)
 ck(c['started_epoch']<=gr.stat().st_mtime<=c['ended_epoch'],'closed original guard epoch '+phase)
 for num,row in enumerate(rows,1):
  rr=(gr/f'{num:03d}.stdout.bin').read_bytes();ee=(gr/f'{num:03d}.stderr.bin').read_bytes();ck(row['actual_exit']==0 and sha(rr)==row['stdout_sha256'] and sha(ee)==row['stderr_sha256'],'guard raw '+phase+str(num));ck(rr==(L+'\n').encode() if num%2 else rr==b'','guard HEAD/clean '+phase+str(num))
 ck(not any('GUARD_LATEST' in k for k in inv),'no later mutable guard relabeled')
inputs={x['path']:x for x in read(inv['pool-preparation/layout/POOL_INPUTS.json']['originalPath'])}
original_c=subprocess.run(['git','-C','/workspace/geometry-axiom','show',L+':current_geometry.c'],capture_output=True)
ck(original_c.returncode==0 and sha(original_c.stdout)==inputs['current_geometry.c']['sha256'],'currentC exact Git raw matches immutable pool')
lf_c=sha(original_c.stdout.replace(b'\r\n',b'\n'))
for x in s['excluded']:
 if 'ELF' in x['reason']:
  q=Path(x['path']);fp=read(q.with_name(q.name+'.fingerprint.json'));ck(fp['exe_sha256']==x['sha256'] and fp['exe_size']==x['bytes'],'excluded ELF exact preserved hash '+q.name)
  for name,digest in fp['files'].items():ck(name in inputs and (lf_c if name=='current_geometry.c' else inputs[name]['sha256'])==digest,'runtime build fixed source '+name)
ck(sum('ELF' in x['reason'] for x in s['excluded'])==3 and sum('cache leaf' in x['reason'] for x in s['excluded'])==82,'threeELF/82cache explicit exclusions')
paths={x['originalPath'] for x in inv.values()};exc={x['path'] for x in s['excluded']};nodes={x['path'] for x in s['nonRegularNodes']}
for root in (J,A,Path('/workspace/train337-browser-L-documents/tmp')):
 actual={str(x) for x in root.rglob('*') if not x.is_dir() or x.is_symlink()};ck(actual<=paths|exc|nodes,'complete non-cache job namespace '+str(root))
report={'schema':'independent-final-L-documents-actual-package-peer/1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'source_sha':L,'original_exit':0,'wrapper_exit':0,'passed_assertions':47,'failed_assertions':0,'screenshots':8,'elapsed_seconds':r['seconds'],'ci_timeout_minutes':10,'archive_sha256':p['archiveSHA256'],'member_count':670,'raw_original_bytes':31819902,'limits':s['limits'],'reviewer_correction':'Initial checker added an unnecessary second trailing newline and compared current_geometry.c raw CRLF with original LF-normalized fingerprint; initial report/script retained. Only checker follows original driver321/binaries183 rules; no subject/receipt/archive change.', 'scope':'All archived members compared with immutable original bytes/symlinks; exact L workflow, original job/launcher/reaper raw, prior pool guards, source fingerprint inputs and declared exclusions verified. No browser/test rerun. No claim other browser jobs or native passed.'}
q=O/'FINAL_L_DOCUMENTS_ACTUAL_PACKAGE_PEER.json';q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':checks,'exit_code':report['exit_code'],'findings':findings,'report':str(q),'sha256':h(q)},ensure_ascii=False));sys.exit(report['exit_code'])
