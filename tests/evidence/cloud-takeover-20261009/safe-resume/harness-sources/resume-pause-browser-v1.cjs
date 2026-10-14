/* New safe Resume browser supplement. Fixtures are synthetic; the Pause,
   iframe teardown, Edit/Resume, native parameter edits and Finish/Cancel use
   the shipped controls. No forced click, reload shortcut, or mocked service. */
'use strict';
const fs=require('fs'),path=require('path'),os=require('os'),cp=require('child_process'),assert=require('assert/strict'),crypto=require('crypto');
const {chromium}=require('playwright');
const root=path.resolve(process.env.GEOMETRY_RESUME_ROOT||'<resume-repository-root>');
const url=process.env.GEOMETRY_TEST_URL,out=process.env.GEOMETRY_RESUME_OUT,feedback=process.env.GEOMETRY_FEEDBACK_DIR;
if(!url||![out,feedback].every(p=>p&&path.resolve(p).startsWith(os.tmpdir()+path.sep)))throw Error('Explicit URL and isolated TEMP evidence/feedback required');
const P=require(path.join(root,'geometry-web/project-store.js')),zip=require(path.join(root,'geometry-web/vendor/fflate/umd/index.js'));
const pdfFixture=require(path.join(root,'tests/fixtures/evidence_pdf.cjs'));
fs.mkdirSync(out,{recursive:true});
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const git=(...args)=>cp.execFileSync('git',args,{cwd:root,encoding:'utf8'}).trim();
const head=git('rev-parse','HEAD'),tree=git('rev-parse','HEAD^{tree}'),dirty=git('status','--porcelain')!=='';
assert.equal(dirty,false,'Frozen clean candidate required');
const results=[];let runtime,browserIdentity;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
async function ready(frame){await frame.waitForFunction(()=>typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy);}
async function snapshot(frame){return frame.evaluate(async()=>({world:(await apiRequest('dump')).text,state:ReferenceWorkspace.getProjectState(),
 catalog:ReferenceWorkspace.readScenarioCatalog().catalog,drafts:ReferenceWorkspace.getEngineeringDrafts(),assembly:ReferenceWorkspace.getAssemblyDrafts(),
 history:{undo:ReferenceWorkspace.history.undo.map(s=>s.action),redo:ReferenceWorkspace.history.redo.map(s=>s.action)}}));}
async function packageOf(frame,name){const data=await frame.evaluate(async()=>{const b=await ReferenceWorkspace.exportBytes();let s='';for(const v of b)s+=String.fromCharCode(v);return btoa(s);});
 const bytes=Buffer.from(data,'base64');fs.writeFileSync(path.join(out,name+'.gcanvas'),bytes);const unpacked=await P.unpack(bytes,zip);
 return {packageHash:hash(bytes),manifest:unpacked.manifest,scene:unpacked.scene,sources:[...unpacked.sources].map(([id,b])=>({id,hash:hash(b),bytes:b.length})).sort((a,b)=>a.id.localeCompare(b.id))};}
