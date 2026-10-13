/* Run the unchanged P78 module alone with real Chromium/CDP controls.
 * Playwright supplies the owned browser transport, not replacement UI tests.
 * Browser plugin not available in the diagnostic cloud environment.
 */
'use strict';
const fs=require('node:fs'), path=require('node:path'), crypto=require('node:crypto');
const {chromium}=require('playwright');
const root=path.resolve(process.env.P78_SOURCE_ROOT||path.join(__dirname,'../..'));
const cdp=require(path.join(root,'geometry-web/cdp_helpers.js'));
const {createRetainedEvaluator}=require(path.join(root,'geometry-web/cdp_evaluation.js'));
const [url,out,rateText,mode='full']=process.argv.slice(2), rate=Number(rateText);
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const sink=fs.createWriteStream(path.join(out,'browser.jsonl'),{flags:'wx'});
const emit=(event,data={})=>sink.write(JSON.stringify({event,hostEpochMs:Date.now(),hostMonoNs:process.hrtime.bigint().toString(),...data})+'\n');
const delay=ms=>new Promise(r=>setTimeout(r,ms));

function instrument(source) {
  function replace(a,b){if(source.split(a).length!==2)throw Error('Instrumentation anchor not unique: '+a);source=source.replace(a,b);}
  replace("let disposed=false,serial=0", "const instance=++window.__p78Instances;let disposed=false,serial=0");
  replace("pending=true;const seq=++serial;clearTimeout(timer);timer=setTimeout(async()=>{try{const r=await options.query(",
    "pending=true;const seq=++serial;window.__p78({event:'candidate.scheduled',instance,seq,key,queryRect,command});clearTimeout(timer);timer=setTimeout(async()=>{try{window.__p78Current={instance,seq,key};window.__p78({event:'candidate.query',instance,seq,serial,disposed});const r=await options.query(");
  replace("if(disposed||seq!==serial||!options.current())return;",
    "window.__p78({event:'candidate.return',instance,seq,serial,disposed,ok:r.ok,error:r.error});if(disposed||seq!==serial||!options.current())return;");
  replace("error=e.message;}finally", "error=e.message;window.__p78({event:'candidate.error',instance,seq,serial,error});}finally");
  replace("pending=false;options.redraw();}}},180)",
    "pending=false;window.__p78({event:'candidate.finally',instance,seq,serial,error});options.redraw();}}},180)");
  replace("section.dataset.trialState=pending?'pending':error?'error':'ready';",
    "section.dataset.trialState=pending?'pending':error?'error':'ready';window.__p78({event:'trial.render',instance,serial,pending,error,state:section.dataset.trialState});");
  return source;
}

