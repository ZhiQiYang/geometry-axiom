/* Thin adapter for the existing reference/face workspace; shared owner wires hooks. */
const RoomCollectionWorkspace = (() => {
  "use strict";
  const S = GeometrySourcePlane, R = GeometryRoomCollection;
  const pages = new Map(),renders=new Map();
  let overviewCollectionId = null, overviewContextToken = null;
  let candidateSession = null, candidateGeneration = 0, candidateMode = 'manual', zeroMode = 'adopt';
  let writingCandidates = false;
  let instance = null, activeBid = null, lease = null, ownedPreviewToken = null, ownedPreviewCommand = null, currentDialog = null, retireDialog = null, integration = null, cleaningUI = false;
  const W = () => ReferenceWorkspace;
  const token = () => W().getProjectState().contextToken;
  const state = () => W().readFeatureAttachment("source-rooms", token()) || S.empty();
  const escape = value => W().escape(value);
  function ensureReady() {
    if (!W().readFeatureAttachment || !W().setFeatureAttachment || !integration) throw new Error("房間來源接線尚未啟用。");
  }
  function configure(adapter) {
    for (const name of ["readSource", "readIncarnation", "beginTransaction", "assertTransaction", "endTransaction", "preflightAttachment", "groupOpen", "labelTransaction", "adoptLegacySource"])
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
  function collectionRoomsPin(data, collection) {
    return Drafts().roomsPin(collection.roomIds.map(id => {
      const room = data.rooms.find(item => item.id === id);
      return {id: room.id, boundaryRef: {id: room.boundaryRef.id, geometryFingerprint: room.boundaryRef.associationPin || null},
        acceptedBasisRevision: room.acceptedBasisRevision, reviewState: room.reviewState};
    }));
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
      const plane = data.planes.find(entry => entry.id === covering.planeId);
      return {...base, kind: "collection", collectionId: covering.id, plane: structuredClone(plane), planePin: D.planePin(plane),
        roomsPin: collectionRoomsPin(data, covering),
        geometry: structuredClone(data.rooms.map(room => [room.boundaryRef.id, integration.readIncarnation(room.boundaryRef.id, token()), oc.bmap[room.boundaryRef.id]]))};
    }
    return {...base, kind: "page", bid, pageId: page.id, pagePin: D.pagePin(page), hostBoundaryId: bid,
      geometry: structuredClone([[bid, integration.readIncarnation(bid, token()), oc.bmap[bid]]])};
  }
  function draftFromSession(s) {
    const anchor = s.stamp.kind === "page"
      ? {kind: "page", boundaryId: s.stamp.hostBoundaryId, pageId: s.stamp.pageId, pagePin: s.stamp.pagePin}
      : {kind: "collection", collectionId: s.stamp.collectionId, planeId: s.stamp.plane.id, planePin: s.stamp.planePin, roomsPin: s.stamp.roomsPin};
    return {schema: Drafts().SCHEMA, draftId: s.draftId, anchor, analysis: s.analysis, rows: Drafts().rowsFromLive(s.candidates)};
  }
  function writeSavedCandidates(s, options) {
    const value = Drafts().persistValue(draftFromSession(s));
    writingCandidates = true;
    try {
      W().setFeatureAttachment(Drafts().KIND, value, options.contextToken || token(), options);
      if (s === candidateSession && !s.stale) {
        try { s.stamp = candidateStamp(s.bid); } catch (error) { s.stale = true; s.reason = error.message; }
      }
    } finally { writingCandidates = false; }
  }
  function acceptCandidateRow(payload) {
    const s = candidateSession;
    if (!s || s.active === null) return;
    const row = s.candidates[s.active], previousStatus = row.status, previousRoom = row.roomId;
    row.status = "accepted"; row.roomId = payload.roomId; row.reviewed = false;
    try { writeSavedCandidates(s, {recordHistory: false, roomLease: lease, contextToken: lease.contextToken}); }
    catch (error) {
      row.status = previousStatus;
      if (previousRoom === undefined) delete row.roomId; else row.roomId = previousRoom;
      throw error;
    }
  }
  function restoreSavedCandidates(bid) {
    if (candidateSession || !W().readFeatureAttachment || !integration) return;
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
    let stamp, stale = false, reason = "";
    try { stamp = candidateStamp(bid); }
    catch (error) { stale = true; reason = error.message; stamp = {kind: anchor.kind, owner: {}, crop: saved.analysis?.crop || [], rooms: [], collections: [], planes: []}; }
    if (!stale && anchor.kind === "page" && (stamp.kind !== "page" || stamp.pagePin !== anchor.pagePin || stamp.pageId !== anchor.pageId)) { stale = true; reason = "圖頁已變更"; }
    if (!stale && anchor.kind === "collection" && (stamp.collectionId !== anchor.collectionId || stamp.planePin !== anchor.planePin || stamp.roomsPin !== anchor.roomsPin)) { stale = true; reason = "共享來源或房間清單已變更"; }
    candidateSession = {bid, stamp, request: saved.analysis?.options || {}, runId: saved.draftId, draftId: saved.draftId, generation: ++candidateGeneration,
      candidates, total: saved.analysis?.total || candidates.length, complete: saved.analysis?.complete !== false, ignoredNested: saved.analysis?.ignoredNested || 0,
      analysis: saved.analysis, active: null, parked: true, stale, committing: false, reason};
  }
  function flushCandidates() {
    if (!candidateSession) return;
    if (candidateSession.active !== null) snapshotActive(candidateSession);
    writeSavedCandidates(candidateSession, {recordHistory: true});
  }
  function assertCandidates(s=candidateSession) {
    if(!s||s!==candidateSession||s.stale||!same(s.stamp,candidateStamp(s.bid)))throw Error('來源、房間或專案已變更，舊候選不可接受；請重新取得。');
    W().assertEditable();return s;
  }
  function invalidateCandidates() {
    const s=candidateSession;if(!s||s.committing||s.stale)return;
    try{assertCandidates(s);}catch(error){
      s.stale=true;s.reason=error.message;
      // Never retire an unknown native owner. Its normal receipt recovery owns it.
      if(s.active!==null&&!lease&&!instance?.busy){instance?.cancel().catch(()=>{});activeBid=null;RoomOutlineWorkspace.reset();s.active=null;}
    }
  }
  window.addEventListener('project-info-changed',()=>{ if(!writingCandidates) invalidateCandidates(); });
  window.addEventListener('beforeunload',event=>{if(candidateSession?.candidates.some(c=>c.status!=='accepted')){event.preventDefault();event.returnValue='';}});
  function receiveCandidates(bid,result,request,expected) {
    const stamp=candidateStamp(bid),runId=crypto.randomUUID(),page=W().active(bid);
    if(!same(expected,stamp))throw Error('分析期間專案、房間或來源已變更，未採用晚到候選。');
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
    candidateSession={bid,stamp,request:structuredClone(request),runId,draftId:crypto.randomUUID(),generation:++candidateGeneration,candidates,total:result.total,
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
    const s=assertCandidates(),row=s.candidates[index];
    if(!row||row.status==='accepted')throw Error('請選擇尚未接受的候選。');
    await releaseCandidateEditor(s);assertCandidates(s);
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
    const s=assertCandidates();
    if(s.active!==null)snapshotActive(s);
    Drafts().persistValue(draftFromSession(s));
    await releaseCandidateEditor(s);assertCandidates(s);
    writeSavedCandidates(s,{recordHistory:true});
    s.parked=true;renderFaceInspector();drawFaceEditor();setStatus('候選已暫停。未接受的房間候選已寫入專案，重新開啟後仍在；接受後才進入場景。');
  }
  async function discardCandidates() {
    const s=candidateSession;if(!s)return;
    if(s.active!==null)await releaseCandidateEditor(s);
    if(lease||instance?.busy)throw Error('請先恢復房間交易。');
    writingCandidates=true;
    try{W().setFeatureAttachment(Drafts().KIND,null,token(),{recordHistory:true});}
    finally{writingCandidates=false;}
    RoomOutlineWorkspace.reset();candidateSession=null;candidateGeneration++;renderFaceInspector();drawFaceEditor();
  }
  function candidatesHTML(bid) {
    const s=candidateSession;if(!s)return '';
    invalidateCandidates();
    const disabled=s.stale||s.committing||!!lease||!!instance?.busy||!!currentDialog;
    return `<section id="roomCandidates"><p role="status">${s.stale?'舊候選已失效，只能查看或放棄：'+escape(s.reason):s.parked?'已暫停。未接受的房間候選已寫入專案，重新開啟後仍在':`找到 ${s.total} 個可核對區域${s.complete?'':`，僅顯示前 12 個（未完整呈現）`}`}；來源取景 ${escape(s.stamp.crop.join(', '))}${s.ignoredNested?`；排除 ${s.ignoredNested} 個巢狀障礙內框`:''}</p>`+
      s.candidates.map((c,i)=>`<div class="ref-record" data-candidate-row="${i}"><span>候選 ${i+1} · ${c.existing?'與既有房間外環相同':c.status==='accepted'?'已建立':c.status==='excluded'?'已排除':s.active===i?'核對中':'待核對'}</span><button type="button" class="btn" style="min-height:44px" data-room-candidate="${i}"${disabled||c.status==='accepted'?' disabled':''}>${c.status==='excluded'?'恢復並核對':s.parked?'恢復核對':'選取核對'}</button>${c.status==='accepted'?'':`<button type="button" class="btn" style="min-height:44px" data-room-exclude="${i}"${disabled?' disabled':''}>排除</button>`}</div>`).join('')+
      `<div class="ref-actions"><button id="roomCandidatesPark" type="button" class="btn"${disabled?' disabled':''}>暫停候選，以便保存成果</button><button id="roomCandidatesDiscard" type="button" class="btn"${s.committing||lease?' disabled':''}>放棄剩餘候選</button></div></section>`;
  }
  function drawCandidates(root) {
    const s=candidateSession;if(!s||s.stale||s.parked)return;
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
        if(candidateSession&&!confirm('重新分析會放棄本分頁尚未接受的候選與修正；已接受房間保留。繼續嗎？'))return;
        if(instance?.intent||lease||instance?.busy)throw Error('請先完成或取消房間草稿。');
        await RoomOutlineWorkspace.collect(bid,pane);return;
      }
      if(candidateMode==='manual')return beginNew(bid);
      if(candidateSession&&!confirm('重新分析會放棄本分頁尚未接受的候選與修正；已接受房間保留。繼續嗎？'))return;
      if(instance?.intent||lease||instance?.busy)throw Error('請先完成或取消房間草稿。');
      await RoomOutlineWorkspace.collect(bid,pane);
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
    s.committing=true;
    try {
      const old=s.stamp,ok=await commitRoomDraft(pts);
      if(!ok){
        if(s!==candidateSession)return false;
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
      selected.status='accepted';selected.roomId=added[0].id;s.active=null;s.stamp=next;s.generation=++candidateGeneration;
      for(const row of s.candidates)row.reviewed=false;
      RoomOutlineWorkspace.reset(false);renderFaceInspector();return true;
    } catch(error) {
      if(!lease&&!instance?.intent){s.stale=true;s.reason=error.message;s.active=null;RoomOutlineWorkspace.reset();}
      else if(!lease)RoomOutlineWorkspace.afterCommit(candidate,false);
      throw error;
    } finally {s.committing=false;if(s===candidateSession&&oc.edit)renderFaceInspector();}
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
    if(candidateSession){candidateSession.stale=true;candidateSession.reason='房間交易經回執恢復；請重新分析候選。已恢復的正式房間依專案現況保留。';candidateSession.active=null;candidateSession.generation=++candidateGeneration;}
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
  return {configure, assertTransaction, paneHTML, bindPane, overviewHTML, bindOverview, sourcePage, prepareSharedPages, roomForBoundary, beginNew, beginEdit, commitDraft, cancel, changeView, changeBasis, observeNativeResult, settleRecoveredTransaction, recoveredTransaction,
    receiveCandidates,captureCandidateStamp:candidateStamp,parkCandidates,selectCandidate,drawCandidates,flushCandidates,
    get hasUnacceptedCandidates(){return !!candidateSession?.candidates.some(c=>c.status!=='accepted');},
    candidateSnapshot:()=>candidateSession?structuredClone(candidateSession):null,
    get cleaningUI() {return cleaningUI;}, get dialogOpen() {return !!currentDialog?.open;},
    get hasWork() {return !!instance?.intent || !!lease;}, get busy() {return !!instance?.busy || !!lease;}, get transactionLease() {return lease;}, get controller() {return controller();}};
})();
window.RoomCollectionWorkspace = RoomCollectionWorkspace;
if (typeof ReferenceWorkspace !== "undefined" && ReferenceWorkspace.getRoomIntegration) RoomCollectionWorkspace.configure(ReferenceWorkspace.getRoomIntegration());
