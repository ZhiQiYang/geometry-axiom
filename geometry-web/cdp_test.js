/* CDP 驅動 headless Chrome 實測物件畫布互動 */
const { spawn } = require("child_process");
const fs = require('fs'), path = require('path'), os = require('os');
const net = require('net');
const floor = require('./cdp_floor.js');
const cdp = require('./cdp_helpers.js');
const {createRetainedEvaluator} = require('./cdp_evaluation.js');
const {waitForExpectedNavigation} = require('./cdp_navigation.js');
const SCOPE_FLAGS = ['GEOMETRY_ROOM_OUTLINE_ONLY','GEOMETRY_TIMBER_SCHEDULE_ONLY','GEOMETRY_ASSEMBLY_ONLY','GEOMETRY_PARAMETERS_ONLY','GEOMETRY_SELECTION_CURSOR_ONLY','GEOMETRY_UX_REFINEMENT_ONLY','GEOMETRY_UIUX_FIX_ONLY','GEOMETRY_MARQUEE_ONLY','GEOMETRY_PROJECT_AUDIT_ONLY','GEOMETRY_ENGINEERING_WORKFLOW_ONLY','GEOMETRY_GRID_SYSTEM_ONLY','GEOMETRY_INFINITE_FACE_ONLY','GEOMETRY_COMPOSITION_ONLY','GEOMETRY_UI_REVIEW_ONLY','GEOMETRY_REPAIR_ONLY','GEOMETRY_FLOW_REPAIR_ONLY','GEOMETRY_REFERENCE_ONLY','GEOMETRY_CDP_FROM_P31'];
const ENGINEERING_MODIFIERS=['GEOMETRY_ENGINEERING_EXAMPLE_ONLY','GEOMETRY_ENGINEERING_NAVIGATION_ONLY','GEOMETRY_ENGINEERING_SUBGRID_ONLY'];
function runConfiguration(env = process.env) {
  if (!env.GEOMETRY_TEST_URL) throw Error('GEOMETRY_TEST_URL is required: use an explicitly isolated test service. No browser or reset was started.');
  const url = new URL(env.GEOMETRY_TEST_URL);
  if (!['http:','https:'].includes(url.protocol)) throw Error('GEOMETRY_TEST_URL must be an HTTP(S) test service');
  if(env.GEOMETRY_CDP_PORT && (!/^\d+$/.test(env.GEOMETRY_CDP_PORT) || Number(env.GEOMETRY_CDP_PORT)<1 || Number(env.GEOMETRY_CDP_PORT)>65535))throw Error('GEOMETRY_CDP_PORT must be an integer from 1 to 65535');
  if (!env.GEOMETRY_FEEDBACK_DIR || !path.isAbsolute(env.GEOMETRY_FEEDBACK_DIR)) throw Error('GEOMETRY_FEEDBACK_DIR must name the isolated server feedback directory under TEMP');
  const relative = path.relative(os.tmpdir(),path.resolve(env.GEOMETRY_FEEDBACK_DIR));
  if (!relative || relative==='..' || relative.startsWith('..'+path.sep) || path.isAbsolute(relative)) throw Error('GEOMETRY_FEEDBACK_DIR must be a dedicated directory under TEMP');
  const filters=SCOPE_FLAGS.filter(name=>env[name]);
  const modifiers=ENGINEERING_MODIFIERS.filter(name=>env[name]);
  if([...filters,...modifiers].some(name=>env[name]!=='1'))throw Error('Scope flags accept only 1; remove a flag to disable it');
  if(filters.length>1)throw Error('Choose only one CDP scope flag; combined filters can silently omit every suite');
  if(modifiers.length>1)throw Error('Choose only one engineering workflow modifier');
  if(modifiers.length && env.GEOMETRY_ENGINEERING_WORKFLOW_ONLY!=='1')throw Error('Engineering modifiers require GEOMETRY_ENGINEERING_WORKFLOW_ONLY=1');
  return {mode:filters.length?'partial':'full',filters,modifiers,url:url.href,feedbackDirectory:path.resolve(env.GEOMETRY_FEEDBACK_DIR)};
}
// Legacy checks log a verdict as a separate argument. Never scan arbitrary
// diagnostics or page console strings for checkmark characters.
const EXPLICIT_VERDICT=Symbol('explicit-test-verdict');
function explicitVerdict(text) {
  if(typeof text!=='string' || !/[✓✗]/.test(text))throw Error('Explicit test verdict must contain a success/failure marker');
  return {[EXPLICIT_VERDICT]:text.includes('✗')?false:true,text};
}
/* 本體各段的 check 共用 cdp_helpers.makeCheck:只把判定值換成 explicitVerdict,讓 harness 只計受控斷言。
   通過判定一律 value===true;選項見 cdp_helpers.js。 */
const bodyCheck=(options={})=>cdp.makeCheck({...options,mark:ok=>explicitVerdict(ok?'✓':'✗')});
function assertionVerdicts(args) {
  if(typeof args[0]==='string' && /^\[(?:console|EXCEPTION)\]/.test(args[0]))return [];
  return args.flatMap(value=>value && typeof value==='object' && EXPLICIT_VERDICT in value?[value[EXPLICIT_VERDICT]]:value==='✓'?[true]:value==='✗'?[false]:[]);
}
function evaluationValue(message, expression) {
  if(message.error)throw Error('CDP Runtime.evaluate failed: '+JSON.stringify(message.error));
  if(!message.result?.result)throw Error('CDP Runtime.evaluate returned no result');
  const error=message.result.exceptionDetails;
  if(error)throw Error('Browser evaluation failed: '+(error.exception?.description || error.text || JSON.stringify(error))+'; expression='+expression.slice(0,180));
  return message.result.result.value;
}
/* 預設為 Windows 的 Chrome；下列環境變數可覆寫，用於在 WSL/Linux 內整條跑：
     GEOMETRY_CHROME         chrome 執行檔路徑（Linux 下通常是 google-chrome）
     GEOMETRY_CHROME_PROFILE --user-data-dir 的位置
     GEOMETRY_CHROME_FLAGS   追加旗標，空白分隔（在 WSL 內以 root 跑需要 --no-sandbox）
     GEOMETRY_TEST_SERVER_PATH_STYLE=wsl  Windows harness 對 WSL 服務傳送 /mnt/<drive>/ 路徑
   不設時行為與先前完全相同。 */
const CHROME = process.env.GEOMETRY_CHROME || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PROFILE = process.env.GEOMETRY_CHROME_PROFILE || null;
const EXTRA_FLAGS = (process.env.GEOMETRY_CHROME_FLAGS || "").split(" ").filter(Boolean);
const PORT = +(process.env.GEOMETRY_CDP_PORT || 9333);
function serverFixturePath(localPath) {
  const style=process.env.GEOMETRY_TEST_SERVER_PATH_STYLE || 'native';
  if(style==='native')return localPath;
  if(style==='wsl'&&/^[A-Za-z]:[\\/]/.test(localPath))return '/mnt/'+localPath[0].toLowerCase()+'/'+localPath.slice(3).replace(/\\/g,'/');
  throw Error('Unsupported test server path style or fixture path: '+style+' '+localPath);
}

let chrome, browserEndpoint=null, browserStartupOutput='';
async function assertPortAvailable(port,network=net) {
  await new Promise((resolve,reject)=>{
    const probe=network.createServer();
    probe.once('error',error=>reject(Error('CDP port '+port+' is unavailable; refusing to attach to another browser: '+error.message)));
    probe.listen({host:'127.0.0.1',port,exclusive:true},()=>probe.close(error=>error?reject(error):resolve()));
  });
}
function verifyBrowserOwnership(version,endpoint,port) {
  const actual=new URL(version.webSocketDebuggerUrl),expected=new URL(endpoint);
  if(!['127.0.0.1','localhost','[::1]'].includes(actual.hostname) || actual.protocol!=='ws:' || Number(actual.port)!==port || Number(expected.port)!==port || !/^\/devtools\/browser\/[a-zA-Z0-9-]+$/.test(expected.pathname) || actual.pathname!==expected.pathname){
    const error=Error('CDP browser ownership mismatch: endpoint does not belong to the Chrome process started by this test');error.code='BROWSER_OWNERSHIP';throw error;
  }
}
function startBrowser() {
  const profile=PROFILE || fs.mkdtempSync(path.join(os.tmpdir(),'geometry-cdp-'));
  scope.browserProfile=path.resolve(profile);scope.cdpPort=PORT;
  const child=spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
  "--window-size=1400,900", `--user-data-dir=${profile}`, ...EXTRA_FLAGS, "about:blank"
  ]);
  child.stderr.on('data',chunk=>{
    browserStartupOutput=(browserStartupOutput+chunk.toString()).slice(-8192);
    const match=browserStartupOutput.match(/DevTools listening on (ws:\/\/\S+)/);
    if(match)browserEndpoint=match[1];
  });
  scope.browserPid=child.pid;
  return child;
}

const delay = ms => new Promise(r => setTimeout(r, ms));
const sleep = async ms => {
  await delay(ms);
  if(ms>=200 && ws?.readyState===1)
    await eval_('window.__cdpSettleUI?.(0)');
};
let ws, mid = 0, pending = {};

/* ✓/✗ 計數：所有印出的判定一律計入，exit code 依此決定。 */
let passN = 0, failN = 0;
let excN = 0;            /* Runtime.exceptionThrown 計數(BF2 驗收用) */
let currentTestStep='connecting to isolated test browser';
/* 每段斷言數(cdp_floor.js 的 sectionOf 由 `=== ` 標頭取主編號);CDP_RESULT.sections 與 golden 比對都用它。 */
let currentSection=floor.NO_SECTION;
const sectionPass={}, sectionFail={};
let expectedBeforeUnloadUntil=0;
let expectedNativeDialog=null;
let expectedException=null, scope, skipped=[];
const assetRequests=new Map(), assetFailures=[];
const _log = console.log;
function observeAssetNetwork(message) {
  const p=message.params,key=(message.sessionId||'main')+':'+p.requestId;
  if(message.method==='Network.requestWillBeSent'){
    let url;try {url=new URL(p.request.url);}catch{return;}
    if(url.origin!==new URL(scope.url).origin || (!['Script','Stylesheet'].includes(p.type)&&! /\.(?:js|css)$/i.test(url.pathname)))return;
    assetRequests.set(key,{url:url.href,type:p.type,requestId:p.requestId,sessionId:message.sessionId||null,step:currentTestStep,requestedAt:new Date().toISOString()});
    return;
  }
  const request=assetRequests.get(key);if(!request)return;
  let failure=null;
  if(message.method==='Network.responseReceived'&&p.response.status>=400)
    failure={...request,event:message.method,status:p.response.status,errorText:p.response.statusText,type:p.type||request.type};
  else if(message.method==='Network.loadingFailed')
    failure={...request,event:message.method,errorText:p.errorText,type:p.type||request.type,canceled:!!p.canceled,blockedReason:p.blockedReason||null};
  if(failure){assetFailures.push(failure);if(assetFailures.length>60)assetFailures.shift();_log('[NETWORK ASSET FAILURE]',JSON.stringify(failure));}
  if(message.method==='Network.loadingFinished'||message.method==='Network.loadingFailed')assetRequests.delete(key);
}
function recordLog(...args) {
  const s = args.join(" ");
  if(s.startsWith('===')){
    currentTestStep=s;
    currentSection=floor.sectionOf(s)||currentSection;
    sectionPass[currentSection]=sectionPass[currentSection]||0;
  }
  for(const passed of assertionVerdicts(args)){
    if(passed){passN++;sectionPass[currentSection]=(sectionPass[currentSection]||0)+1;}
    else{failN++;sectionFail[currentSection]=(sectionFail[currentSection]||0)+1;}
  }
  _log(...args.map(value=>value && typeof value==='object' && EXPLICIT_VERDICT in value?value.text:value));
}

async function connect() {
  // A fresh isolated Chrome profile can need longer than ten seconds on Windows.
  for (let i = 0; i < 120; ++i) {
    if(chrome.exitCode!==null)throw Error('Test Chrome exited before CDP ownership was established: '+browserStartupOutput);
    if(!browserEndpoint){await delay(250);continue;}
    try {
      const version=await fetch(`http://127.0.0.1:${PORT}/json/version`,{signal:AbortSignal.timeout(3000)}).then(r=>r.json());
      verifyBrowserOwnership(version,browserEndpoint,PORT);
      const list = await fetch(`http://127.0.0.1:${PORT}/json`,{signal:AbortSignal.timeout(3000)}).then(r => r.json());
      const page = list.find(t => t.type === "page" && t.url==='about:blank') || list.find(t => t.type === "page");
      if (page) {
        ws = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
        ws.onmessage = ev => {
          const m = JSON.parse(ev.data);
          if (m.id && pending[m.id]) { pending[m.id](m); delete pending[m.id]; }
          else if (['Network.requestWillBeSent','Network.responseReceived','Network.loadingFailed','Network.loadingFinished'].includes(m.method))observeAssetNetwork(m);
          else if (m.method === "Runtime.consoleAPICalled")
            console.log("[console]", m.params.args.map(a => a.value ?? a.description).join(" "));
          else if (m.method === "Runtime.exceptionThrown") {
            excN++;
            const description=m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text || '';
            const expected=expectedException && Date.now()<expectedException.until && description.split('\n')[0]===expectedException.message;
            if(expected){expectedException=null;_log('[EXPECTED EXCEPTION]',description);}
            else {failN++;_log('[UNEXPECTED EXCEPTION]',currentTestStep,description);}
          }
          else if (m.method === 'Page.javascriptDialogOpening' && expectedNativeDialog && m.params.type===expectedNativeDialog.type && m.params.message===expectedNativeDialog.message) {
            const expectation=expectedNativeDialog;expectedNativeDialog=null;expectation.seen=true;
            _log('[EXPECTED NATIVE DIALOG]',m.params.message,'accept='+expectation.accept);
            send('Page.handleJavaScriptDialog',{accept:expectation.accept},m.sessionId);
          }
          else if (m.method === 'Page.javascriptDialogOpening' && m.params.type==='confirm' &&
              /目前專案有尚未保存的變更|只能在本次工作階段修改數字的形狀特徵/.test(m.params.message)) {
            // This isolated acceptance run is authorized to leave its own test project.
            console.log('[TEST PROJECT DIALOG]',m.params.message);
            send('Page.handleJavaScriptDialog',{accept:true},m.sessionId);
          }
          else if (m.method==='Page.javascriptDialogOpening' && m.params.type==='beforeunload' && Date.now()<expectedBeforeUnloadUntil) {
            expectedBeforeUnloadUntil=0;
            console.log('[TEST PAGE LEAVE]',currentTestStep,m.params.message);
            send('Page.handleJavaScriptDialog',{accept:true},m.sessionId);
          }
          else if (m.method==='Page.javascriptDialogOpening') {
            const message='Unexpected native dialog at '+currentTestStep+': '+m.params.type+' '+m.params.message;
            console.log(explicitVerdict('✗ '+message),JSON.stringify(m.params));
            // Reject the unexpected action and terminate this run. Leaving a
            // native modal open would hang Runtime.evaluate indefinitely.
            send('Page.handleJavaScriptDialog',{accept:false},m.sessionId).then(()=>fatal(Error(message))).catch(fatal);
          }
          else if (m.method==='Inspector.targetCrashed')console.log(explicitVerdict('✗ Browser target crashed at '+currentTestStep));
        };
        return;
      }
    } catch(error) {if(error.code==='BROWSER_OWNERSHIP')throw error;}
    await sleep(250);
  }
  throw new Error("no CDP; Chrome startup output: " + browserStartupOutput);
}
function send(method, params = {}, sessionId = null) {
  if(method==='Page.reload'||method==='Page.navigate')expectedBeforeUnloadUntil=Date.now()+15000;
  return new Promise((res,rej) => {
    const id=++mid,timer=setTimeout(()=>{delete pending[id];rej(Error('CDP timed out: '+method+' at '+currentTestStep+(params.expression?' expression='+params.expression.slice(0,160):'')));},120000);
    pending[id]=message=>{clearTimeout(timer);if(message.error)rej(Error('CDP '+method+' failed: '+JSON.stringify(message.error)));else res(message);};
    ws.send(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})}));
  });
}
const eval_ = createRetainedEvaluator(send, evaluationValue);
async function waitForUI(expr, timeout=5000) {
  const end=Date.now()+timeout;
  while(Date.now()<end){if(await eval_(expr)===true)return;await sleep(50);}
  throw Error('UI condition timed out at '+currentTestStep+': '+expr);
}
async function expectNativeDialog(action,{message,accept,type='confirm'}) {
  if(expectedNativeDialog)throw Error('A native dialog expectation is already pending');
  const expected={message,accept,type,seen:false};expectedNativeDialog=expected;
  try {await action();if(!expected.seen)throw Error('Expected native dialog did not appear: '+message);}
  finally {if(expectedNativeDialog===expected)expectedNativeDialog=null;}
}
// Observe actual, newly appended DOM toasts during one action. Never read an
// earlier toast or replace toast()/its timers; retain evidence after expiry.
async function captureNewToasts(action, visibleState = 'null') {
  await eval_(`(()=>{
    if(window.__cdpActionToastProbe)throw Error('A toast observation is already active');
    const region=document.getElementById('toastRegion');if(!region)throw Error('Missing toastRegion');
    const seen=new WeakSet(region.querySelectorAll('.toast'));
    const probe=window.__cdpActionToastProbe={rows:[],frames:new Set(),active:true};
    probe.collect=records=>{for(const record of records)for(const node of record.addedNodes){
      if(node.nodeType!==1||!node.matches('.toast')||seen.has(node))continue;seen.add(node);
      const row={text:node.textContent,classes:[...node.classList],visible:false};probe.rows.push(row);
      const sample=()=>{const s=getComputedStyle(node),r=node.getBoundingClientRect();
        row.visible=row.visible||(node.isConnected&&s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)>0&&r.width>0&&r.height>0&&r.right>0&&r.bottom>0&&r.left<innerWidth&&r.top<innerHeight);
        if(row.visible&&!row.bounds){row.bounds={left:r.left,top:r.top,right:r.right,bottom:r.bottom};row.state=(${visibleState});}
        if(!row.visible&&node.isConnected&&probe.active){const id=requestAnimationFrame(()=>{probe.frames.delete(id);sample()});probe.frames.add(id);}};
      const id=requestAnimationFrame(()=>{probe.frames.delete(id);sample()});probe.frames.add(id);
    }};
    probe.observer=new MutationObserver(probe.collect);probe.observer.observe(region,{childList:true});return true;
  })()`);
  let observed;
  try {
    await action();
    // Synchronous actions also get a real paint opportunity. The bounded wait
    // only observes this probe's pending samples; it cannot invent a toast.
    await eval_(`(async()=>{const p=window.__cdpActionToastProbe;p.collect(p.observer.takeRecords());
      if(p.frames.size)await new Promise(resolve=>{let done=false,waitFrame=null;const finish=()=>{if(done)return;done=true;clearTimeout(timer);if(waitFrame!==null)cancelAnimationFrame(waitFrame);resolve()};
        const timer=setTimeout(finish,1000);const tick=()=>{waitFrame=null;if(done)return;if(!p.active||!p.frames.size)finish();else waitFrame=requestAnimationFrame(tick)};waitFrame=requestAnimationFrame(tick);});return true;})()`);
  }
  finally {
    observed=await eval_(`(()=>{const p=window.__cdpActionToastProbe;if(!p)throw Error('Toast observation was lost');
      p.collect(p.observer.takeRecords());p.observer.disconnect();p.active=false;for(const id of p.frames)cancelAnimationFrame(id);
      delete window.__cdpActionToastProbe;return p.rows;})()`);
  }
  return observed;
}
const toastText=(rows,type)=>rows.filter(t=>t.visible&&t.classes.includes(type)).map(t=>t.text).join(' | ');
async function click(x, y) {
  for (const [type, btn] of [["mousePressed", "left"], ["mouseReleased", "left"]])
    await send("Input.dispatchMouseEvent", { type, x, y, button: btn, clickCount: 1 });
}
// Persistent entries and relocated creation commands are exercised through the
// same visible menu a user opens, never by clicking a hidden DOM button.
async function clickControl(selector) {
  const menu=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});return e?.closest('#exampleMenuPop')?.hidden?'examples':e?.closest('#fileMenuPop')?.hidden?'file':e?.closest('#createObjectPop')?.hidden?'create':e?.closest('#filterDisclosure')&&!e.matches('summary')&&!e.closest('#filterDisclosure').open?'filter':null;})()`);
  if(menu==='create'){
    const trigger=await eval_(`(()=>{const visible=['mobileCreateObject','btnCreateObject'].filter(id=>{const e=document.getElementById(id),r=e?.getBoundingClientRect();return r&&r.width>0&&r.height>0;});if(visible.length!==1)throw Error('Expected one visible create-object opener: '+visible.join(','));return '#'+visible[0];})()`);
    await clickControl(trigger);
  }else if(menu==='examples')await clickControl('#exampleMenuBtn');
  else if(menu==='file')await clickControl('#fileMenuBtn');
  else if(menu==='filter')await clickControl('#filterDisclosure > summary');
  await eval_(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'nearest',inline:'nearest'});void 0`);
  let p;
  for(let n=0;n<12;n++){
    await sleep(70);
    p=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing control '+${JSON.stringify(selector)});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,w:r.width,h:r.height,hit:e.contains(document.elementFromPoint(x,y)),disabled:!!e.disabled};})()`);
    if(p.w&&p.h&&p.hit&&!p.disabled)break;
  }
  if(!p.w||!p.h||!p.hit||p.disabled)throw Error('Unreachable control '+selector+' '+JSON.stringify(p));
  await click(p.x,p.y);await sleep(150);
}
async function dblclick(x, y) {
  for (const n of [1, 2])
    for (const type of ["mousePressed", "mouseReleased"])
      await send("Input.dispatchMouseEvent", { type, x, y, button: "left", clickCount: n });
}
async function drag(x0, y0, x1, y1, steps = 6) {
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: x0, y: y0, button: "left", clickCount: 1 });
  for (let i = 1; i <= steps; ++i)
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x0 + (x1 - x0) * i / steps, y: y0 + (y1 - y0) * i / steps, button: "left" });
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: x1, y: y1, button: "left", clickCount: 1 });
}
/* GEO-192:帶 modifiers 的拖曳(CDP bitmask 同 pressKey:Alt=1、Ctrl=2、Meta=4、Shift=8),
   §P44-1/2/3 Alt+拖頂點捏缺口、§P44-4 拖預覽矩形邊都要用。 */
async function dragMod(x0, y0, x1, y1, steps = 6, modifiers = 0) {
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: x0, y: y0, button: "left", clickCount: 1, modifiers });
  for (let i = 1; i <= steps; ++i)
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x0 + (x1 - x0) * i / steps, y: y0 + (y1 - y0) * i / steps, button: "left", modifiers });
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: x1, y: y1, button: "left", clickCount: 1, modifiers });
}
/* GEO-192:放開拖曳但不放開按鍵(給 §P44-3 拖到一半按 Esc 用)。 */
async function pressDownMod(x0, y0, modifiers = 0) {
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: x0, y: y0, button: "left", clickCount: 1, modifiers });
}
async function moveMod(x, y, modifiers = 0) {
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y, button: "left", modifiers });
}
async function rightClick(x, y) {
  for (const type of ["mousePressed", "mouseReleased"])
    await send("Input.dispatchMouseEvent", { type, x, y, button: "right", clickCount: 1 });
}

/* 每段斷言數地板:完整模式與 golden 嚴格比對(差異 → failN 增加);部分模式只印不比。
   GEOMETRY_CDP_UPDATE_GOLDEN=1 才會重寫 golden(僅完整模式、且本次零失敗)。 */
const GOLDEN_PATH=path.join(__dirname,'cdp_sections.golden.json');
function evaluateSections() {
  const actual={sections:{...sectionPass}};
  const total=Object.values(actual.sections).reduce((a,b)=>a+b,0);
  const wantUpdate=process.env.GEOMETRY_CDP_UPDATE_GOLDEN;
  _log('CDP_SECTIONS '+Object.keys(actual.sections).length+' 段,合計 '+total+' 通過斷言');
  if(wantUpdate!==undefined && wantUpdate!=='1'){failN++;_log('[CDP FLOOR] GEOMETRY_CDP_UPDATE_GOLDEN 只接受 1');}
  if(scope.mode!=='full'){
    if(wantUpdate){failN++;_log('[CDP FLOOR] 部分模式不可更新 golden(golden 只記完整模式)');return 'update-refused (partial mode)';}
    _log('[CDP FLOOR] 部分模式,未比對 golden。各段通過數:'+JSON.stringify(actual.sections));
    return 'not compared (partial mode)';
  }
  if(wantUpdate==='1'){
    if(failN>0){_log('[CDP FLOOR] 本次有失敗斷言,不更新 golden');return 'update-refused (failures)';}
    fs.writeFileSync(GOLDEN_PATH,JSON.stringify(floor.buildGolden(actual.sections),null,2)+'\n');
    _log('[CDP FLOOR] 已重寫 '+GOLDEN_PATH+'(請檢視 git diff 後再提交)');
    return 'golden updated';
  }
  let golden;
  try {golden=JSON.parse(fs.readFileSync(GOLDEN_PATH,'utf8'));}
  catch(error){failN++;_log('[CDP FLOOR] 讀不到 golden '+GOLDEN_PATH+':'+error.message+'(以 GEOMETRY_CDP_UPDATE_GOLDEN=1 建立)');return 'golden unreadable';}
  const problems=floor.validateGolden(golden);
  if(problems.length){failN++;for(const problem of problems)_log('[CDP FLOOR] golden 格式錯誤:'+problem);return 'golden invalid';}
  const diffs=floor.compare(golden,actual);
  for(const diff of diffs){failN++;_log('[CDP FLOOR]',diff.message);}
  if(diffs.length)return 'mismatch ('+diffs.length+')';
  _log('[CDP FLOOR] 與 golden 逐段相符('+Object.keys(golden.sections).length+' 段)');
  return 'matched';
}

async function main() {
  await connect();
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Network.enable");
  // A reused Chrome profile can restore a narrow window. Pin the desktop
  // baseline explicitly; responsive cases restore this same viewport.
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  // Observe async UI completion without changing application behavior. A fixed 300–400 ms
  // pause was reading between a committed command and its subsequent inspector refresh.
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`(()=>{
    let pending=0,last=performance.now();const original=window.fetch.bind(window);
    window.fetch=(...args)=>{pending++;last=performance.now();return original(...args).finally(()=>{pending--;last=performance.now();});};
    const observer=new MutationObserver(()=>{last=performance.now();});
    document.addEventListener('DOMContentLoaded',()=>observer.observe(document.body,{subtree:true,childList:true,attributes:true,characterData:true}));
    window.__cdpSettleUI=async ms=>{
      await new Promise(r=>setTimeout(r,ms));const end=performance.now()+5000;
      while(performance.now()<end){if(pending===0&&performance.now()-last>=150)return;await new Promise(r=>setTimeout(r,50));}
      // Opportunistic settling only: some race tests deliberately keep a fetch
      // pending. Their explicit waitForUI predicate/assertion is authoritative.
    };
  })()`});
  await send("Page.navigate", { url: process.env.GEOMETRY_TEST_URL || "http://localhost:8765/" });
  await waitForUI(`typeof api==='function' && typeof oc==='object' && connection.phase==='ready'`,30000);
  if (!await eval_(`typeof api==='function' && typeof oc==='object' && connection.phase==='ready'`))
    throw Error('Application did not finish loading: '+JSON.stringify(await eval_(`({state:document.readyState,url:location.href,api:typeof api,message:document.querySelector('#connectionMessage')?.textContent})`)));
  if (!process.env.GEOMETRY_ROOM_OUTLINE_ONLY) {
  if (!process.env.GEOMETRY_PARAMETERS_ONLY && !process.env.GEOMETRY_ASSEMBLY_ONLY && !process.env.GEOMETRY_TIMBER_SCHEDULE_ONLY) {
  if (!process.env.GEOMETRY_SELECTION_CURSOR_ONLY && !process.env.GEOMETRY_UX_REFINEMENT_ONLY && !process.env.GEOMETRY_UIUX_FIX_ONLY && !process.env.GEOMETRY_MARQUEE_ONLY && !process.env.GEOMETRY_PROJECT_AUDIT_ONLY && !process.env.GEOMETRY_ENGINEERING_WORKFLOW_ONLY && !process.env.GEOMETRY_GRID_SYSTEM_ONLY && !process.env.GEOMETRY_INFINITE_FACE_ONLY && !process.env.GEOMETRY_COMPOSITION_ONLY) {
  if (!process.env.GEOMETRY_UI_REVIEW_ONLY && !process.env.GEOMETRY_REPAIR_ONLY && !process.env.GEOMETRY_FLOW_REPAIR_ONLY && !process.env.GEOMETRY_REFERENCE_ONLY && !process.env.GEOMETRY_CDP_FROM_P31) {
  /* 清世界 + 建一個乾淨的測試場：一片游離面、一個空容器 */
  console.log('=== Setup. 確認重置隔離驗收專案 ===');
  await eval_(`window.__cdpInitialResetDone=false;window.__cdpInitialReset=api('line reset').then(r=>{window.__cdpInitialResetDone=true;return r;});void 0`);
  await waitForUI(`window.__cdpInitialResetDone || !!document.querySelector('.reference-impact[open] #impact-confirm')`,15000);
  if(await eval_(`!!document.querySelector('.reference-impact[open] #impact-confirm')`)){
    const point=await eval_(`(()=>{const e=$('impact-confirm');e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,hit:e.contains(document.elementFromPoint(x,y)),disabled:e.disabled};})()`);
    if(!point.hit||point.disabled)throw Error('Initial isolated reset confirmation is unreachable '+JSON.stringify(point));
    console.log('[TEST FIXTURE RESET] confirming the isolated project impact preview');
    await click(point.x,point.y);
  }
  const initialReset=await eval_(`window.__cdpInitialReset`);
  if(!initialReset?.ok)throw Error('Initial isolated reset failed '+JSON.stringify(initialReset));
  await eval_(`delete window.__cdpInitialReset;delete window.__cdpInitialResetDone;void 0`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`api("line canvas-pos boundary 1 60 60")`);
  await sleep(500);

  console.log("=== 1. Phase 1 版面檢查點(§6) ===");
  /* (a) 固定頂列、工作區、狀態列；浮動選單不計入排版列。 */
  const rows = await eval_(`(()=>{const app=document.getElementById("app");
    const kids=[app.querySelector(':scope > .topbar'),app.querySelector(':scope > .workspace'),app.querySelector(':scope > .statusbar')];return {n:kids.filter(Boolean).length,
      cls:kids.map(k=>k.className.split(" ")[0]).join(","),
      h:kids.map(k=>Math.round(k.getBoundingClientRect().height))}})()`);
  console.log("app rows:", JSON.stringify(rows),explicitVerdict(rows.n === 3 && rows.h[0] === 56 && rows.h[2] === 28 ? "✓ 三列殼" : "✗"));
  /* (b) 主畫布不再保留空白右欄，物件庫與畫布共用完整寬度。 */
  const cols = await eval_(`(()=>{const w=document.querySelector(".workspace");
    const l=w.querySelector('.sidebar-left').getBoundingClientRect(),c=$('canvasViewport').getBoundingClientRect();return {left:l.width,leftRight:l.right,canvasLeft:c.left,canvasRight:c.right,canvasWidth:c.width,iw:innerWidth,composition:document.body.classList.contains('canvas-composition'),hasInspector:document.body.classList.contains('canvas-has-inspector')};})()`);
  console.log("workspace composition:",JSON.stringify(cols),explicitVerdict(cols.composition&&!cols.hasInspector&&cols.left>0&&Math.abs(cols.leftRight-cols.canvasLeft)<=2&&Math.abs(cols.canvasRight-cols.iw)<=2&&cols.canvasWidth>cols.iw/2?'✓ 物件庫與完整畫布':'✗'));
  /* (c) 專案頂列與畫布浮動工具列分工。 */
  const tb = await eval_(`!!document.querySelector('.topbar > .brand') && !!document.querySelector('.topbar > .top-actions') && $('canvasDrawToolbar').closest('#canvasViewport')!==null && !$('canvasDrawToolbar').closest('.topbar')`);
  console.log("topbar / canvas tools:",explicitVerdict(tb?'✓ 專案列與畫布工具分開':'✗'));
  /* (d) #ocv 在 #canvasViewport 內且同大小(誤差≤2px) */
  const fit = await eval_(`(()=>{const v=document.getElementById("canvasViewport").getBoundingClientRect();
    const o=document.getElementById("ocv").getBoundingClientRect();
    return {dv:Math.abs(v.left-o.left)+Math.abs(v.top-o.top),
            ds:Math.abs(v.width-o.width)+Math.abs(v.height-o.height)}})()`);
  console.log("ocv fit:", JSON.stringify(fit),explicitVerdict(fit.dv <= 2 && fit.ds <= 2 ? "✓ ocv 鋪滿 viewport" : "✗"));
  /* (e) #status 與 #cmd 都在 .statusbar 裡 */
  const sb = await eval_(`(()=>{const sb=document.querySelector(".statusbar");
    return !!(sb.querySelector("#status") && sb.querySelector("#cmd"))})()`);
  console.log("statusbar:",explicitVerdict(sb ? "✓ status/cmd 在狀態列" : "✗"));
  /* (f) 各寬度頂列控制與浮動工具皆可見、可點且不互相遮擋。 */
  for (const w of [1382, 1160, 900, 680, 600]) {
    await send("Emulation.setDeviceMetricsOverride",
      { width: w, height: 804, deviceScaleFactor: 1, mobile: false });
    await sleep(350);
    const ov = await eval_(`(()=>{
      const top=document.querySelector('.topbar').getBoundingClientRect(),tools=$('canvasDrawToolbar').getBoundingClientRect();
      const buttons=[...document.querySelectorAll('.topbar button,#canvasDrawToolbar button')].filter(e=>e.getBoundingClientRect().width>0&&getComputedStyle(e).visibility!=='hidden').map(e=>{const r=e.getBoundingClientRect();return {id:e.id||e.dataset.tool,fit:r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight,hit:e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))};});return {toolsBelowHeader:tools.top>=top.bottom-1,buttons};})()`);
    console.log(`防溢出@${w}:`,JSON.stringify(ov),explicitVerdict(ov.toolsBelowHeader&&ov.buttons.length>6&&ov.buttons.every(b=>b.fit&&b.hit)?'✓':'✗'));
  }
  await send("Emulation.setDeviceMetricsOverride",
    { width: 1382, height: 804, deviceScaleFactor: 1, mobile: false });
  await sleep(300);
  /* (g) S2 結構:搜尋在左欄;fileMenu 含四鈕;viewSwitch 含 btnObj */
  const s2 = await eval_(`({
    searchInSide: !!document.querySelector(".sidebar-left #searchInput"),
    fileKids: ["btnOpen","btnDatums","btnEx","btnClear"].every(id=>
      document.getElementById("fileMenu").contains(document.getElementById(id))),
    vsHasObj: document.getElementById("viewSwitch").contains(document.getElementById("btnObj")),
    zoomInCtl: document.querySelector(".canvas-controls").contains(document.getElementById("btnZoom")),
    kbd: document.querySelectorAll(".tool-group kbd").length
  })`);
  console.log("S2 結構:", JSON.stringify(s2),explicitVerdict(s2.searchInSide && s2.fileKids && s2.vsHasObj && s2.zoomInCtl && s2.kbd === 4 ? "✓" : "✗"));
  /* (h) A2 清單樣式:.row-copy > strong + small */
  await eval_(`renderObjects()`); await sleep(400);
  const rowCk = await eval_(`(()=>{const r=document.querySelector(".object-row .row-copy strong");
    return r ? getComputedStyle(r).fontSize : null})()`);
  console.log("清單樣式 row-copy strong:", rowCk,explicitVerdict(rowCk && parseFloat(rowCk) >= 12 ? "✓" : "✗"));
  /* (i) E8:800px 寬進面內工作區,工具列仍有不少於 5 顆可見鈕 */
  await send("Emulation.setDeviceMetricsOverride",
    { width: 800, height: 600, deviceScaleFactor: 1, mobile: false });
  await eval_(`enterFocus("face",1)`); await sleep(600);
  const e8 = await eval_(`[...document.querySelectorAll("#faceWorkspaceTools .workspace-tool")]
    .filter(b=>b.getBoundingClientRect().width>0).length`);
  console.log("E8 800px 面內工具鈕:", e8,explicitVerdict(e8 >= 5 ? "✓" : "✗"));
  await eval_(`leaveFocus()`); await sleep(300);
  await send("Emulation.setDeviceMetricsOverride",
    { width: 1382, height: 804, deviceScaleFactor: 1, mobile: false });
  await sleep(300);
  /* 截圖存檔 */
  const shot = await send("Page.captureScreenshot", { format: "png" });
  const screenshotPath = process.env.GEOMETRY_TEST_SCREENSHOT || path.join(os.tmpdir(),'geometry-tests','cdp-'+process.pid,'phase1-shell.png');
  fs.mkdirSync(path.dirname(screenshotPath),{recursive:true});
  require("fs").writeFileSync(screenshotPath, Buffer.from((shot.result && shot.result.data) || "", "base64"));
  console.log("screenshot:", screenshotPath);
  /* 牙齒:存檔不等於截到圖——讀回剛寫的檔,必須非空且以 PNG 簽名(89 50 4E 47)開頭。 */
  const shotBytes = fs.readFileSync(screenshotPath);
  console.log("screenshot PNG:", shotBytes.length, "bytes", explicitVerdict(shotBytes.length > 8 && shotBytes.subarray(0, 4).equals(Buffer.from([0x89, 0x50, 0x4E, 0x47])) ? "✓ 截圖非空且為 PNG" : "✗ 截圖為空或不是 PNG"));
  console.log("初始:oc.on=", await eval_(`oc.on`),
    "ocv.hidden=", await eval_(`document.getElementById("ocv").hasAttribute("hidden")`),
    "cv.hidden=", await eval_(`document.getElementById("cv").hasAttribute("hidden")`),
    "cards=", await eval_(`document.querySelectorAll(".ocard").length`));

  console.log("=== 2. 三視圖覆層開/關 ===");
  const btnRect = await eval_(`(()=>{const r=document.getElementById("btnObj").getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
  await click(btnRect.x, btnRect.y);
  await sleep(1000);
  const v3on = await eval_(`({cv:document.getElementById("cv").hasAttribute("hidden"),
    vt:document.getElementById("viewToolbar").hasAttribute("hidden"),on:oc.on,
    world:document.getElementById("world").childElementCount})`);
  console.log("view3 open:", JSON.stringify(v3on),explicitVerdict(!v3on.cv && !v3on.vt && !v3on.on ? "✓ 三視圖開啟" : "✗"));
  await click(btnRect.x, btnRect.y);
  await sleep(300);
  console.log("view3 repeated selection:",explicitVerdict(!(await eval_(`oc.on`)) ? "✓ 維持三視圖" : "✗"));
  const canvasButton = await eval_(`(()=>{const r=document.getElementById("btnCanvasView").getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
  await click(canvasButton.x, canvasButton.y);
  await sleep(700);
  const v3off = await eval_(`({cv:document.getElementById("cv").hasAttribute("hidden"),on:oc.on})`);
  console.log("view3 close:", JSON.stringify(v3off),explicitVerdict(v3off.cv && v3off.on ? "✓ 返回物件畫布" : "✗"));
  console.log("cards:", await eval_(`document.querySelectorAll(".ocard").length`));

  console.log("=== 3. H 平移工具拖曳空白處（GEO-209：V 空白拖曳改為框選） ===");
  const ocvRect = await eval_(`JSON.stringify(document.getElementById("ocv").getBoundingClientRect())`);
  console.log("ocv rect:", ocvRect);
  const panBefore = await eval_(`({x:oc.panX,y:oc.panY})`);
  /* 找 ocv 內避開卡片的空白點 */
  const panPt = await eval_(`(()=>{
    const r = document.getElementById("ocv").getBoundingClientRect();
    const boxes = [...document.querySelectorAll(".ocard")].map(c => c.getBoundingClientRect());
    for (let y = r.top + 60; y < r.bottom - 60; y += 40)
      for (let x = r.left + 60; x < r.right - 60; x += 40)
        if (boxes.every(b => x < b.left - 20 || x > b.right + 20 ||
                             y < b.top - 20 || y > b.bottom + 20))
          return {x, y};
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  console.log("pan pt:", JSON.stringify(panPt));
  for (const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{type,key:'h',code:'KeyH',windowsVirtualKeyCode:72});
  await drag(panPt.x, panPt.y, panPt.x + 80, panPt.y + 50);
  for (const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{type,key:'v',code:'KeyV',windowsVirtualKeyCode:86});
  const panAfter = await eval_(`({x:oc.panX,y:oc.panY})`);
  console.log("pan:", JSON.stringify(panBefore), "->", JSON.stringify(panAfter),explicitVerdict(panBefore.x !== panAfter.x ? "✓ 平移有效" : "✗ 平移無效"));

  console.log("=== 4. 點「＋面·矩形」再拉矩形（避開卡片的空白區） ===");
  await eval_(`document.getElementById("btnNewRect").click()`);
  await sleep(200);
  const facesBefore = await eval_(`oc.faces.length`);
  /* 找出空白處：避開所有卡片的螢幕範圍 */
  const empty = await eval_(`(()=>{
    const r = document.getElementById("ocv").getBoundingClientRect();
    const boxes = [...document.querySelectorAll(".ocard")].map(c => c.getBoundingClientRect());
    for (let y = r.top + 60; y < r.bottom - 60; y += 30)
      for (let x = r.left + 60; x < r.right - 160; x += 30)
        if (boxes.every(b => x < b.left - 40 || x > b.right + 160 ||
                             y < b.top - 40 || y > b.bottom + 110))
          return {x, y};
    return {x: r.right - 200, y: r.bottom - 150};
  })()`);
  console.log("empty pt:", JSON.stringify(empty));
  /* 探針：看 pointerdown 是否真的送達 ocv，以及 target/button 是什麼 */
  await eval_(`window.__pd = null; ocv.addEventListener("pointerdown",
    e => window.__pd = { b: e.button, t: e.target.tagName, cls: e.target.getAttribute("class"),
                         x: e.clientX, y: e.clientY }, true)`);
  console.log("elementFromPoint:", await eval_(
    `(()=>{const e=document.elementFromPoint(${empty.x},${empty.y});return e?e.tagName+"#"+e.id+"."+(e.getAttribute("class")||""):"null"})()`));
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: empty.x, y: empty.y, button: "left", clickCount: 1 });
  await sleep(150);
  console.log("probe:", await eval_(`JSON.stringify(window.__pd)`));
  console.log("after down: drawTool=", await eval_(`oc.drawTool`),
              "rect=", await eval_(`JSON.stringify(oc.rect)`),
              "card=", await eval_(`JSON.stringify(oc.card)`),
              "pan=", await eval_(`JSON.stringify(oc.pan)`));
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: empty.x + 70, y: empty.y + 45, button: "left" });
  await sleep(150);
  console.log("after move: rect=", await eval_(`JSON.stringify(oc.rect)`));
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: empty.x + 140, y: empty.y + 90, button: "left", clickCount: 1 });
  await sleep(1500);
  const facesAfter = await eval_(`oc.faces.length`);
  console.log("faces:", facesBefore, "->", facesAfter,explicitVerdict(facesAfter > facesBefore ? "✓ 建面成功" : "✗ 建面失敗"));
  console.log("status:", await eval_(`document.getElementById("status").textContent`));
  console.log("cards:", await eval_(`document.querySelectorAll(".ocard").length`));

  console.log("=== 5. 拖卡片（應寫 canvas-pos，不進入） ===");
  // The earlier rectangle may overlap the first card. Keep the original target
  // and require a real, unobstructed header hit before dispatching the gesture.
  const cardBox = await eval_(`(()=>{
    const c = document.querySelector('#ocv .ocard[data-kind="boundary"][data-id="1"]');
    if (!c || c !== document.querySelector('#ocv .ocard')) throw Error('P5: original boundary:1 card missing');
    const local = ocFind(c.dataset.kind, +c.dataset.id);
    if (!local) throw Error('P5: original boundary:1 record missing');
    const frame = c.querySelector('.ocard-frame').getBBox(), matrix = c.getScreenCTM();
    const viewport = document.querySelector('#ocv').getBoundingClientRect(), attempts = [];
    const interactive = 'button,a,input,select,textarea,summary,[role="button"],[role="link"],[contenteditable]:not([contenteditable="false"]),[data-insp-scroll],.card-enter';
    for (const y of [20, 32, 42]) for (const fraction of [0.5, 0.625, 0.75, 0.85, 0.9]) {
      const point = new DOMPoint(frame.x + frame.width * fraction, y).matrixTransform(matrix);
      const hit = document.elementFromPoint(point.x, point.y), card = hit?.closest('.ocard');
      const focusable = hit?.closest('[tabindex]');
      const valid = point.x >= viewport.left && point.x < viewport.right && point.y >= viewport.top && point.y < viewport.bottom && card === c && !hit.closest(interactive) && !(focusable && c.contains(focusable) && focusable.tabIndex >= 0);
      attempts.push({x:point.x,y:point.y,hitKind:card?.dataset.kind,hitId:card?.dataset.id,valid});
      if (valid) return {x:point.x,y:point.y,kind:c.dataset.kind,id:+c.dataset.id,cx:local.cx,cy:local.cy,attempts};
    }
    throw Error('P5: original card has no reachable noninteractive header point: '+JSON.stringify(attempts));
  })()`);
  console.log('P5 pointer precondition', JSON.stringify(cardBox));
  if (cardBox) {
    const posBefore = await eval_(`JSON.stringify(oc.faces.map(f=>[f.id,f.cx,f.cy]))`);
    await drag(cardBox.x, cardBox.y, cardBox.x + 120, cardBox.y + 60);
    const commit = await cdp.waitCardCanvasPos(eval_, {kind:cardBox.kind, id:cardBox.id, beforeCx:cardBox.cx, beforeCy:cardBox.cy});
    const posAfter = await eval_(`JSON.stringify(oc.faces.map(f=>[f.id,f.cx,f.cy]))`);
    console.log("card pos:", posBefore, "->", posAfter,explicitVerdict(commit.ok && posBefore !== posAfter ? "✓ 拖卡片有效" : "✗ 拖卡片無效"), JSON.stringify(commit));
  }

  console.log("=== 6. 點卡=選取(檢視器);雙擊=進入面編輯 ===");
  const cardPt = await eval_(`(()=>{
    const cards = [...document.querySelectorAll(".ocard")];
    const c = cards[cards.length - 1];   /* 最後建的游離面 */
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  console.log("card pt:", JSON.stringify(cardPt));
  if (cardPt) {
    await click(cardPt.x, cardPt.y);
    await sleep(600);
    const sel = await eval_(`JSON.stringify(oc.sel)`);
    console.log("click sel:", sel,explicitVerdict(JSON.parse(sel) ? "✓ 單擊選取" : "✗"),
      "| inspector hidden:", await eval_(`document.getElementById("inspectorContent").hidden`));
    console.log("focus(應為 null):", await eval_(`JSON.stringify(oc.focus)`));
    await dblclick(cardPt.x, cardPt.y);
    await sleep(1000);
    console.log("focus:", await eval_(`JSON.stringify(oc.focus)`));
    console.log("status:", await eval_(`document.getElementById("status").textContent`));
  }

  console.log("=== 7. 面編輯：拖一個頂點 ===");
  console.log("workspace open:", await eval_(
    `!document.getElementById("objectWorkspace").hidden`));
  const vtx = await eval_(`(()=>{
    if (!oc.focus || oc.focus.t !== "face" || !oc.edit) return null;
    const e = oc.edit, loops = oc.bmap[e.bid];
    if (!loops || !loops[0].verts.length) return null;
    const p = loops[0].verts[0];
    const r = document.getElementById("faceEditorSvg").getBoundingClientRect();
    return { x: r.left + p[0]*fe.zoom + fe.panX, y: r.top + p[1]*fe.zoom + fe.panY };
  })()`);
  if (vtx) {
    const vBefore = await eval_(`JSON.stringify(oc.bmap[oc.edit.bid][0].verts[0])`);
    await drag(vtx.x, vtx.y, vtx.x + 60, vtx.y + 40);
    await sleep(1200);
    const vAfter = await eval_(`JSON.stringify(oc.bmap[oc.edit.bid][0].verts[0])`);
    console.log("vert0:", vBefore, "->", vAfter,explicitVerdict(vBefore !== vAfter ? "✓ 頂點編輯有效" : "✗ 頂點編輯無效"));
    console.log("status:", await eval_(`document.getElementById("status").textContent`));
  } else console.log("沒進入面編輯，跳過");

  console.log("=== 8. Esc 返回世界 ===");
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(500);
  console.log("focus after Esc:", await eval_(`JSON.stringify(oc.focus)`));

  console.log("=== 9. 「＋空間」建空容器 ===");
  const spBefore = await eval_(`oc.spaces.length`);
  await clickControl('#btnNewSpace');
  await sleep(1500);
  const spAfter = await eval_(`oc.spaces.length`);
  console.log("spaces:", spBefore, "->", spAfter,explicitVerdict(spAfter > spBefore ? "✓ 空間建立成功" : "✗ 失敗"));
  console.log("status:", await eval_(`document.getElementById("status").textContent`));
  console.log("newid:", await eval_(`api("newid").then(r=>JSON.stringify(r))`));

  console.log("=== 9b. 點空間卡進入成員層 ===");
  const spPt = await eval_(`(()=>{
    const c = [...document.querySelectorAll(".ocard")].find(c => c.dataset.kind === "space");
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  if (spPt) {
    await dblclick(spPt.x, spPt.y);
    await sleep(800);
    console.log("focus:", await eval_(`JSON.stringify(oc.focus)`),explicitVerdict(await eval_(`oc.focus && oc.focus.t === "space" ? "✓" : "✗"`)));
    await eval_(`leaveFocus()`); await sleep(300);
  }

  console.log("=== 9c. 「＋面·多邊形」建面卡→面內畫外環(GEO-186 b) ===");
  /* GEO-186(b,2026-09-24 拍板):P 不再是畫布上的 mm 繪圖工具——同一張畫布混用
     「mm 繪圖」與「固定尺寸卡片排版」兩套座標是 GEO-187「找不到卡片」的根因。
     按一下 = 建預設外環的面卡 → 直接進入該面工作區並啟用「重畫外環」,
     在面內以實際 mm 逐點畫。面內繪圖機制另有 §P35/P36 專門斷言。 */
  await eval_(`oc.zoom=1;oc.panX=0;oc.panY=0;ocApply()`);
  const fb2 = await eval_(`oc.faces.length`);
  await eval_(`document.getElementById("btnNewPoly").click()`);
  await sleep(900);
  const fa2 = await eval_(`oc.faces.length`);
  const ws9 = await eval_(`({focus:oc.focus, tool:fe.tool})`);
  console.log("faces:", fb2, "->", fa2,explicitVerdict(fa2 > fb2 ? "✓ 建面成功" : "✗ 失敗"),
    "| 自動進面內:",explicitVerdict(ws9.focus && ws9.focus.t === "face" ? "✓" : "✗"),
    "| 重畫外環就緒:",explicitVerdict(ws9.tool === "redraw" ? "✓" : "✗ " + ws9.tool));
  console.log("status:", await eval_(`document.getElementById("status").textContent`));
  /* Esc 回物件畫布,讓 9d 在畫布上驗 undo/redo(單次 undo 移除整個建面交易) */
  for (const type of ['keyDown','keyUp'])
    await send('Input.dispatchKeyEvent', { type, key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await sleep(500);
  console.log("Esc 回畫布:",explicitVerdict((await eval_(`oc.focus`)) === null ? "✓" : "✗"));

  console.log("=== 9d. Ctrl+Z 復原 / Ctrl+Y 重做 ===");
  /* §5.A.1.15 已知風險,實測後更新(2026-09-22):新 objEmitFace 閉合當下直接算 bbox
     左上送 canvas-pos，不再落入 renderObjects() 的 homeless 自動排格分支；而
     `canvas-pos` 本身不進 undo 歷史(DOM-CONTRACT.md「canvas-pos 是展示中繼資料，
     不進歷史」/ canvas_test.js U1/L1 既有斷言)，所以「建 boundary」+「送 canvas-pos」
     不再是兩筆各自要復原的交易——實測(本檔案 2026-09-22 一併驗證,見下方單步 undo/redo)
     單次 Ctrl+Z 就讓面連同座標一起消失、單次 Ctrl+Y 就完整還原。HEAD 舊註解「undo 兩次
     才回到面消失」的假設在這版 objEmitFace 下不成立,依規則更新。
     不测「再按一次應不變」:§9 建立過的空間也在同一份 undo 歷史裡,多按一次 undo/redo
     會動到空間那筆交易(不影響 oc.faces.length,但也不是嚴格「無事發生」),用 dump 比對
     世界整體是否精確復原比只看 face 數更準確、也更貼近規格意圖。 */
  const facesN = `oc.faces.length`;
  const fPreUndo = await eval_(facesN);
  const dumpPreUndo = (await eval_(`api("dump").then(r=>r.text)`));
  const key = async (k, code, vk) => {
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, modifiers: 2, windowsVirtualKeyCode: vk });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, modifiers: 2, windowsVirtualKeyCode: vk });
  };
  await key("z", "KeyZ", 90); await sleep(800);
  const fU1 = await eval_(facesN);
  const st1 = await eval_(`document.getElementById("status").textContent`);
  console.log("undo1 api faces:", await eval_(`api("objects").then(r=>r.faces.length)`));
  console.log("undo×1(單步移除建面+落點):", fPreUndo, "->", fU1,explicitVerdict(fU1 === fPreUndo - 1 ? "✓ undo 有效" : "✗"), "|", st1);
  await key("y", "KeyY", 89); await sleep(800);
  const fR1 = await eval_(facesN);
  const dumpAfterRedo = (await eval_(`api("dump").then(r=>r.text)`));
  console.log("redo×1(單步還原):", fU1, "->", fR1,explicitVerdict(fR1 === fPreUndo ? "✓ redo 有效" : "✗"));
  console.log("redo 後世界與 undo 前逐字相同:",explicitVerdict(dumpAfterRedo === dumpPreUndo ? "✓" : "✗"));

  console.log("=== 9e. contains 連線(edgeGroup) ===");
  /* 空間成員必須是有承載面的邊界面:先用 surface 建地板+牆(區間一致),
     再用 #cmd 送 space 1 boundary 10 11 → edgeGroup 應有 2 條邊 */
  const cmdLine = async t => {
    await eval_(`(()=>{const c=document.getElementById("cmd");
      c.value=${JSON.stringify("X")}.replace("X",${JSON.stringify(t)});
      c.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter",bubbles:true}))})()`);
    await sleep(600);
  };
  await cmdLine("surface 10 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000");
  await cmdLine("surface 11 origin 0 0 0 u +x v +z outline 0,0 4000,0 4000,2500 0,2500");
  await cmdLine("space 1 boundary 10 11");
  await sleep(1200);
  console.log("space members:", await eval_(
    `api("objects").then(r=>JSON.stringify(r.spaces.map(s=>[s.id,s.members])))`));
  const edgeN = await eval_(`document.querySelectorAll("#edgeGroup .edge-path").length`);
  console.log("edges:", edgeN,explicitVerdict(edgeN === 2 ? "✓ contains 邊×2" : "✗"));
  console.log("edge labels:", await eval_(
    `[...document.querySelectorAll("#edgeLabelLayer .edge-label")].map(t=>t.textContent).join(",")`));

  console.log("=== 9f. 搜尋過濾 ===");
  const cardsAll = await eval_(`document.querySelectorAll(".ocard").length`);
  await eval_(`(()=>{const si=document.getElementById("searchInput");
    si.value="面 1";si.dispatchEvent(new Event("input",{bubbles:true}))})()`);
  await sleep(600);
  const cardsQ = await eval_(`document.querySelectorAll(".ocard").length`);
  console.log("cards:", cardsAll, "->", cardsQ,explicitVerdict(cardsQ === 1 ? "✓ 搜尋只剩 1 張卡" : "✗"));
  const listQ = await eval_(`document.querySelectorAll("#objectList .object-row").length`);
  console.log("list rows:", listQ,explicitVerdict(listQ === 1 ? "✓ 清單同步過濾" : "✗"));
  /* 清掉搜尋 */
  await eval_(`(()=>{const si=document.getElementById("searchInput");
    si.value="";si.dispatchEvent(new Event("input",{bubbles:true}))})()`);
  await sleep(400);

  /* ================= Phase 3：面內工作區 ================= */
  console.log("=== P3-1. 已放置面（天花 surface 20）進入工作區 ===");
  await cmdLine("surface 20 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
  await sleep(800);
  await clickControl('#btnZoom');
  const card20 = await eval_(`(()=>{
    const c = document.querySelector('.ocard[data-id="20"]');
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  console.log("card20:", JSON.stringify(card20));
  if (card20) {
    await dblclick(card20.x, card20.y);
    await sleep(1000);
    console.log("focus:", await eval_(`JSON.stringify(oc.focus)`),explicitVerdict(await eval_(`oc.focus && oc.focus.t==="face" && oc.focus.id===20 ? "✓ 進入面 20" : "✗"`)));
    console.log("workspace:",explicitVerdict(await eval_(
      `!document.getElementById("objectWorkspace").hidden ? "✓ 開啟" : "✗ 未開啟"`)));
  }

  console.log("=== P3-2. 參考線：水平拖 → guide <n> 20 v <off> ===");
  await eval_(`document.querySelector('[data-face-tool="guide"]').click()`);
  await sleep(300);
  const feCtr = await eval_(`(()=>{
    const r = document.getElementById("faceEditorViewport").getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  const dumpBeforeDrag = await eval_(`api("dump").then(r=>r.text)`);
  /* 牙齒:拖放真的走到「snap 拒絕」路徑才會彈出 R5 toast;拖放若根本沒發生,下面的「dump 沒有 guide 行」照綠,
     所以要另外觀察這次拖放必然產生的可見 toast(reference_bridge.inc 的 snap 訊息)。 */
  const freeDragToasts = await captureNewToasts(async()=>{
    await drag(feCtr.x - 80, feCtr.y, feCtr.x + 80, feCtr.y + 4);   /* 水平拖 → v 線 */
    await sleep(900);
  });
  const dump1 = await eval_(`api("dump").then(r=>r.text)`);
  const rawGuide = /^guide /m.test(dump1);
  console.log("無具名規格或鄰近引用的自由拖放拒絕:",explicitVerdict(!rawGuide ? "✓" : "✗"));
  const freeDragToastText = freeDragToasts.filter(t=>t.visible).map(t=>t.text).join(' | ');
  console.log("自由拖放被拒的正向證據(R5 toast,世界不變):",JSON.stringify(freeDragToastText),explicitVerdict(freeDragToastText.includes('R5') && freeDragToastText.includes('附近沒有合法引用') && dump1 === dumpBeforeDrag ? "✓" : "✗"));
  await eval_(`(async()=>{await api("line spec 面內線 1500"); await api("line guide 1 20 u spec:面內線"); await feLoadGuides();drawFaceEditor()})()`);
  const gMatch = await eval_(`api('references').then(r=>r.guides.find(g=>g.surface===20))`);
  console.log("引用建線:",explicitVerdict(gMatch?.expression === 'spec:面內線' && gMatch.off === 1500 ? "✓" : "✗"));

  console.log("=== P3-3. 開口：拉矩形 → boundary 20 loops=2 ===");
  await eval_(`document.querySelector('[data-face-tool="hole"]').click()`);
  await sleep(200);
  const holeBox = await eval_(`(()=>{
    const r = document.getElementById("faceEditorSvg").getBoundingClientRect();
    const toScr = p => ({x: r.left + p[0]*fe.zoom + fe.panX,
                         y: r.top + p[1]*fe.zoom + fe.panY});
    const a = toScr([500, 500]), b = toScr([1200, 1000]);
    return {a, b};
  })()`);
  await drag(holeBox.a.x, holeBox.a.y, holeBox.b.x, holeBox.b.y);
  await sleep(900);
  const loopN = await eval_(`api("boundary 20").then(r=>r.ok ? r.loops.length : -1)`);
  console.log("loops:", loopN,explicitVerdict(loopN === 2 ? "✓ 開口成功" : "✗"));

  console.log("=== P3-4. 投影面板：天花面 → 恰一個 data-view=2 ===");
  await eval_(`document.getElementById("projToggle").click()`);
  await sleep(1000);
  const projN2 = await eval_(
    `document.querySelectorAll('#projViews [data-view="2"]').length`);
  const projAll = await eval_(
    `document.querySelectorAll('#projViews [data-view]').length`);
  console.log("proj groups:", projAll, "view2:", projN2,explicitVerdict(projN2 === 1 && projAll === 1 ? "✓ 只顯示仰視" : "✗"));

  console.log("=== P3-5. 非法編輯 → toast + boundary 不變 ===");
  const bSnap = await eval_(
    `api("boundary 20").then(r=>JSON.stringify(r.loops))`);
  const invalidEditToasts=await captureNewToasts(async()=>{
    await cmdLine("boundary 20 outline 0,0 4000,0 4000,3000 1500,1500 0,3000");
    await sleep(900);
  });
  const invalidEditToast=invalidEditToasts.some(t=>t.visible&&t.classes.includes('error')&&t.text.includes('邊界面輪廓不合法：邊要軸平行'));
  const bAfter = await eval_(
    `api("boundary 20").then(r=>JSON.stringify(r.loops))`);
  console.log("本次非法輪廓錯誤 toast:", JSON.stringify(invalidEditToasts),explicitVerdict(invalidEditToast ? "✓" : "✗"),
    "| boundary 未變:",explicitVerdict(bSnap === bAfter ? "✓" : "✗"));

  console.log("=== P3-6. Esc 回世界；游離面放置表單 ===");
  /* P3-3 把工具停在 hole;Esc 先退出工具層級,先歸零再按 Esc 才會離開工作區 */
  await eval_(`document.querySelector('[data-face-tool="select"]').click()`);
  await sleep(200);
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(500);
  console.log("focus:", await eval_(`JSON.stringify(oc.focus)`));
  /* 建游離矩形面（DSL + canvas-pos，跟 btnNewRect 同路） */
  const ids6 = await eval_(`api("newid").then(r=>r.boundary)`);
  await cmdLine(`boundary ${ids6} outline 0,0 500,0 500,400 0,400`);
  await eval_(`api("line canvas-pos boundary ${ids6} 700 300")`);
  await eval_(`renderObjects()`);
  await sleep(900);
  await clickControl('#btnZoom');
  const freeCard = await eval_(`(()=>{
    const c = document.querySelector('.ocard[data-kind="boundary"][data-id="${ids6}"]');
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  if (freeCard) {
    /* Compact cards hide their entry button. Expand the target, then open it
       without relying on the two-click timing gate already tested above. */
    await eval_(`centerOnNode('boundary',${ids6})`);
    await clickControl(`.ocard[data-kind="boundary"][data-id="${ids6}"] .card-enter`);
    await waitForUI(`oc.focus?.t==='face' && oc.focus.id===${ids6} && oc.edit?.bid===${ids6} && !$('objectWorkspace').hidden && document.querySelector('#faceInspectorContent #placeSubmit')?.dataset.bid==='${ids6}'`,10000);
    const gDis = await eval_(
      `document.querySelector('[data-face-tool="guide"]').disabled`);
    console.log("guide 工具 disabled（游離）:",explicitVerdict(gDis ? "✓" : "✗"));
    /* 工作區檢視器放置表單：天花預設 + origin 0 0 2500 */
    await eval_(`document.querySelector('#faceInspectorContent [data-place-preset="天花"]').click()`);
    await eval_(`(()=>{const p=document.getElementById("faceInspectorContent");
      p.querySelector("#placeOX").value=0; p.querySelector("#placeOY").value=0;
      p.querySelector("#placeOZ").value=2500;})()`);
    await eval_(`document.querySelector("#faceInspectorContent #placeSubmit").click()`);
    await sleep(1200);
    const placed = await eval_(
      `api("objects").then(r=>{const f=r.faces.find(x=>x.id===${ids6});return f&&f.placed})`);
    const surfN = await eval_(
      `api("surfaces").then(r=>r.surfaces.filter(s=>s.boundary===${ids6}).length)`);
    console.log("placed:", placed,explicitVerdict(placed === true ? "✓" : "✗"),
      "| surfaces:", surfN,explicitVerdict(surfN === 1 ? "✓" : "✗"));
    const gEn = await eval_(
      `!document.querySelector('[data-face-tool="guide"]').disabled`);
    console.log("guide 工具啟用（已放置）:",explicitVerdict(gEn ? "✓" : "✗"));
    /* 放置後拉參考線成功 */
    await eval_(`document.querySelector('[data-face-tool="guide"]').click()`);
    await sleep(200);
    const fc2 = await eval_(`(()=>{
      const r = document.getElementById("faceEditorViewport").getBoundingClientRect();
      return {x: r.left + r.width/2, y: r.top + r.height/2};
    })()`);
    await drag(fc2.x - 60, fc2.y, fc2.x + 60, fc2.y + 3);
    await sleep(900);
    const d3 = await eval_(`api("dump").then(r=>r.text)`);
    const valid = (await eval_(`api("references")`)).guides.every(g => !/^-?\d+$/.test(g.expression));
    console.log("放置後參考線皆保留引用式:",explicitVerdict(valid ? "✓" : "✗"));
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await sleep(400);
  } else console.log(explicitVerdict("✗ 游離面卡未出現"));

  /* ================= Phase 4：空間工作區 ================= */
  /* WORLD_MAX_BOUNDARIES=8：清掉前面累積的面再測六面盒;
     P3-6 結尾焦點可能還在面工作區,先明確退出 */
  await eval_(`leaveFocus()`);
  await eval_(`api("line reset")`);
  await eval_(`renderObjects()`);
  await sleep(600);
  console.log("=== P4-1. 快速六面盒 4000/3000/2500 ===");
  const objPre = await eval_(
    `api("objects").then(r=>({f:r.faces.length,s:r.spaces.length}))`);
  await clickControl('#btnBox6');
  await sleep(300);
  console.log("box6 dialog:",explicitVerdict(await eval_(
    `!document.getElementById("box6Dialog").hidden ? "✓ 開啟" : "✗"`)));
  await eval_(`document.getElementById("box6Submit").click()`);
  await sleep(1500);
  const objBox = await eval_(
    `api("objects").then(r=>({f:r.faces.length,s:r.spaces.length,
      closed:r.spaces.map(x=>[x.id,x.closed,x.members.length])}))`);
  const boxSp = objBox.closed.find(x => x[2] === 6);
  console.log("objects:", JSON.stringify(objPre), "->", JSON.stringify(objBox));
  console.log("六面盒:",explicitVerdict(objBox.f === objPre.f + 6 && objBox.s === objPre.s + 1 &&
    boxSp && boxSp[1] === true ? `✓ 6面+1空間 closed:true (空間 ${boxSp && boxSp[0]})` : "✗"));
  const boxSid = boxSp && boxSp[0];

  console.log("=== P4-2. 空間工作區：成員/槽位/三視圖 ===");
  /* 服務完成建模後還要刷新卡片；慢速橋接器可能超過通用 settle 的 5 秒上限。 */
  await waitForUI(`!!document.querySelector('.ocard[data-kind="space"][data-id="${boxSid}"]')`, 30000);
  await clickControl('#btnZoom');
  const spCard = await eval_(`(()=>{
    const c = document.querySelector('.ocard[data-kind="space"][data-id="${boxSid}"]');
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  if (spCard) {
    await dblclick(spCard.x, spCard.y);
    await sleep(1100);
    console.log("focus:", await eval_(`JSON.stringify(oc.focus)`),explicitVerdict(await eval_(`oc.focus && oc.focus.t==="space" ? "✓" : "✗"`)));
    console.log("space layout:",explicitVerdict(await eval_(
      `!document.getElementById("spaceWorkspaceLayout").hidden ? "✓" : "✗"`)));
    const memN = await eval_(
      `document.querySelectorAll("#spaceMemberList .space-boundary-button").length`);
    const slotOn = await eval_(
      `document.querySelectorAll("#spaceInspectorContent .slot.on").length`);
    const projKids = await eval_(
      `document.getElementById("spaceProjSvg").childElementCount`);
    console.log("成員列:", memN,explicitVerdict(memN === 6 ? "✓" : "✗"),
      "| 槽位佔用:", slotOn,explicitVerdict(slotOn === 6 ? "✓" : "✗"),
      "| 三視圖群組:", projKids,explicitVerdict(projKids >= 3 ? "✓" : "✗"));
  } else console.log(explicitVerdict("✗ 六面盒空間卡未出現"));

  console.log("=== P4-3. 編輯成員：移除一面 → closed:false ===");
  await eval_(`document.getElementById("spEditMembers").click()`);
  await sleep(400);
  console.log("member dialog:",explicitVerdict(await eval_(
    `!document.getElementById("memberDialog").hidden ? "✓" : "✗"`)));
  /* 取消勾選第一個成員 */
  await eval_(`(()=>{
    const c = document.querySelector('#memberCheckList input:checked');
    if (c) c.checked = false;
  })()`);
  await eval_(`document.getElementById("memberSubmit").click()`);
  await sleep(1200);
  const spAfterEdit = await eval_(
    `api("objects").then(r=>r.spaces.find(s=>s.id===${boxSid}))`);
  console.log("members:", spAfterEdit && spAfterEdit.members.length,explicitVerdict(spAfterEdit && spAfterEdit.members.length === 5 ? "✓" : "✗"),
    "| closed:", spAfterEdit && spAfterEdit.closed,explicitVerdict(spAfterEdit && spAfterEdit.closed === false ? "✓ closed:false" : "✗"));

  console.log("=== P4-4. Esc 回世界；mutate 第4行送錯回滾 ===");
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(400);
  console.log("focus:", await eval_(`JSON.stringify(oc.focus)`));
  const objPre2 = await eval_(
    `api("objects").then(r=>({f:r.faces.length,s:r.spaces.length}))`);
  const ids9 = await eval_(`api("newid").then(r=>r.boundary)`);
  /* 世界已有 6/8 邊界:2 面 + 空間重宣告(收成 1 成員,真的改變狀態) + 第4行錯 + 1 */
  const boxMem1 = await eval_(
    `api("objects").then(r=>r.spaces.find(s=>s.id===${boxSid}).members[0])`);
  const mutR = await eval_(`mutate([
    "boundary ${ids9} outline 0,0 100,0 100,100 0,100",
    "boundary ${ids9 + 1} outline 0,0 100,0 100,100 0,100",
    "space ${boxSid} boundary ${boxMem1}",
    "bogus_command_xyz",
    "boundary ${ids9 + 2} outline 0,0 100,0 100,100 0,100"
  ])`);
  await sleep(900);
  const objPost = await eval_(
    `api("objects").then(r=>({f:r.faces.length,s:r.spaces.length,
      mem:r.spaces.find(s=>s.id===${boxSid}).members.length}))`);
  console.log("mutate 回傳:", mutR,
    "| objects:", JSON.stringify(objPre2), "->", JSON.stringify(objPost),explicitVerdict(objPost.f === objPre2.f && objPost.s === objPre2.s && objPost.mem === 5
      ? "✓ 已回滾(含空間成員還原)" : "✗"));


  console.log("=== P5. 鍵盤表(主畫布 v/h/f/1、/ 搜尋)===");
  const kbR = await eval_(`(async()=>{
    const press = k => window.dispatchEvent(new KeyboardEvent("keydown",{key:k,bubbles:true}));
    const rel   = k => window.dispatchEvent(new KeyboardEvent("keyup",{key:k,bubbles:true}));
    press("h"); const t1 = oc.tool;
    press("v"); const t2 = oc.tool;
    oc.zoom = 0.5; ocApply(); press("1"); const z1 = oc.zoom;
    press("f"); await new Promise(r=>setTimeout(r,50));
    press(" "); const sp = !!oc.spacePan; rel(" ");
    press("/"); const foc = document.activeElement === searchInput;
    searchInput.blur();
    return {t1,t2,z1,sp,foc};
  })()`);
  console.log("h→", kbR.t1, "| v→", kbR.t2, "| 1→zoom", kbR.z1,
    "| space→", kbR.sp, "| / →搜尋", kbR.foc,explicitVerdict(kbR.t1==="pan" && kbR.t2==="select" && kbR.z1===1 && kbR.sp===true && kbR.foc===true ? "✓" : "✗"));

  /* 投影面板互動(§5.5.4):建 guide 後 hover → pick 命中 + overlay 有線 */
  console.log("=== P5b. 空間工作區投影 hover/pick ===");
  const projR = await eval_(`(async()=>{
    leaveFocus();
    if (!oc.spaces.length) return {err:"no space"};
    /* 在一個已放置成員面上建 guide v=2000(預設視圖可見) */
    const sid = oc.surfs[0] && oc.surfs[0].id;
    const gid = (await api("newid")).guide;
    await api("line spec 投影線 2000");
    await api("line guide " + gid + " " + sid + " v spec:投影線");
    await enterFocus("space", oc.spaces[0].id);
    const svg = document.querySelector("#spaceProjSvg");
    if (!svg) return {err:"no svg"};
    /* 在三視圖各自的局部範圍內掃點,找 guide>=0 的命中座標 */
    const views = (await api("render")).layout.views;
    let hit = null;
    outer:
    for (let v = 0; v < 3; ++v) {
      const L = views[v], b = L.bounds;
      for (let y = b[1]; y <= b[3]; y += 250)
        for (let x = b[0]; x <= b[2]; x += 250) {
          const p = await api("pick " + v + " " + x + " " + y + " 20");
          if (p.guide >= 0) { hit = {v, x, y}; break outer; }
        }
    }
    if (!hit) return {err:"guide 在三視圖都掃不到"};
    /* Hover only runs on a visible projection; open the user's existing tab
       before converting coordinates and dispatching the pointer event. */
    const previousTab = document.querySelector("#spaceStageTabs [data-ss-tab].active");
    document.querySelector('#spaceStageTabs [data-ss-tab="proj"]').click();
    await window.__cdpSettleUI(0);
    const box = svg.getBoundingClientRect();
    if (svg.closest("[hidden]") || !box.width || !box.height) {
      previousTab?.click(); return {err:"三視圖分頁尚未顯示"};
    }
    const L = views[hit.v];
    const pt = svg.createSVGPoint();
    pt.x = hit.x + L.tx; pt.y = hit.y + L.ty;
    const sc = pt.matrixTransform(svg.getScreenCTM());
    svg.dispatchEvent(new PointerEvent("pointermove",
      {clientX: sc.x, clientY: sc.y, bubbles: true}));
    await window.__cdpSettleUI(600);
    const ov = svg.querySelector("g:last-child").childElementCount;
    const hov = document.getElementById("hovertxt").textContent;
    previousTab?.click();
    return {hit, ov, hov};
  })()`);
  console.log("proj hover:", JSON.stringify(projR),explicitVerdict(projR.ov > 0 ? "✓ pick/hover 有回應" : "✗"));
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* Q1:delete 指令——拒絕路徑 + UI 刪除鈕交易 + guide 刪除 */
  console.log("=== P6. delete(Q1)===");
  const delR = await eval_(`(async()=>{
    await api("line reset");
    /* C4:deleteObject 已不呼叫 confirm()——不再需要 stub。 */
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 100,0 100,100 0,100");
    const refuse = await api("line delete boundary 1");
    await deleteObject("boundary", 1);           /* 檢視器路徑:先 placement 再 boundary */
    const after1 = (await api("objects")).faces.length;
    /* guide:面內圖層列 ✕ 路徑 = emitLine("delete guide id") */
    await api("line surface 2 origin 0 0 0 u +x v +y outline 0,0 200,0 200,100 0,100");
    const gid = (await api("newid")).guide;
    await emitLine("guide " + gid + " 2 v 50");
    await emitLine("delete guide " + gid);
    const noGuide = !(await api("dump")).text.includes("guide " + gid);
    /* space */
    await api("line space 9");
    await deleteObject("space", 9);
    const spLeft = (await api("objects")).spaces.length;
    return {refuse: refuse.ok, msg: refuse.error,
            after1, noGuide, spLeft};
  })()`);
  console.log("boundary 拒絕:",explicitVerdict(!delR.refuse ? "✓" : "✗"), delR.msg || "",
    "| 刪除後面數:", delR.after1,explicitVerdict(delR.after1 === 0 ? "✓" : "✗"),
    "| guide 已刪:",explicitVerdict(delR.noGuide ? "✓" : "✗"),
    "| 空間已刪:",explicitVerdict(delR.spLeft === 0 ? "✓" : "✗"));

  /* Q2:插入凹口——GEO-188 後走「選邊 → 浮動列凹口 → 面板 → 套用」,頂點 4→8 且核心仍判合法 */
  console.log("=== P7. 插入凹口(Q2)===");
  const insR = await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 200,0 200,100 0,100");
    await renderObjects();
    await enterFocus("face", 1);
    feSetTool("select");
    const hit = document.querySelector('[data-face-hit="e:0:0"]');
    await feDown({x: 100, y: 0}, {target: hit, clientX: 0, clientY: 0});
    await feUp({x: 100, y: 0}, {target: hit, clientX: 0, clientY: 0});
    document.querySelector('#feActionBar [data-fe-act="op:notch"]').click();
    const panel = !$("feOpPanel").hidden;
    const w = document.querySelector('#feOpPanel [data-fe-param="w"]');
    const d = document.querySelector('#feOpPanel [data-fe-param="d"]');
    w.value = "100"; w.dispatchEvent(new Event("input"));
    d.value = "50"; d.dispatchEvent(new Event("input"));
    document.querySelector("#feOpApply").click();
    await window.__cdpSettleUI(300);
    const b = await api("boundary 1");
    const ortho = b.ok && b.loops[0].verts.every((v,i,vs)=>{
      const nx = vs[(i+1)%vs.length];
      return v[0]===nx[0] || v[1]===nx[1];
    });
    return {tool: fe.tool, verts: b.loops[0].verts.length,
            fixity: b.loops[0].fixity.length, ortho, panel};
  })()`);
  console.log("select 工具:",explicitVerdict(insR.tool === "select" ? "✓" : "✗"),
    "| 面板:",explicitVerdict(insR.panel ? "✓" : "✗"),
    "| 頂點 4→", insR.verts,explicitVerdict(insR.verts === 8 ? "✓" : "✗"),
    "| fixity 同步:",explicitVerdict(insR.fixity === 8 ? "✓" : "✗"),
    "| 全正交:",explicitVerdict(insR.ortho ? "✓" : "✗"));
  /* 拖凹口底部頂點加深 → 仍合法(用既有頂點拖曳路徑) */
  const notchR = await eval_(`(async()=>{
    feSetTool("select");
    fe.work = (await api("boundary 1")).loops.map(l=>({verts:l.verts.map(p=>[...p]),fixity:[...l.fixity]}));
    fe.work[0].verts[2][1] += 30;   /* 凹底左點再往下 30 */
    fe.work[0].verts[3][1] += 30;   /* 凹底右點同步 */
    const ok = await emitBoundary(1, fe.work);
    fe.work = null;
    const b1 = await api("boundary 1");
    return {ok, verts: b1.loops[0].verts.length};
  })()`);
  console.log("凹口加深:",explicitVerdict(notchR.ok ? "✓" : "✗"),
    "| 頂點:", notchR.verts,explicitVerdict(notchR.verts === 8 ? "✓" : "✗"));
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* GEO-188 形狀編輯(方案 A 邊優先 + B 形狀頁):
     選邊 → 浮動列 → 凹口參數面板(即時預覽)→ Enter 套用;F⇄X 改走浮動列;
     切角;形狀頁改數字/鏡射/刪除;拆片拒絕;推拉;Esc 階梯 */
  console.log("=== P7b. 形狀編輯(GEO-188)===");
  const seA = await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    await renderObjects();
    await enterFocus("face", 1);
    feSetTool("select");
    const hit = document.querySelector('[data-face-hit="e:0:0"]');
    await feDown({x:2000,y:0},{target:hit,clientX:0,clientY:0});
    await feUp({x:2000,y:0},{target:hit,clientX:0,clientY:0});
    await new Promise(r=>setTimeout(r,150));
    const barShown = !$("feActionBar").hidden;
    const acts = [...document.querySelectorAll("#feActionBar [data-fe-act]")].map(b=>b.dataset.feAct);
    const fx0 = (await api("boundary 1")).loops[0].fixity[0];
    const selLine = !!document.querySelector("#faceEditorRoot .face-edge-sel");
    document.querySelector('#feActionBar [data-fe-act="op:notch"]').click();
    const panel = !$("feOpPanel").hidden;
    const ghost = !!document.querySelector('#faceEditorRoot [data-fe-ghost="sub"]');
    const w = document.querySelector('#feOpPanel [data-fe-param="w"]');
    const d = document.querySelector('#feOpPanel [data-fe-param="d"]');
    w.value = "600"; w.dispatchEvent(new Event("input"));
    d.value = "300"; d.dispatchEvent(new Event("input"));
    const g = document.querySelector('#faceEditorRoot [data-fe-ghost="sub"]');
    const ghostW = g ? +g.getAttribute("width") : 0, ghostH = g ? +g.getAttribute("height") : 0;
    w.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter",bubbles:true}));
    await window.__cdpSettleUI(400);
    const b = await api("boundary 1");
    const vs = b.loops[0].verts;
    const ortho = vs.every((v,i,a)=>{const n=a[(i+1)%a.length];return v[0]===n[0]||v[1]===n[1];});
    const depth = vs.filter(p=>p[1]===300).length;
    return {barShown, acts, fx0, selLine, panel, ghost, ghostW, ghostH,
            verts: vs.length, fixity: b.loops[0].fixity.length, ortho, depth,
            start: vs[0][0]===0 && vs[0][1]===0, allF: b.loops[0].fixity.every(f=>f===1),
            feats: (fe.feats[1]||[]).length, panelClosed: $("feOpPanel").hidden};
  })()`);
  console.log("選邊→浮動列:",explicitVerdict(seA.barShown && seA.selLine ? "✓" : "✗"),
    "| 動作:", seA.acts.join(","),explicitVerdict(["op:notch","op:extend","op:push","fixity"].every(a=>seA.acts.includes(a)) ? "✓" : "✗"),
    "| 單擊不再切 fixity:",explicitVerdict(seA.fx0 === 1 ? "✓" : "✗"));
  console.log("凹口面板+即時預覽:",explicitVerdict(seA.panel && seA.ghost ? "✓" : "✗"),
    "| 預覽尺寸 600×300:",explicitVerdict(seA.ghostW === 600 && seA.ghostH === 300 ? "✓" : `✗ ${seA.ghostW}×${seA.ghostH}`),
    "| Enter 套用 頂點 4→", seA.verts,explicitVerdict(seA.verts === 8 ? "✓" : "✗"),
    "| fixity 同步:",explicitVerdict(seA.fixity === 8 ? "✓" : "✗"),
    "| 新邊全 F:",explicitVerdict(seA.allF ? "✓" : "✗"),
    "| 全正交:",explicitVerdict(seA.ortho ? "✓" : "✗"),
    "| 凹深 300:",explicitVerdict(seA.depth === 2 ? "✓" : "✗"),
    "| e0 起點沿用:",explicitVerdict(seA.start ? "✓" : "✗"),
    "| 入特徵堆疊:",explicitVerdict(seA.feats === 1 ? "✓" : "✗"),
    "| 面板已關:",explicitVerdict(seA.panelClosed ? "✓" : "✗"));
  /* F⇄X 走浮動列 */
  const seF = await eval_(`(async()=>{
    const hit = document.querySelector('[data-face-hit="e:0:0"]');
    await feDown({x:800,y:0},{target:hit,clientX:0,clientY:0});
    await feUp({x:800,y:0},{target:hit,clientX:0,clientY:0});
    const before = (await api("boundary 1")).loops[0].fixity[0];
    document.querySelector('#feActionBar [data-fe-act="fixity"]').click();
    for(let i=0;i<100&&!document.querySelector('#feActionBar [data-fe-act="fixity"]').textContent.includes('X → F');i++)await new Promise(r=>setTimeout(r,50));
    const after = (await api("boundary 1")).loops[0].fixity[0];
    return {before, after, label: document.querySelector('#feActionBar [data-fe-act="fixity"]').textContent};
  })()`);
  console.log("浮動列切 fixity:",explicitVerdict(seF.before === 1 && seF.after === 0 ? "✓" : "✗"),
    "|", seF.before, "→", seF.after, "| 鈕文案跟著翻:",explicitVerdict(/X → F/.test(seF.label) ? "✓" : "✗ " + seF.label));
  /* 切角:點凸角 → 浮動列「切角」→ a=500 b=400 */
  const seC = await eval_(`(async()=>{
    const hit = document.querySelector('[data-face-hit="v:0:0"]');
    await feDown({x:0,y:0},{target:hit,clientX:0,clientY:0});
    await feUp({x:0,y:0},{target:hit,clientX:0,clientY:0});
    const sel = fe.sel && fe.sel.kind;
    const acts = [...document.querySelectorAll("#feActionBar [data-fe-act]")].map(b=>b.dataset.feAct);
    document.querySelector('#feActionBar [data-fe-act="op:corner"]').click();
    const w = document.querySelector('#feOpPanel [data-fe-param="w"]');
    const d = document.querySelector('#feOpPanel [data-fe-param="d"]');
    w.value = "500"; w.dispatchEvent(new Event("input"));
    d.value = "400"; d.dispatchEvent(new Event("input"));
    document.querySelector("#feOpApply").click();
    await window.__cdpSettleUI(400);
    for(let i=0;i<100&&(fe.feats[1]||[]).length!==2;i++)await new Promise(r=>setTimeout(r,50));
    for(let i=0;i<100&&document.querySelectorAll('#faceInspectorContent .fe-feat').length!==2;i++)await new Promise(r=>setTimeout(r,50));
    const vs = (await api("boundary 1")).loops[0].verts;
    const has = (x,y) => vs.some(p=>p[0]===x&&p[1]===y);
    return {sel, acts, verts: vs.length, gone: !has(0,0), a: has(500,0), b: has(0,400),
            feats: (fe.feats[1]||[]).length};
  })()`);
  console.log("點凸角→切角:",explicitVerdict(seC.sel === "corner" && seC.acts.join() === "op:corner" ? "✓" : "✗"),
    "| 頂點 8→", seC.verts,explicitVerdict(seC.verts === 10 ? "✓" : "✗"),
    "| 角點移除+新角 (500,0)(0,400):",explicitVerdict(seC.gone && seC.a && seC.b ? "✓" : "✗"),
    "| 特徵 2:",explicitVerdict(seC.feats === 2 ? "✓" : "✗"));
  /* 形狀頁:清單 2 筆;改凹口寬 600→800 落地;鏡射切角;刪除切角還原 */
  const seB = await eval_(`(async()=>{
    fiShowTab("shape");
    const tabOn = document.querySelector('[data-fi-tab="shape"]').classList.contains("active");
    const rows = document.querySelectorAll("#faceInspectorContent .fe-feat").length;
    const w = document.querySelector('#faceInspectorContent [data-feat] [data-feat-num="w"]');
    w.value = "800"; w.dispatchEvent(new Event("change"));
    await window.__cdpSettleUI(400);
    let vs = (await api("boundary 1")).loops[0].verts;
    const widened = vs.some(p=>p[0]===2500&&p[1]===300) && vs.some(p=>p[0]===1700&&p[1]===300);
    const rowsAfter = document.querySelectorAll("#faceInspectorContent .fe-feat").length;
    /* 鏡射切角(第 2 筆):對面右上角也切 → 10→12 */
    document.querySelectorAll("#faceInspectorContent [data-feat]")[1].querySelector('[data-feat-mirror="x"]').click();
    for(let i=0;i<100&&document.querySelectorAll('#faceInspectorContent .fe-feat').length!==3;i++)await new Promise(r=>setTimeout(r,50));
    vs = (await api("boundary 1")).loops[0].verts;
    const mirrored = vs.length === 12 && vs.some(p=>p[0]===3500&&p[1]===0) && vs.some(p=>p[0]===4000&&p[1]===400);
    const rows3 = document.querySelectorAll("#faceInspectorContent .fe-feat").length;
    /* 刪除第 2 筆(左上切角)→ 角回來 */
    document.querySelectorAll("#faceInspectorContent [data-feat]")[1].querySelector("[data-feat-del]").click();
    for(let i=0;i<100&&document.querySelectorAll('#faceInspectorContent .fe-feat').length!==2;i++)await new Promise(r=>setTimeout(r,50));
    vs = (await api("boundary 1")).loops[0].verts;
    const restored = vs.length === 10 && vs.some(p=>p[0]===0&&p[1]===0);
    const rows4 = document.querySelectorAll("#faceInspectorContent .fe-feat").length;
    return {tabOn, rows, widened, rowsAfter, mirrored, rows3, restored, rows4};
  })()`);
  console.log("形狀頁清單:",explicitVerdict(seB.tabOn && seB.rows === 2 ? "✓" : `✗ rows=${seB.rows}`),
    "| 改寬 800 落地:",explicitVerdict(seB.widened && seB.rowsAfter === 2 ? "✓" : "✗"),
    "| 鏡射切角 10→12:",explicitVerdict(seB.mirrored && seB.rows3 === 3 ? "✓" : "✗"),
    "| 刪除還原:",explicitVerdict(seB.restored && seB.rows4 === 2 ? "✓" : "✗"));
  /* undo 兩步(回到鏡射前)→ 鏡射那筆對不上現況,堆疊自動剔除 */
  const seU = await eval_(`(async()=>{
    await doUndoRedo("undo");
    await doUndoRedo("undo");
    await window.__cdpSettleUI(300);
    return {verts: (await api("boundary 1")).loops[0].verts.length, feats: (fe.feats[1]||[]).length,
            rows: document.querySelectorAll("#faceInspectorContent .fe-feat").length};
  })()`);
  console.log("undo 後堆疊驗活:",explicitVerdict(seU.verts === 10 ? "✓" : "✗ verts=" + seU.verts), "| 特徵", seU.feats,explicitVerdict(seU.feats === 1 && seU.rows === 1 ? "✓" : "✗"));
  /* 拆片拒絕:凹口深到穿透整片 → toast,不送指令 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    oc.focus = null; oc.stack = [];
    await renderObjects();
    await enterFocus("face", 1);
    const hit = document.querySelector('[data-face-hit="e:0:0"]');
    await feDown({x:2000,y:0},{target:hit,clientX:0,clientY:0});
    await feUp({x:2000,y:0},{target:hit,clientX:0,clientY:0});
    document.querySelector('#feActionBar [data-fe-act="op:notch"]').click();
    const d = document.querySelector('#feOpPanel [data-fe-param="d"]');
    d.value = "3000"; d.dispatchEvent(new Event("input"));
  })()`);
  let seS;
  const splitToasts=await captureNewToasts(async()=>{seS=await eval_(`(async()=>{
    document.querySelector("#feOpApply").click();
    await window.__cdpSettleUI(300);
    const verts = (await api("boundary 1")).loops[0].verts.length;
    return {verts, panelOpen: !$("feOpPanel").hidden};
  })()`);});seS.toastTxt=toastText(splitToasts,'error');
  console.log("拆片拒絕:",explicitVerdict(/兩片/.test(seS.toastTxt) && seS.verts === 4 && seS.panelOpen ? "✓" : `✗ ${seS.toastTxt} verts=${seS.verts}`));
  /* 推拉:右邊往內 500 → 寬 3500,頂點仍 4;Esc 階梯:關面板 → 清選取 → 離開 */
  const seP = await eval_(`(async()=>{
    feCancelOp();
    const hit = document.querySelector('[data-face-hit="e:0:1"]');
    await feDown({x:4000,y:1500},{target:hit,clientX:0,clientY:0});
    await feUp({x:4000,y:1500},{target:hit,clientX:0,clientY:0});
    document.querySelector('#feActionBar [data-fe-act="op:push"]').click();
    const dist = document.querySelector('#feOpPanel [data-fe-param="dist"]');
    dist.value = "500"; dist.dispatchEvent(new Event("input"));
    const ghost = document.querySelector('#faceEditorRoot [data-fe-ghost="sub"]');
    const gw = ghost ? +ghost.getAttribute("width") : 0;
    document.querySelector("#feOpApply").click();
    await window.__cdpSettleUI(400);
    const b = await api("boundary 1");
    const bb = loopsBBox(b.loops);
    /* Esc 階梯 */
    const hit2 = document.querySelector('[data-face-hit="e:0:0"]');
    await feDown({x:1000,y:0},{target:hit2,clientX:0,clientY:0});
    await feUp({x:1000,y:0},{target:hit2,clientX:0,clientY:0});
    document.querySelector('#feActionBar [data-fe-act="op:extend"]').click();
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));
    const s1 = {op: !!fe.op, sel: !!fe.sel, focus: !!oc.focus};
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));
    const s2 = {op: !!fe.op, sel: !!fe.sel, focus: !!oc.focus, bar: $("feActionBar").hidden};
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));
    await window.__cdpSettleUI(300);
    const s3 = {focus: !!oc.focus};
    return {gw, w: bb[2]-bb[0], verts: b.loops[0].verts.length, s1, s2, s3};
  })()`);
  console.log("推拉往內 500:",explicitVerdict(seP.gw === 500 && seP.w === 3500 && seP.verts === 4 ? "✓" : `✗ w=${seP.w} verts=${seP.verts}`),
    "| Esc 關面板:",explicitVerdict(!seP.s1.op && seP.s1.sel && seP.s1.focus ? "✓" : "✗"),
    "| Esc 清選取:",explicitVerdict(!seP.s2.sel && seP.s2.bar && seP.s2.focus ? "✓" : "✗"),
    "| Esc 離開:",explicitVerdict(!seP.s3.focus ? "✓" : "✗"));
  await sleep(300);

  /* GEO-189 描繪指定正交多邊形的完整路徑:
     純鍵盤重畫(數字+方向鍵、自動補角、回選取)、切角/凹口「留下」連動、
     點面內→開口填數字、圖層列刪孔、開口工具拖矩形記特徵、距邊以套用當下外接框起算、套用後無殘留高亮 */
  console.log("=== P7c. 描繪指定多邊形(GEO-189)===");
  const gp1 = await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    oc.focus = null; oc.stack = [];
    await renderObjects();
    await enterFocus("face", 1);
    feSetTool("redraw");
    const key = (k, code) => window.dispatchEvent(new KeyboardEvent("keydown", {key: k, code: code || k, bubbles: true}));
    const seq = [["4000","ArrowRight"],["1500","ArrowDown"],["2500","ArrowLeft"],["1500","ArrowDown"]];
    for (const [len, dir] of seq) { for (const ch of len) key(ch, "Digit" + ch); key(dir); }
    const draftPts = fe.drag && fe.drag.pts.length;
    key("Backspace"); const afterBs = fe.drag && fe.drag.pts.length;
    for (const ch of "1500") key(ch, "Digit" + ch); key("ArrowDown");
    key("Enter");
    await window.__cdpSettleUI(400);
    const b = await api("boundary 1");
    return {draftPts, afterBs, verts: b.loops[0].verts.map(v=>v.join(",")).join(" "), tool: fe.tool, draft: !!fe.drag};
  })()`);
  console.log("鍵盤重畫 L 形:",explicitVerdict(gp1.verts === "0,0 4000,0 4000,1500 1500,1500 1500,3000 0,3000" ? "✓" : "✗ " + gp1.verts),
    "| 草稿 5 點:",explicitVerdict(gp1.draftPts === 5 ? "✓" : "✗ " + gp1.draftPts),
    "| Backspace 退一點:",explicitVerdict(gp1.afterBs === 4 ? "✓" : "✗"),
    "| 閉合自動補角+回選取:",explicitVerdict(gp1.tool === "select" && !gp1.draft ? "✓" : "✗ " + gp1.tool));
  /* 切角「留下」連動 */
  const gp2 = await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    oc.focus = null; oc.stack = [];
    await renderObjects();
    await enterFocus("face", 1);
    const hit = document.querySelector('[data-face-hit="v:0:1"]');
    await feDown({x:4000,y:0},{target:hit,clientX:0,clientY:0});
    await feUp({x:4000,y:0},{target:hit,clientX:0,clientY:0});
    document.querySelector('#feActionBar [data-fe-act="op:corner"]').click();
    const ku = document.querySelector('#feOpPanel [data-fe-keep="w"]'), kv = document.querySelector('#feOpPanel [data-fe-keep="d"]');
    ku.value = "2500"; ku.dispatchEvent(new Event("input"));
    kv.value = "1800"; kv.dispatchEvent(new Event("input"));
    const a = document.querySelector('#feOpPanel [data-fe-param="w"]').value, bb = document.querySelector('#feOpPanel [data-fe-param="d"]').value;
    const aIn = document.querySelector('#feOpPanel [data-fe-param="w"]'); aIn.value = "1000"; aIn.dispatchEvent(new Event("input"));
    const kuBack = ku.value;
    document.querySelector("#feOpApply").click();
    await window.__cdpSettleUI(400);
    const b = await api("boundary 1");
    return {a, bb, kuBack, verts: b.loops[0].verts.map(v=>v.join(",")).join(" "),
            hi: !!document.querySelector("#faceEditorRoot .fe-feat-hi")};
  })()`);
  console.log("切角留下→切掉:",explicitVerdict(gp2.a === "1500" && gp2.bb === "1200" ? "✓" : `✗ a=${gp2.a} b=${gp2.bb}`),
    "| 切掉→留下反向:",explicitVerdict(gp2.kuBack === "3000" ? "✓" : "✗ " + gp2.kuBack),
    "| 結果:",explicitVerdict(gp2.verts === "0,0 3000,0 3000,1200 4000,1200 4000,3000 0,3000" ? "✓" : "✗ " + gp2.verts),
    "| 套用後無殘留高亮:",explicitVerdict(!gp2.hi ? "✓" : "✗"));
  /* 點面內 → 開口填數字 → 圖層列刪孔 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    oc.focus = null; oc.stack = [];
    await renderObjects();
    await enterFocus("face", 1);
  })()`);
  // GEO-209: blank selection commits in the viewport pointerup handler so a
  // click can be distinguished from marquee. Exercise that real event path.
  const gp3Point = async (x,y) => eval_(`(()=>{const r=$('faceEditorViewport').getBoundingClientRect();return {x:r.left+fe.panX+${x}*fe.zoom,y:r.top+fe.panY+${y}*fe.zoom}})()`);
  const gp3Inside = await gp3Point(1000,800);
  await click(gp3Inside.x,gp3Inside.y);await sleep(220);
  const gp3 = await eval_(`(async()=>{
    const sel = fe.sel && fe.sel.kind, mark = !!document.querySelector("#faceEditorRoot .fe-point-mark");
    const acts = [...document.querySelectorAll("#feActionBar [data-fe-act]")].map(b=>b.dataset.feAct).join();
    document.querySelector('#feActionBar [data-fe-act="op:hole"]').click();
    const set = (k, v) => { const i = document.querySelector('#feOpPanel [data-fe-param="' + k + '"]'); i.value = v; i.dispatchEvent(new Event("input")); };
    set("w", 600); set("d", 400); set("dx", 1000); set("dy", 800);
    document.querySelector("#feOpApply").click();
    await window.__cdpSettleUI(400);
    const b = await api("boundary 1");
    const hb = b.loops.length === 2 ? loopsBBox([b.loops[1]]).join(",") : "";
    const feats = (fe.feats[1]||[]).map(f=>f.type).join();
    const del = document.querySelector("#faceLayerList .face-layer-del");
    if (del) del.click();
    await window.__cdpSettleUI(400);
    const b2 = await api("boundary 1");
    return {sel, mark, acts, loops: b.loops.length, hb, feats, hasDel: !!del, loopsAfter: b2.loops.length,
            featsAfter: (fe.feats[1]||[]).length};
  })()`);
  /* A point just beyond the boundary still lies inside the fitted viewport. */
  const gp3Outside = await gp3Point(-80,-80);
  await click(gp3Outside.x,gp3Outside.y);await sleep(220);
  gp3.selOut = await eval_(`fe.sel`);
  console.log("點面內→開口:",explicitVerdict(gp3.sel === "point" && gp3.mark && gp3.acts === "op:hole" ? "✓" : "✗ " + JSON.stringify([gp3.sel, gp3.mark, gp3.acts])),
    "| 孔 600×400 @(1000,800):",explicitVerdict(gp3.loops === 2 && gp3.hb === "1000,800,1600,1200" ? "✓" : "✗ " + gp3.hb),
    "| 記為 hole 特徵:",explicitVerdict(gp3.feats === "hole" ? "✓" : "✗ " + gp3.feats),
    "| 圖層列刪孔:",explicitVerdict(gp3.hasDel && gp3.loopsAfter === 1 && gp3.featsAfter === 0 ? "✓" : "✗"),
    "| 點面外清選取:",explicitVerdict(gp3.selOut === null ? "✓" : "✗"));
  /* 開口工具拖矩形 → 走布林記特徵(面內=hole,蓋到邊=notch,矩形裁到外接框) */
  const gp4 = await eval_(`(async()=>{
    feSetTool("hole");
    await feDown({x:500,y:500},{target:$("faceEditorSvg"),clientX:0,clientY:0});
    feMove({x:1100,y:900},{clientX:0,clientY:0});
    await feUp({x:1100,y:900});
    await window.__cdpSettleUI(300);
    await feDown({x:2000,y:-200},{target:$("faceEditorSvg"),clientX:0,clientY:0});
    feMove({x:2600,y:300},{clientX:0,clientY:0});
    await feUp({x:2600,y:300});
    await window.__cdpSettleUI(300);
    const b = await api("boundary 1");
    return {loops: b.loops.length, outer: b.loops[0].verts.length,
            feats: (fe.feats[1]||[]).map(f=>f.type + ":" + f.rect.join(",")).join(" ")};
  })()`);
  console.log("開口工具拖矩形:",explicitVerdict(gp4.loops === 2 && gp4.outer === 8 ? "✓" : "✗"),
    "| 特徵 hole+notch(裁到外接框):",explicitVerdict(gp4.feats === "hole:500,500,1100,900 notch:2000,0,2600,300" ? "✓" : "✗ " + gp4.feats));
  /* 距邊跟著現況走:凹口建立時較近的是右邊(距右 1400),推拉右邊 800 後距右 600;起算邊不翻轉 */
  const gp5 = await eval_(`(async()=>{
    feSetTool("select");
    const before = feFeatMeta(fe.feats[1][1]).dx;
    const hit = document.querySelector('[data-face-hit="e:0:5"]');
    const vs = oc.bmap[1][0].verts, a = vs[5], c = vs[6];
    await feDown({x:(a[0]+c[0])/2,y:(a[1]+c[1])/2},{target:hit,clientX:0,clientY:0});
    await feUp({x:(a[0]+c[0])/2,y:(a[1]+c[1])/2},{target:hit,clientX:0,clientY:0});
    const side = document.querySelector("#feOpPanel") && fe.sel;
    document.querySelector('#feActionBar [data-fe-act="op:push"]').click();
    const i = document.querySelector('#feOpPanel [data-fe-param="dist"]'); i.value = "800"; i.dispatchEvent(new Event("input"));
    document.querySelector("#feOpApply").click();
    await window.__cdpSettleUI(400);
    const bb = loopsBBox((await api("boundary 1")).loops);
    const m = feFeatMeta(fe.feats[1][1]);
    return {before, after: m.dx, ax: m.ax, w: bb[2]-bb[0], n: fe.feats[1].length};
  })()`);
  console.log("推拉右邊 800 後凹口距右 1400→600:",explicitVerdict(gp5.before === 1400 && gp5.after === 600 && gp5.ax === "right" && gp5.w === 3200 ? "✓" : `✗ ${gp5.before}→${gp5.after} ${gp5.ax} w=${gp5.w}`),
    "| 特徵 3:",explicitVerdict(gp5.n === 3 ? "✓" : "✗ " + gp5.n));
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* Q3:角材/網格圖形化——工具點放角材、表單建網格、圖層列刪除 */
  console.log("=== P8. 角材與網格(Q3)===");
  const q3R = await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    await renderObjects();
    await enterFocus("face", 1);
    /* 角材:設定 L/A/B + 方向 + 深度 → timber 工具點 (500,300) */
    $("tbAnchor").value = "at-face e0"; $("tbRole").value = "boundary"; $("tbA").value = "27"; $("tbB").value = "33";
    $("tbDir").value = "+u"; $("tbSide").value = "+n";
    feSetTool("timber");
    await feDown({x: 500, y: 300}, {target: $("faceEditorSvg"), clientX: 0, clientY: 0});
    await window.__cdpSettleUI(300);
    const dump1 = (await api("dump")).text;
    const hasTimber = /timber \\d+ 27 33 role boundary/.test(dump1) &&
                      /place \\d+ on \\d+ at-face e0 \\+u \\+n/.test(dump1);
    const fp = document.querySelector(".face-timber");
    /* 空白欄位的範例不應當作座標送出；填寫後仍可正常建立。 */
    $("gridMainAlong").value = "v";
    $("gridCreate").click();
    await window.__cdpSettleUI(300);
    const emptyGridRejected = $("gridU").value === "" && $("gridV").value === "" &&
      $("gridPreviewStatus").textContent.includes("尚未填入格線資料") &&
      (await api("dump")).text === dump1;
    /* 網格:表單建 u 500 1500 / v 300 900 */
    $("gridU").value = "500 1500"; $("gridV").value = "300 900";
    $("gridMainAlong").value = "v";
    $("gridV").dispatchEvent(new Event("input"));
    await window.__cdpSettleUI(600);
    $("gridCreate").click();
    await window.__cdpSettleUI(300);
    const dump2 = (await api("dump")).text;
    const hasGrid = /grid \\d+ on \\d+ main-along v u 500 1500/.test(dump2) &&
                    /grid \\d+ on \\d+ v 300 900/.test(dump2);
    const gridLines = document.querySelectorAll(".face-grid-line").length;
    const rows = [...document.querySelectorAll(".face-layer-row strong")]
      .map(x => x.textContent).join("|");
    const roles = document.querySelectorAll(".face-grid-line.role-primary").length === 2 &&
      document.querySelectorAll(".face-grid-line.role-secondary").length === 2;
    return {hasTimber, fp: !!fp, emptyGridRejected, hasGrid, gridLines, roles, rows};
  })()`);
  console.log("角材放置:",explicitVerdict(q3R.hasTimber ? "✓" : "✗"),
    "| 足跡繪製:",explicitVerdict(q3R.fp ? "✓" : "✗"),
    "| 空白座標提示且世界不變:",explicitVerdict(q3R.emptyGridRejected ? "✓" : "✗"),
    "| 網格建立:",explicitVerdict(q3R.hasGrid ? "✓" : "✗"),
    "| 網格線數與角色:", q3R.gridLines,explicitVerdict(q3R.gridLines === 4 && q3R.roles ? "✓" : "✗"),
    "| 圖層列:",explicitVerdict(/角材/.test(q3R.rows) && /網格/.test(q3R.rows) ? "✓" : "✗"));
  const gridSourceUI = await eval_(`(async()=>{
    fiShowTab("grid");
    $("gridUSource").value="series"; $("gridUSource").dispatchEvent(new Event("change"));
    $("gridUStart").value="500"; $("gridUStep").value="1000"; $("gridUCount").value="2";
    $("gridVSource").value="panel"; $("gridVSource").dispatchEvent(new Event("change"));
    $("gridVPanel").value="400"; $("gridVGap").value="5"; $("gridVFrom").value="0";
    $("gridVGap").dispatchEvent(new Event("input"));
    await window.__cdpSettleUI(600);
    const preview=fe.gridPreview;
    const worldBefore=(await api("dump")).text;
    $("gridCreate").click(); await window.__cdpSettleUI(450);
    const refs=await api("references"), grid=refs.grids[0];
    const filled=$("gridMainAlong").value==="v" && $("gridUSource").value==="series" && $("gridVSource").value==="panel" &&
      $("gridVGap").value==="5";
    const saved=(await api("dump")).text;
    $("gridUStart").value="3900"; $("gridUStart").dispatchEvent(new Event("input"));
    await window.__cdpSettleUI(600);
    return {preview:preview?.u?.join(",")==="500,1500" && preview?.v?.[0]===402,
      untouchedBeforeSave:!worldBefore.includes("panel 400 gap 5"),
      saved:grid?.uDefinition?.source==="series" && grid?.vDefinition?.gap===5 && grid?.v?.[0]===402,
      filled, invalid:$("gridPreviewStatus").classList.contains("invalid") && fe.gridPreview===null,
      unchanged:saved===(await api("dump")).text};
  })()`);
  console.log("網格來源即時預覽:",explicitVerdict(gridSourceUI.preview?"✓":"✗"),
    "| 預覽不改世界:",explicitVerdict(gridSourceUI.untouchedBeforeSave?"✓":"✗"),
    "| 來源儲存與回填:",explicitVerdict(gridSourceUI.saved&&gridSourceUI.filled?"✓":"✗"),
    "| 錯誤草稿拒絕且世界不變:",explicitVerdict(gridSourceUI.invalid&&gridSourceUI.unchanged?"✓":"✗"));
  /* Click position does not set timber placement. Explicitly retry the occupied
     e0 anchor created above; rejection must report occupancy and keep World. */
  const q3bBefore=await eval_(`api('dump').then(r=>r.text)`);
  await eval_(`feSetTool('timber');$('tbAnchor').value='at-face e0';$('tbRole').value='boundary';$('tbA').value='27';$('tbB').value='33';$('tbDir').value='+u';$('tbSide').value='+n';void 0`);
  const q3bToasts=await captureNewToasts(async()=>{await eval_(`(async()=>{
    await feDown({x: 3999, y: 2999}, {target: $("faceEditorSvg"), clientX: 0, clientY: 0});
    await window.__cdpSettleUI(300);
  })()`);});
  const q3b={same:q3bBefore===await eval_(`api('dump').then(r=>r.text)`),toast:toastText(q3bToasts,'error')};
  console.log("重複定位拒絕:",explicitVerdict(q3b.same ? "✓" : "✗"),
    "| toast:",explicitVerdict(q3b.toast.includes('占滿') ? "✓" : "✗"),JSON.stringify(q3bToasts));
  /* 圖層列 ✕ 刪角材與網格 */
  const q3c = await eval_(`(async()=>{
    const dels = [...document.querySelectorAll(".face-layer-del")];
    for (const b of dels) { b.click(); await window.__cdpSettleUI(200);
      const confirm=document.querySelector("#impact-confirm"); if (confirm && !confirm.disabled) { confirm.click(); await window.__cdpSettleUI(200); } }
    const dump = (await api("dump")).text;
    return {noTimber: !/timber /.test(dump), noGrid: !/grid /.test(dump)};
  })()`);
  console.log("角材已刪:",explicitVerdict(q3c.noTimber ? "✓" : "✗"),
    "| 網格已刪:",explicitVerdict(q3c.noGrid ? "✓" : "✗"));
  const gridRoleUI = await eval_(`(async()=>{
    /* 與圖層刪除測試隔離：主支需上下兩條邊界材作合法擋面。 */
    leaveFocus();
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    await api("line grid 1 on 1 main-along v u 500 1500 v 300 900");
    await renderObjects();
    await enterFocus("face",1);
    const supports=await mutate([
      "timber 1 27 33 role boundary", "place 1 on 1 at-face e0 +u +n",
      "timber 2 27 33 role boundary", "place 2 on 1 at-face e2 +u +n"]);
    if (supports) await feAfterChange();
    const anchor=$("tbAnchor"), role=$("tbRole");
    const grid=(await api("references")).grids[0];
    anchor.value="at-line grid "+grid.id+" u 0"; anchor.dispatchEvent(new Event("change"));
    const defaultPrimary=role.value==="primary";
    role.value="custom"; role.dispatchEvent(new Event("change"));
    anchor.value="at-line grid "+grid.id+" v 0"; anchor.dispatchEvent(new Event("change"));
    const manualPreserved=role.value==="custom";
    $("tbUseSuggestion").click();
    const resetSecondary=role.value==="secondary";
    const hit=document.querySelector('[data-face-hit="k:'+grid.id+':u:0"]');
    const before=(await api("references")).timbers.length;
    feSetTool("timber");
    feMove({x:500,y:500},{target:hit,clientX:0,clientY:0});
    const roleCard=!!document.querySelector('#gridTimberPopover select') && document.querySelector('#gridTimberPopover select').value==='primary';
    await feDown({x:500,y:500},{target:hit,clientX:0,clientY:0});
    await window.__cdpSettleUI(350);
    const refs=await api("references");
    return {supports,defaultPrimary,manualPreserved,resetSecondary,hit:!!hit,roleCard,
      referenceCount:fe.grids[0]?.references?.length,
      placed:refs.timbers.length===before+1 &&
        refs.timbers.some(t=>t.role==="primary"),
      timberCount:refs.timbers.length, before, role:$("tbRole").value};
  })()`);
  console.log("格線角色預填:",explicitVerdict(gridRoleUI.defaultPrimary?"✓":"✗"),
    "| 手動覆寫保留:",explicitVerdict(gridRoleUI.manualPreserved?"✓":"✗"),
    "| 套用建議:",explicitVerdict(gridRoleUI.resetSecondary?"✓":"✗"),
    "| 清單引用數:",explicitVerdict(gridRoleUI.referenceCount===1?"✓":"✗"),
    "| 格線放材角色卡:",explicitVerdict(gridRoleUI.roleCard?'✓':'✗'),
    "| 點格線放材:",explicitVerdict(gridRoleUI.supports&&gridRoleUI.hit&&gridRoleUI.placed?"✓":"✗"), gridRoleUI.placed?"":`${gridRoleUI.before}→${gridRoleUI.timberCount} role=${gridRoleUI.role}`);
  const gridLinkedChange=await eval_(`(async()=>{
    const before=(await api('references')).timbers.map(t=>[t.id,t.role,t.geometry]);
    document.querySelector('[data-grid-id="1"] .face-layer-del').click();
    const locked=$('gridPreviewStatus').textContent.includes('仍引用格線') && (await api('references')).grids.length===1;
    $('gridMainAlong').value='u';$('gridMainAlong').dispatchEvent(new Event('change'));await window.__cdpSettleUI(500);
    $('gridCreate').click();await window.__cdpSettleUI(400);
    const confirm=document.querySelector('#impact-confirm');if(confirm&&!confirm.disabled){confirm.click();await window.__cdpSettleUI(500);}
    const after=await api('references');
    const roles=after.grids[0].mainAlong==='u' && JSON.stringify(before)===JSON.stringify(after.timbers.map(t=>[t.id,t.role,t.geometry]));
    $('gridUSource').value='panel';$('gridUPanel').value='5000';$('gridUGap').value='5';$('gridUFrom').value='0';$('gridUPanel').dispatchEvent(new Event('input'));await window.__cdpSettleUI(500);
    const missing=$('gridPreviewStatus').textContent.includes('索引將消失') && !fe.gridPreview && $('gridUSource').getAttribute('aria-invalid')==='true' && (await api('references')).grids[0].u.length===after.grids[0].u.length;
    return {locked,roles,missing};
  })()`);
  for(const [name,pass] of Object.entries(gridLinkedChange)) console.log('P8v2 linked '+name,explicitVerdict(pass?'✓':'✗'));
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* GEO-202: entry paths, draft isolation, accessible errors and source gestures. */
  console.log("=== P8v2. 網格設計稿整合 ===");
  const gridV2 = await eval_(`(async()=>{
    await api('line reset');
    await api('line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000');
    await api('line grid 1 on 1 main-along v u 500 1500 2500 v 600 1200');
    await renderObjects();await enterFocus('face',1);fiShowTab('components');
    const before=(await api('dump')).text;
    const set=(id,value)=>{$(id).value=value;$(id).dispatchEvent(new Event($(id).tagName==='SELECT'?'change':'input'));};
    const applied=$('gridDraftBadge').textContent==='已套用' && !fe.gridPreview && $('gridCreate').disabled;
    const rowCopy=document.querySelector('[data-grid-id="1"] .face-layer-copy');
    const rowReadable=rowCopy.getBoundingClientRect().width>=120 && rowCopy.getBoundingClientRect().height<80;
    set('gridUSource','series');set('gridUStart','800');set('gridUStep','800');set('gridUCount','4');
    await window.__cdpSettleUI(600);
    const entryPreview=fe.gridPreview?.u.join(',')==='800,1600,2400,3200' && document.querySelectorAll('.face-grid-preview-line').length===6;
    const isolated=(await api('dump')).text===before;
    document.querySelector('[data-grid-id="1"] .grid-layer-open').click();
    const row=fe.fiTab==='grid' && fe.tool==='grid' && document.activeElement.matches('[data-grid-direction]');
    const retained=$('gridUStart').value==='800';
    $('gridReset').click();await window.__cdpSettleUI(400);
    const reset=$('gridUSource').value==='explicit' && $('gridU').value==='500 1500 2500' && !fe.gridPreview && (await api('dump')).text===before;
    set('gridU','1500 500');await window.__cdpSettleUI(400);$('gridCreate').click();await window.__cdpSettleUI(200);
    const inline=$('gridU').getAttribute('aria-invalid')==='true' && document.activeElement.id==='gridU' && !$('gridUError').hidden && !document.querySelector('.reference-impact[open]');
    const other=$('gridV').value==='600 1200';
    set('gridUSource','panel');set('gridUPanel','400');set('gridUGap','5');set('gridUFrom','5000');await window.__cdpSettleUI(400);
    const bounds=$('gridUFrom').getAttribute('aria-invalid')==='true' && $('gridUError').textContent.includes('4000');
    set('gridUFrom','0');await window.__cdpSettleUI(600);
    const odd=fe.gridPreview?.u[0]===402;
    GridEditor.addLine('u',700);
    const conversion=$('gridUSource').value==='panel' && !$('gridSourceConversion').hidden;
    [...$('gridSourceConversion').querySelectorAll('button')].find(b=>b.textContent==='取消').click();
    set('gridUPanel','5000');await window.__cdpSettleUI(600);
    const zero=fe.gridPreview?.u.length===0 && !document.querySelector('.grid-preview-status.invalid');
    $('gridCreate').click();await window.__cdpSettleUI(600);
    const saved=(await api('references')).grids[0];
    const save=saved.uDefinition.source==='panel' && saved.u.length===0 && $('gridDraftBadge').textContent==='已套用' && !fe.gridPreview;
    await doUndoRedo('undo');await window.__cdpSettleUI(300);
    const undo=(await api('references')).grids[0].u.join(',')==='500,1500,2500';
    set('gridU','700 1700 2700');await window.__cdpSettleUI(500);renderFaceInspector();await window.__cdpSettleUI(500);
    const rerender=$('gridU').value==='700 1700 2700' && fe.gridPreview?.u[0]===700;
    set('gridU','900 1900');set('gridU','1000 2000 3000');await window.__cdpSettleUI(600);
    const latest=fe.gridPreview?.u.join(',')==='1000,2000,3000';
    const grouped=!!$('tbAnchor').querySelector('optgroup[label*="網格 1"]');
    return {applied,rowReadable,entryPreview,isolated,row,retained,reset,inline,other,bounds,odd,conversion,zero,save,undo,rerender,latest,grouped};
  })()`);
  if(gridV2.__err) throw Error(gridV2.__err);
  for(const [name,pass] of Object.entries(gridV2)) console.log('P8v2 '+name,explicitVerdict(pass?'✓':'✗'));
  await eval_(`GridEditor.open(1)`);
  const gridDragPoint=await eval_(`(()=>{const r=document.querySelector('[data-grid-label="u:0"] rect').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,z:fe.zoom};})()`);
  await drag(gridDragPoint.x,gridDragPoint.y,gridDragPoint.x+100*gridDragPoint.z,gridDragPoint.y);
  await sleep(600);
  console.log('P8v2 pointer drag explicit',explicitVerdict(await eval_(`$('gridU').value==='1100 2000 3000' && fe.gridPreview?.u[0]===1100`)?'✓':'✗'));
  const cancelGridPoint=await eval_(`(()=>{const r=document.querySelector('[data-grid-label="u:0"] rect').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,z:fe.zoom};})()`);
  await pressDownMod(cancelGridPoint.x,cancelGridPoint.y);
  await moveMod(cancelGridPoint.x+100*cancelGridPoint.z,cancelGridPoint.y);
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:cancelGridPoint.x+100*cancelGridPoint.z,y:cancelGridPoint.y,button:'left',clickCount:1});
  await sleep(600);
  console.log('P8v2 drag Escape restores draft',explicitVerdict(await eval_(`$('gridU').value==='1100 2000 3000' && oc.focus?.t==='face'`)?'✓':'✗'));
  const gridDerivedEdit=await eval_(`(async()=>{
    const set=(id,value)=>{$(id).value=value;$(id).dispatchEvent(new Event($(id).tagName==='SELECT'?'change':'input'));};
    set('gridUSource','series');set('gridUStart','500');set('gridUStep','1000');set('gridUCount','3');await window.__cdpSettleUI(600);
    document.querySelector('[data-grid-label="u:1"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));
    $('gridSourceConversion').querySelector('input').value='1700';$('gridSourceConversion').querySelector('button').click();await window.__cdpSettleUI(600);
    const series=$('gridUSource').value==='series' && $('gridUStep').value==='1200' && fe.gridPreview.u[2]===2900;
    set('gridUSource','panel');set('gridUPanel','400');set('gridUGap','5');set('gridUFrom','0');await window.__cdpSettleUI(600);
    document.querySelector('[data-grid-label="u:0"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));
    $('gridSourceConversion').querySelector('input').value='452';$('gridSourceConversion').querySelector('button').click();await window.__cdpSettleUI(600);
    return {series,panel:$('gridUSource').value==='panel' && $('gridUFrom').value==='50' && fe.gridPreview.u[0]===452};
  })()`);
  for(const [name,pass] of Object.entries(gridDerivedEdit)) console.log('P8v2 keyboard '+name,explicitVerdict(pass?'✓':'✗'));
  const gridShot=async name=>{
    if(!process.env.GEOMETRY_GRID_SCREENSHOT_DIR)return;
    const fs=require('fs'),path=require('path');fs.mkdirSync(process.env.GEOMETRY_GRID_SCREENSHOT_DIR,{recursive:true});
    const shot=await send('Page.captureScreenshot',{format:'png'});
    fs.writeFileSync(path.join(process.env.GEOMETRY_GRID_SCREENSHOT_DIR,name+'.png'),Buffer.from(shot.result.data,'base64'));
  };
  await eval_(`fiShowTab('grid')`);await gridShot('grid-v2-desktop-final');
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});
  const gridPhone=await eval_(`(async()=>{
    GridEditor.open(1);await window.__cdpSettleUI(100);
    const width=document.querySelector('.face-inspector-panel').getBoundingClientRect().width;
    const targets=[...document.querySelectorAll('.grid-editor input,.grid-editor button')].filter(e=>e.getBoundingClientRect().height>0);
    const touch=targets.every(e=>e.getBoundingClientRect().height>=44);
    const draft=$('gridU').value,scroll=$('faceInspectorContent').scrollTop;
    $('gridShowCanvas').click();const canvas=!document.body.classList.contains('drawer-right-open')&&!$('gridReturnSettings').hidden;
    $('gridReturnSettings').click();
    const vp=$('faceEditorViewport').getBoundingClientRect(),labels=[...document.querySelectorAll('[data-grid-label]')].map(e=>e.getBoundingClientRect());
    return {full:width>=389,touch,canvas,retained:$('gridU').value===draft && $('faceInspectorContent').scrollTop===scroll,noOverflow:document.documentElement.scrollWidth<=390,labels:labels.every(r=>r.left>=vp.left && r.right<=vp.right)};
  })()`);
  for(const [name,pass] of Object.entries(gridPhone)) console.log('P8v2 phone '+name,explicitVerdict(pass?'✓':'✗'));
  await gridShot('grid-v2-mobile-settings-final');
  await eval_(`$('gridShowCanvas').click()`);await gridShot('grid-v2-mobile-canvas-final');
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  await eval_(`closePanels();leaveFocus()`);

  /* GEO-203: presentation-only reference visibility, including grid lines. */
  console.log("=== P8v3. 參考線顯示控制 ===");
  const referenceVisibility = await eval_(`(async()=>{
    resetSceneFocus();await api('line reset');
    for(const line of [
      'surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
      'surface 2 origin 5000 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
      'spec 顯示水平線 800','spec 顯示直線 2000',
      'guide 1 1 u spec:顯示水平線','guide 2 1 v spec:顯示直線',
      'grid 1 on 1 main-along v u 500 1500 v 600 1200',
      'grid 2 on 2 main-along v u 500 1500 v 600 1200',
      'timber 1 27 33 role boundary','place 1 on 1 at-face e0 +u +n',
      'timber 2 27 33 role boundary','place 2 on 1 at-face e2 +u +n',
      'timber 3 27 33 role primary','place 3 on 1 at-line grid 1 u 0 +v +n'
    ]) {const r=await api('line '+line);if(!r.ok)throw Error(r.error+' '+line);}
    await renderObjects();await enterFocus('face',1);feSetTool('grid');
    document.querySelector('#faceReferenceVisibility summary').click();
    const control=key=>[...$('faceReferenceVisibility').querySelectorAll('input')].find(i=>i.dataset.refVisible===key);
    const saved=(await api('dump')).text,refs=JSON.stringify(await api('references'));
    const undo=ReferenceWorkspace.history.undo.length,redo=ReferenceWorkspace.history.redo.length;
    const initial=control('all').checked && document.querySelectorAll('.face-reference-line').length===2 && document.querySelectorAll('.face-grid-line').length===4;
    control('guide:1').click();
    const guideHidden=document.querySelectorAll('.face-reference-line').length===1 && !document.querySelector('[data-face-hit="g:1:u"]') && !document.querySelector('[data-guide-label="1"]') && control('all').indeterminate;
    control('grid:1:u:0').click();
    const gridHidden=document.querySelectorAll('.face-grid-line').length===3 && !document.querySelector('[data-face-hit="k:1:u:0"]') && !document.querySelector('[data-grid-label="u:0"]') && control('group:grid:1').indeterminate;
    feSetTool('timber');$('tbAnchor').value='at-line grid 1 u 0';fe.anchorPreview=true;drawFaceEditor();
    const anchorHidden=!document.querySelector('.fe-anchor-hi') && [...$('tbAnchor').options].some(o=>o.value==='at-line grid 1 u 0') && document.querySelectorAll('.face-timber').length===3;
    control('group:grid:1').click();control('group:grid:1').click();
    const groupHidden=!document.querySelector('.face-grid-line') && document.querySelectorAll('.face-reference-line').length===1;
    control('all').click();
    const restoreAll=control('all').checked && document.querySelectorAll('.face-grid-line').length===4 && document.querySelectorAll('.face-reference-line').length===2;
    control('all').click();
    const hideAll=!document.querySelector('.face-grid-line,.face-reference-line,.fe-anchor-hi,.face-grid-hit,[data-face-hit^="g:"]') && document.querySelectorAll('.face-timber').length===3;
    control('guide:2').click();
    const singleRestore=document.querySelectorAll('.face-reference-line').length===1 && !document.querySelector('.face-grid-line') && control('all').indeterminate;
    control('all').click();control('grid:1:u:0').click();
    feSetTool('grid');$('gridU').value='700 1700';$('gridU').dispatchEvent(new Event('input'));await window.__cdpSettleUI(500);
    const draftHidden=fe.gridPreview?.u[0]===700 && document.querySelectorAll('.face-grid-preview-line').length===3 && !document.querySelector('[data-grid-label="u:0"]');
    control('guide:1').click();
    const draftRetained=$('gridU').value==='700 1700' && fe.gridPreview?.u[0]===700;
    $('gridReset').click();await window.__cdpSettleUI(500);
    await feLoadGuides();drawFaceEditor();renderFaceLayers();renderFaceInspector();
    const redraw=!control('grid:1:u:0').checked && !control('guide:1').checked && !document.querySelector('[data-face-hit="k:1:u:0"]');
    await leaveFocus();await enterFocus('face',2);
    const otherFace=control('all').checked && document.querySelectorAll('.face-grid-line').length===4;
    await leaveFocus();await enterFocus('face',1);
    const retained=!control('guide:1').checked && !control('grid:1:u:0').checked;
    const unchanged=(await api('dump')).text===saved && JSON.stringify(await api('references'))===refs && ReferenceWorkspace.history.undo.length===undo && ReferenceWorkspace.history.redo.length===redo;
    return {initial,guideHidden,gridHidden,anchorHidden,groupHidden,restoreAll,hideAll,singleRestore,draftHidden,draftRetained,redraw,otherFace,retained,unchanged};
  })()`);
  if(referenceVisibility.__err)throw Error(referenceVisibility.__err);
  for(const [name,pass] of Object.entries(referenceVisibility))console.log('P8v3 '+name,explicitVerdict(pass?'✓':'✗'));
  await eval_(`document.querySelector('[data-ref-visible="guide:1"]').focus()`);
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:' ',code:'Space',windowsVirtualKeyCode:32});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:' ',code:'Space',windowsVirtualKeyCode:32});
  console.log('P8v3 keyboard Space',explicitVerdict(await eval_(`document.querySelector('[data-ref-visible="guide:1"]').checked && document.querySelectorAll('.face-reference-line').length===2`)?'✓':'✗'));
  await eval_(`feSetTool('grid')`);
  await gridShot('reference-visibility-desktop');
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await eval_(`openPanel('left',$('workspaceToggleLeft'))`);
  const visibilityPhone=await eval_(`(()=>{
    const box=$('faceReferenceVisibility'),labels=[...box.querySelectorAll('label')];
    box.scrollIntoView({block:'start'});
    return {touch:labels.every(l=>l.getBoundingClientRect().height>=44),fits:box.scrollWidth<=box.clientWidth && document.documentElement.scrollWidth<=390};
  })()`);
  console.log('P8v3 phone touch',explicitVerdict(visibilityPhone.touch?'✓':'✗'),'fits',explicitVerdict(visibilityPhone.fits?'✓':'✗'));
  await gridShot('reference-visibility-mobile');
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  const visibilityReset=await eval_(`(async()=>{resetSceneFocus();await renderObjects();await enterFocus('face',1);return document.querySelector('[data-ref-visible="all"]').checked && document.querySelectorAll('.face-grid-line').length===4;})()`);
  console.log('P8v3 reset clears preferences',explicitVerdict(visibilityReset?'✓':'✗'));
  await eval_(`leaveFocus()`);

  /* GEO-204 / D19 / I25 / R23: local subgrids through the real editor. */
  console.log("=== P8v4. 局部子網格 ===");
  {
    const subgridExceptionStart=excN;
    const subgridCheck=(name,ok,detail)=>console.log('P8v4 '+name,explicitVerdict(ok?'✓':'✗'),ok?'':JSON.stringify(detail));
    const subgridRead=async expression=>{const value=await eval_(expression);if(value?.__err)throw Error(value.__err);return value;};
    const subgridShot=async name=>{
      if(!process.env.GEOMETRY_GRID_SCREENSHOT_DIR)return;
      await waitForUI(`!document.querySelector('.toast')`,6000);
      const fs=require('fs'),path=require('path');fs.mkdirSync(process.env.GEOMETRY_GRID_SCREENSHOT_DIR,{recursive:true});
      const result=await send('Page.captureScreenshot',{format:'png'});
      fs.writeFileSync(path.join(process.env.GEOMETRY_GRID_SCREENSHOT_DIR,name+'.png'),Buffer.from(result.result.data,'base64'));
    };
    await subgridRead(`(async()=>{
      resetSceneFocus();await api('line reset');
      for(const command of [
        'surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000 hole 2300,1400 2800,1400 2800,1900 2300,1900',
        'grid 1 on 1 main-along v u 1000 3000 v 500 2500'
      ]){const r=await api('line '+command);if(!r.ok)throw Error(JSON.stringify(r));}
      await renderObjects();await enterFocus('face',1);feSetTool('grid');
      window.subgridBefore=(await api('dump')).text;
      $('subgridNew').click();await window.__cdpSettleUI(200);
      return true;
    })()`);
    subgridCheck('新增入口與可用父格',await subgridRead(`!!$('subgridCellChoice') && $('subgridCellChoice').options.length>=9 && !!$('subgridPickCell')`));
    await subgridRead(`$('subgridPickCell').click()`);
    const selectedCell=await subgridRead(`(()=>{const e=[...document.querySelectorAll('[data-subgrid-cell]')].find(e=>e.dataset.subgridCell==='line:0|line:1|line:0|line:1');if(!e)throw Error('Missing central cell hit');const r=e.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2};})()`);
    await click(selectedCell.x,selectedCell.y);
    await waitForUI(`fe.gridPreview?.kind==='subgrid' && fe.gridPreview.u[0]===2000`,10000);
    const subgridDraft=await subgridRead(`(async()=>{
      const g=fe.gridPreview;
      window.subgridId=g?.id;
      return {picked:$('subgridCellChoice').value==='line:0|line:1|line:0|line:1',
        lines:g?.u.join(',')==='2000'&&g?.v.join(',')==='1500',
        scope:JSON.stringify(g?.bounds)==='{"u":[1000,3000],"v":[500,2500]}',
        roles:g?.lines.every(l=>l.role==='secondary'&&l.priority===3),
        clip:g?.lines.reduce((n,l)=>n+l.segments.length,0)===3,
        readOnly:(await api('dump')).text===subgridBefore,
        rendered:document.querySelectorAll('.face-grid-preview-line').length===3};
    })()`);
    for(const [key,value]of Object.entries(subgridDraft))subgridCheck('選格預覽 '+key,value,subgridDraft);
    const subgridError=await subgridRead(`(async()=>{
      $('subgridDivU').value='3';$('subgridDivU').dispatchEvent(new Event('input',{bubbles:true}));await window.__cdpSettleUI(500);
      const rejected=$('gridPreviewStatus').classList.contains('invalid')&&!fe.gridPreview&&$('subgridDivU').getAttribute('aria-invalid')==='true';
      const intact=(await api('dump')).text===subgridBefore;
      $('subgridDivU').value='2';$('subgridDivU').dispatchEvent(new Event('input',{bubbles:true}));await window.__cdpSettleUI(500);
      return {rejected,intact,recovered:fe.gridPreview?.u[0]===2000};
    })()`);
    for(const [key,value]of Object.entries(subgridError))subgridCheck('除不盡與修正 '+key,value,subgridError);
    await subgridShot('subgrid-desktop-preview');
    await subgridRead(`$('gridCreate').click()`);
    await waitForUI(`fe.grids.some(g=>g.kind==='subgrid')`,10000);
    const subgridSaved=await subgridRead(`(async()=>{
      const refs=await api('references'),g=refs.grids.find(g=>g.kind==='subgrid');
      window.subgridId=g.id;window.subgridSaved=(await api('dump')).text;
      return {definition:subgridSaved.includes('subgrid '+g.id+' parent 1 cell u line:0 line:1 v line:0 line:1 divisions u 2 v 2'),
        row:!!document.querySelector('[data-grid-id="'+g.id+'"][data-grid-kind="subgrid"]'),
        parent:refs.grids.find(g=>g.id===1).u.join(',')==='1000,3000',
        childHit:document.querySelectorAll('[data-face-hit="k:'+g.id+':v:0"]').length===2};
    })()`);
    for(const [key,value]of Object.entries(subgridSaved))subgridCheck('建立 '+key,value,subgridSaved);
    const subgridVisibility=await subgridRead(`(async()=>{
      document.querySelector('#faceReferenceVisibility summary').click();
      const ctl=k=>[...$('faceReferenceVisibility').querySelectorAll('input')].find(x=>x.dataset.refVisible===k);
      const parentHits=document.querySelectorAll('[data-face-hit^="k:1:"]').length;
      ctl('grid:'+subgridId+':v:0').click();
      const one=!document.querySelector('[data-face-hit="k:'+subgridId+':v:0"]')&&!!document.querySelector('[data-face-hit="k:'+subgridId+':u:0"]');
      const parent=document.querySelectorAll('[data-face-hit^="k:1:"]').length===parentHits;
      ctl('group:grid:'+subgridId).click();ctl('group:grid:'+subgridId).click();
      const group=!document.querySelector('[data-face-hit^="k:'+subgridId+':"]');
      ctl('group:grid:'+subgridId).click();
      return {one,parent,group,restored:document.querySelectorAll('[data-face-hit="k:'+subgridId+':v:0"]').length===2,unchanged:(await api('dump')).text===subgridSaved};
    })()`);
    for(const [key,value]of Object.entries(subgridVisibility))subgridCheck('顯示 '+key,value,subgridVisibility);
    const subgridEdit=await subgridRead(`(async()=>{
      document.querySelector('[data-grid-id="'+subgridId+'"] .grid-layer-open').click();await window.__cdpSettleUI(200);
      const filled=$('subgridDivU').value==='2'&&$('subgridDivV').value==='2';
      $('subgridDivU').value='4';$('subgridDivU').dispatchEvent(new Event('input',{bubbles:true}));await window.__cdpSettleUI(500);
      const draft=fe.gridPreview?.u.join(',')==='1500,2000,2500'&&(await api('dump')).text===subgridSaved;
      $('gridReset').click();await window.__cdpSettleUI(500);
      return {filled,draft,reset:$('subgridDivU').value==='2'&&(await api('dump')).text===subgridSaved};
    })()`);
    for(const [key,value]of Object.entries(subgridEdit))subgridCheck('編輯 '+key,value,subgridEdit);
    // Changing a child without any timbers still requires a concrete I8a preview.
    await subgridRead(`$('subgridDivU').value='4';$('subgridDivU').dispatchEvent(new Event('input',{bubbles:true}))`);
    await waitForUI(`fe.gridPreview?.u.length===3`,10000);
    await subgridRead(`$('gridCreate').click()`);
    await waitForUI(`!!document.querySelector('.reference-impact[open]')`,10000);
    subgridCheck('無角材也列子格影響',await subgridRead(`(async()=>!!document.querySelector('.reference-impact[open]')&&document.querySelector('.reference-impact').textContent.includes('子網格')&&(await api('dump')).text===subgridSaved)()`));
    await subgridRead(`document.querySelector('.reference-impact .impact-actions button').click()`);
    await waitForUI(`!document.querySelector('.reference-impact')`,10000);
    subgridCheck('取消保留世界',await subgridRead(`(async()=>(await api('dump')).text===subgridSaved)()`));
    // Cancellation refreshes the draft asynchronously. A disabled click is ignored;
    // wait for the same valid proposal before testing the second I8a confirmation.
    await waitForUI(`!oc.busy && $('gridCreate') && !$('gridCreate').disabled && fe.gridPreview?.u.length===3`,10000);
    await subgridRead(`$('gridCreate').click()`);await waitForUI(`!!$('impact-confirm')`,10000);
    await subgridRead(`$('impact-confirm').click()`);await waitForUI(`fe.grids.find(g=>g.id===subgridId)?.u.length===3`,10000);
    subgridCheck('確認更新與來源保留',await subgridRead(`fe.grids.find(g=>g.id===subgridId).u.join(',')==='1500,2000,2500'`));
    await subgridRead(`$('btnUndo').click()`);await waitForUI(`fe.grids.find(g=>g.id===subgridId)?.u.length===1`,10000);
    subgridCheck('復原整筆子格',await subgridRead(`(async()=>(await api('dump')).text===subgridSaved)()`));
    await subgridRead(`$('btnRedo').click()`);await waitForUI(`fe.grids.find(g=>g.id===subgridId)?.u.length===3`,10000);
    subgridCheck('重做整筆子格',await subgridRead(`fe.grids.find(g=>g.id===subgridId).u.length===3`));
    // Save through the real project writer, then reopen that package.
    const subgridRoundtrip=await subgridRead(`(async()=>{
      const picker=window.showSaveFilePicker,before=(await api('dump')).text;
      let bytes;
      window.showSaveFilePicker=async()=>({createWritable:async()=>({write:async data=>{bytes=new Uint8Array(data instanceof Blob?await data.arrayBuffer():data);},close:async()=>{}})});
      try{await ReferenceWorkspace.save();}finally{window.showSaveFilePicker=picker;}
      if(!bytes?.length)throw Error('Project save did not write bytes');
      const control=[...$('faceReferenceVisibility').querySelectorAll('input')].find(x=>x.dataset.refVisible==='group:grid:'+subgridId);control.click();
      await ReferenceWorkspace.importBytes(bytes,'子網格驗收.gcanvas');await renderObjects();await enterFocus('face',1);
      return {saved:(await api('dump')).text===before,
        definition:fe.grids.some(g=>g.kind==='subgrid'&&g.divisions.u===4),
        visible:!!document.querySelector('[data-face-hit="k:'+subgridId+':u:0"]')};
    })()`);
    for(const [key,value]of Object.entries(subgridRoundtrip))subgridCheck('專案重開 '+key,value,subgridRoundtrip);
    await subgridRead(`document.querySelector('[data-grid-id="'+subgridId+'"] .grid-layer-open').click()`);
    await subgridShot('subgrid-desktop-saved');
    await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
    await subgridRead(`openPanel('right',$('workspaceToggleRight'))`);await sleep(250);
    const subgridPhone=await subgridRead(`(()=>{
      const form=$('subgridDivU').closest('.grid-editor');
      const controls=[...form.querySelectorAll('input,select,button')].filter(e=>e.getBoundingClientRect().height>0);
      return {touch:controls.every(e=>e.getBoundingClientRect().height>=44),fits:document.documentElement.scrollWidth<=390,
        labels:!!$('subgridDivU').labels.length&&!!$('subgridDivV').labels.length,
        choices:$('subgridCellChoice').options.length>=9};
    })()`);
    for(const [key,value]of Object.entries(subgridPhone))subgridCheck('手機 '+key,value,subgridPhone);
    await subgridShot('subgrid-mobile-settings');
    await subgridRead(`$('subgridPickCell').click()`);await sleep(250);
    subgridCheck('手機選格露出畫布',await subgridRead(`!document.body.classList.contains('drawer-right-open')&&!!document.querySelector('[data-subgrid-cell]')`));
    await subgridShot('subgrid-mobile-pick');
    await subgridRead(`document.querySelector('[data-subgrid-cell="min|line:0|min|line:0"]').focus()`);
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
    await waitForUI(`fe.gridPreview?.bounds.u[0]===0`,10000);
    subgridCheck('鍵盤重新選邊格',await subgridRead(`$('subgridCellChoice').value==='min|line:0|min|line:0'&&fe.gridPreview?.bounds.u.join(',')==='0,1000'&&fe.gridPreview?.bounds.v.join(',')==='0,500'`));
    await subgridRead(`$('gridReset').click()`);await sleep(500);
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
    const subgridDependencyUI=await subgridRead(`(async()=>{
      closePanels();const before=(await api('dump')).text;
      document.querySelector('[data-grid-id="1"] .grid-layer-open').click();
      $('gridU').value='500 1000 3000';$('gridU').dispatchEvent(new Event('input',{bubbles:true}));await window.__cdpSettleUI(500);
      const countLock=$('gridPreviewStatus').classList.contains('invalid')&&!fe.gridPreview&&(await api('dump')).text===before;
      $('gridReset').click();await window.__cdpSettleUI(500);
      document.querySelector('[data-grid-id="1"] .face-layer-del').click();await window.__cdpSettleUI(150);
      return {countLock,deleteLock:$('gridPreviewStatus').textContent.includes('子網格')&&(await api('dump')).text===before};
    })()`);
    for(const [key,value]of Object.entries(subgridDependencyUI))subgridCheck('父格守門 '+key,value,subgridDependencyUI);
    const subgridRoles=await subgridRead(`(async()=>{
      fiShowTab('timber');const anchor=$('tbAnchor'),role=$('tbRole');
      anchor.value='at-line grid '+subgridId+' u 0';anchor.dispatchEvent(new Event('change'));$('tbUseSuggestion').click();
      const first=role.value==='secondary'&&$('tbSuggestion').textContent.includes('尚未建立實際主支方向');
      anchor.value='at-line grid '+subgridId+' v 0';anchor.dispatchEvent(new Event('change'));$('tbUseSuggestion').click();
      const second=role.value==='secondary';
      const made=await mutate(['timber 1 27 33 role boundary','place 1 on 1 at-face e0 +u +n','timber 2 27 33 role boundary','place 2 on 1 at-face e2 +u +n']);
      if(!made)throw Error('Support fixture failed');await feAfterChange();fiShowTab('timber');
      $('tbAnchor').value='at-line grid '+subgridId+' u 0';$('tbAnchor').dispatchEvent(new Event('change'));$('tbUseSuggestion').click();
      const conflict=$('tbRole').value==='secondary'&&$('tbSuggestion').textContent.includes('平行');
      const before=(await api('dump')).text;$('tbPlace').click();await window.__cdpSettleUI(250);
      const blocked=(await api('dump')).text===before;
      $('tbRole').value='custom';$('tbRole').dispatchEvent(new Event('change'));
      $('tbAnchor').value='at-line grid '+subgridId+' v 0';$('tbAnchor').dispatchEvent(new Event('change'));
      return {first,second,conflict,blocked,override:$('tbRole').value==='custom'};
    })()`);
    for(const [key,value]of Object.entries(subgridRoles))subgridCheck('角色預設 '+key,value,subgridRoles);
    const subgridLargeCoordinates=await subgridRead(`(async()=>{
      resetSceneFocus();await api('line reset');
      for(const command of [
        'surface 1 origin 0 0 0 u +x v +y outline 99999998,99999998 100000000,99999998 100000000,100000000 99999998,100000000',
        'grid 1 on 1 main-along v u 99999999 v 99999999'
      ]){const r=await api('line '+command);if(!r.ok)throw Error(JSON.stringify(r));}
      await renderObjects();await enterFocus('face',1);feSetTool('grid');$('subgridNew').click();
      return $('subgridCellChoice').options.length===5;
    })()`);
    subgridCheck('大座標保留四個1平方mm格',subgridLargeCoordinates);
    const subgridZeroIdentity=await subgridRead(`(async()=>{
      resetSceneFocus();await api('line reset');
      for(const command of [
        'surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
        'grid 1 on 1 main-along v u 2000 v 1500',
        'subgrid 0 parent 1 cell u min line:0 v min line:0 divisions u 2 v 2'
      ]){const r=await api('line '+command);if(!r.ok)throw Error(JSON.stringify(r));}
      await renderObjects();await enterFocus('face',1);feSetTool('grid');GridEditor.open(1);$('subgridNew').click();
      const option=[...$('subgridCellChoice').options].find(o=>o.value==='min|line:0|min|line:0');
      return option.disabled&&option.textContent.includes('子格 0')&&!document.querySelector('[data-subgrid-cell="min|line:0|min|line:0"]');
    })()`);
    subgridCheck('子格ID0仍標示已占用',subgridZeroIdentity);
    await subgridRead(`(async()=>{closePanels();resetSceneFocus();await renderObjects();})()`);
    subgridCheck('無執行期例外',excN===subgridExceptionStart,{before:subgridExceptionStart,after:excN});
  }

  /* RC/多邊形 Phase 1:重畫外環 + 形狀庫 */
  console.log("=== P9. 重畫外環與形狀庫(RC Phase 1)===");
  const rw = await eval_(`(async()=>{
    await api("line reset");
    await api("line boundary 1 outline 0,0 400,0 400,300 0,300");
    await renderObjects();
    await enterFocus("face", 1);
    /* L 形:6 點軸鎖,Enter 閉合 */
    feSetTool("redraw");
    const pts = [[50,50],[350,50],[350,150],[150,150],[150,280],[50,280]];
    for (const p of pts)
      await feDown({x:p[0],y:p[1]}, {target:$("faceEditorSvg"),clientX:0,clientY:0});
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter"}));
    await window.__cdpSettleUI(300);
    const b = await api("boundary 1");
    const ortho = b.loops[0].verts.every((v,i,vs)=>{
      const nx = vs[(i+1)%vs.length];
      return v[0]===nx[0] || v[1]===nx[1];
    });
    return {tool:"redraw", verts:b.loops[0].verts.length, ortho,
            fixity:b.loops[0].fixity.length};
  })()`);
  console.log("L 形閉合:",explicitVerdict(rw.verts === 6 ? "✓" : "✗"),
    "| 頂點:", rw.verts, "| 全正交:",explicitVerdict(rw.ortho ? "✓" : "✗"),
    "| fixity:",explicitVerdict(rw.fixity === 6 ? "✓" : "✗"));
  /* Esc 取消:畫一半按 Esc → boundary 不變 */
  const rw2 = await eval_(`(async()=>{
    feSetTool("redraw");
    await feDown({x:10,y:10},{target:$("faceEditorSvg"),clientX:0,clientY:0});
    await feDown({x:90,y:10},{target:$("faceEditorSvg"),clientX:0,clientY:0});
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));
    const b = await api("boundary 1");
    return {verts:b.loops[0].verts.length, draft:!!fe.drag};
  })()`);
  console.log("Esc 取消:",explicitVerdict(rw2.verts === 6 && !rw2.draft ? "✓" : "✗"),
    "| 草稿已清:",explicitVerdict(!rw2.draft ? "✓" : "✗"));
  /* 共線點自動去除:4 點中夾一個共線 → 仍 4 頂點 */
  const rw3 = await eval_(`(async()=>{
    feSetTool("redraw");
    const pts = [[0,0],[200,0],[300,0],[300,200],[0,200]];   /* 200,0 與 300,0 共線 */
    for (const p of pts)
      await feDown({x:p[0],y:p[1]},{target:$("faceEditorSvg"),clientX:0,clientY:0});
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter"}));
    await window.__cdpSettleUI(300);
    const b = await api("boundary 1");
    return {verts:b.loops[0].verts.length};
  })()`);
  console.log("共線去除:",explicitVerdict(rw3.verts === 4 ? "✓" : "✗"), "| 頂點:", rw3.verts);
  /* 形狀庫:L 4000/3000/臂1000 → 6 頂點、面積 = 4000*3000-3000*2000 */
  const rw4 = await eval_(`(async()=>{
    feSetTool("select");
    $("faceShapeButton").click();
    $("shapeW").value="4000"; $("shapeD").value="3000"; $("shapeA").value="1000";
    $("shapeSubmit").click();
    await window.__cdpSettleUI(300);
    const b = await api("boundary 1");
    const vs = b.loops[0].verts;
    let area = 0;
    for (let i=0;i<vs.length;++i){
      const p=vs[i], q=vs[(i+1)%vs.length];
      area += p[0]*q[1]-q[0]*p[1];
    }
    return {verts:vs.length, area:Math.abs(area)/2,
            dlg:$("shapeDialog").hidden};
  })()`);
  console.log("形狀庫 L:",explicitVerdict(rw4.verts === 6 ? "✓" : "✗"),
    "| 面積:", rw4.area,explicitVerdict(rw4.area === 6000000 ? "✓" : "✗"),
    "| 對話框已關:",explicitVerdict(rw4.dlg ? "✓" : "✗"));
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* RC/多邊形 Phase 2:尺寸導向編輯 */
  console.log("=== P10. 尺寸導向編輯(RC Phase 2)===");
  /* 鍵入長度:redraw 中數字鍵 + Enter → 下一段長度即所鍵 */
  const tl = await eval_(`(async()=>{
    await api("line reset");
    await api("line boundary 1 outline 0,0 400,0 400,300 0,300");
    await renderObjects();
    await enterFocus("face", 1);
    feSetTool("redraw");
    await feDown({x:0,y:0},{target:$("faceEditorSvg"),clientX:0,clientY:0});
    await feMove({x:500,y:3});              /* 游標朝 +u → 軸向 +u */
    for (const ch of ["1","2","0","0"])
      window.dispatchEvent(new KeyboardEvent("keydown",{key:ch}));
    const bufShown = !$("feLenInput").hidden && $("feLenInput").value === "1200";
    /* Esc 只清輸入不取消整段 */
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));
    const draftKept = !!fe.drag && fe.lenBuf === "" && $("feLenInput").hidden;
    for (const ch of ["1","5","0","0"])
      window.dispatchEvent(new KeyboardEvent("keydown",{key:ch}));
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter"}));
    const last = fe.drag.pts[fe.drag.pts.length - 1];
    return {bufShown, draftKept, last};
  })()`);
  console.log("鍵入長度:",explicitVerdict(tl.last[0] === 1500 && tl.last[1] === 0 ? "✓" : "✗"),
    "| 浮動框:",explicitVerdict(tl.bufShown ? "✓" : "✗"),
    "| Esc 只清輸入:",explicitVerdict(tl.draftKept ? "✓" : "✗"));
  /* 邊長清單:edge0 400→500,右半邊整串 +100x(矩形 500×300) */
  const el1 = await eval_(`(async()=>{
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));  /* 丟草稿 */
    feSetTool("select");
    const inp = document.querySelector('[data-edge-len="0"]');
    inp.value = "500";
    inp.dispatchEvent(new Event("change"));
    await window.__cdpSettleUI(300);
    const b = await api("boundary 1");
    const vs = b.loops[0].verts;
    const w = vs[1][0] - vs[0][0], h = vs[2][1] - vs[1][1];
    return {w, h, verts: vs.length};
  })()`);
  console.log("邊長清單:",explicitVerdict(el1.w === 500 && el1.h === 300 ? "✓" : "✗"),
    "| 結果:", el1.w + "×" + el1.h, "| 頂點:", el1.verts);
  /* 單擊邊 = 選取(GEO-188);fixity 改走浮動列的 F⇄X 鈕 */
  const fx = await eval_(`(async()=>{
    feSetTool("select");
    const hit = document.querySelector('[data-face-hit="e:0:0"]');
    const before = (await api("boundary 1")).loops[0].fixity[0];
    await feDown({x:250,y:0},{target:hit,clientX:0,clientY:0});
    await feUp({x:250,y:0},{target:hit,clientX:0,clientY:0});
    await new Promise(r=>setTimeout(r,100));
    const mid = (await api("boundary 1")).loops[0].fixity[0];
    document.querySelector('#feActionBar [data-fe-act="fixity"]').click();
    await window.__cdpSettleUI(300);
    const after = (await api("boundary 1")).loops[0].fixity[0];
    return {before, mid, after};
  })()`);
  console.log("點邊選取+浮動列切 fixity:",explicitVerdict(fx.before === 1 && fx.mid === 1 && fx.after === 0 ? "✓" : "✗"),
    "|", fx.before, "→", fx.mid, "→", fx.after);
  /* 參數化凹口:選邊 → 浮動列「凹口」→ 面板 w=40 d=20 → 4→8 頂點(取代舊 #notchDialog) */
  const nt = await eval_(`(async()=>{
    feSetTool("select");
    const hit = document.querySelector('[data-face-hit="e:0:0"]');
    await feDown({x:250,y:0},{target:hit,clientX:0,clientY:0});
    await feUp({x:250,y:0},{target:hit,clientX:0,clientY:0});
    document.querySelector('#feActionBar [data-fe-act="op:notch"]').click();
    const dlgOpen = !$("feOpPanel").hidden;
    const w = document.querySelector('#feOpPanel [data-fe-param="w"]');
    const d = document.querySelector('#feOpPanel [data-fe-param="d"]');
    w.value = "40"; w.dispatchEvent(new Event("input"));
    d.value = "20"; d.dispatchEvent(new Event("input"));
    document.querySelector("#feOpApply").click();
    await window.__cdpSettleUI(300);
    const b = await api("boundary 1");
    const vs = b.loops[0].verts;
    /* 凹口深 20:找 y=20 的頂點(內側朝下) */
    const depth = vs.filter(p => p[1] === 20).length;
    return {dlgOpen, closed: $("feOpPanel").hidden,
            verts: vs.length, depth};
  })()`);
  console.log("參數化凹口:",explicitVerdict(nt.dlgOpen && nt.closed ? "✓" : "✗"),
    "| 頂點 4→", nt.verts,explicitVerdict(nt.verts === 8 ? "✓" : "✗"),
    "| 凹深 20:",explicitVerdict(nt.depth === 2 ? "✓" : "✗"));
  /* 拖邊對齊吸附:L 形拖邊經過他頂點同軸座標 → snapTo */
  const sn = await eval_(`(async()=>{
    await api("line reset");
    await api("line boundary 1 outline 0,0 300,0 300,100 100,100 100,300 0,300");
    oc.focus = null; oc.stack = [];         /* 前段已在面 1,勿再推疊 */
    await renderObjects();
    await enterFocus("face", 1);
    feSetTool("select");
    const hit = document.querySelector('[data-face-hit="e:0:0"]');
    await feDown({x:150,y:0},{target:hit,clientX:0,clientY:0});
    await feMove({x:150,y:103});            /* 接近 v=100 的頂點軸 */
    const snap = fe.drag.snapTo;
    const movedY = fe.work[0].verts[0][1];
    fe.work = null; fe.drag = null;         /* 不落地,只驗吸附偵測 */
    return {snap, movedY};
  })()`);
  console.log("對齊吸附:",explicitVerdict(sn.snap === 100 ? "✓" : "✗"),
    "| snapTo:", sn.snap, "| 吸附後 v:", sn.movedY);
  await eval_(`leaveFocus()`);
  await sleep(300);

  console.log("=== P11. RC 柱樑一等物件(RC Phase 4)===");
  await eval_(`(async()=>{
    await api("line reset");
    for (const ln of [
      "boundary 1 outline 0,0 4000,0 4000,3000 0,3000",
      "placement 1 on boundary 1 origin 0 0 2500 u +x v +y",
      "boundary 2 outline 0,0 3000,0 3000,4000 0,4000",
      "placement 2 on boundary 2 origin 0 0 0 u +y v +x",
      "space 1 boundary 1 2",
    ]) await api("line " + ln);
    await renderObjects();
  })()`);
  await sleep(700);
  /* ＋柱:對話框 → 選空間 → 建立 */
  await clickControl('#btnNewColumn');
  await sleep(300);
  console.log("rcDialog:",explicitVerdict(await eval_(
    `!document.getElementById("rcDialog").hidden ? "✓ 開啟" : "✗"`)));
  await eval_(`(()=>{
    document.getElementById("rcSpace").value = "1";
    document.getElementById("rcX").value = "500";
    document.getElementById("rcY").value = "500";
  })()`);
  await eval_(`document.getElementById("rcSubmit").click()`);
  await sleep(1000);
  const colObj = await eval_(`api("objects").then(r=>r.columns)`);
  console.log("柱建立:",explicitVerdict(colObj.length === 1 && colObj[0].space === 1
    ? `✓ id=${colObj[0].id} z=${colObj[0].box[2]}~${colObj[0].box[5]}`
    : "✗ " + JSON.stringify(colObj)));
  const colCard = await eval_(`(()=>{
    const c = document.querySelector('.ocard[data-kind="column"]');
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  console.log("柱卡片:",explicitVerdict(colCard ? "✓" : "✗"));
  /* 拖卡片 → canvas-pos 持久化 */
  if (colCard) {
    const columnBefore = await eval_(`api("objects").then(r=>{const c=r.columns[0];return c?{id:c.id,cx:c.cx,cy:c.cy}:null;})`);
    await drag(colCard.x, colCard.y, colCard.x + 130, colCard.y + 80);
    const commit = columnBefore ? await cdp.waitCardCanvasPos(eval_, {kind:'column', id:columnBefore.id, beforeCx:columnBefore.cx, beforeCy:columnBefore.cy}) : {ok:false};
    const dragR = await eval_(`api("objects").then(r=>({
      has: r.columns[0] && r.columns[0].hasPos }))`);
    const dumpPos = await eval_(
      `api("dump").then(d=>/canvas-pos column/.test(d.text))`);
    console.log("拖卡片→canvas-pos:",explicitVerdict(commit.ok && dragR.has && dumpPos ? "✓" : "✗"),
      "| dump 有記錄:", dumpPos, JSON.stringify(commit));
  }
  /* 空間→柱 障礙連線 */
  const rcEdgeLabels = await eval_(
    `[...document.querySelectorAll("#edgeLabelLayer .edge-label")].map(t=>t.textContent).join(",")`);
  console.log("障礙連線:",explicitVerdict(/障礙/.test(rcEdgeLabels) ? `✓ ${rcEdgeLabels}` : `✗ ${rcEdgeLabels}`));
  /* ＋樑 */
  await clickControl('#btnNewBeam');
  await sleep(300);
  await eval_(`(()=>{
    document.getElementById("rcSpace").value = "1";
    document.getElementById("rcA").value = "0";
    document.getElementById("rcB").value = "4000";
    document.getElementById("rcC").value = "1500";
  })()`);
  await eval_(`document.getElementById("rcSubmit").click()`);
  await sleep(1000);
  const beamObj = await eval_(`api("objects").then(r=>r.beams)`);
  console.log("樑建立:",explicitVerdict(beamObj.length === 1 && beamObj[0].box[5] === 2500
    ? `✓ top=${beamObj[0].box[5]}` : "✗ " + JSON.stringify(beamObj)));
  console.log("樑卡片:",explicitVerdict(await eval_(
    `!!document.querySelector('.ocard[data-kind="beam"]') ? "✓" : "✗"`)));
  /* 搜尋「柱」命中柱卡 */
  await eval_(`(()=>{ const s=document.getElementById("searchInput");
    s.value="柱"; s.dispatchEvent(new Event("input")); })()`);
  await sleep(400);
  const srch = await eval_(`(()=>{
    const cards=[...document.querySelectorAll("#cardLayer .ocard")];
    return {n:cards.length, kind:cards[0] && cards[0].dataset.kind};
  })()`);
  console.log("搜尋柱:",explicitVerdict(srch.n === 1 && srch.kind === "column" ? "✓" : `✗ ${JSON.stringify(srch)}`));
  await eval_(`(()=>{ const s=document.getElementById("searchInput");
    s.value=""; s.dispatchEvent(new Event("input")); })()`);
  await sleep(400);
  /* 檢視器表單 → 重宣告 */
  await eval_(`selectObject("column", ${colObj[0].id})`);
  await sleep(500);
  console.log("檢視器表單:",explicitVerdict(await eval_(
    `!!document.getElementById("rcfX") ? "✓" : "✗"`)));
  await eval_(`document.getElementById("rcfX").value = "800"`);
  await eval_(`document.getElementById("rcfApply").click()`);
  await sleep(900);
  const movedX = await eval_(`api("objects").then(r=>r.columns[0].box[0])`);
  console.log("表單重宣告 x→800:",explicitVerdict(movedX === 800 ? "✓" : `✗ ${movedX}`));
  /* 雙擊柱卡 → 只開只開檢視器(🔒 Q10) */
  const cc = await eval_(`(()=>{
    const c = document.querySelector('.ocard[data-kind="column"]');
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  await dblclick(cc.x, cc.y);
  await sleep(700);
  const dbl = await eval_(`({f:oc.focus, s:oc.sel && oc.sel.kind})`);
  console.log("雙擊只開檢視器:",explicitVerdict(dbl.f === null && dbl.s === "column" ? "✓" : `✗ ${JSON.stringify(dbl)}`));
  /* 刪除 → 卡片消失(C4:deleteObject 已不呼叫 confirm(),不再需要 stub） */
  await eval_(`document.getElementById("inspDelete").click()`);
  await sleep(900);
  const gone = await eval_(`api("objects").then(r=>r.columns.length === 0)`);
  const cardGone = await eval_(`!document.querySelector('.ocard[data-kind="column"]')`);
  console.log("刪除→卡片消失:",explicitVerdict(gone && cardGone ? "✓" : `✗ obj=${gone} card=${cardGone}`));

  console.log("=== P12. 空間工作區:平面示意+構件+鬼影(RC Phase 5)===");
  /* 等前段 mutate 完全沉降,避免 emitLine 撞 oc.busy */
  await eval_(`new Promise(r=>{const t=()=>oc.busy?setTimeout(t,60):r();t()})`);
  await eval_(`(async()=>{
    await api("line reset");
    for (const ln of [
      "boundary 1 outline 0,0 4000,0 4000,3000 0,3000",
      "placement 1 on boundary 1 origin 0 0 2500 u +x v +y",
      "boundary 2 outline 0,0 3000,0 3000,4000 0,4000",
      "placement 2 on boundary 2 origin 0 0 0 u +y v +x",
      "boundary 3 outline 0,0 4000,0 4000,2500 0,2500",
      "placement 3 on boundary 3 origin 0 0 0 u +x v +z",
      "boundary 4 outline 0,0 2500,0 2500,4000 0,4000",
      "placement 4 on boundary 4 origin 0 3000 0 u +z v +x",
      "boundary 5 outline 0,0 2500,0 2500,3000 0,3000",
      "placement 5 on boundary 5 origin 0 0 0 u +z v +y",
      "boundary 6 outline 0,0 3000,0 3000,2500 0,2500",
      "placement 6 on boundary 6 origin 4000 0 0 u +y v +z",
      "space 1 boundary 1 2 3 4 5 6",
      "column 1 in 1 at 1000 1000 size 400 400",
      "beam 1 in 1 along y from 0 to 3000 at 2000 width 300 depth 500",
    ]) await api("line " + ln);
    await renderObjects();
    await enterFocus("space", 1);
  })()`);
  await sleep(1000);
  const plan0 = await eval_(`({
    cols: document.querySelectorAll("#spacePlanSvg .space-plan-col").length,
    beams: document.querySelectorAll("#spacePlanSvg .space-plan-beam").length,
    mine: document.querySelectorAll("#spaceRcList .space-boundary-button").length,
    free: document.querySelectorAll("#spaceRcFreeList .space-boundary-button").length,
    floor: !!document.querySelector("#spacePlanSvg .space-plan-floor")
  })`);
  console.log("平面圖:",explicitVerdict(plan0.floor && plan0.cols === 1 && plan0.beams === 1
    ? "✓" : `✗ ${JSON.stringify(plan0)}`));
  console.log("構件清單:",explicitVerdict(plan0.mine === 2 && plan0.free === 0
    ? "✓" : `✗ ${JSON.stringify(plan0)}`));

  /* 點放柱:房間 (1500,500) → at 1200 200 size 600;
     房間→螢幕走 CTM(preserveAspectRatio letterbox 也算進去) */
  const ptCol = await eval_(`(()=>{
    const svg = document.getElementById("spacePlanSvg");
    const pt = svg.createSVGPoint(); pt.x = 1500; pt.y = 500;
    const p = pt.matrixTransform(svg.getScreenCTM());
    return {x: p.x, y: p.y};
  })()`);
  await click(ptCol.x, ptCol.y);
  await sleep(1000);
  const colP = await eval_(`api("objects").then(r=>({
    n: r.columns.length,
    dom: document.querySelectorAll("#spacePlanSvg .space-plan-col").length
  }))`);
  console.log("點放柱:",explicitVerdict(colP.n === 2 && colP.dom === 2
    ? "✓" : `✗ ${JSON.stringify(colP)}`));

  /* 拖放樑:水平拖 → along x;房間→螢幕走 CTM */
  const bmD = await eval_(`(()=>{
    const svg = document.getElementById("spacePlanSvg");
    const px = (x,y)=>{ const pt = svg.createSVGPoint(); pt.x = x; pt.y = y;
      const p = pt.matrixTransform(svg.getScreenCTM()); return {x: p.x, y: p.y}; };
    return {a: px(300, 2400), b: px(2700, 2450)};
  })()`);
  await drag(bmD.a.x, bmD.a.y, bmD.b.x, bmD.b.y);
  await sleep(1000);
  const beamP = await eval_(`api("objects").then(r=>({
    n: r.beams.length,
    ax: r.beams[1] && r.beams[1].axis,
    dom: document.querySelectorAll("#spacePlanSvg .space-plan-beam").length
  }))`);
  console.log("拖放樑:",explicitVerdict(beamP.n === 2 && beamP.ax === "x" && beamP.dom === 2
    ? "✓" : `✗ ${JSON.stringify(beamP)}`));

  /* 構件移出→游離列→收進 */
  await eval_(`document.querySelector("#spaceRcList .space-boundary-button").click()`);
  await sleep(900);
  const det = await eval_(`api("objects").then(r=>({
    sp: r.columns[0] && r.columns[0].space,
    free: document.querySelectorAll("#spaceRcFreeList .space-boundary-button").length
  }))`);
  console.log("移出→游離:",explicitVerdict(det.sp === 0 && det.free === 1
    ? "✓" : `✗ ${JSON.stringify(det)}`));
  await eval_(`document.querySelector("#spaceRcFreeList .space-boundary-button").click()`);
  await sleep(900);
  const att = await eval_(`api("objects").then(r=>r.columns[0] && r.columns[0].space)`);
  console.log("收進→空間:",explicitVerdict(att === 1 ? "✓" : `✗ ${att}`));

  /* 面內鬼影:天花(面1)應有 柱×2 + 樑條帶×2 = 4 個 */
  await eval_(`leaveFocus()`);
  await sleep(300);
  await eval_(`enterFocus("face", 1)`);
  await sleep(1000);
  const ghost = await eval_(`({
    n: document.querySelectorAll("#faceEditorRoot .obstacle-ghost").length,
    cls: [...document.querySelectorAll("#faceEditorRoot .obstacle-ghost")]
      .map(e=>e.dataset.cls).join(","),
    rows: document.querySelectorAll("#faceLayerList .face-layer-row").length
  })`);
  console.log("面內鬼影:",explicitVerdict(ghost.n === 4 && ghost.cls.includes("hole")
    && ghost.cls.includes("strip")
    ? "✓" : `✗ ${JSON.stringify(ghost)}`));
  /* 牆面鬼影:y=0 牆(面3)應有 樑1頂凹 + 樑2頂降 */
  await eval_(`leaveFocus()`);
  await sleep(300);
  await eval_(`enterFocus("face", 3)`);
  await sleep(1000);
  const ghostW = await eval_(`[...document.querySelectorAll("#faceEditorRoot .obstacle-ghost")]
    .map(e=>e.dataset.cls).join(",")`);
  console.log("牆面鬼影:",explicitVerdict(/top_notch/.test(ghostW) ? "✓" : `✗ ${ghostW}`));
  await eval_(`leaveFocus()`);
  await sleep(300);

  console.log("=== P13. apply-proj 套用按鈕(RC Phase 6)===");
  await eval_(`(async()=>{
    await api("line reset");
    for (const ln of [
      "boundary 1 outline 0,0 4000,0 4000,3000 0,3000",
      "placement 1 on boundary 1 origin 0 0 2500 u +x v +y",
      "boundary 2 outline 0,0 3000,0 3000,4000 0,4000",
      "placement 2 on boundary 2 origin 0 0 0 u +y v +x",
      "boundary 3 outline 0,0 4000,0 4000,2500 0,2500",
      "placement 3 on boundary 3 origin 0 0 0 u +x v +z",
      "boundary 4 outline 0,0 2500,0 2500,4000 0,4000",
      "placement 4 on boundary 4 origin 0 3000 0 u +z v +x",
      "boundary 5 outline 0,0 2500,0 2500,3000 0,3000",
      "placement 5 on boundary 5 origin 0 0 0 u +z v +y",
      "boundary 6 outline 0,0 3000,0 3000,2500 0,2500",
      "placement 6 on boundary 6 origin 4000 0 0 u +y v +z",
      "space 1 boundary 1 2 3 4 5 6",
      "column 1 in 1 at 1000 1000 size 400 400",
      "beam 1 in 1 along y from 0 to 3000 at 2000 width 300 depth 500",
    ]) await api("line " + ln);
    await renderObjects();
    await enterFocus("face", 1);
  })()`);
  /* 投影清單是 obstacles 查詢後才渲染:輪詢到 2 個勾選框為止(最多 4.5s),不靠固定 sleep */
  let obUi = null;
  for (let i = 0; i < 15; ++i) {
    await sleep(300);
    obUi = await eval_(`({
      checks: document.querySelectorAll("#faceProjectionEditor .fe-ob-check").length,
      checked: document.querySelectorAll("#faceProjectionEditor .fe-ob-check:checked").length,
      btn: !!document.getElementById("feApplyProj"),
      cut: !!document.getElementById("feCutStrip"),
      btnTxt: document.getElementById("feApplyProj") &&
        document.getElementById("feApplyProj").textContent
    })`);
    if (obUi.checks === 2 && obUi.btn && obUi.cut) break;
  }
  console.log("套用UI:",explicitVerdict(obUi.checks === 2 && obUi.checked === 1 &&
    obUi.btn && obUi.cut ? "✓" : `✗ ${JSON.stringify(obUi)}`));
  /* 只勾柱(預設)→ 套用 → 孔出現 */
  await eval_(`document.getElementById("feApplyProj").click()`);
  await sleep(1200);
  const ap1 = await eval_(`api("boundary 1").then(b=>({
    loops: b.loops.length, verts: b.loops[0].verts.length,
    holeF: b.loops[1] && b.loops[1].fixity.every(f=>f)
  }))`);
  console.log("套用柱孔:",explicitVerdict(ap1.loops === 2 && ap1.verts === 4 && ap1.holeF
    ? "✓" : `✗ ${JSON.stringify(ap1)}`));
  /* 只勾樑(取消已套用的柱:重套=拒絕)+ 裁切條帶 → 套用 */
  await eval_(`(()=>{
    for (const c of document.querySelectorAll("#faceProjectionEditor .fe-ob-check")) {
      c.checked = c.dataset.itemType === "beam";
      c.dispatchEvent(new Event("change"));
    }
    const cut=document.getElementById("feCutStrip");
    if(cut) cut.checked=true;
    document.getElementById("feApplyProj").click();
  })()`);
  await sleep(1500);
  const ap2 = await eval_(`api("objects").then(r=>({
    faces: r.faces.length,
    sp: r.spaces[0] && r.spaces[0].members
  }))`);
  console.log("裁切條帶:",explicitVerdict(ap2.faces === 10 && !ap2.sp.includes(1)
    ? "✓" : `✗ ${JSON.stringify(ap2)}`));
  const apGhost = await eval_(`document.querySelectorAll("#faceEditorRoot .obstacle-ghost").length`);
  console.log("保留片無殘影(柱樑都離開此片):",explicitVerdict(apGhost === 0 ? "✓" : `✗ ${apGhost}`));
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* ================= P14. 模式回饋 =================
   * 任何工具在任何輸入下都要有可見反應:
   *   切工具 → 狀態列手勢 + 浮標 + 游標類;錯誤手勢 → toast(不靜默);
   *   Esc → 有草稿先清草稿+toast,否則一次離開工作區。 */
  console.log("=== P14. 模式回饋(工具手勢/錯誤輸入/Esc) ===");
  await eval_(`(async()=>{
    await api("line reset");
    for (const ln of [
      "boundary 1 outline 0,0 4000,0 4000,3000 0,3000",
      "placement 1 on boundary 1 origin 0 0 2500 u +x v +y",
    ]) await api("line " + ln);
    await renderObjects();
    await enterFocus("face", 1);
  })()`);
  await sleep(800);
  const fbVp = await eval_(`(()=>{const r=document.getElementById("faceEditorViewport").getBoundingClientRect();
    return {cx: r.left + r.width/2, cy: r.top + r.height/2,
            qx: r.left + r.width*0.3, qy: r.top + r.height*0.32}})()`);
  /* (a) 切工具:狀態列手勢 + 浮標 + 游標類 */
  const fbTool = await eval_(`(()=>{
    document.querySelector('[data-face-tool="guide"]').click();
    return {status: document.getElementById("status").textContent,
            hint: document.getElementById("faceCanvasHint").textContent,
            hintHid: document.getElementById("faceCanvasHint").hidden,
            help: !document.getElementById("faceCanvasHintHelp").hidden,
            cls: document.getElementById("faceEditorViewport").className};
  })()`);
  /* B6:浮標只給多步工具(redraw),單發工具看狀態列 */
  console.log("切參考線:狀態列標明工具",explicitVerdict(fbTool.status.includes("參考線") ? "✓" : "✗ " + fbTool.status),
    "| 工具教學可重新開啟",explicitVerdict(fbTool.help&&fbTool.hint.includes('水平或垂直拖曳') ? "✓" : "✗"),
    "| 游標類",explicitVerdict(fbTool.cls.includes("tool-referenceLine") ? "✓" : "✗ " + fbTool.cls));
  /* (b) 參考線只點沒拖 → u/v 小選單 → 選 v → dump 出現 guide */
  await eval_(`(async()=>{const r=document.getElementById("faceEditorViewport").getBoundingClientRect();const p=feSnap(fePoint({clientX:r.left+r.width/2,clientY:r.top+r.height/2}));await api('line spec 點放定位 '+Math.round(p.x))})()`);
  // Raw spec acknowledgements have no revision: synchronize this fixture before
  // the gesture, so a later autosave dump cannot retire its prepared source stamp.
  await eval_(`api('dump')`);
  await click(fbVp.cx, fbVp.cy);
  await sleep(400);
  const pkShown = await eval_(`!document.getElementById("feGuidePick").hidden`);
  console.log("參考線點一下→方向選單:",explicitVerdict(pkShown ? "✓" : "✗"));
  const pkBtn = await eval_(`(()=>{const b=document.querySelector('#feGuidePick [data-axis="v"]');
    if(!b) return null; const r=b.getBoundingClientRect();
    return {x:r.left+r.width/2,y:r.top+r.height/2};})()`);
  if (pkBtn) { await click(pkBtn.x, pkBtn.y); await sleep(700); }
  const gDump = await eval_(`api("dump").then(d=>{const m=d.text.match(/^guide (\\d+) (\\d+) v spec:點放定位$/m);return m&&m[0]})`);
  console.log("選 v 後建線:",explicitVerdict(gDump ? "✓ " + gDump : "✗"));
  /* (c) 開口只點沒拖 → toast「拖出矩形」 */
  await eval_(`document.querySelector('[data-face-tool="hole"]').click()`);
  await sleep(250);
  const holeToasts=await captureNewToasts(async()=>{await click(fbVp.qx, fbVp.qy);await sleep(350);});
  console.log("開口只點→toast:",explicitVerdict(toastText(holeToasts,'error').includes("開口：請拖出矩形") ? "✓" : "✗"),JSON.stringify(holeToasts));
  /* (d) select 點面內空白 → 選一個「點」,浮動列只有「開口」(GEO-189);舊凹口工具已移除 */
  await eval_(`document.querySelector('[data-face-tool="select"]').click()`);
  await sleep(250);
  await click(fbVp.qx, fbVp.qy);
  await sleep(150);
  const insFb = await eval_(`({sel: fe.sel && fe.sel.kind, bar: document.getElementById("feActionBar").hidden,
    acts: [...document.querySelectorAll("#feActionBar [data-fe-act]")].map(b=>b.dataset.feAct).join(),
    noInsert: !document.querySelector('[data-face-tool="insert"]') && !document.getElementById("notchDialog")})`);
  console.log("點面內→點選取+開口:",explicitVerdict(insFb.sel === "point" && !insFb.bar && insFb.acts === "op:hole" ? "✓" : "✗ " + JSON.stringify(insFb)),
    "| 舊凹口工具已移除:",explicitVerdict(insFb.noInsert ? "✓" : "✗"));
  await eval_(`(()=>{ fe.sel = null; fe.op = null; feSyncOverlays(); drawFaceEditor(); })()`);
  /* (e) 角材 A 空白 → toast + #tbA 標紅 */
  await eval_(`(()=>{
    document.querySelector('[data-face-tool="timber"]').click();
    const tb=document.getElementById("tbA"); if (tb) tb.value="";
  })()`);
  await sleep(250);
  const tbToasts=await captureNewToasts(async()=>{await click(fbVp.qx, fbVp.qy);await sleep(350);});
  const tbFb = await eval_(`({
    inv: document.getElementById("tbA") && document.getElementById("tbA").classList.contains("invalid")})`);
  console.log("角材A空→toast:",explicitVerdict(toastText(tbToasts,'error').includes("角材截面 A/B 須為正整數 mm") ? "✓" : "✗"),JSON.stringify(tbToasts),
    "| tbA標紅:",explicitVerdict(tbFb.inv ? "✓" : "✗"));
  /* (f) 狀態列綁定工具:切走後上一工具的訊息被手勢取代 */
  const stLife = await eval_(`(()=>{
    document.querySelector('[data-face-tool="select"]').click();
    return document.getElementById("status").textContent;
  })()`);
  console.log("切回選取→狀態列=手勢:",explicitVerdict(stLife.includes("選取") ? "✓" : "✗ " + stLife));
  /* (g) Esc 一次離開(無草稿,工具非 select 也直接走) */
  await eval_(`document.querySelector('[data-face-tool="timber"]').click()`);
  await sleep(200);
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(400);
  console.log("Esc一次離開:",explicitVerdict(await eval_(`JSON.stringify(oc.focus)`) === "null" ? "✓" : "✗"));
  /* (h) 有草稿 → 第一次 Esc 清草稿+toast,再一次才離開 */
  await eval_(`enterFocus("face", 1)`);
  await sleep(500);
  await eval_(`document.querySelector('[data-face-tool="redraw"]').click()`);
  await sleep(250);
  await click(fbVp.qx, fbVp.qy);
  await click(fbVp.cx, fbVp.cy);
  await sleep(300);
  const escDraftBefore=await eval_(`({tool:fe.tool,kind:fe.drag?.kind,points:fe.draft.pts.length,focus:oc.focus})`);
  if(escDraftBefore.tool!=='redraw'||escDraftBefore.kind!=='redraw'||escDraftBefore.points<2||escDraftBefore.focus?.t!=='face'||escDraftBefore.focus.id!==1)
    throw Error('Esc draft-clear prerequisite was not created: '+JSON.stringify(escDraftBefore));
  const escToasts=await captureNewToasts(async()=>{
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await sleep(300);
  });
  const esc1 = await eval_(`({draft: !!fe.drag||!!fe.work||fe.draft.pts.length>0,focus:oc.focus?.t==='face'&&oc.focus.id===1})`);
  console.log("Esc清草稿:",explicitVerdict(!esc1.draft ? "✓" : "✗"),
    "| toast再按Esc:",explicitVerdict(escToasts.some(t=>t.visible&&t.classes.includes('ok')&&t.text.includes('再按 Esc')) ? "✓" : "✗"),JSON.stringify(escToasts),
    "| 仍在工作區:",explicitVerdict(esc1.focus ? "✓" : "✗"));
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(400);
  console.log("第二次Esc離開:",explicitVerdict(await eval_(`JSON.stringify(oc.focus)`) === "null" ? "✓" : "✗"));

  /* ================= P15. 主畫布模式回饋 E7 =================
   * 建面工具:浮標(#canvasModeHint)+ crosshair 游標 + 狀態列頂點進度;
   * rect 單點 → toast;Esc → 清草稿+隱浮標;select → 全還原。 */
  console.log("=== P15. 主畫布模式回饋 E7 ===");
  const ocPt = await eval_(`(()=>{
    const r = document.getElementById("canvasViewport").getBoundingClientRect();
    for (const [fx, fy] of [[0.08,0.85],[0.5,0.9],[0.9,0.85],[0.9,0.2],[0.08,0.5]]) {
      const x = r.left + r.width*fx, y = r.top + r.height*fy;
      const el = document.elementFromPoint(x, y);
      if (el && el.closest("#ocv") && !el.closest(".ocard")) return {x, y};
    }
    return {x: r.left + r.width*0.5, y: r.top + r.height*0.9};
  })()`);
  /* (a) rect 工具:浮標 + crosshair */
  await eval_(`setOcTool("rect")`);
  await sleep(250);
  await clickControl('#canvasModeHintHelp');
  const mh1 = await eval_(`(()=>{const h=document.getElementById("canvasModeHint");
    return {vis:!h.hidden, txt:h.textContent,
      cur:getComputedStyle(document.getElementById("canvasViewport")).cursor};})()`);
  console.log("E7 rect 浮標:",explicitVerdict(mh1.vis && mh1.txt.includes("拖出範圍") ? "✓" : "✗ " + JSON.stringify(mh1)),
    "| 游標:",explicitVerdict(mh1.cur === "crosshair" ? "✓" : "✗ " + mh1.cur));
  /* (b) rect 只點沒拖 → toast */
  const mhToasts=await captureNewToasts(async()=>{await click(ocPt.x, ocPt.y);await sleep(400);});
  console.log("E7 rect 單點 toast:",explicitVerdict(toastText(mhToasts,'error').includes("矩形：請拖出範圍") ? "✓" : "✗"),JSON.stringify(mhToasts));
  /* (c) P 鍵(GEO-186 b):不再進入畫布繪圖工具——按一下即建預設外環的面卡、
     直接進入該面工作區並啟用「重畫外環」。 */
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "p", code: "KeyP", windowsVirtualKeyCode: 80 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "p", code: "KeyP", windowsVirtualKeyCode: 80 });
  await sleep(700);
  const mh2 = await eval_(`(()=>({
    faces: oc.faces.length,
    focus: oc.focus, tool: fe.tool,
    drawTool: oc.drawTool,
    hint: !document.getElementById("canvasModeHint").hidden}))()`);
  const mh2faces = await eval_(`api("objects").then(r=>r.faces.length)`);
  console.log("E7 P 鍵建面卡進面內:",explicitVerdict(mh2.faces === mh2faces && mh2.focus && mh2.focus.t === "face" && mh2.tool === "redraw"
      && !mh2.drawTool && !mh2.hint ? "✓" : "✗ " + JSON.stringify(mh2)));
  /* (d) Esc 離開工作區回畫布(redraw 無草稿時一次 Esc 即返回) */
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(400);
  const mh3 = await eval_(`(()=>({
    focus: oc.focus,
    vis: !document.getElementById("canvasModeHint").hidden}))()`);
  console.log("E7 Esc 回畫布:",explicitVerdict(!mh3.focus && !mh3.vis ? "✓" : "✗ " + JSON.stringify(mh3)));
  /* (e) 回選取 → 游標復原、浮標仍隱藏 */
  await eval_(`setOcTool("select")`);
  await sleep(200);
  const mh4 = await eval_(`(()=>({
    cur: getComputedStyle(document.getElementById("canvasViewport")).cursor,
    vis: !document.getElementById("canvasModeHint").hidden}))()`);
  console.log("E7 select 游標復原:",explicitVerdict(!mh4.vis && mh4.cur !== "crosshair" ? "✓" : "✗ " + JSON.stringify(mh4)));

  /* ================= P16. 放置流程 F1/A7/A8 =================
   * #placeFlow 三步條、#placeValid u⊥v 即時驗證、預設卡、游離徽章捲動。 */
  console.log("=== P16. 放置流程條 + 放置表單 ===");
  await eval_(`(async()=>{
    await api("line reset");
    await api("line boundary 1 outline 0,0 3000,0 3000,2400 0,2400");
    await api("line canvas-pos boundary 1 80 80");
    await renderObjects();
    selectObject("boundary", 1);
  })()`);
  await sleep(500);
  /* (a) 游離面:流程條存在、步1 done、步2 current、限制說明 */
  const pf1 = await eval_(`(()=>{const f=document.getElementById("placeFlow");
    if(!f) return null;
    const st=[...f.querySelectorAll(".pf-step")].map(s=>s.className);
    return {steps:st,
      note: !!document.querySelector(".pf-note")};})()`);
  console.log("P16 流程條:",explicitVerdict(pf1 && pf1.steps[0].includes("done")
    && pf1.steps[1].includes("current") ? "✓ " + pf1.steps.join(",") : "✗ " + JSON.stringify(pf1)),
    "| 游離說明:",explicitVerdict(pf1 && pf1.note ? "✓" : "✗"));
  /* (b) u=+x v=+x → 禁用+錯誤訊息;u=+x v=+y → 解禁+法向 +Z */
  await eval_(`(()=>{
    const p=document.getElementById("inspectorContent");
    p.querySelector("#placeU").value="+x";
    p.querySelector("#placeV").value="+x";
    p.querySelector("#placeV").dispatchEvent(new Event("change"));
  })()`);
  const pv1 = await eval_(`(()=>({
    dis: document.querySelector("#placeSubmit").disabled,
    txt: document.getElementById("placeValid").textContent,
    cls: document.getElementById("placeValid").className}))()`);
  console.log("P16 平行禁用:",explicitVerdict(pv1.dis && pv1.txt.includes("垂直") && pv1.cls.includes("bad") ? "✓" : "✗ " + JSON.stringify(pv1)));
  await eval_(`(()=>{
    const p=document.getElementById("inspectorContent");
    p.querySelector("#placeV").value="+y";
    p.querySelector("#placeV").dispatchEvent(new Event("change"));
  })()`);
  const pv2 = await eval_(`(()=>({
    dis: document.querySelector("#placeSubmit").disabled,
    txt: document.getElementById("placeValid").textContent}))()`);
  console.log("P16 垂直解禁:",explicitVerdict(!pv2.dis && pv2.txt.includes("+Z") ? "✓ " + pv2.txt : "✗ " + JSON.stringify(pv2)));
  /* (c) 預設卡「天花」→ u=+x v=+y;送出後 placed + 步3亮 + 鈕文案「重綁」 */
  await eval_(`(()=>{
    const b=[...document.querySelectorAll("[data-place-preset]")]
      .find(x=>x.dataset.placePreset==="天花");
    if(b) b.click();
  })()`);
  const pv3 = await eval_(`(()=>({
    u: document.querySelector("#placeU").value,
    v: document.querySelector("#placeV").value}))()`);
  console.log("P16 預設卡:",explicitVerdict(pv3.u === "+x" && pv3.v === "+y" ? "✓" : "✗ " + JSON.stringify(pv3)));
  await eval_(`document.querySelector("#placeSubmit").click()`);
  await sleep(700);
  const pf2 = await eval_(`(()=>{const f=document.getElementById("placeFlow");
    const o=ocFind("boundary",1);
    return {placed: !!o && !!o.placed,
      step3: f ? [...f.querySelectorAll(".pf-step")][2].className : "",
      btn: document.querySelector("#placeSubmit") ? document.querySelector("#placeSubmit").textContent : ""};})()`);
  console.log("P16 放置後:",explicitVerdict(pf2.placed ? "✓ placed" : "✗"),
    "| 步3:",explicitVerdict(pf2.step3.includes("current") || pf2.step3.includes("done") ? "✓" : "✗ " + pf2.step3),
    "| 鈕:",explicitVerdict(pf2.btn.includes("更新放置") ? "✓" : "✗ " + pf2.btn));
  /* (d) 刪除鈕文案含 Ctrl+Z */
  const delTxt = await eval_(`document.getElementById("inspDelete").textContent`);
  console.log("P16 刪除文案:",explicitVerdict(delTxt.includes("Ctrl+Z") ? "✓" : "✗ " + delTxt));
  /* (e) 游離面:清單徽章點擊 → 檢視器捲到放置區 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line boundary 1 outline 0,0 2000,0 2000,1500 0,1500");
    await api("line canvas-pos boundary 1 60 60");
    await renderObjects();
  })()`);
  await sleep(500);
  const badgePos = await eval_(`(()=>{
    const b=[...document.querySelectorAll(".object-row .row-badge")][0];
    if(!b) return null; const r=b.getBoundingClientRect();
    return {x:r.left+r.width/2, y:r.top+r.height/2};})()`);
  if (badgePos) {
    await click(badgePos.x, badgePos.y);
    await sleep(600);
    const sc = await eval_(`(()=>{
      const t=document.querySelector("#inspectorContent .place-block")
           || document.getElementById("placeFlow");
      if(!t) return null; const r=t.getBoundingClientRect();
      return {top:r.top, ih:innerHeight};})()`);
    console.log("P16 徽章捲動:",explicitVerdict(sc && sc.top >= 0 && sc.top < sc.ih ? "✓" : "✗ " + JSON.stringify(sc)));
  } else console.log(explicitVerdict("P16 徽章捲動: ✗ 找不到徽章"));

  /* ================= P17. 主畫布其餘 A3-A6 A9-A11 F2 ================= */
  console.log("=== P17. 主畫布其餘 ===");
  /* (a) 常駐來源入口 + 真實建立選單保留原本物件與資料入口。 */
  await clickControl('#btnCreateObject');
  const qc = await eval_(`(()=>{const pop=$('createObjectPop'),ids=['btnQuickGrid','btnCreateRect','btnCreatePoly','btnBox6','btnNewSpace','btnNewColumn','btnNewBeam'];return {open:!pop.hidden,entries:ids.map(id=>({id,inside:pop.contains($(id)),label:$(id)?.textContent.trim()})),onlyCreation:!pop.querySelector('[data-project-action="import"],#btnSpaceModelTrial,#btnSpaceModels'),permanent:['btnNewGridSystem','btnQuickBoundary'].every(id=>$(id).closest('.sidebar-left')&&$(id).getBoundingClientRect().height>=44)};})()`);
  console.log('P17 物件庫:',explicitVerdict(qc.open&&qc.permanent&&qc.onlyCreation&&qc.entries.every(e=>e.inside&&e.label)?'✓':'✗ '+JSON.stringify(qc)));
  await clickControl('#btnCreateObject');
  /* (b) chips:關空間與構件 → groupOn.structures=false + aria-pressed;全部顯示還原 */
  await clickControl('[data-filter-group="structures"]');
  await sleep(300);
  const ch1 = await eval_(`(()=>({on:oc.groupOn.structures,
    ap:document.querySelector('[data-filter-group="structures"]').getAttribute("aria-pressed")}))()`);
  console.log("P17 chip關空間與構件:",explicitVerdict(!ch1.on && ch1.ap === "false" ? "✓" : "✗ " + JSON.stringify(ch1)));
  await clickControl('#filterAll');
  await sleep(300);
  const ch2 = await eval_(`oc.groupOn.sources && oc.groupOn.bindings && oc.groupOn.structures`);
  console.log("P17 全部顯示:",explicitVerdict(ch2 ? "✓" : "✗"));
  /* (c) compact:zoom 0.5 → .ocard.compact;1.0 → 無 */
  await eval_(`oc.zoom=0.5; ocApply()`);
  await sleep(250);
  const cp1 = await eval_(`document.querySelectorAll(".ocard.compact").length`);
  await eval_(`oc.zoom=1; ocApply()`);
  await sleep(250);
  const cp2 = await eval_(`document.querySelectorAll(".ocard.compact").length`);
  console.log("P17 compact:",explicitVerdict(cp1 > 0 && cp2 === 0 ? "✓" : `✗ ${cp1}/${cp2}`));
  /* (d) 邊樣式:包含實線 + 障礙虛線 + 中文標籤 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 10 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000");
    await api("line surface 11 origin 0 0 0 u +x v +z outline 0,0 4000,0 4000,2500 0,2500");
    await api("line space 1 boundary 10 11");
    await api("line column 1 in 1 at 1000 800 size 400 400 z 0 2500");
    await api("line canvas-pos space 1 60 60");
    await renderObjects();
  })()`);
  await sleep(600);
  const ed = await eval_(`(()=>{
    const items=[...document.querySelectorAll("#edgeGroup .edge-group-item")];
    return {n:items.length,
      dash:items.map(i=>i.querySelector(".edge-path").getAttribute("stroke-dasharray")),
      labels:[...document.querySelectorAll("#edgeLabelLayer .edge-label")].map(t=>t.textContent)};})()`);
  console.log("P17 連線:",explicitVerdict(ed.n >= 2 && ed.dash.includes("6 4") && ed.dash.includes("none")
    && ed.labels.includes("包含") && ed.labels.includes("障礙")
    ? "✓ " + ed.labels.join(",") : "✗ " + JSON.stringify(ed)));
  /* (e) 空間卡語意槽 + footer 管理入口 */
  const sl = await eval_(`(()=>{
    const c=document.querySelector('.ocard[data-kind="space"]');
    return c ? c.textContent : "";})()`);
  console.log("P17 槽位語意:",explicitVerdict(sl.includes("天花") && !/\+X \d/.test(sl) ? "✓" : "✗ " + sl.slice(0, 100)));
  console.log("P17 footer管理:",explicitVerdict(sl.includes("管理成員面") && !sl.includes("缺 ") ? "✓" : "✗ " + sl.slice(-40)));
  /* (f) 組合畫布 statusbar 28px + 摘要含物件 + 成功 toast.ok */
  const stb = await eval_(`(()=>({
    h:getComputedStyle(document.querySelector(".statusbar")).height,
    sum:document.getElementById("statusSummary").textContent}))()`);
  console.log("P17 狀態列:",explicitVerdict(stb.h === "28px" && stb.sum.includes("物件") ? "✓ " + stb.sum : "✗ " + JSON.stringify(stb)));
  const successToasts=await captureNewToasts(async()=>{await eval_(`(async()=>{
    await emitLine("boundary 99 outline 0,0 500,0 500,400 0,400");
    await renderObjects();
  })()`);await sleep(400);});
  console.log("P17 成功toast:",explicitVerdict(toastText(successToasts,'ok').includes('boundary 99 outline 0,0 500,0 500,400 0,400') ? "✓" : "✗"),JSON.stringify(successToasts));
  /* (g) snap/grid 鈕在 canvas-controls + aria-pressed;minimap 112+收合鈕 */
  const ctl = await eval_(`(()=>{
    const cc=document.querySelector(".canvas-controls");
    const st=document.getElementById("snapToggle"), gt=document.getElementById("gridToggle");
    const mm=document.querySelector(".minimap-shell");
    return {inCc: cc.contains(st) && cc.contains(gt),
      ap: st.getAttribute("aria-pressed") + "/" + gt.getAttribute("aria-pressed"),
      w: Math.round(mm.getBoundingClientRect().width),
      tog: !!document.getElementById("minimapToggle")};})()`);
  console.log("P17 畫布控制:",explicitVerdict(ctl.inCc && ctl.ap === "true/true" && ctl.w === 112 && ctl.tog
    ? "✓" : "✗ " + JSON.stringify(ctl)));
  /* (h) gridToggle 關 → show-grid 消失;開回 */
  await eval_(`document.getElementById("gridToggle").click()`);
  await sleep(150);
  const g1 = await eval_(`document.getElementById("canvasViewport").classList.contains("show-grid")`);
  await eval_(`document.getElementById("gridToggle").click()`);
  await sleep(150);
  const g2 = await eval_(`document.getElementById("canvasViewport").classList.contains("show-grid")`);
  console.log("P17 格線切換:",explicitVerdict(!g1 && g2 ? "✓" : "✗"));

  /* ================= P18. 面內工作區 B1-B9 =================
   * B1 工具鈕 icon+kbd、說明區移除;B2 分頁;B3 邊表;B4 zoom 適應格線;
   * B5 標註;B6 浮標限定;B7 #feApplyCard;B8 讀數;B9 麵包屑+膠囊。 */
  console.log("=== P18. 面內工作區 B1-B9 ===");
  await eval_(`(async()=>{
    await api("line reset");
    for (const ln of [
      "surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
      "surface 2 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000",
      "space 1 boundary 1 2",
      "column 1 in 1 at 1000 800 size 400 400 z 0 2500",
      "boundary 3 outline 0,0 500,0 500,400 0,400",
    ]) await api("line " + ln);
    await renderObjects();
    await enterFocus("face", 1);
  })()`);
  await sleep(900);
  /* (1) B1:工具鈕皆含 svg+kbd;說明區塊不存在 */
  const b1 = await eval_(`(()=>{
    const btns=[...document.querySelectorAll("[data-face-tool]")];
    const panel=document.querySelector(".face-layer-panel");
    return {n:btns.length,
      ok:btns.every(b=>b.querySelector("svg")&&b.querySelector("kbd")),
      noHelp:!panel.textContent.includes("說明")};})()`);
  /* GEO-188 移除舊凹口工具後剩 6 顆(select/guide/hole/timber/redraw/pan) */
  console.log("P18 B1 工具icon+kbd:",explicitVerdict(b1.n >= 6 && b1.ok ? "✓" : `✗ n=${b1.n} ok=${b1.ok}`),
    "| 說明區已移除:",explicitVerdict(b1.noHelp ? "✓" : "✗"));
  /* (2) B2:四頁;切構件 → tbA 可見 */
  const b2 = await eval_(`(()=>{
    const tabs=[...document.querySelectorAll("[data-fi-tab]")].map(t=>t.dataset.fiTab);
    fiShowTab('timber');
    const tb=document.getElementById("tbA");
    return {tabs, vis: !!tb && tb.offsetParent !== null};})()`);
  console.log("P18 B2 四頁:",explicitVerdict(b2.tabs.join() === "prop,shape,components,underlay" ? "✓" : "✗ " + b2.tabs),
    "| 角材頁tbA可見:",explicitVerdict(b2.vis ? "✓" : "✗"));
  /* (3) B3:邊表方向文字+mm+segmented */
  const b3 = await eval_(`(()=>{
    document.querySelector('[data-fi-tab="prop"]').click();
    /* §5.A.1.10 之後 #inspectorContent 也有一份同構 .edge-row(主畫布外環邊清單),
       這裡只驗面內右欄,scope 到 #faceInspectorContent 避免兩份互相命中(見 DOM-CONTRACT)。 */
    const scope=document.querySelector("#faceInspectorContent");
    const rows=[...scope.querySelectorAll(".edge-row")];
    return {n:rows.length,
      dir:rows.every(r=>/[→←↓↑]/.test(r.querySelector(".edge-dir").textContent)),
      mm:rows.every(r=>r.querySelector(".edge-mm").textContent.trim()==="mm"),
      seg:rows.every(r=>r.querySelectorAll(".fixity-btn").length===2),
      title:scope.querySelector(".ib-sub") && scope.querySelector(".ib-sub").textContent};})()`);
  console.log("P18 B3 邊表:",explicitVerdict(b3.n === 4 && b3.dir && b3.mm && b3.seg
    ? "✓" : `✗ ${JSON.stringify(b3)}`), "| 標題:",explicitVerdict((b3.title||"").includes("固定") ? "✓" : "✗"));
  /* (4) B4:zoom 0.17 → 螢幕格距≥24px、格線<60;zoom 2 → 檔位變小 */
  const b4a = await eval_(`(()=>{
    fe.zoom=0.17; feApplyZoom();
    const xs=[...document.querySelectorAll(".fe-grid-line")]
      .filter(l=>l.getAttribute("x1")===l.getAttribute("x2"))
      .map(l=>+l.getAttribute("x1")).sort((a,b)=>a-b);
    const uniq=[...new Set(xs)];
    let min=Infinity;
    for(let i=1;i<uniq.length;++i) min=Math.min(min,uniq[i]-uniq[i-1]);
    return {n:document.querySelectorAll(".fe-grid-line").length,
      gap:min*fe.zoom};})()`);
  console.log("P18 B4 zoom0.17:",explicitVerdict(b4a.gap >= 24 && b4a.n < 60
    ? `✓ gap=${b4a.gap.toFixed(1)}px n=${b4a.n}` : `✗ ${JSON.stringify(b4a)}`));
  const b4b = await eval_(`(()=>{
    fe.zoom=2; feApplyZoom();
    const xs=[...document.querySelectorAll(".fe-grid-line")]
      .filter(l=>l.getAttribute("x1")===l.getAttribute("x2"))
      .map(l=>+l.getAttribute("x1")).sort((a,b)=>a-b);
    const uniq=[...new Set(xs)];
    return uniq.length>1?uniq[1]-uniq[0]:0;})()`);
  console.log("P18 B4 zoom2檔位變小:",explicitVerdict(b4b === 25 ? "✓ g=25" : `✗ g=${b4b}`));
  /* (5) B5:邊長標註 + 原點標 */
  const b5 = await eval_(`(()=>{
    const dims=[...document.querySelectorAll(".fe-edge-dim")];
    const texts=[...document.querySelectorAll("#faceEditorRoot text")].map(t=>t.textContent);
    return {dimN:dims.length, dimOk:dims.every(d=>/^\\d+$/.test(d.textContent)),
      origin:document.querySelectorAll('.fe-origin-mark').length===2&&!document.querySelector('.fe-origin')&&!!$('faceTechnicalDetails'),
      guide:texts.some(t=>/^[uv] = -?\\d+$/.test(t))};})()`);
  console.log("P18 B5 邊長標註:",explicitVerdict(b5.dimN >= 4 && b5.dimOk ? `✓ n=${b5.dimN}` : `✗ ${JSON.stringify(b5)}`),
    "| 原點標:",explicitVerdict(b5.origin ? "✓" : "✗"));
  /* (6) B6:select 隱藏、redraw 顯示 */
  const b6a = await eval_(`(()=>{
    document.querySelector('[data-face-tool="select"]').click();
    return document.getElementById("faceCanvasHint").hidden;})()`);
  await sleep(200);
  const b6b = await eval_(`(()=>{
    document.querySelector('[data-face-tool="redraw"]').click();
    document.getElementById('faceCanvasHintHelp').click();
    return {h:document.getElementById("faceCanvasHint").hidden,
      t:document.getElementById("faceCanvasHint").textContent};})()`);
  console.log("P18 B6 浮標:select隱藏",explicitVerdict(b6a ? "✓" : "✗"),
    "| redraw顯示",explicitVerdict(!b6b.h && b6b.t.includes("外環") ? "✓" : `✗ h=${b6b.h}`));
  await eval_(`document.querySelector('[data-face-tool="select"]').click()`);
  /* (7) B7:#feApplyCard + feCutStrip/feApplyProj;無 #b48 */
  const b7 = await eval_(`(()=>{
    const card=document.getElementById("feApplyCard");
    return {card:!!card,
      cut:card&&!!card.querySelector("#feCutStrip"),
      ap:card&&!!card.querySelector("#feApplyProj"),
      b48:!document.getElementById("b48"),
      noOld:!document.querySelector(".fe-ob-ctrl")};})()`);
  console.log("P18 B7 套用卡:",explicitVerdict(b7.card && b7.cut && b7.ap && b7.b48 && b7.noOld
    ? "✓" : "✗ " + JSON.stringify(b7)));
  /* (8) B8:讀數格式 u N v N mm(指位移動後) */
  const b8vp = await eval_(`(()=>{const r=document.getElementById("faceEditorViewport").getBoundingClientRect();
    return {x:r.left+r.width/2,y:r.top+r.height/2};})()`);
  await send("Input.dispatchMouseEvent", { type:"mouseMoved", x:b8vp.x, y:b8vp.y });
  await sleep(250);
  const b8 = await eval_(`document.getElementById("faceCoordinateReadout").textContent`);
  console.log("P18 B8 讀數:",explicitVerdict(/^u \d+ v \d+ mm$/.test(b8) ? `✓ ${b8}` : `✗ ${b8}`));
  /* (9) B9:麵包屑完整格式「空間 1 / ● 面 1」(UI-REVIEW-SPEC §S3,非子字串)+ 天花膠囊;游離面→游離 */
  const b9a = await eval_(`({
    eb:document.getElementById("workspaceEyebrow").textContent,
    cap:document.getElementById("workspacePlaceTag").textContent,
    capCls:document.getElementById("workspacePlaceTag").className,
    back:document.getElementById("workspaceBackLabel").textContent})`);
  if (b9a && b9a.__err) console.log(explicitVerdict("P18 B9 麵包屑: ✗ eval"), b9a.__err);
  else console.log("P18 B9 麵包屑:",explicitVerdict(b9a.eb === "空間 1 ›" ? "✓ " + b9a.eb : `✗ ${b9a.eb}`),
    "| 天花膠囊:",explicitVerdict(b9a.cap.includes("天花") ? "✓ " + b9a.cap : `✗ ${b9a.cap}`),
    "| 返回:",explicitVerdict(b9a.back.includes("物件畫布") ? "✓" : "✗"));
  /* (10) 游離面:角材頁停用說明 + 游離膠囊 */
  await eval_(`enterFocus("face", 3)`);
  await sleep(700);
  const b9b = await eval_(`(()=>{
    fiShowTab('timber');
    return {note:!!document.querySelector('[data-component-section="timber"] .fi-note'),
      cap:document.getElementById("workspacePlaceTag").textContent,
      tbDis:document.getElementById("tbA").disabled};})()`);
  console.log("P18 游離停用說明:",explicitVerdict(b9b.note && b9b.tbDis ? "✓" : "✗ " + JSON.stringify(b9b)),
    "| 未放置膠囊:",explicitVerdict(b9b.cap.includes("未放置") ? "✓" : "✗ " + b9b.cap));
  /* (11) 狀態列依工具顯示快捷鍵與 Esc 語意 */
  const b11 = await eval_(`(()=>{
    const s=document.getElementById('workspaceKeyHints').textContent;
    feSetTool('redraw');const r=document.getElementById('workspaceKeyHints').textContent;feSetTool('select');
    return {select:s.includes('V 框選角材')&&s.includes('Shift'),redraw:r.includes('E 外環')&&r.includes('Enter'),Esc:s.includes('Esc')&&r.includes('Esc')};})()`);
  console.log("P18 快捷鍵列:",explicitVerdict(b11.select && b11.redraw && b11.Esc ? "✓" : "✗ " + JSON.stringify(b11)));
  await eval_(`(async()=>{ if(oc.focus) await leaveFocus(); })()`);
  await sleep(400);

  /* ================= P19. 空間工作區 C1-C5 + 三視圖 D1-D3 ================= */
  console.log("=== P19. 空間工作區 + 三視圖 ===");
  await eval_(`(async()=>{
    await api("line reset");
    for (const ln of [
      "surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
      "surface 2 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000",
      "space 1 boundary 1 2",
      "column 1 in 1 at 1000 800 size 400 400 z 0 2500",
      "column 2 at 5000 5000 size 400 400 z 0 2000",
      "boundary 3 outline 0,0 500,0 500,400 0,400",
    ]) await api("line " + ln);
    await renderObjects();
    await enterFocus("space", 1);
  })()`);
  await sleep(1200);
  /* (1) C1:兩頁切換 planSvg/projSvg 輪流可見;spaceFaceGrid 不存在 */
  const c1a = await eval_(`(()=>{
    const tabs=[...document.querySelectorAll("[data-ss-tab]")].map(t=>t.dataset.ssTab);
    const planVis=()=>!document.querySelector('[data-ss-pane="plan"]').hidden;
    const projVis=()=>!document.querySelector('[data-ss-pane="proj"]').hidden;
    const a=[planVis(),projVis()];
    document.querySelector('[data-ss-tab="proj"]').click();
    const b=[planVis(),projVis()];
    document.querySelector('[data-ss-tab="plan"]').click();
    return {tabs,a,b,grid:!!document.getElementById("spaceFaceGrid")};})()`);
  console.log("P19 C1 舞台分頁:",explicitVerdict(c1a.tabs.join() === "plan,proj" &&
    c1a.a[0] && !c1a.a[1] && !c1a.b[0] && c1a.b[1] ? "✓" : "✗ " + JSON.stringify(c1a)),
    "| spaceFaceGrid移除:",explicitVerdict(!c1a.grid ? "✓" : "✗"));
  /* (2) C4:構件列 .rc-act 可點(移出);刪除 toast 含 Ctrl+Z */
  const c4 = await eval_(`(()=>{
    const rows=[...document.querySelectorAll("#spaceRcList .rc-row")];
    const r=rows[0];
    return {n:rows.length, act:r && !!r.querySelector(".rc-act"),
      actTxt:r && r.querySelector(".rc-act").textContent,
      del:r && !!r.querySelector(".face-layer-del")};})()`);
  console.log("P19 C4 構件列動作鈕:",explicitVerdict(c4.n >= 1 && c4.act && c4.del
    ? `✓ ${c4.actTxt}` : "✗ " + JSON.stringify(c4)));
  /* 點「移出」→ 構件游離;再「收進」 */
  const c4b = await eval_(`(async()=>{
    document.querySelector("#spaceRcList .rc-act").click();
    await window.__cdpSettleUI(800);
    const free1=document.querySelectorAll("#spaceRcFreeList .rc-row").length;
    document.querySelector("#spaceRcFreeList .rc-act").click();
    await window.__cdpSettleUI(800);
    const free2=document.querySelectorAll("#spaceRcFreeList .rc-row").length;
    const mine=document.querySelectorAll("#spaceRcList .rc-row").length;
    return {free1,free2,mine};})()`);
  console.log("P19 C4 移出/收進:",explicitVerdict(c4b.free1 === 2 && c4b.free2 === 1 && c4b.mine === 1
    ? "✓" : "✗ " + JSON.stringify(c4b)));
  /* 刪除 → toast 含 Ctrl+Z */
  const c4cToasts=await captureNewToasts(async()=>{await eval_(`(async()=>{
    document.querySelector("#spaceRcFreeList .face-layer-del").click();
    await window.__cdpSettleUI(800);})()`);});
  const c4c = toastText(c4cToasts,'error');
  console.log("P19 C4 刪除toast含Ctrl+Z:",explicitVerdict(c4c.includes("Ctrl+Z") ? "✓" : "✗ " + c4c));
  /* (3) C3:槽位語意名+空槽「放置一片面」可點 */
  const c3 = await eval_(`(()=>{
    const rows=[...document.querySelectorAll("#spaceInspectorContent .slot-row")];
    return {n:rows.length,
      names:rows.map(r=>r.querySelector(".slot-name").textContent),
      axis:rows.every(r=>/[-+xyzXYZ=DW]/.test(r.querySelector(".slot-axis").textContent)),
      empty:rows.filter(r=>r.querySelector(".slot-empty")).length};})()`);
  console.log("P19 C3 槽位語意:",explicitVerdict(c3.n === 6 && c3.names.includes("天花")
    && c3.names.includes("前牆") && c3.axis ? "✓" : "✗ " + JSON.stringify(c3)),
    "| 空槽鈕:",explicitVerdict(c3.empty >= 3 ? `✓ ${c3.empty}` : `✗ ${c3.empty}`));
  const c3bToasts=await captureNewToasts(async()=>{await eval_(`document.querySelector(".slot-empty").click()`);await sleep(800);});
  const c3b = await eval_(`({focus:oc.focus && oc.focus.t==="face"})`);c3b.toast=c3bToasts.filter(t=>t.visible).map(t=>t.text).join('|');
  console.log("P19 C3 空槽點擊有反應:",explicitVerdict(c3b.focus || c3b.toast.includes("預設")
    ? `✓ focus=${c3b.focus}` : "✗ " + JSON.stringify(c3b)));
  await eval_(`(async()=>{ if(oc.focus) await leaveFocus(); await enterFocus("space",1); })()`);
  await sleep(800);
  /* (4) C5:#spProjRefresh 不存在;mutate(刪柱)後 spaceProjSvg 自動更新 */
  const c5 = await eval_(`(async()=>{
    const noBtn=!document.getElementById("spProjRefresh");
    const before=document.getElementById("spaceProjSvg").innerHTML.length;
    await emitLine("delete column 1");
    await window.__cdpSettleUI(900);
    const after=document.getElementById("spaceProjSvg").innerHTML.length;
    return {noBtn,before,after};})()`);
  console.log("P19 C5 無refresh鈕:",explicitVerdict(c5.noBtn ? "✓" : "✗"),
    "| 自動更新:",explicitVerdict(c5.after !== c5.before ? `✓ ${c5.before}→${c5.after}` : `✗ ${c5.before}→${c5.after}`));
  await eval_(`(async()=>{ if(oc.focus) await leaveFocus(); })()`);
  await sleep(400);
  /* (5) D1:三視圖開 → 左 #v3Panel 視圖/圖層勾選;右 #v3PickPanel */
  await eval_(`document.getElementById("btnObj").click()`);
  await sleep(900);
  const d1 = await eval_(`(()=>{
    const vp=document.getElementById("v3Panel");
    return {vis: vp && !vp.hidden && vp.offsetParent !== null,
      views:document.querySelectorAll("[data-v3-view]").length,
      layers:document.querySelectorAll("[data-v3-layer]").length,
      pick:!document.getElementById("v3PickPanel").hidden};})()`);
  console.log("P19 D1 左欄視圖/圖層:",explicitVerdict(d1.vis && d1.views === 3 && d1.layers === 4
    ? "✓" : "✗ " + JSON.stringify(d1)),
    "| 右欄pick容器:",explicitVerdict(d1.pick ? "✓" : "✗"));
  /* (6) D2:#tool 非原生顯示(segmented)+三視圖縮放列 */
  const d2 = await eval_(`(()=>{
    const sel=document.getElementById("tool");
    const cs=getComputedStyle(sel);
    return {nativeHidden: +cs.opacity < 0.1 || cs.display === "none" ||
      sel.classList.contains("v3-native-select"),
      seg:document.querySelectorAll("[data-v3-tool]").length,
      segActive:document.querySelector("[data-v3-tool].active").dataset.v3Tool,
      /* 🔒 Q17(GEO-181):三視圖舊多邊形工具已移除,建多邊形面只走主畫布 P(PolyDraft) */
      noPoly:!document.querySelector('[data-v3-tool="poly"]') && !sel.querySelector('option[value="poly"]'),
      zoom:!!document.querySelector(".v3-zoom")};})()`);
  console.log("P19 D2 segmented:",explicitVerdict(d2.nativeHidden && d2.seg === 4 && d2.noPoly && d2.segActive === "view"
    ? "✓" : "✗ " + JSON.stringify(d2)),
    "| 縮放列:",explicitVerdict(d2.zoom ? "✓" : "✗"));
  /* segmented 切工具 → #tool 同步 */
  const d2b = await eval_(`(()=>{
    document.querySelector('[data-v3-tool="rect"]').click();
    return {tool:document.getElementById("tool").value,
      act:document.querySelector("[data-v3-tool].active").dataset.v3Tool};})()`);
  console.log("P19 D2 切工具同步:",explicitVerdict(d2b.tool === "rect" && d2b.act === "rect"
    ? "✓" : "✗ " + JSON.stringify(d2b)));
  await eval_(`document.querySelector('[data-v3-tool="view"]').click()`);
  /* (7) D3:zoom 反比縮放——font-size(mm) 隨 zoom 反比,螢幕 px 不變 */
  const d3 = await eval_(`(()=>{
    const tx=document.querySelector("#world text[data-fs0]");
    if(!tx) return {none:true};
    const z0=zoom, fs0=+tx.getAttribute("font-size"), px0=fs0*transform().s;
    zoom=2; applyTransform();
    const fs2=+tx.getAttribute("font-size"), px2=fs2*transform().s;
    zoom=0.5; applyTransform();
    const fsH=+tx.getAttribute("font-size"), pxH=fsH*transform().s;
    zoom=z0; applyTransform();
    return {px0,px2,pxH};})()`);
  console.log("P19 D3 字級恆定:",explicitVerdict(d3.none ? "✗ 無文字" :
    (Math.abs(d3.px2 - d3.px0) < 0.5 && Math.abs(d3.pxH - d3.px0) < 0.5
      ? `✓ ${d3.px0.toFixed(1)}px 恆定` : `✗ ${JSON.stringify(d3)}`)));
  /* (8) D1 圖層過濾生效:關掉「面」→ world 面元素減少 */
  const d1b = await eval_(`(async()=>{
    const before=document.querySelectorAll("#world polygon").length;
    document.querySelector('[data-v3-layer="face"]').click();
    await window.__cdpSettleUI(600);
    const after=document.querySelectorAll("#world polygon").length;
    document.querySelector('[data-v3-layer="face"]').click();
    await window.__cdpSettleUI(600);
    return {before,after};})()`);
  console.log("P19 D1 圖層過濾:",explicitVerdict(d1b.after < d1b.before
    ? `✓ ${d1b.before}→${d1b.after}` : `✗ ${JSON.stringify(d1b)}`));
  await eval_(`document.getElementById("btnCanvasView").click()`);
  await sleep(600);

  console.log("=== 10. 三視圖覆層再開 ===");
  await eval_(`document.getElementById("btnObj").click()`);
  await sleep(800);
  console.log("cv hidden:", await eval_(`document.getElementById("cv").hasAttribute("hidden")`));
  console.log("world children:", await eval_(`document.getElementById("world").childElementCount`));

  /* ================= Bugfix 2026-09-14 ================= */
  console.log("=== BF2. 一按就壞/會丟資料 ===");
  await eval_(`document.getElementById("btnCanvasView").click()`);
  await eval_(`api("line reset")`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`api("line canvas-pos boundary 1 60 60")`);
  await eval_(`renderObjects()`);
  await sleep(800);
  /* (a) 「顯示全部」:ocFit() 無參數曾是 TypeError → 例外計數不得增加 */
  const exc0 = excN;
  await eval_(`document.getElementById("btnZoom").click()`);
  await sleep(500);
  console.log("BF2 btnZoom 無例外:",explicitVerdict(excN === exc0 ? "✓" : "✗ exc=" + (excN - exc0)));
  /* (b) 放大鈕曾把 transform 變 NaN → 畫布消失 */
  await eval_(`document.getElementById("zoomInButton").click()`);
  await sleep(400);
  const tf = await eval_(`document.getElementById("oroot").getAttribute("transform")`);
  console.log("BF2 zoom transform:", tf,explicitVerdict(tf && !/NaN/.test(tf) ? "✓" : "✗"));
  /* (c) /upload 後 curScene/標籤同步;btnScene 載回上傳內容,不載回 room_a */
  const fsB = require("fs"), osB = require("os"), pathB = require("path");
  const up = pathB.join(osB.tmpdir(), "verify-upload-bf.scene");
  fsB.writeFileSync(up, "boundary 1 outline 0,0 111,0 111,222 0,222\n");
  const doc = await send("DOM.getDocument");
  const fnode = await send("DOM.querySelector", { nodeId: doc.result.root.nodeId, selector: "#file" });
  await send("DOM.setFileInputFiles", { files: [up], nodeId: fnode.result.nodeId });
  await sleep(1500);
  const up1 = await eval_(`(async()=>({name:curScene.name,
    label:document.getElementById("sceneMenuLabel").textContent,
    mark:(await api("dump")).text.includes("111,222")}))()`);
  console.log("BF2 upload curScene:", JSON.stringify(up1),explicitVerdict(up1.name === "verify-upload-bf.scene" && up1.mark ? "✓" : "✗"));
  await eval_(`loadScene(curScene.path,curScene.name)`);
  await sleep(1500);
  const up2 = await eval_(`(async()=>{const t=(await api("dump")).text;
    return {mark:t.includes("111,222"),roomA:t.includes("guide 1 1 v spec:主支1中線")}})()`);
  console.log("BF2 上傳場景重載不載回 room_a:", JSON.stringify(up2),explicitVerdict(up2.mark && !up2.roomA ? "✓" : "✗"));
  /* (d) 換場景清焦點:enterFocus → loadScene → focus null、工作區關閉 */
  await eval_(`api("line reset")`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`api("line placement 1 on boundary 1 origin 0 0 2500 u +x v +y")`);
  await eval_(`api("line canvas-pos boundary 1 60 60")`);
  await eval_(`renderObjects()`);
  await sleep(800);
  await eval_(`enterFocus("face",1)`);
  await sleep(800);
  const fpre = await eval_(`({focus:oc.focus && oc.focus.t,g:fe.guides.length})`);
  /* 路徑向 /scenes 取(伺服器端絕對路徑),不寫死——Windows 與 WSL 皆可跑。 */
  await eval_(`(async()=>{
    const list = await fetch("/scenes").then(r => r.json());
    const s = list.find(x => x.name === "room_a.scene");
    if (!s) throw new Error("/scenes 沒有 room_a.scene");
    return loadScene(s.path, s.name);
  })()`);
  await sleep(1800);
  const fpost = await eval_(`({focus:oc.focus,
    wsHidden:document.getElementById("objectWorkspace").hidden,
    guides:fe.guides.length,stack:oc.stack.length})`);
  console.log("BF2 換場景清焦點:", JSON.stringify(fpre), "→", JSON.stringify(fpost),explicitVerdict(fpre.focus === "face" && fpost.focus === null && fpost.wsHidden === true &&
    fpost.guides === 0 && fpost.stack === 0 ? "✓" : "✗"));

  /* ================= BF3. undo 群組(L2) ================= */
  console.log("=== BF3. undo 群組 ===");
  /* 六面盒是 mutate 多行交易 → 一次 Ctrl+Z 應全退 */
  await eval_(`api("line reset")`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`renderObjects()`);
  await sleep(600);
  const bf3pre = await eval_(`api("objects").then(r=>r.faces.length)`);
  await clickControl('#btnBox6');
  await sleep(300);
  await eval_(`document.getElementById("box6Submit").click()`);
  await sleep(1500);
  const bf3mid = await eval_(`api("objects").then(r=>r.faces.length)`);
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "z", code: "KeyZ", modifiers: 2, windowsVirtualKeyCode: 90 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "z", code: "KeyZ", modifiers: 2, windowsVirtualKeyCode: 90 });
  await sleep(1200);
  const bf3post = await eval_(`api("objects").then(r=>r.faces.length)`);
  console.log("BF3 六面盒一次 Ctrl+Z 全退:", bf3pre, "→", bf3mid, "→", bf3post,explicitVerdict(bf3mid === bf3pre + 6 && bf3post === bf3pre ? "✓" : "✗"));

  /* ================= BF4. 其餘功能錯誤 ================= */
  console.log("=== BF4. 功能錯誤 ===");
  await eval_(`window.__apiLog = []; { const _a = api;
    api = c => { __apiLog.push(c); return _a(c); }; }`);
  /* (b) 六面盒排版避讓:既有卡佔 (60,60) 時,新卡不得同座標 */
  await eval_(`api("line reset")`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`api("line canvas-pos boundary 1 60 60")`);
  await eval_(`renderObjects()`); await sleep(500);
  await clickControl('#btnBox6'); await sleep(300);
  await eval_(`document.getElementById("box6Submit").click()`); await sleep(1500);
  const bf4dup = await eval_(`api("dump").then(r => {
    const seen = {}, dups = [];
    for (const l of r.text.split("\\n")) {
      const m = l.match(/^canvas-pos \\S+ \\d+ (-?\\d+) (-?\\d+)$/);
      if (m) { const k = m[1] + "," + m[2]; if (seen[k]) dups.push(k); seen[k] = 1; }
    }
    return dups; })`);
  console.log("BF4 六面盒排版無重疊:", JSON.stringify(bf4dup),explicitVerdict(bf4dup.length === 0 ? "✓" : "✗"));
  /* (b2) GEO-157:六面盒不得覆寫既有物件。
     世界 boundary {1,2,5,9,MAX}、placement {MAX} → newid.boundary=3、newid.placement=0,
     舊算法 b0 = max(3,0) = 3,用掉 3,4,5,6,7,8——其中 5 已經存在,
     而 `surface` 對既有 id 是交易式重宣告＝**靜默覆寫**(狀態列照樣顯示 ✓)。
     修好之後會跳過 5,既有的 boundary 5 原封不動。 */
  for (const c of ["reset",
                   "surface 4294967295 origin 0 0 200 u +x v +y outline 0,0 100,0 100,100 0,100",
                   "boundary 9 outline 0,0 40,0 40,40 0,40",
                   "boundary 1 outline 0,0 50,0 50,50 0,50",
                   "boundary 2 outline 0,0 60,0 60,60 0,60",
                   "boundary 5 outline 0,0 90,0 90,90 0,90"]) {
    const result = await eval_(`api(${JSON.stringify("line " + c)})`);
    if (result?.ok !== true) throw new Error("BF4 夾具建立失敗: " + c + " " + JSON.stringify(result));
  }
  await eval_(`renderObjects()`); await sleep(500);
  await clickControl('#btnBox6'); await sleep(300);
  await eval_(`document.getElementById("box6W").value = 4000;
               document.getElementById("box6D").value = 3000;
               document.getElementById("box6H").value = 2500;
               document.getElementById("box6Floor").checked = true;`);
  await eval_(`document.getElementById("box6Submit").click()`); await sleep(1500);
  const bf4keep = await eval_(`api("dump").then(r => {
    const rows = r.text.split("\\n");
    return { kept: rows.includes("boundary 5 outline 0,0 90,0 90,90 0,90"),
             faces: rows.filter(l => l.startsWith("boundary ")).length }; })`);
  console.log("BF4 六面盒不覆寫既有面(GEO-157):", JSON.stringify(bf4keep),explicitVerdict(bf4keep.kept && bf4keep.faces === 11 ? "✓" : "✗"));
  /* (b3) GEO-157:0 沒被占用時也不能發給 surface(D4 的 boundary_id=0 是矩形標記)。 */
  const bf4zeroSeed = await eval_(`(async () => {
    const reset = await api("line reset");
    const seed = await api("line surface 4294967295 origin 0 0 200 u +x v +y outline 0,0 100,0 100,100 0,100");
    return reset.ok && seed.ok;
  })()`);
  await eval_(`renderObjects()`); await sleep(500);
  await clickControl('#btnBox6'); await sleep(300);
  await eval_(`document.getElementById("box6W").value = 4000;
               document.getElementById("box6D").value = 3000;
               document.getElementById("box6H").value = 2500;
               document.getElementById("box6Floor").checked = true;`);
  await eval_(`document.getElementById("box6Submit").click()`); await sleep(1500);
  const bf4zero = await eval_(`(async () => {
    const dump = await api("dump"), objects = await api("objects");
    const rows = dump.text.split("\\n");
    return { kept: rows.includes("boundary 4294967295 outline 0,0 100,0 100,100 0,100"),
             faces: rows.filter(l => l.startsWith("boundary ")).length,
             spaces: objects.spaces.length, closed: objects.spaces[0]?.closed };
  })()`);
  console.log("BF4 六面盒回繞跳過保留編號0(GEO-157):", JSON.stringify(bf4zero),explicitVerdict(bf4zeroSeed === true && bf4zero.kept && bf4zero.faces === 7 &&
    bf4zero.spaces === 1 && bf4zero.closed ? "✓" : "✗"));
  /* (b4) GEO-164:空間配號回繞也必須跳過 0 與已存在的空間 1。 */
  const bf4spaceSeed = await eval_(`api("line space 4294967295 boundary")`);
  if (bf4spaceSeed?.ok !== true) throw new Error("BF4 空間回繞夾具失敗: " + JSON.stringify(bf4spaceSeed));
  await clickControl('#btnBox6'); await sleep(300);
  await eval_(`document.getElementById("box6W").value = 4000;
               document.getElementById("box6D").value = 3000;
               document.getElementById("box6H").value = 2500;
               document.getElementById("box6Floor").checked = true;`);
  await eval_(`document.getElementById("box6Submit").click()`); await sleep(1500);
  const bf4spaces = await eval_(`api("objects").then(r => r.spaces.map(s => ({id:s.id, closed:s.closed})))`);
  console.log("BF4 空間回繞跳過保留編號0及既有空間(GEO-164):", JSON.stringify(bf4spaces),explicitVerdict(bf4spaces.length === 3 && bf4spaces.some(s => s.id === 1 && s.closed) &&
    bf4spaces.some(s => s.id === 2 && s.closed) && bf4spaces.some(s => s.id === 4294967295) ? "✓" : "✗"));
  /* (a) 空間示意圖 toRoom:點地板左上角內側 2px → 映射點(柱中心)應在角 100mm 內 */
  const bf4sp = await eval_(`api("objects").then(r => r.spaces[0] && r.spaces[0].id)`);
  await eval_(`enterFocus("space", ${bf4sp})`); await sleep(1000);
  const bf4pt = await eval_(`(() => {
    const f = document.querySelector("#spacePlanSvg .space-plan-floor");
    if (!f) return null;
    const r = f.getBoundingClientRect();
    return { x: r.x + 2, y: r.y + 2 }; })()`);
  await eval_(`window.__apiLog.length = 0`);
  if (bf4pt) await click(bf4pt.x, bf4pt.y);
  await sleep(1000);
  const bf4line = await eval_(`__apiLog.find(c => c.indexOf("column") >= 0) || ""`);
  const bf4m = /at (-?\d+) (-?\d+)/.exec(bf4line);
  /* at x y = 映射點 - 半柱邊(600/2=300);還原映射點驗證 ≈ 房角 (0,0) */
  const bf4px = bf4m && +bf4m[1] + 300, bf4py = bf4m && +bf4m[2] + 300;
  console.log("BF4 平面點放柱映射:", bf4line, "→ 映射點", bf4px + "," + bf4py,explicitVerdict(bf4m && Math.abs(bf4px) < 100 && Math.abs(bf4py) < 100 ? "✓" : "✗"));
  /* (c) 面內 undo 刷新:刪 guide → 面內復原 → fe.guides 與 dump 一致 */
  await eval_(`leaveFocus()`); await sleep(400);
  await eval_(`api("line reset")`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`api("line placement 1 on boundary 1 origin 0 0 2500 u +x v +y")`);
  await eval_(`(async()=>{await api("line spec 線位置 500"); await api("line guide 1 1 u spec:線位置")})()`);
  await eval_(`(async()=>{await api("line spec 線位置2 700"); await api("line guide 2 1 v spec:線位置2")})()`);
  await eval_(`renderObjects()`); await sleep(500);
  await eval_(`enterFocus("face",1)`); await sleep(800);
  await eval_(`api("line delete guide 2")`);
  await eval_(`feLoadGuides()`);            /* 同 UI 刪除後的快取狀態=1 */
  await eval_(`document.getElementById("faceUndoButton").click()`); await sleep(1200);
  const bf4g = await eval_(`(async () => ({ fe: fe.guides.length,
    dump: (await api("dump")).text.split("\\n").filter(l => /^guide /.test(l)).length }))()`);
  console.log("BF4 面內 undo 刷新:", JSON.stringify(bf4g),explicitVerdict(bf4g.fe === 2 && bf4g.dump === 2 ? "✓" : "✗"));
  /* (e) Esc 在輸入框不關工作區:聚焦 .edge-len 按 Esc → 工作區仍開
     §5.A.1.10 之後 #inspectorContent 也有一份同構 .edge-len(主畫布外環邊清單,
     可能因 hidden 而 focus() 失敗),scope 到 #faceInspectorContent 避免誤命中。 */
  await eval_(`fiShowTab("prop")`); await sleep(300);
  const bf4hasLen = await eval_(`(() => {
    const i = document.querySelector("#faceInspectorContent .edge-len");
    if (i) { i.focus(); } return !!i && document.activeElement === i; })()`);
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(600);
  const bf4ws = await eval_(`document.getElementById("objectWorkspace").hidden`);
  console.log("BF4 Esc 輸入框不關工作區:", "focused=" + bf4hasLen, "wsHidden=" + bf4ws,explicitVerdict(bf4ws === false && bf4hasLen ? "✓" : "✗"));
  /* (d) RC 表單驗證:x 留空 → 不送 column;w 留空 → 不送任何 line + 表單提示 */
  await eval_(`leaveFocus()`); await sleep(400);
  await eval_(`window.__apiLog.length = 0`);
  await clickControl('#btnNewColumn'); await sleep(300);
  await eval_(`document.getElementById("rcX").value = ""`);
  await eval_(`document.getElementById("rcSubmit").click()`); await sleep(500);
  const bf4rc1 = await eval_(`__apiLog.filter(c => c.startsWith("line") || c === "newid")`);
  console.log("BF4 RC 空 x 不送指令:", JSON.stringify(bf4rc1),explicitVerdict(bf4rc1.length === 0 ? "✓" : "✗"));
  await eval_(`window.__apiLog.length = 0;
    document.getElementById("rcW").value = ""; document.getElementById("rcX").value = "0"`);
  await eval_(`document.getElementById("rcSubmit").click()`); await sleep(500);
  const bf4rc2 = await eval_(`__apiLog.filter(c => c.startsWith("line") || c === "newid")`);
  const bf4err = await eval_(`!document.getElementById("rcErr").hidden`);
  console.log("BF4 RC 空 w 不送+表單提示:", JSON.stringify(bf4rc2),explicitVerdict(bf4rc2.length === 0 && bf4err ? "✓" : "✗"));
  await eval_(`document.getElementById("rcCancel").click()`);

  /* ================= P20. 對抗審查漂移修正(A3 A4 A9 A10/A11 B1 B3 + toast/busy) =================
   * 對應 audit-A.md/audit-B.md 揪出的假完成項:斷言要咬住「修前」的錯誤做法。 */
  console.log("=== P20. 對抗審查漂移修正 ===");
  /* (a) 新組合版面：網格與邊界常駐，不依賴隱藏選單或空白世界。 */
  const p20a3=await eval_(`['btnCreateObject','btnNewGridSystem','btnQuickBoundary'].map(id=>{const e=$(id),r=e.getBoundingClientRect();return {id,visible:r.width>0&&r.height>=44&&r.top>=0&&r.bottom<=innerHeight,hit:e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))};})`);
  console.log('P20 A3 常駐建立入口:',explicitVerdict(p20a3.every(e=>e.visible&&e.hit)?'✓':'✗ '+JSON.stringify(p20a3)));
  /* (b) A10/A11:minimapToggle 熱區 ≥28×28(原 20×20) */
  const p20a10 = await eval_(`(()=>{const r=document.getElementById("minimapToggle").getBoundingClientRect();
    return {w:Math.round(r.width),h:Math.round(r.height)};})()`);
  console.log("P20 A10 minimapToggle熱區≥28:",explicitVerdict(p20a10.w >= 28 && p20a10.h >= 28
    ? `✓ ${p20a10.w}×${p20a10.h}` : `✗ ${JSON.stringify(p20a10)}`));
  /* (c) toast 避讓小地圖:.toast-region bottom ≥ 118(14+96+8),原 42 會被小地圖蓋住 */
  const p20tr = await eval_(`parseFloat(getComputedStyle(document.querySelector(".toast-region")).bottom)`);
  console.log("P20 toast避讓小地圖:",explicitVerdict(p20tr >= 118 ? `✓ bottom=${p20tr}px` : `✗ bottom=${p20tr}px`));
  /* (d) 建物件:free 面(boundary 3)+ space(1,由已放置 boundary 1/2 組成,帶 guide)供 A4/B1/B3 用 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    await api("line surface 2 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000");
    await api("line space 1 boundary 1 2");
    await api("line spec 線位置 500"); await api("line guide 1 1 u spec:線位置");
    await api("line boundary 3 outline 0,0 500,0 500,400 0,400");
    await api("line canvas-pos boundary 3 500 60");
    await api("line canvas-pos space 1 60 60");
    await renderObjects();
  })()`);
  await sleep(700);
  /* (e) 來源卡標題 15px；空間卡保留既有 12.5px 可讀字級。 */
  const p20a4 = await eval_(`(()=>{
    const fc = document.querySelector('.ocard[data-kind="boundary"] text');
    const sc = document.querySelector('.ocard[data-kind="space"] text');
    return {f: fc && fc.getAttribute("font-size"), s: sc && sc.getAttribute("font-size")};})()`);
  console.log("P20 A4 來源與空間卡片標題:",explicitVerdict(p20a4.f === "15" && p20a4.s === "12.5"
    ? "✓" : `✗ ${JSON.stringify(p20a4)}`));
  /* (f) A9:成功 toast 的 .toast.ok svg 著色 = --face(原無 .toast.ok 規則) */
  // Capture the real success toast when it appears; slow bridge refreshes can
  // outlive its deliberately short 2000 ms lifetime.
  const p20a9 = await eval_(`(async()=>{
    let captured=null;
    const observer=new MutationObserver(records=>{
      for(const record of records)for(const node of record.addedNodes){
        const svg=node.matches?.('.toast.ok') && node.querySelector('svg');if(!svg)continue;
        const probe=document.createElement('span');probe.style.color='var(--face)';document.body.appendChild(probe);
        captured={got:getComputedStyle(svg).color,want:getComputedStyle(probe).color};probe.remove();
      }
    });
    observer.observe($('toastRegion'),{childList:true});
    await emitLine('boundary 77 outline 0,0 300,0 300,300 0,300');observer.disconnect();
    await renderObjects();return captured;
  })()`);
  console.log("P20 A9 toast.ok著色:",explicitVerdict(p20a9 && p20a9.got === p20a9.want
    ? `✓ ${p20a9.got}` : `✗ ${JSON.stringify(p20a9)}`));
  /* (g) B1:面內圖層列 .face-layer-icon 一律 svg,不含 ▱▨⌖▤╬ 純文字 */
  await eval_(`enterFocus("face", 1)`);
  await sleep(700);
  await eval_(`fiShowTab("prop")`);
  await sleep(200);
  /* 範圍限定 #faceLayerList(renderFaceLayers() 的圖層列),避開 #workspaceTypeIcon
     這個同名 class 但語意無關的頂列型別圖示(index.html 靜態標記,非 B1 範圍) */
  const p20b1 = await eval_(`(()=>{
    const icons = [...document.querySelectorAll("#faceLayerList .face-layer-icon")];
    return {n: icons.length,
      svgN: icons.filter(i => i.querySelector("svg")).length,
      bad: icons.some(i => /[▱▨⌖▤╬]/.test(i.textContent))};})()`);
  console.log("P20 B1 圖層列SVG圖示:",explicitVerdict(p20b1.n >= 1 && p20b1.svgN === p20b1.n && !p20b1.bad
    ? `✓ n=${p20b1.n}` : `✗ ${JSON.stringify(p20b1)}`));
  /* (h) B3:.fixity-btn.seg 熱區高度 ≥28(原 22) */
  const p20b3 = await eval_(`(()=>{
    const btns = [...document.querySelectorAll(".fixity-btn.seg")];
    return {n: btns.length,
      minH: btns.length ? Math.min(...btns.map(b => b.getBoundingClientRect().height)) : 0};})()`);
  console.log("P20 B3 fixity-btn熱區≥28:",explicitVerdict(p20b3.n >= 1 && p20b3.minH >= 28
    ? `✓ n=${p20b3.n} minH=${p20b3.minH}` : `✗ ${JSON.stringify(p20b3)}`));
  await eval_(`leaveFocus()`);
  await sleep(400);
  /* (i) v2:短操作不閃動;超過 400 ms 才顯示進度,結束收起。 */
  const p20busy = await eval_(`(async () => {
    const original = api;
    let delayed = false;
    api = async cmd => { if (!delayed) { delayed=true; await window.__cdpSettleUI(800); } return original(cmd); };
    try {
      const p = mutate(["boundary 555 outline 0,0 10,0 10,10 0,10"]);
      const early = document.getElementById("busyIndicator").hidden;
      await window.__cdpSettleUI(500);
      const mid = document.getElementById("busyIndicator").hidden;
      const opacity = getComputedStyle(document.querySelector('.workspace')).opacity;
      await p;
      return {early, mid, after:document.getElementById("busyIndicator").hidden, opacity};
    } finally { api=original; }
  })()`);
  console.log("P20 busy指示:",explicitVerdict(p20busy.early && !p20busy.mid && p20busy.after && p20busy.opacity === '1'
    ? "✓" : `✗ ${JSON.stringify(p20busy)}`));
  /* (j) §S1 全域最小字級 11px:主畫布／面內／空間工作區三畫面全掃描,
     不得有任何可見元素 computed font-size < 11px。
     排除:①未顯示元素(如空的 .toast-region)因寬高為 0 自然排除,不需另立白名單;
     ②SVG 命名空間下畫布繪製的 <text>/<tspan>(卡片副標、狀態膠囊「游離/無邊界」、
     空間卡槽位軸標、面內原點座標標註)——這些數值由 §S2 明文另訂
     (「副標 10.5＋狀態膠囊 10.5」),不屬 §S1『元件最小 11px』規範對象,
     此處明文排除、非隨意放寬。 */
  await eval_(`window.__scanMinFont = () => {
    let min = Infinity, sel = "";
    for (const el of document.querySelectorAll("body *")) {
      if (el.namespaceURI === "http://www.w3.org/2000/svg") continue;
      const cs = getComputedStyle(el);
      if (cs.display === "none" || cs.visibility === "hidden") continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const fs = parseFloat(cs.fontSize);
      if (fs && fs < min) { min = fs;
        sel = (el.id ? "#" + el.id : "") + (el.className ? "." + String(el.className).split(" ")[0] : "") || el.tagName; }
    }
    return {min, sel};
  }`);
  const p20fontMain = await eval_(`__scanMinFont()`);
  await eval_(`enterFocus("face", 1)`);
  await sleep(500);
  const p20fontFace = await eval_(`__scanMinFont()`);
  await eval_(`(async()=>{ await leaveFocus(); await enterFocus("space", 1); })()`);
  await sleep(500);
  const p20fontSpace = await eval_(`__scanMinFont()`);
  const p20fontAll = [["主畫布", p20fontMain], ["面內", p20fontFace], ["空間工作區", p20fontSpace]];
  const p20fontBad = p20fontAll.filter(([, v]) => !(v.min >= 11));
  console.log("P20 全域最小字級≥11px:",explicitVerdict(p20fontBad.length === 0
    ? `✓ ${p20fontAll.map(([n, v]) => `${n}=${v.min}`).join(" ")}`
    : `✗ ${p20fontBad.map(([n, v]) => `${n}: min=${v.min}px @ ${v.sel}`).join("; ")}`));
  /* (k) B-icon:.space-member-thumb 無承載面(bmap 缺失)時走 icon("rectangle")
     SVG 佔位,不留 ▱▨⌖▤╬ 等 Unicode 圖示字元。目前處於空間 1 工作區
     (成員 1 2 皆已放置、bmap 皆有值),故先人為刪除成員 2 的 bmap 條目
     模擬「無承載面資料」情形,重繪縮圖列後檢查該格內容。 */
  const p20thumb = await eval_(`(async()=>{
    delete oc.bmap[2];
    await renderSpaceWorkspace();
    const rows = [...document.querySelectorAll(".space-member-thumb")];
    return {n: rows.length,
      bad: rows.some(t => /[▱▨⌖▤╬]/.test(t.textContent)),
      svgN: rows.filter(t => t.querySelector("svg")).length};})()`);
  console.log("P20 space-member-thumb無殘留Unicode圖示:",explicitVerdict(p20thumb.n >= 1 && !p20thumb.bad && p20thumb.svgN === p20thumb.n
    ? `✓ n=${p20thumb.n} svgN=${p20thumb.svgN}` : `✗ ${JSON.stringify(p20thumb)}`));
  await eval_(`leaveFocus()`);
  await sleep(400);

  /* ================= P21. 對抗審查漂移修正(C1 C3 C4 D2) =================
   * 對應 audit-CD.md 揪出的 PARTIAL 項:C1 佔滿高度、C3 空槽直達放置、
   * C4 移出/收進鈕熱區、D2 縮放列移左下。斷言要咬住「修前」的錯誤做法。 */
  console.log("=== P21. 對抗審查漂移修正(空間工作區/三視圖) ===");
  /* (a) C1:空間工作區「平面示意」舞台內容高度 ≥ 可用高度 85%,且無捲軸 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    await api("line space 1 boundary 1");
    await api("line canvas-pos space 1 60 60");
    await renderObjects();
    await enterFocus("space", 1);
  })()`);
  await sleep(600);
  const p21c1 = await eval_(`(()=>{
    const stage = document.querySelector(".space-workspace-stage");
    const strip = document.querySelector(".space-plan-strip");
    if (!stage || !strip) return null;
    const sr = stage.getBoundingClientRect(), cr = strip.getBoundingClientRect();
    return { ratio: +(cr.height / sr.height).toFixed(3),
      overflow: stage.scrollHeight > stage.clientHeight + 2,
      sh: Math.round(sr.height), ch: Math.round(cr.height) };
  })()`);
  console.log("P21 C1 舞台佔滿高度:",explicitVerdict(p21c1 && p21c1.ratio >= 0.85 && !p21c1.overflow
    ? `✓ ratio=${p21c1.ratio} h=${p21c1.ch}/${p21c1.sh}` : `✗ ${JSON.stringify(p21c1)}`));

  /* (b) C3:空槽點擊直達放置——帶入槽位對應預設 u/v,且選中的是預期的游離面 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    await api("line space 1 boundary 1");
    await api("line boundary 10 outline 0,0 400,0 400,300 0,300");
    await api("line canvas-pos space 1 60 60");
    await api("line canvas-pos boundary 10 400 60");
    await renderObjects();
    await enterFocus("space", 1);
  })()`);
  await sleep(600);
  const p21c3click = await eval_(`(()=>{
    const b = [...document.querySelectorAll(".slot-empty")]
      .find(x => x.dataset.slotLabel === "地板");
    if (!b) return false;
    b.click();
    return true;
  })()`);
  await sleep(700);
  const p21c3 = await eval_(`(()=>{
    const p = document.getElementById("faceInspectorContent");
    const u = p && p.querySelector("#placeU"), v = p && p.querySelector("#placeV");
    return { clicked: true, focus: oc.focus && JSON.parse(JSON.stringify(oc.focus)),
      u: u && u.value, v: v && v.value };
  })()`);
  console.log("P21 C3 空槽直達放置:",explicitVerdict(p21c3click && p21c3.focus && p21c3.focus.t === "face" && p21c3.focus.id === 10 &&
    p21c3.u === "+y" && p21c3.v === "+x"
      ? `✓ face=${p21c3.focus.id} u=${p21c3.u} v=${p21c3.v}` : `✗ ${JSON.stringify(p21c3)}`));
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* (c) C4:構件列「移出/收進」鈕熱區 ≥28px,與旁邊 ✕ 一致
     柱需落在一個有地板足跡的空間內才會生效,否則核心回「空間不存在」。 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000");
    await api("line space 1 boundary 1");
    await api("line canvas-pos space 1 60 60");
    await api("line column 5 in 1 at 0 0 size 600 600 z 0 2500");
    await renderObjects();
    await enterFocus("space", 1);
  })()`);
  await sleep(600);
  const p21c4 = await eval_(`(()=>{
    const b = document.querySelector(".rc-act");
    return b ? Math.round(b.getBoundingClientRect().height) : null;
  })()`);
  console.log("P21 C4 rc-act熱區≥28:",explicitVerdict(p21c4 !== null && p21c4 >= 28
    ? `✓ h=${p21c4}` : `✗ ${JSON.stringify(p21c4)}`));
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* (d) D2:三視圖縮放列獨立於左下,不在 #viewToolbar 內 */
  await eval_(`document.getElementById("btnObj").click()`);
  await sleep(600);
  const p21d2 = await eval_(`(()=>{
    const canvas = document.getElementById("canvasViewport").getBoundingClientRect();
    const bar = document.querySelector(".v3-zoom");
    if (!bar) return null;
    const bb = bar.getBoundingClientRect();
    return { left: Math.round(bb.left - canvas.left),
      bottom: Math.round(canvas.bottom - bb.bottom),
      inToolbar: !!bar.closest("#viewToolbar") };
  })()`);
  console.log("P21 D2 縮放列移左下:",explicitVerdict(p21d2 && p21d2.left < 100 && p21d2.bottom < 60 && !p21d2.inToolbar
      ? `✓ ${JSON.stringify(p21d2)}` : `✗ ${JSON.stringify(p21d2)}`));
  await eval_(`document.getElementById("btnCanvasView").click()`);
  await sleep(300);

  /* ================= P22. #inspDelete 對齊 C4(不彈 confirm,toast+可 Ctrl+Z 復原) =================
   * 對抗審查指認:主畫布/RC 檢視器 #inspDelete 仍走 confirm(),與空間工作區
   * renderSpaceRc 構件列 ✕(C4:直接刪除+toast)不一致。 */
  console.log("=== P22. #inspDelete 對齊 C4 ===");
  await eval_(`(async()=>{
    await api("line reset");
    await api("line boundary 41 outline 0,0 1000,0 1000,800 0,800");
    await api("line canvas-pos boundary 41 60 60");
    await renderObjects();
    selectObject("boundary", 41);
  })()`);
  await sleep(500);
  /* (a) 裝 confirm 監聽 spy(不覆寫成通過,只記錄有沒有被呼叫)→ 點刪除鈕 → 物件即消失 */
  await eval_(`window.__confirmCalled = false;
    window.confirm = () => { window.__confirmCalled = true; return true; };`);
  const p22Toasts=await captureNewToasts(async()=>{await eval_(`document.getElementById("inspDelete").click()`);await sleep(700);});
  const p22a = await eval_(`api("objects").then(r=>({
    called: window.__confirmCalled, gone: !r.faces.some(f=>f.id===41)}))`);
  console.log("P22 不彈confirm+直接刪除:",explicitVerdict(!p22a.called && p22a.gone
    ? "✓" : `✗ ${JSON.stringify(p22a)}`));
  /* (b) toast 提示可復原 */
  const p22b = toastText(p22Toasts,'error');
  console.log("P22 toast含復原字樣:",explicitVerdict(p22b && (p22b.includes("復原") || p22b.includes("Ctrl+Z"))
    ? `✓ ${p22b}` : `✗ ${p22b}`));
  /* (c) Ctrl+Z 一次整組復原(boundary 41 沒有 placement,delete 只有一行,仍走同一 mutate 機制) */
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "z", code: "KeyZ", modifiers: 2, windowsVirtualKeyCode: 90 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "z", code: "KeyZ", modifiers: 2, windowsVirtualKeyCode: 90 });
  await sleep(800);
  const p22c = await eval_(`api("objects").then(r=>r.faces.some(f=>f.id===41))`);
  console.log("P22 Ctrl+Z復原:",explicitVerdict(p22c ? "✓" : `✗ ${p22c}`));

  const gridRefUi = await eval_(`(async()=>{
    resetSceneFocus();
    const lines = [
      "reset",
      "surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
      "grid 1 on 1 u 2000",
      "timber 2 20 20 role boundary",
      "timber 3 20 20 role boundary",
      "place 2 on 1 at-face e0 +u +n",
      "place 3 on 1 at-face e2 -u +n",
      "timber 1 27 33 role primary",
      "place 1 on 1 at-line grid 1 u 0 +v +n"
    ];
    for (const line of lines) {
      const r = await api("line " + line);
      if (!r.ok) return {error:r.error};
    }
    await renderObjects();
    await enterFocus("face", 1);
    const before = fe.timbers.find(t => t.id === 1);
    const saved = (await api("dump")).text;
    const uploaded = await fetch("/upload", {method:"POST", body:saved}).then(r=>r.json());
    if (!uploaded.ok) return {error:uploaded.error};
    resetSceneFocus();
    await renderObjects();
    await enterFocus("face", 1);
    const after = fe.timbers.find(t => t.id === 1);
    const locked = await apiRequest("line grid 1 on 1 u 1500");
    await apiRequest("line cancel-preview");
    return {before,after,hasRef:saved.includes("at-line grid 1 u 0"),
            locked:!locked.ok && locked.preview?.valid};
  })()`);
  const gridRefUiOk = gridRefUi && gridRefUi.hasRef && gridRefUi.locked &&
    gridRefUi.before && gridRefUi.before.L === 2960 &&
    JSON.stringify(gridRefUi.before) === JSON.stringify(gridRefUi.after);
  console.log("P23 grid-ref 存檔上傳後足跡與引用鎖:",explicitVerdict(gridRefUiOk ? "✓" : "✗"), JSON.stringify(gridRefUi));

  }
  if (!process.env.GEOMETRY_FLOW_REPAIR_ONLY && !process.env.GEOMETRY_REFERENCE_ONLY) { // P24–P32 使用獨立作用域，避免與既有測試的輔助函式同名。
  const check = bodyCheck({detail:'empty',detailWhenPassing:true});
  const waitIdle = async () => {
    for (let i=0;i<100;i++) {
      if (await eval_('!oc.busy && !dragging')) return;
      await sleep(50);
    }
    throw Error('UI did not finish transaction');
  };
  const clickSelector = async sel => {
    const menu=await eval_(`document.querySelector(${JSON.stringify(sel)})?.closest('#createObjectPop')?.hidden===true`);
    if(menu)await clickControl(await eval_(`(()=>{const visible=['mobileCreateObject','btnCreateObject'].filter(id=>{const e=document.getElementById(id),r=e?.getBoundingClientRect();return r&&r.width>0&&r.height>0;});if(visible.length!==1)throw Error('Expected one visible create-object opener: '+visible.join(','));return '#'+visible[0];})()`));
    const p = await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)throw Error('Missing control '+${JSON.stringify(sel)}+' '+JSON.stringify({focus:oc.focus,connection:connection.phase,error:connection.error,status:$('status').textContent}));e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,hit=document.elementFromPoint(x,y);return {x,y,hit:e.contains(hit),target:hit?.outerHTML?.slice(0,200)}})()`);
    if (!p.hit) throw Error('Control is not reachable '+sel+' '+JSON.stringify(p));
    await click(p.x,p.y); await sleep(120); await waitIdle();
    await eval_(`window.__cdpSettleUI(0)`);
  };
  const setupRemaining = async lines => {
    const out = await eval_(`(async()=>{await setView3(false);resetSceneFocus();const reset=await api('reset');if(!reset.ok)throw Error('Fixture reset failed: '+JSON.stringify(reset));const out=[];for(const s of ${JSON.stringify(lines)})out.push(await api('line '+s));const refreshed=await renderObjects();if(refreshed!==true)throw Error('Fixture did not finish rendering: '+JSON.stringify({refreshed,connection:connection.phase,error:connection.error,events:window.geometryFeedback?.events?.slice(-10)}));return out})()`);
    if (!Array.isArray(out) || out.some(r=>!r.ok)) throw Error('test setup failed '+JSON.stringify(out));
  };
  const remainingShot = async name => {
    const dest=process.env.GEOMETRY_REPAIR_SCREENSHOT_DIR;
    if (!dest) return;
    fs.mkdirSync(dest,{recursive:true});
    const r=await send('Page.captureScreenshot',{format:'png'});
    require('fs').writeFileSync(require('path').join(dest,name+'.png'),Buffer.from(r.result.data,'base64'));
  };
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
  check('P24 page identity',await eval_(`location.href === ${JSON.stringify(process.env.GEOMETRY_TEST_URL || 'http://localhost:8765/')} && document.title.length>0 && document.querySelectorAll('button').length>10 && !document.querySelector('vite-error-overlay,nextjs-portal')`));
  /* 牙齒:數量與「title 非空」不證明頁面是這個 app——比對已知鈕(index.html)的 title 文字。 */
  const p24Titles = await eval_(`({canvasView:document.getElementById('btnCanvasView')?.title,views3:document.getElementById('btnObj')?.title,fitAll:document.getElementById('btnZoom')?.title})`);
  check('P24 page identity 已知按鈕 title 文字',p24Titles.canvasView==='物件畫布' && p24Titles.views3==='三視圖' && p24Titles.fitAll==='顯示全部 (F)',p24Titles);

  if (!process.env.GEOMETRY_UI_REVIEW_ONLY) {
  // P31 starts from its own default scene, so a failed asynchronous modal wait
  // can be rerun together with every remaining phase without repeating P1–30.
  if (!process.env.GEOMETRY_CDP_FROM_P31) {
  for (const axis of ['x','y']) for (const center of [-100,-1,0,100]) for (const width of [300,301]) {
    await setupRemaining([`beam 1 along ${axis} from 0 to 1000 at ${center} width ${width} depth 100 top 1000`]);
    await eval_(`selectObject('beam',1)`);
    const before=await eval_(`(async()=>({box:(await api('objects')).beams[0].box,c:+document.querySelector('#rcfC').value,hasApply:!!document.querySelector('#rcfApply')}))()`);
    const shifted=center+40;
    await eval_(`document.querySelector('#rcfC').value=${JSON.stringify(String(shifted))}`);
    await clickSelector('#rcfApply');
    const after=await eval_(`api('objects').then(r=>r.beams[0].box)`);
    const gotC=axis==='x' ? after[1]+Math.floor((after[4]-after[1])/2) : after[0]+Math.floor((after[3]-after[0])/2);
    check(`P25 beam ${axis}/${center}/${width}`,before.hasApply && before.c===center && gotC===shifted,{before,after,gotC,shifted});
  }

  const outer=['0,0','4000,0','4000,3000','0,3000'];
  const hole=['500,500','1500,500','1500,1500','500,1500'];
  for (const ro of [false,true]) for (const rh of [false,true]) {
    await setupRemaining(['boundary 1 outline '+(ro?[...outer].reverse():outer).join(' ')+' hole '+(rh?[...hole].reverse():hole).join(' ')]);
    await eval_(`enterFocus('face',1)`);
    const text=await eval_(`document.querySelector('#faceInspectorContent').innerText`);
    check(`P26 hole area outer=${ro} hole=${rh}`,text.includes('11.00 m²'),text.match(/面積[^\n]*\n[^\n]*/)?.[0]);
  }
  await remainingShot('hole-area');

  await setupRemaining(['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000', 'spec 起點 300', 'spec 目標 900', 'spec 再移 1200', 'guide 1 1 u spec:起點']);
  await eval_(`(async()=>{await setView3(true);await render()})()`);
  const initial=(await eval_(`api('dump')`)).text;
  const points=await eval_(`(async()=>{const a=[];for(const v of [300,900,1200]){const p=await api('proj 2 2500 '+v+' 1');const t=transform(),r=cv.getBoundingClientRect(),l=layout.views[2];a.push({x:r.left+t.ox+(p.x+l.tx)*t.s,y:r.top+t.oy+(p.y+l.ty)*t.s});}return a})()`);
  await drag(points[0].x,points[0].y,points[1].x,points[1].y,8);
  await waitIdle();
  const moved=(await eval_(`api('dump')`)).text;
  check('P27 real guide drag changed model',initial!==moved && /guide 1 1 u spec:目標/.test(moved));
  const key = async redo => {
    for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key:'z',code:'KeyZ',windowsVirtualKeyCode:90,modifiers:redo?10:2});
    await sleep(200);await waitIdle();
  };
  await key(false);
  check('P27 one Ctrl+Z restores whole gesture',(await eval_(`api('dump')`)).text===initial);
  await key(true);
  check('P27 Ctrl+Shift+Z redoes whole gesture',(await eval_(`api('dump')`)).text===moved);
  await send('Input.dispatchMouseEvent',{type:'mousePressed',...points[1],button:'left',clickCount:1});
  // The bridge resolves the hit and opens the history group asynchronously.
  // Wait for that real state before testing cancellation on a slower service.
  await waitForUI(`!!(dragging && dragging.started && dragging.guide>=0)`,15000);
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',...points[2],button:'left',buttons:1});
  await sleep(100);
  const mid=(await eval_(`api('dump')`)).text;
  const engaged=await eval_(`!!(dragging && dragging.started && dragging.guide>=0)`);
  check('P27 cancel drag engaged',engaged && mid===moved,{engaged,mid});
  await eval_(`cv.dispatchEvent(new PointerEvent('pointercancel',{bubbles:true,cancelable:true,pointerId:1}))`);
  await send('Input.dispatchMouseEvent',{type:'mouseReleased',...points[2],button:'left',clickCount:1});
  await waitIdle();
  check('P27 cancelled drag restores model',(await eval_(`api('dump')`)).text===moved);
  // A quick click must not leave an open transaction or consume an undo step.
  await click(points[1].x,points[1].y);await waitIdle();await key(false);
  check('P27 quick click keeps prior undo',(await eval_(`api('dump')`)).text===initial);

  for (const scope of ['face','space']) {
    await setupRemaining(['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
                          'spec 起點 300', 'spec 目標 900', 'guide 1 1 u spec:起點', 'space 1 boundary 1']);
    await eval_(`enterFocus('${scope}',1)`);
    await clickSelector(scope==='face' ? '#projToggle' : '[data-ss-tab="proj"]');
    await sleep(200);
    const pp=await eval_(`(async()=>{
      const svg='${scope}'==='face' ? document.querySelector('#projViews [data-view="2"]').closest('svg') : document.querySelector('#spaceProjSvg');
      svg.scrollIntoView({block:'center'});
      const L=(await api('render')).layout.views[2];
      const out=[];
      for(const v of [300,900]) {
        const p=await api('proj 2 2500 '+v+' 1'),q=svg.createSVGPoint();
        q.x=p.x+('${scope}'==='space'?L.tx:0);q.y=p.y+('${scope}'==='space'?L.ty:0);
        const c=q.matrixTransform(svg.getScreenCTM());out.push({x:c.x,y:c.y});
      }
      return out;
    })()`);
    if (!Array.isArray(pp)) { check('P27 '+scope+' projection setup',false,pp); continue; }
    const start=(await eval_(`api('dump')`)).text;
    await drag(pp[0].x,pp[0].y,pp[1].x,pp[1].y,6);await waitIdle();
    const after=(await eval_(`api('dump')`)).text;
    check('P27 '+scope+' projection drag',after!==start && /guide 1 1 u spec:目標/.test(after),{points:pp,changed:after!==start,guide:after.match(/guide 1[^\n]+/g)});
    await key(false);
    check('P27 '+scope+' projection one-step undo',(await eval_(`api('dump')`)).text===start);
  }

  for (const width of [1400,1160]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    await setupRemaining(['boundary 99 outline 0,0 100,0 100,100 0,100']);
    await eval_(`closeMenus()`);
    await clickSelector('#fileMenuBtn');await clickControl('#exampleMenuBtn');
    const hit=await eval_(`(()=>{const e=document.querySelector('#btnEx'),r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))})()`);
    check('P28 file menu hit target @'+width,hit);
    await remainingShot('file-menu-'+width);
    await clickSelector('#btnEx');
    let loaded;
    for (let i=0;i<100;i++) {
      loaded=await eval_(`({path:curScene.path,name:curScene.name,status:document.querySelector('#status').textContent,ids:oc.faces.map(f=>f.id)})`);
      if (loaded.status.includes('已載入') && loaded.ids.includes(1) && !loaded.ids.includes(99)) break;
      await sleep(50);
    }
    check('P29 example loads from web directory @'+width,loaded.name==='room_a.scene' && loaded.path!=='room_a.scene' && loaded.ids.includes(1) && !loaded.ids.includes(99) && loaded.status.includes('已載入'),loaded);
  }
  }
  await eval_(`(async()=>{resetSceneFocus();await api('default');await setView3(false);await renderObjects();await enterFocus('face',1);fiShowTab('guide')})()`);
  const beforeImpact = (await eval_(`api('dump')`)).text;
  await eval_(`ParameterUI.openLegacy()`);await waitForUI(`!!$('paramSpec')`);
  await eval_(`$('paramSpec').value='主支中線';$('paramSpecValue').value='900';$('paramSpecSave').click();void 0`);
  await sleep(250);
  check('P31 form opens impact preview',await eval_(`!!document.querySelector('dialog.reference-impact[open]') && !document.querySelector('#impact-confirm').disabled && document.querySelector('dialog.reference-impact').innerText.includes('500 → 900')`));
  check('P31 preview leaves world unchanged',(await eval_(`apiRequest('dump')`)).text===beforeImpact);
  await clickSelector('#impact-confirm');
  check('P31 confirm updates dependent center',await eval_(`apiRequest('references').then(r=>r.timbers.find(t=>t.id===3).geometry.centerline===900)`));
  await eval_(`window.__previewResult=api('line spec 主支中線 1200');void 0`);
  await waitForUI(`!!document.querySelector('dialog.reference-impact[open] .impact-actions button:first-child')`,10000);
  await clickSelector('dialog.reference-impact .impact-actions button:first-child');
  check('P31 cancel keeps approved world',await eval_(`apiRequest('references').then(r=>r.timbers.find(t=>t.id===3).geometry.centerline===900)`));
  await eval_(`window.__previewResult=api('line spec 主支中線 0');void 0`);
  await waitForUI(`!!document.querySelector('dialog.reference-impact[open] #impact-confirm')`,10000);
  check('P31 invalid impact cannot confirm',await eval_(`document.querySelector('#impact-confirm').disabled && document.querySelectorAll('.impact-violation').length>0`));
  await clickSelector('dialog.reference-impact .impact-actions button:first-child');
  await remainingShot('reference-controls');
  }
  console.log('=== P32. UI review v2: reachable panels, stable editing and complete slot workflow ===');
  const pressKey = async (key,code,vk,modifiers=0) => {
    for (const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:vk,modifiers});
    await sleep(150); await waitIdle();
    await eval_(`window.__cdpSettleUI(0)`);
  };
  const fillInput = async (selector,text) => {
    await clickSelector(selector);
    await pressKey('a','KeyA',65,2);
    await send('Input.insertText',{text});
  };
  await send('Emulation.setDeviceMetricsOverride',{width:1382,height:804,deviceScaleFactor:1,mobile:false});
  await setupRemaining(['boundary 1 outline 0,0 400,0 400,300 0,300','canvas-pos boundary 1 71 81']);
  const cards = await eval_(`(async()=>{
    oc.zoom=1;oc.panX=0;oc.panY=0;ocApply();
    await api('line boundary 2 outline 0,0 200,0 200,300 0,300');await renderObjects();
    return oc.faces.map(cardBox);
  })()`);
  check('M2 new card avoids offset existing bbox',cards.length===2 && (cards[0].x+cards[0].w<=cards[1].x || cards[1].x+cards[1].w<=cards[0].x || cards[0].y+cards[0].h<=cards[1].y || cards[1].y+cards[1].h<=cards[0].y),cards);
  const quick = await eval_(`['btnNewGridSystem','btnQuickBoundary'].map(id=>{const e=$(id).querySelector('strong');return {id,w:e.clientWidth,scroll:e.scrollWidth,h:e.getBoundingClientRect().height,text:e.textContent};})`);
  check('M1 persistent library labels stay one line',quick.length===2&&quick.every(r=>r.h>0&&r.h<=24&&r.w>=r.scroll),quick);
  const pan0=await eval_(`[oc.panX,oc.panY]`);
  await clickSelector('.object-row[data-kind="boundary"][data-id="1"]');
  check('M12 visible list selection does not pan',JSON.stringify(pan0)===JSON.stringify(await eval_(`[oc.panX,oc.panY]`)));
  check('M4 common properties precede the complete placement form',await eval_(`(()=>{const pane=$('inspectorContent'),submit=pane.querySelector('#placeSubmit'),common=pane.querySelector('.inspector-block');return ['用途','面積','位置','所屬空間'].every(t=>common.textContent.includes(t))&&!!(common.compareDocumentPosition(submit)&Node.DOCUMENT_POSITION_FOLLOWING);})()`));
  let placementReachable;
  for(let attempt=0;attempt<12;attempt++){
    placementReachable=await eval_(`(()=>{const e=document.querySelector('#inspectorContent #placeSubmit'),r=e.getBoundingClientRect(),panel=e.closest('.sidebar-right').getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {width:r.width,height:r.height,top:r.top,bottom:r.bottom,panelTop:panel.top,panelBottom:panel.bottom,hit:e.contains(document.elementFromPoint(x,y)),disabled:e.disabled,wheelX:panel.right-18,wheelY:panel.top+panel.height/2,delta:r.bottom>panel.bottom-8?Math.min(300,r.bottom-panel.bottom+16):r.top<panel.top+8?Math.max(-300,r.top-panel.top-16):0};})()`);
    if(placementReachable.hit&&placementReachable.top>=placementReachable.panelTop&&placementReachable.bottom<=placementReachable.panelBottom)break;
    await send('Input.dispatchMouseEvent',{type:'mouseWheel',x:placementReachable.wheelX,y:placementReachable.wheelY,deltaX:0,deltaY:placementReachable.delta||100});await sleep(160);
  }
  check('M4 placement submit remains reachable by scrolling the property dock',placementReachable.hit&&!placementReachable.disabled&&placementReachable.width>=44&&placementReachable.height>=28&&placementReachable.top>=placementReachable.panelTop&&placementReachable.bottom<=placementReachable.panelBottom,placementReachable);
  check('M3 M5 M7 T3 contextual controls',await eval_(`document.querySelector('#fileMenuPop').contains(document.querySelector('#btnDatums')) && !document.querySelector('#btnScene') && document.querySelectorAll('#canvasDrawToolbar [data-tool]').length===2 && document.querySelector('#btnNewRect').closest('#canvasDrawToolbar') && document.querySelector('#btnNewPoly').closest('#canvasDrawToolbar') && document.querySelector('#cmdPanel').hidden`));
  await pressKey(':','Semicolon',186,8);
  check('M7 command shortcut opens focused input',await eval_(`!document.querySelector('#cmdPanel').hidden && document.activeElement.id==='cmd'`));
  await send('Input.insertText',{text:'spec 測試尺寸 123'});await pressKey('Enter','Enter',13);
  check('M7 command executes',await eval_(`api('dump').then(r=>r.text.includes('spec 測試尺寸 123'))`));
  await pressKey('Escape','Escape',27);
  check('M7 command Escape closes only command',await eval_(`document.querySelector('#cmdPanel').hidden && !oc.focus`));
  // This layout fixture measures one toast, not preceding command notices.
  await eval_(`document.querySelectorAll('#toastRegion .toast').forEach(t=>t.remove())`);
  const topToasts=await captureNewToasts(async()=>{await eval_(`toast('畫布頂部驗證','ok')`);});
  const topToast=topToasts.find(t=>t.visible&&t.classes.includes('ok')&&t.text==='畫布頂部驗證');
  check('M10 toast above canvas, away from minimap',!!topToast&&topToast.bounds.top>=56&&topToast.bounds.bottom<200,topToasts);
  await clickSelector('.ocard[data-id="1"] .card-enter');
  check('M8 explicit card entry',await eval_(`oc.focus?.t==='face' && oc.focus.id===1`));
  check('F1 F3 F4 four tabs, seven tools, five persistent groups',await eval_(`document.querySelectorAll('#faceInspectorTabs [data-fi-tab]').length===4 && document.querySelectorAll('#faceWorkspaceTools [data-face-tool]').length===7 && document.querySelectorAll('#faceLayerList .fl-group').length===5 && document.querySelectorAll('#faceLayerList .fl-empty').length>=3 && document.querySelector('#faceInspectorContent').contains(document.querySelector('#faceShapeButton'))`));
  await fillInput('#edgeLength0','500');await pressKey('Tab','Tab',9);await sleep(300);
  const lengthEdit = await eval_(`({focus:document.activeElement.id,a:document.querySelector('#edgeLength0').value,b:document.querySelector('#edgeLength2').value,status:document.querySelector('#status').textContent,loops:oc.bmap[1]})`);
  check('F2 real length edit retains next keyboard target',lengthEdit.focus==='edgeFixed0' && lengthEdit.a==='500' && lengthEdit.b==='500',lengthEdit);
  await eval_(`document.querySelector('#gridU').value='100 200';document.querySelector('#placeOX').value='250';document.querySelector('#faceInspectorContent').scrollTop=15;renderFaceInspector()`);
  check('F2 form drafts survive redraw',await eval_(`document.querySelector('#gridU').value==='100 200' && document.querySelector('#placeOX').value==='250'`));
  for (const width of [1382,1160,900,680,600]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:804,deviceScaleFactor:1,mobile:false});
    check('T4 adopted 56/96 header, reachable tools and history in right actions @'+width,await eval_(`(()=>{const h=document.querySelector('.object-workspace-topbar').getBoundingClientRect(),s=document.querySelector('.object-workspace-statusbar').getBoundingClientRect(),t=document.querySelector('.workspace-tools-row').getBoundingClientRect(),a=document.querySelector('.object-workspace-actions').getBoundingClientRect(),title=document.querySelector('#workspaceTitle').getBoundingClientRect(),vp=$('faceEditorViewport').getBoundingClientRect();return h.height===(innerWidth<=560?96:56) && s.height===32 && a.right<=innerWidth+1 && t.left>=0 && t.right<=innerWidth+1 && (innerWidth<=560?t.top>=h.top+44:t.top>=h.top&&t.bottom<=h.bottom) && document.querySelector('.object-workspace-actions').contains(document.querySelector('.workspace-history-tools')) && title.width>0 && vp.top>=h.bottom-1 && vp.height>300})()`));
  }
  await clickSelector('#workspaceToggleRight');
  await eval_(`document.querySelector('#edgeLength0').scrollIntoView({block:'center',inline:'nearest'})`);
  const drawerHit=await eval_(`(()=>{const e=document.querySelector('#edgeLength0'),r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {same:e===hit,hit:hit?.outerHTML,rect:{x:r.x,y:r.y}}})()`);
  check('T2 face drawer belongs to face workspace',drawerHit.same,drawerHit);
  await remainingShot('ui-v2-mobile-face');
  await pressKey('Escape','Escape',27);
  check('T2 drawer Escape retains workspace',await eval_(`oc.focus?.t==='face' && !document.body.classList.contains('drawer-right-open') && document.activeElement.id==='workspaceToggleRight'`));
  await clickSelector('#workspaceToggleLeft');
  check('T2 face layer drawer hit target',await eval_(`(()=>{const e=document.querySelector('#faceLayerList .fl-empty'),r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))})()`));
  await clickSelector('#workspaceBackButton');
  await clickSelector('#toggleLeft');
  check('T2 main drawer exposes source creation',await eval_(`['btnNewGridSystem','btnQuickBoundary'].every(id=>{const e=$(id),r=e.getBoundingClientRect();return r.width>0&&r.height>0&&e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})`));
  await pressKey('Escape','Escape',27);

  await setupRemaining(['space 1']);await eval_(`enterFocus('space',1)`);
  await clickSelector('#workspaceToggleRight');
  check('S1 empty space exposes all six actions',await eval_(`document.querySelectorAll('#spaceInspectorContent .slot-empty').length===6`));
  await clickSelector('[data-slot-label="地板"]');
  check('S1 empty slot starts visible guided creation',await eval_(`!oc.focus && oc.drawTool==='rect' && pendingSlot?.space===1 && !document.querySelector('#canvasModeHint').hidden`));
  await drag(330,430,510,600);await sleep(450);await waitIdle();
  // The rectangle handler refreshes objects before entering the placement workspace.
  // Waiting for the HTTP queue alone can finish between those two asynchronous steps.
  for(let i=0;i<100;i++) {
    if(await eval_(`oc.focus?.t==='face' && pendingSlot?.bid===oc.focus.id && document.querySelector('#faceInspectorContent #placeU')?.value==='+y'`)) break;
    await sleep(50);
  }
  const slotDrawn=await eval_(`({focus:oc.focus,pending:pendingSlot,u:document.querySelector('#faceInspectorContent #placeU')?.value,v:document.querySelector('#faceInspectorContent #placeV')?.value,status:document.querySelector('#status').textContent})`);
  check('S1 drawn face continues into intended placement',slotDrawn.focus?.t==='face' && slotDrawn.pending?.bid===slotDrawn.focus.id && slotDrawn.u==='+y' && slotDrawn.v==='+x',slotDrawn);
  await fillInput('#edgeLength0','800');await pressKey('Tab','Tab',9);await sleep(200);
  await fillInput('#edgeLength1','600');await pressKey('Tab','Tab',9);await sleep(200);
  await clickSelector('#faceInspectorContent #placeSubmit');await sleep(500);
  const slotPlaced=await eval_(`api('objects').then(r=>({focus:oc.focus,faces:r.faces,spaces:r.spaces,status:document.querySelector('#status').textContent}))`);
  check('S1 explicit placement returns to original space',slotPlaced.focus?.t==='space' && slotPlaced.focus.id===1 && slotPlaced.faces.length===1 && slotPlaced.faces[0].placed && slotPlaced.spaces[0].members.includes(slotPlaced.faces[0].id),slotPlaced);
  await pressKey('z','KeyZ',90,2);await sleep(300);
  check('S1 placement and membership undo together',await eval_(`api('objects').then(r=>r.faces.length===1 && !r.faces[0].placed && r.spaces[0].members.length===0)`));
  await clickSelector('#workspaceToggleRight');await clickSelector('[data-slot-label="地板"]');
  await clickSelector('#faceInspectorContent [data-place-preset="天花"]');
  const slotDirection=await eval_(`({pending:pendingSlot,focus:oc.focus,u:document.querySelector('#faceInspectorContent #placeU').value,v:document.querySelector('#faceInspectorContent #placeV').value,disabled:document.querySelector('#faceInspectorContent #placeSubmit').disabled,valid:document.querySelector('#faceInspectorContent #placeValid').textContent})`);
  check('S1 changed orientation cannot silently fill wrong slot',slotDirection.disabled,slotDirection);
  await pressKey('Escape','Escape',27);await clickSelector('#workspaceBackButton');

  await send('Emulation.setDeviceMetricsOverride',{width:1382,height:804,deviceScaleFactor:1,mobile:false});
  await setupRemaining(['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000','space 1 boundary 1']);
  await eval_(`(async()=>{await enterFocus('face',1);fiShowTab('timber')})()`);
  await fillInput('#tbA','35');await clickSelector('#tbPlace');
  const f5 = await eval_(`({tool:fe.tool,tab:fe.fiTab,timbers:fe.timbers.map(t=>({id:t.id,A:t.A,role:t.role})),status:$('status').textContent,toast:document.querySelector('.toast')?.textContent})`);
  check('F5 timber form directly places with matching section',f5.timbers.some(t=>t.A===35) && f5.tab==='timber',f5);
  await clickSelector('[data-fi-tab="prop"]');
  await clickSelector('#placeDetails summary');await clickSelector('#projToggle');
  await eval_(`renderFaceInspector()`);
  check('F9 both disclosures keep expanded state',await eval_(`document.querySelector('#placeDetails').open && document.querySelector('#projectionDetails').open`));
  await clickSelector('#workspaceBackButton');await clickSelector('#btnObj');
  check('V1 V2 toolbar does not overlap drawing and adopted empty inspector retains 240px',await eval_(`(()=>{const t=document.querySelector('#viewToolbar').getBoundingClientRect(),c=document.querySelector('#cv').getBoundingClientRect(),r=document.querySelector('.sidebar-right').getBoundingClientRect(),e=$('v3PickPanel'),b=e.getBoundingClientRect();return c.top>=t.bottom-1 && c.height>400 && r.width===240 && Math.abs(c.right-r.left)<=1 && r.right<=innerWidth && !oc.sel && !document.body.classList.contains('v3-picked') && !e.hidden && b.width>0 && b.height>0 && b.left>=r.left && b.right<=r.right && b.top>=r.top && b.bottom<=r.bottom && $('v3PickInfo').textContent.trim().length>0})()`));
  await clickSelector('#btnObj');
  check('V3 selecting three-view twice stays in three-view',await eval_(`!oc.on && document.querySelectorAll('#canvasDrawToolbar [data-tool]').length===2 && [...document.querySelectorAll('#canvasDrawToolbar [data-tool]')].every(b=>b.disabled)`));
  await remainingShot('ui-v2-three-view');
  await clickSelector('#btnCanvasView');
  check('V3 canvas switch restores active main tools',await eval_(`oc.on && document.querySelectorAll('#canvasDrawToolbar [data-tool]').length===2 && [...document.querySelectorAll('#canvasDrawToolbar [data-tool]')].every(b=>!b.disabled)`));

  /* ================= P33. 主畫布 boundary 檢視器:外環邊 · 尺寸確認清單(RC-POLYGON-PLAN §5.A.1.10,🔒 Q16) =================
   * P21/P23 編號已被既有段落占用,依 §5.A.1.14 規則往後遞補用 P33。
   * 涵蓋:清單存在且列數=外環邊數、每列顯示長度 mm 與 F/X 狀態、改長度/切 F/X 後世界對應改變、
   * 非法長度(0/負/非數字)被拒且世界不變、面內右欄清單與主畫布清單對同一 boundary 顯示一致。 */
  console.log('=== P33. 主畫布外環邊 · 尺寸確認清單(§5.A.1.10) ===');
  const readMainEdgeList = () => eval_(`(()=>{
    const pane = document.querySelector('#inspectorContent');
    const rows = [...pane.querySelectorAll('.edge-row')];
    return {
      n: rows.length,
      title: pane.textContent.includes('外環邊 · 尺寸確認'),
      lens: rows.map((_,i)=>document.querySelector('#mainEdgeLength'+i)?.value),
      fx: rows.map((_,i)=>({
        f: document.querySelector('#mainEdgeFixed'+i)?.classList.contains('on'),
        x: document.querySelector('#mainEdgeFree'+i)?.classList.contains('on')
      }))
    };
  })()`);
  const readFaceEdgeList = () => eval_(`(()=>{
    const pane = document.querySelector('#faceInspectorContent');
    const rows = [...pane.querySelectorAll('.edge-row')];
    return {
      n: rows.length,
      lens: rows.map((_,i)=>document.querySelector('#edgeLength'+i)?.value),
      fx: rows.map((_,i)=>({
        f: document.querySelector('#edgeFixed'+i)?.classList.contains('on'),
        x: document.querySelector('#edgeFree'+i)?.classList.contains('on')
      }))
    };
  })()`);
  const readBoundary1 = () => eval_(`api('boundary 1').then(b=>JSON.stringify(b.loops))`);

  await setupRemaining(['boundary 1 outline 0,0 400,0 400,300 0,300','canvas-pos boundary 1 60 60']);
  await eval_(`selectObject('boundary',1)`); await sleep(300);
  const mainList0 = await readMainEdgeList();
  check('P33-1 主畫布清單存在且列數=外環邊數', mainList0.n===4 && mainList0.title, mainList0);
  check('P33-2 每列顯示長度mm與F/X狀態(預設全F)', JSON.stringify(mainList0.lens)===JSON.stringify(['400','300','400','300']) &&
    mainList0.fx.every(v=>v.f && !v.x), mainList0);

  /* 改長度 → outline 座標對應改變(邊0 400→500,寬跟著變,高不變) */
  await fillInput('#mainEdgeLength0','500'); await pressKey('Tab','Tab',9); await sleep(300);
  const lenChanged = await eval_(`api('boundary 1').then(b=>{
    const vs=b.loops[0].verts;
    return {w: vs[1][0]-vs[0][0], h: vs[2][1]-vs[1][1]};
  })`);
  check('P33-3 改長度後 outline 座標對應改變', lenChanged.w===500 && lenChanged.h===300, lenChanged);

  /* 切 F/X → fixity 對應改變,再切回驗證雙向 */
  await clickSelector('#mainEdgeFree1');
  const fixChanged = await eval_(`api('boundary 1').then(b=>b.loops[0].fixity[1])`);
  check('P33-4 切X後 fixity 對應改變', fixChanged===0, fixChanged);
  await clickSelector('#mainEdgeFixed1');
  const fixRestored = await eval_(`api('boundary 1').then(b=>b.loops[0].fixity[1])`);
  check('P33-5 切回F fixity 還原', fixRestored===1, fixRestored);

  /* 非法長度:0、負、非數字 → 拒絕且世界不變 */
  const beforeIllegal = await readBoundary1();
  await fillInput('#mainEdgeLength0','0'); await pressKey('Tab','Tab',9); await sleep(300);
  const afterZero = await readBoundary1();
  check('P33-6 長度0被拒且世界不變', afterZero===beforeIllegal, {before:beforeIllegal,after:afterZero});
  await fillInput('#mainEdgeLength0','-50'); await pressKey('Tab','Tab',9); await sleep(300);
  const afterNeg = await readBoundary1();
  check('P33-7 負長度被拒且世界不變', afterNeg===beforeIllegal, {before:beforeIllegal,after:afterNeg});
  const nanResult = await eval_(`commitEdgeLength(1, oc.bmap[1], 0, NaN)`);
  const afterNaN = await readBoundary1();
  check('P33-8 非數字長度被拒且世界不變', nanResult===false && afterNaN===beforeIllegal,
    {nanResult,before:beforeIllegal,after:afterNaN});

  /* 面內工作區右欄清單與主畫布清單對同一 boundary 顯示一致 */
  await eval_(`enterFocus('face',1)`); await sleep(300);
  const feList = await readFaceEdgeList();
  await eval_(`leaveFocus()`); await sleep(200);
  await eval_(`selectObject('boundary',1)`); await sleep(300);
  const mainList2 = await readMainEdgeList();
  check('P33-9 面內與主畫布清單對同一boundary顯示一致',
    feList.n===mainList2.n && JSON.stringify(feList.lens)===JSON.stringify(mainList2.lens) &&
    JSON.stringify(feList.fx)===JSON.stringify(mainList2.fx), {feList,mainList2});

  /* ================= P34. P 鍵/「＋面·多邊形」:建面卡→面內畫外環(GEO-186 b) =================
   * 2026-09-24 GEO-186(b) 拍板:主畫布不再用 mm 畫多邊形——同一張畫布混用
   * 「mm 繪圖」與「固定 200×156 卡片排版」兩套座標是 GEO-186 的根因
   * (畫 4000×3000 的房間要縮到 2–5%,閉合後卡片被放到多邊形左上角、
   * 縮成一個點——GEO-187「找不到卡片」)。新流程:
   *   P/「＋面·多邊形」= 建預設外環的面卡 → 自動進入面內工作區並啟用「重畫外環」
   *   → 面內以實際 mm 逐點畫 → Esc 回畫布。
   * 畫布端逐點閉合機制(吸附/補角/Esc 階梯/鍵入長度/草稿層)已隨畫布繪圖移除;
   * PolyDraft 狀態機行為由 polydraft_test.js 單元測試 + 面內 §P35/P36 繼續覆蓋。 */
  console.log('=== P34. P=建面卡→面內畫外環(GEO-186) ===');
  /* GEO-197 草稿列在畫布外占位；700px 的測試落點必須完整落在可繪區內。 */
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1100,deviceScaleFactor:1,mobile:false});
  const ocOrigin = async () => eval_(`(()=>{const r=document.getElementById('ocv').getBoundingClientRect();
    return {x:r.left,y:r.top};})()`);
  /* setupRemaining([]) 重置成完全空世界後,#emptyState(「建立第一個領域物件」提示卡)
     會蓋在畫布正中央(.empty-illustration 有 pointer-events:auto,120×80px 置中),
     建出新物件、drawObjects() 重繪之前都不會自動收起——點擊若剛好落在置中那塊區域
     會被這張卡片吃掉,不會傳到 #ocv。這裡直接把它隱藏,建出新面後 drawObjects()
     會依當下物件數自行重算 hidden,不需要手動復原。 */
  const emptyWorld = async () => {
    await setupRemaining([]);
    await eval_(`document.getElementById('emptyState').hidden = true`);
  };

  /* 按 P → 面數+1、預設外環佔位、自動進入面內工作區且重畫外環就緒、新面被選取 */
  await emptyWorld();
  await eval_(`oc.zoom=1;oc.panX=0;oc.panY=0;ocApply()`);
  const p34f0 = await eval_(`api('objects').then(r=>r.faces.length)`);
  await pressKey('p','KeyP',80);
  await sleep(900);
  const t1 = await eval_(`(async()=>{
    const r = await api('objects');
    const f = r.faces[r.faces.length-1];
    const b = await api('boundary '+f.id);
    return {faces:r.faces.length, id:f.id, verts:b.loops[0].verts,
      focus:oc.focus, tool:fe.tool, sel:oc.sel,
      st:document.getElementById('status').textContent};})()`);
  check('P34-1 按 P 建面卡:面數+1、自動進入面內工作區、重畫外環就緒、新面被選取',
    t1.faces===p34f0+1 && t1.focus && t1.focus.t==='face' && t1.focus.id===t1.id &&
    t1.tool==='redraw' && t1.sel && t1.sel.id===t1.id, t1);
  check('P34-1b 狀態列提示「逐點畫出外環」與 Esc 返回', /逐點畫出外環/.test(t1.st) && /Esc/.test(t1.st), t1.st);
  check('P34-2 預設外環是 4000×3000 矩形佔位(進面內後被 redraw 整份取代)',
    JSON.stringify(t1.verts)==='[[0,0],[4000,0],[4000,3000],[0,3000]]', t1.verts);

  /* 面內以實際 mm 畫 L 形外環:固定 fe.zoom=1/pan=0 讓螢幕像素=面內 mm;
     落點全取 50 的倍數,與面內格距(feGridStep()=25、feSnap()=50)都對齊,
     吸附開著也不偏移。末點(100,700)與起點(100,100)同軸,不需補角,6 點閉合即 L。 */
  const f34 = t1.id;
  await eval_(`fe.zoom=1;fe.panX=0;fe.panY=0;feApply();
    document.getElementById('faceSnapToggle').checked = true`);
  const fo34 = await eval_(`(()=>{const r=document.getElementById('faceEditorSvg').getBoundingClientRect();
    return {x:r.left,y:r.top};})()`);
  check('P34 測試所有落點都在可繪區內', await eval_(`(()=>{const r=$('faceEditorSvg').getBoundingClientRect();return r.width>712 && r.height>760})()`));
  for (const [x, y] of [[100,100],[700,100],[700,400],[400,400],[400,700],[100,700]]) {
    await click(fo34.x+x, fo34.y+y); await sleep(90);
  }
  await click(fo34.x+100, fo34.y+100); await sleep(900);   /* 點回起點閉合 */
  const drawn34 = await eval_(`api('boundary '+${f34}).then(b=>JSON.stringify(b.loops[0].verts))`);
  check('P34-3 面內 redraw 以實際 mm 畫外環,點回起點閉合後世界 outline 更新',
    drawn34==='[[100,100],[700,100],[700,400],[400,400],[400,700],[100,700]]', drawn34);

  /* Esc 回畫布:卡片可見且在視野內(落點是建立當下的視野中心)、維持選取 */
  await pressKey('Escape','Escape',27); await sleep(500);
  const back34 = await eval_(`(()=>{const c=document.querySelector('.ocard[data-id="${f34}"]');
    const v=document.getElementById('ocv').getBoundingClientRect();
    const r=c&&c.getBoundingClientRect();
    return {focus:oc.focus, sel:oc.sel, card:!!r,
      inView:!!r && r.left>=v.left && r.right<=v.right && r.top>=v.top && r.bottom<=v.bottom};})()`);
  check('P34-4 Esc 回畫布:卡片可見、在視野內、維持選取',
    !back34.focus && back34.card && back34.inView && back34.sel && back34.sel.id===f34, back34);

  /* pendingSlot:空間槽位「＋放置」會備妥矩形工具;此時按 P 改走建面卡路徑,
     新面仍自動帶入該槽位、進面內直接開「放置」頁(S1 矩形路徑的對應分支) */
  await setupRemaining(['space 1']);
  await eval_(`enterFocus('space',1)`); await sleep(400);
  await eval_(`document.querySelector('#spaceInspectorContent .slot-empty').click()`); await sleep(400);
  const armed34 = await eval_(`({focus:oc.focus, drawTool:oc.drawTool,
    slot:pendingSlot && {space:pendingSlot.space, preset:pendingSlot.presetName}})`);
  await pressKey('p','KeyP',80); await sleep(900);
  const slotFlow = await eval_(`({focus:oc.focus, bid:pendingSlot && pendingSlot.bid,
    tab:(document.querySelector('#faceInspectorTabs [data-fi-tab].active')||{}).dataset?.fiTab})`);
  check('P34-5 槽位「＋放置」後按 P:新面帶入 pendingSlot、面內工作區直接開放置頁',
    !armed34.focus && armed34.drawTool==='rect' && armed34.slot && armed34.slot.space===1 &&
    slotFlow.focus && slotFlow.focus.t==='face' && slotFlow.bid===slotFlow.focus.id &&
    slotFlow.tab==='prop', {armed34, slotFlow});
  await eval_(`leaveFocus()`); await sleep(400);


  /* ================= P35. 面內「重畫外環」逐點閉合改接共用 PolyDraft(diff#12 面內段) =================
   * RC-POLYGON-PLAN.md §5.A.1.12/.16、POLYDRAFT-API.md §6。續 §P34 之後編號。
   * 初始 camera 為 zoom=1/pan=0；工具提示改變可繪區後，依實際 SVG camera 映射 mm 落點。
   * polydraft.js 本體不受本節影響(該模組由另一 agent 同時維護 tryClose 收尾驗證，本節只讀)。 */
  console.log('=== P35. 面內重畫外環逐點閉合(polydraft,diff#12 面內段) ===');
  const waitForFaceViewport = async () => {
    await eval_(`new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))`);
    await waitForUI(`(()=>{const r=$('faceEditorViewport').getBoundingClientRect(),v=fe.viewportSize,i=feViewportInsets(r);
      return !!v&&Math.abs(v.width-r.width)<.5&&Math.abs(v.height-r.height)<.5&&v.top===i.top&&v.bottom===i.bottom;})()`);
  };
  const feOrigin = async () => {
    await waitForFaceViewport();
    const origin=await eval_(`(()=>{const r=$('faceEditorSvg').getBoundingClientRect(),m=$('faceEditorRoot').getScreenCTM();
      return {x:r.left,y:r.top,matrix:{a:m.a,b:m.b,c:m.c,d:m.d,e:m.e,f:m.f}};})()`);
    // Existing callers add their own camera offsets to x/y; retain that contract.
    const m=origin.matrix;
    return {...origin,point:(u,v)=>({x:m.a*u+m.c*v+m.e,y:m.b*u+m.d*v+m.f})};
  };
  const clickFacePoint = async (origin,u,v) => {const p=origin.point(u,v);await click(p.x,p.y);};
  /* 每次都用一個夠大的外環(4000×3000)進場：重畫是整份重建 loops[0]，舊外環正被取代
     不算「既有」(POLYDRAFT-API.md §6)，這裡只是給新草稿足夠的畫布空間，座標互不干擾。 */
  const enterFaceRedraw = async () => {
    await setupRemaining(['boundary 1 outline 0,0 4000,0 4000,3000 0,3000']);
    await eval_(`(async()=>{ await enterFocus('face', 1);
      fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply(); })()`);
    await sleep(250);
  };

  /* diff#12:進入面內按 e 後草稿層存在 */
  await enterFaceRedraw();
  await pressKey('e', 'KeyE', 69);
  const t35_1 = await eval_(`({tool: fe.tool, layer: !!document.getElementById('feDraftLayer')})`);
  check('P35-1 面內按 e 後 fe.tool=redraw 且 #feDraftLayer 草稿層存在',
    t35_1.tool === 'redraw' && t35_1.layer, t35_1);
  check('P35 切換外環工具保留使用者縮放', await eval_(`fe.zoom===1 && fe.panX===0 && fe.panY===0`));

  /* diff#3/§5.A.1.3:面內 gridMm 不是固定 250，是 feGridStep()(B4 依 zoom 挑距)算出來的值，
     測試自己讀取這個值再驗證吸附後座標是它的整數倍——snapOn 預設開(#faceSnapToggle checked)。 */
  const fo2 = await feOrigin();
  const gridStep2 = await eval_(`feGridStep()`);
  // Keep the non-grid-aligned sample inside the viewport after redraw's notice appears.
  const snapSample=fo2.point(13,108);
  check('P35-2 吸附採樣點在可繪區內且無遮擋',await eval_(`(()=>{const p=${JSON.stringify(snapSample)},v=$('faceEditorViewport'),r=v.getBoundingClientRect(),hit=document.elementFromPoint(p.x,p.y);
    return p.x>r.left&&p.x<r.right&&p.y>r.top&&p.y<r.bottom&&!!hit&&$('faceEditorSvg').contains(hit);})()`),snapSample);
  await clickFacePoint(fo2, 13, 108);
  await sleep(150);
  const fsnap2 = await eval_(`fe.draft.pts[0]`);
  check(`P35-2 點擊吸附到 B4 格距(zoom=1→${gridStep2}mm)`,
    fsnap2[0] % gridStep2 === 0 && fsnap2[1] % gridStep2 === 0, { fsnap2, gridStep2 });

  /* diff#6:靠近既有「非相鄰」頂點 ±8px 出現對齊參考線並吸附該軸(同 P34-7 手法，
     驗證面內也有這道吸附——關 snapOn 避免格線吸附干擾像素級判斷，用完即還原)。 */
  await enterFaceRedraw();
  await eval_(`feSetTool('redraw'); document.getElementById('faceSnapToggle').checked = false`);
  const fo3 = await feOrigin();
  await clickFacePoint(fo3, 100, 100); await sleep(90);
  await clickFacePoint(fo3, 500, 100); await sleep(90);
  await clickFacePoint(fo3, 500, 400); await sleep(90);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', ...fo3.point(103, 600) });
  await sleep(150);
  const guide3 = await eval_(`({guides: fe.draftPreview.guides, cur: fe.draftPreview.cur,
    lines: document.querySelectorAll('#feDraftLayer .draft-align-guide').length})`);
  check('P35-3 靠近既有頂點±8px 吸附該軸並畫參考線(對齊起點 x=100)',
    guide3.lines > 0 && guide3.cur[0] === 100 &&
    guide3.guides.some(g => g.axis === 'x' && g.value === 100), guide3);

  /* diff#7/#9:末點與起點不同軸 → 自動補一個直角轉折，dump 頂點數 = 點擊數 3 + 1(同 P34-9) */
  await enterFaceRedraw();
  await eval_(`feSetTool('redraw')`);
  const fo4 = await feOrigin();
  await clickFacePoint(fo4, 100, 100); await sleep(90);
  await clickFacePoint(fo4, 400, 100); await sleep(90);
  await clickFacePoint(fo4, 400, 400); await sleep(90);
  await pressKey('Enter', 'Enter', 13); await sleep(700);
  const closed4 = await eval_(`api('boundary 1').then(b => b.loops[0].verts)`);
  /* 不只驗頂點數(舊碼點 3 下因未達 4 點而拒絕、boundary 維持原狀，巧合也是 4 頂點但內容是
     沒被取代的原始 4000×3000 外環)——這裡逐點驗證真的是新畫的 L 轉角形狀，
     [400,400] 之後補上 [100,400] 這個直角轉折點，不是舊外環殘留。 */
  check('P35-4 末點不同軸自動補直角(dump 頂點數=點擊數 3 + 1，且內容確實是新外環)',
    JSON.stringify(closed4) === JSON.stringify([[100,100],[400,100],[400,400],[100,400]]), closed4);

  /* diff#8:與自身既有邊交叉時橡皮筋轉紅、點擊無效、世界不變。
     existingEdges 含自身邊的證明:feDraftOpts() 恆傳 existingEdges:[]（重畫外環沒有
     「既有」邊可比，見上方 enterFaceRedraw 的說明），CROSS 仍被抓到，證明是
     PolyDraft.place 內部對 state.pts(草稿自身已定邊)自動比對的結果，不靠 existingEdges
     陣列本身——與主畫布 P34-10a/b(同樣傳 existingEdges:[])是同一套機制，共用的直接證據。 */
  await enterFaceRedraw();
  await eval_(`feSetTool('redraw')`);
  const fo5 = await feOrigin();
  await clickFacePoint(fo5, 100, 100); await sleep(90);
  await clickFacePoint(fo5, 100, 500); await sleep(90);
  await clickFacePoint(fo5, 500, 500); await sleep(90);
  await clickFacePoint(fo5, 500, 200); await sleep(90);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', ...fo5.point(50, 200) });
  await sleep(150);
  const cross5 = await eval_(`({error: fe.draftPreview.error,
    rubberError: !!document.querySelector('#feDraftLayer .draft-rubber.error')})`);
  check('P35-5a 面內與自身既有邊交叉時橡皮筋轉紅(CROSS)',
    cross5.error && cross5.error.code === 'CROSS' && cross5.rubberError, cross5);
  const beforeCrossPts = await eval_(`fe.draft.pts.length`);
  await clickFacePoint(fo5, 50, 200); await sleep(150);
  const afterCrossPts = await eval_(`fe.draft.pts.length`);
  const worldUnchanged5 = await eval_(`api('boundary 1').then(b => b.loops[0].verts.length)`);
  check('P35-5b 交叉時點擊無效(頂點數不變)、世界不變',
    afterCrossPts === beforeCrossPts && worldUnchanged5 === 4,
    { beforeCrossPts, afterCrossPts, worldUnchanged5 });

  /* diff#7:Enter 閉合與點回起點閉合，同一組點擊序列結果一致(同 P34-8 手法的子集，
     面內沒有雙擊閉合，兩種既夠) */
  const drawFaceRect = async () => {
    await enterFaceRedraw();
    await eval_(`feSetTool('redraw')`);
    const o = await feOrigin();
    await clickFacePoint(o, 100, 100); await sleep(90);
    await clickFacePoint(o, 500, 100); await sleep(90);
    await clickFacePoint(o, 500, 400); await sleep(90);
    await clickFacePoint(o, 100, 400); await sleep(90);
    return o;
  };
  let ofa = await drawFaceRect();
  await clickFacePoint(ofa, 100, 100); await sleep(700);
  const closeFA = await eval_(`api('boundary 1').then(b => JSON.stringify(b.loops[0].verts))`);
  ofa = await drawFaceRect();
  await pressKey('Enter', 'Enter', 13); await sleep(700);
  const closeFB = await eval_(`api('boundary 1').then(b => JSON.stringify(b.loops[0].verts))`);
  check('P35-6 Enter 閉合與點回起點閉合結果相同', closeFA === closeFB, { closeFA, closeFB });

  /* UIUX-FIX-PLAN「Esc 三段式決定 🔒」既有七階梯不變——驗其中三級的順序：
     清鍵入長度(第4級) → 清草稿並提示「再按」(第6級) → 離開工作區(第7級)。 */
  await enterFaceRedraw();
  await eval_(`feSetTool('redraw')`);
  const fo7 = await feOrigin();
  await clickFacePoint(fo7, 100, 100); await sleep(90);
  await clickFacePoint(fo7, 300, 100); await sleep(90);
  await pressKey('4', 'Digit4', 52); await pressKey('2', 'Digit2', 50);
  const typed7 = await eval_(`fe.lenBuf`);
  check('P35-7a 面內鍵入長度中 fe.lenBuf 非空', typed7 === '42', typed7);
  await pressKey('Escape', 'Escape', 27); await sleep(150);
  const esc7a = await eval_(`({lenBuf: fe.lenBuf, drag: !!fe.drag, focus: !!oc.focus})`);
  check('P35-7b 第一次 Esc(第4級)只清鍵入長度，草稿與工作區不變',
    esc7a.lenBuf === '' && esc7a.drag && esc7a.focus, esc7a);
  const esc7Toasts=await captureNewToasts(async()=>{await pressKey('Escape', 'Escape', 27);await sleep(150);});
  const esc7b = await eval_(`({drag: !!fe.drag, focus: !!oc.focus})`);esc7b.toast=toastText(esc7Toasts,'ok');
  check('P35-7c 第二次 Esc(第6級)清草稿並提示「再按」，仍在工作區',
    !esc7b.drag && esc7b.focus && esc7b.toast.includes('再按'), esc7b);
  await pressKey('Escape', 'Escape', 27); await sleep(300);
  const esc7c = await eval_(`!!oc.focus`);
  check('P35-7d 第三次 Esc(第7級)離開工作區', esc7c === false, esc7c);

  /* diff#10/§5.A.1.10(既有共用邏輯):閉合後面內右欄「外環邊 · 尺寸確認」清單列數=新邊數 */
  ofa = await drawFaceRect();
  await clickFacePoint(ofa, 100, 100); await sleep(700);
  const feList8 = await readFaceEdgeList();
  check('P35-8 閉合後面內右欄「外環邊 · 尺寸確認」清單列數=新邊數', feList8.n === 4, feList8);

  /* 原 P35-9(主畫布 P 與面內 e 對同序列產生相同 outline、覆蓋兩側格距刻意分歧)已移除:
     GEO-186(b) 後主畫布不再有 mm 繪圖工具,「兩個呼叫點共用 PolyDraft」只剩面內一側,
     對照失去意義;PolyDraft 狀態機行為由 polydraft_test.js 單元測試覆蓋。 */

  /* ================= P36. 對抗審查「多邊形逐點閉合」UI 接線 finding =================
   * 原 4 個 finding 中 finding-1(oc.polyDraft 重置)/finding-2(undo 後草稿層閃空)/
   * finding-3 主畫布段都是畫布 poly 機器的接線修正——GEO-186(b) 機器移除後一併移除。
   * 保留 finding-3 的面內段:鍵入長度錯誤的持久回饋(狀態列+紅橡皮筋)。 */
  console.log('=== P36. 對抗審查 finding 修正(面內段) ===');

  /* finding-3 面內段:「C 形」座標(P35-5a 同款)鍵入長度 450 觸發 CROSS——
     面內沒有 .hint-context 容器(只有主畫布 #canvasModeHint 有這個結構)，
     改驗狀態列 + 紅橡皮筋兩項持久回饋。 */
  await enterFaceRedraw();
  await eval_(`feSetTool('redraw'); document.getElementById('faceSnapToggle').checked = false`);
  const fo36 = await feOrigin();
  await clickFacePoint(fo36, 100, 100); await sleep(90);
  await clickFacePoint(fo36, 100, 500); await sleep(90);
  await clickFacePoint(fo36, 500, 500); await sleep(90);
  await clickFacePoint(fo36, 500, 200); await sleep(90);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', ...fo36.point(50, 200) });
  await sleep(150);
  await pressKey('4','Digit4',52); await pressKey('5','Digit5',53); await pressKey('0','Digit0',48);
  await pressKey('Enter','Enter',13); await sleep(150);
  const t3b = await eval_(`({
    statusText: document.getElementById('status').textContent.replace('✗','[X]'),
    rubberError: !!document.querySelector('#feDraftLayer .draft-rubber.error'),
    typed: fe.draft.typed, ptsLen: fe.draft.pts.length
  })`);
  check('P36-3b 面內鍵入會交叉的長度後 Enter,狀態列顯示警示文字、橡皮筋轉紅(面內沒有 .hint-context,狀態列+紅橡皮筋是對應的持久回饋;不再只有一次性 toast)',
    /交叉/.test(t3b.statusText) && t3b.rubberError && t3b.typed==='450' && t3b.ptsLen===4, t3b);

  await pressKey('Escape','Escape',27); await sleep(150);
  const t3b2 = await eval_(`({
    rubberError: !!document.querySelector('#feDraftLayer .draft-rubber.error'),
    typed: fe.lenBuf
  })`);
  check('P36-3b2 面內清數字(Esc 第一階)後鍵入長度錯誤態消失(橡皮筋不再紅)',
    t3b2.typed==='' && !t3b2.rubberError, t3b2);
  await eval_(`document.getElementById('faceSnapToggle').checked = true; leaveFocus()`);  /* 還原頁面預設 */

  console.log('=== P37. 工作區狀態與手機操作回歸 ===');
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
  await setupRemaining(['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000']);
  await eval_(`enterFocus('face',1)`);
  await clickSelector('#placeDetails > summary');
  await fillInput('#faceInspectorContent #placeOZ','3000');
  await clickSelector('#faceInspectorContent #placeSubmit');
  // Placement refresh is asynchronous; wait for its visible completion instead of a 120 ms machine-speed assumption.
  const waitPlaceHeader = async value => {
    for(let i=0;i<100;i++) { if(await eval_(`$('workspacePlaceTag').textContent.includes(${JSON.stringify(value)})`))return; await sleep(50); }
  };
  await waitPlaceHeader('3000');
  check('P37 placement update refreshes header',await eval_(`document.querySelector('#workspacePlaceTag').textContent.includes('3000')`));
  await clickSelector('#faceUndoButton');
  await waitPlaceHeader('2500');
  check('P37 placement undo refreshes form and header',await eval_(`document.querySelector('#faceInspectorContent #placeOZ').value==='2500' && document.querySelector('#workspacePlaceTag').textContent.includes('2500')`));
  await clickSelector('#faceRedoButton');
  await waitPlaceHeader('3000');
  check('P37 placement redo refreshes form and header',await eval_(`document.querySelector('#faceInspectorContent #placeOZ').value==='3000' && document.querySelector('#workspacePlaceTag').textContent.includes('3000')`));
  if (!await eval_(`document.querySelector('#placeDetails').open`)) await clickSelector('#placeDetails > summary');
  await fillInput('#faceInspectorContent #placeOZ','3100');
  await eval_(`feAfterChange()`);
  check('P37 inspector rebuild preserves unsubmitted placement draft and focus',await eval_(`document.querySelector('#faceInspectorContent #placeOZ').value==='3100' && document.activeElement.id==='placeOZ' && feSurf(1).origin[2]===3000`));

  /* Pause the second boundary response, leaving the existing face SVG interactive.
     This exercises the actual refresh and pointer handlers, not a copied cache model. */
  await setupRemaining([
    'boundary 1 outline 0,0 4000,0 4000,3000 0,3000',
    'boundary 2 outline 0,0 4000,0 4000,3000 0,3000'
  ]);
  await eval_(`enterFocus('face',2)`);
  const p37Exceptions=excN;
  await eval_(`(()=>{
    const original=api, oldCache=oc.bmap;
    const gate={original,oldCache,waiting:false,blocked:false};
    window.__p37BoundaryGate=gate;
    api=async function(cmd){
      if(cmd==='boundary 2' && !gate.blocked){
        gate.blocked=true;gate.waiting=true;
        await new Promise(resolve=>{gate.release=resolve});
      }
      return original(cmd);
    };
    gate.refresh=renderObjects();
  })()`);
  try {
    let pendingBoundary=false;
    for(let i=0;i<100;i++) {
      pendingBoundary=await eval_(`window.__p37BoundaryGate.waiting`);
      if(pendingBoundary) break;
      await sleep(25);
    }
    const cache=await eval_(`({same:oc.bmap===window.__p37BoundaryGate.oldCache,ids:Object.keys(oc.bmap),focus:oc.focus?.id})`);
    check('P37 pending multi-face refresh retains complete published cache',pendingBoundary && cache.same && cache.ids.includes('1') && cache.ids.includes('2') && cache.focus===2,cache);
    await clickSelector('#faceEditorRoot [data-face-hit="e:0:0"]');
    check('P37 existing face edge remains interactive while boundary refresh waits',excN===p37Exceptions && await eval_(`oc.focus?.id===2 && !!oc.bmap[2] && !document.querySelector('#objectWorkspace').hidden`));
  } finally {
    await eval_(`(async()=>{
      const gate=window.__p37BoundaryGate;
      api=gate.original;
      if(gate.release)gate.release();
      await gate.refresh;
      delete window.__p37BoundaryGate;
    })()`);
  }

  for (const kind of ['face','space']) {
    await setupRemaining(kind==='face' ? ['boundary 1 outline 0,0 4000,0 4000,3000 0,3000'] : ['space 1']);
    await eval_(`enterFocus('${kind}',1)`);
    await clickSelector('#faceUndoButton');
    // Undo refreshes the scene asynchronously without setting oc.busy.
    // Wait for its observable completion, not clickSelector's 120 ms delay.
    await waitForUI(`!oc.focus && !oc.edit && $('objectWorkspace').hidden && $('faceEditorRoot').childElementCount===0`);
    const gone=await eval_(`({focus:oc.focus,edit:oc.edit,hidden:document.querySelector('#objectWorkspace').hidden,svg:document.querySelector('#faceEditorRoot').childElementCount})`);
    check('P37 undo removes focused '+kind+' and clears workspace',!gone.focus && !gone.edit && gone.hidden && gone.svg===0,gone);
  }

  for (const width of [390,320]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:804,deviceScaleFactor:1,mobile:false});
    await eval_(`closePanels();closeMenus()`);await sleep(200);
    const buttons=await eval_(`[...document.querySelectorAll('.topbar button')].filter(e=>e.getClientRects().length && getComputedStyle(e).visibility!=='hidden').map(e=>{const r=e.getBoundingClientRect();return {id:e.id,inside:r.left>=0 && r.right<=innerWidth && r.top>=0 && r.bottom<=innerHeight,hit:e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}})`);
    check('P37 all visible topbar buttons fit and are reachable @'+width,buttons.length>0 && buttons.every(b=>b.inside && b.hit),buttons);
    if (width===390) await eval_(`showCommand(true)`);
    await clickSelector('#toggleLeft');
    await clickSelector('#searchInput');
    await pressKey('Escape','Escape',27);
    check('P37 search Escape closes drawer and restores toggle @'+width,await eval_(`!document.body.classList.contains('drawer-left-open') && document.activeElement.id==='toggleLeft'`));
    if (width===390) {
      check('P37 search Escape leaves background command panel open',await eval_(`!document.querySelector('#cmdPanel').hidden`));
      await eval_(`showCommand(false)`);
    }
  }
  await send('Emulation.setDeviceMetricsOverride',{width:600,height:804,deviceScaleFactor:1,mobile:false});
  for (const [button,dialog,field,cancel] of [
    ['#btnBox6','#box6Dialog','#box6W','#box6Cancel'],
    ['#btnNewColumn','#rcDialog','#rcW','#rcCancel']
  ]) {
    await clickSelector('#toggleLeft');
    await clickSelector(button);
    await clickSelector(field);
    check('P37 drawer closes before opening '+dialog,await eval_(`!document.body.classList.contains('drawer-left-open') && !document.querySelector('${dialog}').hidden && document.activeElement.id==='${field.slice(1)}'`));
    await clickSelector(cancel);
  }

  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
  /* geometry-core/transactions.inc::reference_default_world defines spec 主支中線 500,
     guide 1 and dependent timber 3, so editing it must open an impact preview. */
  await eval_(`(async()=>{resetSceneFocus();await api('default');await renderObjects();await enterFocus('face',1)})()`);
  await eval_(`fiShowTab('guide')`);
  const p37Before=(await eval_(`apiRequest('dump')`)).text;
  await clickSelector('#refParameterOpen');await waitForUI(`!!$('paramSpec')`);
  await eval_(`$('paramSpec').value='主支中線';$('paramSpec').dispatchEvent(new Event('change'));void 0`);
  await fillInput('#paramSpecValue','900');
  await clickSelector('#paramSpecSave');
  await waitForUI(`!!document.querySelector('dialog.reference-impact[open]')`,10000);
  check('P37 reference form opens native impact dialog',await eval_(`!!document.querySelector('dialog.reference-impact[open]')`));
  await pressKey('Escape','Escape',27);
  check('P37 impact Escape cancels only dialog and retains face',await eval_(`!document.querySelector('dialog.reference-impact[open]') && oc.focus?.t==='face' && oc.focus.id===1 && !document.querySelector('#objectWorkspace').hidden`));
  check('P37 impact Escape leaves model unchanged',(await eval_(`apiRequest('dump')`)).text===p37Before);
  check('P30 no uncaught browser exceptions',excN===0,excN);

  console.log('=== P38. 回報收件匣(GEO-183):F8 面板、Esc 不外洩、指出位置不觸發 app、送出寫檔、程式錯誤自動擷取 ===');
  const fbDir = process.env.GEOMETRY_FEEDBACK_DIR;
  const fbList = () => fbDir && require('fs').existsSync(fbDir)
    ? require('fs').readdirSync(fbDir).filter(n => n.startsWith('F-')).sort() : [];
  const fbMeta = id => JSON.parse(require('fs').readFileSync(require('path').join(fbDir, id, 'meta.json'), 'utf8'));
  await send('Emulation.setDeviceMetricsOverride',{width:1382,height:900,deviceScaleFactor:1,mobile:false});
  await eval_(`(async()=>{resetSceneFocus();await api('default');await renderObjects();await enterFocus('face',1)})()`);
  await eval_(`api('line place 999 on 1 at-line guide 1')`);
  check('P38 黑盒子記下被拒的指令與錯誤', await eval_(`geometryFeedback.events.some(e=>e.k==='api'&&e.cmd.includes('place 999')&&!e.ok&&!!e.error)`));
  check('P38 回報鈕可見且不在頂列內', await eval_(`(()=>{const b=document.querySelector('#fbButton');const r=b.getBoundingClientRect();return r.width>0&&getComputedStyle(b).visibility==='visible'&&r.top>parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--topbar-h'))&&!document.querySelector('#app').contains(b)})()`));
  await pressKey('F8','F8',119);
  check('P38 F8 開面板且焦點在說明欄', await eval_(`!document.querySelector('#fbPanel').hidden && document.activeElement.id==='fbNote'`));
  await pressKey('Escape','Escape',27);
  check('P38 面板內 Esc 只關面板,不退出面工作區', await eval_(`document.querySelector('#fbPanel').hidden && oc.focus?.t==='face' && oc.focus.id===1`));
  await clickSelector('#fbButton');
  check('P38 回報鈕開面板', await eval_(`!document.querySelector('#fbPanel').hidden`));
  await send('Input.insertText',{text:'P38 測試:這裡怪怪的'});
  await clickSelector('[data-fb-kind="unexpected"]');
  const tabBefore = await eval_(`fe.fiTab`);
  await clickSelector('#fbPick');
  await clickSelector('#faceInspectorTabs [data-fi-tab="components"]');
  check('P38 指出位置記下元素、且那一下沒有交給 app', await eval_(`!document.querySelector('#fbPanel').hidden && document.querySelector('#fbTarget').textContent.includes('data-fi-tab="components"')`) && await eval_(`fe.fiTab`) === tabBefore);
  if (!fbDir) {
    skipped.push('P38 feedback submission/automatic capture: isolated feedback directory unavailable');
    console.log('[SKIP]',skipped.at(-1));
    await pressKey('Escape','Escape',27);
  } else {
    const before = fbList();
    await pressKey('Enter','Enter',13,2);
    for (let i=0;i<300 && fbList().length===before.length;i++) await sleep(100);
    /* 競態修復:fbList() 偵到的是 serve.py 落盤;面板要等瀏覽器收到 POST 回應
       才關閉、欄位才清空——「檔案已到但回應還沒回來」時立刻斷言會間歇誤判。
       繼續輪詢真正的條件(面板 hidden),斷言本身不變。 */
    for (let i=0;i<50;i++) {
      if (await eval_(`document.querySelector('#fbPanel').hidden`)) break;
      await sleep(100);
    }
    const added = fbList().filter(n=>!before.includes(n));
    check('P38 Ctrl+Enter 送出後寫出一筆回報且面板關閉', added.length===1 && await eval_(`document.querySelector('#fbPanel').hidden`), added);
    if (added.length===1) {
      const m = fbMeta(added[0]); const d = require('path').join(fbDir, added[0]); const fs = require('fs');
      check('P38 回報帶分類、說明、指到的元素與畫面', m.kind==='unexpected' && m.note.includes('P38') && m.target.el.includes('data-fi-tab="components"') && m.context.view.includes('面工作區 · 面 1'), m);
      check('P38 回報帶被拒指令、世界與紅框畫面快照',
        fs.readFileSync(require('path').join(d,'events.jsonl'),'utf8').includes('place 999') &&
        fs.readFileSync(require('path').join(d,'world.scene'),'utf8').includes('spec') &&
        fs.readFileSync(require('path').join(d,'page.html'),'utf8').includes('data-fb-target') &&
        !fs.readFileSync(require('path').join(d,'page.html'),'utf8').includes('<script'));
    }
    check('P38 送出後面板欄位已清空', await eval_(`document.querySelector('#fbNote').value==='' && document.querySelector('#fbTarget').textContent==='尚未指定元素'`));
    // Test the negative case BEFORE the error probe starts the 20s auto-report
    // cooldown. Use the same observation budget as a positive report, not 800ms.
    const beforeRejection = fbList();
    const rejected = await eval_(`api('line place 998 on 1 at-line guide 1')`);
    for (let i=0;i<300 && fbList().length===beforeRejection.length;i++) await sleep(100);
    const rejectionQuiet = rejected?.ok===false && typeof rejected.error==='string' && rejected.error.length>0 && fbList().length===beforeRejection.length;
    check('P38 規則拒絕(ok:false)不自動存', rejectionQuiet, {rejected,added:fbList().filter(n=>!beforeRejection.includes(n))});
    if (!rejectionQuiet) throw Error('P38 rule rejection failed or created a report; refusing to run the auto probe under an unexpected cooldown.');
    const before2 = fbList();
    expectedException={message:'Error: fb-auto-probe',until:Date.now()+15000};
    await eval_(`setTimeout(()=>{throw new Error('fb-auto-probe')},0)`);
    // Like manual submission above, allow the actual report to finish writing.
    // On WSL the async capture can exceed six seconds; receiving the error event
    // does not mean its report has already reached the filesystem.
    for (let i=0;i<300;i++) {
      const pendingAuto = fbList().filter(n=>!before2.includes(n));
      if (pendingAuto.length && pendingAuto.every(id=>fs.existsSync(path.join(fbDir,id,'meta.json')))) break;
      await sleep(100);
    }
    const auto = fbList().filter(n=>!before2.includes(n));
    const autoComplete = auto.length===1 && fbMeta(auto[0]).kind==='auto' && fbMeta(auto[0]).auto_reason.includes('fb-auto-probe');
    check('P38 未捕捉的 JS 例外自動存一筆 kind=auto', autoComplete, auto);
    if (!autoComplete) throw Error('P38 automatic capture did not complete correctly.');
    check('P38 預期的單次例外確實抵達',expectedException===null);
    expectedException=null;
  }

  console.log('=== P39. 主畫布 Delete/Backspace 刪除選取的卡片 ===');
  const faceExists = id => eval_(`api("objects").then(r=>r.faces.some(f=>f.id===${id}))`);
  const selectCard = async id => { await eval_(`(()=>{selectObject("boundary",${id});document.activeElement&&document.activeElement.blur()})()`); await sleep(150); };
  await setupRemaining(['boundary 51 outline 0,0 1000,0 1000,800 0,800','canvas-pos boundary 51 60 60']);
  await selectCard(51);
  const deleted51Toasts=await captureNewToasts(async()=>{await pressKey('Delete','Delete',46);await sleep(300);});
  check('P39 Delete 刪除選取的面', !(await faceExists(51)));
  check('P39 刪除後 toast 提示可復原',deleted51Toasts.some(t=>t.visible&&t.classes.includes('error')&&t.text.includes('51')&&t.text.includes('復原')),deleted51Toasts);
  await pressKey('z','KeyZ',90,2);
  await sleep(300);
  check('P39 Ctrl+Z 復原被 Delete 刪掉的面', await faceExists(51));
  await eval_(`renderObjects()`); await sleep(200);
  await selectCard(51);
  await pressKey('Backspace','Backspace',8);
  await sleep(300);
  check('P39 Backspace 同樣刪除選取的面', !(await faceExists(51)));
  await pressKey('z','KeyZ',90,2); await sleep(300);
  await eval_(`renderObjects()`); await sleep(200);
  await selectCard(51);
  await eval_(`document.getElementById('searchInput').focus()`);
  await pressKey('Backspace','Backspace',8);
  check('P39 焦點在輸入框時 Backspace 不刪卡片', await faceExists(51));
  await eval_(`document.activeElement.blur()`);
  await selectCard(51);
  /* GEO-186(b) 後畫布只剩 rect 繪圖工具;繪圖工具備妥時 Delete/Backspace 一樣不刪卡片 */
  await eval_(`setOcTool('rect')`); await sleep(150);
  await eval_(`oc.sel={kind:'boundary',id:51}`);
  await pressKey('Backspace','Backspace',8);
  await pressKey('Delete','Delete',46);
  check('P39 矩形工具備妥時 Delete/Backspace 不刪卡片', await faceExists(51));
  await pressKey('Escape','Escape',27); await pressKey('Escape','Escape',27); await pressKey('Escape','Escape',27);
  await eval_(`(async()=>{resetSceneFocus();await api('default');await renderObjects()})()`);
  const p39Before = (await eval_(`apiRequest('dump')`)).text;
  await selectCard(1);
  /* 被引用的面:核心回 I8a 影響預覽,deleteObject 停在原生對話框等確認——不能用 pressKey(它會 waitIdle) */
  for (const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{type,key:'Delete',code:'Delete',windowsVirtualKeyCode:46});
  for (let i=0;i<30 && !(await eval_(`!!document.querySelector('dialog.reference-impact[open]')`));i++) await sleep(100);
  check('P39 刪除被引用的面先跳影響預覽,不直接刪', await eval_(`!!document.querySelector('dialog.reference-impact[open]')`) && await faceExists(1));
  await pressKey('Escape','Escape',27);
  await sleep(300);
  check('P39 影響預覽 Esc 取消後世界不變', !(await eval_(`!!document.querySelector('dialog.reference-impact[open]')`)) && await faceExists(1) && (await eval_(`apiRequest('dump')`)).text === p39Before);

  console.log('=== P40. 建面 UI/UX 審查修正(GEO-185 存活路徑;GEO-186 後) ===');
  /* GEO-186(b) 移除畫布 P 工具後,原 P40 的多邊形格線(#polyGridSize)、閉合就緒浮標、
     Esc 暫存草稿、鍵入長度浮標等斷言隨機器一併移除(狀態機行為由 polydraft_test.js
     + §P35/P36 面內段覆蓋)。本節改驗 GEO-185 修正中仍存在於現行路徑的部分:
     一般格線間距、工具浮標不被 toast 蓋掉、建面成功單一 toast、放置表單預設軸。 */
  await send('Emulation.setDeviceMetricsOverride',{width:1382,height:860,deviceScaleFactor:1,mobile:false});
  await emptyWorld();
  await eval_(`oc.zoom=1;oc.panX=0;oc.panY=0;ocApply();setOcTool('select')`);
  const gridOf = () => eval_(`(()=>{const v=document.getElementById('canvasViewport');return {size:v.style.getPropertyValue('--grid-size'),cls:v.classList.contains('poly-snap-grid')}})()`);
  check('P40-1 一般模式格線 24 單位、無吸附格線類別', (await gridOf()).size === '24px' && !(await gridOf()).cls, await gridOf());
  /* rect 工具浮標不被 toast 蓋掉(原 P40-5 的存活路徑):R 啟用 → 單點出
     「請拖出範圍」toast → 浮標仍可見且 toast 排在浮標下方。
     先清掉前段殘留的 toast,只取這次點擊產生的那則。 */
  const o40 = await ocOrigin();
  await pressKey('r','KeyR',82); await sleep(150);
  await clickControl('#canvasModeHintHelp');
  await eval_(`document.querySelectorAll('#toastRegion .toast').forEach(t=>t.remove())`);
  const t40Toasts=await captureNewToasts(async()=>{await click(o40.x+600, o40.y+550);await sleep(300);},
    `(()=>{const h=document.getElementById('canvasModeHint');return {hintVis:!h.hidden&&getComputedStyle(h).visibility==='visible',hintBottom:h.getBoundingClientRect().bottom};})()`);
  const t40Toast=t40Toasts.find(t=>t.visible&&t.classes.includes('error')&&t.text.includes('拖出範圍'));
  const t40={hintVis:t40Toast?.state.hintVis,hintBottom:t40Toast?.state.hintBottom,toastTop:t40Toast?.bounds.top??null,toastText:t40Toast?.text||''};
  check('P40-2 rect 浮標在 toast 出現時仍可見、toast 排在浮標下方',
    t40.hintVis && t40.toastTop!==null && t40.toastTop>=t40.hintBottom && /拖出範圍/.test(t40.toastText), t40);
  /* 拖出矩形建面(objEmitFace):成功 toast 只有一則;新面放置表單預設 u=+x/v=+y、
     沒有「必須垂直」錯誤(原 P40-6/P40-8,改走矩形路徑) */
  await eval_(`document.querySelectorAll('#toastRegion .toast').forEach(t=>t.remove())`);
  const madeToasts=await captureNewToasts(async()=>{await drag(o40.x+100,o40.y+100,o40.x+400,o40.y+350);await sleep(900);});
  const made = await eval_(`({
    v:document.querySelector('#placeV')?.value, u:document.querySelector('#placeU')?.value,
    err:[...document.querySelectorAll('#inspectorContent *, .inspector *')].some(e=>e.children.length===0&&e.textContent.includes('必須垂直'))})`);
  made.toasts=madeToasts.filter(t=>t.visible&&t.classes.includes('ok')&&t.text.includes('已建立')).length;
  check('P40-3 建面成功只跳一則 toast', made.toasts===1, made);
  check('P40-4 新面的放置表單預設 u=+x、v=+y,沒有「必須垂直」錯誤', made.u==='+x' && made.v==='+y' && !made.err, made);
  await eval_(`setOcTool('select')`);

  console.log('=== P41. 縮到很小後找回卡片(GEO-187) ===');
  await setupRemaining(['boundary 61 outline 0,0 1000,0 1000,800 0,800','canvas-pos boundary 61 60 60',
    'boundary 62 outline 0,0 1000,0 1000,800 0,800','canvas-pos boundary 62 500 -3000']);
  const cardIn = id => eval_(`(()=>{const c=oroot.querySelector('.ocard[data-id="${id}"]');const r=c.getBoundingClientRect(),v=ocv.getBoundingClientRect();
    return {w:Math.round(r.width),inside:r.left>=v.left&&r.right<=v.right&&r.top>=v.top&&r.bottom<=v.bottom,zoom:oc.zoom}})()`);
  await eval_(`oc.zoom=0.02;oc.panX=300;oc.panY=300;ocApply()`);
  check('P41-1 縮到 2% 時格線間距不小於 8px(不再糊成灰色)', parseFloat(await eval_(`document.getElementById('canvasViewport').style.getPropertyValue('--grid-size')`)) >= 8);
  await eval_(`(()=>{selectObject('boundary',62);centerOnNode('boundary',62)})()`); await sleep(150);
  const loc = await cardIn(62);
  check('P41-2 縮很小時「定位卡片」會放大回 100% 並把卡片放進畫面', loc.zoom===1 && loc.inside && loc.w>=150, loc);
  await eval_(`oc.zoom=0.02;ocApply();centerOnNode('boundary',61);oc.zoom=0.02;(()=>{const c=cardCenter('boundary',61),r=ocv.getBoundingClientRect();oc.panX=r.width/2-c.x*oc.zoom;oc.panY=r.height/2-c.y*oc.zoom;ocApply()})()`);
  await clickSelector('#zoomLevelButton');
  const back = await cardIn(61);
  check('P41-3 點縮放比例回 100% 以畫面中心為準,中心的卡片不會飛出畫面', back.zoom===1 && back.inside, back);

  console.log('=== P42. 面內底圖臨摹(GEO-190) ===');
  await send('Emulation.setDeviceMetricsOverride',{width:1382,height:900,deviceScaleFactor:1,mobile:false});
  await setupRemaining(['boundary 1 outline 0,0 4000,0 4000,3000 0,3000']);
  await eval_(`(async()=>{ await enterFocus('face', 1); fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply(); })()`);
  await sleep(250);

  /* (1) 分頁 4 頁且順序正確;點「底圖」分頁顯示 #ulFile */
  const tabs42 = await eval_(`[...document.querySelectorAll('#faceInspectorTabs [data-fi-tab]')].map(t=>t.dataset.fiTab)`);
  check('P42-1 分頁 4 頁且順序正確(屬性/形狀/構件/底圖)',
    tabs42.join() === 'prop,shape,components,underlay', tabs42);
  await clickSelector('[data-fi-tab="underlay"]');
  const ul1 = await eval_(`(()=>{const p=document.querySelector('[data-fi-pane="underlay"]');
    return {hidden:p.hidden, hasFile:!!p.querySelector('#ulFile')};})()`);
  check('P42-1b 點「底圖」分頁顯示 #ulFile', !ul1.hidden && ul1.hasFile, ul1);

  /* (2) canvas 產生 200×100 PNG dataURL,feUnderlaySet 後 #feUnderlay 存在、
     預設 mmPerPx=面寬/200(4000 寬面 → 20)、opacity 0.5 */
  const ul2 = await eval_(`(()=>{
    const c=document.createElement('canvas'); c.width=200; c.height=100;
    c.getContext('2d').fillRect(0,0,200,100);
    const src=c.toDataURL('image/png');
    feUnderlaySet(1,{src,imgW:200,imgH:100});
    const img=document.getElementById('feUnderlay'), ul=oc.underlays[1];
    return {exists:!!img, mmPerPx:ul.mmPerPx, opacity:+img.getAttribute('opacity')};
  })()`);
  check('P42-2 #feUnderlay 存在、預設 mmPerPx=20(4000/200)、opacity 0.5',
    ul2.exists && ul2.mmPerPx === 20 && ul2.opacity === 0.5, ul2);

  /* (3) 量比例尺:餵 (0,0)/(100,0)(圖片 px)、套用 1000mm → mmPerPx=10,x/y 不變,
     #ulScale 更新,#feUnderlayCalib 消失 */
  const ul3 = await eval_(`(()=>{
    const before={x:oc.underlays[1].x,y:oc.underlays[1].y};
    feUnderlayCalibStart();
    feUnderlayCalibPoint([0,0]); feUnderlayCalibPoint([100,0]);
    const applied=feUnderlayApplyScale(1000), ul=oc.underlays[1];
    return {applied, mmPerPx:ul.mmPerPx, xSame:ul.x===before.x, ySame:ul.y===before.y,
      scale:+(document.getElementById('ulScale')?.textContent||'').split(' ')[0],
      calibGone:!document.getElementById('feUnderlayCalib')};
  })()`);
  check('P42-3 校準套用:mmPerPx=10、x/y 不變、#ulScale 更新、#feUnderlayCalib 消失',
    ul3.applied && ul3.mmPerPx === 10 && ul3.xSame && ul3.ySame && ul3.scale === 10 && ul3.calibGone, ul3);

  /* (4) #ulOpacity 改 0.8 → image opacity 0.8;#ulLock 勾選 → image pointer-events none */
  await clickSelector('#refAlignmentDetails summary');
  const ul4a = await eval_(`(()=>{
    const op=document.getElementById('ulOpacity'); op.value='0.8';
    op.dispatchEvent(new Event('input',{bubbles:true}));
    return +document.getElementById('feUnderlay').getAttribute('opacity');
  })()`);
  check('P42-4a #ulOpacity 改 0.8 → image opacity 0.8', ul4a === 0.8, ul4a);
  await clickSelector('#ulLock');
  const ul4b = await eval_(`document.getElementById('feUnderlay').getAttribute('pointer-events')`);
  check('P42-4b #ulLock 勾選 → image pointer-events none', ul4b === 'none', ul4b);
  await clickSelector('#ulLock');   /* 解鎖回去,供下面的拖曳測試用 */

  /* (5) 分頁作用中、未鎖定:CDP 滑鼠在圖上按住拖 100px → x 改變量換算 mm 後與
     #ulX 一致(誤差 ≤1mm,fe.zoom=1 時 100px screen = 100mm);
     切到「屬性」分頁後同樣拖曳 x 不變(#feUnderlay 這時 pointer-events=none)。 */
  const org42 = await feOrigin();
  const sx = org42.x + 200, sy = org42.y + 150;   /* 底圖(0,0)-(2000,1000)內、避開原點標與頂點 */
  const beforeDrag = await eval_(`({x:oc.underlays[1].x})`);
  await drag(sx, sy, sx + 100, sy, 8);
  await sleep(200);
  const afterDrag = await eval_(`({x:oc.underlays[1].x, ulX:+document.getElementById('ulX').value})`);
  const dx5 = afterDrag.x - beforeDrag.x;
  check('P42-5 底圖分頁拖 100px → x 改變量換算 mm 後與 #ulX 一致(誤差 ≤1mm)',
    Math.abs(dx5 - 100) <= 1 && Math.abs(afterDrag.x - afterDrag.ulX) <= 1,
    { beforeDrag, afterDrag, dx5 });
  await clickSelector('[data-fi-tab="prop"]');
  const beforeDrag2 = await eval_(`oc.underlays[1].x`);
  await drag(sx, sy, sx + 100, sy, 8);
  await sleep(200);
  const afterDrag2 = await eval_(`oc.underlays[1].x`);
  check('P42-5b 切到「屬性」分頁後同樣拖曳 x 不變', afterDrag2 === beforeDrag2, { beforeDrag2, afterDrag2 });

  /* (6) 底圖存在時,e 重畫外環用鍵盤仍成功(底圖不擋既有互動) */
  const ul6 = await eval_(`(async()=>{
    feSetTool('redraw');
    const key=(k,code)=>window.dispatchEvent(new KeyboardEvent('keydown',{key:k,code:code||k,bubbles:true}));
    for (const ch of '3000') key(ch,'Digit'+ch); key('ArrowRight');
    for (const ch of '2000') key(ch,'Digit'+ch); key('ArrowDown');
    key('Enter');
    for(let i=0;i<100&&fe.tool!=='select';i++)await new Promise(r=>setTimeout(r,50));
    const b=await api('boundary 1');
    return {ok:b.ok, nverts:b.loops[0].verts.length, tool:fe.tool, hasUnderlay:!!oc.underlays[1]};
  })()`);
  check('P42-6 底圖存在時鍵盤重畫外環(3000→ 2000↓ Enter)仍成功',
    ul6.ok && ul6.nverts >= 3 && ul6.tool === 'select' && ul6.hasUnderlay, ul6);

  /* (7) 量比例尺進行中按 Esc → fe.ulCalib 為 null 且仍在工作區 */
  const startedCalib = await eval_(`(()=>{ feUnderlayCalibStart(); return !!fe.ulCalib; })()`);
  await pressKey('Escape','Escape',27);
  const ul7 = await eval_(`({calib: fe.ulCalib, stillIn: !!(oc.focus && oc.focus.t==='face')})`);
  check('P42-7 量比例尺進行中按 Esc → fe.ulCalib 為 null 且仍在工作區',
    startedCalib && ul7.calib === null && ul7.stillIn, { startedCalib, ul7 });

  /* (8) 離開面(Esc)再進同一面,底圖仍在;api("dump") 文字不含底圖資訊 */
  await pressKey('Escape','Escape',27);
  await eval_(`enterFocus('face',1)`); await sleep(250);
  const ul8 = await eval_(`({hasUnderlay: !!oc.underlays[1], imgExists: !!document.getElementById('feUnderlay')})`);
  const dump8 = (await eval_(`api('dump')`)).text;
  check('P42-8 離開面再進同一面底圖仍在;dump 不含底圖資訊',
    ul8.hasUnderlay && ul8.imgExists && !/underlay/i.test(dump8) &&
    !dump8.includes('底圖') && !dump8.includes('data:image'),
    { ul8, dumpLen: dump8.length });

  /* (9) 移除底圖的調整欄位；通用描面／保存／放置入口仍保留。 */
  const ul9 = await eval_(`(()=>{
    feUnderlayRemove(1);
    const pane=document.querySelector('[data-fi-pane="underlay"]');
    const others=pane ? [...pane.querySelectorAll('input,select,button')].filter(el=>!['ulFile','refImport','refDrawOutline','refGoPlace','refChoosePage','refCalibrateStep'].includes(el.id)&&el.dataset.projectAction!=='save') : ['no-pane'];
    return {imgGone: !document.getElementById('feUnderlay'), othersLeft: others.length, importKept:!!pane?.querySelector('#refImport')};
  })()`);
  check('P42-9 feUnderlayRemove 後底圖與調整欄位移除，保留匯入入口',
    ul9.imgGone && ul9.othersLeft === 0 && ul9.importKept, ul9);

  console.log('=== P43. 面內角材可選取(GEO-191) ===');
  await setupRemaining([
    'surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'timber 10 27 33 role boundary',
    'place 10 on 1 at-face e0 +u +n',
  ]);
  await eval_(`(async()=>{ await enterFocus('face', 1); })()`);
  await sleep(250);
  const feSvgOrigin = await eval_(`(()=>{const r=document.getElementById('faceEditorSvg').getBoundingClientRect();
    return {x:r.left,y:r.top};})()`);
  const timberScreenCenter = async () => {
    const p = await eval_(`(()=>{const t=fe.timbers.find(x=>x.id===10);
      const r=feTimberRect(t),o=$('faceEditorSvg').getBoundingClientRect(),p=feMmToPx((r[0]+r[2])/2,(r[1]+r[3])/2);return {x:o.left+p.x,y:o.top+p.y};})()`);
    return p;
  };
  const feBlankScreenPt = async (mx, my) => {
    return eval_(`(()=>{const o=$('faceEditorSvg').getBoundingClientRect(),p=feMmToPx(${mx},${my});return {x:o.left+p.x,y:o.top+p.y};})()`);
  };

  /* (1) 畫布有 .face-timber[data-face-hit="t:10"] */
  const p43_1 = await eval_(`!!document.querySelector('.face-timber[data-face-hit="t:10"]')`);
  check('P43-1 畫布有 .face-timber[data-face-hit="t:10"]', p43_1);

  /* (2) select 工具下點角材矩形內 → fe.sel、矩形 .sel、左欄列 .sel、feActionBar 只有一顆刪除鈕 */
  await eval_(`feSetTool('select')`);
  let tc = await timberScreenCenter();
  await click(tc.x, tc.y);
  await sleep(150);
  const p43_2 = await eval_(`(()=>{
    const rect = document.querySelector('.face-timber[data-face-hit="t:10"]');
    const row = document.querySelector('.face-layer-row[data-timber-id="10"]');
    const acts = [...document.querySelectorAll('#feActionBar [data-fe-act]')].map(b=>b.dataset.feAct);
    return { sel: fe.sel, rectSel: rect && rect.classList.contains('sel'),
      rowSel: !!(row && row.classList.contains('sel')),
      barHidden: document.getElementById('feActionBar').hidden, acts };
  })()`);
  check('P43-2 點角材 → fe.sel=timber:10、矩形/左欄高亮、feActionBar 有編輯與刪除',
    p43_2.sel && p43_2.sel.kind === 'timber' && p43_2.sel.id === 10 && p43_2.rectSel && p43_2.rowSel &&
    !p43_2.barHidden && JSON.stringify(p43_2.acts) === JSON.stringify(['edit','delete']), p43_2);

  /* (3) 點面內、不在角材上的空白 → fe.sel.kind === "point"(舊行為不變) */
  const blankPt = await feBlankScreenPt(2000, 1500);
  await click(blankPt.x, blankPt.y);
  await sleep(150);
  const p43_3 = await eval_(`fe.sel && fe.sel.kind`);
  check('P43-3 點面內空白 → fe.sel.kind === "point"', p43_3 === 'point', p43_3);

  /* (4) 選角材後按 Esc → fe.sel === null,矩形無 .sel,仍在工作區 */
  tc = await timberScreenCenter();
  await click(tc.x, tc.y);
  await sleep(150);
  await pressKey('Escape', 'Escape', 27);
  const p43_4 = await eval_(`(()=>{
    const rect = document.querySelector('.face-timber[data-face-hit="t:10"]');
    return { sel: fe.sel, rectSel: rect && rect.classList.contains('sel'),
      stillIn: !!(oc.focus && oc.focus.t === 'face') };
  })()`);
  check('P43-4 選角材後 Esc → fe.sel===null、矩形無 .sel、仍在工作區',
    p43_4.sel === null && !p43_4.rectSel && p43_4.stillIn, p43_4);

  /* (5) hover 左欄列 → 矩形加 .hover;mouseleave → 沒有 */
  const p43_5 = await eval_(`(()=>{
    const row = document.querySelector('.face-layer-row[data-timber-id="10"]');
    row.dispatchEvent(new MouseEvent('mouseenter', {bubbles:true}));
    const rect = document.querySelector('.face-timber[data-face-hit="t:10"]');
    const hoverOn = rect && rect.classList.contains('hover');
    row.dispatchEvent(new MouseEvent('mouseleave', {bubbles:true}));
    const rect2 = document.querySelector('.face-timber[data-face-hit="t:10"]');
    const hoverOff = !(rect2 && rect2.classList.contains('hover'));
    return { hoverOn, hoverOff };
  })()`);
  check('P43-5 hover 左欄列 → 矩形加 .hover;mouseleave → 沒有',
    p43_5.hoverOn && p43_5.hoverOff, p43_5);

  /* (6) 點左欄列(非 ✕ 鈕)→ 選取(同 P43-2) */
  const p43_6a = await eval_(`(()=>{
    document.querySelector('.face-layer-row[data-timber-id="10"]').click(); return true;
  })()`);
  await sleep(150);
  const p43_6 = await eval_(`(()=>{
    const rect = document.querySelector('.face-timber[data-face-hit="t:10"]');
    const row = document.querySelector('.face-layer-row[data-timber-id="10"]');
    return { sel: fe.sel, rectSel: rect && rect.classList.contains('sel'),
      rowSel: !!(row && row.classList.contains('sel')) };
  })()`);
  check('P43-6 點左欄列 → 選取(同畫布點選)',
    p43_6a && p43_6.sel && p43_6.sel.kind === 'timber' && p43_6.sel.id === 10 &&
    p43_6.rectSel && p43_6.rowSel, p43_6);

  /* (7) 角材頁顯示 #tbSelected「角材 10」;#tbSelDelete → fe.timbers 無 10、fe.sel===null;Ctrl+Z → 角材回來
     刪這支 boundary 角材會觸發 I8a 影響預覽(角色衍生屬性重算,api() 自動開 confirmReferenceImpact 對話框),
     要點 #impact-confirm 確認套用才真的落地——同 P22/P31/P39 既有影響預覽測試的作法。 */
  await eval_(`fiShowTab('timber')`);
  const p43_7a = await eval_(`(document.getElementById('tbSelected')?.textContent || '')`);
  check('P43-7a 角材頁 #tbSelected 顯示「角材 10」', p43_7a.includes('角材 10'), p43_7a);
  await clickSelector('#tbSelDelete');
  for (let i = 0; i < 30 && !(await eval_(`!!document.querySelector('dialog.reference-impact[open]')`)); i++) await sleep(100);
  /* 牙齒:上面註解明載刪 boundary 角材必觸發 I8a 影響預覽;對話框沒出現就是失敗,不是靜默略過。 */
  const p43_7dialog = await eval_(`!!document.querySelector('dialog.reference-impact[open]')`);
  check('P43-7a 刪 boundary 角材必須彈出 I8a 影響預覽對話框', p43_7dialog === true, p43_7dialog);
  if (p43_7dialog) await clickSelector('#impact-confirm');
  await sleep(200);
  const p43_7b = await eval_(`({ hasTimber: fe.timbers.some(t=>t.id===10), sel: fe.sel })`);
  check('P43-7b 刪除後 fe.timbers 無 10、fe.sel===null',
    !p43_7b.hasTimber && p43_7b.sel === null, p43_7b);
  await pressKey('z', 'KeyZ', 90, 2);
  await sleep(300);
  const p43_7c = await eval_(`fe.timbers.some(t=>t.id===10)`);
  check('P43-7c Ctrl+Z → 角材回來', p43_7c === true, p43_7c);
  const p43FaceLayout=await eval_(`(()=>{const top=document.querySelector('.object-workspace-topbar').getBoundingClientRect(),vp=$('faceEditorViewport').getBoundingClientRect();return {focus:oc.focus,composition:document.body.classList.contains('canvas-composition'),topHeight:top.height,viewportTop:vp.top,viewportHeight:vp.height,topBottom:top.bottom};})()`);
  check('P43-7d Undo 後仍是面內版面，沒有主畫布底部樣式殘留',p43FaceLayout.focus?.t==='face'&&!p43FaceLayout.composition&&p43FaceLayout.topHeight===56&&p43FaceLayout.viewportHeight>300&&p43FaceLayout.viewportTop>=p43FaceLayout.topBottom,p43FaceLayout);

  /* (8) 切到重畫外環工具 e,在角材位置落點仍成功(角材不擋) */
  await eval_(`feSetTool('redraw')`);
  tc = await timberScreenCenter();
  const p43RedrawHit=await eval_(`(()=>{const e=document.elementFromPoint(${tc.x},${tc.y}),r=$('faceEditorSvg').getBoundingClientRect(),rect=e=>{const b=e?.getBoundingClientRect();return b?{left:b.left,top:b.top,right:b.right,bottom:b.bottom}:null;};return {point:${JSON.stringify(tc)},hit:e?.outerHTML?.slice(0,220),origin:{x:r.left,y:r.top},previousOrigin:${JSON.stringify(feSvgOrigin)},viewport:rect($('faceEditorViewport')),timber:rect(document.querySelector('.face-timber[data-face-hit="t:10"]')),timberMm:feTimberRect(fe.timbers.find(t=>t.id===10)),bodyClass:document.body.className,focus:oc.focus,topbar:getComputedStyle(document.documentElement).getPropertyValue('--topbar-h')};})()`);
  await click(tc.x, tc.y);
  await sleep(150);
  const p43_8 = await eval_(`({ len: fe.draft.pts.length, tool: fe.tool })`);
  check('P43-8 e 工具時點角材位置仍成功落點(角材不擋)',
    p43_8.len === 1 && p43_8.tool === 'redraw', {...p43_8,hit:p43RedrawHit});
  await pressKey('Escape', 'Escape', 27);
  await pressKey('Escape', 'Escape', 27);

  console.log('=== P44. 面內工作區的四種游標互動(GEO-192) ===');
  /* 場景:surface 1 4000×3000,初始 camera 為 zoom=1/pan=0；視窗放大到能整份看到
     4000×3000。版面 settling 可能調整 camera，必須以實際 SVG CTM 換算螢幕座標，
     不能把 mm 直接加在 SVG 原點上，也不能再疊加 pan。每個大情境重新 setupRemaining。
     關掉吸附格線,避免縮放相依格距(feGridStep)干擾精確的 mm 斷言。 */
  // A failed edit must stop here: Undo would otherwise undo the fixture itself.
  const check44 = bodyCheck({detail:'empty',detailWhenPassing:true,throwOnFail:true});
  const requireFaceHit44 = async (name, point, expected) => {
    const hit = await eval_(`(()=>{const p=${JSON.stringify(point)},e=document.elementFromPoint(p.x,p.y),
      target=e?.closest('[data-face-hit]'),r=$('faceEditorViewport').getBoundingClientRect(),m=$('faceEditorRoot').getScreenCTM();
      return {point:p,expected:${JSON.stringify(expected)},actual:target?.dataset.faceHit||null,
        element:e?.outerHTML?.slice(0,300)||null,inViewport:p.x>=r.left&&p.x<r.right&&p.y>=r.top&&p.y<r.bottom,
        viewport:{left:r.left,top:r.top,right:r.right,bottom:r.bottom},
        camera:{zoom:fe.zoom,panX:fe.panX,panY:fe.panY},matrix:{a:m.a,b:m.b,c:m.c,d:m.d,e:m.e,f:m.f}};})()`);
    console.log('[P44 pointer precondition]', name, JSON.stringify(hit));
    // Preconditions strengthen existing cases without changing their golden assertion count.
    if (!hit.inViewport || hit.actual !== expected) check44(name+' 命中預期頂點／邊', false, hit);
    return hit;
  };
  await send('Emulation.setDeviceMetricsOverride', { width: 5400, height: 3800, deviceScaleFactor: 1, mobile: false });
  const openFace44 = async (panY = 0) => {
    await setupRemaining(['surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000']);
    await eval_(`(async()=>{ await enterFocus('face', 1); fe.zoom = 1; fe.panX = 0; fe.panY = ${panY}; feApply();
      const t = document.getElementById('faceSnapToggle'); if (t) t.checked = false; })()`);
    await sleep(250);
    const org = await feOrigin();
    return (mx, my) => org.point(mx, my);
  };
  const P44_TR = [4000, 0];      /* 右上角頂點 */
  const P44_EDGE_R_MID = [4000, 1500];   /* 右邊中點 */

  /* (1) 不按 Alt 拖右上角頂點往左下 500,500 → 外環仍 4 頂點、尺寸變 3500×2500 */
  let pt = await openFace44();
  const p44_1hit = await requireFaceHit44('P44-1 drag start', pt(...P44_TR), 'v:0:1');
  await drag(pt(...P44_TR).x, pt(...P44_TR).y, pt(3500, 500).x, pt(3500, 500).y);
  await sleep(200);
  const p44_1 = await eval_(`(async()=>{const b=await api('boundary 1');return {n:b.loops[0].verts.length, bb:loopsBBox(b.loops)};})()`);
  check44('P44-1 不按 Alt 拖頂點:外環仍 4 頂點、尺寸變 3500×2500',
    p44_1.n === 4 && p44_1.bb[2] - p44_1.bb[0] === 3500 && p44_1.bb[3] - p44_1.bb[1] === 2500, {...p44_1, hit:p44_1hit});
  await pressKey('z', 'KeyZ', 90, 2);
  const p44_1u = await eval_(`(async()=>{const b=await api('boundary 1');return b.loops[0].verts.length;})()`);
  check44('P44-1u Ctrl+Z 復原回 4 頂點', p44_1u === 4, p44_1u);

  /* (2) Alt 拖右上角頂點往左下(換算 1000,1000)→ 外環 6 頂點、指定形狀;
     fe.feats[1] 有一筆 type corner;形狀頁列出它。 */
  pt = await openFace44();
  await requireFaceHit44('P44-2 drag start', pt(...P44_TR), 'v:0:1');
  await dragMod(pt(4000, 0).x, pt(4000, 0).y, pt(3000, 1000).x, pt(3000, 1000).y, 6, 1);
  await sleep(200);
  const p44_2 = await eval_(`(async()=>{const b=await api('boundary 1');
    return {verts: b.loops[0].verts, feats: (fe.feats[1]||[]).map(f=>f.type)};})()`);
  const want2 = [[0,0],[3000,0],[3000,1000],[4000,1000],[4000,3000],[0,3000]];
  check44('P44-2 Alt 拖頂點捏缺口:外環 6 頂點且形狀正確', JSON.stringify(p44_2.verts) === JSON.stringify(want2), p44_2);
  check44('P44-2b fe.feats[1] 有一筆 type corner', p44_2.feats.length === 1 && p44_2.feats[0] === 'corner', p44_2.feats);
  await clickSelector('[data-fi-tab="shape"]');
  const p44_2c = await eval_(`document.querySelectorAll('.fe-feat[data-feat]').length`);
  check44('P44-2c 形狀頁列出這筆特徵', p44_2c === 1, p44_2c);
  await clickSelector('[data-fi-tab="prop"]');
  await pressKey('z', 'KeyZ', 90, 2);
  const p44_2u = await eval_(`(async()=>{const b=await api('boundary 1');return b.loops[0].verts.length;})()`);
  check44('P44-2u Ctrl+Z 復原回 4 頂點', p44_2u === 4, p44_2u);

  /* (3) Alt 拖到一半按 Esc → 外環不變、無 .fe-ghost */
  pt = await openFace44();
  const before3 = await eval_(`(async()=>(await api('boundary 1')).loops[0].verts)()`);
  await requireFaceHit44('P44-3 drag start', pt(...P44_TR), 'v:0:1');
  await pressDownMod(pt(4000, 0).x, pt(4000, 0).y, 1);
  await moveMod(pt(3400, 600).x, pt(3400, 600).y, 1);
  await sleep(150);
  await pressKey('Escape', 'Escape', 27);
  const after3 = await eval_(`(async()=>({verts:(await api('boundary 1')).loops[0].verts, ghost: !!document.querySelector('[data-fe-ghost]'), drag: fe.drag}))()`);
  check44('P44-3 Alt 拖到一半按 Esc:外環不變、無 .fe-ghost、fe.drag 清空',
    JSON.stringify(after3.verts) === JSON.stringify(before3) && !after3.ghost && after3.drag === null, { before3, after3 });
  /* 收尾:放開滑鼠鍵(避免殘留 pressed 狀態影響後續情境) */
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: pt(3400, 600).x, y: pt(3400, 600).y, button: 'left', clickCount: 1 });

  /* (4) 點右邊 → 凹口 → 面板開;拖預覽矩形「左」邊(depth 邊界)→ d 欄位 +200、其他欄位不變;
     Enter 套用後頂點數 8。(規則:B 的手把——沿邊方向的邊界動 w,垂直於邊且不與母邊重合的
     邊界動 d/dist,詳見 app.js feApplyGhostDrag 註解) */
  pt = await openFace44();
  await requireFaceHit44('P44-4 edge selection', pt(...P44_EDGE_R_MID), 'e:0:1');
  await click(pt(...P44_EDGE_R_MID).x, pt(...P44_EDGE_R_MID).y);
  await sleep(150);
  await clickSelector('[data-fe-act="op:notch"]');
  await sleep(150);
  const before4 = await eval_(`({...fe.op.params})`);
  const rect4 = await eval_(`feOpRect()`);   /* [3700,1200,4000,1800] */
  pt = (await feOrigin()).point;
  const hx = pt(rect4[0], (rect4[1] + rect4[3]) / 2);   /* 左邊界(depth)中點 */
  await dragMod(hx.x, hx.y, pt(rect4[0] - 200, (rect4[1] + rect4[3]) / 2).x, hx.y, 6, 0);
  await sleep(150);
  const after4 = await eval_(`({...fe.op.params})`);
  check44('P44-4a 拖預覽矩形「左」邊(depth 邊界)往左 200 → d 欄位 +200、其他欄位不變',
    after4.d === before4.d + 200 && after4.w === before4.w && after4.anchor === before4.anchor && after4.dist === before4.dist,
    { before4, after4 });
  await clickSelector('#feOpApply');
  await sleep(200);
  const p44_4b = await eval_(`(async()=>(await api('boundary 1')).loops[0].verts.length)()`);
  check44('P44-4b 套用後頂點數 8', p44_4b === 8, p44_4b);
  await pressKey('z', 'KeyZ', 90, 2);

  /* (5) 右鍵點右邊 → fe.sel 為 edge、#feCtxMenu 可見、其 [data-fe-act] 清單與 #feActionBar 逐一相同;
     點選單「凹口」→ fe.op.type==="notch"、選單關。Esc 兩下 → 面板關、選取清。 */
  pt = await openFace44();
  await rightClick(pt(...P44_EDGE_R_MID).x, pt(...P44_EDGE_R_MID).y);
  await sleep(150);
  const p44_5a = await eval_(`(()=>{
    const barActs = [...document.querySelectorAll('#feActionBar [data-fe-act]')].map(b=>b.dataset.feAct);
    const menuActs = [...document.querySelectorAll('#feCtxMenu [data-fe-act]')].map(b=>b.dataset.feAct);
    return { sel: fe.sel, menuHidden: document.getElementById('feCtxMenu').hidden, barActs, menuActs };
  })()`);
  check('P44-5a B 右鍵選邊：保留浮動列真命令並加入建立與檢視',
    p44_5a.sel && p44_5a.sel.kind === 'edge' && !p44_5a.menuHidden &&
    p44_5a.barActs.every(act=>p44_5a.menuActs.includes(act)) && p44_5a.menuActs.includes('create') && p44_5a.menuActs.includes('view'), p44_5a);
  await clickSelector('#feCtxMenu [data-fe-act="op:notch"]');
  await sleep(150);
  const p44_5b = await eval_(`({ opType: fe.op && fe.op.type, menuHidden: document.getElementById('feCtxMenu').hidden })`);
  check('P44-5b B 凹口表單側接、選單保留',
    p44_5b.opType === 'notch' && !p44_5b.menuHidden, p44_5b);
  await pressKey('Escape', 'Escape', 27);
  await pressKey('Escape', 'Escape', 27);
  const p44_5c = await eval_(`({ opPanelHidden: document.getElementById('feOpPanel').hidden, menuHidden:document.getElementById('feCtxMenu').hidden, sel: fe.sel })`);
  check('P44-5c B Esc 兩下 → 面板與選單關，原邊選取保留', p44_5c.opPanelHidden && p44_5c.menuHidden && p44_5c.sel?.kind === 'edge', p44_5c);

  /* (6) B 面外空白提供檢視、fe.sel===null；角材保留編輯與刪除。 */
  pt = await openFace44();
  const outside6 = pt(4300, 1500);
  await rightClick(outside6.x, outside6.y);
  await sleep(150);
  const p44_6a = await eval_(`({ menuHidden: document.getElementById('feCtxMenu').hidden, sel: fe.sel })`);
  check('P44-6a B 右鍵面外空白 → 檢視選單、fe.sel===null', !p44_6a.menuHidden && p44_6a.sel === null, p44_6a);
  await setupRemaining([
    'surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'timber 10 27 33 role boundary',
    'place 10 on 1 at-face e0 +u +n',
  ]);
  await eval_(`(async()=>{ await enterFocus('face', 1); fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply(); })()`);
  await sleep(250);
  const org6 = await feOrigin();
  const tc6 = await eval_(`(()=>{const t=fe.timbers.find(x=>x.id===10);const r=feTimberRect(t);return feMmToPx((r[0]+r[2])/2,(r[1]+r[3])/2);})()`);
  await rightClick(org6.x + tc6.x, org6.y + tc6.y);
  await sleep(150);
  const p44_6b = await eval_(`[...document.querySelectorAll('#feCtxMenu [data-fe-act]')].map(b=>b.dataset.feAct)`);
  check('P44-6b 右鍵角材 → 選單保留「編輯」與「刪除」', ['edit','delete'].every(a=>p44_6b.includes(a)) && !p44_6b.some(a=>a.startsWith('op:')), p44_6b);
  await pressKey('Escape', 'Escape', 27);

  /* (7) 雙擊右邊 → notch 面板可見;雙擊右上角 → corner;雙擊面內空白(2000,1500) → hole 且
     fe.sel.kind==="point";雙擊角材 → fe.fiTab==="timber" 且 fe.sel.kind==="timber"。
     注意:瀏覽器原生 dblclick 是照「第二下當時滑鼠位置底下的元素」派送——如果第一下選取後
     跳出的浮動列/面板恰好蓋住同一個點,而點到的按鈕又在自己的 click handler 裡同步整份重繪
     (feSyncOverlays 換掉 DOM),原生 dblclick 事件會指到一個剛被拔掉的節點、永遠冒泡不到
     #faceEditorViewport(這是瀏覽器事件模型的既有限制,不是本票要修的行為)。凹口浮動列在
     邊中點附近、切角浮動列在角本身正上方(y 下限 24px 的夾限讓它幾乎貼著頂列的角)都恰好撞上
     這個情況,所以雙擊點刻意避開浮動列涵蓋的範圍(邊改點邊上別的位置、頂列的角改把面往下平移),
     不代表雙擊互動本身只在特定位置才有效——feDblOpenFor 的邏輯與點擊位置無關。 */
  pt = await openFace44();
  await dblclick(pt(4000, 300).x, pt(4000, 300).y);   /* 右邊,避開邊中點附近的浮動列 */
  await sleep(200);
  const p44_7a = await eval_(`({ opType: fe.op && fe.op.type, panelHidden: document.getElementById('feOpPanel').hidden })`);
  check('P44-7a 雙擊右邊 → fe.op.type==="notch" 且面板可見', p44_7a.opType === 'notch' && !p44_7a.panelHidden, p44_7a);
  pt = await openFace44(200);   /* 面往下平移 200px,讓頂列的角不再貼著視窗上緣、浮動列不夾在角上 */
  await dblclick(pt(...P44_TR).x, pt(...P44_TR).y);
  await sleep(200);
  const p44_7b = await eval_(`fe.op && fe.op.type`);
  check('P44-7b 雙擊右上角 → fe.op.type==="corner"', p44_7b === 'corner', p44_7b);
  pt = await openFace44();
  await dblclick(pt(2000, 1500).x, pt(2000, 1500).y);
  await sleep(200);
  const p44_7c = await eval_(`({ opType: fe.op && fe.op.type, selKind: fe.sel && fe.sel.kind })`);
  check('P44-7c 雙擊面內空白 → fe.op.type==="hole" 且 fe.sel.kind==="point"',
    p44_7c.opType === 'hole' && p44_7c.selKind === 'point', p44_7c);
  await setupRemaining([
    'surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'timber 10 27 33 role boundary',
    'place 10 on 1 at-face e0 +u +n',
  ]);
  await eval_(`(async()=>{ await enterFocus('face', 1); fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply(); })()`);
  await sleep(250);
  const org7 = await feOrigin();
  const tc7 = await eval_(`(()=>{const t=fe.timbers.find(x=>x.id===10);const r=feTimberRect(t);return feMmToPx((r[0]+r[2])/2,(r[1]+r[3])/2);})()`);
  await dblclick(org7.x + tc7.x, org7.y + tc7.y);
  await sleep(200);
  const p44_7d = await eval_(`({ fiTab: fe.fiTab, selKind: fe.sel && fe.sel.kind })`);
  check('P44-7d 雙擊角材 → fe.fiTab==="timber" 且 fe.sel.kind==="timber"',
    p44_7d.fiTab === 'timber' && p44_7d.selKind === 'timber', p44_7d);

  /* (8) 雙擊後單擊面外空白 → 面板關、選取清(雙擊沒留下殘留狀態) */
  pt = await openFace44();
  await dblclick(pt(...P44_EDGE_R_MID).x, pt(...P44_EDGE_R_MID).y);
  await sleep(200);
  await click(pt(4300, 2500).x, pt(4300, 2500).y);
  await sleep(150);
  const p44_8 = await eval_(`({ opPanelHidden: document.getElementById('feOpPanel').hidden, barHidden: document.getElementById('feActionBar').hidden, sel: fe.sel })`);
  check('P44-8 雙擊後單擊面外空白 → 面板關、選取清',
    p44_8.opPanelHidden && p44_8.barHidden && p44_8.sel === null, p44_8);

  await pressKey('Escape', 'Escape', 27);

  console.log('=== P45. 重畫外環閉合併點提示(GEO-193)===');
  /* (a) 鍵盤 4000→ 1000↓ 1000← Enter:末點(3000,1000)與起點(0,0)不同軸,自動補角
     (0,1000)閉合;(3000,1000)與相鄰兩點共線,被去共線併掉——外環仍是合法的
     4000×1000 矩形(4頂點),但狀態列要提示哪個轉折被併入直線,不能靜默消失。 */
  const p45a = await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    oc.focus = null; oc.stack = [];
    await renderObjects();
    await enterFocus("face", 1);
    feSetTool("redraw");
    const key = (k, code) => window.dispatchEvent(new KeyboardEvent("keydown", {key: k, code: code || k, bubbles: true}));
    const seq = [["4000","ArrowRight"],["1000","ArrowDown"],["1000","ArrowLeft"]];
    for (const [len, dir] of seq) { for (const ch of len) key(ch, "Digit" + ch); key(dir); }
    key("Enter");
    for(let i=0;i<100&&!document.getElementById('status').textContent.includes('併入直線');i++)await new Promise(r=>setTimeout(r,50));
    const b = await api("boundary 1");
    return { verts: b.loops[0].verts.map(v=>v.join(",")).join(" "),
      status: document.getElementById('status').textContent };
  })()`);
  check('P45a 鍵盤 4000→1000↓1000← Enter → 外環4頂點4000×1000,狀態列含「(3000,1000)」與「併入直線」',
    p45a.verts === '0,0 4000,0 4000,1000 0,1000' &&
    p45a.status.includes('(3000,1000)') && p45a.status.includes('併入直線'), p45a);

  /* (b) 鍵盤 4000→ 3000↓ Enter:末點(4000,3000)與起點(0,0)不同軸,同樣要補角
     (0,3000),但這次補角後 4 點都是原本草稿+候選點、沒有共線贅點——直接閉合成
     4000×3000 矩形,狀態列不該出現「併入直線」提示。 */
  const p45b = await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    oc.focus = null; oc.stack = [];
    await renderObjects();
    await enterFocus("face", 1);
    feSetTool("redraw");
    const key = (k, code) => window.dispatchEvent(new KeyboardEvent("keydown", {key: k, code: code || k, bubbles: true}));
    const seq = [["4000","ArrowRight"],["3000","ArrowDown"]];
    for (const [len, dir] of seq) { for (const ch of len) key(ch, "Digit" + ch); key(dir); }
    key("Enter");
    await window.__cdpSettleUI(400);
    const b = await api("boundary 1");
    return { verts: b.loops[0].verts.map(v=>v.join(",")).join(" "),
      status: document.getElementById('status').textContent };
  })()`);
  check('P45b 4000→3000↓ Enter(直接同軸補角無併點) → 外環4頂點4000×3000,狀態列不含「併入直線」',
    p45b.verts === '0,0 4000,0 4000,3000 0,3000' && !p45b.status.includes('併入直線'), p45b);

  console.log('=== P46. 面內角材就地編輯(GEO-194) ===');
  await setupRemaining([
    'surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'timber 10 27 33 role boundary',
    'place 10 on 1 at-face e0 +u +n',
  ]);
  await eval_(`(async()=>{ await enterFocus('face', 1); })()`);
  await sleep(250);
  const p46SvgOrigin = await eval_(`(()=>{const r=document.getElementById('faceEditorSvg').getBoundingClientRect();
    return {x:r.left,y:r.top};})()`);
  const p46TimberCenter = async () => {
    const p = await eval_(`(()=>{const t=fe.timbers.find(x=>x.id===10);
      const r=feTimberRect(t); return feMmToPx((r[0]+r[2])/2,(r[1]+r[3])/2);})()`);
    return { x: p46SvgOrigin.x + p.x, y: p46SvgOrigin.y + p.y };
  };
  await eval_(`feSetTool('select')`);
  const p46tc = await p46TimberCenter();
  await click(p46tc.x, p46tc.y);
  await sleep(150);
  await eval_(`fiShowTab('timber')`);

  /* (a) 選取後 #tbEditForm 出現,A/B/dir/side 預填正確(橋接有回傳這幾項) */
  const p46a = await eval_(`(()=>{
    const f = document.getElementById('tbEditForm');
    return f ? {
      exists: true,
      A: document.getElementById('tbEditA').value,
      B: document.getElementById('tbEditB').value,
      dir: document.getElementById('tbEditDir').value,
      side: document.getElementById('tbEditSide').value,
      anchor: document.getElementById('tbEditAnchor').value,
    } : { exists: false };
  })()`);
  check('P46a #tbEditForm 出現且尺寸、方向及原定位引用皆正確帶入',
    p46a.exists && p46a.A === '27' && p46a.B === '33' && p46a.dir === '+u' &&
    p46a.side === '+n' && p46a.anchor === 'at-face e0', p46a);

  /* (b) 改 A=40、B=60、side 改 -n，保留已帶入的原定位引用 → 套用 →
     fe.timbers 仍只有一筆 id 10、A/B/side 如預期、fe.sel 仍是 timber 10。
     不用 clickSelector——它內建 waitIdle() 只等 5 秒,而 mutate() 的 oc.busy 在
     I8a 對話框開著、等使用者確認的整段期間都是 true,5 秒等不到會直接丟例外。
     改成:`.click()` 觸發後(不在 eval_ 裡 await 整條 mutate 鏈,那會卡死等一個沒有人
     會去點的對話框),自己分兩段輪詢——先等對話框(若有)、確認後再等 oc.busy 清空。 */
  await eval_(`{
    document.getElementById('tbEditA').value = '40';
    document.getElementById('tbEditB').value = '60';
    document.getElementById('tbEditSide').value = '-n';
  }`);
  await eval_(`document.getElementById('tbEditApply').click()`);
  for (let i = 0; i < 30 && !(await eval_(`!!document.querySelector('dialog.reference-impact[open]')`)); i++) await sleep(100);
  /* 牙齒:改 boundary 角材的 A/B/side 一律進 I8a 影響預覽(實測 2026-10-01 必出現);沒出現就是失敗,不靜默略過。 */
  const p46b_dialog = await eval_(`!!document.querySelector('dialog.reference-impact[open]')`);
  check('P46b 套用角材編輯必須彈出 I8a 影響預覽對話框', p46b_dialog === true, p46b_dialog);
  if (p46b_dialog) await eval_(`document.getElementById('impact-confirm').click()`);
  for (let i = 0; i < 60 && !(await eval_(`!oc.busy`)); i++) await sleep(100);
  await sleep(300);
  const p46b = await eval_(`({ timbers: fe.timbers.map(t=>t.id), t10: fe.timbers.find(t=>t.id===10), sel: fe.sel })`);
  check('P46b 套用 A=40/B=60/side=-n → fe.timbers 只有 id10、欄位如預期、fe.sel 仍是 timber 10',
    JSON.stringify(p46b.timbers) === '[10]' && p46b.t10 &&
    p46b.t10.A === 40 && p46b.t10.B === 60 && p46b.t10.side === '-n' &&
    p46b.sel && p46b.sel.kind === 'timber' && p46b.sel.id === 10, p46b);

  /* (c) Ctrl+Z → mutate 的三行(delete/timber/place)是同一個 history 群組,單步復原回 27×33 */
  await pressKey('z', 'KeyZ', 90, 2);
  await sleep(300);
  const p46c = await eval_(`(async()=>{ await feLoadGuides();
    return fe.timbers.find(t=>t.id===10); })()`);
  check('P46c Ctrl+Z 一次 → 回 A=27/B=33(mutate history 群組單步 undo)',
    p46c && p46c.A === 27 && p46c.B === 33, p46c);

  /* (d) 填 A=0 → 套用被前端擋下(不送指令),toast 出現,fe.timbers 不變 */
  await eval_(`fiShowTab('timber')`);
  let p46d;
  const invalidEditToasts46=await captureNewToasts(async()=>{p46d=await eval_(`(async()=>{
    document.getElementById('tbEditA').value = '0';
    document.getElementById('tbEditAnchor').value = 'at-face e0';
    const ok = await feTimberEditApply(10);
    return { ok, A: fe.timbers.find(t=>t.id===10).A };
  })()`);});p46d.toast=toastText(invalidEditToasts46,'error');
  check('P46d A=0 套用被擋、toast 出現、fe.timbers 不變',
    p46d.ok === false && p46d.A === 27 && p46d.toast.includes('正整數'), p46d);

  /* (e) Stored anchors can be changed explicitly and read back after revalidation. */
  await eval_(`$('tbEditA').value='27';$('tbEditAnchor').value='at-face e2';$('tbEditApply').click()`);
  for (let i=0;i<30 && !(await eval_(`!!document.querySelector('dialog.reference-impact[open]') || !oc.busy`));i++) await sleep(100);
  /* 牙齒:改定位引用到對邊同樣進 I8a 影響預覽(實測必出現);迴圈在「對話框或 busy 清空」任一成立即離開,
     所以這裡要明確要求是對話框,而不是 busy 清空後靜默略過。 */
  const p46e_dialog = await eval_(`!!document.querySelector('dialog.reference-impact[open]')`);
  check('P46e 改定位引用必須彈出 I8a 影響預覽對話框', p46e_dialog === true, p46e_dialog);
  if (p46e_dialog) await eval_(`$('impact-confirm').click()`);
  await waitForUI(`!oc.busy`,10000);await sleep(300);
  const p46e=await eval_(`(async()=>{await feLoadGuides();return fe.timbers.find(t=>t.id===10);})()`);
  check('P46e 明確改到對邊後回傳新定位並保持同一角材 ID',p46e?.definition?.anchor==='at-face e2' && p46e.A===27 && p46e.id===10,p46e);

  console.log('=== P47. 面內「角材放置」表單 UX 止血(GEO-195) ===');
  /* geometry-core/transactions.inc::reference_default_world 就是本票起因場景本身
     (面 1 4000×3000;角材 1/2 boundary 分別在 e0/e2;spec 主支中線 500 + guide 1 +
     角材 3 primary 在 guide 1 上)——用 api('default') 直接還原,不用手打 DSL。 */
  await send('Emulation.setDeviceMetricsOverride', { width: 5400, height: 3800, deviceScaleFactor: 1, mobile: false });
  await eval_(`(async()=>{ resetSceneFocus(); await api('default'); await renderObjects();
    await enterFocus('face', 1); fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
    const t = document.getElementById('faceSnapToggle'); if (t) t.checked = false; })()`);
  await sleep(250);
  await eval_(`fiShowTab('timber')`);
  const openFace47 = async () => {
    await eval_(`(()=>{ fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply(); })()`);
    await sleep(100);
    const org = await feOrigin();
    return (mx, my) => ({ x: org.x + mx, y: org.y + my });
  };
  const clearToasts = () => eval_(`document.getElementById('toastRegion').innerHTML = ''`);

  /* (1) #tbAnchor 預設值不是已占用的 e0/e2/guide 1(三者都已有角材);
     選項文字含「已有角材 1」「已有角材 2」(guide 1 被角材 3 占用,文字含「已有角材 3」)。 */
  const p47_1 = await eval_(`(()=>{
    const sel = document.getElementById('tbAnchor');
    return { value: sel.value, opts: [...sel.options].map(o => o.textContent) };
  })()`);
  check('P47-1 #tbAnchor 預設值不是 e0/e2/guide 1,選項含已占用標記',
    !['at-face e0', 'at-face e2', 'at-line guide 1'].includes(p47_1.value) &&
    p47_1.opts.some(t => t.includes('已有角材 1')) &&
    p47_1.opts.some(t => t.includes('已有角材 2')) &&
    p47_1.opts.some(t => t.includes('已有角材 3')), p47_1);

  /* (2) 角材工具啟用 → 畫布有 .fe-anchor-hi 且 .fe-anchor-band;
     #faceCanvasHint 或狀態列含「點一條邊或參考線直接放置」;切回 select → 兩者消失。
     GEO-196:提示文字整句換掉(見 feTimberHintRefresh),不再是「點擊位置不影響位置」——
     這是本票故意的行為變更(新增點線直接放置路徑),不是鬆綁斷言。 */
  await eval_(`feSetTool('timber')`);
  await sleep(150);
  const p47_2a = await eval_(`({
    hi: document.querySelectorAll('#faceEditorRoot .fe-anchor-hi').length,
    band: document.querySelectorAll('#faceEditorRoot .fe-anchor-band').length,
    hint: document.getElementById('faceCanvasHint').textContent,
    status: document.getElementById('status').textContent,
  })`);
  check('P47-2a 角材工具保留定位預示及即時定位與截面摘要',
    p47_2a.hi > 0 && p47_2a.band > 0 &&
    p47_2a.hint.includes('目前定位：')&&p47_2a.hint.includes('截面'), p47_2a);
  await eval_(`feSetTool('select')`);
  await sleep(150);
  const p47_2b = await eval_(`({
    hi: document.querySelectorAll('#faceEditorRoot .fe-anchor-hi').length,
    band: document.querySelectorAll('#faceEditorRoot .fe-anchor-band').length,
  })`);
  check('P47-2b 切回 select → 預示消失', p47_2b.hi === 0 && p47_2b.band === 0, p47_2b);

  /* (3) 主支軸為 v(角材 3 primary、dir +v):方向 +u(垂直於主支軸)→ primary disabled、
     boundary 可選;方向 +v(平行於主支軸)→ boundary/secondary disabled、primary 可選。 */
  await eval_(`(()=>{ const s = document.getElementById('tbDir'); s.value = '+u';
    s.dispatchEvent(new Event('change')); })()`);
  const p47_3a = await eval_(`(()=>{ const o = [...document.getElementById('tbRole').options];
    return Object.fromEntries(o.map(x => [x.value, x.disabled])); })()`);
  check('P47-3a 方向 +u(垂直主支軸)→ primary disabled、boundary 可選',
    p47_3a.primary === true && p47_3a.boundary === false, p47_3a);
  await eval_(`(()=>{ const s = document.getElementById('tbDir'); s.value = '+v';
    s.dispatchEvent(new Event('change')); })()`);
  const p47_3b = await eval_(`(()=>{ const o = [...document.getElementById('tbRole').options];
    return Object.fromEntries(o.map(x => [x.value, x.disabled])); })()`);
  check('P47-3b 方向 +v(平行主支軸)→ boundary/secondary disabled、primary 可選',
    p47_3b.boundary === true && p47_3b.secondary === true && p47_3b.primary === false, p47_3b);

  /* (4) 強制 #tbAnchor=e0(已占滿)、方向 +u、角色 boundary(此方向下未 disabled,
     不用繞過),真滑鼠點面內 → toast 含「已被角材 1 占滿」與「可用:」;fe.timbers 仍 3;
     #tbAnchor 有 invalid 標記。 */
  await eval_(`(()=>{
    document.getElementById('tbAnchor').value = 'at-face e0';
    const dirSel = document.getElementById('tbDir'); dirSel.value = '+u';
    dirSel.dispatchEvent(new Event('change'));
    document.getElementById('tbRole').value = 'boundary';
  })()`);
  await eval_(`feSetTool('timber')`);
  await sleep(100);
  await clearToasts();
  let pt47 = await openFace47();
  const p47_4Toasts=await captureNewToasts(async()=>{await click(pt47(2000,1500).x,pt47(2000,1500).y);await sleep(300);});
  const p47_4 = await eval_(`({
    timbers: fe.timbers.map(t => t.id).sort(),
    anchorInvalid: document.getElementById('tbAnchor').classList.contains('invalid'),
  })`);p47_4.toast=toastText(p47_4Toasts,'error');
  check('P47-4 e0 已被角材 1 占滿 → toast 含「已被角材 1 占滿」與「可用:」;仍 3 支;#tbAnchor invalid',
    p47_4.toast.includes('已被角材 1 占滿') && p47_4.toast.includes('可用:') &&
    JSON.stringify(p47_4.timbers) === '[1,2,3]' && p47_4.anchorInvalid, p47_4);

  /* (5) 依預設值(自動挑到的空線)點面內 → 成功,fe.timbers 4 支。「自動挑到的空線」
     用 referenceAnchorEntries 直接算第一條未占用的(不透過重新整理表單取得——
     renderFaceInspector() 的 restoreInspectorState 會刻意保留使用者上一次在 #tbAnchor
     打的值/選的值,這是給真實使用者用的草稿保留機制,不是這裡要測的「預設挑空線」邏輯,
     所以改直接算出第一條未占用的值再寫回欄位,等同使用者自己重選一條空線)。
     方向/角色照「垂直於主支軸→boundary、平行→primary」規則挑一組會被引擎接受的合法值
     (規格本身沒規定預設方向/角色一定是哪個,只規定定位引用要挑空線)。Ctrl+Z 回 3 支。 */
  const p47_5anchor = await eval_(`(()=>{
    const entries = referenceAnchorEntries(oc.edit.bid, feSurf(oc.edit.bid));
    return entries.find(e => e.occupied == null).value;
  })()`);
  await eval_(`(()=>{
    const s = document.getElementById('tbAnchor'); s.value = ${JSON.stringify(p47_5anchor)};
    s.dispatchEvent(new Event('change'));
  })()`);
  const p47_5line = await eval_(`feAnchorLineInfo(oc.edit.bid, document.getElementById('tbAnchor').value)`);
  const p47_5runAxis = p47_5line.constAxis === 'u' ? 'v' : 'u';
  const p47_5primaryAxis = await eval_(`feTimberPrimaryAxis(oc.edit.bid)`);
  const p47_5role = p47_5runAxis === p47_5primaryAxis ? 'primary' : 'boundary';
  await eval_(`(()=>{
    const dirSel = document.getElementById('tbDir'); dirSel.value = ${JSON.stringify('+' + p47_5runAxis)};
    dirSel.dispatchEvent(new Event('change'));
    document.getElementById('tbRole').value = ${JSON.stringify(p47_5role)};
  })()`);
  await eval_(`feSetTool('timber')`);
  await sleep(100);
  pt47 = await openFace47();
  await click(pt47(2000, 1500).x, pt47(2000, 1500).y);
  await waitForUI(`!oc.busy && fe.timbers.length===4`);
  const p47_5 = await eval_(`fe.timbers.map(t => t.id).sort()`);
  check('P47-5 依預設值(自動挑到的空線)點面內 → 成功,fe.timbers 4 支',
    JSON.stringify(p47_5) === '[1,2,3,4]', { p47_5, p47_5line, p47_5runAxis, p47_5role });
  await pressKey('z', 'KeyZ', 90, 2);
  await sleep(300);
  const p47_5u = await eval_(`(async()=>{ await feLoadGuides(); return fe.timbers.map(t => t.id).sort(); })()`);
  check('P47-5u Ctrl+Z → 回 3 支', JSON.stringify(p47_5u) === '[1,2,3]', p47_5u);

  /* (6) 設 #tbAnchor=e1、方向 +v(=主支軸,平行)、角色強制 boundary(JS 移除 disabled
     後選)→ 點面內 → toast 含「主支軸是 v」;仍 3 支。 */
  await eval_(`fiShowTab('timber')`);
  await eval_(`(()=>{
    document.getElementById('tbAnchor').value = 'at-face e1';
    const dirSel = document.getElementById('tbDir'); dirSel.value = '+v';
    dirSel.dispatchEvent(new Event('change'));
    const roleSel = document.getElementById('tbRole');
    const opt = [...roleSel.options].find(o => o.value === 'boundary');
    opt.disabled = false;
    roleSel.value = 'boundary';
  })()`);
  await eval_(`feSetTool('timber')`);
  await sleep(100);
  await clearToasts();
  pt47 = await openFace47();
  const p47_6Toasts=await captureNewToasts(async()=>{await click(pt47(2000,1500).x,pt47(2000,1500).y);await sleep(300);});
  const p47_6 = await eval_(`({
    timbers: fe.timbers.map(t => t.id).sort(),
  })`);p47_6.toast=toastText(p47_6Toasts,'error');
  check('P47-6 強制 boundary + 方向 v(平行主支軸)→ toast 含「主支軸是 v」;仍 3 支',
    p47_6.toast.includes('主支軸是 v') && JSON.stringify(p47_6.timbers) === '[1,2,3]', p47_6);

  console.log('=== P48. 角材工具下「點畫布上的線」直接放置(GEO-196) ===');
  /* 場景同 §P47(api('default') 還原:面 1 4000×3000、角材 1 boundary@e0(v=0)、
     角材 2 boundary@e2(v=3000)、角材 3 primary@guide 1(u=500,dir +v) → 主支軸 v)。
     命中線的透明判定線寬只有 12(邊)/14(參考線)局部座標單位、半寬 6/7——固定
     zoom=1/pan=0 時局部座標=mm 1:1(同 §P35 起頭的既有慣例),所以點擊座標要落在
     線的 ±6~7mm 內才會真的命中 data-face-hit,不能像人眼那樣「大概點在線附近」；
     下面每個點擊點都刻意落在線的 3mm 內。 */
  await eval_(`(async()=>{ resetSceneFocus(); await api('default'); await renderObjects();
    await enterFocus('face', 1); fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
    const t = document.getElementById('faceSnapToggle'); if (t) t.checked = false; })()`);
  await sleep(250);
  await eval_(`fiShowTab('timber')`);
  const openFace48 = async () => {
    await eval_(`(()=>{ fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply(); })()`);
    await sleep(100);
    const org = await feOrigin();
    return (mx, my) => ({ x: org.x + mx, y: org.y + my });
  };
  const clearToasts48 = () => eval_(`document.getElementById('toastRegion').innerHTML = ''`);

  /* (1) 真滑鼠點外輪廓邊 1(右邊,u=4000)靠面內側 3mm(3997,1500)→ fe.timbers 4 支,
     新支 dir 沿 v(邊 1 是 u 固定的線,沿 v 跑)、side "+n"(G196-R02 後由表單 #tbSide
     預設值決定,不再由點擊的面內側決定)、role primary(主支軸 v,邊 1 方向也是 v,
     平行);#tbAnchor 同步 at-face e1、#tbRole 同步 primary。Ctrl+Z 回 3 支。 */
  await eval_(`feSetTool('timber')`);
  await sleep(100);
  let pt48 = await openFace48();
  await click(pt48(3997, 1500).x, pt48(3997, 1500).y);
  await sleep(300);
  const p48_1 = await eval_(`(()=>{
    const ids = fe.timbers.map(t => t.id).sort((a,b)=>a-b);
    const newT = fe.timbers.find(t => t.id !== 1 && t.id !== 2 && t.id !== 3);
    return { ids, newT, anchor: document.getElementById('tbAnchor').value,
      role: document.getElementById('tbRole').value };
  })()`);
  check('P48-1 真滑鼠點外輪廓邊 1 靠內側 → 4 支,新支 dir=+v/side=+n/role=primary,表單同步',
    p48_1.ids.length === 4 && [1,2,3].every(id => p48_1.ids.includes(id)) &&
    p48_1.newT && p48_1.newT.dir === '+v' && p48_1.newT.side === '+n' && p48_1.newT.role === 'primary' &&
    p48_1.anchor === 'at-face e1' && p48_1.role === 'primary', p48_1);
  await pressKey('z', 'KeyZ', 90, 2);
  await sleep(300);
  const p48_1u = await eval_(`(async()=>{ await feLoadGuides(); return fe.timbers.map(t => t.id).sort(); })()`);
  check('P48-1u Ctrl+Z → 回 3 支', JSON.stringify(p48_1u) === '[1,2,3]', p48_1u);

  /* (2) 點外輪廓邊 0(v=0,已被角材 1 占滿;點在線上 (2000,0),側任意不影響本測項)→
     前端不擋,照舊送出,引擎拒絕、GEO-195 人話訊息接手:toast 含「已被角材 1 占滿」;
     仍 3 支。 */
  await clearToasts48();
  pt48 = await openFace48();
  const p48_2Toasts=await captureNewToasts(async()=>{await click(pt48(2000,0).x,pt48(2000,0).y);await sleep(300);});
  const p48_2 = await eval_(`({
    ids: fe.timbers.map(t => t.id).sort(),
  })`);p48_2.toast=toastText(p48_2Toasts,'error');
  check('P48-2 點已占滿的外輪廓邊 0 → 照舊送出、引擎拒絕,toast 含「已被角材 1 占滿」;仍 3 支',
    p48_2.toast.includes('已被角材 1 占滿') && JSON.stringify(p48_2.ids) === '[1,2,3]', p48_2);

  /* (3) 新增一條參考線 u≈2000(line spec 測試 2000 + line guide 2 1 v spec:測試),
     點它左側 3mm(u=1997)→ 4 支,新支 role primary(方向與主支軸 v 平行)。
     G196-R02 語意更正:side 一律由表單 #tbSide 決定(此處表單值 +n),點擊點在線的
     哪一側【不】再影響 ±n——舊斷言「點 +n 側→side +n」看起來同值,但因果不同:
     舊版是點擊位置覆寫,新版是表單沿用。左/右點對照與 -n 組合見 §P49。 */
  await eval_(`api("line spec 測試 2000")`);
  await eval_(`api("line guide 2 1 v spec:測試")`);
  /* 直接用 api() 建線繞過了 app.js 自己的建線按鈕(那條路徑事後會呼叫 feAfterChange()
     重繪檢視器),所以這裡要自己補一次 feLoadGuides()+renderFaceInspector(),否則
     #tbAnchor 的 <select> 還是舊 DOM,沒有新參考線的 <option>,之後把 .value 設成
     "at-line guide 2" 會因為找不到匹配選項而被瀏覽器悄悄清空成 ""(見 P48-3 除錯記錄)。 */
  await eval_(`(async()=>{ await feLoadGuides(); renderFaceInspector(); })()`);
  await eval_(`fiShowTab('timber')`);
  const p48_3info = await eval_(`feAnchorLineInfo(oc.edit.bid, 'at-line guide 2')`);
  const off3 = 3;
  const p48_3pt = p48_3info.constAxis === 'u'
    ? { x: p48_3info.value - off3, y: 1500 }
    : { x: 1500, y: p48_3info.value + off3 };
  const p48_3expectSide = '+n';
  await eval_(`feSetTool('timber')`);
  await sleep(100);
  pt48 = await openFace48();
  await click(pt48(p48_3pt.x, p48_3pt.y).x, pt48(p48_3pt.x, p48_3pt.y).y);
  await waitForUI(`!oc.busy && fe.timbers.length===4`);
  const p48_3 = await eval_(`(()=>{
    const ids = fe.timbers.map(t => t.id).sort((a,b)=>a-b);
    const newT = fe.timbers.find(t => t.id !== 1 && t.id !== 2 && t.id !== 3);
    return { ids, newT, anchor: document.getElementById('tbAnchor').value,
      side: document.getElementById('tbSide').value };
  })()`);
  check('P48-3 點新參考線 → 4 支,新支 role=primary/side 依表單(+n),#tbAnchor 同步該參考線(G196-R02)',
    p48_3.ids.length === 4 && [1,2,3].every(id => p48_3.ids.includes(id)) &&
    p48_3.newT && p48_3.newT.role === 'primary' && p48_3.newT.side === p48_3expectSide &&
    p48_3.anchor === 'at-line guide 2' && p48_3.side === '+n', { p48_3, p48_3info, p48_3pt });
  await pressKey('z', 'KeyZ', 90, 2);
  await waitForUI(`!oc.busy && fe.timbers.length===3`);
  const p48_3u = await eval_(`(async()=>{ await feLoadGuides(); return fe.timbers.map(t => t.id).sort(); })()`);
  check('P48-3u Ctrl+Z → 回 3 支', JSON.stringify(p48_3u) === '[1,2,3]', p48_3u);

  /* (4) 面內空白(1000,1700,遠離所有邊/上面新增的參考線 u≈2000/guide 1 u=500)→
     照舊走表單值:先把 #tbAnchor 設 e3、方向 +v、角色 primary(e3 是 u=0 的邊,
     方向 +v 與主支軸 v 平行,合法),點空白 → 4 支且 place 行含 "e3"。Ctrl+Z 回 3 支。 */
  await eval_(`window.__apiLog && (window.__apiLog.length = 0)`);
  await eval_(`(()=>{
    document.getElementById('tbAnchor').value = 'at-face e3';
    const dirSel = document.getElementById('tbDir'); dirSel.value = '+v';
    dirSel.dispatchEvent(new Event('change'));
    document.getElementById('tbRole').value = 'primary';
  })()`);
  await eval_(`feSetTool('timber')`);
  await sleep(100);
  pt48 = await openFace48();
  await click(pt48(1000, 1700).x, pt48(1000, 1700).y);
  await waitForUI(`!oc.busy && fe.timbers.length===4`);
  const p48_4 = await eval_(`({
    ids: fe.timbers.map(t => t.id).sort(),
    anchor: document.getElementById('tbAnchor').value,
    centerline: fe.timbers.find(t=>t.id===4)?.centerline,
    placeLine: (window.__apiLog || []).find(c => c.includes('place') && c.includes('e3')) || '',
  })`);
  check('P48-4 點面內空白 → 照舊走表單 e3，落在左外邊；共 4 支',
    JSON.stringify(p48_4.ids) === '[1,2,3,4]' && p48_4.anchor === 'at-face e3' &&
    p48_4.centerline < 100, p48_4);
  await pressKey('z', 'KeyZ', 90, 2);
  await waitForUI(`!oc.busy && fe.timbers.length===3`);
  const p48_4u = await eval_(`(async()=>{ await feLoadGuides(); return fe.timbers.map(t => t.id).sort(); })()`);
  check('P48-4u Ctrl+Z → 回 3 支', JSON.stringify(p48_4u) === '[1,2,3]', p48_4u);

  /* (5) hover(不點)邊 1(u=4000)→ .fe-anchor-hi 畫的是 e1(x1=x2=4000);
     移開到面內空白(不在任何線的命中走廊內)→ 回到表單目前值那條線。
     G196-R02:hover 不得改 #tbSide——先把表單 side 故意設 -n,hover 過線後仍要是 -n。 */
  await eval_(`(()=>{ document.getElementById('tbAnchor').value = 'at-face e0';
    document.getElementById('tbAnchor').dispatchEvent(new Event('change'));
    document.getElementById('tbSide').value = '-n';
    document.getElementById('tbSide').dispatchEvent(new Event('change')); })()`);
  await sleep(150);
  pt48 = await openFace48();
  const hoverPt1 = pt48(3999, 1500);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: hoverPt1.x, y: hoverPt1.y });
  await sleep(200);
  const p48_5a = await eval_(`(()=>{
    const l = document.querySelector('#faceEditorRoot .fe-anchor-hi');
    return { x1: l && l.getAttribute('x1'), x2: l && l.getAttribute('x2'), hoverAnchor: fe.timberHoverAnchor };
  })()`);
  check('P48-5a hover 邊 1(不點)→ .fe-anchor-hi 是 x=4000 的邊,fe.timberHoverAnchor=at-face e1',
    p48_5a.x1 === '4000' && p48_5a.x2 === '4000' && p48_5a.hoverAnchor === 'at-face e1', p48_5a);
  const blankPt48 = pt48(1000, 1700);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: blankPt48.x, y: blankPt48.y });
  await sleep(200);
  const p48_5b = await eval_(`(()=>{
    const l = document.querySelector('#faceEditorRoot .fe-anchor-hi');
    return { y1: l && l.getAttribute('y1'), y2: l && l.getAttribute('y2'), hoverAnchor: fe.timberHoverAnchor,
      side: document.getElementById('tbSide').value,
      hasHoverSide: 'timberHoverSide' in fe };
  })()`);
  check('P48-5b 移開到面內空白 → hoverAnchor 清空,預示回到表單值(#tbAnchor=at-face e0,v=0)',
    p48_5b.hoverAnchor === null && p48_5b.y1 === '0' && p48_5b.y2 === '0', p48_5b);
  check('P48-5c G196-R02:hover 過線不改 #tbSide(仍 -n)且 fe 無 timberHoverSide 殘留欄位',
    p48_5b.side === '-n' && p48_5b.hasHoverSide === false, p48_5b);

  /* (6) G196-R01:獨立 F-HOLE 場景——不依賴 (1)..(5) 留下的世界(guide 2、undo 歷史、
     表單殘值都不相干)。reset 後建一面 4000×3000 + 一個孔,零角材。
     setup 走 apiRequest 低階路徑(不經 api()→confirmReferenceImpact,setup 不該彈
     對話框),逐條記 {line,ok,error,preview},第一條失敗即停——前置壞了就讓對應
     check 紅掉,不進入互動步驟。 */
  const setupLinesG196 = async (lines) => eval_(`(async()=>{
    const out = [];
    const r0 = await apiRequest('reset');
    out.push({ line: 'reset', ok: r0.ok === true, error: r0.error || null, preview: !!r0.preview });
    if (r0.ok !== true) return out;
    for (const l of ${"__LINES__"}) {
      const r = await apiRequest('line ' + l);
      out.push({ line: l, ok: r.ok === true, error: r.error || null, preview: !!r.preview });
      if (r.ok !== true || r.preview) break;
    }
    return out;
  })()`.replace('__LINES__', JSON.stringify(lines)));

  /* helper 自測:故意餵一條不合法指令(引用不存在的 spec),setup 必須當場報錯返回,
     不得繼續——證明「前置失敗立即報錯」真的會失敗,不是擺設。被拒絕的指令不改世界
     (I8),不污染後續測試。 */
  const badSetup = await setupLinesG196(['guide 1 1 v spec:不存在', 'timber 9 27 33 role primary']);
  check('P48-6a setup helper:不合法指令(不存在的 spec)→ 當步失敗、不繼續送後面的指令',
    Array.isArray(badSetup) && badSetup.length === 2 && badSetup[0].ok === true &&
    badSetup[1].ok === false && !!badSetup[1].error, badSetup);

  /* F-HOLE(附錄 A):一面 4000×3000 + 孔 (1000,1000)~(2000,2000),零角材。 */
  const s6 = await setupLinesG196([
    'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000 hole 1000,1000 2000,1000 2000,2000 1000,2000']);
  check('P48-6b F-HOLE setup 全部成功且無 preview', Array.isArray(s6) &&
    s6.length === 2 && s6.every(r => r.ok === true && !r.preview), s6);
  await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
    fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
    const t = document.getElementById('faceSnapToggle'); if (t) t.checked = false;
    await feLoadGuides(); renderFaceInspector(); fiShowTab('timber'); })()`);
  await sleep(250);

  /* 點擊前驗證:孔確實存在(loops=2)、目標孔邊的 DOM hit 元素存在、
     elementFromPoint 真的命中 e:1:0(不是猜孔索引、不盲點畫面座標)。 */
  const pre6 = await eval_(`(()=>{
    const loops = oc.bmap[1] || [];
    const svgR = document.getElementById('faceEditorSvg').getBoundingClientRect();
    const cx = svgR.x + 1500, cy = svgR.y + 1000;   /* 孔邊 e:1:0 中點 */
    const el0 = document.elementFromPoint(cx, cy);
    const hitEl = el0 && el0.closest ? el0.closest('[data-face-hit]') : null;
    return { loops: loops.length, holeVerts: loops[1] ? loops[1].verts.length : 0,
      hitAtPoint: hitEl ? hitEl.dataset.faceHit : null, cx, cy };
  })()`);
  check('P48-6c 前置:孔存在(2 環)且 (1500,1000) elementFromPoint 命中孔邊 e:1:0',
    pre6.loops === 2 && pre6.holeVerts === 4 && pre6.hitAtPoint === 'e:1:0', pre6);

  /* 點擊前記錄世界 dump + 角材數(零支才是這個場景的正確基準),
     並攔截 apiRequest 記錄點擊後送出的指令。 */
  const dumpBefore6 = (await eval_(`apiRequest('dump')`)).text;
  await eval_(`(()=>{ window.__p48sent = [];
    if (!window.__rawApiRequest) window.__rawApiRequest = apiRequest;
    apiRequest = async c => { window.__p48sent.push(c); return window.__rawApiRequest(c); };
    return 0; })()`);
  await eval_(`feSetTool('timber')`);
  await sleep(120);
  await clearToasts48();
  const holeEdgeToasts=await captureNewToasts(async()=>{await click(pre6.cx,pre6.cy);await sleep(400);});
  const after6 = await eval_(`(async()=>{
    const d = await apiRequest('dump');
    const refs = await apiRequest('references');
    apiRequest = window.__rawApiRequest;   /* 還原攔截 */
    return { dump: d.text, bridgeTimbers: (refs.timbers || []).length,
      sent: (window.__p48sent || []).filter(c => /timber|place/.test(c)),
      feTimbers: (fe.timbers || []).length };
  })()`);after6.toast=toastText(holeEdgeToasts,'error');
  /* G196-R02 文案映射:舊訊息「孔邊不能當定位引用」→ 新訊息「目前不支援直接點孔邊——
     請從右欄「定位引用」選孔邊(at-face h<i>e<j>)」。改文案的理由:舊句暗示公理禁止孔邊
     當定位引用,但 I13 明文允許 at-face h<i>e<j>(表單路徑一直在);只是快捷點選
     尚未實作孔邊。斷言同步更新為新訊息的關鍵子句。 */
  check('P48-6d 點孔邊 → toast 說明快捷不支援並指路右欄、無 timber/place 指令送出、世界 dump 逐字不變、零角材',
    after6.toast.includes('孔邊') && after6.toast.includes('定位引用') && after6.sent.length === 0 &&
    after6.dump === dumpBefore6 && after6.bridgeTimbers === 0 && after6.feTimbers === 0,
    { toast: after6.toast, sent: after6.sent, bridgeTimbers: after6.bridgeTimbers });

  console.log('=== P49. 點線不暗改法線厚度方向(G196-R02 驗收) ===');
  /* 工單 G196-R02 固定驗收:F-SUPPORT 世界(兩支 boundary 沿 u @ e0/e2、guide 2 @ u=2000、
     無 primary)。表單 side × 點擊左右各組合:送出的 DSL 一律帶表單的 side,
     cross 足跡恆為 1987..2014(at-line 中線對齊,I13),改變的只有法線厚度方向
     (B 軸/Z 範圍)。每個組合重新 setup 同一基準,不靠 undo 殘值。
     幾何驗證用真實 bridge 的 references 回傳(origin/axes/A/B/length),
     不只驗表單欄位或支數。 */
  const F_SUPPORT = [
    'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'timber 1 27 33 role boundary',
    'place 1 on 1 at-face e0 +u +n',
    'timber 2 27 33 role boundary',
    'place 2 on 1 at-face e2 +u +n',
    'spec 測試中線 2000',
    'guide 2 1 v spec:測試中線'];
  const enterTimber49 = async (formSide) => {
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
      const t = document.getElementById('faceSnapToggle'); if (t) t.checked = false;
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
      window.__sent = [];
      if (!window.__rawApiRequest) window.__rawApiRequest = apiRequest;
      apiRequest = async c => { window.__sent.push(c); return window.__rawApiRequest(c); }; })()`);
    await eval_(`(()=>{ const s = document.getElementById('tbSide'); s.value = '${formSide}';
      s.dispatchEvent(new Event('change')); })()`);
    await eval_(`feSetTool('timber')`);
    await sleep(150);
    pt48 = await openFace48();
  };
  for (const formSide of ['+n', '-n']) {
    for (const px of [1997, 2003]) {
      const rs = await setupLinesG196(F_SUPPORT);
      check(`P49 setup(${formSide}@${px}) F-SUPPORT 全過`, Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
      await enterTimber49(formSide);
      await click(pt48(px, 1500).x, pt48(px, 1500).y);
      await sleep(400);
      const r = await eval_(`(async()=>{
        const refs = await apiRequest('references');
        const t = (refs.timbers || []).find(x => x.id === 3);
        apiRequest = window.__rawApiRequest;
        return { sent: (window.__sent || []).filter(c => /timber|place/.test(c)),
          formSide: document.getElementById('tbSide').value, g: t && t.geometry };
      })()`);
      const g = r.g || {};
      /* 八角點三維範圍:axes[0]=長度軸、axes[1]=截面寬 cross 軸、axes[2]=厚度 B 軸;
         原點 + 軸×尺寸推三個軸的極值,全部用真實 bridge 回傳,不依賴前端 helper。 */
      const xLo = g.origin && Math.min(g.origin[0], g.origin[0] + g.axes[1][0] * g.A);
      const xHi = g.origin && Math.max(g.origin[0], g.origin[0] + g.axes[1][0] * g.A);
      const vLo = g.origin && Math.min(g.origin[1], g.origin[1] + g.axes[0][1] * g.length);
      const vHi = g.origin && Math.max(g.origin[1], g.origin[1] + g.axes[0][1] * g.length);
      const zLo = g.origin && Math.min(g.origin[2], g.origin[2] + g.axes[2][2] * g.B);
      const zHi = g.origin && Math.max(g.origin[2], g.origin[2] + g.axes[2][2] * g.B);
      const placeLine = r.sent.map(c => c.replace(/^line /, '')).find(c => /^place /.test(c)) || '';
      const wantZ = formSide === '+n' ? [2500, 2533] : [2467, 2500];
      check(`P49 side=${formSide} 點u=${px} → place 帶 ${formSide}、cross u 1987..2014、長度 v 27..2973、Z ${wantZ[0]}..${wantZ[1]}`,
        /place \d+ on 1 at-line guide 2\s+\+v/.test(placeLine) &&
        placeLine.trim().endsWith(' ' + formSide) &&
        g.centerline === 2000 && g.A === 27 && g.length === 2946 &&
        xLo === 1987 && xHi === 2014 && vLo === 27 && vHi === 2973 &&
        zLo === wantZ[0] && zHi === wantZ[1] &&
        r.formSide === formSide,
        { placeLine, g, formSide: r.formSide });
    }
  }

  /* 牆面框架(origin=(3000,0,0), U=+Y, V=+Z, N=+X):同樣的左右點選,B=33 厚度範圍
     變的是 X(3000..3033 / 2967..3000),不是 Z——驗證「厚度方向跟著承載面法線走」,
     不是寫死成世界 Z。 */
  const F_WALL = [
    'surface 1 origin 3000 0 0 u +y v +z outline 0,0 4000,0 4000,3000 0,3000',
    'timber 1 27 33 role boundary',
    'place 1 on 1 at-face e0 +u +n',
    'timber 2 27 33 role boundary',
    'place 2 on 1 at-face e2 +u +n',
    'spec 測試中線 2000',
    'guide 2 1 v spec:測試中線'];
  for (const formSide of ['+n', '-n']) {
    const rs = await setupLinesG196(F_WALL);
    check(`P49 wall setup(${formSide}) 全過`, Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
    await enterTimber49(formSide);
    /* 牆面的面內 v 軸 = 世界 +z,但面內編輯器畫的是 uv 平面,點擊座標用 uv 不變 */
    await click(pt48(1997, 1500).x, pt48(1997, 1500).y);
    await sleep(400);
    const r = await eval_(`(async()=>{
      const refs = await apiRequest('references');
      const t = (refs.timbers || []).find(x => x.id === 3);
      return { g: t && t.geometry, formSide: document.getElementById('tbSide').value };
    })()`);
    const g = r.g || {};
    const xLo = g.origin && Math.min(g.origin[0], g.origin[0] + g.axes[2][0] * g.B);
    const xHi = g.origin && Math.max(g.origin[0], g.origin[0] + g.axes[2][0] * g.B);
    const wantX = formSide === '+n' ? [3000, 3033] : [2967, 3000];
    check(`P49 wall side=${formSide} 點線 → 厚度沿世界 X ${wantX[0]}..${wantX[1]}(非寫死 Z)`,
      g.length === 2946 && xLo === wantX[0] && xHi === wantX[1] && r.formSide === formSide,
      { g, formSide: r.formSide });
  }

  /* 外輪廓邊點擊同樣不覆寫 side:表單 -n,點 e1(u=4000 邊)內側——送出的 place 行
     一律帶 -n(不論角色/是否被核心接受——角色推導是 G196-R04 的範圍,這裡只驗 side)。 */
  {
    const rs = await setupLinesG196(F_SUPPORT);
    check('P49 e1 setup 全過', Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
    await enterTimber49('-n');
    await click(pt48(3997, 1500).x, pt48(3997, 1500).y);
    await sleep(400);
    const r = await eval_(`(async()=>{
      return { sent: (window.__sent || []).filter(c => /timber|place/.test(c)),
        formSide: document.getElementById('tbSide').value };
    })()`);
    const placeLine = r.sent.map(c => c.replace(/^line /, '')).find(c => /^place /.test(c)) || '';
    check('P49 表單 -n 點外邊 e1 → place 行帶 -n(點擊側不覆寫)',
      /place \d+ on 1 at-face e1\s+\+v -n/.test(placeLine) && r.formSide === '-n',
      { sent: r.sent, formSide: r.formSide });
  }

  /* 面內空白路徑不回歸:表單含負向長度軸 -v 與 -n 時,點空白照表單送出
     (點線邏輯不得重設表單值)。選 e3(u=0)避免占用。 */
  {
    const rs = await setupLinesG196(F_SUPPORT);
    check('P49 blank setup 全過', Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
    await enterTimber49('-n');
    await eval_(`(()=>{
      document.getElementById('tbAnchor').value = 'at-face e3';
      const d = document.getElementById('tbDir'); d.value = '-v'; d.dispatchEvent(new Event('change'));
      const s = document.getElementById('tbSide'); s.value = '-n'; s.dispatchEvent(new Event('change'));
    })()`);
    await click(pt48(1000, 1700).x, pt48(1000, 1700).y);   /* 面內空白:遠離 guide 2(u=2000±7)與所有邊 */
    await sleep(400);
    const r = await eval_(`(()=>{
      return { sent: (window.__sent || []).filter(c => /timber|place/.test(c)),
        formSide: document.getElementById('tbSide').value,
        formDir: document.getElementById('tbDir').value };
    })()`);
    const placeLine = r.sent.map(c => c.replace(/^line /, '')).find(c => /^place /.test(c)) || '';
    check('P49 空白點擊走表單:place 帶 at-face e3 -v -n,表單值不被重設',
      /place \d+ on 1 at-face e3\s+-v -n/.test(placeLine) &&
      r.formSide === '-n' && r.formDir === '-v',
      { sent: r.sent, formSide: r.formSide, formDir: r.formDir });
  }

  /* hover 不送任何修改世界指令:mouseMoved 過線,攔截到的 apiRequest 不含
     timber/place/boundary/spec/guide(寫入指令)。 */
  {
    const rs = await setupLinesG196(F_SUPPORT);
    await enterTimber49('+n');
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: pt48(1997, 1500).x, y: pt48(1997, 1500).y });
    await sleep(250);
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: pt48(2003, 1500).x, y: pt48(2003, 1500).y });
    await sleep(250);
    const r = await eval_(`(()=>{
      return { sent: (window.__sent || []).filter(c => /timber|place|boundary|guide|spec/.test(c)),
        hover: fe.timberHoverAnchor, side: document.getElementById('tbSide').value };
    })()`);
    check('P49 hover 過線不送寫入指令、不改表單 side(仍 +n)、timberHoverAnchor 只記線',
      r.sent.length === 0 && r.side === '+n' && r.hover === 'at-line guide 2', r);
    /* 還原攔截,避免影響後面的段落 */
    await eval_(`(()=>{ if (window.__rawApiRequest) apiRequest = window.__rawApiRequest; })()`);
  }

  console.log('=== P50. 吸附/格距/縮放不改變點線語意(G196-R03) ===');
  /* 每個情境重建 F-SUPPORT(同一基準,不靠 undo/殘值)。點擊命中以事件實際
     target(data-face-hit)為準;吸附(feSnap)只動 fePoint 的座標,不得改寫
     被命中的引用、方向、角色或表單 side。驗證「送出的 DSL 逐字一致」(timber id
     正規化成 N)與真實 bridge 幾何,不只數支數。 */
  const sentNorm = (arr) => (arr || []).map(c => c.replace(/^line /, '').replace(/^(timber|place) \d+/, '$1 N')).sort();
  for (const snap of [null, 10, 50, 100]) {
    for (const px of [1997, 2000, 2003]) {
      const rs = await setupLinesG196(F_SUPPORT);
      check(`P50 setup(snap=${snap ?? 'off'}@${px}) 全過`, Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
      await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
        fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
        const t = document.getElementById('faceSnapToggle'); if (t) t.checked = ${snap != null};
        const gs = document.getElementById('faceGridSizeSelect'); if (gs) gs.value = '${snap || 50}';
        await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
        window.__sent = [];
        if (!window.__rawApiRequest) window.__rawApiRequest = apiRequest;
        apiRequest = async c => { window.__sent.push(c); return window.__rawApiRequest(c); };
        const s = document.getElementById('tbSide'); s.value = '+n'; s.dispatchEvent(new Event('change'));
        feSetTool('timber'); })()`);
      await sleep(150);
      pt48 = await openFace48();
      await click(pt48(px, 1500).x, pt48(px, 1500).y);
      await sleep(350);
      const r = await eval_(`(async()=>{
        const refs = await apiRequest('references');
        const t = (refs.timbers || []).find(x => x.id === 3);
        apiRequest = window.__rawApiRequest;
        return { sent: (window.__sent || []).filter(c => /timber|place/.test(c)), g: t && t.geometry };
      })()`);
      const g = r.g || {};
      check(`P50 snap=${snap ?? 'off'} 點u=${px} → 引用/dir/role/side 不變、cross 1987..2014`,
        JSON.stringify(sentNorm(r.sent)) === JSON.stringify(sentNorm([
          'timber N 27 33 role primary', 'place N on 1 at-line guide 2  +v +n'])) &&
        g.centerline === 2000 && g.length === 2946,
        { sent: r.sent, g });
    }
  }

  /* snap=50、表單 -n、點正好在線上(u=2000):舊語意下 dot=0 會回 +n;
     修正後吸附/位置都不影響 side——仍送 -n。 */
  {
    const rs = await setupLinesG196(F_SUPPORT);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
      const t = document.getElementById('faceSnapToggle'); if (t) t.checked = true;
      const gs = document.getElementById('faceGridSizeSelect'); if (gs) gs.value = '50';
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
      window.__sent = [];
      if (!window.__rawApiRequest) window.__rawApiRequest = apiRequest;
      apiRequest = async c => { window.__sent.push(c); return window.__rawApiRequest(c); };
      const s = document.getElementById('tbSide'); s.value = '-n'; s.dispatchEvent(new Event('change'));
      feSetTool('timber'); })()`);
    await sleep(150);
    pt48 = await openFace48();
    await click(pt48(2000, 1500).x, pt48(2000, 1500).y);
    await sleep(350);
    const r = await eval_(`(async()=>{
      const refs = await apiRequest('references');
      const t = (refs.timbers || []).find(x => x.id === 3);
      apiRequest = window.__rawApiRequest;
      return { sent: (window.__sent || []).filter(c => /timber|place/.test(c)), g: t && t.geometry,
        formSide: document.getElementById('tbSide').value };
    })()`);
    const g = r.g || {};
    const zLo = g.origin && Math.min(g.origin[2], g.origin[2] + g.axes[2][2] * g.B);
    const zHi = g.origin && Math.max(g.origin[2], g.origin[2] + g.axes[2][2] * g.B);
    check('P50 snap=50 點在線上(u=2000)+表單 -n → 仍送 -n(Z 2467..2500),不回 +n',
      JSON.stringify(sentNorm(r.sent)) === JSON.stringify(sentNorm([
        'timber N 27 33 role primary', 'place N on 1 at-line guide 2  +v -n'])) &&
      zLo === 2467 && zHi === 2500 && r.formSide === '-n', { sent: r.sent, g });
  }

  /* 參考線不在格點上(u=2003):snap=50 時點 u=2000/2005 都吸附到 2000,
     但命中的 DOM 線仍是 guide 2(在 u=2003),送出的引用不能變成別的。 */
  {
    const rs = await setupLinesG196([
      'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
      'timber 1 27 33 role boundary', 'place 1 on 1 at-face e0 +u +n',
      'timber 2 27 33 role boundary', 'place 2 on 1 at-face e2 +u +n',
      'spec 測試中線 2003', 'guide 2 1 v spec:測試中線']);
    check('P50 off-grid guide setup 全過', Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
      const t = document.getElementById('faceSnapToggle'); if (t) t.checked = true;
      const gs = document.getElementById('faceGridSizeSelect'); if (gs) gs.value = '50';
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
      window.__sent = [];
      if (!window.__rawApiRequest) window.__rawApiRequest = apiRequest;
      apiRequest = async c => { window.__sent.push(c); return window.__rawApiRequest(c); };
      const s = document.getElementById('tbSide'); s.value = '+n'; s.dispatchEvent(new Event('change'));
      feSetTool('timber'); })()`);
    await sleep(150);
    pt48 = await openFace48();
    for (const px of [2000, 2005]) {
      await eval_(`(()=>{ window.__sent = []; })()`);
      await click(pt48(px, 1500).x, pt48(px, 1500).y);
      await sleep(350);
      const r = await eval_(`(async()=>{
        const refs = await apiRequest('references');
        const ts = (refs.timbers || []).map(t => t.id).sort();
        return { sent: (window.__sent || []).filter(c => /timber|place/.test(c)),
          last: refs.timbers && refs.timbers[refs.timbers.length - 1],
          n: ts.length };
      })()`);
      const ok = r.sent.some(c => /place \d+ on 1 at-line guide 2\s+\+v \+n/.test(c));
      check(`P50 off-grid guide@2003,snap=50,點u=${px} → 命中引用仍 guide 2`,
        ok, r.sent);
      if (ok) { await pressKey('z', 'KeyZ', 90, 2); await sleep(300);
        await eval_(`(async()=>{ await feLoadGuides(); })()`); }
    }
  }

  /* 非 zoom=1/pan=0:fit 視圖(1382×900)+ 任意 pan 下點同一條線,引用不變。
     螢幕座標由當前 transform(svgRect+pan+uv*zoom)算出,不是固定假設。 */
  {
    await send('Emulation.setDeviceMetricsOverride', { width: 1382, height: 900, deviceScaleFactor: 1, mobile: false });
    await sleep(200);
    const rs = await setupLinesG196(F_SUPPORT);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      feFit(loopsBBox(oc.bmap[1])); fe.panX += 40; fe.panY += 25; feApply();
      const t = document.getElementById('faceSnapToggle'); if (t) t.checked = true;
      const gs = document.getElementById('faceGridSizeSelect'); if (gs) gs.value = '50';
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
      window.__sent = [];
      if (!window.__rawApiRequest) window.__rawApiRequest = apiRequest;
      apiRequest = async c => { window.__sent.push(c); return window.__rawApiRequest(c); };
      feSetTool('timber'); })()`);
    await sleep(250);
    const cp = await eval_(`(()=>{
      const r = document.getElementById('faceEditorSvg').getBoundingClientRect();
      return { x: r.x + fe.panX + 1997 * fe.zoom, y: r.y + fe.panY + 1500 * fe.zoom,
        zoom: fe.zoom };
    })()`);
    await click(cp.x, cp.y);
    await sleep(400);
    const r = await eval_(`(async()=>{
      const refs = await apiRequest('references');
      const t = (refs.timbers || []).find(x => x.id === 3);
      apiRequest = window.__rawApiRequest;
      return { sent: (window.__sent || []).filter(c => /timber|place/.test(c)), g: t && t.geometry };
    })()`);
    check('P50 fit+zoom+pan(非100%)下點線 → 引用/dir/role/side 不變',
      JSON.stringify(sentNorm(r.sent)) === JSON.stringify(sentNorm([
        'timber N 27 33 role primary', 'place N on 1 at-line guide 2  +v +n'])) &&
      r.g && r.g.centerline === 2000,
      { sent: r.sent, zoom: cp.zoom });
    await send('Emulation.setDeviceMetricsOverride', { width: 5400, height: 3800, deviceScaleFactor: 1, mobile: false });
    await sleep(200);
  }

  /* 390px 視窗煙霧測試(模擬窄版,非實體手機/Safari):面板收合後點線仍走同一路徑。 */
  {
    await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 700, deviceScaleFactor: 1, mobile: true });
    await send('Emulation.setTouchEmulationEnabled', { enabled: true });
    await sleep(250);
    const rs = await setupLinesG196(F_SUPPORT);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      feFit(loopsBBox(oc.bmap[1]));
      const t = document.getElementById('faceSnapToggle'); if (t) t.checked = false;
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
      window.__sent = [];
      if (!window.__rawApiRequest) window.__rawApiRequest = apiRequest;
      apiRequest = async c => { window.__sent.push(c); return window.__rawApiRequest(c); };
      feSetTool('timber'); })()`);
    await sleep(250);
    const cp = await eval_(`(()=>{
      const r = document.getElementById('faceEditorSvg').getBoundingClientRect();
      return { x: r.x + fe.panX + 1997 * fe.zoom, y: r.y + fe.panY + 1500 * fe.zoom,
        zoom: fe.zoom, vw: innerWidth, vh: innerHeight };
    })()`);
    await click(cp.x, cp.y);
    await sleep(400);
    const r = await eval_(`(async()=>{
      const refs = await apiRequest('references');
      const t = (refs.timbers || []).find(x => x.id === 3);
      apiRequest = window.__rawApiRequest;
      return { sent: (window.__sent || []).filter(c => /timber|place/.test(c)),
        centerline: t && t.geometry && t.geometry.centerline };
    })()`);
    check('P50 390px 窄視窗模擬:點線放置 smoke(非實體裝置驗收)',
      r.sent.some(c => /place \d+ on 1 at-line guide 2\s+\+v/.test(c)) && r.centerline === 2000,
      { sent: r.sent, vw: cp.vw });
    await send('Emulation.setTouchEmulationEnabled', { enabled: false });
    await send('Emulation.setDeviceMetricsOverride', { width: 5400, height: 3800, deviceScaleFactor: 1, mobile: false });
    /* touch 模擬期間的 mousePressed/mouseReleased 可能被 Chrome 翻譯成觸控事件,
       mouse 側按鍵狀態殘留「已按下」——之後的 mousePressed 會被靜默丟棄、
       只有 release 產生 pointerup(本段曾因這個讓下一個測試的點擊整個消失)。
       補一個 release 確保按鍵狀態乾淨。 */
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: 10, y: 10, button: 'left', clickCount: 1 });
    await sleep(200);
  }

  /* 命中的線其引用已失效 → 報錯且不送,不靜默退回表單另一條引用。
     用合成狀態觸發:渲染後把 fe.guides 清空(DOM 命中層還在,但解析不到 guide 2),
     等效於「點擊瞬間引用已失效」的路徑。
     注意:本段自帶 viewport 還原——不依賴上一段(390px 窄視窗)的善後;
     行動裝置模擬下 elementFromPoint 看 layout viewport 仍命中,
     但 Input.dispatchMouseEvent 對超出 visual viewport 的座標會靜默丟棄。 */
  {
    await send('Emulation.setTouchEmulationEnabled', { enabled: false });
    const mres = await send('Emulation.setDeviceMetricsOverride', { width: 5400, height: 3800, deviceScaleFactor: 1, mobile: false });
    await sleep(250);
    const rs = await setupLinesG196(F_SUPPORT);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
      const t = document.getElementById('faceSnapToggle'); if (t) t.checked = false;
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
      window.__sent = [];
      if (!window.__rawApiRequest) window.__rawApiRequest = apiRequest;
      apiRequest = async c => { window.__sent.push(c); return window.__rawApiRequest(c); };
      feSetTool('timber');
    })()`);
    /* 探測:記錄點擊當下的真實狀態(busy/tool/hit)與 toast/feDown 呼叫,
       失敗時從 diag 直接看出是哪一層把點擊吞掉。 */
    const instOk = await eval_(`(()=>{ window.__dbg = { toasts: [], feDownCalls: [], downs: [], docDowns: [] };
      const _toast = toast;
      toast = m => { window.__dbg.toasts.push(String(m)); return _toast(m); };
      const _feDown = feDown;
      feDown = async (pt, ev) => {
        const el = ev && ev.target && ev.target.closest ? ev.target.closest('[data-face-hit]') : null;
        window.__dbg.feDownCalls.push({ hit: el ? el.dataset.faceHit : null,
          tool: fe.tool, busy: oc.busy, guides: fe.guides.length });
        return _feDown(pt, ev);
      };
      /* capture 階段先記一筆——區分「事件沒到 fevp」與「handler 早期 return 吞掉」。 */
      for (const evName of ['pointerdown', 'pointerup', 'pointermove', 'pointercancel'])
        document.addEventListener(evName, ev => {
          const t = ev.target;
          window.__dbg.docDowns.push({ ev: evName, tag: t && t.tagName, id: t && t.id || null,
            inFevp: fevp.contains(t), x: ev.clientX, y: ev.clientY });
        }, true);
      fevp.addEventListener('pointerdown', ev => {
        const t = ev.target;
        window.__dbg.downs.push({ btn: ev.button, busy: oc.busy, tool: fe.tool,
          ulCalib: !!fe.ulCalib,
          tag: t && t.tagName, id: t && t.id || null,
          overlay: !!(t && t.closest && t.closest('#feGuidePick, #feActionBar, #feOpPanel, #feCtxMenu')),
          hitEl: (t && t.closest && t.closest('[data-face-hit]') || {}).dataset ?
            t.closest('[data-face-hit]').dataset.faceHit : null });
      }, true);
      return 'installed';
    })()`);
    await sleep(150);
    await clearToasts48();
    await waitForFaceViewport();
    const pre = await eval_(`(()=>{
      /* 最後才製造失效引用:工具/提示版面與 ResizeObserver 均已穩定,
         不讓正常重繪先移除刻意保留的陳舊命中層。 */
      fe.guides = [];
      const m=$('faceEditorRoot').getScreenCTM(),p=new DOMPoint(2000,1500).matrixTransform(m);
      const elAt=document.elementFromPoint(p.x,p.y),hitEl=elAt?.closest('[data-face-hit]');
      return {focus:oc.edit?.bid,tool:fe.tool,guides:fe.guides.length,
        hitNow:hitEl?.dataset.faceHit||null,iw:innerWidth,cx:p.x,cy:p.y};})()`);
    check('P50 失效引用前置:進面1+timber 工具+fe.guides 已清+命中層仍含 g:2:v+視窗已還原',
      pre && pre.focus === 1 && pre.tool === 'timber' && pre.guides === 0 &&
      pre.hitNow === 'g:2:v' && pre.iw > 2300, { pre, mres: mres && (mres.error || 'ok') });
    /* 點擊前一刻再測一次 elementFromPoint——若此時頂層元素已不是命中線,
       代表 pre-eval 到 click 之間 DOM 被重繪或有浮層蓋上。 */
    const atClick = await eval_(`(()=>{ const el = document.elementFromPoint(${pre && typeof pre.cx === 'number' ? pre.cx : 0}, ${pre && typeof pre.cy === 'number' ? pre.cy : 0});
      const he = el && el.closest ? el.closest('[data-face-hit]') : null;
      return { tag: el && el.tagName, id: el && el.id || null,
        inFevp: el ? fevp.contains(el) : null, hit: he ? he.dataset.faceHit : null }; })()`);
    check('P50 真實點擊前仍命中失效參考線 g:2:v',atClick.hit==='g:2:v',atClick);
    let disp = null;
    const invalidReferenceToasts=await captureNewToasts(async()=>{if (pre && typeof pre.cx === 'number') {
      /* 防禦:先送一個 release 清掉可能殘留的按鍵狀態(上一段 touch 模擬留下的),
         否則下面的 press 會被 Chrome 當成「已按著」靜默丟棄。
         座標刻意避開 fevp(送到視窗左上角頂列)——pointerup 若在畫布內落地會走
         feUp() 無條件 drawFaceEditor(),把本段故意保留的陳舊命中層重繪掉。 */
      await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: 5, y: 5, button: "left", clickCount: 1 });
      const pd = await send("Input.dispatchMouseEvent", { type: "mousePressed", x: pre.cx, y: pre.cy, button: "left", clickCount: 1 });
      const pu = await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: pre.cx, y: pre.cy, button: "left", clickCount: 1 });
      disp = { pd: pd && (pd.error || pd.result), pu: pu && (pu.error || pu.result) };
    }
    await sleep(350);});
    const r = await eval_(`(async()=>{
      const refs = await apiRequest('references');
      apiRequest = window.__rawApiRequest;
      const dbg = window.__dbg || {};
      return { sent: (window.__sent || []).filter(c => /timber|place/.test(c)),
        toastCalls: dbg.toasts, feDownCalls: dbg.feDownCalls, downs: dbg.downs,
        docDowns: dbg.docDowns,
        n: (refs.timbers || []).length };
    })()`);r.toast=toastText(invalidReferenceToasts,'error');
    if (r && typeof r === 'object') { r.atClick = atClick; r.disp = disp; r.instOk = instOk; }
    check('P50 命中線引用失效 → 報錯、不送指令、不退回表單引用',
      (r.sent || []).length === 0 && (r.toast || '').includes('定位引用') && r.n === 2, r);
  }

  console.log('=== P51. D17 主支軸推導與自動角色(G196-R04) ===');
  /* 推導表:|primary|boundary|→軸|;全沿 v|全沿 u 或無|v;全沿 u|…|u;
     無|全沿 u|v;無|全沿 v|u;無|無|未定義;矛盾|不自選。
     custom/secondary 不定義軸;矛盾時不自動選、留診斷。
     (1) F-SUPPORT(兩支 boundary 沿 u、無 primary)→ 軸應為 v,
         點外邊 e1(沿 v)自動帶 primary,核心接受、cross 3973..4000、長度 27..2973。 */
  {
    const rs = await setupLinesG196(F_SUPPORT);
    check('P51-1 setup 全過', Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
      const t = document.getElementById('faceSnapToggle'); if (t) t.checked = false;
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
      window.__sent = [];
      if (!window.__rawApiRequest) window.__rawApiRequest = apiRequest;
      apiRequest = async c => { window.__sent.push(c); return window.__rawApiRequest(c); };
      feSetTool('timber'); })()`);
    await sleep(150);
    const axisNow = await eval_(`fePrimaryAxisInfo(oc.edit.bid)`);
    check('P51-1a F-SUPPORT 無 primary、兩支 boundary 沿 u → 主支軸推導 v(src=boundary)',
      axisNow && axisNow.axis === 'v' && axisNow.src === 'boundary' && !axisNow.conflict, axisNow);
    pt48 = await openFace48();
    await click(pt48(3997, 1500).x, pt48(3997, 1500).y);
    await sleep(400);
    const r = await eval_(`(async()=>{
      const refs = await apiRequest('references');
      const t = (refs.timbers || []).find(x => x.id === 3);
      apiRequest = window.__rawApiRequest;
      return { sent: (window.__sent || []).map(c => c.replace(/^line /, '')),
        formRole: document.getElementById('tbRole').value, g: t && t.geometry };
    })()`);
    const g = r.g || {};
    const xLo = g.origin && Math.min(g.origin[0], g.origin[0] + g.axes[1][0] * g.A);
    const xHi = g.origin && Math.max(g.origin[0], g.origin[0] + g.axes[1][0] * g.A);
    const vLo = g.origin && Math.min(g.origin[1], g.origin[1] + g.axes[0][1] * g.length);
    const vHi = g.origin && Math.max(g.origin[1], g.origin[1] + g.axes[0][1] * g.length);
    check('P51-1b 點 e1 → 自動角色 primary、核心接受、cross u 3973..4000、長度 v 27..2973',
      r.sent.some(c => /^timber \d+ 27 33 role primary$/.test(c)) &&
      r.sent.some(c => /^place \d+ on 1 at-face e1\s+\+v/.test(c)) &&
      r.formRole === 'primary' && xLo === 3973 && xHi === 4000 &&
      vLo === 27 && vHi === 2973, { sent: r.sent, g });
  }

  /* (2) 旋轉對應:boundary 在 e1/e3(沿 v)→ 主支軸 u;點 e0(沿 u,平行)→ primary。 */
  {
    const rs = await setupLinesG196([
      'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
      'timber 1 27 33 role boundary', 'place 1 on 1 at-face e1 +v +n',
      'timber 2 27 33 role boundary', 'place 2 on 1 at-face e3 +v +n',
      'spec 測試中線 2000', 'guide 2 1 u spec:測試中線']);
    check('P51-2 setup 全過(垂直 boundary 於 e1/e3)', Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
      const t = document.getElementById('faceSnapToggle'); if (t) t.checked = false;
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
      window.__sent = [];
      if (!window.__rawApiRequest) window.__rawApiRequest = apiRequest;
      apiRequest = async c => { window.__sent.push(c); return window.__rawApiRequest(c); };
      feSetTool('timber'); })()`);
    await sleep(150);
    const axisNow = await eval_(`fePrimaryAxisInfo(oc.edit.bid)`);
    check('P51-2a boundary 沿 v → 主支軸推導 u', axisNow && axisNow.axis === 'u' && axisNow.src === 'boundary', axisNow);
    pt48 = await openFace48();
    await click(pt48(2000, 3).x, pt48(2000, 3).y);   /* e0 頂邊 v=0,沿 u 跑 */
    await sleep(400);
    const r = await eval_(`(async()=>{
      const refs = await apiRequest('references');
      const t = (refs.timbers || []).find(x => x.id === 3);
      apiRequest = window.__rawApiRequest;
      return { sent: (window.__sent || []).map(c => c.replace(/^line /, '')),
        role: t && t.role, g: t && t.geometry };
    })()`);
    /* 兩支 boundary 在 e1/e3(u=0/4000)→ 主支在 u 向跨它們內側:u 27..3973、長度 3946 */
    const g51 = r.g || {};
    const uLo = g51.origin && Math.min(g51.origin[0], g51.origin[0] + g51.axes[0][0] * g51.length);
    const uHi = g51.origin && Math.max(g51.origin[0], g51.origin[0] + g51.axes[0][0] * g51.length);
    check('P51-2b 點 e0(平行主支軸 u)→ 角色 primary、核心接受、跨 u 27..3973(長度 3946)',
      r.sent.some(c => /^timber \d+ 27 33 role primary$/.test(c)) &&
      r.role === 'primary' && g51.length === 3946 && uLo === 27 && uHi === 3973,
      { sent: r.sent, g: r.g });
  }

  /* (3) 空面(無角材)→ 軸未定義:點外邊給 boundary、點參考線給 primary(首支規則);
         只有 custom 角材不定義軸。 */
  {
    const infoEmpty = await eval_(`(()=>{ const save = fe.timbers; fe.timbers = [];
      const r = fePrimaryAxisInfo(1); fe.timbers = save; return r; })()`);
    check('P51-3a 空面 → 主支軸未定義(非矛盾)', infoEmpty && infoEmpty.axis === null && !infoEmpty.conflict, infoEmpty);
    const infoCustom = await eval_(`(()=>{ const save = fe.timbers; fe.timbers = [{id:9,role:'custom',dir:'+u',A:27,B:33,side:'+n',u:0,v:0}];
      const r = fePrimaryAxisInfo(1); fe.timbers = save; return r; })()`);
    check('P51-3b 只有 custom → 主支軸仍未定義(D15:custom 不定義軸)',
      infoCustom && infoCustom.axis === null && !infoCustom.conflict, infoCustom);
    /* 空面點參考線 → 首支規則給 primary;點外邊 → boundary */
    const rs = await setupLinesG196([
      'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
      'spec 測試中線 2000', 'guide 2 1 v spec:測試中線']);
    check('P51-3c 空面 setup 全過', Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
      const t = document.getElementById('faceSnapToggle'); if (t) t.checked = false;
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
      window.__sent = [];
      if (!window.__rawApiRequest) window.__rawApiRequest = apiRequest;
      apiRequest = async c => { window.__sent.push(c); return window.__rawApiRequest(c); };
      feSetTool('timber'); })()`);
    await sleep(150);
    pt48 = await openFace48();
    await click(pt48(2000, 1500).x, pt48(2000, 1500).y);   /* guide 線上 */
    await sleep(350);
    const r = await eval_(`(()=>{ const s = (window.__sent || []).map(c => c.replace(/^line /, ''));
      apiRequest = window.__rawApiRequest; return { sent: s }; })()`);
    check('P51-3d 空面點參考線 → 首支規則角色 primary',
      r.sent.some(c => /^timber \d+ 27 33 role primary$/.test(c)), r.sent);
  }

  /* (4) 矛盾 → 不自選:合成 fe.timbers(primary 沿 u + boundary 沿 u,
     D17 下不可能出現在合法世界,這裡驗 helper 的診斷分支)。 */
  {
    const r = await eval_(`(()=>{ const save = fe.timbers;
      fe.timbers = [{id:1,role:'primary',dir:'+u',A:27,B:33,side:'+n',u:0,v:0},
                    {id:2,role:'boundary',dir:'+u',A:27,B:33,side:'+n',u:0,v:0}];
      const info = fePrimaryAxisInfo(1);
      const role = feTimberRoleForClick(1, 'line', 'v');
      fe.timbers = save; return { info, role }; })()`);
    check('P51-4 推導矛盾 → conflict 標記、feTimberRoleForClick 不自選(回 null)',
      r.info && r.info.conflict === true && r.role === null, r);
  }

  /* (5) 下拉與自動角色同源:主支軸 v、方向 +v(平行)→ boundary/secondary disabled、
     primary/custom 可選(D15:custom 不被方向一刀切禁用)。 */
  {
    const rs = await setupLinesG196(F_SUPPORT);
    check('P51-5 setup 全過', Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
      const d = document.getElementById('tbDir'); d.value = '+v'; d.dispatchEvent(new Event('change')); })()`);
    await sleep(150);
    const opts = await eval_(`(()=>{ const o = [...document.getElementById('tbRole').options];
      return Object.fromEntries(o.map(x => [x.value, x.disabled])); })()`);
    check('P51-5 方向平行主支軸 v → boundary/secondary 停用、primary 與 custom 可選(D15)',
      opts.primary === false && opts.custom === false &&
      opts.boundary === true && opts.secondary === true, opts);
  }

  console.log('=== P52. 預示帶橫向幾何符合 at-line/at-face 語意(G196-R05) ===');
  /* 預示帶(.fe-anchor-band)的 cross 範圍用 feAnchorCrossRange 直接算,再與
     真實放置後的核心 footprint 對照——兩邊是不同實作(前端示意 vs 引擎求解),
     交叉驗證不是共用同一個 helper 當裁判。 */
  {
    const rs = await setupLinesG196(F_SUPPORT);
    check('P52 setup 全過', Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
      const t = document.getElementById('faceSnapToggle'); if (t) t.checked = false;
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
      feSetTool('timber'); })()`);
    await sleep(150);
    /* at-line u=2000, A=27 → [1987,2014];A=28 → [1986,2014](I13 多的 1mm 在 +cross) */
    const c27 = await eval_(`feAnchorCrossRange(oc.edit.bid, 'at-line guide 2', 27)`);
    const c28 = await eval_(`feAnchorCrossRange(oc.edit.bid, 'at-line guide 2', 28)`);
    check('P52-1 at-line 置中:A27 → u 1987..2014,A28 → 1986..2014',
      c27 && c27.constAxis === 'u' && c27.lo === 1987 && c27.hi === 2014 &&
      c28 && c28.lo === 1986 && c28.hi === 2014, { c27, c28 });
    /* at-face 四邊 × 兩軸:e1(u=4000,材料 -u)→ [3973,4000];e3(u=0,+u)→ [0,27];
       e0(v=0,材料 +v)→ [0,27];e2(v=3000,-v)→ [2973,3000] */
    const cE1 = await eval_(`feAnchorCrossRange(oc.edit.bid, 'at-face e1', 27)`);
    const cE3 = await eval_(`feAnchorCrossRange(oc.edit.bid, 'at-face e3', 27)`);
    const cE0 = await eval_(`feAnchorCrossRange(oc.edit.bid, 'at-face e0', 27)`);
    const cE2 = await eval_(`feAnchorCrossRange(oc.edit.bid, 'at-face e2', 27)`);
    check('P52-2 at-face 貼材料側:e1 3973..4000、e3 0..27、e0 v0..27、e2 v2973..3000',
      cE1 && cE1.constAxis === 'u' && cE1.lo === 3973 && cE1.hi === 4000 &&
      cE3 && cE3.lo === 0 && cE3.hi === 27 &&
      cE0 && cE0.constAxis === 'v' && cE0.lo === 0 && cE0.hi === 27 &&
      cE2 && cE2.lo === 2973 && cE2.hi === 3000, { cE1, cE3, cE0, cE2 });
    /* ±n 與負向長度軸不影響 cross 帶:同 anchor 只由錨法決定。
       G196-R06-A:不再用 check(...,true) 帶過——下面是真實 UI 行為矩陣:
       兩軸場景 × 兩種引用 × A{27,28} × dir{±} × side{±n} = 32 情境。
       每情境獨立重建場景(setup 失敗即拋出)、啟用角材工具後設表單
       (anchor/A/B/dir/side/role=primary,走既有 change/input 事件)、
       滑鼠移到已知空白點確認 fe.timberHoverAnchor===null、讀 DOM 帶的
       橫向範圍/裁切/標籤(預示前後 dump 不得改變)、再點面內空白走表單
       路徑放置——負向 dir 用表單+空白確認,不用點線快捷(快捷既有規則
       固定選正向長度軸,P49/P50 已驗,不為測試改壞)。最後驗送出 DSL 與
       核心 origin+axes×length/A/B 八角點三軸範圍。 */
    const SC53 = [
      { tag: 'V(長度軸v)', lines: [
          'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
          'timber 1 27 33 role boundary', 'place 1 on 1 at-face e0 +u +n',
          'timber 2 27 33 role boundary', 'place 2 on 1 at-face e2 +u +n',
          'spec 測試中線 2000', 'guide 2 1 v spec:測試中線'],
        blank: [1000, 1500], dirs: ['+v', '-v'], lenAxis: 'v', lenExp: [27, 2973],
        refs: [
          { anchor: 'at-line guide 2', axis: 'u', exp: { 27: [1987, 2014], 28: [1986, 2014] } },
          { anchor: 'at-face e1', axis: 'u', exp: { 27: [3973, 4000], 28: [3972, 4000] } }] },
      { tag: 'H(長度軸u)', lines: [
          'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
          'timber 1 27 33 role boundary', 'place 1 on 1 at-face e1 +v +n',
          'timber 2 27 33 role boundary', 'place 2 on 1 at-face e3 +v +n',
          'spec 測試中線 2000', 'guide 2 1 u spec:測試中線'],
        blank: [2000, 1000], dirs: ['+u', '-u'], lenAxis: 'u', lenExp: [27, 3973],
        refs: [
          { anchor: 'at-line guide 2', axis: 'v', exp: { 27: [1987, 2014], 28: [1986, 2014] } },
          { anchor: 'at-face e2', axis: 'v', exp: { 27: [2973, 3000], 28: [2972, 3000] } }] },
    ];
    await send('Emulation.setDeviceMetricsOverride', { width: 5400, height: 3800, deviceScaleFactor: 1, mobile: false });
    for (const sc of SC53) for (const ref of sc.refs) for (const A of [27, 28])
      for (const dir of sc.dirs) for (const side of ['+n', '-n']) {
        const tag = `P52-3 ${sc.tag} ${ref.anchor} A${A} ${dir}${side}`;
        const rs = await setupLinesG196(sc.lines);
        if (!(Array.isArray(rs) && rs.every(r => r.ok && !r.preview)))
          throw new Error(tag + ' setup 失敗: ' + JSON.stringify(rs));
        await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
          fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply();
          const t = document.getElementById('faceSnapToggle'); if (t) t.checked = false;
          await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
          window.__sent = [];
          if (!window.__rawApiRequest) window.__rawApiRequest = apiRequest;
          apiRequest = async c => { window.__sent.push(c); return window.__rawApiRequest(c); };
          feSetTool('timber');
          const a = document.getElementById('tbAnchor');
          a.value = ${JSON.stringify(ref.anchor)}; a.dispatchEvent(new Event('change'));
          const av = document.getElementById('tbA'); av.value = '${A}'; av.dispatchEvent(new Event('input'));
          const bv = document.getElementById('tbB'); bv.value = '33'; bv.dispatchEvent(new Event('input'));
          const d = document.getElementById('tbDir'); d.value = '${dir}'; d.dispatchEvent(new Event('change'));
          const s = document.getElementById('tbSide'); s.value = '${side}'; s.dispatchEvent(new Event('change'));
          const ro = document.getElementById('tbRole'); ro.value = 'primary'; ro.dispatchEvent(new Event('change')); })()`);
        const dumpBefore = (await eval_(`apiRequest('dump')`)).text;
        /* 已知空白點:滑鼠移過去 → hoverAnchor 應回到 null(預示回到表單值) */
        const bp = await eval_(`(()=>{ const r = document.getElementById('faceEditorSvg').getBoundingClientRect();
          return { x: r.x + fe.panX + ${sc.blank[0]} * fe.zoom, y: r.y + fe.panY + ${sc.blank[1]} * fe.zoom }; })()`);
        await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: bp.x, y: bp.y, button: 'none' });
        await sleep(200);
        const band = await eval_(`(()=>{ const b = document.querySelector('#faceEditorRoot .fe-anchor-band');
          const g = b && b.parentElement;
          const lb = document.querySelector('#faceEditorRoot .fe-anchor-band-label');
          return b ? { x: +b.getAttribute('x'), y: +b.getAttribute('y'),
            w: +b.getAttribute('width'), h: +b.getAttribute('height'),
            clip: g && g.getAttribute('clip-path'),
            label: lb && lb.textContent,
            hoverNull: fe.timberHoverAnchor === null } : { hoverNull: fe.timberHoverAnchor === null }; })()`);
        const dumpAfter = (await eval_(`apiRequest('dump')`)).text;
        const [expLo, expHi] = ref.exp[A];
        const bandLo = band && (ref.axis === 'u' ? band.x : band.y);
        const bandHi = band && bandLo + (ref.axis === 'u' ? band.w : band.h);
        const bandOk = band && band.hoverNull === true && bandLo === expLo && bandHi === expHi &&
          band.clip === 'url(#face-material-clip)' && band.label === '橫向定位示意' &&
          dumpBefore === dumpAfter;
        /* 面內空白確認(表單路徑,保留負向 dir 與 ±n) */
        await click(bp.x, bp.y);
        await sleep(400);
        const placed = await eval_(`(async()=>{ const refs = await apiRequest('references');
          const t = (refs.timbers || []).find(x => x.id === 3);
          return { sent: (window.__sent || []).filter(c => /timber|place/.test(c)),
            g: t && t.geometry, n: (refs.timbers || []).length }; })()`);
        let rng = null;
        const g = placed && placed.g;
        if (g) {
          const pts = [];
          for (const l of [0, g.length]) for (const a2 of [0, g.A]) for (const b2 of [0, g.B])
            pts.push([0, 1, 2].map(i => g.origin[i] + g.axes[0][i] * l + g.axes[1][i] * a2 + g.axes[2][i] * b2));
          rng = [0, 1, 2].map(i => [Math.min(...pts.map(p => p[i])), Math.max(...pts.map(p => p[i]))]);
        }
        const crossI = ref.axis === 'u' ? 0 : 1, lenI = sc.lenAxis === 'v' ? 1 : 0;
        const zExp = side === '+n' ? [2500, 2533] : [2467, 2500];
        const dirEsc = dir.replace('+', '\\+'), sideEsc = side.replace('+', '\\+');
        const anchorEsc = ref.anchor.replace(/ /g, '\\s+');
        const dslOk = placed && placed.n === 3 &&
          placed.sent.some(c => new RegExp(`timber \\d+ ${A} 33 role primary`).test(c)) &&
          placed.sent.some(c => new RegExp(`place \\d+ on 1 ${anchorEsc}\\s+${dirEsc} ${sideEsc}`).test(c));
        const geoOk = rng &&
          rng[crossI][0] === expLo && rng[crossI][1] === expHi &&
          rng[lenI][0] === sc.lenExp[0] && rng[lenI][1] === sc.lenExp[1] &&
          rng[2][0] === zExp[0] && rng[2][1] === zExp[1];
        check(tag, bandOk && dslOk && geoOk, { band, expCross: [expLo, expHi], sent: placed && placed.sent, rng, expLen: sc.lenExp, expZ: zExp });
      }
    await eval_(`(()=>{ if (window.__rawApiRequest) apiRequest = window.__rawApiRequest; })()`);
    /* P52-3 矩陣把世界留在最後一個情境;P52-4/5 沿用本區塊開頭的假設
       (F_SUPPORT 場景 + 角材工具 + 表單 v 向/+n/A27)——在這裡還原,
       不讓矩陣的殘留狀態污染後面的既有檢查。 */
    {
      const rs53r = await setupLinesG196(F_SUPPORT);
      if (!(Array.isArray(rs53r) && rs53r.every(r => r.ok && !r.preview)))
        throw new Error('P52-3 收尾回 F_SUPPORT 失敗: ' + JSON.stringify(rs53r));
      await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
        await feLoadGuides(); renderFaceInspector(); fiShowTab('timber');
        feSetTool('timber');
        const d = document.getElementById('tbDir'); d.value = '+v'; d.dispatchEvent(new Event('change'));
        const s = document.getElementById('tbSide'); s.value = '+n'; s.dispatchEvent(new Event('change'));
        const av = document.getElementById('tbA'); av.value = '27'; av.dispatchEvent(new Event('input')); })()`);
    }
    /* 畫出的 DOM 帶 = 計算範圍,且套 face-material-clip */
    await eval_(`(()=>{ const a = document.getElementById('tbAnchor');
      a.value = 'at-line guide 2'; a.dispatchEvent(new Event('change'));
      const av = document.getElementById('tbA'); av.value = '27'; av.dispatchEvent(new Event('change')); })()`);
    await sleep(200);
    const dom = await eval_(`(()=>{ const b = document.querySelector('#faceEditorRoot .fe-anchor-band');
      return b ? { x: +b.getAttribute('x'), w: +b.getAttribute('width'),
        clip: b.parentElement.getAttribute('clip-path') } : null; })()`);
    check('P52-4 DOM 帶畫 u 1987..2014 且套材料區裁切',
      dom && dom.x === 1987 && dom.w === 27 && dom.clip === 'url(#face-material-clip)', dom);
    /* 真實放置後核心 footprint 的 cross 範圍 = 帶的範圍 */
    pt48 = await openFace48();
    await click(pt48(2000, 1500).x, pt48(2000, 1500).y);
    await sleep(400);
    const g = await eval_(`(async()=>{ const refs = await apiRequest('references');
      const t = (refs.timbers || []).find(x => x.id === 3); return t && t.geometry; })()`);
    const fxLo = g && Math.min(g.origin[0], g.origin[0] + g.axes[1][0] * g.A);
    const fxHi = g && Math.max(g.origin[0], g.origin[0] + g.axes[1][0] * g.A);
    check('P52-5 真實放置的 cross 足跡(核心) = 預示帶範圍 1987..2014',
      fxLo === 1987 && fxHi === 2014, { g });
  }

  /* L 形:凹入垂直邊 u=2500(v 1500..3000)的材料在較小 u 側 → 帶 [2473,2500];
     用實際幾何找邊,不固定 e<i> 索引(環序可能不同)。 */
  {
    const rs = await setupLinesG196([
      'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,1500 2500,1500 2500,3000 0,3000']);
    check('P52 L形 setup 全過', Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber'); })()`);
    const cr = await eval_(`(()=>{
      const vs = oc.bmap[1][0].verts;
      let idx = -1;
      for (let i = 0; i < vs.length; ++i) {
        const a = vs[i], b = vs[(i + 1) % vs.length];
        if (a[0] === 2500 && b[0] === 2500 &&
            Math.min(a[1], b[1]) === 1500 && Math.max(a[1], b[1]) === 3000) { idx = i; break; }
      }
      return idx < 0 ? null : feAnchorCrossRange(1, 'at-face e' + idx, 27);
    })()`);
    check('P52-6 L 形凹邊(u=2500,v 1500..3000)→ 材料側較小 u,帶 2473..2500',
      cr && cr.constAxis === 'u' && cr.lo === 2473 && cr.hi === 2500, cr);
    /* 反環走向再驗一次(頂點順序反轉的同一形狀) */
    const rs2 = await setupLinesG196([
      'surface 1 origin 0 0 2500 u +x v +y outline 0,0 0,3000 2500,3000 2500,1500 4000,1500 4000,0']);
    check('P52 L形反環 setup 全過', Array.isArray(rs2) && rs2.every(r => r.ok && !r.preview), rs2);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      await feLoadGuides(); })()`);
    const cr2 = await eval_(`(()=>{
      const vs = oc.bmap[1][0].verts;
      let idx = -1;
      for (let i = 0; i < vs.length; ++i) {
        const a = vs[i], b = vs[(i + 1) % vs.length];
        if (a[0] === 2500 && b[0] === 2500 &&
            Math.min(a[1], b[1]) === 1500 && Math.max(a[1], b[1]) === 3000) { idx = i; break; }
      }
      return idx < 0 ? null : feAnchorCrossRange(1, 'at-face e' + idx, 27);
    })()`);
    check('P52-7 L 形反環走向 → 同一凹邊材料側仍為較小 u,帶 2473..2500',
      cr2 && cr2.lo === 2473 && cr2.hi === 2500, cr2);
  }

  /* 孔邊(F-HOLE):材料側 = 孔外側。孔 (1000,1000)~(2000,2000) 頂邊 v=1000
     → 材料在 v<1000 側 → 帶 v [973,1000];跨孔參考線的帶套 clip 不跨孔。 */
  {
    const rs = await setupLinesG196([
      'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000 hole 1000,1000 2000,1000 2000,2000 1000,2000']);
    check('P52 孔場景 setup 全過', Array.isArray(rs) && rs.every(r => r.ok && !r.preview), rs);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); await enterFocus('face', 1);
      await feLoadGuides(); renderFaceInspector(); fiShowTab('timber'); })()`);
    const crH = await eval_(`(()=>{
      /* 找孔環(loop 1)頂邊 v=1000 那條邊的引用式 */
      const vs = oc.bmap[1][1].verts;
      let idx = -1;
      for (let i = 0; i < vs.length; ++i) {
        const a = vs[i], b = vs[(i + 1) % vs.length];
        if (a[1] === 1000 && b[1] === 1000) { idx = i; break; }
      }
      return idx < 0 ? null : feAnchorCrossRange(1, 'at-face h0e' + idx, 27);
    })()`);
    check('P52-8 孔頂邊 v=1000 → 材料側在孔外(v<1000),帶 v 973..1000',
      crH && crH.constAxis === 'v' && crH.lo === 973 && crH.hi === 1000, crH);
  }
  }

  if (!process.env.GEOMETRY_REFERENCE_ONLY) { // GEO-197：四項流程修正，使用真实 UI 事件與可恢復的故障注入。
    console.log('=== P53. 連線錯誤、重新載入與重試 ===');
    const check = bodyCheck({detail:'empty',detailWhenPassing:true});
    const until = async expr => {
      for (let i = 0; i < 120; i++) { if (await eval_(expr) === true) return; await sleep(100); }
      throw Error('GEO-197 wait failed: ' + expr);
    };
    const ctl = async selector => {
      const r = await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
      await click(r.x, r.y); await sleep(150);
    };
    const key = async (key, code, windowsVirtualKeyCode) => {
      await send('Input.dispatchKeyEvent', { type:'keyDown', key, code, windowsVirtualKeyCode });
      await send('Input.dispatchKeyEvent', { type:'keyUp', key, code, windowsVirtualKeyCode });
      await sleep(150);
    };
    const facePoint = async (u, v) => {
      const p = await eval_(`(()=>{const r=$('faceEditorViewport').getBoundingClientRect();return {x:r.x+fe.panX+${u}*fe.zoom,y:r.y+fe.panY+${v}*fe.zoom}})()`);
      await click(p.x, p.y); await sleep(100);
    };
    const field = async (id, value) => eval_(`(()=>{const e=$('faceInspectorContent').querySelector('#'+${JSON.stringify(id)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    const scene = async lines => {
      const r = await eval_(`(async()=>{resetSceneFocus();await setView3(false);const out=[await api('reset')];for(const l of ${JSON.stringify(lines)})out.push(await api('line '+l));await renderObjects();return out.every(r=>r.ok&&!r.preview)})()`);
      if (r !== true) throw Error('GEO-197 setup failed: ' + JSON.stringify(r));
    };
    await send('Emulation.setDeviceMetricsOverride', {width:1400,height:1000,deviceScaleFactor:1,mobile:false});
    console.log('P53 setup isolated connection fixture');
    await scene(['boundary 1 outline 0,0 4000,0 4000,3000 0,3000']);
    const beforeConnection = await eval_(`api('dump').then(r=>r.text)`);
    const navigationMarker = require('crypto').randomUUID();
    const injected = await send('Page.addScriptToEvaluateOnNewDocument', { source: `
      window.__cdpExpectedNavigationMarker = ${JSON.stringify(navigationMarker)};
      window.__g197NativeFetch = window.fetch.bind(window);
      window.__g197Mode = '403'; window.__g197Commands = [];
      window.fetch = async (input, init) => {
        if (input === '/api') {
          const cmd = JSON.parse(init.body).cmd;
          window.__g197Commands.push(cmd);
          if (window.__g197Mode === '403') return new Response('<h1>Forbidden</h1>', {status:403});
          if (window.__g197Mode === 'malformed') return new Response('<html>unavailable</html>');
          if (window.__g197Mode === 'network') throw new TypeError('Failed to fetch');
          if (window.__g197Mode === 'bridge') return new Response(JSON.stringify({ok:false,error:'橋接器連線中斷，請重新啟動服務'}));
          if (window.__g197Mode === 'partial' && cmd === 'objects') return new Response(JSON.stringify({ok:true,faces:[],spaces:[]}));
          if (window.__g197Mode === 'partial' && cmd === 'surfaces') return new Response('<html>unavailable</html>');
        }
        return window.__g197NativeFetch(input, init);
      };` });
    console.log('P53 reload with expected test-project leave protection');
    await send('Page.reload');
    console.log('P53 wait for injected connection error');
    await waitForExpectedNavigation({evaluate:eval_, marker:navigationMarker, label:'P53 injected connection error',
      condition:`typeof connection !== 'undefined' && connection.phase === 'error'`});
    const failedStart = await eval_(`({message:$('connectionMessage').textContent,empty:$('emptyState').hidden,count:$('objectCountBadge').textContent,inert:$('app').inert})`);
    check('P53-1 初始 403 明示錯誤、未知數量、停用編輯', failedStart.message.includes('403') && failedStart.empty && failedStart.count === '—' && failedStart.inert, failedStart);
    const offlineRequests = await eval_(`__g197Commands.length`);
    await key('p','KeyP',80);
    check('P53-2 失敗時快捷鍵不送建立指令', await eval_(`__g197Commands.length`) === offlineRequests);
    await eval_(`__g197Mode='';__g197Commands=[]`);
    await ctl('#connectionRetry');
    await until(`connection.phase === 'ready'`);
    const recovered = await eval_(`({commands:__g197Commands.slice(),count:$('objectCountBadge').textContent,hidden:$('connectionNotice').hidden})`);
    check('P53-3 重試只讀取，不重送修改', recovered.commands.length > 0 && recovered.commands.every(c=>/^(dump|objects|surfaces|boundary|references|obstacles|render)(\s|$)/.test(c)) && recovered.count === '1' && recovered.hidden, recovered);
    check('P53-4 重試前後世界逐字相同', typeof beforeConnection === 'string' && await eval_(`api('dump').then(r=>r.text)`) === beforeConnection);
    const cached = await eval_(`JSON.stringify([oc.faces,oc.surfs,oc.bmap])`);
    await eval_(`__g197Mode='partial';renderObjects()`);
    await until(`connection.phase === 'error'`);
    check('P53-5 部分讀取失敗保留整份舊快取', await eval_(`JSON.stringify([oc.faces,oc.surfs,oc.bmap])`) === cached && await eval_(`$('connectionMessage').textContent.includes('最後讀取') && $('emptyState').hidden`));
    for (const mode of ['malformed','network','bridge']) {
      await eval_(`__g197Mode=${JSON.stringify(mode)}`);
      await ctl('#connectionRetry');
      await until(`connection.phase === 'error'`);
      check('P53-6 ' + mode + ' 留在可重試錯誤狀態', await eval_(`!$('connectionRetry').hidden && !$('connectionRetry').disabled && $('app').inert`));
    }
    await eval_(`__g197Mode=''`);
    await ctl('#connectionRetry'); await until(`connection.phase === 'ready'`);
    await send('Page.removeScriptToEvaluateOnNewDocument', {identifier:injected.result.identifier});
    await eval_(`window.fetch=__g197NativeFetch`);

    await scene([]);
    await ctl('#btnNewPoly'); await until(`oc.edit?.bid > 0 && fe.tool === 'redraw'`);
    const bid = await eval_(`oc.edit.bid`);
    const defaultShape = await eval_(`api('boundary '+oc.edit.bid).then(r=>JSON.stringify(r.loops))`);
    check('P54-1 開始就說明預設矩形、草稿與返回保留', await eval_(`$('faceDraftMessage').textContent.includes('預設矩形') && $('faceDraftMessage').textContent.includes('返回會保留此面') && !$('faceDraftNotice').hidden && $('faceDraftFinish').disabled`));
    const noticeLayout = await eval_(`(()=>{const a=$('faceDraftNotice').getBoundingClientRect(),b=$('faceEditorViewport').getBoundingClientRect();return a.bottom<=b.top+1})()`);
    check('P54-2 草稿操作列不遮蓋畫布', noticeLayout);
    for (const p of [[0,0],[3000,0],[3000,2000],[0,2000]]) await facePoint(...p);
    check('P54-3 畫草稿未改已建立面', await eval_(`api('boundary '+oc.edit.bid).then(r=>JSON.stringify(r.loops))`) === defaultShape && await eval_(`fe.draft.pts.length===4`));
    await ctl('#faceDraftCancel');
    check('P54-4 放棄只清草稿，按鈕不被算成落點', await eval_(`fe.draft.pts.length===0 && oc.edit.bid===${bid}`) && await eval_(`api('boundary '+oc.edit.bid).then(r=>JSON.stringify(r.loops))`) === defaultShape);
    for (const p of [[0,0],[3000,0],[3000,2000],[0,2000]]) await facePoint(...p);
    await ctl('#faceDraftFinish'); await until(`fe.tool==='select'`);
    check('P54-5 完成後才更新外環、收起草稿列', await eval_(`$('faceDraftNotice').hidden && loopsBBox(oc.bmap[${bid}]).join(',')==='0,0,3000,2000'`));
    await key('Escape','Escape',27);
    await ctl('#btnNewPoly'); await until(`fe.tool==='redraw' && oc.edit?.bid !== ${bid}`);
    await key('Escape','Escape',27);
    check('P54-6 未落點就返回，已建立的面仍保留', await eval_(`!oc.focus && oc.faces.length===2`));

    await eval_(`enterFocus('face',${bid})`);
    await ctl('[data-face-tool="timber"]');
    check('P55-1 游離面不啟動放材、不顯示預示，提供直接入口', await eval_(`fe.tool==='select' && fe.fiTab==='timber' && !!$('tbGoPlace') && !$('tbGoPlace').disabled && $('tbPlace').disabled && !document.querySelector('.fe-anchor-hi') && $('faceCanvasHint').textContent.includes('先放置')`));
    await ctl('#tbGoPlace');
    check('P55-2 一鍵到放置表單並聚焦', await eval_(`fe.fiTab==='prop' && document.activeElement.id==='placeOX'`));
    await field('placeOZ','2500'); await ctl('#faceInspectorContent #placeSubmit');
    await until(`!!feSid(${bid})`);
    await ctl('[data-face-tool="timber"]');
    check('P56-1 新放置面預填外邊 boundary，與點線相同', await eval_(`$('tbAnchor').value==='at-face e0' && $('tbDir').value==='+u' && $('tbRole').value==='boundary'`));
    await ctl('#tbPlace'); await facePoint(1500,1000); await until(`fe.timbers.length===1`);
    check('P56-2 沿用預填設定點面內成功放第一支邊界材', await eval_(`fe.timbers[0].role==='boundary' && connection.phase==='ready'`));

    await scene(['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000']);
    await eval_(`enterFocus('face',1)`); await ctl('[data-face-tool="timber"]');
    await field('tbAnchor','at-face e1');
    check('P56-3 換定位邊同步建議方向與角色', await eval_(`$('tbDir').value==='+v' && $('tbRole').value==='boundary'`));
    await field('tbRole','custom'); await field('tbPri','7'); await field('tbSide','-n'); await field('tbA','31');
    await field('tbAnchor','at-face e0'); await eval_(`renderFaceInspector()`);
    check('P56-4 手選 custom 與截面深度在換邊、重繪後保留', await eval_(`$('tbRole').value==='custom' && $('tbPri').value==='7' && $('tbSide').value==='-n' && $('tbA').value==='31'`));
    await ctl('#tbUseSuggestion');
    check('P56-5 套用建議只改方向角色', await eval_(`$('tbRole').value==='boundary' && $('tbSide').value==='-n' && $('tbA').value==='31'`));
    // Hold only the real native snapshot returned after a rejected or committed
    // transaction. Busy must cover that refresh, not merely the DSL response.
    const holdTimberSettlement = async mode => eval_(`(()=>{
      const nativeFetch=window.fetch;
      const g=window.__g197Settlement={mode:${JSON.stringify(mode)},commands:[],events:[],settled:false,held:false};
      const released=new Promise(resolve=>g.release=resolve);
      const observe=e=>{if(e.type==='pointerdown'||e.key==='Enter')g.events.push({type:e.type,key:e.key,trusted:e.isTrusted,id:e.target.id,hit:e.target.closest?.('[data-face-hit]')?.dataset.faceHit});};
      window.addEventListener('pointerdown',observe,true);window.addEventListener('keydown',observe,true);
      g.cleanup=()=>{g.release();window.fetch=nativeFetch;window.removeEventListener('pointerdown',observe,true);window.removeEventListener('keydown',observe,true);};
      window.fetch=async(input,init)=>{
        const cmd=input==='/api'?JSON.parse(init.body).cmd:null;if(cmd)g.commands.push(cmd);
        const response=await nativeFetch(input,init);if(!cmd)return response;
        const result=await response.clone().json();
        if(g.mode==='rejected'&&cmd.startsWith('line place ')&&!result.ok){g.settled=true;g.error=result.error;}
        if(g.mode==='committed'&&cmd==='line history-end'&&result.ok)g.settled=true;
        if(g.settled&&!g.held&&cmd==='source-inspect'){
          g.held=true;g.native=result;g.raw=JSON.stringify(['tbA','tbB','tbAnchor','tbSelector','tbDir','tbSide','tbRole','tbPri'].map(id=>[id,$(id)?.value]));
          g.requestsAtHold=g.commands.length;await released;
        }
        return response;
      };
    })()`);
    const settlementState = () => eval_(`(()=>{const g=__g197Settlement;return {busy:oc.busy,held:g.held,mode:g.mode,native:g.native,error:g.error,referenceRevision:fe.referenceRevision,fingerprint:fe.timberReferenceData?.sourceFingerprint??null};})()`);
    const attemptSettlementReentry = async () => {
      await facePoint(2000,0);
      await eval_(`$('tbPlace').focus()`);
      await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,text:'\r',unmodifiedText:'\r'});
      await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
      await sleep(150);
      return eval_(`(()=>{const g=__g197Settlement,raw=JSON.stringify(['tbA','tbB','tbAnchor','tbSelector','tbDir','tbSide','tbRole','tbPri'].map(id=>[id,$(id)?.value]));
        const writes=g.commands.slice(g.requestsAtHold).filter(c=>/^(newid(?:\\s|$)|line |drag |reset$|default$|undo$|redo$|loadfile |engineering-confirm |assembly-confirm )/.test(c));
        return {busy:oc.busy,unchanged:raw===g.raw,writes,pointer:g.events.some(e=>e.type==='pointerdown'&&e.trusted&&e.hit==='e:0:0'),enter:g.events.some(e=>e.type==='keydown'&&e.trusted&&e.key==='Enter'&&e.id==='tbPlace')};})()`);
    };
    await field('tbRole','primary');await holdTimberSettlement('rejected');
    try {
      await ctl('#tbPlace');await until(`__g197Settlement.held`);
      const held=await settlementState();
      check('P56-6a 真拒絕後來源重讀尚未完成時維持 busy',held.busy&&held.held&&held.native?.ok===true&&held.fingerprint===null&&held.error.includes('V_CUT_PRIORITY'),held);
      await facePoint(2000,1500);
      const reentry=await attemptSettlementReentry();
      check('P56-6b 拒絕後重讀期間真點線與 Enter 不再入或改輸入',reentry.busy&&reentry.unchanged&&reentry.writes.length===0&&reentry.pointer&&reentry.enter,reentry);
      await eval_(`__g197Settlement.release()`);await until(`!oc.busy`);
      check('P56-6c 解除 busy 前完成同一原生 revision 與 fingerprint 重讀',await eval_(`fe.referenceRevision===__g197Settlement.native.revision&&fe.timberReferenceData?.sourceFingerprint===__g197Settlement.native.sourceFingerprint`));
      check('P56-6 不合法手選仍交核心拒絕，不當作断線',await eval_(`fe.timbers.length===0 && $('tbRole').classList.contains('invalid') && connection.phase==='ready'`));
    } finally {await eval_(`__g197Settlement.cleanup()`);}
    await holdTimberSettlement('committed');
    try {
      await facePoint(2000,0);await until(`__g197Settlement.held`);
      const held=await settlementState();
      check('P56-7a 真成功後來源重讀尚未完成時也維持 busy',held.busy&&held.held&&held.native?.ok===true&&held.fingerprint===null,held);
      const reentry=await attemptSettlementReentry();
      check('P56-7b 成功後重讀期間真點線與 Enter 不重複放置或改輸入',reentry.busy&&reentry.unchanged&&reentry.writes.length===0&&reentry.pointer&&reentry.enter,reentry);
      await eval_(`__g197Settlement.release()`);await until(`!oc.busy&&fe.timbers.length===1`);
      check('P56-7 改用點線成功後移除角色錯誤標示',await eval_(`$('tbRole').value==='boundary' && !$('tbRole').classList.contains('invalid')`));
    } finally {await eval_(`__g197Settlement.cleanup()`);}
  }

  { // GEO-198: portable references, browser PDF rendering and context isolation.
    console.log('=== P57–P61. PDF 與專案保存(GEO-198) ===');
    const referenceExceptions = excN;
    const check=bodyCheck();
    const until=async expr=>{for(let i=0;i<150;i++){if(await eval_(expr)===true)return;await sleep(100);}throw Error('G198 wait: '+expr);};
    const ctl=async selector=>{
      const p=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
      await click(p.x,p.y);await sleep(100);
    };
    const field=async(id,value)=>eval_(`(()=>{const e=$(${JSON.stringify(id)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
    await eval_(`(async()=>{resetSceneFocus();await api('reset');await api('line boundary 1 outline 0,0 2000,0 2000,1000 0,1000');await renderObjects();await enterFocus('face',1);fiShowTab('underlay');
      const c=document.createElement('canvas');c.width=200;c.height=100;c.getContext('2d').fillRect(20,20,160,60);feUnderlaySet(1,{src:c.toDataURL(),imgW:200,imgH:100});})()`);
    check('P57-1 圖片未校準且原有手動面可編輯',await eval_(`$('refCalibrationStatus').textContent.includes('未校準') && oc.edit.bid===1`));
    await ctl('#ulCalibStart');await eval_(`feUnderlayCalibPoint([20,20]);feUnderlayCalibPoint([180,20])`);
    await field('ulCalibUnit','cm');await field('ulCalibDist','160');await ctl('#ulCalibApply');
    check('P57-2 cm 校準保存原值及整數 mm',await eval_(`(()=>{const p=ReferenceWorkspace.active(1);return p.mmPerPx===10&&p.calibration.distanceMm===1600&&p.calibration.inputUnit==='cm'&&p.reviewRequired;})()`));
    await ctl('#refRecordDetails summary');
    await field('refRecordLabel','天花完成高度');await field('refRecordValue','2650');
    await field('refRecordLocation','主區域');await field('refRecordDatum','FFL');await ctl('#refRecordAdd');
    await field('refRecordLabel','RC樑底');await field('refRecordValue','');
    await field('refRecordLocation','待確認');await ctl('#refRecordAdd');
    check('P57-2b 表單保存高度、基準及未知值，並顯示來源頁',await eval_(`(()=>{const r=ReferenceWorkspace.active(1).records;return r.length===2&&r[0].value===2650&&r[0].unit==='mm'&&r[0].datum==='FFL'&&r[1].value===null&&[...document.querySelectorAll('.ref-record small')].every(e=>e.textContent==='第 1 頁');})()`));
    await field('refRecordLabel','');await ctl('#refRecordAdd');
    check('P57-2c 缺少項目名稱不新增紀錄',await eval_(`ReferenceWorkspace.active(1).records.length===2`));
    await field('refRecordLabel','待移除測試');await ctl('#refRecordAdd');
    const r57hit=await eval_(`(()=>{const e=document.querySelector('.ref-record:last-of-type [data-ref-remove-record]');e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect(),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {rect:[r.x,r.y,r.width,r.height],hit:h?.outerHTML?.slice(0,130),target:e.outerHTML?.slice(0,130)};})()`);
    await ctl('.ref-record:last-of-type [data-ref-remove-record]');
    const r57 = await eval_(`ReferenceWorkspace.active(1).records.map(r=>r.label)`);
    check('P57-2d 移除紀錄保留其餘來源資訊',r57.length===2&&r57[1]==='RC樑底',{r57,r57hit});
    check('P57-3 直角旋轉與反向換算精度',await eval_(`(()=>{const p=ReferenceWorkspace.active(1);return [0,90,180,270].every(rot=>{p.rot=rot;const a=feUlImgToMm(p,42.5,61.25),b=feUlMmToImg(p,...a);return Math.abs(b[0]-42.5)<1e-8&&Math.abs(b[1]-61.25)<1e-8;});})()`));
    await eval_(`(async()=>{window.g198Saved=await ReferenceWorkspace.exportBytes();window.g198Before=JSON.stringify((await ReferenceWorkspace.manifest()).faces);window.g198Dump=(await api('dump')).text;})()`);
    check('P57-4 .scene 不混入來源／待補紀錄',await eval_(`!g198Dump.includes('sourceId')&&!g198Dump.includes('RC樑底')`));
    await eval_(`(async()=>{await api('line reset');await renderObjects();await api('line boundary 1 outline 0,0 1000,0 1000,1000 0,1000');await renderObjects();})()`);
    check('P58-1 新場景同號面不繼承底圖',await eval_(`!ReferenceWorkspace.active(1)&&!oc.underlays[1]`));
    await eval_(`(async()=>{await doUndoRedo('undo');await doUndoRedo('undo');})()`);
    check('P58-2 復原回舊場景恢復来源',await eval_(`ReferenceWorkspace.active(1)?.calibration.distanceMm===1600&&!!oc.underlays[1]`));
    await eval_(`(async()=>{await doUndoRedo('redo');await doUndoRedo('redo');await ReferenceWorkspace.importBytes(g198Saved);})()`);
    check('P58-3 專案重開恢复來源、校準與待補值',await eval_(`(async()=>JSON.stringify((await ReferenceWorkspace.manifest()).faces)===g198Before&&(await api('dump')).text===g198Dump)()`));
    check('P58-4 損壞專案不替換目前世界',await eval_(`(async()=>{const id=ReferenceWorkspace.context().id;try{await ReferenceWorkspace.importBytes(new Uint8Array([1,2,3]));return false;}catch(e){return id===ReferenceWorkspace.context().id&&(await api('dump')).text===g198Dump;}})()`));
    check('P58-5 有效封裝內的非法場景仍由核心拒絕並保留來源',await eval_(`(async()=>{const m=await ReferenceWorkspace.manifest(),s=new Map([...ReferenceWorkspace.context().sources].map(([k,v])=>[k,v.bytes]));const bad=await GeometryProject.pack('boundary 1 outline 0,0 1,1 2,0\\n',m,s,fflate);const id=ReferenceWorkspace.context().id;try{await ReferenceWorkspace.importBytes(bad);return false;}catch(e){return id===ReferenceWorkspace.context().id&&(await api('dump')).text===g198Dump;}})()`));
    const pdf=require('../tests/reference_pdf_fixture.js')().toString('base64');
    await eval_(`(async()=>{window.g198PDF=await ReferenceWorkspace.sourceFromFile(new File([Uint8Array.from(atob(${JSON.stringify(pdf)}),c=>c.charCodeAt(0))],'test-reference.pdf',{type:'application/pdf'}));await ReferenceWorkspace.openSource(g198PDF,1);})()`);
    check('P59-1 本機 PDF.js 讀到兩頁與縮圖',await eval_(`$('refPageCount').textContent==='/ 2 頁'&&document.querySelectorAll('.ref-thumbnail').length===2&&!$('refApply').disabled`));
    const cancelDump=await eval_(`api('dump').then(r=>r.text)`);
    await ctl('#refClose');
    check('P59-2 取消選頁不建立物件',await eval_(`(async()=>!$('referenceDialog').open&&(await api('dump')).text===${JSON.stringify(cancelDump)})()`));
    await eval_(`ReferenceWorkspace.openSource(g198PDF,1)`);await field('refPageNumber','2');
    await until(`!$('refApply').disabled&&document.querySelector('#refPagePreview img')?.alt==='第 2 頁預覽'`);
    // Ready controls precede asynchronous image decode and thumbnail layout.
    // Measure only a decoded, stable preview; retain the original 240px oracle.
    await until(`(()=>{const imgs=[...document.querySelectorAll('#refPagePreview img,.ref-thumbnail img')];return imgs.length===3&&imgs.every(img=>img.complete&&img.naturalWidth>0);})()`);
    const crop=await eval_(`(async()=>{const imgs=[...document.querySelectorAll('#refPagePreview img,.ref-thumbnail img')];await Promise.all(imgs.map(img=>img.decode()));let previous='',stable=0;for(let i=0;i<60;i++){await new Promise(requestAnimationFrame);const r=$('refPagePreview').getBoundingClientRect(),current={x:r.x,y:r.y,w:r.width,h:r.height};const encoded=JSON.stringify(current);stable=encoded===previous?stable+1:0;previous=encoded;if(stable>=2&&r.width>0&&r.height>0)return current;}throw Error('PDF crop preview did not stabilize');})()`);
    await drag(crop.x+crop.w*.03,crop.y+crop.h*.1,crop.x+crop.w*.83,crop.y+crop.h*.9);
    const cropAfter=await eval_(`(()=>{const r=$('refPagePreview').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,overlay:$('refCropOverlay').getAttribute('style'),page:$('refPageNumber').value}})()`);
    await ctl('#refApply');await until(`!$('referenceDialog').open`);
    const cropActual=await eval_(`(()=>{const p=ReferenceWorkspace.active(1);return {page:p.page,imgW:p.imgW,imgH:p.imgH,crop:p.crop,pages:ReferenceWorkspace.group(1).pages.length,sourceId:p.sourceId};})()`);
    console.log('[PDF_CROP_COORDINATES]',JSON.stringify({expectedWidth:240,before:crop,after:cropAfter,actual:cropActual}));
    check('P59-3 PDF 取景使用固定頁面座標，與圖片共用面',cropActual.page===2&&cropActual.imgW===300&&cropActual.imgH===200&&Math.abs(cropActual.crop[2]-240)<1&&cropActual.pages===2,cropActual);
    await ctl('#ulCalibStart');await eval_(`feUnderlayCalibPoint([20,70]);feUnderlayCalibPoint([220,70]);`);
    await field('ulCalibDist','2000');await ctl('#ulCalibApply');
    check('P59-4 PDF 校準後座標與縮放算繪一致',await eval_(`(async()=>{const p=ReferenceWorkspace.active(1),before=feUlImgToMm(p,100,100);await ReferenceWorkspace.preparePage(p,g198PDF);const after=feUlImgToMm(p,100,100);return p.mmPerPx===10&&before.every((v,i)=>Math.abs(v-after[i])<1e-8);})()`));
    check('P59-4b 已知矩形及 L 形的四種直角座標誤差不超過 1 mm',await eval_(`(()=>{
      const p=ReferenceWorkspace.active(1);p.x=-200;p.y=-700;
      // Independent expected coordinates from the authored PDF (its Y axis points upward).
      const fixtures=[
        {source:[[20,70],[220,70],[220,170],[20,170]],expected:[
          [[0,0],[2000,0],[2000,1000],[0,1000]],
          [[1600,-1000],[1600,1000],[600,1000],[600,-1000]],
          [[2600,600],[600,600],[600,-400],[2600,-400]],
          [[1000,1600],[1000,-400],[2000,-400],[2000,1600]]]},
        {source:[[20,70],[100,70],[100,110],[220,110],[220,170],[20,170]],expected:[
          [[0,0],[800,0],[800,400],[2000,400],[2000,1000],[0,1000]],
          [[1600,-1000],[1600,-200],[1200,-200],[1200,1000],[600,1000],[600,-1000]],
          [[2600,600],[1800,600],[1800,200],[600,200],[600,-400],[2600,-400]],
          [[1000,1600],[1000,800],[1400,800],[1400,-400],[2000,-400],[2000,1600]]]}
      ];
      const ok=fixtures.every(f=>[0,90,180,270].every((rot,r)=>{p.rot=rot;return f.source.every((v,i)=>feUlImgToMm(p,...v).every((n,j)=>Math.abs(Math.round(n)-f.expected[r][i][j])<=1));}));
      p.rot=0;window.g198ExpectedL=fixtures[1].expected[0];
      window.g198TracedL=fixtures[1].source.map(v=>feUlImgToMm(p,...v).map(Math.round));return ok;
    })()`));
    await eval_(`(async()=>{const r=await api('line boundary 1 outline '+g198TracedL.map(v=>v.join(',')).join(' '));await feAfterChange();return r.ok;})()`);
    check('P59-5 L 形邊界仍走既有核心，底圖保留',await eval_(`oc.bmap[1][0].verts.length===6&&ReferenceWorkspace.active(1).page===2`));
    await eval_(`(async()=>{window.g198PDFSaved=await ReferenceWorkspace.exportBytes();await ReferenceWorkspace.importBytes(g198PDFSaved);await enterFocus('face',1);fiShowTab('underlay');})()`);
    check('P60-1 PDF 重開仍是 L 形、兩張來源及原校準',await eval_(`JSON.stringify(oc.bmap[1][0].verts)===JSON.stringify(g198ExpectedL)&&ReferenceWorkspace.group(1).pages.length===2&&ReferenceWorkspace.active(1).mmPerPx===10`));
    await field('refActivePage',await eval_(`ReferenceWorkspace.group(1).pages[0].id`));
    await until(`ReferenceWorkspace.active(1)?.page===1`);
    check('P60-2 切回圖片保留獨立校準、旋轉與紀錄',await eval_(`ReferenceWorkspace.active(1).rot===270&&ReferenceWorkspace.active(1).records[1].value===null&&ReferenceWorkspace.active(1).calibration.distanceMm===1600`));
    check('P60-3 慢速圖頁完成時不蓋過使用者後選的頁',await eval_(`(async()=>{
      const g=ReferenceWorkspace.group(1),first=g.pages[0],second=g.pages[1];delete second.src;
      const doc=ReferenceWorkspace.context().sources.get(second.sourceId).doc,original=doc.getPage.bind(doc);
      let release,entered;const gate=new Promise(r=>release=r),started=new Promise(r=>entered=r);
      doc.getPage=async n=>{entered();await gate;return original(n);};
      try{const pending=ReferenceWorkspace.selectPage(1,second.id);await started;await ReferenceWorkspace.selectPage(1,first.id);release();await pending;return ReferenceWorkspace.active(1).id===first.id;}
      finally{release();doc.getPage=original;}
    })()`));
    await eval_(`ReferenceWorkspace.openSource(g198PDF,1)`);
    await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
    check('P61-1 窄版選頁對話框與確認按鈕在視窗內',await eval_(`(()=>{const d=$('referenceDialog').getBoundingClientRect(),b=$('refApply').getBoundingClientRect();return d.left>=0&&d.right<=innerWidth&&d.bottom<=innerHeight&&b.bottom<=innerHeight&&b.width>0;})()`));
    await ctl('#refClose');await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
    check('P61-2 取消後原來源與面仍存在',await eval_(`!$('referenceDialog').open&&!!ReferenceWorkspace.active(1)&&oc.bmap[1][0].verts.length===6`));
    check('P61-3 切圖頁不累積同一面的返回堆疊',await eval_(`oc.stack.filter(f=>f.t==='face'&&f.id===1).length===0`));
    check('P61-4 另存取消不變更世界或來源',await eval_(`(async()=>{const old=window.showSaveFilePicker,before=(await api('dump')).text,id=ReferenceWorkspace.context().id;window.showSaveFilePicker=async()=>{throw new DOMException('cancel','AbortError');};try{await ReferenceWorkspace.save();return (await api('dump')).text===before&&ReferenceWorkspace.context().id===id&&!ReferenceWorkspace.busy;}finally{window.showSaveFilePicker=old;}})()`));
    check('P61-5 寫檔失敗保留未保存狀態並中止寫入',await eval_(`(async()=>{const old=window.showSaveFilePicker;let aborted=false;ReferenceWorkspace.context().dirty=true;window.showSaveFilePicker=async()=>({createWritable:async()=>({write:async()=>{throw Error('disk full');},abort:async()=>{aborted=true;}})});try{await ReferenceWorkspace.save();return false;}catch(e){return e.message==='disk full'&&aborted&&ReferenceWorkspace.context().dirty&&!ReferenceWorkspace.busy;}finally{window.showSaveFilePicker=old;}})()`));
    check('P61-5b 寫入關閉完成前不宣告已保存',await eval_(`(async()=>{
      const old=window.showSaveFilePicker;let release,entered,written;
      const gate=new Promise(r=>release=r),started=new Promise(r=>entered=r);
      window.showSaveFilePicker=async()=>({createWritable:async()=>({write:async bytes=>{written=bytes;},close:async()=>{entered();await gate;},abort:async()=>{}})});
      ReferenceWorkspace.context().dirty=true;setStatus('等待測試寫入');
      try{const pending=ReferenceWorkspace.save();await Promise.race([started,pending.then(()=>{throw Error('write never reached close');})]);
        const dump=(await api('dump')).text;
        $('btnClear').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true}));$('btnClear').click();
        await new Promise(r=>setTimeout(r,100));
        const before=ReferenceWorkspace.context().dirty&&!$('status').textContent.includes('專案已保存')&&(await api('dump')).text===dump;release();await pending;
        return before&&written instanceof Uint8Array&&written.length>0&&!ReferenceWorkspace.context().dirty&&$('status').textContent.includes('專案已保存');
      }finally{release();window.showSaveFilePicker=old;}
    })()`));
    check('P61-6 不同 PDF 算繪解析度共用同一頁面座標',await eval_(`(async()=>{const a=await ReferenceWorkspace.renderPage(g198PDF,1,1),b=await ReferenceWorkspace.renderPage(g198PDF,1,3);return a.width===b.width&&a.height===b.height&&a.canvas.width!==b.canvas.width;})()`));
    await eval_(`(async()=>{const data=await ReferenceWorkspace.exportBytes();await ReferenceWorkspace.importBytes(data);await enterFocus('face',1);fiShowTab('underlay');feUnderlayRemove(1);})()`);
    await until(`!!oc.underlays[1]?.src`);
    check('P61-7 移除目前頁後可載入尚未算繪的另一頁',await eval_(`ReferenceWorkspace.group(1).pages.length===1&&ReferenceWorkspace.active(1).page===2&&!!$('feUnderlay')`));
    const lastDump=await eval_(`api('dump').then(r=>r.text)`);
    await eval_(`(async()=>{const bad=await ReferenceWorkspace.sourceFromFile(new File(['%PDF-broken'],'broken.pdf',{type:'application/pdf'}));await ReferenceWorkspace.openSource(bad,1);})()`);
    check('P61-8 PDF 讀取失敗提供訊息且不能套用',await eval_(`$('refApply').disabled&&$('refPreviewMessage').textContent.includes('無法讀取')`));
    const failedPdfExceptions = excN;
    await eval_(`$('refPagePreview').dispatchEvent(new PointerEvent('pointerup',{bubbles:true}))`);
    check('P61-8b 未就緒預覽的點按不觸發例外',excN===failedPdfExceptions);
    await ctl('#refClose');
    check('P61-9 PDF 讀取失敗保留原場景',await eval_(`api('dump').then(r=>r.text===${JSON.stringify(lastDump)})`));
    check('P61-10 載入未送達時，重試連線保留原幾何與來源',await eval_(`(async()=>{
      const oldFetch=window.fetch.bind(window),before=(await api('dump')).text,ref=ReferenceWorkspace.active(1).id;
      window.fetch=async(input,init)=>{if(input==='/upload/confirm')throw new TypeError('test upload disconnected');return oldFetch(input,init);};
      let blocked=false;try{await ReferenceWorkspace.importBytes(g198Saved);}catch(e){blocked=connection.phase==='error';}finally{window.fetch=oldFetch;}
      await recoverConnection();return blocked&&connection.phase==='ready'&&(await api('dump')).text===before&&ReferenceWorkspace.active(1).id===ref;
    })()`));
    check('P61-11 載入已送達但回應遺失時，核對核心後恢復正確來源',await eval_(`(async()=>{
      const oldFetch=window.fetch.bind(window);
      window.fetch=async(input,init)=>{if(input==='/upload/confirm'){await oldFetch(input,init);throw new TypeError('test response lost');}return oldFetch(input,init);};
      let blocked=false;try{await ReferenceWorkspace.importBytes(g198Saved);}catch(e){blocked=connection.phase==='error';}finally{window.fetch=oldFetch;}
      await recoverConnection();return blocked&&connection.phase==='ready'&&(await api('dump')).text===g198Dump&&ReferenceWorkspace.active(1).calibration.distanceMm===1600&&typeof curScene.path==='string'&&curScene.path.endsWith('.scene');
    })()`));
    await eval_(`ReferenceWorkspace.openSource(g198PDF,1)`);
    await field('refTarget','new');
    await eval_(`(async()=>{
      const original=objNewPolyFace;let release,entered;
      const gate=new Promise(r=>release=r),started=new Promise(r=>entered=r);
      window.g198Applying={original,release:()=>release()};
      objNewPolyFace=async()=>{entered();await gate;return original();};
      g198Applying.pending=$('refApply').onclick();await started;
    })()`);
    await ctl('#refNext');await field('refPageNumber','2');await ctl('#refResetCrop');
    check('P61-12 建面等待期間鎖定已確認圖頁與取景',await eval_(`(async()=>{
      const locked=ReferenceWorkspace.busy&&$('referenceDialog').inert;
      try{g198Applying.release();await g198Applying.pending;const p=ReferenceWorkspace.active(oc.edit.bid);
        return locked&&p?.sourceId===g198PDF.meta.id&&p.page===1&&JSON.stringify(p.crop)==='[0,0,300,200]'&&!$('referenceDialog').open&&!$('referenceDialog').inert;
      }finally{objNewPolyFace=g198Applying.original;g198Applying.release();}
    })()`));
    await eval_(`ReferenceWorkspace.importBytes(g198Saved)`);
    check('P61-13 寫入回應遺失可查回結果，復原保留同一面的來源',await eval_(`(async()=>{
      const old=window.fetch.bind(window),before=(await api('dump')).text,ref=ReferenceWorkspace.active(1).id;
      window.fetch=async(input,init)=>{const body=input==='/api'&&JSON.parse(init.body);if(body?.cmd==='line spec receipt_probe 10'){await old(input,init);throw new TypeError('lost reply');}return old(input,init);};
      let result;try{result=await api('line spec receipt_probe 10');}finally{window.fetch=old;}
      await doUndoRedo('undo');return result.ok&&connection.phase==='ready'&&(await api('dump')).text===before&&ReferenceWorkspace.active(1).id===ref;
    })()`));
    check('P61-14 未送達操作不重送，也不新增來源歷史',await eval_(`(async()=>{
      const old=window.fetch.bind(window),before=(await api('dump')).text,n=ReferenceWorkspace.history.undo.length;
      window.fetch=async(input,init)=>{const body=input==='/api'&&JSON.parse(init.body);if(body?.cmd==='line spec never_arrived 10')throw new TypeError('not sent');return old(input,init);};
      let result;try{result=await api('line spec never_arrived 10');}finally{window.fetch=old;}
      return !result.ok&&!result.transport&&connection.phase==='ready'&&(await api('dump')).text===before&&ReferenceWorkspace.history.undo.length===n;
    })()`));
    const receiptDir=require('fs').mkdtempSync(require('path').join(require('os').tmpdir(),'geometry-receipt-'));
    const receiptScene=require('path').join(receiptDir,'same-id.scene');
    const receiptServerScene=serverFixturePath(receiptScene);
    require('fs').writeFileSync(receiptScene,'boundary 1 outline 0,0 3000,0 3000,1500 0,1500\n');
    try {
      const receiptLoadResult=await eval_(`(async()=>{
        const old=window.fetch.bind(window),ref=ReferenceWorkspace.active(1).id,cmd='loadfile '+${JSON.stringify(receiptServerScene)};
        window.fetch=async(input,init)=>{const body=input==='/api'&&JSON.parse(init.body);if(body?.cmd===cmd){await old(input,init);throw new TypeError('lost load reply');}if(body?.receipt)throw new TypeError('still offline');return old(input,init);};
        let result;try{result=await api(cmd);}finally{window.fetch=old;}
        const blocked=!result.ok&&connection.phase==='error';await recoverConnection();
        const isolated=connection.phase==='ready'&&!ReferenceWorkspace.active(1)&&!oc.underlays[1];
        await doUndoRedo('undo');return {blocked,isolated,restored:ReferenceWorkspace.active(1)?.id===ref,result};
      })()`);
      check('P61-15 場景載入回應遺失，重連隔離同號面且復原恢復來源',receiptLoadResult?.blocked&&receiptLoadResult.isolated&&receiptLoadResult.restored,receiptLoadResult);
    } finally {require('fs').unlinkSync(receiptScene);require('fs').rmdirSync(receiptDir);}
    check('P61-16 群組提交回應遺失仍只復原一步並保留來源',await eval_(`(async()=>{
      const old=window.fetch.bind(window),before=(await api('dump')).text,ref=ReferenceWorkspace.active(1).id;
      window.fetch=async(input,init)=>{const body=input==='/api'&&JSON.parse(init.body);if(body?.cmd==='line history-end'){await old(input,init);throw new TypeError('lost commit reply');}if(body?.receipt)throw new TypeError('offline');return old(input,init);};
      try{await mutate(['spec receipt_group_a 10','spec receipt_group_b 20']);}finally{window.fetch=old;}
      const blocked=connection.phase==='error';await recoverConnection();await doUndoRedo('undo');
      return blocked&&connection.phase==='ready'&&(await api('dump')).text===before&&ReferenceWorkspace.active(1)?.id===ref;
    })()`));
    check('P61-16b 群組內操作未送達時重連仍回復核心群組',await eval_(`(async()=>{
      const old=window.fetch.bind(window),before=(await api('dump')).text,ref=ReferenceWorkspace.active(1).id;
      window.fetch=async(input,init)=>{const body=input==='/api'&&JSON.parse(init.body);if(body?.cmd==='line spec group_not_sent 20'||body?.receipt)throw new TypeError('offline before send');return old(input,init);};
      try{await mutate(['spec group_before_disconnect 10','spec group_not_sent 20']);}finally{window.fetch=old;}
      const blocked=connection.phase==='error';
      let abortBlocked=false;
      window.fetch=async(input,init)=>{const body=input==='/api'&&JSON.parse(init.body);if(body?.cmd==='line history-abort'){abortBlocked=true;throw new TypeError('rollback not sent');}if(body?.receipt&&abortBlocked)throw new TypeError('rollback still offline');return old(input,init);};
      try{await recoverConnection();}finally{window.fetch=old;}
      const retryBlocked=connection.phase==='error';await recoverConnection();
      const restored=(await api('dump')).text===before&&ReferenceWorkspace.active(1)?.id===ref;
      const next=await mutate(['spec after_group_recovery 10']);await doUndoRedo('undo');
      return blocked&&retryBlocked&&restored&&next&&connection.phase==='ready'&&(await api('dump')).text===before;
    })()`));
    check('P61-17 參考資料流程沒有未處理的瀏覽器例外',excN===referenceExceptions);
    await require('./project_import_final_objects_test.js')({read:eval_,send,until,check,doUndoRedo:op=>eval_('doUndoRedo('+JSON.stringify(op)+')')});
  }

  { /* ===== P62. 自訂 SVG 游標 — #116 B 面內 v2 =====
       驗收:(a) 圖形層與附件 v2 一致(箭頭路徑、狀態塊 h=18/rx=5/白描邊/色值、
       文字 11px 650 白字、獨立修飾鍵);(b) 狀態解析跟真實行為一致——
       select 命中族(edge/vertex/alt-vertex/move-line/timber-pick/hole-pick)、
       工具族(guide/hole/timber 族)、拖曳尺寸膠囊、space-pan、busy;
       (c) overlay pointer-events:none 不干擾命中、進畫布隱原生游標、離開即隱藏。 */
    console.log('=== P62. 自訂 SVG 游標(#116 B 面內 v2) ===');
    const ck62 = (n, v, d) => {
      console.log(n,explicitVerdict(v === true ? '✓' : '✗'), v === true ? '' : JSON.stringify(d));
      // Attribute checks miss a global CSS rule overriding SVG presentation attributes.
      if (d?.vis === 'visible' && d.labelStyle) {
        const s=d.labelStyle;
        console.log(n+' 實際字樣無描邊且保留白字',explicitVerdict(s.stroke==='none'&&s.width===0&&s.fill==='rgb(255, 255, 255)'?'✓':'✗'),s);
      }
      if (d?.tipStyle) {
        const s=d.tipStyle;
        console.log(n+' 尺寸提示實際字樣無描邊',explicitVerdict(s.stroke==='none'&&s.width===0&&s.fill==='rgb(255, 255, 255)'?'✓':'✗'),s);
      }
    };
    /* 面內區段慣例:視窗放大到 5400×3800,讓 zoom=1 的 scene mm 座標直接等於螢幕 px,
       可以直接對 4000×3000 的面點擊/滑過任意 mm 座標(同 P48-P52)。 */
    await send('Emulation.setDeviceMetricsOverride', { width: 5400, height: 3800, deviceScaleFactor: 1, mobile: false });
    /* Part A 世界:面 1 = 4000×3000 附孔 (1000,1000)~(2000,2000)、零角材——
       頂點把手不被角材帶蓋住,可直接點到 v:0:0;孔邊給 hole-pick/deny 用。 */
    const setup62 = await eval_(`(async()=>{
      const out=[]; for(const l of ['reset','line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000 hole 1000,1000 2000,1000 2000,2000 1000,2000',
        'line spec cx導線 2500','line guide 2 1 v spec:cx導線']) { const r=await apiRequest(l); out.push({l,ok:r.ok===true,err:r.error||null}); if(r.ok!==true) break; }
      return out; })()`);
    ck62('P62-0 Part A 場景建立全過', Array.isArray(setup62) && setup62.every(r => r.ok), setup62);
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects();
      await enterFocus('face',1); fe.zoom=1; fe.panX=0; fe.panY=0; feApply();
      await feLoadGuides(); drawFaceEditor();
      const t=$('faceSnapToggle'); if(t) t.checked=false; })()`);
    await sleep(350);
    const org62 = await eval_(`(()=>{const r=$('faceEditorSvg').getBoundingClientRect();
      return {x:r.left+fe.panX,y:r.top+fe.panY};})()`);
    const mv62 = async (mx, my, mods) => {
      await send('Input.dispatchMouseEvent', { type:'mouseMoved', x:org62.x+mx, y:org62.y+my, button:'none', modifiers:mods||0 });
      await sleep(60);
    };
    /* 讀游標覆層目前狀態(對測試最穩的是 DOM,不是螢幕截圖) */
    const cx62 = () => eval_(`(()=>{const h=cxUI.fe; if(!h) return null;
      const cap=h.cur.querySelector('.cx-capsule'), txt=h.cur.querySelector('.cx-label');
      const arrow=h.cur.querySelector('path');
      const style=e=>{if(!e)return null;const s=getComputedStyle(e);return {stroke:s.stroke,width:parseFloat(s.strokeWidth),fill:s.fill};};
      return { vis:h.svg.style.visibility, on:$('faceEditorViewport').classList.contains('cx-on'),
        cssCursor:getComputedStyle($('faceEditorSvg')).cursor,
        layerPE:getComputedStyle(h.svg).pointerEvents,
        arrowD:arrow?arrow.getAttribute('d'):null,
        transform:h.cur.getAttribute('transform'),
        capsule:cap?{x:+cap.x.baseVal.value,y:+cap.y.baseVal.value,w:+cap.width.baseVal.value,
          h:+cap.height.baseVal.value,rx:+cap.rx.baseVal.value,fill:cap.getAttribute('fill'),
          stroke:cap.getAttribute('stroke'),sw:cap.getAttribute('stroke-width')}:null,
        label:txt?txt.textContent:null, labelFill:txt?txt.getAttribute('fill'):null,
        text:h.cur.textContent,modifierStyle:style([...h.cur.querySelectorAll('text')].find(e=>e.textContent==='Space')),
        labelStyle:style(txt),tipStyle:style(h.cur.querySelector('.cx-tip text')),
        labelFs:txt?txt.getAttribute('font-size'):null, labelFw:txt?txt.getAttribute('font-weight'):null,
        tip:(h.cur.querySelector('.cx-tip text')||{}).textContent||null,
        marks:[...h.marks.children].map(c=>c.tagName)};})()`);

    const vpOrg62 = await eval_(`(()=>{const r=$('faceEditorViewport').getBoundingClientRect();
      return {x:r.left,y:r.top};})()`);
    await eval_(`feSetTool('select')`); await sleep(80);
    await mv62(3000, 2500);                                    /* 面內空白(避開孔與 guide 2) */
    let s62 = await cx62();
    ck62('P62-1 選取空白:箭頭無膠囊,cx-on 隱原生游標,熱點 translate 對齊指標',
      s62 && s62.vis === 'visible' && s62.on === true && s62.cssCursor === 'none' &&
      s62.layerPE === 'none' && s62.capsule === null &&
      s62.arrowD === 'M6 3.5 17.4 14l-5.2.7 2.8 5.1-2.5 1.3-2.7-5-3.8 3.5Z' &&
      s62.transform === `translate(${org62.x + 3000 - vpOrg62.x},${org62.y + 2500 - vpOrg62.y})`,
      s62);

    await mv62(2, 2);                                          /* 頂點 v0 把手圈(無角材世界,圈可直接點) */
    s62 = await cx62();
    ck62('P62-2 指到凸角:「拉角」face 綠 + v2 h18/rx5/白描邊1.5/字11-650',
      s62 && s62.label === '拉角' &&
      s62.capsule && s62.capsule.fill === '#2f8f7b' && s62.capsule.h === 18 && s62.capsule.rx === 5 &&
      s62.capsule.stroke === '#fff' && +s62.capsule.sw === 1.5 &&
      s62.labelFs === '11' && s62.labelFw === '650' && s62.labelFill === '#fff', s62);

    await mv62(2, 2, 1);                                       /* Alt=1 按住 */
    s62 = await cx62();
    ck62('P62-3 Alt+凸角:「捏缺口」face 綠與獨立 Alt 鍵',
      s62 && s62.label === '捏缺口' && s62.text.includes('Alt') && s62.capsule && s62.capsule.fill === '#2f8f7b', s62);

    await mv62(3997, 1500);                                    /* 外輪廓邊 e1 */
    s62 = await cx62();
    ck62('P62-4 指到外環邊:「推拉」', s62 && s62.label === '推拉', s62);

    await mv62(1000, 1500);                                    /* 孔左緣 e:1:x */
    s62 = await cx62();
    ck62('P62-5 指到孔邊:「孔」ink 膠囊',
      s62 && s62.label === '孔' && s62.capsule && s62.capsule.fill === '#172033', s62);

    await mv62(2500, 1500);                                    /* guide 2(u=2500 直立線) */
    s62 = await cx62();
    ck62('P62-6 指到參考線:「移動參考線」', s62 && s62.label === '移動參考線', s62);

    /* 開口工具拖矩形(驗拖曳中尺寸膠囊),區域避開既有孔 */
    await eval_(`feSetTool('hole')`); await sleep(80);
    await send('Input.dispatchMouseEvent', { type:'mousePressed', x:org62.x+2400, y:org62.y+2400, button:'left', clickCount:1 });
    await send('Input.dispatchMouseEvent', { type:'mouseMoved', x:org62.x+2800, y:org62.y+2800, button:'left', buttons:1 });
    await sleep(80);
    s62 = await cx62();
    ck62('P62-7 拖開口矩形中:「開口」+ 尺寸膠囊 400×400',
      s62 && s62.label === '開口' && s62.tip === '400 × 400 mm', s62);
    await send('Input.dispatchMouseEvent', { type:'mouseReleased', x:org62.x+2800, y:org62.y+2800, button:'left', clickCount:1 });
    await waitForUI(`(oc.bmap[1]||[]).length>=3`, 4000);
    // Boundary data arrives before feAfterChange finishes reloading guide hits.
    // Finish that refresh before switching tools and probing the guide cursor.
    await eval_(`window.__cdpSettleUI(0)`);

    await eval_(`feSetTool('timber')`); await sleep(80);
    await mv62(2500, 1500);                                    /* guide 2(u=2500,無角材蓋) */
    s62 = await cx62();
    ck62('P62-8 角材工具指到參考線:「沿此線放置」face 綠 + cross 基底',
      s62 && s62.label === '沿此線放置' && s62.capsule && s62.capsule.fill === '#2f8f7b', s62);
    await mv62(1000, 1500);                                    /* 孔的左緣 */
    s62 = await cx62();
    ck62('P62-9 角材工具指到孔邊:「孔邊請用右欄定位」danger 紅',
      s62 && s62.label === '孔邊請用右欄定位' && s62.capsule && s62.capsule.fill === '#c2414f', s62);
    await mv62(3000, 2200);                                    /* 面內空白(避開 guide 2;面外亦同:走表單) */
    s62 = await cx62();
    ck62('P62-10 角材工具空白:「角材」accent 膠囊(依右欄設定放置)',
      s62 && s62.label === '角材' && s62.capsule && s62.capsule.fill === '#4e67e8', s62);

    await eval_(`feSetTool('guide'); $('faceSnapToggle').checked=true;`); await sleep(80);
    await mv62(937, 1211);                                     /* 非格點 → 吸附標記 */
    s62 = await cx62();
    ck62('P62-11 參考線+吸附開:格點標記出現',
      s62 && s62.label === '參考線' && s62.marks.length >= 1, s62);
    await eval_(`$('faceSnapToggle').checked=false;`);

    await eval_(`feSetTool('pan')`); await sleep(80); await mv62(2000, 1500);
    s62 = await cx62();
    ck62('P62-12 平移工具:hand 基底', s62 && s62.arrowD === 'M7.5 11V6.8a1.4 1.4 0 0 1 2.8 0v3.4-5.6a1.4 1.4 0 0 1 2.8 0v5-4a1.4 1.4 0 0 1 2.8 0v4.6-2.4a1.4 1.4 0 0 1 2.8 0v5.1c0 4.3-2.5 7-6.6 7h-.8c-2.7 0-4.6-1.1-6.1-3L3 13.6a1.5 1.5 0 0 1 2.4-1.8Z', s62);
    ck62('P62-12b 手形已表意，不疊多餘狀態塊',s62 && s62.capsule === null && s62.label === null,s62);

    await eval_(`fe.spaceDown=true; feSetTool('select'); cxRefreshAll();`);
    s62 = await cx62();
    ck62('P62-13 按住空白:hand 基底與獨立 Space 鍵',
      s62 && s62.arrowD === 'M7.5 11V6.8a1.4 1.4 0 0 1 2.8 0v3.4-5.6a1.4 1.4 0 0 1 2.8 0v5-4a1.4 1.4 0 0 1 2.8 0v4.6-2.4a1.4 1.4 0 0 1 2.8 0v5.1c0 4.3-2.5 7-6.6 7h-.8c-2.7 0-4.6-1.1-6.1-3L3 13.6a1.5 1.5 0 0 1 2.4-1.8Z' && s62.text === 'Space', s62);
    // SVG's unused default stroke-width is 1 even when stroke:none disables it.
    ck62('P62-13b Space 鍵實際字樣無描邊且保留深字',s62?.modifierStyle?.stroke === 'none' && s62.modifierStyle.fill === 'rgb(89, 99, 118)',s62);
    await eval_(`fe.spaceDown=false;`);

    await eval_(`oc.busy=true; document.body.classList.add('oc-busy'); cxRefreshAll();`);
    await sleep(60); s62 = await cx62();
    ck62('P62-14 busy:「套用中」warning 橘 + spin 圖示',
      s62 && s62.label === '套用中' && s62.capsule && s62.capsule.fill === '#b96a16', s62);
    await eval_(`oc.busy=false; document.body.classList.remove('oc-busy'); cxRefreshAll();`);

    /* 指標移到畫布外(頂列)→ 覆層隱藏、原生游標回來 */
    await send('Input.dispatchMouseEvent', { type:'mouseMoved', x:60, y:8, button:'none' }); await sleep(80);
    s62 = await cx62();
    ck62('P62-15 離開畫布:覆層隱藏 + cx-on 解除',
      s62 && s62.vis === 'hidden' && s62.on === false, s62);

    /* Part B:預設世界(3 支角材)驗 select 工具指到角材本體 →「角材」ink。 */
    await eval_(`(async()=>{ await api('default'); await renderObjects();
      await enterFocus('face',1); fe.zoom=1; fe.panX=0; fe.panY=0; feApply(); await feLoadGuides(); drawFaceEditor(); feSetTool('select'); })()`);
    await sleep(350);
    await mv62(2000, 14);                                      /* 角材 1@e0 帶中央 */
    s62 = await cx62();
    ck62('P62-16 指到角材:真實「角材 1」ink 狀態塊',
      s62 && s62.label === '角材 1' && s62.capsule && s62.capsule.fill === '#172033', s62);

    /* 物件畫布層 */
    await eval_(`(async()=>{ resetSceneFocus(); await renderObjects(); })()`); await sleep(300);
    const card62 = await eval_(`(()=>{const c=[...document.querySelectorAll('.ocard')][0];
      if(!c) return null; const r=c.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
    if (!card62) ck62('P62-17 物件卡片存在', false, 'no .ocard');
    else {
      await send('Input.dispatchMouseEvent', { type:'mouseMoved', x:card62.x, y:card62.y, button:'none' }); await sleep(80);
      const s62o = await eval_(`(()=>{const h=cxUI.oc; if(!h) return null;
        const txt=h.cur.querySelector('.cx-label');
        const s=txt&&getComputedStyle(txt);
        return {vis:h.svg.style.visibility,on:$('canvasViewport').classList.contains('cx-on'),
          label:txt?txt.textContent:null,labelStyle:s?{stroke:s.stroke,width:parseFloat(s.strokeWidth),fill:s.fill}:null};})()`);
      ck62('P62-17 物件畫布指到卡片:「移動」hand', s62o && s62o.on === true && s62o.label === '移動', s62o);
      await eval_(`setOcTool('rect')`); await sleep(80);
      await send('Input.dispatchMouseEvent', { type:'mouseMoved', x:card62.x, y:card62.y, button:'none' }); await sleep(60);
      const s62r = await eval_(`(()=>{const h=cxUI.oc;const t=h.cur.querySelector('.cx-label');
        const s=t&&getComputedStyle(t);return {vis:h.svg.style.visibility,label:t?.textContent,
          labelStyle:s?{stroke:s.stroke,width:parseFloat(s.strokeWidth),fill:s.fill}:null};})()`);
      ck62('P62-18 矩形工具:「面·矩形」', s62r.label === '面·矩形', s62r);
      await eval_(`setOcTool('select')`);
    }

    /* 游標覆層不攔截命中:畫布上 elementFromPoint 仍穿到底下元素 */
    await eval_(`(async()=>{ await enterFocus('face',1); fe.zoom=1; fe.panX=0; fe.panY=0; feApply(); })()`);
    await sleep(250);
    await mv62(3997, 1500);
    const pe62 = await eval_(`(()=>{const h=cxUI.fe;
      const svgR=$('faceEditorSvg').getBoundingClientRect();
      const under=document.elementFromPoint(svgR.left+fe.panX+3997, svgR.top+fe.panY+1500);
      return {pe:getComputedStyle(h.svg).pointerEvents,
        under:under?(under.dataset&&under.dataset.faceHit)||under.tagName:null};})()`);
    ck62('P62-19 覆層 pointer-events:none,游標底下仍命中邊 e1',
      pe62 && pe62.pe === 'none' && pe62.under === 'e:0:1', pe62);
    ck62('P62-20 拖底圖出視窗的空命中不觸發例外',await eval_(`(()=>{
      const drag=fe.ulDrag,tool=fe.tool;try{fe.ulDrag={x0:0,y0:0,cx:0,cy:0};fe.tool='select';return !!cxResolveFace(-10,-10,false,false);}
      finally{fe.ulDrag=drag;fe.tool=tool;}
    })()`));
  }

  { // Reference interface: user-visible workflow and mobile point picking.
    console.log('=== P63. 參考描面新版介面 ===');
    const startErrors=excN;
    const check=bodyCheck();
    const ctl=async selector=>{
      const p=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
      await click(p.x,p.y);await sleep(100);
    };
    await send('Emulation.setDeviceMetricsOverride',{width:1440,height:800,deviceScaleFactor:1,mobile:false});
    await eval_(`(async()=>{resetSceneFocus();await api('reset');await api('line boundary 1 outline 0,0 2000,0 2000,1000 0,1000');await renderObjects();await ReferenceWorkspace.openSource(g198PDF,1);})()`);
    check('P63-1 預設整頁預覽完整可見',await eval_(`(()=>{const p=$('refPagePreview').getBoundingClientRect(),v=document.querySelector('.ref-preview-scroll').getBoundingClientRect();return $('refZoom').value==='page'&&p.height>100&&p.top>=v.top&&p.bottom<=v.bottom&&p.left>=v.left&&p.right<=v.right;})()`));
    await ctl('#refApply');await waitForUI(`!$('referenceDialog').open && !!ReferenceWorkspace.active(1)`,5000);
    check('P63-2 參考描面不補入高度或放置',await eval_(`!feSurf(1)&&$('workspacePlaceTag').textContent.includes('未放置')`));
    check('P63-3 校準入口在首屏，舊放置表單不擋住它',await eval_(`(()=>{const b=$('ulCalibStart').getBoundingClientRect();return b.width>0&&b.bottom<innerHeight&&getComputedStyle(document.querySelector('.face-placement-flow')).display==='none'&&!$('refAlignmentDetails').open&&$('faceReferenceSummary').textContent.includes('未校準');})()`));
    await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});
    if (!await eval_(`document.body.classList.contains('drawer-right-open')`)) await ctl('#workspaceToggleRight');
    const p63hit=await eval_(`(()=>{const e=$('ulCalibStart');e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect(),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {innerWidth,rect:[r.x,r.y,r.width,r.height],hit:h?.outerHTML?.slice(0,150),target:e.outerHTML?.slice(0,150),dialog:$('referenceDialog').open};})()`);
    await ctl('#ulCalibStart');
    const p63_4=await eval_(`({drawer:document.body.classList.contains('drawer-right-open'),promptHidden:$('calibrationCanvasPrompt').hidden,prompt:$('calibrationCanvasPrompt').textContent,calib:fe.ulCalib?.pts?.length,tab:fe.fiTab})`);
    check('P63-4 手機取點自動收起檢查器且保留取消入口',!p63_4.drawer&&!p63_4.promptHidden&&p63_4.prompt.includes('第 1'),{p63_4,p63hit});
    await eval_(`ReferenceWorkspace.fitReference()`);
    const clickPoint=async(x,y)=>{
      const p=await eval_(`(()=>{const ul=ReferenceWorkspace.active(1),q=feUlImgToMm(ul,${x},${y}),r=$('faceEditorViewport').getBoundingClientRect();return {x:r.x+fe.panX+q[0]*fe.zoom,y:r.y+fe.panY+q[1]*fe.zoom};})()`);
      await click(p.x,p.y);await sleep(100);
    };
    await clickPoint(20,70);await clickPoint(220,70);
    const p63_5=await eval_(`({pts:fe.ulCalib?.pts,drawer:document.body.classList.contains('drawer-right-open'),focus:document.activeElement.id,disabled:$('ulCalibDist')?.disabled})`);
    check('P63-5 實際畫布點兩點後回到距離輸入',p63_5.pts?.length===2&&p63_5.drawer&&p63_5.focus==='ulCalibDist'&&!p63_5.disabled,p63_5);
    check('P63-5b 校準草稿不宣稱已保存，也不能默默略過取點',await eval_(`(async()=>{try{await ReferenceWorkspace.exportBytes();return false;}catch(e){return e.message.includes('校準尚未套用')&&document.querySelector('[data-project-status]').textContent==='校準尚未套用';}})()`));
    check('P63-5c 手機回報鈕不擋住校準單位',await eval_(`(()=>{const e=$('ulCalibUnit'),r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return e===hit||e.contains(hit);})()`));
    await eval_(`$('ulCalibDist').value='200';$('ulCalibUnit').value='cm';`);await ctl('#ulCalibApply');
    check('P63-6 手機套用校準保留原幾何與待核對提示',await eval_(`ReferenceWorkspace.active(1).calibration.distanceMm===2000&&ReferenceWorkspace.active(1).reviewRequired&&oc.bmap[1][0].verts[1][0]===2000&&!fe.ulCalib&&$('calibrationCanvasPrompt').hidden`));
    await ctl('#ulCalibStart');await ctl('#cancelCalibration');
    check('P63-7 取消取點不修改已校準比例',await eval_(`!fe.ulCalib&&ReferenceWorkspace.active(1).calibration.distanceMm===2000&&document.body.classList.contains('drawer-right-open')`));
    await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
    await eval_(`closePanels();feSetTool('redraw');fe.draft.pts=[[0,0],[1000,0]];feSyncDraftMirror();`);
    check('P63-8 保存不會默默丟掉未套用外環草稿',await eval_(`(async()=>{try{await ReferenceWorkspace.exportBytes();return false;}catch(e){return e.message.includes('草稿')&&fe.draft.pts.length===2;}})()`));
    await eval_(`fe.draft=PolyDraft.createState();feSetTool('select');`);
    check('P63-9 保存按鈕在工作區頂列且匯出仍在檔案選單',await eval_(`(()=>{const b=document.querySelector('#projectBar [data-project-action="save"]').getBoundingClientRect(),h=document.querySelector('.object-workspace-topbar').getBoundingClientRect();return b.top>=h.top&&b.bottom<=h.bottom&&h.top===0&&$('btnExport').closest('#fileMenuPop')!==null;})()`));
    check('P63-10 寫入完成後顯示已保存，後續變更恢復未保存',await eval_(`(async()=>{const old=window.showSaveFilePicker;window.showSaveFilePicker=async()=>({createWritable:async()=>({write:async()=>{},close:async()=>{}})});try{await ReferenceWorkspace.save();const ok=[...document.querySelectorAll('[data-project-status]')].every(e=>e.textContent==='已保存');ReferenceWorkspace.changed(1);ReferenceWorkspace.present();return ok&&document.querySelector('[data-project-status]').textContent==='有未保存的變更';}finally{window.showSaveFilePicker=old;}})()`));
    check('P63-11 下載模式不宣稱已寫入檔案，也保留未保存狀態',await eval_(`(async()=>{const old=window.showSaveFilePicker,click=HTMLAnchorElement.prototype.click;window.showSaveFilePicker=undefined;HTMLAnchorElement.prototype.click=function(){};try{await ReferenceWorkspace.save();return ReferenceWorkspace.context().dirty&&document.querySelector('[data-project-status]').textContent.includes('已產生下載');}finally{window.showSaveFilePicker=old;HTMLAnchorElement.prototype.click=click;}})()`));
    await ctl('[data-fi-tab="prop"]');
    const p63_12=await eval_(`({tab:fe.fiTab,flow:getComputedStyle(document.querySelector('.face-placement-flow')).display,form:!!$('placeOX'),pressed:document.querySelector('[data-fi-tab="prop"]').getAttribute('aria-pressed')})`);
    check('P63-12 屬性頁可返回既有放置表單',p63_12.tab==='prop'&&p63_12.form&&p63_12.flow!=='none'&&p63_12.pressed==='true',p63_12);
    await ctl('.object-workspace-topbar #fileMenuBtn');
    for (const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{type,key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    await sleep(100);
    check('P63-13 檔案選單 Esc 只關閉選單，仍在同一個面',await eval_(`document.querySelector('#fileMenuPop').hidden&&!$('objectWorkspace').hidden&&oc.edit.bid===1`));
    await eval_(`window.uiSavedPicker=window.showSaveFilePicker;window.uiWriteCount=0;window.showSaveFilePicker=async()=>({createWritable:async()=>({write:async()=>{uiWriteCount++;},close:async()=>{}})});`);
    await ctl('#projectBar [data-project-action="save"]');await waitForUI(`uiWriteCount===1&&!ReferenceWorkspace.busy`,5000);
    check('P63-14 固定保存按鈕實際呼叫專案寫入',await eval_(`uiWriteCount===1&&document.querySelector('[data-project-status]').textContent==='已保存'`));
    await eval_(`window.showSaveFilePicker=uiSavedPicker;`);
    check('P63-15 開啟專案後解除處理中狀態並恢復保存按鈕',await eval_(`(async()=>{
      const bytes=await ReferenceWorkspace.exportBytes(),input=$('projectFile'),files=new DataTransfer();files.items.add(new File([bytes],'ui-reopen.gcanvas'));input.files=files.files;
      await input.onchange({target:input});return !ReferenceWorkspace.busy&&document.querySelector('[data-project-status]').textContent==='已保存'&&[...document.querySelectorAll('[data-project-action="save"]')].every(b=>!b.disabled);
    })()`));
    check('P63-16 新版流程沒有未處理的瀏覽器例外',excN===startErrors);
  }

  { // The 2026-09-27 review draft: visible controls and their real interactions.
    console.log('=== P64. UI/UX 審查修正稿 ===');
    const check=bodyCheck();
    const setupRemaining=async lines=>{
      const out=await eval_(`(async()=>{await setView3(false);resetSceneFocus();await api('reset');const out=[];for(const s of ${JSON.stringify(lines)})out.push(await api('line '+s));await renderObjects();return out})()`);
      if (!Array.isArray(out)||out.some(r=>!r.ok)) throw Error('P64 setup '+JSON.stringify(out));
    };
    const clickSelector=async selector=>{
      const p=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,hit:e.contains(document.elementFromPoint(x,y))};})()`);
      if (!p.hit) throw Error('P64 control unreachable '+selector+' '+JSON.stringify(p));
      await click(p.x,p.y);await sleep(120);
    };
    const remainingShot=async name=>{
      const dest=process.env.GEOMETRY_REPAIR_SCREENSHOT_DIR;if(!dest)return;
      fs.mkdirSync(dest,{recursive:true});
      const r=await send('Page.captureScreenshot',{format:'png'});
      require('fs').writeFileSync(require('path').join(dest,name+'.png'),Buffer.from(r.result.data,'base64'));
    };
    const waitIdle=()=>waitForUI('!oc.busy && !dragging');
    await send('Emulation.setDeviceMetricsOverride',{width:1382,height:804,deviceScaleFactor:1,mobile:false});
    await eval_(`geometryFeedback.close()`);
    await setupRemaining(['boundary 1 outline 0,0 4000,0 4000,3000 0,3000']);
    check('P64 M1-M4 主畫布專案、保存與常駐來源入口',await eval_(`(()=>{
      return document.querySelector('#fileMenuPop').contains(document.querySelector('#sceneList'))
        && !document.querySelector('#sceneMenuLabel').textContent.includes('.scene')
        && document.querySelector('#projectBar [data-project-name]')
        && document.querySelector('.topbar [data-project-status]')
        && document.querySelector('#btnSaveProject').textContent.includes('另存新檔')
        && document.querySelector('.topbar .project-save [data-icon="save"]')
        && document.querySelector('#btnNewRect').closest('.tool-group')
        && document.querySelector('#btnNewPoly').closest('.tool-group')
        && $('btnNewGridSystem').closest('.sidebar-left') && $('btnQuickBoundary').closest('.sidebar-left')
        && $('createObjectPop').contains($('btnBox6')) && !$('createObjectPop').querySelector('[data-project-action="import"],#btnSpaceModelTrial,#btnSpaceModels');})()`));
    check('P64 M5-M8 型別色、未放置、畫布切換與空間卡',await eval_(`(()=>{
      const root=getComputedStyle(document.documentElement),face=document.querySelector('.object-row[data-kind="boundary"]');
      const s=$('snapToggle'),g=$('gridToggle');
      return !!root.getPropertyValue('--column').trim() && !!root.getPropertyValue('--beam').trim()
        && face?.textContent.includes('未放置') && s.textContent.includes('吸附') && g.textContent.includes('格點')
        && s.getAttribute('aria-pressed')==='true' && g.getAttribute('aria-pressed')==='true';})()`));
    await eval_(`enterFocus('face',1)`);
    check('P64 M7 面內吸附切換文案與狀態一致',await eval_(`(()=>{
      const t=$('faceSnapToggle'),label=t.closest('.mini-toggle'),before=t.checked;t.click();
      const changed=t.checked!==before&&label.textContent.includes('吸附')&&label.getAttribute('aria-pressed')===String(t.checked);
      t.click();return changed&&t.checked===before&&label.getAttribute('aria-pressed')===String(before);})()`));
    check('P64 F1 單列工作區與共用保存選單',await eval_(`(()=>{
      const ws=$('objectWorkspace');return !ws.hidden && !ws.querySelector('.workspace-project-bar')
        && ws.querySelector('.object-workspace-topbar #fileMenu')
        && ws.querySelector('.object-workspace-topbar .project-save')
        && !!ws.querySelector('.object-workspace-topbar [data-project-status]');})()`));
    await clickSelector('#shapeToolButton');
    check('P64 F2 四個不同形狀操作與唯一 R 開口入口',await eval_(`!$('shapeToolPop').hidden && ['notch','extend','push','corner'].every(a=>$('shapeToolPop').querySelector('[data-shape-action="'+a+'"]')) && !$('shapeToolPop').querySelector('[data-shape-action="hole"]') && document.querySelectorAll('#faceWorkspaceTools [data-face-tool="hole"]').length===1 && document.querySelector('#faceWorkspaceTools [data-face-tool="hole"] kbd').textContent==='R'`));
    await clickSelector('[data-shape-action="notch"]');
    check('P64 F2 凹口等待選邊並可取消',await eval_(`fe.queuedShapeAction==='notch' && $('faceCanvasHint').textContent.includes('外環邊')`));
    for (const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{type,key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    const cancelledShape=await eval_(`!fe.queuedShapeAction && !!oc.edit`);
    for (const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{type,key:'r',code:'KeyR',windowsVirtualKeyCode:82});
    const retainedHoleShortcut=await eval_(`fe.tool==='hole' && !!oc.edit && !fe.queuedShapeAction`);
    for (const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{type,key:'v',code:'KeyV',windowsVirtualKeyCode:86});
    check('P64 F2 Esc 取消形狀選擇且 R 開口與 V 選取快捷鍵仍可用',cancelledShape&&retainedHoleShortcut&&await eval_(`!fe.queuedShapeAction && !!oc.edit && fe.tool==='select'`));
    check('P64 F3-F5 四頁、構件段與形狀庫',await eval_(`(()=>{
      const tabs=[...document.querySelectorAll('#faceInspectorTabs [data-fi-tab]')].map(e=>e.dataset.fiTab);
      fiShowTab('shape');const shape=$('faceInspectorContent').contains($('faceShapeButton'))&&!$('faceShapeButton').hidden;
      fiShowTab('timber');return tabs.join()==='prop,shape,components,underlay' && shape
        && document.querySelector('[data-fi-tab="components"]').classList.contains('active')
        && ['guide','timber','grid'].every(s=>!!document.querySelector('[data-component-section="'+s+'"]'))
        && $('tbA').offsetParent!==null;})()`));
    check('P64 F7-F8 T1-T2 中文欄位、分組與軸向',await eval_(`(()=>{
      const p=$('faceInspectorContent'),h=$('workspaceKeyHints').textContent;
      return h.includes('Esc') && p.querySelectorAll('.timber-form-group').length===3
        && p.textContent.includes('寬 A（沿面）') && p.textContent.includes('厚 B（出面）')
        && !!p.querySelector('#tbDirAuto') && !!p.querySelector('#tbRoleAuto');})()`));
    check('P64 G2 R1 R2 特徵說明、描面三步與底圖版型',await eval_(`(()=>{
      fiShowTab('shape');const feature=!!document.querySelector('.feature-persistence-note');
      fiShowTab('underlay');const steps=document.querySelectorAll('[data-reference-step]').length;
      return feature && steps===3 && !!document.querySelector('[data-fi-pane="underlay"] .inspector-block');})()`));
    check('P64 G2 切場景前提示特徵參數會消失',await eval_(`(()=>{
      const old=window.confirm,prior=fe.feats[1];let prompt='';fe.feats[1]=[{id:'review-probe'}];
      window.confirm=s=>{prompt=s;return false};
      try{return !ReferenceWorkspace.mayLeave()&&prompt.includes('特徵參數會消失')}
      finally{window.confirm=old;if(prior)fe.feats[1]=prior;else delete fe.feats[1]}
    })()`));
    await remainingShot('uiux-20260927-face-desktop');
    await send('Emulation.setDeviceMetricsOverride',{width:900,height:700,deviceScaleFactor:1,mobile:false});
    check('P64 R2 中寬面畫布與檢查器皆可操作',await eval_(`(()=>{
      const vp=$('faceEditorViewport'),v=vp.getBoundingClientRect(),i=document.querySelector('.face-inspector-panel').getBoundingClientRect();
      const hit=document.elementFromPoint(v.left+v.width/2,v.top+v.height/2);
      return v.width>250&&i.width>200&&i.right<=innerWidth+1&&vp.contains(hit)
        && $('objectWorkspace').scrollWidth<=$('objectWorkspace').clientWidth+1;})()`));
    await remainingShot('uiux-20260927-face-medium');
    await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});
    check('P64 R2 手機面畫布可點且無水平溢出',await eval_(`(()=>{
      const vp=$('faceEditorViewport'),r=vp.getBoundingClientRect(),hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);
      return r.width>innerWidth-2&&vp.contains(hit)&&document.documentElement.scrollWidth<=innerWidth+1;})()`));
    await remainingShot('uiux-20260927-face-mobile');
    await send('Emulation.setDeviceMetricsOverride',{width:1382,height:804,deviceScaleFactor:1,mobile:false});
    await setupRemaining(['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000','space 1 boundary 1']);
    await eval_(`(async()=>{await enterFocus('face',1);fiShowTab('timber')})()`);
    check('P64 T2 厚度側向有具體法向',await eval_(`[...$('tbSide').options].some(o=>o.textContent.includes('下')) && [...$('tbSide').options].some(o=>o.textContent.includes('上'))`));
    await eval_(`$('tbA').value='0';$('tbPlace').click()`);await sleep(250);
    check('P64 T3 無效截面不改世界',await eval_(`!fe.timbers.length && $('tbA').classList.contains('invalid')`));
    await eval_(`$('tbA').value='27';$('tbA').dispatchEvent(new Event('input',{bubbles:true}));$('tbPlace').click()`);
    await waitForUI(`fe.timbers.length===1`,5000);
    const t3=await eval_(`({timbers:fe.timbers.map(t=>({id:t.id,A:t.A})),tool:fe.tool,tab:fe.fiTab,status:$('status').textContent})`);
    check('P64 T3 表單直接放角材',t3.timbers.length===1&&t3.timbers[0].A===27&&t3.tool!=='timber',t3);
    check('P64 T1 手動改朝向與角色會撤除自動標記',await eval_(`(()=>{
      const a=$('tbDirAuto'),b=$('tbRoleAuto'),before=!a.hidden&&!b.hidden;
      $('tbDir').value='-u';$('tbDir').dispatchEvent(new Event('change',{bubbles:true}));
      $('tbRole').value='custom';$('tbRole').dispatchEvent(new Event('change',{bubbles:true}));
      return before&&a.hidden&&b.hidden;})()`));
    await eval_(`fe.sel={kind:'timber',id:fe.timbers[0].id};renderFaceInspector();feRunAction('edit')`);
    const t4=await eval_(`({tab:fe.fiTab,focus:document.activeElement.id,anchor:$('tbEditAnchor')?.value,note:$('tbSelected')?.textContent.includes('已帶入原定位引用')})`);
    check('P64 T4 編輯角材聚焦且明示已帶入原定位引用',t4.tab==='timber'&&t4.focus==='tbEditAnchor'&&!!t4.anchor&&t4.note,t4);
    const edgeTimber=await eval_(`(async()=>{const occupied=[...$('tbAnchor').options].find(o=>/^at-face e\\d+$/.test(o.value)&&o.textContent.includes('已有角材'));const i=occupied?((+occupied.value.match(/e(\\d+)$/)[1]+2)%4):0,free='at-face e'+i;fe.sel={kind:'edge',loop:0,i};await feRunAction('timber');return {n:fe.timbers.length,free,anchor:$('tbAnchor')?.value,dir:$('tbDir')?.value,side:$('tbSide')?.value,role:$('tbRole')?.value,toast:[...document.querySelectorAll('.toast')].map(e=>e.textContent)};})()`);
    check('P64 F2 邊浮動列可沿選邊放角材',edgeTimber.n===2&&edgeTimber.anchor===edgeTimber.free,edgeTimber);
    await setupRemaining(['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000','space 1 boundary 1']);
    check('P64 M8 空間卡顯示佔槽數與管理入口',await eval_(`(()=>{const s=document.querySelector('.ocard[data-kind="space"]')?.textContent||'';return s.includes('1／6 面')&&s.includes('管理成員面')&&!s.includes('缺 ');})()`));
    await eval_(`enterFocus('space',1)`);
    check('P64 S2 收成員在標題旁',await eval_(`$('spaceAddMembers').closest('.inner-section-title')?.contains($('spaceMemberCount'))`));
    await clickSelector('#spacePlaceColumn');
    check('P64 S1 平面放柱時尺寸在工具旁',await eval_(`!$('spaceSizeTools').hidden && $('spaceWorkspaceTools').contains($('spaceSizeTools'))`));
    await clickSelector('[data-ss-tab="proj"]');
    check('P64 S1 三視圖停用放置並說明',await eval_(`$('spacePlaceColumn').disabled && $('spacePlaceBeam').disabled && $('spaceSizeTools').hidden && $('workspaceToolStatus').textContent.includes('僅供檢視')`));
    await eval_(`leaveFocus()`);await clickSelector('#btnObj');await eval_(`v3SetTool('rect')`);
    check('P64 V1-V2 三視圖工作面、高度與 SVG 控制',await eval_(`!$('v3PlaneControls').hidden && $('v3ToolbarSurf').options.length>0 && document.querySelectorAll('#v3ZoomBar .v3-zoom button svg').length>=2`));
  }

  { // First-version space-model entry points; the full real-browser flow lives in space_model_test.js.
    console.log('=== P65. 從面建立 3D 空間入口 ===');
    const check=bodyCheck();
    await eval_(`leaveFocus();setView3(false)`);await sleep(200);
    check('P65-1 正式版本載入建模模組並提供現成範例入口',await eval_(`typeof SpaceModelWorkspace==='object' && typeof SpaceModelWorkspace.openCurrentFace==='function' && !!$('btnSpaceModelTrial') && !!$('btnSpaceModels') && $('btnSpaceModelTrial').textContent.includes('現成範例')`));
    /* 牙齒:入口存在但工作區點擊前必須是關的、入口標籤是真內容(3D 模型 <n>),否則 P65-1 只證明 id 在。 */
    const p65Entry=await eval_(`({open:document.getElementById('smWorkspace')?.open,count:document.getElementById('spaceModelCount')?.textContent,library:document.getElementById('btnSpaceModels')?.textContent})`);
    check('P65-1b 點擊前建模工作區關閉,模型庫入口顯示「3D 模型 <數量>」',p65Entry.open!==true && /^\d+$/.test(p65Entry.count||'') && /^3D 模型\s*\d+$/.test((p65Entry.library||'').trim()),p65Entry);
    await clickControl('#btnSpaceModelTrial');await sleep(200);
    check('P65-2 三步操作、範例與明示高度欄位皆在正式工作區',await eval_(`$('smWorkspace').open && !!$('smTryRectangle') && !!$('smTryLShape') && !!$('smBottom') && !!$('smHeight') && !!$('smPreview') && !!$('smConfirmFaces') && !!$('smCreate')`));
    /* 牙齒:點「現成範例」的可觀察結果(DOM-CONTRACT:96-100)——載入矩形範例並自動預覽:來源 example、牆高預設 3000、
       厚度 100、核心回傳閉合 6 面體(4 外環邊+底+頂)且面清單同步列出 6 面。 */
    await waitForUI(`SpaceModelWorkspace.snapshot().phase==='preview'`,15000);
    const p65Example=await eval_(`(()=>{const s=SpaceModelWorkspace.snapshot(),r=s.resultSummary||{};return {sourceKind:s.sourceKind,stale:s.stale,height:$('smHeight').value,thickness:$('smThickness').value,closed:r.closed,faceCount:r.face_count,top:r.top,listed:document.querySelectorAll('#smGeneratedFaces li').length};})()`);
    check('P65-2b 點現成範例後載入矩形範例並預覽出閉合 6 面體',p65Example.sourceKind==='example' && p65Example.stale===false && p65Example.height==='3000' && p65Example.thickness==='100' && p65Example.closed===true && p65Example.faceCount===6 && p65Example.top===3000 && p65Example.listed===6,p65Example);
    for (const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{type,key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    await sleep(100);
    check('P65-3 Esc 可關閉建模工作區',await eval_(`!$('smWorkspace').open`));
  }

  { // Projection metadata is explicit per face; full persistence is exercised by space_model_test.js.
    console.log('=== P66. 每面平面投影用途與建模守門 ===');
    const check=bodyCheck();
    const ctl=async selector=>{const r=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,hit:e.contains(document.elementFromPoint(x,y)),disabled:e.disabled};})()`);if(!r.hit||r.disabled)throw Error('Projection control unreachable '+selector);await click(r.x,r.y);await sleep(150);};
    await send('Emulation.setDeviceMetricsOverride',{width:1382,height:804,deviceScaleFactor:1,mobile:false});
    await eval_(`(async()=>{await leaveFocus();await setView3(false);await api('reset');await api('line surface 501 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000');await renderObjects();await enterFocus('face',501);})()`);
    check('P66-1 面工作區提供真正的投影設定入口（GEO-219：工具列鈕已移除，入口在屬性欄）',await eval_(`typeof FaceProjection==='object' && !$('btnFaceProjection') && !$('btnFaceSpaceModel') && !!document.querySelector('#faceInspectorContent [data-fp-edit]') && !!document.querySelector('#faceInspectorContent [data-fp-build]') && ReferenceWorkspace.getFaceProjection(501,501)==null`));
    await eval_(`fiShowTab('prop')`);await sleep(150);
    await ctl('#faceInspectorContent [data-fp-build]');
    await waitForUI(`$('smWorkspace').open && SpaceModelWorkspace.snapshot().phase==='ready'`);
    check('P66-2 未定義的自己面不偷推用途或方向',await eval_(`!$('smProjectionCallout').hidden && $('smPreview').disabled && $('smCreate').disabled`));
    await ctl('#smSetProjection');
    await waitForUI(`$('fpDialog')?.open`);
    check('P66-3 對話框明示位置、輪廓、用途、視向與內淨空',await eval_(`$('fpPurpose').value==='general' && !$('fpInterior').checked && /2500|2,500/.test($('fpZ').textContent) && !!$('fpOutline') && !!$('fpView') && !!$('fpPlacement')`));
    await ctl('#fpCancel');
    check('P66-4 取消設定不寫入任何投影定義',await eval_(`ReferenceWorkspace.getFaceProjection(501,501)==null && $('smPreview').disabled`));
    await ctl('#smClose');
  }

  }
  if (!process.env.GEOMETRY_SELECTION_CURSOR_ONLY && !process.env.GEOMETRY_UX_REFINEMENT_ONLY && !process.env.GEOMETRY_UIUX_FIX_ONLY && !process.env.GEOMETRY_MARQUEE_ONLY && !process.env.GEOMETRY_ENGINEERING_WORKFLOW_ONLY && !process.env.GEOMETRY_GRID_SYSTEM_ONLY && !process.env.GEOMETRY_INFINITE_FACE_ONLY && !process.env.GEOMETRY_COMPOSITION_ONLY)
    await require('./project_audit_test.js')({send,eval_,sleep,click,waitForUI,exceptionCount:()=>excN});
  if (!process.env.GEOMETRY_SELECTION_CURSOR_ONLY && !process.env.GEOMETRY_UX_REFINEMENT_ONLY && !process.env.GEOMETRY_UIUX_FIX_ONLY && !process.env.GEOMETRY_PROJECT_AUDIT_ONLY && !process.env.GEOMETRY_MARQUEE_ONLY && !process.env.GEOMETRY_GRID_SYSTEM_ONLY && !process.env.GEOMETRY_INFINITE_FACE_ONLY && !process.env.GEOMETRY_COMPOSITION_ONLY)
    await require('./engineering_workflow_test.js')({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount:()=>excN});
  if (!process.env.GEOMETRY_SELECTION_CURSOR_ONLY && !process.env.GEOMETRY_UX_REFINEMENT_ONLY && !process.env.GEOMETRY_UIUX_FIX_ONLY && !process.env.GEOMETRY_PROJECT_AUDIT_ONLY && !process.env.GEOMETRY_ENGINEERING_WORKFLOW_ONLY && !process.env.GEOMETRY_GRID_SYSTEM_ONLY && !process.env.GEOMETRY_INFINITE_FACE_ONLY && !process.env.GEOMETRY_COMPOSITION_ONLY)
    await require('./marquee_test.js')({send, eval_, sleep, click, dblclick, drag, dragMod, pressDownMod, moveMod, waitForUI, exceptionCount:()=>excN});
  if (scope.mode==='full' || process.env.GEOMETRY_GRID_SYSTEM_ONLY)
    await require('./grid_system_test.js')({send,eval_,sleep,click,drag,waitForUI,expectNativeDialog,exceptionCount:()=>excN});
  if (scope.mode==='full' || process.env.GEOMETRY_GRID_SYSTEM_ONLY)
    await require('./grid_rule_editor_test.js')({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount:()=>excN});
  if (scope.mode==='full' || process.env.GEOMETRY_GRID_SYSTEM_ONLY)
    await require('./grid_rule_lines_test.js')({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount:()=>excN});
  if (process.env.GEOMETRY_INFINITE_FACE_ONLY)
    await require('./infinite_grid_face_test.js')({send,eval_,sleep,click,waitForUI});
  if (scope.mode==='full' || process.env.GEOMETRY_COMPOSITION_ONLY)
    await require('./composition_canvas_test.js')({send,eval_,sleep,click,drag,waitForUI,exceptionCount:()=>excN});
  if (scope.mode==='full' || process.env.GEOMETRY_UIUX_FIX_ONLY)
    await require('./uiux_review_test.js')({send,eval_,sleep,click,waitForUI,captureNewToasts,expectNativeDialog,exceptionCount:()=>excN});
  if (scope.mode==='full' || process.env.GEOMETRY_UX_REFINEMENT_ONLY)
    await require('./ux_refinement_test.js')({send,eval_,sleep,click,waitForUI,captureNewToasts,expectNativeDialog,expectBeforeUnload:()=>{expectedBeforeUnloadUntil=Date.now()+15000;},exceptionCount:()=>excN});
  if (scope.mode==='full' || process.env.GEOMETRY_SELECTION_CURSOR_ONLY)
    await require('./selection_cursor_test.js')({send,eval_,sleep,click,drag,waitForUI,exceptionCount:()=>excN});

  }
  if(scope.mode==='full'||process.env.GEOMETRY_PARAMETERS_ONLY)await require('./parameter_workflow_test.js')({send,eval_,sleep,click,waitForUI,exceptionCount:()=>excN});
  if(scope.mode==='full'||process.env.GEOMETRY_ASSEMBLY_ONLY)await require('./assembly_workflow_test.js')({send,eval_,sleep,click,dblclick,drag,waitForUI,exceptionCount:()=>excN});
  if(scope.mode==='full'||process.env.GEOMETRY_ASSEMBLY_ONLY)await require('./assembly_context_entry_test.js')({send,eval_,sleep,click,waitForUI,exceptionCount:()=>excN});
  if(scope.mode==='full'||process.env.GEOMETRY_TIMBER_SCHEDULE_ONLY)await require('./timber_schedule_test.js')({send,eval_,sleep,click,waitForUI,exceptionCount:()=>excN});
  if(scope.mode==='full'||process.env.GEOMETRY_TIMBER_SCHEDULE_ONLY)await require('./cutting_plan_test.js')({send,eval_,sleep,click,waitForUI,exceptionCount:()=>excN});
  if(scope.mode==='full'||process.env.GEOMETRY_TIMBER_SCHEDULE_ONLY)await require('./timber_supports_browser_test.js')({send,eval_,sleep,click,waitForUI,exceptionCount:()=>excN});
  if(scope.mode==='full'||process.env.GEOMETRY_TIMBER_SCHEDULE_ONLY)await require('./source_navigation_test.js')({send,eval_,sleep,click,waitForUI,exceptionCount:()=>excN});
  }
  if(scope.mode==='full'||process.env.GEOMETRY_ROOM_OUTLINE_ONLY)await require('./room_outline_test.js')({send,eval_,sleep,click,drag,waitForUI,exceptionCount:()=>excN});
  if(scope.mode==='full')await require('./model_snapshot_schedule_test.js')({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount:()=>excN});
  if(scope.mode==='full')await require('./model_snapshot_navigation_test.js')({send,eval_,sleep,click,waitForUI,exceptionCount:()=>excN});
  chrome.kill();
  if(passN+failN===0){failN++;_log('No assertions executed');}
  const goldenCompare=evaluateSections();
  _log(`\n=== 結果:${passN} 通過斷言 / ${failN} 失敗斷言 / ${skipped.length} 略過群組 (${scope.mode}) ===`);
  _log('CDP_RESULT '+JSON.stringify({schema:'geometry-cdp-result/1',scope,completed:true,passedAssertions:passN,failedAssertions:failN,skipped,sections:sectionPass,...(Object.keys(sectionFail).length?{sectionsFailed:sectionFail}:{}),goldenCompare,uncaughtBrowserExceptions:excN,coverage:'Mixed trusted input, DOM/programmatic integration and native API checks; assertion counts are not end-to-end scenario counts.'}));
  process.exit(failN > 0 ? 1 : 0);
}
async function fatal(e) {
  _log("FATAL:", e.message);
  _log('FATAL_NETWORK:',JSON.stringify({failures:assetFailures,pendingAssets:[...assetRequests.values()]}));
  try {
    if(ws?.readyState===1){
      const state=await Promise.race([eval_(`({ready:document.readyState,focus:typeof oc==='object'?oc.focus:null,connection:typeof connection==='object'?{phase:connection.phase,error:connection.error}:null,events:window.geometryFeedback?.events?.slice(-10),dialogs:[...document.querySelectorAll('dialog[open]')].map(d=>({id:d.id,classes:d.className,text:d.textContent.slice(0,1200)})),active:document.activeElement?.id,feedback:document.querySelector('#fbPanel')?.hidden,status:document.querySelector('#status')?.textContent})`),delay(1500).then(()=>null)]);
      _log('FATAL_UI:',JSON.stringify(state));
      const capture=await Promise.race([send('Page.captureScreenshot',{format:'png'}),delay(1500).then(()=>null)]);
      if(capture?.result?.data&&process.env.GEOMETRY_REPAIR_SCREENSHOT_DIR){
        fs.mkdirSync(process.env.GEOMETRY_REPAIR_SCREENSHOT_DIR,{recursive:true});
        fs.writeFileSync(path.join(process.env.GEOMETRY_REPAIR_SCREENSHOT_DIR,'fatal-state.png'),Buffer.from(capture.result.data,'base64'));
      }
    }
  } catch(captureError) {_log('FATAL_CAPTURE_FAILED:',captureError.message);}
  finally {
    _log('CDP_RESULT '+JSON.stringify({schema:'geometry-cdp-result/1',scope,completed:false,passedAssertions:passN,failedAssertions:failN,fatal:e.message,skipped,sections:sectionPass,...(Object.keys(sectionFail).length?{sectionsFailed:sectionFail}:{}),currentSection,goldenCompare:'not compared (run did not complete)'}));
    chrome?.kill();process.exit(1);
  }
}
if(require.main===module){
  try {scope=runConfiguration();console.log=recordLog;(async()=>{await assertPortAvailable(PORT);chrome=startBrowser();chrome.on('error',fatal);_log('CDP_SCOPE '+JSON.stringify(scope));await main();})().catch(fatal);}
  catch(error){_log('CDP preflight failed:',error.message);process.exitCode=1;}
} else module.exports={runConfiguration,assertionVerdicts,evaluationValue,explicitVerdict,assertPortAvailable,verifyBrowserOwnership};
