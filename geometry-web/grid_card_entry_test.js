/* PR #353 / R01: trusted browser input, native candidates and formal .gcanvas I/O.
 * Baseline: 037a28267f07503d5b85f6632f57f6e1ea50475e + pr353-tests-v1.
 * Fixture writes are explicit and isolated; tested grid edits use visible controls.
 * No expected failure is converted to pass. Run via cdp_test.js, never standalone.
 */
'use strict';
const fs = require('fs'), os = require('os'), path = require('path');
const {isDeepStrictEqual: same} = require('util');
const cdp = require('./cdp_helpers.js');
const P = require('./project-store.js'), zip = require('./vendor/fflate/umd/index.js');
const CASE_IDS = Object.freeze([
  'entry', 'explicit_mapping', 'commit_cancel', 'swap', 'equal_swap', 'reopen',
  'native_rejection', 'raw_roundtrip', 'archive_roundtrip', 'history',
  'lost_source', 'stale_preview', 'binding_effective',
  'pin_preserve_untouched', 'pin_reacquire_cancel', 'pin_reacquire_confirm',
  'pin_shared_consumers', 'lost_card_existing_pins', 'lost_card_same_id_rebuild',
  'card_render_repeat_repeat', 'card_render_repeat_panel', 'card_render_panel_panel',
  'inspector_repeat_repeat', 'inspector_repeat_panel', 'inspector_panel_panel',
  'inspector_direct_control', 'inspector_parameter_control',
  'compat_raw_capability', 'compat_legacy_unchanged', 'compat_raw_rule_roundtrip',
  'compat_mixed_roundtrip', 'compat_reader_rejection_atomic',
  'compat_historical_pins', 'compat_geo219_reduction'
]);
function selectCases(value) {
  if (value === undefined) return [...CASE_IDS];
  if (typeof value !== 'string' || !value.trim()) throw Error('Empty GEOMETRY_GRID_CARD_ENTRY_CASE');
  const ids = value.split(',').map(id => id.trim());
  if (new Set(ids).size !== ids.length || ids.some(id => !CASE_IDS.includes(id)))
    throw Error('GEOMETRY_GRID_CARD_ENTRY_CASE must contain unique exact IDs: ' + CASE_IDS.join(','));
  return ids;
}
function failure(kind, assertion, message, detail) {
  const error = new Error(message + (detail === undefined ? '' : ' ' + JSON.stringify(detail)));
  error.p353 = {kind, assertion};
  return error;
}
module.exports = async function gridCardEntryTests({
  send, eval_, sleep, click, waitForUI, expectNativeDialog, exceptionCount
}) {
  if (process.env.GEOMETRY_GRID_CARD_ENTRY_CASE !== undefined && process.env.GEOMETRY_GRID_CARD_ENTRY_ONLY !== '1')
    throw failure('precondition','CASE_FILTER_REQUIRES_ONLY','GEOMETRY_GRID_CARD_ENTRY_CASE requires GEOMETRY_GRID_CARD_ENTRY_ONLY=1');
  const selected = selectCases(process.env.GEOMETRY_GRID_CARD_ENTRY_CASE);
  console.log('=== P353. R01 whole-card entry, identity, draft and project roundtrip ===');
  const read = cdp.makeRead(eval_);
  const page = (fn, ...args) => read('(' + fn.toString() + ')(' + args.map(arg => JSON.stringify(arg)).join(',') + ')');
  const wait = cdp.makeWait(waitForUI, 20000);
  const recordCheck = cdp.makeCheck({prefix:'P353 ', throwOnFail:false});
  const check = (code, value, detail) => {
    recordCheck(code, value, detail);
    if (value !== true) throw failure('assertion', code, code, detail);
  };
  const need = (code, value, detail) => {
    if (value !== true) throw failure('precondition', code, code, detail);
  };
  const ctl = cdp.makeCtl({eval_, sleep, click}, {
    scroll:'center', attempts:12, pollMs:60, settleMs:100, missing:'P353 missing ',
    unreachable:(selector, point) => 'P353 unreachable ' + selector + ' ' + JSON.stringify(point),
    before:cdp.openCreateObjectMenu(read, selector => ctl(selector))
  });
  const key = cdp.makeKey({send, sleep});
  const fill = cdp.makeFill({ctl, key, send, sleep}, {afterMs:50});
  const history = cdp.makeHistoryOracle(read, 'P353');
  let pins = [], nativeTokens = [], currentCase = null;
  const query = cmd => page(async command => {
    const result = await apiRequest(command);
    if (!result.ok) throw Error(command + ': ' + JSON.stringify(result));
    return result;
  }, cmd);
  const dump = async () => (await query('dump')).text;
  const objects = () => query('objects');
  const raw = () => page(() => {
    const all = ReferenceWorkspace.readGridDrafts().drafts;
    const id = document.getElementById('infiniteGridWorkspace')?.dataset.draftId;
    return all.find(draft => draft.draftId === id) || (all.length === 1 ? all[0] : null);
  });
  const allRaw = () => page(() => ReferenceWorkspace.readGridDrafts());
  const settled = () => wait("connection.phase==='ready'&&!oc.busy&&!ReferenceWorkspace.busy");
  const pinHistory = async () => { const pin = await history.capture(); pins.push(pin); return pin; };
  const releasePin = async pin => { await history.release(pin); pins = pins.filter(item => item !== pin); };
  const visible = selector => page(s => {
    const n = document.querySelector(s), r = n?.getBoundingClientRect();
    return !!n && !!r && r.width > 0 && r.height > 0 && getComputedStyle(n).visibility !== 'hidden';
  }, selector);
  const choose = async (selector, value, {waitForValue = true} = {}) => {
    const wanted = String(value);
    const index = await page((s, v) => {
      const node = document.querySelector(s);
      if (!node) throw Error('No select: ' + s);
      return [...node.options].filter(option => !option.disabled).findIndex(option => option.value === v);
    }, selector, wanted);
    need('SELECT_OPTION_AVAILABLE', index >= 0, {selector, value:wanted});
    await ctl(selector);
    await key('Home', 'Home', 36);
    for (let n = 0; n < index; n++) await key('ArrowDown', 'ArrowDown', 40);
    await key('Enter', 'Enter', 13);
    if (waitForValue) await wait('document.querySelector(' + JSON.stringify(selector) + ')?.value===' + JSON.stringify(wanted));
  };
  const mapping = () => page(() => ({
    card:document.getElementById('igCard')?.value,
    u:document.getElementById('igCardU')?.value,
    v:document.getElementById('igCardV')?.value
  }));
  const map = async (id, u, v) => {
    await choose('#igCard', id);
    await choose('#igCardU', u);
    await choose('#igCardV', v);
    await settled();
  };
  const leave = async () => {
    if (await page(() => !!document.querySelector('.reference-impact[open]'))) await cancel();
    if (await page(() => !!document.getElementById('infiniteGridWorkspace')?.open)) {
      await ctl('#igClose');
      await wait("!document.getElementById('infiniteGridWorkspace')?.open");
    }
  };
  const newProject = async () => {
    await leave();
    const before = await page(() => ReferenceWorkspace.getProjectState().id);
    const dirty = await page(() => ReferenceWorkspace.context().dirty);
    await ctl('#fileMenuBtn');
    await expectNativeDialog(() => ctl('#btnNewProject'), {
      message:'建立一份空白新專案，切換為新的專案識別及「未命名專案」。' +
        (dirty ? '目前尚未保存的變更不會自動寫入檔案。' : '') +
        '本次切換可一步復原；僅保存在本頁的形狀特徵參數不會恢復。確定繼續嗎？',
      accept:true
    });
    await wait('ReferenceWorkspace.getProjectState().id!==' + JSON.stringify(before));
    await settled();
    const state = await page(() => ({
      id:ReferenceWorkspace.getProjectState().id,
      blocked:ReferenceWorkspace.getProjectInfo().editingBlocked,
      drafts:ReferenceWorkspace.readGridDrafts().drafts.length
    }));
    const o = await objects();
    need('ISOLATED_NEW_PROJECT', state.id !== before && !state.blocked && state.drafts === 0 &&
      o.gridSystems.length === 0 && o.parameters.length === 0, state);
  };
  const parameter = (id, a, b, secondType = 'dimension') => ({
    op:'put-parameter', value:{id, name:'R01 card ' + id + ' <&>', fields:[
      {id:8, name:'first-listed', type:secondType, input:String(b)},
      {id:3, name:'second-listed', type:'dimension', input:String(a)},
      {id:13, name:'extra count', type:'count', input:'4'}
    ]}
  });
  const grid = (id = 4, parameterId = 10, u = 3, v = 8, mixed = false) => ({
    op:'put-grid-system', value:{id, name:'R01 existing ' + id, mainAlong:'none',
      u:mixed ? 'repeat-panel card gap 3 from -5' : 'repeat -5 card',
      v:'repeat 7 card', cardReference:{parameterId, uFieldId:u, vFieldId:v}}
  });
  const applyFixture = async operations => {
    const result = await page(async ops => {
      const base = await apiRequest('engineering-read');
      if (!base.ok) throw Error(JSON.stringify(base));
      const p = await EngineeringAdapter.preview({expectedRevision:base.revision, operations:ops});
      if (!p.valid) throw Error('Fixture candidate rejected: ' + JSON.stringify(p));
      const result = await EngineeringAdapter.confirm({token:p.token});
      if (!result.ok || !await renderObjects()) throw Error('Fixture commit/render failed');
      return result;
    }, operations);
    need('NATIVE_FIXTURE_COMMITTED', result.ok === true, result);
  };
  const fixture = async ({source = false, equal = false, mixed = false, board = false} = {}) => {
    await newProject();
    const ops = [
      parameter(10, board ? 915 : 12, board ? 1830 : 30),
      parameter(20, 12, 12), parameter(30, 12, 30, 'count')
    ];
    if (source) ops.push(grid(4, equal ? 20 : 10, 3, 8, mixed));
    await applyFixture(ops);
    const o = await objects();
    need('NATIVE_FIXTURE_CARDS', o.parameters.length === 3, o.parameters.map(row => row.id));
    if (source) {
      const g = o.gridSystems.find(row => row.id === 4);
      need('NATIVE_FIXTURE_CARD_SOURCE', g?.cardReference?.parameterId === (equal ? 20 : 10) &&
        g.cardReference.uFieldId === 3 && g.cardReference.vFieldId === 8, g);
    }
    await page(() => {
      if (window.__p353ApiTrace) throw Error('Trace leaked from another case');
      const trace = window.__p353ApiTrace = {original:window.apiRequest, calls:[]};
      window.apiRequest = async function(command, ...args) {
        const row = {command, state:'pending'};
        trace.calls.push(row);
        try {
          const result = await trace.original.call(this, command, ...args);
          row.result = structuredClone(result); row.state = 'fulfilled';
          return result;
        } catch (error) { row.error = String(error); row.state = 'rejected'; throw error; }
      };
    });
  };
  const openNew = async name => {
    await ctl('#btnNewGridSystem');
    await wait("document.getElementById('infiniteGridWorkspace')?.open&&document.getElementById('igName')&&!document.getElementById('igName').disabled");
    check('ENTRY_CARD_VISIBLE', await visible('#igCardRef') && await visible('#igCard'));
    await fill('#igName', name);
  };
  const openSource = async id => {
    await leave();
    await ctl('#btnZoom');
    if (await visible('#ocSelectionSummary .guidance-dismiss')) await ctl('#ocSelectionSummary .guidance-dismiss');
    await ctl('.ocard[data-kind="grid-system"][data-id="' + id + '"]');
    await wait("!!document.getElementById('gridObjectOpen')");
    await ctl('#gridObjectOpen');
    await wait("document.getElementById('infiniteGridWorkspace')?.open&&document.getElementById('igCard')&&!document.getElementById('igName').disabled");
  };
  const openDraft = async id => {
    await leave();
    await ctl('#btnNewGridSystem');
    await wait("document.getElementById('gridDraftChooser')?.open");
    await ctl('#gridDraftChooser [data-draft-id="' + id + '"]');
    await wait("document.getElementById('infiniteGridWorkspace')?.open&&!document.getElementById('igName').disabled");
  };
  const healthy = async code => {
    const state = await page(async () => ({
      connection:connection.phase, ready:document.readyState,
      response:await apiRequest('objects')
    }));
    if (state.connection !== 'ready' || state.ready !== 'complete' || state.response?.ok !== true)
      throw failure('exception', code + '_ENVIRONMENT', 'Application/native service is not healthy', state);
  };
  const waitProduct = async (code, expression) => {
    try { await wait(expression); }
    catch (error) {
      // Only a completed, responsive application can produce a product timeout.
      // CDP/protocol errors and unfinished native requests are never mutation kills.
      if (!error.message.startsWith('UI condition timed out')) throw error;
      const pending = await page(() => window.__p353ApiTrace?.calls.filter(row => row.state === 'pending') || []);
      if (pending.length) throw failure('exception',code + '_PENDING_NATIVE','Native request did not complete',pending);
      await healthy(code);
      check(code, false, {timeout:true,expression});
    }
  };
  const preview = async (prefix, {button = '#igSaveSource', command = 'line preview grid-system ', inspectCommand = null} = {}) => {
    check(prefix + '_PREVIEW_ENABLED', await page(selector => {
      const b = document.querySelector(selector); return !!b && !b.disabled;
    },button));
    const cursor = await page(() => window.__p353ApiTrace.calls.length);
    await ctl(button);
    const completed = '(window.__p353ApiTrace.calls.slice(' + cursor + ').some(row=>' +
      'row.command.startsWith(' + JSON.stringify(command) + ')&&row.state!=="pending"))';
    await waitProduct(prefix + '_NATIVE_PREVIEW', completed);
    const result = await page((start, cmd) => window.__p353ApiTrace.calls.slice(start)
      .find(row => row.command.startsWith(cmd) && row.state !== 'pending'), cursor, command);
    if (result?.state === 'rejected') throw failure('exception',prefix + '_PREVIEW_REQUEST_REJECTED',result.error);
    if (inspectCommand) inspectCommand(result?.command);
    await healthy(prefix + '_PREVIEW');
    check(prefix + '_NATIVE_PREVIEW', result?.result?.ok === true && !!result.result.preview, result);
    check(prefix + '_PREVIEW_VALID', result.result.preview.valid === true, result.result.preview);
    await waitProduct(prefix + '_IMPACT_VISIBLE', "!!document.querySelector('.reference-impact[open]')");
    check(prefix + '_IMPACT_VISIBLE', await visible('.reference-impact[open]'));
    return result.result.preview;
  };
  const confirm = async () => {
    check('CONFIRM_REACHABLE', await visible('#impact-confirm') &&
      await page(() => document.getElementById('impact-confirm').disabled === false));
    await ctl('#impact-confirm');
    await wait("!document.querySelector('.reference-impact[open]')");
    await settled();
    await wait("!document.getElementById('infiniteGridWorkspace')?.open||!document.getElementById('igName')?.disabled");
  };
  const rejectedAttempt = async code => {
    if (await page(() => !document.getElementById('igSaveSource').disabled)) await ctl('#igSaveSource');
    // A mutation that wrongly reaches a confirmation is an assertion failure,
    // not an artificial wait for the still-open modal to become idle.
    await waitProduct(code + '_FINISHED', "!!document.querySelector('.reference-impact[open]')||(!document.getElementById('infiniteGridWorkspace').classList.contains('ig-busy')&&!oc.busy&&!ReferenceWorkspace.busy)");
    await healthy(code);
  };
  async function cancel() {
    await ctl('.reference-impact[open] .impact-actions button:first-child');
    await wait("!document.querySelector('.reference-impact[open]')");
    await settled();
  }
  const source = async id => (await objects()).gridSystems.find(row => row.id === id);
  const identity = (g, pid, u, v) => !!g && same(g.cardReference, {parameterId:pid, uFieldId:u, vFieldId:v}) &&
    ['u','v'].every(axis => {
      const d = g[axis + 'Definition'], slot = d.source === 'repeat' ? 'step' : 'panel';
      return d[slot + 'Source'] === 'card' && !Object.hasOwn(d, slot) && !Object.hasOwn(d.parameterRefs || {}, slot);
    });
  const assertIdentity = async (code, id, pid, u, v) => {
    const g = await source(id), scene = await dump();
    const line = scene.split('\n').find(text => text.startsWith('grid-system ' + id + ' '));
    check(code, identity(g, pid, u, v) && line?.includes(' card-reference ' + pid + ' ' + u + ' ' + v + ' ') &&
      line.split(/\s+/).filter(token => token === 'card').length === 2, {source:g, line});
    return g;
  };
  const nativeLines = async id => {
    const result = await query('grid-query system ' + id + ' rect -100 -100 100 100 mode exact limit 64');
    need('NATIVE_QUERY_EXACT', result.exact === true && result.mode === 'exact', result);
    return Object.fromEntries(['u','v'].map(axis => {
      const byIndex = new Map(result.axes[axis].lines.map(line => [line.index, line.coordinate]));
      return [axis, ['-1','0','1'].map(index => byIndex.get(index))];
    }));
  };
  const newCardGrid = async (name = 'R01 create') => {
    await openNew(name);
    await map(10, 3, 8);
    await fill('#igUPhase', '-5');
    await fill('#igVPhase', '7');
  };
  const addedSource = async name => {
    const rows = (await objects()).gridSystems.filter(row => row.name === name);
    check('CREATE_ONE_SOURCE', rows.length === 1, rows);
    return rows[0];
  };
  const saveFile = async () => {
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'geometry-p353-' + currentCase + '-'));
    await send('Browser.setDownloadBehavior', {behavior:'allow', downloadPath:directory});
    await page(() => {
      if (window.__p353SavePicker) throw Error('Save picker override already installed');
      window.__p353SavePicker = {descriptor:Object.getOwnPropertyDescriptor(window, 'showSaveFilePicker')};
      Object.defineProperty(window, 'showSaveFilePicker', {value:undefined, configurable:true});
    });
    let file = null;
    try {
      await ctl('#projectBar [data-project-action="save"]');
      for (let attempt = 0; attempt < 150; attempt++) {
        const files = fs.readdirSync(directory).filter(name => name.endsWith('.gcanvas'));
        if (files.length > 1) throw failure('exception', 'AMBIGUOUS_DOWNLOAD', 'Multiple project downloads', files);
        if (files.length === 1) { file = path.join(directory, files[0]); break; }
        await sleep(100);
      }
    } finally {
      await page(() => {
        const saved = window.__p353SavePicker;
        if (saved?.descriptor) Object.defineProperty(window, 'showSaveFilePicker', saved.descriptor);
        else delete window.showSaveFilePicker;
        delete window.__p353SavePicker;
      });
    }
    check('FORMAL_SAVE_FILE', !!file && fs.statSync(file).size > 0, {directory, file});
    await settled();
    const bytes = new Uint8Array(fs.readFileSync(file));
    const loaded = await P.unpack(bytes, zip);
    console.log('P353_ARTIFACT ' + JSON.stringify({case:currentCase, file, format:loaded.manifest.format}));
    return {file, directory, bytes, loaded};
  };
  const openFile = async (file, expectedProjectId) => {
    await newProject();
    await send('Page.setInterceptFileChooserDialog', {enabled:true});
    try {
      await page(() => {
        window.__p353FileChooser = false;
        document.getElementById('projectFile').addEventListener('click', () => {window.__p353FileChooser = true;}, {once:true});
      });
      await ctl('#fileMenuBtn');
      await ctl('#btnOpenProject');
      check('FORMAL_OPEN_CHOOSER', await page(() => window.__p353FileChooser === true));
      const document = await send('DOM.getDocument', {depth:0});
      const input = await send('DOM.querySelector', {nodeId:document.result.root.nodeId, selector:'#projectFile'});
      need('FORMAL_FILE_INPUT', input.result.nodeId > 0);
      await send('DOM.setFileInputFiles', {nodeId:input.result.nodeId, files:[file]});
      // A still-idle old context is not evidence that the FileReader/import ran.
      await waitProduct('FORMAL_OPEN_PROJECT_ID', 'ReferenceWorkspace.getProjectState().id===' + JSON.stringify(expectedProjectId));
      await waitProduct('FORMAL_OPEN_FINISHED', "!ReferenceWorkspace.busy&&!document.getElementById('app').inert&&document.getElementById('projectFile').value===''");
      await settled();
      check('FORMAL_OPEN_PROJECT_ID', await page(id => ReferenceWorkspace.getProjectState().id === id, expectedProjectId));
    } finally {
      await send('Page.setInterceptFileChooserDialog', {enabled:false});
      await page(() => {delete window.__p353FileChooser;});
    }
  };
  const fromArchive = loaded => {
    const record = loaded.manifest.featureAttachments?.records.find(item => item.kind === 'grid-draft');
    return P.Features.gridDrafts(record ? record.value : null);
  };
  const writeArchive = async (saved, name, manifest, writer = P) => {
    const file = path.join(saved.directory, name + '.gcanvas');
    fs.writeFileSync(file, await writer.pack(saved.loaded.scene, manifest, saved.loaded.sources, zip));
    return file;
  };
  const rejectFileWithoutReplacement = async (file, code) => {
    await leave();
    const before = {world:await dump(), drafts:await allRaw(), metadata:await page(() => ReferenceWorkspace.manifest()),
      state:await page(() => ReferenceWorkspace.getProjectState()),
      nativeRevision:(await query('engineering-read')).revision};
    const hp = await pinHistory();
    const cursor = await page(() => window.__p353ApiTrace.calls.length);
    await send('Page.setInterceptFileChooserDialog', {enabled:true});
    try {
      await page(() => {
        window.__p353RejectedFileChange = false;
        document.getElementById('projectFile').addEventListener('change', () => {
          window.__p353RejectedFileChange = true;
        }, {once:true, capture:true});
      });
      await ctl('#fileMenuBtn');
      const dirty = await page(() => ReferenceWorkspace.context().dirty);
      if (dirty) await expectNativeDialog(() => ctl('#btnOpenProject'), {
        message:'目前專案有尚未保存的變更。要離開目前專案嗎？', accept:true
      });
      else await ctl('#btnOpenProject');
      const document = await send('DOM.getDocument', {depth:0});
      const input = await send('DOM.querySelector', {nodeId:document.result.root.nodeId, selector:'#projectFile'});
      need('COMPAT_FILE_INPUT', input.result.nodeId > 0);
      await send('DOM.setFileInputFiles', {nodeId:input.result.nodeId, files:[file]});
      await waitProduct(code + '_FINISHED', "window.__p353RejectedFileChange===true&&!ReferenceWorkspace.busy&&document.getElementById('projectFile').value===''");
      const observed = await page(start => ({
        calls:window.__p353ApiTrace.calls.slice(start),
        message:[...document.querySelectorAll('#toastRegion .toast')].map(node => node.textContent).join('\n'),
        state:ReferenceWorkspace.getProjectState()
      }), cursor);
      check(code + '_REJECTED', /能力/.test(observed.message), observed);
      // Background recovery may read dump after the rejected import finishes.
      // Its read is allowed; every other command (including any mutation) fails.
      check(code + '_NO_NATIVE_WRITE', observed.calls.every(row => row.command === 'dump' && row.result?.ok === true), observed.calls);
      check(code + '_PROJECT_UNCHANGED', same(observed.state,before.state) &&
        (await dump()) === before.world && (await query('engineering-read')).revision === before.nativeRevision &&
        same(await allRaw(),before.drafts) && same(await page(() => ReferenceWorkspace.manifest()),before.metadata) &&
        await history.unchanged(hp), observed.state);
    } finally {
      await send('Page.setInterceptFileChooserDialog', {enabled:false});
      await page(() => {delete window.__p353RejectedFileChange;});
      await releasePin(hp);
    }
  };
  const operationsPreview = async operations => {
    const p = await page(async ops => {
      const base = await apiRequest('engineering-read');
      if (!base.ok) throw Error(JSON.stringify(base));
      return EngineeringAdapter.preview({expectedRevision:base.revision, operations:ops});
    }, operations);
    nativeTokens.push(p.token);
    return p;
  };
  const discardRaw = async () => {
    await ctl('#igDiscardDraft');
    await wait("!!document.getElementById('igDiscardConfirmation')");
    check('DISCARD_QUESTION', await page(() => document.getElementById('igDiscardQuestion').textContent ===
      '捨棄這份未發布的原始草稿？已保存到場景的網格保持不變。'));
    await ctl('#igDiscardConfirm');
    await wait("!document.getElementById('infiniteGridWorkspace')?.open");
  };
  const fieldPin = (draft, parameterId, fieldId) => draft.inputRefs.find(ref =>
    ref.kind === 'parameter-field' && ref.parameterId === parameterId && ref.fieldId === fieldId);
  const threeFieldParameter = (b, a = 12) => {
    const operation = parameter(10, a, b);
    operation.value.fields.push({id:14, name:'third dimension', type:'dimension', input:'45'});
    return operation;
  };
  const staleCardDraft = async () => {
    await fixture();
    await applyFixture([threeFieldParameter(30)]);
    await newCardGrid('R353 stale other axis');
    const original = await raw();
    need('STALE_FIXTURE_TWO_PINS', !!fieldPin(original,10,3) && !!fieldPin(original,10,8), original);
    await leave();
    await applyFixture([threeFieldParameter(60)]);
    await openDraft(original.draftId);
    const restored = await raw();
    need('STALE_FIXTURE_OWNED_EVIDENCE', same(restored.inputRefs,original.inputRefs) &&
      restored.rawForm.igVStep === '30', restored);
    return restored;
  };
  const actualFieldPin = (parameterId, fieldId) => page(async (pid,fid) => {
    const result = await apiRequest('objects');
    if (!result.ok) throw Error('Cannot read the native parameter field');
    const row = result.parameters.find(item => item.id === pid), field = row?.card.fields.find(item => item.id === fid);
    if (!field) throw Error('Missing native parameter field');
    return {kind:'parameter-field',parameterId:pid,fieldId:fid,
      fingerprint:await GeometryProject.sha(new TextEncoder().encode(JSON.stringify([row.card.id,field])))};
  }, parameterId, fieldId);
  const reacquireStale = async (before, accept) => {
    const after = await actualFieldPin(10,8), prior = fieldPin(before,10,8);
    need('REACQUIRE_FIXTURE_CHANGED', prior?.fingerprint !== after.fingerprint && !prior?.lost, {prior,after});
    const message = '重新選取來源（舊 → 新）；原始輸入保留，仍須預覽與確認。\n' + JSON.stringify({before:prior,after});
    try {
      // Explicitly selecting the stale field for u is a real select gesture.
      // Its shared v pin requires confirmation before native same-field validation.
      await expectNativeDialog(() => choose('#igCardU',8,{waitForValue:false}), {message,accept});
    } catch (error) {
      if (!error.message.startsWith('Expected native dialog did not appear:')) throw error;
      await healthy('REACQUIRE');
      check('REACQUIRE_OLD_NEW_CONFIRMATION', false, {message});
    }
    await settled();
    return after;
  };
  const axisKinds = shape => ({repeat_repeat:['repeat','repeat'],repeat_panel:['repeat','repeat-panel'],
    panel_panel:['repeat-panel','repeat-panel']})[shape];
  const axisWorld = shape => axisKinds(shape).map((kind,index) => ({kind,length:index ? 1200 : 600,
    phase:index ? 211 : -137,gap:index ? 5 : 3,field:index ? 8 : 3}));
  const renderGrid = (id, shape, sourceKind) => {
    const axes = axisWorld(shape);
    const body = axes.map(axis => {
      const length = sourceKind === 'card' ? 'card' : sourceKind === 'parameter' ? 'param:10:' + axis.field : axis.length;
      return axis.kind === 'repeat' ? `repeat ${axis.phase} ${length}` : `repeat-panel ${length} gap ${axis.gap} from ${axis.phase}`;
    });
    return {op:'put-grid-system',value:{id,name:'R353 '+shape+' '+sourceKind,mainAlong:'none',u:body[0],v:body[1],
      ...(sourceKind === 'card' ? {cardReference:{parameterId:10,uFieldId:3,vFieldId:8}} : {})}};
  };
  const effectiveWorld = async shape => {
    await fixture();
    await applyFixture([parameter(10,600,1200),renderGrid(4,shape,'card'),
      renderGrid(5,shape,'direct'),renderGrid(6,shape,'parameter')]);
    const controlled = await source(4);
    need('EFFECTIVE_WORLD_NATIVE_CARD', identity(controlled,10,3,8) && axisWorld(shape).every((axis,index) => {
      const d = controlled[['uDefinition','vDefinition'][index]];
      return d[axis.kind === 'repeat' ? 'effectiveStep' : 'effectivePanel'] === axis.length;
    }), controlled);
  };
  const cardView = id => page(value => {
    const card = document.querySelector('.grid-system-card[data-id="'+value+'"]'), body = card?.querySelector('.ocard-body');
    const rect = body?.querySelector('rect'), attrs = (node,keys) => keys.map(k => {
      const value = node?.getAttribute(k); return value === null || value === undefined ? null : Number(value);
    });
    return {title:card?.querySelector('title')?.textContent || '',text:body?.textContent || '',
      bounds:attrs(rect,['x','y','width','height']),
      lines:[...(body?.querySelectorAll('line') || [])].map(line => attrs(line,['x1','y1','x2','y2']))};
  }, id);
  const sketchMatches = (view, shape) => {
    if (!view.bounds.every(Number.isFinite) || !view.lines.length || !view.lines.every(line => line.every(Number.isFinite))) return false;
    const [x,y,w,h] = view.bounds, axes = axisWorld(shape).map(axis => ({
      pitch:axis.length + (axis.kind === 'repeat-panel' ? axis.gap : 0),
      phase:axis.phase + (axis.kind === 'repeat-panel' ? axis.length + Math.floor(axis.gap/2) : 0)
    }));
    const scale = Math.min(w/(4*axes[0].pitch),h/(4*axes[1].pitch));
    // Independent fixture oracle: each visible coordinate lies on the declared
    // phase + integer*pitch lattice, and both axes have their expected sample.
    return axes.every((axis,index) => {
      const start = index ? y : x, span = index ? h : w, center = start+span/2;
      const lines = view.lines.filter(line => index ? line[1] === line[3] : line[0] === line[2]);
      const low = Math.ceil(((start-center)/scale-axis.phase)/axis.pitch);
      const high = Math.floor(((start+span-center)/scale-axis.phase)/axis.pitch);
      return lines.length === high-low+1 && lines.every((line,n) => {
        const position = index ? line[1] : line[0];
        return Math.abs(position - (center+(axis.phase+(low+n)*axis.pitch)*scale)) < 1e-7;
      });
    });
  };
  const renderEffective = async shape => {
    await effectiveWorld(shape);
    const before = await dump(), views = await Promise.all([4,5,6].map(cardView));
    const [card,direct,parameter] = views, lengths = axisWorld(shape);
    check('RENDER_DIRECT_CONTROL', sketchMatches(direct,shape) && !/undefined|NaN/.test(direct.title+direct.text), direct);
    check('RENDER_PARAMETER_CONTROL', sketchMatches(parameter,shape) && same(parameter.lines,direct.lines) &&
      !/undefined|NaN/.test(parameter.title+parameter.text), parameter);
    const expectedPitch = 'X 間距 '+(lengths[0].length+(lengths[0].kind === 'repeat-panel' ? lengths[0].gap : 0))+
      ' · Y 間距 '+(lengths[1].length+(lengths[1].kind === 'repeat-panel' ? lengths[1].gap : 0))+' mm';
    check('RENDER_CARD_EFFECTIVE', !/undefined|NaN/.test(card.title+card.text) && card.text.includes(expectedPitch) &&
      card.title.includes('600') && card.title.includes('1200'), card);
    check('RENDER_CARD_SOURCE_MEANING', card.title.includes('整張參數卡 #10') &&
      card.title.includes('u ← 欄位 #3') && card.title.includes('v ← 欄位 #8'), card.title);
    check('RENDER_CARD_PHASE_AND_LINES', sketchMatches(card,shape) && same(card.lines,direct.lines) &&
      same(card.lines,parameter.lines), {card,direct,parameter});
    check('RENDER_READ_ONLY_MODEL', (await dump()) === before && identity(await source(4),10,3,8));
  };
  const openInspector = async id => {
    await leave();
    await ctl('#btnZoom');
    if (await visible('#ocSelectionSummary .guidance-dismiss')) await ctl('#ocSelectionSummary .guidance-dismiss');
    await ctl('.ocard[data-kind="grid-system"][data-id="'+id+'"]');
    await wait('!!document.getElementById("gridInlineInspector")&&!!document.getElementById("giName")');
  };
  const inspectorView = () => page(() => ({
    fields:[...document.querySelectorAll('#gridInlineInspector .gi-axis-field')].map(label => {
      const input = label.querySelector('input'), readonly = label.querySelector('.gi-readonly');
      return {value:input?.value ?? null,readonly:input?.readOnly ?? null,aria:input?.getAttribute('aria-readonly') ?? null,
        panel:readonly?.textContent ?? null,text:label.textContent};
    }),
    bindingDisabled:document.getElementById('gridObjectNewBinding')?.disabled,
    bindingTitle:document.getElementById('gridObjectNewBinding')?.title,
    text:document.getElementById('gridInlineInspector')?.textContent || ''
  }));
  const inspectorEffective = async shape => {
    await effectiveWorld(shape);
    const before = await source(4);
    await openInspector(4);
    const ui = await inspectorView();
    check('INSPECTOR_EFFECTIVE_VALUES', ui.fields.length === 2 && axisWorld(shape).every((axis,index) => {
      const field = ui.fields[index];
      return axis.kind === 'repeat' ? field.value === String(axis.length) :
        field.panel?.includes('面材 '+axis.length+' + 縫 '+axis.gap+' mm');
    }) && !/undefined|NaN/.test(ui.text), ui);
    check('INSPECTOR_CARD_READONLY', axisWorld(shape).every((axis,index) => {
      const field = ui.fields[index];
      return field.text.includes('整張參數卡') && (axis.kind !== 'repeat' || field.readonly && field.aria === 'true');
    }), ui);
    check('INSPECTOR_UNEDITED_BINDING_ENABLED', ui.bindingDisabled === false && !ui.bindingTitle.includes('請先預覽'), ui);
    await ctl('#gridObjectNewBinding');
    await waitProduct('INSPECTOR_CREATE_BINDING_OPENS', 'document.getElementById("infiniteGridWorkspace")?.open&&!!document.getElementById("igBoundary")');
    check('INSPECTOR_CREATE_BINDING_SOURCE', await page(() => document.getElementById('igSystem')?.value === '4'));
    await openInspector(4);
    const name = 'R353 inspector '+shape;
    await fill('#giName',name);
    check('INSPECTOR_REAL_DIRTY_BLOCKS_BINDING', (await inspectorView()).bindingDisabled === true);
    const inspectCommand = command => {
      check('INSPECTOR_SERIALIZED_CARD_IDENTITY', command.includes(' card-reference 10 3 8 '), command);
      check('INSPECTOR_SERIALIZED_CARD_TOKENS', command.split(/\s+/).filter(token => token === 'card').length === 2 &&
        !/undefined|NaN/.test(command), command);
    };
    const scene = await dump();
    await preview('INSPECTOR_RENAME',{button:'#giPreview',inspectCommand});
    await cancel();
    check('INSPECTOR_CANCEL_PRESERVES_SOURCE', (await dump()) === scene && same(await source(4),before));
    await preview('INSPECTOR_RENAME',{button:'#giPreview',inspectCommand});
    await confirm();
    const after = await assertIdentity('INSPECTOR_RENAME_SOURCE_IDENTITY',4,10,3,8);
    check('INSPECTOR_RENAME_ONLY', after.name === name && same(after.uDefinition,before.uDefinition) &&
      same(after.vDefinition,before.vDefinition), {before,after});
    await openInspector(4);
    check('INSPECTOR_SAVED_BINDING_ENABLED', (await inspectorView()).bindingDisabled === false);
  };
  const cases = {
    async entry() {
      await fixture({board:true});
      await openNew('R01 visible entry');
      check('ENTRY_LABEL', await page(() => document.getElementById('igCardRef').textContent.includes('長度來源')));
      const before = await dump();
      await map(10, 3, 8);
      check('ENTRY_MAPPING_CONTROLS', await visible('#igCardU') && await visible('#igCardV') && await visible('#igCardSwap'));
      check('ENTRY_LENGTH_READONLY', await page(() =>
        document.getElementById('igUStep').readOnly && document.getElementById('igVStep').readOnly &&
        document.getElementById('igUStep').value === '915' && document.getElementById('igVStep').value === '1830' &&
        document.getElementById('igUStepSource').disabled && document.getElementById('igVStepSource').disabled));
      check('ENTRY_SELECTION_IS_DRAFT', (await dump()) === before && (await objects()).gridSystems.length === 0);
      await send('Emulation.setDeviceMetricsOverride', {width:390,height:844,deviceScaleFactor:1,mobile:true});
      await ctl('#igCardSwap');
      check('ENTRY_MOBILE_SWAP', same(await mapping(), {card:'10',u:'8',v:'3'}), await mapping());
      check('ENTRY_MOBILE_NO_PAGE_OVERFLOW', await page(() => document.documentElement.scrollWidth <= innerWidth));
    },
    async explicit_mapping() {
      await fixture();
      await openNew('R01 explicit map');
      await choose('#igCard', 10);
      const initial = await mapping();
      check('MAPPING_REQUIRES_EXPLICIT_TWO_FIELDS', initial.card === '10' && initial.u === '' && initial.v === '', initial);
      await choose('#igCardU', 3);
      check('MAPPING_ONE_AXIS_REMAINS_INCOMPLETE', (await mapping()).v === '');
      await choose('#igCardV', 8);
      check('MAPPING_UV_IDS_EXPLICIT', same(await mapping(), {card:'10',u:'3',v:'8'}));
      const p = await preview('EXPLICIT');
      check('MAPPING_NATIVE_EXPLICIT', p.gridSystems.some(row => identity(row.after, 10, 3, 8)), p.gridSystems);
      await cancel();
    },
    async commit_cancel() {
      await fixture();
      await newCardGrid();
      const before = await dump(), beforeRaw = await raw(), pin = await pinHistory();
      const state = await page(() => ReferenceWorkspace.getProjectState());
      const p = await preview('CREATE');
      check('CREATE_NATIVE_CARD_SOURCE', p.gridSystems.some(row => row.before === null && identity(row.after, 10, 3, 8)), p.gridSystems);
      check('PREVIEW_NO_PUBLISH', (await dump()) === before && await history.unchanged(pin));
      await cancel();
      check('CANCEL_WORLD_RAW_HISTORY', (await dump()) === before && same(await raw(), beforeRaw) &&
        await history.unchanged(pin) && same(await page(() => ReferenceWorkspace.getProjectState()), state));
      await preview('CREATE_AGAIN');
      await confirm();
      const g = await addedSource('R01 create');
      await assertIdentity('CREATE_ONE_CARD_REFERENCE', g.id, 10, 3, 8);
      check('CREATE_HAND_ORACLE', same(await nativeLines(g.id), {u:[-17,-5,7],v:[-23,7,37]}));
      check('CREATE_CLEARS_MATCHING_DRAFT', (await allRaw()).drafts.every(draft => draft.draftId !== beforeRaw.draftId));
      await releasePin(pin);
    },
    async swap() {
      await fixture({source:true,mixed:true});
      await openSource(4);
      const before = await source(4);
      await ctl('#igCardSwap');
      check('SWAP_MAPPING_ONLY', same(await mapping(), {card:'10',u:'8',v:'3'}), await mapping());
      const p = await preview('SWAP');
      const next = p.gridSystems.find(row => row.id === 4)?.after;
      check('SWAP_CANDIDATE_KEEP_AXES', identity(next,10,8,3) && next.uDefinition.source === 'repeat-panel' &&
        next.uDefinition.gap === before.uDefinition.gap && next.uDefinition.anchor === before.uDefinition.anchor &&
        next.vDefinition.phase === before.vDefinition.phase && next.mainAlong === before.mainAlong, next);
      await confirm();
      await assertIdentity('SWAP_FORMAL_MAPPING', 4, 10, 8, 3);
      check('SWAP_HAND_ORACLE', same(await nativeLines(4), {u:[-7,26,59],v:[-5,7,19]}));
    },
    async equal_swap() {
      await fixture({source:true,equal:true});
      await openSource(4);
      const before = await source(4), lines = await nativeLines(4);
      const graph = await query('source-inspect'), oldNode = graph.nodes.find(node => node.key === 'grid-system:4');
      await ctl('#igCardSwap');
      check('EQUAL_SWAP_STILL_DIRTY', same(await mapping(), {card:'20',u:'8',v:'3'}) &&
        await page(() => !document.getElementById('igSaveSource').disabled));
      await preview('EQUAL');
      const impact = await page(() => document.querySelector('[data-impact-system="4"]')?.textContent || '');
      await confirm();
      const after = await assertIdentity('EQUAL_SWAP_FORMAL_IDENTITY', 4, 20, 8, 3);
      const newNode = (await query('source-inspect')).nodes.find(node => node.key === 'grid-system:4');
      check('EQUAL_SWAP_NATIVE_FINGERPRINT', !!oldNode && !!newNode &&
        oldNode.definitionFingerprint !== newNode.definitionFingerprint &&
        oldNode.valueFingerprint === newNode.valueFingerprint && same(await nativeLines(4), lines));
      check('SOURCE_KEY_INCLUDES_MAPPING', P.Features.gridSourceKey(before) !== P.Features.gridSourceKey(after), {before,after});
      check('EQUAL_SWAP_IMPACT_IDENTITY', impact.includes('first-listed') && impact.includes('second-listed') &&
        impact.includes('原：') && impact.includes('新：'), impact);
    },
    async reopen() {
      await fixture({source:true,mixed:true});
      await openSource(4);
      await ctl('#igCardSwap');
      await preview('REOPEN_SWAP');
      await confirm();
      const before = await dump();
      await openSource(4);
      check('REOPEN_MAPPING', same(await mapping(), {card:'10',u:'8',v:'3'}), await mapping());
      check('REOPEN_EFFECTIVE_NOT_FALLBACK', await page(() =>
        document.getElementById('igUPanel').value === '30' && document.getElementById('igVStep').value === '12' &&
        document.getElementById('igUPanel').readOnly && document.getElementById('igVStep').readOnly &&
        document.getElementById('igSaveSource').disabled && !document.getElementById('igCardNote').textContent.includes('600')));
      check('REOPEN_NO_PUBLISH_OR_DRAFT', (await dump()) === before && (await allRaw()).drafts.length === 0);
      await fill('#igName', 'R01 rename preserving source');
      await preview('RENAME');
      await confirm();
      await assertIdentity('RENAME_KEEP_CARD_SOURCE',4,10,8,3);
      check('RENAME_ONLY', (await source(4)).name === 'R01 rename preserving source' &&
        same(await nativeLines(4), {u:[-7,26,59],v:[-5,7,19]}));
    },
    async native_rejection() {
      await fixture({source:true});
      await openSource(4);
      await choose('#igCardV', 3);
      const before = await dump(), savedRaw = await raw(), pin = await pinHistory();
      await rejectedAttempt('SAME_FIELD');
      check('SAME_FIELD_UI_REJECT', await page(() =>
        /I74|不同/.test(document.getElementById('igCardNote').textContent + document.getElementById('igDraftNote').textContent)) &&
        (await dump()) === before && await history.unchanged(pin) && same(await raw(), savedRaw));
      await leave();
      for (const [code, ref, reason] of [
        ['SAME_FIELD', {parameterId:10,uFieldId:3,vFieldId:3}, 'DISTINCT_FIELDS'],
        ['CROSS_CARD', {parameterId:10,uFieldId:3,vFieldId:8,vParameterId:20}, 'SAME_CARD'],
        ['WRONG_TYPE', {parameterId:30,uFieldId:3,vFieldId:8}, 'not a dimension']
      ]) {
        const world = await dump(), hp = await pinHistory();
        const p = await operationsPreview([{op:'set-grid-card-reference',id:4,value:ref}]);
        check('NATIVE_' + code + '_REJECT', p.valid === false &&
          p.violations.some(item => String(item.message).includes(reason)), p);
        const result = await page(token => apiRequest('engineering-confirm ' + token), p.token);
        check('NATIVE_' + code + '_NO_COMMIT', result.ok === false && (await dump()) === world && await history.unchanged(hp), result);
        await query('engineering-cancel ' + p.token); nativeTokens = nativeTokens.filter(token => token !== p.token);
        await releasePin(hp);
      }
      await releasePin(pin);
      await openSource(4);
      await choose('#igCardU', 8); await choose('#igCardV', 3);
      await preview('DISTINCT_FIELDS'); await confirm();
      await assertIdentity('DISTINCT_FIELDS_ACCEPTED',4,10,8,3);
      await choose('#igCard',20); await map(10,8,3);
      await fill('#igName','R01 raw with missing source evidence');
      const evidenceDraft = await raw(), saved = await saveFile();
      need('MISSING_PIN_FIXTURE_HAS_TWO_PINS', evidenceDraft.inputRefs.filter(ref =>
        ref.kind === 'parameter-field' && ref.parameterId === 10).length === 2, evidenceDraft);
      const manifest = structuredClone(saved.loaded.manifest);
      const record = manifest.featureAttachments.records.find(item => item.kind === 'grid-draft');
      const withoutPins = record.value.schema === P.Features.GRID_DRAFTS_SCHEMA ? record.value.drafts[0] : record.value;
      withoutPins.inputRefs = [];
      const file = path.join(saved.directory,'missing-card-pins.gcanvas');
      fs.writeFileSync(file,await P.pack(saved.loaded.scene,manifest,saved.loaded.sources,zip));
      await openFile(file,manifest.projectId);
      await openDraft(evidenceDraft.draftId);
      const missing = await raw(), missingWorld = await dump(), missingHistory = await pinHistory();
      check('MISSING_PINS_NOT_RECONSTRUCTED', missing.inputRefs.length === 0 &&
        same(await mapping(),{card:'10',u:'8',v:'3'}),missing);
      await rejectedAttempt('MISSING_PINS');
      check('MISSING_CARD_PINS_BLOCK_PUBLISH', !await visible('.reference-impact[open]') &&
        (await dump()) === missingWorld && same(await raw(),missing) && await history.unchanged(missingHistory) &&
        await page(() => /證據|來源|重新.*選/.test(document.getElementById('igStatus').textContent)),await raw());
      await releasePin(missingHistory);
    },
    async raw_roundtrip() {
      await fixture();
      await newCardGrid('  R01 raw <&>  ');
      await fill('#igUPhase', ' - ');
      const draft = await raw(), scene = await dump();
      check('RAW_SOURCE_MAPPING', draft.rawForm.igCard === '10' && draft.rawForm.igCardU === '3' &&
        draft.rawForm.igCardV === '8' && draft.rawForm.igUPhase === ' - ' && draft.rawForm.igName === '  R01 raw <&>  ', draft);
      check('RAW_TYPED_PINS', [3,8].every(id => draft.inputRefs.some(ref => ref.kind === 'parameter-field' &&
        ref.parameterId === 10 && ref.fieldId === id && /^[0-9a-f]{64}$/.test(ref.fingerprint))), draft.inputRefs);
      const saved = await saveFile(), stored = fromArchive(saved.loaded).drafts;
      check('RAW_ARCHIVE_EXACT', saved.loaded.scene === scene && same(stored,[draft]));
      await openFile(saved.file, saved.loaded.manifest.projectId);
      check('RAW_OPEN_WORLD_UNCHANGED', (await dump()) === scene && same((await allRaw()).drafts,[draft]));
      await openDraft(draft.draftId);
      check('RAW_RESTORE_EXACT', same(await raw(),draft) && await page(() =>
        document.getElementById('igUPhase').value === ' - ' && document.getElementById('igName').value === '  R01 raw <&>  '));
      // Deliberately invalid portable raw is a fixture, not a UI edit or a native source.
      // Re-pack through the real writer so archive checksums/capabilities are genuine.
      const manifest = structuredClone(saved.loaded.manifest);
      const record = manifest.featureAttachments.records.find(item => item.kind === 'grid-draft');
      const invalid = record.value.schema === P.Features.GRID_DRAFTS_SCHEMA ? record.value.drafts[0] : record.value;
      invalid.rawForm.igCardU = '999';
      const invalidFile = path.join(saved.directory,'unknown-field-raw.gcanvas');
      fs.writeFileSync(invalidFile, await P.pack(saved.loaded.scene,manifest,saved.loaded.sources,zip));
      await openFile(invalidFile, manifest.projectId);
      await openDraft(draft.draftId);
      check('RAW_UNKNOWN_FIELD_NOT_REPLACED', await page(() => document.getElementById('igCardU').value === '999') &&
        (await raw()).rawForm.igCardU === '999' && (await dump()) === scene);
    },
    async archive_roundtrip() {
      await fixture({board:true});
      await newCardGrid('R01 saved board');
      await preview('ARCHIVE_CREATE'); await confirm();
      const g = await addedSource('R01 saved board');
      const before = await dump(), row = await source(g.id);
      const saved = await saveFile();
      check('ARCHIVE_CAPABILITIES', saved.loaded.manifest.format === P.CARD_FORMAT &&
        ['parameters/1','grid-card-reference/1'].every(cap => saved.loaded.manifest.requiredCapabilities.includes(cap) &&
          saved.loaded.scene.includes('requires ' + cap + '\n')), saved.loaded.manifest);
      check('ARCHIVE_SOURCE_NOT_CACHE', saved.loaded.scene === before &&
        saved.loaded.scene.includes(' card-reference 10 3 8 ') &&
        !saved.loaded.scene.includes('effectiveStep') && !saved.loaded.scene.includes('grid-query '));
      await openFile(saved.file,saved.loaded.manifest.projectId);
      check('ARCHIVE_FORMAL_REOPEN', (await dump()) === before && same((await source(g.id)).cardReference,row.cardReference));
      await openSource(g.id);
      check('ARCHIVE_UI_RESTORED', same(await mapping(),{card:'10',u:'3',v:'8'}) && await page(() =>
        document.getElementById('igUStep').value === '915' && document.getElementById('igVStep').value === '1830' &&
        document.getElementById('igSaveSource').disabled));
      await assertIdentity('ARCHIVE_CARD_REFERENCE',g.id,10,3,8);
    },
    async history() {
      await fixture();
      await newCardGrid('R01 one history step');
      const before = await dump(), draft = await raw(), pin = await pinHistory();
      await preview('HISTORY'); await confirm();
      const g = await addedSource('R01 one history step'), after = await dump();
      check('CONFIRM_AND_DRAFT_ONE_STEP', await history.single(pin) && (await allRaw()).drafts.length === 0);
      await releasePin(pin); await leave();
      await ctl('#btnUndo'); await settled();
      check('UNDO_WORLD_AND_RAW_TOGETHER', (await dump()) === before && same((await allRaw()).drafts,[draft]));
      await ctl('#btnRedo'); await settled();
      check('REDO_WORLD_AND_RAW_TOGETHER', (await dump()) === after && (await allRaw()).drafts.length === 0);
      await assertIdentity('HISTORY_REDO_CARD_SOURCE',g.id,10,3,8);
    },
    async lost_source() {
      await fixture();
      await newCardGrid('R01 lost card');
      const draftId = (await raw()).draftId;
      await leave();
      await applyFixture([{op:'delete-parameter',id:10}]);
      let retained = (await allRaw()).drafts.find(d => d.draftId === draftId);
      check('DELETED_CARD_PINS_LOST', retained.inputRefs.filter(ref => ref.kind === 'parameter-field' &&
        ref.parameterId === 10 && ref.lost === true).length === 2, retained);
      await applyFixture([parameter(10,12,30)]);
      await openDraft(draftId);
      const before = await dump(), pin = await pinHistory();
      await rejectedAttempt('LOST_SOURCE');
      retained = await raw();
      check('RECREATED_CARD_NOT_REATTACHED', retained.inputRefs.filter(ref => ref.parameterId === 10 && ref.lost === true).length === 2 &&
        (await dump()) === before && await history.unchanged(pin) &&
        !await page(() => !!document.querySelector('.reference-impact[open]')), retained);
      await releasePin(pin);
      await discardRaw();
      // A separate valid restored draft must release old, non-lost card pins when
      // its user explicitly selects another card. Stale pins are not a dependency.
      await newCardGrid('R01 restored repoint');
      const rawBefore = await raw(), saved = await saveFile();
      await openFile(saved.file,saved.loaded.manifest.projectId);
      await openDraft(rawBefore.draftId);
      await map(20,3,8);
      const changed = await raw();
      check('REPLACED_CARD_PINS_RELEASED', changed.inputRefs.filter(ref => ref.kind === 'parameter-field' &&
        ref.parameterId === 20).length === 2 && !changed.inputRefs.some(ref => ref.kind === 'parameter-field' &&
        ref.parameterId === 10), changed.inputRefs);
    },
    async stale_preview() {
      await fixture({source:true});
      await openSource(4); await fill('#igName','R01 candidate before race');
      await preview('STALE');
      const draft = await raw();
      // Explicit external edit after the real UI preview, through the real native bridge.
      const write = await query('line spec R01CandidateRace 1');
      need('RACE_FIXTURE_COMMITTED', !write.preview, write);
      const afterRace = await dump(), pin = await pinHistory();
      const cursor = await page(() => window.__p353ApiTrace.calls.length);
      const control = await page(() => {
        const button = document.querySelector('.reference-impact[open] #impact-confirm');
        return {exists:!!button,disabled:!!button?.disabled};
      });
      const mode = !control.exists ? 'retired' : control.disabled ? 'disabled' : 'clicked';
      if (mode === 'clicked') await confirm();
      const confirms = await page(start => window.__p353ApiTrace.calls.slice(start)
        .filter(row => row.command.startsWith('line confirm ') || row.command.startsWith('engineering-confirm ')),cursor);
      check('STALE_CONFIRM_NO_OVERWRITE', (await dump()) === afterRace && same(await raw(),draft) &&
        await history.unchanged(pin) && (await source(4)).name === 'R01 existing 4' &&
        (mode === 'clicked' || confirms.length === 0),{mode,confirms});
      await releasePin(pin);
    },
    async binding_effective() {
      await fixture({source:true,mixed:true});
      const boundary = await query('line boundary 301 outline 100,200 250,200 250,500 100,500');
      need('BINDING_BOUNDARY_FIXTURE', !boundary.preview,boundary);
      need('BINDING_FIXTURE_RENDERED', await page(() => renderObjects()));
      const original = await source(4), before = await dump();
      need('BINDING_NATIVE_CONTROLLED_SLOTS', identity(original,10,3,8) &&
        original.uDefinition.effectivePanel === 12 && original.vDefinition.effectiveStep === 30,original);
      await openSource(4);
      check('BINDING_ENTRY_ENABLED', await visible('#igNewBinding') &&
        await page(() => !document.getElementById('igNewBinding').disabled));
      await ctl('#igNewBinding');
      await wait("!!document.getElementById('infiniteGridWorkspace')?.open&&!!document.getElementById('igBoundary')&&!document.getElementById('igBoundary').disabled");
      const rendered = await page(() => {
        const view = document.getElementById('igGridView');
        return {u:view.querySelectorAll('line[data-ig-axis="u"]').length,
          v:view.querySelectorAll('line[data-ig-axis="v"]').length,
          text:view.textContent,zoom:document.getElementById('igZoom').textContent};
      });
      check('BINDING_EFFECTIVE_AXES_RENDERED', rendered.u > 0 && rendered.v > 0 &&
        rendered.zoom.includes('15×30') && !/NaN|undefined|BigInt/.test(rendered.text),rendered);
      await choose('#igBoundary',301);
      await wait('!!document.querySelector(' + JSON.stringify('[data-ig-vertex="outer:0"]') + ')');
      await ctl('[data-ig-vertex="outer:0"]');
      await fill('#igCellI','0'); await fill('#igCellJ','0'); await ctl('#igLocateCell');
      const lines = await nativeLines(4);
      check('BINDING_SOURCE_HAND_ORACLE',same(lines,{u:[-7,8,23],v:[-23,7,37]}),lines);
      const geometry = await page(() => {
        const view = document.getElementById('igGridView'),plot=view.querySelector('[data-ig-plot]');
        const camera = view.dataset.igCamera.split(' ').map(Number);
        const number = (node,attribute) => node ? Number(node.getAttribute(attribute)) : null;
        return {camera,scale:number(plot,'width')/(camera[2]-camera[0]),x:number(plot,'x'),y:number(plot,'y'),
          u:['-1','0','1'].map(index=>number(view.querySelector('line[data-ig-axis="u"][data-ig-index="'+index+'"]'),'x1')),
          v:['-1','0','1'].map(index=>number(view.querySelector('line[data-ig-axis="v"][data-ig-index="'+index+'"]'),'y1'))};
      });
      check('BINDING_DRAW_MATCHES_NATIVE', Number.isFinite(geometry.scale) && geometry.scale > 0 &&
        ['u','v'].every((axis,a) => lines[axis].every((coordinate,index) =>
          geometry[axis][index] !== null && Math.abs(geometry[axis][index] -
            ((a === 0 ? geometry.x : geometry.y) + (coordinate-geometry.camera[a])*geometry.scale)) < 0.02)),geometry);
      await fill('#igCellI','-1'); await fill('#igCellJ','1'); await ctl('#igLocateCell');
      await ctl('[data-ig-anchor="0,0"]');
      check('BINDING_LOCATE_SIGNED_CELL',await page(() => {
        const selected = document.querySelector('#igGridView [data-ig-cell="-1,1"]');
        return !!selected && ['x','y','width','height'].every(key => Number.isFinite(Number(selected.getAttribute(key)))) &&
          document.getElementById('igCellI').value === '-1' && document.getElementById('igCellJ').value === '1';
      }));
      const p = await preview('BINDING',{button:'#igSaveBinding',command:'line preview grid-binding '});
      const candidate = p.gridBindings.find(row=>row.before === null)?.after;
      check('BINDING_CANDIDATE_EXACT',!!candidate && candidate.system === 4 && candidate.boundary === 301 &&
        same(candidate.cell,['-1','1']) && same(candidate.translation,[107,163]) && (await dump()) === before,candidate);
      await confirm();
      const saved = (await objects()).gridBindings.filter(row=>row.system === 4 && row.boundary === 301);
      check('BINDING_COMMIT_EXACT',saved.length === 1 && same(saved[0].cell,['-1','1']) &&
        same(saved[0].translation,[107,163]) && identity(await source(4),10,3,8),saved);
      await leave(); await ctl('#btnZoom');
      await ctl('.ocard[data-kind="grid-binding"][data-id="'+saved[0].id+'"]');
      await ctl('#gridObjectOpen');
      await wait("document.getElementById('infiniteGridWorkspace')?.open&&document.getElementById('igVertex')?.value!==''");
      await waitProduct('BINDING_REOPEN_RESULT', 'document.querySelectorAll("#igResultView [data-ig-result-axis]").length>0');
      check('BINDING_REOPEN_RESULT', await page(() =>
        document.getElementById('igCellI').value === '-1' && document.getElementById('igCellJ').value === '1' &&
        document.querySelectorAll('#igGridView [data-ig-axis="u"]').length > 0 &&
        document.querySelectorAll('#igGridView [data-ig-axis="v"]').length > 0));
    },
    async pin_preserve_untouched() {
      const before = await staleCardDraft(), scene = await dump();
      await choose('#igCardU',14);
      const after = await raw();
      check('UNTOUCHED_AXIS_PIN_RETAINED', same(fieldPin(after,10,8),fieldPin(before,10,8)) &&
        after.rawForm.igVStep === before.rawForm.igVStep && after.rawForm.igCardV === '8' &&
        after.rawForm.igCardU === '14', {before,after});
      const pin = await pinHistory();
      await rejectedAttempt('UNTOUCHED_STALE');
      check('UNTOUCHED_STALE_PREVIEW_REJECTED', !await visible('.reference-impact[open]') &&
        same(await raw(),after) && (await dump()) === scene && await history.unchanged(pin));
      await releasePin(pin);
    },
    async pin_reacquire_cancel() {
      const before = await staleCardDraft(), scene = await dump(), pin = await pinHistory();
      await reacquireStale(before,false);
      check('REACQUIRE_CANCEL_RAW_PINS_UNCHANGED', same(await raw(),before) &&
        same(await mapping(),{card:'10',u:'3',v:'8'}) && (await dump()) === scene && await history.unchanged(pin), await raw());
      await releasePin(pin);
    },
    async pin_reacquire_confirm() {
      const before = await staleCardDraft(), actual = await reacquireStale(before,true);
      check('REACQUIRE_CONFIRM_NEW_EVIDENCE', same(fieldPin(await raw(),10,8),actual) &&
        same(await mapping(),{card:'10',u:'8',v:'8'}), await raw());
      await choose('#igCardU',14);
      check('REACQUIRE_EXPLICIT_FINAL_MAPPING', same(await mapping(),{card:'10',u:'14',v:'8'}) &&
        same(fieldPin(await raw(),10,8),actual));
      await preview('REACQUIRED'); await confirm();
      const saved = await addedSource('R353 stale other axis');
      const g = await assertIdentity('REACQUIRED_COMMITTED_CARD',saved.id,10,14,8);
      check('REACQUIRED_EFFECTIVE_LENGTHS', g.uDefinition.effectiveStep === 45 && g.vDefinition.effectiveStep === 60, g);
    },
    async pin_shared_consumers() {
      await fixture(); await applyFixture([threeFieldParameter(30)]);
      await newCardGrid('R353 shared phase and card');
      await choose('#igUPhaseSource','10:3');
      const original = await raw();
      need('SHARED_FIXTURE_CARD_AND_PHASE', original.rawForm.igCardU === '3' &&
        original.rawForm.igUPhaseSource === '10:3' && !!fieldPin(original,10,3), original);
      await leave(); await applyFixture([threeFieldParameter(30,24)]); await openDraft(original.draftId);
      const stale = await raw();
      await choose('#igUPhaseSource','');
      const phaseLeft = await raw();
      check('SHARED_CARD_PIN_SURVIVES_PHASE_RELEASE', same(fieldPin(phaseLeft,10,3),fieldPin(stale,10,3)) &&
        phaseLeft.rawForm.igUPhaseSource === '' && phaseLeft.rawForm.igCardU === '3', {stale,phaseLeft});
      await choose('#igCardU',14);
      check('SHARED_LAST_CARD_USER_RELEASES_PIN', !fieldPin(await raw(),10,3), await raw());
      // The opposite order must count the per-field user too. Fresh selection
      // is explicit here, after the old pin's final user has already left.
      await choose('#igUPhaseSource','10:3'); await choose('#igCardU',3);
      const fresh = await raw();
      await choose('#igCardU',14);
      const cardLeft = await raw();
      check('SHARED_PHASE_PIN_SURVIVES_CARD_RELEASE', same(fieldPin(cardLeft,10,3),fieldPin(fresh,10,3)) &&
        cardLeft.rawForm.igUPhaseSource === '10:3' && cardLeft.rawForm.igCardU === '14', cardLeft);
      await choose('#igUPhaseSource','');
      check('SHARED_LAST_PHASE_USER_RELEASES_PIN', !fieldPin(await raw(),10,3), await raw());
      await preview('SHARED_PIN_RELEASE'); await cancel();
    },
    async lost_card_existing_pins() {
      await fixture(); await newCardGrid('R353 lost A to shared B');
      await choose('#igUPhaseSource','20:3'); await choose('#igVPhaseSource','20:8');
      const owned = await raw();
      await leave(); await applyFixture([{op:'delete-parameter',id:10}]);
      const lost = (await allRaw()).drafts.find(d => d.draftId === owned.draftId);
      need('LOST_SHARED_FIXTURE', lost.inputRefs.filter(ref => ref.parameterId === 10 && ref.lost).length === 2 &&
        !!fieldPin(lost,20,3) && !!fieldPin(lost,20,8), lost);
      await openDraft(lost.draftId);
      await choose('#igCard',20);
      check('REPOINT_CARD_CHOICE_NOT_PARTIAL_WRITE', same(await raw(),lost), await raw());
      await choose('#igCardU',3);
      check('REPOINT_ONE_AXIS_NOT_PARTIAL_WRITE', same(await raw(),lost), await raw());
      await choose('#igCardV',8);
      const replaced = await raw();
      check('REPOINT_EXISTING_PINS_ATOMIC_COMPLETE', replaced.rawForm.igCard === '20' &&
        replaced.rawForm.igCardU === '3' && replaced.rawForm.igCardV === '8' &&
        replaced.rawForm.igUPhaseSource === '20:3' && replaced.rawForm.igVPhaseSource === '20:8' &&
        replaced.inputRefs.length === 2 && same(fieldPin(replaced,20,3),fieldPin(lost,20,3)) &&
        same(fieldPin(replaced,20,8),fieldPin(lost,20,8)) && !replaced.inputRefs.some(ref => ref.parameterId === 10), replaced);
      await preview('REPOINT_SHARED'); await confirm();
      const saved = await addedSource('R353 lost A to shared B');
      const after = await assertIdentity('REPOINT_SHARED_NATIVE_IDENTITY',saved.id,20,3,8);
      check('REPOINT_SHARED_PHASE_SOURCES', same(after.uDefinition.parameterRefs.phase,{kind:'parameter',parameterId:20,fieldId:3}) &&
        same(after.vDefinition.parameterRefs.phase,{kind:'parameter',parameterId:20,fieldId:8}), after);
    },
    async lost_card_same_id_rebuild() {
      await fixture(); await newCardGrid('R353 same id remains lost');
      const owned = await raw();
      await leave(); await applyFixture([{op:'delete-parameter',id:10}]); await applyFixture([parameter(10,12,30)]);
      await openDraft(owned.draftId);
      const lost = await raw(), scene = await dump();
      need('SAME_ID_FIXTURE_TOMBSTONE', lost.inputRefs.filter(ref => ref.parameterId === 10 && ref.lost).length === 2, lost);
      await choose('#igCard',20); await choose('#igCard',10,{waitForValue:false});
      check('SAME_ID_EXPLICIT_RESELECT_REFUSED', (await mapping()).card === '20' && same(await raw(),lost), await raw());
      await openDraft(owned.draftId); await rejectedAttempt('SAME_ID_REBUILD');
      check('SAME_ID_REBUILD_STILL_LOST', same(await raw(),lost) && (await dump()) === scene &&
        !await visible('.reference-impact[open]'), await raw());
    },
    async card_render_repeat_repeat() { await renderEffective('repeat_repeat'); },
    async card_render_repeat_panel() { await renderEffective('repeat_panel'); },
    async card_render_panel_panel() { await renderEffective('panel_panel'); },
    async inspector_repeat_repeat() { await inspectorEffective('repeat_repeat'); },
    async inspector_repeat_panel() { await inspectorEffective('repeat_panel'); },
    async inspector_panel_panel() { await inspectorEffective('panel_panel'); },
    async inspector_direct_control() {
      await effectiveWorld('repeat_repeat'); await openInspector(5);
      const ui = await inspectorView(), before = await source(5);
      check('INSPECTOR_DIRECT_EDITABLE', ui.fields.length === 2 && ui.fields[0].value === '600' &&
        ui.fields[1].value === '1200' && ui.fields.every(field => field.readonly === false) && ui.bindingDisabled === false, ui);
      await fill('#giName','R353 direct edited'); await fill('#giUStep','650');
      check('INSPECTOR_DIRECT_DIRTY', (await inspectorView()).bindingDisabled === true);
      await preview('INSPECTOR_DIRECT',{button:'#giPreview',inspectCommand:command =>
        check('INSPECTOR_DIRECT_LITERAL_COMMAND', !command.includes('card-reference') && / u repeat -137 650 v repeat 211 1200$/.test(command), command)});
      await confirm();
      const after = await source(5);
      check('INSPECTOR_DIRECT_EDIT_COMMITTED', after.name === 'R353 direct edited' && !after.cardReference &&
        after.uDefinition.step === 650 && after.uDefinition.phase === before.uDefinition.phase &&
        same(after.vDefinition,before.vDefinition), after);
    },
    async compat_raw_capability() {
      await fixture();
      await newCardGrid('R353 raw capability');
      await fill('#igUPhase',' - ');
      const draft = await raw(), world = await dump(), saved = await saveFile();
      check('COMPAT_RAW_CAPABILITY_DECLARED', saved.loaded.manifest.requiredCapabilities.includes('grid-card-draft/1'), saved.loaded.manifest);
      check('COMPAT_RAW_ONLY_MATRIX', saved.loaded.manifest.format === P.FEATURE_FORMAT &&
        !saved.loaded.manifest.requiredCapabilities.includes('grid-card-reference/1') &&
        !saved.loaded.scene.includes('requires grid-card-draft/1') && same(fromArchive(saved.loaded).drafts,[draft]));
      for (const [name, values] of [['empty',['','','']],['unknown',['10','999','8']]]) {
        const manifest = structuredClone(saved.loaded.manifest);
        const record = manifest.featureAttachments.records.find(item => item.kind === 'grid-draft');
        const value = record.value.schema === P.Features.GRID_DRAFTS_SCHEMA ? record.value.drafts[0] : record.value;
        ['igCard','igCardU','igCardV'].forEach((field,index) => {value.rawForm[field] = values[index];});
        const file = await writeArchive(saved,'raw-' + name,manifest);
        const loaded = await P.unpack(new Uint8Array(fs.readFileSync(file)),zip);
        check('COMPAT_RAW_PROPERTY_PRESENCE_' + name.toUpperCase(), loaded.manifest.requiredCapabilities.includes('grid-card-draft/1'));
        await openFile(file,manifest.projectId);
        check('COMPAT_RAW_PORTABLE_' + name.toUpperCase(), same((await allRaw()).drafts,[value]) && (await dump()) === world);
      }
    },
    async compat_legacy_unchanged() {
      let legacy;
      try {legacy = require('../tests/pr353_legacy_reader.js').loadLegacyReader();}
      catch (error) {throw failure('precondition','COMPAT_LEGACY_READER_SOURCE',error.message);}
      for (const rules of [false,true]) {
        if (rules) await cleanup();
        await fixture();
        if (rules) {
          await applyFixture([{op:'put-grid-system',value:{id:4,name:'R353 legacy direct',mainAlong:'none',u:'repeat -5 12',v:'repeat 7 30'}}]);
          await openSource(4);
          // Create the /2 editing session before any /1 draft exists. This
          // compatibility test does not silently replace an existing base pin.
          await ctl('#igRuleAdd');
          await wait("!document.getElementById('igRuleEditor').hidden");
        } else await openNew('  R353 legacy raw  ');
        await choose('#igUStepSource','10:3');
        if (rules) {
          await fill('#igRuleName','  legacy rule  ');
          await fill('#igRuleU',' - ');
        } else await fill('#igVPhase',' - ');
        const draft = await raw(), world = await dump(), saved = await saveFile();
        check('COMPAT_LEGACY_CARDLESS_' + rules, !['igCard','igCardU','igCardV'].some(field => Object.hasOwn(draft.rawForm,field)) &&
          !saved.loaded.manifest.requiredCapabilities.includes('grid-card-draft/1') &&
          draft.schema === (rules ? 'grid-editor-draft/2' : 'grid-editor-draft/1'),draft);
        const oldFile = await writeArchive(saved,rules ? 'legacy-v2' : 'legacy-v1',saved.loaded.manifest,legacy);
        const oldLoaded = await legacy.unpack(new Uint8Array(fs.readFileSync(oldFile)),zip);
        check('COMPAT_LEGACY_REAL_WRITER_' + rules, same(fromArchive(oldLoaded).drafts,[draft]) && oldLoaded.scene === world);
        await openFile(oldFile,oldLoaded.manifest.projectId);
        check('COMPAT_LEGACY_OPEN_EXACT_' + rules, same((await allRaw()).drafts,[draft]) && (await dump()) === world);
        await openDraft(draft.draftId);
        check('COMPAT_LEGACY_RESTORE_EXACT_' + rules, same(await raw(),draft),await raw());
      }
    },
    async compat_raw_rule_roundtrip() {
      await fixture();
      await applyFixture([{op:'put-grid-system',value:{id:4,name:'R353 raw-only rule base',mainAlong:'none',u:'repeat -5 12',v:'repeat 7 30'}}]);
      await openSource(4);
      await ctl('#igRuleAdd');
      await wait("!document.getElementById('igRuleEditor').hidden");
      await map(10,3,8);
      await fill('#igRuleName','  R353 raw rule <&>  ');
      await fill('#igRuleU',' - ');
      const draft = await raw(), world = await dump();
      check('COMPAT_RULE_RAW_CAPTURE', draft.schema === 'grid-editor-draft/2' &&
        draft.ruleDraft?.rawForm.name === '  R353 raw rule <&>  ' && draft.ruleDraft.rawForm.divisionsU === ' - ' &&
        draft.rawForm.igCard === '10' && draft.rawForm.igCardU === '3' && draft.rawForm.igCardV === '8',draft);
      const saved = await saveFile();
      check('COMPAT_RULE_RAW_MATRIX', saved.loaded.manifest.format === P.GRID_RULE_FORMAT &&
        ['grid-editor-draft/2','grid-card-draft/1'].every(cap => saved.loaded.manifest.requiredCapabilities.includes(cap)) &&
        !saved.loaded.manifest.requiredCapabilities.includes('grid-card-reference/1') && same(fromArchive(saved.loaded).drafts,[draft]));
      await openFile(saved.file,saved.loaded.manifest.projectId);
      await openDraft(draft.draftId);
      check('COMPAT_RULE_RAW_REOPEN_EXACT', same(await raw(),draft) && (await dump()) === world && await page(() =>
        document.getElementById('igRuleU').value === ' - ' && document.getElementById('igRuleName').value === '  R353 raw rule <&>  '));
    },
    async compat_mixed_roundtrip() {
      await fixture({source:true});
      const original = await source(4);
      await newCardGrid('R353 mixed raw');
      await fill('#igUPhase',' - ');
      const draft = await raw(), world = await dump(), saved = await saveFile();
      check('COMPAT_MIXED_MATRIX', saved.loaded.manifest.format === P.CARD_FORMAT &&
        ['parameters/1','grid-card-reference/1','grid-card-draft/1'].every(cap => saved.loaded.manifest.requiredCapabilities.includes(cap)) &&
        saved.loaded.scene.includes('requires grid-card-reference/1') && !saved.loaded.scene.includes('requires grid-card-draft/1'),saved.loaded.manifest);
      await openFile(saved.file,saved.loaded.manifest.projectId);
      check('COMPAT_MIXED_FORMAL_REOPEN', (await dump()) === world && same((await source(4)).cardReference,original.cardReference) &&
        same((await allRaw()).drafts,[draft]));
      await openDraft(draft.draftId);
      check('COMPAT_MIXED_RAW_RESTORE', same(await raw(),draft),await raw());
    },
    async compat_reader_rejection_atomic() {
      await fixture();
      await newCardGrid('R353 incompatible raw');
      const saved = await saveFile();
      const entries = zip.unzipSync(saved.bytes);
      const manifest = JSON.parse(new TextDecoder().decode(entries['manifest.json']));
      // Corrupt only the declaration, keeping the real file's scene/hash/raw.
      // This exercises the current app's formal Open staging path. The fixed
      // 405f8c5 reader itself is tested separately with its verified originals.
      manifest.requiredCapabilities = manifest.requiredCapabilities.filter(cap => cap !== 'grid-card-draft/1');
      entries['manifest.json'] = new TextEncoder().encode(JSON.stringify(manifest));
      const file = path.join(saved.directory,'undeclared-card-raw.gcanvas');
      fs.writeFileSync(file,zip.zipSync(entries,{level:0}));
      await rejectFileWithoutReplacement(file,'COMPAT_UNDECLARED_RAW');
    },
    async compat_historical_pins() {
      await fixture();
      await newCardGrid('R353 historical source evidence');
      const draft = await raw();
      await leave();
      await applyFixture([parameter(10,12,60)]);
      const actual = await actualFieldPin(10,8);
      need('COMPAT_HISTORICAL_FIXTURE_STALE', fieldPin(draft,10,8).fingerprint !== actual.fingerprint);
      const world = await dump(), saved = await saveFile();
      check('COMPAT_HISTORICAL_ARCHIVE_EXACT', same(fromArchive(saved.loaded).drafts,[draft]));
      await openFile(saved.file,saved.loaded.manifest.projectId);
      check('COMPAT_HISTORICAL_OPEN_EXACT', same((await allRaw()).drafts,[draft]) && (await dump()) === world);
      await openDraft(draft.draftId);
      check('COMPAT_HISTORICAL_PINS_NOT_RECOMPUTED', same(await raw(),draft) &&
        fieldPin(await raw(),10,8).fingerprint !== actual.fingerprint,await raw());
      const hp = await pinHistory();
      await rejectedAttempt('COMPAT_HISTORICAL_STALE');
      check('COMPAT_HISTORICAL_PREVIEW_REJECTED', !await visible('.reference-impact[open]') &&
        same(await raw(),draft) && (await dump()) === world && await history.unchanged(hp));
      await releasePin(hp);
    },
    async compat_geo219_reduction() {
      await fixture();
      await newCardGrid('R353 merged help');
      check('COMPAT_GEO219_ONE_HELP_BLOCK', await page(() => {
        const note = document.getElementById('igViewNote');
        return document.querySelectorAll('#infiniteGridWorkspace .ig-def-hint').length === 0 &&
          document.querySelectorAll('#igViewNote').length === 1 &&
          /拖曳平移/.test(note?.textContent || '') && /卡片標題/.test(note?.textContent || '');
      }));
      check('COMPAT_GEO219_ENTRY_RETAINED', await visible('#igCardRef') && await visible('#igDefinition') &&
        same(await mapping(),{card:'10',u:'3',v:'8'}));
    },
    async inspector_parameter_control() {
      await effectiveWorld('repeat_repeat'); await openInspector(6);
      const ui = await inspectorView(), before = await source(6);
      check('INSPECTOR_PARAMETER_READONLY', ui.fields.length === 2 && ui.fields[0].value === '600' &&
        ui.fields[1].value === '1200' && ui.fields.every(field => field.readonly === true) && ui.bindingDisabled === false, ui);
      await fill('#giName','R353 per field renamed');
      await preview('INSPECTOR_PARAMETER',{button:'#giPreview',inspectCommand:command =>
        check('INSPECTOR_PARAMETER_COMMAND', !command.includes('card-reference') && command.includes('param:10:3') &&
          command.includes('param:10:8') && !/undefined|NaN/.test(command), command)});
      await confirm();
      const renamed = await source(6);
      check('INSPECTOR_PARAMETER_RENAME_PRESERVES', renamed.name === 'R353 per field renamed' &&
        same(renamed.uDefinition,before.uDefinition) && same(renamed.vDefinition,before.vDefinition) && !renamed.cardReference, renamed);
      const mixed = renderGrid(7,'repeat_repeat','parameter'); mixed.value.v = 'repeat 211 1200';
      await applyFixture([mixed]); await openInspector(7);
      check('INSPECTOR_MIXED_CONTROL_EDITABLE', await page(() => document.getElementById('giUStep').readOnly &&
        !document.getElementById('giVStep').readOnly));
      await fill('#giVStep','1300'); await preview('INSPECTOR_PARAMETER_DIRECT_EDIT',{button:'#giPreview'}); await confirm();
      const edited = await source(7);
      check('INSPECTOR_PARAMETER_WITH_DIRECT_EDIT', same(edited.uDefinition.parameterRefs.step,{kind:'parameter',parameterId:10,fieldId:3}) &&
        edited.uDefinition.step === 600 && edited.vDefinition.step === 1300 && !edited.cardReference, edited);
    }
  };
  const cleanup = async () => {
    for (const token of nativeTokens) await query('engineering-cancel ' + token);
    nativeTokens = [];
    if (await page(() => ReferenceWorkspace.featureConfirmationPending())) throw Error('Unsettled feature confirmation');
    await leave();
    for (const pin of pins) await history.release(pin);
    pins = [];
    await page(() => {
      const trace = window.__p353ApiTrace;
      if (trace) {window.apiRequest = trace.original; delete window.__p353ApiTrace;}
      const picker = window.__p353SavePicker;
      if (picker) {
        if (picker.descriptor) Object.defineProperty(window,'showSaveFilePicker',picker.descriptor);
        else delete window.showSaveFilePicker;
        delete window.__p353SavePicker;
      }
      delete window.__p353FileChooser;
    });
    await send('Page.setInterceptFileChooserDialog',{enabled:false});
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
    await settled();
  };
  const results = [];
  for (const id of selected) {
    currentCase = id;
    const baselineExceptions = exceptionCount();
    let result = {id,status:'pass',kind:null,assertion:null,error:null};
    try {
      await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
      await cases[id]();
      if (exceptionCount() !== baselineExceptions)
        throw failure('exception','UNCAUGHT_BROWSER_EXCEPTION','Browser exception count changed',
          {before:baselineExceptions,after:exceptionCount()});
    } catch (error) {
      const kind = error.p353?.kind || 'exception';
      result = {id,status:kind === 'assertion' ? 'fail' : 'error',kind,
        assertion:error.p353?.assertion || 'UNEXPECTED_EXCEPTION',error:error.message};
    }
    if (exceptionCount() !== baselineExceptions) {
      result = {id,status:'error',kind:'exception',assertion:'UNCAUGHT_BROWSER_EXCEPTION',
        error:'Browser exception count changed: ' + baselineExceptions + ' -> ' + exceptionCount(),
        ...(result.status !== 'pass' ? {firstFailure:result} : {})};
    }
    const cleanupExceptions = exceptionCount();
    try {
      await cleanup();
      if (exceptionCount() !== cleanupExceptions) throw Error('Browser exception during cleanup');
    }
    catch (error) {
      result = {id,status:'error',kind:'cleanup',assertion:'CLEANUP_FAILED',error:error.message,
        ...(result.status !== 'pass' ? {firstFailure:result} : {})};
    }
    results.push(result);
    console.log('P353_CASE_RESULT ' + JSON.stringify(result));
    if (result.kind === 'cleanup') break; // The next case cannot claim an isolated precondition.
  }
  // Assertion failures have already entered the harness failN. Let its footer
  // finish with completed:true and exit 1 so a healthy mutation can be killed.
  // Environment/precondition/exception/cleanup failures remain incomplete runs.
  if (results.some(result => result.status === 'error') || results.length !== selected.length)
    throw Error('P353 cases failed: ' + results.filter(result => result.status !== 'pass').map(result =>
      result.id + '/' + result.kind + '/' + result.assertion).join(','));
};
module.exports.caseIds = CASE_IDS;
module.exports.selectCases = selectCases;
