/* #476 T1: real Chromium input for the existing face/space operation paths.
 * Fixture commands and diagnostic composition events are labelled separately.
 * No Chrome result, assertion census or cost is manufactured by this module.
 */
'use strict';

module.exports = async helpers => {
  const {send, eval_, click, waitForUI, makeCheck, exceptionCount} = helpers;
  console.log('=== P1163. R11 鍵盤右鍵、同面角材與同空間直接 RC 重用 ===');
  const check = makeCheck({prefix:'P1163 ', throwOnFail:true});
  const initialExceptions = exceptionCount();
  const read = async expression => {
    const value = await eval_(expression);
    if (value?.__err) throw Error('P1163 evaluation: '+value.__err);
    return value;
  };
  const page = (fn,...args) => read('('+fn.toString()+')('+args.map(value=>JSON.stringify(value)).join(',')+')');
  const same = (a,b) => JSON.stringify(a) === JSON.stringify(b);
  const precondition = (name,value,details) => {
    if (value !== true) throw Error('P1163_SETUP '+name+' '+JSON.stringify(details));
  };
  const frames = () => read('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))');
  const settle = async () => {
    await waitForUI("!oc.busy&&!ReferenceWorkspace.busy&&window.__t476.pending===0&&pendingApiResults.size===0");
    await frames();
  };
  const key = async (name,code,vk,modifiers=0) => {
    for (const type of ['rawKeyDown','keyUp'])
      await send('Input.dispatchKeyEvent',{type,key:name,code,windowsVirtualKeyCode:vk,modifiers});
    await frames();
  };
  const focus = selector => page(value=>{
    const node=document.querySelector(value);
    if (!node || !node.getClientRects().length || node.closest('[hidden]')) throw Error('No visible focus target '+value);
    node.focus({preventScroll:true}); return document.activeElement===node;
  },selector);
  const visible = selector => page(value=>{
    const node=document.querySelector(value),r=node?.getBoundingClientRect();
    return !!r&&r.width>0&&r.height>0&&!node.closest('[hidden]')&&getComputedStyle(node).visibility!=='hidden';
  },selector);
  async function control(selector) {
    await page(value=>document.querySelector(value)?.scrollIntoView({block:'nearest',inline:'nearest'}),selector);
    await frames();
    const point=await page(value=>{
      const node=document.querySelector(value),r=node?.getBoundingClientRect();
      if (!r) return null;
      const x=r.left+r.width/2,y=r.top+r.height/2,hit=document.elementFromPoint(x,y);
      return {x,y,width:r.width,height:r.height,hit:!!hit&&node.contains(hit),disabled:node.disabled===true};
    },selector);
    precondition('CONTROL_REACHABLE',!!point&&point.width>0&&point.height>0&&point.hit&&!point.disabled,{selector,point});
    await click(point.x,point.y); await settle();
  }
  async function choose(selector,value) {
    await page(value=>document.querySelector(value)?.scrollIntoView({block:'nearest',inline:'nearest'}),selector);
    await frames();
    precondition('SELECT_FOCUS',await focus(selector),{selector});
    const choice=await page((s,v)=>{
      const node=document.querySelector(s),options=[...node.options],index=options.findIndex(option=>option.value===v);
      return {index,count:options.length};
    },selector,String(value));
    precondition('SELECT_OPTION_EXISTS',choice.index>=0,{selector,value,choice});
    // Closed native selects accept Home/ArrowDown. Avoid Escape: it belongs to
    // the product's cancellation path and must never be used as test setup.
    await key('Home','Home',36);
    for (let i=0;i<choice.index;i++) await key('ArrowDown','ArrowDown',40);
    await key('Tab','Tab',9); await settle();
    precondition('SELECT_VALUE',await page((s,v)=>document.querySelector(s).value===v,selector,String(value)),{selector,value});
  }
  async function query(command) {
    const result=await read('apiRequest('+JSON.stringify(command)+')');
    precondition('NATIVE_COMMAND',result?.ok===true&&!result.preview,{command,result});
    return result;
  }
  const dump = async () => (await query('dump')).text;
  const mark = () => read('__t476.requests.length');
  const requests = from => page(value=>window.__t476.requests.slice(value),from);
  async function capture() {
    const scene=await dump();
    const pin=await page(()=>{
      const h=ReferenceWorkspace.history,p=window.__t476;
      const index=p.history.length;
      p.history.push({frame:h.frame,undo:h.undo.slice(),redo:h.redo.slice(),group:h.group,limit:h.limit,
        project:JSON.stringify(ReferenceWorkspace.getProjectState()),manifest:JSON.stringify(ReferenceWorkspace.manifest())});
      return index;
    });
    return {scene,pin,from:await mark()};
  }
  async function unchanged(before) {
    const history=await page(index=>{
      const h=ReferenceWorkspace.history,b=window.__t476.history.at(index);
      const entries=(a,z)=>a.length===z.length&&a.every((entry,i)=>entry===z.at(i));
      return h.limit===b.limit&&h.frame===b.frame&&h.group===b.group&&entries(h.undo,b.undo)&&entries(h.redo,b.redo)&&
        JSON.stringify(ReferenceWorkspace.getProjectState())===b.project&&JSON.stringify(ReferenceWorkspace.manifest())===b.manifest;
    },before.pin);
    return await dump()===before.scene&&history;
  }
  const singleHistory = before => page(index=>{
    const h=ReferenceWorkspace.history,b=window.__t476.history.at(index);
    const retained=b.undo.slice(Math.max(0,b.undo.length+1-b.limit));
    return h.limit===b.limit&&h.group===null&&h.redo.length===0&&
      h.undo.length===Math.min(b.undo.length+1,b.limit)&&h.undo.length===retained.length+1&&
      h.undo.slice(0,-1).every((entry,i)=>entry===retained.at(i))&&!b.undo.includes(h.undo.at(-1));
  },before.pin);
  const noWrites = async before => (await requests(before.from)).every(row=>
    row.path!=='/api'||!/^(?:line|newid|reset|load|undo|redo|timber-edit-confirm)\b/.test(row.body?.cmd||''));
  const menuWithinViewport = selector => page(value=>{
    const node=document.querySelector(value),r=node?.getBoundingClientRect();
    return !!r&&!node.hidden&&r.left>=0&&r.top>=0&&r.right<=innerWidth&&r.bottom<=innerHeight;
  },selector);
  const selection = () => read('({selected:fe.sel,timbers:[...fe.timberSelection].sort((a,b)=>a-b)})');
  async function selectTimber(id,additive=false) {
    const selector='[data-face-hit="t:'+id+'"]';
    await waitForUI('!!document.querySelector('+JSON.stringify(selector)+')&&!oc.busy');
    const point=await page((value,wanted)=>{
      const node=document.querySelector(value),r=node?.getBoundingClientRect(),v=document.getElementById('faceEditorViewport').getBoundingClientRect();
      if (!r) return null;
      for (const fx of [.5,.25,.75]) for (const fy of [.5,.25,.75]) {
        const x=r.left+r.width*fx,y=r.top+r.height*fy,hit=document.elementFromPoint(x,y);
        if (x>v.left&&x<v.right&&y>v.top&&y<v.bottom&&hit?.closest('[data-face-hit]')?.getAttribute('data-face-hit')==='t:'+wanted)
          return {x,y};
      }
      return null;
    },selector,id);
    precondition('TIMBER_HIT_TEST',!!point,{id,selector});
    await send('Input.dispatchMouseEvent',{type:'mouseMoved',...point,button:'none'});
    for (const type of ['mousePressed','mouseReleased'])
      await send('Input.dispatchMouseEvent',{type,...point,button:'left',clickCount:1,modifiers:additive?8:0});
    await settle();
    precondition('NATIVE_TIMBER_SELECTED',await page(value=>fe.timberSelection.has(value)||fe.sel?.kind==='timber'&&fe.sel.id===value,id),{id});
  }
  async function openFaceKeyboard(shift=false) {
    precondition('FACE_FOCUS',await focus('#faceEditorViewport'));
    await key(shift?'F10':'ContextMenu',shift?'F10':'ContextMenu',shift?121:93,shift?8:0);
    await settle();
  }
  async function reuseFace(action) {
    await control('#feCtxMenu [data-fe-act="reuse"]');
    const selector='#feCtxMenu [data-fe-act="timber-'+action+'"]';
    await waitForUI('(()=>{const n=document.querySelector('+JSON.stringify(selector)+');return !!n&&!n.disabled&&n.getAttribute("aria-disabled")!=="true";})()');
    await control(selector);
  }
  async function right(selector) {
    const point=await page(value=>{
      const node=document.querySelector(value),r=node?.getBoundingClientRect();
      if (!r) return null;
      const x=r.left+r.width/2,y=r.top+r.height/2,hit=document.elementFromPoint(x,y);
      return {x,y,hit:!!hit&&node.contains(hit),width:r.width,height:r.height};
    },selector);
    precondition('RIGHT_CLICK_HIT',!!point&&point.hit&&point.width>0&&point.height>0,{selector,point});
    for (const type of ['mousePressed','mouseReleased'])
      await send('Input.dispatchMouseEvent',{type,x:point.x,y:point.y,button:'right',clickCount:1});
    await settle();
  }
  async function spacePaste() {
    precondition('SPACE_PASTE_FOCUS',await focus('#spacePlanSvg'));
    await key('ContextMenu','ContextMenu',93);await settle();
    await control('#spaceCtxMenu [data-sp-act="reuse"]');
    await control('#spaceCtxMenu [data-sp-act="paste"]');
  }
  async function selectRoomPoint() {
    const point=await page(()=>{
      const svg=document.getElementById('spacePlanSvg'),m=svg.getScreenCTM();
      if (!m) return null;
      // Fixed legal room positions, then independent visibility/hit testing.
      // Picking a reachable point does not assign the form or call its handler.
      for (const y of [1500,2200,1000,150,600,2500]) for (const x of [1500,500,100,900,2100,2700,3300]) {
        const p=new DOMPoint(x,y).matrixTransform(m),hit=document.elementFromPoint(p.x,p.y);
        if (p.x>0&&p.x<innerWidth&&p.y>0&&p.y<innerHeight&&hit&&svg.contains(hit))
          return {x:p.x,y:p.y,matrix:[m.a,m.b,m.c,m.d,m.e,m.f]};
      }
      return null;
    });
    precondition('SPACE_PLACEMENT_POINT_REACHABLE',!!point,await page(()=>{
      const svg=document.getElementById('spacePlanSvg').getBoundingClientRect(),form=document.getElementById('rcDialog').getBoundingClientRect();
      return {svg:{x:svg.x,y:svg.y,width:svg.width,height:svg.height},form:{x:form.x,y:form.y,width:form.width,height:form.height}};
    }));
    const from=await read('__t476.events.length');
    await click(point.x,point.y);await settle();
    const event=await page(index=>window.__t476.events.slice(index).find(row=>row.type==='pointerup'&&row.trusted&&row.button===0),from);
    precondition('SPACE_PLACEMENT_TRUSTED_POINT',!!event&&event.target==='spacePlanSvg',event);
    return page((matrix,actual)=>{
      const p=new DOMPoint(actual.x,actual.y).matrixTransform(new DOMMatrix(matrix).inverse());
      return {x:Math.round(p.x),y:Math.round(p.y),actual};
    },point.matrix,event);
  }
  async function staleSpaceClipboard() {
    const before=await capture();
    precondition('SPACE_STALE_FOCUS',await focus('#spacePlanSvg'));
    await key('ContextMenu','ContextMenu',93);await settle();
    await control('#spaceCtxMenu [data-sp-act="reuse"]');
    const disabled=await page(()=>{
      const node=document.querySelector('#spaceCtxMenu [data-sp-act="paste"]');
      return !!node&&node.getAttribute('aria-disabled')==='true';
    });
    if (!disabled) return false;
    // Disabled menu rows remain clickable so their explicit reason can be read.
    await control('#spaceCtxMenu [data-sp-act="paste"]');
    const refused=await read("!document.getElementById('spaceCtxMenu').hidden&&document.querySelector('#spaceCtxMenu .fcm-footer').textContent.includes('請重新複製')")&&
      await unchanged(before)&&await noWrites(before);
    await key('Escape','Escape',27);await settle();return refused;
  }
  async function reset() {
    await page(()=>{window.FaceContextMenu?.hide();window.SpaceContextMenu?.hide();window.TimberEdit?.close(false);
      closeDialogs();closeMenus();closePanels();resetSceneFocus();});
    await settle();
    await query('reset');
  }
  async function faceFixture() {
    await reset();
    const ids=await query('newid'),surface=ids.surfaces.at(0),timber=ids.timber,parameter=ids.parameter;
    precondition('FRESH_NATIVE_IDS',Number.isSafeInteger(surface)&&surface>0&&Number.isSafeInteger(timber)&&Number.isSafeInteger(parameter),ids);
    for (const line of [
      'surface '+surface+' origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
      'timber '+timber+' 180 33 role boundary','place '+timber+' on '+surface+' at-face e0 +u +n'
    ]) await query('line '+line);
    const revision=(await query('engineering-read')).revision;
    const operations=[{op:'put-parameter',value:{id:parameter,name:'T476 寬度',nextFieldId:2,
      fields:[{id:1,name:'A',type:'dimension',input:'180'}]}},
      {op:'set-source',target:{kind:'timber',id:timber,field:'A'},source:{kind:'parameter',parameterId:parameter,fieldId:1}}];
    const preview=await page(async body=>{
      const response=await fetch('/engineering/preview',{method:'POST',headers:{'Content-Type':'application/json','X-Geometry-Version':pageRuntimeVersion},body:JSON.stringify(body)});
      return response.json();
    },{schema:'engineering-transaction/1',expectedRevision:revision,operations});
    precondition('PARAMETER_FIXTURE_PREVIEW',preview?.ok===true&&preview.preview?.valid===true,preview);
    await query('engineering-confirm '+preview.preview.token);
    await page(async id=>{await setView3(false);await renderObjects({persistPositions:false});await enterFocus('face',id);feSetTool('select');closePanels();},surface);
    await settle();
    await control('#feZoomFit');
    await selectTimber(timber);
    console.log('P1163_SETUP '+JSON.stringify({workspace:'face',surface,timber,parameter}));
    return {surface,timber,parameter};
  }
  async function spaceFixture() {
    await reset();
    const ids=await query('newid 2'),ceiling=ids.surfaces.at(0),floor=ids.surfaces.at(1),space=ids.space,column=ids.column;
    precondition('FRESH_NATIVE_SPACE_IDS',Number.isSafeInteger(ceiling)&&Number.isSafeInteger(floor)&&ceiling!==floor&&Number.isSafeInteger(space)&&Number.isSafeInteger(column),ids);
    for (const line of [
      'surface '+ceiling+' origin 0 0 2600 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
      'surface '+floor+' origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000',
      'space '+space+' boundary '+ceiling+' '+floor,
      'column '+column+' in '+space+' at 500 500 size 300 400 z 0 2500'
    ]) await query('line '+line);
    await page(async id=>{await setView3(false);await renderObjects({persistPositions:false});await enterFocus('space',id);closePanels();},space);
    await settle();
    if (!await visible('#spacePlanSvg')) await control('[data-ss-tab="plan"]');
    precondition('SPACE_PLAN_VISIBLE',await visible('#spacePlanSvg'));
    console.log('P1163_SETUP '+JSON.stringify({workspace:'space',space,column,ceiling,floor}));
    return {space,column};
  }
  await page(()=>{
    if (window.__t476) throw Error('P1163 observer already installed');
    const original=window.fetch,p=window.__t476={pending:0,requests:[],events:[],history:[]};
    const observe=event=>p.events.push({type:event.type,key:event.key,button:event.button,x:event.clientX,y:event.clientY,
      trusted:event.isTrusted,target:event.target?.id||event.target?.tagName});
    for (const type of ['keydown','keyup','contextmenu','pointerdown','pointerup']) document.addEventListener(type,observe,true);
    const wrapped=async(...args)=>{
      const url=new URL(typeof args.at(0)==='string'?args.at(0):args.at(0).url,location.href);
      if (!['/api','/timber-edit/read','/timber-edit/preview','/engineering/preview'].includes(url.pathname)) return original.apply(window,args);
      let body=null;try {body=JSON.parse(args.at(1)?.body||'{}');} catch (_) { /* record only */ }
      const row={path:url.pathname,body,result:null,settled:false};p.requests.push(row);p.pending++;
      try {const response=await original.apply(window,args);row.result=await response.clone().json();return response;}
      finally {row.settled=true;p.pending--;}
    };
    window.fetch=wrapped;
    p.cleanup=()=>{if(window.fetch===wrapped)window.fetch=original;
      for(const type of ['keydown','keyup','contextmenu','pointerdown','pointerup'])document.removeEventListener(type,observe,true);
      delete window.__t476;};
  });
  try {
    for (const size of [{width:1400,height:900},{width:390,height:844}]) {
      const suffix='_'+size.width;
      await send('Emulation.setDeviceMetricsOverride',{...size,deviceScaleFactor:1,mobile:false});
      await frames();
      await page(()=>{window.__t476.events.length=0;});
      const face=await faceFixture(),selected=await selection(),copyBaseline=await capture();
      await openFaceKeyboard();
      check('T476_FACE_KEYBOARD_SELECTION'+suffix,await visible('#feCtxMenu')&&same(await selection(),selected));
      check('T476_FACE_MENU_WITHIN_VIEWPORT'+suffix,await menuWithinViewport('#feCtxMenu'));
      await reuseFace('copy');
      check('T476_FACE_COPY_READONLY'+suffix,await unchanged(copyBaseline)&&await noWrites(copyBaseline));
      await openFaceKeyboard(true);
      check('T476_FACE_SHIFT_F10_SELECTION'+suffix,await visible('#feCtxMenu')&&same(await selection(),selected));
      await reuseFace('paste');
      check('T476_FACE_PASTE_FORM'+suffix,await read("document.getElementById('timberEditForm')?.dataset.mode==='create'"));
      check('T476_FACE_EXPLICIT_ANCHOR'+suffix,await read("document.getElementById('tbAnchor')?.value===''"));
      await choose('#timberEditPlacement',face.surface);await choose('#tbAnchor','at-face e2');
      await choose('#tbDir','+u');await choose('#tbSide','+n');
      const previewFrom=await mark();await control('#timberEditPreview');
      await waitForUI("__t476.requests.some((r,i)=>i>="+previewFrom+"&&r.path==='/timber-edit/preview'&&r.settled)");
      await settle();
      const response=(await requests(previewFrom)).find(row=>row.path==='/timber-edit/preview')?.result;
      check('T476_FACE_NATIVE_PREVIEW'+suffix,response?.ok===true&&response.preview?.valid===true,response);
      const created=response?.preview?.after?.at(0);
      check('T476_FACE_PARAMETER_REFERENCE'+suffix,created?.definition?.A?.mode==='source'&&
        same(created.definition.A.source,{kind:'parameter',parameterId:face.parameter,fieldId:1})&&created.definition.placement.anchor==='at-face e2',created);
      check('T476_FACE_PRIVATE_CANDIDATE'+suffix,created?.handle==='new:0'&&!Object.hasOwn(created,'id')&&await unchanged(copyBaseline)&&await noWrites(copyBaseline));
      await control('#timberEditCancel');await settle();
      check('T476_FACE_CANCEL_ZERO_WRITE'+suffix,await unchanged(copyBaseline)&&await noWrites(copyBaseline));
      await openFaceKeyboard();await key('Escape','Escape',27);await settle();
      check('T476_FACE_ESCAPE_FOCUS'+suffix,await read("document.getElementById('feCtxMenu').hidden&&document.activeElement===document.getElementById('faceEditorViewport')"));

      // Add a second ordinary member only after the first clipboard round has ended.
      const second=(await query('newid')).timber;
      await query('line timber '+second+' 180 33 role boundary');
      await query('line place '+second+' on '+face.surface+' at-face e2 +u +n');
      await page(async id=>{await renderObjects({persistPositions:false});await enterFocus('face',id);feSetTool('select');closePanels();},face.surface);
      await settle();await control('#feZoomFit');await selectTimber(face.timber);await selectTimber(second,true);
      if (await visible('#timberEditCancel')) await control('#timberEditCancel');
      const multiple=await selection(),multiBefore=await capture();
      await openFaceKeyboard();
      check('T476_FACE_MULTI_SELECTION'+suffix,await visible('#feCtxMenu')&&same(await selection(),multiple)&&multiple.timbers.length===2);
      await waitForUI("(()=>{const n=document.querySelector('#feCtxMenu [data-fe-act=timber-batch]');return !!n&&!n.disabled&&n.getAttribute('aria-disabled')!=='true';})()");
      await control('#feCtxMenu [data-fe-act="timber-batch"]');
      check('T476_FACE_BATCH_ENTRY'+suffix,await read("document.getElementById('timberEditForm')?.dataset.mode==='batch'"));
      await control('#timberEditCancel');await settle();
      check('T476_FACE_BATCH_CANCEL'+suffix,await unchanged(multiBefore)&&await noWrites(multiBefore));
      precondition('FACE_CLEAR_SELECTION_FOCUS',await focus('#faceEditorViewport'));
      await key('Escape','Escape',27);await settle();
      precondition('FACE_SELECTION_CLEARED',await read("oc.focus?.t==='face'&&fe.sel===null&&fe.timberSelection.size===0"));
      const noPointBefore=await capture();
      await openFaceKeyboard();
      check('T476_FACE_KEYBOARD_NO_GEOMETRIC_ANCHOR'+suffix,await read("fe.sel===null&&fe.timberSelection.size===0&&document.querySelector('#faceEditorViewport .fcm-anchor').style.display==='none'"));
      await control('#feCtxMenu [data-fe-act="create"]');
      for (const axis of ['u','v']) {
        const selector='#feCtxMenu [data-fe-act="guide-'+axis+'"]';
        const disabled=await page(value=>document.querySelector(value)?.getAttribute('aria-disabled')==='true',selector);
        await control(selector);
        check('T476_FACE_GUIDE_'+axis.toUpperCase()+'_NEEDS_POINT'+suffix,disabled&&
          await read("document.querySelector('#feCtxMenu .fcm-footer').textContent.includes('請先在面內指定位置')&&fe.op===null&&fe.sel===null")&&
          await unchanged(noPointBefore)&&await noWrites(noPointBefore));
      }
      await key('Escape','Escape',27);await settle();
      await focus('#faceEditorViewport');
      await page(()=>document.getElementById('faceEditorViewport').dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true,data:''})));
      await key('ContextMenu','ContextMenu',93);await settle();
      check('T476_FACE_COMPOSITION_GUARD'+suffix,await read("document.getElementById('feCtxMenu').hidden")&&await unchanged(noPointBefore));
      await page(()=>document.getElementById('faceEditorViewport').dispatchEvent(new CompositionEvent('compositionend',{bubbles:true,data:''})));
      await key('ContextMenu','ContextMenu',93);await settle();
      check('T476_FACE_AFTER_COMPOSITION'+suffix,await visible('#feCtxMenu'));
      await key('Escape','Escape',27);await settle();

      const space=await spaceFixture(),spaceBefore=await capture();
      precondition('SPACE_FOCUS',await focus('#spacePlanSvg'));
      await key('ContextMenu','ContextMenu',93);await settle();
      check('T476_SPACE_KEYBOARD_NO_ANCHOR'+suffix,await page(()=>{
        const menu=document.getElementById('spaceCtxMenu'),action=menu.querySelector('[data-sp-act="column"]');
        return !menu.hidden&&!!action&&(action.disabled||action.getAttribute('aria-disabled')==='true');
      }));
      check('T476_SPACE_MENU_WITHIN_VIEWPORT'+suffix,await menuWithinViewport('#spaceCtxMenu'));
      await key('Escape','Escape',27);await settle();
      await right('[data-sp-kind="column"][data-sp-id="'+space.column+'"]');
      await control('#spaceCtxMenu [data-sp-act="reuse"]');
      await control('#spaceCtxMenu [data-sp-act="copy"]');
      check('T476_SPACE_COPY_READONLY'+suffix,await unchanged(spaceBefore)&&await noWrites(spaceBefore));
      await spacePaste();
      check('T476_SPACE_PASTE_EXPLICIT_POSITION'+suffix,await read("!document.getElementById('rcDialog').hidden&&document.getElementById('rcX').value===''&&document.getElementById('rcY').value===''"));
      await key('Escape','Escape',27);await settle();
      check('T476_SPACE_CANCEL_ZERO_WRITE'+suffix,await unchanged(spaceBefore)&&await noWrites(spaceBefore));
      // Browser-level diagnostic: composition ownership at the canvas. This is
      // not a claim that a physical IME was exercised; the key itself is CDP input.
      await focus('#spacePlanSvg');
      await page(()=>document.getElementById('spacePlanSvg').dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true,data:''})));
      await key('ContextMenu','ContextMenu',93);await settle();
      check('T476_SPACE_COMPOSITION_GUARD'+suffix,await read("document.getElementById('spaceCtxMenu').hidden")&&await unchanged(spaceBefore));
      await page(()=>document.getElementById('spacePlanSvg').dispatchEvent(new CompositionEvent('compositionend',{bubbles:true,data:''})));
      await key('ContextMenu','ContextMenu',93);await settle();
      check('T476_SPACE_AFTER_COMPOSITION'+suffix,await visible('#spaceCtxMenu'));
      await key('Escape','Escape',27);await settle();
      await spacePaste();
      const room=await selectRoomPoint();
      check('T476_SPACE_POSITION_FROM_TRUSTED_INPUT'+suffix,await page(point=>
        document.getElementById('rcX').value===String(point.x)&&document.getElementById('rcY').value===String(point.y),room),room);
      check('T476_SPACE_RECIPE_FIELDS'+suffix,await page(id=>
        document.getElementById('rcW').value==='300'&&document.getElementById('rcD').value==='400'&&
        document.getElementById('rcZ0').value==='0'&&document.getElementById('rcZ1').value==='2500'&&
        document.getElementById('rcSpace').value===String(id),space.space));
      check('T476_SPACE_STAGED_ZERO_WRITE'+suffix,await unchanged(spaceBefore)&&await noWrites(spaceBefore));
      const commitBefore=await capture(),original=(await query('objects')).columns;
      await control('#rcSubmit');await waitForUI("document.getElementById('rcDialog').hidden&&!rcSubmitting");await settle();
      const result=await query('objects'),added=result.columns.filter(row=>!original.some(old=>old.id===row.id));
      const calls=await requests(commitBefore.from),allocations=calls.filter(row=>row.path==='/api'&&row.body?.cmd==='newid');
      check('T476_SPACE_NATIVE_NEW_ID'+suffix,added.length===1&&allocations.length===1&&
        allocations.at(0).result?.ok===true&&added.at(0).id===allocations.at(0).result.column&&
        calls.filter(row=>row.path==='/api'&&/^line column\b/.test(row.body?.cmd||'')).length===1,{added,allocations});
      check('T476_SPACE_EXACT_GEOMETRY'+suffix,added.length===1&&added.at(0).space===space.space&&
        same(added.at(0).box,[room.x,room.y,0,room.x+300,room.y+400,2500]),added);
      check('T476_SPACE_ORIGINAL_UNCHANGED'+suffix,same(result.columns.filter(row=>row.id===space.column),original));
      check('T476_SPACE_SINGLE_HISTORY'+suffix,await singleHistory(commitBefore));
      const committed=await dump();
      check('T476_SPACE_CLIPBOARD_STALE_AFTER_COMMIT'+suffix,await staleSpaceClipboard());
      await control('#faceUndoButton');
      check('T476_SPACE_UNDO'+suffix,await dump()===commitBefore.scene);
      check('T476_SPACE_CLIPBOARD_STALE_AFTER_UNDO'+suffix,await staleSpaceClipboard());
      await control('#faceRedoButton');
      check('T476_SPACE_REDO'+suffix,await dump()===committed);
      check('T476_TRUSTED_INPUT'+suffix,await read("__t476.events.some(e=>e.type==='keydown'&&e.key==='ContextMenu'&&e.trusted)&&__t476.events.some(e=>e.type==='contextmenu'&&e.trusted)&&__t476.events.some(e=>e.type==='pointerdown'&&e.trusted)"));
      console.log('P1163_WIDTH_COMPLETE '+JSON.stringify({width:size.width,height:size.height,face,space,input:'CDP Input.dispatchKeyEvent/Input.dispatchMouseEvent'}));
    }
    check('T476_NO_BROWSER_EXCEPTION',exceptionCount()===initialExceptions);
  } finally {
    await page(async()=>{window.FaceContextMenu?.hide();window.SpaceContextMenu?.hide();window.TimberEdit?.close(false);
      closeDialogs();closeMenus();closePanels();
      for (const id of ['faceEditorViewport','spacePlanSvg'])document.getElementById(id)?.dispatchEvent(new CompositionEvent('compositionend',{bubbles:true,data:''}));
      // The next suite opens the global file menu. Leave the workspace without
      // persisting incidental card positions, as the preceding P1161 does.
      resetSceneFocus();await setView3(false,{persistPositions:false});window.WorkspaceView?.syncControls();});
    await settle();
    await page(()=>window.__t476?.cleanup());
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
    await frames();
  }
};
