/* Deterministic case-reader regressions. Synthetic data only; no network or deps.
 * This small DOM double checks controller behavior, not browser layout/decoding.
 * Real browser acceptance lives in geometry-web/documents_browser_test.js. */
'use strict';
const assert = require('node:assert/strict');

class Element {
  constructor(tag) {
    this.tagName = tag;
    this.children = [];
    this.events = {};
    this.attributes = {};
    this.style = {};
    this.value = '';
    this.disabled = false;
    this.clientWidth = 400;
    this.clientHeight = 300;
    this.classList = { toggle() {}, add() {}, remove() {} };
  }
  append(...items) {
    for (const item of items) { item.parent = this; this.children.push(item); }
  }
  prepend(...items) {
    for (const item of items) item.parent = this;
    this.children.unshift(...items);
  }
  replaceChildren(...items) { this.text = ''; this.children = []; this.append(...items); }
  set textContent(value) { this.text = String(value); this.children = []; }
  get textContent() { return (this.text || '') + this.children.map(x => x.textContent).join(''); }
  setAttribute(key, value) { this.attributes[key] = value; }
  removeAttribute(key) { delete this.attributes[key]; }
  addEventListener(name, fn) { (this.events[name] ||= []).push(fn); }
  async emit(name) { for (const fn of this.events[name] || []) await fn({}); }
  click() {
    if (this.disabled) return Promise.resolve();
    if (this.tagName === 'a' && this.download) downloaded = blobs.get(this.href);
    return this.emit('click');
  }
  remove() {
    if (this.parent) this.parent.children = this.parent.children.filter(x => x !== this);
  }
}

const globals = {
  document: global.document, addEventListener: global.addEventListener,
  fetch: global.fetch, createObjectURL: URL.createObjectURL, revokeObjectURL: URL.revokeObjectURL
};
const events = {}, blobs = new Map();
let downloaded = null, blobSerial = 0;
global.document = { createElement: tag => new Element(tag) };
global.addEventListener = (name, fn) => { events[name] = fn; };
global.fetch = () => { throw new Error('Case reader must not fetch remote data'); };
URL.createObjectURL = blob => {
  const url = 'blob:synthetic-' + (++blobSerial); blobs.set(url, blob); return url;
};
URL.revokeObjectURL = url => { blobs.delete(url); };

const Cases = require('../geometry-web/document-cases.js'), h = Cases.helpers;
const manifest = [
  {
    schema_version: '1.0', id: 'C1', title: 'Synthetic one', assets: [{
      id: 'A1', path: 'a.pdf', view_path: 'a.png', page_previews: ['a.png', 'b.png'],
      kind: 'plan', caption: 'Synthetic asset', source_pdf_path: 'source.pdf',
      source_page_number: 28, transform: 'Synthetic page extraction', view_transform: 'Synthetic PNG render',
      source_url: 'https://example.invalid/source', figure_url: 'https://example.invalid/figure',
      source_page_url: 'https://example.invalid/catalog', license_url: 'https://example.invalid/license',
      license_evidence_url: 'https://example.invalid/evidence', license_evidence: 'Synthetic license evidence',
      catalog_description: '<script>literal description</script>', copyright_credit: 'Synthetic author'
    }]
  },
  { schema_version: '1.0', id: 'C2', title: 'Synthetic two', assets: [] }
];
const clone = () => JSON.parse(JSON.stringify(manifest));
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/lXkAAAAASUVORK5CYII=', 'base64');
function file(path, text = '') {
  return {
    name: path.split('/').pop(), webkitRelativePath: path, size: Buffer.byteLength(text),
    text: async () => text, arrayBuffer: async () => Uint8Array.from(png).buffer
  };
}
const fixture = m => [
  file('synthetic/case_index.json', JSON.stringify(m)), file('synthetic/a.pdf', 'synthetic PDF'),
  file('synthetic/source.pdf', 'synthetic full PDF'), file('synthetic/a.png', 'PNG'), file('synthetic/b.png', 'PNG')
];
const nodes = node => [node, ...node.children.flatMap(nodes)];
function pick(container, predicate) {
  const result = nodes(container).find(predicate);
  assert.ok(result, 'Expected synthetic DOM control');
  return result;
}
const byClass = (container, cls) => pick(container, n => n.className === cls);
const button = (container, text) => pick(container, n => n.tagName === 'button' && n.textContent === text);
const noteValue = container => byClass(container, 'doc-case-note-input').value;
async function setNote(container, text) {
  const input = byClass(container, 'doc-case-note-input'); input.value = text; await input.emit('input');
}
async function selectCase(container, id) {
  await pick(container, n => n.className?.includes('doc-case-list-item') && n.children[0]?.textContent === id).click();
}
async function exported(container) {
  downloaded = null;
  await button(container, '匯出筆記 JSON').click();
  assert.ok(downloaded instanceof Blob, 'Export produces a local JSON Blob');
  return downloaded.text();
}
async function settle() { await new Promise(resolve => setImmediate(resolve)); }

