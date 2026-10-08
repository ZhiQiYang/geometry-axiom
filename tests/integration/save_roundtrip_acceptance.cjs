// Focused acceptance: real UI commands/forms, Save download, chooser reopen.
// Runtime.evaluate only observes state except explicitly named save-error injection.
const fs=require('fs'),path=require('path'),os=require('os'),net=require('net'),crypto=require('crypto'),assert=require('assert/strict'),{execFileSync}=require('child_process');
const ROOT=path.resolve(__dirname,'../..'),ENV=process.env;
const URL=ENV.GEOMETRY_TEST_URL,feedback=ENV.GEOMETRY_FEEDBACK_DIR;
if(!URL||!feedback||!path.isAbsolute(feedback)||!path.resolve(feedback).startsWith(os.tmpdir()+path.sep))throw Error('Explicit isolated GEOMETRY_TEST_URL and dedicated TEMP GEOMETRY_FEEDBACK_DIR required');
const targetURL=new globalThis.URL(URL);
if(!['http:','https:'].includes(targetURL.protocol)||!['127.0.0.1','localhost','[::1]'].includes(targetURL.hostname)||!targetURL.port||targetURL.pathname!=='/'||targetURL.username||targetURL.password||targetURL.search||targetURL.hash)throw Error('Expected an explicit isolated loopback HTTP(S) URL with a non-default port and root path');
const expectedRoot=path.resolve(ENV.GEOMETRY_RUNTIME_ROOT||ROOT);
const helper=path.join(ROOT,'geometry-web/docs/evidence/qa-acceptance-d6b4b45-20261005/tools/qa_cdp.js');
const qa=require(helper);
const OUT=path.resolve(ENV.GEOMETRY_SAVE_EVIDENCE||path.join(os.tmpdir(),'geometry-tests','save-roundtrip-'+process.pid));
const inside=(parent,child)=>{const r=path.relative(parent,child);return !r||r!=='..'&&!r.startsWith('..'+path.sep)&&!path.isAbsolute(r);};
if(inside(ROOT,OUT)||inside(expectedRoot,OUT))throw Error('Evidence must stay outside both harness and runtime checkouts');
if(fs.existsSync(OUT)&&fs.readdirSync(OUT).length)throw Error('Evidence output must be new or empty; refusing potentially stale downloads');
fs.mkdirSync(OUT,{recursive:true});
const testEnvironment=['GEOMETRY_TEST_URL','GEOMETRY_FEEDBACK_DIR','GEOMETRY_RUNTIME_ROOT','GEOMETRY_SAVE_EVIDENCE','GEOMETRY_CHROME','GEOMETRY_CHROME_FLAGS','GEOMETRY_CDP_PORT'];
const record={argv:[process.execPath,...process.argv.slice(1)],cwd:process.cwd(),expectedRuntimeRoot:expectedRoot,environment:Object.fromEntries(testEnvironment.filter(k=>ENV[k]!==undefined).map(k=>[k,ENV[k]])),harnessSha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),helperSha256:crypto.createHash('sha256').update(fs.readFileSync(helper)).digest('hex')};
async function identity(){const runtime=await fetch(new globalThis.URL('/runtime',URL)).then(r=>r.json());assert.equal(runtime.fresh,true,'formal runtime must be fresh');assert.equal(path.resolve(runtime.root),expectedRoot,'runtime must belong to explicit expected worktree');const git=args=>execFileSync('git',args,{cwd:expectedRoot,encoding:'utf8'});return {runtime,head:git(['rev-parse','HEAD']).trim(),tree:git(['rev-parse','HEAD^{tree}']).trim(),status:git(['status','--porcelain=v1'])};}
const BASE='boundary 311 outline 0,0 4000,0 4000,3000 0,3000\nplacement 311 on boundary 311 origin 0 0 2500 u +x v +y\ncanvas-pos boundary 311 60 60\n';
const projection={kind:'space-boundary-plan',view:'bottom',region:'interior',wallSide:'outside'};
const results=[],logs=[];let b,phase='start';
const check=(name,actual,expected=true)=>{assert.deepEqual(actual,expected,name);results.push({name,ok:true});console.log('PASS '+name);};
const write=(name,value)=>fs.writeFileSync(path.join(OUT,name),typeof value==='string'?value:JSON.stringify(value,null,2));
async function read(expression){const r=await b.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;}
async function dump(){const r=await fetch(new globalThis.URL('/api',URL),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd:'dump'})}).then(r=>r.json());assert.equal(r.ok,true);return r.text;}
async function waitDump(expected){for(let i=0;i<150;i++){if(await dump()===expected)return;await b.sleep(100);}assert.equal(await dump(),expected,'native dump must settle to independently declared expected bytes');}
async function idle(){await b.waitFor("!ReferenceWorkspace.busy&&!oc.busy",30000);}
async function click(selector){await b.click(selector);await idle();}
async function fill(selector,value){await b.fill(selector,String(value));await b.press('Tab');await idle();}
async function command(value){await click('#cmdToggle');await b.fill('#cmd',value,{enter:true});await b.press('Escape');await idle();}
async function menu(selector){await click('#fileMenuBtn');await click(selector);}
async function choose(selector,value){const opts=await read(`Array.from(document.querySelector(${JSON.stringify(selector)}).options).filter(o=>!o.disabled).map(o=>o.value)`);assert.ok(opts.includes(value));await click(selector);await b.press('Escape');await b.send('Input.dispatchKeyEvent',{type:'keyDown',key:'Home',code:'Home',windowsVirtualKeyCode:36});await b.send('Input.dispatchKeyEvent',{type:'keyUp',key:'Home',code:'Home',windowsVirtualKeyCode:36});for(let i=0;i<opts.indexOf(value);i++)await b.press('ArrowDown');await b.press('Tab');check('select '+selector,await b.readValue(selector),value);}
async function snap(){return {world:await dump(),project:await read(`(async()=>{const c=ReferenceWorkspace.context(),m=await ReferenceWorkspace.manifest();return {id:c.id,name:c.name,manifest:m,models:ReferenceWorkspace.getSpaceModels(),sources:Array.from(c.sources,([key,v])=>[key,Array.from(v.bytes)]),undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,dirty:c.dirty};})()`)};}
function semantic(s){return {world:s.world,id:s.project.id,name:s.project.name,manifest:s.project.manifest,models:s.project.models,sources:s.project.sources};}
async function launch(n){
 const port=Number(ENV.GEOMETRY_CDP_PORT||9422);assert.ok(Number.isInteger(port)&&port>=1024&&port<=65535,'CDP port must be explicit valid unprivileged port');
 await new Promise((resolve,reject)=>{const probe=net.createServer();probe.once('error',e=>reject(Error('Own CDP port unavailable; no browser launched: '+e.message)));probe.listen({host:'127.0.0.1',port,exclusive:true},()=>probe.close(resolve));});
 b=await qa.launch({chrome:ENV.GEOMETRY_CHROME||'/usr/bin/chromium',port,profileDir:path.join(os.tmpdir(),`geometry-save-profile-${process.pid}-${n}`),chromeFlags:(ENV.GEOMETRY_CHROME_FLAGS||'').split(/\s+/).filter(Boolean),downloadDir:path.join(OUT,'downloads-'+n),width:1440,height:1000});b.setDialogPolicy('accept');await b.goto(URL);await b.waitFor("typeof connection==='object'&&connection.phase==='ready'",30000);
}
async function close(){if(!b)return;logs.push(...b.consoleLog());try{process.kill(b.pid,'SIGTERM')}catch{}await b.close();b=null;}
async function history(kind){await click(kind==='undo'?'#btnUndo':'#btnRedo');await b.sleep(120);await idle();}
async function preview(){await click('#smPreview');await b.waitFor("SpaceModelWorkspace.snapshot().phase==='preview'&&!document.querySelector('#smPreview').disabled",30000);}
async function openSaved(id){await menu('#btnModelLibraryMenu');await click(`[data-sm-open-model="${id}"]`);await b.waitFor("SpaceModelWorkspace.snapshot().phase==='created'",30000);}
(async()=>{try{
record.before=await identity();record.startedAt=new Date().toISOString();write('run.json',record);check('runtime worktree is clean before fixture mutation',record.before.status,'');
phase='author';await launch(1);check('browser URL and title identify the actual nonblank product',await read(`location.href===${JSON.stringify(URL)}&&document.title==='構形 Canvas · 工程規格與空間建模'&&!!document.querySelector('#btnNewProject')`));await menu('#btnNewProject');await waitDump('');
await command('surface 311 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000');await waitDump(BASE);
check('native 4m x 3m source and persisted canvas position exactly match independent oracle',await dump(),BASE);
await command('surface 311 origin 0 0 2500 u +x v +y outline 0,0 4500,0 4500,3000 0,3000');await waitDump(BASE.replaceAll('4000','4500'));
await history('undo');await waitDump(BASE);check('native geometry edit undo restores complete exact World',await dump(),BASE);
await history('redo');await waitDump(BASE.replaceAll('4000','4500'));check('native geometry edit redo applies complete exact World',await dump(),BASE.replaceAll('4000','4500'));
await history('undo');await waitDump(BASE);
await click('.ocard[data-kind="boundary"][data-id="311"] .card-enter');await click('#faceInspectorTabs [data-fi-tab="prop"]');await click('#faceInspectorContent [data-fp-build]');
await b.waitFor("SpaceModelWorkspace.snapshot().phase==='ready'",30000);await choose('#smProjectionView','bottom');await click('#smConfirmProjection');
await fill('#smModelName','Save Roundtrip 4x3');await click('#smBottomZero');await preview();
check('independent preview volume equals 4m x 3m x 3m',await read('SpaceModelWorkspace.snapshot().resultSummary.volume_mm3'),'36000000000');
await click('#smConfirmFaces');await click('#smCreate');await b.waitFor('!!SpaceModelWorkspace.snapshot().createdId',30000);
let current=await snap();const id=current.project.models[0].id;check('created model has exact source projection',current.project.models[0].source.projection,projection);
await click('#smLibrary');await click(`[data-sm-edit-height="${id}"]`);await fill('#smEditHeight',3200);await preview();
check('independent edited preview volume equals 38.4m3',await read('SpaceModelWorkspace.snapshot().resultSummary.volume_mm3'),'38400000000');
await click('#smConfirmFaces');await click('#smCreate');await b.waitFor('ReferenceWorkspace.getSpaceModels()[0].input.settings.height===3200',30000);
check('model update leaves all native source bytes intact',await dump(),BASE);
await click('#smLibrary');const updated=await snap();write('before-save.json',updated);
await history('undo');check('model height undo returns exact 3000mm',await read('ReferenceWorkspace.getSpaceModels()[0].input.settings.height'),3000);check('model height undo preserves exact native World',await dump(),BASE);
await history('redo');check('model height redo restores full raw record and source',semantic(await snap()),semantic(updated));
await b.screenshot(path.join(OUT,'01-model-library.png'));
phase='save';await click('#projectBar [data-project-action="save"]');const download=await b.waitForDownload(null,'.gcanvas',30000);check('real Save downloads a nonempty complete project ZIP',download.size>1000);fs.copyFileSync(download.file,path.join(OUT,'saved.gcanvas'));
check('download branch honestly reports completion still needs user confirmation',await read("ReferenceWorkspace.context().downloaded===true&&ReferenceWorkspace.context().dirty===true"));
const saved=await snap();write('saved-state.json',saved);await b.screenshot(path.join(OUT,'02-saved.png'));
phase='save-errors';const beforeFailed=semantic(await snap());
await read(`window.__cancelCalled=false;Object.defineProperty(window,'showSaveFilePicker',{configurable:true,writable:true,value:async()=>{window.__cancelCalled=true;throw new DOMException('test cancel','AbortError')}});void 0`);await click('#projectBar [data-project-action="save"]');check('cancelled picker was actually invoked',await read('window.__cancelCalled'));check('cancelled picker preserves exact native/model/projection fixture and full manifest',semantic(await snap()),beforeFailed);
await read(`window.__saveAborted=false;window.showSaveFilePicker=async()=>({createWritable:async()=>({write:async()=>{throw Error('injected disk full')},abort:async()=>{window.__saveAborted=true}})});void 0`);await click('#projectBar [data-project-action="save"]');
check('injected write failure aborts and keeps unsaved state',await read('window.__saveAborted&&ReferenceWorkspace.context().dirty&&!ReferenceWorkspace.busy'));
check('injected write failure preserves exact native/model/projection fixture and full manifest',semantic(await snap()),beforeFailed);await read('window.showSaveFilePicker=undefined;void 0');
await click('#smClose');phase='new-history';await menu('#btnNewProject');await waitDump('');check('New project clears models in a distinct context',await read(`ReferenceWorkspace.getSpaceModels().length===0&&ReferenceWorkspace.context().id!==${JSON.stringify(saved.project.id)}`));
await history('undo');await waitDump(BASE);check('New project Undo restores nonempty full World and full model/projection fixture manifest',semantic(await snap()),semantic(saved));
await history('redo');await waitDump('');check('New project Redo restores empty project',await read('ReferenceWorkspace.getSpaceModels().length'),0);
await close();
phase='fresh-profile';await launch(2);check('fresh browser profile starts with empty World',await dump(),'');check('fresh browser profile has no model records',await read('ReferenceWorkspace.getSpaceModels().length'),0);
await b.chooseFileOnNext(path.join(OUT,'saved.gcanvas'));await menu('#btnOpenProject');await b.waitForChooser();await b.waitFor(`ReferenceWorkspace.context().id===${JSON.stringify(saved.project.id)}&&!ReferenceWorkspace.busy`,30000);await waitDump(BASE);
check('fresh session real chooser reopen restores exact native World, full fixture manifest and raw model/source bytes',semantic(await snap()),semantic(saved));
await openSaved(id);check('reopened UI reports exact 3200mm model extent and 38.4m3',await read(`(()=>{const x=SpaceModelWorkspace.snapshot();return x.resultSummary.volume_mm3==='38400000000'&&x.viewer.bounds.min[2]===0&&x.viewer.bounds.max[2]===3200})()`));await b.screenshot(path.join(OUT,'03-fresh-reopened.png'));await click('#smClose');
phase='bad-import';const beforeBad=await snap(),statusBeforeBad=await b.readText('#status');write('before-bad-import.json',beforeBad);fs.writeFileSync(path.join(OUT,'corrupt.gcanvas'),'not a zip file');
await b.chooseFileOnNext(path.join(OUT,'corrupt.gcanvas'));await menu('#btnOpenProject');const corruptChooser=await b.waitForChooser();await idle();
const corruptStatus=await b.readText('#status');write('corrupt-import-status.json',{before:statusBeforeBad,after:corruptStatus,chooser:corruptChooser});
check('corrupt archive produces its own archive-specific visible failure',corruptStatus!==statusBeforeBad&&/未能完成/.test(corruptStatus)&&/invalid zip|zip data|壓縮|ZIP|專案缺少清單或場景/i.test(corruptStatus));
check('corrupt archive chooser consumed the intended file',corruptChooser.files,[path.join(OUT,'corrupt.gcanvas')]);
check('failed archive import preserves full fixture snapshot and history',await snap(),beforeBad);
await history('undo');await waitDump('');check('successful import Undo restores previous empty project with no models',await read('ReferenceWorkspace.getSpaceModels().length'),0);
await history('redo');await waitDump(BASE);check('successful import Redo restores nonempty World and full project payload',semantic(await snap()),semantic(saved));
write('final-state.json',await snap());await b.screenshot(path.join(OUT,'04-final.png'));check('no uncaught page errors during complete flow',[...logs,...b.consoleLog()].filter(x=>x.kind==='pageerror'),[]);
record.after=await identity();check('clean head tree and runtime source process/session stayed identical during acceptance',{head:record.after.head,tree:record.after.tree,status:record.after.status,version:record.after.runtime.version,pid:record.after.runtime.pid,session:record.after.runtime.session},{head:record.before.head,tree:record.before.tree,status:record.before.status,version:record.before.runtime.version,pid:record.before.runtime.pid,session:record.before.runtime.session});
assert.equal(results.length,33,'focused acceptance assertion floor');const summary={schema:'geometry-save-roundtrip-result/1',completed:true,expected:33,passed:results.length,failed:0,ok:true};console.log('SAVE_ROUNDTRIP_RESULT '+JSON.stringify(summary));write('results.json',{...summary,checks:results,limits:['Linux Chromium download fallback, not real native OS save picker','Save cancellation and disk failure are deliberately injected environment responses','Geometric/model/projection data covered; reference images/PDF and draft payloads not included']});
}catch(e){console.error('FAIL PHASE',phase,e);if(b){write('failed-state.json',await snap().catch(e=>String(e)));write('failed-ui.txt',await b.pageText().catch(e=>String(e)));await b.screenshot(path.join(OUT,'failed.png')).catch(()=>{});}const summary={schema:'geometry-save-roundtrip-result/1',completed:false,expected:33,passed:results.length,failed:1,ok:false};console.log('SAVE_ROUNDTRIP_RESULT '+JSON.stringify(summary));write('results.json',{...summary,phase,error:String(e.stack),checks:results});process.exitCode=1;}finally{await close();record.finishedAt=new Date().toISOString();record.exitCode=process.exitCode||0;write('run.json',record);write('browser-log.json',logs);}})();
