from pathlib import Path
import json,hashlib,os,statistics,collections,datetime,re
P=Path('/tmp/geo341-F8-fallback-cost-run-20261025');T=Path('/tmp/geo341-cost-preparation-v2-20261025');O=Path('/tmp/geo341-F8-fallback-cost-actual-peer-20261025');F='75a1e93811a52b69385cbdaf6a09d773ed9052ad';checks=[]
def read(p):
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME)
 with os.fdopen(fd,'rb')as f:return f.read()
def h(b):return hashlib.sha256(b).hexdigest()
def c(n,v):checks.append({'name':n,'passed':bool(v)})
x=json.loads(read(P/'RESULT.json'));final=json.loads(read('/tmp/geo341-F8-fallback-cost-EXEC_FINAL-20261025.json'));pins=json.loads(read(T/'PINS.json'));c('exact v2 tool pin',h(read(T/'PINS.json'))=='008b50d645074777e38c2d2b61074d510a28e7069319b9afc79d20e2966cbeab')
for name,d in pins.items():c('tool file pin '+name,h(read(T/name))==d)
c('true tool/semantic0, no performance acceptance',final['exit_code']==x['exit']==0 and x['passed']and x['semantic_passed']and x['performance_acceptance_decided']is False and x['formal_acceptance']is False)
c('fixed F8 scope',x['source_sha']==F and x['scope']=='F8 legacy fallback only; does not discharge historical whole-341 B1' and x['Sc493_whole_withdrawal_executed']is False)
c('stack16MiB',x['stack_limit'][0]==16777216);c('original timeouts',x['compile_timeout']==300 and x['run_timeout']==20);c('O2 same explicit flags',x['compiler_flags']==['-std=c11','-O2','-Werror=implicit-function-declaration']);c('no discarded adaptive sampling',x['warmup_triplets']==1 and x['scored_triplets']==7 and x['collects_per_sample']==1 and x['alternating_order']and x['performance_thresholds_added']is False)
cmd={r['directory']:r for r in x['commands']};c('546 unique completed commands',len(cmd)==len(x['commands'])==546)
raws={}
for i,r in enumerate(x['commands'],1):
 d=Path(r['directory']);c('original process0 '+str(i),r['actual_process_returncode']==0 and r['timeout_expired']is False);c('command original F8 '+str(i),r['source_sha']==r['acceptance_sha']==F)
 for s in ['stdout','stderr']:
  b=read(d/(s+'.bin'));c('original stream pin '+str(i)+' '+s,len(b)==r[s+'_bytes']and h(b)==r[s+'_sha256'])
  if s=='stdout':raws[str(d)]=b
for s in x['source_files']:
 b=read(P/'source'/s['path']);c('source snapshot pin '+s['path'],len(b)==s['bytes']and h(b)==s['sha256'])
 matching=[r for r in x['commands']if r['command'][-2:]==['show',F+':'+s['path']]]
 c('source snapshot original fixed Git bytes '+s['path'],len(matching)==1 and raws[matching[0]['directory']]==b)
for e in x['elfs']:
 b=read(e['path']);c('retained ELF pin '+Path(e['path']).name,len(b)==e['bytes']and h(b)==e['sha256']and b[:4]==b'\x7fELF')
c('nine retained ELF outputs',len(x['elfs'])==9)
positive=[]
for r in x['commands']:
 a=r['command']
 if len(a)==2 and a[0].endswith('-positive'):positive.append((Path(a[0]).name.removesuffix('-positive'),a[1]))
expected_positive={(v,n)for v in ['fixed','withdrawn','restored']for n in x['positive_cases']};c('all8 positive cases in all3 variants',len(positive)==24 and set(positive)==expected_positive)
header=read(P/'source/geometry-templates/woodworking/native/supports.h').decode();c('original face enum mapping',re.search(r'WOOD_STOP_OUTLINE_EDGE\s*,\s*WOOD_STOP_HOLE_EDGE\s*,\s*WOOD_STOP_MEMBER_SIDE',header)is not None and 'WOOD_STOP_FIXED = 1'in header)
def expected_faces(case,n):
 unique=case.startswith('unique-');kind=case.removeprefix('unique-');pairs=1 if kind in ['dense','fallback-dense']else n-1 if kind=='few'else n
 return ['FACE 2 0 %d -1 %d 1 %d 0 27'%(i+1 if unique else 42,e,(0 if kind in ['dense','fallback-dense']else i*200)+e*100)for i in range(pairs)for e in [0,1]]
def parse(raw):
 fields={};faces=[]
 for line in raw.decode().splitlines():
  key,_,rest=line.partition(' ')
  if key=='FACE':faces.append(line)
  elif key!='MODE':fields[key]=dict(t.split('=',1)for t in rest.split())
 fields['FACE']=faces;return fields
