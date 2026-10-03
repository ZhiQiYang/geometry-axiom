/* Single UI owner integration seam: existing panes, no app/store/common edits. */
(() => {
  'use strict';
  const S=window.SourceInspector,context=()=>ReferenceWorkspace.context();
  const stamp=()=>JSON.stringify([ReferenceWorkspace.history?.frame,ReferenceWorkspace.getProjectState?.().revision]);
  const read=()=>apiRequest('source-inspect');
  async function readSnapshot(scene,signal){const r=await fetch('/sources/snapshot',{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:scene,signal});if(!r.ok)throw Error('來源快照尚未檢查；服務能力不足。');return r.json();}
  async function navigate(n,g){
    const id=Number(n.id);
    if(n.kind==='parameter-field')n={...n,kind:'parameter',hasField:true};
    if(n.kind==='placement'&&!ocFind('placement',id)){const p=oc.surfs.find(p=>p.id===id);if(p&&ocFind('boundary',p.boundary)){if(oc.focus)leaveFocus();selectObject('boundary',p.boundary);centerOnNode('boundary',p.boundary);return;}}
    if(['boundary','placement','space','column','beam','grid-system','grid-binding','parameter','assembly-rule','assembly-binding'].includes(n.kind)){
      if(n.kind==='assembly-rule'){const active=ocFind(n.kind,id);if(active?.version!==n.version)throw Error(`固定 v${n.version} 保留；目前卡片顯示其他版本，請於既有組構工作區核對。`);}
      if(!ocFind(n.kind,id))throw Error('來源尚未在目前畫布提供定位。');
      if(oc.focus)leaveFocus();selectObject(n.kind,id);centerOnNode(n.kind,id);
      if(n.hasField){const row=document.querySelector(`[data-param-field="${n.fieldId}"]`);row?.scrollIntoView({block:'nearest'});row?.querySelector('[data-input]')?.focus({preventScroll:true});}
      if(innerWidth<=900)openPanel('right',document.getElementById('toggleRight'));return;
    }
    if(['guide','grid','timber'].includes(n.kind)){
      const edge=(g.out.get(n.key)||[]).find(e=>e.relation==='position'&&e.field==='surface'),surface=edge&&g.nodes.get(edge.to);
      const boundary=surface&&(g.out.get(surface.key)||[]).find(e=>e.field==='boundary'),bid=boundary&&Number(g.nodes.get(boundary.to)?.id);
      if(!Number.isSafeInteger(bid)||!ocFind('boundary',bid))throw Error('來源面目前無法定位。');
      const ctx=context();if(oc.focus?.t!=='face'||oc.focus.id!==bid)await enterFocus('face',bid);
      if(context()!==ctx)throw Error('定位期間專案已切換。');
      await feLoadGuides();if(context()!==ctx)throw Error('定位期間專案已切換。');if(n.kind==='timber')feSelectTimber(id);else if(n.kind==='grid'){fe.gridEditingId=id;renderFaceInspector();fiShowTab('grid');}else{fiShowTab('guide');document.querySelector(`[data-guide-edit="${id}"]`)?.scrollIntoView({block:'nearest'});document.querySelector(`[data-guide-edit="${id}"]`)?.focus({preventScroll:true});}
      if(innerWidth<=680)openPanel('right',document.getElementById('workspaceToggleRight'));return;
    }
    throw Error('此來源保留具型別身分；目前尚無欄位定位入口。');
  }
  const watched=new Map();
  function install(host,selection,record=null){
    if(!host||!selection||host.hidden)return;
    const tag=JSON.stringify([context().id,selection,record?.id,stamp()]);const current=watched.get(host);
    if(current?.tag===tag&&current.mount.detail.isConnected)return;
    current?.mount.cancel();const mount=S.mount(host,{selection,record,context,stamp,read,readSnapshot,navigate});watched.set(host,{tag,mount});
  }
  function sync(){
    const pane=document.getElementById('inspectorContent');if(oc.sel&&!oc.parameterCreating&&oc.selection.length===1){const o=ocFind(oc.sel.kind,oc.sel.id);if(o)install(pane,S.key(oc.sel.kind,o.id,oc.sel.kind==='assembly-rule'?o.version:0));}
    const face=document.getElementById('faceInspectorContent');if(oc.edit&&fe.timberSelection.size<=1){const selected=fe.sel?.kind==='timber'?S.key('timber',fe.sel.id):fe.fiTab==='grid'&&fe.gridEditingId!=null?S.key('grid',fe.gridEditingId):S.key('boundary',oc.edit.bid);install(face,selected);}
    const list=document.getElementById('smLibraryList');for(const button of list?.querySelectorAll('[data-sm-open-model]')||[]){const model=ReferenceWorkspace.getSpaceModels().find(m=>m.id===button.dataset.smOpenModel),host=button.closest('.sm-model-card');if(model)install(host,S.modelRoots(model)[0]||'untraceable',model);}
  }
  let scheduled=false;function queue(){if(scheduled)return;scheduled=true;queueMicrotask(()=>{scheduled=false;sync();});}
  for(const id of ['inspectorContent','faceInspectorContent']){const host=document.getElementById(id);if(host)new MutationObserver(records=>{if(records.some(r=>!r.target.closest?.('[data-source-inspector]')))queue();}).observe(host,{childList:true,subtree:true});}
  // SpaceWorkspace is loaded before this adapter; observe its existing library only.
  const library=document.getElementById('smLibraryList');if(library)new MutationObserver(records=>{if(records.some(r=>!r.target.closest?.('[data-source-inspector]')))queue();}).observe(library,{childList:true,subtree:true});
  window.SourceInspectorApp={sync,navigate};queue();
})();
