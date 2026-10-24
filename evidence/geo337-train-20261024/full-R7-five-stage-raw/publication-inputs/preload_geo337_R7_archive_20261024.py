from pathlib import Path
import fcntl, hashlib, importlib.util, json, os
R=Path('/workspace/geometry-axiom');O=Path('/tmp/geo337-R7-archive-preload-20261024')
STORE=Path('/tmp/geo337-published-archive-git-objects-20261024')
HEAD='bd5df6b7fb3c563fa10d0e4cfd37e2ee3ca2b99e';F='6df0264f75e84f03adb70746b6ac3db07a9910fc'
TOOL=Path('/workspace/git-archive-object-store-tool-20261024/write_archive_blob.py')
PIN='8f2420a2c4a78cd99355b32183928d1c8ce14c893fdbe88db0f101104622cd7e';SIZE=31359550
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H(TOOL)=='d4c9f40e41aac7e210a038f466f89945b8c21b68ffff9b6f44c2c6fed244d940'
package_path=Path('/tmp/geo323-r7-full-package-20261024/PACKAGE.json')
assert H(package_path)=='76673d5886bf55fe9cc710a2b55a2167704b4e29a9e9d89a93b1b2f0214114f1'
package=json.loads(package_path.read_text())
assert package['source_sha']==F and package['archive']['sha256']==PIN and package['archive']['bytes']==SIZE
capture=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert H(capture)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec=importlib.util.spec_from_file_location('capture',capture);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
O.mkdir();env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1')
cap.dump(O/'ENVIRONMENT_SCOPE.json',{'cleared_child_git_variable_names':sorted(k for k in os.environ if k.startswith('GIT_')),'parent_environment_unchanged':True,'permanent_git_objects_store':str(STORE),'do_not_delete_store':True})
rec=cap.Recorder(O/'outer',env,F)
with Path('/tmp/g261r3/secondary.lock').open('a') as lock:
 fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 argv=['python3','-B',str(TOOL),'--repo',str(R),'--archive',package['archive']['path'],'--store',str(STORE),'--out',str(O/'r7'),'--expected-head',HEAD,'--archive-source-sha',F,'--expected-common-dir',str(R/'.git'),'--expected-alternates','e4003887d478e946abfb1c76daa861b688d1c37d936f510a73fd833fbf48b7be','--expected-store-lease-sha256','556c513142d9559c9497bb118d12da5487ee61b80953ee27095e49269d7c0104','--expected-archive-sha256',PIN,'--expected-archive-bytes',str(SIZE)]
 for reader in ['/workspace/geo300-capacity512-work-20261024','/tmp/geo323-final-r7-source-20261024','/tmp/train337-323-f64d638f-source']:
  argv+=['--reader',reader]
 rec.run(argv,cwd=R,check=True,timeout=None,source_variant='preload complete R7 archive into permanent Git object store; no ref or index changes')
 result=json.loads((O/'r7/RESULT.json').read_text())
 assert result['exit_code']==0 and result['alternate_connected'] and not result['refs_or_index_adopted'] and not result['original_objects_moved_or_deleted']
 fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
cap.dump(O/'RESULT.json',{'exit':0,'root_head_unchanged':HEAD,'product_source':F,'protected_store':str(STORE),'do_not_delete_git_objects':True,'global_environment_changed':False,'oid':result['object_oid'],'bytes':SIZE,'sha256':PIN,'receipt':str(O/'r7/RESULT.json'),'lease':result['permanent_lease'],'final_alternates_sha256':result['final_alternates_sha256']})
print((O/'RESULT.json').read_text())
