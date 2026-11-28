#!/usr/bin/env python3
"""U476 bounded, named source withdrawals; an unrelated error is never a kill."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import time

TARGETS={
 'U476_DROP_CONTEXT_FRESHNESS':'U476_CT12_DECLARATION_CONTEXT_AND_EXCLUDED_FRESHNESS',
 'U476_SKIP_TYPED_NODE_SELF_ID':'U476_CT06_TYPED_NODE_KEY_KIND_ID_ALL_ROOTS',
 'U476_SKIP_CONTINUITY':'U476_CT07_INCARNATION_IS_NOT_CONTENT',
 'U476_SKIP_TYPED_SOURCE_CONTENT':'U476_CT05_DEFINITION_VALUE_AND_CLOSURE_AXES',
 'U476_ACCEPT_UNPROVEN_SUPPORT':'U476_CT09_REPRESENTATIVE_CANNOT_HIDE_BAD_ALIAS',
 'U476_ACCEPT_UNDECLARED_DUPLICATE':'U476_CT02_NO_IMPLICIT_MERGE',
 'U476_REPRESENTATIVE_MASKS_ALIAS':'U476_CT05_DEFINITION_VALUE_AND_CLOSURE_AXES',
 'U476_FORGET_REMOVED_ALIAS_LENGTH':'U476_CT01_EXPLICIT_ONE_ITEM',
 'U476_UNDO_REWINDS_HIGH_WATER':'U476_CT20_HIGHWATER_UNDO_BRANCH_DELETE_AND_COLD_OPEN',
 'U476_REOPEN_CLAIMS_VERIFIED':'U476_CT15_SAVE_COLD_REOPEN_NO_AUTHORIZATION',
 'U476_JSON_DUPLICATE_KEY_LAST_WINS':'U476_CT16_STRICT_SAVE_SCHEMA_AND_ATOMIC_FAILURE',
}

def run(repo,folder,stage,case):
    command=['node','--test','--test-reporter=spec','--test-name-pattern=^'+case+'$','tests/test_r05_takeoff_study.cjs']
    start=time.monotonic()
    try:
        result=subprocess.run(command,cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
    except subprocess.TimeoutExpired as error:
        raise AssertionError('U476_WITHDRAWAL_TIMEOUT_NOT_A_KILL '+case) from error
    folder.mkdir(parents=True,exist_ok=True)
    (folder/(stage+'.stdout.txt')).write_bytes(result.stdout)
    (folder/(stage+'.stderr.txt')).write_bytes(result.stderr)
    text=(result.stdout+result.stderr).decode('utf-8',errors='replace')
    record={'command':command,'cwd':str(repo),'exit':result.returncode,'seconds':round(time.monotonic()-start,4),'test':case}
    (folder/(stage+'.receipt.json')).write_text(json.dumps(record,indent=2)+'\n')
    if stage=='withdrawn':
        assert result.returncode==1 and case in text and 'AssertionError' in text and 'ERR_ASSERTION' in text,'U476_UNRELATED_FAILURE_NOT_A_KILL '+case+'\n'+text
        assert not any(word in text for word in ('SyntaxError','MODULE_NOT_FOUND','ReferenceError','TypeError:')),'U476_SETUP_FAILURE_NOT_A_KILL '+case
    else:
        assert result.returncode==0,'U476_BASELINE_OR_RESTORATION_NOT_GREEN '+case+'\n'+text
    return record

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();repo=args.repo.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    here=Path(__file__).resolve().parent
    specs=json.loads((here/'withdrawal-candidates.json').read_text())
    assert len(specs)==len(TARGETS) and {x['name'] for x in specs}==set(TARGETS),'U476_WITHDRAWAL_CATALOG_EXACT'
    target=repo/'geometry-core/timber-takeoff/research/candidate.cjs';original=target.read_bytes();source=original.decode()
    records=[]
    try:
        for spec in specs:
            name=spec['name'];folder=out/name
            assert source.count(spec['find'])==1,'U476_WITHDRAWAL_ANCHOR '+name
            mutant=source.replace(spec['find'],spec['replace'],1).encode()
            before=run(repo,folder,'baseline',TARGETS[name])
            diff=''.join(difflib.unified_diff(source.splitlines(True),mutant.decode().splitlines(True),fromfile='a/geometry-core/timber-takeoff/research/candidate.cjs',tofile='b/geometry-core/timber-takeoff/research/candidate.cjs'))
            (folder/'withdrawal.patch').write_text(diff,newline='\n')
            target.write_bytes(mutant)
            try: withdrawn=run(repo,folder,'withdrawn',TARGETS[name])
            finally: target.write_bytes(original)
            restored=run(repo,folder,'restored',TARGETS[name])
            record={'name':name,'test':TARGETS[name],'exits':[before['exit'],withdrawn['exit'],restored['exit']],'originalSha256':hashlib.sha256(original).hexdigest(),'mutantSha256':hashlib.sha256(mutant).hexdigest()}
            records.append(record);print(json.dumps(record),flush=True)
    finally: target.write_bytes(original)
    summary={'researchOnly':True,'officialMutationEvidence':False,'count':len(records),'withdrawals':records}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')

if __name__=='__main__':main()
