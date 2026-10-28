'use strict';
// Archive admission and workspace transaction tests. Native geometry and real
// fresh-profile UI round trips are separate acceptance gates, not mocked passes.
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const P=require('../geometry-web/project-store.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const capabilities=['engineering-spec/1','panel-fill/1','parameters/1'];
const base='boundary 4 outline 0,0 800,0 800,600 0,600\n';
const definitions=[
  'finish-surface 1 on boundary 4 origin 0 0 2480 u +x v +y n +z side +n name-hex 46',
  'panel-fill 1 definition-hex '+Buffer.from('{"id":1,"finishSurfaceId":1}').toString('hex'),
  'derived-placement 0 definition-hex '+Buffer.from('{"id":0,"fillId":1,"h":30}').toString('hex')
];
// Deliberately not a native-valid fill fixture: these tests establish the archive
// boundary only and never claim native source/geometry validation.
const scene=capabilities.map(c=>'requires '+c+'\n').join('')+base+definitions.join('\n')+'\n';
const manifest=()=>({projectId:'pf-save',name:'完成面',sources:[],faces:[],models:[],faceProjections:[]});
const pack=(s=scene,extra={})=>P.pack(s,{...manifest(),...extra},new Map(),zip);
function rewrite(bytes,change){
  const files=zip.unzipSync(bytes),m=JSON.parse(zip.strFromU8(files['manifest.json']));change(m);
  files['manifest.json']=zip.strToU8(JSON.stringify(m));return zip.zipSync(files);
}
test('PF_SAVE_DEFINITIONS_ONLY /19 round trip keeps three source records and ID 0',async()=>{
  const bytes=await pack(),loaded=await P.unpack(bytes,zip);
  assert.equal(loaded.manifest.format,'geometry-canvas/19');
  assert.deepEqual(loaded.manifest.requiredCapabilities,capabilities);
  assert.equal(loaded.scene,scene);
  assert.deepEqual(Object.keys(zip.unzipSync(bytes)).sort(),['manifest.json','world.scene']);
  assert.deepEqual(Object.keys(loaded.manifest).sort(),['faceProjections','faces','format','models','name','projectId','requiredCapabilities','sceneHash','sources']);
  assert.deepEqual(P.formatPolicy(loaded.manifest.format),{modelCollections:true,engineeringCandidate:true,canonicalScene:true});
});
test('PF_SAVE_NO_DOWNGRADE every old format rejects PF; missing and unknown capabilities reject',async()=>{
  const bytes=await pack();
  for(let i=1;i<19;i++)await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.format='geometry-canvas/'+i),zip));
  for(const cap of capabilities){
    await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==cap)),zip));
    await assert.rejects(()=>pack(scene.replace('requires '+cap+'\n','')),/能力宣告/);
  }
  await assert.rejects(()=>pack(scene.replace('panel-fill/1','panel-fill/2')),/尚未支援/);
  const old=await pack(base);
  await assert.rejects(()=>P.unpack(rewrite(old,m=>m.format=P.PANEL_FILL_FORMAT),zip));
});
test('PF_SAVE_READER_CAPABILITY cannot open PF with an older native service',()=>{
  P.assertProjectCapabilities({requiredCapabilities:capabilities},P.readerCapabilities(capabilities));
  assert.throws(()=>P.assertProjectCapabilities({requiredCapabilities:capabilities},P.readerCapabilities(['engineering-spec/1','parameters/1'])),/不支援/);
});
test('PF_SAVE_PROJECTION_COEXISTS source and projection definitions remain independent',async()=>{
  const faceProjections=[{bid:4,placement_id:0,projection:{kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'}}];
  const loaded=await P.unpack(await pack(scene,{faceProjections}),zip);
  assert.deepEqual(loaded.manifest.faceProjections,faceProjections);assert.equal(loaded.scene,scene);
  const old=await P.unpack(await pack(base,{faceProjections}),zip);
  assert.equal(old.manifest.format,P.PROJECTION_FORMAT);
});
test('PF_SAVE_CARD_COEXISTS /19 preserves /18 card capability and source',async()=>{
  const s=scene+'requires grid-card-reference/1\ngrid-system 4 name-hex 47 main-along none card-reference 10 8 3 u repeat -5 card v repeat 7 card\n';
  const loaded=await P.unpack(await pack(s),zip);
  assert.equal(loaded.scene,s);assert.equal(loaded.manifest.format,P.PANEL_FILL_FORMAT);
  assert.ok(loaded.manifest.requiredCapabilities.includes(P.CARD_CAPABILITY));
});
test('PF_SAVE_CANDIDATE_DEFINITION_COMPARE rejects silently changed/dropped records',()=>{
  P.assertPanelFillDefinitions(scene,scene.split('\n').reverse().map(l=>'  '+l+'  ').join('\n'));
  for(const line of definitions)assert.throws(()=>P.assertPanelFillDefinitions(scene,scene.replace(line,'')),/候選定義/);
  assert.throws(()=>P.assertPanelFillDefinitions(scene,scene.replace('derived-placement 0','derived-placement 9')),/候選定義/);
  assert.throws(()=>P.assertPanelFillDefinitions(scene,scene+definitions[0]+'\n'),/候選定義/);
});
function workspace(options={}){
  const calls=[],events=[],messages=[],elements=new Map();
  const element=id=>{if(!elements.has(id))elements.set(id,{textContent:'',dataset:{},classList:{toggle(){}},style:{},setAttribute(){},removeAttribute(){},querySelector:()=>null});return elements.get(id);};
  const env={GeometryProject:P,fflate:zip,crypto,structuredClone,JSON,TextEncoder,TextDecoder,Uint8Array,Map,Set,WeakMap,console,AbortSignal,
    requestAnimationFrame:()=>1,CustomEvent:class {constructor(type){this.type=type;}},
    window:{PanelFillWorkspace:{pending:false},dispatchEvent:e=>events.push(e.type),confirm:()=>true,addEventListener(){}},
    document:{getElementById:element,querySelectorAll:()=>[],querySelector:()=>null},
    oc:{busy:false,faces:[],bmap:{},edit:null},fe:{feats:{}},connection:{phase:'ready',session:'a'.repeat(32)},
    api:async command=>{calls.push(command);assert.equal(command,'dump');return {ok:true,text:base};},
    fetch:async(url,request)=>{calls.push(url);if(url==='/upload/cancel')return {ok:true,json:async()=>({ok:true})};
      assert.equal(url,'/upload/prepare');return {ok:true,json:async()=>options.candidate};},
    setStatus:s=>messages.push(s),toast:s=>messages.push(s),drawFaceEditor(){},renderFaceInspector(){},innerWidth:1280};
  vm.runInNewContext(fs.readFileSync(require.resolve('../geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  return {w:env.workspace,env,calls,events,messages};
}
test('PF_SAVE_PENDING_GUARD blocks formal archive, project opening and leave without writing',async()=>{
  const {w,env,calls}=workspace(),before=w.context(),state=w.getProjectState();
  env.window.PanelFillWorkspace.pending=true;
  await assert.rejects(()=>w.exportBytes(),/完成面與鋪排草稿尚未確認/);
  await assert.rejects(()=>w.openProject(()=>{throw Error('must not read');}),/請先確認或取消/);
  assert.equal(w.mayLeave(),false);assert.deepEqual(calls,[]);
  assert.equal(w.context(),before);assert.deepEqual(w.getProjectState(),state);
  env.window.PanelFillWorkspace.pending=false;
  const loaded=await P.unpack(await w.exportBytes(),zip);assert.equal(loaded.scene,base);
});
test('PF_SAVE_CONFIRM_PENDING result tracking prevents an archive before the receipt',async()=>{
  const {w}=workspace(),finish=w.beginNativeOperation('panel-fill-confirm 17');
  assert.equal(typeof finish,'function');
  await assert.rejects(()=>w.exportBytes(),/原生操作結果尚未取得/);
  finish();finish();await w.exportBytes();
});
test('PF_HISTORY_ONCE confirm uses shared history; no-op, failure and cancel do not change it',()=>{
  const {w}=workspace(),initial=w.getProjectState();
  for(const [command,result] of [['panel-fill-cancel 1',{ok:true}],['panel-fill-confirm 1',{ok:false}],['panel-fill-confirm 1',{ok:true,history_changed:false}]]){
    w.observe(command,result);assert.equal(w.history.undo.length,0);assert.equal(w.context().dirty,false);
  }
  w.observe('panel-fill-confirm 2',{ok:true,history_changed:true});
  assert.equal(w.history.undo.length,1);assert.equal(w.context().dirty,true);
  assert.equal(w.getProjectState().revision,initial.revision+1);
  w.observe('panel-fill-read',{ok:true});assert.equal(w.history.undo.length,1);
});
test('PF_SAVE_ATOMIC_REJECTION keeps World/context/dirty/history before native candidate commit',async()=>{
  const loaded=await P.unpack(await pack(),zip);
  for(const candidate of [
    {ok:false,error:'missing material version'},
    {ok:false,error:'missing parameter field'},
    {ok:false,error:'tampered fill reference'},
    {ok:true,token:7,capabilities:capabilities.filter(c=>c!==P.PANEL_FILL_CAPABILITY),required_capabilities:capabilities,final_objects:{boundaries:[],placements:[]},final_scene:scene},
    {ok:true,token:7,capabilities,required_capabilities:capabilities,final_objects:{boundaries:[],placements:[]},final_scene:scene.replace(definitions[1],'')},
    {ok:true,token:7,capabilities,required_capabilities:['engineering-spec/1'],final_objects:{boundaries:[],placements:[]},final_scene:scene}
  ]){
    const {w,calls}=workspace({candidate}),before=w.context(),state=w.getProjectState();
    await assert.rejects(()=>w.uploadScene(scene,{manifest:loaded.manifest,context:{},ids:[]}));
    assert.equal(w.context(),before);assert.deepEqual(w.getProjectState(),state);assert.equal(w.history.undo.length,0);
    assert.equal(calls.includes('/upload/confirm'),false);
    assert.deepEqual(calls,['dump','/upload/prepare',...(candidate.ok?['/upload/cancel']:[])]);
  }
});
