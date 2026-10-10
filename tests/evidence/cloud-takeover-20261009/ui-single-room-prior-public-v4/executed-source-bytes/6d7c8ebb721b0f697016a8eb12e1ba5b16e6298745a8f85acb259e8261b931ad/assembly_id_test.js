/* P77 identity regression: API prepares real native fixtures only. Creation,
 * copy, edit, preview, publish and recovery use trusted browser controls. */
'use strict';
module.exports=async({send,read,sleep,ctl,fill,choose,publish,wait,check})=>{
 const fs=require('fs'),path=require('path'),os=require('os'),same=require('node:util').isDeepStrictEqual,MAX=4294967295;
 const rule=id=>({id,version:1,name:'配號規則 '+id,slots:[{id:1,name:'主支'},{id:2,name:'副支'}],members:[{id:1,slotId:1},{id:2,slotId:2}],joints:[{id:1,kind:'end-to-side',scope:'one',targetMember:1,terminatedMember:2,end:'start',side:'+u',dir:'u'}]});
 const binding=(id,name='原配置 '+id)=>({id,name,rule:{id:1,version:1},slots:[1,2].map(slotId=>({slotId,A:{kind:'literal',value:27},B:{kind:'literal',value:33},contactFace:'A',orientation:'B'}))});
 const apply=operations=>read(`(async()=>{const state=await apiRequest('assembly-read');const response=await fetch('/assembly/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'assembly-transaction/1',expectedRevision:state.revision,operations:${JSON.stringify(operations)}})});const result=await response.json();if(!response.ok||!result.ok||!result.preview.valid)throw Error('Identity fixture rejected: '+JSON.stringify(result));const done=await api('assembly-confirm '+result.preview.token);if(!done.ok)throw Error(JSON.stringify(done));await renderObjects();})()`);
 const reset=()=>read(`(async()=>{AssemblyWorkspace.close();await api('reset');await renderObjects();})()`);
 const draft=(id,kind,data,intent)=>({id,kind,base_ref:null,data,updated_at:'2026-10-02T00:00:00Z',...(intent?{binding_intent:intent}:{})});
 const addDraft=value=>read(`ReferenceWorkspace.setAssemblyDraft(${JSON.stringify(value)},ReferenceWorkspace.getProjectState().contextToken);void 0`);
 const drafts=()=>read(`ReferenceWorkspace.getAssemblyDrafts()`);
 const state=()=>read(`apiRequest('assembly-read').then(r=>r.state)`);
 const open=async()=>{await ctl('#btnNewAssembly');await wait(`AssemblyWorkspace.isOpen`);};
 const reopen=async()=>{await ctl('#asmClose');await read(`(async()=>{const bytes=await ReferenceWorkspace.exportBytes();await ReferenceWorkspace.importBytes(bytes,'配號驗收.gcanvas');await renderObjects();})()`);await open();};
 const refused=async(label,expected)=>{
   const before=await state(),saved=await drafts();await ctl('#asmPreview');
   await wait(`$('asmStatus')?.classList.contains('asm-error')`);
   check(label,same(await state(),before)&&same(await drafts(),saved)&&await read(`$('asmConfirm').hidden||$('asmConfirm').disabled`));
   if(expected)check(label+'：錯誤明確',await read(`new RegExp(${JSON.stringify(expected)}).test($('asmStatus').textContent)`));
 };
 console.log('=== P77 A15 uint32 與草稿配號、A23 空白手機流程 ===');
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});

 // Native max wraps to 1; draft 1 is reserved and live 2 must also be skipped.
 await reset();await apply([{op:'publish-rule',value:rule(1)},{op:'put-binding',value:binding(2)},{op:'put-binding',value:binding(MAX)}]);
 await addDraft(draft('reserved-binding-one','binding',binding(1,'保留草稿一'),{mode:'create'}));
 check('A15 fixture 原生 MAX 回繞1且2仍是既有配置',await read(`apiRequest('newid').then(r=>r.assemblyBinding===1)`));
 await open();await ctl('[data-asm-rule="1:1"]');await ctl('#asmBind');await fill('#asmName','真正新增配置三');
 const create=(await drafts()).find(d=>d.data.name==='真正新增配置三');
 check('A15 真新增跳過草稿1與原生2取得3',create.data.id===3&&create.binding_intent?.mode==='create');
 await reopen();await ctl(`[data-asm-draft="${create.id}"]`);
 check('A15 新建意圖與保留草稿跨專案封包重開不失',same((await drafts()).find(d=>d.id===create.id),create)&&(await drafts()).some(d=>d.id==='reserved-binding-one'));
 await publish();let after=await state();
 check('A15 發布新增3不覆寫原生2或MAX',same(after.bindings.find(b=>b.value.id===2).value,binding(2))&&same(after.bindings.find(b=>b.value.id===MAX).value,binding(MAX))&&after.bindings.some(b=>b.value.id===3&&b.value.name==='真正新增配置三')&&after.bindings.length===3);
 await ctl('[data-asm-binding="2"]');await ctl('#asmEdit');await fill('#asmName','明確編輯配置二');
 const edit=(await drafts()).find(d=>d.data.name==='明確編輯配置二');
 check('A15 真編輯保留2與精確原來源快照',edit.data.id===2&&edit.binding_intent?.mode==='update'&&same(edit.binding_intent.source,binding(2)));
 await reopen();await ctl(`[data-asm-draft="${edit.id}"]`);await publish();after=await state();
 check('A15 保存重開後真正編輯仍只更新2',after.bindings.length===3&&after.bindings.find(b=>b.value.id===2).value.name==='明確編輯配置二'&&after.bindings.find(b=>b.value.id===3).value.name==='真正新增配置三');

 // A live object appearing after draft creation may not silently turn create into edit.
 await ctl('[data-asm-rule="1:1"]');await ctl('#asmBind');await fill('#asmName','後到碰撞新配置');
 const staleCreate=(await drafts()).find(d=>d.data.name==='後到碰撞新配置'),intruder=binding(staleCreate.data.id,'另一個來源已用此號');
 await apply([{op:'put-binding',value:intruder}]);await refused('A15 新建後號碼被占用拒絕而不吞草稿');
 await reopen();await ctl(`[data-asm-draft="${staleCreate.id}"]`);await refused('A15 碰撞草稿重開仍拒絕更新別人配置');await ctl('#asmDeleteDraft');
 await addDraft(draft('legacy-collision','binding',binding(2,'無意圖舊草稿')));await ctl('[data-asm-draft="legacy-collision"]');await refused('A15 舊格式無意圖草稿不得冒充既有配置編輯');await ctl('#asmDeleteDraft');
 await ctl('[data-asm-binding="2"]');await ctl('#asmEdit');await fill('#asmName','過期編輯不准復蓋');
 const replacement=binding(2,'刪除後同號新來源');await apply([{op:'delete-binding',id:2},{op:'put-binding',value:replacement}]);
 await refused('A15 編輯来源被刪除重建後拒絕覆寫新來源');await ctl('#asmDeleteDraft');

 // Rule creation/copy must use the same occupied+reserved union as bindings.
 await reset();await apply([{op:'publish-rule',value:rule(2)},{op:'publish-rule',value:rule(MAX)}]);
 await addDraft(draft('reserved-rule-one','rule',rule(1)));await open();await ctl('[data-asm-rule="2:1"]');await ctl('#asmCopy');await fill('#asmName','真正複製規則三');
 const copy=(await drafts()).find(d=>d.data.name==='真正複製規則三');check('A15 真複製跳過原生及草稿取得規則3',copy.data.id===3&&copy.data.version===1);await publish();
 check('A15 複製發布保留原有2與MAX且未吞草稿1',(await state()).rules.length===3&&(await drafts()).some(d=>d.id==='reserved-rule-one'));
 await ctl('#asmNewRule');await fill('#asmName','空白新規則四');check('A15 真空白新增使用未占用規則4',(await drafts()).some(d=>d.data.name==='空白新規則四'&&d.data.id===4));await ctl('#asmDeleteDraft');

 // A23: every authoring step starts empty at 390px, not a desktop fixture.
 await reset();await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await open();await ctl('#asmNewRule');await fill('#asmName','手機從空白建立');
 await ctl('#asmAddSlot');await fill('#asmSlot1','手機主支');await ctl('#asmAddMember');await ctl('#asmAddSlot');await fill('#asmSlot2','手機副支');await ctl('#asmAddMember');await ctl('#asmAddJoint');
 await fill('#asmScope1','手機左接合');await choose('#asmSide1','-v');await choose('#asmDir1','v');
 const mobileDraft=(await drafts()).find(d=>d.data.name==='手機從空白建立');
 const expected={id:1,version:1,name:'手機從空白建立',slots:[{id:1,name:'手機主支'},{id:2,name:'手機副支'}],members:[{id:1,slotId:1},{id:2,slotId:2}],joints:[{id:1,kind:'end-to-side',scope:'手機左接合',terminatedMember:2,targetMember:1,end:'start',side:'-v',dir:'v'}]};
 check('A23 390px 空白建立完整規則的精確來源',same(mobileDraft.data,expected));
 check('A23 390px 從空白新增全流程無橫向溢出',await read(`innerWidth===390&&document.documentElement.scrollWidth<=innerWidth&&$('assemblyWorkspace').scrollWidth<=innerWidth`));
 await reopen();await ctl(`[data-asm-draft="${mobileDraft.id}"]`);check('A23 未發布手機草稿真正保存重開仍可編輯',same((await drafts()).find(d=>d.id===mobileDraft.id).data,expected)&&await read(`$('asmName').value==='手機從空白建立'&&$('asmSide1').value==='-v'`));await publish();
 check('A23 手機發布資料由原生核心讀回完全一致',same((await state()).rules[0].value,expected));
 await ctl('[data-asm-rule="1:1"]');fs.writeFileSync(path.join(os.tmpdir(),'geometry-tests','assembly-blank-390.png'),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'));
 await reopen();check('A23 手機已發布規則再重開仍保留身分接合與來源',same((await state()).rules[0].value,expected)&&(await drafts()).length===0);await ctl('#asmClose');
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
};
