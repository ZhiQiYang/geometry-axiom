'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const F=()=>{assert.ok(P.Features.Framing,'FT_H01 framing recipe owner must be registered');return P.Features.Framing;};
const defaults=()=>({panelWidth:915,panelLength:1830,gap:2,timberWidth:27,timberDepth:33,maxSecondarySpacing:367});
const recipe=()=>({id:'ceiling-one',name:'客廳平釘天花',template:{id:'flat-ceiling',version:1,policyFingerprint:F().POLICY_FINGERPRINT},
  defaults:defaults(),preference:{corner:'min-min',lengthAlong:'v'},sourceSlots:['boundary','frame','material-semantics','panel-version','support-threshold'],sourceHints:[]});
const value=()=>({schema:'framing-template-recipes/1',recipes:[recipe()]});
const envelope=v=>({schema:P.Features.SCHEMA,records:[P.Features.record(F().KIND,v)]});
const manifest=v=>({format:P.FORMAT,projectId:'r03-recipe-project',name:'R03',sceneHash:'0'.repeat(64),sources:[],faces:[],featureAttachments:envelope(v)});
const scene='boundary 1 outline 0,0 2000,0 2000,3700 0,3700\nplacement 1 on boundary 1 origin 0 0 2500 u +x v +y\n';
test('FT_H01 recipe owner is registered as project-only capability',()=>{
 const f=F(),v=value();assert.equal(f.CAPABILITY,'framing-template-recipes/1');assert.deepEqual(P.Features.capabilities(envelope(v)),[f.CAPABILITY]);
 assert.ok(P.readerCapabilities([]).includes(f.CAPABILITY));assert.throws(()=>P.sceneCapabilities('requires '+f.CAPABILITY+'\n'),/尚未支援/);
});
test('FT_H02 recipe rejects output caches and runtime or identity claims',()=>{
 for(const key of ['outputs','objects','timbers','lengthCache','searchTrace','token','valid','owner','incarnation']){
  const v=value();v.recipes[0][key]=[];assert.throws(()=>envelope(v),/FT_RECIPE_FIELDS/);
 }
 const v=value();v.recipes[0].defaults.panelWidth=915.5;assert.throws(()=>envelope(v),/FT_RECIPE_DEFAULTS/);
});
test('FT_H03 known policy mismatch rejects; unknown generator is preserved readonly',()=>{
 const bad=value();bad.recipes[0].template.policyFingerprint='a'.repeat(64);assert.throws(()=>envelope(bad),/FT_RECIPE_POLICY/);
 const unknown=value();unknown.recipes[0].template.version=999;unknown.recipes[0].template.policyFingerprint='b'.repeat(64);
 assert.deepEqual(envelope(unknown).records[0].value,unknown);assert.equal(F().availability(unknown.recipes[0]).canGenerate,false);
 assert.throws(()=>F().assertGeneratable(unknown.recipes[0]),/FT_GENERATOR_UNAVAILABLE/);
});
test('FT_H04 bounded collection, unique ids, literal defaults and slots reject invalid values',()=>{
 for(const change of [v=>v.recipes.push(structuredClone(v.recipes[0])),v=>v.recipes[0].sourceSlots.push('outputs'),v=>v.recipes[0].defaults.gap=-1,v=>v.recipes[0].defaults.maxSecondarySpacing=0,v=>v.recipes[0].preference.corner='CENTER',v=>v.recipes[0].sourceHints.push({slot:'boundary',id:1,incarnation:'pretend-live'}),v=>v.recipes=Array.from({length:33},(_,i)=>({...structuredClone(v.recipes[0]),id:'r'+i}))]){
  const v=value();change(v);assert.throws(()=>envelope(v));
 }
});
test('FT_H05 actual ZIP roundtrip preserves recipe plus World, without output lists',async()=>{
 const v=value(),packed=await P.pack(scene,manifest(v),new Map(),zip),opened=await P.unpack(packed,zip);
 assert.equal(opened.scene,scene);assert.equal(opened.manifest.format,P.ROOM_CANDIDATE_FORMAT);
 assert.deepEqual(opened.manifest.featureAttachments,envelope(v));assert.ok(opened.manifest.requiredCapabilities.includes(F().CAPABILITY));
 assert.deepEqual(Object.keys(zip.unzipSync(packed)).sort(),['manifest.json','world.scene']);
 assert.deepEqual(Object.keys(opened.manifest.featureAttachments.records[0].value.recipes[0]).sort(),['defaults','id','name','preference','sourceHints','sourceSlots','template']);
});
test('FT_H06 malformed or unsupported archive rejects before host replacement',async()=>{
 const bytes=await P.pack(scene,manifest(value()),new Map(),zip),enc=new TextEncoder(),dec=new TextDecoder();
 for(const change of [m=>m.featureAttachments.records[0].schema='framing-template-recipes/2',m=>m.requiredCapabilities=[],m=>m.requiredCapabilities.push('framing-template-recipes/2'),m=>m.featureAttachments.records[0].value.recipes[0].template.policyFingerprint='c'.repeat(64),m=>m.format=P.FEATURE_FORMAT]){
  const entries=zip.unzipSync(bytes),m=JSON.parse(dec.decode(entries['manifest.json']));change(m);entries['manifest.json']=enc.encode(JSON.stringify(m));await assert.rejects(()=>P.unpack(zip.zipSync(entries),zip));
 }
});
test('FT_H07 archive keeps an unknown generator exactly, without upgrading it',async()=>{
 const v=value();v.recipes[0].template.version=999;v.recipes[0].template.policyFingerprint='f'.repeat(64);
 const opened=await P.unpack(await P.pack(scene,manifest(v),new Map(),zip),zip);
 assert.deepEqual(opened.manifest.featureAttachments,envelope(v));assert.equal(opened.scene,scene);
});
test('FT_H08 recipe edits are one local history and leave native World untouched',async()=>{
 const {fixture}=require('./fixtures/reference_workspace_vm.cjs'),{w,calls}=await fixture();
 const before=w.history.undo.length,token=w.getProjectState().contextToken,originalCalls=[...calls];
 w.setFeatureAttachment(F().KIND,value(),token);
 assert.equal(w.history.undo.length,before+1);assert.equal(w.history.undo.at(-1).kind,'local');assert.deepEqual(calls,originalCalls);
 assert.deepEqual(w.readFeatureAttachment(F().KIND),value());assert.equal(w.tryLocalHistory('line undo').ok,true);assert.equal(w.readFeatureAttachment(F().KIND),null);
 assert.equal(w.tryLocalHistory('line redo').ok,true);assert.deepEqual(w.readFeatureAttachment(F().KIND),value());assert.deepEqual(calls,originalCalls);
});
test('FT_H18 length is a declared field, square or swapped dimensions keep chosen axis',()=>{
 for(const [width,length] of [[1830,915],[915,915]]){const v=value();v.recipes[0].defaults.panelWidth=width;v.recipes[0].defaults.panelLength=length;v.recipes[0].preference.lengthAlong='u';assert.deepEqual(envelope(v).records[0].value,v);}
 const v=value();v.recipes[0].sourceHints=[{slot:'boundary',kind:'boundary',id:0,fingerprint:'a'.repeat(64)}];assert.deepEqual(envelope(v).records[0].value,v);
});
module.exports={defaults,recipe,value,envelope,manifest,scene};
