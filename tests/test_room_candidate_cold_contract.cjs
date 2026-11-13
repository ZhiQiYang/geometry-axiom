/* The P358 oracle tests are Node-only. They do not certify a Chrome run. */
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const path=require('node:path');
const root=process.env.GEOMETRY_R358_TEST_ROOT||path.resolve(__dirname,'..');
const C=require(path.join(root,'geometry-web/cdp_room_candidate_contract.js'));
const Outline=require(path.join(root,'geometry-web/room-outline.js'));
const clone=value=>structuredClone(value),digest=value=>crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex');
function fixture(){
 const source=crypto.createHash('sha256').update('fixture source bytes').digest('hex'),nativePin='bb'.repeat(32);
 const page={id:'page',sourceId:source,page:1,imgW:320,imgH:200,mmPerPx:10,x:0,y:0,rot:0,
  calibration:{points:[[30,30],[290,30]],distanceMm:2600,inputValue:2600,inputUnit:'mm'},crop:[0,0,320,200],opacity:.5,locked:false,records:[]};
 const rows=C.EXPECTED_SOURCE_LOOPS.map((points,i)=>({rowKey:'row-'+i,ordinal:i+1,method:'image-lines',sourcePoints:points,
  warnings:[],deviation:0,pointsMm:points.map(p=>p.map(v=>v*10)),dimensions:[],rawInputs:{refRoomVertices:'raw '+i,refRoomLength:'',refRoomEdge:'0'},draftRevision:0,status:'pending'}));
 const before={projectId:'project',scene:'before\n',rooms:null,draft:{schema:'room-candidate-drafts/1',draftId:'draft',
  anchor:{kind:'page',boundaryId:1,pageId:'page',pagePin:'cc'.repeat(32)},analysis:{sourceId:source},rows},
  native:[{id:1,kind:'unspecified',geometryFingerprint:'dd'.repeat(32),loops:[]}],hostPage:page,sourceIds:[source],undo:4,redo:0,group:false};
 const plane={id:'plane',sourceId:source,page:1,coordinateSpace:'image-pixel/1',pageSize:[320,200],calibration:page.calibration,
  alignment:{x:0,y:0,mmPerPx:10,rotation:0},basisRevision:1};
 const room={id:'room',name:'first',boundaryRef:{kind:'boundary',id:2,associationPin:nativePin},acceptedBasisRevision:1,reviewState:'confirmed'};
 const after=clone(before);after.scene='accepted\n';after.rooms={schema:'source-rooms/3',planes:[plane],collections:[{id:'collection',planeId:'plane',roomIds:['room']}],rooms:[room]};
 after.native.push({id:2,kind:'unspecified',geometryFingerprint:nativePin,loops:[]});
 after.draft.rows[0]={...after.draft.rows[0],status:'accepted',roomId:'room'};
 after.draft.anchor={kind:'collection',collectionId:'collection',planeId:'plane',
  planePin:digest(['plane',source,1,'image-pixel/1',[320,200],[[[30,30],[290,30]],2600,2600,'mm'],[0,0,10,0],1]),
  roomsPin:digest([['room',2,nativePin,1,'confirmed']])};
 after.session={active:null,stale:false,expired:false,candidates:[{status:'accepted',reviewed:false},{status:'pending',reviewed:false}]};
 after.undo=5;
 return {before,after};
}
function archive(snapshot){return {scene:snapshot.scene,sources:new Map(snapshot.sourceIds.map(id=>[id,new Uint8Array(Buffer.from('fixture source bytes'))])),manifest:{projectId:snapshot.projectId,sources:snapshot.sourceIds.map(hash=>({hash})),
 featureAttachments:{records:[{kind:'source-rooms',value:clone(snapshot.rooms)},{kind:'room-candidates',value:clone(snapshot.draft)}]}}};}
function ownership(){return {sourceRuntime:{fresh:true,root:'/checkout',version:'v1',session:'source',pid:10},
 service:{fresh:true,root:'/checkout',version:'v1',session:'cold',pid:20},bridge:{state:'fresh'},profile:'/tmp/cold-profile',browserPid:30};}

