'use strict';
module.exports=s=>{
  const {send,read,key,check,pre,wait,settle,visible,ctl,fill,sp,query,dump,mark,rows,checkpoint,unchanged,fixture,
    rightPlan,planPoint,viewport,actions,geometry,objectLine,history,same,snap}=s;
  async function planClick(x,y){const p=await planPoint(x,y);
    pre('PLAN_LOCATION_REACHABLE',await read(`$('spacePlanSvg').contains(document.elementFromPoint(${p.x},${p.y}))`),{x,y,point:p});
    await s.click(p.x,p.y);await settle();}
  const unique=items=>[...new Set(items)].sort();
  return [
    {id:'W01',run:async()=>{
      await fixture();const before=await checkpoint();await rightPlan(650,700);
      check('SPACE_COLUMN_ACTIONS',same(unique(await actions('spaceCtxMenu','data-sp-act')),['delete','duplicate','size']));
      check('SPACE_COLUMN_TYPED_TARGET',await read(`$('spaceCtxMenu').textContent.includes('71')`));
      await unchanged(before);await snap('space-column-desktop');await key('Escape','Escape',27);
      await rightPlan(3500,800);
      check('SPACE_BLANK_ACTIONS',same(unique(await actions('spaceCtxMenu','data-sp-act')),['beam','column','view']));
      await unchanged(before);
    }},
    {id:'W02',run:async()=>{
      await fixture();const before=await checkpoint();await rightPlan(650,700);await ctl(sp('size'));
      await wait('SIZE_FORM_VISIBLE',`!$('rcDialog').hidden`);
      check('ORIGINAL_COLUMN_DIMENSIONS',await read(`$('rcW').value==='300'&&$('rcD').value==='400'`));
      await fill('#rcW','340');await fill('#rcD','420');await ctl('#rcCancel');await unchanged(before);
      await rightPlan(650,700);await ctl(sp('size'));await ctl('#rcSubmit');await unchanged(before);
      await rightPlan(650,700);await ctl(sp('size'));await fill('#rcW','340');await fill('#rcD','420');
      const commit=await checkpoint();await ctl('#rcSubmit');await wait('SIZE_FORM_CLOSED',`$('rcDialog').hidden`);
      const after=await dump();
      check('COLUMN_SAME_ID_AND_UNCHANGED_FIELDS',objectLine(after,'column',71)===objectLine(before.scene,'column',71).replace('size 300 400','size 340 420'),{before:before.scene,after});
      check('ONE_HISTORY_STEP',await history.single(commit.pin));
      await ctl('#faceUndoButton');check('UNDO_ORIGINAL_COLUMN',await dump()===before.scene);
      await ctl('#faceRedoButton');check('REDO_RESIZED_COLUMN',await dump()===after);
    }},
    {id:'W03',run:async()=>{
      await fixture();const before=await checkpoint();await rightPlan(2000,1500);await ctl(sp('size'));
      check('BEAM_ORIGINAL_SECTION',await read(`$('rcW').value==='201'&&$('rcD').value==='450'`));
      await fill('#rcW','203');await fill('#rcD','470');await ctl('#rcSubmit');
      const after=await dump();check('BEAM_AXIS_ENDPOINT_TOP_PRESERVED',objectLine(after,'beam',91)===objectLine(before.scene,'beam',91).replace('width 201 depth 450','width 203 depth 470'),{before:before.scene,after});
      check('BEAM_SINGLE_HISTORY_STEP',await history.single(before.pin));
      await rightPlan(2000,1500);await ctl(sp('size'));const invalid=await checkpoint();
      await fill('#rcW','-1');await ctl('#rcSubmit');
      check('INVALID_SIZE_VISIBLE_AND_FORM_RETAINED',await read(`!$('rcDialog').hidden&&!$('rcErr').hidden&&$('rcErr').textContent.includes('正整數')`));
      await unchanged(invalid);await ctl('#rcCancel');
      await rightPlan(2000,1500);const deletion=await checkpoint();await ctl(sp('delete'));await settle();
      const commands=(await rows(deletion.mark)).filter(r=>r.path==='/api').map(r=>r.body?.cmd);
      check('DELETE_IS_NATIVE_TYPED_COMMAND',commands.includes('line delete beam 91'),commands);
      check('DELETE_REMOVES_ONLY_BEAM',!(await query('objects')).beams.some(o=>o.id===91)&&!!(await geometry('column',71)));
      check('DELETE_SINGLE_HISTORY_STEP',await history.single(deletion.pin));
      await ctl('#faceUndoButton');check('DELETE_UNDO_RESTORES_BEAM',await dump()===after);
    }},
    {id:'W04',run:async()=>{
      await fixture();const before=await checkpoint();await rightPlan(650,700);await ctl(sp('duplicate'));
      await unchanged(before);await key('Escape','Escape',27);await unchanged(before);
      await rightPlan(650,700);await ctl(sp('duplicate'));
      const a=await planPoint(1000,2000),b=await planPoint(1100,2100);
      await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:2});
      try{
        await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:a.x,y:a.y,id:1}]});
        await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:a.x,y:a.y,id:1},{x:b.x,y:b.y,id:2}]});
        await send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
      }finally{await send('Emulation.setTouchEmulationEnabled',{enabled:false});}
      await settle();check('SECOND_POINTER_CANCELS_DUPLICATE_DRAFT',await read(`$('rcDialog').hidden`));await unchanged(before);
      await rightPlan(650,700);await ctl(sp('duplicate'));await planClick(1000,2000);
      await wait('DUPLICATE_POSITION_FORM',`!$('rcDialog').hidden&&$('rcX').value==='1000'&&$('rcY').value==='2000'`);
      check('DUPLICATE_PRESERVES_DIRECT_DEFINITION',await read(`$('rcW').value==='300'&&$('rcD').value==='400'&&$('rcZ0').value==='0'&&$('rcZ1').value==='2500'&&$('rcSpace').value==='9'`));
      await unchanged(before);const commit=await checkpoint();await ctl('#rcSubmit');await settle();
      const objects=await query('objects'),added=objects.columns.filter(o=>![71,83].includes(o.id));
      check('DUPLICATE_CREATES_AT_EXPLICIT_NEW_LOCATION',added.length===1&&same(added[0].box,[1000,2000,0,1300,2400,2500])&&added[0].space===9,added);
      check('DUPLICATE_ORIGINAL_UNCHANGED',objectLine(await dump(),'column',71)===objectLine(before.scene,'column',71));
      check('DUPLICATE_ONE_HISTORY_STEP',await history.single(commit.pin));
      await ctl('#faceUndoButton');check('DUPLICATE_UNDO',await dump()===before.scene);
    }},
    {id:'W05',run:async()=>{
      await fixture();const before=await checkpoint();await rightPlan(3500,800);await ctl(sp('column'));
      await wait('COLUMN_CREATE_FORM_VISIBLE',`!$('rcDialog').hidden`);
      check('CREATE_KEEPS_SPACE',await read(`$('rcSpace').value==='9'`));
      await ctl('#rcCancel');await unchanged(before);
      await rightPlan(3500,800);await ctl(sp('beam'));await unchanged(before);
      await key('Escape','Escape',27);await unchanged(before);
      const actionMark=await read('__r11menu.events.length');
      const anchor=await planPoint(1800,1000);await s.right(anchor,'spaceCtxMenu');
      const actionEvent=await read(`__r11menu.events.slice(${actionMark}).filter(e=>e.type==='contextmenu'&&e.trusted===true&&e.button===2).at(-1)||null`);
      pre('CREATE_TRUSTED_CONTEXTMENU_CLIENT_POINT',!!actionEvent&&Number.isFinite(actionEvent.x)&&Number.isFinite(actionEvent.y),{anchor,actionEvent});
      // A real viewport resize changes the letterboxed SVG CTM after opening.
      // The retained client point, not a cached room point, is authoritative.
      await viewport(1100,900);
      // The actual trusted DOM contextmenu coordinates are the product's retained anchor.
      // CDP's requested float screen point can differ from the delivered clientX/clientY.
      const expected=await read(`(()=>{const p=new DOMPoint(${actionEvent.x},${actionEvent.y}).matrixTransform($('spacePlanSvg').getScreenCTM().inverse());return {x:Math.round(p.x),y:Math.round(p.y)};})()`);
      await ctl(sp('column'));
      const ctmProbe=await read(`(()=>{const m=$('spacePlanSvg').getScreenCTM(),
        event=__r11menu.events.slice().reverse().find(e=>e.type==='contextmenu'&&e.trusted),
        room=p=>{if(!p)return null;const q=new DOMPoint(p.x,p.y).matrixTransform(m.inverse());return {x:Math.round(q.x),y:Math.round(q.y)};};
        return {rc:{x:$('rcX').value,y:$('rcY').value},trustedContextmenu:event?{x:event.x,y:event.y,trusted:event.trusted}:null,
          originalAnchor:${JSON.stringify(anchor)},finalCtm:{a:m.a,b:m.b,c:m.c,d:m.d,e:m.e,f:m.f},
          fromAnchor:room(${JSON.stringify(anchor)}),fromEvent:room(event)};})()`);
      console.log('R11_W05_FINAL_CTM_PROBE '+JSON.stringify(ctmProbe));
      check('CREATE_USES_FINAL_CTM_AT_ACTION',await read(`$('rcX').value===${JSON.stringify(String(expected.x))}&&$('rcY').value===${JSON.stringify(String(expected.y))}`),{anchor,expected});
      await fill('#rcW','200');await fill('#rcD','250');const create=await checkpoint();await ctl('#rcSubmit');await settle();
      const added=(await query('objects')).columns.filter(o=>![71,83].includes(o.id));
      check('COLUMN_CREATE_EXACT_GEOMETRY',added.length===1&&same(added[0].box,[expected.x,expected.y,0,expected.x+200,expected.y+250,2600])&&added[0].space===9,added);
      check('COLUMN_CREATE_SINGLE_HISTORY_STEP',await history.single(create.pin));
      await ctl('#faceUndoButton');check('COLUMN_CREATE_UNDO',await dump()===before.scene);
      await viewport();await rightPlan(250,1200);await ctl(sp('beam'));const waiting=await checkpoint();
      check('RIGHT_POINTERUP_IS_NOT_BEAM_ENDPOINT',await read(`$('rcA').value===''&&$('rcB').value===''`));
      await unchanged(waiting);await planClick(250,2300);
      check('BEAM_EXPLICIT_ENDPOINTS',await read(`$('rcAxis').value==='y'&&$('rcA').value==='1200'&&$('rcB').value==='2300'&&$('rcC').value==='250'`));
      await fill('#rcW','150');await fill('#rcD','250');const beam=await checkpoint();await ctl('#rcSubmit');await settle();
      const beams=(await query('objects')).beams.filter(o=>o.id!==91);
      check('BEAM_CREATE_EXACT_GEOMETRY',beams.length===1&&beams[0].axis==='y'&&beams[0].space===9&&same(beams[0].box,[175,1200,2350,325,2300,2600]),beams);
      check('BEAM_CREATE_SINGLE_HISTORY_STEP',await history.single(beam.pin));
    }},
    {id:'W06',run:async()=>{
      await fixture();const before=await checkpoint();
      await ctl('#spacePlaceColumn');
      check('P64_S1_SINGLE_ON_DEMAND_DIMENSIONS',await read(`!$('rcDialog').hidden&&!$('spaceSizeTools').hidden&&$('rcDialog').contains($('spaceSizeTools'))&&!$('spaceWorkspaceTools').contains($('spaceSizeTools'))&&['planColSize','planColCustom','planBeamSize','planBeamW','planBeamD'].every(id=>document.querySelectorAll('#'+id).length===1)`));
      await ctl('#rcCancel');await unchanged(before);
      const sel='#spacePlanSvg [data-sp-kind="column"][data-sp-id="71"]';
      pre('KEYBOARD_TYPED_TARGET',await read(`!!document.querySelector(${JSON.stringify(sel)})`));
      await read(`document.querySelector(${JSON.stringify(sel)}).focus();void 0`);
      await key('ContextMenu','ContextMenu',93);
      await wait('KEYBOARD_SPACE_MENU',`!!$('spaceCtxMenu')&&!$('spaceCtxMenu').hidden`);
      check('KEYBOARD_SPACE_ID',await read(`$('spaceCtxMenu').textContent.includes('71')`));
      await key('Escape','Escape',27);await unchanged(before);
      await rightPlan(650,700);
      await read(`window.__r11old=document.querySelector('#spaceCtxMenu [data-sp-act="size"]');void 0`);
      console.log('R11_FAULT W06 native revision changed while space action was retained');
      const altered=await read(`apiRequest('line spec R11CurrentProbe 17')`);pre('NATIVE_REVISION_CHANGED',altered?.ok===true,altered);
      const stale=await checkpoint();await read('__r11old.click();void 0');await settle();
      check('STALE_SPACE_MENU_CANNOT_OPEN_FORM',await read(`$('rcDialog').hidden`));await unchanged(stale);
      await rightPlan(3500,800);await ctl(sp('view'));check('SPACE_VIEW_SUBMENU',same(unique(await actions('spaceCtxMenu','data-sp-act',true)),['fit','projection']));
      await ctl(sp('projection'));await wait('PROJECTION_TAB_SELECTED',`!document.querySelector('[data-ss-pane="proj"]').hidden`);await unchanged(stale);
    }}
  ];
};
