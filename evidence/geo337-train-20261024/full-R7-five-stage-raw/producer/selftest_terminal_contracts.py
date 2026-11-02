"""Pure collection-guard contracts against copied terminal metadata; no subject execution."""
from pathlib import Path
import ast,copy,json,sys,hashlib
D=Path(__file__).resolve().parent;OLD=Path('/workspace/geo323-r6-full-collection-20261024')
mode=sys.argv[1] if len(sys.argv)>1 else 'fixed';assert mode in ('fixed','withdrawn','restored')
plan=json.loads((D/'PLAN.json').read_bytes());r=json.loads(Path(plan['terminal_bindings']['receipt']['path']).read_bytes());outer=json.loads(Path(plan['terminal_bindings']['launcher']['path']).read_bytes());driver=json.loads(Path(plan['terminal_bindings']['outer']['path']).read_bytes());R=plan['source_sha'];STAGES=['prepare','build','compare','perf','profile'];count=0

def check(value,message):
 global count
 assert value,message
 count+=1
new_ast=ast.parse((D/'collect.py').read_text());old_ast=ast.parse((OLD/'collect.py').read_text())
for name in ['sha_bytes','digest','save','need','row','BoundedArchive']:
 a=next(x for x in new_ast.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==name);b=next(x for x in old_ast.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==name)
 check(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),'unchanged byte preservation helper '+name)
messages=['frozen actual outer Recorder and launcher terminal retained','original df and five-stage outer exits','frozen original cumulative CLI exits','frozen original own-stage exits','unrun stages not passed','original downstream audit presence stays unchanged','all original target values and verdicts retained, never inferred from R6']
expressions={}
for node in ast.walk(new_ast):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='need' and len(node.args)==2 and isinstance(node.args[1],ast.Constant) and node.args[1].value in messages:expressions[node.args[1].value]=node.args[0]
check(set(expressions)==set(messages),'all actual seven collection acceptance predicates selected')
if mode=='withdrawn':
 expressions[messages[-1]]=ast.parse("r['quantitative_targets']['N64_fix_main']['target_met'] is False and r['quantitative_targets']['small_N_no_regression']['points']['16']['target_met'] is False",mode='eval').body

def evaluate(expr,rr=r,oo=outer,dd=driver,pp=plan):
 return eval(compile(ast.fix_missing_locations(ast.Expression(expr)),'<actual collector guard>','eval'),{'r':rr,'outer':oo,'driver':dd,'plan':pp,'R':R,'STAGES':STAGES,'type':type,'int':int,'len':len})
for message in messages:check(evaluate(expressions[message]),'current original R7 snapshot accepted: '+message)
changed=copy.deepcopy(r);changed['quantitative_targets']['N64_fix_main']['target_met']=not r['quantitative_targets']['N64_fix_main']['target_met'];check(not evaluate(expressions[messages[-1]],rr=changed),'changed original target verdict rejected')
changed=copy.deepcopy(r);changed['quantitative_targets']['N16_TEST_INVENTED_FIELD']=0;check(not evaluate(expressions[messages[-1]],rr=changed),'invented target field rejected')
changed=copy.deepcopy(r);changed['stages']['perf']['execution_exit']=91;check(not evaluate(expressions[messages[3]],rr=changed),'changed own-stage exit rejected')
changed=copy.deepcopy(outer);changed['commands'][2]['actual_process_exit']=91;check(not evaluate(expressions[messages[2]],oo=changed),'changed cumulative CLI exit rejected')
changed=copy.deepcopy(driver);changed['exit']=None;check(not evaluate(expressions[messages[0]],dd=changed),'nonterminal driver rejected')
changed=copy.deepcopy(outer);changed['exit']=None;check(not evaluate(expressions[messages[0]],oo=changed),'nonterminal launcher rejected')
changed=copy.deepcopy(r);changed['ABC_result']='invented';check(not evaluate(expressions[messages[5]],rr=changed),'invented downstream audit rejected')
changed=copy.deepcopy(r);changed['full_acceptance_passed']=True;check(not evaluate(expressions[messages[4]],rr=changed),'incomplete five stages cannot become full acceptance')
for name,pin in plan['terminal_bindings'].items():
 raw=Path(pin['path']).read_bytes();check(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'exact original terminal binding '+name)
check(not Path('/tmp/geo323-r7-full-package-20261024').exists(),'collector not executed by preparation')
print(json.dumps({'mode':mode,'checks':count,'failed':0,'source':R,'subject_executions':0,'scope':'Only actual collection guard predicates and small terminal metadata; no performance samples or product judge executed.'}))
