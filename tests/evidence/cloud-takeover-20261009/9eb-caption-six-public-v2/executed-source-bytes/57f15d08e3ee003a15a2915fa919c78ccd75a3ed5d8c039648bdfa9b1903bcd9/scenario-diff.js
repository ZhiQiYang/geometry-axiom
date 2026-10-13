/* #46: compare bounded archived definitions; no live World, object merge or evaluator.
 * Inputs must first pass snapshot archive hash/capability/native validation. This
 * module compares declared pins and complete definitions; it does not authenticate
 * an archive or register supported object kinds/attachment schemas.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ScenarioDiff = api;
})(globalThis, () => {
  'use strict';
  const LIMITS = Object.freeze({depth:48, nodes:1000000, stringBytes:16 * 1024 * 1024,
    metadataBytes:8 * 1024 * 1024});
  const HASH = /^[a-f0-9]{64}$/;
  const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  const record = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  function fail(code, message) {
    const error = new Error(message);
    error.name = 'ScenarioDiffError'; error.code = code;
    throw error;
  }

  // Inspect data descriptors before reading values: accessors/toJSON/functions are not JSON.
  // Count encoded bytes without calling user coercion or allocating an encoded large string.
  function stringSize(value) {
    if (value.length > LIMITS.stringBytes) fail('INPUT_CAP', 'Scenario string exceeds the input cap.');
    let bytes = 0, json = 2;
    for (let i = 0; i < value.length; i++) {
      const code = value.charCodeAt(i);
      if (code < 0x80) {
        const shortEscape = code === 8 || code === 9 || code === 10 || code === 12 || code === 13;
        bytes++; json += code < 0x20 ? shortEscape ? 2 : 6 : code === 0x22 || code === 0x5c ? 2 : 1;
      } else if (code < 0x800) { bytes += 2; json += 2; }
      else if (code >= 0xd800 && code <= 0xdbff && i + 1 < value.length &&
          value.charCodeAt(i + 1) >= 0xdc00 && value.charCodeAt(i + 1) <= 0xdfff) {
        bytes += 4; json += 4; i++;
      } else { bytes += 3; json += code >= 0xd800 && code <= 0xdfff ? 6 : 3; }
      if (bytes > LIMITS.stringBytes) fail('INPUT_CAP', 'Scenario string exceeds the input cap.');
    }
    return {bytes, json};
  }
  function detached(input) {
    const budget = {nodes:0, metadata:0}, ancestors = new Set();
    function charge(amount, scene) {
      if (!scene) budget.metadata += amount;
      if (budget.metadata > LIMITS.metadataBytes) fail('INPUT_CAP', 'Scenario metadata exceeds the input cap.');
    }
    function text(value, scene) {
      const size = stringSize(value);
      // The raw scene has its own 16 MiB cap; all other JSON together has 8 MiB.
      charge(size.json, scene);
    }
    function visit(value, depth, path) {
      if (++budget.nodes > LIMITS.nodes || depth > LIMITS.depth)
        fail('INPUT_CAP', 'Scenario JSON exceeds the traversal cap.');
      const scene = path.length === 2 && path[0] === 'snapshot' && path[1] === 'worldScene';
      if (value === null) { charge(4, false); return null; }
      if (typeof value === 'string') { text(value, scene); return value; }
      if (typeof value === 'boolean') { charge(value ? 4 : 5, false); return value; }
      if (typeof value === 'number') {
        if (!Number.isFinite(value)) fail('INVALID_JSON', 'Scenario JSON numbers must be finite.');
        charge(String(value).length, false); return value;
      }
      if (typeof value !== 'object') fail('INVALID_JSON', 'Scenario inputs must contain plain JSON only.');
      const array = Array.isArray(value), proto = Object.getPrototypeOf(value);
      if ((!array && proto !== Object.prototype && proto !== null) || (array && proto !== Array.prototype))
        fail('INVALID_JSON', 'Scenario inputs must contain plain JSON objects and arrays.');
      if (ancestors.has(value)) fail('INVALID_JSON', 'Scenario JSON cannot contain cycles.');
      const length = array ? Object.getOwnPropertyDescriptor(value, 'length').value : 0;
      if (array && length > LIMITS.nodes - budget.nodes)
        fail('INPUT_CAP', 'Scenario array exceeds the traversal cap.');
      const keys = Reflect.ownKeys(value);
      if (keys.length > LIMITS.nodes - budget.nodes + (array ? 1 : 0))
        fail('INPUT_CAP', 'Scenario object exceeds the traversal cap.');
      if (array && keys.length !== length + 1)
        fail('INVALID_JSON', 'Scenario JSON arrays must be dense without extra properties.');
      const output = array ? [] : Object.create(null);
      charge(2 + Math.max(0, keys.length - (array ? 2 : 1)), false);
      ancestors.add(value);
      for (const key of keys) {
        if (array && key === 'length') continue;
        if (typeof key !== 'string') fail('INVALID_JSON', 'Scenario JSON cannot contain symbol keys.');
        if (array && (!/^(0|[1-9][0-9]*)$/.test(key) || Number(key) >= length))
          fail('INVALID_JSON', 'Scenario JSON arrays cannot contain extra properties.');
        const descriptor = Object.getOwnPropertyDescriptor(value, key);
        if (!descriptor || !own(descriptor, 'value') || !descriptor.enumerable)
          fail('INVALID_JSON', 'Scenario JSON cannot contain accessors or hidden properties.');
        if (!array) { text(key, false); charge(1, false); }
        output[key] = visit(descriptor.value, depth + 1, path.concat(key));
      }
      ancestors.delete(value);
      return output;
    }
    return visit(input, 0, []);
  }
  const name = value => typeof value === 'string' && value.length > 0 && value.length <= 128;
  const uint = value => Number.isSafeInteger(value) && value >= 0 && value <= 4294967295;
  const fields = (value, keys) => record(value) && Object.keys(value).length === keys.length &&
    keys.every(key => own(value, key));
  function validObject(ref, scoped) {
    return fields(ref, scoped ? ['scenarioId','kind','id','version'] : ['kind','id','version']) &&
      (!scoped || name(ref.scenarioId)) && name(ref.kind) && (name(ref.id) || uint(ref.id)) &&
      (ref.version === null || Number.isSafeInteger(ref.version) && ref.version > 0);
  }
  const key = ref => JSON.stringify([ref.scenarioId, ref.kind, typeof ref.id, ref.id, ref.version]);
  const scoped = (scenarioId, object) => ({scenarioId, kind:object.kind, id:object.id, version:object.version});
  function checked(input) {
    const value = detached(input);
    const envelopeFields = ['scenarioId','closureHash','basis','snapshot','originMapping','objects','label','requiredCapabilities'];
    if (!record(value) || Object.keys(value).some(field => !envelopeFields.includes(field)) ||
        !name(value.scenarioId) || typeof value.closureHash !== 'string' || !HASH.test(value.closureHash) ||
        !own(value, 'basis') || !Array.isArray(value.originMapping) || !Array.isArray(value.objects) ||
        !fields(value.snapshot, ['projectManifest','worldScene','assetHashes']) ||
        !record(value.snapshot.projectManifest) || typeof value.snapshot.worldScene !== 'string' ||
        !Array.isArray(value.snapshot.assetHashes))
      fail('INVALID_SNAPSHOT', 'Scenario comparison requires a complete archived snapshot envelope.');
    if (own(value, 'label') && (typeof value.label !== 'string' || !value.label.trim() || value.label.length > 200))
      fail('INVALID_SNAPSHOT', 'Scenario archive label is invalid.');
    if (value.basis !== null && (!fields(value.basis, ['scenarioId','snapshotHash']) ||
        !name(value.basis.scenarioId) || value.basis.scenarioId === value.scenarioId ||
        typeof value.basis.snapshotHash !== 'string' || !HASH.test(value.basis.snapshotHash)))
      fail('INVALID_BASIS', 'Scenario copy basis must pin a different scenario snapshot.');
    if (own(value, 'requiredCapabilities') && (!Array.isArray(value.requiredCapabilities) ||
        value.requiredCapabilities.some(capability => !name(capability)) ||
        new Set(value.requiredCapabilities).size !== value.requiredCapabilities.length))
      fail('INVALID_CAPABILITIES', 'Scenario required capabilities must be unique explicit names.');
    const objects = new Map();
    for (const object of value.objects) {
      if (!validObject(object, false)) fail('INVALID_OBJECT', 'Scenario objects need exact typed references.');
      const ref = scoped(value.scenarioId, object), identity = key(ref);
      if (objects.has(identity)) fail('INVALID_OBJECT', 'Scenario typed object references must be unique.');
      objects.set(identity, ref);
    }
    const assets = value.snapshot.assetHashes;
    if (assets.some(hash => typeof hash !== 'string' || !HASH.test(hash)) || new Set(assets).size !== assets.length)
      fail('INVALID_ASSETS', 'Scenario assets need unique complete SHA-256 hashes.');
    const fromKeys = new Set(), toKeys = new Set();
    for (const mapping of value.originMapping) {
      if (!fields(mapping, ['from','to','snapshotHash']) || !validObject(mapping.from, true) || !validObject(mapping.to, true) ||
          !value.basis || mapping.from.scenarioId !== value.basis.scenarioId || mapping.to.scenarioId !== value.scenarioId ||
          mapping.from.kind !== mapping.to.kind || mapping.from.version !== mapping.to.version ||
          mapping.snapshotHash !== value.basis.snapshotHash)
        fail('INVALID_ORIGIN', 'Scenario origins must pin the typed copy basis and destination.');
      const from = key(mapping.from), to = key(mapping.to);
      if (fromKeys.has(from) || toKeys.has(to)) fail('INVALID_ORIGIN', 'Scenario copy origins must be unambiguous.');
      fromKeys.add(from); toKeys.add(to);
    }
    return {value, objects};
  }
  function same(a, b) {
    if (a === b) return true;
    if (a === null || b === null || typeof a !== 'object' || typeof b !== 'object') return false;
    if (Array.isArray(a) !== Array.isArray(b)) return false;
    const keys = Object.keys(a), others = Object.keys(b);
    if (keys.length !== others.length) return false;
    return keys.every(key => own(b, key) && same(a[key], b[key]));
  }
  function compare(before, after) {
    // Detach and cap both complete inputs before inspecting definitions or tracing origins.
    const a = checked(before), b = checked(after), sections = [], originPairs = [], ignoredOrigins = [];
    const left = a.value.snapshot, right = b.value.snapshot;
    function section(field, first, next, beforePresent = true, afterPresent = true) {
      if (beforePresent !== afterPresent || !same(first, next))
        sections.push({field, before:first, after:next, beforePresent, afterPresent});
    }
    section('worldScene', left.worldScene, right.worldScene);
    const firstManifest = left.projectManifest, nextManifest = right.projectManifest;
    const manifestKeys = [...new Set([...Object.keys(firstManifest), ...Object.keys(nextManifest)])].sort();
    for (const field of manifestKeys) {
      const first = own(firstManifest, field), next = own(nextManifest, field);
      section('projectManifest.' + field, first ? firstManifest[field] : null, next ? nextManifest[field] : null, first, next);
    }
    section('assets', left.assetHashes.slice().sort(), right.assetHashes.slice().sort());
    if (own(a.value, 'requiredCapabilities') || own(b.value, 'requiredCapabilities')) {
      const first = own(a.value, 'requiredCapabilities'), next = own(b.value, 'requiredCapabilities');
      section('requiredCapabilities', first ? a.value.requiredCapabilities.slice().sort() : null,
        next ? b.value.requiredCapabilities.slice().sort() : null, first, next);
    }
    const pairedBefore = new Set(), pairedAfter = new Set();
    function origins(source, copy, reverse) {
      for (const mapping of copy.value.originMapping) {
        let reason = null;
        if (copy.value.basis.scenarioId !== source.value.scenarioId) reason = 'different-basis-scenario';
        else if (copy.value.basis.snapshotHash !== source.value.closureHash) reason = 'different-basis-snapshot';
        else if (!source.objects.has(key(mapping.from)) || !copy.objects.has(key(mapping.to))) reason = 'missing-typed-endpoint';
        if (reason) { ignoredOrigins.push({mapping, reason}); continue; }
        const first = reverse ? mapping.to : mapping.from, next = reverse ? mapping.from : mapping.to;
        const firstKey = key(first), nextKey = key(next);
        if (pairedBefore.has(firstKey) || pairedAfter.has(nextKey))
          fail('INVALID_ORIGIN', 'Scenario comparison has conflicting copy origins.');
        pairedBefore.add(firstKey); pairedAfter.add(nextKey);
        originPairs.push({before:first, after:next, relationship:'matchedOrigin',
          copyIdentity:'independent-copy', physicalIdentity:'unknown', snapshotHash:mapping.snapshotHash});
      }
    }
    origins(a, b, false); origins(b, a, true);
    const ordered = refs => refs.sort((x, y) => key(x) < key(y) ? -1 : key(x) > key(y) ? 1 : 0);
    originPairs.sort((x, y) => key(x.before) < key(y.before) ? -1 : key(x.before) > key(y.before) ? 1 : 0);
    return {scope:'definitions', geometry:{status:'not-evaluated'}, physicalIdentity:'unknown', sections, originPairs,
      ignoredOrigins, unmatched:{before:ordered([...a.objects.values()].filter(ref => !pairedBefore.has(key(ref)))),
        after:ordered([...b.objects.values()].filter(ref => !pairedAfter.has(key(ref))))}};
  }
  return Object.freeze({compare, LIMITS});
});
