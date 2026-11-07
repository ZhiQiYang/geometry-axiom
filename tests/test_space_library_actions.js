'use strict';
/* #362: execute the shipped library renderer, delegated click handler and
 * mode dispatch. The finite DOM and owner callbacks are explicit seams;
 * this test does not claim Chrome layout or native model recomputation. */
const test = require('node:test'), assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path');
const {createDOM} = require('./_model_update_dom.js');
const ROOT = path.resolve(__dirname, '..');
const source = fs.readFileSync(process.env.GEOMETRY_SPACE_ACTION_SOURCE || path.join(ROOT, 'geometry-web/space-workspace.js'), 'utf8');
const clone = value => JSON.parse(JSON.stringify(value));

function between(start, end) {
  const at = source.indexOf(start), last = source.indexOf(end, at + start.length);
  assert.ok(at >= 0 && last > at && source.indexOf(start, at + 1) === -1, 'R362_SPACE_SOURCE_ANCHOR: ' + start);
  return source.slice(at, last);
}

function harness() {
  const {document, Element} = createDOM(), elements = new Map(), calls = [], lease = {allowed:true};
  Element.prototype.closest = function(selector) {
    for (let at = this; at; at = at.parentNode) if (at.matches(selector)) return at;
    return null;
  };
  const $ = id => {
    if (!elements.has(id)) {
      const element = document.createElement('div'); element.setAttribute('id', id);
      document.body.append(element); elements.set(id, element);
    }
    return elements.get(id);
  };
  const records = ['plan', 'faces'].map(mode => ({id:mode + '-model', name:mode + ' model',
    created_at:'2026-11-01T00:00:00.000Z', source:{kind:'scene',boundary_id:1},
    input:{mode,...(mode === 'plan' ? {settings:{height:2800,bottom:0}} : {uses:[{placement_id:2,orientation:1,purpose:'boundary'}]})},
    result:{summary:{closed:true,face_count:6,volume_mm3:'33600000000',timber_count:0}}}));
  // The selected library row is deliberately not the currently open model:
  // a missing data-sm-edit-model ID must not fall back to state.createdId.
  const state = {createdId:'plan-model', viewer:true, phase:'created', editing:null, previewRevision:2};
  const env = {$, state, ReferenceWorkspace:{getSpaceModels:()=>records},
    esc:value=>String(value).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;'),
    metric:String, wallRequirementMissing:()=>false, sectionProfileLibraryList(){},
    libraryActionAllowed:()=>lease.allowed,
    window:{ModelUpdateApp:{open:id=>{calls.push(['model-update',id]); return Promise.resolve();}}},
    close:()=>calls.push(['close']), show:()=>assert.fail('R362_SPACE_UNEXPECTED_SHOW'),
    openRecord:id=>calls.push(['record',id]), copy:clone, contextId:()=> 'project-context',
    updateActions:()=>calls.push(['update-actions']), setTab:tab=>calls.push(['tab',tab]),
    message:(...args)=>calls.push(['message',...args]), refresh:()=>assert.fail('R362_SPACE_UNEXPECTED_REFRESH'),
    openExample:()=>assert.fail('R362_SPACE_UNEXPECTED_EXAMPLE')};
  const code = between('  function libraryList() {', '  function openLibrary(') + '\n' +
    between('  function beginHeightEdit(', '  function cancelHeightEdit(') + '\n' +
    between('  $("smLibraryList").addEventListener("click",', '  window.addEventListener("space-models-changed",') + '\nreturn {libraryList};';
  const app = new Function(...Object.keys(env), code)(...Object.values(env));
  const action = id => {
    const row = $('smLibraryList').querySelector('[data-sm-open-model="' + id + '"]')?.parentNode;
    assert.ok(row, 'R362_SPACE_RENDERED_LIBRARY_ROW');
    return row.querySelectorAll('button').find(button => button.textContent === '修改模型');
  };
  return {...env, document, records, calls, lease, render:app.libraryList, action};
}

