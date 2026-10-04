/* Adapter failure regressions: load the real workspace in a VM, with only
 * the shared-owner callbacks and API transport controlled by this fixture.
 * Run: node --test tests/test_issue77_workspace.js
 */
'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {webcrypto} = require('node:crypto');
const S = require('../geometry-web/source-plane.js');
const R = require('../geometry-web/room-collection.js');
const workspaceSource = readFileSync(path.join(__dirname, '../geometry-web/room-collection-workspace.js'), 'utf8');
const clone = value => structuredClone(value);
const outline = [[0,0],[4000,0],[4000,3000],[0,3000]];
const callbacks = ['readSource','readIncarnation','beginTransaction','assertTransaction','endTransaction','groupOpen','labelTransaction','adoptLegacySource'];

function fixture({rejectConfirm = false, rejectMetadata = false, loseAbort = false, rejectAbortKnown = false, rejectCancelKnown = false, existingRoom = false} = {}) {
  const plane = S.fromPage({sourceId:'a'.repeat(64), page:1, imgW:600, imgH:400, x:0, y:0, mmPerPx:20, rot:0,
    calibration:{points:[[50,300],[250,300]],distanceMm:4000,inputValue:4000,inputUnit:'mm'}}, 'application/pdf', 'shared-plane');
  const native = {ok:true, kind:'room_plan', geometryFingerprint:'f'.repeat(64), loops:[{verts:clone(outline),fixity:[1,1,1,1]}]};
  const initial = {...S.empty(), planes:[plane], collections:[{id:'shared-rooms',planeId:plane.id,roomIds:existingRoom ? ['room-a'] : []}],
    rooms:existingRoom ? [{id:'room-a',name:'Room A',boundaryRef:{kind:'boundary',id:1,associationPin:native.geometryFingerprint},acceptedBasisRevision:1,reviewState:'confirmed'}] : []};
  const owner = {attachment:clone(initial), revision:1, lease:null, ended:[], group:false, confirmed:existingRoom,
    requests:[], sources:[], incarnations:[], writes:0, labels:[], expectRecovery:false,blockCancel:rejectCancelKnown};
  const ui={draft:{pts:[]},draftPreview:null,panHold:null,newOutline:null,tool:'select',events:[]};
  let roomWorkspace;
  const connection = {phase:'ready'};
  const workspace = {
    getProjectState:() => ({contextToken:'fixture-context',revision:owner.revision}),
    readFeatureAttachment:(kind, token) => {
      assert.equal(kind,'source-rooms'); assert.equal(token,'fixture-context'); return clone(owner.attachment);
    },
    setFeatureAttachment:(kind, next, token, options) => {
      assert.equal(kind,'source-rooms'); assert.equal(token,'fixture-context');
      assert.equal(options.recordHistory,false); assert.equal(options.roomLease,owner.lease);
      if (rejectMetadata) throw new Error('metadata validator rejected attachment');
      S.validate(next); owner.attachment=clone(next); owner.writes++; owner.revision++;
    },
    assertEditable:() => {assert.equal(owner.lease,null,'ordinary operations cannot bypass an owner transaction');},
    escape:value => String(value),
    preparePage:async (page, source) => {assert.equal(source.id,plane.sourceId);page.src='data:fixture';},
    sync:() => {},
    context:() => {throw new Error('private owner context must not be accessed');},
  };
  Object.defineProperty(workspace,'history',{get() {throw new Error('private owner history must not be accessed');}});
  const integration = {
    readSource:(id, token) => {owner.sources.push([id,token]);return {id};},
    readIncarnation:(id, token) => {owner.incarnations.push([id,token]);return 'native-incarnation-1';},
    beginTransaction:token => {assert.equal(owner.lease,null);assert.equal(token,'fixture-context');return owner.lease={contextToken:token};},
    assertTransaction:lease => {assert.ok(lease);assert.equal(lease,owner.lease);},
    endTransaction:lease => {
      assert.equal(lease,owner.lease);
      if(owner.expectRecovery) {
        assert.equal(roomWorkspace.transactionLease,lease,'UI cleanup must finish before the owner releases the room lease');
        assert.equal(roomWorkspace.hasWork,true,'the settled lease still guards mutations while cleanup completes');
        assert.equal(roomWorkspace.cleaningUI,false,'cleanup protection closes before publishing lease completion');
        assert.equal(ui.draft.pts.length,0);assert.equal(ui.draftPreview,null);
        assert.equal(ui.panHold,null);assert.equal(ui.newOutline,null);assert.equal(ui.tool,'select');
        ui.events.push('owner-end');
      }
      owner.ended.push(lease);owner.lease=null;
    },
    groupOpen:lease => {assert.equal(lease,owner.lease);return owner.group;},
    labelTransaction:(lease,label) => {assert.equal(lease,owner.lease);owner.labels.push(label);},
    adoptLegacySource:() => {throw new Error('source adoption is outside this failure fixture');},
  };
  const apiRequest = async (command, lease) => {
    owner.requests.push(command);
    if (lease) assert.equal(lease,owner.lease);
    if (command==='newid') return {ok:true,boundary:1};
    if (command==='boundary 1') return owner.confirmed ? clone(native) : {ok:false,error:'boundary does not exist'};
    if (command.startsWith('line preview ')) return {ok:true,preview:{valid:true,token:123,
      boundaries:[{id:1,before:owner.confirmed ? {...clone(native),id:1} : null,after:{...clone(native),id:1}}]}};
    if (command==='line cancel-preview') return owner.blockCancel ? {ok:false,error:'cancellation rejected before delivery',stale:true} : {ok:true};
    if (command==='line history-begin') {owner.group=true;return {ok:true};}
    if (command==='line confirm 123') {
      if (rejectConfirm) {if (!rejectAbortKnown) owner.group=false;return {ok:false,error:'preview is stale'};}
      owner.confirmed=true;return {ok:true};
    }
    if (command==='line history-abort') {
      if (rejectAbortKnown) return {ok:false,error:'rollback rejected before delivery',stale:true};
      if (loseAbort) {connection.phase='error';return {ok:false,error:'rollback receipt unavailable',transport:true};}
      owner.group=false;owner.confirmed=existingRoom;return {ok:true};
    }
    if (command==='line history-end') {owner.group=false;return {ok:true};}
    throw new Error('Unexpected API request: '+command);
  };
  const recordUI=stage => {
    if(owner.expectRecovery) {
      assert.ok(owner.lease,'room ownership must remain held throughout editor cleanup');
      assert.equal(roomWorkspace.transactionLease,owner.lease);
      assert.equal(roomWorkspace.cleaningUI,true,'cleanup callbacks run inside the guarded internal cleanup phase');
    }
    ui.events.push(stage);
  };
  const context = {GeometrySourcePlane:S,GeometryRoomCollection:R,ReferenceWorkspace:workspace,apiRequest,connection,
    connectionFailed:message => {connection.phase='error';connection.error=message;},
    crypto:webcrypto,structuredClone,window:{},fe:ui,
    PolyDraft:{createState:()=>({pts:[]})},
    feSyncDraftMirror:()=>recordUI('draft-mirror'),feLenShow:()=>recordUI('length-ui'),
    drawFaceEditor:()=>recordUI('draw'),renderFaceInspector:()=>recordUI('inspector'),
    feSetTool:tool => {
      // This models only the shared UI patch's pending-room guard. It does not
      // implement recovery or Controller behavior; the loaded workspace does.
      if(roomWorkspace.hasWork && !roomWorkspace.cleaningUI && tool!=='redraw') return false;
      recordUI('tool:'+tool);ui.tool=tool;return true;
    }};
  vm.runInNewContext(workspaceSource,context,{filename:'room-collection-workspace.js'});
  roomWorkspace=context.window.RoomCollectionWorkspace;
  roomWorkspace.configure(integration);
  return {owner,connection,integration,roomWorkspace,initial,ui,context};
}

