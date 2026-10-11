(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./cutting-settings.js'):root.CuttingSettings,
 typeof module==='object'&&module.exports?require('./cutting-plan.js'):root.CuttingPlan);if(typeof module==='object'&&module.exports)module.exports=api;else root.CuttingWorkspace=api;})(typeof globalThis!=='undefined'?globalThis:this,(Settings,Plan)=>{
 'use strict';const copy=v=>JSON.parse(JSON.stringify(v));
 function createSession(host){
  let identity=host.state().context??host.state().contextToken,scopes=[],plan=null,receipt=null,generation=0,exporting=false;
  function current(){const state=host.state(),context=state.context??state.contextToken;if(context!==identity){identity=context;scopes=[];plan=receipt=null;generation++;}return state;}
  const scopeKey=()=>JSON.stringify(scopes);
  function capture(){const state=current();return {contextToken:state.contextToken,revision:state.revision,scopes:scopeKey(),settings:Settings.canonical(host.settings()||Settings.empty()),generation};}
  function guard(before){if(JSON.stringify(capture())!==JSON.stringify(before))throw Error('裁切來源、設定或範圍已變更，請重新求方案。');}
  const session={host,get scopes(){current();return copy(scopes);},get plan(){current();return plan;},
   invalidate(){plan=receipt=null;generation++;},
   addScope(scope){current();scopes.push(copy(scope));this.invalidate();},removeScope(index){current();scopes.splice(index,1);this.invalidate();},
   async calculate(){const before=capture(),request={world:{kind:'live'},scopes:copy(scopes)},settings=copy(host.settings()||Settings.empty());
    const references=await host.references();guard(before);const candidate=await Plan.evaluate(references,settings,request);guard(before);plan=candidate;receipt=before;return candidate;},
   async exportCSV(){if(exporting)return false;exporting=true;try{
    current();if(!plan||plan.status!=='COMPLETE'||!receipt)throw Error('請先重新求出 COMPLETE 方案，再匯出。');guard(receipt);
    const candidate=plan,before=receipt,latest=await host.references();guard(before);
    if(!latest?.ok||latest.sourceFingerprint!==candidate.worldFingerprint)throw Error('計量世界已變更，請重新求方案。');
    if(await Settings.fingerprint(host.settings()||Settings.empty())!==candidate.settingsFingerprint)throw Error('裁切設定已變更，請重新求方案。');guard(before);
    host.download(Plan.csv(candidate));return true;
   }finally{exporting=false;}}
  };return session;
 }
 let activeSession=null,activeDialog=null;
 function open({workspace,references,scope,locate}){
  activeDialog?.remove();
  const host={state:()=>({...workspace.getProjectState(),context:workspace.context()}),settings:()=>workspace.readFeatureAttachment(Settings.KIND),references,
   download:csv=>{const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='cutting-plan.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}};
  if(!activeSession)activeSession=createSession(host);else Object.assign(activeSession.host,host);
  const session=activeSession;session.addScope(scope);const contextToken=workspace.getProjectState().contextToken;
  let draft=copy(host.settings()||Settings.empty()),baseSettings=Settings.canonical(draft),edited=false,calculating=false;
  const dialog=document.createElement('dialog');dialog.id='cuttingDialog';dialog.className='cutting-dialog';activeDialog=dialog;
  dialog.innerHTML='<form method="dialog" class="cutting-heading"><h2>裁切與採購</h2><button class="btn" aria-label="關閉裁切與採購">關閉</button></form><div class="cutting-body"><p class="fi-note">尺寸一律宣告為整數 mm。未填的鋸縫、加工餘量與留用下限保持未設定；剩料須由使用者另行宣告。</p><section><h3>裁切設定</h3><div id="cuttingGlobals" class="cutting-fields"></div><h4>原材種類</h4><div id="cuttingStocks"></div><button type="button" id="cuttingAddStock" class="btn">新增原材種類</button><h4>宣告餘料</h4><div id="cuttingRemnants"></div><button type="button" id="cuttingAddRemnant" class="btn">新增宣告餘料</button><button type="button" id="cuttingSave" class="btn">保存設定</button></section><section><h3>本次需求範圍</h3><ol id="cuttingScopes"></ol></section><div class="cutting-actions"><button type="button" id="cuttingCalculate" class="btn">求本次方案</button><button type="button" id="cuttingExport" class="btn" disabled>匯出精確 mm CSV</button><label>顯示單位<select id="cuttingUnit"><option>mm</option><option>cm</option></select></label><label>件的排序<select id="cuttingOrder"><option value="id">構件身分</option><option value="length">完成長度</option></select></label></div><p id="cuttingStatus" role="status"></p><div id="cuttingPlan"></div></div>';
  const $=id=>dialog.querySelector('#'+id),message=text=>{$('cuttingStatus').textContent=text;};
  function changed(){edited=true;session.invalidate();$('cuttingExport').disabled=true;message('設定尚未保存。');}
  function input(parent,label,value,onchange,type='text'){
   const l=document.createElement('label'),i=document.createElement('input');l.append(document.createTextNode(label),i);i.type=type;i.value=Number.isNaN(value)?'':value??'';i.setAttribute('aria-label',label);i.oninput=()=>{onchange(i.value);changed();};parent.append(l);return i;
  }
  const number=text=>text===''?NaN:/^\d+$/.test(text)?Number(text):NaN;
  function renderSettings(){
   $('cuttingGlobals').replaceChildren();for(const [field,label]of [['kerf','鋸縫 mm'],['allowance','加工餘量 mm'],['minRemnant','留用下限 mm']]){const i=input($('cuttingGlobals'),label,draft[field],v=>draft[field]=v===''?null:number(v));i.dataset.setting=field;}
   $('cuttingStocks').replaceChildren();for(const s of draft.stockTypes){const row=document.createElement('fieldset');row.dataset.stockKey=s.key;const title=document.createElement('legend');title.textContent='原材 '+s.key;row.append(title);
    input(row,'名稱',s.name,v=>s.name=v);for(const [field,label]of [['A','截面 A mm'],['B','截面 B mm']])input(row,label,s.section[field==='A'?0:1],v=>s.section[field==='A'?0:1]=number(v));
    input(row,'新料長度 mm',s.length,v=>s.length=number(v));input(row,'原廠端修整 mm',s.endTrim,v=>s.endTrim=number(v));
    const l=document.createElement('label'),select=document.createElement('select');l.append('材料鍵',select);select.setAttribute('aria-label','材料鍵');select.innerHTML='<option value="">請宣告</option><option value="unset">材料未設定</option><option value="fixed">固定材料版本</option>';select.value=s.material===null?'unset':s.material?'fixed':'';row.append(l);
    const m=document.createElement('div');m.className='cutting-fields';m.hidden=select.value!=='fixed';row.append(m);
    const renderMaterial=()=>{m.replaceChildren();if(s.material)for(const [field,label]of [['id','材料 id'],['version','材料版本'],['fingerprint','材料內容指紋']])input(m,label,s.material[field],v=>s.material[field]=field==='version'?number(v):v);};renderMaterial();
    select.onchange=()=>{s.material=select.value==='unset'?null:select.value==='fixed'?{id:'',version:NaN,fingerprint:''}:undefined;m.hidden=select.value!=='fixed';renderMaterial();changed();};
    const remove=document.createElement('button');remove.type='button';remove.className='btn';remove.textContent='移除原材 '+s.key;remove.onclick=()=>{draft.stockTypes=draft.stockTypes.filter(x=>x!==s);changed();renderSettings();};row.append(remove);$('cuttingStocks').append(row);
   }
   $('cuttingRemnants').replaceChildren();for(const r of draft.remnants){const row=document.createElement('fieldset');row.dataset.remnantKey=r.key;const title=document.createElement('legend');title.textContent='宣告餘料 R'+r.key;row.append(title);
    const l=document.createElement('label'),select=document.createElement('select');l.append('所屬原材種類',select);select.innerHTML='<option value="">請選擇</option>';for(const s of draft.stockTypes){const o=document.createElement('option');o.value=s.key;o.textContent=`${s.key}：${s.name}`;select.append(o);}select.value=r.stockType??'';select.setAttribute('aria-label','所屬原材種類');select.onchange=()=>{r.stockType=number(select.value);changed();};row.append(l);
    for(const [field,label]of [['length','餘料實長 mm'],['headTrim','起端修整 mm'],['tailTrim','末端修整 mm']])input(row,label,r[field],v=>r[field]=number(v));
    const remove=document.createElement('button');remove.type='button';remove.className='btn';remove.textContent='移除餘料 R'+r.key;remove.onclick=()=>{draft.remnants=draft.remnants.filter(x=>x!==r);changed();renderSettings();};row.append(remove);$('cuttingRemnants').append(row);
   }
  }
  function renderScopes(){$('cuttingScopes').replaceChildren();session.scopes.forEach((s,i)=>{const li=document.createElement('li'),remove=document.createElement('button');li.append(`承載面 ${s.surface}：${s.ids===null?'全部角材':'構件 '+s.ids.join('、')}`);remove.type='button';remove.className='btn';remove.textContent='移除此範圍';remove.onclick=()=>{session.removeScope(i);renderScopes();renderPlan();};li.append(remove);$('cuttingScopes').append(li);});}
  const diagnosticNames={WORLD_KIND:'此世界種類不支援裁切',CAPACITY:'超過執行器容量',WORLD_UNREADABLE:'無法核對世界',SCOPE_STALE:'需求範圍已失效',SCOPE_EMPTY:'需求範圍沒有角材',NATIVE_CAPABILITY:'原生來源未提供材料末端',MATERIAL_UNRESOLVED:'材料末端未就緒',MATERIAL_MIXED:'兩軸的材料末端不一致',NO_STOCK:'缺少符合的原材種類',MATERIAL_FINGERPRINT_MISMATCH:'材料內容指紋不符',STOCK_SECTION_MISMATCH:'原材截面不符',OVER_LENGTH:'需求件超過全部可用料長',MISSING_SETTING:'裁切設定尚未完整',REMNANT_EXHAUSTED:'本次找到的方案無法排入'};
  function renderPlan(){const p=session.plan,area=$('cuttingPlan');area.replaceChildren();$('cuttingExport').disabled=edited||p?.status!=='COMPLETE';if(!p)return;
   message(`${p.status} · ${p.label}`);for(const d of p.diagnostics){const text=document.createElement('p');text.textContent=`${diagnosticNames[d.code]||'角材料單尚未就緒'}${d.detail?.timberId!==undefined?'：構件 '+d.detail.timberId:''}${d.code==='MISSING_SETTING'?'（'+d.detail.join('、')+'）':''}`;area.append(text);}
   const unit=$('cuttingUnit').value,dimension=n=>unit==='cm'?String(n/10):String(n);
   for(const g of p.groups){const section=document.createElement('section'),h=document.createElement('h3');h.textContent=`${g.stockType.name} · 新料需購入 ${g.newStockCount} 支`;section.append(h);
    for(const s of g.stocks){const title=document.createElement('h4');title.textContent=`${s.label} · 實長 ${dimension(s.length)} ${unit} · 下刀 ${s.cuts} 次`;section.append(title);
     const table=document.createElement('table'),head=document.createElement('tr');for(const label of ['構件','承載面','完成長度 '+unit,'加工長度 '+unit,'在料上的區間 '+unit]){const th=document.createElement('th');th.textContent=label;head.append(th);}table.append(head);
     const pieces=[...s.pieces].sort($('cuttingOrder').value==='length'?(a,b)=>a.L-b.L||a.timberId-b.timberId:(a,b)=>a.timberId-b.timberId);
     for(const piece of pieces){const tr=document.createElement('tr');tr.dataset.cuttingTimber=piece.timberId;for(const value of [piece.timberId,piece.surface,dimension(piece.L),dimension(piece.C),`${dimension(piece.start)}–${dimension(piece.end)}`]){const td=document.createElement('td');td.textContent=value;tr.append(td);}if(locate)tr.onclick=()=>{dialog.close();locate(piece);};table.append(tr);}section.append(table);
     const end=document.createElement('p');end.textContent=`末端：${{trim:'修整',none:'原端面',separate:'末刀分離'}[s.tail.kind]}，耗損 ${dimension(s.tail.consumed)} ${unit}；${s.leftover?`剩料 ${dimension(s.leftover.length)} ${unit}，可用 ${dimension(s.leftover.usable)} ${unit}（${s.leftover.class==='reusable'?'可留用':'廢料'}）`:'無剩料'}`;section.append(end);
    }const unused=document.createElement('p');unused.textContent='未使用宣告餘料：'+(g.unusedRemnants.map(k=>'R'+k).join('、')||'無');section.append(unused);area.append(section);
   }
  }
  function addDraft(list,counter,row){if(draft[counter]===0)throw Error('key 已耗盡。');draft[list].push({key:draft[counter],...row});draft[counter]=draft[counter]===4294967295?0:draft[counter]+1;changed();renderSettings();}
  $('cuttingAddStock').onclick=()=>{try{addDraft('stockTypes','nextStockKey',{name:'',section:['',''],material:undefined,length:'',endTrim:''});}catch(e){message(e.message);}};
  $('cuttingAddRemnant').onclick=()=>{try{addDraft('remnants','nextRemnantKey',{stockType:'',length:'',headTrim:'',tailTrim:''});}catch(e){message(e.message);}};
  $('cuttingSave').onclick=()=>{try{if(Settings.canonical(host.settings()||Settings.empty())!==baseSettings)throw Error('裁切設定已變更，請關閉後重新開啟核對。');Settings.validate(draft);workspace.setFeatureAttachment(Settings.KIND,draft,contextToken);draft=copy(host.settings());baseSettings=Settings.canonical(draft);edited=false;session.invalidate();renderSettings();renderPlan();message('裁切設定已保存。');}catch(e){message(e.message);}};
  $('cuttingCalculate').onclick=async()=>{if(calculating)return;calculating=true;try{if(edited)throw Error('請先保存設定，再求方案。');await session.calculate();renderPlan();}catch(e){message(e.message);}finally{calculating=false;}};
  $('cuttingExport').onclick=async()=>{try{await session.exportCSV();}catch(e){message(e.message);$('cuttingExport').disabled=true;}};
  $('cuttingUnit').onchange=$('cuttingOrder').onchange=renderPlan;
  dialog.addEventListener('close',()=>{session.invalidate();dialog.remove();if(activeDialog===dialog)activeDialog=null;});document.body.append(dialog);renderSettings();renderScopes();renderPlan();dialog.showModal();return session;
 }
 return {createSession,open};
});
