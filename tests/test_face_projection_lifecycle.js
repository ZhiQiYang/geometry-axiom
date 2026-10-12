'use strict';
// Execute the shipped FaceProjection closure. The finite DOM models queued
// native close delivery; pointer, keyboard and browser task ordering need CDP.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(process.env.GEOMETRY_PROJECTION_SOURCE ||
  path.join(__dirname, '../geometry-web/app.js'), 'utf8');
const start = source.indexOf('window.FaceProjection = (() => {');
const end = source.indexOf('\n})();', start);
assert.ok(start >= 0 && end > start, 'production FaceProjection closure exists');
const projectionSource = source.slice(start, end + '\n})();'.length);
const plain = value => JSON.parse(JSON.stringify(value));
const definition = view => ({kind: 'space-boundary-plan', view, region: 'interior', wallSide: 'outside'});

function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return {promise, resolve};
}

function harness() {
  const elements = new Map(), queuedCloses = [], definitions = new Map(), writes = [], calls = [];
  const pendingReads = [], notices = [], windowListeners = new Map();
  let contextId = 'original-project';
  const surfaces = [1, 2].map(id => ({id, boundary: id, origin: [0, 0, 2500], u: [1, 0, 0], v: [0, 1, 0]}));
  const loops = [{verts: [[0, 0], [4000, 0], [4000, 3000], [0, 3000]]}];
  class Element {
    constructor(tag = 'div') {
      this.tagName = tag.toUpperCase(); this.listeners = new Map(); this.open = false;
      this.value = ''; this.checked = false; this.disabled = false; this.hidden = false;
      this.textContent = ''; this.classList = {toggle() {}};
    }
    set innerHTML(text) {
      this.html = text;
      for (const match of text.matchAll(/<([a-z]+)[^>]*\bid="([^"]+)"/g)) {
        const item = new Element(match[1]); item.id = match[2]; elements.set(item.id, item);
      }
      if (this.tagName === 'SELECT') this.value = /<option value="([^"]*)"/.exec(text)?.[1] || '';
    }
    get innerHTML() { return this.html || ''; }
    setAttribute() {}
    addEventListener(type, listener) {
      const list = this.listeners.get(type) || []; list.push(listener); this.listeners.set(type, list);
    }
    dispatch(type) {
      const event = {type, target: this, defaultPrevented: false, preventDefault() { this.defaultPrevented = true; }};
      for (const listener of this.listeners.get(type) || []) listener(event);
      return event;
    }
    showModal() { this.open = true; }
    close() {
      if (!this.open) return;
      this.open = false;
      // HTMLDialogElement.close() closes now and queues the close event later.
      queuedCloses.push(() => this.dispatch('close'));
    }
    escape() { if (!this.dispatch('cancel').defaultPrevented) this.close(); }
  }
  const document = {
    getElementById: id => elements.get(id), createElement: tag => new Element(tag), addEventListener() {},
    body: {appendChild: element => elements.set(element.id, element)},
  };
  const history = {frame: {ids: new Map([[1, 'face-one'], [2, 'face-two']])}, undo: []};
  const reference = {
    context: () => ({id: contextId}), history,
    getFaceProjection: (bid, pid) => definitions.get(`${bid}/${pid}`) || null,
    setFaceProjection: (bid, pid, value) => {
      writes.push({bid, pid, value: plain(value)});
      if (value) definitions.set(`${bid}/${pid}`, plain(value)); else definitions.delete(`${bid}/${pid}`);
    },
  };
  const window = {addEventListener: (type, listener) => windowListeners.set(type, listener)};
  const sandbox = {
    window, document, ReferenceWorkspace: reference, oc: {surfs: surfaces},
    toast: message => notices.push(message),
    api: async command => {
      calls.push(command);
      const hold = pendingReads.find(item => item.command === command && !item.used);
      if (hold) { hold.used = true; hold.entered.resolve(); await hold.release.promise; }
      if (command === 'surfaces') return {ok: true, surfaces: plain(surfaces)};
      if (/^boundary [12]$/.test(command)) return {ok: true, loops: plain(loops)};
      throw Error(`unexpected source read: ${command}`);
    },
  };
  vm.runInNewContext(projectionSource, sandbox, {filename: 'FaceProjection.production.js'});
  const element = id => { assert.ok(elements.has(id), `element ${id} exists`); return elements.get(id); };
  return {
    open: (id = 1) => window.FaceProjection.open(id, id), element, writes, calls, notices,
    get queuedCloseCount() { return queuedCloses.length; },
    flushClose() { assert.ok(queuedCloses.length > 0, 'a real close invocation queued an event'); queuedCloses.shift()(); },
    flushAllCloses() { while (queuedCloses.length) queuedCloses.shift()(); },
    click(id) { const control = element(id); assert.equal(control.disabled, false, `${id} is enabled`); return control.onclick(); },
    change(id, value) { const control = element(id); assert.equal(control.disabled, false, `${id} is enabled`); control.value = value; control.onchange(); },
    selectPlan(view) {
      this.change('fpPurpose', 'space-boundary-plan'); this.change('fpView', view);
      element('fpInterior').checked = true; element('fpInterior').onchange();
    },
    saved(id = 1) { return plain(reference.getFaceProjection(id, id)); },
    seed(view) { definitions.set('1/1', definition(view)); },
    escape() { element('fpDialog').escape(); },
    replaceProject() { contextId = 'replacement-project'; },
    changeSource() { loops[0].verts[1][0] = 4100; },
    hold(command = 'surfaces') {
      const item = {command, entered: deferred(), release: deferred(), used: false}; pendingReads.push(item);
      return {entered: item.entered.promise, release: () => item.release.resolve()};
    },
  };
}

