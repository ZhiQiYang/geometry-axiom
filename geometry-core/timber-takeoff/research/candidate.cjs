'use strict';

/* U476: executable research candidate, not a registered application capability.
 * Native acquisition facts are the explicit finite study input. This module is
 * never an authorization boundary for callers, project-store, or cutting-plan/1.
 */
const fs = require('node:fs');
const MAX_U32 = 0xffffffff;
const LIMITS = Object.freeze({items: 64, representations: 128, models: 8, bytes: 128 * 1024, nodes: 4096, depth: 12});
const DOCUMENT_SCHEMA = 'U476-study-document/1';
const copy = value => JSON.parse(JSON.stringify(value));
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const uint = value => Number.isSafeInteger(value) && value >= 0 && value <= MAX_U32;
const positive = value => uint(value) && value > 0;
const text = value => typeof value === 'string' && value.length > 0;
const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const order = (a, b) => a < b ? -1 : a > b ? 1 : 0;
const fail = code => { const error = new Error(code); error.code = code; throw error; };
function sorted(value) {
  if (Array.isArray(value)) return value.map(sorted);
  if (!object(value)) return value;
  return Object.fromEntries(Object.keys(value).sort().map(key => [key, sorted(value[key])]));
}
const stable = value => JSON.stringify(sorted(value));
const equal = (a, b) => stable(a) === stable(b);
const exactKeys = (value, required) => object(value) && Object.keys(value).length === required.length && required.every(k => Object.hasOwn(value, k));
const typed = (value, kind) => object(value) && value.kind === kind && uint(value.id);
const pin = value => text(value) || exactKeys(value, ['timber', 'placement']) && text(value.timber) && text(value.placement);
const identity = row => [row.projectScope, row.scenario, row.timber.kind, row.timber.id, row.timber.mark,
  row.placement.kind, row.placement.id, row.placement.mark];
