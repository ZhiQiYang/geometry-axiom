'use strict';
// Q38j-b display/content checks consume the actual native producer fixture.
// Canvas draw calls are recorded, not substituted for real-browser coverage.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const viewerPath = process.env.GEOMETRY_TEST_PROFILE_VIEWER || path.join(root, 'geometry-web/model-viewer.js');
const sourcePath = process.env.GEOMETRY_TEST_PROFILE_SOURCE || path.join(root, 'geometry-web/source-inspector.js');
const V = require(viewerPath), S = require(sourcePath);
const native = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures/q38j-b-native-model.json'), 'utf8'));
const clone = value => JSON.parse(JSON.stringify(value));
const hash = n => String(n).repeat(64);
const members = () => native.model.result.profile_runs.derived.objects.filter(o => o.role === 'geometry');
const L = require('../geometry-web/identity-ledger.js');
function identified() {
  const model=clone(native.model),input={...model.input,boundary_id:model.source.boundary_id};
  const roots=L.expectedRoots(input).roots;
  const nodes=roots.map((root,index)=>({key:S.key(root.kind,root.id),kind:root.kind,id:String(root.id),
    incarnation:'a'.repeat(32)+':'+(index+1),definitionFingerprint:hash(1),valueFingerprint:hash(2)}));
  nodes.push({key:'profile-run:1',kind:'profile-run',id:'1',definitionFingerprint:hash(1),valueFingerprint:hash(2)});
  const data={ok:true,schema:'source-inspector/1',live:true,complete:true,revision:11,sourceFingerprint:hash(3),
    identityLedger:{schema:'identity-ledger/1',active:true},nodes,edges:[]};
  model.sourceIdentity=L.buildSourceIdentity(input,new Map(nodes.map(node=>[node.key,node])));
  return {model,data,graph:S.index(data)};
}

test('Q38JB_K3_ROOTS: content includes runs while identity remains the exact covered whitelist',()=>{
  const {model,graph}=identified();
  assert.ok(S.modelRoots(model).includes('profile-run:1'),'Q38JB_K3_CONTENT_ROOT');
  assert.deepEqual(model.sourceIdentity.roots.map(root=>root.kind+':'+root.id),['placement:1','boundary:1','timber:0'],'Q38JB_K3_COVERED_ROOTS');
  assert.deepEqual(S.untrackedModelRoots(model),[{kind:'profile-run',id:1}],'Q38JB_K3_UNTRACKED');
  assert.equal(S.continuityOf(model,graph).token,'proved','Q38JB_K3_COVERED_PROOF');
});
test('Q38JB_K3_SCOPE: covered proof is retained and explicitly excludes run continuity',()=>{
  const {model,graph}=identified(),result=S.continuityOf(model,graph);
  assert.equal(result.token,'proved','Q38JB_K3_COVERED_PROOF');
  assert.equal(result.text,'已追蹤根延續已證明；拉伸件延續未知','Q38JB_K3_PROOF_SCOPE');
  assert.deepEqual(result.untrackedModelRoots,[{kind:'profile-run',id:1}],'Q38JB_K3_UNTRACKED');
});
test('Q38JB_K3_REPLACED: a replaced covered timber remains a listed problem alongside an untracked run',()=>{
  const {model,data}=identified();data.nodes.find(node=>node.kind==='timber').incarnation='b'.repeat(32)+':9';
  const result=S.continuityOf(model,S.index(data));
  assert.equal(result.token,'partial','Q38JB_K3_REPLACED_PRIORITY');
  assert.deepEqual(result.listed,['timber #0'],'Q38JB_K3_REPLACED_LISTED');
  assert.match(result.text,/已不存在或已刪除重建.*拉伸件延續未知/,'Q38JB_K3_REPLACED_SCOPE');
});
test('Q38JB_K3_RUN_CONTENT: changed or absent runs change content without rewriting covered continuity or saved data',()=>{
  const {model,data,graph}=identified(),before=JSON.stringify(model),changed=clone(data);
  changed.nodes.find(node=>node.kind==='profile-run').definitionFingerprint=hash(4);
  assert.equal(S.freshness(graph,S.index(changed),S.modelRoots(model)).contentStatus,'changed','Q38JB_K3_RUN_CONTENT_CHANGED');
  assert.equal(S.continuityOf(model,S.index(changed)).token,'proved','Q38JB_K3_NO_RUN_PIN');
  changed.nodes=changed.nodes.filter(node=>node.kind!=='profile-run');
  assert.equal(S.freshness(graph,S.index(changed),S.modelRoots(model)).contentStatus,'missing','Q38JB_K3_RUN_CONTENT_MISSING');
  assert.equal(S.continuityOf(model,S.index(changed)).token,'proved','Q38JB_K3_NO_RUN_PIN');
  assert.equal(JSON.stringify(model),before,'Q38JB_K3_READ_ONLY');
});
test('Q38JB_K3_HISTORY: inactive live ledger preserves historical source identity with unknown continuity',()=>{
  const {model,data}=identified(),before=JSON.stringify(model);
  data.identityLedger.active=false;for(const node of data.nodes)delete node.incarnation;
  assert.equal(S.continuityOf(model,S.index(data)).token,'unknown','Q38JB_K3_INACTIVE_UNKNOWN');
  assert.match(S.continuityOf(model,S.index(data)).text,/拉伸件延續未知/);
  assert.equal(JSON.stringify(model),before,'Q38JB_K3_HISTORY_PRESERVED');
});

