'use strict';
/* Windows formal UI: grid source/binding, assembly generation, model library.
   Download fallback because headless Chrome has no operable native save picker.
   Does not rerun the cited 16/35/33 suites. */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const qa = require('D:/geometry-axiom-inspector-draft/geometry-web/docs/evidence/qa-acceptance-d6b4b45-20261005/tools/qa_cdp.js');

const TEST_URL = process.env.GEOMETRY_TEST_URL;
const ROOT = 'D:/geometry-axiom-inspector-draft';
const OUT = process.env.GEOMETRY_PHASE3_OUT;
const CHROME = process.env.GEOMETRY_CHROME;
const CDP = Number(process.env.GEOMETRY_CDP_PORT || 9516);
if (!TEST_URL || !OUT || !CHROME) throw Error('GEOMETRY_TEST_URL, GEOMETRY_PHASE3_OUT, GEOMETRY_CHROME required');
fs.mkdirSync(OUT, { recursive: true });
const shots = path.join(OUT, 'shots');
fs.mkdirSync(shots, { recursive: true });
const example = path.join(ROOT, 'geometry-web/examples/assembly-generation-v1.gcanvas');

const results = [];
let b;
const sha = buf => crypto.createHash('sha256').update(buf).digest('hex');
function record(name, ok, detail) {
  results.push({ name, ok: !!ok, detail: detail === undefined ? null : detail });
  console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail === undefined ? '' : ' ' + JSON.stringify(detail)));
}
async function shot(name) {
  const file = path.join(shots, name + '.png');
  await b.screenshot(file);
  const bytes = fs.readFileSync(file);
  return { file: path.basename(file), bytes: bytes.length, sha256: sha(bytes) };
}
async function idle() { await b.waitFor('!oc.busy && !ReferenceWorkspace.busy', 30000); }
async function read(expr) { return b.evalReadOnly(expr); }
async function dump() {
  return read(`(async()=>{const r=await apiRequest('dump');if(!r.ok)throw Error(JSON.stringify(r));return r.text;})()`);
}
async function objects() { return read(`apiRequest('objects').then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})`); }
async function refs() { return read(`apiRequest('references').then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})`); }
async function assembly() { return read(`apiRequest('assembly-read').then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r.state;})`); }
async function project() {
  return read(`(async()=>{const c=ReferenceWorkspace.context();return {id:c.id,name:c.name,dirty:!!c.dirty,saved:!!c.saved,downloaded:!!c.downloaded,models:(ReferenceWorkspace.getSpaceModels()||[]).map(m=>({id:m.id,name:m.name,source:m.source&&m.source.scene_sha256||m.result&&m.result.source_sha256||null}))};})()`);
}
async function confirmImpact() {
  await b.waitFor(`!!document.querySelector('.reference-impact[open] #impact-confirm') && !$('impact-confirm').disabled`, 20000);
  const before = await dump();
  await b.click('#impact-confirm');
  await b.waitFor(`!document.querySelector('.reference-impact[open]')`, 20000);
  await idle();
  return before;
}
async function keyRaw(key, code, vk) {
  await b.send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key, code, windowsVirtualKeyCode: vk });
  await b.send('Input.dispatchKeyEvent', { type: 'keyUp', key, code, windowsVirtualKeyCode: vk });
}
async function choose(selector, value) {
  const wanted = String(value);
  const n = await read(`(()=>{const n=document.querySelector(${JSON.stringify(selector)});if(!n)return -2;return [...n.options].filter(o=>!o.disabled).findIndex(o=>o.value===${JSON.stringify(wanted)});})()`);
  if (n < 0) throw Error('Missing enabled option ' + selector + '=' + wanted + ' index ' + n);
  await b.click(selector);
  await keyRaw('Home', 'Home', 36);
  for (let i = 0; i < n; i++) await b.press('ArrowDown', { settle: 40 });
  await b.press('Enter', { settle: 80 });
  await b.waitFor(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(wanted)}`, 8000);
}
async function clickIfHit(selector) {
  const ok = await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)return false;const r=e.getBoundingClientRect();if(r.width<1||r.height<1)return false;const x=Math.min(Math.max(r.x+r.width/2,1),innerWidth-2),y=Math.min(Math.max(r.y+r.height/2,1),innerHeight-2);const h=document.elementFromPoint(x,y);return !!h&&(h===e||e.contains(h));})()`);
  if (!ok) return false;
  await b.click(selector);
  await idle();
  return true;
}
async function recover() {
  b.setDialogPolicy('accept');
  if (await read(`!!document.querySelector('.reference-impact[open]')`)) await clickIfHit('.reference-impact .impact-actions button:first-child');
  await clickIfHit('#igDiscardDraft');
  await clickIfHit('#igClose');
  await clickIfHit('#asmClose');
  await clickIfHit('#smClose');
  await clickIfHit('#workspaceBackButton');
  await b.press('Escape');
}
async function command(line) {
  const visible = await read(`(()=>{const e=document.getElementById('cmd');if(!e)return false;const r=e.getBoundingClientRect();return r.width>0&&r.height>0;})()`);
  if (!visible) await b.click('#cmdToggle');
  await b.waitFor(`(()=>{const e=document.getElementById('cmd');const r=e.getBoundingClientRect();return r.width>0&&r.height>0;})()`, 8000);
  await b.fill('#cmd', line, { enter: true });
  await b.sleep(250);
  if (await read(`!!document.querySelector('.reference-impact[open]')`)) await confirmImpact();
  await idle();
  const status = await b.readText('#status');
  if (status && status.includes('✗')) throw Error(line + ' ' + status);
  await b.press('Escape');
  await idle();
}
async function newProject() {
  b.setDialogPolicy('accept');
  await b.click('#fileMenuBtn');
  await b.click('#btnNewProject');
  await idle();
  await b.press('Escape');
  await b.waitFor(`(async()=>{const r=await apiRequest('objects');return r.ok&&r.faces.length===0&&r.gridSystems.length===0;})()`, 20000);
}
async function saveDownload(dirName) {
  const dir = path.join(OUT, dirName);
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  await b.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: dir, eventsEnabled: true });
  await b.click('#projectBar [data-project-action="save"]');
  const download = await b.waitForDownload(dir, '.gcanvas', 30000);
  const bytes = fs.readFileSync(download.file);
  const stable = path.join(OUT, dirName + '.gcanvas');
  fs.copyFileSync(download.file, stable);
  return { file: stable, size: bytes.length, sha256: sha(bytes), downloaded: await project() };
}
async function openFile(file) {
  await b.chooseFileOnNext(file);
  await b.click('#fileMenuBtn');
  await b.click('#btnOpenProject');
  const chooser = await b.waitForChooser();
  await idle();
  await b.waitFor('!ReferenceWorkspace.busy', 30000);
  return chooser;
}
function gridSemantic(dumpText, obj, ref) {
  return {
    dump: dumpText,
    systems: (obj.gridSystems || []).map(g => ({ id: g.id, name: g.name, mode: g.mode })),
    bindings: (obj.gridBindings || []).map(g => ({ id: g.id, system: g.system, boundary: g.boundary, cell: g.cell, vertexKey: g.vertexKey })),
    grids: (ref.grids || []).map(g => ({ id: g.id, surface: g.surface, bindingId: g.bindingId, sourceSystem: g.sourceSystem }))
  };
}

