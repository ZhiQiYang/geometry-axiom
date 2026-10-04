/* #77: one drawing basis per source plane. No native geometry is stored here. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.GeometrySourcePlane = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const MAX_PLANES = 256, MAX_ROOMS = 10000;
  const SCHEMA = "source-rooms/1", CAPABILITY = "source-room-collection/1";
  const copy = value => structuredClone(value);
  const fail = message => { throw new Error(message); };
  const object = value => !!value && typeof value === "object" && !Array.isArray(value);
  const keys = (value, names) => object(value) && Object.keys(value).length === names.length && names.every(k => Object.hasOwn(value, k));
  const id = value => typeof value === "string" && /^[\w-]{1,100}$/.test(value);
  const hash = value => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
  const finite = (value, lo, hi) => typeof value === "number" && Number.isFinite(value) && value >= lo && value <= hi;
  const uint = value => Number.isInteger(value) && value >= 0 && value <= 4294967295;
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
    if (!keys(state, ["schema", "planes", "collections", "rooms"]) || state.schema !== SCHEMA ||
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
    return state;
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
  return {SCHEMA, CAPABILITY, MAX_PLANES, MAX_ROOMS, empty, validatePlane, validate, validateNativeRefs, validateNativePins, references, fromPage, materialize, changeBasis, planeForRoom, retireBoundary, boundaryChanged, unknownHistory, sourceIds};
});
