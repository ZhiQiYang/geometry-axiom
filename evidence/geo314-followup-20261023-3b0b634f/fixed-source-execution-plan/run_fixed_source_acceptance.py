#!/usr/bin/env python3
"""Run the original #314 partial gates only after the root grants a resource slot.

No product/judge edits, no full ledger regeneration and no branch mutations.
The only native adapter changes binaries.OUT_DIR, an existing registry output
binding, before calling the unchanged run_all.main with its original arguments.
"""
from pathlib import Path
import argparse, datetime, fcntl, hashlib, importlib.util, json, os, platform
import resource, shutil, sys, traceback

S='3b0b634feb54266700cc61f26c34d7aeac4c0314'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAPSHA='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
SELECTORS=['py:test_geo314_stagger_commit','py:test_geo314_commit_paths',
           'py:test_geo314_ordered_facts','py:test_geo261_wood_grid_application',
           'py:test_geo261_native_grid_product','py:test_grid_inspector_contract']
NATIVE_ARGS=['--build',*[word for selector in SELECTORS for word in ('--only',selector)]]
IDS=['M'+str(i) for i in range(99,122)]
PATTERNS=['/*','!/evidence/','!/tests/evidence/','!/tests/release-evidence/']
NATIVE_BINDING=('import pathlib,sys;sys.path.insert(0,"tests");import binaries;'
 'binaries.OUT_DIR=pathlib.Path(sys.argv[1]);import run_all;'
 'raise SystemExit(run_all.main(sys.argv[2:]))')
