'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const {execFileSync}=require('node:child_process');
const root='/workspace/geometry-wp60-a',P=require(root+'/geometry-web/project-store.js'),zip=require(root+'/geometry-web/vendor/fflate/umd/index.js');
const evidence='/tmp/wp60-evidence',url='http://127.0.0.1:18860/';
const checks=[],errors=[];const check=(name,actual,expected)=>{assert.deepEqual(actual,expected,name);checks.push({name,status:'pass'});console.log('PASS '+name);};
const snapshot=async page=>page.evaluate(async()=>({scene:(await api('dump')).text,refs:await api('references'),systems:(await api('objects')).gridSystems,state:ReferenceWorkspace.getProjectState(),features:ReferenceWorkspace.history.frame.context.featureAttachments}));
async function ready(page){await page.goto(url);await page.waitForFunction(()=>typeof ReferenceWorkspace!=='undefined'&&connection.phase==='ready');}
(async()=>{
  fs.mkdirSync(evidence,{recursive:true});
  const f=await require(root+'/tests/issue77_attachment_fixture.js').fixture(),Rooms=require(root+'/geometry-web/source-plane.js');
  const rooms={...f.payload,schema:Rooms.HISTORY_SCHEMA,legacyHistory:[{planeId:'plane-two-rooms',boundaryId:11,pageId:'legacy-page',records:[{id:'height',label:'歷史高度',value:null,unit:'mm',datum:'FFL',location:'未完成'}],reconstructionReview:null}]};
  const rawForm=Object.fromEntries(P.Features.sourceFields.map(field=>[field,'']));rawForm.igName=' 尚未提交 ';rawForm.igUStep='-';
  const draft={schema:P.Features.GRID_SCHEMA,draftId:'old-grid-draft',kind:'source',intent:'create',baseRef:null,inputRefs:[],rawForm};
  const native=fs.readFileSync(evidence+'/world.scene','utf8');
  fs.writeFileSync(evidence+'/rooms-candidate.scene',native+f.scene);
  const answers=execFileSync('/tmp/geometry-tests/bridge',[],{input:'loadfile '+evidence+'/rooms-candidate.scene\ndump\n',encoding:'utf8'}).trim().split('\n').map(JSON.parse);
  assert.equal(answers[0].ok,true,JSON.stringify(answers[0]));const scene=answers[1].text;
  const features={schema:P.Features.SCHEMA,records:[P.Features.record('grid-draft',draft),P.Features.record('source-rooms',rooms)]};
  const bytes=await P.pack(scene,{...f.base,format:P.FORMAT,projectId:'wp60-browser',featureAttachments:features},f.sources,zip);
  fs.writeFileSync(evidence+'/source-subdivision-rooms-v11.gcanvas',bytes);
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  try{
    let context=await browser.newContext({viewport:{width:1440,height:900},acceptDownloads:true});
    await context.addInitScript(()=>{window.showSaveFilePicker=undefined;}); // Actual download fallback; no writable handle simulation.
    let page=await context.newPage();
    const watch=page=>{page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});page.on('dialog',d=>d.accept());};watch(page);
    await ready(page);check('page identity',await page.title(),'構形 Canvas · 工程規格與空間建模');
    check('nonblank application',((await page.locator('body').innerText()).length>100),true);
    check('no framework overlay',await page.locator('[data-nextjs-dialog],.vite-error-overlay').count(),0);
    await page.locator('#projectFile').setInputFiles(evidence+'/source-subdivision-rooms-v11.gcanvas');
    await page.waitForFunction(()=>ReferenceWorkspace.getProjectState().id==='wp60-browser'&&!ReferenceWorkspace.busy,{timeout:30000});
    const first=await snapshot(page),loaded=await page.evaluate(async()=>[...await ReferenceWorkspace.exportBytes()]);
    const definitions=s=>s.split('\n').filter(line=>!line.startsWith('canvas-pos ')).join('\n');
    check('native formal definitions include all rules and exact refs',definitions(first.scene),definitions(scene));
    check('existing source-room history and raw grid draft preserved',first.features,features.records);
    check('rule highwater and unused sources preserved',first.systems.map(s=>[s.id,s.nextRuleKey,s.rules.map(r=>r.ruleKey)]),[[0,11,[7]],[22,0,[7]],[33,8,[]]]);
    const decoded=await P.unpack(new Uint8Array(loaded),zip);check('source PDF bytes preserved',decoded.sources.get(f.hash),f.bytes);
    check('v11 keeps existing source-room/history/draft capabilities',decoded.manifest.requiredCapabilities,[P.SUBDIVISION_CAPABILITY,P.Features.GRID_SCHEMA,Rooms.CAPABILITY,Rooms.HISTORY_CAPABILITY].sort());
    await page.screenshot({path:evidence+'/desktop-open.png'});
    // Exercise the existing shared save action, with a real browser download.
    const downloadPromise=page.waitForEvent('download');
    await page.locator('#fileMenuBtn').click();await page.locator('#btnSaveProject').click();
    const download=await downloadPromise;await download.saveAs(evidence+'/actual-save.gcanvas');
    const saved=await P.unpack(new Uint8Array(fs.readFileSync(evidence+'/actual-save.gcanvas')),zip);
    check('actual download retains native scene and saved layout',saved.scene,first.scene);check('actual download retains original source',saved.sources.get(f.hash),f.bytes);
    await context.close();
    context=await browser.newContext({viewport:{width:390,height:844},acceptDownloads:true});page=await context.newPage();watch(page);await ready(page);
    await page.locator('#projectFile').setInputFiles(evidence+'/actual-save.gcanvas');
    await page.waitForFunction(()=>ReferenceWorkspace.getProjectState().id==='wp60-browser'&&!ReferenceWorkspace.busy,{timeout:30000});
    const reopened=await snapshot(page);check('fresh browser context restores full native scene',reopened.scene,first.scene);check('fresh browser context preserves formal references',reopened.refs,first.refs);
    check('fresh browser context preserves raw attachments',reopened.features,first.features);
    check('fresh open does not restore previous undo stack',await page.evaluate(()=>ReferenceWorkspace.history.undo.length),1);
    await page.screenshot({path:evidence+'/mobile-reopen.png'});
    const entries=zip.unzipSync(new Uint8Array(fs.readFileSync(evidence+'/actual-save.gcanvas'))),bad=JSON.parse(new TextDecoder().decode(entries['manifest.json']));bad.requiredCapabilities=[];entries['manifest.json']=new TextEncoder().encode(JSON.stringify(bad));
    fs.writeFileSync(evidence+'/tampered.gcanvas',zip.zipSync(entries));
    const before=await snapshot(page);await page.locator('#projectFile').setInputFiles(evidence+'/tampered.gcanvas');
    await page.waitForTimeout(1000);const after=await snapshot(page);check('tampered file preserves world and project context',after,before);
    check('console and page errors',errors,[]);
    fs.writeFileSync(evidence+'/browser-results.json',JSON.stringify({completed:true,checks,errors,browserPlugin:'absent',agentBrowserCLI:'unavailable',browser:'Chromium',viewports:[[1440,900],[390,844]],fixtureCreation:'native/codec, not #61 rule editor UI'},null,2));
    await context.close();
  }finally{await browser.close();}
})().catch(e=>{fs.writeFileSync(evidence+'/browser-failure.txt',e.stack);console.error(e);process.exitCode=1;});
