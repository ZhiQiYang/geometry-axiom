/* D53 room-candidate-drafts/1. Project attachment, never a scene capability.
 * Unaccepted rows stay out of World until a preview/confirm transaction. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.GeometryRoomCandidateDraft = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const SCHEMA = "room-candidate-drafts/1";
  const CAPABILITY = "room-candidate-drafts/1";
  const KIND = "room-candidates";
  const ANALYZER_REVISION = "room-outline-batch/1";
  const MAX_ROWS = 12, MAX_RAW = 20000, MAX_BYTES = 1024 * 1024, MAX_BARRIERS = 64, MAX_DIMENSIONS = 256;
  const fail = message => { throw new Error(message); };
  const object = value => !!value && typeof value === "object" && !Array.isArray(value);
  const keys = (value, required, optional = []) => object(value) && required.every(key => Object.hasOwn(value, key)) &&
    Object.keys(value).every(key => required.includes(key) || optional.includes(key));
  const id = value => typeof value === "string" && /^[\w-]{1,100}$/.test(value);
  const hash = value => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
  const finite = (value, lo, hi) => typeof value === "number" && Number.isFinite(value) && value >= lo && value <= hi;
  const uint = value => Number.isSafeInteger(value) && value >= 0 && value <= 4294967295;
  const copy = value => { assertDefined(value); return JSON.parse(JSON.stringify(value)); };
  function assertDefined(value, path = "$") {
    if (value === undefined) fail("指紋不得省略欄位。");
    if (Array.isArray(value)) value.forEach((item, index) => assertDefined(item, path + "." + index));
    else if (object(value)) for (const key of Object.keys(value)) assertDefined(value[key], path + "." + key);
  }
  function sha256Hex(message) {
    const K = new Uint32Array([
      0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
      0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
      0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
      0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
      0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
      0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
      0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
      0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ]);
    const rotr = (x, n) => (x >>> n) | (x << (32 - n));
    const data = new TextEncoder().encode(message);
    const bitLen = data.length * 8;
    const padded = new Uint8Array(((data.length + 9 + 63) >> 6) << 6);
    padded.set(data); padded[data.length] = 0x80;
    const view = new DataView(padded.buffer);
    view.setUint32(padded.length - 8, Math.floor(bitLen / 0x100000000));
    view.setUint32(padded.length - 4, bitLen >>> 0);
    let h0 = 0x6a09e667, h1 = 0xbb67ae85, h2 = 0x3c6ef372, h3 = 0xa54ff53a, h4 = 0x510e527f, h5 = 0x9b05688c, h6 = 0x1f83d9ab, h7 = 0x5be0cd19;
    const w = new Uint32Array(64);
    for (let i = 0; i < padded.length; i += 64) {
      for (let t = 0; t < 16; t++) w[t] = view.getUint32(i + t * 4);
      for (let t = 16; t < 64; t++) {
        const s0 = rotr(w[t - 15], 7) ^ rotr(w[t - 15], 18) ^ (w[t - 15] >>> 3);
        const s1 = rotr(w[t - 2], 17) ^ rotr(w[t - 2], 19) ^ (w[t - 2] >>> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) >>> 0;
      }
      let a = h0, b = h1, c = h2, d = h3, e = h4, f = h5, g = h6, h = h7;
      for (let t = 0; t < 64; t++) {
        const s1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        const ch = (e & f) ^ (~e & g);
        const t1 = (h + s1 + ch + K[t] + w[t]) >>> 0;
        const s0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        const maj = (a & b) ^ (a & c) ^ (b & c);
        const t2 = (s0 + maj) >>> 0;
        h = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
      }
      h0 = (h0 + a) >>> 0; h1 = (h1 + b) >>> 0; h2 = (h2 + c) >>> 0; h3 = (h3 + d) >>> 0;
      h4 = (h4 + e) >>> 0; h5 = (h5 + f) >>> 0; h6 = (h6 + g) >>> 0; h7 = (h7 + h) >>> 0;
    }
    return [h0, h1, h2, h3, h4, h5, h6, h7].map(value => value.toString(16).padStart(8, "0")).join("");
  }
  function canonical(value) { assertDefined(value); return JSON.stringify(value); }
  function pin(value) { return sha256Hex(canonical(value)); }
  function pageFields(page) {
    return {id: page.id, sourceId: page.sourceId, page: page.page, imgW: page.imgW, imgH: page.imgH,
      mmPerPx: page.mmPerPx, x: page.x, y: page.y, rot: page.rot, calibration: page.calibration ?? null};
  }
  function pagePin(page) {
    const fields = pageFields(page);
    return pin([fields.id, fields.sourceId, fields.page, fields.imgW, fields.imgH, fields.mmPerPx, fields.x, fields.y, fields.rot,
      fields.calibration === null ? null : [fields.calibration.points, fields.calibration.distanceMm, fields.calibration.inputValue, fields.calibration.inputUnit]]);
  }
  function planePin(plane) {
    const calibration = plane.calibration === null ? null : [plane.calibration.points, plane.calibration.distanceMm, plane.calibration.inputValue, plane.calibration.inputUnit];
    return pin([plane.id, plane.sourceId, plane.page, plane.coordinateSpace, plane.pageSize, calibration,
      [plane.alignment.x, plane.alignment.y, plane.alignment.mmPerPx, plane.alignment.rotation], plane.basisRevision]);
  }
  function roomsPin(rooms) {
    return pin(rooms.map(room => [room.id, room.boundaryRef.id, room.boundaryRef.geometryFingerprint ?? room.nativePin ?? null, room.acceptedBasisRevision, room.reviewState]));
  }
  function orthogonal(points) {
    return points.every((point, index) => {
      const next = points[(index + 1) % points.length];
      return (point[0] === next[0]) !== (point[1] === next[1]);
    });
  }
  function ring(points, name) {
    if (!Array.isArray(points) || points.length < 4 || points.length > 256 || !points.every(point => Array.isArray(point) && point.length === 2 &&
        point.every(value => Number.isSafeInteger(value) && Math.abs(value) <= 1e8)) || !orthogonal(points)) fail(name + "必須是 4–256 個正交整數毫米頂點。");
    return points;
  }
  function validate(draft) {
    if (!keys(draft, ["schema", "draftId", "anchor", "analysis", "rows"]) || draft.schema !== SCHEMA || !id(draft.draftId) ||
        !Array.isArray(draft.rows) || draft.rows.length > MAX_ROWS) fail("房間候選草稿版本或列數不支援。");
    const anchor = draft.anchor;
    if (anchor?.kind === "collection") {
      if (!keys(anchor, ["kind", "collectionId", "planeId", "planePin", "roomsPin"]) || !id(anchor.collectionId) || !id(anchor.planeId) ||
          !hash(anchor.planePin) || !hash(anchor.roomsPin)) fail("房間候選的集合錨點不合法。");
    } else if (anchor?.kind === "page") {
      if (!keys(anchor, ["kind", "boundaryId", "pageId", "pagePin"]) || !uint(anchor.boundaryId) || anchor.boundaryId < 1 ||
          !id(anchor.pageId) || !hash(anchor.pagePin)) fail("房間候選的圖頁錨點不合法。");
    } else fail("房間候選必須有集合或圖頁錨點。");
    const analysis = draft.analysis;
    if (!keys(analysis, ["sourceId", "page", "coordinateSpace", "pageSize", "crop", "options", "barriers", "analyzerRevision", "total", "complete", "ignoredNested"]) ||
        !hash(analysis.sourceId) || !Number.isInteger(analysis.page) || analysis.page < 1 ||
        !["pdf-page-viewport/1", "image-pixel/1"].includes(analysis.coordinateSpace) ||
        !Array.isArray(analysis.pageSize) || analysis.pageSize.length !== 2 || !analysis.pageSize.every(value => finite(value, 1, 1e7)) ||
        !Array.isArray(analysis.crop) || analysis.crop.length !== 4 || !analysis.crop.every((value, index) => finite(value, 0, index < 2 ? analysis.pageSize[index] : 1e7)) ||
        !keys(analysis.options, ["mode", "minWidth", "minLength"]) || !["auto", "vector", "image"].includes(analysis.options.mode) ||
        !finite(analysis.options.minWidth, 1e-9, 1e7) || !finite(analysis.options.minLength, 1e-9, 1e7) ||
        !Array.isArray(analysis.barriers) || analysis.barriers.length > MAX_BARRIERS ||
        !analysis.barriers.every(barrier => Array.isArray(barrier) && barrier.length === 4 && barrier.every(value => Number.isFinite(value))) ||
        typeof analysis.analyzerRevision !== "string" || !analysis.analyzerRevision || analysis.analyzerRevision.length > 100 ||
        !Number.isInteger(analysis.total) || analysis.total < 0 || typeof analysis.complete !== "boolean" ||
        !Number.isInteger(analysis.ignoredNested) || analysis.ignoredNested < 0) fail("房間候選的分析紀錄不合法。");
    const ordinals = new Set();
    for (const row of draft.rows) {
      if (!keys(row, ["rowKey", "ordinal", "method", "sourcePoints", "warnings", "deviation", "pointsMm", "dimensions", "rawInputs", "draftRevision", "status"], ["roomId"]) ||
          typeof row.rowKey !== "string" || row.rowKey.length < 1 || row.rowKey.length > MAX_RAW ||
          !Number.isInteger(row.ordinal) || row.ordinal < 1 || row.ordinal > MAX_ROWS || ordinals.has(row.ordinal) ||
          !["pdf-vector", "image-lines"].includes(row.method) || !Array.isArray(row.sourcePoints) || row.sourcePoints.length < 4 || row.sourcePoints.length > 256 ||
          !row.sourcePoints.every(point => Array.isArray(point) && point.length === 2 && point.every(value => Number.isFinite(value))) ||
          !Array.isArray(row.warnings) || row.warnings.length > 100 || !row.warnings.every(warning => typeof warning === "string" && warning.length <= 1000) ||
          !finite(row.deviation, 0, 1e8) || !Number.isInteger(row.draftRevision) || row.draftRevision < 0 ||
          !["pending", "excluded", "accepted", "existing"].includes(row.status)) fail("房間候選列不合法。");
      ordinals.add(row.ordinal);
      ring(row.pointsMm, "候選外環");
      if (!Array.isArray(row.dimensions) || row.dimensions.length > MAX_DIMENSIONS || !row.dimensions.every(item => keys(item, ["edge", "length", "kind"]) &&
          Number.isInteger(item.edge) && item.edge >= 0 && item.edge < row.pointsMm.length && Number.isInteger(item.length) && item.length > 0 && item.kind === "user-confirmed-mm"))
        fail("房間候選的核對尺寸不合法。");
      const raw = row.rawInputs;
      if (!keys(raw, ["refRoomVertices", "refRoomLength", "refRoomEdge"]) || !["refRoomVertices", "refRoomLength", "refRoomEdge"].every(key => typeof raw[key] === "string" && raw[key].length <= MAX_RAW))
        fail("房間候選的表單原字串不合法。");
      if (row.status === "accepted") { if (!id(row.roomId)) fail("已接受的房間候選必須保存房間記錄 id。"); }
      else if (Object.hasOwn(row, "roomId")) fail("未接受的房間候選不得預先配號。");
    }
    if (new TextEncoder().encode(JSON.stringify(draft)).length > MAX_BYTES) fail("房間候選草稿超過 1 MiB。");
    return draft;
  }
  function freshness(draft, view) {
    validate(draft);
    const note = view.analyzerRevision !== draft.analysis.analyzerRevision ? "分析器版本不同" : "";
    if (draft.anchor.kind === "collection") {
      if (!view.plane || view.plane.id !== draft.anchor.planeId || !view.collection || view.collection.id !== draft.anchor.collectionId)
        return {fresh: false, reason: "共享來源或房間集合已不存在。", note};
      if (planePin(view.plane) !== draft.anchor.planePin) return {fresh: false, reason: "共同基準已變更", note};
      if (view.roomsPin !== draft.anchor.roomsPin) return {fresh: false, reason: "房間清單已變更", note};
      return {fresh: true, reason: "", note};
    }
    const page = view.page;
    if (!page || page.id !== draft.anchor.pageId || view.hostBoundaryId !== draft.anchor.boundaryId || !page.calibration)
      return {fresh: false, reason: "宿主圖頁已不在或尚未校準。", note};
    if (pagePin(page) !== draft.anchor.pagePin) return {fresh: false, reason: "圖頁已變更", note};
    if (view.planeForPage) return {fresh: false, reason: "此來源頁已有共享來源。", note};
    return {fresh: true, reason: "", note};
  }
  function assertSelectable(draft, report) {
    validate(draft);
    if (!report.fresh) fail("過期草稿不可選取、預覽或接受。");
  }
  function rowFromLive(row, ordinal) {
    const status = row.status === "accepted" && row.roomId ? "accepted" : row.status === "accepted" && row.existing ? "existing" : row.status === "excluded" ? "excluded" : "pending";
    const raw = row.rawInputs || {};
    const out = {rowKey: String(row.id), ordinal, method: row.method, sourcePoints: row.sourcePoints, warnings: row.warnings || [], deviation: row.deviation,
      pointsMm: row.points, dimensions: row.dimensions || [],
      rawInputs: {refRoomVertices: raw.refRoomVertices || "", refRoomLength: raw.refRoomLength || "", refRoomEdge: raw.refRoomEdge || "0"},
      draftRevision: row.revision || 0, status};
    if (status === "accepted") out.roomId = row.roomId;
    return out;
  }
  function rowsFromLive(candidates) {
    return (Array.isArray(candidates) ? candidates : []).map((row, index) => rowFromLive(row, index + 1));
  }
  function persistValue(draft) {
    if (draft === null) return null;
    validate(draft);
    return draft.rows.some(row => row.status === "pending" || row.status === "excluded") ? copy(draft) : null;
  }
  return {SCHEMA, CAPABILITY, KIND, ANALYZER_REVISION, MAX_ROWS, MAX_RAW, MAX_BYTES, sha256Hex, canonical, pin, pageFields, pagePin, planePin, roomsPin,
    orthogonal, validate, freshness, assertSelectable, rowFromLive, rowsFromLive, persistValue};
});
