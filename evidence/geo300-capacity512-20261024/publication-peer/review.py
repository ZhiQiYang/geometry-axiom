from pathlib import Path
import hashlib,json,subprocess,tarfile
ROOT=Path('/workspace/geo300-capacity512-work-20261024')
BASE=Path('/workspace/geo300-capacity512-publication-20261024');OUT=Path('/workspace/geo300-capacity512-public-package-peer-20261024')
S='400a6d0ca50f3aca104fb569c77c8ef753c93355';M='696f7f07846c6224775dab5736bd1dc45541a4bf'
def sha(body):return hashlib.sha256(body).hexdigest()
count=0;failures=[];commands=[]
def check(label,value):
 global count;count+=1
 if not value:failures.append(label)
def git(*args):
 r=subprocess.run(['git',*args],cwd=ROOT,capture_output=True,timeout=60)
 commands.append({'argv':['git',*args],'cwd':str(ROOT),'exit':r.returncode,'stdout_bytes':len(r.stdout),'stdout_sha256':sha(r.stdout),'stderr':r.stderr.decode('utf-8',errors='replace'),'source_locator':'Public Git object '+S+' (not re-copied due root disk budget)'})
 check('git-exit:'+repr(args),r.returncode==0);return r.stdout
index=json.loads((BASE/'package/RAW_INDEX.json').read_bytes());archive=BASE/'package'/index['archive']
check('public-S-and-fixed-archive',index['product_sha']==S and index['archive_bytes']==751021 and index['member_count']==578 and index['archive_sha256']=='0b6ea82d93952e40dc199483828c3e595401720f4e36da755022e9e8fe016542')
check('actual-archive-size-hash',archive.stat().st_size==index['archive_bytes'] and sha(archive.read_bytes())==index['archive_sha256'])
with tarfile.open(archive,'r:gz')as tar:
 members=tar.getmembers();check('exact-unique-member-set',len(members)==578 and len({m.name for m in members})==578 and {m.name for m in members}=={r['member']for r in index['files']})
 rows={r['member']:r for r in index['files']}
 for m in members:
  r=rows[m.name];check('regular-safe:'+m.name,m.isfile() and not m.name.startswith('/') and '..'not in Path(m.name).parts)
  raw=tar.extractfile(m).read();check('member-bytes-pin:'+m.name,len(raw)==r['bytes']and sha(raw)==r['sha256'])
  check('exact-original-local:'+m.name,raw==Path(r['source']).read_bytes())
check('exact-S-parent',git('show','-s','--format=%H %P',S).decode().strip()==S+' '+M)
prep=json.loads((BASE/'source-preparation/RESULT.json').read_bytes())
names=git('diff-tree','--no-commit-id','--name-only','-r',S).decode().splitlines()
check('only-fifteen-reviewed-leaves',set(names)==set(prep['candidate_files'])and len(names)==15)
for path,pin in prep['candidate_files'].items():
 raw=git('show',S+':'+path)
 check('public-byte-pin:'+path,len(raw)==pin['bytes']and sha(raw)==pin['sha256'])
remote=git('ls-remote','--heads','origin','refs/heads/codex/geo300-capacity512-20261024').split()
check('public-remote-resolves-S',remote and remote[0].decode()==S)
progress=(BASE/'PROGRESS.md').read_text();questions=(BASE/'QUESTIONS.md').read_text()
check('one-current-state-matrix',progress.count('唯一 current-state')==1)
check('AST-not-runtime',all(x in progress for x in ('AST 7／5','尚未 runtime discovery','UNRUN at this S','不能宣稱 0 skip','NOT READY')))
check('no-inherited-green',all(x in progress for x in ('不把 #346 或 P2','反證 | **UNRUN**','正式 C 時槽尚未授權')))
check('512-unplaced-boundary-explicit','不能當作512個已放置' in progress and '未放置 fixture 不取代它' in questions)
check('safe-no-append-negative-boundary','不得把有效第513成員送進已撤 guard 的固定512陣列' in progress)
check('registry-and-original-witness-boundaries','P2=13、report=11' in progress and '原 64 witnesses 保留' in progress)
check('prior-helper-error-transparent','初 matcher' in progress and '原稿與修正也保留' in progress)
result={'schema':'independent-capacity512-public-source-package-peer/1','product_sha':S,'source_parent':M,'checks_total':count,'failed_checks':len(failures),'findings':failures,'archive_sha256':index['archive_sha256'],'members':len(index['files']),'public_git_reads':commands,'progress_sha256':sha(progress.encode()),'questions_sha256':sha(questions.encode()),'raw_index_sha256':sha((BASE/'package/RAW_INDEX.json').read_bytes()),'scope':'Read-only archive roundtrip/public-source and wording narrow review; no subject or compiler execution. No payload copies under disk constraint.','compiled':False,'formal':'UNRUN'}
(OUT/'REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':count,'failed':len(failures),'findings':failures,'review_sha256':sha((OUT/'REVIEW.json').read_bytes())}))
raise SystemExit(bool(failures))
