/* P2: real source-inspector controls, public native World fixture. Loaded by
 * the aggregate CDP harness; screenshots and asynchronous gates stay in TEMP. */
const fs=require('fs'),path=require('path'),os=require('os'),cdp=require('./cdp_helpers.js');
module.exports=async function({send,eval_,sleep,click,waitForUI,exceptionCount}){
  console.log('=== P85. 原生來源定位保留承載面身分 ===');
  const check=cdp.makeCheck({prefix:'source-navigation ',throwOnFail:true}),errors=exceptionCount();
  const fixture=fs.readFileSync(path.join(__dirname,'../_p2_source_navigation.scene'),'utf8');
  const out=process.env.GEOMETRY_SOURCE_NAVIGATION_SCREENSHOT_DIR||path.join(os.tmpdir(),'geometry-source-navigation-'+process.pid);
  fs.mkdirSync(out,{recursive:true});
  const ctl=async selector=>{
    const p=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing source control');e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,hit:e.contains(document.elementFromPoint(x,y))};})()`);
    if(!p.hit)throw Error('Covered source control: '+selector);
    await click(p.x,p.y);await sleep(100);
  };
  const snapshot=()=>eval_(`(async()=>({dump:(await api('dump')).text,dirty:ReferenceWorkspace.context().dirty,project:ReferenceWorkspace.getProjectState(),history:{undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,frame:ReferenceWorkspace.history.frame}}))()`);
  async function setup({open=false,zero=false,view3=false}={}){
    const scene=zero?fixture.replaceAll('placement 20','placement 0').replaceAll('timber 7','timber 0').replaceAll('place 7 on 20','place 0 on 0'):fixture;
    await eval_(`(async()=>{SpaceModelWorkspace.close();EngineeringWorkspace.close();resetSceneFocus();const bytes=await GeometryProject.pack(${JSON.stringify(scene)},{projectId:'public-source-navigation',name:'公開來源定位測例',sources:[],faces:[]},new Map(),fflate);await ReferenceWorkspace.importBytes(bytes,'public-source-navigation.gcanvas');await setView3(${view3},{persistPositions:false});await renderObjects({persistPositions:false});${open?"await enterFocus('face',1,{placementId:10});fiShowTab('prop');":"selectObject('boundary',1);"}SourceInspectorApp.sync();if(innerWidth<=680)openPanel('right',$(${JSON.stringify(open?'workspaceToggleRight':'toggleRight')}));})()`);
    const root=open?'#faceInspectorContent':'#inspectorContent';
    await ctl(root+' [data-source-inspector] summary');
    const selector=root+` [data-source-locate="timber:${zero?0:7}"]`;
    await waitForUI(`!!document.querySelector(${JSON.stringify(selector)})`);
    return selector;
  }
  for(const [name,options,width] of [['canvas',{},1400],['open10',{open:true},1400],['zero',{open:true,zero:true},1400],['mobile',{open:true},390]]){
    await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width===390});
    const selector=await setup(options),before=await snapshot(),pid=options.zero?0:20,tid=options.zero?0:7;
    if(name==='canvas')check('native graph retains timber7 → placement20 → boundary1',await eval_(`(async()=>{const g=await apiRequest('source-inspect');return g.edges.some(e=>e.from==='timber:7'&&e.to==='placement:20'&&e.active&&e.field==='surface')&&g.edges.some(e=>e.from==='placement:20'&&e.to==='boundary:1'&&e.active&&e.field==='boundary');})()`));
    await ctl(selector);
    await waitForUI(`oc.focus?.placementId===${pid}&&fe.sel?.kind==='timber'&&fe.sel.id===${tid}`);
    check(name+' opens the native placement and selects its actual timber',await eval_(`(async()=>{const r=await apiRequest('references'),t=r.timbers.find(t=>t.id===${tid});return oc.focus?.t==='face'&&oc.focus.id===1&&feSid(1)===${pid}&&t.geometry.surface===${pid}&&fe.timberSelection.has(${tid})&&document.querySelector('[data-schedule-timber="${tid}"]')?.getAttribute('aria-pressed')==='true'&&!$('objectWorkspace').hidden;})()`));
    check(name+' navigation preserves World, dirty, project revision and history',JSON.stringify(await snapshot())===JSON.stringify(before));
    fs.writeFileSync(path.join(out,name+'.png'),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'));
  }
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  // Hold an actual native read, then close its source details or move the page.
  // No geometry result is fabricated: this exercises late-response ownership.
  for(const mode of ['cancel','page','reuse','missing']){
    const selector=await setup({open:true}),before=await snapshot();
    await eval_(`(()=>{const original=apiRequest,g=window.__p85Gate={held:false};const gate=new Promise(resolve=>g.release=resolve);g.restore=()=>apiRequest=original;apiRequest=async(...args)=>{const r=await original(...args);if(args[0]==='source-inspect'&&!g.held){g.held=true;await gate;}return r;};})()`);
    const p=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
    await click(p.x,p.y);await waitForUI(`window.__p85Gate.held`);
    if(mode==='cancel')await ctl('#faceInspectorContent [data-source-inspector] summary');
    else if(mode==='page')await eval_(`ReferenceWorkspace.context().groups.set('p85-test',{activePageId:'changed',pages:[]})`);
    else await eval_(`(async()=>{for(const line of ${JSON.stringify(mode==='reuse'?['delete timber 7','timber 7 29 35 role boundary','place 7 on 10 at-face e0 +u +n']:['delete timber 7'])}){let r=await apiRequest('line '+line);if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(JSON.stringify(r));}})()`);
    await eval_(`window.__p85Gate.restore();window.__p85Gate.release();`);await sleep(200);
    check(mode+' late source result never selects a stale/reused ID or switches placement',await eval_(`oc.focus?.placementId===10&&fe.sel===null`));
    if(mode==='cancel')check('cancelled read preserves World and project state',JSON.stringify(await snapshot())===JSON.stringify(before));
    if(mode==='page')await eval_(`ReferenceWorkspace.context().groups.delete('p85-test')`);
  }
  // An embedded rectangular placement has a real canvas card and no boundary
  // relation. Locate that typed card through the existing timber's source UI.
  await setup();
  await eval_(`(async()=>{resetSceneFocus();const scene='surface 0 origin 0 0 2500 u +x v +y rect 0 0 4000 3000\\nsurface 1 origin 18000 0 2500 u +x v +y rect 0 0 4000 3000\\ntimber 0 27 33 role boundary\\nplace 0 on 0 at-face e0 +u +n\\n';const bytes=await GeometryProject.pack(scene,{projectId:'embedded-placement',name:'公開矩形承載面',sources:[],faces:[]},new Map(),fflate);await ReferenceWorkspace.importBytes(bytes,'embedded.gcanvas');await renderObjects({persistPositions:false});selectObject('placement',1);centerOnNode('placement',1);const input={mode:'plan',base_scene:(await api('dump')).text,placement_id:0,obstacles:[],settings:{bottom:0,height:3000,edges:[0,1,2,3],floor:'boundary',ceiling:'boundary',holes:'none',wall_thickness:null}};const response=await fetch('/model/space-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)}),result=await response.json();if(!result.ok)throw Error(JSON.stringify(result));ReferenceWorkspace.addSpaceModel({id:'embedded-source',name:'embedded-source',created_at:new Date().toISOString(),source:{kind:'scene',placement_id:0,boundary_id:null,scene_hash:result.source_sha256},input,result});SpaceModelWorkspace.openLibrary();SourceInspectorApp.sync();})()`);
  const embeddedRoot='#smLibraryList [data-source-inspector]';
  await ctl(embeddedRoot+' summary');
  await waitForUI(`!!document.querySelector(${JSON.stringify(embeddedRoot+' [data-source-path="timber:0"]')})`);
  await ctl(embeddedRoot+' [data-source-path="timber:0"]');
  if(!await eval_(`oc.sel?.kind==='placement'&&oc.sel.id===1`))throw Error('Embedded oracle must begin at the other placement');
  const embeddedBefore=await snapshot();
  await eval_(`(()=>{const original=EngineeringAdapter.navigateObject,g=window.__p85Embedded={done:false,error:null};EngineeringAdapter.navigateObject=async(...args)=>{try{return await original(...args);}catch(e){g.error=e.message;throw e;}finally{g.done=true;EngineeringAdapter.navigateObject=original;}};})()`);
  await ctl(embeddedRoot+' [data-source-locate="placement:0"]');await waitForUI(`window.__p85Embedded.done`);
  check('native boundaryless placement0 changes selection, centers its card and completes without error',await eval_(`(async()=>{const g=await apiRequest('source-inspect'),card=document.querySelector('.ocard[data-kind="placement"][data-id="0"] rect'),c=card?.getBoundingClientRect(),v=ocv.getBoundingClientRect();return __p85Embedded.error===null&&!g.edges.some(e=>e.from==='placement:0'&&e.field==='boundary')&&oc.focus===null&&oc.sel.kind==='placement'&&oc.sel.id===0&&!!c&&Math.abs(c.x+c.width/2-(v.x+v.width/2))<8&&Math.abs(c.y+c.height/2-(v.y+v.height/2))<8;})()`),await eval_(`({sel:oc.sel,error:__p85Embedded.error,card:document.querySelector('.ocard[data-kind="placement"][data-id="0"] rect')?.getBoundingClientRect().toJSON(),viewport:ocv.getBoundingClientRect().toJSON(),pan:[oc.panX,oc.panY],zoom:oc.zoom})`));
  check('embedded placement navigation preserves World and project state',JSON.stringify(await snapshot())===JSON.stringify(embeddedBefore));
  for(const stage of ['render','final'])for(const action of ['collapse','close','switch']){
    await setup({open:true});
    const holdLibrary = stage === "render" && action === "collapse";
    await eval_(`(async()=>{const input={mode:'plan',base_scene:(await api('dump')).text,placement_id:20,obstacles:[],settings:{bottom:0,height:3000,edges:[0,1,2,3],floor:'boundary',ceiling:'boundary',holes:'none',wall_thickness:null}};const response=await fetch('/model/space-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)});const result=await response.json();if(!result.ok)throw Error(JSON.stringify(result));for(const id of ['p85-a','p85-b'])ReferenceWorkspace.addSpaceModel({id,name:id,created_at:new Date().toISOString(),source:{kind:'scene',placement_id:20,boundary_id:1,scene_hash:result.source_sha256},input,result});if(${holdLibrary}){await SectionProfileWorkspace.refreshLibrary();const original=apiRequest,g=window.__p85Library={held:false,refreshed:false};const gate=new Promise(resolve=>g.release=resolve);g.restore=()=>apiRequest=original;apiRequest=async(...args)=>{const r=await original(...args);if(args[0]==="section-profile-read"&&!g.held){g.held=true;await gate;}return r;};window.addEventListener("section-profile-library-changed",()=>g.refreshed=true,{once:true});}SpaceModelWorkspace.openLibrary();SourceInspectorApp.sync();})()`);
    if (holdLibrary) await waitForUI(`window.__p85Library.held`);
    const selector='[data-sm-open-model="p85-a"]',root='#smLibraryList .sm-model-card:first-child [data-source-inspector]';
    await ctl(root+' summary');await waitForUI(`!!document.querySelector(${JSON.stringify(root+' [data-source-locate="timber:7"]')})`);
    if (holdLibrary) {
      const beforeRefresh = await snapshot(), modelsBefore = await eval_(`JSON.stringify(ReferenceWorkspace.getSpaceModels())`);
      await eval_(`(()=>{const g=__p85Library;g.cards=[...document.querySelectorAll("#smLibraryList [data-sm-open-model]")].map(b=>({id:b.dataset.smOpenModel,card:b.closest(".sm-model-card")}));g.detail=g.cards[0].card.querySelector("[data-source-inspector]");g.focus=document.activeElement;g.restore();g.release();})()`);
      await waitForUI(`window.__p85Library.refreshed`);
      check("late profile read preserves both same-source model cards and the open source inspector",await eval_(`(()=>{const g=__p85Library,buttons=[...document.querySelectorAll("#smLibraryList [data-sm-open-model]")];return g.cards.length===2&&buttons.length===2&&g.cards.every((r,i)=>r.id===buttons[i].dataset.smOpenModel&&r.card===buttons[i].closest(".sm-model-card")&&r.card.isConnected)&&g.detail===g.cards[0].card.querySelector("[data-source-inspector]")&&g.detail.isConnected&&g.detail.open&&!!g.detail.querySelector('[data-source-locate="timber:7"]')&&document.activeElement===g.focus;})()`));
      check("late profile read preserves World, complete saved models, dirty, project revision and history",JSON.stringify(await snapshot())===JSON.stringify(beforeRefresh)&&await eval_(`JSON.stringify(ReferenceWorkspace.getSpaceModels())`)===modelsBefore);
    }
    const before=await snapshot();
    await eval_(`(()=>{const originalRead=apiRequest,originalRender=renderObjects,g=window.__p85Late={held:false,count:0};const gate=new Promise(resolve=>g.release=resolve);g.restore=()=>{apiRequest=originalRead;renderObjects=originalRender;};apiRequest=async(...args)=>{const r=await originalRead(...args);if(args[0]==='source-inspect'&&++g.count===4&&${JSON.stringify(stage)}==='final'){g.held=true;await gate;}return r;};renderObjects=async(...args)=>{const r=await originalRender(...args);if(${JSON.stringify(stage)}==='render'&&!g.held){g.held=true;await gate;}return r;};})()`);
    await ctl(root+' [data-source-locate="timber:7"]');await waitForUI(`window.__p85Late.held`);
    await ctl(action==='collapse'?root+' summary':action==='close'?'#smClose':'[data-sm-open-model="p85-b"]');
    await eval_(`window.__p85Late.restore();window.__p85Late.release();`);await sleep(200);
    check(stage+'/'+action+' explicitly cancelled saved-model owner cannot enter/select the late target',await eval_(`fe.sel?.id!==7&&${stage==='render'?"oc.focus===null":"oc.focus?.placementId===20"}`));
    check(stage+'/'+action+' cancellation preserves World, dirty and history',JSON.stringify(await snapshot())===JSON.stringify(before));
  }
  await eval_(`SpaceModelWorkspace.close()`);
  check('source navigation has no new browser exceptions',exceptionCount()===errors);
};
