from pathlib import Path
import ast,hashlib,json
O=Path('/workspace/train337-canvas-peer-resume');P=Path('/workspace/collect_visual_nested_tmp_stdout_alias_originals_20261024.py');OLD=Path('/workspace/collect_root_eleven_archive_extensions_originals_20261024.py');checks=0;findings=[]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ck(v,n):
 global checks
 checks+=1
 if not v:findings.append(n)
s=P.read_text();old=OLD.read_text();ck(h(P)=='42731aa4a5b39436ce7a7084acb5c3dd681e2dddbeadac2f2c1a1f32c85e1020','fixed finalcollector')
def functions(src):return {n.name:ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(src)) if isinstance(n,ast.FunctionDef)}
a=functions(s);b=functions(old)
for n in ['digest','readj','dump','add','tree']:ck(a[n]==b[n],'exact previous function '+n)
start=' with tarfile.open(archive,\'w:gz\',compresslevel=1) as tar:';end=' result=dict(schema='
ck(s[s.index(start):s.index(end)]==old[old.index(start):old.index(end)],'all original tar/re-read/source guard bytes unchanged')
tree=ast.parse(s);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');specs=ast.literal_eval(next(n.value for n in main.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='specs' for t in n.targets)))
ck([(x[0],*x[4:]) for x in specs]==[('visual21',21,147,101842944),('nested8',8,56,50405376),('tmp3',3,14,523485184),('rawpairs2',2,4,31252480)],'four exact known scopes and configured gross figures')
allpaths=set()
for label,prep,actual,outer,groups,paths,saving in specs:
 p=json.loads((Path(prep)/'PLAN.json').read_bytes());r=json.loads((Path(actual)/'RESULT.json').read_bytes());o=json.loads((Path(outer)/'RESULT.json').read_bytes());members=[x['path'] for g in p['groups']for x in g['members']]
 ck(len(p['groups'])==groups and len(members)==paths and p['expected_allocated_saving']==saving,'exact selected scope '+label)
 ck(r['exit_code']==o['actual_process_returncode']==0 and not o['timeout_expired'] and r['plan_sha256']==h(Path(prep)/'PLAN.json'),'true completed preservation '+label)
 ck(r['all_original_payload_paths_retained'] and r['all_original_receipt_bytes_preserved'],'original path/receipt retention '+label);allpaths.update(members)
ck(len(allpaths)==221 and sum(x[-1]for x in specs)==706985984,'221 distinct payloadpaths excluded; total configured only')
for text in ["assert not archive_bodies.intersection(x['source'] for x in entries.values())","assert total<64*1024*1024","assert len(plan['groups'])==group_count and len(members)==target_count and plan['expected_allocated_saving']==saving","assert not a['timeout_expired'] and r['plan_sha256']==digest(prep/'PLAN.json')","v['source_sha']==t['source_sha'] and v['stages']==t['stages']","peer['exit_code']==0 and not peer['findings']"]:ck(text in s,'original guards '+text)
for name in ['VISUAL21_NESTED8_STATIC_ACTUAL_METADATA_PEER.json','TMP_THREE_ARCHIVE_STATIC_ACTUAL_METADATA_PEER.json','R5_R6_ARCHIVE_STDOUT_PAIRS_STATIC_ACTUAL_PEER.json']:
 q=json.loads((O/name).read_bytes());ck(q['exit_code']==0 and not q['findings'] and name in s,'actual independent peer bound '+name)
for name in ['VISUAL21_NESTED8_INITIAL_ARCHIVE_SUFFIX_ASSUMPTION.json','review_visual21_nested8_actual.initial-suffix.py.txt','R5_R6_STDOUT_PAIRS_REVIEW_INITIAL_ARGV_ASSUMPTION.json','review_r5_r6_archive_stdout_pairs_actual.initial-argv.py.txt']:
 ck((O/name).is_file() and name in s,'original reviewer failure history included '+name)
ck('prepare_r5_r6_two_archive_stdout_pairs_20261024.py.initial-stdin-assumption.txt'in s,'original producer assumption failure preserved')
ck(not any(x in s for x in ['subprocess.','unlink(','os.link(','os.replace(','shutil.rmtree','chmod(']),'collector performs no product/mutation/deletion/link actions')
report={'schema':'four-alias-scopes-original-metadata-collector-static-peer-v1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'collector_sha256':h(P),'previous_collector_sha256':h(OLD),'group_counts':[21,8,3,2],'preserved_path_counts':[147,56,14,4],'configured_gross_bytes':706985984,'limits':['Static small tools/plans/existing terminal receipts only. No packing or payload hash by reviewer.','All221 PNG/nested archive/TMP archive/raw stdout bodies are excluded from metadata archive while retaining every original path and byte.','Original failed reviewer/producer records retained; no failed product gate changes. Actual collector outer and independent package peer remain separate post-package attachments.','Shared heavy-slot scheduling and root resource reservation remain required for actual compression.']}
q=O/'FOUR_SCOPE_ALIAS_COLLECTOR_STATIC_PEER.json';q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q),'checks':checks,'exit_code':report['exit_code'],'findings':findings}));raise SystemExit(report['exit_code'])
