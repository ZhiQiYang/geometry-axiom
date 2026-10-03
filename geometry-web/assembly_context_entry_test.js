/* P82: real app/native context entry. Positive fixtures use existing published
 * rule content and actual native transactions; metadata faults are negatives.
 * Run only through the parent's isolated CDP harness, not as a standalone app. */
'use strict';
const cdp=require('./cdp_helpers.js'),same=require('node:util').isDeepStrictEqual;
module.exports=async({send,eval_,sleep,click,waitForUI,exceptionCount})=>{
  console.log('=== P82 單選固定規則建立材料配置 ===');
  const read=cdp.makeRead(eval_),wait=cdp.makeWait(waitForUI,20000),errors=exceptionCount();
  const check=cdp.makeCheck({prefix:'P82 ',throwOnFail:true}),key=cdp.makeKey({send,sleep});
  const rawCtl=cdp.makeCtl({eval_:read,sleep,click},{scroll:'center',attempts:3,pollMs:100,settleMs:100,
    before:cdp.openCreateObjectMenu(read,selector=>ctl(selector))});
  const ctl=async selector=>{await wait(`!!document.querySelector(${JSON.stringify(selector)})`);return rawCtl(selector);};
  const fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:80});
  const shot=cdp.makeShot(send,['GEOMETRY_ASSEMBLY_CONTEXT_SCREENSHOTS']);
  const card=(kind,id)=>`.ocard[data-kind="${kind}"][data-id="${id}"]`;
  const snapshot=()=>read(`(async()=>({dump:(await __p82.originalApi('dump')).text,project:ReferenceWorkspace.getProjectState(),drafts:ReferenceWorkspace.getAssemblyDrafts(),undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length}))()`);
  const selectCard=async(kind,id)=>{
    await read(`(()=>{resetSceneFocus();oc.search='';drawObjects();centerOnNode(${JSON.stringify(kind)},${id});closePanels();void 0;})()`);
    await sleep(480); // Keep a new single selection distinct from a prior double click.
    await ctl(card(kind,id)+' > text');
    await wait(`oc.selection.length===1&&oc.sel?.kind===${JSON.stringify(kind)}&&oc.sel.id===${id}&&!AssemblyWorkspace.isOpen`);
    if(await read(`innerWidth<=900`))await read(`openPanel('right',$('toggleRight'));void 0`);
    await wait(`!!$('asmInspectorOpen')`);
  };
  const draftFor=id=>read(`ReferenceWorkspace.getAssemblyDrafts().find(d=>d.kind==='binding'&&d.data.rule.id===${id})`);
  const publish=async()=>{await ctl('#asmPreview');await wait(`$('asmConfirm')&&!$('asmConfirm').disabled`);await ctl('#asmConfirm');await wait(`$('asmStatus')?.textContent.includes('已套用')`);};
  const restore=()=>read(`(()=>{if(window.__p82){apiRequest=__p82.originalApi;__p82.gate?.release();}void 0;})()`);
  const clearToast=()=>read(`$('toastRegion').replaceChildren();void 0`);
  const fault=async mode=>read(`(()=>{const mode=${JSON.stringify(mode)};apiRequest=async(command,...args)=>{const result=await __p82.originalApi(command,...args);if(command!=='assembly-read')return result;const copy=structuredClone(result);if(mode==='unknown')delete copy.state.capabilities;else copy.state.capabilities=mode==='generation'?['assembly-timber-generation/1']:[];return copy;};void 0;})()`);
  const hold=async command=>read(`(()=>{const g=__p82.gate={held:false,finished:false,calls:0,active:0};const gate=new Promise(resolve=>g.release=resolve);apiRequest=async(command,...args)=>{g.active++;try{const result=await __p82.originalApi(command,...args);if(command===${JSON.stringify(command)}){g.calls++;if(!g.held){g.held=true;await gate;g.finished=true;}}return result;}finally{g.active--;}};void 0;})()`);
  const release=async()=>{await read(`__p82.gate.release();void 0`);await wait(`__p82.gate.finished&&__p82.gate.active===0`);await restore();};
  try{
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
    await wait(`window.ContextOperations&&window.AssemblyWorkspace?.createBindingFromRule&&connection.phase==='ready'`);
    await read(`(async()=>{AssemblyWorkspace.close();ParameterUI.discard();InfiniteGridWorkspace.close(true);resetSceneFocus();await setView3(false);const response=await fetch('/examples/assembly-generation-v1.gcanvas');if(!response.ok)throw Error('P82 fixture unavailable');await ReferenceWorkspace.importBytes(new Uint8Array(await response.arrayBuffer()),'P82-synthetic.gcanvas');
      window.__p82={originalApi:apiRequest};__p82.tx=async operations=>{const r=await __p82.originalApi('assembly-read');if(!r.ok)throw Error(JSON.stringify(r));const p=await(await fetch('/assembly/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'assembly-transaction/1',expectedRevision:r.revision,operations})})).json();if(!p.ok||!p.preview?.valid)throw Error(JSON.stringify(p));const c=await __p82.originalApi('assembly-confirm '+p.preview.token);if(!c.ok)throw Error(JSON.stringify(c));};
      const original=(await __p82.originalApi('assembly-read')).state.rules.find(r=>r.value.id===1&&r.value.version===1);if(!original)throw Error('P82 published fixture missing');__p82.originalRule=structuredClone(original.value);
      for(const id of [77,78,79]){const value=structuredClone(__p82.originalRule);value.id=id;value.name='P82 同名來源';await __p82.tx([{op:'publish-rule',value}]);}await renderObjects();__p82.archive=await ReferenceWorkspace.exportBytes();})()`);

    await selectCard('assembly-rule',77);await wait(`!!$('inspectorContent').querySelector('[data-source-inspector]')`);
    check('單選卡片指紋與來源 disclosure 保留，原單一入口換為建立配置',await read(`(async()=>{const o=ocFind('assembly-rule',77),r=(await __p82.originalApi('assembly-read')).state.rules.find(r=>r.value.id===77&&r.value.version===o.version);return $('asmInspectorOpen').textContent==='建立材料配置'&&$('inspectorContent').querySelectorAll('#asmInspectorOpen').length===1&&!!$('inspectorContent').querySelector('[data-source-inspector]')&&o.fingerprint===r.fingerprint&&!!document.querySelector(${JSON.stringify(card('assembly-rule',77)+' .card-enter')});})()`));
    const beforeDesktop=await snapshot();
    // Focus only prepares the keyboard target; Enter is trusted CDP input.
    await read(`$('asmInspectorOpen').focus();void 0`);await key('Enter','Enter',13);await wait(`AssemblyWorkspace.isOpen&&!!$('asmBindingRule')`);
    const created=await draftFor(77),selected=await read(`ocFind('assembly-rule',77)`),afterDesktop=await snapshot();
    check('桌面鍵盤入口只建固定來源草稿，槽位全空且正式 World 不變',created?.base_ref.fingerprint===selected.fingerprint&&created.base_ref.version===selected.version&&created.binding_intent.mode==='create'&&created.data.slots.every(s=>s.A===null&&s.B===null&&s.contactFace===null&&s.orientation===null)&&beforeDesktop.dump===afterDesktop.dump&&afterDesktop.drafts.length===beforeDesktop.drafts.length+1);
    await fill('#asmName','P82 桌面未完成');await shot('context-desktop-form');
    const savedDraft=await draftFor(77);await read(`__p82.draftArchive=await ReferenceWorkspace.exportBytes()`);await ctl('#asmClose');
    await read(`ReferenceWorkspace.importBytes(__p82.draftArchive,'P82-draft-reopen.gcanvas')`);
    check('真 gcanvas 保存重開保留固定 pin 與未完成具型別槽位',same(await draftFor(77),savedDraft));
    await selectCard('assembly-rule',77);
    const origin=await read(`({cx:ocFind('assembly-rule',77).cx,cy:ocFind('assembly-rule',77).cy,zoom:oc.zoom,panX:oc.panX,panY:oc.panY})`);
    await ctl('#btnNewAssembly');await wait(`AssemblyWorkspace.isOpen`);await ctl(`[data-asm-draft="${savedDraft.id}"]`);
    const timbers=await read(`(await __p82.originalApi('objects')).timbers`);await publish();
    const desktopBinding=await read(`(await __p82.originalApi('assembly-read')).state.bindings.find(b=>b.value.id===${savedDraft.data.id})`);
    check('真預覽確認發布合法未完成配置，不暗生角材',desktopBinding?.complete===false&&desktopBinding.value.rule.id===77&&desktopBinding.value.rule.version===savedDraft.base_ref.version&&same(await read(`(await __p82.originalApi('objects')).timbers`),timbers));
    await ctl('#asmClose');
    check('返回畫布保留原選取與卡片位置',await read(`(()=>{const o=ocFind('assembly-rule',77);return oc.sel?.kind==='assembly-rule'&&oc.sel.id===77&&o.cx===${origin.cx}&&o.cy===${origin.cy}&&oc.zoom===${origin.zoom}&&oc.panX===${origin.panX}&&oc.panY===${origin.panY};})()`));
    await selectCard('assembly-binding',desktopBinding.value.id);const legacyLabel=await read(`$('asmInspectorOpen').textContent`);await ctl('#asmInspectorOpen');await wait(`AssemblyWorkspace.isOpen&&!!$('asmEdit')`);const bindingOpen=await read(`$('asmEditor').textContent.includes('P82 桌面未完成')`);await ctl('#asmClose');
    await selectCard('assembly-rule',77);await ctl(card('assembly-rule',77)+' .card-enter');await wait(`AssemblyWorkspace.isOpen&&!!$('asmBind')`);const authoringOpen=await read(`!!$('asmEdit')&&!!$('asmCopy')`);await ctl('#asmClose');
    check('既有配置 open 與規則 authoring 卡片入口都保留',legacyLabel==='開啟組構工作區'&&bindingOpen&&authoringOpen);

    await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await selectCard('assembly-rule',77);await ctl('#asmInspectorOpen');await wait(`AssemblyWorkspace.isOpen&&!!$('asmName')`);await fill('#asmName','P82 手機未完成');
    const mobileDraft=await draftFor(77),mobileUI=await read(`document.documentElement.scrollWidth<=innerWidth+1&&$('assemblyWorkspace').scrollWidth<=innerWidth+1&&[...$('assemblyWorkspace').querySelectorAll('button,input,select')].filter(n=>n.getBoundingClientRect().height).every(n=>n.getBoundingClientRect().height>=44)`);await shot('context-390-form');await publish();
    check('390px 同一 context 表單可操作並真發布未完成固定配置',mobileUI&&await read(`(await __p82.originalApi('assembly-read')).state.bindings.some(b=>b.value.id===${mobileDraft.data.id}&&b.value.rule.id===77&&b.value.rule.version===${mobileDraft.base_ref.version}&&!b.complete)`));await ctl('#asmClose');
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});

    await selectCard('assembly-rule',78);const old78=await read(`(await __p82.originalApi('assembly-read')).state.rules.find(r=>r.value.id===78&&r.value.version===1)`);
    await read(`(async()=>{const value=structuredClone(__p82.originalRule);value.id=78;value.name='P82 同名來源';value.joints[0].side=value.joints[0].side==='+u'?'-u':'+u';await __p82.tx([{op:'delete-rule',id:78,version:1}]);await __p82.tx([{op:'publish-rule',value}]);})()`);
    const changed78=await read(`(await __p82.originalApi('assembly-read')).state.rules.find(r=>r.value.id===78&&r.value.version===1)`),staleBefore=await snapshot();
    let stalePreserved=old78.fingerprint!==changed78.fingerprint&&same(old78.value.slots,changed78.value.slots);
    for(let i=0;i<2;i++){await clearToast();await ctl('#asmInspectorOpen');await wait(`!$('asmInspectorOpen').disabled&&$('toastRegion').textContent.includes('所選固定規則內容已變更')`);stalePreserved&&=same(await snapshot(),staleBefore)&&await read(`!AssemblyWorkspace.isOpen`);}
    check('真同 tuple 換語義後首次與重試均拒絕，不暗採新指紋',stalePreserved);

    await selectCard('assembly-rule',79);await read(`(async()=>{const value=structuredClone(__p82.originalRule);value.id=79;value.version=2;value.name='P82 新版同名';await __p82.tx([{op:'publish-rule',value}]);})()`);await ctl('#asmInspectorOpen');await wait(`AssemblyWorkspace.isOpen&&!!$('asmBindingRule')`);
    const olderDraft=await draftFor(79);
    check('讀取間新增 latest 仍只建立已捕獲的舊固定版本',olderDraft?.base_ref.version===1&&olderDraft.data.rule.version===1&&await read(`$('asmBindingRule').value==='79:1'`));await ctl('#asmClose');

    await selectCard('assembly-rule',77);const capabilityBefore=await snapshot();
    // Explicit metadata-negative injection: actual read, only capability declaration changed.
    await fault('unknown');await clearToast();await ctl('#asmInspectorOpen');await wait(`!$('asmInspectorOpen').disabled&&$('toastRegion').textContent.includes('能力尚未核對')`);
    check('metadata 負例：能力未知獨立拒絕且保留 World 草稿與歷史',same(await snapshot(),capabilityBefore)&&await read(`!AssemblyWorkspace.isOpen`));await restore();
    let knownMissing=true;
    for(const mode of ['missing','generation']){await fault(mode);await clearToast();await ctl('#asmInspectorOpen');await wait(`!$('asmInspectorOpen').disabled&&$('toastRegion').textContent.includes('未提供組構規則編寫能力')`);knownMissing&&=same(await snapshot(),capabilityBefore)&&await read(`!AssemblyWorkspace.isOpen`);await restore();}
    check('metadata 負例：缺 authoring 或只有 generation 都不能替代',knownMissing);

    await selectCard('assembly-rule',77);const selectionBefore=await snapshot();await hold('newid');await ctl('#asmInspectorOpen');await wait(`__p82.gate.held`);await selectCard('assembly-rule',79);await release();
    check('真 newid 遲到且改選後不串入草稿或搶工作區',same(await snapshot(),selectionBefore)&&await read(`!AssemblyWorkspace.isOpen&&oc.sel?.kind==='assembly-rule'&&oc.sel.id===79`));
    await selectCard('assembly-rule',77);await hold('assembly-read');await ctl('#asmInspectorOpen');await wait(`__p82.gate.held`);await read(`ReferenceWorkspace.importBytes(__p82.archive,'P82-context-switch.gcanvas')`);const switched=await snapshot();await release();
    check('真來源回覆遲到且切專案後不污染新專案',same(await snapshot(),switched)&&await read(`!AssemblyWorkspace.isOpen&&!$('projectBar').closest('.workspace-project-header')`));

    await selectCard('assembly-rule',77);const doubleBefore=await snapshot();await hold('newid');
    const point=await read(`(()=>{const r=$('asmInspectorOpen').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
    await click(point.x,point.y);await click(point.x,point.y);await wait(`__p82.gate.held`);await release();await wait(`AssemblyWorkspace.isOpen&&!!$('asmBindingRule')`);
    const doubled=await snapshot(),allocationCalls=await read(`__p82.gate.calls`);
    check('信任連點只配號一次且只建立一份草稿',allocationCalls===1&&doubled.drafts.length===doubleBefore.drafts.length+1&&doubled.dump===doubleBefore.dump);await ctl('#asmClose');

    // Explicit old-service metadata-negative injection: remove only displayed card hash.
    await read(`(()=>{apiRequest=async(command,...args)=>{const result=await __p82.originalApi(command,...args);if(command!=='objects')return result;const copy=structuredClone(result);for(const rule of copy.assemblyRules||[])if(rule.id===77)delete rule.fingerprint;return copy;};void 0;})()`);await read(`renderObjects()`);await selectCard('assembly-rule',77);
    check('metadata 負例：舊卡片缺原生指紋只停用情境入口',await read(`$('asmInspectorOpen').disabled&&$('inspectorContent').textContent.includes('缺少固定來源')&&!!$('inspectorContent').querySelector('[data-source-inspector]')`));await restore();await read(`renderObjects()`);
    check('沒有新增未處理例外且測試來源攔截已移除',exceptionCount()===errors&&await read(`apiRequest===__p82.originalApi`));
  }finally{
    await restore();await read(`AssemblyWorkspace.close();delete window.__p82;void 0`);
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
  }
};
