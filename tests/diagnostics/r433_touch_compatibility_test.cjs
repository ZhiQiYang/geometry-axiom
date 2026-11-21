/* Node listener contract only: a VM, synthetic events and a small DOM adapter.
 * This is not Chrome/CDP evidence and does not exercise trusted browser input,
 * browser hit testing, native compatibility-event generation or sheet layout.
 * The product file is loaded unchanged and uses its real timers, including the
 * existing 500 ms hold. R433_TOUCH_SOURCE selects a product file for red/green
 * and named-withdrawal runs; it never edits that file.
 */
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createHash } = require('node:crypto');
const { performance } = require('node:perf_hooks');
const { test } = require('node:test');

const sourcePath = path.resolve(process.env.R433_TOUCH_SOURCE ||
  path.join(__dirname, '../../geometry-web/touch-gestures.js'));
const sourceBytes = fs.readFileSync(sourcePath);

function listeners() {
  const entries = new Map();
  return {
    addEventListener(type, listener) {
      if (!entries.has(type)) entries.set(type, []);
      entries.get(type).push(listener);
    },
    dispatch(type, values = {}) {
      const event = {
        type, isTrusted: false, defaultPrevented: false, immediateStopped: false,
        preventDefault() { this.defaultPrevented = true; },
        stopImmediatePropagation() { this.immediateStopped = true; },
        ...values,
      };
      for (const listener of entries.get(type) || []) {
        listener(event);
        if (event.immediateStopped) break;
      }
      return event;
    },
  };
}

function element(name) {
  return {
    name, parentNode: null, children: [], hidden: false, dataset: {},
    classList: { add() {} },
    style: { setProperty() {} },
    setAttribute() {},
    append(child) {
      child.remove();
      child.parentNode = this;
      this.children.push(child);
    },
    remove() {
      if (!this.parentNode) return;
      const siblings = this.parentNode.children;
      siblings.splice(siblings.indexOf(this), 1);
      this.parentNode = null;
    },
    contains(child) {
      for (let current = child; current; current = current.parentNode)
        if (current === this) return true;
      return false;
    },
  };
}

function fixture(t) {
  const window = listeners();
  const document = { ...listeners(), body: element('body'), hidden: false,
    createElementNS() { return element('svg'); } };
  const surface = element('canvas');
  const sheet = element('sheet');
  const openAction = element('open action');
  document.body.append(surface);
  surface.append(sheet);
  sheet.append(openAction);
  sheet.hidden = true;
  document.getElementById = id => id === 'canvasCtxMenu' ? sheet : null;
  const captured = new Set();
  surface.setPointerCapture = id => captured.add(id);
  surface.hasPointerCapture = id => captured.has(id);
  surface.releasePointerCapture = id => {
    captured.delete(id);
    window.dispatch('lostpointercapture', { pointerId: id });
  };

  const timers = new Set();
  function schedule(callback, delay) {
    const timer = setTimeout(() => { timers.delete(timer); callback(); }, delay);
    timers.add(timer);
    return timer;
  }
  function unschedule(timer) { clearTimeout(timer); timers.delete(timer); }
  const calls = { openMenu: 0, beginSingle: 0, endSingle: 0, cancelSingle: 0,
    sheetClick: 0, errors: [] };
  let opened;
  const menuOpened = new Promise(resolve => { opened = resolve; });
  const adapter = {
    surface,
    contains: event => surface.contains(event.target),
    eligible: event => surface.contains(event.target) && !sheet.contains(event.target),
    captureDown: () => ({ menu: true }),
    current: () => true,
    clearPresentation() {},
    closeMenu() { sheet.hidden = true; },
    openMenu() {
      calls.openMenu++;
      document.body.append(sheet);
      sheet.hidden = false;
      opened();
      return true;
    },
    beginSingle() { calls.beginSingle++; return true; },
    endSingle() { calls.endSingle++; },
    cancelSingle() { calls.cancelSingle++; },
    onError(error) { calls.errors.push(error); },
  };
  t.after(() => {
    window.dispatch('blur');
    for (const timer of timers) clearTimeout(timer);
    timers.clear();
  });
  const context = vm.createContext({
    window, document, performance,
    setTimeout: schedule, clearTimeout: unschedule,
    requestAnimationFrame: callback => schedule(() => callback(performance.now()), 16),
    cancelAnimationFrame: unschedule,
    MutationObserver: class { observe() {} },
    CursorV2: { pressRing: () => '' },
  });
  vm.runInContext(sourceBytes.toString('utf8'), context, { filename: sourcePath });
  window.CanvasTouchGestures.attach(adapter);
  // A later listener represents the sheet's action handler. This models only
  // listener order and stopImmediatePropagation, not DOM event propagation.
  window.addEventListener('click', event => {
    if (event.target === openAction) calls.sheetClick++;
  });
  return { window, document, surface, sheet, openAction, adapter, calls, menuOpened };
}

