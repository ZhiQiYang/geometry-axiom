'use strict';

// 真 DOM 與專案保存器；只用記憶體 handle 代替 OS 選檔器。
module.exports=async ({send,eval_,waitForUI,makeCheck})=>{
  console.log('=== P4635. R13 選取後保存與跨專案草稿隔離 ===');
  const check=makeCheck({prefix:'P4635 '});
  const read=async expression=>{const result=await eval_(expression);if(result?.__err)throw Error(result.__err);return result;};
  const data="ReferenceWorkspace.readFeatureAttachment('reconstruction-data')";
  const idle="ReferenceWorkspace.getEvidenceState().blocked===false";
  async function openFixture(project,raw){
    const is21=await read(`(async()=>{
      const R=GeometryReconstructionData,P=GeometryProject;
      let v=R.edit(null,{type:'create',name:${JSON.stringify(project)}});
      v=R.edit(v,{type:'edit',id:'rd-1',fields:{height:{raw:${JSON.stringify(raw)},unit:'mm'},top:{raw:'2\\r\\n3',unit:'cm'}}});
      const manifest={projectId:${JSON.stringify(project)},name:${JSON.stringify(project)},faces:[],sources:[],
        featureAttachments:{schema:P.Features.SCHEMA,records:[P.Features.record(R.KIND,v)]}};
      const scene='reset\\nsurface 4635 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000\\n';
      const bytes=await P.pack(scene,manifest,new Map(),fflate);
      return (await ReferenceWorkspace.importBytes(bytes,'輸入.gcanvas')).manifest.format==='geometry-canvas/21';
    })()`);
    if(!is21)throw Error('P4635 輸入不是 /21');
    await waitForUI(idle);
  }
  async function selectRecord(){
    await read(`enterFocus('face',4635)`);
    await read(`document.querySelector('#faceInspectorTabs [data-fi-tab="underlay"]').click()`);
    await waitForUI(`!!document.querySelector('#rdPanel')`);
    await read(`(()=>{const panel=document.querySelector('#rdPanel');if(!panel.open)panel.querySelector('summary').click();
      const select=panel.querySelector('#rdSelect');select.value='rd-1';select.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    await waitForUI(`document.querySelector('#rdSelect')?.value==='rd-1'&&!document.querySelector('#rdEditor').hidden`);
  }
  async function save(){
    return read(`(async()=>{
      const original=window.showSaveFilePicker;let bytes;
      window.showSaveFilePicker=async()=>({createWritable:async()=>({write:async data=>{bytes=new Uint8Array(data);},close:async()=>{}})});
      try{if(!await ReferenceWorkspace.save()||!bytes)throw Error('未寫入專案檔');return {bytes:[...bytes]};}
      catch(e){return {error:e.message};}finally{window.showSaveFilePicker=original;}
    })()`);
  }
  try{
    for(const width of [390,1400]){
      await send('Emulation.setDeviceMetricsOverride',{width,height:width===390?844:900,deviceScaleFactor:1,mobile:width===390});
      await openFixture('A','1\n');
      const original=await read(data);
      if(original.records.at(0).fields.height.raw!=='1\n')throw Error('P4635 未開啟含 LF 的原件');
      await selectRecord(); // 不發出任何欄位編輯事件。
      const a=await save();if(!a.bytes)throw Error('A 保存失敗：'+a.error);
      await read(`(async()=>{await ReferenceWorkspace.importBytes(new Uint8Array(${JSON.stringify(a.bytes)}),'A 重開.gcanvas');return true;})()`);
      const reopened=await read(data);
      check('R13_UNEDITED_RAW_REOPENS_EXACTLY '+width,JSON.stringify(reopened)===JSON.stringify(original),{
        height:reopened.records.at(0).fields.height.raw,top:reopened.records.at(0).fields.top.raw,nextRevision:reopened.nextRevision});

      await selectRecord();
      // A 有一筆容量被拒的編輯。離開底圖，再開同樣有 rd-1 的 B，不進 B 底圖。
      await read(`(()=>{const raw=document.querySelector('#rdHeightRaw');raw.value='x'.repeat(65);raw.dispatchEvent(new Event('input',{bubbles:true}));})()`);
      await waitForUI(`!document.querySelector('#rdReload').hidden`);
      await read(`document.querySelector('#faceInspectorTabs [data-fi-tab="prop"]').click()`);
      await waitForUI(`fe.fiTab==='prop'`);
      await openFixture('B','820');
      await waitForUI(`!document.querySelector('#rdPanel')&&ReferenceWorkspace.context().id==='B'`);
      const b=await save();
      const savedB=b.bytes?await read(`(async()=>{const {manifest}=await GeometryProject.unpack(new Uint8Array(${JSON.stringify(b.bytes)}),fflate);
        return {project:manifest.projectId,height:manifest.featureAttachments.records.find(r=>r.kind==='reconstruction-data').value.records[0].fields.height.raw};})()`):b;
      check('R13_DETACHED_A_DOES_NOT_BLOCK_B_SAVE '+width,savedB.project==='B'&&savedB.height==='820',savedB);
      await read(`doUndoRedo('undo')`);await waitForUI(`ReferenceWorkspace.context().id==='A'&&${idle}`);
      await selectRecord();
      check('R13_REJECTED_TEXT_STAYS_WITH_A '+width,await read(`!document.querySelector('#rdReload').hidden&&document.querySelector('#rdHeightRaw').value==='x'.repeat(65)&&${data}.records[0].fields.height.raw!== 'x'.repeat(65)`));
    }
  }finally{await send('Emulation.clearDeviceMetricsOverride',{});}
};
