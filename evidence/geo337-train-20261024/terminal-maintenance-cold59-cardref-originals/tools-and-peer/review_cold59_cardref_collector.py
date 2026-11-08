from pathlib import Path
import ast,hashlib,json
N=Path('/workspace/collect_cold59_and_cardref_originals_20261024.py');OLD=Path('/workspace/collect_cold212_and_sevenfinal15_originals_20261024.py');O=Path('/workspace/train337-canvas-peer-resume/COLD59_CARDREF_COLLECTOR_STATIC_PEER.json')
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def ck(n,v):checks.append((n,bool(v)))
ck('new fixed final collector',h(N)=='e4b0056a2dc08a5b1900f26abbeb7644726464a5a75d77b8a0fb226051a0c1b5')
ck('original collector exact',h(OLD)=='526219f78a90c4cd95193e596fed52ce12be928150e0c5c9045b4e3fad0a8c3f')
nt=ast.parse(N.read_text());ot=ast.parse(OLD.read_text());nm=next(x for x in nt.body if isinstance(x,ast.FunctionDef) and x.name=='main');om=next(x for x in ot.body if isinstance(x,ast.FunctionDef) and x.name=='main')
for name in ['digest','readj','dump']:
 a=next(x for x in nt.body if isinstance(x,ast.FunctionDef) and x.name==name);b=next(x for x in ot.body if isinstance(x,ast.FunctionDef) and x.name==name);ck('same original helper '+name,ast.dump(a)==ast.dump(b))
for name in ['add','tree']:
 a=next(x for x in nm.body if isinstance(x,ast.FunctionDef) and x.name==name);b=next(x for x in om.body if isinstance(x,ast.FunctionDef) and x.name==name);ck('same original guarded collector '+name,ast.dump(a)==ast.dump(b))
nw=[x for x in nm.body if isinstance(x,ast.With)];ow=[x for x in om.body if isinstance(x,ast.With)];ck('same original tar write and full roundtrip AST',len(nw)==len(ow)==2 and all(ast.dump(a)==ast.dump(b) for a,b in zip(nw,ow)))
t=N.read_text()
ck('one exact59 manifest pin',"cold_text_59_exact_body_manifest_20261024.json','482ad13ed12a4029dc4e79c6ab084ad034521abba16d073d74818178fb82f602'" in t and 'assert len(items)==59' in t and '==286375936' in t)
ck('each59 original terminal guards',"r['exit_code']==0 and r['all_three_paths_and_bytes_preserved'] and a['actual_process_returncode']==0" in t)
ck('cardref exact63/116/53 plan',"'d8c7d397aa041080c3b98fadb242069abd12b301d19475fb1c2aa3b4cb08ea58'" in t and "p['target_count']==63 and p['original_elf_count']==116 and p['excluded_unique_elf_count']==53" in t)
ck('original inventories hash-bound only',"for key in ['original_inventory','original_excluded_inventory','terminal_receipt']" in t and "assert digest(x['path'])==x['sha256']" in t)
ck('review helper and initial schema-error originals kept',all(x in t for x in ['review_cold59_actual_summary.py','COLD59_ACTUAL_SUMMARY_HELPER_PEER.json','COLD59_SCOPE_INITIAL_SCHEMA_ERROR.json','review_cold59_immutable_scope.v1.py.txt']))
ck('requires actual peers true zero before tar',"assert r['exit_code']==0 and not r['findings']" in t and t.index("assert r['exit_code']==0 and not r['findings']")<t.index("with tarfile.open(archive,'w:gz'"))
ck('64MiB cap before tar',"assert total<64*1024*1024" in t)
ck('original sources rehashed after roundtrip',"assert all(digest(x['source'])==x['sha256'] for x in entries.values())" in t)
ck('separate295cold/2cardref alias reservations','all_established_cold_alias_groups=295' in t and 'cardref_elf_alias_groups_added=2' in t and 'separate from the295 cold groups' in t)
ck('no product/fullbody claim','Maintenance only; no product gate' in t and 'No actual receipt body or ELF executable bytes duplicated' in t and 'references their exact inventory and does not duplicate them' in t)
ck('collector cannot execute subject',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ['run','Popen','system','unlink','remove','replace','link'] for n in ast.walk(nt)))
findings=[n for n,v in checks if not v];r={'schema':'independent-cold59-cardref-collector-static-peer-v1','checks':len(checks),'exit_code':int(bool(findings)),'findings':findings,'collector_sha256':h(N),'original_collector_sha256':h(OLD),'scope':'Static exact collection-only adaptation; no collection or subject executed by reviewer. Actual package requires separate byte roundtrip peer.','limits':['Original output must be terminal and original actual peers0; missing prerequisite files must fail.','Scope contains59 exact cold operations plus closed cardref preparation/execution metadata, not the cold receipt bodies or116 ELF payloads.','Original tar lookup implementation is retained; no product assertion, threshold or source modified.']}
O.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(O),'sha256':h(O),'checks':len(checks),'findings':findings,'exit_code':r['exit_code']}));raise SystemExit(r['exit_code'])
