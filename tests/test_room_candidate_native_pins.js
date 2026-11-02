'use strict';
// Real API function, workspace and ContextHistory; native delivery and DOM are
// controlled. This suite is deliberately independent of a browser or bridge.
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {webcrypto}=require('node:crypto');
const root=process.env.GEOMETRY_REVIEW_ROOT||path.resolve(__dirname,'..');
const D=require(path.join(root,'geometry-web/room-candidate-draft.js'));
const S=require(path.join(root,'geometry-web/source-plane.js'));
const R=require(path.join(root,'geometry-web/room-collection.js'));
const P=require(path.join(root,'geometry-web/project-store.js'));
const {installClientTransportTrace}=require(path.join(root,'geometry-web/transport_failure_trace.js'));
const source=fs.readFileSync(path.join(root,'geometry-web/room-collection-workspace.js'),'utf8');
const app=fs.readFileSync(path.join(root,'geometry-web/app.js'),'utf8');
const apiSource=app.slice(app.indexOf('async function apiRequest('),app.indexOf('\nfunction setStatus(',app.indexOf('async function apiRequest(')));
const rect=[[0,0],[1000,0],[1000,1000],[0,1000]],other=[[2000,0],[3000,0],[3000,1000],[2000,1000]],sourceId='ab'.repeat(32);
const page={id:'page-a',sourceId,page:1,imgW:100,imgH:80,x:0,y:0,rot:0,mmPerPx:10,crop:[0,0,100,80],opacity:0.5,locked:false,
 calibration:{points:[[0,0],[10,0]],distanceMm:100,inputValue:100,inputUnit:'mm'}};
