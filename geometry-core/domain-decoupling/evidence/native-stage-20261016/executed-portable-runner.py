from pathlib import Path
import contextlib,datetime,io,json,subprocess,sys,unittest

root=Path('D:/geometry-axiom-work/geo261-native')
sys.path[:0]=[str(root),str(root/'tests')]
names=[
    'tests.test_geo261_mutation_migration',
    'tests.test_mutation_freshness',
    'tests.test_geo261_native_enclosures.EnclosureBoundary',
    'tests.test_geo261_native_document.DocumentBoundary',
    'tests.test_geo261_assembly_sources.AssemblySourceBoundary',
    'tests.test_geo261_wood_assembly.AssemblyBoundary',
    'tests.test_geo261_contact_sources.ContactSourcesBoundary',
    'tests.test_geo261_grid_sources.GridSourceBoundary',
]
suite=unittest.defaultTestLoader.loadTestsFromNames(names)
assert suite.countTestCases()==53,suite.countTestCases()
log=io.StringIO()
with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
here=Path(__file__).parent
(here/'stage-portable-tests.log').write_text(log.getvalue(),encoding='utf-8')
record={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection':names,'methods':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'exit':0 if result.wasSuccessful() else 1,'native_execution':False}
(here/'stage-portable-tests.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(log.getvalue());print(json.dumps(record,ensure_ascii=False))
import tests.run_all as runner
issues=runner.check_registry()
print(json.dumps({'registry_issues':issues},ensure_ascii=False))
if issues:raise SystemExit(1)
raise SystemExit(record['exit'])
