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
    await eval_(`(async()=>{EngineeringWorkspace.close();resetSceneFocus();const bytes=await GeometryProject.pack(${JSON.stringify(scene)},{projectId:'public-source-navigation',name:'公開來源定位測例',sources:[],faces:[]},new Map(),fflate);await ReferenceWorkspace.importBytes(bytes,'public-source-navigation.gcanvas');await setView3(${view3},{persistPositions:false});await renderObjects({persistPositions:false});${open?"await enterFocus('face',1,{placementId:10});fiShowTab('prop');":"selectObject('boundary',1);"}SourceInspectorApp.sync();if(innerWidth<=680)openPanel('right',$(${JSON.stringify(open?'workspaceToggleRight':'toggleRight')}));})()`);
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
    else await eval_(`(async()=>{for(const line of ${JSON.stringify(mode==='reuse'?['delete timber 7','timber 7 29 35 role boundary','place 7 on 10 at-face e0 +u +n']:['delete timber 7'])}){let r=await api('line '+line);if(r.preview?.valid)r=await api('line confirm '+r.preview.token);if(!r.ok)throw Error(JSON.stringify(r));}})()`);
    await eval_(`window.__p85Gate.restore();window.__p85Gate.release();`);await sleep(200);
    check(mode+' late source result never selects a stale/reused ID or switches placement',await eval_(`oc.focus?.placementId===10&&fe.sel===null`));
    if(mode==='cancel')check('cancelled read preserves World and project state',JSON.stringify(await snapshot())===JSON.stringify(before));
    if(mode==='page')await eval_(`ReferenceWorkspace.context().groups.delete('p85-test')`);
  }
  check('source navigation has no new browser exceptions',exceptionCount()===errors);
};
