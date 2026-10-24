"""Schedule original five stages exclusively; never change the original judges."""
from pathlib import Path
import argparse,datetime,fcntl,json,os,re,subprocess,sys
from prepare_source import clean_env,pins_ok,sha,need
HERE=Path(__file__).resolve().parent
STAGES=('prepare','build','compare','perf','profile')
def main():
    p=argparse.ArgumentParser();p.add_argument('--sha',required=True);p.add_argument('--stage',choices=(*STAGES,'five'),default='five');a=p.parse_args()
    need(re.fullmatch('[0-9a-f]{40}',a.sha),'full final source SHA required')
    request=json.loads((HERE/'REQUEST.json').read_text());prep=json.loads((HERE/'preparation/RESULT.json').read_text())
    need(prep['exit']==0 and prep['source_sha']==request['source_sha']==a.sha,'one actual prepared source SHA')
    root=Path(request['source_checkout']);target=Path(request['acceptance_out'])
    selected=STAGES if a.stage=='five'else(a.stage,)
    journal=HERE/('launch-'+a.stage);need(not journal.exists(),'fresh launcher receipt; never overwrite a previous attempt')
    journal.mkdir();locks=[];env=clean_env();rows=[]
    report={'source_sha':a.sha,'base':request['base'],'main':request['main'],'stages':list(selected),'original_judges_modified':False,'commands':rows,'exit':None,'locks':request['global_locks'],'environment':{key:env.get(key)for key in ('PATH','LANG','LC_ALL','TMPDIR','PYTHONDONTWRITEBYTECODE','PYTHONIOENCODING')}}
    try:
        pins_ok(request)
        for path in request['global_locks']:
            handle=Path(path).open('a+');fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(handle)
        git=lambda *args:subprocess.run(['git','-C',str(root),*args],env=env,capture_output=True,check=True).stdout
        need(git('rev-parse','HEAD').decode().strip()==a.sha and git('status','--porcelain=v1','--untracked-files=all')==b'','exact clean prepared source')
        for item in prep['entries']:need(sha((root/item['path']).read_bytes())==item['sha256'],'prepared source changed '+item['path'])
        # Global primary and secondary stay held here. The unchanged original child
        # uses its own lock so it does not deadlock against its parent's lock.
        for stage in selected:
            pins_ok(request)
            command=[sys.executable,'-B',str(Path(request['original_tools'])/'run.py'),'--repo',str(root),'--sha',a.sha,'--base',request['base'],'--main',request['main'],'--out',str(target),'--heavy-lock',request['inner_lock'],'--stage',stage]
            folder=journal/stage;folder.mkdir()
            started=datetime.datetime.now(datetime.timezone.utc).isoformat();print('START '+stage,flush=True)
            with(folder/'stdout').open('wb')as stdout,(folder/'stderr').open('wb')as stderr:
                result=subprocess.run(command,cwd=root,env=env,stdout=stdout,stderr=stderr)
            row={'command':command,'cwd':str(root),'source_sha':a.sha,'stage':stage,'started_utc':started,'actual_process_exit':result.returncode,'stdout_sha256':sha((folder/'stdout').read_bytes()),'stderr_sha256':sha((folder/'stderr').read_bytes())}
            receipt=target/'receipt.json'
            if receipt.exists():
                original=json.loads(receipt.read_text());row['original_stage']=original.get('stages',{}).get(stage);row['original_quantitative_targets']=original.get('quantitative_targets');row['original_full_acceptance_passed']=original.get('full_acceptance_passed')
            rows.append(row);(folder/'result.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
            print('END '+stage+' actual_exit='+str(result.returncode),flush=True)
            # Original compare/perf red does not prevent collection of remaining stages.
        report['exit']=0 if all(row['actual_process_exit']==0 for row in rows)else 1
        report['full_acceptance_claim']=False
    except BaseException as exc:report.update(exit=1,error=repr(exc))
    finally:
        for handle in reversed(locks):fcntl.flock(handle,fcntl.LOCK_UN);handle.close()
        (journal/'RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'source_sha':a.sha,'launcher_exit':report['exit'],'original_stages_recorded':len(rows)}),flush=True)
    return report['exit']
if __name__=='__main__':sys.exit(main())
