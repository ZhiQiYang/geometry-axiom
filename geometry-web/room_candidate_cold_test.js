/* R358: actual candidate-first acceptance, immediate formal Save, independent
 * Chrome profile/native service Open, and source-session atomic undo/redo.
 * Native commands/image bytes below arrange the isolated fixture only. Candidate
 * selection/review/accept/Save/Open/history actions use real CDP input. No product
 * function or successful response is replaced. Original P90 remains a separate 8.
 */
'use strict';
const fs=require('node:fs');
const H=require('./cdp_helpers.js'),C=require('./cdp_room_candidate_contract.js');
const {createArchiveHarness}=require('./cdp_room_candidate_io.js');
const Project=require('./project-store.js'),zip=require('./vendor/fflate/umd/index.js');

const snapshotExpression=`(async()=>{
 const r=await apiRequest('dump');if(!r.ok)throw Error(r.error||'dump failed');
 const rooms=ReferenceWorkspace.readFeatureAttachment('source-rooms'),draft=ReferenceWorkspace.readFeatureAttachment('room-candidates');
 const ids=[...new Set([1,...(rooms?.rooms||[]).map(row=>row.boundaryRef.id)])].sort((a,b)=>a-b),native=[];
 for(const id of ids){const n=await apiRequest('boundary '+id);if(!n.ok)throw Error(n.error||'boundary read failed');native.push({id:n.id,kind:n.kind,geometryFingerprint:n.geometryFingerprint,loops:n.loops});}
 const page=ReferenceWorkspace.active(1),hostPage=page?{id:page.id,sourceId:page.sourceId,page:page.page,imgW:page.imgW,imgH:page.imgH,
  mmPerPx:page.mmPerPx,x:page.x,y:page.y,rot:page.rot,calibration:page.calibration,crop:page.crop,opacity:page.opacity,locked:page.locked,records:page.records}:null;
 return {projectId:ReferenceWorkspace.context().id,scene:r.text,rooms,draft,native,hostPage,
  sourceIds:[...ReferenceWorkspace.context().sources.keys()].sort(),session:RoomCollectionWorkspace.candidateSnapshot(),
  undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,group:!!ReferenceWorkspace.history.group};
})()`;