async function preview(f) {
  const controller=f.roomWorkspace.controller;
  controller.beginNew('shared-rooms');await controller.prepare(outline,'Room A');
  assert.ok(f.roomWorkspace.transactionLease);return controller;
}

test('known native confirmation rejection can be cancelled and a fresh room can begin', async () => {
  const f=fixture({rejectConfirm:true}), controller=await preview(f);
  await assert.rejects(controller.confirm(),/preview is stale/);
  assert.equal(controller.preview,null,'the rejected native candidate is retired');
  assert.equal(f.roomWorkspace.transactionLease,null);
  await controller.cancel();assert.equal(f.roomWorkspace.hasWork,false);
  assert.deepEqual(f.owner.attachment,f.initial);assert.equal(f.owner.confirmed,false);assert.equal(f.owner.group,false);
  controller.beginNew('shared-rooms');await controller.cancel();assert.equal(f.roomWorkspace.hasWork,false);
});

test('known metadata rejection rolls back native work and leaves a cancellable draft', async () => {
  const f=fixture({rejectMetadata:true}), controller=await preview(f);
  await assert.rejects(controller.confirm(),/metadata validator rejected/);
  assert.equal(f.owner.requests.includes('line history-abort'),true);
  assert.equal(f.owner.confirmed,false);assert.equal(f.owner.group,false);assert.equal(f.owner.writes,0);
  assert.deepEqual(f.owner.attachment,f.initial);assert.equal(f.roomWorkspace.transactionLease,null);
  await controller.cancel();assert.equal(f.roomWorkspace.hasWork,false);
});

