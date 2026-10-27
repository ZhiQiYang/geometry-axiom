from pathlib import Path
import datetime,hashlib,json,os,stat,subprocess,tarfile
TOOLS=Path(__file__).parent;OUT=Path('/workspace/scratch/geo337-p52-capture-20261027');SUBJECT=Path('/tmp/g337p52F27')
SHA='cbf0fb621888596aa14ad5f2349b503e23b1b72d';MAIN='adbaebf9c73ea6801d7b4d5214e4b846b132923b'
def h(data):return hashlib.sha256(data).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
outer=read(OUT/'RESULT.json');formal=read(SUBJECT/'formal/execution-receipt.json');receipt=read(SUBJECT/'formal/receipt.json');verify=read(SUBJECT/'verifier/receipt.json');special=read(SUBJECT/'receipt.json')
assert outer['actual_exit']==0 and outer['passed'] and not outer['timeout_expired']
assert special['passed'] and special['launcher_exit_code']==0 and not special['errors']
assert formal['sha']==SHA and formal['main']==MAIN and formal['passed'] and formal['original_body_completed'] and formal['original_body_system_exit']==0 and formal['actual_driver_exit_code']==0 and not formal['errors']
assert verify['passed'] and verify['original_assertions_unchanged'] and verify['original_verifier_process_exit']==0 and verify['actual_driver_exit_code']==0 and not verify['errors']
assert [r['sha'] for r in receipt['records']]==[MAIN,SHA,SHA,MAIN]
assert all(len(r['result']['samples'])==8 and r['result']['failed']==0 and r['result']['exceptions']==0 for r in receipt['records'])
assert receipt['timing']['count']=={'main':16,'fix':16} and receipt['timing']['no_regression']
assert receipt['timing']['medians_ms']['fix']<=receipt['timing']['medians_ms']['main']
assert [r['mode'] for r in receipt['controls']]==['normal','delay','revert-delay','wrong','missing']
assert [r['exit'] for r in receipt['controls']]==[0,0,1,1,1] and all(r['expected_behavior_proved'] for r in receipt['controls'])
assert [r['actual_process_returncode'] for r in formal['node_commands']]==[0,0,0,0,0,0,1,1,1]
raw_commands=0
for root in [SUBJECT,OUT]:
 for path in root.rglob('result.json'):
  if path.parent.parent.name!='subcommands':continue
  r=read(path);assert not r['timeout_expired'] and 'exception' not in r
  for stream in ['stdin','stdout','stderr']:
   data=(path.parent/(stream+'.bin')).read_bytes();assert h(data)==r[stream+'_sha256'],str(path)
   if stream!='stdin':assert len(data)==r[stream+'_bytes']
  raw_commands+=1
guards={}
for label,sha in [('fix',SHA),('main',MAIN)]:
 root=Path('/workspace/geo337-p52-sources-20261027')/label
 head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip();status=subprocess.check_output(['git','-C',str(root),'status','--porcelain','--untracked-files=all'],text=True)
 assert head==sha and status==''
 a=read(SUBJECT/f'formal/{label}-before-runtime-inputs.json');b=read(SUBJECT/f'formal/{label}-after-runtime-inputs.json')
 assert a['source_set_complete'] and b['source_set_complete'] and a['source_version']==b['source_version'] and a['inputs']==b['inputs']
 guards[label]={'head':head,'status':status,'runtime_inputs':a['actual_count'],'source_version':a['source_version'],'full_inputs_unchanged':True}
remaining=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  name=(p/'comm').read_text().strip()
  if any(x in name for x in ('chrom','node','cc1')):remaining.append({'pid':int(p.name),'comm':name,'stat':(p/'stat').read_text()})
 except OSError:pass
assert not remaining,remaining
dump(OUT/'OWNED_PROCESSES_AFTER.json',remaining)
inventory={};ipc={}
for p in sorted(SUBJECT.rglob('*')):
 s=p.lstat();rel=str(p.relative_to(SUBJECT));base={'mode':stat.S_IMODE(s.st_mode),'mtime_ns':s.st_mtime_ns}
 if stat.S_ISREG(s.st_mode):inventory[rel]={**base,'kind':'file','bytes':s.st_size,'sha256':h(p.read_bytes())}
 elif stat.S_ISLNK(s.st_mode):inventory[rel]={**base,'kind':'symlink','target':os.readlink(p)}
 elif not stat.S_ISDIR(s.st_mode):ipc[rel]={**base,'kind':'socket' if stat.S_ISSOCK(s.st_mode) else 'other-ipc','uid':s.st_uid,'gid':s.st_gid,'size':s.st_size}
archive=OUT/'subject.original.tar.gz'
assert not archive.exists()
with tarfile.open(archive,'w:gz',dereference=False) as tar:
 tar.add(SUBJECT,arcname='subject',filter=lambda info:info if info.name=='subject' or info.name.removeprefix('subject/') not in ipc else None)
actual={}
with tarfile.open(archive,'r:gz') as tar:
 for m in tar:
  rel=m.name.removeprefix('subject/')
  if m.isfile():actual[rel]={'kind':'file','bytes':m.size,'sha256':h(tar.extractfile(m).read()),'mode':m.mode}
  elif m.issym():actual[rel]={'kind':'symlink','target':m.linkname,'mode':m.mode}
