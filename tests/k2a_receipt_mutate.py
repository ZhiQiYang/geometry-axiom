"""Compile isolated bridge receipt mutants; current_geometry.c stays byte-identical."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]
out=Path(tempfile.gettempdir())/'k2aa-receipt-mutants-review'
out.mkdir(exist_ok=True)
tests=['tests.test_grid_system_contract.GridSystemContract.test_k2a_deletion_receipt_names_removed_source_and_not_recreated_identity',
       'tests.test_grid_system_contract.GridSystemContract.test_k2a_parameter_confirmation_receipt_includes_intermediate_deletion']
command=['python3','-m','unittest',*tests]
baseline=subprocess.run(command,cwd=root,capture_output=True,text=True)
(out/'baseline.log').write_text(baseline.stdout+baseline.stderr)
assert baseline.returncode==0 and 'Ran 2 tests' in baseline.stderr and 'skipped' not in baseline.stderr,baseline.stdout+baseline.stderr
cases=[('M06-no-native-deletion-receipt','web_bridge.c',
        'if(ok && !(g_preview.ready && g_preview.token!=token))json_deleted_objects(before,false);',
        '/* mutant: no committed deletion receipt */'),
       ('M14b-final-state-only','engineering_bridge.inc','if(ok)receipt_scan_candidate(candidate);',
        '/* mutant: ignore transaction-internal deletion */')]
results=[]
for name,file,before,after in cases:
    directory=out/name
    (directory/'geometry-web').mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/'current_geometry.c',directory/'current_geometry.c')
    shutil.copytree(root/'geometry-core',directory/'geometry-core',dirs_exist_ok=True)
    for source in (root/'geometry-web').iterdir():
        if source.suffix in {'.c','.h','.inc'}:shutil.copy2(source,directory/'geometry-web'/source.name)
    target=directory/'geometry-web'/file
    original=target.read_bytes()
    source=target.read_text();assert source.count(before)==1,(name,source.count(before))
    selected=tests[0] if file=='web_bridge.c' else tests[1]
    positive=subprocess.run(['python3','-m','unittest',selected],cwd=root,capture_output=True,text=True)
    (directory/'baseline.log').write_text(positive.stdout+positive.stderr)
    assert positive.returncode==0 and 'Ran 1 test' in positive.stderr and 'skipped' not in positive.stderr,positive.stdout+positive.stderr
    target.write_text(source.replace(before,after))
    executable=directory/'bridge'
    built=subprocess.run([os.environ.get('CC','cc'),'-std=c11','-O1',str(directory/'geometry-web/web_bridge.c'),'-lm','-o',str(executable)],capture_output=True,text=True)
    (directory/'build.log').write_text(built.stdout+built.stderr)
    assert built.returncode==0,built.stdout+built.stderr
    # Deliberately instrumented executables are not registry binaries. Use the
    # documented direct BridgeSession harness path, with no forged sidecar.
    runner="import os,sys,unittest;from tests.test_grid_system_contract import GridSystemContract;GridSystemContract.setUpClass=classmethod(lambda cls:setattr(cls,'bridge',os.environ['K2A_MUTANT_BRIDGE']));suite=unittest.defaultTestLoader.loadTestsFromNames("+repr([selected])+");result=unittest.TextTestRunner(verbosity=2).run(suite);print('STRICT_RED',result.testsRun==1 and len(result.failures)==1 and not result.errors and not result.skipped);sys.exit(0 if result.wasSuccessful() and result.testsRun==1 and not result.skipped else 1)"
    run=subprocess.run(['python3','-c',runner],cwd=root,env=dict(os.environ,K2A_MUTANT_BRIDGE=str(executable)),capture_output=True,text=True)
    (directory/'result.log').write_text(run.stdout+run.stderr)
    target.write_bytes(original)
    restored_build=subprocess.run([os.environ.get('CC','cc'),'-std=c11','-O1',str(directory/'geometry-web/web_bridge.c'),'-lm','-o',str(executable)],capture_output=True,text=True)
    (directory/'restored-build.log').write_text(restored_build.stdout+restored_build.stderr)
    assert restored_build.returncode==0,restored_build.stdout+restored_build.stderr
    restored=subprocess.run(['python3','-c',runner],cwd=root,env=dict(os.environ,K2A_MUTANT_BRIDGE=str(executable)),capture_output=True,text=True)
    (directory/'restored.log').write_text(restored.stdout+restored.stderr)
    assert restored.returncode==0,restored.stdout+restored.stderr
    result={'id':name,'expected_test':selected,'exit':run.returncode,'detected':run.returncode!=0 and 'AssertionError' in run.stdout+run.stderr and 'STRICT_RED True' in run.stdout,'restored_exit':restored.returncode,
            'source_sha256':hashlib.sha256((root/'geometry-web'/file).read_bytes()).hexdigest(),
            'judge_sha256':hashlib.sha256((root/'tests/test_grid_system_contract.py').read_bytes()).hexdigest()}
    results.append(result);print(json.dumps(result),flush=True)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(result['detected'] for result in results),results