async function rootNative(page,context){return page.evaluate(async context=>{const r=await fetch('/api',{method:'POST',headers:{'Content-Type':'application/json','X-Geometry-Scenario':context},body:'{"cmd":"dump"}'});return {status:r.status,result:await r.json()};},context);}
async function stored(page,context){return page.evaluate(async context=>{
 const db=await new Promise((resolve,reject)=>{const q=indexedDB.open('geometry-canvas-recovery',1);q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error);});
 const keys=['geometry-scenario-resume-'+context,'geometry-scenario-resume-package-'+context];
 const rows=await new Promise((resolve,reject)=>{const tx=db.transaction('projects','readonly'),s=tx.objectStore('projects'),a=s.get(keys[0]),b=s.get(keys[1]);tx.oncomplete=()=>resolve({journal:a.result,record:b.result});tx.onerror=()=>reject(tx.error);});db.close();
 const b=rows.record?.bytes;if(b){let t='';for(const v of b)t+=String.fromCharCode(v);rows.record={...rows.record,bytesBase64:btoa(t)};delete rows.record.bytes;}return rows;
},context);}
function auditRequests(page){const calls=[];page.on('request',request=>{if(request.method()!=='POST')return;let body;try{body=request.postDataJSON();}catch(_){body=request.postData();}calls.push({route:new URL(request.url()).pathname,context:request.headers()['x-geometry-scenario']||null,body});});return calls;}
async function scenarios(page){await page.locator('#projectInfoButton').click();if(!await page.locator('#scenarioOpen').isVisible())await page.locator('.project-concepts summary').click();await page.locator('#scenarioOpen').click();}
async function parameter(frame,value,create=false){
 if(create){await frame.locator(await frame.evaluate(()=>innerWidth<=900)?'#mobileCreateObject':'#btnCreateObject').click();await frame.locator('#btnNewParameter').click();}
 else{await frame.locator('body').press('f');await frame.locator('.ocard[data-kind="parameter"]').first().click();}
 if(await frame.locator('#paramGridLessonClose').isVisible())await frame.locator('#paramGridLessonClose').click();
 if(create)await frame.locator('#paramName').fill('Resume authored parameter');
 await frame.locator('#paramFields [data-input]').first().fill(String(value));await frame.locator('#paramPreview').click();await frame.waitForFunction(()=>!document.querySelector('#paramConfirm').disabled);
 await frame.locator('#paramConfirm').click();await frame.waitForFunction(()=>!ParameterUI.pending);
}
async function metadataFixture(child,label){
 // Confirmed metadata/source fixture, not a claim of physical calibration input.
 // It creates the native-hash equality counterexample checked by this protocol.
 return child.evaluate(label=>{const W=ReferenceWorkspace,token=W.getProjectState().contextToken;W.assertEditable();
  W.context().name=label;W.calibrated(1,[[0,0],[10,0]],100,10,'cm');const p=W.active(1);p.opacity=.73;p.x=42;W.changed(1,true);
  W.setEngineeringDraft({id:'resume-latest-engineering',kind:'material',base_ref:null,data:{name:label,width:'123',length:'456'},updated_at:'2026-10-09T00:00:00.000Z'},token);
  W.setAssemblyDraft({id:'resume-latest-assembly',kind:'rule',base_ref:null,data:{id:1,version:1,name:label,slots:[],members:[],joints:[]},updated_at:'2026-10-09T00:00:00.000Z'},token);
  return {name:W.context().name,opacity:p.opacity,x:p.x,calibration:p.calibration};},label);
}
async function fresh(browser,width){const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage();page.on('dialog',d=>d.accept());
 await page.addLocatorHandler(page.locator('#paramGridLessonClose'),async n=>n.click());await page.goto(url);await ready(page);const old=await page.evaluate(()=>ReferenceWorkspace.getProjectState().id);
 await page.locator('#fileMenuBtn').click();await page.locator('#btnNewProject').click();await page.waitForFunction(id=>ReferenceWorkspace.getProjectState().id!==id&&!ReferenceWorkspace.busy,old);
 await parameter(page,200,true);
 // Real PDF file import/apply into a synthetic, explicitly created face.
 await page.evaluate(async()=>{const r=await apiRequest('line boundary 1 outline 0,0 4000,0 4000,3000 0,3000');if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();await enterFocus('face',1);fiShowTab('underlay');ReferenceWorkspace.chooseFile(1);});
 await page.locator('#referenceFile').setInputFiles({name:'resume-synthetic.pdf',mimeType:'application/pdf',buffer:pdfFixture()});await page.waitForFunction(()=>document.querySelector('#referenceDialog').open&&!document.querySelector('#refApply').disabled);
 await page.locator('#refApply').click();await page.waitForFunction(()=>!ReferenceWorkspace.busy&&!document.querySelector('#referenceDialog').open);
 await page.locator('#btnObj').click();await scenarios(page);await page.locator('#scenarioName').fill('A');await page.locator('#scenarioCapture').click();await page.waitForFunction(()=>ReferenceWorkspace.readScenarioCatalog().catalog?.scenarios.length===1&&!document.querySelector('#scenarioCapture').disabled);
 await page.locator('#scenarioName').fill('B');await page.locator('#scenarioFork').click();await page.waitForFunction(()=>ReferenceWorkspace.readScenarioCatalog().catalog?.scenarios.length===2&&!document.querySelector('#scenarioCapture').disabled);
 const ids=await page.evaluate(()=>ReferenceWorkspace.readScenarioCatalog().catalog.scenarios.map(s=>s.scenarioId));await page.locator('#scenarioAfter').selectOption(ids[1]);return page;
}
async function liveBrowserIdentity(){const processes=cp.execFileSync('ps',['-eo','pid=,ppid=,args='],{encoding:'utf8'}).split('\n');
 const rows=processes.map(l=>l.trim().match(/^(\d+)\s+(\d+)\s+(.+)$/)).filter(Boolean).filter(r=>+r[2]===process.pid&&r[3].includes('--remote-debugging-pipe'));
 assert.equal(rows.length,1,'Owned browser process belongs directly to this test Node');const pid=+rows[0][1],exe=fs.realpathSync('/proc/'+pid+'/exe');
 return {node:{pid:process.pid,exe:process.execPath,version:process.version,sha256:hash(fs.readFileSync(process.execPath))},browser:{pid,exe,sha256:hash(fs.readFileSync('/proc/'+pid+'/exe')),cmdline:rows[0][3]}};
}
(async()=>{
 runtime=await fetch(new URL('/runtime',url)).then(r=>r.json());assert.ok(runtime.fresh&&path.resolve(runtime.root)===root,'Fresh exact selected-worktree service');
 const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,chromiumSandbox:true});browserIdentity=await liveBrowserIdentity();
 try{for(const width of [1280,390])for(const terminal of ['finish','cancel']){
  const record={name:'pause-resume-'+terminal+'-'+width,width,terminal,ok:false,assertions:[],pageErrors:[],preconditionOrHarnessError:null};results.push(record);
  const check=(label,value)=>{record.assertions.push({label,passed:value===true});assert.equal(value,true,label);console.log('PASS '+record.name+' '+label);};
  let page;try{page=await fresh(browser,width);page.on('pageerror',e=>record.pageErrors.push(e.message));const calls=auditRequests(page),aBefore=await snapshot(page),catalogBefore=aBefore.catalog;
   await page.locator('#scenarioEdit').click();await page.waitForFunction(()=>!document.querySelector('#scenarioFinishEdit').disabled);let child=page.frames().find(f=>f.url().includes('scenario='));assert.ok(child,'Actual isolated B frame');
   await parameter(child,300);const nativeBeforeMetadata=(await rootNative(page,await child.evaluate(()=>connection.session))).result.text;
   await metadataFixture(child,'Latest B '+width+' '+terminal);const active=await page.evaluate(()=>ReferenceWorkspace.readScenarioEditorTicket()),bBefore=await snapshot(child),fullBefore=await packageOf(child,record.name+'-before-pause');
   check('metadata-only fixture retains the latest unchanged native B while source and drafts are complete',bBefore.world===nativeBeforeMetadata&&fullBefore.manifest.name==='Latest B '+width+' '+terminal&&fullBefore.manifest.sources.length===1&&fullBefore.manifest.faces[0].pages[0].opacity===.73&&fullBefore.manifest.engineeringDrafts.records[0].data.width==='123'&&fullBefore.manifest.assemblyDrafts.records[0].data.name===fullBefore.manifest.name&&fullBefore.sources[0].hash===hash(pdfFixture()));
   check('live A confirmed state is unchanged by B native and metadata editing',same(aBefore,await snapshot(page)));
   const ownedBefore=await page.evaluate(async()=>navigator.locks.query());
   check('B owns its native editor and native-specific recovery locks before Pause',ownedBefore.held.some(l=>l.name==='geometry-canvas-service-editor-'+active.context)&&ownedBefore.held.some(l=>l.name==='geometry-canvas-recovery-geometry-scenario-recovery-'+active.context));
   const beforePauseCalls=calls.length;await page.locator('#scenarioPauseEdit').click();await page.waitForFunction(()=>!document.querySelector('#scenarioEditorDialog').open&&document.querySelector('#scenarioEditorFrame').getAttribute('src')==='about:blank');
   await page.waitForFunction(async context=>{const q=await navigator.locks.query();return !q.held.some(l=>l.name==='geometry-canvas-service-editor-'+context||l.name==='geometry-canvas-recovery-geometry-scenario-recovery-'+context);},active.context);
   const paused=await stored(page,active.context),storedBytes=Buffer.from(paused.record.bytesBase64,'base64'),storedProject=await P.unpack(storedBytes,zip);
   check('Pause blank frame releases both B leases while keeping exact active ticket and live native B',same(active,await page.evaluate(()=>ReferenceWorkspace.readScenarioEditorTicket()))&&(await rootNative(page,active.context)).result.text===bBefore.world&&paused.journal.eligible===true);
   check('strict Pause record retains exact full latest package and source closure',paused.journal.packageHash===hash(storedBytes)&&same(storedProject.manifest,fullBefore.manifest)&&storedProject.scene===fullBefore.scene&&[...storedProject.sources].every(([id,b])=>fullBefore.sources.some(s=>s.id===id&&s.hash===hash(b))));
   check('Pause does not close or create native B',calls.slice(beforePauseCalls).filter(c=>c.route==='/scenarios/editor'&&['create','close'].includes(c.body?.action)).length===0);
   const resumeStart=calls.length;await page.locator('#scenarioEdit').click();await page.waitForFunction(()=>!document.querySelector('#scenarioFinishEdit').disabled&&document.querySelector('#scenarioEditorDialog').open&&!document.querySelector('#scenarioEditorFrame').inert);
   child=page.frames().find(f=>f.url().includes('scenario='));assert.ok(child);await ready(child);const fullAfter=await packageOf(child,record.name+'-after-resume'),stateAfter=await snapshot(child),resumeCalls=calls.slice(resumeStart),resumed=await stored(page,active.context);
   check('Resume resolves the same native B and restores exact complete metadata/source package',await child.evaluate(()=>connection.session)===active.context&&same(fullAfter.manifest,fullBefore.manifest)&&fullAfter.scene===fullBefore.scene&&same(fullAfter.sources,fullBefore.sources)&&stateAfter.world===bBefore.world&&stateAfter.state.dirty===bBefore.state.dirty&&stateAfter.state.saved===bBefore.state.saved);
   check('Resume consumed only its eligible journal and left exact ticket and parent A unchanged',resumed.journal.eligible===false&&same(active,await page.evaluate(()=>ReferenceWorkspace.readScenarioEditorTicket()))&&same(aBefore,await snapshot(page)));
   const ownedAfter=await page.evaluate(async()=>navigator.locks.query());
   check('resumed B reacquires both exact native-specific editor and recovery locks',ownedAfter.held.some(l=>l.name==='geometry-canvas-service-editor-'+active.context)&&ownedAfter.held.some(l=>l.name==='geometry-canvas-recovery-geometry-scenario-recovery-'+active.context));
   check('Resume sent exact resolve once with zero upload/create/close/reset/loadfile/native mutation',resumeCalls.filter(c=>c.route==='/scenarios/editor'&&c.body?.action==='resolve').length===1&&resumeCalls.every(c=>!c.route.startsWith('/upload')&&!(c.route==='/scenarios/editor'&&['create','close'].includes(c.body?.action))&&!(c.route==='/api'&&/^(line |drag |reset$|default$|undo$|redo$|loadfile |engineering-confirm |assembly-confirm )/.test(c.body?.cmd||''))));
   await parameter(child,400);const later=await snapshot(child),laterPackage=await packageOf(child,record.name+'-later-edit');
   check('resumed B accepts a new normal parameter edit without touching A or prior metadata',later.world!==bBefore.world&&laterPackage.manifest.name===fullBefore.manifest.name&&same(laterPackage.manifest.faces,fullBefore.manifest.faces)&&same(laterPackage.manifest.engineeringDrafts,fullBefore.manifest.engineeringDrafts)&&same(aBefore,await snapshot(page)));
   await page.locator(terminal==='finish'?'#scenarioFinishEdit':'#scenarioCancelEdit').click();await page.waitForFunction(()=>!document.querySelector('#scenarioEditorDialog').open);const aAfter=await snapshot(page),closed=await rootNative(page,active.context);
   check('normal '+terminal+' retires exact B context and clears its ticket',closed.status===410&&(await page.evaluate(()=>ReferenceWorkspace.readScenarioEditorTicket()))===null);
   if(terminal==='finish')check('Finish preserves live A and complete A archive while recording latest full B once',aAfter.world===aBefore.world&&same(aAfter.catalog.scenarios[0],catalogBefore.scenarios[0])&&aAfter.catalog.scenarios[1].snapshot.worldScene===later.world&&same(aAfter.catalog.scenarios[1].snapshot.projectManifest,laterPackage.manifest)&&aAfter.history.undo.length===aBefore.history.undo.length+1&&aAfter.history.undo.at(-1)==='保存候選方案');
   else check('Cancel preserves complete confirmed A and its original B archive',same(aBefore,aAfter));
   check('no unexpected browser exception',record.pageErrors.length===0);record.ok=true;record.requests=calls;
   fs.writeFileSync(path.join(out,record.name+'-state.json'),JSON.stringify({active,aBefore,bBefore,fullBefore,stateAfter,fullAfter,later,laterPackage,aAfter,paused:{journal:paused.journal,project:paused.record.project},resumedJournal:resumed.journal,requests:calls},null,2));
  }catch(error){record.error=error.stack;record.preconditionOrHarnessError=error instanceof assert.AssertionError?null:error.message;if(page)await page.screenshot({path:path.join(out,record.name+'-failure.png')}).catch(()=>{});throw error;}
  finally{if(page)await page.context().close();fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2));}
 }}finally{await browser.close();fs.writeFileSync(path.join(out,'identity.json'),JSON.stringify({head,tree,dirty,runtime,browserIdentity,script:{path:__filename,sha256:hash(fs.readFileSync(__filename))},scope:'Four synthetic browser lifecycles; not full CDP, physical mobile, abrupt reload or cross-service Resume'},null,2));}
 console.log('RESUME_PAUSE_RESULT '+JSON.stringify({head,completed:true,cases:results.length,pass:results.filter(r=>r.ok).length,fail:results.filter(r=>!r.ok).length,assertions:results.reduce((n,r)=>n+r.assertions.length,0)}));
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
