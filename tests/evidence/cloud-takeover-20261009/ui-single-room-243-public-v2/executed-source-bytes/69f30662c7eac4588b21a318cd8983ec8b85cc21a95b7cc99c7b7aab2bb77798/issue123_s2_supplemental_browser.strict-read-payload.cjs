/* PREPARED ONLY. Standalone, explicit partial #123 contract probe.
 * Requires a frozen clean checkout and a dedicated isolated native service.
 * API is used only for disclosed fixture setup; tested actions use normal
 * Playwright pointer/keyboard input. No force clicks or click-until-pass loops.
 * Full CDP/space, physical mobile/IME/OS pickers and private ZIP remain separate.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto'),util=require('node:util');
const {execFileSync}=require('node:child_process');
const {chromium}=require('playwright');
const ROOT=path.resolve(process.env.GEOMETRY_REPO||'<takeover-repository-root>');
const URL=process.env.GEOMETRY_TEST_URL,EXPECTED=process.env.GEOMETRY_EXPECTED_SHA;
if(process.env.GEOMETRY_ISOLATED_SERVICE!=='1')throw Error('GEOMETRY_ISOLATED_SERVICE=1 is required; never use a user scene');
if(!URL||!EXPECTED||!/^[0-9a-f]{40}$/.test(EXPECTED))throw Error('Explicit isolated GEOMETRY_TEST_URL and full GEOMETRY_EXPECTED_SHA required');
const address=new globalThis.URL(URL);
if(address.protocol!=='http:'||!['127.0.0.1','localhost'].includes(address.hostname)||!address.port||address.port==='8765'||address.pathname!=='/')throw Error('Dedicated localhost test URL required');
const OUT=path.resolve(process.env.GEOMETRY_UI123_OUT||path.join(os.tmpdir(),'geometry-ui123-'+process.pid));
const rel=path.relative(os.tmpdir(),OUT);
if(!rel||rel==='..'||rel.startsWith('..'+path.sep)||path.isAbsolute(rel))throw Error('Output must be a new dedicated TEMP directory');
fs.mkdirSync(OUT,{recursive:false});
const log=path.join(OUT,'command.log'),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const emit=(...args)=>{const line=util.format(...args);fs.appendFileSync(log,line+'\n');console.log(line);};
const allGroups=['colors','headers','components','v3','grid-mobile','model'];
const supplementGroups=['plan','bom','row-blur','s2'];
const allowedGroups=[...allGroups,...supplementGroups];
const requested=(process.env.GEOMETRY_UI123_GROUPS||'s2').split(',');
if(new Set(requested).size!==requested.length||requested.some(n=>!allowedGroups.includes(n)))throw Error('Invalid/duplicate explicit #123 group scope');
if(requested.some(n=>allGroups.includes(n)))throw Error('Supplement-only file: run original six through the current frozen formal harness, including later header assertions');
const sourcePaths=['geometry-web/app.js','geometry-web/app.css','geometry-web/index.html','geometry-web/workspace-shell.js','geometry-web/workspace-shell.css','geometry-web/space-workspace.js','geometry-web/space-workspace.css','geometry-web/grid-system-workspace.js','geometry-web/grid-system-workspace.css','geometry-web/grid-inspector.css','geometry-web/room-outline-workspace.js','geometry-web/reference-workspace.js','geometry-web/model-viewer.js','tests/binaries.py','tests/room_outline_fixture.js','geometry-web/room-outline.js','geometry-web/timber-schedule.js','geometry-web/grid-inspector.js','geometry-web/grid-anchor-positions.js'];
const git=args=>execFileSync('git',args,{cwd:ROOT,encoding:'utf8'}).trim();
const results=[],groupResults=[],errors=[];
const run={schema:'geometry-issue123-adopted-slices/1',startedAt:new Date().toISOString(),command:[process.execPath,...process.argv.slice(1)],commandEnvironment:Object.fromEntries(['GEOMETRY_REPO','GEOMETRY_EXPECTED_SHA','GEOMETRY_ISOLATED_SERVICE','GEOMETRY_TEST_URL','GEOMETRY_TEST_BRIDGE','GEOMETRY_MODEL_BASE','GEOMETRY_CHROME','GEOMETRY_UI123_OUT','GEOMETRY_UI123_GROUPS'].map(k=>[k,process.env[k]??null])),node:{path:process.execPath,sha256:sha(process.execPath),version:process.version},expectedSHA:EXPECTED,head:git(['rev-parse','HEAD']),dirty:git(['status','--porcelain']),pwd:execFileSync('pwd',{cwd:ROOT,encoding:'utf8'}).trim(),scriptSHA256:sha(__filename),sources:Object.fromEntries(sourcePaths.map(p=>[p,sha(path.join(ROOT,p))])),scope:{mode:'explicit-partial-adopted-ui-contract',included:requested,omitted:allowedGroups.filter(n=>!requested.includes(n)),fixture:'Original six scopes retained unchanged; C1 uses disclosed original CDP P12 scene lines; BOM uses disclosed native default; row-blur uses actual self-authored PDF import, calibration and room proposal, without candidate injection; S2 uses disclosed native outer/hole custom-rational binding and actual export/import same-ID owner interruption, plus scheduling-only unchanged retired callback delivery',input:'Trusted pointer/keyboard after fixture setup',notCovered:['full CDP or full space regression','physical phone/touch/IME','operating-system dialogs','private ZIP pixel/reference comparison','new snapping or nearby-object policies','all 43 checklist items']},sandbox:true,browserExecuted:false,nativeStandaloneSuiteExecuted:false};
let browser,context,page,current='preflight',contextGroup='preflight',contextOrdinal=0,expectedDialog=null;
const dialogs=[];
const check=(name,ok,detail)=>{const r={group:current,name,ok:ok===true,...(detail===undefined?{}:{detail})};results.push(r);emit((r.ok?'PASS ':'FAIL ')+name,detail===undefined?'':JSON.stringify(detail));if(!r.ok)throw Error(name);};
const read=expression=>page.evaluate(expression);
const wait=expression=>page.waitForFunction(expression,null,{timeout:20000});
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const visible=selector=>read(`(()=>{
  const e=document.querySelector(${JSON.stringify(selector)});if(!e)return false;
  const s=getComputedStyle(e),r=e.getBoundingClientRect();
  if(!(s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0))return false;
  // Closed disclosure contents can retain nonzero layout rectangles. The first
  // summary stays visible; the remaining content does not participate in paint.
  for(let n=e;n;n=n.parentElement){
    const style=getComputedStyle(n);
    if(style.display==='none'||style.contentVisibility==='hidden')return false;
    if(n!==e&&n.tagName==='DETAILS'&&!n.open){
      const summary=n.querySelector(':scope > summary');
      if(!summary||!summary.contains(e))return false;
    }
  }
  return true;
})()`);
const rect=selector=>read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing '+${JSON.stringify(selector)});const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {x:r.x,y:r.y,left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,display:s.display,visibility:s.visibility};})()`);
const dump=()=>read(`api('dump').then(r=>{if(!r.ok||typeof r.text!=='string')throw Error(JSON.stringify(r));return r.text;})`);
async function settle(){await wait(`connection.phase==='ready'&&!oc.busy&&!ReferenceWorkspace.busy&&!ReferenceWorkspace.history.group`);await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));}
async function disclose(selector){for(let i=0;i<8;i++){const item=await page.locator(selector).evaluate(e=>{for(let n=e.parentElement;n;n=n.parentElement)if(n.tagName==='DETAILS'&&!n.open){const first=[...n.children].find(child=>child.tagName==='SUMMARY');if(first&&(first===e||first.contains(e)))continue;return {id:n.id,text:first?.textContent};}return null;});if(!item)return;const summary=item.id?page.locator('#'+item.id+' > summary'):page.locator('summary').filter({hasText:item.text}).first();await summary.click();}throw Error('Disclosure nesting exceeds bound: '+selector);}
async function click(selector){await disclose(selector);await page.locator(selector).click();await settle();}
async function fill(selector,value){await disclose(selector);await page.locator(selector).fill(String(value));check('actual input contains typed raw value '+selector,await page.locator(selector).inputValue()===String(value));await page.locator(selector).press('Tab');await settle();}
async function select(selector,value){await disclose(selector);await page.locator(selector).selectOption(String(value));await settle();}
async function panel(){if(await read(`innerWidth<=680&&!document.body.classList.contains('drawer-right-open')`))await click('#workspaceToggleRight');}
async function tab(name){await panel();await click('#faceInspectorTabs [data-fi-tab="'+name+'"]');}
async function shot(name){await page.screenshot({path:path.join(OUT,current+'-'+name+'.png')});}
async function focusByTab(selector){const seen=[];for(let i=0;i<80;i++){await page.keyboard.press('Tab');const s=await read(`(()=>{const e=document.activeElement;return {id:e?.id,tag:e?.tagName,text:e?.textContent?.trim().slice(0,70),target:e===document.querySelector(${JSON.stringify(selector)}),visible:e?.matches(':focus-visible'),outline:e&&getComputedStyle(e).outlineStyle};})()`);seen.push(s);if(s.target){check('real Tab reaches visible focus target '+selector,s.visible&&s.outline!=='none',seen);return;}}check('real Tab reaches visible focus target '+selector,false,seen);}
async function expectedConfirm(action,predicate){if(expectedDialog)throw Error('Another native confirm is pending');const request={predicate,seen:0};expectedDialog=request;try{await action();check('declared product confirmation appeared exactly once',request.seen===1);}finally{expectedDialog=null;}}
async function newProject(){await click('#fileMenuBtn');await expectedConfirm(()=>click('#btnNewProject'),message=>message.startsWith('建立一份空白新專案，切換為新的專案識別及「未命名專案」。')&&message.endsWith('確定繼續嗎？'));await wait(`oc.faces.length===0&&!ReferenceWorkspace.busy`);}
const fixture=['boundary 1 outline 0,0 4000,0 4000,3000 0,3000','placement 1 on boundary 1 origin 0 0 2500 u +x v +y','canvas-pos boundary 1 280 100'];
const gridFixture=[...fixture,'grid-system 1 name-hex 7461696c20736f75726365 main-along u u repeat 0 600 v repeat 0 400','canvas-pos grid-system 1 560 100'];
async function setup(lines=fixture){await newProject();const responses=await read(`(async()=>{const rows=[];for(const line of ${JSON.stringify(lines)}){const r=await api('line '+line);rows.push({line,response:r});if(!r.ok)throw Error(JSON.stringify(rows));}await renderObjects();return rows;})()`);fs.writeFileSync(path.join(OUT,current+'-context-'+contextOrdinal+'-fixture.json'),JSON.stringify(responses,null,2)+'\n');await click('#btnZoom');await settle();}
async function enterFace(){await page.locator('.ocard[data-kind="boundary"][data-id="1"]').dblclick();await wait(`oc.edit?.bid===1&&!$('objectWorkspace').hidden`);await settle();}
async function sourceGrid(){
  // Return restores the object camera to 100%; fit the declared x560 card once
  // through the normal shortcut before a narrow-viewport pointer double-click.
  if(await read('innerWidth===390')){await page.keyboard.press('f');await settle();}
  await page.locator('.ocard[data-kind="grid-system"][data-id="1"]').dblclick();
  await wait(`$('infiniteGridWorkspace')?.open&&!!$('igName')`);await settle();
}
async function modelEmpty(){await click('#fileMenuBtn');await click('#btnModelLibraryMenu');await wait(`$('smWorkspace')?.open&&!$('smLibraryPanel').hidden`);await click('#smBackToBuild');await wait(`!$('smMain').hidden&&SpaceModelWorkspace.snapshot().sourceKind===null`);}
async function modelExample(){await click('#smWelcomeTry');await wait(`SpaceModelWorkspace.snapshot().resultSummary!==null&&!SpaceModelWorkspace.snapshot().stale`);await settle();}
async function archiveInput(){if(!page||page.isClosed())return;const rows=await read('window.__ui123Input').catch(error=>({error:error.message}));fs.writeFileSync(path.join(OUT,contextGroup+'-context-'+contextOrdinal+'-trusted-input-events.json'),JSON.stringify(rows,null,2)+'\n');}
async function freshContext(width=1382,height=804){await archiveInput();await context?.close();contextOrdinal++;contextGroup=current;context=await browser.newContext({viewport:{width,height},acceptDownloads:true});await context.addInitScript(()=>{Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});window.__ui123Input=[];for(const type of ['pointerdown','pointerup','click','dblclick','keydown','keyup','change','input'])document.addEventListener(type,e=>{const n=e.target;window.__ui123Input.push({type,at:performance.now(),trusted:e.isTrusted,id:n?.id||'',tag:n?.tagName,key:e.key,detail:e.detail,clientX:e.clientX,clientY:e.clientY,component:n?.closest('[data-component-tab]')?.dataset.componentTab,edge:n?.dataset.roomEdgeLength});},true);});page=await context.newPage();page.on('pageerror',e=>errors.push({group:contextGroup,context:contextOrdinal,error:e.stack||e.message}));page.on('dialog',async d=>{const accepted=d.type()==='confirm'&&expectedDialog&&expectedDialog.predicate(d.message());dialogs.push({group:contextGroup,context:contextOrdinal,type:d.type(),message:d.message(),accepted:!!accepted});if(accepted){expectedDialog.seen++;await d.accept();}else{errors.push({group:contextGroup,context:contextOrdinal,unexpectedNativeDialog:{type:d.type(),message:d.message()}});await d.dismiss();}});await page.goto(URL);await settle();}
// This is the exact independent rendered-geometry oracle from the original
// space_model_test.js, not a resultSummary-only or screenshot-only assertion.
async function canvasFootprint(){return read(`(()=>{const c=document.querySelector('#smCanvas'),r=c.getBoundingClientRect(),w=c.width,h=c.height,d=c.getContext('2d').getImageData(0,0,w,h).data,mask=new Uint8Array(w*h),queue=new Int32Array(w*h);for(let p=0;p<mask.length;p++){const i=p*4;mask[p]=Math.min(d[i],d[i+1],d[i+2])<170&&Math.max(d[i],d[i+1],d[i+2])<230?1:0;}let best={count:0,left:0,right:-1,top:0,bottom:-1};for(let seed=0;seed<mask.length;seed++){if(!mask[seed])continue;mask[seed]=0;queue[0]=seed;let head=0,tail=1,left=w,right=-1,top=h,bottom=-1;while(head<tail){const p=queue[head++],x=p%w,y=Math.floor(p/w);left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const nx=x+dx,ny=y+dy;if(nx<0||ny<0||nx>=w||ny>=h)continue;const n=ny*w+nx;if(mask[n]){mask[n]=0;queue[tail++]=n;}}}if(tail>best.count)best={count:tail,left,right,top,bottom};}return {canvasWidth:r.width,canvasHeight:r.height,pixelWidth:best.right-best.left+1,pixelHeight:best.bottom-best.top+1,pixels:best.count,docWidth:document.documentElement.scrollWidth,innerWidth};})()`);}
async function visibleModel(label,width){const footprint=await canvasFootprint(),minimum=width===390?100:120;check('actual connected rendered model footprint '+label,footprint.pixelWidth>=minimum&&footprint.pixelHeight>=minimum&&footprint.pixels>=3000&&footprint.docWidth<=footprint.innerWidth+1,footprint);}
// Bounded read-only preflight chooses one actual native-hit/none point before
// a single real pointer click. It does not retry UI input after a failed oracle.
async function v3PointerPoint(kind){
  const probe=await read(`(async()=>{
    const wanted=${JSON.stringify(kind)},tried=[],candidates=[];
    if(wanted==='hit')for(const shape of document.querySelectorAll('#world > g[data-view-index] rect,#world > g[data-view-index] polygon')){
      const b=shape.getBBox(),m=shape.getScreenCTM();if(!m||!b.width||!b.height)continue;
      const point=new DOMPoint(b.x+b.width/2,b.y+b.height/2).matrixTransform(m);
      candidates.push({px:point.x,py:point.y,source:'rendered-shape-center'});
    }
    if(wanted==='none'){
      const fractions=[[.5,.5],[.08,.08],[.92,.08],[.08,.92],[.92,.92],[.5,.08],[.5,.92],[.08,.5],[.92,.5]],rect=cv.getBoundingClientRect(),t=transform();
      for(const v of [2,0,1]){const L=layout.views[v],b=L.bounds;for(const [fx,fy] of fractions){const x=Math.round(b[0]+(b[2]-b[0])*fx),y=Math.round(b[1]+(b[3]-b[1])*fy);candidates.push({px:rect.left+t.ox+(x+L.tx)*t.s,py:rect.top+t.oy+(y+L.ty)*t.s,source:'declared-view-fraction',v});}}
    }
    if(candidates.length>128)throw Error('Prepared fixture exceeded native-point preflight bound');
    for(const candidate of candidates){const {px,py}=candidate,hit=document.elementFromPoint(px,py),sv=screenToView(px,py);if(!hit||!cv.contains(hit)||!sv||('v'in candidate&&sv.v!==candidate.v))continue;const response=await pickAt(sv),entry={...candidate,sv,response};tried.push(entry);if(response.ok&&(wanted==='none'?response.none===true:!response.none&&response.column>=0))return {point:entry,tried};}
    return {point:null,tried};
  })()`);
  fs.writeFileSync(path.join(OUT,current+'-context-'+contextOrdinal+'-v3-'+kind+'-preflight.json'),JSON.stringify(probe,null,2)+'\n');
  check('one native '+kind+' point inside unobstructed three-view SVG is available',!!probe.point,probe);return probe.point;
}
async function runtime(label){const response=await fetch(new globalThis.URL('/runtime',URL));const raw=await response.text();fs.writeFileSync(path.join(OUT,label+'-runtime.raw.json'),raw);if(!response.ok)throw Error('/runtime HTTP '+response.status);return JSON.parse(raw);}
function nativeIdentity(runtime){const bridge=process.env.GEOMETRY_TEST_BRIDGE,model=process.env.GEOMETRY_MODEL_BASE;if(!bridge||!model)throw Error('Explicit GEOMETRY_TEST_BRIDGE and GEOMETRY_MODEL_BASE required for executable identity');const script="import sys,json;from pathlib import Path;sys.path.insert(0,sys.argv[1]+'/tests');import binaries;rows=[]\nfor name,p in [('bridge',sys.argv[2]),('model-base',sys.argv[3])]:\n i=binaries.inspect_one(binaries.BY_NAME[name],path=Path(p));r=i.as_dict();r['fingerprint']=i.fingerprint;rows.append(r)\nprint(json.dumps(rows))";const infos=JSON.parse(execFileSync('python',['-c',script,ROOT,bridge,model],{cwd:ROOT,encoding:'utf8'}));check('native binary closure fingerprints are fresh',infos.every(r=>r.state==='fresh'),infos);const children=execFileSync('ps',['--ppid',String(runtime.pid),'-o','pid='],{encoding:'utf8'}).trim().split(/\s+/).filter(Boolean).map(Number);const live=children.map(pid=>{try{const executable=fs.realpathSync('/proc/'+pid+'/exe');return {pid,executable,sha256:sha(executable),command:fs.readFileSync('/proc/'+pid+'/cmdline').toString().replaceAll('\0',' ')};}catch(e){return {pid,error:e.message};}});check('live direct-child bridge matches recorded native executable bytes',live.some(r=>r.sha256===sha(bridge)),live);return {bridge:{path:path.resolve(bridge),sha256:sha(bridge)},modelBase:{path:path.resolve(model),sha256:sha(model)},infos,liveDirectChildren:live};}

const groups={
async colors(){const colors=[];for(const width of [1382,390]){await freshContext(width,width===390?844:804);await setup(gridFixture);let base=await dump();colors.length=0;colors.push({view:'main',color:await page.locator('#app .project-save').evaluate(e=>getComputedStyle(e).backgroundColor)});await enterFace();await tab('components');await click('[data-component-tab="timber"]');colors.push({view:'face',color:await page.locator('#tbPlace').evaluate(e=>getComputedStyle(e).backgroundColor)});await click('#workspaceBackButton');await sourceGrid();colors.push({view:'grid',color:await page.locator('#infiniteGridWorkspace .project-save').evaluate(e=>getComputedStyle(e).backgroundColor)});await click('#igClose');await modelEmpty();await modelExample();if(width===390)await click('#smTabSetup');await click('#smConfirmFaces');check('actual model primary is enabled before computed-color comparison',await page.locator('#smCreate').isEnabled());colors.push({view:'model',color:await page.locator('#smCreate').evaluate(e=>getComputedStyle(e).backgroundColor)});check('four real view primary computed backgrounds agree at '+width,colors.length===4&&new Set(colors.map(r=>r.color)).size===1&&!['transparent','rgba(0, 0, 0, 0)'].includes(colors[0].color),colors);check('color/view changes and independent example preview do not mutate native scene at '+width,(await dump())===base);await shot('color-'+width);await click('#smClose');}},
async headers(){for(const [width,height] of [[1382,804],[900,804],[600,804],[390,844]]){await freshContext(width,height);await setup(gridFixture);const main=await rect('#app > .topbar');check('main documented header single/double row at '+width,Math.abs(main.height-(width<=560?96:56))<=1,main);await enterFace();const face=await rect('.object-workspace-topbar'),vp=await rect('#faceEditorViewport');check('face documented header single/double row at '+width,Math.abs(face.height-(width<=560?96:56))<=1,face);if(width>560)check('face viewport meets adopted viewport-minus-88 minimum at '+width,vp.height>=height-88-1,vp);check('one original file/save/history DOM remains',await read(`document.querySelectorAll('#fileMenuBtn').length===1&&document.querySelectorAll('#btnUndo').length===1&&document.querySelectorAll('#btnRedo').length===1&&document.querySelectorAll('#projectBar').length===1`));await focusByTab('#workspaceBackButton');await page.keyboard.press('Enter');await wait(`!oc.focus`);await sourceGrid();const g=await read(`(()=>{const a=$('infiniteGridWorkspace').querySelector('.ig-header').getBoundingClientRect(),b=$('infiniteGridWorkspace').querySelector('.workspace-project-header').getBoundingClientRect();return {top:Math.min(a.top,b.top),bottom:Math.max(a.bottom,b.bottom),height:Math.max(a.bottom,b.bottom)-Math.min(a.top,b.top)};})()`);check('grid project and return share adopted header row at '+width,Math.abs(g.height-(width<=560?96:56))<=1,g);await click('#igClose');await modelEmpty();const m=await read(`(()=>{const a=$('smWorkspace').querySelector('.sm-header').getBoundingClientRect(),b=$('smWorkspace').querySelector('.workspace-project-header').getBoundingClientRect();return {top:Math.min(a.top,b.top),bottom:Math.max(a.bottom,b.bottom),height:Math.max(a.bottom,b.bottom)-Math.min(a.top,b.top)};})()`);check('model project and return share adopted header row at '+width,Math.abs(m.height-(width<=560?96:56))<=1,m);await shot('header-'+width);await click('#smClose');}},
async components(){for(const width of [1382,390]){await freshContext(width,width===390?844:804);await setup();const base=await dump();await enterFace();await tab('components');check('adopted component switch retains three original roles',await page.locator('#faceComponentSwitch [data-component-tab]').count()===3);const activeSections=()=>read(`[...document.querySelectorAll('[data-component-section]')].filter(e=>getComputedStyle(e).display!=='none'&&e.getBoundingClientRect().height>0).map(e=>e.dataset.componentSection)`);await click('[data-component-tab="guide"]');check('only guide form is visible',equal(await activeSections(),['guide']));await select('#refGuideRatio','1/2');await click('[data-component-tab="timber"]');check('only timber form is visible',equal(await activeSections(),['timber']));await fill('#tbA','41');await fill('#tbB','37');await fill('#tbSelector','through 601');await click('[data-component-tab="grid"]');check('only grid form is visible',equal(await activeSections(),['grid']));await fill('#gridU','0 600 1200');await click('[data-component-tab="guide"]');check('guide draft survives component navigation',await page.locator('#refGuideRatio').inputValue()==='1/2');await click('[data-component-tab="timber"]');check('timber draft survives component navigation',await page.locator('#tbA').inputValue()==='41'&&await page.locator('#tbB').inputValue()==='37'&&await page.locator('#tbSelector').inputValue()==='through 601');await focusByTab('[data-component-tab="grid"]');await page.keyboard.press('Enter');await settle();check('keyboard component switch selects only grid and retains grid draft',equal(await activeSections(),['grid'])&&await page.locator('#gridU').inputValue()==='0 600 1200');check('unsubmitted component drafts leave full native scene unchanged',(await dump())===base);await shot('drafts-'+width);}},
async v3(){for(const width of [1382,390]){await freshContext(width,width===390?844:804);await setup([...fixture,'column 1 at 1500 1000 size 400 400 z 0 2500']);const base=await dump();await click('#btnObj');await wait('view3===true');const initial=await rect('#cv');if(width>900){const sidebar=await rect('#app .sidebar-right');check('desktop unselected three-view inspector is continuously 240px',sidebar.width===240&&sidebar.height>0,sidebar);check('existing empty-state readout is discoverable',await visible('#v3PickPanel')&&/在三視圖上点選|在三視圖上點選|未選取/.test(await page.locator('#v3PickInfo').innerText()));}else{await click('#toggleRight');check('390 inspector opens through original drawer',await visible('#v3PickPanel')&&await read(`document.body.classList.contains('drawer-right-open')`));await click('#app .sidebar-right [data-close-panel="right"]');check('drawer close restores focus to its original opener',await read(`document.activeElement===$('toggleRight')`));}await click('#v3ZoomIn');await click('#v3ZoomFit');if(width===390)await click('#toggleLeft');const labels=page.locator('#v3Panel .v3-check-col label');check('seven original view/layer labels remain',await labels.count()===7);for(let i=0;i<7;i++){const label=labels.nth(i),input=label.locator('input'),was=await input.isChecked();const r=await label.boundingBox();if(width===390)check('390 full-row view/layer target is at least 44px #'+i,!!r&&r.height>=44,r);await label.click();check('normal full label pointer activates exact original view/layer #'+i,await input.isChecked()===!was);await input.press('Space');check('real Space returns original checked view/layer #'+i,await input.isChecked()===was);}if(width===390)await click('#app .sidebar-left [data-close-panel="left"]');const hit=await v3PointerPoint('hit');await page.mouse.click(hit.px,hit.py);await settle();check('real pointer selects the exact independent native-picked object',equal(await read('selected'),hit.response),{preflight:hit,actual:await read('selected')});const picked=await rect('#cv');const empty=await v3PointerPoint('none');await page.mouse.click(empty.px,empty.py);await settle();check('real pointer clears selection at the independent native-empty point',await read(`selected===null&&/未選取/.test($('v3PickInfo').textContent)`),{preflight:empty,actual:await read('selected')});if(width>900){const after=await rect('#cv');check('initial, selected and cleared three-view keep the same continuous canvas rectangle',[picked,after].every(r=>equal({left:r.left,width:r.width,top:r.top,height:r.height},{left:initial.left,width:initial.width,top:initial.top,height:initial.height})),{initial,picked,after});}check('view and layer gestures never change native geometry',(await dump())===base);await shot('view-'+width);}},
async 'grid-mobile'(){await freshContext(390,844);await setup(gridFixture);const base=await dump();await sourceGrid();const view=await rect('#igGridView'),zoom=await rect('.ig-zoombar'),settings=await rect('.ig-settings');const hits=await read(`['igZoomOut','igZoomIn','igFit'].map(id=>{const e=$(id),r=e.getBoundingClientRect(),p=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return {id,width:r.width,height:r.height,top:r.top,bottom:r.bottom,hit:e===p||e.contains(p)};})`);check('390 original zoom controls reachable before settings/scroll',zoom.top>=0&&zoom.bottom<=844&&settings.top>=view.top&&hits.every(r=>r.hit&&r.height>=44&&r.width>=44),{view,zoom,settings,hits});await click('#igZoomIn');await click('#igZoomOut');await click('#igFit');check('zoom retains source-spacing and screen-pixel readout',/600/.test(await page.locator('#igZoom').innerText())&&/px/.test(await page.locator('#igZoom').innerText()));check('grid display gestures do not mutate original scene',(await dump())===base);await shot('zoom');},
async model(){for(const width of [1382,390]){await freshContext(width,width===390?844:804);await setup();const original=await dump();await modelEmpty();check('empty build has one visible primary welcome trial',await visible('#smWelcomeTry')&&await page.locator('#smWelcome .sm-primary:visible').count()===1);for(const id of ['smTryRectangle','smTryLShape','smTryTimberFrame'])check('additional original trial is not a parallel welcome action '+id,await page.locator('#'+id).count()===1&&!await visible('#'+id));const hiddenSelectors=['.sm-view-tools','#smViewDirection','.sm-display-options','.sm-metrics'];for(const selector of hiddenSelectors)check('no-source controls and metrics hidden '+selector,!await visible(selector));await modelExample();const result=await read('SpaceModelWorkspace.snapshot().resultSummary');check('real rectangle example preview has exact adopted source topology and volume',result.closed===true&&result.face_count===6&&result.volume_mm3==='36000000000',result);for(const selector of hiddenSelectors)check('real preview reveals corresponding controls '+selector,await visible(selector));await visibleModel('initial preview '+width,width);check('preview creates no native geometry',(await dump())===original);await shot('real-preview-'+width);if(width===390)await click('#smTabSetup');await fill('#smHeight',3100);check('editing explicit height marks preview stale and blocks creation',await read(`SpaceModelWorkspace.snapshot().stale&&$('smCreate').disabled&&$('smResultBadge').dataset.state==='stale'`));if(width===390)await click('#smTabPreview');check('stale preview remains visible with controls',await visible('.sm-view-tools')&&await visible('#smViewDirection'));if(width===390)await click('#smTabSetup');await click('#smPreview');await wait(`!SpaceModelWorkspace.snapshot().stale&&SpaceModelWorkspace.snapshot().resultSummary?.volume_mm3==='37200000000'`);await click('#smConfirmFaces');await focusByTab('#smCreate');await page.keyboard.press('Enter');await wait(`!!SpaceModelWorkspace.snapshot().createdId`);const models=await read('ReferenceWorkspace.getSpaceModels()');check('one explicit model created with new height and full preview',models.length===1&&models[0].input.settings.height===3100&&models[0].result.summary.volume_mm3==='37200000000',models.map(m=>({id:m.id,input:m.input.settings,result:m.result.summary})));check('explicit model creation preserves full original native scene',(await dump())===original);await click('#smClose');const [download]=await Promise.all([page.waitForEvent('download'),click('#app .project-save')]);const saved=path.join(OUT,'model-'+width+'.gcanvas');await download.saveAs(saved);check('real product save downloaded complete archive',fs.statSync(saved).size>100&&download.suggestedFilename().endsWith('.gcanvas'));await newProject();check('UI New clears model list before Open',await read('ReferenceWorkspace.getSpaceModels().length===0&&oc.faces.length===0'));await click('#fileMenuBtn');const picker=page.waitForEvent('filechooser');await click('#btnOpenProject');await (await picker).setFiles(saved);await wait('!ReferenceWorkspace.busy&&ReferenceWorkspace.getSpaceModels().length===1');check('UI Open restores exact full saved model',equal(await read('ReferenceWorkspace.getSpaceModels()'),models));check('UI Open restores full original native scene',(await dump())===original);await click('#fileMenuBtn');await click('#btnModelLibraryMenu');await wait(`$('smWorkspace')?.open&&!$('smLibraryPanel').hidden`);await click('[data-sm-open-model="'+models[0].id+'"]');await wait(`SpaceModelWorkspace.snapshot().createdId===${JSON.stringify(models[0].id)}`);check('saved model opens real preview with original controls',await visible('.sm-view-tools')&&equal(await read('SpaceModelWorkspace.snapshot().resultSummary'),models[0].result.summary));await visibleModel('saved model re-open '+width,width);if(width===390)await click('#smTabSetup');await click('#smEditHeightButton');await fill('#smEditHeight',3200);await click('#smCancelHeightEdit');check('cancelled height edit preserves exact saved model',equal(await read('ReferenceWorkspace.getSpaceModels()'),models));await shot('saved-reopened-'+width);await click('#smClose');}}
};



// One actual user pointer attempt at a disabled control. Playwright locator.click
// correctly waits for enabledness, so it cannot represent this negative gesture.
async function attemptDisabledRoomConfirm(){
  const selector='#refRoomConfirm',requests=[];
  const capture=request=>{if(request.method()==='POST'&&new globalThis.URL(request.url()).pathname==='/api')requests.push({url:request.url(),postData:request.postData()});};
  await disclose(selector);await page.locator(selector).scrollIntoViewIfNeeded();
  const before=await read(`(()=>{const e=$('refRoomConfirm'),r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return {disabled:e.disabled,dirty:document.querySelector('[data-room-edge-length="0"]').value,rawDirty:!!document.querySelector('[data-room-edge-length="0"][data-row-dirty]'),hit:e===hit||e.contains(hit),rect:{x:r.left,y:r.top,width:r.width,height:r.height}};})()`);
  check('negative row confirm retains exact invalid raw and disabled live pointer target',before.disabled&&before.dirty==='0'&&before.rawDirty&&before.hit&&before.rect.width>0&&before.rect.height>0,before);
  await read(`(()=>{window.__disabledRoomPointer=[];for(const type of ['pointerdown','pointerup'])document.addEventListener(type,e=>{if(e.target.closest?.('#refRoomConfirm'))window.__disabledRoomPointer.push({type,trusted:e.isTrusted,id:e.target.closest('#refRoomConfirm').id});},true);return true;})()`);
  page.on('request',capture);
  try{await page.mouse.click(before.rect.x+before.rect.width/2,before.rect.y+before.rect.height/2);await settle();}finally{page.off('request',capture);}
  const events=await read('window.__disabledRoomPointer');
  check('one disabled confirm pointer attempt has trusted down/up on actual button',events.length===2&&events[0].type==='pointerdown'&&events[1].type==='pointerup'&&events.every(e=>e.trusted&&e.id==='refRoomConfirm'),events);
  check('disabled confirm pointer attempt submits zero native API requests',requests.length===0,requests);
  check('disabled confirm pointer attempt retains disabledness and exact dirty invalid row',await read(`$('refRoomConfirm').disabled&&document.querySelector('[data-room-edge-length="0"]').value==='0'&&!!document.querySelector('[data-room-edge-length="0"][data-row-dirty]')`));
}

// Supplemental scopes use public source import and disclosed native fixtures.
// They make no full-suite, physical phone, time-cost, or all-checklist claim.
const {pdf:publicRoomPDF,shapes:publicRoomShapes}=require(path.join(ROOT,'tests/room_outline_fixture.js'));
const planFixture=[
  'boundary 1 outline 0,0 4000,0 4000,3000 0,3000',
  'placement 1 on boundary 1 origin 0 0 2500 u +x v +y',
  'boundary 2 outline 0,0 3000,0 3000,4000 0,4000',
  'placement 2 on boundary 2 origin 0 0 0 u +y v +x',
  'boundary 3 outline 0,0 4000,0 4000,2500 0,2500',
  'placement 3 on boundary 3 origin 0 0 0 u +x v +z',
  'boundary 4 outline 0,0 2500,0 2500,4000 0,4000',
  'placement 4 on boundary 4 origin 0 3000 0 u +z v +x',
  'boundary 5 outline 0,0 2500,0 2500,3000 0,3000',
  'placement 5 on boundary 5 origin 0 0 0 u +z v +y',
  'boundary 6 outline 0,0 3000,0 3000,2500 0,2500',
  'placement 6 on boundary 6 origin 4000 0 0 u +y v +z',
  'space 1 boundary 1 2 3 4 5 6',
  'column 1 in 1 at 1000 1000 size 400 400',
  'beam 1 in 1 along y from 0 to 3000 at 2000 width 300 depth 500',
  'canvas-pos space 1 280 100'
];
async function leftPanel(){if(await read(`innerWidth<=680&&!document.body.classList.contains('drawer-left-open')`))await click('#workspaceToggleLeft');}
async function typedOnly(selector,value){await disclose(selector);await page.locator(selector).fill(String(value));check('raw input retained before real focus transition '+selector,await page.locator(selector).inputValue()===String(value));}
function canonicalRoom(points){return [points,points.slice().reverse()].flatMap(p=>p.map((_,i)=>JSON.stringify(p.slice(i).concat(p.slice(0,i))))).sort()[0];}
function sourceWorld(s,q,round=true){const dx=(q[0]-s.imgW/2)*s.mmPerPx,dy=(q[1]-s.imgH/2)*s.mmPerPx,cx=s.x+s.imgW*s.mmPerPx/2,cy=s.y+s.imgH*s.mmPerPx/2,d=s.rot===0?[dx,dy]:s.rot===90?[-dy,dx]:s.rot===180?[-dx,-dy]:[dy,-dx],p=[cx+d[0],cy+d[1]];return round?p.map(Math.round):p;}
async function roomSourcePoint(bid,q){const source=await read(`ReferenceWorkspace.active(${bid})`),world=sourceWorld(source,q,false);if(await read(`innerWidth<=680&&document.body.classList.contains('drawer-right-open')`))await click('#faceWorkspaceLayout .face-inspector-panel [data-close-panel="right"]');const p=await read(`(()=>{const r=$('faceEditorSvg').getBoundingClientRect();return [r.left+fe.panX+${world[0]}*fe.zoom,r.top+fe.panY+${world[1]}*fe.zoom];})()`);await page.mouse.click(...p);await settle();}
async function importCalibratedRoom(width){await newProject();const file=path.join(OUT,'row-blur-'+width+'.pdf');fs.writeFileSync(file,publicRoomPDF());await click('#fileMenuBtn');const picking=page.waitForEvent('filechooser');await click('#btnImportReference');await (await picking).setFiles(file);await wait(`$('referenceDialog').open&&!$('refApply').disabled`);await click('#refApply');await wait(`!$('referenceDialog').open&&!!oc.edit&&!!ReferenceWorkspace.active(oc.edit.bid)`);const bid=await read('oc.edit.bid');await tab('underlay');check('real public PDF import preserves exact original file bytes',await read(`ReferenceWorkspace.active(${bid}).sourceId`)===sha(file));check('uncalibrated real PDF cannot propose a room',await read(`$('refRoomPick').disabled&&ReferenceWorkspace.reconstructionState(${bid})==='unreviewed'`));await click('#ulCalibStart');await roomSourcePoint(bid,[30,30]);await roomSourcePoint(bid,[230,30]);await wait(`fe.ulCalib?.pts.length===2`);await panel();await fill('#ulCalibDist','2000');await click('#ulCalibApply');await wait(`!!ReferenceWorkspace.active(${bid}).calibration&&!fe.ulCalib`);await click('#refFit');const source=await read(`ReferenceWorkspace.active(${bid})`);check('real calibration is independently known 10 mm per source unit',Math.abs(source.mmPerPx-10)<.001,source.calibration);return {bid,source,file};}
async function proposePublicRoom(bid,source){await panel();await click('#refRoomPick');await roomSourcePoint(bid,[70,70]);await wait(`!!RoomOutlineWorkspace.snapshot()||!RoomOutlineWorkspace.hasWork`);await panel();const state=await read('RoomOutlineWorkspace.snapshot()');check('source-normal PDF candidate equals independently authored painted inner rectangle',!!state&&canonicalRoom(state.points)===canonicalRoom(publicRoomShapes[0].inside.map(q=>sourceWorld(source,q))),state);check('candidate requires explicit review before confirmation',await page.locator('#refRoomConfirm').isDisabled()&&state.reviewed===false);return state;}

// One direct user Cancel from the still-focused invalid input. There is no
// intervening blur/review gesture and no retry if the first pointer is lost.
async function immediateInvalidRowCancel(width,selector,baseline,bid,source){
  const before=await read('RoomOutlineWorkspace.snapshot()');
  const oldRow=await page.locator(selector).elementHandle();
  await typedOnly(selector,'0');
  check('direct invalid-to-Cancel starts with focused exact raw and unchanged candidate '+width,
    await read(`document.activeElement===document.querySelector(${JSON.stringify(selector)})&&document.querySelector(${JSON.stringify(selector)}).value==='0'&&!!document.querySelector(${JSON.stringify(selector)}+'[data-row-dirty]')&&!RoomOutlineWorkspace.snapshot().reviewed&&$('refRoomConfirm').disabled`)
    &&equal((await read('RoomOutlineWorkspace.snapshot()')).points,before.points)&&(await dump())===baseline);
  const start=await read('window.__ui123Input.length'),requests=[],responses=[];
  // Cancel redraw is allowed to read exactly these existing native sources.
  // Every observed command/response is retained; any unknown or write is denied.
  const capture=request=>{if(request.method()!=='POST'||new globalThis.URL(request.url()).pathname!=='/api')return;
    const record={url:request.url(),postData:request.postData(),payload:null,cmd:null,response:null,error:null};requests.push(record);
    try{const data=JSON.parse(record.postData);record.payload=data;record.cmd=typeof data?.cmd==='string'?data.cmd:null;}catch(error){record.error=error.message;}
    responses.push((async()=>{try{const response=await request.response();if(!response)throw Error('No actual API response');
      const body=await response.text();record.response={status:response.status(),body,bodySHA256:crypto.createHash('sha256').update(body).digest('hex'),json:JSON.parse(body)};
    }catch(error){record.error=error.message;}})());};
  page.on('request',capture);
  try{await page.locator('#refRoomCancel').click();await settle();}finally{page.off('request',capture);}
  const events=await read(`window.__ui123Input.slice(${start}).filter(e=>e.id==='refRoomCancel'&&['pointerdown','pointerup','click'].includes(e.type))`);
  check('direct invalid-to-Cancel uses exactly one trusted pointer click '+width,
    events.length===3&&equal(events.map(e=>e.type),['pointerdown','pointerup','click'])&&events.every(e=>e.trusted),events);
  await Promise.all(responses);
  const afterCancel=await dump();
  const readOnly=record=>!record.error&&['source-inspect','engineering-read'].includes(record.cmd)
    &&record.payload!==null&&typeof record.payload==='object'&&!Array.isArray(record.payload)&&Object.keys(record.payload).length===1&&Object.prototype.hasOwnProperty.call(record.payload,'cmd')
    &&record.response?.status===200&&record.response.json?.ok===true;
  const nativeEvidence={beforeSHA256:crypto.createHash('sha256').update(baseline).digest('hex'),afterSHA256:crypto.createHash('sha256').update(afterCancel).digest('hex'),equal:afterCancel===baseline,requests};
  fs.writeFileSync(path.join(OUT,'direct-invalid-cancel-'+width+'-native-reads.json'),JSON.stringify(nativeEvidence,null,2)+'\n');
  check('direct invalid-to-Cancel permits only exact declared native reads and zero mutation '+width,requests.every(readOnly)&&afterCancel===baseline,nativeEvidence);
  check('direct invalid-to-Cancel retires candidate and old row while retaining entire native scene '+width,
    await read('!RoomOutlineWorkspace.hasWork&&RoomOutlineWorkspace.snapshot()===null')&&await oldRow.evaluate(e=>!e.isConnected)&&(await dump())===baseline);
  const fresh=await proposePublicRoom(bid,source);
  check('new candidate after direct invalid Cancel has exact clean rows and no inherited review '+width,
    await read(`document.querySelectorAll('[data-room-edge-length][data-row-dirty]').length===0&&!RoomOutlineWorkspace.snapshot().reviewed&&$('refRoomConfirm').disabled&&[...document.querySelectorAll('[data-room-edge-length]')].every(e=>{const ps=RoomOutlineWorkspace.snapshot().points,i=Number(e.dataset.roomEdgeLength),a=ps[i],b=ps[(i+1)%ps.length];return e.value===String(Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1]));})`)
    &&canonicalRoom(fresh.points)===canonicalRoom(publicRoomShapes[0].inside.map(q=>sourceWorld(source,q)))&&(await dump())===baseline);
  return fresh;
}

function rectangularEdgeExtension(points,edge,extra){const a=points[edge],b=points[(edge+1)%points.length],axis=a[0]===b[0]?1:0,side=b[axis],delta=Math.sign(b[axis]-a[axis])*extra;return points.map(p=>p.map((n,i)=>i===axis&&n===side?n+delta:n));}
function readQuotedCSV(text){const rows=[];let row=[],cell='',quoted=false;for(let i=0;i<text.length;i++){const c=text[i];if(i===0&&c==='\ufeff')continue;if(quoted){if(c==='"'&&text[i+1]==='"'){cell+='"';i++;}else if(c==='"')quoted=false;else cell+=c;}else if(c==='"')quoted=true;else if(c===','){row.push(cell);cell='';}else if(c==='\n'){row.push(cell.replace(/\r$/,''));rows.push(row);row=[];cell='';}else cell+=c;}if(quoted)throw Error('CSV has unclosed quoted field');if(cell||row.length){row.push(cell);rows.push(row);}return rows;}
function independentTimberRows(references,surface){if(!references.ok)throw Error('Native references read failed');return references.timbers.filter(t=>t.geometry?.surface===surface).map(t=>({id:t.id,role:t.role,A:t.geometry.A,B:t.geometry.B,L:t.geometry.length,dir:t.geometry.dir,side:t.geometry.side,origin:t.geometry.origin,finish:t.geometry.origin.map((n,i)=>n+t.geometry.axes[0][i]*t.geometry.length),fingerprint:references.sourceFingerprint,sources:(references.engineeringSources||[]).filter(s=>s.target?.kind==='timber'&&s.target.id===t.id)})).sort((a,b)=>a.id-b.id);}
async function checkBOMRows(expected,unit){const actual=await page.locator('#faceTimberSchedule .timber-schedule-row').evaluateAll(nodes=>nodes.map(n=>({id:Number(n.dataset.timberId),dimensions:n.querySelector('small').textContent,source:n.querySelector('.timber-schedule-source p').textContent})));check('BOM dimensions and world endpoints equal independent native geometry in '+unit,equal(actual.map(a=>a.id),expected.map(t=>t.id))&&actual.every((a,i)=>{const t=expected[i],scale=unit==='cm'?10:1;return a.dimensions===`完成 L ${t.L/scale} × A ${t.A/scale} × B ${t.B/scale} ${unit} · ${t.dir}${t.side}`&&a.source.includes(JSON.stringify(t.origin))&&a.source.includes(JSON.stringify(t.finish))&&a.source.includes(t.fingerprint)&&a.source.includes('材料／加工：未知或未設定');}),{actual,expected,unit});}

// The existing I8a HTML dialog must be reviewed before the native candidate is
// committed. This is one delete action and, when required, one actual Confirm;
// no direct API commit, bypass, click retry, or product-state injection.
async function deleteTimberReviewed(id){
  const beforeDelete=await dump();
  await page.locator('#faceLayerList [data-timber-id="'+id+'"] .face-layer-del').click();
  await wait(`!!document.querySelector('dialog.reference-impact[open]')||!fe.timbers.some(t=>t.id===${id})`);
  const preview=await read(`(()=>{const all=document.querySelectorAll('dialog.reference-impact[open]'),d=all[0];if(!d)return null;return {count:all.length,command:d.querySelector('code')?.textContent,title:d.querySelector('h2')?.textContent,violations:d.querySelectorAll('.impact-violation').length,confirmEnabled:!!d.querySelector('#impact-confirm')&&!d.querySelector('#impact-confirm').disabled,content:d.textContent};})()`);
  if(id===3)check('original default timber 3 deletion obtains the required native preview',preview!==null,preview);
  if(preview){
    check('BOM native deletion preview matches exactly the requested timber '+id,preview.count===1&&preview.command==='delete timber '+id&&preview.title==='確認連動變更'&&preview.violations===0&&preview.confirmEnabled,preview);
    check('BOM native deletion preview retains entire scene before explicit Confirm '+id,(await dump())===beforeDelete);
    fs.writeFileSync(path.join(OUT,'bom-'+await read('innerWidth')+'-delete-'+id+'-preview.json'),JSON.stringify({id,beforeDelete,preview},null,2)+'\n');
    await shot('delete-'+id+'-preview');
    await page.locator('dialog.reference-impact[open] #impact-confirm').click();
    await wait(`!document.querySelector('dialog.reference-impact[open]')`);
  }
  await settle();
  await wait(`!fe.timbers.some(t=>t.id===${id})`);
}

Object.assign(groups,{
  async plan(){for(const width of [1382,390]){await freshContext(width,width===390?844:804);await setup(planFixture);const baseline=await dump();await page.locator('.ocard[data-kind="space"][data-id="1"]').dblclick();await wait(`oc.focus?.t==='space'&&oc.focus.id===1`);await settle();await click('#spaceStageTabs [data-ss-tab="plan"]');const expected=['柱1 400×400','樑1 300×3000'];const inspect=()=>read(`(()=>{const svg=$('spacePlanSvg'),matrix=svg.getScreenCTM(),scale=Math.hypot(matrix.a,matrix.b),pattern=$('spacePlanGridPattern'),grid=svg.querySelector('[data-plan-grid]');return {labels:[...svg.querySelectorAll('.space-plan-label')].map(e=>({text:e.textContent,pixels:parseFloat(getComputedStyle(e).fontSize)*scale})),step:Number(svg.dataset.planGridStep),patternWidth:Number(pattern.getAttribute('width')),patternHeight:Number(pattern.getAttribute('height')),gridPointer:getComputedStyle(grid).pointerEvents,metrics:$('spacePlanMetrics').textContent,docWidth:document.documentElement.scrollWidth,viewport:innerWidth};})()`);let state=await inspect();check('real C1 labels retain native dimensions and readable screen text on '+width,equal(state.labels.map(e=>e.text),expected)&&state.labels.every(e=>Math.abs(e.pixels-12)<=.05),state);check('C1 grid has consistent mm units and cannot intercept pointer input',Number.isFinite(state.step)&&state.step>0&&state.step===state.patternWidth&&state.step===state.patternHeight&&state.gridPointer==='none'&&state.metrics.includes(`格距 ${state.step} mm`)&&state.docWidth<=state.viewport+1,state);await read(`(()=>{document.addEventListener('pointermove',e=>{if($('spacePlanSvg')?.contains(e.target))window.__ui123Input.push({type:'pointermove',trusted:e.isTrusted,clientX:e.clientX,clientY:e.clientY,id:e.target.id||'',tag:e.target.tagName});},true);return true;})()`);const p=await read(`(()=>{const svg=$('spacePlanSvg'),m=svg.getScreenCTM(),point=new DOMPoint(1700,1700).matrixTransform(m);return {x:point.x,y:point.y,a:m.a,b:m.b,c:m.c,d:m.d,e:m.e,f:m.f};})()`);await page.mouse.move(p.x,p.y);await settle();const moves=await read(`window.__ui123Input.filter(e=>e.type==='pointermove')`),last=moves.at(-1);check('C1 room readout follows actual trusted pointer coordinate',!!last&&last.trusted,moves);const determinant=p.a*p.d-p.b*p.c,wx=(p.d*(last.clientX-p.e)-p.c*(last.clientY-p.f))/determinant,wy=(-p.b*(last.clientX-p.e)+p.a*(last.clientY-p.f))/determinant;state=await inspect();check('C1 actual metric coordinate matches independent inverse screen transform',state.metrics===`x ${Math.round(wx)} · y ${Math.round(wy)} mm · 格距 ${state.step} mm`,{state,wx,wy,last});await click('#spaceStageTabs [data-ss-tab="proj"]');check('projection keeps the plan placement controls guarded',await page.locator('#spacePlaceColumn').isDisabled()&&await page.locator('#spacePlaceBeam').isDisabled());await click('#spaceStageTabs [data-ss-tab="plan"]');state=await inspect();check('real plan return retains readable dimensional labels',equal(state.labels.map(e=>e.text),expected)&&state.labels.every(e=>Math.abs(e.pixels-12)<=.05),state);check('C1 display and pointer observations preserve full native geometry',(await dump())===baseline);await shot('plan-'+width);}},
  async bom(){for(const width of [1382,390]){await freshContext(width,width===390?844:804);await newProject();const fixtureResponse=await read(`(async()=>{const r=await api('default');if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();return r;})()`);fs.writeFileSync(path.join(OUT,'bom-'+width+'-native-default-fixture.json'),JSON.stringify(fixtureResponse,null,2)+'\n');await click('#btnZoom');await enterFace();await tab('components');await click('[data-component-tab="timber"]');const baseline=await dump(),native=await read(`apiRequest('references')`),expected=independentTimberRows(native,1);check('native default is the original three placed timber source',equal(expected.map(t=>t.id),[1,2,3])&&expected.every(t=>t.A===27&&t.B===33),native);await checkBOMRows(expected,'mm');const leftIDs=()=>read(`[...document.querySelectorAll('#faceLayerList .face-layer-row[data-timber-id]')].map(e=>Number(e.dataset.timberId))`);check('BOM controls appear once on right and left timber rows stay pure locating/removal',await read(`['timberScheduleScope','timberScheduleUnit','timberScheduleOrder','timberScheduleCSV'].every(id=>document.querySelectorAll('#'+id).length===1&&$('faceTimberSchedule').contains($(id)))&&[...document.querySelectorAll('#faceLayerList [data-timber-id]')].every(e=>!e.querySelector('select,input,details,.timber-schedule-controls'))`)&&equal(await leftIDs(),[1,2,3]));await leftPanel();await page.locator('#faceLayerList [data-timber-id="3"] .grid-layer-open').click();await settle();check('trusted left-row action preserves original timber selection',await read(`fe.sel?.kind==='timber'&&fe.sel.id===3&&document.querySelector('.face-timber[data-face-hit="t:3"]').classList.contains('sel')`));await panel();await select('#timberScheduleScope','selection');await checkBOMRows(expected.filter(t=>t.id===3),'mm');check('selection-only BOM does not hide other left layer rows',equal(await leftIDs(),[1,2,3]));await select('#timberScheduleUnit','cm');await checkBOMRows(expected.filter(t=>t.id===3),'cm');await select('#timberScheduleScope','surface');await select('#timberScheduleOrder','length');const sorted=expected.slice().sort((a,b)=>a.L-b.L||a.id-b.id);await checkBOMRows(sorted,'cm');const waiting=page.waitForEvent('download');await click('#timberScheduleCSV');const download=await waiting,file=path.join(OUT,'bom-'+width+'.csv');await download.saveAs(file);const csv=readQuotedCSV(fs.readFileSync(file,'utf8')),header=csv.shift(),index=name=>{const i=header.indexOf(name);if(i<0)throw Error('Missing independent CSV column '+name);return i;};check('real CSV contains exact mm values, identity, native world endpoints and unknown materials',csv.length===sorted.length&&csv.every((r,i)=>{const t=sorted[i];return Number(r[index('timber_id')])===t.id&&Number(r[index('surface_id')])===1&&r[index('role')]===t.role&&Number(r[index('A_mm')])===t.A&&Number(r[index('B_mm')])===t.B&&Number(r[index('finished_length_mm')])===t.L&&equal(JSON.parse(r[index('start_world_mm')]),t.origin)&&equal(JSON.parse(r[index('finish_world_mm')]),t.finish)&&r[index('source_fingerprint')]===t.fingerprint&&r[index('material')]==='未知／未設定'&&r[index('machining')]==='未知／未設定'&&equal(JSON.parse(r[index('dimension_source_definitions')]),t.sources);}),{file,sha256:sha(file),header,csv});check('BOM sorting, scope, unit and real export preserve full native scene',(await dump())===baseline);for(const id of [3,2,1]){await leftPanel();await page.locator('#faceLayerList [data-timber-id="'+id+'"] .grid-layer-open').click();await settle();await deleteTimberReviewed(id);}check('deleting last timber clears stale BOM rows and controls',await read(`fe.timbers.length===0&&$('faceTimberSchedule').childElementCount===0&&document.querySelectorAll('#timberScheduleCSV,#timberScheduleStatus,#faceLayerList [data-timber-id]').length===0`));for(const ids of [[1],[1,2],[1,2,3]]){await page.keyboard.press('Control+z');await settle();await wait(`JSON.stringify(fe.timbers.map(t=>t.id).sort((a,b)=>a-b))===${JSON.stringify(JSON.stringify(ids))}`);}check('real Undo restores exact full native default scene after BOM cleanup',(await dump())===baseline);await panel();await select('#timberScheduleOrder','id');check('BOM normal ID-order selection preserves exactly restored native scene',await page.locator('#timberScheduleOrder').inputValue()==='id'&&(await dump())===baseline);await checkBOMRows(expected,'cm');await shot('bom-'+width);}},
  async 'row-blur'(){for(const width of [1382,390]){await freshContext(width,width===390?844:804);const {bid,source}=await importCalibratedRoom(width),baseline=await dump();let initial=await proposePublicRoom(bid,source);check('real proposal leaves the entire original native scene unchanged',(await dump())===baseline);const row0='[data-room-edge-length="0"]',row1='[data-room-edge-length="1"]',handle=await page.locator(row0).elementHandle();let length=Math.abs(initial.points[0][0]-initial.points[1][0])+Math.abs(initial.points[0][1]-initial.points[1][1]);await typedOnly(row0,length+40);check('new row input immediately clears explicit review',await read(`!RoomOutlineWorkspace.snapshot().reviewed&&$('refRoomConfirm').disabled&&$('faceDraftFinish').disabled`));await page.locator('#refRoomReviewed').click();await settle();let after=await read('RoomOutlineWorkspace.snapshot()');check('direct pointer review after blur commits only independently expected rectangle edit',equal(after.points,rectangularEdgeExtension(initial.points,0,40))&&after.reviewed&&await page.locator('#refRoomReviewed').isChecked()&&await page.locator('#refRoomConfirm').isEnabled(),after);check('real blur preserves the pointer target row node instead of replacing the pane',await handle.evaluate(e=>e.isConnected&&document.querySelector('[data-room-edge-length="0"]')===e));check('row edit and review preserve full native geometry',(await dump())===baseline);const revision=after.revision;await page.locator(row0).click();await page.locator('#refRoomCandidate > strong').click();await settle();check('bare focus and blur retain reviewed candidate and revision',await read(`RoomOutlineWorkspace.snapshot().reviewed&&RoomOutlineWorkspace.snapshot().revision===${revision}&&$('refRoomReviewed').checked&&!$('refRoomConfirm').disabled`));const nextHandle=await page.locator(row1).elementHandle();initial=await read('RoomOutlineWorkspace.snapshot()');length=Math.abs(initial.points[0][0]-initial.points[1][0])+Math.abs(initial.points[0][1]-initial.points[1][1]);await typedOnly(row0,length+20);await page.locator(row0).press('Tab');await settle();after=await read('RoomOutlineWorkspace.snapshot()');check('real Tab lands on the same next row after one geometric edit',await nextHandle.evaluate(e=>e.isConnected&&document.activeElement===e)&&equal(after.points,rectangularEdgeExtension(initial.points,0,20))&&!after.reviewed,after);initial=after;length=Math.abs(initial.points[1][0]-initial.points[2][0])+Math.abs(initial.points[1][1]-initial.points[2][1]);await typedOnly(row1,length+10);await page.locator(row1).press('Enter');await settle();after=await read('RoomOutlineWorkspace.snapshot()');check('real Enter applies exactly one pending row edit and retains field focus',equal(after.points,rectangularEdgeExtension(initial.points,1,10))&&after.revision===initial.revision+1&&await nextHandle.evaluate(e=>document.activeElement===e),after);await typedOnly(row0,'0');await page.locator('#refRoomReviewed').click();await settle();await attemptDisabledRoomConfirm();check('invalid pending raw row never reaches native commit even after explicit review',await read(`RoomOutlineWorkspace.hasWork&&!!RoomOutlineWorkspace.snapshot()&&!!document.querySelector('[data-room-edge-length][data-row-dirty]')`)&&(await dump())===baseline);await page.locator('#refRoomCancel').click();await settle();check('direct pointer Cancel after invalid row discards candidate without native writes',await read('!RoomOutlineWorkspace.hasWork&&RoomOutlineWorkspace.snapshot()===null')&&(await dump())===baseline);check('cancelled old row nodes cannot remain attached to new UI',await handle.evaluate(e=>!e.isConnected)&&await nextHandle.evaluate(e=>!e.isConnected));initial=await proposePublicRoom(bid,source);check('new source-normal candidate has no old dirty input or review',await read(`document.querySelectorAll('[data-room-edge-length][data-row-dirty]').length===0&&!RoomOutlineWorkspace.snapshot().reviewed&&$('refRoomConfirm').disabled`)&&canonicalRoom(initial.points)===canonicalRoom(publicRoomShapes[0].inside.map(q=>sourceWorld(source,q))));initial=await immediateInvalidRowCancel(width,row0,baseline,bid,source);length=Math.abs(initial.points[0][0]-initial.points[1][0])+Math.abs(initial.points[0][1]-initial.points[1][1]);await typedOnly(row0,length+20);await page.locator('#refRoomCancel').click();await settle();check('direct pointer Cancel survives a valid committing blur and retains original scene',await read('!RoomOutlineWorkspace.hasWork')&&(await dump())===baseline);await proposePublicRoom(bid,source);await click('#refRoomReviewed');await click('#refRoomConfirm');await wait(`!RoomOutlineWorkspace.hasWork&&ReferenceWorkspace.reconstructionState(${bid})==='confirmed'`);check('new reviewed candidate remains commit-capable after stale rows were cancelled',canonicalRoom(await read(`oc.bmap[${bid}][0].verts`))===canonicalRoom(publicRoomShapes[0].inside.map(q=>sourceWorld(source,q))));await page.keyboard.press('Control+z');await settle();check('real Undo restores entire pre-proposal native scene',(await dump())===baseline);await shot('row-blur-'+width);}}
});

// S2 is a separate adopted-contract scope. Fixtures and the owner interruption
// are disclosed native/project API setup; every editing action uses one normal
// pointer or bounded real Tab/Enter/Space. No mocked geometry or token rewriting.
Object.assign(groups, {
async s2() {
  const titleNames=['左上','上中','右上','左中','中心','右中','左下','下中','右下'];
  const fixtureLines=[
    'boundary 901 outline -1800,-1200 2400,-1200 2400,1600 -1800,1600 hole 100,200 100,600 700,600 700,200',
    'grid-system 901 name-hex 533220636f6e7472616374 main-along none u repeat 0 600 v repeat 0 400',
    'canvas-pos boundary 901 200 100','canvas-pos grid-system 901 500 100'
  ];
  const raw=()=>read(`ReferenceWorkspace.readFeatureAttachment('grid-draft')`);
  const project=()=>read(`ReferenceWorkspace.getProjectState()`);
  const vertexSelector=id=>'#igBoundaryView [data-ig-vertex="'+id+'"]';
  const fullAnchor=()=>read(`['igAnchorUN','igAnchorUD','igAnchorVN','igAnchorVD'].map(id=>$(id).value)`);
  const custom=['1','3','1','2'];
  async function realTabTo(selector) {
    const seen=[];
    for(let count=0;count<80;count++) {
      await page.keyboard.press('Tab');
      const state=await read(`(()=>{const target=document.querySelector(${JSON.stringify(selector)}),e=document.activeElement;if(!e)return {};const s=getComputedStyle(e);return {target:e===target,id:e.id,vertex:e.dataset.igVertex,focusVisible:e.matches(':focus-visible'),outline:s.outlineStyle,stroke:s.stroke,strokeWidth:s.strokeWidth};})()`);
      seen.push(state);
      if(state.target) {check('S2 real Tab reaches visible keyboard target '+selector,state.focusVisible&&(state.outline!=='none'||parseFloat(state.strokeWidth)>=5),seen);return;}
    }
    check('S2 real Tab reaches visible keyboard target '+selector,false,seen);
  }

  async function compactTabTo(selector) {
    const seen=[];
    for(let count=0;count<80;count++) {
      await page.keyboard.press('Tab');
      const row=await read(`(()=>{const target=document.querySelector(${JSON.stringify(selector)}),e=document.activeElement,s=e&&getComputedStyle(e),dot=e?.querySelector('.gi-vertex-dot,.gi-anchor-dot'),ds=dot&&getComputedStyle(dot);return {target:e===target,focusVisible:e?.matches(':focus-visible'),outline:s?.outlineStyle,strokeWidth:ds?.strokeWidth,vertex:e?.dataset.giVertex,anchor:e?.dataset.giAnchor};})()`);seen.push(row);
      if(row.target){check('S2 compact real Tab reaches visible original SVG button '+selector,row.focusVisible&&(row.outline!=='none'||parseFloat(row.strokeWidth)>=3),seen);return;}
    }
    check('S2 compact real Tab reaches visible original SVG button '+selector,false,seen);
  }
  async function compactKeyboardPair(kind,first,next,key) {
    const attr=kind==='vertex'?'data-gi-vertex':'data-gi-anchor',selector='['+attr+'="'+first+'"]',nextSelector='['+attr+'="'+next+'"]';
    await compactTabTo(selector);await page.keyboard.press(key);await settle();
    check('S2 compact '+kind+' '+key+' keeps focus on replacement matching exact identity',await read(`document.activeElement===document.querySelector(${JSON.stringify(selector)})&&document.activeElement.isConnected&&document.activeElement.getAttribute('aria-pressed')==='true'`));
    await page.keyboard.press('Tab');
    check('S2 compact '+kind+' next real Tab continues at exact following native button',await read(`document.activeElement===document.querySelector(${JSON.stringify(nextSelector)})&&document.activeElement.matches(':focus-visible')`));
    await page.keyboard.press(key==='Enter'?' ':'Enter');await settle();
    check('S2 compact '+kind+' alternate Enter/Space keeps next exact replacement focused',await read(`document.activeElement===document.querySelector(${JSON.stringify(nextSelector)})&&document.activeElement.getAttribute('aria-pressed')==='true'`));
  }

  async function pointerSvg(selector) {
    await disclose(selector);await page.locator(selector).scrollIntoViewIfNeeded();
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(resolve)));
    const point=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),b=e.getBBox(),m=e.getScreenCTM(),p=new DOMPoint(b.x+b.width/2,b.y+b.height/2).matrixTransform(m),h=document.elementFromPoint(p.x,p.y),r=e.getBoundingClientRect();return {x:p.x,y:p.y,width:r.width,height:r.height,hit:h===e||e.contains(h),target:e.dataset.igVertex||e.dataset.giAnchor,hitTag:h?.tagName,hitId:h?.id};})()`);
    check('S2 one unobstructed actual SVG pointer target '+selector,point.hit,point);
    await page.mouse.click(point.x,point.y);await settle();
  }
  async function closeMainDrawers() {
    if(await read(`innerWidth<=900&&document.body.classList.contains('drawer-right-open')`))await click('#app .drawer-close[data-close-panel="right"]');
    if(await read(`innerWidth<=900&&document.body.classList.contains('drawer-left-open')`))await click('#app .drawer-close[data-close-panel="left"]');
  }
  async function mainInspector() {
    const inspect=()=>read(`(()=>{const panel=document.querySelector('#app .sidebar-right'),target=$('gridObjectOpen');
      function painted(e){if(!e)return {ok:false};const s=getComputedStyle(e),r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {ok:s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0&&r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight&&e.contains(hit),position:s.position,left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,hit:e.contains(hit)};}
      const p=painted(panel),t=painted(target),selected=document.body.classList.contains('canvas-composition')&&document.body.classList.contains('canvas-has-inspector')&&!!panel?.querySelector('#gridInlineInspector');
      return {width:innerWidth,selected,panel:p,target:t,targetInsidePanel:!!target&&panel.contains(target)&&t.left>=p.left&&t.right<=p.right&&t.top>=p.top&&t.bottom<=p.bottom};})()`);
    const before=await inspect();
    if(before.width<=900&&before.selected&&before.panel.position==='fixed'&&before.panel.ok&&before.target.ok&&before.targetInsidePanel){
      check('S2 selected composition already exposes real fixed inspector and reachable original full-workspace action',before.panel.ok&&before.target.ok&&before.targetInsidePanel,before);return;
    }
    // Retain the established ordinary drawer route for all other layouts.
    if(await read(`innerWidth<=900&&!document.body.classList.contains('drawer-right-open')`))await click('#toggleRight');
    const after=await inspect();
    check('S2 original inspector full-workspace action is painted inside panel and hit-testable after ordinary opening',after.panel.ok&&after.target.ok&&after.targetInsidePanel,after);
  }
  async function openBinding() {
    await closeMainDrawers();await click('#btnZoom');
    // The fixture card's native layer location is explicit; fit once on mobile.
    if(await read('innerWidth===390')){await page.keyboard.press('f');await settle();}
    const lesson='#ocSelectionSummary .guidance-dismiss';
    if(await visible(lesson))await click(lesson);
    await click('.ocard[data-kind="grid-binding"][data-id="901"]');
    await mainInspector();
    await click('#gridObjectOpen');
    await wait(`$('infiniteGridWorkspace')?.open&&$('igVertex')?.value==='outer:0'&&!!$('igBoundaryView')?.querySelector('[data-ig-vertex="hole:0:0"]')`);
    await settle();
  }
  async function discard(accept) {
    await click('#igDiscardDraft');await wait(`!!$('igDiscardConfirmation')`);
    check('S2 inline discard retains original question',await read(`$('igDiscardQuestion').textContent==='捨棄這份未發布的原始草稿？已保存到場景的網格保持不變。'&&$('igDiscardConfirmation').getAttribute('role')==='alertdialog'&&$('igDiscardConfirmation').getAttribute('aria-modal')==='true'`));
    await click(accept?'#igDiscardConfirm':'#igDiscardCancel');
    await wait(`!$('igDiscardConfirmation')`);
  }
  for(const width of [1382,390]) {
    await freshContext(width,width===390?844:804);await setup(fixtureLines);
    const created=await read(`(async()=>{
      const boundary=await apiRequest('boundary 901');if(!boundary.ok)throw Error(JSON.stringify(boundary));
      const line='grid-binding 901 on-boundary 901 from-system 901 vertex outer 0 geometry-hash '+boundary.geometryFingerprint+' cell -2 1 anchor 1 3 1 2';
      let response=await apiRequest('line '+line);
      if(response.preview){if(!response.preview.valid)throw Error(JSON.stringify(response));response=await apiRequest('line confirm '+response.preview.token);}
      if(!response.ok)throw Error(JSON.stringify(response));
      const positioned=await apiRequest('line canvas-pos grid-binding 901 800 100');if(!positioned.ok)throw Error(JSON.stringify(positioned));
      await renderObjects();return {boundaryBefore:boundary,boundary:await apiRequest('boundary 901'),createdLine:line,response,positioned,objects:await apiRequest('objects')};
    })()`);
    fs.writeFileSync(path.join(OUT,'s2-'+width+'-native-fixture.json'),JSON.stringify(created,null,2)+'\n');
    const baseline=await dump(),nativeBoundary=created.boundary;
    check('S2 disclosed canonical fixture has outer and hole keys and custom rational anchor '+width,nativeBoundary.loops.length===2&&nativeBoundary.loops.every(l=>l.vertices.length===4)&&created.objects.gridBindings.find(b=>b.id===901).anchor[0].num===1&&created.objects.gridBindings.find(b=>b.id===901).anchor[0].den===3,created);
    // Existing real gcanvas export is used later for a same-ID owner switch.
    await read(`(async()=>{window.__s2OwnerBBytes=await ReferenceWorkspace.exportBytes();return __s2OwnerBBytes.length;})()`);
    await openBinding();
    const placement=await read(`(()=>{const section=$('igBoundarySection'),form=$('igBindingForm'),step=$('igVertexSummary'),diagram=$('igBoundaryView');return {inRight:section.closest('.ig-inspector')!==null,stepNext:step.nextElementSibling===section,inForm:form.contains(section),diagramCount:document.querySelectorAll('#igBoundaryView').length,sectionCount:document.querySelectorAll('#igBoundarySection').length,parentWidth:section.getBoundingClientRect().width,svgWidth:diagram.getBoundingClientRect().width};})()`);
    check('S2 one existing real vertex diagram is in right binding step2 '+width,placement.inRight&&placement.inForm&&placement.stepNext&&placement.diagramCount===1&&placement.sectionCount===1,placement);
    check('S2 reopening custom one-third does not select a nearest nine-point preset '+width,equal(await fullAnchor(),custom)&&await read(`![...document.querySelectorAll('[data-ig-anchor]')].some(e=>e.getAttribute('aria-pressed')==='true')`)&&(await dump())===baseline);
    const fullNames=await read(`[...document.querySelectorAll('[data-ig-anchor]')].map(e=>e.textContent)`);
    check('S2 full-workspace nine names retain original shared vocabulary '+width,equal(fullNames,titleNames),fullNames);
    // Real outer and hole pointer selection, with independently read native keys.
    for(const id of ['outer:1','hole:0:0']) {
      await pointerSvg(vertexSelector(id));
      const [loop,index]=id.startsWith('outer:')?[-1,+id.split(':')[1]]:[+id.split(':')[1],+id.split(':')[2]];
      const native=nativeBoundary.loops[loop+1].vertices[index];
      const selected=await read(`(()=>{const e=document.querySelector(${JSON.stringify(vertexSelector(id))});return {value:$('igVertex').value,key:e.dataset.igVertexKey,label:e.getAttribute('aria-label'),summary:$('igVertexSummary').textContent};})()`);
      check('S2 normal SVG pointer and dropdown share exact native vertex identity '+id+' '+width,selected.value===id&&selected.key===String(native.key)&&selected.label.includes(String(native.uv[0]))&&selected.label.includes(String(native.uv[1]))&&(await dump())===baseline,selected);
    }
    for(const [id,key] of [['outer:2','Enter'],['hole:0:2','Space']]) {
      await realTabTo(vertexSelector(id));await page.keyboard.press(key);await settle();
      const selected=await read(`({value:$('igVertex').value,summary:$('igVertexSummary').textContent})`);
      check('S2 real '+key+' selects intended outer or hole vertex '+id+' '+width,selected.value===id&&(await dump())===baseline,selected);
    }
    const optionIndex=await read(`[...$('igVertex').options].filter(o=>!o.disabled).findIndex(o=>o.value==='outer:3')`);
    check('S2 actual outer dropdown option exists '+width,optionIndex>=0);
    await click('#igVertex');await page.keyboard.press('Home');
    for(let option=0;option<optionIndex;option++)await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');await settle();
    check('S2 actual dropdown redraws same real vertex and preserves exact custom anchor '+width,await read(`$('igVertex').value==='outer:3'&&document.querySelector('[data-ig-vertex="outer:3"]').getAttribute('fill')==='#c66b2c'`)&&equal(await fullAnchor(),custom)&&(await dump())===baseline);
    // Native already supports these same rational presets; no new snapping policy.
    for(let index=0;index<9;index++) {
      const u=index%3,v=Math.floor(index/3),selector='[data-ig-anchor="'+u+','+v+'"]';
      await click(selector);const values=(await fullAnchor()).map(Number);
      check('S2 full nine-point preset uses exact existing half fractions '+index+' '+width,values[0]*2===u*values[1]&&values[2]*2===v*values[3]&&await read(`document.querySelector(${JSON.stringify(selector)}).getAttribute('aria-pressed')==='true'`)&&(await dump())===baseline,values);
    }
    await fill('#igAnchorUN',1);await fill('#igAnchorUD',3);await fill('#igAnchorVN',1);await fill('#igAnchorVD',2);
    const beforeRaw=await raw(),beforeState=await project(),beforeDialogs=dialogs.length;
    const order=await read(`(()=>{const a=[...document.querySelector('.ig-footer-actions').children].filter(e=>!e.hidden),r=id=>$(id).getBoundingClientRect();return {first:a[0].id,last:a.at(-1).id,discard:r('igDiscardDraft'),primary:r('igSaveBinding')};})()`);
    check('S2 discard sits left of active right primary operation '+width,order.first==='igDiscardDraft'&&order.primary.x>=order.discard.right-1,order);
    await discard(false);
    check('S2 normal Cancel returns exact raw draft native scene and focus '+width,equal(await raw(),beforeRaw)&&(await dump())===baseline&&await read(`$('infiniteGridWorkspace').open&&document.activeElement===$('igDiscardDraft')`)&&equal(await project(),beforeState)&&dialogs.length===beforeDialogs);
    await click('#igDiscardDraft');await wait(`!!$('igDiscardConfirmation')`);await page.keyboard.press('Escape');await settle();
    check('S2 real Escape dismisses only inline question and preserves raw native owner '+width,await read(`!$('igDiscardConfirmation')&&$('infiniteGridWorkspace').open&&document.activeElement===$('igDiscardDraft')`)&&equal(await raw(),beforeRaw)&&(await dump())===baseline&&equal(await project(),beforeState)&&dialogs.length===beforeDialogs);
    await shot('s2-inline-cancel-'+width);
    await discard(true);
    check('S2 explicit inline discard clears only raw feature and closes workspace '+width,(await raw())===null&&(await dump())===baseline&&await read(`!$('infiniteGridWorkspace').open`)&&dialogs.length===beforeDialogs);
    // The compact inspector retains the same custom fraction until explicit preset choice.
    await closeMainDrawers();await click('#btnZoom');if(width===390){await page.keyboard.press('f');await settle();}
    await click('.ocard[data-kind="grid-binding"][data-id="901"]');await mainInspector();
    await wait(`!!$('giAnchorView')&&$('giVertex').value==='outer:0'`);
    check('S2 inline inspector keeps custom one-third untouched and identical nine terminology '+width,await read(`$('giAnchorSummary').textContent==='自訂比例 · 1/3, 1/2'&&![...document.querySelectorAll('[data-gi-anchor]')].some(e=>e.getAttribute('aria-pressed')==='true')`)&&equal(await read(`[...document.querySelectorAll('[data-gi-anchor]')].map(e=>e.getAttribute('aria-label'))`),titleNames)&&(await dump())===baseline);
    for(let index=0;index<9;index++) {
      const u=index%3,v=Math.floor(index/3),selector='[data-gi-anchor="'+u+','+v+'"]';
      await pointerSvg(selector);
      const expected=[u===2?1:u,u===1?2:1,v===2?1:v,v===1?2:1];
      const summary=titleNames[index]+' · '+expected[0]+'/'+expected[1]+', '+expected[2]+'/'+expected[3];
      check('S2 compact nine-point pointer retains exact same native preset '+index+' '+width,await read(`document.querySelector(${JSON.stringify(selector)}).getAttribute('aria-pressed')==='true'&&$('giAnchorSummary').textContent===${JSON.stringify(summary)}`)&&(await dump())===baseline);
    }

    // Added coverage for the adopted compact controls. Source expected to retain
    // exact real focused vertex/anchor after redraw, matching the full contract.
    const compactNativeAnchor=structuredClone(created.objects.gridBindings.find(b=>b.id===901).anchor);
    await compactKeyboardPair('vertex','outer:0','outer:1','Enter');
    check('S2 compact keyboard outer vertex agrees with exact original dropdown '+width,await read(`$('giVertex').value==='outer:1'`)&&(await dump())===baseline);
    await compactKeyboardPair('vertex','hole:0:0','hole:0:1',' ');
    check('S2 compact keyboard hole vertex agrees with exact original dropdown '+width,await read(`$('giVertex').value==='hole:0:1'`)&&(await dump())===baseline);
    await compactKeyboardPair('anchor','0,0','1,0','Enter');
    check('S2 compact keyboard anchor changes only draft to same native nine-point fractions '+width,await read(`$('giAnchorSummary').textContent==='上中 · 1/2, 0/1'`)&&equal(await read(`oc.gridBindings.find(b=>b.id===901).anchor`),compactNativeAnchor)&&(await dump())===baseline);
    const compactDeletion=await read(`(()=>{const button=$('gridObjectDelete'),disclosure=button.closest('details');return {closed:!disclosure?.open,isolated:!!disclosure?.classList.contains('gi-delete-section'),footer:!!disclosure?.closest('.gi-footer'),inActions:!!button.closest('.gi-actions'),nodeCount:document.querySelectorAll('#gridObjectDelete').length};})()`);
    check('S2 compact original delete node is unique and isolated in closed footer disclosure '+width,compactDeletion.closed&&compactDeletion.isolated&&compactDeletion.footer&&!compactDeletion.inActions&&compactDeletion.nodeCount===1,compactDeletion);
    await read(`(()=>{const node=$('gridObjectDelete');window.__s2RetiredCompactDelete={node,callback:node.onclick};return true;})()`);
    const compactDeleteRaw=await raw(),compactDeleteProject=await project();
    await click('.gi-delete-section > summary');await page.locator('#gridObjectDelete').click();
    await wait(`!!document.querySelector('dialog.reference-impact[open]')`);
    check('S2 compact delete uses exactly existing native delete preview before mutation '+width,(await dump())===baseline&&await read(`(()=>{const ds=[...document.querySelectorAll('dialog.reference-impact[open]')];return ds.length===1&&ds[0].querySelector('code')?.textContent.trim()==='delete grid-binding 901'&&!ds[0].querySelector('#impact-confirm').disabled;})()`));
    await click('dialog.reference-impact[open] .impact-actions button:first-child');await settle();
    check('S2 compact normal delete preview Cancel preserves exact native project raw and original binding '+width,(await dump())===baseline&&equal(await raw(),compactDeleteRaw)&&equal(await project(),compactDeleteProject)&&equal(await read(`oc.gridBindings.find(b=>b.id===901).anchor`),compactNativeAnchor)&&await read(`!document.querySelector('dialog.reference-impact[open]')&&$('gridObjectDelete').isConnected`));

    // Full workspace opens the saved binding, not the abandoned compact draft.
    await click('#gridObjectOpen');await wait(`$('infiniteGridWorkspace').open&&$('igVertex').value==='outer:0'`);
    check('S2 full open restores saved custom fraction after compact-only choices '+width,equal(await fullAnchor(),custom)&&(await dump())===baseline);
    const deletion=await read(`(()=>{const b=$('igDeleteBinding'),d=b.closest('details');return {separate:!!d?.classList.contains('ig-delete-section'),closed:!d?.open,text:d?.querySelector(':scope>summary')?.textContent,locatedInBinding:d?.closest('#igBindingForm')!==null,buttonId:b.id};})()`);
    check('S2 original binding-delete action is isolated in its own closed disclosure '+width,deletion.separate&&deletion.closed&&deletion.locatedInBinding&&deletion.buttonId==='igDeleteBinding',deletion);
    const deleteRaw=await raw(),deleteState=await project();
    await click('.ig-delete-section > summary');await page.locator('#igDeleteBinding').click();
    await wait(`!!document.querySelector('dialog.reference-impact[open]')`);
    check('S2 original isolated delete still obtains actual native preview before write '+width,(await dump())===baseline&&await read(`!!document.querySelector('dialog.reference-impact[open] .ig-impact-title')`));
    await click('dialog.reference-impact[open] .impact-actions button:first-child');
    await wait(`!document.querySelector('dialog.reference-impact[open]')`);await settle();
    check('S2 normal delete preview Cancel preserves native binding raw and custom fraction '+width,(await dump())===baseline&&equal(await fullAnchor(),custom)&&equal(await raw(),deleteRaw)&&equal(await project(),deleteState)&&await read(`$('infiniteGridWorkspace').open&&!$('igDeleteBinding').disabled`));
    // Scheduling-only diagnostic: keep the real old confirmation callback, switch
    // to an actual exported same-ID project through the public import API, create
    // B's draft with real typing, then deliver the retired callback unchanged.
    await fill('#igCellI','-4');await click('#igDiscardDraft');await wait(`!!$('igDiscardConfirmation')`);
    const ownerA=await project();
    await read(`(()=>{const node=$('igDiscardConfirm');window.__s2RetiredDiscard={node,callback:node.onclick};return true;})()`);
    const interrupt=await read(`(async()=>{await ReferenceWorkspace.importBytes(__s2OwnerBBytes,'s2-same-id-owner-b.gcanvas');await renderObjects();return {state:ReferenceWorkspace.getProjectState(),oldConnected:__s2RetiredDiscard.node.isConnected,oldWorkspaceOpen:$('infiniteGridWorkspace').open};})()`);
    check('S2 real same-ID project import retires old workspace confirmation owner '+width,interrupt.state.id===ownerA.id&&interrupt.state.contextToken!==ownerA.contextToken&&!interrupt.oldConnected&&!interrupt.oldWorkspaceOpen,interrupt);
    await openBinding();await fill('#igCellI','-5');const bRaw=await raw(),bState=await project(),bWorld=await dump();

    const compactLateRequests=[];const compactLateCapture=request=>{if(request.method()==='POST'&&new globalThis.URL(request.url()).pathname==='/api')compactLateRequests.push(request.postData());};
    page.on('request',compactLateCapture);
    const compactLate=await read(`(()=>{const old=__s2RetiredCompactDelete;old.callback.call(old.node);return {oldConnected:old.node.isConnected,newOpen:$('infiniteGridWorkspace').open,newRaw:$('igCellI')?.value,impact:!!document.querySelector('dialog.reference-impact[open]')};})()`);
    await settle();page.off('request',compactLateCapture);
    check('S2 retired compact delete original current guard submits zero native API requests '+width,!compactLate.oldConnected&&compactLate.newOpen&&compactLate.newRaw==='-5'&&!compactLate.impact&&compactLateRequests.length===0,compactLateRequests);
    check('S2 retired compact delete callback leaves exact B project raw and native world untouched '+width,equal(await raw(),bRaw)&&equal(await project(),bState)&&(await dump())===bWorld);

    const stale=await read(`(()=>{const old=__s2RetiredDiscard;old.callback.call(old.node);return {newOpen:$('infiniteGridWorkspace').open,value:$('igCellI')?.value,oldConnected:old.node.isConnected,prompt:!!$('igDiscardConfirmation')};})()`);
    check('S2 retired real confirmation callback cannot clear new owner raw or close B '+width,stale.newOpen&&stale.value==='-5'&&!stale.oldConnected&&!stale.prompt&&equal(await raw(),bRaw)&&equal(await project(),bState)&&(await dump())===bWorld,stale);
    await discard(true);check('S2 B remains normally discardable after rejected stale callback '+width,(await raw())===null&&(await dump())===bWorld);
    const eventRows=await read(`window.__ui123Input`);
    check('S2 tested editing events are trusted normal pointer and keyboard '+width,eventRows.filter(e=>['pointerdown','pointerup','click','keydown','input'].includes(e.type)).every(e=>e.trusted)&&eventRows.some(e=>e.type==='keydown'&&e.key==='Enter')&&eventRows.some(e=>e.type==='keydown'&&e.key===' '),eventRows.filter(e=>e.type==='keydown'));
    await shot('s2-complete-'+width);
  }
}
});

(async()=>{let completed=false;try{check('frozen checkout matches full SHA and is clean',run.head===EXPECTED&&run.dirty==='',{head:run.head,dirty:run.dirty});run.runtimeBefore=await runtime('before');check('isolated runtime is fresh and belongs to exact checkout',run.runtimeBefore.fresh===true&&path.resolve(run.runtimeBefore.root)===ROOT,run.runtimeBefore);run.executables=nativeIdentity(run.runtimeBefore);browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,chromiumSandbox:true,args:['--no-proxy-server']});run.browserExecuted=true;run.browserVersion=browser.version();const launcher=path.resolve(process.env.GEOMETRY_CHROME||'/usr/bin/chromium');run.browserLauncher={path:launcher,realPath:fs.realpathSync(launcher),sha256:sha(launcher),version:browser.version(),identityLimit:'Launcher bytes and browser reported version recorded; native bridge live executable bytes checked separately'};for(const group of requested){current=group;const startedAt=new Date().toISOString(),before=results.length;let ok=false;try{await groups[group]();ok=true;}catch(error){emit('GROUP_ERROR',group,error.stack||error.message);if(!results.at(-1)||results.at(-1).ok)results.push({group,name:'unexpected execution failure',ok:false,error:error.stack||error.message});await shot('failure').catch(()=>{});}finally{if(page&&!page.isClosed()){fs.writeFileSync(path.join(OUT,group+'-trusted-input-events.json'),JSON.stringify(await read('window.__ui123Input').catch(error=>({error:error.message})),null,2)+'\n');}groupResults.push({group,startedAt,finishedAt:new Date().toISOString(),ok,checks:results.length-before});}}current='final';run.runtimeAfter=await runtime('after');check('runtime source/session fresh and unchanged after explicit scopes',run.runtimeAfter.fresh===true&&run.runtimeAfter.version===run.runtimeBefore.version&&run.runtimeAfter.session===run.runtimeBefore.session,run.runtimeAfter);run.headAfter=git(['rev-parse','HEAD']);run.dirtyAfter=git(['status','--porcelain']);check('all measured product and harness source identities remain frozen',run.headAfter===run.head&&run.dirtyAfter===run.dirty&&sourcePaths.every(p=>sha(path.join(ROOT,p))===run.sources[p])&&sha(__filename)===run.scriptSHA256);check('no unexpected page errors or native dialogs',errors.length===0,errors);completed=groupResults.length===requested.length;}catch(error){emit('PROBE_ERROR',current,error.stack||error.message);if(!results.at(-1)||results.at(-1).ok)results.push({group:current,name:'unexpected preparation/execution failure',ok:false,error:error.stack||error.message});}finally{await archiveInput().catch(()=>{});await context?.close();await browser?.close();run.finishedAt=new Date().toISOString();const passed=results.filter(r=>r.ok).length,failed=results.filter(r=>!r.ok).length,exitCode=completed&&failed===0?0:1;emit('UI123_RESULT',JSON.stringify({completed,passed,failed,exitCode,scope:run.scope,groupResults,out:OUT}));run.exitCode=exitCode;run.rawLogPath=log;run.rawLogSHA256=sha(log);fs.writeFileSync(path.join(OUT,'receipt.json'),JSON.stringify({run,completed,passed,failed,results,groupResults,errors,dialogs},null,2)+'\n');process.exitCode=exitCode;}})();
