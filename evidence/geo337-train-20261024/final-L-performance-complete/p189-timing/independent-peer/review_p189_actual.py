from pathlib import Path
import csv,json,statistics,sys
from review_performance_package_common import Review,L
gate=sys.argv[1]
pin={'p189':'a2c4775e54a118c429060575f4b1ddd981d3d827726e69837f4222afa0a59615','p189-timing':'d48055d2e7f46fd8948ebda8364f6548e0022cb36d953102ce7101a4a9dffdde'}[gate]
v=Review(gate,pin);r=v.root;m=r/'measurement';expected={'main':'adbaebf9c73ea6801d7b4d5214e4b846b132923b','base':'3e600772076465fc65a26ac09055028301c0fb0b','fix':L}
producer=v.j(v.B.parent/(gate+'-v2-collection-launch')/'RESULT.json');v.capture(producer);v.ck(producer['actual_process_returncode']==0 and producer['command'][-2:]==['--gate',gate],'actual collection process zero')
if gate=='p189':
 v.ck(v.r['launcher_exit_code']==1 and v.r['passed'] is False,'full original product red preserved')
 prov=v.j(m/'provenance.json');v.ck(prov['shas']==expected,'three original source SHAs')
 phase=v.r['phases'][0];d=Path(phase['outer_command']['directory']);stdout=(d/'stdout.bin').read_text();stderr=(d/'stderr.bin').read_text();bad='repo-_role_priority_mutant.scene'
 v.ck("assert raw['base'] == raw['fix'], f'dump 不同：{name}'" in stderr and ('AssertionError: dump 不同：'+bad) in stderr,'precise original assertion and mismatch fixture')
 passed=[x.removesuffix(' loadfile+dump 逐位元組相同') for x in stdout.splitlines() if x.endswith(' loadfile+dump 逐位元組相同')]
 v.ck(len(passed)==len(set(passed)) and all('s'+str(n)+'.scene' in passed for n in [16,32,48,64]),'all four generated scenes completed byte equality')
 for name in [*passed,bad]:
  a=(m/(name+'-base.stdout')).read_bytes();b=(m/(name+'-fix.stdout')).read_bytes();v.ck((a==b)==(name!=bad),'actual raw dump equality '+name)
  for side,body in [('base',a),('fix',b)]:
   rows=[json.loads(x) for x in body.splitlines()];v.ck(len(rows)==2 and isinstance(rows[0].get('ok'),bool) and rows[1].get('ok') is True,'original two JSON load/dump replies '+name+'/'+side)
   if name.startswith('s') and name[1:3].rstrip('.').isdigit():v.ck(rows[0]['ok'] is True,'generated scene actually loads '+name+'/'+side)
 v.ck(not (m/'dump-equivalence.json').exists() and not (m/'receipt.json').exists() and not (m/'samples.tsv').exists(),'failed full assertion prevented completed dump receipt and original timings')
 extra={'product_passed':False,'exact_original_assertion':"assert raw['base'] == raw['fix'], f'dump 不同：{name}'",'first_failed_scene':bad,'completed_equal_scene_count':len(passed),'generated_scenes_equal':[16,32,48,64],'full_timing_executed':False,'raw_mismatch_hashes':{side:v.h(m/(bad+'-'+side+'.stdout')) for side in ['base','fix']},'classification':'Original full byte-equality gate red; timing-only cannot waive it. Semantic authorization/classification needs separate review; this receipt does not change baseline or assertion.'}
else:
 rr=v.j(m/'receipt.json');scope=v.j(m/'TIMING_ONLY_SCOPE.json');v.ck(rr['shas']==expected and rr['overall_P189_passed'] is False and scope['overall_P189_passed'] is False and v.r['overall_P189_passed'] is False,'original timing-only no waiver')
 v.ck(scope['original_full_exit']==1 and scope['original_full_receipt_sha256']==v.h('/workspace/g337p189L/receipt.json') and scope['sampling_retried'] is False and scope['dump_equivalence_executed_in_this_stage'] is False,'precise previous-red binding no retry')
 v.ck(v.r['launcher_exit_code']==0 and v.r['passed'] is True and scope['timing_tail_exit']==0,'original timing stage zero only')
 for z in scope['binary_identities']:
  v.ck(z['source_sha']==expected[z['side']] and v.h(z['from'])==v.h(z['path'])==z['sha256'] and Path(z['path']).stat().st_size==z['bytes'],'same original three binaries '+z['side'])
 samples=v.j(m/'loadfile-samples.json');rows=list(csv.DictReader((m/'samples.tsv').open(),delimiter='\t'))
 wanted={(n,k,s) for n in [16,32,48,64] for k in [0,1,2] for s in expected}
 v.ck(len(samples)==len(rows)==rr['samples']==36 and {(x['n'],x['round'],x['side']) for x in samples}==wanted,'36 unique interleaved points')
 v.ck([(x['n'],x['round'],x['side']) for x in samples]==[(n,k,s) for n in [16,32,48,64] for k in [0,1,2] for s in (list(expected) if k%2==0 else list(expected)[::-1])],'exact original alternating interleaving')
 for i,x in enumerate(samples,1):
  v.ck(x['index']==i and x['actual_process_returncode']==0 and x['timeout_expired'] is False and x['timeout_exception'] is None and x['load_ok'] is True,'sample true successful process '+str(i))
  v.ck(x['command'][-1]==str(r/'work'/x['side']/'bridge') and x['seconds']>0,'sample original binary and time '+str(i))
  for kind,z in x['files'].items():
   p=m/z['path'];v.ck(p.stat().st_size==z['bytes'] and v.h(p)==z['sha256'],'sample full raw '+str(i)+'/'+kind)
  out=(m/x['files']['stdout.bin']['path']).read_bytes();v.ck(json.loads(out.splitlines()[0]).get('ok') is True,'actual load response '+str(i))
  inp=(m/x['files']['stdin.bin']['path']).read_text();v.ck(inp=='loadfile '+x['scene']+'\n','exact load-only stdin '+str(i))
  t=rows[i-1];v.ck(t['status']=='ok' and t['ok']=='True' and int(t['n'])==x['n'] and int(t['round'])==x['round'] and t['side']==x['side'] and abs(float(t['seconds'])-x['seconds'])<=0.000051,'original rounded TSV binds raw duration '+str(i))
 calc=[]
 for n in [16,32,48,64]:
  meds={s:statistics.median(float(x['seconds']) for x in rows if int(x['n'])==n and x['side']==s) for s in expected};ratio=meds['fix']/meds['main'];calc.append({'n':n,'medians':meds,'fix_main':ratio,'pass':ratio<=2})
 v.ck(calc==rr['ratios'] and all(x['pass'] for x in calc) and rr['pass'] is True,'original four thresholds unchanged independently recomputed')
 extra={'timing_only_passed':True,'overall_P189_passed':False,'sample_count':36,'source_shas':expected,'ratios':calc,'original_full_gate_exit':1,'sampling_retried':False,'dump_equivalence_executed_in_timing_stage':False}
raise SystemExit(v.finish(extra))
