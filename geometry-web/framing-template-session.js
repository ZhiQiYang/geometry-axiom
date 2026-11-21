/* R03 host transaction owner. Native owns generation, checking and World writes. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./framing-recipes.js'):root.GeometryFramingRecipes);if(typeof module==='object'&&module.exports)module.exports=api;else root.GeometryFramingSession=api;})(typeof globalThis!=='undefined'?globalThis:this,F=>{
  'use strict';
  const clone=v=>JSON.parse(JSON.stringify(v));
  const canonical=v=>Array.isArray(v)?'['+v.map(canonical).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}':JSON.stringify(v);
  const same=(a,b)=>canonical(a)===canonical(b);
  const DEFINITION_CHAIN=['finish-surface','panel-fill','derived-placement','from-fill','guide','timber','place'];
  const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
  const fail=(code,message)=>Object.assign(new Error(code+'：'+message),{code});
  class Session {
    constructor({host,transport,boundaryId}){this.host=host;this.transport=transport;this.boundaryId=boundaryId;this.phase='idle';this.reason='先保存配方，再明選本次來源並預覽。';this.collection=F.empty();this.currentRecipe=null;this.selectedSource=null;this.readResult=null;this.candidate=null;this.ownerKey=null;this.lease=null;this.pendingCommand=null;this.retired=false;this.owner=this.stamp();}
    get recipes(){return clone(this.collection.recipes);}
    get pending(){return !!this.lease||['reading','previewing','confirmable','confirming','cancelling','unknown'].includes(this.phase);}
    stamp(){const p=this.host.getProjectState(),e=this.host.getEvidenceState();return {contextToken:p.contextToken,revision:p.revision,session:e.session};}
    current(){return !this.retired&&same(this.owner,this.stamp());}
    assertCurrent(){if(!this.current())throw fail('FT_STALE','面、專案、工作階段或來源已變更，請重新選取；舊候選不能確認。');}
    assertIdle(){if(this.pending)throw fail('FT_PENDING','請先確認或取消候選；結果未明時只能核對原回執。');}
    restore(){
      this.assertIdle();const value=this.host.readFeatureAttachment(F.KIND)||F.empty();F.validate(value);
      this.collection=clone(value); // FT_H11_COLD_OPEN_NO_SEARCH: restoration has no native request.
      this.currentRecipe=null;this.selectedSource=null;this.readResult=null;this.owner=this.stamp();this.phase='idle';return this.recipes;
    }
    select(id){this.assertIdle();this.assertCurrent();const r=this.collection.recipes.find(r=>r.id===id);if(!r)throw fail('FT_RECIPE_MISSING','請選現有配方。');this.currentRecipe=clone(r);this.selectedSource=null;return clone(r);}
    save(recipe){
      this.assertIdle();this.assertCurrent();this.host.assertEditable();const next=F.upsert(this.collection,recipe);
      this.host.setFeatureAttachment(F.KIND,next,this.owner.contextToken);
      this.collection=clone(next);this.currentRecipe=clone(recipe);this.owner=this.stamp();this.selectedSource=null;this.phase='ready';this.reason='配方已保存為一筆專案紀錄，尚未新增骨架。';return clone(recipe);
    }
    remove(id){this.assertIdle();this.assertCurrent();this.host.assertEditable();const next=F.remove(this.collection,id);this.host.setFeatureAttachment(F.KIND,next,this.owner.contextToken);this.collection=clone(next);this.currentRecipe=null;this.selectedSource=null;this.owner=this.stamp();this.reason='配方已刪除；既有正式物件保持不變。';}
    validateRead(r){
      return r?.ok===true&&r.schema==='framing-template-read-result/1'&&typeof r.revision==='string'&&/^(0|[1-9]\d{0,19})$/.test(r.revision)&&hash(r.contextKey)&&hash(r.definitionFingerprint)&&r.source?.boundaryId===this.boundaryId&&Array.isArray(r.source.outer)&&r.source.outer.length===4&&r.source.outer.every(p=>Array.isArray(p)&&p.length===2&&p.every(Number.isSafeInteger))&&r.source.holes===0&&Array.isArray(r.source.placements)&&r.source.placements.every(p=>Number.isSafeInteger(p.id)&&p.id>=0&&p.frame&&Array.isArray(p.frame.origin)&&p.frame.origin.length===3&&p.frame.origin.every(Number.isSafeInteger)&&['+x','-x','+y','-y','+z','-z'].includes(p.frame.u)&&['+x','-x','+y','-y','+z','-z'].includes(p.frame.v))&&same({id:r.generator?.id,version:r.generator?.version,policyFingerprint:r.generator?.policyFingerprint},F.TEMPLATE)&&r.generator.scope==='rectangle-common-policy'&&same(r.generator.defaults,F.DEFAULTS)&&Array.isArray(r.sources?.panels)&&Array.isArray(r.sources?.parameters);
    }
    async open(){
      this.assertIdle();this.restore();this.host.assertEditable();this.phase='reading';this.reason='正在讀取本次封閉面與可明選框架。';
      try{const r=await this.transport.post('/framing-template/read',{schema:'framing-template-read/1',boundaryId:this.boundaryId});this.assertCurrent();if(!this.validateRead(r))throw fail(r?.code||'FT_READ_CONTRACT',r?.error||'來源或不可變模板契約不完整；未提供生成動作。');this.readResult=clone(r);this.phase='ready';this.reason='矩形第一片：先保存配方，再明選本次框架與材料語意。';return clone(r);}
      catch(error){this.phase=error.code==='FT_STALE'?'stale':'rejected';this.reason=error.message;throw error;}
    }
    selectSource(on,material,sources){
      this.assertIdle();this.assertCurrent();if(!this.readResult?.source.placements.some(p=>p.id===on))throw fail('FT_SOURCE_REQUIRED','請明選這個面目前的放置框架；保存的提示不會自動綁定。');
      if(!same(material,{boundary:'rc',timber:'literal'}))throw fail('FT_MATERIAL_REQUIRED','請明示 RC 邊界與本配方整數角材尺寸。');
      const panel=this.readResult.sources.panels.map(p=>p.value||p).find(p=>p.id===sources?.panel?.id&&p.version===sources?.panel?.version&&p.kind==='panel');
      const card=this.readResult.sources.parameters.find(p=>p.id===sources?.threshold?.parameterId),field=card?.fields?.find(f=>f.id===sources?.threshold?.fieldId&&f.type==='dimension');
      if(!panel||!field)throw fail('FT_ENGINEERING_SOURCE_REQUIRED','請明選固定板材版本與承接門檻 X 的 dimension 欄位；不會代入隱藏常數。');
      this.selectedSource={on,material:clone(material),sources:{panel:{id:panel.id,version:panel.version},threshold:{parameterId:card.id,fieldId:field.id}}};return clone(this.selectedSource);
    }
    payload(){
      this.assertCurrent();F.assertGeneratable(this.currentRecipe);if(!same(this.currentRecipe,this.collection.recipes.find(r=>r.id===this.currentRecipe.id)))throw fail('FT_RECIPE_UNSAVED','請先保存這份配方，再生成。');
      if(!this.readResult||!this.selectedSource)throw fail('FT_SOURCE_REQUIRED','每次生成都要明選目前來源、放置框架與材料語意。');
      const panel=this.readResult.sources.panels.map(p=>p.value||p).find(p=>p.id===this.selectedSource.sources.panel.id&&p.version===this.selectedSource.sources.panel.version);
      if(panel.width!==this.currentRecipe.defaults.panelWidth||panel.length!==this.currentRecipe.defaults.panelLength)throw fail('FT_PANEL_MISMATCH','配方板寬／板長與明選固定板材不同；請明設並保存符合來源的配方，不會自動換尺寸。');
      return {schema:'framing-template-generate/1',expectedRevision:this.readResult.revision,contextKey:this.readResult.contextKey,boundaryId:this.boundaryId,on:this.selectedSource.on,definitionFingerprint:this.readResult.definitionFingerprint,template:clone(this.currentRecipe.template),parameters:clone(this.currentRecipe.defaults),layout:clone(this.currentRecipe.preference),material:clone(this.selectedSource.material),sources:clone(this.selectedSource.sources)};
    }
    validCandidate(r){const p=r?.preview;return r?.ok===true&&hash(r.ownerKey)&&p?.schema==='framing-template-preview/1'&&Number.isInteger(p.token)&&p.token>0&&p.token<=4294967295&&p.valid===true&&p.revision===this.readResult?.revision&&Array.isArray(p.members)&&p.members.length>0&&p.members.every(m=>m&&typeof m.kind==='string'&&typeof m.role==='string'&&Array.isArray(m.rect)&&m.rect.length===4&&m.rect.every(Number.isSafeInteger)&&m.rect[0]<m.rect[2]&&m.rect[1]<m.rect[3]&&Number.isSafeInteger(m.length)&&m.length>0&&Number.isSafeInteger(m.A)&&m.A>0&&Number.isSafeInteger(m.B)&&m.B>0)&&Array.isArray(p.seams?.u)&&Array.isArray(p.seams?.v)&&Array.isArray(p.marks)&&same(p.definitionChain,DEFINITION_CHAIN)&&same(p.sources,this.selectedSource?.sources)&&p.supportComplete===true&&Array.isArray(p.support)&&p.support.every(s=>['u','v'].includes(s.axis)&&typeof s.k==='string'&&/^-?(0|[1-9]\d*)$/.test(s.k)&&Array.isArray(s.range)&&s.range.length===2&&s.range.every(Number.isSafeInteger)&&s.range[0]<s.range[1]&&Number.isSafeInteger(s.left)&&s.left>=0&&Number.isSafeInteger(s.right)&&s.right>=0&&s.supported===true);}
    release(){this.host.finishTimberPreview(this.lease);this.lease=null;this.candidate=null;this.ownerKey=null;this.pendingCommand=null;}
    async preview(){
      this.assertIdle();const payload=this.payload();this.lease=this.host.beginTimberPreview();this.phase='previewing';this.reason='正在生成並核對整組候選；尚未寫入。';
      try{
        const r=await this.transport.post('/framing-template/preview',payload);
        if(!r?.ok){this.release();this.phase='rejected';throw fail(r?.code||'FT_PREVIEW_REJECTED',r?.error||'完整候選未通過，場景保持原狀。');}
        if(!this.validCandidate(r)){
          if(Number.isInteger(r.preview?.token)&&r.preview.token>0&&hash(r.ownerKey)){this.candidate={token:r.preview.token};this.ownerKey=r.ownerKey;this.phase='confirmable';await this.cancel();}
          else this.release();
          this.phase='rejected';throw fail('FT_PREVIEW_CONTRACT','候選資料不完整，沒有可確認的骨架。');
        }
        this.candidate=clone(r.preview);this.ownerKey=r.ownerKey;this.phase='confirmable';
        if(!this.current()){await this.cancel();this.phase='stale';throw fail('FT_STALE','晚到的候選已取消；來源變更後須重新選取。');}
        this.host.bindTimberPreview(this.lease,this.candidate.token);this.phase='confirmable';this.reason='整組候選已通過原生驗證；確認才寫入一筆歷史。';return clone(r.preview);
      }catch(error){if(error.transport){this.phase='unknown';this.pendingCommand=error.command||null;}else if(this.phase==='previewing'){this.release();this.phase=error.code==='FT_STALE'?'stale':'rejected';}this.reason=error.message;throw error;}
    }
    async cancel(){
      if(['confirming','previewing','unknown'].includes(this.phase))throw fail('FT_PENDING','結果尚未確認；請先核對原回執，不能重送或取消未知候選。');
      if(!this.candidate){this.release();this.phase='ready';this.reason='已取消本次輸入，沒有新增物件或歷史。';return {ok:true,history_changed:false};}
      if(this.owner.session!==this.stamp().session)throw fail('FT_STALE','服務工作階段已改變，不會把舊 token 傳給別的工作。');
      const command=`framing-template-cancel ${this.candidate.token} ${this.ownerKey}`;
      this.phase='cancelling';this.pendingCommand=command;
      const result=await this.transport.command(command); // FT_H10_CANCEL_NO_WRITE: cancel never confirms.
      if(result.transport){this.phase='unknown';this.reason='取消結果未明；重新連線只查原回執，不重送。';return result;}
      if(!result.ok){this.phase='confirmable';this.pendingCommand=null;throw fail(result.code||'FT_CANCEL_REJECTED',result.error||'取消遭拒，候選仍待核對。');}
      this.release();this.phase='ready';this.reason='本次生成已取消，配方與場景保持取消前原狀。';return result;
    }
    async confirm(){
      if(this.phase!=='confirmable'||!this.candidate)throw fail('FT_NOT_CONFIRMABLE','沒有可確認的本次候選。');
      this.assertCurrent();this.host.assertTimberPreview(this.lease,this.candidate.token);
      const command=`framing-template-confirm ${this.candidate.token} ${this.ownerKey}`;this.pendingCommand=command;this.phase='confirming';
      const result=await this.transport.command(command);
      if(result.transport){this.phase='unknown';this.reason='確認結果未明；重新連線只查原回執，禁止重送。';return result;}
      this.finishConfirmation(result);return result;
    }
    finishConfirmation(result){this.release();this.phase=result.ok?'committed':'rejected';this.reason=result.ok?'骨架已整筆確認為一般正式物件；配方不擁有物件，冷開不重新搜尋。':result.error||'確認遭拒，沒有提交本次骨架。';if(result.ok){this.owner=this.stamp();this.selectedSource=null;this.readResult=null;}}
    settleRecovered(command,result){
      if(this.phase!=='unknown'||command!==this.pendingCommand)return false;
      if(command.startsWith('framing-template-confirm ')){this.finishConfirmation(result);return true;}
      if(command.startsWith('framing-template-cancel ')){if(result.ok){this.release();this.phase='ready';this.reason='已核對原取消回執，沒有新增骨架。';}else{this.phase='confirmable';this.reason=result.error||'原取消未成功，候選仍待處理。';this.pendingCommand=null;}return true;}
      return false;
    }
    async settlePreviewReceipt(command,result){
      if(this.phase!=='unknown'||this.pendingCommand!==command||!command.startsWith('framing-template-preview '))return false;
      if(result?.ok&&Number.isInteger(result.preview?.token)&&result.preview.token>0&&hash(result.ownerKey)){
        this.candidate={token:result.preview.token};this.ownerKey=result.ownerKey;this.phase='confirmable';await this.cancel();
        if(this.phase!=='unknown'){this.phase='stale';this.reason='已核對並取消先前未知的預覽；請重新選取來源。';}
      }else{this.release();this.phase='rejected';this.reason=result?.error||'已核對原預覽未成功，未寫入場景。';}
      return true;
    }
    invalidate(reason='來源已變更，舊候選不得確認。'){this.reason=reason;if(['confirming','cancelling','unknown','previewing'].includes(this.phase))return;this.phase=this.candidate?'stale':'rejected';if(!this.candidate)this.readResult=null;this.selectedSource=null;}
    retire(){this.retired=true;this.invalidate('專案或面已切換，舊候選不可確認。');}
  }
  return Object.freeze({Session,DEFINITION_CHAIN:Object.freeze(DEFINITION_CHAIN)});
});