test('R362_SPACE_FACES_ACTION has one model action and no single wall-height action', () => {
  const h = harness(), before = JSON.stringify(h.records); h.render();
  const action = h.action('faces-model');
  assert.ok(action, 'R362_SPACE_FACES_MODEL_ACTION');
  assert.equal(action.getAttribute('data-sm-edit-height'), null, 'R362_SPACE_FACES_NO_HEIGHT_ACTION');
  assert.equal(action.getAttribute('data-sm-edit-model'), 'faces-model', 'R362_SPACE_FACES_MODEL_ACTION');
  assert.equal(action.parentNode.querySelectorAll('button').length, 3, 'R362_SPACE_NO_EXTRA_LIBRARY_ACTION');
  assert.equal(h.$('smLibraryList').querySelectorAll('[data-sm-edit-model]').length, 1, 'R362_SPACE_ONLY_FACES_MODEL_ACTION');
  assert.equal(JSON.stringify(h.records), before, 'R362_SPACE_RENDER_IS_READONLY');
  assert.deepEqual(h.calls, [], 'R362_SPACE_RENDER_DOES_NOT_OPEN_OR_COMMIT');
});

test('R362_SPACE_FACES_DISPATCH delegates the clicked row to the existing model-update owner', async () => {
  const h = harness(), before = JSON.stringify(h.records), stateBefore = JSON.stringify(h.state); h.render();
  const action = h.action('faces-model'); assert.ok(action, 'R362_SPACE_FACES_MODEL_ACTION');
  const child = h.document.createElement('span'); action.append(child);
  h.lease.allowed = false; await child.dispatch('click');
  assert.deepEqual(h.calls, [], 'R362_SPACE_LIBRARY_LEASE_GUARD');
  h.lease.allowed = true; await child.dispatch('click');
  assert.deepEqual(h.calls, [['close'], ['model-update','faces-model']], 'R362_SPACE_FACES_DISPATCH');
  assert.equal(JSON.stringify(h.state), stateBefore, 'R362_SPACE_FACES_NEVER_STARTS_HEIGHT_EDIT');
  assert.equal(JSON.stringify(h.records), before, 'R362_SPACE_FACES_ENTRY_DOES_NOT_COMMIT');
});

test('R362_SPACE_PLAN_ACTION preserves the existing saved-source wall-height entry', async () => {
  const h = harness(), before = JSON.stringify(h.records); h.render();
  const action = h.$('smLibraryList').querySelector('[data-sm-edit-height="plan-model"]');
  assert.ok(action, 'R362_SPACE_PLAN_HEIGHT_ACTION');
  assert.equal(action.getAttribute('data-sm-edit-model'), null, 'R362_SPACE_PLAN_RETAINS_HEIGHT_ACTION');
  assert.equal(action.textContent, '修改模型');
  await action.dispatch('click');
  assert.deepEqual(h.calls[0], ['record','plan-model'], 'R362_SPACE_PLAN_SAVED_SOURCE_ENTRY');
  assert.ok(h.calls.every(call => call[0] !== 'model-update' && call[0] !== 'close'), 'R362_SPACE_PLAN_NOT_SOURCE_ADOPTION');
  assert.deepEqual(h.state.editing, {record:h.records[0],context_id:'project-context'}, 'R362_SPACE_PLAN_ORIGINAL_RECORD');
  assert.equal(h.state.createdId, null); assert.equal(h.state.phase, 'editing');
  assert.equal(h.$('smEditHeight').value, 2800, 'R362_SPACE_PLAN_SAVED_HEIGHT');
  assert.equal(JSON.stringify(h.records), before, 'R362_SPACE_PLAN_ENTRY_DOES_NOT_COMMIT');
});

