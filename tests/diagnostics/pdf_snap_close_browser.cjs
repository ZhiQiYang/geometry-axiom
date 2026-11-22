/* #432 / D06: independent real-browser PDF close-path acceptance.
 * This is NOT a formal canvas section and changes no golden or registry.
 * No model, draft, camera or parser state is assigned by page.evaluate.
 *
 * Generate fixtures first:
 *   python3 tests/diagnostics/pdf_snap_close_fixtures.py --out /tmp/pdf-close
 * Start the repo's fresh native service on a dedicated test URL, then run:
 *   node tests/diagnostics/pdf_snap_close_browser.cjs --repo /path/to/checkout \
 *     --url http://127.0.0.1:18839/ --fixtures /tmp/pdf-close --out /tmp/pdf-close-main
 * Add --cdp http://127.0.0.1:9222 to use existing Chromium, or --executable PATH.
 * Existing Playwright is required; --playwright-module PATH selects its module.
 * The same assertions run against main and patched checkouts. On the original
 * product, the h-then-line cases must FAIL their named endpoint assertions;
 * a timeout, unavailable service or browser failure is not a mutation kill.
 * The known ICONS.eye SVG error may keep the overall result red on both
 * sources. Console errors remain recorded and fail the existing strict gate;
 * they are not a named geometric mutation kill. Inspect geometryPassed and
 * the named geometric checks separately; exit 1 alone is never proof of kill.
 * Chromium execution is delegated to cloud Claude; no run is claimed here.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');

const WAIT_MS = 20000;
const L_VIEWPORT = [[60,180],[300,180],[300,80],[220,80],[220,20],[60,20]];
const L_MM = [[600,1800],[3000,1800],[3000,800],[2200,800],[2200,200],[600,200]];
const FOLLOW_VIEWPORT = [40,180];
const FOLLOW_MM = [400,1800];
const CASES = [
  {fixture:'valid-h', snap:true, kind:'outline'},
  {fixture:'explicit-l', snap:true, kind:'outline'},
  {fixture:'valid-h', snap:false, kind:'outline'},
  {fixture:'explicit-l', snap:false, kind:'outline'},
  {fixture:'malformed-h', snap:true, kind:'diagnostic'},
  {fixture:'malformed-h', snap:false, kind:'diagnostic'},
  {fixture:'h-then-line', snap:true, kind:'continuation'},
  {fixture:'h-h-then-line', snap:true, kind:'continuation'},
  {fixture:'curved-h-then-line', snap:true, kind:'continuation'}
];

function options(argv) {
  const values = {repo:path.resolve(__dirname,'../..')};
  const names = new Set(['repo','url','fixtures','out','cdp','executable','playwright-module']);
  for(let i=0;i<argv.length;i++) {
    if(argv[i]==='--help')return {help:true};
    const key=argv[i].replace(/^--/,'');
    if(!argv[i].startsWith('--') || !names.has(key) || !argv[i+1] || argv[i+1].startsWith('--'))
      throw Error('Unknown option or missing value: '+argv[i]);
    if(Object.hasOwn(values,key) && key!=='repo')throw Error('Duplicate option: '+key);
    values[key]=argv[++i];
  }
  for(const key of ['url','fixtures','out'])if(!values[key])throw Error('--'+key+' is required');
  if(values.cdp && values.executable)throw Error('Choose --cdp or --executable');
  for(const key of ['repo','fixtures','out'])values[key]=path.resolve(values[key]);
  const url=new URL(values.url);
  if(!['http:','https:'].includes(url.protocol) || !['127.0.0.1','localhost','[::1]'].includes(url.hostname))
    throw Error('--url must name a dedicated local test service');
  const relative=path.relative(values.repo,values.out);
  if(!relative || (!relative.startsWith('..'+path.sep) && relative!=='..' && !path.isAbsolute(relative)))
    throw Error('--out must be outside the checkout');
  return values;
}
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const hashFile = file => sha(fs.readFileSync(file));
const same = (a,b) => JSON.stringify(a)===JSON.stringify(b);
function canonical(points) {
  if(!Array.isArray(points) || !points.length)return null;
  return [points,points.slice().reverse()].flatMap(p=>p.map((_,i)=>JSON.stringify(p.slice(i).concat(p.slice(0,i))))).sort()[0];
}
function outline(dump,bid) {
  const line=dump.split(/\r?\n/).find(value=>value.startsWith('boundary '+bid+' outline '));
  if(!line)return {line:null,points:[]};
  const points=[];
  for(const token of line.split(/\s+/).slice(3)) {
    if(!/^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$/.test(token))break;
    points.push(token.split(',').map(Number));
  }
  return {line,points};
}

async function main(opt) {
  fs.mkdirSync(opt.out,{recursive:true});
  const reportPath=path.join(opt.out,'pdf_snap_close_browser.result.json');
  if(fs.existsSync(reportPath))throw Error('Refusing to overwrite prior evidence: '+reportPath);
  const git = (...args) => execFileSync('git',args,{cwd:opt.repo,encoding:'utf8'}).trim();
  const productFile=path.join(opt.repo,'geometry-web/room-outline.js');
  const fixtureNames=[...new Set(CASES.map(c=>c.fixture))];
  const report={schema:'geometry-pdf-close-browser/1',startedAt:new Date().toISOString(),
    formalCanvasAcceptance:false,executed:false,head:git('rev-parse','HEAD'),
    trackedChanges:git('status','--porcelain','--untracked-files=no'),
    repo:opt.repo,url:opt.url,driverSha256:hashFile(__filename),productSha256:hashFile(productFile),
    fixtures:Object.fromEntries(fixtureNames.map(name=>[name,{file:name+'.pdf',sha256:hashFile(path.join(opt.fixtures,name+'.pdf'))}])),
    oracle:{page:2,viewport:[360,220],calibration:[[60,200],[260,200],2000],outlineMm:L_MM,
      outlineWidthMm:2400,continuationSourcePoint:FOLLOW_VIEWPORT,continuationMm:FOLLOW_MM,
      malformed:'Different PDF input: missing line-to before h; no equivalent-L assertion.'},
    checks:[],cases:[],errors:[],dialogs:[]};
  const save=()=>fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
  function check(name,ok,detail) {
    const item={name,ok:ok===true,...(detail===undefined?{}:{detail})};
    report.checks.push(item);console.log((item.ok?'PASS ':'FAIL ')+name);save();return item.ok;
  }
  function requireCheck(name,ok,detail) {if(!check(name,ok,detail))throw Error(name);}
  async function runtime() {
    const response=await fetch(new URL('/runtime',opt.url),{signal:AbortSignal.timeout(WAIT_MS)});
    if(!response.ok)throw Error('runtime HTTP '+response.status);
    return response.json();
  }
  let browser,context,page,acceptDialog=false,current=null;
  const wait=expression=>page.waitForFunction(expression,null,{timeout:WAIT_MS});
  async function settle() {
    await wait("typeof connection==='object'&&connection.phase==='ready'&&!oc.busy&&!ReferenceWorkspace.busy&&!ReferenceWorkspace.history.group");
  }
  async function lesson() {
    const button=page.getByRole('button',{name:'知道了',exact:true}).first();
    for(let i=0;i<3 && await button.isVisible();i++)await button.click();
  }
  async function disclose(selector) {
    for(let i=0;i<8;i++) {
      const closed=await page.locator(selector).evaluate(element=>{
        for(let p=element.parentElement;p;p=p.parentElement)
          if(p.tagName==='DETAILS'&&!p.open)return {id:p.id,text:p.querySelector(':scope > summary').textContent};
        return null;
      });
      if(!closed)return;
      const summary=closed.id?page.locator('#'+closed.id+' > summary'):page.locator('summary').filter({hasText:closed.text}).first();
      await summary.click();
    }
    throw Error('Cannot disclose '+selector);
  }
  async function ctl(selector) {await disclose(selector);await page.locator(selector).click();await settle();}
  async function fill(selector,value) {
    await disclose(selector);await page.locator(selector).fill(String(value));
    await page.locator(selector).press('Tab');await settle();
  }
  async function nativeDump() {
    return page.evaluate(async()=>{
      const result=await apiRequest('dump');
      if(result.ok===false || typeof result.text!=='string')throw Error('Native dump failed');
      return result.text;
    });
  }
  async function snapshot(label) {
    const state=await page.evaluate(()=>{
      const bid=oc.edit?.bid,source=bid&&ReferenceWorkspace.active(bid);
      const job=source&&ReferenceWorkspace.tracingFeatures(bid);
      const segments=job?.features?.segments||[];
      const endpoints=[...new Map(segments.flatMap(s=>[s.a,s.b]).map(p=>[JSON.stringify(p),p])).values()];
      return {bid,source:source&&Object.fromEntries(['sourceId','page','imgW','imgH','crop','x','y','rot','mmPerPx','calibration'].map(key=>[key,source[key]])),
        camera:{zoom:fe.zoom,panX:fe.panX,panY:fe.panY},grid:feDraftOpts(),tool:fe.tool,
        snap:document.getElementById('faceSnapToggle').checked,draft:fe.draft,
        preview:fe.draftPreview&&{cur:fe.draftPreview.cur,pdfTarget:fe.draftPreview.pdfTarget},
        parser:{status:job?.status,segments,endpoints},
        readout:document.getElementById('faceCoordinateReadout')?.textContent};
    });
    const dump=await nativeDump();
    const value={label,...state,nativeDump:dump,nativeOutline:outline(dump,state.bid)};
    current.steps.push(value);save();return value;
  }
  // Independent source-to-world transform; SVG's observed screen matrix is used
  // only to aim real mouse input. Product coordinate functions are not invoked.
  async function screenPoint(sourcePoint) {
    return page.evaluate(([ix,iy])=>{
      const p=ReferenceWorkspace.active(oc.edit.bid),rad=p.rot*Math.PI/180;
      const dx=(ix-p.imgW/2)*p.mmPerPx,dy=(iy-p.imgH/2)*p.mmPerPx;
      const x=p.x+p.imgW*p.mmPerPx/2+dx*Math.cos(rad)-dy*Math.sin(rad);
      const y=p.y+p.imgH*p.mmPerPx/2+dx*Math.sin(rad)+dy*Math.cos(rad);
      const matrix=document.getElementById('faceEditorRoot').getScreenCTM();
      if(!matrix)throw Error('Canvas has no screen transform');
      return {x:matrix.a*x+matrix.c*y+matrix.e,y:matrix.b*x+matrix.d*y+matrix.f};
    },sourcePoint);
  }
  async function move(sourcePoint) {
    const p=await screenPoint(sourcePoint);
    requireCheck(current.id+': mouse target is inside viewport',p.x>=0&&p.y>=0&&p.x<1400&&p.y<900,p);
    await page.mouse.move(p.x,p.y);
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    return p;
  }
  async function clickSource(sourcePoint) {const p=await move(sourcePoint);await page.mouse.click(p.x,p.y);await settle();}
  async function setup(spec) {
    current={id:spec.fixture+'/snap-'+(spec.snap?'on':'off'),...spec,steps:[]};report.cases.push(current);save();
    await ctl('#fileMenuBtn');acceptDialog=true;
    try{await ctl('#btnNewProject');await wait('oc.faces.length===0');}finally{acceptDialog=false;}
    await lesson();await ctl('#fileMenuBtn');await ctl('#exampleMenuBtn');acceptDialog=true;
    try{await ctl('#btnEx');await wait('oc.faces.some(f=>f.kind==="boundary"&&f.id===1)');}finally{acceptDialog=false;}
    await page.locator('.ocard[data-kind="boundary"][data-id="1"]').click();
    await ctl('.ocard[data-kind="boundary"][data-id="1"] .card-enter');await lesson();
    await ctl('[data-fi-tab="underlay"]');
    const chooser=page.waitForEvent('filechooser',{timeout:WAIT_MS});
    // #refImport -> ReferenceWorkspace.chooseFile -> #referenceFile.click().
    // This path uses an HTML file input, not the File System Access picker.
    await ctl('#refImport');await (await chooser).setFiles(path.join(opt.fixtures,spec.fixture+'.pdf'));
    await wait("document.getElementById('referenceDialog').open&&!document.getElementById('refApply').disabled");
    await fill('#refPageNumber',2);
    await wait("!document.getElementById('refApply').disabled&&document.querySelector('#refPagePreview img')?.alt==='第 2 頁預覽'");
    requireCheck(current.id+': two-page fixture',await page.locator('#refPageNumber').getAttribute('max')==='2');
    await page.locator('#refTarget').selectOption('new');await ctl('#refApply');
    await wait("!document.getElementById('referenceDialog').open&&!!oc.edit&&!!ReferenceWorkspace.active(oc.edit.bid)");
    await ctl('#ulCalibStart');await clickSource([60,200]);await clickSource([260,200]);
    await wait('fe.ulCalib?.pts.length===2');await fill('#ulCalibDist',2000);await ctl('#ulCalibApply');
    await wait('!!ReferenceWorkspace.active(oc.edit.bid).calibration&&!fe.ulCalib');
    await ctl('[data-face-tool="redraw"]');await lesson();
    await page.locator('#faceSnapToggle').setChecked(spec.snap);await move(L_VIEWPORT[0]);
    // UI hover starts extraction when snapping is on. The query also waits for
    // source extraction in snap-off controls; it never changes native geometry.
    await wait("ReferenceWorkspace.tracingFeatures(oc.edit.bid).status==='ready'");
    // A ready parser does not itself replay a hover made while it was loading.
    // Leave and re-enter by real input before recording the first preview.
    await page.mouse.move(8,8);await move(L_VIEWPORT[0]);
    const first=await snapshot('ready-before-drawing');
    requireCheck(current.id+': selected page and source bytes',first.source.page===2&&first.source.imgW===360&&first.source.imgH===220&&first.source.sourceId===report.fixtures[spec.fixture].sha256,first.source);
    requireCheck(current.id+': 2000 mm calibration and zero placement',Math.abs(first.source.mmPerPx-10)<.001&&first.source.x===0&&first.source.y===0&&first.source.rot===0,first.source);
    return first;
  }
  async function runCase(spec) {
    const before=await setup(spec);
    if(spec.kind==='continuation') {
      check(current.id+': PDF_CLOSE_CONTINUATION_ENDPOINT',before.parser.endpoints.some(p=>same(p,FOLLOW_VIEWPORT)),before.parser);
      await move(FOLLOW_VIEWPORT);const hover=await snapshot('continuation-hover');
      check(current.id+': PDF_CLOSE_CONTINUATION_TARGET',hover.preview?.pdfTarget?.kind==='endpoint'&&same(hover.preview.pdfTarget.source,FOLLOW_VIEWPORT)&&same(hover.preview.cur,FOLLOW_MM),hover.preview);
      await clickSource(FOLLOW_VIEWPORT);const clicked=await snapshot('continuation-click');
      check(current.id+': PDF_CLOSE_CONTINUATION_DRAFT',same(clicked.draft.pts,[FOLLOW_MM]),clicked.draft);
      check(current.id+': PDF_CLOSE_DRAFT_NATIVE_UNCHANGED',clicked.nativeDump===before.nativeDump);
      await page.screenshot({path:path.join(opt.out,current.id.replace('/','-')+'.png')});
      await ctl('#faceDraftCancel');await page.keyboard.press('v');await settle();
      const cancelled=await snapshot('continuation-cancelled');
      check(current.id+': PDF_CLOSE_CANCEL_NATIVE_UNCHANGED',cancelled.nativeDump===before.nativeDump);
      return;
    }
    for(let i=0;i<L_VIEWPORT.length;i++) {
      await move(L_VIEWPORT[i]);await snapshot('vertex-'+(i+1)+'-hover');
      await clickSource(L_VIEWPORT[i]);await snapshot('vertex-'+(i+1)+'-click');
    }
    await page.keyboard.press('Enter');await wait("fe.tool==='select'");await settle();
    const finished=await snapshot('committed');current.outline=finished.nativeOutline;
    await page.screenshot({path:path.join(opt.out,current.id.replace('/','-')+'.png')});
    if(spec.kind==='diagnostic') {
      current.diagnostic='Recorded unequal input; its outline is not asserted equal to the valid L.';
      return;
    }
    const points=finished.nativeOutline.points;
    check(current.id+': PDF_CLOSE_EQUIVALENT_L',canonical(points)===canonical(L_MM),finished.nativeOutline);
    check(current.id+': PDF_CLOSE_WIDTH_2400',points.length===6&&Math.max(...points.map(p=>p[0]))-Math.min(...points.map(p=>p[0]))===2400,finished.nativeOutline);
  }
  try {
    report.runtimeBefore=await runtime();
    requireCheck('PDF_CLOSE_FRESH_NATIVE_SOURCE',report.runtimeBefore.fresh===true&&typeof report.runtimeBefore.root==='string'&&path.resolve(report.runtimeBefore.root)===opt.repo,report.runtimeBefore);
    const {chromium}=require(opt['playwright-module']||'playwright');
    browser=opt.cdp?await chromium.connectOverCDP(opt.cdp,{timeout:WAIT_MS}):await chromium.launch({headless:true,timeout:WAIT_MS,...(opt.executable?{executablePath:opt.executable}:{})});
    report.browserVersion=browser.version();
    context=await browser.newContext({viewport:{width:1400,height:900},acceptDownloads:true});
    page=await context.newPage();page.setDefaultTimeout(WAIT_MS);page.setDefaultNavigationTimeout(WAIT_MS);
    page.on('pageerror',error=>report.errors.push({case:current?.id,kind:'pageerror',message:String(error)}));
    page.on('console',message=>{if(message.type()==='error')report.errors.push({case:current?.id,kind:'console',message:message.text()});});
    page.on('dialog',async dialog=>{report.dialogs.push({case:current?.id,type:dialog.type(),message:dialog.message(),accepted:acceptDialog});await (acceptDialog?dialog.accept():dialog.dismiss());});
    await page.goto(opt.url,{waitUntil:'domcontentloaded'});await settle();await lesson();report.executed=true;save();
    const script=await page.locator('script[src]').evaluateAll(nodes=>nodes.map(node=>node.src).find(src=>new URL(src).pathname.endsWith('/room-outline.js')));
    requireCheck('PDF_CLOSE_PRODUCT_SCRIPT_PRESENT',typeof script==='string',script);
    const response=await page.request.get(script,{timeout:WAIT_MS}),served=await response.body();
    requireCheck('PDF_CLOSE_SERVED_BYTES_MATCH_REPO',response.ok()&&sha(served)===report.productSha256,{url:script,sha256:sha(served)});
    for(const spec of CASES) {
      try{await runCase(spec);}catch(error) {
        current.error={name:error.name,message:error.message,stack:error.stack};
        current.failureKind=/timeout/i.test(error.name+' '+error.message)?'timeout-not-a-kill':'execution-error-not-a-kill';
        check(current.id+': completed real UI scenario',false,current.error);save();
        // A broken prerequisite is not a named assertion kill. Stop instead of
        // issuing another scenario into unknown UI/native state.
        throw error;
      }
    }
    const equivalent=report.cases.filter(c=>c.kind==='outline').map(c=>canonical(c.outline.points));
    check('PDF_CLOSE_ON_OFF_EXPLICIT_RESULTS_EQUAL',equivalent.length===4&&equivalent.every(p=>p===canonical(L_MM)),equivalent);
    check('PDF_CLOSE_NO_BROWSER_ERRORS',report.errors.length===0,report.errors);
    report.runtimeAfter=await runtime();
    check('PDF_CLOSE_RUNTIME_UNCHANGED',report.runtimeAfter.fresh===true&&report.runtimeAfter.version===report.runtimeBefore.version&&report.runtimeAfter.session===report.runtimeBefore.session,report.runtimeAfter);
    report.headAfter=git('rev-parse','HEAD');
    check('PDF_CLOSE_SOURCES_UNCHANGED',report.headAfter===report.head&&git('status','--porcelain','--untracked-files=no')===report.trackedChanges&&hashFile(productFile)===report.productSha256&&hashFile(__filename)===report.driverSha256&&fixtureNames.every(name=>hashFile(path.join(opt.fixtures,name+'.pdf'))===report.fixtures[name].sha256));
  } catch(error) {
    report.fatal={name:error.name,message:error.message,stack:error.stack};
    console.error(error.stack||error);
  } finally {
    report.completed=report.cases.length===CASES.length&&!report.fatal&&report.cases.every(c=>!c.error);
    report.consoleClean=report.errors.length===0;
    report.geometryPassed=report.executed&&report.completed&&!report.fatal&&report.checks.length>0&&report.checks.filter(c=>c.name!=='PDF_CLOSE_NO_BROWSER_ERRORS').every(c=>c.ok);
    report.passed=report.executed&&report.completed&&report.checks.length>0&&report.checks.every(c=>c.ok);
    report.failureKind=report.passed?null:report.fatal?(/timeout/i.test(report.fatal.name+' '+report.fatal.message)?'timeout-not-a-kill':'execution-error-not-a-kill'):'named-assertion-failure';
    report.finishedAt=new Date().toISOString();save();
    if(context)await context.close();
    if(browser)await browser.close();
    console.log(JSON.stringify({report:reportPath,executed:report.executed,completed:report.completed,geometryPassed:report.geometryPassed,consoleClean:report.consoleClean,passed:report.passed,checks:report.checks.length,failed:report.checks.filter(c=>!c.ok).map(c=>c.name)}));
  }
  process.exitCode=report.passed?0:1;
}

let opt;
try{opt=options(process.argv.slice(2));}catch(error){console.error(error.message);process.exitCode=2;}
if(opt?.help)console.log('Usage: node tests/diagnostics/pdf_snap_close_browser.cjs --repo CHECKOUT --url ISOLATED_URL --fixtures DIR --out DIR [--cdp URL | --executable PATH] [--playwright-module PATH]\nRuns all nine cases with identical expected geometry on main and patched sources. A fresh native service and existing Playwright/Chromium are required.');
else if(opt)main(opt).catch(error=>{console.error(error.stack||error);process.exitCode=1;});
