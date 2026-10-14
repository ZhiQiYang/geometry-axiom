import hashlib,json,pathlib,re
root=pathlib.Path('/tmp/geometry-wake25-201');folder=root/'controls';rows=[]
for p in sorted(folder.glob('*.receipt.json')):
 r=json.loads(p.read_text());label=p.name[:-len('.receipt.json')];s=(folder/(label+'.stdout')).read_text();e=(folder/(label+'.stderr')).read_bytes()
 expected=1 if r['phase'] in ['before','removed'] else 0
 assert r['actual_exit']==expected
 assert r['case'] in s
 if expected:
  deadline=5000 if label.startswith('ordinary') else 10000
  assert f'test timed out after {deadline}ms' in s
 else:
  for value in ['tests 1','pass 1','fail 0','cancelled 0']:assert value in s
 duration=re.search(re.escape(r['case'])+r' \(([\d.]+)ms\)',s);assert duration
 wrapper=folder/(label+'.cjs');assert hashlib.sha256(wrapper.read_bytes()).hexdigest()==r['wrapper_sha256']
 rows.append({'case':r['case'],'phase':r['phase'],'duration_ms':float(duration.group(1)),'actual_exit':r['actual_exit'],'nominal_duty':r['nominal_duty'],'pid':r['pid'],'pgid':r['pgid'],'source_sha256':r['source_sha256'],'stdout_sha256':hashlib.sha256(s.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(e).hexdigest(),'failure_class':'timeout cancellation' if expected else None})
assert len(rows)==16
(root/'controls-summary.json').write_text(json.dumps(rows,indent=2)+'\n');print('16 target controls verified; 8 real passes, 8 timeout cancellations, all actual OS exits preserved')
