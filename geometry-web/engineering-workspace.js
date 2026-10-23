/* Engineering UI drafts are not World definitions. Only the host's verified
 * preview/confirm adapter can publish definitions or change geometry. */
"use strict";
window.EngineeringWorkspace = (() => {
  const roles = GeometryApplication.woodworking.engineeringRoles;
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const clone = value => value == null ? value : JSON.parse(JSON.stringify(value));
  const list = value => Array.isArray(value) ? value : Object.values(value || {});
  const ref = record => record ? {id:record.id, version:record.version} : null;
  const refKey = value => value ? JSON.stringify([value.id, value.version]) : "";
  const sameRef = (a, b) => refKey(a) === refKey(b);
  const refText = value => value ? `${value.name || value.id} · v${value.version}` : "未設定";
  const uiLabels={id:'識別',version:'版本',fingerprint:'內容指紋',archived:'已封存',kind:'種類',type:'種類',name:'名稱',width:'寬 mm',length:'長 mm',thickness:'厚 mm',A:'A mm',B:'B mm',brand:'品牌',model:'型號',notes:'來源與備註',panel:'面材',roles:'各角色材料',boundary:'邊界材',primary:'主支',secondary:'副支',gap:'縫寬 mm',longAxis:'面材長邊軸向',mainAlong:'主支方向',placement_id:'放置面',method:'工程做法',overrides:'本面覆寫',anchorOptions:'新建起點選項',bindings:'來源綁定',sources:'尺寸來源',source:'來源',override:'物件覆寫',target:'物件欄位',effective:'生效值',field:'欄位',axis:'軸向',u:'u 軸',v:'v 軸',geometry:'幾何',segments:'核心線段',coordinates:'座標',centerline:'中線',origin:'原點',dir:'延伸方向',side:'側向',priority:'優先序',role:'角色',grid:'網格',timber:'角材',material:'材料',spec:'具名尺寸',application:'面套用',literal:'明設數值',value:'值',path:'來源路徑',materials:'材料版本',methods:'做法版本',applications:'面套用',grids:'網格',timbers:'角材',guides:'參考線',definition:'定義',revision:'定義版本',capability:'能力',uDefinition:'u 軸定義',vDefinition:'v 軸定義',anchor:'起算點'};
  const integer = (value, min = 0) => /^-?\d+$/.test(String(value).trim()) && Number.isSafeInteger(Number(value)) && Number(value) >= min && Number(value) <= 100000000;
  const decimal = value => /^\d+(?:\.\d+)?$/.test(String(value).trim()) && /[1-9]/.test(String(value));
  const state = {snapshot:null, context:null, section:"apply", inlineKind:null, mobile:"settings", activePlacement:null, request:0, formRevision:0, busy:false, preview:null, intent:null, selectedMaterial:null, selectedMethod:null, material:null, method:null, application:{method:null,targets:{}}, search:"", importText:""};
  let adapter = null, dialog = null, unsubscribe = null, opener = null, draftBaseline = null;
  const drafts = new Map();
  const $ = id => dialog?.querySelector(`#${id}`);

  function context() {
    const value = adapter?.getProjectState?.() ?? adapter?.context?.();
    if (!value || value.contextToken == null && value.token == null && value.incarnation == null) return null;
    return {id:value.id, token:value.contextToken ?? value.token ?? value.incarnation};
  }
  function sameContext(a, b) { return a && b && a.id === b.id && a.token === b.token; }
  function current(sequence, sourceContext) { return dialog?.open && sequence === state.request && sameContext(context(), sourceContext) && (state.mode!=='grid'||adapter?.isGridContextCurrent?.(state.gridFlow)!==false); }
  function message(text, kind = "") {
    if (!$('ewStatus')) return;
    $('ewStatus').textContent = text;
    $('ewStatus').dataset.kind = kind;
  }
  function ensure() {
    if (dialog) return;
    dialog = document.createElement('dialog');
    dialog.id = 'ewWorkspace'; dialog.className = 'ew-workspace'; dialog.setAttribute('aria-labelledby', 'ewTitle');
    dialog.innerHTML = `<header class="ew-header"><div><h1 id="ewTitle">工程規格</h1></div><div class="ew-header-actions"><button type="button" id="ewClose" aria-label="返回畫布">返回畫布</button></div></header>
      <p id="ewWorkspaceLesson" class="studio-first-lesson" hidden></p>
      <nav class="ew-nav" aria-label="工程規格工作區"><button type="button" data-ew-section="apply" aria-current="page">套用至面</button><button type="button" data-ew-section="materials">材料規格</button><button type="button" data-ew-section="methods">工程做法</button><button type="button" data-ew-section="transfer">匯入／匯出</button></nav>
      <p id="ewStatus" class="ew-status" role="status" aria-live="polite"></p>
      <div id="ewContent" class="ew-content"></div>
      <section id="ewReview" class="ew-review" aria-label="核對這次變更" hidden></section>
      <footer class="ew-footer"><p id="ewFooterHelp">先設定材料與做法，再預覽要套用的面。</p><div><button type="button" id="ewCancelPreview" hidden>返回修改</button><button type="button" id="ewPreview" class="ew-primary">預覽變更</button><button type="button" id="ewConfirm" class="ew-primary" hidden disabled>確認套用</button></div></footer>`;
    document.body.append(dialog);
    $('ewClose').onclick = close;
    $('ewPreview').onclick = requestPreview;
    $('ewConfirm').onclick = confirm;
    $('ewCancelPreview').onclick = () => { invalidate(); render(); message('已返回修改，尚未套用這次變更。請重新預覽。'); };
    dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
    dialog.addEventListener('click', handleClick);
    dialog.addEventListener('input', handleInput);
    dialog.addEventListener('change', handleChange);
    dialog.addEventListener('keydown', event => {
      if (event.key !== 'Enter' || event.target.tagName === 'TEXTAREA' || event.target.tagName === 'BUTTON' || event.target.tagName === 'SELECT' || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return;
      if (event.target.tagName === 'INPUT' && event.target.type !== 'checkbox') { event.preventDefault(); if (!$('ewPreview').disabled && !state.preview)requestPreview(); }
    });
  }
  function configure(next) {
    unsubscribe?.(); adapter = next;
    unsubscribe = adapter?.subscribe?.(() => {
      if (!dialog?.open) return;
      const now = context();
      if (!sameContext(now, state.context)) { invalidate();dialog.close();return; }
      if ($('ewConfirm')?.dataset.committing === 'true') return;
      invalidate(); message('工程定義已改變，請重新讀取後再預覽。未提交的表單仍保留。', 'warning');
      load(false);
    }) || null;
  }
  const draftContent = () => JSON.stringify({material:state.material,method:state.method,application:state.application,importText:state.importText});
  function saveDraft() {
    // A grid hand-off is a temporary view of the existing GridEditor draft.
    // Cancelling it must not save unrelated workspace metadata or dirty the project.
    if(state.mode==='grid')return;
    if (!state.context || !sameContext(state.context,context())) return;
    const value = {material:state.material,method:state.method,application:state.application,section:state.section,inlineKind:state.inlineKind,activePlacement:state.activePlacement,importText:state.importText};
    drafts.set(JSON.stringify(state.context), clone(value));
    if(!adapter?.setEngineeringDraft)return;
    // Opening selects a useful face and initial form. Navigation stays in this
    // session; only a changed form creates/updates portable draft records.
    const content=draftContent();
    if(content===draftBaseline)return;
    const existing=adapter.getEngineeringDrafts?.()||[];
    for(const kind of ['material','method','application']){
      const id='engineering-workspace-'+kind;
      const data=kind==='application'?{form:state.application,ui:{section:state.section,inlineKind:state.inlineKind,activePlacement:state.activePlacement,importText:state.importText}}:state[kind];
      if(!data){adapter.removeEngineeringDraft?.(id,state.context.token);continue;}
      const base=data.base&&list(state.snapshot?.[kind==='material'?'materials':'methods']).find(r=>sameRef(r,data.base));
      const base_ref=base?.fingerprint?{...ref(base),fingerprint:base.fingerprint}:null;
      const prior=existing.find(record=>record.id===id);
      if(prior && JSON.stringify(prior.data)===JSON.stringify(data) && JSON.stringify(prior.base_ref)===JSON.stringify(base_ref))continue;
      adapter.setEngineeringDraft({id,kind,base_ref,data:clone(data),updated_at:new Date().toISOString()},state.context.token);
    }
    draftBaseline=content;syncProjectStatus();
  }
  function restoreDraft() {
    const records=adapter?.getEngineeringDrafts?.();
    const saved=records?.find(r=>r.id==='engineering-workspace-application')?.data;
    const value=records?{material:records.find(r=>r.id==='engineering-workspace-material')?.data??null,method:records.find(r=>r.id==='engineering-workspace-method')?.data??null,application:saved?.form??{method:null,targets:{}},...(saved?.ui||{})}:drafts.get(JSON.stringify(state.context));
    state.inlineKind=null;
    if (!value) { state.material=null;state.method=null;state.application={method:null,targets:{}};state.importText='';return; }
    for (const key of ['material','method','application','section','inlineKind','activePlacement','importText']) if (Object.hasOwn(value,key))state[key]=clone(value[key]);
  }
  async function open(options = {}) {
    if(window.DraftGate && !window.DraftGate.ask())return;
    ensure(); opener = document.activeElement;
    invalidate();
    const nextContext = context();
    if (!sameContext(nextContext, state.context)) { state.context=nextContext;restoreDraft(); }
    state.mode=options.mode==='grid'?'grid':null;
    if(state.mode==='grid'){
      state.previousSection=state.section==='grid'?'apply':state.section;
      state.section='grid';state.mobile='settings';state.gridSeed=clone(options.gridDraft||options);state.gridFlow={placementId:options.placementId,gridId:options.gridId??null};
    }else if(state.section==='grid')state.section=state.previousSection||'apply';
    state.preview=null;state.intent=null;
    if (options.placementId != null) { state.activePlacement=options.placementId;if(state.mode!=='grid')state.section='apply';state.inlineKind=null; }
    // Also covers closing while the initial read is still pending.
    draftBaseline=draftContent();
    dialog.dataset.mode=state.mode||'standard';
    $('ewTitle').textContent=state.mode==='grid'?'材料規格排格':'工程規格';
    dialog.querySelector('.ew-nav').hidden=state.mode==='grid';
    if (!dialog.open)dialog.showModal();
    placeStudioLesson($('ewWorkspaceLesson'), 'engineering:first', '這裡改面材與角材來源；預覽確認後才影響用到它的物件。');
    WorkspaceShell.attach(dialog, {saveBlocked:()=>state.busy || !adapter?.saveProject,
      saveReason:()=>state.busy?'正在處理工程變更，完成後即可保存。':'工程規格服務尚未連接。', onProjectState:syncProjectStatus});
    await load(true, options);
  }
  function close() {
    if (state.busy && $('ewConfirm')?.dataset.committing === 'true') return;
    saveDraft(); invalidate(); dialog?.close(); WorkspaceShell.detach(dialog);
    if (opener?.isConnected)opener.focus();
  }
  async function load(initial, options = {}) {
    const sequence = ++state.request, sourceContext = context(), initialFormRevision=state.formRevision;
    state.busy=true;updateActions();message('正在讀取材料、做法及目前工程…');
    try {
      if (!sourceContext || !adapter?.read)throw new Error('工程規格服務尚未連接；目前工程保持不變。');
      const result = await adapter.read();
      if (!current(sequence,sourceContext))return;
      if (result.capability !== 'engineering-spec/1')throw new Error('目前服務尚未支援工程規格來源，請開啟支援此功能的版本。');
      state.snapshot={...result,materials:list(result.materials).map(r=>({...r,type:r.kind??r.type}))};state.context=sourceContext;
      const placements = list(result.placements);
      if(state.mode==='grid'){
        if(!placements.some(p=>p.id===state.gridFlow.placementId))throw new Error('原本的放置面已不存在，請返回畫布重新開啟網格。');
        if(initial||!state.gridFlow.route)initializeGridFlow(state.gridSeed);
        render();message('已讀取目前工程。選面材、設定排格後，一次預覽並建立目前面的網格。');return true;
      }
      if (!placements.some(p => p.id === state.activePlacement))state.activePlacement=placements[0]?.id ?? null;
      if(initial&&options.placementId!=null){
        const previous=state.application.targets[state.activePlacement];
        state.application.stashedTargets={...state.application.stashedTargets,...state.application.targets};state.application.targets={};
        if(previous)state.application.targets[state.activePlacement]=previous;else selectTarget(state.activePlacement,options.gridId);
        if(options.gridId!=null){const target=state.application.targets[state.activePlacement];target.gridAction='update';target.gridId=options.gridId;target.anchors={u:{mode:'keep',value:''},v:{mode:'keep',value:''}};}
        if(!previous){const application=list(state.snapshot.applications).find(a=>a.placement_id===state.activePlacement);if(application)state.application.method=clone(application.method);}
      }
      if (initial && state.activePlacement != null && !Object.keys(state.application.targets).length)selectTarget(state.activePlacement, options.gridId);
      for(const [id,target] of Object.entries(state.application.targets))
        if(target.gridAction==='defaults'&&!canUseFutureDefaults(state.snapshot,Number(id)))target.gridAction='application';
      render();
      // A background reload must never swallow edits made while reading.
      if(initial && state.formRevision===initialFormRevision)draftBaseline=draftContent();
      message('已讀取目前工程。草稿與預覽不會改變已套用的定義。');return true;
    } catch(error) {
      if (sequence !== state.request)return;
      state.snapshot=null;render();message(error.message,'error');
    } finally { if(sequence===state.request){state.busy=false;updateActions();} }
  }
  function invalidate() {
    const token=state.preview?.token;
    state.preview=null;state.intent=null;++state.request;++state.formRevision;
    if($('ewConfirm')?.dataset.committing!=='true')state.busy=false;
    if(token && adapter?.cancel)Promise.resolve(adapter.cancel({token})).catch(() => {});
    if($('ewReview'))$('ewReview').hidden=true;
    updateActions();
  }
  function changed() { invalidate();saveDraft();message('設定已修改，預覽後才會套用到工程。'); }
  function syncProjectStatus() {
    WorkspaceShell.refresh(dialog);
  }
  function updateActions() {
    if(!dialog)return;
    const available=!!state.snapshot && !!adapter?.preview && !state.busy;
    $('ewPreview').disabled=!available;
    $('ewPreview').hidden=!!state.preview;
    $('ewConfirm').hidden=!state.preview;
    $('ewCancelPreview').hidden=!state.preview;
    $('ewConfirm').disabled=state.busy || !state.preview?.valid || !state.preview?.token || !$('ewReviewed')?.checked;
    $('ewClose').disabled=state.busy && $('ewConfirm').dataset.committing==='true';
    WorkspaceShell.refresh(dialog);
    $('ewContent').inert=$('ewConfirm').dataset.committing==='true'||state.mode==='grid'&&state.busy;
    dialog.querySelector('.ew-nav').inert=$('ewConfirm').dataset.committing==='true';
    $('ewPreview').textContent=state.section==='materials'?'預覽發布材料':state.section==='methods'?'預覽發布做法':state.section==='transfer'?'檢查匯入':'預覽套用';
    if(state.section==='apply'&&state.inlineKind)$('ewPreview').textContent=state.inlineKind==='material'?'預覽發布面材':'預覽發布做法';
    $('ewFooterHelp').textContent=state.preview?'核對完整影響後確認；任一目標失敗會整批保留原狀。':state.section==='apply'?'已選目標才會直接套用；角材只綁定明確勾選的項目。':'發布新版不會自動升級既有使用位置。未發布表單為草稿。';
    $('ewConfirm').textContent='確認套用';
    if(state.mode==='grid'){
      const update=state.gridFlow?.gridId!=null;
      $('ewPreview').textContent=update?'預覽更新網格':'預覽建立網格';
      $('ewConfirm').textContent=update?'確認更新網格':'確認建立網格';
      $('ewFooterHelp').textContent=state.preview?'確認後才會一次發布規格並套用網格；請核對既有來源的連帶影響。':'只處理目前面與指定網格。返回畫布會保留原網格草稿；既有角材不自動改綁材料。';
    }
  }
  function render() {
    if (!dialog)return;
    const detailKey=details=>{
      const summary=details.querySelector(':scope > summary')?.textContent?.replace(/\s*·\s*(?:已選\s*)?\d+.*$/,'')||'';
      const owner=details.closest('.ew-record')?.querySelector('[data-ew-edit-material],[data-ew-edit-method]');
      return (owner?.dataset.ewEditMaterial||owner?.dataset.ewEditMethod||details.closest('.ew-source-row')?.querySelector('strong')?.textContent||'')+'|'+summary;
    };
    const previousSection=$('ewContent').dataset.section;
    const openDetails=previousSection===state.section?Array.from($('ewContent').querySelectorAll('details[open]')).map(detailKey):[];
    const scrolls=previousSection===state.section?Array.from($('ewContent').querySelectorAll('.ew-editor,.ew-library-list')).map(n=>n.scrollTop):[];
    for(const button of dialog.querySelectorAll('[data-ew-section]')) {
      if(button.dataset.ewSection===state.section)button.setAttribute('aria-current','page');else button.removeAttribute('aria-current');
    }
    if(!state.snapshot){$('ewContent').innerHTML='<div class="ew-empty"><h2>尚未取得工程規格資料</h2><p>確認服務支援後，即可在這裡管理材料與真實工程的套用關係。</p><button type="button" data-ew-retry>重新讀取</button></div>';updateActions();return;}
    $('ewContent').innerHTML=state.mode==='grid'?renderGridFlow():state.section==='materials'?renderMaterials():state.section==='methods'?renderMethods():state.section==='transfer'?renderTransfer():renderApply();
    $('ewContent').dataset.section=state.section;
    if(state.section==='apply'&&state.inlineKind&&state[state.inlineKind]){
      const template=document.createElement('template');template.innerHTML=state.inlineKind==='material'?renderMaterials():renderMethods();
      $('ewContent').querySelector('.ew-apply>.ew-editor').innerHTML='<button type="button" data-ew-leave-inline>← 返回套用設定（保留草稿）</button>'+template.content.querySelector('.ew-editor').innerHTML;
    }
    if(state.section==='apply'&&!state.inlineKind){
      const method=list(state.snapshot.methods).find(r=>sameRef(r,state.application.method)),panel=list(state.snapshot.materials).find(r=>sameRef(r,method?.panel));
      const editButton=$('ewContent').querySelector('[data-ew-section="materials"]');
      if(editButton){delete editButton.dataset.ewSection;editButton.dataset.ewEditAppliedPanel='';editButton.textContent=panel?'編輯此面材尺寸':'建立面材規格';if(panel)editButton.parentElement.insertAdjacentHTML('beforebegin',`<p class="ew-panel-summary"><strong>${esc(refText(panel))}</strong><br>${esc(panel.width)} × ${esc(panel.length)} mm · 厚 ${esc(panel.thickness??'未設定')} mm<br><small>面材長邊對應與主支方向分別設定，發布新版後再明確選面套用。</small></p>`);}
      const target=state.application.targets[state.activePlacement];
      if(target){
        if(!canUseFutureDefaults(state.snapshot,state.activePlacement)){
          const path=`application.targets.${state.activePlacement}.gridAction`,field=dialog.querySelector(`[data-ew-field="${path}"]`);
          if(field){field.innerHTML=[['create','建立新主網格'],['update','更新指定主網格'],['application','更新本面做法與既有引用']].map(([value,label])=>`<option value="${value}"${value===target.gridAction?' selected':''}>${label}</option>`).join('');field.parentElement.insertAdjacentHTML('afterend','<p class="ew-note" id="ewExistingSourcesNotice">此面已有套用或尺寸來源。更新做法會重算沿用它的既有物件，全部影響須先預覽；不會自動增加角材綁定。既有主格的具體起算點保持，除非明選更新。</p>');}
        }
        $('ewFormError')?.insertAdjacentHTML('beforebegin',renderObjectSources(state.activePlacement,target));
        for(const select of dialog.querySelectorAll('[data-ew-field$=".mode"]'))if(select.dataset.ewField.includes('.anchors.')){
          const axis=select.dataset.ewField.split('.').at(-2);
          if(target.gridAction==='update')select.querySelector('option[value="lower"]')?.remove();
          else {select.insertAdjacentHTML('afterbegin','<option value="keep">保留新建起點設定</option>');select.insertAdjacentHTML('beforeend','<option value="upper">使用本次面上界</option>');}
          select.value=target.anchors[axis].mode;
        }
        const existing=list(state.snapshot.applications).find(a=>a.placement_id===state.activePlacement);
        if(existing)$('ewFormError')?.insertAdjacentHTML('beforebegin',`<details><summary>目前本面套用與覆寫</summary><p class="ew-note">升級預設保留這些設定。以下是目前核心定義。</p>${renderData(existing)}</details>`);
      }
    }
    if(state.section==='materials'||state.section==='methods')for(const recordElement of $('ewContent').querySelectorAll('.ew-record')){
      const kind=state.section==='materials'?'material':'method',key=recordElement.querySelector(`[data-ew-edit-${kind}]`)?.getAttribute(`data-ew-edit-${kind}`);
      const record=list(state.snapshot[state.section]).find(r=>refKey(r)===key);if(record)recordElement.insertAdjacentHTML('beforeend',renderUsage(kind,record));
    }
    if(state.section==='transfer')$('ewImportText')?.parentElement.insertAdjacentHTML('beforebegin','<label>選取正式做法包 JSON<input type="file" accept=".json,application/json" data-ew-package-file></label>');
    for(const details of $('ewContent').querySelectorAll('details'))if(openDetails.includes(detailKey(details)))details.open=true;
    Array.from($('ewContent').querySelectorAll('.ew-editor,.ew-library-list')).forEach((element,index)=>{element.scrollTop=scrolls[index]||0;});
    if((state.section==='materials'||state.inlineKind==='material')&&state.material?.mode==='version'&&$('ewField-material-type'))$('ewField-material-type').disabled=true;
    if(state.mode==='grid'&&state.gridFlow.gridId!=null&&$('ewField-gridFlow-mainAlong'))$('ewField-gridFlow-mainAlong').disabled=true;
    syncProjectStatus();updateActions();
  }
  function input(label,path,value,extra='') { const id='ewField-'+path.replace(/[^\w-]/g,'-');return `<label for="${id}">${label}<input id="${id}" data-ew-field="${path}" value="${esc(value)}" ${extra}></label>`; }
  function select(label,path,value,options) {const id='ewField-'+path.replace(/[^\w-]/g,'-');return `<label for="${id}">${label}<select id="${id}" data-ew-field="${path}">${options.map(([v,t])=>`<option value="${esc(v)}"${String(v)===String(value)?' selected':''}>${esc(t)}</option>`).join('')}</select></label>`;}
  function recordOptions(kind, type) {return [['','未設定'],...list(state.snapshot[kind]).filter(r=>(!type||(r.kind??r.type)===type)).map(r=>[refKey(r),refText(r)+(r.archived?'（已封存）':'')])];}
  function initializeGridFlow(draft) {
    const placementId=state.gridFlow.placementId,gridId=state.gridFlow.gridId;
    const application=list(state.snapshot.applications).find(a=>a.placement_id===placementId);
    const method=list(state.snapshot.methods).find(m=>sameRef(m,application?.method));
    const panels=list(state.snapshot.materials).filter(m=>m.type==='panel'&&!m.archived);
    const grid=gridId==null?null:list(state.snapshot.grids).find(g=>g.id===gridId&&(g.placement_id??g.surface)===placementId&&g.kind!=='subgrid');
    if(gridId!=null&&!grid)throw new Error('原本選取的主網格已不存在，請返回畫布重新選擇。');
    const strings=values=>Object.fromEntries(['u','v'].map(axis=>[axis,typeof values?.[axis]==='string'?values[axis]:'']));
    state.gridFlow={placementId,gridId,route:method?'method':panels.length?'panel':'new',method:ref(method),panel:null,
      name:'',width:'',length:'',thickness:'',methodName:`面 ${state.snapshot.placements.find(p=>p.id===placementId)?.boundary??placementId} 排格做法`,
      longAxis:application?.longAxis??method?.longAxis??'',mainAlong:grid?(grid.mainAlong||'none'):(draft.mainAlong??''),
      gaps:strings(draft.gaps),anchors:strings(draft.anchors)};
    // Existing typed values remain exact, including invalid or blank input.
    // Method defaults enter only after explicitly choosing a method or its button.
  }
  function applyGridMethodDefaults(replace) {
    const d=state.gridFlow,m=list(state.snapshot.methods).find(record=>sameRef(record,d.method));
    if(!m)return;
    for(const axis of ['u','v'])if((replace||d.gaps[axis]==='')&&m.gap!=null)d.gaps[axis]=String(m.gap);
    if((replace||!d.longAxis)&&m.longAxis)d.longAxis=m.longAxis;
    if(d.gridId==null&&(replace||!d.mainAlong)&&m.mainAlong)d.mainAlong=m.mainAlong;
  }
  function gridOrigin() {
    const placement=list(state.snapshot.placements).find(p=>p.id===state.gridFlow.placementId),points=placement?.loops?.flat();
    if(!points?.length||points.some(p=>!Array.isArray(p)||p.length!==2||p.some(n=>!Number.isSafeInteger(n))))return null;
    return {u:Math.min(...points.map(p=>p[0])),v:Math.min(...points.map(p=>p[1]))};
  }
  function renderGridFlow() {
    const d=state.gridFlow,p=list(state.snapshot.placements).find(p=>p.id===d.placementId),origin=gridOrigin();
    const existing=list(state.snapshot.applications).find(a=>a.placement_id===d.placementId);
    const method=list(state.snapshot.methods).find(m=>sameRef(m,d.method));
    const panel=list(state.snapshot.materials).find(m=>sameRef(m,d.route==='method'?method?.panel:d.panel));
    const heading=d.gridId==null?'用材料規格建立網格':`用材料規格更新網格 #${d.gridId}`;
    const panelSummary=panel?`<p class="ew-panel-summary" id="ewGridPanelSummary"><strong>${esc(refText(panel))}</strong><br>${esc(panel.width)} × ${esc(panel.length)} mm · 厚 ${esc(panel.thickness??'未設定')} mm<br><small>固定引用這個材料版本的長、寬。</small></p>`:'';
    return `<div class="ew-mobile-tabs"><button type="button" data-ew-mobile="settings" aria-pressed="${state.mobile==='settings'}">設定與套用</button><button type="button" data-ew-mobile="canvas" aria-pressed="${state.mobile==='canvas'}">查看畫布</button></div><div class="ew-apply ew-grid-flow" data-mobile="${state.mobile}"><section class="ew-stage" aria-label="目前面的核心幾何"><div class="ew-stage-head"><h2>${esc(placementLabel(p))}</h2><span id="ewGridTarget">${d.gridId==null?'建立一個主網格':`更新既有網格 #${d.gridId}`}</span></div><div class="ew-stage-geometry">${renderGeometry(p)}</div><p class="ew-note">只有確認後才會改變工程；預覽由核心計算，既有角材不自動改綁。</p></section><section class="ew-editor" aria-label="材料規格排格設定"><div class="ew-form"><h2>${heading}</h2>${select('規格來源','gridFlow.route',d.route,[['panel','選用已發布面材'],['new','新增面材規格'],['method','選用已發布工程做法']])}
      ${d.route==='method'?select('工程做法版本','gridFlow.method',refKey(d.method),recordOptions('methods'))+`<button type="button" data-ew-grid-method-defaults${method?'':' disabled'}>採用做法排格設定</button>`:d.route==='panel'?select('面材版本','gridFlow.panel',refKey(d.panel),recordOptions('materials','panel')):`<fieldset><legend>新增面材規格</legend>${input('材料名稱','gridFlow.name',d.name,'maxlength="160"')}<div class="ew-fields">${input('面材寬 mm','gridFlow.width',d.width,'inputmode="numeric"')}${input('面材長 mm','gridFlow.length',d.length,'inputmode="numeric"')}${input('面材厚 mm（選填）','gridFlow.thickness',d.thickness,'inputmode="decimal"')}</div><p class="ew-note">厚度可留空；這一步以長寬排格，不建立面材實體。</p></fieldset>`}${panelSummary}
      ${d.route==='method'?'':`<fieldset><legend>建立排格做法</legend>${input('排格做法名稱','gridFlow.methodName',d.methodName,'maxlength="160"')}<p class="ew-note">確認時一起發布此做法與所選材料的固定版本引用。${existing?'沿用目前做法的三角色用料；本面與物件覆寫仍保留。':'三角色角材用料保持未設定。'}</p></fieldset>`}
      <fieldset><legend>排格方向與縫寬</legend>${select('面材長邊方向','gridFlow.longAxis',d.longAxis,[['','請選擇'],['u','沿 u（橫向）'],['v','沿 v（直向）']])}${select('主支長度方向','gridFlow.mainAlong',d.mainAlong,[...(d.gridId!=null?[['none','未設定角色預設（保留）']]:[['','請選擇']]),['u','沿 u（橫向）'],['v','沿 v（直向）']])}${d.gridId!=null?'<p class="ew-note">更新材料來源時保留既有網格的主支方向；未設定時繼續保持未設定，不改角材角色。</p>':''}<div class="ew-fields">${input('u 軸縫寬 mm','gridFlow.gaps.u',d.gaps.u,'inputmode="numeric"')}${input('v 軸縫寬 mm','gridFlow.gaps.v',d.gaps.v,'inputmode="numeric"')}</div><p class="ew-note">兩軸縫寬各自明設，可為 0；與做法不同的數值會列為此網格覆寫。</p></fieldset>
      <fieldset><legend>具體起算點</legend><div class="ew-fields">${input('u 起算點 mm','gridFlow.anchors.u',d.anchors.u,'inputmode="numeric"')}${input('v 起算點 mm','gridFlow.anchors.v',d.anchors.v,'inputmode="numeric"')}</div><button type="button" data-ew-grid-origin${origin?'':' disabled'}>使用面起點${origin?`（u ${origin.u}、v ${origin.v} mm）`:''}</button><p class="ew-note">沿用網格表單已填的座標。留空時請明寫，或按上方按鈕採用目前面下界。</p></fieldset>
      ${existing?`<details><summary>本面已有做法與覆寫，核對保留內容</summary><p class="ew-note">更換做法或長邊方向可能影響本面已綁定的其他物件，預覽會完整列出。角材不會新增綁定。</p>${renderData(existing)}${renderData(bindingsForPlacement(d.placementId).filter(binding=>binding.override))}</details>`:''}<p class="ew-field-error" id="ewFormError" role="alert"></p></div></section></div>`;
  }
  function renderUsage(kind,record) {
    const methods=kind==='material'?list(state.snapshot.methods).filter(m=>sameRef(m.panel,record)||Object.values(m.roles||{}).some(r=>sameRef(r,record))):[record];
    const applications=list(state.snapshot.applications).filter(a=>methods.some(m=>sameRef(m,a.method)));
    const direct=kind==='material'?list(state.snapshot.sources??state.snapshot.bindings).filter(b=>[b.source,b.override].some(s=>s?.kind==='material'&&sameRef(s,record))):[];
    const content=[...methods.filter(m=>kind==='material').map(m=>`做法 ${refText(m)}`),...applications.map(a=>`放置 #${a.placement_id} · 面套用 ${a.id}`),...direct.map(b=>targetLabel(b.target))];
    return `<details><summary>使用位置 · ${content.length}</summary>${content.length?`<ul>${content.map(label=>`<li>${esc(label)}</li>`).join('')}</ul>`:'<p>目前沒有使用位置，仍會隨專案保存。</p>'}<p class="ew-note">${esc(record.fingerprint?'內容指紋：'+record.fingerprint:'核心未提供指紋')}<br>發布新版本不會改動這些固定版本引用。</p></details>`;
  }
  function allowReplaceDraft(kind) {if(!state[kind])return true;state.section=kind==='material'?'materials':'methods';render();message('這裡已有未發布草稿。請先完成或明確捨棄，再開啟另一份。','warning');return false;}
  function newMaterial(type='panel') {if(!allowReplaceDraft('material'))return;state.material=GeometryApplication.woodworking.materialDraft(type);state.section='materials';changed();render();$('ewField-material-name')?.focus();}
  function editRecord(kind,key,mode) {
    if(!allowReplaceDraft(kind))return false;
    const record=list(state.snapshot[kind==='material'?'materials':'methods']).find(r=>refKey(r)===key);
    if(!record)return;
    state[kind]={...clone(record),mode,base:ref(record)};
    if(kind==='material')Object.assign(state.material,{type:record.kind??record.type,note:record.notes??'',source:'',brand:record.brand??'',model:record.model??''});
    if(kind==='method')Object.assign(state.method,{note:record.notes??'',gap:record.gap??'',longAxis:record.longAxis??'',mainAlong:record.mainAlong??''});
    if(kind==='method')state.method.roles={...Object.fromEntries(roles.map(([k])=>[k,null])),...state.method.roles};
    state.section=kind==='material'?'materials':'methods';changed();render();$('ewField-'+kind+'-name')?.focus();return true;
  }
  function renderMaterials() {
    const records=list(state.snapshot.materials),d=state.material;
    return `<div class="ew-library"><aside class="ew-library-list"><h2>材料規格</h2><p>面材與角材各自保存固定版本。</p><div class="ew-button-row"><button type="button" data-ew-new-material="panel">＋ 面材</button><button type="button" data-ew-new-material="timber">＋ 角材</button></div>${input('搜尋材料','search',state.search,'type="search"')}<div id="ewMaterialList">${records.map(r=>`<article class="ew-record" data-ew-search="${esc((r.name+' '+r.id).toLowerCase())}"${state.search&&!`${r.name} ${r.id}`.toLowerCase().includes(state.search.toLowerCase())?' hidden':''}><strong>${esc(refText(r))}</strong><p>${r.type==='panel'?`${esc(r.width)} × ${esc(r.length)} mm · 厚 ${esc(r.thickness??'未設定')}`:`${esc(r.A)} × ${esc(r.B)} mm`}${r.archived?' · 已封存':''}</p><div class="ew-button-row"><button type="button" data-ew-edit-material="${esc(refKey(r))}">查看／編輯新版</button><button type="button" data-ew-copy-material="${esc(refKey(r))}">複製</button><button type="button" data-ew-archive-material="${esc(refKey(r))}">${r.archived?'恢復使用':'封存'}</button></div></article>`).join('')||'<p class="ew-empty">尚無材料。按「＋ 面材」從可修改的工作預設開始。</p>'}</div></aside><section class="ew-editor" aria-label="材料編輯">${d?`<div class="ew-section-head"><h2>${d.mode==='version'?'另存材料新版本':d.mode==='copy'?'複製成新材料':'新增材料'}</h2><span class="ew-draft-badge">未發布草稿</span></div>${d.base?`<p class="ew-note">來源 ${esc(d.base.id)} · v${esc(d.base.version)}；原版本保持不變。</p>`:''}<div class="ew-form">${input('規格名稱','material.name',d.name,'maxlength="160"')}${select('種類','material.type',d.type,[['panel','面材'],['timber','角材']])}<fieldset><legend>${d.type==='panel'?'面材尺寸':'角材截面'} · mm</legend><div class="ew-fields">${d.type==='panel'?input('寬','material.width',d.width,'inputmode="numeric"')+input('長','material.length',d.length,'inputmode="numeric"')+input('厚（選填）','material.thickness',d.thickness,'inputmode="decimal"'):input('A（沿面）','material.A',d.A,'inputmode="numeric"')+input('B（出面）','material.B',d.B,'inputmode="numeric"')}</div>${d.type==='panel'?`<div class="ew-button-row">${GeometryApplication.woodworking.materialPresets.map(p=>`<button type="button" data-ew-preset="${p.width},${p.length}">${p.width} × ${p.length}</button>`).join('')}${GeometryApplication.woodworking.thicknessPresets.map(t=>`<button type="button" data-ew-thickness="${t}">厚 ${t}</button>`).join('')}</div><p class="ew-note">長寬參與排格；厚度只保存為材料資料，不會建立面材實體。</p>`:'<p class="ew-note">截面不提供長度，也不指定位置、角色或支撐條件。</p>'}</fieldset><details><summary>品牌、型號及來源（選填）</summary>${input('品牌','material.brand',d.brand)}${input('型號','material.model',d.model)}${input('來源網址或備註','material.source',d.source)}${input('備註','material.note',d.note)}</details><p class="ew-field-error" id="ewFormError" role="alert"></p><button type="button" data-ew-discard="material">捨棄這份草稿</button></div>`:'<div class="ew-empty"><h2>選擇要查看的材料</h2><p>編輯會建立新版本，已套用的面保持原來的版本。</p></div>'}</section></div>`;
  }
  function renderMethods() {
    const records=list(state.snapshot.methods),d=state.method;
    return `<div class="ew-library"><aside class="ew-library-list"><h2>工程做法</h2><p>組合面材與各角色用料，再選面套用。</p><button type="button" data-ew-new-method>＋ 新增工程做法</button>${records.map(r=>`<article class="ew-record"><strong>${esc(refText(r))}${r.archived?'（已封存）':''}</strong><div class="ew-button-row"><button type="button" data-ew-edit-method="${esc(refKey(r))}">查看／編輯新版</button><button type="button" data-ew-copy-method="${esc(refKey(r))}">複製</button><button type="button" data-ew-use-method="${esc(refKey(r))}">選面套用</button><button type="button" data-ew-archive-method="${esc(refKey(r))}">${r.archived?'恢復使用':'封存'}</button></div></article>`).join('')||'<p class="ew-empty">尚無工程做法。</p>'}</aside><section class="ew-editor" aria-label="做法編輯">${d?`<div class="ew-section-head"><h2>${d.mode==='version'?'另存做法新版本':d.mode==='copy'?'複製成新做法':'新增工程做法'}</h2><span class="ew-draft-badge">未發布草稿</span></div><div class="ew-form">${input('做法名稱','method.name',d.name)}${select('面材版本','method.panel',refKey(d.panel),recordOptions('materials','panel'))}<button type="button" data-ew-edit-current-panel>編輯所選面材尺寸</button><fieldset><legend>各角色角材</legend>${roles.map(([role,label])=>select(label+'用料','method.roles.'+role,refKey(d.roles?.[role]),recordOptions('materials','timber'))).join('')}<p class="ew-note">未選擇的用料保持未設定；发布做法不會自動放置或改綁既有角材。</p></fieldset><fieldset><legend>排板預設</legend>${input('縫寬 mm（未設定可留空）','method.gap',d.gap,'inputmode="numeric"')}${select('面材長邊方向','method.longAxis',d.longAxis,[['','未設定'],['u','沿 u'],['v','沿 v']])}${select('主支長度方向','method.mainAlong',d.mainAlong,[['','未設定'],['u','沿 u'],['v','沿 v']])}</fieldset>${input('來源與支撐限制備註（選填）','method.note',d.note)}<p class="ew-note">備註不代表力學驗證，也不會自動選等分數。</p><p class="ew-field-error" id="ewFormError" role="alert"></p><button type="button" data-ew-discard="method">捨棄這份草稿</button></div>`:'<div class="ew-empty"><h2>先建立一份可重用的做法</h2><p>選擇已發布材料版本。新版本不會自動改動現有使用位置。</p></div>'}</section></div>`;
  }
  function placementLabel(p) {return `${p.name||'面 '+(p.bid??p.boundary_id??p.boundary??p.id)} · 放置 #${p.id}`;}
  function selectTarget(id,gridId) {
    const existing=list(state.snapshot?.applications).find(a=>a.placement_id===id);
    const grids=list(state.snapshot?.grids).filter(g=>(g.placement_id??g.surface)===id && g.kind!=='subgrid');
    const mode=gridId!=null?'keep':'lower';
    const anchors=Object.fromEntries(['u','v'].map(axis=>{const setting=existing?.anchorOptions?.[axis];return [axis,gridId!=null?{mode:'keep',value:''}:setting?.kind==='coordinate'?{mode:'value',value:String(setting.value)}:setting?.kind==='edge'?{mode:setting.side==='max'?'upper':'lower',value:''}:{mode:existing?'keep':mode,value:''}];}));
    state.application.targets[id]={placement_id:id,gridAction:gridId!=null?'update':grids.length?(canUseFutureDefaults(state.snapshot,id)?'defaults':'application'):'create',gridId:gridId??null,longAxis:existing?.longAxis??'inherit',mainAlong:existing?.mainAlong??'inherit',anchors,preserveOverrides:true,overrides:{},timberIds:[],objectOverrides:{},objectSources:{}};
    if(existing?.method && !state.application.method)state.application.method=clone(existing.method);
  }
  function overrideField(label,path,value,options={}) {
    const setting=value||{mode:'inherit',value:''};
    return `<div class="ew-override">${select(label,path+'.mode',setting.mode,[['inherit','沿用來源'],['literal','改成本面數值'],['spec','引用具名尺寸']])}${setting.mode==='spec'?select('具名尺寸',path+'.value',setting.value,[['','請選擇'],...list(state.snapshot.specs).map(s=>[s.name,`${s.name} · ${s.value} mm`])]):setting.mode==='literal'?input(label+' mm',path+'.value',setting.value,'inputmode="numeric"'):'<small>移除覆寫後會重新預覽來源與完整影響。</small>'}</div>`;
  }
  function bindingsForPlacement(id) {
    const gridIds=new Set(list(state.snapshot.grids).filter(g=>(g.placement_id??g.surface)===id).map(g=>g.id));
    const timberIds=new Set(list(state.snapshot.timbers).filter(t=>(t.placement_id??t.surface??t.geometry?.placement_id)===id).map(t=>t.id));
    return list(state.snapshot.sources??state.snapshot.bindings).filter(b=>b.target&&(b.target.kind==='grid'?gridIds.has(b.target.id):timberIds.has(b.target.id)));
  }
  function canUseFutureDefaults(snapshot,id) {
    if(list(snapshot.applications).some(application=>application.placement_id===id))return false;
    const grids=new Set(list(snapshot.grids).filter(g=>(g.placement_id??g.surface)===id).map(g=>g.id));
    const timbers=new Set(list(snapshot.timbers).filter(t=>(t.placement_id??t.surface??t.geometry?.surface??t.geometry?.placement_id)===id).map(t=>t.id));
    return !list(snapshot.sources??snapshot.bindings).some(binding=>binding.target&&(binding.target.kind==='grid'?grids.has(binding.target.id):binding.target.kind==='timber'&&timbers.has(binding.target.id)));
  }
  function sourceLabel(source) {
    if(!source)return '既有直接輸入';
    if(source.kind==='literal')return `明設 ${source.value} mm`;
    if(source.kind==='spec')return `具名尺寸「${source.name}」`;
    if(source.kind==='parameter')return window.ParameterUI?.sourceLabel(source,state.snapshot.parameters)||`參數 ${source.parameterId}:${source.fieldId}`;
    if(source.kind==='material'){const material=lookupVersion('materials',source);return `${material?refText(material):'材料版本 v'+source.version} · ${uiLabels[source.field]||source.field}`;}
    if(source.kind==='application'){const application=list(state.preview?.after?.applications??state.snapshot.applications).find(a=>a.id===source.id);return `${application?faceName(application.placement_id):'本面'}做法 · ${sourceFieldLabel(source.field)}`;}
    return '來源資料待核對';
  }
  function lookupVersion(collection,reference){return [...list(state.preview?.after?.[collection]),...list(state.snapshot?.[collection])].find(record=>sameRef(record,reference));}
  function faceName(id){const placement=list(state.snapshot?.placements).find(p=>p.id===id);return placement?placementLabel(placement):`放置 #${id}`;}
  function sourceFieldLabel(field){const labels={'u.panel':'u 軸面材尺寸','v.panel':'v 軸面材尺寸','u.gap':'u 軸縫寬','v.gap':'v 軸縫寬',gap:'縫寬'};for(const [role,label] of roles)for(const axis of ['A','B'])labels[role+'.'+axis]=label+' '+axis;return labels[field]||field;}
  function targetLabel(target){return target.kind==='grid'?`網格 #${target.id} · ${target.axis} ${target.field==='panel'?'面材尺寸':'縫寬'}`:`角材 #${target.id} · ${target.field}`;}
  function sourceEditor(target,setting,placementId,level) {
    const key=JSON.stringify(target),draft=setting||{mode:'keep',value:'',field:target.field==='panel'?'width':target.field};
    const modes=[['keep','保持目前設定'],...(level==='override'?[['inherit','移除覆寫，恢復來源']]:[['unbind','解除引用，保留有效值']]),['literal','明設數值'],['spec','引用具名尺寸'],['parameter','引用參數欄位'],...(target.field!=='gap'?[['material','引用固定材料版本']]:[])];
    const common=`data-placement="${placementId}" data-ew-source-target="${esc(key)}" data-ew-source-level="${level}"`;
    const control=(name,label,options)=>`<label>${label}<select data-ew-source-${name} ${common}>${options.map(([value,text])=>`<option value="${esc(value)}"${String(draft[name])===String(value)?' selected':''}>${esc(text)}</option>`).join('')}</select></label>`;
    let html=control('mode',level==='source'?'尺寸來源':'物件覆寫',modes);
    if(draft.mode==='literal')html+=`<label>數值 mm<input inputmode="numeric" data-ew-source-value ${common} value="${esc(draft.value)}"></label>`;
    if(draft.mode==='spec')html+=control('value','具名尺寸',[['','請選擇'],...list(state.snapshot.specs).map(spec=>[spec.name,`${spec.name} · ${spec.value} mm`])]);
    if(draft.mode==='parameter')html+=control('value','參數欄位',[['','請選擇'],...(window.ParameterUI?.options({dimensions:true,catalog:state.snapshot.parameters||[]})||[]).map(o=>[o.ref.parameterId+':'+o.ref.fieldId,o.text])]);
    if(draft.mode==='material'){
      html+=control('value','固定材料版本',recordOptions('materials',target.kind==='grid'?'panel':'timber'));
      if(target.kind==='grid')html+=control('field','採用面材的',[['width','寬'],['length','長']]);
    }
    return `<div class="ew-source-editor">${html}</div>`;
  }
  function renderObjectSources(id,t) {
    const existing=bindingsForPlacement(id),rows=[...existing];
    for(const grid of list(state.snapshot.grids).filter(g=>(g.placement_id??g.surface)===id&&g.kind!=='subgrid'))for(const axis of ['u','v']){
      const definition=grid[axis+'Definition'];if(definition?.source!=='panel')continue;
      for(const field of ['panel','gap']){
        const target={kind:'grid',id:grid.id,axis,field};
        if(!rows.some(r=>r.target.kind==='grid'&&r.target.id===grid.id&&r.target.axis===axis&&r.target.field===field))rows.push({target,source:null,override:null,effective:definition[field]});
      }
    }
    for(const timber of list(state.snapshot.timbers).filter(item=>(item.placement_id??item.surface??item.geometry?.placement_id)===id))for(const field of ['A','B']){
      const target={kind:'timber',id:timber.id,field};
      if(!rows.some(r=>r.target.kind===target.kind&&r.target.id===target.id&&r.target.field===field))rows.push({target,source:null,override:null,effective:timber[field]??timber.geometry?.[field]});
    }
    return `<details data-ew-source-details><summary>物件來源、有效值與覆寫 · ${rows.length} 項</summary><p class="ew-note">包含 custom 角材。直接指定材料或具名尺寸只改截面來源，不會改角色、位置引用或優先序。只修改下方來源時可單獨預覽，不必另選做法。</p>${rows.map(binding=>{
      const key=JSON.stringify(binding.target);
      const parameterLinks=[binding.source,binding.override].filter(s=>s?.kind==='parameter').map(s=>`<button type="button" data-ew-parameter="${s.parameterId}">查看 ${esc(sourceLabel(s))}</button>`).join('');
      return `<div class="ew-source-row"><strong>${esc(targetLabel(binding.target))}</strong><p>${esc(sourceLabel(binding.source))}<br>生效值：${esc(binding.effective??'待核心提供')} mm${binding.override?` · 目前覆寫：${esc(sourceLabel(binding.override))}`:''}</p>${parameterLinks}${binding.path?`<details><summary>有效來源路徑</summary>${renderData(binding.path)}</details>`:''}${sourceEditor(binding.target,t.objectSources?.[key],id,'source')}${binding.source?sourceEditor(binding.target,t.objectOverrides[key],id,'override'):''}</div>`;
    }).join('')||'<p class="ew-note">目前沒有已放角材或工程來源綁定。可先從上方明確綁定既有主網格。</p>'}<button type="button" data-ew-source-preview="${id}">只預覽這個面的來源變更</button></details>`;
  }
  function renderApply() {
    const placements=list(state.snapshot.placements),selected=Object.keys(state.application.targets),p=placements.find(p=>p.id===state.activePlacement),t=p&&state.application.targets[p.id];
    return `<div class="ew-mobile-tabs"><button type="button" data-ew-mobile="settings" aria-pressed="${state.mobile==='settings'}">設定與套用</button><button type="button" data-ew-mobile="canvas" aria-pressed="${state.mobile==='canvas'}">查看畫布</button></div><div class="ew-apply" data-mobile="${state.mobile}"><section class="ew-stage" aria-label="目前面的核心幾何"><div class="ew-stage-head"><h2>${p?esc(placementLabel(p)):'尚無已放置的面'}</h2><span>目前工程 · 尚未套用草稿</span></div><div class="ew-stage-geometry">${renderGeometry(p)}</div><p class="ew-note">預覽線段由核心提供；此處不自行依面材尺寸猜排格。</p></section><section class="ew-editor"><div class="ew-form"><h2>選做法，再核對要套用的面</h2>${select('工程做法版本','application.method',refKey(state.application.method),recordOptions('methods'))}<div class="ew-button-row"><button type="button" data-ew-section="materials">設定面材尺寸</button><button type="button" data-ew-new-method>新增工程做法</button></div><details${!selected.length?' open':''}><summary>套用目標 · 已選 ${selected.length} 個放置面</summary><div class="ew-target-list">${placements.map(item=>`<label><input type="checkbox" data-ew-target="${item.id}"${state.application.targets[item.id]?' checked':''}>${esc(placementLabel(item))}</label>`).join('')||'<p>請先建立並放置面。</p>'}</div></details>${select('核對這個面','activePlacement',state.activePlacement??'',placements.map(item=>[item.id,placementLabel(item)]))}${p&&!t?'<p class="ew-note">此面未勾選，不會直接套用。仍會列出引用鏈造成的連帶影響。</p>':t?renderTarget(p,t):''}<p class="ew-field-error" id="ewFormError" role="alert"></p></div></section></div>`;
  }
  function renderTarget(p,t) {
    const base=`application.targets.${p.id}`,grids=list(state.snapshot.grids).filter(g=>(g.placement_id??g.surface)===p.id&&g.kind!=='subgrid'),timbers=list(state.snapshot.timbers).filter(item=>(item.placement_id??item.surface??item.geometry?.placement_id)===p.id);
    return `${select('網格處理',base+'.gridAction',t.gridAction,[['create','建立新主網格'],['update','更新指定主網格'],['defaults','只提供後續新建預設']])}${t.gridAction==='update'?select('要更新的主網格',base+'.gridId',t.gridId??'',[['','請明確選擇'],...grids.map(g=>[g.id,`主網格 #${g.id}`])]):''}${select('面材長邊對應',base+'.longAxis',t.longAxis,[['inherit','沿用做法'],['u','長邊沿 u，寬沿 v'],['v','長邊沿 v，寬沿 u']])}${select('主支長度方向',base+'.mainAlong',t.mainAlong,[['inherit','沿用做法'],['u','沿 u'],['v','沿 v']])}<fieldset><legend>起算點 · mm</legend><p class="ew-note">更新已有主格時保留具體起點，除非這次明確指定新值。</p>${['u','v'].map(axis=>`<div class="ew-fields">${select(axis+' 軸起算',base+'.anchors.'+axis+'.mode',t.anchors[axis].mode,[...(t.gridAction==='update'?[['keep','保留目前起點']]:[]),['lower','使用本次面下界'],['value','明寫座標']])}${t.anchors[axis].mode==='value'?input(axis+' 起算座標',base+'.anchors.'+axis+'.value',t.anchors[axis].value,'inputmode="numeric"'):''}</div>`).join('')}</fieldset><details><summary>本面覆寫與恢復沿用</summary><label class="ew-checkbox"><input type="checkbox" data-ew-field="${base}.preserveOverrides"${t.preserveOverrides?' checked':''}>升級時保留原有覆寫</label>${overrideField('縫寬',base+'.overrides.gap',t.overrides.gap)}${roles.map(([key,label])=>`<details><summary>${label}截面覆寫</summary>${['A','B'].map(axis=>overrideField(label+' '+axis,base+'.overrides.'+key+axis,t.overrides[key+axis])).join('')}</details>`).join('')}</details><details><summary>綁定既有角材 · 已選 ${t.timberIds.length} 支</summary><p class="ew-note">勾選才套用角色對應材料；位置引用與角色保持。custom 角色不能綁定三角色槽位。</p>${timbers.map(item=>`<label class="ew-checkbox"><input type="checkbox" data-ew-timber="${item.id}" data-placement="${p.id}"${t.timberIds.includes(item.id)?' checked':''}${item.role==='custom'?' disabled':''}>角材 #${item.id} · ${esc(item.role)}${item.role==='custom'?'（本次不綁定）':''}</label>`).join('')||'<p>這個放置面沒有已放角材。</p>'}</details>`;
  }
  function renderGeometry(placement,segments) {
    if(!placement)return '<p class="ew-empty">從正式畫布放置面後，即可選取。</p>';
    const loops=placement.loops;
    if(!Array.isArray(loops)||!loops.length)return '<p class="ew-empty">目前來源未提供可顯示的輪廓；數值與套用仍由核心驗證。</p>';
    const points=loops.flat();if(points.some(p=>!Array.isArray(p)||p.length!==2||p.some(n=>!Number.isFinite(n))))return '<p class="ew-empty">輪廓資料不完整，請重新讀取工程。</p>';
    const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]),minX=Math.min(...xs),minY=Math.min(...ys),width=Math.max(...xs)-minX,height=Math.max(...ys)-minY,pad=Math.max(width,height)*.07||1;
    const path=loops.map(loop=>'M'+loop.map(p=>p.join(',')).join('L')+'Z').join('');
    const lines=segments||list(state.snapshot.grids).filter(g=>(g.placement_id??g.surface)===placement.id).flatMap(g=>g.segments||g.lines?.flatMap(line=>line.segments||[])||[]);
    return `<svg viewBox="${minX-pad} ${minY-pad} ${width+2*pad} ${height+2*pad}" role="img" aria-label="${esc(placementLabel(placement))}，u 向右、v 向下"><path d="${esc(path)}" fill-rule="evenodd" class="ew-outline"/>${lines.map(line=>Array.isArray(line)&&line.length===2&&line.every(p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite))?`<line x1="${line[0][0]}" y1="${line[0][1]}" x2="${line[1][0]}" y2="${line[1][1]}" class="ew-grid-line"/>`:'').join('')}</svg>`;
  }
  function renderTransfer() {return `<section class="ew-transfer"><h2>攜帶材料與工程做法</h2><p>做法包匯入會核對完整版本與來源，同 id／版本異內容整包拒絕。原型 JSON 不能直接代替正式做法包。</p><label for="ewImportText">正式做法包 JSON<textarea id="ewImportText" data-ew-field="importText" spellcheck="false" rows="10">${esc(state.importText)}</textarea></label><p class="ew-field-error" id="ewFormError" role="alert"></p><div class="ew-button-row"><button type="button" data-ew-export>匯出本專案材料與做法包</button></div><p class="ew-note">保存完整工程請用上方「保存專案」；做法包不是場景備份。</p></section>`;}
  function setPath(path,value) {const parts=path.split('.');let target=state;for(const part of parts.slice(0,-1)){if(['__proto__','prototype','constructor'].includes(part))return;target=target[part]??(target[part]={});}const key=parts.at(-1);if(!['__proto__','prototype','constructor'].includes(key))target[key]=value;}
  function fieldValue(element) {
    const path=element.dataset.ewField;
    if(element.type==='checkbox')return element.checked;
    if(path==='application.method'||path==='method.panel'||path==='gridFlow.method'||path==='gridFlow.panel'||path?.startsWith('method.roles.')) {const parsed=element.value?JSON.parse(element.value):null;return parsed?{id:parsed[0],version:parsed[1]}:null;}
    if(path==='activePlacement'||path?.endsWith('.gridId'))return element.value===''?null:Number(element.value);
    return element.value;
  }
  function handleInput(event) {
    const element=event.target,path=element.dataset.ewField;
    if(element.hasAttribute('data-ew-source-value')&&element.tagName!=='SELECT'){updateSourceDraft(element,'value',false);return;}
    if(element.dataset.ewObjectValue!=null){const target=state.application.targets[element.dataset.placement],key=element.dataset.ewObjectValue;target.objectOverrides[key].value=element.value;changed();return;}
    if(!path||element.tagName==='SELECT'||element.type==='checkbox')return;
    setPath(path,fieldValue(element));
    if(path==='search'){for(const record of dialog.querySelectorAll('[data-ew-search]'))record.hidden=!record.dataset.ewSearch.includes(state.search.toLowerCase());return;}
    changed();
  }
  function handleChange(event) {
    const e=event.target;
    if(e.hasAttribute('data-ew-package-file')){
      const file=e.files?.[0];if(!file)return;
      if(file.size>1048576){message('做法包超過 1 MiB，尚未匯入。','error');return;}
      invalidate();const sourceContext=context(),revision=state.formRevision;
      file.text().then(text=>{if(!sameContext(context(),sourceContext)||revision!==state.formRevision||!dialog.open)return;state.importText=text;changed();render();message('已讀入做法包，按「檢查匯入」核對後再確認。');}).catch(error=>{if(sameContext(context(),sourceContext))message(error.message,'error');});
      return;
    }
    for(const key of ['mode','value','field'])if(e.hasAttribute('data-ew-source-'+key)){updateSourceDraft(e,key,e.tagName==='SELECT');return;}
    if(e.dataset.ewObjectMode!=null){const target=state.application.targets[e.dataset.placement],key=e.dataset.ewObjectMode;target.objectOverrides[key]={mode:e.value,value:''};changed();render();dialog.querySelector(`[data-ew-object-mode="${CSS.escape(key)}"]`)?.focus();return;}
    if(e.dataset.ewObjectValue!=null){const target=state.application.targets[e.dataset.placement],key=e.dataset.ewObjectValue;target.objectOverrides[key].value=e.value;changed();return;}
    if(e.dataset.ewField && (e.tagName==='SELECT'||e.type==='checkbox')) {
      const path=e.dataset.ewField;setPath(path,fieldValue(e));
      if(path==='gridFlow.method')applyGridMethodDefaults(false);
      if(path.endsWith('.gridAction')){const target=state.application.targets[path.split('.')[2]];for(const axis of ['u','v'])target.anchors[axis].mode=target.gridAction==='update'?'keep':'lower';}
      changed();render();dialog.querySelector(`[data-ew-field="${CSS.escape(path)}"]`)?.focus();return;
    }
    if(e.dataset.ewTarget!=null){const id=Number(e.dataset.ewTarget);if(e.checked){if(state.application.stashedTargets?.[id])state.application.targets[id]=clone(state.application.stashedTargets[id]);else selectTarget(id);}else {state.application.stashedTargets??={};state.application.stashedTargets[id]=state.application.targets[id];delete state.application.targets[id];}state.activePlacement=id;changed();render();return;}
    if(e.dataset.ewTimber!=null){const id=Number(e.dataset.ewTimber),t=state.application.targets[e.dataset.placement];t.timberIds=t.timberIds.filter(n=>n!==id);if(e.checked)t.timberIds.push(id);changed();return;}
    if(e.id==='ewReviewed')updateActions();
  }
  function handleClick(event) {
    const button=event.target.closest('button');if(!button||!dialog.contains(button)||state.busy)return;
    if(button.hasAttribute('data-ew-parameter')){close();window.ParameterUI?.jump('parameter',Number(button.dataset.ewParameter));return;}
    if(button.hasAttribute('data-ew-grid-origin')){const origin=gridOrigin();if(origin){state.gridFlow.anchors={u:String(origin.u),v:String(origin.v)};changed();render();}return;}
    if(button.hasAttribute('data-ew-grid-method-defaults')){applyGridMethodDefaults(true);changed();render();return;}
    if(button.dataset.ewSection){state.section=button.dataset.ewSection;invalidate();saveDraft();render();message('已切換頁面，草稿仍保留。請重新預覽要套用的變更。');return;}
    if(button.hasAttribute('data-ew-retry')){load(false);return;}
    if(button.hasAttribute('data-ew-return-settings')){invalidate();render();message('已返回本次設定，請依阻擋原因修改後重新預覽。');return;}
    if(button.hasAttribute('data-ew-leave-inline')){state.inlineKind=null;changed();render();return;}
    if(button.hasAttribute('data-ew-source-preview')){const id=Number(button.dataset.ewSourcePreview);requestPreview({action:'sources',draft:clone(state.application.targets[id])});return;}
    if(button.dataset.ewMobile){state.mobile=button.dataset.ewMobile;render();return;}
    if(button.dataset.ewNewMaterial){newMaterial(button.dataset.ewNewMaterial);return;}
    if(button.hasAttribute('data-ew-new-method')){if(!allowReplaceDraft('method'))return;state.method={mode:'new',base:null,name:'',panel:null,roles:Object.fromEntries(roles.map(([key])=>[key,null])),gap:'',longAxis:'',mainAlong:'',note:''};state.section='methods';changed();render();$('ewField-method-name')?.focus();return;}
    for(const kind of ['material','method'])for(const mode of ['edit','copy']){const key=button.getAttribute(`data-ew-${mode}-${kind}`);if(key!=null){editRecord(kind,key,mode==='edit'?'version':'copy');return;}}
    if(button.dataset.ewUseMethod){const record=list(state.snapshot.methods).find(r=>refKey(r)===button.dataset.ewUseMethod);state.application.method=ref(record);state.section='apply';changed();render();return;}
    if(button.dataset.ewPreset){const [width,length]=button.dataset.ewPreset.split(',');Object.assign(state.material,{width,length});changed();render();return;}
    if(button.dataset.ewThickness){state.material.thickness=button.dataset.ewThickness;changed();render();return;}
    if(button.hasAttribute('data-ew-edit-current-panel')){if(state.method?.panel){if(editRecord('material',refKey(state.method.panel),'version')){state.material.continueMethod=true;saveDraft();message('發布面材新版本後，會回到原本的做法草稿繼續編輯。');}}else message('請先選擇面材版本，或到材料規格新增面材。','warning');return;}
    if(button.hasAttribute('data-ew-edit-applied-panel')){
      const method=list(state.snapshot.methods).find(r=>sameRef(r,state.application.method));
      if(!allowReplaceDraft('material')||!allowReplaceDraft('method'))return;
      if(method?.panel){editRecord('method',refKey(method),'version');editRecord('material',refKey(method.panel),'version');}
      else {newMaterial('panel');state.method={mode:'new',base:null,name:'',panel:null,roles:Object.fromEntries(roles.map(([key])=>[key,null])),gap:'',longAxis:'',mainAlong:'',note:''};}
      state.method.continueApply=true;state.material.continueMethod=true;state.material.continueInline=true;state.inlineKind='material';state.section='apply';saveDraft();render();message('在畫布旁編輯尺寸。發布材料後會接著設定做法，再回到選面預覽。');
      return;
    }
    if(button.dataset.ewDiscard){if(!window.confirm('捨棄這份未發布草稿？已發布版本與工程不會改變。'))return;state[button.dataset.ewDiscard]=null;if(state.inlineKind===button.dataset.ewDiscard)state.inlineKind=null;changed();render();return;}
    for(const kind of ['material','method']){const key=button.getAttribute('data-ew-archive-'+kind);if(key!=null){const record=list(state.snapshot[kind==='material'?'materials':'methods']).find(r=>refKey(r)===key);requestPreview({action:'archive',draft:{kind,reference:ref(record),archived:!record.archived}});return;}}
    if(button.hasAttribute('data-ew-export'))exportPackage();
    if(button.dataset.ewLocate)navigateToObject(JSON.parse(button.dataset.ewLocate));
  }
  async function navigateToObject(target) {
    if(!adapter?.navigateObject){message('此服務尚未連接定位操作，請返回畫布查看本次目標。','error');return;}
    const sourceContext=context();close();const closedRequest=state.request;
    try {await adapter.navigateObject(target,{isCurrent:()=>sameContext(context(),sourceContext)&&state.request===closedRequest&&!dialog.open});}
    catch(error){
      if(!sameContext(context(),sourceContext)||state.request!==closedRequest||dialog.open)return;
      const reopening=open(),openingRequest=state.request;await reopening;
      if(sameContext(context(),sourceContext)&&state.request===openingRequest&&dialog.open)message('無法完成定位：'+error.message,'error');
    }
  }
  function validateIntent(intent) {
    const d=intent.draft;
    if(intent.action==='grid'){
      if(!d||!Number.isSafeInteger(d.placementId))return '請返回畫布選擇要排格的面。';
      if(d.route==='method'&&!list(state.snapshot.methods).some(m=>sameRef(m,d.method)))return '請選擇已發布的工程做法版本。';
      if(d.route==='panel'&&!list(state.snapshot.materials).some(m=>sameRef(m,d.panel)&&m.type==='panel'))return '請選擇已發布的面材版本。';
      if(d.route==='new'){
        if(!d.name.trim())return '請填寫材料名稱。';
        if(!integer(d.width,1)||!integer(d.length,1))return '面材長、寬請填寫 1～100,000,000 的整數 mm。';
        if(d.thickness.trim()!==''&&!decimal(d.thickness))return '面材厚度須為正十進位 mm，或留空表示未設定。';
      }
      if(d.route!=='method'&&!d.methodName.trim())return '請填寫要一起建立的排格做法名稱。';
      if(!['u','v'].includes(d.longAxis))return '請選擇面材長邊方向。';
      if(!['u','v'].includes(d.mainAlong)&&!(d.gridId!=null&&d.mainAlong==='none'))return '請選擇主支長度方向。';
      for(const axis of ['u','v']){
        if(!integer(d.gaps[axis]))return `${axis} 軸縫寬請填寫 0～100,000,000 的整數 mm。`;
        if(!integer(d.anchors[axis],-100000000))return `${axis} 起算點請填寫整數 mm，或明選「使用面起點」。`;
      }
    }
    if(intent.action==='publishMaterial'){
      if(!d?.name?.trim())return '請填寫材料名稱。';
      for(const key of d.type==='panel'?['width','length']:['A','B'])if(!integer(d[key],1))return `${key} 請填寫 1～100,000,000 的整數 mm。`;
      if(d.type==='panel' && d.thickness!=='' && d.thickness!=null && !decimal(d.thickness))return '厚度須為正十進位 mm，或留空表示未設定。';
    }
    if(intent.action==='publishMethod'){
      if(!d?.name?.trim())return '請填寫做法名稱。';
      if(d.gap!==''&&d.gap!=null&&!integer(d.gap))return '縫寬须為 0～100,000,000 的整數 mm，或留空表示未設定。';
    }
    if(intent.action==='apply'){
      if(!d.method)return '請選擇已發布的工程做法版本。';
      if(!Object.keys(d.targets).length)return '請明確選擇至少一個放置面。';
      for(const target of Object.values(d.targets)){
        if(target.gridAction==='update'&&target.gridId==null)return `放置 #${target.placement_id}：請選擇要更新的主網格。`;
        for(const axis of ['u','v'])if(target.anchors[axis].mode==='value'&&!integer(target.anchors[axis].value,-100000000))return `放置 #${target.placement_id}：${axis} 起點須為範圍內的整數 mm。`;
      }
    }
    if(intent.action==='sources'&&!Object.values({...d?.objectSources,...d?.objectOverrides}).some(setting=>setting.mode!=='keep'))return '請先選擇要變更的物件來源或覆寫。';
    return '';
  }
  function updateSourceDraft(element,key,rerender) {
    const target=state.application.targets[element.dataset.placement];if(!target)return;
    const property=element.dataset.ewSourceLevel==='source'?'objectSources':'objectOverrides',identity=element.dataset.ewSourceTarget;
    target[property]??={};
    if(key==='mode')target[property][identity]={mode:element.value,value:'',field:JSON.parse(identity).field==='panel'?'width':JSON.parse(identity).field};
    else (target[property][identity]??={mode:'keep',value:'',field:''})[key]=element.value;
    changed();if(rerender){render();dialog.querySelector(`[data-ew-source-${key}][data-ew-source-target="${CSS.escape(identity)}"][data-ew-source-level="${element.dataset.ewSourceLevel}"]`)?.focus();}
  }
  function defaultIntent() {
    if(state.mode==='grid')return {action:'grid',draft:clone(state.gridFlow)};
    if(state.section==='apply'&&state.inlineKind)return {action:state.inlineKind==='material'?'publishMaterial':'publishMethod',draft:clone(state[state.inlineKind])};
    if(state.section==='materials')return {action:'publishMaterial',draft:clone(state.material)};
    if(state.section==='methods')return {action:'publishMethod',draft:clone(state.method)};
    if(state.section==='transfer')return {action:'import',draft:{text:state.importText}};
    return {action:'apply',draft:clone(state.application)};
  }
  function sourceFromDraft(d, minimum=0) {
    if(d.mode==='parameter'){if(!/^\d+:\d+$/.test(d.value))throw Error('請選擇參數欄位。');const [parameterId,fieldId]=d.value.split(':').map(Number);return {kind:'parameter',parameterId,fieldId};}
    if(d.mode==='inherit')return null;
    if(d.mode==='spec'){if(!d.value)throw new Error('請選擇具名尺寸。');return {kind:'spec',name:d.value};}
    if(d.mode==='material'){if(!d.value)throw new Error('請選擇固定材料版本。');const parsed=JSON.parse(d.value);if(!Array.isArray(parsed)||parsed.length!==2||!['width','length','A','B'].includes(d.field))throw new Error('材料欄位未設定。');return {kind:'material',id:parsed[0],version:parsed[1],field:d.field};}
    if(d.mode==='literal'){if(!integer(d.value,minimum))throw new Error(`覆寫值須為 ${minimum}～100,000,000 的整數 mm。`);return {kind:'literal',value:Number(d.value)};}
    throw new Error('尺寸來源未設定，請重新選擇。');
  }
  function identity(d, records, prefix) {
    if(d.mode!=='version')return {id:prefix+'-'+crypto.randomUUID(),version:1};
    if(!d.base||!records.some(r=>sameRef(r,d.base)))throw new Error('原版本不存在，請重新讀取。');
    const version=1+Math.max(...records.filter(r=>r.id===d.base.id).map(r=>r.version));
    if(version>4294967295)throw new Error('版本數超過上限，請複製為新規格。');
    return {id:d.base.id,version};
  }
  async function buildGridOperations(d,snapshot) {
    const placement=list(snapshot.placements).find(p=>p.id===d.placementId);
    if(!placement)throw new Error('目標面已不存在，請返回畫布重新開啟。');
    const existing=list(snapshot.applications).find(a=>a.placement_id===d.placementId);
    const previousMethod=list(snapshot.methods).find(m=>sameRef(m,existing?.method));
    const grid=d.gridId==null?null:list(snapshot.grids).find(g=>g.id===d.gridId&&(g.placement_id??g.surface)===d.placementId&&g.kind!=='subgrid');
    if(d.gridId!=null&&!grid)throw new Error('指定的主網格已不存在，請返回畫布重新選擇。');
    if(grid&&d.mainAlong!==(grid.mainAlong||'none'))throw new Error('既有網格的主支方向已改變，請重新讀取後再預覽。');
    if(d.gridId==null&&list(snapshot.grids).some(g=>(g.placement_id??g.surface)===d.placementId&&g.kind!=='subgrid'))throw new Error('這個面已有主網格，請返回畫布開啟該網格，再選擇材料規格。');
    const operations=[];
    let method=d.route==='method'?list(snapshot.methods).find(m=>sameRef(m,d.method)):null,panel=d.panel;
    if(d.route==='new'){
      const value={...identity({mode:'new'},list(snapshot.materials),'material'),kind:'panel',name:d.name.trim(),width:Number(d.width),length:Number(d.length),thickness:d.thickness.trim()||null};
      operations.push({op:'publish-material',value});panel=ref(value);
    }
    if(d.route!=='method'){
      if(!panel)throw new Error('請選擇面材固定版本。');
      method={...identity({mode:'new'},list(snapshot.methods),'method'),name:d.methodName.trim(),panel:clone(panel),
        roles:clone(previousMethod?.roles||Object.fromEntries(roles.map(([key])=>[key,null]))),gap:Number(d.gaps.u),longAxis:d.longAxis,mainAlong:d.mainAlong==='none'?(previousMethod?.mainAlong??null):d.mainAlong,notes:previousMethod?.notes??null};
      operations.push({op:'publish-method',value:method});
    }
    if(!method?.panel)throw new Error('這份工程做法尚未設定面材版本，請改選面材或選擇完整做法。');
    const application={id:existing?.id??'application-'+crypto.randomUUID(),placement_id:d.placementId,method:ref(method),
      longAxis:d.longAxis,mainAlong:grid?(existing?.mainAlong??null):d.mainAlong,overrides:clone(existing?.overrides||{}),anchorOptions:clone(existing?.anchorOptions||{u:null,v:null})};
    if(!grid)for(const axis of ['u','v'])application.anchorOptions[axis]={kind:'coordinate',value:Number(d.anchors[axis])};
    operations.push({op:'put-application',value:application});
    let gridId=d.gridId;
    if(gridId==null){
      if(!adapter?.allocateGridIds)throw new Error('服務尚未提供網格配號，尚未建立網格。');
      const ids=await adapter.allocateGridIds(1);
      if(!Array.isArray(ids)||ids.length!==1||!Number.isSafeInteger(ids[0])||ids[0]<0||ids[0]>4294967295)throw new Error('網格配號不完整，請重新預覽。');
      gridId=ids[0];
    }
    operations.push({op:'bind-grid',id:gridId,application:application.id,...(!grid?{create:true}:{}),anchors:{u:Number(d.anchors.u),v:Number(d.anchors.v)}});
    // Retain existing overrides unless the user explicitly changes that gap.
    // New axes inherit the application's fixed method whenever its value fits.
    const gapSource=application.overrides.gap;
    const baseGap=gapSource?.kind==='literal'?gapSource.value:gapSource?.kind==='spec'?list(snapshot.specs).find(s=>s.name===gapSource.name)?.value:gapSource?undefined:method.gap;
    for(const axis of ['u','v']){
      const binding=list(snapshot.sources??snapshot.bindings).find(b=>b.target?.kind==='grid'&&b.target.id===gridId&&b.target.axis===axis&&b.target.field==='gap');
      const wanted=Number(d.gaps[axis]);
      if(binding?.override&&binding.effective===wanted)continue;
      if(!binding?.override&&baseGap===wanted)continue;
      operations.push({op:'set-override',target:{kind:'grid',id:gridId,axis,field:'gap'},value:{kind:'literal',value:wanted}});
    }
    return operations;
  }
  async function buildOperations(intent,snapshot) {
    const d=intent.draft;
    if(intent.action==='grid')return buildGridOperations(d,snapshot);
    if(intent.action==='publishMaterial'){
      const value={...identity(d,list(snapshot.materials),'material'),kind:d.type,name:d.name.trim(),brand:d.brand?.trim()||null,model:d.model?.trim()||null,notes:[d.source?.trim(),d.note?.trim()].filter(Boolean).join('\n')||null};
      if(d.type==='panel')Object.assign(value,{width:Number(d.width),length:Number(d.length),thickness:d.thickness==null||String(d.thickness).trim()===''?null:String(d.thickness).trim()});
      else Object.assign(value,{A:Number(d.A),B:Number(d.B)});
      return [{op:'publish-material',value}];
    }
    if(intent.action==='publishMethod')return [{op:'publish-method',value:{...identity(d,list(snapshot.methods),'method'),name:d.name.trim(),panel:clone(d.panel),roles:Object.fromEntries(roles.map(([key])=>[key,clone(d.roles?.[key]??null)])),gap:d.gap==null||d.gap===''?null:Number(d.gap),longAxis:d.longAxis||null,mainAlong:d.mainAlong||null,notes:d.note?.trim()||null}}];
    if(intent.action==='archive')return [{op:'archive',kind:d.kind,id:d.reference.id,version:d.reference.version,value:d.archived}];
    if(intent.action==='import')return importOperations(d.text);
    if(intent.action==='sources')return buildSourceOperations(d);
    if(intent.action!=='apply')throw new Error('不支援這個工程規格操作。');
    const targets=Object.values(d.targets),count=targets.filter(t=>t.gridAction==='create').length;
    if(count&&!adapter?.allocateGridIds)throw new Error('服務尚未提供網格配號，不能建立新主格。');
    const gridIds=count?await adapter.allocateGridIds(count):[];
    if(!Array.isArray(gridIds)||gridIds.length!==count||gridIds.some(id=>!Number.isInteger(id)||id<0||id>4294967295)||new Set(gridIds).size!==gridIds.length)throw new Error('服務回傳的網格編號不完整，工程保持不變。');
    const operations=[];let allocated=0;
    for(const target of targets){
      if(!list(snapshot.placements).some(p=>p.id===target.placement_id))throw new Error(`放置 #${target.placement_id} 已不存在，請重新讀取。`);
      if(target.gridAction==='defaults'&&!canUseFutureDefaults(snapshot,target.placement_id))throw new Error(`放置 #${target.placement_id} 已有套用或尺寸來源，不能只作未來預設。請選擇更新本面做法並核對既有引用。`);
      const existing=list(snapshot.applications).find(a=>a.placement_id===target.placement_id);
      const application={id:existing?.id??'application-'+crypto.randomUUID(),placement_id:target.placement_id,method:clone(d.method),longAxis:target.longAxis==='inherit'?null:target.longAxis,mainAlong:target.mainAlong==='inherit'?null:target.mainAlong,overrides:target.preserveOverrides?clone(existing?.overrides||{}):{},anchorOptions:clone(existing?.anchorOptions||{u:null,v:null})};
      for(const [field,setting] of Object.entries(target.overrides)){
        const key=field==='gap'?field:field.replace(/(A|B)$/,'.$1');
        const source=sourceFromDraft(setting,key==='gap'?0:1);
        if(source===null)delete application.overrides[key];else application.overrides[key]=source;
      }
      if(target.gridAction==='create'||target.gridAction==='defaults'||target.gridAction==='application')for(const axis of ['u','v']){
        const setting=target.anchors[axis];
        application.anchorOptions[axis]=setting.mode==='lower'?{kind:'edge',side:'min'}:setting.mode==='upper'?{kind:'edge',side:'max'}:setting.mode==='value'?{kind:'coordinate',value:Number(setting.value)}:application.anchorOptions[axis];
      }
      operations.push({op:'put-application',value:application});
      if(target.gridAction==='create')operations.push({op:'bind-grid',id:gridIds[allocated++],application:application.id,create:true});
      if(target.gridAction==='update'){
        const grid=list(snapshot.grids).find(g=>g.id===target.gridId&&(g.placement_id??g.surface)===target.placement_id&&g.kind!=='subgrid');
        if(!grid)throw new Error(`放置 #${target.placement_id} 的指定主格已不存在。`);
        const operation={op:'bind-grid',id:target.gridId,application:application.id};
        if(['u','v'].some(axis=>target.anchors[axis].mode!=='keep')){
          operation.anchors={};
          for(const axis of ['u','v']){
            const setting=target.anchors[axis],original=grid[axis+'Definition']?.anchor??grid.definition?.[axis]?.anchor;
            if(setting.mode==='keep'&&!Number.isInteger(original))throw new Error(`核心未提供網格 #${grid.id} 的 ${axis} 原起點，請明寫兩軸起點或保持兩軸不變。`);
            if(setting.mode!=='keep'&&setting.mode!=='value')throw new Error('更新既有主格請保留目前起點，或明寫新的座標。');
            operation.anchors[axis]=setting.mode==='keep'?original:Number(setting.value);
          }
        }
        operations.push(operation);
      }
      for(const id of target.timberIds){
        const timber=list(snapshot.timbers).find(t=>t.id===id&&(t.placement_id??t.surface??t.geometry?.placement_id)===target.placement_id);
        if(!timber||!roles.some(([key])=>key===timber.role))throw new Error(`角材 #${id} 不適用三角色材料綁定，工程保持不變。`);
        operations.push({op:'bind-timber',id,application:application.id,slot:timber.role});
      }
      operations.push(...buildSourceOperations(target));
    }
    return operations;
  }
  function buildSourceOperations(target) {
    const operations=[];
    for(const [key,setting] of Object.entries(target.objectSources||{}))if(setting.mode!=='keep'){
      const bound=JSON.parse(key);operations.push(setting.mode==='unbind'?{op:'unbind-source',target:bound}:{op:'set-source',target:bound,source:sourceFromDraft(setting,bound.field==='gap'?0:1)});
    }
    for(const [key,setting] of Object.entries(target.objectOverrides||{}))if(setting.mode!=='keep'){
      const bound=JSON.parse(key);operations.push({op:'set-override',target:bound,value:sourceFromDraft(setting,bound.field==='gap'?0:1)});
    }
    return operations;
  }
  function diffSnapshots(before,after) {
    const rows=[];
    for(const collection of ['materials','methods','applications','sources','bindings','grids','guides','timbers']){
      if(before?.[collection]==null&&after?.[collection]==null)continue;
      const previousRecords=list(before?.[collection]),nextRecords=list(after?.[collection]);
      // Failed native trials can retain an unresolved geometry slot as null.
      // Keep that incomplete collection visible without inventing a deletion
      // or treating an unresolved slot as an identified object.
      if([...previousRecords,...nextRecords].some(record=>record==null)){
        rows.push({label:`${uiLabels[collection]} · 候選資料尚未完整求值`,before:{[collection]:previousRecords},after:{[collection]:nextRecords},unresolved:true});
        continue;
      }
      const key=r=>r.target?JSON.stringify(r.target):JSON.stringify([r.id,r.version??null]);
      const previous=new Map(previousRecords.map(r=>[key(r),r])),next=new Map(nextRecords.map(r=>[key(r),r]));
      for(const identity of new Set([...previous.keys(),...next.keys()])){
        const old=previous.get(identity)??null,value=next.get(identity)??null;if(JSON.stringify(old)===JSON.stringify(value))continue;
        const record=value||old;
        const related=record.target?list(after?.[record.target.kind==='grid'?'grids':'timbers']??before?.[record.target.kind==='grid'?'grids':'timbers']).find(r=>r.id===record.target.id):null;
        rows.push({collection,label:`${uiLabels[collection]} · ${record.target?targetLabel(record.target):record.name||record.id}${record.version?' · v'+record.version:''}`,before:old,after:value,placement_id:record.placement_id??record.surface??record.geometry?.surface??related?.surface??related?.placement_id??related?.geometry?.surface,segments:collection==='grids'?(value?.segments??value?.lines?.flatMap(line=>line.segments||[])):undefined});
      }
    }
    if(!rows.length&&JSON.stringify(before)!==JSON.stringify(after))rows.push({label:'核心完整候選定義與幾何',before,after});
    const order={grids:0,timbers:1,sources:2,bindings:2,guides:3,applications:4,materials:5,methods:6};
    for(const row of rows)if(row.collection==='applications')row.label=faceName(row.placement_id)+' · 工程做法套用';
    return rows.sort((a,b)=>(order[a.collection]??7)-(order[b.collection]??7));
  }
  async function requestPreview(explicit) {
    if(state.busy||!state.snapshot)return;
    if(state.mode==='grid'&&adapter?.isGridContextCurrent?.(state.gridFlow)===false){invalidate();message('畫布已切換，請返回目前面重新開啟網格。','error');return;}
    const intent=explicit?.action?explicit:defaultIntent(),error=validateIntent(intent);
    if(error){message(error,'error');if($('ewFormError')){$('ewFormError').textContent=error;$('ewFormError').scrollIntoView({block:'nearest'});}return;}
    invalidate();state.busy=true;updateActions();
    const sequence=state.request,sourceContext=context(),formRevision=state.formRevision;
    try {
      const operations=await buildOperations(clone(intent),clone(state.snapshot));
      if(!current(sequence,sourceContext)||formRevision!==state.formRevision)return;
      const result=await adapter.preview({operations,expectedRevision:state.snapshot.revision});
      if(!current(sequence,sourceContext)||formRevision!==state.formRevision){if(result.token)adapter.cancel?.({token:result.token});return;}
      if(result.ok===false)throw new Error(result.error||'核心未接受此預覽，工程保持不變。');
      const normalized=result.preview?{...result.preview,diagnostics:result.preview.violations??result.diagnostics}:result;
      if(!normalized.rows && (normalized.before||normalized.after))normalized.rows=diffSnapshots(normalized.before,normalized.after);
      if(normalized.valid&&normalized.rows?.some(row=>row.unresolved))throw new Error('核心候選資料尚未完整求值，不能確認套用。');
      const selected=intent.action==='grid'?[intent.draft.placementId]:intent.action==='apply'?Object.values(intent.draft.targets).map(t=>t.placement_id):intent.action==='sources'?[intent.draft.placement_id]:null;
      if(selected)normalized.outsideScope=(normalized.rows||[]).filter(row=>row.placement_id!=null&&!selected.includes(row.placement_id)).map(row=>({name:row.label,placement_id:row.placement_id}));
      if(normalized.before&&normalized.after){
        normalized.preservedOverrides=list(normalized.after.sources??normalized.after.bindings).filter(binding=>binding.override&&list(normalized.before.sources??normalized.before.bindings).some(old=>JSON.stringify(old.target)===JSON.stringify(binding.target)&&JSON.stringify(old.override)===JSON.stringify(binding.override))).map(binding=>({target:binding.target,override:binding.override,effective:binding.effective}));
        for(const application of list(normalized.after.applications)){
          const previous=list(normalized.before.applications).find(a=>a.id===application.id);
          for(const [field,source] of Object.entries(application.overrides||{}))if(JSON.stringify(previous?.overrides?.[field])===JSON.stringify(source))normalized.preservedOverrides.push({placement_id:application.placement_id,field,source});
        }
      }
      state.preview=normalized;state.intent={...intent,operations,publishedMaterial:ref(operations.find(o=>o.op==='publish-material')?.value),publishedMethod:ref(operations.find(o=>o.op==='publish-method')?.value)};renderPreview();message(normalized.valid?'預覽檢查通過。請核對完整影響，再確認套用。':'這次變更有阻擋，整個工程尚未改動。','warning');
    } catch(error){if(current(sequence,sourceContext))message(error.message,'error');}
    finally{if(sequence===state.request){state.busy=false;updateActions();}}
  }
  function renderPreview() {
    const result=state.preview;if(!result)return;
    result.rows=(result.rows||[]).filter(row=>row.collection!=='reference-redeclarations').concat((result.redeclaredReferences||[]).map(reference=>({collection:'reference-redeclarations',label:'刪後重宣告',before:{'引用':'來源刪除，舊引用已結束'},after:{'引用':reference.message}})));
    const rows=result.rows||[],faces=new Set(rows.map(row=>row.placement_id).filter(id=>id!=null));
    const grids=new Set(rows.flatMap(row=>row.collection==='grids'?[row.after?.id??row.before?.id]:(row.after?.target??row.before?.target)?.kind==='grid'?[(row.after?.target??row.before?.target).id]:[]));
    const timbers=new Set(rows.flatMap(row=>row.collection==='timbers'?[row.after?.id??row.before?.id]:(row.after?.target??row.before?.target)?.kind==='timber'?[(row.after?.target??row.before?.target).id]:[]));
    $('ewReview').hidden=false;
    $('ewReview').innerHTML=`<h2>${result.valid?'核對這次變更':'無法套用'}</h2><div class="ew-review-scroll">${(result.diagnostics||[]).map(d=>`<p class="ew-diagnostic">${esc(typeof d==='string'?d:d.message||d.code)}${d.object?` <button type="button" data-ew-locate="${esc(JSON.stringify(d.object))}">定位問題物件</button>`:''}</p>`).join('')}${(result.rows||[]).map((row,i)=>`<article class="ew-diff"><h3>${esc(row.label||row.name||`變更 ${i+1}`)}</h3>${renderDiff(row)}${row.segments&&row.placement_id!=null?renderGeometry(list(state.snapshot.placements).find(p=>p.id===row.placement_id),row.segments):''}</article>`).join('')||'<p>核心未回傳變更列，請核對操作摘要。</p>'}${result.preservedOverrides?.length?`<details><summary>保留的覆寫 · ${result.preservedOverrides.length}</summary>${renderData(result.preservedOverrides)}</details>`:''}${result.outsideScope?.length?`<details open><summary>選取面以外的連帶影響 · ${result.outsideScope.length}</summary>${renderData(result.outsideScope)}</details>`:''}</div>${result.valid?'<label class="ew-checkbox ew-review-check"><input id="ewReviewed" type="checkbox">我已核對版本、目標、覆寫及連帶影響</label>':''}`;
    appendSectionProfileImpact($('ewReview').querySelector('.ew-review-scroll'), result);
    $('ewReview').scrollIntoView({block:'nearest'});updateActions();
    $('ewReview').querySelector('h2').insertAdjacentHTML('afterend',`<p class="ew-impact-summary">${faces.size||grids.size||timbers.size?`核對 ${faces.size} 個面 · ${grids.size} 個網格 · ${timbers.size} 支角材`:`核對 ${rows.length} 項版本或定義變更`}。目前工程尚未改動。</p>`);
    const targetIds=state.intent?.action==='grid'?[state.intent.draft.placementId]:state.intent?.action==='apply'?Object.values(state.intent.draft.targets).map(target=>target.placement_id):state.intent?.action==='sources'?[state.intent.draft.placement_id]:[];
    const diagnosticElements=$('ewReview').querySelectorAll('.ew-diagnostic');
    (result.diagnostics||[]).forEach((diagnostic,index)=>{
      if(diagnostic?.object)return;
      diagnosticElements[index]?.insertAdjacentHTML('beforeend',targetIds.length?`<span class="ew-diagnostic-targets"><br>核心未提供單一問題物件的位置；可查看本次選取的面。<br>${[...new Set(targetIds)].map(id=>`<button type="button" data-ew-locate-fallback data-ew-locate="${esc(JSON.stringify({kind:'placement',id}))}">查看本次目標：${esc(faceName(id))}</button>`).join(' ')}</span>`:' <button type="button" data-ew-return-settings>返回本次設定</button>');
    });
  }
  function renderData(value) {
    if(value==null)return '<span>未設定</span>';
    if(typeof value!=='object')return `<span>${esc(value)}</span>`;
    if(Array.isArray(value))return `<ul>${value.map(item=>`<li>${renderData(item)}</li>`).join('')}</ul>`;
    return `<dl class="ew-data">${Object.entries(value).map(([key,v])=>`<div><dt>${esc(uiLabels[key]||key)}</dt><dd>${renderData(v)}</dd></div>`).join('')}</dl>`;
  }
  function changeSummary(value,collection) {
    if(!value)return null;
    const axisText=axis=>axis==='u'?'沿 u':axis==='v'?'沿 v':'未設定';
    const versionText=(kind,reference)=>{const record=lookupVersion(kind,reference);return record?refText(record):reference?'版本 v'+reference.version:'未設定';};
    if(collection==='grids'){
      const axisSummary=axis=>{const d=value[axis+'Definition'];return d?.source==='panel'?`面材 ${d.panel} mm ＋ 縫 ${d.gap} mm；起算 ${d.anchor} mm`:'目前軸定義請展開核對';};
      return {'所在面':faceName(value.placement_id??value.surface),'主支方向':axisText(value.mainAlong),'u 軸排格':axisSummary('u'),'v 軸排格':axisSummary('v'),'實際格線':`u ${value.u?.length??0} 條 · v ${value.v?.length??0} 條`};
    }
    if(collection==='timbers'){
      const g=value.geometry||value;return {'所在面':faceName(value.placement_id??g.surface),'角色':roles.find(([key])=>key===value.role)?.[1]||'自訂角色','截面':`${g.A??'—'} × ${g.B??'—'} mm`,'長度':g.length==null?'由核心幾何提供':g.length+' mm',...(g.origin?{'原點':g.origin.join?.(', ')??g.origin}:{})};
    }
    if(collection==='sources'||collection==='bindings')return {'物件欄位':targetLabel(value.target),'尺寸來源':sourceLabel(value.source),'物件覆寫':value.override?sourceLabel(value.override):'無，沿用來源','生效尺寸':value.effective==null?'尚未取得':value.effective+' mm'};
    if(collection==='applications'){
      const method=lookupVersion('methods',value.method),panel=lookupVersion('materials',method?.panel),anchors={};
      for(const axis of ['u','v']){const setting=value.anchorOptions?.[axis];anchors[axis+' 軸']=setting?.kind==='edge'?'建立時採本面'+(setting.side==='min'?'下界':'上界'):setting?.kind==='coordinate'?setting.value+' mm':'新建起點尚未設定';}
      return {'套用面':faceName(value.placement_id),'工程做法':versionText('methods',value.method),'面材':panel?`${panel.name} · v${panel.version} · ${panel.width} × ${panel.length} mm`:'未設定','面材長邊':value.longAxis==null?'沿用做法（'+axisText(method?.longAxis)+'）':axisText(value.longAxis),'新建主支方向':value.mainAlong==null?'沿用做法（'+axisText(method?.mainAlong)+'）':axisText(value.mainAlong),'新建起點':anchors,'本面覆寫':Object.keys(value.overrides||{}).length?Object.fromEntries(Object.entries(value.overrides).map(([field,source])=>[sourceFieldLabel(field),sourceLabel(source)])):'無，沿用做法'};
    }
    if(collection==='materials')return {'材料':refText(value),'種類':value.kind==='panel'?'面材':'角材','尺寸':value.kind==='panel'?`${value.width} × ${value.length} mm`:`${value.A} × ${value.B} mm`,...(value.kind==='panel'?{'厚度':value.thickness==null?'未設定':value.thickness+' mm'}:{}),'品牌／型號':[value.brand,value.model].filter(Boolean).join(' · ')||'未填寫','來源與備註':value.notes||'未填寫','封存':value.archived?'已封存':'使用中'};
    if(collection==='methods')return {'工程做法':refText(value),'面材':versionText('materials',value.panel),'角色用料':Object.fromEntries(roles.map(([key,label])=>[label,versionText('materials',value.roles?.[key])])),'縫寬':value.gap==null?'未設定':value.gap+' mm','面材長邊':axisText(value.longAxis),'主支方向':axisText(value.mainAlong),'來源與支撐限制備註':value.notes||'未填寫'};
    const result={...value};delete result.rawValue;delete result.fingerprint;delete result.id;return result;
  }
  function renderDiff(row) {return `<div class="ew-diff-values"><div><h4>目前</h4>${row.before==null?'尚未建立':renderData(changeSummary(row.before,row.collection))}</div><div><h4>套用後</h4>${row.after==null?'已移除':renderData(changeSummary(row.after,row.collection))}</div></div><details><summary>完整定義、識別與核心幾何</summary><div class="ew-diff-values"><div>${renderData(row.before)}</div><div>${renderData(row.after)}</div></div></details>`;}
  async function confirm() {
    if($('ewConfirm').disabled||!state.preview?.token)return;
    if(state.mode==='grid'&&adapter?.isGridContextCurrent?.(state.gridFlow)===false){invalidate();message('畫布已切換，請返回目前面重新開啟網格。','error');return;}
    if(!sameContext(context(),state.context)){close();return;}
    const token=state.preview.token,intent=state.intent;state.busy=true;$('ewConfirm').dataset.committing='true';updateActions();
    try {
      const result=await adapter.confirm({token});
      if(result?.ok===false)throw new Error(result.error||'套用失敗，請重新預覽。');
      if(!sameContext(context(),state.context)){dialog.close();return;}
      state.preview=null;state.intent=null;
      if(intent.action==='publishMaterial'){
        const published=intent.publishedMaterial;
        if(state.method && intent.draft.continueMethod && published){state.method.panel=published;state.section=intent.draft.continueInline?'apply':'methods';state.inlineKind=intent.draft.continueInline?'method':null;}
        else state.inlineKind=null;
        state.material=null;
      }
      if(intent.action==='publishMethod'){
        state.inlineKind=null;
        if(intent.publishedMethod){state.application.method=intent.publishedMethod;state.section='apply';}
        state.method=null;
      }
      if(intent.action==='apply'){
        for(const operation of intent.operations.filter(o=>o.op==='bind-grid'&&o.create)){
          const app=intent.operations.find(o=>o.op==='put-application'&&o.value.id===operation.application)?.value;
          const target=state.application.targets[app?.placement_id];
          if(target){target.gridAction='update';target.gridId=operation.id;target.anchors={u:{mode:'keep',value:''},v:{mode:'keep',value:''}};}
        }
        for(const target of Object.values(state.application.targets)){target.timberIds=[];target.objectOverrides={};target.objectSources={};target.overrides={};}
      }
      if(intent.action==='sources'){
        const target=state.application.targets[intent.draft.placement_id];if(target){target.objectOverrides={};target.objectSources={};}
      }
      if(intent.action==='grid'){
        const binding=intent.operations.find(o=>o.op==='bind-grid'),application=intent.operations.find(o=>o.op==='put-application').value;
        state.gridFlow.gridId=binding.id;state.gridFlow.route='method';state.gridFlow.method=clone(application.method);
        adapter?.gridConfirmed?.({placementId:intent.draft.placementId,gridId:binding.id});
      }
      saveDraft();const reloaded=await load(false);$('ewReview').hidden=true;
      if(intent.action==='grid'&&reloaded!==true){message('網格已確認套用，但最新來源讀取失敗。請按「重新讀取」核對；請勿重複建立網格。','error');return;}
      message(intent.action==='grid'?'已套用到目前工程。網格已依材料固定版本建立；返回畫布可查看格線與來源。按「保存專案」寫入專案檔案。':'已套用到目前工程。按「保存專案」後，才會寫入專案檔案。','success');
    }catch(error){message(error.message,'error');invalidate();}
    finally{state.busy=false;delete $('ewConfirm').dataset.committing;updateActions();}
  }
  function strictJSON(text) {
    if(new TextEncoder().encode(text).length>1048576)throw new Error('做法包超過 1 MiB，請分批整理規格。');
    let at=0;
    const space=()=>{while(/\s/.test(text[at]||'')&&at<text.length)at++;};
    const string=()=>{const start=at++;while(at<text.length){const c=text[at++];if(c==='"')return JSON.parse(text.slice(start,at));if(c==='\\')at++;}throw new Error('JSON 字串未結束。');};
    const value=depth=>{
      if(depth>32)throw new Error('做法包 JSON 層級過深。');space();const c=text[at];
      if(c==='"'){string();return;}
      if(c==='{'||c==='['){const object=c==='{',end=object?'}':']',keys=new Set();at++;space();if(text[at]===end){at++;return;}
        while(at<text.length){if(object){space();if(text[at]!=='"')throw new Error('JSON 欄位名稱格式不正確。');const key=string();if(keys.has(key))throw new Error(`做法包有重複欄位「${key}」，未匯入。`);keys.add(key);space();if(text[at++]!==':')throw new Error('JSON 欄位缺少冒號。');}value(depth+1);space();if(text[at]===end){at++;return;}if(text[at++]!==',')throw new Error('JSON 項目分隔格式不正確。');}
        throw new Error('JSON 容器未結束。');
      }
      const match=text.slice(at).match(/^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/);
      if(!match)throw new Error('JSON 值格式不正確。');at+=match[0].length;
    };
    value(0);space();if(at!==text.length)throw new Error('JSON 結尾有多餘資料。');return JSON.parse(text);
  }
  function exactKeys(value,required,optional=[],where='做法包') {
    if(!value||typeof value!=='object'||Array.isArray(value)||required.some(k=>!Object.hasOwn(value,k))||Object.keys(value).some(k=>!required.includes(k)&&!optional.includes(k)))throw new Error(`${where} 欄位不完整或含未知欄位，整包未匯入。`);
  }
  function validatePackage(value) {
    exactKeys(value,['schema','materials','methods']);
    if(value.schema!=='engineering-package/1')throw new Error('此檔案不是正式工程做法包；原型 JSON 與完整專案請使用各自的開啟方式。');
    if(!Array.isArray(value.materials)||!Array.isArray(value.methods)||value.materials.length>64||value.methods.length>32)throw new Error('做法包的材料／做法目錄格式或數量不合法。');
    const seen=new Set();
    for(const [kind,records] of [['material',value.materials],['method',value.methods]])for(const record of records){
      exactKeys(record,['value','fingerprint','archived'],[],kind+' 版本');
      if(!/^[a-f0-9]{64}$/.test(record.fingerprint)||typeof record.archived!=='boolean')throw new Error('版本指紋或封存狀態格式不合法。');
      const item=record.value;
      const fields=kind==='method'?['id','version','name']:item?.kind==='panel'?['id','version','kind','name','width','length']:item?.kind==='timber'?['id','version','kind','name','A','B']:[];
      const optional=kind==='method'?['panel','roles','gap','longAxis','mainAlong','notes']:item?.kind==='panel'?['thickness','brand','model','notes']:['brand','model','notes'];
      if(!fields.length)throw new Error('材料種類必須為 panel 或 timber。');
      exactKeys(item,fields,optional,kind+' 內容');
      if(!/^[A-Za-z0-9_-]{1,64}$/.test(item.id)||!Number.isInteger(item.version)||item.version<1||item.version>4294967295)throw new Error('版本識別或版本數不合法。');
      const key=kind+':'+refKey(item);if(seen.has(key))throw new Error('做法包重複宣告相同版本，整包未匯入。');seen.add(key);
      if(kind==='method'){
        if(item.roles!=null)exactKeys(item.roles,[],['boundary','primary','secondary'],'角色用料');
        for(const reference of [item.panel,...Object.values(item.roles||{})])if(reference!=null)exactKeys(reference,['id','version'],[],'材料版本引用');
      }
    }
    return value;
  }
  function packageRecords(records) {
    return list(records).map(record=>{
      const value=clone(record.rawValue??record.value??record);
      if(!record.rawValue&&!record.value)for(const field of ['fingerprint','archived','type'])delete value[field];
      return {value:clone(value),fingerprint:record.fingerprint,archived:!!record.archived};
    });
  }
  function importOperations(text) {
    const value=validatePackage(strictJSON(text));
    return [...value.materials.map(record=>({op:'publish-material',value:record.value,fingerprint:record.fingerprint})),...value.methods.map(record=>({op:'publish-method',value:record.value,fingerprint:record.fingerprint})),...['material','method'].flatMap(kind=>value[kind==='material'?'materials':'methods'].map(record=>({op:'archive',kind,...ref(record.value),value:record.archived})))];
  }
  async function exportPackage() {
    try {
      const value={schema:'engineering-package/1',materials:packageRecords(state.snapshot.materials),methods:packageRecords(state.snapshot.methods)};
      validatePackage(value);
      const url=URL.createObjectURL(new Blob([typeof value==='string'?value:JSON.stringify(value,null,2)],{type:'application/json'})),link=document.createElement('a');
      link.href=url;link.download='工程規格-做法包.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message('做法包下載已開始，請確認檔案已存到電腦。');
    }catch(error){message(error.message,'error');}
  }
  return {configure,open,close,refresh:()=>load(false),get isOpen(){return !!dialog?.open;}};
})();
