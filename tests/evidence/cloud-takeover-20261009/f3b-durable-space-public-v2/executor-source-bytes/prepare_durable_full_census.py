from pathlib import Path
import ast,datetime,hashlib,json,subprocess,sys
base=Path('<workspace-path>')
original=base/'validate_f3b_full_integration.py'
output=base/'validate_f3b_durable_integration.py'
assert not output.exists()
source=original.read_text()
old="  accept('zero failures/no skips/no browser exceptions',actual['failedAssertions']==0 and actual['skipped']==[] and actual.get('sectionsFailed',{})=={} and actual.get('uncaughtBrowserExceptions')==0)"
new="""  accept('zero failures and no skips under original gate contract',actual['failedAssertions']==0 and actual['skipped']==[] and actual.get('sectionsFailed',{})=={})
  expected_exception_rows=[line for line in raw.splitlines() if line.startswith('[EXPECTED EXCEPTION]')]
  unexpected_exception_rows=[line for line in raw.splitlines() if line.startswith('[UNEXPECTED EXCEPTION]')]
  check('exception census classified by unchanged original P38 expectation',expected_exception_rows==['[EXPECTED EXCEPTION] Error: fb-auto-probe'] and not unexpected_exception_rows and actual.get('uncaughtBrowserExceptions')==len(expected_exception_rows))"""
assert source.count(old)==1
source=source.replace(old,new)
output.write_text(source)
ast.parse(source)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
root=Path('<workspace-path>')
gate=(root/'tests/release_gate.py').read_text()
test=(root/'geometry-web/cdp_test.js').read_text()
checks={
 'only explicit exception classification delta':source.replace(new,old)==original.read_text(),
 'original gate never imposed exception-count zero': 'uncaughtBrowserExceptions' not in gate,
 'original P38 arms exact expected exception': "expectedException={message:'Error: fb-auto-probe'" in test,
 'original P38 injects exactly named probe': "throw new Error('fb-auto-probe')" in test,
 'original callback counts expected exceptions': 'excN++;' in test and "if(expected){expectedException=null;_log('[EXPECTED EXCEPTION]',description);}" in test,
 'no product/browser/service execution in preparer': 'subprocess.Popen' not in Path(__file__).read_text(),
}
for n,rows,count,unexpected,ok in [
 ('exact expected P38 accepts', ['[EXPECTED EXCEPTION] Error: fb-auto-probe'],1,[],True),
 ('zero count with expected raw rejects',['[EXPECTED EXCEPTION] Error: fb-auto-probe'],0,[],False),
 ('unexplained second exception rejects',['[EXPECTED EXCEPTION] Error: fb-auto-probe'],2,[],False),
 ('unexpected exception rejects',['[EXPECTED EXCEPTION] Error: fb-auto-probe'],1,['[UNEXPECTED EXCEPTION] x'],False),
 ('wrong expected message rejects',['[EXPECTED EXCEPTION] Error: other'],1,[],False),
 ('missing expected rows rejects',[],1,[],False),
]:
 checks[n]=(rows==['[EXPECTED EXCEPTION] Error: fb-auto-probe'] and not unexpected and count==len(rows))==ok
record={'schema':'geometry-durable-census-preparation/1','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'testedFullSHA':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
 'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True),
 'actualReviewCommand':sys.orig_argv,'actualPython':str(Path('/proc/self/exe').resolve()),'actualPythonSHA256':sha('/proc/self/exe'),
 'sourceFiles':{str(p):sha(p) for p in [original,output,Path(__file__),root/'tests/release_gate.py',root/'geometry-web/cdp_test.js']},
 'checks':checks,'allStaticChecksPassed':all(checks.values()),
 'productTestsExecuted':False,'actualFullAcceptance':'pending terminal and sealed original receipt',
 'limits':['Source/delta and counterexample review only; not browser or product assertions.','Preserves original gate/observer, all source/native/actor/golden/scope checks.','Expected exception 1 is original P38 behavior, not a new product failure.']}
out=base/'durable-census-preparation-review.json'
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'source':str(output),'sourceSHA256':sha(output),'review':str(out),'reviewSHA256':sha(out),'staticChecks':len(checks),'allStaticChecksPassed':all(checks.values())}))
sys.exit(0 if all(checks.values()) else 1)
