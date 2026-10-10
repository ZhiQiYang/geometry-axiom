/* #49 detached component: host ports, no app globals/native World/store access. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.RuleCaseWorkbench = api;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const PROTOCOL = 'rule-case-workbench/1', DATA_SCHEMA = 'rule-case-workbench-data/1';
  const clone = value => JSON.parse(JSON.stringify(value));
  const same = (a, b) => a && b && a.projectId === b.projectId &&
    a.generation === b.generation && a.contextToken === b.contextToken;
  const labels = {passed:'通過', failed:'驗證失敗', blocked:'受阻', stale:'已過期',
    timeout:'執行逾時', crashed:'執行中止', 'unknown-runtime':'驗證版本未確認',
    'missing-capability':'缺少執行能力', 'not-run':'尚未執行'};
  const outcome = value => ({accepted:'接受', rejected:'拒絕'}[value] || '未取得原生觀察');

  function httpPort(endpoint = '/rule-cases/workbench', fetcher = globalThis.fetch) {
    async function request(action, fields = {}, signal) {
      const response = await fetcher(endpoint, {method:'POST', credentials:'same-origin',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({protocol:PROTOCOL, action, ...fields}), signal});
      const result = await response.json();
      if (!response.ok || result.ok !== true) {
        const error = new Error(result.error || '案例請求失敗');
        error.code = result.code; throw error;
      }
      return result;
    }
    return {
      open: () => request('open'),
      close: sessionId => request('close', {sessionId}),
      cancel: (sessionId, runId) => request('cancel', {sessionId, runId}),
      validate: (sessionId, definition) => request('validate', {sessionId, definition}),
      run: (sessionId, runId, definition, signal) => request('run', {sessionId, runId, definition}, signal),
      assess: (sessionId, data) => request('assess', {sessionId, data}),
      importData: (sessionId, data) => request('import', {sessionId, data}),
    };
  }

  function createController(ports) {
    if (!ports.transport || typeof ports.captureContext !== 'function')
      throw new Error('RuleCaseWorkbench requires transport and captureContext ports');
    const opening = {active:true, original:clone(ports.captureContext()), controller:null, unsubscribe:null};
    opening.cancel = () => {
      opening.active = false;
      if (opening.controller) opening.controller.teardown();
      else if (opening.unsubscribe) {opening.unsubscribe(); opening.unsubscribe = null;}
    };
    if (ports.subscribeContext) opening.unsubscribe = ports.subscribeContext(opening.cancel);
    if (!opening.active && opening.unsubscribe) {opening.unsubscribe(); opening.unsubscribe = null;}
    const pending = initializeController(ports, opening).catch(error => {opening.cancel(); throw error;});
    pending.teardown = opening.cancel;
    return pending;
  }

  async function initializeController(ports, opening) {
    if (!opening.active) throw new Error('案例初始化已退休');
    const transport = ports.transport;
    const opened = await transport.open();
    if (!opening.active || !same(opened.context, opening.original) || !same(opening.original, ports.captureContext())) {
      await transport.close(opened.sessionId).catch(() => {}); throw new Error('案例開啟時原始專案或操作已退休');
    }
    let epoch = 0, live = true, active = null, mutation = null, unsubscribe = opening.unsubscribe;
    let entries = [], views = [], listeners = new Set();
    const state = {context:clone(opened.context), runtime:clone(opened.runtime),
      definitions:clone(opened.definitions), hashes:clone(opened.definitionHashes),
      templates:clone(opened.definitions), selected:opened.definitions[0]?.caseId,
      busy:false, editing:false, message:'選擇案例後，可在隔離環境執行。', error:null};
    const matches = (ticket, context = state.context) => live && ticket === epoch &&
      same(context, ports.captureContext()) && same(context, state.context);
    function emit() { if (live) for (const listener of listeners) listener(snapshot()); }
    function snapshot() {
      return clone({...state, live, receipts:entries.map((entry, index) => ({...entry,
        view:views[index]?.receipt || entry.receipt,
        trust:entry.controlled && same(entry.origin, state.context) &&
          entry.receipt.definitionHash === state.hashes[entry.definition.caseId] &&
          views[index]?.receipt.status !== 'stale' ? 'controlled-run' : 'historical-unverified'}))});
    }
    function data() {
      return clone({schema:DATA_SCHEMA, definitions:state.definitions,
        receipts:entries.map(({definition, receipt}) => ({definition, receipt}))});
    }
    function cancel(message = '已取消本次案例執行。') {
      ++epoch;
      if (active) {
        const retired = active; active = null;
        retired.abort.abort();
        // Retire server run even when HTTP abort hides the native completion.
        transport.cancel(opened.sessionId, retired.runId).catch(() => {});
      }
      state.busy = false; state.editing = mutation !== null; state.message = message; emit();
    }
    function beginMutation(message) {
      if (!live || mutation !== null) return null;
      mutation = epoch + 1; // Reserve before cancel emits to any host subscribers.
      cancel(message); state.editing = true; state.error = null; emit(); return mutation;
    }
    function endMutation(ticket) {
      if (mutation === ticket) mutation = null;
      state.editing = mutation !== null;
      // Release the cancelled operation's own control lock, without adopting
      // its late data or message. A retired host never receives this repaint.
      if (live && same(state.context, ports.captureContext())) emit();
    }
    function adoptViews(result) {
      views = clone(result.views);
      if (result.runtime) state.runtime = clone(result.runtime);
      for (const [index, entry] of entries.entries())
        if (views[index]?.receipt.status === 'stale') entry.controlled = false;
    }
    async function assess(ticket) {
      const result = await transport.assess(opened.sessionId, data());
      if (!matches(ticket) || !same(result.context, state.context)) return false;
      adoptViews(result); state.hashes = clone(result.definitionHashes); return true;
    }
    async function refresh() {
      if (!live || state.busy || mutation !== null) return false;
      const ticket = beginMutation('正在核對結果是否過期…');
      try {if (!await assess(ticket)) return false; emit(); return true;}
      catch (error) {if (matches(ticket)) {state.error = error.message; emit();} return false;}
      finally {endMutation(ticket);}
    }
    function select(caseId) {
      if (!live || mutation !== null || !state.definitions.some(d => d.caseId === caseId)) return;
      cancel('已切換所選案例。'); state.selected = caseId; state.error = null; emit();
    }
    async function edit(patch) {
      if (!live || mutation !== null) return false;
      const id = state.selected;
      const original = state.definitions.find(d => d.caseId === id);
      const definition = clone(original);
      // Only editorial strings and candidate joint 101 side are editable.
      if (Object.keys(patch).some(key => !['label','transactionName','jointSide'].includes(key)))
        throw new Error('不支援的有限編輯欄位');
      if ('label' in patch) definition.label = patch.label;
      if ('transactionName' in patch) definition.input.transaction[0].value.name = patch.transactionName;
      if ('jointSide' in patch) {
        const joint = definition.input.transaction[0].value.joints?.find(j => j.id === 101);
        if (!joint) throw new Error('本案例沒有可編輯的接合 101');
        joint.side = patch.jointSide;
      }
      const ticket = beginMutation('正在核對有限案例修改…');
      try {
        const result = await transport.validate(opened.sessionId, definition);
        if (!matches(ticket) || state.selected !== id || !same(result.context, state.context)) return false;
        const nextDefinitions = state.definitions.map(d => d.caseId === id ? clone(result.definition) : d);
        const checked = await transport.assess(opened.sessionId, {...data(), definitions:nextDefinitions});
        if (!matches(ticket) || state.selected !== id || !same(checked.context, state.context)) return false;
        // Adopt the definition and freshness view together after both gates.
        state.definitions = nextDefinitions; adoptViews(checked);
        if (state.hashes[id] !== result.definitionHash)
          for (const entry of entries) if (entry.definition.caseId === id) entry.controlled = false;
        state.hashes[id] = result.definitionHash;
        state.message = '案例修改已核對；先前結果保留為歷史。'; return true;
      } catch (error) {
        if (matches(ticket)) {state.error = error.message; state.message = '案例修改未採用。';}
        return false;
      } finally {endMutation(ticket);}
    }
    async function reset() {
      if (!live || mutation !== null) return false;
      const ticket = beginMutation('正在還原所選模板…'), id = state.selected;
      const definition = clone(state.templates.find(d => d.caseId === id));
      try {
        const result = await transport.validate(opened.sessionId, definition);
        if (!matches(ticket) || !same(result.context, state.context)) return false;
        const nextDefinitions = state.definitions.map(d => d.caseId === id ? definition : d);
        const checked = await transport.assess(opened.sessionId, {...data(), definitions:nextDefinitions});
        if (!matches(ticket) || !same(checked.context, state.context)) return false;
        state.definitions = nextDefinitions; adoptViews(checked);
        state.hashes[id] = result.definitionHash;
        // Returning to identical data does not renew trust of an old run.
        for (const entry of entries) if (entry.definition.caseId === id) entry.controlled = false;
        state.message = '已還原模板；請重新執行核對。'; emit(); return true;
      } catch (error) {if (matches(ticket)) {state.error = error.message; emit();} return false;}
      finally {endMutation(ticket);}
    }
    async function run() {
      if (!live || state.busy || mutation !== null || !same(state.context, ports.captureContext())) return false;
      cancel('正在隔離執行所選案例…');
      const ticket = epoch, context = clone(state.context), id = state.selected;
      const definition = clone(state.definitions.find(d => d.caseId === id)), hash = state.hashes[id];
      for (const entry of entries) if (entry.definition.caseId === id) entry.controlled = false;
      const runId = (ports.newRunId || (() => globalThis.crypto.randomUUID()))();
      const abort = new AbortController(); active = {runId, abort}; state.busy = true;
      state.error = null; emit();
      try {
        const result = await transport.run(opened.sessionId, runId, definition, abort.signal);
        if (!matches(ticket, context) || active?.runId !== runId || state.selected !== id ||
            state.hashes[id] !== hash || !same(result.context, context)) return false;
        const receipt = result.receipt;
        if (result.trust !== 'controlled-run' || result.runId !== runId ||
            result.definitionHash !== hash || receipt.caseId !== id ||
            receipt.definitionHash !== hash || receipt.context.projectId !== context.projectId ||
            receipt.context.generation !== context.generation) throw new Error('結果與原始案例請求不符');
        if (entries.length >= 24) throw new Error('已達 24 筆結果上限；請由專案資料管理介面整理歷史。');
        const next = [...entries, {definition, receipt:clone(receipt), controlled:true, origin:context}];
        // Validate complete bounded receipt before making it visible.
        const checked = await transport.assess(opened.sessionId, {schema:DATA_SCHEMA,
          definitions:state.definitions, receipts:next.map(({definition, receipt}) => ({definition, receipt}))});
        if (!matches(ticket, context) || active?.runId !== runId || !same(checked.context, context)) return false;
        entries = next; adoptViews(checked); state.message = labels[receipt.status] || '結果資料無法核對';
        return true;
      } catch (error) {
        if (matches(ticket, context)) {state.error = error.message; state.message = '未取得可核對的本次結果。';}
        return false;
      } finally {if (matches(ticket, context)) {active = null; state.busy = false; emit();}}
    }
    async function restore(value) {
      if (!live || mutation !== null) return false;
      const ticket = beginMutation('正在核對保存的案例資料…');
      try {
        const result = await transport.importData(opened.sessionId, clone(value));
        if (!matches(ticket) || !same(result.context, state.context)) return false;
        state.definitions = clone(result.data.definitions); state.hashes = clone(result.definitionHashes);
        entries = result.data.receipts.map(entry => ({...clone(entry), controlled:false}));
        adoptViews(result);
        if (!state.definitions.some(d => d.caseId === state.selected)) state.selected = state.definitions[0]?.caseId;
        state.error = null; state.message = '已載入歷史資料；受控重跑後才是本次核對。'; emit(); return true;
      } catch (error) {
        if (matches(ticket)) {state.error = error.message; state.message = '保存資料無法核對；目前資料保留。'; emit();}
        return false;
      } finally {endMutation(ticket);}
    }
    async function retain() {
      if (!live || state.busy || mutation !== null || !ports.retainCaseData) return false;
      const ticket = beginMutation('正在保留案例資料…'), context = clone(state.context), payload = data();
      const stamp = JSON.stringify(payload);
      const isCurrent = () => matches(ticket, context) && JSON.stringify(data()) === stamp;
      try {
        if (!await assess(ticket)) return false;
        if (!isCurrent()) return false;
        // Host must gate ORIGINAL context and atomically add exactly one metadata history step.
        const result = await ports.retainCaseData(payload, context, {isCurrent});
        if (!isCurrent()) return false;
        if (result?.ok !== true) throw new Error(result?.error || '案例資料未保留');
        state.message = result.changed === false ? '案例資料未變更。' : '案例資料已明確保留。'; emit(); return true;
      } catch (error) {if (matches(ticket, context)) {state.error = error.message; emit();} return false;}
      finally {endMutation(ticket);}
    }
    function invalidate() {
      if (!live) return;
      cancel('專案或歷史脈絡已變更；本面板已退休，重新開啟可再執行。');
      for (const entry of entries) entry.controlled = false;
      live = false; transport.close(opened.sessionId).catch(() => {});
      for (const listener of listeners) listener(clone({...state, live:false, receipts:[]}));
      if (unsubscribe) {unsubscribe(); unsubscribe = null;}
    }
    function teardown() {opening.active = false; invalidate(); listeners.clear();}
    const controller = {snapshot, data, select, edit, reset, run, cancel, restore, retain, refresh,
      invalidate, teardown, subscribe(listener) {listeners.add(listener); listener(snapshot()); return () => listeners.delete(listener);}};
    opening.controller = controller;
    if (ports.loadCaseData) {
      try {
        const ticket = epoch, value = await ports.loadCaseData(clone(state.context));
        if (value && matches(ticket)) await restore(value);
      } catch (error) {teardown(); throw error;}
    }
    if (!opening.active || !live || !same(opening.original, ports.captureContext())) {
      teardown(); throw new Error('案例初始化已退休');
    }
    return controller;
  }

  const mounts = new WeakMap();
  function mount(root, ports) {
    mounts.get(root)?.teardown();
    const initialization = createController(ports);
    const operation = {retired:false, controller:null, teardown() {
      operation.retired = true; initialization.teardown(); operation.controller?.teardown();
      if (mounts.get(root) === operation) mounts.delete(root);
    }};
    mounts.set(root, operation);
    const pending = renderMount(root, ports, initialization, operation);
    pending.teardown = operation.teardown;
    return pending;
  }

  async function renderMount(root, ports, initialization, operation) {
    const document = root.ownerDocument;
    const controller = await initialization;
    if (operation.retired || mounts.get(root) !== operation || !same(controller.snapshot().context, ports.captureContext())) {
      controller.teardown(); throw new Error('案例 mount 已退休');
    }
    operation.controller = controller;
    root.classList.add('rule-case-workbench');
    function node(tag, text, attrs = {}) {
      const el = document.createElement(tag); if (text !== null) el.textContent = text;
      for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
      return el;
    }
    function button(text, action, attrs = {}) {
      const el = node('button', text, {type:'button', ...attrs});
      el.addEventListener('click', () => {Promise.resolve(action()).catch(error => {
        status.textContent = error.message;
      });}); return el;
    }
    const header = node('header', null), heading = node('h2', '規則案例試驗台');
    const status = node('p', '', {role:'status','aria-live':'polite','data-rcw':'status'});
    header.append(heading, button('關閉案例', () => {controller.teardown(); root.replaceChildren(); ports.onClose?.();}, {'data-rcw':'close'}));
    const grid = node('div', null, {class:'rcw-grid'}), list = node('nav', null, {'aria-label':'六個有限案例'});
    const detail = node('section', null, {'aria-label':'所選案例'});
    grid.append(list, detail); root.replaceChildren(header, status, grid);
    const off = controller.subscribe(state => {
      status.textContent = state.error ? `${state.message} ${state.error}` : state.message;
      root.dataset.live = String(state.live);
      list.replaceChildren(); detail.replaceChildren();
      const selected = state.definitions.find(d => d.caseId === state.selected);
      for (const definition of state.definitions) {
        const records = state.receipts.filter(e => e.definition.caseId === definition.caseId);
        const latest = records.at(-1);
        const current = latest?.trust === 'controlled-run' && latest.view.status !== 'stale';
        const resultText = latest ? `${current ? '本次' : '歷史未核信'} · ${labels[latest.view.status] || '無法核對'}` : '尚未執行';
        const el = button(`${definition.label}\n預期${outcome(definition.expect.outcome)} · ${resultText}`, () => {
          controller.select(definition.caseId);
          root.querySelector('[data-rcw="selected-title"]')?.focus();
        }, {'data-case-id':definition.caseId,'aria-current':String(definition.caseId === state.selected)});
        el.disabled = !state.live || state.editing; list.append(el);
      }
      if (!selected) return;
      const title = node('h3', selected.label, {tabindex:'-1','data-rcw':'selected-title'});
      detail.append(title);
      detail.append(button('返回案例清單', () => {
        root.querySelector('nav [aria-current="true"]')?.focus();
      }, {class:'rcw-back','data-rcw':'back'}));
      const form = node('form', null, {'data-rcw':'edit'});
      function field(text, name, value) {
        const label = node('label', text), input = node('input', null, {name, value, maxlength:'96'});
        input.disabled = !state.live || state.editing; label.append(input); form.append(label); return input;
      }
      const labelInput = field('案例名稱', 'label', selected.label);
      const nameInput = field('交易記錄名稱', 'transactionName', selected.input.transaction[0].value.name);
      const joint = selected.input.transaction[0].value.joints?.find(j => j.id === 101);
      let sideInput;
      if (joint) {
        const label = node('label', '交易接合 101 的面向');
        sideInput = node('select', null, {name:'jointSide'});
        for (const side of ['+u','-u','+v','-v']) sideInput.append(node('option', side, {value:side}));
        sideInput.value = joint.side; sideInput.disabled = !state.live || state.editing; label.append(sideInput); form.append(label);
      }
      const apply = node('button', '採用有限修改', {type:'submit'}); apply.disabled = !state.live || state.editing;
      form.append(apply);
      form.addEventListener('submit', event => {
        event.preventDefault(); const patch = {label:labelInput.value,transactionName:nameInput.value};
        if (sideInput) patch.jointSide = sideInput.value;
        controller.edit(patch).catch(error => {status.textContent = error.message;});
      });
      detail.append(form);
      const actions = node('div', null, {class:'rcw-actions'});
      const run = button('隔離執行所選案例', controller.run, {'data-rcw':'run'});
      run.disabled = !state.live || state.busy || state.editing;
      const cancel = button('取消執行', controller.cancel, {'data-rcw':'cancel'}); cancel.disabled = !state.busy;
      const reset = button('還原所選模板', controller.reset, {'data-rcw':'reset'}); reset.disabled = !state.live || state.editing;
      const retain = button('保留案例資料', controller.retain, {'data-rcw':'retain'});
      retain.disabled = !state.live || state.busy || state.editing || !ports.retainCaseData;
      actions.append(run, cancel, reset, retain); detail.append(actions);
      const records = state.receipts.filter(e => e.definition.caseId === selected.caseId), latest = records.at(-1);
      const summary = node('dl', null, {'data-rcw':'result'});
      for (const [term, value] of [['預期',outcome(selected.expect.outcome)], ['原生實際',
        (state.busy && latest ? '上次結果 · ' : '') + outcome(latest?.view.actualOutcome)],
        ['驗證狀態',state.busy ? '執行中' : latest ? `${latest.trust === 'controlled-run' ? '本次核對' : '歷史未核信'} · ${labels[latest.view.status] || '結果資料無法核對'}` : '尚未執行']]) {
        summary.append(node('dt',term),node('dd',value));
      }
      detail.append(summary);
      function disclosure(title, value, open = false) {
        const box = node('details', null); if (open) box.open = true;
        box.append(node('summary',title),node('pre',JSON.stringify(value, null, 2))); detail.append(box);
      }
      disclosure('案例输入與私有來源 pins', {input:selected.input,sourcePins:selected.sourcePins});
      disclosure('預期診斷與核對項目', {expect:selected.expect,assertions:selected.assertions});
      if (latest) {
        disclosure('原生診斷與核對明細', {actualDiagnostics:latest.view.actualDiagnostics,
          assertionResults:latest.view.assertionResults, reason:latest.view.reason,
          staleReasons:latest.view.staleReasons,observations:latest.view.observations || '未取得原生觀察'}, true);
        disclosure(`歷史結果 (${records.length})`, records.map(e => ({trust:e.trust,
          freshness:e.view.status,originalReceipt:e.receipt,originalDefinition:e.definition})));
      }
    });
    const originalTeardown = controller.teardown;
    controller.teardown = () => {originalTeardown(); off();
      if (mounts.get(root) === operation) {root.replaceChildren(); root.classList.remove('rule-case-workbench');mounts.delete(root);}
    };
    return controller;
  }
  return {PROTOCOL, DATA_SCHEMA, httpPort, createController, mount};
});
