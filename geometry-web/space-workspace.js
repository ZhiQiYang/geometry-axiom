/* Explicit D21/D22 modeling workspace. A preview never changes the source world. */
"use strict";
window.SpaceModelWorkspace = (() => {
  const $ = id => document.getElementById(id);
  const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const copy = v => JSON.parse(JSON.stringify(v));
  const DEFAULT_WALL_HEIGHT = 3000;
  const EXAMPLE_PROJECTION = {kind:"space-boundary-plan",view:"top",region:"interior",wallSide:"outside"};
  const state = { source: null, result: null, input: null, revision: 0, previewRevision: -1, sequence: 0, phase: "empty", createdId: null, examples: null, viewer: null, controller: null, readonly: false, editing: null, committingId: null, recordSignature: null, projectionPending: false, projectionSequence: 0 };
  let draft = null, viewerLoad = null, viewerOpenSequence = 0;
  let savedContext=null, snapshotNavigation=null;
  function clearSnapshotNavigation(){snapshotNavigation=null;state.viewer?.setSelectableRoots([]);state.viewer?.selectRoot(null);}
  function snapshotRecord(){
    if(!dialog.open||$('smMain').hidden||!state.readonly||state.editing||savedContext!==ReferenceWorkspace.context())return null;
    const records=ReferenceWorkspace.getSpaceModels().filter(m=>m.id===state.createdId);
    return records.length===1&&JSON.stringify(records[0])===state.recordSignature?records[0]:null;
  }
  function authorizeSnapshotSchedule(record,schedule,{isCurrent=()=>false}={}){
    if(!schedule){clearSnapshotNavigation();return false;}
    const current=snapshotRecord();
    if(!current||JSON.stringify(current)!==JSON.stringify(record)||!isCurrent()||schedule.modelId!==current.id)return false;
    snapshotNavigation={ids:new Set(schedule.ids),isCurrent};
    state.viewer.setSelectableRoots(current.input.timbers);
    return true;
  }
  function selectSnapshotTimber(id,focus=true){
    if(!snapshotRecord()||!snapshotNavigation?.isCurrent()||id!==null&&!snapshotNavigation.ids.has(id)){clearSnapshotNavigation();return false;}
    if(id!==null&&focus){$('smShowTimbers').checked=true;$('smShowWalls').checked=false;drawResult();}
    if(!state.viewer.selectRoot(id===null?null:{kind:'timber',id},focus))return false;
    window.dispatchEvent(new CustomEvent('space-model-timber-selected',{detail:{modelId:state.createdId,id,signature:state.recordSignature}}));
    if(focus){setTab('preview');$('smCanvas').scrollIntoView({block:'nearest'});}return true;
  }
  const dialog = document.createElement("dialog");
  dialog.id = "smWorkspace"; dialog.className = "sm-workspace";
  dialog.setAttribute("aria-labelledby", "smTitle");
  dialog.innerHTML = `
    <header class="sm-header"><div class="sm-brand"><span class="sm-mark" aria-hidden="true">▱</span><div><h1 id="smTitle">空間建模 <span id="smVersion">正在確認建模服務</span></h1></div></div><button id="smClose" class="sm-button sm-close" type="button" aria-label="返回畫布">返回畫布</button></header>
    <nav class="sm-source-actions" aria-label="選擇建模來源"><button id="smTryTimberFrame" class="sm-button" type="button">試用角材骨架範例</button><button id="smTryRectangle" class="sm-button" type="button">試用矩形範例</button><button id="smTryLShape" class="sm-button" type="button">試用 L 形範例</button><button id="smUseCurrent" class="sm-button" type="button">使用目前面</button><button id="smLibrary" class="sm-button sm-library-button" type="button">已建立空間 <span id="smModelCount">0</span></button></nav>
    <ol class="sm-steps" aria-label="建立空間的三個步驟"><li data-sm-step="1"><span>1</span><div><strong>選擇來源</strong><small>從平面輪廓或既有面開始</small></div></li><li data-sm-step="2"><span>2</span><div><strong>補齊幾何資料</strong><small>明確指定高度、邊界與厚度</small></div></li><li data-sm-step="3"><span>3</span><div><strong>預覽並建立</strong><small>核對各面，保存到專案</small></div></li></ol>
    <div class="sm-mobile-tabs" role="tablist" aria-label="建模工作區"><button id="smTabPreview" role="tab" aria-selected="true" type="button">3D 預覽</button><button id="smTabSetup" role="tab" aria-selected="false" type="button">設定與建立</button></div>
    <div id="smMain" class="sm-layout" data-tab="preview">
      <section class="sm-stage" aria-label="三維模型預覽"><div class="sm-stage-head"><div><p class="sm-eyebrow">模型預覽</p><h2 id="smPreviewTitle">讓平面，成為空間。</h2></div><span id="smResultBadge" class="sm-badge">尚未選取來源</span></div>
        <div class="sm-canvas-wrap"><canvas id="smCanvas" aria-label="空間三維預覽；拖曳旋轉，滾輪縮放"></canvas><div id="smWelcome" class="sm-welcome"><div class="sm-wire-cube" aria-hidden="true">◇</div><h2>先用現成範例，走一次完整流程</h2><p>輪廓、牆高與牆厚已填好。<br>預覽完成後，確認各面並按「建立空間」。</p><button id="smWelcomeTry" class="sm-button sm-primary" type="button">開始試用 4 × 3 m 房間 →</button><small>範例獨立預覽，不會改動畫布裡的面。</small></div></div>
        <div class="sm-view-tools"><div class="sm-view-segment" role="group" aria-label="預覽角度"><button data-sm-view="iso" class="active" aria-pressed="true" type="button">立體</button><button data-sm-view="top" aria-pressed="false" type="button" title="由上往下，沿 −Z 看">俯視</button><button data-sm-view="bottom" aria-pressed="false" type="button" title="由下往上，沿 +Z 看">仰視</button><button data-sm-view="front" aria-pressed="false" type="button">正視</button><button id="smFit" type="button">置中</button></div><span class="sm-gesture">拖曳旋轉 · 滾輪縮放 · Shift 拖曳平移</span></div>
        <p id="smViewDirection" class="sm-view-direction">立體檢視；切換視角不改動模型幾何。</p><div class="sm-display-options"><label><input id="smShowSpace" type="checkbox" checked>空間邊界</label><label><input id="smShowWalls" type="checkbox" checked>材料牆</label><label><input id="smShowTimbers" type="checkbox" checked>角材結構</label><label><input id="smShowRoof" type="checkbox">顯示頂面</label><small>頂面僅在檢視中隱藏，幾何仍保留。</small></div>
        <div class="sm-metrics"><div><span>空間體積</span><strong id="smVolume">—</strong><small>尚未扣除障礙物</small></div><div><span>扣除後淨空</span><strong id="smClearance">—</strong><small>只扣除明確選取的柱樑</small></div><div><span>材料牆體積</span><strong id="smWallVolume">—</strong><small>依指定厚度與外側方向</small></div><div><span>角材體積合計</span><strong id="smTimberVolume">—</strong><small>各支材料量，非布林聯集</small></div></div><button id="smMobileNext" class="sm-button sm-primary sm-mobile-next" type="button">下一步：設定與建立 →</button>
      </section>
      <aside class="sm-setup" aria-label="空間建模設定"><div class="sm-setup-scroll">
        <details class="sm-guide" open><summary>第一次使用？照這 3 步就能完成</summary><ol><li>點上方「試用角材骨架範例」，直接載入 z=2500、角材厚 33 mm、牆高 3000 mm 的模型。</li><li>查看 3D 預覽；可用「角材結構」開關獨立檢視。修改牆高、角材納入或邊界後，按「更新預覽」。</li><li>勾選核對面清單，按「建立空間」，再「保存專案」。之後從「已建立空間」重開。</li></ol><p>要用自己的圖：在畫布開啟一個已放置的面，再點面工具列的「建立空間」。先「設定平面投影」，明定俯視／仰視、輪廓內為淨空、牆在外側。圖面 z 是位置；牆底須另外填寫，牆高預設 3000 mm，可事後修改。</p></details>
        <section class="sm-section"><div class="sm-section-heading"><span>01</span><h2>來源與建模方式</h2></div><div id="smSourceSummary" class="sm-source-summary">尚未選擇來源，先試範例或使用目前面。</div><section id="smProjectionCallout" class="sm-projection-callout" hidden><div id="smProjectionSummary"></div><button id="smSetProjection" class="sm-button" type="button">設定平面投影</button></section><label class="sm-field">建模方式<select id="smMode"><option value="plan">由平面輪廓建立空間</option><option value="faces">組合已有的放置面</option></select></label><label id="smSourceSelectWrap" class="sm-field" hidden>來源放置面<select id="smSourceSelect"></select></label><label class="sm-field">空間名稱<input id="smModelName" maxlength="100" placeholder="例如：客廳空間" autocomplete="off"></label></section>
        <section id="smHeightEditPanel" class="sm-section sm-height-editor" hidden><div class="sm-section-heading"><span>02</span><h2>修改已建立空間</h2></div><p id="smHeightEditSummary" class="sm-help"></p><label class="sm-field">新牆高 <span>mm</span><input id="smEditHeight" type="number" min="1" step="1" inputmode="numeric" aria-describedby="smHeightEditSummary"></label><button id="smCurrentSourceUpdate" class="sm-button" type="button">採用現行來源…</button><button id="smCancelHeightEdit" class="sm-button" type="button">取消修改，保留原模型</button></section><fieldset id="smSettings" disabled><div id="smPlanSettings">
          <section class="sm-section"><div class="sm-section-heading"><span>02</span><h2>高度與空間邊界</h2></div><div class="sm-field-pair"><label class="sm-field">牆底標高 <span>mm</span><input id="smBottom" type="number" step="1" inputmode="numeric" placeholder="請明確填寫" aria-describedby="smBottomHelp"></label><label class="sm-field">牆高 <span>mm</span><input id="smHeight" type="number" min="1" step="1" inputmode="numeric" value="3000" placeholder="預設 3000"></label></div><p id="smBottomHelp" class="sm-help">牆底標高是牆開始的位置；若從 z=0 起請填 0，不能以圖面 z 代替。</p><p class="sm-help">牆高預設 3000 mm，建立前可改，建立後可從「已建立空間 → 修改模型」調整。牆頂 = 牆底 + 牆高；圖面 z 不代替牆底。</p><div id="smPlanOutline" class="sm-plan-outline" aria-label="來源輪廓及邊編號"></div><p id="smOutlineViewHelp" class="sm-help"></p><div class="sm-field-label">哪些外環邊形成空間邊界？</div><p class="sm-help">逐邊勾選，未勾選處保持開放。FREE 邊初始不選，請依實際用途決定。</p><div id="smEdges" class="sm-edge-list"></div><div class="sm-field-pair"><label class="sm-field">底面用途<select id="smFloor"><option value="boundary">實際邊界</option><option value="calculation-cap">僅作體積計算封口</option><option value="none">不建立</option></select></label><label class="sm-field">頂面用途<select id="smCeiling"><option value="boundary">實際邊界</option><option value="calculation-cap">僅作體積計算封口</option><option value="none">不建立</option></select></label></div><section id="smTimberSettings" class="sm-timber-settings"><label class="sm-check"><input id="smIncludeTimbers" type="checkbox" disabled><span>一併納入此面角材（<b id="smTimberCount">0</b> 支）</span></label><p class="sm-help">沿用各支已放置角材的真實尺寸、位置與方向；修改牆高不會搬移或拉伸角材。只納入這個放置面的角材。</p><details id="smTimberCandidateDetails" hidden><summary>核對角材尺寸與世界高度</summary><ul id="smTimberCandidates" class="sm-timber-list"></ul></details><div id="smTimberEmpty" class="sm-help">此放置面沒有已放置角材。可先建立空間，或返回面內工作區，在「構件 → 角材」完成放置再重新使用目前面。</div><button id="smBackToTimbers" class="sm-button" type="button">返回面內放置角材</button></section><div id="smHolesWrap" hidden><label class="sm-field">平面孔洞的用途<select id="smHoles"><option value="none">尚未指定（請先確認用途）</option><option value="through">形成上下貫通孔</option></select></label><p class="sm-help">孔洞不自動當成門窗或柱。選擇貫通孔會明確生成孔邊內壁。</p></div></section>
          <section class="sm-section"><div class="sm-section-heading"><span>03</span><h2>材料牆 <small>選用</small></h2></div><label class="sm-check"><input id="smWallsEnabled" type="checkbox" checked><span>同時建立有厚度的牆</span></label><label class="sm-field">牆厚 <span>mm</span><input id="smThickness" type="number" value="100" min="1" step="1" inputmode="numeric"></label><p class="sm-help">朝空間外側加厚，採方角接合，保留輪廓內的淨尺寸。100 mm 是可修改的工作預設。</p></section>
        </div><section id="smFaceSettings" class="sm-section" hidden><div class="sm-section-heading"><span>02</span><h2>明確選取空間的各個面</h2></div><p class="sm-help">只使用下方勾選的已有放置面。方向是相對該面法向的正負；封閉空間的方向須朝外。</p><div id="smFaceUses"></div></section>
        <details class="sm-obstacles"><summary>納入淨空計算的柱樑 <span id="smObstacleCount">0</span></summary><p class="sm-help">只扣除明確選取且幾何完整的障礙物，不自動加入附近物件。</p><div id="smObstacles"></div></details></fieldset>
        <section id="smPreviewDetails" class="sm-section" hidden><div class="sm-section-heading"><span>04</span><h2>核對預覽結果</h2></div><p id="smPreviewDescription" class="sm-help"></p><ul id="smGeneratedFaces" class="sm-face-summary"></ul><div id="smTimberReview" class="sm-timber-review"></div><div id="smTimberReviewList" class="sm-timber-list" hidden></div><div id="smMissing" class="sm-missing" hidden></div><label class="sm-check sm-confirm"><input id="smConfirmFaces" type="checkbox"><span>我已核對以上各面、朝向與用途</span></label><p class="sm-help">建立時保存這次的明確定義。牆高可事後修改；來源面的修改不會自動套入，可由「修改模型」明選現行來源並核對新舊差異。</p></section>
      </div><footer class="sm-setup-footer"><div id="smStatus" class="sm-status" role="status" aria-live="polite">選一個範例即可開始，無須先畫圖。</div><button id="smReviewJump" class="sm-review-jump" type="button" hidden>查看面清單並確認 ↓</button><div class="sm-footer-actions"><button id="smPreview" class="sm-button" type="button" disabled>更新預覽</button><button id="smCreate" class="sm-button sm-primary" type="button" disabled>建立空間</button></div><div id="smCreatedActions" hidden><button id="smEditHeightButton" class="sm-button sm-edit-height-button" type="button" hidden>修改模型</button><div class="sm-export"><select id="smExportKind" aria-label="要匯出的模型"><option value="space">空間邊界</option><option value="volume">空間實體</option><option value="clearance">扣除後淨空</option><option value="walls">材料牆</option><option value="timbers">角材結構</option></select><button id="smExport" class="sm-button" type="button">匯出 .model.json</button></div><p>保存後可由「檔案 → 開啟 .gcanvas 專案」還原全部模型。</p></div></footer></aside>
    </div>
    <section id="smLibraryPanel" class="sm-library-panel" hidden><header><div><p class="sm-eyebrow">專案空間</p><h2>已建立空間</h2><p>模型保存在目前專案中；保存 .gcanvas 後可再次開啟。</p></div><button id="smBackToBuild" class="sm-button" type="button">返回建模</button></header><div id="smLibraryList"></div></section>`;
  document.body.append(dialog);
  // Keep the established controls and validation, while putting the common path
  // ahead of optional source choices and per-face configuration.
  function organizeSetup() {
    const sourceSection=$('smSourceSummary').closest('.sm-section');
    sourceSection.querySelector('h2').textContent='來源與名稱';
    const sourceAdvanced=document.createElement('details');sourceAdvanced.id='smSourceAdvanced';sourceAdvanced.className='sm-advanced';
    sourceAdvanced.innerHTML='<summary>其他建模方式與來源放置</summary>';
    sourceAdvanced.append($('smMode').parentElement,$('smSourceSelectWrap'));sourceSection.append(sourceAdvanced);
    const inline=document.createElement('div');inline.id='smInlineProjection';
    inline.innerHTML='<label class="sm-field">原圖觀看方向<select id="smProjectionView"><option value="top">俯視（從 +Z 往下看）</option><option value="bottom">仰視（從 −Z 往上看）</option></select></label><p id="smProjectionHelp" class="sm-help"></p><button id="smConfirmProjection" class="sm-button sm-primary" type="button">確認用途與觀看方向</button>';
    $('smProjectionCallout').insertBefore(inline,$('smSetProjection'));
    const common=$('smPlanSettings').firstElementChild;common.id='smCommonSettings';common.querySelector('h2').textContent='高度、材料與角材';
    const bottomShortcut=document.createElement('button');bottomShortcut.id='smBottomZero';bottomShortcut.className='sm-button sm-bottom-shortcut';bottomShortcut.type='button';bottomShortcut.textContent='牆底設為 0 mm';
    common.insertBefore(bottomShortcut,$('smBottomHelp'));
    $('smBottomHelp').textContent='牆底需另外指定；圖面 z 是原面的位置。牆頂＝牆底＋牆高。';
    const heightHelp = $('smBottomHelp').nextElementSibling;
    heightHelp.id='smHeightHelp'; heightHelp.textContent='空間建模的牆高預設 3000 mm，建立後仍可修改。「六面盒」另以 2500 mm 作為整盒預設高度；兩個入口的工作預設各自獨立，請依同一工程的尺寸調整。牆頂＝牆底＋牆高。';
    $('smHeight').setAttribute('aria-describedby', 'smHeightHelp');
    const boundary=document.createElement('details');boundary.id='smBoundaryAdvanced';boundary.className='sm-advanced';boundary.innerHTML='<summary>調整輪廓邊、底面與頂面</summary>';
    const outline=$('smPlanOutline'),outlineHelp=$('smOutlineViewHelp'),edgeLabel=outlineHelp.nextElementSibling,edgeHelp=edgeLabel.nextElementSibling,floorPair=$('smFloor').closest('.sm-field-pair');
    boundary.append(outline,outlineHelp,edgeLabel,edgeHelp,$('smEdges'),floorPair);
    const material=$('smWallsEnabled').closest('.sm-section');material.classList.add('sm-material-common');material.querySelector('.sm-section-heading').remove();
    material.querySelector('.sm-help').textContent='材料牆向外增加，保留室內淨尺寸；牆厚可修改。';
    const timber=$('smTimberSettings'),holes=$('smHolesWrap');
    timber.querySelector('.sm-help').textContent='保留角材原尺寸、方向及高度；修改牆高不搬移角材。';
    const boundarySummary=document.createElement('p');boundarySummary.id='smBoundarySummary';boundarySummary.className='sm-boundary-summary';
    const boundaryWarning=document.createElement('p');boundaryWarning.id='smBoundaryWarning';boundaryWarning.className='sm-missing';boundaryWarning.hidden=true;
    common.append(material,timber,boundarySummary,boundaryWarning,holes,boundary);
    const guide=dialog.querySelector('.sm-guide');guide.open=false;guide.querySelector('summary').textContent='操作說明與幾何定義';
    guide.querySelector('ol').innerHTML='<li>使用自己的面時，在這裡確認平面投影用途與俯視／仰視；或從上方選現成範例。</li><li>指定牆底，牆高預設 3000 mm、材料牆厚 100 mm。可修改設定及角材納入，再按「更新預覽」。</li><li>核對預覽及各面用途，在建立按鈕旁勾選確認、按「建立空間」，最後使用頂列的「保存」保存專案。</li>';
    guide.querySelector('p').textContent='圖面 z 是原面位置，不代替牆底或牆高。輪廓內代表室內淨空，材料牆向外加厚；FREE 邊及孔洞需明確核對。需要逐邊、底頂用途或另一種建模方式時，可展開對應設定。';
    dialog.querySelector('.sm-setup-scroll').append(guide);
    const review=$('smPreviewDetails'),heading=review.querySelector('.sm-section-heading'),details=document.createElement('details');details.id='smReviewFaces';details.className='sm-advanced sm-review-faces';
    const summary=document.createElement('summary');summary.textContent='各面、朝向與用途清單';details.append(summary);heading.remove();
    const confirm=$('smConfirmFaces').closest('label');confirm.querySelector('span').textContent='我已核對各面、朝向與用途';
    const commit=document.createElement('section');commit.id='smCommitReview';commit.hidden=true;commit.setAttribute('aria-label','確認預覽並建立');
    commit.innerHTML='<p id="smCommitSummary" class="sm-commit-summary"></p>';
    commit.append($('smReviewJump'),confirm);$('smStatus').before(commit);
    for(const child of [...review.children])details.append(child);review.append(details);
    const saveNotice=document.createElement('p');saveNotice.id='smSaveNotice';saveNotice.className='sm-save-notice';saveNotice.textContent='已加入目前專案。還需要保存 .gcanvas 檔案，才能在下次開啟。';$('smCreatedActions').prepend(saveNotice);
  }
  organizeSetup();
  let capabilitiesPromise=null, supportsTimbers=null, supportsEngineering=false;
  function probeCapabilities() {
    if(capabilitiesPromise)return capabilitiesPromise;
    capabilitiesPromise=fetch("/model/capabilities",{cache:"no-store"}).then(async response=>{if(!response.ok)throw new Error("服務版本無法確認");return response.json();}).then(data=>{
      supportsEngineering=data.release==='engineering-spec-v1-20260928' && Array.isArray(data.capabilities) && data.capabilities.includes('engineering-spec/1');
      supportsTimbers=Array.isArray(data.space_preview_schemas)&&data.space_preview_schemas.includes("geometry-space-preview/2");return supportsTimbers;
    }).catch(()=>{supportsTimbers=false;return false;}).then(supported=>{
      const label=supportsEngineering?'工程規格版 2026.09.28':supported?"角材結構建模版":"服務待更新：角材功能未啟用";
      $("smVersion").textContent=supported?'':label;$("smVersion").hidden=supported;
      for(const badge of document.querySelectorAll(".space-model-release")){badge.textContent=supported?'空間建模':label;badge.title=label;}
      if(!supported)dialog.querySelector(".sm-guide li").textContent="此服務尚未啟用角材結構。請用本次交付網址或啟動腳本開新版；現有服務仍可試用矩形或 L 形空間。";
      return supported;
    });
    return capabilitiesPromise;
  }
  async function requireTimberCapability() {if(!await probeCapabilities())throw new Error("目前服務尚未啟用角材結構建模。請使用本次交付的網址或啟動腳本開啟新版；若只要建立空間，可明確取消「一併納入此面角材」後再預覽。");}

  function message(text, kind = "") { $("smStatus").textContent = text; $("smStatus").dataset.kind = kind; }
  function contextId() { return ReferenceWorkspace.context().id; }
  function sourceHistoryToken() {const h=ReferenceWorkspace.history;return h?{frame:h.frame,undo:h.undo.at(-1),redo:h.redo.at(-1),group:h.group}:null;}
  function sameSourceHistory(token) {const now=sourceHistoryToken();return token===null||!!now&&token.frame===now.frame&&token.undo===now.undo&&token.redo===now.redo&&token.group===now.group;}
  function faceKey(bid) {return ReferenceWorkspace.history?.frame.ids.get(bid);}
  function sourceSignature(source) {return JSON.stringify([source.boundary_id,source.placement_id,source.frame,source.loops,source.projection]);}
  function rememberDraft() {
    const source=state.source;
    if(!source||source.kind!=="scene"||state.readonly||state.editing||state.createdId)return;
    if(source.context_id!==contextId()||source.face_key!==faceKey(source.boundary_id)||!sameSourceHistory(source.history_token)){draft=null;return;}
    const controls=[...dialog.querySelectorAll('#smSettings input,#smSettings select,#smMode,#smModelName,#smProjectionView')];
    draft={context_id:source.context_id,face_key:source.face_key,history_token:source.history_token,signature:sourceSignature(source),base_scene:source.base_scene,
      controls:controls.map(el=>({selector:el.id?'#'+el.id:el.dataset.smEdge!=null?`[data-sm-edge="${el.dataset.smEdge}"]`:el.dataset.smObstacle?`[data-sm-obstacle="${el.dataset.smObstacle}"][value="${el.value}"]`:el.dataset.smFace!=null?`[data-sm-face="${el.dataset.smFace}"]`:el.dataset.smOrientation!=null?`[data-sm-orientation="${el.dataset.smOrientation}"]`:el.dataset.smPurpose!=null?`[data-sm-purpose="${el.dataset.smPurpose}"]`:null,value:el.value,checked:el.checked})).filter(item=>item.selector)};
  }
  function restoreDraft(source) {
    if(!draft)return false;
    const saved=draft;draft=null;
    if(source.kind!=="scene"||saved.context_id!==source.context_id||saved.face_key!==source.face_key||saved.base_scene!==source.base_scene||saved.signature!==sourceSignature(source)||!sameSourceHistory(saved.history_token))return false;
    for(const item of saved.controls){const el=dialog.querySelector(item.selector);if(!el)continue;if(el.type==='checkbox')el.checked=item.checked;else el.value=item.value;}
    $('smObstacleCount').textContent=String(dialog.querySelectorAll('[data-sm-obstacle]:checked').length);
    toggleMode(false);$('smConfirmFaces').checked=false;state.previewRevision=-1;updateActions();return true;
  }
  function cancelProjectionConfirmation() {state.projectionSequence++;if(state.projectionPending){state.projectionPending=false;updateActions();}}
  function onlyProjectionChanged(source) {
    const h=ReferenceWorkspace.history,token=source.history_token,entry=h?.undo.at(-1);
    if(!token||!h||h.frame!==token.frame||h.group||token.group||entry===token.undo||entry?.kind!=="local")return false;
    // Permit one metadata append from the captured source, never rebase over an
    // intervening edit or undo/redo even when its resulting scene text is equal.
    if(token.undo?h.undo.at(-2)!==token.undo:h.undo.length!==1)return false;
    const previous=entry.faceProjections?.get(entry.ids.get(source.boundary_id))?.find(item=>item.placement_id===source.placement_id)?.projection||null;
    return JSON.stringify(previous)===JSON.stringify(source.projection);
  }
  function assertSourceHistory() {if(!state.editing&&state.source?.kind==="scene"&&!sameSourceHistory(state.source.history_token))throw new Error("來源讀取後已有編輯、復原或重做。請重新「使用目前面」取得一致的來源與角材，再更新預覽。");}
  // Other face tools may need to reveal the underlying placement editor.
  // Closing owns presentation only; saved models and the core scene stay intact.
  function cancelSourceLoad() {
    if(!["loading","previewing","creating"].includes(state.phase))return;
    state.controller?.abort();state.sequence++;state.phase=state.source?"ready":"empty";state.previewRevision=-1;$("smConfirmFaces").checked=false;
    $("smResultBadge").textContent="建模操作已取消";updateActions();
  }
  function close() { viewerOpenSequence++;clearSnapshotNavigation();rememberDraft();cancelProjectionConfirmation();cancelSourceLoad();if(dialog.open)dialog.close();WorkspaceShell.detach(dialog); }
  function setTab(tab) { $("smMain").dataset.tab = tab; for (const [id, key] of [["smTabPreview", "preview"], ["smTabSetup", "setup"]]) $(id).setAttribute("aria-selected", String(tab === key)); }
  function viewChanged(viewState) {
    for(const button of dialog.querySelectorAll("[data-sm-view]")){const active=button.dataset.smView===viewState.view;button.classList.toggle("active",active);button.setAttribute("aria-pressed",String(active));}
    $("smViewDirection").textContent=({top:"俯視：沿 −Z 看，來源 U 軸朝右。",bottom:"仰視：沿 +Z 看，來源 U 軸朝右。",front:"正視：沿 +Y 看，+Z 朝上。"}[viewState.view]||"立體檢視。")+"只改視角，不改幾何。";
  }
  function loadViewer() {
    if (window.GeometryModelViewer?.create) return Promise.resolve();
    if (viewerLoad) return viewerLoad;
    // The ordinary scripts are ordered. A failed resource load must not turn a
    // later user action into an unhandled ReferenceError; retry that same asset.
    viewerLoad = new Promise((resolve, reject) => {
      const script = document.createElement("script"); script.src = "model-viewer.js";
      const finish = error => { clearTimeout(timer); script.onload = script.onerror = null; script.remove(); error ? reject(error) : resolve(); };
      const timer = setTimeout(() => finish(new Error("3D 檢視器載入逾時。請再按一次原操作重試。")), 15000);
      script.onload = () => finish(window.GeometryModelViewer?.create ? null : new Error("3D 檢視器未能啟動。請重新整理頁面後重試。"));
      script.onerror = () => finish(new Error("3D 檢視器載入失敗。請確認服務連線，再按一次原操作重試。"));
      document.head.append(script);
    }).finally(() => { viewerLoad = null; });
    return viewerLoad;
  }
  function show(resume) {
    if (!dialog.open) dialog.showModal();
    WorkspaceShell.attach(dialog, {saveBlocked:()=>state.viewerLoading || state.projectionPending || ['loading','previewing','creating'].includes(state.phase),
      saveReason:()=> '正在處理空間變更，完成後即可保存。', onProjectState:updateActions});
    if (!window.GeometryModelViewer?.create) {
      const sequence = ++viewerOpenSequence, sourceContextId = contextId();
      state.viewerLoading = true; message("正在載入 3D 檢視器…"); $("smResultBadge").textContent = "檢視器載入中"; updateActions();
      loadViewer().then(() => {
        if (sequence !== viewerOpenSequence) return;
        state.viewerLoading = false;
        if (!dialog.open) return;
        if (sourceContextId !== contextId()) { message("載入期間專案已切換，請重新選擇建模來源。", "warning"); updateActions(); return; }
        return resume?.();
      }).catch(error => {
        if (sequence !== viewerOpenSequence) return;
        state.viewerLoading = false; $("smResultBadge").textContent = "檢視器尚未就緒"; message(error.message, "error"); updateActions();
      });
      return false;
    }
    state.viewerLoading = false;
    try { if (!state.viewer) state.viewer = window.GeometryModelViewer.create($("smCanvas"), { emptyText: "", background: "#edf2f5", onChange:viewChanged, onPick:ref=>selectSnapshotTimber(ref?.id??null,false) }); }
    catch (error) { message(`3D 檢視器無法啟動：${error.message}`, "error"); updateActions(); return false; }
    refresh();
    return true;
  }
  function validProjection(def) { return !!def && def.kind==="space-boundary-plan" && ["top","bottom"].includes(def.view) && def.region==="interior" && def.wallSide==="outside"; }
  function currentProjection(source=state.source) { return source?.kind==="scene" ? ReferenceWorkspace.getFaceProjection?.(source.boundary_id,source.placement_id)||null : source?.projection||null; }
  function needsProjection() { return !!state.source && $("smMode").value==="plan" && !state.editing && !state.readonly && !state.createdId; }
  function needsDrawingAlignment(source=state.source, view=source?.projection?.view) {
    if(source?.kind!=="scene"||!validProjection(source.projection)||!source.frame||!source.loops?.length)return false;
    return GeometryModelViewer.drawingAlignment(source.frame,source.loops,view).changed;
  }
  function renderProjection() {
    const source=state.source,plan=$("smMode").value==="plan",def=source?.projection;
    const editable=source?.kind==="scene"&&!state.readonly&&!state.createdId&&!state.editing;
    const horizontal=source?.frame?.u?.[2]===0&&source?.frame?.v?.[2]===0&&Math.abs(source.frame.u[0]*source.frame.v[1]-source.frame.u[1]*source.frame.v[0])===1;
    $("smProjectionCallout").hidden=!source||!plan;
    $("smSetProjection").hidden=!editable;
    const alignment=editable&&horizontal&&validProjection(def)&&needsDrawingAlignment(source);
    $("smInlineProjection").hidden=!editable||validProjection(def)&&!alignment||!horizontal;
    $("smProjectionView").disabled=state.projectionPending;
    $("smConfirmProjection").disabled=state.projectionPending||!editable||!horizontal||["loading","creating","previewing"].includes(state.phase);
    $("smConfirmProjection").textContent=state.projectionPending?"正在核對來源…":alignment&&$('smProjectionView').value===def.view?"依原圖對齊放置方向":"確認用途與觀看方向";
    $('smProjectionHelp').textContent=alignment?'目前放置與輪廓編輯圖的上下方向相反。若此輪廓按原圖描繪，請對齊放置方向；保留局部輪廓、外框位置與圖面高度。已放角材會先顯示影響預覽，這次對齊可復原。':'確認這片面為空間邊界的平面投影；輪廓內是室內淨空、材料牆向外加厚。圖面 z 不代替牆底或牆高。';
    $("smSetProjection").disabled=state.projectionPending;
    $("smProjectionCallout").setAttribute("aria-busy",String(state.projectionPending));
    $("smProjectionCallout").dataset.state=validProjection(def)?"defined":"missing";
    $("smSetProjection").textContent=validProjection(def)?"修改平面投影定義":horizontal?"更多投影設定／編輯圖面 z":"設定平面投影／編輯放置";
    $("smProjectionSummary").innerHTML=validProjection(def)?`<strong>空間邊界平面投影 · ${def.view==="top"?"俯視（沿 −Z）":"仰視（沿 +Z）"}</strong><p>輪廓內為室內淨空，材料牆朝外側加厚；圖面高度與牆高獨立。</p>`:state.readonly||state.editing||state.createdId?'<strong>舊模型未保存投影定義</strong><p>沿用原模型的明確幾何；可修改牆高，不推測或補寫原圖用途及俯仰方向。</p>':horizontal?'<strong>先確認：這個面代表空間邊界的平面投影</strong>':'<strong>此面尚不能作為水平投影</strong><p>請先編輯為水平放置，或展開「其他建模方式」組合已有的放置面。</p>';
  }
  function renderBoundarySummary() {
    if(!state.source||$('smMode').value!=="plan"||state.readonly)return;
    const edges=[...dialog.querySelectorAll('[data-sm-edge]')],selected=edges.filter(el=>el.checked).length;
    const purpose=value=>({boundary:"實際邊界","calculation-cap":"計算封口",none:"不建立"}[value]||"待指定");
    $('smBoundarySummary').textContent=`邊界：周邊 ${selected}/${edges.length} 邊；底面${purpose($('smFloor').value)}，頂面${purpose($('smCeiling').value)}。${selected<edges.length||$('smFloor').value==='none'||$('smCeiling').value==='none'?'保留未選處的開口。':'預覽時再檢查是否封閉。'}`;
    const free=(state.source.loops?.[0]?.fixity||[]).filter(isFree).length,holes=(state.source.loops?.length||1)-1,warnings=[];
    if(free)warnings.push(`有 ${free} 條 FREE 邊，初始不納入；請展開下方逐邊核對用途。`);
    if(holes&&$('smHoles').value==='none')warnings.push(`有 ${holes} 個孔洞，請先指定下方孔洞用途，才可預覽。`);
    $('smBoundaryWarning').hidden=!warnings.length;$('smBoundaryWarning').textContent=warnings.join(' ');
  }
  function buildView() { $("smLibraryPanel").hidden = true; $("smMain").hidden = false; dialog.classList.remove("sm-in-library");window.dispatchEvent(new Event('space-model-view-changed')); }
  function updateActions() {
    const busy = state.viewerLoading || !state.viewer || state.projectionPending || state.phase === "loading" || state.phase === "previewing" || state.phase === "creating";
    WorkspaceShell.refresh(dialog);
    const missingProjection=needsProjection()&&!validProjection(state.source.projection);
    $("smPreview").disabled = !state.source || busy || missingProjection || (state.readonly && !state.editing);
    $("smCreate").disabled = busy || missingProjection || !state.result || wallRequirementMissing(state.input,state.result) || state.previewRevision !== state.revision || !$("smConfirmFaces").checked || !!state.createdId;
    $("smPreview").textContent = state.phase === "previewing" ? "計算預覽中…" : "更新預覽";
    $("smCreate").textContent = state.phase === "creating" ? (state.editing ? "更新中…" : "建立中…") : state.createdId ? "已建立 ✓" : state.editing ? "更新空間" : "建立空間";
    $("smCreatedActions").hidden = !state.createdId;
    const project=ReferenceWorkspace.context();
    $('smSaveNotice').textContent=project.saved&&!project.dirty?'目前專案檔案已保存，包含這個空間。':project.downloaded?'專案下載已開始；請確認 .gcanvas 檔案已存到電腦。':'已加入目前專案。還需要保存 .gcanvas 檔案，才能在下次開啟。';
    $("smEditHeightButton").hidden = !state.createdId || state.input?.mode !== "plan";
    $("smHeightEditPanel").hidden = !state.editing;
    $("smSettings").hidden = state.readonly;
    $("smMode").parentElement.hidden = state.readonly;
    $("smSourceAdvanced").hidden=state.readonly;
    $("smModelName").readOnly = state.readonly || !!state.createdId;
    $("smReviewJump").hidden = !state.result || state.previewRevision !== state.revision || !!state.createdId || $("smConfirmFaces").checked;
    $("smReviewJump").textContent = `查看 ${state.result?.summary.face_count || ""} 個面並確認 ↓`;
    $("smCommitReview").hidden=!state.result||state.previewRevision!==state.revision||!!state.createdId;
    $("smConfirmFaces").disabled=busy;
    $("smMobileNext").textContent = state.createdId ? "保存、修改與匯出模型 →" : state.result && state.previewRevision === state.revision ? (state.editing ? "下一步：核對各面並更新 →" : "下一步：核對各面並建立 →") : "下一步：設定與建立 →";
    $("smThickness").disabled = !$("smWallsEnabled").checked;
    renderProjection();renderBoundarySummary();
    for (const el of dialog.querySelectorAll("[data-sm-step]")) el.classList.toggle("current", Number(el.dataset.smStep) === (!state.source ? 1 : state.result && state.previewRevision === state.revision ? 3 : 2));
  }
  function stale() {
    state.revision++; state.createdId = null; $("smConfirmFaces").checked = false;
    if (state.result) { $("smResultBadge").textContent = "設定已改，請更新預覽"; $("smResultBadge").dataset.state = "stale"; message(state.editing ? "牆高已變更，原模型尚未修改。請更新預覽並核對各面，再按「更新空間」。" : "設定已變更。3D 仍是上次預覽，請按「更新預覽」後再建立。", "warning"); }
    updateActions();
  }
  async function request(url, body) {
    const response = await fetch(url, { method: body ? "POST" : "GET", headers: body ? {"Content-Type":"application/json"} : {}, body: body ? JSON.stringify(body) : undefined, signal: state.controller?.signal });
    let data; try { data = await response.json(); } catch (_) { throw new Error("服務未傳回可讀取的模型資料，請確認目前開啟的是空間建模第一版。"); }
    if (!response.ok || data.ok === false || ["INCOMPLETE", "UNSUPPORTED", "INVALID"].includes(data.status)) {
      const diagnostics = Array.isArray(data.diagnostics) && data.diagnostics.length ? data.diagnostics : [data.error && typeof data.error === "object" ? data.error : data];
      throw new Error(diagnostics.map(d => ["BASE_COMPILER", "BASE_EXECUTABLE"].includes(d.code)
        ? "空間建模服務尚未就緒，請保存專案並重新啟動應用。"
        : [d.message || d.error || "無法建立預覽", d.code, d.clause].filter(Boolean).join(" · ")).join("\n"));
    }
    return data;
  }
  function startSource() {
    clearSnapshotNavigation();savedContext=null;
    rememberDraft();cancelProjectionConfirmation();
    state.controller?.abort(); state.controller = new AbortController(); state.sequence++; state.phase = "loading";
    state.result = null; state.input = null; state.source = null; state.createdId = null; state.readonly = false; state.editing = null; state.recordSignature = null; state.revision++; state.previewRevision = -1;
    $("smConfirmFaces").checked = false; $("smPreviewDetails").hidden = true; $("smWelcome").hidden = true; $("smSettings").disabled = true;
    for (const id of ["smVolume", "smClearance", "smWallVolume", "smTimberVolume"]) $(id).textContent = "—";
    state.viewer?.setObjects([]); $("smResultBadge").textContent = "讀取來源中"; $("smResultBadge").dataset.state = ""; buildView(); updateActions();
    return state.sequence;
  }
  const isFree = value => value === 0 || value === false || value === "FREE" || value === "X";
  const timberRole = role => ({boundary:"邊界材",primary:"主支",secondary:"副支",unspecified:"未指定角色"}[role]||role||"未指定角色");
  function sourceTimbers(references,placementId) {
    if(!references.ok||!Array.isArray(references.timbers))throw new Error(references.error||"無法讀取已放置角材，請重新讀取目前面。");
    return references.timbers.filter(t=>t.geometry?.surface===placementId).map(t=>{
      const g=t.geometry,dimensions=[g.length,g.A,g.B];
      if(!Number.isInteger(t.id)||t.id<0||t.id>4294967295||!dimensions.every(n=>Number.isSafeInteger(n)&&n>0)||!Array.isArray(g.origin)||g.origin.length!==3||!g.origin.every(Number.isSafeInteger)||!Array.isArray(g.axes)||g.axes.length!==3||!g.axes.every(a=>Array.isArray(a)&&a.length===3&&a.every(Number.isSafeInteger)))throw new Error(`角材 #${t.id} 的幾何資料不完整，請返回面內檢查放置。`);
      const dz=g.axes.map((axis,i)=>axis[2]*dimensions[i]);
      return {id:t.id,role:t.role,A:g.A,B:g.B,length:g.length,placement_id:placementId,z_min:g.origin[2]+dz.reduce((sum,n)=>sum+Math.min(0,n),0),z_max:g.origin[2]+dz.reduce((sum,n)=>sum+Math.max(0,n),0)};
    });
  }
  function renderTimberCandidates(source) {
    const candidates=source.timbers||[];
    $("smTimberCount").textContent=String(candidates.length);$("smIncludeTimbers").disabled=!candidates.length;$("smIncludeTimbers").checked=!!candidates.length;
    $("smTimberEmpty").hidden=!!candidates.length;$("smBackToTimbers").hidden=!!candidates.length||source.kind!=="scene";$("smTimberCandidateDetails").hidden=!candidates.length;
    $("smTimberCandidates").innerHTML=candidates.map(t=>`<li data-sm-timber="${esc(t.id)}"><strong>角材 #${esc(t.id)} · ${esc(timberRole(t.role))}</strong><span>放置面 #${esc(t.placement_id)} · A×B ${esc(t.A)}×${esc(t.B)} mm · 長 ${esc(t.length)} mm</span><small>世界 z：${esc(t.z_min)}～${esc(t.z_max)} mm</small></li>`).join("");
  }
  function renderOutline(loops) {
    const verts = loops?.[0]?.verts || []; if (!verts.length) { $("smPlanOutline").innerHTML = ""; return; }
    const source=state.source,def=source?.projection;
    if(!validProjection(def)||!source.frame) {$("smPlanOutline").innerHTML="";$("smOutlineViewHelp").textContent="設定平面投影後，這裡會依承載面框架顯示實際俯視或仰視輪廓。";return;}
    const project=p=>GeometryModelViewer.projectPlanPoint(p,source.frame,def.view,true),projected=verts.map(project);
    const xs = projected.map(p => p[0]), ys = projected.map(p => p[1]), x0 = Math.min(...xs), y0 = Math.min(...ys), w = Math.max(...xs) - x0 || 1, h = Math.max(...ys) - y0 || 1;
    const scale = Math.min(250 / w, 115 / h), map = p => {const q=project(p);return [32 + (q[0] - x0) * scale, 28 + (q[1] - y0) * scale];};
    const paths = loops.map(l => "M" + l.verts.map(map).map(p => p.join(",")).join("L") + "Z").join(" ");
    $("smPlanOutline").innerHTML = `<svg viewBox="0 0 320 175" role="img" aria-label="來源面輪廓，外環各邊對應下方編號"><path d="${paths}" fill-rule="evenodd"/>${verts.map((p,i) => { const a=map(p), b=map(verts[(i+1)%verts.length]);return `<g><circle cx="${(a[0]+b[0])/2}" cy="${(a[1]+b[1])/2}" r="10"/><text x="${(a[0]+b[0])/2}" y="${(a[1]+b[1])/2+3}">${i+1}</text></g>`; }).join("")}</svg>`;
    $("smOutlineViewHelp").textContent=`此圖沿原面 U 軸向右，以${def.view==="top"?"俯視（沿 −Z）":"仰視（沿 +Z）"}顯示實際放置。${GeometryModelViewer.drawingAlignment(source.frame,loops,def.view).changed?'上下方向與輪廓編輯圖相反；可在投影設定依原圖對齊放置。':'方向與輪廓編輯圖一致。'}邊編號對應同一條原始邊。`;
  }
  function renderSource(source, settings = {}) {
    state.source = source; state.phase = "ready";
    const loops = source.loops || [], verts = loops[0]?.verts || [];
    $("smSourceSummary").innerHTML = `<strong>${esc(source.name)} · ${source.kind === "example" ? "獨立範例" : "目前專案"}</strong><span>放置面 #${esc(source.placement_id)} · 圖面 z = ${esc(source.source_z ?? "非水平面")} mm · ${source.timbers?.length||0} 支角材</span>`;
    $("smModelName").value = source.name.replace(/\s*#\s*(\d+)$/, " $1") + "空間";
    $("smProjectionView").value=source.projection?.view||"top";
    $("smSourceAdvanced").open=false;$("smBoundaryAdvanced").open=false;$("smReviewFaces").open=false;
    $("smBottom").value = settings.bottom ?? ""; $("smHeight").value = settings.height ?? DEFAULT_WALL_HEIGHT;
    $("smThickness").value = settings.wall_thickness ?? 100; $("smWallsEnabled").checked = settings.wall_thickness !== null;
    $("smFloor").value = settings.floor || "boundary"; $("smCeiling").value = settings.ceiling || "boundary"; $("smHoles").value = settings.holes || "none";
    renderTimberCandidates(source);
    $("smEdges").innerHTML = verts.map((p,i) => { const q=verts[(i+1)%verts.length],free=isFree(loops[0].fixity?.[i]),selected=Array.isArray(settings.edges)?settings.edges.includes(i):!free; return `<label class="sm-edge"><input type="checkbox" data-sm-edge="${i}" ${selected?"checked":""}><span>邊 ${i+1}</span><small>${Math.abs(q[0]-p[0])+Math.abs(q[1]-p[1])} mm${free?" · FREE":""}</small></label>`; }).join("");
    renderOutline(loops); $("smHolesWrap").hidden = loops.length < 2; $("smSettings").disabled = false;
    $("smPreviewTitle").textContent = source.name; $("smResultBadge").textContent = "待預覽"; $("smResultBadge").dataset.state = "";
    $("smSourceSelectWrap").hidden = source.kind === "example";
    $("smSourceSelect").innerHTML = source.kind === "example" ? "" : oc.surfs.map(s=>`<option value="${s.id}" ${s.id===source.placement_id?"selected":""}>放置面 #${s.id} · 輪廓 #${s.boundary}</option>`).join("");
    const obstacles = source.kind === "example" ? [] : [...oc.columns.map(o=>({kind:"column",id:o.id,label:"柱"})),...oc.beams.map(o=>({kind:"beam",id:o.id,label:"樑"}))];
    $("smObstacles").innerHTML = obstacles.length ? obstacles.map(o=>`<label class="sm-check"><input type="checkbox" data-sm-obstacle="${o.kind}" value="${o.id}"><span>${o.label} #${o.id}</span></label>`).join("") : '<p class="sm-help">此來源沒有可選取的柱樑。</p>';
    $("smObstacleCount").textContent = "0";
    const surfaces = source.kind === "example" ? [{id:source.placement_id,boundary:source.boundary_id}] : oc.surfs;
    $("smFaceUses").innerHTML = surfaces.map(s=>`<div class="sm-face-use"><label class="sm-check"><input type="checkbox" data-sm-face="${s.id}"><span>放置面 #${s.id}<small>輪廓 #${s.boundary}</small></span></label><div class="sm-field-pair"><label class="sm-field">法向方向<select data-sm-orientation="${s.id}"><option value="1">+1：沿原面法向</option><option value="-1">−1：反原面法向</option></select></label><label class="sm-field">用途<select data-sm-purpose="${s.id}"><option value="boundary">實際邊界</option><option value="calculation-cap">僅作體積計算封口</option></select></label></div></div>`).join("");
    toggleMode(false); updateActions();
  }
  async function openExample(kind = "rectangle") {
    if (!show(() => openExample(kind))) return;
    const seq=startSource(),sourceContextId=contextId(); $("smMode").value="plan"; message("正在載入現成範例…");
    try {
      if(kind==="timber-frame")await requireTimberCapability();
      if(seq!==state.sequence)return;
      if (!state.examples) state.examples=(await request("/model/space-examples")).examples;
      if(seq!==state.sequence)return;
      if(sourceContextId!==contextId())throw new Error("讀取期間專案已切換，請在目前專案重新選取範例。");
      const example=state.examples.find(e=>e.id===(kind==="timber-frame"?"timber-frame":kind==="l-shape"||kind==="lshape"?"l-shape":"rectangle"));
      if(!example)throw new Error("找不到此範例，請重新整理後再試。");
      const s=example.source||{};
      renderSource({kind:"example",name:example.name,base_scene:example.base_scene,placement_id:example.placement_id,boundary_id:s.boundary_id??example.placement_id,source_z:example.source_z??s.source_z??s.origin?.[2],frame:{origin:copy(s.origin),u:copy(s.u),v:copy(s.v)},projection:copy(EXAMPLE_PROJECTION),timbers:copy(s.timbers||[]),loops:s.loops||example.loops||[],context_id:sourceContextId},{...example.settings,height:DEFAULT_WALL_HEIGHT});
      if(!state.source.loops.length) throw new Error("範例缺少來源輪廓，請確認服務版本。");
      setTab("preview"); await preview();
    } catch(e) { if(e.name!=="AbortError" && seq===state.sequence){state.phase="error";message(e.message,"error");updateActions();} }
  }
  async function openCurrentFace(placementId) {
    if (!show(() => openCurrentFace(placementId))) return;
    const seq=startSource(),sourceContextId=contextId(),historyToken=sourceHistoryToken();$("smMode").value="plan"; message("正在讀取目前場景與來源面…");
    try {
      if(connection.phase!=="ready")throw new Error("請先等待場景連線完成，再使用目前面。");
      const bid=oc.edit?.bid??(oc.sel?.kind==="face"?oc.sel.id:null);
      const selectedSurface=placementId!=null?oc.surfs.find(s=>s.id===Number(placementId)):bid!=null?feSurf(bid):oc.surfs.length===1?oc.surfs[0]:null;
      if(!selectedSurface) throw new Error("請先返回畫布，開啟要使用的面並完成放置，再由屬性欄建立空間。");
      const dump=await api("dump");
      if(seq!==state.sequence)return;
      if(sourceContextId!==contextId())throw new Error("讀取期間專案已切換。請在目前專案重新選取來源面。");
      if(!dump.ok||typeof dump.text!=="string")throw new Error(dump.error||"無法讀取來源場景。");
      const placements=await api("surfaces");
      if(seq!==state.sequence)return;
      if(sourceContextId!==contextId())throw new Error("讀取期間專案已切換。請在目前專案重新選取來源面。");
      const surface=placements.ok&&placements.surfaces?.find(s=>s.id===selectedSurface.id&&s.boundary===selectedSurface.boundary);
      if(!surface)throw new Error("來源放置面已變更或不存在，請返回畫布重新選取。");
      const boundary=await api("boundary "+surface.boundary);
      if(seq!==state.sequence)return;
      if(sourceContextId!==contextId())throw new Error("讀取期間專案已切換。請在目前專案重新選取來源面。");
      if(!boundary.ok||!Array.isArray(boundary.loops))throw new Error(boundary.error||"無法讀取來源面的輪廓。");
      const references=await api("references");
      if(seq!==state.sequence)return;
      if(sourceContextId!==contextId())throw new Error("讀取角材期間專案已切換，請重新選取來源面。");
      const timbers=sourceTimbers(references,surface.id),checkedDump=await api("dump");
      if(seq!==state.sequence)return;
      if(sourceContextId!==contextId())throw new Error("讀取角材期間專案已切換，請重新選取來源面。");
      if(!checkedDump.ok||checkedDump.text!==dump.text||!sameSourceHistory(historyToken))throw new Error("讀取期間來源面或角材已改變，請重新「使用目前面」，以免混用不同版本的資料。");
      renderSource({kind:"scene",name:"面 #"+surface.boundary,base_scene:dump.text,placement_id:surface.id,boundary_id:surface.boundary,face_key:faceKey(surface.boundary),source_z:surface.origin?.[2],frame:{origin:copy(surface.origin),u:copy(surface.u),v:copy(surface.v)},projection:ReferenceWorkspace.getFaceProjection?.(surface.boundary,surface.id)||null,timbers,history_token:historyToken,loops:boundary.loops,context_id:sourceContextId});
      const restored=restoreDraft(state.source);
      setTab("setup");dialog.querySelector('.sm-setup-scroll').scrollTop=0;
      message(restored?"已保留這個來源的未完成設定。請更新預覽並重新核對，再建立空間。":validProjection(state.source.projection)?"設定牆底後即可預覽。若從 z=0 起，可按「牆底設為 0 mm」；牆高與牆厚可修改。":"在這裡確認平面投影用途與觀看方向，再指定牆底，即可預覽空間。");
    } catch(e) { if(seq===state.sequence){state.phase="error";message(e.message,"error");$("smSourceSummary").textContent=e.message;updateActions();} }
  }
  function toggleMode(mark = true) { const faces=$("smMode").value==="faces"; $("smPlanSettings").hidden=faces; $("smFaceSettings").hidden=!faces; if(mark)stale(); }
  function assertPlanProjection() {
    if(state.editing||$("smMode").value!=="plan")return;
    if(!state.source||state.source.context_id!==contextId())throw new Error("專案已切換，請重新選取來源面。");
    if(!validProjection(state.source.projection))throw new Error("請先選擇俯視或仰視，再按「確認用途與觀看方向」，指定輪廓內淨空及外側材料牆。");
    if(state.source.frame?.u?.[2]!==0||state.source.frame?.v?.[2]!==0)throw new Error("此來源不是水平放置面，請先調整放置或改用「組合已有的放置面」。");
    if(JSON.stringify(currentProjection())!==JSON.stringify(state.source.projection))throw new Error("平面投影定義已改變，請重新設定或選取來源，再更新預覽。");
  }
  function projectionChanged() {
    if(!state.source||state.source.kind!=="scene"||state.readonly||state.editing||state.createdId)return;
    if(state.source.context_id!==contextId()){state.controller?.abort();state.sequence++;state.previewRevision=-1;state.phase="stale";message("專案已切換，請重新選取來源面。","warning");updateActions();return;}
    const projection=currentProjection();
    if(JSON.stringify(projection)===JSON.stringify(state.source.projection))return;
    const projectionOnly=onlyProjectionChanged(state.source);
    state.controller?.abort();state.controller=new AbortController();state.sequence++;state.phase="ready";state.source.projection=projection;
    // A committed definition replaces the inline draft. Ordinary rendering
    // must not overwrite a direction the user has selected but not confirmed.
    $('smProjectionView').value=projection?.view||'top';
    if(projectionOnly)state.source.history_token=sourceHistoryToken();
    stale();renderOutline(state.source.loops||[]);
    if(!projectionOnly){state.phase="stale";state.previewRevision=-1;message("投影定義已保存，但來源讀取後還有其他編輯、復原或重做。請重新「使用目前面」取得最新來源；修改投影不能恢復過期預覽。","warning");updateActions();return;}
    message(validProjection(projection)?"平面投影定義已更新，原有高度及牆厚設定已保留。請重新更新預覽並核對。":"平面投影定義已移除。請先設定用途及方向，才能由輪廓建立空間。","warning");
  }
  async function confirmProjection() {
    const source=state.source;
    if(!source||$('smConfirmProjection').disabled||!dialog.open)return;
    const serial=++state.projectionSequence,seq=state.sequence,view=$('smProjectionView').value,original=JSON.stringify(currentProjection(source));
    state.projectionPending=true;updateActions();message('正在核對來源面與放置，確認後保留目前高度及材料設定…');
    const active=()=>serial===state.projectionSequence&&seq===state.sequence&&state.source===source&&dialog.open&&$('smProjectionView').value===view;
    try {
      const dump=await api('dump');if(!active())return;
      if(source.context_id!==contextId()||source.face_key!==faceKey(source.boundary_id)||!sameSourceHistory(source.history_token)||!dump.ok||dump.text!==source.base_scene)throw new Error('來源或專案已變更。請重新「使用目前面」，核對後再確認用途。');
      const placements=await api('surfaces');if(!active())return;
      const surface=placements.ok&&placements.surfaces?.find(s=>s.id===source.placement_id&&s.boundary===source.boundary_id);
      const checked=await api('dump');if(!active())return;
      if(source.context_id!==contextId()||source.face_key!==faceKey(source.boundary_id)||!sameSourceHistory(source.history_token)||!checked.ok||checked.text!==source.base_scene||!surface||JSON.stringify({origin:surface.origin,u:surface.u,v:surface.v})!==JSON.stringify(source.frame)||JSON.stringify(currentProjection(source))!==original)throw new Error('核對期間來源面、放置或定義已變更。請重新「使用目前面」再設定。');
      if(surface.u?.[2]!==0||surface.v?.[2]!==0||Math.abs(surface.u[0]*surface.v[1]-surface.u[1]*surface.v[0])!==1||!['top','bottom'].includes(view))throw new Error('平面投影需要水平放置與明確觀看方向。');
      if(validProjection(source.projection)&&source.projection.view===view&&needsDrawingAlignment(source,view)) {
        const candidate=GeometryModelViewer.drawingAlignment(source.frame,source.loops,view).frame;
        const axis=a=>AXIS_WORD[a.join()];
        const line=`placement ${source.placement_id} on boundary ${source.boundary_id} origin ${candidate.origin.join(' ')} u ${axis(candidate.u)} v ${axis(candidate.v)}`;
        // The ordinary native path owns I8/I8a preview, cancellation and one undo.
        // Projection metadata stays unchanged; no mixed native/local transaction.
        if(!await mutate([line])) {if(active())message('方向對齊未套用；原放置保持不變。','warning');return;}
        if(!active()||source.context_id!==contextId()||source.face_key!==faceKey(source.boundary_id))return;
        await renderObjects();if(!active())return;
        const token=sourceHistoryToken(),updated=await api('surfaces'),references=await api('references'),nextDump=await api('dump');
        if(!active())return;
        const placed=updated.ok&&updated.surfaces?.find(s=>s.id===source.placement_id&&s.boundary===source.boundary_id);
        if(!sameSourceHistory(token)||!nextDump.ok||!placed||JSON.stringify({origin:placed.origin,u:placed.u,v:placed.v})!==JSON.stringify(candidate))throw new Error('對齊後來源又有變更，請重新「使用目前面」核對。');
        source.base_scene=nextDump.text;source.frame=candidate;source.history_token=token;source.timbers=sourceTimbers(references,source.placement_id);
        const includeTimbers=$('smIncludeTimbers').checked;renderTimberCandidates(source);$('smIncludeTimbers').checked=includeTimbers;
        state.result=null;state.input=null;state.phase='ready';state.previewRevision=-1;state.viewer?.setObjects([]);$('smResultBadge').textContent='方向已對齊，待預覽';
        $('smPreviewDetails').hidden=true;$('smGeneratedFaces').innerHTML='';
        for(const id of ['smVolume','smClearance','smWallVolume','smTimberVolume'])$(id).textContent='—';
        stale();renderOutline(source.loops);message('放置已依原圖方向對齊，尺寸、外框位置及圖面高度保留。牆底、牆高與材料設定也保留；請更新預覽。','success');
        return;
      }
      ReferenceWorkspace.setFaceProjection(source.boundary_id,source.placement_id,{kind:'space-boundary-plan',view,region:'interior',wallSide:'outside'});
      projectionChanged();
      message('已確認用途與觀看方向，現有設定已保留。指定牆底後按「更新預覽」；定義會隨專案保存。','success');
      const next=$('smBottom').value.trim()?$('smPreview'):$('smBottom');next.scrollIntoView({block:'center'});next.focus();
    } catch(e) {if(active()){state.previewRevision=-1;message(e.message,'error');}}
    finally {if(serial===state.projectionSequence){state.projectionPending=false;updateActions();}}
  }
  async function editProjection() {
    const source=state.source;if(!source||source.kind!=="scene"||state.readonly||state.editing||state.createdId)return;
    if(!window.FaceProjection?.open){message("平面投影設定尚未載入，請確認已開啟最新版本。","error");return;}
    try {await FaceProjection.open(source.boundary_id,source.placement_id,{onApplied:applied=>{
      if(state.source!==source||source.context_id!==contextId())return;
      projectionChanged();setTab("setup");
      if(applied.placement_id!==source.placement_id){message("已保存其他放置面的投影定義。請在來源放置面選單選取該面，再建立空間。","warning");return;}
      if(!sameSourceHistory(source.history_token))return;
      if(validProjection(source.projection)){const next=$("smBottom").value.trim()?$("smPreview"):$("smBottom");next.scrollIntoView({block:"center"});next.focus();message("平面投影已設定。請填寫牆底標高（若從 z=0 起請填 0），再按「更新預覽」。");}
    }});}catch(e){message(e.message,"error");}
  }
  function readInteger(id, label, positive = false) { const raw=$(id).value.trim(),number=Number(raw); if(!raw||!Number.isSafeInteger(number)||(positive&&number<=0)){setTab("setup");$(id).scrollIntoView({block:"center"});$(id).focus();throw new Error(id==="smBottom"?"請明確填寫牆底標高；若從 z=0 起請填 0。圖面 z 是位置，不能代替牆底。":`請填寫${label}${positive?"（大於 0 的整數 mm）":"（整數 mm）"}。`);} return number; }
  function makeInput() {
    if(!state.source)throw new Error("請先選擇來源。");
    if(state.editing) { assertEditableRecord(); const input=copy(state.editing.record.input); input.settings.height=readInteger("smEditHeight","新牆高",true); return input; }
    assertSourceHistory();
    assertPlanProjection();
    const input={base_scene:state.source.base_scene,mode:$("smMode").value,obstacles:[...dialog.querySelectorAll("[data-sm-obstacle]:checked")].map(e=>({kind:e.dataset.smObstacle,id:Number(e.value)}))};
    if(input.mode==="faces") { input.uses=[...dialog.querySelectorAll("[data-sm-face]:checked")].map(e=>({placement_id:Number(e.dataset.smFace),orientation:Number(dialog.querySelector(`[data-sm-orientation="${e.dataset.smFace}"]`).value),purpose:dialog.querySelector(`[data-sm-purpose="${e.dataset.smFace}"]`).value})); if(!input.uses.length)throw new Error("請至少選取一個已放置的面，並核對方向及用途。"); }
    else {input.placement_id=state.source.placement_id; input.settings={bottom:readInteger("smBottom","牆底標高"),height:readInteger("smHeight","牆高",true),edges:[...dialog.querySelectorAll("[data-sm-edge]:checked")].map(e=>Number(e.dataset.smEdge)),floor:$("smFloor").value,ceiling:$("smCeiling").value,holes:$("smHoles").value,wall_thickness:$("smWallsEnabled").checked?readInteger("smThickness","牆厚",true):null};if((state.source.loops?.length||0)>1&&input.settings.holes==='none'){setTab('setup');$('smHoles').scrollIntoView({block:'center'});$('smHoles').focus();throw new Error('此平面含有孔洞，請明確指定「平面孔洞的用途」，不會自動猜成門窗或柱。');}if($("smIncludeTimbers").checked&&(state.source.timbers||[]).length)input.timbers=state.source.timbers.map(t=>({kind:"timber",id:t.id}));}
    return input;
  }
  function metric(value,maximumFractionDigits=3) { const number=typeof value==="string"&&/^-?\d+$/.test(value)?Number(value):value; return typeof number==="number"&&Number.isFinite(number) ? new Intl.NumberFormat("zh-TW",{maximumFractionDigits}).format(number/1e9)+" m³" : "尚未確定"; }
  function wallRequirementMissing(input,result) {
    return input?.mode==='plan' && input.settings?.wall_thickness!=null && (!result?.walls || !!result.summary?.wall_diagnostics?.length);
  }
  function assertWallRequirement(input,result) {
    if(wallRequirementMissing(input,result))throw new Error('指定的材料牆未完整產生，這次預覽不能建立或更新。請減少來源場景或選邊；若只需要空間邊界，請明確取消材料牆後重新預覽。');
  }
  function renderResult(result, fit = true) {
    const s=result.summary,wallMissing=wallRequirementMissing(state.input,result);
    $("smVolume").textContent=metric(s.volume_mm3); $("smClearance").textContent=metric(s.clearance_mm3); $("smWallVolume").textContent=s.wall_volume_mm3==null?(s.wall_diagnostics?.length?"未能建立":"未建立"):metric(s.wall_volume_mm3);
    $("smTimberVolume").textContent=result.timbers?metric(s.timber_volume_mm3,9):"未納入";
    $("smTimberVolume").title=result.timbers?`${s.timber_volume_mm3} mm³；各支角材材料量合計`:"";
    const timberObjects=result.timbers?.derived?.objects||[],count=s.timber_count||0;
    $("smTimberReview").textContent=count?`本次納入 ${count} 支角材。它們各自保留原位置及尺寸，不會變成空間殼或自動扣除淨空。`:(state.input?.mode==="faces"?"本次組合已有面，未納入角材。":"本次未納入角材；已保存模型不會自動補入來源中其他角材。");
    $("smTimberReviewList").hidden=!count;
    const list=$("smTimberReviewList");
    if(state.readonly&&!state.editing&&state.input?.mode==='plan'&&count){
      list.replaceChildren();
      $('smShowTimbers').closest('.sm-display-options').after(list);
    }else{
      $('smTimberReview').after(list);
      list.innerHTML='<ul>'+timberObjects.map(o=>{const zs=o.vertices_mm.map(p=>p[2]),lo=Math.min(...zs),hi=Math.max(...zs);return `<li><strong>角材 #${esc(o.root?.id)}</strong><span>世界 z：${esc(lo)}～${esc(hi)} mm${typeof s.top==="number"&&hi>s.top?" · 高於空間牆頂，保留原位置":""}</span></li>`;}).join("")+'</ul>';
    }
    $("smResultBadge").textContent=wallMissing?"材料牆缺失 · 未滿足建模要求":s.closed?"已封閉 · 可計算體積":"開放空間 · 體積未定"; $("smResultBadge").dataset.state=wallMissing?"stale":s.closed?"complete":"open";
    $("smPreviewDetails").hidden=false;
    $("smPreviewDescription").textContent=`共 ${s.face_count} 個面${typeof s.bottom==="number"?`，牆底 ${s.bottom} mm、牆頂 ${s.top} mm`:""}。${s.closed?"邊界已封閉。空間體積、扣除後淨空與材料量分別呈現。":"可建立部分空間；尚未封閉，因此沒有確定的內部體積。"}`;
    const purposes=(s.generated_faces||[]).reduce((totals,face)=>{totals[face.purpose]=(totals[face.purpose]||0)+1;return totals;},{});
    const purposeSummary=[purposes.boundary?`${purposes.boundary} 面實際邊界`:null,purposes['calculation-cap']?`${purposes['calculation-cap']} 面計算封口`:null].filter(Boolean).join('、');
    const wallSummary=wallMissing?'要求的材料牆未完整產生':result.walls?`材料牆 ${state.input?.settings?.wall_thickness} mm`:s.wall_diagnostics?.length?'材料牆未能建立':'未建立材料牆';
    $('smCommitSummary').textContent=`${s.closed?'封閉空間':'開放空間，體積未定'} · ${s.face_count} 個面${typeof s.bottom==='number'?` · z ${s.bottom}～${s.top} mm`:''}。${purposeSummary?purposeSummary+'。':''}${wallSummary}；角材 ${count} 支。`;
    $('smReviewFaces').open=false;
    $("smGeneratedFaces").innerHTML=(s.generated_faces||[]).map(f=>`<li><strong>${esc(f.label||"放置面 #"+f.placement_id)}</strong><span>#${f.placement_id} · ${f.orientation===-1?"−1":"+1"} · ${f.purpose==="calculation-cap"?"僅作體積計算封口":"實際邊界"}</span></li>`).join("");
    const missing=[...(s.missing||[]),...(s.wall_diagnostics||[]).map(d=>typeof d==="string"?d:d.message||d.code||"材料牆尚未確定"),...(wallMissing?['此保存模型要求材料牆，但結果未完整包含材料牆。原記錄保留；不能把它當成已完成材料的模型。']:[])];
    $("smMissing").hidden=!missing.length; $("smMissing").innerHTML=missing.map(d=>`<p>${esc(d)}</p>`).join("");
    for(const option of $("smExportKind").options)option.disabled=!result[option.value];
    drawResult(fit);
  }
  function drawResult(fit = false) {
    if(!state.result||!state.viewer)return;
    const objects=GeometryModelViewer.spacePreviewObjects(state.result,{space:$("smShowSpace").checked,walls:$("smShowWalls").checked,timbers:$("smShowTimbers").checked,roof:$("smShowRoof").checked});
    const selected=state.viewer.getState().selection;
    state.viewer.setPlanFrame(state.source?.frame||GeometryModelViewer.placementFrame(state.input?.base_scene,state.source?.placement_id));
    state.viewer.setObjects(objects); if(fit)state.viewer.fit();
    if(snapshotRecord()&&snapshotNavigation?.isCurrent()){state.viewer.setSelectableRoots(state.input.timbers);if(selected&&!state.viewer.selectRoot(selected))selectSnapshotTimber(null,false);}
  }
  async function preview() {
    let input; try{input=makeInput();}catch(e){state.phase="error";state.previewRevision=-1;$("smConfirmFaces").checked=false;$("smResultBadge").textContent="預覽已失效，請重新確認來源與設定";$("smResultBadge").dataset.state="stale";message(e.message,"error");setTab("setup");updateActions();return;}
    const seq=state.sequence,revision=state.revision,source=state.source,sourceContextId=contextId(); state.phase="previewing"; state.createdId=null; $("smConfirmFaces").checked=false; updateActions(); message("正在推導各面、檢查封閉狀態與材料幾何…");
    try {
      if(input.timbers)await requireTimberCapability();
      if(seq!==state.sequence)return;
      if(sourceContextId!==contextId())throw new Error("目前專案已切換，請重新選取來源。");
      assertSourceHistory();
      if(!state.editing&&source.kind==="scene") {
        const dump=await api("dump");
        if(seq!==state.sequence)return;
        if(sourceContextId!==contextId()||!dump.ok||dump.text!==source.base_scene)throw new Error("來源面或角材已變更。請重新「使用目前面」取得最新來源，再更新預覽。");
      }
      const result=await request("/model/space-preview",input);
      if(seq!==state.sequence)return;
      if(sourceContextId!==contextId())throw new Error("目前專案已切換，請重新選取來源。");
      if(!state.editing&&source.kind==="scene") {
        const dump=await api("dump");
        if(seq!==state.sequence)return;
        if(sourceContextId!==contextId()||!dump.ok||dump.text!==source.base_scene)throw new Error("預覽期間來源面或角材已變更。請重新「使用目前面」，這次過期預覽不能建立。");
      }
      if(revision!==state.revision){state.phase="ready";message("計算途中設定已變更，請重新更新預覽。","warning");return;}
      assertSourceHistory();
      assertPlanProjection();
      if(!result.summary||!result.space)throw new Error("預覽回應缺少空間或摘要，無法建立。");
      assertWallRequirement(input,result);
      if(input.timbers&&(!result.timbers||result.summary.timber_count!==input.timbers.length))throw new Error("指定角材未完整產生，這次預覽不能建立。請查看來源角材，或明確取消納入後重試。");
      state.result=result; state.input=input; state.previewRevision=revision; state.phase="preview"; renderResult(result);
      message(state.editing?"新牆高的預覽已完成，原模型仍保持不變。核對面清單並勾選確認後，按「更新空間」。":result.summary.closed?"預覽已完成。核對面清單並勾選確認後，即可建立空間。":"這是合法的開放空間。體積尚未確定；核對面清單後仍可建立。",!result.summary.closed?"warning":"success");
    } catch(e) {if(e.name!=="AbortError"&&seq===state.sequence){state.phase="error";state.previewRevision=-1;$("smResultBadge").textContent="預覽未完成";$("smResultBadge").dataset.state="stale";message(e.message,"error");}}
    finally{if(seq===state.sequence)updateActions();}
  }
  async function create() {
    if($("smCreate").disabled)return;
    const revision=state.revision,seq=state.sequence; state.phase="creating";updateActions();
    try {
      assertWallRequirement(state.input,state.result);
      if(state.source.context_id!==contextId())throw new Error("目前專案已切換，請重新選取來源並更新預覽。");
      if(state.editing) {
        assertEditableRecord();
        if(seq!==state.sequence||revision!==state.revision||state.previewRevision!==revision)throw new Error("牆高已改變，請更新預覽後再保存。");
        const record={...copy(state.editing.record),input:copy(state.input),result:copy(state.result)};
        state.committingId=record.id;
        try { ReferenceWorkspace.updateSpaceModel(record.id,record); } finally { state.committingId=null; }
        openRecord(record.id); setTab("setup");
        message(`「${record.name}」牆高已更新為 ${record.input.settings.height} mm。可復原這次修改；請保存專案。`,"success");
        return;
      }
      if(state.source.kind==="scene") {const dump=await api("dump");if(!dump.ok||dump.text!==state.source.base_scene)throw new Error("來源場景已修改。請重新「使用目前面」並更新預覽，避免保存過期幾何。");}
      if(seq!==state.sequence||revision!==state.revision)throw new Error("設定已改變，請更新預覽後再建立。");
      assertSourceHistory();
      if(state.source.context_id!==contextId())throw new Error("目前專案已切換，請重新選取來源並更新預覽。");
      assertPlanProjection();
      const record={id:crypto.randomUUID(),name:$("smModelName").value.trim()||"未命名空間",created_at:new Date().toISOString(),source:{kind:state.source.kind,placement_id:state.source.placement_id,boundary_id:state.source.boundary_id,scene_hash:state.result.source_sha256,...(state.input.mode==="plan"?{projection:copy(state.source.projection)}:{})},input:copy(state.input),result:copy(state.result)};
      ReferenceWorkspace.addSpaceModel(record); draft=null;state.createdId=record.id;state.recordSignature=JSON.stringify(record);state.phase="created";message(`「${record.name}」已加入目前專案，尚未保存成檔案。請按「保存專案 .gcanvas」，之後可完整重開。`,"success");refresh();
    }catch(e){if(seq===state.sequence){state.phase="error";state.previewRevision=-1;message(e.message,"error");}}
    finally{updateActions();}
  }
  function libraryList() {
    const models=ReferenceWorkspace.getSpaceModels?.()||[]; $("smModelCount").textContent=String(models.length); if($("spaceModelCount"))$("spaceModelCount").textContent=String(models.length);
    $("smLibraryList").innerHTML=models.length?models.map(m=>`<article class="sm-model-card"><div class="sm-model-symbol" aria-hidden="true">▱</div><div><h3>${esc(m.name)}</h3><p>${wallRequirementMissing(m.input,m.result)?"材料牆缺失 · 未滿足要求":m.result.summary.closed?"封閉空間":"開放空間"} · ${m.result.summary.face_count} 個面 · ${esc(metric(m.result.summary.volume_mm3))} · 角材 ${esc(m.result.summary.timber_count||0)} 支</p><small>${esc(new Date(m.created_at).toLocaleString("zh-TW"))} · 來源${m.source.kind==="example"?"範例":"面 #"+m.source.boundary_id}</small></div><div class="sm-model-actions"><button class="sm-button" data-sm-open-model="${esc(m.id)}" type="button">開啟 3D</button>${m.input.mode==="plan"?`<button class="sm-button" data-sm-edit-height="${esc(m.id)}" type="button">修改模型</button>`:""}<button class="sm-button sm-danger" data-sm-remove-model="${esc(m.id)}" type="button">移除</button></div></article>`).join(""):'<div class="sm-library-empty"><h3>還沒有建立空間</h3><p>選一個範例，核對預覽後按「建立空間」，它就會出現在這裡。</p><button class="sm-button sm-primary" data-sm-library-trial type="button">試用矩形範例 →</button></div>';
  }
  function openLibrary(){clearSnapshotNavigation();if(state.editing)cancelHeightEdit();if(!show(openLibrary))return;libraryList();$("smLibraryPanel").hidden=false;$("smMain").hidden=true;dialog.classList.add("sm-in-library");window.dispatchEvent(new Event('space-model-view-changed'));}
  function openRecord(id, display = true) {
    const record=ReferenceWorkspace.getSpaceModels().find(m=>m.id===id); if(!record)return;
    const ctx=ReferenceWorkspace.context(),pin=JSON.stringify(record);
    // show() refreshes saved records; clear the previous signature before entering it.
    state.recordSignature=null;
    if(display&&!show(()=>{const current=ReferenceWorkspace.getSpaceModels().filter(m=>m.id===id);if(ReferenceWorkspace.context()===ctx&&current.length===1&&JSON.stringify(current[0])===pin)openRecord(id,display);}))return;
    state.recordSignature=null;startSource();const input=record.input,s=record.result.summary;
    // A saved definition keeps its source snapshot. Height editing changes only its explicit height.
    state.source={kind:record.source.kind,name:record.name,base_scene:input.base_scene,placement_id:record.source.placement_id,boundary_id:record.source.boundary_id,source_z:s.source_z,projection:record.source.projection?copy(record.source.projection):null,context_id:contextId()};
    state.result=copy(record.result);state.input=copy(input);state.previewRevision=state.revision;state.createdId=id;state.recordSignature=JSON.stringify(record);state.phase="created";state.readonly=true;
    savedContext=ctx;
    $("smPreviewTitle").textContent=record.name;$("smModelName").value=record.name;$("smSourceSummary").innerHTML=`<strong>${esc(record.name)}</strong><span>已建立的空間 · ${s.face_count} 個面 · 角材 ${s.timber_count||0} 支${input.mode==="plan"?` · 牆高 ${esc(input.settings.height)} mm`:""}</span><small>${input.mode==="plan"?"可用「修改牆高」更新此模型。輪廓沿用保存的定義，不會自動讀取畫布的新變更。":"這是保存的各面定義。若要改變成員，請重新選取放置面建立。"}</small>`;
    $("smMode").value=input.mode;$("smSourceSelectWrap").hidden=true;$("smSettings").disabled=true;$("smConfirmFaces").checked=true;toggleMode(false);renderResult(state.result);updateActions();$("smPreview").disabled=true;setTab("preview");message(wallRequirementMissing(input,state.result)?"此保存模型的材料牆缺失，未滿足原建模要求。原記錄保留；可查看已有邊界，修改仍須完整通過預覽。":"已開啟保存的模型。可旋轉查看、匯出模型或保存專案。",wallRequirementMissing(input,state.result)?"warning":"success");
    window.dispatchEvent(new Event('space-model-view-changed'));
  }
  function assertEditableRecord() {
    const editing=state.editing;
    if(!editing||editing.context_id!==contextId())throw new Error("專案已切換，這次修改已失效。請重新開啟要修改的模型。");
    const current=ReferenceWorkspace.getSpaceModels().find(m=>m.id===editing.record.id);
    if(!current||JSON.stringify(current)!==JSON.stringify(editing.record))throw new Error("原模型已被修改、移除或復原。請重新開啟模型後再修改牆高。");
  }
  function beginHeightEdit(id = state.createdId) {
    const record=ReferenceWorkspace.getSpaceModels().find(m=>m.id===id);
    if(!record||record.input.mode!=="plan")return;
    if(!state.viewer&&!show(()=>beginHeightEdit(id)))return;
    openRecord(id);
    state.editing={record:copy(record),context_id:contextId()};state.createdId=null;state.phase="editing";state.previewRevision=-1;
    $("smEditHeight").value=record.input.settings.height;$("smConfirmFaces").checked=false;
    $("smHeightEditSummary").textContent=`目前牆高 ${record.input.settings.height} mm，牆底 ${record.input.settings.bottom} mm。此處沿用保存來源只改牆高；採用現行畫布來源須另行明選及核對差異。`;
    $("smResultBadge").textContent="原模型 · 修改後請更新預覽";$("smResultBadge").dataset.state="stale";
    updateActions();setTab("setup");$("smHeightEditPanel").scrollIntoView({block:"start"});$("smEditHeight").focus();
    message("輸入新牆高後，按「更新預覽」。只有核對並按「更新空間」才會修改原模型。");
  }
  function cancelHeightEdit() {
    const id=state.editing?.record.id;if(!id)return;
    if(ReferenceWorkspace.getSpaceModels().some(m=>m.id===id))openRecord(id,dialog.open);
    else {startSource();state.phase="empty";updateActions();}
    message("已取消牆高修改，未改動已保存的模型。");
  }
  function refresh() {
    libraryList();
    if(state.editing && state.committingId!==state.editing.record.id) {
      try { assertEditableRecord(); }
      catch(e) {state.controller?.abort();state.sequence++;state.editing=null;state.source=null;state.result=null;state.input=null;state.createdId=null;state.previewRevision=-1;state.phase="stale";state.viewer?.setObjects([]);$("smPreviewDetails").hidden=true;$("smSourceSummary").textContent="這次修改已失效。請從「已建立空間」重新開啟模型。";$("smResultBadge").textContent="模型已變更，請重新開啟";for(const id of ["smVolume","smClearance","smWallVolume","smTimberVolume"])$(id).textContent="—";message(e.message,"warning");updateActions();}
    }
    if(state.createdId && state.recordSignature && dialog.open) {
      const current=ReferenceWorkspace.getSpaceModels().find(m=>m.id===state.createdId);
      if(current && JSON.stringify(current)!==state.recordSignature){openRecord(current.id);message("模型已更新或復原，目前顯示專案中的最新保存內容。");return;}
    }
    if(state.createdId && !(ReferenceWorkspace.getSpaceModels?.()||[]).some(m=>m.id===state.createdId)){clearSnapshotNavigation();state.viewer?.setObjects([]);state.result=null;state.createdId=null;state.previewRevision=-1;state.phase="stale";message("這個模型已移除或復原。請重新選取來源再建立。","warning");updateActions();}
    if(state.source&&state.source.context_id!==contextId()&&state.previewRevision===state.revision){state.previewRevision=-1;message("目前專案已切換。請重新選擇來源，以免使用上個專案的預覽。","warning");updateActions();}
  }
  function exportModel(){const pack=state.result?.[$("smExportKind").value];if(!pack){message("這個結果尚未確定，沒有可匯出的模型。","warning");return;}const a=document.createElement("a"),url=URL.createObjectURL(new Blob([JSON.stringify(pack,null,2)],{type:"application/json"}));a.href=url;a.download=($("smModelName").value.trim()||"空間").replace(/[\\/:*?"<>|]/g,"_")+"-"+$("smExportKind").value+".model.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message("模型下載已開始；.model.json 保留完整定義與推導資料。","success");}
  $("smClose").onclick=close;$("smTryTimberFrame").onclick=()=>openExample("timber-frame"); $("smTryRectangle").onclick=()=>openExample();$("smTryLShape").onclick=()=>openExample("l-shape");$("smWelcomeTry").onclick=()=>openExample();$("smUseCurrent").onclick=()=>openCurrentFace();$("smLibrary").onclick=openLibrary;$("smBackToBuild").onclick=buildView;
  $("smBackToTimbers").onclick=async()=>{const source=state.source;if(!source||source.kind!=="scene"||source.context_id!==contextId())return;close();if(oc.edit?.bid!==source.boundary_id)await enterFocus("face",source.boundary_id);if(source.context_id!==contextId())return;fiShowTab("timber");if(innerWidth<=680)openPanel("right",$("workspaceToggleRight"));};
  $("smTabPreview").onclick=()=>setTab("preview");$("smTabSetup").onclick=()=>setTab("setup");$("smPreview").onclick=preview;$("smCreate").onclick=create;$("smConfirmFaces").onchange=updateActions;
  $("smCurrentSourceUpdate").onclick=()=>{const id=state.editing?.record.id;if(id){close();void window.ModelUpdateApp.open(id);}};
  $("smEditHeightButton").onclick=()=>beginHeightEdit();$("smCancelHeightEdit").onclick=cancelHeightEdit;$("smEditHeight").addEventListener("input",stale);
  $("smSetProjection").onclick=editProjection;
  $('smConfirmProjection').onclick=confirmProjection;
  $('smProjectionView').onchange=()=>{const pending=state.projectionPending;cancelProjectionConfirmation();updateActions();if(pending)message('觀看方向已變更，請重新確認用途與觀看方向。');};
  $('smBottomZero').onclick=()=>{$('smBottom').value='0';stale();message('牆底已明確設為 0 mm；圖面維持原來的 z。確認設定後按「更新預覽」。');$('smBottom').focus();};
  dialog.addEventListener("cancel",()=>{viewerOpenSequence++;state.viewerLoading=false;rememberDraft();cancelProjectionConfirmation();cancelSourceLoad();});
  dialog.addEventListener("close",()=>{viewerOpenSequence++;clearSnapshotNavigation();state.viewerLoading=false;rememberDraft();cancelProjectionConfirmation();cancelSourceLoad();if(state.editing)cancelHeightEdit();window.dispatchEvent(new Event('space-model-view-changed'));});
  const reviewJump=()=>{setTab("setup");if(state.result&&state.previewRevision===state.revision){$('smReviewFaces').open=true;$("smPreviewDetails").scrollIntoView({block:"start"});}};$("smReviewJump").onclick=reviewJump;
  $('smMobileNext').onclick=()=>{setTab('setup');if(state.result&&state.previewRevision===state.revision&&!state.createdId)$('smConfirmFaces').focus({preventScroll:true});};
  $("smSourceSelect").onchange=()=>openCurrentFace($("smSourceSelect").value);$("smMode").onchange=()=>toggleMode();$("smFit").onclick=()=>state.viewer?.fit();
  for(const id of ["smShowSpace","smShowWalls","smShowTimbers","smShowRoof"])$(id).onchange=()=>drawResult();
  dialog.querySelectorAll("[data-sm-view]").forEach(button=>button.onclick=()=>{state.viewer?.setView(button.dataset.smView);dialog.querySelectorAll("[data-sm-view]").forEach(b=>{b.classList.toggle("active",b===button);b.setAttribute("aria-pressed",String(b===button));});});
  $("smSettings").addEventListener("input",()=>{stale();$("smObstacleCount").textContent=String(dialog.querySelectorAll("[data-sm-obstacle]:checked").length);});
  $("smModelName").addEventListener("input",()=>{if(state.createdId)message("若要以新名稱建立模型，請重新選擇來源。此處不會改動已保存的模型。","warning");});
  $("smExport").onclick=exportModel;
  $("smLibraryList").addEventListener("click",e=>{const open=e.target.closest("[data-sm-open-model]"),edit=e.target.closest("[data-sm-edit-height]"),remove=e.target.closest("[data-sm-remove-model]");if(open)openRecord(open.dataset.smOpenModel);else if(edit)beginHeightEdit(edit.dataset.smEditHeight);else if(remove){ReferenceWorkspace.removeSpaceModel(remove.dataset.smRemoveModel);refresh();}else if(e.target.closest("[data-sm-library-trial]"))openExample();});
  window.addEventListener("space-models-changed",refresh);
  window.addEventListener("face-projections-changed",projectionChanged);
  $("btnSpaceModelTrial")?.addEventListener("click",()=>openExample());$("btnSpaceModels")?.addEventListener("click",openLibrary);
  probeCapabilities();
  if(["#space-model-v1","#timber-space-v1"].includes(location.hash)) { const deadline=Date.now()+30000; const autoOpen=()=>{if(connection.phase==="ready")openExample(location.hash==="#timber-space-v1"?"timber-frame":"rectangle");else if(Date.now()<deadline)setTimeout(autoOpen,150);};setTimeout(autoOpen,0); }
  return {openCurrentFace,openLibrary,openExample,close,refresh,snapshotRecord,authorizeSnapshotSchedule,selectSnapshotTimber,snapshot:()=>({phase:state.phase,sourceKind:state.source?.kind||null,resultSummary:state.result?copy(state.result.summary):null,createdId:state.createdId,editingId:state.editing?.record.id||null,supportsTimbers,timberCandidates:copy(state.source?.timbers||[]),stale:state.previewRevision!==state.revision,previewRevision:state.previewRevision,inputRevision:state.revision,viewer:state.viewer?.getState()||null})};
})();
