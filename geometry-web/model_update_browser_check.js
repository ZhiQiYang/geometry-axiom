/* #44 F1b acceptance against the actual app and isolated native HTTP producer.
 * Browser plugin is unavailable; use the installed Playwright/Chromium.
 * Run with explicit GEOMETRY_TEST_URL and GEOMETRY_FEEDBACK_DIR under /tmp.
 * Optional: GEOMETRY_MODEL_UPDATE_PATH, GEOMETRY_MODEL_UPDATE_TEST_DIR.
 * GEOMETRY_MODEL_UPDATE_ENTRY=owner requires actual shared-owner edit wiring;
 * the default direct-module scope injects missing modules and opens directly.
 * This harness delays real HTTP replies; it never fabricates native success.
 */
'use strict';
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const url = process.env.GEOMETRY_TEST_URL;
if (!url || !process.env.GEOMETRY_FEEDBACK_DIR?.startsWith('/tmp/'))
  throw Error('An explicit isolated GEOMETRY_TEST_URL and /tmp feedback directory are required.');
const output = process.env.GEOMETRY_MODEL_UPDATE_TEST_DIR || '/tmp/geometry-f1b/browser';
const routePath = process.env.GEOMETRY_MODEL_UPDATE_PATH || '/model/update-preview';
const ownerEntry = process.env.GEOMETRY_MODEL_UPDATE_ENTRY === 'owner';
fs.mkdirSync(output, {recursive: true});
const deferred = () => {let resolve, reject; const promise = new Promise((r, j) => {resolve = r; reject = j;}); return {promise, resolve, reject};};
const selectors = {dialog: '#muDialog', placement: '#muPlacement', edge: '[data-mu-edge]',
  timber: '[data-mu-timber]', preview: '#muPreview', confirm: '#muApply',
  cancel: '#muClose', close: '#muClose', status: '#muStatus', review: '#muReview'};

