/* #54: proposals use the existing face draft, native boundary transaction and project history. */
'use strict';
const RoomOutlineWorkspace=(()=>{
  const R=RoomOutline,P=GeometryProject,W=ReferenceWorkspace,esc=W.escape;
  let draft=null,picking=null,acquiring=null,generation=0,message='',options=null,barriers=[],barrierStamp=null;
  const pending=bid=>!!draft&&draft.bid===bid;
  const sourceCurrent=d=>!!d&&oc.edit?.bid===d.bid&&W.getProjectState().contextToken===d.contextToken&&W.history.frame.ids.get(d.bid)===d.incarnation&&W.active(d.bid)?.id===d.pageId&&P.reviewBasis(W.active(d.bid))===d.basis;
  const current=d=>sourceCurrent(d)&&P.outlineFingerprint(oc.bmap[d.bid])===d.baseGeometry;
  function stamp(bid) {
    W.assertEditable();const p=W.active(bid);
    if(!p?.calibration)throw Error('請先校準目前來源頁，再取得房間候選。');
    return {bid,contextToken:W.getProjectState().contextToken,incarnation:W.history.frame.ids.get(bid),pageId:p.id,basis:P.reviewBasis(p),baseGeometry:P.outlineFingerprint(oc.bmap[bid])};
  }
  function refresh(){if(oc.edit){drawFaceEditor();renderFaceInspector();document.getElementById('refOutlineDetails')?.setAttribute('open','');}W.present();}
  function notice(text){message=text;setStatus(text);refresh();}
  function calibrated(){message='';}
  function reset(clear=true){generation++;picking=null;acquiring=null;draft=null;barriers=[];barrierStamp=null;options=null;message='';if(clear&&typeof fe!=='undefined'){fe.draft=PolyDraft.createState();fe.draftPreview=null;feSyncDraftMirror();feLenShow();}}
  function invalidate(){if((draft&&!draft.committing&&!current(draft))||(picking&&!current(picking))||(acquiring&&!current(acquiring))||(barrierStamp&&!current(barrierStamp))){reset();message='來源頁、校準／對位或原面已變更，舊候選已失效。請重新取得；正式面尺寸未縮放。';if(oc.edit){drawFaceEditor();renderFaceInspector();}}}
  window.addEventListener('project-info-changed',invalidate);
  function readOptions(pane,bid) {
    const pdf=W.context().sources.get(W.active(bid)?.sourceId)?.meta.type==='application/pdf';
    const o={mode:pane.querySelector('#refRoomMethod')?.value||'auto',minWidth:Number(pane.querySelector('#refRoomMinWidth')?.value|| (pdf?1:2)),minLength:Number(pane.querySelector('#refRoomMinLength')?.value||(pdf?8:24))};
    if(!Number.isFinite(o.minWidth)||o.minWidth<=0||o.minWidth>1000||!Number.isFinite(o.minLength)||o.minLength<=0||o.minLength>1e6)throw Error('線寬與最短線須為正值。');
    return o;
  }
  function start(bid,pane,mode='room') {
    try {
      const s=stamp(bid),o=readOptions(pane,bid);
      if(barrierStamp&&!current(barrierStamp)){barriers=[];barrierStamp=null;}
      if(fe.draft?.pts?.length&&!draft)throw Error('請先套用或取消人工外環草稿。');
      if(o.mode==='manual'&&mode==='room'){reset();feSetTool('redraw');if(innerWidth<=680)closePanels();return;}
      generation++;draft=null;acquiring=null;fe.draft=PolyDraft.createState();fe.draftPreview=null;feSyncDraftMirror();feSetTool('redraw');options=o;picking={...s,mode,down:null,move:null};
      message=mode==='room'?'點房間內空白處，或拖框限縮來源取景內的搜尋範圍；不受既有外環裁切，框選不會建立矩形。':`依兩端明確畫出${mode==='horizontal'?'水平':'垂直'}分隔；不會寫入正式面。`;
      refresh();if(innerWidth<=680)closePanels();document.getElementById('faceEditorViewport').focus();
    }catch(e){notice(e.message);}
  }
  function cancel(){reset();message='候選已取消，原面保留。';feSetTool('select');refresh();}
  const isPicking=()=>!!picking&&fe.tool==='redraw';
  function down(pt){if(!isPicking())return false;picking.down=[pt.x,pt.y];picking.move=[pt.x,pt.y];return true;}
  function move(pt){if(!isPicking())return false;if(picking.down){picking.move=[pt.x,pt.y];drawFaceEditor();}return true;}
  async function up(pt) {
    if(!isPicking()||!picking.down)return false;
    const s=picking,a=s.down,b=[pt.x,pt.y];picking=null;
    if(!current(s)){notice('來源或原面已變更，請重新選房間。');return true;}
    const p=W.active(s.bid),ia=feUlMmToImg(p,...a),ib=feUlMmToImg(p,...b);
    if(s.mode!=='room') {
      // Explicit axis lock in face-local coordinates, like manual PolyDraft.
      const end=s.mode==='horizontal'?[b[0],a[1]]:[a[0],b[1]],ie=feUlMmToImg(p,...end);
      if(Math.hypot(end[0]-a[0],end[1]-a[1])<1){notice('分隔線長度不足，請重新畫兩端。');return true;}
      barriers.push([ia,ie]);barrierStamp=s;notice('已加入人工分隔（僅供候選搜尋）；再點目標房間重取候選。');return true;
    }
    let crop=[...p.crop],seed=ia;
    if(Math.hypot(b[0]-a[0],b[1]-a[1])*fe.zoom>12) {
      const x=Math.max(p.crop[0],Math.min(ia[0],ib[0])),y=Math.max(p.crop[1],Math.min(ia[1],ib[1]));
      const right=Math.min(p.crop[0]+p.crop[2],Math.max(ia[0],ib[0])),bottom=Math.min(p.crop[1]+p.crop[3],Math.max(ia[1],ib[1]));
      crop=[x,y,right-x,bottom-y];seed=[(x+right)/2,(y+bottom)/2];
    }
    await acquire(s,seed,crop,options);return true;
  }
  function addBarriers(o) {
    const boxes=barriers.map(([a,b])=>{const w=.001;return [Math.min(a[0],b[0])-w,Math.min(a[1],b[1])-w,Math.max(a[0],b[0])+w,Math.max(a[1],b[1])+w];});
    return {...o,boxes:[...o.boxes,...boxes],warnings:[...o.warnings,...(boxes.length?['使用人工分隔，請核對門洞與相鄰房間的連通關係；分隔不代表實際牆體。']:[])]};
  }
  async function rasterObstacles(p,source,crop,o) {
    const render=await W.renderPage(source,p.page),pdf=source.meta.type==='application/pdf';
    const scale=Math.min(pdf?2:1,1800/Math.max(crop[2],crop[3])),canvas=document.createElement('canvas');
    canvas.width=Math.max(1,Math.ceil(crop[2]*scale));canvas.height=Math.max(1,Math.ceil(crop[3]*scale));
    const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(render.canvas,crop[0]*render.canvas.width/p.imgW,crop[1]*render.canvas.height/p.imgH,crop[2]*render.canvas.width/p.imgW,crop[3]*render.canvas.height/p.imgH,0,0,canvas.width,canvas.height);
    const kx=canvas.width/crop[2],ky=canvas.height/crop[3];
    const result=R.imageObstacles(ctx.getImageData(0,0,canvas.width,canvas.height),{minWidth:Math.max(1,o.minWidth*Math.min(kx,ky)),minLength:o.minLength*Math.min(kx,ky)});
    result.boxes=result.boxes.map(b=>[crop[0]+b[0]/kx,crop[1]+b[1]/ky,crop[0]+b[2]/kx,crop[1]+b[3]/ky]);
    if(scale<1)result.warnings.push('影像分析已降低解析度；小凹口與薄牆可能遺漏，請核對並局部補點。');
    return result;
  }
  async function acquire(s,seed,crop,o) {
    const ticket=++generation,p=W.active(s.bid),source=W.context().sources.get(p.sourceId);
    acquiring=s;
    message='正在本地取得房間候選…';refresh();
    try {
      let result,vectorFailure='';
      if(source.meta.type==='application/pdf'&&o.mode==='auto') {
        try {
          const doc=await W.documentFor(source),page=await doc.getPage(p.page),lib=await W.library();
          const list=await page.getOperatorList({intent:'display',annotationMode:lib.AnnotationMode.DISABLE});
          result=R.region(addBarriers(R.pdfObstacles(list,lib.OPS,page.getViewport({scale:1}),o)),seed,crop);
        }catch(e){vectorFailure=e.message;}
      }
      if(!result) {
        const obstacles=await rasterObstacles(p,source,crop,o);
        if(vectorFailure)obstacles.warnings.unshift('原始向量未取得閉合區域，改用影像輔助：'+vectorFailure);
        result=R.region(addBarriers(obstacles),seed,crop);
      }
      if(ticket!==generation||!current(s))return;
      W.assertEditable();
      const estimated=result.points.map(v=>feUlImgToMm(p,...v)),integer=R.integerProposal(estimated);
      draft={...s,schema:'room-outline-candidate/1',method:result.method,sourcePoints:result.points,estimated,deviation:integer.deviation,warnings:result.warnings,seed,crop,reviewed:false,dimensions:[],committing:false};
      fe.draft={...PolyDraft.createState(),pts:integer.points};fe.draftPreview=null;feSyncDraftMirror();
      message='候選尚未提交；請疊圖核對、修正頂點與尺寸，再確認。';refresh();
      if(innerWidth<=680)openPanel('right',document.getElementById('workspaceToggleRight'));
    }catch(e){if(ticket===generation&&sourceCurrent(s)){acquiring=null;draft=null;notice('未取得候選：'+e.message);if(innerWidth<=680)openPanel('right',document.getElementById('workspaceToggleRight'));}}
    finally {if(ticket===generation){acquiring=null;W.present();}}
  }
  function editPoints(points,dimensions=[]) {
    W.assertEditable();if(!current(draft))throw Error('候選已過期，請重新取得。');
    if(points.length<4||points.length>256||!points.every(p=>p.length===2&&p.every(n=>Number.isSafeInteger(n)&&Math.abs(n)<=1e8))||!R.orthogonal(points))throw Error('頂點須為整數 mm、至少四點且每邊正交，不能偷偷修整斜邊。');
    fe.draft={...fe.draft,pts:points.map(p=>[...p])};draft.dimensions=dimensions;draft.reviewed=false;fe.draftPreview=null;feSyncDraftMirror();refresh();
  }
  function paneHTML(bid) {
    const p=W.active(bid);if(!p)return '';
    const pdf=W.context().sources.get(p.sourceId)?.meta.type==='application/pdf',o=options||{mode:'auto',minWidth:pdf?1:2,minLength:pdf?8:24};
    const needsOutline=p.calibration&&W.reconstructionState(bid)!=='confirmed';
    let html=`<details id="refOutlineDetails" class="ref-section"${needsOutline||draft||picking||message?' open':''}><summary>房間輪廓候選與人工修正</summary><p id="refRoomStatus" role="status">${esc(message||(p.calibration?'搜尋來源取景範圍，不受既有外環裁切。選房間取得候選，核對後替換目前面的外環；也可選人工描繪。':'先校準，選房間內空白處；候選須核對室內淨輪廓。'))}</p><button id="refFit" type="button" class="btn">顯示取景範圍</button>`;
    html+=W.reconstructionStatusHTML(bid);
    html+=`<label class="ib-row">取得方式<select id="refRoomMethod"><option value="auto"${o.mode==='auto'?' selected':''}>${pdf?'PDF 原始向量優先':'本地影像輔助'}</option><option value="image"${o.mode==='image'?' selected':''}>本地影像輔助</option><option value="manual"${o.mode==='manual'?' selected':''}>人工逐點描繪</option></select></label><div class="place-form"><label>線寬至少（${pdf?'頁面單位':'原圖 px'}）<input id="refRoomMinWidth" type="number" min="0.01" step="any" value="${o.minWidth}"></label><label>最短線（${pdf?'頁面單位':'原圖 px'}）<input id="refRoomMinLength" type="number" min="1" step="any" value="${o.minLength}"></label></div><button id="refRoomPick" class="btn" type="button"${p.calibration?'':' disabled'}>在圖上選房間／框選重取</button>`;
    html+=`<details class="ref-section"><summary>缺口與連通房間：明確分隔後重取</summary><div class="ref-actions"><button id="refRoomHorizontal" class="btn" type="button">畫水平分隔</button><button id="refRoomVertical" class="btn" type="button">畫垂直分隔</button><button id="refRoomClearBarriers" class="btn" type="button">清除分隔（${barriers.length}）</button></div></details>`;
    if(pending(bid)) {
      const pts=fe.draft.pts;
      html+=`<section id="refRoomCandidate"><strong>待核對候選 · ${draft.method==='pdf-vector'?'PDF 原始向量內緣推估':'影像暗線內緣推估'}</strong><p>確認將替換目前面 #${bid} 的外環；取消保留原面，確認後可復原。轉成整數 mm 最大座標偏差 ${draft.deviation.toFixed(4)} mm。圖上標註尺寸不會自動入值。</p><ul>${draft.warnings.map(w=>`<li>${esc(w)}</li>`).join('')}</ul><ol data-room-dimensions>${pts.map((a,i)=>{const b=pts[(i+1)%pts.length];return `<li>邊 ${i+1}：擬提交 ${Math.abs(b[0]-a[0])+Math.abs(b[1]-a[1])} mm${draft.dimensions.some(d=>d.edge===i)?'（人工核對入值）':''}</li>`;}).join('')}</ol><div class="place-form"><label>核對邊<select id="refRoomEdge">${pts.map((_,i)=>`<option value="${i}">邊 ${i+1}</option>`).join('')}</select></label><label>圖上標註／核對尺寸（mm）<input id="refRoomLength" type="number" min="1" step="1"></label></div><button id="refRoomSetLength" class="btn" type="button">將核對尺寸寫入候選</button><details class="ref-section"><summary>局部補點／凹口與頂點修正</summary><label>沿外環順序輸入 u,v（mm）；可插入凹口與補邊<textarea id="refRoomVertices" rows="6" spellcheck="false">${esc(pts.map(p=>p.join(',')).join('\n'))}</textarea></label><button id="refRoomApplyVertices" class="btn" type="button">更新候選頂點</button></details><label class="ib-row"><input id="refRoomReviewed" type="checkbox"${draft.reviewed?' checked':''}> 已逐邊核對室內淨範圍、連通關係、尺寸及上述修整／警告</label><div class="ref-actions"><button id="refRoomConfirm" class="btn primary" type="button"${draft.reviewed?'':' disabled'}>確認替換外環，交核心驗證</button><button id="refRoomCancel" class="btn" type="button">取消候選</button></div></section>`;
    } else if(picking||acquiring)html+=`<button id="refRoomCancel" class="btn" type="button">${acquiring?'取消辨識':'取消取點'}</button>`;
    return html+'</details>';
  }
  function bindPane(pane,bid) {
    const safe=fn=>async()=>{try{await fn();}catch(e){notice(e.message);}};
    pane.querySelector('#refRoomPick')?.addEventListener('click',()=>start(bid,pane));
    pane.querySelector('#refRoomHorizontal')?.addEventListener('click',()=>start(bid,pane,'horizontal'));
    pane.querySelector('#refRoomVertical')?.addEventListener('click',()=>start(bid,pane,'vertical'));
    pane.querySelector('#refRoomClearBarriers')?.addEventListener('click',safe(()=>{W.assertEditable();barriers=[];barrierStamp=null;refresh();}));
    pane.querySelector('#refRoomCancel')?.addEventListener('click',cancel);
    pane.querySelector('#refRoomApplyVertices')?.addEventListener('click',safe(()=>editPoints(pane.querySelector('#refRoomVertices').value.trim().split(/\n/).map(line=>line.trim().split(',').map(Number)))));
    pane.querySelector('#refRoomSetLength')?.addEventListener('click',safe(()=>{
      const edge=Number(pane.querySelector('#refRoomEdge').value),length=Number(pane.querySelector('#refRoomLength').value);
      const points=R.resizeEdge(fe.draft.pts,edge,length);editPoints(points,[{edge,length,kind:'user-confirmed-mm'}]);
    }));
    pane.querySelector('#refRoomReviewed')?.addEventListener('change',safe(()=>{W.assertEditable();if(!current(draft))throw Error('候選已過期。');draft.reviewed=pane.querySelector('#refRoomReviewed').checked;pane.querySelector('#refRoomConfirm').disabled=!draft.reviewed;document.getElementById('faceDraftFinish').disabled=!draft.reviewed;}));
    pane.querySelector('#refRoomConfirm')?.addEventListener('click',safe(()=>feDraftTryClose()));
  }
  function beforeCommit() {
    if(!draft)return null;
    W.assertEditable();if(!current(draft)||!draft.reviewed)throw Error('請重新核對室內淨輪廓、尺寸與警告，再確認候選。');
    if(!R.orthogonal(fe.draft.pts)||!fe.draft.pts.every(p=>p.every(Number.isSafeInteger)))throw Error('候選須為正交整數 mm。');
    draft.committing=true;return draft;
  }
  function afterCommit(s,ok) {
    if(!s)return;
    s.committing=false;
    if(!ok){s.reviewed=false;message='確認已取消或核心拒絕；原面保留，候選仍可修正。';refresh();return;}
    if(sourceCurrent(s))W.markReconstructionReviewed(s.bid,{method:s.method,warnings:s.warnings,local:false,expectedBasis:s.basis});
    reset(false);message='已確認來源輪廓，可復原／重做及保存專案。';refresh();
  }
  function draw(root) {
    if(pending(oc.edit?.bid)&&!draft.committing) {
      const g=document.getElementById('feDraftLayer');
      if(g)el('polygon',{id:'roomCandidateOverlay',points:fe.draft.pts.map(p=>p.join(',')).join(' '),fill:'rgba(22,150,130,.16)',stroke:'var(--accent)','stroke-width':2/fe.zoom,'stroke-dasharray':`${8/fe.zoom} ${4/fe.zoom}`,'pointer-events':'none'},g);
    }
    const p=oc.edit&&W.active(oc.edit.bid);
    if(p&&barriers.length)for(const [a,b] of barriers){const x=feUlImgToMm(p,...a),y=feUlImgToMm(p,...b);el('line',{x1:x[0],y1:x[1],x2:y[0],y2:y[1],stroke:'#d78532','stroke-width':3/fe.zoom,'stroke-dasharray':`${6/fe.zoom} ${3/fe.zoom}`,'pointer-events':'none'},root);}
    if(isPicking()&&picking.down&&picking.move) {
      const a=picking.down,b=picking.move;
      if(picking.mode==='room')el('rect',{x:Math.min(a[0],b[0]),y:Math.min(a[1],b[1]),width:Math.abs(a[0]-b[0]),height:Math.abs(a[1]-b[1]),fill:'rgba(22,150,130,.1)',stroke:'#169682','stroke-width':2/fe.zoom,'pointer-events':'none'},root);
      else el('line',{x1:a[0],y1:a[1],x2:picking.mode==='horizontal'?b[0]:a[0],y2:picking.mode==='horizontal'?a[1]:b[1],stroke:'#d78532','stroke-width':3/fe.zoom,'pointer-events':'none'},root);
    }
  }
  return {pending,isPicking,start,down,move,up,paneHTML,bindPane,beforeCommit,afterCommit,draw,cancel,reset,invalidate,calibrated,
    get hasWork(){return !!(draft||picking||acquiring);},
    snapshot:()=>draft?structuredClone({...draft,points:fe.draft.pts}):null};
})();
window.RoomOutlineWorkspace=RoomOutlineWorkspace;
