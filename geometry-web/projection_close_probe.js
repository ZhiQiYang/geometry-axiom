'use strict';

// Test-only scheduling fault injection. The browser creates the native close
// event; this probe can delay invoking the listener that the app registered.
// It never dispatches a replacement Event or edits the production closure.
function installProjectionCloseProbe() {
  const originalAdd = HTMLDialogElement.prototype.addEventListener;
  const nativeEvents = [], deliveries = [];
  let armed = false, heldEvent = null, callbacks = [];
  HTMLDialogElement.prototype.addEventListener = function(type, listener, options) {
    if (type !== 'close' || this.id !== 'fpDialog') return originalAdd.call(this, type, listener, options);
    return originalAdd.call(this, type, event => {
      const invoke = () => {
        deliveries.push({at: performance.now(), eventTime: event.timeStamp, trusted: event.isTrusted});
        if (typeof listener === 'function') listener.call(this, event); else listener.handleEvent(event);
      };
      if (armed) callbacks.push(invoke); else invoke();
    }, options);
  };
  document.addEventListener('close', event => {
    if (event.target.id !== 'fpDialog') return;
    const entry = {at: performance.now(), eventTime: event.timeStamp, trusted: event.isTrusted};
    nativeEvents.push(entry);
    if (armed) heldEvent = entry;
  }, true);
  window.__projectionCloseProbe = {
    nativeEvents, deliveries,
    arm() {
      if (armed || callbacks.length) throw Error('Previous close gate is still active');
      heldEvent = null; armed = true;
    },
    snapshot() {
      return {armed, heldEvent, callbackCount: callbacks.length, nativeEvents: nativeEvents.slice(), deliveries: deliveries.slice()};
    },
    release() {
      if (!heldEvent) throw Error('No browser-generated close event was received');
      const row = {releasedAt: performance.now(), ...this.snapshot()};
      armed = false;
      const pending = callbacks; callbacks = [];
      for (const invoke of pending) invoke();
      return row;
    },
    cleanup() {
      armed = false;
      const pending = callbacks; callbacks = [];
      for (const invoke of pending) invoke();
      HTMLDialogElement.prototype.addEventListener = originalAdd;
    },
  };
}

