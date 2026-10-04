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

function fixture({rejectConfirm = false, rejectMetadata = false, loseAbort = false, existingRoom = false} = {}) {
  const plane = S.fromPage({sourceId:'a'.repeat(64), page:1, imgW:600, imgH:400, x:0, y:0, mmPerPx:20, rot:0,
    calibration:{points:[[50,300],[250,300]],distanceMm:4000,inputValue:4000,inputUnit:'mm'}}, 'application/pdf', 'shared-plane');
  const native = {ok:true, kind:'room_plan', geometryFingerprint:'f'.repeat(64), loops:[{verts:clone(outline),fixity:[1,1,1,1]}]};
  const initial = {...S.empty(), planes:[plane], collections:[{id:'shared-rooms',planeId:plane.id,roomIds:existingRoom ? ['room-a'] : []}],
    rooms:existingRoom ? [{id:'room-a',name:'Room A',boundaryRef:{kind:'boundary',id:1,associationPin:native.geometryFingerprint},acceptedBasisRevision:1,reviewState:'confirmed'}] : []};
  const owner = {attachment:clone(initial), revision:1, lease:null, ended:[], group:false, confirmed:existingRoom,
    requests:[], sources:[], incarnations:[], writes:0, labels:[]};
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
    endTransaction:lease => {assert.equal(lease,owner.lease);owner.ended.push(lease);owner.lease=null;},
    groupOpen:lease => {assert.equal(lease,owner.lease);return owner.group;},
    labelTransaction:(lease,label) => {assert.equal(lease,owner.lease);owner.labels.push(label);},
    adoptLegacySource:() => {throw new Error('source adoption is outside this failure fixture');},
  };
  const apiRequest = async (command, lease) => {
    owner.requests.push(command);
    if (lease) assert.equal(lease,owner.lease);
    if (command==='newid') return {ok:true,boundary:1};
    if (command==='boundary 1') return owner.confirmed ? clone(native) : {ok:false,error:'boundary does not exist'};
    if (command.startsWith('line preview ')) return {ok:true,preview:{valid:true,token:123}};
    if (command==='line cancel-preview') return {ok:true};
    if (command==='line history-begin') {owner.group=true;return {ok:true};}
    if (command==='line confirm 123') {
      if (rejectConfirm) {owner.group=false;return {ok:false,error:'preview is stale'};}
      owner.confirmed=true;return {ok:true};
    }
    if (command==='line history-abort') {
      if (loseAbort) {connection.phase='error';return {ok:false,error:'rollback receipt unavailable',transport:true};}
      owner.group=false;owner.confirmed=existingRoom;return {ok:true};
    }
    if (command==='line history-end') {owner.group=false;return {ok:true};}
    throw new Error('Unexpected API request: '+command);
  };
  const context = {GeometrySourcePlane:S,GeometryRoomCollection:R,ReferenceWorkspace:workspace,apiRequest,connection,
    crypto:webcrypto,structuredClone,window:{}};
  vm.runInNewContext(workspaceSource,context,{filename:'room-collection-workspace.js'});
  const roomWorkspace=context.window.RoomCollectionWorkspace;
  roomWorkspace.configure(integration);
  return {owner,connection,integration,roomWorkspace,initial};
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
  // The external receipt recovery owns settlement; only then may the workspace release its lease.
  f.owner.group=false;f.owner.confirmed=false;f.connection.phase='ready';
  f.roomWorkspace.recoveredTransaction();assert.equal(f.roomWorkspace.transactionLease,null);assert.equal(f.roomWorkspace.hasWork,false);
  assert.deepEqual(f.owner.ended,[lease]);
  f.roomWorkspace.controller.beginNew('shared-rooms');await f.roomWorkspace.controller.cancel();
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