// ---- Identity ledger activation keeps the space source current (2026-11-07 cloud L4 walk, R09a) ----
{
/* Space workspace: turning on the identity ledger records one core undo step
 * but leaves the de-identified scene unchanged. Before this fix the next step
 * ("確認用途與觀看方向") always failed with 「來源或專案已變更」 because the
 * source's history token no longer matched (2026-11-07 cloud L4 walk, R09a).
 * The real space-workspace.js functions run with the real ContextHistory;
 * transport is a fake. Only an exact one-step activation may re-pin.
 */
const P = require('../geometry-web/project-store.js');

function slice(from, to) {
  const start = source.indexOf(from), end = source.indexOf(to, start);
  assert.ok(start >= 0 && end > start, 'anchor ' + from);
  return source.slice(start, end);
}
function line(prefix) {
  const start = source.indexOf(prefix);
  assert.ok(start >= 0, 'anchor ' + prefix);
  return source.slice(start, source.indexOf('\n', start));
}

function fixture({beforeActivate, afterActivate, dumpText, lineReply} = {}) {
  const history = new P.ContextHistory(() => ({id: 'project-a', models: [], sources: new Map()}));
  history.frame.ids.set(1, 'face-key-1');
  const base = 'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000\n';
  const evidence = {nativeRevision: 7, blocked: false};
  const calls = [], messages = [];
  const state = {source: null, result: null, revision: 3, previewRevision: -1, phase: 'ready', ledgerKnown: false, ledgerActive: false};
  const ReferenceWorkspace = {history, getEvidenceState: () => ({...evidence})};
  const sandbox = {
    state, ReferenceWorkspace, Number,
    contextId: () => 'project-a',
    faceKey: bid => history.frame.ids.get(bid),
    syncIdentityOffer() {}, updateActions() {},
    message: (text, kind = '') => messages.push({text, kind}),
    async api(command) {
      calls.push(command);
      if (command === 'identity-read') return {ok: true, active: false};
      if (command === 'line identity-ledger activate') {
        beforeActivate?.(history, evidence);
        const reply = {ok: true, history_changed: true, before_revision: evidence.nativeRevision, revision: evidence.nativeRevision + 1, ...lineReply};
        history.observe(command, reply);
        evidence.nativeRevision = reply.revision;
        afterActivate?.(history, evidence);
        return reply;
      }
      if (command === 'dump-deidentified') return {ok: true, text: dumpText ?? base};
      throw Error('unexpected command ' + command);
    },
  };
  const code = [line('  function sourceHistoryToken()'), line('  function sameSourceHistory('),
    // Baseline sources without the helpers still run activateIdentity, so a
    // missing re-pin fails as an assertion rather than a harness error.
    source.includes('  /* Activating the ledger appends') ? slice('  /* Activating the ledger appends', '  function creationOwner(')
      : slice('  async function activateIdentity()', '  function creationOwner(')].join('\n');
  const fns = new Function(...Object.keys(sandbox), code + '\nreturn {activateIdentity, sourceHistoryToken, sameSourceHistory};')(...Object.values(sandbox));
  state.source = {kind: 'scene', context_id: 'project-a', boundary_id: 1, face_key: 'face-key-1', base_scene: base, history_token: fns.sourceHistoryToken()};
  return {state, history, calls, messages, ...fns};
}
const coreStep = h => h.observe('line spec other 1', {ok: true, history_changed: true});

test('activation keeps a current scene source usable for the next step', async () => {
  const f = fixture();
  const before = f.state.source.history_token;
  await f.activateIdentity();
  assert.equal(f.history.undo.length, 1, 'activation is one undo step');
  assert.notEqual(f.state.source.history_token, before);
  assert.equal(f.sameSourceHistory(f.state.source.history_token), true, 'source is current after activation');
  assert.equal(f.state.ledgerActive, true);
  assert.deepEqual(f.messages.at(-1), {text: '已啟用物件身分追蹤。重新預覽後建立的模型才會帶來源身分。', kind: 'success'});
});

test('anything beyond the single activation step leaves the source stale', async () => {
  for (const [label, options] of [
    ['edit before activation', {beforeActivate: h => coreStep(h)}],
    ['edit after activation', {afterActivate: h => coreStep(h)}],
    ['scene text changed', {dumpText: 'surface 1 changed\n'}],
    ['native revision jumped', {lineReply: {before_revision: 9, revision: 10}}],
  ]) {
    const f = fixture(options);
    const before = f.state.source.history_token;
    await f.activateIdentity();
    assert.equal(f.state.source.history_token, before, label + ': token kept');
    assert.equal(f.sameSourceHistory(f.state.source.history_token), false, label + ': still stale');
    assert.equal(f.state.ledgerActive, true, label + ': ledger still activated');
    assert.deepEqual(f.messages.at(-1), {text: '已啟用物件身分追蹤。來源讀取後另有變更，請重新「使用目前面」再預覽。', kind: 'warning'}, label);
  }
});

test('an activation that records no history step keeps the source as it was', async () => {
  const f = fixture({lineReply: {history_changed: false}});
  const before = f.state.source.history_token;
  await f.activateIdentity();
  assert.equal(f.history.undo.length, 0);
  assert.equal(f.state.source.history_token, before);
  assert.equal(f.sameSourceHistory(before), true);
  assert.equal(f.messages.at(-1).kind, 'success');
});

test('a source that was already stale is not re-pinned by activation', async () => {
  const f = fixture();
  coreStep(f.history);
  const before = f.state.source.history_token;
  await f.activateIdentity();
  assert.equal(f.state.source.history_token, before);
  assert.equal(f.sameSourceHistory(before), false);
  assert.equal(f.calls.includes('dump-deidentified'), false, 'no re-pin attempt without a current pin');
});
}
