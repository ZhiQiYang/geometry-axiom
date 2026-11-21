// Actual vendored PDF.js + actual App sampling functions, without Chromium.
// Generate fixtures first with pdf_snap_close_fixtures.py. This is a diagnostic,
// not a replacement for browser/native evidence or the formal canvas gate.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {parseArgs} from 'node:util';
import * as pdfjs from '../../geometry-web/vendor/pdfjs-dist/build/pdf.mjs';

const {values} = parseArgs({options: {
  fixtures: {type: 'string'}, out: {type: 'string'},
  phase: {type: 'string', default: 'fixed'}, reference: {type: 'string'},
}});
assert(values.fixtures && values.out, '--fixtures DIR --out FILE are required');
assert(['baseline', 'fixed'].includes(values.phase), '--phase baseline|fixed');
const root = fileURLToPath(new URL('../../', import.meta.url));
const require = createRequire(import.meta.url);
const R = require('../../geometry-web/room-outline.js');
const PolyDraft = require('../../geometry-web/polydraft.js');
const hash = data => createHash('sha256').update(data).digest('hex');
const plain = data => JSON.parse(JSON.stringify(data, (_k, v) => ArrayBuffer.isView(v) ? Array.from(v) : v));
// Node 24 compatibility for standard intrinsics only. No parser/geometry stubs.
if (!Uint8Array.prototype.toHex) Object.defineProperty(Uint8Array.prototype, 'toHex', {
  value() { return Buffer.from(this.buffer, this.byteOffset, this.byteLength).toString('hex'); },
});
for (const C of [Map, WeakMap]) if (!C.prototype.getOrInsertComputed) {
  Object.defineProperty(C.prototype, 'getOrInsertComputed', {value(key, fn) {
    if (this.has(key)) return this.get(key);
    const value = fn(key); this.set(key, value); return value;
  }});
}
const app = fs.readFileSync(path.join(root, 'geometry-web/app.js'), 'utf8');
function between(start, end) {
  const a = app.indexOf(start), b = app.indexOf(end, a + start.length);
  assert(a >= 0 && b > a && app.indexOf(start, a + 1) < 0, 'App source anchor: ' + start);
  return app.slice(a, b);
}
const sampler = [
  between('function feGridStep() {', 'function feSyncGridSize() {'),
  between('function feUlCenter(ul) {', 'function feUlMmToImg(ul, mx, my) {'),
  between('function feDraftOpts() {', '/* fe.drag/fe.lenBuf'),
].join('\n');
const expected = [[600,1800],[3000,1800],[3000,800],[2200,800],[2200,200],[600,200]];
const originalBad = [[3000,1800],[3000,800],[2200,800],[2200,200],[500,200],[500,1800]];
const clicks = [[60,180],[300,180],[300,80],[220,80],[220,20],[60,20]];
function replay(features, snapOn, zoom, mmPerPx) {
  const page = {id: 'diagnostic', sourceId: 'fixture', page: 2, crop: null,
    x: 0, y: 0, rot: 0, imgW: 360, imgH: 220, mmPerPx, calibration: {knownMm: 2000}};
  const context = vm.createContext({
    fe: {zoom, draft: PolyDraft.createState()}, oc: {edit: {bid: 2}},
    PolyDraft, RoomOutline: R,
    $: id => { assert.equal(id, 'faceSnapToggle'); return {checked: snapOn}; },
    ReferenceWorkspace: {active: () => page, tracingFeatures: () => ({status: 'ready', features})},
  });
  vm.runInContext(sampler, context, {filename: 'actual-app-sampler.js'});
  const steps = [];
  for (const source of clicks) {
    const raw = context.feUlImgToMm(page, ...source);
    const sample = context.feDraftSample({x: raw[0], y: raw[1]});
    const next = PolyDraft.place(context.fe.draft, sample.point, sample.opts);
    assert.equal(next.error, null, 'App replay point must be legal');
    context.fe.draft = next.state;
    steps.push(plain({source, raw, target: sample.target ?? null,
      sampled: sample.point, effectiveGridMm: sample.opts.gridMm, draft: next.state.pts}));
  }
  const closed = plain(PolyDraft.tryClose(context.fe.draft, {existingEdges: []}));
  assert.equal(closed.ok, true, 'App replay closes a legal orthogonal ring');
  return {snapOn, zoom, mmPerPx, gridMm: context.feGridStep(), steps, closed,
    widthMm: Math.max(...closed.pts.map(p => p[0])) - Math.min(...closed.pts.map(p => p[0]))};
}
const output = {kind: 'node-parser-and-app-function-diagnostic', chromiumRun: false,
  phase: values.phase, node: process.version, pdfjsVersion: pdfjs.version,
  replayParametersAreNotOriginalCloudTelemetry: true, files: {}, cases: {}};