async function main(){
  const original=fs.readFileSync(path.join(root,'geometry-web/grid-trial.js'),'utf8');
  const observed=instrument(original);
  fs.writeFileSync(path.join(out,'served-grid-trial.js'),observed);
  emit('instrumentation',{originalSha256:sha(original),servedSha256:sha(observed),rate,mode});
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true});
  const context=await browser.newContext({viewport:{width:1400,height:1000}});
  const page=await context.newPage(), session=await context.newCDPSession(page);
  let exceptions=0, checks=0, failures=0, passed=false, fatal=null;
  const oldLog=console.log;
  console.log=(...args)=>{oldLog(...args);if(args[1]==='✓')checks++;if(args[1]==='✗')failures++;};
  page.on('console',m=>emit('console',{type:m.type(),text:m.text()}));
  page.on('pageerror',e=>{exceptions++;emit('page.exception',{message:e.message,stack:e.stack});});
  await page.exposeBinding('__p78Sink',(_,row)=>emit('browser',row));
  await page.route(/\/grid-trial\.js(?:\?.*)?$/,route=>route.fulfill({body:observed,contentType:'text/javascript'}));
  await page.addInitScript(()=>{
    window.__p78Instances=0;window.__p78Current=null;let request=0;
    window.__p78=row=>window.__p78Sink({browserMs:performance.now(),epochMs:performance.timeOrigin+performance.now(),...row});
    const realFetch=window.fetch;
    window.fetch=function(input,options){
      let cmd;try{cmd=JSON.parse(options?.body||'{}').cmd;}catch{}
      if(!cmd)return realFetch.apply(this,arguments);
      const rid='p78-'+(++request), candidate=cmd.startsWith('grid-trial-query ')?window.__p78Current:null;
      const fields={rid,cmd,candidate};
      window.__p78({event:'fetch.begin',...fields,stack:new Error().stack});
      options={...options,headers:new Headers(options.headers)};
      options.headers.set('X-P78-Request-ID',rid);
      options.signal?.addEventListener('abort',()=>window.__p78({event:'fetch.signal.abort',...fields,reason:{name:options.signal.reason?.name,message:options.signal.reason?.message},stack:new Error().stack}),{once:true});
      return realFetch.call(this,input,options).then(r=>{window.__p78({event:'fetch.headers',...fields,status:r.status});return r;},e=>{window.__p78({event:'fetch.reject',...fields,name:e.name,message:e.message,stack:e.stack});throw e;});
    };
    const originalTimeout=AbortSignal.timeout;
    AbortSignal.timeout=function(ms){const signal=originalTimeout.call(this,ms);window.__p78({event:'abort.timer.created',ms,stack:new Error().stack});return signal;};
  });
  const networkIds=new Set();
  session.on('Network.requestWillBeSent',p=>{if(p.request.url.endsWith('/api')){networkIds.add(p.requestId);emit('network.request',p);}});
  for(const name of ['responseReceived','loadingFinished','loadingFailed'])session.on('Network.'+name,p=>{if(networkIds.has(p.requestId))emit('network.'+name,p);});
  const send=async(method,params={})=>({result:await session.send(method,params)});
  const eval_=createRetainedEvaluator(send,(m)=>{if(m.result.exceptionDetails)throw Error(m.result.exceptionDetails.exception?.description||m.result.exceptionDetails.text);return m.result.result.value;});
  const sleep=async ms=>{await delay(ms);if(ms>=200)await eval_('window.__cdpSettleUI?.(0)');};
  let readyCalls=0, inOriginal=false;
  async function waitForUI(expr,timeout=5000){
    const start=Date.now(),end=start+timeout;emit('wait.begin',{expr,timeout});
    while(Date.now()<end){if(await eval_(expr)===true){emit('wait.pass',{expr,elapsedMs:Date.now()-start});if(inOriginal&&expr.includes("dataset.trialState==='ready'")&&mode==='prefix'&&++readyCalls===1)throw Object.assign(Error('Bounded P78 prefix completed'),{prefixComplete:true});return;}await sleep(50);}
    emit('wait.fail',{expr,elapsedMs:Date.now()-start});throw Error('UI condition timed out: '+expr);
  }
  const click=async(x,y)=>{for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1});};
  const drag=async(x0,y0,x1,y1,steps=6)=>{await send('Input.dispatchMouseEvent',{type:'mousePressed',x:x0,y:y0,button:'left',clickCount:1});for(let i=1;i<=steps;i++)await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:x0+(x1-x0)*i/steps,y:y0+(y1-y0)*i/steps,button:'left'});await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:x1,y:y1,button:'left',clickCount:1});};
  const snapshot=label=>eval_(`(()=>({label:${JSON.stringify(label)},title:document.title,url:location.href,trial:$('igTrial')?.dataset.trialState,note:$('igTrialNote')?.textContent,connection:{...connection},retryHidden:$('connectionRetry').hidden,retryDisabled:$('connectionRetry').disabled,inert:$('app').inert,workspaceOpen:$('infiniteGridWorkspace').open,boundary:!!document.querySelector('[data-ig-trial-boundary]'),ghosts:document.querySelectorAll('[data-ig-trial-ghost]').length}))()`);
  try{
    await send('Network.enable');await page.goto(url,{waitUntil:'load'});
    await waitForUI("typeof connection==='object' && connection.phase==='ready'",30000);
    emit('page.identity',{title:await page.title(),url:page.url(),browserVersion:browser.version()});
    await eval_(`(()=>{for(const key of ['phase','error','recovering']){let value=connection[key];Object.defineProperty(connection,key,{enumerable:true,configurable:true,get:()=>value,set:next=>{if(next!==value)window.__p78({event:'connection.change',key,old:value,next,stack:new Error().stack});value=next;}});}new MutationObserver(records=>{for(const r of records)if(r.type==='attributes'&&r.target.id==='igTrial')window.__p78({event:'trial.dom',old:r.oldValue,next:r.target.dataset.trialState});}).observe(document.documentElement,{subtree:true,attributes:true,attributeOldValue:true,attributeFilter:['data-trial-state']});})()`);
    await send('Emulation.setCPUThrottlingRate',{rate});emit('cpu.rate',{rate,scope:'Chromium renderer only; server/native unaffected'});
    inOriginal=true;
    try{await require(path.join(root,'geometry-web/grid_trial_test.js'))({send,eval_,sleep,click,drag,waitForUI,exceptionCount:()=>exceptions,expectNativeDialog:()=>{throw Error('Unexpected native dialog');}});passed=true;}
    catch(e){if(e.prefixComplete){passed=true;emit('prefix.completed');}else{fatal=e.stack;emit('p78.failed',{error:fatal});}}
    finally{inOriginal=false;}
    emit('state.final',{state:await snapshot('after original P78')});
    await page.screenshot({path:path.join(out,'final.png')});
    if(!passed){
      await eval_("$('igTrialNote')?.scrollIntoView({block:'center'})");
      await page.screenshot({path:path.join(out,'trial-error.png')});
      // Bounded observation, then exercise existing recovery separately from the failed test.
      await delay(3000);emit('state.observed',{state:await snapshot('3s after failed wait')});
      const ctl=cdp.makeCtl({eval_,sleep,click},{scroll:'center',attempts:12,pollMs:80,settleMs:140});
      emit('recovery.begin');
      // A modal workspace may make the real connection retry inaccessible.
      try{await ctl('#connectionRetry');emit('recovery.click',{reachable:true});}
      catch(e){emit('recovery.click',{reachable:false,error:e.message});await eval_('recoverConnection()');emit('recovery.direct',{diagnosticOnly:true});}
      await waitForUI("connection.phase==='ready'",20000);await delay(2000);
      emit('state.recovered',{state:await snapshot('connection retry, same candidate')});
      await page.screenshot({path:path.join(out,'recovered.png')});
      if(await eval_("$('infiniteGridWorkspace').open")){
        const key=cdp.makeKey({send,sleep}),fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:60});
        await fill('#igTrialWidth',2401);await waitForUI("$('igTrial')?.dataset.trialState==='ready'",20000);
        emit('state.edited',{state:await snapshot('explicit new candidate')});
      }
    }
  }catch(e){emit('harness.error',{error:e.stack});fatal=fatal||e.stack;passed=false;}
  finally{
    await session.send('Emulation.setCPUThrottlingRate',{rate:1}).catch(()=>{});
    await browser.close();console.log=oldLog;
    const result={passed,checks,failures,exceptions,fatal,mode,rate,fullCanvas:false,goldenCompared:false,originalP78Sha256:sha(fs.readFileSync(path.join(root,'geometry-web/grid_trial_test.js')))};
    fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
    emit('run.result',result);await new Promise(resolve=>sink.end(resolve));
    process.exitCode=passed?0:1;
  }
}
main().catch(e=>{console.error(e);process.exitCode=2;sink.end();});
