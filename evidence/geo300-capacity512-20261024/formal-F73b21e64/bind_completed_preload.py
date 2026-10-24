"""Bind completed preload receipts and already-reviewed documents; no Git writes."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;B=Path('/tmp/geo348-original-archives-preload-20261024')
PREFIX='evidence/geo300-capacity512-20261024/formal-F73b21e64/'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((P/'FILE_ALLOWLIST_UNBOUND.json').read_bytes());completed=json.loads((B/'RESULT.json').read_bytes())
assert completed['exit']==0 and completed['parent_environment_unchanged']
assert json.loads((B/'EXEC_COMPLETION.json').read_bytes())['exit_code']==0
def add(p,rel):
 p=Path(p);assert p.is_file()and not p.is_symlink();m['files'].append({'local':str(p),'relative':PREFIX+rel,'bytes':p.stat().st_size,'sha256':h(p),'archive_preload_required':False})
for p in sorted(B.rglob('*')):
 if p.is_file():add(p,'storage-preload/'+p.relative_to(B).as_posix())
add(P/'preload_archives.py','storage-preload/preload_archives.py')
add(P/'prepare_file_allowlist.py','prepare_file_allowlist.py')
add(Path(__file__),'bind_completed_preload.py')
add('/workspace/geo348-F73-publication-doc-peer-specials-20261024/REVIEW.json','independent-peers/F73/CURRENT_DOC_REVIEW.json')
doc=json.loads(Path('/workspace/geo348-F73-publication-doc-peer-specials-20261024/REVIEW.json').read_bytes())
assert doc['failed']==0 and doc['body_sha256']==h(P/'PR_BODY.template.md') and doc['progress_sha256']==h(P/'PROGRESS.md')
preloads={}
for phase in completed['phases']:
 r=json.loads(Path(phase['tool_result']).read_bytes());assert phase['actual_exit']==r['exit_code']==0 and r['before']==r['after'] and r['global_git_environment_unchanged']
 a=r['archive_identity'];matches=[x for x in m['files']if x['archive_preload_required']and x['sha256']==a['sha256']and x['bytes']==a['bytes']];assert len(matches)==1
 preloads[matches[0]['relative']]={'oid':r['object_oid'],'bytes':a['bytes'],'sha256':a['sha256'],'receipt':phase['tool_result']}
assert len(preloads)==2
m.update(status='READY: original archive preloads completed; final publisher still requires fresh guards',
 preloaded_archives=preloads,permanent_store_lease={'path':'/tmp/geo337-published-archive-git-objects-20261024/info/CODEX_PERMANENT_OBJECTS.json','sha256':'556c513142d9559c9497bb118d12da5487ee61b80953ee27095e49269d7c0104'},
 root_alternates={'path':'/workspace/geometry-axiom/.git/objects/info/alternates','sha256':'e4003887d478e946abfb1c76daa861b688d1c37d936f510a73fd833fbf48b7be'})
m['payload_bytes']=sum(x['bytes']for x in m['files']);m['nonarchive_bytes']=sum(x['bytes']for x in m['files']if not x['archive_preload_required'])
m['publication_min_free_bytes']=2*m['nonarchive_bytes']+16*1024*1024
m['publication_budget_basis']='Two full nonarchive payload allowances plus16MiB for owned index/tree/raw metadata. Archive26,458,248B already resides in permanent TMP Git store; each ordinary writer must prove no primary duplicate. This is a publication resource estimate, not a measured peak or product threshold.'
assert len({x['relative']for x in m['files']})==len(m['files'])
target=P/'READY_MANIFEST.json';assert not target.exists();target.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
s=(P/'publish_draft.py').read_text();old="READY_MANIFEST_SHA256='UNBOUND_DO_NOT_EXECUTE'";assert s.count(old)==1
bound=P/'publish_bound.py';assert not bound.exists();bound.write_text(s.replace(old,"READY_MANIFEST_SHA256='"+h(target)+"'"))
print(json.dumps({'manifest':str(target),'manifest_sha256':h(target),'publisher':str(bound),'publisher_sha256':h(bound),'payload_bytes':m['payload_bytes'],'nonarchive_bytes':m['nonarchive_bytes'],'publication_min_free_bytes':m['publication_min_free_bytes'],'files':len(m['files']),'runtime':'UNRUN'},ensure_ascii=False))