(async () => {
  const head = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: ROOT, encoding: 'utf8' }).trim();
  const status = execFileSync('git', ['status', '--porcelain=v1'], { cwd: ROOT, encoding: 'utf8' });
  const runtime = await fetch(new URL('/runtime', TEST_URL)).then(r => r.json());
  const identity = { head, status, runtime: { version: runtime.version, fresh: runtime.fresh, pid: runtime.pid, session: runtime.session, root: runtime.root }, modelBase: process.env.GEOMETRY_MODEL_BASE || null };
  fs.writeFileSync(path.join(OUT, 'identity.json'), JSON.stringify(identity, null, 2));
  console.log('IDENTITY ' + JSON.stringify(identity));
  if (status !== '') throw Error('worktree not clean');
  if (runtime.fresh !== true) throw Error('runtime not fresh');
  b = await qa.launch({
    chrome: CHROME,
    port: CDP,
    profileDir: path.join(OUT, 'chrome-profile-5'),
    downloadDir: path.join(OUT, 'downloads'),
    width: 1440,
    height: 1000,
    cleanupProfile: false
  });
  b.setDialogPolicy('accept');
  await b.goto(TEST_URL);
  await b.waitFor(`typeof connection==='object' && connection.phase==='ready' && typeof ReferenceWorkspace==='object'`, 40000);
  record('正式頁面標題', await read(`document.title==='構形 Canvas · 工程規格與空間建模'`));

  let gridFile = null;
  let gridSaved = null;
  try {
    await newProject();
    await command('boundary 1 outline 0,0 1200,0 1200,800 0,800');
    await command('placement 1 on boundary 1 origin 0 0 0 u +x v +y');
    const host = await dump();
    record('命令建立 1200×800 面', host.includes('boundary 1') && host.includes('placement 1'));
    await b.click('#btnNewGridSystem');
    await b.waitFor(`!!$('infiniteGridWorkspace')?.open && !$('igName').disabled`, 15000);
    await b.fill('#igName', '假格網甲');
    await b.press('Tab');
    await b.click('#igUSource input[value="repeat"]');
    await b.fill('#igUPhase', '0'); await b.press('Tab');
    await b.fill('#igUStep', '200'); await b.press('Tab');
    await b.click('#igVSource input[value="repeat"]');
    await b.fill('#igVPhase', '0'); await b.press('Tab');
    await b.fill('#igVStep', '100'); await b.press('Tab');
    await b.click('#igMainAlong input[value="none"]');
    const beforeSource = await dump();
    await b.click('#igSaveSource');
    const previewSource = await dump();
    record('來源預覽尚未寫入世界', previewSource === beforeSource);
    await confirmImpact();
    const systems = (await objects()).gridSystems;
    record('已建立無限來源', systems.length === 1 && systems[0].name === '假格網甲' && systems[0].mode === 'infinite', systems.map(g => ({ id: g.id, name: g.name, mode: g.mode })));
    await b.click('#igNewBinding');
    await b.waitFor(`!!$('igBoundary') && !$('igBoundary').disabled`, 10000);
    await choose('#igBoundary', '1');
    await b.waitFor(`$('igVertex') && $('igVertex').options.length>1 && !$('igCellI').disabled`, 10000);
    await choose('#igVertex', 'outer:0');
    await b.fill('#igCellI', '0'); await b.press('Tab');
    await b.fill('#igCellJ', '0'); await b.press('Tab');
    const beforeBinding = await dump();
    await b.click('#igSaveBinding');
    record('配置預覽尚未寫入世界', (await dump()) === beforeBinding);
    await confirmImpact();
    const bindings = (await objects()).gridBindings;
    record('配置保存 cell 0,0 與頂點 key', bindings.length === 1 && bindings[0].cell.join(',') === '0,0' && bindings[0].vertexKey > 0, bindings);
    await choose('#igSurface', '1');
    const beforeApply = await dump();
    await b.click('#igApplyBinding');
    record('套用預覽尚未寫入世界', (await dump()) === beforeApply);
    await confirmImpact();
    const applied = gridSemantic(await dump(), await objects(), await refs());
    record('套用後主格引用同一配置與來源', applied.grids.length === 1 && applied.grids[0].bindingId === bindings[0].id && applied.grids[0].sourceSystem === systems[0].id && applied.grids[0].surface === 1, applied.grids);
    fs.writeFileSync(path.join(OUT, 'grid-applied.json'), JSON.stringify(applied));
    await shot('grid-applied-1440');
    await b.click('#igClose');
    await b.waitFor(`!$('infiniteGridWorkspace')?.open`, 10000);
    await b.click('#btnUndo');
    await idle();
    const undone = (await refs()).grids || [];
    record('復原套用後主格消失且配置仍在', undone.length === 0 && (await objects()).gridBindings.length === 1, { grids: undone.length });
    await b.click('#btnRedo');
    await idle();
    const redone = gridSemantic(await dump(), await objects(), await refs());
    record('重做套用後幾何與引用回到原值', JSON.stringify(redone) === JSON.stringify(applied));
    const saved = await saveDownload('grid-save');
    gridFile = saved.file;
    record('保存走下載備援且檔案非空', saved.size > 100 && saved.downloaded.downloaded === true && saved.downloaded.dirty === true, { size: saved.size, sha256: saved.sha256 });
    const projectBefore = await project();
    await newProject();
    record('新專案清空網格與面', (await objects()).gridSystems.length === 0 && (await dump()) === '');
    await openFile(gridFile);
    const reopened = gridSemantic(await dump(), await objects(), await refs());
    const reProject = await project();
    gridSaved = { applied, reopened, projectBefore, reProject, file: { size: saved.size, sha256: saved.sha256 } };
    fs.writeFileSync(path.join(OUT, 'grid-reopen.json'), JSON.stringify(gridSaved));
    record('重開後 dump、來源、配置與主格引用相同', JSON.stringify(reopened) === JSON.stringify(applied));
    record('重開保留專案 id', reProject.id === projectBefore.id, { before: projectBefore.id, after: reProject.id });
    await shot('grid-reopen-1440');
    await b.resize(390, 844, true);
    const narrow = await read(`(()=>{const e=document.querySelector('#projectBar [data-project-action="save"]');const r=e.getBoundingClientRect();const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {w:r.width,h:r.height,hit:!!hit&&(hit===e||e.contains(hit)),overflow:document.documentElement.scrollWidth<=391};})()`);
    record('390 保存控制可點且不橫向溢出', narrow.h >= 44 && narrow.hit && narrow.overflow, narrow);
    const still = gridSemantic(await dump(), await objects(), await refs());
    record('390 重開後引用不因縮放改變', JSON.stringify(still) === JSON.stringify(applied));
    await shot('grid-reopen-390');
    await b.resize(1440, 1000, false);
  } catch (error) {
    record('網格路徑中止', false, String(error.stack || error));
    await shot('grid-failed').catch(() => {});
    await recover().catch(error => console.log('RECOVER ' + error));
  }

  let modelFile = null;
  try {
    await recover();
    if (!gridFile) throw Error('grid file missing');
    await newProject();
    await openFile(gridFile);
    const sceneBefore = await dump();
    await b.click('#btnSpaceModels');
    await b.waitFor(`$('smWorkspace')?.open && !!$('smTryRectangle')`, 15000);
    await b.click('#smTryRectangle');
    await b.waitFor(`!$('smPreview').disabled`, 40000);
    await b.click('#smPreview');
    await b.waitFor(`SpaceModelWorkspace.snapshot().phase==='preview' && !$('smPreview').disabled`, 30000);
    const preview = await read(`SpaceModelWorkspace.snapshot().resultSummary`);
    record('矩形範例預覽不改目前網格世界', (await dump()) === sceneBefore && preview && preview.volume_mm3 === '36000000000', preview);
    await b.click('#smConfirmFaces');
    await b.click('#smCreate');
    await b.waitFor(`!!SpaceModelWorkspace.snapshot().createdId`, 30000);
    const created = await read(`(async()=>{const id=SpaceModelWorkspace.snapshot().createdId,m=ReferenceWorkspace.getSpaceModels().find(x=>x.id===id);return {id,name:m.name,source:m.result&&m.result.source_sha256,count:ReferenceWorkspace.getSpaceModels().length,scene:(await apiRequest('dump')).text};})()`);
    record('建立模型後原生場景仍是網格專案', created.count === 1 && created.scene === sceneBefore, { id: created.id, source: created.source });
    await shot('model-created-1440');
    await b.click('#smLibrary');
    await b.waitFor(`!$('smLibraryPanel').hidden && !!document.querySelector(${JSON.stringify('[data-sm-remove-model="' + created.id + '"]')})`, 10000);
    await b.click(`[data-sm-remove-model="${created.id}"]`);
    await idle();
    record('刪除模型不改原生場景', (await read('ReferenceWorkspace.getSpaceModels().length')) === 0 && (await dump()) === sceneBefore);
    await b.click('#btnUndo');
    await idle();
    const restored = await read(`ReferenceWorkspace.getSpaceModels().find(m=>m.id===${JSON.stringify(created.id)})`);
    record('復原刪除恢復同一模型與來源摘要', !!restored && restored.result && restored.result.source_sha256 === created.source);
    await b.click('#btnRedo');
    await idle();
    record('重做刪除再次移除模型', (await read('ReferenceWorkspace.getSpaceModels().length')) === 0);
    await b.click('#btnUndo');
    await idle();
    await b.click('#smClose');
    await b.waitFor(`!$('smWorkspace').open`, 10000);
    const modelSaved = await saveDownload('model-save');
    modelFile = modelSaved.file;
    const beforeSwitch = { scene: await dump(), project: await project(), models: await read('ReferenceWorkspace.getSpaceModels().map(m=>({id:m.id,source:m.result&&m.result.source_sha256}))') };
    await newProject();
    record('切換新專案清空模型', (await read('ReferenceWorkspace.getSpaceModels().length')) === 0 && (await dump()) === '');
    await b.click('#btnUndo');
    await idle();
    const undoneSwitch = { scene: await dump(), project: await project(), models: await read('ReferenceWorkspace.getSpaceModels().map(m=>({id:m.id,source:m.result&&m.result.source_sha256}))') };
    record('復原新專案回到含模型的原專案', JSON.stringify(undoneSwitch) === JSON.stringify(beforeSwitch));
    await newProject();
    await openFile(modelFile);
    const reopenedModels = await read('ReferenceWorkspace.getSpaceModels().map(m=>({id:m.id,source:m.result&&m.result.source_sha256}))');
    record('模型專案重開保留場景、模型 id 與來源摘要', (await dump()) === sceneBefore && JSON.stringify(reopenedModels) === JSON.stringify(beforeSwitch.models), reopenedModels);
    await shot('model-reopen-1440');
    fs.writeFileSync(path.join(OUT, 'model-reopen.json'), JSON.stringify({ created, beforeSwitch, reopenedModels, file: { size: modelSaved.size, sha256: modelSaved.sha256 } }));
  } catch (error) {
    record('模型庫路徑中止', false, String(error.stack || error));
    await shot('model-failed').catch(() => {});
  }

  try {
    await recover();
    await newProject();
    await openFile(example);
    await idle();
    const opened = await assembly();
    record('正式開啟既有組構範例', opened.rules.length > 0 && opened.bindings.length > 0, { rules: opened.rules.length, bindings: opened.bindings.length, instances: opened.instances.length });
    await b.click('#btnCreateObject');
    await b.waitFor(`!$('createObjectPop').hidden`, 8000);
    await b.click('#btnNewAssembly');
    await b.waitFor(`$('assemblyWorkspace')?.open && !!document.querySelector('[data-asm-binding="1"]')`, 15000);
    await b.click('[data-asm-binding="1"]');
    await b.waitFor(`!!$('asmEdit')`, 10000);
    await b.click('#asmEdit');
    await b.waitFor(`!!$('asmValue1A') && !$('asmValue1A').disabled`, 10000);
    const beforeEdit = await assembly();
    await b.fill('#asmValue1A', '40'); await b.press('Tab');
    await b.fill('#asmValue1B', '50'); await b.press('Tab');
    await b.fill('#asmValue2A', '40'); await b.press('Tab');
    await b.fill('#asmValue2B', '50'); await b.press('Tab');
    const beforePreview = JSON.stringify(await assembly());
    await b.click('#asmPreview');
    await b.waitFor(`$('asmConfirm') && !$('asmConfirm').disabled`, 20000);
    record('組構預覽尚未改已發布狀態', JSON.stringify(await assembly()) === beforePreview);
    await b.click('#asmConfirm');
    await b.waitFor(`($('asmStatus')?.textContent||'').includes('已套用')`, 20000);
    await idle();
    const changed = await assembly();
    const sizes = changed.instances[0] && changed.instances[0].members.map(m => m.geometry && m.geometry.A + 'x' + m.geometry.B);
    record('確認後角材截面改為送出的 40×50', changed.instances.length === beforeEdit.instances.length && sizes && sizes.every(s => s === '40x50'), sizes);
    const changedDump = await dump();
    await shot('assembly-confirmed-1440');
    await b.click('#asmClose');
    await b.waitFor(`!$('assemblyWorkspace').open`, 10000);
    await b.click('#btnUndo');
    await idle();
    record('復原組構確認回到改前實例', JSON.stringify(await assembly()) === JSON.stringify(beforeEdit));
    await b.click('#btnRedo');
    await idle();
    record('重做組構確認恢復 40×50 與場景', JSON.stringify(await assembly()) === JSON.stringify(changed) && (await dump()) === changedDump);
    const asmSaved = await saveDownload('assembly-save');
    const beforeReopen = { assembly: await assembly(), dump: await dump(), project: await project() };
    await newProject();
    await openFile(asmSaved.file);
    const afterReopen = { assembly: await assembly(), dump: await dump(), project: await project() };
    record('組構重開保留規則、實例、dump 與專案 id', JSON.stringify(afterReopen.assembly) === JSON.stringify(beforeReopen.assembly) && afterReopen.dump === beforeReopen.dump && afterReopen.project.id === beforeReopen.project.id);
    await shot('assembly-reopen-1440');
    fs.writeFileSync(path.join(OUT, 'assembly-reopen.json'), JSON.stringify({ sizes, file: { size: asmSaved.size, sha256: asmSaved.sha256 }, project: afterReopen.project }));

    const guardBefore = { dump: await dump(), project: await project(), assembly: await assembly() };
    await read(`Object.defineProperty(window,'showSaveFilePicker',{configurable:true,value:async()=>{throw new DOMException('cancel','AbortError')}});void 0`);
    await b.click('#projectBar [data-project-action="save"]');
    await idle();
    const afterCancel = { dump: await dump(), project: await project(), assembly: await assembly() };
    record('注入的保存取消不改目前專案', JSON.stringify(afterCancel) === JSON.stringify(guardBefore));
    await read(`Object.defineProperty(window,'showSaveFilePicker',{configurable:true,value:async()=>({createWritable:async()=>({write:async()=>{throw Error('injected disk full')},abort:async()=>{window.__phase3Aborted=true}})})});window.__phase3Aborted=false;void 0`);
    let writeError = '';
    try { await b.click('#projectBar [data-project-action="save"]'); await idle(); } catch (error) { writeError = String(error); }
    await b.sleep(500);
    const afterWrite = { dump: await dump(), project: await project(), assembly: await assembly(), aborted: await read('window.__phase3Aborted===true'), busy: await read('!!ReferenceWorkspace.busy') };
    record('注入的寫入失敗不改目前專案', JSON.stringify({ dump: afterWrite.dump, project: afterWrite.project, assembly: afterWrite.assembly }) === JSON.stringify(guardBefore) && afterWrite.aborted === true && afterWrite.busy === false, { writeError, aborted: afterWrite.aborted });
    await read(`delete window.showSaveFilePicker;void 0`);
    const corrupt = path.join(OUT, 'corrupt.gcanvas');
    fs.writeFileSync(corrupt, 'not a zip file');
    await openFile(corrupt);
    await b.sleep(400);
    const afterBad = { dump: await dump(), project: await project(), assembly: await assembly(), status: await b.readText('#status') };
    record('壞檔匯入不改目前專案', JSON.stringify({ dump: afterBad.dump, project: afterBad.project, assembly: afterBad.assembly }) === JSON.stringify(guardBefore), { status: afterBad.status });
    await shot('bad-import-1440');
    fs.writeFileSync(path.join(OUT, 'guards.json'), JSON.stringify({ afterCancel, afterWrite: { aborted: afterWrite.aborted, busy: afterWrite.busy }, afterBad }, null, 2));
  } catch (error) {
    record('組構或保護路徑中止', false, String(error.stack || error));
    await shot('assembly-failed').catch(() => {});
  }

  const passed = results.filter(r => r.ok).length;
  const failed = results.filter(r => !r.ok).length;
  const summary = { schema: 'geometry-phase3-formal/1', passed, failed, unverified: ['native-os-save-picker', 'physical-mouse', 'ime', 'real-device', 'hosted-ci'], citedNotRerun: { A: 16, B: 35, C: 33 }, results };
  fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify(summary, null, 2));
  console.log('PHASE3_SUMMARY ' + JSON.stringify({ passed, failed }));
  if (b) await b.close();
  process.exitCode = failed ? 1 : 0;
})().catch(async error => {
  console.error('PHASE3_FATAL ' + (error.stack || error));
  if (b) await b.close().catch(() => {});
  process.exitCode = 1;
});
