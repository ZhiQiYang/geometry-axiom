"""Root-only byte adoption after reviewed and published full original receipts."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, sys

ROOT=Path('/workspace/geometry-axiom')
F8='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
BRANCH='codex/train-337-continue-20261024'
LEDGER=Path('/tmp/geo337-full123-F8-job-20261025/mutants_results.json')
LEDGER_HASH='0123548b29bf8adbaf3cf896bfffb212134452f2574eaf8ae1d1b663104ead1b'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
PROGRESS='evidence/geo337-train-20261024/PROGRESS.md'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,why):
    if not ok:raise RuntimeError(why)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--request-sha256',required=True)
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args()
    need(h(a.request)==a.request_sha256,'request changed')
    request=json.loads(a.request.read_text())
    need(request['source_sha']==F8 and request['root_reviewed_original_and_package'] is True,'wrong source or missing root review')
    before=request['expected_parent'];need(len(before)==40,'full before SHA required')
    need(h(LEDGER)==LEDGER_HASH,'original ledger changed')
    peers=request['required_peer_files']
    need(set(peers)=={'actual_peer','package_peer'},'both named independent peers required')
    for role,item in peers.items():
        need(h(item['path'])==item['sha256'],'peer changed')
        peer=json.loads(Path(item['path']).read_text())
        need(type(peer[item['exit_field']]) is int and peer[item['exit_field']]==0,'peer not accepted')
        need(peer['source_sha']==F8,'peer source differs from F8')
        if role=='actual_peer':
            need(peer['ledger_sha256']==LEDGER_HASH,'actual peer ledger differs')
    need(h(CAP)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762','capture changed')
    need(not a.out.exists(),'fresh output required');a.out.mkdir()
    spec=importlib.util.spec_from_file_location('original_capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
    env={k:v for k,v in os.environ.items() if not k.startswith(('GIT_','MUTATE_')) and k not in ('PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP')}
    env.update(PYTHONDONTWRITEBYTECODE='1',LANG='C.UTF-8',LC_ALL='C.UTF-8',PYTHONIOENCODING='utf-8',GIT_OPTIONAL_LOCKS='0')
    rec=cap.Recorder(a.out,env,F8)
    result={'generated_source_sha':F8,'previous_head':before,'ledger_sha256':LEDGER_HASH,'published':False,'commands':rec.rows,'source_execution_heads_rewritten':False,'formal_other_gates_executed':False,'request_sha256':a.request_sha256}
    cap.dump(a.out/'REQUEST.json',request)
    def run(argv,data=None,sha=None,check=True):
        row,out,err=rec.run(argv,cwd=ROOT,data=data,timeout=None,check=False,source_sha=sha or before,source_variant='byte-identical F8 ledger adoption, normal publication, original F9 tracked check')
        if check:need(row['actual_process_returncode']==0,'command failed; original streams at '+row['directory'])
        return row,out
    def git(*args,sha=None,data=None,check=True):return run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],data=data,sha=sha,check=check)
    def remote():
        _,raw=git('ls-remote','--heads','origin','refs/heads/'+BRANCH)
        lines=raw.splitlines();need(len(lines)==1,'single remote ref required');oid,ref=lines[0].split(b'\t');need(ref.decode()=='refs/heads/'+BRANCH,'wrong remote');return oid.decode()
    def paths(raw):return set(raw.decode().rstrip('\0').split('\0')) if raw else set()
    exit_code=1
    try:
        need(git('branch','--show-current')[1].decode().strip()==BRANCH,'wrong branch')
        need(git('rev-parse','HEAD')[1].decode().strip()==before,'HEAD moved')
        need(not git('status','--porcelain=v1','--untracked-files=all')[1],'dirty root')
        need(remote()==before,'remote moved')
        git('merge-base','--is-ancestor',F8,before)
        delta=paths(git('diff','--no-renames','--name-only','-z',F8,before)[1])
        need(delta and all(p.startswith('evidence/') for p in delta),'product or test changed before adoption')
        # The already-published package/index and both peer receipts must match original bytes.
        bindings=request['published_bindings']
        need(set(bindings)=={'archive','index','actual_peer','package_peer'},'four named public evidence roles required')
        need(len({x['git_path'] for x in bindings.values()})==4,'public evidence roles must be distinct')
        published={}
        for role,item in bindings.items():
            raw=git('show',before+':'+item['git_path'])[1]
            need(hashlib.sha256(raw).hexdigest()==item['sha256'],'published original binding mismatch')
            if role in peers:need(item['sha256']==peers[role]['sha256'],'public peer not same reviewed original')
            if role!='archive':published[role]=json.loads(raw)
        index=published['index']
        need(index['source_sha']==F8 and index['terminal']['formal_accepted'] is True and index['archive_sha256']==bindings['archive']['sha256'],'archive index source or terminal differs')
        need(index['terminal']['terminal_files']['ledger']['sha256']==LEDGER_HASH,'archive ledger identity differs')
        old_progress=(ROOT/PROGRESS).read_bytes()
        new_progress=Path(request['progress_path']).read_bytes()
        need(hashlib.sha256(new_progress).hexdigest()==request['progress_sha256'] and new_progress.startswith(old_progress) and len(new_progress)>len(old_progress),'progress must append exactly to latest bytes')
        old=git('show',before+':tests/mutants_results.json')[1]
        need(hashlib.sha256(old).hexdigest()!=LEDGER_HASH,'ledger must actually change')
        (ROOT/'tests/mutants_results.json').write_bytes(LEDGER.read_bytes())
        (ROOT/PROGRESS).write_bytes(new_progress)
        need(h(ROOT/'tests/mutants_results.json')==LEDGER_HASH,'adopted bytes changed')
        git('add','--update','--','tests/mutants_results.json',PROGRESS)
        need(paths(git('diff','--cached','--no-renames','--name-only','-z')[1])=={'tests/mutants_results.json',PROGRESS},'unexpected staged paths')
        need(hashlib.sha256(git('show',':tests/mutants_results.json')[1]).hexdigest()==LEDGER_HASH,'staged ledger not original')
        git('commit','-m','test: adopt verified F8 ledger for final train acceptance')
        final=git('rev-parse','HEAD')[1].decode().strip();result['final_sha']=final
        need(git('show','-s','--format=%P',final)[1].decode().strip()==before,'final must have exactly the expected single parent')
        need(hashlib.sha256(git('show',final+':tests/mutants_results.json',sha=final)[1]).hexdigest()==LEDGER_HASH,'final committed ledger differs from original')
        need(git('show',final+':'+PROGRESS,sha=final)[1]==new_progress,'final committed progress differs')
        changed=paths(git('diff','--no-renames','--name-only','-z',F8,final,sha=final)[1])
        need('tests/mutants_results.json' in changed and all(p=='tests/mutants_results.json' or p.startswith('evidence/') for p in changed),'F8 to final product/test closure changed')
        need(not git('status','--porcelain=v1','--untracked-files=all',sha=final)[1],'commit not clean')
        pushed,_=git('push','origin','HEAD:refs/heads/'+BRANCH,sha=final,check=False)
        result['push_exit']=pushed['actual_process_returncode']
        if result['push_exit']==0:result['published']=remote()==final
        result['cleared_mutate_environment']=not any(k.startswith('MUTATE_') for k in env)
        row,_=run([sys.executable,'-B','tests/mutate.py','--check'],sha=final,check=False)
        result['tracked_check_exit']=row['actual_process_returncode']
        result['tracked_check_command']=row
        need(git('rev-parse','HEAD',sha=final)[1].decode().strip()==final and not git('status','--porcelain=v1','--untracked-files=all',sha=final)[1],'final tracked check changed checkout')
        result['final_closure']=sorted(changed)
        exit_code=0 if result['published'] and result['tracked_check_exit']==0 else 1
    except BaseException as exc:
        result['error']=repr(exc)
    finally:
        result['exit_code']=exit_code;cap.dump(a.out/'RESULT.json',result)
    print(json.dumps({k:result.get(k) for k in ('final_sha','published','push_exit','tracked_check_exit','exit_code','error')}))
    return exit_code
if __name__=='__main__':sys.exit(main())