for (const name of ['geometry-web/room-outline.js', 'geometry-web/app.js', 'geometry-web/polydraft.js',
  'geometry-web/vendor/pdfjs-dist/build/pdf.mjs', 'geometry-web/vendor/pdfjs-dist/build/pdf.worker.mjs']) {
  const data = fs.readFileSync(path.join(root, name));
  output.files[name] = {bytes: data.length, sha256: hash(data)};
}
const manifest = JSON.parse(fs.readFileSync(path.join(values.fixtures, 'manifest.json'), 'utf8'));
for (const [name, fixture] of Object.entries(manifest)) {
  const data = fs.readFileSync(path.join(values.fixtures, name + '.pdf'));
  assert.equal(hash(data), fixture.sha256, 'fixture bytes: ' + name);
  const task = pdfjs.getDocument({data: new Uint8Array(data), useSystemFonts: true,
    disableFontFace: true, isEvalSupported: false});
  try {
    const doc = await task.promise;
    assert.equal(doc.numPages, 2, 'two-page reproduction');
    const page = await doc.getPage(2), viewport = page.getViewport({scale: 1});
    const list = await page.getOperatorList();
    const features = R.pdfSnapFeatures(list, pdfjs.OPS, viewport);
    const snap = point => R.nearestSnap(features, point, {map: p => p.map(n => n * 10), zoom: .09});
    output.cases[name] = plain({fixture, viewport: viewport.transform,
      operators: list.fnArray.map((id, i) => ({id,
        name: Object.entries(pdfjs.OPS).find(([, v]) => v === id)?.[0], args: list.argsArray[i]})),
      features, targets: [[600,1800],[600,200],[400,1800]].map(point => ({point, target: snap(point)}))});
    if (['malformed-h', 'valid-h', 'explicit-l'].includes(name)) {
      output.cases[name].replays = [];
      for (const zoom of [.09, .12, .2]) for (const mmPerPx of [10, 9.999999917520057]) {
        for (const snapOn of [true, false]) {
          const got = replay(features, snapOn, zoom, mmPerPx);
          assert.deepEqual(got.closed.pts, name === 'malformed-h' && snapOn ? originalBad : expected,
            'D06 exact ordered ring: ' + name + '/' + snapOn);
          output.cases[name].replays.push(got);
        }
      }
    }
  } finally { await task.destroy(); }
}
// Exclude only the independently known scale line from shape comparisons.
const shape = name => output.cases[name].features.segments.filter(s =>
  JSON.stringify([s.a, s.b]) !== '[[60,200],[260,200]]');
assert.equal(shape('malformed-h').length, 5, 'D06 original has five declared vertices');
assert.deepEqual([shape('malformed-h').at(-1).a, shape('malformed-h').at(-1).b],
  [[220,20],[60,180]], 'D06 original h closes diagonally; do not invent a vertex');
assert.equal(output.cases['malformed-h'].targets[0].target.distance, 0, 'D06 first vertex exists');
assert.equal(output.cases['malformed-h'].targets[1].target, null, 'D06 sixth vertex was never declared');
const geometry = name => shape(name).map(s => [s.a, s.b]);
assert.equal(shape('valid-h').length, 6);
for (const name of ['explicit-l', 'implicit-s', 'implicit-b', 'implicit-b-star', 'double-h', 'h-then-s']) {
  assert.deepEqual(geometry(name), geometry('valid-h'), name + ': same six source segments');
  assert.deepEqual(output.cases[name].targets[1].target.point, [600,200], name + ': last endpoint');
}
for (const name of ['curved-v-h', 'curved-y-h', 'straight-v-h', 'straight-y-h']) {
  assert.equal(shape(name).length, 0, name + ': declared curves remain excluded');
}
assert.equal(shape('rectangle-re').length, 4);
for (const name of ['h-then-line', 'h-h-then-line', 'curved-h-then-line']) {
  const target = output.cases[name].targets[2].target;
  if (values.phase === 'baseline') assert.equal(target, null, 'existing close-current-point gap: ' + name);
  else {
    assert.deepEqual(target?.point, [400,1800], 'P432_CLOSE_PATH_CONTINUATION: ' + name);
    const segment = shape(name).at(-1);
    assert.deepEqual([segment.a, segment.b, segment.closed], [[60,180],[40,180],false],
      'P432_CLOSE_PATH_OPEN_CONTINUATION: ' + name);
  }
}
if (values.reference) {
  const baseline = JSON.parse(fs.readFileSync(values.reference, 'utf8'));
  for (const name of Object.keys(manifest)) {
    if (['h-then-line', 'h-h-then-line', 'curved-h-then-line'].includes(name)) continue;
    assert.deepEqual(output.cases[name].features, baseline.cases[name].features,
      name + ': unchanged complete a/b/closed/path/id');
  }
  output.unchangedCasesCompared = Object.keys(manifest).length - 3;
}
output.assertions = 'passed';
fs.mkdirSync(path.dirname(path.resolve(values.out)), {recursive: true});
fs.writeFileSync(values.out, JSON.stringify(output, null, 2) + '\n');
console.log(JSON.stringify({phase: values.phase, cases: Object.keys(output.cases).length,
  appFunctionReplays: 36, chromiumRun: false, assertions: output.assertions, output: values.out}));
