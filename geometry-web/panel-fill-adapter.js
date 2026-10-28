/* UI-1 transport. Native definitions and exact derived records are authoritative. */
"use strict";
(function (root) {
  const ACTIONS = Object.freeze(['read','edit-definitions','read-layout','read-support']);
  const clone = value => JSON.parse(JSON.stringify(value));
  const canonical = value => JSON.stringify(value, (_, v) => v && typeof v === 'object' && !Array.isArray(v)
    ? Object.keys(v).sort().reduce((out,key)=>(out[key]=v[key],out),{}) : v);
  const checked = value => {
    if (!value?.ok) { const error=new Error(value?.error || '原生服務未完成操作。'); error.reply=value; throw error; }
    return value;
  };
  const id = value => Number.isSafeInteger(value) && value >= 0 && value <= 4294967295;
  const workspace = () => typeof ReferenceWorkspace!=='undefined' ? ReferenceWorkspace : root.ReferenceWorkspace;
  function contract(reply, preview=false) {
    const c=reply?.uiContract;
    if (!c || c.schema!=='panel-fill-workspace/1' || !Array.isArray(c.supportedActions) ||
        c.supportedActions.some(a=>!ACTIONS.includes(a)) || new Set(c.supportedActions).size!==c.supportedActions.length ||
        !c.supportedActions.includes('read') || !/^\d+$/.test(c.revision) ||
        !Number.isSafeInteger(reply.revision) || c.revision!==String(reply.revision) ||
        typeof c.completeForScope!=='boolean' || !Array.isArray(c.errors) ||
        !c.scope || !['finishSurfaceIds','fillIds'].every(k=>Array.isArray(c.scope[k]) &&
          c.scope[k].every(id) && new Set(c.scope[k]).size===c.scope[k].length))
      throw new Error('目前服務未提供相容、完整的完成面 UI 契約；此片功能不可用。');
    const seenFinish=new Set(),seenFill=new Set();
    for (const key of preview ? ['before','after'] : ['state']) {
      const state=c[key];
      if (!state || !['finishSurfaces','panelFills','derivedPlacements'].every(k=>Array.isArray(state[k])))
        throw new Error('完成面回覆缺少完整定義或原生派生資料。');
      if (state.finishSurfaces.some(r=>!id(r.id)||!c.scope.finishSurfaceIds.includes(r.id)) ||
          state.panelFills.some(r=>!id(r.definition?.id)||!c.scope.fillIds.includes(r.definition.id)))
        throw new Error('完成面回覆的來源範圍不一致。');
      for(const record of state.finishSurfaces)seenFinish.add(record.id);
      for(const record of state.panelFills)seenFill.add(record.definition.id);
      if(c.completeForScope && (c.errors.length || [...state.finishSurfaces,...state.panelFills,...state.derivedPlacements]
        .some(r=>r.derived?.error))) throw new Error('原生完整性旗標與內層錯誤不一致，禁止確認。');
    }
    if(c.scope.finishSurfaceIds.some(i=>!seenFinish.has(i))||c.scope.fillIds.some(i=>!seenFill.has(i)))
      throw new Error('完成面契約宣告的範圍缺少原生紀錄。');
    return c;
  }
  function definition(record, kind) {
    if (!record) return null;
    if(kind!=='finish')return clone(record.definition);
    const {id,name,boundaryId,frame,structureSide,obstacles}=record;
    const origin=frame.origin.map(value=>{
      const text=String(value);if(!/^-?\d+$/.test(text))throw new Error('完成面座標不是 D1 整數。');
      const n=Number(text);if(!Number.isSafeInteger(n)||Math.abs(n)>100000000)throw new Error('完成面座標超出 D1。');return n;
    });
    return clone({id,name,boundaryId,frame:{...frame,origin},structureSide,obstacles});
  }
  function owner(boundaryId) {
    const ws=workspace(), context=ws.context(), p=ws.getProjectState(), history=ws.history;
    return {boundaryId,context,contextToken:p.contextToken,projectId:p.id,projectRevision:p.revision,
      frame:history?.frame,incarnation:history?.frame?.ids?.get(boundaryId),undo:history?.undo?.at(-1),
      redo:history?.redo?.at(-1),undoLength:history?.undo?.length,redoLength:history?.redo?.length,
      nativeRevision:ws.getEvidenceState?.().nativeRevision??null,
      session:typeof connection!=='undefined'?connection.session:undefined};
  }
  function isCurrent(pin) {
    const ws=workspace(),p=ws.getProjectState(),h=ws.history;
    return ws.context()===pin.context && p.contextToken===pin.contextToken && p.id===pin.projectId &&
      p.revision===pin.projectRevision && h?.frame===pin.frame && h?.frame?.ids?.get(pin.boundaryId)===pin.incarnation &&
      h?.undo?.at(-1)===pin.undo && h?.redo?.at(-1)===pin.redo && h?.undo?.length===pin.undoLength &&
      h?.redo?.length===pin.redoLength && (pin.nativeRevision===null || ws.getEvidenceState?.().nativeRevision===pin.nativeRevision) &&
      (typeof connection==='undefined'||(connection.session===pin.session&&connection.phase==='ready'));
  }
  function token(value) {
    if(!/^[1-9]\d*$/.test(String(value))||!Number.isSafeInteger(Number(value))||Number(value)>4294967295)
      throw new Error('預覽識別無效，請重新預覽。');return String(value);
  }
  class Session {
    constructor(boundaryId,onChange) {
      if(!id(boundaryId)||boundaryId===0)throw new Error('請從既有物件面開啟面設定。');
      this.boundaryId=boundaryId;this.owner=owner(boundaryId);this.onChange=onChange;this.generation=0;
      this.phase='loading';this.candidate=null;this.retired=false;this.reason='正在讀取完成面來源。';
      this.dirty=false;
    }
    current(generation=this.generation) {return !this.retired && generation===this.generation && isCurrent(this.owner);}
    assertCurrent(generation=this.generation) {if(!this.current(generation))throw new Error('專案、面或來源已變更，請重新開啟面設定。');}
    emit(){this.onChange?.();}
    async read() {
      const generation=this.generation, first=checked(await apiRequest('panel-fill-read'));
      this.assertCurrent(generation);const c=contract(first);
      const [engineering,objects,ids]=await Promise.all(['engineering-read','objects','newid'].map(async cmd=>checked(await apiRequest(cmd))));
      this.assertCurrent(generation);
      const last=checked(await apiRequest('panel-fill-read'));this.assertCurrent(generation);
      const final=contract(last);if(final.revision!==c.revision)throw new Error('讀取期間原生來源已變更，請重新開啟。');
      if(!id(ids.finishSurface)||!id(ids.panelFill)||!id(ids.placement))throw new Error('目前服務未提供完成面、鋪排與宿主的正式識別。');
      this.snapshot=final.state;this.contract=final;this.revision=last.revision;
      this.owner.nativeRevision=workspace().getEvidenceState?.().nativeRevision??null;
      this.sources=engineering.state;this.objects=objects;this.ids=ids;
      this.phase='editing';this.reason=final.completeForScope?'請設定完成面與鋪排，再由原生預覽。':'來源不完整；可檢視及修正定義，尚不可確認。';
      return this;
    }
    discardCandidate() {
      const candidate=this.candidate;this.candidate=null;
      if(candidate?.token)apiRequest('panel-fill-cancel '+token(candidate.token)).catch(()=>{});
    }
    changed() {
      if(['confirming','unknown'].includes(this.phase))return false;
      ++this.generation;this.dirty=true;this.discardCandidate();this.phase='editing';this.reason='輸入已變更；舊預覽不可確認。';return true;
    }
    invalidate(reason='來源已變更，請重新開啟。') {
      ++this.generation;this.retired=true;
      if(!['confirming','unknown'].includes(this.phase))this.discardCandidate();
      this.phase=['confirming','unknown'].includes(this.phase)?this.phase:'invalid';this.reason=reason;this.emit();
    }
    async preview(operations) {
      this.assertCurrent();if(!this.contract.supportedActions.includes('edit-definitions'))throw new Error('目前服務不支援編輯完成面定義。');
      this.changed();if(!operations.length){this.dirty=false;this.reason='定義沒有變更；不建立候選，也不新增歷史。';this.emit();return null;}
      const generation=this.generation;this.phase='previewing';this.reason='原生正在計算候選；尚未套用。';this.emit();
      let result;
      try {
        const response=await fetch('/panel-fill/preview',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({schema:'panel-fill-transaction/1',expectedRevision:this.revision,operations}),signal:AbortSignal.timeout(30000)});
        checkApiSession(response);if(!response.ok)throw new Error(`無法建立預覽（HTTP ${response.status}）。`);
        result=checked(await response.json()).preview;
        if(!result||typeof result.valid!=='boolean')throw new Error('原生預覽資料不完整。');
        if(!this.current(generation)){if(result.token)await apiRequest('panel-fill-cancel '+token(result.token));return null;}
        const c=contract(result,true);if(c.revision!==String(this.revision))throw new Error('預覽來源版本已變更。');
        const required=['edit-definitions','read-layout','read-support'];
        this.candidate={...result,before:c.before,after:c.after,uiContract:c,generation};
        this.phase=result.valid && c.completeForScope && !c.errors.length && required.every(a=>c.supportedActions.includes(a)) ? 'confirmable':'invalid';
        this.reason=this.phase==='confirmable'?'候選尚未套用；請核對原生結果後確認。':'候選不完整或違反條件，禁止確認；請依診斷修正。';this.emit();return this.candidate;
      } catch(error) {
        if(this.current(generation)){this.phase='invalid';this.reason=error.message;this.emit();}
        if(result?.token && !this.candidate)await apiRequest('panel-fill-cancel '+token(result.token)).catch(()=>{});
        throw error;
      }
    }
    async confirm() {
      this.assertCurrent();const c=this.candidate;
      if(this.phase!=='confirmable'||!c||c.generation!==this.generation)throw new Error('沒有目前可確認的候選。');
      workspace().assertEditable();workspace().assertAssemblyIdle?.();
      this.phase='confirming';this.reason='正在等待原生確認回執；請勿重複提交。';this.emit();
      this.confirmationCommand='panel-fill-confirm '+token(c.token);
      let reply;
      try {
        reply=await apiRequest(this.confirmationCommand);
        if(reply?.transport){this.phase='unknown';this.reason='確認結果未知。保留原 requestId 回執，禁止重送；請由連線回執復原。';this.emit();return reply;}
        checked(reply);this.receipt=reply;this.candidate=null;this.dirty=false;
        // The shared apiRequest observer owns dirty/history. Never create a second entry here.
        const sameOwner=workspace().context()===this.owner.context && workspace().getProjectState().contextToken===this.owner.contextToken;
        if(this.retired||!sameOwner){this.phase='committed';return reply;}
        this.owner=owner(this.boundaryId);const official=checked(await apiRequest('panel-fill-read'));
        this.assertCurrent();const currentContract=contract(official);
        this.snapshot=currentContract.state;this.contract=currentContract;this.revision=official.revision;
        this.ids=checked(await apiRequest('newid'));this.assertCurrent();
        this.phase='committed';this.reason='已確認；正式定義已重新讀取。此確認只新增一筆共用歷史。';this.emit();return reply;
      }catch(error){
        this.phase=reply?.ok?'committed':error.reply?'invalid':'unknown';
        this.reason=reply?.ok?'原生已確認，畫面重新讀取失敗；請重新開啟，不要重送。':
          this.phase==='unknown'?'確認結果未知；禁止重送，請查原 requestId 回執。':error.message;
        this.emit();throw error;
      }
    }
    async reconcileReceipt(reply,command) {
      if(this.phase!=='unknown'||command!=='panel-fill-confirm '+token(this.candidate?.token))return false;
      this.receipt=reply;this.candidate=null;
      if(!reply?.ok){this.phase='invalid';this.reason=reply?.error||'原確認回執為失敗；正式資料未套用。';this.emit();return true;}
      this.dirty=false;this.phase='committed';this.reason='原 requestId 回執取得：已確認，未重送。';
      if(this.retired||workspace().context()!==this.owner.context||workspace().getProjectState().contextToken!==this.owner.contextToken){this.emit();return true;}
      this.owner=owner(this.boundaryId);
      try {
        const official=checked(await apiRequest('panel-fill-read'));this.assertCurrent();const c=contract(official);
        this.snapshot=c.state;this.contract=c;this.revision=official.revision;
        this.ids=checked(await apiRequest('newid'));this.assertCurrent();
      }catch(error){this.reason+=' 畫面重讀失敗，請重新開啟：'+error.message;}
      this.emit();return true;
    }
    close(){if(['confirming','unknown'].includes(this.phase))return false;++this.generation;this.retired=true;this.discardCandidate();return true;}
  }
  const api={ACTIONS,Session,contract,definition,canonical,clone,isCurrent};
  root.PanelFillAdapter=api;
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
