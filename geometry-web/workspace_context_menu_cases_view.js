'use strict';
module.exports=s=>{
  const {send,read,key,check,pre,wait,settle,point,ctl,v3,query,dump,mark,rows,checkpoint,unchanged,
    fixture,right,rawRight,blankView,viewState,viewPoint,rightView,align,actions,same,snap}=s;
  const rootSelector=(kind,id)=>`#world [data-owner-kind="${kind}"][data-owner-id="${id}"]`;
  async function openSettings(){
    const selector=await read(`(()=>{const e=document.querySelector('[data-v3-layer="rc"]');
      const d=e?.closest('details');return d&&!d.open?'#'+d.id+' > summary':null;})()`);
    if(selector)await ctl(selector);
  }
  async function expectedTarget(pick,kind,id){
    check('NATIVE_ROOT_EXACT_TYPE_AND_ID',same(pick.target.root,{kind,id}),pick.target);
    check('UI_ROOT_IS_SAME_NATIVE_TARGET',same((await viewState()).lastTarget,pick.target));
  }
  function shapeBounds(snapshot,kind,id){
    const points=[];
    for(const o of snapshot.ops.filter(o=>o.owner?.kind===kind&&o.owner.id===id)){
      if(o.op==='poly')for(let i=0;i<o.p.length;i+=2)points.push([o.p[i],o.p[i+1]]);
      else if(o.op==='rect'||o.op==='line')points.push([o.x0,o.y0],[o.x1,o.y1]);
    }
    return points.length?[Math.min(...points.map(p=>p[0])),Math.min(...points.map(p=>p[1])),
      Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))]:null;
  }
  return [
    {id:'W07',run:async()=>{
      await fixture('view');const before=await checkpoint();await right(await blankView(),'viewCtxMenu');
      check('BLANK_VIEW_HAS_NO_OPEN',!(await actions('viewCtxMenu','data-v3-act')).includes('open'));
      check('BLANK_VIEW_ALIGNS_AND_RESTORES',await read(`$('viewCtxMenu').textContent.includes('對齊視角')&&$('viewCtxMenu').textContent.includes('顯示已隱藏物件')`));
      await unchanged(before);await snap('view-blank-desktop');await key('Escape','Escape',27);
      await fixture('space');await ctl('[data-ss-tab="proj"]');const projection=await checkpoint();
      const p=await rightView('front',3500,-2600,'space');
      check('SPACE_PROJECTION_USES_SAME_TYPED_MENU',same(p.target.root,{kind:'boundary',id:71})&&p.target.boundaryId===71,p.target);
      await unchanged(projection);await snap('space-projection-menu');
    }},
    {id:'W08',run:async()=>{
      await fixture('view');const before=await checkpoint();
      const rc=await rightView('front',650,-1200);await expectedTarget(rc,'column',71);
      check('RC_DOES_NOT_INVENT_D3',rc.target.boundaryId===null&&await read(`document.querySelector('#viewCtxMenu [data-v3-act="open"]').getAttribute('aria-disabled')==='true'`),rc.target);
      check('RC_OPEN_DISABLED_REASON',await read(`$('viewCtxMenu').textContent.includes('此物件沒有可開啟的面內工作區')||document.querySelector('#viewCtxMenu [data-v3-act="open"]').title.includes('此物件沒有可開啟的面內工作區')`));
      await ctl(v3('props'));await settle();
      check('RC_PROPERTY_IS_TYPED_READ_ONLY',await read(`!$('workspaceProperties').hidden&&$('workspaceProperties').dataset.readonly==='true'&&$('workspaceProperties').dataset.propertiesKind==='column'&&$('workspaceProperties').dataset.propertiesId==='71'&&$('workspaceProperties').textContent.includes('71')&&!$('workspaceProperties').querySelector('input,select,textarea')`));
      await unchanged(before);
      const face=await rightView('front',3500,-2600);await expectedTarget(face,'boundary',71);
      check('NATIVE_BOUNDARY_ID_DISTINCT_FROM_SCENE_INDEX',face.target.boundaryId===71&&face.target.placementId===71,face.target);
      check('EXACT_FOUR_OBJECT_ACTIONS',same([...new Set(await actions('viewCtxMenu','data-v3-act'))].sort(),['align','hide','open','props']));
      await ctl(v3('open'));await wait('OPEN_CORRECT_D3',`oc.focus?.t==='face'&&oc.focus.id===71&&oc.edit?.bid===71&&!$('objectWorkspace').hidden`);
      await unchanged(before);
    }},
    {id:'W09',run:async()=>{
      await fixture('view');const before=await checkpoint();
      await right(await blankView(),'viewCtxMenu');await ctl(v3('align'));
      check('EXACT_FOUR_ORTHOGRAPHIC_VIEWS_AND_RESTORE',same([...new Set(await actions('viewCtxMenu','data-v3-act',true))].sort(),['bottom','front','side','three','top']));
      await ctl(v3('top'));await settle();
      const top=(await viewState()).snapshot;
      check('TOP_NATIVE_FRAME_IS_POSITIVE_X_NEGATIVE_Y',top.layout.views.length===1&&top.layout.views[0].viewId==='top'&&same(top.layout.views[0].right,[1,0,0])&&same(top.layout.views[0].down,[0,-1,0]),top.layout);
      check('TOP_NATIVE_COLUMN_GEOMETRY',same(shapeBounds(top,'column',71),[500,-900,800,-500]),shapeBounds(top,'column',71));
      const topPick=await rightView('top',650,-700);await expectedTarget(topPick,'column',71);await snap('view-top-column');
      await key('Escape','Escape',27);await align('bottom');
      const bottom=(await viewState()).snapshot;
      check('BOTTOM_FRAME_IS_POSITIVE_X_POSITIVE_Y',same(bottom.layout.views[0].right,[1,0,0])&&same(bottom.layout.views[0].down,[0,1,0]),bottom.layout);
      check('BOTTOM_NATIVE_COLUMN_GEOMETRY',same(shapeBounds(bottom,'column',71),[500,500,800,900]),shapeBounds(bottom,'column',71));
      await expectedTarget(await rightView('bottom',650,700),'column',71);
      await key('Escape','Escape',27);await align('side');
      check('SIDE_NATIVE_FRAME',same((await viewState()).snapshot.layout.views[0].right,[0,1,0])&&same((await viewState()).snapshot.layout.views[0].down,[0,0,-1]));
      await align('front');check('FRONT_NATIVE_FRAME',same((await viewState()).snapshot.layout.views[0].right,[1,0,0])&&same((await viewState()).snapshot.layout.views[0].down,[0,0,-1]));
      await align('three');check('RESTORE_THREE_NATIVE_FRAMES',same((await viewState()).snapshot.layout.views.map(v=>v.viewId),['front','side','bottom']));
      await unchanged(before);
    }},
    {id:'W10',run:async()=>{
      await fixture('view');const before=await checkpoint();
      await rightView('front',650,-1200);await ctl(v3('hide'));await settle();
      const hidden=await viewState();
      check('ONE_TYPED_ROOT_HIDDEN',same(hidden.hidden,[{kind:'column',id:71}]),hidden.hidden);
      check('ALL_HIDDEN_OWNER_OPS_REMOVED',hidden.snapshot.ops.every(o=>!(o.owner?.kind==='column'&&o.owner.id===71)));
      check('OTHER_COLUMN_AND_SAME_ID_BOUNDARY_REMAIN',hidden.snapshot.ops.some(o=>o.owner?.kind==='column'&&o.owner.id===83)&&hidden.snapshot.ops.some(o=>o.owner?.kind==='boundary'&&o.owner.id===71));
      check('SVG_HAS_NO_HIDDEN_OWNER',await read(`document.querySelectorAll(${JSON.stringify(rootSelector('column',71))}).length===0&&document.querySelectorAll(${JSON.stringify(rootSelector('column',83))}).length>0`));
      const at=await mark();await right(await viewPoint('front',650,-1200),'viewCtxMenu');
      const pick=(await rows(at)).filter(r=>r.path==='/view/pick').at(-1);
      check('HIDDEN_ROOT_UNPICKABLE',pick?.result?.status==='NONE'&&pick.result.target===null,pick);
      await key('Escape','Escape',27);await openSettings();
      check('HIDDEN_COUNT_AND_RESTORE_VISIBLE',await read(`$('v3Panel').textContent.includes('已隱藏 1')||$('v3Panel').textContent.includes('已隱藏1')`));
      const restore=await read(`(()=>{const b=[...$('v3Panel').querySelectorAll('button')].find(n=>/還原/.test(n.textContent)&&!/全部/.test(n.textContent));return b?.outerHTML;})()`);
      pre('PER_ROOT_RESTORE_CONTROL',typeof restore==='string',{restore});
      const r=await read(`(()=>{const b=[...$('v3Panel').querySelectorAll('button')].find(n=>/還原/.test(n.textContent)&&!/全部/.test(n.textContent));b.scrollIntoView({block:'nearest'});const r=b.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,hit:b.contains(document.elementFromPoint(x,y))};})()`);
      pre('RESTORE_BUTTON_HIT',r.hit,r);await s.click(r.x,r.y);await settle();
      check('PER_ROOT_RESTORE_CLEARS_MASK',(await viewState()).hidden.length===0);
      await rightView('front',650,-1200);await ctl(v3('hide'));await openSettings();
      await ctl('[data-v3-layer="rc"]');
      await right(await blankView(),'viewCtxMenu');await ctl(v3('show-all'));await settle();
      check('SHOW_ALL_KEEPS_CATEGORY_OFF',await read(`!document.querySelector('[data-v3-layer="rc"]').checked`)&&(await viewState()).hidden.length===0);
      check('LAYER_INTERSECTION_STILL_HIDES_RC',(await viewState()).snapshot.ops.every(o=>!['column','beam'].includes(o.owner?.kind)));
      await openSettings();await ctl('[data-v3-layer="rc"]');await settle();
      await expectedTarget(await rightView('front',650,-1200),'column',71);await unchanged(before);
    }},
    {id:'W11',run:async()=>{
      await fixture('view');const before=await checkpoint();await rightView('front',650,-1200);
      await read(`window.__r11old=document.querySelector('#viewCtxMenu [data-v3-act="hide"]');void 0`);
      await key('Escape','Escape',27);await rightView('front',2825,-1200);
      console.log('R11_FAULT W11 stale node retained across close/reopen');
      await read('__r11old.click();void 0');await settle();
      check('OLD_OPENING_NODE_CANNOT_HIDE_NEW_TARGET',(await viewState()).hidden.length===0);
      check('ONLY_ONE_SHARED_MENU',await read(`document.querySelectorAll('#viewCtxMenu:not([hidden]),#spaceCtxMenu:not([hidden]),#canvasCtxMenu:not([hidden]),#feCtxMenu:not([hidden])').length===1`));
      await key('Escape','Escape',27);await unchanged(before);
      await rightView('front',650,-1200);await ctl(v3('hide'));await settle();
      console.log('R11_FAULT W11 native revision changed by another owner');
      const mutate=await read(`(async()=>{const a=await apiRequest('line delete column 71');if(!a.ok)return a;
        const b=await apiRequest('line column 71 in 9 at 500 500 size 310 410 z 0 2500');await render();return b;})()`);
      pre('SAME_ID_RECREATED_NATIVE',mutate?.ok===true,mutate);
      await settle();check('REVISION_CHANGE_CLEARS_OLD_MASK',(await viewState()).hidden.length===0);
      await expectedTarget(await rightView('front',650,-1200),'column',71);await key('Escape','Escape',27);
      const p=await viewPoint('front',650,-1200);
      await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x,y:p.y,button:'none'});await settle();
      console.log('R11_FAULT W11 hold real native pick response across viewport change');
      await read(`__r11menu.arm('/view/pick');void 0`);await rawRight(p,false);
      await wait('ACTUAL_NATIVE_PICK_HELD',`__r11menu.held?.phase==='held'`);
      pre('HELD_PICK_WAS_HIT',await read(`__r11menu.held.result?.status==='HIT'`));
      await send('Input.dispatchMouseEvent',{type:'mouseWheel',x:p.x,y:p.y,deltaY:-120,deltaX:0});
      await read('__r11menu.held.release();void 0');await settle();
      check('LATE_PICK_CANNOT_REOPEN_MENU',await read(`$('viewCtxMenu').hidden`));
    }},
    {id:'W12',run:async()=>{
      await fixture('view',390);const before=await checkpoint();await right(await blankView(),'viewCtxMenu');
      check('MOBILE_MENU_CONTAINED',await read(`(()=>{const r=$('viewCtxMenu').getBoundingClientRect();return r.left>=0&&r.top>=0&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1&&document.documentElement.scrollWidth<=innerWidth+1;})()`));
      await unchanged(before);await snap('view-blank-mobile');await key('Escape','Escape',27);
      await read(`$('cv').focus();void 0`);await key('ContextMenu','ContextMenu',93);
      await wait('V3_KEYBOARD_MENU',`!$('viewCtxMenu').hidden`);
      check('TRUSTED_KEYBOARD_MENU_EVENT',await read(`__r11menu.events.some(e=>e.type==='keydown'&&e.key==='ContextMenu'&&e.trusted===true)`));
      await key('Escape','Escape',27);check('KEYBOARD_ESCAPE_CLOSED',await read(`$('viewCtxMenu').hidden`));
      await unchanged(before);
      await fixture('space',390);const spBefore=await checkpoint();await s.rightPlan(650,700);await ctl(s.sp('size'));
      check('MOBILE_SIDE_FORM_REACHABLE',await read(`(()=>{const r=$('rcDialog').getBoundingClientRect();return !$('rcDialog').hidden&&r.left>=0&&r.right<=innerWidth+1&&r.top>=0&&r.bottom<=innerHeight+1&&document.documentElement.scrollWidth<=innerWidth+1;})()`));
      await point('#rcSubmit');await snap('space-size-mobile');await ctl('#rcCancel');await unchanged(spBefore);
    }}
  ];
};
