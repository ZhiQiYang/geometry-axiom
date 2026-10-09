"""Read-only binding of reviewed proposals to the committed candidate."""
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path('<workspace-path>')
OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
before={'head':git('rev-parse','HEAD'),'dirty':git('status','--porcelain')}
checks={
    'cleanFullSHA':before=={'head':'bb7e6302d4d909766521840ca564fbe1aaf57a27','dirty':''},
    'appExactReviewedCandidate':(ROOT/'geometry-web/app.js').read_bytes()==(OUT/'app.focus-reveal.candidate.js').read_bytes(),
    'captionExactCommentOnlyCopy':(ROOT/'tests/issue123_caption_browser.cjs').read_bytes()==(OUT/'issue123_caption_browser.cjs').read_bytes(),
    'formalSixOriginalBytes':sha(ROOT/'tests/issue123_adopted_slices_browser.cjs')=='6efba5412916a31df431c557a7893019f186bf8adc3fa15aa059098367e272d1',
    'goldenOriginalBytes':sha(ROOT/'geometry-web/cdp_sections.golden.json')=='e3e742ec3d731e701afc22149efa9bc11cf6506340715176175e594c94778bd9',
    'floorOriginalBytes':sha(ROOT/'geometry-web/cdp_floor.js')=='01a45d7881d583a7d328e579b457c959baa2b8d3570c3e3fbe66e8781c5f679e',
}
sources={name:sha(ROOT/name) for name in ['geometry-web/app.js','geometry-web/app.css','geometry-web/parameters.css','tests/issue123_caption_browser.cjs','tests/issue123_adopted_slices_browser.cjs','geometry-web/cdp_sections.golden.json','geometry-web/cdp_floor.js']}
after={'head':git('rev-parse','HEAD'),'dirty':git('status','--porcelain')}
checks['unchangedBeforeAfter']=after==before
log=OUT/'committed-bb7-source-binding.log';log.write_text('\n'.join(('PASS ' if v else 'FAIL ')+k for k,v in checks.items())+'\n')
receipt={'schema':'geometry-committed-source-binding/1','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'executor':{'path':sys.executable,'sha256':sha(sys.executable),'command':sys.orig_argv,'scriptSHA256':sha(__file__)},'before':before,'after':after,'checks':checks,
    'passed':sum(checks.values()),'failed':sum(not v for v in checks.values()),'sources':sources,'rawLog':str(log),'rawLogSHA256':sha(log),
    'staticProof':{'path':str(OUT/'static-vm-review-mock-corrected.json'),'sha256':sha(OUT/'static-vm-review-mock-corrected.json')},
    'acceptanceClaim':False,'browserExecuted':False,'productModified':False,
    'limits':['Only source identity is verified; future actual caption/full/SIX receipts must remain separately bound to bb7','102ff historical failures and old198/0 results are not rebound']}
p=OUT/'committed-bb7-source-binding.json';p.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'passed':receipt['passed'],'failed':receipt['failed'],'receipt':str(p),'sha256':sha(p)}))
sys.exit(0 if all(checks.values()) else 1)
