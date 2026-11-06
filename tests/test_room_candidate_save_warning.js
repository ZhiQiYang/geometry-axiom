/* Main R07 increment kept separate so the existing node:tests-js count remains unchanged. */
const {test:nodeTest}=require('node:test');
const test=(name,fn,options={})=>nodeTest(name,{timeout:5000,...options},fn);
const assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const {fixture}=require('./fixtures/reference_workspace_vm.cjs');

test('R07 failed candidate sync preserves saved draft and final save warning',async()=>{
  const D=require('../geometry-web/room-candidate-draft.js');
  for(const previous of [false,true])for(const download of [false,true])for(const failure of ['容量超限','專案已切換']) {
    const f=await fixture(),page=f.w.active(1),points=[[0,0],[1000,0],[1000,1000],[0,1000]];
    const draft={schema:D.SCHEMA,draftId:'saved-draft',anchor:{kind:'page',boundaryId:1,pageId:page.id,pagePin:D.pagePin(page)},
      analysis:{sourceId:page.sourceId,page:1,coordinateSpace:'image-pixel/1',pageSize:[100,80],crop:[0,0,100,80],
        options:{mode:'image',minWidth:1,minLength:8},barriers:[],analyzerRevision:D.ANALYZER_REVISION,total:1,complete:true,ignoredNested:0},
      rows:[{rowKey:'saved-row',ordinal:1,method:'image-lines',sourcePoints:points,warnings:[],deviation:0,pointsMm:points,dimensions:[],
        rawInputs:{refRoomVertices:'old raw input',refRoomLength:'',refRoomEdge:'0'},draftRevision:0,status:'pending'}]};
    if(previous)f.w.setFeatureAttachment(D.KIND,draft,f.w.getProjectState().contextToken);
    const before=structuredClone(f.w.readFeatureAttachment(D.KIND)),history=f.w.history.undo.length;
    f.w.context().dirty=false;
    let flushes=0,downloadBlob;
    f.env.window.RoomCollectionWorkspace={hasWork:false,flushCandidates(){flushes++;throw new Error(failure);}};
    if(download){
      delete f.env.window.showSaveFilePicker;
      f.env.URL={createObjectURL(blob){downloadBlob=blob;return 'blob:room-candidate-save';},revokeObjectURL(){}};
      f.env.setTimeout=()=>0;
    }
    f.writeGate.resolve();await f.w.save();
    assert.equal(flushes,1);
    const bytes=download?new Uint8Array(await downloadBlob.arrayBuffer()):f.writes[0],opened=await P.unpack(bytes,zip);
    const saved=opened.manifest.featureAttachments?.records.find(record=>record.kind===D.KIND)?.value||null;
    assert.deepEqual(saved,before,'failed sync must keep exactly the last stored draft or no draft');
    assert.deepEqual(f.w.readFeatureAttachment(D.KIND),before);
    assert.equal(f.w.history.undo.length,history,'failed sync must not add history');
    assert.match(f.statuses.at(-1),/房間候選草稿未能寫入.*先前的草稿或沒有草稿/,JSON.stringify(f.statuses));
    assert.match(f.statuses.at(-1),download?/已產生專案下載/:/專案已保存/);
    assert.equal(f.w.context().dirty,true,'unsynchronized candidate input must not look fully saved');
  }
});
