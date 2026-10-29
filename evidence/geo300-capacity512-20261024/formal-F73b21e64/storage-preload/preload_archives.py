"""Run the already-reviewed archive-only storage tool in an assigned root snapshot window."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,sys
P=Path(__file__).resolve().parent;OUT=Path('/tmp/geo348-original-archives-preload-20261024')
ROOT=Path('/workspace/geometry-axiom');READER=Path('/workspace/geo300-capacity512-work-20261024')
STORE=Path('/tmp/geo337-published-archive-git-objects-20261024')
TOOL=Path('/workspace/git-archive-object-store-tool-20261024/write_archive_blob.py')
TOOL_SHA='d4c9f40e41aac7e210a038f466f89945b8c21b68ffff9b6f44c2c6fed244d940'
LEASE_SHA='556c513142d9559c9497bb118d12da5487ee61b80953ee27095e49269d7c0104'
ALTERNATE_SHA='e4003887d478e946abfb1c76daa861b688d1c37d936f510a73fd833fbf48b7be'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
ARCHIVES=[
 {'label':'historical-F0f','path':'/workspace/geo348-F0f695866-formal-package/ORIGINAL_W7_H7_AND_HELPER_TRIPLES.tar.gz','source_sha':'0f695866c0ba12d2c70dfd7d40628d0fda0f905f','bytes':12616070,'sha256':'dbe988b880024aee708d85d3b0364adf5ab61c9587f861271d8e2170755b37a7'},
 {'label':'targeted-F73','path':'/workspace/geo348-F73b21e64-formal-with-resume-package-r2/ORIGINAL_AFFECTED_H3_HELPERS_AND_ENVIRONMENT_RESUME.tar.gz','source_sha':'73b21e64dce72f0d16ca29e18559c51815b9724d','bytes':13842178,'sha256':'72eb29033c8d7d6bed80fd045ba302846313815ca0953a8aa5148abbbf0c3b23'}]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root-head',required=True);a=ap.parse_args()
 need(len(a.root_head)==40 and all(c in '0123456789abcdef'for c in a.root_head),'explicit full assigned root HEAD')
 need(h(TOOL)==TOOL_SHA,'reviewed storage core exact pin')
 need(h(CAP)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762','original recorder')
 need(h(STORE/'info/CODEX_PERMANENT_OBJECTS.json')==LEASE_SHA,'permanent root store lease')
 need(h(ROOT/'.git/objects/info/alternates')==ALTERNATE_SHA,'exact connected root alternate')
 need(not OUT.exists(),'fresh original output')
 for item in ARCHIVES:need(Path(item['path']).stat().st_size==item['bytes'],'known original archive size')
 # Store is already connected. Only new archive objects and small receipts
 # may be written; keep margin for compression and metadata, not test policy.
 need(shutil.disk_usage('/tmp').free>=sum(x['bytes']for x in ARCHIVES)+16*1024*1024,'archive-only TMP storage budget')
 OUT.mkdir();original_env=dict(os.environ)
 env={k:v for k,v in original_env.items()if not k.startswith('GIT_')}
 env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1')
 sp=importlib.util.spec_from_file_location('capture',CAP);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
 rec=c.Recorder(OUT/'outer',env,a.root_head)
 request={'root_head':a.root_head,'core_sha256':TOOL_SHA,'archives':ARCHIVES,'ordinary_reader':str(READER),'permanent_store':str(STORE),'permanent_lease_sha256':LEASE_SHA,'root_alternate_sha256':ALTERNATE_SHA,'cleared_child_git_variable_names':sorted(k for k in original_env if k.startswith('GIT_')),'refs_index_products_changed':False}
 dump(OUT/'REQUEST.json',request);result={**request,'exit':1,'phases':[]}
 try:
  for item in ARCHIVES:
   argv=[sys.executable,'-B',str(TOOL),'--repo',str(ROOT),'--archive',item['path'],'--store',str(STORE),'--out',str(OUT/item['label']),'--expected-head',a.root_head,'--archive-source-sha',item['source_sha'],'--expected-common-dir',str(ROOT/'.git'),'--expected-alternates',ALTERNATE_SHA,'--expected-archive-sha256',item['sha256'],'--expected-archive-bytes',str(item['bytes']),'--expected-store-lease-sha256',LEASE_SHA,'--reader',str(READER)]
   row,out,err=rec.run(argv,cwd=ROOT,timeout=None,check=False,source_variant='archive-only preload; no product execution or ref adoption')
   result['phases'].append({'label':item['label'],'actual_exit':row['actual_process_returncode'],'directory':row['directory'],'tool_result':str(OUT/item['label']/'RESULT.json')})
   need(row['actual_process_returncode']==0,'original preload tool failure; preserve original result')
   r=json.loads((OUT/item['label']/'RESULT.json').read_bytes());need(r['exit_code']==0 and r['global_git_environment_unchanged'],'completed storage-only phase')
  need(dict(os.environ)==original_env,'parent environment unchanged');result['exit']=0
 except BaseException as e:result['error']=repr(e)
 finally:
  result['parent_environment_unchanged']=dict(os.environ)==original_env;dump(OUT/'RESULT.json',result);print(json.dumps(result,ensure_ascii=False))
 return result['exit']
if __name__=='__main__':sys.exit(main())