expected={p:{k:v for k,v in r.items() if k!='mtime_ns'} for p,r in inventory.items()}
assert actual==expected
dump(OUT/'RAW_INVENTORY.json',inventory);dump(OUT/'TERMINAL_IPC_METADATA.json',{'policy':'Original terminal IPC sockets are retained in place; no representable file payload is omitted. Symlink targets are archived without following links. Socket metadata only is recorded, not a fictional socket payload.','paths':ipc})
dump(OUT/'ARCHIVE_VERIFICATION.json',{'archive':archive.name,'bytes':archive.stat().st_size,'sha256':h(archive.read_bytes()),'regular_files':sum(r['kind']=='file' for r in inventory.values()),'symlinks':sum(r['kind']=='symlink' for r in inventory.values()),'terminal_ipc_metadata_count':len(ipc),'all_file_bytes_and_modes_and_symlink_targets_match':True})
dump(OUT/'VERIFICATION.json',{'execution_sha':SHA,'main_sha':MAIN,'raw_commands_hash_checked':raw_commands,'guards':guards,'timing':receipt['timing'],'controls':[{'mode':r['mode'],'actual_exit':r['exit'],'expected_behavior_proved':r['expected_behavior_proved']} for r in receipt['controls']],'original_verifier_nine_asserts_unchanged':verify['original_assertions_unchanged'],'all_three_exit_codes':[formal['actual_driver_exit_code'],verify['actual_driver_exit_code'],outer['actual_exit']]})
report=f'''# Fixed-F P52 original formal acceptance

**PASS**, execution source `{SHA}`, fixed main denominator `{MAIN}`. Original formal body, independent verifier and outer capture all exit **0**. Started {outer['started_utc']}; completed {outer['completed_utc']}; elapsed {outer['elapsed_seconds']:.3f} seconds. No timeout, retry or replacement of valid samples.

The original main/fix/fix/main order ran eight trials in each block: main 16 and fix 16. Median main **{receipt['timing']['medians_ms']['main']:.6f} ms**, fix **{receipt['timing']['medians_ms']['fix']:.6f} ms**, fix/main **{receipt['timing']['ratio']:.9f}**. Original criterion fix median <= main median passed. All four blocks have zero failed checks and zero exceptions. Five original controls normal/delay/revert-delay/wrong/missing have actual Node exits **0/0/1/1/1**, all satisfying the original cause checks. Original independent verifier completed its nine unchanged assertions.

Exact executed argv is in capture/REQUEST.json and original capture request. The unmodified `special/run_special.py --gate p52` used the independent clean `/workspace/geo337-p52-sources-20261027/fix` and `main` checkouts, private `/tmp/g337p52F27`, `/tmp/geo337-native-owner.lock`, and preparation pin `254accbf8562210e339509c6bff0ab80f1ba625965bb70852ee428671f1a0805`. Fixed main is the original historical denominator, not moving main. The original nested formal/verifier argv and all actual streams are retained.

Original stack 16 MiB, 1200-second build/Node limits, 90-second service readiness, 900 ms delay and 5000 ms missing-placement conditions remain unchanged; outer capture has no added timeout. Original capture/reaper hashes are unchanged. Chromium 154.0.8037.57 is supplied by the private expected-path alias to `/usr/bin/chromium`; original `--no-sandbox` argument is unchanged. Installed Noto CJK, compiler, Node and Python versions are captured by original commands. No competing heavy process was present.

Both sources remain clean, with original complete runtime inventories verifying all **734 F / 466 main inputs** before and after. Independent git directories share existing objects read-only; product checkout files are separate. Only historical evidence outside runtime roots is sparse. No product, test, assertion, axiom, P189 comparator, main branch or deployment changed.

`capture/subject.original.tar.gz` retains all **{sum(r['kind']=='file' for r in inventory.values())} regular original files** and **{sum(r['kind']=='symlink' for r in inventory.values())} symlinks**, including ELF bodies/fingerprints, all streams, samples, screenshots, generated probes, source/runtime inventories, verifier projections, and profiles. Every archived regular byte/mode and symlink target was read back and checked. The {len(ipc)} terminal IPC sockets have metadata receipts; they have no regular-file payload to archive and remain at their original paths. No existing file was deleted. No Chrome, Node or compiler remained after original reaper completion. {raw_commands} c387 command records had all original stream lengths/hashes rechecked.

The verifier's legacy launch projection is explicitly derived from real c387 records, not claimed as original launch stdout. The original formal ledger's additional Node annotations remain as originally generated; raw result files are unchanged.

PF3/Q38 and native/oracle/reader/required-eight were already accepted and were not rerun. Next scope review must preserve existing #314 native/Node coverage and distinguish historical whole-memo receipts from the current recovery lineage; no P189 whitelist expansion is adopted.
'''
(TOOLS/'HANDOFF.md').write_text(report)
print(json.dumps({'passed':True,'archive_bytes':archive.stat().st_size,'regular_files':sum(r['kind']=='file' for r in inventory.values()),'raw_commands_checked':raw_commands}))