test('a lost rollback reply retains the owner lease until receipt recovery settles the group', async () => {
  const f=fixture({rejectMetadata:true,loseAbort:true}), controller=await preview(f), lease=f.roomWorkspace.transactionLease;
  await assert.rejects(controller.confirm(),error => error.transport===true && /rollback receipt unavailable/.test(error.message));
  assert.equal(f.owner.confirmed,true,'the fixture leaves the native outcome unresolved');
  assert.equal(f.owner.group,true);assert.equal(f.owner.writes,0);assert.deepEqual(f.owner.attachment,f.initial);
  assert.equal(f.roomWorkspace.transactionLease,lease,'unknown rollback cannot release mutation ownership');
  assert.equal(f.owner.ended.length,0);assert.equal(f.roomWorkspace.busy,true);assert.equal(controller.preview.token,123);
  f.ui.draft={pts:clone(outline)};f.ui.draftPreview={token:123};f.ui.panHold={pts:clone(outline)};f.ui.newOutline=clone(outline);f.ui.tool='redraw';
  assert.equal(f.context.feSetTool('select'),false,'ordinary tool changes cannot bypass the unresolved room lease');
  assert.equal(f.ui.tool,'redraw');assert.equal(f.ui.draft.pts.length,4);
  // The external receipt recovery owns settlement; only then may the workspace release its lease.
  f.owner.group=false;f.owner.confirmed=false;f.connection.phase='ready';
  f.owner.expectRecovery=true;
  f.roomWorkspace.recoveredTransaction();assert.equal(f.roomWorkspace.transactionLease,null);assert.equal(f.roomWorkspace.hasWork,false);
  assert.deepEqual(f.owner.ended,[lease]);
  assert.deepEqual(f.ui.events,['draft-mirror','length-ui','draw','tool:select','inspector','owner-end']);
  assert.notEqual(f.roomWorkspace.controller,controller,'the settled operation retires its previous controller');
  assert.equal(f.roomWorkspace.controller.intent,null);assert.equal(f.roomWorkspace.controller.preview,null);
  f.roomWorkspace.controller.beginNew('shared-rooms');await f.roomWorkspace.controller.cancel();
});

test('a known rollback rejection retains an open native group and exposes receipt recovery', async () => {
  const f=fixture({rejectConfirm:true,rejectAbortKnown:true}), controller=await preview(f), lease=f.roomWorkspace.transactionLease;
  await assert.rejects(controller.confirm(),error => error.transport===true && /rollback rejected before delivery/.test(error.message));
  assert.equal(f.owner.group,true,'a rejection before delivery cannot close the native transaction');
  assert.equal(f.connection.phase,'error','the existing connection retry becomes available');
  assert.match(f.connection.error,/房間交易尚未回復/);
  assert.equal(controller.preview.token,123,'the owned candidate remains guarded until native rollback is confirmed');
  assert.equal(f.roomWorkspace.transactionLease,lease);assert.equal(f.roomWorkspace.busy,true);
  assert.equal(f.owner.ended.length,0);assert.deepEqual(f.owner.attachment,f.initial);
  // Receipt recovery performs the real abort externally; this VM checks only
  // that its confirmed outcome is the prerequisite for owner/UI cleanup.
  f.owner.group=false;f.connection.phase='ready';
  f.roomWorkspace.observeNativeResult('line history-abort',{ok:true});
  f.owner.expectRecovery=true;await f.roomWorkspace.settleRecoveredTransaction();
  assert.equal(f.roomWorkspace.transactionLease,null);assert.equal(f.roomWorkspace.hasWork,false);
  assert.deepEqual(f.owner.ended,[lease]);assert.deepEqual(f.owner.attachment,f.initial);
});

