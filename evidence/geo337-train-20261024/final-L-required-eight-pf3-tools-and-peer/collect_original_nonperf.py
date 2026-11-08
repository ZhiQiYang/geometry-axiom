"""Package only terminal original required-eight/PF3 evidence; never run a subject or read ROOT."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,stat,tarfile
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
def hfile(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def need(x,s):
 if not x:raise RuntimeError(s)
p=argparse.ArgumentParser();p.add_argument('--gate',choices=['required-eight','pf3'],required=True);a=p.parse_args()
out=Path('/workspace/train337-final-L-'+a.gate+'-7af8c5d8');outer=Path(str(out)+'-launch');d=Path(__file__).parent/a.gate
need(not d.exists(),'fresh collection directory required')
r=json.loads((out/'receipt.json').read_text());o=json.loads((outer/'RESULT.json').read_text())
need(r['source_sha']==o['source_sha']==L and r.get('ended_utc') and r['launcher_exit_code']==o['actual_exit'] and len(r['gates'])==1,'real exact-L terminal receipts required')
b=json.loads((out/a.gate/'before-source.json').read_text());e=json.loads((out/a.gate/'after-source.json').read_text())
need(b==e and b['head']==L and b['status']=='','original source guard must restore; no current ROOT read')
d.mkdir();rows=[];excluded=[];stream_rows=[]
for label,root in [('original',out),('outer',outer)]:
 for f in sorted(root.rglob('*')):
  s=f.lstat();name=label+'/'+str(f.relative_to(root))
  if stat.S_ISDIR(s.st_mode):continue
  need(stat.S_ISREG(s.st_mode),'unexpected nonregular original evidence: '+str(f))
  with f.open('rb') as fh:elf=fh.read(4)==b'\x7fELF'
  z={'name':name,'source_path':str(f),'bytes':s.st_size,'sha256':hfile(f)}
  if elf:z['reason']='ELF payload excluded only; original ordinary or controlled executable retained at source_path';excluded.append(z)
  else:rows.append(z)
 for row in json.loads((root/'subcommands.json').read_text()):
  q=Path(row['directory']);need(q.is_relative_to(root),'capture directory containment')
  saved=json.loads((q/'result.json').read_text());need(saved==row,'original c387 row equals result')
  for kind in ['stdout','stderr']:
   f=q/(kind+'.bin');need(f.stat().st_size==row[kind+'_bytes'] and hfile(f)==row[kind+'_sha256'],'full captured '+kind)
  f=q/'stdin.bin';need(hfile(f)==row['stdin_sha256'],'full captured stdin')
  need((q/'request.json').is_file(),'original request retained')
  stream_rows.append({'directory':str(q),'exit':row['actual_process_returncode'],'timeout':row['timeout_expired'],'source_sha':row['source_sha']})
# Keep the original frozen preparation/capture/reaper bytes alongside their original receipt pins.
for root in [Path('/tmp/train337-final-nonperf-specials-prep')]:
 for f in sorted(root.iterdir()):
  if f.is_file() and f.suffix in ['.py','.json','.md']:
   rows.append({'name':'tools/'+f.name,'source_path':str(f),'bytes':f.stat().st_size,'sha256':hfile(f)})
for f in [Path(__file__),Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py'),Path('/workspace/geo261-environment/reap_children.py')]:
 rows.append({'name':'capture-tools/'+f.name,'source_path':str(f),'bytes':f.stat().st_size,'sha256':hfile(f)})
need(len({z['name']for z in rows})==len(rows),'unique package members')
summary={'schema':'required-eight-pf3-original-terminal-collection/1','source_sha':L,'gate':a.gate,'original_exit':r['gates'][0]['commands'][0]['primary_command_exit'],'driver_exit':r['launcher_exit_code'],'outer_exit':o['actual_exit'],'original_passed':r['passed'],'source_before':b,'source_after':e,'started_utc':r['started_utc'],'ended_utc':r['ended_utc'],'original_capture_rows':stream_rows,'elf_payload_excluded_count':len(excluded),'elf_payload_excluded_bytes':sum(z['bytes']for z in excluded),'no_existing_file_deleted':True,'no_subject_executed':True,'limitations':['Only outputs exposed by the original runner/capture are retained; no hidden pipe or already-cleaned source snapshot is invented.','All excluded ELF payloads remain at original paths; hashes are retained here, not executable payload bytes.','Before/after identity is the original closed capture; current shared ROOT is intentionally not read.']}
# Preserve the v4 subject's distinct stage receipt and complete inner capture.
stage_receipt=out/a.gate/'subject/receipt.json';stage=json.loads(stage_receipt.read_text())
need(stage['source_sha']==L and stage['stages'][a.gate]['ended_utc'] and stage['stages'][a.gate]['execution_exit']==0 and stage['wrapper_exit']==0,'original nested stage terminal0 required')
need(hfile(stage_receipt)==r['gates'][0]['original_stage_receipt_sha256'],'original stage receipt pin')
inner=[]
for commands in sorted((out/a.gate/'subject/invocations').glob('*/commands/commands.json')):
 for row in json.loads(commands.read_text()):
  q=Path(row['directory']);need(q.is_relative_to(out/a.gate/'subject'),'inner capture containment')
  need(json.loads((q/'result.json').read_text())==row,'inner row matches full result')
  for kind in ['stdout','stderr']:
   f=q/(kind+'.bin');need(f.stat().st_size==row[kind+'_bytes'] and hfile(f)==row[kind+'_sha256'],'complete inner stream '+kind)
  need(row['source_sha']==L and row['ended_epoch'] and not row['timeout_expired'],'inner L terminal identity')
  inner.append(row)
summary['original_nested_stage']={k:stage[k] for k in ['source_sha','stages','wrapper_exit','all_executed_stage_commands_passed','full_acceptance_passed']}
summary['original_inner_commands']=len(inner)
save(d/'INNER_COMMANDS.json',inner)
if a.gate=='required-eight':
 expected=json.loads((Path('/tmp/train337-final-nonperf-specials-prep')/'PREPARATION.json').read_text())['required_eight_expected']
 selected=[x for x in inner if 'tests/run_all.py' in x['command']]
 need(len(selected)==1 and selected[0]['actual_process_returncode']==0,'one original selected aggregate')
 argv=selected[0]['command'];names=[argv[i+1] for i,x in enumerate(argv) if x=='--only']
 need(set(names)==set(expected) and len(names)==8,'original exact eight selection')
 text=(Path(selected[0]['directory'])/'stdout.bin').read_text();counts=[]
 for name,e in expected.items():
  found=[line.split() for line in text.splitlines() if line.split() and line.split()[0]==name]
  need(len(found)==1,'one actual aggregate row '+name);fields=found[0]
  count,passed,failed,skipped=map(int,fields[1:5]);need(count==passed==e['count'] and failed==skipped==0,'original exact selected row '+name)
  counts.append(dict(name=name,count=count,passed=passed,failed=failed,skipped=skipped,unit=e['unit']))
 need(sum(x['count'] for x in counts)==676,'original selected676')
 summary['original_selected_counts']=counts
 summary['selected_total_registered_units']=676
 summary['selected_aggregate_capture']=selected[0]['directory']
 summary['limitations'].append('required-eight-suite-logs is the original runner copy of the global log directory, which can retain previous unselected logs. Only the exact eight selected argv and original aggregate rows above count as this execution; 676 combines tests, C checkpoints and scenarios, not676 unittest methods.')
else:
 original=out/a.gate/'subject/evidence/pf3/summary.json';report=json.loads(original.read_text())
 need(report['originalSourcesUnchanged'] is True,'PF3 original source restore')
 for phase in ['baseline','restored']:
  item=report[phase];need(item['verdict']=='pass' and item['exit']==0 and item['counts']==dict(run=20,failures=0,errors=0,skipped=0),'PF3 original full20 '+phase)
 mutants=report['mutations'];need(len(mutants)==19 and len({x['id'] for x in mutants})==19,'original distinct19 mutations')
 for item in mutants:
  need(item['verdict']=='killed' and item['exit']==1 and item['counts']==dict(run=1,failures=1,errors=0,skipped=0) and bool(item['requiredMarker']),'PF3 original assertion kill '+item['id'])
 summary['original_pf3_report']=dict(path=str(original),sha256=hfile(original),baseline=report['baseline'],mutations=mutants,restored=report['restored'],originalSourcesUnchanged=True)
 summary['limitations'].append('PF3 baseline20, nineteen independent one-method assertion negatives, restored20 are separate counts; compiler executions are not test passes or mutation kills.')
for name,value in [('EXCLUDED_ELF_PAYLOADS.json',excluded),('SUMMARY.json',summary)]:save(d/name,value)
for f in sorted(d.iterdir()):
 rows.append({'name':'collection/'+f.name,'source_path':str(f),'bytes':f.stat().st_size,'sha256':hfile(f)})
inv={'source_sha':L,'gate':a.gate,'members':rows,'regular_file_count':len(rows),'logical_original_bytes':sum(z['bytes']for z in rows),'excluded_elf_manifest':'collection/EXCLUDED_ELF_PAYLOADS.json'};save(d/'RAW_INVENTORY.json',inv)
archive=d/'ORIGINAL_NONPERF_LOGS_REPORTS_AND_ELF_HASHES.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=6,dereference=True) as t:
 for z in rows:t.add(z['source_path'],arcname=z['name'],recursive=False)
 t.add(d/'RAW_INVENTORY.json',arcname='RAW_INVENTORY.json',recursive=False)
expected={z['name']:z for z in rows};seen=set()
with tarfile.open(archive,'r:gz') as t:
 for m in t:
  need(m.isfile() and m.name not in seen,'unique regular member');seen.add(m.name)
  body=t.extractfile(m).read()
  if m.name=='RAW_INVENTORY.json':need(body==(d/'RAW_INVENTORY.json').read_bytes(),'inventory roundtrip')
  else:
   z=expected[m.name];need(len(body)==z['bytes'] and hashlib.sha256(body).hexdigest()==z['sha256'] and hfile(Path(z['source_path']))==z['sha256'],'original byte roundtrip '+m.name)
need(seen==set(expected)|{'RAW_INVENTORY.json'},'exact archive coverage')
package={'source_sha':L,'gate':a.gate,'archive':{'path':str(archive),'bytes':archive.stat().st_size,'sha256':hfile(archive),'members':len(seen)},'inventory':{'path':str(d/'RAW_INVENTORY.json'),'sha256':hfile(d/'RAW_INVENTORY.json')},'all_selected_original_bytes_roundtrip':True,'elf_payloads_included':False,'original_elf_files_retained':True,'subject_executions':0,'published':False}
save(d/'PACKAGE.json',package);print(json.dumps(package))
