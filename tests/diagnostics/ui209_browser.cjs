'use strict';
// Bounded, isolated excerpts. Original helpers, assertions and deadlines remain.
// Recovery observations are separate from (and cannot erase) the first red.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),Module=require('node:module');
const {chromium}=require('playwright');
const root=process.env.UI209_SOURCE_ROOT, [url,out,which]=process.argv.slice(2);
const cdp=require(path.join(root,'geometry-web/cdp_helpers.js'));
const {createRetainedEvaluator}=require(path.join(root,'geometry-web/cdp_evaluation.js'));
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const sink=fs.createWriteStream(path.join(out,'browser.jsonl'),{flags:'wx'});
const emit=(event,data={})=>sink.write(JSON.stringify({event,hostEpochMs:Date.now(),hostMonoNs:process.hrtime.bigint().toString(),...data})+'\n');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const result={case:which,scope:'bounded prefix and separate recovery',firstRed:null,originalChecks:0,originalFailures:0,exceptions:[],recovery:null,fullRunner:false,historicalWSL:false,goldenCompared:false};
const save=(name,obj)=>fs.writeFileSync(path.join(out,name+'.json'),JSON.stringify(obj,null,2)+'\n');

async function main(){
  const source=fs.readFileSync(path.join(root,'geometry-web/grid-system-workspace.js'),'utf8');
  const observed=require('./ui209_instrument.cjs')(source);
  fs.writeFileSync(path.join(out,'served-grid-system-workspace.js'),observed.source);
  save('instrumentation',{originalSha256:sha(source),servedSha256:sha(observed.source),awaits:observed.awaits,returns:observed.returns,overhead:'Uncalibrated; each await adds a logging Promise layer.'});
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true});
  const context=await browser.newContext({viewport:{width:1400,height:1000}}),page=await context.newPage(),session=await context.newCDPSession(page);
  const log=console.log;
  console.log=(...args)=>{log(...args);if(args[1]==='✓')result.originalChecks++;if(args[1]==='✗')result.originalFailures++;emit('original.log',{args});};
  page.on('pageerror',error=>{result.exceptions.push(error.stack);emit('page.exception',{error:error.stack});});
  page.on('console',m=>emit('console',{type:m.type(),text:m.text()}));
  await page.exposeBinding('__uiSink',(_,row)=>emit('browser',row));
  await page.route(/\/grid-system-workspace\.js(?:\?.*)?$/,route=>route.fulfill({body:observed.source,contentType:'text/javascript'}));
  await page.addInitScript(fs.readFileSync(path.join(__dirname,'ui209_observer.js'),'utf8'));
  const harness=fs.readFileSync(path.join(root,'geometry-web/cdp_test.js'),'utf8');
  const init=harness.split("await send('Page.addScriptToEvaluateOnNewDocument',{source:`")[1]?.split('`});')[0];
  if(!init)throw Error('Missing original CDP initialization');
  fs.writeFileSync(path.join(out,'original-harness-init.js'),init);await page.addInitScript(init);
  const ids=new Set();
  session.on('Network.requestWillBeSent',p=>{if(p.request.url.endsWith('/api')){ids.add(p.requestId);emit('network.request',p);}});
  for(const name of ['responseReceived','loadingFinished','loadingFailed'])session.on('Network.'+name,p=>{if(ids.has(p.requestId))emit('network.'+name,p);});
  const send=async(method,params={})=>({result:await session.send(method,params)});
  // Playwright screenshots restore its configured viewport after a CDP override.
  // Direct CDP capture keeps the emulated viewport used by the original module.
  const screenshot=async name=>{const r=await session.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(r.data,'base64'));};
  const evaluate=createRetainedEvaluator(send,m=>{if(m.result.exceptionDetails)throw Error(m.result.exceptionDetails.exception?.description||m.result.exceptionDetails.text);return m.result.result.value;});
  let p88Scrolls=0;
  async function eval_(expr){
    const value=await evaluate(expr);
    if(which==='p88-wheel'&&expr.startsWith('document.querySelector("#igNewBinding")?.scrollIntoView')&&++p88Scrolls===2){
      emit('injection.reopen.begin',{description:'Explicit product openSystem call after the second old-helper scroll; not a spontaneous historical event.'});
      result.replacement=await evaluate(`(async()=>{const before=window.__uiSnapshot();const old=$('igNewBinding');await InfiniteGridWorkspace.openSystem(oc.gridSystems[0].id);return {before,after:window.__uiSnapshot(),nodeReplaced:old!==$('igNewBinding')};})()`);
      emit('injection.reopen.end',result.replacement);save('replacement',result.replacement);
    }
    return value;
  }
  const sleep=async ms=>{await delay(ms);if(ms>=200)await eval_('window.__cdpSettleUI?.(0)');};
  const waitForUI=async(expr,timeout=5000)=>{
    const start=Date.now();emit('wait.begin',{expr,timeout});
    while(Date.now()-start<timeout){if(await eval_(expr)===true){emit('wait.pass',{expr,elapsedMs:Date.now()-start});return;}await delay(50);}
    emit('wait.fail',{expr,elapsedMs:Date.now()-start});throw Error('UI condition timed out: '+expr);
  };
  const click=async(x,y)=>{emit('input.pointer',{x,y});for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1});};
  const expectNativeDialog=async(action,expected)=>{
    const pending=page.waitForEvent('dialog',{timeout:10000});const running=action();const dialog=await pending;
    emit('native.dialog',{type:dialog.type(),message:dialog.message(),expected});
    if(dialog.message()!==expected.message){await dialog.dismiss();throw Error('Unexpected native dialog');}
    await (expected.accept===false?dialog.dismiss():dialog.accept());await running;
  };
  const snapshot=async label=>{const ui=await eval_('window.__uiSnapshot()');emit('state.snapshot',{label,ui});return ui;};
  const validDump=async()=>{const r=await eval_("apiRequest('dump')");if(r?.ok!==true||typeof r.text!=='string')throw Error('Invalid dump receipt');return {ok:r.ok,text:r.text,sha256:sha(r.text)};};
  const pin=async()=>{
    const dump=await validDump();const history=await eval_(`(()=>{const h=ReferenceWorkspace.history;window.__uiHistory={undo:h.undo.slice(),redo:h.redo.slice(),limit:h.limit,frame:h.frame,context:ReferenceWorkspace.context(),token:ReferenceWorkspace.getProjectState().contextToken};return {undo:h.undo.length,redo:h.redo.length,limit:h.limit,frame:h.frame};})()`);
    return {dump,history};
  };
  const compare=async before=>{
    const dump=await validDump(),history=await eval_(`(()=>{const h=ReferenceWorkspace.history,b=window.__uiHistory,same=(a,z)=>a.length===z.length&&a.every((v,i)=>v===z[i]);return {undoSame:same(h.undo,b.undo),redoSame:same(h.redo,b.redo),frameSame:h.frame===b.frame,limitSame:h.limit===b.limit,contextSame:ReferenceWorkspace.context()===b.context,tokenSame:ReferenceWorkspace.getProjectState().contextToken===b.token,undo:h.undo.length,redo:h.redo.length};})()`);
    const receipt={before,after:{dump,history},dumpSame:dump.text===before.dump.text};
    save('recovery-state-comparison',receipt);
    // These are observations, not a new zero-history product requirement.
    // Opening/editing a portable draft can append undo entries without native writes.
    // Invalid dump receipts still fail above; individual differences stay visible.
    return receipt;
  };
  const initialRed=async error=>{result.firstRed={message:error.message,stack:error.stack,ui:await snapshot('first red, original control')};emit('original.first-red',result.firstRed);save('first-red',result.firstRed);await screenshot('first-red');};
  async function p70({ctl,choose,wait,read,open,mobile}){
    const before=await pin();await eval_("window.__uiArm=true;window.__uiTargetOpen=window.__uiOpenSerial+1;void 0");
    emit('critical.begin',{action:'Original P70: ctl igNewBinding then choose igBoundary=301',mobile});
    try{await ctl('#igNewBinding');await choose('#igBoundary',301);}
    catch(error){await initialRed(error);}
    if(result.firstRed){
      await waitForUI('window.__uiEnded[window.__uiTargetOpen]===true',22000);
      result.afterOpen=await snapshot('original open settled, before recovery');
      if(await read("connection.phase==='ready'")){
        emit('recovery.begin',{route:'wait for existing open, then real boundary selection'});
        await choose('#igBoundary',301);
        result.recovery={route:'existing open completed; real select interaction',reachable:true};
      }else{
        emit('recovery.begin',{route:'real Return canvas -> connection retry -> original source -> new binding'});
        await ctl('#igClose');await wait("!$('infiniteGridWorkspace').open");
        await ctl('#connectionRetry');await wait("connection.phase==='ready'&&!ReferenceWorkspace.busy");
        await open('grid-system',mobile);await ctl('#igNewBinding');
        await wait("!$('igBindingForm').hidden&&!$('igBoundary').disabled&&$('igBoundary').getBoundingClientRect().width>0");
        await choose('#igBoundary',301);
        result.recovery={route:'Return canvas -> connection retry -> original source -> new binding',reachable:true};
      }
    }
    await wait(`!!document.querySelector('[data-ig-vertex="outer:0"]')`);
    result.boundaryUsable=await read("$('igBoundary').value==='301'&&!$('igBindingForm').hidden&&connection.phase==='ready'");
    if(!result.boundaryUsable)throw Error('Boundary did not become usable');
    result.comparison=await compare(before);
    await snapshot('boundary selection completed');
  }
  async function p88(action,index){
    if(!index)return action();
    const before=await pin();
    try{await action();}
    catch(error){
      await initialRed(error);
      emit('recovery.begin',{route:'trusted wheel over current inspector, then hit-tested pointer'});
      let found=false;
      for(let attempt=0;attempt<8;attempt++){
        const position=await eval_(`(()=>{const n=$('igNewBinding'),r=n.getBoundingClientRect(),p=n.closest('.ig-inspector').getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,hit:n.contains(document.elementFromPoint(x,y)),disabled:n.disabled,w:r.width,h:r.height,wheelX:p.x+p.width/2,wheelY:Math.min(innerHeight-60,Math.max(p.y+60,p.y+p.height/2))};})()`);
        emit('recovery.wheel.measure',{attempt,position,ui:await snapshot('wheel '+attempt)});
        if(position.hit&&!position.disabled&&position.w&&position.h){await click(position.x,position.y);found=true;break;}
        await send('Input.dispatchMouseEvent',{type:'mouseWheel',x:position.wheelX,y:position.wheelY,deltaX:0,deltaY:400});await delay(100);
      }
      if(!found)throw Error('Bounded wheel recovery could not reach button');
      await waitForUI("!$('igBindingForm').hidden&&!$('igBoundary').disabled",25000);
      result.recovery={route:'trusted wheel -> current button hit-tested pointer -> binding form',reachable:true};
    }
    result.comparison=await compare(before);
  }
  try{
    await send('Network.enable');await page.goto(url,{waitUntil:'load'});
    await waitForUI("typeof connection==='object'&&connection.phase==='ready'",30000);
    await eval_('window.__uiObserveReady();void 0');emit('page.identity',{url:page.url(),title:await page.title(),browserVersion:browser.version()});
    let testName,code;
    if(which.startsWith('p70')){
      testName='grid_system_test.js';const original=fs.readFileSync(path.join(root,'geometry-web',testName),'utf8');
      const cut=original.indexOf("  await send('Emulation.setDeviceMetricsOverride',{width:1400");
      if(cut<0)throw Error('Missing P70 prefix boundary');
      code=original.slice(0,cut).replace('exceptionCount})','exceptionCount,ui209})')+`
  await reset();
  await fixture(['boundary 301 outline 100,200 1300,200 1300,1000 100,1000']);
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await sleep(200);
  if(!await read("$('btnNewGridSystem').getBoundingClientRect().width>0"))await ctl('#toggleLeft');
  const mobile=await create('手機 無限');
  await ui209({ctl,choose,wait,read,open,mobile});
};\n`;
    }else{
      testName='grid_rule_lines_test.js';const original=fs.readFileSync(path.join(root,'geometry-web',testName),'utf8');
      const cut=original.indexOf('    const refs=await query');if(cut<0)throw Error('Missing P88 prefix boundary');
      code=original.slice(0,cut)+'\n  }\n};\n';
      code=code.replace('exceptionCount})','exceptionCount,ui209})').replace('for(const width of [1280,390])','for(const width of [1280])');
      const anchor="if(index)await ctl('#igEditSource');await ctl('#igNewBinding');";
      if(code.split(anchor).length!==2)throw Error('Missing historical P88 control anchor');
      code=code.replace(anchor,"if(index)await ctl('#igEditSource');await ui209(()=>ctl('#igNewBinding'),index);");
    }
    fs.writeFileSync(path.join(out,'executed-prefix.cjs'),code);
    const filename=path.join(root,'geometry-web',testName),mod=new Module(filename);mod.filename=filename;mod.paths=Module._nodeModulePaths(path.dirname(filename));mod._compile(code,filename);
    result.testSource={file:testName,sha256:sha(fs.readFileSync(filename)),prefixSha256:sha(code)};
    await mod.exports({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount:()=>result.exceptions.length,ui209:which.startsWith('p70')?p70:p88});
    result.prefixCompleted=true;
    result.final=await snapshot('final');await screenshot('final');
    result.postScreenshotViewport=await eval_('({width:innerWidth,height:innerHeight})');
    const expected=which.startsWith('p70')?{width:390,height:844}:{width:1280,height:900};
    if(result.final.viewport.width!==expected.width||result.final.viewport.height!==expected.height||JSON.stringify(result.postScreenshotViewport)!==JSON.stringify(expected))throw Error('Diagnostic changed the original viewport');
  }catch(error){result.harnessError=error.stack;emit('harness.error',{error:error.stack});result.final=await snapshot('harness stopped').catch(()=>null);}
  finally{
    await browser.close();console.log=log;
    result.exit=result.harnessError?2:result.firstRed?1:0;
    save('result',result);emit('run.result',result);await new Promise(resolve=>sink.end(resolve));process.exitCode=result.exit;
  }
}
main().catch(error=>{console.error(error);process.exitCode=2;sink.end();});
