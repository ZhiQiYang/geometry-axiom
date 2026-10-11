/* Finite portable editor data. These records never declare native geometry. */
(function (root, factory) {
  const api = factory(typeof module === "object" && module.exports ? require("./source-plane.js") : root.GeometrySourcePlane,
    typeof module === "object" && module.exports ? require("./evidence-links.js") : root.EvidenceLinks,
    typeof module === "object" && module.exports ? require("./rule-case-data.js") : root.GeometryRuleCaseData);
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.GeometryFeatureAttachments = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (Rooms, Evidence, Cases) {
  "use strict";
  const SCHEMA = "geometry-feature-attachments/1";
  const CASE_KIND=Cases.KIND, CASE_SCHEMA=Cases.SCHEMA;
  const GRID_SCHEMA = "grid-editor-draft/1", GRID_RULE_SCHEMA = "grid-editor-draft/2", GRID_KIND = "grid-draft";
  const GRID_DRAFTS_SCHEMA = "grid-editor-drafts/1", MAX_GRID_DRAFTS = 16, MAX_GRID_DRAFTS_BYTES = 1024 * 1024;
  const ROOM_KIND = "source-rooms", ROOM_SCHEMA = "source-rooms/1", ROOM_CAPABILITY = "source-room-collection/1";
  const ROOM_HISTORY_SCHEMA = "source-rooms/2", ROOM_HISTORY_CAPABILITY = "source-room-history/1";
  const ROOM_DISPLAY_SCHEMA = "source-rooms/3", ROOM_DISPLAY_CAPABILITY = "source-room-display/1";
  const MAX_BYTES = 128 * 1024, MAX_STRING = 4096;
  const MAX_ROOM_BYTES = 8 * 1024 * 1024;
  const sourceFields = ["igName", "igMainAlong", ...["U", "V"].flatMap(axis => [
    "Source", ...["Step", "Phase", "Panel", "Gap", "Anchor", "Stagger"].flatMap(field => [field, field + "Source"])
  ].map(field => "ig" + axis + field))];
  const bindingFields = ["igSystem", "igBoundary", "igVertex", "igCellI", "igCellJ", "igAnchorUN", "igAnchorUD", "igAnchorVN", "igAnchorVD"];
  const ruleFields = ["name", "selector", "cellI", "cellJ", "divisionsU", "divisionsV"];
  // One representation for current source identity. The legacy representation
  // is retained solely for reading /1 draft pins; it cannot attest to rules.
  const gridSourceDefinition = (row, legacy = false) => row && [row.id, row.mode, row.name, row.mainAlong,
    row.uDefinition, row.vDefinition, ...(legacy ? [] : [row.nextRuleKey ?? 1, row.rules || []])];
  const gridSourceKey = (row, legacy = false) => JSON.stringify(gridSourceDefinition(row, legacy));
  const ruleAwareSource = row => !!row && ((row.rules || []).length > 0 || (row.nextRuleKey ?? 1) !== 1);
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
  // Count the escaped JSON's UTF-8 bytes before serialization or copying. The
  // same counter serves feature records and the complete project manifest.
  function byteCounter(maxBytes, message, reserve = 0) {
    let bytes = reserve;
    const charge = size => {bytes += size;if (bytes > maxBytes) fail(message);};
    function string(value) {
      charge(2);
      for (let index = 0; index < value.length; index++) {
        const code = value.charCodeAt(index);
        if (code < 128) charge(code < 32 ? [8,9,10,12,13].includes(code) ? 2 : 6 : code === 34 || code === 92 ? 2 : 1);
        else if (code < 2048) charge(2);
        else if (code >= 0xd800 && code <= 0xdbff && value.charCodeAt(index+1) >= 0xdc00 && value.charCodeAt(index+1) <= 0xdfff) {charge(4);index++;}
        else charge(code >= 0xd800 && code <= 0xdfff ? 6 : 3);
      }
    }
    charge(0);
    return {charge,string,bytes:()=>bytes};
  }
  function jsonBytes(value, maxBytes, reserve = 0, message = "功能附件超過容量上限。") {
    const counter = byteCounter(maxBytes,message,reserve), ancestors = new Set(), stack = [{item:value}];
    while (stack.length) {
      const frame = stack.at(-1), item = frame.item;
      if (!frame.keys) {
        let scalar = true;
        if (item === null) counter.charge(4);
        else if (typeof item === "boolean") counter.charge(item ? 4 : 5);
        else if (typeof item === "number" && Number.isFinite(item)) counter.charge(JSON.stringify(item).length);
        else if (typeof item === "string") counter.string(item);
        else scalar = false;
        if (scalar) {stack.pop();continue;}
        frame.array = Array.isArray(item);
        if (!item || typeof item !== "object" || (!frame.array && !plainObject(item)) ||
            (frame.array && !nativePrototype(Object.getPrototypeOf(item),"Array")) || Object.getOwnPropertySymbols(item).length || ancestors.has(item))
          fail("專案資料必須是有限 plain JSON。");
        ancestors.add(item);counter.charge(2);
        frame.keys = Object.getOwnPropertyNames(item).filter(key=>!frame.array || key !== "length");frame.index = 0;
      }
      if (frame.index === frame.keys.length) {
        if (frame.array && frame.index !== item.length) fail("專案資料陣列不完整。");
        ancestors.delete(item);stack.pop();continue;
      }
      const key = frame.keys[frame.index], descriptor = Object.getOwnPropertyDescriptor(item,key);
      if (!descriptor.enumerable || !Object.hasOwn(descriptor,"value") || frame.array && key !== String(frame.index)) fail("專案資料欄位不合法。");
      if (frame.index++) counter.charge(1);
      if (!frame.array) {counter.string(key);counter.charge(1);}
      stack.push({item:descriptor.value});
    }
    return counter.bytes();
  }
  // Native edits may change every room to the longest finite lifecycle status.
  // Reserve only that exact growth; history and the public 8 MiB limit stay intact.
  function lifecycleReserve(value) {
    return (value?.rooms || []).reduce((bytes,room) => bytes + "needs-reassociation".length - room.reviewState.length,0);
  }
  // Reject values that JSON.stringify would silently change, and bound traversal
  // before serializing or copying caller-owned data.
  function boundedJSON(value, roomEnvelope = false, markingBytes = 0) {
    const maxNodes = roomEnvelope ? 600000 : 4096, maxArray = roomEnvelope ? 10000 : 128;
    const ownValue = (node,key) => node !== null && typeof node === "object" ? Object.getOwnPropertyDescriptor(node,key)?.value : undefined;
    const historyRecord = node => ownValue(node,"kind") === ROOM_KIND && [ROOM_HISTORY_SCHEMA,ROOM_DISPLAY_SCHEMA].includes(ownValue(node,"schema")) &&
      ownValue(ownValue(node,"value"),"schema") === ownValue(node,"schema");
    function legacyGeometry(path) {
      if (!roomEnvelope) return false;
      const offset = path.length === 5 && historyRecord(value) ? 0 :
        path.length === 7 && ownValue(value,"schema") === SCHEMA && path[0] === "records" && Number.isInteger(path[1]) &&
        historyRecord(ownValue(ownValue(value,"records"),path[1])) ? 2 : -1;
      return offset >= 0 && path[offset] === "value" && path[offset+1] === "legacyHistory" && Number.isInteger(path[offset+2]) &&
        path[offset+3] === "reconstructionReview" && path[offset+4] === "geometry";
    }
    const maxBytes = (roomEnvelope ? MAX_ROOM_BYTES : MAX_BYTES) + markingBytes;
    let count = 0;
    const counter = byteCounter(maxBytes,"功能附件超過容量上限。"), charge = counter.charge, stringBytes = counter.string;
    function visit(item, depth, path = []) {
      const record = path.length===1 && path[0]==="value" ? value :
        path.length===3 && path[0]==="records" && Number.isInteger(path[1]) && path[2]==="value" ? ownValue(ownValue(value,"records"),path[1]) : null;
      if(roomEnvelope && ownValue(record,"kind")===CASE_KIND && ownValue(record,"schema")===CASE_SCHEMA){
        Cases.validate(item);charge(Cases.bounded(item));return;
      }
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
    visit(value, 0);return counter.bytes();
  }
  function validateReference(ref, allowLost = false) {
    const lostKeys = allowLost ? ["lost"] : [];
    if (Object.hasOwn(ref || {}, "lost") && (!allowLost || ref.lost !== true)) fail("曾缺失旗標只准為 true。");
    if (ref?.kind === "parameter-field") {
      if (!keys(ref, ["kind", "parameterId", "fieldId", "fingerprint"], lostKeys) ||
          !uint(ref.parameterId) || !uint(ref.fieldId) || !hash(ref.fingerprint)) fail("網格草稿參數引用不合法。");
    } else {
      const boundary = ref?.kind === "boundary";
      if (!keys(ref, ["kind", "id", "fingerprint"], [...(boundary ? ["vertexKeysFingerprint"] : []), ...lostKeys]) ||
          !["grid-system", "grid-binding", "boundary"].includes(ref.kind) || !uint(ref.id) ||
          (boundary && (ref.id === 0 || !hash(ref.vertexKeysFingerprint))) || !hash(ref.fingerprint))
        fail("網格草稿的已發布引用不合法。");
    }
    return ref;
  }
  function referenceKey(ref) {
    return ref.kind === "parameter-field" ? `${ref.kind}:${ref.parameterId}:${ref.fieldId}` : `${ref.kind}:${ref.id}`;
  }
  const gridLostReserve=draft=>draft.inputRefs.reduce((bytes,ref)=>bytes+(ref.lost?0:12),0);
  // Stored values receive only the measured growth of validated lifecycle
  // annotations. This projection is a byte oracle, never saved editor data.
  function gridUnmarkedValue(value) {
    const unmark = draft => ({...draft,inputRefs:draft.inputRefs.map(ref=>{
      const next={...ref};delete next.lost;return next;
    })});
    if(value.schema!==GRID_DRAFTS_SCHEMA)return unmark(value);
    const drafts=value.drafts.map(unmark);
    if(drafts.length===1&&(value.orphans.length||value.drafts[0].inputRefs.some(ref=>ref.lost)))return drafts[0];
    return {...value,drafts,orphans:[]};
  }
  function gridUnmarkedEnvelope(envelope) {
    return {...envelope,records:envelope.records.map(record=>{
      if(record.kind!==GRID_KIND)return record;
      const value=gridUnmarkedValue(record.value);return {...record,schema:value.schema,value};
    })};
  }
  function gridCollectionReserve(value){
    const missing=value.drafts.filter(draft=>draft.baseRef&&!value.orphans.includes(draft.draftId));
    return value.drafts.reduce((bytes,draft)=>bytes+gridLostReserve(draft),0)+missing.reduce((bytes,draft)=>bytes+draft.draftId.length+2,0)+
      (value.orphans.length?missing.length:Math.max(0,missing.length-1));
  }
  function gridLifecycleValue(value){
    if(value===null)return null;
    const next=gridDrafts(value);
    for(const draft of next.drafts){if(draft.baseRef&&!next.orphans.includes(draft.draftId))next.orphans.push(draft.draftId);for(const ref of draft.inputRefs)ref.lost=true;}
    if(value.schema===GRID_DRAFTS_SCHEMA)return validateGridDrafts({schema:GRID_DRAFTS_SCHEMA,drafts:next.drafts,orphans:next.orphans},true);
    return gridDraftValue(next.drafts,next.orphans,true);
  }
  function gridRecordReserve(record){
    const value=gridLifecycleValue(record.value),projected={kind:GRID_KIND,schema:value.schema,value};
    return jsonBytes(projected,MAX_ROOM_BYTES)-jsonBytes(record,MAX_ROOM_BYTES);
  }
  function validateGridDraft(value, allowLost = false, stored = false) {
    boundedJSON(value,false,stored?20*12:0);
    const rules = value?.schema === GRID_RULE_SCHEMA;
    if (!keys(value, ["schema", "draftId", "kind", "intent", "baseRef", "inputRefs", "rawForm", ...(rules ? ["ruleDraft"] : [])]) ||
        ![GRID_SCHEMA, GRID_RULE_SCHEMA].includes(value.schema) || typeof value.draftId !== "string" || !/^[\w-]{1,100}$/.test(value.draftId) ||
        !["source", "binding"].includes(value.kind) || !["create", "edit"].includes(value.intent)) fail("網格編輯草稿版本或身分不合法。");
    if (value.intent === "create" && value.baseRef !== null || value.intent === "edit" &&
        (value.baseRef === null || validateReference(value.baseRef).kind !== (value.kind === "source" ? "grid-system" : "grid-binding")))
      fail("網格草稿的建立／編輯意圖不合法。");
    if (!Array.isArray(value.inputRefs) || value.inputRefs.length > 20) fail("網格草稿來源清單不合法。");
    const seen = new Set();
    for (const ref of value.inputRefs) {
      validateReference(ref, allowLost);
      const key = referenceKey(ref);
      if (seen.has(key)) fail("網格草稿來源引用重複。");
      seen.add(key);
    }
    const fields = value.kind === "source" ? sourceFields : bindingFields;
    if (!keys(value.rawForm, fields) || fields.some(field => typeof value.rawForm[field] !== "string" || value.rawForm[field].length > MAX_STRING))
      fail("網格草稿原始輸入欄位不完整或不合法。");
    if (rules && value.ruleDraft !== null) {
      const rule = value.ruleDraft;
      if (value.kind !== "source" || value.intent !== "edit" ||
          !keys(rule, ["intent", "ruleKey", "rawForm"]) || !["create", "edit", "delete"].includes(rule.intent) ||
          (rule.intent === "create" ? rule.ruleKey !== null : !uint(rule.ruleKey) || rule.ruleKey === 0) ||
          !keys(rule.rawForm, ruleFields) || ruleFields.some(field => typeof rule.rawForm[field] !== "string" || rule.rawForm[field].length > MAX_STRING))
        fail("來源規則草稿的意圖、身分或原始欄位不合法。");
    }
    // Empty, incorrect, inactive and whitespace-bearing fields are intentional.
    // The native preview validator alone decides whether they may be published.
    jsonBytes(stored?gridUnmarkedValue(value):value,MAX_BYTES,stored?0:gridLostReserve(value),"網格草稿未保留自動缺失補標容量。");
    return value;
  }
  function validateGridDrafts(value, stored = false) {
    jsonBytes(value, MAX_GRID_DRAFTS_BYTES+(stored?MAX_GRID_DRAFTS*(20*12+103):0));
    if (!keys(value,["schema","drafts","orphans"]) || value.schema !== GRID_DRAFTS_SCHEMA ||
        !Array.isArray(value.drafts) || value.drafts.length < 1 || value.drafts.length > MAX_GRID_DRAFTS ||
        !Array.isArray(value.orphans) || value.orphans.length > value.drafts.length || new Set(value.orphans).size !== value.orphans.length)
      fail("網格草稿集合版本、份數或孤兒清單不合法。");
    const ids = new Set(), targets = new Set();
    for (const draft of value.drafts) {
      validateGridDraft(draft,true,stored);
      if (ids.has(draft.draftId)) fail("網格草稿身分重複。");
      ids.add(draft.draftId);
      if (draft.intent === "edit" && !value.orphans.includes(draft.draftId)) {
        const target = referenceKey(draft.baseRef);
        if (targets.has(target)) fail("同目標已有非孤兒網格草稿。");
        targets.add(target);
      }
    }
    if (value.orphans.some(id=>!value.drafts.some(d=>d.draftId===id && d.intent==="edit"))) fail("孤兒必須指向集合內的編輯草稿。");
    jsonBytes(stored?gridUnmarkedValue(value):value,MAX_GRID_DRAFTS_BYTES,stored?0:gridCollectionReserve(value),"草稿集合未保留自動缺失補標容量。");
    return value;
  }
  function gridDrafts(value) {
    if (value === null) return {drafts:[],orphans:[]};
    if (value.schema === GRID_DRAFTS_SCHEMA) {validateGridDrafts(value,true);return JSON.parse(JSON.stringify({drafts:value.drafts,orphans:value.orphans}));}
    validateGridDraft(value,false,true);return {drafts:[JSON.parse(JSON.stringify(value))],orphans:[]};
  }
  function gridDraftValue(drafts, orphans = [], stored = false) {
    if (!drafts.length) return null;
    if (drafts.length === 1 && !orphans.length && !drafts[0].inputRefs.some(ref=>ref.lost)) return validateGridDraft(drafts[0],false,stored);
    return validateGridDrafts({schema:GRID_DRAFTS_SCHEMA,drafts:[...drafts].sort((a,b)=>a.draftId<b.draftId?-1:a.draftId>b.draftId?1:0),orphans:[...orphans].sort()},stored);
  }
  function validateRecord(record, stored = false) {
    const bytes = boundedJSON(record, true,stored?MAX_GRID_DRAFTS*(20*12+103):0);
    if (!keys(record, ["kind", "schema", "value"]))
      fail("功能附件種類或版本不支援。");
    if (record.kind === GRID_KIND && record.schema === GRID_DRAFTS_SCHEMA) {
      validateGridDrafts(record.value,stored);
      const original=stored?gridUnmarkedEnvelope({records:[record]}).records[0]:record;
      jsonBytes(original,MAX_GRID_DRAFTS_BYTES,stored?0:gridCollectionReserve(record.value),"集合附件未保留自動缺失補標容量。");
      if(stored&&original.schema!==GRID_DRAFTS_SCHEMA)boundedJSON(original);
    } else if (record.kind === GRID_KIND && [GRID_SCHEMA, GRID_RULE_SCHEMA].includes(record.schema)) {
      if (record.value?.schema !== record.schema) fail("網格草稿附件版本不一致。");
      boundedJSON(record); validateGridDraft(record.value,false,stored);
    } else if (record.kind === ROOM_KIND && [ROOM_SCHEMA,ROOM_HISTORY_SCHEMA,ROOM_DISPLAY_SCHEMA].includes(record.schema)) {
      if (!Rooms || Rooms.SCHEMA !== ROOM_SCHEMA || Rooms.CAPABILITY !== ROOM_CAPABILITY || Rooms.HISTORY_SCHEMA !== ROOM_HISTORY_SCHEMA || Rooms.HISTORY_CAPABILITY !== ROOM_HISTORY_CAPABILITY || Rooms.DISPLAY_SCHEMA !== ROOM_DISPLAY_SCHEMA || Rooms.DISPLAY_CAPABILITY !== ROOM_DISPLAY_CAPABILITY) fail("房間來源驗證器尚未就緒。");
      if (record.value?.schema !== record.schema) fail("房間來源附件版本不一致。");
      Rooms.validate(record.value);
      if (bytes + lifecycleReserve(record.value) > MAX_ROOM_BYTES) fail("功能附件未保留房間狀態更新所需容量。");
    } else if (record.kind === CASE_KIND && record.schema === CASE_SCHEMA) {
      Cases.validate(record.value);
    } else if (record.kind === Evidence.KIND && record.schema === Evidence.SCHEMA) {
      Evidence.validate(record.value);
    } else fail("功能附件種類或版本不支援。");
    return record;
  }
  function validate(envelope, stored = false) {
    const bytes = boundedJSON(envelope, true,stored?MAX_GRID_DRAFTS*(20*12+103)+256:0);
    if (!keys(envelope, ["schema", "records"]) || envelope.schema !== SCHEMA || !Array.isArray(envelope.records) || envelope.records.length > 4)
      fail("功能附件版本或清單不支援。");
    const kinds = new Set();
    for (const record of envelope.records) {
      validateRecord(record,stored);
      if (record.kind === GRID_KIND && record.schema !== GRID_DRAFTS_SCHEMA) boundedJSON({schema:SCHEMA, records:[record]});
      if (kinds.has(record.kind)) fail("功能附件種類重複。");
      kinds.add(record.kind);
    }
    if(stored)for(const record of gridUnmarkedEnvelope(envelope).records)if(record.kind===GRID_KIND&&record.schema!==GRID_DRAFTS_SCHEMA)boundedJSON({schema:SCHEMA,records:[record]});
    if ((stored?jsonBytes(gridUnmarkedEnvelope(envelope),MAX_ROOM_BYTES):bytes) + envelope.records.reduce((size,record) => size + (record.kind === ROOM_KIND ? lifecycleReserve(record.value) : record.kind===GRID_KIND&&!stored?gridRecordReserve(record):0),0) > MAX_ROOM_BYTES)
      fail("功能附件未保留房間狀態更新所需容量。");
    return envelope;
  }
  function assertKind(kind) { if (![GRID_KIND, ROOM_KIND, Evidence.KIND, CASE_KIND].includes(kind)) fail("功能附件種類不支援。"); }
  function record(kind, value, stored = false) {
    assertKind(kind);
    const schema = value !== null && typeof value === "object" ? Object.getOwnPropertyDescriptor(value,"schema")?.value : undefined;
    return validateRecord({kind, schema, value},stored);
  }
  function capabilities(envelope) { validate(envelope,true); return [...new Set(envelope.records.flatMap(record => record.kind === GRID_KIND ?
    (record.schema === GRID_DRAFTS_SCHEMA ? [GRID_DRAFTS_SCHEMA,...record.value.drafts.map(d=>d.schema)] : [record.schema]) :
    record.kind === Evidence.KIND ? [Evidence.SCHEMA] : record.kind === CASE_KIND ? [CASE_SCHEMA] :
    [ROOM_CAPABILITY,...(record.schema===ROOM_DISPLAY_SCHEMA?[ROOM_DISPLAY_CAPABILITY]:[]),
      ...((record.schema===ROOM_HISTORY_SCHEMA||record.value.legacyHistory?.length)?[ROOM_HISTORY_CAPABILITY]:[])]))].sort(); }
  function evidenceLinks(envelope, sources, projectScope) {
    validate(envelope,true);
    const value = envelope.records.find(record => record.kind === Evidence.KIND)?.value || null;
    for (const link of value?.links || []) {
      if (projectScope !== undefined && link.target.projectScope !== projectScope) fail("證據欄位屬於另一專案。");
      if (sources) {
        const entry = sources.get(link.document.sourceHash), meta = entry?.meta || entry;
        if (!meta || meta.id !== link.document.sourceHash || meta.hash !== meta.id || meta.type !== "application/pdf")
          fail("證據原 PDF 缺失或來源類型不符。");
      }
    }
    return value;
  }
  function sourceRooms(envelope, sources) {
    validate(envelope,true);
    const value = envelope.records.find(record => record.kind === ROOM_KIND)?.value || null;
    if (value) Rooms.validate(value, sources);
    return value;
  }
  function validateNativeRefs(envelope, objects) {
    const value = sourceRooms(envelope); if (value) Rooms.validateNativeRefs(value, objects);
  }
  function sourceIds(envelope) {
    const rooms = sourceRooms(envelope), evidence = evidenceLinks(envelope);
    return [...new Set([...(rooms?.planes || []).map(plane=>plane.sourceId),
      ...(evidence ? Evidence.references(evidence).sources : [])])];
  }
  function validateNativePins(envelope, definitions) {
    const value = sourceRooms(envelope); if (value) Rooms.validateNativePins(value, definitions);
  }
  function retireRoomBoundary(value, id) { return Rooms.retireBoundary(validateRecord(record(ROOM_KIND, value)).value, id); }
  function changedRoomBoundary(value, id) { return Rooms.boundaryChanged(validateRecord(record(ROOM_KIND, value)).value, id); }
  function unknownRoomHistory(value) { return Rooms.unknownHistory(validateRecord(record(ROOM_KIND, value)).value); }
  function references(value) { validateGridDraft(value); return JSON.parse(JSON.stringify([...(value.baseRef === null ? [] : [value.baseRef]), ...value.inputRefs])); }
  return {ReferenceDisplay:Rooms.Display,Evidence,Cases,CASE_KIND,CASE_SCHEMA, evidenceLinks, sourceIds, SCHEMA, GRID_SCHEMA, GRID_RULE_SCHEMA, GRID_KIND, ROOM_KIND, ROOM_SCHEMA, ROOM_CAPABILITY, ROOM_HISTORY_SCHEMA, ROOM_HISTORY_CAPABILITY, ROOM_DISPLAY_SCHEMA, ROOM_DISPLAY_CAPABILITY, MAX_BYTES, MAX_ROOM_BYTES,
    validateSourceRecords:Rooms.validateSourceRecords, validateReconstructionReviews:Rooms.validateReconstructionReviews,
    sourceFields:Object.freeze(sourceFields), bindingFields:Object.freeze(bindingFields), ruleFields:Object.freeze(ruleFields),
    gridSourceDefinition, gridSourceKey, ruleAwareSource,
    GRID_DRAFTS_SCHEMA, MAX_GRID_DRAFTS, MAX_GRID_DRAFTS_BYTES, validateGridDrafts, gridDrafts, gridDraftValue, gridLifecycleValue, gridUnmarkedEnvelope, referenceKey,
    validate, validateRecord, validateGridDraft, assertKind, record, capabilities, references, sourceRooms, validateNativeRefs, validateNativePins, jsonBytes, lifecycleReserve,
    retireRoomBoundary, changedRoomBoundary, unknownRoomHistory};
});
