"""Stage A only: preserve 26 exact old index/ELF payloads; never unlink."""
from pathlib import Path
import argparse,datetime,gzip,hashlib,importlib.util,json,os,sys
HERE=Path(__file__).parent
COMMON_PIN='d11e9dd829a0a0d53386943556b55bd0f6721eb12301534e875ce485202409b5'
COMMON=HERE/'exact_common.py'
def H(raw):return hashlib.sha256(raw).hexdigest()
if H(COMMON.read_bytes())!=COMMON_PIN:raise RuntimeError('exact common helper pin')
spec=importlib.util.spec_from_file_location('native_tmp_exact_common',COMMON)
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--request',type=Path,required=True);parser.add_argument('--request-sha256',required=True);parser.add_argument('--execute-archive',action='store_true');args=parser.parse_args()
    c.need(not sys.flags.optimize,'PYTHONOPTIMIZE forbidden')
    raw=args.request.read_bytes();c.need(H(raw)==args.request_sha256,'request pin');q=json.loads(raw)
    plan,source,indexes,elfs,chrome=c.read_plan()
    if not args.execute_archive:
        print(json.dumps(dict(executed=False,stage='archive-only',payload_leaves=26,originals_removed=False,plan_sha256=c.PLAN_PIN)));return 0
    c.bind_request(q,'independent_archive_executor_peer',Path(__file__))
    c.need(q['root_shared_SHM_capacity_lease'] is True,'root SHM scheduler lease')
    out=Path(q['out']);c.need(out==c.OWN/'native-TMP-preservation-20261025' and out.resolve()==out and not out.exists(),'exact fresh approved SHM archive destination')
    c.need(c.OWN.is_dir() and not c.OWN.is_symlink(),'existing exact OWN root')
    cap=c.load(c.original.CAP,c.original.CAP_PIN,'original_capture')
    guard=c.load(c.original.GUARD,c.original.GUARD_PIN,'original_consumer')
    env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None)
    payloads=[dict(path=x['effective_index'],kind='private-index',original_state=x['original_state']) for x in indexes]+[dict(x,kind='old-ELF') for x in elfs]
    c.need(len(payloads)==26,'exact payload count')
    raw_bytes=sum(x['original_state']['bytes'] for x in payloads)
    gzip_upper=raw_bytes+(raw_bytes//16383+1)*5+26*100
    manifest_bytes=sum(p['bytes'] for p in plan['bindings'].values())
    required=raw_bytes+gzip_upper+2*manifest_bytes+8*1024**2+64*1024**2
    with c.leases():
        free=os.statvfs(c.OWN);free_bytes=free.f_bavail*free.f_frsize;own_bytes=c.owned_allocated()
        c.need(free_bytes>=required and own_bytes+required<=2*1024**3,'fresh actual SHM preservation budget')
        out.mkdir(mode=0o700);rec=cap.Recorder(out/'commands',env,q['task_sha'])
        result=dict(schema='native-TMP-exact-preservation/1',exit_code=1,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=c.PLAN_PIN,request_sha256=args.request_sha256,executor_sha256=H(Path(__file__).read_bytes()),common_sha256=COMMON_PIN,originals_removed=False,formal_executed=False,remote_delivered=False,archives=[],commands=rec.rows,resource_before=dict(SHM_available_bytes=free_bytes,combined_OWN_allocated_bytes=own_bytes,planned_increment_bytes=required,original_raw_bytes=raw_bytes,gzip_upper_reference_bytes=gzip_upper,manifest_reference_bytes=manifest_bytes,reserve_bytes=64*1024**2))
        paths=c.group_paths(source,indexes,elfs,chrome)
        try:
            (out/'REQUEST.json').write_bytes(raw);(out/'EXECUTOR.py').write_bytes(Path(__file__).read_bytes());(out/'COMMON.py').write_bytes(COMMON.read_bytes());(out/'PLAN.json').write_bytes(c.PLAN.read_bytes())
            c.consumers(out,'before',guard,paths)
            before=c.source_state(rec)
            for item in indexes:c.private_index_state(rec,item)
            c.chrome_namespace(chrome)
            for item in source:c.exact_file(Path(item['path']),item['original_state'],guard)
            for item in payloads:c.exact_file(Path(item['path']),item['original_state'],guard)
            for group in chrome:
                for item in group['files']:c.exact_file(Path(group['path'])/item['relative'],item['original_state'],guard)
            prerequisites=out/'original-prerequisites';prerequisites.mkdir();prerequisite_map=[]
            for number,(path,pin) in enumerate(plan['bindings'].items()):
                body=Path(path).read_bytes();c.need(len(body)==pin['bytes'] and H(body)==pin['sha256'],'original prerequisite drift')
                destination=prerequisites/(str(number).zfill(4)+'.bin')
                with destination.open('xb') as stream:stream.write(body);stream.flush();os.fsync(stream.fileno())
                prerequisite_map.append(dict(original_path=path,member=str(destination.relative_to(out)),**pin))
            c.dump(out/'PREREQUISITE_PATH_MAP.json',prerequisite_map);c.syncdir(prerequisites)
            raws=out/'original-payloads';packed=out/'gzip-payloads';raws.mkdir();packed.mkdir()
            for number,item in enumerate(payloads):
                c.consumers(out,'payload-'+str(number),guard,paths)
                body=c.exact_file(Path(item['path']),item['original_state'],guard)
                if item['kind']=='private-index':c.need(body[:4]==b'DIRC','original index header')
                else:c.need(body[:4]==b'\x7fELF','original ELF header')
                name=str(number).zfill(2);rawfile=raws/(name+'.bin');gzfile=packed/(name+'.gz')
                with rawfile.open('xb') as stream:os.chmod(rawfile,0o600);stream.write(body);stream.flush();os.fsync(stream.fileno())
                with gzfile.open('xb') as stream:
                    os.chmod(gzfile,0o600)
                    with gzip.GzipFile(filename='',mode='wb',fileobj=stream,mtime=0) as gz:gz.write(body)
                    stream.flush();os.fsync(stream.fileno())
                with gzip.open(gzfile,'rb') as stream:restored=stream.read()
                c.need(rawfile.read_bytes()==body==restored,'complete original raw/gzip roundtrip')
                c.need(c.exact_file(Path(item['path']),item['original_state'],guard)==body,'original payload changed while archived')
                result['archives'].append(dict(original_path=item['path'],kind=item['kind'],original_state=item['original_state'],raw_member=str(rawfile.relative_to(out)),raw_bytes=len(body),raw_sha256=H(body),gzip_member=str(gzfile.relative_to(out)),gzip_bytes=gzfile.stat().st_size,gzip_sha256=H(gzfile.read_bytes()),complete_roundtrip=True))
                c.syncdir(raws);c.syncdir(packed);c.save_mutable(out/'RESULT.json',result)
            c.consumers(out,'after',guard,paths)
            c.need(c.source_state(rec)==before,'original source status/HEAD/refs changed')
            for item in indexes:c.private_index_state(rec,item)
            for item in payloads:c.exact_file(Path(item['path']),item['original_state'],guard)
            c.need(len(result['archives'])==26,'all original payloads preserved')
            result.update(exit_code=0,all_26_original_payloads_still_present=True,archive_raw_bytes=raw_bytes,all_full_raw_and_gzip_roundtrips=True)
        except BaseException as error:
            result['error']=repr(error);raise
        finally:
            result['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();c.save_mutable(out/'RESULT.json',result);c.syncdir(out);c.syncdir(out.parent)
        print(json.dumps(dict(exit_code=0,out=str(out),originals_removed=False,remote_delivered=False,archive_raw_bytes=raw_bytes)))
    return 0

if __name__=='__main__':raise SystemExit(main())