const rootKey = row => stable([row.timber.kind, row.timber.id, row.placement.kind, row.placement.id]);
function rootNodesProved(row) {
  const nodes = row.native && row.native.rootNodes;
  if (!object(nodes) || !object(nodes.timber) || !object(nodes.placement)) return false;
  return ['timber', 'placement'].every(kind => nodes[kind].key === kind + ':' + row[kind].id &&
    nodes[kind].kind === kind && nodes[kind].id === row[kind].id && uint(nodes[kind].id)) &&
    nodes.timber.placed === true && nodes.timber.surface === row.placement.id;
}
function exactSupport(supports) {
  const source = end => object(end) && ['boundary', 'placement', 'timber', 'column', 'beam'].includes(end.kind) && uint(end.id);
  if (Array.isArray(supports)) return supports.length === 2 && supports.every(end => source(end) && text(end.faceSelector));
  return object(supports) && ['start', 'finish'].every(side => object(supports[side]) && supports[side].status === 'exact' &&
    object(supports[side].relation) && source(supports[side].relation.source));
}
function trace(row) {
  return {ref: row.ref, kind: row.kind, projectScope: row.projectScope, scenario: row.scenario,
    timber: copy(row.timber), placement: copy(row.placement),
    modelRecordId: row.model === null ? null : row.model.recordId,
    modelRecordSha256: row.model === null ? null : row.model.recordSha256,
    readPin: row.native.readPin, definitionPin: copy(row.native.definitionPin), effectivePin: copy(row.native.effectivePin),
    content: copy(row.native.content)};
}
function evaluate(data) {
  if (!object(data) || data.studySchema !== 'U476-facts/1') fail('U476_FACTS_SCHEMA');
  const rows = data.representations, currentRows = data.current, items = data.declarations.items, excluded = data.declarations.excluded;
  if (![rows, currentRows, items, excluded].every(Array.isArray)) fail('U476_FACTS_SHAPE');
  const diagnostics = [];
  const add = (severity, code, ref = '') => diagnostics.push({severity, code, ref});
  const byRef = new Map(rows.map(row => [row.ref, row]));
  const current = new Map(currentRows.map(row => [rootKey(row), row]));
  if (byRef.size !== rows.length || current.size !== currentRows.length) add('INVALID', 'DUPLICATE_INPUT_FACT');
  if (items.length > LIMITS.items || rows.length > LIMITS.representations || Object.keys(data.context.modelPins).length > LIMITS.models) add('INVALID', 'CAPACITY');
  // U476_WITHDRAW_CONTEXT
  if (!equal(data.context, data.endContext)) add('INCOMPLETE', 'READ_CONTEXT_CHANGED');
  const keys = new Set(), memberships = new Map();
  const own = (ref, allocation) => { if (!memberships.has(ref)) memberships.set(ref, []); memberships.get(ref).push(allocation); };
  for (const item of items) {
    if (!positive(item.itemKey) || keys.has(item.itemKey)) add('INVALID', 'ITEM_KEY');
    keys.add(item.itemKey);
    if (!item.members.length || !item.members.includes(item.representative)) add('INVALID', 'REPRESENTATIVE');
    for (const ref of item.members) own(ref, item.itemKey);
  }
  for (const ref of excluded) own(ref, 'excluded');
  for (const [ref, owners] of memberships) if (!byRef.has(ref) || owners.length !== 1) add('INVALID', 'REPRESENTATION_PARTITION', ref);
  const included = rows.filter(row => !excluded.includes(row.ref));
  // U476_WITHDRAW_ALL_MEMBERS
  for (const row of included) {
    const at = (severity, code) => add(severity, code, row.ref);
    if (!memberships.has(row.ref)) at('INCOMPLETE', 'ITEM_DECLARATION_REQUIRED');
    if (row.projectScope !== data.context.projectScope || row.scenario !== data.context.scenario) at('UNSUPPORTED', 'CONTEXT_OUTSIDE_SCOPE');
    if (!['live', 'model'].includes(row.kind) || row.category !== 'ordinary-d7') at('UNSUPPORTED', 'REPRESENTATION_KIND');
    if (!typed(row.timber, 'timber') || !typed(row.placement, 'placement')) at('INVALID', 'TYPED_ROOT');
    if (!text(row.timber.mark) || !text(row.placement.mark)) at('INCOMPLETE', 'SOURCE_IDENTITY_UNKNOWN');
    if (row.native.complete !== true) at('INCOMPLETE', 'NATIVE_READ_INCOMPLETE');
    if (!pin(row.native.definitionPin) || !pin(row.native.effectivePin)) at('INCOMPLETE', 'SOURCE_PIN_MISSING');
    // U476_WITHDRAW_TYPED_ROOT
    if (!rootNodesProved(row)) at('INCOMPLETE', 'SOURCE_TYPED_ROOT_UNPROVEN');
    if (['material', 'direction', 'surface', 'placement', 'supports', 'typedSources'].some(field => row.native.content[field] == null)) at('INCOMPLETE', 'SOURCE_DETAIL_MISSING');
    // U476_WITHDRAW_SUPPORT
    if (!exactSupport(row.native.content.supports)) at('INCOMPLETE', 'SOURCE_SUPPORT_UNPROVEN');
    if (row.kind === 'model') {
      const model = row.model;
      if (!model || model.sourceKind !== 'ordinary-plan' || model.inputOutcome !== 'COMPLETE' || model.resultOutcome !== 'COMPLETE') at('UNSUPPORTED', 'MODEL_DUAL_VALIDATION');
      else if (!model.inputTimbers.includes(row.timber.id)) at('INVALID', 'MODEL_INPUT_ROOT');
      if (model && !equal(data.context.modelPins[model.recordId], {owner: model.owner, recordSha256: model.recordSha256, readPin: row.native.readPin})) at('INCOMPLETE', 'MODEL_RECORD_CHANGED');
    } else if (row.kind === 'live' && row.native.readPin !== data.context.liveReadPin) at('INCOMPLETE', 'MIXED_LIVE_READ');
    const now = current.get(rootKey(row));
    if (!now) at('INCOMPLETE', 'SOURCE_ABSENT');
    else {
      if (now.native.complete !== true || now.native.readPin !== data.context.liveReadPin || !pin(now.native.definitionPin) || !pin(now.native.effectivePin) || !rootNodesProved(now)) at('INCOMPLETE', 'CURRENT_SOURCE_INCOMPLETE');
      // U476_WITHDRAW_IDENTITY
      if (!equal(identity(row), identity(now))) at('INCOMPLETE', 'SOURCE_REPLACED');
      // U476_WITHDRAW_CONTENT
      if (['definitionPin', 'effectivePin', 'content'].some(axis => !equal(row.native[axis], now.native[axis]))) at('INCOMPLETE', 'SOURCE_CONTENT_CHANGED');
    }
  }
  for (const item of items) {
    const group = item.members.map(ref => byRef.get(ref)).filter(Boolean);
    for (const row of group.slice(1)) if (!equal(identity(row), identity(group[0]))) add('INCOMPLETE', 'MANUAL_GROUP_SOURCE_MISMATCH', row.ref);
  }
  const sourceOwners = new Map();
  for (const row of included) {
    const id = stable(identity(row));
    if (!sourceOwners.has(id)) sourceOwners.set(id, new Set());
    sourceOwners.get(id).add(memberships.get(row.ref)?.[0] ?? ('pending:' + row.ref));
  }
  // U476_WITHDRAW_EXPLICIT_GROUP
  for (const owners of sourceOwners.values()) if (owners.size > 1) add('INCOMPLETE', 'DUPLICATE_SOURCE_NEEDS_REVIEW');
  const unique = [...new Map(diagnostics.map(d => [stable(d), d])).values()];
  unique.sort((a, b) => order(a.code, b.code) || order(a.ref, b.ref) || order(a.severity, b.severity));
  const rank = {INCOMPLETE: 1, UNSUPPORTED: 2, INVALID: 3};
  let status = included.length ? 'COMPLETE' : 'EMPTY';
  for (const d of unique) if ((rank[d.severity] || 0) > (rank[status] || 0)) status = d.severity;
  const length = list => list.reduce((sum, row) => sum + row.native.content.L, 0);
  const result = {studySchema: 'U476-result/1', researchOnly: true, status, diagnostics: unique,
    rawRows: copy([...rows].sort((a, b) => order(a.ref, b.ref))), excluded: [...excluded].sort(order), items: [], itemCount: null,
    accounting: {rawRepresentedLengthMm: length(rows), excludedLengthMm: length(rows.filter(row => excluded.includes(row.ref))),
      includedRepresentedLengthMm: length(included), physicalItemLengthMm: null, removedAliasLengthMm: null}};
  if (!['COMPLETE', 'EMPTY'].includes(status)) return result;
  for (const item of [...items].sort((a, b) => a.itemKey - b.itemKey)) {
    const row = byRef.get(item.representative), content = row.native.content;
    result.items.push({itemKey: item.itemKey, representative: item.representative, members: [...item.members].sort(order),
      sourceIdentity: identity(row), A: content.A, B: content.B, L: content.L, material: copy(content.material),
      provenance: [...item.members].sort(order).map(ref => trace(byRef.get(ref)))});
  }
  result.itemCount = result.items.length;
  result.accounting.physicalItemLengthMm = result.items.reduce((sum, item) => sum + item.L, 0);
  // U476_WITHDRAW_CONSERVATION
  result.accounting.removedAliasLengthMm = result.items.reduce((sum, item) => sum + (item.members.length - 1) * item.L, 0);
  return result;
}

