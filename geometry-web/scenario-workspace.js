"use strict";
window.ScenarioWorkspace = (() => {
  const P=GeometryProject,W=ReferenceWorkspace,I=ScenarioIntegration,$=id=>document.getElementById(id);
  const dialog=$('scenarioDialog'),editor=$('scenarioEditorDialog');
  let generation=0,working=false,edit=null,comparison=null,childExport=null;
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
  function childRequest(owner,type,payload={},allowCancelled=false){const requestId=crypto.randomUUID();return new Promise((resolve,reject)=>{
    let settled=false;
    const timer=setTimeout(()=>finish(new Error('方案回應逾時；尚未保存試改。')),60000);
    const cancelled=()=>finish(new Error('方案編輯已取消。'));
    function finish(error,result){if(settled)return;settled=true;clearTimeout(timer);window.removeEventListener('message',listener);owner.guard.signal.removeEventListener('abort',cancelled);error?reject(error):resolve(result);}
    function listener(e){if(e.origin!==location.origin||e.source!==owner.frame.contentWindow||e.data?.requestId!==requestId)return;
      if(edit!==owner)return finish(new Error('方案編輯已取消。'));e.data.ok===true?finish(null,e.data):finish(new Error(e.data.error||'方案編輯未完成。'));}
    if(!allowCancelled){if(owner.guard.signal.aborted)return cancelled();owner.guard.signal.addEventListener('abort',cancelled,{once:true});}
    window.addEventListener('message',listener);owner.frame.contentWindow.postMessage({type,requestId,...payload},location.origin);
  });}
  function sameEditor(a,b){return !!a&&!!b&&['schema','rootSession','scenarioId','label'].every(k=>a[k]===b[k])&&
    ['action','requestId','sequence','session'].every(k=>a.request?.[k]===b.request?.[k])&&(!a.context||a.context===b.context);}
  function editorControls(owner){if(edit!==owner)return;
    $('scenarioFinishEdit').disabled=!owner.ready||owner.recovered||owner.finishing||owner.cancelled||owner.ticket.phase==='retiring';
    if($('scenarioPauseEdit'))$('scenarioPauseEdit').disabled=!owner.ready||owner.recovered||owner.finishing||owner.cancelled||owner.ticket.phase!=='active';
    $('scenarioCancelEdit').disabled=!!owner.critical||!!owner.cancelling;
    $('scenarioCancelEdit').textContent=owner.ticket.phase==='retiring'?'重試結束':'取消試改';}
  function showEditor(ticket,guard,recovered=false){const owner={ticket,id:ticket.scenarioId,guard,frame:$('scenarioEditorFrame'),recovered,ready:false};
    edit=owner;owner.frame.inert=true;$('scenarioEditorTitle').textContent='隔離試改：'+ticket.label;
    editorControls(owner);if(!editor.open)editor.showModal();return owner;}
  function retained(owner,error){if(edit!==owner||owner.cancelling)return;owner.recovered=true;owner.frame.inert=true;editorControls(owner);
    $('scenarioEditorStatus').textContent=(error?error.message+' ':'')+(owner.ticket.phase==='retiring'?
      '已保留原結束請求，尚未確認清理完成；請重試結束。':
      '這次試改已中斷，資料與編輯識別仍保留；無法安全續接，也不會建立另一份。若要捨棄，請明確取消「'+owner.ticket.label+'」。');}
  function writeTicket(owner,change){const pending=W.updateScenarioEditorTicket(owner.ticket,change).then(ticket=>{owner.ticket=ticket;return ticket;});
    owner.ticketWrite=pending;return pending;}
  async function retireEditor(owner){if(owner.retiring)return owner.retiring;const ticket=owner.ticket;
    owner.retiring=(async()=>{
      if(ticket.phase!=='retiring'||await W.verifyScenarioEditorRetirement(ticket)!==true)throw new Error('尚未確認可結束這次試改，資料仍保留。');
      const result=await editorRequest({...ticket.request,action:'close'});
      if(result.state!=='retired')throw new Error('尚未確認方案已結束，原請求仍保留。');
      await W.clearScenarioEditorTicket(ticket);
      if(edit===owner){owner.guard.cancel();edit=null;editor.close();owner.frame.src='about:blank';owner.frame.inert=true;}
    })();try{return await owner.retiring;}finally{owner.retiring=null;}
  }
  async function closeEdit(){const old=edit;if(!old||old.critical)return;if(old.cancelling)return old.cancelling;
    if(old.recovered&&old.ticket.phase!=='retiring'&&!confirm('捨棄「'+old.ticket.label+'」（方案 '+old.id+'，編輯 '+(old.ticket.context||old.ticket.request.requestId)+'）的未保存試改？此方案可能仍在其他分頁開啟；結束後，這次未保存變更將無法復原。'))return;
    // Stop pending create/import/export continuations immediately. The native
    // context is retained until the separate durable discard acknowledgement.
    old.cancelled=true;old.guard.cancel();old.frame.inert=true;
    old.cancelling=(async()=>{try{
      if(old.ticketWrite)await old.ticketWrite.catch(()=>{});
      // A failed-Finish release may already be in flight. It must settle before
      // durable discard intent; retirement must never unfreeze B afterward.
      if(old.releasing)await old.releasing.catch(()=>{});
      const current=await W.readScenarioEditorTicket();if(!sameEditor(old.ticket,current))throw new Error('試改識別已變更，原資料仍保留。');
      old.ticket=current;
      if(current.phase!=='retiring')old.ticket=await W.markScenarioEditorRetiring(current,{reason:'cancel'});
      editorControls(old);await retireEditor(old);
    }catch(e){if(edit===old){old.recovered=true;$('scenarioEditorStatus').textContent=e.message+' 試改與原請求仍保留，尚未確認結束。';}throw e;
    }finally{old.cancelling=null;editorControls(old);}})();editorControls(old);return old.cancelling;
  }
  function loadEditorFrame(owner,context){return new Promise((resolve,reject)=>{let settled=false;
    const cancel=()=>finish(new Error('方案編輯已取消。')),timer=setTimeout(()=>finish(new Error('方案畫布開啟逾時。')),30000);
    function finish(error){if(settled)return;settled=true;clearTimeout(timer);owner.frame.onload=null;owner.frame.onerror=null;owner.guard.signal.removeEventListener('abort',cancel);error?reject(error):resolve();}
    owner.frame.onload=()=>finish();owner.frame.onerror=()=>finish(new Error('方案畫布無法開啟。'));
    if(owner.guard.signal.aborted)return cancel();owner.guard.signal.addEventListener('abort',cancel,{once:true});owner.frame.src='/?scenario='+context;
  });}
  async function startEdit(){if(edit){if(!editor.open)editor.showModal();return;}const guard=lease();
    const pending=await W.readScenarioEditorTicket();guard();
    if(pending){const owner=showEditor(pending,guard,true);retained(owner);
      if(pending.phase==='active'){
        try{const resolved=await editorRequest({...pending.request,action:'resolve',context:pending.context});guard();
          if(resolved.state!=='active'||resolved.context!==pending.context||resolved.requestId!==pending.request.requestId||resolved.sequence!==pending.request.sequence)
            throw new Error('原試改不存在或無法確認；未建立另一份。');
          await loadEditorFrame(owner,pending.context);guard();
          await childRequest(owner,'scenario-resume',{ticket:pending});guard();
          owner.recovered=false;owner.ready=true;owner.frame.inert=false;
          $('scenarioEditorStatus').textContent='';editorControls(owner);return;
        }catch(error){retained(owner,error);return;}
      }
      if(pending.phase!=='retiring')return;
      try{await retireEditor(owner);}catch(e){retained(owner,e);throw e;}
      // A verified retirement may be drained, but its cancelled lease cannot
      // authorize another allocation. A fresh click obtains a fresh A lease.
      message('先前試改已結束；可再次選取隔離試改。');return;}
    const a=await archive(guard),id=$('scenarioAfter').value,project=a.project(id),label=a.list().find(s=>s.scenarioId===id).label;
    const bytes=await P.pack(project.scene,project.manifest,project.sources,fflate);guard();
    const response=await fetch('/scenarios/editor'),status=await response.json();guard();
    if(!response.ok||status.ok!==true||!Number.isSafeInteger(status.sequence)||status.sequence<=0||
      typeof status.session!=='string'||!/^[a-f0-9]{32}$/.test(status.session)||status.session!==state().session)throw new Error(status.error||'方案編輯服務識別不符，未建立試改。');
    const request={action:'create',requestId:crypto.randomUUID(),sequence:status.sequence,session:status.session};
    const ticket=await W.createScenarioEditorTicket({request,scenarioId:id,label},guard);guard();
    const owner=showEditor(ticket,guard);$('scenarioEditorStatus').textContent='正在還原完整方案…';
    try{guard();const created=await editorRequest(ticket.request);guard();
      if(typeof created.context!=='string'||!/^[a-f0-9]{32}$/.test(created.context)||created.context===ticket.rootSession||
        (created.session!==undefined&&created.session!==ticket.rootSession))throw new Error('方案編輯回覆識別不符，原請求仍保留。');
      await writeTicket(owner,{phase:'initializing',context:created.context});guard();
      await loadEditorFrame(owner,created.context);guard();
      await childRequest(owner,'scenario-open',{bytes,name:label+'.gcanvas',ticket:owner.ticket});guard();
      await writeTicket(owner,{phase:'active',context:created.context});guard();
      owner.ready=true;owner.frame.inert=false;$('scenarioEditorStatus').textContent='';editorControls(owner);
    }catch(e){if(!owner.cancelled)retained(owner,e);throw e;}
  }
  async function releaseFreeze(owner){if(owner.cancelling)await owner.cancelling.catch(()=>{});
    if(!owner.freezeId||edit!==owner||owner.ticket.phase==='retiring')return;
    owner.releasing=childRequest(owner,'scenario-release',{freezeId:owner.freezeId,freezeToken:owner.freezeToken},true);
    try{await owner.releasing;owner.freezeId=null;owner.freezeToken=null;
      if(!owner.cancelled&&!owner.recovered)owner.frame.inert=false;
    }finally{owner.releasing=null;}}
  async function finishEdit(){const old=edit;if(!old||!old.ready||old.recovered||old.finishing||old.cancelled||old.ticket.phase!=='active')return;
    old.finishing=true;old.frame.inert=true;editorControls(old);
    try{old.guard();old.freezeId=crypto.randomUUID();
      const result=await childRequest(old,'scenario-export',{freezeId:old.freezeId});old.freezeToken=result.freezeToken;old.guard();
      if(typeof old.freezeToken!=='string'||!old.freezeToken)throw new Error('方案凍結回覆不完整；尚未保存試改。');
      const project=await P.unpack(result.bytes,fflate);old.guard();const a=await archive(old.guard);await a.replace(old.id,project);old.guard();
      await childRequest(old,'scenario-assert-frozen',{freezeId:old.freezeId,freezeToken:old.freezeToken});old.guard();
      // From here Cancel cannot race an unknown A checkpoint outcome. The
      // owner persists complete A plus retirement atomically before local A.
      old.critical=true;editorControls(old);
      const saved=await W.finishScenarioEditor(I.exportCatalog(a),I.exportSources(a),old.ticket,old.guard);
      if(!sameEditor(old.ticket,saved?.ticket)||saved.ticket.phase!=='retiring'||saved.ticket.retirement?.reason!=='finish'||!saved.checkpoint)
        throw new Error('尚未確認試改保存結果，原資料仍保留。');
      old.ticket=saved.ticket;old.critical=false;old.ready=false;editorControls(old);comparison=null;render();
      $('scenarioEditorStatus').textContent='完整試改已保存，正在結束獨立方案…';await retireEditor(old);
      message('已保存試改；基準的資料與草稿未變更，請重新比較。');
    }catch(e){old.critical=false;
      if(old.cancelling)await old.cancelling.catch(()=>{});
      if(edit===old){
        try{const current=await W.readScenarioEditorTicket();if(!sameEditor(old.ticket,current))throw new Error('試改識別無法確認。');old.ticket=current;
          if(current.phase!=='retiring')await releaseFreeze(old);
          else old.recovered=true;
        }catch(_){old.recovered=true;}
        if(old.cancelled)old.recovered=true;
        $('scenarioEditorStatus').textContent=e.message+' 試改與原請求仍保留。';
      }
    }finally{old.critical=false;old.finishing=false;editorControls(old);}
  }
  async function pauseEdit(){const owner=edit;
    if(!owner?.ready||owner.recovered||owner.finishing||owner.cancelled||owner.ticket.phase!=='active')return;
    owner.finishing=true;owner.frame.inert=true;editorControls(owner);
    try{owner.guard();await childRequest(owner,'scenario-pause',{ticket:owner.ticket});owner.guard();
      // Keep native B and the exact ticket. Closing the frame releases its
      // browser leases; no release-freeze or close/create request is sent.
      owner.guard.cancel();edit=null;owner.frame.src='about:blank';editor.close();
      message('已暫存完整試改；再次選「隔離試改」可核對並續接。');
    }catch(error){retained(owner,error);}
    finally{owner.finishing=false;editorControls(owner);}
  }
  window.addEventListener('message',async e=>{if(!window.GeometryNativeContext||e.origin!==location.origin||e.source!==parent||!e.data?.requestId)return;
    const {type,requestId}=e.data;if(!['scenario-open','scenario-resume','scenario-pause','scenario-export','scenario-assert-frozen','scenario-release'].includes(type))return;
    try{if(type==='scenario-open'||type==='scenario-resume'){const start=Date.now();while(connection.phase!=='ready'){if(Date.now()-start>30000)throw new Error('方案服務尚未連線。');await new Promise(r=>setTimeout(r,50));}
        if(type==='scenario-open')await W.initializeScenarioProject(e.data.bytes,e.data.name,e.data.ticket);
        else await W.resumeScenarioProject(e.data.ticket);
        parent.postMessage({requestId,ok:true},location.origin);
      }else if(type==='scenario-pause'){
        if(connection.phase!=='ready'||pendingApiResults.size)throw new Error('操作結果尚未確認，不能暫存續接點。');
        document.body.inert=true;const paused=await W.pauseScenarioProject(e.data.ticket);parent.postMessage({requestId,ok:true,...paused},location.origin);
      }else if(type==='scenario-export'){
        if(childExport||typeof e.data.freezeId!=='string'||!e.data.freezeId)throw new Error('上一筆方案保存尚未結束。');
        const owner={id:e.data.freezeId};childExport=owner;owner.pending=Promise.resolve().then(()=>W.freezeScenarioProject());
        let frozen;try{frozen=await owner.pending;}catch(error){if(childExport===owner)childExport=null;throw error;}
        owner.token=frozen.freezeToken;parent.postMessage({requestId,ok:true,...frozen},location.origin);
      }else{
        const owner=childExport;
        if(!owner){if(type!=='scenario-release')throw new Error('方案凍結已失效。');}
        else{if(owner.id!==e.data.freezeId)throw new Error('方案凍結識別不符。');
          const frozen=await owner.pending;if(e.data.freezeToken!==undefined&&e.data.freezeToken!==null&&frozen.freezeToken!==e.data.freezeToken)throw new Error('方案凍結識別不符。');
          if(type==='scenario-assert-frozen'){if(frozen.freezeToken!==e.data.freezeToken)throw new Error('方案凍結識別不符。');await W.assertScenarioFrozen(frozen.freezeToken);}
          else{await W.releaseScenarioProject(frozen.freezeToken);if(childExport===owner)childExport=null;}}
        parent.postMessage({requestId,ok:true},location.origin);
      }
    }catch(error){parent.postMessage({requestId,ok:false,error:error.message},location.origin);}});
  $('scenarioOpen').onclick=()=>{if(edit){if(!editor.open)editor.showModal();return;}comparison=null;generation++;render();dialog.showModal();};
  $('scenarioCapture').onclick=()=>run(capture);$('scenarioFork').onclick=()=>run(fork);$('scenarioCompare').onclick=()=>run(compare);
  $('scenarioAdopt').onclick=()=>run(adopt);$('scenarioEdit').onclick=()=>run(startEdit);
  for(const select of [$('scenarioBefore'),$('scenarioAfter')])select.onchange=()=>{comparison=null;controls();};
  function close(){if(edit)return;generation++;comparison=null;dialog.close();}
  dialog.addEventListener('cancel',e=>{e.preventDefault();close();});dialog.querySelector('[data-scenario-close]').onclick=close;
  editor.addEventListener('cancel',e=>{e.preventDefault();closeEdit().catch(e=>message(e.message));});
  $('scenarioCancelEdit').onclick=()=>closeEdit().catch(e=>message(e.message));$('scenarioFinishEdit').onclick=finishEdit;
  if($('scenarioPauseEdit'))$('scenarioPauseEdit').onclick=pauseEdit;
  if(window.GeometryNativeContext)$('scenarioOpen').hidden=true;
  return {open:()=>{$('scenarioOpen').click();}};
})();
