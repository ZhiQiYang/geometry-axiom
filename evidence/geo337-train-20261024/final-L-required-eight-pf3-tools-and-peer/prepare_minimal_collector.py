"""Derive the existing terminal section7 packer for two other frozen original stages."""
from pathlib import Path
import hashlib,json,difflib
BASE=Path(__file__).parent
old=Path('/tmp/train337-section7-terminal-collection/collect_original_section7.py')
source=old.read_text()
changes=[('Package only terminal original section7 evidence','Package only terminal original required-eight/PF3 evidence'),("choices=['cardref','axiom']","choices=['required-eight','pf3']"),("'schema':'section7-original-terminal-collection/1'","'schema':'required-eight-pf3-original-terminal-collection/1'"),('ORIGINAL_SECTION7_LOGS_REPORTS_AND_ELF_HASHES.tar.gz','ORIGINAL_NONPERF_LOGS_REPORTS_AND_ELF_HASHES.tar.gz')]
for before,after in changes:
 assert source.count(before)==1
 source=source.replace(before,after)
start=source.index("if a.gate=='cardref':")
end=source.index("for name,value in [('EXCLUDED_ELF_PAYLOADS.json'",start)
addition='''# Preserve the v4 subject's distinct stage receipt and complete inner capture.
stage_receipt=out/a.gate/'subject/receipt.json';stage=json.loads(stage_receipt.read_text())
need(stage['source_sha']==L and stage['stages'][a.gate]['ended_utc'] and stage['stages'][a.gate]['execution_exit']==0 and stage['wrapper_exit']==0,'original nested stage terminal0 required')
need(hfile(stage_receipt)==r['gates'][0]['original_stage_receipt_sha256'],'original stage receipt pin')
inner=[]
for commands in sorted((out/a.gate/'subject/invocations').glob('*/commands/commands.json')):
 for row in json.loads(commands.read_text()):
  q=Path(row['directory']);need(q.is_relative_to(out/a.gate/'subject'),'inner capture containment')
  need(json.loads((q/'result.json').read_text())==row,'inner row matches full result')
  for kind in ['stdout','stderr']:
   f=q/(kind+'.bin');need(f.stat().st_size==row[kind+'_bytes'] and hfile(f)==row[kind+'_sha256'],'complete inner stream '+kind)
  need(row['source_sha']==L and row['ended_epoch'] and not row['timeout_expired'],'inner L terminal identity')
  inner.append(row)
summary['original_nested_stage']={k:stage[k] for k in ['source_sha','stages','wrapper_exit','all_executed_stage_commands_passed','full_acceptance_passed']}
summary['original_inner_commands']=len(inner)
save(d/'INNER_COMMANDS.json',inner)
if a.gate=='required-eight':
 expected=json.loads((Path('/tmp/train337-final-nonperf-specials-prep')/'PREPARATION.json').read_text())['required_eight_expected']
 selected=[x for x in inner if 'tests/run_all.py' in x['command']]
 need(len(selected)==1 and selected[0]['actual_process_returncode']==0,'one original selected aggregate')
 argv=selected[0]['command'];names=[argv[i+1] for i,x in enumerate(argv) if x=='--only']
 need(set(names)==set(expected) and len(names)==8,'original exact eight selection')
 text=(Path(selected[0]['directory'])/'stdout.bin').read_text();counts=[]
 for name,e in expected.items():
  found=[line.split() for line in text.splitlines() if line.split() and line.split()[0]==name]
  need(len(found)==1,'one actual aggregate row '+name);fields=found[0]
  count,passed,failed,skipped=map(int,fields[1:5]);need(count==passed==e['count'] and failed==skipped==0,'original exact selected row '+name)
  counts.append(dict(name=name,count=count,passed=passed,failed=failed,skipped=skipped,unit=e['unit']))
 need(sum(x['count'] for x in counts)==676,'original selected676')
 summary['original_selected_counts']=counts
 summary['selected_total_registered_units']=676
 summary['selected_aggregate_capture']=selected[0]['directory']
 summary['limitations'].append('required-eight-suite-logs is the original runner copy of the global log directory, which can retain previous unselected logs. Only the exact eight selected argv and original aggregate rows above count as this execution; 676 combines tests, C checkpoints and scenarios, not676 unittest methods.')
else:
 original=out/a.gate/'subject/evidence/pf3/summary.json';report=json.loads(original.read_text())
 need(report['originalSourcesUnchanged'] is True,'PF3 original source restore')
 for phase in ['baseline','restored']:
  item=report[phase];need(item['verdict']=='pass' and item['exit']==0 and item['counts']==dict(run=20,failures=0,errors=0,skipped=0),'PF3 original full20 '+phase)
 mutants=report['mutations'];need(len(mutants)==19 and len({x['id'] for x in mutants})==19,'original distinct19 mutations')
 for item in mutants:
  need(item['verdict']=='killed' and item['exit']==1 and item['counts']==dict(run=1,failures=1,errors=0,skipped=0) and bool(item['requiredMarker']),'PF3 original assertion kill '+item['id'])
 summary['original_pf3_report']=dict(path=str(original),sha256=hfile(original),baseline=report['baseline'],mutations=mutants,restored=report['restored'],originalSourcesUnchanged=True)
 summary['limitations'].append('PF3 baseline20, nineteen independent one-method assertion negatives, restored20 are separate counts; compiler executions are not test passes or mutation kills.')
'''
source=source[:start]+addition+source[end:]
new=BASE/'collect_original_nonperf.py';assert not new.exists();new.write_text(source);compile(source,str(new),'exec')
(BASE/'COLLECTOR_DIFF.patch').write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),source.splitlines(True),fromfile=str(old),tofile=str(new))))
pin=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(original=str(old),original_sha256=pin(old),collector=str(new),collector_sha256=pin(new),patch_sha256=pin(BASE/'COLLECTOR_DIFF.patch'),source_sha='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db',changes='Only gate choices/schema/archive label and original nested-stage summary collection replace the unrelated cardref-specific summary; source guards, byte capture, ELF retention/exclusion and full roundtrip remain.',subject_executed=False)
(BASE/'PREPARATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
