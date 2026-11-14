/* R14 host/App slice 1: ordinary UI creates a PANEL source and a shared rule,
 * sees native lines, cancels/undoes and saves/opens the real project ZIP.
 * No product mutation API is used to construct the successful example. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const cdp=require('./cdp_helpers.js'),P=require('./project-store.js'),zip=require('./vendor/fflate/umd/index.js');
module.exports=async function r14PanelEntryTests({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount}){
  console.log('=== P381. R14 面材分份：正式入口、完整 pitch、保存與重開 ===');
  const check=cdp.makeCheck({prefix:'P381 ',throwOnFail:true}),read=cdp.makeRead(eval_),wait=cdp.makeWait(waitForUI,15000);
  const ctl=cdp.makeCtl({eval_,sleep,click},{scroll:'center',attempts:12,pollMs:35,settleMs:60});
  const key=cdp.makeKey({send,sleep}),fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:35});
  const shot=cdp.makeShot(send,['GEOMETRY_R14_SCREENSHOT_DIR']),history=cdp.makeHistoryOracle(read,'P381');
  const initialErrors=exceptionCount(),V2='grid-subdivision-rules/2';
  const query=cmd=>read(`apiRequest(${JSON.stringify(cmd)}).then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})`);
  const dump=async()=>(await query('dump')).text,objects=()=>query('objects'),settled=()=>wait('!oc.busy&&!ReferenceWorkspace.busy');
  const raw=()=>read(`(()=>{const c=ReferenceWorkspace.readGridDrafts(),id=$('infiniteGridWorkspace')?.dataset.draftId;return c.drafts.find(d=>d.draftId===id)||(c.drafts.length===1?c.drafts[0]:null)||null;})()`);
  const impact=()=>wait(`!!document.querySelector('.reference-impact[open]')`);
  const confirm=async()=>{await ctl('#impact-confirm');await wait(`!document.querySelector('.reference-impact[open]')`);await settled();};
  const cancel=async()=>{await ctl('.reference-impact .impact-actions button:first-child');await wait(`!document.querySelector('.reference-impact[open]')`);await settled();};
  const leave=async()=>{if(await read(`!!$('infiniteGridWorkspace')?.open`))await ctl('#igClose');};
  const newProject=async()=>{await leave();const warning=await read('ReferenceWorkspace.context().dirty');await ctl('#fileMenuBtn');
    await expectNativeDialog(()=>ctl('#btnNewProject'),{message:'建立一份空白新專案，切換為新的專案識別及「未命名專案」。'+(warning?'目前尚未保存的變更不會自動寫入檔案。':'')+'本次切換可一步復原；僅保存在本頁的形狀特徵參數不會恢復。確定繼續嗎？',accept:true});await settled();};
  const openSource=async id=>{await leave();await key('f','KeyF',70);await ctl(`.ocard[data-kind="grid-system"][data-id="${id}"]`);await wait(`!!$('gridObjectOpen')`);await ctl('#gridObjectOpen');await wait(`$('infiniteGridWorkspace')?.open&&!!$('igRuleAdd')&&!$('igRuleAdd').disabled`);};
  const selectCellZero=async()=>{
    await read(`$('igGridView').scrollIntoView({block:'center'});void 0`);await sleep(60);
    const point=await read(`(()=>{const view=$('igGridView'),at=(a,i)=>view.querySelector('[data-ig-axis="'+a+'"][data-ig-index="'+i+'"]'),u0=at('u',0),u1=at('u',1),v0=at('v',0),v1=at('v',1);if(!u0||!u1||!v0||!v1)throw Error('Exact cell zero is not visible');const p=view.createSVGPoint();p.x=(+u0.getAttribute('x1')+(+u1.getAttribute('x1')))/2;p.y=(+v0.getAttribute('y1')+(+v1.getAttribute('y1')))/2;const q=p.matrixTransform(view.getScreenCTM());return {x:q.x,y:q.y};})()`);
    await click(point.x,point.y);await wait(`$('igInfoCell').textContent.includes('(0, 0)')&&$('igGridView').querySelectorAll('[data-ig-source-rule]').length===7`);
  };
  const saveProject=async()=>{
    const downloads=fs.mkdtempSync(path.join(os.tmpdir(),'r14-panel-entry-'));await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:downloads});
    await read(`window.__r14Picker=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});void 0`);
    let file;try{await ctl('#projectBar [data-project-action="save"]');for(let i=0;i<150;i++){const files=fs.readdirSync(downloads).filter(f=>f.endsWith('.gcanvas'));if(files.length===1){file=path.join(downloads,files[0]);break;}await sleep(100);}}
    finally{await read(`if(window.__r14Picker)Object.defineProperty(window,'showSaveFilePicker',window.__r14Picker);else delete window.showSaveFilePicker;delete window.__r14Picker;void 0`);}
    if(!file)throw Error('No formal R14 project download');return {file,downloads};
  };
  const openFile=async file=>{await send('Page.setInterceptFileChooserDialog',{enabled:true});
    try{await ctl('#fileMenuBtn');await ctl('#btnOpenProject');const doc=await send('DOM.getDocument',{depth:0}),node=await send('DOM.querySelector',{nodeId:doc.result.root.nodeId,selector:'#projectFile'});await send('DOM.setFileInputFiles',{nodeId:node.result.nodeId,files:[file]});await settled();await wait('oc.gridSystems.length===1');}
    finally{await send('Page.setInterceptFileChooserDialog',{enabled:false});}
  };
  for(const width of [1280,390]){
    await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width===390});await newProject();
    await ctl('#emptyNewGridSystem');await wait(`!!$('igName')&&!$('igName').disabled`);await fill('#igName',`R14 面材七等分 ${width}`);
    await ctl('input[name="igUSource"][value="repeat-panel"]');await fill('#igUPanel','915');await fill('#igUGap','2');await fill('#igUAnchor','0');
    await fill('#igVStep','400');await fill('#igVPhase','0');
    await ctl('#igSaveSource');await impact();await confirm();await wait(`!!$('igRuleAdd')&&!$('igRuleAdd').disabled`);
    let source=(await objects()).gridSystems[0],sid=source.id;
    check(`${width} 一般建立入口保留915+2面材、混合軸、空規則及零面`,source.uDefinition.source==='repeat-panel'&&source.uDefinition.panel===915&&source.uDefinition.gap===2&&source.vDefinition.source==='repeat'&&source.vDefinition.step===400&&source.rules.length===0&&(await objects()).faces.length===0);
    check(`${width} 面材分份沿既有表單並說明完整間距`,await read(`$('igRuleReason').textContent===''&&$('igRuleNote').textContent.includes('面材＋縫')&&document.querySelectorAll('#igRuleAdd').length===1`));
    await ctl('#igRuleAdd');await fill('#igRuleName','面材七等分');await fill('#igRuleU','7');await fill('#igRuleV','2');
    const before=await dump(),draft=await raw(),pin=await history.capture();await ctl('#igRulePreview');await impact();
    check(`${width} 真候選摘要顯示14個131×200小格`,await read(`document.querySelector('.reference-impact').textContent.includes('14 個 131×200 mm 小格')&&!$('impact-confirm').disabled`));
    check(`${width} 預覽不寫World、不耗key、不寫歷史`,(await dump())===before&&(await objects()).gridSystems[0].nextRuleKey===1&&await history.unchanged(pin));
    await shot(`r14-${width}-preview`);await cancel();
    check(`${width} 取消保留逐字World/raw/history`,(await dump())===before&&JSON.stringify(await raw())===JSON.stringify(draft)&&await history.unchanged(pin));
    await ctl('#igRulePreview');await impact();await confirm();source=(await objects()).gridSystems[0];
    check(`${width} 確認同一步提交規則與清raw`,source.rules.length===1&&source.rules[0].ruleKey===1&&source.nextRuleKey===2&&source.rules[0].selector.kind==='all-cells'&&source.rules[0].divisions.join('/')==='7/2'&&await raw()===null&&await history.single(pin));await history.release(pin);
    const q=await query(`grid-rule-query system ${sid} rule 1 cell 0 0`),negative=await query(`grid-rule-query system ${sid} rule 1 cell -1 0`);
    check(`${width} 真核心完整pitch與phase的獨立座標oracle`,q.systemId===sid&&q.ruleKey===1&&JSON.stringify(q.cell)==='["0","0"]'&&q.lines.length===7&&JSON.stringify(q.bounds)==='[916,0,1833,400]'&&JSON.stringify(q.lines.filter(l=>l.axis==='u').map(l=>l.coordinate))==='[1047,1178,1309,1440,1571,1702]'&&JSON.stringify(q.lines.filter(l=>l.axis==='v').map(l=>l.coordinate))==='[200]');
    check(`${width} 負cell保持真實縫中心與signed身分`,negative.systemId===sid&&negative.ruleKey===1&&negative.lines.length===7&&JSON.stringify(negative.cell)==='["-1","0"]'&&JSON.stringify(negative.bounds)==='[-1,0,916,400]'&&JSON.stringify(negative.lines.filter(l=>l.axis==='u').map(l=>l.coordinate))==='[130,261,392,523,654,785]');
    await selectCellZero();
    check(`${width} 畫面真顯示7條子線且不偽造正式引用`,await read(`(()=>{const view=$('igGridView'),lines=[...view.querySelectorAll('[data-ig-source-rule]')];return lines.length===7&&lines.every(n=>n.dataset.igRuleRef==='none'&&n.querySelector('title').textContent.includes('cell (0, 0)'));})()`));
    await shot(`r14-${width}-result`);
    await leave();await ctl('#btnUndo');await settled();
    check(`${width} 一步復原同時恢復零規則與原始輸入`,(await objects()).gridSystems[0].rules.length===0&&(await objects()).gridSystems[0].nextRuleKey===1&&JSON.stringify(await raw())===JSON.stringify(draft));
    await ctl('#btnRedo');await settled();
    check(`${width} 一步重做恢復原key及清除原始輸入`,(await objects()).gridSystems[0].rules[0].ruleKey===1&&(await objects()).gridSystems[0].nextRuleKey===2&&await raw()===null);
    await openSource(sid);await ctl('[data-ig-rule-key="1"] [data-ig-rule-action="edit"]');await fill('#igRuleU','6');const invalidBefore=await dump(),invalidRaw=await raw();await ctl('#igRulePreview');await impact();
    check(`${width} 917不能六等分由真核心拒絕且零寫入`,await read(`$('impact-confirm').disabled&&document.querySelector('.reference-impact').textContent.includes('變更無法套用')`)&&(await dump())===invalidBefore&&JSON.stringify(await raw())===JSON.stringify(invalidRaw));await cancel();await ctl('#igRuleCancel');
    await ctl('[data-ig-rule-key="1"] [data-ig-rule-action="edit"]');await fill('#igRuleU',' 7 ');await fill('#igRuleV','');
    const scene=await dump(),savedRaw=await raw(),saved=await saveProject(),archive=await P.unpack(new Uint8Array(fs.readFileSync(saved.file)),zip);
    const archiveRaw=archive.manifest.featureAttachments.records.find(record=>record.kind===P.Features.GRID_KIND)?.value;
    check(`${width} 真ZIP保留/2、native定義及未確認raw`,archive.scene===scene&&archive.manifest.requiredCapabilities.includes(V2)&&JSON.stringify(P.Features.gridDrafts(archiveRaw).drafts[0])===JSON.stringify(savedRaw));
    const projectToken=await read('ReferenceWorkspace.getProjectState().contextToken');await newProject();
    check(`${width} 重開前建立不同空白context`,(await objects()).gridSystems.length===0&&await raw()===null&&await read(`ReferenceWorkspace.getProjectState().contextToken!==${JSON.stringify(projectToken)}`));
    // The source card is reachable at both widths; the desktop library's
    // btnNewGridSystem shortcut is hidden at 390px. Opening the same source
    // resumes its saved draft through the production matching path.
    await openFile(saved.file);await openSource(sid);await wait(`$('infiniteGridWorkspace')?.open&&!!$('igRuleName')&&!$('igRuleName').disabled`);
    check(`${width} 正式開檔還原逐字World、ruleKey高水位及未確認raw`,(await dump())===scene&&(await objects()).gridSystems[0].rules[0].ruleKey===1&&(await objects()).gridSystems[0].nextRuleKey===2&&JSON.stringify(await raw())===JSON.stringify(savedRaw)&&await read(`$('igRuleU').value===' 7 '&&$('igRuleV').value===''`));
    await ctl('#igRuleU');await shot(`r14-${width}-reopened`);await ctl('#igRuleCancel');await selectCellZero();
    check(`${width} 重開後仍顯示真子線且無水平溢出`,await read(`$('igGridView').querySelectorAll('[data-ig-source-rule]').length===7&&$('infiniteGridWorkspace').scrollWidth<=$('infiniteGridWorkspace').clientWidth+1`));
    fs.writeFileSync(path.join(saved.downloads,'r14-roundtrip.json'),JSON.stringify({width,scene,raw:savedRaw,manifest:archive.manifest,positive:q,negative},null,2));console.log(`P381 saved artifact ${saved.file}`);
    await leave();
  }
  await send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});await newProject();
  check('R14 首片沒有未捕捉瀏覽器例外',exceptionCount()===initialErrors);
};
