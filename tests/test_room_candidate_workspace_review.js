/* Independent #358 regression probes. These load the unmodified workspace in
 * Node VM, with owner/native/DOM boundaries controlled; this is not a browser. */
'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {webcrypto} = require('node:crypto');
const root = process.env.GEOMETRY_REVIEW_ROOT || path.resolve(__dirname, '..');
const D = require(path.join(root, 'geometry-web/room-candidate-draft.js'));
const S = require(path.join(root, 'geometry-web/source-plane.js'));
const R = require(path.join(root, 'geometry-web/room-collection.js'));
const source = fs.readFileSync(path.join(root, 'geometry-web/room-collection-workspace.js'), 'utf8');
const copy = value => structuredClone(value);
const rect = [[0,0],[1000,0],[1000,1000],[0,1000]];
const sourceId = 'ab'.repeat(32);
function page(id) { return {id,sourceId,page:1,imgW:100,imgH:80,x:0,y:0,rot:0,mmPerPx:10,crop:[0,0,100,80],opacity:0.5,locked:false,
  calibration:{points:[[0,0],[10,0]],distanceMm:100,inputValue:100,inputUnit:'mm'}}; }
function savedDraft(host = page('page-1'), bid = 1, draftId = 'saved') {
  return {schema:D.SCHEMA,draftId,anchor:{kind:'page',boundaryId:bid,pageId:host.id,pagePin:D.pagePin(host)},
    analysis:{sourceId,page:1,coordinateSpace:'image-pixel/1',pageSize:[100,80],crop:[0,0,100,80],options:{mode:'image',minWidth:1,minLength:8},barriers:[],analyzerRevision:D.ANALYZER_REVISION,total:1,complete:true,ignoredNested:0},
    rows:[{rowKey:'row-1',ordinal:1,method:'image-lines',sourcePoints:rect,warnings:[],deviation:0,pointsMm:rect,dimensions:[],rawInputs:{refRoomVertices:'0,0\n1000,0\n1000,1000\n0,1000',refRoomLength:'',refRoomEdge:'0'},draftRevision:0,status:'pending'}]};
}
function fixture(owner = null) {
  owner ||= {token:'A',revision:1,pages:{1:page('page-1'),2:page('page-2')},attachments:{A:{'source-rooms':S.empty(),'room-candidates':null},B:{'source-rooms':S.empty(),'room-candidates':null}},writes:[],protocol:[],confirms:0,collects:0,notices:[],allowConfirm:true};
  const W = {getProjectState:()=>({id:owner.projectId||owner.token,contextToken:owner.token,revision:owner.revision}),getModelOperationState:()=>({context:owner.projectId||owner.token,contextToken:owner.token,frame:owner.token,revision:owner.revision,blocked:false,group:false}),
    readFeatureAttachment:(kind,token)=>{assert.equal(token,owner.token);return copy(owner.attachments[owner.token][kind]);},
    setFeatureAttachment:(kind,value,token,options)=>{assert.equal(token,owner.token);if(value&&kind===D.KIND)D.validate(value);owner.writes.push({kind,value:copy(value),token,options:copy(options)});owner.protocol.push(value===null?'discard':'write');owner.attachments[owner.token][kind]=copy(value);owner.revision++;if(owner.onWrite)owner.onWrite(kind,value);},
    active:bid=>owner.pages[bid],assertEditable(){},escape:value=>String(value),history:{group:null},sync(){}};
  const window = new EventTarget(), oc = {edit:{bid:1},bmap:{1:[{verts:rect}],2:[{verts:rect}]}};
  const nativeCalls = [], nativeRows = {1:{ok:true,id:1,geometryFingerprint:'bb'.repeat(32),loops:[{verts:rect}]}};
  let pane = null;
  const sandbox = {GeometryRoomCandidateDraft:D,GeometrySourcePlane:S,GeometryRoomCollection:R,ReferenceWorkspace:W,structuredClone,crypto:webcrypto,window,oc,
    document:{getElementById:id=>id==='faceInspectorContent'?pane:null},fe:{draft:{pts:[]}},connection:{phase:'ready'},
    RoomOutlineWorkspace:{hasWork:false,reset(){},paneHTML:()=>'',collect:async bid=>{owner.collects++;owner.protocol.push('analyze');if(owner.onCollect)await owner.onCollect(bid);}},
    renderFaceInspector(){},drawFaceEditor(){},feSetTool(){},toast:message=>owner.notices.push(message),confirm:()=>{owner.confirms++;return owner.allowConfirm;},
    apiRequest:async command=>{
      const settle=window.RoomCollectionWorkspace?.beginNativeRequest(command);let result;
      try{
        nativeCalls.push(command);if(owner.onNative)await owner.onNative(command);
        result=command==='objects'?{ok:true,faces:Object.values(nativeRows).map(row=>({id:row.id,kind:'boundary'}))}
          :copy(nativeRows[Number(command.replace(/^boundary /,''))]||{ok:false,error:'BOUNDARY_NOT_FOUND'});
        return result;
      }finally{settle?.(result);}
    },
    feUlImgToMm:(_,x,y)=>[x,y],RoomOutline:{integerProposal:points=>({points,deviation:0}),canonicalLoop:JSON.stringify}};
  vm.runInNewContext(source,sandbox,{filename:path.join(root,'geometry-web/room-collection-workspace.js')});
  const workspace = window.RoomCollectionWorkspace;
  workspace.configure({readSource:()=>({meta:{type:'image/png'}}),readIncarnation:id=>Object.hasOwn(oc.bmap,id)?'native-'+id:null,
    beginTransaction(){},assertTransaction(){},endTransaction(){},preflightAttachment(){},groupOpen(){},labelTransaction(){},adoptLegacySource(){}});
  function makePane(bid) {
    const elements = new Map();
    for(const selector of ['#roomNewMethod','#roomNew','#roomCandidatesDiscard'])elements.set(selector,{value:'candidates',listeners:{},addEventListener(type,fn){this.listeners[type]=fn;}});
    pane={isConnected:true,querySelector:s=>elements.get(s)||null,querySelectorAll:()=>[]};
    workspace.paneHTML(bid);workspace.bindPane(pane,bid);
    return {pane,elements,click:selector=>elements.get(selector).listeners.click(),change:()=>elements.get('#roomNewMethod').listeners.change()};
  }
  function receive(count=0,bid=1) {
    const candidates=Array.from({length:count},(_,i)=>({key:'candidate-'+i,points:rect,method:'image-lines',warnings:[]}));
    const request={mode:'image',minWidth:1,minLength:8,barriers:[]};
    workspace.receiveCandidates(bid,{candidates,total:count,complete:true,ignoredNested:0},request,workspace.captureCandidateStamp(bid));
  }
  return {owner,workspace,window,oc,makePane,receive,nativeRows,nativeCalls,apiRequest:sandbox.apiRequest};
}
for(const count of [0,1])test('R358-02 project switch cannot '+(count?'overwrite':'delete')+' target draft',()=>{
  const f=fixture();f.receive(count);const original=savedDraft(page('page-2'),2,'project-b');f.owner.attachments.B[D.KIND]=copy(original);
  f.owner.token='B';f.window.dispatchEvent(new Event('project-info-changed'));
  assert.equal(f.workspace.candidateSnapshot().stale,true);
  try{f.workspace.flushCandidates();}catch(error){f.owner.notices.push(error.message);}
  console.log(JSON.stringify({case:'R358-02',count,writes:f.owner.writes.map(w=>({token:w.token,draftId:w.value?.draftId||null})),notices:f.owner.notices}));
  assert.deepEqual(f.owner.attachments.B[D.KIND],original,'old project must never write with newly current project token');
});
test('R358-02 stale discard cannot delete the new project draft',async()=>{
  const f=fixture();f.receive(1);const pane=f.makePane(1),original=savedDraft(page('page-2'),2,'project-b');f.owner.attachments.B[D.KIND]=copy(original);
  f.owner.token='B';f.window.dispatchEvent(new Event('project-info-changed'));await pane.click('#roomCandidatesDiscard');
  console.log(JSON.stringify({case:'R358-02-discard',writes:f.owner.writes.map(w=>({token:w.token,value:w.value})),notices:f.owner.notices}));
  assert.deepEqual(f.owner.attachments.B[D.KIND],original);
});
test('R358-02 old frame cannot resurrect a draft removed by local undo',()=>{
  const f=fixture();f.owner.projectId='same-project';f.receive(1);f.workspace.flushCandidates();
  f.owner.attachments['A-after-undo']={'source-rooms':S.empty(),'room-candidates':null};f.owner.token='A-after-undo';f.window.dispatchEvent(new Event('project-info-changed'));
  try{f.workspace.flushCandidates();}catch(error){f.owner.notices.push(error.message);}
  console.log(JSON.stringify({case:'R358-02-undo',sameProject:f.owner.projectId,restoredDraft:f.owner.attachments[f.owner.token][D.KIND]?.draftId||null}));
  assert.equal(f.owner.attachments[f.owner.token][D.KIND],null,'runtime owner from the pre-undo frame cannot resurrect its prior draft');
});
for(const count of [0,1])test('R358-03 cross-anchor analysis explicitly discards saved draft before collecting '+count+' rows',async()=>{
  const f=fixture();f.owner.attachments.A[D.KIND]=savedDraft();const pane=f.makePane(2);assert.equal(f.workspace.candidateSnapshot(),null);
  f.owner.onCollect=bid=>f.receive(count,bid);await pane.change();await pane.click('#roomNew');f.workspace.flushCandidates();
  console.log(JSON.stringify({case:'R358-03',count,confirms:f.owner.confirms,protocol:f.owner.protocol,collects:f.owner.collects,savedAfterSync:f.owner.attachments.A[D.KIND]?.anchor||null}));
  assert.equal(f.owner.confirms,1);assert.deepEqual(f.owner.protocol.slice(0,2),['discard','analyze']);assert.equal(f.owner.writes[0].value,null);assert.equal(f.owner.writes[0].options.recordHistory,true);
});
test('R358-03 refusing cross-anchor discard leaves saved draft and analysis untouched',async()=>{
  const f=fixture();const original=savedDraft();f.owner.attachments.A[D.KIND]=copy(original);f.owner.allowConfirm=false;
  const pane=f.makePane(2);await pane.change();await pane.click('#roomNew');
  console.log(JSON.stringify({case:'R358-03-cancel',confirms:f.owner.confirms,collects:f.owner.collects,writes:f.owner.writes.length}));
  assert.equal(f.owner.confirms,1);assert.equal(f.owner.collects,0);assert.equal(f.owner.writes.length,0);assert.deepEqual(f.owner.attachments.A[D.KIND],original);
});
for(const present of [true,false])test('R358-04 roomsPin uses '+(present?'current native geometry':'null for a missing D3'),async()=>{
  const f=fixture(),plane=S.fromPage(f.owner.pages[1],'image/png','plane-a'),room={id:'room-a',name:'room',boundaryRef:{kind:'boundary',id:1,associationPin:'aa'.repeat(32)},acceptedBasisRevision:1,reviewState:'needs-review'};
  const collection={id:'collection-a',planeId:plane.id,roomIds:[room.id]};f.owner.attachments.A['source-rooms']={...S.empty(),planes:[plane],collections:[collection],rooms:[room]};
  if(!present){delete f.oc.bmap[1];delete f.nativeRows[1];}
  const native=await f.apiRequest('boundary 1');if(!present)await f.apiRequest('objects');f.nativeCalls.length=0;
  const actual=f.workspace.captureCandidateStamp(2).roomsPin,expected=D.roomsPin([{...room,boundaryRef:{id:1,geometryFingerprint:native.ok?native.geometryFingerprint:null}}]);
  console.log(JSON.stringify({case:'R358-04',present,actual,expected,nativeResponse:native,nativeCallsDuringCapture:f.nativeCalls,associationPin:room.boundaryRef.associationPin}));
  assert.equal(actual,expected,'associationPin is a prior acceptance receipt, not R51 current native fingerprint');
});
test('R358-08 saving stale same-project draft preserves original anchor across reopen',()=>{
  const f=fixture();const original=savedDraft();f.owner.attachments.A[D.KIND]=copy(original);f.owner.pages[1].x=50;
  f.workspace.paneHTML(1);assert.equal(f.workspace.candidateSnapshot().stale,true);f.workspace.flushCandidates();
  const after=f.owner.attachments.A[D.KIND],reopened=fixture(f.owner);reopened.workspace.paneHTML(1);
  console.log(JSON.stringify({case:'R358-08',originalPin:original.anchor.pagePin,writtenPin:after.anchor.pagePin,reopenedStale:reopened.workspace.candidateSnapshot().stale,writes:f.owner.writes.length}));
  assert.deepEqual(after.anchor,original.anchor,'same-project stale sync is allowed but cannot repin its persistent anchor');
  assert.equal(reopened.workspace.candidateSnapshot().stale,true);
});
test('R358-08 stale collection draft cannot silently adopt a changed plane',()=>{
  const f=fixture(),plane=S.fromPage(f.owner.pages[1],'image/png','plane-a'),collection={id:'collection-a',planeId:plane.id,roomIds:[]};
  f.owner.attachments.A['source-rooms']={...S.empty(),planes:[plane],collections:[collection]};
  const original=savedDraft();original.anchor={kind:'collection',collectionId:collection.id,planeId:plane.id,planePin:D.planePin(plane),roomsPin:D.roomsPin([])};f.owner.attachments.A[D.KIND]=copy(original);
  plane.alignment.x=25;plane.basisRevision=2;
  f.workspace.paneHTML(1);assert.equal(f.workspace.candidateSnapshot().stale,true);f.workspace.flushCandidates();
  const reopened=fixture(f.owner);reopened.workspace.paneHTML(1);
  console.log(JSON.stringify({case:'R358-08-collection',original:original.anchor,written:f.owner.attachments.A[D.KIND].anchor,reopenedStale:reopened.workspace.candidateSnapshot().stale}));
  assert.deepEqual(f.owner.attachments.A[D.KIND].anchor,original.anchor);assert.equal(reopened.workspace.candidateSnapshot().stale,true);
});
test('control: fresh same-project pending draft sync retains its rows and anchor',()=>{
  const f=fixture(),original=savedDraft();f.owner.attachments.A[D.KIND]=copy(original);f.workspace.paneHTML(1);
  assert.equal(f.workspace.candidateSnapshot().stale,false);f.workspace.flushCandidates();
  assert.deepEqual(f.owner.attachments.A[D.KIND],original);assert.equal(f.owner.writes[0].token,'A');
});


