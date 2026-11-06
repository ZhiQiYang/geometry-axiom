/* Strict mixed-capability regressions for the #360 -> #365 stack.
 * Real archive/owner/transport implementations; controlled HTTP and DOM ports.
 */
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),path=require('node:path');
const ROOT=path.resolve(process.env.EVIDENCE_STACK_ROOT||path.join(__dirname,'..'));
const P=require(path.join(ROOT,'geometry-web/project-store.js')),E=require(path.join(ROOT,'geometry-web/evidence-links.js'));
const zip=require(path.join(ROOT,'geometry-web/vendor/fflate/umd/index.js'));
const epoch='0123456789abcdef0123456789abcdef';
const scene='requires identity-ledger/1\nboundary 1 outline 0,0 3000,0 3000,2000 0,2000\nidentity boundary 1 '+epoch+':1\n';
const settings=()=>({kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'wood',section:[27,33],material:null,length:3636,endTrim:5}],remnants:[],nextStockKey:2,nextRemnantKey:1});
async function fixture(){
  const bytes=new TextEncoder().encode('authored original PDF source'),hash=await P.sha(bytes);
  const evidence={schema:E.SCHEMA_V2,links:[{evidenceId:'e0',document:{sourceHash:hash,referencePageId:'page-1',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[0,0,300,200]},
    region:[10,20,80,40],target:{projectScope:'stack',kind:'boundary',id:1,definitionPin:'b'.repeat(64),valuePin:'c'.repeat(64),incarnation:epoch+':1'},
    observations:{drawing:{rawText:'915/2',rawValue:'915/2',unit:'mm',note:'kept'},measurement:null},humanConfirmation:null,identityBasis:'ledger',adoption:null}]};
  const manifest={projectId:'stack',name:'mixed stack',faces:[],sources:[{id:hash,hash,name:'same.pdf',type:'application/pdf',size:bytes.length,path:'sources/'+hash}],
    featureAttachments:{schema:P.Features.SCHEMA,records:[{kind:E.KIND,schema:E.SCHEMA_V2,value:evidence}]}};
  return{bytes,hash,evidence,manifest,sources:new Map([[hash,bytes]])};
}
test('R365_STACK_CUTTING strict ZIP preserves v2 evidence, original PDF, identity scene and exact cutting declarations',async()=>{
  const f=await fixture();let opened;
  await assert.doesNotReject(async()=>{
    f.manifest.featureAttachments.records.push(P.Features.record('cutting-settings',settings()));
    opened=await P.unpack(await P.pack(scene,f.manifest,f.sources,zip),zip);
  },'R365_STACK_CUTTING_V2_ADMISSION');
  assert.equal(opened.manifest.format,'geometry-canvas/17');assert.equal(opened.scene,scene);
  assert.deepEqual(opened.manifest.requiredCapabilities,['cutting-plan/1',E.SCHEMA_V2,'identity-ledger/1']);
  assert.deepEqual(opened.manifest.featureAttachments.records.find(r=>r.kind===E.KIND).value,f.evidence);
  assert.deepEqual(opened.manifest.featureAttachments.records.find(r=>r.kind==='cutting-settings').value,settings());
  assert.deepEqual(opened.sources.get(f.hash),f.bytes);
  assert.doesNotThrow(()=>P.assertProjectCapabilities(opened.manifest,P.readerCapabilities(['identity-ledger/1'],{cutting:true})));
  assert.throws(()=>P.assertProjectCapabilities(opened.manifest,P.readerCapabilities(['identity-ledger/1'])));
});
test('R365_STACK_R08 format19 keeps v2 evidence and unaccepted room rows out of World with both exact capabilities',async()=>{
  const f=await fixture();let opened,draft;
  await assert.doesNotReject(async()=>{
    const D=P.Features.RoomCandidates;assert.ok(D,'R365_STACK_ROOM_DRAFT_REGISTRY');
    const page={id:'page-1',sourceId:f.hash,page:1,imgW:300,imgH:200,mmPerPx:10,x:0,y:0,rot:0,opacity:.5,locked:false,
      calibration:{points:[[10,5],[90,5]],distanceMm:800,inputValue:800,inputUnit:'mm'},crop:[0,0,300,200],reviewRequired:false,records:[]};
    draft={schema:D.SCHEMA,draftId:'draft-1',anchor:{kind:'page',boundaryId:1,pageId:page.id,pagePin:D.pagePin(page)},
      analysis:{sourceId:f.hash,page:1,coordinateSpace:'image-pixel/1',pageSize:[300,200],crop:[0,0,300,200],options:{mode:'image',minWidth:1,minLength:8},barriers:[],analyzerRevision:D.ANALYZER_REVISION,total:1,complete:true,ignoredNested:0},
      rows:[{rowKey:'row-1',ordinal:1,method:'image-lines',sourcePoints:[[0,0],[10,0],[10,10],[0,10]],warnings:[],deviation:0,pointsMm:[[0,0],[100,0],[100,100],[0,100]],dimensions:[],
        rawInputs:{refRoomVertices:'0,0\n100,0\n100,100\n0,100',refRoomLength:'',refRoomEdge:'0'},draftRevision:0,status:'pending'}]};
    f.manifest.faces=[{bid:1,activePageId:page.id,pages:[page]}];f.manifest.featureAttachments.records.push(P.Features.record(D.KIND,draft));
    opened=await P.unpack(await P.pack(scene,f.manifest,f.sources,zip),zip);
  },'R365_STACK_ROOM_V2_FORMAT19');
  assert.equal(opened.manifest.format,'geometry-canvas/19');assert.equal(opened.scene,scene,'R365_STACK_DRAFT_NEVER_IN_WORLD');
  assert.deepEqual(opened.manifest.requiredCapabilities,[E.SCHEMA_V2,'identity-ledger/1','room-candidate-drafts/1']);
  assert.deepEqual(opened.manifest.featureAttachments.records.find(r=>r.kind==='room-candidates').value,draft);
  assert.deepEqual(opened.manifest.featureAttachments.records.find(r=>r.kind===E.KIND).value,f.evidence);
  assert.deepEqual(opened.sources.get(f.hash),f.bytes);
  assert.throws(()=>P.sceneCapabilities('requires room-candidate-drafts/1\n'));
});
test('R365_STACK_CONFIRM both native import and evidence adoption retain the actual app owner lease and one history step',async()=>{
  const {fixture:host,prepare}=require(path.join(ROOT,'tests/fixtures/evidence_adoption_host.cjs'));
  for(const kind of ['definition-import','engineering']){
    let release,f;const gate=new Promise(resolve=>release=resolve);
    f=host({native:async command=>{assert.equal(command,kind+'-confirm 7');await gate;return f.receipt;}});
    f.w.observeNativeRevision({revision:7});if(kind==='engineering')prepare(f);
    const count=f.w.history.undo.length,pending=f.api(kind+'-confirm 7');
    assert.throws(()=>f.w.assertEditable(),/確認/,'R365_STACK_NATIVE_CONFIRM_LEASE_'+kind);
    release();assert.equal((await pending).ok,true);assert.equal(f.w.history.undo.length,count+1,'R365_STACK_ONE_HISTORY_'+kind);
    assert.doesNotThrow(()=>f.w.assertEditable());
    if(kind==='engineering')assert.equal(f.w.readFeatureAttachment(E.KIND).links[0].adoption.literal,'3235');
  }
});
