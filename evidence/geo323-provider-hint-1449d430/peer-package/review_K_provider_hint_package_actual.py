from pathlib import Path
import fcntl,hashlib,json,tarfile
O=Path('/workspace/train337-canvas-peer-resume');H=Path('/tmp/geo323-provider-hint-publication-20261024');B=H/'package';S='1449d430d1c4734bb1bc3a9f91f3851c845cc0f3';checks=0;findings=[]
def h(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(Path(p).read_bytes())
def ck(v,n):
 global checks
 checks+=1
 if not v:findings.append(n)
held=None
for name in ['/tmp/g261r3/heavy.lock','/tmp/g261r3/secondary.lock']:
 f=Path(name).open('a+b')
 try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);held=f;break
 except BlockingIOError:f.close()
if held is None:raise RuntimeError('Both original heavy slots busy; no package read started, no wait/retry.')
try:
 summary=j(B/'SUMMARY.json');idx=j(B/'RAW_INDEX.json');plan=j(H/'PACKAGE_PLAN.json');rows=idx['files'];meta={r['archive']:r for r in rows};local={r['local']:r for r in rows};archive=Path(summary['archive']['path'])
 ck(summary['exit']==0 and summary['roundtrip'] and summary['original_bytes_unchanged'] and not summary['originals_deleted'] and not summary['product_tests_reexecuted'],'actual completed single collection no test rerun')
 ck(summary['source_sha']==idx['source_sha']==plan['source_sha']==S,'fixed final public source')
 ck(len(rows)==len(meta)==idx['count']==summary['archive']['members']==3201,'complete unique3201members')
 ck(sum(r['bytes']for r in rows)==idx['logical_bytes']==summary['logical_bytes']==34272208,'all34272208original bytes')
 ck(archive.stat().st_size==summary['archive']['bytes']==6289014 and h(archive.read_bytes())==summary['archive']['sha256']=='5b9d327d7f009ae3d305a0c4e3c44c94d2c7391647996dd4eae3300af0c6c4cd','single exact tar hash')
 ck([{k:v for k,v in r.items() if k!='sha256'}for r in rows]==plan['files'],'exact immutable preparation membership')
 seen=[];objects={}
 with tarfile.open(archive,'r|gz') as tf:
  for m in tf:
   ck(m.isfile() and m.name in meta and not Path(m.name).is_absolute() and '..'not in Path(m.name).parts,'safe known regular member '+m.name);seen.append(m.name)
   x=meta[m.name];data=tf.extractfile(m).read();ck(len(data)==m.size==x['bytes'] and h(data)==x['sha256'],'complete member bytes '+m.name)
   source=Path(x['local']);ck(source.is_file() and not source.is_symlink() and source.stat().st_size==x['bytes'] and h(source.read_bytes())==x['sha256'],'unchanged original exact member '+m.name)
   if m.name.endswith('.json'):
    try:objects[m.name]=json.loads(data)
    except(ValueError,UnicodeError):pass
 ck(seen==[r['archive']for r in rows],'complete tar membership and original order')
 for name,pin in [('peer-train/K_PROVIDER_HINT_PUBLIC_SOURCE_ACTUAL_PEER.json','a05e5b9e944a6f9ef8f6c3efb68a851c624dff728ee154774d2d58f3f0bf3503'),('peer-train/K_PROVIDER_HINT_FULL18_ACTUAL_PEER.json','068621e6c00c6606f0d81b6f9d86ec4606f5a7d42f969a6491185d2e48455aee')]:
  ck(meta[name]['sha256']==pin and objects[name]['exit_code']==0 and not objects[name]['findings'],'actual independent peer retained '+name)
 r=objects['source-index-formal/RESULT.json'];ck(r['exit']==0 and r['source_sha']==S and r['original_methods']==18 and r['skips']==0 and r['actual_native_commands']==51 and r['actual_compile_link_commands']==66,'original full18 actual unchanged')
 o=objects['source-index-formal/observed/receipt.json'];ck(o['original_exit']==0 and o['observer_complete'] and not o['observation_errors'],'complete original117 observed flows')
 for c in o['commands']:
  for k in ['stdout','stderr']:
   x=c[k];item=local.get(x['path']);ck(item is not None and item['sha256']==x['sha256'] and item['bytes']==x['bytes'],'original command stream present '+str(c['number'])+'/'+k)
  if 'actual_executable'in c:
   x=c['actual_executable'];item=local.get(x['retained']);ck(item is not None and item['sha256']==x['sha256'] and item['bytes']==x['bytes'],'executed ELF retained in same archive')
 ck(objects['alignment-environment-stop/RESULT.json']['exit']==1 and objects['alignment-environment-stop/RESULT.json']['commands']==[],'original environment stop1 preserved')
 ck(objects['source-publication-S81/RESULT.json']['source_sha']=='81b6c388f8b73e9aaf885b1d948e5f306b77bafd' and objects['alignment-publication-S144/RESULT.json']['source_sha']==S,'original source provenance never relabeled')
 ck(objects['related-formal/RESULT.json']['source_sha']==S,'related formal actual source S')
 ck('peer-train/K_PROVIDER_HINT_SOURCE_PEER_INITIAL_LITERAL_ERROR.json'in objects and objects['peer-train/K_PROVIDER_HINT_SOURCE_PEER_INITIAL_LITERAL_ERROR.json']['exit_code']==1,'initial reviewer literal error retained')
 ck(not any('/.git/'in r['local'] or '/.git/'in r['archive']for r in rows),'no Git objects packaged')
 report={'schema':'K-provider-hint-single-original-package-actual-peer-v1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'source_sha':S,'summary_sha256':h((B/'SUMMARY.json').read_bytes()),'raw_index_sha256':h((B/'RAW_INDEX.json').read_bytes()),'archive_sha256':summary['archive']['sha256'],'archive_bytes':6289014,'members':3201,'logical_bytes':34272208,'limits':['One original archive including actual executed ELF snapshots,103 nested C/header snapshots, source-publication/shadow/formal original streams, and peer error history. No new subject or timing run.','Formal18 actual1579/0 and source708/0 pins match; related24 correctness raw is included but its independent actual peer is separately supplied by specials, not invented here.','Package SUMMARY/RAW_INDEX, collection top tool completion, later independent package/related peer and publisher are post-package attachments; do not falsely claim recursively included.','Product source remains S144 while evidence head advances. Original F2bbe R6 compare and performance reds are not overridden.']}
 q=O/'K_PROVIDER_HINT_SINGLE_PACKAGE_ACTUAL_PEER.json';q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q.read_bytes()),'checks':checks,'exit_code':report['exit_code'],'findings':findings}));code=report['exit_code']
finally:
 fcntl.flock(held,fcntl.LOCK_UN);held.close()
raise SystemExit(code)
