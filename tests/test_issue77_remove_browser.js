/* Real UI regression for shared-source removal with retained legacy evidence. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {chromium}=require('playwright');
const url=process.env.GEOMETRY_TEST_URL;
if(!url || !process.env.GEOMETRY_FEEDBACK_DIR?.startsWith(os.tmpdir()+path.sep))throw new Error('Explicit isolated URL and TEMP feedback directory required.');
const fixture=fs.readFileSync(path.join(__dirname,'fixtures/issue77-two-rooms.pdf'));
const ownerAdapter=process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER?fs.readFileSync(process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER,'utf8'):null;
const evidence=process.env.GEOMETRY_ISSUE77_REMOVE_SCREENSHOTS||path.join(os.tmpdir(),'issue77-remove-evidence');
fs.mkdirSync(evidence,{recursive:true});
const changedPDF=label=>Buffer.from(fixture.toString('ascii').replace('Room A',label),'ascii'); // Equal-length labels retain exact xref offsets.
let checks=0;
const check=(actual,expected,label)=>{assert.deepEqual(actual,expected,label);checks++;console.log('PASS '+label);};
async function snapshot(page){return page.evaluate(async()=>({
  scene:(await api('dump')).text,attachment:RoomCollectionWorkspace.controller.state(),
  sources:[...ReferenceWorkspace.context().sources.keys()].sort(),
  pages:ReferenceWorkspace.group(1)?.pages.map(({src,...page})=>page)||[]
}));}
async function main(){
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
  page.on('pageerror',error=>errors.push(error.message));page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
  page.on('dialog',dialog=>dialog.accept('房間 A'));
  try{
    await page.goto(url);await page.waitForFunction(()=>typeof RoomCollectionWorkspace!=='undefined'&&connection.phase==='ready');
    if(ownerAdapter)await page.evaluate(ownerAdapter);
    const retained=await page.evaluate(async encoded=>{
      for(const command of ['line reset','line boundary 1 outline 1000,1000 5000,1000 5000,4000 1000,4000','line boundary 2 outline 6600,1000 10600,1000 10600,4000 6600,4000']){
        const result=await api(command);if(!result.ok)throw new Error(result.error);
      }
      await renderObjects();
      const make=async(bytes,name,id,records,calibration)=>{
        const source=await ReferenceWorkspace.sourceFromFile(new File([Uint8Array.from(atob(bytes),ch=>ch.charCodeAt(0))],name,{type:'application/pdf'}));
        ReferenceWorkspace.context().sources.set(source.meta.id,source);
        const page={id,sourceId:source.meta.id,page:1,imgW:600,imgH:400,crop:[0,0,600,400],mmPerPx:20,x:0,y:0,rot:0,opacity:.5,locked:false,calibration,reviewRequired:false,records};
        await ReferenceWorkspace.preparePage(page,source);ReferenceWorkspace.addPage(1,page);return {id,records,sourceId:source.meta.id};
      };
      const saved=[];
      for(const [index,bytes]of encoded.legacy.entries())saved.push(await make(bytes,'自製舊頁 '+index+'.pdf','legacy-'+index,
        [{id:'evidence-'+index,label:'保留紀錄 '+index,location:'自製 unrelated legacy page '+index,datum:'測試基準',unit:'mm',value:index?null:2500}],null));
      await make(encoded.shared,'issue77-two-rooms.pdf','selected-source',[],{points:[[50,300],[250,300]],distanceMm:4000,inputValue:4000,inputUnit:'mm'});
      await enterFocus('face',1);fiShowTab('underlay');
      window.issue77OldRemoveButton=document.getElementById('ulRemove'); // Retain the real bound legacy button across adoption.
      return saved;
    },{shared:fixture.toString('base64'),legacy:[changedPDF('Note X').toString('base64'),changedPDF('Note Y').toString('base64')]});
    await page.locator('#roomNew').click();await page.waitForFunction(()=>RoomCollectionWorkspace.controller.state().rooms.length===1);
    const before=await snapshot(page);
    check(before.pages.map(page=>({id:page.id,records:page.records,sourceId:page.sourceId})),retained,'explicit adoption preserves both unrelated legacy pages and records');
    check(before.attachment.rooms.length,1,'selected PDF is adopted as one room');
    check(await page.locator('#ulRemove').count(),0,'shared pane hides legacy remove-current-underlay button');
    await page.locator('#refDrawOutline').click();
    await page.waitForFunction(()=>RoomCollectionWorkspace.controller.intent!==null);
    check(await page.evaluate(()=>RoomOutlineWorkspace.hasWork),false,'shared draw step starts manual room intent without automatic recognition');
    await page.locator('#faceDraftCancel').click();await page.waitForFunction(()=>!RoomCollectionWorkspace.hasWork);
    check(await snapshot(page),before,'manual draw-step cancellation preserves retained evidence');
    await page.evaluate(()=>{const button=window.issue77OldRemoveButton;button.id='issue77StaleRemove';document.getElementById('faceInspectorContent').append(button);});
    await page.locator('#issue77StaleRemove').click();
    check(await snapshot(page),before,'actual stale legacy button click cannot delete a retained page or room geometry');
    await page.evaluate(()=>window.issue77OldRemoveButton.remove());
    check(await page.evaluate(()=>{try{ReferenceWorkspace.remove(1);return false;}catch{return true;}}),true,'shared owner remove API refuses legacy deletion');
    check(await snapshot(page),before,'rejected public remove leaves complete evidence unchanged');
    const archive=await page.evaluate(async()=>{const entries=fflate.unzipSync(await ReferenceWorkspace.exportBytes());return JSON.parse(new TextDecoder().decode(entries['manifest.json']));});
    check(archive.faces[0].pages.map(page=>page.records),retained.map(page=>page.records),'actual ZIP retains original records on unrelated pages');
    check(archive.faces[0].pages.every(page=>page.sourceId!==before.attachment.planes[0].sourceId),true,'selected shared PDF has no legacy basis shadow while unrelated pages remain');
    await page.locator('#fileMenuBtn').click();
    const chooserPromise=page.waitForEvent('filechooser');await page.locator('#btnImportReference').click();
    await(await chooserPromise).setFiles({name:'self-authored-import.pdf',mimeType:'application/pdf',buffer:changedPDF('Import')});
    await page.waitForFunction(()=>document.getElementById('referenceDialog').open&&!document.getElementById('refApply').disabled);
    check(await page.locator('#refTarget option').evaluateAll(options=>options.map(option=>option.value)),['new','2'],'real global import modal excludes shared boundary but retains ordinary targets');
    await page.evaluate(()=>document.getElementById('refTarget').add(new Option('stale shared target','1')));
    await page.locator('#refTarget').selectOption('1');await page.locator('#refApply').click();
    check(await snapshot(page),before,'forced stale shared import target writes no invisible legacy page or asset');
    check(await page.locator('#referenceDialog').evaluate(dialog=>dialog.open),true,'shared-target rejection keeps import dialog reviewable');
    await page.locator('#refTarget').selectOption('2');await page.locator('#refApply').click();
    await page.waitForFunction(()=>!document.getElementById('referenceDialog').open&&oc.edit?.bid===2);
    check(await page.evaluate(()=>ReferenceWorkspace.active(2)?.sourceId===ReferenceWorkspace.group(2)?.pages[0]?.sourceId),true,'ordinary target still displays its newly imported source');
    check((await snapshot(page)).pages,before.pages,'valid import to another face preserves all unrelated retained evidence');
    check((await snapshot(page)).attachment,before.attachment,'valid import to another face does not change shared room basis or association');
    check((await snapshot(page)).scene,before.scene,'source operations change no native geometry');
    await page.evaluate(async()=>{await enterFocus('face',1);fiShowTab('underlay');});
    await page.locator('[data-room-unlink]').click();
    check((await snapshot(page)).pages,before.pages,'explicit room unlink preserves every unrelated legacy page and record');
    check((await snapshot(page)).scene,before.scene,'explicit room unlink keeps native geometry');
    check((await snapshot(page)).attachment.rooms.length,0,'explicit room unlink removes only room association');
    await page.locator('#projectInfoButton').click();
    await page.locator('[data-room-source-overview] > summary').click();
    check(await page.locator('[data-room-source-overview]').isVisible(),true,'existing project information retains shared source overview after all unlink');
    check(await page.locator('[data-room-source-collection] option').count(),1,'shared source collection remains reachable with no rooms');
    check(await page.evaluate(()=>RoomCollectionWorkspace.controller.state().planes),before.attachment.planes,'unlink retains exact shared basis');
    await page.locator('[data-room-source-boundary]').selectOption('1');
    await page.locator('[data-room-source-associate]').click();
    await page.waitForFunction(()=>RoomCollectionWorkspace.controller.state().rooms.length===1&&oc.edit?.bid===1);
    const reassociated=await snapshot(page), roomId=reassociated.attachment.rooms[0].id;
    check(reassociated.scene,before.scene,'overview explicitly associates retained native geometry without replacing it');
    check(reassociated.pages,before.pages,'overview association keeps unrelated legacy records');
    check(reassociated.attachment.planes,before.attachment.planes,'overview association uses the existing unique basis');
    const nativeBefore=await page.evaluate(async()=>await api('boundary 1'));
    await page.evaluate(async()=>{await leaveFocus();const result=await api('line delete boundary 1');if(!result.ok)throw Error(result.error);await renderObjects();});
    check((await snapshot(page)).attachment.rooms[0].reviewState,'needs-reassociation','native deletion retires relation without removing source plane');
    const retiredArchive=await page.evaluate(async()=>{const entries=fflate.unzipSync(await ReferenceWorkspace.exportBytes());return {keys:Object.keys(entries),manifest:JSON.parse(new TextDecoder().decode(entries['manifest.json']))};});
    check(retiredArchive.keys.includes('sources/'+before.attachment.planes[0].sourceId),true,'true ZIP keeps shared PDF after the only room boundary was deleted');
    await page.evaluate(async()=>{const result=await api('line boundary 1 outline 1000,1000 4600,1000 4600,4000 1000,4000');if(!result.ok)throw Error(result.error);await renderObjects();});
    check((await snapshot(page)).attachment.rooms[0].reviewState,'needs-reassociation','same-ID creation does not revive old room relation');
    await page.locator('#projectInfoButton').click();
    await page.locator('[data-room-source-overview] > summary').click();
    await page.locator('[data-room-source-room]').selectOption(roomId);
    await page.locator('[data-room-source-boundary]').selectOption('1');
    await page.locator('[data-room-source-associate]').click();
    await page.waitForFunction(()=>RoomCollectionWorkspace.controller.state().rooms[0].reviewState==='confirmed'&&oc.edit?.bid===1);
    const rebuilt=await page.evaluate(async()=>await api('boundary 1'));
    check(rebuilt.geometryFingerprint!==nativeBefore.geometryFingerprint,true,'explicit reassociation checks the changed full native fingerprint');
    check((await snapshot(page)).attachment.rooms[0].id,roomId,'explicit reassociation preserves stable room ID');
    check((await snapshot(page)).attachment.rooms[0].boundaryRef.associationPin,rebuilt.geometryFingerprint,'explicit reassociation pins the new native definition');
    await page.evaluate(async()=>{await api('line undo');renderFaceInspector();});
    check((await snapshot(page)).attachment.rooms[0].reviewState,'needs-reassociation','one metadata undo restores retired relation');
    check((await page.evaluate(async()=>await api('boundary 1'))).geometryFingerprint,rebuilt.geometryFingerprint,'relation undo leaves new native geometry intact');
    await page.evaluate(async()=>{await api('line redo');renderFaceInspector();});
    check((await snapshot(page)).attachment.rooms[0].boundaryRef.associationPin,rebuilt.geometryFingerprint,'relation redo restores the explicitly accepted pin');
    // The persisted schema allows nonempty string IDs, including "new". Admit
    // that valid record through the formal owner API and exercise the real UI.
    await page.evaluate(async()=>{
      await leaveFocus();const next=RoomCollectionWorkspace.controller.state(),oldId=next.rooms[0].id;
      next.rooms[0].id='new';for(const collection of next.collections)collection.roomIds=collection.roomIds.map(id=>id===oldId?'new':id);
      ReferenceWorkspace.setFeatureAttachment('source-rooms',next,ReferenceWorkspace.getProjectState().contextToken,{reason:'valid saved string room ID fixture'});
    });
    const stringIdBefore=await snapshot(page);
    await page.locator('#projectInfoButton').click();await page.locator('[data-room-source-overview] > summary').click();
    check(await page.locator('[data-room-source-room]').inputValue(),'','new-room UI intent uses an empty sentinel outside the persisted ID domain');
    check(await page.locator('[data-room-source-room] option[value="new"]').count(),1,'valid saved room ID new has exactly one existing-room option');
    await page.locator('[data-room-source-boundary]').selectOption('2');await page.locator('[data-room-source-associate]').click();
    await page.waitForFunction(()=>RoomCollectionWorkspace.controller.state().rooms.length===2&&oc.edit?.bid===2);
    const stringIdAfter=await snapshot(page);
    check(stringIdAfter.attachment.rooms.find(room=>room.id==='new'),stringIdBefore.attachment.rooms[0],'new-room choice preserves valid existing room named by ID new');
    check(stringIdAfter.scene,stringIdBefore.scene,'new explicit relation never replaces either native boundary');
    await page.evaluate(async()=>{await api('line undo');renderFaceInspector();});
    check(await snapshot(page),stringIdBefore,'one metadata undo removes only the newly associated room');
    // Hold the real derived-page preparation, then navigate to another actual
    // native boundary. No source pixels or native success replies are faked.
    await page.evaluate(async()=>{
      await leaveFocus();const derived=RoomCollectionWorkspace.sourcePage(1);delete derived.src;
      const original=ReferenceWorkspace.preparePage;let release;
      window.__coldRoom={started:false,finished:null,release:()=>release(),original};
      const gate=new Promise(resolve=>{release=resolve;});
      ReferenceWorkspace.preparePage=async(page,source)=>{
        if(!__coldRoom.started){__coldRoom.started=true;await gate;}
        return original(page,source);
      };
      __coldRoom.pending=RoomCollectionWorkspace.beginEdit('new').then(()=>{__coldRoom.finished='opened';},error=>{__coldRoom.finished=error.message;});
    });
    await page.waitForFunction(()=>__coldRoom.started);
    await page.evaluate(async()=>{await enterFocus('face',2);});
    check(await page.evaluate(()=>oc.focus.id),2,'newer real native face navigation completes while old source load waits');
    await page.evaluate(async()=>{__coldRoom.release();await __coldRoom.pending;ReferenceWorkspace.preparePage=__coldRoom.original;});
    check(await page.evaluate(()=>/晚到/.test(__coldRoom.finished)),true,'old room edit rejects its late source load');
    check(await page.evaluate(()=>({focus:oc.focus.id,edit:oc.edit.bid,tool:fe.tool,intent:RoomCollectionWorkspace.controller.intent})),
      {focus:2,edit:2,tool:'select',intent:null},'late room open cannot replace newer navigation or start an old room draft');
    check(await snapshot(page),stringIdBefore,'late navigation changes no native geometry, basis or saved metadata');
    await page.setViewportSize({width:390,height:844});
    await page.locator('#projectInfoButton').click();
    await page.locator('[data-room-source-overview] > summary').click();
    check(await page.locator('[data-room-source-associate]').isVisible(),true,'390px existing project info contains usable source relation controls');
    await page.locator('[data-room-source-associate]').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(evidence,'mobile-source-overview.png')});
    check(errors,[],'no page or console errors');
    console.log(JSON.stringify({checks,evidence,browser:'Chromium actual UI',ownerAdapter:process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER||'official owner API',privateAssets:false}));
  }finally{await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
