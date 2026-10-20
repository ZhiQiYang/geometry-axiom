/* 外部診斷器：在記憶體擷取指定工作樹的原版 CDP helpers 與整段 P52；不改產品檔案。 */
'use strict';
const fs = require('fs');
const path = require('path');
const Module = require('module');
const cp = require('child_process');
const root = path.resolve(process.argv[2] || path.join(__dirname,'../../..'));
const repeatText=process.env.P52_REPEATS??'1';
if(!/^[1-9][0-9]*$/.test(repeatText)||!Number.isSafeInteger(Number(repeatText)))throw Error('P52_REPEATS 必須是安全範圍內的正整數，不可零輪或非數字');
const probeRepeats=Number(repeatText);
const sourcePath = path.join(root, 'geometry-web/cdp_test.js');
const actualSource = fs.readFileSync(sourcePath, 'utf8');
const ORIGINAL_WAIT = "    await sleep(400);\n    const g = await eval_(`(async()=>{ const refs = await apiRequest('references');\n      const t = (refs.timbers || []).find(x => x.id === 3); return t && t.geometry; })()`);";
const CANDIDATE_WAIT = [
  "    const g = await (async () => {",
  "      const deadline = Date.now() + 15000;",
  "      let last = { references: null, geometry: null, busyBefore: null, busy: null, toasts: null, phase: '尚未取樣' };",
  "      const timeout = () => Error('P52-5 等待 timber id=3 geometry 與放置完成逾時（15000ms）；最後狀態：' + JSON.stringify(last));",
  "      // 每次 CDP/API 共用同一截止時間；單次 references 卡住也不能拖長總上限。",
  "      const read = async expression => {",
  "        const remaining = deadline - Date.now();",
  "        if (remaining <= 0) throw timeout();",
  "        let timer;",
  "        try {",
  "          return await Promise.race([eval_(expression), new Promise((_, reject) => {",
  "            timer = setTimeout(() => reject(timeout()), remaining);",
  "          })]);",
  "        } finally { clearTimeout(timer); }",
  "      };",
  "      last = await read(`({ references: null, geometry: null, busyBefore: !!oc.busy, busy: !!oc.busy,",
  "        toasts: document.getElementById('toastRegion')?.textContent || '', phase: '首次讀取前' })`);",
  "      while (Date.now() < deadline) {",
  "        last.phase = 'references 回應等待中';",
  "        last = await read(`(async()=>{ const busyBefore = !!oc.busy;",
  "          const references = await apiRequest('references');",
  "          const timber = (references.timbers || []).find(x => x.id === 3);",
  "          return { references, geometry: timber?.geometry || null, busyBefore, busy: !!oc.busy,",
  "            toasts: document.getElementById('toastRegion')?.textContent || '', phase: 'references 已回應' }; })()`);",
  "        if (last.references?.ok !== true)",
  "          throw Error('P52-5 timber id=3 的 references 查詢失敗：' + JSON.stringify(last));",
  "        // 只等資料及交易就緒；幾何期望值仍交給下方原斷言判斷。",
  "        if (last.geometry && !last.busyBefore && !last.busy) return last.geometry;",
  "        await delay(Math.min(50, Math.max(0, deadline - Date.now())));",
  "      }",
  "      throw timeout();",
  "    })();"
].join('\n');
const originalCount=actualSource.split(ORIGINAL_WAIT).length-1;
const candidateCount=actualSource.split(CANDIDATE_WAIT).length-1;
if(originalCount+candidateCount!==1)throw Error('P52-5 等待標記必須唯一，且須是原版或已審候選');
if(process.env.P52_CANDIDATE_WAIT==='1'&&process.env.P52_WITHDRAW_WAIT==='1')throw Error('安裝候選與撤除修正不可同時使用');
const actualSourceHasCandidate=candidateCount===1;
let source=actualSource,memoryPatch='none';
if(process.env.P52_CANDIDATE_WAIT==='1'){
  if(actualSourceHasCandidate)throw Error('來源已套候選，請使用預設精確來源模式');
  source=source.replace(ORIGINAL_WAIT,CANDIDATE_WAIT);memoryPatch='install-candidate';
}
if(process.env.P52_WITHDRAW_WAIT==='1'){
  if(!actualSourceHasCandidate)throw Error('來源尚未套候選，不能宣稱撤除修正');
  source=source.replace(CANDIDATE_WAIT,ORIGINAL_WAIT);memoryPatch='withdraw-wait';
}
const effectiveWait=source.includes(CANDIDATE_WAIT)?CANDIDATE_WAIT:ORIGINAL_WAIT;
function between(start, end, from = 0) {
  const a = source.indexOf(start, from), b = source.indexOf(end, a + start.length);
  if (a < 0 || b < 0) throw Error('找不到原版擷取標記：' + start + ' / ' + end);
  return source.slice(a, b);
}
let prelude = source.slice(0, source.indexOf('async function main() {'));
const networkBranch="else if (['Network.requestWillBeSent'";
if(prelude.split(networkBranch).length!==2)throw Error('CDP 網路事件標記不是唯一');
prelude=prelude.replace(networkBranch,"else if(m.method==='Fetch.requestPaused')handleP52PausedRequest(m);\n          "+networkBranch);
const bootstrap = between('async function main() {', '  if (!process.env.GEOMETRY_ROOM_OUTLINE_ONLY) {');
const viewport = between('  const waitForFaceViewport = async () => {', '  const clickFacePoint = async');
const openFace = between('  const openFace48 = async () => {', '  const clearToasts48');
const setup = between('  const setupLinesG196 = async (lines)', '\n\n  /* helper 自測');
const fixture = between('  const F_SUPPORT = [', '  const enterTimber49');
let section = between("  console.log('=== P52.", '\n  }\n\n  if (!process.env.GEOMETRY_REFERENCE_ONLY)');
if(process.env.P52_TARGETED_CONTROL==='1'){
  const a=section.indexOf('    /* P52-3 矩陣把世界留在最後一個情境');
  const b=section.indexOf('\n  /* L 形',a);
  if(a<0||b<0)throw Error('找不到針對性控制的前置範圍');
  section=`  console.log('=== P52. 僅P52-4/5針對性控制，不冒充完整43斷言 ===');\n  {\n    await send('Emulation.setDeviceMetricsOverride', { width: 5400, height: 3800, deviceScaleFactor: 1, mobile: false });\n`+section.slice(a,b);
}
const originalAction = '    await click(pt48(2000, 1500).x, pt48(2000, 1500).y);';
if (section.split(originalAction).length !== 2) throw Error('P52-5 動作標記不是唯一');
section = section.replace(originalAction, `
    const clickPoint = pt48(2000,1500);
    await installP52Probe(clickPoint);
    await click(clickPoint.x, clickPoint.y);
    const sleepStarted = performance.now();probeWaitStarted=sleepStarted;`);
