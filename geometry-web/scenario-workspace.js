"use strict";
window.ScenarioWorkspace = (() => {
  const P=GeometryProject,W=ReferenceWorkspace,I=ScenarioIntegration,$=id=>document.getElementById(id);
  const dialog=$('scenarioDialog'),editor=$('scenarioEditorDialog');
  let generation=0,working=false,edit=null,comparison=null;const retiring=new Map();
  function state(){const p=W.getEvidenceState(),m=W.getModelOperationState();return {contextToken:p.contextToken,revision:p.revision,
    nativeRevision:p.nativeRevision,session:p.session,frame:m.frame,undo:m.undo,redo:m.redo,blocked:p.blocked};}
  function lease(){let before=state();const cancel=new AbortController(),id=generation;if(before.blocked)throw new Error('請先完成或取消目前操作。');
    const owned=()=>{if(cancel.signal.aborted||id!==generation)throw new Error('方案操作已取消，這次結果未提交。');};
    const guard=()=>{owned();const next=state(),expected={...before};delete next.blocked;delete expected.blocked;
      if(JSON.stringify(next)!==JSON.stringify(expected))throw new Error('專案或歷史已變更，這次方案結果未提交。');};
    // Only the synchronous, owned draft flush may renew the data stamp. No
    // asynchronous result can acquire a new operation or reopen a cancelled one.
    guard.afterFlush=()=>{owned();before=state();};guard.cancel=()=>cancel.abort();guard.signal=cancel.signal;return guard;}
  const message=text=>{$('scenarioStatus').textContent=text;};
  function controls(){for(const el of dialog.querySelectorAll('button:not([data-scenario-close]),input,select'))el.disabled=working;
    $('scenarioAdopt').disabled=working||!comparison;}
  async function run(action){if(working)return;working=true;controls();try{await action();}catch(e){message(e.message);}finally{working=false;controls();}}
  function render(){const list=W.readScenarioCatalog().catalog?.scenarios||[];
    for(const id of ['scenarioBase','scenarioBefore','scenarioAfter']){const select=$(id),selected=select.value;select.replaceChildren();
      for(const [index,s] of list.entries()){const o=document.createElement('option');o.value=s.scenarioId;o.textContent=s.label+' · 第 '+(index+1)+' 份';select.append(o);}
      if(list.some(s=>s.scenarioId===selected))select.value=selected;}
    $('scenarioCount').textContent=list.length+' / 8 份完整快照';controls();}
  async function archive(guard){const root=W.readScenarioCatalog();return I.read(root.catalog,root.sources,guard);}
  function commit(a,guard){guard();W.commitScenarioCatalog(I.exportCatalog(a),I.exportSources(a),guard);comparison=null;render();}
  function name(){const n=$('scenarioName').value.trim();if(!n)throw new Error('請輸入方案名稱。');return n;}
  async function capture(){const guard=lease(),read=await W.readScenarioProject(guard,guard.afterFlush),check=()=>{read.assertCurrent();guard();};
    const a=await archive(check);await a.capture(read.project,{scenarioId:crypto.randomUUID(),label:name()});commit(a,check);message('已保存完整專案、原圖、草稿及模型。');}
  async function fork(){const guard=lease(),a=await archive(guard);await a.fork($('scenarioBase').value,{scenarioId:crypto.randomUUID(),label:name()});
    commit(a,guard);message('已建立獨立副本。選取右側方案並隔離試改。');}
  const text=value=>typeof value==='string'?value:JSON.stringify(value,null,2);
  // These are canonical final declarations from the disposable native verifier.
  // Each column uses its own catalog; this display neither pairs objects across
  // scenarios nor evaluates expressions or resolves them against the live A.
  function parameterDefinitions(scene){
    const cards=new Map(),fields=[];
    for(const line of scene.split('\n')){
      const match=line.match(/^parameters (card|field) ([A-Za-z0-9+/]+={0,2})$/);if(!match)continue;
      const value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Uint8Array.from(atob(match[2]),c=>c.charCodeAt(0))));
      if(match[1]==='card')cards.set(value.id,{...value,fields:[]});else fields.push(value);
    }
    for(const field of fields)cards.get(field.parameterId)?.fields.push(field);
    const list=document.createElement('div'),catalog=[...cards.values()];list.className='scenario-parameter-definitions';
    if(!cards.size){const empty=document.createElement('p');empty.textContent='這份方案沒有參數定義。';list.append(empty);return list;}
    for(const card of catalog){const heading=document.createElement('h4'),values=document.createElement('dl');heading.textContent=card.name;
      for(const field of card.fields){const label=document.createElement('dt'),definition=document.createElement('dd');label.textContent=field.name;definition.textContent=ParameterUI.formatDefinition(field.expression,catalog);values.append(label,definition);}
      list.append(heading,values);
    }return list;
  }
  const sectionLabels={worldScene:'模型與參數定義',assets:'原圖與來源檔案',requiredCapabilities:'所需功能',
    'projectManifest.sceneHash':'資料校驗','projectManifest.sources':'原圖資料','projectManifest.faces':'圖頁與對位',
    'projectManifest.models':'空間模型','projectManifest.faceProjections':'面投影','projectManifest.name':'專案名稱',
    'projectManifest.engineeringDrafts':'工程草稿','projectManifest.assemblyDrafts':'組構草稿','projectManifest.featureAttachments':'工程附件與證據'};

  async function compare(){const guard=lease(),a=await archive(guard),list=a.list(),left=$('scenarioBefore').value,right=$('scenarioAfter').value;
    if(left===right)throw new Error('請選取兩份不同方案。');
    const before=list.find(s=>s.scenarioId===left),after=list.find(s=>s.scenarioId===right),diff=ScenarioDiff.compare(before,after);guard();
    const result=$('scenarioDifference');result.replaceChildren();const note=document.createElement('p');
    note.textContent='定義比較；幾何與料長尚未求值。可證明複製關係 '+diff.originPairs.length+' 組；未匹配 '+diff.unmatched.before.length+' / '+diff.unmatched.after.length+' 個物件，實物身分未知。';result.append(note);
    if(!diff.sections.length){const same=document.createElement('p');same.textContent='兩份完整定義相同。';result.append(same);}
    for(const s of diff.sections){const item=document.createElement('details'),title=document.createElement('summary');title.textContent=sectionLabels[s.field]||s.field;
      const columns=document.createElement('div');columns.className='scenario-diff-columns';
      for(const [scenario,value] of [[before,s.before],[after,s.after]]){const col=document.createElement('section'),h=document.createElement('h3'),pre=document.createElement('pre');h.textContent=scenario.label;pre.textContent=text(value);col.append(h);
        if(s.field==='worldScene'){const finalScene=I.finalScene(a,scenario.scenarioId),storage=document.createElement('details'),summary=document.createElement('summary');
          summary.textContent='完整原生最終定義';pre.textContent=finalScene;storage.append(summary,pre);col.append(parameterDefinitions(finalScene),storage);item.open=true;
          if(value!==finalScene){const original=document.createElement('details'),heading=document.createElement('summary'),raw=document.createElement('pre');heading.textContent='原始儲存內容';raw.textContent=text(value);original.append(heading,raw);col.append(original);}}
        else col.append(pre);columns.append(col);}
      item.append(title,columns);result.append(item);}
    comparison={after:right,guard,project:a.project(right)};message('已核對完整定義；整體採用可一步復原。');controls();}
  async function adopt(){if(!comparison)throw new Error('請先比較方案。');const candidate=comparison;candidate.guard();
    if(!confirm('整體採用右側方案？World、原圖、草稿與模型一起替換，可一步復原。'))return;
    candidate.guard();const read=await W.readScenarioProject(candidate.guard);candidate.guard();await I.verifyProject(read.project,candidate.guard);
    await W.adoptScenario(structuredClone(candidate.project),candidate.guard);comparison=null;render();message('已整體採用，可復原／重做到完整原方案。');}
  async function editorRequest(data){
    const body=JSON.stringify(data),send=()=>fetch('/scenarios/editor',{method:'POST',headers:{'Content-Type':'application/json'},body,signal:AbortSignal.timeout(30000)});
    let r;try{r=await send();}catch(error){r=await send();}
    const result=await r.json();if(!r.ok||result.ok!==true)throw new Error(result.error||result.message||'方案編輯服務未完成。');return result;}
  function childRequest(type,payload={}){const owner=edit,requestId=crypto.randomUUID();return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>finish(new Error('方案回應逾時；尚未保存試改。')),60000);
    const cancelled=()=>finish(new Error('方案編輯已取消。'));
    function finish(error,result){clearTimeout(timer);window.removeEventListener('message',listener);owner.guard.signal.removeEventListener('abort',cancelled);error?reject(error):resolve(result);}
    function listener(e){if(e.origin!==location.origin||e.source!==owner.frame.contentWindow||e.data?.requestId!==requestId)return;
      if(edit!==owner)return finish(new Error('方案編輯已取消。'));e.data.ok===true?finish(null,e.data):finish(new Error(e.data.error||'方案編輯未完成。'));}
    if(owner.guard.signal.aborted)return cancelled();owner.guard.signal.addEventListener('abort',cancelled,{once:true});
    window.addEventListener('message',listener);owner.frame.contentWindow.postMessage({type,requestId,...payload},location.origin);
  });}
  async function retireEditors(){for(const [id,owner] of retiring){await editorRequest({...owner.request,action:'close'});retiring.delete(id);}}
  async function closeEdit(){const old=edit;if(old){old.guard.cancel();retiring.set(old.request.requestId,old);}edit=null;editor.close();$('scenarioEditorFrame').src='about:blank';await retireEditors();}
  async function startEdit(){const guard=lease(),a=await archive(guard),id=$('scenarioAfter').value,project=a.project(id);
    const bytes=await P.pack(project.scene,project.manifest,project.sources,fflate);guard();await retireEditors();guard();
    const status=await fetch('/scenarios/editor').then(r=>r.json());guard();if(status.ok!==true)throw new Error(status.error||'方案編輯服務未完成。');
    const request={action:'create',requestId:crypto.randomUUID(),sequence:status.sequence,session:status.session},frame=$('scenarioEditorFrame'),owner={request,id,guard,frame};edit=owner;
    try{guard();
      $('scenarioEditorTitle').textContent='隔離試改：'+a.list().find(s=>s.scenarioId===id).label;
      $('scenarioEditorStatus').textContent='正在還原完整方案…';$('scenarioFinishEdit').disabled=true;editor.showModal();
      const created=await editorRequest(request);guard();owner.context=created.context;
      await new Promise((resolve,reject)=>{frame.onload=resolve;frame.onerror=()=>reject(new Error('方案畫布無法開啟。'));frame.src='/?scenario='+created.context;});
      guard();await childRequest('scenario-open',{bytes});guard();$('scenarioEditorStatus').textContent='此處變更只在獨立方案內；完成後保存試改，或取消。';$('scenarioFinishEdit').disabled=false;
    }catch(e){guard.cancel();if(edit===owner)await closeEdit();else{retiring.set(request.requestId,owner);await retireEditors();}throw e;}}
  async function finishEdit(){const old=edit;if(!old)return;$('scenarioFinishEdit').disabled=true;
    try{old.guard();const result=await childRequest('scenario-export');old.guard();const project=await P.unpack(result.bytes,fflate);old.guard();
      const a=await archive(old.guard);await a.replace(old.id,project);commit(a,old.guard);await closeEdit();message('已保存试改；基準的資料與草稿未變更，請重新比較。');
    }catch(e){if(edit===old)$('scenarioEditorStatus').textContent=e.message;else message(e.message);}finally{if(edit===old)$('scenarioFinishEdit').disabled=false;}}
  window.addEventListener('message',async e=>{if(!window.GeometryNativeContext||e.origin!==location.origin||e.source!==parent||!e.data?.requestId)return;
    const {type,requestId}=e.data;if(!['scenario-open','scenario-export'].includes(type))return;
    try{if(type==='scenario-open'){const start=Date.now();while(connection.phase!=='ready'){if(Date.now()-start>30000)throw new Error('方案服務尚未連線。');await new Promise(r=>setTimeout(r,50));}
        await W.importBytes(e.data.bytes,'候選方案.gcanvas');parent.postMessage({requestId,ok:true},location.origin);
      }else{const bytes=await W.exportBytes();parent.postMessage({requestId,ok:true,bytes},location.origin);}
    }catch(error){parent.postMessage({requestId,ok:false,error:error.message},location.origin);}});
  $('scenarioOpen').onclick=()=>{comparison=null;generation++;render();dialog.showModal();};
  $('scenarioCapture').onclick=()=>run(capture);$('scenarioFork').onclick=()=>run(fork);$('scenarioCompare').onclick=()=>run(compare);
  $('scenarioAdopt').onclick=()=>run(adopt);$('scenarioEdit').onclick=()=>run(startEdit);
  for(const select of [$('scenarioBefore'),$('scenarioAfter')])select.onchange=()=>{comparison=null;controls();};
  function close(){generation++;comparison=null;dialog.close();}
  dialog.addEventListener('cancel',e=>{e.preventDefault();close();});dialog.querySelector('[data-scenario-close]').onclick=close;
  editor.addEventListener('cancel',e=>{e.preventDefault();closeEdit().catch(e=>message(e.message));});
  $('scenarioCancelEdit').onclick=()=>closeEdit().catch(e=>message(e.message));$('scenarioFinishEdit').onclick=finishEdit;
  if(window.GeometryNativeContext)$('scenarioOpen').hidden=true;
  return {open:()=>{$('scenarioOpen').click();}};
})();
