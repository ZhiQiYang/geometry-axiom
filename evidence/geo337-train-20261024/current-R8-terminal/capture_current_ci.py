from pathlib import Path
import importlib.util,os,json,re,hashlib
O=Path('/tmp/geo337-F8-E815-current-required-ci-20261025');O.mkdir();R=Path('/workspace/geometry-axiom');F='75a1e93811a52b69385cbdaf6a09d773ed9052ad';E='815cd2e348e47e1666371aff5060820ff29a913a'
p=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');assert hashlib.sha256(p.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762';s=importlib.util.spec_from_file_location('cap',p);c=importlib.util.module_from_spec(s);s.loader.exec_module(c);r=c.Recorder(O,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),F)
def api(endpoint):
 row,out,err=r.run(['gh','api',endpoint],cwd=R,timeout=None,check=False,source_variant='read-only current required CI classification');assert row['actual_process_returncode']==0,(endpoint,err);return json.loads(out)
summary=[]
for sha in [F,E]:
 listing=api('repos/ZhiQiYang/geometry-axiom/actions/runs?head_sha='+sha+'&per_page=100');matching=[x for x in listing['workflow_runs'] if x['path']=='.github/workflows/integration-tests.yml'];assert len(matching)<=1
 if not matching:summary.append({'head_sha':sha,'run_present':False,'required_jobs_green':False});continue
 run=matching[0];assert run['head_sha']==sha and run['head_branch']=='codex/train-337-continue-20261024';run_id=run['id'];jobs=api(f'repos/ZhiQiYang/geometry-axiom/actions/runs/{run_id}/jobs?per_page=100');assert jobs['total_count']==len(jobs['jobs'])
 result={'run_id':run_id,'head_sha':sha,'status':run['status'],'conclusion':run['conclusion'],'jobs':[]}
 for job in jobs['jobs']:
  match=re.fullmatch(r'https://api.github.com/repos/ZhiQiYang/geometry-axiom/check-runs/(\d+)',job['check_run_url']);assert match
  annotations=api(f'repos/ZhiQiYang/geometry-axiom/check-runs/{match.group(1)}/annotations?per_page=100')
  result['jobs'].append({'id':job['id'],'name':job['name'],'conclusion':job['conclusion'],'runner_id':job.get('runner_id'),'runner_name':job.get('runner_name'),'steps_count':len(job['steps']),'annotations':[{'message':x['message'],'level':x['annotation_level']} for x in annotations]})
 result['required_jobs_green']=len(result['jobs'])==7 and all(x['conclusion']=='success' for x in result['jobs']);summary.append(result)
c.dump(O/'SUMMARY.json',{'product_source':F,'evidence_head':E,'runs':summary,'environment_fixed_by_this_task':False,'formal_substitution_accepted':False,'required_checks_passed':all(x['required_jobs_green'] for x in summary)})
for x in summary:print(json.dumps({'head':x['head_sha'],'run_id':x.get('run_id'),'jobs':len(x.get('jobs',[])),'green':x['required_jobs_green'],'messages':sorted({a['message'] for j in x.get('jobs',[]) for a in j['annotations']})},ensure_ascii=False))
