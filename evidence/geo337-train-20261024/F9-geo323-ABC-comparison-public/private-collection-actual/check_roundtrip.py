"""Readonly SHM archive verification. Invoke only through approved require_escalated exec."""
from pathlib import Path, PurePosixPath
import datetime, gzip, hashlib, json, os, stat, tarfile, traceback

HERE=Path(__file__).resolve().parent
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
PACKAGE=OWN/'geo323-F9-owner-comparison-terminal-package-shm-v2-20261025'
LAUNCH=OWN/'geo323-F9-comparison-collection-root-launch-20261025'
HOST=Path('/workspace/geo323-F9-comparison-SHM-collection-EXEC_FINAL-20261025.json')
F='4f8a794f4167c3562eb182045102e86e9e37cca9'
CPIN='9a1a6d673b7ade12bbe49480e8e646cd7d919619015749b34ab30ebc4401aae9'
IPIN='1ab22f16962fb861204932c4c46ff379c9c1e6144d9b7006999ded216a0f416f'
PPIN='14f6ddb9cb1358f93125d86f3dc8b716400fa16e2a62e9d6b9007d5e35745143'
RPIN='96cdb61eadb05a6bff9f98c2d8a8d1a5d5424f7c366aed590c9403f69c908bfc'
PEER='5d67bf327477915bc4e2a4d98a89238f87d798fdc1294f49c0a1bca08830e3b3'
R={'schema':'geo323-SHM-collection-actual-readonly/1','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'source_sha':F,'checks':0,'failures':[],'pins':[],'parts':[],
   'SHM_access_requires':'formal exec_command require_escalated auto_review',
   'SHM_writes_by_reviewer':False,'archive_recollected':False,'product_rerun':False,
   'storage_is_volatile':True,'published':False,'remote_hash_verified':False,'delivered':False}

def need(v,msg):
    R['checks']+=1
    if not v:raise RuntimeError(msg)

