/* Finite portable editor data. These records never declare native geometry. */
(function (root, factory) {
  const api = factory(typeof module === "object" && module.exports ? require("./source-plane.js") : root.GeometrySourcePlane);
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.GeometryFeatureAttachments = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (Rooms) {
  "use strict";
  const SCHEMA = "geometry-feature-attachments/1";
  const GRID_SCHEMA = "grid-editor-draft/1", GRID_KIND = "grid-draft";
  const ROOM_KIND = "source-rooms", ROOM_SCHEMA = "source-rooms/1", ROOM_CAPABILITY = "source-room-collection/1";
  const ROOM_HISTORY_SCHEMA = "source-rooms/2", ROOM_HISTORY_CAPABILITY = "source-room-history/1";
  const MAX_BYTES = 128 * 1024, MAX_STRING = 4096;
  const MAX_ROOM_BYTES = 8 * 1024 * 1024;
  const sourceFields = ["igName", "igMainAlong", ...["U", "V"].flatMap(axis => [
    "Source", ...["Step", "Phase", "Panel", "Gap", "Anchor", "Stagger"].flatMap(field => [field, field + "Source"])
  ].map(field => "ig" + axis + field))];
  const bindingFields = ["igSystem", "igBoundary", "igVertex", "igCellI", "igCellJ", "igAnchorUN", "igAnchorUD", "igAnchorVN", "igAnchorVD"];
  const fail = message => { throw new Error(message); };
  const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
  const keys = (value, required, optional = []) => object(value) && required.every(k => Object.hasOwn(value, k)) &&
    Object.keys(value).every(k => required.includes(k) || optional.includes(k));
  const uint = value => Number.isSafeInteger(value) && value >= 0 && value <= 4294967295;
  const hash = value => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
  const nativePrototype = (proto, name) => {
    const constructor = proto && Object.getOwnPropertyDescriptor(proto, "constructor")?.value;
    return typeof constructor === "function" && constructor.prototype === proto &&
      Function.prototype.toString.call(constructor) === Function.prototype.toString.call(name === "Object" ? Object : Array) && !Object.hasOwn(proto, "toJSON");
  };
  const objectPrototype = proto => proto !== null && Object.getPrototypeOf(proto) === null && nativePrototype(proto, "Object");
  const plainObject = value => Object.getPrototypeOf(value) === null || objectPrototype(Object.getPrototypeOf(value));
  // Reject values that JSON.stringify would silently change, and bound traversal
  // before serializing or copying caller-owned data.
  function boundedJSON(value, roomEnvelope = false) {
    const maxNodes = roomEnvelope ? 600000 : 4096, maxArray = roomEnvelope ? 10000 : 128;
    const ownValue = (node,key) => node !== null && typeof node === "object" ? Object.getOwnPropertyDescriptor(node,key)?.value : undefined;
    const historyRecord = node => ownValue(node,"kind") === ROOM_KIND && ownValue(node,"schema") === ROOM_HISTORY_SCHEMA &&
      ownValue(ownValue(node,"value"),"schema") === ROOM_HISTORY_SCHEMA;
    function legacyGeometry(path) {
      if (!roomEnvelope) return false;
      const offset = path.length === 5 && historyRecord(value) ? 0 :
        path.length === 7 && ownValue(value,"schema") === SCHEMA && path[0] === "records" && Number.isInteger(path[1]) &&
        historyRecord(ownValue(ownValue(value,"records"),path[1])) ? 2 : -1;
      return offset >= 0 && path[offset] === "value" && path[offset+1] === "legacyHistory" && Number.isInteger(path[offset+2]) &&
        path[offset+3] === "reconstructionReview" && path[offset+4] === "geometry";
    }
    const maxBytes = roomEnvelope ? MAX_ROOM_BYTES : MAX_BYTES;
    let count = 0, bytes = 0;
    const charge = size => {bytes += size;if (bytes > maxBytes) fail("功能附件超過容量上限。");};
    function stringBytes(value) {
      charge(2);
      for (let index = 0; index < value.length; index++) {
        const code = value.charCodeAt(index);
        if (code < 128) charge(code < 32 ? [8,9,10,12,13].includes(code) ? 2 : 6 : code === 34 || code === 92 ? 2 : 1);
        else if (code < 2048) charge(2);
        else if (code >= 0xd800 && code <= 0xdbff && value.charCodeAt(index+1) >= 0xdc00 && value.charCodeAt(index+1) <= 0xdfff) {charge(4);index++;}
        else charge(code >= 0xd800 && code <= 0xdfff ? 6 : 3);
      }
    }
    function visit(item, depth, path = []) {
      if (++count > maxNodes || depth > 12) fail("功能附件過大或巢狀過深。");
      if (item === null) {charge(4);return;}
      if (typeof item === "boolean") {charge(item ? 4 : 5);return;}
      if (typeof item === "number" && Number.isFinite(item)) {charge(JSON.stringify(item).length);return;}
      if (typeof item === "string" && item.length <= (legacyGeometry(path) ? 100000 : MAX_STRING)) {stringBytes(item);return;}
      if (Array.isArray(item)) {
        const proto = Object.getPrototypeOf(item);
        if (!nativePrototype(proto, "Array") ||
            !objectPrototype(Object.getPrototypeOf(proto)) || Object.getOwnPropertySymbols(item).length ||
            item.length > maxArray || Object.getOwnPropertyNames(item).length !== item.length + 1) fail("功能附件陣列不合法。");
        charge(2);
        for (let index = 0; index < item.length; index++) {
          if (index) charge(1);
          const descriptor = Object.getOwnPropertyDescriptor(item, index);
          if (!descriptor?.enumerable || !Object.hasOwn(descriptor, "value")) fail("功能附件陣列不完整。");
          visit(descriptor.value, depth + 1, [...path,index]);
        }
        return;
      }
      if (object(item) && plainObject(item)) {
        if (Object.getOwnPropertySymbols(item).length) fail("功能附件欄位不合法。");
        charge(2);let fields = 0;
        for (const key of Object.getOwnPropertyNames(item)) {
          const descriptor = Object.getOwnPropertyDescriptor(item, key);
          if (["__proto__", "constructor", "prototype"].includes(key) || key.length > 100 ||
              !descriptor.enumerable || !Object.hasOwn(descriptor, "value")) fail("功能附件欄位不合法。");
          if (fields++) charge(1);
          stringBytes(key);charge(1);
          visit(descriptor.value, depth + 1, [...path,key]);
        }
        return;
      }
      fail("功能附件必須是有界 plain JSON。");
    }
    visit(value, 0);
  }
  function validateReference(ref) {
    if (ref?.kind === "parameter-field") {
      if (!keys(ref, ["kind", "parameterId", "fieldId", "fingerprint"]) ||
          !uint(ref.parameterId) || !uint(ref.fieldId) || !hash(ref.fingerprint)) fail("網格草稿參數引用不合法。");
    } else {
      const boundary = ref?.kind === "boundary";
      if (!keys(ref, ["kind", "id", "fingerprint"], boundary ? ["vertexKeysFingerprint"] : []) ||
          !["grid-system", "grid-binding", "boundary"].includes(ref.kind) || !uint(ref.id) ||
          (boundary && (ref.id === 0 || !hash(ref.vertexKeysFingerprint))) || !hash(ref.fingerprint))
        fail("網格草稿的已發布引用不合法。");
    }
    return ref;
  }
  function referenceKey(ref) {
    return ref.kind === "parameter-field" ? `${ref.kind}:${ref.parameterId}:${ref.fieldId}` : `${ref.kind}:${ref.id}`;
  }
  function validateGridDraft(value) {
    boundedJSON(value);
    if (!keys(value, ["schema", "draftId", "kind", "intent", "baseRef", "inputRefs", "rawForm"]) ||
        value.schema !== GRID_SCHEMA || typeof value.draftId !== "string" || !/^[\w-]{1,100}$/.test(value.draftId) ||
        !["source", "binding"].includes(value.kind) || !["create", "edit"].includes(value.intent)) fail("網格編輯草稿版本或身分不合法。");
    if (value.intent === "create" && value.baseRef !== null || value.intent === "edit" &&
        (value.baseRef === null || validateReference(value.baseRef).kind !== (value.kind === "source" ? "grid-system" : "grid-binding")))
      fail("網格草稿的建立／編輯意圖不合法。");
    if (!Array.isArray(value.inputRefs) || value.inputRefs.length > 20) fail("網格草稿來源清單不合法。");
    const seen = new Set();
    for (const ref of value.inputRefs) {
      validateReference(ref);
      const key = referenceKey(ref);
      if (seen.has(key)) fail("網格草稿來源引用重複。");
      seen.add(key);
    }
    const fields = value.kind === "source" ? sourceFields : bindingFields;
    if (!keys(value.rawForm, fields) || fields.some(field => typeof value.rawForm[field] !== "string" || value.rawForm[field].length > MAX_STRING))
      fail("網格草稿原始輸入欄位不完整或不合法。");
    // Empty, incorrect, inactive and whitespace-bearing fields are intentional.
    // The native preview validator alone decides whether they may be published.
    return value;
  }
  function validateRecord(record) {
    boundedJSON(record, true);
    if (!keys(record, ["kind", "schema", "value"]))
      fail("功能附件種類或版本不支援。");
    if (record.kind === GRID_KIND && record.schema === GRID_SCHEMA) {
      boundedJSON(record); validateGridDraft(record.value);
    } else if (record.kind === ROOM_KIND && [ROOM_SCHEMA,ROOM_HISTORY_SCHEMA].includes(record.schema)) {
      if (!Rooms || Rooms.SCHEMA !== ROOM_SCHEMA || Rooms.CAPABILITY !== ROOM_CAPABILITY || Rooms.HISTORY_SCHEMA !== ROOM_HISTORY_SCHEMA || Rooms.HISTORY_CAPABILITY !== ROOM_HISTORY_CAPABILITY) fail("房間來源驗證器尚未就緒。");
      if (record.value?.schema !== record.schema) fail("房間來源附件版本不一致。");
      Rooms.validate(record.value);
    } else fail("功能附件種類或版本不支援。");
    return record;
  }
  function validate(envelope) {
    boundedJSON(envelope, true);
    if (!keys(envelope, ["schema", "records"]) || envelope.schema !== SCHEMA || !Array.isArray(envelope.records) || envelope.records.length > 2)
      fail("功能附件版本或清單不支援。");
    const kinds = new Set();
    for (const record of envelope.records) {
      validateRecord(record);
      if (record.kind === GRID_KIND) boundedJSON({schema:SCHEMA, records:[record]});
      if (kinds.has(record.kind)) fail("功能附件種類重複。");
      kinds.add(record.kind);
    }
    return envelope;
  }
  function assertKind(kind) { if (![GRID_KIND, ROOM_KIND].includes(kind)) fail("功能附件種類不支援。"); }
  function record(kind, value) {
    assertKind(kind);
    const schema = kind === GRID_KIND ? GRID_SCHEMA : value !== null && typeof value === "object" ? Object.getOwnPropertyDescriptor(value,"schema")?.value : undefined;
    return validateRecord({kind, schema, value});
  }
  function capabilities(envelope) { validate(envelope); return envelope.records.flatMap(record => record.kind === GRID_KIND ? [GRID_SCHEMA] :
    record.schema === ROOM_HISTORY_SCHEMA ? [ROOM_CAPABILITY,ROOM_HISTORY_CAPABILITY] : [ROOM_CAPABILITY]).sort(); }
  function sourceRooms(envelope, sources) {
    validate(envelope);
    const value = envelope.records.find(record => record.kind === ROOM_KIND)?.value || null;
    if (value) Rooms.validate(value, sources);
    return value;
  }
  function validateNativeRefs(envelope, objects) {
    const value = sourceRooms(envelope); if (value) Rooms.validateNativeRefs(value, objects);
  }
  function validateNativePins(envelope, definitions) {
    const value = sourceRooms(envelope); if (value) Rooms.validateNativePins(value, definitions);
  }
  function retireRoomBoundary(value, id) { return Rooms.retireBoundary(validateRecord(record(ROOM_KIND, value)).value, id); }
  function changedRoomBoundary(value, id) { return Rooms.boundaryChanged(validateRecord(record(ROOM_KIND, value)).value, id); }
  function unknownRoomHistory(value) { return Rooms.unknownHistory(validateRecord(record(ROOM_KIND, value)).value); }
  function references(value) { validateGridDraft(value); return JSON.parse(JSON.stringify([...(value.baseRef === null ? [] : [value.baseRef]), ...value.inputRefs])); }
  return {SCHEMA, GRID_SCHEMA, GRID_KIND, ROOM_KIND, ROOM_SCHEMA, ROOM_CAPABILITY, ROOM_HISTORY_SCHEMA, ROOM_HISTORY_CAPABILITY, MAX_BYTES, MAX_ROOM_BYTES,
    validateSourceRecords:Rooms.validateSourceRecords, validateReconstructionReviews:Rooms.validateReconstructionReviews,
    sourceFields:Object.freeze(sourceFields), bindingFields:Object.freeze(bindingFields),
    validate, validateRecord, validateGridDraft, assertKind, record, capabilities, references, sourceRooms, validateNativeRefs, validateNativePins,
    retireRoomBoundary, changedRoomBoundary, unknownRoomHistory};
});
