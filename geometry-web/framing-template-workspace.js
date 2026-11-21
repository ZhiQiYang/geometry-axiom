/* Face properties R03. Displays native candidates; never computes layout geometry. */
window.FramingWorkspace=(()=>{
  'use strict';
  const F=window.GeometryFramingRecipes,Session=window.GeometryFramingSession.Session;
  const clone=v=>JSON.parse(JSON.stringify(v)),esc=v=>ReferenceWorkspace.escape(String(v??''));
  const memberName=kind=>({'boundary':'邊界材','rc_parallel':'平行邊界材','main':'主支','secondary:mark':'記號副支','secondary:seam':'板縫副支'}[kind]||kind);
  let active=null;const retired=new Set();
  const emptySources=()=>({on:'',panel:'',threshold:'',materials:false});
  const stableOwner=bid=>({context:ReferenceWorkspace.context(),incarnation:ReferenceWorkspace.history.frame.ids.get(bid),session:connection.session,bid});
  const owns=o=>o.context===ReferenceWorkspace.context()&&o.incarnation===ReferenceWorkspace.history.frame.ids.get(o.bid)&&o.session===connection.session&&connection.phase==='ready';
  async function post(path,body){
    const session=connection.session,requestId=path==='/framing-template/preview'?crypto.randomUUID():null;
    try{
      const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Geometry-Version':pageRuntimeVersion,...(requestId?{'X-Geometry-Request-Id':requestId,'X-Geometry-Session':session}:{})},body:JSON.stringify(body),signal:AbortSignal.timeout(30000)});
      checkApiSession(response);
      if(!session||session!==connection.session||response.headers.get('X-Geometry-Session')!==session)throw Error('骨架服務的工作階段已改變，請重新連線核對。');
      const result=await response.json();if(!response.ok||typeof result?.ok!=='boolean')throw Error('骨架服務回應不完整。');
      if(requestId)acknowledgedApiResults.add(requestId);return result;
    }catch(error){
      if(requestId){const command='framing-template-preview '+requestId;pendingApiResults.set(requestId,command);
        try{if(session!==connection.session)throw error;const result=await readApiReceipt(requestId);pendingApiResults.delete(requestId);acknowledgedApiResults.add(requestId);return result;}
        catch(_){connectionFailed('骨架預覽結果未明，重新連線將只核對原回執。');throw Object.assign(error,{transport:true,command});}
      }throw error;
    }
  }
  const transport={post,command:cmd=>apiRequest(cmd)};
  const panelList=v=>(v.session.readResult?.sources.panels||[]).map(p=>p.value||p);
  const thresholds=v=>(v.session.readResult?.sources.parameters||[]).flatMap(p=>(p.fields||[]).filter(f=>f.type==='dimension').map(f=>({key:p.id+':'+f.id,label:`${p.name}／${f.name} · ${f.value?.num}/${f.value?.den} mm`,parameterId:p.id,fieldId:f.id})));
  const option=(value,label,current)=>`<option value="${esc(value)}"${String(value)===String(current)?' selected':''}>${esc(label)}</option>`;
  function sourceSelect(name,label,items,value,disabled=false){return `<label>${esc(label)}<select data-ft-field="${name}"${disabled?' disabled':''}>${option('','請明選',value)}${items.map(([id,text])=>option(id,text,value)).join('')}</select></label>`;}
  function display(){if(!active)return;const pane=document.querySelector('#faceInspectorContent [data-fi-pane="prop"]');if(pane)render(pane,active.session.boundaryId,true);}
  function draft(){return F.create(crypto.randomUUID(),'平釘天花');}
  function isSaved(v){return !!v.session.currentRecipe&&!v.dirty&&JSON.stringify(v.recipe)===JSON.stringify(v.session.currentRecipe);}
  function results(v){
    const p=v.session.candidate;if(!p?.members)return '';
    const outer=v.session.readResult?.source.outer||[],xs=outer.map(q=>q[0]),ys=outer.map(q=>q[1]),minX=Math.min(...xs),minY=Math.min(...ys),width=Math.max(...xs)-minX,height=Math.max(...ys)-minY;
    return `<section class="ft-results" aria-label="整組骨架候選"><h3>候選 ${p.members.length} 支 · 確認前未寫入</h3><p>圖與表逐項來自本次原生候選，尺寸單位為 mm。</p><svg role="img" aria-label="邊界材、主支與副支候選" viewBox="${minX} ${minY} ${width} ${height}"><polygon points="${outer.map(q=>q.join(',')).join(' ')}"/>${p.members.map((m,i)=>`<rect data-ft-member="${i}" data-ft-kind="${esc(m.kind)}" x="${m.rect[0]}" y="${m.rect[1]}" width="${m.rect[2]-m.rect[0]}" height="${m.rect[3]-m.rect[1]}"><title>${esc(memberName(m.kind))} · ${m.length} mm</title></rect>`).join('')}</svg><div class="pf-table-scroll"><table><thead><tr><th>角色</th><th>位置矩形</th><th>長度</th><th>寬×厚</th></tr></thead><tbody>${p.members.map((m,i)=>`<tr data-ft-member-row="${i}"><td>${esc(memberName(m.kind))}</td><td>${m.rect.join(', ')}</td><td>${m.length}</td><td>${m.A} × ${m.B}</td></tr>`).join('')}</tbody></table></div></section>`;
  }
  function render(pane,bid,force=false){
    const v=active;if(!v||v.session.boundaryId!==Number(bid))return false;
    if(pane.id==='faceInspectorContent')pane=pane.querySelector('[data-fi-pane="prop"]')||pane;
    const previous=pane.querySelector('[data-ft-workspace]');if(!force&&previous===v.region)return true;
    const focused=previous?.contains(document.activeElement)?document.activeElement:null,focusKey=focused?.dataset.ftField||focused?.dataset.ftAction,focusAction=!!focused?.dataset.ftAction,selection=focused?.tagName==='INPUT'?[focused.selectionStart,focused.selectionEnd]:null;
    const s=v.session,r=v.recipe,readonly=!F.availability(r).canGenerate,busy=s.pending,locked=busy||readonly||s.retired,available=!!s.readResult&&!s.retired&&!['stale','unknown'].includes(s.phase);
    const numeric=[['panelWidth','板寬 width'],['panelLength','板長 length'],['gap','板縫'],['timberWidth','角材寬 A'],['timberDepth','角材厚 B'],['maxSecondarySpacing','副支最大間距 M']];
    pane.innerHTML=`<section class="pf-workspace ft-workspace" data-ft-workspace="${bid}" aria-labelledby="ftTitle"><div class="pf-heading"><h2 id="ftTitle" tabindex="-1">平釘天花骨架</h2><button type="button" data-ft-action="close"${['previewing','confirming','cancelling','unknown'].includes(s.phase)?' disabled':''}>返回面設定</button></div>
      <label>面內工作<select data-face-product-mode${busy||v.dirty?' disabled':''}><option value="finish">完成面與鋪排</option><option value="framing" selected>平釘天花骨架（矩形第一片）</option></select></label>
      <section class="ft-scope" aria-label="第一片範圍"><strong>矩形第一片：無孔、無柱，邊界明設 RC。</strong><p>從起鋪牆整片開始，裁切只在對牆；主支整支連續。副支每條板端縫重新起算，採上界公式。與既有模板規則不相容的尺寸或排法會明確拒絕，不能確認。</p><p>例如既有 3700 mm 案例需要退縫，本片回報規則衝突。現在不搜尋其他角或方向；請自行明選後重新預覽。</p></section>
      <p class="pf-status" data-ft-status="${s.phase}" role="status" aria-live="polite">${esc(readonly?F.availability(r).reason:s.reason)}</p>
      <fieldset${busy?' disabled':''}><legend>1 · 保存配方意圖（獨立一筆歷史）</legend>${sourceSelect('recipe','專案配方',s.recipes.map(r=>[r.id,r.name+' · '+r.template.id+'/'+r.template.version]),s.currentRecipe?.id||'')}<div class="ft-recipe-actions"><button type="button" data-ft-action="new">新增配方</button><button type="button" data-ft-action="copy"${readonly?' disabled':''}>複製為新配方</button><button type="button" data-ft-action="delete"${!s.currentRecipe?' disabled':''}>刪除所選配方</button></div>
      <fieldset${readonly?' disabled':''}><legend>配方預設</legend><label>配方名稱<input data-ft-field="name" maxlength="160" value="${esc(r.name)}"></label><div class="pf-fields">${numeric.map(([key,label])=>`<label>${label}（mm）<input data-ft-field="defaults.${key}" type="number" step="1" min="${key==='gap'?0:1}" value="${esc(r.defaults[key])}"></label>`).join('')}
      <label>起鋪角<select data-ft-field="corner">${[['min-min','預覽圖左上'],['max-min','預覽圖右上'],['min-max','預覽圖左下'],['max-max','預覽圖右下']].map(([key,label])=>option(key,label,r.preference.corner)).join('')}</select></label><label>板長欄位沿<select data-ft-field="lengthAlong">${[['u','面 u 軸'],['v','面 v 軸']].map(([key,label])=>option(key,label,r.preference.lengthAlong)).join('')}</select></label></div><button type="button" data-ft-action="save">保存配方</button></fieldset><p class="ft-source-note">固定模板 ${esc(r.template.id)}/${r.template.version}；保存配方不生成骨架。保存重開不升版，也不重新搜尋。</p></fieldset>
      <fieldset${locked||!available?' disabled':''}><legend>2 · 本次明選來源（不存入配方）</legend>${sourceSelect('on','目前封閉面的放置框架',(s.readResult?.source.placements||[]).map(p=>[p.id,`放置面 ${p.id} · 原點 ${p.frame.origin.join(', ')} · u ${p.frame.u}／v ${p.frame.v}`]),v.sources.on)}${sourceSelect('panel','已發布板材固定版本',panelList(v).map(p=>[JSON.stringify([p.id,p.version]),`${p.name} · v${p.version} · ${p.width} × ${p.length} × ${p.thickness} mm`]),v.sources.panel)}${sourceSelect('threshold','承接門檻 X 的參數欄位',thresholds(v).map(p=>[p.key,p.label]),v.sources.threshold)}<label class="pf-toggle"><input data-ft-field="materials" type="checkbox"${v.sources.materials?' checked':''}>本次邊界採 RC，角材寬 A／厚 B 採配方明設整數。板寬／板長須與選定材料版本相符。</label></fieldset>
      <div class="ft-recipe-actions"><button type="button" data-ft-action="materials"${busy?' disabled':''}>準備板材來源／返回骨架</button><button type="button" data-ft-action="threshold"${busy?' disabled':''}>獨立建立 8 mm 門檻 X</button><button type="button" data-ft-action="reload"${busy?' disabled':''}>重新讀取來源</button></div><p class="ft-source-note">來源須各自預覽並確認；取消本次骨架不撤回先前已保存的配方或來源。返回後仍須明選，不會沿用已失效的綁定。</p>
      ${results(v)}<div class="pf-actions"><button type="button" data-ft-action="preview"${locked||!available||!isSaved(v)?' disabled':''}>預覽整組骨架</button><button type="button" data-ft-action="confirm"${s.phase!=='confirmable'||s.retired?' disabled':''}>確認骨架（一筆歷史）</button><button type="button" data-ft-action="cancel"${['previewing','confirming','cancelling','unknown'].includes(s.phase)?' disabled':''}>取消本次生成</button></div></section>`;
    const region=pane.querySelector('[data-ft-workspace]');v.region=region;
    region.addEventListener('input',event=>change(v,event));region.addEventListener('change',event=>change(v,event));
    region.addEventListener('click',event=>{const button=event.target.closest('[data-ft-action]');if(button&&!button.disabled){event.preventDefault();act(v,button.dataset.ftAction);}});
    region.addEventListener('keydown',event=>{if(event.isComposing||event.keyCode===229)return;if(event.key==='Escape'){event.preventDefault();event.stopPropagation();act(v,'cancel');}if(event.key==='Enter'&&event.target.matches('input,select'))event.preventDefault();});
    region.querySelector('[data-face-product-mode]').addEventListener('change',event=>{if(event.target.value==='finish'&&close())window.PanelFillWorkspace.open(bid,v.trigger);});
    let focus=focusKey?region.querySelector(`[data-ft-${focusAction?'action':'field'}="${focusKey}"]`):region.querySelector('#ftTitle');
    if(focus?.disabled||focus?.closest('fieldset[disabled]'))focus=region.querySelector('#ftTitle');focus?.focus({preventScroll:true});if(selection&&focus?.setSelectionRange&&selection[0]!==null)try{focus.setSelectionRange(...selection);}catch(_){}return true;
  }
  function change(v,event){
    if(v!==active||v.session.pending)return;const el=event.target,key=el.dataset.ftField;if(!key)return;if(event.type==='input'&&el.tagName==='SELECT')return;if(event.type==='change'&&el.tagName==='INPUT'&&el.type!=='checkbox')return;
    if(key==='recipe'){if(!el.value)return;try{v.recipe=v.session.select(el.value);v.dirty=false;v.sources=emptySources();display();}catch(error){v.session.reason=error.message;display();}return;}
    if(['on','panel','threshold','materials'].includes(key)){v.sources[key]=key==='materials'?el.checked:el.value;v.session.selectedSource=null;return;}
    if(!F.availability(v.recipe).canGenerate)return;
    if(key.startsWith('defaults.'))v.recipe.defaults[key.slice(9)]=el.value;else if(key==='corner'||key==='lengthAlong')v.recipe.preference[key]=el.value;else v.recipe.name=el.value;
    v.dirty=true;v.session.reason='配方預設尚未保存；先保存配方，再預覽本次骨架。';
    const status=v.region?.querySelector('[data-ft-status]');if(status)status.textContent=v.session.reason;v.region?.querySelector('[data-ft-action="preview"]')?.setAttribute('disabled','');
  }
  function validatedRecipe(v){const r=clone(v.recipe);for(const key of Object.keys(F.DEFAULTS)){const raw=String(r.defaults[key]);if(!/^\d+$/.test(raw)||!Number.isSafeInteger(Number(raw)))throw Error('尺寸須明設整數 mm。');r.defaults[key]=Number(raw);}return F.validateRecipe(r);}
  function takeSources(v){if(v.sources.on===''||!v.sources.materials||!v.sources.panel||!v.sources.threshold)throw Error('請明選放置框架、固定板材、承接門檻，並確認 RC／角材語意。');const panel=JSON.parse(v.sources.panel),[parameterId,fieldId]=v.sources.threshold.split(':').map(Number);v.session.selectSource(Number(v.sources.on),{boundary:'rc',timber:'literal'},{panel:{id:panel[0],version:panel[1]},threshold:{parameterId,fieldId}});}
  async function returnTo(v,owner){
    if(!owns(owner))throw Error('原專案、封閉面或服務已變更，請重新由面設定開啟骨架。');
    const before=oc.navigationSequence,pending=enterFocus('face',owner.bid),focus=oc.focus,nav=oc.navigationSequence;await pending;
    if(!owns(owner)||nav!==before+1||oc.navigationSequence!==nav||oc.focus!==focus||focus?.id!==owner.bid)return;
    fiShowTab('prop');if(innerWidth<=900)openPanel('right',document.getElementById('workspaceToggleRight'));
    const okay=await open(owner.bid,null);if(!okay||!active||!owns(owner))return;
    const next=active;next.recipe=clone(v.recipe);next.dirty=v.dirty;const saved=next.session.recipes.find(r=>r.id===v.session.currentRecipe?.id);if(saved)next.session.select(saved.id);
    next.sources=emptySources();next.session.reason='已返回骨架並重讀來源；配方輸入保留，請重新明選本次框架、板材與 X。';display();
  }
  async function prepareSource(v,kind){
    v.session.assertIdle();const owner=stableOwner(v.session.boundaryId);if(!close())return;
    if(kind==='threshold'){await window.ParameterUI.create({proposal:'framing-template-threshold',isCurrent:()=>owns(owner),onConfirmed:()=>{},onReturn:()=>returnTo(v,owner)});return;}
    await window.EngineeringWorkspace.open({section:'materials',returnLabel:'返回原面骨架（重新讀取）'});
    const dialog=document.getElementById('ewWorkspace');if(dialog?.open)dialog.addEventListener('close',()=>{returnTo(v,owner).catch(error=>toast(error.message));},{once:true});
  }
  async function act(v,action){
    if(v!==active)return;const s=v.session;
    try{
      if(action==='close'){close();return;}
      if(action==='cancel'){await s.cancel();if(active!==v)return;v.sources=emptySources();v.dirty=false;v.recipe=s.currentRecipe?clone(s.currentRecipe):draft();display();return;}
      if(action==='materials'||action==='threshold'){await prepareSource(v,action);return;}
      if(action==='reload'){await s.open();v.sources=emptySources();const saved=s.recipes.find(r=>r.id===v.recipe.id);if(saved)s.select(saved.id);display();return;}
      if(action==='new'||action==='copy'){s.assertIdle();const r=action==='new'?draft():validatedRecipe(v);if(action==='copy'){F.assertGeneratable(r);r.id=crypto.randomUUID();r.name+=' 副本';}s.currentRecipe=null;v.recipe=r;v.sources=emptySources();v.dirty=true;display();return;}
      if(action==='delete'){s.remove(s.currentRecipe.id);v.recipe=draft();v.sources=emptySources();v.dirty=false;display();return;}
      if(action==='save'){v.recipe=s.save(validatedRecipe(v));v.dirty=false;v.sources=emptySources();display();ReferenceWorkspace.present();return;}
      if(action==='preview'){if(!isSaved(v))throw Error('配方仍有未保存內容。');takeSources(v);const pending=s.preview();display();await pending;}
      if(action==='confirm'){const pending=s.confirm();display();const result=await pending;if(result.ok&&s.phase==='committed'){
        const context=ReferenceWorkspace.context(),frame=ReferenceWorkspace.history.frame,session=connection.session;
        const current=()=>active===v&&context===ReferenceWorkspace.context()&&frame===ReferenceWorkspace.history.frame&&session===connection.session;
        await renderObjects({current});if(current())await feAfterChange(current);
      }}
      if(active===v)display();ReferenceWorkspace.present();
    }catch(error){if(active===v){s.reason=(s.phase==='committed'?'骨架已確認，但畫面重新讀取未完成；請重新讀取來源。':'')+error.message;display();}}
  }
  async function open(bid,trigger){if(active&&!close())return false;const s=new Session({host:ReferenceWorkspace,transport,boundaryId:Number(bid)}),v={session:s,recipe:draft(),sources:emptySources(),dirty:false,trigger};active=v;display();try{const pending=s.open();display();await pending;if(active!==v||s.retired)return false;const recipes=s.recipes;if(recipes.length){v.recipe=s.select(recipes[0].id);}display();return true;}catch(error){if(active===v){s.reason=error.message;display();}return false;}}
  function close(){const v=active;if(!v)return true;const s=v.session;if(s.pending){s.reason='請先按取消本次生成；結果未明時須先重新連線核對原回執。';display();return false;}active=null;renderFaceInspector();const entry=document.querySelector(`[data-face-settings="${s.boundaryId}"]`);(entry||(v.trigger?.isConnected?v.trigger:null))?.focus({preventScroll:true});ReferenceWorkspace.present();return true;}
  function invalidate(reason){if(active){active.session.invalidate(reason);display();}}
  function retireContext(){const v=active;if(!v)return;active=null;v.session.retire();if(v.session.pending)retired.add(v.session);}
  async function settleRecovered(command,result){for(const s of [...(active?[active.session]:[]),...retired]){const handled=command.startsWith('framing-template-preview ')?await s.settlePreviewReceipt(command,result):s.settleRecovered(command,result);if(handled){if(!s.pending)retired.delete(s);display();ReferenceWorkspace.present();return true;}}return false;}
  function isRecoveryCancel(command){return [...(active?[active.session]:[]),...retired].some(s=>s.candidate&&command===`framing-template-cancel ${s.candidate.token} ${s.ownerKey}`);}
  window.addEventListener('geometry-definition-changed',event=>{if(active?.session.pendingCommand===event.detail?.command)return;invalidate('定義來源已變更，舊候選不可確認；請取消並重新讀取來源。');});
  window.addEventListener('space-models-changed',()=>{if(active&&!active.session.current()&&!['confirming','cancelling','unknown'].includes(active.session.phase))invalidate('專案或歷史已改變，請取消並重新讀取來源。');});
  return {open,close,render,invalidate,retireContext,settleRecovered,isRecoveryCancel,activeFor:bid=>active?.session.boundaryId===Number(bid),get pending(){return !!active&&(active.session.pending||active.dirty)||[...retired].some(s=>s.pending);},get isOpen(){return !!active;}};
})();