// R358-02/03: preflight itself is asynchronous, before collect captures a worker owner.
function analysisDeferred() { let resolve; const promise=new Promise(r=>resolve=r);return {promise,resolve}; }
function nativePreflightFixture() {
  const f=fixture(),plane=S.fromPage(f.owner.pages[1],'image/png','plane-a');
  const room={id:'room-a',name:'room',boundaryRef:{kind:'boundary',id:1,associationPin:'aa'.repeat(32)},acceptedBasisRevision:1,reviewState:'needs-review'};
  f.owner.attachments.A['source-rooms']={...S.empty(),planes:[plane],collections:[{id:'collection-a',planeId:plane.id,roomIds:[room.id]}],rooms:[room]};
  const started=analysisDeferred(),release=analysisDeferred();let delayed=false;
  f.owner.onNative=async command=>{if(command==='boundary 1'&&!delayed){delayed=true;started.resolve();await release.promise;}};
  return {f,started,release};
}
test('R358-02 control: unchanged owner continues after native preflight',async()=>{
  const {f,started,release}=nativePreflightFixture(),pane=f.makePane(1);await pane.change();
  f.owner.onCollect=bid=>f.receive(1,bid);const pending=pane.click('#roomNew');await started.promise;
  release.resolve();await pending;f.workspace.flushCandidates();
  assert.equal(f.owner.collects,1);assert.equal(f.owner.writes.length,1);assert.equal(f.owner.writes[0].token,'A');
});
for(const kind of ['project','undo'])test('R358-02 native preflight cannot rebind a stale start after '+kind,async()=>{
  const {f,started,release}=nativePreflightFixture();if(kind==='undo')f.owner.projectId='same-project';
  const pane=f.makePane(1);await pane.change();
  f.owner.onCollect=bid=>f.receive(1,bid);const pending=pane.click('#roomNew');await started.promise;
  const next=kind==='project'?'B':'A-after-undo';
  f.owner.attachments[next]={'source-rooms':S.empty(),'room-candidates':null};f.owner.token=next;
  pane.pane.isConnected=false;f.makePane(1);f.window.dispatchEvent(new Event('project-info-changed'));
  release.resolve();await pending;f.workspace.flushCandidates();
  assert.equal(f.owner.collects,0,'old click must not initiate analysis under the replacement owner');
  assert.equal(f.owner.writes.length,0);assert.equal(f.owner.attachments[next][D.KIND],null);
});
test('R358-02 native preflight cannot resume a detached inspector',async()=>{
  const {f,started,release}=nativePreflightFixture(),pane=f.makePane(1);await pane.change();
  const pending=pane.click('#roomNew');await started.promise;
  pane.pane.isConnected=false;f.oc.edit.bid=2;f.makePane(2);
  release.resolve();await pending;
  assert.equal(f.owner.collects,0);assert.equal(f.owner.writes.length,0);
});
for(const accept of [true,false])test('R358-03 stale start never offers or executes B discard, confirm='+accept,async()=>{
  const {f,started,release}=nativePreflightFixture(),pane=f.makePane(1);await pane.change();
  const pending=pane.click('#roomNew');await started.promise;
  const original=savedDraft(page('page-2'),2,'project-b-existing');
  f.owner.attachments.B[D.KIND]=copy(original);f.owner.token='B';f.owner.allowConfirm=accept;
  pane.pane.isConnected=false;f.makePane(1);f.window.dispatchEvent(new Event('project-info-changed'));
  release.resolve();await pending;
  assert.deepEqual(f.owner.attachments.B[D.KIND],original);assert.equal(f.owner.writes.length,0);
  assert.equal(f.owner.confirms,0,'retired A action must not ask to discard B work');assert.equal(f.owner.collects,0);
});
test('R358-03 control: own discard may redraw inspector before valid analysis',async()=>{
  const f=fixture();f.owner.attachments.A[D.KIND]=savedDraft();f.oc.edit.bid=2;
  const pane=f.makePane(2);await pane.change();
  f.owner.onWrite=(kind,value)=>{if(kind===D.KIND&&value===null){pane.pane.isConnected=false;f.makePane(2);}};
  f.owner.onCollect=bid=>f.receive(1,bid);await pane.click('#roomNew');
  assert.equal(f.owner.confirms,1);assert.equal(f.owner.collects,1);
  assert.deepEqual(f.owner.protocol.slice(0,2),['discard','analyze']);assert.equal(f.owner.writes.length,1);
  assert.equal(f.owner.writes[0].options.recordHistory,true);assert.equal(f.workspace.candidateSnapshot().ownerToken,'A');
});
