"""Pure synthetic collector protocol tests, not C/semantic/performance acceptance."""
from pathlib import Path
import argparse,json
P=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--withdraw',choices=['count','identity','numeric','duplicates']);a=p.parse_args()
s=(P/'run_costs.py').read_text()
patches={'count':"need(len(fields['FACE'])==expected_faces,'complete expected FACE row count')",'identity':"need(meta['case']==case and meta['n']==str(n),'META matches exact requested case/size')",'numeric':"need(len(values)==9 and all(re.fullmatch(r'-?[0-9]+',v)for v in values),'nine numeric FACE fields')",'duplicates':"need(len({p[0]for p in pairs})==len(pairs),'unique fields')"}
if a.withdraw:
 old=patches[a.withdraw];assert s.count(old)==1;s=s.replace(old,'pass # isolated protocol guard withdrawal')
ns={'__name__':'_synthetic_only','__file__':str(P/'run_costs.py')};exec(compile(s,str(P/'run_costs.py'),'exec'),ns);parse=ns['inspect_output'];checks=[]
def make(case,n,diag=False):
 kind=case.removeprefix('unique-');count=2 if kind in ('dense','fallback-dense')else 2*(n-1)if kind=='few'else 2*n
 lines=['MODE diagnostic=true performance_sample=false'if diag else 'MODE diagnostic=false performance_sample=true',f'META case={case} n={n} admitted={n*2} capacity=2432 fallback={int(case.startswith("fallback-"))} face_size=64','TIME cpu_ns=1 wall_ns=2 cpu_resolution_ns=1 wall_resolution_ns=1']
 if diag:lines+=['WORK shadow_iterations=0 active_initializations=0 active_reads=0 active_deletions=0 memmove_calls=0 memmove_bytes=0 compaction_copies=0','PATH orders_indexed=1 orders_unique=0 admitted='+str(2*n)+' indexed_calls=0']
 lines+=['FACE 1 0 42 -1 0 0 0 0 27']*count
 return ('\n'.join(lines)+'\n').encode()
def check(name,raw,diag=False,case='none',n=8,reject=True):
 failed=False
 try:parse(raw,diag,case,n)
 except Exception:failed=True
 checks.append({'name':name,'passed':failed==reject})
for case,n in ns['CASES']:
 for diag in [False,True]:check(f'complete-{case}-{n}-{diag}',make(case,n,diag),diag,case,n,False)
b=make('none',8);face=b'FACE 1 0 42 -1 0 0 0 0 27\n'
for name,raw in [('truncated-one-face',b.replace(face,b'',15)),('extra-face',b+face),('wrong-meta-case',b.replace(b'case=none',b'case=few')),('wrong-meta-n',b.replace(b'n=8 ',b'n=9 ')),('wrong-admitted',b.replace(b'admitted=16',b'admitted=14')),('wrong-capacity',b.replace(b'capacity=2432',b'capacity=2433')),('wrong-fallback',b.replace(b'fallback=0',b'fallback=1')),('nonnumeric-face',b.replace(b'0 0 27\n',b'0 0 2.5\n')),('short-face',b.replace(b'FACE 1 0 ',b'FACE 1 ')),('duplicate-time-key',b.replace(b'TIME cpu_ns=1 ',b'TIME cpu_ns=1 cpu_ns=1 ')),('duplicate-mode',b+b'MODE diagnostic=false performance_sample=true\n'),('unknown-line',b+b'UNEXPECTED hidden-output\n'),('missing-newline',b[:-1]),('invalid-id',b.replace(b'FACE 1 0 42',b'FACE 1 -1 42')),('invalid-face-size',b.replace(b'face_size=64',b'face_size=0'))]:check(name,raw)
d=make('none',8,True);check('duplicate-work',d+d.split(b'WORK ',1)[1].split(b'\n',1)[0].join([b'WORK ',b'\n']),True)
check('missing-path',b,True)
failures=[x['name']for x in checks if not x['passed']];r={'exit':int(bool(failures)),'checks':len(checks),'failures':failures,'withdrawn_guard':a.withdraw,'C_executed':False,'product_mutation_proof':False,'details':checks};print(json.dumps(r));raise SystemExit(r['exit'])
