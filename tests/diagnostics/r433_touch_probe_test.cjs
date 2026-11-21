/* R433 T3 recorder contract. Node VM and synthetic Event-shaped objects only.
 * No Chrome, trusted input, hit testing, product success or CDP 0/1/0 is claimed.
 * Load the actual two observer functions; never substitute a product handler.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');
const {performance} = require('node:perf_hooks');

const sourcePath = path.resolve(process.env.R433_PROBE_SOURCE ||
  path.join(__dirname, '../../geometry-web/canvas_touch_test.js'));
const source = fs.readFileSync(sourcePath, 'utf8');
const start = source.indexOf('function installEarlyObserver() {');
const end = source.indexOf('\nmodule.exports = async function canvasTouch(');
assert.ok(start >= 0 && end > start, 'R433_PROBE_REAL_FUNCTION_BOUNDARIES');

function fixture({ownerAvailable = true, productListener = () => {}} = {}) {
  const entries = new Map();
  const window = {
    fetch: async () => ({ok:true}),
    addEventListener(type, fn) {
      if (!entries.has(type)) entries.set(type, []);
      entries.get(type).push(fn);
    },
    removeEventListener(type, fn) {
      entries.set(type, (entries.get(type) || []).filter(item => item !== fn));
    },
  };
  const document = {body:{}, getElementById() { return null; }, querySelector() { return null; }};
  const context = {window, document, performance, URL, location:{href:'http://example.invalid/'},
    MutationObserver: class { observe() {} disconnect() {} }};
  if (ownerAvailable) {
    const identity = {};
    context.objectTouchOwner = () => ({frame:identity, revision:4, viewport:'0,0,390,722'});
  }
  vm.createContext(context);
  vm.runInContext(source.slice(start, end), context, {filename:sourcePath});
  vm.runInContext('installEarlyObserver()', context);
  window.addEventListener('click', productListener);
  vm.runInContext('installProbe()', context);
  function dispatch(type, values = {}) {
    let stopped = false;
    const event = {type, isTrusted:false, timeStamp:1, target:window, defaultPrevented:false,
      preventDefault() { this.defaultPrevented = true; },
      stopImmediatePropagation() { stopped = true; }, ...values};
    for (const listener of [...(entries.get(type) || [])]) {
      listener(event);
      if (stopped) break;
    }
    return event;
  }
  function snapshot() {
    assert.equal(typeof window.__p1162.snapshot, 'function', 'R433_PROBE_FINAL_SNAPSHOT_AVAILABLE');
    return window.__p1162.snapshot();
  }
  return {window, document, entries, dispatch, snapshot};
}

test('final snapshot observes consumption after the early listener', () => {
  const f = fixture({productListener: event => { event.preventDefault(); event.stopImmediatePropagation(); }});
  const event = f.dispatch('click', {pointerType:'touch', pointerId:5});
  const [row] = f.snapshot();
  assert.equal(row.trusted, false, 'R433_PROBE_DOES_NOT_INVENT_TRUST');
  assert.equal(row.earlyDefaultPrevented, false, 'R433_PROBE_EARLY_STATE_SEPARATE');
  assert.equal(row.defaultPrevented, true, 'R433_PROBE_FINAL_PREVENT_DEFAULT');
  assert.equal(row.lateWindowCapture, false, 'R433_PROBE_STOPPED_EVENT_STAYS_EARLY');
  assert.equal(event.defaultPrevented, true);
  f.window.__p1162.cleanup();
});

test('late observation matches Event identity, not reused ID or timestamp', () => {
  const f = fixture({productListener: event => {
    if (event.consume) { event.preventDefault(); event.stopImmediatePropagation(); }
  }});
  f.dispatch('click', {pointerId:5, consume:true});
  f.dispatch('click', {pointerId:5, consume:false});
  const rows = f.snapshot();
  assert.equal(rows.length, 2);
  assert.equal(rows[0].defaultPrevented, true);
  assert.equal(rows[0].lateWindowCapture, false, 'R433_PROBE_IDENTITY_CONSUMED');
  assert.equal(rows[1].defaultPrevented, false);
  assert.equal(rows[1].lateWindowCapture, true, 'R433_PROBE_IDENTITY_UNCONSUMED');
  f.window.__p1162.cleanup();
});

test('observer remains passive and records native cancellation candidates', () => {
  const f = fixture();
  for (const type of ['scroll','resize','lostpointercapture']) {
    const event = f.dispatch(type, {isPrimary:true});
    assert.equal(event.defaultPrevented, false, 'R433_PROBE_NEVER_CANCELS_INPUT');
  }
  const rows = f.snapshot();
  assert.equal(rows.length, 3, 'R433_PROBE_RECORDS_CANCELLATION_CANDIDATES');
  for (const row of rows) {
    assert.equal(row.lateWindowCapture, true);
    assert.equal(row.isPrimary, true);
  }
  f.window.__p1162.cleanup();
});

test('clear and cleanup release old Event references and later listeners', () => {
  const f = fixture();
  const original = f.window.__p1162Early;
  const event = f.dispatch('click');
  f.snapshot();
  const row = original.eventRows.get(event);
  assert.ok(row);
  f.window.__p1162.clearGesture();
  assert.equal(original.eventRows.has(event), false, 'R433_PROBE_CLEAR_EVENT_IDENTITY');
  assert.equal(original.eventRefs.has(row), false, 'R433_PROBE_CLEAR_EVENT_REFERENCE');
  assert.equal(f.snapshot().length, 0);
  f.dispatch('click');
  const count = f.entries.get('click').length;
  f.window.__p1162.cleanup();
  assert.equal(f.entries.get('click').length, count - 1, 'R433_PROBE_REMOVES_LATE_LISTENER');
  assert.equal(f.window.__p1162, undefined);
  f.dispatch('click');
  assert.equal(original.events.length, 0, 'R433_PROBE_DISABLED_AFTER_CLEANUP');
});

test('the exact pre-product baseline can still report its normal assertion red', () => {
  const f = fixture({ownerAvailable:false});
  assert.equal(typeof f.window.__p1162.owner, 'function', 'R433_PROBE_OWNER_OBSERVATION_AVAILABLE');
  assert.equal(f.window.__p1162.owner(), null, 'R433_PROBE_PREPRODUCT_OWNER_IS_ABSENT');
  f.window.__p1162.cleanup();
});

test('owner object identities remain stable across observation reads', () => {
  const f = fixture();
  assert.equal(typeof f.window.__p1162.owner, 'function', 'R433_PROBE_OWNER_OBSERVATION_AVAILABLE');
  const first = f.window.__p1162.owner(), second = f.window.__p1162.owner();
  assert.equal(first.frame.identity, second.frame.identity);
  assert.equal(first.revision, second.revision);
  assert.equal(first.viewport, second.viewport);
  f.window.__p1162.cleanup();
});

test('point preparation completes its frame barrier before measuring the input', async () => {
  const pointStart = source.indexOf('  async function point(selector) {');
  const pointEnd = source.indexOf('  const blankTouchTarget =', pointStart);
  assert.ok(pointStart >= 0 && pointEnd > pointStart, 'R433_PROBE_REAL_POINT_FUNCTION');
  let scrolling = false, framesCompleted = 0;
  const context = {
    read: async expression => {
      if (expression.includes('scrollIntoView')) { scrolling = true; return; }
      assert.equal(scrolling, false, 'R433_POINT_MEASURE_AFTER_FRAME_BARRIER');
      return {x:137.2,y:275.2,width:260,height:180,disabled:false};
    },
    frames: async () => { await Promise.resolve(); scrolling = false; framesCompleted++; },
    check: (name, passed) => assert.equal(passed, true, name),
  };
  vm.createContext(context);
  vm.runInContext(source.slice(pointStart, pointEnd), context, {filename:sourcePath});
  const result = await context.point('.ocard');
  assert.equal(framesCompleted, 1, 'R433_POINT_PREPARATION_WAITS_EXISTING_FRAMES_ONCE');
  assert.equal(result.x, 137.2);
});
