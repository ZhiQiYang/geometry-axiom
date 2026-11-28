/* O467 controlled-clock Node tests of the unchanged shipped touch controller.
 * Events and DOM ports are synthetic. This is not Chromium/trusted-input,
 * hit-testing, OS touch delivery, device timing or physical-device evidence.
 */
'use strict';
const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(process.env.R433_TOUCH_SOURCE ||
  path.join(__dirname, '../geometry-web/touch-gestures.js'), 'utf8');

function fixture() {
  let now = 0, serial = 0, current = true;
  const pending = new Map(), listeners = new Map(), capture = new Set(), nodes = [];
  const calls = { menu: 0, begin: 0, move: 0, end: 0, cancel: 0, cameras: [], errors: [] };
  const schedule = (fn, delay) => { const id = ++serial; pending.set(id, {at: now + delay, fn}); return id; };
  const element = () => ({dataset: {}, classList: {add() {}}, style: {setProperty() {}},
    setAttribute() {}, remove() { const i = nodes.indexOf(this); if (i >= 0) nodes.splice(i, 1); }});
  const window = {addEventListener(type, fn) {
    if (!listeners.has(type)) listeners.set(type, []); listeners.get(type).push(fn);
  }};
  const document = {body: {append(node) { nodes.push(node); }}, hidden: false,
    createElementNS: element, getElementById: () => null, addEventListener() {}};
  const context = vm.createContext({window, document, performance: {now: () => now},
    setTimeout: schedule, clearTimeout: id => pending.delete(id),
    requestAnimationFrame: fn => schedule(fn, 16), cancelAnimationFrame: id => pending.delete(id),
    MutationObserver: class {observe() {}}, CursorV2: {pressRing: () => '<circle/>'}, console});
  vm.runInContext(source, context, {filename: 'touch-gestures.production.js'});
  const adapter = {surface: {hasPointerCapture: id => capture.has(id),
    setPointerCapture: id => capture.add(id), releasePointerCapture: id => capture.delete(id)},
    current: () => current, eligible: () => true, contains: () => true,
    captureDown: () => ({menu: true}), closeMenu() {}, clearPresentation() {},
    openMenu() { calls.menu++; return true; }, beginSingle() { calls.begin++; return true; },
    moveSingle() { calls.move++; }, endSingle() { calls.end++; }, cancelSingle() { calls.cancel++; },
    localPoint: (x, y) => ({x, y}), getCamera: () => ({zoom: 2, x: 4, y: 6}),
    setCamera(value) { calls.cameras.push(JSON.parse(JSON.stringify(value))); },
    onError(error) { calls.errors.push(error); }};
  window.CanvasTouchGestures.attach(adapter);
  function emit(type, pointerId = 1, x = 0, y = 0, extra = {}) {
    const event = {type, pointerType: 'touch', pointerId, isPrimary: pointerId === 1,
      isTrusted: false, clientX: x, clientY: y, preventDefault() {}, stopImmediatePropagation() {}, ...extra};
    for (const fn of listeners.get(type) || []) fn(event);
  }
  function advance(target) {
    assert.ok(target >= now);
    for (;;) {
      const first = [...pending].sort((a, b) => a[1].at - b[1].at || a[0] - b[0])[0];
      if (!first || first[1].at > target) break;
      pending.delete(first[0]); now = first[1].at; first[1].fn(now);
    }
    now = target;
  }
  return {emit, advance, calls, nodes, stale: () => { current = false; }};
}

