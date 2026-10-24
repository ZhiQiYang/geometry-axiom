from pathlib import Path
import fcntl,hashlib,importlib.util,json,os
R=Path('/workspace/geometry-axiom');O=Path('/tmp/geo337-archive-object-store-root-20261024');STORE=Path('/tmp/geo337-published-archive-git-objects-20261024')
HEAD='3df56ff38b450ad228da04b2c1dcb6511582af42'
TOOL=Path('/workspace/git-archive-object-store-tool-20261024/write_archive_blob.py')
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H(TOOL)=='d4c9f40e41aac7e210a038f466f89945b8c21b68ffff9b6f44c2c6fed244d940'
assert H('/workspace/git-archive-store-peer-combined-r2-20261024/REVIEW.json')=='597e503a1b2ec5a0068dd51ee21f510457526e4e8a27a7cfb4b4ec5f98c0abec'
p=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');assert H(p)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
sp=importlib.util.spec_from_file_location('cap',p);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
O.mkdir();env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1')
c.dump(O/'ENVIRONMENT_SCOPE.json',{'cleared_child_git_variable_names':sorted(k for k in os.environ if k.startswith('GIT_')),'parent_environment_unchanged':True,'native_or_mutation_environment_changed':False,'permanent_git_objects_store':str(STORE),'do_not_delete_store':True})
r=c.Recorder(O/'outer',env,HEAD);results=[]
with Path('/tmp/g261r3/heavy.lock').open('a') as lock:
    fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    for label,source,pin,size in [('r5','a22df116c7e9f6b7d074451f1c8052d59e7e4f3e','caaf311a748c2ce1dc4ebd754fbebc9c4d70f59a5d0938fb2e9e34e57f2dd794',31186327),('r6','2bbe54f19b2d19e8a816530f0c4edca950629a34','a9113e5e8e3474da70ee21970a29d451a46e148a3abdde1cecded4c36631d3f1',31317807)]:
        package=json.loads(Path('/tmp/geo323-'+label+'-full-package-20261024/PACKAGE.json').read_text())
        assert package['source_sha']==source and package['archive']['sha256']==pin and package['archive']['bytes']==size
        prior='absent' if not results else results[-1]['final_alternates_sha256']
        argv=['python3','-B',str(TOOL),'--repo',str(R),'--archive',package['archive']['path'],'--store',str(STORE),'--out',str(O/label),'--expected-head',HEAD,'--archive-source-sha',source,'--expected-common-dir',str(R/'.git'),'--expected-alternates',prior,'--expected-archive-sha256',pin,'--expected-archive-bytes',str(size)]
        if results:argv+=['--expected-store-lease-sha256',results[-1]['permanent_lease']['sha256']]
        for reader in ['/workspace/geo300-capacity512-work-20261024','/workspace/geo323-final-r6-source-20261024','/tmp/train337-323-f64d638f-source']:argv+=['--reader',reader]
        row,out,err=r.run(argv,cwd=R,timeout=None,check=True,source_variant='store exact immutable archive blob only; no refs or index adoption')
        result=json.loads((O/label/'RESULT.json').read_text());assert result['exit_code']==0 and result['alternate_connected'] and not result['refs_or_index_adopted'] and not result['original_objects_moved_or_deleted']
        results.append(result)
    fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
c.dump(O/'RESULT.json',{'exit':0,'root_head_unchanged':HEAD,'protected_store':str(STORE),'do_not_delete_git_objects':True,'existing_objects_moved_or_deleted':False,'refs_or_index_adopted':False,'global_environment_changed':False,'archives':[{'label':label,'source_sha':x['archive_source_sha'],'oid':x['object_oid'],'bytes':x['archive_identity']['bytes'],'sha256':x['archive_identity']['sha256'],'receipt':str(O/label/'RESULT.json')} for label,x in zip(['r5','r6'],results)],'lease':results[-1]['permanent_lease'],'final_alternates_sha256':results[-1]['final_alternates_sha256']})
print((O/'RESULT.json').read_text())
