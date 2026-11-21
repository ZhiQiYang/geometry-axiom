'use strict';
/* Real Chromium Storage controls for R386. Each invocation owns a fresh profile;
 * source withdrawal happens only in an in-memory Node module, never in Git. */
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const http=require('node:http'),crypto=require('node:crypto'),Module=require('node:module');
const {spawn}=require('node:child_process');
const ROOT=path.resolve(__dirname,'../..');
const harness=require(path.join(ROOT,'geometry-web/cdp_test.js'));
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const ANCHORS={
  'omit-restore':['await helpers.eval_(restoreStorageExpression(snapshot));','/* R386 exact restore withdrawal */'],
  'omit-guard':["requireThat(same(snapshot,actual),'R386_CANVAS_SLOT_STATE_RESTORE');",'/* R386 exact state guard withdrawal */'],
};
const TESTS=['R386_CANVAS_SLOT_STORAGE_RESTORE','R386_CANVAS_SLOT_STATE_GUARD'];
const ORACLES=['R386_SLOT_STORAGE_ROUNDTRIP','R386_SLOT_FAILED_RESTORE_MUST_REJECT'];
const SNAPSHOT=`(()=>{const take=s=>Object.fromEntries(Object.keys(s).sort().map(k=>[k,s.getItem(k)]));return {local:take(localStorage),session:take(sessionStorage)};})()`;
const restoreExpression=value=>`(()=>{if(window.__r386OriginalSetItem){Storage.prototype.setItem=window.__r386OriginalSetItem;delete window.__r386OriginalSetItem;}const value=${JSON.stringify(value)};for(const [name,storage] of [['local',localStorage],['session',sessionStorage]]){storage.clear();for(const [key,text] of Object.entries(value[name]))storage.setItem(key,text);}return true;})()`;
function check(value,code){if(!value)throw Object.assign(Error(code),{oracle:code});}
function loadWrapper(variant){
  const file=path.join(ROOT,'geometry-web/canvas_registry.js');
  const original=fs.readFileSync(file,'utf8').replace(/\r\n/g,'\n');let source=original;
  if(variant!=='none'){
    const [before,after]=ANCHORS[variant]||[];
    if(!before||source.split(before).length!==2)throw Error('R386_SLOT_MUTATION_ANCHOR_NOT_UNIQUE');
    source=source.replace(before,after);
  }
  const loaded=new Module(file,module);loaded.filename=file;loaded.paths=Module._nodeModulePaths(path.dirname(file));
  loaded._compile(source,file);
  if(typeof loaded.exports.runSlotIsolation!=='function')throw Error('R386_SLOT_WRAPPER_MISSING');
  return {wrapper:loaded.exports.runSlotIsolation,registrySourceSha256:sha(original),mutationSourceSha256:sha(source)};
}
async function execute(variant){
  const loaded=loadWrapper(variant),profile=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-slot-probe-'));
  let browser,ws,server,endpoint='',startupError=null,sequence=0;const pending=new Map(),exceptions=[];
  const result={schema:'geometry-canvas-slot-probe/1',mutation:variant,registrySourceSha256:loaded.registrySourceSha256,
    mutationSourceSha256:loaded.mutationSourceSha256,tests:[],skipped:[],infrastructureError:false};
  try{
    server=http.createServer((request,response)=>{response.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});response.end('<!doctype html><meta charset="utf-8"><title>R386 Storage isolation probe</title>');});
    await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
    const url='http://127.0.0.1:'+server.address().port+'/';
    browser=spawn(process.env.GEOMETRY_CHROME||'/usr/bin/google-chrome',[
      '--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--remote-debugging-port=0',
      '--user-data-dir='+profile,...(process.env.GEOMETRY_CHROME_FLAGS||'').split(' ').filter(Boolean),'about:blank']);
    let startup='';browser.stderr.on('data',bytes=>{startup+=bytes;const match=startup.match(/DevTools listening on (ws:\/\/\S+)/);if(match)endpoint=match[1];});
    browser.stdout.on('data',()=>{});browser.once('error',error=>{startupError=error;});
    for(let attempt=0;attempt<120&&!endpoint;attempt++){
      if(startupError)throw startupError;if(browser.exitCode!==null)throw Error('R386_SLOT_CHROME_EXITED: '+startup);await delay(250);
    }
    if(!endpoint)throw Error('R386_SLOT_CHROME_START_TIMEOUT: '+startup);
    const port=Number(new URL(endpoint).port),origin='http://127.0.0.1:'+port;
    const version=await fetch(origin+'/json/version',{signal:AbortSignal.timeout(20000)}).then(response=>response.json());
    harness.verifyBrowserOwnership(version,endpoint,port);result.browserVersion=version.Browser;
    const tabs=await fetch(origin+'/json',{signal:AbortSignal.timeout(20000)}).then(response=>response.json());
    const page=tabs.find(tab=>tab.type==='page');if(!page)throw Error('R386_SLOT_CHROME_PAGE_MISSING');
    ws=new WebSocket(page.webSocketDebuggerUrl);
    await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('R386_SLOT_WS_TIMEOUT')),20000);
      ws.onopen=()=>{clearTimeout(timer);resolve();};ws.onerror=error=>{clearTimeout(timer);reject(error);};});
    ws.onmessage=event=>{const message=JSON.parse(event.data);
      if(message.id&&pending.has(message.id)){pending.get(message.id)(message);pending.delete(message.id);}
      else if(message.method==='Runtime.exceptionThrown')exceptions.push(message.params.exceptionDetails);};
    const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;
      const timer=setTimeout(()=>{pending.delete(id);reject(Error('R386_SLOT_CDP_TIMEOUT: '+method));},20000);
      pending.set(id,message=>{clearTimeout(timer);message.error?reject(Error(JSON.stringify(message.error))):resolve(message);});
      ws.send(JSON.stringify({id,method,params}));});
    const read=async expression=>harness.evaluationValue(await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true}),expression);
    await send('Page.enable');await send('Runtime.enable');await send('Page.navigate',{url});
    let ready=false;
    for(let attempt=0;attempt<150;attempt++){
      if(await read(`location.href===${JSON.stringify(url)}&&document.readyState==='complete'`)){ready=true;break;}await delay(100);
    }
    if(!ready)throw Error('R386_SLOT_PAGE_NOT_READY');
    for(let index=0;index<TESTS.length;index++){
      await read(restoreExpression({local:{keep:'本機\n原值'},session:{keep:'工作階段原值'}}));
      const before=await read(SNAPSHOT);let failure=null;
      try{
        if(index===0){
          let thrown=null;
          try{await loaded.wrapper({eval_:read},async()=>{await read("localStorage.removeItem('keep');localStorage.setItem('new','changed');sessionStorage.setItem('keep','changed');sessionStorage.setItem('new','extra');true");});}
          catch(error){thrown=error;}
          const after=await read(SNAPSHOT);
          check(!thrown&&JSON.stringify(after)===JSON.stringify(before),ORACLES[index]);
        }else{
          let thrown=null;
          try{await loaded.wrapper({eval_:read},async()=>{await read("localStorage.setItem('keep','changed');sessionStorage.setItem('new','extra');window.__r386OriginalSetItem=Storage.prototype.setItem;Storage.prototype.setItem=function(){};true");});}
          catch(error){thrown=error;}
          check(thrown?.code==='R386_CANVAS_SLOT_STATE_RESTORE',ORACLES[index]);
        }
      }catch(error){if(!error.oracle)throw error;failure=error.oracle;}
      finally{await read(restoreExpression(before));}
      result.tests.push({id:TESTS[index],passed:failure===null,oracle:failure});
      console.log((failure?'FAIL ':'PASS ')+TESTS[index]+(failure?' '+failure:''));
    }
    if(exceptions.length)throw Error('R386_SLOT_BROWSER_EXCEPTION: '+JSON.stringify(exceptions));
    result.passedAssertions=result.tests.filter(test=>test.passed).length;
    result.failedAssertions=result.tests.length-result.passedAssertions;
    result.completed=true;
  }catch(error){result.infrastructureError=true;result.error=String(error.stack||error);result.completed=false;}
  finally{
    ws?.close();
    if(browser&&browser.exitCode===null){browser.kill();await Promise.race([new Promise(resolve=>browser.once('exit',resolve)),delay(3000)]);if(browser.exitCode===null)browser.kill('SIGKILL');}
    if(server)await new Promise(resolve=>server.close(resolve));
    fs.rmSync(profile,{recursive:true,force:true});
  }
  console.log('CANVAS_SLOT_MUTATION_RESULT '+JSON.stringify(result));
  return result.infrastructureError?2:result.failedAssertions?1:0;
}
if(require.main===module){
  const variant=process.argv[2];
  if(!['none',...Object.keys(ANCHORS)].includes(variant)){console.error('Use none, omit-restore or omit-guard');process.exitCode=2;}
  else execute(variant).then(status=>{process.exitCode=status;}).catch(error=>{console.error(error.stack);process.exitCode=2;});
}
module.exports={ANCHORS,TESTS,ORACLES,loadWrapper,restoreExpression};