if(section.split(effectiveWait).length!==2)throw Error('P52-5 有效等待區塊不是唯一');
section=section.replace(effectiveWait,effectiveWait+`
    const waitAndReadMs=performance.now()-sleepStarted;
    console.log('P52_WAIT_COMPLETE '+JSON.stringify({waitAndReadMs,state:await eval_(probeStateExpression)}));`);
const originalCheck = `    check('P52-5 真實放置的 cross 足跡(核心) = 預示帶範圍 1987..2014',
      fxLo === 1987 && fxHi === 2014, { g });`;
if (section.split(originalCheck).length !== 2) throw Error('P52-5 斷言標記不是唯一');
section = section.replace(originalCheck, originalCheck + `
    await finishP52Probe();
    console.log('P52_PROBE_RESULT '+JSON.stringify({version:probeVersion,iteration,waitAndReadMs,assertionPassed:fxLo===1987&&fxHi===2014,activeSampling:process.env.P52_ACTIVE_SAMPLING==='1',probe:await eval_('window.__p52Probe'),state:await eval_(probeStateExpression)}));
    await eval_('apiRequest=window.__p52OriginalApi;void 0');`);

const instrumentation = String.raw`
const probeVersion=JSON.parse(process.env.P52_PROBE_VERSION);
let probeWaitStarted=0;
async function finishP52Probe(){
  let timer;
  try{
    await Promise.race([eval_('window.__p52Finish()'),new Promise((_,reject)=>{
      timer=setTimeout(()=>reject(Error('P52-5 診斷收尾逾時（15000ms）：timber id=3 的查詢或 busy 解除仍未完成')),15000);
    })]);
  }finally{clearTimeout(timer);}
}
async function closeProbeBrowser(){
  if(!chrome)return;
  const pid=chrome.pid,profile=scope.browserProfile;
  try{if(ws?.readyState===1)await Promise.race([send('Browser.close'),delay(1500)]);}catch(_){}
  if(chrome.exitCode===null)await Promise.race([new Promise(r=>chrome.once('exit',r)),delay(1500)]);
  if(chrome.exitCode===null){chrome.kill('SIGTERM');await Promise.race([new Promise(r=>chrome.once('exit',r)),delay(1000)]);}
  if(chrome.exitCode===null)chrome.kill('SIGKILL');
  console.log('P52_BROWSER_CLEANUP '+JSON.stringify({pid,profile,exitCode:chrome.exitCode,signalCode:chrome.signalCode}));
}
let networkDelayArmed=false;
function handleP52PausedRequest(message){
  const p=message.params;let cmd='';try{cmd=JSON.parse(p.request.postData||'{}').cmd||'';}catch(_){}
  const ms=networkDelayArmed&&cmd==='newid'?Number(process.env.P52_DELAY_NETWORK_MS||0):0;
  if(ms)networkDelayArmed=false;
  const resume=()=>send('Fetch.continueRequest',{requestId:p.requestId},message.sessionId).catch(fatal);
  if(ms){console.log('P52_NETWORK_DELAY '+JSON.stringify({command:cmd,delayMs:ms,requestId:p.requestId}));setTimeout(resume,ms);}
  else resume();
}
const probeStateExpression = "({busy:oc.busy,tool:fe.tool,focus:oc.focus,edit:oc.edit&&{bid:oc.edit.bid,contextId:oc.edit.contextId},connection:{phase:connection.phase,error:connection.error},referenceRevision:fe.referenceRevision,inputs:Object.fromEntries(['tbA','tbB','tbAnchor','tbSelector','tbDir','tbSide','tbRole','tbPri'].map(id=>[id,document.getElementById(id)?.value])),toasts:document.getElementById('toastRegion')?.textContent,events:window.geometryFeedback?.events?.slice(-12)})";
async function installP52Probe(point) {
  if(Number(process.env.P52_DELAY_NETWORK_MS||0)>0){networkDelayArmed=true;await send('Fetch.enable',{patterns:[{urlPattern:'*/api',requestStage:'Request'}]});}
  const before=await eval_(probeStateExpression);
  await eval_('('+function(point,before,delayMs,pollMs,activeSampling,control){
    const old=apiRequest;window.__p52OriginalApi=old;
    const p=window.__p52Probe={before,point,preparedAt:performance.now(),clickAt:null,rows:[],samples:[],done:false,delayMs,pollMs,activeSampling,control};
    const hit=document.elementFromPoint(point.x,point.y);
    p.hit=hit&&{tag:hit.tagName,id:hit.id,classes:hit.getAttribute('class'),faceHit:hit.closest('[data-face-hit]')?.dataset.faceHit};
    const observe=(r,start,source)=>{
      const timber=(r.timbers||[]).find(t=>t.id===3)||null;
      p.samples.push({source,start,at:performance.now(),ok:r.ok,busy:oc.busy,timberCount:r.timbers?.length,timber});
      if(timber&&p.firstTimberObservedMs===undefined)p.firstTimberObservedMs=performance.now()-p.clickAt;
      if(timber?.geometry&&p.firstGeometryObservedMs===undefined){p.firstGeometryObservedMs=performance.now()-p.clickAt;p.geometry=timber.geometry;}
      return timber;
    };
    apiRequest=async function(cmd,...args){
      const row={cmd,start:performance.now()};p.rows.push(row);
      try{
        if(cmd==='references'&&control==='hold')return await new Promise(()=>{});
        if(cmd==='references'&&control==='error'){row.end=performance.now();row.ok=false;row.error='探針刻意的 references API 失敗';return {ok:false,error:row.error};}
        if(cmd==='newid'&&delayMs)await new Promise(r=>setTimeout(r,delayMs));
        const r=await old(cmd,...args);row.end=performance.now();row.ok=r.ok;row.preview=!!r.preview;row.error=r.error;
        if(cmd==='references'&&control==='wrong-geometry'){
          const timber=(r.timbers||[]).find(t=>t.id===3);
          if(timber?.geometry)timber.geometry.origin[0]+=1;
        }
        if(cmd==='references')row.timber=observe(r,row.start,'原流程');
        return r;
      }catch(e){row.end=performance.now();row.error=e.message;throw e;}
    };
    const poll=async(source)=>{
      while(true){
        const start=performance.now();
        try{
          const r=await old('references');const timber=observe(r,start,source);
          if(timber?.geometry&&!oc.busy){p.done=true;return;}
        }catch(e){p.samples.push({source,start,at:performance.now(),error:e.message});}
        if(performance.now()-p.clickAt>=15000){p.timedOut=true;p.done=true;return;}
        await new Promise(r=>setTimeout(r,pollMs));
      }
    };
    window.__p52Finish=async()=>{
      p.originalReadFinishedAt=performance.now();
      if(activeSampling){while(!p.done)await new Promise(r=>setTimeout(r,20));}
      else if(!p.geometry||oc.busy)await poll('原斷言之後診斷');
      else p.done=true;
      if(p.timedOut)throw Error('P52-5 診斷未確認 timber id=3 geometry 與 busy 解除：'+JSON.stringify({geometry:p.geometry,busy:oc.busy,sample:p.samples.at(-1)}));
    };
    const onDown=e=>{
      document.removeEventListener('pointerdown',onDown,true);p.clickAt=performance.now();p.trusted=e.isTrusted;p.eventType=e.type;
      if(activeSampling)setTimeout(()=>poll('主動輪詢'),0);
    };
    document.addEventListener('pointerdown',onDown,true);
  }.toString()+')('+JSON.stringify(point)+','+JSON.stringify(before)+','+Number(process.env.P52_DELAY_NEWID_MS||0)+','+Number(process.env.P52_POLL_MS||50)+','+(process.env.P52_ACTIVE_SAMPLING==='1')+','+JSON.stringify(process.env.P52_REFERENCE_CONTROL||'')+')');
}
`;
const sha = cp.execFileSync('git', ['rev-parse', 'HEAD'], {cwd: root, encoding:'utf8'}).trim();
const status = cp.execFileSync('git', ['status','--short'], {cwd:root,encoding:'utf8'}).trim();
process.env.P52_PROBE_VERSION=JSON.stringify({root,sha,status,repeats:probeRepeats,actualSourceHasCandidate,memoryPatch,effectiveCandidateWait:effectiveWait===CANDIDATE_WAIT,targetedControl:process.env.P52_TARGETED_CONTROL==='1',referenceControl:process.env.P52_REFERENCE_CONTROL||'',sourceSha256:require('crypto').createHash('sha256').update(actualSource).digest('hex'),effectiveSourceSha256:require('crypto').createHash('sha256').update(source).digest('hex'),probeSha256:require('crypto').createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),candidateWaitSha256:require('crypto').createHash('sha256').update(CANDIDATE_WAIT).digest('hex')});
const runner = prelude + instrumentation + bootstrap + '\n' + viewport + openFace + setup + fixture + `
  const check=bodyCheck({detail:'empty',detailWhenPassing:true});let pt48;
  for(let iteration=1;iteration<=probeVersion.repeats;iteration++){
` + section + `
  }
  const expectedAssertions=(probeVersion.targetedControl?2:43)*probeVersion.repeats;
  if(passN+failN!==expectedAssertions)throw Error('P52 斷言數不符：預期 '+expectedAssertions+'，實際 '+(passN+failN));
  console.log('P52_PROBE_SUMMARY '+JSON.stringify({version:probeVersion,passedAssertions:passN,failedAssertions:failN,exceptions:excN}));
  await closeProbeBrowser();process.exit(failN||excN?1:0);
}
async function fatal(error){
  console.error('P52_PROBE_FATAL',error.stack||error.message);
  console.error('P52_PROBE_FATAL_TIMING',JSON.stringify({waitElapsedMs:probeWaitStarted?performance.now()-probeWaitStarted:null,version:probeVersion}));
  try{if(ws?.readyState===1)console.error('P52_PROBE_FATAL_STATE',JSON.stringify(await Promise.race([eval_(probeStateExpression),delay(1500).then(()=>({capture:'診斷超時'}))])));}catch(_){}
  await closeProbeBrowser();process.exit(1);
}
scope=runConfiguration();console.log=recordLog;
(async()=>{await assertPortAvailable(PORT);chrome=startBrowser();chrome.on('error',fatal);await main();})().catch(fatal);
`;
const target = new Module(sourcePath, module);
target.filename=sourcePath;
target.paths=Module._nodeModulePaths(path.dirname(sourcePath));
if(process.env.P52_PROBE_PARSE_ONLY==='1'){
  new Function('require','module','exports','__filename','__dirname',runner);
  console.log('P52 探針與擷取後程式語法檢查通過');
  process.exit(0);
}
target._compile(runner,sourcePath);
