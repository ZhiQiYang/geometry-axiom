"""Read existing PUBLIC collection only; validate part4 stream delta and original identities without any product run."""
from pathlib import Path
import argparse,gzip,hashlib,json,tarfile,time
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
PRIVATE=OWN/'geo323-F9-owner-comparison-terminal-package-shm-v2-20261025'
F='4f8a794f4167c3562eb182045102e86e9e37cca9'
EX='comparison/tools-frozen/authority/connected-user/subcommands/000001/stdout.bin'
EXHASH='b8939b00b88600ac7c4e96dcb45f38d75ffa5b5eddf7a3fa3f24d8109f6d9f29'

def h(b):return hashlib.sha256(b).hexdigest()
def digest(p):
 z=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):z.update(b)
 return z.hexdigest()
def J(p):return json.loads(p.read_bytes())
def fullstream(f):
 z=hashlib.sha256();n=0
 for b in iter(lambda:f.read(1024*1024),b''):z.update(b);n+=len(b)
 return n,z.hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--public-root',type=Path,required=True);p.add_argument('--launch',type=Path,required=True);p.add_argument('--host-final',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 count=0;bindings={}
 def check(v,msg):
  nonlocal count
  count+=1
  if not v:raise RuntimeError(msg)
 def bind(path):
  row={'path':str(path),'bytes':path.stat().st_size,'sha256':digest(path)};bindings[str(path)]=row;return row
 check(a.public_root.parent==OWN and a.launch.parent==OWN and not OWN.is_symlink() and OWN.resolve()==OWN,'Fixed approved SHM roots')
 check(a.out.parent==Path('/workspace') and not a.out.exists(),'Fresh small WS review directory')
 private_raw=PRIVATE/'RESULT.json';check(digest(private_raw)=='3e657ca399ad833d714c00e8ce0bf37739cbd5dc9d955adbd1c4a4925438febd','Private original RESULT unchanged');old=J(private_raw);bind(private_raw)
 resultpath=a.public_root/'RESULT.json';result=J(resultpath);bind(resultpath)
 check(result['collection_exit']==0 and result['source_sha']==F and result['errors']==[],'Actual PUBLIC terminal0/F9')
 check(result['private_complete_bundle_mutated'] is False and result['subject_rerun'] is False and result['performance_rerun'] is False,'No private/product/perf mutation claim')
 check(result['selected_members']==4666 and result['selected_regular_files']==4662 and result['selected_symlinks']==4 and result['selected_regular_bytes']==19843056,'Exact PUBLIC scope')
 check(result['excluded_auxiliary_profile_members']==1 and result['excluded_auxiliary_profile_bytes']==2795 and result['all_formal_comparison_commands_preserved']==712 and result['formal_O2_trace_commands']==700,'Exact exclusion and formal command preservation')
 check(result['all_auxiliary_API_raw_public'] is False and result['public_full_authority_input_replay_self_contained'] is False,'Auxiliary privacy/replay limit remains explicit')
 check(result['published'] is False and result['remote_hash_verified'] is False and result['delivered'] is False and result['storage_is_volatile'] is True,'Volatile collection not remote delivery')
 check([x['part'] for x in result['parts']]==[1,2,3,4,5],'Five exact logical parts')
 for row,original in zip(result['parts'],old['parts']):
  i=row['part'];oldpath=PRIVATE/f'ORIGINAL_COMPARISON_PART{i}.tar.gz'
  check(oldpath.stat().st_size==original['archive_bytes'] and digest(oldpath)==original['archive_sha256'],'Original archive bytes/hash unchanged');bind(oldpath)
  expected=a.public_root/'PUBLIC_COMPARISON_PART4.tar.gz' if i==4 else oldpath
  check(Path(row['source_path'])==expected and row['public_name']==f'PUBLIC_COMPARISON_PART{i}.tar.gz','Public source mapping')
  check(expected.stat().st_size==row['bytes'] and digest(expected)==row['sha256'],'Actual public archive hash')
  check(row['reused_original_bytes']==(i!=4) and row['roundtrip_executed_this_run']==(i==4),'Reuse not relabeled as new roundtrip')
 archive=a.public_root/'PUBLIC_COMPARISON_PART4.tar.gz';bind(archive)
 with tarfile.open(PRIVATE/'ORIGINAL_COMPARISON_PART4.tar.gz','r:gz') as original,tarfile.open(archive,'r:gz') as public:
  oldmembers=original.getmembers();newmembers=public.getmembers();check(len(oldmembers)==32 and len(newmembers)==31,'Original32 to PUBLIC31 members')
  check([m.name for m in newmembers]==[m.name for m in oldmembers if m.name!=EX],'Only exact named auxiliary profile excluded, original order preserved')
  excluded=[m for m in oldmembers if m.name==EX];check(len(excluded)==1,'Single original excluded profile')
  with original.extractfile(excluded[0]) as f:n,z=fullstream(f)
  check(n==2795 and z==EXHASH,'Exact excluded original raw identity')
  lookup={m.name:m for m in oldmembers};total=0
  for member in newmembers:
   before=lookup[member.name]
   check((member.type,member.mode,member.mtime,member.uid,member.gid,member.uname,member.gname,member.linkname,member.size)==(before.type,before.mode,before.mtime,before.uid,before.gid,before.uname,before.gname,before.linkname,before.size),'Member metadata preserved')
   if member.issym():
    check(member.linkname==before.linkname and member.size==before.size==0,'Literal ELF symlink preserved without dereference')
   else:
    check(member.isfile() and not member.islnk(),'Part4 regular member type')
    with original.extractfile(before) as f:oldsize,oldhash=fullstream(f)
    with public.extractfile(member) as f:newsize,newhash=fullstream(f)
    check((oldsize,oldhash)==(newsize,newhash) and newsize==member.size,'Every retained PUBLIC regular fullbytes/hash')
    total+=newsize
  check(total==6429790,'Exact retained part4 bytes')
 with gzip.open(archive,'rb') as f:decompressed,_=fullstream(f)
 check(result['public_part4_gzip_crc_verified'] is True and decompressed==result['public_part4_decompressed_tar_bytes'],'Full gzip EOF/trailer/CRC valid')
 budget=J(a.public_root/'PUBLIC_PART4_BUDGET.json');bind(a.public_root/'PUBLIC_PART4_BUDGET.json')
 check(budget['admitted'] is True and budget['reserve_bytes']==64*1024*1024 and budget['metadata_bytes']==2*1024*1024 and budget['fresh_output_free']>=budget['required_fresh_bytes'],'Original fresh worst-case budget admitted')
 check(archive.stat().st_size<=budget['gzip_upper_bytes'] and decompressed<=budget['tar_upper_bytes'],'Actual tar/gzip respects upper')
 manifest=J(a.public_root/'metadata/PUBLIC_METADATA_MANIFEST.json')
 for row in manifest['files']:
  q=a.public_root/'metadata'/row['relative_path'];check(q.stat().st_size==row['bytes'] and digest(q)==row['sha256'],'All fixed PUBLIC metadata original bytes/hash')
 launch=J(a.launch/'RESULT.json');bind(a.launch/'RESULT.json');check(launch['exit_code']==0,'Root collection launch0')
 commands=J(a.launch/'subcommands.json');check(len(commands)==1,'Single original collection command')
 command=commands[0];folder=Path(command['directory']);check(folder==a.launch/'subcommands/000001','Original capture directory exact')
 request=J(folder/'request.json');terminal=J(folder/'result.json')
 check(terminal['actual_process_returncode']==command['actual_process_returncode']==0 and terminal['timeout_expired'] is False,'Actual captured terminal0/no timeout')
 check(request['command']==terminal['command']==command['command'],'Exact original command argv')
 for stream in ['stdout','stderr']:
  q=folder/(stream+'.bin');raw=q.read_bytes();check(len(raw)==terminal[stream+'_bytes'] and h(raw)==terminal[stream+'_sha256']==command[stream+'_sha256'],'Original complete CLI stream bytes/hash');bind(q)
 check(h((folder/'stdin.bin').read_bytes())==terminal['stdin_sha256']==command['stdin_sha256'],'Original complete CLI stdin hash')
 for name in ['request.json','result.json','stdin.bin']:bind(folder/name)
 host=J(a.host_final);bind(a.host_final)
 check(digest(a.host_final)=='c22a1520d99ee284c66f0dd1c8d8f6eebe62c4d7e69af1c0c3c0d8cacf298533' and host['source_sha']==F,'Exact original wrapped host identity')
 check(type(host['actual_tool_result']['exit_code']) is int and host['actual_tool_result']['exit_code']==0 and 'session_id' not in host['actual_tool_result'],'True completed host tool final0')
 host_output=json.loads(host['actual_tool_result']['output'])
 check(host_output['exit_code']==0 and host_output['source_sha']==F and host_output['package_result']==str(resultpath) and host_output['subject_rerun'] is False,'Original host launcher summary matches exact PUBLIC output')
 check(digest(private_raw)=='3e657ca399ad833d714c00e8ce0bf37739cbd5dc9d955adbd1c4a4925438febd','Private receipt unchanged after review')
 a.out.mkdir();report={'schema':'geo323-PUBLIC-comparison-collection-actual/1','source_sha':F,'exit_code':0,'checks':count,'bindings':bindings,
 'original_private_bundle_unchanged':True,'historical_original_R8_outer_exit_from_immutable_private_bundle':1,'original_R8_live_files_not_reread':True,'public_part4_retained_members_verified':31,'public_part4_regular_members_fullbytes_verified':28,'public_part4_literal_ELF_symlinks_verified':3,'excluded_auxiliary_profile_members':1,
 'reused_parts_full_archive_hash_verified':[1,2,3,5],'reused_parts_roundtrip_repeated':False,'all_formal_comparison_commands_retained':712,
 'full_auxiliary_API_raw_public':False,'authority_full_input_replay_publicly_self_contained':False,'subject_rerun':False,'performance_rerun':False,
 'storage_is_volatile':True,'published':False,'remote_hash_verified':False,'delivered':False,'reviewed_epoch':time.time(),'checker_sha256':digest(Path(__file__)),'prior_checker_attempt':{'path':'/workspace/geo323-F9-PUBLIC-actual-read-original-20261025/RESULT.json','exit_code':1,'cause':'v1 read top-level exit_code but original host uses actual_tool_result.exit_code; original failure kept, collector/product not rerun'}}
 (a.out/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'report':str(a.out/'REVIEW.json'),'sha256':digest(a.out/'REVIEW.json'),'exit_code':0,'checks':count,'bytes':(a.out/'REVIEW.json').stat().st_size}))
if __name__=='__main__':main()
