"""Explicit ledger-only F9 binding for original Q38 / card-reference / GEO323 gates; no new judge."""
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
from binding_guards import F8, validate_counts, validate_q38_source, validate_delta

HERE=Path(__file__).resolve().parent
CAPTURE=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
REAPER=Path('/workspace/geo261-environment/reap_children.py')
V5=Path('/workspace/geo323-recorder-fidelity-v5-draft-20261024/tools-v5')
BASE='b74f9a2ae7ade1555b9be45283adecc097fb76e3'
MAIN='adbaebf9c73ea6801d7b4d5214e4b846b132923b'
GATES=('q38','cardref','axiom','required-eight','pf3')

def sha(body):return hashlib.sha256(body).hexdigest()
def need(ok,message):
    if not ok:raise RuntimeError(message)
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gate',choices=(*GATES,'all'),required=True)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--sha',required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--heavy-lock',type=Path,required=True)
    p.add_argument('--preparation-sha256',required=True)
    a=p.parse_args();repo=a.repo.resolve();out=a.out.resolve();heavy=a.heavy_lock.resolve()
    need(len(a.sha)==40 and all(c in '0123456789abcdef'for c in a.sha),'explicit full final F9 required')
    need(repo.is_dir()and(repo/'.git').is_dir()and not(repo/'.git').is_symlink(),'independent private .git directory required; no browser pool/worktree')
    need(out.parent.is_dir()and not out.exists(),'fresh output with existing parent required')
    need(out.is_relative_to(Path('/workspace'))or out.is_relative_to(Path('/tmp')),'private workspace/tmp output only')
    for protected in (repo,HERE,V5):need(not out.is_relative_to(protected)and not protected.is_relative_to(out),'output/source/tools must not overlap')
    need(heavy.is_file()and not heavy.is_relative_to(repo),'existing external root heavy lock required')
    prep_raw=(HERE/'PREPARATION.json').read_bytes();need(sha(prep_raw)==a.preparation_sha256,'reviewed preparation pin')
    prep=json.loads(prep_raw)
    for item in prep['files']:need(sha((HERE/item['path']).read_bytes())==item['sha256'],'preparation file changed '+item['path'])
    for item in prep['external_tools']:
        path=Path(item['path']);need(path.stat().st_size==item['bytes']and sha(path.read_bytes())==item['sha256'],'original tool changed '+str(path))
    need(not sys.flags.optimize,'Python optimize disables original assertions')
    out.mkdir();(out/'tmp').mkdir()
    env={k:v for k,v in os.environ.items()if not k.startswith(('GIT_','GEOMETRY_','MUTATE_','GEO261_','GEO323_'))}
    for key in ('PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','NODE_OPTIONS','LD_PRELOAD','AXIOM_ONLY','FRAMING_QUOTE_QUEUE'):env.pop(key,None)
    env.update(PATH='/workspace/geo261-environment/bin:/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin:'+env.get('PATH',''),LANG='C.UTF-8',LC_ALL='C.UTF-8',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',TMPDIR=str(out/'tmp'),GITHUB_SHA=a.sha,GITHUB_WORKSPACE=str(repo))
    spec=importlib.util.spec_from_file_location('nonperf_original_c387',CAPTURE);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
    recorder=cap.Recorder(out,env,a.sha)
    r={'schema':'train337-final-original-nonperf-specials/1','source_sha':a.sha,'repo':str(repo),'argv':sys.argv,'preparation_sha256':a.preparation_sha256,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{k:env.get(k)for k in ('PATH','LANG','LC_ALL','TMPDIR','GITHUB_SHA','GITHUB_WORKSPACE','PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','NODE_OPTIONS','LD_PRELOAD','AXIOM_ONLY','FRAMING_QUOTE_QUEUE','CC','CFLAGS','CPPFLAGS','LDFLAGS')},'commands':recorder.rows,'gates':[],'errors':[],'passed':False,'outer_timeout':None,'original_judges_counts_limits_changed':False,'source_lease':'root exclusive ownership of this checkout; no native/ledger/browser consumer while any gate runs','source_writes':{'q38':'disposable copies only','cardref':'temporarily edits checkout; original finally restores','axiom':'temporarily edits checkout; original finally restores','required-eight':'original tests build and run; exclusive /tmp/geometry-tests shared with native','pf3':'disposable source copies inside output only'}}
    def run(argv,variant='original-final-special',check=False):
        return recorder.run(argv,cwd=repo,timeout=None,check=check,source_sha=a.sha,source_variant=variant)
    def identity(folder,label):
        values={}
        for key,argv in [('head',['git','rev-parse','HEAD']),('tree',['git','rev-parse','HEAD^{tree}']),('status',['git','status','--porcelain=v1','--untracked-files=all']),('diff',['git','diff','--exit-code']),('index',['git','ls-files','--stage','-z']),('refs',['git','for-each-ref','--format=%(refname) %(objectname)'])]:
            row,body,_=run(argv,'source-identity');need(row['actual_process_returncode']==0,'original Git identity command failed');values[key]=body
        need(values['head'].decode().strip()==a.sha and not values['status']and not values['diff'],'exact clean final F9 required; no reset/clean performed')
        row,_,_=run(['git','merge-base','--is-ancestor',F8,a.sha],'ledger-only-source-ancestry')
        ancestor_exit=row['actual_process_returncode']
        delta_row,delta,_=run(['git','diff','--no-renames','--name-only','-z',F8,a.sha],'ledger-only-source-delta')
        need(delta_row['actual_process_returncode']==0,'F8/F9 closure Git diff failed')
        closure=validate_delta(a.sha,ancestor_exit,[p.decode('utf-8') for p in delta.split(b'\0') if p])
        result={'head':a.sha,'tree':values['tree'].decode().strip(),'status':'','index_sha256':sha(values['index']),'refs_sha256':sha(values['refs']),'ledger_only_closure':closure};save(folder/(label+'-source.json'),result);return result
    def original(folder,name,argv,internal_reaper=False):
        item={'name':name,'original_argv':argv,'primary_command_exit':None,'outer_process_exit':None,'uses_original_internal_reaper':internal_reaper}
        current['commands'].append(item);save(out/'receipt.json',r)
        if internal_reaper:
            item['environment_explicit']={k:env.get(k)for k in ('TMPDIR','GEOMETRY_MODEL_BASE','GEO261_REAPER_LOG','GITHUB_SHA','GITHUB_WORKSPACE','PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','NODE_OPTIONS','LD_PRELOAD','AXIOM_ONLY')}
            row,_,_=run(argv);item.update(primary_command_exit=row['actual_process_returncode'],outer_process_exit=row['actual_process_returncode'],capture=row)
        else:
            log=folder/(name+'-reaper.jsonl');need(not log.exists(),'fresh original reaper log')
            env['GEO261_REAPER_LOG']=str(log)
            item['environment_explicit']={k:env.get(k)for k in ('TMPDIR','GEOMETRY_MODEL_BASE','GEO261_REAPER_LOG','GITHUB_SHA','GITHUB_WORKSPACE','PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','NODE_OPTIONS','LD_PRELOAD','AXIOM_ONLY')}
            row,_,_=run([sys.executable,'-B',str(REAPER),*argv]);item.update(outer_process_exit=row['actual_process_returncode'],capture=row,reaper_log=str(log))
            events=[json.loads(line)for line in log.read_text().splitlines()];terminal=[e for e in events if e.get('event')=='完成']
            need(len(terminal)==1 and events[-1]is terminal[0]and type(terminal[0].get('primary_returncode'))is int,'unique real original reaper terminal required')
            primary=terminal[0]['primary_returncode'];item.update(primary_command_exit=primary,reaper_sha256=sha(log.read_bytes()))
            need(row['actual_process_returncode']==(primary if primary>=0 else 128-primary),'reaper must preserve original primary exit')
        save(out/'receipt.json',r);return item['primary_command_exit']
    soft,hard=resource.getrlimit(resource.RLIMIT_STACK);code=2
    try:
        need(hard==resource.RLIM_INFINITY or hard>=16777216,'16MiB stack unavailable');resource.setrlimit(resource.RLIMIT_STACK,(16777216,hard));r['stack_before']=[soft,hard];r['stack_during']=list(resource.getrlimit(resource.RLIMIT_STACK))
        for gate in GATES if a.gate=='all'else(a.gate,):
            folder=out/gate;folder.mkdir();(folder/'tmp').mkdir();env['TMPDIR']=str(folder/'tmp');env.pop('GEOMETRY_MODEL_BASE',None);env.pop('GEO261_REAPER_LOG',None)
            current={'gate':gate,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':[],'passed':False,'errors':[]};r['gates'].append(current);save(out/'receipt.json',r)
            before=None;lock=None
            try:
                if gate not in ('required-eight','pf3'):
                    lock=heavy.open('a+b');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                before=identity(folder,'before')
                for relative,pin in prep['original_judges_sha256'].items():
                    row,body,_=run(['git','show',a.sha+':'+relative],'original-final-judge-identity');need(row['actual_process_returncode']==0 and sha(body)==pin and(repo/relative).read_bytes()==body,'final original judge/registry bytes changed '+relative)
                if gate=='q38':
                    current['original_q38_case_ids']=validate_q38_source((repo/'tests/section_profile_mutation_check.py').read_bytes())
                    (folder/'q38').mkdir();env['GEOMETRY_MODEL_BASE']=str(folder/'q38-bin/model-base')
                    build=[sys.executable,'-B','-c','from pathlib import Path; import sys; from tests import binaries; binaries.OUT_DIR=Path(sys.argv[1]); raise SystemExit(binaries.main(["build","model-base"]))',str(folder/'q38-bin')]
                    build_exit=original(folder,'model-base-build',build)
                    if build_exit==0:
                        original(folder,'q38',[sys.executable,'-B','-u','tests/section_profile_mutation_check.py','--receipt',str(folder/'q38/receipt.json'),'--logs',str(folder/'q38/logs'),'--jobs','1'])
                    else:current['not_run_reason']='Q38 original model-base prerequisite build nonzero; no subject result invented'
                elif gate in ('cardref','axiom'):
                    script='run_mutations.py'if gate=='cardref'else'run_axiom_mutations.py'
                    original(folder,gate,[sys.executable,'-B','-u','geometry-core/card-reference/'+script,'--output',str(folder/'subject')])
                else:
                    counts=json.loads((repo/'tests/run_all.expected.json').read_text())['suites']
                    selected_count=validate_counts(counts,prep['required_eight_expected'])
                    current['original_selected_registered_count']=selected_count if gate=='required-eight'else None
                    argv=[sys.executable,'-B',str(V5/'run.py'),'--repo',str(repo),'--sha',a.sha,'--base',BASE,'--main',MAIN,'--out',str(folder/'subject'),'--heavy-lock',str(heavy),'--stage',gate]
                    original(folder,gate,argv,internal_reaper=True)
                    receipt=json.loads((folder/'subject/receipt.json').read_text());current['original_stage_receipt_sha256']=sha((folder/'subject/receipt.json').read_bytes());current['original_stage_execution_exit']=receipt['stages'][gate]['execution_exit']
                    need(current['original_stage_execution_exit']==0 and receipt['wrapper_exit']==0,'original GEO323 stage/wrapper nonzero; raw preserved')
                need(current['commands']and all(item['primary_command_exit']==0 for item in current['commands'])and'not_run_reason'not in current,'original command nonzero or prerequisite blocked')
                current['passed']=True
            except BaseException:
                current['errors'].append(traceback.format_exc());current['passed']=False
            finally:
                try:
                    after=identity(folder,'after');need(before is None or after==before,'final source/index/refs did not restore')
                except BaseException:current['errors'].append(traceback.format_exc());current['passed']=False
                if lock is not None:lock.close()
                current['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(out/'receipt.json',r)
        need(all(sha((HERE/item['path']).read_bytes())==item['sha256']for item in prep['files']),'frozen preparation changed during gates')
        for item in prep['external_tools']:need(sha(Path(item['path']).read_bytes())==item['sha256'],'original frozen external tool changed during gates')
        r['passed']=bool(r['gates'])and all(row['passed']for row in r['gates']);code=0 if r['passed']else 1
    except BaseException:r['errors'].append(traceback.format_exc());r['passed']=False;code=2
    finally:
        resource.setrlimit(resource.RLIMIT_STACK,(soft,hard));r.update(launcher_exit_code=code,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());save(out/'receipt.json',r)
    print(json.dumps({'source_sha':a.sha,'gates':[{'gate':x['gate'],'passed':x['passed']}for x in r['gates']],'launcher_exit_code':code,'receipt':str(out/'receipt.json')},ensure_ascii=False),flush=True)
    return code

if __name__=='__main__':raise SystemExit(main())
