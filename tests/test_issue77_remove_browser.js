/* Real UI regression for shared-source removal with retained legacy evidence. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {chromium}=require('playwright');
const url=process.env.GEOMETRY_TEST_URL;
if(!url || !process.env.GEOMETRY_FEEDBACK_DIR?.startsWith(os.tmpdir()+path.sep))throw new Error('Explicit isolated URL and TEMP feedback directory required.');
const fixture=fs.readFileSync(path.join(__dirname,'fixtures/issue77-two-rooms.pdf'));
const ownerAdapter=process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER?fs.readFileSync(process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER,'utf8'):null;
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
    await page.locator('#roomSourceCreate').click();await page.waitForSelector('#roomNew');
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
    check(errors,[],'no page or console errors');
    console.log(JSON.stringify({checks,browser:'Chromium actual UI',ownerAdapter:process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER||'official owner API',privateAssets:false}));
  }finally{await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