function testHelpers() {
  assert.equal(h.validateManifest(manifest).assetCount, 1);
  for (const value of [undefined, '2.0', 1]) {
    const m = clone(); m[0].schema_version = value;
    assert.throws(() => h.validateManifest(m), /schema_version/);
  }
  assert.throws(() => h.validateManifest({ schema_version: '2.0', cases: manifest }), /schema_version/);
  assert.equal(h.validateManifest({ schema_version: '1.0', cases: manifest }).cases.length, 2);
  for (const field of ['path', 'thumbnail', 'source_pdf_path', 'view_path']) {
    const m = clone(); m[0].assets[0][field] = '../bad'; assert.throws(() => h.validateManifest(m));
  }
  for (const field of ['source_url', 'figure_url', 'source_page_url', 'license_url', 'license_evidence_url']) {
    const m = clone(); m[0].assets[0][field] = 'javascript:alert(1)'; assert.throws(() => h.validateManifest(m));
  }
  for (const previews of [['../bad'], ['a.png', 'a.png'], ['a.png', 'A.png'], ['https://example.invalid/a.png'], 'a.png']) {
    const m = clone(); m[0].assets[0].page_previews = previews; assert.throws(() => h.validateManifest(m));
  }
  assert.throws(() => h.safeJSON(JSON.parse('{"__proto__":{"polluted":true}}')));
  assert.equal({}.polluted, undefined);
  const nested = [
    file('bundle/case_index.json', '[]'), file('bundle/snapshots/v1/case_index.json', '[]'),
    file('bundle/snapshots/v2/case_index.json', '[]')
  ];
  assert.equal(h.indexFiles(nested).manifest, nested[0]);
  assert.equal(h.indexFiles(nested).name, 'bundle');
  assert.equal(h.indexFiles([nested[1]]).name, 'v1');
  assert.throws(() => h.indexFiles(nested.slice(1)), /case_index/);
  assert.throws(() => h.indexFiles([file('a/case_index.json'), file('b/case_index.json')]));
  assert.throws(() => h.indexFiles([file('a/case_index.json'), file('a/CASE_INDEX.JSON')]));
  assert.throws(() => h.indexFiles([file('a/not-a-manifest.json')]));
  assert.equal(h.imageDimensions(Uint8Array.from(png)).width, 1);
  console.log('PASS case helpers: schema, safe metadata paths/URLs, previews, nested manifests');
}

async function testController() {
  let opened = null;
  const container = new Element('div'), api = Cases.mount(container, { onOpenFile: f => { opened = f; } });
  const files = fixture(manifest);
  assert.equal(await api.importFiles(files), true); await settle();
  for (const text of ['Synthetic page extraction', 'Synthetic PNG render', '<script>literal description</script>', 'Synthetic author', 'Synthetic license evidence', '28']) {
    assert.ok(container.textContent.includes(text), 'Safe text metadata: ' + text);
  }
  assert.equal(nodes(container).filter(n => n.tagName === 'script').length, 0);
  const links = nodes(container).filter(n => n.tagName === 'a');
  for (const suffix of ['license', 'evidence']) {
    const link = links.find(n => n.href === 'https://example.invalid/' + suffix);
    assert.ok(link); assert.equal(link.rel, 'noopener noreferrer'); assert.equal(link.referrerPolicy, 'no-referrer');
  }
  await button(container, '開啟素材 PDF').click(); assert.equal(opened, files[1]);
  await button(container, '開啟完整來源 PDF').click(); assert.equal(opened, files[2]);
  const page = byClass(container, 'doc-case-page'); page.value = 'b.png'; await page.emit('change'); await settle();
  assert.equal(byClass(container, 'doc-case-page').value, 'b.png');
  assert.ok(container.textContent.includes('b.png'));
  await setNote(container, 'Preserve synthetic notes');
  let prevented = false;
  events.beforeunload({ preventDefault() { prevented = true; } }); assert.equal(prevented, true);
  await selectCase(container, 'C2'); assert.equal(noteValue(container), '');
  await selectCase(container, 'C1'); assert.equal(noteValue(container), 'Preserve synthetic notes');
  const text = await exported(container), payload = JSON.parse(text);
  assert.equal(payload.notes[0].text, 'Preserve synthetic notes');
  await setNote(container, ''); assert.equal(await api.importNotes(file('notes.json', text)), true);
  assert.equal(noteValue(container), 'Preserve synthetic notes');
  const bad = { ...payload, notes: [{ ...payload.notes[0], text: 'Conflicting text' }] };
  assert.equal(await api.importNotes(file('notes.json', JSON.stringify(bad))), false);
  assert.equal(noteValue(container), 'Preserve synthetic notes');
  for (const notes of [[payload.notes[0], payload.notes[0]], [{ caseId: 'unknown', text: 'x' }], [{ caseId: 'C1', text: 'x'.repeat(20001) }]]) {
    assert.equal(await api.importNotes(file('notes.json', JSON.stringify({ ...payload, notes }))), false);
    assert.equal(noteValue(container), 'Preserve synthetic notes');
  }
  assert.equal(await api.importNotes(file('notes.json', JSON.stringify({ ...payload, bundleId: 'wrong-bundle' }))), false);
  const oversized = file('notes.json', ' '.repeat(h.limits.notesBytes + 1)); oversized.size = 0;
  assert.equal(await api.importNotes(oversized), false, 'Actual UTF-8 size checked independently of file.size');
  await setNote(container, 'x'.repeat(20001)); assert.equal(noteValue(container), 'Preserve synthetic notes');
  const other = clone(); other[0].title = 'Different synthetic bundle';
  assert.equal(await api.importFiles(fixture(other)), true); assert.equal(noteValue(container), '');
  await setNote(container, 'Other bundle note');
  assert.equal(await api.importFiles(files), true); assert.equal(noteValue(container), 'Preserve synthetic notes');
  assert.equal(await api.importFiles([file('synthetic/case_index.json', '{}')]), false);
  assert.equal(noteValue(container), 'Preserve synthetic notes');
  api.destroy();
  const remounted = Cases.mount(container);
  assert.equal(await remounted.importFiles(files), true); assert.equal(noteValue(container), 'Preserve synthetic notes');
  assert.equal(await remounted.importFiles(fixture(other)), true); assert.equal(noteValue(container), 'Other bundle note');
  remounted.destroy();
  console.log('PASS case controller: PDF callbacks, page selection, safe text/links, note roundtrip/rejection/navigation/remount');
}

