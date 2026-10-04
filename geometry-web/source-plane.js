/* #77: one current drawing basis per source plane; approved original receipts
 * remain historical evidence, never editable geometry or current acceptance. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.GeometrySourcePlane = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const MAX_PLANES = 256, MAX_ROOMS = 10000;
  const SCHEMA = "source-rooms/1", CAPABILITY = "source-room-collection/1";
  const HISTORY_SCHEMA = "source-rooms/2", HISTORY_CAPABILITY = "source-room-history/1", MAX_HISTORY = 10000;
  const copy = value => structuredClone(value);
  const fail = message => { throw new Error(message); };
  const object = value => !!value && typeof value === "object" && !Array.isArray(value);
  const keys = (value, names) => object(value) && Object.keys(value).length === names.length && names.every(k => Object.hasOwn(value, k));
  const id = value => typeof value === "string" && /^[\w-]{1,100}$/.test(value);
  const hash = value => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
  const finite = (value, lo, hi) => typeof value === "number" && Number.isFinite(value) && value >= lo && value <= hi;
  const uint = value => Number.isInteger(value) && value >= 0 && value <= 4294967295;
  const positiveId = value => uint(value) && value > 0;
  const str = (value, max = 1000) => typeof value === "string" && value.length <= max;
  const pt = value => Array.isArray(value) && value.length === 2 && value.every(v => finite(v, 0, 1e7));
  const empty = () => ({schema: SCHEMA, planes: [], collections: [], rooms: []});
  function validatePlane(p) {
    if (!keys(p, ["id", "sourceId", "page", "coordinateSpace", "pageSize", "calibration", "alignment", "basisRevision"]) ||
        !id(p.id) || !hash(p.sourceId) || !Number.isInteger(p.page) || p.page < 1 || p.page > 100000 ||
        !["pdf-page-viewport/1", "image-pixel/1"].includes(p.coordinateSpace) ||
        !Array.isArray(p.pageSize) || p.pageSize.length !== 2 || !p.pageSize.every(v => finite(v, 1, 1e7)) ||
        !Number.isSafeInteger(p.basisRevision) || p.basisRevision < 1) fail("共享來源平面資料不合法。");
    if (p.coordinateSpace === "image-pixel/1" && p.page !== 1) fail("圖片來源只能使用第一頁。");
    const a = p.alignment;
    if (!keys(a, ["x", "y", "mmPerPx", "rotation"]) || !finite(a.x, -1e8, 1e8) || !finite(a.y, -1e8, 1e8) ||
        !finite(a.mmPerPx, 1e-9, 1e8) || ![0, 90, 180, 270].includes(a.rotation)) fail("共享來源對位不合法。");
    const c = p.calibration;
    if (c !== null) {
      if (!keys(c, ["points", "distanceMm", "inputValue", "inputUnit"]) || !Array.isArray(c.points) || c.points.length !== 2 ||
          !c.points.every(pt => Array.isArray(pt) && pt.length === 2 && pt.every((v, i) => finite(v, 0, p.pageSize[i]))) ||
          !Number.isSafeInteger(c.distanceMm) || !finite(c.distanceMm, 1, 1e8) || !finite(c.inputValue, 1e-9, 1e8) ||
          !["mm", "cm"].includes(c.inputUnit)) fail("共享來源校準不合法。");
      const distance = Math.hypot(c.points[1][0] - c.points[0][0], c.points[1][1] - c.points[0][1]);
      if (!(distance > 0) || Math.abs(c.distanceMm / distance - a.mmPerPx) > 1e-8 * a.mmPerPx ||
          Math.abs(c.inputValue * (c.inputUnit === "cm" ? 10 : 1) - c.distanceMm) > 1e-7) fail("共享來源校準與比例不一致。");
    }
    return p;
  }
  function validate(state, sources) {
    const history = state?.schema === HISTORY_SCHEMA;
    if (!keys(state, ["schema", "planes", "collections", "rooms", ...(history ? ["legacyHistory"] : [])]) || ![SCHEMA,HISTORY_SCHEMA].includes(state.schema) ||
        !Array.isArray(state.planes) || state.planes.length > MAX_PLANES || !Array.isArray(state.collections) ||
        state.collections.length > MAX_PLANES || !Array.isArray(state.rooms) || state.rooms.length > MAX_ROOMS) fail("房間來源附件版本或容量不支援。");
    const planes = new Map(), sourcePages = new Set(), collections = new Set(), rooms = new Set(), refs = new Set(), memberships = new Set();
    for (const plane of state.planes) {
      validatePlane(plane);
      if (planes.has(plane.id)) fail("共享來源平面識別重複。");
      const sourcePage = plane.sourceId + ":" + plane.page;
      if (sourcePages.has(sourcePage)) fail("同一來源頁只能有一份共享校準與對位。");
      sourcePages.add(sourcePage);
      if (sources) {
        const source = sources instanceof Map ? sources.get(plane.sourceId) : sources.find(s => s.id === plane.sourceId);
        const meta = source?.meta || source;
        if (!meta || meta.hash !== plane.sourceId || (meta.type === "application/pdf") !== (plane.coordinateSpace === "pdf-page-viewport/1")) fail("共享來源檔案遺失或座標型別不一致。");
      }
      planes.set(plane.id, plane);
    }
    for (const collection of state.collections) {
      if (!keys(collection, ["id", "planeId", "roomIds"]) || !id(collection.id) || collections.has(collection.id) || !planes.has(collection.planeId) ||
          !Array.isArray(collection.roomIds) || collection.roomIds.length > MAX_ROOMS || !collection.roomIds.every(id)) fail("房間集合資料不合法。");
      collections.add(collection.id);
      for (const rid of collection.roomIds) {
        if (memberships.has(rid)) fail("房間不可重複隸屬來源集合。");
        memberships.add(rid);
      }
    }
    for (const room of state.rooms) {
      const ref = room.boundaryRef;
      if (!keys(room, ["id", "name", "boundaryRef", "acceptedBasisRevision", "reviewState"]) || !id(room.id) || rooms.has(room.id) ||
          typeof room.name !== "string" || !room.name.trim() || room.name.length > 200 ||
          !keys(ref, ["kind", "id", "associationPin"]) || ref.kind !== "boundary" || !uint(ref.id) || ref.id === 0 || !hash(ref.associationPin) ||
          !Number.isSafeInteger(room.acceptedBasisRevision) || room.acceptedBasisRevision < 1 ||
          !["confirmed", "needs-review", "needs-reassociation"].includes(room.reviewState) || !memberships.has(room.id) || refs.has(ref.id)) fail("房間名稱或原生邊界關聯不合法。");
      const collection = state.collections.find(c => c.roomIds.includes(room.id)), plane = planes.get(collection.planeId);
      if (room.acceptedBasisRevision > plane.basisRevision || (room.reviewState === "confirmed" && room.acceptedBasisRevision !== plane.basisRevision)) fail("房間核對基準不一致。");
      rooms.add(room.id); refs.add(ref.id);
    }
    if ([...memberships].some(rid => !rooms.has(rid))) fail("房間集合引用不存在的房間。");
    if (history) validateLegacyHistory(state.legacyHistory, planes);
    return state;
  }
  function validateSourceRecords(records) {
    if (!Array.isArray(records) || records.length > 1000) fail("來源紀錄不合法。");
    const recordIds = new Set();
    for (const r of records) {
      if (!object(r) || !id(r.id) || recordIds.has(r.id) || !str(r.label, 300) || !str(r.location, 1000) || !str(r.datum, 300) ||
          !["mm", "cm"].includes(r.unit) || !(r.value === null || finite(r.value, -1e8, 1e8))) fail("來源紀錄欄位不合法。");
      recordIds.add(r.id);
    }
    return records;
  }
  function validateLegacyHistory(records, planes) {
    if (!Array.isArray(records) || !records.length || records.length > MAX_HISTORY) fail("來源歷史紀錄版本或容量不支援。");
    const seen = new Set();
    for (const entry of records) {
      if (!keys(entry,["planeId","boundaryId","pageId","records","reconstructionReview"]) || !id(entry.planeId) ||
          !positiveId(entry.boundaryId) || !id(entry.pageId) || !planes.has(entry.planeId)) fail("來源歷史紀錄引用不合法。");
      const key = JSON.stringify([entry.planeId,entry.boundaryId,entry.pageId]);
      if (seen.has(key)) fail("來源歷史紀錄引用重複。");
      seen.add(key); validateSourceRecords(entry.records);
      if (entry.reconstructionReview !== null) {
        if (!keys(entry.reconstructionReview,["basis","geometry","method","warnings","confirmedAt"])) fail("來源歷史核對收據欄位不合法。");
        const plane = planes.get(entry.planeId);
        validateReconstructionReviews([{bid:entry.boundaryId,pageId:entry.pageId,...entry.reconstructionReview}],
          [{bid:entry.boundaryId,pages:[{id:entry.pageId,sourceId:plane.sourceId,page:plane.page}]}]);
        const basis = JSON.parse(entry.reconstructionReview.basis);
        if (basis[3] !== plane.pageSize[0] || basis[4] !== plane.pageSize[1]) fail("來源歷史核對收據的原頁尺寸不一致。");
      }
      if (!entry.records.length && entry.reconstructionReview === null) fail("來源歷史紀錄不可為空。");
    }
  }
  function validateReconstructionReviews(records, faces) {
    if (!Array.isArray(records) || records.length > 10000) fail("輪廓核對收據清單不合法。");
    const seen=new Set();
    for (const r of records) {
      if (!keys(r,["bid","pageId","basis","geometry","method","warnings","confirmedAt"]) || !positiveId(r.bid) || !id(r.pageId) ||
          !str(r.basis,4000) || !str(r.geometry,100000) || !["manual","pdf-vector","image-lines"].includes(r.method) ||
          !Array.isArray(r.warnings) || r.warnings.length>100 || !r.warnings.every(w=>str(w,1000)) || !str(r.confirmedAt,40) || !Number.isFinite(Date.parse(r.confirmedAt))) fail("輪廓核對收據欄位不合法。");
      const key=r.bid+":"+r.pageId, p=faces?.find(f=>f.bid===r.bid)?.pages.find(p=>p.id===r.pageId);
      if (!p || seen.has(key)) fail("輪廓核對收據引用不存在或重複的來源頁。");
      seen.add(key);
      let basis,loops;try {basis=JSON.parse(r.basis);loops=JSON.parse(r.geometry);}catch {fail("輪廓核對指紋不合法。");}
      if (!Array.isArray(basis) || basis.length!==11 || basis[0]!==p.sourceId || basis[1]!==p.id || basis[2]!==p.page ||
          !finite(basis[3],1,1e7) || !finite(basis[4],1,1e7) || !finite(basis[6],1e-9,1e8) || !finite(basis[7],-1e8,1e8) || !finite(basis[8],-1e8,1e8) || ![0,90,180,270].includes(basis[9])) fail("輪廓核對收據的來源／幾何不合法。");
      const crop=basis[5],q=basis[10];
      if (!Array.isArray(crop) || crop.length!==4 || !crop.every(Number.isFinite) || crop[0]<0 || crop[1]<0 || crop[2]<=0 || crop[3]<=0 || crop[0]+crop[2]>basis[3]+.001 || crop[1]+crop[3]>basis[4]+.001 ||
          !keys(q,["points","distanceMm","inputValue","inputUnit"]) || !Array.isArray(q.points) || q.points.length!==2 || !q.points.every(pt) || q.points.some(v=>v[0]>basis[3]||v[1]>basis[4]) ||
          !Number.isSafeInteger(q.distanceMm) || !finite(q.distanceMm,1,1e8) || !finite(q.inputValue,1e-9,1e8) || !["mm","cm"].includes(q.inputUnit)) fail("輪廓核對收據的校準不合法。");
      const distance=Math.hypot(q.points[0][0]-q.points[1][0],q.points[0][1]-q.points[1][1]);
      if (!(distance>0) || Math.abs(q.distanceMm/distance-basis[6])>1e-8*basis[6] || Math.abs(q.inputValue*(q.inputUnit==="cm"?10:1)-q.distanceMm)>1e-7) fail("輪廓核對收據的校準與比例不一致。");
      if (!Array.isArray(loops) || !loops.length || loops.length>256 || loops.some(l=>!Array.isArray(l)||l.length!==2 || !Array.isArray(l[0]) || l[0].length<4 || l[0].length>1024 ||
            !Array.isArray(l[1]) || l[0].length!==l[1].length || !l[1].every(v=>v===0||v===1) || l[0].some(p=>!Array.isArray(p)||p.length!==2||!p.every(v=>Number.isSafeInteger(v)&&Math.abs(v)<=1e8)))) fail("輪廓核對收據的幾何不合法。");
      if (loops.some(l=>l[0].some((p,i)=>((p[0]===l[0][(i+1)%l[0].length][0])===(p[1]===l[0][(i+1)%l[0].length][1]))))) fail("輪廓核對收據的幾何必須正交。");
      if (JSON.stringify(basis)!==r.basis || JSON.stringify(loops)!==r.geometry) fail("輪廓核對指紋必須使用標準編碼。");
    }
  }
  function validateNativeRefs(state, objects) {
    validate(state);
    if (!objects || !Array.isArray(objects.boundaries) || !objects.boundaries.every(v => uint(v) && v > 0)) fail("無法核對原生房間邊界。");
    const live = new Set(objects.boundaries);
    for (const room of state.rooms) if (room.reviewState !== "needs-reassociation" && !live.has(room.boundaryRef.id)) fail("房間邊界不存在於原生候選場景。");
  }
  function validateNativePins(state, definitions) {
    validate(state);
    if (!(definitions instanceof Map)) fail("原生房間指紋讀取失敗。");
    for (const room of state.rooms) {
      if (room.reviewState === "needs-reassociation") continue;
      const native = definitions.get(room.boundaryRef.id);
      if (!native || native.id !== room.boundaryRef.id || !hash(native.geometryFingerprint)) fail("原生房間指紋讀取失敗。");
      if (room.reviewState === "confirmed" && native.geometryFingerprint !== room.boundaryRef.associationPin) fail("已核對房間的原生邊界指紋不一致。");
    }
  }
  function planeForRoom(state, roomId) {
    const collection = state.collections.find(c => c.roomIds.includes(roomId));
    return collection && state.planes.find(p => p.id === collection.planeId);
  }
  function fromPage(page, sourceType, planeId) {
    const p = {id: planeId, sourceId: page.sourceId, page: page.page,
      coordinateSpace: sourceType === "application/pdf" ? "pdf-page-viewport/1" : "image-pixel/1", pageSize: [page.imgW, page.imgH],
      calibration: copy(page.calibration), alignment: {x: page.x, y: page.y, mmPerPx: page.mmPerPx, rotation: page.rot}, basisRevision: 1};
    return copy(validatePlane(p));
  }
  // Derived renderer data is disposable, and is never serialized as a second basis.
  function materialize(plane, view = {}) {
    validatePlane(plane);
    return {id: "plane-" + plane.id, sourceId: plane.sourceId, page: plane.page, imgW: plane.pageSize[0], imgH: plane.pageSize[1],
      crop: [0, 0, ...plane.pageSize], x: plane.alignment.x, y: plane.alignment.y, mmPerPx: plane.alignment.mmPerPx,
      rot: plane.alignment.rotation, calibration: copy(plane.calibration), reviewRequired: false, records: [], opacity: .5, locked: false,
      ...(view.src ? {src: view.src} : {})};
  }
  function changeBasis(state, planeId, calibration, alignment) {
    validate(state);
    const next = copy(state), plane = next.planes.find(p => p.id === planeId);
    if (!plane) fail("共享來源平面不存在。");
    if (JSON.stringify([plane.calibration, plane.alignment]) === JSON.stringify([calibration, alignment])) return next;
    plane.calibration = copy(calibration); plane.alignment = copy(alignment); plane.basisRevision++;
    validatePlane(plane);
    for (const room of next.rooms) if (planeForRoom(next, room.id)?.id === planeId && room.reviewState !== "needs-reassociation") room.reviewState = "needs-review";
    return validate(next);
  }
  function retireBoundary(state, boundaryId) {
    const next = copy(validate(state));
    for (const room of next.rooms) if (room.boundaryRef.id === boundaryId) room.reviewState = "needs-reassociation";
    return next;
  }
  function boundaryChanged(state, boundaryId) {
    const next = copy(validate(state));
    for (const room of next.rooms) if (room.boundaryRef.id === boundaryId && room.reviewState !== "needs-reassociation") room.reviewState = "needs-review";
    return next;
  }
  function unknownHistory(state) {
    const next = copy(validate(state));
    for (const room of next.rooms) room.reviewState = "needs-reassociation";
    return next;
  }
  function sourceIds(state) {return [...new Set(validate(state).planes.map(p => p.sourceId))];}
  function references(state) {
    validate(state);
    return {sourceIds: sourceIds(state), boundaries: state.rooms.map(room => ({...copy(room.boundaryRef), reviewState: room.reviewState}))};
  }
  return {SCHEMA, CAPABILITY, HISTORY_SCHEMA, HISTORY_CAPABILITY, MAX_HISTORY, validateSourceRecords, validateReconstructionReviews, MAX_PLANES, MAX_ROOMS, empty, validatePlane, validate, validateNativeRefs, validateNativePins, references, fromPage, materialize, changeBasis, planeForRoom, retireBoundary, boundaryChanged, unknownHistory, sourceIds};
});
