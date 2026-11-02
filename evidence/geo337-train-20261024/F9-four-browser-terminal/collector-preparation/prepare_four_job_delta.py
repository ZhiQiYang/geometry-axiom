"""Prepare the four-job scope delta; never import/execute the collector or read SHM."""
from pathlib import Path
import ast, difflib, hashlib, json
HERE=Path(__file__).parent
BASE=Path('/workspace/geo337-assembly-terminal-preparation-20261025/collect_assembly_terminal.py')
raw=BASE.read_bytes()
if hashlib.sha256(raw).hexdigest()!='ff1aae84cd00a73190f3d8e7c3623087d9965804ae6821d872487a2b42b01049':raise RuntimeError('original assembly tool changed')
s=raw.decode()
def replace(old,new):
 global s
 if s.count(old)!=1:raise RuntimeError('delta anchor not unique: '+old[:70])
 s=s.replace(old,new)
replace('"""Preserve both terminated F9 assembly attempts; root-approved SHM execution only."""','"""Preserve four named terminated F9 jobs; root-approved SHM execution only."""')
replace('META = 2 * 1024**2','META = 4 * 2 * 1024**2  # Four job inventories, retaining the original per-job metadata allowance.')
start=s.index('FINALS = {');end=s.index('\n}\n',start)+3
s=s[:start]+"JOBS = {'documents': ('d', 10), 'grid': ('g', 15), 'space': ('s', 15), 'timber': ('t', 20)}\n"+s[end:]
replace("attempts={'assembly':1, 'assembly-r2':0}","jobs=list(JOBS), terminal_pins='UNBOUND until four true host terminals exist'")
replace("q.get('both_attempts_closed_no_more_guard_writes')", "q.get('all_four_jobs_closed_no_more_guard_writes')")
replace("'root closed-attempt lease'","'root closed-four-job lease'")
replace("out.name.startswith('assembly-terminal-package-')","out.name.startswith('remaining-browser-terminal-package-')")
replace("schema='geo337-F9-assembly-two-attempt-full-package/1'","schema='geo337-F9-four-browser-full-package/1'")
replace("  for attempt, (finalpath, finalpin, code, storage_rel) in FINALS.items():\n   finalp = safe(finalpath); need(digest(finalp) == finalpin, 'true host final pin'); final = J(finalp); host = final['actual_tool_result']; hostout = json.loads(host['output'])",
"""  terminal_inputs=q['terminal_inputs']; need(set(terminal_inputs)==set(JOBS),'all four named terminal inputs')
  for attempt, (short, minutes) in JOBS.items():
   pins=terminal_inputs[attempt]; finalpin=pins['final_sha256']; finalpath=f'/workspace/geo337-F9-{attempt}-SHM-EXEC_FINAL-20261025.json'; storage_rel='r/'+short
   finalp = safe(finalpath); need(digest(finalp) == finalpin, 'true host final pin'); final = J(finalp); host = final['actual_tool_result']; hostout = json.loads(host['output'])
   code=host['exit_code']; need(type(code) is int, 'true host integer exit')""")
replace("wfpath = storage/'original/assembly/receipt.json'", "wfpath = storage/'original'/attempt/'receipt.json'")
replace("== wf['job'] == 'assembly'", "== wf['job'] == attempt")
replace("req['plan_dir'] == str(OWN/'plans/assembly') and req['source_layout'] == str(OWN/'sources/assembly')", "req['plan_dir'] == str(OWN/'plans'/attempt) and req['source_layout'] == str(OWN/'sources'/attempt)")
replace("'same shared source plan'","'exact isolated source plan'")
replace("wf['ci_timeout_minutes'] == 15", "wf['ci_timeout_minutes'] == minutes")
replace("Path(final['entry'].split()[-1])", "Path('/workspace/launch_geo337_F9_next_browser_root_20261025.py')")
replace("original_15minute_gate_exit=0", "original_ci_timeout_minutes=minutes, original_ci_gate_exit=0")
replace("historical_environment_failure=attempt=='assembly'", "historical_environment_failure=False")
start=s.index("  need(requests[0]['plan_sha256']");end=s.index("  sampler = Path(",start)
s=s[:start]+"""  for req in requests:
   job=req['job']; pins=terminal_inputs[job]; plan=OWN/'plans'/job
   need(req['plan_sha256']==digest(plan/'PLAN.json'),'original single-job plan identity')
   prep=req['source_preparation']; need(digest(safe(prep['path']))==prep['sha256'] and J(prep['path'])['actual_process_returncode']==0,'original materialization true zero')
   roots += [(f'sourceplan/{job}',plan,True),(f'source-materialization/{job}',OWN/'host'/(job+'-materialize'),False),(f'source-plan-generation/{job}',OWN/'host'/(job+'-plan'),False)]
   for phase in ['plan','materialize']:
    p=safe(f'/workspace/geo337-F9-{job}-SHM-{phase}-EXEC_FINAL-20261025.json')
    need(digest(p)==pins[phase+'_final_sha256'] and J(p)['exit_code']==0,'original preparation host terminal')
    extras[f'source-preparation/{job}/{phase}-EXEC_FINAL.json']=p
"""+s[end:]
start=s.index("  for name, p in [('first-attempt'");end=s.index('\n',start)
s=s[:start]+"  # Per-job actual peers are published as separate evidence leaves after collection, not invented here."+s[end:]
replace("schema='geo337-F9-assembly-complete-terminal-inventory/1'", "schema='geo337-F9-four-browser-complete-terminal-inventory/1'")
replace("All regular bytes and symlink targets of both launch/storage/sampler roots", "All regular bytes and symlink targets of four isolated launch/storage/sampler roots")
replace("ORIGINAL_ASSEMBLY_PART", "ORIGINAL_FOUR_BROWSER_PART")
replace("'actual metadata within fixed2MiB bound'", "'actual metadata within four original2MiB allowances'")
ast.parse(s)
out=HERE/'collect_four_browser_terminal.py'
if out.exists():raise RuntimeError('fresh generated draft required')
out.write_text(s)
(HERE/'ASSEMBLY_TO_FOUR_JOB.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),s.splitlines(True),fromfile=str(BASE),tofile=str(out))))
(HERE/'DELTA_PREPARATION.json').write_text(json.dumps({'state':'PREPARATION_ONLY','base_sha256':hashlib.sha256(raw).hexdigest(),'collector_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'collector_executed':False,'SHM_access':False,'product_rerun':False,'static_validation':'AST only','terminal_inputs':'UNBOUND; no accepted collection until all four true terminal files are pinned by root'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'prepared':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