test('a known cancellation rejection retains the candidate lease and exposes recovery without inventing a receipt', async () => {
  const f=fixture({rejectCancelKnown:true}),controller=await preview(f),lease=f.roomWorkspace.transactionLease;
  await assert.rejects(controller.cancel(),error=>error.transport===true && /cancellation rejected before delivery/.test(error.message));
  assert.equal(f.connection.phase,'error');assert.equal(controller.preview.token,123);
  assert.equal(f.roomWorkspace.transactionLease,lease);assert.equal(f.roomWorkspace.busy,true);assert.equal(f.owner.group,false);
  assert.equal(f.owner.ended.length,0);assert.deepEqual(f.owner.attachment,f.initial);
  f.owner.blockCancel=false;f.connection.phase='loading';f.owner.expectRecovery=true;
  await f.roomWorkspace.settleRecoveredTransaction();
  assert.equal(f.roomWorkspace.transactionLease,null);assert.equal(f.roomWorkspace.hasWork,false);
  assert.deepEqual(f.owner.ended,[lease]);assert.deepEqual(f.owner.attachment,f.initial);
  assert.equal(f.owner.requests.filter(command=>command==='line cancel-preview').length,2,'retry cancels once after the first request was rejected before delivery');
});

test('receipt recovery clears draft candidate and redraw while lease ownership still blocks other operations', async () => {
  const f=fixture(), controller=await preview(f), lease=f.roomWorkspace.transactionLease;
  f.ui.draft={pts:clone(outline)};f.ui.draftPreview={token:123};f.ui.panHold={pts:clone(outline)};f.ui.newOutline=clone(outline);f.ui.tool='redraw';
  f.owner.expectRecovery=true;
  const requests=f.owner.requests.length;
  f.roomWorkspace.recoveredTransaction();
  assert.deepEqual(f.ui.events,['draft-mirror','length-ui','draw','tool:select','inspector','owner-end']);
  assert.equal(f.owner.requests.length,requests,'settled receipt cleanup does not cancel a possibly newer native candidate');
  assert.deepEqual(f.owner.ended,[lease]);assert.equal(f.roomWorkspace.hasWork,false);assert.equal(f.roomWorkspace.busy,false);
  assert.equal(f.roomWorkspace.cleaningUI,false);assert.equal(f.roomWorkspace.dialogOpen,false);
  assert.notEqual(f.roomWorkspace.controller,controller);assert.equal(f.roomWorkspace.controller.intent,null);
  assert.deepEqual(f.owner.attachment,f.initial);assert.equal(f.owner.writes,0);
});

test('configure rejects each missing owner callback before replacing the integration adapter', () => {
  const f=fixture();
  for (const callback of callbacks) {
    const incomplete={...f.integration};delete incomplete[callback];
    assert.throws(() => f.roomWorkspace.configure(incomplete),new RegExp(callback));
  }
  assert.doesNotThrow(() => f.roomWorkspace.controller.beginNew('shared-rooms'));
});

test('shared rendering and native identity use configured callbacks without private context or history access', async () => {
  const f=fixture({existingRoom:true}), page=f.roomWorkspace.sourcePage(1);
  assert.equal(page.sourceId,'a'.repeat(64));assert.equal(page.mmPerPx,20);
  await f.roomWorkspace.prepareSharedPages();assert.equal(page.src,'data:fixture');
  assert.deepEqual(f.owner.sources,[['a'.repeat(64),'fixture-context']]);
  assert.match(f.roomWorkspace.paneHTML(1),/Room A/);
  f.roomWorkspace.controller.beginEdit('shared-rooms','room-a');
  assert.deepEqual(f.owner.incarnations,[[1,'fixture-context']]);await f.roomWorkspace.controller.cancel();
});
