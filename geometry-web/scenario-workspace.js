"use strict";
window.ScenarioWorkspace = (() => {
  const P=GeometryProject,W=ReferenceWorkspace,I=ScenarioIntegration,$=id=>document.getElementById(id);
  const dialog=$('scenarioDialog'),editor=$('scenarioEditorDialog');
  let generation=0,working=false,edit=null,comparison=null;
  function state(){const p=W.getEvidenceState(),m=W.getModelOperationState();return {contextToken:p.contextToken,revision:p.revision,
    nativeRevision:p.nativeRevision,session:p.session,frame:m.frame,undo:m.undo,redo:m.redo,blocked:p.blocked};}
  function lease(){const before=state(),id=generation;if(before.blocked)throw new Error('請先完成或取消目前操作。');
    return ()=>{const next=state(),expected={...before};delete next.blocked;delete expected.blocked;
      if(id!==generation||JSON.stringify(next)!==JSON.stringify(expected))throw new Error('專案或歷史已變更，這次方案結果未提交。');};}
  const message=text=>{$('scenarioStatus').textContent=text;};
  function controls(){for(const el of dialog.querySelectorAll('button:not([data-scenario-close]),input,select'))el.disabled=working;
    $('scenarioAdopt').disabled=working||!comparison;}
  async function run(action){if(working)return;working=true;controls();try{await action();}catch(e){message(e.message);}finally{working=false;controls();}}
  function render(){const list=W.readScenarioCatalog().catalog?.scenarios||[];
    for(const id of ['scenarioBase','scenarioBefore','scenarioAfter']){const select=$(id),selected=select.value;select.replaceChildren();
      for(const s of list){const o=document.createElement('option');o.value=s.scenarioId;o.textContent=s.label+' · '+s.scenarioId;select.append(o);}
      if(list.some(s=>s.scenarioId===selected))select.value=selected;}
    $('scenarioCount').textContent=list.length+' / 8 份完整快照';controls();}
  async function archive(guard){const root=W.readScenarioCatalog();return I.read(root.catalog,root.sources,guard);}
  function commit(a,guard){guard();W.commitScenarioCatalog(I.exportCatalog(a),I.exportSources(a),guard);comparison=null;render();}
  function name(){const n=$('scenarioName').value.trim();if(!n)throw new Error('請輸入方案名稱。');return n;}
  async function capture(){const read=await W.readScenarioProject(),guard=lease(),check=()=>{read.assertCurrent();guard();};
    const a=await archive(check);await a.capture(read.project,{scenarioId:crypto.randomUUID(),label:name()});commit(a,check);message('已保存完整專案、原圖、草稿及模型。');}
  async function fork(){const guard=lease(),a=await archive(guard);await a.fork($('scenarioBase').value,{scenarioId:crypto.randomUUID(),label:name()});
    commit(a,guard);message('已建立獨立副本。選取右側方案並隔離試改。');}
  const text=value=>typeof value==='string'?value:JSON.stringify(value,null,2);
  async function compare(){const guard=lease(),a=await archive(guard),list=a.list(),left=$('scenarioBefore').value,right=$('scenarioAfter').value;
    if(left===right)throw new Error('請選取兩份不同方案。');
    const before=list.find(s=>s.scenarioId===left),after=list.find(s=>s.scenarioId===right),diff=ScenarioDiff.compare(before,after);guard();
    const result=$('scenarioDifference');result.replaceChildren();const note=document.createElement('p');
    note.textContent='定義比較；幾何與料長尚未求值。可證明複製關係 '+diff.originPairs.length+' 組；未匹配 '+diff.unmatched.before.length+' / '+diff.unmatched.after.length+' 個物件，實物身分未知。';result.append(note);
    if(!diff.sections.length){const same=document.createElement('p');same.textContent='兩份完整定義相同。';result.append(same);}
    for(const s of diff.sections){const item=document.createElement('details'),title=document.createElement('summary');title.textContent=s.field;
      const columns=document.createElement('div');columns.className='scenario-diff-columns';
      for(const [label,value] of [[before.label,s.before],[after.label,s.after]]){const col=document.createElement('section'),h=document.createElement('h3'),pre=document.createElement('pre');h.textContent=label;pre.textContent=text(value);col.append(h,pre);columns.append(col);}
      item.append(title,columns);result.append(item);}
    comparison={after:right,guard,project:a.project(right)};message('已核對完整定義；整體採用可一步復原。');controls();}
  async function adopt(){if(!comparison)throw new Error('請先比較方案。');const candidate=comparison;candidate.guard();
    if(!confirm('整體採用右側方案？World、原圖、草稿與模型一起替換，可一步復原。'))return;
    candidate.guard();const read=await W.readScenarioProject();candidate.guard();await I.verifyProject(read.project,candidate.guard);
    await W.adoptScenario(structuredClone(candidate.project),candidate.guard);comparison=null;render();message('已整體採用，可復原／重做到完整原方案。');}
  async function editorRequest(data){
    if(data.action==='create')data={...data,requestId:crypto.randomUUID()};
    const body=JSON.stringify(data),send=()=>fetch('/scenarios/editor',{method:'POST',headers:{'Content-Type':'application/json'},body,signal:AbortSignal.timeout(30000)});
    let r;try{r=await send();}catch(error){if(data.action!=='create')throw error;r=await send();}
    const result=await r.json();if(!r.ok||result.ok!==true)throw new Error(result.error||result.message||'方案編輯服務未完成。');return result;}
  function childRequest(type,payload={}){const owner=edit,requestId=crypto.randomUUID();return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>finish(new Error('方案回應逾時；尚未保存試改。')),60000);
    function finish(error,result){clearTimeout(timer);window.removeEventListener('message',listener);error?reject(error):resolve(result);}
    function listener(e){if(e.origin!==location.origin||e.source!==owner.frame.contentWindow||e.data?.requestId!==requestId)return;
      if(edit!==owner)return finish(new Error('方案編輯已取消。'));e.data.ok===true?finish(null,e.data):finish(new Error(e.data.error||'方案編輯未完成。'));}
    window.addEventListener('message',listener);owner.frame.contentWindow.postMessage({type,requestId,...payload},location.origin);
  });}
  async function closeEdit(){const old=edit;edit=null;editor.close();$('scenarioEditorFrame').src='about:blank';if(old)await editorRequest({action:'close',context:old.context});}
  async function startEdit(){const guard=lease(),a=await archive(guard),id=$('scenarioAfter').value,project=a.project(id);
    const bytes=await P.pack(project.scene,project.manifest,project.sources,fflate);guard();const created=await editorRequest({action:'create'});
    try{guard();const frame=$('scenarioEditorFrame');edit={context:created.context,id,guard,frame};
      $('scenarioEditorTitle').textContent='隔離試改：'+a.list().find(s=>s.scenarioId===id).label;
      $('scenarioEditorStatus').textContent='正在還原完整方案…';$('scenarioFinishEdit').disabled=true;editor.showModal();
      await new Promise((resolve,reject)=>{frame.onload=resolve;frame.onerror=()=>reject(new Error('方案畫布無法開啟。'));frame.src='/?scenario='+created.context;});
      guard();await childRequest('scenario-open',{bytes});guard();$('scenarioEditorStatus').textContent='此處變更只在獨立方案內；完成後保存試改，或取消。';$('scenarioFinishEdit').disabled=false;
    }catch(e){const owned=!!edit;await closeEdit();if(!owned)await editorRequest({action:'close',context:created.context});throw e;}}
  async function finishEdit(){const old=edit;if(!old)return;$('scenarioFinishEdit').disabled=true;
    try{old.guard();const result=await childRequest('scenario-export');old.guard();const project=await P.unpack(result.bytes,fflate);old.guard();
      const a=await archive(old.guard);await a.replace(old.id,project);commit(a,old.guard);await closeEdit();message('已保存试改；基準的資料與草稿未變更，請重新比較。');
    }catch(e){$('scenarioEditorStatus').textContent=e.message;}finally{if(edit)$('scenarioFinishEdit').disabled=false;}}
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
