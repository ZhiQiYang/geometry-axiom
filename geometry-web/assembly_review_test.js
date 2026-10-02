/* P77 regressions: real browser controls and native bridge on an isolated service.
 * Fault injection holds parsed HTTP replies AFTER the real server has processed
 * them. It never suppresses the outbound confirmation request.
 */
'use strict';
module.exports=async({send,read,sleep,click,ctl,fill,choose,publish,wait,key,check})=>{
 const fs=require('fs'),path=require('path'),os=require('os');
 const shot=async name=>fs.writeFileSync(path.join(os.tmpdir(),'geometry-tests',`assembly-review-${name}.png`),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'));
 const literal=value=>({kind:'literal',value});
 const rule={id:1,version:1,name:'回覆測試',slots:[{id:1,name:'主支'},{id:2,name:'副支'}],members:[{id:1,slotId:1},{id:2,slotId:2},{id:3,slotId:2}],joints:[{id:1,kind:'end-to-side',scope:'one',targetMember:1,terminatedMember:2,end:'start',side:'+u',dir:'u'}]};
 const binding={id:1,name:'角材配置',rule:{id:1,version:1},slots:[1,2].map(slotId=>({slotId,A:literal(27),B:literal(33),contactFace:'A',orientation:'B'}))};
 const apply=operations=>read(`(async()=>{const state=await apiRequest('assembly-read');const r=await fetch('/assembly/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'assembly-transaction/1',expectedRevision:state.revision,operations:${JSON.stringify(operations)}})});const data=await r.json();if(!r.ok||!data.ok||!data.preview.valid)throw Error('Fixture preview rejected: '+JSON.stringify(data));const result=await api('assembly-confirm '+data.preview.token);if(!result.ok)throw Error(JSON.stringify(result));await renderObjects();return true;})()`);
 const reset=async()=>{await read(`(async()=>{AssemblyWorkspace.close();await api('reset');await renderObjects();})()`);await apply([{op:'publish-rule',value:rule},{op:'put-binding',value:binding}]);await ctl('#btnNewAssembly');await wait(`AssemblyWorkspace.isOpen`);};
 const edit=async()=>{await ctl('[data-asm-binding="1"]');await ctl('#asmEdit');await wait(`!!$('asmSource1A')`);};
 const preview=async()=>{await ctl('#asmPreview');await wait(`$('asmConfirm')&&!$('asmConfirm').disabled`);};
 const tap=async selector=>{const p=await read(`(()=>{const n=document.querySelector(${JSON.stringify(selector)});n.scrollIntoView({block:'center'});const r=n.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);await click(p.x,p.y);await sleep(100);};
 const hold=mode=>read(`(()=>{const original=window.fetch;window.__asmReply={confirm:0,receipt:0,uploads:0,held:false,mode:${JSON.stringify(mode)}};const gate=new Promise(resolve=>window.__asmReleaseReply=resolve);window.__asmRestoreFetch=()=>{window.fetch=original;};window.fetch=async(...args)=>{const url=String(args[0]),body=url==='/api'?JSON.parse(args[1]?.body||'{}'):{};if(url==='/upload')window.__asmReply.uploads++;if(body.receipt){window.__asmReply.receipt++;if(window.__asmReply.mode==='unknown')throw Error('Injected receipt outage');}const response=await original(...args);if(body.cmd?.startsWith('assembly-confirm ')){window.__asmReply.confirm++;const json=response.json.bind(response);response.json=async()=>{const data=await json();window.__asmReply.serverResult=data;window.__asmReply.held=true;await gate;if(['lost','unknown'].includes(window.__asmReply.mode))throw Error('Injected lost success response');return data;};}return response;};})()`);
 const release=async()=>{await read(`window.__asmReleaseReply();void 0`);};
 const restore=()=>read(`window.__asmRestoreFetch?.();void 0`);

 console.log('=== P77 review #33 #35 #36 #37 ===');
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
 await reset();
 await ctl('[data-asm-rule="1:1"]');await ctl('#asmCopy');await fill('#asmName','保留草稿 B');
 const draftB=await read(`ReferenceWorkspace.getAssemblyDrafts().find(d=>d.data.name==='保留草稿 B')`);
 await ctl('[data-asm-rule="1:1"]');await ctl('#asmEdit');await fill('#asmName','提交草稿 A');
 const draftA=await read(`ReferenceWorkspace.getAssemblyDrafts().find(d=>d.data.name==='提交草稿 A')`);
 await preview();
 const beforeHistory=await read(`ReferenceWorkspace.history.undo.length`);
 await read(`(async()=>{window.__asmBeforeConfirmBytes=await ReferenceWorkspace.exportBytes();})()`);
 await hold('success');await ctl('#asmConfirm');await wait(`window.__asmReply.held`);
 check('成功回覆延遲前服務已實際提交',await read(`window.__asmReply.serverResult.ok&&apiRequest('assembly-read').then(r=>r.state.rules.some(x=>x.value.name==='提交草稿 A'))`));
 await tap(`[data-asm-draft="${draftB.id}"]`);await tap('#asmName');await key('a','KeyA',65,2);await send('Input.insertText',{text:'不得吞掉的輸入'});await tap('#asmConfirm');await tap('#asmClose');await key('Escape','Escape',27);
 check('確認期間明確鎖住改稿切稿關閉與連點',await read(`AssemblyWorkspace.isOpen&&$('asmName').disabled&&$('asmName').value==='提交草稿 A'&&$('asmClose').disabled&&$('asmStatus').textContent.includes('暫停')&&window.__asmReply.confirm===1&&JSON.stringify(ReferenceWorkspace.getAssemblyDrafts().find(d=>d.id===${JSON.stringify(draftB.id)}))===${JSON.stringify(JSON.stringify(draftB))}`));
 const context=await read(`ReferenceWorkspace.getProjectState().contextToken`);
 const rejected=await read(`(async()=>{try{await ReferenceWorkspace.importBytes(window.__asmBeforeConfirmBytes,'確認中不得換專案.gcanvas');return false;}catch(error){return /組構.*確認|確認.*組構/.test(error.message);}})()`);
 check('延遲成功回覆期間換專案在上傳前拒絕',rejected&&await read(`window.__asmReply.uploads===0&&ReferenceWorkspace.getProjectState().contextToken===${JSON.stringify(context)}&&ReferenceWorkspace.history.undo.length===${beforeHistory}`));
 await release();await wait(`$('asmStatus')?.textContent.includes('已套用')`);await restore();
 check('成功僅清理提交草稿且只新增一筆共用歷史',await read(`ReferenceWorkspace.history.undo.length===${beforeHistory+1}&&ReferenceWorkspace.getProjectState().dirty&&!ReferenceWorkspace.getAssemblyDrafts().some(d=>d.id===${JSON.stringify(draftA.id)})&&JSON.stringify(ReferenceWorkspace.getAssemblyDrafts().find(d=>d.id===${JSON.stringify(draftB.id)}))===${JSON.stringify(JSON.stringify(draftB))}`));
 await ctl('#asmClose');await read(`api('line undo')`);check('單步復原原生發布同時恢復兩份草稿',await read(`ReferenceWorkspace.getAssemblyDrafts().some(d=>d.id===${JSON.stringify(draftA.id)})&&apiRequest('assembly-read').then(r=>!r.state.rules.some(x=>x.value.version===2))`));
 await read(`api('line redo')`);check('單步重做只清理原提交草稿',await read(`!ReferenceWorkspace.getAssemblyDrafts().some(d=>d.id===${JSON.stringify(draftA.id)})&&ReferenceWorkspace.getAssemblyDrafts().some(d=>d.id===${JSON.stringify(draftB.id)})&&apiRequest('assembly-read').then(r=>r.state.rules.some(x=>x.value.version===2))`));
 await read(`(async()=>{const bytes=await ReferenceWorkspace.exportBytes();await ReferenceWorkspace.importBytes(bytes,'延遲回覆保存.gcanvas');await renderObjects();})()`);
 check('回覆完成後共用保存重開仍保留 B 精確資料',await read(`JSON.stringify(ReferenceWorkspace.getAssemblyDrafts().find(d=>d.id===${JSON.stringify(draftB.id)}))===${JSON.stringify(JSON.stringify(draftB))}`));
 await ctl('#btnNewAssembly');await ctl(`[data-asm-draft="${draftB.id}"]`);await ctl('#asmDeleteDraft');await ctl('#asmClose');

 // A real native TOKEN rejection is distinct from an uncertain network result.
 await ctl('#btnNewAssembly');await edit();await fill('#asmName','失敗仍保留');
 await read(`(()=>{const original=window.fetch;window.fetch=async(...args)=>{const r=await original(...args);if(String(args[0])==='/assembly/preview'){window.fetch=original;const json=r.json.bind(r);r.json=async()=>{const d=await json();window.__asmRejectedToken=d.preview.token;return d;};}return r;};})()`);
 await preview();await read(`apiRequest('assembly-cancel '+window.__asmRejectedToken)`);
 const failureHistory=await read(`ReferenceWorkspace.history.undo.length`);await hold('success');await ctl('#asmConfirm');await wait(`window.__asmReply.held`);await release();await wait(`!$('assemblyWorkspace').hasAttribute('aria-busy')`);
 check('真核心拒絕不刪草稿不新增歷史且舊 token 不可重送',await read(`!window.__asmReply.serverResult.ok&&window.__asmReply.confirm===1&&ReferenceWorkspace.history.undo.length===${failureHistory}&&ReferenceWorkspace.getAssemblyDrafts().some(d=>d.data.name==='失敗仍保留')&&$('asmConfirm').hidden&&!$('asmClose').disabled`));await restore();await ctl('#asmDeleteDraft');

 await edit();await fill('#asmName','遺失回覆回執恢復');await preview();const receiptHistory=await read(`ReferenceWorkspace.history.undo.length`);
 await hold('lost');await ctl('#asmConfirm');await wait(`window.__asmReply.held`);await release();await wait(`$('asmStatus')?.textContent.includes('已套用')`);
 check('遺失成功回覆由精確回執恢復而非重送確認',await read(`window.__asmReply.confirm===1&&window.__asmReply.receipt===1&&ReferenceWorkspace.history.undo.length===${receiptHistory+1}&&apiRequest('assembly-read').then(r=>r.state.bindings[0].value.name==='遺失回覆回執恢復')`));await restore();

 await edit();await fill('#asmName','未知結果保留草稿');await preview();await hold('unknown');await ctl('#asmConfirm');await wait(`window.__asmReply.held`);await release();await wait(`connection.phase==='error'&&$('asmStatus').textContent.includes('尚未確認')`);
 check('回執也失敗時保留草稿並鎖住編輯',await read(`$('asmName').disabled&&$('asmName').value==='未知結果保留草稿'&&ReferenceWorkspace.getAssemblyDrafts().some(d=>d.data.name==='未知結果保留草稿')&&window.__asmReply.confirm===1`));
 await key('Escape','Escape',27);await wait(`!AssemblyWorkspace.isOpen`);const retryFocused=await read(`document.activeElement===$('connectionRetry')`);await restore();await key('Enter','Enter',13);await wait(`connection.phase==='ready'`);await ctl('#btnNewAssembly');
 check('未知结果只用鍵盤返回重連再開不盲送也不刪草稿',retryFocused&&await read(`window.__asmReply.confirm===1&&ReferenceWorkspace.getAssemblyDrafts().some(d=>d.data.name==='未知結果保留草稿')&&apiRequest('assembly-read').then(r=>r.state.bindings[0].value.name==='未知結果保留草稿')`));
 await ctl(`[data-asm-draft]`);await ctl('#asmDeleteDraft');

 // Actual authoring controls must alter visible SVG coordinates/markers.
 await ctl('[data-asm-rule="1:1"]');await ctl('#asmEdit');await choose('#asmEnd1','start');
 const startDrawing=await read(`$('asmDiagram').querySelector('[data-end="start"]').getAttribute('cx')`);await choose('#asmEnd1','finish');
 check('起終端控制改变接觸處實際圖形位置',startDrawing==='48'&&await read(`$('asmDiagram').querySelector('[data-end="start"]').getAttribute('cx')==='126'&&$('asmDiagram').querySelector('[data-end="finish"]').getAttribute('x')==='43'&&$('asmDiagram').querySelector('figcaption').textContent.includes('終點')`));
 await choose('#asmDir1','u');const uAxis=await read(`$('asmDiagram').querySelector('[data-direction-axis]').getAttribute('x2')`);await choose('#asmDir1','v');
 check('局部 u/v 控制改变實際方向箭頭端點',uAxis==='30'&&await read(`$('asmDiagram').querySelector('[data-direction-axis]').getAttribute('x2')==='0'&&$('asmDiagram').querySelector('[data-direction-axis]').getAttribute('y2')==='30'`));
 for(const side of ['+u','-u','+v','-v']){await choose('#asmSide1',side);check(`圖與表單同步局部側面 ${side}`,await read(`$('asmDiagram').querySelector('[data-contact-end]').dataset.contactSide===${JSON.stringify(side)}&&$('asmDiagram').querySelector('[aria-pressed="true"]').dataset.face===${JSON.stringify(side)}`));}
 await ctl('[data-joint="1"][data-face="+u"]');await read(`document.querySelector('[data-joint="1"][data-face="+v"]').focus();void 0`);await key('Enter','Enter',13);
 check('圖上點選與鍵盤選面同步表單',await read(`$('asmSide1').value==='+v'&&ReferenceWorkspace.getAssemblyDrafts().find(d=>d.data.id===1&&d.data.version===3).data.joints[0].side==='+v'`));
 await choose('#asmKind1','ortho-split');
 check('正交分段分別標明 first.finish 與 second.start',await read(`$('asmDiagram').querySelector('[data-contact-end="finish"]')?.dataset.member==='2'&&$('asmDiagram').querySelector('[data-contact-end="start"]')?.dataset.member==='3'&&$('asmDiagram').querySelector('[data-continuous="true"]')?.dataset.member==='1'`));
 const definition=await read(`JSON.stringify(ReferenceWorkspace.getAssemblyDrafts().find(d=>d.data.id===1&&d.data.version===3).data)`);await ctl('#asmRotate');await ctl('#asmZoomIn');
 check('新增方向及端點圖形旋轉縮放不改固定身分',await read(`JSON.stringify(ReferenceWorkspace.getAssemblyDrafts().find(d=>d.data.id===1&&d.data.version===3).data)===${JSON.stringify(definition)}`));
 await read(`$('asmDiagram').scrollIntoView({block:'center'});void 0`);await shot('glyphs-desktop');
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await ctl('[data-joint="1"][data-face="-u"]');await shot('glyphs-390');
 check('390px 端點方向圖可操作且沒有橫向溢出',await read(`$('asmSide1').value==='-u'&&document.documentElement.scrollWidth<=innerWidth&&$('assemblyWorkspace').scrollWidth<=innerWidth`));
 for(let n=0;n<5;n++)await ctl('#asmZoomIn');await ctl('#asmRotate');await read(`$('asmDiagram').scrollIntoView({block:'center'});void 0`);await shot('glyphs-max-zoom-390');
 check('390px 最大縮放旋轉後選面至少44px且不覆蓋接觸圖',await read(`(()=>{const map=$('asmDiagram').querySelector('[data-contact-map]').getBoundingClientRect();return [...$('asmDiagram').querySelectorAll('[data-face]')].every(n=>{const b=n.getBoundingClientRect();return b.width>=44&&b.height>=44&&b.top>map.bottom;});})()`));
 await publish();check('示意控制結果與真核心讀回一致且不生成角材',await read(`(async()=>{const a=await apiRequest('assembly-read'),o=await apiRequest('objects'),j=a.state.rules.find(x=>x.value.version===3).value.joints[0];return j.dir==='v'&&j.side==='-u'&&j.kind==='ortho-split'&&j.splitMembers.join(',')==='2,3'&&o.timbers.length===0;})()`));
 await ctl('#asmClose');

 // Keep native identities and source values independent in the main summary.
 await apply([{op:'put-parameter',value:{id:7,name:'同名 <i>尺寸</i>',fields:[{id:2,name:'A & "值"',type:'dimension',input:'27'},{id:9,name:'B',type:'dimension',input:'33'}]}},{op:'put-parameter',value:{id:8,name:'同名 <i>尺寸</i>',fields:[{id:2,name:'A & "值"',type:'dimension',input:'27'}]}},...['pine','oak'].flatMap(id=>[1,2].map(version=>({op:'publish-material',value:{id,version,name:'同名木料',kind:'timber',A:27,B:33}}))),{op:'put-binding',value:binding}]);
 await read(`api('line spec review27 27')`);await ctl('#btnNewAssembly');
 const changes=[['A',{kind:'parameter',parameterId:7,fieldId:2},'#7'],['A',{kind:'parameter',parameterId:8,fieldId:2},'#8'],['A',literal(27),'直接數值'],['A',{kind:'spec',name:'review27'},'review27'],['A',{kind:'material',id:'pine',version:1,field:'A'},'#pine'],['A',{kind:'material',id:'oak',version:1,field:'A'},'#oak'],['A',{kind:'material',id:'oak',version:2,field:'A'},'第 2 版'],['B',{kind:'parameter',parameterId:7,fieldId:9},'#9']];
 for(const [index,[axis,source,needle]] of changes.entries()){
   await edit();const worldBefore=await read(`apiRequest('assembly-read').then(r=>JSON.stringify(r.state))`);
   await choose('#asmSource1'+axis,source.kind==='literal'?'literal':JSON.stringify(source));if(source.kind==='literal')await fill('#asmValue1'+axis,source.value);await preview();
   check(`同值換來源 ${index+1} 主摘要顯示型別身分與版本`,await read(`(()=>{const n=$('asmPreviewResult').querySelector('.asm-diff');return n.textContent.includes('主支 ${axis} 來源')&&n.textContent.includes(${JSON.stringify(needle)})&&n.textContent.includes('尺寸仍為 ${axis==='A'?27:33} mm')&&!n.querySelector('i');})()`));
   if(index===0){check('預覽與取消不改真核心且特殊名稱只作文字',await read(`$('asmPreviewResult').textContent.includes('同名 <i>尺寸</i>')&&apiRequest('assembly-read').then(r=>JSON.stringify(r.state)===${JSON.stringify(worldBefore)})`));await shot('sources-390');await ctl('#asmCancel');check('取消換來源仍保留原生直接值',await read(`apiRequest('assembly-read').then(r=>r.state.bindings[0].value.slots[0].A.kind==='literal')`));await preview();}
   if(index===6){await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});await shot('sources-desktop');}
   await ctl('#asmConfirm');await wait(`$('asmStatus')?.textContent.includes('已套用')`);check(`同值換來源 ${index+1} 確認保留精確引用`,await read(`apiRequest('assembly-read').then(r=>JSON.stringify(r.state.bindings[0].value.slots[0][${JSON.stringify(axis)}])===${JSON.stringify(JSON.stringify(source))})`));
 }
 await ctl('#asmClose');await read(`api('line undo')`);check('換來源單步復原還原先前 B 引用',await read(`apiRequest('assembly-read').then(r=>r.state.bindings[0].value.slots[0].B.kind==='literal')`));await read(`api('line redo')`);
 await read(`(async()=>{const bytes=await ReferenceWorkspace.exportBytes();await ReferenceWorkspace.importBytes(bytes,'來源摘要保存.gcanvas');await renderObjects();})()`);
 check('換來源重做保存重開保留固定版本與參數引用',await read(`apiRequest('assembly-read').then(r=>r.state.bindings[0].value.slots[0].A.id==='oak'&&r.state.bindings[0].value.slots[0].A.version===2&&r.state.bindings[0].value.slots[0].B.parameterId===7&&r.state.bindings[0].value.slots[0].B.fieldId===9)`));

 // #37: every zero-ID position plus the ordinary positive-ID control travels
 // through real selection, flush, archive/import, native confirm and recompute.
 await apply([0,1].map(id=>({op:'put-parameter',value:{id,name:'零身分 '+id,fields:[0,1].map(field=>({id:field,name:'尺寸 '+field,type:'dimension',input:'27'}))}})));
 for(const [parameterId,fieldId] of [[0,1],[1,0],[0,0],[1,1]]){
   const source={kind:'parameter',parameterId,fieldId};await ctl('#btnNewAssembly');await edit();await choose('#asmSource1A',JSON.stringify(source));
   check(`ParameterRef ${parameterId}:${fieldId} 實際表單與草稿保留精確 ID`,await read(`$('asmSource1A').value===${JSON.stringify(JSON.stringify(source))}&&ReferenceWorkspace.getAssemblyDrafts().some(d=>JSON.stringify(d.data.slots?.[0]?.A)===${JSON.stringify(JSON.stringify(source))})`));
   await read(`(async()=>{window.__asmZeroBytes=await ReferenceWorkspace.exportBytes();AssemblyWorkspace.close();await api('reset');await ReferenceWorkspace.importBytes(window.__asmZeroBytes,'零 ID 草稿.gcanvas');await renderObjects();})()`);
   await ctl('#btnNewAssembly');await ctl('[data-asm-draft]');check(`ParameterRef ${parameterId}:${fieldId} 新專案重開草稿仍完整`,await read(`$('asmSource1A').value===${JSON.stringify(JSON.stringify(source))}`));await publish();await ctl('#asmClose');
   const parameter=await read(`apiRequest('engineering-read').then(r=>{const c=r.state.parameters.find(c=>c.id===${parameterId});return {id:c.id,name:c.name,fields:c.fields.map(f=>({id:f.id,name:f.name,type:f.type,expression:f.expression}))};})`);const field=parameter.fields.find(f=>f.id===fieldId);delete field.expression;field.input='29';await apply([{op:'put-parameter',value:parameter}]);
   check(`ParameterRef ${parameterId}:${fieldId} 原生確認後仍追隨來源更新`,await read(`apiRequest('assembly-read').then(r=>JSON.stringify(r.state.bindings[0].value.slots[0].A)===${JSON.stringify(JSON.stringify(source))}&&r.state.bindings[0].effective[0].A.value===29)`));
   parameter.fields.find(f=>f.id===fieldId).input='27';await apply([{op:'put-parameter',value:parameter}]);
 }
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
};
