/* PF-5 V: native service + ordinary face entry + real CDP input.
 * API writes below are explicitly fixture setup. Every tested edit, preview,
 * cancel, confirmation and view navigation uses an existing visible control.
 * No A-package property, synthetic click, handler replacement or geometry
 * callback is used. This module writes no golden or browser evidence file.
 */
'use strict';
const {isDeepStrictEqual:same}=require('node:util');
const {randomUUID}=require('node:crypto');
const {waitForExpectedNavigation}=require('../cdp_navigation.js');
module.exports=async helpers=>{
  const {send,eval_,sleep,click,dblclick,waitForUI,makeCheck,exceptionCount}=helpers;
  const check=makeCheck({prefix:'P1285 ',throwOnFail:true}),initialExceptions=exceptionCount();
  const read=async expression=>{const r=await eval_(expression);if(r?.__err)throw Error('P1285 browser evaluation: '+r.__err);return r;};
  const call=(fn,...args)=>read('('+fn.toString()+')('+args.map(v=>JSON.stringify(v)).join(',')+')');
  const wait=expression=>waitForUI(expression,15000);
  const field=name=>'[data-pf-field='+JSON.stringify(name)+']',action=name=>'[data-pf-action='+JSON.stringify(name)+']';
  const key=async(name,code,vk,modifiers=0)=>{
    for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key:name,code,windowsVirtualKeyCode:vk,modifiers});
  };
  const painted=()=>read('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))');
  const point=selector=>call(selector=>{
    const e=document.querySelector(selector);if(!e)return {exists:false};
    const r=e.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2,h=document.elementFromPoint(x,y);
    return {exists:true,x,y,width:r.width,height:r.height,disabled:!!e.disabled,hit:e.contains(h),hitElement:h?.tagName+'#'+h?.id};
  },selector);
  const usable=p=>p.exists&&p.width>0&&p.height>0&&!p.disabled&&p.hit;
  async function reachable(selector){
    let p;
    for(let i=0;i<8;i++){
      await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'center',inline:'nearest'});void 0`);
      await sleep(50);p=await point(selector);if(usable(p))return p;
    }
    throw Error('P1285 control unreachable '+selector+' '+JSON.stringify(p));
  }
  async function ctl(selector){
    await wait('!!document.querySelector('+JSON.stringify(selector)+')');
    for(let i=0;i<8;i++){
      const closed=await call(async selector=>{const e=document.querySelector(selector);let ancestor=null;for(let p=e?.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS'&&!p.open)ancestor=p;const summary=ancestor?.querySelector(':scope > summary');if(!summary)return null;summary.scrollIntoView({block:'center'});await new Promise(resolve=>requestAnimationFrame(resolve));const r=summary.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2;return {x,y,hit:summary.contains(document.elementFromPoint(x,y))};},selector);
      if(!closed)break;if(!closed.hit)throw Error('P1285 closed details summary is obstructed '+selector);await click(closed.x,closed.y);await sleep(80);
    }
    const p=await reachable(selector);await click(p.x,p.y);await sleep(80);
  }
  async function fill(selector,value){await ctl(selector);await key('a','KeyA',65,2);await send('Input.insertText',{text:String(value)});await sleep(30);}
  async function choose(selector,value){
    const index=await read(`[...document.querySelector(${JSON.stringify(selector)}).options].findIndex(o=>o.value===${JSON.stringify(String(value))})`);
    if(index<0)throw Error('P1285 missing explicit option '+selector+' '+value);
    await ctl(selector);await key('Home','Home',36);for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);await key('Enter','Enter',13);await sleep(80);
    if(!await read(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(String(value))}`))throw Error('P1285 native select did not accept '+value);
  }
  const phase=name=>'!!document.querySelector(\'[data-pf-status="'+name+'"]\')';
  const wire=()=>read('window.__pf5Wire.records');
  const official=()=>read("apiRequest('panel-fill-read')");
  const snapshot=()=>read(`(async()=>{const r=await apiRequest('panel-fill-read');return {dump:(await apiRequest('dump')).text,revision:r.revision,state:r.state,project:ReferenceWorkspace.getProjectState()};})()`);
  async function pinHistory(){return read(`(()=>{const h=ReferenceWorkspace.history;window.__pf5History={undo:h.undo.slice(),redo:h.redo.slice(),frame:h.frame,limit:h.limit};return true;})()`);}
  const unchangedHistory=()=>read(`(()=>{const h=ReferenceWorkspace.history,b=window.__pf5History,same=(a,z)=>a.length===z.length&&a.every((e,i)=>e===z[i]);return h.frame===b.frame&&h.limit===b.limit&&same(h.undo,b.undo)&&same(h.redo,b.redo);})()`);
  const singleHistory=()=>read(`(()=>{const h=ReferenceWorkspace.history,b=window.__pf5History,retained=b.undo.slice(Math.max(0,b.undo.length+1-b.limit));return h.limit===b.limit&&h.group===null&&h.redo.length===0&&h.undo.length===Math.min(b.undo.length+1,b.limit)&&h.undo.length===retained.length+1&&h.undo.slice(0,-1).every((e,i)=>e===retained[i])&&!b.undo.includes(h.undo.at(-1));})()`);
  async function fixture(kind,width){
    return call(async(kind,width)=>{
      // Independent fixture construction: explicit source values, no defaults.
      resetSceneFocus();await setView3(false);const reset=await apiRequest('reset');if(!reset.ok)throw Error(JSON.stringify(reset));
      const fresh=await apiRequest('newid 3');if(!fresh.ok||fresh.surfaces.length!==3)throw Error('P1285 fixture requires native fresh surface ids');
      const before=await apiRequest('objects'),placed=await apiRequest('surfaces'),occupied=new Set([...before.faces,...placed.surfaces].map(o=>o.id));
      if(new Set(fresh.surfaces).size!==3||fresh.surfaces.some(id=>occupied.has(id)))throw Error('P1285 native newid collided with the existing scene');
      const outlines=kind==='flat'?['0,0 100,0 100,100 0,100']:['0,0 31,0 31,100 0,100','31,0 69,0 69,100 31,100','0,0 100,0 100,139 0,139'];
      for(let i=0;i<outlines.length;i++){
        const r=await apiRequest('line boundary '+fresh.surfaces.at(i)+' outline '+outlines.at(i)+' kind room_plan');if(!r.ok)throw Error(JSON.stringify(r));
      }
      const beam=fresh.beam,widthY=kind==='flat'?60:100;
      const made=await apiRequest('line beam '+beam+' along x from 40 to 60 at 50 width '+widthY+' depth 500 top 3000');if(!made.ok)throw Error(JSON.stringify(made));
      async function apply(kind,operations){
        const revision=(await apiRequest('panel-fill-read')).revision;
        const response=await fetch('/'+kind+'/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:kind+'-transaction/1',expectedRevision:revision,operations})});
        const p=await response.json();if(!p.ok||!p.preview.valid)throw Error('P1285 fixture '+JSON.stringify(p));
        const done=await apiRequest(kind+'-confirm '+p.preview.token);if(!done.ok)throw Error(JSON.stringify(done));
      }
      const material='pf5-'+kind+'-'+width,parameter=fresh.parameter;
      await apply('engineering',[
        {op:'publish-material',value:{id:material,version:1,name:'PF5 明設測試板',kind:'panel',width:100,length:100,thickness:'9'}},
        {op:'put-parameter',value:{id:parameter,name:'PF5 明設門檻',fields:[{id:1,name:'X',type:'dimension',input:'8'}]}}
      ]);
      const records=[];
      if(kind==='step'){
        const frames=[{origin:[0,0,2600],U:'+X',V:'+Y',N:'+Z'},{origin:[0,0,2461],U:'+X',V:'+Y',N:'+Z'},{origin:[31,0,2461],U:'+Y',V:'+Z',N:'+X'}];
        for(let i=0;i<frames.length;i++){
          // Allocate each typed identity after the prior fixture is committed.
          const ids=await apiRequest('newid'),bid=fresh.surfaces.at(i),finish=ids.finishSurface,fill=ids.panelFill,host=ids.placement;
          await apply('panel-fill',[
            {op:'put-finish-surface',value:{id:finish,name:['明設主天花','明設樑底面','明設側封'].at(i),boundaryId:bid,frame:frames.at(i),structureSide:1,obstacles:['b'+beam]}},
            {op:'put-panel-fill',value:{id:fill,finishSurfaceId:finish,panel:{id:material,version:1},lengthAlong:'u',origin:[0,0],gap:0,pattern:'straight',threshold:{parameterId:parameter,fieldId:1}}},
            {op:'put-derived-placement',value:{id:host,fillId:fill,h:30}}
          ]);records.push({bid,finish,fill,host});
        }
      }
      await renderObjects();return {kind,width,bid:fresh.surfaces.at(kind==='flat'?0:2),beam,material,parameter,records,freshSurfaces:fresh.surfaces};
    },kind,width);
  }
  async function enterPF(f,width){
    const selector='.object-row[data-kind="boundary"][data-id="'+f.bid+'"]';
    // A closed mobile library and a selected inspector are ordinary drawers;
    // use their visible toggle, never remove overlays or change CSS to enter.
    if(width===390&&await read("document.body.classList.contains('drawer-right-open')"))await ctl('#toggleRight');
    if(width===390&&!await read("document.body.classList.contains('drawer-left-open')"))await ctl('#toggleLeft');
    if(width===1400&&await read("document.body.classList.contains('canvas-library-collapsed')"))await ctl('#btnCollapseLibrary');
    await ctl('#searchInput');await key('a','KeyA',65,2);await key('Backspace','Backspace',8);await ctl('#filterAll');
    await ctl(selector);const p=await reachable(selector);
    check('PF5_ENTRY_FACE_HIT '+width,usable(p),{id:f.bid,point:p,freshSurfaces:f.freshSurfaces});
    await dblclick(p.x,p.y);await wait(`oc.focus?.t==='face'&&oc.focus.id===${f.bid}&&!!document.querySelector('[data-face-settings="${f.bid}"]')`);
    if(width===390&&!await read("document.body.classList.contains('drawer-right-open')"))await ctl('#workspaceToggleRight');
    await ctl('[data-fi-tab="prop"]');await ctl('[data-face-settings="'+f.bid+'"]');await ctl('[data-panel-fill-open="'+f.bid+'"]');await wait(phase('editing'));
    const r=await official();
    check('PF5_BROWSER_NATIVE_SPATIAL_PRESENT '+width,r.spatial?.schema==='panel-fill-spatial/1'&&
      await read(`!!document.querySelector('[data-pf-workspace="${f.bid}"] [data-pf5-spatial]')`),{schema:r.spatial?.schema,unavailable:await read("document.querySelector('[data-pf5-unavailable]')?.textContent")});
  }
  async function createFlat(f){
    await fill(field('name'),'PF5 明選 2480 mm');
    for(const [name,value] of [['origin.0',0],['origin.1',0],['origin.2',2480]])await fill(field(name),value);
    for(const [name,value] of [['U','+X'],['V','+Y'],['N','+Z'],['side','1']])await choose(field(name),value);
    await ctl('[data-pf-obstacle="b'+f.beam+'"]');await ctl(field('fill'));await choose(field('panel'),JSON.stringify([f.material,1]));
    await choose(field('lengthAlong'),'u');await fill(field('fillOrigin.0'),0);await fill(field('fillOrigin.1'),0);
    await choose(field('pattern'),'straight');await choose(field('threshold'),f.parameter+':1');await fill(field('gap.value'),0);
    await ctl(field('host'));check('PF5_EXPLICIT_H_BLANK '+f.width,await read(`document.querySelector('[data-pf-field="h.value"]').value===''`));await fill(field('h.value'),30);
  }
  async function preview(width){
    const before=(await wire()).filter(r=>r.url==='/panel-fill/preview').length;await ctl(action('preview'));await wait(phase('confirmable'));
    const requests=(await wire()).filter(r=>r.url==='/panel-fill/preview'),row=requests.at(-1),p=row?.reply?.preview;
    check('PF5_PREVIEW_NATIVE_OWNER '+width,requests.length===before+1&&p?.valid===true&&p.uiContract.completeForScope===true&&
      p.spatial?.after?.schema==='panel-fill-spatial/1'&&await read("!!document.querySelector('[data-pf5-spatial]')&&!document.querySelector('[data-pf5-unavailable]')"),row);
    return p;
  }
  function exactLayer(f,height,panel,timber,panelRelation,timberRelation,width){
    check('PF5_Q47_LAYER_VALUES '+height+' '+width,same(f.frame.origin,['0','0',String(height)])&&f.thickness==='9'&&f.h==='30'&&
      same(f.panel.interval,['0','9'])&&same(f.timber.interval,['9','39'])&&f.panel.area===String(panel)&&f.timber.area===String(timber)&&
      f.obstacles.at(0).panel===panelRelation&&f.obstacles.at(0).timber===timberRelation&&same(f.host.frame.origin,['0','0',String(height+9)]),f);
  }
  const pathData=r=>[r.outer,...r.holes].map(ring=>'M '+ring.map(p=>p.join(' ')).join(' L ')+' Z').join(' ');
  async function inspectDiagrams(native,width,name){
    for(const axis of ['top','front','side']){
      const selector='[data-pf5-view="'+axis+'"] svg';await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'center',inline:'nearest'});void 0`);await painted();
      const observed=await call(selector=>{
        const svg=document.querySelector(selector);if(!svg)return {exists:false};
        const r=svg.getBoundingClientRect(),center={x:r.left+r.width/2,y:r.top+r.height/2};
        let left=Math.max(0,r.left),right=Math.min(innerWidth,r.right),top=Math.max(0,r.top),bottom=Math.min(innerHeight,r.bottom);
        for(let p=svg.parentElement;p;p=p.parentElement){const s=getComputedStyle(p),b=p.getBoundingClientRect();
          if(/auto|scroll|hidden|clip/.test(s.overflowX)){left=Math.max(left,b.left+p.clientLeft);right=Math.min(right,b.left+p.clientLeft+p.clientWidth);}
          if(/auto|scroll|hidden|clip/.test(s.overflowY)){top=Math.max(top,b.top+p.clientTop);bottom=Math.min(bottom,b.top+p.clientTop+p.clientHeight);}
        }
        return {exists:true,rect:{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height},clip:{left,right,top,bottom},
          hit:svg.contains(document.elementFromPoint(center.x,center.y)),documentWidth:document.documentElement.scrollWidth,viewport:innerWidth,
          paths:[...svg.querySelectorAll('path[data-pf5-fill]')].map(e=>({fill:Number(e.dataset.pf5Fill),layer:e.dataset.pf5Layer,component:Number(e.dataset.pf5Component),depth:e.dataset.pf5Depth,d:e.getAttribute('d')})),
          obstacles:[...svg.querySelectorAll('[data-pf5-rc]')].map(e=>e.dataset.pf5Rc)};
      },selector);
      const expected=native.finishes.flatMap(f=>['panel','timber'].flatMap(layer=>(new Map(Object.entries(f)).get(layer)?.components||[]).flatMap((c,component)=>
        ['near','far'].map(depth=>({fill:f.id,layer,component,depth,d:pathData(new Map(Object.entries(new Map(Object.entries(c.projections)).get(axis))).get(depth))})))));
      console.log('P1285_LAYOUT '+JSON.stringify({width,case:name,view:axis,observation:observed}));
      check('PF5_NATIVE_PROJECTION_PATHS '+name+' '+axis+' '+width,same(observed.paths,expected)&&
        same([...new Set(native.finishes.flatMap(f=>f.obstacles.map(o=>o.ref)))].sort(),observed.obstacles.slice().sort()),{actual:observed.paths,expected});
      check('PF5_PROJECTION_VISIBLE '+name+' '+axis+' '+width,observed.exists&&observed.rect.width>=180&&observed.rect.height>=180&&observed.hit&&
        observed.clip.right-observed.clip.left>=observed.rect.width-1&&observed.clip.bottom-observed.clip.top>=observed.rect.height-1&&
        observed.documentWidth<=observed.viewport+1,observed);
    }
  }
  async function closeAndView(width,formal,beam){
    await ctl(action('close'));
    if(width===390&&await read("document.body.classList.contains('drawer-right-open')"))await ctl('#workspaceToggleRight');
    await ctl('#workspaceBackButton');await wait('!oc.focus');await ctl('#btnObj');await wait("view3===true&&!!WorkspaceView.state({kind:'project'}).snapshot");
    const ids=formal.finishes.map(f=>f.hostId);
    const visible=await call((ids,beam)=>{
      const groups=[...document.querySelectorAll('#world > g[data-view-id]')].filter(g=>!g.classList.contains('v3-annotation-layer'));
      return groups.map(g=>({view:g.dataset.viewId,hosts:ids.map(id=>({id,polygons:[...g.querySelectorAll('polygon[data-owner-kind="placement"][data-owner-id="'+id+'"]')].map(p=>p.getAttribute('points').split(/\s+/).map(Number))})),
        beam:[...g.querySelectorAll('polygon[data-owner-kind="beam"][data-owner-id="'+beam+'"]')].map(p=>p.getAttribute('points').split(/\s+/).map(Number))}));
    },ids,beam);
    check('PF5_EXISTING_THREE_VIEW_FRAMES '+width,same(visible.map(v=>v.view),['front','side','bottom']),visible);
    for(const group of visible){
      for(const f of formal.finishes){
        const projection=group.view==='bottom'?'top':group.view;
        const loops=f.timber.components.flatMap(c=>{const p=new Map(Object.entries(c.projections)).get(projection).near;return [p.outer,...p.holes];});
        // Existing D4 rendering may use another start vertex/winding. Compare
        // the complete point multiset per ring, preserving every hole/part.
        const normalized=values=>values.map(p=>{const points=[];for(let i=0;i<p.length;i+=2)points.push([p.at(i),p.at(i+1)].join(','));return points.sort().join(';');}).sort();
        const expected=loops.map(r=>r.flatMap(p=>[Number(p.at(0)),Number(p.at(1))*(group.view==='bottom'?1:-1)]));
        const actual=group.hosts.find(h=>h.id===f.hostId)?.polygons;
        check('PF5_EXISTING_HOST_WORLD_LOOPS '+group.view+' '+f.id+' '+width,same(normalized(actual||[]),normalized(expected)),{actual,expected});
      }
      const points=group.beam.flatMap(p=>{const output=[];for(let i=0;i<p.length;i+=2)output.push([p.at(i),p.at(i+1)]);return output;});
      const xs=points.map(p=>p.at(0)),ys=points.map(p=>p.at(1));
      const bounds=[Math.min(...xs),Math.min(...ys),Math.max(...xs),Math.max(...ys)];
      const expected=group.view==='front'?[40,-3000,60,-2500]:group.view==='side'?[0,-3000,100,-2500]:[40,0,60,100];
      check('PF5_EXISTING_BEAM_WORLD_BOUNDS '+group.view+' '+width,points.length>0&&same(bounds,expected),{bounds,expected});
    }
    const canvas=await point('#cv');check('PF5_EXISTING_THREE_VIEW_CANVAS_HIT '+width,usable(canvas),canvas);
    await ctl('#btnCanvasView');await wait('!view3&&oc.on');
  }
  console.log('=== P1285. PF-5 明設完成面雙層與交界真入口 ===');
  // WorkspaceView's presentation/layers are deliberately not stored in the
  // project. Recreate the document before fixture setup so this independent
  // section cannot inherit a prior module's focused view or hidden layer.
  // The existing navigation helper keeps its original 12 second deadline.
  const marker='P1285-'+randomUUID(),injected=await send('Page.addScriptToEvaluateOnNewDocument',{
    source:'window.__cdpExpectedNavigationMarker='+JSON.stringify(marker)+';'});
  try{
    await send('Page.reload',{});
    await waitForExpectedNavigation({evaluate:read,marker,label:'P1285 isolated fixture document',
      condition:"typeof apiRequest==='function'&&typeof oc==='object'&&typeof ReferenceWorkspace!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy&&ReferenceWorkspace.getProjectInfo().recovery.state!=='pending'"});
  }finally{await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:injected.result.identifier});}
  await read(`(()=>{const original=window.fetch,wire=window.__pf5Wire={records:[],original};window.fetch=async(...args)=>{const request=new Request(...args),url=new URL(request.url),body=request.method==='POST'?await request.clone().json().catch(()=>null):null,watch=url.pathname==='/panel-fill/preview'||url.pathname==='/api'&&body?.cmd?.startsWith('panel-fill-'),row={url:url.pathname,body};if(watch)wire.records.push(row);const response=await original.apply(window,args);if(watch)row.reply=await response.clone().json().catch(()=>null);return response;};})()`);
  try{
    for(const width of [1400,390]){
      await send('Emulation.setDeviceMetricsOverride',{width,height:width===390?844:900,deviceScaleFactor:1,mobile:width===390});await painted();
      const flat=await fixture('flat',width);await enterPF(flat,width);
      check('PF5_NO_DEFAULT_PHYSICAL_VALUES '+width,await read(`['origin.0','origin.1','origin.2','U','V','N','side'].every(name=>document.querySelector('[data-pf-field="'+name+'"]').value==='')&&!document.querySelector('[data-pf-field="fill"]').checked&&!document.querySelector('[data-pf-field="host"]')`));
      await createFlat(flat);const baseline=await snapshot();await pinHistory();const p=await preview(width);
      exactLayer(p.spatial.after.finishes.at(0),2480,10000,8800,'clear','cut',width);
      check('PF5_PREVIEW_ZERO_WORLD '+width,same(await snapshot(),baseline)&&await unchangedHistory());
      await inspectDiagrams(p.spatial.after,width,'Q47-2480');
      await ctl(action('cancel'));check('PF5_CANCEL_ZERO_WORLD '+width,same(await snapshot(),baseline)&&await unchangedHistory());
      await ctl('[data-face-settings="'+flat.bid+'"]');await ctl('[data-panel-fill-open="'+flat.bid+'"]');await wait(phase('editing'));
      await createFlat(flat);await preview(width);const beforeCommit=await official();await pinHistory();
      await ctl(action('confirm'));await wait(phase('committed'));const committed=await official();
      check('PF5_CONFIRM_ONE_HISTORY '+width,committed.revision===beforeCommit.revision+1&&await singleHistory()&&committed.spatial.finishes.length===1&&
        same(committed.spatial.finishes.at(0).host.frame.origin,['0','0','2489']),committed.spatial);
      const formal=await snapshot();await pinHistory();
      for(const [height,panel,timber,panelRelation,timberRelation] of [[2491,10000,8800,'touch','cut'],[2461,10000,10000,'clear','touch'],[2600,8800,8800,'cut','cut']]){
        await fill(field('origin.2'),height);const candidate=await preview(width);
        exactLayer(candidate.spatial.after.finishes.at(0),height,panel,timber,panelRelation,timberRelation,width);
        check('PF5_HEIGHT_PREVIEW_ZERO_WORLD '+height+' '+width,same(await snapshot(),formal)&&await unchangedHistory());
      }
      await ctl(action('cancel'));check('PF5_HEIGHT_CANCEL_ZERO_WORLD '+width,same(await snapshot(),formal)&&await unchangedHistory());
      if(width===390&&await read("document.body.classList.contains('drawer-right-open')"))await ctl('#workspaceToggleRight');
      await ctl('#workspaceBackButton');await wait('!oc.focus');
      const step=await fixture('step',width);await enterPF(step,width);const stepPin=await snapshot();await pinHistory();
      await fill(field('name'),'明選側封，接法未選');const candidate=await preview(width),spatial=candidate.spatial.after;
      check('PF5_EXPLICIT_STEP_AREAS '+width,same(spatial.finishes.map(f=>[f.panel.area,f.timber.area]),[['3100','3100'],['3800','3800'],['13900','3900']])&&spatial.finishes.length===3,spatial.finishes);
      const low=step.records.at(1).fill,side=step.records.at(2).fill,j=spatial.junctions.find(j=>same(j.finishes,[low,side]));
      check('PF5_EXPLICIT_STEP_JOIN_UNSELECTED '+width,j?.layers?.['panel-panel']?.volume==='8100'&&j.joinPolicy==='unselected'&&j.minimumL1Gap==='0'&&
        j.sharedEdges.some(e=>e.length==='100'&&same(e.start,['31','0','2461'])&&same(e.end,['31','100','2461']))&&
        spatial.junctions.every(j=>j.joinPolicy==='unselected'),j);
      check('PF5_STEP_PREVIEW_ZERO_WORLD '+width,same(await snapshot(),stepPin)&&await unchangedHistory());
      await inspectDiagrams(spatial,width,'explicit-step');
      await ctl(action('cancel'));check('PF5_STEP_CANCEL_ZERO_WORLD '+width,same(await snapshot(),stepPin)&&await unchangedHistory());
      await ctl('[data-face-settings="'+step.bid+'"]');await ctl('[data-panel-fill-open="'+step.bid+'"]');await wait(phase('editing'));
      await closeAndView(width,(await official()).spatial,step.beam);
    }
    check('PF5_BROWSER_EXCEPTIONS',exceptionCount()===initialExceptions,{before:initialExceptions,after:exceptionCount()});
  }finally{
    await read(`(()=>{if(window.__pf5Wire){window.fetch=window.__pf5Wire.original;delete window.__pf5Wire;}delete window.__pf5History;return true;})()`);
    await send('Emulation.setDeviceMetricsOverride',{width:1382,height:804,deviceScaleFactor:1,mobile:false});
  }
};
