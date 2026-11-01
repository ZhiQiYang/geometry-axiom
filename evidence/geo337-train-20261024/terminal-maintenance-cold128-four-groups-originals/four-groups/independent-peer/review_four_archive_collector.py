from pathlib import Path
import ast,hashlib,json
P=Path('/workspace/collect_four_archive_groups_originals_combined_20261024.py');OLD=Path('/workspace/collect_cold128_originals_20261024.py');O=Path('/workspace/train337-canvas-peer-resume');s=P.read_text();old=OLD.read_text();checks=0;find=[]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ck(v,n):
 global checks
 checks+=1
 if not v:find.append(n)
ck(h(P)=='778c03422749422fb2b522f7562920edc1f52bb8705ae5de3ff220d5f44e29da','fixed final collector')
ck(h(OLD)=='ecf974c68609a926c57d52da43e3d1fa12dd0366a12b6cd0d45a119feab5a153','fixed original128collector')
a=ast.parse(s);b=ast.parse(old)
for name in ['add','tree']:
 one=next(n for n in ast.walk(a) if isinstance(n,ast.FunctionDef) and n.name==name);two=next(n for n in ast.walk(b) if isinstance(n,ast.FunctionDef) and n.name==name);ck(ast.dump(one)==ast.dump(two),'exact original '+name+' AST')
start=' with tarfile.open(archive,\'w:gz\',compresslevel=1) as tar:';end=" assert all(digest(x['source'])==x['sha256'] for x in entries.values())"
ck(s[s.index(start):s.index(end)+len(end)]==old[old.index(start):old.index(end)+len(end)],'exact original all bytes/tar/fullroundtrip/recheck block')
for phrase in ["r['plan_sha256']==digest(prep/'PLAN.json')","r['exit_code']==0 and r['all_original_payload_paths_retained'] and r['all_original_receipt_bytes_preserved'] and a['actual_process_returncode']==0","assert not a['timeout_expired']","assert gross==476540928","assert len(plans[0]['members'])==6 and [g['count'] for g in plans[1]['groups']]==[7,4,2]","assert readj(t['path'])==t['original_rows']","assert not archive_bodies.intersection(x['source'] for x in entries.values())","assert total<64*1024*1024","THREE_LARGE_ARCHIVE_GROUPS_ACTUAL_METADATA_PEER.json","review_three_large_archive_groups_actual.py","Original423 cold groups,2 cardref ELF groups,1 six-alias group and3 large archive groups","Original6alias publication exits1/1/1/0","Original prep producers ran via direct exec","F2perf source-counterfactual excluded"]:ck(phrase in s,'scope/guard/provenance '+phrase[:65])
ck('unlink(' not in s and 'os.replace' not in s and 'subprocess' not in s,'collector read-only subject/maintenance sources')
ck("'original-collector.py'" in s and "'collector.py'" in s and "Independent post-package peer is adjacent" in s,'full original tools and no self-reference')
ck("s.st_size<4*1024*1024" in s and "('.tar.gz','.zip','.exe','.pyc')" in s,'no large archive/ELF bodies admitted')
r={'schema':'four-archive-groups-collector-static-peer-v1','checks':checks,'exit_code':int(bool(find)),'findings':find,'collector_sha256':h(P),'original_collector_sha256':h(OLD),'limits':['Only static exact original add/tree/tar-recheck comparison and narrow scope/guard audit; collector not executed by reviewer.','Actual small package still needs independent member/hash review after execution; no archive bodies or maintenance subjects rerun.','Original historical red outcomes and direct-prep-no-outer limitation retained.']};q=O/'FOUR_ARCHIVE_GROUPS_COLLECTOR_STATIC_PEER.json';q.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q),'checks':checks,'exit_code':r['exit_code'],'findings':find}));raise SystemExit(r['exit_code'])
