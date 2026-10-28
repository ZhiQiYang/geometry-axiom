/* C09-C16. Normal gestures stay trusted; explicit stale-node/state injections
 * exercise the execution-time guard without substituting a production result. */
'use strict';
module.exports = s => {
  const {send,read,key,check,pre,wait,visible,point,ctl,fill,card,act,search,frames,settle,
    rawRight,right,rightCard,blank,mark,rows,events,commands,query,dump,checkpoint,noWrites,
    unchanged,fixtureCommands,fixture,selectCard,setCamera,beginBusy,releaseBusy,disconnect,
    online,focus,openParameter,settleParameterDraft,facePoint,hostCount,backToCanvas,objectLines,cardsVisible,
    saveOld,invokeOld,history,same,expectNativeDialog}=s;
  const selection=()=>read('JSON.stringify(oc.selection)');
  async function exclusive() {check('ONE_MENU_HOST',await hostCount()<=1);}
  async function geometryWithin(selector,viewport='#canvasViewport') {
    const bounds=await read(`(() => {const e=document.querySelector(${JSON.stringify(selector)}),v=document.querySelector(${JSON.stringify(viewport)});
      const r=e?.getBoundingClientRect(),p=v?.getBoundingClientRect();return r&&p?{visible:!!e.getClientRects().length&&!e.hidden,
        r:{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height},
        p:{left:p.left,right:p.right,top:p.top,bottom:p.bottom},overflow:document.documentElement.scrollWidth-innerWidth}:null;})()`);
    check('MENU_WITHIN_VIEWPORT',!!bounds&&bounds.visible&&bounds.r.width>0&&bounds.r.height>0&&
      bounds.r.left>=bounds.p.left+7&&bounds.r.right<=bounds.p.right-7&&
      bounds.r.top>=bounds.p.top+7&&bounds.r.bottom<=bounds.p.bottom-7&&bounds.overflow<=0,{selector,bounds});
  }
  async function faceFlow(width=1400,measure=false) {
    await fixture('reject',width);const before=await checkpoint();
    await rightCard(1);await exclusive();await ctl(act('open'));
    await wait('FACE_WORKSPACE_READY',`!$('objectWorkspace').hidden&&oc.edit?.bid===1`);await settle();await exclusive();
    await ctl('[data-face-tool="select"]');await ctl('#workspaceFitButton');await frames();
    const p=await facePoint(4000,1500);
    const hit=p&&await read(`document.elementFromPoint(${p.x},${p.y})?.closest('[data-face-hit]')?.dataset.faceHit`);
    pre('REAL_FACE_EDGE_HIT',hit==='e:0:1',{p,hit});const m=await mark();await rawRight(p);
    await wait('FACE_MENU_VISIBLE',`!$('feCtxMenu').hidden`);await exclusive();
    check('FACE_MENU_TYPED_EDGE',await read(`fe.sel?.kind==='edge'&&$('canvasCtxMenu').hidden&&!!$('feCtxMenu').querySelector('[data-fe-act="op:notch"]')&&!$('feCtxMenu').querySelector('[data-oc-act]')`));
    check('FACE_TRUSTED_CONTEXTMENU',(await events(m)).some(e=>e.type==='contextmenu'&&e.trusted));
    if(measure)await geometryWithin('#feCtxMenu','#faceEditorViewport');
    await ctl('#feCtxMenu [data-fe-act="op:notch"]');await wait('NOTCH_SIDE_FORM',`fe.op?.type==='notch'&&!$('feOpPanel').hidden`);await exclusive();
    if(measure)await geometryWithin('#feOpPanel','#faceEditorViewport');
    else check('FACE_MENU_RETAINED_WITH_FORM',await read(`!$('feCtxMenu').hidden`));
    await key('Escape','Escape',27);await key('Escape','Escape',27);await frames();
    check('FACE_ESC_CANCELS_ONLY_FORM_AND_MENU',await read(`$('feCtxMenu').hidden&&$('feOpPanel').hidden&&!fe.op&&fe.sel?.kind==='edge'`));
    await backToCanvas();await rightCard(1);await exclusive();
    check('NO_FACE_HOST_RESIDUE',await read(`$('feCtxMenu').hidden&&$('feOpPanel').hidden&&!$('feActionBar').classList.contains('fcm-suppressed')&&!$('faceEditorViewport').classList.contains('fcm-active')`));
    await unchanged(before);
  }
  async function staleResult(before,variant) {
    await invokeOld();const cmd=await commands(before.mark);
    check('STALE_ACTION_ZERO_WRITES',cmd.every(c=>/^(?:dump|objects|surfaces|references|engineering-read|source-inspect|render|boundary \d+|obstacles \d+)$/.test(c)),{variant,commands:cmd});
    check('STALE_ACTION_NO_NAV',await read('!oc.focus'),{variant});await unchanged(before);
  }
  async function retireVariant(variant) {
    await fixture();
    if(variant==='undo-redo')await fixtureCommands(['boundary 41 outline 0,0 1100,0 1100,800 0,800']);
    await rightCard(41);await saveOld();
    if(variant==='selection'||variant==='navigation-aba'){
      await selectCard(42);if(variant==='navigation-aba')await selectCard(41);
      pre('NAVIGATION_ADVANCED',await read('oc.navigationSequence>__p352Owner.navigation'),{variant});
      if(variant==='navigation-aba')pre('SELECTION_ABA',await read(`oc.sel?.kind==='boundary'&&oc.sel.id===41`));
    } else if(variant==='definition'){
      await fixtureCommands(['boundary 41 outline 0,0 1100,0 1100,800 0,800']);
      pre('DEFINITION_SAME_FRAME_NEW_REVISION',await read('ReferenceWorkspace.history.frame===__p352Owner.frame&&ReferenceWorkspace.getProjectState().revision>__p352Owner.revision'));
      pre('REFRESH_AFTER_EDIT',await read('renderObjects().then(r=>r===true)'));
    } else if(variant==='reincarnation'){
      await fixtureCommands(['history-begin','delete boundary 41','boundary 41 outline 0,0 1000,0 1000,800 0,800','canvas-pos boundary 41 80 100','history-end']);
      pre('SAME_ID_NEW_INCARNATION',await read(`ReferenceWorkspace.history.frame===__p352Owner.frame&&typeof ReferenceWorkspace.history.frame.ids.get(41)==='string'&&ReferenceWorkspace.history.frame.ids.get(41)!==__p352Owner.incarnation`));
      pre('REFRESH_AFTER_RECREATE',await read('renderObjects().then(r=>r===true)'));
    } else if(variant==='undo-redo'){
      await focus('#canvasViewport');await key('z','KeyZ',90,2);await settle();
      pre('UNDO_RETIRES_FRAME',await read('ReferenceWorkspace.history.frame!==__p352Owner.frame'));
      await key('y','KeyY',89,2);await settle();
      pre('REDO_RETIRES_OLD_FRAME',await read('ReferenceWorkspace.history.frame!==__p352Owner.frame'));
    } else if(variant==='context'){
      const r=await read(`apiRequest('reset')`);pre('RESET_OK',r.ok===true&&!r.preview,r);
      await fixtureCommands(['boundary 41 outline 0,0 1000,0 1000,800 0,800','canvas-pos boundary 41 80 100']);
      pre('REFRESH_AFTER_CONTEXT_CHANGE',await read('renderObjects().then(r=>r===true)'));
      pre('CONTEXT_RETIRED',await read('ReferenceWorkspace.context()!==__p352Owner.context'));
    } else if(variant==='connection'){
      const session=await read('connection.session');
      try {await disconnect();}finally{await online();}
      await settle();pre('SAME_SERVER_SESSION',await read(`connection.session===${JSON.stringify(session)}`));
    }
    await settle();const before=await checkpoint();await staleResult(before,variant);
  }
  async function attemptBlocked(name,mode) {
    await fixture();
    if(name==='create')await right(await blank());else await rightCard(41);
    const button=await point(act(name)),beforeFocus=await read('JSON.stringify(oc.focus)');
    if(mode==='busy')await beginBusy();else await disconnect();
    const m=await mark();
    try {
      // If the app retired the menu, that is an allowed rejection; never call a
      // helper to resurrect it. If it remains, click its real current position.
      const retained=await visible(act(name));
      if(retained){
        const p=await point(act(name));await s.click(p.x,p.y);await frames();
        if(name==='create'&&await visible(act('new:btnNewSpace')))await ctl(act('new:btnNewSpace'));
      } else console.log('P352_RETIRED_MENU '+JSON.stringify({name,mode,button}));
      await noWrites(m,'BLOCKED_ACTION_ZERO_WRITES');
      check('BLOCKED_ACTION_NO_NAV',await read(`JSON.stringify(oc.focus)===${JSON.stringify(beforeFocus)}`),{name,mode});
      if(await visible('#canvasCtxMenu'))check('BLOCKED_REASON_READABLE',await read(`$('canvasCtxMenu').querySelector('.fcm-footer')?.classList.contains('has-reason')===true||!!$('canvasCtxMenu').querySelector('[aria-disabled="true"][title]')`),{name,mode});
    } finally {if(mode==='busy')await releaseBusy();else await online();}
    await settle();
  }
  return [
    {id:'C09',run:async()=>{
      await fixture();await selectCard(41);const before=await checkpoint();await rightCard(41);
      pre('SEARCH_HAS_FOCUS',await read(`document.activeElement===document.querySelector(${JSON.stringify(search)})`));
      await key('Escape','Escape',27);await frames();
      check('FIRST_ESC_CLOSES_MENU_AND_RESTORES_FOCUS',await read(`$('canvasCtxMenu').hidden&&document.activeElement===$('canvasViewport')&&oc.sel?.id===41&&oc.selection.length===1`));
      await key('Escape','Escape',27);await settle();
      check('SECOND_ESC_REACHES_WORKSPACE',await read('oc.selection.length===0&&oc.sel===null'));await unchanged(before);
    }},
    {id:'C10',run:async()=>{await faceFlow();}},
    {id:'C11',run:async()=>{
      // This variant is first so M3 cannot be hidden by outside-pointer close.
      await fixture();await rightCard(41);
      // Focus/hover while still current: their reason()->position() also checks
      // current. The final true click must not accidentally test those guards.
      await key('ArrowDown','ArrowDown',40);await key('Home','Home',36);
      await key('ArrowDown','ArrowDown',40);await key('ArrowDown','ArrowDown',40);
      pre('CURRENT_PROBE_DELETE_FOCUSED',await read(`document.activeElement?.dataset.ocAct==='delete'`));
      const deletePoint=await point(act('delete'));
      await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:deletePoint.x,y:deletePoint.y,button:'none'});
      await saveOld();const before=await checkpoint();
      console.log('P352_FAULT C11 selection-only injection; same opening, connected node');
      await read(`oc.selection=[{kind:'boundary',id:42}];oc.sel={kind:'boundary',id:42};void 0`);
      pre('STALE_NODE_STILL_CONNECTED',await read(`__p352Old.isConnected&&CanvasContextMenu.open&&document.activeElement===__p352Old&&
        __p352Old.contains(document.elementFromPoint(${deletePoint.x},${deletePoint.y}))`));
      await s.click(deletePoint.x,deletePoint.y);await settle();
      check('CURRENT_PROBE_TRUSTED_CLICK',(await events(before.mark)).some(e=>e.type==='pointerdown'&&e.trusted&&e.button===0));
      await noWrites(before.mark,'STALE_ACTION_ZERO_WRITES');await unchanged(before);
      check('ISOLATED_CURRENT_PRESERVES_BOTH',(await query('objects')).faces.some(f=>f.id===41)&&(await query('objects')).faces.some(f=>f.id===42));
      if(s.currentOnly)return;
      for(const variant of ['selection','navigation-aba','definition','reincarnation','undo-redo','context','connection'])await retireVariant(variant);
    }},
    {id:'C12',run:async()=>{
      for(const target of [41,42]){
        await fixture();await rightCard(41);await saveOld();const worldA=await dump();
        await key('Escape','Escape',27);await rightCard(target);
        pre('OLD_NODE_DETACHED',await read('!__p352Old.isConnected'));
        pre('SAME_WORLD_BEFORE_REPLAY',(await dump())===worldA,{target});const before=await checkpoint();
        await invokeOld();await noWrites(before.mark,'OLD_NODE_ZERO_WRITES');await unchanged(before);
        check('OLD_NODE_NO_NAV',await read('!oc.focus'));
        // The allowed stale response may close B: always open a new valid menu.
        if(await visible('#canvasCtxMenu'))await key('Escape','Escape',27);
        await rightCard(target);const fresh=await checkpoint();await ctl(act('delete'));await settle();
        const cmd=await commands(fresh.mark),o=await query('objects');
        check('FRESH_MENU_DELETE_COMMAND_ONCE',cmd.filter(c=>c==='line delete boundary '+target).length===1,cmd);
        check('FRESH_MENU_NATIVE_DELETE',!o.faces.some(f=>f.kind==='boundary'&&f.id===target));
        check('FRESH_MENU_ONE_HISTORY_STEP',await history.single(fresh.pin));
        await focus('#canvasViewport');await key('z','KeyZ',90,2);await settle();
        check('FRESH_DELETE_UNDO_RESTORES_WORLD',(await dump())===fresh.scene);
      }
    }},
    {id:'C13',run:async()=>{
      await fixture();await openParameter();await fill('#paramName','右鍵取消保留草稿');await settleParameterDraft();
      const before=await checkpoint(),selectionBefore=await selection(),focusBefore=await read('JSON.stringify(oc.focus)');
      const p=await point(card(41)),m=await mark();
      await expectNativeDialog(()=>rawRight(p),{message:'參數有未套用的草稿。選擇確定會捨棄，取消可繼續編輯。',accept:false});
      await settle();
      check('DRAFT_CANCEL_TRUSTED_RIGHT_CLICK',(await events(m)).some(e=>e.type==='contextmenu'&&e.trusted&&e.card==='boundary:41'));
      check('CANCEL_RETAINS_DRAFT_AND_NO_MENU',await read(`ParameterUI.pending&&$('paramName')?.value==='右鍵取消保留草稿'&&$('canvasCtxMenu').hidden&&!CanvasContextMenu.open`)&&
        await selection()===selectionBefore&&await read('JSON.stringify(oc.focus)')===focusBefore);
      await unchanged(before);
    }},
    {id:'C14',run:async()=>{
      await fixture();const before=await checkpoint();await rightCard(42);await setCamera(-5000,-5000,.6);
      await ctl(act('locate'));await settle();check('LOCATE_TARGET_VISIBLE',await cardsVisible([42]));await unchanged(before);
      await rightCard(42);await ctl(act('props'));await settle();
      check('PROPS_TYPED_TARGET_VISIBLE',await visible('#inspectorContent')&&await read(`oc.sel?.kind==='boundary'&&oc.sel.id===42&&$('inspectorContent').querySelector('.ib-title')?.textContent.includes('42')`));
      await unchanged(before);
      for(const mode of ['busy','offline'])for(const name of ['open','delete','create'])await attemptBlocked(name,mode);
      // Positive nav control after recovery uses a fresh real menu.
      await fixture();const recovered=await checkpoint();await rightCard(41);await ctl(act('open'));
      await wait('RECOVERED_NAV_WORKS',`oc.focus?.t==='face'&&oc.edit?.bid===41&&!$('objectWorkspace').hidden`);await settle();await unchanged(recovered);
    }},
    {id:'C15',run:async()=>{
      await fixture();const before=await checkpoint(),o=await query('objects');await right(await blank());await focus(search);
      const selectionBefore=await selection();console.log('P352_LIMIT C15 synthetic composition contract; physical Chinese IME NOT VERIFIED');
      await read(`(() => {const input=document.querySelector(${JSON.stringify(search)});
        input.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true,data:''}));
        input.dispatchEvent(new CompositionEvent('compositionupdate',{bubbles:true,data:'空'}));
        for(const key of ['Enter','Escape','ArrowDown','ArrowUp'])for(const type of ['keydown','keyup'])
          input.dispatchEvent(new KeyboardEvent(type,{key,bubbles:true,cancelable:true,isComposing:true}));
      })()`);
      await frames();check('IME_KEYS_LEAVE_MENU_AND_FOCUS',await read(`!$('canvasCtxMenu').hidden&&document.activeElement===document.querySelector(${JSON.stringify(search)})`));
      await unchanged(before);
      await read(`document.querySelector(${JSON.stringify(search)}).dispatchEvent(new CompositionEvent('compositionend',{bubbles:true,data:'空'}));void 0`);
      await ctl(search);await send('Input.insertText',{text:'選取這段文字'});await key('a','KeyA',65,2);
      check('CTRL_A_ONLY_SELECTS_INPUT_TEXT',await read(`(() => {const n=document.querySelector(${JSON.stringify(search)});return document.activeElement===n&&n.selectionStart===0&&n.selectionEnd===n.value.length;})()`)&&await selection()===selectionBefore);
      await send('Input.insertText',{text:'空間'});await frames();
      check('UNIQUE_SPACE_SEARCH_RESULT',await read(`(() => {const n=[...$('canvasCtxMenu').querySelectorAll('.fcm-list [data-oc-act]')];return n.length===1&&n[0].dataset.ocAct==='new:btnNewSpace'&&n[0].getAttribute('aria-disabled')==='false';})()`));
      const enter=await mark();await key('Enter','Enter',13);await settle();
      const after=await query('objects'),ids=new Set(o.spaces.map(x=>x.id)),added=after.spaces.filter(x=>!ids.has(x.id)),cmd=await commands(enter);
      check('IME_END_ONE_NATIVE_SPACE',added.length===1&&cmd.filter(c=>/^line space \d+$/.test(c)).length===1,{added,cmd});
      check('IME_END_ONE_HISTORY_STEP',await history.single(before.pin));
      const afterScene=await dump();check('IME_PRESERVES_EXISTING_OBJECTS',[41,42,43].every(id=>same(objectLines(before.scene,id),objectLines(afterScene,id))));

      await fixture();await openParameter();await fill('#paramName','文字編輯右鍵');await settleParameterDraft();
      const textBefore=await checkpoint(),controls=await read(`(() => {const root=$('parameterEditor');if(!root)return [];
        return [...root.querySelectorAll('input:not([type="hidden"]),textarea,[contenteditable="true"],[contenteditable=""]')]
          .filter(e=>!e.disabled&&e.getClientRects().length>0).map((e,i)=>{e.dataset.p352Text=String(i);return {selector:'[data-p352-text="'+i+'"]',tag:e.tagName,editable:e.isContentEditable,value:e.value??e.textContent};});})()`);
      pre('REAL_TEXT_CONTROL_EXISTS',controls.length>0,controls);
      console.log('P352_TEXT_CONTROLS '+JSON.stringify(controls.map(({tag,editable})=>({tag,editable}))));
      for(const control of controls){
        await focus(control.selector);await key('ContextMenu','ContextMenu',93);await frames();
        check('TEXT_CONTEXT_NOT_GEOMETRY_MENU',await read(`$('canvasCtxMenu').hidden&&document.querySelector(${JSON.stringify(control.selector)})?.[${JSON.stringify(control.editable?'textContent':'value')}]===${JSON.stringify(control.value)}`),control);
        await key('Escape','Escape',27);
      }
      await read(`document.querySelectorAll('[data-p352-text]').forEach(e=>delete e.dataset.p352Text);void 0`);
      await settle();await unchanged(textBefore);
    }},
    {id:'C16',run:async()=>{
      for(const width of [1280,390]){
        await fixture('cards',width);const before=await checkpoint();
        for(const corner of ['tl','tr','bl','br']){
          if(await visible('#canvasCtxMenu'))await key('Escape','Escape',27);
          await right(await blank(corner));await geometryWithin('#canvasCtxMenu');await ctl(act('create'));
          await geometryWithin('#canvasCtxMenu .fcm-submenu');
          const names=await read(`[...$('canvasCtxMenu').querySelectorAll('.fcm-submenu [data-oc-act]')].map(n=>n.dataset.ocAct)`);
          check('ALL_SUBMENU_ENTRIES_PRESENT',names.length===10,names);
          for(const name of names)await point(act(name));
          // Leave the overlapping submenu before accessing the search input.
          await focus(act(names.at(-1)));await key('ArrowLeft','ArrowLeft',37);
          check('SUBMENU_BACK_TO_PARENT',await read(`!$('canvasCtxMenu').querySelector('.fcm-submenu')&&document.activeElement?.dataset.ocAct==='create'`));
          await fill(search,'多邊形');await frames();
          check('SEARCH_FIND_POLYGON',await read(`$('canvasCtxMenu').querySelectorAll('.fcm-list [data-oc-act]').length===1&&$('canvasCtxMenu').querySelector('.fcm-list [data-oc-act]').dataset.ocAct==='new:btnCreatePoly'`));
          await ctl(search);await key('a','KeyA',65,2);await key('Backspace','Backspace',8);await frames();
          for(let n=0;n<12&&!(await read(`document.activeElement?.dataset.ocAct==='create'`));n++)await key('ArrowDown','ArrowDown',40);
          check('KEYBOARD_REACHES_CREATE_PARENT',await read(`document.activeElement?.dataset.ocAct==='create'`));
          await key('ArrowRight','ArrowRight',39);await frames();
          check('KEYBOARD_ENTERS_SUBMENU',await read(`!!document.activeElement?.closest('.fcm-submenu')`));
          await key('ArrowLeft','ArrowLeft',37);await frames();
          check('KEYBOARD_RETURNS_PARENT',await read(`document.activeElement?.dataset.ocAct==='create'&&!$('canvasCtxMenu').querySelector('.fcm-submenu')`));
          const outside=await blank(corner.includes('b')?'tl':'br');await s.click(outside.x,outside.y);await frames();
          check('OUTSIDE_POINTER_CLOSES_MENU',await read(`$('canvasCtxMenu').hidden`));
          await unchanged(before);
        }
        await right(await blank());check('REOPEN_AFTER_OUTSIDE_CLOSE',await visible('#canvasCtxMenu'));await key('Escape','Escape',27);
        await faceFlow(width,true);
      }
    }}
  ];
};
