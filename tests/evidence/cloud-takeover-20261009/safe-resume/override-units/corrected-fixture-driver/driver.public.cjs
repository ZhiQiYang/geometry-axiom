'use strict';
// Production owner/ZIP/hash execution with controlled DOM/native/IDB schedules.
// This is a unit supplement, never a browser or actual-native acceptance claim.
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const ROOT_DIR=process.env.GEOMETRY_RESUME_ROOT||'<resume-repository-root>';
const fixtureFile=path.join(ROOT_DIR,'tests/test_scenario_recovery_owner.js');
let fixtureSource=fs.readFileSync(fixtureFile,'utf8')
  .replace("const {test}=require('node:test'),assert=require('node:assert/strict');","const test=()=>{},assert=require('node:assert/strict');")
  .replace("restore=true,rootKey='root-tab'", "restore=true,rootKey='root-tab',withPDF=true")
  .replace('openFixture({pdfLibrary})','openFixture({pdfLibrary,withPDF})');
assert.ok(fixtureSource.includes('const test=()=>{}'),'fixture test registration suppressed');
const fixtureModule=new Module(fixtureFile,module);fixtureModule.filename=fixtureFile;fixtureModule.paths=Module._nodeModulePaths(path.dirname(fixtureFile));
fixtureModule._compile(fixtureSource+'\nmodule.exports={environment,transactionalDB,ticket,catalog,defer,ROOT,B,C};',fixtureFile);
const {environment,ticket,catalog,defer,ROOT,B,C}=fixtureModule.exports;
const P=require(path.join(ROOT_DIR,'geometry-web/project-store.js')),zip=require(path.join(ROOT_DIR,'geometry-web/vendor/fflate/umd/index.js'));
const clone=x=>JSON.parse(JSON.stringify(x)),journalKey='geometry-scenario-resume-'+B,packageKey='geometry-scenario-resume-package-'+B;
const unit=(name,fn)=>test(name,{timeout:8000},fn);
async function setup(){
  const root=await environment(),creating=await ticket(root),initializing=await root.w.updateScenarioEditorTicket(creating,{phase:'initializing',context:B});
  const child=await environment({native:B,storage:root.storage});await child.w.initializeScenarioProject(child.bytes,'B',initializing);
  const active=await root.w.updateScenarioEditorTicket(initializing,{phase:'active',context:B});
  return {root,child,active,storage:root.storage};
}
function metadata(child,name='最新 B1'){
  child.w.context().name=name;
  child.w.calibrated(1,[[0,0],[10,0]],100,10,'cm');
  const page=child.w.active(1);page.opacity=.73;page.x=42;child.w.changed(1,true);
  child.w.setEngineeringDraft({id:'engineering-B1',kind:'material',base_ref:null,data:{name:'B1 material',width:'123',length:'456'},updated_at:'2026-10-09T00:00:00.000Z'},child.w.getProjectState().contextToken);
  child.w.setAssemblyDraft({id:'assembly-B1',kind:'rule',base_ref:null,data:{id:1,version:1,name:'B1 rule',slots:[],members:[],joints:[]},updated_at:'2026-10-09T00:00:00.000Z'},child.w.getProjectState().contextToken);
}
async function paused(){const f=await setup();metadata(f.child);await f.child.w.pauseScenarioProject(f.active);return f;}
async function reloaded(f){return environment({native:B,storage:f.storage});}
const destructive=f=>f.requests.filter(r=>/\/(upload|scenarios\/editor)(\/|$)/.test(r.url));
unit('explicit pause stores the complete latest metadata/source package and resume attaches it once without native upload/create/close',async()=>{
  const f=await paused(),record=structuredClone(f.storage.records.get(packageKey)),journal=structuredClone(f.storage.records.get(journalKey));
  const saved=await P.unpack(record.bytes,zip);assert.equal(journal.eligible,true);assert.equal(await P.sha(record.bytes),journal.packageHash);
  assert.equal(saved.manifest.name,'最新 B1');assert.equal(saved.manifest.faces[0].pages[0].opacity,.73);assert.equal(saved.manifest.engineeringDrafts.records[0].data.width,'123');assert.equal(saved.manifest.assemblyDrafts.records[0].data.name,'B1 rule');
  assert.throws(()=>f.child.w.assertEditable());const beforeA=clone(f.root.w.context().scenarioCatalog),rootRevision=f.root.w.getProjectState().revision;
  const b=await reloaded(f);assert.equal(b.restored.state,'scenario-blocked');const initial=b.w.getProjectState();assert.equal(destructive(b).length,0);
  const result=await b.w.resumeScenarioProject(f.active);assert.equal(result.ok,true);assert.equal(result.context,B);assert.doesNotThrow(()=>b.w.assertEditable());
  assert.deepEqual(await b.w.manifest(),saved.manifest);assert.equal(b.w.getProjectState().dirty,record.project.dirty);assert.equal(b.w.getProjectState().saved,record.project.saved);
  assert.equal(b.w.context().sources.size,saved.sources.size);for(const [id,bytes] of saved.sources)assert.deepEqual(b.w.context().sources.get(id).bytes,bytes);
  assert.notEqual(b.w.getProjectState().contextToken,initial.contextToken);assert.equal(f.storage.records.get(journalKey).eligible,false);assert.equal(destructive(b).length,0);
  assert.deepEqual(clone(f.root.w.context().scenarioCatalog),beforeA);assert.equal(f.root.w.getProjectState().revision,rootRevision);
  await assert.rejects(b.w.resumeScenarioProject(f.active),/身份不符/);
});
unit('held strict Resume disarm cannot attach metadata or enable editing before transaction completion',async()=>{
  const f=await paused(),b=await reloaded(f),initial=b.w.context(),reached=defer(),gate=defer();
  f.storage.options.beforeCommit=async writes=>{if(writes.includes(journalKey)&&!writes.includes(packageKey)){reached.resolve();await gate.promise;}};
  const work=b.w.resumeScenarioProject(f.active);await reached.promise;
  assert.equal(b.w.context(),initial);assert.equal(f.storage.records.get(journalKey).eligible,true);assert.throws(()=>b.w.assertEditable());assert.equal(destructive(b).length,0);
  gate.resolve();await work;assert.equal(b.w.context().name,'最新 B1');assert.equal(f.storage.records.get(journalKey).eligible,false);
});
unit('Resume disarm quota abort retains eligible checkpoint but never attaches old metadata',async()=>{
  const f=await paused(),b=await reloaded(f),initial=b.w.context(),before=structuredClone([...f.storage.records]);f.storage.options.failPutAt=1;
  await assert.rejects(b.w.resumeScenarioProject(f.active),/quota/);assert.equal(b.w.context(),initial);assert.throws(()=>b.w.assertEditable());assert.deepEqual([...f.storage.records],before);assert.equal(destructive(b).length,0);
});
unit('unsupported strict durability never disarms or attaches the saved B package',async()=>{
  const f=await paused(),b=await reloaded(f),initial=b.w.context(),before=structuredClone([...f.storage.records]);f.storage.options.relaxed=true;
  await assert.rejects(b.w.resumeScenarioProject(f.active),/嚴格儲存/);assert.equal(b.w.context(),initial);assert.throws(()=>b.w.assertEditable());assert.deepEqual([...f.storage.records],before);
});
unit('durably committed disarm with lost local owner acknowledgement leaves no attach and a fresh owner cannot reuse eligibility',async()=>{
  const f=await paused(),b=await reloaded(f),initial=b.w.context();
  f.storage.options.beforeCommit=async writes=>{if(writes.includes(journalKey)&&!writes.includes(packageKey))b.env.connection.session=C;};
  await assert.rejects(b.w.resumeScenarioProject(f.active),/身份已變更|工作階段/);assert.equal(b.w.context(),initial);assert.equal(f.storage.records.get(journalKey).eligible,false);assert.equal(destructive(b).length,0);
  delete f.storage.options.beforeCommit;const next=await reloaded(f);await assert.rejects(next.w.resumeScenarioProject(f.active),/未在離開前/);assert.throws(()=>next.w.assertEditable());
});
unit('ordinary active B debounce never creates Resume qualification and an abrupt reload rejects it',async()=>{
  const f=await setup();metadata(f.child);await f.child.w.persistSession();assert.equal(f.storage.records.has(journalKey),false);assert.equal(f.storage.records.has(packageKey),false);
  const next=await reloaded(f),initial=next.w.context();await assert.rejects(next.w.resumeScenarioProject(f.active),/續接點不完整/);assert.equal(next.w.context(),initial);assert.throws(()=>next.w.assertEditable());assert.equal(destructive(next).length,0);
});
unit('metadata-only edit after Resume keeps identical native fingerprint but old suspend metadata is ineligible on reload',async()=>{
  const f=await paused(),b=await reloaded(f);await b.w.resumeScenarioProject(f.active);const scene=(await b.env.api('dump')).text;
  metadata(b,'新的 B2');assert.equal((await b.env.api('dump')).text,scene);await b.w.persistSession();assert.equal(f.storage.records.get(journalKey).eligible,false);
  const next=await reloaded(f),initial=next.w.context();await assert.rejects(next.w.resumeScenarioProject(f.active),/未在離開前/);assert.equal(next.w.context(),initial);assert.notEqual(next.w.context().name,'最新 B1');assert.throws(()=>next.w.assertEditable());
});
unit('Suspend transaction abort preserves current B metadata and leaves its freeze authoritative',async()=>{
  const f=await setup();metadata(f.child);const before=structuredClone([...f.storage.records]);f.storage.options.failPutAt=1;
  await assert.rejects(f.child.w.pauseScenarioProject(f.active),/quota/);assert.equal(f.child.w.context().name,'最新 B1');assert.throws(()=>f.child.w.assertEditable());assert.deepEqual([...f.storage.records],before);assert.equal(f.storage.records.has(journalKey),false);
});
unit('Cancel during package validation wins over an older Resume and preserves checkpoint without attaching it',async()=>{
  const f=await paused(),b=await reloaded(f),initial=b.w.context(),reached=defer(),gate=defer(),original=b.env.GeometryProject.sha;let once=false;
  b.env.GeometryProject.sha=async bytes=>{if(!once&&bytes.length===f.storage.records.get(packageKey).bytes.length){once=true;reached.resolve();await gate.promise;}return original(bytes);};
  const work=b.w.resumeScenarioProject(f.active),rejection=assert.rejects(work,/取消|完成/);await reached.promise;
  const retiring=await f.root.w.markScenarioEditorRetiring(f.active,{reason:'cancel'});assert.equal(retiring.phase,'retiring');gate.resolve();await rejection;
  assert.equal(b.w.context(),initial);assert.equal(f.storage.records.get(journalKey).eligible,true);assert.throws(()=>b.w.assertEditable());assert.equal(destructive(b).length,0);
});
unit('Finish during package validation wins and an old Resume cannot reopen the retired decision',async()=>{
  const f=await paused(),b=await reloaded(f),initial=b.w.context(),reached=defer(),gate=defer(),original=b.env.GeometryProject.sha;let once=false;
  b.env.GeometryProject.sha=async bytes=>{if(!once&&bytes.length===f.storage.records.get(packageKey).bytes.length){once=true;reached.resolve();await gate.promise;}return original(bytes);};
  const work=b.w.resumeScenarioProject(f.active),rejection=assert.rejects(work,/取消|完成/);await reached.promise;
  const next=await catalog(f.root),finished=await f.root.w.finishScenarioEditor(next.value,next.sources,f.active);assert.equal(finished.ticket.retirement.reason,'finish');gate.resolve();await rejection;
  assert.equal(b.w.context(),initial);assert.throws(()=>b.w.assertEditable());assert.equal(destructive(b).length,0);
});
unit('native fingerprint mismatch rejects before disarm and leaves all stored records unchanged',async()=>{
  const f=await paused(),b=await reloaded(f),before=structuredClone([...f.storage.records]),initial=b.w.context();b.env.api=async()=>({ok:true,text:'boundary 99 outline 0,0 1,0 1,1 0,1\n'});
  await assert.rejects(b.w.resumeScenarioProject(f.active),/原生內容/);assert.equal(b.w.context(),initial);assert.deepEqual([...f.storage.records],before);assert.throws(()=>b.w.assertEditable());
});
unit('corrupted complete package rejects without disarm, import or metadata attachment',async()=>{
  const f=await paused();f.storage.records.get(packageKey).bytes[9]^=1;const before=structuredClone([...f.storage.records]),b=await reloaded(f),initial=b.w.context();
  await assert.rejects(b.w.resumeScenarioProject(f.active),/完整包|指紋/);assert.equal(b.w.context(),initial);assert.deepEqual([...f.storage.records],before);assert.equal(destructive(b).length,0);
});
unit('a second editing epoch can explicitly suspend its new complete metadata before the next Resume',async()=>{
  const f=await paused(),b=await reloaded(f);await b.w.resumeScenarioProject(f.active);const epoch=f.storage.records.get(journalKey).epoch;metadata(b,'第二個明確暫存點');
  await b.w.pauseScenarioProject(f.active);assert.notEqual(f.storage.records.get(journalKey).epoch,epoch);assert.equal(f.storage.records.get(journalKey).eligible,true);
  const next=await reloaded(f);await next.w.resumeScenarioProject(f.active);assert.equal(next.w.context().name,'第二個明確暫存點');assert.equal(f.storage.records.get(journalKey).eligible,false);assert.equal(destructive(next).length,0);
});
unit('present malformed reserved Resume journals are not treated as absent and overwritten by Suspend',async()=>{
  for(const corrupt of [null,undefined]){const f=await setup();metadata(f.child);f.storage.records.set(journalKey,corrupt);const before=structuredClone([...f.storage.records]);
    await assert.rejects(f.child.w.pauseScenarioProject(f.active),/續接點|損壞|記錄/);assert.deepEqual([...f.storage.records],before);assert.throws(()=>f.child.w.assertEditable());}
});