function fixture({reviewState='needs-review',association='aa'.repeat(32),pin='bb'.repeat(32),present=true,idsReady=true,trace=false}={}){
 const context=()=>({id:'project-a',sources:new Map(),groups:new Map(),models:[],faceProjections:new Map(),reconstructionReviews:new Map(),featureAttachments:[]});
 const history=new P.ContextHistory(context),tokens=new WeakMap();let sequence=0,revision=1,override=null,hold=null;
 const scope=()=>{if(!tokens.has(history.frame))tokens.set(history.frame,'frame-'+(++sequence));return tokens.get(history.frame);};
 const plane=S.fromPage(page,'image/png','plane-a'),room={id:'room-a',name:'Room A',boundaryRef:{kind:'boundary',id:1,associationPin:association},acceptedBasisRevision:1,reviewState};
 const collection={id:'collection-a',planeId:plane.id,roomIds:[room.id]},data={...S.empty(),planes:[plane],collections:[collection],rooms:[room]};S.validate(data);
 history.frame.context.featureAttachments=[P.Features.record('source-rooms',data)];if(present&&idsReady)history.frame.ids.set(1,'incarnation-1');
 const calls=[],writes=[],connection={phase:'ready',session:'session-a'},window=new EventTarget();let renders=0,loads=0;
 const oc={edit:{bid:1},bmap:present?{1:[{verts:rect}]}:{}},nativeRows=present?{1:{ok:true,id:1,geometryFingerprint:pin,loops:[{verts:rect}],revision:1}}:{};
 const state=()=>structuredClone(history.frame.context.featureAttachments.find(r=>r.kind==='source-rooms')?.value||S.empty());
 let workspace;
 const W={history,getProjectState:()=>({id:history.frame.context.id,contextToken:scope(),revision}),
  getModelOperationState:()=>({context:history.frame.context.id,frame:scope(),contextToken:scope()+':'+connection.session,revision,blocked:connection.phase!=='ready',group:!!history.group}),
  active:()=>page,assertEditable(){assert.equal(connection.phase,'ready');},assertAssemblyIdle(){},hasFeatureConfirmation:()=>false,escape:String,sync(){},
  readFeatureAttachment(kind,token){if(token!==undefined)assert.equal(token,scope());return structuredClone(history.frame.context.featureAttachments.find(r=>r.kind===kind)?.value||null);},
  setFeatureAttachment(kind,value,token,options){assert.equal(token,scope());if(value&&kind===D.KIND)D.validate(value);writes.push({kind,value:structuredClone(value),options:structuredClone(options)});history.frame.context.featureAttachments=history.frame.context.featureAttachments.filter(r=>r.kind!==kind);if(value)history.frame.context.featureAttachments.push(P.Features.record(kind,value));revision++;},
  observe(command,result){history.observe(command,result,connection.session);workspace?.observeNativeResult(command,result);if(result.ok&&!result.preview&&/^(line (?!history-|preview|cancel-preview)|drag )/.test(command))revision++;}
 };
 const sandbox={GeometryRoomCandidateDraft:D,GeometrySourcePlane:S,GeometryRoomCollection:R,ReferenceWorkspace:W,structuredClone,crypto:webcrypto,window,oc,connection,
  performance,AbortSignal,CustomEvent,document:{getElementById:()=>null},fe:{draft:{pts:[]}},RoomOutlineWorkspace:{hasWork:false,reset(){},paneHTML:()=>'',collect:async()=>{},loadCandidate(){loads++;}},
  pendingApiResults:new Map(),pendingAssemblyConfirmations:new Map(),acknowledgedApiResults:new Set(),pageRuntimeVersion:'test',checkApiSession(){},
  connectionFailed(message){connection.phase='error';connection.error=message;},renderFaceInspector(){renders++;},drawFaceEditor(){},feSetTool(){},fiShowTab(){},setStatus(){},innerWidth:1000,toast(){},confirm:()=>true,
  feUlImgToMm:(_,x,y)=>[x,y],RoomOutline:{integerProposal:points=>({points,deviation:0}),canonicalLoop:JSON.stringify},
  fetch:async(_,options)=>{
   const command=JSON.parse(options.body).cmd;calls.push(command);
   if(hold&&hold.command===command){const pending=hold;pending.started();await pending.promise;hold=null;}
   const supplied=override?await override(command):null;
   const result=supplied||(/^boundary (\d+)$/.test(command)?structuredClone(nativeRows[Number(command.slice(9))]||{ok:false,error:'BOUNDARY_NOT_FOUND'}):command==='objects'?{ok:true,faces:Object.keys(nativeRows).map(id=>({id:+id,kind:'boundary'})),spaces:[]}:{ok:true});
   return {ok:true,headers:{get:()=>null},json:async()=>result};
  }};
 vm.runInNewContext(apiSource+'\n'+source,sandbox,{filename:'real-app-api-and-room-workspace.js'});workspace=window.RoomCollectionWorkspace;
 workspace.configure({readSource:()=>({meta:{type:'image/png'}}),readIncarnation:(id,t)=>{assert.equal(t,scope());return history.frame.ids.get(id)||null;},beginTransaction(){},assertTransaction(){},endTransaction(){},preflightAttachment(){},groupOpen(){},labelTransaction(){},adoptLegacySource(){}});
 if(trace)installClientTransportTrace(sandbox,()=>{});
 function expected(value){const current=state().rooms[0];return D.roomsPin([{...current,boundaryRef:{id:1,geometryFingerprint:value}}]);}
 function save(value){const draft={schema:D.SCHEMA,draftId:'draft-a',anchor:{kind:'collection',collectionId:collection.id,planeId:plane.id,planePin:D.planePin(plane),roomsPin:expected(value)},
  analysis:{sourceId,page:1,coordinateSpace:'image-pixel/1',pageSize:[100,80],crop:[0,0,100,80],options:{mode:'image',minWidth:1,minLength:8},barriers:[],analyzerRevision:D.ANALYZER_REVISION,total:1,complete:true,ignoredNested:0},
  rows:[{rowKey:'row-1',ordinal:1,method:'image-lines',sourcePoints:other,warnings:[],deviation:0,pointsMm:other,dimensions:[],rawInputs:{refRoomVertices:'2000,0\n3000,0\n3000,1000\n2000,1000',refRoomLength:'',refRoomEdge:'0'},draftRevision:0,status:'pending'}]};W.setFeatureAttachment(D.KIND,draft,scope(),{recordHistory:true});writes.length=0;return draft;}
 function receive(){workspace.receiveCandidates(1,{candidates:[{key:'row-1',points:other,method:'image-lines',warnings:[]}],total:1,complete:true,ignoredNested:0},{mode:'image',minWidth:1,minLength:8,barriers:[]},workspace.captureCandidateStamp(1));}
 function holdNext(command){let release,started;const promise=new Promise(r=>release=r),reached=new Promise(r=>started=r);hold={command,promise,started};return{release,reached};}
 return{workspace,W,history,window,oc,connection,nativeRows,calls,writes,state,expected,save,receive,holdNext,scope,
  get renders(){return renders;},get loads(){return loads;},setOverride:fn=>override=fn,request:(...args)=>sandbox.apiRequest(...args),tick:()=>new Promise(r=>setImmediate(r)),changed:()=>window.dispatchEvent(new Event('project-info-changed'))};
}
test('confirmed association receipt never substitutes for an unread native fingerprint',()=>{
 const f=fixture({reviewState:'confirmed'}),stamp=f.workspace.captureCandidateStamp(1);
 assert.equal(stamp.roomsPin,null);assert.deepEqual(Array.from(stamp.unknownNative),[1]);
});
test('live D3 with no runtime incarnation is unknown, then its native report proves existence',async()=>{
 const f=fixture({idsReady:false}),before=f.workspace.captureCandidateStamp(1);assert.equal(before.roomsPin,null);assert.deepEqual(Array.from(before.unknownNative),[1]);
 await f.request('boundary 1');assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,f.expected(f.nativeRows[1].geometryFingerprint));
});
test('only an authoritative complete objects response proves a missing D3',async()=>{
 const f=fixture({present:false});assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,null);
 await f.request('objects');assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,f.expected(null));
});
test('confirmed stale receipt remains unavailable after a definition change and a failed reread',async()=>{
 const f=fixture({reviewState:'confirmed'});await f.request('boundary 1');f.nativeRows[1].geometryFingerprint='cc'.repeat(32);await f.request('line apply-proj 1 c1');
 assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,null);
 f.setOverride(cmd=>cmd==='boundary 1'?{ok:false,error:'controlled read failure'}:null);await f.request('boundary 1');assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,null);
 f.setOverride(()=>null);await f.request('boundary 1');assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,f.expected('cc'.repeat(32)));
});
test('cold restored draft is pending, then fresh without changing its saved anchor or rows',async()=>{
 const f=fixture({reviewState:'confirmed',idsReady:false}),saved=f.save(f.nativeRows[1].geometryFingerprint);
 f.workspace.paneHTML(1);assert.equal(f.workspace.candidateSnapshot().nativePending,true);assert.equal(f.workspace.candidateSnapshot().stale,false);
 await f.tick();f.workspace.paneHTML(1);assert.equal(f.workspace.candidateSnapshot().nativePending,false);assert.equal(f.workspace.candidateSnapshot().stale,false);
 assert.ok(f.renders>0,'settled native reads must request a real inspector redraw');
 assert.deepEqual(f.W.readFeatureAttachment(D.KIND),saved);assert.equal(f.writes.length,0);
});
test('failed restore read stays blocked and recovers after a later successful native read',async()=>{
 const f=fixture(),saved=f.save(f.nativeRows[1].geometryFingerprint);f.setOverride(cmd=>cmd==='boundary 1'?{ok:false,error:'controlled read failure'}:null);
 f.workspace.paneHTML(1);await f.tick();f.workspace.paneHTML(1);assert.equal(f.workspace.candidateSnapshot().nativePending,true);
 await assert.rejects(f.workspace.selectCandidate(0));assert.deepEqual(f.W.readFeatureAttachment(D.KIND),saved);
 f.setOverride(()=>null);await f.request('boundary 1');f.workspace.paneHTML(1);assert.equal(f.workspace.candidateSnapshot().nativePending,false);assert.equal(f.workspace.candidateSnapshot().stale,false);
});
for(const trace of [false,true])test('stable canvas-pos does not discard an in-flight native read, trace='+trace,async()=>{
 const f=fixture({trace}),gate=f.holdNext('boundary 1'),pending=f.request('boundary 1');await gate.reached;
 await f.request('line canvas-pos boundary 1 10 20');gate.release();await pending;assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,f.expected(f.nativeRows[1].geometryFingerprint));
});
for(const trace of [false,true])test('confirmed preview of another D3 preserves this native pin, trace='+trace,async()=>{
 const f=fixture({trace});await f.request('boundary 1');
 f.setOverride(cmd=>cmd.startsWith('line preview ')?{ok:true,preview:{valid:true,token:7,boundaries:[{id:7,after:{}}]}}:null);
 await f.request('line preview boundary 7 outline 0,0 100,0 100,100 0,100');await f.request('line confirm 7');
 assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,f.expected(f.nativeRows[1].geometryFingerprint));
});
for(const trace of [false,true])test('history-abort preserves reports obtained before the group, trace='+trace,async()=>{
 const f=fixture({trace});await f.request('boundary 1');await f.request('line history-begin');await f.request('line history-abort');
 assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,f.expected(f.nativeRows[1].geometryFingerprint));
});
test('definition-changing command overlapping a read discards that report',async()=>{
 const f=fixture(),gate=f.holdNext('boundary 1'),pending=f.request('boundary 1');await gate.reached;
 await f.request('line apply-proj 1 c1');gate.release();await pending;assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,null);
});
test('native report cannot cross a service session',async()=>{
 const f=fixture();await f.request('boundary 1');f.connection.session='session-b';assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,null);
});
test('native read completing in a replacement project cannot populate its current pin',async()=>{
 const f=fixture(),gate=f.holdNext('boundary 1'),pending=f.request('boundary 1');await gate.reached;
 const replacement=structuredClone(f.history.frame.context);f.history.replace(replacement,new Map([[1,'new-incarnation']]));gate.release();await pending;
 assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,null);
});
test('unrelated drag temporarily blocks live candidates, then recovers from unchanged native geometry',async()=>{
 const f=fixture();await f.request('boundary 1');f.receive();const before=f.workspace.candidateSnapshot();
 await f.request('drag 1 0 5 5');f.changed();assert.equal(f.workspace.candidateSnapshot().nativePending,true);await assert.rejects(f.workspace.selectCandidate(0));
 await f.tick();f.workspace.paneHTML(1);const after=f.workspace.candidateSnapshot();assert.equal(after.stale,false);assert.equal(after.nativePending,false);
 assert.deepEqual(after.anchor,before.anchor);assert.deepEqual(after.candidates,before.candidates);assert.equal(f.writes.length,0);
});
test('changed native geometry stays domain-stale and preserves the persistent anchor',async()=>{
 const f=fixture();await f.request('boundary 1');f.receive();const anchor=f.workspace.candidateSnapshot().anchor;
 f.nativeRows[1].geometryFingerprint='cc'.repeat(32);await f.request('drag 1 0 5 5');f.changed();await f.tick();f.workspace.paneHTML(1);
 assert.equal(f.workspace.candidateSnapshot().stale,true);assert.equal(f.workspace.candidateSnapshot().nativePending,false);assert.deepEqual(f.workspace.candidateSnapshot().anchor,anchor);await assert.rejects(f.workspace.selectCandidate(0));
});
test('an owner rejection before native delivery preserves authority and does not send',async()=>{
 const f=fixture();await f.request('boundary 1');const before=f.workspace.captureCandidateStamp(1).roomsPin;
 f.W.assertAssemblyIdle=()=>{throw Error('owned by another operation');};const result=await f.request('line apply-proj 1 c1');
 assert.equal(result.ok,false);assert.deepEqual(f.calls,['boundary 1']);assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,before);
});
test('local history short circuit does not masquerade as native delivery',async()=>{
 const f=fixture();await f.request('boundary 1');f.W.tryLocalHistory=()=>({ok:true,local:true});await f.request('undo');
 assert.deepEqual(f.calls,['boundary 1']);assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,f.expected(f.nativeRows[1].geometryFingerprint));
});
test('unknown delivery clears authority but a subsequent authoritative read can recover',async()=>{
 const f=fixture();await f.request('boundary 1');f.setOverride(cmd=>{if(cmd==='line apply-proj 1 c1')throw Error('controlled unknown delivery');return null;});
 const result=await f.request('line apply-proj 1 c1');assert.equal(result.transport,true);assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,null);
 f.connection.phase='ready';f.setOverride(()=>null);await f.request('boundary 1');assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,f.expected(f.nativeRows[1].geometryFingerprint));
});
test('definition change in flight makes a previously cached fingerprint unavailable',async()=>{
 const f=fixture();await f.request('boundary 1');const gate=f.holdNext('line apply-proj 1 c1'),pending=f.request('line apply-proj 1 c1');await gate.reached;
 assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,null);gate.release();await pending;assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,null);
});
test('malformed objects response cannot prove absence',async()=>{
 const f=fixture({present:false});f.setOverride(cmd=>cmd==='objects'?{ok:true}:null);await f.request('objects');assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,null);
});
test('revision changing during pending restore cannot be silently adopted by that read',async()=>{
 const f=fixture(),saved=f.save(f.nativeRows[1].geometryFingerprint),gate=f.holdNext('boundary 1');f.workspace.paneHTML(1);await gate.reached;
 const renamed=f.state();renamed.rooms[0].name='Renamed';f.W.setFeatureAttachment('source-rooms',renamed,f.scope(),{recordHistory:true});gate.release();await f.tick();
 assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,null);assert.equal(f.workspace.candidateSnapshot().nativePending,true);
 assert.deepEqual(f.W.readFeatureAttachment(D.KIND),saved);await assert.rejects(f.workspace.selectCandidate(0));
 await f.request('boundary 1');f.workspace.paneHTML(1);assert.equal(f.workspace.candidateSnapshot().stale,false);assert.equal(f.workspace.candidateSnapshot().nativePending,false);
});
for(const action of ['select','park'])test('idle revalidation cannot adopt a new revision for an already-started '+action+' action',async()=>{
 const f=fixture();await f.request('boundary 1');f.receive();
 const pending=action==='select'?f.workspace.selectCandidate(0):f.workspace.parkCandidates();
 const renamed=f.state();renamed.rooms[0].name='Renamed';f.W.setFeatureAttachment('source-rooms',renamed,f.scope(),{recordHistory:true});f.writes.length=0;f.changed();
 await assert.rejects(pending,/專案版本已變更|來源、房間或專案已變更/);
 assert.equal(f.writes.length,0);assert.equal(f.loads,0);assert.equal(f.workspace.candidateSnapshot().active,null);
});
test('unchanged owner can select an idle candidate through the real room controller',async()=>{
 const f=fixture();await f.request('boundary 1');f.receive();await f.workspace.selectCandidate(0);
 assert.equal(f.loads,1);assert.equal(f.workspace.candidateSnapshot().active,0);assert.equal(f.workspace.hasWork,true);
});
test('unchanged owner can park idle candidates as one metadata write',async()=>{
 const f=fixture();await f.request('boundary 1');f.receive();await f.workspace.parkCandidates();
 assert.equal(f.writes.length,1);assert.equal(f.workspace.candidateSnapshot().parked,true);assert.equal(f.workspace.candidateSnapshot().stale,false);
});
test('targeted confirm preserves authoritative absence of an unrelated room but not a new D3',async()=>{
 const f=fixture({present:false,reviewState:'needs-reassociation'});await f.request('objects');
 assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,f.expected(null));
 f.setOverride(cmd=>cmd.startsWith('line preview ')?{ok:true,preview:{valid:true,token:7,boundaries:[{id:7,before:null,after:{}}]}}:null);
 await f.request('line preview boundary 7 outline 0,0 100,0 100,100 0,100');
 f.nativeRows[7]={ok:true,id:7,geometryFingerprint:'cc'.repeat(32),loops:[{verts:rect}]};await f.request('line confirm 7');
 assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,f.expected(null),'unrelated missing room must keep its authoritative null');
 const data=f.state();data.rooms.push({id:'room-7',name:'New',boundaryRef:{kind:'boundary',id:7,associationPin:'cc'.repeat(32)},acceptedBasisRevision:1,reviewState:'confirmed'});data.collections[0].roomIds.push('room-7');
 f.W.setFeatureAttachment('source-rooms',data,f.scope(),{recordHistory:true});
 assert.deepEqual(Array.from(f.workspace.captureCandidateStamp(1).unknownNative),[7],'the old object list cannot prove the newly confirmed id absent');
});
test('an older failed owner check cannot clear a newer authoritative read',async()=>{
 const f=fixture();await f.request('boundary 1');f.receive();const gate=f.holdNext('objects');
 await f.request('drag 1 0 5 5');f.changed();await f.tick();
 assert.ok(f.calls.includes('objects'),'native pin invalidation must request an authoritative objects refresh');
 await gate.reached;
 f.workspace.flushCandidates();await f.request('boundary 1');const current=f.expected(f.nativeRows[1].geometryFingerprint);
 assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,current);gate.release();await f.tick();f.workspace.paneHTML(1);
 assert.equal(f.workspace.captureCandidateStamp(1).roomsPin,current);assert.equal(f.workspace.candidateSnapshot().nativePending,false);assert.equal(f.workspace.candidateSnapshot().stale,false);
});
