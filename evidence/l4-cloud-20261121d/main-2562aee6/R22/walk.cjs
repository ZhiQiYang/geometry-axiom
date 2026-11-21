// Node 24. Attach to the operator's prepared Chromium; never launch a browser.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');
const assert = require('node:assert/strict');
const {chromium} = require('playwright-core');
const kind=process.argv[2];
assert.ok(['pdf','png'].includes(kind),'node walk.cjs pdf|png');
const main='2562aee65c9f21a9ffdfd684100102d764bc2eb4';
const app=process.env.R22_URL || 'http://127.0.0.1:18851';
const cdp=process.env.R22_CDP;
assert.ok(cdp&&process.env.R22_BROWSER_PID,'Set R22_CDP and R22_BROWSER_PID to the prepared browser');
const repo=execFileSync('git',['rev-parse','--show-toplevel'],{encoding:'utf8'}).trim();
const input=kind==='pdf'?path.join(repo,'geometry-web/docs/fixtures/issue54-public-rooms.pdf'):path.join(__dirname,'connected.png');
const output=process.env.R22_OUTPUT || path.join(__dirname,kind);
fs.mkdirSync(output,{recursive:true});
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const r={scope:kind,main,app,node:process.version,started:new Date().toISOString(),input:{name:path.basename(input),sha256:hash(input)},steps:[],assertions:[]};
let p,ctx;
const pause=ms=>new Promise(done=>setTimeout(done,ms));
function check(label,ok,actual){r.assertions.push({label,pass:!!ok,actual}); assert.ok(ok,label);}
async function snapshot(){
  return p.evaluate(()=>{
    const bid=typeof oc==='undefined'?1:(oc.focus?.t==='face'?oc.focus.id:1);
    const el=id=>document.getElementById(id), c=window.RoomOutlineWorkspace?.snapshot(), ref=typeof ReferenceWorkspace==='undefined'?null:ReferenceWorkspace.active(bid);
    return {
      faceId:bid, outline:typeof oc!=='undefined'?oc.bmap?.[bid]?.[0]?.verts:null,
      source:ref?{sourceId:ref.sourceId,page:ref.page,crop:ref.crop,mmPerPx:ref.mmPerPx,calibration:ref.calibration}:null,
      candidate:c?{method:c.method,sourcePoints:c.sourcePoints,points:c.points,crop:c.crop,warnings:c.warnings,dimensions:c.dimensions,reviewed:c.reviewed}:null,
      status:el('refRoomStatus')?.innerText, reviewState:ref?ReferenceWorkspace.reconstructionState(bid):null,
      visibleCandidate:el('refRoomCandidate')?.innerText, confirmDisabled:el('refRoomConfirm')?.disabled,
      impact:document.querySelector('dialog.reference-impact[open]')?.innerText,
    };
  });
}
async function step(id,action,op){
  if(op)await op();
  await pause(180);
  const file=String(r.steps.length+1).padStart(2,'0')+'-'+id+'.jpg';
  await p.screenshot({path:path.join(output,file),type:'jpeg',quality:78});
  const state=await snapshot();
  r.steps.push({action,file,sha256:hash(path.join(output,file)),state});
  console.log(id,state.status||'');
  return state;
}
async function click(id,selector){
  const loc=typeof selector==='string'?p.locator(selector):selector;
  if(typeof selector==='string')await openParents(selector);
  return step(id,typeof selector==='string'?selector:id,()=>loc.click());
}
async function openParents(selector){
  for(let i=0;i<4;i++){
    const ancestors=p.locator('details:not([open])').filter({has:p.locator(selector)});
    if(!(await ancestors.count()))break;
    await ancestors.first().locator(':scope > summary').click();
  }
}
async function write(selector,value){
  await openParents(selector); await p.locator(selector).click(); await p.keyboard.press('Control+a');
  await p.keyboard.insertText(String(value));
}
async function xy(x,y){
  return p.evaluate(([x,y])=>{
    const [u,v]=feUlImgToMm(ReferenceWorkspace.active(oc.focus.id),x,y);
    const pos=new DOMPoint(u,v).matrixTransform(document.getElementById('faceEditorRoot').getScreenCTM());
    if(!document.getElementById('faceEditorSvg').contains(document.elementFromPoint(pos.x,pos.y)))throw Error('來源位置未在可點畫布上');
    return [pos.x,pos.y];
  },[x,y]);
}
async function srcClick(x,y){await p.mouse.click(...await xy(x,y));}
async function srcDrag(a,b){
  const from=await xy(...a),to=await xy(...b);
  await p.mouse.move(...from);await p.mouse.down();await p.mouse.move(...to,{steps:15});await p.mouse.up();
}
async function waitCandidate(){await p.locator('#refRoomCandidate').waitFor({timeout:12000});}
async function waitSettled(state){await p.waitForFunction(s=>!oc.busy&&ReferenceWorkspace.reconstructionState(oc.focus.id)===s,state);}
async function lessons(){for(let i=0;i<4;i++){
  const btn=p.getByRole('button',{name:'知道了',exact:true}).first();if(!await btn.isVisible())return;
  await click('dismiss-tip',btn);
}}
async function pickDiskFile(){
  // Ordinary native file dialog opened by the visible import button.
  // The helper may only send keyboard input to the verified browser-owned file dialog.
  const helper=process.env.R22_PICKER || path.join(__dirname,'tools','native_picker.py');
  await p.locator('#refImport').click();
  execFileSync('python',[helper,'choose',process.env.R22_BROWSER_PID,input],{stdio:'inherit',timeout:20000});
  await p.locator('#referenceDialog[open] #refApply:enabled').waitFor();
}
function same(a,b){return JSON.stringify(a)===JSON.stringify(b);}
function contains(poly,[x,y]){
  let inside=false;
  for(let i=0,j=poly.length-1;i<poly.length;j=i++){
    let [a,b]=poly[i],[c,d]=poly[j];
    if((b>y)!==(d>y)&&x<(c-a)*(y-b)/(d-b)+a)inside=!inside;
  }
  return inside;
}
async function setup(){
  await p.goto(app);await p.locator('#fileMenuBtn').waitFor(); await lessons();
  await click('file','#fileMenuBtn');
  await click('examples','#exampleMenuBtn');
  await click('load-example','#btnEx');
  await p.locator('.ocard[data-kind="boundary"][data-id="1"]').waitFor();
  await p.waitForFunction(()=>JSON.stringify(oc.bmap?.[1]?.[0]?.verts)===JSON.stringify([[0,0],[4000,0],[4000,3000],[0,3000]]));
  const initial=await snapshot();check('獨立頁籤以範例原外環起步，無先前底圖或候選',!initial.source&&!initial.candidate,initial);
  const card='.ocard[data-kind="boundary"][data-id="1"]';
  await click('face-card',card); await click('enter-face',card+' .card-enter');await lessons();
  await click('underlay','[data-fi-tab="underlay"]');
  await openParents('#refImport');
  await step('import','按「匯入 PDF／圖片」，於檔案選擇器以鍵盤選取磁碟原件',pickDiskFile);
  if(kind==='png'&&!process.env.R22_USE_EXISTING_FACE){
    await step('new-tracing-face','目標選「建立描繪用面」',async()=>{await p.locator('#refTarget').click();await p.keyboard.press('Home');await p.keyboard.press('Enter');});
    check('PNG 選取獨立新描繪面',await p.locator('#refTarget').inputValue()==='new',await p.locator('#refTarget').inputValue());
  }
  await click('attach','#refApply');
  await p.waitForFunction(()=>oc.focus?.t==='face'&&!!ReferenceWorkspace.active(oc.focus.id));
  if(!(await p.locator('#refRoomPick').count()))await click('new-face-underlay','[data-fi-tab="underlay"]');
  const base=await step('attached','核對參考頁與目前面');
  check('校準前不能選房間',await p.locator('#refRoomPick').isDisabled(),base.source);
  await click('calibrate-start','#ulCalibStart');
  await step('calibrate-a','校準點 A (30,30)',()=>srcClick(30,30));
  await step('calibrate-b','校準點 B (230,30)',()=>srcClick(230,30));
  await step('calibrate-length','輸入已知距離 2000 mm',()=>write('#ulCalibDist',2000));
  await click('calibrate-apply','#ulCalibApply');
  await click('fit','#refFit');
  const s=await snapshot();
  check('200 頁面單位約為 2000 mm',Math.abs(s.source.mmPerPx-10)<.08,s.source.mmPerPx);
  return s.outline;
}
async function select(target='click'){
  await click('choose-room','#refRoomPick');
  return step(target==='box'?'box-candidate':'pick-candidate',target==='box'?'從 (20,20) 拖到 (250,165)':'點房間內 (70,70)',async()=>{
    if(target==='box')await srcDrag([20,20],[250,165]);else await srcClick(70,70);await waitCandidate();
  });
}
async function commit(original,candidate,expectConflict=false){
  await click('review','#refRoomReviewed');
  await click('confirm','#refRoomConfirm');
  const impact=p.locator('dialog.reference-impact[open]');
  await p.waitForFunction(()=>!!document.querySelector('dialog.reference-impact[open]')||ReferenceWorkspace.reconstructionState(oc.focus.id)==='confirmed');
  if(await impact.isVisible()){
    const before=await step('impact','核對連動變更');
    check('連動確認前外環維持原狀',same(original,before.outline),before.outline);
    if(expectConflict){
      check('現有角材端點失去擋面時核心拒絕變更',await p.locator('#impact-confirm').isDisabled()&&before.impact.includes('V_CUT_PRIORITY'),before.impact);
      await click('return-to-edit',impact.getByRole('button',{name:'返回修改',exact:true}));
      return;
    }
    await click('apply-impact',impact.getByRole('button',{name:'確認套用',exact:true}));
  }
  await waitSettled('confirmed');
  const s=await step('confirmed','確認正式外環與核對狀態');
  check('正式外環逐頂點等於候選',same(s.outline,candidate),s.outline);
  await click('undo','#faceUndoButton');await p.waitForFunction(a=>JSON.stringify(oc.bmap[oc.focus.id][0].verts)===JSON.stringify(a),original);
  const back=await step('undo-result','復原後核對原外環');
  check('復原還原原外環',same(back.outline,original),back.outline);
  await click('redo','#faceRedoButton');await waitSettled('confirmed');
  const again=await step('redo-result','重做後核對正式外環');
  check('重做恢復候選',same(again.outline,candidate),again.outline);
}
async function pdfWalk(original){
  const picked=await select();check('PDF 點取使用向量',picked.candidate.method==='pdf-vector',picked.candidate);
  const box=await select('box');
  check('框選限縮範圍但取得真實四邊內緣',box.candidate.crop[2]<box.source.crop[2]&&same(box.candidate.points,picked.candidate.points)&&same(box.candidate.sourcePoints,[[32,32],[228,32],[228,148],[32,148]]),box.candidate);
  check('框選尚未寫入',same(box.outline,original),box.outline);
  await commit(original,box.candidate.points);
  await click('return-to-original','#faceUndoButton');
  await p.waitForFunction(a=>JSON.stringify(oc.bmap[1][0].verts)===JSON.stringify(a),original);
  const fresh=await select('box');
  check('重新取得可編輯的同一內緣',same(fresh.candidate.points,box.candidate.points),fresh.candidate.points);
  await click('review-before-edit','#refRoomReviewed');
  const points=box.candidate.points;
  const [[x,y],[right],[,bottom]]=points;
  const newPts=[[x,y],[right,y],[right,bottom],[right-320,bottom],[right-320,bottom-180],[right-740,bottom-180],[right-740,bottom],[x,bottom]];
  await openParents('#refRoomVertices');
  await step('edit-vertices','在「局部補點／凹口與頂點修正」輸入 8 點',()=>write('#refRoomVertices',newPts.map(a=>a.join(',')).join('\n')));
  const corrected=await click('update-vertices','#refRoomApplyVertices');
  check('套用凹口清除舊核對且未改動正式面',same(corrected.candidate.points,newPts)&&corrected.confirmDisabled&&same(original,corrected.outline),corrected);
  await step('edit-edge','第一邊實際輸入 '+(right-x+40)+' mm，按 Enter',async()=>{await write('#refRoomEdgeLength0',right-x+40);await p.keyboard.press('Enter');});
  const edited=await snapshot();
  check('人工尺寸記錄與八點凹口均保留',edited.candidate.points.length===8&&edited.candidate.dimensions.some(d=>d.edge===0&&d.length===right-x+40)&&same(edited.outline,original),edited.candidate);
  await commit(original,edited.candidate.points,true);
  const legal=[[x,y],[right+40,y],[right+40,bottom],[x+120,bottom],[x+120,bottom-180],[x+70,bottom-180],[x+70,bottom],[x,bottom]];
  await step('move-notch','將凹口移至左側以保留既有角材擋面',()=>write('#refRoomVertices',legal.map(a=>a.join(',')).join('\n')));
  const adjusted=await click('apply-revised-notch','#refRoomApplyVertices');
  check('修正後的候選含八個指定頂點',same(adjusted.candidate.points,legal),adjusted.candidate.points);
  await step('confirm-edge-length','逐邊欄輸入第一邊 '+(right-x+40)+' mm 再按 Enter',async()=>{await write('#refRoomEdgeLength0',right-x+40);await p.keyboard.press('Enter');});
  await commit(original,legal);
}
async function pngWalk(original){
  const before=await select();
  check('PNG 暗線初取包含相鄰兩房',before.candidate.method==='image-lines'&&contains(before.candidate.sourcePoints,[70,70])&&contains(before.candidate.sourcePoints,[250,100]),before.candidate);
  await click('vertical','#refRoomVertical');
  const separated=await step('barrier','從 (230,70) 拖至 (230,150)，畫出門洞分隔',()=>srcDrag([230,70],[230,150]));
  check('分隔只影響搜尋',same(separated.outline,original)&&separated.status.includes('人工分隔'),separated.status);
  const after=await select();
  check('分隔後只取主房且提醒人工核對',contains(after.candidate.sourcePoints,[70,70])&&!contains(after.candidate.sourcePoints,[250,100])&&after.candidate.warnings.some(t=>t.includes('人工分隔'))&&same(after.outline,original),after.candidate);
  await commit(original,after.candidate.points);
}
(async()=>{
  const b=await chromium.connectOverCDP(cdp);r.chromium=b.version();
  ctx=await b.newContext({viewport:{width:1400,height:900}});p=await ctx.newPage();p.setDefaultTimeout(12000);
  const session=await ctx.newCDPSession(p);
  await session.send('Page.setInterceptFileChooserDialog',{enabled:false});
  try{const original=await setup();if(kind==='pdf')await pdfWalk(original);else await pngWalk(original);r.result='pass';}
  catch(e){r.result='failed-or-blocked';r.error=e.message;console.error(e);await step('last-screen','停在此畫面').catch(console.error);process.exitCode=1;}
  finally{r.finished=new Date().toISOString();fs.writeFileSync(path.join(output,'result.json'),JSON.stringify(r,null,2)+'\n');await ctx.close();}
})().then(()=>process.exit(process.exitCode||0),e=>{console.error(e);process.exit(1);});
