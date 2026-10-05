/* Formal host: original workspace stamp, detached admission, one metadata commit. */
"use strict";
window.RuleCaseHost = (()=>{
  const W=ReferenceWorkspace,P=GeometryProject,C=P.Features.Cases;
  let active=null;const retiring=new Set();
  const stamp=()=>({evidence:W.getEvidenceState(),frame:W.getModelOperationState().frame,runtime:pageRuntimeVersion});
  const same=(a,b)=>a.frame===b.frame&&a.runtime===b.runtime&&JSON.stringify(a.evidence)===JSON.stringify(b.evidence);
  async function request(path,data){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Geometry-Version':pageRuntimeVersion},body:JSON.stringify(data),signal:AbortSignal.timeout(30000)});
    // An expired selected B returns 410; it never supplies a root scope.
    if(response.status!==410)checkApiSession(response);const result=await response.json();
    if(!response.ok||result.ok!==true)throw Object.assign(new Error(result.error||'規則案例請求未完成。'),{code:result.code,status:response.status});return result;}
  function cleanup(owner){if(!owner.request)return Promise.resolve();retiring.add(owner);
    if(owner.cleanup)return owner.cleanup;
    owner.cleanup=(async()=>{for(let attempt=0;attempt<2;attempt++)try{
      const result=await request('/rule-cases/binding',{...owner.request,action:'cancel'});retiring.delete(owner);return result;
    }catch(error){
      // High-water RETIRED or a closed selected native context is terminal.
      // Other errors leave a bounded retryable retirement, blocking new binds.
      if(error.status===410||error.status===409&&error.code==='RETIRED'){retiring.delete(owner);return {ok:true,state:'retired'};}
      if(attempt===1)throw error;
    }})().finally(()=>{owner.cleanup=null;});return owner.cleanup;}
  function retire(owner,message='專案或操作已變更，請重新開啟案例。'){
    if(!owner||owner.retired)return;owner.retired=true;clearInterval(owner.timer);
    for(const listener of [...owner.listeners])listener();owner.listeners.clear();owner.pending?.teardown();owner.controller?.teardown();
    for(const type of owner.events)window.removeEventListener(type,owner.observe);
    cleanup(owner).catch(()=>{});if(active===owner){active=null;owner.element.replaceChildren();const p=document.createElement('p');p.setAttribute('role','status');p.textContent=message;owner.element.append(p);}
  }
  function close(){const owner=active;retire(owner,'案例已關閉。');if(owner)owner.element.hidden=true;}
  async function open(element,completion=''){
    close();const original=stamp();if(original.evidence.blocked||original.evidence.nativeRevision===null)throw new Error('請先完成目前操作，再開啟規則案例。');
    const owner={original,element,retired:false,listeners:new Set(),events:['project-info-changed','geometry-definition-changed','pagehide']};active=owner;element.hidden=false;
    const guard=()=>{if(owner.retired||active!==owner||!same(original,stamp())||stamp().evidence.blocked)throw new Error('原始專案或案例操作已退休，未提交晚到結果。');};
    owner.observe=()=>{if(!same(original,stamp())||stamp().evidence.blocked)retire(owner);};
    // Capture and subscribe before the first await, including cold binding creation.
    for(const type of owner.events)window.addEventListener(type,owner.observe);owner.timer=setInterval(owner.observe,50);
    try{
      await Promise.all([...retiring].map(cleanup));guard();
      const response=await fetch('/rule-cases/binding',{headers:{'X-Geometry-Version':pageRuntimeVersion},signal:AbortSignal.timeout(30000)});checkApiSession(response);
      const status=await response.json();
      if(!response.ok||status.ok!==true||status.session!==original.evidence.session||status.runtime!==original.runtime)throw new Error('所選案例服務已變更。');
      owner.context={projectId:original.evidence.projectScope,generation:status.sequence,contextToken:original.evidence.contextToken};
      owner.request={protocol:'rule-case-binding/1',action:'create',requestId:crypto.randomUUID().replaceAll('-',''),sequence:status.sequence,
        session:original.evidence.session,runtime:original.runtime,revision:original.evidence.nativeRevision,context:owner.context};
      if(owner.retired){await cleanup(owner);throw new Error('案例建立已取消。');}guard();
      await request('/rule-cases/binding',owner.request);guard();
      const notice=document.createElement('p'),mount=document.createElement('section');notice.setAttribute('role','status');notice.textContent=completion;
      element.replaceChildren(notice,mount);
      const pending=RuleCaseWorkbench.mount(mount,{
        captureContext:()=>{guard();return {...owner.context};},
        subscribeContext:listener=>{owner.listeners.add(listener);return ()=>owner.listeners.delete(listener);},
        transport:RuleCaseWorkbench.httpPort(),
        loadCaseData:context=>{guard();return W.readFeatureAttachment(C.KIND,context.contextToken);},
        retainCaseData:async(data,context,lease)=>{
          const originalGuard=()=>{guard();if(context.contextToken!==owner.context.contextToken||!lease.isCurrent())throw new Error('案例保留已取消，未寫入。');};
          originalGuard();const prepared=await W.prepareFeatureAttachment(C.KIND,data,context.contextToken,originalGuard);originalGuard();
          // A successful metadata commit changes the history/revision stamp.
          // Retire explicitly and show completion in the newly mounted host;
          // never repin the old controller to pass its post-await guard.
          const changed=W.commitPreparedFeatureAttachment(prepared,originalGuard);
          if(changed){retire(owner,'案例與原始結果已保留，可一步復原。');queueMicrotask(()=>{if(!active&&element.isConnected&&!element.hidden)open(element,'案例與原始結果已保留；以下是歷史，重跑後取得本次結果。').catch(e=>{notice.textContent=e.message;});});}
          return {ok:true,changed};
        },onClose:close
      });owner.pending=pending;owner.controller=await pending;guard();return owner.controller;
    }catch(error){retire(owner,error.message);throw error;}
  }
  return {open,close};
})();
