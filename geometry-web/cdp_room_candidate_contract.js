/* Independent R358 browser oracles and a deterministic two-room image fixture.
 * These helpers do not call product draft/pin constructors or change the page.
 */
'use strict';
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const SECTION='P358';
const ASSERTION_NAMES=Object.freeze([
 'TWO_CANDIDATES','BASELINE_FILE','PENDING_BASELINE','GROUPED_ACCEPTANCE',
 'IMMEDIATE_SAVE_FILE','SAVE_NO_REPAIR','ARCHIVE_EXACT','ONE_ACCEPTANCE_STEP',
 'COLD_OWNERSHIP','COLD_ARCHIVE_EXACT','COLD_ANCHOR_FRESH','SECOND_RESELECT',
 'SECOND_REVIEW','UNDO_ATOMIC','REDO_ATOMIC','NO_EXCEPTIONS',
]);
const EXPECTED_SOURCE_LOOPS=Object.freeze([[[32,32],[138,32],[138,158],[32,158]],[[182,32],[288,32],[288,158],[182,158]]]);
function fixturePixels(){
 const width=320,height=200,data=new Uint8ClampedArray(width*height*4);data.fill(255);
 for(const [left,top,right,bottom] of [[28,28,142,162],[178,28,292,162]])
  for(let y=top;y<bottom;y++)for(let x=left;x<right;x++)
   if(x<left+4||x>=right-4||y<top+4||y>=bottom-4){const at=(y*width+x)*4;data[at]=data[at+1]=data[at+2]=0;}
 return {width,height,data};
}
const pin=value=>crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex');
function expectedAnchor(data,native){
 assert.equal(data.collections.length,1);assert.equal(data.planes.length,1);
 const collection=data.collections[0],plane=data.planes[0],c=plane.calibration,a=plane.alignment;
 assert.equal(collection.planeId,plane.id);
 const byId=new Map(native.map(row=>[row.id,row]));
 const planePin=pin([plane.id,plane.sourceId,plane.page,plane.coordinateSpace,plane.pageSize,
  c===null?null:[c.points,c.distanceMm,c.inputValue,c.inputUnit],[a.x,a.y,a.mmPerPx,a.rotation],plane.basisRevision]);
 const roomsPin=pin(collection.roomIds.map(id=>{
  const room=data.rooms.find(row=>row.id===id);assert.ok(room);
  const boundary=byId.get(room.boundaryRef.id);assert.ok(boundary);
  assert.match(boundary.geometryFingerprint,/^[a-f0-9]{64}$/);
  return [room.id,room.boundaryRef.id,boundary.geometryFingerprint,room.acceptedBasisRevision,room.reviewState];
 }));
 return {kind:'collection',collectionId:collection.id,planeId:plane.id,planePin,roomsPin};
}
function acceptedSnapshot(before,after){
 assert.equal(before.rooms,null);assert.equal(before.draft.anchor.kind,'page');
 assert.equal(before.draft.rows.length,2);assert.ok(before.draft.rows.every(row=>row.status==='pending'&&!Object.hasOwn(row,'roomId')));
 assert.equal(after.rooms.rooms.length,1);assert.equal(after.rooms.collections.length,1);assert.equal(after.rooms.planes.length,1);
 const room=after.rooms.rooms[0];assert.notEqual(room.boundaryRef.id,1);
 assert.equal(after.native.length,2);assert.deepEqual(after.native.map(row=>row.id).sort((a,b)=>a-b),[1,room.boundaryRef.id].sort((a,b)=>a-b));
 assert.equal(room.reviewState,'confirmed');assert.equal(room.acceptedBasisRevision,1);assert.equal(after.rooms.planes[0].basisRevision,1);
 assert.equal(room.boundaryRef.associationPin,after.native.find(row=>row.id===room.boundaryRef.id).geometryFingerprint);
 assert.equal(after.draft.rows.length,2);assert.equal(after.draft.rows[0].status,'accepted');
 assert.equal(after.draft.rows[0].roomId,room.id);assert.equal(after.draft.rows[1].status,'pending');
 assert.equal(Object.hasOwn(after.draft.rows[1],'roomId'),false);
 assert.deepEqual(after.draft.anchor,expectedAnchor(after.rooms,after.native));
 assert.deepEqual(after.draft.rows[1],before.draft.rows[1]);
 assert.deepEqual(after.hostPage,before.hostPage);assert.deepEqual(after.sourceIds,before.sourceIds);
 assert.deepEqual(after.native.find(row=>row.id===1),before.native.find(row=>row.id===1));
 assert.equal(after.session.stale,false);assert.equal(after.session.expired,false);assert.equal(after.session.active,null);
 assert.equal(!!after.session.nativePending,false);
 assert.ok(after.session.candidates.every(row=>row.reviewed===false));
 return true;
}
function savedState(snapshot){
 return {projectId:snapshot.projectId,scene:snapshot.scene,rooms:snapshot.rooms,draft:snapshot.draft,
  native:snapshot.native,hostPage:snapshot.hostPage,sourceIds:snapshot.sourceIds};
}
function archiveMatches(loaded,snapshot){
 assert.equal(loaded.manifest.projectId,snapshot.projectId);assert.equal(loaded.scene,snapshot.scene);
 const records=loaded.manifest.featureAttachments.records;
 assert.deepEqual(records.find(row=>row.kind==='source-rooms').value,snapshot.rooms);
 assert.deepEqual(records.find(row=>row.kind==='room-candidates').value,snapshot.draft);
 assert.deepEqual(loaded.manifest.sources.map(row=>row.hash).sort(),snapshot.sourceIds);
 assert.equal(loaded.sources.size,snapshot.sourceIds.length);
 for(const id of snapshot.sourceIds){
  const bytes=loaded.sources.get(id);assert.ok(bytes instanceof Uint8Array);
  assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),id);
 }
 return true;
}
function coldOwnership(info,sourceProfile){
 assert.equal(info.sourceRuntime.fresh,true);assert.equal(info.service.fresh,true);
 assert.notEqual(info.service.session,info.sourceRuntime.session);assert.notEqual(info.service.pid,info.sourceRuntime.pid);
 assert.equal(info.service.root,info.sourceRuntime.root);assert.equal(info.service.version,info.sourceRuntime.version);
 assert.equal(info.bridge.state,'fresh');assert.ok(Number.isInteger(info.browserPid)&&info.browserPid>0);
 assert.ok(typeof sourceProfile==='string'&&sourceProfile.length>0);
 assert.ok(typeof info.profile==='string'&&info.profile.length>0);assert.notEqual(info.profile,sourceProfile);
 return true;
}
module.exports={SECTION,ASSERTION_NAMES,EXPECTED_SOURCE_LOOPS,fixturePixels,expectedAnchor,acceptedSnapshot,savedState,archiveMatches,coldOwnership};