test('P358 fixture invokes real image analysis and yields exactly the two independent source loops',()=>{
 const image=C.fixturePixels(),result=Outline.regions(Outline.imageObstacles(image),[0,0,image.width,image.height]);
 assert.equal(result.total,2);assert.equal(result.complete,true);assert.equal(result.ignoredNested,0);
 assert.deepEqual(result.candidates.map(row=>row.points),C.EXPECTED_SOURCE_LOOPS);
});
test('P358 accepted snapshot independently matches R51 plane and current native room pins',()=>{
 const {before,after}=fixture();assert.equal(C.acceptedSnapshot(before,after),true);
 assert.deepEqual(C.expectedAnchor(after.rooms,after.native),after.draft.anchor);
});
test('P358 rejects a page anchor left in storage even when the live batch claims acceptance',()=>{
 const {before,after}=fixture();after.draft.anchor=clone(before.draft.anchor);
 assert.throws(()=>C.acceptedSnapshot(before,after),{name:'AssertionError',code:'ERR_ASSERTION'});
});
test('P358 rejects an old roomsPin or a non-current native acceptance receipt',()=>{
 for(const field of ['roomsPin','associationPin']){
  const {before,after}=fixture();
  if(field==='roomsPin')after.draft.anchor.roomsPin='ee'.repeat(32);else after.rooms.rooms[0].boundaryRef.associationPin='ee'.repeat(32);
  assert.throws(()=>C.acceptedSnapshot(before,after),{name:'AssertionError',code:'ERR_ASSERTION'});
 }
});
test('P358 requires the original second row and unchanged host rather than any pending row',()=>{
 for(const mutation of [s=>s.draft.rows[1].rawInputs.refRoomVertices='lost',s=>s.draft.rows[1].roomId='premature',s=>s.hostPage.x=1,
  s=>s.native[0].geometryFingerprint='ff'.repeat(32),s=>s.session.candidates[1].reviewed=true,s=>s.session.nativePending=true]){
  const {before,after}=fixture();mutation(after);assert.throws(()=>C.acceptedSnapshot(before,after),{name:'AssertionError',code:'ERR_ASSERTION'});
 }
});
test('P358 archive oracle rejects changed World, rooms, draft or source bytes identity',()=>{
 const {after}=fixture();assert.equal(C.archiveMatches(archive(after),after),true);
 for(const mutation of [v=>v.scene+='changed',v=>v.manifest.featureAttachments.records[0].value.rooms[0].name='changed',
  v=>v.manifest.featureAttachments.records[1].value.rows.pop(),v=>v.manifest.sources[0].hash='00'.repeat(32),v=>v.sources.values().next().value[0]^=1]){
  const changed=archive(after);mutation(changed);assert.throws(()=>C.archiveMatches(changed,after),{name:'AssertionError',code:'ERR_ASSERTION'});
 }
});
test('P358 cold ownership rejects same profile/service, stale bridge and another checkout',()=>{
 assert.equal(C.coldOwnership(ownership(),'/tmp/source-profile'),true);
 for(const mutation of [v=>v.profile='/tmp/source-profile',v=>v.service.session='source',v=>v.service.pid=10,
  v=>v.service.fresh=false,v=>v.bridge.state='stale',v=>v.service.root='/other',v=>v.service.version='old']){
  const value=ownership();mutation(value);assert.throws(()=>C.coldOwnership(value,'/tmp/source-profile'),{name:'AssertionError',code:'ERR_ASSERTION'});
 }
 assert.throws(()=>C.coldOwnership(ownership(),undefined),{name:'AssertionError',code:'ERR_ASSERTION'});
});
test('P358 undo oracle compares saved state while excluding execution-time history identities',()=>{
 const {after}=fixture(),copy=clone(after);copy.undo=99;copy.redo=2;copy.session.stale=true;
 assert.deepEqual(C.savedState(copy),C.savedState(after));copy.draft.rows[1].status='accepted';
 assert.notDeepEqual(C.savedState(copy),C.savedState(after));
});

