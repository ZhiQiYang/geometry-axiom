/* Thin adapter for the existing reference/face workspace; shared owner wires hooks. */
const RoomCollectionWorkspace = (() => {
  "use strict";
  const S = GeometrySourcePlane, R = GeometryRoomCollection;
  const pages = new Map(),renders=new Map();
  let overviewCollectionId = null, overviewContextToken = null;
  let candidateSession = null, candidateGeneration = 0, candidateMode = 'manual', zeroMode = 'adopt';
  let writingCandidates = false;
  let instance = null, activeBid = null, lease = null, ownedPreviewToken = null, ownedPreviewCommand = null, currentDialog = null, retireDialog = null, integration = null, cleaningUI = false;
  // R51 needs each referenced D3's *current native* fingerprint. Native boundary
  // reports are remembered per owner token and D3 incarnation; any native change
  // that may overlap a report forgets it, so a remembered value is never older
  // than the last observed change.
  const nativePins = new Map(), previewBoundaries = new Map(), nativeRefresh = new Map();
  let nativeEpoch = 0, nativeSettled = 0, nativeReadOrder = 0, nativeGroup = null, nativeReadFailure = null, nativeObjects = null;
  const nativeChanging = new Set();
  const W = () => ReferenceWorkspace;
  const token = () => W().getProjectState().contextToken;
  const state = () => W().readFeatureAttachment("source-rooms", token()) || S.empty();
  const escape = value => W().escape(value);
  const isHash = value => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
  const NATIVE_CHANGE = /^(line |drag |reset$|default$|undo$|redo$|loadfile |engineering-confirm |assembly-confirm |section-profile-confirm )/;
  // Commands that never change a committed boundary definition when they succeed.
  const NATIVE_STEADY = /^line (?:$|preview\b|cancel-preview\b|history-(?:begin|end)\b|canvas-pos\b)/;
  function ensureReady() {
    if (!W().readFeatureAttachment || !W().setFeatureAttachment || !integration) throw new Error("房間來源接線尚未啟用。");
  }
  function configure(adapter) {
    for (const name of ["readSource", "readIncarnation", "beginTransaction", "assertTransaction", "endTransaction", "preflightAttachment", "groupOpen", "labelTransaction", "adoptLegacySource"])
      if (typeof adapter?.[name] !== "function") throw new Error("房間來源缺少 owner 接口：" + name);
    integration = adapter;
  }
  function nativeCommand(command) {
    if (typeof command !== "string") return "";
    return command.startsWith("line ") ? "line " + command.slice(5).split("#", 1)[0].trim() : command.trim();
  }
  function pinScope() {
    try { return integration && W()?.getModelOperationState ? W().getModelOperationState().contextToken : null; } catch (_) { return null; }
  }
  function forgetNativePins(ids = null) {
    if (ids === null) {nativeObjects = null; nativePins.clear(); previewBoundaries.clear();}
    else for (const id of ids) {nativePins.delete(id); nativeObjects?.unknown.add(id);}
  }
  // Applies one settled result of a changing command to the remembered fingerprints.
  function noteNativeChange(command, result) {
    if (result?.ok !== true) {
      if (result?.stale === true) return; // Version rejection did not reach native.
      // Unknown delivery: anything may have changed.
      if (!result || result.transport) {forgetNativePins(); nativeGroup = null; return;}
      // A known rejection changes nothing, except that the core rolls back an open group
      // (a rejected preview keeps it): values learnt inside that group no longer hold.
      if (nativeGroup && !/^line preview\b/.test(command)) {forgetNativePins(nativeGroup); nativeGroup = null;}
      return;
    }
    if (/^line preview\b/.test(command)) {
      const preview = result.preview;
      if (preview?.valid === true && Number.isInteger(preview.token) && Array.isArray(preview.boundaries) && preview.boundaries.every(row => Number.isInteger(row?.id))) {
        previewBoundaries.set(String(preview.token), {scope: pinScope(), ids: preview.boundaries.map(row => row.id)});
        if (previewBoundaries.size > 32) previewBoundaries.delete(previewBoundaries.keys().next().value);
      }
      return;
    }
    if (/^line history-begin\b/.test(command)) {nativeGroup = new Set(); return;}
    if (/^line history-end\b/.test(command)) {nativeGroup = null; return;}
    if (/^line history-abort\b/.test(command)) {forgetNativePins(nativeGroup); nativeGroup = null; return;}
    if (NATIVE_STEADY.test(command)) return;
    const confirmed = command.match(/^line confirm (\d+)$/), recorded = confirmed && previewBoundaries.get(confirmed[1]);
    if (confirmed) previewBoundaries.delete(confirmed[1]);
    // A confirmed preview changes exactly its listed boundaries; anything else may change any of them.
    if (recorded && recorded.scope === pinScope()) forgetNativePins(recorded.ids); else forgetNativePins();
  }
  function rememberBoundaryRead(command, result, scope, order, ownerRevision) {
    const match = command.match(/^boundary (\d+)$/);
    if (!match) return;
    const id = Number(match[1]);
    let incarnation = null;
    if (scope === null || scope !== pinScope()) return;
    if ((nativePins.get(id)?.order ?? 0) > order) return;
    try { incarnation = integration.readIncarnation(id, token()) ?? null; } catch (_) { return; }
    if (!result?.ok || result.id !== id || !isHash(result.geometryFingerprint)) {
      nativePins.delete(id); return;
    }
    nativePins.set(id, {scope, incarnation, pin: result.geometryFingerprint, order, ownerRevision});
    nativeGroup?.add(id);
  }
  function rememberObjects(result, scope, order, ownerRevision) {
    if (scope === null || scope !== pinScope()) return;
    if ((nativeObjects?.order ?? 0) > order) return;
    if (!result?.ok || !Array.isArray(result.faces) || result.faces.some(face =>
        !Number.isSafeInteger(face?.id) || face.id <= 0 || typeof face.kind !== "string")) {nativeObjects = null; return;}
    nativeObjects = {scope, ids: new Set(result.faces.filter(face => face.kind === "boundary").map(face => face.id)), unknown: new Set(), order, ownerRevision};
  }
  // apiRequest calls this once, immediately before delivery, and settles it once.
  // Diagnostic wrappers never own this observation and cannot make it run twice.
  function beginNativeRequest(text) {
    const command = nativeCommand(text), change = NATIVE_CHANGE.test(command), steady = change && NATIVE_STEADY.test(command), scope = pinScope();
    const order = ++nativeReadOrder, ownerRevision = W().getModelOperationState().revision;
    const ticket = {};
    if (change && !steady) {nativeEpoch++; nativeChanging.add(ticket);}
    const epoch = nativeEpoch;
    let settled = false;
    return result => {
      if (settled) return; settled = true; nativeChanging.delete(ticket);
      try {
        nativeSettled++;
        if (change) {if (!steady || result?.ok !== true) nativeEpoch++; noteNativeChange(command, result);}
        else if (epoch === nativeEpoch && !nativeChanging.size) {
          if (command === "objects") rememberObjects(result, scope, order, ownerRevision);
          else rememberBoundaryRead(command, result, scope, order, ownerRevision);
        }
      } catch (_) { /* Observation must not change the request's result. */ }
    };
  }
  function request(command) { return apiRequest(command, lease); }
  function assertTransaction(ownerLease) {ensureReady(); return integration.assertTransaction(ownerLease);}
  async function checked(command) {
    const result = await request(command);
    if (!result.ok) throw Object.assign(new Error(result.error || "房間操作失敗。"), {transport: result.transport});
    return result;
  }
  async function cancelOwnedCandidate() {
    try {
      await checked("line cancel-preview"); ownedPreviewToken = null; ownedPreviewCommand = null;
    } catch (error) {
      // A known rejection before delivery still leaves our native candidate
      // unsettled. Keep ownership and expose the existing recovery path.
      error.transport = true;
      if (connection.phase !== "error" && typeof connectionFailed === "function") connectionFailed("房間候選尚未取消：" + error.message);
      throw error;
    }
  }
  function boundaryCommand(id, outline, existing) {
    return R.buildBoundaryCommand(id, outline, existing);
  }
  function controller() {
    ensureReady();
    return instance ||= new R.Controller({
      uuid: () => crypto.randomUUID(), readAttachment: state, readProjectStamp: () => W().getProjectState(),
      assertEditable: () => lease ? integration.assertTransaction(lease) : W().assertEditable(),
      boundaryIncarnation: id => integration.readIncarnation(id, token()),
      allocateBoundary: async () => (await checked("newid")).boundary,
      readBoundary: async id => {const result = await request("boundary " + id); return result.ok ? result : null;},
      boundaryCommand,
      previewBoundary: async command => {
        lease = integration.beginTransaction(token());
        ownedPreviewCommand = "line preview " + command;
        const result = await request("line preview " + command);
        if (!result.ok) {
          if (!result.transport) {integration.endTransaction(lease); lease = null; ownedPreviewCommand = null;}
          throw Object.assign(new Error(result.error || "房間預覽失敗。"), {transport: result.transport});
        }
        ownedPreviewToken = result.preview?.token;
        return {ok: result.ok, ...result.preview};
      },
      cancelPreview: async previewToken => {
        // The workspace owns the only pending draft; callers cannot cancel a foreign token.
        if (!lease || ownedPreviewToken !== previewToken) throw new Error("房間預覽識別已變更，未取消其他工作的候選。");
        integration.assertTransaction(lease);
        await cancelOwnedCandidate(); integration.endTransaction(lease); lease = null;
      },
      changeMetadata: (next, {label, stamp}) => W().setFeatureAttachment("source-rooms", next, stamp.contextToken, {recordHistory: true, reason: label}),
      assertHost(host) {
        const page = W().active(host.boundaryId), D = GeometryRoomCandidateDraft;
        if (!page?.calibration || page.id !== host.pageId || D.pagePin(page) !== D.pagePin(host.page)) throw new Error("宿主圖頁已變更，請取消草稿後重新操作。");
        if (state().planes.some(item => item.sourceId === page.sourceId && item.page === page.page)) throw new Error("此來源頁已有共享來源，請從該集合新增房間。");
      },
      afterGroupedRooms(payload) { acceptCandidateRow(payload); },
      commitWithMetadata: async ({token: previewToken, boundaryId, label, assertCurrent, makeAttachment, proposeAttachment, afterGroupedRooms}) => {
        assertCurrent(); integration.assertTransaction(lease);
        if (ownedPreviewToken !== previewToken) throw new Error("房間預覽識別已變更。");
        let begun = false, unknown = false;
        try {
          integration.preflightAttachment(proposeAttachment(),lease);
          assertCurrent(); await checked("line history-begin"); begun = true;
          assertCurrent(); await checked("line confirm " + previewToken);
          const native = await checked("boundary " + boundaryId);
          const attachment = await makeAttachment(native); integration.assertTransaction(lease);
          W().setFeatureAttachment("source-rooms", attachment, lease.contextToken, {recordHistory: false, roomLease: lease, reason: label});
          if (afterGroupedRooms) await afterGroupedRooms({boundaryId, attachment, lease});
          await checked("line history-end"); begun = false;
          integration.labelTransaction(lease, label);
          return {ok: true};
        } catch (error) {
          unknown = !!error.transport || connection.phase === "error";
          if (!unknown) {
            try {
              if (begun && integration.groupOpen(lease)) await checked("line history-abort");
              // Aborting an unchanged native group does not necessarily retire
              // its unconfirmed candidate. Settle it before releasing ownership.
              if (ownedPreviewToken !== null) {
                await cancelOwnedCandidate();
              }
            }
            catch (rollbackError) {
              // A rollback with no confirmed outcome still owns the native group.
              unknown = !!rollbackError.transport || connection.phase === "error";
              if (!unknown) {
                try {unknown = integration.groupOpen(lease) || ownedPreviewToken !== null;} catch (_) {unknown = true;}
              }
              if (unknown && connection.phase !== "error" && typeof connectionFailed === "function")
                connectionFailed("房間交易尚未回復：" + rollbackError.message);
              rollbackError.transport = unknown;
              throw rollbackError;
            }
          }
          error.transport = unknown;
          throw error;
        } finally {
          // Unknown transport outcomes retain the lease until the existing receipt recovery aborts/settles the group.
          if (!unknown) {integration.endTransaction(lease); lease = null; ownedPreviewToken = null; ownedPreviewCommand = null;}
        }
      }
    });
  }
  function roomForBoundary(bid) { return state().rooms.find(r => r.boundaryRef.id === bid && r.reviewState !== "needs-reassociation") || null; }
  function sourcePage(bid) {
    if (!W().readFeatureAttachment || !integration) return null;
    const data = state(), room = data.rooms.find(r => r.boundaryRef.id === bid && r.reviewState !== "needs-reassociation");
    if (!room) return null;
    const plane = S.planeForRoom(data, room.id), contextToken = token();
    if (!pages.has(contextToken)) {pages.set(contextToken, new Map()); if(pages.size > 32)pages.delete(pages.keys().next().value);}
    const renderKey=JSON.stringify([plane.sourceId,plane.page,plane.pageSize]),render=renders.get(renderKey);
    const display=S.displayForRoom(data,room.id),cache = pages.get(contextToken), old = cache.get(bid), signature = JSON.stringify([plane,display]);
    if (old && old.planeId === plane.id) {
      if (old.signature !== signature) {Object.assign(old.page, S.materialize(plane, old.page,display)); old.signature = signature;}
      old.page.reviewRequired = room.reviewState !== "confirmed"; return old.page;
    }
    const page = S.materialize(plane,render?{src:render}:{},display); page.reviewRequired = room.reviewState !== "confirmed";
    cache.set(bid, {planeId: plane.id, signature, page}); return page;
  }
  async function prepareSharedPages(contextToken = token()) {
    if (!W().readFeatureAttachment || !integration) return;
    const stamp = W().getProjectState();
    for (const room of state().rooms) {
      const p = sourcePage(room.boundaryRef.id); if (!p || p.src) continue;
      const source = integration.readSource(p.sourceId, contextToken); if (!source) throw new Error("共享來源檔案已遺失。");
      await W().preparePage(p, source);
      if (token() !== contextToken || W().getProjectState().revision !== stamp.revision) throw new Error("共享來源載入晚到，未套用到目前專案。");
      // Cache only the derived raster by the original content hash/page. View
      // metadata always comes from the current persisted room, including undo.
      renders.set(JSON.stringify([p.sourceId,p.page,[p.imgW,p.imgH]]),p.src);
      if(renders.size>S.MAX_PLANES)renders.delete(renders.keys().next().value);
    }
    W().sync();
  }
  function collectionFor(bid) {
    const data = state(), room = data.rooms.find(r => r.boundaryRef.id === bid && r.reviewState !== "needs-reassociation");
    return room ? data.collections.find(c => c.roomIds.includes(room.id)) : null;
  }
  const same = (a,b) => JSON.stringify(a) === JSON.stringify(b);
  const Drafts = () => GeometryRoomCandidateDraft;
  // R51: [roomId, boundaryId, current native fingerprint of the referenced D3 (null when it
  // does not exist), acceptedBasisRevision, reviewState]. undefined = not known yet.
  function currentNativePin(room, known = {}) {
    if (Object.hasOwn(known, room.id)) return known[room.id];
    if (nativeChanging.size) return undefined;
    const id = room.boundaryRef.id, scope = pinScope(), incarnation = integration.readIncarnation(id, token()) ?? null;
    const report = nativePins.get(id);
    if (report && report.scope === scope && report.incarnation === incarnation) return report.pin;
    // A missing runtime incarnation can mean objects has not synchronized yet.
    // Only the current native object list proves absence; metadata is a receipt.
    if (nativeObjects?.scope === scope && !nativeObjects.unknown.has(id) && !nativeObjects.ids.has(id)) return null;
    return undefined;
  }
  function collectionRoomsPin(data, collection, unknown = [], known = {}) {
    const rooms = collection.roomIds.map(id => {
      const room = data.rooms.find(item => item.id === id), pin = currentNativePin(room, known);
      if (pin === undefined) unknown.push(room.boundaryRef.id);
      return {id: room.id, boundaryRef: {id: room.boundaryRef.id, geometryFingerprint: pin ?? null},
        acceptedBasisRevision: room.acceptedBasisRevision, reviewState: room.reviewState};
    });
    return unknown.length ? null : Drafts().roomsPin(rooms);
  }
  async function readNativePins(bid) {
    // Reads the referenced D3 definitions whose current native fingerprint is not known yet.
    // A report that overlapped a native change is discarded and read again (bounded).
    const scope = pinScope(), owner = W().getModelOperationState(), firstRead = nativeReadOrder;
    const assertOwner = () => {
      if (pinScope() !== scope || !same(W().getModelOperationState(), owner)) {
        // Retire only reports learnt by obsolete work. A newer independent read
        // must survive this late rejection (including a save during refresh).
        for (const [id, report] of nativePins) if (report.scope === scope && report.order > firstRead && report.ownerRevision === owner.revision) nativePins.delete(id);
        if (nativeObjects?.scope === scope && nativeObjects.order > firstRead && nativeObjects.ownerRevision === owner.revision) nativeObjects = null;
        throw new Error("房間原生幾何讀取期間專案或版本已變更，請重新操作。");
      }
    };
    for (let attempt = 0; attempt < 3; attempt++) {
      assertOwner();
      const stamp = candidateStamp(bid);
      if (stamp.kind !== "collection" || !stamp.unknownNative.length) return stamp;
      if (nativeObjects?.scope !== scope || stamp.unknownNative.some(id => nativeObjects.unknown.has(id))) {
        const objects = await request("objects"); assertOwner();
        if (!objects.ok) throw new Error("房間原生物件清單讀取失敗：" + (objects.error || "未知錯誤"));
      }
      for (const id of candidateStamp(bid).unknownNative) {
        const result = await request("boundary " + id); assertOwner();
        if (!result.ok) throw Object.assign(new Error("房間 D3 " + id + " 的原生幾何讀取失敗：" + (result.error || "未知錯誤")), {transport: result.transport});
      }
    }
    const after = candidateStamp(bid);
    if (after.kind === "collection" && after.roomsPin === null) throw new Error("房間原生幾何在讀取期間持續變更，請稍候重新操作。");
    return after;
  }
  function candidateStamp(bid) {
    const data = state(), page = W().active(bid), D = Drafts();
    if (!page?.calibration) throw Error("同頁候選需要已校準的圖頁。");
    const {blocked, group, ...owner} = W().getModelOperationState();
    const base = {owner, crop: [...page.crop], rooms: structuredClone(data.rooms), collections: structuredClone(data.collections), planes: structuredClone(data.planes)};
    const direct = collectionFor(bid);
    const covering = direct || data.collections.find(item => {
      const plane = data.planes.find(entry => entry.id === item.planeId);
      return plane && plane.sourceId === page.sourceId && plane.page === page.page;
    });
    if (covering) {
      const plane = data.planes.find(entry => entry.id === covering.planeId), unknownNative = [];
      return {...base, kind: "collection", collectionId: covering.id, plane: structuredClone(plane), planePin: D.planePin(plane),
        roomsPin: collectionRoomsPin(data, covering, unknownNative), unknownNative,
        geometry: structuredClone(data.rooms.map(room => [room.boundaryRef.id, integration.readIncarnation(room.boundaryRef.id, token()), oc.bmap[room.boundaryRef.id]]))};
    }
    return {...base, kind: "page", bid, pageId: page.id, pagePin: D.pagePin(page), hostBoundaryId: bid,
      geometry: structuredClone([[bid, integration.readIncarnation(bid, token()), oc.bmap[bid]]])};
  }
  // The persistent D53 anchor is fixed when the analysis is received (or read back) and
  // changes only inside the acceptance transaction (R52). The observed stamp never repins it.
  function anchorFromStamp(stamp) {
    if (stamp.kind === "page") return {kind: "page", boundaryId: stamp.hostBoundaryId, pageId: stamp.pageId, pagePin: stamp.pagePin};
    if (!isHash(stamp.roomsPin)) throw new Error("房間原生幾何指紋尚未讀取，無法固定候選錨點；請稍候重新分析。");
    return {kind: "collection", collectionId: stamp.collectionId, planeId: stamp.plane.id, planePin: stamp.planePin, roomsPin: stamp.roomsPin};
  }
  function draftFromSession(s, anchor = s.anchor) {
    return {schema: Drafts().SCHEMA, draftId: s.draftId, anchor: structuredClone(anchor), analysis: s.analysis, rows: Drafts().rowsFromLive(s.candidates)};
  }
  // A session belongs to the owner frame (project and history frame) that produced it.
  // Project switches and undo/redo create a new frame; an older session never writes again.
  function ownsSession(s) { return !!s && s.ownerToken === token(); }
  function retireForeignSession() {
    const s = candidateSession;
    if (!s || ownsSession(s) || s.active !== null || s.committing) return false;
    candidateSession = null; candidateGeneration++; return true;
  }
  function foreignSessionError() { return new Error("房間候選工作屬於先前的專案或復原前的狀態；未變更目前專案的草稿。"); }
  function writeSavedCandidates(s, options, value = Drafts().persistValue(draftFromSession(s))) {
    if (!ownsSession(s) || (options.contextToken || s.ownerToken) !== s.ownerToken) throw foreignSessionError();
    writingCandidates = true;
    try {
      W().setFeatureAttachment(Drafts().KIND, value, s.ownerToken, options);
      // A grouped acceptance write is confirmed only by the R52 continuation proof.
      if (options.recordHistory !== false && s === candidateSession && !s.stale) {
        try { s.stamp = candidateStamp(s.bid); } catch (error) { s.stale = true; s.reason = error.message; }
      }
    } finally { writingCandidates = false; }
    return value;
  }
  function revertAcceptance(s, pending) {
    const row = s.candidates[pending.index];
    if (!row) return;
    row.status = pending.previousStatus;
    if (pending.previousRoom === undefined) delete row.roomId; else row.roomId = pending.previousRoom;
  }
  function acceptCandidateRow(payload) {
    const s = candidateSession;
    if (!s || s.active === null) return;
    if (!ownsSession(s) || payload.lease?.contextToken !== s.ownerToken) throw foreignSessionError();
    const index = s.active, row = s.candidates[index], previousStatus = row.status, previousRoom = row.roomId;
    // I65/R52: the grouped draft update already anchors the remaining rows to the committed
    // collection, so a same-transaction save and a cold reopen agree with the continued work.
    const data = payload.attachment, collection = data.collections.find(item => item.id === payload.collectionId);
    const plane = collection && data.planes.find(item => item.id === collection.planeId);
    const accepted = data.rooms.find(item => item.id === payload.roomId);
    if (!plane || !accepted || !collection.roomIds.includes(accepted.id)) throw new Error("新增房間的共享來源無法確認，未寫入候選草稿。");
    // The new room's fingerprint was read from native inside this transaction (makeAttachment).
    const roomsPin = collectionRoomsPin(data, collection, [], {[accepted.id]: accepted.boundaryRef.associationPin});
    if (!isHash(roomsPin)) throw new Error("房間原生幾何指紋無法確認，未寫入候選草稿。");
    const anchor = {kind: "collection", collectionId: collection.id, planeId: plane.id, planePin: Drafts().planePin(plane), roomsPin};
    row.status = "accepted"; row.roomId = payload.roomId; row.reviewed = false;
    try {
      const value = writeSavedCandidates(s, {recordHistory: false, roomLease: payload.lease, contextToken: payload.lease.contextToken},
        Drafts().persistValue(draftFromSession(s, anchor)));
      s.pendingAcceptance = {index, previousStatus, previousRoom, anchor, roomsValue: structuredClone(data), value: value === null ? null : structuredClone(value)};
    } catch (error) {
      revertAcceptance(s, {index, previousStatus, previousRoom});
      throw error;
    }
  }
  // Reads missing D3 fingerprints for a restored draft, then re-renders so the draft is
  // judged again from its stored value. One read per owner token and pane; a failure is
  // not retried until another native result has settled (at most three times).
  function refreshRestoredPins(key, bid) {
    if (nativeRefresh.has(key)) return;
    const scope = pinScope();
    nativeRefresh.set(key, readNativePins(bid).then(() => {nativeReadFailure = null;}, error => {
      const attempts = nativeReadFailure?.key === key ? nativeReadFailure.attempts + 1 : 1;
      nativeReadFailure = {key, settled: nativeSettled, attempts, message: "房間原生幾何指紋讀取失敗：" + error.message};
    }).finally(() => {nativeRefresh.delete(key); if (scope === pinScope()) {invalidateCandidates(); renderFaceInspector();}}));
  }
  const canonical = value => JSON.stringify(value, (_, item) => item && typeof item === "object" && !Array.isArray(item)
    ? Object.fromEntries(Object.keys(item).sort().map(key => [key, item[key]])) : item);
  // A stale restored session that still equals the stored draft holds no work of its own;
  // it is judged again from storage (R51 fingerprints only) instead of keeping a runtime verdict.
  function mirrorsStoredDraft(s, bid) {
    if (!s.parked || (!s.stale && !s.nativePending) || s.expired || s.active !== null || s.committing || s.bid !== bid || !ownsSession(s)) return false;
    try { return canonical(Drafts().persistValue(draftFromSession(s))) === canonical(W().readFeatureAttachment(Drafts().KIND, token())); }
    catch (_) { return false; }
  }
  function restoreSavedCandidates(bid) {
    if (!W().readFeatureAttachment || !integration) return;
    retireForeignSession();
    if (candidateSession) {
      if (!mirrorsStoredDraft(candidateSession, bid)) return;
      candidateSession = null; candidateGeneration++;
    }
    let saved;
    try { saved = W().readFeatureAttachment(Drafts().KIND, token()); } catch { return; }
    if (!saved?.rows) return;
    const page = W().active(bid);
    if (!page) return;
    const anchor = saved.anchor;
    if (anchor?.kind === "page" && (anchor.boundaryId !== bid || anchor.pageId !== page.id)) return;
    if (anchor?.kind === "collection") {
      const data = state(), collection = data.collections.find(item => item.id === anchor.collectionId);
      const plane = collection && data.planes.find(item => item.id === collection.planeId);
      const here = collectionFor(bid);
      if (!here && !(plane && plane.sourceId === page.sourceId && plane.page === page.page)) return;
    }
    const candidates = saved.rows.map(row => ({id: row.rowKey, sourcePoints: row.sourcePoints, points: row.pointsMm, deviation: row.deviation, method: row.method,
      warnings: row.warnings, dimensions: row.dimensions, rawInputs: row.rawInputs, reviewed: false, revision: row.draftRevision,
      status: row.status === "existing" ? "accepted" : row.status, existing: row.status === "existing", ...(row.roomId ? {roomId: row.roomId} : {})}));
    let stamp, stale = false, reason = "", nativePending = false;
    try { stamp = candidateStamp(bid); }
    catch (error) { stale = true; reason = error.message; stamp = {kind: anchor.kind, owner: {}, crop: saved.analysis?.crop || [], rooms: [], collections: [], planes: []}; }
    // R51 freshness compares the persisted anchor with the current domain fingerprints only.
    if (!stale && anchor.kind === "page" && (stamp.kind !== "page" || stamp.pagePin !== anchor.pagePin || stamp.pageId !== anchor.pageId)) { stale = true; reason = "圖頁已變更"; }
    if (!stale && anchor.kind === "collection" && stamp.kind === "collection" && stamp.collectionId === anchor.collectionId &&
        stamp.planePin === anchor.planePin && stamp.roomsPin === null) {
      const key = pinScope() + "\n" + bid, failed = nativeReadFailure?.key === key ? nativeReadFailure : null;
      nativePending = true;
      if (failed && failed.settled === nativeSettled) reason = failed.message;
      else {reason = "正在讀取房間原生幾何指紋"; refreshRestoredPins(key, bid);}
    }
    else if (!stale && anchor.kind === "collection" && (stamp.collectionId !== anchor.collectionId || stamp.planePin !== anchor.planePin || stamp.roomsPin !== anchor.roomsPin)) { stale = true; reason = "共享來源或房間清單已變更"; }
    candidateSession = {bid, stamp, anchor: structuredClone(anchor), ownerToken: token(), expired: false, nativePending,
      request: saved.analysis?.options || {}, runId: saved.draftId, draftId: saved.draftId, generation: ++candidateGeneration,
      candidates, total: saved.analysis?.total || candidates.length, complete: saved.analysis?.complete !== false, ignoredNested: saved.analysis?.ignoredNested || 0,
      analysis: saved.analysis, active: null, parked: true, stale, committing: false, reason};
  }
  function flushCandidates() {
    const s = candidateSession;
    if (!s) return;
    // R358-02: work from an earlier project or a pre-undo frame never writes into this one.
    if (!ownsSession(s)) {retireForeignSession(); return;}
    // Expired candidate work (R52) is no longer the source of the draft; the stored value stays.
    if (s.expired) return;
    if (s.active !== null) snapshotActive(s);
    writeSavedCandidates(s, {recordHistory: true});
  }
  function assertCandidates(s=candidateSession) {
    if(!s||s!==candidateSession||s.stale||s.nativePending||s.expired||!ownsSession(s)||!same(s.stamp,candidateStamp(s.bid)))throw Error('來源、房間或專案已變更，或原生指紋尚未確認；候選目前不可接受。');
    if(s.stamp.kind==='collection'&&!isHash(s.stamp.roomsPin))throw Error('房間原生幾何指紋尚未讀取，舊候選不可接受；請稍候重新操作。');
    W().assertEditable();return s;
  }
  function invalidateCandidates() {
    const s=candidateSession;if(!s||s.committing||s.stale)return;
    try{
      const next=candidateStamp(s.bid),before=s.stamp.owner,after=next.owner;
      if(!s.nativePending&&same(s.stamp,next)){assertCandidates(s);return;}
      // No active editor or transaction is rebased. Idle rows may wait for a
      // native report without confusing an empty cache with a changed domain.
      if(!s.expired&&s.active===null&&!lease&&!instance?.intent&&!instance?.busy&&!s.pendingAcceptance&&ownsSession(s)&&
        before.context===after.context&&before.frame===after.frame&&before.contextToken===after.contextToken&&
        s.anchor.kind==='collection'&&next.kind==='collection'&&next.collectionId===s.anchor.collectionId&&next.planePin===s.anchor.planePin){
        if(next.roomsPin===null){
          s.nativePending=true;
          const key=pinScope()+'\n'+s.bid,failed=nativeReadFailure?.key===key?nativeReadFailure:null;
          s.reason=failed&&failed.settled===nativeSettled?failed.message:'正在讀取房間原生幾何指紋';
          if(!failed||failed.settled!==nativeSettled)refreshRestoredPins(key,s.bid);
          return;
        }
        if(next.roomsPin===s.anchor.roomsPin){s.stamp=next;s.nativePending=false;s.reason='';return;}
      }
      assertCandidates(s);
    }catch(error){
      s.stale=true;s.nativePending=false;s.reason=error.message;
      // Never retire an unknown native owner. Its normal receipt recovery owns it.
      if(s.active!==null&&!lease&&!instance?.busy){instance?.cancel().catch(()=>{});activeBid=null;RoomOutlineWorkspace.reset();s.active=null;}
    }
  }
  window.addEventListener('project-info-changed',()=>{ if(!writingCandidates) invalidateCandidates(); });
  window.addEventListener('beforeunload',event=>{if(hasUnacceptedCandidates()){event.preventDefault();event.returnValue='';}});
  function hasUnacceptedCandidates() {
    const s=candidateSession;
    try{return !!s&&ownsSession(s)&&!s.expired&&s.candidates.some(c=>c.status!=='accepted');}catch(_){return false;}
  }
  function receiveCandidates(bid,result,request,expected) {
    const stamp=candidateStamp(bid),runId=crypto.randomUUID(),page=W().active(bid);
    if(!same(expected,stamp))throw Error('分析期間專案、房間或來源已變更，未採用晚到候選。');
    retireForeignSession();
    // I65: a new analysis never silently replaces a stored draft (any anchor); unsaved
    // in-memory work was already confirmed away when this analysis started.
    if(W().readFeatureAttachment(Drafts().KIND,token())!==null)throw Error('已有房間候選草稿；請先明選捨棄，再採用新的分析結果。');
    const anchor=anchorFromStamp(stamp);
    const members=stamp.kind==='page'?[]:state().collections.find(c=>c.id===stamp.collectionId).roomIds;
    const candidates=result.candidates.map(c=>{
      const estimated=c.points.map(p=>feUlImgToMm(page,...p)),integer=RoomOutline.integerProposal(estimated);
      const duplicate=stamp.kind!=='page'&&state().rooms.some(r=>members.includes(r.id)&&r.acceptedBasisRevision===stamp.plane.basisRevision&&oc.bmap[r.boundaryRef.id]?.length===1&&RoomOutline.canonicalLoop(oc.bmap[r.boundaryRef.id][0].verts)===RoomOutline.canonicalLoop(integer.points));
      const sameHost=stamp.kind==='page'&&oc.bmap[bid]?.length===1&&RoomOutline.canonicalLoop(oc.bmap[bid][0].verts)===RoomOutline.canonicalLoop(integer.points);
      return {id:runId+':'+c.key,sourcePoints:c.points,points:integer.points,deviation:integer.deviation,method:c.method,
        warnings:sameHost?[...c.warnings,'與目前描繪用面外環相同']:c.warnings,
        dimensions:[],rawInputs:{refRoomVertices:integer.points.map(p=>p.join(',')).join('\n'),refRoomLength:'',refRoomEdge:'0'},reviewed:false,revision:0,status:duplicate?'accepted':'pending',existing:duplicate};
    });
    const plane=stamp.plane||{coordinateSpace:page.sourceId&&integration.readSource(page.sourceId,token())?.meta.type==='application/pdf'?'pdf-page-viewport/1':'image-pixel/1',pageSize:[page.imgW,page.imgH]};
    candidateSession={bid,stamp,anchor,ownerToken:token(),expired:false,request:structuredClone(request),runId,draftId:crypto.randomUUID(),generation:++candidateGeneration,candidates,total:result.total,
      complete:result.complete,ignoredNested:result.ignoredNested,active:null,parked:false,stale:false,committing:false,
      analysis:{sourceId:page.sourceId,page:page.page,coordinateSpace:plane.coordinateSpace,pageSize:[...plane.pageSize],crop:[...page.crop],
        options:{mode:request.mode,minWidth:request.minWidth,minLength:request.minLength},barriers:request.barriers||[],
        analyzerRevision:Drafts().ANALYZER_REVISION,total:result.total,complete:!!result.complete,ignoredNested:result.ignoredNested||0}};
  }
  function snapshotActive(s=candidateSession) {
    if(!s||s.active===null)return;
    const value=RoomOutlineWorkspace.snapshot(),row=s.candidates[s.active];
    if(!value||value.candidateId!==row.id)throw Error('候選編輯器身份已變更，未覆寫其他候選。');
    const raw={...value.rawInputs};
    for(const id of ['refRoomVertices','refRoomLength','refRoomEdge']){const el=document.getElementById(id);if(el)raw[id]=el.value;}
    if(Object.values(raw).some(v=>v.length>20000))throw Error('候選輸入超過容量；請縮短後再暫停。');
    Object.assign(row,{points:value.points,dimensions:value.dimensions,rawInputs:raw,revision:value.revision,reviewed:false});
  }
  async function releaseCandidateEditor(s) {
    if(lease||instance?.busy||currentDialog||W().history.group)throw Error('房間預覽或交易尚未結束，請先確認、取消或恢復結果。');
    if(s.active===null&&instance?.intent)throw Error('其他房間草稿仍在編輯中，請先完成或取消。');
    if(s.active!==null){
      snapshotActive(s);const operation=controller(),index=s.active,generation=s.generation;
      await operation.cancel();
      if(s!==candidateSession||instance!==operation||s.active!==index||s.generation!==generation)throw Error('候選退休結果晚到，未清除新的編輯器。');
      activeBid=null;RoomOutlineWorkspace.reset();s.active=null;feSetTool('select');
    }
    s.generation=++candidateGeneration;
  }
  async function selectCandidate(index) {
    const s=assertCandidates(),row=s.candidates[index],actionStamp=s.stamp;
    if(!row||row.status==='accepted')throw Error('請選擇尚未接受的候選。');
    await releaseCandidateEditor(s);
    if(s.stamp!==actionStamp)throw Error('候選操作期間專案版本已變更，請重新選取。');
    assertCandidates(s);
    if(RoomOutlineWorkspace.hasWork||fe.draft.pts.length)throw Error('請先完成其他輪廓草稿。');
    const bid=oc.edit?.bid;
    Drafts().assertSelectable(draftFromSession(s), {fresh:!s.stale, reason:s.reason||'', note:''});
    if(s.stamp.kind==='page'){
      if(bid!==s.bid)throw Error('請回到原圖頁再選候選。');
      const page=W().active(bid),source=integration.readSource(page.sourceId,token());
      if(!source)throw Error('共享來源檔案已遺失。');
      const plane=S.fromPage(page,source.meta.type,crypto.randomUUID());
      controller().beginNewStaged({plane,collectionId:crypto.randomUUID(),display:{crop:[...page.crop],opacity:page.opacity,locked:!!page.locked},
        host:{boundaryId:bid,pageId:page.id,page:Drafts().pageFields(page)}});
    }else{
      const collection=collectionFor(bid);
      if(collection?.id!==s.stamp.collectionId)throw Error('請回到原共享來源再選候選。');
      controller().beginNew(collection.id);
    }
    activeBid=bid;s.active=index;s.parked=false;row.status='pending';
    feSetTool('redraw');RoomOutlineWorkspace.loadCandidate(bid,row);fiShowTab('underlay');
    if(innerWidth<=680)openPanel('right',document.getElementById('workspaceToggleRight'));
    document.getElementById('refRoomVertices')?.focus();
  }
  async function parkCandidates() {
    const s=assertCandidates(),actionStamp=s.stamp;
    if(s.active!==null)snapshotActive(s);
    Drafts().persistValue(draftFromSession(s));
    await releaseCandidateEditor(s);
    if(s.stamp!==actionStamp)throw Error('候選操作期間專案版本已變更，請重新暫停。');
    assertCandidates(s);
    writeSavedCandidates(s,{recordHistory:true});
    s.parked=true;renderFaceInspector();drawFaceEditor();setStatus('候選已暫停。未接受的房間候選已寫入專案，重新開啟後仍在；接受後才進入場景。');
  }
  // I65 discard: one metadata history step that removes the stored draft, then the work.
  async function discardDraft(s,removeStored=true) {
    if(s&&!ownsSession(s)){retireForeignSession();throw foreignSessionError();}
    if(s&&s.active!==null)await releaseCandidateEditor(s);
    if(lease||instance?.busy)throw Error('請先恢復房間交易。');
    if(removeStored){
      writingCandidates=true;
      try{W().setFeatureAttachment(Drafts().KIND,null,token(),{recordHistory:true});}
      finally{writingCandidates=false;}
    }
    if(!s||candidateSession===s){RoomOutlineWorkspace.reset();candidateSession=null;candidateGeneration++;}
  }
  async function discardCandidates() {
    const s=candidateSession;if(!s)return;
    try{await discardDraft(s);}
    finally{if(candidateSession!==s){renderFaceInspector();drawFaceEditor();}}
  }
  async function startCandidateAnalysis(bid,pane) {
    if(instance?.intent||lease||instance?.busy)throw Error('請先完成或取消房間草稿。');
    retireForeignSession();
    const analysisInput=()=>{
      const {owner,roomsPin,unknownNative,...input}=candidateStamp(bid);
      return {...input,owner:{context:owner.context,frame:owner.frame,contextToken:owner.contextToken}};
    };
    const ownerToken=token(),navigationBid=oc.edit?.bid,expectedInput=analysisInput();
    const assertAnalysisCurrent=(requirePane=false)=>{
      if(token()!==ownerToken||oc.edit?.bid!==navigationBid||!same(analysisInput(),expectedInput)||
        (requirePane&&(!pane.isConnected||pane!==document.getElementById('faceInspectorContent'))))
        throw Error('房間候選分析的專案、圖頁或工作區已變更；請從目前圖頁重新開始。');
    };
    // Read the referenced D3 fingerprints first: a failed read must leave any draft untouched.
    await readNativePins(bid);assertAnalysisCurrent(true);
    if(instance?.intent||lease||instance?.busy)throw Error('請先完成或取消房間草稿。');
    const s=ownsSession(candidateSession)?candidateSession:null,stored=W().readFeatureAttachment(Drafts().KIND,token());
    if(stored!==null){
      // I65: a stored draft (any anchor) is explicitly discarded first, as its own undoable step.
      if(!confirm('已有房間候選草稿。重新分析前須先捨棄它（捨棄可復原）；已接受的房間保留。要捨棄並重新分析嗎？'))return;
      await discardDraft(s,true);
    }else if(s&&!confirm('重新分析會放棄本分頁尚未接受的候選與修正；已接受房間保留。繼續嗎？'))return;
    // Discard can redraw this pane; retain its chosen options but recheck ownership and source.
    assertAnalysisCurrent();
    await RoomOutlineWorkspace.collect(bid,pane);
  }
  function candidatesHTML(bid) {
    const s=candidateSession;if(!s)return '';
    invalidateCandidates();
    const disabled=s.stale||s.nativePending||s.committing||!!lease||!!instance?.busy||!!currentDialog;
    return `<section id="roomCandidates"><p role="status">${s.nativePending?escape(s.reason):s.stale?'舊候選已失效，只能查看或放棄：'+escape(s.reason):s.parked?'已暫停。未接受的房間候選已寫入專案，重新開啟後仍在':`找到 ${s.total} 個可核對區域${s.complete?'':`，僅顯示前 12 個（未完整呈現）`}`}；來源取景 ${escape(s.stamp.crop.join(', '))}${s.ignoredNested?`；排除 ${s.ignoredNested} 個巢狀障礙內框`:''}</p>`+
      s.candidates.map((c,i)=>`<div class="ref-record" data-candidate-row="${i}"><span>候選 ${i+1} · ${c.existing?'與既有房間外環相同':c.status==='accepted'?'已建立':c.status==='excluded'?'已排除':s.active===i?'核對中':'待核對'}</span><button type="button" class="btn" style="min-height:44px" data-room-candidate="${i}"${disabled||c.status==='accepted'?' disabled':''}>${c.status==='excluded'?'恢復並核對':s.parked?'恢復核對':'選取核對'}</button>${c.status==='accepted'?'':`<button type="button" class="btn" style="min-height:44px" data-room-exclude="${i}"${disabled?' disabled':''}>排除</button>`}</div>`).join('')+
      `<div class="ref-actions"><button id="roomCandidatesPark" type="button" class="btn"${disabled?' disabled':''}>暫停候選，以便保存成果</button><button id="roomCandidatesDiscard" type="button" class="btn"${s.committing||lease?' disabled':''}>放棄剩餘候選</button></div></section>`;
  }
  function drawCandidates(root) {
    const s=candidateSession;if(!s||s.stale||s.nativePending||s.parked)return;
    if(s.stamp.kind==='page'?oc.edit?.bid!==s.bid:collectionFor(oc.edit?.bid)?.id!==s.stamp.collectionId)return;
    s.candidates.forEach((c,i)=>{
      if(c.status!=='pending'||s.active===i)return;
      el('polygon',{points:c.points.map(p=>p.join(',')).join(' '),fill:'rgba(22,150,130,.035)',stroke:'#169682','stroke-opacity':.4,'stroke-width':1/fe.zoom,'pointer-events':'none'},root);
      const p=c.points[0];el('text',{x:p[0]+6/fe.zoom,y:p[1]+16/fe.zoom,fill:'#169682','font-size':14/fe.zoom,'pointer-events':'none'},root).textContent=String(i+1);
    });
  }
  function paneHTML(bid) {
    if (!W().readFeatureAttachment || !integration) return "";
    restoreSavedCandidates(bid);
    const collection = collectionFor(bid), data = state();
    if (!collection) {
      const page = W().active(bid);
      if (!page?.calibration) return "";
      if (data.planes.some(item => item.sourceId === page.sourceId && item.page === page.page)) return `<p role="status">此圖頁已有共享來源。請從新房間進入同來源列表。</p>`;
      const busy = instance?.intent || RoomOutlineWorkspace.hasWork;
      return `<label>新增方式<select id="roomNewMethod"${busy ? " disabled" : ""}><option value="adopt"${zeroMode === "adopt" ? " selected" : ""}>把目前面設為第一個房間</option><option value="manual"${zeroMode === "manual" ? " selected" : ""}>人工描繪第一個房間</option><option value="candidates"${zeroMode === "candidates" ? " selected" : ""}>取得同頁候選</option></select></label><button type="button" id="roomNew" class="btn"${busy ? " disabled" : ""}>開始</button>` +
        candidatesHTML(bid) + (zeroMode === "candidates" || candidateSession && candidateSession.active !== null ? RoomOutlineWorkspace.paneHTML(bid, true) : "");
    }
    const current = roomForBoundary(bid), intent = instance?.intent;
    return `<details class="ref-section" open><summary>同來源房間（${collection.roomIds.length}）</summary>` +
      `<p role="status">${intent ? intent.roomId ? "正在編輯所選房間" : "正在新增房間 · 原房間保留" : "明選新增或編輯房間"}</p>` +
      `<label>新增方式<select id="roomNewMethod"${intent||RoomOutlineWorkspace.hasWork?' disabled':''}><option value="manual"${candidateMode==='manual'?' selected':''}>人工描繪</option><option value="candidates"${candidateMode==='candidates'?' selected':''}>取得同頁候選</option></select></label><button type="button" id="roomNew" class="btn"${intent||RoomOutlineWorkspace.hasWork ? " disabled" : ""}>${candidateMode==='manual'?'新增房間':'分析來源取景'}</button>` +
      candidatesHTML(bid)+(candidateMode==='candidates'||candidateSession&&candidateSession.active!==null?RoomOutlineWorkspace.paneHTML(bid,true):'')+
      collection.roomIds.map(id => {const room = data.rooms.find(r => r.id === id), unknown = room.reviewState === "needs-reassociation";
        return `<article class="ref-record" data-room-id="${room.id}"><strong>${escape(room.name)}</strong><span>邊界 ${room.boundaryRef.id} · ${{confirmed:"已核對", "needs-review":"基準或邊界變更 · 需複核", "needs-reassociation":"原邊界身份未知 · 需重新關聯"}[room.reviewState]}</span>` +
          `<button type="button" class="text-button" data-room-open="${room.id}"${unknown || intent ? " disabled" : ""}>${current.id === id ? "目前房間" : "查看"}</button>` +
          `<button type="button" class="text-button" data-room-edit="${room.id}"${unknown || intent ? " disabled" : ""}>編輯外環</button>` +
          `<button type="button" class="text-button" data-room-rename="${room.id}"${intent ? " disabled" : ""}>改名</button>` +
          `<button type="button" class="text-button" data-room-unlink="${room.id}"${intent ? " disabled" : ""}>解除列表關聯</button>` +
          (room.reviewState === "needs-review" ? `<button type="button" class="text-button" data-room-review="${room.id}"${intent ? " disabled" : ""}>已逐邊核對</button>` : "") + "</article>";
      }).join("") + historyHTML(data, collection.planeId, true) + "</details>";
  }
  function historyHTML(data, planeId, evidence = false) {
    const entries = (data.legacyHistory || []).filter(entry => entry.planeId === planeId), plane = data.planes.find(plane => plane.id === planeId);
    if (!entries.length && !evidence) return "";
    return `<details class="ref-section"${evidence ? ' id="refRecordDetails"' : ''}${entries.length ? ` data-room-source-history="${planeId}"` : ''}><summary>原頁歷史紀錄與核對（${entries.length}）</summary>` +
      (entries.length ? `<label>歷史來源<select data-room-history-entry>${entries.map((entry,index) => `<option value="${index}">原邊界 ${entry.boundaryId} · 第 ${plane.page} 頁</option>`).join("")}</select></label><div data-room-history-content></div>` : '') +
      (evidence ? '<div data-evidence-host></div>' : '') + '</details>';
  }
  function bindHistory(host) {
    const contextToken = token();
    for (const details of host.querySelectorAll("[data-room-source-history]")) {
      const planeId = details.dataset.roomSourceHistory, entries = (state().legacyHistory || []).filter(entry => entry.planeId === planeId);
      const show = () => {
        if (!details.open) return;
        if (token() !== contextToken) {details.querySelector("[data-room-history-content]").textContent = "來源歷史已過期，請重新開啟。";return;}
        const index = Number(details.querySelector("[data-room-history-entry]").value), entry = entries[index];
        const current = (state().legacyHistory || []).filter(entry => entry.planeId === planeId)[index];
        if (!entry || JSON.stringify(entry) !== JSON.stringify(current)) {details.querySelector("[data-room-history-content]").textContent = "來源歷史已變更，請重新開啟。";return;}
        const receipt = entry.reconstructionReview;
        details.querySelector("[data-room-history-content]").innerHTML = entry.records.map(record =>
          `<article class="ref-record"><strong>${escape(record.label || "未命名紀錄")}</strong><span>${record.value === null ? "待補" : escape(record.value) + " " + record.unit}</span>` +
          `<p>${escape(record.location)}${record.datum ? " · 基準：" + escape(record.datum) : ""}</p></article>`).join("") +
          (receipt ? `<p>原頁核對：${escape(receipt.confirmedAt)} · ${{manual:"人工逐邊", "pdf-vector":"PDF 線段", "image-lines":"圖片線段"}[receipt.method]}</p>` +
            receipt.warnings.map(warning => `<p>${escape(warning)}</p>`).join("") : "") +
          `<p role="note">原頁歷史保留供查閱；房間現況依目前共同基準重新核對。</p>`;
      };
      details.addEventListener("toggle", show);
      details.querySelector("[data-room-history-entry]").addEventListener("change", show);
    }
  }
  const safe = operation => async () => {try {await operation();} catch (error) {toast(error.message);}};
  function overviewHTML() {
    if (!integration || !W().readFeatureAttachment) return "";
    const data = state(); if (!data.collections.length) return "";
    const contextToken = token();
    if (overviewContextToken !== contextToken) {overviewContextToken = contextToken; overviewCollectionId = null;}
    const collection = data.collections.find(item => item.id === overviewCollectionId) || data.collections[0];
    overviewCollectionId = collection.id;
    const plane = data.planes.find(item => item.id === collection.planeId), rooms = data.rooms.filter(room => collection.roomIds.includes(room.id));
    const sourceLabel = item => {
      const sourcePlane = data.planes.find(plane => plane.id === item.planeId), source = integration.readSource(sourcePlane.sourceId, contextToken);
      return (source?.meta.name || "共享來源") + " · 第 " + sourcePlane.page + " 頁";
    };
    const disabled = instance?.intent || instance?.busy || lease || W().getModelOperationState().blocked;
    return `<details class="ref-section" data-room-source-overview><summary>${escape(sourceLabel(collection))} · ${rooms.length} 個房間</summary>` +
      `<label>共享來源<select data-room-source-collection${disabled ? " disabled" : ""}>${data.collections.map(item =>
        `<option value="${item.id}"${item.id === collection.id ? " selected" : ""}>${escape(sourceLabel(item))}</option>`).join("")}</select></label>` +
      `<p role="status">共同基準 ${plane.basisRevision} · ${rooms.filter(room => room.reviewState === "needs-reassociation").length} 個需重新關聯</p>` +
      `<label>房間<select data-room-source-room${disabled ? " disabled" : ""}><option value="">關聯新的房間</option>${rooms.map(room =>
        `<option value="${room.id}">${escape(room.name)} · ${room.reviewState === "needs-reassociation" ? "需重新關聯" : room.reviewState === "needs-review" ? "需複核" : "已核對"}</option>`).join("")}</select></label>` +
      `<label>既有邊界<select data-room-source-boundary${disabled ? " disabled" : ""}><option value="">明選已有邊界</option>${(oc.faces || []).filter(face => face.kind === "boundary").map(face =>
        `<option value="${face.id}">邊界 ${face.id}</option>`).join("")}</select></label>` +
      `<button type="button" class="btn" data-room-source-associate${disabled ? " disabled" : ""}>核對並關聯既有邊界</button>` + historyHTML(data, plane.id) + `</details>`;
  }
  function bindOverview(host) {
    bindHistory(host);
    const contextToken = token(), collectionId = overviewCollectionId;
    host.querySelector("[data-room-source-collection]")?.addEventListener("change", event => {
      overviewCollectionId = event.target.value; window.ProjectInfoUI?.render();
    });
    host.querySelector("[data-room-source-associate]")?.addEventListener("click", safe(async () => {
      if (token() !== contextToken) throw new Error("來源總覽已過期，請重新選擇。");
      if (RoomOutlineWorkspace.hasWork || fe.draft.pts.length || fe.ulCalib?.pts?.length) throw new Error("請先完成或取消目前輪廓或校準草稿。");
      const roomId = host.querySelector("[data-room-source-room]").value, boundaryId = Number(host.querySelector("[data-room-source-boundary]").value);
      if (!Number.isInteger(boundaryId) || boundaryId < 1) throw new Error("請明確選擇既有原生邊界。");
      const data = state(), collection = data.collections.find(item => item.id === collectionId);
      const room = roomId ? data.rooms.find(room => room.id === roomId && collection?.roomIds.includes(room.id)) : null;
      if (roomId && !room) throw new Error("所選房間已變更，請重新選擇。");
      const name = room ? room.name : prompt("房間名稱", "房間 " + boundaryId);
      if (name === null) return;
      if (!confirm("請確認已逐邊核對所選來源基準與邊界 " + boundaryId + " 的輪廓及尺寸，再關聯至「" + name + "」。")) return;
      const next = await controller().associate(collectionId, boundaryId, name, roomId || null);
      const associated = next.rooms.find(room => room.boundaryRef.id === boundaryId);
      await openRoom(associated.id);
      document.getElementById("projectInfoPanel")?.hidePopover();
    }));
  }
  function bindPane(pane, bid) {
    bindHistory(pane);
    const session=candidateSession,sessionGeneration=session?.generation;
    const candidateAction=fn=>safe(async()=>{
      if(!pane.isConnected||pane!==document.getElementById('faceInspectorContent')||session!==candidateSession||sessionGeneration!==candidateSession?.generation)return;
      await fn();
    });
    pane.querySelector('#roomNewMethod')?.addEventListener('change',candidateAction(()=>{
      const value=pane.querySelector('#roomNewMethod').value;
      if(!collectionFor(bid))zeroMode=value;else candidateMode=value;
      renderFaceInspector();
    }));
    for(const button of pane.querySelectorAll('[data-room-candidate]'))button.addEventListener('click',candidateAction(()=>selectCandidate(Number(button.dataset.roomCandidate))));
    for(const button of pane.querySelectorAll('[data-room-exclude]'))button.addEventListener('click',candidateAction(async()=>{
      const s=assertCandidates(),index=Number(button.dataset.roomExclude);
      if(s.active===index)await releaseCandidateEditor(s);
      s.candidates[index].status='excluded';renderFaceInspector();
    }));
    pane.querySelector('#roomCandidatesPark')?.addEventListener('click',candidateAction(parkCandidates));
    pane.querySelector('#roomCandidatesDiscard')?.addEventListener('click',candidateAction(discardCandidates));
    pane.querySelector("#roomNew")?.addEventListener("click", candidateAction(async()=>{
      if(!collectionFor(bid)){
        if(zeroMode==='adopt')return adoptCurrent(bid);
        if(zeroMode==='manual')return beginFirst(bid);
        return startCandidateAnalysis(bid,pane);
      }
      if(candidateMode==='manual')return beginNew(bid);
      return startCandidateAnalysis(bid,pane);
    }));
    for (const button of pane.querySelectorAll("[data-room-open]")) button.addEventListener("click", safe(() => openRoom(button.dataset.roomOpen)));
    for (const button of pane.querySelectorAll("[data-room-edit]")) button.addEventListener("click", safe(() => beginEdit(button.dataset.roomEdit)));
    for (const button of pane.querySelectorAll("[data-room-rename]")) button.addEventListener("click", safe(() => {
      const room = state().rooms.find(r => r.id === button.dataset.roomRename), name = prompt("房間名稱", room.name);
      if (name !== null) controller().rename(room.id, name); renderFaceInspector();
    }));
    for (const button of pane.querySelectorAll("[data-room-unlink]")) button.addEventListener("click", safe(async () => {
      if (!confirm("解除房間列表關聯；原生幾何保留。確定繼續嗎？")) return;
      controller().unlink(button.dataset.roomUnlink); W().sync(); renderFaceInspector(); drawFaceEditor();
    }));
    for (const button of pane.querySelectorAll("[data-room-review]")) button.addEventListener("click", safe(async () => {
      await controller().review(button.dataset.roomReview); renderFaceInspector();
    }));
  }
  function cleanDraft() {fe.draft = PolyDraft.createState(); fe.draftPreview = null; feSyncDraftMirror(); feLenShow(); drawFaceEditor();}
  async function adoptCurrent(bid) {
    const page = W().active(bid), stamp = W().getProjectState(), source = integration.readSource(page.sourceId, stamp.contextToken);
    const plane = S.fromPage(page, source.meta.type, crypto.randomUUID()), collectionId = crypto.randomUUID();
    const name = prompt("目前房間名稱", "房間 1");
    if (name === null) return;
    if (!name.trim() || name.trim().length > 200) throw new Error("請填寫房間名稱（最多 200 字）。");
    const native = await checked("boundary " + bid), pin = await R.boundaryPin(native);
    if (JSON.stringify(stamp) !== JSON.stringify(W().getProjectState()) || W().active(bid) !== page) throw new Error("來源關聯結果晚到，請重新操作。");
    await integration.adoptLegacySource({plane, collectionId, boundaryId: bid, page, roomId: crypto.randomUUID(), name: name.trim(), associationPin: pin, contextToken: stamp.contextToken});
    await prepareSharedPages(); renderFaceInspector();
  }
  async function beginFirst(bid) {
    if (RoomOutlineWorkspace.hasWork || fe.draft.pts.length) throw new Error("請先完成或取消目前外環草稿。");
    const page = W().active(bid);
    if (!page?.calibration) throw new Error("請先校準圖頁。");
    const source = integration.readSource(page.sourceId, token());
    if (!source) throw new Error("共享來源檔案已遺失。");
    const plane = S.fromPage(page, source.meta.type, crypto.randomUUID());
    controller().beginNewStaged({plane, collectionId: crypto.randomUUID(), display: {crop: [...page.crop], opacity: page.opacity, locked: !!page.locked},
      host: {boundaryId: bid, pageId: page.id, page: Drafts().pageFields(page)}});
    activeBid = bid; feSetTool("redraw"); fiShowTab("underlay");
    cleanDraft(); renderFaceInspector();
    setStatus("人工描繪第一個房間：確認後建立新邊界與共享來源；目前描繪用面保留、不關聯。");
  }
  async function beginNew(bid) {
    if (RoomOutlineWorkspace.hasWork || fe.draft.pts.length) throw new Error("請先完成或取消目前外環草稿。");
    const collection = collectionFor(bid); if (!collection) throw new Error("請先建立共享房間來源。");
    controller().beginNew(collection.id); activeBid = bid; feSetTool("redraw"); fiShowTab("underlay");
    cleanDraft(); renderFaceInspector(); setStatus("新增房間：逐點描繪外環，確認後建立獨立邊界；取消保留原房間。");
  }
  async function openRoom(roomId) {
    const contextToken = token(), room = state().rooms.find(r => r.id === roomId);
    if (!room || room.reviewState === "needs-reassociation") throw new Error("房間原生邊界需要重新關聯。");
    const pendingFocus = enterFocus("face", room.boundaryRef.id), focus = oc.focus;
    await pendingFocus;
    if (token() !== contextToken || oc.focus !== focus || focus?.t !== "face" || focus.id !== room.boundaryRef.id || oc.edit?.bid !== room.boundaryRef.id)
      throw new Error("房間開啟結果晚到，請重新選擇。");
    const current = state().rooms.find(r => r.id === roomId);
    if (!current || current.reviewState === "needs-reassociation" || current.boundaryRef.id !== room.boundaryRef.id) throw new Error("房間關聯已變更，請重新選擇。");
    fiShowTab("underlay");
  }
  async function beginEdit(roomId) {
    if (RoomOutlineWorkspace.hasWork || fe.draft.pts.length) throw new Error("請先完成或取消目前外環草稿。");
    await openRoom(roomId); const room = state().rooms.find(r => r.id === roomId), collection = collectionFor(room.boundaryRef.id);
    controller().beginEdit(collection.id, roomId); activeBid = room.boundaryRef.id; feSetTool("redraw"); cleanDraft(); renderFaceInspector();
  }
  async function commitDraft(pts) {
    const s=candidateSession,selected=s&&s.active!==null?s.candidates[s.active]:null;
    if(!selected)return commitRoomDraft(pts);
    assertCandidates(s);snapshotActive(s);
    const candidate=RoomOutlineWorkspace.beforeCommit();
    if(!candidate?.collectionCandidate||candidate.candidateId!==selected.id||instance?.intent?.roomId)throw Error('候選的新建意圖無法確認。');
    if(s.committing)throw Error('候選確認中，請等待原操作結果。');
    s.committing=true;s.pendingAcceptance=null;
    const index=s.active;
    try {
      const others=otherAttachments(),old=s.stamp,ok=await commitRoomDraft(pts);
      if(!ok){
        if(s!==candidateSession)return false;
        if(s.pendingAcceptance){
          // The grouped acceptance was written, but this caller cannot prove its outcome.
          s.pendingAcceptance=null;s.stale=true;s.expired=true;s.reason='房間交易結果未能由本操作確認；剩餘候選已失效。';
        }
        if(!lease){
          // Dismissing the name prompt returns before prepare/cancel. Retire
          // that real intent as well; clearing its UI alone leaves a blocker.
          if(instance?.intent)await releaseCandidateEditor(s);
          else {RoomOutlineWorkspace.reset();s.active=null;}
        }
        return false;
      }
      if(s!==candidateSession)return true;
      const next=candidateStamp(s.bid),oldIds=new Set(old.rooms.map(r=>r.id)),added=next.rooms.filter(r=>!oldIds.has(r.id));
      // Only a uniquely proven native + metadata success may renew the batch.
      if(old.kind==='page'){
        const oldPlaneIds=new Set((old.planes||[]).map(p=>p.id)),oldCollectionIds=new Set((old.collections||[]).map(c=>c.id));
        const addedPlanes=(next.planes||[]).filter(p=>!oldPlaneIds.has(p.id)),addedCollections=(next.collections||[]).filter(c=>!oldCollectionIds.has(c.id));
        if(added.length!==1||addedPlanes.length!==1||addedCollections.length!==1||addedCollections[0].planeId!==addedPlanes[0].id||!same(addedCollections[0].roomIds,[added[0].id])||
          added[0].boundaryRef.id===old.hostBoundaryId||next.rooms.some(r=>r.boundaryRef.id===old.hostBoundaryId)||
          Drafts().pagePin(W().active(old.hostBoundaryId))!==old.pagePin||old.owner.context!==next.owner.context||old.owner.frame!==next.owner.frame||old.owner.contextToken!==next.owner.contextToken||
          !old.rooms.every(r=>same(r,next.rooms.find(x=>x.id===r.id)))||!(old.planes||[]).every(p=>same(p,next.planes.find(x=>x.id===p.id))))
          throw Error('新增回執不能證明首房交易完整；剩餘候選已失效。');
      }else{
      const collection=next.collections.find(c=>c.id===old.collectionId),oldCollection=old.collections.find(c=>c.id===old.collectionId);
      if(added.length!==1||old.owner.context!==next.owner.context||old.owner.frame!==next.owner.frame||old.owner.contextToken!==next.owner.contextToken||!same(old.plane,next.plane)||!same(old.crop,next.crop)||
        !old.rooms.every(r=>same(r,next.rooms.find(x=>x.id===r.id)))||
        !old.geometry.every(g=>same(g,next.geometry.find(x=>x[0]===g[0])))||
        !old.collections.filter(c=>c.id!==old.collectionId).every(c=>same(c,next.collections.find(x=>x.id===c.id)))||
        !same(collection?.roomIds,[...oldCollection.roomIds,added[0].id]))throw Error('新增回執不能證明既有房間完整保留；剩餘候選已失效。');
      }
      const native=await checked('boundary '+added[0].boundaryRef.id);
      if(await R.boundaryPin(native)!==added[0].boundaryRef.associationPin)throw Error('新增房間原生身份不符；剩餘候選已失效。');
      if(s!==candidateSession||!same(next,candidateStamp(s.bid)))throw Error('新增回執核對晚到，未續用過期候選。');
      const grouped=s.pendingAcceptance;
      // R52: continue only if the stored draft equals the value written in the same group
      // (still no draft when the group removed it) and every other attachment is unchanged.
      if(!grouped||grouped.index!==index||!same(W().readFeatureAttachment(Drafts().KIND,s.ownerToken),grouped.value))
        throw Error('房間候選草稿不是同一交易剛寫入的值；剩餘候選已失效。');
      if(!same(state(),grouped.roomsValue))throw Error('房間來源附件不是同一交易剛寫入的值；剩餘候選已失效。');
      if(!same(otherAttachments(),others))throw Error('房間交易期間其他專案附件已變更；剩餘候選已失效。');
      if(next.kind!=='collection'||next.collectionId!==grouped.anchor.collectionId||next.plane.id!==grouped.anchor.planeId||
        next.planePin!==grouped.anchor.planePin||next.roomsPin!==grouped.anchor.roomsPin)throw Error('新增後的集合錨點無法由回執證明；剩餘候選已失效。');
      selected.status='accepted';selected.roomId=added[0].id;s.anchor=structuredClone(grouped.anchor);s.pendingAcceptance=null;
      s.active=null;s.stamp=next;s.generation=++candidateGeneration;
      for(const row of s.candidates)row.reviewed=false;
      RoomOutlineWorkspace.reset(false);renderFaceInspector();return true;
    } catch(error) {
      const pending=s.pendingAcceptance;s.pendingAcceptance=null;
      if(lease){
        // Unknown native outcome: receipt recovery settles it; the live rows cannot be trusted.
        if(pending){s.stale=true;s.expired=true;s.reason='房間交易結果未確認；剩餘候選已失效。';}
      }else if(instance?.intent){
        // Known rollback: World and the draft are restored, so the live row is not accepted either.
        if(pending)revertAcceptance(s,pending);
        RoomOutlineWorkspace.afterCommit(candidate,false);
      }else{
        s.stale=true;s.reason=error.message;s.active=null;RoomOutlineWorkspace.reset();
        // The room exists, but R52 could not prove continuation: the stored draft stays as written.
        if(pending)s.expired=true;
      }
      throw error;
    } finally {s.committing=false;if(s===candidateSession&&oc.edit)renderFaceInspector();}
  }
  function otherAttachments() {
    // R52: every project attachment except source rooms and the room-candidate draft.
    const F=typeof GeometryFeatureAttachments!=='undefined'?GeometryFeatureAttachments:null;
    const kinds=F?[F.GRID_KIND,F.Evidence?.KIND,F.CASE_KIND,F.Cutting?.KIND]:['grid-draft','evidence-links','rule-cases','cutting-settings'];
    return kinds.filter(Boolean).map(kind=>[kind,W().readFeatureAttachment(kind,token())]);
  }
  async function commitRoomDraft(pts) {
    const operation = controller(), intent = operation.intent;
    if (!intent || activeBid !== oc.edit?.bid) throw new Error("房間工作區已切換，請取消草稿。");
    const name = intent.room ? intent.room.name : prompt("新房間名稱", "房間 " + (state().rooms.length + 1));
    if (name === null) return false;
    const preview = await operation.prepare(pts, name);
    if (instance !== operation) return false;
    const dialog = document.createElement("dialog"); dialog.className = "reference-impact"; currentDialog = dialog;
    const title = document.createElement("h2"); title.textContent = intent.room ? "確認編輯「" + name + "」" : "確認新增「" + name + "」";
    const note = document.createElement("p"); note.textContent = intent.staged ? "建立共享來源（目前基準）與第一個房間；目前描繪用面保留、不關聯。" : intent.room ? "明確替換所選房間外環；既有孔與其他房間保持原狀。" : "建立新的獨立房間邊界；既有房間保持原狀。";
    dialog.append(title, note); appendGridDefinitionImpact(dialog, preview.review);
    const commands = document.createElement("code"); commands.textContent = preview.command; dialog.append(commands);
    const cancel = document.createElement("button"), apply = document.createElement("button");
    cancel.textContent = "取消，保留原狀"; cancel.id = "roomCancel"; apply.textContent = "確認套用"; apply.id = "roomConfirm";
    dialog.append(cancel, apply); document.body.append(dialog);
    const accepted = await new Promise(resolve => {
      let settled = false;
      const closeOwnedDialog = () => {
        dialog.close(); dialog.remove();
        if (currentDialog === dialog) {currentDialog = null; retireDialog = null;}
      };
      retireDialog = () => {
        if (settled) return;
        settled = true; cancel.disabled = apply.disabled = true;
        resolve(false); closeOwnedDialog();
      };
      const finish = async value => {if (settled) return; settled = true; cancel.disabled = apply.disabled = true;
        try {if (!value) await operation.cancel(); resolve(value);} catch (error) {toast(error.message); resolve(false);}
        finally {closeOwnedDialog();}};
      cancel.onclick = () => finish(false); apply.onclick = () => finish(true);
      dialog.addEventListener("cancel", event => {event.preventDefault(); finish(false);}); dialog.showModal(); cancel.focus();
    });
    if (instance !== operation) return false;
    if (!accepted) {activeBid = null; cleanDraft(); if (!lease) feSetTool("select"); renderFaceInspector(); return false;}
    const room = await operation.confirm();
    if (instance !== operation) return false;
    activeBid = null; cleanDraft();
    const settledGeneration = operation.generation, settledContext = token();
    const current = () => instance === operation && operation.generation === settledGeneration && token() === settledContext;
    await renderObjects(); if (!current()) return true;
    await prepareSharedPages(); if (!current()) return true;
    await enterFocus("face", room.boundaryId); if (!current()) return true;
    fiShowTab("underlay"); feSetTool("select");
    setStatus("✓ 房間「" + name + "」已保存為獨立邊界 · 可復原"); return true;
  }
  async function cancel() {
    if (currentDialog) {currentDialog.dispatchEvent(new Event("cancel", {cancelable: true})); return;}
    const operation = controller(); await operation.cancel();
    if (instance !== operation) return;
    if(candidateSession?.active!==null&&candidateSession){snapshotActive(candidateSession);candidateSession.active=null;candidateSession.generation=++candidateGeneration;RoomOutlineWorkspace.reset();}
    activeBid = null; cleanDraft(); feSetTool("select"); renderFaceInspector();
  }
  function changeView(bid, changes, calibration = undefined) {
    const room = roomForBoundary(bid); if (!room) return false;
    const data=state(),plane = S.planeForRoom(data, room.id), alignment = {...plane.alignment},display=S.displayForRoom(data,room.id);
    for (const [key, value] of Object.entries(changes)) {
      if (["x", "y", "mmPerPx", "rot"].includes(key)) alignment[key === "rot" ? "rotation" : key] = value;
      else if(['crop','opacity','locked'].includes(key))display[key]=value;
      else throw new Error('房間來源顯示欄位不支援。');
    }
    controller().sourceView(room.id, calibration === undefined ? plane.calibration : calibration, alignment,display);
    W().sync(); renderFaceInspector(); return true;
  }
  const changeBasis=changeView;
  function observeNativeResult(command, result) {
    if (!lease || !result.ok) return;
    if (command === ownedPreviewCommand && result.preview?.valid === true && Number.isInteger(result.preview.token) && result.preview.token > 0)
      ownedPreviewToken = result.preview.token;
    if (command === "line cancel-preview" || command === "line confirm " + ownedPreviewToken)
      ownedPreviewToken = null;
  }
  async function settleRecoveredTransaction() {
    if (lease && ownedPreviewToken !== null) {
      integration.assertTransaction(lease);
      await cancelOwnedCandidate();
    }
    recoveredTransaction();
  }
  function recoveredTransaction() {
    // A settled native receipt retires the whole room operation. Clear its
    // editor state while the owner lease still blocks unrelated mutations;
    // otherwise Finish could reinterpret a New-room outline as an old-room edit.
    const settledLease = lease, recoveringCandidate = !!candidateSession && candidateSession.active !== null;
    // R52: candidate work whose grouped acceptance write is unresolved is expired; the stored
    // draft (as settled by recovery) stays authoritative and is never overwritten by it.
    if(candidateSession?.pendingAcceptance)candidateSession.expired=true;
    if(candidateSession){candidateSession.stale=true;candidateSession.pendingAcceptance=null;candidateSession.reason='房間交易經回執恢復；請重新分析候選。已恢復的正式房間依專案現況保留。';candidateSession.active=null;candidateSession.generation=++candidateGeneration;}
    cleaningUI = true;
    try {
      retireDialog?.();
      if (currentDialog) {currentDialog.close(); currentDialog.remove(); currentDialog = null;}
      instance = null; activeBid = null; ownedPreviewToken = null; ownedPreviewCommand = null;
      fe.panHold = null; fe.newOutline = null;
      if(recoveringCandidate)RoomOutlineWorkspace.reset(false);
      cleanDraft(); feSetTool("select"); renderFaceInspector();
    } finally {cleaningUI = false;}
    if (settledLease) integration.endTransaction(settledLease);
    lease = null;
  }
  return {configure, beginNativeRequest, assertTransaction, paneHTML, bindPane, overviewHTML, bindOverview, sourcePage, prepareSharedPages, roomForBoundary, beginNew, beginEdit, commitDraft, cancel, changeView, changeBasis, observeNativeResult, settleRecoveredTransaction, recoveredTransaction,
    receiveCandidates,captureCandidateStamp:candidateStamp,parkCandidates,selectCandidate,drawCandidates,flushCandidates,
    get hasUnacceptedCandidates(){return hasUnacceptedCandidates();},
    candidateSnapshot:()=>candidateSession?structuredClone(candidateSession):null,
    get cleaningUI() {return cleaningUI;}, get dialogOpen() {return !!currentDialog?.open;},
    get hasWork() {return !!instance?.intent || !!lease;}, get busy() {return !!instance?.busy || !!lease;}, get transactionLease() {return lease;}, get controller() {return controller();}};
})();
window.RoomCollectionWorkspace = RoomCollectionWorkspace;
if (typeof ReferenceWorkspace !== "undefined" && ReferenceWorkspace.getRoomIntegration) RoomCollectionWorkspace.configure(ReferenceWorkspace.getRoomIntegration());
