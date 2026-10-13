/* #48 real app/Chromium/native adapter check. Attachment backend below is
   deliberately injected memory: project ZIP registration belongs to its owner. */
'use strict';
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const url=process.env.GEOMETRY_TEST_URL,feedback=process.env.GEOMETRY_FEEDBACK_DIR;
if(!url||!feedback||!path.resolve(feedback).startsWith(os.tmpdir()+path.sep))throw Error('An explicit isolated GEOMETRY_TEST_URL and feedback directory under TEMP are required');
const output=process.env.GEOMETRY_EVIDENCE_TEST_DIR||path.join(os.tmpdir(),'geometry-evidence-tests','browser');
if(!path.resolve(output).startsWith(os.tmpdir()+path.sep))throw Error('Screenshots must remain under TEMP');
fs.mkdirSync(output,{recursive:true});
function fixture(changed=false){
  // Authored here. No private PDF, OCR, external font, or asset request.
  const objects=['<< /Type /Catalog /Pages 2 0 R >>','<< /Type /Pages /Kids [3 0 R 5 0 R 7 0 R 9 0 R] /Count 4 >>'];
  for(const [i,rotation]of [0,90,180,270].entries()){
    const stream=`0 0 0 RG 1 w 20 30 90 70 re S BT /F1 12 Tf 20 160 Td (Authored evidence ${changed?'458':'457.5'} mm) Tj ET`;
    objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 340 260] /CropBox [20 30 320 230] /Rotate ${rotation} /Resources << /Font << /F1 11 0 R >> >> /Contents ${4+i*2} 0 R >>`,`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`);
  }objects.push('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
  let text='%PDF-1.4\n',offsets=[0];objects.forEach((object,i)=>{offsets.push(text.length);text+=`${i+1} 0 obj\n${object}\nendobj\n`;});const xref=text.length;
  text+=`xref\n0 ${objects.length+1}\n0000000000 65535 f \n`+offsets.slice(1).map(n=>String(n).padStart(10,'0')+' 00000 n \n').join('');
  return Buffer.from(text+`trailer\n<< /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`);
}
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const context=await browser.newContext({viewport:{width:1280,height:900},deviceScaleFactor:2}),page=await context.newPage(),errors=[];let passed=0;
  page.on('pageerror',error=>errors.push(error.message));page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});page.on('dialog',dialog=>dialog.accept());
  const check=(name,value)=>{assert.equal(value,true,name);++passed;console.log('PASS '+name);};
  const native=()=>page.evaluate(async()=>({scene:(await apiRequest('dump')).text,revision:(await apiRequest('engineering-read')).revision}));
  async function parameter(input='457.5',remove=false){
    await page.evaluate(async({input,remove})=>{
      const r=await apiRequest('engineering-read'),operations=remove?[{op:'delete-parameter',id:0}]:[{op:'put-parameter',value:{id:0,name:'Authored card',fields:[{id:0,name:'Authored field',type:'dimension',input}]}}];
      const preview=await (await fetch('/engineering/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'engineering-transaction/1',expectedRevision:r.revision,operations})})).json();
      if(!preview.preview?.valid)throw Error(JSON.stringify(preview));const c=await apiRequest('engineering-confirm '+preview.preview.token);if(!c.ok)throw Error(c.error);await renderObjects();
      window.__evidenceNativeRevision=(await apiRequest('source-inspect')).revision;
    },{input,remove});
  }
  async function importPage(number,changed=false){
    await page.evaluate(async bytes=>{window.__evidenceSource=await ReferenceWorkspace.sourceFromFile(new File([new Uint8Array(bytes)],'authored-evidence.pdf',{type:'application/pdf'}));window.__evidenceSources=window.__evidenceSources||new Map();__evidenceSources.set(__evidenceSource.meta.id,__evidenceSource);await ReferenceWorkspace.openSource(__evidenceSource,1);},Array.from(fixture(changed)));
    await page.locator('#refApply').waitFor({state:'visible'});await page.waitForFunction(()=>!document.getElementById('refApply').disabled);
    if(number!==1){await page.locator('#refPageNumber').fill(String(number));await page.locator('#refPageNumber').dispatchEvent('change');await page.waitForFunction(()=>!document.getElementById('refApply').disabled);}
    await page.locator('#refApply').click();await page.waitForFunction(()=>ReferenceWorkspace.active(1)?.page===Number(document.getElementById('refPageNumber').value)&&!document.getElementById('referenceDialog').open);
    await page.evaluate(()=>{document.getElementById('refRecordDetails').open=true;});
  }
  async function mount(reuseController=false,expectRejected=false){
    await page.evaluate(async reuseController=>{
      window.__evidenceUI?.destroy();window.__evidenceController?.cancel();
      document.getElementById('refRecordDetails').open=true;
      window.__evidenceAnnotationRevision=window.__evidenceAnnotationRevision||0;
      window.__evidenceAddCalls=window.__evidenceAddCalls||0;window.__evidenceWriteCalls=window.__evidenceWriteCalls||0;
      window.__evidenceNativeRevision=(await apiRequest('source-inspect')).revision;
      window.__evidenceBackend=window.__evidenceBackend||EvidenceLinks.empty();window.__evidenceHold=null;
      const getStamp=()=>{const p=ReferenceWorkspace.getProjectState();return {projectScope:p.id,contextToken:p.contextToken,revision:p.revision+__evidenceAnnotationRevision,nativeRevision:__evidenceNativeRevision};};
      const modelValue=(r,target)=>r.state.parameters.find(p=>p.id===target.parameterId)?.fields.find(f=>f.id===target.fieldId)?.value??null;
      const readCurrent=async(document,target)=>{
        const hold=window.__evidenceHold;if(hold)await hold.promise;
        const [graph,r]=await Promise.all([apiRequest('source-inspect'),apiRequest('engineering-read')]),p=ReferenceWorkspace.group(1)?.pages.find(p=>p.id===document.referencePageId);
        const node=graph.nodes.find(n=>n.key===`parameter-field:${target.parameterId}:f${target.fieldId}`),scope=ReferenceWorkspace.getProjectState().id;
        if(graph.revision!==r.revision)throw Error('Native graph/value snapshot changed while reading');
        return {document:p?EvidenceLinks.documentFromReference(p,__evidenceSources.get(p.sourceId)):null,target:node?EvidenceLinks.targetFromNode(scope,node):null,modelValue:modelValue(r,target),nativeRevision:graph.revision};
      };
      const readSelection=async()=>{
        const captured=getStamp(),hold=window.__evidenceHold;if(hold)await hold.promise;
        const [graph,r]=await Promise.all([apiRequest('source-inspect'),apiRequest('engineering-read')]),p=ReferenceWorkspace.active(1);
        if(graph.revision!==r.revision||graph.revision!==captured.nativeRevision)throw Error('Native selection snapshot changed while reading');
        return {stamp:captured,document:p?EvidenceLinks.documentFromReference(p,__evidenceSources.get(p.sourceId)):null,targets:graph.nodes.filter(n=>n.kind==='parameter-field').map(n=>{const target=EvidenceLinks.targetFromNode(captured.projectScope,n);return {target,label:n.label+' · #'+n.id+':'+n.fieldId,modelValue:modelValue(r,target)};})};
      };
      window.__evidenceLocateCounters=window.__evidenceLocateCounters||{navigation:0,fit:0,paint:0};window.__evidenceAsyncNavigationErrors=window.__evidenceAsyncNavigationErrors||[];
      const getSourceStamp=document=>{
        const group=ReferenceWorkspace.group(1),p=group?.pages.find(p=>p.id===document.referencePageId),source=p&&__evidenceSources.get(p.sourceId);
        EvidenceLinks.documentFromReference(p,source);
        return {referencePageId:p.id,sourceId:source.meta.id,sourceHash:source.meta.hash,sourceType:source.meta.type,basis:GeometryProject.reviewBasis(p),activeReference:group.activePageId,selection:group.selection??null,panX:fe.panX,panY:fe.panY,zoom:fe.zoom};
      };
      const locator=EvidenceLinks.createLocator({getSourceStamp,
        async prepare(document,region,{assertCurrent}){
          const p=ReferenceWorkspace.group(1)?.pages.find(p=>p.id===document.referencePageId),source=p&&__evidenceSources.get(p.sourceId);
          EvidenceLinks.documentFromReference(p,source);assertCurrent();
          // PDF handles/render caches belong to this detached byte snapshot;
          // preparation never adopts a render or touches the live source cache.
          const sourceSnapshot={meta:{...source.meta},bytes:source.bytes.slice()};
          const hold=window.__evidenceLocatorHold;if(hold){hold.enteredResolve();await hold.promise;assertCurrent();}
          const hash=await GeometryProject.sha(sourceSnapshot.bytes);assertCurrent();
          if(hash!==document.sourceHash)throw Object.assign(Error('Detached PDF bytes do not match saved source'),{code:'EVIDENCE_DOCUMENT'});
          const pdf=await ReferenceWorkspace.documentFor(sourceSnapshot);assertCurrent();const page=await pdf.getPage(document.page);assertCurrent();
          const viewport=page.getViewport({scale:1}),render=await ReferenceWorkspace.renderPage(sourceSnapshot,document.page);assertCurrent();
          if(viewport.width!==document.pageWidth||viewport.height!==document.pageHeight||render.width!==document.pageWidth||render.height!==document.pageHeight)throw Error('Detached PDF dimensions do not match saved document');
          const prepared={sourceHash:hash,page:document.page,width:render.width,height:render.height,src:render.src,sourceStamp:JSON.stringify(getSourceStamp(document))};
          if(window.__evidenceBadPrepared==='source')prepared.sourceHash='0'.repeat(64);if(window.__evidenceBadPrepared==='page')prepared.page++;if(window.__evidenceBadPrepared==='dimensions')prepared.width++;
          return prepared;
        },
        commit(prepared,document,region){
          if(prepared?.sourceHash!==document.sourceHash||prepared.page!==document.page||prepared.width!==document.pageWidth||prepared.height!==document.pageHeight||typeof prepared.src!=='string'||!prepared.src.startsWith('data:image/png;')||prepared.sourceStamp!==JSON.stringify(getSourceStamp(document)))throw Object.assign(Error('Wrong detached source/page/dimensions'),{code:'EVIDENCE_DOCUMENT'});
          ReferenceWorkspace.assertEditable();const p=ReferenceWorkspace.group(1)?.pages.find(p=>p.id===document.referencePageId);
          // Harness shim only. Stage into a detached render, then warm the
          // existing reader before its no-await branch. Production integration
          // still requires the shared owner's true synchronous prepared entry.
          p.src=prepared.src;if(!p.src)throw Error('Cold reader activation is prohibited');++window.__evidenceLocateCounters.navigation;
          ReferenceWorkspace.selectPage(1,p.id).catch(error=>__evidenceAsyncNavigationErrors.push(error.message));
          const current=ReferenceWorkspace.active(1);if(current!==p||current.sourceId!==document.sourceHash)throw Error('Synchronous warm reader activation failed');
          window.__evidenceLocated={document,region};const [x,y,w,h]=region,points=[[x,y],[x+w,y],[x+w,y+h],[x,y+h]].map(p=>feUlImgToMm(current,...p));
          ++window.__evidenceLocateCounters.fit;feFit([Math.min(...points.map(p=>p[0])),Math.min(...points.map(p=>p[1])),Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))]);++window.__evidenceLocateCounters.paint;drawFaceEditor();return {ok:true};
        }
      });
      if(!reuseController||!window.__evidenceController)window.__evidenceController=EvidenceLinks.createController({getStamp,readCurrent,
        readFeatureAttachment:kind=>kind===EvidenceLinks.KIND?structuredClone(__evidenceBackend):null,
        setFeatureAttachment:(kind,value,token)=>{++window.__evidenceWriteCalls;if(window.__evidenceRejectWrite)throw Error('Injected shared busy rejection');if(kind!==EvidenceLinks.KIND||token!==getStamp().contextToken)throw Error('Stale injected attachment write');EvidenceLinks.validate(value);window.__evidenceBackend=structuredClone(value);++window.__evidenceAnnotationRevision;},
        locateDocument:locator
      });
      window.__evidenceUI=EvidenceLinksUI.mount(document.getElementById('refRecordDetails'),{controller:{...__evidenceController,add(input){++window.__evidenceAddCalls;return __evidenceController.add(input);}},getStamp,readSelection,canvas:{svg:document.getElementById('faceEditorSvg'),layer:()=>document.getElementById('faceEditorRoot'),eventPoint:fePoint,toPage:p=>feUlMmToImg(ReferenceWorkspace.active(1),...p),fromPage:p=>feUlImgToMm(ReferenceWorkspace.active(1),...p),pageIdentity:()=>{const p=ReferenceWorkspace.active(1);return p&&[p.id,p.sourceId,p.page,p.rot,p.crop,p.x,p.y,p.mmPerPx];}}});
      await __evidenceUI.refresh();
    },reuseController);await page.locator(expectRejected?'[data-evidence-error]':'[data-evidence-target]').waitFor();
  }
  async function selectRegion(rect=[30,40,70,50]){
    await page.locator('[data-evidence-select]').click();
    if(page.viewportSize().width<=680)await page.evaluate(()=>closePanels());
    const points=await page.evaluate(([x,y,w,h])=>{const p=ReferenceWorkspace.active(1),root=document.getElementById('faceEditorRoot'),svg=document.getElementById('faceEditorSvg');return [[x,y],[x+w,y+h]].map(v=>{const mm=feUlImgToMm(p,...v),q=svg.createSVGPoint();q.x=mm[0];q.y=mm[1];const r=q.matrixTransform(root.getScreenCTM());return {x:r.x,y:r.y};});},rect);
    await page.mouse.move(points[0].x,points[0].y);await page.mouse.down();await page.mouse.move(points[1].x,points[1].y,{steps:5});await page.mouse.up();
    await page.waitForFunction(()=>!!__evidenceUI.snapshot().region&&!__evidenceUI.snapshot().selecting);
    if(page.viewportSize().width<=680)await page.evaluate(()=>openPanel('right',document.getElementById('workspaceToggleRight')));
    return page.evaluate(()=>__evidenceUI.snapshot().region);
  }
  async function saveObservation(){
    await page.locator('[data-evidence-target]').selectOption('0:0');
    await page.locator('[data-evidence-input="drawing-text"]').fill('<img src=x onerror=window.__unsafe=true> drawing');
    await page.locator('[data-evidence-input="drawing-value"]').fill('457.5');await page.locator('[data-evidence-input="drawing-unit"]').selectOption('mm');
    await page.locator('[data-evidence-input="measurement-value"]').fill('458.25');await page.locator('[data-evidence-input="measurement-unit"]').selectOption('mm');
    const count=await page.evaluate(()=>__evidenceBackend.links.length);await page.locator('[data-evidence-save]').click();await page.waitForFunction(n=>__evidenceBackend.links.length===n+1,count);await page.waitForFunction(()=>document.querySelectorAll('[data-evidence-id]').length===__evidenceBackend.links.length);
  }
  async function delayedLocator(mode){
    const beforeNative=await native();
    if(mode==='hash')await page.evaluate(async bytes=>{const source=await ReferenceWorkspace.sourceFromFile(new File([new Uint8Array(bytes)],'authored-evidence.pdf',{type:'application/pdf'}));__evidenceSources.set(source.meta.id,source);window.__evidenceReplacement=source;},Array.from(fixture(true)));
    await page.evaluate(async mode=>{const p=ReferenceWorkspace.group(1).pages.find(p=>p.id===__evidenceBackend.links.at(-1).document.referencePageId);window.__evidenceLocatorOriginal={id:p.id,sourceId:p.sourceId,src:p.src,cold:mode==='cancel'};if(__evidenceLocatorOriginal.cold)delete p.src;let release,enteredResolve;window.__evidenceLocatorHold={promise:new Promise(r=>release=r),entered:new Promise(r=>enteredResolve=r),release:()=>release(),enteredResolve:()=>enteredResolve()};window.__evidenceLocatorPending=__evidenceController.locate(__evidenceBackend.links.at(-1).evidenceId).then(()=>({ok:true}),error=>({ok:false,code:error.code}));await __evidenceLocatorHold.entered;},mode);
    const preparationWasDetached=await page.evaluate(()=>{const p=ReferenceWorkspace.group(1).pages.find(p=>p.id===__evidenceLocatorOriginal.id);return !__evidenceLocatorOriginal.cold||!Object.hasOwn(p,'src');});
    await page.evaluate(async mode=>{if(mode==='cancel')__evidenceController.cancel();else if(mode==='hash'){const p=ReferenceWorkspace.group(1).pages.find(p=>p.id===__evidenceLocatorOriginal.id);if(__evidenceReplacement.meta.hash===p.sourceId||!feChangeUnderlay(1,p,{sourceId:__evidenceReplacement.meta.hash},true))throw Error('Unable to replace recorded source identity');}else if(mode==='basis'){const p=ReferenceWorkspace.active(1);if(!feChangeUnderlay(1,p,{rot:(p.rot+90)%360},true))throw Error('Unable to change live source basis');}else if(mode==='camera'){fe.panX+=37;fe.panY-=19;fe.zoom*=1.1;feApply();}else if(mode==='page')await ReferenceWorkspace.selectPage(1,__evidenceBackend.links[0].document.referencePageId);},mode);
    const afterInput=await page.evaluate(()=>({counts:JSON.stringify(__evidenceLocateCounters),active:ReferenceWorkspace.active(1).id,camera:[fe.panX,fe.panY,fe.zoom],backend:JSON.stringify(__evidenceBackend)}));
    const result=await page.evaluate(async()=>{const hold=__evidenceLocatorHold;window.__evidenceLocatorHold=null;hold.release();return await __evidenceLocatorPending;});
    check(`delayed locator ${mode} supersession performs zero navigation fit or paint`,preparationWasDetached&&result.ok===false&&result.code==='EVIDENCE_STALE'&&await page.evaluate(old=>{const p=ReferenceWorkspace.group(1).pages.find(p=>p.id===__evidenceLocatorOriginal.id);return JSON.stringify(__evidenceLocateCounters)===old.counts&&ReferenceWorkspace.active(1).id===old.active&&JSON.stringify([fe.panX,fe.panY,fe.zoom])===JSON.stringify(old.camera)&&JSON.stringify(__evidenceBackend)===old.backend&&(!__evidenceLocatorOriginal.cold||!Object.hasOwn(p,'src'));},afterInput));assert.deepEqual(await native(),beforeNative);
    // Cleanup follows every no-navigation assertion, outside the canceled job.
    await page.evaluate(async()=>{const original=__evidenceLocatorOriginal,p=ReferenceWorkspace.group(1).pages.find(p=>p.id===original.id);if(p.sourceId!==original.sourceId&&!feChangeUnderlay(1,p,{sourceId:original.sourceId},true))throw Error('Unable to restore original recorded source');if(original.cold){p.src=original.src;await ReferenceWorkspace.selectPage(1,original.id);if(ReferenceWorkspace.active(1)!==p||oc.underlays[1]!==p)throw Error('Cold fixture restoration did not restore current underlay');}window.__evidenceLocatorOriginal=null;});
  }
  try{
    // This independent adapter gate deliberately supplies its own backend.
    // The separate formal integration gate loads the production adapter/store.
    await page.route('**/evidence-links-app.js',route=>route.fulfill({contentType:'application/javascript',body:'/* isolated EvidenceLinksUI adapter harness */'}));
    await page.goto(url);await page.waitForFunction(()=>typeof connection!=='undefined'&&connection.phase==='ready');
    check('page identity, meaningful app, and no framework overlay',/幾何|Geometry|工程|物件/.test(await page.title())&&(await page.locator('body').innerText()).length>100&&await page.locator('nextjs-portal,vite-error-overlay').count()===0);
    await page.addScriptTag({path:path.join(__dirname,'evidence-links.js')});await page.addScriptTag({path:path.join(__dirname,'evidence-links-ui.js')});
    await page.evaluate(async()=>{await ReferenceWorkspace.newProject();const r=await apiRequest('line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000');if(!r.ok)throw Error(r.error);await renderObjects();await enterFocus('face',1);});await parameter();
    for(const type of ['image/png','image/jpeg']){
      const beforeImage=await native();await page.evaluate(async type=>{const canvas=document.createElement('canvas');canvas.width=320;canvas.height=240;const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,320,240);ctx.strokeRect(30,40,70,50);ctx.fillStyle='black';ctx.fillText('Authored image rejection fixture',20,20);const blob=await new Promise(resolve=>canvas.toBlob(resolve,type));const source=await ReferenceWorkspace.sourceFromFile(new File([blob],'authored-rejected.'+(type==='image/png'?'png':'jpg'),{type}));window.__evidenceSources=window.__evidenceSources||new Map();__evidenceSources.set(source.meta.id,source);await ReferenceWorkspace.openSource(source,1);},type);await page.waitForFunction(()=>!document.getElementById('refApply').disabled);await page.locator('#refApply').click();await page.waitForFunction(()=>!document.getElementById('referenceDialog').open);await mount(false,true);
      check(`${type} actual app source is rejected before controller add or attachment write`,await page.evaluate(type=>{const p=ReferenceWorkspace.active(1),source=__evidenceSources.get(p.sourceId);let rejected=false;try{EvidenceLinks.documentFromReference(p,source);}catch(e){rejected=e.code==='EVIDENCE_DOCUMENT';}return source.meta.type===type&&rejected&&__evidenceAddCalls===0&&__evidenceWriteCalls===0&&__evidenceBackend.links.length===0&&!document.querySelector('[data-evidence-save]');},type));assert.deepEqual(await native(),beforeImage);
    }
    for(let number=1;number<=4;++number){
      await importPage(number);const dims=await page.evaluate(async()=>{const p=ReferenceWorkspace.active(1),render=await ReferenceWorkspace.renderPage(__evidenceSource,p.page),pdf=await (await ReferenceWorkspace.documentFor(__evidenceSource)).getPage(p.page),viewport=pdf.getViewport({scale:1});return {img:[p.imgW,p.imgH],render:[render.width,render.height],viewport:[viewport.width,viewport.height],rotation:pdf.rotate};});
      check(`real PDF page ${number} intrinsic rotation ${(number-1)*90} uses existing scale1 dimensions`,dims.rotation===(number-1)*90&&JSON.stringify(dims.img)===JSON.stringify(dims.viewport)&&JSON.stringify(dims.render)===JSON.stringify(dims.viewport));
      for(const [rotation,zoom]of [[0,.14],[90,.28],[180,.22],[270,.2]]){
        await page.evaluate(({rotation,zoom})=>{const p=ReferenceWorkspace.active(1);feChangeUnderlay(1,p,{rot:rotation,crop:[10,15,p.imgW-20,p.imgH-30]},true);drawFaceEditor();ReferenceWorkspace.fitReference();fe.zoom=zoom;const svg=document.getElementById('faceEditorSvg'),mm=feUlImgToMm(p,65,65);fe.panX=svg.clientWidth/2-mm[0]*zoom;fe.panY=svg.clientHeight/2-mm[1]*zoom;feApplyZoom();document.getElementById('refRecordDetails').open=true;},{rotation,zoom});
        await mount();const before=await native(),rect=await selectRegion();check(`page ${number}, display rotation ${rotation}, crop and zoom preserve full original rect at DPR2`,rect.every((n,i)=>Math.abs(n-[30,40,70,50][i])<1e-3));
        if(number===1&&rotation===0){const stayed=await page.evaluate(()=>{const old=JSON.stringify(__evidenceUI.snapshot().region);fe.zoom*=1.25;fe.panX+=17;fe.panY-=11;feApply();const polygon=document.querySelector('[data-evidence-region]'),points=polygon.points,rect=__evidenceUI.snapshot().region,p=ReferenceWorkspace.active(1),mm=feUlImgToMm(p,rect[0],rect[1]);const a=document.getElementById('faceEditorSvg').createSVGPoint();a.x=points[0].x;a.y=points[0].y;const screen=a.matrixTransform(polygon.getScreenCTM());const b=document.getElementById('faceEditorSvg').createSVGPoint();b.x=mm[0];b.y=mm[1];const expected=b.matrixTransform(document.getElementById('faceEditorRoot').getScreenCTM());const sameScreen=Math.abs(screen.x-expected.x)<1e-6&&Math.abs(screen.y-expected.y)<1e-6;feApplyZoom();__evidenceUI.redraw();return sameScreen&&document.querySelector('[data-evidence-region]')?.parentNode.id==='faceEditorRoot'&&JSON.stringify(__evidenceUI.snapshot().region)===old;});check('selected evidence overlay follows existing layer pan and zoom and redraw without changing original rect',stayed);}
        await saveObservation();assert.deepEqual(await native(),before);check(`manual add is annotation only for page ${number}, rotation ${rotation}`,true);
      }
    }
    check('drawing measurement and current native model are separate and safe text',await page.evaluate(()=>{const last=document.querySelector('[data-evidence-id]:last-child');return last.querySelector('[data-evidence-value="drawing"]').textContent.includes('457.5 mm')&&last.querySelector('[data-evidence-value="measurement"]').textContent.includes('458.25 mm')&&last.querySelector('[data-evidence-value="model"]').textContent==='915/2 mm'&&!window.__unsafe&&!last.querySelector('img');}));
    const beforeReview=await native();await page.locator('[data-evidence-reviewed]').last().check();await page.waitForFunction(()=>__evidenceBackend.links.at(-1).humanConfirmation!==null);assert.deepEqual(await native(),beforeReview);check('human review writes confirmation without a native mutation',true);
    const sourceStatus=await page.evaluate(async()=>{const previous=await __evidenceController.readView();await ReferenceWorkspace.selectPage(1,__evidenceBackend.links[0].document.referencePageId);const current=await __evidenceController.readView();return current.links.every((l,i)=>l.status===previous.links[i].status)&&current.links.at(-1).status==='confirmed-content';});check('ordinary active page switch preserves saved source identity and current confirmation',sourceStatus);
    await mount(true);const beforeLocate=await native();await page.evaluate(()=>{const p=ReferenceWorkspace.group(1).pages.find(p=>p.id===__evidenceBackend.links.at(-1).document.referencePageId);delete p.src;window.__evidenceColdSuccessCounts={...__evidenceLocateCounters};});await page.locator('[data-evidence-locate]').last().click();await page.waitForFunction(()=>window.__evidenceLocated?.document.page===4&&ReferenceWorkspace.active(1)?.page===4);assert.deepEqual(await native(),beforeLocate);check('detached cold PDF preparation adopts only in synchronous reader navigation fit and paint without native mutation',await page.evaluate(()=>!!ReferenceWorkspace.active(1).src&&JSON.stringify(__evidenceLocated.region)===JSON.stringify(__evidenceBackend.links.at(-1).region)&&['navigation','fit','paint'].every(k=>__evidenceLocateCounters[k]===__evidenceColdSuccessCounts[k]+1)));await mount(true);
    for(const mode of ['cancel','hash','basis','camera','page'])await delayedLocator(mode);
    for(const bad of ['source','page','dimensions']){const before=await native(),result=await page.evaluate(async bad=>{const counts=JSON.stringify(__evidenceLocateCounters),active=ReferenceWorkspace.active(1).id,camera=JSON.stringify([fe.panX,fe.panY,fe.zoom]),p=ReferenceWorkspace.group(1).pages.find(p=>p.id===__evidenceBackend.links.at(-1).document.referencePageId),src=p.src;delete p.src;window.__evidenceBadPrepared=bad;let rejected=false;try{await __evidenceController.locate(__evidenceBackend.links.at(-1).evidenceId);}catch(e){rejected=e.code==='EVIDENCE_DOCUMENT';}finally{window.__evidenceBadPrepared=null;}const unchanged=!Object.hasOwn(p,'src')&&JSON.stringify(__evidenceLocateCounters)===counts&&ReferenceWorkspace.active(1).id===active&&JSON.stringify([fe.panX,fe.panY,fe.zoom])===camera;p.src=src;return rejected&&unchanged;},bad);check(`wrong detached ${bad} cannot activate reader fit or paint`,result);assert.deepEqual(await native(),before);}await mount(true);
    await page.locator('[data-evidence-id]').last().scrollIntoViewIfNeeded();await page.screenshot({path:path.join(output,'desktop.png')});
    // Recreated controller simulates a new archive context: no durable lease.
    await mount();check('reopened identical typed IDs retain observations but require explicit reassociation',await page.locator('[data-evidence-status="needs-reassociation"]').count()>0&&await page.locator('[data-evidence-reviewed]').last().isDisabled());
    await page.locator('[data-evidence-rebind-target]').last().selectOption('0:0');await page.locator('[data-evidence-rebind]').last().click();await page.waitForFunction(()=>!document.querySelector('[data-evidence-id]:last-child [data-evidence-reviewed]').disabled);check('explicit field zero reassociation grants a new local review without automatic confirmation',await page.locator('[data-evidence-status="unchecked"]').count()===1&&await page.locator('[data-evidence-reviewed]').last().isChecked()===false);
    const rejectedBefore=await native();await page.evaluate(()=>window.__evidenceRejectWrite=true);await page.locator('[data-evidence-reviewed]').last().check();await page.locator('[data-evidence-message]').filter({hasText:'Injected shared busy rejection'}).waitFor();check('rejected annotation review restores unchecked control and persisted confirmation stays null',await page.locator('[data-evidence-reviewed]').last().isChecked()===false&&await page.evaluate(()=>__evidenceBackend.links.at(-1).humanConfirmation===null));assert.deepEqual(await native(),rejectedBefore);await page.evaluate(()=>window.__evidenceRejectWrite=false);
    await parameter('457.5',true);await parameter();await page.evaluate(()=>__evidenceUI.refresh());check('actual delete and same-name same-ID recreation is unknown despite same native definition',await page.locator('[data-evidence-status="needs-reassociation"]').count()>0&&await page.locator('[data-evidence-reviewed]').last().isDisabled());
    // Hold both actual native read adapters until cancel; neither may repaint.
    await page.evaluate(()=>{let resolve;window.__evidenceHold={promise:new Promise(r=>resolve=r),resolve:()=>resolve()};window.__evidencePending=__evidenceUI.refresh();__evidenceUI.cancel();});
    const cancelled=await page.locator('[data-evidence-message]').textContent();await page.evaluate(async()=>{const h=__evidenceHold;window.__evidenceHold=null;h.resolve();await __evidencePending;});
    check('cancelled late native reads do not repaint or write annotations',await page.locator('[data-evidence-message]').textContent()===cancelled&&await page.evaluate(()=>__evidenceBackend.links.length===16));
    // Late source-page read loses its page identity even when project token stays.
    await page.evaluate(()=>{let resolve;window.__evidenceHold={promise:new Promise(r=>resolve=r),resolve:()=>resolve()};window.__evidencePending=__evidenceUI.refresh();});
    await importPage(1,true);await page.evaluate(async()=>{const h=__evidenceHold;window.__evidenceHold=null;h.resolve();await __evidencePending;const id=__evidenceBackend.links.at(-1).document.referencePageId;await ReferenceWorkspace.selectPage(1,id);const p=ReferenceWorkspace.active(1);feChangeUnderlay(1,p,{sourceId:__evidenceSource.meta.hash},true);await ReferenceWorkspace.preparePage(p,__evidenceSource);drawFaceEditor();document.getElementById('refRecordDetails').open=true;});
    check('same filename with changed original source bytes cannot reuse confirmation',await page.evaluate(()=>__evidenceBackend.links.every(l=>l.document.sourceHash!==__evidenceSource.meta.hash)));
    await mount();check('recorded source replacement requires review and keeps conflicting observations',await page.locator('[data-evidence-status="source-changed"]').count()===4&&await page.locator('[data-evidence-reviewed]:disabled').count()===16);
    const closure=await page.evaluate(async()=>{const p=ReferenceWorkspace.active(1),graph=await apiRequest('source-inspect'),link={...__evidenceBackend.links[0],evidenceId:'closure-original',document:EvidenceLinks.documentFromReference(p,__evidenceSources.get(p.sourceId)),target:EvidenceLinks.targetFromNode(ReferenceWorkspace.getProjectState().id,graph.nodes.find(n=>n.kind==='parameter-field')),humanConfirmation:null};const v={schema:EvidenceLinks.SCHEMA,links:[link]};let missing=false,wrongBytes=false;
      const hooks={readSource:()=>__evidenceSource,hashBytes:GeometryProject.sha,readPage:async(s,n)=>{const r=await ReferenceWorkspace.renderPage(s,n);return {width:r.width,height:r.height};}};
      await EvidenceLinks.validateSourceClosure(v,hooks);try{await EvidenceLinks.validateSourceClosure(v,{...hooks,readSource:()=>null});}catch(e){missing=e.code==='EVIDENCE_SOURCE_CLOSURE';}try{await EvidenceLinks.validateSourceClosure(v,{...hooks,hashBytes:async()=> '0'.repeat(64)});}catch(e){wrongBytes=e.code==='EVIDENCE_SOURCE_CLOSURE';}return missing&&wrongBytes;});
    check('original self-authored PDF byte and real page closure accepts complete and rejects missing or changed bytes',closure);
    const rejectedRegion=await selectRegion();await page.locator('[data-evidence-target]').selectOption('0:0');await page.locator('[data-evidence-input="drawing-value"]').fill('457.5');const beforeRejectedAdd=await native();await page.evaluate(()=>window.__evidenceRejectWrite=true);await page.locator('[data-evidence-save]').click();await page.locator('[data-evidence-message]').filter({hasText:'Injected shared busy rejection'}).waitFor();check('rejected add retains exact transient raw input and selected region without committing',await page.locator('[data-evidence-input="drawing-value"]').inputValue()==='457.5'&&await page.evaluate(rect=>JSON.stringify(__evidenceUI.snapshot().region)===JSON.stringify(rect)&&__evidenceBackend.links.length===16,rejectedRegion));assert.deepEqual(await native(),beforeRejectedAdd);await page.evaluate(()=>window.__evidenceRejectWrite=false);await page.locator('[data-evidence-cancel]').click();
    await selectRegion();await page.locator('[data-evidence-target]').selectOption('0:0');await page.locator('[data-evidence-input="drawing-value"]').fill('cancelled 459');
    const beforeCancel=await native();await page.evaluate(()=>{let resolve;window.__evidenceHold={promise:new Promise(r=>resolve=r),resolve:()=>resolve()};});await page.locator('[data-evidence-save]').click();await page.locator('[data-evidence-cancel]').click();await page.evaluate(async()=>{const hold=__evidenceHold;window.__evidenceHold=null;hold.resolve();});await page.waitForTimeout(100);
    check('cancelled late creation cannot commit annotations and controls recover',await page.evaluate(()=>__evidenceBackend.links.length===16)&&await page.locator('[data-evidence-input="drawing-value"]').isEnabled());assert.deepEqual(await native(),beforeCancel);
    await page.setViewportSize({width:390,height:844});await page.evaluate(()=>{openPanel('right',document.getElementById('workspaceToggleRight'));document.getElementById('refRecordDetails').open=true;});
    const mobileBefore=await native();await page.evaluate(()=>{const p=ReferenceWorkspace.active(1),svg=document.getElementById('faceEditorSvg'),mm=feUlImgToMm(p,65,65);fe.zoom=.12;fe.panX=svg.clientWidth/2-mm[0]*fe.zoom;fe.panY=svg.clientHeight/2-mm[1]*fe.zoom;feApplyZoom();__evidenceUI.redraw();});const mobileRect=await selectRegion();check('actual 390px canvas selection uses original region at DPR2',mobileRect.every((n,i)=>Math.abs(n-[30,40,70,50][i])<1e-3));await saveObservation();assert.deepEqual(await native(),mobileBefore);check('390px field-zero controls save manual evidence without changing native model',true);
    await page.locator('[data-evidence-id]').last().scrollIntoViewIfNeeded();await page.screenshot({path:path.join(output,'mobile.png')});check('390px merged reference disclosure stays inside viewport',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1&&[...document.querySelectorAll('[data-evidence-links] input,[data-evidence-links] select')].every(n=>n.getBoundingClientRect().width<=390)));
    const oldContext=await page.evaluate(()=>ReferenceWorkspace.getProjectState().contextToken),oldBackend=await page.evaluate(()=>JSON.stringify(__evidenceBackend));await page.evaluate(()=>{let resolve;window.__evidenceHold={promise:new Promise(r=>resolve=r),resolve:()=>resolve()};window.__evidencePending=__evidenceUI.refresh();});await page.evaluate(()=>ReferenceWorkspace.newProject());const switched=await native();await page.evaluate(async()=>{const hold=__evidenceHold;window.__evidenceHold=null;hold.resolve();await __evidencePending;});check('late native reads after an actual project switch cannot repaint or write old evidence',await page.evaluate(({oldContext,oldBackend})=>ReferenceWorkspace.getProjectState().contextToken!==oldContext&&JSON.stringify(__evidenceBackend)===oldBackend&&!document.querySelector('[data-evidence-links]'),{oldContext,oldBackend}));assert.deepEqual(await native(),switched);
    check('browser console uncaught exceptions and synchronous navigation shim stay clean',errors.length===0&&await page.evaluate(()=>__evidenceAsyncNavigationErrors.length===0));
    console.log(JSON.stringify({passed,url,viewports:['1280x900 DPR2','390x844 DPR2'],attachmentBackend:'injected-memory; ZIP integration pending shared owner',screenshots:output}));
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
