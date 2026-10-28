/* Face properties UI-1: form definitions only; native owns geometry and support. */
"use strict";
window.PanelFillWorkspace = (() => {
  const A=window.PanelFillAdapter,clone=A.clone,esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let active=null;const retiredSessions=new Set();
  const scalar=(value,label)=>{
    if(!/^-?\d+$/.test(String(value)))throw new Error(label+'須明設整數 mm。');
    const n=Number(value);if(!Number.isSafeInteger(n)||Math.abs(n)>100000000)throw new Error(label+'超出 D1 範圍。');return n;
  };
  const list=v=>Array.isArray(v)?v:[];
  const material=r=>r.value?{...r.value,fingerprint:r.fingerprint,archived:r.archived}:r;
  const ref=r=>JSON.stringify([r.id,r.version]);
  const finishRecords=s=>s.snapshot.finishSurfaces.filter(r=>r.boundaryId===s.boundaryId);
  const fillRecords=(s,id)=>s.snapshot.panelFills.filter(r=>r.definition.finishSurfaceId===id);
  const hostRecords=(s,id)=>s.snapshot.derivedPlacements.filter(r=>r.definition.fillId===id);
  const parameters=s=>list(s.sources?.parameters).flatMap(p=>list(p.fields).filter(f=>f.type==='dimension').map(f=>({
    key:p.id+':'+f.id,label:`${p.name} / ${f.name}（${p.id}:${f.id}）`,parameterId:p.id,fieldId:f.id,value:f.value})));
  function sourceDraft(value,host=false) {
    if(typeof value==='number')return {kind:'literal',value:String(value),original:value};
    if(!value)return {kind:'literal',value:'',original:undefined};
    if(value.parameterId!==undefined)return {kind:'parameter',value:value.parameterId+':'+value.fieldId,original:clone(value)};
    if(host&&value.kind==='literal')return {kind:'literal',value:String(value.value),original:clone(value)};
    if(host&&value.kind==='spec')return {kind:'spec',value:value.name,original:clone(value)};
    if(host&&value.kind==='material')return {kind:'material',value:ref(value),original:clone(value)};
    throw new Error('來源型別不受本片支援；保留原定義，禁止轉換成明設值。');
  }
  function sourceValue(source,host=false) {
    let result;
    if(source.kind==='literal')result=scalar(source.value,'明設尺寸');
    else if(source.kind==='parameter'){
      if(!/^\d+:\d+$/.test(source.value))throw new Error('請明選尺寸參數欄位。');
      const [parameterId,fieldId]=source.value.split(':').map(Number);
      result={...(host?{kind:'parameter'}:{}),parameterId,fieldId};
    }else if(host&&source.kind==='spec'){
      if(!source.value)throw new Error('請明選具名尺寸。');result={kind:'spec',name:source.value};
    }else if(host&&source.kind==='material'){
      const value=JSON.parse(source.value||'null');if(!Array.isArray(value)||value.length!==2)throw new Error('請明選固定角材材料版本。');
      result={kind:'material',id:value[0],version:value[1],field:'B'};
    }else throw new Error('未知尺寸來源，禁止提交。');
    // Preserve literal-vs-source identity on an unchanged form, including kind:literal.
    if(host&&source.original?.kind==='literal'&&source.kind==='literal'&&source.original.value===result)return clone(source.original);
    return result;
  }
  function selectFinish(s,idValue) {
    const record=finishRecords(s).find(r=>String(r.id)===idValue),value=record?A.definition(record,'finish'):null;
    s.selection={finish:record?.id??null,fill:null,host:null};
    s.draft={finishId:value?.id??s.ids.finishSurface,name:value?.name??'',origin:value?.frame.origin.map(String)??['','',''],
      U:value?.frame.U??'',V:value?.frame.V??'',N:value?.frame.N??'',side:value?String(value.structureSide):'',
      obstacles:value?clone(value.obstacles):[],fill:false,host:false,remove:null};
    selectFill(s,record?String(fillRecords(s,record.id)[0]?.definition.id??'new'):'new');
  }
  function selectFill(s,idValue) {
    const record=fillRecords(s,s.draft.finishId).find(r=>String(r.definition.id)===idValue),value=record?.definition;
    s.selection.fill=value?.id??null;s.selection.host=null;
    Object.assign(s.draft,{fill:!!value,fillId:value?.id??s.ids.panelFill,panel:value?ref(value.panel):'',lengthAlong:value?.lengthAlong??'',
      fillOrigin:value?.origin.map(String)??['',''],gap:sourceDraft(value?.gap),pattern:value?.pattern??'',
      staggerAxis:value?.stagger?.axis??'',stagger:sourceDraft(value?.stagger?.value),
      threshold:value?value.threshold.parameterId+':'+value.threshold.fieldId:'',remove:null});
    selectHost(s,value?String(hostRecords(s,value.id)[0]?.definition.id??'new'):'new');
  }
  function selectHost(s,idValue) {
    const record=hostRecords(s,s.draft.fillId).find(r=>String(r.definition.id)===idValue),value=record?.definition;
    s.selection.host=value?.id??null;Object.assign(s.draft,{host:!!value,hostId:value?.id??s.ids.placement,h:sourceDraft(value?.h,true),remove:null});
  }
  function operations(s) {
    const d=s.draft,ops=[],defs=s.snapshot;
    if(d.remove){const [kind,id]=d.remove;return [{op:'delete-'+kind,id}];}
    if(!d.name.trim())throw new Error('請填完成面名稱。');
    const axes=['+X','-X','+Y','-Y','+Z','-Z'];if(![d.U,d.V,d.N].every(a=>axes.includes(a)))throw new Error('請明選 U、V、N 三個軸向。');
    if(!['-1','1'].includes(d.side))throw new Error('請明選結構側。');
    const finish={id:d.finishId,name:d.name,boundaryId:s.boundaryId,frame:{origin:d.origin.map(v=>scalar(v,'框架原點')),U:d.U,V:d.V,N:d.N},
      structureSide:Number(d.side),obstacles:clone(d.obstacles)};
    const oldFinish=defs.finishSurfaces.find(r=>r.id===finish.id);
    if(A.canonical(finish)!==A.canonical(oldFinish?A.definition(oldFinish,'finish'):null))ops.push({op:'put-finish-surface',value:finish});
    if(d.fill){
      const panel=JSON.parse(d.panel||'null');if(!Array.isArray(panel)||panel.length!==2)throw new Error('請明選已發布的固定面材版本。');
      if(!['u','v'].includes(d.lengthAlong))throw new Error('請明選面材長邊軸向，正方形面材亦需明選。');
      if(!['straight','stagger'].includes(d.pattern))throw new Error('請明選鋪排方式。');
      if(!/^\d+:\d+$/.test(d.threshold))throw new Error('請明選支撐門檻 X 的尺寸參數欄位。');
      const [parameterId,fieldId]=d.threshold.split(':').map(Number);
      const fill={id:d.fillId,finishSurfaceId:d.finishId,panel:{id:panel[0],version:panel[1]},lengthAlong:d.lengthAlong,
        origin:d.fillOrigin.map(v=>scalar(v,'鋪排原點')),gap:sourceValue(d.gap),pattern:d.pattern,threshold:{parameterId,fieldId}};
      if(d.pattern==='stagger'){if(!['u','v'].includes(d.staggerAxis))throw new Error('請明選交丁軸向。');fill.stagger={axis:d.staggerAxis,value:sourceValue(d.stagger)};}
      const previous=defs.panelFills.find(r=>r.definition.id===fill.id)?.definition;
      if(A.canonical(fill)!==A.canonical(previous))ops.push({op:'put-panel-fill',value:fill});
      if(d.host){const host={id:d.hostId,fillId:d.fillId,h:sourceValue(d.h,true)},previous=defs.derivedPlacements.find(r=>r.definition.id===d.hostId)?.definition;
        if(A.canonical(host)!==A.canonical(previous))ops.push({op:'put-derived-placement',value:host});}
      else if(s.selection.host!==null)throw new Error('已有宿主請使用「刪除宿主候選」，不可暗中移除。');
    }else if(s.selection.fill!==null)throw new Error('已有鋪排請使用「刪除鋪排候選」，不可暗中移除。');
    return ops;
  }
  const input=(label,key,value,attrs='')=>`<label>${esc(label)}<input data-pf-field="${key}" value="${esc(value)}" ${attrs}></label>`;
  const select=(label,key,value,options)=>`<label>${esc(label)}<select data-pf-field="${key}">${options.map(([v,t])=>`<option value="${esc(v)}"${String(v)===String(value)?' selected':''}>${esc(t)}</option>`).join('')}</select></label>`;
  const options=(items,label)=>[['','請明選'],...items.map(item=>[item.key,label?label(item):item.label])];
  function sourceFields(s,label,key,d,host=false) {
    const kinds=[['literal','明設整數 mm'],['parameter','尺寸參數欄位'],...(host?[['spec','具名尺寸'],['material','固定角材版本 B']]:[])];
    let value;
    if(d.kind==='literal')value=input('明設值',key+'.value',d.value,'inputmode="numeric"');
    else if(d.kind==='parameter')value=select('來源欄位',key+'.value',d.value,options(parameters(s)));
    else if(d.kind==='spec')value=select('具名尺寸',key+'.value',d.value,[['','請明選'],...list(s.sources.specs).map(r=>[r.name,r.name+' = '+r.value+' mm'])]);
    else value=select('固定材料版本',key+'.value',d.value,[['','請明選'],...list(s.sources.materials).map(material).filter(r=>r.kind==='timber').map(r=>[ref(r),`${r.name} · ${r.id} v${r.version} · B=${r.B}`])]);
    let typed;try{typed=sourceValue(d,host);}catch(_){typed={kind:d.kind,input:d.value};}
    return `<fieldset class="pf-source"><legend>${esc(label)}</legend>${select('來源種類',key+'.kind',d.kind,kinds)}${value}<output data-pf-source="${key}">定義來源：${esc(JSON.stringify(typed))}</output></fieldset>`;
  }
  function form(s) {
    const d=s.draft,axes=[['','請明選'],...['+X','-X','+Y','-Y','+Z','-Z'].map(a=>[a,a])];
    const finishes=finishRecords(s),fills=fillRecords(s,d.finishId),hosts=hostRecords(s,d.fillId);
    const obstacleOptions=[...list(s.objects.columns).map(r=>({ref:'c'+r.id,name:r.name||'柱 '+r.id})),...list(s.objects.beams).map(r=>({ref:'b'+r.id,name:r.name||'樑 '+r.id}))];
    for(const value of d.obstacles)if(!obstacleOptions.some(r=>r.ref===value))obstacleOptions.push({ref:value,name:value+'（目前來源不存在）'});
    const disabled=['loading','confirming','unknown'].includes(s.phase)||s.retired;
    return `<fieldset class="pf-form"${disabled?' disabled':''}><legend>本面定義</legend>
      ${select('完成面','selectFinish',s.selection.finish??'new',[...finishes.map(r=>[r.id,`${r.name} · #${r.id}`]),['new','新增完成面']])}
      ${d.remove?`<p class="pf-warning">待刪除 ${esc(d.remove[0])} #${esc(d.remove[1])}。預覽會檢查全部依賴，確認前正式資料保持不變。</p><button type="button" data-pf-action="restore-edit">返回編輯</button>`:`
      ${input('完成面名稱','name',d.name,'maxlength="160"')}
      <fieldset><legend>明設完成面框架（值快照，不會改寫投影定義）</legend><div class="pf-fields">${d.origin.map((v,i)=>input(['O.x mm','O.y mm','O.z mm'][i],'origin.'+i,v,'inputmode="numeric"')).join('')}${['U','V','N'].map(k=>select(k+' 軸向',k,d[k],axes)).join('')}${select('結構側','side',d.side,[['','請明選'],['1','+N 側'],['-1','−N 側']])}</div></fieldset>
      <fieldset><legend>明選障礙（只有勾選來源參與）</legend><div class="pf-obstacles">${obstacleOptions.map(r=>`<label><input type="checkbox" data-pf-obstacle="${esc(r.ref)}"${d.obstacles.includes(r.ref)?' checked':''}>${esc(r.name)} · ${esc(r.ref)}</label>`).join('')||'<p>目前沒有柱樑；空集合不套用障礙。</p>'}</div></fieldset>
      ${s.selection.finish!==null?'<button type="button" data-pf-action="delete-finish">刪除此完成面候選</button>':''}
      ${select('鋪排定義','selectFill',s.selection.fill??'new',[...fills.map(r=>[r.definition.id,'鋪排 #'+r.definition.id]),['new','新增鋪排']])}
      <label class="pf-toggle"><input type="checkbox" data-pf-field="fill"${d.fill?' checked':''}>設定鋪排（PF-2／3）</label>
      ${d.fill?`<fieldset><legend>鋪排 #${d.fillId}</legend><div class="pf-fields">${select('固定面材版本','panel',d.panel,[['','請明選'],...list(s.sources.materials).map(material).filter(r=>r.kind==='panel').map(r=>[ref(r),`${r.name} · ${r.id} v${r.version} · ${r.width}×${r.length} · 厚 ${r.thickness??'未設'}`])])}${select('面材長邊軸向','lengthAlong',d.lengthAlong,[['','請明選'],['u','u 軸'],['v','v 軸']])}${d.fillOrigin.map((v,i)=>input(['鋪排原點 u mm','鋪排原點 v mm'][i],'fillOrigin.'+i,v,'inputmode="numeric"')).join('')}${select('鋪排方式','pattern',d.pattern,[['','請明選'],['straight','正排'],['stagger','交丁']])}${select('支撐門檻 X（尺寸參數）','threshold',d.threshold,options(parameters(s)))}</div>
      ${sourceFields(s,'板縫 gap','gap',d.gap)}${d.pattern==='stagger'?select('交丁軸向','staggerAxis',d.staggerAxis,[['','請明選'],['u','u 軸'],['v','v 軸']])+sourceFields(s,'交丁量','stagger',d.stagger):''}
      ${s.selection.fill!==null?'<button type="button" data-pf-action="delete-fill">刪除此鋪排候選</button>':''}
      ${select('宿主定義','selectHost',s.selection.host??'new',[...hosts.map(r=>[r.definition.id,'宿主 #'+r.definition.id]),['new','新增宿主']])}
      <label class="pf-toggle"><input type="checkbox" data-pf-field="host"${d.host?' checked':''}>設定派生宿主（PF-H）</label>
      ${d.host?sourceFields(s,'角材層厚 h（不暗設為 0）','h',d.h,true):''}
      ${s.selection.host!==null?'<button type="button" data-pf-action="delete-host">刪除此宿主候選</button>':''}</fieldset>`:''}`}</fieldset>`;
  }
  function exact(value) {return typeof value==='object'?JSON.stringify(value):String(value??'未提供');}
  const table=(headers,rows)=>`<div class="pf-table-scroll"><table><thead><tr>${headers.map(h=>'<th scope="col">'+esc(h)+'</th>').join('')}</tr></thead><tbody>${rows.map(row=>'<tr>'+row.map(v=>'<td>'+esc(exact(v))+'</td>').join('')+'</tr>').join('')}</tbody></table></div>`;
  function picture(fill) {
    const d=fill.derived;if(d?.error)return '';
    const loops=list(d?.tiles).flatMap(t=>list(t.fragments).map(f=>f.outer));
    const points=loops.flat();if(!points.length)return '<p>原生結果：零片。</p>';
    // Viewport arithmetic only. Never create/cut geometry or recompute native values.
    const display=points.map(p=>p.map(v=>Number(v)));
    if(display.some(p=>p.length!==2||p.some(v=>!Number.isSafeInteger(v))))return '<p>此座標無法安全繪圖，以下保留完整精確資料。</p>';
    const xs=display.map(p=>p[0]),ys=display.map(p=>p[1]),x=Math.min(...xs),y=Math.min(...ys),width=Math.max(...xs)-x,height=Math.max(...ys)-y;
    const paths=list(d.tiles).flatMap(t=>list(t.fragments).map(f=>`<path d="${[f.outer,...list(f.holes)].map(loop=>'M '+loop.map(p=>p.map(esc).join(' ')).join(' L ')+' Z').join(' ')}" fill-rule="evenodd"><title>片 ${esc(JSON.stringify(f.key))} · 面積 ${esc(f.area)} mm²</title></path>`)).join('');
    const seams=list(d.effectiveSeams).map(seam=>`<line x1="${esc(seam.axis==='u'?seam.coordinate:seam.range[0])}" y1="${esc(seam.axis==='u'?seam.range[0]:seam.coordinate)}" x2="${esc(seam.axis==='u'?seam.coordinate:seam.range[1])}" y2="${esc(seam.axis==='u'?seam.range[1]:seam.coordinate)}"><title>${esc(JSON.stringify(seam))}</title></line>`).join('');
    return `<svg class="pf-layout" role="img" aria-label="原生裁片與有效板縫；支撐狀態另列文字" viewBox="${x} ${y} ${width||1} ${height||1}" preserveAspectRatio="xMidYMid meet"><g class="pf-tiles">${paths}</g><g class="pf-seams">${seams}</g></svg>`;
  }
  function results(s) {
    const state=s.candidate?.after||(['editing','committed'].includes(s.phase)?s.snapshot:null);
    if(!state)return '<p>尚無目前輸入的原生結果。</p>';
    const finishes=state.finishSurfaces.filter(f=>f.boundaryId===s.boundaryId),ids=new Set(finishes.map(f=>f.id));
    const fills=state.panelFills.filter(f=>ids.has(f.definition.finishSurfaceId)),fillIds=new Set(fills.map(f=>f.definition.id));
    return `<section class="pf-results" aria-label="原生完成面結果"><h3>${s.candidate?'候選結果（尚未套用）':'正式來源結果'}</h3>
      ${finishes.map(f=>`<details><summary>${esc(f.name)} · 完成面 #${f.id} · ${f.derived?.error?'錯誤':'原生框架與障礙'}</summary>${table(['欄位','精確原生值'],[['frame',f.frame],['結構側',f.structureSide],['明選障礙',f.obstacles],['region',f.derived?.region],['障礙判定',f.derived?.obstacles],...(f.derived?.error?[['錯誤',f.derived.error]]:[])])}</details>`).join('')}
      ${fills.map(f=>{const d=f.derived;return `<article data-pf-fill-result="${f.definition.id}"><h4>鋪排 #${f.definition.id}</h4>${d?.error?'<p role="alert">原生錯誤：'+esc(d.error)+'</p>':`${picture(f)}<p>片數 ${esc(d.tileCount)} · 裁片數 ${esc(d.fragmentCount)} · 整片 ${esc(d.wholeCount)} · 厚 ${esc(d.thickness)} mm</p>${table(['裁片完整 key','面積 mm²'],list(d.tiles).flatMap(t=>list(t.fragments).map(p=>[p.key,p.area])))}<h5>有效板縫／支撐</h5>${table(['seam','區間','左側實寬 mm','右側實寬 mm','判定'],list(d.support).map(p=>[p.seam,p.range,p.left,p.right,p.supported?'支撐足夠':'支撐不足（可保存）']))}<details><summary>完整板縫鍵、非板縫與障礙分層</summary>${table(['類型','精確原生值'],[['有效板縫',d.effectiveSeams],['非板縫（不是支撐不足）',d.nonSeams],['非板縫原因',d.nonSeamReason],['障礙分層',d.obstacles]])}</details>`}<details><summary>定義來源（與有效值分開）</summary><pre>${esc(JSON.stringify(f.definition,null,2))}</pre></details></article>`;}).join('')}
      ${state.derivedPlacements.filter(h=>fillIds.has(h.definition.fillId)).map(h=>`<details><summary>宿主 #${h.definition.id} · ${h.derived?.error?'錯誤':'原生 h／框架／完整邊鍵'}</summary>${table(['欄位','精確原生值'],[['h 來源',h.definition.h],['h 有效值',h.derived?.h],['frame',h.derived?.frame],['components／完整邊鍵',h.derived?.components],...(h.derived?.error?[['錯誤',h.derived.error]]:[])])}</details>`).join('')}</section>`;
  }
  function display() {
    if(!active)return;const pane=document.querySelector('#faceInspectorContent [data-fi-pane="prop"]');if(pane)render(pane,active.boundaryId,true);
  }
  function render(pane,bid,force=false) {
    const s=active;if(!s||s.boundaryId!==Number(bid))return false;
    if(pane.id==='faceInspectorContent')pane=pane.querySelector('[data-fi-pane="prop"]')||pane;
    const previous=pane.querySelector('[data-pf-workspace]');if(!force&&previous===s.renderedRegion)return true;
    const focused=previous?.contains(document.activeElement)?document.activeElement:null;
    const focusField=focused?.dataset.pfField,focusAction=focused?.dataset.pfAction,focusObstacle=focused?.dataset.pfObstacle;
    const focusTitle=focused?.id==='pfTitle',selection=focused?.tagName==='INPUT'?[focused.selectionStart,focused.selectionEnd]:null;
    const first=!previous;
    pane.innerHTML=`<section class="pf-workspace" data-pf-workspace="${s.boundaryId}" aria-labelledby="pfTitle"><div class="pf-heading"><h2 id="pfTitle" tabindex="-1">完成面與鋪排</h2><button type="button" data-pf-action="close"${['confirming','unknown'].includes(s.phase)?' disabled':''}>返回面設定</button></div>
      <p class="pf-status" data-pf-status="${s.phase}" role="status" aria-live="polite">${esc(s.reason)}</p>
      ${s.draft?form(s):''}
      <details class="pf-source-preparation"><summary>來源與本片能力</summary><p>材料與尺寸參數須先在既有工程規格獨立確認。取消本次鋪排不會撤回先前已正式確認的來源。</p><button type="button" data-pf-action="sources"${['confirming','unknown'].includes(s.phase)?' disabled':''}>前往既有工程規格準備來源</button><p>本片：完成面、鋪排、板縫支撐與派生宿主（PF1–3＋PF-H）。PF-6 角材建議、PF-4 主格轉接、PF-5 空間流程尚未提供，沒有可執行動作。整體 complete:false。</p><p>服務支援：${esc(s.contract?.supportedActions.join('、')??'尚未取得相容契約')}；範圍完整：${s.contract?String(s.contract.completeForScope):'未知'}。</p></details>
      ${s.draft?results(s):''}
      ${(s.candidate?.violations?.length||s.candidate?.uiContract.errors.length)?`<section class="pf-diagnostics" role="alert"><h3>原生診斷</h3><pre>${esc(JSON.stringify({violations:s.candidate?.violations,errors:s.candidate?.uiContract.errors},null,2))}</pre></section>`:''}
      <div class="pf-actions"><button type="button" data-pf-action="preview"${!s.draft||s.retired||['loading','previewing','confirming','unknown'].includes(s.phase)?' disabled':''}>預覽</button><button type="button" data-pf-action="confirm"${s.phase!=='confirmable'||s.retired?' disabled':''}>確認一次變更</button><button type="button" data-pf-action="cancel"${['confirming','unknown'].includes(s.phase)?' disabled':''}>取消／返回</button></div></section>`;
    const region=pane.querySelector('[data-pf-workspace]');
    s.renderedRegion=region;
    region.addEventListener('input',event=>update(s,event));region.addEventListener('change',event=>update(s,event));
    region.addEventListener('click',event=>{const button=event.target.closest('[data-pf-action]');if(button&&!button.disabled){event.preventDefault();act(s,button.dataset.pfAction);}});
    region.addEventListener('keydown',event=>{
      if(event.isComposing||event.keyCode===229)return;
      if(event.key==='Escape'){event.preventDefault();event.stopPropagation();close();}
      // No implicit submit: Enter in an input (including IME completion) cannot confirm.
      if(event.key==='Enter'&&event.target.matches('input,select,textarea'))event.preventDefault();
    });
    let focus;
    if(focusField)focus=[...region.querySelectorAll('[data-pf-field]')].find(e=>e.dataset.pfField===focusField);
    else if(focusAction)focus=region.querySelector(`[data-pf-action="${focusAction}"]`);
    else if(focusObstacle)focus=[...region.querySelectorAll('[data-pf-obstacle]')].find(e=>e.dataset.pfObstacle===focusObstacle);
    else if(first||focusTitle)focus=region.querySelector('#pfTitle');
    focus?.focus({preventScroll:true});if(selection&&focus?.setSelectionRange&&selection[0]!==null)try{focus.setSelectionRange(...selection);}catch(_){}
    return true;
  }
  function update(s,event) {
    if(active!==s||!s.draft||['confirming','unknown'].includes(s.phase)||s.retired)return;
    const el=event.target,key=el.dataset.pfField,obstacle=el.dataset.pfObstacle;
    if(!key&&!obstacle)return;
    if(event.type==='input'&&el.tagName==='SELECT')return;
    if(event.type==='change'&&el.tagName==='INPUT'&&el.type!=='checkbox')return;
    if(!s.changed())return;
    if(obstacle){s.draft.obstacles=s.draft.obstacles.filter(v=>v!==obstacle);if(el.checked)s.draft.obstacles.push(obstacle);}
    else if(key==='selectFinish')selectFinish(s,el.value);
    else if(key==='selectFill')selectFill(s,el.value);
    else if(key==='selectHost')selectHost(s,el.value);
    else {const parts=key.split('.');let target=s.draft;for(const p of parts.slice(0,-1))target=target[p];
      target[parts.at(-1)]=el.type==='checkbox'?el.checked:el.value;
      if(parts.at(-1)==='kind'){target.value='';target.original=undefined;}}
    if(key?.startsWith('select')||['fill','host','pattern'].includes(key)||key?.endsWith('.kind')){
      display();document.querySelector(`[data-pf-field="${key}"]`)?.focus({preventScroll:true});
    }else{
      const region=el.closest('[data-pf-workspace]');region.querySelector('[data-pf-action="confirm"]').disabled=true;
      region.querySelector('[data-pf-action="preview"]').disabled=false;
      region.querySelector('[data-pf-status]').textContent=s.reason;region.querySelector('[data-pf-status]').dataset.pfStatus=s.phase;
      region.querySelector('.pf-results')?.remove();region.querySelector('.pf-diagnostics')?.remove();
      const sourceKey=key?.split('.')[0],output=region.querySelector(`[data-pf-source="${sourceKey}"]`);
      if(output){let value;try{value=sourceValue(s.draft[sourceKey],sourceKey==='h');}catch(_){value={kind:s.draft[sourceKey].kind,input:s.draft[sourceKey].value};}output.textContent='定義來源：'+JSON.stringify(value);}
    }
  }
  async function act(s,action) {
    if(active!==s)return;
    try {
      if(action==='close'||action==='cancel'){close();return;}
      if(action==='sources'){if(close())await window.EngineeringWorkspace.open();return;}
      if(action==='restore-edit'){s.changed();s.draft.remove=null;display();return;}
      if(action.startsWith('delete-')){
        const kind=action.slice(7),map={finish:['finish-surface',s.selection.finish],fill:['panel-fill',s.selection.fill],host:['derived-placement',s.selection.host]};
        if(map[kind]?.[1]!=null){s.changed();s.draft.remove=map[kind];display();}return;
      }
      if(action==='preview')await s.preview(operations(s));
      if(action==='confirm'){
        await s.confirm();if(active!==s||s.retired||s.phase!=='committed')return;
        const selection=s.selection,finish=selection.finish??s.draft.finishId,fill=selection.fill??s.draft.fillId,host=selection.host??s.draft.hostId;
        selectFinish(s,String(finish));if(fillRecords(s,s.draft.finishId).some(f=>f.definition.id===fill))selectFill(s,String(fill));
        if(hostRecords(s,s.draft.fillId).some(h=>h.definition.id===host))selectHost(s,String(host));display();ReferenceWorkspace.present?.();ReferenceWorkspace.sync?.();
      }
    }catch(error){if(active===s){s.reason=error.message;display();}}
  }
  async function open(boundaryId,trigger) {
    if(active&&!close())return false;
    const s=new A.Session(Number(boundaryId),()=>{if(active===s)display();});active=s;s.trigger=trigger;
    display();
    try{await s.read();if(active!==s||s.retired)return false;selectFinish(s,String(finishRecords(s)[0]?.id??'new'));display();return true;}
    catch(error){if(active===s){s.phase='invalid';s.reason=error.message;display();}return false;}
  }
  function close() {
    const s=active;if(!s)return true;if(!s.close()){s.reason='原確認回執尚未取得，禁止放棄或重送。';display();return false;}
    active=null;if(typeof renderFaceInspector==='function')renderFaceInspector();
    const entry=document.querySelector(`[data-face-settings="${s.boundaryId}"]`);
    (entry||(s.trigger?.isConnected?s.trigger:null))?.focus({preventScroll:true});ReferenceWorkspace.present?.();return true;
  }
  function invalidate(reason) {if(active)active.invalidate(reason);}
  function retireContext() {
    const s=active;if(!s)return;active=null;
    if(['confirming','unknown'].includes(s.phase))retiredSessions.add(s);
    s.invalidate('專案或面已退出；舊視圖已退役，原確認仍只接收既有回執。');
  }
  window.addEventListener('geometry-definition-changed',event=>{
    if(active?.confirmationCommand===event.detail?.command)return;
    if(active)invalidate('定義來源已變更；舊候選已失效，請重新開啟。');
  });
  window.addEventListener('space-models-changed',()=>{if(active&&!['confirming','unknown'].includes(active.phase)&&!A.isCurrent(active.owner))invalidate('專案或歷史身分已變更，請重新開啟。');});
  return {open,render,close,invalidate,retireContext,activeFor:bid=>!!active&&active.boundaryId===Number(bid),
    async reconcileReceipt(result,command){
      const candidates=[...(active?[active]:[]),...retiredSessions];
      for(const session of candidates)if(await session.reconcileReceipt(result,command)){retiredSessions.delete(session);ReferenceWorkspace.present?.();return true;}
      return false;
    },
    get pending(){return !!active && (active.dirty||['previewing','confirmable','confirming','unknown'].includes(active.phase));},
    mayLeave:()=>close(),get isOpen(){return !!active;},_test:{sourceDraft,sourceValue,operations,scalar}};
})();
