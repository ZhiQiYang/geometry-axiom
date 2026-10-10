'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const app = fs.readFileSync(process.env.GEOMETRY_TEST_HISTORY_APP || path.join(__dirname, '../geometry-web/app.js'), 'utf8').replace(/\r\n/g, '\n');
const start = app.indexOf('async function doUndoRedo(verb) {');
const end = app.indexOf('\n$("btnUndo").addEventListener', start);
assert(start >= 0 && end > start, 'Actual application history handler is required');
const handler = app.slice(start, end);
function deferred() { let resolve; const promise = new Promise(r => { resolve = r; }); return {promise, resolve}; }
function harness(apiResult = async () => ({ok:true}), repaint = async () => {}) {
  const classes = new Set(), calls = [], statuses = [], toasts = [];
  const context = {oc:{busy:false,on:true,focus:null}, document:{body:{classList:{add:k=>classes.add(k),remove:k=>classes.delete(k)}}},
    ReferenceWorkspace:{context:()=>({id:'project-a'}),historyActionLabel:()=>null},
    api:async cmd=>{calls.push(cmd);return apiResult(cmd);},clearCanvasSelections:()=>{},
    renderObjects:repaint,render:repaint,refreshSurfaces:async()=>{},
    setStatus:s=>statuses.push(s),toast:s=>toasts.push(s)};
  vm.createContext(context);vm.runInContext(handler, context);
  return {context,classes,calls,statuses,toasts,run:verb=>context.doUndoRedo(verb)};
}
test('a second history action cannot overtake a deferred native result', async () => {
  const response = deferred(), h = harness(() => response.promise), first = h.run('undo');
  assert.equal(h.context.oc.busy, true);assert(h.classes.has('oc-busy'));
  await h.run('redo');assert.deepEqual(h.calls, ['line undo']);assert.equal(h.toasts.length, 1);
  response.resolve({ok:true});await first;
  assert.equal(h.context.oc.busy, false);assert(!h.classes.has('oc-busy'));assert.equal(h.statuses.length, 1);
  await h.run('redo');assert.deepEqual(h.calls, ['line undo','line redo']);
});
test('the history action stays busy until the actual repaint finishes', async () => {
  const painting = deferred(), h = harness(undefined, () => painting.promise), first = h.run('redo');
  await Promise.resolve();await Promise.resolve();
  assert.equal(h.context.oc.busy, true);assert(h.classes.has('oc-busy'));assert.equal(h.statuses.length, 0);
  await h.run('undo');assert.deepEqual(h.calls, ['line redo']);
  painting.resolve();await first;
  assert.equal(h.context.oc.busy, false);assert(!h.classes.has('oc-busy'));assert.equal(h.statuses.length, 1);
});
test('a native refusal releases the gate without reporting success', async () => {
  const h = harness(async () => ({ok:false,error:'native refusal'}));
  await h.run('undo');assert.equal(h.context.oc.busy, false);assert(!h.classes.has('oc-busy'));
  assert.equal(h.statuses[0], '✗ native refusal');await h.run('redo');assert.equal(h.calls.length, 2);
});
test('native and repaint exceptions both release the gate', async () => {
  for (const h of [harness(async()=>{throw Error('native interrupted');}), harness(undefined,async()=>{throw Error('paint interrupted');})]) {
    await assert.rejects(h.run('undo'), /interrupted/);
    assert.equal(h.context.oc.busy, false);assert(!h.classes.has('oc-busy'));assert.equal(h.statuses.length, 0);
  }
});
