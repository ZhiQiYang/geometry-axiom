"""Preserve genuine red terminal receipts without treating collection as acceptance."""
from pathlib import Path
import ast, difflib, hashlib, json
HERE=Path(__file__).parent
base=HERE/'collect_four_browser_terminal.py';raw=base.read_bytes()
if hashlib.sha256(raw).hexdigest()!='fee55afbf8fc480704c94478bc0572e070661eab28c7e2e10d79051707818c69':raise RuntimeError('exact initial draft')
s=raw.decode()
def replace(old,new):
 global s
 if s.count(old)!=1:raise RuntimeError('nonunique delta: '+old[:80])
 s=s.replace(old,new)
replace("need(host['exit_code'] == hostout['wrapper_exit'] == hostout['original_process_returncode'] == sr['wrapper_exit'] == sr['original_process_returncode'] == wr['wrapper_exit'] == wr['original_primary_exit'] == wf['exit_code'] == code, 'true terminal exit chain')",
"need(host['exit_code'] == hostout['wrapper_exit'] == hostout['original_process_returncode'] == sr['wrapper_exit'] == sr['original_process_returncode'] == wr['wrapper_exit'] == code, 'true host/sampler/launcher exit chain')\n   primary=wf['exit_code']; need(type(primary) is int and wr['original_primary_exit']==primary, 'true original workflow exit preserved independently')")
replace("need(sr['sampling_complete'] is True and hostout['sampling_complete'] is True and sr['original_receipt_sha256'] == digest(launch/'receipt.json') and wr['original_receipt_sha256'] == digest(wfpath), 'closed sampler and workflow receipt bindings')",
"need(type(sr['sampling_complete']) is bool and hostout['sampling_complete']==sr['sampling_complete'] and sr['original_receipt_sha256'] == digest(launch/'receipt.json') and wr['original_receipt_sha256'] == digest(wfpath), 'closed sampler and workflow receipt bindings; sampling failures preserved')")
replace("need(wf['ci_timeout_minutes'] == minutes and wf['watchdog_factor'] == 3 and wf['over_ci_timeout'] is False and wf['checkout_before'] == wf['checkout_after'], 'unchanged original timing and checkout guards')",
"need(wf['ci_timeout_minutes'] == minutes and wf['watchdog_factor'] == 3 and type(wf['over_ci_timeout']) is bool, 'unchanged original time definitions; actual gate result preserved')")
replace("need(wr[phase]['actual_process_returncode'] == 0 and wr[phase]['timeout_expired'] is False, 'closed original source guard')",
"need(type(wr[phase]['actual_process_returncode']) is int and type(wr[phase]['timeout_expired']) is bool, 'closed original source guard; original red preserved')")
replace("done[0]['primary_returncode'] == code", "done[0]['primary_returncode'] == primary")
replace("wr['original_command']['actual_process_returncode'] == code", "wr['original_command']['actual_process_returncode'] == primary")
replace("original_formal_exit=code", "original_formal_exit=primary")
replace("original_ci_gate_exit=0", "original_ci_gate_exit=1 if wf['over_ci_timeout'] else 0")
replace("historical_environment_failure=False", "failure_classification='not inferred by collector', sampling_complete=sr['sampling_complete'], checkout_before_after_equal=wf['checkout_before']==wf['checkout_after'], guard_exits={phase:wr[phase]['actual_process_returncode'] for phase in ['before_guard','after_guard']}")
replace("  for attempt, (short, minutes) in JOBS.items():",
"""  # Refuse an incomplete attempt list rather than silently omit a later environment retry.
  for job in JOBS:
   expected={job+'.json',job+'-sampled.json'}
   actual={p.name for p in (OWN/'requests').iterdir() if p.name.startswith(job) and p.suffix=='.json'}
   need(actual==expected,'unexpected additional attempt requires explicit reviewed scope: '+job)
  for attempt, (short, minutes) in JOBS.items():""")
ast.parse(s);out=HERE/'collect_four_browser_terminal_v2.py'
if out.exists():raise RuntimeError('fresh v2 draft')
out.write_text(s)
(HERE/'FOUR_JOB_V1_TO_V2.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),s.splitlines(True),fromfile=str(base),tofile=str(out))))
(HERE/'V2_PREPARATION.json').write_text(json.dumps({'state':'PREPARATION_ONLY','collector_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'preservation':'host/wrapper/workflow/CI/guard exits separately retained; no acceptance rejudgment; unexpected retry path fails scope before payload','collector_executed':False,'SHM_access':False,'product_rerun':False,'static_validation':'AST only'},indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
