"""Prepare small root-owned publisher input after PUBLIC collection; never publishes or copies payloads."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,stat
HERE=Path(__file__).resolve().parent
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
PRIVATE=OWN/'geo323-F9-owner-comparison-terminal-package-shm-v2-20261025'
F='4f8a794f4167c3562eb182045102e86e9e37cca9'
DEST='evidence/geo337-train-20261024/F9-geo323-ABC-comparison-public/'
SCANNER_PIN='9dfe7dd170477ffc99d2cbbf580325a300d4437649c9b40737a7a30a1321422a'

def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(p.read_bytes())
def statkey(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_nlink)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--public-root',type=Path,required=True)
 p.add_argument('--collection-launch',type=Path,required=True)
 p.add_argument('--launch-script',type=Path,required=True)
 p.add_argument('--host-final',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 need(a.out.is_absolute() and a.out.parent==Path('/workspace') and not a.out.exists(),'New direct WS manifest only')
 need(a.public_root.parent==OWN and a.public_root.name.startswith('geo323-F9-PUBLIC-comparison-') and not OWN.is_symlink() and OWN.resolve()==OWN and not a.public_root.is_symlink(),'Exact PUBLIC SHM root')
 need(a.collection_launch.parent==OWN and not a.collection_launch.is_symlink(),'Exact root collection launch in OWN SHM')
 receipt=load(a.public_root/'RESULT.json')
 need(receipt['source_sha']==F and receipt['collection_exit']==0 and receipt['private_complete_bundle_mutated'] is False,'Actual successful PUBLIC collection required')
 need(receipt['selected_members']==4666 and receipt['selected_regular_files']==4662 and receipt['selected_symlinks']==4 and receipt['selected_regular_bytes']==19843056,'Exact PUBLIC selected scope')
 need(receipt['excluded_auxiliary_profile_members']==1 and receipt['excluded_auxiliary_profile_bytes']==2795 and receipt['all_formal_comparison_commands_preserved']==712,'Exact PUBLIC exclusion/formal scope')
 host=load(a.host_final)
 need(digest(a.host_final)=='c22a1520d99ee284c66f0dd1c8d8f6eebe62c4d7e69af1c0c3c0d8cacf298533' and host['source_sha']==F and type(host['actual_tool_result']['exit_code']) is int and host['actual_tool_result']['exit_code']==0 and 'session_id' not in host['actual_tool_result'],'Exact completed original wrapped root host0 required')
 scanner=HERE/'scan_profile_scope.py';need(digest(scanner)==SCANNER_PIN,'Reviewed scanner changed')
 spec=importlib.util.spec_from_file_location('public_profile_inspector',scanner);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 original_profile=mod.PROFILE.read_bytes();need(hashlib.sha256(original_profile).hexdigest()==mod.PROFILE_PIN,'Original auxiliary cloud-only profile changed')
 body,profile=mod.body_of(original_profile);inspect=mod.make_profile_inspector(original_profile,body,profile)
 files=[];destinations=set();metadata_count=0;metadata_bytes=0
 def add(source,relative,archive=False):
  nonlocal metadata_count,metadata_bytes
  source=Path(source);s=source.lstat();need(stat.S_ISREG(s.st_mode),'Selected publication source is not regular')
  destination=DEST+relative;need(destination not in destinations and '..' not in Path(relative).parts and not Path(relative).is_absolute(),'Unsafe or duplicate publication destination')
  need(source!=PRIVATE/'ORIGINAL_COMPARISON_PART4.tar.gz','Private profile-containing part4 forbidden')
  if not archive:
   raw=source.read_bytes();need(not inspect(raw),'Unrelated complete profile in auxiliary publication metadata: '+relative)
   metadata_count+=1;metadata_bytes+=len(raw)
  files.append({'source_path':str(source),'destination':destination,'bytes':s.st_size,'sha256':digest(source)})
  need(statkey(source.lstat())==statkey(s),'Publication source changed while pinning')
  destinations.add(destination)
 parts=receipt['parts'];need([x['part'] for x in parts]==[1,2,3,4,5],'Five exact ordered logical parts required')
 for row in parts:
  i=row['part'];expected=a.public_root/'PUBLIC_COMPARISON_PART4.tar.gz' if i==4 else PRIVATE/f'ORIGINAL_COMPARISON_PART{i}.tar.gz'
  need(Path(row['source_path'])==expected and row['public_name']==f'PUBLIC_COMPARISON_PART{i}.tar.gz','Unexpected PUBLIC archive source')
  need(expected.stat().st_size==row['bytes'] and digest(expected)==row['sha256'],'PUBLIC archive actual bytes/hash changed')
  add(expected,'archives/'+row['public_name'],archive=True)
 # All small PUBLIC output metadata includes exact scope/scanner/0-1-0 receipts, bounded request and both peers.
 for root,dirs,names in os.walk(a.public_root,followlinks=False):
  for name in dirs:need(not (Path(root)/name).is_symlink(),'PUBLIC metadata symlink forbidden')
  for name in sorted(names):
   q=Path(root)/name
   if q==a.public_root/'PUBLIC_COMPARISON_PART4.tar.gz':continue
   need(not name.endswith('.tar.gz'),'Unexpected extra archive in PUBLIC output')
   add(q,'public-collection/'+q.relative_to(a.public_root).as_posix())
 # Inventory includes the one excluded auxiliary leaf only as path/size/hash; it never contains response payload.
 for name in ['RESULT.json','ORIGINAL_INVENTORY.json','ORIGINAL_PARTS.json','ORIGINAL_RESULT.json','BOUND_REQUEST.json','COLLECTOR.py.txt','INDEPENDENT_STATIC_PEER.json','INVENTORY_PREPARER.py.txt']+[f'PART{i}_BUDGET.json' for i in range(1,6)]:
  add(PRIVATE/name,'private-collection-original-metadata/'+name)
 for source,prefix in [('/workspace/geo323-F9-SHM-collection-actual-20261025','private-collection-actual'),('/workspace/geo323-F9-SHM-collection-actual-peer-xv28ou_f','private-collection-actual-peer')]:
  for q in sorted(Path(source).iterdir()):
   if q.is_file():add(q,prefix+'/'+q.name)
 oldlaunch=OWN/'geo323-F9-comparison-collection-root-launch-20261025'
 for root,dirs,names in os.walk(oldlaunch,followlinks=False):
  for name in dirs:need(not (Path(root)/name).is_symlink(),'Original root CLI directory symlink forbidden')
  for name in sorted(names):
   q=Path(root)/name;add(q,'private-collection-original-root-cli/'+q.relative_to(oldlaunch).as_posix())
 add(Path('/workspace/geo323-F9-comparison-SHM-collection-EXEC_FINAL-20261025.json'),'private-collection-original-root-host/EXEC_FINAL.json')
 add(Path('/workspace/launch_geo323_F9_comparison_collection_shm_root_20261025.py'),'private-collection-original-root-host/LAUNCHER.py.txt')
 for root,dirs,names in os.walk(a.collection_launch,followlinks=False):
  for name in dirs:need(not (Path(root)/name).is_symlink(),'Root CLI directory symlink forbidden')
  for name in sorted(names):
   q=Path(root)/name;add(q,'public-collection-root-cli/'+q.relative_to(a.collection_launch).as_posix())
 add(a.host_final,'public-collection-root-host/EXEC_FINAL.json')
 add(a.launch_script,'public-collection-root-host/LAUNCHER.py.txt')
 add(Path(__file__),'publication/prepare_publication_manifest.py')
 add(HERE/'PUBLICATION_DRAFT.md','publication/PROGRESS_DRAFT.md')
 # This inventory is a publisher input only. Root owns expected-parent, normal push and remote verification.
 result={'schema':'geo337-PUBLIC-comparison-publication-input/1','source_sha':F,'background_evidence_sha':'70d00309d7985db722c339c77331c436d26a7ab1','publisher_expected_parent':'ROOT_MUST_BIND_CURRENT_HEAD','files':files,
         'archive_count':5,'metadata_count':metadata_count,'metadata_bytes':metadata_bytes,
         'auxiliary_profile_full_response_public':False,'formal_comparison_all_raw_in_archives':True,
         'public_full_authority_input_replay_self_contained':False,'private_complete_archives_unchanged':True,
         'subject_rerun':False,'performance_rerun':False,'published':False,'remote_hash_verified':False,'delivered':False}
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'manifest':str(a.out),'sha256':digest(a.out),'files':len(files),'archive_count':5,'metadata_count':metadata_count,'metadata_bytes':metadata_bytes,'published':False}))
if __name__=='__main__':main()
