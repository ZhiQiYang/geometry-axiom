/* Single UI owner integration seam: existing panes, no app/store/common edits. */
(() => {
  'use strict';
  const S=window.SourceInspector,context=()=>ReferenceWorkspace.context();
  const stamp=()=>JSON.stringify([ReferenceWorkspace.history?.frame,ReferenceWorkspace.getProjectState?.().revision,
    [...context().groups||[]].map(([bid,g])=>[bid,g.activePageId])]);
  const read=()=>apiRequest('source-inspect');
  async function readSnapshot(scene,signal){const r=await fetch('/sources/snapshot',{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:scene,signal});if(!r.ok)throw Error('來源快照尚未檢查；服務能力不足。');return r.json();}
  function exportSnapshotCSV(csv,snapshot){
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),link=document.createElement('a');
    link.href=url;link.download=`model-snapshot-${snapshot.modelId}.csv`;
    try{link.click();}finally{setTimeout(()=>URL.revokeObjectURL(url),0);}
  }
  async function navigate(n,g,{isCurrent=()=>true,beginNavigation=()=>true}={}){
    const id=Number(n.id);
    if(['guide','grid','timber','placement'].includes(n.kind))return EngineeringAdapter.navigateObject({kind:n.kind,id},{sourceGraph:g,isCurrent,beginNavigation});
    if(n.kind==='parameter-field')n={...n,kind:'parameter',hasField:true};
    if(['boundary','placement','space','column','beam','grid-system','grid-binding','parameter','assembly-rule','assembly-binding'].includes(n.kind)){
      if(!isCurrent())return;
      if(n.kind==='assembly-rule'){const active=ocFind(n.kind,id);if(active?.version!==n.version)throw Error(`固定 v${n.version} 保留；目前卡片顯示其他版本，請於既有組構工作區核對。`);}
      if(!ocFind(n.kind,id))throw Error('來源尚未在目前畫布提供定位。');
      // Accepted discard can replace this inspector. Transfer its existing
      // lease before asking; cancellation still changes no presentation.
      if(!beginNavigation()||!window.DraftGate.ask({selection:[{kind:n.kind,id}]})||!isCurrent())return;
      if(oc.focus){
        await leaveFocus();if(!isCurrent()||oc.focus)return;
      }
      if(!selectObject(n.kind,id)||!isCurrent())return;
      centerOnNode(n.kind,id);
      if(n.hasField){const row=document.querySelector(`[data-param-field="${n.fieldId}"]`);row?.scrollIntoView({block:'nearest'});row?.querySelector('[data-input]')?.focus({preventScroll:true});}
      if(innerWidth<=900)openPanel('right',document.getElementById('toggleRight'));return;
    }
    throw Error('此來源保留具型別身分；目前尚無欄位定位入口。');
  }
  const watched=new Map();let modelHost=null,modelSequence=0;
  function install(host,selection,record=null,snapshotOnly=false){
    if(!host||!selection||host.hidden)return;
    const tag=JSON.stringify([context().id,selection,record,stamp()]);const current=watched.get(host);
    if(current?.tag===tag&&current.mount.detail.isConnected)return;
    current?.mount.cancel();
    const getRecord=()=>{if(snapshotOnly)return SpaceModelWorkspace.snapshotRecord();const found=ReferenceWorkspace.getSpaceModels().filter(m=>m.id===record.id);return found.length===1?found[0]:null;};
    const mount=S.mount(host,{selection,record,context,stamp:record&&!snapshotOnly?()=>JSON.stringify([stamp(),modelSequence]):stamp,read,readSnapshot,navigate,
      ...(record?{getRecord,project:window.GeometryProject,timberSchedule:window.TimberSchedule,exportCSV:exportSnapshotCSV,
        activate(){if(modelHost!==host){modelHost=host;++modelSequence;}},
        isActive:()=>modelHost===host&&host.isConnected!==false&&!host.closest('[hidden]')&&host.closest('dialog')?.open!==false}: {}),
      ...(snapshotOnly?{snapshotOnly,activate(){},isActive:()=>!!SpaceModelWorkspace.snapshotRecord(),
        onSchedule:(schedule,proof)=>SpaceModelWorkspace.authorizeSnapshotSchedule(record,schedule,proof),
        onSelect:id=>SpaceModelWorkspace.selectSnapshotTimber(id)}:{})});watched.set(host,{tag,mount});
  }
  function sync(){
    const pane=document.getElementById('inspectorContent');if(oc.sel&&!oc.parameterCreating&&oc.selection.length===1){const o=ocFind(oc.sel.kind,oc.sel.id);if(o)install(pane,S.key(oc.sel.kind,o.id,oc.sel.kind==='assembly-rule'?o.version:0));}
    const face=document.getElementById('faceInspectorContent');if(oc.edit&&fe.timberSelection.size<=1){const selected=fe.sel?.kind==='timber'?S.key('timber',fe.sel.id):fe.fiTab==='grid'&&fe.gridEditingId!=null?S.key('grid',fe.gridEditingId):S.key('boundary',oc.edit.bid);install(face,selected);}
    const list=document.getElementById('smLibraryList');for(const button of list?.querySelectorAll('[data-sm-open-model]')||[]){const model=ReferenceWorkspace.getSpaceModels().find(m=>m.id===button.dataset.smOpenModel),host=button.closest('.sm-model-card');if(model)install(host,S.modelRoots(model)[0]||'untraceable',model);}
    const host=document.getElementById('smTimberReviewList'),model=window.SpaceModelWorkspace?.snapshotRecord();
    if(model?.input.mode==='plan'&&model.input.timbers?.length)install(host,S.modelRoots(model)[0]||'untraceable',model,true);
    else if(watched.has(host)){watched.get(host).mount.cancel();watched.delete(host);host.querySelector('[data-source-inspector]')?.remove();}
  }
  let scheduled=false;function queue(){if(scheduled)return;scheduled=true;queueMicrotask(()=>{scheduled=false;sync();});}
  for(const id of ['inspectorContent','faceInspectorContent']){const host=document.getElementById(id);if(host)new MutationObserver(records=>{if(records.some(r=>!r.target.closest?.('[data-source-inspector]')))queue();}).observe(host,{childList:true,subtree:true});}
  // SpaceWorkspace is loaded before this adapter; observe its existing library only.
  const library=document.getElementById('smLibraryList');if(library){
    // The existing library's model actions select another owner without a
    // project edit. Invalidate pending CSV work even if its card stays in DOM.
    library.addEventListener('click',event=>{if(event.target.closest('[data-sm-open-model],[data-sm-edit-height],[data-sm-remove-model],[data-sm-library-trial]')){modelHost=null;++modelSequence;}});
    new MutationObserver(records=>{if(records.some(r=>!r.target.closest?.('[data-source-inspector]')))queue();}).observe(library,{childList:true,subtree:true});
  }
  for(const event of ['space-model-view-changed','space-models-changed'])window.addEventListener(event,queue);
  window.addEventListener('space-model-timber-selected',event=>{
    const record=SpaceModelWorkspace.snapshotRecord(),mount=watched.get(document.getElementById('smTimberReviewList'))?.mount;
    if(record?.id===event.detail.modelId&&JSON.stringify(record)===event.detail.signature&&!mount?.selectSnapshot(event.detail.id))SpaceModelWorkspace.authorizeSnapshotSchedule(record,null);
  });
  window.SourceInspectorApp={sync,navigate};queue();
})();