async function testNotesBudget() {
  const container = new Element('div'), api = Cases.mount(container);
  const cases = Array.from({ length: 36 }, (_, i) => ({ schema_version: '1.0', id: 'B' + String(i).padStart(2, '0'), title: 'Synthetic budget case ' + i, assets: [] }));
  assert.equal(await api.importFiles(fixture(cases)), true);
  const identity = JSON.parse(await exported(container));
  const noteMap = new Map(cases.slice(0, 34).map(c => [c.id, { text: '字'.repeat(20000), updatedAt: '2026-01-01T00:00:00.000Z' }]));
  const bundle = { key: identity.bundleId, name: identity.bundleName };
  const large = h.serializeNotes(bundle, noteMap);
  assert.ok(Buffer.byteLength(large) <= h.limits.notesBytes);
  assert.equal(await api.importNotes(file('large-notes.json', large)), true);
  const roundtrip = await exported(container);
  assert.ok(Buffer.byteLength(roundtrip) <= h.limits.notesBytes);
  assert.deepEqual(JSON.parse(roundtrip).notes, JSON.parse(large).notes);
  assert.equal(await api.importNotes(file('large-notes.json', roundtrip)), true);
  const overflow = new Map(noteMap); overflow.set('B34', { text: '字'.repeat(20000), updatedAt: '2026-01-01T00:00:00.000Z' });
  assert.throws(() => h.serializeNotes(bundle, overflow), /2 MB/);
  const incoming = h.serializeNotes(bundle, new Map([['B34', overflow.get('B34')]]));
  assert.equal(await api.importNotes(file('more-notes.json', incoming)), false, 'Oversize merge is rejected atomically');
  assert.equal(noteValue(container), '字'.repeat(20000));
  await selectCase(container, 'B34'); assert.equal(noteValue(container), '');
  await setNote(container, '字'.repeat(20000)); assert.equal(noteValue(container), '', 'Oversize edit restores previous value');
  assert.deepEqual(JSON.parse(await exported(container)).notes, JSON.parse(large).notes);
  let prevented = false;
  events.beforeunload({ preventDefault() { prevented = true; } });
  assert.equal(prevented, true, 'Download click does not silently remove the unsaved-note warning');
  api.destroy();
  console.log('PASS notes budget: 34 full CJK notes roundtrip; 35th edit/merge rejected without data loss');
}

(async () => {
  testHelpers(); await testController(); await testNotesBudget();
  console.log('Document case synthetic regressions: passed');
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => {
  Cases.destroy();
  global.document = globals.document; global.addEventListener = globals.addEventListener; global.fetch = globals.fetch;
  URL.createObjectURL = globals.createObjectURL; URL.revokeObjectURL = globals.revokeObjectURL;
});
