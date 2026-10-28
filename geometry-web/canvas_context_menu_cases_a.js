/* C01-C08. Loaded only by canvas_context_menu_test.js. */
'use strict';
module.exports = s => {
  const {send,read,key,check,pre,wait,visible,point,ctl,card,act,search,settle,
    rawRight,right,rightCard,blank,mark,rows,events,commands,query,dump,checkpoint,
    noWrites,unchanged,fixture,selectCard,setCamera,beginBusy,releaseBusy,disconnect,
    online,focus,backToCanvas,objectLines,cardsVisible,history,same,captureNewToasts,drag}=s;
  const selection=()=>read('oc.selection.map(x=>x.kind+":"+x.id).sort()');
  const cameraHome=()=>read(`oc.panX===0&&oc.panY===0&&oc.zoom===1&&$('oroot').getAttribute('transform')==='translate(0,0) scale(1)'`);
  const faceReady=id=>`oc.focus?.t==='face'&&oc.focus.id===${id}&&oc.edit?.bid===${id}&&!$('objectWorkspace').hidden`;
  async function createdIds(before,kind='faces') {
    const after=await query('objects'),ids=new Set(before[kind].map(o=>o.id));
    return {after,added:after[kind].filter(o=>!ids.has(o.id))};
  }
  async function rejectFixture(preview) {
    await fixture(preview?'preview':'reject');
    const refs=await query('references'),scene=await dump(),o=await query('objects');
    pre('GUIDE_ATTACHED',refs.guides.some(g=>g.id===71&&g.surface===1),refs.guides);
    if(preview)pre('PLACED_TIMBER_81',refs.timbers.some(t=>t.id===81&&t.geometry?.surface===1),refs.timbers);
    else pre('NO_PREVIEW_PREREQUISITE',refs.timbers.length===0&&o.gridBindings.length===0&&refs.grids.length===0&&
      !/^engineering\s/m.test(scene),{timbers:refs.timbers,bindings:o.gridBindings,grids:refs.grids});
  }
  return [
    {id:'C01',run:async()=>{
      await fixture();const before=await checkpoint();
      await rightCard(42,'MENU_VISIBLE_FOR_42');
      const menu=await read(`({title:$('canvasCtxMenu').querySelector('.fcm-heading strong').textContent,
        acts:[...$('canvasCtxMenu').querySelectorAll('[data-oc-act]')].map(n=>n.dataset.ocAct),
        selected:[...document.querySelectorAll('#ocv .ocard.selected')].map(n=>n.dataset.kind+':'+n.dataset.id)})`);
      check('CARD_TARGET_AND_ACTIONS',/42/.test(menu.title)&&same(await selection(),['boundary:42'])&&
        same(menu.selected,['boundary:42'])&&same(menu.acts,['open','locate','delete','props']),menu);
      await unchanged(before);
      await ctl(act('open'));await wait('OPEN_TARGET_42',faceReady(42));await settle();
      check('OBJECT_MENU_CLOSED_AFTER_NAV',await read(`$('canvasCtxMenu').hidden`));
      await unchanged(before);
    }},
    {id:'C02',run:async()=>{
      await fixture();const before=await checkpoint(),m=await mark();
      await focus(card(41)+' .card-enter[tabindex="0"]');
      await key('ContextMenu','ContextMenu',93);
      await wait('KEYBOARD_MENU_VISIBLE',`!$('canvasCtxMenu').hidden`);
      const trace=await events(m);
      check('TRUSTED_KEYBOARD_CONTEXT',trace.some(e=>e.type==='keydown'&&e.trusted&&e.key==='ContextMenu')&&
        trace.some(e=>e.type==='contextmenu'&&e.trusted&&e.card==='boundary:41'),trace);
      check('KEYBOARD_TARGET_41',same(await selection(),['boundary:41'])&&await read(`$('canvasCtxMenu').querySelector('.fcm-heading strong').textContent.includes('41')`));
      await key('ArrowDown','ArrowDown',40);await key('Home','Home',36);
      check('HOME_FOCUSES_OPEN',await read(`document.activeElement?.getAttribute('data-oc-act')==='open'`));
      await key('End','End',35);
      check('END_FOCUSES_LAST',await read(`document.activeElement?.getAttribute('data-oc-act')==='props'&&document.activeElement.getAttribute('aria-disabled')!=='true'`));
      await key('Home','Home',36);await key('Enter','Enter',13);
      await wait('KEYBOARD_OPEN_41',faceReady(41));await settle();await unchanged(before);

      await fixture();const emptyBefore=await checkpoint();await focus('#canvasViewport');
      await key('ContextMenu','ContextMenu',93);await wait('KEYBOARD_BLANK_MENU',`!$('canvasCtxMenu').hidden`);
      check('KEYBOARD_HOME_AVAILABLE',await visible(act('home'))&&await read(`document.querySelector(${JSON.stringify(act('home'))}).getAttribute('aria-disabled')==='false'`));
      await ctl(act('create'));
      if(await visible(act('new:btnCreatePoly')))await ctl(act('new:btnCreatePoly'));
      await settle();
      const reason=await read(`$('canvasCtxMenu').textContent`);
      check('KEYBOARD_REQUIRES_LOCATION',/先.*(?:指定|選擇|點).*位置|需要.*位置|請.*位置/.test(reason),{reason});
      await unchanged(emptyBefore);
    }},
    {id:'C03',run:async()=>{
      await fixture();await selectCard(41);await selectCard(42,8);
      pre('TWO_SELECTED',same(await selection(),['boundary:41','boundary:42']));
      const before=await checkpoint();await rightCard(42);
      check('MULTI_PRESERVED',same(await selection(),['boundary:41','boundary:42'])&&await read(`$('canvasCtxMenu').querySelector('.fcm-heading strong').textContent.includes('2')`));
      check('ONLY_CLEAR_ENABLED',await read(`(() => {const n=[...$('canvasCtxMenu').querySelectorAll('[data-oc-act]')];return n.filter(b=>b.getAttribute('aria-disabled')==='false').map(b=>b.dataset.ocAct).join(',')==='clear'&&['open','delete'].every(a=>n.some(b=>b.dataset.ocAct===a&&b.getAttribute('aria-disabled')==='true'&&b.title.includes('單選')));})()`));
      for(const name of ['open','delete']){
        await ctl(act(name));await settle();
        check('DISABLED_REASON_VISIBLE',await read(`$('canvasCtxMenu').querySelector('.fcm-footer').textContent.includes('單選')`),{name});
        check('DISABLED_NO_NAV',await read('!oc.focus'));await unchanged(before);
      }
      await focus(search);await key('ArrowDown','ArrowDown',40);await key('End','End',35);
      check('KEYBOARD_SKIPS_DISABLED',await read(`document.activeElement?.dataset.ocAct==='clear'`));
      await ctl(act('clear'));await settle();
      check('CLEAR_ONLY_SELECTION',same(await selection(),[])&&await read(`oc.sel===null&&document.querySelectorAll('#ocv .ocard.selected').length===0&&[41,42,43].every(id=>document.querySelector('#ocv .ocard[data-kind="boundary"][data-id="'+id+'"]'))`));
      await unchanged(before);
    }},
    {id:'C04',run:async()=>{
      await fixture();await setCamera(137,-91,.65);const before=await checkpoint();
      await right(await blank());await ctl(act('home'));await settle();
      check('HOME_EXACT_TRANSFORM',await cameraHome());await unchanged(before);
      await setCamera(-5000,-5000,.65);await right(await blank());await ctl(act('fit'));await settle();
      check('FIT_ALL_CARDS',await cardsVisible([41,42,43]));
      check('FIT_NOT_HOME',!await cameraHome());await unchanged(before);
      for(const [name,id] of [['snap','snapToggle'],['grid','gridToggle']]){
        const initial=await read(`$( '${id}' ).getAttribute('aria-pressed')`);
        for(let i=0;i<2;i++){
          await right(await blank());await ctl(act(name));await settle();
          const actual=await read(`({pressed:$('${id}').getAttribute('aria-pressed'),on:$('${id}').classList.contains('on'),grid:$('canvasViewport').classList.contains('show-grid')})`);
          const expected=i===0?initial!=='true':initial==='true';
          check('VIEW_TOGGLE_STATE',actual.pressed===String(expected)&&actual.on===expected&&(name!=='grid'||actual.grid===expected),{name,actual,expected});
          await unchanged(before);
        }
      }
      check('HOME_OLD_DOM_REMOVED',await read(`document.getElementById('homeButton')===null`));
    }},
    {id:'C05',run:async()=>{
      await fixture();await setCamera(137,-91,.65);const busyPoint=await blank();
      await beginBusy();const beforeBusy=await checkpoint();
      try {
        await right(busyPoint,'HOME_REACHABLE_WHILE_WORLD_BLOCKED');
        if(await visible(act('create'))){await ctl(act('create'));if(await visible(act('new:btnNewSpace')))await ctl(act('new:btnNewSpace'));}
        await noWrites(beforeBusy.mark,'BLOCKED_CREATE_ZERO_WRITES');
        await ctl(act('home'));await settle('HOME_SETTLED_WHILE_BUSY',true);
        check('BUSY_HOME_EXACT_TRANSFORM',await cameraHome());await unchanged(beforeBusy);
      } finally {await releaseBusy();}
      await settle();

      await fixture();await setCamera(137,-91,.65);const offlinePoint=await blank(),beforeOffline=await checkpoint();
      try {
        await disconnect();const m=await mark();
        await right(offlinePoint,'HOME_REACHABLE_WHILE_WORLD_BLOCKED');await ctl(act('home'));await s.frames();
        check('OFFLINE_HOME_EXACT_TRANSFORM',await cameraHome());await noWrites(m,'OFFLINE_ZERO_WRITES');
      } finally {await online();}
      await settle();await unchanged(beforeOffline);

      await fixture();const beforeTool=await checkpoint();await s.createEntry('#btnCreateRect');
      pre('RECT_TOOL_ARMED',await read(`oc.drawTool==='rect'`));
      const toolPoint=await blank();await right(toolPoint,'HOME_REACHABLE_WHILE_WORLD_BLOCKED');
      await ctl(act('home'));await settle();check('RECT_HOME_EXACT_TRANSFORM',await cameraHome());
      check('RIGHT_RELEASE_NOT_RECTANGLE',await read('oc.rect===null'));
      await unchanged(beforeTool);await focus('#canvasViewport');await key('Escape','Escape',27);
    }},
    {id:'C06',run:async()=>{
      await fixture();const before=await checkpoint(),objectsBefore=await query('objects'),p=await blank('br');
      const size=await read(`(() => {const r=document.querySelector(${JSON.stringify(card(41)+' .ocard-frame')});return {w:+r.getAttribute('width'),h:+r.getAttribute('height')};})()`);
      pre('UNSCALED_CARD_SIZE',size.w>0&&size.h>0,size);
      const coordinate=()=>read(`(() => {const r=$('ocv').getBoundingClientRect();return {x:Math.round((${p.x}-r.left-oc.panX)/oc.zoom-${size.w}/2),y:Math.round((${p.y}-r.top-oc.panY)/oc.zoom-${size.h}/2),centerX:Math.round((r.width/2-oc.panX)/oc.zoom-${size.w}/2),centerY:Math.round((r.height/2-oc.panY)/oc.zoom-${size.h}/2)};})()`);
      const old=await coordinate();await right(p);await ctl(act('create'));
      const expectedActs=['btnQuickGrid','btnCreateRect','btnCreatePoly','btnNewParameter','btnNewAssembly','btnNewSectionProfile','btnNewSpace','btnNewColumn','btnNewBeam','btnBox6'].map(x=>'new:'+x);
      const actualActs=await read(`[...$('canvasCtxMenu').querySelectorAll('.fcm-submenu [data-oc-act]')].map(n=>n.dataset.ocAct)`);
      check('TEN_CREATE_ENTRIES',same(actualActs,expectedActs),actualActs);await unchanged(before);
      await setCamera(173,-89,.7);const expected=await coordinate();
      pre('ANCHOR_DISTINGUISHES_BOTH_FAULTS',(expected.x!==old.x||expected.y!==old.y)&&
        (expected.x!==expected.centerX||expected.y!==expected.centerY),{p,old,expected});
      pre('SAME_MENU_AFTER_TRANSFORM',await read(`CanvasContextMenu.open&&!$('canvasCtxMenu').hidden`));
      await ctl(act('new:btnCreatePoly'));await wait('POLY_CREATED_AND_OPEN',`oc.focus?.t==='face'&&!!oc.edit&&fe.tool==='redraw'`);await settle();
      const created=await createdIds(objectsBefore);
      check('ONE_NEW_BOUNDARY',created.added.length===1&&created.added[0].kind==='boundary',created.added);
      const id=created.added[0].id,after=await dump();
      const pos=after.split(/\r?\n/).find(line=>line.startsWith('canvas-pos boundary '+id+' '))?.split(/\s+/).slice(-2).map(Number);
      check('NATIVE_CANVAS_POSITION_AT_CURRENT_TRANSFORM',same(pos,[expected.x,expected.y]),{id,p,old,expected,pos});
      check('EXISTING_DEFINITIONS_UNCHANGED',[41,42,43].every(n=>same(objectLines(before.scene,n),objectLines(after,n))));
      check('CREATE_ONE_HISTORY_STEP',await history.single(before.pin));
      await backToCanvas();
      check('CREATED_CARD_MATCHES_NATIVE',await read(`(() => {const c=document.querySelector(${JSON.stringify(card(id))});return !!c&&c.getAttribute('transform')==='translate(${expected.x},${expected.y})';})()`));

      await fixture();const rectBefore=await checkpoint(),o=await query('objects');
      await right(await blank());await ctl(act('create'));await ctl(act('new:btnCreateRect'));await settle();
      check('RECT_ENTRY_ONLY_ARMS_TOOL',await read(`oc.drawTool==='rect'&&oc.rect===null`));await unchanged(rectBefore);
      const a=await blank('br'),v=await read(`(()=>{const r=$('canvasViewport').getBoundingClientRect();return {left:r.left,top:r.top};})()`);
      const b={x:Math.max(v.left+60,a.x-120),y:Math.max(v.top+90,a.y-90)};
      pre('NONZERO_RECT_DRAG',Math.abs(a.x-b.x)>10&&Math.abs(a.y-b.y)>10,{a,b});
      await drag(a.x,a.y,b.x,b.y);await settle();const added=await createdIds(o);
      check('TRUSTED_RECTANGLE_CREATED',added.added.length===1&&added.added[0].kind==='boundary',added.added);
      check('RECTANGLE_NATIVE_COMMAND', (await commands(rectBefore.mark)).some(cmd=>/^line boundary \d+ outline /.test(cmd)));
    }},
    {id:'C07',run:async()=>{
      await fixture();const before=await checkpoint();await rightCard(41);await ctl(act('delete'));await settle();
      // Do not wait for a command that a DOM-only mutant intentionally omits.
      const cmd=await commands(before.mark),o=await query('objects'),after=await dump();
      check('DELETE_COMMAND_ONCE',cmd.filter(c=>c==='line delete boundary 41').length===1,cmd);
      check('DELETE_TRANSACTION_ONCE',cmd.filter(c=>c==='line history-begin').length===1&&cmd.filter(c=>c==='line history-end').length===1&&
        !cmd.some(c=>/^line delete boundary (42|43)$/.test(c)),cmd);
      check('NATIVE_TARGET_ABSENT',!o.faces.some(f=>f.kind==='boundary'&&f.id===41)&&objectLines(after,41).length===0,{faces:o.faces,after});
      check('OTHER_CARDS_RETAINED',[42,43].every(id=>o.faces.some(f=>f.id===id)&&same(objectLines(before.scene,id),objectLines(after,id)))&&
        await read(`!document.querySelector(${JSON.stringify(card(41))})&&[42,43].every(id=>document.querySelector('#ocv .ocard[data-kind="boundary"][data-id="'+id+'"]'))`));
      check('ONE_HISTORY_STEP',await history.single(before.pin));
      await focus('#canvasViewport');await key('z','KeyZ',90,2);await settle();
      check('UNDO_RESTORES_NATIVE_DUMP',(await dump())===before.scene);
      check('UNDO_RESTORES_CARDS',await read(`[41,42,43].every(id=>document.querySelector('#ocv .ocard[data-kind="boundary"][data-id="'+id+'"]'))`));
    }},
    {id:'C08',run:async()=>{
      for(const preview of [false,true]) {
        await rejectFixture(preview);const before=await checkpoint();await rightCard(1);
        const toasts=await captureNewToasts(async()=>{
          await ctl(act('delete'));
          if(preview){
            await wait('INVALID_PREVIEW_VISIBLE',`!!document.querySelector('.reference-impact[open]')`);
            const response=(await rows(before.mark)).find(r=>r.cmd==='line delete placement 1');
            check('INVALID_PREVIEW_FROM_CORE',response?.ok===false&&response.preview?.valid===false,response);
            check('INVALID_PREVIEW_CANNOT_APPLY',await read(`$('impact-confirm').disabled&&[...document.querySelectorAll('.reference-impact[open] .impact-violation')].some(n=>n.textContent.includes('先刪參考線'))`));
            check('PREVIEW_WORLD_UNCHANGED',(await dump())===before.scene);
            const back='.reference-impact[open] .impact-actions > button:not(#impact-confirm)';
            check('REAL_PREVIEW_BACK_BUTTON',await read(`document.querySelector(${JSON.stringify(back)}).textContent==='返回修改'`));
            await ctl(back);
          }
          await settle('DELETE_REJECTION_SETTLED');
        });
        const r=await rows(before.mark),cmd=r.map(x=>x.cmd),reply=r.find(x=>x.cmd==='line delete placement 1');
        check('REJECT_DELETE_COMMAND_ONCE',cmd.filter(c=>c==='line delete placement 1').length===1,cmd);
        if(!preview){check('DIRECT_CORE_REJECTION',reply?.ok===false&&!reply.preview&&reply.error?.includes('這個承載面還有參考線，先刪參考線（guide）'),reply);
          check('NEW_CORE_ERROR_VISIBLE',toasts.some(t=>t.visible&&t.text.includes('先刪參考線')),toasts);}
        else check('PREVIEW_CANCEL_ONCE',cmd.filter(c=>c==='line cancel-preview').length===1,cmd);
        check('REJECT_ABORTS_NOT_COMMIT',cmd.filter(c=>c==='line history-abort').length===1&&!cmd.includes('line delete boundary 1')&&
          !cmd.includes('line history-end')&&!cmd.some(c=>/^line confirm /.test(c)),cmd);
        check('REJECT_UNLOCKS',await read('!oc.busy&&ReferenceWorkspace.history.group===null'));
        await unchanged(before,{writes:false});
        const refs=await query('references'),surfaces=await query('surfaces');
        check('REJECT_RETAINS_NATIVE_OBJECTS',surfaces.surfaces.some(p=>p.id===1&&p.boundary===1)&&refs.guides.some(g=>g.id===71)&&
          (!preview||refs.timbers.some(t=>t.id===81&&t.geometry?.surface===1))&&await visible(card(1)),{preview,surfaces:surfaces.surfaces,refs});
      }
    }}
  ];
};
