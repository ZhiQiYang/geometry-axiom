'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
const draft=()=>({id:'identity-draft',kind:'rule',base_ref:null,intent:{kind:'create'},localHighWater:{slot:2,member:3,joint:4},
 data:{id:1,version:1,name:'identity',slots:[],members:[],joints:[]},updated_at:'2026-10-02T00:00:00Z'});
const pack=(scene,records=[])=>P.pack(scene,{projectId:'identity-project',name:'identities',sources:[],faces:[],assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records}},new Map(),zip);
function rewrite(bytes,fn){const files=zip.unzipSync(bytes),m=JSON.parse(new TextDecoder().decode(files['manifest.json']));fn(m);files['manifest.json']=new TextEncoder().encode(JSON.stringify(m));return zip.zipSync(files);}
test('allocator draft intent and local counters reopen with explicit format 8 and identity capability',async()=>{
 const record=draft(),bytes=await pack('reset\n',[record]),p=await P.unpack(bytes,zip);
 assert.equal(p.manifest.format,'geometry-canvas/8');assert.deepEqual(p.manifest.assemblyDrafts.records,[record]);
 assert.deepEqual(p.manifest.requiredCapabilities,['assembly-rule-authoring/1','assembly-rule-identities/1']);
 assert.throws(()=>P.assertProjectCapabilities(p.manifest,['engineering-spec/1','parameters/1','assembly-rule-authoring/1']));
 for(const alter of [m=>m.format='geometry-canvas/7',m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==P.ASSEMBLY_ID_CAPABILITY)])
  await assert.rejects(()=>P.unpack(rewrite(bytes,alter),zip));
});
test('identity record capability inference accepts native token whitespace even without requires marker',async()=>{
 const header=Buffer.from(JSON.stringify({kind:'identity',bytes:1,sha256:'0'.repeat(64)})).toString('base64');
 for(const spaces of [' ','  ','\t']){
  const scene=`reset\nassembly begin\nassembly${spaces}record${spaces}${header}\nassembly end\n`;
  assert.deepEqual(P.sceneCapabilities(scene),['assembly-rule-authoring/1','assembly-rule-identities/1']);
  const bytes=await pack(scene),p=await P.unpack(bytes,zip);assert.equal(p.manifest.format,P.ASSEMBLY_ID_FORMAT);
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>{m.format='geometry-canvas/7';m.requiredCapabilities=['assembly-rule-authoring/1'];}),zip));
 }
});
test('draft counters and edit intent reject malformed identity metadata',()=>{
 for(const alter of [d=>d.localHighWater.slot=-1,d=>d.localHighWater.member=4294967296,d=>d.localHighWater.joint=0.5,
   d=>d.localHighWater.extra=1,d=>delete d.localHighWater.member,d=>d.intent={kind:'unknown'},d=>d.intent={kind:'edit',fingerprint:'invalid'}]){
  const d=draft();alter(d);assert.throws(()=>P.validateAssemblyDraft(d));
 }
 const d=draft();delete d.intent;delete d.localHighWater;assert.equal(P.validateAssemblyDraft(d),d);
});
test('separate load sessions with identical saved project and draft IDs do not merge counters',()=>{
 const make=water=>({id:'same-saved-project',assemblyDrafts:[{...draft(),localHighWater:{slot:water,member:water,joint:water}}],models:[],faceProjections:new Map()});
 const h=new P.ContextHistory(()=>make(2)),a=h.frame.context;
 h.replace(make(4294967295));h.observe('line undo',{ok:true});
 assert.equal(h.frame.context,a);assert.equal(h.frame.context.assemblyDrafts[0].localHighWater.slot,2);
 h.observe('line redo',{ok:true});assert.equal(h.frame.context.assemblyDrafts[0].localHighWater.slot,4294967295);
 h.observe('line undo',{ok:true});h.push(h.snapshot(),'local');h.frame.context.assemblyDrafts[0].localHighWater.slot=7;
 assert.equal(h.tryLocal('line undo').ok,true);assert.equal(h.frame.context.assemblyDrafts[0].localHighWater.slot,7);
 assert.equal(h.tryLocal('line redo').ok,true);assert.equal(h.frame.context.assemblyDrafts[0].localHighWater.slot,7);
});