async function closeFirst(h, action) {
  if (action === 'clear') h.seed('bottom');
  await h.open();
  if (action === 'save') { h.selectPlan('bottom'); await h.click('fpApply'); }
  else if (action === 'clear') { h.change('fpPurpose', 'general'); await h.click('fpApply'); }
  else { h.selectPlan('bottom'); await h.click('fpCancel'); }
  assert.equal(h.element('fpDialog').open, false);
  assert.equal(h.queuedCloseCount, 1);
  assert.deepEqual(h.saved(), action === 'save' ? definition('bottom') : null);
}

for (const action of ['cancel', 'save', 'clear']) {
  for (const arrival of ['during-source-read', 'after-reopen']) {
    test(`old ${action} close delivered ${arrival} cannot retire the next projection session`, async () => {
      const h = harness(); await closeFirst(h, action);
      if (arrival === 'during-source-read') {
        const hold = h.hold(), opening = h.open(); await hold.entered;
        assert.equal(h.element('fpDialog').open, false, 'new open is still waiting on its real source port');
        h.flushClose(); hold.release(); await opening;
      } else { await h.open(); h.flushClose(); }
      assert.equal(h.element('fpDialog').open, true, 'the newer open survives the older close');
      h.selectPlan('top');
      assert.equal(h.element('fpApply').disabled, false, 'the newer session remains editable');
      await h.click('fpApply');
      assert.equal(h.element('fpDialog').open, false, 'the newer apply closes its own dialog');
      assert.deepEqual(h.saved(), definition('top'), 'the newer definition is actually committed');
      h.flushAllCloses();
    });
  }
}

for (const action of ['cancel', 'close-button', 'escape']) {
  test(`${action} discards only the uncommitted projection draft`, async () => {
    const h = harness(); h.seed('top'); await h.open(); h.selectPlan('bottom');
    if (action === 'escape') h.escape(); else await h.click(action === 'cancel' ? 'fpCancel' : 'fpClose');
    assert.equal(h.element('fpDialog').open, false); h.flushAllCloses();
    assert.deepEqual(h.saved(), definition('top')); assert.equal(h.writes.length, 0);
    await h.open(); assert.equal(h.element('fpView').value, 'top');
  });
}

test('Escape invalidates an in-flight apply before its delayed close event is delivered', async () => {
  const h = harness(); h.seed('top'); await h.open(); h.selectPlan('bottom');
  const hold = h.hold(), applying = h.click('fpApply'); await hold.entered;
  h.escape(); assert.equal(h.element('fpDialog').open, false); assert.equal(h.queuedCloseCount, 1);
  hold.release(); await applying;
  assert.deepEqual(h.saved(), definition('top'), 'a canceled source reply cannot commit the draft');
  assert.equal(h.writes.length, 0); h.flushAllCloses();
});

test('a newer open rejects the previous open source reply', async () => {
  const h = harness(), hold = h.hold(), first = h.open(1); await hold.entered;
  await h.open(2); hold.release(); await first;
  assert.match(h.element('fpTitle').textContent, /^面 2 /);
  h.selectPlan('bottom'); await h.click('fpApply');
  assert.deepEqual(h.saved(2), definition('bottom')); assert.equal(h.saved(1), null);
});

test('closing the old visible session cannot cancel a newer pending open', async () => {
  const h = harness(); await h.open(1);
  const hold = h.hold(), opening = h.open(2); await hold.entered;
  await h.click('fpCancel'); h.flushClose(); hold.release(); await opening;
  assert.equal(h.element('fpDialog').open, true, 'only the closing generation is retired');
  assert.match(h.element('fpTitle').textContent, /^面 2 /);
  h.selectPlan('bottom'); await h.click('fpApply');
  assert.deepEqual(h.saved(2), definition('bottom')); assert.equal(h.saved(1), null);
});

test('a replaced project rejects an old open source reply', async () => {
  const h = harness(), hold = h.hold(), opening = h.open(); await hold.entered;
  h.replaceProject(); hold.release(); await opening;
  assert.equal(h.element('fpDialog').open, false); assert.equal(h.writes.length, 0);
});

test('a changed source still rejects apply and keeps the saved definition', async () => {
  const h = harness(); h.seed('top'); await h.open(); h.selectPlan('bottom');
  const hold = h.hold(), applying = h.click('fpApply'); await hold.entered;
  h.changeSource(); hold.release(); await applying;
  assert.deepEqual(h.saved(), definition('top')); assert.equal(h.writes.length, 0);
  assert.equal(h.element('fpDialog').open, true); assert.equal(h.element('fpApply').disabled, true);
  assert.match(h.element('fpMessage').textContent, /來源面、放置或定義已變更/);
});
