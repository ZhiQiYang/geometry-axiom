/* PF-6 App first slice. Fixture setup uses the real native HTTP service;
 * every tested PF-6 state change is a trusted mouse/keyboard DOM action.
 * The observer only copies requests/replies. It never changes product state,
 * network results, time, validation, or input. True cold-open is a separate
 * cloud acceptance step: this strict module cannot spawn a service/Chrome.
 */
'use strict';
const {isDeepStrictEqual:same}=require('node:util');

function installObserver() {
  const original=window.fetch;
  const observer={records:[],clicks:[]};
  const click=e=>{
    const el=e.target.closest('[data-pf6-action],[data-pf6-select],[data-pf-action="suggest-timbers"]');
    if(el)observer.clicks.push({trusted:e.isTrusted,action:el.getAttribute('data-pf6-action')||el.getAttribute('data-pf-action'),
      selected:el.getAttribute('data-pf6-select'),open:el.getAttribute('data-pf-fill-id')});
  };
  const wrapper=async(...args)=>{
    const req=new Request(...args),url=new URL(req.url);
    const body=req.method==='POST'?await req.clone().json().catch(()=>null):null;
    const watched=url.pathname.startsWith('/panel-fill/builder/')||
      url.pathname==='/api'&&(body?.cmd?.startsWith('pf6-')||body?.receipt);
    const row={url:url.pathname,body,headers:{version:req.headers.get('X-Geometry-Version'),
      session:req.headers.get('X-Geometry-Session'),requestId:req.headers.get('X-Geometry-Request-Id')}};
    if(watched)observer.records.push(row);
    const response=await original(...args);
    if(watched)row.reply=await response.clone().json().catch(()=>null);
    return response;
  };
  document.addEventListener('click',click,true);window.fetch=wrapper;
  observer.close=()=>{document.removeEventListener('click',click,true);if(window.fetch===wrapper)window.fetch=original;};
  window.__p1286=observer;
}

function pinHistory(key) {
  const h=ReferenceWorkspace.history;
  (window.__p1286History ||= new Map()).set(key,{undo:h.undo.slice(),redo:h.redo.slice(),frame:h.frame,limit:h.limit});
  return key;
}
function historyMatches(key,mode) {
  const h=ReferenceWorkspace.history,b=window.__p1286History.get(key);
  if(!b||h.limit!==b.limit||h.group!==null)return false;
  if(mode==='same')return h.frame===b.frame&&h.undo.length===b.undo.length&&h.redo.length===b.redo.length&&
    h.undo.every((entry,i)=>entry===b.undo.at(i))&&h.redo.every((entry,i)=>entry===b.redo.at(i));
  const retained=b.undo.slice(Math.max(0,b.undo.length+1-b.limit));
  return h.redo.length===0&&h.undo.length===retained.length+1&&
    h.undo.slice(0,-1).every((entry,i)=>entry===retained.at(i))&&!b.undo.includes(h.undo.at(-1));
}

