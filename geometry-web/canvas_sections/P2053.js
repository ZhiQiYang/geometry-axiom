/* R03B: strict canvas module. Setup uses native commands; all recipe/source
 * selection, preview, cancellation, confirmation and history use trusted UI.
 * Expected geometry is generated from the independent unchanged oracle.
 * Archive ZIP / new native process cold-open are separate Node/native gates;
 * this module does not use filesystem or change the strict driver boundary.
 */
'use strict';
const fixture=require('../../tests/fixtures/framing_template_notch_canvas.json');
const {isDeepStrictEqual:same}=require('node:util');
module.exports=async helpers=>{
  const {send,eval_,click,dblclick,waitForUI,makeCheck,exceptionCount}=helpers;
  const judge=makeCheck({prefix:'P2053 ',throwOnFail:true}),seen=new Set(),initialExceptions=exceptionCount();
  const read=async expression=>{const value=await eval_(expression);if(value?.__err)throw Error(value.__err);return value;};
  const wait=expression=>waitForUI(expression,15000),settle=()=>read('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))');
  const field=name=>'[data-ft-field='+JSON.stringify(name)+']',action=name=>'[data-ft-action='+JSON.stringify(name)+']',phase=name=>`!!document.querySelector('[data-ft-status="${name}"]')`;
  const normalize=rows=>rows.map(row=>JSON.stringify(row)).sort();
  const key=async(name,code,vk,modifiers=0)=>{for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key:name,code,windowsVirtualKeyCode:vk,modifiers});};
  async function ctl(selector){
    await wait(`!!document.querySelector(${JSON.stringify(selector)})`);
    await read(`document.querySelector(${JSON.stringify(selector)}).scrollIntoView({block:'nearest',inline:'nearest'});void 0`);await settle();
    await wait(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect();return !!r&&r.width>0&&r.height>0&&!e.disabled&&e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})()`);
    const point=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);await click(point.x,point.y);await settle();
  }
  async function choose(selector,value){
    const index=await read(`[...document.querySelector(${JSON.stringify(selector)}).options].findIndex(option=>option.value===${JSON.stringify(String(value))})`);
    if(index<0)throw Error('R03B_OPTION_MISSING '+selector+' '+value);
    await ctl(selector);await key('Home','Home',36);for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);await key('Enter','Enter',13);
    await wait(`document.querySelector(${JSON.stringify(selector)})?.value===${JSON.stringify(String(value))}`);
  }
  async function fill(selector,value){await ctl(selector);await key('a','KeyA',65,2);await send('Input.insertText',{text:String(value)});await settle();}
  async function enter(bid,optionCheck=null,expectedPhase='ready'){
    if(await read(`innerWidth<=900&&document.querySelector('#toggleLeft')?.getAttribute('aria-expanded')==='false'`))await ctl('#toggleLeft');
    const selector=`.object-row[data-kind="boundary"][data-id="${bid}"]`;await ctl(selector);
    const point=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);await dblclick(point.x,point.y);await wait(`oc.focus?.t==='face'&&oc.focus.id===${bid}`);
    if(await read(`innerWidth<=900&&document.querySelector('#workspaceToggleRight')?.getAttribute('aria-expanded')==='false'`))await ctl('#workspaceToggleRight');
    await ctl('[data-fi-tab="prop"]');await ctl(`[data-face-settings="${bid}"]`);await ctl(`[data-panel-fill-open="${bid}"]`);await wait(`!!document.querySelector('[data-face-product-mode]:not(:disabled)')`);
    if(optionCheck)optionCheck('TEMPLATE_OPTION',await read(`[...document.querySelector('[data-face-product-mode]').options].some(option=>option.value==='framing-notch')`));
    await choose('[data-face-product-mode]','framing-notch');await wait(expectedPhase==='settled'?phase('ready')+'||'+phase('rejected'):phase(expectedPhase));
  }
  async function hideFaceDrawer(){if(await read(`innerWidth<=900&&document.body.classList.contains('drawer-right-open')`))await ctl('#workspaceToggleRight');}
  async function leave(){await ctl(action('close'));await hideFaceDrawer();await ctl('#workspaceBackButton');await wait('!oc.focus');}
  async function sources(on){await choose(field('on'),on);await choose(field('panel'),'["r03b-canvas-board",1]');await choose(field('threshold'),'90:1');await ctl(field('materials'));}
  const wire=()=>read('__p2053.records'),snapshot=()=>read(`(async()=>({world:(await apiRequest('dump')).text,recipe:ReferenceWorkspace.readFeatureAttachment(GeometryFramingRecipes.KIND),revision:ReferenceWorkspace.getProjectState().revision}))()`);
  async function capture(name){return read(`(()=>{const h=ReferenceWorkspace.history;__p2053.history.set(${JSON.stringify(name)},{undo:h.undo.slice(),redo:h.redo.slice(),limit:h.limit,frame:h.frame});return ${JSON.stringify(name)};})()`);}
  const unchanged=name=>read(`(()=>{const h=ReferenceWorkspace.history,b=__p2053.history.get(${JSON.stringify(name)}),eq=(a,z)=>a.length===z.length&&a.every((entry,i)=>entry===z.at(i));return h.limit===b.limit&&h.frame===b.frame&&eq(h.undo,b.undo)&&eq(h.redo,b.redo);})()`);
  const single=name=>read(`(()=>{const h=ReferenceWorkspace.history,b=__p2053.history.get(${JSON.stringify(name)}),retained=b.undo.slice(Math.max(0,b.undo.length+1-h.limit));return h.limit===b.limit&&h.group===null&&h.redo.length===0&&h.undo.length===Math.min(b.undo.length+1,h.limit)&&h.undo.length===retained.length+1&&h.undo.slice(0,-1).every((entry,i)=>entry===retained.at(i))&&!b.undo.includes(h.undo.at(-1));})()`);
  async function preview(){await ctl(action('preview'));await wait(phase('confirmable'));return (await wire()).filter(row=>row.url==='/framing-template/preview').at(-1);}
  console.log('=== P2053. R03 政策 A 單一凹角 L 形第一片 ===');
  for(const size of [{width:1400,height:1000},{width:390,height:844}]){
    const check=(name,value,detail)=>{const id=size.width+' '+name;if(seen.has(id))throw Error('R03B_DUPLICATE_ASSERTION '+id);seen.add(id);judge(id,value,detail);};
    await send('Emulation.setDeviceMetricsOverride',{...size,deviceScaleFactor:1,mobile:size.width<=560});await settle();
    const vertices=fixture.room.map(point=>point.join(',')).join(' ');
    await read(`(async()=>{resetSceneFocus();await setView3(false);for(const cmd of ['reset',${JSON.stringify('line surface 1 origin 0 0 2500 u +x v +y outline '+vertices)},'line surface 2 origin 6000 0 2500 u +x v +y outline 0,0 3700,0 3700,2000 0,2000']){const r=await apiRequest(cmd);if(!r.ok)throw Error(JSON.stringify(r));}const revision=(await apiRequest('engineering-read')).revision,p=await(await fetch('/engineering/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'engineering-transaction/1',expectedRevision:revision,operations:[{op:'publish-material',value:{id:'r03b-canvas-board',version:1,name:'L 形明選板材',kind:'panel',width:915,length:1830,thickness:'6'}},{op:'put-parameter',value:{id:90,name:'L 形承接',fields:[{id:1,name:'X',type:'dimension',input:'8'}]}}]})})).json();if(!p.ok||!p.preview.valid)throw Error(JSON.stringify(p));const c=await apiRequest('engineering-confirm '+p.preview.token);if(!c.ok)throw Error(JSON.stringify(c));await renderObjects();})()`);
    await read(`(()=>{if(window.__p2053)throw Error('R03B_OBSERVER_ALREADY_INSTALLED');const original=window.fetch,log=window.__p2053={records:[],history:new Map(),original};window.fetch=async(...args)=>{const request=new Request(...args),url=new URL(request.url),body=request.method==='POST'?await request.clone().json().catch(()=>null):null,watched=url.pathname.startsWith('/framing-template/')||url.pathname==='/api'&&body?.cmd?.startsWith('framing-template-'),row={url:url.pathname,body};if(watched)log.records.push(row);const response=await original(...args);if(watched)row.reply=await response.clone().json().catch(()=>null);return response;};return true;})()`);
    try{
      await enter(1,check);
      check('ENTRY',await read(`document.querySelectorAll('[data-ft-workspace="1"]').length===1&&document.querySelectorAll('[data-ft-action="confirm"]').length===1&&document.querySelector('[data-face-product-mode]').value==='framing-notch'`));
      check('LIMITED_SCOPE',await read(`document.querySelector('.ft-scope').textContent.includes('單一凹角')&&document.querySelector('.ft-scope').textContent.includes('本片不涵蓋任意 L 形')&&document.querySelector('.ft-scope').textContent.includes('明確拒絕')`));
      check('EXPLICIT_SOURCES',await read(`['on','panel','threshold'].every(name=>document.querySelector('[data-ft-field="'+name+'"]').value==='')&&!document.querySelector('[data-ft-field="materials"]').checked`));
      const source=(await wire()).filter(row=>row.url==='/framing-template/read').at(-1);
      check('READ_VERSION',source.body.schema==='framing-template-read/3'&&same(source.body.template,fixture.template)&&source.reply.schema==='framing-template-read-result/3'&&source.reply.generator.scope==='rectangle-or-single-notch-l-centered-no-retreat'&&same(source.reply.source.outer,fixture.room));
      await ctl(action('new'));await fill(field('name'),'L 形第一片 '+size.width);const recipeBefore=await snapshot(),recipeHistory=await capture('recipe');await ctl(action('save'));await wait(`ReferenceWorkspace.readFeatureAttachment(GeometryFramingRecipes.KIND)?.recipes.some(recipe=>recipe.name===${JSON.stringify('L 形第一片 '+size.width)})`);
      check('SAVE_INTENT',(await snapshot()).world===recipeBefore.world&&await single(recipeHistory)&&await read(`ReferenceWorkspace.history.undo.at(-1).kind==='local'&&Object.keys(ReferenceWorkspace.readFeatureAttachment(GeometryFramingRecipes.KIND).recipes.find(recipe=>recipe.name===${JSON.stringify('L 形第一片 '+size.width)})).sort().join(',')==='defaults,id,name,preference,sourceHints,sourceSlots,template'`));
      await sources(1);const before=await snapshot(),h=await capture('preview'),firstReceipt=await preview(),first=firstReceipt.reply.preview;
      check('POLICY_REQUEST',same(firstReceipt.body.template,fixture.template)&&same(first.template,fixture.template)&&same(firstReceipt.body.layout,{corner:'min-min',lengthAlong:'v'})&&same(firstReceipt.body.sources,{panel:{id:'r03b-canvas-board',version:1},threshold:{parameterId:90,fieldId:1}}));
      check('ORACLE_EVERY_MEMBER',same(normalize(first.members.map(member=>[member.kind,member.rect,member.length,member.role,member.priority,member.A,member.B])),normalize(fixture.expected.members)),{actual:first.members,expected:fixture.expected.members});
      check('ONE_ORIGIN',same(first.seams,fixture.expected.seams)&&same(first.marks,fixture.expected.marks),{seams:first.seams,marks:first.marks});
      check('REFLEX_ROLES',first.members.some(member=>member.role==='custom'&&member.priority===3)&&first.members.some(member=>member.role==='custom'&&member.priority===4));
      check('NATIVE_SUPPORT',first.valid===true&&first.supportComplete===true&&first.support.every(row=>row.supported===true));
      const rows=await read(`[...document.querySelectorAll('[data-ft-member-row]')].map(row=>[...row.cells].map(cell=>cell.textContent))`);
      check('PREVIEW_TABLE',rows.length===first.members.length&&rows.every((row,i)=>{const member=first.members.at(i);return row.at(1)===member.rect.join(', ')&&row.at(2)===String(member.length)&&row.at(3)===member.A+' × '+member.B;})&&await read(`document.querySelectorAll('[data-ft-member]').length===${first.members.length}&&document.querySelector('.ft-results').textContent.includes('凹角沿牆料')&&document.querySelector('.ft-results').textContent.includes('承接沿牆料的副支')`));
      check('PREVIEW_ZERO',same(await snapshot(),before)&&await unchanged(h));
      await ctl(action('cancel'));await wait(phase('ready'));
      check('CANCEL_ZERO',same(await snapshot(),before)&&await unchanged(h)&&(await wire()).filter(row=>row.body?.cmd==='framing-template-cancel '+first.token+' '+firstReceipt.reply.ownerKey).length===1&&!(await wire()).some(row=>row.body?.cmd?.startsWith('framing-template-confirm ')));
      await sources(1);const secondReceipt=await preview(),second=secondReceipt.reply.preview;
      check('NEW_TOKEN_SAME_GEOMETRY',second.token!==first.token&&same(second.members,first.members)&&second.definitionFingerprint===first.definitionFingerprint);
      const commitHistory=await capture('confirm'),searches=(await wire()).filter(row=>row.url==='/framing-template/preview').length;await ctl(action('confirm'));await wait(phase('committed'));const committed=await snapshot(),confirms=(await wire()).filter(row=>row.body?.cmd?.startsWith('framing-template-confirm ')),native=await read("apiRequest('engineering-read')");
      check('CONFIRM_ONE_HISTORY',confirms.length===1&&confirms.at(0).body.cmd==='framing-template-confirm '+second.token+' '+secondReceipt.reply.ownerKey&&await single(commitHistory)&&native.definition_sha256===second.definitionFingerprint&&(await wire()).filter(row=>row.url==='/framing-template/preview').length===searches);
      check('LIVE_DEFINITIONS',['finish-surface ','panel-fill ','derived-placement ','from-fill'].every(text=>committed.world.includes(text))&&committed.world.split('\n').filter(line=>line.startsWith('panel-fill ')).length===1);
      await ctl(action('close'));await hideFaceDrawer();await ctl('#faceUndoButton');await wait('!oc.busy&&!ReferenceWorkspace.busy');check('UNDO',(await snapshot()).world===before.world&&same((await snapshot()).recipe,committed.recipe));await ctl('#faceRedoButton');await wait('!oc.busy&&!ReferenceWorkspace.busy');check('REDO',(await snapshot()).world===committed.world&&same((await snapshot()).recipe,committed.recipe));
      await ctl('#workspaceBackButton');await wait('!oc.focus');await enter(1);
      check('VIEWPORT_LAYOUT',await read(`(()=>{const e=document.querySelector('[data-ft-workspace]'),controls=[...e.querySelectorAll('input,select,button')].filter(control=>!control.disabled);return innerWidth===${size.width}&&e.scrollWidth<=e.clientWidth+1&&e.getBoundingClientRect().width<=innerWidth&&controls.every(control=>control.getBoundingClientRect().width>0);})()`));
      await leave();await enter(2);await sources(2);const rejectBefore=await snapshot(),rejectHistory=await capture('reject');await ctl(action('preview'));await wait(phase('rejected'));
      check('POLICY_CONFLICT_ZERO',await read(`document.querySelector('[data-ft-status]').textContent.includes('POLICY_RULE_CONFLICT')&&document.querySelector('[data-ft-action="confirm"]').disabled`)&&same(await snapshot(),rejectBefore)&&await unchanged(rejectHistory));await ctl(action('cancel'));await leave();
      const scopeIds=await read(`(async()=>{const result=await apiRequest('newid 2');if(!result.ok||!Array.isArray(result.surfaces)||result.surfaces.length!==2)throw Error('R03B_SCOPE_FIXTURE_IDS '+JSON.stringify(result));return result.surfaces;})()`);
      for(const blocked of [{id:scopeIds.at(0),origin:18000,label:'U',reason:'U 形',outline:'0,0 3880,0 3880,500 3580,500 3580,900 3880,900 3880,3600 0,3600'}, {id:scopeIds.at(1),origin:24000,label:'HOLES',reason:'孔',outline:'0,0 3740,0 3740,3301 0,3301 hole 1000,500 1200,500 1200,700 1000,700'}]){
        await read(`(async()=>{const result=await apiRequest(${JSON.stringify('line surface '+blocked.id+' origin '+blocked.origin+' 0 2500 u +x v +y outline '+blocked.outline)});if(!result.ok)throw Error(JSON.stringify(result));await renderObjects();})()`);
        const scopeBefore=await snapshot(),scopeHistory=await capture('scope-'+blocked.label),scopeCalls=(await wire()).length;
        await enter(blocked.id,null,'settled');const observed=(await wire()).slice(scopeCalls),readReply=observed.find(row=>row.url==='/framing-template/read')?.reply;
        check(blocked.label+'_READ_SCOPE_REASON',readReply?.ok===true&&readReply.schema==='framing-template-read-result/3'&&await read(`document.querySelector('[data-ft-status="rejected"]')?.textContent.includes('UNSUPPORTED_SCOPE')&&document.querySelector('[data-ft-status]').textContent.includes(${JSON.stringify(blocked.reason)})&&document.querySelector('[data-ft-action="confirm"]').disabled&&document.querySelector('[data-ft-action="preview"]').disabled`),{readReply});
        check(blocked.label+'_READ_ZERO',same(await snapshot(),scopeBefore)&&await unchanged(scopeHistory)&&observed.length===1&&observed[0].url==='/framing-template/read');await leave();
      }
    }finally{await read(`(()=>{if(window.__p2053){window.fetch=__p2053.original;delete window.__p2053;}return true;})()`);}
  }
  judge('NO_EXCEPTIONS',exceptionCount()===initialExceptions);
  console.log('R03B_BROWSER_SCOPE '+JSON.stringify({schema:'framing-template-notch-browser-scope/1',assertions:seen.size+1,viewports:[390,1400],oracle:fixture.oracle,coldOpen:'separate real ZIP Node and new-process native gates; Chrome archive cold-open is not executed by this strict module',unrun:['physical touch','physical IME','assistive technology']}));
};
