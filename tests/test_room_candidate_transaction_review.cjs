/* Independent review probe; executes unchanged workspace/controller modules in Node VM.
 * This is NOT a browser/native E2E. DOM, native protocol, and owner contract are fakes.
 * Product files are read directly from GEOMETRY_ROOM_WORKSPACE_ROOT or ../geometry-web.
 */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const base=(process.env.GEOMETRY_ROOM_WORKSPACE_ROOT||require('node:path').resolve(__dirname,'../geometry-web'))+'/';
const S=require(base+'source-plane.js'),R=require(base+'room-collection.js'),D=require(base+'room-candidate-draft.js'),O=require(base+'room-outline.js'),E=require(base+'evidence-links.js');
const clone=x=>structuredClone(x),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const source='ab'.repeat(32),pin='cd'.repeat(32),hostLoop={verts:[[0,0],[3000,0],[3000,2000],[0,2000]],fixity:[1,1,1,1]};
const page={id:'page-a',sourceId:source,page:1,imgW:100,imgH:80,mmPerPx:10,x:0,y:0,rot:0,opacity:.5,locked:false,crop:[0,0,100,80],records:[],
  calibration:{points:[[10,5],[90,5]],distanceMm:800,inputValue:800,inputUnit:'mm'}};
function harness(options={}) {
  let serial=0,revision=0,dirty=false,snapshot=null,ownedLease=null,outline=null,workspace;
  const attachments=clone(options.attachments||{}),native=clone(options.native||{1:{id:1,kind:'unspecified',geometryFingerprint:pin,loops:[hostLoop]}});
  const history={group:null,undo:[],redo:[]},writes=[],commands=[],events={};
  const oc={edit:{bid:options.bid||1},bmap:Object.fromEntries(Object.entries(native).map(([k,v])=>[k,clone(v.loops)])),focus:null};
  const fe={draft:{pts:[]},zoom:1};
  const getProjectState=()=>({id:'project-a',contextToken:'ctx',revision,dirty,saved:true});
  const modelState=()=>({context:'context-a',frame:'frame-a',revision,contextToken:'ctx:session-a',undo:history.undo.length?'undo-'+history.undo.length:null,redo:null,group:history.group?'group-a':null,blocked:!!history.group});
  const restore=state=>{for(const k of Object.keys(attachments))delete attachments[k];Object.assign(attachments,clone(state.attachments));for(const k of Object.keys(native))delete native[k];Object.assign(native,clone(state.native));oc.bmap=clone(state.bmap);revision=state.revision;dirty=state.dirty;};
  const capture=()=>clone({attachments,native,bmap:oc.bmap,revision,dirty});
  const integration={readSource:()=>({meta:{type:'image/png',hash:source}}),readIncarnation:id=>native[id]?'inc-'+id:null,
    beginTransaction:()=>{assert.equal(ownedLease,null);ownedLease=Object.freeze({contextToken:'ctx'});return ownedLease;},
    assertTransaction:l=>assert.equal(l,ownedLease),endTransaction:l=>{assert.equal(l,ownedLease);assert.equal(history.group,null);ownedLease=null;},
    preflightAttachment:(value,l)=>{assert.equal(l,ownedLease);S.validate(value);},groupOpen:l=>{assert.equal(l,ownedLease);return !!history.group;},
    labelTransaction:(l,label)=>{assert.equal(l,ownedLease);if(options.fail==='label')throw Error('injected label failure');history.undo.at(-1).label=label;},adoptLegacySource:()=>{throw Error('unused');}};
  const W={getProjectState,getModelOperationState:modelState,history,escape:String,
    active:bid=>workspace?.sourcePage(bid)||(bid===1?page:null),readFeatureAttachment:kind=>clone(attachments[kind]||null),
    setFeatureAttachment:(kind,value,token,opts={})=>{assert.equal(token,'ctx');if(opts.recordHistory===false){assert.equal(opts.roomLease,ownedLease);assert.ok(history.group?.dirty);}if(kind==='source-rooms')S.validate(value);else if(kind===D.KIND&&value!==null)D.validate(value);else if(kind===E.KIND&&value!==null)E.validate(value);
      if(options.fail==='draft-write'&&kind===D.KIND&&opts.recordHistory===false)throw Error('injected draft write failure');
      writes.push({kind,value:clone(value),group:!!history.group});if(value===null)delete attachments[kind];else attachments[kind]=clone(value);revision++;dirty=true;},
    assertEditable:()=>{assert.equal(history.group,null);},preparePage:async p=>{p.src='fixture';},sync:()=>{},getRoomIntegration:()=>integration};
  const outlineWorkspace={get hasWork(){return !!outline;},loadCandidate:(bid,row)=>{outline={candidateId:row.id,points:clone(row.points),dimensions:clone(row.dimensions),rawInputs:clone(row.rawInputs),revision:row.revision};},
    snapshot:()=>clone(outline),beforeCommit:()=>({...clone(outline),collectionCandidate:true}),reset:()=>{outline=null;},afterCommit:()=>{},paneHTML:()=>''};
  function element(tag){return {tag,children:[],append(...x){this.children.push(...x);},addEventListener(){},close(){this.open=false;},remove(){},focus(){},showModal(){this.open=true;queueMicrotask(()=>this.children.find(x=>x.id==='roomConfirm').onclick());}};}
  const context={GeometrySourcePlane:S,GeometryRoomCollection:R,GeometryRoomCandidateDraft:D,RoomOutline:O,RoomOutlineWorkspace:outlineWorkspace,ReferenceWorkspace:W,
    structuredClone,TextEncoder,PolyDraft:{createState:()=>({pts:[]})},feSyncDraftMirror:()=>{},feLenShow:()=>{},crypto:{randomUUID:()=>`id-${++serial}`},console,window:{addEventListener:(n,f)=>{events[n]=f;}},document:{createElement:element,body:{append(){}},getElementById:()=>null},
    oc,fe,connection:{phase:'ready',session:'session-a'},innerWidth:1000,prompt:()=> 'Probe room',appendGridDefinitionImpact:()=>{},
    feUlImgToMm:(_p,x,y)=>[x*10,y*10],feSetTool:()=>{},fiShowTab:()=>{},openPanel:()=>{},drawFaceEditor:()=>{},setStatus:()=>{},toast:()=>{},
    cleanDraft:()=>{fe.draft.pts=[];},renderObjects:async()=>{if(options.tamperOldCollection){const changed=clone(attachments['source-rooms']);changed.collections.find(c=>c.id==='other-collection').roomIds.reverse();W.setFeatureAttachment('source-rooms',changed,'ctx',{recordHistory:true});}if(options.tamperOther)W.setFeatureAttachment(E.KIND,E.empty(),'ctx',{recordHistory:true});if(options.tamperDraft){const changed=clone(attachments[D.KIND]);changed.rows[1].rawInputs.refRoomLength='999';W.setFeatureAttachment(D.KIND,changed,'ctx',{recordHistory:true});}},
    enterFocus:async(t,id)=>{oc.edit={bid:id};oc.focus={t,id};},renderFaceInspector:()=>{if(workspace&&oc.edit)workspace.paneHTML(oc.edit.bid);},
    apiRequest:async(command,l)=>{commands.push(command);let result;
      if(command==='newid')result={ok:true,boundary:2};
      else if(command.startsWith('boundary ')){const id=Number(command.split(' ')[1]);result=native[id]?{ok:true,...clone(native[id])}:{ok:false,error:'missing'};}
      else if(command.startsWith('line preview boundary ')){const id=Number(command.split(' ')[3]),points=command.split(' outline ')[1].split(' ').map(p=>p.split(',').map(Number));snapshot={id,kind:'unspecified',geometryFingerprint:'ef'.repeat(32),loops:[{verts:points,fixity:points.map(()=>1)}]};result={ok:true,preview:{valid:true,token:7,boundaries:[{id,before:null,after:clone(snapshot)}]}};}
      else if(command==='line history-begin'){history.group={base:capture(),dirty:false};result={ok:true};}
      else if(command==='line confirm 7'){native[2]=clone(snapshot);oc.bmap[2]=clone(snapshot.loops);history.group.dirty=true;result={ok:true};}
      else if(command==='line history-end'){if(options.fail==='history-end-unknown')result={ok:false,transport:true,error:'injected unknown history-end'};else if(options.fail==='history-end')result={ok:false,error:'injected history-end failure'};else {history.undo.push({before:history.group.base,after:capture()});history.group=null;result={ok:true};}}
      else if(command==='line history-abort'){restore(history.group.base);history.group=null;result={ok:true};}
      else if(command==='line cancel-preview'){snapshot=null;result={ok:true};}
      else throw Error('unexpected command '+command);
      workspace?.observeNativeResult(command,result);return result;
    }};
  context.window.RoomCollectionWorkspace=undefined;vm.createContext(context);vm.runInContext(fs.readFileSync(base+'room-collection-workspace.js','utf8'),context,{filename:'room-collection-workspace.js'});workspace=context.window.RoomCollectionWorkspace;
  async function start(){const bid=oc.edit.bid;workspace.receiveCandidates(bid,{candidates:[{key:'a',points:[[10,10],[30,10],[30,30],[10,30]],method:'image-lines',warnings:[]},{key:'b',points:[[40,10],[60,10],[60,30],[40,30]],method:'image-lines',warnings:[]}],total:2,complete:true,ignoredNested:0},{mode:'image',minWidth:1,minLength:8},workspace.captureCandidateStamp(bid));workspace.flushCandidates();await workspace.selectCandidate(0);}
  async function commit(){return workspace.commitDraft(outline.points);}
  function undo(){const entry=history.undo.pop();assert.ok(entry);restore(entry.before);history.redo.push(entry);}
  return {workspace,attachments,native,history,writes,commands,oc,start,commit,undo,capture,get lease(){return ownedLease;}};
}

