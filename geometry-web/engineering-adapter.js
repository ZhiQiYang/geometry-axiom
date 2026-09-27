/* Formal Canvas transport: the native World remains the only source evaluator. */
"use strict";
window.EngineeringAdapter = (() => {
  const listeners = new Set();
  let ownConfirmation = false;
  const clone = value => JSON.parse(JSON.stringify(value));
  const project = () => ({...ReferenceWorkspace.getProjectState(), name:ReferenceWorkspace.context().name});
  const same = (a,b) => a.contextToken === b.contextToken && a.id === b.id;
  const assertContext = expected => {
    if (!same(expected,project())) throw new Error('專案已切換，請在目前專案重新開啟工程規格。');
  };
  const checked = result => {
    if (!result?.ok) throw new Error(result?.error || '未能取得工程資料，請確認連線後重試。');
    return result;
  };
  const command = async text => checked(await apiRequest(text));
  const normalizeRecord = record => {
    if(record.value)return {...record.value,fingerprint:record.fingerprint,archived:!!record.archived,rawValue:clone(record.value)};
    const {fingerprint,archived,...content}=record;
    return {...record,rawValue:clone(content)};
  };
  function normalize(value) {
    value={...value,...value.geometry};
    return {...value,capability:(value.capabilities || []).includes('engineering-spec/1')?'engineering-spec/1':value.capability,
      materials:(value.materials || []).map(normalizeRecord),
      methods:(value.methods || []).map(normalizeRecord),
      applications:(value.applications || []).map(record => record.value ? {...record.value} : record),
      timbers:(value.timbers || []).map(record => ({...record,placement_id:record.placement_id ?? record.surface ?? record.geometry?.surface ?? record.geometry?.placement_id}))};
  }
  async function read() {
    const expected=project(), first=await command('engineering-read');
    assertContext(expected);
    const [surfaces,references]=await Promise.all([command('surfaces'),command('references')]);
    assertContext(expected);
    const boundaries=new Map();
    for(const surface of surfaces.surfaces) {
      if(boundaries.has(surface.boundary))continue;
      const result=await apiRequest('boundary '+surface.boundary);
      if(!result.ok && (surface.boundary!==0 || result.transport))checked(result);
      assertContext(expected);boundaries.set(surface.boundary,(result.loops || []).map(loop=>loop.verts));
    }
    const last=await command('engineering-read');
    assertContext(expected);
    if(first.revision!==last.revision)throw new Error('讀取期間工程已變更，請重新讀取後預覽。');
    return normalize({...last.state,revision:last.revision,definition_sha256:last.definition_sha256,
      placements:surfaces.surfaces.map(surface=>({...surface,placement_id:surface.id,loops:boundaries.get(surface.boundary)})),
      grids:references.grids || [],guides:references.guides || [],timbers:references.timbers || [],
      specs:last.state?.specs || references.specs || []});
  }
  async function preview({operations,expectedRevision}) {
    const expected=project();
    const response=await fetch('/engineering/preview',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({schema:'engineering-transaction/1',expectedRevision,operations}),signal:AbortSignal.timeout(30000)});
    checkApiSession(response);
    if(!response.ok)throw new Error(`無法建立預覽（HTTP ${response.status}）。`);
    const result=checked(await response.json());
    assertContext(expected);
    if(!result.preview || typeof result.preview.valid!=='boolean')throw new Error('預覽資料不完整，尚未套用變更。');
    const diagnostics=(result.preview.violations || []).map(issue=>{
      if(!issue || typeof issue!=='object')return issue;
      for(const [field,kind] of [['timber','timber'],['grid','grid'],['placement_id','placement']])
        if(Number.isSafeInteger(issue[field]) && issue[field]>=0)return {...issue,object:{kind,id:issue[field]}};
      return issue;
    });
    return {...result.preview,before:normalize(result.preview.before || {}),after:normalize(result.preview.after || {}),diagnostics};
  }
  function token(value) {
    if(!/^[1-9]\d*$/.test(String(value)) || !Number.isSafeInteger(Number(value)) || Number(value)>4294967295)throw new Error('預覽識別已失效，請重新預覽。');
    return String(value);
  }
  async function confirm({token:previewToken}) {
    const expected=project();
    let result;ownConfirmation=true;
    try { result=await command('engineering-confirm '+token(previewToken)); }
    finally { ownConfirmation=false; }
    assertContext(expected);
    if(oc.edit?.kind==='boundary' || oc.edit?.bid!=null)await feAfterChange();else await refreshActive();
    assertContext(expected);
    return result;
  }
  async function cancel({token:previewToken}) { return command('engineering-cancel '+token(previewToken)); }
  async function allocateGridIds(count) {
    if(!Number.isSafeInteger(count) || count<1 || count>16)throw new Error('請選擇 1 至 16 個要建立網格的面。');
    const expected=project(), result=await command('newid '+count);assertContext(expected);
    if(!Array.isArray(result.grids) || result.grids.length!==count || new Set(result.grids).size!==count || !result.grids.every(id=>Number.isSafeInteger(id)&&id>=0&&id<=4294967295))throw new Error('目前服務未能提供完整網格識別，尚未建立網格。');
    return result.grids;
  }
  let navigationSequence=0;
  async function navigateObject(target, { isCurrent = () => true } = {}) {
    if(!target || !['timber','grid','placement'].includes(target.kind) || !Number.isSafeInteger(target.id) || target.id<0)
      throw new Error('定位資料不完整，請返回本次設定查看。');
    const sequence=++navigationSequence,expected=project(),initialFocus=oc.focus,initialObject=oc.sel,initialFaceSelection=fe.sel;
    const active=()=>sequence===navigationSequence && same(expected,project()) && !EngineeringWorkspace.isOpen && isCurrent();
    const snapshot=await read();
    if(!active() || oc.focus!==initialFocus || oc.sel!==initialObject || fe.sel!==initialFaceSelection)return;
    const item=target.kind==='placement'?snapshot.placements.find(p=>p.id===target.id)
      :snapshot[target.kind==='timber'?'timbers':'grids'].find(p=>p.id===target.id);
    const placementId=target.kind==='placement'?item?.id:item?.placement_id??item?.surface??item?.geometry?.surface;
    const placement=snapshot.placements.find(p=>p.id===placementId);
    if(!item || !placement)throw new Error('這個物件已不在目前工程，請重新讀取工程規格。');
    if(!placement.loops?.length)throw new Error('這個放置面沒有可開啟的輪廓工作區，請由三視圖查看放置 #'+placement.id+'。');
    resetSceneFocus();
    const viewChange=setView3(false,{persistPositions:false}),canvasSelection=oc.sel,faceSelection=fe.sel;
    await viewChange;
    if(!active() || oc.focus!==null || oc.sel!==canvasSelection || fe.sel!==faceSelection)return;
    await renderObjects({persistPositions:false});
    if(!active() || oc.focus!==null || oc.sel!==canvasSelection || fe.sel!==faceSelection)return;
    const pendingFocus=enterFocus('face',placement.boundary,{placementId:placement.id}),focus=oc.focus;
    await pendingFocus;
    if(!active() || oc.focus!==focus)return;
    if(oc.focus?.t!=='face' || oc.focus.id!==placement.boundary || feSid(placement.boundary)!==placement.id)
      throw new Error('定位期間畫布已切換，請重新選擇目標。');
    if(target.kind==='timber') {
      if(!fe.timbers.some(t=>t.id===target.id))throw new Error('這支角材已變更，請重新讀取後定位。');
      feSelectTimber(target.id);fiShowTab('components');
    } else if(target.kind==='grid') {
      if(!fe.grids.some(g=>g.id===target.id))throw new Error('這個網格已變更，請重新讀取後定位。');
      GridEditor.open(target.id);
    } else fiShowTab('prop');
    if(innerWidth<=680)openPanel('right',document.getElementById('workspaceToggleRight'));
    toast('已定位'+(target.kind==='timber'?'角材':target.kind==='grid'?'網格':'放置面')+' #'+target.id+'；本次工程變更尚未套用。');
  }
  let previousContext=project();
  function notify() { for(const listener of listeners)listener(); }
  window.addEventListener('geometry-definition-changed',event=>{
    if(ownConfirmation && event.detail?.command?.startsWith('engineering-confirm '))return;
    notify();
  });
  window.addEventListener('space-models-changed',()=>{
    const next=project();if(!same(previousContext,next)){previousContext=next;notify();}
  });
  const adapter={getProjectState:project,context:()=>{const value=project();return {...value,token:value.contextToken};},
    getEngineeringDrafts:()=>ReferenceWorkspace.getEngineeringDrafts(),
    setEngineeringDraft:(record,contextToken)=>ReferenceWorkspace.setEngineeringDraft(record,contextToken),
    removeEngineeringDraft:(id,contextToken)=>ReferenceWorkspace.removeEngineeringDraft(id,contextToken),
    read,preview,confirm,cancel,allocateGridIds,navigateObject,
    saveProject:()=>ReferenceWorkspace.save(),
    subscribe:listener=>{listeners.add(listener);return ()=>listeners.delete(listener);}};
  EngineeringWorkspace.configure(adapter);
  document.addEventListener('click',event=>{
    const button=event.target.closest('[data-engineering-open]');if(!button || button.disabled)return;
    event.preventDefault();document.getElementById('fileMenuPop').hidden=true;
    const placementId=button.dataset.placementId,gridId=button.dataset.gridId;
    EngineeringWorkspace.open({...(placementId!==undefined?{placementId:Number(placementId)}:{}),...(gridId!==undefined?{gridId:Number(gridId)}:{})});
  });
  document.getElementById('btnEngineeringExample').onclick=async event=>{
    const button=event.currentTarget;
    if(button.disabled || oc.busy || ReferenceWorkspace.busy || !ReferenceWorkspace.mayLeave())return;
    const expected=project();button.disabled=true;
    try {
      const response=await fetch('/examples/engineering-spec-v1.gcanvas',{signal:AbortSignal.timeout(30000)});
      checkApiSession(response);
      if(!response.ok)throw new Error('無法讀取現成工程專案，請確認服務版本後重試。');
      const bytes=new Uint8Array(await response.arrayBuffer());
      assertContext(expected);
      if(expected.revision!==project().revision)throw new Error('讀取範例期間目前工程已有變更，請再次開啟範例。');
      await ReferenceWorkspace.importBytes(bytes,'engineering-spec-v1.gcanvas');
      resetSceneFocus();await setView3(false);await renderObjects();
      document.getElementById('fileMenuPop').hidden=true;
      await EngineeringWorkspace.open();
    }catch(error){toast(error.message,'error');}
    finally {button.disabled=false;}
  };
  return adapter;
})();
