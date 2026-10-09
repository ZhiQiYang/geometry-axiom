/* One synthetic save/reopen: placed 600×400 face, unplaced 300×300 boundary,
 * infinite grid, all-cells 2×2 rule. Top and bottom boundary timbers support
 * two in-cell primaries; the secondary spans those primaries on the cell's
 * rule line. Host outlines and support guides are bridge commands. Grid, rule,
 * binding, timber, save and reopen use the real controls.
 */
'use strict';
const fs = require('fs');
const crypto = require('crypto');
const zip = require('./vendor/fflate/umd/index.js');

module.exports = { saveReopenGridRegression };

function saveReopenGridRegression(h) {
  const must = (name, cond, detail) => {
    if (!h.check(name, cond === true, detail)) throw Error(name + ' ' + JSON.stringify(detail));
  };
  const read = expr => h.evaluate(expr);
  const objects = () => read(`apiRequest('objects').then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})`);
  const refs = () => read(`apiRequest('references').then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})`);
  const projectId = () => read(`ReferenceWorkspace.getProjectState().id`);
  const reveal = async selector => {
    const info = await read(`(()=>{const n=document.querySelector(${JSON.stringify(selector)});if(!n)return {place:'missing'};const r=n.getBoundingClientRect();let place='page';if(n.closest('.sidebar-left,#objectList'))place='left';else if(n.closest('.sidebar-right,#inspectorContent'))place='right';else if(n.closest('.face-inspector-panel,#faceInspectorContent'))place='face';return {place,width:r.width,height:r.height};})()`);
    if (info.place === 'missing') throw Error('Missing ' + selector);
    if (info.place === 'page' || (info.width > 0 && info.height > 0)) return;
    if (info.place === 'left' && await read(`innerWidth<=900 && !document.body.classList.contains('drawer-left-open')`)) await h.click('#toggleLeft');
    if (info.place === 'face' && await read(`innerWidth<=900 && !document.body.classList.contains('drawer-right-open')`)) await h.click('#workspaceToggleRight');
    if (info.place === 'right') {
      const toggle = await read(`(()=>{const n=$('toggleRight');const r=n?.getBoundingClientRect();return !!(r&&r.width>0&&r.height>0)&&!document.body.classList.contains('drawer-right-open');})()`);
      if (toggle) await h.click('#toggleRight');
    }
    await h.wait(`(()=>{const n=document.querySelector(${JSON.stringify(selector)});const r=n?.getBoundingClientRect();return !!(r&&r.width>0&&r.height>0);})()`, 'visible ' + selector);
  };
  const click = async selector => { await reveal(selector); await h.click(selector); };
  const closeLibrary = async () => {
    if (await read(`innerWidth<=900 && document.body.classList.contains('drawer-left-open')`)) await h.click('#toggleLeft');
  };
  const plant = async lines => {
    const out = await read(`(async()=>{await setView3(false);resetSceneFocus();const lines=${JSON.stringify(lines)};const out=[await api('reset')];for(const line of lines){let r=await api('line '+line);if(r.preview){if(!r.preview.valid)return {line,r};r=await api('line confirm '+r.preview.token);}out.push(r);}await renderObjects();return out;})()`);
    if (!Array.isArray(out) || out.some(r => r?.ok !== true)) throw Error('Fixture rejected ' + JSON.stringify(out));
    await h.settle();
  };
  const sendLines = async lines => {
    const out = await read(`(async()=>{const lines=${JSON.stringify(lines)};const out=[];for(const line of lines){let r=await api('line '+line);if(r.preview){if(!r.preview.valid)return {line,r};r=await api('line confirm '+r.preview.token);}out.push({ok:r.ok===true,error:r.error||'',line});}if(typeof feLoadGuides==='function')await feLoadGuides();await renderObjects();return out;})()`);
    if (!Array.isArray(out) || out.some(r => r?.ok !== true)) throw Error('Fixture rejected ' + JSON.stringify(out));
    await h.settle();
  };
  const confirmImpact = async () => {
    await h.wait(`!!document.querySelector('.reference-impact[open]')`, 'impact preview');
    const blocked = await read(`({disabled:!!$('impact-confirm')?.disabled,text:document.querySelector('.reference-impact')?.innerText||''})`);
    if (blocked.disabled) throw Error('Impact confirm disabled: ' + blocked.text);
    await h.click('#impact-confirm');
    await h.wait(`!document.querySelector('.reference-impact[open]') && !ReferenceWorkspace.busy && !oc.busy`, 'impact settled');
  };
  const closeEditors = async () => {
    if (await read(`!!$('infiniteGridWorkspace')?.open`)) await h.click('#igClose');
    if (await read(`!!oc.edit`)) await h.click('#workspaceBackButton');
    await h.wait(`!$('infiniteGridWorkspace')?.open && !oc.edit`, 'editors closed');
  };
  const uLines = async bindingId => {
    const q = await read(`apiRequest(${JSON.stringify('grid-query binding ' + bindingId + ' rect 0 0 600 400 mode exact limit 64')}).then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r.axes.u.lines.map(l=>l.coordinate);})`);
    return q;
  };
  const identity = async () => {
    const [o, r, scene, id] = await Promise.all([objects(), refs(), h.scene(), projectId()]);
    const system = o.gridSystems[0];
    const binding = o.gridBindings[0];
    const grid = r.grids[0];
    const timbers = (r.timbers || []).map(t => ({
      id: t.id, role: t.role, A: t.geometry?.A, B: t.geometry?.B,
      anchor: t.definition?.anchor, selector: t.definition?.selector || ''
    })).sort((a, b) => a.id - b.id);
    return {
      projectId: id,
      scene: String(scene).replace(/\r\n/g, '\n'),
      system: system && {id: system.id, name: system.name, mode: system.mode, mainAlong: system.mainAlong ?? null, nextRuleKey: system.nextRuleKey, u: system.uDefinition, v: system.vDefinition, rules: system.rules},
      binding: binding && {id: binding.id, system: binding.system, boundary: binding.boundary, vertexKey: binding.vertexKey, cell: binding.cell, anchor: binding.anchor},
      grid: grid && {id: grid.id, surface: grid.surface, bindingId: grid.bindingId, sourceSystem: grid.sourceSystem, indexSpace: grid.indexSpace},
      timbers
    };
  };
  const saveProject = async () => {
    fs.rmSync(h.downloadDir, {recursive: true, force: true});
    fs.mkdirSync(h.downloadDir, {recursive: true});
    await read(`window.__savePicker=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});0`);
    let file = null;
    try {
      await click('[data-project-action="save"]');
      for (let i = 0; i < 150; i++) {
        const names = fs.readdirSync(h.downloadDir).filter(name => name.endsWith('.gcanvas'));
        if (names.length === 1) { file = require('path').join(h.downloadDir, names[0]); break; }
        if (names.length > 1) throw Error('Ambiguous project download');
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    } finally {
      await read(`if(window.__savePicker)Object.defineProperty(window,'showSaveFilePicker',window.__savePicker);else delete window.showSaveFilePicker;delete window.__savePicker;0`);
    }
    if (!file) throw Error('Product save did not write a .gcanvas');
    return file;
  };
  const reopen = async file => {
    await h.click('#btnNewProject');
    await h.wait(`!ReferenceWorkspace.busy && oc.gridSystems.length===0 && oc.faces.length===0`, 'new empty project');
    await h.send('Page.setInterceptFileChooserDialog', {enabled: true});
    try {
      await read(`window.__projectChooser=false;$('projectFile').addEventListener('click',()=>{window.__projectChooser=true;},{once:true});0`);
      await h.click('#btnOpenProject');
      await h.wait(`window.__projectChooser===true`, 'project file chooser');
      const doc = await h.send('DOM.getDocument', {depth: 0});
      const node = await h.send('DOM.querySelector', {nodeId: doc.root.nodeId, selector: '#projectFile'});
      await h.send('DOM.setFileInputFiles', {nodeId: node.nodeId, files: [file]});
      await h.wait(`!ReferenceWorkspace.busy && oc.gridSystems.length===1 && oc.gridBindings.length===1`, 'project reopened');
    } finally {
      await h.send('Page.setInterceptFileChooserDialog', {enabled: false});
    }
  };
  const placeTimber = async ({anchor, a, b, dir, role, selector}) => {
    await click('#faceInspectorTabs [data-fi-tab="components"]');
    try {
      await h.wait(`!!$('tbAnchor') && !$('tbAnchor').disabled && $('tbAnchor').getBoundingClientRect().height>0`, 'timber form');
    } catch (error) {
      const info = await read(`({tabs:[...document.querySelectorAll('#faceInspectorTabs [data-fi-tab]')].map(n=>n.dataset.fiTab), pane:$('faceInspectorContent')?.innerText?.slice(0,400)||'', edit:oc.edit&&oc.edit.bid})`);
      throw Error(error.message + ' ' + JSON.stringify(info));
    }
    await h.select('#tbAnchor', anchor);
    await h.input('#tbA', String(a));
    await h.input('#tbB', String(b));
    await h.select('#tbDir', dir);
    await h.select('#tbRole', role);
    await h.input('#tbSelector', selector);
    const before = (await refs()).timbers?.length || 0;
    await click('#tbPlace');
    await h.wait(`(async()=>(await apiRequest('references')).timbers.length===${before + 1})()`, 'timber ' + anchor);
  };

  return async () => {
    for (const width of [1400, 390]) {
      const height = width === 1400 ? 900 : 844;
      await h.viewport(width, height);
      await plant([
        'boundary 11 outline 0,0 600,0 600,400 0,400',
        'placement 21 on boundary 11 origin 0 0 0 u +x v +y',
        'boundary 12 outline 0,0 300,0 300,300 0,300'
      ]);
      const host = await read(`(async()=>{const s=await apiRequest('surfaces');const d=await api('dump');return {surfaces:s.surfaces||s,dump:d.text};})()`);
      const placed = (host.surfaces || []).some(s => Number(s.boundary || s.boundaryId) === 11 || Number(s.id) === 21);
      must(width + ' 宿主面：11 放置在原點，12 沒有放置', placed && host.dump.includes('boundary 12 outline') && !host.dump.includes('on boundary 12'), host.surfaces);
      const sid = (host.surfaces || []).find(s => Number(s.boundary || s.boundaryId) === 11)?.id;
      if (!sid) throw Error('Placed surface missing ' + JSON.stringify(host.surfaces));
      await sendLines([
        'spec supportLeft 60',
        'spec supportRight 140',
        `guide 31 ${sid} v spec:supportLeft`,
        `guide 32 ${sid} v spec:supportRight`
      ]);

      await click(width <= 900 ? '#btnQuickGrid' : '#btnNewGridSystem');
      await h.wait(`!!$('infiniteGridWorkspace')?.open && !$('igName').disabled`, 'new grid source');
      await h.input('#igName', '假格網');
      await h.input('#igUPhase', '0');
      await h.input('#igUStep', '200');
      await h.input('#igVPhase', '0');
      await h.input('#igVStep', '100');
      await h.click('#igSaveSource');
      await confirmImpact();
      await h.click('#igRuleAdd');
      await h.wait(`!$('igRuleName').disabled`, 'rule editor');
      await h.input('#igRuleName', '假規則');
      await h.input('#igRuleU', '2');
      await h.input('#igRuleV', '2');
      await h.click('#igRulePreview');
      await confirmImpact();
      const created = await objects();
      const system = created.gridSystems[0];
      must(width + ' 系統身分：假格網 u repeat 0 200、v repeat 0 100、無 stagger',
        created.gridSystems.length === 1 && system.name === '假格網' && system.mode === 'infinite' && (system.mainAlong == null || system.mainAlong === 'none') &&
        system.uDefinition?.source === 'repeat' && system.uDefinition.phase === 0 && system.uDefinition.step === 200 && !Object.hasOwn(system.uDefinition, 'stagger') &&
        system.vDefinition?.source === 'repeat' && system.vDefinition.phase === 0 && system.vDefinition.step === 100 && !Object.hasOwn(system.vDefinition, 'stagger'),
        system);
      const rule = system.rules?.[0];
      must(width + ' 規則屬於系統：key 1、next 2、all-cells、2×2、名稱假規則',
        system.rules?.length === 1 && rule.ruleKey === 1 && system.nextRuleKey === 2 && rule.name === '假規則' && rule.selector?.kind === 'all-cells' && rule.divisions?.join('/') === '2/2',
        {rules: system.rules, next: system.nextRuleKey});

      await h.click('#igNewBinding');
      await h.wait(`!!$('igBoundary') && !$('igBoundary').disabled`, 'binding editor');
      await h.select('#igBoundary', '11');
      await h.wait(`[...$('igVertex').options].some(o=>/\\(0, 0\\)/.test(o.textContent))`, 'vertex (0, 0)');
      const vertex = await read(`([...$('igVertex').options].find(o=>/\\(0, 0\\)/.test(o.textContent))||{}).value||''`);
      await h.click(`[data-ig-vertex="${vertex}"]`);
      await h.wait(`$('igVertex').value===${JSON.stringify(vertex)}`, 'vertex selected');
      await h.input('#igCellI', '0');
      await h.input('#igCellJ', '0');
      await h.input('#igAnchorUN', '0');
      await h.input('#igAnchorUD', '1');
      await h.input('#igAnchorVN', '0');
      await h.input('#igAnchorVD', '1');
      await h.click('#igSaveBinding');
      await confirmImpact();
      await h.select('#igSurface', '21');
      await h.click('#igApplyBinding');
      await confirmImpact();
      const bound = await identity();
      must(width + ' 配置身分：邊界 11、頂點 (0,0)、cell 0,0、比例 0/1,0/1、vertexKey 為正整數',
        bound.binding?.boundary === 11 && bound.binding.system === system.id && bound.binding.vertexKey > 0 &&
        JSON.stringify(bound.binding.cell) === '["0","0"]' && JSON.stringify(bound.binding.anchor) === '[{"num":0,"den":1},{"num":0,"den":1}]',
        bound.binding);
      must(width + ' 套用主格引用同一邊界的配置與系統，未放置邊界 12 沒有主格',
        bound.grid?.surface === 21 && bound.grid.bindingId === bound.binding.id && bound.grid.sourceSystem === system.id && bound.grid.indexSpace === 'lattice' &&
        (await refs()).grids.length === 1 && !bound.scene.includes('on boundary 12'),
        bound.grid);
      const beforeLines = await uLines(bound.binding.id);
      await closeEditors();
      await reveal('#objectList .object-row[data-kind="boundary"][data-id="11"]');
      await h.click('#objectList .object-row[data-kind="boundary"][data-id="11"]');
      await closeLibrary();
      await reveal('#inspEnter');
      await h.click('#inspEnter');
      await h.wait(`oc.edit?.bid===11 && GridRuleLines.entries().some(l=>l.segments.length)`, 'face rule lines');
      const line = (await read(`GridRuleLines.entries().find(l=>l.ref.ruleKey===1&&l.ref.cellI==='0'&&l.ref.cellJ==='0'&&l.ref.axis==='v'&&l.ref.innerIndex===0)`));
      const anchor = line && ('at-line rule ' + [line.ref.appliedGridId, line.ref.systemId, line.ref.ruleKey, line.ref.cellI, line.ref.cellJ, line.ref.axis, line.ref.innerIndex].join(' '));
      if (!anchor || anchor !== `at-line rule ${bound.grid.id} ${system.id} 1 0 0 v 0`) throw Error('Rule anchor ' + JSON.stringify(line));
      await placeTimber({anchor: 'at-face e0', a: 20, b: 20, dir: '+u', role: 'boundary', selector: ''});
      await placeTimber({anchor: 'at-face e2', a: 20, b: 20, dir: '+u', role: 'boundary', selector: ''});
      await placeTimber({anchor: 'at-line guide 31', a: 20, b: 20, dir: '+v', role: 'primary', selector: ''});
      await placeTimber({anchor: 'at-line guide 32', a: 20, b: 20, dir: '+v', role: 'primary', selector: ''});
      const placedTimbers = (await refs()).timbers;
      const bottom = placedTimbers.find(t => t.definition?.anchor === 'at-face e0' && t.role === 'boundary');
      const top = placedTimbers.find(t => t.definition?.anchor === 'at-face e2' && t.role === 'boundary');
      const left = placedTimbers.find(t => t.definition?.anchor === 'at-line guide 31' && t.role === 'primary');
      const right = placedTimbers.find(t => t.definition?.anchor === 'at-line guide 32' && t.role === 'primary');
      const supportIds = [bottom, top, left, right].map(t => t && t.id);
      must(width + ' 上下邊界材 20×20 指向 e0 與 e2，格內主支指向參考線 31 與 32',
        supportIds.every(id => id != null) && new Set(supportIds).size === 4 &&
        [bottom, top, left, right].every(t => t.geometry?.A === 20 && t.geometry?.B === 20),
        placedTimbers.map(t => ({id: t.id, role: t.role, anchor: t.definition?.anchor, A: t.geometry?.A, B: t.geometry?.B})));
      await placeTimber({anchor, a: 20, b: 30, dir: '+u', role: 'secondary', selector: `between t${left.id} t${right.id}`});
      const secondary = (await refs()).timbers.find(t => t.definition?.anchor === anchor);
      must(width + ' 副支 20×30 的 at-line rule 引用完整 tuple，between 指向那兩支主支',
        secondary?.role === 'secondary' && secondary.geometry?.A === 20 && secondary.geometry?.B === 30 &&
        secondary.definition?.selector === `between t${left.id} t${right.id}` && !/mm|中線/.test(anchor),
        secondary && {id: secondary.id, anchor: secondary.definition.anchor, selector: secondary.definition.selector});

      await h.click('#workspaceBackButton');
      await h.wait(`!oc.edit`, 'leave face');
      await reveal('#objectList .object-row[data-kind="grid-system"]');
      await h.click('#objectList .object-row[data-kind="grid-system"]');
      await closeLibrary();
      await reveal('#gridObjectOpen');
      await h.click('#gridObjectOpen');
      await h.wait(`$('infiniteGridWorkspace').open && !$('igUStep').disabled`, 'reopen source');
      await h.input('#igUStep', '300');
      await h.click('#igSaveSource');
      await confirmImpact();
      await closeEditors();
      const after = await identity();
      const afterLines = await uLines(after.binding.id);
      must(width + ' u 間距改 300 後 cell、vertexKey、ruleKey、角材引用不變，推導 u 線改變',
        after.binding.vertexKey === bound.binding.vertexKey && JSON.stringify(after.binding.cell) === '["0","0"]' &&
        after.system.rules[0].ruleKey === 1 && after.system.nextRuleKey === 2 && after.system.u.step === 300 &&
        after.timbers.some(t => t.role === 'primary' && t.anchor === 'at-line guide 31') &&
        after.timbers.some(t => t.role === 'primary' && t.anchor === 'at-line guide 32') &&
        after.timbers.some(t => t.role === 'secondary' && t.anchor === anchor && t.selector === `between t${left.id} t${right.id}`) &&
        beforeLines.includes(200) && afterLines.includes(300) && JSON.stringify(beforeLines) !== JSON.stringify(afterLines),
        {beforeLines, afterLines, vertexKey: after.binding.vertexKey, step: after.system.u.step});

      const savedId = after.projectId;
      const file = await saveProject();
      const packed = zip.unzipSync(fs.readFileSync(file));
      const packedScene = Buffer.from(packed['world.scene']).toString('utf8').replace(/\r\n/g, '\n');
      const packedText = Object.values(packed).map(bytes => Buffer.from(bytes).toString('utf8')).join('\n');
      const sceneHash = crypto.createHash('sha256').update(packedScene).digest('hex');
      must(width + ' .gcanvas 的 world.scene 與當時 dump 全等，含規則能力與 next-key，不含 translation',
        packedScene === after.scene && packedText.includes('grid-subdivision-rules/1') && packedScene.includes('next-key ') &&
        packedScene.includes('from-binding ' + after.binding.id) && !packedScene.includes('translation '),
        {file: require('path').basename(file), sceneHash, bytes: fs.statSync(file).size});
      await reopen(file);
      const opened = await identity();
      must(width + ' 重開保留 projectId、scene hash、vertexKey、ruleKey 與 owned 角材引用',
        opened.projectId === savedId && crypto.createHash('sha256').update(opened.scene).digest('hex') === sceneHash &&
        opened.binding.vertexKey === after.binding.vertexKey && opened.binding.id === after.binding.id &&
        opened.system.id === after.system.id && opened.system.rules[0].ruleKey === 1 && opened.system.nextRuleKey === 2 &&
        JSON.stringify(opened.timbers) === JSON.stringify(after.timbers) && opened.grid.bindingId === after.grid.bindingId,
        {projectId: opened.projectId, sceneHash, vertexKey: opened.binding.vertexKey, ruleKey: opened.system.rules[0].ruleKey});
    }
  };
}