module.exports=async helpers=>{
  const {send,eval_,sleep,click,dblclick,waitForUI,makeCheck,exceptionCount}=helpers;
  const rawCheck=makeCheck({prefix:'P1286 ',throwOnFail:false}),failures=[];
  class AppAssertion extends Error {}
  const check=(name,value,detail)=>{
    rawCheck(name,value,detail);
    if(value!==true){failures.push({kind:'assertion',name:name.split(' ').at(0)});throw new AppAssertion(name);}
  };
  const read=async expression=>{const value=await eval_(expression);if(value?.__err)throw Error(value.__err);return value;};
  const call=(fn,...args)=>read('('+fn.toString()+')('+args.map(value=>JSON.stringify(value)).join(',')+')');
  const wait=expression=>waitForUI(expression,15000);
  const key=async(name,code,vk,modifiers=0)=>{
    for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key:name,code,windowsVirtualKeyCode:vk,modifiers});
  };
  const point=async selector=>{
    let result=null;
    for(let attempt=0;attempt<8;attempt++){
      await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e?.scrollIntoView({block:'nearest',inline:'nearest'});})()`);
      await sleep(50);
      result=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)return null;const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,width:r.width,height:r.height,enabled:!e.disabled,hit:e.contains(document.elementFromPoint(x,y))};})()`);
      if(result?.enabled&&result.hit&&result.width>0&&result.height>0)break;
    }
    return result;
  };
  const ctl=async selector=>{
    await wait('!!document.querySelector('+JSON.stringify(selector)+')');
    const disclosures=[];
    for(let attempt=0;attempt<8;attempt++){
      const summary=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});let closed;for(let p=e?.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS'&&!p.open)closed=p;const s=closed?.querySelector(':scope > summary');if(!s)return null;s.scrollIntoView({block:'nearest'});const r=s.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,hit:s.contains(document.elementFromPoint(x,y))};})()`);
      if(!summary)break;
      disclosures.push(summary);if(!summary.hit)break;
      await click(summary.x,summary.y);await sleep(80);
    }
    const p=await point(selector);
    // One verdict per requested control, regardless of inherited disclosure
    // state. Every summary actually needed and the control must be hittable.
    check('PF6_DOM_CONTROL_REACH '+selector,disclosures.every(summary=>summary.hit)&&!!p&&p.enabled&&p.hit&&p.width>0&&p.height>0,{point:p,disclosures});
    await click(p.x,p.y);await sleep(80);
  };
  const fill=async(selector,value)=>{await ctl(selector);await key('a','KeyA',65,2);await send('Input.insertText',{text:String(value)});await sleep(30);};
  const choose=async(selector,value)=>{
    const index=await read(`[...document.querySelector(${JSON.stringify(selector)}).options].findIndex(option=>option.value===${JSON.stringify(value)})`);
    check('PF6_DOM_OPTION_EXISTS '+selector,index>=0,{value,index});
    await ctl(selector);await key('Home','Home',36);
    for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);
    await key('Enter','Enter',13);await sleep(80);
    check('PF6_DOM_EXPLICIT_VALUE '+selector,await read(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(value)}`));
  };
  const field=name=>'[data-pf6-field='+JSON.stringify(name)+']';
  const action=name=>'[data-pf6-action='+JSON.stringify(name)+']';
  const wire=()=>read('window.__p1286.records');
  const snapshot=()=>read(`(async()=>({world:(await apiRequest('dump')).text,revision:(await apiRequest('panel-fill-read')).revision,
    identity:await apiRequest('identity-read'),nextIds:await apiRequest('newid'),project:ReferenceWorkspace.getProjectState(),
    attachments:ReferenceWorkspace.context().featureAttachments}))()`);
  const last=async path=>(await wire()).filter(row=>row.url===path).at(-1);
  const startExceptions=exceptionCount();
  console.log('=== P1286. PF-6 一般面入口、明選集合與同候選確認 ===');

  async function setup() {
    // Independent fixture: 300 x 300, 100 x 100 panels, gap 3, X=8 mm.
    // No host/grid/timber exists before entering the PF-6 App workflow.
    await read(`(async()=>{resetSceneFocus();await setView3(false);
      for(const command of ['reset','line boundary 8 outline 0,0 300,0 300,300 0,300 kind room_plan']){const r=await apiRequest(command);if(!r.ok)throw Error(JSON.stringify(r));}
      let revision=(await apiRequest('engineering-read')).revision;
      let r=await(await fetch('/engineering/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'engineering-transaction/1',expectedRevision:revision,operations:[
        {op:'publish-material',value:{id:'pf6-app-board',version:1,name:'PF-6 100 毫米板',kind:'panel',width:100,length:100,thickness:'9'}},
        {op:'put-parameter',value:{id:90,name:'PF-6 承接門檻',fields:[{id:1,name:'X',type:'dimension',input:'8'}]}}
      ]})})).json();if(!r.ok||!r.preview.valid)throw Error(JSON.stringify(r));
      r=await apiRequest('engineering-confirm '+r.preview.token);if(!r.ok)throw Error(JSON.stringify(r));
      revision=(await apiRequest('panel-fill-read')).revision;
      r=await(await fetch('/panel-fill/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'panel-fill-transaction/1',expectedRevision:revision,operations:[
        {op:'put-finish-surface',value:{id:1,name:'PF-6 正式完成面',boundaryId:8,frame:{origin:[0,0,0],U:'+X',V:'+Y',N:'+Z'},structureSide:1,obstacles:[]}},
        {op:'put-panel-fill',value:{id:1,finishSurfaceId:1,panel:{id:'pf6-app-board',version:1},lengthAlong:'v',origin:[0,0],gap:3,pattern:'straight',threshold:{parameterId:90,fieldId:1}}}
      ]})})).json();if(!r.ok||!r.preview.valid)throw Error(JSON.stringify(r));
      r=await apiRequest('panel-fill-confirm '+r.preview.token);if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();})()`);
  }
  async function enterFace(width) {
    const selector='.object-row[data-kind="boundary"][data-id="8"]';
    const row=await point(selector),toggle=row?.hit?null:await point('#toggleLeft');
    check('PF6_DOM_OBJECT_LIST_ACCESS',row?.hit===true||!!toggle&&toggle.enabled&&toggle.hit&&toggle.width>0&&toggle.height>0,{row,toggle});
    if(!row?.hit){await click(toggle.x,toggle.y);await sleep(80);}
    await ctl(selector);const p=await point(selector);await dblclick(p.x,p.y);
    await wait('oc.focus?.t==="face"&&oc.focus.id===8');
    if(width<=900)await ctl('#workspaceToggleRight');
    await ctl('[data-fi-tab="prop"]');await ctl('[data-face-settings="8"]');await ctl('[data-panel-fill-open="8"]');
    await wait('!!document.querySelector("[data-pf-workspace=\\"8\\"]")');
    check('PF6_DOM_ENTRY',await read(`document.querySelectorAll('[data-pf-action="suggest-timbers"]').length===1&&!!document.querySelector('[data-pf-action="suggest-timbers"][data-pf-fill-id="1"]')&&!document.querySelector('[data-pf6-open]')`));
  }
  async function openBuilder() {
    await ctl('[data-pf-action="suggest-timbers"][data-pf-fill-id="1"]');
    check('PF6_DOM_ENTRY',await read('!!document.querySelector("[data-pf6-workspace=\\"8\\"]")'));
  }
  async function explicitSources() {
    await choose(field('A.kind'),'literal');await fill(field('A.value'),'27');
    await choose(field('B.kind'),'literal');await fill(field('B.value'),'30');
    await choose(field('primaryAlong'),'u');
  }
  async function suggest() {
    await ctl(action('suggest'));
    await wait('document.querySelectorAll("[data-pf6-select]").length===16');
    const row=await last('/panel-fill/builder/suggest');
    check('PF6_DOM_EXACT_WIRE',row?.body?.schema==='panel-fill-builder-suggest/1'&&
      typeof row.body.expectedRevision==='string'&&same(row.body.pre,[])&&same(row.body.post,[])&&
      same(row.body.input,{fillId:1,A:{kind:'literal',value:27},B:{kind:'literal',value:30},roles:{u:'secondary',v:'primary'}})&&
      !!row.headers.version&&!!row.headers.session&&!!row.headers.requestId,row);
    check('PF6_DOM_EXPLICIT_SET',await read('![...document.querySelectorAll("[data-pf6-select]")].some(e=>e.checked)'));
    return row.reply;
  }
  async function preview() {
    await ctl(action('preview'));
    await wait('!!document.querySelector("[data-pf6-action=\\"confirm\\"]")&&!document.querySelector("[data-pf6-action=\\"confirm\\"]").disabled');
    const row=await last('/panel-fill/builder/select'),suggestion=await last('/panel-fill/builder/suggest');
    check('PF6_DOM_SELECTED_OWNER',row?.reply?.preview?.valid===true&&row.reply.preview.phase==='SELECTED'&&
      Number.isInteger(row.reply.preview.token)&&row.reply.preview.token>0&&row.reply.preview.token<=4294967295&&
      row.reply.preview.candidateIdsAreTemporary===true&&row.reply.preview.idMap===null&&
      row.reply.preview.createdDefinitions.every(def=>same(Object.keys(def).sort(),['candidateId','kind','tempKey']))&&
      typeof row.body.expectedRevision==='string'&&typeof row.body.generation==='string'&&
      typeof row.body.setKey==='string'&&!!row.headers.requestId&&
      row.body.expectedRevision===suggestion.reply.revision&&row.body.setKey===suggestion.reply.setKey&&
      row.body.generation===suggestion.reply.generation&&row.headers.session===suggestion.headers.session,row);
    return row.reply.preview;
  }

  try {
  for(const size of [{width:390,height:844},{width:1400,height:900}]) {
    await send('Emulation.setDeviceMetricsOverride',{...size,deviceScaleFactor:1,mobile:size.width===390});
    await setup();await call(installObserver);
    try {
      await enterFace(size.width);await openBuilder();
      check('PF6_DOM_ENTRY '+size.width,await read('document.querySelectorAll("[data-pf6-workspace]").length===1&&document.querySelectorAll("[data-pf6-action=\\"confirm\\"]").length===1&&!document.querySelector("[data-pf-action=\\"confirm\\"]")'));
      check('PF6_DOM_EXPLICIT_INPUTS '+size.width,await read('document.querySelector("[data-pf6-field=\\"A.kind\\"]").value===""&&document.querySelector("[data-pf6-field=\\"B.kind\\"]").value===""&&document.querySelector("[data-pf6-field=\\"primaryAlong\\"]").value===""'));
      const before=await snapshot(),cancelPin=await call(pinHistory,'cancel-'+size.width);
      await explicitSources();const suggestions=await suggest();
      check('PF6_DOM_SUGGEST_ZERO '+size.width,same(await snapshot(),before)&&await call(historyMatches,cancelPin,'same'));
      await ctl(action('all'));await ctl(action('none'));
      check('PF6_DOM_NONE '+size.width,await read('![...document.querySelectorAll("[data-pf6-select]")].some(e=>e.checked)'));
      await ctl(action('all'));const all=await preview();
      const allIds=new Set(all.createdDefinitions.filter(row=>row.kind==='timber').map(row=>row.candidateId));
      check('PF6_DOM_FULL_SET_ORACLE '+size.width,allIds.size===12&&all.entries.filter(row=>row.selected).length===16,
        {count:allIds.size,entries:all.entries});
      check('PF6_DOM_PREVIEW_ZERO '+size.width,same(await snapshot(),before)&&await call(historyMatches,cancelPin,'same'));
      await ctl(action('cancel'));await wait('!document.querySelector("[data-pf6-workspace]")');
      check('PF6_DOM_CANCEL_ZERO '+size.width,same(await snapshot(),before)&&await call(historyMatches,cancelPin,'same'));
      await openBuilder();await explicitSources();const fresh=await suggest();await ctl(action('all'));
      const omitted=fresh.entries.filter(row=>row.phase==='seam-primary'&&row.source.k==='0');
      check('PF6_DOM_SUBSET_FIXTURE '+size.width,omitted.length===3,omitted);
      for(const row of omitted)await ctl('[data-pf6-select='+JSON.stringify(row.key)+']');
      const selected=await preview(),secondary=selected.entries.filter(row=>row.selected&&row.phase==='seam-secondary');
      const unique=new Set(selected.createdDefinitions.filter(row=>row.kind==='timber').map(row=>row.candidateId));
      check('PF6_DOM_SELECTED_REBUILD '+size.width,unique.size===9&&selected.entries.filter(row=>row.selected).length===13&&
        same(secondary.map(row=>row.geometry.length),['164','164','55','164','164','55'])&&
        !selected.entries.some(row=>row.selected&&omitted.some(old=>old.key===row.key)),{count:unique.size,secondary});
      const texts=await read('[...document.querySelectorAll("[data-pf6-member]")].map(e=>({key:e.getAttribute("data-pf6-member"),text:e.textContent}))');
      check('PF6_DOM_READABLE_VALUES '+size.width,secondary.every(row=>texts.some(text=>text.key===row.key&&text.text.includes(row.geometry.length+' mm')))&&
        await read('document.querySelector("[data-pf6-created-count]").textContent.includes("9")&&document.querySelectorAll("[data-pf6-support]").length>0'),texts);
      const parts=selected.appView.uiContract.after.panelFills.find(fill=>fill.definition.id===1).derived.support;
      const supports=await read('[...document.querySelectorAll("[data-pf6-support]")].map(e=>({key:e.getAttribute("data-pf6-support"),supported:e.getAttribute("data-supported"),text:e.textContent,color:getComputedStyle(e).color}))');
      check('PF6_DOM_READABLE_SUPPORT '+size.width,parts.length===32&&parts.some(row=>row.left==='0'&&row.right==='0')&&
        parts.some(row=>row.left==='12'&&row.right==='12')&&parts.every(row=>supports.some(text=>
          text.key==='after:'+row.seam+':'+row.range.join(':')&&text.supported===String(row.supported)&&
          text.text.includes('左 '+row.left+' mm／右 '+row.right+' mm')&&text.text.includes('X 8/1 mm')&&
          text.text.includes(row.supported?'已承接':'承接不足')&&(row.supported||text.color==='rgb(194, 31, 48)'))),{parts,supports});
      check('PF6_DOM_TEMPORARY_IDS '+size.width,await read(`!document.querySelector('[data-pf6-formal]')&&document.querySelector('.pf6-results').textContent.includes('候選暫號')&&document.querySelector('.pf6-results').textContent.includes('尚未正式建立')`));
      check('PF6_DOM_NARROW_LAYOUT '+size.width,await read('(()=>{const e=document.querySelector("[data-pf6-workspace]");return e.scrollWidth<=e.clientWidth+1&&e.getBoundingClientRect().width<=innerWidth;})()'));
      const confirmPin=await call(pinHistory,'confirm-'+size.width);
      await ctl(action('confirm'));await wait('!!document.querySelector("[data-pf6-status=\\"committed\\"]")');
      const after=await snapshot(),confirms=(await wire()).filter(row=>row.body?.cmd?.startsWith('pf6-confirm '));
      check('PF6_DOM_CONFIRM_ONCE '+size.width,confirms.length===1&&typeof confirms.at(0).body.requestId==='string'&&
        confirms.at(0).body.cmd==='pf6-confirm '+String(selected.token)&&
        confirms.at(0).body.session===(await last('/panel-fill/builder/select')).headers.session&&
        await call(historyMatches,confirmPin,'single')&&after.world!==before.world&&after.revision===before.revision+1,confirms);
      const formal=confirms.at(0).reply.actionReceipt?.idMap,shownIds=await read(`[...document.querySelectorAll('[data-pf6-formal]')].map(e=>e.getAttribute('data-pf6-formal'))`);
      check('PF6_DOM_FORMAL_RECEIPT_IDS '+size.width,Array.isArray(formal)&&formal.length===selected.createdDefinitions.length&&
        same(formal.map(row=>row.kind+':'+row.id),shownIds)&&formal.every(row=>same(Object.keys(row).sort(),['id','kind','tempKey']))&&
        await read(`document.querySelector('.pf6-results').textContent.includes('正式識別')`),{formal,shownIds});
      check('PF6_DOM_ORDINARY_DEFINITIONS '+size.width,['derived-placement ','from-fill','timber ','at-line '].every(text=>after.world.includes(text))&&
        !/setKey|generation|pf6-suggest|pf6-select|pf6-confirm/.test(after.world)&&same(after.attachments,before.attachments));
      await ctl(action('close'));await ctl('#faceUndoButton');await wait('!oc.busy&&!ReferenceWorkspace.busy');
      check('PF6_DOM_UNDO '+size.width,(await snapshot()).world===before.world&&same((await snapshot()).attachments,before.attachments));
      await ctl('#faceRedoButton');await wait('!oc.busy&&!ReferenceWorkspace.busy');
      check('PF6_DOM_REDO '+size.width,(await snapshot()).world===after.world&&same((await snapshot()).attachments,after.attachments));
      check('PF6_DOM_TRUSTED_ACTIONS '+size.width,await read('window.__p1286.clicks.length>0&&window.__p1286.clicks.every(e=>e.trusted===true)'));
      check('PF6_DOM_FRESH_SUGGESTION '+size.width,fresh.setKey!==suggestions.setKey&&
        typeof suggestions.generation==='string'&&typeof fresh.generation==='string'&&fresh.generation!==suggestions.generation);
      await ctl('#workspaceBackButton');await wait('!oc.focus');
    } finally {
      await read('window.__p1286?.close();delete window.__p1286;delete window.__p1286History;void 0');
    }
  }
  check('PF6_DOM_NO_EXCEPTIONS',exceptionCount()===startExceptions);
  } catch(error) {
    // Only an assertion already recorded by makeCheck ends this module with
    // an honest completed red result. Fixture, transport and timeout errors
    // propagate to the driver and cannot count as a killed withdrawal.
    if(!(error instanceof AppAssertion))throw error;
  }
  console.log('P1286_SUITE_RESULT '+JSON.stringify({case:'P1286',status:failures.length?'failed':'passed',failures}));
  console.log('PF6_APP_BROWSER_SCOPE '+JSON.stringify({schema:'pf6-app-browser-scope/1',
    viewportCases:['390x844','1400x900'],fixture:'300x300 / panels100x100 / gap3 / A27 B30 / X8',
    actualAppActions:'entry, explicit sources, suggestions, all/none/subset, preview, cancel, confirm, undo, redo',
    coldOpen:'not run by strict module; requires a fresh native service and browser process/profile',
    unverified:['fresh .gcanvas cold-open','Windows dialogs','physical touch','physical IME','derived-host object canvas/face canvas/parameter usage (package A)']}));
};