test('O467_R11_HOLD_500MS: no menu at 499ms, exactly one at 500ms', () => {
  const f = fixture(); f.emit('pointerdown'); f.advance(499);
  assert.equal(f.calls.menu, 0, 'O467_R11_HOLD_500MS'); f.advance(500);
  assert.equal(f.calls.menu, 1, 'O467_R11_HOLD_500MS'); f.advance(700); f.emit('pointerup');
  assert.equal(f.calls.menu, 1, 'O467_R11_HOLD_500MS');
  assert.equal(f.calls.begin + f.calls.end, 0, 'O467_R11_HOLD_NO_SINGLE');
});
test('O467_R11_RING_150MS: ring starts at 150ms and never opens the menu itself', () => {
  const f = fixture(); f.emit('pointerdown'); f.advance(149);
  assert.equal(f.nodes.length, 0, 'O467_R11_RING_150MS'); f.advance(150);
  assert.equal(f.nodes.length, 1, 'O467_R11_RING_150MS');
  assert.equal(f.calls.menu, 0, 'O467_R11_RING_150MS'); f.emit('pointercancel');
  assert.equal(f.nodes.length, 0, 'O467_R11_RING_CANCEL_REMOVES_PRESENTATION');
});
test('O467_R11_MOVE_CANCELS_HOLD: 8px remains eligible; 9px becomes one single tool gesture', () => {
  const exact = fixture(); exact.emit('pointerdown'); exact.emit('pointermove', 1, 8); exact.advance(500);
  assert.equal(exact.calls.menu, 1, 'O467_R11_MOVE_BOUNDARY'); exact.emit('pointerup', 1, 8);
  const f = fixture(); f.emit('pointerdown'); f.emit('pointermove', 1, 9); f.advance(500);
  assert.equal(f.calls.menu, 0, 'O467_R11_MOVE_CANCELS_HOLD');
  assert.equal(f.calls.begin, 1, 'O467_R11_MOVE_CANCELS_HOLD'); f.emit('pointerup', 1, 9);
  assert.equal(f.calls.end, 1, 'O467_R11_SINGLE_END_ONCE');
});
test('O467_R11_MULTI_CAMERA: ratio and midpoint preserve the captured camera anchor', () => {
  const f = fixture(); f.emit('pointerdown', 1, 0); f.emit('pointerdown', 2, 20);
  f.emit('pointermove', 2, 40); f.advance(500);
  assert.deepEqual(f.calls.cameras, [{zoom: 4, x: 8, y: 12}], 'O467_R11_MULTI_CAMERA');
  assert.equal(f.calls.menu + f.calls.begin + f.calls.end, 0, 'O467_R11_MULTI_NO_SINGLE');
});
test('O467_R11_MULTI_DRAIN_NO_SINGLE: the remaining finger cannot replay a single gesture', () => {
  const f = fixture(); f.emit('pointerdown', 1, 0); f.emit('pointerdown', 2, 20);
  f.emit('pointermove', 2, 40); f.emit('pointerup', 2, 40);
  f.emit('pointermove', 1, 50); f.emit('pointerup', 1, 50);
  assert.equal(f.calls.begin + f.calls.end, 0, 'O467_R11_MULTI_DRAIN_NO_SINGLE');
  assert.equal(f.calls.cameras.length, 1, 'O467_R11_MULTI_DRAIN_STOPS_CAMERA');
  f.emit('pointerdown', 3, 5, 0, {isPrimary: true}); f.emit('pointerup', 3, 5);
  assert.equal(f.calls.end, 1, 'O467_R11_NEXT_SEQUENCE_IS_INDEPENDENT');
});
test('O467_R11_STALE_SINGLE_CANCELLED: ownership changes retire a pending tool before pointerup', () => {
  const f = fixture(); f.emit('pointerdown'); f.emit('pointermove', 1, 9);
  assert.equal(f.calls.begin, 1, 'O467_R11_STALE_SINGLE_BEGINS'); f.stale(); f.emit('geometry-definition-changed');
  assert.equal(f.calls.cancel, 1, 'O467_R11_STALE_SINGLE_CANCELLED'); f.emit('pointerup', 1, 9);
  assert.equal(f.calls.end, 0, 'O467_R11_STALE_SINGLE_CANCELLED');
  assert.deepEqual(f.calls.errors, []);
});
