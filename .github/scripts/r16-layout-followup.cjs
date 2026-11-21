'use strict';
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {spawn} = require('node:child_process');
const {createHash} = require('node:crypto');
const {setTimeout: sleep} = require('node:timers/promises');

async function main() {
  const out = process.env.R16_OBSERVATIONS;
  const source = fs.readFileSync('geometry-web/workspace_height_test.js', 'utf8');
  const digest = createHash('sha256').update(source).digest('hex');
  if (digest !== 'd212a41d6ce516703b2996211d118626542ef663250efb84dfbc16a8dd135489') throw Error('Incorrect probe source');
  function between(start,end) {
    const p=source.indexOf(start),q=source.indexOf(end,p+start.length);
    if(p<0||q<0||source.indexOf(start,p+1)>=0) throw Error('Unrecognized source bounds: '+start);
    return source.slice(p,q);
  }
  const probeSource = between('  const sizes = [','  async function measure(');
  const fixtureSource = between('  await viewport({width:1400,height:900});\n  await read(`(async()=>{for(const d','  await matrix(\'main\'');
  const fitStart=fixtureSource.lastIndexOf("  await ctl('#btnZoom');");
  if(fitStart<0)throw Error('Unrecognized initial fit call');
  const survey = new (Object.getPrototypeOf(async()=>{}).constructor)('send','eval_','click','sleep','waitForUI','kind','emit','event',probeSource+fixtureSource.slice(0,fitStart)+`
    let label=kind, selector, controls, initialFit=null;
    try{await ctl('#btnZoom');}catch(error){initialFit=String(error);}

    if(kind==='main'){selector='#ocv'; controls=rootControls;}
    if(kind==='face'){await ctl('.ocard[data-kind="boundary"][data-id="1"] .card-enter'); await waitForUI("oc.focus?.t==='face'&&fe.tool==='select'");selector='#faceEditorSvg';controls=faceControls;}
    if(kind==='space-plan'||kind==='space-projection'){await ctl('.ocard[data-kind="space"][data-id="1"] .card-enter');await waitForUI("oc.focus?.t==='space'");await ctl('#spaceStageTabs [data-ss-tab="'+(kind==='space-plan'?'plan':'proj')+'"]');selector=kind==='space-plan'?'#spacePlanSvg':'#spaceProjSvg';controls=kind==='space-plan'?spaceControls:projectionControls;}
    if(kind==='three-view'){await ctl('#btnObj');await waitForUI('view3===true');selector='#cv';controls=viewControls;}
    if(kind==='full-grid'){await ctl('#btnNewGridSystem');await waitForUI("document.querySelector('#infiniteGridWorkspace')?.open&&!!document.querySelector('#igGridView')");selector='#igGridView';controls=gridControls;}
    if(kind==='3d'){await ctl('#btnSpaceModelTrial');await waitForUI("document.querySelector('#smWorkspace')?.open&&SpaceModelWorkspace.snapshot().phase==='preview'&&!SpaceModelWorkspace.snapshot().stale");selector='#smCanvas';controls=modelControls;}
    event('workspace-entry',{kind,initialFit});
    for(const size of sizes.slice(0,3)){
      await viewport(size);
      if(kind==='3d'&&await shown('#smTabPreview'))await ctl('#smTabPreview');
      if(kind==='full-grid')await read("document.querySelector('#igGridView').scrollIntoView({block:'start',inline:'nearest'});void 0");
      await settle();
      const p=await call(surfaceProbe,selector), minimum=size.height-(size.width<=560?128:88);
      event('canvas',{kind,size,width:p.clipped?.width,height:p.clipped?.height,minimum,viewport:p.viewport,occluding:p.obstructions?.map(o=>o.id||o.className)});
      const observations=[];
      for(const query of controls){
        const control=await point(query);
        if(control.points){
          control.hitTargets=await call((points)=>points.map(({x,y})=>document.elementsFromPoint(x,y).slice(0,5).map(n=>({id:n.id,tag:n.tagName,classes:n.getAttribute('class'),text:(n.getAttribute('aria-label')||n.textContent||'').trim().slice(0,55)}))),control.points);
        }
        observations.push(control);event('control',{kind,size,selector:query,reachable:control.reachable,rect:control.rect,top:control.hitTargets?.map(t=>t[0])});
      }
      emit({kind,label,initialFit,requested:size,minimum,surface:p,controls:observations});
    }`);
  fs.mkdirSync(out,{recursive:true});const chosen=process.argv[2];
  if(!['main','face','space-plan','space-projection','three-view','full-grid','3d'].includes(chosen))throw Error('Unknown selected workspace');
  const log=path.join(out,chosen+'-measurements.jsonl');
  const event=(stage,more={})=>{const line={at:new Date().toISOString(),stage,...more}; console.log(JSON.stringify(line));fs.appendFileSync(path.join(out,chosen+'-events.jsonl'),JSON.stringify(line)+'\n');};
  event('start',{chosen});
  const emit=r=>{if(r.error)console.log(JSON.stringify(r));fs.appendFileSync(log,JSON.stringify(r)+'\n');};
  const stderr=fs.openSync(path.join(out,'chrome-'+chosen+'.stderr'),'w');
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'r16-layout-survey-'));
  const chrome=spawn(process.env.GEOMETRY_CHROME,['--headless=new','--disable-gpu','--no-first-run','--no-sandbox','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{stdio:['ignore','ignore',stderr]});
  let ws;
  try{
    const portFile=path.join(profile,'DevToolsActivePort');
    for(let i=0;i<150&&!fs.existsSync(portFile);i++){if(chrome.exitCode!==null)throw Error('Chrome exited '+chrome.exitCode);await sleep(100);}
    const port=fs.readFileSync(portFile,'utf8').split('\n')[0];
    const tabs=await (await fetch('http://127.0.0.1:'+port+'/json/list')).json();
    ws=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);
    await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
    let id=0;const pending=new Map();
    ws.addEventListener('message',event=>{const m=JSON.parse(event.data);if(m.method==='Page.javascriptDialogOpening'){event('dialog',{kind:m.params.type,text:m.params.message});if(m.params.type==='beforeunload')send('Page.handleJavaScriptDialog',{accept:true}).catch(()=>{});}if(!pending.has(m.id))return;const [resolve,reject,timer]=pending.get(m.id);clearTimeout(timer);pending.delete(m.id);if(m.error)reject(Error(JSON.stringify(m.error)));else resolve(m.result);});
    function send(method,params={}){return new Promise((resolve,reject)=>{const n=++id;const timer=setTimeout(()=>{pending.delete(n);reject(Error('CDP method timeout: '+method+' '+(params.expression||'').slice(0,160)));},9000);pending.set(n,[resolve,reject,timer]);ws.send(JSON.stringify({id:n,method,params}));});}
    async function eval_(expression){const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;}
    async function click(x,y){await send('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',clickCount:1});await send('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',clickCount:1});}
    async function waitForUI(expression){const start=Date.now();while(Date.now()-start<30000){try{if(await eval_(expression))return;}catch{}await sleep(120);}throw Error('Timed out waiting for '+expression);}
    await send('Page.enable');let blocked=0;
    for(const kind of [chosen]){
      try{
        await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
        event('new-profile',{kind,version:process.env.R16_CHROME_VERSION});
        await send('Page.navigate',{url:process.env.GEOMETRY_TEST_URL});
        await waitForUI("typeof api==='function'&&typeof oc==='object'&&connection.phase==='ready'");
        event('app-ready',{kind});await survey(send,eval_,click,sleep,waitForUI,kind,emit,event);
      }catch(error){blocked++;emit({kind,error:String(error)});}
    }
    const rows=fs.readFileSync(log,'utf8').trim().split('\n').map(JSON.parse);
    const summary=rows.map(r=>r.error?{kind:r.kind,error:r.error}:{kind:r.kind,width:r.requested.width,height:r.requested.height,canvasHeight:r.surface.clipped?.height,canvasWidth:r.surface.clipped?.width,minimum:r.minimum,obstructions:r.surface.obstructions?.map(o=>o.id||o.className),missedSurfaceSamples:r.surface.samples?.filter(x=>!x.hit).length,unreachable:r.controls.filter(x=>!x.reachable).map(x=>x.selector),missingName:r.controls.filter(x=>!x.name).map(x=>x.selector)});
    fs.writeFileSync(path.join(out,chosen+'-summary.json'),JSON.stringify({schema:'r16-independent-layout-observation/1',source:process.env.SOURCE_SHA,probeSha256:digest,blocked,summary},null,2)+'\n');
    console.log(JSON.stringify(summary));
    if(blocked||summary.length!==3||summary.some(r=>r.canvasHeight<r.minimum||r.missedSurfaceSamples||r.obstructions?.length||r.unreachable?.length||r.missingName?.length))process.exitCode=1;
  }finally{if(ws)ws.close();chrome.kill('SIGTERM');fs.closeSync(stderr);}
}
main().catch(e=>{console.error(e);process.exitCode=2;});
