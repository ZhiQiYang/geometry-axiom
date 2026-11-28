'use strict';
/* R16 v3: actual layout and trusted input. No computed style, hit result,
 * native reply or product handler is replaced. This is a new section; existing
 * section counts and historical pins remain untouched. */
const {controlProbe, entryControlReady, controlWithinClip} = require('../../tests/diagnostics/r16_control_probe.cjs');

function styleProbe(selector) {
  const e = document.querySelector(selector);
  if (!e) return {exists:false};
  const s = getComputedStyle(e), r = e.getBoundingClientRect();
  const label = e.closest('label'), ls = label ? getComputedStyle(label) : null;
  const visibleBackground = node => {
    for (let n=node;n;n=n.parentElement) {
      const color = getComputedStyle(n).backgroundColor;
      if (color !== 'rgba(0, 0, 0, 0)' && color !== 'transparent') return color;
    }
    return 'rgb(255, 255, 255)';
  };
  return {exists:true, value:e.value ?? null, height:r.height, width:r.width,
    fontSize:s.fontSize, borderRadius:s.borderRadius, color:s.color,
    fontWeight:s.fontWeight, minHeight:s.minHeight, outlineWidth:s.outlineWidth,
    outlineStyle:s.outlineStyle, outlineColor:s.outlineColor, outlineOffset:s.outlineOffset,
    labelColor:ls?.color ?? null, labelSize:ls?.fontSize ?? null,
    labelBackground:label ? visibleBackground(label) : null,
    rootMuted:getComputedStyle(document.documentElement).getPropertyValue('--muted').trim(),
    rootLabelToken:getComputedStyle(document.documentElement).getPropertyValue('--form-label-color').trim(),
    labelToken:ls?.getPropertyValue('--form-label-color').trim()??null,
    workspaceInk:getComputedStyle(e.closest('.ig-workspace')||document.documentElement).color,
    viewport:innerWidth, compoundHeight:e.closest('.ig-pf-box')?.getBoundingClientRect().height ?? null,
    active:document.activeElement===e, focusVisible:e.matches(':focus-visible')};
}

function contrast(foreground, background) {
  const luminance = color => {
    const numbers = color.match(/[\d.]+/g).map(Number);
    if (numbers.length !== 3 && !(numbers.length === 4 && numbers.at(3) === 1))
      throw Error('P4541 needs opaque computed colors: '+color);
    return numbers.slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4)
      .reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722].at(i),0);
  };
  const a=luminance(foreground), b=luminance(background);
  return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
}

