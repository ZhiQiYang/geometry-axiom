/* #61 slice 1: real input and formal Save/open; native is the sole rule
 * authority. API mutations below are explicit fixtures for stale-owner races. */
'use strict';
const cdp=require('./cdp_helpers.js');
module.exports=async function ruleEditorTests({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount}){
  // S2 keeps the same exact discard question inside the active workspace.
  const discardDraft=async({message,accept})=>{
    await ctl('#igDiscardDraft');
    await waitForUI(`!!$('igDiscardConfirmation')&&$('igDiscardConfirmation').getAttribute('role')==='alertdialog'`,10000);
    const actual=await eval_(`$('igDiscardQuestion').textContent`);
    if(actual!==message)throw Error('Discard question changed: '+JSON.stringify({expected:message,actual}));
    await ctl(accept?'#igDiscardConfirm':'#igDiscardCancel');
    await waitForUI(`!$('igDiscardConfirmation')`,10000);
  };

  console.log('=== P87. 來源規則 CRUD、typed baseline、原始草稿與正式 ZIP ===');
  const fs=require('fs'),path=require('path'),os=require('os'),P=require('./project-store.js'),zip=require('./vendor/fflate/umd/index.js');
  const read=cdp.makeRead(eval_),wait=cdp.makeWait(waitForUI,20000),check=cdp.makeCheck({prefix:'P87 ',throwOnFail:true}),startExceptions=exceptionCount();
  const baseCtl=cdp.makeCtl({eval_,sleep,click},{scroll:'center',attempts:12,pollMs:70,settleMs:100,missing:'Missing ',unreachable:(s,p)=>'Rule control unreachable '+s+' '+JSON.stringify(p)});
  const ctl=async selector=>{
    try{return await baseCtl(selector);}catch(error){
      if(!error.message.startsWith('Rule control unreachable '))throw error;
      let control,state;
      try{control=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect(),hit=r?document.elementFromPoint(r.x+r.width/2,r.y+r.height/2):null,menu=document.querySelector('#fileMenuPop'),style=menu?getComputedStyle(menu):null;return {rect:r?{x:r.x,y:r.y,width:r.width,height:r.height,top:r.top,right:r.right,bottom:r.bottom,left:r.left}:null,disabled:!!e?.disabled,hit:hit?.outerHTML?.slice(0,200)||null,menu:menu?{display:style.display,visibility:style.visibility,hidden:menu.hidden}:null,fileMenuExpanded:document.querySelector('#fileMenuBtn')?.getAttribute('aria-expanded')??null};})()`);}catch(failure){control={diagnosticError:failure.message};}
      try{state=await read(`(async()=>({connection:typeof connection==='undefined'?null:{phase:connection.phase,session:connection.session},info:typeof ReferenceWorkspace==='undefined'?null:ReferenceWorkspace.getProjectInfo(),busy:typeof ReferenceWorkspace==='undefined'?null:ReferenceWorkspace.busy,locks:navigator.locks?await navigator.locks.query():null}))()`);}catch(failure){state={diagnosticError:failure.message};}
      throw Error(error.message+' '+JSON.stringify({control,state}));
    }
  };
  const key=cdp.makeKey({send,sleep}),fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:35});
  const historyOracle=cdp.makeHistoryOracle(read,'P87');
  const query=cmd=>read(`apiRequest(${JSON.stringify(cmd)}).then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})`);
  const dump=async()=>(await query('dump')).text,objects=()=>query('objects'),raw=()=>read(`(()=>{const c=ReferenceWorkspace.readGridDrafts(),id=$('infiniteGridWorkspace')?.dataset.draftId;return c.drafts.find(d=>d.draftId===id)||(c.drafts.length===1?c.drafts[0]:null);})()`),history=()=>read('ReferenceWorkspace.history.undo.length');
  const settled=()=>wait('!oc.busy&&!ReferenceWorkspace.busy'),impact=()=>wait(`!!document.querySelector('.reference-impact[open]')`);
  const confirm=async()=>{await ctl('#impact-confirm');await wait(`!document.querySelector('.reference-impact[open]')`);await settled();};
  const cancel=async()=>{await ctl('.reference-impact .impact-actions button:first-child');await wait(`!document.querySelector('.reference-impact[open]')`);await settled();};
  const discard=async()=>{await discardDraft({message:'捨棄這份未發布的原始草稿？已保存到場景的網格保持不變。',accept:true});};
  const leave=async()=>{if(await read(`!!$('infiniteGridWorkspace')?.open`))await ctl('#igClose');};
  const newProject=async()=>{await leave();const warning=await read('ReferenceWorkspace.context().dirty');await ctl('#fileMenuBtn');
    await expectNativeDialog(()=>ctl('#btnNewProject'),{message:'建立一份空白新專案，切換為新的專案識別及「未命名專案」。'+(warning?'目前尚未保存的變更不會自動寫入檔案。':'')+'本次切換可一步復原；僅保存在本頁的形狀特徵參數不會恢復。確定繼續嗎？',accept:true});await settled();};
  const open=async(id,enabled=true)=>{await leave();
    // SVG cards do not scroll into view. Use the existing real F shortcut once
    // before the unchanged hit test, so camera inherited from 390px can show all cards.
    await key('f','KeyF',70);
    await ctl(`.ocard[data-kind="grid-system"][data-id="${id}"]`);await wait(`!!$('gridObjectOpen')`);await ctl('#gridObjectOpen');await wait(`!!$('infiniteGridWorkspace')?.open&&!!$('igRuleAdd')${enabled?"&&!$('igRuleAdd').disabled":''}`);};
  const choose=async(selector,value)=>{const index=await read(`(()=>{const n=document.querySelector(${JSON.stringify(selector)});return [...n.options].findIndex(o=>o.value===${JSON.stringify(value)});})()`);if(index<0)throw Error('Missing rule option');await ctl(selector);await key('Home','Home',36);for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);await key('Enter','Enter',13);await wait(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(value)}`);};
  const fixture=async line=>read(`(async()=>{let r=await apiRequest('line '+${JSON.stringify(line)});if(r.preview){if(!r.preview.valid)throw Error(JSON.stringify(r));r=await apiRequest('line confirm '+r.preview.token);}if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();return true;})()`);
  const shot=cdp.makeShot(send,['GEOMETRY_GRID_RULE_SCREENSHOT_DIR']);
  const saveProject=async()=>{
    const downloads=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-rule-editor-'));await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:downloads});
  await read(`window.__rulePicker=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});void 0`);
    let file;try{await ctl('#projectBar [data-project-action="save"]');for(let i=0;i<150;i++){const files=fs.readdirSync(downloads).filter(f=>f.endsWith('.gcanvas'));if(files.length===1){file=path.join(downloads,files[0]);break;}await sleep(100);}}
  finally{await read(`if(window.__rulePicker)Object.defineProperty(window,'showSaveFilePicker',window.__rulePicker);else delete window.showSaveFilePicker;delete window.__rulePicker;void 0`);}
    if(!file)throw Error("No formal project download");return {file,downloads};
  };
  if(await read(`!!$('infiniteGridWorkspace')?.open&&!!ReferenceWorkspace.readFeatureAttachment('grid-draft')`))await discard();
  await send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});await newProject();
  const empty=(await objects());check('新空白 context 無來源、配置、面或規則',empty.gridSystems.length===0&&empty.gridBindings.length===0&&empty.faces.length===0&&await raw()===null);
  await ctl('#emptyNewGridSystem');await wait(`!!$('igSaveSource')&&!$('igName').disabled`);await fill('#igName','Synthetic source rules');await ctl('#igSaveSource');await impact();await confirm();
  let source=(await objects()).gridSystems[0],sid=source.id;
  check('原有 2a 真 UI 建立雙 REPEAT 獨立來源',source.uDefinition.step===600&&source.vDefinition.step===400&&source.rules.length===0&&source.nextRuleKey===1);
  await ctl('#igRuleAdd');await fill('#igRuleName','All cells <authored>');
  const before=await dump(),draft=await raw(),count=await history(),historyPin=await historyOracle.capture();await ctl('#igRulePreview');await impact();
  check('建立草稿沒有保留正式 key/token，唯一主動作沿用固定頁尾',draft.schema===P.Features.GRID_RULE_SCHEMA&&draft.ruleDraft.ruleKey===null&&!Object.hasOwn(draft.ruleDraft,'token')&&await read(`$('igSaveSource').hidden&&$('igRulePreview').closest('.ig-footer')!==null`));
  const text=await read(`document.querySelector('.reference-impact').textContent`);
  check('native 候選原/新摘要含 source、rule、nextKey 與 200×200／6 小格',text.includes('下一 ruleKey 1')&&text.includes('下一 ruleKey 2')&&text.includes('rule 1')&&text.includes('200×200')&&text.includes('6 個'));
  check('預覽沒有提前改 World 或歷史',(await dump())===before&&await historyOracle.unchanged(historyPin));
  await shot('rule-editor-desktop-preview');await cancel();
  check('取消保留逐字 World、raw 與歷史且不耗 ruleKey',(await dump())===before&&JSON.stringify(await raw())===JSON.stringify(draft)&&await historyOracle.unchanged(historyPin)&&(await objects()).gridSystems[0].nextRuleKey===1);
  await ctl('#igRulePreview');await impact();await confirm();source=(await objects()).gridSystems[0];
  check('native 確認唯一新增 key1 並保留 all-cells 定義',source.rules.length===1&&source.rules[0].ruleKey===1&&source.rules[0].selector.kind==='all-cells'&&source.rules[0].divisions.join('/')==='3/2'&&source.nextRuleKey===2);
  check('確認及清除對應 raw 同一 ContextHistory step',await historyOracle.single(historyPin)&&await raw()===null,{beforeCount:count,limit:historyPin.limit});await historyOracle.release(historyPin);
  await leave();await ctl('#btnUndo');await settled();source=(await objects()).gridSystems[0];
  check('真復原同時恢復無規則 native 與確認前 raw',source.rules.length===0&&source.nextRuleKey===1&&JSON.stringify(await raw())===JSON.stringify(draft));
  await ctl('#btnRedo');await settled();check('真重做同時恢復規則及移除 raw',(await objects()).gridSystems[0].rules.length===1&&await raw()===null);
  await open(sid);await ctl('[data-ig-rule-key="1"] [data-ig-rule-action="edit"]');await fill('#igRuleName','Renamed <safe & exact>');await ctl('#igRulePreview');await impact();
  const renameText=await read(`document.querySelector('.reference-impact').textContent`);check('只有改名仍出現原/新規則摘要',renameText.includes('All cells <authored>')&&renameText.includes('Renamed <safe & exact>'));
  await confirm();source=(await objects()).gridSystems[0];check('改名不重配 key，不增加高水位、不產生 HTML',source.rules[0].ruleKey===1&&source.rules[0].name==='Renamed <safe & exact>'&&source.nextRuleKey===2&&await read(`!$('igRuleList').querySelector('safe')`));
  await ctl('[data-ig-rule-key="1"] [data-ig-rule-action="edit"]');await fill('#igRuleName','Native race candidate');const candidateRaw=await raw();await ctl('#igRulePreview');await impact();
  await fixture(`grid-source-rule ${sid} key 1 name-hex 496e646570656e64656e742066697874757265 selector all-cells divide 3 2`);const raceWorld=await dump(),raceCount=await history();await confirm();
  check('真 UI 確認遇到 native 變更拒絕舊候選，保留 raw／新 World／歷史',(await dump())===raceWorld&&await history()===raceCount&&JSON.stringify(await raw())===JSON.stringify(candidateRaw));await discard();await open(sid);
  await ctl('[data-ig-rule-key="1"] [data-ig-rule-action="edit"]');await fill('#igRuleName','History race candidate');await ctl('#igRulePreview');await impact();await query('line undo');const historyWorld=await dump(),historyRaw=await raw(),historyCount=await history();
  await read(`window.__ruleSent={original:window.fetch,confirms:0};window.fetch=async function(url,init){if(url==='/api'&&JSON.parse(init.body).cmd?.startsWith('line confirm '))window.__ruleSent.confirms++;return window.__ruleSent.original.call(window,url,init);};void 0`);
  try{await confirm();check('真 UI 確認遇到 metadata undo 換 frame，仍有效的 native token 不送出',(await dump())===historyWorld&&await history()===historyCount&&JSON.stringify(await raw())===JSON.stringify(historyRaw)&&await read('window.__ruleSent.confirms===0'));}
  finally{await read('window.fetch=window.__ruleSent.original;delete window.__ruleSent;void 0');}
  await open(sid);await discard();await open(sid);
  await ctl('[data-ig-rule-key="1"] [data-ig-rule-action="delete"]');const deleting=await dump();await ctl('#igRulePreview');await impact();await cancel();check('刪除必須先預覽，取消仍保留原規則',(await dump())===deleting&&(await objects()).gridSystems[0].rules.length===1);
  await ctl('#igRulePreview');await impact();await confirm();source=(await objects()).gridSystems[0];check('刪除保留 nextKey 高水位',source.rules.length===0&&source.nextRuleKey===2);
  await ctl('#igRuleAdd');await choose('#igRuleSelector','cell');await fill('#igRuleCellI','-2');await fill('#igRuleCellJ','1');await fill('#igRuleName','Negative authored cell');await ctl('#igRulePreview');await impact();await confirm();source=(await objects()).gridSystems[0];
  check('重建配 key2，不復用刪除 key；signed cell 保持字串',source.rules[0].ruleKey===2&&source.nextRuleKey===3&&JSON.stringify(source.rules[0].selector.cell)==='["-2","1"]');
  // Overlap and exact integer divisions are judged by the actual candidate.
  await ctl('#igRuleAdd');await choose('#igRuleSelector','cell');await read(`$('igGridView').scrollIntoView({block:'center'});void 0`);const point=await read(`(()=>{const g=$('igGridView'),c=g.dataset.igCamera.split(' ').map(Number),r=g.querySelector('[data-ig-plot]').getBoundingClientRect(),k=r.width/(c[2]-c[0]);return {x:r.left+(-900-c[0])*k,y:r.top+(600-c[1])*k};})()`);await click(point.x,point.y);await ctl('#igRuleUseCell');
  check('真點主格後明選使用目前主格，以 signed 原字串填規則欄位',await read(`$('igRuleCellI').value==='-2'&&$('igRuleCellJ').value==='1'&&ReferenceWorkspace.readGridDrafts().drafts.find(d=>d.draftId===$('infiniteGridWorkspace').dataset.draftId).ruleDraft.rawForm.cellI==='-2'`));const conflict=await dump(),conflictCount=await history();await ctl('#igRulePreview');await impact();
  check('同來源重疊 cell 真 native 拒絕並停用確認',await read(`$('impact-confirm').disabled&&document.querySelector('.impact-violation')!==null`)&&(await dump())===conflict&&await history()===conflictCount);await cancel();await ctl('#igRuleCancel');
  for(const [u,v] of [['0','2'],['66','2'],['1','1'],['7','2']]){
    await ctl('#igRuleAdd');await fill('#igRuleU',u);await fill('#igRuleV',v);const world=await dump(),n=await history(),draft=await raw();
    await read(`window.__ruleRangeApi=apiRequest;window.__ruleRangeWrites=[];apiRequest=async function(cmd,...rest){if(cmd.startsWith('line '))__ruleRangeWrites.push(cmd);return __ruleRangeApi(cmd,...rest);};void 0`);
    try{await ctl('#igRulePreview');if(u==='0'||u==='66'){
      await settled();check(`inline 1–65 拒絕 U${u}/V${v}，焦點/raw/World/history 保留且零 native mutation`,await read(`!document.querySelector('.reference-impact[open]')&&$('igDraftNote').textContent.includes('1 至 65')&&document.activeElement.id==='igRuleU'&&__ruleRangeWrites.length===0`)&&(await dump())===world&&await history()===n&&JSON.stringify(await raw())===JSON.stringify(draft));
    }else{await impact();check(`native 拒絕 U${u}/V${v}，raw/World/history 保留`,await read(`$('impact-confirm').disabled&&!!document.querySelector('.impact-violation')&&__ruleRangeWrites.some(cmd=>cmd.startsWith('line preview grid-source-rule '))`)&&(await dump())===world&&await history()===n&&JSON.stringify(await raw())===JSON.stringify(draft));await cancel();}
    }finally{await read(`apiRequest=__ruleRangeApi;delete window.__ruleRangeApi;delete window.__ruleRangeWrites;void 0`);}await ctl('#igRuleCancel');
  }
  await ctl('#igRuleAdd');await choose('#igRuleSelector','cell');await fill('#igRuleCellI','9007199254740993');await fill('#igRuleCellJ','-9007199254740995');await ctl('#igRulePreview');await impact();await confirm();source=(await objects()).gridSystems[0];
  check('大於 2^53 的正負索引一路原字串抵達 native',JSON.stringify(source.rules[1].selector.cell)==='["9007199254740993","-9007199254740995"]'&&source.rules[1].ruleKey===3);
  await ctl('#igRuleAdd');await choose('#igRuleSelector','cell');await fill('#igRuleName','Pending raw');await fill('#igRuleCellI','9007199254740997');await fill('#igRuleCellJ',' - ');await fill('#igRuleU',' 7 ');await fill('#igRuleV','');
  const rawBefore=await raw(),sceneBefore=await dump(),scopeBefore=await read('ReferenceWorkspace.getProjectState().id');
  check('未 blur 的空白／非法輸入及 signed 原文留在有限 /2 raw',rawBefore.ruleDraft.rawForm.divisionsU===' 7 '&&rawBefore.ruleDraft.rawForm.divisionsV===''&&rawBefore.ruleDraft.rawForm.cellJ===' - '&&await read(`document.activeElement.id==='igRuleV'`));
  const {file,downloads}=await saveProject();
  check('真正 Save 產生非空 ZIP，原生 World 未被 raw 確認',typeof file==='string'&&fs.statSync(file).size>0&&(await dump())===sceneBefore);
  const loaded=await P.unpack(new Uint8Array(fs.readFileSync(file)),zip);
  check('正式 ZIP /13 保存 raw、native rule/highwater 與兩類能力',loaded.manifest.format===P.GRID_RULE_FORMAT&&loaded.scene===sceneBefore&&JSON.stringify(loaded.manifest.featureAttachments.records[0].value)===JSON.stringify(rawBefore)&&loaded.manifest.requiredCapabilities.includes(P.SUBDIVISION_CAPABILITY)&&loaded.manifest.requiredCapabilities.includes(P.Features.GRID_RULE_SCHEMA));
  await newProject();check('開檔前確有新空白 context，未借用舊規則',(await objects()).gridSystems.length===0&&await raw()===null&&await read(`ReferenceWorkspace.getProjectState().id!==${JSON.stringify(scopeBefore)}`));
  await send('Page.setInterceptFileChooserDialog',{enabled:true});try{await ctl('#fileMenuBtn');await ctl('#btnOpenProject');const doc=await send('DOM.getDocument',{depth:0}),node=await send('DOM.querySelector',{nodeId:doc.result.root.nodeId,selector:'#projectFile'});await send('DOM.setFileInputFiles',{nodeId:node.result.nodeId,files:[file]});await settled();await wait(`oc.gridSystems.length===1`);}finally{await send('Page.setInterceptFileChooserDialog',{enabled:false});}
  check('新空白 context 真開檔恢復逐字 native 與 raw',(await dump())===sceneBefore&&JSON.stringify(await raw())===JSON.stringify(rawBefore));
  await ctl('#btnNewGridSystem');await wait(`!!$('gridDraftChooser')?.open`);
  await ctl(`#gridDraftChooser [data-draft-id="${rawBefore.draftId}"]`);await wait(`$('infiniteGridWorkspace')?.open&&!!$('igRuleName')&&!$('igRuleName').disabled`);
  check('正式重新進入來源恢復無效 raw，不自動配 key/確認',await read(`$('igRuleU').value===' 7 '&&$('igRuleV').value===''&&$('igRuleCellJ').value===' - '`)&&(await objects()).gridSystems[0].nextRuleKey===4);
  await ctl('#igRuleName');await shot('rule-editor-desktop-restored');await ctl('#igRuleCancel');
  // A rule-only native change must invalidate the full source baseline.
  await ctl('[data-ig-rule-key="2"] [data-ig-rule-action="edit"]');await fill('#igRuleName','Stale local edit');const staleRaw=await raw();
  await fixture(`grid-source-rule ${sid} key 2 name-hex 526163652066697874757265 selector cell -2 1 divide 3 2`);const staleWorld=await dump();await ctl('#igRulePreview');await settled();
  check('rule-only native 更新使舊 baseline 拒絕，不覆盖新規則',!await read(`!!document.querySelector('.reference-impact[open]')`)&&(await dump())===staleWorld&&JSON.stringify(await raw())===JSON.stringify(staleRaw)&&await read(`$('igDraftNote').textContent.includes('身分已變更')||$('igDraftNote').textContent.includes('來源已更新')`));
  await discard();await open(sid);
  await ctl('[data-ig-rule-key="2"] [data-ig-rule-action="edit"]');await fill('#igRuleName','Deleted source raw');const orphan=await raw();
  await fixture(`delete grid-system ${sid}`);await fixture(`grid-system ${sid} name-hex 52656275696c74 main-along none u repeat 0 600 v repeat 0 400`);
  const rebuilt=await dump();if(!await read(`$('igRulePreview').disabled`)){await ctl('#igRulePreview');await settled();}
  check('刪除與同 ID 重建不自動接管舊 rule raw 或耗 key',(await dump())===rebuilt&&JSON.stringify(await raw())===JSON.stringify(orphan)&&(await objects()).gridSystems[0].rules.length===0&&await read(`($('igDraftNote').textContent.includes('身分已變更')||$('igDraftNote').textContent.includes('已遺失'))`));await discard();await open(sid);
  await ctl('#igRuleAdd');const equalRaw=await raw(),definition=P.Features.gridSourceKey((await objects()).gridSystems[0]);
  await fixture(`delete grid-system ${sid}`);await fixture(`grid-system ${sid} name-hex 52656275696c74 main-along none u repeat 0 600 v repeat 0 400`);const equalWorld=await dump();
  if(!await read(`$('igRulePreview').disabled`)){await ctl('#igRulePreview');await settled();}check('同工作階段同 ID 同定義重建仍被永久孤兒 guard 拒絕',P.Features.gridSourceKey((await objects()).gridSystems[0])===definition&&(await dump())===equalWorld&&JSON.stringify(await raw())===JSON.stringify(equalRaw)&&await read(`($('igDraftNote').textContent.includes('場景已更新')||$('igDraftNote').textContent.includes('已遺失'))`));await discard();await open(sid);
  // Response arrives after an external context replacement. The old owner
  // cannot write the new frame or unscopingly cancel its candidate.
  await ctl('#igRuleAdd');await read(`(()=>{const g=window.__ruleDelay={original:window.apiRequest,release:null,cancels:0};window.apiRequest=async function(cmd,...args){if(cmd==='line cancel-preview')g.cancels++;const r=await g.original(cmd,...args);if(cmd.startsWith('line preview grid-source-rule')&&!g.release)return new Promise(resolve=>{g.release=()=>resolve(r);});return r;};return true;})()`);
  try{await ctl('#igRulePreview');await wait(`typeof window.__ruleDelay.release==='function'`);await read(`(()=>{const c=ReferenceWorkspace.history.makeContext();c.name='Synthetic replacement';ReferenceWorkspace.history.replace(c,[],'Race fixture');return true;})()`);const n=await history();await read(`window.__ruleDelay.release();void 0`);await settled();
    check('延遲 preview 失去 context 後不寫入、不開確認、不取消新 owner 候選',await history()===n&&await raw()===null&&!await read(`!!document.querySelector('.reference-impact[open]')`)&&await read(`window.__ruleDelay.cancels===0`));}
  finally{await read(`window.apiRequest=window.__ruleDelay.original;delete window.__ruleDelay;InfiniteGridWorkspace.close(true);void 0`);}
  // 390px is a real normal CRUD path, rather than desktop CSS inspection.
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await newProject();await ctl('#emptyNewGridSystem');await wait(`!!$('igName')&&!$('igName').disabled`);await fill('#igName','390 authored source');await ctl('#igSaveSource');await impact();await confirm();await ctl('#igRuleAdd');await choose('#igRuleSelector','cell');await fill('#igRuleCellI','-3');await fill('#igRuleCellJ','-1');await ctl('#igRulePreview');await impact();await confirm();
  source=(await objects()).gridSystems[0];check('390px 正常空白來源→signed cell→真 native 確認',source.rules.length===1&&JSON.stringify(source.rules[0].selector.cell)==='["-3","-1"]');
  await ctl('[data-ig-rule-key="1"] [data-ig-rule-action="edit"]');await fill('#igRuleName','390 renamed');await ctl('#igRulePreview');await impact();await cancel();check('390px 真取消不改已確認 native 名稱',(await objects()).gridSystems[0].rules[0].name!=='390 renamed');
  await ctl('#igRulePreview');await impact();await confirm();check('390px 真改名保持 key',(await objects()).gridSystems[0].rules[0].name==='390 renamed'&&(await objects()).gridSystems[0].rules[0].ruleKey===1);
  await ctl('#igRuleAdd');await fill('#igRuleU','1e');await ctl('#igRulePreview');await settled();check('無效等分指出正確 u 欄位並保留原文',await read(`document.activeElement.id==='igRuleU'&&$('igRuleU').value==='1e'&&$('igDraftNote').textContent.includes('規則 u 等分')`));
  const layout=await read(`(()=>{const d=$('infiniteGridWorkspace'),nodes=['igRuleName','igRuleSelector','igRuleU','igRuleV','igRulePreview','igRuleCancel'];return {overflow:d.scrollWidth>d.clientWidth+1,small:nodes.filter(id=>$(id).getBoundingClientRect().height<44),primary:[...d.querySelectorAll('.ig-footer .primary-button,.ig-footer .primary')].filter(n=>n.getClientRects().length).length};})()`);
  check('390px 無橫向溢出、規則控件至少44px、單一頁尾主動作',!layout.overflow&&layout.small.length===0&&layout.primary===1,layout);await shot('rule-editor-390-raw');
  const mobileScene=await dump(),mobileRaw=await raw(),mobile=await saveProject(),mobileZip=await P.unpack(new Uint8Array(fs.readFileSync(mobile.file)),zip),mobileSid=(await objects()).gridSystems[0].id;
  check('390px 真 Save 保存未確認 raw 與已確認 native',mobileZip.scene===mobileScene&&JSON.stringify(mobileZip.manifest.featureAttachments.records[0].value)===JSON.stringify(mobileRaw));
  await newProject();check('390px 開檔前新空白 context 沒有借用原場景',(await objects()).gridSystems.length===0&&await raw()===null);
  await send('Page.setInterceptFileChooserDialog',{enabled:true});try{await ctl('#fileMenuBtn');await ctl('#btnOpenProject');const doc=await send('DOM.getDocument',{depth:0}),node=await send('DOM.querySelector',{nodeId:doc.result.root.nodeId,selector:'#projectFile'});await send('DOM.setFileInputFiles',{nodeId:node.result.nodeId,files:[mobile.file]});await settled();await wait(`oc.gridSystems.length===1`);}finally{await send('Page.setInterceptFileChooserDialog',{enabled:false});}
  await open(mobileSid);check('390px 真重開與續編保留非法 raw、key、高水位',(await dump())===mobileScene&&JSON.stringify(await raw())===JSON.stringify(mobileRaw)&&await read(`$('igRuleU').value==='1e'`));await ctl('#igRuleName');await shot('rule-editor-390-reopened');await discard();
  await send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
  for(const [id,axes,reason] of [[901,'u repeat-panel 600 gap 0 from 0 v repeat 0 400','兩軸固定間距'],[902,'u repeat 0 600 v none','兩軸固定間距'],[903,'u repeat 0 600 v repeat 0 400 stagger 200','相鄰格子相位差']]){
    await fixture(`grid-system ${id} name-hex 556e737570706f72746564 main-along none ${axes}`);await open(id,false);const frozen=await dump();
    check(`不支援的來源 ${id} 明示原因並鎖住規則，不改其定義`,await read(`$('igRuleAdd').disabled&&$('igRuleReason').textContent.includes(${JSON.stringify(reason)})`)&&(await dump())===frozen);await leave();
  }
  // Normal entry regression: preserve raw, delete its source through the card,
  // resume from the empty-state button, then Save/new context/open/discard.
  // No fixture API or render/cache refresh substitutes for these user actions.
  for(const intent of ['edit','delete']){
    await newProject();await ctl('#emptyNewGridSystem');await wait(`!!$('igName')&&!$('igName').disabled`);await fill('#igName',`Orphan authored ${intent}`);await ctl('#igSaveSource');await impact();await confirm();
    await ctl('#igRuleAdd');await ctl('#igRulePreview');await impact();await confirm();
    await ctl(`[data-ig-rule-key="1"] [data-ig-rule-action="${intent}"]`);if(intent==='edit')await fill('#igRuleName','Pending orphan raw');const ownedRaw=await raw(),ownedId=ownedRaw.baseRef.id;
    await leave();await ctl(`.ocard[data-kind="grid-system"][data-id="${ownedId}"]`);await ctl('.gi-delete-section > summary');await ctl('#gridObjectDelete');await settled();
    if(await read(`!!document.querySelector('.reference-impact[open]')`))await confirm();await wait('oc.gridSystems.length===0');
    const orphanScene=await dump(),orphanCount=await history();
    check(`${intent} 正式卡片刪除來源保留原始 rule 草稿`,JSON.stringify(await raw())===JSON.stringify(ownedRaw));
    await ctl('#emptyNewGridSystem');await wait(`!!$('gridDraftChooser')?.open`);await ctl(`#gridDraftChooser [data-draft-id="${ownedRaw.draftId}"]`);await wait(`!!$('infiniteGridWorkspace')?.open&&typeof $('igClose')?.onclick==='function'`);
    check(`${intent} 空狀態續編 orphan 不改 World/raw/history`,(await dump())===orphanScene&&await history()===orphanCount&&JSON.stringify(await raw())===JSON.stringify(ownedRaw));
    check(`${intent} orphan 明示遺失、鎖住發布與輸入，保存/返回/捨棄可用`,await read(`$('igTitle').textContent.includes('已遺失')&&$('igRulePreview').disabled&&$('igRuleName').disabled&&$('igSaveSource').disabled&&!$('igDiscardDraft').disabled&&!!document.querySelector('#infiniteGridWorkspace .workspace-project-header')&&!$('igClose').disabled`));
    await shot(`rule-editor-orphan-${intent}`);const saved=await saveProject(),package_=await P.unpack(new Uint8Array(fs.readFileSync(saved.file)),zip);
    check(`${intent} orphan 真 Save ZIP 保留原 pin、raw 及無來源 native`,package_.scene===orphanScene&&JSON.stringify(P.Features.gridDrafts(package_.manifest.featureAttachments.records[0].value).drafts[0])===JSON.stringify(ownedRaw)&&P.Features.gridDrafts(package_.manifest.featureAttachments.records[0].value).orphans.includes(ownedRaw.draftId)&&(await objects()).gridSystems.length===0);
    await newProject();await send('Page.setInterceptFileChooserDialog',{enabled:true});
    try{await ctl('#fileMenuBtn');await ctl('#btnOpenProject');const doc=await send('DOM.getDocument',{depth:0}),node=await send('DOM.querySelector',{nodeId:doc.result.root.nodeId,selector:'#projectFile'});await send('DOM.setFileInputFiles',{nodeId:node.result.nodeId,files:[saved.file]});await settled();await wait(`!!ReferenceWorkspace.readFeatureAttachment('grid-draft')`);}
    finally{await send('Page.setInterceptFileChooserDialog',{enabled:false});}
    await ctl('#emptyNewGridSystem');await wait(`!!$('gridDraftChooser')?.open`);await ctl(`#gridDraftChooser [data-draft-id="${ownedRaw.draftId}"]`);await wait(`$('infiniteGridWorkspace')?.open&&!!$('igRuleName')&&$('igRuleName').disabled`);
    check(`${intent} 新 context 真重開 orphan 仍唯讀，不默認新建或重關聯`,(await dump())===orphanScene&&JSON.stringify(await raw())===JSON.stringify(ownedRaw)&&(await objects()).gridSystems.length===0&&await read(`$('igRulePreview').disabled&&$('igTitle').textContent.includes('已遺失')`));
    await leave();check(`${intent} orphan 真返回解除 modal 且保留 raw`,!await read(`$('infiniteGridWorkspace').open`)&&JSON.stringify(await raw())===JSON.stringify(ownedRaw));
    await ctl('#emptyNewGridSystem');await wait(`!!$('gridDraftChooser')?.open`);await ctl(`#gridDraftChooser [data-draft-id="${ownedRaw.draftId}"]`);await wait(`$('infiniteGridWorkspace')?.open&&!!$('igDiscardDraft')&&!$('igDiscardDraft').disabled`);await discard();await leave();
    check(`${intent} orphan 明確捨棄只清 raw，不創建 native 來源`,await raw()===null&&(await dump())===orphanScene&&(await objects()).gridSystems.length===0);
    console.log(`P87 orphan ${intent} saved artifact ${saved.file}`);
  }
  check('本切片真 UI 沒有新增未捕捉瀏覽器錯誤',exceptionCount()===startExceptions);
  fs.writeFileSync(path.join(downloads,'rule-editor-roundtrip.json'),JSON.stringify({scene:sceneBefore,raw:rawBefore,manifest:loaded.manifest,sourceId:sid},null,2));console.log('P87 saved artifact '+file);
  fs.writeFileSync(path.join(mobile.downloads,'rule-editor-roundtrip.json'),JSON.stringify({scene:mobileScene,raw:mobileRaw,manifest:mobileZip.manifest,sourceId:mobileSid},null,2));console.log('P87 mobile saved artifact '+mobile.file);
};
