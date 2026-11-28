'use strict';
/* D09 discovery: ordinary App controls, exact native sources, 390/1400 paint.
 * This module intentionally uses an explicit wheel-to-top for the layout
 * matrix; it does NOT call that cold-open evidence. The separate fresh-profile
 * driver tests a real saved archive before any wheel, click or expansion. */
const {controlProbe,controlWithinClip}=require('../../tests/diagnostics/r16_control_probe.cjs');
module.exports=async helpers=>{
  const {send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount,makeCheck}=helpers;
  console.log('=== P4549. D09 已套用覆寫的首屏摘要與明示檢視 ===');
  const check=makeCheck({prefix:'P4549 ',throwOnFail:true});
  const errors=exceptionCount();
  const read=async expression=>{const value=await eval_(expression);if(value?.__err)throw Error(value.__err);return value;};
  const call=(fn,...args)=>read('('+fn.toString()+')('+args.map(value=>JSON.stringify(value)).join(',')+')');
  const idle=()=>waitForUI("connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy",20000);
  const ready=()=>waitForUI("$('ewWorkspace')?.open&&!$('ewPreview').disabled&&!$('ewContent').inert&&$('ewStatus').textContent.startsWith('已讀取目前工程。')&&$('ewStatus').dataset.kind!=='error'",20000);
  const settle=()=>read('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))');
  const ctl=async selector=>{
    await read('document.querySelector('+JSON.stringify(selector)+')?.scrollIntoView({block:"nearest",inline:"nearest"});void 0');
    let probe;
    for(let i=0;i<16;i++){
      await settle();probe=await call(controlProbe,selector);
      if(controlWithinClip(probe))break;await sleep(70);
    }
    if(!controlWithinClip(probe))throw Error('P4549 unreachable control '+selector+' '+JSON.stringify(probe));
    await click(probe.points.at(0).x,probe.points.at(0).y);await sleep(100);await settle();
  };
  const key=async(keyName,code,vk,modifiers=0)=>{
    for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key:keyName,code,windowsVirtualKeyCode:vk,modifiers});
  };
  const field='#ewField-application-targets-1-overrides-gap-';
  const choose=async(selector,value)=>{
    const choices=await read('Array.from(document.querySelector('+JSON.stringify(selector)+').options).filter(o=>!o.disabled).map(o=>o.value)');
    if(!choices.includes(value))throw Error('P4549 missing native select option '+value);
    await ctl(selector);await key('Home','Home',36);
    for(let i=0;i<choices.indexOf(value);i++)await key('ArrowDown','ArrowDown',40);
    await key('Enter','Enter',13);
    await waitForUI('document.querySelector('+JSON.stringify(selector)+')?.value==='+JSON.stringify(value),20000);
  };
  const dump=()=>read("apiRequest('dump').then(r=>{if(!r.ok)throw Error('native dump rejected');return r.text;})");
  const pin=()=>read("(()=>{const h=ReferenceWorkspace.history;window.__p4549History={undo:h.undo.slice(),redo:h.redo.slice(),frame:h.frame,limit:h.limit};return {undo:h.undo.length,redo:h.redo.length};})()");
  const sameHistory=()=>read("(()=>{const h=ReferenceWorkspace.history,b=window.__p4549History;return h.frame===b.frame&&h.limit===b.limit&&h.undo.length===b.undo.length&&h.redo.length===b.redo.length&&h.undo.every((entry,i)=>entry===b.undo[i])&&h.redo.every((entry,i)=>entry===b.redo[i]);})()");
  const open=async()=>{await ctl('#fileMenuBtn');await ctl('#btnEngineeringSpecs');await ready();};
  const preview=async()=>{await ctl('#ewPreview');await waitForUI("!$('ewReview').hidden&&!!$('ewReviewed')&&!$('ewContent').inert",20000);};
  try{
    // Only fixture setup closes any preceding test workspace. Every editing,
    // preview, cancellation, confirmation and inspection below uses real input.
    await read('(async()=>{EngineeringWorkspace.close();resetSceneFocus();await setView3(false);return true;})()');
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
    await ctl('#fileMenuBtn');
    const dirty=await read('ReferenceWorkspace.context().dirty');
    await expectNativeDialog(()=>ctl('#btnNewProject'),{accept:true,message:'建立一份空白新專案，切換為新的專案識別及「未命名專案」。'+(dirty?'目前尚未保存的變更不會自動寫入檔案。':'')+'本次切換可一步復原；僅保存在本頁的形狀特徵參數不會恢復。確定繼續嗎？'});
    await idle();await ctl('#fileMenuBtn');await ctl('#exampleMenuBtn');await ctl('#btnEngineeringExample');await ready();
    await ctl('#ewContent details:has(> .ew-override '+field+'mode) > summary');await choose(field+'mode','literal');
    await ctl(field+'value');await key('a','KeyA',65,2);await send('Input.insertText',{text:'4'});await key('Tab','Tab',9);
    const original=await dump();await pin();await preview();
    check('D09_DISCOVERY_PREVIEW_ZERO_WRITE',await dump()===original&&await sameHistory());
    await ctl('#ewCancelPreview');check('D09_DISCOVERY_CANCEL_ZERO_WRITE',await dump()===original&&await sameHistory());
    await preview();const beforeConfirm=await pin();
    check('D09_DISCOVERY_REVIEW_REQUIRED',await read("$('ewConfirm').disabled"));
    await ctl('#ewReviewed');await ctl('#ewConfirm');
    await waitForUI("$('ewReview').hidden&&$('ewStatus').dataset.kind==='success'&&!$('ewContent').inert",20000);
    const committed=await dump();
    check('D09_DISCOVERY_SINGLE_CONFIRM',await read('ReferenceWorkspace.history.undo.length')===beforeConfirm.undo+1&&await read('ReferenceWorkspace.history.redo.length')===0);
    check('D09_DISCOVERY_NATIVE_SOURCE',await read("apiRequest('engineering-read').then(r=>{const a=r.state.applications.find(a=>a.placement_id===1);return a.overrides.gap.kind==='literal'&&a.overrides.gap.value===4;})"));
    await ctl('#ewClose');await ctl('#btnUndo');check('D09_DISCOVERY_UNDO',await dump()===original);
    await ctl('#btnRedo');check('D09_DISCOVERY_REDO',await dump()===committed);
    for(const width of [390,1400]){
      await send('Emulation.setDeviceMetricsOverride',{width,height:width===390?844:900,deviceScaleFactor:1,mobile:width===390});await settle();
      await open();const before=await dump();await pin();
      const editor=await read("(()=>{const r=document.querySelector('#ewContent .ew-editor').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()");
      await send('Input.dispatchMouseEvent',{type:'mouseWheel',x:editor.x,y:editor.y,deltaX:0,deltaY:-10000});
      await waitForUI("document.querySelector('#ewContent .ew-editor').scrollTop===0",20000);await settle();
      const probe=await call(controlProbe,'#ewOverrideOverview > summary');
      const observation=await read("(()=>{const d=$('ewOverrideOverview');return {text:d?.querySelector('summary').textContent,open:d?.open,face:Number(d?.dataset.ewFaceCount),object:Number(d?.dataset.ewObjectCount),width:innerWidth,height:innerHeight,scrollTop:document.querySelector('#ewContent .ew-editor').scrollTop};})()");
      console.log('P4549_LAYOUT '+JSON.stringify({width,probe,observation,mode:'explicit-wheel-to-top'}));
      check('D09_DISCOVERY_PAINT_'+width,controlWithinClip(probe)&&probe.rect.height>=44&&observation.width===width&&observation.height===(width===390?844:900),{probe,observation});
      check('D09_DISCOVERY_VALUE_'+width,observation.text.includes('明設 4 mm')&&observation.face>=1,observation);
      check('D09_DISCOVERY_OPEN_ZERO_WRITE_'+width,await dump()===before&&await sameHistory());
      if(!observation.open)await ctl('#ewOverrideOverview > summary');
      await ctl('[data-ew-reveal-overrides="face"]');
      const revealed=await call(controlProbe,field+'value');
      check('D09_DISCOVERY_EXPLICIT_REVEAL_'+width,controlWithinClip(revealed)&&revealed.active&&await read('document.querySelector('+JSON.stringify(field+'value')+').value')==='4',revealed);
      check('D09_DISCOVERY_REVEAL_ZERO_WRITE_'+width,await dump()===before&&await sameHistory());
      await preview();check('D09_DISCOVERY_UNEDITED_PREVIEW_'+width,await read("$('ewReview').querySelectorAll('.ew-diff').length===0"));
      await ctl('#ewCancelPreview');check('D09_DISCOVERY_UNEDITED_CANCEL_'+width,await dump()===before&&await sameHistory());
      await ctl('#ewClose');
    }
    check('D09_DISCOVERY_NO_EXCEPTIONS',exceptionCount()===errors);
  }finally{
    await read('delete window.__p4549History;EngineeringWorkspace.close();void 0');
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  }
};