h=lambda raw:hashlib.sha256(raw).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--heavy-lock',type=Path,required=True)
    a=ap.parse_args()
    assert not sys.flags.optimize
    assert h(CAP.read_bytes())==CAPSHA
    origin=a.repo.resolve();out=a.out.resolve()
    assert origin.is_dir() and not out.exists() and not out.is_relative_to(origin)
    assert a.heavy_lock.is_file()
    lock=a.heavy_lock.open('a+b')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    out.mkdir();(out/'tmp').mkdir()
    source=out/'source';cache=out/'mutation-cache';ledger=out/'M99-M121-results.json'
    binaries=out/'native-binaries';binaries.mkdir()
    env={k:v for k,v in os.environ.items() if not k.startswith(('GEOMETRY_','MUTATE_','GIT_'))}
    cleared={k:env.pop(k,None) for k in ('PYTHONOPTIMIZE','NODE_OPTIONS','PYTHONPATH','PYTHONSTARTUP')}
    env.update(LANG='C.UTF-8',LC_ALL='C.UTF-8',PYTHONIOENCODING='utf-8',
        PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(out/'tmp'),
        MUTATE_CACHE=str(cache),MUTATE_RESULTS=str(ledger))
    spec=importlib.util.spec_from_file_location('geo314_original_capture',CAP)
    cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
    r=cap.Recorder(out,env,S)
    report=dict(schema='geo314-fixed-committed-source-partial-acceptance/1',sourceSHA=S,
      startedUTC=now(),python=sys.version,platform=platform.platform(),
      sourceRepository=str(origin),checkout=str(source),driverSHA256=h(Path(__file__).read_bytes()),
      recorderSHA256=CAPSHA,commands=r.rows,clearedInheritedEnvironment=cleared,
      environment={k:env.get(k) for k in ('PATH','LANG','LC_ALL','TMPDIR','MUTATE_CACHE','MUTATE_RESULTS','NODE_OPTIONS','PYTHONOPTIMIZE','PYTHONPATH')},
      sparsePatterns=PATTERNS,originalNativeArguments=NATIVE_ARGS,
      nativeOutputBindingOnly=NATIVE_BINDING,globalLedgerRegenerated=False,
      originalPhases=[],errors=[],limitations=[
        'The native selector run is partial and cannot be represented as the complete native workflow.',
        'The original node inspector file uses a native bridge and a VM, not HTTP or Chrome.',
        'Only M99-M121 are executed into a new external result file; this is not the complete project mutation ledger.',
        'Underlying judges may capture internal outputs without persisting them; no omitted streams are reconstructed.'])
    def save(): (out/'receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    def cmd(argv,cwd,timeout=120,check=True):
        return r.run(argv,cwd=cwd,timeout=timeout,check=check,source_variant='fixed-committed-S3b-partial-acceptance')
    def clone(parent,dest):
        dest.parent.mkdir(parents=True,exist_ok=True)
        cmd(['git','clone','--shared','--no-checkout',str(parent),str(dest)],out)
        cmd(['git','sparse-checkout','set','--no-cone',*PATTERNS],dest)
        cmd(['git','-c','core.autocrlf=false','checkout','--detach',S],dest)
    def identity(repo):
        _,head,_=cmd(['git','rev-parse','HEAD'],repo)
        _,status,_=cmd(['git','status','--porcelain=v1','--untracked-files=all'],repo)
        assert head.decode().strip()==S and not status
        return dict(head=head.decode().strip(),status=status.decode())
    def phase(label,argv,timeout,phase_env=None):
        previous=r.env
        if phase_env is not None:r.env=phase_env
        phase_exception=None
        try:row,_,_=cmd(argv,source,timeout=timeout,check=False)
        except Exception:
            phase_exception=traceback.format_exc()
            row=r.rows[-1]
        finally:r.env=previous
        report['originalPhases'].append(dict(label=label,commandResult=row,
          collectionException=phase_exception,
          explicitEnvironment={k:(phase_env or env).get(k) for k in (
            'NODE_OPTIONS','PYTHONOPTIMIZE','TMPDIR','MUTATE_CACHE','MUTATE_RESULTS',
            'GEOMETRY_TEST_BRIDGE','GEOMETRY_263_TRANSCRIPT')}))
        save()
        return row
    soft,hard=resource.getrlimit(resource.RLIMIT_STACK);code=2
    try:
        assert hard==resource.RLIM_INFINITY or hard>=16777216
        resource.setrlimit(resource.RLIMIT_STACK,(16777216,hard))
        report['stackDuring']=list(resource.getrlimit(resource.RLIMIT_STACK))
        report['diskBefore']={str(p):shutil.disk_usage(p)._asdict() for p in (out,origin)}
        _,head,_=cmd(['git','rev-parse',S+'^{commit}'],origin)
        assert head.decode().strip()==S
        clone(origin,source)
        report['sourceBefore']=identity(source)
        report['sourceLedgerSHA256Before']=h((source/'tests/mutants_results.json').read_bytes())
        (out/'driver.py.txt').write_bytes(Path(__file__).read_bytes())
        save()
        # The original aggregate runs every selected suite despite a preceding
        # suite failure. Its own timeouts, expected counts and assertions stand.
        native=phase('original-native-four-suites',
          [sys.executable,'-B','-c',NATIVE_BINDING,str(binaries),*NATIVE_ARGS],7200)
        # This is the unchanged original standalone Node file, not a replacement
        # fixture or a partial extraction of its assertions.
        nodeenv=dict(env,GEOMETRY_TEST_BRIDGE=str(binaries/'bridge'),
            GEOMETRY_263_TRANSCRIPT=str(out/'inspector-transcript.jsonl'))
        phase('original-native-inspector-file',
          ['node','--test','--test-reporter=spec','tests/test_grid_inspector_stagger.cjs'],900,nodeenv)
        # Precreate the exact scratch directory the original runner accepts.
        # This omits only historical evidence trees, while preserving all C/H/
        # INC, tests/*.py, tests/*.c and all tests/fixtures scenes used in hashes.
        scratch=cache/'_bridge-work'/S/'repo'
        clone(source,scratch)
        phase('original-partial-mutation-M99-through-M121',
          [sys.executable,'-B','tests/mutate.py',*IDS],21600)
        proof_problems=[]
        if ledger.exists():
            table=json.loads(ledger.read_text())
            def row_index(i):
                row=table[i];execution=row.get('execution') or {}
                return dict(verdict=row.get('verdict'),why=row.get('why'),
                  executionHead=execution.get('head'),methods=execution.get('methods'),
                  byteRestored=execution.get('byte_restored'),
                  originalExits={k:execution[k].get('exit_code') for k in (
                    'baseline_build','baseline','mutant_build','mutant','restored_build','restored') if k in execution},
                  mutantResult=execution.get('mutant',{}).get('result'),
                  originalRecordPointer='/'+i)
            report['partialMutationRows']={i:row_index(i) for i in IDS if i in table}
            report['partialMutationResultsSHA256']=h(ledger.read_bytes())
            report['partialMutationSelectedIDs']=IDS
            report['partialMutationRecordedSelectedIDs']=[i for i in IDS if i in table]
            if set(table)!=set(IDS):proof_problems.append('External subgroup record IDs do not exactly match M99-M121')
            for identifier in IDS:
                if identifier not in table:continue
                row=table[identifier];execution=row.get('execution') or {}
                expected_verdict='equivalent' if identifier=='M110' else 'killed'
                if row.get('verdict')!=expected_verdict:proof_problems.append(identifier+': original verdict is not '+expected_verdict)
                if execution.get('head')!=S or execution.get('byte_restored') is not True:
                    proof_problems.append(identifier+': original source SHA or exact restoration is incomplete')
                names=('baseline','mutant','restored')
                actual=[execution.get(name,{}).get('exit_code') for name in names]
                if actual!=([0,0,0] if identifier=='M110' else [0,1,0]):
                    proof_problems.append(identifier+': original exits do not satisfy the declared single-withdrawal proof')
                if any(execution.get(name,{}).get('exit_code')!=0 for name in ('baseline_build','mutant_build','restored_build')):
                    proof_problems.append(identifier+': an original build did not finish successfully')
                failures=(execution.get('mutant',{}).get('result') or {}).get('failures')
                if identifier=='M110':
                    if failures!=[]:proof_problems.append(identifier+': the single masked equivalent must not claim a failure')
                elif not failures or any(f.get('kind')!='assertion' for f in failures):
                    proof_problems.append(identifier+': mutation requires normal named assertion failures, not a crash or unproven failure')
                if identifier=='M121':
                    prefix='tests.test_geo314_stagger_commit.StaggerCommit.'
                    methods=[prefix+'test_Q3_same_final_reference_preserves_card_then_unbind_and_rebind_order',
                             prefix+'test_Q3_same_final_reference_cannot_exempt_value_changing_rebind']
                    if execution.get('methods')!=methods or not failures or len(failures)!=1 or failures[0].get('test')!=methods[1]:
                        proof_problems.append('M121: exact positive/negative methods and sole named negative failure must agree')
        else:proof_problems.append('Original partial mutation result file is missing')
        report['mutationProofAccepted']=not proof_problems
        report['mutationProofProblems']=proof_problems
        report['sourceAfter']=identity(source)
        report['scratchAfter']=identity(scratch)
        report['sourceLedgerSHA256After']=h((source/'tests/mutants_results.json').read_bytes())
        assert report['sourceLedgerSHA256Before']==report['sourceLedgerSHA256After']
        # Keep original phase return codes. Do not convert an original failure
        # into success because metadata collection completed.
        code=0 if not proof_problems and all(p['commandResult']['actual_process_returncode']==0 and not p['commandResult']['timeout_expired'] and p['collectionException'] is None for p in report['originalPhases']) else 1
    except Exception:
        report['errors'].append(traceback.format_exc())
    finally:
        report['collectorExit']=code;report['endedUTC']=now()
        report['diskAfter']={str(p):shutil.disk_usage(p)._asdict() for p in (out,origin)}
        save();resource.setrlimit(resource.RLIMIT_STACK,(soft,hard))
        fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
    print(json.dumps(dict(out=str(out),collectorExit=code,
      originalExits={p['label']:p['commandResult']['actual_process_returncode'] for p in report['originalPhases']},errors=report['errors']),ensure_ascii=False))
    return code
if __name__=='__main__':raise SystemExit(main())

