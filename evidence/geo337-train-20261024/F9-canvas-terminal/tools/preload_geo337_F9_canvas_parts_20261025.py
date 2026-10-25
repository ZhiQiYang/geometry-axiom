from pathlib import Path
import fcntl, hashlib, importlib.util, json, os, shutil

ROOT=Path('/workspace/geometry-axiom');OUT=Path('/tmp/geo337-F9-canvas-archive-preload-20261025')
STORE=Path('/tmp/geo337-published-archive-git-objects-20261024')
HEAD='c32e70aa2c848f89a0e2e9fd92ed232a4dd27bcc';F='4f8a794f4167c3562eb182045102e86e9e37cca9'
TOOL=Path('/workspace/git-archive-object-store-tool-20261024/write_archive_blob.py')
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H(TOOL)=='d4c9f40e41aac7e210a038f466f89945b8c21b68ffff9b6f44c2c6fed244d940'
pkg=Path('/tmp/geo337-F9-canvas-terminal-package-20261025/RESULT.json')
assert H(pkg)=='eb604c5973fa7e19549d85cd3c7c045485a84a0697730fe6a682f984121fe704'
q=json.loads(pkg.read_bytes());assert q['collection_exit']==0 and q['source_sha']==F and len(q['parts'])==4
assert H('/workspace/geo337-F9-canvas-terminal-package-actual-peer-20261025/REVIEW.json')=='fd9878fbb1c0ce77e724f04a65bc55becec8dc4cc9cec1e72acb437b3df24a0b'
cap=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert H(cap)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec=importlib.util.spec_from_file_location('capture',cap);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OUT.mkdir();env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1')
r=m.Recorder(OUT/'outer',env,F);results=[]
with Path('/tmp/g261r3/secondary.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for part in q['parts']:
  # Admission uses the full input plus conservative zlib overhead and metadata, never an assumed compression ratio.
  n=part['archive_bytes'];required=64*1024*1024+n+(n//4096+1)+(n//16384+1)+2*1024*1024
  assert shutil.disk_usage(STORE).free>=required,'Insufficient fresh TMP room for immutable blob'
  target=OUT/('part'+str(part['part']))
  argv=['python3','-B',str(TOOL),'--repo',str(ROOT),'--archive',part['archive_path'],'--store',str(STORE),'--out',str(target),'--expected-head',HEAD,'--archive-source-sha',F,'--expected-common-dir',str(ROOT/'.git'),'--expected-alternates','e4003887d478e946abfb1c76daa861b688d1c37d936f510a73fd833fbf48b7be','--expected-store-lease-sha256','556c513142d9559c9497bb118d12da5487ee61b80953ee27095e49269d7c0104','--expected-archive-sha256',part['archive_sha256'],'--expected-archive-bytes',str(n)]
  for reader in ['/tmp/geo323-final-r8-source-20261024','/tmp/train337-323-f64d638f-source']:argv+=['--reader',reader]
  row,_,_=r.run(argv,cwd=ROOT,timeout=None,check=False)
  assert row['actual_process_returncode']==0,'Original preload failed; retain raw and do not retry'
  result=json.loads((target/'RESULT.json').read_bytes())
  assert result['exit_code']==0 and result['alternate_connected'] and not result['refs_or_index_adopted']
  results.append({'part':part['part'],'receipt':str(target/'RESULT.json'),'receipt_sha256':H(target/'RESULT.json'),'oid':result['object_oid'],'archive':part})
 m.dump(OUT/'RESULT.json',{'exit_code':0,'source_sha':F,'root_head_unchanged':HEAD,'original_archives_unchanged':True,'permanent_store_do_not_delete':str(STORE),'archives':results})
print(json.dumps({'exit_code':0,'parts':len(results),'result':str(OUT/'RESULT.json')}))
