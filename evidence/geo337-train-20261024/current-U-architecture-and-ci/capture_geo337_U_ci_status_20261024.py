from pathlib import Path
import importlib.util,os,json,re,hashlib
O=Path('/workspace/geo337-U-current-required-ci-20261024');O.mkdir()
R=Path('/workspace/geometry-axiom');U='ca7838e0f4950452b9befcf40899d606db9b81fa'
E='b09a34c53ccac652cf0efa3f3e9b4b18ca74d6c5'
p=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
s=importlib.util.spec_from_file_location('cap',p);c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
r=c.Recorder(O,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),U)
def api(endpoint):
 row,out,err=r.run(['gh','api',endpoint],cwd=R,timeout=None,check=False,source_variant='read-only current required CI classification')
 assert row['actual_process_returncode']==0,(endpoint,err)
 return json.loads(out)
summary=[]
for run_id,sha in [(40058889738,U),(40059064935,E)]:
 run=api(f'repos/ZhiQiYang/geometry-axiom/actions/runs/{run_id}')
 assert run['head_sha']==sha and run['head_branch']=='codex/train-337-continue-20261024'
 jobs=api(f'repos/ZhiQiYang/geometry-axiom/actions/runs/{run_id}/jobs?per_page=100')
 assert jobs['total_count']==len(jobs['jobs'])==7
 result={'run_id':run_id,'head_sha':sha,'status':run['status'],'conclusion':run['conclusion'],'jobs':[]}
 for job in jobs['jobs']:
  match=re.fullmatch(r'https://api.github.com/repos/ZhiQiYang/geometry-axiom/check-runs/(\d+)',job['check_run_url']);assert match
  annotations=api(f'repos/ZhiQiYang/geometry-axiom/check-runs/{match.group(1)}/annotations?per_page=100')
  result['jobs'].append({'id':job['id'],'name':job['name'],'conclusion':job['conclusion'],'runner_id':job.get('runner_id'),'runner_name':job.get('runner_name'),'steps_count':len(job['steps']),'annotations':[{'message':a['message'],'level':a['annotation_level']} for a in annotations]})
 summary.append(result)
c.dump(O/'SUMMARY.json',{'product_source':U,'evidence_head':E,'runs':summary,'environment_fixed':False,'formal_substitution_accepted':False,'required_checks_passed':False})
for run in summary:
 print(json.dumps({'run_id':run['run_id'],'head_sha':run['head_sha'],'job_count':len(run['jobs']),'conclusions':[j['conclusion'] for j in run['jobs']],'step_counts':[j['steps_count'] for j in run['jobs']],'annotation_messages':sorted({a['message'] for j in run['jobs'] for a in j['annotations']})},ensure_ascii=False))
