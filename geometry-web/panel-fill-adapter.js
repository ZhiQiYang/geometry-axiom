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
  const wire=(ok,label)=>{if(!ok)throw new Error('原生 UI 資料不完整或型別不符：'+label);};
  const integerText=v=>typeof v==='string'&&/^(0|-?[1-9]\d*)$/.test(v)&&BigInt(v)>=-9223372036854775808n&&BigInt(v)<=9223372036854775807n;
  const tuple=(v,n)=>Array.isArray(v)&&v.length===n&&v.every(integerText);
  const axis=v=>['+X','-X','+Y','-Y','+Z','-Z'].includes(v);
  const frame=v=>!!v&&tuple(v.origin,3)&&[v.U,v.V,v.N].every(axis);
  const loop=v=>Array.isArray(v)&&v.every(p=>tuple(p,2));
  const region=v=>!!v&&loop(v.outline)&&Array.isArray(v.holes)&&v.holes.every(loop);
  const unique=(items,key,label)=>{wire(new Set(items.map(key)).size===items.length,label+' 重複身分');};
  const positiveId=v=>id(v)&&v>0;
  const d1=v=>Number.isSafeInteger(v)&&Math.abs(v)<=100000000;
  const parameter=v=>!!v&&id(v.parameterId)&&id(v.fieldId);
  function sameDefinition(a,b,kind){
    const normalized=v=>kind==='finish'&&v?{...v,obstacles:[...v.obstacles].sort()}:v;
    return canonical(normalized(a))===canonical(normalized(b));
  }
  function definitionShape(value,kind){
    wire(value&&typeof value==='object',kind+' 定義');
    if(kind==='finish')wire(positiveId(value.id)&&positiveId(value.boundaryId)&&typeof value.name==='string'&&frame(value.frame)&&
      [-1,1].includes(value.structureSide)&&Array.isArray(value.obstacles)&&value.obstacles.every(v=>typeof v==='string'&&/^[bc]\d+$/.test(v)), '完成面定義');
    if(kind==='fill')wire(positiveId(value.id)&&positiveId(value.finishSurfaceId)&&value.panel&&typeof value.panel.id==='string'&&positiveId(value.panel.version)&&
      ['u','v'].includes(value.lengthAlong)&&Array.isArray(value.origin)&&value.origin.length===2&&value.origin.every(d1)&&
      (d1(value.gap)||parameter(value.gap))&&parameter(value.threshold)&&['straight','stagger'].includes(value.pattern)&&
      (value.pattern==='straight'?!('stagger' in value):value.stagger&&['u','v'].includes(value.stagger.axis)&&(d1(value.stagger.value)||parameter(value.stagger.value))), '鋪排定義');
    if(kind==='host')wire(id(value.id)&&positiveId(value.fillId)&&
      (d1(value.h)||value.h&&(['literal','spec','parameter','material'].includes(value.h.kind))), '宿主定義');
  }
  function validateState(state,contract,stage){
    unique(state.finishSurfaces,r=>r.id,'完成面');unique(state.panelFills,r=>r.definition?.id,'鋪排');unique(state.derivedPlacements,r=>r.definition?.id,'宿主');
    const finishes=new Map(state.finishSurfaces.map(r=>[r.id,r])),fills=new Map(state.panelFills.map(r=>[r.definition?.id,r]));
    const hosts=new Map(state.derivedPlacements.map(r=>[r.definition?.id,r]));
    unique(state.derivedPlacements,r=>r.definition?.fillId,'鋪排宿主');
    const failed=(r,type,recordId)=>{
      const bad=!r.derived||typeof r.derived!=='object'||Array.isArray(r.derived)||Object.prototype.hasOwnProperty.call(r.derived,'error');
      if(bad)wire(!contract.completeForScope&&contract.errors.some(e=>e.stage===stage&&e.recordType===type&&e.id===recordId),type+' 缺派生結果卻未宣告錯誤');
      return bad;
    };
    for(const r of state.finishSurfaces){
      definitionShape(r,'finish');unique(r.obstacles,v=>v,'明選障礙');if(failed(r,'finish-surface',r.id))continue;
      const d=r.derived;wire(axis(d.n)&&region(d.region)&&Array.isArray(d.obstacles),'完成面區域');unique(d.obstacles,o=>o.ref,'障礙');
      wire(d.obstacles.length===r.obstacles.length&&d.obstacles.every(o=>r.obstacles.includes(o.ref)),'明選障礙閉包');
      for(const o of d.obstacles){
        if(Object.prototype.hasOwnProperty.call(o,'error'))wire(!contract.completeForScope&&contract.errors.some(e=>e.stage===stage&&e.recordType==='finish-surface'&&e.id===r.id),'內層障礙錯誤');
        else wire(tuple(o.rect,4)&&tuple(o.q,2)&&typeof o.relation==='string'&&o.layers===null,'障礙精確座標');
      }
    }
    for(const r of state.panelFills){
      const f=r.definition;definitionShape(f,'fill');wire(finishes.has(f.finishSurfaceId),'鋪排完成面來源閉包');if(failed(r,'panel-fill',f.id))continue;
      const d=r.derived;wire(['tileCount','fragmentCount','wholeCount','cutCount'].every(k=>id(d[k]))&&integerText(d.thickness),'片數與厚度');
      wire(['tiles','obstacles','seamLines','effectiveSeams','nonSeams','support'].every(k=>Array.isArray(d[k])),'鋪排派生集合');
      wire(d.threshold===null&&!contract.completeForScope&&contract.errors.some(e=>e.stage===stage&&e.recordType==='panel-fill'&&e.id===f.id)||
        d.threshold&&integerText(d.threshold.num)&&integerText(d.threshold.den)&&BigInt(d.threshold.den)>0n,'精確支撐門檻 X');
      unique(d.tiles,t=>canonical(t.key),'片 key');let fragments=0;
      for(const t of d.tiles){
        wire(Array.isArray(t.key)&&t.key.length===3&&t.key[0]===f.id&&integerText(t.i)&&integerText(t.j)&&t.key[1]===t.i&&t.key[2]===t.j&&tuple(t.body,4)&&typeof t.whole==='boolean'&&Array.isArray(t.fragments),'片 key／座標');
        unique(t.fragments,p=>canonical(p.key),'裁片 key');fragments+=t.fragments.length;
        for(const p of t.fragments)wire(Array.isArray(p.key)&&p.key.length===4&&p.key[0]===f.id&&p.key[1]===t.i&&p.key[2]===t.j&&id(p.key[3])&&integerText(p.area)&&region({outline:p.outer,holes:p.holes}),'裁片精確面積／輪廓');
      }
      wire(d.tiles.length===d.tileCount&&fragments===d.fragmentCount,'裁片集合完整性');
      const seam=(s,effective)=>['u','v'].includes(s.axis)&&integerText(s.k)&&integerText(s.coordinate)&&
        (!('band' in s)||integerText(s.band))&&(!('range' in s)||tuple(s.range,2))&&
        (!effective||(s.fillId===f.id&&tuple(s.range,2)&&tuple(s.edges,2)));
      wire(d.seamLines.every(s=>seam(s,false))&&d.effectiveSeams.every(s=>seam(s,true))&&d.nonSeams.every(s=>seam(s,true)),'板縫完整 key／精確區間');
      for(const p of d.support)wire(id(p.seam)&&p.seam<d.effectiveSeams.length&&tuple(p.range,2)&&integerText(p.left)&&integerText(p.right)&&typeof p.supported==='boolean'&&p.status===(p.supported?'supported':'insufficient'),'原生支撐分段');
      wire(d.derivedPlacement===null||(id(d.derivedPlacement)&&hosts.get(d.derivedPlacement)?.definition.fillId===f.id),'鋪排宿主閉包');
      const refs=finishes.get(f.finishSurfaceId).obstacles;unique(d.obstacles,o=>o.ref,'鋪排障礙');
      wire(d.obstacles.length===refs.length&&d.obstacles.every(o=>refs.includes(o.ref)&&typeof o.panelLayer==='boolean'&&(o.timberLayer===null||typeof o.timberLayer==='boolean')),'鋪排障礙分層閉包');
    }
    for(const r of state.derivedPlacements){
      const h=r.definition;definitionShape(h,'host');wire(r.id===h.id&&fills.has(h.fillId),'宿主鋪排來源閉包');if(failed(r,'derived-placement',h.id))continue;
      const d=r.derived;wire(integerText(d.h)&&frame(d.frame)&&Array.isArray(d.components),'宿主精確框架');
      for(const c of d.components){wire(region(c)&&Array.isArray(c.edges),'宿主分量');
        for(const e of c.edges)wire(Array.isArray(e.key)&&e.key.length>0&&e.key.every(k=>Array.isArray(k)&&k.length===3&&typeof k[0]==='string'&&id(k[1])&&positiveId(k[2]))&&tuple(e.start,2)&&tuple(e.end,2)&&['FREE','FIXED'].includes(e.fixity),'宿主完整邊 key');}
    }
  }
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
    for(const e of c.errors)wire(e&&['finish-surface','panel-fill','derived-placement','transaction'].includes(e.recordType)&&
      (e.id===null||id(e.id))&&['state','before','after'].includes(e.stage)&&typeof e.code==='string'&&typeof e.message==='string','具型別診斷');
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
      validateState(state,c,key);
    }
    if(c.scope.finishSurfaceIds.some(i=>!seenFinish.has(i))||c.scope.fillIds.some(i=>!seenFill.has(i)))
      throw new Error('完成面契約宣告的範圍缺少原生紀錄。');
    return c;
  }
  function requestScope(candidate,snapshot,operations){
    wire(canonical(candidate.before)===canonical(snapshot),'預覽 before 不符本次來源快照');
    if(!candidate.valid)return;
    const keys={finishSurfaces:'finish',panelFills:'fill',derivedPlacements:'host'},expected={};
    for(const [key,kind] of Object.entries(keys))expected[key]=new Map(snapshot[key].map(r=>[kind==='finish'?r.id:r.definition.id,definition(r,kind)]));
    const kinds={'finish-surface':'finishSurfaces','panel-fill':'panelFills','derived-placement':'derivedPlacements'};
    for(const op of operations){
      const match=/^(put|delete)-(finish-surface|panel-fill|derived-placement)$/.exec(op.op||'');wire(match,'未知本片操作');
      const values=expected[kinds[match[2]]];if(match[1]==='put')values.set(op.value.id,clone(op.value));else values.delete(op.id);
    }
    for(const [key,kind] of Object.entries(keys)){
      const actual=new Map(candidate.after[key].map(r=>[kind==='finish'?r.id:r.definition.id,definition(r,kind)]));
      wire(actual.size===expected[key].size&&[...expected[key]].every(([recordId,value])=>sameDefinition(actual.get(recordId),value,kind)), '預覽 after 不符本次 '+key+' 操作範圍');
    }
  }
  function impactContract(candidate){
    wire(Array.isArray(candidate.changes)&&candidate.changes.every(change=>change&&id(change.id)&&
      ['finish-surface','panel-fill','derived-placement'].includes(change.record??'finish-surface')&&
      ['created','modified','deleted','derived'].includes(change.change)), '原生變更清單');
    if(candidate.before.derivedPlacements.length||candidate.after.derivedPlacements.length)
      wire(candidate.dependencies&&['before','after'].every(stage=>candidate.dependencies[stage]&&
        Array.isArray(candidate.dependencies[stage].geometry?.timbers)), '宿主下游影響缺少原生前後依賴');
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
      this.snapshot=final.state;this.snapshotFresh=true;this.contract=final;this.revision=last.revision;
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
        requestScope({...result,before:c.before,after:c.after},this.snapshot,operations);
        impactContract({...result,before:c.before,after:c.after});
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
        checked(reply);this.receipt=reply;this.candidate=null;this.dirty=false;this.snapshotFresh=false;
        // The shared apiRequest observer owns dirty/history. Never create a second entry here.
        const sameOwner=workspace().context()===this.owner.context && workspace().getProjectState().contextToken===this.owner.contextToken;
        if(this.retired||!sameOwner){this.phase='committed';this.reason='原生已確認；視圖已退役，請重新開啟讀取正式資料。';return reply;}
        await this.refreshPresentation(); // PF_UI05_CONFIRM_SCENE_SYNC
        this.owner=owner(this.boundaryId);const official=checked(await apiRequest('panel-fill-read'));
        this.assertCurrent();const currentContract=contract(official);
        this.snapshot=currentContract.state;this.snapshotFresh=true;this.contract=currentContract;this.revision=official.revision;
        this.ids=checked(await apiRequest('newid'));this.assertCurrent();
        this.phase='committed';this.reason=reply.history_changed===false?'原生確認定義未變更；零新增歷史。':'已確認；正式定義已重新讀取。此確認只新增一筆共用歷史。';this.emit();return reply;
      }catch(error){
        this.phase=reply?.ok?'committed':error.reply?'invalid':'unknown';
        this.reason=reply?.ok?'原生已確認，畫面重新讀取失敗；請重新開啟，不要重送。':
          this.phase==='unknown'?'確認結果未知；禁止重送，請查原 requestId 回執。':error.message;
        this.emit();throw error;
      }
    }
    async refreshPresentation(){
      const pin=owner(this.boundaryId);
      // Existing card-position metadata may change revision while this refresh
      // runs. Keep context/incarnation/history ownership, then repin after it.
      const current=()=>{
        const ws=workspace(),p=ws.getProjectState(),h=ws.history;
        return !this.retired&&ws.context()===pin.context&&p.contextToken===pin.contextToken&&p.id===pin.projectId&&
          h?.frame===pin.frame&&h?.frame?.ids?.get(this.boundaryId)===pin.incarnation&&h?.undo?.at(-1)===pin.undo&&
          h?.redo?.at(-1)===pin.redo&&h?.undo?.length===pin.undoLength&&h?.redo?.length===pin.redoLength&&
          (typeof connection==='undefined'||connection.session===pin.session&&connection.phase==='ready');
      };
      if(!current()||await renderObjects({current})!==true||!current())throw new Error('確認已完成，但原場景身分已變更或物件畫面未能刷新。');
    }
    async reconcileReceipt(reply,command) {
      if(this.phase!=='unknown'||command!=='panel-fill-confirm '+token(this.candidate?.token))return false;
      this.receipt=reply;this.candidate=null;
      if(!reply?.ok){this.phase='invalid';this.reason=reply?.error||'原確認回執為失敗；正式資料未套用。';this.emit();return true;}
      this.dirty=false;this.snapshotFresh=false;this.phase='committed';this.reason=reply.history_changed===false?'原 requestId 回執取得：定義未變更，零新增歷史，未重送。':'原 requestId 回執取得：已確認，未重送。';
      if(this.retired||workspace().context()!==this.owner.context||workspace().getProjectState().contextToken!==this.owner.contextToken||
         (typeof connection!=='undefined'&&connection.phase!=='ready')){this.reason+=' 請重新開啟讀取正式資料。';this.emit();return true;}
      this.owner=owner(this.boundaryId);
      try {
        const official=checked(await apiRequest('panel-fill-read'));this.assertCurrent();const c=contract(official);
        this.snapshot=c.state;this.snapshotFresh=true;this.contract=c;this.revision=official.revision;
        this.ids=checked(await apiRequest('newid'));this.assertCurrent();
      }catch(error){this.reason+=' 畫面重讀失敗，請重新開啟：'+error.message;}
      this.emit();return true;
    }
    close(){if(['confirming','unknown'].includes(this.phase))return false;++this.generation;this.retired=true;this.discardCandidate();return true;}
  }
  const api={ACTIONS,Session,contract,definition,canonical,clone,isCurrent,requestScope,sameDefinition};
  root.PanelFillAdapter=api;
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
