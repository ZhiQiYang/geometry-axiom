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
    try {
      assertContext(expected);
      if(oc.edit?.kind==='boundary' || oc.edit?.bid!=null)await feAfterChange();else await refreshActive();
      assertContext(expected);
    } catch (cause) {
      // Native confirmation already succeeded. Preserve that receipt even if
      // refreshing its presentation fails or the project owner has retired.
      // Native rejection remains outside this catch and has no such receipt.
      const error=new Error(cause?.message || String(cause),{cause});
      error.engineeringConfirmation=result;
      throw error;
    }
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
  async function navigateObject(target, { isCurrent = () => true, beginNavigation = () => true, sourceGraph = null } = {}) {
    if(!target || !['guide','timber','grid','placement'].includes(target.kind) || !Number.isSafeInteger(target.id) || target.id<0 || target.id>4294967295)
      throw new Error('定位資料不完整，請返回本次設定查看。');
    const sequence=++navigationSequence,expected=project(),context=ReferenceWorkspace.context(),frame=ReferenceWorkspace.history?.frame;
    const pages=()=>JSON.stringify([...context.groups||[]].map(([bid,g])=>[bid,g.activePageId]));
    const pageContext=pages(),initialFocus=oc.focus,initialObject=oc.sel,initialFaceSelection=fe.sel;
    const active=()=>isCurrent() && sequence===navigationSequence && ReferenceWorkspace.context()===context && same(expected,project()) &&
      project().revision===expected.revision && ReferenceWorkspace.history?.frame===frame && pages()===pageContext && !EngineeringWorkspace.isOpen;
    const initial=()=>active() && isCurrent() && oc.focus===initialFocus && oc.sel===initialObject && fe.sel===initialFaceSelection;
    const snapshot=SourceInspector.index(await command('source-inspect'));
    if(!initial())return;
    const pin=sourceGraph||snapshot;
    const verify=graph=>{
      if(graph.data.revision!==pin.data.revision || graph.data.sourceFingerprint!==pin.data.sourceFingerprint)
        throw new Error('來源已變更或刪除，請重新檢查後定位。');
    };
    verify(snapshot);
    const {placementId,boundaryId}=SourceInspector.resolveLocation(snapshot,target);
    if(boundaryId===null){
      const surfaces=await command('surfaces');if(!initial())return;
      const placements=surfaces.surfaces.filter(p=>p.id===placementId);
      if(placements.length!==1 || placements[0].boundary!==0)throw new Error('來源放置關係缺失，請重新檢查。');
      const final=SourceInspector.index(await command('source-inspect'));if(!initial())return;verify(final);
      if(!window.DraftGate.ask() || !beginNavigation())return;
      resetSceneFocus();const selection=oc.sel,faceSelection=fe.sel;
      const canvasCurrent=()=>active()&&oc.focus===null&&oc.sel===selection&&fe.sel===faceSelection;
      await setView3(false,{persistPositions:false});if(!canvasCurrent())return;
      await renderObjects({persistPositions:false});if(!canvasCurrent())return;
      const loaded=SourceInspector.index(await command('source-inspect'));if(!canvasCurrent())return;verify(loaded);
      if(!ocFind('placement',placementId))throw new Error('來源放置卡片目前無法定位。');
      selectObject('placement',placementId);centerOnNode('placement',placementId);
      if(innerWidth<=900)openPanel('right',document.getElementById('toggleRight'));return;
    }
    const boundary=await apiRequest('boundary '+boundaryId);
    if(!initial())return;
    if(!boundary.ok || !boundary.loops?.length)throw new Error('這個放置面沒有可開啟的輪廓工作區，請由三視圖查看放置 #'+placementId+'。');
    const checkedSource=SourceInspector.index(await command('source-inspect'));
    if(!initial())return;
    verify(checkedSource);
    // The source owner transfers its lease across its own pane replacement;
    // explicit cancellation and saved-model ownership remain checked throughout.
    if(!window.DraftGate.ask() || !beginNavigation())return;
    resetSceneFocus();
    const viewChange=setView3(false,{persistPositions:false}),canvasSelection=oc.sel,faceSelection=fe.sel;
    await viewChange;
    if(!active() || oc.focus!==null || oc.sel!==canvasSelection || fe.sel!==faceSelection)return;
    await renderObjects({persistPositions:false});
    if(!active() || oc.focus!==null || oc.sel!==canvasSelection || fe.sel!==faceSelection)return;
    const pendingFocus=enterFocus('face',boundaryId,{placementId}),focus=oc.focus;
    await pendingFocus;
    if(!active() || oc.focus!==focus)return;
    if(oc.focus?.t!=='face' || oc.focus.id!==boundaryId || oc.focus.placementId!==placementId || feSid(boundaryId)!==placementId)
      throw new Error('定位期間畫布已切換，請重新選擇目標。');
    const loadedSelection=fe.sel,final=SourceInspector.index(await command('source-inspect'));
    if(!active() || oc.focus!==focus || fe.sel!==loadedSelection)return;
    verify(final);
    if(target.kind==='timber') {
      if(!fe.timbers.some(t=>t.id===target.id))throw new Error('這支角材已變更，請重新讀取後定位。');
      feSelectTimber(target.id);fiShowTab('components');
    } else if(target.kind==='grid') {
      if(!fe.grids.some(g=>g.id===target.id))throw new Error('這個網格已變更，請重新讀取後定位。');
      GridEditor.open(target.id);
    } else if(target.kind==='guide') {
      if(!fe.guides.some(g=>g.id===target.id))throw new Error('這條參考線已變更，請重新檢查後定位。');
      fiShowTab('guide');
      const row=document.querySelector(`[data-guide-edit="${target.id}"]`);
      row?.scrollIntoView({block:'nearest'});row?.focus({preventScroll:true});
    } else fiShowTab('prop');
    if(innerWidth<=680)openPanel('right',document.getElementById('workspaceToggleRight'));
    toast('已定位'+(target.kind==='timber'?'角材':target.kind==='grid'?'網格':target.kind==='guide'?'參考線':'放置面')+' #'+target.id+(sourceGraph?'。':'；本次工程變更尚未套用。'));
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
    isGridContextCurrent:value=>!!value&&oc.focus?.t==='face'&&feSid(oc.focus.id)===value.placementId,
    gridConfirmed:value=>{if(oc.focus?.t==='face'&&feSid(oc.focus.id)===value.placementId)GridEditor.open(value.gridId);},
    saveProject:()=>ReferenceWorkspace.save(),
    subscribe:listener=>{listeners.add(listener);return ()=>listeners.delete(listener);}};
  EngineeringWorkspace.configure(adapter);
  document.addEventListener('click',event=>{
    const gridButton=event.target.closest('[data-engineering-grid]');
    if(gridButton){
      if(gridButton.disabled)return;
      event.preventDefault();
      const draft=GridEditor.engineeringContext();
      const placement=gridButton.dataset.placementId,grid=gridButton.dataset.gridId;
      if(!draft||placement===undefined||Number(placement)!==draft.placementId||(grid===undefined?null:Number(grid))!==draft.gridId){toast('網格畫布已切換，請在目前面的網格表單重新選擇材料規格。','error');return;}
      EngineeringWorkspace.open({placementId:draft.placementId,gridId:draft.gridId,gridDraft:draft,mode:'grid'});
      return;
    }
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
      await ReferenceWorkspace.openProject(async()=>{
        const response=await fetch('/examples/engineering-spec-v1.gcanvas',{signal:AbortSignal.timeout(30000)});
        checkApiSession(response);
        if(!response.ok)throw new Error('無法讀取現成工程專案，請確認服務版本後重試。');
        const bytes=new Uint8Array(await response.arrayBuffer());
        assertContext(expected);
        if(expected.revision!==project().revision)throw new Error('讀取範例期間目前工程已有變更，請再次開啟範例。');
        return bytes;
      },'engineering-spec-v1.gcanvas',async()=>{
        resetSceneFocus();await setView3(false);await renderObjects();
        document.getElementById('fileMenuPop').hidden=true;
        await EngineeringWorkspace.open();
      },{source:'example'});
    }catch(error){toast(error.message,'error');}
    finally {button.disabled=false;}
  };
  return adapter;
})();
