/* R09a + latest main: execute the actual archive, history and workspace owner.
 * The finite DOM and HTTP replies below are controlled ports, not browser/native
 * evidence. test_identity_definition_import_merge.py supplies the native proof.
 */
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const ROOT=path.resolve(process.env.IDENTITY_MAIN_MERGE_ROOT||path.join(__dirname,'..'));
const P=require(path.join(ROOT,'geometry-web/project-store.js'));
const zip=require(path.join(ROOT,'geometry-web/vendor/fflate/umd/index.js'));
const scene='requires identity-ledger/1\n';
const settings=()=>({kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'wood',section:[27,33],material:null,length:3636,endTrim:5}],remnants:[],nextStockKey:2,nextRemnantKey:1});
async function archive() {
  let bytes;
  await assert.doesNotReject(async()=>{
    const featureAttachments={schema:P.Features.SCHEMA,records:[P.Features.record('cutting-settings',settings())]};
    bytes=await P.pack(scene,{format:P.FORMAT,projectId:'identity-main',name:'identity plus cutting',sources:[],faces:[],featureAttachments},new Map(),zip);
  },'R360_MERGE_MIXED_ARCHIVE_SUPPORTED');
  return bytes;
}
function owner() {
  const elements=new Map(),requests=[];
  function element(id){if(!elements.has(id))elements.set(id,{textContent:'',dataset:{},classList:{toggle(){}},style:{},value:'',
    addEventListener(){},setAttribute(){},removeAttribute(){},replaceChildren(){},click(){},close(){},showModal(){},querySelector:()=>({}),
    parentElement:{clientWidth:800,clientHeight:600},append(){},prepend(){}});return elements.get(id);}
  const env={GeometryProject:P,fflate:zip,crypto:crypto.webcrypto,structuredClone,JSON,TextEncoder,TextDecoder,Uint8Array,Map,Set,WeakMap,console,AbortSignal,File,Blob,
    requestAnimationFrame:()=>1,CustomEvent:class{},ResizeObserver:class{observe(){}},pageRuntimeVersion:'r360-merge-vm',checkApiSession(){},
    window:{dispatchEvent(){},addEventListener(){},confirm:()=>false},document:{getElementById:element,querySelectorAll:()=>[],querySelector:()=>element('scroll'),
      addEventListener(){},createElement:tag=>element(tag)},oc:{busy:false,faces:[],bmap:{},edit:null},fe:{feats:{}},connection:{phase:'ready'},
    api:async command=>{assert.ok(command==='dump'||command==='dump-deidentified');return{ok:true,text:'',revision:1};},
    fetch:async(url,request)=>{requests.push(url);assert.ok(['/upload/prepare','/upload/confirm','/upload/cancel'].includes(url));
      if(url==='/upload/prepare'){assert.equal(request.body,scene);return{ok:true,json:async()=>({ok:true,token:7,
        capabilities:['identity-ledger/1','definition-import/1'],required_capabilities:['identity-ledger/1'],final_scene:scene,
        final_objects:{boundaries:[],placements:[]}})};}
      return{ok:true,json:async()=>({ok:true,path:'identity-main.scene',revision:2})};},
    curScene:{},resetSceneFocus(){},markSceneItem(){},sceneMenuDisplay:name=>name,refreshActive:async()=>{},
    setStatus(){},toast(){},drawFaceEditor(){},renderFaceInspector(){},innerWidth:1280,feUlImgToMm:(_p,x,y)=>[x,y],feFit(){}};
  vm.runInNewContext(fs.readFileSync(path.join(ROOT,'geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  return{w:env.workspace,requests};
}
test('R360_MERGE_CAPABILITIES retains native identity and all editor admissions without promoting operation or draft capabilities',()=>{
  const capabilities=P.readerCapabilities(['identity-ledger/1','definition-import/1'],{cutting:true});
  for(const name of ['identity-ledger/1','cutting-plan/1','grid-card-draft/1','room-candidate-drafts/1'])
    assert.ok(capabilities.includes(name),'R360_MERGE_CAPABILITY_'+name);
  assert.equal(capabilities.includes('definition-import/1'),false);
  assert.doesNotThrow(()=>P.validateManifestCapabilities(['identity-ledger/1','cutting-plan/1','grid-card-draft/1','room-candidate-drafts/1']));
  assert.deepEqual(P.sceneCapabilities(scene),['identity-ledger/1']);
  assert.throws(()=>P.sceneCapabilities('requires room-candidate-drafts/1\n'),/不是場景能力/);
  assert.throws(()=>P.sceneCapabilities('requires definition-import/1\n'),/尚未支援/);
});
test('R360_MERGE_ARCHIVE preserves active identity and exact cutting declarations through a cold ZIP read',async()=>{
  const bytes=await archive(),opened=await P.unpack(bytes,zip);
  assert.equal(opened.manifest.format,'geometry-canvas/17');assert.equal(opened.scene,scene);
  assert.deepEqual(opened.manifest.requiredCapabilities,['cutting-plan/1','identity-ledger/1']);
  assert.deepEqual(opened.manifest.featureAttachments.records[0].value,settings());
  assert.deepEqual(Object.keys(zip.unzipSync(bytes)).sort(),['manifest.json','world.scene']);
});
test('R360_MERGE_OWNER opens the mixed archive through the shipped transaction owner and supports undo redo',async()=>{
  const bytes=await archive(),h=owner(),before=h.w.context();
  await assert.doesNotReject(()=>h.w.importBytes(bytes),'R360_MERGE_OWNER_CUTTING_AND_IDENTITY');
  assert.notEqual(h.w.context(),before);const adopted=h.w.context();
  assert.equal(adopted.id,'identity-main');assert.deepEqual(adopted.featureAttachments[0].value,settings());
  assert.deepEqual(h.requests,['/upload/prepare','/upload/confirm']);assert.equal(h.w.history.undo.length,1);
  h.w.observe('line undo',{ok:true});assert.equal(h.w.context(),before);
  h.w.observe('line redo',{ok:true});assert.equal(h.w.context(),adopted);
});
test('R360_MERGE_NOOP definition-import confirmation shares the generic native no-op history guard',()=>{
  const h=new P.ContextHistory(()=>({id:'history',sources:new Map(),groups:new Map(),featureAttachments:[]}));
  h.observe('definition-import-confirm 7',{ok:true,history_changed:true});assert.equal(h.undo.length,1);
  const saved=h.snapshot();h.observe('definition-import-confirm 8',{ok:true,history_changed:false});
  assert.equal(h.undo.length,1,'R360_MERGE_NO_PHANTOM_IMPORT_HISTORY');assert.deepEqual(h.snapshot(),saved);
  h.observe('line undo',{ok:true});assert.equal(h.undo.length,0);assert.equal(h.redo.length,1);
});
test('R360_MERGE_CDP retains both parents scope flags and the main-only strict context menu selectors',()=>{
  const {runConfiguration}=require(path.join(ROOT,'geometry-web/cdp_test.js'));
  const basic={GEOMETRY_TEST_URL:'http://127.0.0.1:48991',GEOMETRY_FEEDBACK_DIR:path.join(os.tmpdir(),'r360-merge-scope')};
  const flags=['GEOMETRY_IDENTITY_LEDGER_ONLY','GEOMETRY_ROOM_CANDIDATE_ONLY','GEOMETRY_GRID_CARD_ENTRY_ONLY','GEOMETRY_DEFINITION_IMPORT_ONLY','GEOMETRY_CANVAS_CONTEXT_MENU_ONLY'];
  for(const flag of flags){const got=runConfiguration({...basic,[flag]:'1'});assert.equal(got.mode,'partial','R360_MERGE_CDP_'+flag);assert.deepEqual(got.filters,[flag]);}
  assert.throws(()=>runConfiguration({...basic,GEOMETRY_IDENTITY_LEDGER_ONLY:'1',GEOMETRY_ROOM_CANDIDATE_ONLY:'1'}),/only one CDP scope/);
  assert.throws(()=>runConfiguration({...basic,GEOMETRY_CANVAS_CONTEXT_MENU_CASES:'C11'}),/requires ONLY/);
  assert.throws(()=>runConfiguration({...basic,GEOMETRY_CANVAS_CONTEXT_MENU_ONLY:'1',GEOMETRY_CANVAS_CONTEXT_MENU_CASES:'C11,C11'}),/unique/);
});