c('378 complete samples',len(x['samples'])==378);c('42 diagnostics+42warmup+294scored',dict(collections.Counter(s['kind']for s in x['samples']))=={'diagnostic-not-performance':42,'warmup':42,'scored':294})
seen=set();tuples=[]
for i,s in enumerate(x['samples'],1):
 label=f'{s["case"]}/{s["n"]}/{s["variant"]}/{s["kind"]}/{s.get("round")}';r=cmd[s['command']];raw=raws[s['command']];fields=parse(raw)
 c('sample raw output exact '+label,fields==s['fields']);c('independent full9field face sequence '+label,fields['FACE']==expected_faces(s['case'],s['n']))
 c('each sample its own real command '+label,s['command']not in seen);seen.add(s['command']);c('sample exact argv '+label,r['command']==[str(P/'bins'/(s['variant']+('-diagnostic'if s['kind']=='diagnostic-not-performance'else'-cost'))),s['case'],str(s['n'])])
 diag=s['kind']=='diagnostic-not-performance';c('sample diagnostic separation '+label,('WORK'in fields)==diag and (b'MODE diagnostic=true performance_sample=false\n'in raw if diag else b'MODE diagnostic=false performance_sample=true\n'in raw))
 if diag:
  path=fields['PATH'];c('actual path admission '+label,int(path['admitted'])==s['n']*2 and int(path['orders_indexed'])==int(s['n']<=64)and int(path['indexed_calls'])==int(s['case'].startswith('unique-')))
  if s['n']<=64:c('actual duplicate/unique route '+label,int(path['orders_unique'])==int(s['case'].startswith('unique-')))
 tuples.append((s['case'],s['n'],s['variant'],s['kind'],s.get('round')))
expected=[]
for case,n in x['cases']:
 for v in ['fixed','withdrawn','restored']:expected.append((case,n,v,'diagnostic-not-performance',None))
 for r in range(8):
  for v in (['fixed','withdrawn','restored']if r%2==0 else ['restored','withdrawn','fixed']):expected.append((case,n,v,'warmup'if r==0 else'scored',r))
c('all14 inputs and exact original interleaved8triplet execution order',tuples==expected)
medians=[];measurements=[]
for case,n in x['cases']:
 rawvalues={v:{metric:[int(s['fields']['TIME'][metric])for s in x['samples']if(s['case'],s['n'],s['variant'],s['kind'])==(case,n,v,'scored')]for metric in ['cpu_ns','wall_ns']}for v in ['fixed','withdrawn','restored']}
 c('all7 raw values '+case+str(n),all(len(a)==7 for d in rawvalues.values()for a in d.values()));values={v:{k:statistics.median(a)for k,a in d.items()}for v,d in rawvalues.items()}
 medians.append({'case':case,'n':n,'values':values,'scope':'measurement only; no new performance pass threshold'})
 works={s['variant']:{k:int(v)for k,v in s['fields']['WORK'].items()}for s in x['samples']if s['case']==case and s['n']==n and s['kind']=='diagnostic-not-performance'}
 c('restored exact work '+case+str(n),works['fixed']==works['restored'])
 measurements.append({'case':case,'n':n,'median_ns':values,'all7_raw_values_ns':rawvalues,'fixed_to_withdrawn':{k:values['fixed'][k]/values['withdrawn'][k]for k in ['cpu_ns','wall_ns']},'restored_to_withdrawn':{k:values['restored'][k]/values['withdrawn'][k]for k in ['cpu_ns','wall_ns']},'work':works})
c('reported medians derive from all originals',x['medians']==medians);c('no recorded execution errors',not x['errors'])
failed=[z for z in checks if not z['passed']]
r={'schema':'geo341-F8-fallback-cost-independent-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':F,'checks':len(checks),'exit':int(bool(failed)),'findings':failed,'checks_performed':checks,'original_commands':546,'original_positive_runs':24,'original_samples':378,'original_elfs':9,'source_files':95,'original_driver_exit':0,'semantic_passed':True,'performance_acceptance_decided':False,'historical_whole341_B1_discharged':False,'measurements':measurements,'bindings':{str(P/'RESULT.json'):h(read(P/'RESULT.json')),str(T/'PINS.json'):h(read(T/'PINS.json'))},'scope':'Actual raw/commands/semantic sequences/work/timers only. No C/performance rerun. F8 fallback-only with #343 indexed controls preserved.','limitations':['No existing quantitative microbenchmark pass line was supplied or invented. Original passed means semantic/collection complete, not all performance improved.','Fixed/restored identical source still shows microsecond-scale sample variability; all samples and both ratios are retained.','Sc493 whole withdrawal remains separate and unexecuted; unique-ID controls are not fallback benefit samples.','No R8 rerun, no source/ledger/train changes, and no overall READY claim.','O2 diagnostic WORK is separately instrumented; CPU/wall uses uninstrumented binaries. Counters are not hardware memory-traffic measurements.']}
(O/'REVIEW.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k]for k in ['checks','exit','findings','original_samples']}));raise SystemExit(r['exit'])
