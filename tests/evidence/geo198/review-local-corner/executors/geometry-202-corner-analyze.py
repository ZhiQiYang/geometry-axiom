import hashlib,json,pathlib,re,sys
out=pathlib.Path('/tmp/geometry-202-corner/aggregate')
receipt=json.loads((out/'run.json').read_text()); log=(out/'run.log').read_text()
rows=[]
for line in log.splitlines():
    m=re.match(r'^(\S+:\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)',line)
    if m:rows.append(dict(zip(('suite','total','passed','failed','skipped','display_seconds'),[m[1],*[int(m[i]) for i in range(2,6)],float(m[6])])))
m=re.search(r'^合計\(已執行、有計數者\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)',log,re.M)
assert m
totals=dict(zip(('total','passed','failed','skipped'),map(int,m.groups()[:4])))
assert {k:sum(r[k] for r in rows) for k in totals}==totals
assert receipt['returncode']==1
failed=[r for r in rows if r['failed']]
assert len(failed)==1 and failed[0]['suite']=='py:test_axiom_reader' and failed[0]['failed']==6,failed
reader=json.loads((out/'logs/py_test_axiom_reader.json').read_text())
index={r['path']:r for r in json.loads((out/'log-index.json').read_text())}
assert all(index['logs/'+name]['modified_after_runner_start'] for name in ('py_test_axiom_reader.json','node_tests-js.log','c_integrity.log','core_run_tests.log'))
node=next(r for r in rows if r['suite']=='node:tests-js')
assert (node['total'],node['passed'],node['failed'],node['skipped'])==(651,651,0,0)
node_log=(out/'logs/node_tests-js.log').read_text()
assert re.search(r'cancelled\s+0\b',node_log) and re.search(r'todo\s+0\b',node_log)
sys.path.insert(0,str(pathlib.Path('tests').resolve()));import run_all
assert len(run_all.NODE_TEST_FILES)==36
data={'receipt':receipt,'totals':totals,'counted_suites':len(rows),'all_suites':len(re.findall(r'^\[\d+/83\]',log,re.M)),
      'failed_rows':failed,'skipped_rows':[r for r in rows if r['skipped']],'node':node,
      'reader_failures':reader['failures'],'rows':rows,'scope':'Original cloud-native aggregate; not final-SHA seven jobs/WSL/browser/GDI/isolation'}
(out/'analysis.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
sentence=f"原完整 83-suite aggregate：{totals['total']} 項＝{totals['passed']} pass／{totals['failed']} fail／{totals['skipped']} 個具名允許 Windows GDI skip，直接 returncode {receipt['returncode']}、{receipt['seconds']:.2f} 秒；六紅全屬 reader。Node 全 36 檔 651/651、零 fail／cancel／skip。"
for name in ('README','body','reply'):
    path=pathlib.Path('/tmp/geometry-202-corner-'+name+'.md')
    text=path.read_text();assert text.count('AGGREGATE_RESULT')==1
    path.write_text(text.replace('AGGREGATE_RESULT',sentence))
print(json.dumps({'totals':totals,'receipt':receipt,'all_suites':data['all_suites'],'failed_rows':failed,'skipped_rows':data['skipped_rows']},ensure_ascii=False))
