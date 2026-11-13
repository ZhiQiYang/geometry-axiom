"""Independent compact archive/descriptor review; no C, extraction or mutation."""
from pathlib import Path
import hashlib,json,os,stat,tarfile
P=Path('/workspace/geo348-F73b21e64-formal-with-resume-package-r2');O=Path('/workspace/geo348-F73-package-peer-combined-20261024');O.mkdir(exist_ok=False)
checks=0;failures=[]
def check(value,label):
 global checks
 checks+=1
 if not value:failures.append(label)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
j=read(P/'RAW_INDEX.json');s=read(P/'SUMMARY.json');a=P/j['archive'];rows=j['files']
check(j['source_sha']=='73b21e64dce72f0d16ca29e18559c51815b9724d','source');check(j['member_count']==len(rows)==5901,'member count');check(a.stat().st_size==j['archive_bytes']==13842178,'archive bytes');check(sha(a.read_bytes())==j['archive_sha256']=='72eb29033c8d7d6bed80fd045ba302846313815ca0953a8aa5148abbbf0c3b23','archive pin')
check(len({r['member']for r in rows})==len(rows),'unique member names');total=0
with tarfile.open(a,'r:gz')as tf:
 members=tf.getmembers();check(len(members)==len(rows),'actual tar count')
 for row,member in zip(rows,members):
  check(member.isfile() and member.name==row['member'],'member type/order '+row['member']);raw=tf.extractfile(member).read();path=Path(row['source']);st=path.lstat()
  check(stat.S_ISREG(st.st_mode)and not path.is_symlink(),'original regular '+row['member'])
  check(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'indexed member bytes '+row['member']);check(raw==path.read_bytes(),'actual original bytes '+row['member']);total+=len(raw)
check(total==s['original_bytes']==92383591,'total original regular/descriptor bytes')
descriptor=read(P/'SPECIAL_FIXTURE_ENTRIES.json')['entries'];check(len(descriptor)==6,'exact special inventory')
check(sorted(x['original_kind']for x in descriptor)==['fifo']*3+['symlink']*3,'three fifo plus three symlink')
for item in descriptor:
 path=Path(item['original_path']);st=path.lstat();check(st.st_mode==item['mode'],'original special lstat '+str(path));expected_kind='symlink' if stat.S_ISLNK(st.st_mode)else 'fifo' if stat.S_ISFIFO(st.st_mode)else 'other';check(expected_kind==item['original_kind'],'original special kind '+str(path))
 if expected_kind=='symlink':check(os.readlink(os.fsencode(path)).hex()==item['readlink_bytes_hex'],'exact raw readlink '+str(path))
 else:check(item['readlink_bytes_hex'] is None,'FIFO metadata only '+str(path))
 check(not any(r['source']==str(path)for r in rows),'special not misrepresented as regular '+str(path))
first=read(Path('/workspace/geo348-F73b21e64-formal/RESULT.json'));resume=read(Path('/workspace/geo348-F73b21e64-sentinel-resume/RESULT.json'))
check(first['exit_code']==s['original_partial_exit']==1 and first['accepted'] is False,'original environment red preserved');check(resume['exit_code']==s['environment_resume_exit']==0 and resume['accepted'] is True,'separate resume true0')
check(len(first['phases'])==13 and all(x['passed'] for x in first['phases'][:10]),'first ten phases complete');check(all(x['state']=='UNRUN_ENVIRONMENT' for x in first['phases'][10:]),'last three original environment unrun')
check([x['actual_exit']for x in resume['phases']]==[0,1,0]and all(x['passed']and x['observation_complete']for x in resume['phases']),'resume exact normal0/1/0 complete');check(first['source_clean_after']and resume['source_clean_after'],'both source clean')
result={'source_sha':j['source_sha'],'checks':checks,'failed_checks':len(failures),'failures':failures,'member_count':len(rows),'archive_sha256':j['archive_sha256'],'original_regular_and_descriptor_bytes':total,'special_entry_count':6,'first_batch_exit':1,'resume_exit':0,'scope':'Independent full archive/original-byte roundtrip and exact six lstat/readlink descriptors; small true terminal phase projection. No C, tar extraction, archive rewrite, or independent full H/pipe/ELF semantic rerun. Backlog171 actual covers the separate targeted native assertions.','limits':['Original firstbatch exit1 is retained; resume0 does not relabel the old batch.','Neither unresolved512 placed method, fullH7, native/browser/ledger/architecture is certified by this package.','FIFO streams never opened and symlink targets never followed.']}
(O/'REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':checks,'failed_checks':len(failures),'review':str(O/'REVIEW.json'),'sha256':sha((O/'REVIEW.json').read_bytes())}));raise SystemExit(bool(failures))
