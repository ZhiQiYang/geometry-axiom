/* Real app/Chromium/native F1a slice. Run only against an isolated test service. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const url=process.env.GEOMETRY_TEST_URL;
if(!url||!process.env.GEOMETRY_FEEDBACK_DIR?.startsWith('/tmp/'))throw Error('Explicit isolated GEOMETRY_TEST_URL and /tmp feedback directory required');
const output=process.env.GEOMETRY_SOURCE_TEST_DIR||'/tmp/geometry-f1a/browser';fs.mkdirSync(output,{recursive:true});
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];let passed=0;
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('dialog',d=>d.accept());
  const check=(name,value)=>{assert.equal(value,true,name);passed++;console.log('PASS '+name);};
  const state=()=>page.evaluate(async()=>({scene:(await apiRequest('dump')).text,project:ReferenceWorkspace.getProjectState(),frame:ReferenceWorkspace.history.frame,undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,models:JSON.stringify(ReferenceWorkspace.getSpaceModels(),(k,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v)}));
  const open=async(host='#inspectorContent')=>{const details=page.locator(host+' [data-source-inspector]');await details.locator('summary').click();await details.locator('[data-source-body]').filter({hasText:'未試算'}).waitFor();return details;};
  try{
    await page.goto(url);await page.waitForFunction(()=>window.SourceInspectorApp&&connection.phase==='ready');
    check('app identity and meaningful first viewport',/幾何|Geometry|geometry|工程|物件|應用/.test(await page.title())&&(await page.locator('body').innerText()).length>100);
    await page.evaluate(async()=>{await ReferenceWorkspace.newProject();for(const cmd of ['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000','timber 0 27 33 role boundary','place 0 on 1 at-face e0 +u +n']){const r=await apiRequest('line '+cmd);if(!r.ok)throw Error(JSON.stringify(r));}await renderObjects();selectObject('boundary',1);});
    const before=await state();let detail=await open();
    check('selected face uses existing inspector with native relationships',await detail.getByText('修改可能涉及（未試算）',{exact:true}).isVisible()&&(await detail.innerText()).includes('timber:0'));
    assert.deepEqual(await state(),before);check('readonly inspection preserves dump dirty revision history and models',true);
    await detail.locator('[data-source-path="timber:0"]').click();
    check('bounded path expansion displays ID0 with actual native endpoints without asserting global continuity',(await detail.innerText()).includes('timber:0')&&await detail.locator('[data-source-support-status="exact"]').count()===2&&(await detail.innerText()).includes('物件延續性仍未知'));
    await page.screenshot({path:path.join(output,'desktop.png')});
    await detail.locator('[data-source-path="placement:1"]').click();
    await detail.locator('[data-source-locate="timber:0"]').click();await page.waitForFunction(()=>oc.edit?.bid===1&&fe.sel?.kind==='timber'&&fe.sel.id===0);
    check('actual ID0 source navigation selects timber and preserves core history dirty',(await state()).scene===before.scene&&(await state()).undo===before.undo&&(await state()).project.dirty===before.project.dirty);
    detail=await open('#faceInspectorContent');
    await page.evaluate(async()=>{const r=await apiRequest('line spec readonly_guard 13');if(!r.ok)throw Error(r.error);});
    await detail.locator('[data-source-path="placement:1"]').click();
    check('stale path expansion refuses to repaint captured native relationships',(await detail.innerText()).includes('來源已變更，請重新檢查')&&await detail.locator('[data-source-support-status="exact"]').count()===0);
    // Build one real saved model through the established source/preview/create flow.
    await page.evaluate(async()=>{selectObject('boundary',1);await enterFocus('face',1);});
    await page.evaluate(()=>SpaceModelWorkspace.openCurrentFace());await page.waitForFunction(()=>SpaceModelWorkspace.snapshot().phase==='ready');
    await page.evaluate(()=>ReferenceWorkspace.setFaceProjection(1,1,{kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'}));
    await page.locator('#smBottom').fill('0');
    await page.locator('#smPreview').click();await page.waitForFunction(()=>SpaceModelWorkspace.snapshot().phase==='preview');
    await page.locator('#smConfirmFaces').check();await page.locator('#smCreate').click();await page.waitForFunction(()=>ReferenceWorkspace.getSpaceModels().length===1);
    await page.locator('#smLibrary').click();let model=await open('#smLibraryList');
    check('saved real model content matches with identity honestly unknown',await model.locator('[data-source-freshness="unknown"]').isVisible()&&(await model.innerText()).includes('內容一致'));
    const saved=await state();await model.locator('summary').click();check('cancelling readonly details preserves saved model',(await state()).models===saved.models);
    // Actual archive save/reopen uses existing format and source snapshots.
    await page.evaluate(async()=>{window.__f1aArchive=Array.from(await ReferenceWorkspace.exportBytes());await ReferenceWorkspace.importBytes(new Uint8Array(__f1aArchive),'f1a-reopen');});
    await page.evaluate(()=>SpaceModelWorkspace.openLibrary());model=await open('#smLibraryList');
    check('save/reopen retains content evidence without inventing durable lineage',(await model.innerText()).includes('物件延續性未知'));
    // Hold an actual native snapshot response to test UI cancellation and project switch.
    let captured=deferred(),release=deferred();
    await page.route('**/sources/snapshot',async route=>{const response=await route.fetch();captured.resolve();await release.promise;try{await route.fulfill({response});}catch(e){/* browser cancelled this readonly request */}});
    await model.locator('[data-source-refresh]').click();await captured.promise;await model.locator('summary').click();release.resolve();await page.waitForTimeout(100);
    check('late real response after cancellation cannot repaint closed inspector',(await model.locator('[data-source-body]').textContent())==='尚未檢查'&&(await state()).models===saved.models);
    captured=deferred();release=deferred();await model.locator('summary').click();await captured.promise;
    const oldContext=await page.evaluate(()=>ReferenceWorkspace.context().id);await page.evaluate(()=>ReferenceWorkspace.newProject());release.resolve();await page.waitForTimeout(100);
    check('late real response after project switch cannot paint or alter new project',await page.evaluate(old=>ReferenceWorkspace.context().id!==old&&ReferenceWorkspace.getSpaceModels().length===0&&!document.querySelector('[data-source-freshness]'),oldContext));
    await page.unroute('**/sources/snapshot');
    await page.evaluate(async()=>{await ReferenceWorkspace.importBytes(new Uint8Array(__f1aArchive),'f1a-after-late');SpaceModelWorkspace.openLibrary();});model=await open('#smLibraryList');
    captured=deferred();release=deferred();
    await page.route('**/sources/snapshot',async route=>{const response=await route.fetch();captured.resolve();await release.promise;try{await route.fulfill({response});}catch(e){}});
    await model.locator('[data-source-refresh]').click();await captured.promise;
    await page.evaluate(async()=>{const r=await apiRequest('line spec unrelated 20');if(!r.ok)throw Error(r.error);});release.resolve();
    await model.locator('[data-source-body]').filter({hasText:/來源已更新|來源已變更/}).waitFor();
    check('actual source revision change rejects held native response',(await model.innerText()).includes('重新檢查')&&(await state()).models===saved.models);
    await page.unroute('**/sources/snapshot');
    await page.evaluate(async()=>{const r=await apiRequest('line spec unrelated 19');if(!r.ok)throw Error(r.error);});
    await model.locator('[data-source-refresh]').click();await page.waitForFunction(()=>document.querySelector('[data-source-freshness]')?.textContent.includes('內容一致'));
    check('unrelated native definition does not stale saved model',(await model.innerText()).includes('內容一致'));
    await page.evaluate(async()=>{let r=await apiRequest('line preview placement 1 on boundary 1 origin 0 0 2600 u +x v +y');if(!r.preview?.valid)throw Error(JSON.stringify(r));r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(r.error);});
    await model.locator('[data-source-refresh]').click();await model.locator('[data-source-freshness="changed"]').waitFor();
    check('actual relevant source update marks model changed without recompute',(await state()).models===saved.models&&(await model.innerText()).includes('模型保持原快照'));
    await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(output,'mobile.png')});
    check('390px disclosure and lists stay within horizontal viewport',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await page.evaluate(async()=>{for(const cmd of ['delete timber 0','delete placement 1']){let r=await apiRequest('line '+cmd);if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(r.error);}});
    await model.locator('[data-source-refresh]').click();await model.locator('[data-source-freshness="missing"]').waitFor();
    check('actual deleted source stays missing and does not rebuild saved model',(await state()).models===saved.models&&(await model.innerText()).includes('來源缺失'));
    await page.setViewportSize({width:1280,height:900});
    await page.evaluate(async()=>{SpaceModelWorkspace.close();if(oc.focus)leaveFocus();
      const r=await apiRequest('engineering-read'),request={schema:'engineering-transaction/1',expectedRevision:r.revision,operations:[{op:'put-parameter',value:{id:0,name:'Zero',fields:[{id:0,name:'pitch',type:'dimension',input:'600'}]}}]};
      const p=await (await fetch('/engineering/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request)})).json();if(!p.preview?.valid)throw Error(JSON.stringify(p));const c=await apiRequest('engineering-confirm '+p.preview.token);if(!c.ok)throw Error(c.error);await renderObjects();selectObject('parameter',0);});
    detail=await open();const parameterBefore=await state();
    check('parameter usage consolidates into one existing inspector and retains export delete',await page.locator('#inspectorContent [data-source-inspector]').count()===1&&await detail.locator('#paramExport').count()===1&&await detail.locator('#paramDelete').count()===1);
    await detail.locator('[data-source-locate="parameter-field:0:f0"]').click();
    await page.waitForFunction(()=>oc.sel?.kind==='parameter'&&oc.sel.id===0&&document.activeElement.closest('[data-param-field]')?.dataset.paramField==='0');
    check('actual native parameter field zero navigation preserves definitions and history',(await state()).scene===parameterBefore.scene&&(await state()).undo===parameterBefore.undo);
    // Actual three-member assembly; source support ID0 remains covered above,
    // while this existing finite generator requires positive selected support IDs.
    await page.evaluate(async()=>{
      await ReferenceWorkspace.newProject();for(const cmd of ['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
        'timber 90 20 20 role boundary','place 90 on 1 at-face e0 +u +n','timber 91 20 20 role boundary','place 91 on 1 at-face e2 +u +n',
        'spec pos1 500','guide 1 1 v spec:pos1','spec pos2 2500','guide 2 1 v spec:pos2','spec pos3 1500','guide 3 1 u spec:pos3']){let r=await apiRequest('line '+cmd);if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(JSON.stringify(r));}
      const rule={id:1,version:1,name:'native support source',slots:[{id:1,name:'主支'},{id:2,name:'副支'}],members:[{id:1,slotId:1},{id:2,slotId:1},{id:3,slotId:2}],joints:[
        {id:1,kind:'end-to-side',scope:'left',terminatedMember:3,targetMember:1,end:'start',side:'+u',dir:'u'},
        {id:2,kind:'end-to-side',scope:'right',terminatedMember:3,targetMember:2,end:'finish',side:'-u',dir:'u'}]};
      const binding={id:1,name:'native material',rule:{id:1,version:1},slots:[1,2].map(slotId=>({slotId,A:{kind:'literal',value:27},B:{kind:'literal',value:33},contactFace:'A',orientation:'A'}))};
      async function apply(url,schema,operations){const read=await apiRequest('assembly-read'),r=await (await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema,expectedRevision:read.revision,operations})})).json();if(!r.preview?.valid)throw Error(JSON.stringify(r));const c=await apiRequest('assembly-confirm '+r.preview.token);if(!c.ok)throw Error(JSON.stringify(c));}
      await apply('/assembly/preview','assembly-transaction/1',[{op:'publish-rule',value:rule},{op:'create-binding',value:binding}]);
      const state=(await apiRequest('assembly-read')).state,source={id:1,name:'three native members',bindingId:1,rule:{id:1,version:1,fingerprint:state.rules[0].fingerprint},surfaceId:1,members:[1,2,3].map(memberId=>({memberId,role:memberId<3?'primary':'secondary',guideId:memberId,dir:memberId<3?'+v':'+u',depthSide:'+n',ends:memberId<3?{start:{kind:'timber',id:91},finish:{kind:'timber',id:90}}:{start:{kind:'member',memberId:1},finish:{kind:'member',memberId:2}}}))};
      await apply('/assembly/generate-preview','assembly-generation-transaction/1',[{op:'create-instance',value:source,expectedBindingFingerprint:state.bindings[0].fingerprint}]);
      const instance=(await apiRequest('assembly-read')).state.instances[0];window.__f1aOwnedTimber=instance.members.find(m=>m.memberId===3).timberId;
      await renderObjects();selectObject('boundary',1);await enterFocus('face',1);await feLoadGuides();feSelectTimber(__f1aOwnedTimber);
    });
    detail=await open('#faceInspectorContent');const ownedBefore=await state();
    check('actual owned endpoints display B0 B1 exact member owner and fixed rule versions',(await detail.innerText()).includes('／B0')&&(await detail.innerText()).includes('／B1')&&(await detail.innerText()).includes('member 1')&&(await detail.innerText()).includes('member 2')&&(await detail.innerText()).includes('規則 1 固定 v1')&&await detail.locator('[data-source-support-status="exact"]').count()===2);
    assert.deepEqual(await state(),ownedBefore);check('owned source disclosure is readonly in actual World and history',true);
    await page.screenshot({path:path.join(output,'owned-support-desktop.png')});await page.setViewportSize({width:390,height:844});await page.evaluate(()=>openPanel('right',$('workspaceToggleRight')));
    check('390px owned support disclosure remains accessible and does not overflow',await detail.locator('[data-source-support-status="exact"]').first().isVisible()&&await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await page.screenshot({path:path.join(output,'owned-support-390.png')});await page.setViewportSize({width:1280,height:900});
    await page.evaluate(()=>{window.__f1aOriginalApi=apiRequest;window.__f1aBlobCount=0;window.__f1aOriginalBlob=URL.createObjectURL;URL.createObjectURL=function(...args){__f1aBlobCount++;return __f1aOriginalBlob.apply(this,args);};});
    try{
      for(const mutation of ['instanceFingerprint','memberId','ruleVersion','missingTimber','surface','staleHash']){
        await page.evaluate(mutation=>{apiRequest=async function(command,...args){const result=await __f1aOriginalApi(command,...args);if(command!=='source-inspect')return result;const data=structuredClone(result),entry=data.timberSupports.entries.find(e=>e.id===__f1aOwnedTimber),r=entry.start.relation;
          if(mutation==='missingTimber')r.source.id=999999;else if(mutation==='surface')entry.surface=0;else if(mutation==='staleHash')data.timberSupports.sourceFingerprint='a'.repeat(64);else r.owner[mutation]=mutation==='instanceFingerprint'?'a'.repeat(64):999999;return data;};},mutation);
        await detail.locator('[data-source-refresh]').click();await detail.locator('[data-source-body]').filter({hasText:/無法核對|版本不一致/}).waitFor();
        check('corrupt native support '+mutation+' refuses confirmed presentation and creates no Blob',await detail.locator('[data-source-support-status="exact"]').count()===0&&await page.evaluate(()=>__f1aBlobCount===0));
        assert.deepEqual(await state(),ownedBefore);
      }
      await page.evaluate(()=>{apiRequest=__f1aOriginalApi;});await detail.locator('[data-source-refresh]').click();await detail.locator('[data-source-support-status="exact"]').first().waitFor();
      check('restoring authoritative data restores endpoint display without mutation or export',await detail.locator('[data-source-support-status="exact"]').count()===2&&await page.evaluate(()=>__f1aBlobCount===0));
    }finally{await page.evaluate(()=>{apiRequest=__f1aOriginalApi;URL.createObjectURL=__f1aOriginalBlob;delete window.__f1aOriginalApi;delete window.__f1aOriginalBlob;});}
    check('no relevant console or page errors',errors.length===0);
    console.log(JSON.stringify({passed,failed:0,url,viewports:[1280,390],browser:'Chromium/Playwright; Browser plugin unavailable',screenshots:output}));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
