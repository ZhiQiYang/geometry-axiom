"""Bind each original core attempt to its own complete observed run_tests call."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ledger',type=Path,required=True)
    p.add_argument('--observations',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    ledger=json.loads(a.ledger.read_text())
    request=json.loads((a.observations/'request.json').read_text())
    observer=json.loads((a.observations/'receipt.json').read_text())
    failures=[]
    if not observer.get('observer_complete') or not observer.get('original_completed') or observer.get('original_exit')!=0:
        failures.append('observer/original CLI did not complete successfully')
    if observer.get('source_sha')!=request['source_sha']:
        failures.append('observer/request source SHA mismatch')
    if Path(request['environment']['MUTATE_RESULTS']).resolve()!=a.ledger.resolve():
        failures.append('ledger path differs from original request MUTATE_RESULTS')
    root=Path(request['root']).resolve()
    cache=Path(request['environment']['MUTATE_CACHE']).resolve()
    python=request['python_executable']
    runner=str(root/'tests/run_tests.py')
    observed=[]
    all_core_observations=[]
    seen_numbers=set()
    for row in sorted(observer['commands'],key=lambda r:r['number']):
        if row['number'] in seen_numbers:
            failures.append('duplicate observed command number '+str(row['number']))
        seen_numbers.add(row['number'])
        pos=row.get('args',[])
        command=pos[0] if pos else row.get('keyword_arguments_except_env',{}).get('args')
        if not isinstance(command,list) or len(command)!=3 or command[:2]!=[python,runner]:
            continue
        all_core_observations.append({'command_number':row['number'],'command':command,
                                      'completed_process_returned':row.get('completed_process_returned'),
                                      'returncode':row.get('returncode'),'exception':row.get('exception')})
        valid=(row.get('completed_process_returned') and row.get('exception') is None
               and row.get('keyword_arguments_except_env',{}).get('cwd')==str(root)
               and row.get('selected_environment',{}).get('MUTATE_CACHE')==request['environment']['MUTATE_CACHE'])
        if not row.get('completed_process_returned'):
            continue
        for stream in ['stdout','stderr']:
            entry=row.get(stream,{})
            if not entry.get('captured'):
                valid=False
                continue
            try:
                body=Path(entry['path']).read_bytes()
                if len(body)!=entry['bytes'] or hashlib.sha256(body).hexdigest()!=entry['sha256']:
                    valid=False
            except (KeyError,OSError):
                valid=False
        if valid:
            observed.append((command[2],row))
        else:
            failures.append('incomplete/foreign observed original run_tests command '+str(row['number']))
    def matches(row,expected):
        return (isinstance(expected,dict) and row['returncode']==expected.get('exit_code')
                and row['stdout']['sha256']==expected.get('stdout_sha256')
                and row['stderr']['sha256']==expected.get('stderr_sha256'))
    def mapped(row):
        return {'command_number':row['number'],'original_args':row['args'],
                'returncode':row['returncode'],'stdout':row['stdout'],'stderr':row['stderr']}
    binary_cache={}
    def binary_identity(path,expected):
        if not path.is_file():
            return {'path':str(path),'cache_present':False,'scope':'No inferred binary identity; original ledger/check remains the oracle.'}
        if str(path) not in binary_cache:
            binary_cache[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        actual=binary_cache[str(path)]
        if actual!=expected:
            failures.append('retained binary hash differs from original execution: '+str(path))
        return {'path':str(path),'cache_present':True,'sha256':actual,'matches_original_execution':actual==expected}
    mappings=[]
    not_core_execution=[]
    used_numbers=set()
    for mid,record in ledger.items():
        execution=record.get('execution',{})
        if execution.get('schema')!='geometry-mutation-execution/1':
            not_core_execution.append({'id':mid,'verdict':record.get('verdict'),'schema':execution.get('schema')})
            continue
        if execution.get('head')!=request['source_sha']:
            failures.append(mid+' execution head differs from original observation F')
        exe=cache/mid/'_mut.exe'
        baseline_exe=cache/'_baseline/baseline.exe'
        calls=[row for path,row in observed if path==str(exe)]
        attempts=execution.get('attempts',[])
        if not attempts or len(calls)!=len(attempts):
            failures.append(mid+' completed command count does not equal original attempt count')
        first_mutant=calls[0]['number'] if calls else -1
        baselines=[row for path,row in observed if path==str(baseline_exe) and row['number']<first_mutant]
        baseline=baselines[-1] if baselines else None
        if baseline is None or not matches(baseline,execution.get('baseline')):
            failures.append(mid+' exact last pre-mutant baseline does not match')
        if baseline:
            used_numbers.add(baseline['number'])
        mapping={'mutant':mid,'baseline':mapped(baseline) if baseline else None,
                 'baseline_binary':binary_identity(baseline_exe,execution.get('baseline_exe_sha256')),
                 'mutant_binary':binary_identity(exe,execution.get('exe_sha256')),'attempts':[]}
        for i,(call,expected) in enumerate(zip(calls,attempts)):
            used_numbers.add(call['number'])
            if not matches(call,expected):
                failures.append(mid+' attempt-'+str(i+1)+' raw hashes/exit differ')
            mapping['attempts'].append({'attempt':i+1,'observed':mapped(call),'matches_original_attempt':matches(call,expected)})
        mappings.append(mapping)
    result={'schema':'original-core-attempt-full-stream-mapping/2',
            'ledger':str(a.ledger.resolve()),'ledger_sha256':hashlib.sha256(a.ledger.read_bytes()).hexdigest(),
            'observer_request_sha256':hashlib.sha256((a.observations/'request.json').read_bytes()).hexdigest(),
            'observer_receipt_sha256':hashlib.sha256((a.observations/'receipt.json').read_bytes()).hexdigest(),
            'mappings':mappings,'not_core_execution':not_core_execution,'failures':failures,'passed':bool(mappings) and not failures,
            'unmapped_original_run_tests_observations':[row for row in all_core_observations if row['command_number'] not in used_numbers],
            'unmapped_scope':'Retained provenance, not fabricated attempts. Earlier blocked baseline retries and original exceptions may have no original attempt_receipt. Original CLI/--check remains the verdict judge.',
            'scope':'Exact root/interpreter/runner/cache-ID/ordered distinct completed-call/raw-hash mapping only. Shared exact last baseline may map across IDs. Original mutate.py --check remains source/compile/judge/verdict oracle; original bridge Popen streams are separately inventoried.'}
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
