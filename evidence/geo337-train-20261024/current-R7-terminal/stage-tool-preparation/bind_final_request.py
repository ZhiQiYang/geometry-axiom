"""Bind root's final R without materializing its checkout or executing C."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess
HERE=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('--sha',required=True);a=p.parse_args()
 if not re.fullmatch('[0-9a-f]{40}',a.sha):raise RuntimeError('full root-selected final R required')
 original=(HERE/'REQUEST.unbound.json').read_bytes();request=json.loads(original)
 if json.loads((HERE/'REQUEST.template.json').read_bytes())!=request:raise RuntimeError('request already bound; do not rewrite')
 if any(Path(request[n]).exists()for n in ('source_checkout','acceptance_out'))or(HERE/'preparation').exists():raise RuntimeError('source/preparation/output must remain fresh')
 out=HERE/'binding';out.mkdir(exist_ok=False)
 from prepare_source import Recorder,clean_env,need,pins_ok
 rec=Recorder(out,a.sha,clean_env());root=Path(request['source_owner_repo']);pins_ok(request)
 def git(*args):return rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],root)
 need(git('rev-parse',a.sha+'^{commit}').decode().strip()==a.sha,'actual selected commit exists')
 git('merge-base','--is-ancestor','1449d430d1c4734bb1bc3a9f91f3851c845cc0f3',a.sha)
 request['selected_final_source']=a.sha;request['status']='FINAL_R_BOUND_ONLY; source/materialization and five stages UNRUN'
 (HERE/'REQUEST.template.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
 result={'source_sha':a.sha,'source_materialized':False,'formal_run':False,'original_unbound_sha256':hashlib.sha256(original).hexdigest(),'bound_request_sha256':hashlib.sha256((HERE/'REQUEST.template.json').read_bytes()).hexdigest(),'commands':rec.rows,'exit':0}
 (out/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'source_sha':a.sha,'source_materialized':False,'formal_run':False,'exit':0}))
if __name__=='__main__':main()
