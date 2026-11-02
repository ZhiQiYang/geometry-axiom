/* Real file-menu entry for definition-import/1.
   Fresh reopen clears this origin's storage and navigates the same tab.
   It does not start a second Chrome user-data-dir.
   Because it wipes origin storage (seen-guidance flags included), cdp_test.js runs it last in full mode. */
const cdp = require('./cdp_helpers.js');
const fs = require('fs');
const os = require('os');
const path = require('path');
const {waitForExpectedNavigation} = require('./cdp_navigation.js');

module.exports = async ({send, eval_, sleep, click, waitForUI, exceptionCount}) => {
  const check = cdp.makeCheck({prefix:'P359 ', throwOnFail:true, detail:'none', failMessage:name => 'P359 ' + name});
  const read = cdp.makeRead(eval_);
  const wait = (expression, timeout = 20000) => waitForUI(expression, timeout);
  const ctl = cdp.makeCtl({eval_, sleep, click}, {
    scroll:'center', attempts:12, pollMs:70, settleMs:120,
    unreachable:(selector, point) => 'R08 unreachable ' + selector + ' ' + JSON.stringify(point)
  });
  const key = cdp.makeKey({send, sleep});
  const fill = cdp.makeFill({ctl, key, send, sleep});
  const started = exceptionCount();
  console.log('=== P359. 從其他專案匯入定義（R08） ===');
  await send('Emulation.setDeviceMetricsOverride', {width:1400, height:1000, deviceScaleFactor:1, mobile:false});

  const rule = (id, version, name) => ({
    id, version, name,
    slots:[{id:1, name:'主支'}, {id:2, name:'副支'}],
    members:[{id:1, slotId:1}, {id:2, slotId:1}, {id:3, slotId:2}],
    joints:[
      {id:1, kind:'end-to-side', scope:'left', terminatedMember:3, targetMember:1, end:'start', side:'+u', dir:'u'},
      {id:2, kind:'end-to-side', scope:'right', terminatedMember:3, targetMember:2, end:'finish', side:'-u', dir:'u'}
    ]
  });
  const face = (sourceA, sourceB, slotId = 1) => ({slotId, A:sourceA, B:sourceB, contactFace:'A', orientation:'B'});
  const install = await read(`(()=>{
    window.__diSpec = async (name, value) => {
      let result = await apiRequest('line spec ' + name + ' ' + value);
      if (result.preview) {
        if (!result.preview.valid) return result;
        result = await apiRequest('line confirm ' + result.preview.token);
      }
      return result;
    };
    window.__diApply = async operations => {
      const readState = await apiRequest('assembly-read');
      if (!readState.ok) return {ok:false, stage:'read', body:readState};
      const response = await fetch('/assembly/preview', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({schema:'assembly-transaction/1', expectedRevision:readState.revision, operations})});
      const preview = await response.json();
      if (!preview.ok || !preview.preview || !preview.preview.valid) return {ok:false, stage:'preview', body:preview};
      return api('assembly-confirm ' + preview.preview.token);
    };
    window.__diDump = async () => {
      const result = await apiRequest('dump');
      if (!result.ok) throw Error(JSON.stringify(result));
      return result.text;
    };
    return typeof window.__diSpec === 'function';
  })()`);
  check('頁面可建立匯入夾具', install === true);
  const reset = await read(`apiRequest('reset')`);
  if (!reset.ok) throw Error('R08 reset failed ' + JSON.stringify(reset));
  const sourceSpec = await read(`__diSpec('柱寬', 27)`);
  if (!sourceSpec.ok) throw Error('R08 source spec failed ' + JSON.stringify(sourceSpec));
  const sourceApply = await read(`__diApply(${JSON.stringify([
    {op:'publish-rule', value:rule(1, 1, 'S框架')},
    {op:'publish-material', value:{id:'sharedwood', version:1, kind:'timber', name:'共享', A:27, B:33}},
    {op:'publish-material', value:{id:'otherwood', version:1, kind:'timber', name:'另一', A:45, B:90}},
    {op:'put-parameter', value:{id:0, name:'S卡', fields:[{id:1, name:'W', type:'dimension', input:'27'}]}},
    {op:'put-parameter', value:{id:1, name:'S衍生', fields:[{id:1, name:'W', type:'dimension', input:'=@0:1 + 6 mm'}]}},
    {op:'put-binding', value:{id:1, name:'來源配置', rule:{id:1, version:1}, slots:[
      face({kind:'parameter', parameterId:1, fieldId:1}, {kind:'spec', name:'柱寬'}),
      face({kind:'material', id:'sharedwood', version:1, field:'A'}, {kind:'material', id:'otherwood', version:1, field:'B'}, 2)
    ]}}
  ])})`);
  if (!sourceApply.ok) throw Error('R08 source assembly failed ' + JSON.stringify(sourceApply));
  const sourceB64 = await read(`(async()=>{
    const bytes = new Uint8Array(await ReferenceWorkspace.exportBytes());
    let binary = '';
    for (let index = 0; index < bytes.length; index += 0x4000) binary += String.fromCharCode.apply(null, bytes.subarray(index, Math.min(index + 0x4000, bytes.length)));
    return btoa(binary);
  })()`);
  const sourceFile = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'geometry-definition-import-')), 'source.gcanvas');
  fs.writeFileSync(sourceFile, Buffer.from(sourceB64, 'base64'));
  const resetAgain = await read(`apiRequest('reset')`);
  if (!resetAgain.ok) throw Error('R08 target reset failed ' + JSON.stringify(resetAgain));
  const targetSpec = await read(`__diSpec('柱寬', 30)`);
  if (!targetSpec.ok) throw Error('R08 target spec failed ' + JSON.stringify(targetSpec));
  const targetApply = await read(`__diApply(${JSON.stringify([
    {op:'publish-rule', value:rule(1, 1, '目標框架')},
    {op:'publish-material', value:{id:'sharedwood', version:1, kind:'timber', name:'共享', A:27, B:33}},
    {op:'put-parameter', value:{id:0, name:'目標卡', fields:[{id:1, name:'W', type:'dimension', input:'10'}]}},
    {op:'put-binding', value:{id:1, name:'目標配置', rule:{id:1, version:1}, slots:[face({kind:'literal', value:27}, {kind:'literal', value:33}), face({kind:'literal', value:27}, {kind:'literal', value:33}, 2)]}}
  ])})`);
  if (!targetApply.ok) throw Error('R08 target assembly failed ' + JSON.stringify(targetApply));
  const before = await read(`__diDump()`);

  check('匯入入口只在檔案選單', await read(`document.querySelectorAll('#btnDefinitionImport').length===1 && $('btnDefinitionImport').closest('#fileMenuPop') && $('btnDefinitionImport').textContent.includes('從其他專案匯入定義')`));
  await send('Page.setInterceptFileChooserDialog', {enabled:true});
  try {
    await ctl('#fileMenuBtn');
    await wait(`!$('fileMenuPop').hidden`);
    await ctl('#btnDefinitionImport');
    const documentNode = await send('DOM.getDocument', {depth:0});
    const input = await send('DOM.querySelector', {nodeId:documentNode.result.root.nodeId, selector:'#definitionImportFile'});
    await send('DOM.setFileInputFiles', {nodeId:input.result.nodeId, files:[sourceFile]});
    await wait(`$('definitionImportDialog').open && !!document.querySelector('#definitionImportBindings input[data-di-binding="1"]')`);
  } finally {
    await send('Page.setInterceptFileChooserDialog', {enabled:false});
  }
  check('來源檔名顯示在對話框', await read(`$('definitionImportSource').textContent==='source.gcanvas'`));
  await ctl('#definitionImportPreview');
  await wait(`$('definitionImportStatus').textContent.includes('匯入根不得是空的')`);
  check('空的匯入根被拒且世界不變', await read(`(async()=> (await __diDump())===${JSON.stringify(before)})()`));
  await ctl('#definitionImportBindings input[data-di-binding="1"]');
  await ctl('#definitionImportPreview');
  await wait(`$('definitionImportStatus').textContent.includes('IMPORT_RENAME_REQUIRED') && !!document.querySelector('#definitionImportNames [data-di-row="柱寬"]')`);
  check('未選擇撞名處理時不發確認權杖', await read(`(async()=> $('definitionImportConfirm').disabled && (await __diDump())===${JSON.stringify(before)})()`));
  await ctl('#definitionImportNames input[data-di-mode="rename"]');
  await fill('#definitionImportNames input[data-di-rename="柱寬"]', '柱寬匯入');
  await ctl('#definitionImportPreview');
  await wait(`!$('definitionImportConfirm').disabled && $('definitionImportClosure').textContent.includes('規格 柱寬 → 柱寬匯入（rename）')`);
  const previewText = await read(`$('definitionImportClosure').textContent`);
  check('預覽列出重寫後的規格', previewText.includes('規格 柱寬 → 柱寬匯入（rename）'), previewText);

  // Cancel requests go through a test gate, so the races below do not depend
  // on which request reaches the bridge first.
  const gateInstalled = await read(`(()=>{
    window.__diRealApi = api;
    window.__diCancelLog = [];
    window.__diCancelMode = 'pass';
    window.api = async cmd => {
      if (typeof cmd === 'string' && cmd.startsWith('definition-import-cancel ')) {
        window.__diCancelLog.push(cmd.slice('definition-import-cancel '.length));
        if (window.__diCancelMode === 'transport') return {ok:false, transport:true, error:'測試：取消結果尚未確認'};
        if (window.__diCancelMode === 'hold') await new Promise(resolve => { window.__diReleaseCancel = resolve; });
      }
      return window.__diRealApi(cmd);
    };
    return true;
  })()`);
  if (gateInstalled !== true) throw Error('R08 cancel gate not installed');
  const forceConfirm = `(()=>{ $('definitionImportConfirm').disabled = false; $('definitionImportConfirm').click(); return true; })()`;
  const unchanged = `(async()=> (await __diDump())===${JSON.stringify(before)})()`;
  try {
    // B1: editing a name choice after a valid preview makes it stale at once.
    await fill('#definitionImportNames input[data-di-rename="柱寬"]', '柱寬改名');
    check('改名稱後確認立即停用', await read(`$('definitionImportConfirm').disabled===true`));
    await read(forceConfirm);
    await sleep(500);
    check('改名稱後強制確認也不寫入舊預覽', await read(unchanged));
    await ctl('#definitionImportPreview');
    await wait(`!$('definitionImportConfirm').disabled && $('definitionImportClosure').textContent.includes('規格 柱寬 → 柱寬改名（rename）')`);
    check('重新預覽後帶入新名稱', await read(`$('definitionImportClosure').textContent.includes('規格 柱寬 → 柱寬改名（rename）')`));
    await ctl('#definitionImportNames input[data-di-mode="map-existing"]');
    check('改成沿用既有名稱後確認立即停用', await read(`$('definitionImportConfirm').disabled===true`));
    await read(forceConfirm);
    await sleep(500);
    check('改成沿用既有名稱後強制確認也不寫入', await read(unchanged));
    await ctl('#definitionImportNames input[data-di-mode="rename"]');
    await fill('#definitionImportNames input[data-di-rename="柱寬"]', '柱寬匯入');
    await ctl('#definitionImportPreview');
    await wait(`!$('definitionImportConfirm').disabled && $('definitionImportClosure').textContent.includes('規格 柱寬 → 柱寬匯入（rename）')`);

    // B2: toggling a root and confirming in the same task, while the cancel
    // of the old token is still in flight, must not publish the old candidate.
    await read(`window.__diCancelMode = 'hold'; true`);
    const raced = await read(`(()=>{
      document.querySelector('#definitionImportBindings input[data-di-binding="1"]').click();
      const disabled = $('definitionImportConfirm').disabled;
      $('definitionImportConfirm').disabled = false;
      $('definitionImportConfirm').click();
      return disabled;
    })()`);
    check('改勾匯入根後確認立即停用', raced === true);
    await sleep(500);
    await read(`window.__diCancelMode = 'pass'; if (window.__diReleaseCancel) window.__diReleaseCancel(); true`);
    await sleep(500);
    check('改勾匯入根後立即確認也不發布舊候選', await read(unchanged));
    await ctl('#definitionImportBindings input[data-di-binding="1"]');
    await ctl('#definitionImportPreview');
    await wait(`!$('definitionImportConfirm').disabled && $('definitionImportClosure').textContent.includes('規格 柱寬 → 柱寬匯入（rename）')`);

    // B3: an unconfirmed cancel keeps the dialog and the token for a retry.
    await read(`window.__diCancelLog = []; window.__diCancelMode = 'transport'; true`);
    await ctl('#definitionImportClose');
    await wait(`window.__diCancelLog.length === 1 && $('definitionImportStatus').textContent.includes('取消結果尚未確認')`);
    await sleep(300);
    check('取消結果未確認時保留對話框', await read(`$('definitionImportDialog').open === true`));
    await ctl('#definitionImportPreview');
    await wait(`window.__diCancelLog.length === 2`);
    check('新預覽前仍以同一個權杖重試取消', await read(`window.__diCancelLog[1] === window.__diCancelLog[0] && ${unchanged}`));
    await read(`window.__diCancelMode = 'pass'; true`);
    await ctl('#definitionImportClose');
    await wait(`!$('definitionImportDialog').open`);
    check('重試取消用同一個權杖並關閉', await read(`window.__diCancelLog.length === 3 && window.__diCancelLog[2] === window.__diCancelLog[0]`));
  } finally {
    await read(`if (window.__diRealApi) { window.api = window.__diRealApi; delete window.__diRealApi; } window.__diCancelMode = 'pass'; if (window.__diReleaseCancel) window.__diReleaseCancel(); true`);
  }

  // Reopen the same source for the original cancel / confirm path.
  await send('Page.setInterceptFileChooserDialog', {enabled:true});
  try {
    await ctl('#fileMenuBtn');
    await wait(`!$('fileMenuPop').hidden`);
    await ctl('#btnDefinitionImport');
    const documentAgain = await send('DOM.getDocument', {depth:0});
    const inputAgain = await send('DOM.querySelector', {nodeId:documentAgain.result.root.nodeId, selector:'#definitionImportFile'});
    await send('DOM.setFileInputFiles', {nodeId:inputAgain.result.nodeId, files:[sourceFile]});
    await wait(`$('definitionImportDialog').open && !!document.querySelector('#definitionImportBindings input[data-di-binding="1"]')`);
  } finally {
    await send('Page.setInterceptFileChooserDialog', {enabled:false});
  }
  await ctl('#definitionImportBindings input[data-di-binding="1"]');
  await ctl('#definitionImportPreview');
  await wait(`$('definitionImportStatus').textContent.includes('IMPORT_RENAME_REQUIRED') && !!document.querySelector('#definitionImportNames [data-di-row="柱寬"]')`);
  await ctl('#definitionImportNames input[data-di-mode="rename"]');
  await fill('#definitionImportNames input[data-di-rename="柱寬"]', '柱寬匯入');
  await ctl('#definitionImportPreview');
  await wait(`!$('definitionImportConfirm').disabled && $('definitionImportClosure').textContent.includes('規格 柱寬 → 柱寬匯入（rename）')`);
  await ctl('#definitionImportCancel');
  await wait(`$('definitionImportStatus').textContent.includes('已取消預覽') && $('definitionImportConfirm').disabled`);
  check('取消預覽不寫入世界', await read(`(async()=> (await __diDump())===${JSON.stringify(before)})()`));
  await ctl('#definitionImportPreview');
  await wait(`!$('definitionImportConfirm').disabled`);
  await ctl('#definitionImportConfirm');
  await wait(`!$('definitionImportDialog').open && document.getElementById('status').textContent.includes('已匯入 6 項，可復原')`);
  const imported = await read(`__diDump()`);
  check('確認後目標規格保留、新名稱帶入來源值', imported.includes('spec 柱寬 30') && imported.includes('spec 柱寬匯入 27'), imported);

  const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), 'geometry-definition-import-save-'));
  await send('Browser.setDownloadBehavior', {behavior:'allow', downloadPath:downloadDir});
  await read(`window.__diPicker=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});void 0`);
  let saved = null;
  try {
    await ctl('#projectBar [data-project-action="save"]');
    for (let attempt = 0; attempt < 150; attempt++) {
      const names = fs.readdirSync(downloadDir).filter(name => name.endsWith('.gcanvas'));
      if (names.length === 1) { saved = path.join(downloadDir, names[0]); break; }
      if (names.length > 1) throw Error('R08 ambiguous project download');
      await sleep(100);
    }
  } finally {
    await read(`if(window.__diPicker)Object.defineProperty(window,'showSaveFilePicker',window.__diPicker);else delete window.showSaveFilePicker;delete window.__diPicker;void 0`);
  }
  if (!saved) throw Error('R08 save did not write a .gcanvas');
  check('確認後可以保存完整專案', fs.statSync(saved).size > 0);

  await read(`localStorage.setItem('definition-import-fresh','1')`);
  const marker = require('crypto').randomUUID();
  await send('Page.addScriptToEvaluateOnNewDocument', {source:`window.__cdpExpectedNavigationMarker=${JSON.stringify(marker)};`});
  await send('Storage.clearDataForOrigin', {origin:new URL(process.env.GEOMETRY_TEST_URL).origin, storageTypes:'all'});
  await send('Page.navigate', {url:process.env.GEOMETRY_TEST_URL});
  await waitForExpectedNavigation({
    evaluate:eval_, marker, label:'R08 fresh profile', timeout:30000,
    condition:`typeof api==='function' && typeof oc==='object' && connection.phase==='ready'`
  });
  check('清掉來源儲存後重開不再留著舊分頁標記', await read(`localStorage.getItem('definition-import-fresh')===null`));
  await send('Page.setInterceptFileChooserDialog', {enabled:true});
  try {
    await ctl('#fileMenuBtn');
    await wait(`!$('fileMenuPop').hidden`);
    await ctl('#btnOpenProject');
    const reopened = await send('DOM.getDocument', {depth:0});
    const projectInput = await send('DOM.querySelector', {nodeId:reopened.result.root.nodeId, selector:'#projectFile'});
    await send('DOM.setFileInputFiles', {nodeId:projectInput.result.nodeId, files:[saved]});
    await wait(`(async()=>{if(ReferenceWorkspace.busy)return false; const result=await apiRequest('dump'); return result.ok===true && result.text.includes('spec 柱寬 30') && result.text.includes('spec 柱寬匯入 27');})()`);
  } finally {
    await send('Page.setInterceptFileChooserDialog', {enabled:false});
  }
  check('fresh profile 重開後匯入結果仍在', await read(`(async()=>{const result=await apiRequest('dump'); return result.text.includes('spec 柱寬 30') && result.text.includes('spec 柱寬匯入 27');})()`));
  check('這段沒有新增未捕捉的頁面例外', exceptionCount() === started);
};