function graph() {
  const nodes = [['placement',1],['profile-run',1],['section-profile',1],['profile-timber',1],['profile-run',2]].map(([kind,id]) =>
    ({key:S.key(kind,id),kind,id:String(id),definitionFingerprint:hash(1),valueFingerprint:hash(2)}));
  return {ok:true,schema:'source-inspector/1',revision:1,sourceFingerprint:hash(3),complete:true,live:false,nodes,
    edges:[{from:'profile-run:1',to:'section-profile:1',relation:'profile',field:'profile',active:true},
      {from:'section-profile:1',to:'profile-timber:1',relation:'member',field:'members',active:true}]};
}
function record() {
  const result = clone(native.model);
  delete result.input.timbers;
  return result;
}
function canvasHarness() {
  const frames = [], labels = [], faces = [], listeners = new Map(), attrs = new Map();
  let current = [];
  const noop = () => {};
  const ctx = new Proxy({
    measureText:text=>({width:text.length*7}),
    clearRect(){labels.length=0;faces.length=0;},
    beginPath(){current=[];},moveTo(x,y){current.push([x,y]);},lineTo(x,y){current.push([x,y]);},
    fill(){if(current.length===3)faces.push(current.slice());},fillText(text){labels.push(text);}
  },{get:(target,key)=>target[key]||noop});
  const win = {devicePixelRatio:1,requestAnimationFrame:fn=>{frames.push(fn);return frames.length;},cancelAnimationFrame:noop,
    addEventListener:noop,removeEventListener:noop};
  const canvas = {style:{},ownerDocument:{defaultView:win},getContext:()=>ctx,
    getBoundingClientRect:()=>({width:600,height:400,left:0,top:0}),
    getAttribute:key=>attrs.has(key)?attrs.get(key):null,setAttribute:(key,value)=>attrs.set(key,value),removeAttribute:key=>attrs.delete(key),
    addEventListener:(name,fn)=>listeners.set(name,fn),removeEventListener:name=>listeners.delete(name)};
  const view = V.create(canvas);
  const flush = () => {while(frames.length)frames.shift()();};
  return {view,flush,faces,labels};
}

test('Q38JB_VIEW_MODULES_LOAD: full display modules load in Node VM without browser globals',()=>{
  for(const [file,method] of [[viewerPath,'spacePreviewObjects'],[sourcePath,'modelRoots']]){
    const context = vm.createContext({module:{exports:{}},require:require('node:module').createRequire(file)});
    new vm.Script(fs.readFileSync(file,'utf8'),{filename:file}).runInContext(context);
    assert.equal(typeof context.module.exports[method],'function','Q38JB_VIEW_MODULES_LOAD');
  }
});