/* Strict finite JSON inspection happens before stringify/copy. No accessors,
 * sparse arrays, cycles, exotic prototypes, undefined, or non-finite numbers. */
function inspectJSON(value) {
  let nodes = 0;
  const ancestors = new Set();
  function visit(item, depth) {
    if (++nodes > LIMITS.nodes) fail('U476_CAPACITY_NODES');
    if (depth > LIMITS.depth) fail('U476_CAPACITY_DEPTH');
    if (item === null || typeof item === 'boolean') return;
    if (typeof item === 'string') { if (item.length > 4096) fail('U476_CAPACITY_STRING'); return; }
    if (typeof item === 'number' && Number.isFinite(item) && !Object.is(item, -0)) return;
    if (!item || typeof item !== 'object' || ancestors.has(item) || Object.getOwnPropertySymbols(item).length) fail('U476_FINITE_JSON');
    const array = Array.isArray(item), proto = Object.getPrototypeOf(item);
    if (array ? proto !== Array.prototype : proto !== null && proto !== Object.prototype) fail('U476_FINITE_JSON');
    ancestors.add(item);
    const names = Object.getOwnPropertyNames(item).filter(key => !array || key !== 'length');
    if (array && names.length !== item.length) fail('U476_FINITE_JSON');
    for (let i = 0; i < names.length; i++) {
      const key = names[i], descriptor = Object.getOwnPropertyDescriptor(item, key);
      if (!descriptor.enumerable || !Object.hasOwn(descriptor, 'value') || array && key !== String(i)) fail('U476_FINITE_JSON');
      if (key.length > 4096) fail('U476_CAPACITY_STRING');
      visit(descriptor.value, depth + 1);
    }
    ancestors.delete(item);
  }
  visit(value, 0);
  if (Buffer.byteLength(JSON.stringify(value), 'utf8') > LIMITS.bytes) fail('U476_CAPACITY_BYTES');
  return nodes;
}
function tupleOf(member) {
  return [member.kind, member.kind === 'model' ? member.recordId : null, 'timber', member.timber.id, 'placement', member.placement.id];
}
function pairPin(value) { return typeof value === 'string' ? {timber: value, placement: value} : value == null ? null : copy(value); }
function memberOf(row) {
  const member = {kind: row.kind, projectScope: row.projectScope, scenario: row.scenario,
    timber: copy(row.timber), placement: copy(row.placement), definitionPin: pairPin(row.native.definitionPin), effectivePin: pairPin(row.native.effectivePin)};
  if (row.kind === 'model') { member.recordId = row.model?.recordId ?? null; member.recordSha256 = row.model?.recordSha256 ?? null; }
  return member;
}
function validateMember(member, scope, scenario) {
  const fields = ['kind', 'projectScope', 'scenario', 'timber', 'placement', 'definitionPin', 'effectivePin'];
  if (member?.kind === 'model') fields.push('recordId', 'recordSha256');
  if (!exactKeys(member, fields) || !['live', 'model'].includes(member.kind)) fail('U476_MEMBER_FIELDS');
  if (member.projectScope !== scope || member.scenario !== scenario) fail('U476_MEMBER_CONTEXT');
  for (const kind of ['timber', 'placement']) {
    if (!exactKeys(member[kind], ['kind', 'id', 'mark']) || !typed(member[kind], kind) || !text(member[kind].mark)) fail('U476_MEMBER_ROOT');
  }
  for (const axis of ['definitionPin', 'effectivePin']) if (!exactKeys(member[axis], ['timber', 'placement']) ||
    !hash(member[axis].timber) || !hash(member[axis].placement)) fail('U476_MEMBER_PIN');
  if (member.kind === 'model' && (!text(member.recordId) || !hash(member.recordSha256))) fail('U476_MODEL_PIN');
}
function memberOrder(a, b) {
  return order(a.kind === 'live' ? 0 : 1, b.kind === 'live' ? 0 : 1) ||
    order(a.recordId || '', b.recordId || '') || a.timber.id - b.timber.id || a.placement.id - b.placement.id;
}
function canonicalMember(member) {
  const result = {kind: member.kind, projectScope: member.projectScope, scenario: member.scenario,
    timber: {kind: 'timber', id: member.timber.id, mark: member.timber.mark},
    placement: {kind: 'placement', id: member.placement.id, mark: member.placement.mark},
    definitionPin: {timber: member.definitionPin.timber, placement: member.definitionPin.placement},
    effectivePin: {timber: member.effectivePin.timber, placement: member.effectivePin.placement}};
  if (member.kind === 'model') {result.recordId = member.recordId; result.recordSha256 = member.recordSha256;}
  return result;
}
function validateDocument(document) {
  inspectJSON(document);
  if (!exactKeys(document, ['schema', 'projectScope', 'scenario', 'nextItemKey', 'items', 'excluded']) || document.schema !== DOCUMENT_SCHEMA) fail('U476_DOCUMENT_SCHEMA');
  if (!text(document.projectScope) || !text(document.scenario) || !uint(document.nextItemKey) || !Array.isArray(document.items) || !Array.isArray(document.excluded)) fail('U476_DOCUMENT_SHAPE');
  if (document.items.length > LIMITS.items) fail('U476_CAPACITY_ITEMS');
  const keys = new Set(), members = [], seen = new Set(), models = new Set();
  for (const item of document.items) {
    if (!exactKeys(item, ['itemKey', 'members', 'representative']) || !positive(item.itemKey) || keys.has(item.itemKey)) fail('U476_ITEM_KEY');
    keys.add(item.itemKey);
    if (!Array.isArray(item.members) || !item.members.length || !Array.isArray(item.representative)) fail('U476_REPRESENTATIVE');
    for (const member of item.members) validateMember(member, document.projectScope, document.scenario);
    if (!item.members.some(member => equal(tupleOf(member), item.representative))) fail('U476_REPRESENTATIVE');
    members.push(...item.members);
  }
  for (const member of document.excluded) validateMember(member, document.projectScope, document.scenario);
  members.push(...document.excluded);
  if (members.length > LIMITS.representations) fail('U476_CAPACITY_REPRESENTATIONS');
  for (const member of members) {
    const key = stable(tupleOf(member));
    if (seen.has(key)) fail('U476_REPRESENTATION_PARTITION');
    seen.add(key);
    if (member.kind === 'model') models.add(member.recordId);
  }
  if (models.size > LIMITS.models) fail('U476_CAPACITY_MODELS');
  if (document.nextItemKey !== 0 && [...keys].some(key => key >= document.nextItemKey)) fail('U476_HIGH_WATER');
  const canonical = {schema: DOCUMENT_SCHEMA, projectScope: document.projectScope, scenario: document.scenario, nextItemKey: document.nextItemKey,
    items: [...document.items].sort((a, b) => a.itemKey - b.itemKey).map(item => ({itemKey: item.itemKey,
      members: [...item.members].sort(memberOrder).map(canonicalMember), representative: copy(item.representative)})),
    excluded: [...document.excluded].sort(memberOrder).map(canonicalMember)};
  if (Buffer.byteLength(JSON.stringify(canonical), 'utf8') + 1 > LIMITS.bytes) fail('U476_CAPACITY_BYTES');
  return canonical;
}
function serializeDocument(document) { return Buffer.from(JSON.stringify(validateDocument(document)) + '\n', 'utf8'); }

