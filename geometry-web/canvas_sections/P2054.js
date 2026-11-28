'use strict';
/* Work package A, independent preview-table slice. The fixture is native;
 * entry, recipe save, source selection, preview and cancel use trusted UI.
 * Nothing here calls the framing generator directly or changes its policy. */
const {previewLengthProbe,lengthValuesReady,lengthSingleLine,lengthUnclipped}=require('../../tests/diagnostics/r03_preview_length_probe.cjs');
// Authored assertion contract, not a browser measurement or accepted count.
const ASSERTIONS=Object.freeze([1,2].flatMap(version=>[
  ...[1400,390].flatMap(width=>['VALUES','SINGLE_LINE','UNCLIPPED'].map(kind=>'R03_PREVIEW_LENGTH_'+kind+' v'+version+' '+width)),
  'R03_PREVIEW_CANCEL_ZERO v'+version
]).concat('R03_PREVIEW_LENGTH_NO_EXCEPTIONS'));
module.exports=async helpers=>{
  const {send,eval_,sleep,click,waitForUI,makeCheck,exceptionCount}=helpers;
  console.log('=== P2054. R03 骨架預覽四位數長度不折行 ===');
  const record=makeCheck({prefix:'P2054 ',throwOnFail:false}),beforeExceptions=exceptionCount(),seen=new Set();
  const check=(name,okay,detail)=>{if(!ASSERTIONS.includes(name)||seen.has(name))throw Error('R2054_ASSERTION_IDENTITY '+name);seen.add(name);return record(name,okay,detail);};
  const read=async expression=>{const result=await eval_(expression);if(result?.__err)throw Error(result.__err);return result;};
  const settle=()=>read('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(true))))');
  const key=async(name,code,vk,modifiers=0)=>{for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key:name,code,windowsVirtualKeyCode:vk,modifiers});};
  const ctl=async selector=>{
    await waitForUI('!!document.querySelector('+JSON.stringify(selector)+')');
    await read(`document.querySelector(${JSON.stringify(selector)}).scrollIntoView({block:'nearest',inline:'nearest'});void 0`);
    await settle();
    const p=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2;return {x,y,okay:r.width>0&&r.height>0&&!e.disabled&&e.contains(document.elementFromPoint(x,y))};})()`);
    if(!p.okay)throw Error('P2054 control unreachable '+selector+' '+JSON.stringify(p));
    await click(p.x,p.y);await sleep(100);await settle();
  };
  const choose=async(selector,value)=>{
    const index=await read(`[...document.querySelector(${JSON.stringify(selector)}).options].findIndex(o=>o.value===${JSON.stringify(String(value))})`);
    if(index<0)throw Error('P2054 missing option '+selector+' '+value);
    await ctl(selector);await key('Home','Home',36);
    for(let at=0;at<index;at++)await key('ArrowDown','ArrowDown',40);
    await key('Enter','Enter',13);await sleep(100);
    if(!await read(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(String(value))}`))throw Error('P2054 selection not applied');
  };
  const action=name=>'[data-ft-action="'+name+'"]',field=name=>'[data-ft-field="'+name+'"]';
  const phase=name=>`!!document.querySelector('[data-ft-status="${name}"]')`;
  const viewport=async(width,height)=>{
    await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<=560});await sleep(220);await settle();
    if(width<=900&&await read(`$('workspaceToggleRight')?.getAttribute('aria-expanded')==='false'`))await ctl('#workspaceToggleRight');
  };
  await viewport(1400,900);
  await read(`(async()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();await setView3(false);closePanels();
    for(const cmd of ['reset','line surface 1 origin 0 0 2500 u +x v +y outline 0,0 3740,0 3740,2000 0,2000','line surface 2 origin 0 0 2500 u +x v +y outline 0,0 3740,0 3740,3301 0,3301']){const r=await apiRequest(cmd);if(!r.ok)throw Error(JSON.stringify(r));}
    const revision=(await apiRequest('engineering-read')).revision;
    const p=await(await fetch('/engineering/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'engineering-transaction/1',expectedRevision:revision,operations:[{op:'publish-material',value:{id:'p2054-board',version:1,name:'P2054 版面夾具',kind:'panel',width:915,length:1830,thickness:'6'}},{op:'put-parameter',value:{id:90,name:'P2054 X',fields:[{id:1,name:'X',type:'dimension',input:'8'}]}}]})})).json();
    if(!p.ok||!p.preview.valid)throw Error(JSON.stringify(p));const c=await apiRequest('engineering-confirm '+p.preview.token);if(!c.ok)throw Error(JSON.stringify(c));
    if(!await renderObjects())throw Error('P2054 fixture render failed');setOcTool('select');return true;})()`);
  for(const scenario of [{bid:1,mode:'framing',version:1,count:33,length:'3740'},{bid:2,mode:'framing-fixed',version:2,count:53,length:'3247'}]){
    await ctl('#btnZoom');await ctl('.ocard[data-kind="boundary"][data-id="'+scenario.bid+'"] .card-enter');
    await waitForUI(`oc.focus?.t==='face'&&oc.focus.id===${scenario.bid}`);
    await ctl('[data-fi-tab="prop"]');await ctl('[data-face-settings="'+scenario.bid+'"]');await ctl('[data-panel-fill-open="'+scenario.bid+'"]');
    await waitForUI(`!!document.querySelector('[data-face-product-mode]:not(:disabled)')`);
    await choose('[data-face-product-mode]',scenario.mode);await waitForUI(phase('ready'));
    await ctl(action('new'));await choose(field('corner'),'min-min');await choose(field('lengthAlong'),'v');
    await ctl(field('name'));await key('a','KeyA',65,2);await send('Input.insertText',{text:'P2054 v'+scenario.version});
    await ctl(action('save'));await waitForUI(`ReferenceWorkspace.readFeatureAttachment(GeometryFramingRecipes.KIND)?.recipes.some(r=>r.name==='P2054 v${scenario.version}')`);
    await choose(field('on'),scenario.bid);await choose(field('panel'),'["p2054-board",1]');await choose(field('threshold'),'90:1');await ctl(field('materials'));
    await read(`(async()=>{const h=ReferenceWorkspace.history;window.__p2054Pin={world:(await apiRequest('dump')).text,history:h,frame:h.frame,undo:h.undo.slice(),redo:h.redo.slice()};return true;})()`);
    await ctl(action('preview'));await waitForUI(phase('confirmable'));
    for(const size of [{width:1400,height:900},{width:390,height:844}]){
      await viewport(size.width,size.height);
      const observed=await read('('+previewLengthProbe.toString()+')()'),label='v'+scenario.version+' '+size.width;
      console.log('P2054_LENGTH_MEASUREMENT '+JSON.stringify({label,observed}));
      check('R03_PREVIEW_LENGTH_VALUES '+label,lengthValuesReady(observed,scenario.count,scenario.length),observed);
      check('R03_PREVIEW_LENGTH_SINGLE_LINE '+label,lengthSingleLine(observed),observed);
      check('R03_PREVIEW_LENGTH_UNCLIPPED '+label,lengthUnclipped(observed),observed);
    }
    await viewport(1400,900);await ctl(action('cancel'));await waitForUI(phase('ready'));
    const unchanged=await read(`(async()=>{const p=__p2054Pin,h=ReferenceWorkspace.history;return (await apiRequest('dump')).text===p.world&&h===p.history&&h.frame===p.frame&&h.undo.length===p.undo.length&&h.redo.length===p.redo.length&&h.undo.every((v,i)=>v===p.undo.at(i))&&h.redo.every((v,i)=>v===p.redo.at(i));})()`);
    check('R03_PREVIEW_CANCEL_ZERO v'+scenario.version,unchanged);
    await ctl(action('close'));await ctl('#workspaceBackButton');await waitForUI('!oc.focus');
  }
  await read('delete window.__p2054Pin;void 0');
  await viewport(1382,804);
  check('R03_PREVIEW_LENGTH_NO_EXCEPTIONS',exceptionCount()===beforeExceptions);
  if(seen.size!==ASSERTIONS.length)throw Error('R2054_ASSERTION_COVERAGE');
};
module.exports.ASSERTIONS=ASSERTIONS;