test('Q38JB_CONTENT_ROOTS: selected runs including zero join only the content root set',()=>{
  const saved = record();
  saved.input.profile_runs=[{kind:'profile-run',id:0},{kind:'profile-run',id:1},{kind:'profile-run',id:0}];
  saved.input.obstacles=[{kind:'column',id:5}];saved.input.timbers=[{kind:'timber',id:0}];
  const before=JSON.stringify(saved);
  assert.deepEqual(S.modelRoots(saved),['placement:1','column:5','timber:0','profile-run:0','profile-run:1'],'Q38JB_CONTENT_ROOTS');
  assert.equal(JSON.stringify(saved),before,'Q38JB_CONTENT_ROOTS_READONLY');
  assert.equal(Object.hasOwn(saved,'sourceIdentity'),false,'Q38JB_NO_PROFILE_IDENTITY_PIN');
  assert.deepEqual(S.modelTimberIds(saved),[0],'Q38JB_RUNS_NOT_TIMBER_SCHEDULE');
});

test('Q38JB_LEGACY_ROOTS: omitted runs and example models retain the previous root scope',()=>{
  const saved=record();delete saved.input.profile_runs;
  assert.deepEqual(S.modelRoots(saved),['placement:1']);
  saved.source.kind='example';saved.input.profile_runs=[{kind:'profile-run',id:1}];
  assert.deepEqual(S.modelRoots(saved),[],'Q38JB_EXAMPLE_NOT_LIVE');
});

test('Q38JB_RUN_CHANGED: changing selected run contents marks the saved model changed',()=>{
  const before=graph(),now=clone(before),saved=record(),bytes=JSON.stringify(saved);
  now.nodes.find(n=>n.key==='profile-run:1').valueFingerprint=hash(4);
  const result=S.freshness(S.index(before),S.index(now),S.modelRoots(saved));
  assert.equal(result.status,'changed','Q38JB_RUN_CHANGED');
  assert.deepEqual(result.changes,[{key:'profile-run:1',kind:'value'}]);
  assert.equal(JSON.stringify(saved),bytes,'Q38JB_SNAPSHOT_NOT_REWRITTEN');
});

test('Q38JB_MEMBER_CHANGED: run dependency closure catches changed profile members only when selected',()=>{
  const before=graph(),now=clone(before);
  now.nodes.find(n=>n.key==='profile-timber:1').definitionFingerprint=hash(4);
  let result=S.freshness(S.index(before),S.index(now),S.modelRoots(record()));
  assert.equal(result.status,'changed','Q38JB_MEMBER_CHANGED');
  assert.deepEqual(result.changes,[{key:'profile-timber:1',kind:'source-definition'}]);
  const unselected=record();delete unselected.input.profile_runs;
  result=S.freshness(S.index(before),S.index(now),S.modelRoots(unselected));
  assert.equal(result.contentStatus,'consistent','Q38JB_UNSELECTED_NOT_ADOPTED');
});

test('Q38JB_RUN_MISSING: removed run is missing; same-content reappearance never proves continuity',()=>{
  const before=graph(),now=clone(before);
  now.nodes=now.nodes.filter(n=>n.key!=='profile-run:1');
  const missing=S.freshness(S.index(before),S.index(now),S.modelRoots(record()));
  assert.equal(missing.status,'missing','Q38JB_RUN_MISSING');
  assert.ok(missing.changes.some(c=>c.key==='profile-run:1'));
  const same=S.freshness(S.index(before),S.index(clone(before)),S.modelRoots(record()));
  assert.equal(same.status,'unknown','Q38JB_RUN_CONTINUITY_UNKNOWN');
  assert.equal(same.contentStatus,'consistent');
  assert.match(same.message,/物件延續性未知/);
});

test('Q38JB_SAME_REVISION: profile source session rejects a changed final native revision',async()=>{
  const old=graph(),newer=clone(old),context={id:'same-project'};newer.revision++;
  let reads=0;
  const session=S.createSession({context:()=>context,stamp:()=>1,read:async()=>clone(++reads===1?old:newer),readSnapshot:async()=>clone(old)});
  await assert.rejects(session.inspect(record()),/來源已更新/);
  assert.equal(reads,2);
});

