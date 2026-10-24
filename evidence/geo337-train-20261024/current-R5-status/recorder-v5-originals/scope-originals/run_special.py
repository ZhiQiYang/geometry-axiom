"""Bind one original formal special to explicit final L; preparation is not execution."""
import argparse
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys
import traceback

HERE=Path(__file__).resolve().parent
MAIN='adbaebf9c73ea6801d7b4d5214e4b846b132923b'
BASE='3e600772076465fc65a26ac09055028301c0fb0b'
CAPTURE=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
REAPER=Path('/workspace/geo261-environment/reap_children.py')

def h(body):return hashlib.sha256(body).hexdigest()
def need(ok,message):
    if not ok:raise RuntimeError(message)
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gate',choices=['p52','p189','p189-timing'],required=True)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--sha',required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--heavy-lock',type=Path,required=True)
    p.add_argument('--main-repo',type=Path,default=Path('/workspace/geo288-main-merge-20261023/reference/main'))
    p.add_argument('--preparation-sha256',required=True)
    p.add_argument('--p189-full-out',type=Path)
    a=p.parse_args();repo=a.repo.resolve();out=a.out.resolve();main_repo=a.main_repo.resolve()
    need(len(a.sha)==40 and all(c in '0123456789abcdef'for c in a.sha)and a.sha not in (MAIN,BASE),'explicit full final SHA required')
    need(repo.is_dir()and(repo/'.git').is_dir(),'independent clean final Git checkout required')
    need(not out.exists()and out.parent.is_dir(),'fresh out with existing parent required')
    need(out.is_relative_to(Path('/workspace'))or out.is_relative_to(Path('/tmp')),'private workspace/tmp only')
    for protected in (repo,main_repo,HERE):
        need(not out.is_relative_to(protected)and not protected.is_relative_to(out),'out/source/tools must not overlap')
    if a.gate=='p52':need(out.is_relative_to(Path('/tmp')),'unchanged P52 formal requires short private /tmp out')
    prep_path=HERE/'PREPARATION.json';prep_raw=prep_path.read_bytes()
    need(h(prep_raw)==a.preparation_sha256,'static reviewed preparation pin')
    prep=json.loads(prep_raw)
    for item in prep['files']:
        path=HERE/item['path'];need(path.is_file()and path.stat().st_size==item['bytes']and h(path.read_bytes())==item['sha256'],'frozen tool changed '+item['path'])
    need(h(CAPTURE.read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762','original c387 pin')
    need(h(REAPER.read_bytes())=='7d848d6c135b7f329852d16c6da5743effde8b29ccbbc6e70092b6ba25877760','original reaper pin')
    need(a.heavy_lock.is_file(),'existing root heavy lock required')
    out.mkdir();(out/'tmp').mkdir()
    env={k:v for k,v in os.environ.items()if not k.startswith(('GIT_','GEOMETRY_','P52_','GEO261_P189_'))}
    for k in ['PYTHONOPTIMIZE','PYTHONPATH','PYTHONSTARTUP','NODE_OPTIONS','LD_PRELOAD','AXIOM_ONLY']:env.pop(k,None)
    env.update(PATH='/workspace/geo261-environment/bin:/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',LANG='C.UTF-8',LC_ALL='C.UTF-8',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(out/'tmp'),GITHUB_SHA=a.sha,GITHUB_WORKSPACE=str(repo),GEO261_FINAL_REPO=str(repo))
    spec=importlib.util.spec_from_file_location('special_c387',CAPTURE);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
    r=cap.Recorder(out,env,a.sha)
    record={'schema':'train337-original-final-special/1','source_sha':a.sha,'gate':a.gate,'repo':str(repo),'out':str(out),'main':MAIN,'base':BASE if a.gate.startswith('p189')else None,'argv':sys.argv,'preparation_sha256':a.preparation_sha256,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{k:env.get(k)for k in ['PATH','LANG','LC_ALL','TMPDIR','GITHUB_SHA','GITHUB_WORKSPACE','PYTHONOPTIMIZE','NODE_OPTIONS','PYTHONPATH','LD_PRELOAD','AXIOM_ONLY','CC','CFLAGS','CPPFLAGS','LDFLAGS']},'source_mutation_authorized':False,'commands':r.rows,'phases':[],'errors':[],'passed':False,'original_timeouts_and_thresholds_changed':False}
    def run(argv,variant='final-original-special',check=True):
        row,stdout,stderr=r.run(argv,cwd=repo,timeout=None,check=check,source_sha=a.sha,source_variant=variant)
        return row,stdout,stderr
    def identity(label):
        values={}
        for key,argv in [('head',['git','rev-parse','HEAD']),('tree',['git','rev-parse','HEAD^{tree}']),('status',['git','status','--porcelain=v1','--untracked-files=all']),('index',['git','ls-files','--stage','-z']),('refs',['git','for-each-ref','--format=%(refname) %(objectname)'])]:
            _,stdout,_=run(argv,'source-identity');values[key]=stdout
        need(values['head'].decode().strip()==a.sha and values['status']==b'','final source must be exact and clean')
        result={'head':values['head'].decode().strip(),'tree':values['tree'].decode().strip(),'status':values['status'].decode(),'index_sha256':h(values['index']),'refs_sha256':h(values['refs'])};save(out/(label+'-source.json'),result);return result
    def phase(name,argv):
        log=out/(name+'-reaper.jsonl');need(not log.exists(),'fresh per-command reaper log')
        env['GEO261_REAPER_LOG']=str(log)
        row,stdout,stderr=run([sys.executable,'-B',str(REAPER),*argv],check=False)
        item={'name':name,'original_argv':argv,'outer_command':row,'reaper_log':str(log),'primary_returncode':None};record['phases'].append(item)
        events=[json.loads(line)for line in log.read_text().splitlines()]
        completed=[event for event in events if event.get('event')=='完成']
        need(len(completed)==1 and events[-1]is completed[0]and type(completed[0].get('primary_returncode'))is int,'unique real terminal primary exit required')
        primary=completed[0]['primary_returncode'];item['primary_returncode']=primary;item['reaper_sha256']=h(log.read_bytes())
        need(row['actual_process_returncode']==(primary if primary>=0 else 128-primary),'reaper must preserve original primary exit')
        return primary
    lock=None;code=2;before=None
    soft,hard=resource.getrlimit(resource.RLIMIT_STACK)
    try:
        need(hard==resource.RLIM_INFINITY or hard>=16777216,'16MiB stack unavailable');resource.setrlimit(resource.RLIMIT_STACK,(16777216,hard));record['stack_before']=[soft,hard];record['stack_during']=list(resource.getrlimit(resource.RLIMIT_STACK))
        if a.gate.startswith('p189'):
            lock=a.heavy_lock.open('a+b');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # Unchanged P52 formal takes this same R3 lock itself; never double-lock.
        before=identity('before')
        if a.gate=='p52':
            rc=phase('formal',[sys.executable,'-B',str(HERE/'p52/p52-formal.py'),'--repo',str(repo),'--main-repo',str(main_repo),'--sha',a.sha,'--out',str(out/'formal'),'--heavy-lock',str(a.heavy_lock)])
            verify_rc=phase('verifier',[sys.executable,'-B',str(HERE/'p52-verifier/run.py'),'--sha',a.sha,'--formal-out',str(out/'formal'),'--out',str(out/'verifier')])
            code=0 if (rc,verify_rc)==(0,0)else 1
        else:
            env.update(GEO261_P189_OUT=str(out/'measurement'),GEO261_P189_WORK=str(out/'work'))
            record['original_p189_path_bindings']={k:env[k]for k in ['GEO261_P189_OUT','GEO261_P189_WORK','GEO261_FINAL_REPO']}
            if a.gate=='p189-timing':
                need(a.p189_full_out is not None,'explicit original P189 full red output required')
                prior=a.p189_full_out.resolve()
                need(prior.is_dir()and not out.is_relative_to(prior)and not prior.is_relative_to(out),'new timing out cannot modify original full raw')
                env['GEO261_P189_FULL_OUT']=str(prior)
                record.update(scope='independent timing only; never full P189 green',overall_P189_passed=False,original_full_out=str(prior))
                script=HERE/'p189/timing_only_after_dump_red.py'
            else:script=HERE/'p189/p189_verify.py'
            primary=phase(a.gate,[sys.executable,'-B','-u',str(script),a.sha])
            code=primary if primary>=0 else 128-primary
            provenance_path=out/'measurement/provenance.json'
            if provenance_path.exists():
                prov=json.loads(provenance_path.read_bytes());binary_checks=[]
                for label,wanted in prov['binaries_sha256'].items():
                    path=out/'work'/label/'bridge';actual=h(path.read_bytes());binary_checks.append({'side':label,'path':str(path),'sha256':actual,'matches_original_record':actual==wanted})
                record['after_binary_checks']=binary_checks;need(all(x['matches_original_record']for x in binary_checks),'P189 binary bytes changed after execution')
        record['passed']=code==0
    except BaseException:
        record['errors'].append(traceback.format_exc());record['passed']=False;code=2
    finally:
        try:
            after=identity('after')
            if before is not None:need(after==before,'final source/index/refs changed')
            for item in prep['files']:need(h((HERE/item['path']).read_bytes())==item['sha256'],'frozen tool changed during execution')
        except BaseException:record['errors'].append(traceback.format_exc());record['passed']=False;code=2
        if lock is not None:lock.close()
        resource.setrlimit(resource.RLIMIT_STACK,(soft,hard))
        record.update(ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),launcher_exit_code=code)
        save(out/'receipt.json',record)
    print(json.dumps({'gate':a.gate,'sha':a.sha,'passed':record['passed'],'launcher_exit_code':code,'receipt':str(out/'receipt.json')},ensure_ascii=False),flush=True)
    return code
if __name__=='__main__':raise SystemExit(main())
