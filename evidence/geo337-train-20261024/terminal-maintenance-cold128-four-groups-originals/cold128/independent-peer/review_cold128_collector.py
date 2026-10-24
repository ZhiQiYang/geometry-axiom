from pathlib import Path
import ast,hashlib,json
P=Path('/workspace/collect_cold128_originals_20261024.py');OLD=Path('/workspace/collect_cold59_and_cardref_originals_20261024.py');O=Path('/workspace/train337-canvas-peer-resume');checks=0;find=[]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ck(v,n):
 global checks
 checks+=1
 if not v:find.append(n)
s=P.read_text();old=OLD.read_text();a=ast.parse(s);b=ast.parse(old)
ck(h(P)=='ecf974c68609a926c57d52da43e3d1fa12dd0366a12b6cd0d45a119feab5a153','fixed collector')
ck(h(OLD)=='e4b0056a2dc08a5b1900f26abbeb7644726464a5a75d77b8a0fb226051a0c1b5','fixed original collector')
for name in ['digest','readj','dump','add','tree']:
 x=next(x for x in ast.walk(a) if isinstance(x,ast.FunctionDef) and x.name==name);y=next(x for x in ast.walk(b) if isinstance(x,ast.FunctionDef) and x.name==name);ck(ast.dump(x)==ast.dump(y),'original helper unchanged '+name)
start=' with tarfile.open(archive,\'w:gz\',compresslevel=1) as tar:';end=' result=dict('
ck(s[s.index(start):s.index(end)]==old[old.index(start):old.index(end)],'original entire tar/roundtrip/after-hash block unchanged')
for fragment in ["OUT=Path('/workspace/cold128-originals-20261024')","850b38009a13d79321a0de06b316fac85249889a531f6105056c9e712289ccfe","assert len(items)==128 and sum(i['expected_allocated_saving'] for i in items)==150953984","r['exit_code']==0 and r['all_three_paths_and_bytes_preserved'] and a['actual_process_returncode']==0","tree(plan.parent,'preparation/'+name);tree(out,'actual/'+name);tree(outer,'launch/'+name)","add('/workspace/cold128-root-sequential-execution-20261024.json','root-sequential-execution.json')","'COLD128_ACTUAL_SUMMARY_HELPER_PEER.json'","'COLD128_ROOT_WRAPPER_STATIC_PEER.json'","total<64*1024*1024","all_established_cold_alias_groups=423","configured_gross_source_block_saving=150953984"]:ck(fragment in s,'exact collection scope '+fragment[:60])
ck("tree('/workspace/cardref" not in s and 'actual_cold212' not in s,'no duplicate cardref/prior actual collection')
ck("43759f9d932eb66581fc3aad6a94e936e4c6334355c5e7fb56cc359646e0ab7d" in s and h('/workspace/cold59-and-cardref-links-originals-20261024/PACKAGE.json')=='43759f9d932eb66581fc3aad6a94e936e4c6334355c5e7fb56cc359646e0ab7d','prior original tree package reference exact')
ck('configured_gross_source_block_saving' in s and 'not net storage recovery' in s and 'not a hard bound' in s,'capacity estimates not actual net claims')
ck('no independent c387 environment/stream capture' in s and 'direct exec_command' in s,'selector provenance limitation preserved')
ck('subprocess' not in s and 'os.system' not in s and 'unlink(' not in s and 'rmtree(' not in s and 'os.link' not in s,'no subject/maintenance/delete action in collector')
r={'schema':'cold128-original-collector-static-peer-v1','checks':checks,'exit_code':int(bool(find)),'findings':find,'collector_sha256':h(P),'original_collector_sha256':h(OLD),'scope':'128 completed maintenance groups only, exact original small metadata/streams; includes root sequential JSON, all original tools/peers, net plan and metadata census.','limits':['No collector run, no large payload hash or subject execution by reviewer. Root authorized collection must still finish real roundtrip before package pass.','423 is total reserved cold groups, not a claim this batch revalidated all423. Cardref2 groups are separate, already published, and not recollected.','384 preserved receipt bodies excluded. Historical full Git-tree payload referenced via pinned prior package rather than duplicated.','No independent c387 outer exists for original selector; its transcript provenance states that limitation.']}
p=O/'COLD128_COLLECTOR_STATIC_PEER.json';p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':h(p),'checks':checks,'exit_code':r['exit_code'],'findings':find}));raise SystemExit(r['exit_code'])
