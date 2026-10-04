/* Thin adapter for the existing reference/face workspace; shared owner wires hooks. */
const RoomCollectionWorkspace = (() => {
  "use strict";
  const S = GeometrySourcePlane, R = GeometryRoomCollection;
  const pages = new Map();
  let instance = null, activeBid = null, lease = null, ownedPreviewToken = null, currentDialog = null, retireDialog = null, integration = null, cleaningUI = false;
  const W = () => ReferenceWorkspace;
  const token = () => W().getProjectState().contextToken;
  const state = () => W().readFeatureAttachment("source-rooms", token()) || S.empty();
  const escape = value => W().escape(value);
  function ensureReady() {
    if (!W().readFeatureAttachment || !W().setFeatureAttachment || !integration) throw new Error("房間來源接線尚未啟用。");
  }
  function configure(adapter) {
    for (const name of ["readSource", "readIncarnation", "beginTransaction", "assertTransaction", "endTransaction", "groupOpen", "labelTransaction", "adoptLegacySource"])
      if (typeof adapter?.[name] !== "function") throw new Error("房間來源缺少 owner 接口：" + name);
    integration = adapter;
  }
  function request(command) { return apiRequest(command, lease); }
  function assertTransaction(ownerLease) {ensureReady(); return integration.assertTransaction(ownerLease);}
  async function checked(command) {
    const result = await request(command);
    if (!result.ok) throw Object.assign(new Error(result.error || "房間操作失敗。"), {transport: result.transport});
    return result;
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
        const result = await request("line preview " + command);
        if (!result.ok) {
          if (!result.transport) {integration.endTransaction(lease); lease = null;}
          throw Object.assign(new Error(result.error || "房間預覽失敗。"), {transport: result.transport});
        }
        ownedPreviewToken = result.preview?.token;
        return {ok: result.ok, ...result.preview};
      },
      cancelPreview: async previewToken => {
        // The workspace owns the only pending draft; callers cannot cancel a foreign token.
        if (!lease || ownedPreviewToken !== previewToken) throw new Error("房間預覽識別已變更，未取消其他工作的候選。");
        integration.assertTransaction(lease);
        await checked("line cancel-preview");
        ownedPreviewToken = null; integration.endTransaction(lease); lease = null;
      },
      changeMetadata: (next, {label, stamp}) => W().setFeatureAttachment("source-rooms", next, stamp.contextToken, {recordHistory: true, reason: label}),
      commitWithMetadata: async ({token: previewToken, boundaryId, label, assertCurrent, makeAttachment}) => {
        assertCurrent(); integration.assertTransaction(lease);
        if (ownedPreviewToken !== previewToken) throw new Error("房間預覽識別已變更。");
        let begun = false, unknown = false;
        try {
          assertCurrent(); await checked("line history-begin"); begun = true;
          assertCurrent(); await checked("line confirm " + previewToken);
          const native = await checked("boundary " + boundaryId);
          const attachment = await makeAttachment(native); integration.assertTransaction(lease);
          W().setFeatureAttachment("source-rooms", attachment, lease.contextToken, {recordHistory: false, roomLease: lease, reason: label});
          await checked("line history-end"); begun = false;
          integration.labelTransaction(lease, label);
          return {ok: true};
        } catch (error) {
          unknown = !!error.transport || connection.phase === "error";
          if (begun && !unknown && integration.groupOpen(lease)) {
            try {await checked("line history-abort");}
            catch (rollbackError) {
              // A rollback with no confirmed outcome still owns the native group.
              unknown = !!rollbackError.transport || connection.phase === "error";
              rollbackError.transport = unknown;
              throw rollbackError;
            }
          }
          error.transport = unknown;
          throw error;
        } finally {
          // Unknown transport outcomes retain the lease until the existing receipt recovery aborts/settles the group.
          if (!unknown) {integration.endTransaction(lease); lease = null; ownedPreviewToken = null;}
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
    const cache = pages.get(contextToken), old = cache.get(bid), signature = JSON.stringify(plane);
    if (old && old.planeId === plane.id) {
      if (old.signature !== signature) {Object.assign(old.page, S.materialize(plane, old.page)); old.signature = signature;}
      old.page.reviewRequired = room.reviewState !== "confirmed"; return old.page;
    }
    const page = S.materialize(plane); page.reviewRequired = room.reviewState !== "confirmed";
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
    }
    W().sync();
  }
  function collectionFor(bid) {
    const data = state(), room = data.rooms.find(r => r.boundaryRef.id === bid && r.reviewState !== "needs-reassociation");
    return room ? data.collections.find(c => c.roomIds.includes(room.id)) : null;
  }
  function paneHTML(bid) {
    if (!W().readFeatureAttachment || !integration) return "";
    const collection = collectionFor(bid), data = state();
    if (!collection) return W().active(bid)?.calibration ? '<p><button type="button" id="roomSourceCreate" class="btn">以此底圖連續新增房間</button></p>' : "";
    const current = roomForBoundary(bid), intent = instance?.intent;
    return `<details class="ref-section" open><summary>同來源房間（${collection.roomIds.length}）</summary>` +
      `<p role="status">${intent ? intent.roomId ? "正在編輯所選房間" : "正在新增房間 · 原房間保留" : "明選新增或編輯房間"}</p>` +
      `<button type="button" id="roomNew" class="btn"${intent ? " disabled" : ""}>新增房間</button>` +
      collection.roomIds.map(id => {const room = data.rooms.find(r => r.id === id), unknown = room.reviewState === "needs-reassociation";
        return `<article class="ref-record" data-room-id="${room.id}"><strong>${escape(room.name)}</strong><span>邊界 ${room.boundaryRef.id} · ${{confirmed:"已核對", "needs-review":"基準或邊界變更 · 需複核", "needs-reassociation":"原邊界身份未知 · 需重新關聯"}[room.reviewState]}</span>` +
          `<button type="button" class="text-button" data-room-open="${room.id}"${unknown || intent ? " disabled" : ""}>${current.id === id ? "目前房間" : "查看"}</button>` +
          `<button type="button" class="text-button" data-room-edit="${room.id}"${unknown || intent ? " disabled" : ""}>編輯外環</button>` +
          `<button type="button" class="text-button" data-room-rename="${room.id}"${intent ? " disabled" : ""}>改名</button>` +
          `<button type="button" class="text-button" data-room-unlink="${room.id}"${intent ? " disabled" : ""}>解除列表關聯</button>` +
          (room.reviewState === "needs-review" ? `<button type="button" class="text-button" data-room-review="${room.id}"${intent ? " disabled" : ""}>已逐邊核對</button>` : "") + "</article>";
      }).join("") + "</details>";
  }
  const safe = operation => async () => {try {await operation();} catch (error) {toast(error.message);}};
  function bindPane(pane, bid) {
    pane.querySelector("#roomSourceCreate")?.addEventListener("click", safe(async () => {
      const page = W().active(bid), stamp = W().getProjectState(), source = integration.readSource(page.sourceId, stamp.contextToken);
      const plane = S.fromPage(page, source.meta.type, crypto.randomUUID()), collectionId = crypto.randomUUID();
      // The existing face is deliberately associated only after the user explicitly chooses this action.
      const name = prompt("目前房間名稱", "房間 1");
      if (name === null) return;
      if (!name.trim() || name.trim().length > 200) throw new Error("請填寫房間名稱（最多 200 字）。");
      const native = await checked("boundary " + bid), pin = await R.boundaryPin(native);
      if (JSON.stringify(stamp) !== JSON.stringify(W().getProjectState()) || W().active(bid) !== page) throw new Error("來源關聯結果晚到，請重新操作。");
      // The shared owner atomically adopts this explicit selection, preserves
      // source records, and removes the old independent basis from serialization.
      await integration.adoptLegacySource({plane, collectionId, boundaryId: bid, page, roomId: crypto.randomUUID(), name: name.trim(), associationPin: pin, contextToken: stamp.contextToken});
      await prepareSharedPages(); renderFaceInspector();
    }));
    pane.querySelector("#roomNew")?.addEventListener("click", safe(() => beginNew(bid)));
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
  async function beginNew(bid) {
    if (RoomOutlineWorkspace.hasWork || fe.draft.pts.length) throw new Error("請先完成或取消目前外環草稿。");
    const collection = collectionFor(bid); if (!collection) throw new Error("請先建立共享房間來源。");
    controller().beginNew(collection.id); activeBid = bid; feSetTool("redraw"); fiShowTab("underlay");
    cleanDraft(); renderFaceInspector(); setStatus("新增房間：逐點描繪外環，確認後建立獨立邊界；取消保留原房間。");
  }
  async function openRoom(roomId) {
    const room = state().rooms.find(r => r.id === roomId);
    if (!room || room.reviewState === "needs-reassociation") throw new Error("房間原生邊界需要重新關聯。");
    await prepareSharedPages(); await enterFocus("face", room.boundaryRef.id); fiShowTab("underlay");
  }
  async function beginEdit(roomId) {
    if (RoomOutlineWorkspace.hasWork || fe.draft.pts.length) throw new Error("請先完成或取消目前外環草稿。");
    await openRoom(roomId); const room = state().rooms.find(r => r.id === roomId), collection = collectionFor(room.boundaryRef.id);
    controller().beginEdit(collection.id, roomId); activeBid = room.boundaryRef.id; feSetTool("redraw"); cleanDraft(); renderFaceInspector();
  }
  async function commitDraft(pts) {
    const operation = controller(), intent = operation.intent;
    if (!intent || activeBid !== oc.edit?.bid) throw new Error("房間工作區已切換，請取消草稿。");
    const name = intent.room ? intent.room.name : prompt("新房間名稱", "房間 " + (state().rooms.length + 1));
    if (name === null) return false;
    const preview = await operation.prepare(pts, name);
    if (instance !== operation) return false;
    const dialog = document.createElement("dialog"); dialog.className = "reference-impact"; currentDialog = dialog;
    const title = document.createElement("h2"); title.textContent = intent.room ? "確認編輯「" + name + "」" : "確認新增「" + name + "」";
    const note = document.createElement("p"); note.textContent = intent.room ? "明確替換所選房間外環；既有孔與其他房間保持原狀。" : "建立新的獨立房間邊界；既有房間保持原狀。";
    dialog.append(title, note); appendGridDefinitionImpact(dialog, preview.review);
    const commands = document.createElement("code"); commands.textContent = preview.command; dialog.append(commands);
    const cancel = document.createElement("button"), apply = document.createElement("button");
    cancel.textContent = "取消，保留原狀"; apply.textContent = "確認套用"; apply.id = "roomConfirm";
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
    activeBid = null; cleanDraft(); feSetTool("select"); renderFaceInspector();
  }
  function changeBasis(bid, changes, calibration = undefined) {
    const room = roomForBoundary(bid); if (!room) return false;
    const plane = S.planeForRoom(state(), room.id), alignment = {...plane.alignment};
    for (const [key, value] of Object.entries(changes)) if (["x", "y", "mmPerPx", "rot"].includes(key)) alignment[key === "rot" ? "rotation" : key] = value;
    controller().basis(plane.id, calibration === undefined ? plane.calibration : calibration, alignment);
    W().sync(); renderFaceInspector(); return true;
  }
  function recoveredTransaction() {
    // A settled native receipt retires the whole room operation. Clear its
    // editor state while the owner lease still blocks unrelated mutations;
    // otherwise Finish could reinterpret a New-room outline as an old-room edit.
    const settledLease = lease;
    cleaningUI = true;
    try {
      retireDialog?.();
      if (currentDialog) {currentDialog.close(); currentDialog.remove(); currentDialog = null;}
      instance = null; activeBid = null; ownedPreviewToken = null;
      fe.panHold = null; fe.newOutline = null;
      cleanDraft(); feSetTool("select"); renderFaceInspector();
    } finally {cleaningUI = false;}
    if (settledLease) integration.endTransaction(settledLease);
    lease = null;
  }
  return {configure, assertTransaction, paneHTML, bindPane, sourcePage, prepareSharedPages, roomForBoundary, beginNew, beginEdit, commitDraft, cancel, changeBasis, recoveredTransaction,
    get cleaningUI() {return cleaningUI;}, get dialogOpen() {return !!currentDialog?.open;},
    get hasWork() {return !!instance?.intent || !!lease;}, get busy() {return !!instance?.busy || !!lease;}, get transactionLease() {return lease;}, get controller() {return controller();}};
})();
window.RoomCollectionWorkspace = RoomCollectionWorkspace;
if (typeof ReferenceWorkspace !== "undefined" && ReferenceWorkspace.getRoomIntegration) RoomCollectionWorkspace.configure(ReferenceWorkspace.getRoomIntegration());
