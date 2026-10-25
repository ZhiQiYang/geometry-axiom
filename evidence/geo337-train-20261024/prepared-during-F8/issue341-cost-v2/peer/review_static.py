from pathlib import Path
import json,hashlib,datetime,ast
P=Path('/tmp/geo341-cost-preparation-20261025');O=Path('/tmp/geo341-cost-tool-peer-20261025')
checks=[]
def h(b):return hashlib.sha256(b).hexdigest()
def check(n,v):
 checks.append({'name':n,'passed':bool(v)})
check('exact submitted PINS',h((P/'PINS.json').read_bytes())=='b56ae79481390f36bf9ddfeffd32fd7322cedb5fbb7697bf55a8817a01207558')
for n,d in json.loads((P/'PINS.json').read_bytes()).items():check('pinned '+n,h((P/n).read_bytes())==d)
f=(P/'fixed.c').read_text();w=(P/'withdrawn.c').read_text();r=(P/'restored.c').read_text();wd=json.loads((P/'WITHDRAWAL.json').read_bytes())
check('source fixed equals original Git stdout',(P/'fixed.c').read_bytes()==(P/'source-read.stdout.bin').read_bytes())
sr=json.loads((P/'source-read.json').read_bytes());check('original Git read success and fixed full SHA',sr['exit']==0 and sr['sha']=='75a1e93811a52b69385cbdaf6a09d773ed9052ad' and sr['argv']==['git','show',sr['sha']+':geometry-templates/woodworking/native/contact_world.c'])
check('one exact legacy fallback block',f.count(wd['before'])==1)
check('withdrawal exact entire leaf',f.replace(wd['before'],wd['after'])==w)
check('restore exact entire F8 leaf',f==r and w.count(wd['after'])==1 and w.replace(wd['after'],wd['before'])==r)
for name in ['contact_indexed_dedup','contact_member_index_sort','contact_face_index_build']:
 marker='static void '+name+'('
 start=f.index(marker);end=f.index('\n}',start)+2
 check('343 function unchanged '+name,f[start:end] in w)
for v in json.loads((P/'INSTRUMENTATION.json').read_bytes())['variants']:
 orig=(P/(v['name']+'.c')).read_text();diag=(P/(v['name']+'-diagnostic.c')).read_text();s=orig
 for a,b in v['edits']:
  check('unique instrumentation anchor '+v['name']+' '+str(v['edits'].index([a,b])),s.count(a)==1);s=s.replace(a,b)
 check('diagnostic reconstructed '+v['name'],s==diag)
 for a,b in reversed(v['edits']):
  check('unique instrumentation reverse '+v['name']+' '+str(v['edits'].index([a,b])),s.count(b)==1);s=s.replace(b,a)
 check('diagnostic byte reversible '+v['name'],s==orig)
ns={'__name__':'_peer_metadata','__file__':str(P/'run_costs.py')};exec(compile((P/'run_costs.py').read_bytes(),str(P/'run_costs.py'),'exec'),ns)
check('frozen plan matches actual plan',json.loads(json.dumps(ns['plan']()))==json.loads((P/'COMMAND_PLAN.json').read_bytes()))
check('all14 cases retained',len(ns['CASES'])==14 and len(set(ns['CASES']))==14)
check('eight original semantic cases',len(ns['POSITIVE'])==8)
proof=json.loads((P/'metadata-original-capture/RESULT.json').read_bytes());check('metadata proof phase exit 0 1 0',[x['command']['actual_process_returncode']for x in proof['phases']]==[0,1,0])
for row in proof['phases']:
 d=Path(row['command']['directory']);raw=(d/'stdout.bin').read_bytes();err=(d/'stderr.bin').read_bytes()
 check('metadata stdout pin '+row['phase'],h(raw)==row['command']['stdout_sha256'])
 check('metadata stderr pin '+row['phase'],h(err)==row['command']['stderr_sha256'])
 check('metadata parsed stdout '+row['phase'],json.loads(raw)==row['result'])
 check('metadata exactly14 '+row['phase'],row['result']['checks']==14)
check('withdrawn unique failing guard',proof['phases'][1]['result']['failures']==['wrong-source'])
text=(P/'run_costs.py').read_text();tree=ast.parse(text)
for phrase in ["fcntl.LOCK_EX|fcntl.LOCK_NB","for name in ('heavy.lock','secondary.lock')","not out.exists()","out.is_relative_to('/tmp')","no checkout changes","timeout=300","round_no in range(8)","order=VARIANTS if round_no%2==0 else tuple(reversed(VARIANTS))","all(len(xs)==7","performance_acceptance_decided=False"]:
 check('runtime static guard '+phrase,phrase in text)
report={'schema':'geo341-cost-static-adversarial/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'subject':str(P),'subject_pins_sha256':h((P/'PINS.json').read_bytes()),'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'checks_performed':checks,'exit':1,'passed':False,'finding':'TRUNCATED_FACE_FINDING.json','finding_severity':'collector completeness guard must be fixed before formal execution','positive_scope':'fallback block only; later #343 functions byte unchanged; restored exact F8; original locks/timeouts/samples retained','limits':['Pure metadata/static review only, no C/performance/Chrome executed.','Four-class work/CPU/wall and all original eight semantic cases remain UNRUN.','The fallback plan cannot by itself discharge historical Sc493 whole-withdrawal B1.','Initial parser accepts a one-row truncated none/N8 output; no claim this occurred in actual product output.']}
(O/'INITIAL_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k]for k in ['checks','failed_checks','exit','passed','finding']},ensure_ascii=False))
