/* #47 support slice: plugin for the existing isolated CDP/Playwright harness.
 * The integration owner loads timber-supports.js after timber-schedule.js and
 * adds timberSupports to references; no shared app implementation is changed. */
const cdp=require('./cdp_helpers.js'),fs=require('fs'),path=require('path'),os=require('os');
module.exports=async function({send,eval_,sleep,click,waitForUI,exceptionCount}){
  console.log('=== P81. 原生角材支撐來源與局部面 ===');
  const check=cdp.makeCheck({prefix:'support ',throwOnFail:true}),errors=exceptionCount();
  const out=process.env.GEOMETRY_SUPPORT_SCREENSHOT_DIR||path.join(os.tmpdir(),'geometry-support-screens-'+process.pid);
  if(!path.isAbsolute(out))throw Error('Use an isolated absolute screenshot directory');
  fs.mkdirSync(out,{recursive:true});
  const ctl=async selector=>{
    const p=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing control');e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,hit:e.contains(document.elementFromPoint(x,y))};})()`);
    if(!p.hit)throw Error('Support control is covered: '+selector);
    await click(p.x,p.y);await sleep(100);
  };
  const snapshot=()=>eval_(`(async()=>({dump:(await api('dump')).text,dirty:ReferenceWorkspace.context().dirty,undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length}))()`);
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  await eval_(`(async()=>{resetSceneFocus();const r=await fetch('/examples/assembly-generation-v1.gcanvas');if(!r.ok)throw Error('Example unavailable');await ReferenceWorkspace.importBytes(new Uint8Array(await r.arrayBuffer()),'support.gcanvas');await renderObjects();await enterFocus('face',1);})()`);
  await waitForUI(`!!$('timberScheduleCSV')&&!$('timberScheduleCSV').disabled`);
  check('native support projection and schedule share one formal source fingerprint',await eval_(`(()=>{const s=feTimberScheduleSnapshot(),r=fe.timberReferenceData;return r.timberSupports.schema==='native-timber-supports/1'&&s.sourceFingerprint===r.timberSupports.sourceFingerprint&&s.rows.length===5&&new Set(s.ids).size===5&&s.rows.filter(x=>x.assembly).length===3;})()`));
  const id=await eval_(`feTimberScheduleSnapshot().rows.find(r=>r.assembly?.memberId===3).id`);
  check('secondary start and finish identify actual owned member local faces',await eval_(`(()=>{const r=feTimberScheduleSnapshot().rows.find(r=>r.id===${id});return r.supports.start.relation.localFace==='B0'&&r.supports.start.relation.owner.memberId===1&&r.supports.finish.relation.localFace==='B1'&&r.supports.finish.relation.owner.memberId===2&&r.L===1973;})()`));
  check('existing source details display support identities and local faces',await eval_(`(()=>{const e=document.querySelector('[data-timber-id="${id}"] .timber-schedule-source p');return e.textContent.includes('起端：角材')&&e.textContent.includes('B0')&&e.textContent.includes('末端：角材')&&e.textContent.includes('B1')&&!e.textContent.includes('支撐身分未提供');})()`));
  const before=await snapshot();
  await ctl(`[data-schedule-timber="${id}"]`);
  check('existing list selection still locates the exact native member',await eval_(`fe.timberSelection.has(${id})&&document.querySelector('[data-schedule-timber="${id}"]').getAttribute('aria-pressed')==='true'`));
  await ctl(`[data-timber-id="${id}"] .timber-schedule-source summary`);
  await eval_(`window.__supportBlob=null;window.__supportURL=URL.createObjectURL;URL.createObjectURL=b=>{window.__supportBlob=b;return __supportURL.call(URL,b);};`);
  await ctl('#timberScheduleCSV');await waitForUI(`!!window.__supportBlob`);
  check('actual CSV export contains exact support provenance and fixed native source versions',await eval_(`(async()=>{const csv=await __supportBlob.text(),s=feTimberScheduleSnapshot();return csv.includes('start_support_provenance')&&csv.includes('finish_support_provenance')&&csv.includes('instanceFingerprint')&&csv.includes('B0')&&csv.includes(s.sourceFingerprint)&&csv.includes('"1973"');})()`));
  check('selection, source details and CSV export preserve World, dirty and history',JSON.stringify(before)===JSON.stringify(await snapshot()));
  // Corrupt only the received projection, retaining its real native fingerprint.
  // The existing export handler must reject before constructing any CSV Blob.
  await eval_(`window.__supportOriginalReferences=fe.timberReferenceData;`);
  for(const [name,mutation] of [
    ['false instance fingerprint',`e.owner.instanceFingerprint='e'.repeat(64)`],
    ['false supporting member',`e.start.relation.owner.memberId=999`],
    ['false supporting rule version',`e.start.relation.owner.ruleVersion=999`],
    ['nonexistent supporting timber',`e.start.relation.source.id=4294967295`],
  ]){
    await eval_(`(()=>{const r=JSON.parse(JSON.stringify(__supportOriginalReferences)),e=r.timberSupports.entries.find(x=>x.id===${id});${mutation};fe.timberReferenceData=r;window.__supportBlob=null;})()`);
    await ctl('#timberScheduleCSV');
    check('actual CSV rejects '+name+' before Blob creation',await eval_(`window.__supportBlob===null`));
    await eval_(`fe.timberReferenceData=__supportOriginalReferences;`);
  }
  await eval_(`URL.createObjectURL=__supportURL;void 0`);
  await waitForUI(`!document.querySelector('#toastRegion .toast')`,6000);
  await eval_(`document.querySelector('[data-timber-id="${id}"] .timber-schedule-source p').scrollIntoView({block:'start'});`);
  await sleep(100);
  fs.writeFileSync(path.join(out,'support-desktop.png'),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'));
  await eval_(`(async()=>{window.__supportRows=JSON.stringify(feTimberScheduleSnapshot().rows);const bytes=await ReferenceWorkspace.exportBytes();await ReferenceWorkspace.importBytes(bytes,'support-reopened.gcanvas');await renderObjects();await enterFocus('face',1);})()`);
  check('real gcanvas export and reimport retain identical row provenance',await eval_(`JSON.stringify(feTimberScheduleSnapshot().rows)===__supportRows`));
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await eval_(`openPanel('left',$('workspaceToggleLeft'));`);await sleep(100);
  await ctl(`[data-schedule-timber="${id}"]`);
  await ctl(`[data-timber-id="${id}"] .timber-schedule-source summary`);
  check('390px exposes the same local support faces in existing details',await eval_(`fe.timberSelection.has(${id})&&document.querySelector('[data-timber-id="${id}"] .timber-schedule-source').open&&document.querySelector('[data-timber-id="${id}"] .timber-schedule-source p').textContent.includes('B0')`));
  check('390px has no horizontal overflow',await eval_(`document.documentElement.scrollWidth<=innerWidth`));
  await waitForUI(`!document.querySelector('#toastRegion .toast')`,6000);
  await eval_(`document.querySelector('[data-timber-id="${id}"] .timber-schedule-source p').scrollIntoView({block:'start'});`);
  await sleep(100);
  fs.writeFileSync(path.join(out,'support-mobile.png'),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'));
  check('support flow has no new browser exceptions',exceptionCount()===errors);
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
};
