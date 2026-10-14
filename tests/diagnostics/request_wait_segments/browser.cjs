/* Diagnostic reproduction of the original P7 insR expression. Browser plugin
   not available; use the already-installed Playwright and system Chromium. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto'),net=require('node:net'),cp=require('node:child_process');
const {chromium}=require('playwright');
const repo=path.resolve(__dirname,'../../..'),out=path.resolve(process.argv[2]);fs.mkdirSync(out,{recursive:true});
const source=fs.readFileSync(path.join(repo,'geometry-web/cdp_test.js'),'utf8');
function literal(marker,after=0,end='`);') {const a=source.indexOf(marker,after);assert(a>=0);const b=source.indexOf(end,a+marker.length);assert(b>a);const raw=source.slice(a+marker.length,b);assert(!raw.includes('${'));return {raw,value:vm.runInNewContext('`'+raw+'`')};}
const p7=literal('const insR = await eval_(`',source.indexOf('=== P7.'));
const settle=literal("await send('Page.addScriptToEvaluateOnNewDocument',{source:`",source.indexOf('Pin the desktop'), '`});');
fs.writeFileSync(path.join(out,'p7-original-expression.js'),p7.value);fs.writeFileSync(path.join(out,'settle-original.js'),settle.value);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function port(){return new Promise((resolve,reject)=>{const s=net.createServer();s.on('error',reject);s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>resolve(p));});});}
async function instrument(page,config){
 await page.evaluate(config=>{
  const rows=window.__requestWaitRows=[],put=(event,data={})=>rows.push({event,ms:performance.now(),...data});
  const originalFetch=window.fetch.bind(window),originalApi=apiRequest;let current=null,number=0,armed=false;const business=new Map();
  window.fetch=async function(input,options){
   const url=typeof input==='string'?input:input.url;
   if(!url.endsWith('/api'))return originalFetch(input,options);
   const data=JSON.parse(options.body),id='fetch-'+(++number),call=current||business.get(data.receipt)||null;
   if(data.requestId)business.set(data.requestId,call);
   const headers=new Headers(options.headers);headers.set('X-Geometry-Diagnostic-Id',id);
   put('fetch_begin',{id,call,command:data.cmd,receipt:data.receipt,businessRequestId:data.requestId});
   options.signal?.addEventListener('abort',()=>put('fetch_abort',{id,call,reason:options.signal.reason?.name,message:options.signal.reason?.message}),{once:true});
   try{const response=await originalFetch(input,{...options,headers});put('fetch_headers',{id,call,status:response.status});return response;}
   catch(error){put('fetch_error',{id,call,name:error.name,message:error.message});throw error;}
  };
  apiRequest=async function(command,...args){
   const id='call-'+(++number);put('api_enter',{id,command,phase:connection.phase});
   if(config.stage&&!armed&&command.startsWith(config.target)){
    armed=true;put('load_arm',{id,stage:config.stage,seconds:config.seconds});
    const response=await originalFetch('/__diag/hold',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...config,label:id})});
    const ack=await response.json();if(!ack.ok)throw Error('load not acquired');put('load_ack',{id,ack});
   }
   const phase=connection.phase,prior=current;current=id;let promise;
   try{promise=originalApi(command,...args);}finally{current=prior;}
   const result=await promise;put('api_end',{id,command,phase_before:phase,phase_after:connection.phase,result});return result;
  };
 },config);
}
async function run(config){
 const folder=path.join(out,config.name);fs.mkdirSync(folder,{recursive:true});const p=await port();
 const serverArgs=[path.join(__dirname,'server.py'),'--repo',repo,'--out',folder,'--port',String(p)];
 const stdout=fs.openSync(path.join(folder,'server.stdout'),'w'),stderr=fs.openSync(path.join(folder,'server.stderr'),'w');
 const server=cp.spawn('python3',serverArgs,{cwd:repo,detached:true,env:{...process.env,GEOMETRY_BRIDGE_EXECUTABLE:'/tmp/geometry-tests/bridge',GEOMETRY_FEEDBACK_DIR:path.join(folder,'feedback')},stdio:['ignore',stdout,stderr]});
 const toolHashes={};for(const file of ['browser.cjs','server.py']){const bytes=fs.readFileSync(path.join(__dirname,file));fs.writeFileSync(path.join(folder,file+'.executed'),bytes);toolHashes[file]=crypto.createHash('sha256').update(bytes).digest('hex');}
 let browser,result={config,tool_hashes:toolHashes,argv:['python3',...serverArgs],server_pid:server.pid,clock:'browser performance.now; do not subtract server monotonic_ns'};const start=Date.now();
 try{
  for(let n=0;n<200&&!fs.existsSync(path.join(folder,'ready.json'));n++){if(server.exitCode!==null)throw Error('server startup exit '+server.exitCode);await sleep(100);}
  const ready=JSON.parse(fs.readFileSync(path.join(folder,'ready.json'),'utf8'));assert.equal(ready.server_pid,server.pid);result.ready=ready;
  const status=await (await fetch('http://127.0.0.1:'+p+'/runtime')).json();assert.equal(status.root,repo);assert.equal(status.version,ready.version);assert.equal(status.fresh,true);result.runtime=status;
  browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const context=await browser.newContext({viewport:{width:1400,height:900}}),page=await context.newPage();const consoleRows=[],network=[];
  page.on('console',m=>consoleRows.push({type:m.type(),text:m.text()}));page.on('pageerror',e=>consoleRows.push({type:'pageerror',text:e.message}));page.on('requestfailed',r=>network.push({url:r.url(),method:r.method(),failure:r.failure()}));
  await page.addInitScript(settle.value);await page.goto('http://127.0.0.1:'+p+'/',{waitUntil:'load'});
  await page.waitForFunction(()=>typeof api==='function'&&typeof oc==='object'&&connection.phase==='ready',null,{timeout:30000});
  result.identity={url:page.url(),title:await page.title(),bodyText:(await page.locator('body').innerText()).slice(0,1200)};
  await instrument(page,config);
  if(config.cpu){const cdp=await context.newCDPSession(page);await cdp.send('Emulation.setCPUThrottlingRate',{rate:config.cpu});}
  try{result.p7=await page.evaluate(p7.value);result.p7_pass=result.p7.tool==='select'&&result.p7.panel===true&&result.p7.verts===8&&result.p7.fixity===8&&result.p7.ortho===true;}
  catch(e){result.p7_pass=false;result.original_expression_error={name:e.name,message:e.message};}
  result.state=await page.evaluate(()=>({phase:connection.phase,error:connection.error,notice:document.getElementById('connectionMessage')?.textContent,worldView:typeof fe==='object'?{tool:fe.tool,bid:fe.bid}:null}));
  if(result.state.phase==='error')result.followups=await page.evaluate(async()=>{const a=[];for(const cmd of ['dump','boundary 1','references 1'])a.push({cmd,result:await apiRequest(cmd)});return a;});
  await page.screenshot({path:path.join(folder,'state.png'),fullPage:false});
  fs.writeFileSync(path.join(folder,'dom.html'),await page.content());
  // Wait for the holder's actual release and all accepted /api handlers. A
  // deadline relative to process startup can terminate the native process
  // before a late request runs, contaminating the very segment being measured.
  const drainStart=Date.now();let drained=false;
  while(Date.now()-drainStart<40000){
   const events=fs.readFileSync(path.join(folder,'server-events.jsonl'),'utf8').trim().split('\n').map(line=>JSON.parse(line));
   const entered=events.filter(e=>e.event==='http_enter'&&e.path==='/api').map(e=>e.request),exited=new Set(events.filter(e=>e.event==='http_exit').map(e=>e.request));
   const released=!config.stage||events.some(e=>e.event==='load_released'&&e.stage===config.stage);
   if(released&&entered.every(id=>exited.has(id))){drained=true;break;}
   await sleep(100);
  }
  result.drain={complete:drained,wait_ms:Date.now()-drainStart};assert(drained,'late API handlers did not drain');
  result.native_before_cleanup=await (await fetch('http://127.0.0.1:'+p+'/__diag/status',{method:'POST',body:'{}'})).json();
  assert.equal(result.native_before_cleanup.native_returncode,null);assert.equal(result.native_before_cleanup.bridge_failure,null);
  result.browser_rows=await page.evaluate(()=>window.__requestWaitRows);
  fs.writeFileSync(path.join(folder,'browser-events.json'),JSON.stringify(result.browser_rows,null,2)+'\n');delete result.browser_rows;
  fs.writeFileSync(path.join(folder,'console.json'),JSON.stringify(consoleRows,null,2)+'\n');fs.writeFileSync(path.join(folder,'network-failures.json'),JSON.stringify(network,null,2)+'\n');
 }catch(e){result.harness_error={name:e.name,message:e.stack};}
 finally{
  if(browser)await browser.close();
  if(server.exitCode===null)process.kill(-server.pid,'SIGTERM');
  const exit=server.exitCode!==null?{code:server.exitCode,signal:server.signalCode}:await Promise.race([new Promise(resolve=>server.once('exit',(code,signal)=>resolve({code,signal}))),sleep(5000).then(()=>null)]);
  result.server_exit=exit;if(exit===null&&server.exitCode===null){process.kill(-server.pid,'SIGKILL');result.server_forced_cleanup=true;}
  fs.closeSync(stdout);fs.closeSync(stderr);result.wall_ms=Date.now()-start;
  fs.writeFileSync(path.join(folder,'result.json'),JSON.stringify(result,null,2)+'\n');
 }
 console.log(config.name,JSON.stringify({pass:result.p7_pass,state:result.state,error:result.original_expression_error,harness_error:result.harness_error}));return result;
}
(async()=>{
 const configurations=[{name:'baseline'},{name:'renderer-cpu20',cpu:20},{name:'bridge3',stage:'bridge',seconds:3,target:'source-inspect'},{name:'bridge18',stage:'bridge',seconds:18,target:'source-inspect'},{name:'native18',stage:'native',seconds:18,target:'source-inspect'},{name:'runtime18',stage:'runtime',seconds:18,target:'line surface '},{name:'receipt18',stage:'receipt',seconds:18,target:'line surface '}];
 const chosen=process.argv[3]?configurations.filter(c=>c.name===process.argv[3]):configurations;assert(chosen.length>0);
 const results=[];for(const config of chosen)results.push(await run(config));fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2)+'\n');
 if(results.some(r=>r.harness_error))process.exitCode=2;
})().catch(e=>{console.error(e);process.exitCode=2;});