// Delay consumption of one actual surfaces reply from FaceProjection.readSource.
// Concurrent background reads cannot claim it, and no reply is synthesized.
function installProjectionSourceGate() {
  const original = window.fetch;
  const evidence = {phase: 'armed', claimed: 0, nativeOK: false, caller: null};
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  window.__projectionSourceGate = evidence;
  const intercepted = async (...args) => {
    const caller = new Error().stack || '';
    let command;
    try { command = JSON.parse(args[1]?.body || '{}').cmd; } catch (_) {}
    const targeted = evidence.phase === 'armed' && String(args[0]) === '/api' && command === 'surfaces' &&
      /(?:^|\n)\s*at (?:async )?readSource\s*\(/.test(caller);
    if (targeted) {
      evidence.phase = 'requested'; evidence.claimed++; evidence.caller = caller;
      window.fetch = original;
    }
    const response = await original(...args);
    if (targeted) {
      const json = response.json.bind(response);
      response.json = async () => {
        const data = await json(); evidence.nativeOK = data.ok === true; evidence.phase = 'held';
        await gate; evidence.phase = 'released'; return data;
      };
    }
    return response;
  };
  window.fetch = intercepted;
  window.__releaseProjectionSource = () => {
    release();
    if (window.fetch === intercepted) window.fetch = original;
  };
}

function projectionCloseRegression({check, evaluate, click, select, checked, key, setup,
  wait, openFaceModel, closeWorkspace, scene, projectionDialog, record}) {
  return async () => {
    const evidence = [];
    // Observe the actual public entry called by the trusted workspace button.
    // The return value and the app's source/API checks are unchanged.
    await evaluate(`(()=>{
      const original=FaceProjection.open;
      window.__projectionOriginalOpen=original;
      window.__projectionOpenObservation={calls:0,finished:0};
      FaceProjection.open=function(...args){
        const id=++window.__projectionOpenObservation.calls;
        const pending=original.apply(this,args);
        pending.then(()=>{window.__projectionOpenObservation.finished=id;},()=>{window.__projectionOpenObservation.finished=id;});
        return pending;
      };
    })()`);
    try {
      for (const phase of ['during-source-read', 'after-reopen']) {
        await setup(['surface 71 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000']);
        const original = await scene();
        await evaluate(`enterFocus('face',71)`); await openFaceModel();
        await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'close-race source ready');
        const previousEvents = await evaluate(`window.__projectionCloseProbe.nativeEvents.length`);
        await projectionDialog('bottom');
        await wait(`window.__projectionCloseProbe.nativeEvents.length>${previousEvents}`, 'fixture close event completed');
        await click('#smSetProjection');
        await wait(`document.querySelector('#fpDialog').open`, 'clear fixture definition');
        await select('#fpPurpose', 'general');
        await evaluate(`window.__projectionCloseProbe.arm()`);
        await click('#fpApply');
        await wait(`!document.querySelector('#fpDialog').open`, 'clear closes synchronously');
        check(`close-race ${phase}: explicit clear commits without changing geometry`,
          await evaluate(`ReferenceWorkspace.getFaceProjection(71,71)===null`) && await scene() === original);
        await wait(`window.__projectionCloseProbe.snapshot().heldEvent!==null`, 'native close received by gate');
        const held = await evaluate(`window.__projectionCloseProbe.snapshot()`);
        check(`close-race ${phase}: delayed notification is browser generated`, held.armed && held.heldEvent.trusted === true, held);
        if (phase === 'during-source-read') await evaluate(`(${installProjectionSourceGate.toString()})()`);
        await click('#smSetProjection');
        if (phase === 'during-source-read') await wait(`window.__projectionSourceGate.phase==='held'`, 'new open source reply held');
        else await wait(`document.querySelector('#fpDialog').open`, 'new open is visible before old close');
        const overlap = await evaluate(`({open:!!document.querySelector('#fpDialog').open,
          observation:{...window.__projectionOpenObservation},source:window.__projectionSourceGate?{...window.__projectionSourceGate}:null})`);
        check(`close-race ${phase}: requested overlap is reached`, phase === 'during-source-read'
          ? !overlap.open && overlap.observation.finished < overlap.observation.calls && overlap.source.nativeOK && overlap.source.claimed === 1
          : overlap.open && overlap.observation.finished === overlap.observation.calls, overlap);
        const delivery = await evaluate(`window.__projectionCloseProbe.release()`);
        if (phase === 'during-source-read') await evaluate(`window.__releaseProjectionSource()`);
        await wait(`window.__projectionOpenObservation.finished===window.__projectionOpenObservation.calls`, 'new open promise settled');
        const reopened = await evaluate(`document.querySelector('#fpDialog').open`);
        check(`close-race ${phase}: old notification does not cancel the new open`, reopened);
        let saved = false;
        if (reopened) {
          await select('#fpPurpose', 'space-boundary-plan');
          const usable = await evaluate(`!document.querySelector('#fpView').disabled`);
          if (usable) {
            await select('#fpView', 'top'); await checked('#fpInterior', true); await click('#fpApply');
            // Observe the resulting state after the real async source read.
            await wait(`!document.querySelector('#fpDialog').open || !document.querySelector('#fpPurpose').disabled`, 'new apply settles');
            saved = await evaluate(`!document.querySelector('#fpDialog').open && ReferenceWorkspace.getFaceProjection(71,71)?.view==='top'`);
          }
        }
        check(`close-race ${phase}: the new session accepts and saves its own definition`, saved);
        check(`close-race ${phase}: source World stays byte identical`, await scene() === original);
        evidence.push({phase, held, overlap, delivery, reopened, saved});
        // Cleanup only: a failed old implementation can leave an unusable modal.
        const cleanup = await evaluate(`(()=>{const d=document.querySelector('#fpDialog'),open=!!d?.open,count=window.__projectionCloseProbe.nativeEvents.length;d?.close();window.__releaseProjectionSource?.();return {open,count};})()`);
        if (cleanup.open) await wait(`window.__projectionCloseProbe.nativeEvents.length>${cleanup.count}`, 'failed-case modal cleanup completed');
        await closeWorkspace();
      }
      // Keep the ordinary user exits covered through native pointer/keyboard.
      await setup(['surface 71 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000']);
      const original = await scene();
      await evaluate(`enterFocus('face',71)`); await openFaceModel();
      await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'ordinary cancellation source');
      for (const action of ['cancel', 'escape']) {
        await click('#smSetProjection'); await wait(`document.querySelector('#fpDialog').open`, action + ' draft opened');
        await select('#fpPurpose', 'space-boundary-plan'); await select('#fpView', 'bottom'); await checked('#fpInterior', true);
        const beforeClose = await evaluate(`window.__projectionCloseProbe.nativeEvents.length`);
        if (action === 'cancel') await click('#fpCancel'); else await key('Escape', 'Escape', 27);
        await wait(`!document.querySelector('#fpDialog').open`, action + ' draft closed');
        await wait(`window.__projectionCloseProbe.nativeEvents.length>${beforeClose}`, action + ' native close completed');
        check(`close-race ordinary ${action} discards the draft`,
          await evaluate(`ReferenceWorkspace.getFaceProjection(71,71)===null`) && await scene() === original);
      }
      await closeWorkspace();
    } finally {
      const tail = await evaluate(`(()=>{
        window.__releaseProjectionSource?.();
        const value=window.__projectionCloseProbe.snapshot();window.__projectionCloseProbe.cleanup();
        if(window.__projectionOriginalOpen)FaceProjection.open=window.__projectionOriginalOpen;
        return value;
      })()`);
      record({kind:'controlled delivery of real native close callbacks; not natural recurrence of an earlier failure',cases:evidence,tail});
    }
  };
}

module.exports = {installProjectionCloseProbe, projectionCloseRegression};