module.exports = async helpers => {
  const {send,eval_,click,sleep,waitForUI,makeCheck,exceptionCount} = helpers;
  console.log('=== P4541. R16 v2 網格對比、焦點與完整頁尾 ===');
  const check=makeCheck({prefix:'P4541 ',throwOnFail:true});
  const exceptions=exceptionCount();
  const read=async expression=>{
    const value=await eval_(expression);
    if(value?.__err)throw Error('P4541 browser evaluation: '+value.__err);
    return value;
  };
  const call=(fn,...args)=>read('('+fn.toString()+')('+args.map(v=>JSON.stringify(v)).join(',')+')');
  const frames=()=>read('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(true))))');
  const key=async (name,code,vk,modifiers=0)=>{
    for(const type of ['keyDown','keyUp'])
      await send('Input.dispatchKeyEvent',{type,key:name,code,windowsVirtualKeyCode:vk,modifiers});
  };
  const viewport=async size=>{
    await send('Emulation.setDeviceMetricsOverride',{...size,deviceScaleFactor:1,mobile:size.width<=560});
    await sleep(220);await frames();
  };
  const point=async (selector,strict=true)=>{
    let observation;
    // Same 16 x 70 ms reachability budget used by P1231/P74.
    for(let attempt=0;attempt<16;attempt++){
      // Real scrolling centers measured fields; nearest can leave a fractional
      // bottom outside an ancestor scrollport. No epsilon in the clip guard.
      await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:${JSON.stringify(strict?'center':'nearest')},inline:'nearest'});void 0`);
      await frames();observation=await call(controlProbe,selector);
      if((strict?controlWithinClip(observation):entryControlReady(observation))||!observation.exists)break;
      await sleep(70);
    }
    return observation;
  };
  const ctl=async (selector,tag,strict=false)=>{
    const observation=await point(selector,strict);
    check((strict?'R16GF_HIT ':'R16GF_ENTRY ')+tag,
      strict?controlWithinClip(observation):entryControlReady(observation),observation);
    const p=observation.points.at(0);await click(p.x,p.y);await sleep(100);await frames();
  };
  const measure=async (selector,tag,role)=>{
    const observation=await point(selector), style=await call(styleProbe,selector);
    console.log('P4541_STYLE '+JSON.stringify({tag,role,selector,observation,style}));
    check('R16GF_HIT '+tag,controlWithinClip(observation),observation);
    const compact=selector.startsWith('#gi')&&!selector.startsWith('#ig');
    const floor=compact?(style.viewport<=560?44:style.viewport<=760?40:role==='field'?34:35):
      style.viewport<=760?44:role==='field'?38:42;
    check('R16GF_EXISTING_CONTROL_FLOOR '+tag,style.height>=floor&&style.width>=44,{...style,floor});
    if(role==='field'){
      check('R16GF_LABEL_CONTRAST '+tag,contrast(style.labelColor,style.labelBackground)>=4.5,style);
      const muted='rgb('+[1,3,5].map(i=>parseInt(style.rootMuted.slice(i,i+2),16)).join(', ')+')';
      check('R16GF_LABEL_POLICY '+tag,compact?
        style.labelColor===muted&&style.labelSize==='13px'&&style.rootLabelToken===style.rootMuted&&style.labelToken===style.rootMuted:
        style.labelColor===style.workspaceInk&&style.labelSize==='12px'&&contrast(style.labelColor,style.labelBackground)>=12,style);
      check('R16GF_EXISTING_RADIUS '+tag,style.borderRadius===(compact?'5px':'6px'),style);
    }
    return style;
  };
  const focus=async (selector,tag)=>{
    await ctl(selector,tag+'-focus-entry',true);
    // A real keyboard round-trip establishes :focus-visible; no element.focus().
    await key('Tab','Tab',9);await key('Tab','Tab',9,8);await frames();
    const observation=await point(selector);
    check('R16GF_FOCUS_HIT '+tag,controlWithinClip(observation),observation);
    const style=await call(styleProbe,selector);
    check('R16GF_KEYBOARD_FOCUS '+tag,style.active&&style.focusVisible&&
      style.outlineStyle==='solid'&&style.outlineWidth==='2px'&&style.outlineOffset==='2px',style);
    return style;
  };
  const fill=async (selector,value,tag)=>{
    await ctl(selector,tag,true);
    await key('a','KeyA',65,2);
    await send('Input.insertText',{text:value});await frames();
  };
  const pin=()=>read(`(()=>{const h=ReferenceWorkspace.history;window.__p4541History={undo:h.undo.slice(),redo:h.redo.slice(),frame:h.frame,limit:h.limit};return true;})()`);
  const unchanged=async(tag,before,localSteps=0)=>{
    const after=await read(`apiRequest('dump')`);
    check('R16GF_WORLD_UNCHANGED '+tag,after.ok&&after.text===before.text,{before,after});
    const history=await read(`(()=>{const h=ReferenceWorkspace.history,b=window.__p4541History,n=${localSteps};return {
      sameFrame:h.frame===b.frame,sameLimit:h.limit===b.limit,delta:h.undo.length-b.undo.length,
      prefixSame:b.undo.every((v,i)=>h.undo.at(i)===v),newKinds:h.undo.slice(b.undo.length).map(v=>v.kind),
      redoSame:h.redo.length===b.redo.length&&h.redo.every((v,i)=>v===b.redo.at(i)),redoEmpty:h.redo.length===0};})()`);
    check((localSteps?'R16GF_LOCAL_DRAFT_HISTORY ':'R16GF_READ_ONLY_HISTORY ')+tag,
      history.sameFrame&&history.sameLimit&&history.delta===localSteps&&history.prefixSame&&
      (localSteps?history.newKinds.length===localSteps&&history.newKinds.every(v=>v==='local')&&history.redoEmpty:history.redoSame),history);
  };

  // Isolated native fixture only. All workspace entry, focus and close actions
  // below use the ordinary App controls via CDP input.
  await read(`(async()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();await setView3(false);closePanels();
    const reset=await apiRequest('reset');if(!reset.ok)throw Error('P4541 reset');
    for(const line of ['grid-system 31 name-hex 47726964466f726d main-along u u repeat 0 400 v repeat 0 600',
      'boundary 1 outline 0,0 2400,0 2400,2400 0,2400',
      'boundary-vertex-keys 1 outer 1 2 3 4 next-key 5',
      'grid-binding 32 on-boundary 1 from-system 31 vertex-key 1 cell 0 0 anchor 0 1 0 1']){
      let result=await apiRequest('line '+line);
      if(result.preview){if(!result.preview.valid)throw Error('P4541 fixture preview');result=await apiRequest('line confirm '+result.preview.token);}
      if(!result.ok)throw Error('P4541 fixture '+JSON.stringify(result));}
    if(!await renderObjects())throw Error('P4541 render');setOcTool('select');return true;})()`);
  try {
    for(const size of [{width:390,height:844},{width:680,height:900},{width:1400,height:900}]){
      const tag=String(size.width);
      await viewport(size);await ctl('#btnZoom',tag+'-fit');
      await ctl('.ocard[data-kind="grid-system"][data-id="31"]',tag+'-source');
      await waitForUI(`!!$('gridInlineInspector')&&!!$('giName')&&!ReferenceWorkspace.busy`);
      const before=await read(`apiRequest('dump')`);check('R16GF_FIXTURE '+tag,before.ok);
      await pin();
      const compactName=await measure('#giName',tag+'-compact-name','field');
      const compactStep=await measure('#giUStep',tag+'-compact-step','field');
      const compactAction=await measure('#giPreview',tag+'-compact-preview','action');
      const compactFocus=await focus('#giName',tag+'-compact-name');
      check('R16GF_COMPACT_NO_HORIZONTAL_OVERFLOW '+tag,await read(`(()=>{const e=$('gridInlineInspector');return e.scrollWidth<=e.clientWidth;})()`));
      check('R16GF_COMPACT_VALUES '+tag,compactName.value==='GridForm'&&compactStep.value==='400',{compactName,compactStep});
      await unchanged(tag+'-compact-read-only',before);
      await ctl('#gridObjectOpen',tag+'-open-full');
      await waitForUI(`$('infiniteGridWorkspace')?.open&&!$('infiniteGridWorkspace').classList.contains('ig-busy')&&!!$('igName')&&!$('igName').disabled&&!ReferenceWorkspace.busy`);
      // A clean committed target does not create a draft on open (flush).
      // Check the opening itself before repinning; edit/discard add local steps.
      await unchanged(tag+'-full-open-read-only',before);
      await pin();
      const fullName=await measure('#igName',tag+'-full-name','field');
      const compoundHit=await point('#igUStep'), compoundStyle=await call(styleProbe,'#igUStep');
      check('R16GF_COMPOUND_HIT '+tag,controlWithinClip(compoundHit),compoundHit);
      check('R16GF_COMPOUND_EXISTING_DENSITY '+tag,
        compoundStyle.compoundHeight===(size.width<=760?44:38)&&
        compoundStyle.height===compoundStyle.compoundHeight-2&&compoundStyle.width>=44&&compoundStyle.fontSize==='12px',compoundStyle);
      await unchanged(tag+'-full-read-only',before);
      // A clean saved source intentionally disables preview. Create a real raw
      // edit before measuring its enabled hit target; never relax disabled guards.
      await fill('#igName','GridForm-draft-'+tag,tag+'-edit-name');
      await waitForUI(`!$('igSaveSource').disabled`);
      const fullAction=await measure('#igSaveSource',tag+'-full-preview','action');
      const fullFocus=await focus('#igName',tag+'-full-name');
      await ctl('#igUStep',tag+'-compound-focus-entry',true);
      await key('Tab','Tab',9);await key('Tab','Tab',9,8);await frames();
      const compoundFocusHit=await point('#igUStep');
      check('R16GF_COMPOUND_FOCUS_HIT '+tag,controlWithinClip(compoundFocusHit),compoundFocusHit);
      const compoundFocus=await read(`(()=>{const e=$('igUStep'),s=getComputedStyle(e.closest('.ig-pf-box'));return {active:document.activeElement===e,focusVisible:e.matches(':focus-visible'),outline:s.outlineStyle,width:s.outlineWidth,offset:s.outlineOffset};})()`);
      check('R16GF_COMPOUND_FOCUS '+tag,compoundFocus.active&&compoundFocus.focusVisible&&compoundFocus.outline==='solid'&&compoundFocus.width==='2px'&&compoundFocus.offset==='2px',compoundFocus);
      check('R16GF_FOCUS_AND_EXISTING_DENSITY '+tag,
        compactName.fontSize==='14px'&&fullName.fontSize==='13px'&&
        compactFocus.outlineColor===fullFocus.outlineColor&&fullName.value==='GridForm'&&fullFocus.value==='GridForm-draft-'+tag,
        {compactName,fullName,compactAction,fullAction,compactFocus,fullFocus});
      check('R16GF_NO_HORIZONTAL_OVERFLOW '+tag,await read(`(()=>{const nodes=[$('infiniteGridWorkspace'),document.querySelector('.ig-settings')];return nodes.every(e=>e.scrollWidth<=e.clientWidth);})()`));
      await ctl('#igDiscardDraft',tag+'-discard',true);
      await ctl('#igDiscardConfirm',tag+'-discard-confirm',true);
      await waitForUI(`!$('infiniteGridWorkspace')?.open&&!ReferenceWorkspace.busy`);
      await unchanged(tag,before,2);
      await key('Escape','Escape',27);

      await ctl('#btnZoom',tag+'-binding-fit');
      await ctl('.ocard[data-kind="grid-binding"][data-id="32"]',tag+'-binding-card');
      await waitForUI(`$('gridInlineInspector')?.dataset.giKind==='binding'&&!!$('giCellI')&&$('giVertex')?.value==='outer:0'&&$('giVertex').options.length===5&&!ReferenceWorkspace.busy`);
      await pin();
      const bindingBefore=await read(`apiRequest('dump')`);
      check('R16GF_BINDING_FIXTURE '+tag,bindingBefore.ok);
      const compactSystem=await measure('#giSystem',tag+'-binding-compact-system','field');
      await measure('#giBoundary',tag+'-binding-compact-boundary','field');
      await measure('#giVertex',tag+'-binding-compact-vertex','field');
      const compactCell=await measure('#giCellI',tag+'-binding-compact-cell','field');
      await focus('#giCellI',tag+'-binding-compact-cell');
      check('R16GF_COMPACT_BINDING_NO_OVERFLOW '+tag,await read(`(()=>{const e=$('gridInlineInspector');return e.scrollWidth<=e.clientWidth;})()`));
      await unchanged(tag+'-binding-compact-read-only',bindingBefore);
      await ctl('#gridObjectOpen',tag+'-binding-open-full');
      await waitForUI(`$('infiniteGridWorkspace')?.open&&!$('infiniteGridWorkspace').classList.contains('ig-busy')&&!!$('igCellI')&&!$('igCellI').disabled&&!$('igBindingForm').hidden&&$('igVertex')?.value==='outer:0'&&$('igVertex').options.length===5&&!ReferenceWorkspace.busy`);
      await unchanged(tag+'-binding-full-open-read-only',bindingBefore);
      await pin();
      const fullSystem=await measure('#igSystem',tag+'-binding-full-system','field');
      await measure('#igBoundary',tag+'-binding-full-boundary','field');
      await measure('#igVertex',tag+'-binding-full-vertex','field');
      const fullCell=await measure('#igCellI',tag+'-binding-full-cell','field');
      await focus('#igCellI',tag+'-binding-full-cell');
      check('R16GF_BINDING_VALUES_AND_LABELS '+tag,compactSystem.labelSize==='13px'&&fullSystem.labelSize==='12px'&&
        compactCell.value==='0'&&fullCell.value==='0',{compactSystem,fullSystem,compactCell,fullCell});
      check('R16GF_FULL_BINDING_NO_OVERFLOW '+tag,await read(`(()=>{const nodes=[$('infiniteGridWorkspace'),document.querySelector('.ig-settings')];return nodes.every(e=>e.scrollWidth<=e.clientWidth);})()`));
      await unchanged(tag+'-binding-full-read-only',bindingBefore);
      await fill('#igCellI','-2',tag+'-binding-raw-edit');
      await waitForUI(`!$('igSaveBinding').disabled`);
      await measure('#igSaveBinding',tag+'-binding-full-preview','action');
      await ctl('#igDiscardDraft',tag+'-binding-discard',true);
      await ctl('#igDiscardConfirm',tag+'-binding-discard-confirm',true);
      await waitForUI(`!$('infiniteGridWorkspace')?.open&&!ReferenceWorkspace.busy`);
      await unchanged(tag+'-binding',bindingBefore,2);
      await key('Escape','Escape',27);
    }
    check('R16GF_NO_NEW_EXCEPTION',exceptionCount()===exceptions);
  } finally {
    await read('delete window.__p4541History;void 0');
    await viewport({width:1400,height:900});
  }
};
