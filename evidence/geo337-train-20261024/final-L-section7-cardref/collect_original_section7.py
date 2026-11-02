"""Package only terminal original section7 evidence; never run a subject or read ROOT."""
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
p=argparse.ArgumentParser();p.add_argument('--gate',choices=['cardref','axiom'],required=True);a=p.parse_args()
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
summary={'schema':'section7-original-terminal-collection/1','source_sha':L,'gate':a.gate,'original_exit':r['gates'][0]['commands'][0]['primary_command_exit'],'driver_exit':r['launcher_exit_code'],'outer_exit':o['actual_exit'],'original_passed':r['passed'],'source_before':b,'source_after':e,'started_utc':r['started_utc'],'ended_utc':r['ended_utc'],'original_capture_rows':stream_rows,'elf_payload_excluded_count':len(excluded),'elf_payload_excluded_bytes':sum(z['bytes']for z in excluded),'no_existing_file_deleted':True,'no_subject_executed':True,'limitations':['Only outputs exposed by the original runner/capture are retained; no hidden pipe or already-cleaned source snapshot is invented.','All excluded ELF payloads remain at original paths; hashes are retained here, not executable payload bytes.','Before/after identity is the original closed capture; current shared ROOT is intentionally not read.']}
if a.gate=='cardref':
 report=json.loads((out/a.gate/'subject/report.json').read_text());ms=report['mutants'];need(report['source_head']==L,'original report L')
 need(report['baseline']['run']['exit_code']==0 and report['baseline']['counts']['failures']==report['baseline']['counts']['errors']==report['baseline']['counts']['skips']==0,'original baseline success')
 for m in ms:
  need(m['verdict']=='killed' and m['red']['run']['exit_code']==1 and m['red']['counts']['failures']>0 and all(m['red']['counts'][k]==0 for k in ['errors','skips','compile_failures','infrastructure_failures']),'normal assertion red '+m['id'])
  need(m['restored']['run']['exit_code']==0 and all(m['restored']['counts'][k]==0 for k in ['failures','errors','skips','compile_failures','infrastructure_failures']),'restored green '+m['id'])
 summary['original_baseline_counts']=report['baseline']['counts'];summary['original_mutants']=len(ms);summary['mutants_all_normal_assertion_red_and_restored_green']=True
 commands=[]
 for q in sorted((out/a.gate/'subject').rglob('*.command.json')):
  j=json.loads(q.read_text());commands.append({'path':str(q),'exit_code':j.get('exit_code'),'command':j.get('command')})
 summary['original_inner_commands']=len(commands);summary['original_compile_commands']=sum(1 for q in commands if '/compile-' in q['path'])
 summary['original_inner_commands_path']=str(d/'INNER_COMMANDS.json');save(d/'INNER_COMMANDS.json',commands)
for name,value in [('EXCLUDED_ELF_PAYLOADS.json',excluded),('SUMMARY.json',summary)]:save(d/name,value)
for f in sorted(d.iterdir()):
 rows.append({'name':'collection/'+f.name,'source_path':str(f),'bytes':f.stat().st_size,'sha256':hfile(f)})
inv={'source_sha':L,'gate':a.gate,'members':rows,'regular_file_count':len(rows),'logical_original_bytes':sum(z['bytes']for z in rows),'excluded_elf_manifest':'collection/EXCLUDED_ELF_PAYLOADS.json'};save(d/'RAW_INVENTORY.json',inv)
archive=d/'ORIGINAL_SECTION7_LOGS_REPORTS_AND_ELF_HASHES.tar.gz'
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
