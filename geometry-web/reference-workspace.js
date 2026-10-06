/* GEO-198: references are optional presentation/provenance, not a geometry model. */
"use strict";
const ReferenceWorkspace = (() => {
  const P = GeometryProject, uuid = () => crypto.randomUUID();
  const escape = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));
  const fresh = () => ({ id: uuid(), name: "未命名專案", sources: new Map(), groups: new Map(), models: [], modelsDirty: false,
    reconstructionReviews: new Map(), faceProjections: new Map(), faceProjectionsDirty: false, engineeringDrafts: [], assemblyDrafts: [], featureAttachments: [], scenarioCatalog:null, pending: new Set(), dirty: false,
    provenance:{kind:"server",label:"服務目前保留的場景（來源未確認）",openedAt:null,lastSavedAt:null,lastDownloadAt:null} });
  const history = new P.ContextHistory(fresh);
  const revisions = new WeakMap(), selections = new WeakMap(), contextTokens = new WeakMap();
  const modelOperationIdentities = new WeakMap();
  let pdfLib, modal = null, busy = false, busyLabel = "", busyShort = "處理中", sequence = 0, pendingLoad = null;
  let importRenderingContext = null;
  let assemblyConfirmation = null, preparingSceneLoad = false, sceneTransaction = null;
  let roomTransaction = null;
  const featureConfirmations=new Map();
  let presentedModelContext = null, presentedModels = null;
  let presentedProjectionContext = null, presentedProjections = null;
  let presentedDraftContext = null, presentedDrafts = null;
  let recovery = {state:"pending",message:"尚未檢查本分頁的恢復資料。"};
  let recoveryKey = null, recoveryDB = null, recoveryTimer = null, recoveryWriting = false, recoveryAgain = false, recoveryReady = false;
  let recoveryFinishReceipt = null;
  let releaseRecoveryLock = null, recoveryAttempted = false;
  let contextConflict = false, externalEpoch = 0;
  let editorLease = "unchecked", editorLeaseSession = null;
  let nativeRevision = null, nativeSession = null, nativePending = 0;
  const scenarioContext = () => window.GeometryNativeContext?.scenario || null;
  let scenarioBootstrap = "blocked", scenarioInitializationAttempted = false, scenarioInitializationPermit = null;
  let scenarioFreeze = null, lastScenarioRelease = null;
  const E = P.Features.Evidence, preparedReferences = new WeakMap();
  function observeNativeRevision(result) {
    const session = connection.session || "";
    if (session !== nativeSession) {nativeSession = session; nativeRevision = null;}
    if (Number.isSafeInteger(result?.revision)) nativeRevision = Math.max(nativeRevision ?? 0, result.revision);
  }
  function beginNativeOperation(command) {
    if (!/^(line |drag |reset$|default$|undo$|redo$|loadfile |engineering-confirm |assembly-confirm )/.test(command)) return null;
    nativePending++;
    let ended = false;
    return () => {if (!ended) {ended = true; nativePending--;}};
  }
  function getEvidenceState() {
    const p = getProjectState(), operation = getModelOperationState();
    return {projectScope:p.id,contextToken:p.contextToken,revision:p.revision,
      nativeRevision:nativeSession === (connection.session || "") ? nativeRevision : null,
      session:connection.session || "",undo:operation.undo,redo:operation.redo,
      blocked:operation.blocked || nativePending > 0 || connection.phase !== "ready"};
  }
  const recoveryPeer=uuid();
  const recoveryChannel=typeof BroadcastChannel!=="undefined"?new BroadcastChannel("geometry-canvas-project-recovery-v1"):null;
  if(recoveryChannel)recoveryChannel.onmessage=event=>{
    if(event.data?.peer===recoveryPeer || typeof connection==="undefined" || event.data?.session!==connection.session)return;
    recoveryReady=false;externalEpoch++;
    revisions.set(context(),revision(context())+1);
    if(editorLease==="readonly" || editorLease==="unavailable"){
      recoveryMessage("readonly","編輯分頁已更新服務中的工作內容。本分頁仍僅供查看；請關閉原編輯分頁，再按「重新連接此工作」。接管時會重新核對來源，不沿用目前畫面的附件關聯。");return;
    }
    contextConflict=true;
    recoveryMessage("external","另一個分頁已修改服務中的場景，本分頁已暫停編輯、保存及恢復資料更新。請開啟正確專案或建立新專案，避免混用不同專案的附件。");
  };
  function notifySceneChange(){recoveryChannel?.postMessage({peer:recoveryPeer,session:typeof connection!=="undefined"?connection.session:null});}
  function assertConfirmationIdle(){
    if(assemblyConfirmation)throw new Error((assemblyConfirmation.featureCommand?'網格變更':'組構')+"確認結果尚未取得，請先等候結果或重新連線，再編輯或切換專案。");
  }
  function assertAssemblyIdle(){assertConfirmationIdle();if(roomTransaction)throw new Error("房間操作尚未確認，請先確認、取消或恢復結果。");}
  function assertEditorLease(){
    if(editorLease==="readonly" || editorLease==="unavailable")throw new Error("另一個分頁正在編輯這份工作，或瀏覽器無法確認編輯權限。本分頁僅供查看；請關閉原編輯分頁，再從專案資訊重新連接。");
    if(editorLeaseSession && connection.session!==editorLeaseSession)throw new Error("服務工作階段已變更，請重新連接後再編輯。");
    if(scenarioContext() && scenarioBootstrap!=="ready" && !scenarioInitializationPermit)
      throw new Error("這份試改尚未取得可核對的完整資料，原生內容已保留；不能重新匯入舊方案覆蓋它。");
  }
  function assertWritableLease(){assertAssemblyIdle();assertEditorLease();}
  function assertEditable(transactionOwner=null){assertWritableLease();if((sceneTransaction&&sceneTransaction!==transactionOwner)||preparingSceneLoad||pendingLoad)throw new Error("場景載入結果尚未確認，請先等候結果或重新連線，再編輯或復原。");if(contextConflict)throw new Error("另一個分頁已變更目前場景。請先開啟正確的 .gcanvas 專案或建立新專案，再編輯或保存。");}
  function beginSceneTransaction(){assertWritableLease();if(sceneTransaction||preparingSceneLoad||pendingLoad)throw new Error("請先確認上一筆場景載入結果再開啟。");return sceneTransaction={};}
  function finishSceneTransaction(owner){if(sceneTransaction===owner){sceneTransaction=null;schedulePresentation();}}
  const context = () => history.frame.context;
  // The native commit and its local history observation must finish before
  // another project or mutation can become the current history frame.
  function beginAssemblyConfirmation(){
    assertEditable();
    if(busy || oc.busy || preparingSceneLoad || pendingLoad || history.group)throw new Error("請先完成目前操作，再確認組構變更。");
    assemblyConfirmation={context:context(),frame:history.frame};schedulePresentation();return assemblyConfirmation;
  }
  function assemblyConfirmationCurrent(stamp){return context()===stamp.context && history.frame===stamp.frame;}
  function featureTokenKey(token){
    // Native preview emits a uint32 number; the confirm command carries its
    // decimal text. Both representations must name the same prepared lease.
    if(typeof token==='string'&&!/^[1-9]\d{0,9}$/.test(token))return null;
    if(typeof token!=='number'&&typeof token!=='string')return null;
    const value=Number(token);
    return Number.isInteger(value)&&value>0&&value<=4294967295?String(value):null;
  }
  function prepareFeatureConfirmation(token,kind,value,expectedContextToken){
    P.Features.assertKind(kind);P.Features.validateGridDraft(value);assertEditable();
    const key=featureTokenKey(token);
    if(key===null||getProjectState().contextToken!==expectedContextToken||
       busy||history.group||pendingLoad||preparingSceneLoad||!sameModelData(readFeatureAttachment(kind),value))
      throw new Error("草稿或專案已變更，請重新預覽確認。");
    featureConfirmations.clear();
    featureConfirmations.set(key,{context:context(),frame:history.frame,kind,value:JSON.parse(JSON.stringify(value)),
      revision:revision(context()),session:connection.session,nativeRevision});
  }
  function beginFeatureConfirmation(token){
    const key=featureTokenKey(token),prepared=featureConfirmations.get(key);if(!prepared)return null;
    featureConfirmations.delete(key);assertEditable();
    if(busy||history.group||pendingLoad||preparingSceneLoad||!assemblyConfirmationCurrent(prepared)||
       prepared.revision!==revision(context())||prepared.session!==connection.session||prepared.nativeRevision!==nativeRevision||
       !sameModelData(readFeatureAttachment(prepared.kind),prepared.value))throw new Error("草稿確認已過期，未套用。");
    assemblyConfirmation={...prepared,featureCommand:"line confirm "+key};schedulePresentation();return assemblyConfirmation;
  }
  function cancelFeatureConfirmation(token){featureConfirmations.delete(featureTokenKey(token));}
  function finishAssemblyConfirmation(stamp){if(assemblyConfirmation===stamp){assemblyConfirmation=null;schedulePresentation();scheduleRecovery();}}
  const safe = fn => async (...args) => { try { return await fn(...args); } catch (e) { toast(e.message || "參考資料操作失敗"); } };
  function group(bid, create = false) {
    if(create)assertEditable();
    if (!history.frame.ids.has(bid) && create) history.frame.ids.set(bid, uuid());
    const key = history.frame.ids.get(bid);
    if (!key) return null;
    if (!context().groups.has(key) && create) context().groups.set(key, { activePageId: "", pages: [] });
    return context().groups.get(key) || null;
  }
  function active(bid) { const shared = window.RoomCollectionWorkspace?.sourcePage(bid); if (shared) return shared; const g = group(bid); return g?.pages.find(p => p.id === g.activePageId) || null; }
  function sharedRoom(bid) {
    return (context().featureAttachments || []).find(record => record.kind === P.Features.ROOM_KIND)?.value.rooms
      .find(room => room.boundaryRef.id === bid && room.reviewState !== "needs-reassociation") || null;
  }
  function assertLegacyTarget(bid) {
    if (sharedRoom(bid)) throw new Error("共享房間使用共同來源；請從房間列表編輯或解除列表關聯。");
  }
  function assertRoomDraftIdle() {
    if (window.RoomCollectionWorkspace?.hasWork) throw new Error("請先完成、取消或恢復目前房間草稿，再切換專案或來源。");
  }
  let presentationFrame = 0;
  function revision(c) { return revisions.get(c) || 0; }
  function getProjectState() {
    const c = context(), frame = history.frame;
    // Undo may return to the same context object. A former asynchronous owner
    // must not regain write permission merely because that project is visible.
    if (!contextTokens.has(frame)) contextTokens.set(frame, uuid());
    return {id:c.id,contextToken:contextTokens.get(frame),revision:revision(c),dirty:!!c.dirty,saved:!!c.saved};
  }
  function getModelOperationState() {
    const identity=value=>{if(!value)return null;if(!modelOperationIdentities.has(value))modelOperationIdentities.set(value,uuid());return modelOperationIdentities.get(value);};
    let blocked=busy||!!oc.busy||!!sceneTransaction||preparingSceneLoad||!!pendingLoad||!!history.group;
    try{assertModelReady();}catch(_){blocked=true;}
    const project=getProjectState(),session=typeof connection==='undefined'?'':connection.session||'';
    // Only opaque scalar identities cross the model owner boundary. A caller
    // cannot mutate a context, frame or history entry through this snapshot.
    return Object.freeze({context:identity(context()),frame:identity(history.frame),revision:project.revision,
      contextToken:project.contextToken+':'+session,undo:identity(history.undo.at(-1)),redo:identity(history.redo.at(-1)),
      group:identity(history.group),blocked:!!blocked});
  }
  function dirty(reason = "") { const c = context(); revisions.set(c, revision(c) + 1); c.dirty = true; c.dirtyReason = reason; c.downloaded = false; schedulePresentation(); scheduleRecovery(); }
  function statusText(c = context()) {
    return busy ? busyLabel || "處理中…" : editorLease==="readonly" || editorLease==="unavailable" ? "另一分頁編輯中 · 唯讀" : contextConflict ? "場景已由其他分頁變更 · 暫停編輯" : fe.draft?.pts?.length ? "外環草稿尚未套用" : fe.ulCalib?.pts?.length ? "校準尚未套用" : c.downloaded ? "已產生下載 · 請確認檔案" : c.dirty ? c.dirtyReason || "有未保存的變更" : c.provenance?.kind === "example" && !c.saved ? "範例已載入 · 尚未另存" : c.saved ? "已保存" : "尚未保存";
  }
  function getProjectInfo() {
    const c=context(),p=c.provenance || fresh().provenance;
    return {id:c.id,name:c.name,sourceKind:p.kind,sourceLabel:p.label,openedAt:p.openedAt || null,
      lastSavedAt:p.lastSavedAt || null,lastDownloadAt:p.lastDownloadAt || null,statusText:statusText(c),
      undoLabel:history.actionLabel("undo") || (history.undo.length ? "上一步模型修改" : null),
      historyNote:history.undo.length ? "可復原本頁已記錄的操作；開啟專案、新專案及清空內容也各算一步。" : "本頁尚無可確認的復原記錄；服務較早的幾何歷史不保證能恢復附件與工程草稿。",
      recovery:{...recovery},editingBlocked:!!assemblyConfirmation || contextConflict || editorLease==="readonly" || editorLease==="unavailable" || !!scenarioContext()&&scenarioBootstrap!=="ready"};
  }
  function markSceneSource(label,kind="scene") {
    assertWritableLease();
    contextConflict=false;
    context().provenance={kind,label,openedAt:new Date().toISOString(),lastSavedAt:null,lastDownloadAt:null};
    recoveryReady=!!recoveryDB && !!recoveryKey;
    present();scheduleRecovery();
  }
  function recoveryMessage(state,message) { recovery={state,message};schedulePresentation(); }
  function recoveryStore(mode,operation) {
    return new Promise((resolve,reject)=>{
      const transaction=recoveryDB.transaction("projects",mode),request=operation(transaction.objectStore("projects"));
      transaction.oncomplete=()=>resolve(request?.result);transaction.onerror=()=>reject(transaction.error || new Error("本機恢復資料寫入失敗。"));
      transaction.onabort=()=>reject(transaction.error || new Error("本機恢復資料交易已中止。"));
    });
  }
  const sceneFingerprint = text => P.sha(new TextEncoder().encode(text.replace(/\r\n/g,"\n")));
  function scheduleRecovery() {
    if(!recoveryReady)return;
    if(recoveryWriting){recoveryAgain=true;return;}
    if(recoveryTimer)clearTimeout(recoveryTimer);
    recoveryTimer=setTimeout(()=>{recoveryTimer=null;persistSession();},600);
  }
  async function persistSession() {
    if(!recoveryReady)return;
    if(recoveryWriting){recoveryAgain=true;return;}
    if(busy || oc.busy || history.group || pendingLoad || preparingSceneLoad || assemblyConfirmation || sceneTransaction){scheduleRecovery();return;}
    if(fe.draft?.pts?.length || fe.ulCalib?.pts?.length || window.WorkspaceShell?.saveState().blocked){
      recoveryMessage("draft","本次外環、校準或工作區草稿尚未套用；恢復資料只保留上次完成的工作內容。");return;
    }
    recoveryWriting=true;
    try {
      const session=typeof connection!=="undefined"?connection.session:null;
      if(!session)throw new Error("尚未確認服務工作階段，未建立恢復資料。");
      const {bytes,stamp,scene}=await exportSnapshot(),c=stamp.context;
      const record={version:1,session,sceneHash:await sceneFingerprint(scene),bytes,updatedAt:new Date().toISOString(),
        project:{dirty:!!c.dirty,dirtyReason:c.dirtyReason || "",saved:!!c.saved,downloaded:!!c.downloaded,provenance:{...c.provenance}}};
      if(recoveryFinishReceipt?.session===session&&recoveryFinishReceipt.key===recoveryKey)record.finishReceipt=recoveryFinishReceipt.hash;
      assertSnapshot(stamp);
      if(!recoveryReady || connection.session!==session)throw new Error("服務或其他分頁已變更，未更新恢復資料。");
      await recoveryStore("readwrite",store=>store.put(record,recoveryKey));
      if(contextConflict)return;
      if(!unchanged(stamp)){recoveryAgain=true;return;}
      recoveryMessage("ready","已在本機保留本分頁的專案恢復資料；這不等於已保存成檔案。未套用的工具草稿與復原歷史不會保留。");
    } catch(error) {
      if(!contextConflict)recoveryMessage("unavailable","本機恢復資料未更新："+(error.message || "儲存空間不可用")+"請保存專案檔案。");
    } finally {recoveryWriting=false;if(recoveryAgain){recoveryAgain=false;scheduleRecovery();}}
  }
  async function restoreSession() {
    if(recoveryAttempted)return {...recovery};
    recoveryAttempted=true;
    if(typeof navigator==="undefined" || !navigator.locks){
      editorLease="unavailable";
      recoveryMessage("readonly","此瀏覽器無法確認單一分頁的編輯權限，目前僅供查看。請使用支援工作鎖定的瀏覽器重新開啟。");present();return {...recovery};
    }
    let initial={context:context(),frame:history.frame,revision:revision(context())},epoch=externalEpoch;
    const assertInitial=()=>{if(externalEpoch!==epoch || !unchanged(initial))throw new Error("檢查恢復資料期間目前專案已變更，未套用舊資料。");};
    busy=true;busyLabel="正在檢查本分頁的恢復資料…";present();
    try {
      const serviceSession=typeof connection!=="undefined"?connection.session:null;
      if(!serviceSession)throw new Error("尚未確認服務工作階段，請重新連接。");
      if(editorLease!=="owned"){
        const takingOver=editorLease==="readonly" || editorLease==="unavailable";
        const writable=await new Promise((resolve,reject)=>{
          navigator.locks.request("geometry-canvas-service-editor-"+serviceSession,{ifAvailable:true},async lock=>{
            if(!lock){resolve(false);return;}
            resolve(true);await new Promise(()=>{});
          }).catch(reject);
        });
        if(!writable){editorLease="readonly";recoveryMessage("readonly","另一個分頁正在編輯這個服務的工作內容。本分頁僅供查看，未讀取或寫入專案恢復資料。請關閉原編輯分頁，再按「重新連接此工作」。");return {...recovery};}
        editorLease="owned";editorLeaseSession=serviceSession;
        if(takingOver){
          // A reader's displayed world may have changed many times. Establish
          // an unknown predecessor before checking this tab's recovery package.
          history.undo=[];history.redo=[];history.group=null;history.blockCoreRedo=false;
          history.frame={context:fresh(),ids:new Map()};contextConflict=false;sync();
          initial={context:context(),frame:history.frame,revision:revision(context())};epoch=externalEpoch;
        }
      }
      if(typeof indexedDB==="undefined"){recoveryMessage("unavailable","此瀏覽器無法保留本分頁的完整專案。重新整理前請保存 .gcanvas 檔案。");return {...recovery};}
      const storageKey="geometry-canvas-recovery-tab-v1",scenario=scenarioContext();
      if(scenario){
        if(scenario!==serviceSession)throw new Error("試改來源與原生工作階段不符，未開啟恢復資料。");
        recoveryKey="geometry-scenario-recovery-"+serviceSession;
      }else{
        if(!window.sessionStorage)throw new Error("本分頁儲存空間不可用。");
        recoveryKey=window.sessionStorage.getItem(storageKey);
        if(!recoveryKey){recoveryKey=uuid();window.sessionStorage.setItem(storageKey,recoveryKey);}
      }
      const locked=await new Promise((resolve,reject)=>{
        navigator.locks.request("geometry-canvas-recovery-"+recoveryKey,{ifAvailable:true},async lock=>{
          if(!lock){resolve(false);return;}
          resolve(true);await new Promise(release=>{releaseRecoveryLock=release;});
        }).catch(reject);
      });
      if(!locked){recoveryKey=null;recoveryMessage("unavailable","另一個分頁正在使用這份恢復資料。本分頁未讀取或覆蓋它；請另存專案檔案。");return {...recovery};}
      recoveryDB=await new Promise((resolve,reject)=>{
        const request=indexedDB.open("geometry-canvas-recovery",1);
        request.onupgradeneeded=()=>request.result.createObjectStore("projects");
        request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);request.onblocked=()=>reject(new Error("本機恢復資料庫被其他視窗占用。"));
      });
      if(scenario){
        // A surviving native B is not enough to prove its latest browser-only
        // metadata. Bootstrap never restores or overwrites an old B checkpoint.
        // Only the exact fresh initializing ticket can authorize first import.
        recoveryReady=false;
        recoveryMessage("scenario-blocked","試改原生內容與既有恢復資料已保留。中斷的試改尚不能證明完整恢復，請回原方案核對或明確捨棄。");
        return {...recovery};
      }
      let record=await recoveryStore("readonly",store=>store.get(recoveryKey)),finishPin=null;assertInitial();
      // A Finish can commit in storage before its local UI acknowledgement.
      // Its immutable receipt takes precedence over an older debounce record,
      // but only in the original parent recovery namespace and native session.
      const ticket=await readStoredScenarioTicket(serviceSession);assertInitial();
      if(ticket?.phase==="retiring"&&ticket.retirement.reason==="finish"&&ticket.retirement.checkpoint.parentKey===recoveryKey){
        const pin=ticket.retirement.checkpoint;
        const saved=await recoveryStore("readonly",store=>store.get(pin.key));assertInitial();
        if(!saved||saved.session!==serviceSession||saved.sceneHash!==pin.sceneHash||await P.sha(saved.bytes)!==pin.packageHash)
          throw new Error("試改完成收據不完整，未覆寫原方案或試改資料。");
        // A successful restore/commit establishes a descendant epoch. Later
        // acknowledged A edits must win over its older immutable Finish copy.
        // An unknown-outcome writer still holding pre-Finish A has no marker.
        if(record?.finishReceipt!==pin.packageHash){record=saved;finishPin=pin;}
      }
      if(!record){recoveryReady=true;recoveryMessage("empty","本分頁尚無恢復資料。服務上的既有幾何來源未知，不能據此推定已保存專案。");return {...recovery};}
      const session=typeof connection!=="undefined"?connection.session:null,dump=await api("dump");assertInitial();
      if(record.version!==1 || !session || record.session!==session || !dump.ok || record.sceneHash!==await sceneFingerprint(dump.text)){
        recoveryMessage("mismatch","先前專案與目前服務工作階段或場景不一致，未恢復附件、草稿及專案身份，也未覆寫目前場景。請開啟正確的 .gcanvas 檔案。");return {...recovery};
      }
      const stage=label=>{busyLabel=label;present();};
      const {loaded,c,ids}=await readProjectContext(record.bytes,"本機恢復專案",stage,assertInitial,true);
      if(await sceneFingerprint(loaded.scene)!==record.sceneHash)throw new Error("本機恢復資料的場景指紋不一致。");
      if(finishPin&&(loaded.manifest.projectId!==finishPin.projectId||!loaded.manifest.scenarioCatalog?.scenarios.some(s=>s.scenarioId===ticket.scenarioId)))
        throw new Error("試改完成收據與原方案身份不符，資料已保留。");
      const verify=await api("dump");assertInitial();
      if(!verify.ok || connection.session!==session || await sceneFingerprint(verify.text)!==record.sceneHash)throw new Error("恢復期間服務場景已變更，未恢復專案。");
      assertInitial();
      const p=record.project;
      if(!p || typeof p.provenance?.kind!=="string" || typeof p.provenance?.label!=="string")throw new Error("本機專案來源記錄不完整。");
      Object.assign(c,{dirty:!!p.dirty,dirtyReason:String(p.dirtyReason || ""),saved:!!p.saved,downloaded:!!p.downloaded,provenance:{...p.provenance}});
      history.frame={context:c,ids:new Map(ids)};history.undo=[];history.redo=[];history.group=null;history.blockCoreRedo=false;
      if(record.finishReceipt&&/^[a-f0-9]{64}$/.test(record.finishReceipt))recoveryFinishReceipt={session,key:recoveryKey,hash:record.finishReceipt};
      recoveryReady=true;sync();
      recoveryMessage("restored","已核對同一服務及場景，恢復本分頁的專案、來源附件、空間模型與工程草稿。未套用的工具草稿及較早復原歷史無法恢復；檔案保存狀態維持原紀錄。");
      return {...recovery};
    } catch(error) {
      if(editorLease!=="owned")editorLease="unavailable";
      if(!contextConflict)recoveryMessage("unavailable","未恢復本機專案："+(error.message || "儲存空間不可用")+"目前場景未被覆寫，請開啟 .gcanvas 檔案。");return {...recovery};
    } finally {busy=false;busyLabel="";present();if(recoveryReady)scheduleRecovery();}
  }
  async function retryRecovery() {
    if(busy)throw new Error("請先等目前操作完成。");
    if(editorLease!=="readonly" && editorLease!=="unavailable")return {...recovery};
    recoveryAttempted=false;return restoreSession();
  }
  function assertContext(c) { if (context() !== c) throw new Error("專案已切換，請在目前專案重新保存或重新選擇來源。"); }
  function cancelSelection(c, g) {
    const jobs = selections.get(c); jobs?.get(g)?.resolve(null); jobs?.delete(g); g.selection = uuid();
  }
  async function referencesReady(c) {
    // Wait for the latest page choice, not a superseded PDF render. Rendering may
    // finish later, but only a live selection is allowed to change saved values.
    for (;;) {
      assertContext(c);
      const jobs = selections.get(c);
      if (jobs) for (const [g, job] of jobs) {
        if (group(job.bid) !== g || g.selection !== job.request) cancelSelection(c, g);
      }
      const pending = [...c.pending, ...[...(jobs?.values() || [])].map(job => job.promise)];
      if (!pending.length) return;
      const results = await Promise.all(pending); assertContext(c);
      const failed = results.find(value => value?.selectionError); if (failed) throw failed.selectionError;
    }
  }
  function schedulePresentation() {
    if (!presentationFrame) presentationFrame = requestAnimationFrame(() => { presentationFrame = 0; present(); });
  }
  function present() {
    const c = context();
    const state = statusText(c);
    const short = busy ? busyShort : contextConflict || editorLease==="readonly" || editorLease==="unavailable" ? "唯讀" : fe.draft?.pts?.length || fe.ulCalib?.pts?.length ? "有草稿" : c.downloaded ? "已下載" : c.dirty || !c.saved ? "未保存" : "已保存";
    document.querySelectorAll("[data-project-name]").forEach(el => { const name = c.name + ".gcanvas"; if (el.textContent !== name) { el.textContent = name; el.title = name; } });
    document.querySelectorAll("[data-project-status]").forEach(el => { if (el.textContent !== state) el.textContent = state; el.dataset.statusShort = short; el.title = state; el.setAttribute("aria-label", state); });
    document.querySelectorAll('[data-project-action="save"]').forEach(el => { el.disabled = busy || getProjectInfo().editingBlocked || !!window.WorkspaceShell?.saveState().blocked; });
    const p = oc.edit && active(oc.edit.bid), source = p && c.sources.get(p.sourceId);
    const summary = document.getElementById("faceReferenceSummary");
    if (summary) {
      const html = p ? `<button type="button" class="reference-source" data-project-action="reference"><strong>${escape(source?.meta.name || "參考圖片")}</strong><span>第 ${p.page} 頁 · ${sharedRoom(oc.edit.bid) ? "共享房間來源" : (group(oc.edit.bid)?.pages.length || 0) + " 張參考頁"}</span><small>${p.calibration ? "已校準" : "未校準"}${p.reviewRequired ? " · 幾何待核對" : ""}</small></button>` : `<p class="reference-empty">尚未加入來源。也可以直接使用上方工具繪製。</p>`;
      if (summary.innerHTML !== html) summary.innerHTML = html;
    }
    document.getElementById("objectWorkspace")?.classList.toggle("reference-editor", !!p && fe.fiTab === "underlay");
    const pane = document.getElementById("faceInspectorContent");
    if (pane) pane.dataset.activeTab = fe.fiTab;
    const activeTab = ["guide", "timber", "grid"].includes(fe.fiTab) ? "components" : fe.fiTab;
    document.querySelectorAll("#faceInspectorTabs [data-fi-tab]").forEach(el => el.setAttribute("aria-pressed", String(el.dataset.fiTab === activeTab)));
    document.querySelectorAll("[data-reference-step]").forEach(el => {
      const step = el.dataset.referenceStep;
      const selected = !p && step === "page" || p && !p.calibration && step === "calibrate" ||
        p && p.calibration && reconstructionState(oc.edit?.bid) !== "confirmed" && step === "draw";
      el.classList.toggle("current", selected);
      if (selected) el.setAttribute("aria-current", "step"); else el.removeAttribute("aria-current");
    });
    window.dispatchEvent(new CustomEvent("project-info-changed"));
  }
  function sync() {
    if (presentedModelContext && presentedModelContext !== context()) {
      for (const g of selections.get(presentedModelContext)?.keys() || []) cancelSelection(presentedModelContext, g);
      sequence++;
      if (modal && modal.context !== context()) closeSource(true);
    }
    const next = {};
    for (const bid of history.frame.ids.keys()) { const p = active(bid); if (p?.src) next[bid] = p; }
    oc.underlays = next;
    const label = document.getElementById("projectName");
    if (label) label.textContent = context().groups.size || context().models.length || context().faceProjections.size || context().engineeringDrafts?.length ? context().name : "";
    schedulePresentation();
    if (presentedModelContext !== context() || presentedModels !== context().models) {
      presentedModelContext = context(); presentedModels = context().models;
      window.dispatchEvent(new CustomEvent("space-models-changed"));
    }
    if (presentedProjectionContext !== context() || presentedProjections !== context().faceProjections) {
      presentedProjectionContext = context(); presentedProjections = context().faceProjections;
      window.dispatchEvent(new CustomEvent("face-projections-changed"));
    }
    if (presentedDraftContext !== context() || presentedDrafts !== context().engineeringDrafts) {
      presentedDraftContext = context(); presentedDrafts = context().engineeringDrafts;
      window.dispatchEvent(new CustomEvent("engineering-drafts-changed"));
    }
  }
  function observe(cmd, result) {
    observeNativeRevision(result);
    if (pendingLoad) return; // A lost load response must be resolved before reusing any face ids.
    if (cmd.startsWith("line ")) {
      cmd = "line " + cmd.slice(5).split("#", 1)[0].trim();
      if (cmd === "line ") return;
    }
    const hadModels = context().models.length || context().modelsDirty;
    const hadProjections = context().faceProjections.size || context().faceProjectionsDirty;
    const previousProjections = context().faceProjections;
    history.observe(cmd, result, connection.session);
    if (roomTransaction && result.ok && cmd === "line history-begin") roomTransaction.group = history.group;
    if (roomTransaction && result.ok && cmd === "line history-end") roomTransaction.entry = history.undo.at(-1);
    window.RoomCollectionWorkspace?.observeNativeResult?.(cmd, result);
    const feature=assemblyConfirmation;
    if(result.ok&&feature?.featureCommand===cmd&&assemblyConfirmationCurrent(feature)&&sameModelData(readFeatureAttachment(feature.kind),feature.value))
      context().featureAttachments=context().featureAttachments.filter(record=>record.kind!==feature.kind);
    if (hadModels && result.ok && /^line\s+(reset|default)\s*$/.test(cmd)) context().modelsDirty = true;
    if (hadProjections && result.ok && /^line\s+(reset|default)\s*$/.test(cmd)) context().faceProjectionsDirty = true;
    const edited = result.ok && !result.preview && cmd.match(/^line\s+(?:boundary|surface)\s+(\d+)\s/);
    if (edited && active(+edited[1])?.calibration) active(+edited[1]).reviewRequired = true;
    if (result.ok && !result.preview && /^(line |drag |reset$|default$|loadfile )/.test(cmd) && !/^line (history-|preview|cancel-preview)/.test(cmd))
      dirty(importRenderingContext === context() && /^line canvas-pos\s/.test(cmd) ? "畫布已自動排版 · 尚未保存" : "");
    if(result.ok && !result.preview && /^(line |drag |reset$|default$|loadfile |engineering-confirm |assembly-confirm )/.test(cmd) && !/^line (history-|preview|cancel-preview)/.test(cmd))notifySceneChange();
    if (result.ok && /^(engineering-confirm|assembly-confirm) /.test(cmd) && result.history_changed !== false) dirty();
    if (previousProjections !== context().faceProjections && context().faceProjectionsDirty) dirty();
    sync();
  }
  function getSpaceModels() { return JSON.parse(JSON.stringify(context().models)); }
  function getAssemblyDrafts() { return structuredClone(context().assemblyDrafts || []); }
  function readFeatureAttachment(kind, expectedContextToken) {
    P.Features.assertKind(kind);
    if (expectedContextToken !== undefined && expectedContextToken !== getProjectState().contextToken)
      throw new Error("專案已切換，未讀取其他專案的功能附件。");
    const record = (context().featureAttachments || []).find(record => record.kind === kind);
    return record ? JSON.parse(JSON.stringify(record.value)) : null;
  }
  function featureProposal(kind,value) {
    const record = value === null ? null : P.Features.record(kind,value);
    const next = (context().featureAttachments || []).filter(record => record.kind !== kind);
    if (record) next.push(record);
    P.Features.sourceRooms({schema:P.Features.SCHEMA,records:next},context().sources);
    P.Features.evidenceLinks({schema:P.Features.SCHEMA,records:next},context().sources,context().id);
    assertMetadataCapacity({featureAttachments:next});
    return next;
  }
  function setFeatureAttachment(kind, value, expectedContextToken, options = {}) {
    P.Features.assertKind(kind);
    const groupedRoom = kind === P.Features.ROOM_KIND && options.recordHistory === false;
    if (groupedRoom) {
      assertRoomTransaction(options.roomLease);
      if (!roomTransaction.group || history.group !== roomTransaction.group || !history.group.dirty)
        throw new Error("房間來源必須與已確認的原生變更同一交易，未寫入。");
    } else {assertEditable(); if (options.recordHistory === false) throw new Error("此功能附件不能略過復原紀錄。");}
    if (typeof expectedContextToken !== "string" || expectedContextToken !== getProjectState().contextToken)
      throw new Error("專案已切換或缺少編輯上下文，未寫入功能附件。");
    if (busy || oc.busy || (!groupedRoom && history.group) || preparingSceneLoad || pendingLoad || nativePending)
      throw new Error("請先完成目前操作，再變更功能附件。");
    const proposal = featureProposal(kind,value), previous = readFeatureAttachment(kind);
    if (sameModelData(previous, value)) return previous;
    const next = structuredClone(proposal);
    if (!groupedRoom) history.push(history.snapshot(), "local", kind === E.KIND ? "編輯參數證據" : kind === P.Features.ROOM_KIND ? "編輯房間來源" : value === null ? "捨棄網格編輯草稿" : "編輯網格草稿");
    context().featureAttachments = next; dirty(); sync();
    if (kind === E.KIND) window.dispatchEvent(new CustomEvent("evidence-links-changed"));
    return readFeatureAttachment(kind);
  }
  function assertRoomTransaction(lease) {
    if (!roomTransaction || lease !== roomTransaction.lease || context() !== roomTransaction.context ||
        history.frame !== roomTransaction.frame || connection.session !== roomTransaction.session ||
        getProjectState().contextToken !== lease.contextToken) throw new Error("房間交易已過期，未變更目前專案。");
    assertConfirmationIdle(); assertEditorLease();
    if (contextConflict || busy || pendingLoad || preparingSceneLoad) throw new Error("專案狀態已變更，房間交易尚未完成。");
  }
  function beginRoomTransaction(contextToken) {
    assertModelReady();
    if (roomTransaction || busy || oc.busy || preparingSceneLoad || contextToken !== getProjectState().contextToken)
      throw new Error("房間預覽尚未就緒，未開始交易。");
    const lease = Object.freeze({contextToken});
    roomTransaction = {lease, context:context(), frame:history.frame, session:connection.session, group:null, entry:null};
    return lease;
  }
  function endRoomTransaction(lease) {
    assertRoomTransaction(lease);
    if (history.group) throw new Error("房間原生交易尚未完成，請先恢復結果。");
    roomTransaction = null; sync();
  }
  async function adoptRoomSource({plane, collectionId, boundaryId, page, roomId, name, associationPin, contextToken}) {
    assertModelReady();
    const c = context(), frame = history.frame, key = frame.ids.get(boundaryId), g = group(boundaryId), source = c.sources.get(plane.sourceId);
    if (busy || oc.busy || preparingSceneLoad || contextToken !== getProjectState().contextToken || !key || active(boundaryId) !== page || !source)
      throw new Error("來源選取已過期，未轉入共享房間。");
    const reviewKey = key + ":" + page.id, readReview = () => c.reconstructionReviews.has(reviewKey) ? c.reconstructionReviews.get(reviewKey) : null,
      originalReview = readReview();
    const stamp = getModelOperationState(), original = readFeatureAttachment(P.Features.ROOM_KIND),
      incarnation = frame.ids.get(boundaryId);
    if (!sameModelData(GeometrySourcePlane.fromPage(page, source.meta.type, plane.id), plane)) throw new Error("共享來源基準與明選原頁不一致。");
    const next = GeometrySourcePlane.upgradeDisplay(original || GeometrySourcePlane.empty());
    next.planes.push(structuredClone(plane)); next.collections.push({id:collectionId,planeId:plane.id,roomIds:[roomId]});
    next.rooms.push({id:roomId,name,boundaryRef:{kind:"boundary",id:boundaryId,associationPin},acceptedBasisRevision:plane.basisRevision,reviewState:"confirmed",
      display:{crop:structuredClone(page.crop),opacity:page.opacity,locked:page.locked}});
    if (page.records.length || originalReview !== null) {
      (next.legacyHistory ||= []).push({planeId:plane.id,boundaryId,pageId:page.id,records:page.records,reconstructionReview:originalReview});
    }
    // Validate the original JSON before taking detached snapshots; serialization
    // must not erase unsupported values or unknown historical record fields.
    const record = structuredClone(P.Features.record(P.Features.ROOM_KIND, next));
    const originalPage = P.reference(page), reviewSnapshot = structuredClone(originalReview);
    const records = c.featureAttachments.filter(record => record.kind !== P.Features.ROOM_KIND).concat(record);
    P.Features.sourceRooms({schema:P.Features.SCHEMA,records},c.sources);
    const native = await apiRequest("boundary " + boundaryId);
    if (!native.ok || await GeometryRoomCollection.boundaryPin(native) !== associationPin) throw new Error("原生邊界已變更，未轉入共享房間。");
    assertModelReady();
    if (record.value.legacyHistory) {
      // Revalidate caller-owned historical JSON after the native await: JSON
      // equality alone would treat a late NaN as an unchanged saved null.
      const current = structuredClone(record.value), entry = current.legacyHistory.at(-1);
      if (entry.planeId === plane.id && entry.pageId === page.id) {
        entry.records = page.records; entry.reconstructionReview = readReview();
        P.Features.record(P.Features.ROOM_KIND, current);
      }
    }
    if (context() !== c || history.frame !== frame || frame.ids.get(boundaryId) !== incarnation || active(boundaryId) !== page ||
        !sameModelData(getModelOperationState(), stamp) || !sameModelData(P.reference(page), originalPage) ||
        !sameModelData(readReview(), reviewSnapshot) ||
        !sameModelData(readFeatureAttachment(P.Features.ROOM_KIND), original)) throw new Error("來源轉入結果晚到，未改動目前專案。");
    const pages = g.pages.filter(candidate => candidate !== page), groups = new Map(c.groups);
    if (pages.length) groups.set(key, {...g,pages,activePageId:pages[0].id}); else groups.delete(key);
    const reviews = new Map(c.reconstructionReviews); reviews.delete(reviewKey);
    assertMetadataCapacity({groups,reconstructionReviews:reviews,featureAttachments:records});
    history.push(history.snapshot(), "local", "轉入共享房間來源");
    c.groups = groups; c.reconstructionReviews = reviews; c.featureAttachments = records; dirty(); sync();
  }
  const roomIntegration = Object.freeze({
    readSource:(id,token) => {if (token !== getProjectState().contextToken) throw new Error("來源讀取上下文已過期。"); return context().sources.get(id) || null;},
    readIncarnation:(id,token) => {if (token !== getProjectState().contextToken) throw new Error("房間身份上下文已過期。"); return history.frame.ids.get(id) || null;},
    beginTransaction:beginRoomTransaction, assertTransaction:assertRoomTransaction, endTransaction:endRoomTransaction,
    preflightAttachment:(value,lease) => {assertRoomTransaction(lease);featureProposal(P.Features.ROOM_KIND,value);},
    groupOpen:lease => {assertRoomTransaction(lease); return !!roomTransaction.group && history.group === roomTransaction.group;},
    labelTransaction:(lease,label) => {assertRoomTransaction(lease); if (history.group || !roomTransaction.entry || history.undo.at(-1) !== roomTransaction.entry || typeof label !== "string" || label.length > 500) throw new Error("房間歷史步驟已變更。"); roomTransaction.entry.action = label;},
    adoptLegacySource:adoptRoomSource
  });
  function setAssemblyDraft(record, token, recordHistory = true) {
    assertDraftContext(token); P.validateAssemblyDraft(record);
    const next=getAssemblyDrafts(), index=next.findIndex(item=>item.id===record.id);
    if(index<0 && next.length>=256)throw new Error("單一專案最多 256 份組構草稿。");
    if(index>=0 && sameModelData(next[index],record))return next[index];
    const saved=structuredClone(record);if(index<0)next.push(saved);else next[index]=saved;
    assertMetadataCapacity({assemblyDrafts:next});
    if(recordHistory)history.push(history.snapshot(),"local","編輯組構草稿");
    context().assemblyDrafts=next;dirty();sync();return structuredClone(saved);
  }
  function removeAssemblyDraft(id, token, recordHistory = true) {
    assertDraftContext(token);const next=getAssemblyDrafts(),removed=next.find(item=>item.id===id);
    if(!removed)return null;
    if(recordHistory)history.push(history.snapshot(),"local","刪除組構草稿");
    context().assemblyDrafts=next.filter(item=>item.id!==id);dirty();sync();return removed;
  }
  function getEngineeringDrafts() { return JSON.parse(JSON.stringify(context().engineeringDrafts || [])); }
  function assertDraftContext(expectedContextToken) {
    assertEditable();
    if (pendingLoad) throw new Error("請先確認專案載入結果再修改工程草稿。");
    if (expectedContextToken !== undefined && expectedContextToken !== getProjectState().contextToken)
      throw new Error("專案已切換，未將先前的工程草稿寫入目前專案。");
  }
  function setEngineeringDraft(record, expectedContextToken) {
    assertDraftContext(expectedContextToken); P.validateEngineeringDraft(record);
    const next=getEngineeringDrafts(),index=next.findIndex(item=>item.id===record.id);
    if(index<0 && next.length>=P.MAX_ENGINEERING_DRAFTS)throw new Error("單一專案最多可保存 256 份工程規格草稿。");
    if(index>=0 && sameModelData(next[index],record))return next[index];
    const saved=JSON.parse(JSON.stringify(record));if(index<0)next.push(saved);else next[index]=saved;
    assertMetadataCapacity({engineeringDrafts:next});
    context().engineeringDrafts=next;dirty();sync();return JSON.parse(JSON.stringify(saved));
  }
  function removeEngineeringDraft(id, expectedContextToken) {
    assertDraftContext(expectedContextToken);
    const next=getEngineeringDrafts(),removed=next.find(item=>item.id===id);if(!removed)return null;
    context().engineeringDrafts=next.filter(item=>item.id!==id);dirty();sync();return removed;
  }
  function getFaceProjections(bid) {
    return JSON.parse(JSON.stringify(context().faceProjections.get(history.frame.ids.get(bid)) || []));
  }
  function getFaceProjection(bid, placementId) {
    return getFaceProjections(bid).find(record => record.placement_id === placementId)?.projection || null;
  }
  function setFaceProjection(bid, placementId, projection) {
    assertModelReady();
    if (oc.busy) throw new Error("請先完成目前的操作再變更平面投影定義。");
    const key = history.frame.ids.get(bid);
    if (!key || !Number.isSafeInteger(placementId) || placementId < 0 || placementId > 4294967295) throw new Error("找不到要設定平面投影的面或放置。");
    if (projection !== null) {
      P.validateFaceProjection(projection);
      const surface = oc.surfs?.find(s => s.id === placementId && s.boundary === bid);
      if (!surface || surface.u?.[2] !== 0 || surface.v?.[2] !== 0) throw new Error("平面投影必須指定這個面的水平放置。");
    }
    const current = getFaceProjection(bid, placementId);
    if (sameModelData(current, projection)) return current;
    const next = new Map(context().faceProjections), records = getFaceProjections(bid).filter(record => record.placement_id !== placementId);
    if (projection !== null) records.push({placement_id:placementId,projection});
    records.sort((a,b) => a.placement_id-b.placement_id);
    if (records.length) next.set(key, records); else next.delete(key);
    assertMetadataCapacity({faceProjections:next});
    history.changeFaceProjections(next); context().faceProjectionsDirty = true; dirty(); sync();
    return getFaceProjection(bid, placementId);
  }
  function assertModelReady() {
    assertEditable();
    if (pendingLoad || history.group) throw new Error("請先完成目前的操作再變更空間模型。");
    if (typeof connection !== "undefined" && connection.phase !== "ready") throw new Error("場景連線尚未確認，請先重新連線。");
  }
  function addSpaceModel(record) {
    assertModelReady(); P.validateSpaceModel(record);
    if (context().models.length >= P.MAX_MODELS) throw new Error("單一專案最多可保存 64 個空間模型。");
    if (context().models.some(m => m.id === record.id)) throw new Error("空間模型 ID 重複。");
    const next = [...context().models,record];assertMetadataCapacity({models:next});
    history.changeModels(next); context().modelsDirty = true; dirty(); sync();
    return getSpaceModels().at(-1);
  }
  function updateSpaceModel(id, record) {
    assertModelReady(); P.validateSpaceModel(record);
    const index = context().models.findIndex(m => m.id === id);
    if (index < 0 || record.id !== id) throw new Error("找不到要更新的空間模型。");
    const next = context().models.map((m,n) => n === index ? record : m);assertMetadataCapacity({models:next});
    history.changeModels(next); context().modelsDirty = true; dirty(); sync();
    return getSpaceModels()[index];
  }
  function removeSpaceModel(id) {
    assertModelReady();
    const removed = getSpaceModels().find(m => m.id === id);
    if (!removed) throw new Error("找不到要移除的空間模型。");
    history.changeModels(context().models.filter(m => m.id !== id)); context().modelsDirty = true; dirty(); sync(); return removed;
  }
  function tryLocalHistory(cmd) {
    if (pendingLoad) return null;
    if(/^line\s+(undo|redo)\b/.test(cmd))assertEditable();
    const previousContext=context(),previousContextToken=getProjectState().contextToken;
    const result = history.tryLocal(cmd);
    if (result?.ok) {
      // A live editor may follow a local draft undo in the same project. This
      // explicit notification never renews a former editor after a project switch.
      if(context()===previousContext)window.dispatchEvent(new CustomEvent("project-local-history",{
        detail:{previousContextToken,contextToken:getProjectState().contextToken}}));
      context().modelsDirty = true; context().faceProjectionsDirty = true; dirty(); sync();
    }
    return result;
  }
  async function library() {
    if (!pdfLib) pdfLib = import("/vendor/pdfjs-dist/build/pdf.mjs").then(lib => {
      lib.GlobalWorkerOptions.workerSrc = "/vendor/pdfjs-dist/build/pdf.worker.mjs"; return lib;
    });
    return pdfLib;
  }
  async function sourceFromFile(file) {
    if (file.size > P.MAX_SOURCE || file.size < 1) throw new Error("來源檔案須介於 1 byte 與 128 MB。");
    const bytes = new Uint8Array(await file.arrayBuffer());
    let type = file.type;
    if (new TextDecoder().decode(bytes.subarray(0,5)) === "%PDF-") type = "application/pdf";
    if (!P.TYPES.has(type)) throw new Error("請選擇 PDF、PNG、JPEG、WebP 或 GIF。");
    const hash = await P.sha(bytes);
    return { meta: { id: hash, hash, name: file.name || "參考圖片", type, size: bytes.length, path: "sources/" + hash }, bytes };
  }
  async function documentFor(s, assertCurrent = () => {}) {
    if (s.meta.type !== "application/pdf") return null;
    if (s.cleanup) {await s.cleanup; assertCurrent();}
    if (!s.doc) {
      const lib = await library();
      assertCurrent();
      const task = lib.getDocument({ data: s.bytes.slice(), isEvalSupported: false,
        cMapUrl: "/vendor/pdfjs-dist/cmaps/", cMapPacked: true,
        standardFontDataUrl: "/vendor/pdfjs-dist/standard_fonts/", wasmUrl: "/vendor/pdfjs-dist/wasm/" });
      s.loadingTask = task;
      s.documentTask = task;
      task.onPassword = () => { task.destroy().catch(()=>{}); };
      try { s.doc = await task.promise; assertCurrent(); } catch (error) { await releasePDFSource(s);assertCurrent();throw new Error("無法讀取 PDF；請確認檔案完整且未加密。"); }
      finally { if (s.loadingTask === task) s.loadingTask = null; }
    }
    return s.doc;
  }
  async function releasePDFSource(source) {
    const task=source.loadingTask || source.documentTask || source.doc?.loadingTask;
    source.doc=null;source.loadingTask=null;source.documentTask=null;
    if(task)await task.destroy().catch(()=>{});
  }
  // Runtime-only immutable source features: never added to history or saved
  // project metadata. A late extraction only fills its source/page cache.
  const tracingCache = new WeakMap();
  function tracingFeatures(bid) {
    const p=active(bid),s=p&&context().sources.get(p.sourceId);
    if(!s || s.meta.type!=="application/pdf")return {status:"manual"};
    let pages=tracingCache.get(s);if(!pages){pages=new Map();tracingCache.set(s,pages);}
    if(!pages.has(p.page)) {
      const job={status:"loading"};pages.set(p.page,job);
      (async()=>{
        try {
          const lib=await library(),doc=await documentFor(s),page=await doc.getPage(p.page);
          const list=await page.getOperatorList();
          job.features=RoomOutline.pdfSnapFeatures(list,lib.OPS,page.getViewport({scale:1}));
          job.status=job.features.segments.length?"ready":"manual";
        } catch(_) {job.status="unavailable";}
      })();
    }
    return pages.get(p.page);
  }
  function imageFor(s) {
    if (!s.image) s.image = new Promise((resolve, reject) => {
      const url = URL.createObjectURL(new Blob([s.bytes], { type: s.meta.type })), img = new Image();
      img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
      img.onerror = () => { URL.revokeObjectURL(url); s.image = null; reject(new Error("無法讀取圖片。")); };
      img.src = url;
    });
    return s.image;
  }
  async function renderPage(s, page, scale = 4, assertCurrent = () => {}) {
    const canvas = document.createElement("canvas");
    let width, height;
    if (s.meta.type === "application/pdf") {
      const doc = await documentFor(s, assertCurrent); assertCurrent();
      if (page < 1 || page > doc.numPages) throw new Error("PDF 頁码不存在。");
      const p = await doc.getPage(page), base = p.getViewport({ scale: 1 });
      assertCurrent();
      width = base.width; height = base.height;
      const k = Math.min(scale, 5000 / Math.max(width, height), Math.sqrt(16000000 / (width * height)));
      const viewport = p.getViewport({ scale: k });
      canvas.width = Math.ceil(viewport.width); canvas.height = Math.ceil(viewport.height);
      await p.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
      assertCurrent();
    } else {
      const img = await imageFor(s); width = img.naturalWidth; height = img.naturalHeight;
      const k = Math.min(1, 5000 / Math.max(width, height));
      canvas.width = Math.ceil(width * k); canvas.height = Math.ceil(height * k);
      canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
    }
    return { canvas, width, height, src: canvas.toDataURL("image/png") };
  }
  async function preparePage(p, s) {
    const r = await renderPage(s, p.page);
    if (Math.abs(p.imgW - r.width) > 0.01 || Math.abs(p.imgH - r.height) > 0.01) throw new Error("圖頁尺寸與來源不一致。");
    p.src = r.src; return p;
  }
  // Locate a recorded reference independently of the current face/page. An
  // unlinked source remains usable through the same original PDF reader.
  function evidenceReference(d) {
    for (const [bid, key] of history.frame.ids) {
      const g = context().groups.get(key), page = g?.pages.find(p => p.id === d.referencePageId);
      if (page) return {bid, group:g, page, source:context().sources.get(page.sourceId)};
    }
    const rooms = P.Features.sourceRooms({schema:P.Features.SCHEMA,records:context().featureAttachments});
    for (const room of rooms?.rooms || []) {
      const page = active(room.boundaryRef.id);
      if (page?.id === d.referencePageId) return {bid:room.boundaryRef.id,page,source:context().sources.get(page.sourceId)};
    }
    const source = context().sources.get(d.sourceHash);
    return {bid:null, source, page:source ? {id:d.referencePageId,sourceId:d.sourceHash,page:d.page,imgW:d.pageWidth,imgH:d.pageHeight,rot:d.rotationBasis,crop:[...d.cropBasis]} : null};
  }
  function readEvidenceDocument(d) {
    const r = evidenceReference(d);
    return r.page && r.source && r.source.bytes instanceof Uint8Array && r.source.bytes.length === r.source.meta.size
      ? E.documentFromReference(r.page, r.source) : null;
  }
  function getEvidenceNavigationStamp() {
    return {focus:oc.focus ? {...oc.focus} : null,edit:oc.edit ? {...oc.edit} : null,
      selected:oc.sel ? {...oc.sel} : null,panX:fe.panX ?? null,panY:fe.panY ?? null,zoom:fe.zoom ?? null,
      objectPanX:oc.panX ?? null,objectPanY:oc.panY ?? null,objectZoom:oc.zoom ?? null,
      modal:modal ? {sequence,page:modal.page,source:modal.source.meta.id} : null};
  }
  function getReferenceNavigationStamp(d) {
    const r = evidenceReference(d), s = r.source;
    if (!s || !r.page) throw new Error("證據原 PDF 缺失。");
    return {...getEvidenceState(),...getEvidenceNavigationStamp(),sourceId:s.meta.id,sourceHash:s.meta.hash,sourceType:s.meta.type,sourceSize:s.meta.size,
      document:E.documentFromReference(r.page,s),basis:r.bid === null ? null : P.reviewBasis(r.page),
      activeReference:r.group?.activePageId ?? null,selection:r.group?.selection ?? null};
  }
  async function prepareReferencePage(document, region, {assertCurrent}) {
    assertCurrent();
    const expected = JSON.stringify(getReferenceNavigationStamp(document)), r = evidenceReference(document);
    const source = {meta:structuredClone(r.source.meta),bytes:r.source.bytes.slice()};
    const hash = await P.sha(source.bytes); assertCurrent();
    if (hash !== document.sourceHash || source.meta.hash !== hash || source.meta.id !== hash || source.meta.type !== "application/pdf") throw new Error("證據原 PDF 已換版。");
    let pageRender, pageCount;
    try {
      pageRender = await renderPage(source, document.page, 4, assertCurrent); assertCurrent();
      pageCount = source.doc.numPages;
    } finally {
      await releasePDFSource(source);
    }
    assertCurrent();
    if (pageRender.width !== document.pageWidth || pageRender.height !== document.pageHeight) throw new Error("證據頁碼或尺寸不符。");
    const prepared = Object.freeze({document:structuredClone(document),sourceMeta:structuredClone(source.meta),verifiedBytes:source.bytes.slice(),pageCount,pageRender:Object.freeze({...pageRender})});
    preparedReferences.set(prepared, {expected,source,region:[...region],document:JSON.stringify(document)});
    return prepared;
  }
  function commitPreparedReferencePage(prepared, descriptor, region) {
    const lease = preparedReferences.get(prepared);
    if (!lease || lease.document !== JSON.stringify(descriptor) || JSON.stringify(region) !== JSON.stringify(lease.region) ||
        lease.expected !== JSON.stringify(getReferenceNavigationStamp(descriptor)) ||
        prepared.sourceMeta.id !== descriptor.sourceHash || prepared.sourceMeta.hash !== descriptor.sourceHash ||
        prepared.pageRender.width !== descriptor.pageWidth || prepared.pageRender.height !== descriptor.pageHeight ||
        !(prepared.verifiedBytes instanceof Uint8Array) || prepared.verifiedBytes.length !== lease.source.bytes.length ||
        prepared.verifiedBytes.some((b,i) => b !== lease.source.bytes[i])) throw new Error("定位候選或上下文已過期，未變更畫面。");
    assertEditable(); assertRoomDraftIdle();
    if (getEvidenceState().blocked || fe.draft?.pts?.length || fe.ulCalib || window.ParameterUI?.pending) throw new Error("請先完成或取消目前草稿，再定位證據。");
    const r = evidenceReference(descriptor), p = r.page;
    if (!(r.source.bytes instanceof Uint8Array) || r.source.bytes.length !== lease.source.bytes.length ||
        r.source.bytes.some((b,i)=>b!==lease.source.bytes[i])) throw new Error("證據原 PDF bytes 已變更，未定位。");
    const [rx,ry,rw,rh]=region,crop=p.crop;
    const visible=rx>=crop[0]&&ry>=crop[1]&&rx+rw<=crop[0]+crop[2]&&ry+rh<=crop[1]+crop[3];
    if (r.bid !== null && oc.edit?.bid === r.bid && oc.focus?.t === "face" && visible) {
      if (r.group) {
        const groups = new Map(context().groups);groups.set(history.frame.ids.get(r.bid),{...r.group,activePageId:p.id});
        assertMetadataCapacity({groups});
      }
      preparedReferences.delete(prepared);
      p.src = prepared.pageRender.src;
      if (r.group) {cancelSelection(context(),r.group);r.group.activePageId=p.id;dirty();}
      fe.ulCalib=null;fe.ulDrag=null;sync();
      window.EvidenceLinksApp?.showRegion(descriptor,region);
      const [x,y,w,h]=region,pts=[[x,y],[x+w,y],[x+w,y+h],[x,y+h]].map(v=>feUlImgToMm(p,...v));
      feFit([Math.min(...pts.map(v=>v[0])),Math.min(...pts.map(v=>v[1])),Math.max(...pts.map(v=>v[0])),Math.max(...pts.map(v=>v[1]))]);
      drawFaceEditor();renderFaceInspector();
    } else {
      // Existing PDF preview, now in read-only evidence mode. No native face,
      // source linkage or saved calibration is invented for unlinked evidence.
      preparedReferences.delete(prepared);
      modal={context:context(),source:lease.source,bid:null,page:descriptor.page,width:descriptor.pageWidth,height:descriptor.pageHeight,
        crop:[...region],zoom:"page",ready:true,evidence:true,render:prepared.pageRender};sequence++;
      const host=document.getElementById("refPagePreview");
      host.innerHTML='<img alt="證據原 PDF 頁"><div id="refCropOverlay"></div>';
      host.querySelector("img").src=prepared.pageRender.src;
      document.getElementById("refThumbnails").replaceChildren();
      document.getElementById("refPageNumber").value=descriptor.page;
      document.getElementById("refSourceName").textContent=lease.source.meta.name;
      document.getElementById("refZoom").value="page";
      document.getElementById("refPageCount").textContent="／"+prepared.pageCount;
      document.getElementById("refPreviewMessage").textContent="證據原頁範圍 · 唯讀核對";
      document.getElementById("refApply").disabled=true;
      document.getElementById("refApply").hidden=true;
      document.getElementById("refTarget").disabled=true;
      for (const id of ["refPageNumber","refPrev","refNext","refResetCrop"]) document.getElementById(id).disabled=true;
      document.getElementById("referenceDialog").showModal();layoutPreview();drawCrop();
    }
    return {ok:true};
  }
  function addPage(bid, p) {
    assertEditable(); assertLegacyTarget(bid); assertRoomDraftIdle();
    assertPageCapacity(bid,p,{append:true});
    const g = group(bid, true); cancelSelection(context(), g); g.pages.push(p); g.activePageId = p.id;
    dirty(); sync(); return p;
  }
  function adoptLegacy(bid, ul) {
    assertEditable(); assertLegacyTarget(bid); assertRoomDraftIdle();
    const c = context(), frame = history.frame,
      page = {...ul,id:uuid(),sourceId:"pending",page:1,crop:[0,0,ul.imgW,ul.imgH],calibration:null,reviewRequired:false,records:[]};
    // Budget the future hash/asset entry before the synchronous legacy display
    // changes. This placeholder is never published or used as source evidence.
    let budgetId = "0".repeat(64);for (let index = 1;c.sources.has(budgetId);index++) budgetId = index.toString(16).padStart(64,"0");
    const proposedSources = new Map(c.sources);proposedSources.set(budgetId,{meta:{id:budgetId,hash:budgetId,name:"參考圖片",type:"application/pdf",size:P.MAX_SOURCE,path:"sources/"+budgetId}});
    assertPageCapacity(bid,{...page,sourceId:budgetId},{replace:true,sources:proposedSources});
    const p = Object.assign(ul,page);
    const g = group(bid, true); cancelSelection(c, g); g.pages = [p]; g.activePageId = p.id; dirty();
    const pending = (async () => {
      const blob = await fetch(p.src).then(r => r.blob());
      const s = await sourceFromFile(new File([blob], "參考圖片", { type: blob.type }));
      assertEditable();assertContext(c);
      if (history.frame !== frame || group(bid) !== g || active(bid) !== p) throw new Error("底圖來源結果晚到，未改動目前圖頁。");
      const sources = new Map(c.sources);sources.set(s.meta.id,s);
      assertPageCapacity(bid,{...p,sourceId:s.meta.id},{sources});
      c.sources.set(s.meta.id, s); p.sourceId = s.meta.id;
    })();
    c.pending.add(pending); pending.then(() => c.pending.delete(pending), () => {});
  }
  function calibrated(bid, points, distMm, inputValue = distMm, inputUnit = "mm") {
    assertEditable();
    const p = active(bid); if (!p) return;
    if (sharedRoom(bid)) return RoomCollectionWorkspace.changeBasis(bid, {mmPerPx:p.mmPerPx},
      {points:points.map(v => [...v]),distanceMm:distMm,inputValue,inputUnit});
    const calibration = {points:points.map(v=>[...v]),distanceMm:distMm,inputValue,inputUnit};
    assertPageCapacity(bid,{...p,calibration,reviewRequired:true});
    p.calibration = calibration;
    p.reviewRequired = true; dirty();
  }
  function changed(bid, recheck = false) {
    assertEditable(); const p = active(bid);
    if (sharedRoom(bid)) return RoomCollectionWorkspace.changeView(bid, {crop:p.crop,opacity:p.opacity,locked:p.locked,x:p.x,y:p.y,rot:p.rot,mmPerPx:p.mmPerPx});
    if (p) assertPageCapacity(bid,{...p,reviewRequired:recheck ? true : p.reviewRequired});
    if (p && recheck) p.reviewRequired = true; dirty();
  }
  function remove(bid) {
    assertEditable(); assertLegacyTarget(bid); assertRoomDraftIdle();
    const g = group(bid); if (!g) return;
    cancelSelection(context(), g);
    g.pages = g.pages.filter(p => p.id !== g.activePageId); g.activePageId = g.pages[0]?.id || "";
    dirty(); sync();
    const next = active(bid), c = context();
    if (next && !next.src) preparePage(next, c.sources.get(next.sourceId)).then(() => {
      if (context() === c && active(bid) === next) { sync(); if (oc.edit?.bid === bid) redraw(); }
    }).catch(e => toast(e.message));
  }
  function redraw() { sync(); if (oc.edit) { drawFaceEditor(); renderFaceInspector(); } }
  function fitReference() {
    const p = oc.edit && active(oc.edit.bid); if (!p) return;
    const [x,y,w,h] = p.crop;
    const pts = [[x,y],[x+w,y],[x+w,y+h],[x,y+h]].map(v => feUlImgToMm(p,...v));
    feFit([Math.min(...pts.map(v=>v[0])), Math.min(...pts.map(v=>v[1])), Math.max(...pts.map(v=>v[0])), Math.max(...pts.map(v=>v[1]))]);
    drawFaceEditor();
  }
  async function validateEvidenceClosure(c, attachments, assertCurrent) {
    const evidence = attachments && P.Features.evidenceLinks(attachments,c.sources,c.id);
    if (!evidence) return;
    const detached = new Set();
    try { await E.validateSourceClosure(evidence, {
      readSource:hash=>c.sources.get(hash),
      hashBytes:async bytes=>{const hash=await P.sha(bytes);assertCurrent();return hash;},
      readPage:async (source,number)=>{
        detached.add(source);
        const pdf=await documentFor(source,assertCurrent);assertCurrent();
        if(number>pdf.numPages)throw new Error("證據 PDF 頁碼不存在。");
        const page=await pdf.getPage(number);assertCurrent();
        const size=page.getViewport({scale:1});return {width:size.width,height:size.height};
      }
    });assertCurrent();
    } finally {await Promise.all([...detached].map(releasePDFSource));}
    assertCurrent();
  }
  async function selectPage(bid, pageId) {
    assertEditable(); assertLegacyTarget(bid); assertRoomDraftIdle();
    const g = group(bid), p = g?.pages.find(p => p.id === pageId); if (!p) return;
    const c = context(), proposedGroups = new Map(c.groups);
    proposedGroups.set(history.frame.ids.get(bid),{...g,activePageId:p.id});
    assertMetadataCapacity({groups:proposedGroups});
    cancelSelection(c, g); const request = g.selection;
    if (!selections.has(c)) selections.set(c, new Map());
    let resolve; const promise = new Promise(done => { resolve = done; });
    const job = { bid, request, promise, resolve }; selections.get(c).set(g, job);
    revisions.set(c, revision(c) + 1);
    let error = null;
    try {
      if (!p.src) await preparePage(p, c.sources.get(p.sourceId));
      if (context() !== c || group(bid) !== g || g.selection !== request) return;
      assertEditable(); assertLegacyTarget(bid); assertRoomDraftIdle();
      const groups = new Map(c.groups);groups.set(history.frame.ids.get(bid),{...g,activePageId:p.id});
      assertMetadataCapacity({groups});
      g.activePageId = p.id; fe.ulCalib = null; fe.ulDrag = null; dirty(); redraw(); fitReference();
    } catch (e) { error = e; throw e; }
    finally {
      if (selections.get(c).get(g) === job) selections.get(c).delete(g);
      resolve(error ? {selectionError:error} : null);
    }
  }
  function paneHTML(bid) {
    if (sharedRoom(bid)) return window.RoomCollectionWorkspace?.paneHTML(bid) || "";
    const g = group(bid), p = active(bid);
    let html = `<details id="refSourceDetails" class="ref-section"${p ? "" : " open"}><summary>參考頁與來源</summary><div class="ref-actions"><button id="refImport" class="btn" type="button">匯入 PDF／圖片</button>`;
    if (p) html += `<button id="refMorePages" class="btn" type="button">從此來源選其他頁</button>`;
    html += `</div>`;
    if (!p) return html + `<p class="fi-note">參考資料會隨 .gcanvas 專案保存。純 .scene 只保存幾何。</p></details>`;
    html += `<label class="ib-row">參考頁<select id="refActivePage">${g.pages.map(v => `<option value="${v.id}"${v.id===p.id?" selected":""}>${escape(context().sources.get(v.sourceId)?.meta.name || "圖片")} · 第 ${v.page} 頁</option>`).join("")}</select></label>`;
    html += `</details><details class="ref-records ref-section" id="refRecordDetails"><summary>來源紀錄與待補資訊（${p.records.length}）</summary>`;
    for (const r of p.records) html += `<article class="ref-record"><strong>${escape(r.label || "未命名紀錄")}</strong><span>${r.value===null?"待補":escape(r.value)+" "+r.unit}</span><p>${escape(r.location)}${r.datum?" · 基準："+escape(r.datum):""}</p><small>第 ${p.page} 頁</small><button type="button" class="text-button" data-ref-remove-record="${r.id}" aria-label="移除 ${escape(r.label)} 紀錄">移除</button></article>`;
    html += `<label class="ib-row">項目<input id="refRecordLabel" maxlength="300" placeholder="例如：天花完成高度"></label><label class="ib-row">位置說明<input id="refRecordLocation" maxlength="1000" placeholder="例如：A202 主區域"></label><div class="place-form"><label>數值（留空表示待補）<input id="refRecordValue" type="number" step="any"></label><label>單位<select id="refRecordUnit"><option>mm</option><option>cm</option></select></label></div><label class="ib-row">基準<input id="refRecordDatum" maxlength="300" placeholder="例如：完成地坪 FFL"></label><button id="refRecordAdd" type="button" class="btn">新增來源紀錄</button><p class="fi-note">紀錄不會自動建立構件。天花完成高度與 RC 樑底高度請分開記錄。</p></details>`;
    return html.replace('</p></details>', '</p><div data-evidence-host></div></details>');
  }
  function reviewKey(bid, page=active(bid)) { return history.frame.ids.get(bid)+":"+page?.id; }
  function reconstructionState(bid) {
    const room = sharedRoom(bid); if (room) return room.reviewState === "confirmed" ? "confirmed" : "recheck";
    const p=active(bid);if (!p) return "unreviewed";
    if (window.RoomOutlineWorkspace?.pending?.(bid)) return "candidate";
    const r=context().reconstructionReviews.get(reviewKey(bid,p));
    if (!r) return "unreviewed";
    return r.basis===P.reviewBasis(p) && r.geometry===P.outlineFingerprint(oc.bmap[bid]) ? "confirmed" : "recheck";
  }
  function markReconstructionReviewed(bid, {method="manual", warnings=[], local=true, expectedBasis=null}={}) {
    assertEditable(); assertLegacyTarget(bid); const p=active(bid);
    if (!p?.calibration || !oc.bmap[bid]?.[0]?.verts?.length) throw new Error("請先校準來源並完成合法輪廓，再核對。");
    if (expectedBasis && expectedBasis!==P.reviewBasis(p)) throw new Error("來源對位已變更，請重新核對；正式面尺寸保持原值。");
    const receipt = {basis:P.reviewBasis(p),geometry:P.outlineFingerprint(oc.bmap[bid]),method,warnings:[...warnings],confirmedAt:new Date().toISOString()},
      reviews = new Map(context().reconstructionReviews);reviews.set(reviewKey(bid,p),receipt);
    assertPageCapacity(bid,{...p,reviewRequired:false},{reconstructionReviews:reviews});
    if (local) {if (history.group) throw new Error("請先完成目前交易。");history.push(history.snapshot(),"local","核對來源輪廓");}
    context().reconstructionReviews = reviews;
    p.reviewRequired=false;dirty();schedulePresentation();
  }
  function reconstructionStatusHTML(bid) {
    const p = active(bid); if (!p) return "";
    const state=reconstructionState(bid),label={unreviewed:"尚未依此來源核對輪廓（原有矩形不代表重建完成）",candidate:"輪廓候選 · 尚未確認",confirmed:"已依此來源核對輪廓",recheck:"來源或輪廓已變更 · 需要重新核對"}[state];
    return `<div class="reference-review" data-reconstruction-state="${state}" role="status"><p>${label}</p>${p.calibration && state!=="confirmed" && state!=="candidate" ? '<button id="refConfirmChecked" type="button" class="btn">已逐邊核對室內淨輪廓與尺寸</button>' : ""}</div>`;
  }
  function statusHTML(bid, includeOutline=true) {
    const p=active(bid);if(!p)return "";
    return `<p id="refCalibrationStatus" class="ref-status${p.calibration ? "" : " neutral"}">${p.calibration ? `已校準 · ${p.calibration.inputValue} ${p.calibration.inputUnit}` : "未校準 · 請使用圖上已知尺寸"}</p>`+(includeOutline?reconstructionStatusHTML(bid):"");
  }
  function bindPane(pane, bid) {
    pane.querySelector("#refImport")?.addEventListener("click", safe(() => chooseFile(bid)));
    pane.querySelector("#refMorePages")?.addEventListener("click", safe(() => openSource(context().sources.get(active(bid).sourceId), bid)));
    pane.querySelector("#refActivePage")?.addEventListener("change", safe(e => selectPage(bid,e.target.value)));
    pane.querySelector("#refConfirmChecked")?.addEventListener("click", safe(() => { markReconstructionReviewed(bid); redraw(); }));
    pane.querySelector("#refFit")?.addEventListener("click", fitReference);
    pane.querySelector("#refRecordAdd")?.addEventListener("click", safe(() => {
      assertEditable();
      const raw = pane.querySelector("#refRecordValue").value, value = raw.trim()==="" ? null : Number(raw);
      const label = pane.querySelector("#refRecordLabel").value.trim();
      if (!label || (value !== null && (!Number.isFinite(value) || Math.abs(value)>1e8))) { toast("請填項目名稱及有效數值；未知值可留空。"); return; }
      const p = active(bid), records = [...p.records,{ id: uuid(), label, value, unit: pane.querySelector("#refRecordUnit").value,
        location: pane.querySelector("#refRecordLocation").value, datum: pane.querySelector("#refRecordDatum").value }];
      assertPageCapacity(bid,{...p,records});p.records = records;
      dirty(); redraw(); document.getElementById("refRecordDetails").open = true;
    }));
    for (const b of pane.querySelectorAll("[data-ref-remove-record]")) b.addEventListener("click", safe(() => {
      assertEditable();
      const p = active(bid); p.records = p.records.filter(r => r.id !== b.dataset.refRemoveRecord); dirty(); redraw(); document.getElementById("refRecordDetails").open = true;
    }));
  }
  function chooseFile(bid = null) {
    assertEditable(); assertRoomDraftIdle(); if (bid !== null && sharedRoom(bid)) bid = null;
    const input = document.getElementById("referenceFile"); input.dataset.bid = bid ?? ""; input.value = ""; input.click();
  }
  async function openSource(source, bid = null) {
    assertEditable(); assertRoomDraftIdle(); if (bid !== null && sharedRoom(bid)) bid = null;
    if (busy || oc.busy) throw new Error("操作進行中，請稍候。");
    const dialog = document.getElementById("referenceDialog"), token = ++sequence;
    modal = { source, bid, context:context(), targets:new Map([...history.frame.ids].filter(([id]) => !sharedRoom(id))), page: 1, crop: null, width: 1, height: 1, token, zoom: "page", ready: false, drag: null };
    document.getElementById("refZoom").value = "page";
    document.getElementById("refSourceName").textContent = source.meta.name;
    document.getElementById("refPreviewMessage").textContent = "正在讀取來源…";
    document.getElementById("refApply").disabled = true;
    document.getElementById("refPageNumber").disabled = true;
    document.getElementById("refPrev").disabled = true;
    document.getElementById("refNext").disabled = true;
    document.getElementById("refPagePreview").replaceChildren();
    document.getElementById("refThumbnails").replaceChildren();
    const target = document.getElementById("refTarget");
    target.innerHTML = `<option value="new">建立描繪用面（預設矩形）</option>` + oc.faces.filter(f=>f.kind==="boundary" && modal.targets.has(f.id)).map(f=>`<option value="${f.id}">套用至面 ${f.id}</option>`).join("");
    target.value = bid != null && modal.targets.has(bid) ? String(bid) : "new";
    if (!dialog.open) dialog.showModal();
    try {
      const doc = await documentFor(source); if (!modal || modal.token !== token) return;
      assertContext(modal.context);
      modal.count = doc?.numPages || 1;
      document.getElementById("refPageNumber").disabled = false;
      document.getElementById("refPageNumber").max = modal.count;
      document.getElementById("refPageCount").textContent = `/ ${modal.count} 頁`;
      await previewPage(1);
    } catch (e) {
      if (modal?.token === token) document.getElementById("refPreviewMessage").textContent = e.message;
    }
  }
  async function previewPage(number) {
    if (busy || !modal || modal.evidence || !Number.isInteger(modal.count) || !Number.isInteger(number) || number < 1 || number > modal.count) return;
    if (modal.page === number && modal.ready) return;
    const m = modal, request = ++sequence; m.token = request; m.ready = false; m.page = number; m.crop = null;
    document.getElementById("refApply").disabled = true;
    document.getElementById("refPreviewMessage").textContent = "正在讀取第 " + number + " 頁…";
    document.getElementById("refPageNumber").value = number;
    document.getElementById("refPrev").disabled = number === 1;
    document.getElementById("refNext").disabled = number === m.count;
    try {
      assertContext(m.context);
      const r = await renderPage(m.source, number);
      if (modal !== m || m.token !== request) return;
      assertContext(m.context);
      Object.assign(m, { width: r.width, height: r.height, render: r, ready: true, crop: [0,0,r.width,r.height] });
      const host = document.getElementById("refPagePreview");
      host.innerHTML = `<img alt="第 ${number} 頁預覽"><div id="refCropOverlay"></div>`;
      host.querySelector("img").src = r.src; layoutPreview();
      document.getElementById("refPreviewMessage").textContent = "拖曳框選取景範圍；未框選時使用整頁。確認後再校準尺寸。";
      document.getElementById("refApply").disabled = getProjectInfo().editingBlocked; drawCrop();
      // Only five nearby thumbnails are rendered, never the entire document.
      const strip = document.getElementById("refThumbnails"); strip.replaceChildren();
      for (let p = Math.max(1,number-2); p <= Math.min(m.count,number+2); p++) {
        const b = document.createElement("button"); b.type="button"; b.className="ref-thumbnail"; b.setAttribute("aria-label",`第 ${p} 頁`);
        b.setAttribute("aria-current", String(p===number)); b.textContent=String(p); b.onclick=safe(()=>previewPage(p)); strip.append(b);
        const t = p === number ? r : await renderPage(m.source,p,0.15);
        if (modal !== m || m.token !== request) return;
        assertContext(m.context);
        const img = document.createElement("img"); img.alt=""; img.src=t.src; b.prepend(img);
      }
    } catch(e) { if (modal === m && m.token === request) document.getElementById("refPreviewMessage").textContent=e.message; }
  }
  function layoutPreview() {
    if (!modal?.ready) return;
    const host = document.getElementById("refPagePreview"), scroll = host.parentElement;
    const width = Math.max(1, scroll.clientWidth - 24), height = Math.max(1, scroll.clientHeight - 24);
    host.style.width = (modal.zoom === "page" ? Math.min(width, height * modal.width / modal.height) : width * modal.zoom) + "px";
  }
  function drawCrop() {
    if (!modal?.crop) return; const [x,y,w,h]=modal.crop, box=document.getElementById("refCropOverlay"); if (!box) return;
    Object.assign(box.style, { left:100*x/modal.width+"%",top:100*y/modal.height+"%",width:100*w/modal.width+"%",height:100*h/modal.height+"%" });
  }
  function cropPoint(e) {
    const b=document.getElementById("refPagePreview").getBoundingClientRect();
    return [Math.max(0,Math.min(modal.width,(e.clientX-b.left)/b.width*modal.width)),Math.max(0,Math.min(modal.height,(e.clientY-b.top)/b.height*modal.height))];
  }
  async function applySource() {
    assertEditable(); assertRoomDraftIdle();
    if (!modal?.ready || modal.evidence || busy) return;
    // Keep exactly the page and crop confirmed before asynchronous face creation.
    const m={...modal,crop:[...modal.crop]}, dialog=document.getElementById("referenceDialog");
    assertContext(m.context);
    busy=true; dialog.inert=true; document.getElementById("refApply").disabled=true;
    try {
      const id = uuid(), sources = new Map(m.context.sources);sources.set(m.source.meta.id,m.source);
      const pageFor = bb => ({id,sourceId:m.source.meta.id,page:m.page,imgW:m.width,imgH:m.height,crop:[...m.crop],
        mmPerPx:(bb[2]-bb[0])/m.crop[2],x:bb[0]-m.crop[0]*(bb[2]-bb[0])/m.crop[2],y:bb[1]-m.crop[1]*(bb[2]-bb[0])/m.crop[2],
        rot:0,opacity:0.5,locked:false,calibration:null,reviewRequired:false,records:[],src:m.render.src});
      let bid=document.getElementById("refTarget").value;
      if (bid==="new") { bid=await objNewPolyFace({beforeCreate:allocated => {
        assertContext(m.context);assertEditable();assertRoomDraftIdle();
        assertPageCapacity(allocated,pageFor([0,0,4000,3000]),{append:true,sources});
      }}); if (!bid) throw new Error("建立描繪用面失敗。"); }
      else {
        bid=Number(bid);
        assertLegacyTarget(bid);
        if (!m.targets.has(bid) || history.frame.ids.get(bid)!==m.targets.get(bid)) throw new Error("目標面已變更，請重新選擇來源。");
        if (oc.focus?.t !== "face" || oc.focus.id !== bid) await enterFocus("face",bid);
        if (history.frame.ids.get(bid)!==m.targets.get(bid)) throw new Error("目標面已變更，請重新選擇來源。");
      }
      assertContext(m.context);
      assertEditable();
      if (!oc.edit || oc.edit.bid!==bid) throw new Error("目標面已不存在，請重新選擇。");
      assertLegacyTarget(bid); assertRoomDraftIdle();
      const page = pageFor(loopsBBox(oc.bmap[bid]));
      assertPageCapacity(bid,page,{append:true,sources});
      context().sources.set(m.source.meta.id,m.source);
      addPage(bid,page);
      closeSource(true); feSetTool("select"); fiShowTab("underlay"); redraw(); fitReference();
      if (innerWidth <= 680) openPanel("right",document.getElementById("workspaceToggleRight"));
      setStatus("已加入參考頁；請用圖上已知尺寸完成兩點校準。");
    } finally { busy=false; dialog.inert=false; present(); if (modal) document.getElementById("refApply").disabled=!modal.ready || getProjectInfo().editingBlocked; }
  }
  function closeSource(force = false) {
    if (busy && force !== true) return;
    if (modal?.evidence) {
      document.getElementById("refApply").hidden=false;document.getElementById("refTarget").disabled=false;
      for (const id of ["refPageNumber","refPrev","refNext","refResetCrop"]) document.getElementById(id).disabled=false;
    }
    const source=modal?.source;modal=null;sequence++;document.getElementById("referenceDialog").close();
    if(source && context().sources.get(source.meta.id)!==source) {
      // PDF.js 6 exposes destruction on the loading task, not PDFDocumentProxy.
      source.cleanup=releasePDFSource(source);
    }
  }
  function manifestData(c = context(), ids = history.frame.ids) {
    const faces=[], faceProjections=[], reconstructionReviews=[]; const used=new Set();
    for (const [bid,key] of ids) {
      for (const record of c.faceProjections.get(key) || []) faceProjections.push({bid,...record});
      const g=c.groups.get(key); if (!g?.pages.length) continue;
      faces.push({ bid,activePageId:g.activePageId,pages:g.pages.map(p=>{used.add(p.sourceId);return Object.fromEntries(["id","sourceId","page","imgW","imgH","crop","mmPerPx","x","y","rot","opacity","locked","calibration","reviewRequired","records"].map(key=>[key,p[key]]));}) });
      for (const p of g.pages) {const r=c.reconstructionReviews.get(key+":"+p.id);if (r) reconstructionReviews.push({bid,pageId:p.id,...r});}
    }
    const envelope = {schema:P.Features.SCHEMA,records:c.featureAttachments || []};
    P.Features.sourceRooms(envelope,c.sources);P.Features.evidenceLinks(envelope,c.sources,c.id);
    for (const hash of P.Features.sourceIds(envelope)) used.add(hash);
    for (const record of c.scenarioCatalog?.scenarios || []) for (const hash of record.snapshot.assetHashes) used.add(hash);
    const data = { ...(reconstructionReviews.length?{reconstructionReviews}:{}),projectId:c.id,name:c.name,sources:[...used].map(k=>c.sources.get(k).meta),faces,
      ...(c.scenarioCatalog?{scenarioCatalog:c.scenarioCatalog}:{}),
      ...(c.models.length?{models:c.models}:{}),...(faceProjections.length?{faceProjections}:{}),
      ...(c.assemblyDrafts?.length?{assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:c.assemblyDrafts}}:{}),
      ...(c.featureAttachments?.length?{featureAttachments:{schema:P.Features.SCHEMA,records:c.featureAttachments}}:{}),
      ...(c.engineeringDrafts?.length?{engineeringDrafts:{schema:P.DRAFT_SCHEMA,records:c.engineeringDrafts}}:{}) };
    const format = P.projectFormat(data);
    return { ...data,format,...(P.formatPolicy(format).modelCollections?{models:c.models,faceProjections}:{}) };
  }
  function assertMetadataCapacity(overrides = {}, ids = history.frame.ids) {
    const c = {...context(),...overrides};
    if (!c.scenarioCatalog && !c.featureAttachments?.some(record => record.kind === P.Features.ROOM_KIND || record.kind === E.KIND)) return;
    P.assertManifestCapacity(manifestData(c,ids));
  }
  function assertPageCapacity(bid,page,{append = false,replace = false,...overrides} = {}) {
    const c = context(), ids = new Map(history.frame.ids), key = ids.get(bid) || "capacity-proposal";
    ids.set(bid,key);
    const old = c.groups.get(key), groups = new Map(c.groups), pages = replace ? [page] : append ? [...(old?.pages || []),page] : (old?.pages || []).map(p=>p.id === page.id ? page : p);
    groups.set(key,{...old,pages,activePageId:append || replace ? page.id : old?.activePageId});
    assertMetadataCapacity({...overrides,groups},ids);
  }
  async function manifest(c = context(), scene = null) {
    await referencesReady(c); assertContext(c);
    const data = manifestData(c);P.assertManifestCapacity(data,scene);
    return JSON.parse(JSON.stringify(data));
  }
  function assertSaveReady(transactionOwner=null) {
    if(nativePending>0)throw new Error("原生操作結果尚未取得，請等候完成後再保存或凍結試改。");
    if(window.RoomCollectionWorkspace?.hasWork)throw new Error("房間草稿尚未確認。請確認、取消或恢復結果，再保存專案。");
    if(window.RoomOutlineWorkspace?.hasWork)throw new Error("房間輪廓候選尚未確認。請確認或取消候選，再保存專案。");
    if(window.ParameterUI?.pending)throw new Error("參數草稿尚未套用。請先確認或捨棄草稿，再保存專案。");
    assertEditable(transactionOwner);
    if (oc.busy || fe.ulDrag || history.group || pendingLoad) throw new Error("請先完成目前的操作再保存。");
    if (fe.draft?.pts?.length) throw new Error("外環草稿尚未套用。請先完成外環或放棄草稿，再保存專案。");
    if (fe.ulCalib?.pts?.length) throw new Error("校準尚未套用。請先套用比例尺或取消取點，再保存專案。");
  }
  function unchanged(stamp) {
    return context() === stamp.context && history.frame === stamp.frame && revision(stamp.context) === stamp.revision && !pendingLoad;
  }
  function assertSnapshot(stamp,transactionOwner=null) {
    if (!unchanged(stamp)) throw new Error("專案在保存準備期間已變更，請重新保存。");
    assertSaveReady(transactionOwner);
  }
  async function exportSnapshot(c = context(),includeCatalog = true,assertCurrent=()=>{},afterFlush=()=>{},transactionOwner=null,proposal=null) {
    assertCurrent();
    if(!transactionOwner){window.AssemblyWorkspace?.flush();window.InfiniteGridWorkspace?.flush();}
    afterFlush();assertCurrent();
    assertSaveReady(transactionOwner); await referencesReady(c); assertCurrent();assertContext(c); assertSaveReady(transactionOwner);
    const stamp = { context:c, frame:history.frame, revision:revision(c) };
    const r=await api("dump"); if (!r.ok) throw new Error(r.error||"無法讀取場景。");
    assertCurrent();assertSnapshot(stamp,transactionOwner);
    const snapshot=proposal||c,m=includeCatalog?proposal?manifestData(snapshot):await manifest(c,r.text):manifestData({...snapshot,scenarioCatalog:null});
    P.assertManifestCapacity(m,r.text);assertCurrent();assertSnapshot(stamp,transactionOwner);
    await validateEvidenceClosure(snapshot, m.featureAttachments, () => {assertCurrent();assertSnapshot(stamp,transactionOwner);}); assertCurrent();assertSnapshot(stamp,transactionOwner);
    const data=new Map([...snapshot.sources].map(([k,s])=>[k,s.bytes]));
    const bytes=await P.pack(r.text,m,data,fflate); assertCurrent();assertSnapshot(stamp,transactionOwner);
    return {bytes,stamp,scene:r.text,nativeRevision:r.revision??null};
  }
  async function exportBytes() { return (await exportSnapshot()).bytes; }
  async function readScenarioProject(assertCurrent=()=>{},afterFlush=()=>{}) {
    const {bytes,stamp}=await exportSnapshot(context(),false,assertCurrent,afterFlush);assertCurrent();
    const project=await P.unpack(bytes,fflate);assertCurrent();assertSnapshot(stamp);
    return {project,assertCurrent:()=>assertSnapshot(stamp)};
  }
  function readScenarioCatalog() {
    return {catalog:structuredClone(context().scenarioCatalog),sources:new Map([...context().sources].map(([h,s])=>[h,{meta:structuredClone(s.meta),bytes:s.bytes.slice()}]))};
  }
  function commitScenarioCatalog(catalog,sources,assertCurrent=()=>{},transactionOwner=null) {
    assertSaveReady(transactionOwner);assertCurrent();P.ScenarioCatalog.validate(catalog);
    const next=structuredClone(catalog),data=new Map(context().sources);
    for(const [hash,source] of sources)data.set(hash,{meta:structuredClone(source.meta),bytes:source.bytes.slice()});
    const c={...context(),scenarioCatalog:next,sources:data};P.assertManifestCapacity(manifestData(c));
    if(JSON.stringify(context().scenarioCatalog)===JSON.stringify(next))return false;
    assertCurrent();history.push(history.snapshot(),'local','保存候選方案');
    context().scenarioCatalog=next;context().sources=data;dirty();sync();return true;
  }
  const scenarioTicketSchema="scenario-editor-ticket/1";
  const scenarioTicketKey=session=>"geometry-scenario-editor-ticket-"+session;
  const nativeSessionId=value=>typeof value==="string"&&/^[a-f0-9]{32}$/.test(value);
  function storedScenarioTicket(value,count){
    if(count===0)return null;
    if(count!==1||value==null)throw new Error("試改恢復記錄已損壞，保留原資料且不配置新工作階段。");
    return validateScenarioTicket(value);
  }
  async function readStoredScenarioTicket(session){
    let count;const value=await recoveryStore("readonly",store=>{count=store.count(scenarioTicketKey(session));return store.get(scenarioTicketKey(session));});
    return storedScenarioTicket(value,count.result);
  }
  function validateScenarioTicket(value) {
    if(value==null)return null;
    const keys="context,eligible,label,parentCheckpoint,phase,request,retirement,rootSession,scenarioId,schema";
    if(typeof value!=="object"||Array.isArray(value)||Object.keys(value).sort().join(",")!==keys||
       value.schema!==scenarioTicketSchema||!nativeSessionId(value.rootSession)||value.eligible!==false||
       !["creating","initializing","active","retiring"].includes(value.phase)||
       typeof value.scenarioId!=="string"||!value.scenarioId||value.scenarioId.length>4096||
       typeof value.label!=="string"||!value.label||value.label.length>4096||
       !(value.context===null||nativeSessionId(value.context)))throw new Error("試改恢復記錄不完整，原資料已保留。");
    const pin=value.parentCheckpoint;
    if(!pin||Object.keys(pin).sort().join(",")!=="key,packageHash,projectId,sceneHash"||
       typeof pin.key!=="string"||!pin.key||typeof pin.projectId!=="string"||!pin.projectId||
       !/^[a-f0-9]{64}$/.test(pin.sceneHash)||!/^[a-f0-9]{64}$/.test(pin.packageHash))
      throw new Error("試改缺少原方案完整保存位置，未配置工作階段。");
    const r=value.request;
    if(!r||Object.keys(r).sort().join(",")!=="action,requestId,sequence,session"||r.action!=="create"||
       typeof r.requestId!=="string"||!/^[a-f0-9-]{36}$/.test(r.requestId)||!Number.isSafeInteger(r.sequence)||r.sequence<1||
       r.session!==value.rootSession)throw new Error("試改請求身分不完整，未建立或退休任何工作階段。");
    if(value.phase==="creating"&&value.context!==null||["initializing","active"].includes(value.phase)&&!value.context)
      throw new Error("試改階段與原生身分不符，原資料已保留。");
    if(value.phase==="retiring"){
      const retirement=value.retirement;
      if(!retirement||!["cancel","finish"].includes(retirement.reason))throw new Error("試改沒有明確的結束記錄。");
      if(retirement.reason==="cancel"){
        if(Object.keys(retirement).join(",")!=="reason")throw new Error("試改捨棄記錄不完整。");
      }else{
        const p=retirement.checkpoint;
        if(Object.keys(retirement).sort().join(",")!=="checkpoint,reason"||!p||
           Object.keys(p).sort().join(",")!=="key,packageHash,parentKey,projectId,sceneHash"||
           p.key!=="geometry-scenario-finish-receipt-"+value.rootSession||p.parentKey!==pin.key||p.projectId!==pin.projectId||!value.context||
           !/^[a-f0-9]{64}$/.test(p.sceneHash)||!/^[a-f0-9]{64}$/.test(p.packageHash))
          throw new Error("已完成試改缺少可恢復的原方案完整包，未退休B。");
      }
    }else if(value.retirement!==null)throw new Error("試改結束記錄與階段不符。");
    return structuredClone(value);
  }
  function assertScenarioJournalReady() {
    if(scenarioContext())throw new Error("試改記錄只能由原方案管理。");
    assertEditorLease();
    if(editorLease!=="owned"||editorLeaseSession!==connection.session||!nativeSessionId(connection.session)||!recoveryDB||!recoveryKey)
      throw new Error("原方案的編輯權限或本機恢復儲存尚未就緒；未配置試改工作階段。");
  }
  async function readScenarioEditorTicket() {
    assertScenarioJournalReady();const session=connection.session;
    const ticket=await readStoredScenarioTicket(session);
    assertScenarioJournalReady();if(connection.session!==session)throw new Error("服務已變更，試改記錄未轉移。");
    return ticket;
  }
  function scenarioTicketTransaction(expected,next,checkpoint=null,transactionOwner=null) {
    assertScenarioJournalReady();
    const before=validateScenarioTicket(expected),after=validateScenarioTicket(next),session=connection.session;
    if(sceneTransaction&&sceneTransaction!==transactionOwner)throw new Error("原方案資料保全尚未完成，請稍候再結束試改。");
    if((before&&before.rootSession!==session)||(after&&after.rootSession!==session))throw new Error("試改屬於另一服務，未改綁原請求。");
    const key=scenarioTicketKey(session);
    return new Promise((resolve,reject)=>{
      // Acknowledgement is transaction completion, with the strongest standard
      // durability hint. Storage refusal must fail before native allocation.
      const tx=recoveryDB.transaction("projects","readwrite",{durability:"strict"}),store=tx.objectStore("projects");let failure=null;
      const abort=error=>{failure=error;try{tx.abort();}catch(_){reject(error);}};
      tx.onabort=()=>reject(failure||tx.error||new Error("試改恢復記錄交易已中止。"));
      tx.onerror=()=>{failure ||= tx.error||new Error("試改恢復記錄寫入失敗。");};
      tx.oncomplete=()=>{try{assertScenarioJournalReady();if(connection.session!==session)throw new Error("服務已變更，保留原試改記錄。");resolve(after&&structuredClone(after));}catch(error){reject(error);}};
      if(tx.durability!=="strict"){abort(new Error("此瀏覽器未確認嚴格儲存提交，未配置或退休試改工作階段。"));return;}
      const count=store.count(key),request=store.get(key);
      request.onsuccess=()=>{try{
        assertScenarioJournalReady();if(connection.session!==session)throw new Error("服務已變更。");
        const current=storedScenarioTicket(request.result,count.result);
        if(JSON.stringify(current)!==JSON.stringify(before))throw new Error("試改記錄已變更；未覆寫較新的取消或完成決定。");
        if(checkpoint){store.put(checkpoint.record,checkpoint.key);if(checkpoint.receiptKey)store.put(checkpoint.record,checkpoint.receiptKey);}
        if(after)store.put(after,key);else store.delete(key);
      }catch(error){abort(error);}};
      request.onerror=()=>abort(request.error||new Error("無法核對試改恢復記錄。"));
    });
  }
  async function createScenarioEditorTicket({request,scenarioId,label},assertCurrent=()=>{}) {
    assertScenarioJournalReady();assertCurrent();assertSaveReady();
    if(!recoveryReady)throw new Error("原方案完整恢復資料尚未核對，未建立試改。");
    const owner=beginSceneTransaction(),session=connection.session,key=recoveryKey;busy=true;busyLabel="正在保全原方案，再開啟試改…";present();
    try{
      const snapshot=await exportSnapshot(context(),true,assertCurrent,()=>{},owner),c=snapshot.stamp.context;
      const sceneHash=await sceneFingerprint(snapshot.scene),packageHash=await P.sha(snapshot.bytes);assertCurrent();assertSnapshot(snapshot.stamp,owner);
      const record={version:1,session,sceneHash,bytes:snapshot.bytes,updatedAt:new Date().toISOString(),
        project:{dirty:!!c.dirty,dirtyReason:c.dirtyReason||"",saved:!!c.saved,downloaded:!!c.downloaded,provenance:{...c.provenance}}};
      const ticket=validateScenarioTicket({schema:scenarioTicketSchema,rootSession:request?.session,request:structuredClone(request),
        scenarioId,label,parentCheckpoint:{key,sceneHash,packageHash,projectId:c.id},phase:"creating",context:null,eligible:false,retirement:null});
      return await scenarioTicketTransaction(null,ticket,{key,record},owner);
    }finally{finishSceneTransaction(owner);busy=false;busyLabel="";present();scheduleRecovery();}
  }
  async function updateScenarioEditorTicket(expected,patch) {
    const ticket=validateScenarioTicket(expected);
    if(!patch||Object.keys(patch).some(key=>!["phase","context"].includes(key))||
       !(ticket?.phase==="creating"&&patch.phase==="initializing"||ticket?.phase==="initializing"&&patch.phase==="active"))
      throw new Error("試改階段不可倒退或重開。");
    if(ticket.context&&patch.context!==undefined&&patch.context!==ticket.context)throw new Error("不能把試改改綁另一原生工作階段。");
    return scenarioTicketTransaction(ticket,{...ticket,...patch});
  }
  async function markScenarioEditorRetiring(expected,{reason}={}) {
    if(reason!=="cancel")throw new Error("完成試改須先持久保存原方案完整包。");
    const ticket=validateScenarioTicket(expected);
    if(!ticket)throw new Error("沒有可核對的試改記錄。");
    return scenarioTicketTransaction(ticket,{...ticket,phase:"retiring",retirement:{reason:"cancel"}});
  }
  async function verifyScenarioEditorRetirement(expected) {
    const ticket=validateScenarioTicket(expected),current=await readScenarioEditorTicket();
    if(!ticket||ticket.phase!=="retiring"||JSON.stringify(ticket)!==JSON.stringify(current))throw new Error("試改尚未取得相符的結束記錄。");
    if(ticket.retirement.reason==="cancel")return true;
    const pin=ticket.retirement.checkpoint;
    if(pin.parentKey!==recoveryKey||context().id!==pin.projectId)throw new Error("請先核對原分頁的完整專案，B及恢復資料仍保留。");
    const record=await recoveryStore("readonly",store=>store.get(pin.key));
    if(!record||record.session!==ticket.rootSession||record.sceneHash!==pin.sceneHash||await P.sha(record.bytes)!==pin.packageHash)
      throw new Error("原方案完整保存收據不符，未退休B。");
    const project=await P.unpack(record.bytes,fflate),dump=await api("dump");
    if(project.manifest.projectId!==pin.projectId||JSON.stringify(project.manifest.scenarioCatalog)!==JSON.stringify(context().scenarioCatalog)||
       !dump.ok||await sceneFingerprint(dump.text)!==pin.sceneHash||connection.session!==ticket.rootSession)
      throw new Error("原方案或服務已變更，B及完整保存收據仍保留。");
    return true;
  }
  async function clearScenarioEditorTicket(expected) {
    const ticket=validateScenarioTicket(expected);
    if(!ticket||ticket.phase!=="retiring")throw new Error("不能清除尚未結束的試改身份。");
    return scenarioTicketTransaction(ticket,null);
  }
  async function initializeScenarioProject(bytes,name,ticketValue) {
    const ticket=validateScenarioTicket(ticketValue),native=scenarioContext();
    if(!native||native!==connection.session||editorLease!=="owned"||!recoveryDB||scenarioInitializationAttempted||
       ticket?.phase!=="initializing"||ticket.context!==native)throw new Error("試改初始化身份不符；未重新匯入舊方案。");
    const stored=await readStoredScenarioTicket(ticket.rootSession);
    if(JSON.stringify(stored)!==JSON.stringify(ticket))throw new Error("試改已取消或身份已更新；未匯入。");
    scenarioInitializationAttempted=true;scenarioInitializationPermit={};
    try{
      await importBytes(bytes,name);
      const current=await readStoredScenarioTicket(ticket.rootSession);
      if(connection.session!==native||JSON.stringify(current)!==JSON.stringify(ticket))throw new Error("試改初始化終態不再屬於原請求，保留資料等待核對。");
      scenarioBootstrap="ready";recoveryReady=true;scheduleRecovery();return {ok:true,context:native};
    }finally{scenarioInitializationPermit=null;if(scenarioBootstrap!=="ready")recoveryReady=false;}
  }
  async function freezeScenarioProject() {
    if(!scenarioContext()||scenarioFreeze)throw new Error("試改尚未就緒或已在保全中。");
    window.AssemblyWorkspace?.flush();window.InfiniteGridWorkspace?.flush();assertSaveReady();
    const owner=beginSceneTransaction(),session=connection.session,token=uuid();busy=true;busyLabel="正在凍結完整試改資料…";present();
    try{
      const snapshot=await exportSnapshot(context(),true,()=>{if(connection.session!==session||sceneTransaction!==owner)throw new Error("試改工作階段已變更。");},()=>{},owner);
      scenarioFreeze={owner,session,token,...snapshot,sceneHash:await sceneFingerprint(snapshot.scene)};
      return {bytes:snapshot.bytes,freezeToken:token};
    }catch(error){finishSceneTransaction(owner);busy=false;busyLabel="";present();throw error;}
  }
  async function assertScenarioFrozen(token) {
    const frozen=scenarioFreeze;
    if(!frozen||frozen.token!==token||frozen.owner!==sceneTransaction||frozen.session!==connection.session||!unchanged(frozen.stamp))throw new Error("試改保全已過期。");
    const dump=await api("dump");
    if(scenarioFreeze!==frozen||!dump.ok||!unchanged(frozen.stamp)||frozen.session!==connection.session||
       await sceneFingerprint(dump.text)!==frozen.sceneHash||frozen.nativeRevision!==null&&dump.revision!==frozen.nativeRevision)
      throw new Error("試改在保全期間已變更，未完成或退休它。");
    return {ok:true};
  }
  function releaseScenarioProject(token) {
    if(!scenarioFreeze){if(token===lastScenarioRelease)return {ok:true,state:"released"};throw new Error("試改保全身份不符。");}
    if(scenarioFreeze.token!==token)throw new Error("不能解除另一筆試改保全。");
    finishSceneTransaction(scenarioFreeze.owner);scenarioFreeze=null;lastScenarioRelease=token;busy=false;busyLabel="";present();scheduleRecovery();return {ok:true,state:"released"};
  }
  async function finishScenarioEditor(catalog,sources,expected,assertCurrent=()=>{}) {
    assertScenarioJournalReady();assertCurrent();
    window.AssemblyWorkspace?.flush();window.InfiniteGridWorkspace?.flush();assertCurrent.afterFlush?.();assertCurrent();assertSaveReady();
    const ticket=validateScenarioTicket(expected);
    if(ticket?.phase!=="active")throw new Error("試改尚未完整開啟，不能完成。");
    P.ScenarioCatalog.validate(catalog);
    if(!catalog.scenarios.some(s=>s.scenarioId===ticket.scenarioId)||context().id!==ticket.parentCheckpoint.projectId||recoveryKey!==ticket.parentCheckpoint.key)
      throw new Error("試改與原方案保存身份不符，未變更或退休任何資料。");
    const next=structuredClone(catalog),data=new Map(context().sources);
    for(const [hash,source] of sources)data.set(hash,{meta:structuredClone(source.meta),bytes:source.bytes.slice()});
    const proposal={...context(),scenarioCatalog:next,sources:data};P.assertManifestCapacity(manifestData(proposal));
    const owner=beginSceneTransaction(),session=connection.session,key=recoveryKey;busy=true;busyLabel="正在持久保存原方案與試改…";present();
    try{
      const snapshot=await exportSnapshot(context(),true,assertCurrent,()=>{},owner,proposal),c=snapshot.stamp.context;
      const sceneHash=await sceneFingerprint(snapshot.scene),packageHash=await P.sha(snapshot.bytes);assertCurrent();assertSnapshot(snapshot.stamp,owner);
      const record={version:1,session,sceneHash,bytes:snapshot.bytes,updatedAt:new Date().toISOString(),
        project:{dirty:true,dirtyReason:"保存候選方案",saved:!!c.saved,downloaded:false,provenance:{...c.provenance}}};
      record.finishReceipt=packageHash;
      // One bounded immutable Finish backup per root service session. Ordinary
      // recovery never writes here. Replace it only with a later atomic Finish;
      // retain the last backup after retirement instead of deleting user data.
      const receiptKey="geometry-scenario-finish-receipt-"+session;
      const retiring={...ticket,phase:"retiring",retirement:{reason:"finish",checkpoint:{key:receiptKey,parentKey:key,sceneHash,packageHash,projectId:c.id}}};
      const persisted=await scenarioTicketTransaction(ticket,retiring,{key,record,receiptKey},owner);
      // No async gap between the durable commit and the owned in-memory commit.
      assertCurrent();assertSnapshot(snapshot.stamp,owner);
      commitScenarioCatalog(next,data,assertCurrent,owner);
      recoveryFinishReceipt={session,key,hash:packageHash};
      return {ticket:persisted,checkpoint:structuredClone(persisted.retirement.checkpoint)};
    }finally{finishSceneTransaction(owner);busy=false;busyLabel="";present();scheduleRecovery();}
  }
  async function adoptScenario(project,assertCurrent=()=>{}) {
    assertSaveReady();assertCurrent();
    const owner=beginSceneTransaction();busy=true;busyLabel='正在整體採用候選方案…';present();
    try {
    const root=readScenarioCatalog(),bytes=await P.pack(project.scene,project.manifest,project.sources,fflate);
    assertCurrent();const {loaded,c,ids}=await readProjectContext(bytes,'候選方案',()=>{},assertCurrent,true);
    c.scenarioCatalog=root.catalog;
    for(const [hash,source] of root.sources)if(!c.sources.has(hash))c.sources.set(hash,source);
    c.dirty=true;c.saved=false;c.provenance={...context().provenance};
    P.assertManifestCapacity(manifestData(c,new Map(ids)),loaded.scene);assertCurrent();
    const r=await uploadScene(loaded.scene,{context:c,ids,manifest:loaded.manifest,action:'整體採用候選方案'},assertCurrent,owner);
    if(!r.ok)throw new Error(r.error||'方案未採用。');
    resetSceneFocus();sync();await refreshActive();return true;
    }finally{if(pendingLoad?.transaction!==owner)finishSceneTransaction(owner);busy=false;busyLabel='';present();scheduleRecovery();}
  }
  function download(bytes,name) {
    const url=URL.createObjectURL(new Blob([bytes],{type:"application/zip"})),a=document.createElement("a");
    a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
  }
  async function save() {
    if (busy || oc.busy) throw new Error("操作進行中，請稍候。");
    window.AssemblyWorkspace?.flush();
    window.InfiniteGridWorkspace?.flush();
    const shellState=window.WorkspaceShell?.saveState();
    if(shellState?.blocked)throw new Error(shellState.reason || "請先套用或放棄目前視窗的草稿。");
    assertSaveReady();
    // Request the handle while user activation is still available.
    const c=context(), suggested=c.name.replace(/[\\/:*?"<>|]/g,"_")+".gcanvas";
    const handlePromise=window.showSaveFilePicker ? window.showSaveFilePicker({suggestedName:suggested,types:[{description:"構形 Canvas 專案",accept:{"application/zip":[".gcanvas"]}}]}) : null;
    busy=true; busyLabel="正在保存專案…"; busyShort="保存中"; present();
    window.InfiniteGridWorkspace?.setProjectBusy(true);
    try {
      let handle;
      try { handle=handlePromise && await handlePromise; } catch(e) { if(e.name==="AbortError")return;throw e; }
      assertContext(c);
      const {bytes,stamp}=await exportSnapshot(c);
      if(handle){const writable=await handle.createWritable();try{await writable.write(bytes);await writable.close();}catch(e){await writable.abort().catch(()=>{});throw e;}
        c.provenance.lastSavedAt=new Date().toISOString();
        if (unchanged(stamp)) {
          c.dirty=false;c.modelsDirty=false;c.faceProjectionsDirty=false;c.saved=true;c.downloaded=false;setStatus("✓ 專案已保存，包含場景、工程來源與草稿、參考資料及空間模型");
        } else {
          c.dirty=true;c.downloaded=false;
          setStatus(context()===c?"檔案已寫入；保存期間的新變更尚未保存，請再次保存。":"先前專案的檔案已寫入；目前專案的保存狀態未變更。");
        }}
      else {assertSnapshot(stamp);download(bytes,suggested);c.downloaded=true;c.provenance.lastDownloadAt=new Date().toISOString();setStatus("已產生專案下載；請確認下載完成後再關閉。");}
    } finally {busy=false;busyLabel="";busyShort="處理中";window.InfiniteGridWorkspace?.setProjectBusy(false);present();scheduleRecovery();}
  }
  function sameModelData(a, b) {
    const ordered = value => Array.isArray(value) ? value.map(ordered) : value && typeof value === "object"
      ? Object.fromEntries(Object.keys(value).sort().map(key => [key, ordered(value[key])])) : value;
    return JSON.stringify(ordered(a)) === JSON.stringify(ordered(b));
  }
  async function verifyStoredModel(model) {
    const packageKeys = ["space", "volume", "clearance", "walls", ...(model.result.schema === "geometry-space-preview/2" ? ["timbers"] : [])];
    for (const key of packageKeys) {
      const pkg = model.result[key]; if (pkg === null) continue;
      const response = await fetch("/model/verify", {method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify(pkg),signal:AbortSignal.timeout(30000)});
      if (!response.ok) throw new Error("空間模型驗證服務失敗（HTTP "+response.status+"），未變更目前專案。");
      const verified = await response.json();
      try { P.validateModelPackage(verified); }
      catch (_) { throw new Error("空間模型「"+model.name+"」驗證失敗："+(verified.error || verified.message || verified.code || verified.diagnostics?.[0]?.message || "模型內容或版本不一致")+"。未變更目前專案。"); }
    }
    if (model.result.timbers && await P.sha(new TextEncoder().encode(model.result.timbers.definitions.base_scene)) !== model.result.source_sha256)
      throw new Error("空間模型「"+model.name+"」的角材來源摘要不一致，未變更目前專案。");
    // A valid mesh alone cannot establish that the displayed height/settings describe
    // that mesh. Replay the saved declarations, never the current canvas world.
    const response = await fetch("/model/space-replay", {method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({input:model.input,result:model.result}),signal:AbortSignal.timeout(30000)});
    if (!response.ok) throw new Error("空間設定核對服務失敗，未變更目前專案。");
    const rebuilt = await response.json(), original = model.result;
    if (rebuilt.ok !== true || rebuilt.schema !== original.schema || rebuilt.source_sha256 !== original.source_sha256)
      throw new Error("空間模型「"+model.name+"」的來源設定無法重建，未變更目前專案。");
    for (const key of packageKeys) {
      if ((rebuilt[key] === null) !== (original[key] === null) || (original[key] !== null &&
          ["definitions", "request", "derived"].some(field => !sameModelData(rebuilt[key]?.[field], original[key][field]))))
        throw new Error("空間模型「"+model.name+"」的設定與模型不一致，未變更目前專案。");
    }
    const {wall_diagnostics: oldDiagnostics, ...oldSummary} = original.summary;
    const {wall_diagnostics: newDiagnostics, ...newSummary} = rebuilt.summary || {};
    if (!sameModelData(oldSummary, newSummary)) throw new Error("空間模型「"+model.name+"」的摘要與定義不一致，未變更目前專案。");
  }
  async function openProject(readBytes,name="匯入專案",onOpened=null,options={}) {
    assertWritableLease(); assertRoomDraftIdle();
    if (busy || oc.busy || history.group || pendingLoad) throw new Error("請先完成目前的操作再開啟專案。");
    const stamp={context:context(),frame:history.frame,revision:revision(context())};
    const assertCurrent=()=>{
      if (!unchanged(stamp)) throw new Error("開啟專案期間目前工程已有變更，未替換目前專案；請再次開啟。");
    };
    const indicator=document.getElementById("busyIndicator"), previousHTML=indicator?.innerHTML;
    const stage=(label,short="讀取中")=>{
      busyLabel=label;busyShort=short;
      if(indicator){indicator.innerHTML='<span class="busy-spinner"></span><span>'+escape(label)+'</span>';indicator.hidden=false;}
      present();setStatus(label);
    };
    busy=true;stage("正在讀取專案…");
    try {
      const bytes=await readBytes();assertCurrent();
      const loaded=await importProjectData(bytes,name,stage,assertCurrent,options);
      recoveryReady=!!recoveryDB && !!recoveryKey;
      if(onOpened){
        stage("正在開啟工程規格…");await onOpened(loaded);
        setStatus(context().dirtyReason ? "✓ 已開啟專案；畫布已自動排版，請保存以保留排列。" : "✓ 已開啟專案「"+context().name+"」與工程規格");
      }
      return loaded;
    } catch(error) {
      setStatus("未能完成開啟專案："+(error.message || "請重試。"));throw error;
    } finally {
      busy=false;busyLabel="";busyShort="處理中";
      if(indicator){indicator.hidden=true;indicator.innerHTML=previousHTML;}
      present();scheduleRecovery();
    }
  }
  function importBytes(bytes,name="匯入專案") { return openProject(()=>bytes,name); }
  async function readProjectContext(bytes,name,stage,assertCurrent,verifyOnly=false) {
    stage("正在檢查專案完整性…","驗證中");
    const loaded=await P.unpack(bytes,fflate); assertCurrent();
    // Detached, private copies are the exact values subsequently committed.
    loaded.manifest=structuredClone(loaded.manifest);
    loaded.sources=new Map([...loaded.sources].map(([hash,data])=>[hash,data.slice()]));
    const m=loaded.manifest,c=fresh();c.id=m.projectId;c.name=m.name||name;c.saved=true;
    assertCurrent();
    // Rebuild every embedded package before uploading anything. Stored definitions
    // are self-contained and do not depend on the current live source scene.
    for (const [index,model] of m.models.entries()) {
      stage("正在驗證空間模型（"+(index+1)+"／"+m.models.length+"）…","驗證中");
      await verifyStoredModel(model);assertCurrent();
    }
    c.models=JSON.parse(JSON.stringify(m.models));
    c.assemblyDrafts=JSON.parse(JSON.stringify(m.assemblyDrafts?.records||[]));
    c.featureAttachments=JSON.parse(JSON.stringify(m.featureAttachments?.records||[]));
    c.engineeringDrafts=JSON.parse(JSON.stringify(m.engineeringDrafts?.records||[]));
    for(const meta of m.sources)c.sources.set(meta.id,{meta:structuredClone(meta),bytes:loaded.sources.get(meta.id).slice()});
    if(m.scenarioCatalog){
      stage('正在隔離驗證候選方案…','驗證中');
      await ScenarioIntegration.read(m.scenarioCatalog,c.sources,assertCurrent);assertCurrent();
      for(const record of m.scenarioCatalog.scenarios){
        const project={manifest:record.snapshot.projectManifest,scene:record.snapshot.worldScene,
          sources:new Map(record.snapshot.assetHashes.map(h=>[h,loaded.sources.get(h)]))};
        const leafBytes=await P.pack(project.scene,project.manifest,project.sources,fflate);assertCurrent();
        await readProjectContext(leafBytes,record.label,stage,assertCurrent,false);assertCurrent();
      }
      c.scenarioCatalog=structuredClone(m.scenarioCatalog);
    }
    await validateEvidenceClosure(c,m.featureAttachments,assertCurrent); assertCurrent();
    async function verifySourcePage(sourceId, number, width, height) {
      const source = c.sources.get(sourceId);
      if (source.meta.type === "application/pdf") {
        const doc = await documentFor(source,assertCurrent); assertCurrent();
        if (number > doc.numPages) throw new Error("來源關聯的 PDF 頁碼不存在。");
        const page = await doc.getPage(number); assertCurrent();
        const size = page.getViewport({scale:1});
        if (Math.abs(size.width-width)>0.01 || Math.abs(size.height-height)>0.01) throw new Error("來源頁面尺寸不一致。");
      } else {
        const image = await imageFor(source);
        if (image.naturalWidth !== width || image.naturalHeight !== height) throw new Error("來源圖片尺寸不一致。");
      }
      assertCurrent();
    }
    for (const plane of P.Features.sourceRooms(m.featureAttachments || {schema:P.Features.SCHEMA,records:[]})?.planes || [])
      await verifySourcePage(plane.sourceId, plane.page, ...plane.pageSize);
    const ids=[],keys=new Map();
    const keyFor = bid => { if(!keys.has(bid)){const key=uuid();keys.set(bid,key);ids.push([bid,key]);}return keys.get(bid); };
    for(const record of m.faceProjections){
      const key=keyFor(record.bid),records=c.faceProjections.get(key)||[];
      records.push({placement_id:record.placement_id,projection:JSON.parse(JSON.stringify(record.projection))});c.faceProjections.set(key,records);
    }
    for (const record of m.reconstructionReviews || []) {
      const {bid,pageId,...value}=record;c.reconstructionReviews.set(keyFor(bid)+":"+pageId,value);
    }
    for(const f of m.faces){
      stage("正在還原參考資料…");
      const key=keyFor(f.bid);
      // Never trust runtime fields (for example a remote image src) from a project file.
      const pages=f.pages.map(p=>P.reference(p));
      for(const p of pages){
        await verifySourcePage(p.sourceId,p.page,p.imgW,p.imgH);
      }
      const g={activePageId:f.activePageId,pages};
      await preparePage(g.pages.find(p=>p.id===g.activePageId),c.sources.get(g.pages.find(p=>p.id===g.activePageId).sourceId));c.groups.set(key,g);
      assertCurrent();
    }
    assertCurrent();
    if(verifyOnly){
      await ScenarioIntegration.verifyProject(loaded,assertCurrent);assertCurrent();
    }
    return {loaded,c,ids};
  }
  async function importProjectData(bytes,name,stage,assertCurrent,options={}) {
    const {loaded,c,ids}=await readProjectContext(bytes,name,stage,assertCurrent);
    c.saved=options.source!=="example";
    c.provenance={kind:options.source==="example"?"example":"file",label:options.source==="example"?"內建範例「"+c.name+"」":"專案檔案「"+name+"」",openedAt:new Date().toISOString(),lastSavedAt:null,lastDownloadAt:null};
    assertCurrent();stage("正在載入專案場景…","載入中");
    const r=await uploadScene(loaded.scene,{context:c,ids,manifest:loaded.manifest,action:"開啟專案「"+c.name+"」"},assertCurrent);
    if(!r.ok)throw new Error(r.error||"場景載入失敗。");
    curScene={path:r.path||"",name:c.name+".gcanvas"};
    resetSceneFocus();sync();document.getElementById("sceneMenuLabel").textContent=sceneMenuDisplay(curScene.name);
    stage("正在整理畫布…","載入中");
    importRenderingContext=c;
    try {await refreshActive();} finally {importRenderingContext=null;}
    setStatus(c.dirtyReason ? "✓ 已開啟專案；畫布已自動排版，請保存以保留排列。" : "✓ 已開啟專案，場景、工程來源與草稿、參考資料及空間模型已還原");return loaded;
  }
  async function replaceWithEmpty(keepIdentity) {
    assertWritableLease(); assertRoomDraftIdle();
    if(busy || oc.busy || history.group || pendingLoad)throw new Error("請先完成目前的操作。");
    const explanation=keepIdentity ? "清空目前專案的幾何、參考資料、空間模型與工程草稿，保留專案名稱及識別。" : "建立一份空白新專案，切換為新的專案識別及「未命名專案」。";
    const warning=context().dirty ? "目前尚未保存的變更不會自動寫入檔案。" : "";
    if(!window.confirm(explanation+warning+"本次切換可一步復原；僅保存在本頁的形狀特徵參數不會恢復。確定繼續嗎？"))return false;
    const previous=context(),c=fresh(),stamp={context:previous,frame:history.frame,revision:revision(previous)};
    if(keepIdentity){c.id=previous.id;c.name=previous.name;c.provenance={...previous.provenance};c.dirty=true;c.saved=previous.saved;}
    else c.provenance={kind:"new",label:"本頁建立的新專案",openedAt:new Date().toISOString(),lastSavedAt:null,lastDownloadAt:null};
    busy=true;busyLabel=keepIdentity?"正在清空專案內容…":"正在建立新專案…";present();
    try {
      const r=await uploadScene("reset\n",{context:c,ids:[],action:keepIdentity?"清空專案「"+c.name+"」內容":"建立新專案"},()=>{if(!unchanged(stamp))throw new Error("目前專案已變更，請重新操作。");});
      if(!r.ok)throw new Error(r.error || "未能完成專案切換。");
      curScene={path:r.path || "",name:c.name+".gcanvas"};resetSceneFocus();sync();
      document.getElementById("sceneMenuLabel").textContent=sceneMenuDisplay(curScene.name);
      await refreshActive();recoveryReady=!!recoveryDB && !!recoveryKey;setStatus(keepIdentity?"✓ 已清空專案內容，保留專案名稱；可復原。":"✓ 已建立空白新專案；可復原回上一份專案。");return true;
    } finally {busy=false;busyLabel="";present();scheduleRecovery();}
  }
  async function cancelProjectScene(token) {
    const response=await fetch("/upload/cancel",{method:"POST",body:JSON.stringify(token),signal:AbortSignal.timeout(30000)});
    if(!response.ok || (await response.json()).ok!==true)throw new Error("無法確認專案候選已取消；目前場景未被替換。");
  }
  async function prepareProjectScene(text,manifest,assertCurrent) {
    let token=null;
    try {
      const response=await fetch("/upload/prepare",{method:"POST",body:text,signal:AbortSignal.timeout(30000)});
      if(!response.ok)throw new Error("目前服務無法驗證專案，未變更目前專案。");
      const candidate=await response.json();
      if(candidate.ok!==true)throw new Error(candidate.error||"場景驗證失敗。");
      if(!Number.isInteger(candidate.token)||candidate.token<1||candidate.token>4294967295)throw new Error("服務未回傳有效的專案候選識別。");
      token=candidate.token;
      assertWritableLease();assertCurrent();
      P.validateProjectObjectRefs(manifest,candidate.final_objects);
      P.assertProjectCapabilities(manifest,P.readerCapabilities(candidate.capabilities));
      P.validateProjectCapabilities(candidate.required_capabilities);
      const policy=P.formatPolicy(manifest.format);
      if (policy.engineeringCandidate) {
        if(policy.canonicalScene&&typeof candidate.final_scene!=="string")
          throw new Error("服務未提供原生候選場景，未變更目前專案。");
        const finalScene=policy.canonicalScene?candidate.final_scene:text;
        if (manifest.featureAttachments && P.Features.evidenceLinks(manifest.featureAttachments)) {
          const response = await fetch("/sources/snapshot",{method:"POST",headers:{"Content-Type":"text/plain;charset=utf-8"},body:finalScene,signal:AbortSignal.timeout(30000)}); assertCurrent();
          if (!response.ok) throw new Error("無法驗證候選參數證據，未變更目前專案。");
          const graph = await response.json(); assertCurrent();
          P.validateEvidenceTargets(manifest,graph);
        }
        if(!sameModelData([...candidate.required_capabilities].sort(),P.sceneCapabilities(finalScene)))
          throw new Error("工程場景能力與保存來源不一致，未變更目前專案。");
      }
      return token;
    } catch(error) {
      if(token!==null)try{await cancelProjectScene(token);}catch(_){}
      throw error;
    }
  }
  function assertLoadContext(load,result=null) {
    assertWritableLease();
    if(context()!==load.guard.context || history.frame!==load.guard.frame || revision(context())!==load.guard.revision || contextConflict!==load.guard.conflict || connection.session!==load.guard.session || result&&Number.isSafeInteger(result.revision)&&nativeRevision>result.revision)
      throw new Error("載入結果晚到，目前工程已有變更；未替換目前專案資料，請重新開啟。");
  }
  async function uploadScene(text,replacement=null,assertCurrent=()=>{},transaction=null) {
    assertWritableLease(); assertRoomDraftIdle();
    if(pendingLoad || preparingSceneLoad)throw new Error("請先確認上一筆場景載入結果再開啟。");
    assertCurrent();
    const owner=transaction||beginSceneTransaction();if(sceneTransaction!==owner)throw new Error('場景載入交易已過期。');
    preparingSceneLoad=true;
    let nextLoad;
    try {
      const before = await api("dump");
      assertWritableLease();assertCurrent();
      if (!before.ok) throw new Error(before.error || "無法讀取載入前的場景。");
      nextLoad = { text, before: before.text, beforeRevision:before.revision, manifest:replacement?.manifest, context: replacement?.context || fresh(), ids: replacement?.ids, action:replacement?.action || null, isolateHistory:contextConflict,
        transaction:owner,guard:{context:context(),frame:history.frame,revision:revision(context()),conflict:contextConflict,session:connection.session} };
    } catch(error) {preparingSceneLoad=false;finishSceneTransaction(owner);throw error;}
    let result,token=null;
    try {
      if(replacement?.manifest)token=await prepareProjectScene(text,replacement.manifest,assertCurrent);
      assertWritableLease();assertCurrent();nextLoad.token=token;pendingLoad=nextLoad;
    } catch(error) {
      if(token!==null)try{await cancelProjectScene(token);}catch(_){}
      finishSceneTransaction(owner);
      throw error;
    } finally {preparingSceneLoad=false;}
    try {
      const r=await fetch(token===null?"/upload":"/upload/confirm",{method:"POST",body:token===null?text:JSON.stringify(token),signal:AbortSignal.timeout(30000)});
      if(!r.ok)throw new Error("場景載入失敗（HTTP "+r.status+"）。");
      result=await r.json();
      if(!result || typeof result.ok!=="boolean")throw new Error("服務未回傳有效的載入結果。");
    } catch(e) {
      connectionFailed("無法確認載入結果，已暫停編輯。請確認服務後重試。");
      throw e;
    }
    try{assertLoadContext(nextLoad,result);}catch(error){pendingLoad=null;finishSceneTransaction(owner);contextConflict=true;sync();throw error;}
    observeNativeRevision(result);
    if(result.ok){adoptLoadedContext();notifySceneChange();}
    pendingLoad=null;finishSceneTransaction(owner);sync();
    return result;
  }
  function adoptLoadedContext() {
    if(pendingLoad.isolateHistory){
      // The native predecessor belongs to the other tab. Do not attach this
      // tab's old references or drafts when undo returns to that predecessor.
      history.undo=[];history.redo=[];history.group=null;history.blockCoreRedo=false;
      history.frame={context:fresh(),ids:new Map()};
    }
    history.replace(pendingLoad.context,pendingLoad.ids,pendingLoad.action);contextConflict=false;
  }
  async function recoverLoad() {
    if (!pendingLoad) return true;
    const load=pendingLoad;assertLoadContext(load);
    let terminal=null;
    if(load.token!=null){
      // Cancellation and confirmation share the server/native lock. A terminal
      // cancellation invalidates even a confirm request that has not arrived yet.
      const response=await fetch("/upload/cancel",{method:"POST",body:JSON.stringify(load.token),signal:AbortSignal.timeout(30000)});
      if(!response.ok)throw new Error("仍無法確認專案載入終態，已保留目前專案並暫停編輯。");
      terminal=await response.json();assertLoadContext(load);
      if(!["cancelled","committed","rejected"].includes(terminal.state))throw new Error("服務未能確認專案載入終態，請保持目前專案並重新連接服務。");
    }
    const dump = await api("dump"); if (!dump.ok) return false;
    assertLoadContext(load);
    const normalized = s => s.replace(/\r\n/g,"\n").trim();
    const old = normalized(dump.text) === normalized(pendingLoad.before);
    const next = normalized(dump.text) === normalized(pendingLoad.text);
    let restoredNew = false, restoredPath = "";
    if(terminal){
      if(terminal.state==="committed" && terminal.ok===true){
        if(!Number.isSafeInteger(terminal.revision) || dump.revision!==terminal.revision || !terminal.scene_sha256 || await P.sha(new TextEncoder().encode(dump.text))!==terminal.scene_sha256){
          contextConflict=true;throw new Error("載入後的場景已有其他變更，未替換目前專案資料；請重新開啟。");
        }
        assertLoadContext(load);adoptLoadedContext();restoredNew=true;restoredPath=terminal.path||"";
      } else if(!old || Number.isSafeInteger(load.beforeRevision)&&dump.revision!==load.beforeRevision){contextConflict=true;throw new Error("取消載入後場景已變更，請重新開啟目前專案。");}
    }
    else if (next && !old) { adoptLoadedContext(); restoredNew=true; }
    else if (!(old && !next)) {
      // The user pressed retry; repeat the pending load if identical worlds make its outcome ambiguous.
      const token=load.manifest?await prepareProjectScene(load.text,load.manifest,()=>assertLoadContext(load)):null;
      assertLoadContext(load);
      const response = await fetch(token===null?"/upload":"/upload/confirm",{method:"POST",body:token===null?load.text:JSON.stringify(token),signal:AbortSignal.timeout(30000)});
      if (!response.ok) throw new Error("仍無法確認場景載入結果。");
      const r = await response.json(); if (r.ok !== true) throw new Error(r.error || "重試載入失敗。");
      assertLoadContext(load);
      // Earlier core history remains usable, but unprovable reference associations must not be guessed.
      history.undo=[];history.redo=[];history.group=null;history.blockCoreRedo=false;history.frame={context:fresh(),ids:new Map()};
      adoptLoadedContext();
      restoredNew=true;restoredPath=r.path||"";
      toast("已重新載入；連線中斷期間的來源歷史無法確認，較早步驟的底圖需從專案重開。");
    }
    if (restoredNew) {
      curScene={path:restoredPath,name:pendingLoad.context.groups.size||pendingLoad.context.models.length||pendingLoad.context.faceProjections.size?pendingLoad.context.name+".gcanvas":"已恢復場景"};
      document.getElementById("sceneMenuLabel").textContent=sceneMenuDisplay(curScene.name);
      markSceneItem();
    }
    pendingLoad=null;finishSceneTransaction(load.transaction);sync();return true;
  }
  function mayLeave() {
    if (window.RoomCollectionWorkspace?.hasWork) {toast("請先完成、取消或恢復目前房間草稿，再切換專案。"); return false;}
    if(window.DraftGate && !window.DraftGate.ask())return false;
    if (Object.values(fe.feats || {}).some(items => items.length) &&
      !window.confirm("目前有只能在本次工作階段修改數字的形狀特徵。切換場景後仍保留輪廓，但特徵參數會消失。要繼續嗎？")) return false;
    return !context().dirty || window.confirm("目前專案有尚未保存的變更。要離開目前專案嗎？");
  }
  function init() {
    for (const type of ["pointerdown", "pointerup", "click", "dblclick", "keydown", "input", "change", "wheel"]) document.addEventListener(type,e=>{
      if(busy){e.preventDefault();e.stopImmediatePropagation();}
    },{capture:true,passive:false});
    document.getElementById("btnImportReference").onclick=safe(()=>chooseFile(oc.edit?.bid ?? null));
    document.getElementById("btnSaveProject").onclick=safe(save);
    document.addEventListener("click", safe(e => {
      const button = e.target.closest("[data-project-action]");
      if (!button) return;
      const action = button.dataset.projectAction;
      button.closest("details")?.removeAttribute("open");
      if (action === "save") safe(save)();
      else if (action === "import") chooseFile(oc.edit?.bid ?? null);
      else if (action === "open") document.getElementById("btnOpenProject").click();
      else if (action === "name") document.getElementById("btnProjectName").click();
      else if (action === "export") document.getElementById("btnExport").click();
      else if (action === "reference") { fiShowTab("underlay"); if (innerWidth <= 680) openPanel("right",document.getElementById("workspaceToggleRight")); }
    }));
    document.getElementById("btnOpenProject").onclick=safe(()=>{assertWritableLease();if(mayLeave()){const i=document.getElementById("projectFile");i.value="";i.click();}});
    document.getElementById("projectFile").onchange=safe(async e=>{const f=e.target.files[0];if(!f)return;if(f.size>P.MAX_PACKAGE)throw new Error("專案檔案超過 256 MB。");try{await openProject(async()=>new Uint8Array(await f.arrayBuffer()),f.name);}finally{e.target.value="";}});
    document.getElementById("referenceFile").onchange=safe(async e=>{
      assertEditable();
      const input=e.target, f=input.files[0], c=context(), bid=input.dataset.bid===""?null:Number(input.dataset.bid);
      if(!f)return;
      const key=history.frame.ids.get(bid), request=++sequence; input.value="";
      const source=await sourceFromFile(f);
      if(request!==sequence)return;
      assertEditable();
      assertContext(c);
      if(bid!==null && history.frame.ids.get(bid)!==key)throw new Error("目標面已變更，請重新選擇來源。");
      await openSource(source,bid);
    });
    document.getElementById("refClose").onclick=closeSource;
    document.getElementById("referenceDialog").addEventListener("cancel",e=>{e.preventDefault();closeSource();});
    document.getElementById("refApply").onclick=safe(applySource);
    document.getElementById("refPageNumber").onchange=safe(e=>previewPage(Number(e.target.value)));
    document.getElementById("refPrev").onclick=safe(()=>previewPage(modal.page-1));
    document.getElementById("refNext").onclick=safe(()=>previewPage(modal.page+1));
    document.getElementById("refResetCrop").onclick=()=>{if(modal?.ready&&!modal.evidence){modal.crop=[0,0,modal.width,modal.height];drawCrop();}};
    document.getElementById("refZoom").onchange=e=>{if(modal){modal.zoom=e.target.value === "page" ? "page" : Number(e.target.value);layoutPreview();}};
    new ResizeObserver(layoutPreview).observe(document.querySelector(".ref-preview-scroll"));
    const preview=document.getElementById("refPagePreview");
    preview.onpointerdown=e=>{if(!modal?.ready||modal.evidence||e.button!==0)return;e.preventDefault();modal.drag=cropPoint(e);preview.setPointerCapture(e.pointerId);};
    preview.onpointermove=e=>{if(!modal?.drag)return;const p=cropPoint(e),s=modal.drag;modal.crop=[Math.min(p[0],s[0]),Math.min(p[1],s[1]),Math.max(1,Math.abs(p[0]-s[0])),Math.max(1,Math.abs(p[1]-s[1]))];drawCrop();};
    preview.onpointerup=()=>{if(modal&&!modal.evidence){modal.drag=null;if(!modal.ready||!modal.crop)return;if(modal.crop[2]<2||modal.crop[3]<2)modal.crop=[0,0,modal.width,modal.height];drawCrop();}};
    preview.onpointercancel=preview.onpointerup;
    document.getElementById("btnProjectName").onclick=safe(()=>{assertEditable();const n=prompt("專案名稱",context().name);if(n?.trim()){assertEditable();const name=n.trim().slice(0,200);assertMetadataCapacity({name});context().name=name;dirty();sync();}});
    window.addEventListener("beforeunload",e=>{if(context().dirty || Object.values(fe.feats || {}).some(items => items.length)){e.preventDefault();e.returnValue="";}});
    present();
  }
  return { getEvidenceState,getEvidenceNavigationStamp,beginNativeOperation,observeNativeRevision,readEvidenceDocument,getReferenceNavigationStamp,prepareReferencePage,commitPreparedReferencePage,validateEvidenceClosure,
    init,observe,adoptLegacy,calibrated,changed,remove,paneHTML,statusHTML,present,bindPane,active,group,context,history,
    reconstructionState,reconstructionStatusHTML,markReconstructionReviewed,documentFor,library,tracingFeatures,sourceFromFile,openSource,renderPage,preparePage,addPage,selectPage,chooseFile,fitReference,
    addSpaceModel,updateSpaceModel,removeSpaceModel,getSpaceModels,tryLocalHistory,
    getFaceProjection,getFaceProjections,setFaceProjection,
    readFeatureAttachment,setFeatureAttachment,getRoomIntegration:()=>roomIntegration,
    getAssemblyDrafts,setAssemblyDraft,removeAssemblyDraft,getEngineeringDrafts,setEngineeringDraft,removeEngineeringDraft,getProjectState,getModelOperationState,getProjectInfo,restoreSession,retryRecovery,persistSession,assertEditable,assertWritableLease,
    assertAssemblyIdle,beginAssemblyConfirmation,assemblyConfirmationCurrent,finishAssemblyConfirmation,
    prepareFeatureConfirmation,beginFeatureConfirmation,cancelFeatureConfirmation,hasFeatureConfirmation:token=>featureConfirmations.has(featureTokenKey(token)),
    featureConfirmationPending:()=>!!assemblyConfirmation?.featureCommand,
    newProject:()=>replaceWithEmpty(false),clearContents:()=>replaceWithEmpty(true),
    noteSceneSource:({name,kind="scene-file"})=>markSceneSource(name,kind),
    manifest,readScenarioProject,readScenarioCatalog,commitScenarioCatalog,adoptScenario,exportBytes,importBytes,openProject,uploadScene,recoverLoad,mayLeave,sync,save,escape,
    readScenarioEditorTicket,createScenarioEditorTicket,updateScenarioEditorTicket,markScenarioEditorRetiring,verifyScenarioEditorRetirement,clearScenarioEditorTicket,
    initializeScenarioProject,freezeScenarioProject,assertScenarioFrozen,releaseScenarioProject,finishScenarioEditor,
    historyActionLabel:op=>history.actionLabel(op),get busy(){return busy;} };
})();
