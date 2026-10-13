/* #77 manual rooms: session draft -> native preview -> atomic owner commit. */
(function (root, factory) {
  const api = factory(typeof module === "object" && module.exports ? require("./source-plane.js") : root.GeometrySourcePlane);
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.GeometryRoomCollection = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (S) {
  "use strict";
  const copy = value => structuredClone(value);
  const fail = message => { throw new Error(message); };
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  function points(pts) {
    if (!Array.isArray(pts) || pts.length < 4 || pts.length > 10000 || !pts.every(p => Array.isArray(p) && p.length === 2 &&
        p.every(v => Number.isSafeInteger(v) && Math.abs(v) <= 1e8))) fail("房間外環必須使用有效整數毫米座標。");
    return copy(pts); // The real native preview decides orthogonality, topology and dependencies.
  }
  function nativeLoops(value) {
    if (Array.isArray(value)) return value;
    if (!value || !["unspecified", "room_plan", "wall_elevation"].includes(value.kind)) fail("原生邊界分類讀取失敗。");
    return value.loops;
  }
  async function boundaryPin(definition) {
    const loops = nativeLoops(definition);
    validateNativeLoops(loops);
    if (!Array.isArray(definition)) {
      if (!/^[a-f0-9]{64}$/.test(definition.geometryFingerprint || "")) fail("原生邊界指紋讀取失敗。");
      return definition.geometryFingerprint;
    }
    const bytes = new TextEncoder().encode(JSON.stringify(loops.map(loop => [loop.verts, loop.fixity])));
    const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
    return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, "0")).join("");
  }
  function validateNativeLoops(loops) {
    if (!Array.isArray(loops) || !loops.length || loops.length > 10000 || !loops.every(loop => loop &&
      Array.isArray(loop.verts) && loop.verts.length >= 4 && loop.verts.length <= 10000 &&
      loop.verts.every(p => Array.isArray(p) && p.length === 2 && p.every(v => Number.isSafeInteger(v) && Math.abs(v) <= 1e8)) &&
      Array.isArray(loop.fixity) && loop.fixity.length === loop.verts.length && loop.fixity.every(v => v === 0 || v === 1))) fail("原生邊界讀取失敗。");
  }
  function buildBoundaryCommand(id, outline, existing = null) {
    if (!Number.isInteger(id) || id < 1 || id > 4294967295) fail("原生邊界編號不合法。");
    points(outline);
    const existingDefinition = existing;
    if (existing !== null) {existing = nativeLoops(existing); validateNativeLoops(existing);}
    const verts = pts => pts.map(p => p.join(",")).join(" "), flags = values => values.map(v => v ? "fixed" : "free").join(" ");
    let command = `boundary ${id}` + (existingDefinition && !Array.isArray(existingDefinition) ? " kind " + existingDefinition.kind : "") + " outline " + verts(outline);
    // Exact unchanged edges preserve fixity; a new edge uses native FIXED default.
    const outer = existing?.[0], fixity = outline.map((point, index) => {
      const end = outline[(index + 1) % outline.length], equal = (a, b) => a[0] === b[0] && a[1] === b[1];
      const old = outer?.verts.findIndex((a, i) => {const b = outer.verts[(i + 1) % outer.verts.length]; return equal(a, point) && equal(b, end) || equal(a, end) && equal(b, point);});
      return old === undefined || old < 0 ? 1 : outer.fixity[old];
    });
    if (fixity.some(f => !f)) command += " fixity " + flags(fixity);
    for (const loop of (existing || []).slice(1)) {
      command += " hole " + verts(loop.verts);
      if (loop.fixity.some(f => !f)) command += " fixity " + flags(loop.fixity);
    }
    return command;
  }
  class Controller {
    constructor(adapter) { this.a = adapter; this.intent = null; this.preview = null; this.generation = 0; this.busy = false; }
    state() { return copy(S.validate(this.a.readAttachment())); }
    requireIdle() { if (this.busy || this.intent) fail("請先完成或取消目前房間草稿。"); this.a.assertEditable(); }
    begin(collectionId, roomId = null) {
      this.requireIdle(); const state = this.state(), collection = state.collections.find(c => c.id === collectionId);
      if (!collection) fail("房間集合不存在。");
      const plane = state.planes.find(p => p.id === collection.planeId);
      if (!plane.calibration) fail("請先完成共享來源校準。");
      const room = roomId === null ? null : state.rooms.find(r => r.id === roomId && collection.roomIds.includes(r.id));
      if (roomId !== null && !room) fail("請明確選擇要編輯的房間。");
      if (room?.reviewState === "needs-reassociation") fail("原生邊界身份無法確認，請重新關聯。");
      this.intent = {generation: ++this.generation, collectionId, roomId, room: copy(room), plane: copy(plane),
        state, stamp: this.a.readProjectStamp(), incarnation: room ? this.a.boundaryIncarnation(room.boundaryRef.id) : null};
      return copy(this.intent);
    }
    beginNew(collectionId) { return this.begin(collectionId); }
    beginEdit(collectionId, roomId) { return this.begin(collectionId, roomId); }
    assertCurrent(intent = this.intent) {
      this.a.assertEditable();
      if (!intent || this.intent !== intent || intent.generation !== this.generation || !same(intent.stamp, this.a.readProjectStamp()) ||
          !same(intent.state, this.a.readAttachment()) || (intent.room && this.a.boundaryIncarnation(intent.room.boundaryRef.id) !== intent.incarnation)) fail("專案、房間或來源基準已變更，請取消草稿後重新操作。");
    }
    async prepare(pts, name) {
      this.assertCurrent(); if (this.busy) fail("房間預覽處理中。");
      if (typeof name !== "string" || !name.trim() || name.trim().length > 200) fail("請填寫房間名稱（最多 200 字）。");
      const outline = points(pts), intent = this.intent; this.busy = true;
      try {
        if (this.preview) { await this.a.cancelPreview(this.preview.token); this.preview = null; this.assertCurrent(intent); }
        const id = intent.room ? intent.room.boundaryRef.id : await this.a.allocateBoundary(); this.assertCurrent(intent);
        const existing = await this.a.readBoundary(id); this.assertCurrent(intent);
        if (!intent.room && existing) fail("新房間編號已被使用，未覆蓋既有邊界。");
        if (intent.room && (!existing || await boundaryPin(existing) !== intent.room.boundaryRef.associationPin)) fail("原生邊界已變更，請重新核對或關聯。");
        this.assertCurrent(intent);
        const command = await this.a.boundaryCommand(id, outline, existing); this.assertCurrent(intent);
        const preview = await this.a.previewBoundary(command);
        // Cancel only this adapter's owned token; never cancel another workflow's candidate.
        try { this.assertCurrent(intent); } catch (error) { if (preview?.token) await this.a.cancelPreview(preview.token); throw error; }
        if (!preview?.ok || preview.valid !== true || !Number.isInteger(preview.token) || preview.token < 1) {
          if (preview?.token) await this.a.cancelPreview(preview.token);
          fail(preview?.error || "原生房間預覽未通過。");
        }
        const rows = Array.isArray(preview.boundaries) ? preview.boundaries.filter(row => row?.id === id) : [];
        let candidatePin;
        try {
          if (intent.room && Array.isArray(preview.boundaries) && preview.boundaries.length === 0)
            candidatePin = await boundaryPin(existing); // An unchanged native candidate has no delta row.
          else {
            if (rows.length !== 1 || rows[0].after?.id !== id || !intent.room && rows[0].before !== null)
              fail("新房間編號已被使用或候選身份無法確認，未覆蓋既有邊界。");
            candidatePin = await boundaryPin(rows[0].after);
          }
          this.assertCurrent(intent);
        } catch (error) {await this.a.cancelPreview(preview.token);throw error;}
        this.preview = {token: preview.token, id, name: name.trim(), command,candidatePin};
        return {...copy(this.preview), review: preview};
      } finally { this.busy = false; }
    }
    async confirm() {
      this.assertCurrent(); if (!this.preview || this.busy) fail("請先核對原生房間預覽。");
      const intent = this.intent, preview = this.preview; this.busy = true;
      try {
        const roomId = intent.roomId || this.a.uuid();
        const attachmentForPin = pin => {
          const next = copy(intent.state), collection = next.collections.find(c => c.id === intent.collectionId),
            room = {id:roomId,name:preview.name,boundaryRef:{kind:"boundary",id:preview.id,associationPin:pin},
              acceptedBasisRevision:intent.plane.basisRevision,reviewState:"confirmed",
              ...(next.schema===S.DISPLAY_SCHEMA?{display:intent.room?copy(intent.room.display):S.defaultDisplay(intent.plane)}:{})};
          if (intent.room) next.rooms[next.rooms.findIndex(r=>r.id === roomId)] = room;
          else {next.rooms.push(room);collection.roomIds.push(roomId);}
          return S.validate(next);
        };
        // Admission uses the real detached candidate pin. Publication still
        // requires the committed native definition to match that exact pin.
        const result = await this.a.commitWithMetadata({token: preview.token, boundaryId: preview.id,
          proposeAttachment:() => attachmentForPin(preview.candidatePin),
          label: intent.room ? "編輯房間「" + preview.name + "」" : "新增房間「" + preview.name + "」",
          assertCurrent: () => this.assertCurrent(intent), makeAttachment: async loops => {
            const pin = await boundaryPin(loops);
            // Complete native definitions retain their typed candidate pin;
            // the legacy loops-only adapter derives its geometry-only pin.
            if (!Array.isArray(loops) && pin !== preview.candidatePin) fail("原生候選與已確認邊界不一致，未寫入房間來源。");
            return attachmentForPin(pin);
          }});
        if (!result?.ok) throw Object.assign(new Error(result?.error || "房間確認未完成。"), {transport: result?.transport});
        this.intent = null; this.preview = null; this.generation++;
        return {id: roomId, boundaryId: preview.id};
      } catch (error) {
        if (!error.transport) this.preview = null; // A known terminal rejection retires the native candidate.
        throw error;
      } finally { this.busy = false; }
    }
    async cancel() {
      if (this.busy) fail("請等候房間操作完成再取消。");
      if (this.preview) await this.a.cancelPreview(this.preview.token);
      this.preview = null; this.intent = null; this.generation++;
    }
    change(next, label) {
      this.requireIdle(); const before = this.state(), stamp = this.a.readProjectStamp(); S.validate(next);
      if (!same(before, next)) this.a.changeMetadata(copy(next), {label, stamp});
      return this.state();
    }
    addPlane(plane, collectionId) {
      const next = this.state(); S.validatePlane(plane);
      if (next.planes.some(p => p.id === plane.id) || next.collections.some(c => c.id === collectionId)) fail("來源集合識別已存在。");
      next.planes.push(copy(plane)); next.collections.push({id: collectionId, planeId: plane.id, roomIds: []});
      return this.change(next, "建立共享房間來源");
    }
    async associate(collectionId, boundaryId, name, roomId = null) {
      this.requireIdle(); const before = this.state(), next = copy(before), collection = next.collections.find(c => c.id === collectionId);
      if (!collection || !Number.isInteger(boundaryId) || boundaryId < 1 || boundaryId > 4294967295) fail("請明確選擇原生邊界與來源集合。");
      if (next.rooms.some(r => r.boundaryRef.id === boundaryId && r.id !== roomId)) fail("此邊界已關聯其他房間。");
      const old = roomId === null ? null : next.rooms.find(r => r.id === roomId && collection.roomIds.includes(roomId));
      if (roomId !== null && !old) fail("要重新關聯的房間不存在。");
      const stamp = this.a.readProjectStamp(), incarnation = this.a.boundaryIncarnation(boundaryId);
      this.busy = true;
      let pin;
      try {const loops = await this.a.readBoundary(boundaryId); pin = await boundaryPin(loops);}
      finally {this.busy = false;}
      if (!same(stamp, this.a.readProjectStamp()) || !same(before, this.a.readAttachment()) || incarnation !== this.a.boundaryIncarnation(boundaryId)) fail("房間關聯結果晚到，請重新操作。");
      const room = {id: roomId || this.a.uuid(), name: typeof name === "string" ? name.trim() : name,
        boundaryRef: {kind: "boundary", id: boundaryId, associationPin: pin}, acceptedBasisRevision: S.planeForRoom(next, roomId)?.basisRevision || next.planes.find(p => p.id === collection.planeId).basisRevision,
        reviewState: "confirmed",
        ...(next.schema===S.DISPLAY_SCHEMA?{display:old?copy(old.display):S.defaultDisplay(next.planes.find(p=>p.id===collection.planeId))}:{})};
      if (old) next.rooms[next.rooms.findIndex(r => r.id === old.id)] = room;
      else { next.rooms.push(room); collection.roomIds.push(room.id); }
      return this.change(next, old ? "明選重新關聯房間" : "明選關聯既有房間");
    }
    basis(planeId, calibration, alignment) { return this.change(S.changeBasis(this.state(), planeId, calibration, alignment), "調整共享來源基準"); }
    sourceView(roomId,calibration,alignment,display) {
      const before=this.state(),plane=S.planeForRoom(before,roomId);if(!plane)fail('房間來源不存在。');
      const next=S.changeDisplay(S.changeBasis(before,plane.id,calibration,alignment),roomId,display);
      return this.change(next,JSON.stringify([plane.calibration,plane.alignment])===JSON.stringify([calibration,alignment])?'調整房間顯示':'調整共享來源基準');
    }
    rename(roomId, name) {
      const next = this.state(), room = next.rooms.find(r => r.id === roomId); if (!room) fail("房間不存在。");
      room.name = typeof name === "string" ? name.trim() : name; return this.change(next, "重新命名房間");
    }
    unlink(roomId) {
      const next = this.state(); if (!next.rooms.some(r => r.id === roomId)) fail("房間不存在。");
      next.rooms = next.rooms.filter(r => r.id !== roomId);
      for (const collection of next.collections) collection.roomIds = collection.roomIds.filter(id => id !== roomId);
      return this.change(next, "解除房間列表關聯");
    }
    unlinkPlane(planeId) {
      const next = this.state(), collections = next.collections.filter(c => c.planeId === planeId), removed = new Set(collections.flatMap(c => c.roomIds));
      if (!next.planes.some(p => p.id === planeId)) fail("來源平面不存在。");
      if (next.legacyHistory?.some(entry => entry.planeId === planeId)) fail("此來源含保存的歷史紀錄；請保留來源，房間仍可解除列表關聯。");
      next.planes = next.planes.filter(p => p.id !== planeId); next.collections = next.collections.filter(c => c.planeId !== planeId);
      next.rooms = next.rooms.filter(r => !removed.has(r.id)); return this.change(next, "解除共享來源與房間列表關聯");
    }
    async review(roomId) {
      this.requireIdle(); const before = this.state(), next = copy(before), room = next.rooms.find(r => r.id === roomId);
      if (!room || room.reviewState === "needs-reassociation") fail("請先重新關聯原生房間邊界。");
      const stamp = this.a.readProjectStamp(), incarnation = this.a.boundaryIncarnation(room.boundaryRef.id);
      this.busy = true;
      let pin;
      try {const loops = await this.a.readBoundary(room.boundaryRef.id); pin = await boundaryPin(loops);}
      finally {this.busy = false;}
      if (!same(stamp, this.a.readProjectStamp()) || !same(before, this.a.readAttachment()) || incarnation !== this.a.boundaryIncarnation(room.boundaryRef.id)) fail("房間核對結果晚到，請重新操作。");
      room.boundaryRef.associationPin = pin; room.acceptedBasisRevision = S.planeForRoom(next, room.id).basisRevision; room.reviewState = "confirmed";
      return this.change(next, "核對房間與共享來源");
    }
  }
  return {Controller, boundaryPin, buildBoundaryCommand};
});
