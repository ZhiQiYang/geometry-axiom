"""Compile isolated bridge receipt mutants; current_geometry.c stays byte-identical."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]
out=Path(tempfile.gettempdir())/'k2a-receipt-mutants'
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
    source=target.read_text();assert source.count(before)==1,(name,source.count(before))
    target.write_text(source.replace(before,after))
    executable=directory/'bridge'
    built=subprocess.run([os.environ.get('CC','cc'),'-std=c11','-O1',str(directory/'geometry-web/web_bridge.c'),'-lm','-o',str(executable)],capture_output=True,text=True)
    (directory/'build.log').write_text(built.stdout+built.stderr)
    assert built.returncode==0,built.stdout+built.stderr
    # Deliberately instrumented executables are not registry binaries. Use the
    # documented direct BridgeSession harness path, with no forged sidecar.
    runner="import os,sys,unittest;from tests.test_grid_system_contract import GridSystemContract;GridSystemContract.setUpClass=classmethod(lambda cls:setattr(cls,'bridge',os.environ['K2A_MUTANT_BRIDGE']));suite=unittest.defaultTestLoader.loadTestsFromNames("+repr(tests)+");result=unittest.TextTestRunner().run(suite);sys.exit(0 if result.wasSuccessful() and result.testsRun==2 and not result.skipped else 1)"
    run=subprocess.run(['python3','-c',runner],cwd=root,env=dict(os.environ,K2A_MUTANT_BRIDGE=str(executable)),capture_output=True,text=True)
    (directory/'result.log').write_text(run.stdout+run.stderr)
    result={'id':name,'exit':run.returncode,'detected':run.returncode!=0 and 'AssertionError' in run.stdout+run.stderr,
            'source_sha256':hashlib.sha256((root/'geometry-web'/file).read_bytes()).hexdigest(),
            'judge_sha256':hashlib.sha256((root/'tests/test_grid_system_contract.py').read_bytes()).hexdigest()}
    results.append(result);print(json.dumps(result),flush=True)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(result['detected'] for result in results),results
