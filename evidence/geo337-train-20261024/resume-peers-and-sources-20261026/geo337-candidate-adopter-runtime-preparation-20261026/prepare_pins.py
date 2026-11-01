from pathlib import Path
import hashlib,json,ast
here=Path(__file__).parent
subject=Path('/tmp/geo337-resume-final-source-plan-20261026/adopt_candidate_three_leaves.py')
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
for n in ['tiny_candidate_phase.py','run_candidate_tiny.py']:ast.parse((here/n).read_text())
q={'schema':'candidate-adopter-tiny-runtime/1','execute':False,'root_capacity_admitted':False,'root_new_fixture_only_lease':False,'additional_bound_bytes':16*1024*1024,'out':None,'subject':pin(subject),'harness':pin(here/'tiny_candidate_phase.py'),'runner_sha256':pin(here/'run_candidate_tiny.py')['sha256']}
p=here/'REQUEST.UNBOUND.json';assert not p.exists();p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
d={'state':'PREPARATION_ONLY_RUNTIME_UNRUN','formal_adoption_executed':False,'subject':pin(subject),'files':[pin(here/n)for n in ['tiny_candidate_phase.py','run_candidate_tiny.py','REQUEST.UNBOUND.json','README.md']],'phases':9,'groups':['cas','scope','preservation'],'expected_group_exits':[0,1,0],'additional_bound_bytes':16*1024*1024}
p=here/'PINS.json';assert not p.exists();p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(json.dumps(pin(p)))