const {test}=require('node:test');
test('R358-06 first-room commit persists collection anchor and reopens fresh',async()=>{
  const h=harness();await h.start();await h.commit();
  assert.equal(h.attachments[D.KIND].anchor.kind,'collection','same-group persisted anchor must use newly created collection');
  const reopened=harness({attachments:h.attachments,native:h.native});reopened.workspace.paneHTML(1);
  assert.equal(reopened.workspace.candidateSnapshot().stale,false,'unchanged cold reopen must keep remaining rows fresh');
});
test('R358-06 existing-collection commit persists current roomsPin and reopens fresh',async()=>{
  const initial=S.upgradeDisplay(S.empty()),plane=S.fromPage(page,'image/png','existing-plane');
  initial.planes.push(plane);initial.collections.push({id:'existing-collection',planeId:plane.id,roomIds:['existing-room']});
  initial.rooms.push({id:'existing-room',name:'Existing',boundaryRef:{kind:'boundary',id:1,associationPin:pin},acceptedBasisRevision:1,reviewState:'confirmed',display:{crop:page.crop,opacity:page.opacity,locked:false}});S.validate(initial);
  const h=harness({attachments:{'source-rooms':initial}});await h.start();await h.commit();
  assert.equal(h.attachments[D.KIND].anchor.roomsPin,h.workspace.candidateSnapshot().stamp.roomsPin,'same-group persisted pin must include the accepted room');
  const reopened=harness({attachments:h.attachments,native:h.native});reopened.workspace.paneHTML(1);
  assert.equal(reopened.workspace.candidateSnapshot().stale,false);
});
test('R358-06 control: draft attachment rejection rolls World and draft back',async()=>{
  const h=harness({fail:'draft-write'});await h.start();const before=h.capture();
  await assert.rejects(h.commit(),/injected draft write failure/);
  assert.equal(same(h.capture(),before),true);assert.equal(h.workspace.candidateSnapshot().candidates[0].status,'pending');
  assert.equal(h.workspace.candidateSnapshot().candidates[0].roomId,undefined);assert.equal(h.lease,null);assert.equal(h.history.group,null);
  assert.ok(h.commands.includes('line history-abort'));assert.equal(h.history.undo.length,0);
});
test('R358-06 history-end rejection also rolls live acceptance back before save',async()=>{
  const h=harness({fail:'history-end'});await h.start();const before=h.capture();
  await assert.rejects(h.commit(),/injected history-end failure/);assert.equal(same(h.capture(),before),true);
  assert.equal(h.workspace.candidateSnapshot().candidates[0].status,'pending','aborted row must not claim an accepted room');
  assert.equal(h.workspace.candidateSnapshot().candidates[0].roomId,undefined);
  h.workspace.flushCandidates();assert.equal(h.attachments[D.KIND].rows[0].status,'pending');
  assert.equal(h.attachments[D.KIND].rows[0].roomId,undefined);assert.equal(h.attachments[D.KIND].anchor.kind,'page');
});
test('R358-06 continuation rejects any changed other attachment',async()=>{
  const h=harness({tamperOther:true});await h.start();await h.commit().catch(()=>{});
  assert.equal(h.workspace.candidateSnapshot().stale,true,'evidence-links changed after group, so no automatic continuation');
});
test('R358-06 continuation verifies candidate attachment equals grouped write',async()=>{
  const h=harness({tamperDraft:true});await h.start();await h.commit().catch(()=>{});
  assert.equal(h.workspace.candidateSnapshot().stale,true,'candidate persisted value changed after group, so no automatic continuation');
});


