/* PF-6 form inside the existing face inspector. No geometry is constructed here. */
window.PanelFillBuilderWorkspace=(()=>{
  'use strict';
  const M=window.PanelFillBuilderSession,clone=v=>JSON.parse(JSON.stringify(v));
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const list=value=>Array.isArray(value)?value:[],retired=new Set();let active=null;
  const uint=value=>Number.isInteger(value)&&value>=0&&value<=4294967295;
  const positiveToken=value=>Number.isInteger(value)&&value>0&&value<=4294967295;
  const definitionKind=kind=>({placement:'宿主',grid:'主格',timber:'角材'}[kind]||kind);
  const createdDefinitions=rows=>Array.isArray(rows)&&rows.every(row=>row&&Object.keys(row).sort().join(',')==='candidateId,kind,tempKey'&&
    ['placement','grid','timber'].includes(row.kind)&&uint(row.candidateId)&&typeof row.tempKey==='string'&&row.tempKey.length>0)&&
    new Set(rows.map(row=>row.tempKey)).size===rows.length;
  const temporaryCandidate=p=>p?.candidateIdsAreTemporary===true&&p.idMap===null&&createdDefinitions(p.createdDefinitions);
  const candidateIdentity=(kind,id,created)=>created?`<span data-pf6-temporary="${esc(kind)}:${esc(id)}">候選暫號 #${esc(id)}（尚未正式建立）</span>`:`既有正式 #${esc(id)}`;
  const phaseName=phase=>({'boundary':'邊材','edge-primary':'邊界主支','seam-primary':'板縫主支','seam-secondary':'板縫副支','free-edge':'FREE 邊無邊材','covered-edge':'已有邊材覆蓋，不重複提出','hole-edge':'孔環不提出邊材'}[phase]||phase);
  const roleName=role=>({'boundary':'邊材','primary':'主支','secondary':'副支'}[role]||role);
  const material=row=>row?.value?row.value:row;
  function sourceValue(d,field){
    if(!d||!['A','B'].includes(field))throw Error('請明選 A／B 來源。');let value;
    if(d.kind==='literal'){
      if(!/^[1-9]\d*$/.test(d.value)||!Number.isSafeInteger(Number(d.value)))throw Error(field+' 須明設正整數 mm。');value={kind:'literal',value:Number(d.value)};
    }else if(d.kind==='spec')value={kind:'spec',name:d.value};
    else if(d.kind==='parameter'){
      if(!/^(0|[1-9]\d*):(0|[1-9]\d*)$/.test(d.value))throw Error('請明選尺寸卡與欄位。');
      const [parameterId,fieldId]=d.value.split(':').map(Number);value={kind:'parameter',parameterId,fieldId};
    }else if(d.kind==='material'){
      let pair;try{pair=JSON.parse(d.value);}catch(_){throw Error('請明選固定角材材料版本。');}
      if(!Array.isArray(pair)||pair.length!==2)throw Error('請明選固定角材材料版本。');value={kind:'material',id:pair[0],version:pair[1],field};
    }
    if(!M.source(value,field))throw Error(field+' 來源尚未明選或不合法。');return value;
  }
  const dimensionText=d=>d?`${d.name||'尺寸來源'}${d.cardName?'／'+d.cardName:''}${d.fieldName?'／'+d.fieldName:''}：${d.effective===null?'無法求值':d.effective+' mm'}`:'尚未取得來源';
  function sourceText(s,d,field){
    let value;try{value=sourceValue(d,field);}catch(_){return '尚未明選來源';}
    if(value.kind==='literal')return '明設 '+value.value+' mm';
    if(value.kind==='spec'){const r=list(s.sources?.specs).find(r=>r.name===value.name);return `具名尺寸 ${value.name}${r?'：'+r.value+' mm':''}`;}
    if(value.kind==='material'){const r=list(s.sources?.materials).map(material).find(r=>r.id===value.id&&r.version===value.version);return `${r?.name||value.id} · v${value.version} · ${field}＝${r?.[field]??'未讀取'} mm`;}
    const card=list(s.sources?.parameters).find(p=>p.id===value.parameterId),f=list(card?.fields).find(f=>f.id===value.fieldId);
    return `${card?.name||'卡 #'+value.parameterId}／${f?.name||'欄 #'+value.fieldId}${f?.value?'：'+f.value.num+'/'+f.value.den+' mm':''}`;
  }
  const option=(value,text,selected)=>`<option value="${esc(value)}"${String(value)===String(selected)?' selected':''}>${esc(text)}</option>`;
  const select=(label,name,value,items)=>`<label>${esc(label)}<select data-pf6-field="${name}">${option('','請明選',value)}${items.map(([v,t])=>option(v,t,value)).join('')}</select></label>`;
  function sourceForm(s,d,field){
    let editor='';
    if(d.kind==='literal')editor=`<label>${field} 明設值（mm）<input data-pf6-field="${field}.value" inputmode="numeric" value="${esc(d.value)}"></label>`;
    if(d.kind==='spec')editor=select('具名尺寸',field+'.value',d.value,list(s.sources?.specs).map(r=>[r.name,r.name+'＝'+r.value+' mm']));
    if(d.kind==='material')editor=select('固定角材版本 '+field,field+'.value',d.value,list(s.sources?.materials).map(material).filter(r=>r.kind==='timber').map(r=>[JSON.stringify([r.id,r.version]),`${r.name} · v${r.version} · ${field}＝${r[field]} mm`]));
    if(d.kind==='parameter')editor=select('尺寸參數欄位',field+'.value',d.value,list(s.sources?.parameters).flatMap(p=>list(p.fields).filter(f=>f.type==='dimension').map(f=>[p.id+':'+f.id,`${p.name}／${f.name}＝${f.value?.num}/${f.value?.den} mm`])));
    return `<fieldset class="pf-source"><legend>${field==='A'?'角材寬 A':'角材厚 B（朝宿主 +N）'}</legend>${select('來源種類',field+'.kind',d.kind,[['literal','明設整數 mm'],['spec','具名尺寸'],['material','固定角材材料版本'],['parameter','尺寸參數欄位']])}${editor}<output data-pf6-source="${field}">${esc(sourceText(s,d,field))}</output></fieldset>`;
  }
  function sourceLocation(e){const r=e.source;if(['boundary','edge-primary','free-edge','covered-edge','hole-edge'].includes(e.phase))return `${e.phase==='hole-edge'?'孔環':'外環'}衍生邊 · 來源鍵 ${r.edgeKey??'未提供'} · ${e.axis==='u'?'沿 U':'沿 V'} · 區間 ${r.range.join('～')} mm`;return `固定 ${r.lineAxis} 的縫 #${r.k}${r.band!==null?'／板列 '+r.band:''} · 區間 ${r.range.join('～')} mm`;}
  const diagnostic=e=>list(e.diagnostics).map(d=>`${d.clause||'原生條件'}：${d.message||d.actual||'未成立'}`).join('；');
  function plan(s){
    const r=s.suggestions;if(!r)return '';
    const enabled=r.valid===true&&r.appView?.completeForScope===true&&!s.busy&&!s.retired&&!['committed','stale','unknown','cleanup-required','confirm-not-sent'].includes(s.phase);
    return `<section aria-label="角材建議與明選集合"><h3>建議 ${r.entries.length} 個來源 · 本次已選 ${list(s.selected).length} 個來源</h3><div class="pf6-selection-actions"><button type="button" data-pf6-action="all"${enabled?'':' disabled'}>選取全部可選項</button><button type="button" data-pf6-action="none"${enabled?'':' disabled'}>清空明選集合</button></div><div class="pf6-cards">${r.entries.map((e,i)=>`<article data-pf6-entry="${esc(e.key)}"><label class="pf6-pick"><input type="checkbox" data-pf6-select="${esc(e.key)}"${list(s.selected).includes(e.key)?' checked':''}${enabled&&e.selectable&&e.valid?'':' disabled'}><span>第 ${i+1} 項 · ${esc(phaseName(e.phase))}</span></label><p>${esc(sourceLocation(e))}</p><p>建議長 ${esc(e.geometry.length)} mm · ${esc(roleName(e.role))}</p><p>${esc(dimensionText(r.appView?.input.A))}；${esc(dimensionText(r.appView?.input.B))}</p>${e.duplicateOf?'<p>與另一來源指向同一支角材；預覽將按原生結果去重。</p>':''}${diagnostic(e)?'<p class="pf-warning">'+esc(diagnostic(e))+'</p>':''}</article>`).join('')}</div>${r.omissions.length?`<details><summary>未提出建議的邊（${r.omissions.length}）</summary><ul>${r.omissions.map(e=>`<li>${esc(phaseName(e.phase))} · ${esc(sourceLocation(e))}${diagnostic(e)?'；'+esc(diagnostic(e)):''}</li>`).join('')}</ul></details>`:''}${r.error?'<p role="alert">本輪原生診斷：'+esc(r.error)+'</p>':''}</section>`;
  }
  function support(view,stage,fillId){
    const fill=view?.uiContract?.[stage]?.panelFills?.find(f=>f.definition.id===fillId),d=fill?.derived;
    if(!d||d.error)return '<p role="alert">'+esc(d?.error||'缺少完整承接投影')+'</p>';
    const x=d.threshold?d.threshold.num+'/'+d.threshold.den:'未提供';
    return `<section><h4>${stage==='before'?'確認前':'本次候選後'}逐縫承接</h4><p>門檻 X＝${esc(x)} mm；每側分別比較，承接不足仍可保存合法幾何。</p>${d.support.length?`<ol class="pf6-support">${d.support.map(p=>{const seam=d.effectiveSeams[p.seam];return `<li data-pf6-support="${stage}:${p.seam}:${esc(p.range.join(':'))}" data-supported="${p.supported}">固定 ${esc(seam?.axis)} 的縫 #${esc(seam?.k)}${seam?.band!==undefined?'／板列 '+esc(seam.band):''} · ${esc(p.range.join('～'))} mm：左 ${esc(p.left)} mm／右 ${esc(p.right)} mm；X ${esc(x)} mm；${p.supported?'已承接':'承接不足'}</li>`;}).join('')}</ol>`:'<p>目前沒有有效板縫；沒有把外緣或孔邊當成板縫。</p>'}</section>`;
  }
  const labels={id:'識別',surface:'宿主',role:'角色',length:'長度',centerline:'中線',origin:'世界原點',axes:'世界方向',dir:'長度方向',side:'厚度方向',u:'u 座標',v:'v 座標',A:'寬 A',B:'厚 B',source:'定義來源',effective:'有效值',unit:'單位',kind:'來源類型',value:'明設值',name:'名稱',cardName:'卡片',fieldName:'欄位',path:'來源路徑',parameterId:'參數卡識別',fieldId:'欄位識別',version:'固定版本',field:'材料欄位',start:'起點',end:'終點',rect:'足跡',geometry:'幾何',placed:'已放置'};
  function detailsRows(value,prefix=''){
    if(value===null||value===undefined)return [[prefix,'無']];
    if(typeof value!=='object')return [[prefix,typeof value==='boolean'?(value?'是':'否'):String(value)]];
    if(Array.isArray(value)){if(value.every(v=>v===null||typeof v!=='object'))return [[prefix,value.map(v=>v===null?'無':String(v)).join('，')]];return value.flatMap((v,i)=>detailsRows(v,prefix+'／第 '+(i+1)+' 項'));}
    return Object.entries(value).flatMap(([name,v])=>detailsRows(v,(prefix?prefix+'／':'')+(labels[name]||name)));
  }
  function timberDetails(view){return `<details class="pf6-impact"><summary>完整角材影響（含既有物件及來源）</summary>${list(view?.timbers).map(row=>`<article><h4>角材 ${candidateIdentity('timber',row.id,row.before===null)}</h4><table><thead><tr><th>欄位</th><th>確認前</th><th>候選後</th></tr></thead><tbody>${(()=>{const before=new Map(detailsRows(row.before)),after=new Map(detailsRows(row.after)),names=[...new Set([...before.keys(),...after.keys()])];return names.map(name=>`<tr><th>${esc(name)}</th><td>${esc(before.get(name)??'無')}</td><td>${esc(after.get(name)??'無')}</td></tr>`).join('');})()}</tbody></table></article>`).join('')||'<p>本次沒有角材影響。</p>'}</details>`;}
  function picture(entries){
    const rects=entries.filter(e=>e.selected&&e.valid&&BigInt(e.geometry.length)>0n).map(e=>({e,rect:e.geometry.rect.map(Number)}));
    if(!rects.length||rects.some(r=>r.rect.some(n=>!Number.isSafeInteger(n))))return '';
    const x=Math.min(...rects.map(r=>r.rect[0])),y=Math.min(...rects.map(r=>r.rect[1])),w=Math.max(...rects.map(r=>r.rect[2]))-x,h=Math.max(...rects.map(r=>r.rect[3]))-y;
    return `<svg class="pf6-plan" role="img" aria-label="本次所選角材的原生足跡；展示座標不回寫幾何" viewBox="${x} ${y} ${w||1} ${h||1}">${rects.map(({e,rect})=>`<rect data-pf6-picture="${esc(e.key)}" tabindex="0" x="${rect[0]}" y="${rect[1]}" width="${rect[2]-rect[0]}" height="${rect[3]-rect[1]}"><title>${esc(phaseName(e.phase))} · ${esc(e.geometry.length)} mm</title></rect>`).join('')}</svg>`;
  }
  function confirmedIdentities(s){
    const rows=s.receipt?.actionReceipt?.idMap,expected=s.committedDefinitions;
    const complete=s.receipt?.ok===true&&createdDefinitions(expected)&&Array.isArray(rows)&&rows.length===expected.length&&
      new Set(rows.map(row=>row?.tempKey)).size===rows.length&&rows.every(row=>row&&Object.keys(row).sort().join(',')==='id,kind,tempKey'&&
        uint(row.id)&&expected.some(before=>before.tempKey===row.tempKey&&before.kind===row.kind));
    if(!complete)return '<section class="pf6-results"><p role="alert">確認已完成；正式識別對照未確認，請返回並重新讀取正式來源。</p></section>';
    return `<section class="pf6-results" aria-label="原生確認回執的正式識別"><h3>已確認建立：正式識別</h3><p>以下正式識別取自本次原生確認回執。預覽中的候選暫號只用來核對，不代替正式識別。</p><table><thead><tr><th>物件</th><th>候選暫號</th><th>正式識別</th></tr></thead><tbody>${rows.map(row=>`<tr data-pf6-formal="${esc(row.kind)}:${row.id}"><th>${esc(definitionKind(row.kind))}</th><td>#${expected.find(before=>before.tempKey===row.tempKey).candidateId}</td><td>#${row.id}</td></tr>`).join('')}</tbody></table></section>`;
  }
  function results(s){
    if(s.phase==='committed')return confirmedIdentities(s);
    const p=s.candidate;if(!p)return '';
    if(p.phase==='NO_OP')return '<section class="pf6-results"><h3>沒有建立項目</h3><p>空集合沒有建立宿主、主格或角材，也沒有產生可確認令牌與歷史。</p></section>';
    const view=p.appView,count=new Set(list(p.createdDefinitions).filter(r=>r.kind==='timber').map(r=>r.candidateId)).size,selected=list(p.entries).filter(e=>e.selected);
    return `<section class="pf6-results" aria-label="明選集合的最終原生預覽"><h3>本次 ${selected.length} 個來源，新增 <span data-pf6-created-count>${count}</span> 支角材</h3><p>本區使用本次所選集合重新求值的結果。宿主：${candidateIdentity('placement',view?.host?.id,view?.host?.created)}；主格：${candidateIdentity('grid',view?.grid?.id,view?.grid?.created)}。</p><p>${esc(dimensionText(view?.input.A))}；${esc(dimensionText(view?.input.B))}；宿主 h：${esc(dimensionText(view?.host?.h))}</p>${picture(selected)}<div class="pf6-cards">${selected.map(e=>{const old=s.suggestions?.entries?.find(r=>r.key===e.key);return `<article data-pf6-member="${esc(e.key)}" tabindex="-1"><h4>${esc(phaseName(e.phase))} · ${esc(roleName(e.role))}</h4><p>最終長度 ${esc(e.geometry.length)} mm${old&&old.geometry.length!==e.geometry.length?'（原建議 '+esc(old.geometry.length)+' mm）':''}</p><p>${esc(sourceLocation(e))} · 足跡 ${esc(e.geometry.rect.join('，'))} mm</p>${e.duplicateOf?'<p>與另一選取來源共用同一支；新增支數已去重。</p>':''}${diagnostic(e)?'<p class="pf-warning">'+esc(diagnostic(e))+'</p>':''}</article>`;}).join('')}</div>${support(view,'before',s.fillId)}${support(view,'after',s.fillId)}${timberDetails(view)}${list(p.violations).length?'<section role="alert"><h4>逐條原生違規</h4><ul>'+p.violations.map(v=>`<li>${esc(v.clause||v.code)}：${esc(v.message)}${v.expected?'；預期 '+esc(v.expected):''}</li>`).join('')+'</ul></section>':''}</section>`;
  }
  function mayConfirm(s){
    const p=s.candidate;if(!s.confirmable||p?.valid!==true||p.phase!=='SELECTED'||!positiveToken(p.token)||!temporaryCandidate(p)||p.appView?.completeForScope!==true||p.appView?.uiContract?.completeForScope!==true)return false;
    try{M.validateView(p.appView,{revision:s.suggestions.revision,setKey:s.suggestions.setKey,generation:s.suggestions.generation,phase:'SELECTED',input:s.input||s.suggestions.intent.input,selected:s.selected});return true;}catch(_){return false;}
  }
  function markup(v){
    const s=v.session,d=v.draft,busy=s.busy||['suggesting','selecting','confirming','cancelling','unknown'].includes(s.phase),locked=busy||s.retired||['committed','stale','cleanup-required','confirm-not-sent'].includes(s.phase);
    const r=s.snapshot?.panelFills?.find(f=>f.definition.id===s.fillId),finish=s.snapshot?.finishSurfaces?.find(f=>f.id===r?.definition.finishSurfaceId),panel=list(s.sources?.materials).map(material).find(m=>m.id===r?.definition.panel.id&&m.version===r?.definition.panel.version);
    return `<section class="pf-workspace pf6-workspace" data-pf6-workspace="${s.boundaryId}" aria-labelledby="pf6Title"><div class="pf-heading"><h2 id="pf6Title" tabindex="-1">建議角材</h2><button type="button" data-pf6-action="close"${busy?' disabled':''}>返回完成面與鋪排</button></div><p>${esc(finish?.name||'完成面')} · 正式鋪排 #${s.fillId}${panel?' · '+esc(panel.name)+' v'+panel.version+' · '+panel.width+' × '+panel.length+' mm':''}</p><p class="pf-status" data-pf6-status="${s.phase}" role="status" aria-live="polite">${esc(s.reason)}</p><fieldset${locked?' disabled':''}><legend>本次明選來源</legend>${sourceForm(s,d.A,'A')}${sourceForm(s,d.B,'B')}${select('主支走向（副支沿另一軸）','primaryAlong',d.primaryAlong,[['u','主支沿面 U／副支沿面 V'],['v','主支沿面 V／副支沿面 U']])}<p>固定 u 的板縫實際沿 V；固定 v 的板縫實際沿 U。交丁的錯開軸只能是副支。</p><button type="button" data-pf6-action="suggest"${locked?' disabled':''}>取得建議</button></fieldset><details><summary>範圍與原生判定</summary><p>本次只從所選正式鋪排提出外環 FIXED 邊材與有效板縫角材，不補板中間支撐、吊筋或樓板連接，不判定結構安全。取消只退役本次候選，不撤回先前確認的來源。</p><p>同一時間只有一個候選交易。已有覆蓋的邊不重複提出；其他碰撞或既有主支軸不符會由原生拒絕，不自動刪除、改位或重建既有 R03 骨架。</p></details>${plan(s)}${results(s)}<div class="pf-actions"><button type="button" data-pf6-action="preview"${locked||!s.suggestions?.valid||!s.suggestions?.appView?.completeForScope?' disabled':''}>預覽所選集合</button><button type="button" data-pf6-action="confirm"${mayConfirm(s)?'':' disabled'}>確認建立（一筆歷史）</button><button type="button" data-pf6-action="cancel"${['confirming','cancelling','unknown'].includes(s.phase)?' disabled':''}>取消本次建議</button></div></section>`;
  }
  function display(){if(!active)return;const pane=document.querySelector('#faceInspectorContent [data-fi-pane="prop"]');if(pane)render(pane,active.session.boundaryId,true);}
  function render(pane,bid,force=false){
    const v=active;if(!v||v.session.boundaryId!==Number(bid))return false;if(pane.id==='faceInspectorContent')pane=pane.querySelector('[data-fi-pane="prop"]')||pane;
    if(!force&&pane.querySelector('[data-pf6-workspace]')===v.region)return true;
    const focused=v.region?.contains(document.activeElement)?document.activeElement:null,field=focused?.dataset.pf6Field,action=focused?.dataset.pf6Action,pick=focused?.dataset.pf6Select,range=focused?.tagName==='INPUT'?[focused.selectionStart,focused.selectionEnd]:null;
    pane.innerHTML=markup(v);const region=pane.querySelector('[data-pf6-workspace]');v.region=region;
    region.addEventListener('input',event=>change(v,event));region.addEventListener('change',event=>change(v,event));
    region.addEventListener('click',event=>{const button=event.target.closest('[data-pf6-action]');if(button&&!button.disabled){event.preventDefault();act(v,button.dataset.pf6Action);}const rect=event.target.closest('[data-pf6-picture]');if(rect){region.querySelector(`[data-pf6-member="${rect.dataset.pf6Picture}"]`)?.focus({preventScroll:false});}});
    region.addEventListener('keydown',event=>{if(event.isComposing||event.keyCode===229)return;if(event.key==='Escape'){event.preventDefault();event.stopPropagation();act(v,'cancel');}if(event.key==='Enter'&&event.target.matches('input,select'))event.preventDefault();if(event.key==='Enter'&&event.target.dataset.pf6Picture){event.preventDefault();region.querySelector(`[data-pf6-member="${event.target.dataset.pf6Picture}"]`)?.focus();}});
    const target=field?region.querySelector(`[data-pf6-field="${field}"]`):action?region.querySelector(`[data-pf6-action="${action}"]`):pick?region.querySelector(`[data-pf6-select="${pick}"]`):null;
    const focus=target&&!target.disabled&&!target.closest('fieldset[disabled]')?target:region.querySelector('#pf6Title');focus?.focus({preventScroll:true});if(range&&range[0]!==null&&focus?.setSelectionRange)try{focus.setSelectionRange(...range);}catch(_){}return true;
  }
  async function change(v,event){
    if(v!==active||v.session.busy||v.session.retired)return;const el=event.target,field=el.dataset.pf6Field,key=el.dataset.pf6Select;
    if(!field&&!key||event.type==='input'&&el.tagName==='SELECT'||event.type==='change'&&el.tagName==='INPUT'&&el.type!=='checkbox')return;
    try{
      if(key){if(event.type!=='change')return;const selected=v.session.selected.filter(k=>k!==key);if(el.checked)selected.push(key);await v.session.select(selected);return;}
      const pending=v.session.edit();if(field==='primaryAlong')v.draft.primaryAlong=el.value;else{const [slot,name]=field.split('.');v.draft[slot][name]=el.value;if(name==='kind')v.draft[slot].value='';}
      await pending;if(active===v)display();
    }catch(error){if(active===v){v.session.reason=error.message;display();}}
  }
  async function back(v){
    if(active!==v)return;active=null;await window.PanelFillWorkspace.resumeBuilder(v.session.boundaryId,v.session.fillId,v.trigger);document.querySelector(`[data-pf-action="suggest-timbers"][data-pf-fill-id="${v.session.fillId}"]`)?.focus({preventScroll:true});ReferenceWorkspace.present?.();
  }
  async function act(v,action){
    if(active!==v)return;const s=v.session;
    try{
      if(action==='close'){if(s.pending){s.reason='請先取消本次建議或確認；結果待查時先核對原回執。';display();return;}await back(v);return;}
      if(action==='cancel'){await s.cancel();if(s.phase==='cancelled')await back(v);return;}
      if(action==='suggest'){if(!['u','v'].includes(v.draft.primaryAlong))throw Error('請明選主支走向。');const roles=v.draft.primaryAlong==='u'?{u:'secondary',v:'primary'}:{u:'primary',v:'secondary'};await s.suggest({fillId:s.fillId,A:sourceValue(v.draft.A,'A'),B:sourceValue(v.draft.B,'B'),roles});}
      if(action==='all')await s.select(s.suggestions.entries.filter(e=>e.selectable&&e.valid).map(e=>e.key));
      if(action==='none')await s.select([]);
      if(action==='preview')await s.preview();
      if(action==='confirm'){
        const r=await s.confirm();if(r?.ok&&s.phase==='committed'){
          const context=ReferenceWorkspace.context(),frame=ReferenceWorkspace.history.frame,session=connection.session,current=()=>active===v&&ReferenceWorkspace.context()===context&&ReferenceWorkspace.history.frame===frame&&connection.session===session;
          await renderObjects({current});if(current())await feAfterChange(current);
        }
      }
      if(active===v)display();ReferenceWorkspace.present?.();
    }catch(error){if(active===v){s.reason=(s.phase==='committed'?'已確認，畫面重讀未完成：':'')+error.message;display();}}
  }
  function open(parent,fillId,trigger){
    if(active)return false;const s=new M.Session({host:ReferenceWorkspace,transport:{post:(path,body,origin)=>panelFillBuilderPost(path,body,origin),command:cmd=>apiRequest(cmd)},boundaryId:parent.boundaryId,fillId,revision:parent.contract.revision,snapshot:parent.snapshot,sources:parent.sources,onChange:display});
    active={session:s,draft:{A:{kind:'',value:''},B:{kind:'',value:''},primaryAlong:''},trigger};display();return true;
  }
  function close(){if(!active)return true;if(active.session.pending){active.session.reason='請先取消或確認角材建議；結果待查時只核對原回執。';display();return false;}active=null;return true;}
  function invalidate(reason){if(active){active.session.invalidate(reason);display();}}
  function retireContext(){if(!active)return;const s=active.session;active=null;s.retire();if(s.pending)retired.add(s);}
  async function settleRecovered(command,result,origin){
    for(const s of [...(active?[active.session]:[]),...retired]){const handled=/^pf6-(suggest|select) /.test(command)?await s.settlePreviewReceipt(command,result,origin):s.settleRecovered(command,result,origin);if(handled){if(!s.pending)retired.delete(s);display();ReferenceWorkspace.present?.();return true;}}return false;
  }
  function isRecoveryCancel(command){return [...(active?[active.session]:[]),...retired].some(s=>s.owner.session===connection.session&&s.cleanupToken!==null&&command==='pf6-cancel '+s.cleanupToken);}
  window.addEventListener('geometry-definition-changed',event=>{if(active?.session.pendingCommand===event.detail?.command)return;invalidate('幾何定義已改變；舊候選不能確認，請取消並重新明選。');});
  window.addEventListener('space-models-changed',()=>{if(active&&!active.session.busy&&!active.session.current()&&active.session.phase!=='committed')invalidate('原專案、面或來源已改變；請取消並重新開啟。');});
  return {open,render,close,invalidate,retireContext,settleRecovered,isRecoveryCancel,activeFor:bid=>active?.session.boundaryId===Number(bid),get pending(){return !!active&&(active.session.pending||active.session.phase==='editing')||[...retired].some(s=>s.pending);},get isOpen(){return !!active;},_test:{sourceValue,dimensionText,markup}};
})();
