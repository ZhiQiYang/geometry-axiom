"""Scratch-only minimal adaptive-padding proposal on frozen bb7."""
from pathlib import Path
import datetime,difflib,hashlib,json,subprocess,sys
ROOT=Path('<workspace-path>');OUT=Path(__file__).resolve().parent
BASE='bb7e6302d4d909766521840ca564fbe1aaf57a27'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
before={'head':git('rev-parse','HEAD'),'dirty':git('status','--porcelain')}
assert before=={'head':BASE,'dirty':''},before
app=(ROOT/'geometry-web/app.js').read_text()
old='  const left = box.left + nav.clientLeft + 3, right = box.left + nav.clientLeft + nav.clientWidth - 3;\n'
new='  const padding = Math.min(3, Math.max(0, (nav.clientWidth - rect.width) / 2));\n  const left = box.left + nav.clientLeft + padding, right = box.left + nav.clientLeft + nav.clientWidth - padding;\n'
assert app.count(old)==1
candidate=app.replace(old,new)
(OUT/'app.adaptive-focus-reveal.candidate.js').write_text(candidate)
(OUT/'adaptive-focus-reveal.patch').write_text(''.join(difflib.unified_diff(app.splitlines(True),candidate.splitlines(True),fromfile='a/geometry-web/app.js',tofile='b/geometry-web/app.js')))
start=candidate.index('document.addEventListener("focusin", e => {\n  const nav = $("faceWorkspaceTools"), tool = e.target;')
end=candidate.index('\n});',start)+len('\n});\n')
helper=candidate[start:end];(OUT/'focus-reveal.helper.js').write_text(helper)
baseline=Path('<workspace-path>')
review=baseline.read_text()
review=review.replace("EXPECTED='102ff28ecb005a85b42a8ae9cd7f22fdcf8cf01c'","EXPECTED='bb7e6302d4d909766521840ca564fbe1aaf57a27'")
review=review.replace("'app.focus-reveal.candidate.js'","'app.adaptive-focus-reveal.candidate.js'")
review=review.replace("candidate.replace(helper,'')===app&&candidate.split(helper).length===2","candidate.replace("+repr(new)+","+repr(old)+")===app&&candidate.split(helper).length===2")
review=review.replace("helper.trimEnd().split('\\n').length===12","helper.trimEnd().split('\\n').length===13")
review=review.replace("'12-line synchronous helper'","'13-line synchronous helper with one adaptive-padding line'")
review=review.replace("const rect=tool.getBoundingClientRect(),left=o.navLeft+o.border+3,right=o.navLeft+o.border+o.width-3;","const rect=tool.getBoundingClientRect(),padding=Math.min(3,Math.max(0,(o.width-rect.width)/2)),left=o.navLeft+o.border+padding,right=o.navLeft+o.border+o.width-padding;")
review=review.replace("sha(path.join(ROOT,'geometry-web/app.css'))===JSON.parse(fs.readFileSync(path.join(OUT,'proposal-receipt.json'))).inputs['geometry-web/app.css']","sha(path.join(ROOT,'geometry-web/app.css'))===JSON.parse(fs.readFileSync(path.join(OUT,'adaptive-proposal-receipt.json'))).sources['geometry-web/app.css']")
review=review.replace("const original=fs.readFileSync('<workspace-path>','utf8');","const original=fs.readFileSync('<workspace-path>','utf8');")
review=review.replace("path.join(OUT,'issue123_caption_browser.cjs')","path.join(ROOT,'tests/issue123_caption_browser.cjs')")
review=review.replace("['app.adaptive-focus-reveal.candidate.js','focus-reveal.helper.js','issue123_caption_browser.cjs']","['app.adaptive-focus-reveal.candidate.js','focus-reveal.helper.js']")
review=review.replace("['focus-reveal.helper.js','focus-reveal.patch','app.adaptive-focus-reveal.candidate.js','issue123_caption_browser.cjs','retain-caption-regression.patch','caption-comment-only.diff','proposal-receipt.json','static-vm-review-mock-corrected.log']","['focus-reveal.helper.js','adaptive-focus-reveal.patch','app.adaptive-focus-reveal.candidate.js','adaptive-proposal-receipt.json','static-vm-review-v2.log']")
review=review.replace('static-vm-review-mock-corrected.log','static-vm-review-v2.log').replace('static-vm-review-mock-corrected.json','static-vm-review-v2.json')
insert='''
const bb7=JSON.parse(fs.readFileSync('<isolated-test-directory>'));
const actual600=bb7.results.find(r=>r.name==='bounded normal toolbar and live canvas retain original sizes (mobile44) pointer PAN to SELECT 600').detail;
const bad600=bb7.results.find(r=>r.name==='real Tab remains in original nav last PAN 600 step2');
check('actual bb7 fixed-padding failure remains199/1 and exact600 source geometry',bb7.passed===199&&bb7.failed===1&&actual600.nav.clientWidth===72&&actual600.nav.width===73.984375&&bad600.detail.width===72&&bad600.detail.hit===true&&bad600.detail.insideNav===false,{nav:actual600.nav,bad:bad600});
for(const left of [110,142,143,145,214,300,346.03125]){
 const rr=exercise({navLeft:actual600.nav.left,width:actual600.nav.clientWidth,border:1,left,right:left+bad600.detail.width,toolHeight:31,scroll:200,range:503});
 check('actual600 metrics synthetic position '+left+' gives padding0/fullnav bounds',rr.left===143&&rr.right===215&&rr.rect.left>=actual600.nav.left&&rr.rect.right<=actual600.nav.right,rr);
}
for(const [client,toolWidth,expectedPadding] of [[72,72,0],[72,71,0.5],[72,69.03125,1.484375],[72,61,3],[71,72,0],[73,72,0.5],[73.984375,72,0.9921875],[0,72,0]]){
 const pad=Math.min(3,Math.max(0,(client-toolWidth)/2));
 check('adaptive padding bounded for client'+client+'/tool'+toolWidth,pad===expectedPadding&&pad>=0&&pad<=3,{client,toolWidth,pad});
}
check('all focus guards and nearest-delta formula unchanged except padding',helper.replace("  const padding = Math.min(3, Math.max(0, (nav.clientWidth - rect.width) / 2));\\n",'').replace(' + padding',' + 3').replace(' - padding',' - 3')===fs.readFileSync('<workspace-path>','utf8'));
'''
review=review.replace("const original=fs.readFileSync",insert+"\nconst original=fs.readFileSync",1)
review=review.replace("'one exact addition preserves every preexisting app byte'","'exact minimal padding substitution preserves every other app byte'")
review=review.replace("'read frozen clean102ff'","'read frozen cleanbb7'").replace("'checkout remains exact clean frozen102ff'","'checkout remains exact clean frozenbb7'")
review=review.replace("'VM uses actual diagnostic PAN geometry and explicitly assumes existing one-pixel client border; original measurement did not record clientLeft'","'VM uses actual600 nav/client/tool metrics and explicit synthetic tool positions/clientLeft1; original failedgetter did not record those positions or clientLeft'")
review=review.replace("'If scroll viewport is physically narrower than the focused tool, browser clamps; the original stronger full-visibility assertions still reject the layout'","'If toolbar is physically narrower than the tool, native range clamps and original strong seven-width assertion still rejects; adaptivepadding alone does not invent a layout policy'")
(OUT/'review_adaptive_focus_reveal.cjs').write_text(review)
after={'head':git('rev-parse','HEAD'),'dirty':git('status','--porcelain')};assert after==before
receipt={'schema':'geometry-adaptive-nav-focus-reveal-proposal/1','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'executor':{'path':sys.executable,'sha256':sha(sys.executable),'command':sys.orig_argv,'scriptSHA256':sha(__file__)},'before':before,'after':after,
 'sources':{'geometry-web/app.js':sha(ROOT/'geometry-web/app.js'),'geometry-web/app.css':sha(ROOT/'geometry-web/app.css'),'captionFormal':sha(ROOT/'tests/issue123_caption_browser.cjs')},
 'files':{p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='adaptive-proposal-receipt.json'},
 'originalBb7Failure':{'path':'<isolated-test-directory>','sha256':sha('<isolated-test-directory>'),'passed':199,'failed':1,'acceptance':False},
 'productModified':False,'browserExecuted':False,'limits':['Exact minimal scratch proposal, not product acceptance','Actual failedgetter has no full600 guidebbox or clientLeft; VM positions/clientborder are explicitly synthetic','Original073sites/caption01355 bytes and all strong seven-width assertions remain unchanged; futurecleanSHA actual required']}
(OUT/'adaptive-proposal-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'patch':str(OUT/'adaptive-focus-reveal.patch'),'patchSHA256':sha(OUT/'adaptive-focus-reveal.patch'),'candidateSHA256':sha(OUT/'app.adaptive-focus-reveal.candidate.js'),'helperSHA256':sha(OUT/'focus-reveal.helper.js')}))