test('Q38JB_PROFILE_DISPLAY: actual native world member meshes are displayed unchanged with exact material total',()=>{
  const result=clone(native.model.result),before=JSON.stringify(result);
  const displayed=V.spacePreviewObjects(result,{space:false,walls:false,roof:false});
  const profiles=displayed.filter(o=>o.label==='斷面拉伸件');
  assert.equal(profiles.length,3,'Q38JB_PROFILE_DISPLAY');
  for(let i=0;i<profiles.length;i++){
    assert.deepEqual(profiles[i].vertices_mm,members()[i].vertices_mm,'Q38JB_SAVED_WORLD_MESH');
    assert.deepEqual(profiles[i].triangles,members()[i].triangles,'Q38JB_ROOF_NEVER_CUTS_PROFILE');
    assert.equal(profiles[i].section_profile.coordinate_space,'world');
    assert.equal(profiles[i].role,'geometry','Q38JB_ENVELOPE_NOT_DISPLAYED');
  }
  assert.equal(profiles.reduce((n,o)=>n+BigInt(o.section_profile.material_volume_mm3),0n),6415200n,'Q38JB_MEMBER_MATERIAL_ONLY');
  assert.equal(result.profile_runs.derived.objects.filter(o=>o.role==='reference').length,1,'Q38JB_SAVED_ENVELOPE_RETAINED');
  assert.equal(JSON.stringify(result),before,'Q38JB_DISPLAY_READONLY');
});

test('Q38JB_SHARED_SWITCH: one timber visibility flag controls both materials and preserves legacy labels',()=>{
  const result=clone(native.model.result);
  const visible=V.spacePreviewObjects(result,{space:false,walls:false});
  assert.equal(visible.filter(o=>o.label==='角材結構').length,1);
  assert.equal(visible.filter(o=>o.label==='斷面拉伸件').length,3,'Q38JB_SHARED_SWITCH_VISIBLE');
  assert.equal(V.spacePreviewObjects(result,{space:false,walls:false,timbers:false}).length,0,'Q38JB_SHARED_SWITCH');
  const legacy=clone(result);delete legacy.profile_runs;
  assert.deepEqual(V.spacePreviewObjects(legacy,{space:false,walls:false}),visible.filter(o=>o.label==='角材結構'),'Q38JB_LEGACY_TIMBER_DISPLAY');
});

test('Q38JB_ENVELOPE_NOT_DRAWN: canvas receives only member triangles and one profile legend',()=>{
  const h=canvasHarness();
  try{
    const onlyProfiles={profile_runs:clone(native.model.result.profile_runs)};
    h.view.setObjects(V.spacePreviewObjects(onlyProfiles));h.flush();
    const triangles=members().reduce((n,o)=>n+o.triangles.length,0);
    assert.equal(h.view.getState().objectCount,3,'Q38JB_ENVELOPE_NOT_DRAWN');
    assert.equal(h.view.getState().triangleCount,triangles,'Q38JB_ENVELOPE_TRIANGLES_EXCLUDED');
    assert.equal(h.faces.length,triangles,'Q38JB_ACTUAL_CANVAS_MEMBER_DRAW');
    assert.equal(h.labels.filter(label=>label==='斷面拉伸件').length,1,'Q38JB_PROFILE_LEGEND');
    h.view.setSelectableRoots([{kind:'profile-run',id:1}]);
    assert.equal(h.view.selectRoot({kind:'profile-run',id:1}),false,'Q38JB_NO_PROFILE_PICK');
    for(const face of h.faces){
      const x=face.reduce((n,p)=>n+p[0],0)/3,y=face.reduce((n,p)=>n+p[1],0)/3;
      assert.equal(h.view.hitTest(x,y),null,'Q38JB_PROFILE_NOT_A_LIVE_TIMBER');
    }
  }finally{h.view.destroy();}
});

test('Q38JB_TIMBER_SELECTION: existing typed timber selection cannot be borrowed by a profile member',()=>{
  const h=canvasHarness();
  try{
    h.view.setObjects(V.spacePreviewObjects(native.model.result,{space:false,walls:false}));h.flush();
    h.view.setSelectableRoots([{kind:'timber',id:0},{kind:'profile-run',id:1}]);
    assert.equal(h.view.selectRoot({kind:'timber',id:0}),true,'Q38JB_TIMBER_SELECTION');
    assert.deepEqual(h.view.getState().selection,{kind:'timber',id:0});
    assert.equal(h.view.selectRoot({kind:'profile-run',id:1}),false,'Q38JB_PROFILE_SELECTION_SCOPE');
    assert.deepEqual(h.view.getState().selection,{kind:'timber',id:0});
  }finally{h.view.destroy();}
});
