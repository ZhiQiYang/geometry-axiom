/* Project audit: trusted controls with API fixture setup/native read-back.
 * Package roundtrip below exercises exportBytes/importBytes, not OS file-picker UX.
 * GEOMETRY_PROJECT_AUDIT_ONLY=1 node geometry-web/cdp_test.js
 * Always use an isolated server/profile; these fixtures replace that test world.
 */
module.exports = async function projectAudit({send,eval_,sleep,click,waitForUI,exceptionCount}) {
  console.log('=== P68. 共用基準、參考線來源與角材定位回填 ===');
  const errors=exceptionCount(), fs=require('fs'),path=require('path');
  const check=(name,ok,detail=ok)=>{console.log('P68 '+name,ok===true?'✓':'✗',ok===true?'':JSON.stringify(detail));if(ok!==true)throw Error('P68 assertion failed: '+name+' '+JSON.stringify(detail));};
  const read=async expression=>{const v=await eval_(expression);if(v?.__err)throw Error(v.__err);return v;};
  const wait=async(expression,label=expression)=>{await waitForUI(expression,15000);if(await read(expression)!==true)throw Error('Audit timeout: '+label);};
  const ctl=async selector=>{
    await wait(`!!document.querySelector(${JSON.stringify(selector)})`,'control rendered '+selector);
    await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'center'})`);
    let p;
    // Native dialogs and nested scroll panes need one rendered frame after scrolling.
    for(let attempt=0;attempt<8;attempt++){
      await sleep(80);
      p=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('missing '+${JSON.stringify(selector)});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y);return {x,y,w:r.width,h:r.height,hit:e.contains(h),hitElement:h?.tagName+'#'+h?.id,disabled:!!e.disabled};})()`);
      if(p.hit&&!p.disabled&&p.w&&p.h)break;
    }
    if(!p.hit||p.disabled||!p.w||!p.h)throw Error('Audit control unreachable '+selector+' '+JSON.stringify(p));
    await click(p.x,p.y);await sleep(180);
    if(selector.startsWith('[data-edit-guide='))await wait(`!!document.querySelector('#guide-editor[open]')`,'guide source editor opened');
  };
  const key=async(key,code,vk,modifiers=0)=>{for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:vk,modifiers});await sleep(180);};
  const fill=async(selector,value)=>{await ctl(selector);await key('a','KeyA',65,2);await send('Input.insertText',{text:String(value)});await sleep(60);};
  const choose=async(selector,value)=>{
    const option=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});return [...e.options].findIndex(o=>o.value===${JSON.stringify(String(value))}&&!o.disabled);})()`);
    if(option<0)throw Error('Audit select has no enabled option '+selector+'='+value);
    await ctl(selector);await key('Escape','Escape',27);await key('Home','Home',36);
    for(let i=0;i<option;i++)await key('ArrowDown','ArrowDown',40);
    await key('Tab','Tab',9);
    if(await read(`document.querySelector(${JSON.stringify(selector)}).value`)!==String(value))throw Error('Native select did not choose '+selector+'='+value);
  };
  const shot=async name=>{const dir=process.env.GEOMETRY_PROJECT_AUDIT_SCREENSHOT_DIR;if(!dir)return;fs.mkdirSync(dir,{recursive:true});const r=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(dir,name+'.png'),Buffer.from(r.result.data,'base64'));};
  const dump=()=>read(`apiRequest('dump').then(r=>{if(r.ok!==true||typeof r.text!=='string')throw Error('Audit dump failed: '+JSON.stringify(r));return r.text;})`);
  const refs=()=>read(`apiRequest('references').then(r=>{if(r.ok!==true||!['guides','timbers','datums','specs'].every(k=>Array.isArray(r[k])))throw Error('Audit references failed: '+JSON.stringify(r));return r;})`);
  const reset=async(lines,face=null)=>{
    await read(`(async()=>{for(const d of document.querySelectorAll('dialog[open]')){d.close();if(d.matches('#datum-manager,#guide-editor,.reference-impact'))d.remove();}resetSceneFocus();await setView3(false);closePanels();const r=await api('reset');if(!r.ok)throw Error(JSON.stringify(r));for(const line of ${JSON.stringify(lines)}){const r=await api('line '+line);if(!r.ok)throw Error(line+' '+JSON.stringify(r));}await renderObjects();${face===null?'':`await enterFocus('face',${face});`}return true;})()`);
    await sleep(200);
  };
  const manager=async()=>{await ctl('#fileMenuBtn');await ctl('#btnDatums');await wait(`!!document.querySelector('#datum-manager[open]') && !!document.querySelector('#datum-surface option')`);};
  // Undo publishes the new World before its asynchronous workspace refresh.
  // Finish that refresh before navigating or clicking a source from its list.
  const settled=async()=>{
    await wait(`!oc.busy && !document.querySelector('#datum-manager')?.dataset.busy`);
    await read(`window.__cdpSettleUI(0)`);
    await wait(`!oc.busy && !document.querySelector('#datum-manager')?.dataset.busy`);
  };
  const impact=()=>wait(`!!document.querySelector('.reference-impact[open]')`,'impact preview');
  const confirm=async()=>{await ctl('#impact-confirm');await wait(`!document.querySelector('.reference-impact[open]') && !oc.busy`);await sleep(180);};
  const base='surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000';
  const supports=['timber 90 20 33 role boundary','place 90 on 1 at-face e0 +u +n','timber 91 20 33 role boundary','place 91 on 1 at-face e2 +u +n'];
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  check('頁面身份與非空介面',await read(`location.href===${JSON.stringify(process.env.GEOMETRY_TEST_URL||'http://localhost:8765/')} && document.title.length>0 && !!$('btnCanvasView') && !document.querySelector('vite-error-overlay,nextjs-portal')`));

  // Every datum definition and attachment in this scenario is submitted through its form.
  await reset(['surface 1 origin 0 0 0 u +x v +z outline 0,0 4000,0 4000,3000 0,3000','surface 2 origin 0 0 0 u +y v +z outline 0,0 3000,0 3000,3000 0,3000']);
  await manager();await fill('#datum-spec-name','AuditHeight');await fill('#datum-spec-value',1000);await ctl('#datum-spec-form button');await settled();
  check('具名尺寸表單提交與核心值一致',(await refs()).specs.some(s=>s.name==='AuditHeight'&&s.value===1000));
  await fill('#datum-id',0);await choose('#datum-axis','Z');await fill('#datum-expression','spec:AuditHeight');await ctl('#datum-form button');await settled();
  check('共用基準 ID 0 可建立且保留來源',(await refs()).datums.some(d=>d.id===0&&d.axis==='Z'&&d.expression==='spec:AuditHeight'&&d.position===1000));
  for(const sid of [1,2]){await choose('#datum-select',0);await choose('#datum-surface',sid);await ctl('#datum-attach-form button');await settled();}
  let r=await refs();const datumGuides=r.guides.filter(g=>g.source==='datum'&&g.datum===0);
  check('兩面明確引用同一基準',datumGuides.length===2&&datumGuides.map(g=>g.surface).sort().join(',')==='1,2',datumGuides);
  check('被引用基準刪除入口停用並說明原因',await read(`document.querySelector('[data-delete-datum="0"]').disabled && /仍被參考線/.test(document.querySelector('[data-delete-datum="0"]').title)`));
  await ctl('#datum-close');
  await read(`(async()=>{for(const [id,g] of ${JSON.stringify(datumGuides.map((g,i)=>[10+i,g]))}){const start=100+g.surface*10;const lines=[];for(const [offset,edge,role,dir] of [[0,0,'boundary','+u'],[1,2,'boundary','+u'],[2,1,'primary','+v'],[3,3,'primary','+v']])lines.push('timber '+(start+offset)+' 27 33 role '+role,'place '+(start+offset)+' on '+g.surface+' at-face e'+edge+' '+dir+' +n');lines.push('timber '+id+' 27 33 role custom priority 7','place '+id+' on '+g.surface+' at-line guide '+g.id+' +u +n');for(const line of lines){const r=await api('line '+line);if(!r.ok)throw Error(line+' '+JSON.stringify(r));}}await renderObjects();})()`);
  const datumBefore=await dump(), datumTimbersBefore=(await refs()).timbers.filter(t=>[10,11].includes(t.id));
  check('共用基準夾具確有兩支待傳遞角材',datumTimbersBefore.length===2&&datumTimbersBefore.map(t=>t.id).sort().join(',')==='10,11');
  await manager();await fill('#datum-spec-name','AuditHeight');await fill('#datum-spec-value',1500);await ctl('#datum-spec-form button');await impact();
  check('尺寸更改先預覽，世界仍未提交',(await dump())===datumBefore);
  const endpointText=await read(`[...document.querySelectorAll('.impact-guides li')].map(e=>e.textContent).join(' | ')`);
  check('同為一段仍列原與新端點，不只列段數',endpointText.includes('(0, 1000) → (4000, 1000)')&&endpointText.includes('(0, 1500) → (4000, 1500)')&&endpointText.includes('(0, 1000) → (3000, 1000)')&&endpointText.includes('(0, 1500) → (3000, 1500)'),endpointText);
  await shot('datum-impact-endpoints');await ctl('.reference-impact .impact-actions button:first-child');await settled();
  check('取消連動保持具名尺寸、兩面線及角材完整原狀',(await dump())===datumBefore);
  await ctl('#datum-spec-form button');await impact();await confirm();await settled();r=await refs();
  const confirmedGuides=r.guides.filter(g=>g.source==='datum'&&g.datum===0),confirmedTimbers=r.timbers.filter(t=>[10,11].includes(t.id));
  check('確認後兩面角材與線同步到 z1500',confirmedGuides.length===2&&confirmedGuides.map(g=>g.surface).sort().join(',')==='1,2'&&confirmedGuides.every(g=>g.worldPoint[2]===1500)&&confirmedTimbers.length===2&&datumTimbersBefore.every(before=>{const after=confirmedTimbers.find(t=>t.id===before.id);return after&&JSON.stringify(after.definition)===JSON.stringify(before.definition)&&after.geometry.origin.every((v,i)=>v===before.geometry.origin[i]+(i===2?500:0));}),r);
  const datumAfter=await dump();check('確認確實變更共用來源與場景',datumAfter!==datumBefore&&r.datums.find(d=>d.id===0)?.position===1500);
  await ctl('#datum-close');await ctl('#btnUndo');await settled();check('共用來源修改單步復原',(await dump())===datumBefore);
  await ctl('#btnRedo');await settled();check('共用來源修改重做還原完整確認後場景',(await dump())===datumAfter&&(await refs()).datums.find(d=>d.id===0)?.position===1500);
  await read(`(async()=>{window.__auditBytes=await ReferenceWorkspace.exportBytes();await ReferenceWorkspace.importBytes(__auditBytes,'audit-shared-datums.gcanvas');await renderObjects();})()`);
  check('gcanvas封裝／還原API保留共用基準、兩面引用及材定位',(await dump())===datumAfter&&(await refs()).guides.filter(g=>g.source==='datum').length===2);
  await manager();await fill('#datum-id',7);await choose('#datum-axis','X');await fill('#datum-expression','spec:AuditHeight');await ctl('#datum-form button');await settled();await ctl('[data-delete-datum="7"]');await settled();
  check('未引用基準可從介面刪除',(await refs()).datums.every(d=>d.id!==7));await ctl('#datum-close');await ctl('#btnUndo');await settled();check('基準刪除可復原',(await refs()).datums.some(d=>d.id===7));
  await read(`enterFocus('face',1)`);await sleep(180);await ctl(`[data-edit-guide="${datumGuides[0].id}"]`);
  check('DATUM線来源只讀且提供共用管理入口',await read(`$('guide-editor-expression').readOnly && $('guide-editor-apply').hidden && !$('guide-editor-datum').hidden`));await ctl('#guide-editor-datum');await wait(`!!document.querySelector('#datum-manager[open]')`);check('DATUM線可直接前往共用基準',await read(`!$('guide-editor')&&$('datum-manager').open`));await ctl('#datum-close');

  // LOCAL expressions are stored and edited as definitions, never derived coordinates.
  await reset([base,...supports,'spec local_x 1000','spec moved_x 1200','guide 0 1 v spec:local_x','timber 0 27 33 role custom priority 7','place 0 on 1 at-line guide 0 through 600 +v +n'],1);
  await ctl('[data-edit-guide="0"]');check('LOCAL來源與ID0正確顯示',await read(`$('guide-editor-expression').value==='spec:local_x'&&!$('guide-editor-expression').readOnly`));
  const localBefore=await dump();await fill('#guide-editor-expression','777');await ctl('#guide-editor-apply');
  await wait(`!$('guide-editor-apply').disabled || !!document.querySelector('.reference-impact[open]')`);
  if(await read(`!!document.querySelector('.reference-impact[open]')`)){
    check('非法來源的連動預覽不能確認',await read(`$('impact-confirm').disabled`));
    await ctl('.reference-impact .impact-actions button:first-child');await wait(`!$('guide-editor-apply').disabled`);
  }
  check('非法無名尺寸不改場景且顯示失敗',(await dump())===localBefore&&await read(`!!$('guide-editor-error').textContent`));
  await fill('#guide-editor-expression','spec:moved_x');await ctl('#guide-editor-apply');await impact();await confirm();await wait(`!$('guide-editor')`);
  check('合法來源更新由核心重算引用角材',(await refs()).guides.find(g=>g.id===0)?.expression==='spec:moved_x'&&(await refs()).timbers.find(t=>t.id===0).geometry.centerline===1200);
  await ctl('[data-edit-guide="0"]');await fill('#guide-editor-expression','spec:local_x');await ctl('#guide-editor-close');check('關閉來源編輯不套用草稿',(await refs()).guides[0].expression==='spec:moved_x');

  // Readbacks cover boundary anchors, explicit through, and explicit between with timber 0.
  const cases=[
    {name:'邊界定位',lines:[base,'timber 0 27 33 role boundary','place 0 on 1 at-face e0 +u +n'],anchor:'at-face e0',selector:'',priority:1},
    {name:'through與custom優先序',lines:[base,...supports,'spec center_x 1000','guide 0 1 v spec:center_x','timber 0 27 33 role custom priority 7','place 0 on 1 at-line guide 0 through 600 +v +n'],anchor:'at-line guide 0',selector:'through 600',priority:7},
    {name:'between支撐',lines:[base,'timber 90 20 33 role boundary','place 90 on 1 at-face e0 +u +n','timber 91 20 33 role boundary','place 91 on 1 at-face e2 +u +n','spec center_x 1000','guide 0 1 v spec:center_x','timber 0 27 33 role primary','place 0 on 1 at-line guide 0 between t90 t91 +v +n'],anchor:'at-line guide 0',selector:'between t90 t91',priority:2}
  ];
  for(const c of cases){
    await reset(c.lines,1);await ctl('[data-timber-id="0"]');await ctl('[data-fi-tab="components"]');
    // Open the existing timber section through its visible disclosure if collapsed.
    const disclosure=await read(`(()=>{const e=$('tbEditAnchor')?.closest('details');return e&&!e.open?e.id:null;})()`);if(disclosure)await ctl('#'+disclosure+' > summary');
    const originalScene=await dump(),original=(await refs()).timbers.find(t=>t.id===0),fields=await read(`({anchor:$('tbEditAnchor')?.value,selector:$('tbEditSelector')?.value,priority:$('tbEditPri')?.value,note:$('tbSelected')?.textContent})`);
    check(c.name+'：原定位／選段／優先序全部回填',fields.anchor===c.anchor&&fields.selector===c.selector&&fields.priority===String(c.priority)&&fields.note.includes('已帶入原定位'),fields);
    if(c.priority===7){const before=await dump();await fill('#tbEditPri','2.5');await ctl('#tbEditApply');await sleep(200);check('小數custom priority拒絕，沒有偷偷取整',(await dump())===before&&await read(`$('tbEditPri').classList.contains('invalid')`));await fill('#tbEditPri',7);}
    await fill('#tbEditA',29);await fill('#tbEditB',44);await ctl('#tbEditApply');
    await wait(`!oc.busy || !!document.querySelector('.reference-impact[open]')`);
    if(await read(`!!document.querySelector('.reference-impact[open]')`)){
      check(c.name+'：忙碌期間連動確認仍接受滑鼠',await read(`getComputedStyle($('impact-confirm')).pointerEvents!=='none' && getComputedStyle(document.querySelector('.reference-impact .impact-actions button:first-child')).pointerEvents!=='none'`));
      if(c.priority===1){
        await ctl('.reference-impact .impact-actions button:first-child');await wait(`!oc.busy`);await sleep(180);
        check('角材尺寸修改取消保留完整原場景',(await dump())===originalScene);
        await fill('#tbEditA',29);await fill('#tbEditB',44);await ctl('#tbEditApply');await impact();
      }
      await confirm();
    }
    await wait(`!oc.busy`);await sleep(200);
    const updated=(await refs()).timbers.find(t=>t.id===0);
    check(c.name+'：只改A/B保留同ID及完整定位定義',updated?.geometry.A===29&&updated.geometry.B===44&&JSON.stringify(updated.definition)===JSON.stringify(original.definition),updated);
    await shot('timber-'+c.priority+'-definition');
  }
  // The source editor must remain usable at mobile width, without shifting the document sideways.
  await reset([base,'spec local_x 1000','guide 0 1 v spec:local_x'],1);
  await ctl('[data-edit-guide="0"]');await wait(`!!document.querySelector('#guide-editor[open]')`);
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await sleep(180);
  const mobile=await read(`(()=>{const d=$('guide-editor').getBoundingClientRect(),b=$('guide-editor-apply').getBoundingClientRect();return {overflow:document.documentElement.scrollWidth>innerWidth,left:d.left,right:d.right,width:innerWidth,font:getComputedStyle($('guide-editor-expression')).fontSize,buttonHeight:b.height,buttonVisible:b.left>=0&&b.right<=innerWidth&&b.top>=0&&b.bottom<=innerHeight};})()`);
  check('已開啟來源編輯於390px無水平溢出且操作可見',!mobile.overflow&&mobile.left>=0&&mobile.right<=390&&parseFloat(mobile.font)>=11&&mobile.buttonHeight>=24&&mobile.buttonVisible,mobile);await shot('guide-source-mobile');await ctl('#guide-editor-close');
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  check('所有新增流程沒有未處理瀏覽器例外',exceptionCount()===errors,{before:errors,after:exceptionCount()});
};