/* JSON.parse alone erases duplicate object keys. This finite parser preserves
 * that rejection, decodes escaped keys, and rejects malformed UTF-8 first. */
function parseDocument(bytes) {
  const input = Buffer.isBuffer(bytes) ? bytes : typeof bytes === 'string' ? Buffer.from(bytes, 'utf8') : fail('U476_DOCUMENT_BYTES');
  if (input.length > LIMITS.bytes) fail('U476_CAPACITY_BYTES');
  let source;
  try { source = new TextDecoder('utf-8', {fatal: true}).decode(input); } catch { fail('U476_DOCUMENT_UTF8'); }
  let index = 0, nodes = 0;
  const whitespace = () => {while (/[\x20\t\r\n]/.test(source[index] || '') && index < source.length) index++;};
  const string = () => {
    const start = index++;
    while (index < source.length) {
      const c = source[index++];
      if (c === '\\') index++;
      else if (c === '"') {
        try {return JSON.parse(source.slice(start, index));} catch {fail('U476_DOCUMENT_JSON');}
      }
    }
    fail('U476_DOCUMENT_JSON');
  };
  function value(depth) {
    whitespace();
    if (++nodes > LIMITS.nodes) fail('U476_CAPACITY_NODES');
    if (depth > LIMITS.depth) fail('U476_CAPACITY_DEPTH');
    const c = source[index];
    if (c === '"') return string();
    if (c === '{') {
      index++; whitespace(); const result = Object.create(null), seen = new Set();
      if (source[index] === '}') {index++; return result;}
      while (true) {
        whitespace(); if (source[index] !== '"') fail('U476_DOCUMENT_JSON');
        const key = string();
        if (seen.has(key)) fail('U476_DUPLICATE_JSON_KEY');
        seen.add(key); whitespace(); if (source[index++] !== ':') fail('U476_DOCUMENT_JSON');
        result[key] = value(depth + 1); whitespace();
        const end = source[index++]; if (end === '}') return result;
        if (end !== ',') fail('U476_DOCUMENT_JSON');
      }
    }
    if (c === '[') {
      index++; whitespace(); const result = [];
      if (source[index] === ']') {index++; return result;}
      while (true) {
        result.push(value(depth + 1)); whitespace();
        const end = source[index++]; if (end === ']') return result;
        if (end !== ',') fail('U476_DOCUMENT_JSON');
      }
    }
    const token = /^(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)/.exec(source.slice(index));
    if (!token) fail('U476_DOCUMENT_JSON');
    index += token[0].length;
    const result = JSON.parse(token[0]);
    if (typeof result === 'number' && (!Number.isFinite(result) || Object.is(result, -0))) fail('U476_FINITE_JSON');
    return result;
  }
  const document = value(0); whitespace();
  if (index !== source.length) fail('U476_DOCUMENT_JSON');
  return validateDocument(document);
}
function evaluateDocument(document, facts) {
  const valid = validateDocument(document), data = copy(facts);
  const declared = valid.items.flatMap(item => item.members).concat(valid.excluded);
  const wanted = new Set(declared.map(member => stable(tupleOf(member))));
  // A document is a selection. Unselected available facts do not silently join
  // its demand universe. Absent excluded rows stay declared without demand.
  data.representations = data.representations.filter(row => wanted.has(stable(tupleOf(memberOf(row)))));
  const grouped = new Map();
  for (const row of data.representations) {
    const key = stable(tupleOf(memberOf(row)));
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push(row);
  }
  const ambiguous = new Set([...grouped].filter(([, rows]) => rows.length > 1).map(([key]) => key));
  // No last-wins choice is made for a duplicated selected representation.
  const byTuple = new Map([...grouped].filter(([, rows]) => rows.length === 1).map(([key, rows]) => [key, rows[0]]));
  const diagnostics = [];
  const ref = member => byTuple.get(stable(tupleOf(member)))?.ref ?? 'missing:' + stable(tupleOf(member));
  const present = member => byTuple.has(stable(tupleOf(member)));
  const absent = member => !present(member) && !ambiguous.has(stable(tupleOf(member)));
  const missingIncluded = valid.items.flatMap(item => item.members.filter(absent).map(tupleOf));
  const missingExcluded = valid.excluded.filter(absent).map(tupleOf);
  for (const key of ambiguous) diagnostics.push({severity: 'INVALID', code: 'DUPLICATE_REPRESENTATION_FACT', ref: key});
  data.declarations = {items: valid.items.filter(item => item.members.every(present)).map(item => ({itemKey: item.itemKey,
    members: item.members.map(ref), representative: byTuple.get(stable(item.representative)).ref})),
    excluded: valid.excluded.filter(present).map(ref)};
  if (valid.projectScope !== data.context.projectScope || valid.scenario !== data.context.scenario) diagnostics.push({severity: 'UNSUPPORTED', code: 'DOCUMENT_CONTEXT_CHANGED', ref: ''});
  for (const item of valid.items) for (const member of item.members) {
    const row = byTuple.get(stable(tupleOf(member)));
    if (!row && !ambiguous.has(stable(tupleOf(member)))) diagnostics.push({severity: 'INCOMPLETE', code: 'DECLARATION_SOURCE_MISSING', ref: ref(member)});
    else if (!row) continue;
    else if (!equal(canonicalMember(member), memberOf(row))) diagnostics.push({severity: 'INCOMPLETE', code: 'DECLARATION_PIN_CHANGED', ref: ref(member)});
  }
  const answer = evaluate(data);
  answer.observation = {scope: 'available-declared-representations', declaredCount: declared.length, observedCount: data.representations.length,
    missingIncluded, missingExcluded, ambiguousSelected: [...ambiguous].sort(order).map(key => JSON.parse(key))};
  if (diagnostics.length) {
    answer.diagnostics.push(...diagnostics);
    answer.diagnostics.sort((a, b) => order(a.code, b.code) || order(a.ref, b.ref) || order(a.severity, b.severity));
    const rank = {COMPLETE: 0, EMPTY: 0, INCOMPLETE: 1, UNSUPPORTED: 2, INVALID: 3};
    answer.status = answer.diagnostics.reduce((s, d) => rank[d.severity] > rank[s] ? d.severity : s, answer.status);
    answer.items = []; answer.itemCount = null;
    answer.accounting.physicalItemLengthMm = null; answer.accounting.removedAliasLengthMm = null;
  }
  return answer;
}
class StudyHistory {
  #document; #highWater; #revision = 0; #undo = []; #redo = []; #drafts = new WeakMap(); #saved;
  constructor(document) {
    this.#document = validateDocument(document); this.#highWater = this.#document.nextItemKey;
    this.#saved = serializeDocument(this.#document).toString('utf8');
  }
  static reopen(bytes) { return new StudyHistory(parseDocument(bytes)); }
  view() {
    return {document: copy(this.#document), revision: this.#revision, undoDepth: this.#undo.length, redoDepth: this.#redo.length,
      dirty: serializeDocument(this.#document).toString('utf8') !== this.#saved, needsVerification: true};
  }
  begin() {
    const draft = {revision: this.#revision, document: copy(this.#document)};
    this.#drafts.set(draft, {revision: this.#revision, active: true}); return draft;
  }
  cancel(draft) { const ticket = this.#drafts.get(draft); if (ticket) ticket.active = false; return false; }
  commit(draft) {
    const ticket = this.#drafts.get(draft);
    if (!ticket?.active) fail('U476_DRAFT_UNKNOWN');
    if (ticket.revision !== this.#revision || draft.revision !== ticket.revision) fail('U476_DRAFT_STALE');
    inspectJSON(draft.document);
    const next = copy(draft.document), existing = new Set(this.#document.items.map(item => item.itemKey));
    if (next.projectScope !== this.#document.projectScope || next.scenario !== this.#document.scenario) fail('U476_DRAFT_CONTEXT');
    if (next.nextItemKey !== this.#highWater) fail('U476_DRAFT_HIGH_WATER');
    if (!Array.isArray(next.items)) fail('U476_DOCUMENT_SHAPE');
    let highWater = this.#highWater;
    const allocatedKeys = [];
    for (const item of next.items) {
      if (item.itemKey === null) {
        if (highWater === 0) fail('U476_ITEM_KEY_EXHAUSTED');
        item.itemKey = highWater; allocatedKeys.push(highWater);
        highWater = highWater === MAX_U32 ? 0 : highWater + 1;
      } else if (!existing.has(item.itemKey)) fail('U476_ITEM_KEY_NOT_CURRENT');
    }
    next.nextItemKey = highWater;
    const validated = validateDocument(next);
    if (equal(validated, this.#document)) {ticket.active = false;return {changed: false, allocatedKeys: [], document: copy(this.#document), revision: this.#revision};}
    this.#undo.push(copy(this.#document)); this.#redo = [];
    this.#document = validated; this.#highWater = highWater; this.#revision++; ticket.active = false;
    return {changed: true, allocatedKeys, document: copy(this.#document), revision: this.#revision};
  }
  #restore(source, target) {
    if (!source.length) return false;
    target.push(copy(this.#document)); this.#document = source.pop();
    // U476_WITHDRAW_HIGH_WATER
    this.#document.nextItemKey = this.#highWater;
    this.#document = validateDocument(this.#document); this.#revision++; return true;
  }
  undo() { return this.#restore(this.#undo, this.#redo); }
  redo() { return this.#restore(this.#redo, this.#undo); }
  save() { return serializeDocument(this.#document); }
  evaluate(facts) { return evaluateDocument(this.#document, facts); }
}
function runHistory(input) {
  let history = new StudyHistory(input.document);
  const initial = history.view(), steps = [];
  for (const operation of input.operations) {
    try {
      let result;
      if (['commit', 'cancel'].includes(operation.op)) {
        const draft = history.begin(); draft.document = copy(operation.document);
        result = history[operation.op](draft);
      } else if (['undo', 'redo'].includes(operation.op)) result = history[operation.op]();
      else if (operation.op === 'reopen') {history = StudyHistory.reopen(history.save()); result = true;}
      else fail('U476_HISTORY_OPERATION');
      steps.push({op: operation.op, ok: true, result, view: history.view()});
    } catch (error) {steps.push({op: operation.op, ok: false, error: error.code || error.message, view: history.view()});}
  }
  return {initial, steps, final: history.view()};
}
module.exports = {LIMITS, DOCUMENT_SCHEMA, evaluate, memberOf, tupleOf, validateDocument, serializeDocument, parseDocument, evaluateDocument, StudyHistory, runHistory};
if (require.main === module) {
  try {
    const input = JSON.parse(fs.readFileSync(0, 'utf8'));
    const mode = process.argv[2] || 'evaluate';
    const output = mode === 'batch' ? input.map(evaluate) : mode === 'history-batch' ? input.map(runHistory) : mode === 'history' ? runHistory(input) : mode === 'evaluate' ? evaluate(input) : fail('U476_CLI_MODE');
    process.stdout.write(JSON.stringify(output) + '\n');
  } catch (error) {process.stderr.write((error.code || error.message) + '\n'); process.exitCode = 1;}
}
