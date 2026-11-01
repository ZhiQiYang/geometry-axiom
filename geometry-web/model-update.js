/* #44 F1b: transient, explicit source selection; full-record local commit. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ModelUpdate = api;
})(globalThis, () => {
  'use strict';
  const HASH = /^[a-f0-9]{64}$/;
  const PACKAGES = ['space', 'volume', 'clearance', 'walls', 'timbers'];
  const clone = value => JSON.parse(JSON.stringify(value));
  const own = (value, required) => value && typeof value === 'object' && !Array.isArray(value) &&
    Object.keys(value).length === required.length && required.every(key => Object.hasOwn(value, key));
  const uint = value => Number.isSafeInteger(value) && value >= 0 && value <= 4294967295;
  function canonical(value) {
    if (value === null || typeof value === 'boolean' || typeof value === 'string') return JSON.stringify(value);
    if (typeof value === 'number' && Number.isFinite(value)) return JSON.stringify(value);
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (value && typeof value === 'object' && Object.getPrototypeOf(value) === Object.prototype)
      return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
    throw Error('模型更新資料必須是完整、有限的 JSON。');
  }
  const same = (a, b) => canonical(a) === canonical(b);
  function selectionValid(s) {
    if (!own(s, ['placement_id', 'boundary_id', 'edges', 'obstacles', 'timbers', 'projection']) ||
        !uint(s.placement_id) || !uint(s.boundary_id) ||
        !Array.isArray(s.edges) || !s.edges.length || s.edges.length > 512 || !s.edges.every(uint) ||
        new Set(s.edges).size !== s.edges.length) throw Error('請明選現行來源放置面與各個邊，不能沿用舊編號推測。');
    for (const [key, kinds] of [['obstacles', ['column', 'beam']], ['timbers', ['timber']]]) {
      if (!Array.isArray(s[key]) || s[key].length > 512 ||
          !s[key].every(ref => own(ref, ['kind', 'id']) && kinds.includes(ref.kind) && uint(ref.id)) ||
          new Set(s[key].map(ref => ref.kind + ':' + ref.id)).size !== s[key].length)
        throw Error('請明選完整的角材與柱樑清單；沒有時須明確傳空清單。');
    }
    if (s.projection !== null && (!own(s.projection, ['kind', 'view', 'region', 'wallSide']) ||
        s.projection.kind !== 'space-boundary-plan' || !['top', 'bottom'].includes(s.projection.view) ||
        s.projection.region !== 'interior' || s.projection.wallSide !== 'outside'))
      throw Error('請核對現行來源的平面投影用途。');
    canonical(s);
    return clone(s);
  }
  function create(host) {
    for (const key of ['getState', 'getRecord', 'readSource', 'produce', 'validateRecord', 'sha', 'commit'])
      if (typeof host[key] !== 'function') throw Error('模型更新缺少接口：' + key);
    if (host.commit.constructor.name === 'AsyncFunction') throw Error('模型提交接口必須同步且原子。');
    let generation = 0, operation = null, phase = 'idle', lastError = null;
    const digest = async value => {
      const pin = await host.sha(new TextEncoder().encode(value));
      if (typeof pin !== 'string' || !HASH.test(pin)) throw Error('無法可靠核對模型更新內容。');
      return pin;
    };
    function state() {
      const s = host.getState();
      if (!s || !['context', 'frame', 'revision', 'contextToken', 'undo', 'redo', 'group', 'blocked'].every(key => Object.hasOwn(s, key)) ||
          !s.context || !s.frame || !Number.isSafeInteger(s.revision) || s.revision < 0 ||
          typeof s.contextToken !== 'string' || !s.contextToken || typeof s.blocked !== 'boolean')
        throw Error('專案狀態無法可靠核對，請重新開啟模型。');
      if (s.blocked || s.group) throw Error('請先完成目前操作，再更新模型來源。');
      return s;
    }
    function guard(op) {
      if (!op || operation !== op || op.generation !== generation || op.controller?.signal.aborted)
        throw Error('這次模型更新已取消或被取代。');
      const s = state(), saved = op.stamp;
      if (s.context !== saved.context || s.frame !== saved.frame || s.revision !== saved.revision ||
          s.contextToken !== saved.contextToken || s.undo !== saved.undo || s.redo !== saved.redo || s.group !== saved.group)
        throw Error('專案或操作歷史已變更，請重新明選來源。');
      const record = host.getRecord(op.id);
      if (!record || canonical(record) !== op.signature)
        throw Error('模型已移除或同 ID 的完整紀錄已被替換，請重新開啟模型。');
      return s;
    }
    function retire(next = 'cancelled') {
      operation?.controller?.abort(); generation++; operation = null; phase = next; lastError = null;
    }
    function begin(id) {
      retire('selecting');
      try {
        const stamp = {...state()}, record = host.getRecord(id);
        if (!record) throw Error('找不到要更新的模型。');
        host.validateRecord(record);
        if (record.input.mode !== 'plan') throw Error('本版只支援普通單一平面模型更新。');
        operation = {id, stamp, record: clone(record), signature: canonical(record), generation,
          controller: null, candidate: null, review: null};
        return clone(record);
      } catch (error) { phase = 'failed'; lastError = error.message; throw error; }
    }
    async function read(op) {
      guard(op);
      const source = await host.readSource({signal: op.controller.signal});
      guard(op);
      if (!own(source, ['scene', 'revision']) || typeof source.scene !== 'string' || source.scene.includes('\0') ||
          new TextEncoder().encode(source.scene).length > 1024 * 1024 ||
          !Number.isSafeInteger(source.revision) || source.revision < 0)
        throw Error('現行來源無法完整讀取，未更新模型。');
      return clone(source);
    }
    async function diff(before, after) {
      return {source: {before: clone(before.source), after: clone(after.source)},
        input: {before: clone(before.input), after: clone(after.input)},
        settings: {before: clone(before.input.settings), after: clone(after.input.settings)},
        summary: {before: clone(before.result.summary), after: clone(after.result.summary)},
        packages: await Promise.all(PACKAGES.map(async kind => ({kind,
          before: before.result[kind] ? await digest(canonical(before.result[kind].manifest)) : null,
          after: after.result[kind] ? await digest(canonical(after.result[kind].manifest)) : null})))};
    }
    async function checkedCandidate(op, request, source) {
      // Detach immediately: producers must not retain an alias across hash awaits.
      const response = await host.produce(clone(request), {signal: op.controller.signal});
      const candidate = clone(response);
      guard(op);
      if (!own(candidate, ['ok', 'schema', 'identity', 'old_record_sha256', 'current_scene_sha256',
          'selection', 'record', 'diff', 'runtime']) || candidate.ok !== true ||
          candidate.schema !== 'geometry-model-update-candidate/1' || candidate.identity !== 'unknown')
        throw Error(candidate?.diagnostics?.[0]?.message || candidate?.error || '來源候選失敗或能力不足，未更新模型。');
      const runtime = candidate.runtime;
      if (!own(runtime, ['base_binary_sha256', 'bridge_binary_sha256', 'producer_sha256', 'axiom_sha256']) ||
          !Object.values(runtime).every(pin => typeof pin === 'string' && HASH.test(pin)))
        throw Error('原生執行版本未知，不能確認模型更新。');
      host.validateRecord(candidate.record);
      const next = candidate.record, old = op.record;
      if (next.id !== old.id || next.name !== old.name || next.created_at !== old.created_at ||
          next.input.mode !== 'plan' || !same(candidate.selection, request.selection) ||
          next.input.placement_id !== request.selection.placement_id || next.source.kind !== 'scene' ||
          next.source.placement_id !== request.selection.placement_id || next.source.boundary_id !== request.selection.boundary_id ||
          !same({...next.input.settings, edges: old.input.settings.edges}, old.input.settings) ||
          !same(next.input.settings.edges, request.selection.edges) || !same(next.input.obstacles, request.selection.obstacles) ||
          !same(next.input.timbers || [], request.selection.timbers) ||
          !same(next.source.projection || null, request.selection.projection) ||
          next.source.scene_hash !== next.result.source_sha256 ||
          candidate.old_record_sha256 !== await digest(op.signature) ||
          candidate.current_scene_sha256 !== await digest(source.scene) ||
          !same(candidate.diff, await diff(old, next)))
        throw Error('候選內容與已明選來源或完整旧模型不一致，未更新模型。');
      guard(op);
      return clone(candidate);
    }
    function failed(op, error) {
      if (operation === op) { op.candidate = null; op.review = null; phase = 'failed'; lastError = error.message; }
      throw error;
    }
    async function prepare(selection) {
      const previous = operation;
      if (!previous || ['producing', 'confirming', 'committed'].includes(phase)) throw Error('請先開啟模型並明選來源。');
      guard(previous);
      const chosen = selectionValid(selection);
      const op = {...previous, generation: ++generation, controller: new AbortController(), candidate: null, review: null};
      previous.controller?.abort(); operation = op; phase = 'producing'; lastError = null;
      try {
        const source = await read(op), request = {record: clone(op.record), current_scene: source.scene, selection: chosen};
        const candidate = await checkedCandidate(op, request, source);
        if (!same(await read(op), source)) throw Error('預覽期間來源已變更，請重新明選來源。');
        const reviewId = await digest(canonical({generation: op.generation, candidate}));
        guard(op);
        op.source = source; op.request = request; op.candidate = candidate;
        op.review = {reviewId, identity: 'unknown', before: clone(op.record), after: clone(candidate.record), diff: clone(candidate.diff)};
        phase = 'review';
        return getReview();
      } catch (error) { return failed(op, error); }
    }
    function getReview() {
      if (phase !== 'review' || !operation?.review) return null;
      guard(operation);
      return clone(operation.review);
    }
    async function confirm(reviewId) {
      const op = operation;
      if (phase !== 'review' || !op?.review || reviewId !== op.review.reviewId)
        throw Error('請先核對這次新舊差異，再明確確認更新。');
      guard(op); phase = 'confirming';
      try {
        if (!same(await read(op), op.source)) throw Error('確認前來源已變更，請重新明選來源。');
        // A fresh isolated producer validates actual packages and binary contents.
        const replay = await checkedCandidate(op, op.request, op.source);
        if (!same(replay, op.candidate)) throw Error('候選或執行版本已變更，請重新預覽並核對差異。');
        if (!same(await read(op), op.source)) throw Error('重驗期間來源已變更，未更新模型。');
        guard(op);
        // No await between the final guards and the existing single-history write.
        const result = host.commit(op.id, clone(op.candidate.record));
        if (result && typeof result.then === 'function') throw Error('模型提交接口必須同步且原子。');
        // Existing store events may synchronously open/cancel another intent.
        if (operation !== op) return clone(result || replay.record);
        if (result === false || result?.ok === false || !same(host.getRecord(op.id), replay.record))
          throw Error('完整模型提交未確認，請重新核對專案中的模型。');
        phase = 'committed'; op.review = null; op.candidate = null;
        return clone(result || replay.record);
      } catch (error) { return failed(op, error); }
    }
    function status() { return {phase, modelId: operation?.id || null, generation, error: lastError}; }
    return {begin, prepare, getReview, confirm, cancel: () => retire(), status};
  }
  return {create, canonical, selectionValid};
});
