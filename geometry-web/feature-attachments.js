/* Finite portable editor data. These records never declare native geometry. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.GeometryFeatureAttachments = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const SCHEMA = "geometry-feature-attachments/1";
  const GRID_SCHEMA = "grid-editor-draft/1", GRID_KIND = "grid-draft";
  const MAX_BYTES = 128 * 1024, MAX_STRING = 4096;
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
  function boundedJSON(value) {
    let count = 0;
    function visit(item, depth) {
      if (++count > 4096 || depth > 12) fail("功能附件過大或巢狀過深。");
      if (item === null || typeof item === "boolean") return;
      if (typeof item === "number" && Number.isFinite(item)) return;
      if (typeof item === "string" && item.length <= MAX_STRING) return;
      if (Array.isArray(item)) {
        const proto = Object.getPrototypeOf(item);
        if (!nativePrototype(proto, "Array") ||
            !objectPrototype(Object.getPrototypeOf(proto)) || Object.getOwnPropertySymbols(item).length ||
            item.length > 128 || Object.getOwnPropertyNames(item).length !== item.length + 1) fail("功能附件陣列不合法。");
        for (let index = 0; index < item.length; index++) {
          const descriptor = Object.getOwnPropertyDescriptor(item, index);
          if (!descriptor?.enumerable || !Object.hasOwn(descriptor, "value")) fail("功能附件陣列不完整。");
          visit(descriptor.value, depth + 1);
        }
        return;
      }
      if (object(item) && plainObject(item)) {
        if (Object.getOwnPropertySymbols(item).length) fail("功能附件欄位不合法。");
        for (const key of Object.getOwnPropertyNames(item)) {
          const descriptor = Object.getOwnPropertyDescriptor(item, key);
          if (["__proto__", "constructor", "prototype"].includes(key) || key.length > 100 ||
              !descriptor.enumerable || !Object.hasOwn(descriptor, "value")) fail("功能附件欄位不合法。");
          visit(descriptor.value, depth + 1);
        }
        return;
      }
      fail("功能附件必須是有界 plain JSON。");
    }
    visit(value, 0);
    if (new TextEncoder().encode(JSON.stringify(value)).length > MAX_BYTES) fail("功能附件超過 128 KB。");
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
    if (!keys(record, ["kind", "schema", "value"]) || record.kind !== GRID_KIND || record.schema !== GRID_SCHEMA)
      fail("功能附件種類或版本不支援。");
    validateGridDraft(record.value);
    return record;
  }
  function validate(envelope) {
    boundedJSON(envelope);
    if (!keys(envelope, ["schema", "records"]) || envelope.schema !== SCHEMA || !Array.isArray(envelope.records) || envelope.records.length > 1)
      fail("功能附件版本或清單不支援。");
    for (const record of envelope.records) validateRecord(record);
    return envelope;
  }
  function assertKind(kind) { if (kind !== GRID_KIND) fail("功能附件種類不支援。"); }
  function record(kind, value) { assertKind(kind); return validateRecord({kind, schema:GRID_SCHEMA, value}); }
  function capabilities(envelope) { validate(envelope); return envelope.records.length ? [GRID_SCHEMA] : []; }
  function references(value) { validateGridDraft(value); return JSON.parse(JSON.stringify([...(value.baseRef === null ? [] : [value.baseRef]), ...value.inputRefs])); }
  return {SCHEMA, GRID_SCHEMA, GRID_KIND, MAX_BYTES, sourceFields:Object.freeze(sourceFields), bindingFields:Object.freeze(bindingFields),
    validate, validateRecord, validateGridDraft, assertKind, record, capabilities, references};
});
