'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js'),F=P.Features,zip=require('../geometry-web/vendor/fflate/umd/index.js');
const schema='grid-editor-drafts/1',copy=structuredClone;
function draft(id='a',edit=false){return {schema:F.GRID_SCHEMA,draftId:id,kind:'source',intent:edit?'edit':'create',baseRef:edit?{kind:'grid-system',id:1,fingerprint:'a'.repeat(64)}:null,inputRefs:[],rawForm:Object.fromEntries(F.sourceFields.map(f=>[f,f==='igName'?'  原樣 '+id+' ':f==='igUStep'?'1e':'']))};}
const collection=(drafts,orphans=[])=>({schema,drafts,orphans});
const envelope=value=>({schema:F.SCHEMA,records:[{kind:F.GRID_KIND,schema:value.schema,value}]});
const manifest=()=>({format:P.FORMAT,projectId:'k2a',name:'K2a',sceneHash:'0'.repeat(64),sources:[],faces:[]});
test('M10 writer selects legacy only for one healthy draft, collection for orphans or lost',()=>{
  const a=draft('a',true);assert.equal(F.gridDraftValue([a]).schema,F.GRID_SCHEMA);
  assert.equal(F.gridDraftValue([a],['a']).schema,schema);
  a.inputRefs=[{kind:'grid-system',id:2,fingerprint:'b'.repeat(64),lost:true}];assert.equal(F.gridDraftValue([a]).schema,schema);
});
test('M02 two raw drafts survive real ZIP with collection capability and canonical identity order',async()=>{
  const a=draft(),b=draft('b');b.schema=F.GRID_RULE_SCHEMA;b.ruleDraft=null;
  const bytes=await P.pack('',{...manifest(),featureAttachments:envelope(F.gridDraftValue([b,a]))},new Map(),zip);
  const reopened=await P.unpack(bytes,zip),v=reopened.manifest.featureAttachments.records[0].value;
  assert.equal(reopened.manifest.format,'geometry-canvas/17');assert.deepEqual(v.drafts,[a,b]);
  assert.deepEqual(reopened.manifest.requiredCapabilities,[F.GRID_SCHEMA,F.GRID_RULE_SCHEMA,schema]);
});
test('M07 non-orphan target uniqueness rejects the entire collection; orphans do not reserve targets',()=>{
  const a=draft('a',true),b=draft('b',true);
  assert.throws(()=>F.record(F.GRID_KIND,collection([a,b])));
  assert.doesNotThrow(()=>F.record(F.GRID_KIND,collection([a,b],['a'])));
});
test('M08 sixteen drafts accepted; seventeenth rejected without truncation',()=>{
  const drafts=Array.from({length:16},(_,i)=>draft('d'+i));assert.doesNotThrow(()=>F.record(F.GRID_KIND,collection(drafts)));
  drafts.push(draft('d16'));assert.throws(()=>F.record(F.GRID_KIND,collection(drafts)));assert.equal(drafts.length,17);
});
test('M09 drafts are never valid input references',()=>{
  const a=draft();a.inputRefs=[{kind:'grid-draft',id:1,fingerprint:'a'.repeat(64)}];assert.throws(()=>F.record(F.GRID_KIND,collection([a])));
});
test('M10/M14b single orphan or lost collection preserves flags through ZIP reopen',async()=>{
  for(const lost of [false,true]){
    const a=draft('a',true);if(lost)a.inputRefs=[{kind:'grid-system',id:2,fingerprint:'b'.repeat(64),lost:true}];
    const value=collection([a],lost?[]:['a']);
    const saved=await P.unpack(await P.pack('',{...manifest(),featureAttachments:envelope(value)},new Map(),zip),zip);
    assert.deepEqual(saved.manifest.featureAttachments,envelope(value));assert.equal(saved.manifest.format,'geometry-canvas/17');
  }
});
test('M11 strict schema, orphan membership, lost placement and flag values reject',()=>{
  for(const change of [v=>v.schema='grid-editor-drafts/2',v=>v.orphans=['missing'],v=>v.orphans=['a','a'],v=>v.drafts.push(copy(v.drafts[0])),
    v=>v.orphans=['b'],v=>v.drafts[0].baseRef.lost=true,v=>v.drafts[0].inputRefs[0].lost=false,v=>v.drafts[0].inputRefs[0].lost='true']){
    const a=draft('a',true);a.inputRefs=[{kind:'grid-system',id:2,fingerprint:'b'.repeat(64),lost:true}];const value=collection([a,draft('b')]);change(value);
    assert.throws(()=>F.record(F.GRID_KIND,value));
  }
  const a=draft();a.inputRefs=[{kind:'grid-system',id:2,fingerprint:'b'.repeat(64),lost:true}];assert.throws(()=>F.validateGridDraft(a));
});
test('M11 downgrade and capability stripping fail on real archive bytes',async()=>{
  const bytes=await P.pack('',{...manifest(),featureAttachments:envelope(collection([draft(),draft('b')]))},new Map(),zip);
  for(const change of [m=>m.format='geometry-canvas/16',m=>m.format=P.FEATURE_FORMAT,m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==schema),m=>m.featureAttachments.records[0].schema='unknown']){
    const files=zip.unzipSync(bytes),m=JSON.parse(new TextDecoder().decode(files['manifest.json']));change(m);files['manifest.json']=new TextEncoder().encode(JSON.stringify(m));
    await assert.rejects(()=>P.unpack(zip.zipSync(files),zip));
  }
});