test('P90 save trace keeps distinct guards, real input target and the complete picker lifecycle',async()=>{
 const harness=require(path.join(root,'geometry-web/room_candidate_browser_test.js')),install=harness.installSaveProbe;
 assert.equal(typeof install,'function','P90_SAVE_TRACE_REQUIRED');
 const vm=require('node:vm'),window=new EventTarget(),original=async()=>null;
 const listening=new Set(),add=window.addEventListener.bind(window),remove=window.removeEventListener.bind(window);
 window.addEventListener=(type,fn,options)=>{listening.add(type);add(type,fn,options);};
 window.removeEventListener=(type,fn,options)=>{listening.delete(type);remove(type,fn,options);};
 Object.defineProperty(window,'showSaveFilePicker',{configurable:true,writable:true,value:original});
 const button={disabled:false,getBoundingClientRect:()=>({x:10,y:20,width:30,height:40})};
 let disconnected=false;
 let takeFailure=false,cleanupFailure=false;
 class Observer{constructor(callback){this.callback=callback;}observe(){}takeRecords(){if(takeFailure)throw Error('take-records fault');return [];}disconnect(){disconnected=true;if(cleanupFailure)throw Error('cleanup fault');}}
 const reference={busy:true,history:{group:null},getModelOperationState:()=>({blocked:true}),getEvidenceState:()=>({blocked:true}),getProjectInfo:()=>({editingBlocked:false})};
 const context={window,ReferenceWorkspace:reference,RoomCollectionWorkspace:{hasWork:false,busy:false,transactionLease:null},
  oc:{busy:false,focus:{t:'face',id:2},edit:{bid:2}},fe:{draft:{pts:[]},ulCalib:null},performance:{now:()=>7},
  document:{querySelector:()=>button,getElementById:id=>id==='status'?{textContent:'accepted'}:id==='toastRegion'?{}:null},
  MutationObserver:Observer,Blob,Uint8Array,btoa};
 vm.runInNewContext('('+install.toString()+')()',context);
 const event=new Event('click');Object.defineProperty(event,'target',{value:{id:'faceEditorViewport',tagName:'DIV',dataset:{}}});window.dispatchEvent(event);
 const handle=await window.showSaveFilePicker(),writer=await handle.createWritable();
 await writer.write(new Uint8Array([65,66]));await writer.close();
 assert.equal(typeof writer.abort,'function','P90_SAVE_ADAPTER_RETAINS_ABORT');await writer.abort();
 reference.getModelOperationState=()=>{throw Error('getter fault');};takeFailure=cleanupFailure=true;
 const trace=window.__roomSaveProbe.dispose();
 assert.equal(window.__roomSave,'QUI=');assert.equal(window.showSaveFilePicker,original);
 assert.equal(window.__roomSaveProbe,undefined);assert.equal(disconnected,true);
 const armed=trace.events[0];assert.equal(armed.encodedType,'object');assert.equal(armed.referenceBusy,true);assert.equal(armed.objectBusy,false);
 assert.ok(trace.events.some(row=>row.phase==='click'&&row.target==='DIV#faceEditorViewport'),'P90_SAVE_TRACE_INPUT_TARGET');
 for(const phase of ['picker','create-writable','write-begin','write-complete','close','abort','final'])
  assert.ok(trace.events.some(row=>row.phase===phase),'P90_SAVE_TRACE_PHASE_'+phase);
 const count=trace.events.length;window.dispatchEvent(event);assert.equal(trace.events.length,count,'P90_SAVE_TRACE_LISTENER_RELEASE');
 assert.equal(listening.size,0);assert.ok(trace.events.some(row=>row.traceError==='getter fault'));
 assert.ok(trace.events.some(row=>row.phase==='trace-cleanup-error'&&row.operation==='observer'));
 class BrokenObserver extends Observer{observe(){throw Error('install fault');}}
 assert.throws(()=>vm.runInNewContext('('+install.toString()+')()',{...context,MutationObserver:BrokenObserver}),/install fault/);
 assert.equal(listening.size,0,'P90_SAVE_TRACE_INSTALL_FAILURE_CLEANUP');assert.equal(window.showSaveFilePicker,original);
 const messages=[];await harness.collectSaveTrace(async()=>{throw Error('CDP read fault');},line=>messages.push(line));
 assert.deepEqual(messages,['P90_SAVE_TRACE_ERROR CDP read fault'],'P90_SAVE_TRACE_PRESERVES_PRIMARY_ERROR');
});
