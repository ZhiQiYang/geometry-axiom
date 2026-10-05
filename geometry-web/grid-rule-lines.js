/* Readonly D19a transport and presentation. Coordinates and clipping come
 * exclusively from grid-rule-query; identities never come from pixels. */
(() => {
  'use strict';
  const uint=(n,positive=false)=>Number.isInteger(n)&&n>=(positive?1:0)&&n<=4294967295;
  const signed=s=>typeof s==='string'&&/^(0|-?[1-9]\d*)$/.test(s)&&BigInt(s)>=-(1n<<63n)&&BigInt(s)<(1n<<63n);
  function ref(r){
    if(!r||r.kind!=='grid-rule-line'||!uint(r.appliedGridId)||!uint(r.systemId)||!uint(r.ruleKey,true)||
       !signed(r.cellI)||!signed(r.cellJ)||!['u','v'].includes(r.axis)||!uint(r.innerIndex)||r.innerIndex>63)return null;
    return {kind:r.kind,appliedGridId:r.appliedGridId,systemId:r.systemId,ruleKey:r.ruleKey,cellI:r.cellI,cellJ:r.cellJ,axis:r.axis,innerIndex:r.innerIndex};
  }
  const parts=r=>[r.appliedGridId,r.systemId,r.ruleKey,r.cellI,r.cellJ,r.axis,r.innerIndex];
  const key=r=>{r=ref(r);return r?parts(r).join(':'):null;};
  const anchor=r=>{r=ref(r);return r?'at-line rule '+parts(r).join(' '):null;};
  const expression=r=>{r=ref(r);return r?'gridrule:'+key(r):null;};
  function parse(text,prefix,separator){
    if(typeof text!=='string'||!text.startsWith(prefix))return null;
    const p=text.slice(prefix.length).split(separator);if(p.length!==7)return null;
    if(![p[0],p[1],p[2],p[6]].every(s=>/^(0|[1-9]\d*)$/.test(s)))return null;
    return ref({kind:'grid-rule-line',appliedGridId:Number(p[0]),systemId:Number(p[1]),ruleKey:Number(p[2]),cellI:p[3],cellJ:p[4],axis:p[5],innerIndex:Number(p[6])});
  }
  const parseAnchor=text=>parse(text,'at-line rule ',' '),parseExpression=text=>parse(text,'gridrule:',':');
  const label=(r,name='')=>`來源 ${r.systemId}／rule ${r.ruleKey}${name?'「'+name+'」':''} · 套用 ${r.appliedGridId} · cell (${r.cellI}, ${r.cellJ}) · ${r.axis} 子線 ${r.innerIndex}`;
  function rows(query,{kind,id,systemId,ruleKey,cell=null}){
    if(!query?.ok)throw Error(query?.error||'來源子線查詢失敗。');
    const cells=query.cells||[query],out=[];
    for(const c of cells){
      if(c.systemId!==systemId||c.ruleKey!==ruleKey||!Array.isArray(c.cell)||c.cell.length!==2||!c.cell.every(signed)||
         cell&&c.cell.some((v,i)=>v!==cell[i])||!Array.isArray(c.bounds)||c.bounds.length!==4||!c.bounds.every(Number.isSafeInteger))throw Error('來源子線查詢身分不符。');
      for(const l of c.lines||[]){
        if(!['u','v'].includes(l.axis)||!uint(l.innerIndex)||!Number.isSafeInteger(l.coordinate)||!Array.isArray(l.segments)||
           l.segments.some(s=>!Array.isArray(s)||s.length!==2||s.some(p=>!Array.isArray(p)||p.length!==2||!p.every(Number.isSafeInteger))))throw Error('來源子線查詢資料不完整。');
        const r=ref(l.ref);
        if(kind==='grid'?(!r||r.appliedGridId!==id||r.systemId!==systemId||r.ruleKey!==ruleKey||r.cellI!==c.cell[0]||r.cellJ!==c.cell[1]||r.axis!==l.axis||r.innerIndex!==l.innerIndex):l.ref!==null)throw Error('來源子線引用與查詢目標不符。');
        out.push({...l,ref:r,cell:c.cell,bounds:c.bounds,systemId,ruleKey});
      }
    }
    return out;
  }
  /* Count stored typed references, never every user of a source. Guides may
   * contain arithmetic; tokenize its accepted quantity grammar, including
   * signed cells, without using a diagnostic string or evaluated offset. */
  function expressionRefs(text){
    if(typeof text!=='string')return [];
    return [...text.matchAll(/gridrule:(\d+):(\d+):(\d+):(-?\d+):(-?\d+):([uv]):(\d+)(?=$|[+\-])/g)].map(m=>parseExpression(m[0])).filter(Boolean);
  }
  function usage(references,systemId,ruleKey){
    return {guides:(references?.guides||[]).filter(g=>expressionRefs(g.expression).some(r=>r.systemId===systemId&&r.ruleKey===ruleKey)),
      timbers:(references?.timbers||[]).filter(t=>{const r=parseAnchor(t.definition?.anchor);return r?.systemId===systemId&&r.ruleKey===ruleKey;})};
  }
  const api={ref,key,anchor,expression,parseAnchor,parseExpression,expressionRefs,label,rows,usage,signed};
  if(typeof module!=='undefined')module.exports=api;
  if(typeof window==='undefined')return;
  window.GridRuleLines=api;
  let owner=null,sequence=0,reload=null;
  const presentationState=()=>{const {blocked,...state}=ReferenceWorkspace.getEvidenceState();return state;};
  const stamp=()=>JSON.stringify([presentationState(),ReferenceWorkspace.history.frame,
    [...ReferenceWorkspace.context().groups||[]].map(([id,g])=>[id,g.activePageId])]);
  const initial=s=>owner===s&&s.context===ReferenceWorkspace.context()&&s.edit===oc.edit&&s.focus===oc.focus&&s.stamp===stamp();
  const current=s=>initial(s)&&s.key===viewportKey();
  const viewport=()=>{const v=$('faceEditorViewport'),r=v?.getBoundingClientRect();if(!r||!fe.zoom)return null;
    const clamp=n=>Math.max(-100000000,Math.min(100000000,n));return [clamp(Math.floor(-fe.panX/fe.zoom)),clamp(Math.floor(-fe.panY/fe.zoom)),clamp(Math.ceil((r.width-fe.panX)/fe.zoom)),clamp(Math.ceil((r.height-fe.panY)/fe.zoom))];};
  const viewportKey=()=>JSON.stringify([viewport(),fe.grids.map(g=>[g.id,g.sourceSystem,g.bindingId,GeometryProject.Features.gridSourceKey(oc.gridSystems.find(s=>s.id===g.sourceSystem))])]);
  function clear(){if(owner)clearTimeout(owner.timer);owner=null;++sequence;fe.ruleSelection=null;fe.ruleFocus=null;}
  function entries(){return owner&&current(owner)?owner.rows:[];}
  function find(r){const k=key(r);return k&&entries().find(l=>key(l.ref)===k);}
  function refresh(){
    if(reload?.isCurrent())return;
    reload=null;
    if(!oc.edit||oc.focus?.t!=='face')return;
    const k=viewportKey(),mark=stamp();if(owner&&current(owner))return;
    if(owner)clearTimeout(owner.timer);
    const s=owner={context:ReferenceWorkspace.context(),edit:oc.edit,focus:oc.focus,stamp:mark,key:k,rows:[],messages:[],ticket:++sequence};
    s.timer=setTimeout(()=>query(s),80);
  }
  const focusInputs=()=>JSON.stringify(['gridRuleFocusKey','gridRuleCellI','gridRuleCellJ'].map(id=>$(id)?.value));
  function paintQuery(){
    drawFaceEditor();
    // Read completion owns rule presentation, not a nested editor that the
    // user opened in the same face inspector while native reads were pending.
    if($('faceInspectorContent')?.querySelector('.grid-rule-details,#tbAnchor,#refGuideSource'))renderFaceInspector();
  }
  async function query(s,focus=null,isCurrent=()=>true){
    const input=focus?focusInputs():null;
    const request=s.request=(s.request||0)+1,owns=()=>isCurrent()&&current(s)&&s.request===request&&(!focus||input===focusInputs());
    try{
      const before=await apiRequest('source-inspect');if(!owns()||!before.ok)return;
      if(before.sourceFingerprint!==fe.timberReferenceData?.sourceFingerprint)return;
      const out=[],messages=[];
      for(const g of fe.grids){const source=oc.gridSystems.find(row=>row.id===g.sourceSystem);for(const rule of source?.rules||[]){
        if(focus&&(focus.grid!==g.id||focus.rule!==rule.ruleKey))continue;
        const target={kind:'grid',id:g.id,systemId:source.id,ruleKey:rule.ruleKey,...(focus?{cell:focus.cell}:{})};
        const cmd=`grid-rule-query grid ${g.id} rule ${rule.ruleKey} `+(focus?`cell ${focus.cell.join(' ')}`:`rect ${viewport().join(' ')} mode sample limit 32`);
        const result=await apiRequest(cmd);if(!owns())return;
        if(!result.ok){messages.push(`來源 ${source.id}／rule ${rule.ruleKey}：${result.error}`);continue;}
        out.push(...rows(result,target).map(l=>({...l,name:rule.name,grid:g})));
        if(result.complete===false)messages.push(`來源 ${source.id}／rule ${rule.ruleKey}：抽樣未完整（${result.requiredCells} 格，每 ${result.stride} 格顯示一格）；可輸入真正 cell 索引完整定位。`);
      }}
      const after=await apiRequest('source-inspect');if(!owns()||!after.ok||before.revision!==after.revision||before.sourceFingerprint!==after.sourceFingerprint)return;
      s.rows=out;s.messages=messages;s.loaded=true;s.graph=SourceInspector.index(after);
      s.focusStatus=focus&&focusInputs()===JSON.stringify([String(focus.rule),...focus.cell])?(messages.length?messages.join('；'):out.reduce((n,l)=>n+l.segments.length,0)===0?'完整原生 cell 已核對：本面零可見線段。':'完整原生 cell 已核對：'+out.reduce((n,l)=>n+l.segments.length,0)+' 段可見子線。'):'';
      if(fe.ruleSelection&&!out.some(l=>key(l.ref)===key(fe.ruleSelection)))fe.ruleSelection=null;
      paintQuery();
    }catch(error){if(owns()){s.messages=[error.message];s.focusStatus=focus?error.message:'';s.loaded=true;paintQuery();}}
  }
  /* A rollback changes the native revision. Keep the live form untouched
   * while its snapshot and exact cell are read again; never rebuild selects
   * from the temporary empty reference arrays inside the snapshot loader. */
  async function reloadNative(load,isCurrent,reference=null){
    if(!isCurrent())return;
    const pin=reload={isCurrent},focus=fe.ruleFocus,selection=fe.ruleSelection;
    try{
      await load();if(reload!==pin||!isCurrent())return;
      reload=null;refresh();const s=owner;if(!s||!current(s))return;
      clearTimeout(s.timer);fe.ruleFocus=focus;fe.ruleSelection=selection;
      const target=reference?{grid:reference.appliedGridId,rule:reference.ruleKey,cell:[reference.cellI,reference.cellJ]}:focus;
      await query(s,target,isCurrent);
    }finally{if(reload===pin)reload=null;}
  }
  function select(r){if(!find(r))return;fe.ruleSelection=ref(r);fe.gridEditingId=r.appliedGridId;fe.sel=null;fe.timberSelection.clear();fiShowTab('grid');renderFaceInspector();drawFaceEditor();if(innerWidth<=680)openPanel('right',$('workspaceToggleRight'));}
  function draw(root,refRoot,z){
    let index=0;
    for(const l of entries()){
      if(!ReferenceVisibility.visible('rule:'+key(l.ref)))continue;
      const k=key(l.ref),selected=k===key(fe.ruleSelection),clip='rule-cell-'+index++;
      const c=el('clipPath',{id:clip,clipPathUnits:'userSpaceOnUse'},el('defs',{},refRoot));el('rect',{x:l.bounds[0],y:l.bounds[1],width:l.bounds[2]-l.bounds[0],height:l.bounds[3]-l.bounds[1]},c);
      const group=el('g',{'clip-path':`url(#${clip})`},refRoot);
      for(const segment of l.segments){const a=segment[0],b=segment[1];
        const attrs={x1:a[0],y1:a[1],x2:b[0],y2:b[1],'data-rule-line-key':k};
        el('line',{...attrs,class:'face-rule-line'+(selected?' selected':'')},group);
        const hit=el('line',{...attrs,'data-face-hit':'r:'+k,class:'face-rule-hit',stroke:'transparent','stroke-width':Math.max(8,14/z)},group);
        el('title',{},hit).textContent=label(l.ref,l.name)+` · ${l.axis}=${l.coordinate} mm`;
        hit.onpointerdown=e=>{if(['select','grid'].includes(fe.tool)){e.stopPropagation();e.preventDefault();select(l.ref);}};
      }
      if(selected&&l.segments.length){const a=l.segments[0][0];el('text',{x:a[0]+5/z,y:a[1]+15/z,'font-size':11/z,class:'fe-rule-label','data-rule-label':k},group).textContent=`rule ${l.ruleKey} · ${l.axis} 子線 ${l.innerIndex} · ${l.coordinate} mm`;}
    }
    let note=$('feRuleDensity');const messages=owner&&current(owner)?owner.messages:[];
    if(messages.length&&!note){note=document.createElement('p');note.id='feRuleDensity';note.className='fe-rule-density';note.setAttribute('role','status');$('faceEditorViewport').append(note);}
    if(note){note.hidden=!messages.length;note.textContent=messages.join('；');}
  }
  function html(g){
    const source=oc.gridSystems.find(s=>s.id===g?.sourceSystem);if(!source?.rules?.length)return '';
    const esc=ReferenceWorkspace.escape,selected=fe.ruleSelection?.appliedGridId===g.id?find(fe.ruleSelection):null;
    const rule=source.rules.find(r=>r.ruleKey===fe.ruleFocus?.rule)||source.rules[0],cell=fe.ruleFocus?.grid===g.id?fe.ruleFocus.cell:oc.gridBindings.find(b=>b.id===g.bindingId)?.cell||['0','0'];
    return `<div class="grid-rule-details"><h4>來源規則子線 · 共用</h4><p>來源 ${source.id} → ${g.bindingId!=null?'配置 '+g.bindingId+' → ':''}套用 ${g.id}。手動子網格另列於局部等分。</p>${source.rules.map(r=>{const u=usage(fe.timberReferenceData,source.id,r.ruleKey);return `<p data-rule-summary="${r.ruleKey}"><button type="button" class="grid-text-button" data-rule-source="${r.ruleKey}">#${r.ruleKey} ${esc(r.name)}</button> · ${r.selector.kind==='all-cells'?'每個主格':'cell ('+esc(r.selector.cell.join(', '))+')'} · u ${r.divisions[0]}／v ${r.divisions[1]} · 引用：${u.guides.length} 參考線／${u.timbers.length} 角材</p>`;}).join('')}<div class="grid-rule-focus"><label>規則<select id="gridRuleFocusKey" data-rule-focus-key>${source.rules.map(r=>`<option value="${r.ruleKey}"${r.ruleKey===rule.ruleKey?' selected':''}>#${r.ruleKey} ${esc(r.name)}</option>`).join('')}</select></label><label>cell i<input id="gridRuleCellI" data-rule-cell-i value="${esc(cell[0])}" inputmode="numeric" maxlength="4096"></label><label>cell j<input id="gridRuleCellJ" data-rule-cell-j value="${esc(cell[1])}" inputmode="numeric" maxlength="4096"></label><button type="button" class="btn" data-rule-exact>完整定位這一格</button></div><p data-rule-focus-status role="status">${esc(owner?.focusStatus||'')}</p>${selected?`<p data-rule-selected>${esc(label(selected.ref,selected.name))} · ${selected.axis}=${selected.coordinate} mm · 可見 ${selected.segments.length} 段</p>`:''}</div>`;
  }
  function bind(pane,g){
    for(const input of pane.querySelectorAll('[data-rule-focus-key],[data-rule-cell-i],[data-rule-cell-j]'))input.addEventListener('input',()=>{if(owner&&current(owner)){owner.focusStatus='';pane.querySelector('[data-rule-focus-status]').textContent='';}});
    for(const button of pane.querySelectorAll('[data-rule-source]'))button.onclick=async()=>{const s=owner,mark=stamp(),r=Number(button.dataset.ruleSource);if(!s?.loaded||!current(s))return;
      button.disabled=true;try{await SourceInspectorApp.navigate({kind:'grid-source-rule',id:String(g.sourceSystem),fieldId:r},s.graph,{isCurrent:()=>current(s)&&stamp()===mark,beginNavigation:()=>current(s)&&stamp()===mark});}catch(error){toast(error.message);}finally{if(button.isConnected)button.disabled=false;}};
    const button=pane.querySelector('[data-rule-exact]');if(button)button.onclick=async()=>{const captured=owner,feedback=text=>{if(captured===owner&&current(captured))$('faceInspectorContent').querySelector('[data-rule-focus-status]').textContent=text;};try{
      const cell=['i','j'].map(a=>pane.querySelector('[data-rule-cell-'+a+']').value.trim());if(!cell.every(signed))throw Error('cell 須為 signed 64 位元整數；不使用抽樣序號。');
      refresh();const s=owner;if(!current(s))return;fe.ruleFocus={grid:g.id,rule:Number(pane.querySelector('[data-rule-focus-key]').value),cell};button.disabled=true;await query(s,fe.ruleFocus);
    }catch(error){feedback(error.message);}finally{if(button.isConnected)button.disabled=false;}};
  }
  async function readNative(target,selector,isCurrent=()=>true){
    const before=await apiRequest('source-inspect');if(!isCurrent()||!before.ok)return null;
    if(target.sourceFingerprint&&before.sourceFingerprint!==target.sourceFingerprint)throw Error('來源已變更，請重新開啟檢視。');
    const result=await apiRequest(`grid-rule-query ${target.kind} ${target.id} rule ${target.ruleKey} ${selector}`);if(!isCurrent())return null;
    const decoded=rows(result,target),after=await apiRequest('source-inspect');
    if(!isCurrent()||!after.ok||before.revision!==after.revision||before.sourceFingerprint!==after.sourceFingerprint)return null;
    return {rows:decoded,complete:result.complete!==false,requiredCells:result.requiredCells,stride:result.stride};
  }
  Object.assign(api,{refresh,clear,entries,find,select,draw,html,bind,readNative,presentationState,reloadNative});
})();
