import collections,json,pathlib,re,sys
root=pathlib.Path('/workspace/geometry-axiom');sys.path.insert(0,str(root/'tests'));import mutate
out=pathlib.Path('/tmp/geometry-198-review2/mutations-final')
rows=json.loads((out/'workers/workers.json').read_text())
assert all(r['exit']==0 for r in rows),rows
all_ids=[x for r in rows for x in r['ids']];assert len(all_ids)==len(set(all_ids))==len(mutate.MUTANTS)
compiled=[x for p in (out/'workers').glob('worker-*.log') for x in re.findall(r'^(M\d+)  exe 已重編$',p.read_text(),re.M)]
required={m['id'] for m in mutate.MUTANTS if not m.get('retired')}
assert set(compiled)==required and len(compiled)==len(required),(required-set(compiled),len(compiled))
records=mutate.load_records(root/'tests/mutants_results.json')
counts=dict(collections.Counter(r['verdict'] for r in records.values()))
assert counts.get('survived',0)==0 and counts.get('stale',0)==0
for key in ('M61','M62','M63','M64','M65'):assert records[key]['verdict']=='killed',records[key]
report={'inventory':len(records),'non_retired_recompiled':len(compiled),'retirement_records_validated':len(records)-len(compiled),'counts':counts,'new_and_updated_mutants':{k:{'verdict':records[k]['verdict'],'killed_by':records[k]['killed_by']} for k in ('M61','M62','M63','M64','M65')},'workers_returncodes':[r['exit'] for r in rows]}
(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(out/'ledger.json').write_bytes((root/'tests/mutants_results.json').read_bytes());print(report)