function withOtherCollection(tamperOldCollection=false) {
  const initial=S.upgradeDisplay(S.empty());
  const otherPage={...page,id:'other-page',sourceId:'12'.repeat(32)};
  initial.planes.push(S.fromPage(otherPage,'image/png','other-plane'));
  initial.collections.push({id:'other-collection',planeId:'other-plane',roomIds:['other-room-3','other-room-4']});
  for(const id of [3,4])initial.rooms.push({id:'other-room-'+id,name:'Other '+id,
    boundaryRef:{kind:'boundary',id,associationPin:pin},acceptedBasisRevision:1,reviewState:'confirmed',
    display:{crop:page.crop,opacity:page.opacity,locked:false}});
  S.validate(initial);
  const native=Object.fromEntries([1,3,4].map(id=>[id,{id,kind:'unspecified',geometryFingerprint:pin,loops:[hostLoop]}]));
  return harness({attachments:{'source-rooms':initial},native,tamperOldCollection});
}
test('R358-06 extra control: unrelated collection remains exact and first-room continuation succeeds',async()=>{
  const h=withOtherCollection();
  assert.equal(h.workspace.captureCandidateStamp(1).kind,'page');
  await h.start();assert.equal(await h.commit(),true);
  assert.equal(h.workspace.candidateSnapshot().stale,false);
  assert.deepEqual(h.attachments['source-rooms'].collections.find(c=>c.id==='other-collection').roomIds,['other-room-3','other-room-4']);
});
test('R358-06 extra unknown history-end expires live work and prevents later flush',async()=>{
  const h=harness({fail:'history-end-unknown'});await h.start();
  await assert.rejects(h.commit(),/injected unknown history-end/);
  const s=h.workspace.candidateSnapshot();assert.equal(s.stale,true);assert.equal(s.expired,true);
  assert.notEqual(h.lease,null);const before=h.capture(),writes=h.writes.length;
  h.workspace.flushCandidates();assert.equal(same(h.capture(),before),true);assert.equal(h.writes.length,writes);
});
test('R358-06 extra R52: changed pre-existing collection prevents first-room continuation',async()=>{
  const h=withOtherCollection(true);await h.start();
  await h.commit().catch(()=>{});
  assert.deepEqual(h.attachments['source-rooms'].collections.find(c=>c.id==='other-collection').roomIds,['other-room-4','other-room-3']);
  assert.equal(h.workspace.candidateSnapshot().stale,true,'R52 must reject continuation when a pre-existing collection changed');
});
