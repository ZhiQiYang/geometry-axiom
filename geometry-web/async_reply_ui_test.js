/* Late-reply UI races. The harness holds one reply, then uses normal clicks and
 * keyboard input. Assertions describe the state after that reply is applied.
 * The held-proj case starts a newer edit while the older proj reply is held. */
'use strict';
const { installConfirmationDumpGate } = require('./cdp_confirmation_gate.js');

function installEditBoundaryGate(scope, callerStack = () => new Error().stack || '') {
  const original = scope.fetch;
  const evidence = { phase: 'armed', caller: null, command: null, matched: false };
  scope.__editBoundaryHeld = false;
  scope.__editBoundaryGate = evidence;
  const gate = new Promise(resolve => { scope.__releaseEditBoundary = resolve; });
  scope.fetch = async (...args) => {
    const caller = callerStack();
    let command;
    try { command = JSON.parse(args[1]?.body || '{}').cmd; } catch (_) {}
    const targeted = evidence.phase === 'armed' && String(args[0]) === '/api' &&
      /^boundary \d+$/.test(command || '') &&
      /(?:^|\n)\s*at (?:async )?enterEdit\s*\(/.test(caller);
    if (targeted) {
      evidence.phase = 'requested'; evidence.caller = caller; evidence.command = command; evidence.matched = true;
      scope.fetch = original;
    }
    try {
      const response = await original(...args);
      if (targeted) {
        const json = response.json.bind(response);
        response.json = async () => {
          const data = await json();
          evidence.phase = 'held'; scope.__editBoundaryHeld = true;
          await gate;
          evidence.phase = 'released'; scope.__editBoundaryHeld = false;
          return data;
        };
      }
      return response;
    } catch (error) {
      if (targeted) evidence.phase = 'failed';
      throw error;
    }
  };
}

function installHandleProjectionGate(scope, callerStack = () => new Error().stack || '') {
  const original = scope.fetch;
  const evidence = { phase: 'armed', caller: null, command: null, matched: false };
  scope.__handleProjectionHeld = false;
  scope.__handleProjectionGate = evidence;
  const gate = new Promise(resolve => { scope.__releaseHandleProjection = resolve; });
  scope.fetch = async (...args) => {
    const caller = callerStack();
    let command;
    try { command = JSON.parse(args[1]?.body || '{}').cmd; } catch (_) {}
    const targeted = evidence.phase === 'armed' && String(args[0]) === '/api' &&
      /^proj \d+ /.test(command || '') &&
      /(?:^|\n)\s*at (?:async )?drawEditHandles\s*\(/.test(caller);
    if (targeted) {
      evidence.phase = 'requested'; evidence.caller = caller; evidence.command = command; evidence.matched = true;
      scope.fetch = original;
    }
    try {
      const response = await original(...args);
      if (targeted) {
        const json = response.json.bind(response);
        response.json = async () => {
          const data = await json();
          evidence.phase = 'held'; scope.__handleProjectionHeld = true;
          await gate;
          evidence.phase = 'released'; scope.__handleProjectionHeld = false;
          return data;
        };
      }
      return response;
    } catch (error) {
      if (targeted) evidence.phase = 'failed';
      throw error;
    }
  };
}

function asyncReplyUiRegression(h) {
  const rect = id => `surface ${id} origin 0 0 2500 u +x v +y outline 0,0 2000,0 2000,1000 0,1000`;
  const projectionFields = () => h.evaluate(`(()=>{const active=document.activeElement;return {focus:active&&active.id||'',height:document.querySelector('#smHeight').value,bottom:document.querySelector('#smBottom').value,pending:document.querySelector('#smProjectionCallout').getAttribute('aria-busy')==='true',projection:ReferenceWorkspace.getFaceProjection(oc.edit.bid,Number(document.querySelector('#smSourceSelect').value))};})()`);
  async function prepareProjection(width, height, id) {
    await h.closeWorkspace();
    await h.viewport(width, height);
    await h.setup([rect(id)]);
    await h.openFlowFace(id);
    if (width <= 720) await h.click('#smTabSetup');
    await h.wait(`document.querySelector('#smSettings').disabled===false && document.querySelector('#smBottom').value==='' && document.querySelector('#smHeight').value==='3000' && document.querySelector('#smConfirmProjection').disabled===false`, 'projection form ready '+width);
  }
  async function holdProjection(label) {
    await h.evaluate(`(${installConfirmationDumpGate.toString()})(window)`);
    await h.click('#smConfirmProjection');
    await h.wait(`window.__flowProjectionHeld===true`, 'held projection '+label);
    const gate = await h.evaluate(`window.__flowProjectionGate`);
    if (!gate?.matched || gate.phase !== 'held') throw Error('Projection reply was not held for '+label+': '+JSON.stringify(gate));
  }
  async function releaseProjection(label) {
    await h.evaluate(`window.__releaseFlowProjection()`);
    await h.wait(`window.__flowProjectionHeld===false && document.querySelector('#smProjectionCallout').getAttribute('aria-busy')!=='true'`, 'projection reply applied '+label);
    await h.settle();
  }
  async function typeHeight(value) {
    await h.click('#smHeight');
    await h.key('a', 'KeyA', 65, 2);
    await h.key('Backspace', 'Backspace', 8);
    await h.send('Input.insertText', { text: value });
    await h.wait(`document.activeElement===document.querySelector('#smHeight') && document.querySelector('#smHeight').value===${JSON.stringify(value)}`, 'keyboard height '+value);
  }
  return async () => {
    for (const [width, height] of [[1400, 900], [390, 844]]) {
      const label = width + 'px';
      await prepareProjection(width, height, width === 1400 ? 411 : 421);
      await holdProjection(label + ' control');
      const untouched = await projectionFields();
      if (untouched.focus === 'smHeight' || untouched.bottom !== '' || untouched.height !== '3000') throw Error('Control focus was already on the height field: '+JSON.stringify(untouched));
      await releaseProjection(label + ' control');
      const control = await projectionFields();
      h.check(label + ' confirming projection without editing a field still moves focus to the empty wall bottom', control.focus === 'smBottom' && control.bottom === '' && control.height === '3000' && control.pending === false && control.projection?.view === 'top' && control.projection?.kind === 'space-boundary-plan', control);

      await prepareProjection(width, height, width === 1400 ? 412 : 422);
      await holdProjection(label + ' height');
      await typeHeight('3100');
      await releaseProjection(label + ' height');
      const edited = await projectionFields();
      h.check(label + ' a wall-height edit during projection confirmation keeps focus and the typed height', edited.focus === 'smHeight' && edited.height === '3100' && edited.bottom === '' && edited.pending === false && edited.projection?.view === 'top', edited);

      await h.closeWorkspace();
      await h.viewport(width, height);
      const id = width === 1400 ? 413 : 423;
      await h.setup([rect(id)]);
      const world = await h.scene();
      await h.click('#btnObj');
      await h.wait(`view3===true && document.body.classList.contains('v3-mode') && !document.querySelector('#cv').hasAttribute('hidden') && document.querySelector('#viewToolbar').hidden===false`, 'view3 open '+label);
      const surfaceId = String(id);
      const listed = await h.evaluate(`[...document.querySelectorAll('#workSurf option')].map(o=>o.value)`);
      if (!listed.includes(surfaceId)) throw Error('Work surface was not listed for '+label+': '+JSON.stringify(listed));
      if (await h.evaluate(`document.querySelector('#workSurf').value!==${JSON.stringify(surfaceId)}`)) {
        if (width <= 900 && await h.evaluate(`!document.body.classList.contains('drawer-left-open')`)) {
          await h.click('#toggleLeft');
          await h.wait(`document.body.classList.contains('drawer-left-open')`, 'left drawer '+label);
        }
        await h.select('#workSurf', surfaceId);
        if (width <= 900) {
          await h.click('.sidebar-left [data-close-panel="left"]');
          await h.wait(`!document.body.classList.contains('drawer-left-open')`, 'left drawer closed '+label);
        }
      }
      await h.wait(`document.querySelector('#workSurf').value===${JSON.stringify(surfaceId)} && document.querySelector('[data-v3-tool="edit"]').disabled!==true`, 'view3 surface '+label);
      await h.evaluate(`(${installEditBoundaryGate.toString()})(window)`);
      await h.click('[data-v3-tool="edit"]');
      await h.wait(`window.__editBoundaryHeld===true`, 'held edit boundary '+label);
      const held = await h.evaluate(`window.__editBoundaryGate`);
      if (!held?.matched || held.phase !== 'held' || !/^boundary \d+$/.test(held.command || '')) throw Error('Edit boundary reply was not held for '+label+': '+JSON.stringify(held));
      await h.click('[data-v3-tool="view"]');
      const switched = await h.evaluate(`({tool,active:document.querySelector('[data-v3-tool].active')?.dataset.v3Tool,handles:document.querySelectorAll('#world polygon[stroke-dasharray="8 4"],#world circle[fill="#c0392b"]').length})`);
      if (switched.tool !== 'view' || switched.active !== 'view' || switched.handles !== 0) throw Error('View was not selected before the late boundary reply: '+JSON.stringify(switched));
      await h.evaluate(`window.__releaseEditBoundary()`);
      await h.wait(`window.__editBoundaryHeld===false && window.__editBoundaryGate.phase==='released'`, 'edit boundary reply applied '+label);
      await h.settle();
      const late = await h.evaluate(`({tool,active:document.querySelector('[data-v3-tool].active')?.dataset.v3Tool,select:document.querySelector('#tool').value,handles:document.querySelectorAll('#world polygon[stroke-dasharray="8 4"],#world circle[fill="#c0392b"]').length,editLoops:typeof editLoops==='undefined'?null:editLoops&&editLoops.length})`);
      const after = await h.scene();
      h.check(label + ' a view click during an edit boundary read leaves no edit handles and keeps view', late.tool === 'view' && late.active === 'view' && late.select === 'view' && late.handles === 0 && late.editLoops == null && after === world, late);

      await h.closeWorkspace();
      await h.viewport(width, height);
      const heldId = width === 1400 ? 414 : 424;
      await h.setup([rect(heldId)]);
      const heldWorld = await h.scene();
      await h.click('#btnObj');
      await h.wait(`view3===true && document.body.classList.contains('v3-mode') && !document.querySelector('#cv').hasAttribute('hidden') && document.querySelector('#viewToolbar').hidden===false`, 'view3 open held-proj '+label);
      const heldSurface = String(heldId);
      const heldListed = await h.evaluate(`[...document.querySelectorAll('#workSurf option')].map(o=>o.value)`);
      if (!heldListed.includes(heldSurface)) throw Error('Work surface was not listed for held-proj '+label+': '+JSON.stringify(heldListed));
      if (await h.evaluate(`document.querySelector('#workSurf').value!==${JSON.stringify(heldSurface)}`)) {
        if (width <= 900 && await h.evaluate(`!document.body.classList.contains('drawer-left-open')`)) {
          await h.click('#toggleLeft');
          await h.wait(`document.body.classList.contains('drawer-left-open')`, 'left drawer held-proj '+label);
        }
        await h.select('#workSurf', heldSurface);
        if (width <= 900) {
          await h.click('.sidebar-left [data-close-panel="left"]');
          await h.wait(`!document.body.classList.contains('drawer-left-open')`, 'left drawer closed held-proj '+label);
        }
      }
      await h.wait(`document.querySelector('#workSurf').value===${JSON.stringify(heldSurface)} && document.querySelector('[data-v3-tool="edit"]').disabled!==true`, 'view3 surface held-proj '+label);
      await h.evaluate(`(${installHandleProjectionGate.toString()})(window)`);
      await h.click('[data-v3-tool="edit"]');
      await h.wait(`window.__handleProjectionHeld===true`, 'held edit projection '+label);
      const heldProj = await h.evaluate(`window.__handleProjectionGate`);
      if (!heldProj?.matched || heldProj.phase !== 'held' || !/^proj \d+ /.test(heldProj.command || '')) throw Error('Edit projection reply was not held for '+label+': '+JSON.stringify(heldProj));
      const older = await h.evaluate(`({tool,handles:document.querySelectorAll('#world polygon[stroke-dasharray="8 4"],#world circle[fill="#c0392b"]').length})`);
      if (older.tool !== 'edit' || older.handles !== 0) throw Error('Older edit drew handles before its projection returned: '+JSON.stringify(older));
      await h.click('[data-v3-tool="view"]');
      await h.click('[data-v3-tool="edit"]');
      await h.wait(`window.__handleProjectionHeld===true && tool==='edit' && document.querySelector('[data-v3-tool].active')?.dataset.v3Tool==='edit' && document.querySelectorAll('#world polygon[stroke-dasharray="8 4"],#world circle[fill="#c0392b"]').length>0`, 'newer edit handles while older projection is held '+label);
      const newer = await h.evaluate(`({tool,active:document.querySelector('[data-v3-tool].active')?.dataset.v3Tool,select:document.querySelector('#tool').value,handles:document.querySelectorAll('#world polygon[stroke-dasharray="8 4"],#world circle[fill="#c0392b"]').length,editLoops:editLoops&&editLoops.length||0})`);
      const newerScene = await h.scene();
      if (!(newer.handles > 0) || newer.tool !== 'edit' || newerScene !== heldWorld) throw Error('Newer edit did not keep its handles and scene while the older projection was held: '+JSON.stringify(newer));
      await h.evaluate(`window.__releaseHandleProjection()`);
      await h.wait(`window.__handleProjectionHeld===false && window.__handleProjectionGate.phase==='released'`, 'older projection applied '+label);
      await h.settle();
      const released = await h.evaluate(`({tool,active:document.querySelector('[data-v3-tool].active')?.dataset.v3Tool,select:document.querySelector('#tool').value,handles:document.querySelectorAll('#world polygon[stroke-dasharray="8 4"],#world circle[fill="#c0392b"]').length,editLoops:editLoops&&editLoops.length||0})`);
      const releasedScene = await h.scene();
      h.check(label + ' releasing an older edit projection does not clear the newer edit handles', released.handles === newer.handles && released.handles > 0 && released.tool === 'edit' && released.active === 'edit' && released.select === 'edit' && released.editLoops > 0 && releasedScene === newerScene, { newer, released });
    }
  };
}

module.exports = { installEditBoundaryGate, installHandleProjectionGate, asyncReplyUiRegression };
