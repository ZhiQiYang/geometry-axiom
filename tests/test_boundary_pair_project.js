/* R17 portable host slice: archive bytes and explicit limited reader proof. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const scene='requires boundary-pair/1\nsurface 1 origin 0 0 2500 u +x v +y outline 0,0 500,0 500,13 1000,13 1000,1000 0,1000\n'+
  'boundary-pair begin 1 2\ntimber 1 27 20 role boundary\ntimber 2 27 20 role boundary\nplace 1 on 1 at-face e0 +u +n\nplace 2 on 1 at-face e2 +u +n\nboundary-pair end\n';
const manifest=()=>({format:P.FORMAT,projectId:'r17-pair',name:'13 mm 牆階',sceneHash:'0'.repeat(64),sources:[],faces:[]});
const profile=()=>({schema:'boundary-pair-native/1',capability:'boundary-pair/1',complete:false,
  supported:['scene-package','joint-evaluation','preview-confirm-cancel','group-delete','dump-load-undo-redo','host-app-literal-entry'],
  memberDimensionSources:['literal'],unsupported:['engineering-dimension-source','parameter-dimension-source']});
test('R17_PROJECT_ROUNDTRIP retains complete pair definitions without candidate metadata',async()=>{
  const bytes=await P.pack(scene,manifest(),new Map(),zip),loaded=await P.unpack(bytes,zip);
  assert.equal(loaded.scene,scene);assert.equal(loaded.manifest.format,'geometry-canvas/19');
  assert.deepEqual(loaded.manifest.requiredCapabilities,['boundary-pair/1']);
  assert.ok(!JSON.stringify(loaded.manifest).includes('ownerKey'));assert.ok(!JSON.stringify(loaded.manifest).includes('token'));
  const again=await P.unpack(await P.pack(loaded.scene,loaded.manifest,loaded.sources,zip),zip);
  assert.deepEqual(again.manifest,loaded.manifest);assert.equal(again.scene,scene);
});
test('R17_PROJECT_LIMITED_READER requires the explicit native literal host profile',async()=>{
  const loaded=await P.unpack(await P.pack(scene,manifest(),new Map(),zip),zip),m=loaded.manifest;
  assert.throws(()=>P.assertProjectCapabilities(m,P.readerCapabilities(['boundary-pair/1'])),/不支援/);
  const available=P.readerCapabilities([],[],m,scene,null,{},null,profile());
  P.assertProjectCapabilities(m,available);assert.ok(available.includes('boundary-pair/1'));
  for(const bad of [{...profile(),complete:true},{...profile(),memberDimensionSources:['literal','parameter']},
    {...profile(),supported:profile().supported.filter(item=>item!=='host-app-literal-entry')}])
    assert.throws(()=>P.readerCapabilities([],[],m,scene,null,{},null,bad),/不相容/);
});
test('R17_PROJECT_REQUIREMENTS rejects missing and unknown versions before packing',async()=>{
  assert.throws(()=>P.sceneCapabilities(scene.replace('requires boundary-pair/1\n','')),/缺少/);
  assert.throws(()=>P.sceneCapabilities(scene.replace('boundary-pair/1','boundary-pair/2')),/尚未支援/);
  assert.deepEqual(P.sceneCapabilities(scene),['boundary-pair/1']);
});
test('R17_PROJECT_NO_PARTIAL_GROUP rejects missing records and unclosed packages',async()=>{
  for(const broken of [scene.replace('timber 2 27 20 role boundary\n',''),scene.replace('boundary-pair end\n',''),
    scene.replace('place 2 on 1 at-face e2 +u +n','place 1 on 1 at-face e2 +u +n')])
    await assert.rejects(()=>P.pack(broken,manifest(),new Map(),zip),/互頂保存包/);
});
test('R17_PROJECT_NO_SOURCE_FLATTENING rejects unsupported member sources',async()=>{
  for(const source of ['param:1:1','eng:1:1:A']){
    const unsupported=scene.replace('timber 1 27 20','timber 1 '+source+' 20');
    await assert.rejects(()=>P.pack(unsupported,manifest(),new Map(),zip),/字面截面/);
  }
});
test('R17_PROJECT_DEFINITION_IDENTITY rejects dropped group and changed source on reload',()=>{
  P.assertBoundaryPairDefinitions(scene,scene);
  assert.throws(()=>P.assertBoundaryPairDefinitions(scene,scene.replace('at-face e2','at-face e4')),/不一致/);
  assert.throws(()=>P.assertBoundaryPairDefinitions(scene,scene.replace(/boundary-pair (begin 1 2|end)\n/g,'')),/不一致/);
  const reverse=scene.replace('boundary-pair begin 1 2','boundary-pair begin 2 1').replace(
    'timber 1 27 20 role boundary\ntimber 2 27 20 role boundary','timber 2 27 20 role boundary\ntimber 1 27 20 role boundary');
  P.assertBoundaryPairDefinitions(reverse,scene);
});
test('R17_PROJECT_NO_TOKEN_REPLAY rejects interactive control records in saved scene',async()=>{
  for(const command of ['boundary-pair confirm 7','boundary-pair cancel','boundary-pair delete 1 2'])
    await assert.rejects(()=>P.pack(scene+command+'\n',manifest(),new Map(),zip),/互動 token/);
});
test('R17_PROJECT_HISTORY pairs one changed confirmation with exactly one undo frame',()=>{
  const h=new P.ContextHistory(()=>({id:'r17',sources:new Map(),groups:new Map(),models:[],faceProjections:new Map(),featureAttachments:[]}));
  const command='boundary-pair-confirm 19 '+'a'.repeat(64);
  h.observe(command,{ok:true,history_changed:false},'session');assert.equal(h.undo.length,0);
  h.observe(command,{ok:false},'session');assert.equal(h.undo.length,0);
  h.observe(command,{ok:true,history_changed:true},'session');assert.equal(h.undo.length,1);
  h.observe('boundary-pair-cancel 19 '+'a'.repeat(64),{ok:true,history_changed:false},'session');assert.equal(h.undo.length,1);
  h.observe('line undo',{ok:true},'session');assert.equal(h.undo.length,0);assert.equal(h.redo.length,1);
  h.observe('line redo',{ok:true},'session');assert.equal(h.undo.length,1);assert.equal(h.redo.length,0);
});
