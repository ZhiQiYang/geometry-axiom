"""Review production storage-only command receipts without rereading archive bodies."""
from pathlib import Path
import hashlib,json
B=Path('/tmp/geo337-archive-object-store-root-20261024');O=Path('/workspace/root-archive-store-actual-peer-combined-20261024')
T=Path('/workspace/git-archive-object-store-tool-20261024/write_archive_blob.py');PIN='d4c9f40e41aac7e210a038f466f89945b8c21b68ffff9b6f44c2c6fed244d940'
checks=[]
def h(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def need(ok,label):checks.append({'label':label,'ok':bool(ok)})
def raw(r,k):return (Path(r['directory'])/(k+'.bin')).read_bytes()
summary=read(B/'RESULT.json');env=read(B/'ENVIRONMENT_SCOPE.json')
need(h(T.read_bytes())==PIN,'frozen independently reviewed current tool')
need(summary['exit']==0 and summary['root_head_unchanged']=='3df56ff38b450ad228da04b2c1dcb6511582af42','root invocation true result0 and fixed original HEAD')
need(summary['do_not_delete_git_objects'] and not summary['existing_objects_moved_or_deleted'] and not summary['refs_or_index_adopted'],'permanent new-only objects')
need(env['parent_environment_unchanged'] and not env['native_or_mutation_environment_changed'] and env['cleared_child_git_variable_names']==['GIT_PAGER'],'only child namespace sanitized')
allrows=[];scopes={}
for p in sorted(B.rglob('subcommands.json')):
    rows=read(p);scopes[str(p.relative_to(B))]=rows
    for i,r in enumerate(rows):
        label=str(p.relative_to(B))+':'+str(i+1);d=Path(r['directory'])
        need(read(d/'result.json')==r,'original terminal inventory '+label)
        req=read(d/'request.json')
        need(req['actual_process_returncode'] is None and all(r.get(k)==v for k,v in req.items()if k!='actual_process_returncode'),'original request preserved except terminal exit '+label)
        for k in ['stdin','stdout','stderr']:
            value=raw(r,k);need(h(value)==r[k+'_sha256'],'original raw hash '+label+' '+k)
            if k+'_bytes'in r:need(len(value)==r[k+'_bytes'],'original raw bytes '+label+' '+k)
        need(type(r['actual_process_returncode']) is int and not r['timeout_expired'],'actual non-timeout child '+label)
        need(not any(x in r['command'] for x in ['update-ref','update-index','commit','commit-tree','rebase','reset','gc','prune']),'no refs/index/history mutation '+label)
        allrows.append(r)
lease=Path(summary['lease']['path']);need(h(lease.read_bytes())==summary['lease']['sha256']=='556c513142d9559c9497bb118d12da5487ee61b80953ee27095e49269d7c0104','exact permanent lease')
ld=read(lease);need(ld['do_not_delete_git_objects'] and ld['not_a_rebuildable_cache'] and ld['original_objects']=='/workspace/geometry-axiom/.git/objects','lease prohibits cleanup and binds root store')
alt=Path('/workspace/geometry-axiom/.git/objects/info/alternates').read_bytes()
need(alt==(summary['protected_store']+'\n').encode() and h(alt)==summary['final_alternates_sha256'],'only exact store append from absent')
expected=[('r5','9c954153e22de99a03e74997a6b84b278d92f4d8',31186327,'caaf311a748c2ce1dc4ebd754fbebc9c4d70f59a5d0938fb2e9e34e57f2dd794'),('r6','7564a8d69361ebb305d3c4f9f9a28102f8f0d7e5',31317807,'a9113e5e8e3474da70ee21970a29d451a46e148a3abdde1cecded4c36631d3f1')]
previous=None
for label,oid,size,digest in expected:
    r=read(B/label/'RESULT.json');rows=scopes[label+'/commands/subcommands.json']
    need(r['exit_code']==0 and r['alternate_connected'] and r['status']=='new protected blob readable; refs/index untouched','actual new object completion '+label)
    need(r['before']==r['after'] and r['before']['head']==summary['root_head_unchanged'],'refs HEAD index snapshot unchanged '+label)
    need(r['object_oid']==oid and r['archive_identity']['bytes']==size and r['archive_identity']['sha256']==digest,'exact source archive binding '+label)
    need(r['permanent_lease']==summary['lease'] and r['store']==summary['protected_store'],'same permanent store '+label)
    need(r['global_git_environment_unchanged'] and not r['product_tests_run'],'environment/product gate untouched '+label)
    chain=r['planned_reader_graphs']['/workspace/geo300-capacity512-work-20261024']
    need([x['depth']for x in chain]==list(range(6)) and chain[-1]['path']==summary['protected_store'],'true planned fifth hop '+label)
    need(len(r['ordinary_readers'])==4 and '/workspace/geo300-capacity512-work-20261024'in r['ordinary_readers'],'four ordinary readers including348 '+label)
    for reader in r['ordinary_readers']:
        for flag,want in [('-t',b'blob\n'),('-s',(str(size)+'\n').encode())]:
            matching=[x for x in rows if x['cwd']==reader and x['command'][-3:]==['cat-file',flag,oid]]
            need(len(matching)==1 and matching[0]['actual_process_returncode']==0 and raw(matching[0],'stdout')==want,'actual ordinary reader '+label+' '+reader+' '+flag)
    writes=[x for x in rows if x['command'][:2]==['env','GIT_OBJECT_DIRECTORY='+summary['protected_store']]]
    need(len(writes)==1 and writes[0]['actual_process_returncode']==0 and raw(writes[0],'stdout')==(oid+'\n').encode(),'only command-local new blob writer '+label)
    for x in rows:
        code=x['actual_process_returncode']
        need(code==0 or (code==1 and x['command'][-3:]==['cat-file','-e',oid]),'only expected prewrite missing-object1 '+label)
    refs=[raw(x,'stdout')for x in rows if 'for-each-ref'in x['command']]
    need(len(refs)>=3 and all(x==refs[0]for x in refs),'actual refs original streams identical '+label)
    heads=[raw(x,'stdout').decode().strip()for x in rows if x['command'][-3:]==['rev-parse','--verify','HEAD']]
    need(len(heads)>=3 and all(x==summary['root_head_unchanged']for x in heads),'actual HEAD original streams identical '+label)
    loose=Path(summary['protected_store'])/oid[:2]/oid[2:];st=loose.stat();i=r['new_object_identity']
    need((st.st_size,st.st_dev,st.st_ino,st.st_mode,st.st_mtime_ns)==(i['bytes'],i['device'],i['inode'],i['mode'],i['mtime_ns']),'new loose metadata unchanged without reread '+label)
    if previous:need(r['prior_alternates_identity']==previous['final_alternates_sha256'] and r['before']==previous['after'],'sequential reuse original state '+label)
    else:need(r['prior_alternates_identity']=='absent' and (B/label/'alternates.before.bin').read_bytes()==b'' and (B/label/'alternates.appended.bin').read_bytes()==alt,'first actual atomic exact append')
    previous=r
outer=[r for rows in scopes.values()for r in rows if str(T)in r['command']]
need(len(outer)==2 and all(x['actual_process_returncode']==0 for x in outer),'two real outer tool invocations zero')
fail=[x for x in checks if not x['ok']];O.mkdir(exist_ok=False)
report={'checks':len(checks),'failed_checks':len(fail),'findings':fail,'tool_sha256':PIN,'original_commands':len(allrows),'root_result_sha256':h((B/'RESULT.json').read_bytes()),'lease_sha256':summary['lease']['sha256'],'scope':'Read-only full small original command streams and actual root/reader/lease/HEAD/refs/index metadata. No Git invocation, archive/loose-object body reread, compiler, performance or root ref mutation.','limits':['The reviewed d4c9 tool itself fully validated 62MB archive/header/GitOID/payload hashes during execution; this peer validates its complete recorded stream and final metadata, not a second independent62MB scan.','Actual publication of these blobs into commits and remote push is separate; this result certifies only preload and ordinary local readers.','Protected TMP store contains permanent Git data and must never be cache-cleaned.']}
(O/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(O/'CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False));raise SystemExit(bool(fail))
