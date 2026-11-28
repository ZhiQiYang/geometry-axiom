/* PF-6 App owner. All geometry and R43 results come from the native candidate. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./panel-fill-adapter.js'):root.PanelFillAdapter);if(typeof module==='object'&&module.exports)module.exports=api;else root.PanelFillBuilderSession=api;})(typeof globalThis!=='undefined'?globalThis:this,A=>{
  'use strict';
  const clone=v=>JSON.parse(JSON.stringify(v)),same=(a,b)=>A.canonical(a)===A.canonical(b);
  const uint=v=>Number.isInteger(v)&&v>=0&&v<=4294967295;
  const uint64=v=>typeof v==='string'&&/^(0|[1-9]\d{0,19})$/.test(v)&&BigInt(v)<=18446744073709551615n;
  const exact=v=>typeof v==='string'&&/^(0|-?[1-9]\d*)$/.test(v);
  const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
  const token=v=>uint(v)&&v>0?String(v):typeof v==='string'&&/^[1-9]\d{0,9}$/.test(v)&&uint(Number(v))?v:null;
  const fail=(code,message)=>Object.assign(new Error(code+'：'+message),{code});
  const check=(condition,message)=>{if(!condition)throw fail('PF6_VIEW',message);};
  const keys=(value,names)=>value&&typeof value==='object'&&!Array.isArray(value)&&same(Object.keys(value).sort(),names.slice().sort());
  function source(value,field){
    if(!value||typeof value!=='object')return false;
    if(value.kind==='literal')return keys(value,['kind','value'])&&Number.isSafeInteger(value.value)&&value.value>0&&value.value<=100000000;
    if(value.kind==='spec')return keys(value,['kind','name'])&&typeof value.name==='string'&&value.name.length>0;
    if(value.kind==='parameter')return keys(value,['kind','parameterId','fieldId'])&&uint(value.parameterId)&&uint(value.fieldId);
    return value.kind==='material'&&keys(value,['kind','id','version','field'])&&typeof value.id==='string'&&value.id.length>0&&uint(value.version)&&value.version>0&&value.field===field;
  }
  function validateInput(input,fillId){
    check(keys(input,['fillId','A','B','roles'])&&input.fillId===fillId&&source(input.A,'A')&&source(input.B,'B')&&
      keys(input.roles,['u','v'])&&['primary','secondary'].includes(input.roles.u)&&['primary','secondary'].includes(input.roles.v)&&input.roles.u!==input.roles.v,'請明選正式鋪排、A／B 來源與主副支方向。');
  }
  // D28 的本面套用是既有角材的讀取格式，不是 D45 表單可選的新輸入。
  function dimension(d,field,existingRole){
    const value=d?.source,application=existingRole&&keys(value,['kind','id','field'])&&value.kind==='application'&&
      typeof value.id==='string'&&value.id.length>0&&value.field===existingRole+'.'+field;
    return d&&(source(value,field)||application)&&exact(d.effective)&&BigInt(d.effective)>0n&&d.unit==='mm'&&typeof d.name==='string';}
  function timberState(row,existing){
    if(row===null)return true;const g=row?.geometry,role=existing&&row?.role;
    return ['boundary','primary','secondary'].includes(row?.role)&&dimension(row.A,'A',role)&&dimension(row.B,'B',role)&&g&&uint(g.surface)&&
      ['centerline','length','u','v','A','B'].every(name=>exact(g[name]))&&BigInt(g.length)>0n&&['+u','-u','+v','-v'].includes(g.dir)&&['+n','-n'].includes(g.side)&&
      Array.isArray(g.origin)&&g.origin.length===3&&g.origin.every(exact)&&Array.isArray(g.axes)&&g.axes.length===3&&g.axes.every(axis=>Array.isArray(axis)&&axis.length===3&&axis.every(exact));
  }
  function validateView(view,{revision,setKey,generation,phase,input,selected}){
    check(view&&view.schema==='panel-fill-builder-workspace/1'&&uint64(view.revision)&&view.revision===revision&&view.setKey===setKey&&hash(view.setKey)&&uint64(view.generation)&&view.generation===generation&&view.phase===phase,'候選版本、階段或來源世代不完整。');
    check(Array.isArray(view.selected)&&new Set(view.selected).size===view.selected.length&&same(view.selected.slice().sort(),selected.slice().sort()),'候選明選集合與目前選擇不符。');
    check(view.input?.fillId===input.fillId&&view.input.primaryAlong===(input.roles.u==='primary'?'v':'u'),'候選鋪排或主副支方向不符。');
    for(const field of ['A','B']){
      const d=view.input[field];check(d&&same(d.source,input[field])&&d.unit==='mm'&&typeof d.name==='string'&&
        (d.effective===null||exact(d.effective)),'候選 '+field+' 缺來源或精確有效值。');
    }
    check(typeof view.completeForScope==='boolean'&&view.host&&typeof view.host.created==='boolean'&&(view.host.id===null||uint(view.host.id))&&view.grid&&typeof view.grid.created==='boolean'&&(view.grid.id===null||uint(view.grid.id)),'宿主／主格建立與沿用資料不完整。');
    const c=view.uiContract;
    check(c?.schema==='panel-fill-workspace/1'&&c.revision===revision&&typeof c.completeForScope==='boolean'&&Array.isArray(c.errors)&&Array.isArray(c.supportedActions)&&same(c.supportedActions,A.ACTIONS),'同候選完成面／承接投影不完整。'); // PF6_APP_COMPLETE_ORDERED_CAPABILITIES
    check(c.scope&&['finishSurfaceIds','fillIds','fillGridIds'].every(name=>Array.isArray(c.scope[name])&&c.scope[name].every(uint)&&new Set(c.scope[name]).size===c.scope[name].length)&&c.scope.fillIds.includes(input.fillId),'同候選投影缺少完整來源範圍。');
    const seen={finishSurfaceIds:new Set(),fillIds:new Set(),fillGridIds:new Set()};
    for(const stage of ['before','after']){
      const value=c[stage];check(value&&['finishSurfaces','panelFills','derivedPlacements','fillGrids'].every(name=>Array.isArray(value[name])),'同候選缺少 '+stage+' 全部資料。');
      A.validateState(value,c,stage);
      for(const r of value.finishSurfaces){check(c.scope.finishSurfaceIds.includes(r.id),'完成面超出 scope。');seen.finishSurfaceIds.add(r.id);}
      for(const r of value.panelFills){check(c.scope.fillIds.includes(r.definition.id),'鋪排超出 scope。');seen.fillIds.add(r.definition.id);}
      for(const r of value.fillGrids){check(c.scope.fillGridIds.includes(r.id),'主格超出 scope。');seen.fillGridIds.add(r.id);}
    }
    for(const name of Object.keys(seen))check(c.scope[name].every(id=>seen[name].has(id)),'宣告範圍缺少原生紀錄。');
    check(Array.isArray(view.timbers)&&new Set(view.timbers.map(row=>row?.id)).size===view.timbers.length&&view.timbers.every(row=>row&&uint(row.id)&&'before' in row&&'after' in row),'缺少新舊角材完整影響。');
    if(view.completeForScope){
      check(c.completeForScope&&c.errors.length===0&&['A','B'].every(field=>dimension(view.input[field],field)),'完整性旗標與來源／承接結果矛盾。');
      check(view.timbers.every(row=>timberState(row.before,true)&&timberState(row.after,row.before!==null)&&!(row.before===null&&row.after===null)),'完整投影缺少角材尺寸、中線或世界幾何。'); // PF6_APP_COMPLETE_GEOMETRY
      if(view.host.id!==null){const h=c.after.derivedPlacements.find(r=>r.id===view.host.id);check(h?.definition.fillId===input.fillId&&dimension(view.host.h,'B')&&same(h.definition.h,view.host.h.source)&&h.derived.h===view.host.h.effective,'宿主來源與候選有效值不符。');}
      if(view.grid.id!==null){const g=c.after.fillGrids.find(r=>r.id===view.grid.id);check(g?.definition.hostId===view.host.id&&g.definition.fillId===input.fillId&&g.definition.mainAlong===view.grid.mainAlong,'主格來源與候選不符。');}
    }
    return view;
  }
  function validateEntries(entries){
    check(Array.isArray(entries)&&new Set(entries.map(e=>e?.key)).size===entries.length,'建議清單缺失或鍵重複。');
    for(const e of entries)check(hash(e.key)&&typeof e.selectable==='boolean'&&typeof e.valid==='boolean'&&typeof e.selected==='boolean'&&typeof e.phase==='string'&&typeof e.role==='string'&&['u','v'].includes(e.axis)&&e.source&&exact(e.source.k)&&(e.source.band===null||exact(e.source.band))&&Array.isArray(e.source.range)&&e.source.range.length===2&&e.source.range.every(exact)&&e.geometry&&Array.isArray(e.geometry.rect)&&e.geometry.rect.length===4&&e.geometry.rect.every(exact)&&exact(e.geometry.length)&&Array.isArray(e.diagnostics),'建議列缺少精確來源、幾何或診斷。');
  }
  class Session {
    constructor({host,transport,boundaryId,fillId,revision,snapshot,sources,onChange}){
      this.host=host;this.transport=transport;this.boundaryId=boundaryId;this.fillId=fillId;this.revision=revision;this.snapshot=clone(snapshot);this.sources=clone(sources||{});this.onChange=onChange;
      check(uint(boundaryId)&&uint(fillId)&&uint64(revision)&&snapshot.panelFills.some(r=>r.definition.id===fillId&&snapshot.finishSurfaces.some(f=>f.id===r.definition.finishSurfaceId&&f.boundaryId===boundaryId)),'只能從本面已確認的正式鋪排進入建議。');
      this.owner=this.stamp();this.phase='editing';this.reason='明選 A、B 來源與主支走向；尚未取得建議。';this.input=null;this.suggestions=null;this.candidate=null;this.committedDefinitions=[];this.receipt=null;this.selected=[];this.lease=null;this.cleanupToken=null;this.pendingCommand=null;this.retired=false;this.cancelRequested=false;this.operation=null;
    }
    stamp(){const p=this.host.getProjectState(),e=this.host.getEvidenceState(),h=this.host.history,native=e.nativeDefinitionRevision??e.nativeRevision;return {contextToken:p.contextToken,projectRevision:p.revision,projectId:p.id,session:e.session,nativeRevision:native===null||native===undefined?null:String(native),context:this.host.context?.(),frame:h?.frame,incarnation:h?.frame?.ids?.get(this.boundaryId)};}
    current(){
      if(this.retired)return false;const next=this.stamp(),old=this.owner;
      if(next.contextToken!==old.contextToken||next.projectId!==old.projectId||next.session!==old.session||next.context!==old.context||next.frame!==old.frame||next.incarnation!==old.incarnation||next.nativeRevision!==old.nativeRevision)return false;
      if(next.projectRevision!==old.projectRevision){
        if(!this.lease||this.host.refreshTimberPreviewPresentation?.(this.lease)!==true)return false; // PF6_APP_CANVAS_POS_EXPIRES
        this.owner=next;
      }
      return true;
    }
    assertCurrent(){if(!this.current())throw fail('PF6_STALE','專案、面或幾何來源已變更；舊候選不可確認。');}
    get busy(){return ['suggesting','selecting','confirming','cancelling','unknown'].includes(this.phase);}
    get pending(){return !!this.lease||this.busy||this.cleanupToken!==null;}
    get confirmable(){
      const p=this.candidate;if(!['confirmable','confirm-not-sent'].includes(this.phase)||this.retired||!p||p.valid!==true||p.phase!=='SELECTED'||token(p.token)===null||p.appView?.completeForScope!==true||p.appView?.uiContract?.completeForScope!==true)return false; // PF6_APP_TOKEN_MEANS_VALID
      try{this.validateCandidate(p);return this.current();}catch(_){return false;}
    }
    emit(){this.onChange?.();}
    acquire(){if(!this.lease)this.lease=this.host.beginTimberPreview('pf6');}
    revoke(){if(this.lease)this.host.clearTimberPreviewToken(this.lease);this.candidate=null;} // PF6_APP_KEEP_OLD_SELECTION_TOKEN
    release(){this.host.finishTimberPreview(this.lease);this.lease=null;this.cleanupToken=null;this.pendingCommand=null;this.candidate=null;}
    idle(){if(this.busy||['cleanup-required','confirm-not-sent'].includes(this.phase))throw fail('PF6_PENDING','請先完成本次取消或確認；結果待查時只能核對原回執。');}
    async edit(){this.idle();this.revoke();if(this.cleanupToken!==null)await this.cancelToken();this.release();this.input=null;this.suggestions=null;this.committedDefinitions=[];this.receipt=null;this.selected=[];this.phase='editing';this.reason='輸入已變更；請重新取得建議並明選集合。';this.emit();}
    async suggest(input){
      this.idle();this.assertCurrent();validateInput(input,this.fillId);this.revoke();if(this.cleanupToken!==null){await this.cancelToken();this.assertCurrent();}this.acquire();
      this.input=clone(input);this.suggestions=null;this.committedDefinitions=[];this.receipt=null;this.selected=[];this.phase='suggesting';this.reason='正在取得原生建議；尚未建立任何角材。';this.cancelRequested=false;this.emit();
      const run=(async()=>{try{
        const r=await this.transport.post('/panel-fill/builder/suggest',{schema:'panel-fill-builder-suggest/1',expectedRevision:this.revision,input:clone(input),pre:[],post:[]},this.owner.session);
        if(!r?.ok)throw fail(r?.code||'PF6_SUGGEST',r?.error||'原生建議遭拒。');
        check(r.schema==='panel-fill-builder-suggestions/1'&&r.revision===this.revision&&hash(r.setKey)&&uint64(r.generation)&&r.token===null&&r.confirmable===false&&typeof r.valid==='boolean','建議回覆不是目前來源的唯讀建議。');
        validateEntries(r.entries);validateEntries(r.omissions);validateView(r.appView,{revision:this.revision,setKey:r.setKey,generation:r.generation,phase:'ANALYSIS',input,selected:[]});
        check(same(r.appView.uiContract.before,this.snapshot),'建議的確認前資料不符本次正式來源快照。');
        if(this.cancelRequested||!this.current()){this.release();this.phase='cancelled';this.reason='晚到建議已退役，沒有新增物件。';return null;}
        this.suggestions=clone(r);this.phase='suggested';this.reason=r.valid&&r.appView.completeForScope?'請明選要建立的集合，再預覽這份集合。':'整輪建議不完整或不成立；清單只供診斷，不能選取成功前綴。';this.emit();return r;
      }catch(error){if(error.transport){this.phase='unknown';this.pendingCommand=error.command;this.reason='取得建議結果待查；只核對原回執，不重送。';}else{this.release();this.phase='rejected';this.reason=error.message;}this.emit();throw error;}finally{this.operation=null;}})();this.operation=run;return run;
    }
    async select(selected){
      this.idle();this.assertCurrent();const r=this.suggestions;
      check(r?.valid===true&&r.appView?.completeForScope===true&&Array.isArray(selected)&&new Set(selected).size===selected.length&&selected.every(k=>r.entries.some(e=>e.key===k&&e.selectable&&e.valid)),'整輪建議須完整通過，且每個項目均須明選可用鍵。');
      this.revoke();this.selected=selected.slice();this.reason='集合已變更；舊候選不可確認。';this.emit();
      if(this.cleanupToken!==null)await this.cancelToken();this.phase='suggested';this.emit();
    }
    validateCandidate(p){
      const r=this.suggestions;check(p?.schema==='panel-fill-builder-preview/1'&&p.revision===this.revision&&['SELECTED','NO_OP'].includes(p.phase)&&typeof p.valid==='boolean'&&typeof p.beforeScene==='string'&&typeof p.afterScene==='string'&&Array.isArray(p.createdDefinitions)&&Array.isArray(p.reusedDefinitions)&&Array.isArray(p.violations)&&Array.isArray(p.dependencies?.timbers)&&Array.isArray(p.dependencies?.guides),'預覽缺少完整候選或影響資料。');
      check(p.candidateIdsAreTemporary===true,'候選缺少暫號聲明，不能當作正式定義。'); // PF6_APP_TEMPORARY_ID_FLAG
      check(p.idMap===null,'正式識別映射只能來自確認回執。'); // PF6_APP_NO_PREVIEW_ID_MAP
      check(p.phase!=='SELECTED'||token(p.token)!==null,'集合候選必須持有正整數令牌。'); // PF6_APP_POSITIVE_SELECTED_TOKEN
      validateEntries(p.entries);validateEntries(p.omissions);
      validateView(p.appView,{revision:this.revision,setKey:r.setKey,generation:r.generation,phase:p.phase,input:this.input,selected:this.selected});
      check(same(p.appView.uiContract.before,this.snapshot),'候選的確認前資料不符本次正式來源快照。');
      check(p.createdDefinitions.every(row=>keys(row,['kind','tempKey','candidateId'])&&['timber','placement','grid'].includes(row.kind)&&uint(row.candidateId)&&typeof row.tempKey==='string'&&row.tempKey.length>0),'新建定義必須只有種類、暫時鍵與候選暫號。'); // PF6_APP_CREATED_DEFINITION_SHAPE
      check(new Set(p.createdDefinitions.map(row=>row.tempKey)).size===p.createdDefinitions.length,'候選暫時鍵重複。'); // PF6_APP_UNIQUE_TEMP_KEYS
      if(p.valid&&p.appView.completeForScope)check(p.createdDefinitions.filter(row=>row.kind==='timber').every(row=>p.appView.timbers.some(t=>t.id===row.candidateId&&t.after!==null)),'完整投影漏列本次新增角材。'); // PF6_APP_COMPLETE_GEOMETRY
      check(same(p.entries.filter(e=>e.selected).map(e=>e.key).sort(),this.selected.slice().sort()),'候選列與明選來源集合不符。');
      if(p.phase==='NO_OP')check(p.token===null&&p.beforeScene===p.afterScene&&p.createdDefinitions.length===0,'空選不得建立宿主、主格或令牌。');
      return p;
    }
    async preview(){
      this.idle();this.assertCurrent();check(this.suggestions?.valid&&this.suggestions.appView.completeForScope,'請先取得完整、有效的建議。');this.revoke();if(this.cleanupToken!==null){await this.cancelToken();this.assertCurrent();}this.acquire();
      const r=this.suggestions;this.phase='selecting';this.cancelRequested=false;this.reason='正在 fresh 候選重新求值明選集合；尚未寫入。';this.emit();
      const run=(async()=>{try{
        const reply=await this.transport.post('/panel-fill/builder/select',{schema:'panel-fill-builder-select/1',expectedRevision:this.revision,setKey:r.setKey,generation:r.generation,selected:this.selected.slice()},this.owner.session);
        if(!reply?.ok)throw fail(reply?.code||'PF6_SELECT',reply?.error||'本次集合遭拒。');
        const p=reply.preview;this.cleanupToken=token(p?.token); // PF6_APP_POSITIVE_CLEANUP_TOKEN: invalid candidates still own a positive handle.
        if(this.cancelRequested||!this.current()){if(this.cleanupToken!==null)await this.cancelToken();this.release();this.phase='cancelled';this.reason='晚到候選已精確取消，沒有新增物件。';this.emit();return null;}
        this.validateCandidate(p);this.candidate=clone(p);
        if(p.phase==='NO_OP'){this.phase='suggested';this.reason='明選集合為空；沒有建立宿主、主格、角材或歷史。';}
        else if(p.valid&&p.appView.completeForScope&&p.appView.uiContract.completeForScope&&this.cleanupToken!==null){this.host.bindTimberPreview(this.lease,p.token);this.phase='confirmable';this.reason='請核對本次所選集合的最終幾何與承接結果；確認才建立一筆歷史。';}
        else{this.phase='rejected';this.reason='本次候選違規或投影不完整，禁止確認；可改選或取消。';}
        this.emit();return p;
      }catch(error){if(error.transport&&error.sent===false){this.phase='cleanup-required';this.pendingCommand=null;}else if(error.transport){this.phase='unknown';this.pendingCommand=error.command;this.reason='集合預覽結果待查；只核對原回執，不重送。';}else{this.revoke();this.phase='rejected';this.reason=error.message;if(this.cleanupToken!==null)await this.cancelToken();}this.emit();throw error;}finally{this.operation=null;}})();this.operation=run;return run;
    }
    async cancelToken(){
      if(this.cleanupToken===null)return {ok:true,cancelled:false};
      if(this.owner.session!==this.stamp().session)throw fail('PF6_STALE','服務工作階段已改變；不會把舊 token 傳給新服務。');
      const command='pf6-cancel '+this.cleanupToken;this.pendingCommand=command;this.phase='cancelling';this.revoke();this.emit();
      const r=await this.transport.command(command,this.owner.session);
      if(r?.transport&&r.sent===false){this.phase='cleanup-required';this.pendingCommand=null;this.reason='取消尚未送出，沒有待查回執；連線恢復後請取消這一個候選。';throw Object.assign(fail('PF6_NOT_SENT',this.reason),{transport:true,sent:false});} // PF6_APP_CANCEL_UNSENT_IS_NOT_UNKNOWN
      if(r?.transport){this.phase='unknown';this.reason='取消結果待查；只核對原回執。';throw Object.assign(fail('PF6_UNKNOWN',this.reason),{transport:true,command});}
      if(!r?.ok){this.phase='cleanup-required';this.pendingCommand=null;throw fail(r?.code||'PF6_CANCEL',r?.error||'尚未核對取消結果。');}
      this.cleanupToken=null;this.pendingCommand=null;this.phase='suggested';return r;
    }
    async cancel(){
      if(['confirming','unknown','cancelling'].includes(this.phase))throw fail('PF6_PENDING','確認或取消結果待查；必須先核對原回執。');
      this.cancelRequested=true;this.revoke();
      if(this.operation){await this.operation;if(this.phase==='unknown')throw fail('PF6_PENDING','原結果仍待查。');}
      if(this.cleanupToken!==null)await this.cancelToken();this.release();this.suggestions=null;this.selected=[];this.phase='cancelled';this.reason='本次建議已取消；正式專案與歷史保持不變。';this.emit();return {ok:true,history_changed:false};
    }
    async confirm(){
      if(!['confirmable','confirm-not-sent'].includes(this.phase)||!this.candidate)throw fail('PF6_NOT_CONFIRMABLE','沒有本次可確認的候選。');this.assertCurrent();if(!this.confirmable)throw fail('PF6_NOT_CONFIRMABLE','候選無效或投影不完整，不可確認。');
      const command='pf6-confirm '+token(this.candidate.token);this.host.assertTimberPreview(this.lease,this.candidate.token);this.pendingCommand=command;this.phase='confirming';this.reason='確認已送出，正在核對原回執。';this.emit();
      const r=await this.transport.command(command,this.owner.session);
      if(r?.transport&&r.sent===false){this.phase='confirm-not-sent';this.pendingCommand=null;this.reason='確認尚未送出，沒有待查回執；連線恢復並核對來源後，可再按確認或取消。';this.emit();return r;} // PF6_APP_CONFIRM_UNSENT_IS_NOT_UNKNOWN
      if(r?.transport){this.phase='unknown';this.reason='確認結果待查；禁止重送或宣稱取消成功。';this.emit();return r;}
      this.finishConfirmation(r);return r;
    }
    finishConfirmation(r){
      this.committedDefinitions=r?.ok?clone(this.candidate?.createdDefinitions||[]):[]; // PF6_APP_CONFIRM_RECEIPT_KEYS
      this.receipt=clone(r);
      // cmd_pf6_confirm 只有這三種失敗會明確銷毀候選。版本守門、封存回執等拒絕都不算取消。
      if(!r.ok&&this.cleanupToken!==null&&!['EXPIRED','INVALID','CAPACITY'].includes(r.code)){
        this.revoke();this.pendingCommand=null;this.phase='cleanup-required';
        this.reason=(r.error||'確認遭拒。')+' 請取消原候選，不會重送確認。';
      }else{
        this.release();this.phase=r.ok?'committed':'rejected';
        this.reason=r.ok?'已整筆確認為普通角材；一次復原／重做恢復整包。':r.error||'確認遭拒，沒有提交本次候選。';
      }
      this.emit();
    }
    settleRecovered(command,result,originSession){
      if(this.phase!=='unknown'||command!==this.pendingCommand||originSession!==this.owner.session)return false; // PF6_APP_RECEIPT_CURRENT_SESSION
      if(command.startsWith('pf6-confirm ')){this.finishConfirmation(result);return true;}
      if(command.startsWith('pf6-cancel ')){if(result?.ok){this.release();this.phase='cancelled';this.reason='原取消回執已核對，沒有重新送出。';}else{this.phase='cleanup-required';this.pendingCommand=null;this.reason=result?.error||'原取消未成功，仍須處理候選。';}this.emit();return true;}
      return false;
    }
    async settlePreviewReceipt(command,result,originSession){
      if(this.phase!=='unknown'||command!==this.pendingCommand||originSession!==this.owner.session||!/^pf6-(suggest|select) /.test(command))return false;
      if(command.startsWith('pf6-select ')&&result?.ok)this.cleanupToken=token(result.preview?.token);
      if(this.cleanupToken!==null)await this.cancelToken();this.release();this.phase='cancelled';this.reason='原預覽回執已核對並清理；請重新明選，沒有復活舊候選。';this.emit();return true;
    }
    invalidate(reason='幾何來源已變更，舊候選不能確認。'){this.reason=reason;const confirming=this.phase==='confirming'||this.phase==='unknown'&&this.pendingCommand?.startsWith('pf6-confirm ');if(this.lease&&!confirming)this.host.clearTimberPreviewToken(this.lease);if(!this.busy&&this.phase!=='cleanup-required')this.phase='stale';this.emit();} // PF6_APP_CONFIRM_DISCONNECT_KEEPS_RECEIPT
    retire(){this.retired=true;this.invalidate('原面或專案已退出；候選已退役，只核對既有回執。');}
  }
  return Object.freeze({Session,uint64,token,validateInput,validateView,validateEntries,source});
});
