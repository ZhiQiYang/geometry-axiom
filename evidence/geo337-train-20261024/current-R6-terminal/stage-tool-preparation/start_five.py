"""Record fresh admission and the single original five-stage launcher."""
from pathlib import Path
import argparse,json,re,sys,traceback
from prepare_source import Recorder,clean_env,need
HERE=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('--sha',required=True);a=p.parse_args();S=a.sha;need(re.fullmatch('[0-9a-f]{40}',S),'full root-selected new R6 source required')
 out=HERE/'outer-five';out.mkdir(exist_ok=False);env=clean_env();rec=Recorder(out,S,env);request=json.loads((HERE/'REQUEST.json').read_bytes());root=Path(request['source_checkout']);result={'source_sha':S,'commands':rec.rows,'exit':None}
 try:
  need(request['source_sha']==S,'one fixed public R');rec.run(['df','-B1','/workspace','/tmp'],root)
  rec.run([sys.executable,'-B',str(HERE/'launch_stages.py'),'--sha',S,'--stage','five'],root);result['exit']=0
 except BaseException:
  result['error']=traceback.format_exc();result['exit']=rec.rows[-1]['actual_exit'] if rec.rows and rec.rows[-1]['actual_exit']!=0 else 1
 finally:(out/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'source_sha':S,'exit':result['exit'],'original_commands':len(rec.rows)}),flush=True)
 return result['exit']
if __name__=='__main__':sys.exit(main())
