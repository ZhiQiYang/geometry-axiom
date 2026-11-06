/* I60: neutral exact one-dimensional allocation conservation. All intervals,
   consumption and usable bounds are explicit inputs; no domain policy/defaults.
   Identity records are own data properties on local plain/null-prototype objects;
   data from another realm must cross as JSON, not as an opaque live object. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else Object.defineProperty(root, 'GeometryIntervalAllocation', {value: api});
})(this, function () {
  'use strict';
  function fail(code, reason) { throw Object.assign(Error(code + ': ' + reason), {code, reason}); }
  const integer = value => Number.isSafeInteger(value) && value >= 0;
  function canonical(value, ancestors = new Set()) {
    if (value === null || typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value);
    if (typeof value === 'number' && Number.isSafeInteger(value)) return JSON.stringify(value);
    if (value && typeof value === 'object' && ancestors.has(value)) fail('DEMAND_IDENTITY', 'invalid-key');
    if (Array.isArray(value)) {
      if (Object.keys(value).length !== value.length || Object.getOwnPropertyNames(value).length !== value.length + 1 ||
          Object.getOwnPropertySymbols(value).length) fail('DEMAND_IDENTITY', 'invalid-key');
      const nested = new Set(ancestors); nested.add(value);
      return '[' + Array.from({length: value.length}, (_, index) => {
        const property = Object.getOwnPropertyDescriptor(value, String(index));
        if (!property?.enumerable || !Object.hasOwn(property, 'value')) fail('DEMAND_IDENTITY', 'invalid-key');
        return canonical(property.value, nested);
      }).join(',') + ']';
    }
    if (value && typeof value === 'object' && !Object.getOwnPropertySymbols(value).length) {
      const prototype = Object.getPrototypeOf(value);
      if (prototype !== null && prototype !== Object.prototype ||
          Object.getOwnPropertyNames(value).length !== Object.keys(value).length) fail('DEMAND_IDENTITY', 'invalid-key');
      const nested = new Set(ancestors); nested.add(value);
      return '{' + Object.keys(value).sort().map(key => {
        const property = Object.getOwnPropertyDescriptor(value, key);
        if (!property.enumerable || !Object.hasOwn(property, 'value')) fail('DEMAND_IDENTITY', 'invalid-key');
        return JSON.stringify(key) + ':' + canonical(property.value, nested);
      }).join(',') + '}';
    }
    fail('DEMAND_IDENTITY', 'invalid-key');
  }
  function identity(key) {
    const type = key && Object.getOwnPropertyDescriptor(key, 'type');
    const id = key && Object.getOwnPropertyDescriptor(key, 'id');
    if (!key || typeof key !== 'object' || Array.isArray(key) ||
        !type?.enumerable || !id?.enumerable || !Object.hasOwn(type, 'value') || !Object.hasOwn(id, 'value') ||
        typeof type.value !== 'string' || !type.value ||
        !(integer(id.value) || typeof id.value === 'string' && id.value.length)) fail('DEMAND_IDENTITY', 'invalid-key');
    return canonical(key);
  }
  function createIdentityTracker() {
    const identities = new Set();
    function add(key) {
      const id = identity(key);
      if (identities.has(id)) fail('DEMAND_IDENTITY', 'duplicate');
      identities.add(id);
    }
    function has(key) { return identities.has(identity(key)); }
    return Object.freeze({add: Object.freeze(add), has: Object.freeze(has), get size() { return identities.size; }});
  }
  function verifyAllocation(allocation, usable) {
    if (!allocation || !integer(allocation.length) || allocation.length === 0 ||
        !integer(allocation.start) || !integer(allocation.end) || allocation.end <= allocation.start ||
        !Array.isArray(usable) || usable.length !== 2 || !usable.every(integer) || usable[0] > usable[1] ||
        BigInt(allocation.end) - BigInt(allocation.start) !== BigInt(allocation.length) ||
        allocation.start < usable[0] || allocation.end > usable[1]) fail('CONSERVATION', 'invalid-demand');
    return true;
  }
  function verify(value) {
    if (!value || !Array.isArray(value.expected) || !Array.isArray(value.containers)) fail('CONSERVATION', 'invalid-allocation');
    const expected = createIdentityTracker(), actual = createIdentityTracker();
    for (const key of value.expected) expected.add(key);
    for (const container of value.containers) {
      if (!container || !integer(container.length) || container.length === 0 ||
          !Array.isArray(container.usable) || container.usable.length !== 2 ||
          !container.usable.every(integer) || container.usable[0] > container.usable[1] ||
          container.usable[1] > container.length || !Array.isArray(container.allocations) ||
          !Array.isArray(container.consumptions) || !container.remainder) fail('CONSERVATION', 'invalid-container');
      const intervals = [];
      let total = 0n;
      function interval(segment, positive) {
        if (!segment || !integer(segment.start) || !integer(segment.end) ||
            segment.end < segment.start || positive && segment.end === segment.start ||
            segment.end > container.length) fail('CONSERVATION', 'invalid-interval');
        const length = BigInt(segment.end) - BigInt(segment.start);
        total += length;
        if (length > 0n) intervals.push(segment);
        return length;
      }
      for (const allocation of container.allocations) {
        actual.add(allocation?.key);
        verifyAllocation(allocation, container.usable);
        interval(allocation, true);
      }
      for (const consumption of container.consumptions) interval(consumption, false);
      interval(container.remainder, false);
      if (container.remainder.end !== container.length) fail('CONSERVATION', 'invalid-interval');
      intervals.sort((a, b) => a.start - b.start || a.end - b.end);
      for (let index = 1; index < intervals.length; index++) {
        if (intervals.at(index).start < intervals.at(index - 1).end) fail('CONSERVATION', 'overlap');
      }
      if (total !== BigInt(container.length)) fail('CONSERVATION', 'unequal-total');
    }
    if (actual.size !== expected.size || value.expected.some(key => !actual.has(key))) fail('DEMAND_IDENTITY', 'missing');
    return true;
  }
  return Object.freeze({verify: Object.freeze(verify), createIdentityTracker: Object.freeze(createIdentityTracker), verifyAllocation: Object.freeze(verifyAllocation)});
});