module.exports=async function roomCandidateCold({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount,browserProfile}){
 const read=H.makeRead(eval_),key=H.makeKey({send,sleep}),initialExceptions=exceptionCount();
 const check=H.makeCheck({prefix:C.SECTION+' ',throwOnFail:true});
 const ctl=H.makeCtl({eval_,sleep,click:async(x,y)=>{await click(x,y);await sleep(40);}},{attempts:8,pollMs:30,settleMs:60,hitElement:true});
 const wait=async expression=>{await waitForUI(expression,20000);if(await read(expression)!==true)throw Error('R358 wait '+expression);};
 const capture=()=>read(snapshotExpression);
 const settle=()=>wait(`connection.phase==='ready'&&!oc.busy&&!ReferenceWorkspace.busy&&!ReferenceWorkspace.history.group`);
 async function fill(selector,value){await ctl(selector);await key('a','KeyA',65,2);await send('Input.insertText',{text:String(value)});await key('Tab','Tab',9);await sleep(60);}
 async function choose(selector,value){
  const index=await read(`[...document.querySelector(${JSON.stringify(selector)}).options].findIndex(o=>o.value===${JSON.stringify(value)})`);
  if(index<0)throw Error('R358 missing option '+selector+'='+value);
  await ctl(selector);await key('Home','Home',36);for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);await key('Tab','Tab',9);
  await wait(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(value)}`);
 }
 async function sourcePoint(x,y){
  const point=await read(`(()=>{const p=feUlImgToMm(ReferenceWorkspace.active(1),${x},${y}),r=$('faceEditorSvg').getBoundingClientRect();return {x:r.left+fe.panX+p[0]*fe.zoom,y:r.top+fe.panY+p[1]*fe.zoom};})()`);
  await click(point.x,point.y);await sleep(60);
 }
 async function setup(){
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  const warning=await read(`ReferenceWorkspace.context().dirty?'目前尚未保存的變更不會自動寫入檔案。':''`);
  await ctl('#fileMenuBtn');
  await expectNativeDialog(()=>ctl('#btnNewProject'),{type:'confirm',accept:true,
   message:'建立一份空白新專案，切換為新的專案識別及「未命名專案」。'+warning+'本次切換可一步復原；僅保存在本頁的形狀特徵參數不會恢復。確定繼續嗎？'});
  await wait(`!ReferenceWorkspace.busy&&oc.faces.length===0`);
  await read(`(async()=>{const r=await api('line boundary 1 outline 0,0 3200,0 3200,2000 0,2000');if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();await enterFocus('face',1);fiShowTab('underlay');})()`);
  await read(`(async()=>{const pixels=(${C.fixturePixels.toString()})();const canvas=document.createElement('canvas');canvas.width=pixels.width;canvas.height=pixels.height;
   const ctx=canvas.getContext('2d'),image=ctx.createImageData(pixels.width,pixels.height);image.data.set(pixels.data);ctx.putImageData(image,0,0);
   const blob=await new Promise(resolve=>canvas.toBlob(resolve));if(!blob)throw Error('R358 image fixture failed');
   const source=await ReferenceWorkspace.sourceFromFile(new File([blob],'r358-two-room.png',{type:'image/png'}));await ReferenceWorkspace.openSource(source,1);})()`);
  await ctl('#refApply');await wait(`!$('referenceDialog').open&&!!ReferenceWorkspace.active(1)`);
  await ctl('#ulCalibStart');await sourcePoint(30,30);await sourcePoint(290,30);await fill('#ulCalibDist',2600);await ctl('#ulCalibApply');
  await wait(`Math.abs(ReferenceWorkspace.active(1).mmPerPx-10)<.001&&!fe.ulCalib`);
  await read(`(()=>{const p=ReferenceWorkspace.active(1);p.x=0;p.y=0;ReferenceWorkspace.changed(1);feFit(loopsBBox(oc.bmap[1]));renderFaceInspector();})()`);
  await choose('#roomNewMethod','candidates');await ctl('#roomNew');
  await wait(`RoomCollectionWorkspace.candidateSnapshot()?.candidates.length===2&&!RoomOutlineWorkspace.hasWork`);
 }
 console.log('=== '+C.SECTION+'. 候選首房接受、立即保存與獨立冷開 ===');
 let io,cold,coldErrors=[];
 try{
  await setup();
  const analyzed=await capture();
  check('TWO_CANDIDATES 真影像分析取得兩列待核對且仍是零房',analyzed.rooms===null&&analyzed.draft===null&&analyzed.native.length===1&&
   analyzed.session.candidates.length===2&&analyzed.session.candidates.every(row=>row.status==='pending'&&!row.reviewed&&row.method==='image-lines')&&
   JSON.stringify(analyzed.session.candidates.map(row=>row.sourcePoints))===JSON.stringify(C.EXPECTED_SOURCE_LOOPS)&&
   JSON.stringify(analyzed.session.candidates.map(row=>row.points))===JSON.stringify(C.EXPECTED_SOURCE_LOOPS.map(loop=>loop.map(point=>point.map(value=>value*10)))));
  io=await createArchiveHarness({send,read,ctl});
  // Establish the original persisted pending draft before acceptance. There is
  // no Park or explicit flush anywhere in this scenario; Save owns its sync.
  const initialFile=await io.save();
  check('BASELINE_FILE 原始待核對草稿由正式 Save 下載',initialFile.completed===true&&initialFile.size>0&&fs.existsSync(initialFile.file),initialFile);
  const before=await capture(),initialProject=await Project.unpack(initialFile.bytes,zip);
  check('PENDING_BASELINE 保存原稿是圖頁錨點與精確兩列 pending',before.rooms===null&&before.draft?.anchor.kind==='page'&&
   before.draft.rows.length===2&&before.draft.rows.every(row=>row.status==='pending'&&!Object.hasOwn(row,'roomId'))&&
   initialProject.manifest.featureAttachments.records.find(row=>row.kind==='room-candidates').value.anchor.kind==='page');
  await ctl('[data-room-candidate="0"]');await wait(`!!$('refRoomReviewed')&&!$('refRoomReviewed').checked`);
  await ctl('#refRoomReviewed');
  await expectNativeDialog(()=>ctl('#refRoomConfirm'),{type:'prompt',message:'新房間名稱',accept:true,promptText:'候選第一間'});
  await wait(`!!$('roomConfirm')`);await ctl('#roomConfirm');
  await wait(`!RoomCollectionWorkspace.hasWork&&!RoomOutlineWorkspace.hasWork&&!RoomCollectionWorkspace.candidateSnapshot()?.committing`);
  const accepted=await capture();
  check('GROUPED_ACCEPTANCE Save 前已同群組持久化新錨點與 accepted/pending',C.acceptedSnapshot(before,accepted));
  // The next UI action after Accept is Save. Read-only receipts above ensure
  // Save cannot silently repair an old persisted anchor and give a false pass.
  const saved=await io.save();
  check('IMMEDIATE_SAVE_FILE 接受後立即正式 Save 產生真下載檔',saved.completed===true&&saved.size>0&&fs.existsSync(saved.file),saved);
  const afterSave=await capture();
  check('SAVE_NO_REPAIR 保存沒有補寫錨點、修補列或新增歷史',JSON.stringify(C.savedState(afterSave))===JSON.stringify(C.savedState(accepted))&&afterSave.undo===accepted.undo);
  const loaded=await Project.unpack(saved.bytes,zip);
  check('ARCHIVE_EXACT ZIP 精確保存原生場景、兩列與接受後錨點',C.archiveMatches(loaded,accepted));
  check('ONE_ACCEPTANCE_STEP 首房 D3、共享來源與草稿只有一筆歷史',accepted.undo===before.undo+1&&accepted.redo===0&&accepted.group===false);
  cold=await io.cold();
  check('COLD_OWNERSHIP 冷開使用獨立 Chrome profile 與獨立原生服務',C.coldOwnership(cold.info,browserProfile));
  await cold.open(saved.file);
  await cold.wait(`!ReferenceWorkspace.busy&&!oc.busy&&ReferenceWorkspace.getProjectState().id===${JSON.stringify(accepted.projectId)}&&ReferenceWorkspace.readFeatureAttachment('source-rooms')?.rooms.length===1`);
  const boundaryId=accepted.rooms.rooms[0].boundaryRef.id;
  await cold.read(`(async()=>{await renderObjects();await enterFocus('face',${boundaryId});fiShowTab('underlay');})()`);
  await cold.wait(`(()=>{const s=RoomCollectionWorkspace.candidateSnapshot();return !!s&&s.stale===false&&!s.nativePending&&!s.expired;})()`);
  const reopened=await cold.read(snapshotExpression);
  check('COLD_ARCHIVE_EXACT 冷開場景、來源、房間與候選原值全等',JSON.stringify(C.savedState(reopened))===JSON.stringify(C.savedState(accepted)));
  check('COLD_ANCHOR_FRESH 冷服務現行原生指紋吻合保存錨點',JSON.stringify(reopened.draft.anchor)===JSON.stringify(C.expectedAnchor(reopened.rooms,reopened.native))&&
   reopened.session.stale===false&&!reopened.session.nativePending&&!reopened.session.expired&&
   reopened.session.candidates[0].status==='accepted'&&reopened.session.candidates[1].status==='pending');
  await cold.wait(`(()=>{const s=RoomCollectionWorkspace.candidateSnapshot();return !!s&&s.stale===false&&!s.nativePending&&!s.expired;})()`);
  await cold.ctl('[data-room-candidate="1"]');
  await cold.wait(`!!$('refRoomReviewed')&&!!RoomOutlineWorkspace.snapshot()`);
  const selected=await cold.read(`({row:RoomCollectionWorkspace.candidateSnapshot().active,candidate:RoomOutlineWorkspace.snapshot(),checked:$('refRoomReviewed').checked,disabled:$('refRoomConfirm').disabled})`);
  check('SECOND_RESELECT 第二列只能重新選取核對且未繼承已核對',selected.row===1&&selected.candidate.candidateId===reopened.draft.rows[1].rowKey&&selected.candidate.reviewed===false&&selected.checked===false&&selected.disabled===true);
  await cold.ctl('#refRoomReviewed');
  const reviewed=await cold.read(`(async()=>({checked:$('refRoomReviewed').checked,disabled:$('refRoomConfirm').disabled,scene:(await apiRequest('dump')).text,rooms:ReferenceWorkspace.readFeatureAttachment('source-rooms')}))()`);
  check('SECOND_REVIEW 第二列實際重新勾選可確認而未新增 D3',reviewed.checked===true&&reviewed.disabled===false&&reviewed.scene===accepted.scene&&JSON.stringify(reviewed.rooms)===JSON.stringify(accepted.rooms));
  coldErrors=[...cold.errors];await cold.close();cold=null;
  // Runtime history is not serialized in .gcanvas. Test the first acceptance's
  // undo/redo in its owning source session, never the cold session's Open entry.
  await ctl('#faceUndoButton');await settle();const undone=await capture();
  check('UNDO_ATOMIC 一次復原同時移除首房與新來源並恢復原草稿',JSON.stringify(C.savedState(undone))===JSON.stringify(C.savedState(before))&&undone.undo===before.undo&&undone.redo===1);
  await ctl('#faceRedoButton');await settle();const redone=await capture();
  check('REDO_ATOMIC 一次重做同時恢復 D3、來源與接受後草稿',JSON.stringify(C.savedState(redone))===JSON.stringify(C.savedState(accepted))&&redone.undo===accepted.undo&&redone.redo===0);
  check('NO_EXCEPTIONS 原分頁與冷開分頁皆無新增未捕捉例外',exceptionCount()===initialExceptions&&coldErrors.length===0,coldErrors);
  fs.writeFileSync(require('node:path').join(io.directory,'r358-receipts.json'),JSON.stringify({before,accepted,afterSave,reopened,undone,redone,sourceProfile:browserProfile,coldErrors},null,2)+'\n');
 }finally{if(cold)await cold.close();if(io)await io.close();}
};
module.exports.snapshotExpression=snapshotExpression;
