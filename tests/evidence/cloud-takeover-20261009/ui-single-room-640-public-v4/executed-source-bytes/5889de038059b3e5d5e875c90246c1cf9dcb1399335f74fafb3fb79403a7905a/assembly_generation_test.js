/* G09: trusted input in the real work area, real native geometry and archive reopen. */
'use strict';
module.exports=async({send,read,sleep,ctl,fill,choose,publish,wait,check})=>{
 const fs=require('fs'),path=require('path'),os=require('os'),same=require('node:util').isDeepStrictEqual;
 const state=()=>read(`apiRequest('assembly-read').then(r=>r.state)`);
 console.log('=== AR06 G09 組構生成 ===');
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
 await read(`(async()=>{AssemblyWorkspace.close();const r=await fetch('/examples/assembly-generation-v1.gcanvas');if(!r.ok)throw Error('Generation example absent');await ReferenceWorkspace.importBytes(new Uint8Array(await r.arrayBuffer()),'組構生成範例.gcanvas');await renderObjects();})()`);
 await ctl('#btnNewAssembly');await ctl('[data-asm-binding="1"]');await ctl('#asmInstanceDelete1');await wait(`!$('asmConfirm').disabled`);await ctl('#asmConfirm');await wait(`$('asmStatus')?.textContent.includes('已套用')`);
 await ctl('[data-asm-binding="1"]');await ctl('#asmGenerate');await wait(`!!$('asmInstanceSurface')`);await choose('#asmInstanceSurface',1);for(const member of [1,2,3]){await choose('#asmInstanceGuide'+member,member);if(member<3){await choose('#asmInstanceEnd'+member+'start',90);await choose('#asmInstanceEnd'+member+'finish',91);}}
 await ctl('#asmPreview');await wait(`!$('asmConfirm').disabled`);check('G01 真UI從指定來源預覽三支且正式世界未變',(await state()).instances.length===0&&await read(`$('asmPreviewResult').textContent.includes('2960 mm')&&$('asmPreviewResult').textContent.includes('1973 mm')&&$('asmInstanceEnd1start').closest('label').textContent.includes('支撐邊界材一（無序）')&&$('asmInstanceEnd1finish').closest('label').textContent.includes('支撐邊界材二（無序）')`));await ctl('#asmCancel');await publish();
 let original=(await state()).instances[0];const mapping=original.value.mapping;
 check('G01 範例重開為三支原生角材',original.members.map(m=>m.geometry.length).join(',')==='2960,2960,1973');
 await ctl('[data-asm-binding="1"]');await ctl('#asmInstanceEdit1');await wait(`!!$('asmInstanceName')`);await fill('#asmInstanceName','桌面角材來源');
 await ctl('#asmPreview');await wait(`!$('asmConfirm').disabled`);
 check('G02 預覽顯示原生映射與來源且未提交',(await state()).instances[0].value.source.name===original.value.source.name&&await read(`$('asmPreviewResult').textContent.includes('角材 #1')&&$('asmPreviewResult').textContent.includes('1973 mm')&&$('asmPreviewResult').textContent.includes('來源')`));
 await ctl('#asmCancel');check('G02 取消不改來源',same((await state()).instances[0],original));await publish();
 check('G05 編輯來源保留構件映射',same((await state()).instances[0].value.mapping,mapping));
 await ctl('[data-asm-binding="1"]');await ctl('#asmEdit');for(const slot of [1,2])for(const axis of ['A','B'])await fill(`#asmValue${slot}${axis}`,axis==='A'?40:50);await publish();
 const beforeSourceEdit=await read(`apiRequest('dump').then(r=>r.text)`);
 // api() resolves only after the I8a dialog is confirmed or cancelled. Keep the
 // evaluation free so the harness can inspect the preview and send trusted input.
 const editSource=()=>read(`window.__generationSourceEdit=api('line spec position2 2800');void 0`);
 const sourceImpact=()=>wait(`!!document.querySelector('.reference-impact[open] #impact-confirm')&&!$('impact-confirm').disabled`);
 await editSource();await sourceImpact();
 check('G03 定位來源預覽列出連動長度且正式世界未變',await read(`(async()=>document.querySelector('.reference-impact code').textContent==='spec position2 2800'&&document.querySelector('.reference-impact').textContent.includes('1960 → 2260')&&(await apiRequest('dump')).text===${JSON.stringify(beforeSourceEdit)})()`));
 await ctl('.reference-impact .impact-actions button:first-child');await wait(`!document.querySelector('.reference-impact[open]')`);
 const cancelledSourceEdit=await read(`window.__generationSourceEdit`);
 check('G03 取消定位來源變更保留正式世界',cancelledSourceEdit.ok===false&&await read(`apiRequest('dump').then(r=>r.text===${JSON.stringify(beforeSourceEdit)})`));
 await editSource();await sourceImpact();await ctl('#impact-confirm');await wait(`!document.querySelector('.reference-impact[open]')`);
 await read(`(async()=>{const r=await window.__generationSourceEdit;if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();})()`);
 const changed=(await state()).instances[0];check('G03 配置與定位來源改變由原生重算',same(changed.value.mapping,mapping)&&changed.members.map(m=>m.geometry.length).join(',')==='2960,2960,2260'&&changed.members.every(m=>m.geometry.A===40&&m.geometry.B===50));
 await ctl('[data-asm-binding="1"]');await ctl('#asmInstanceEdit1');await fill('#asmInstanceName','保留未完成來源');await choose('#asmInstanceGuide1',0);await ctl('#asmClose');
 const saved=await read(`(async()=>{window.__generationBytes=await ReferenceWorkspace.exportBytes();const p=await GeometryProject.unpack(window.__generationBytes,fflate);return {format:p.manifest.format,drafts:p.manifest.assemblyDrafts.records};})()`);
 check('G07 未完成實例草稿保存第8版',saved.format==='geometry-canvas/8'&&saved.drafts.some(d=>d.kind==='instance'&&d.data.members[0].guideId===0));
 await read(`(async()=>{await ReferenceWorkspace.importBytes(window.__generationBytes,'生成重開.gcanvas');await renderObjects();})()`);check('G07 保存重開原生來源映射幾何精確一致',same((await state()).instances[0],changed));
 await ctl('#btnNewAssembly');await ctl('[data-asm-draft]');await ctl('#asmPreview');await wait(`$('asmConfirm').disabled&&$('asmPreviewResult').textContent.includes('I42')`);check('G06 未選定位線不能套用',same((await state()).instances[0],changed));await ctl('#asmDeleteDraft');
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await ctl('[data-asm-binding="1"]');await ctl('#asmInstanceEdit1');await fill('#asmInstanceName','390px 角材來源');await ctl('#asmPreview');await wait(`!$('asmConfirm').disabled`);
 await read(`(()=>{const original=window.fetch;window.__genReply={held:false,confirm:0,receipt:0};const gate=new Promise(resolve=>window.__genRelease=resolve);window.__genRestore=()=>window.fetch=original;window.fetch=async(...args)=>{const body=String(args[0])==='/api'?JSON.parse(args[1]?.body||'{}'):{};if(body.receipt)window.__genReply.receipt++;const response=await original(...args);if(body.cmd?.startsWith('assembly-confirm ')){window.__genReply.confirm++;const json=response.json.bind(response);response.json=async()=>{const result=await json();window.__genReply.result=result;window.__genReply.held=true;await gate;throw Error('Injected lost generation success response');};}return response;};})()`);
 await ctl('#asmConfirm');await wait(`window.__genReply.held`);check('G08 生成確認期間鎖住來源且已真正提交',await read(`$('asmInstanceName').disabled&&$('asmClose').disabled&&window.__genReply.result.ok&&apiRequest('assembly-read').then(r=>r.state.instances[0].value.source.name==='390px 角材來源')`));await read(`window.__genRelease();void 0`);await wait(`$('asmStatus')?.textContent.includes('已套用')`);await read(`window.__genRestore();void 0`);
 check('G08 生成成功回覆遺失由回執恢復且沒有重送',await read(`window.__genReply.confirm===1&&window.__genReply.receipt===1`));
 check('G09 390px 真輸入確認來源',same((await state()).instances[0].value.mapping,mapping)&&(await state()).instances[0].value.source.name==='390px 角材來源');
 await ctl('[data-asm-binding="1"]');await ctl('#asmInstanceEdit1');check('G09 無橫向溢出且可操作',await read(`document.documentElement.scrollWidth<=innerWidth&&$('assemblyWorkspace').scrollWidth<=innerWidth&&[...$('assemblyWorkspace').querySelectorAll('button,input,select')].filter(n=>n.getBoundingClientRect().height).every(n=>n.getBoundingClientRect().height>=44)`));
 fs.writeFileSync(path.join(os.tmpdir(),'geometry-tests','assembly-generation-mobile.png'),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'));
 await ctl('#asmDeleteDraft');await ctl('[data-asm-binding="1"]');await ctl('#asmInstanceDelete1');await wait(`!$('asmConfirm').disabled`);await ctl('#asmConfirm');await wait(`$('asmStatus')?.textContent.includes('已套用')`);
 check('G08 刪除整個實例與三支原生角材',(await state()).instances.length===0&&await read(`apiRequest('references').then(r=>r.timbers.length===2)`));await ctl('#asmClose');await read(`api('line undo')`);check('G08 單步復原映射與實例',same((await state()).instances[0].value.mapping,mapping));await read(`api('line redo')`);check('G08 單步重做刪除',(await state()).instances.length===0);
 const insufficient=await read(`(async()=>{
   const saved=await GeometryProject.unpack(window.__generationBytes,fflate),draft=saved.manifest.assemblyDrafts.records.find(d=>d.kind==='instance');
   const bytes=await GeometryProject.pack('reset\\n',{projectId:'generation-draft-only',name:'未完成實例',sources:[],faces:[],assemblyDrafts:{schema:GeometryProject.ASSEMBLY_DRAFT_SCHEMA,records:[draft]}},new Map(),fflate);
   const snapshot=async()=>({project:ReferenceWorkspace.getProjectState(),scene:(await apiRequest('dump')).text,drafts:ReferenceWorkspace.getAssemblyDrafts(),undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length});
   const before=await snapshot(),original=window.fetch;let validations=0,uploads=0,error=null;
   window.fetch=async(...args)=>{
     if(['/upload','/upload/confirm'].includes(String(args[0])))uploads++;
     const response=await original(...args);
     if(String(args[0])==='/upload/prepare'){
       validations++;const result=await response.json();
       return new Response(JSON.stringify({...result,capabilities:result.capabilities.filter(c=>c!==GeometryProject.GENERATION_CAPABILITY)}),{status:200,headers:{'Content-Type':'application/json'}});
     }
     return response;
   };
   try{await ReferenceWorkspace.importBytes(bytes,'未完成實例.gcanvas');}catch(e){error=e.message;}finally{window.fetch=original;}
   return {validations,uploads,error,before,after:await snapshot()};
 })()`);
 check('G06 第8版僅實例草稿也先驗服務生成能力',insufficient.validations===1&&insufficient.error?.includes('目前服務不支援'));
 check('G06 能力不足拒絕匯入且世界草稿歷史不變',insufficient.uploads===0&&same(insufficient.before,insufficient.after));
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
};