(async () => {
  const browser = await chromium.launch({executablePath: process.env.GEOMETRY_CHROME || '/usr/bin/chromium',
    headless: true, args: ['--no-sandbox']});
  const context = await browser.newContext({viewport: {width: 1280, height: 900}});
  const page = await context.newPage();
  page.setDefaultTimeout(90000);
  const errors = [], warnings = [], checks = [], heldResponses = [];
  let fixtureId, producerRequests = 0;
  page.on('request', request => {if (new URL(request.url()).pathname === routePath) producerRequests++;});
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text());
    if (message.type() === 'warning') warnings.push(message.text());
  });
  page.on('dialog', dialog => dialog.accept());
  const check = (name, condition, evidence) => {
    assert.equal(condition, true, name + (evidence ? ': ' + JSON.stringify(evidence) : ''));
    checks.push({name, passed: true, ...(evidence ? {evidence} : {})});
    console.log('PASS ' + name);
  };
  const state = () => page.evaluate(async () => {
    window.__f1bFrames ||= new WeakMap(); window.__f1bFrameCounter ||= 0;
    const frame = ReferenceWorkspace.history.frame;
    if (!__f1bFrames.has(frame)) __f1bFrames.set(frame, ++__f1bFrameCounter);
    const dump = await apiRequest('dump');
    if (!dump.ok) throw Error(JSON.stringify(dump));
    return {scene: dump.text, nativeRevision: dump.revision,
      project: ReferenceWorkspace.getProjectState(), frame: __f1bFrames.get(frame),
      undo: ReferenceWorkspace.history.undo.length, redo: ReferenceWorkspace.history.redo.length,
      models: ReferenceWorkspace.getSpaceModels()};
  });
  const close = async () => {
    await page.evaluate(() => window.ModelUpdateApp?.close?.());
    if (await page.locator(selectors.dialog).isVisible()) {
      if (await page.locator(selectors.close).count()) await page.locator(selectors.close).click();
      else await page.keyboard.press('Escape');
    }
  };
  const waitPhase = phase => page.waitForFunction(phase =>
    window.ModelUpdateApp?.snapshot?.().phase === phase, phase);
  const open = async () => {
    if (ownerEntry) {
      await page.evaluate(() => SpaceModelWorkspace.openLibrary());
      await page.locator(`[data-sm-edit-height="${fixtureId}"]`).click();
      await page.locator('#smCurrentSourceUpdate').click();
    } else await page.evaluate(id => ModelUpdateApp.open(id), fixtureId);
    await page.locator(selectors.dialog).waitFor({state: 'visible'});
    await waitPhase('selecting');
  };
  const choose = async () => {
    await page.locator(selectors.placement).selectOption('0');
    await page.waitForFunction(selector => document.querySelectorAll(selector).length === 4, selectors.edge);
    for (const edge of await page.locator(selectors.edge).all()) await edge.check();
    const timber = page.locator('[data-mu-timber="0"]');
    await timber.check();
    const explicit = page.locator('[data-mu-empty-obstacles]');
    if (await explicit.count()) await explicit.check();
    const projection = page.locator('#muProjection');
    if (await projection.count()) {
      const values = await projection.locator('option').evaluateAll(options => options.map(option => option.value));
      if (values.includes('top')) await projection.selectOption('top');
    }
  };
  const restore = async () => {
    await close();
    await page.evaluate(async () => {
      await ReferenceWorkspace.importBytes(new Uint8Array(__f1bArchive), 'f1b-baseline.gcanvas');
      let result = await apiRequest('line timber 0 29 33 role boundary');
      if (result.preview?.valid) result = await apiRequest('line confirm ' + result.preview.token);
      if (!result.ok) throw Error(JSON.stringify(result));
    });
  };
  async function holdProducer() {
    const captured = deferred(), release = deferred(), finished = deferred();
    let delivered = 0;
    const handler = async route => {
      try {
        const response = await route.fetch({timeout: 90000});
        assert.equal(response.status(), 200, 'held reply must be actual successful producer HTTP');
        const receipt = await response.json();
        assert.equal(receipt.ok, true, 'held reply must be an actual native positive candidate');
        assert.equal(receipt.identity, 'unknown');
        captured.resolve(receipt); await release.promise;
        try {await route.fulfill({response}); delivered++;} catch (_) { /* Abort cancelled this readonly request. */ }
      } catch (error) {captured.reject(error);}
      finally {finished.resolve();}
    };
    await page.route('**' + routePath, handler);
    const held = {captured, release, finished,
      async cleanup() {release.resolve(); await finished.promise; await page.unroute('**' + routePath, handler);},
      get delivered() {return delivered;}};
    heldResponses.push(held); return held;
  }
  const preview = async () => {
    await page.locator(selectors.preview).click(); await waitPhase('review');
  };
  async function delayed(name, mutate, cancel = false, stage = 'preview') {
    await restore(); await open(); await choose();
    if (stage === 'confirm') {await preview(); await page.locator('#muConfirmed').check();}
    const held = await holdProducer();
    await page.locator(stage === 'confirm' ? selectors.confirm : selectors.preview).click(); await held.captured.promise;
    await mutate(); const before = await state();
    await held.cleanup();
    if (!cancel) await waitPhase('failed');
    else await page.waitForTimeout(150);
    assert.deepEqual(await state(), before, name);
    check(name + ' rejects a held real candidate with zero update', true,
      {models: before.models.length, undo: before.undo, delivered: held.delivered});
  }
  try {
    const runtimeResponse = await page.request.get(new URL('/runtime', url).href);
    const runtime = await runtimeResponse.json();
    assert.equal(runtime.fresh, true, 'isolated test runtime must be fresh before browser acceptance');
    await page.goto(url); await page.waitForFunction(() => typeof connection !== 'undefined' && connection.phase === 'ready' && window.GeometryProject);
    const title = await page.title(), body = await page.locator('body').innerText();
    check('page identity and meaningful app content', /幾何|Geometry|geometry|工程|物件|應用/.test(title) && body.length > 100);
    check('no framework error overlay', await page.locator('vite-error-overlay,nextjs-portal,[data-nextjs-dialog]').count() === 0);
    await page.screenshot({path: path.join(output, 'app-desktop.png')});
    if (ownerEntry) assert.equal(await page.evaluate(() => !!window.ModelUpdate && !!window.ModelUpdateApp), true,
      'owner-entry scope requires actual index wiring; modules cannot be injected');
    if (!ownerEntry && !await page.evaluate(() => !!window.ModelUpdate)) await page.addScriptTag({path: path.join(__dirname, 'model-update.js')});
    const css = ['model-update-app.css', 'model-update.css'].map(file => path.join(__dirname, file)).find(file => fs.existsSync(file));
    if (!ownerEntry && css) await page.addStyleTag({path: css});
    if (!ownerEntry && !await page.evaluate(() => !!window.ModelUpdateApp)) await page.addScriptTag({path: path.join(__dirname, 'model-update-app.js')});
    await page.waitForFunction(() => !!window.ModelUpdateApp);
    fixtureId = await page.evaluate(async () => {
      await ReferenceWorkspace.newProject();
      for (const line of ['boundary 1 outline 0,0 4000,0 4000,3000 0,3000 kind room_plan',
        'placement 0 on boundary 1 origin 0 0 2500 u +x v +y', 'timber 0 27 33 role boundary',
        'place 0 on 0 at-face e0 +u +n']) {
        let result = await apiRequest('line ' + line);
        if (result.preview?.valid) result = await apiRequest('line confirm ' + result.preview.token);
        if (!result.ok) throw Error(JSON.stringify(result));
      }
      await refreshSurfaces(); await renderObjects();
      ReferenceWorkspace.setFaceProjection(1, 0,
        {kind: 'space-boundary-plan', view: 'top', region: 'interior', wallSide: 'outside'});
      const dump = await apiRequest('dump'); if (!dump.ok) throw Error(JSON.stringify(dump));
      const input = {mode: 'plan', base_scene: dump.text, placement_id: 0, obstacles: [],
        timbers: [{kind: 'timber', id: 0}], settings: {bottom: 0, height: 3000, edges: [0, 1, 2, 3],
          floor: 'boundary', ceiling: 'boundary', holes: 'none', wall_thickness: null}};
      const response = await fetch('/model/space-preview', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(input)});
      const result = await response.json(); if (!response.ok || !result.ok) throw Error(JSON.stringify(result));
      const record = {id: crypto.randomUUID(), name: 'F1b 普通單一平面', created_at: new Date().toISOString(),
        source: {kind: 'scene', placement_id: 0, boundary_id: 1, scene_hash: result.source_sha256,
          projection: {kind: 'space-boundary-plan', view: 'top', region: 'interior', wallSide: 'outside'}}, input, result};
      ReferenceWorkspace.addSpaceModel(record); window.__f1bOld = record;
      window.__f1bArchive = Array.from(await ReferenceWorkspace.exportBytes());
      let changed = await apiRequest('line timber 0 29 33 role boundary');
      if (changed.preview?.valid) changed = await apiRequest('line confirm ' + changed.preview.token);
      if (!changed.ok) throw Error(JSON.stringify(changed)); return record.id;
    });
    const original = await state();
    await open();
    check('opening leaves identity unknown and source choices blank',
      await page.locator(selectors.placement).inputValue() === '' &&
      await page.locator(selectors.edge + ':checked,' + selectors.timber + ':checked').count() === 0 &&
      /未知|unknown/.test(await page.locator(selectors.dialog).innerText()));
    check('unknown source requires explicit selection before any producer request', producerRequests === 0 &&
      await page.locator(selectors.preview).isDisabled() && await page.locator(selectors.confirm).isDisabled());
    assert.deepEqual(await state(), original); check('opening does not mutate models World dirty or history', true);
    await choose(); await preview();
    for (const detail of await page.locator('#muFullDetails > details').all()) await detail.locator('summary').click();
    const reviewText = await page.locator(selectors.review).innerText();
    check('real preview shows old27 new29 while saved model stays27', reviewText.includes('4000 × 27 × 33 mm') && reviewText.includes('4000 × 29 × 33 mm') &&
      await page.evaluate(() => ReferenceWorkspace.getSpaceModels()[0].result.summary.timber_volume_mm3 === __f1bOld.result.summary.timber_volume_mm3));
    assert.deepEqual(await state(), original); check('isolated candidate changes no live record or native World', true);
    for (const detail of await page.locator('#muFullDetails > details').all()) await detail.locator('summary').click();
    const geometryHeading = page.locator('#muDiff h4').filter({hasText: '實際角材幾何'});
    await geometryHeading.evaluate(heading => heading.scrollIntoView({block: 'start'}));
    await page.screenshot({path: path.join(output, 'review-desktop.png')});
    await page.setViewportSize({width: 390, height: 844});
    await geometryHeading.evaluate(heading => heading.scrollIntoView({block: 'start'}));
    await page.screenshot({path: path.join(output, 'review-390.png')});
    check('390px dialog stays within the viewport without horizontal overflow', await page.evaluate(selector => {
      const dialog = document.querySelector(selector); return document.documentElement.scrollWidth <= innerWidth + 1 &&
        dialog.scrollWidth <= innerWidth + 1 && dialog.getBoundingClientRect().width <= innerWidth;
    }, selectors.dialog));
    const controls = await page.locator(selectors.dialog + ' button,' + selectors.dialog + ' select').evaluateAll(nodes =>
      nodes.filter(node => node.getClientRects().length).map(node => ({id: node.id, text: node.textContent, height: node.getBoundingClientRect().height})));
    check('390px visible buttons and selectors have at least44px height', controls.every(control => control.height >= 44), controls);
    await page.setViewportSize({width: 1280, height: 900});
    const confirmCheck = page.locator('#muConfirmed'); await confirmCheck.check();
    await page.locator(selectors.confirm).click();
    await page.waitForFunction(id => ReferenceWorkspace.getSpaceModels().find(model => model.id === id)?.result.summary.timber_volume_mm3 === '3828000', fixtureId);
    await page.locator(selectors.dialog).waitFor({state: 'hidden'});
    const committed = await state();
    check('confirm updates same model exactly once with one undo entry', committed.models.length === 1 && committed.models[0].id === fixtureId &&
      committed.models[0].result.summary.timber_volume_mm3 === '3828000' && committed.undo === original.undo + 1 && committed.project.dirty);
    check('confirm preserves live native source', committed.scene === original.scene && committed.nativeRevision === original.nativeRevision);
    await page.screenshot({path: path.join(output, 'committed-desktop.png')});
    await close();
    await page.evaluate(async () => {const result = await apiRequest('line undo'); if (!result.ok) throw Error(JSON.stringify(result));});
    const undone = await state(); const oldRecord = await page.evaluate(() => __f1bOld);
    assert.deepEqual(undone.models, [oldRecord]); check('single undo restores the complete old source input result record', true);
    check('model undo leaves current29 native scene intact', undone.scene === original.scene && undone.nativeRevision === original.nativeRevision);
    await page.evaluate(async () => {const result = await apiRequest('line redo'); if (!result.ok) throw Error(JSON.stringify(result));});
    const adopted = await state(), oldContext = adopted.project.contextToken;
    await page.evaluate(async () => {const bytes = await ReferenceWorkspace.exportBytes(); window.__f1bUpdatedArchive = Array.from(bytes);
      await ReferenceWorkspace.importBytes(bytes, 'f1b-updated.gcanvas');});
    const reopened = await state(); assert.deepEqual(reopened.models, adopted.models);
    check('real ZIP export and fresh context native-verified reopen preserve the complete updated model', reopened.project.contextToken !== oldContext);
    fs.writeFileSync(path.join(output, 'updated.gcanvas'), Buffer.from(await page.evaluate(() => __f1bUpdatedArchive)));
    await delayed('Cancel', async () => {await page.locator(selectors.cancel).click();}, true);
    await delayed('Close', async () => page.keyboard.press('Escape'), true);
    await delayed('Changed native source', async () => page.evaluate(async () => {
      let result = await apiRequest('line timber 0 31 33 role boundary');
      if (result.preview?.valid) result = await apiRequest('line confirm ' + result.preview.token);
      if (!result.ok) throw Error(JSON.stringify(result));
    }));
    await delayed('Undo history', async () => page.evaluate(async () => {
      const result = await apiRequest('line undo'); if (!result.ok) throw Error(JSON.stringify(result));
    }));
    await delayed('Project revision', async () => page.evaluate(() => ReferenceWorkspace.setFaceProjection(1, 0,
      {kind: 'space-boundary-plan', view: 'bottom', region: 'interior', wallSide: 'outside'})));
    await delayed('Same-ID replaced record', async () => page.evaluate(id => {
      const record = ReferenceWorkspace.getSpaceModels().find(model => model.id === id); record.name = '同 ID 替換紀錄';
      ReferenceWorkspace.updateSpaceModel(id, record);
    }, fixtureId));
    await delayed('Deleted model', async () => page.evaluate(id => ReferenceWorkspace.removeSpaceModel(id), fixtureId));
    await delayed('Switched project context', async () => page.evaluate(() => ReferenceWorkspace.newProject()));
    await delayed('Cancel during final native revalidation', async () => page.locator(selectors.cancel).click(), true, 'confirm');
    await delayed('Source changed during final native revalidation', async () => page.evaluate(async () => {
      let result = await apiRequest('line timber 0 31 33 role boundary');
      if (result.preview?.valid) result = await apiRequest('line confirm ' + result.preview.token);
      if (!result.ok) throw Error(JSON.stringify(result));
    }), false, 'confirm');
    await restore();
    await page.evaluate(async id => {
      const saved = ReferenceWorkspace.getSpaceModels().find(model => model.id === id);
      delete saved.source.projection; ReferenceWorkspace.updateSpaceModel(id, saved);
      for (const line of ['surface 8 origin 0 0 2500 u +x v +y rect 0 0 4000 3000',
        'timber 8 27 33 role boundary', 'place 8 on 8 at-face e0 +u +n']) {
        let result = await apiRequest('line ' + line);
        if (result.preview?.valid) result = await apiRequest('line confirm ' + result.preview.token);
        if (!result.ok) throw Error(JSON.stringify(result));
      }
      await refreshSurfaces(); await renderObjects();
    }, fixtureId);
    const rectangleBefore = await state();
    await open(); await page.locator(selectors.placement).selectOption('8');
    await page.waitForFunction(() => ModelUpdateApp.snapshot().placementId === 8 && !ModelUpdateApp.snapshot().busy);
    for (const edge of await page.locator(selectors.edge).all()) await edge.check();
    check('embedded rectangle with a real placed timber exposes no unsupported timber choices',
      await page.locator(selectors.timber).count() === 0 && /內含矩形.*不可納入角材/.test(await page.locator('#muTimbers').innerText()));
    const requestsBeforeForge = producerRequests;
    await page.evaluate(() => {const input = document.createElement('input'); input.type = 'checkbox';
      input.dataset.muTimber = '8'; input.checked = true; document.querySelector('#muTimbers').append(input);});
    await page.locator(selectors.preview).click(); await waitPhase('failed');
    assert.deepEqual(await state(), rectangleBefore);
    check('forged embedded rectangle timber selection is refused before producer or record/history write',
      producerRequests === requestsBeforeForge && /內含矩形.*不可納入角材/.test(await page.locator(selectors.status).innerText()));
    await close(); await open(); await page.locator(selectors.placement).selectOption('8');
    await page.waitForFunction(() => ModelUpdateApp.snapshot().placementId === 8 && !ModelUpdateApp.snapshot().busy);
    for (const edge of await page.locator(selectors.edge).all()) await edge.check();
    await preview(); assert.deepEqual(await state(), rectangleBefore);
    check('embedded rectangle without selected timbers remains a true-native strict-store-valid candidate',
      await page.evaluate(() => /未納入/.test(document.querySelector('#muDiff').innerText) && ModelUpdateApp.snapshot().phase === 'review'));
    await close();
    check('no uncaught browser exceptions or relevant console errors', errors.length === 0, errors);
    fs.writeFileSync(path.join(output, 'evidence.json'), JSON.stringify({url, title, browser: 'Playwright Chromium',
      browserPlugin: 'unavailable', viewports: [{width: 1280, height: 900}, {width: 390, height: 844}],
      checks, errors, warnings, modelId: fixtureId, routePath, producerRequests,
      entryMode: ownerEntry ? 'actual-owner-edit-entry' : 'direct-module',
      limitations: ['Physical iOS Safari and native OS file dialogs were not exercised.',
        ownerEntry ? 'Actual owner index/serve/edit wiring is required; no module injection.' : 'Direct module scope does not verify the shared-owner edit entry.']}, null, 2));
    console.log('F1B_EVIDENCE ' + JSON.stringify({assertions: checks.length, output, modelId: fixtureId, errors: errors.length}));
  } finally {
    for (const held of heldResponses) held.release.resolve();
    await browser.close();
  }
})().catch(error => {console.error(error.stack || error); process.exitCode = 1;});
