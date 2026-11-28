/* R13 shared room/RC manual-data editor. Confirmation never creates RC geometry. */
(() => {
  'use strict';
  const R=GeometryReconstructionData, K=window.GeometryReconstructionValues, states=new WeakMap();
  const fields=[['bottom','Bottom','底高'],['top','Top','頂高'],['height','Height','高度'],['wallThickness','WallThickness','牆厚（選用）']];
  const templates={'room-height':fields,
    'rc-column':[['x','X','X 起點'],['y','Y','Y 起點'],['width','Width','寬'],['depth','Depth','深'],['bottom','Bottom','底高'],['top','Top','頂高'],['height','Height','高度']],
    'rc-beam':[['start','Start','軸向起點'],['end','End','軸向終點'],['center','Center','橫向中線'],['width','Width','寬'],['depth','Depth','樑深'],['bottom','Bottom','樑底'],['top','Top','樑頂']]};
  const title=kind=>({'room-height':'房間高度','rc-column':'RC 柱','rc-beam':'RC 樑'}[kind]);
  const position=key=>['bottom','top','x','y','start','end','center'].includes(key);
  const editPattern=/^rd(?:Name|Bottom|Top|Height|WallThickness|X|Y|Width|Depth|Start|End|Center|Axis|SpaceId)/;
  const clone=value=>JSON.parse(JSON.stringify(value));
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let binding=null;
  function data(){return ReferenceWorkspace.readFeatureAttachment(R.KIND)||R.empty();}
  function state(){const context=ReferenceWorkspace.context();if(!states.has(context))states.set(context,{id:null,open:false,draft:null,kind:'room-height'});return states.get(context);}
  function selected(value=data()){return value.records.find(record=>record.id===state().id)||null;}
  const readable=text=>String(text).replace(/^[A-Z][A-Z0-9_]*：/,'');
  function message(text,error=false){if(!binding)return;const node=binding.panel.querySelector('#rdStatus');if(node){node.textContent=readable(text);node.dataset.kind=error?'error':'';}}
  function editorHTML(value,retained=null){
    const record=selected(value)||retained;
    const fields=templates[record?.kind||'room-height'];
    return `<p class="rd-note">本專案的人工輸入；未附圖面／量測證據，也未持續關聯到目前面或圖頁。原字可先保存；帶入 3D 時再明選資料與已放置面。</p>
      <div class="rd-actions"><label class="rd-label">資料種類<select id="rdKind"><option value="room-height">房間高度</option><option value="rc-column">RC 柱</option><option value="rc-beam">RC 樑</option></select></label><button type="button" class="btn" id="rdAdd">新增資料</button></div>
      <label class="rd-label">本次明選資料<select id="rdSelect"><option value="">請選一筆資料</option>${value.records.map(item=>`<option value="${esc(item.id)}">${esc(item.name||item.id)}</option>`).join('')}${retained&&!selected(value)?`<option value="${esc(retained.id)}">${esc(retained.name)}（資料已不存在；未保存文字）</option>`:''}</select></label>
      <div id="rdEditor"${record?'':' hidden'}><label class="rd-label">名稱<input id="rdName" autocomplete="off"></label>
      ${record?.kind==='rc-beam'?'<label class="rd-label">樑的水平走向<select id="rdAxis"><option value="">尚未指定</option><option value="x">世界 X</option><option value="y">世界 Y</option></select></label>':''}
      ${record&&record.kind!=='room-height'?'<label class="rd-label">空間編號註記（選用；尚未確認該空間存在）<input id="rdSpaceId" type="text" inputmode="numeric" placeholder="本次不指定"></label>':''}
      <div class="rd-fields">${fields.map(([key,stem,label])=>`<section class="rd-field"><label class="rd-label">${label}<textarea id="rd${stem}Raw" rows="1" inputmode="decimal" autocomplete="off" aria-describedby="rd${stem}State" placeholder="尚未填寫"></textarea></label>
        <label class="rd-label">單位<select id="rd${stem}Unit"><option value="">尚未選單位</option><option value="mm">mm</option><option value="cm">cm</option></select></label>
        ${position(key)?`<label class="rd-label">位置基準<select id="rd${stem}Basis"><option value="unknown">基準未知，不能採用</option>${(['bottom','top'].includes(key)?['z']:['x','y'].includes(key)?[key]:['x','y']).map(axis=>`<option value="world-${axis}">明確使用世界 ${axis.toUpperCase()}</option>`).join('')}</select></label><label class="rd-label">基準說明<input id="rd${stem}Note" autocomplete="off" placeholder="世界座標基準；說明不換算座標"></label>`:''}
        <p id="rd${stem}State" class="rd-note"></p><button type="button" class="btn" id="rdConfirm${stem}">確認${label}</button></section>`).join('')}</div>
      <p id="rdDerivation" class="rd-note"></p><button id="rdConfirmDerived" type="button" class="btn" disabled>確認推導</button>
      <p class="rd-note">${record&&record.kind!=='room-height'?'RC 各尺寸須逐欄確認，位置須明選世界軸；確認只保存核對資料，沒有正式 RC 採用或帶入 3D。':'底高與高度必須確認。觀察值可先核對；帶入位置與推導另須明選世界 Z。基準說明不會換算座標。頂高僅作核對；牆厚空白時不建立材料牆。'}</p>
      <p id="rdPlanStatus" class="rd-note" role="status"></p>
      <div class="rd-actions"><button id="rdAdopt" type="button" class="btn" disabled${record&&record.kind!=='room-height'?' hidden':''}>明選這筆資料與目前面，帶入 3D</button><button id="rdDelete" type="button" class="btn">刪除此筆資料</button></div></div>
      <button id="rdReload" type="button" class="btn" hidden>載入已保存資料，放棄未保存文字</button>
      <p id="rdStatus" class="rd-status" role="status" aria-live="polite"></p>`;
  }
  function paneHTML(){return `<details class="ref-section rd-panel" id="rdPanel"${state().open?' open':''}><summary>補資料紀錄</summary>${editorHTML(data())}</details>`;}
  // Even textarea.value normalizes CR/CRLF to LF. Keep the exact source for
  // controls whose displayed value differs; a save is not an input event.
  const projectedText=new WeakMap();
  function fillText(control,original){
    control.value=original;
    if(control.value!==original)projectedText.set(control,{original,display:control.value});
    else projectedText.delete(control);
  }
  function readText(control){
    const projection=projectedText.get(control);
    if(projection&&projection.display===control.value)return projection.original;
    projectedText.delete(control);
    return control.value;
  }
  function fillControls(record){
    const q=id=>binding.panel.querySelector('#'+id);
    q('rdKind').value=state().kind;
    q('rdSelect').value=record?.id||'';q('rdEditor').hidden=!record;if(!record)return;
    fillText(q('rdName'),record.name);
    if(record.kind!=='room-height')q('rdSpaceId').value=record.spaceId===null?'':String(record.spaceId);
    if(record.kind==='rc-beam')q('rdAxis').value=record.axis??'';
    for(const [key,stem] of templates[record.kind]){const field=record.fields[key];fillText(q('rd'+stem+'Raw'),field.raw);q('rd'+stem+'Unit').value=field.unit??'';
      if(position(key)){q('rd'+stem+'Basis').value=field.basis.kind;fillText(q('rd'+stem+'Note'),field.basis.note);}}
  }
  function render(){
    if(!binding||binding.context!==ReferenceWorkspace.context())return;
    const value=data(),record=selected(value),ui=state(),retained=ui.draft?JSON.parse(ui.draft.base):null,display=record||retained;
    binding.panel.innerHTML='<summary>補資料紀錄</summary>'+editorHTML(value,retained);binding.panel.open=ui.open;binding.kind=display?.kind||'room-height';
    binding.snapshot=JSON.stringify(record);binding.signature=JSON.stringify(value);fillControls(display);
    if(ui.draft&&ui.draft.id===display?.id){fillControls({...display,...ui.draft.action,fields:{...display.fields,...ui.draft.action.fields}});binding.snapshot=ui.draft.base;}
    update();
    if(ui.draft)message('尚有未保存文字，已保留在此編輯區；不會覆蓋已變更的資料。可先複製文字，再明選載入已保存資料。',true);
  }
  function collect(){
    const q=id=>binding.panel.querySelector('#'+id),id=q('rdSelect')?.value;
    if(!id)return null;
    const result={type:'edit',id,name:readText(q('rdName')),fields:{}};
    for(const [key,stem] of templates[binding.kind])result.fields[key]={raw:readText(q('rd'+stem+'Raw')),unit:q('rd'+stem+'Unit').value||null,
      basis:position(key)?{kind:q('rd'+stem+'Basis').value,note:readText(q('rd'+stem+'Note'))}:{kind:'distance',note:''}};
    if(binding.kind!=='room-height'){const raw=q('rdSpaceId').value;result.spaceId=raw===''?null:/^[1-9][0-9]*$/.test(raw)?Number(raw):raw;}
    if(binding.kind==='rc-beam')result.axis=q('rdAxis').value||null;
    return result;
  }
  function sameText(action,record){
    return !!record&&action.id===record.id&&action.name===record.name&&
      (record.kind==='room-height'||action.spaceId===record.spaceId)&&(record.kind!=='rc-beam'||action.axis===record.axis)&&templates[record.kind].every(([key])=>{
      const a=action.fields[key],b=record.fields[key];return a.raw===b.raw&&a.unit===b.unit&&JSON.stringify(a.basis)===JSON.stringify(b.basis);
    });
  }
  function assertOwner(readOnly=false){
    if(!binding||binding.context!==ReferenceWorkspace.context()||binding.token!==ReferenceWorkspace.getProjectState().contextToken)
      throw Error('補資料編輯屬於另一個專案，未寫入。請重新開啟底圖頁。');
    if(!readOnly&&ReferenceWorkspace.getModelOperationState().blocked)throw Error('請先完成目前操作，再保存補資料文字。');
  }
  function releaseForeignPane(){
    // Preserve even a last edit that has not delivered an input event. Never
    // flush it to the new project (record IDs may be identical there).
    const action=collect(),before=JSON.parse(binding.snapshot);
    if(action&&before&&!sameText(action,before))
      states.get(binding.context).draft={id:action.id,action,base:binding.snapshot};
    binding=null;
  }
  function flush(){
    if(!binding)return;
    if(!binding.panel.isConnected&&binding.context!==ReferenceWorkspace.context()){releaseForeignPane();return;}
    const action=collect();if(!action)return;
    const originalBinding=binding,ui=states.get(binding.context);
    binding.writing=true;
    try {
      assertOwner(true);
      const current=data().records.find(record=>record.id===action.id);
      if(JSON.stringify(current||null)!==binding.snapshot)throw Error('房間資料已變更或復原，未以舊欄位覆蓋。未保存文字仍保留，請核對後處理。');
      if(sameText(action,current)){ui.draft=null;update();return;}
      assertOwner();
      const next=ReferenceWorkspace.reconstructionEdit(action,binding.token);
      binding.snapshot=JSON.stringify(next.records.find(record=>record.id===action.id));binding.signature=JSON.stringify(next);state().draft=null;
      update();
    } catch(error){if(ui)ui.draft={id:action.id,action:clone(action),base:originalBinding.snapshot};message(error.message,true);update();throw error;}
    finally{originalBinding.writing=false;}
  }
  function update(){
    if(!binding||binding.context!==ReferenceWorkspace.context())return;
    const value=data(),record=selected(value),q=id=>binding.panel.querySelector('#'+id);
    let blocked=ReferenceWorkspace.getModelOperationState().blocked;
    q('rdAdd').disabled=blocked;q('rdSelect').disabled=blocked;q('rdKind').disabled=blocked;
    q('rdReload').hidden=!state().draft;q('rdReload').disabled=blocked||binding.composing;
    if(!record)return;
    const fields=templates[record.kind];
    for(const [key,stem] of fields){const field=record.fields[key],confirmation=field.confirmation;
      q('rd'+stem+'State').textContent=confirmation?`${confirmation.kind==='derived'?'推導已確認':'觀察值已確認'}：${confirmation.value} mm${field.basis.kind==='unknown'?'；位置基準未知，不能推導或採用':''}`:'原字串已保存；尚未確認';
      q('rdConfirm'+stem).disabled=blocked||binding.composing||!!state().draft;
    }
    let candidate=null,why='只有兩個直接確認值與一個空白欄位時，才有可確認的推導。';
    try{candidate=R.derivation(record);if(candidate)why=`${fields.find(item=>item[0]===candidate.field)[2]}可推導為 ${candidate.value} mm；${record.kind==='rc-beam'?'樑底＋樑深＝樑頂':'底高＋高度＝頂高'}，請另行確認。`;}
    catch(error){why=readable(error.message);}
    binding.derivation=candidate;q('rdDerivation').textContent=why;
    q('rdConfirmDerived').disabled=blocked||binding.composing||!candidate||!!state().draft;
    let ready=false,planStatus='本次明選高度可採用；建立前仍須核對放置面、投影與各面用途。';
    try{if(record.kind!=='room-height'){R.rcValues(record);planStatus='RC 尺寸與位置基準已核對；目前只保存資料，尚未建立柱樑模型。';}
      else {const plan=R.plan(value,record.id);ready=true;if(plan.completeness==='defined-subset')planStatus='本筆仍有待補或待核對欄位；在建模頁明選「只建立已定資料」後，才能建立條件結果。';}}catch(error){
      planStatus=readable(error.message);
      if(error.code==='SUM_CONFLICT'){
        const middle=record.kind==='rc-beam'?'depth':'height',labels=record.kind==='rc-beam'?['樑底','樑深','樑頂']:['底高','高度','頂高'];
        const number=key=>{const field=record.fields[key];return field.raw===''?field.confirmation.value:K.decimal(field.raw,field.unit,key===middle);};
        const bottom=number('bottom'),height=number(middle),top=number('top'),expected=bottom+height;
        planStatus=`關係：${labels[0]}＋${labels[1]}＝${labels[2]}。${labels[0]} ${bottom} mm（人工輸入）＋${labels[1]} ${height} mm（人工輸入）＝${expected} mm，與${labels[2]} ${top} mm（人工輸入）不符；${labels[2]}－（${labels[0]}＋${labels[1]}）的實際差值為 ${top-expected} mm。請核對三欄原件；不自動選擇或覆蓋任何一欄。`;
      }
    }
    q('rdPlanStatus').textContent=planStatus;
    q('rdAdopt').disabled=blocked||binding.composing||!ready||!!state().draft;
    q('rdAdopt').hidden=record.kind!=='room-height';
    q('rdDelete').disabled=blocked||binding.composing;
  }
  function requireCommittedText(){if(binding.composing)throw Error('文字仍在組字，請先完成輸入再確認或帶入 3D。');flush();}
  function onEdit(){try{flush();message('原字串已記錄到目前專案；確認後才可採用。');}catch(error){message(error.message,true);}}
  async function onClick(event){
    const button=event.target.closest('button');if(!button||!binding?.panel.contains(button))return;
    try {
      assertOwner();const id=button.id;
      if(id==='rdReload'){
        if(binding.composing)throw Error('請先完成組字，再決定是否放棄未保存文字。');
        state().draft=null;render();message('已明選載入目前保存資料；未保存文字已放棄。');return;
      }
      if(id==='rdAdd'){
        flush();const kind=state().kind,next=ReferenceWorkspace.reconstructionEdit({type:'create',kind,name:title(kind)+' '+data().nextId},binding.token);
        state().id=next.records.at(-1).id;state().open=true;render();binding.panel.querySelector('#rdName').focus();return;
      }
      requireCommittedText();const record=selected();if(!record)throw Error('請先明選一筆房間高度資料。');
      if(id==='rdAdopt'){
        R.plan(data(),record.id);const surface=feSurf(binding.bid);
        if(!surface)throw Error('此面尚未放置，請先完成放置；原始補資料仍可保存。');
        await window.SpaceModelWorkspace.openReconstruction(record.id,surface.id);return;
      }
      let action=null;
      if(id==='rdDelete')action={type:'delete',id:record.id};
      else if(id==='rdConfirmDerived'){
        const candidate=R.derivation(record);if(!candidate)throw Error('目前沒有唯一的待確認推導。');
        action={type:'confirm-derived',id:record.id,field:candidate.field};
      } else {const field=templates[record.kind].find(item=>id==='rdConfirm'+item[1]);if(field)action={type:'confirm',id:record.id,field:field[0]};}
      if(!action)return;
      ReferenceWorkspace.reconstructionEdit(action,binding.token);render();message(action.type==='delete'?'資料已刪除；既有模型會保留缺失提示，可復原。':'此值已確認；修改輸入或基準後須重新確認。');
    }catch(error){message(error.message,true);}
  }
  function bindPane(pane,bid){
    const panel=pane.querySelector('#rdPanel');if(!panel)return;
    if(binding&&binding.context!==ReferenceWorkspace.context())releaseForeignPane();
    else if(binding){try{flush();}catch(_){} }
    binding={panel,bid,context:ReferenceWorkspace.context(),token:ReferenceWorkspace.getProjectState().contextToken,composing:false,snapshot:null,signature:null};
    render();
    panel.addEventListener('toggle',()=>{if(binding?.panel===panel)state().open=panel.open;});
    panel.addEventListener('input',event=>{if(binding?.panel===panel&&editPattern.test(event.target.id))onEdit();});
    panel.addEventListener('change',event=>{
      if(binding?.panel!==panel)return;
      if(event.target.id==='rdKind'){if(R.KINDS.includes(event.target.value))state().kind=event.target.value;}
      else if(event.target.id==='rdSelect'){
        // Each input event already stores raw text; a rejected draft must remain visible.
        if(state().draft){event.target.value=state().id||'';message('目前文字尚未保存，請先修正再切換資料。',true);return;}
        state().id=event.target.value||null;render();
      }else if(editPattern.test(event.target.id))onEdit();
    });
    panel.addEventListener('compositionstart',()=>{if(binding?.panel===panel){binding.composing=true;update();}});
    panel.addEventListener('compositionend',()=>{if(binding?.panel===panel){binding.composing=false;onEdit();}});
    panel.addEventListener('click',onClick);
  }
  function hasReview(modelId){return data().reviews.some(review=>review.modelId===modelId);}
  function reviewSummary(modelId){
    const value=data(),review=value.reviews.find(item=>item.modelId===modelId);if(!review)return '';
    const status=R.reviewStatus(value,review);
    const scope=review.scope[0],label=key=>fields.find(item=>item[0]===key)?.[2]||key;
    const omitted=scope.omitted.map(item=>`${label(item.field)}：${item.reason==='missing-value'?'缺值':'需複核'}`).join('；');
    const checks=scope.checks.map(item=>`${label(item.field)}：僅人工核對（${item.value} mm），未直接供值`).join('；');
    const summary={current:review.completeness==='defined-subset'?'僅依本次已定資料的條件結果；明選 1 筆仍有待補／待核對欄位':'明選 1 筆房間高度已核對；不代表整張圖完整',stale:'房間高度核對已過期；模型保留原確認版本',missing:'房間高度來源資料缺失；模型保留原確認版本'}[status];
    return summary+(omitted?'。未納入：'+omitted:'')+(checks?'。'+checks:'');
  }
  window.addEventListener('project-local-history',event=>{
    if(!binding||binding.context!==ReferenceWorkspace.context()||binding.writing)return;
    const detail=event?.detail;
    if(!detail||detail.previousContextToken!==binding.token||detail.contextToken!==ReferenceWorkspace.getProjectState().contextToken)return;
    const action=collect(),before=JSON.parse(binding.snapshot),ui=state();
    if(action&&before&&(binding.composing||!sameText(action,before)))ui.draft={id:action.id,action:clone(action),base:binding.snapshot};
    binding.token=detail.contextToken;
    if(!binding.composing&&!ui.draft)render();else update();
  });
  window.addEventListener('project-info-changed',()=>{
    if(!binding||binding.writing)return;
    if(binding.context!==ReferenceWorkspace.context()){releaseForeignPane();return;}
    if(!binding.panel.isConnected)return;
    if(JSON.stringify(data())!==binding.signature&&!binding.composing&&!state().draft)render();else update();
  });
  window.ReconstructionWorkspace={paneHTML,bindPane,flush,hasReview,reviewSummary};
})();
