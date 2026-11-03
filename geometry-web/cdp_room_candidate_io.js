/* R358 formal archive I/O for cdp_test.js.
 * Reuses the independently reviewed R06 process/download ownership pattern. No product functions are substituted.
 * Save selects the real download fallback; Open uses Chromium's file chooser.
 * A cold open owns a new Chrome process/profile and a separately owned server.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),net=require('node:net');
const {spawn,spawnSync}=require('node:child_process');
const ROOT=path.resolve(__dirname,'..');
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const infra=message=>Object.assign(Error('R358 archive infrastructure: '+message),{code:'R358_ARCHIVE_INFRASTRUCTURE'});
async function until(probe,{timeout=20000,description='condition'}={}){
 const end=Date.now()+timeout;
 while(Date.now()<end){const value=await probe();if(value)return value;await pause(50);}
 throw infra('timed out waiting for '+description);
}
async function unusedPort(){
 return new Promise((resolve,reject)=>{const server=net.createServer();server.once('error',reject);
  server.listen({host:'127.0.0.1',port:0},()=>{const port=server.address().port;server.close(error=>error?reject(error):resolve(port));});});
}
async function stop(child){
 if(!child||!Number.isInteger(child.pid)||child.exitCode!==null||child.signalCode!==null)return;
 if(process.platform==='win32'){
  spawnSync('taskkill',['/PID',String(child.pid),'/T','/F'],{stdio:'ignore'});
 }else{
  try{process.kill(-child.pid,'SIGTERM');}catch(error){if(error.code!=='ESRCH')throw error;}
 }
 const ended=await Promise.race([new Promise(resolve=>child.once('exit',()=>resolve(true))),pause(2000).then(()=>false)]);
 if(!ended&&child.exitCode===null&&child.signalCode===null){
  try{process.platform==='win32'?child.kill('SIGKILL'):process.kill(-child.pid,'SIGKILL');}catch(error){if(error.code!=='ESRCH')throw error;}
 }
}
function ownedSpawn(executable,args,options={}){
 const child=spawn(executable,args,{cwd:ROOT,detached:process.platform!=='win32',stdio:['ignore','pipe','pipe'],...options});
 // The strict outer runner can be killed while this cold child's independent
 // process group is still alive. Record only processes started here, with the
 // Linux birth tick so the runner cannot mistake a reused PID for its child.
 if(process.env.GEOMETRY_R358_OWNER_LEDGER&&child.pid){
  let birth=null;try{birth=fs.readFileSync('/proc/'+child.pid+'/stat','utf8').split(') ').slice(1).join(') ').split(' ')[19];}catch{}
  fs.appendFileSync(process.env.GEOMETRY_R358_OWNER_LEDGER,JSON.stringify({pid:child.pid,birth,root:ROOT,
   token:process.env.GEOMETRY_R358_OWNER_TOKEN,executable,args})+'\n');
 }
 child.spawnError=null;child.output='';child.ownedCommand={executable,args:[...args]};
 child.on('error',error=>{child.spawnError=error;});
 for(const stream of [child.stdout,child.stderr])stream.on('data',chunk=>{child.output=(child.output+chunk.toString()).slice(-32768);});
 return child;
}
function alive(child,label){
 if(child.spawnError)throw infra(label+' failed to start: '+child.spawnError.message);
 if(child.exitCode!==null||child.signalCode!==null)throw infra(label+' exited '+(child.signalCode||child.exitCode)+': '+child.output.slice(-3000));
}
async function runtime(url){
 const response=await fetch(new URL('/runtime',url),{signal:AbortSignal.timeout(3000)});
 if(!response.ok)throw infra('/runtime returned '+response.status);
 return response.json();
}
function freshBridge(){
 const python=process.env.GEOMETRY_PYTHON||process.env.PYTHON||'python3';
 const configured=process.env.GEOMETRY_TEST_BRIDGE||process.env.GEOMETRY_BRIDGE_EXECUTABLE||process.env.GEOMETRY_BRIDGE||'';
 // start_local.py owns a per-checkout TEMP directory and exports its paths only
 // to the server child. Use that launcher's directory policy for an unconfigured
 // parent harness, then retain the same source/sidecar/actual-byte inspection.
 const script='import json,sys,runpy;sys.path.insert(0,sys.argv[1]+"/tests");import binaries;from pathlib import Path;launch=runpy.run_path(str(Path(sys.argv[1])/"geometry-web/start_local.py"));candidate=Path(sys.argv[2]) if sys.argv[2] else launch["binary_directory"]()/binaries.BY_NAME["bridge"].path.name;explicit=candidate if sys.argv[2] or candidate.is_file() else None;i=binaries.inspect_one(binaries.BY_NAME["bridge"],path=explicit);print(json.dumps(i.as_dict()))';
 const result=spawnSync(python,['-B','-c',script,ROOT,configured],{cwd:ROOT,encoding:'utf8',timeout:30000});
 if(result.error||result.status!==0)throw infra('fresh bridge inspection failed: '+(result.error?.message||result.stderr));
 let record;try{record=JSON.parse(result.stdout);}catch{throw infra('bridge inspection did not return one JSON record');}
 if(record.state!=='fresh'||typeof record.path!=='string'||!fs.existsSync(record.path))throw infra('a current sidecar-verified bridge is required: '+JSON.stringify(record));
 return {python,record};
}
async function connection(child,endpoint){
 const url=new URL(endpoint);
 if(url.protocol!=='ws:'||!['127.0.0.1','localhost','[::1]'].includes(url.hostname)||!url.port)throw infra('cold Chrome endpoint is not local');
 const version=await fetch('http://127.0.0.1:'+url.port+'/json/version').then(r=>r.json());
 if(version.webSocketDebuggerUrl!==endpoint)throw infra('cold Chrome endpoint ownership mismatch');
 const targets=await fetch('http://127.0.0.1:'+url.port+'/json').then(r=>r.json());
 const target=targets.find(t=>t.type==='page'&&t.url==='about:blank');
 if(!target)throw infra('new Chrome did not provide its own about:blank target');
 const socket=new WebSocket(target.webSocketDebuggerUrl),pending=new Map(),listeners=new Map(),events=new Set();let next=0;
 await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=()=>reject(infra('cold Chrome WebSocket connection failed'));});
 const errors=[];
 socket.onmessage=event=>{
  const message=JSON.parse(event.data);
  if(message.id&&pending.has(message.id)){const entry=pending.get(message.id);pending.delete(message.id);clearTimeout(entry.timer);
   message.error?entry.reject(infra('CDP '+entry.method+': '+JSON.stringify(message.error))):entry.resolve(message);return;}
  if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails.exception?.description||message.params.exceptionDetails.text);
  if(message.method==='Inspector.targetCrashed')errors.push('cold Chrome target crashed');
  if(message.method==='Page.javascriptDialogOpening'){
   // This is the explicitly isolated test project. A rejected import may ask
   // to leave it; unexpected alert/prompt is still recorded as infrastructure.
   if(!['confirm','beforeunload'].includes(message.params.type))errors.push('unexpected native dialog: '+message.params.type);
   void send('Page.handleJavaScriptDialog',{accept:['confirm','beforeunload'].includes(message.params.type)}).catch(e=>errors.push(e.message));
  }
  for(const listener of listeners.get(message.method)||[])listener(message.params);
 };
 socket.onclose=()=>{
  for(const entry of pending.values()){clearTimeout(entry.timer);entry.reject(infra('cold Chrome disconnected during '+entry.method));}pending.clear();
  for(const entry of events){entry.cancel();entry.reject(infra('cold Chrome disconnected waiting for '+entry.method));}
 };
 function send(method,params={}){
  alive(child,'cold Chrome');
  return new Promise((resolve,reject)=>{const id=++next,timer=setTimeout(()=>{pending.delete(id);reject(infra('CDP timeout: '+method));},30000);
   pending.set(id,{resolve,reject,timer,method});socket.send(JSON.stringify({id,method,params}));});
 }
 async function read(expression){
  const message=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
  if(message.result?.exceptionDetails)throw infra('cold page evaluation: '+(message.result.exceptionDetails.exception?.description||message.result.exceptionDetails.text));
  if(!message.result?.result)throw infra('cold page evaluation has no result');
  return message.result.result.value;
 }
 async function wait(expression,timeout=20000){return until(()=>read(expression),{timeout,description:expression});}
 async function ctl(selector){
  const point=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e||e.disabled)return null;e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y);return r.width>0&&r.height>0&&h&&(h===e||e.contains(h))?{x,y}:null;})()`);
  if(!point)throw infra('cold page control is absent, disabled or obscured: '+selector);
  for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,...point,button:'left',clickCount:1});
 }
 function once(method,timeout=10000){
  let cancel;
  const promise=new Promise((resolve,reject)=>{
   const entry={method,reject,cancel:()=>{clearTimeout(timer);listeners.get(method)?.delete(handler);events.delete(entry);}};
   const handler=value=>{entry.cancel();resolve(value);};
   const timer=setTimeout(()=>{entry.cancel();reject(infra('event timeout: '+method));},timeout);
   cancel=entry.cancel;events.add(entry);
   if(!listeners.has(method))listeners.set(method,new Set());listeners.get(method).add(handler);
  });
  promise.cancel=()=>cancel();return promise;
 }
 return {send,read,wait,ctl,once,errors,close:()=>socket.close(),version:version.Browser};
}

async function createArchiveHarness({send,read,ctl}){
 const inheritedFlags=(process.env.GEOMETRY_CHROME_FLAGS||'').split(' ').filter(Boolean);
 const unsafe=flag=>/^--(?:no-sandbox|disable-(?:[a-z0-9]+-)*sandbox)(?:=|$)/.test(flag);
 // The outer CI browser may inherit legacy flags; the independently owned cold
 // child always keeps its sandbox and records every discarded override.
 const discardedUnsafeFlags=inheritedFlags.filter(unsafe),flags=inheritedFlags.filter(flag=>!unsafe(flag));
 if(flags.some(flag=>/^--(?:user-data-dir|profile-directory|remote-debugging-port|remote-debugging-address|remote-debugging-pipe)(?:=|$)/.test(flag)))
  throw infra('Chrome profile and debugging endpoint flags belong to this harness');
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'r358-formal-archive-'));
 fs.writeFileSync(path.join(directory,'launch-policy.json'),JSON.stringify({safeFlags:flags,discardedUnsafeFlags},null,2)+'\n');
 const downloads=path.join(directory,'downloads');fs.mkdirSync(downloads);
 let downloadConfigured=false;
 const restorePicker=()=>read(`(()=>{const state=window.__r358SavePickerState;if(state?.owner!==${JSON.stringify(directory)})return;if(state.descriptor)Object.defineProperty(window,'showSaveFilePicker',state.descriptor);else delete window.showSaveFilePicker;delete window.__r358SavePickerState;})()`);
 let savedDescriptor;
 try{
  savedDescriptor=await read(`(()=>{if(Object.hasOwn(window,'__r358SavePickerState'))throw Error('R358 archive harness already owns this page');window.__r358SavePickerState={owner:${JSON.stringify(directory)},descriptor:Object.getOwnPropertyDescriptor(window,'showSaveFilePicker')};const before=typeof window.showSaveFilePicker;Object.defineProperty(window,'showSaveFilePicker',{configurable:true,writable:true,value:undefined});return before;})()`);
  await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:downloads,eventsEnabled:true});downloadConfigured=true;
 }catch(error){try{await restorePicker();}catch(cleanupError){error.cleanupError=cleanupError.message;}throw error;}
 let serial=0;
 return {directory,savedDescriptor,
  async save(){
   const before=new Set(fs.readdirSync(downloads));
   await ctl('#projectBar [data-project-action="save"]');
   const deadline=Date.now()+20000;let archive=null;
   while(Date.now()<deadline){
    const candidates=fs.readdirSync(downloads).filter(name=>!before.has(name)&&name.endsWith('.gcanvas'));
    if(candidates.length>1)throw infra('Save produced multiple archives');
    if(candidates.length===1&&!fs.readdirSync(downloads).some(name=>name.endsWith('.crdownload'))){
     const file=path.join(downloads,candidates[0]);if(fs.statSync(file).size>0){archive=file;break;}
    }
    await pause(50);
   }
   if(!archive)return {completed:false,files:fs.readdirSync(downloads),status:await read(`({toast:document.querySelector('#toastRegion')?.textContent,status:document.querySelector('#status')?.textContent})`)};
   const file=path.join(directory,'saved-'+(++serial)+'.gcanvas');fs.copyFileSync(archive,file);fs.unlinkSync(archive);
   return {completed:true,file,bytes:new Uint8Array(fs.readFileSync(file)),size:fs.statSync(file).size};
  },
  async cold(){
   const sourceRuntime=await runtime(process.env.GEOMETRY_TEST_URL);
   if(sourceRuntime.schema!=='geometry-runtime/1'||sourceRuntime.fresh!==true||typeof sourceRuntime.root!=='string'||path.resolve(sourceRuntime.root)!==ROOT||
      !Number.isInteger(sourceRuntime.pid)||sourceRuntime.pid<1||typeof sourceRuntime.session!=='string'||!sourceRuntime.session||typeof sourceRuntime.version!=='string'||!sourceRuntime.version)
    throw infra('source service is not the current checkout');
   const {python,record}=freshBridge(),port=await unusedPort(),url='http://127.0.0.1:'+port;
   const feedback=fs.mkdtempSync(path.join(os.tmpdir(),'r358-cold-feedback-'));
   const server=ownedSpawn(python,['-B',path.join(__dirname,'serve.py'),String(port)],{env:{...process.env,
    GEOMETRY_BRIDGE_EXECUTABLE:record.path,GEOMETRY_FEEDBACK_DIR:feedback,GEOMETRY_ISOLATED_SERVICE:'1'}});
   let chrome,client;
   const cleanup=async()=>{try{client?.close();}finally{try{await stop(chrome);}finally{await stop(server);}}};
   try{
    const service=await until(async()=>{alive(server,'cold native service');try{return await runtime(url);}catch(error){if(error.code==='R358_ARCHIVE_INFRASTRUCTURE')throw error;return null;}},{description:'new native /runtime'});
    if(service.schema!=='geometry-runtime/1'||service.pid!==server.pid||service.pid===sourceRuntime.pid||typeof service.session!=='string'||!service.session||service.session===sourceRuntime.session||
       service.version!==sourceRuntime.version||service.fresh!==true||typeof service.root!=='string'||path.resolve(service.root)!==ROOT)
     throw infra('new native service did not prove an independent current session');
    const profile=fs.mkdtempSync(path.join(os.tmpdir(),'r358-cold-chrome-'));
    chrome=ownedSpawn(process.env.GEOMETRY_CHROME||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',[
     '--headless=new','--disable-gpu','--no-first-run','--remote-debugging-port=0','--window-size=1280,900',
     '--user-data-dir='+profile,...flags,'about:blank']);
    const endpoint=await until(()=>{alive(chrome,'cold Chrome');return chrome.output.match(/DevTools listening on (ws:\/\/\S+)/)?.[1];},{description:'owned cold Chrome endpoint'});
    client=await connection(chrome,endpoint);
    await client.send('Page.enable');await client.send('Runtime.enable');await client.send('DOM.enable');
    await client.send('Page.setInterceptFileChooserDialog',{enabled:true});
    await client.send('Page.navigate',{url});
    await client.wait(`typeof ReferenceWorkspace!=='undefined'&&typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy`);
    const info={sourceRuntime,service,profile,browserPid:chrome.pid,browserVersion:client.version,bridge:record,url,
     serverCommand:server.ownedCommand,browserCommand:chrome.ownedCommand,discardedUnsafeFlags};
    fs.writeFileSync(path.join(directory,'cold-'+(++serial)+'.json'),JSON.stringify(info,null,2)+'\n');
    return {...client,info,
     async open(file){
      if(!path.isAbsolute(file)||!fs.existsSync(file))throw infra('Open needs an existing absolute downloaded archive');
      await client.ctl('#fileMenuBtn');
      const choosing=client.once('Page.fileChooserOpened');
      // If the control request itself fails, the event can reject before its
      // await below; keep that failure handled while preserving the original promise.
      void choosing.catch(()=>{});
      try{
       await client.ctl('#btnOpenProject');
       const chooser=await choosing;
       const node=(await client.send('DOM.describeNode',{backendNodeId:chooser.backendNodeId})).result.node;
       const attributes=node.attributes||[],at=attributes.indexOf('id'),elementId=at<0?null:attributes[at+1];
       if(elementId!=='projectFile')throw infra('Open invoked another file chooser: '+elementId);
       await client.send('DOM.setFileInputFiles',{files:[file],backendNodeId:chooser.backendNodeId});
       return {elementId,backendNodeId:chooser.backendNodeId};
      }finally{choosing.cancel();}
     },
     async close(){try{const end=await runtime(url);fs.writeFileSync(path.join(directory,'cold-final-'+serial+'.json'),JSON.stringify({info,end,errors:client.errors},null,2)+'\n');}finally{await cleanup();}}
    };
   }catch(error){await cleanup();throw error;}
  },
  async close(){
   try{await restorePicker();}finally{if(downloadConfigured){downloadConfigured=false;await send('Browser.setDownloadBehavior',{behavior:'default'});}}
  }
 };
}
module.exports={createArchiveHarness};
