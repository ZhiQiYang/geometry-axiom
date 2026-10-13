"""Read-only extra manifest binding; preserves all original gate/census bytes."""
from pathlib import Path
import datetime,hashlib,json,sys
OUT=Path(__file__).resolve().parent
BASE='9eb670110379ec0d726914f3e5b2d8e7237f2b9c'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];scopes=[]
def check(name,ok):checks.append({'name':name,'ok':ok is True})
for kind,test,proof_name,probe_name in [
 ('caption','tests/issue123_caption_browser.cjs','supplementary-validation-9eb-caption-seven-widths.json','geometry-ui123-9eb67011-caption-seven-widths'),
 ('six','tests/issue123_adopted_slices_browser.cjs','supplementary-validation-9eb-ui123.json','geometry-ui123-9eb67011-all-six')]:
 gate=Path('<workspace-path>')/('geometry-root-ui-9eb67011-'+kind+'-gate')/'receipt.json'
 proof=OUT/proof_name;probe=Path('/tmp')/probe_name/'receipt.json';archive=gate.parent/'executed-sources';manifest=archive/'manifest.json'
 before_hashes={str(p):sha(p) for p in [gate,proof,probe,manifest]}
 g=json.loads(gate.read_bytes());m=json.loads(manifest.read_bytes());p=json.loads(probe.read_bytes());c=json.loads(proof.read_bytes());entries=m['entries'];b=g['before'];by_path={e['path']:e for e in entries}
 check(kind+': measured manifest exact fullSHA and original receipt bytes',m['fullSHA']==b['git']['head']==BASE and m['receiptSHA256']==sha(gate))
 check(kind+': measured manifest exact original provenance',m['testSourceProvenance']==g['testSourceProvenance'])
 check(kind+': no duplicate manifest source entries',len(by_path)==len(entries))
 check(kind+': every actual archived entry matches immutable hash and size',all(sha(archive/e['path'])==e['sha256'] and (archive/e['path']).stat().st_size==e['bytes'] for e in entries))
 check(kind+': all304 source snapshots exactly bound; plus one actual runner',len(b['sources'])==304 and len(entries)==305 and all(name in by_path and by_path[name]['sha256']==digest and by_path[name]['origin']=='git show '+BASE+':'+name for name,digest in b['sources'].items()))
 check(kind+': source snapshots may include caption but executed test identified separately',by_path[test]['sha256']==p['run']['scriptSHA256']==g['testSourceProvenance']['executedProbeSHA256'] and g['testSourceProvenance']['sourceOverride'] is False)
 wrapper='run_formal_caption_gate.py' if kind=='caption' else 'run_ui_gate_v3.py'
 check(kind+': actual runner bytes separately match receipt identity',wrapper in by_path and by_path[wrapper]['sha256']==b['runnerSHA256'])
 check(kind+': original independent census acceptance references same gate and fullSHA', (c.get('sourceFullSHA',c.get('sourceSHA'))==BASE) and (c.get('integrityVerified',c.get('ok')) is True) and c['recordedAcceptance']['acceptanceCompleted'] is True)
 check(kind+': no original receipt/probe/census/manifest bytes changed',all(sha(path)==digest for path,digest in before_hashes.items()))
 scopes.append({'scope':kind,'productFullSHA':BASE,'sourceDirty':b['git']['status'],'actualAcceptance':g['probeVerified'],
   'counts':{'passed':g['acceptanceResult']['passed'],'failed':g['acceptanceResult']['failed']},'executedTest':test,'executedTestSHA256':p['run']['scriptSHA256'],
   'artifacts':[{'path':path,'sha256':digest} for path,digest in before_hashes.items()], 'archiveEntries':len(entries),'beforeSourceEntries':len(b['sources']),'actualRunner':wrapper,'actualRunnerSHA256':b['runnerSHA256']})
log=OUT/'supplementary-validation-9eb-ui-manifest-addendum.log';log.write_text('\n'.join(('PASS ' if r['ok'] else 'FAIL ')+r['name'] for r in checks)+'\n')
receipt={'schema':'geometry-measured-ui-manifest-extra-binding/1','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'executor':{'path':sys.executable,'sha256':sha(sys.executable),'command':sys.orig_argv,'scriptSHA256':sha(__file__)},
 'checks':checks,'passed':sum(r['ok'] for r in checks),'failed':sum(not r['ok'] for r in checks),'scopes':scopes,
 'rawLog':str(log),'rawLogSHA256':sha(log),'browserExecuted':False,'nativeExecuted':False,'repoModified':False,
 'limits':['Additional artifact identity verification only; no new product assertion/test execution','Caption329 and SIX198 remain two separately executed scopes; source snapshot inclusion alone does not claim that test executed','No fullCDP/fullSpace/all43/privateZIP/golden/Windows acceptance inferred']}
dest=OUT/'supplementary-validation-9eb-ui-manifest-addendum.json';assert not dest.exists();dest.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'receipt':str(dest),'sha256':sha(dest),'passed':receipt['passed'],'failed':receipt['failed'],'failedChecks':[r for r in checks if not r['ok']]}))
sys.exit(0 if receipt['failed']==0 else 1)