function touch(target, pointerId, clientX = 78, clientY = 673.6) {
  return { target, pointerId, pointerType: 'touch', isPrimary: true, clientX, clientY };
}

function suppressed(event, name) {
  assert.equal(event.defaultPrevented, true, name + ': default prevented');
  assert.equal(event.immediateStopped, true, name + ': later listener stopped');
}

function allowed(event, name) {
  assert.equal(event.defaultPrevented, false, name + ': default remains available');
  assert.equal(event.immediateStopped, false, name + ': later listener remains available');
}

test('Node listener contract: consumed touch and independent inputs (synthetic, not CDP)',
  { timeout: 2000 }, async t => {
    t.diagnostic('Evidence scope: Node VM / synthetic events / real product timers; not CDP.');
    t.diagnostic('Product SHA-256: ' + createHash('sha256').update(sourceBytes).digest('hex'));
    const f = fixture(t);
    const originalTouch = touch(f.surface, 7);
    const began = performance.now();
    suppressed(f.window.dispatch('pointerdown', originalTouch), 'R433_CANVAS_TOUCH_DOWN');
    await f.menuOpened;
    t.diagnostic('Observed menu opening after ' + (performance.now() - began).toFixed(1) + ' ms.');
    assert.equal(f.calls.openMenu, 1, 'R433_LONG_PRESS_OPENS_MENU');
    assert.equal(f.sheet.parentNode, f.document.body, 'R433_SHEET_MOVED_TO_BODY');
    assert.equal(f.adapter.contains({ target: f.openAction }), false, 'R433_SHEET_OUTSIDE_CANVAS');
    suppressed(f.window.dispatch('pointerup', originalTouch), 'R433_LONG_PRESS_UP');
    assert.equal(f.calls.beginSingle, 0, 'R433_LONG_PRESS_DOES_NOT_BEGIN_SINGLE');
    assert.equal(f.calls.endSingle, 0, 'R433_LONG_PRESS_DOES_NOT_END_SINGLE');

    // Simulate a retargeted compatibility click whose ID and coordinates no
    // longer identify the original touch. The controller must consume it.
    const retargeted = { ...touch(f.openAction, 107, 83, 673),
      sourceCapabilities: { firesTouchEvents: true }, detail: 1 };
    suppressed(f.window.dispatch('click', retargeted), 'R433_CONSUMED_TOUCH_RETARGETED_CLICK');
    assert.equal(f.calls.sheetClick, 0, 'R433_CONSUMED_TOUCH_NO_SHEET_ACTION');

    // These are simulated mouse/keyboard inputs, not trusted browser events.
    // Even an ID still present in the consumed-touch set must not block mouse.
    const mouse = { target: f.openAction, pointerType: 'mouse', pointerId: 7,
      clientX: 83, clientY: 673, sourceCapabilities: { firesTouchEvents: false }, detail: 1 };
    allowed(f.window.dispatch('pointerdown', mouse), 'R433_MOUSE_DOWN_ALLOWED');
    allowed(f.window.dispatch('click', mouse), 'R433_MOUSE_CLICK_ALLOWED');
    allowed(f.window.dispatch('keydown', { target: f.openAction, key: 'Enter' }),
      'R433_KEYBOARD_ENTER_ALLOWED');
    allowed(f.window.dispatch('click', { target: f.openAction, pointerId: -1,
      pointerType: '', sourceCapabilities: null, detail: 0, clientX: 0, clientY: 0 }),
    'R433_KEYBOARD_CLICK_ALLOWED');
    assert.equal(f.calls.sheetClick, 2, 'R433_MOUSE_AND_KEYBOARD_REACH_ACTION');

    // A separate touch begins on the sheet after the consumed canvas touch.
    // Reuse the original ID to cover both sequence and pointer-ID retirement.
    const nextTouch = touch(f.openAction, 7, 84, 674);
    allowed(f.window.dispatch('pointerdown', nextTouch), 'R433_NEW_SHEET_TOUCH_DOWN');
    allowed(f.window.dispatch('pointerup', nextTouch), 'R433_NEW_SHEET_TOUCH_UP');
    allowed(f.window.dispatch('click', { ...nextTouch,
      sourceCapabilities: { firesTouchEvents: true }, detail: 1 }),
    'R433_NEW_SHEET_TOUCH_CLICK');
    assert.equal(f.calls.sheetClick, 3, 'R433_NEW_SHEET_TOUCH_REACHES_ACTION_ONCE');

    const cancelledTouch = touch(f.surface, 8, 90, 600);
    suppressed(f.window.dispatch('pointerdown', cancelledTouch), 'R433_CANCEL_TOUCH_DOWN');
    suppressed(f.window.dispatch('pointercancel', cancelledTouch), 'R433_POINTER_CANCEL');
    assert.equal(f.calls.cancelSingle, 1, 'R433_POINTER_CANCEL_CANCELS_OPERATION_ONCE');
    suppressed(f.window.dispatch('click', { ...touch(f.openAction, 108, 94, 601),
      sourceCapabilities: { firesTouchEvents: true }, detail: 1 }),
    'R433_POINTER_CANCEL_COMPATIBILITY_CLICK');
    assert.equal(f.calls.sheetClick, 3, 'R433_POINTER_CANCEL_NO_SHEET_ACTION');
    assert.equal(f.calls.openMenu, 1, 'R433_CANCELLED_TOUCH_OPENS_NO_MENU');
    assert.equal(f.calls.beginSingle, 0, 'R433_CANCELLED_TOUCH_BEGINS_NO_OPERATION');
    assert.equal(f.calls.endSingle, 0, 'R433_CANCELLED_TOUCH_ENDS_NO_OPERATION');
    assert.deepEqual(f.calls.errors, [], 'R433_NO_ADAPTER_ERRORS');

    // A scroll generated by the touch sheet itself (including a descendant)
    // is not an external viewport interruption. The same held pointer must
    // still be allowed to open and keep its menu before release.
    const sheetScroll = fixture(t);
    const held = touch(sheetScroll.surface, 29);
    suppressed(sheetScroll.window.dispatch('pointerdown', held), 'R433_SELF_SCROLL_TOUCH_DOWN');
    await sheetScroll.menuOpened;
    assert.equal(sheetScroll.sheet.hidden, false, 'R433_SELF_SCROLL_MENU_OPENED');
    sheetScroll.window.dispatch('scroll', { target: sheetScroll.sheet });
    assert.equal(sheetScroll.sheet.hidden, false, 'R433_SELF_SCROLL_MUST_PRESERVE_MENU');
    sheetScroll.window.dispatch('wheel', { target: sheetScroll.openAction });
    assert.equal(sheetScroll.sheet.hidden, false, 'R433_DESCENDANT_WHEEL_MUST_PRESERVE_MENU');
    // Scrolling the viewport, unlike scrolling the sheet, must still cancel.
    sheetScroll.window.dispatch('scroll', { target: sheetScroll.surface });
    assert.equal(sheetScroll.sheet.hidden, true, 'R433_EXTERNAL_SCROLL_CLOSES_MENU');
    assert.equal(sheetScroll.calls.cancelSingle, 1, 'R433_EXTERNAL_SCROLL_CANCELS_GESTURE');

    const pending = fixture(t);
    suppressed(pending.window.dispatch('pointerdown', touch(pending.surface, 30)), 'R433_PENDING_TOUCH_DOWN');
    pending.window.dispatch('scroll', { target: pending.surface });
    assert.equal(pending.calls.cancelSingle, 1, 'R433_PENDING_SCROLL_STILL_CANCELS');
  });
