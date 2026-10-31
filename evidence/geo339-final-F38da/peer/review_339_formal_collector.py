import ast,hashlib,json
from pathlib import Path
B=Path('/workspace/geo339-F38da-startup-20261024');O=Path('/workspace/train337-canvas-peer-resume');checks=0;findings=[]
def ck(v,l):
 global checks
 checks+=1
 if not v:findings.append(l)
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
w=(B/'run_reviewed_affected_formal.py').read_text();c=(B/'collect_terminal_affected_formal.py').read_text();ast.parse(w);ast.parse(c)
ck(h(B/'collect_terminal_affected_formal.py')=='739101e5321c0c2e0032b4060355b36bfef3769da987a3386b7b52277ba08e56','collector exact pin')
ck("'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'" in w and "'6e32c6d04f07d8c239aae013d816dc22d6858707fbceca6d0183f353039fdee9'" in w,'capture and original five argv manifest pinned')
a=ast.parse(w);literal={}
for n in a.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
  try:literal[n.targets[0].id]=ast.literal_eval(n.value)
  except ValueError:pass
req=json.loads((B/'COMMANDS.json').read_text());ck(len(req['launchOriginalCommands'])==len(literal['pins'])==5,'five frozen original commands')
for argv,pin in zip(req['launchOriginalCommands'],literal['pins']):ck(h(argv[2])==pin,'original tool pin '+Path(argv[2]).name)
ck("material['exitCode'] == 0 and not material['errors'] and material['cleanFinalHEAD'] == F" in w,'successful exact source materialization before subject')
ck("row, stdout, stderr = rec.run(argv, cwd='/workspace', timeout=None, check=False," in w and "exitCode=0 if all(row['actual_process_returncode'] == 0 for row in rec.rows) else 1" in w,'unmodified original argv; continue independent red; true all-five aggregate exit')
ck("'outerTimeout': None" in w and "'PYTHONOPTIMIZE'" in w and "env.pop(key, None)" in w,'no extra timeout or optimization weakening')
ck("need(not DEST.exists()" in c and "outer['completeFiveCommands'] is True" in c and "type(outer['exitCode']) is int" in c,'fresh archive and actual terminal required')
ck("type(predicate['exitCode']) is int" in c and "type(value['exitCode']) is int" in c and "value.get('endedUTC')" in c,'all original receipt terminal including red')
ck("predicate['checkoutBefore']['status'] == predicate['checkoutAfter']['status'] == ''" in c and "after['head'] == F and after['porcelain'] == ''" in c and "['inputsEqualBefore'] is True" in c and "['indexEqualBefore'] is True" in c,'original closed source and input/index guards')
ck("for path in sorted(root.rglob('*'))" in c and "read(directory / 'result.json') == row" in c and "row['stdin_sha256']" in c,'whole eight original roots and complete exposed capture streams')
ck("if elf:" in c and "excluded.append(row)" in c and 'unlink(' not in c and 'rmtree(' not in c,'ELF body archive exclusion only, no original deletion')
ck("'original_group_exits': {name: value['exitCode']" in c and "'predicate_exit': predicate['exitCode']" in c and "'outer_exit': outer['exitCode']" in c,'summary preserves all original exits')
ck("not aggregate native, six browsers, ledger, or architecture" in c and "Source-preparation first four commands correctly record priorM" in c,'scope and original source variants honest')
ck("need(seen == set(expected) | {'RAW_INVENTORY.json'}" in c and "hfile(Path(row['source_path'])) == row['sha256']" in c,'exact unique member set and original-byte roundtrip')
ck(not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any(v.name.startswith(('subprocess','importlib')) for v in n.names) for n in ast.walk(ast.parse(c))),'collector does not import execution modules; literal explanatory subprocess word is not execution')
report={'schema':'geo339-frozen-formal-wrapper-and-terminal-collector-static-peer/1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'wrapper_sha256':h(B/'run_reviewed_affected_formal.py'),'collector_sha256':h(B/'collect_terminal_affected_formal.py'),'limitations':['Static wrapper/collector review only; no subject run and no current claim about 142/142 or predicates. Actual terminal package requires separate raw verification.','The original inner driver and root scheduler own exclusive/heavy-slot policy; outer wrapper does not add a lock or threshold.']};p=O/'GEO339_FORMAL_COLLECTOR_STATIC_PEER.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':checks,'exit_code':report['exit_code'],'findings':findings,'path':str(p),'sha256':h(p)}));raise SystemExit(report['exit_code'])
