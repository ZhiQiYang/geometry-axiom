'use strict';
// Executes only the proposed event listener in a synthetic DOM; no browser.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm'),cp=require('node:child_process');
const OUT=__dirname,ROOT='<workspace-path>',EXPECTED='bb7e6302d4d909766521840ca564fbe1aaf57a27';
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const git=args=>cp.execFileSync('git',args,{cwd:ROOT,encoding:'utf8'}).trim();
const before={head:git(['rev-parse','HEAD']),dirty:git(['status','--porcelain'])};
const checks=[],raw=[];
function check(name,ok,detail){checks.push({name,ok:ok===true,...(detail===undefined?{}:{detail})});raw.push((ok?'PASS ':'FAIL ')+name+(detail===undefined?'':' '+JSON.stringify(detail)));}
const helper=fs.readFileSync(path.join(OUT,'focus-reveal.helper.js'),'utf8');
const app=fs.readFileSync(path.join(ROOT,'geometry-web/app.js'),'utf8');
const candidate=fs.readFileSync(path.join(OUT,'app.adaptive-focus-reveal.candidate.js'),'utf8');
check('read frozen cleanbb7',before.head===EXPECTED&&before.dirty==='');
check('exact minimal padding substitution preserves every other app byte',candidate.replace('  const padding = Math.min(3, Math.max(0, (nav.clientWidth - rect.width) / 2));\n  const left = box.left + nav.clientLeft + padding, right = box.left + nav.clientLeft + nav.clientWidth - padding;\n','  const left = box.left + nav.clientLeft + 3, right = box.left + nav.clientLeft + nav.clientWidth - 3;\n')===app&&candidate.split(helper).length===2);
check('13-line synchronous helper with one adaptive-padding line',helper.trimEnd().split('\n').length===13&&!/\b(?:async|await|Promise|setTimeout|requestAnimationFrame)\b/.test(helper));
check('only scrollLeft write; no focus/API/input/ancestor scroll changes',(helper.match(/\+=/g)||[]).length===1&&helper.includes('if (delta) nav.scrollLeft += delta;')&&!/preventDefault|stopPropagation|\.focus\(|\bapi\(|scrollIntoView|scrollTop|tabIndex|setAttribute|\.click\(/.test(helper));
check('no CSS/HTML/popover/keyboard semantics edits',sha(path.join(ROOT,'geometry-web/app.css'))===JSON.parse(fs.readFileSync(path.join(OUT,'adaptive-proposal-receipt.json'))).sources['geometry-web/app.css']);

function exercise(options={}){
  const o={nav:true,currentNav:true,targetClass:true,contained:true,active:true,workspace:true,hidden:false,rendered:true,visibility:'visible',width:577,border:1,navLeft:398.59375,left:945.375,right:1019,toolHeight:34,scroll:0,range:122,...options};
  let callback,scroll=o.scroll;const mutations=[],actions=[];
  const tool={matches:s=>o.targetClass&&s==='.workspace-tool',getBoundingClientRect:()=>({left:o.left-(scroll-o.scroll),right:o.right-(scroll-o.scroll),width:o.right-o.left,height:o.toolHeight}),focus:()=>{throw Error('focus takeover');}};
  const nav={contains:t=>o.contained&&t===tool,closest:s=>s==='[hidden]'?(o.hidden?{}:null):(o.workspace?{}:null),getClientRects:()=>o.rendered?[{}]:[],getBoundingClientRect:()=>({left:o.navLeft}),clientWidth:o.width,clientLeft:o.border};
  Object.defineProperty(nav,'scrollLeft',{get:()=>scroll,set:v=>{mutations.push({property:'nav.scrollLeft',requested:v});scroll=Math.min(o.range,Math.max(0,v));}});
  const document={addEventListener:(name,fn)=>{actions.push({event:name});callback=fn;},activeElement:o.active?tool:{}};
  const context={document,$:id=>id==='faceWorkspaceTools'&&o.nav&&o.currentNav?nav:null,getComputedStyle:()=>({visibility:o.visibility}),api:()=>{throw Error('native action');}};
  vm.runInNewContext(helper,context,{filename:'exact-focus-reveal.helper.js'});
  callback({target:tool,preventDefault:()=>{throw Error('Tab takeover');},stopPropagation:()=>{throw Error('event takeover');}});
  const rect=tool.getBoundingClientRect(),padding=Math.min(3,Math.max(0,(o.width-rect.width)/2)),left=o.navLeft+o.border+padding,right=o.navLeft+o.border+o.width-padding;
  return {scroll,mutations,actions,rect,left,right};
}
let r=exercise();
check('actual1382 clipped PAN delta nearest',r.scroll===45.40625&&r.mutations.length===1,r);
check('predicted actual PAN full rect inside nav after exact delta',r.rect.left>=r.left&&r.rect.right<=r.right&&r.rect.height===34,r);
check('actual focused PAN center moves inside content viewport',(r.rect.left+r.rect.right)/2<r.right);
r=exercise({left:402.59375-45.40625,right:476.21875-45.40625,scroll:45.40625});
check('reverse navigation SELECT nearest reveal reaches scroll0',r.scroll===0&&r.rect.left>=r.left&&r.mutations.length===1,r);
r=exercise({left:627.875,right:712.5});check('already fully visible middle tool causes zero mutation',r.mutations.length===0&&r.scroll===0,r);
r=exercise({left:402.59375,right:476.21875});check('at exact padded left edge causes zero mutation',r.mutations.length===0,r);
r=exercise({left:899.96875,right:973.59375});check('at exact padded right edge causes zero mutation',r.mutations.length===0,r);
r=exercise({left:899.96875,right:973.84375});check('subpixel right clip is revealed exactly',r.scroll===.25,r);
r=exercise({left:402.34375,right:475.96875,scroll:20});check('subpixel left clip is revealed exactly',r.scroll===19.75,r);
r=exercise({navLeft:8,width:238,border:1,left:200,right:290,toolHeight:44,range:500});check('mobile44 button reveals without resize',r.scroll===46&&r.rect.height===44&&r.rect.right<=r.right,r);
r=exercise({navLeft:8,width:238,border:0,left:6,right:50,toolHeight:44,scroll:20,range:500});check('mobile44 reverse focus preserves native size',r.scroll===15&&r.rect.left===r.left&&r.rect.height===44,r);
r=exercise({border:4,left:390,right:463.625,scroll:20});check('client border included in left delta',r.scroll===4.40625,r);
r=exercise({left:1010,right:1083.625,range:30});check('native scroll range clamps; no ancestor or other property write',r.scroll===30&&r.mutations.every(x=>x.property==='nav.scrollLeft'),r);
for(const [name,change] of [
  ['missing nav',{nav:false}],['stale/non-current nav',{currentNav:false}],['guidance-help or popover item without workspace-tool class',{targetClass:false}],
  ['other workspace tool outside face nav',{contained:false}],['stale focus event after another target owns activeElement',{active:false}],
  ['face nav outside current visible objectWorkspace',{workspace:false}],['hidden ancestor',{hidden:true}],['display-none nav/no rendered client rect',{rendered:false}],
  ['visibility-hidden actual focused target',{visibility:'hidden'}],['visibility-collapse actual target',{visibility:'collapse'}],['zero client width',{width:0}],
  ['zero target width',{right:945.375}],['zero target height',{toolHeight:0}],
]){r=exercise(change);check('reject '+name,r.mutations.length===0,r);}

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
check('all focus guards and nearest-delta formula unchanged except padding',helper.replace("  const padding = Math.min(3, Math.max(0, (nav.clientWidth - rect.width) / 2));\n",'').replace(' + padding',' + 3').replace(' - padding',' - 3')===fs.readFileSync('<workspace-path>','utf8'));

const original=fs.readFileSync('<workspace-path>','utf8');
const caption=fs.readFileSync(path.join(ROOT,'tests/issue123_caption_browser.cjs'),'utf8');
check('caption only first truth-comment line differs',original.slice(original.indexOf('\n')+1)===caption.slice(caption.indexOf('\n')+1));
check('all73 original check sites/order unchanged',(original.match(/\bcheck\(/g)||[]).length===73&&JSON.stringify(original.match(/\bcheck\([^\n]*/g))===JSON.stringify(caption.match(/\bcheck\([^\n]*/g)));
check('original seven widths untouched',original.includes('[1382,1160,900,680,600,560,390]')&&caption.includes('[1382,1160,900,680,600,560,390]'));
const syntax=[];for(const file of ['app.adaptive-focus-reveal.candidate.js','focus-reveal.helper.js']){const p=cp.spawnSync(process.execPath,['--check',path.join(OUT,file)],{encoding:'utf8'});syntax.push({file,exitCode:p.status,stderr:p.stderr});check('Node syntax '+file,p.status===0,p.stderr);}
const after={head:git(['rev-parse','HEAD']),dirty:git(['status','--porcelain'])};check('checkout remains exact clean frozenbb7',JSON.stringify(after)===JSON.stringify(before));
fs.writeFileSync(path.join(OUT,'static-vm-review-v2.log'),raw.join('\n')+'\n');
const proof={schema:'geometry-nav-focus-reveal-static-vm-review/1',checkedUTC:new Date().toISOString(),executor:{path:process.execPath,sha256:sha(process.execPath),version:process.version,command:[process.execPath,...process.execArgv,...process.argv.slice(1)],scriptSHA256:sha(__filename)},before,after,checks,total:checks.length,passed:checks.filter(x=>x.ok).length,failed:checks.filter(x=>!x.ok).length,syntax,files:Object.fromEntries(['focus-reveal.helper.js','adaptive-focus-reveal.patch','app.adaptive-focus-reveal.candidate.js','adaptive-proposal-receipt.json','static-vm-review-v2.log'].map(p=>[p,sha(path.join(OUT,p))])),actualDiagnosticInput:{path:'<isolated-test-directory>',sha256:sha('<isolated-test-directory>')},browserExecuted:false,productWritten:false,acceptanceClaim:false,limits:['VM uses actual600 nav/client/tool metrics and explicit synthetic tool positions/clientLeft1; original failedgetter did not record those positions or clientLeft','VM can prove helper arithmetic/guards; actual normalTab, hit testing and native unchanged must rerun unchanged seven-width caption on new clean product SHA','No CSS-only remedy proven; existing flex-none already true and observed outer range0','If toolbar is physically narrower than the tool, native range clamps and original strong seven-width assertion still rejects; adaptivepadding alone does not invent a layout policy']};
fs.writeFileSync(path.join(OUT,'static-vm-review-v2.json'),JSON.stringify(proof,null,2)+'\n');
console.log(JSON.stringify({passed:proof.passed,failed:proof.failed,total:proof.total,proof:path.join(OUT,'static-vm-review-v2.json'),sha256:sha(path.join(OUT,'static-vm-review-v2.json')),logSHA256:sha(path.join(OUT,'static-vm-review-v2.log'))}));
process.exitCode=proof.failed?1:0;