def sha(raw):return hashlib.sha256(raw).hexdigest()
def raw(p):return Path(p).read_bytes()
def load(p):return json.loads(raw(p))
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def pin(p):
    p=Path(p);row={'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)};R['pins'].append(row);return row
def state(p):
    s=p.lstat();return [s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_nlink]

def run():
    need(PACKAGE.parent==OWN and not OWN.is_symlink() and OWN.resolve()==OWN,'Wrong SHM OWN parent')
    collection=load(PACKAGE/'RESULT.json');launch=load(LAUNCH/'RESULT.json');host=load(HOST)
    need(host['exit_code']==launch['original_exit']==collection['collection_exit']==0,'Host/launch/collector actual exit not all zero')
    need(launch['source_sha']==collection['source_sha']==F,'Source SHA mismatch')
    need(launch['storage_is_volatile'] is True and launch['published'] is False,'Volatile state mislabeled as published')
    need(collection['errors']==[] and len(collection['parts'])==5,'Incomplete/red five-part collection')
    need(collection['collector_sha256']==CPIN and collection['inventory_sha256']==IPIN
         and collection['parts_sha256']==PPIN and collection['inventory_result_sha256']==RPIN
         and collection['peer_sha256']==PEER,'Collector/input/peer identity mismatch')
    for name,expected in [('COLLECTOR.py.txt',CPIN),('ORIGINAL_INVENTORY.json',IPIN),
                          ('ORIGINAL_PARTS.json',PPIN),('ORIGINAL_RESULT.json',RPIN),
                          ('INDEPENDENT_STATIC_PEER.json',PEER)]:
        need(pin(PACKAGE/name)['sha256']==expected,'Copied pinned metadata changed: '+name)
    need(digest(PACKAGE/'INVENTORY_PREPARER.py.txt')==load(PACKAGE/'ORIGINAL_RESULT.json')['prepare_sha256'],
         'Original inventory preparer identity changed')
    request=load(PACKAGE/'BOUND_REQUEST.json');peer=load(PACKAGE/'INDEPENDENT_STATIC_PEER.json')
    need(request['execute'] is True and request['root_execution_lease'] is True and request['out']==str(PACKAGE),
         'Missing exact root execution lease/out')
    for name,expected in [('collector_sha256',CPIN),('inventory_sha256',IPIN),('parts_sha256',PPIN)]:
        need(request[name]==peer[name]==expected,'Root request/accepted peer binding mismatch')
    need(peer['exit_code']==0 and request['independent_peer']['sha256']==PEER,'Independent peer not accepted')
    command=launch['capture_result'];directory=Path(command['directory'])
    need(directory==LAUNCH/'subcommands/000001','Unexpected original command receipt path')
    actual=load(directory/'result.json');initial=load(directory/'request.json')
    need(actual==command,'Capture wrapper/actual command result differ')
    need(all(actual.get(k)==v for k,v in initial.items() if k!='actual_process_returncode'),
         'Original request/result differs outside initial null returncode')
    need(initial['actual_process_returncode'] is None and actual['actual_process_returncode']==0
         and actual['timeout_expired'] is False,'Original command terminal missing')
    need(actual['source_sha']==actual['acceptance_sha']==F and actual['environment']['PYTHONOPTIMIZE'] is None,
         'Original command source/env mismatch')
    need(raw(directory/'stdin.bin')==b'' and actual['stdin_sha256']==sha(b''),'Unexpected original stdin')
    streams={}
    for stream in ['stdout','stderr']:
        b=raw(directory/(stream+'.bin'));streams[stream]=b
        need(len(b)==actual[stream+'_bytes'] and sha(b)==actual[stream+'_sha256'],'Original full CLI stream/hash mismatch')
        pin(directory/(stream+'.bin'))
    need(streams['stderr']==b'','Original collector stderr is not empty')
    events=[json.loads(line) for line in streams['stdout'].splitlines()]
    need(events[-1]==collection,'Original stdout final result differs from stored collector terminal')
    need([x['part'] for x in events[:-1] if x.get('event')=='part-budget']==[1,2,3,4,5], 'Original stdout missing ordered five budget events')
    need([x['part'] for x in events[:-1] if x.get('event')=='part-complete']==[1,2,3,4,5], 'Original stdout missing ordered five completed parts')
    request_file=Path(actual['command'][actual['command'].index('--request')+1])
    need(raw(request_file)==raw(PACKAGE/'BOUND_REQUEST.json'),'Original executed request bytes changed')
    need(digest(actual['command'][2])==CPIN and '--execute' in actual['command'],'Original executed collector changed')
    inv=load(PACKAGE/'ORIGINAL_INVENTORY.json');parts=load(PACKAGE/'ORIGINAL_PARTS.json')
    roots=inv['roots'];index={}
    for packed in inv['records']:
        ri,rel,kind,size,h,st,target=packed;name=roots[ri]['prefix']+'/'+rel
        need(not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts and name not in index,
             'Unsafe or duplicate inventory member')
        index[name]={'source':Path(roots[ri]['source_root'])/rel,'type':kind,'bytes':size,'sha256':h,'state':st,'target':target}
    flat=[n for part in parts for n in part['members_exact']]
    need(len(parts)==5 and len(flat)==len(set(flat))==len(index)==4667 and set(flat)==set(index),
         'Five-part scope is not exact once 4,667 members')
    source_regular=source_links=0
    # This is a readonly verification of preserved source files, not recollection.
    for name,row in index.items():
        p=row['source'];need(state(p)==row['state'],'Original source lstat changed: '+name)
        if row['type']=='regular':
            need(stat.S_ISREG(p.lstat().st_mode) and digest(p)==row['sha256'],'Original regular raw/hash changed: '+name)
            source_regular+=1
        else:
            need(row['type']=='symlink' and p.is_symlink() and os.readlink(p)==row['target']
                 and sha(os.fsencode(os.readlink(p)))==row['sha256'],'Original literal ELF symlink changed: '+name)
            source_links+=1
    need(source_regular==4663 and source_links==4,'Source regular/link totals wrong')
    seen=[];regular=links=logical=compressed=0
    for spec,reported in zip(parts,collection['parts']):
        number=spec['part'];archive=PACKAGE/f'ORIGINAL_COMPARISON_PART{number}.tar.gz'
        need(reported['part']==number and reported['archive_path']==str(archive),'Archive role/path mismatch')
        need(pin(archive)['sha256']==reported['archive_sha256'] and archive.stat().st_size==reported['archive_bytes'],
             'Archive complete raw hash/size mismatch')
        budget=load(PACKAGE/f'PART{number}_BUDGET.json')
        n=spec['logical_regular_bytes']+4096*spec['members']+11264
        overhead=(n+4095)//4096+(n+16383)//16384+(n+33554431)//33554432+1024
        required=n+overhead+64*1024*1024+2*1024*1024
        need(spec['tar_upper_bytes']==n and spec['gzip_upper_bytes']==n+overhead
             and spec['required_fresh_bytes']==required,'Wrong complete tar/gzip/reserve upper bound')
        need(budget['required_bytes']==required and budget['fresh_output_free']>=required
             and budget['admitted'] is True and budget['compression_ratio_assumed'] is False,
             'Original part was not admitted with full worst bound')
        need(reported['fresh_free_after']>=64*1024*1024 and reported['roundtrip_complete'] is True,
             'Original part reserve/roundtrip did not pass')
        need(archive.stat().st_size<=spec['gzip_upper_bytes'],'Actual archive exceeds full gzip upper bound')
        # Consume complete gzip stream to validate CRC/trailer, then inspect all tar members without extracting.
        gzip_bytes=0
        with gzip.open(archive,'rb') as gz:
            for b in iter(lambda:gz.read(1024*1024),b''):gzip_bytes+=len(b)
        need(gzip_bytes<=spec['tar_upper_bytes'],'Actual full decompressed tar exceeds upper bound')
        part_regular=part_links=part_bytes=0
        with tarfile.open(archive,'r:gz') as tar:
            members=tar.getmembers()
            need([m.name for m in members]==spec['members_exact'],'Original archive ordered member scope mismatch')
            for m in members:
                row=index[m.name];seen.append(m.name)
                need(m.mode==row['state'][2]&0o777 and m.mtime==row['state'][4]//1000000000,
                     'Tar original mode/mtime changed')
                if row['type']=='symlink':
                    need(m.issym() and m.linkname==row['target'] and m.size==0,'ELF link was dereferenced or altered')
                    part_links+=1
                else:
                    need(m.isfile() and not m.islnk() and not m.issym() and m.size==row['bytes'],'Regular tar member type/size changed')
                    f=tar.extractfile(m);need(f is not None,'Missing member stream');hh=hashlib.sha256();count=0
                    with f:
                        for b in iter(lambda:f.read(1024*1024),b''):hh.update(b);count+=len(b)
                    need(count==row['bytes'] and hh.hexdigest()==row['sha256'],'Complete tar member raw/hash mismatch')
                    part_regular+=1;part_bytes+=count
        need(part_bytes==reported['logical_regular_bytes']==spec['logical_regular_bytes'] and len(members)==reported['members'],
             'Original per-part totals differ')
        regular+=part_regular;links+=part_links;logical+=part_bytes;compressed+=archive.stat().st_size
        R['parts'].append({'part':number,'archive_sha256':reported['archive_sha256'],'archive_bytes':archive.stat().st_size,
                           'members':len(members),'regular_files':part_regular,'symlinks':part_links,'regular_bytes':part_bytes,
                           'gzip_crc_and_trailer_verified':True,'decompressed_tar_bytes':gzip_bytes,
                           'full_member_hashes_verified':True,'original_fresh_free':budget['fresh_output_free'],
                           'required_fresh_bytes':required,'original_free_after':reported['fresh_free_after']})
        pin(PACKAGE/f'PART{number}_BUDGET.json')
    need(seen==flat and len(seen)==len(set(seen)),'Complete tar roundtrip member duplication/omission')
    need(regular==collection['regular_files']==4663 and links==collection['symlinks']==4
         and logical==collection['regular_bytes']==19845851,'Full original roundtrip totals wrong')
    original_names=[n for n in index if n.startswith('comparison/')]
    need(sum(index[n]['type']=='regular' for n in original_names)==4645
         and sum(index[n]['type']=='symlink' for n in original_names)==4,'Original raw comparison scope incomplete')
    need(collection['metadata_upper_bytes']<=2*1024*1024 and collection['final_free']>=64*1024*1024,'Original metadata/reserve cap failed')
    need(collection['subject_rerun'] is False and collection['performance_rerun'] is False
         and collection['original_R8_outer_exit_unchanged']==1,'Scope or historical R8 red misrepresented')
    for p in [PACKAGE/'RESULT.json',LAUNCH/'RESULT.json',HOST,PACKAGE/'BOUND_REQUEST.json',directory/'request.json',directory/'result.json']:
        pin(p)
    R.update(actual_host_exit=0,actual_launch_exit=0,actual_collection_exit=0,regular_files=regular,symlinks=links,
             logical_regular_bytes=logical,total_archive_bytes=compressed,all_4667_members_exact_once=True,
             all_original_source_hashes_and_stats_unchanged=True,original_comparison_regular_files=4645,
             original_R8_outer_exit_unchanged=1,metadata_upper_bytes=collection['metadata_upper_bytes'],
             original_final_free=collection['final_free'],output_device=PACKAGE.stat().st_dev,
             limits=['All SHM access used formally approved require_escalated exec; no symlink workaround.',
                     'This verifies volatile local archives, not publication or remote hash.',
                     'No extraction, recollection, source deletion, ELF dereference, C or performance execution.',
                     'no_source_or_git_objects_copied in collector means product checkout/Git payload; executed toolkit sources are intentionally included.'])

if __name__=='__main__':
    try:run()
    except BaseException as e:
        R['failures'].append({'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()});traceback.print_exc()
    R['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();R['exit_code']=int(bool(R['failures']))
    R['checker_sha256']=digest(__file__)
    dest=HERE/'RESULT.json'
    if dest.exists():raise RuntimeError('Do not overwrite original actual verification')
    dest.write_text(json.dumps(R,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'exit_code':R['exit_code'],'checks':R['checks'],'result_sha256':digest(dest),'failures':R['failures']},ensure_ascii=False))
    raise SystemExit(R['exit_code'])
