/* Formal #48 acceptance: actual app wiring/store/history/PDF, no injected backend. */
'use strict';
const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const zip=require('./vendor/fflate/umd/index.js');
const url=process.env.GEOMETRY_TEST_URL,out=process.env.GEOMETRY_EVIDENCE_TEST_DIR,root=path.resolve(__dirname,'..');
if(!url||new URL(url).hostname!=='127.0.0.1'||new URL(url).port==='8765'||!out||!path.resolve(out).startsWith(os.tmpdir()+path.sep))throw Error('Explicit isolated loopback service and TEMP output required');
fs.mkdirSync(out,{recursive:true});
function fixture(changed=false){
  const objects=['<< /Type /Catalog /Pages 2 0 R >>','<< /Type /Pages /Kids [3 0 R 5 0 R 7 0 R 9 0 R] /Count 4 >>'];
  for(const [i,rotation]of [0,90,180,270].entries()){
    const stream=`0 0 0 RG 1 w 20 30 90 70 re S BT /F1 12 Tf 20 160 Td (Authored evidence ${changed?'458':'457.5'} mm) Tj ET`;
    objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 340 260] /CropBox [20 30 320 230] /Rotate ${rotation} /Resources << /Font << /F1 11 0 R >> >> /Contents ${4+i*2} 0 R >>`,`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`);
  }objects.push('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
  let text='%PDF-1.4\n',offsets=[0];objects.forEach((object,i)=>{offsets.push(text.length);text+=`${i+1} 0 obj\n${object}\nendobj\n`;});const xref=text.length;
  text+=`xref\n0 ${objects.length+1}\n0000000000 65535 f \n`+offsets.slice(1).map(n=>String(n).padStart(10,'0')+' 00000 n \n').join('');
  return Buffer.from(text+`trailer\n<< /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`);
}
const checks=[],errors=[];
const check=(name,ok)=>{checks.push({name,pass:ok===true});console.log((ok?'PASS ':'FAIL ')+name);assert.equal(ok,true,name);};
(async()=>{
 const runtime=await (await fetch(new URL('runtime',url))).json();assert.equal(runtime.root,root);assert.equal(runtime.fresh,true);
 const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const git=(...args)=>require('node:child_process').execFileSync('git',args,{cwd:root,encoding:'utf8'}).trim();
 const head=git('rev-parse','HEAD'),tree=git('rev-parse','HEAD^{tree}'),dirty=git('status','--porcelain');
 if(process.env.GEOMETRY_REQUIRE_CLEAN==='1')assert.equal(dirty,'','Final acceptance requires a frozen clean tree');
 try {
 for(const width of [1280,390]){
  const context=await browser.newContext({viewport:{width,height:900},deviceScaleFactor:2,acceptDownloads:true}),page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('dialog',d=>d.accept());
  await page.goto(url);await page.waitForFunction(()=>connection.phase==='ready');await page.evaluate(()=>window.showSaveFilePicker=undefined);
  const ev=async(body,arg)=>page.evaluate(body,arg);
  const native=()=>ev(async()=>({scene:(await apiRequest('dump')).text,revision:(await apiRequest('engineering-read')).revision}));
  const bundle=()=>ev(()=>ReferenceWorkspace.readFeatureAttachment(EvidenceLinks.KIND));
  async function parameter(remove=false,input='457.5'){
    await ev(async({remove,input})=>{
      const read=await apiRequest('engineering-read'),operations=remove?[{op:'delete-parameter',id:0}]:[{op:'put-parameter',value:{id:0,name:'Authored card',fields:[{id:0,name:'Authored field',type:'dimension',input}]}}];
      const p=await EngineeringAdapter.preview({operations,expectedRevision:read.revision});if(!p.valid)throw Error(JSON.stringify(p));await EngineeringAdapter.confirm({token:p.token});await renderObjects();
    },{remove,input});
  }
  async function face(){await ev(async()=>{await enterFocus('face',1);fiShowTab('underlay');});await page.waitForSelector('#refRecordDetails',{state:'attached'});if(width<=680)await ev(()=>openPanel('right',document.getElementById('workspaceToggleRight')));await ev(()=>document.getElementById('refRecordDetails').open=true);await page.waitForSelector('[data-evidence-target]');}
  async function importPDF(number=1,changed=false){
    await ev(()=>ReferenceWorkspace.chooseFile(1));await page.locator('#referenceFile').setInputFiles({name:'same.pdf',mimeType:'application/pdf',buffer:fixture(changed)});
    await page.waitForFunction(()=>document.getElementById('referenceDialog').open&&!document.getElementById('refApply').disabled);
    if(number!==1){await page.locator('#refPageNumber').fill(String(number));await page.locator('#refPageNumber').dispatchEvent('change');await page.waitForFunction(()=>!document.getElementById('refApply').disabled);}
    await page.locator('#refApply').click();await page.waitForFunction(()=>!ReferenceWorkspace.busy&&!document.getElementById('referenceDialog').open);
    if(width<=680)await ev(()=>openPanel('right',document.getElementById('workspaceToggleRight')));
    await ev(()=>document.getElementById('refRecordDetails').open=true);await page.waitForSelector('[data-evidence-target]');
  }
  async function region(rect=[30,40,70,50]){
    await page.locator('[data-evidence-select]').click();
    const points=await ev(([x,y,w,h])=>{const p=ReferenceWorkspace.active(1),root=document.getElementById('faceEditorRoot'),svg=document.getElementById('faceEditorSvg');return [[x,y],[x+w,y+h]].map(v=>{const mm=feUlImgToMm(p,...v),q=svg.createSVGPoint();q.x=mm[0];q.y=mm[1];const r=q.matrixTransform(root.getScreenCTM());return {x:r.x,y:r.y};});},rect);
    await page.mouse.move(points[0].x,points[0].y);await page.mouse.down();await page.mouse.move(points[1].x,points[1].y,{steps:5});await page.mouse.up();
    await page.waitForFunction(()=>EvidenceLinksApp.ui?.snapshot().region&&!EvidenceLinksApp.ui.snapshot().selecting);
    return ev(()=>EvidenceLinksApp.ui.snapshot().region);
  }
  async function add(){
    await page.locator('[data-evidence-target]').selectOption('0:0');
    await page.locator('[data-evidence-input="drawing-text"]').fill('<img src=x onerror=window.__unsafe=true> drawing');
    await page.locator('[data-evidence-input="drawing-value"]').fill('915/2');await page.locator('[data-evidence-input="drawing-unit"]').selectOption('mm');
    await page.locator('[data-evidence-input="measurement-value"]').fill('460.125');await page.locator('[data-evidence-input="measurement-unit"]').selectOption('mm');
    await page.locator('[data-evidence-save]').click();await page.waitForSelector('[data-evidence-id]');
  }
  async function save(name){const archive=path.join(out,width+'-'+name+'.gcanvas');await ev(()=>closePanels());const download=page.waitForEvent('download');await page.locator('#projectBar [data-project-action="save"]').click();await (await download).saveAs(archive);await page.waitForFunction(()=>!ReferenceWorkspace.busy);return archive;}
  async function open(archive){await ev(()=>closePanels());if(!await page.locator('#btnOpenProject').isVisible())await page.locator('#fileMenuBtn').click();const chooser=page.waitForEvent('filechooser');await page.locator('#btnOpenProject').click();await (await chooser).setFiles(archive);await page.waitForFunction(()=>!ReferenceWorkspace.busy);}
  await ev(async()=>{await apiRequest('line reset');await apiRequest('line boundary 1 outline 0,0 4000,0 4000,3000 0,3000');await renderObjects();});await parameter();
  await ev(async()=>{await enterFocus('face',1);fiShowTab('underlay');});await importPDF();
  check(width+' actual scripts and meaningful UI loaded',!!await page.title()&&await page.locator('[data-evidence-target]').count()===1);
  const original=await native(),beforeCount=await ev(()=>ReferenceWorkspace.history.undo.length);
  await region();await page.locator('[data-evidence-cancel]').click();check(width+' rectangle cancel is zero attachment/history/native writes',await bundle()===null&&await ev(()=>ReferenceWorkspace.history.undo.length)===beforeCount&&JSON.stringify(await native())===JSON.stringify(original));
  const rect=await region();await add();
  let saved=await bundle();check(width+' manual field0 creation is one local history and exact original rectangle',saved.links[0].target.parameterId===0&&saved.links[0].target.fieldId===0&&saved.links[0].region.every((n,i)=>Math.abs(n-rect[i])<1e-6)&&await ev(()=>ReferenceWorkspace.history.undo.length)===beforeCount+1);
  check(width+' drawing/measurement/native exact rational kept separate and text safe',saved.links[0].observations.drawing.rawValue==='915/2'&&saved.links[0].observations.measurement.rawValue==='460.125'&&await page.locator('[data-evidence-value="model"]').innerText()==='915/2 mm'&&!await ev(()=>window.__unsafe)&&JSON.stringify(await native())===JSON.stringify(original));
  await page.locator('[data-evidence-reviewed]').check();await page.waitForSelector('[data-evidence-status="confirmed-content"]');
  saved=await bundle();check(width+' review annotation never changes native World',!!saved.links[0].humanConfirmation&&JSON.stringify(await native())===JSON.stringify(original));
  await ev(async()=>{await apiRequest('line undo');await EvidenceLinksApp.ui.refresh();});check(width+' single undo restores unchecked evidence',!(await bundle()).links[0].humanConfirmation);
  await ev(async()=>{await apiRequest('line redo');});await page.waitForSelector('[data-evidence-status="needs-reassociation"]');check(width+' redo preserves historical confirmation and requires reassociation',!!(await bundle()).links[0].humanConfirmation&&await page.locator('[data-evidence-status="needs-reassociation"]').count()===1);
  await page.locator('[data-evidence-rebind-target]').selectOption('0:0');await page.locator('[data-evidence-rebind]').click();await page.waitForSelector('[data-evidence-status="unchecked"]');await page.locator('[data-evidence-reviewed]').check();await page.waitForSelector('[data-evidence-status="confirmed-content"]');
  await page.screenshot({path:path.join(out,width+'-evidence.png'),fullPage:false});
  const archive=await save('full'),entries=zip.unzipSync(fs.readFileSync(archive)),m=JSON.parse(Buffer.from(entries['manifest.json']).toString());
  check(width+' genuine downloaded ZIP uses /12 and exact original PDF once',m.format==='geometry-canvas/12'&&m.requiredCapabilities.includes('geometry-evidence-links/1')&&m.sources.length===1&&Buffer.from(entries[m.sources[0].path]).equals(fixture()));
  const savedScope=(await bundle()).links[0].target.projectScope;
  await ev(async()=>{await ReferenceWorkspace.newProject();await renderObjects();});check(width+' reopen begins in empty distinct context',await bundle()===null&&await ev(async savedScope=>ReferenceWorkspace.getProjectState().id!==savedScope&&(await apiRequest('objects')).parameters.length===0,savedScope));
  await open(archive);check(width+' real file chooser restores full bundle/document/scope in new context',JSON.stringify(await bundle())===JSON.stringify(m.featureAttachments.records.find(r=>r.kind==='evidence-links').value));
  await face();check(width+' reopened historical review requires manual field reassociation',await page.locator('[data-evidence-status="needs-reassociation"]').count()===1&&await page.locator('[data-evidence-reviewed]').isDisabled());
  await page.locator('[data-evidence-rebind-target]').selectOption('0:0');await page.locator('[data-evidence-rebind]').click();await page.waitForSelector('[data-evidence-status="unchecked"]');
  await page.locator('[data-evidence-locate-target]').click();await page.waitForSelector('#paramUsage',{state:'attached'});await ev(()=>document.getElementById('paramUsage').open=true);await page.waitForSelector('[data-parameter-evidence-locate]');
  check(width+' source-to-field guarded navigation uses existing parameter disclosure',await page.locator('[data-param-field="0"]').count()===1&&await page.locator('[data-parameter-evidence]').count()===1);
  await page.locator('[data-parameter-evidence-locate]').click();
  await page.waitForFunction(()=>document.getElementById('referenceDialog').open||document.querySelector('#toastRegion .toast.error'));
  if(!await ev(()=>document.getElementById('referenceDialog').open))throw Error('Original-page locator rejected: '+await page.locator('#toastRegion .toast.error').first().innerText());
  check(width+' field-to-source prepared original PDF paints saved rectangle read-only',await ev(()=>document.getElementById('refCropOverlay').style.width!=='')&&await page.locator('#refApply').isHidden());
  const beforeCrop=await page.locator('#refCropOverlay').getAttribute('style'),preview=await page.locator('#refPagePreview').boundingBox();
  await page.mouse.move(preview.x+10,preview.y+10);await page.mouse.down();await page.mouse.move(preview.x+70,preview.y+50);await page.mouse.up();
  check(width+' read-only original PDF cannot change recorded rectangle',beforeCrop===await page.locator('#refCropOverlay').getAttribute('style')&&await page.locator('#refResetCrop').isDisabled());await page.locator('#refClose').click();
  if(width===1280){
    await face();await importPDF(2);
    const located=await ev(async()=>{const link=ReferenceWorkspace.readFeatureAttachment(EvidenceLinks.KIND).links[0],p=ReferenceWorkspace.group(1).pages[0];delete p.src;p.rot=270;p.crop=[10,15,p.imgW-20,p.imgH-30];ReferenceWorkspace.changed(1,true);const result=await EvidenceLinksApp.getController().locate(link.evidenceId);return {ok:result.ok,active:ReferenceWorkspace.active(1).id,page:link.document.referencePageId,paint:!!document.querySelector('[data-evidence-located]'),src:p.src};});
    check('real cold prepared commit activates exact original page and paints region through rotation/crop',located.ok&&located.active===located.page&&located.paint&&located.src.startsWith('data:image/png;'));
    // Exercise the actual production seam while its original PDF work is cold.
    // Test-only delays wrap real hashing/render preparation, never a fake store.
    for(const stage of ['hash','prepared'])for(const mode of ['cancel','page','pan','basis','native','history','context','bytes']){
      await open(archive);await face();await importPDF(2);
      await ev(async({stage})=>{
        const c=EvidenceLinksApp.getController(),link=ReferenceWorkspace.readFeatureAttachment(EvidenceLinks.KIND).links[0],p=ReferenceWorkspace.group(1).pages.find(p=>p.id===link.document.referencePageId);
        delete p.src;window.__race={stage,link,entered:false,commits:0};let release;const hold=new Promise(r=>release=r);__race.release=release;
        const original=stage==='hash'?GeometryProject.sha:ReferenceWorkspace.prepareReferencePage;__race.restore=()=>{if(stage==='hash')GeometryProject.sha=original;else ReferenceWorkspace.prepareReferencePage=original;};
        if(stage==='hash'){let first=true;GeometryProject.sha=async bytes=>{const hash=await original(bytes);if(first){first=false;__race.entered=true;await hold;}return hash;};}
        else ReferenceWorkspace.prepareReferencePage=async(...args)=>{const prepared=await original(...args);__race.entered=true;await hold;return prepared;};
        const commit=ReferenceWorkspace.commitPreparedReferencePage;ReferenceWorkspace.commitPreparedReferencePage=(...args)=>{__race.commits++;return commit(...args);};__race.restoreCommit=()=>ReferenceWorkspace.commitPreparedReferencePage=commit;
        __race.pending=c.locate(link.evidenceId).then(()=>({ok:true}),e=>({ok:false,message:e.message}));
      },{stage});
      await page.waitForFunction(()=>__race.entered);
      check(stage+' '+mode+' detached preparation does not warm/navigate/fit',await ev(()=>!ReferenceWorkspace.group(1).pages.find(p=>p.id===__race.link.document.referencePageId).src&&ReferenceWorkspace.active(1).page===2&&__race.commits===0));
      if(mode==='cancel')await ev(()=>EvidenceLinksApp.getController().cancel());
      else if(mode==='page')await ev(async()=>ReferenceWorkspace.selectPage(1,ReferenceWorkspace.group(1).pages[0].id));
      else if(mode==='pan')await ev(()=>{fe.panX+=17;drawFaceEditor();});
      else if(mode==='basis')await ev(()=>{const p=ReferenceWorkspace.group(1).pages[0];p.rot=90;ReferenceWorkspace.changed(1,true);});
      else if(mode==='native')await parameter(false,'458');
      else if(mode==='history')await ev(async()=>apiRequest('line undo'));
      else if(mode==='context')await ev(async()=>ReferenceWorkspace.newProject());
      else if(mode==='bytes')await ev(()=>ReferenceWorkspace.context().sources.get(__race.link.document.sourceHash).bytes[0]^=1);
      const after=await ev(()=>JSON.stringify({state:ReferenceWorkspace.getProjectState(),active:ReferenceWorkspace.active(1)?.id??null,camera:[fe.panX,fe.panY,fe.zoom],modal:document.getElementById('referenceDialog').open,paint:document.querySelector('[data-evidence-located]')?.getAttribute('points')??null}));
      const result=await ev(async()=>{__race.release();const result=await __race.pending;__race.restore();__race.restoreCommit();return result;});
      check(stage+' '+mode+' supersession has zero late navigation/fit/paint',!result.ok&&await ev(after=>after===JSON.stringify({state:ReferenceWorkspace.getProjectState(),active:ReferenceWorkspace.active(1)?.id??null,camera:[fe.panX,fe.panY,fe.zoom],modal:document.getElementById('referenceDialog').open,paint:document.querySelector('[data-evidence-located]')?.getAttribute('points')??null}),after));
    }
    await open(archive);await face();
    // A legal same-name PDF replacement never transfers historical review.
    await importPDF(1,true);
    await ev(async()=>ReferenceWorkspace.selectPage(1,ReferenceWorkspace.group(1).pages[0].id));
    await ev(()=>{const g=ReferenceWorkspace.group(1),old=g.pages[0],replacement=g.pages.at(-1);if(!feChangeUnderlay(1,old,{sourceId:replacement.sourceId},true))throw Error('replacement was not applied');renderFaceInspector();});
    await ev(()=>document.getElementById('refRecordDetails').open=true);await page.waitForSelector('[data-evidence-status="source-changed"]');
    check('same filename replacement retains old observations but blocks review/locate',await page.locator('[data-evidence-reviewed]').isDisabled()&&(await bundle()).links[0].observations.drawing.rawValue==='915/2');
    await open(archive);await face();
    const unchanged=await native(),beforeImport=await ev(()=>JSON.stringify({state:ReferenceWorkspace.getProjectState(),bundle:ReferenceWorkspace.readFeatureAttachment(EvidenceLinks.KIND),history:ReferenceWorkspace.history.undo.length}));
    for(const [label,change]of [
      ['unknown-format',m=>m.format='geometry-canvas/999'],['capability-stripped',m=>m.requiredCapabilities=[]],
      ['unknown-schema',m=>m.featureAttachments.records[0].value.schema='geometry-evidence-links/999'],
      ['missing-original',m=>m.sources=[]],['wrong-page',m=>m.featureAttachments.records[0].value.links[0].document.page=99],
      ['wrong-dimensions',m=>m.featureAttachments.records[0].value.links[0].document.pageWidth++],
      ['over-capacity',m=>{const v=m.featureAttachments.records[0].value;v.links=Array.from({length:257},(_,i)=>({...structuredClone(v.links[0]),evidenceId:'e'+i}));}]
    ]){
      const altered=zip.unzipSync(fs.readFileSync(archive)),manifest=JSON.parse(Buffer.from(altered['manifest.json']).toString());change(manifest);altered['manifest.json']=Buffer.from(JSON.stringify(manifest));const bad=path.join(out,'reject-'+label+'.gcanvas');fs.writeFileSync(bad,zip.zipSync(altered));
      const rejected=await ev(async bytes=>{try{await ReferenceWorkspace.importBytes(new Uint8Array(bytes),'bad.gcanvas');return false;}catch{return true;}},Array.from(fs.readFileSync(bad)));
      check('formal import '+label+' rejects before native/project/assets/history replacement',rejected&&JSON.stringify(await native())===JSON.stringify(unchanged)&&await ev(before=>before===JSON.stringify({state:ReferenceWorkspace.getProjectState(),bundle:ReferenceWorkspace.readFeatureAttachment(EvidenceLinks.KIND),history:ReferenceWorkspace.history.undo.length}),beforeImport));
    }
  }
  await face();await parameter(true);await ev(()=>EvidenceLinksApp.ui?.refresh());await page.waitForSelector('[data-evidence-status="target-missing"]');
  check(width+' native target deletion preserves unresolved observations and remains saveable',(await bundle()).links.length===1&&!!await save('missing-target'));
  await parameter();await face();check(width+' exact ID recreation never inherits identity lease',await page.locator('[data-evidence-status="needs-reassociation"]').count()===1);
  // Evidence-only closure: remove reference linkage, save original source, and
  // reopen with no face underlay, then locate through the existing PDF reader.
  await ev(()=>{ReferenceWorkspace.remove(1);});const only=await save('evidence-only'),onlyEntries=zip.unzipSync(fs.readFileSync(only)),onlyManifest=JSON.parse(Buffer.from(onlyEntries['manifest.json']).toString());
  check(width+' evidence-only source survives removal from all face references',onlyManifest.faces.length===0&&onlyManifest.sources.length===1&&Buffer.from(onlyEntries[onlyManifest.sources[0].path]).equals(fixture()));
  await ev(async()=>{await ReferenceWorkspace.newProject();await renderObjects();});await open(only);
  await ev(()=>{resetSceneFocus();drawObjects();selectObject('parameter',0);document.getElementById('paramUsage').open=true;});await page.waitForSelector('[data-parameter-evidence-locate]');
  await page.locator('[data-parameter-evidence-locate]').click();await page.waitForFunction(()=>document.getElementById('referenceDialog').open);check(width+' evidence-only source locates after real ZIP reopen',await page.locator('#refPagePreview img').count()===1);await page.locator('#refClose').click();
  check(width+' no horizontal overflow or runtime injection',await ev(()=>document.documentElement.scrollWidth<=innerWidth)&&!await ev(()=>window.__unsafe));
  await page.screenshot({path:path.join(out,width+'-reopened.png'),fullPage:false});await context.close();
 }
 check('console/page health',errors.length===0);
 }finally{for(const c of browser.contexts())for(const p of c.pages()){await p.screenshot({path:path.join(out,'last-state.png')}).catch(()=>{});fs.writeFileSync(path.join(out,'last-dom.txt'),await p.locator('body').innerText().catch(()=>''));}fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({head,tree,dirty,runtime,checks,errors,coverage:'Actual production app; synthetic PDF only; Playwright picker/download and 390px Chromium; physical OS picker/IME/iOS unverified'},null,2));await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
