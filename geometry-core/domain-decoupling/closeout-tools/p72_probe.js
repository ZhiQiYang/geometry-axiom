/* P72B 外部診斷器：執行指定來源完整 50 題；只在記憶體安裝／撤回導航等待。 */
'use strict';
const fs=require('fs'),path=require('path'),Module=require('module'),cp=require('child_process'),crypto=require('crypto');
const root=path.resolve(process.argv[2]||path.join(__dirname,'../../..'));
const harnessPath=path.join(root,'geometry-web/cdp_test.js'),pluginPath=path.join(root,'geometry-web/grid_inspector_rename_test.js');
const harness=fs.readFileSync(harnessPath,'utf8'),original=fs.readFileSync(pluginPath,'utf8');
const anchor="  const originalRuntime=await runtime();";
const helper=[
  "  const navigate=async(method,params,label)=>{",
  "    const marker=crypto.randomUUID();",
  "    const installed=await send('Page.addScriptToEvaluateOnNewDocument',{source:`window.__cdpExpectedNavigationMarker=${JSON.stringify(marker)}`});",
  "    let navigationError;",
  "    try{",
  "      await send(method,params);",
  "      await require('./cdp_navigation.js').waitForExpectedNavigation({evaluate:read,marker,",
  "        condition:`typeof oc!=='undefined'&&typeof ReferenceWorkspace!=='undefined'&&typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy`,",
  "        label,timeout:20000});",
  "    }catch(error){navigationError=error;throw error;}",
  "    finally{",
  "      try{await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:installed.result.identifier});}",
  "      catch(cleanupError){",
  "        if(navigationError)throw new AggregateError([navigationError,cleanupError],navigationError.message+'；P72B 導航標記清理也失敗：'+cleanupError.message);",
  "        throw cleanupError;",
  "      }",
  "    }",
  "  };"
].join('\n');
const oldOpen=[
  "  if(freshURL){const target=new URL(freshURL);if(target.href===new URL(originalURL).href)throw Error('Fresh service must have a distinct URL');await send('Page.navigate',{url:target.href});}",
  "  else await send('Page.reload');",
  "  await wait(`typeof ReferenceWorkspace!=='undefined'&&typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy`);await settle();"
].join('\n');
const newOpen=[
  "  if(freshURL){const target=new URL(freshURL);if(target.href===new URL(originalURL).href)throw Error('Fresh service must have a distinct URL');await navigate('Page.navigate',{url:target.href},'P72B 第二服務開檔前');}",
  "  else await navigate('Page.reload',{},'P72B 重載後開檔前');",
  "  await settle();"
].join('\n');
const oldReturn="  if(freshURL){await send('Page.navigate',{url:originalURL});await wait(`typeof ReferenceWorkspace!=='undefined'&&typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy`);}";
const newReturn="  if(freshURL)await navigate('Page.navigate',{url:originalURL},'P72B 返回原服務');";
const count=(s,x)=>s.split(x).length-1;
const oldSource=count(original,anchor)===1&&count(original,oldOpen)===1&&count(original,oldReturn)===1&&count(original,helper)===0;
const fixedSource=count(original,anchor)===1&&count(original,newOpen)===1&&count(original,newReturn)===1&&count(original,helper)===1;
if(!oldSource&&!fixedSource)throw Error('P72B 導航片段不是唯一已審原版或候選；整檔版本另由收據雜湊識別');
for(const flag of ['P72B_CANDIDATE_NAVIGATION','P72B_WITHDRAW_NAVIGATION','P72B_PROBE_PARSE_ONLY'])if(process.env[flag]&&process.env[flag]!=='1')throw Error(flag+' 只接受 1');
if(process.env.P72B_CANDIDATE_NAVIGATION&&process.env.P72B_WITHDRAW_NAVIGATION)throw Error('不可同時安裝與撤回導航等待');
let effective=original,memoryPatch='none';
if(process.env.P72B_CANDIDATE_NAVIGATION){
  if(!oldSource)throw Error('來源已修正，請使用預設精確來源模式');
  effective=effective.replace(anchor,helper+'\n'+anchor).replace(oldOpen,newOpen).replace(oldReturn,newReturn);memoryPatch='install-navigation';
}
if(process.env.P72B_WITHDRAW_NAVIGATION){
  if(!fixedSource)throw Error('來源尚未修正，不得宣稱撤回自證');
  effective=effective.replace(helper+'\n','').replace(newOpen,oldOpen).replace(newReturn,oldReturn);memoryPatch='withdraw-navigation';
}
const control=process.env.P72B_NAV_CONTROL||'none';
if(!['none','stale-first','hold-document'].includes(control))throw Error('P72B_NAV_CONTROL 只接受 none、stale-first、hold-document');
const effectiveFixed=effective.includes(helper);
if(control!=='none'&&process.env.GEOMETRY_GRID_RENAME_FRESH_URL)throw Error('導航注入控制只用同服務 reload；第二服務請單獨跑正常50題');
if(control==='hold-document'&&!effectiveFixed)throw Error('hold-document 只驗候選的導航就緒等待期限；需有導航修正');
const digest=s=>crypto.createHash('sha256').update(s).digest('hex');
const metadata={root,sha:cp.execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),status:cp.execFileSync('git',['status','--short'],{cwd:root,encoding:'utf8'}).trim(),memoryPatch,actualSourceHasCandidate:fixedSource,effectiveFixed,control,sourceSha256:digest(original),effectiveSourceSha256:digest(effective),harnessSha256:digest(harness),probeSha256:digest(fs.readFileSync(__filename))};
const mainMarker='async function main() {',bootstrapEnd='  if (!process.env.GEOMETRY_ROOM_OUTLINE_ONLY) {';
if(count(harness,mainMarker)!==1)throw Error('CDP main 標記不是唯一');
const mainAt=harness.indexOf(mainMarker),endAt=harness.indexOf(bootstrapEnd,mainAt);
if(endAt<0)throw Error('找不到 CDP 啟動範圍');
let prelude=harness.slice(0,mainAt);
const networkBranch="else if (['Network.requestWillBeSent'";
if(count(prelude,networkBranch)!==1)throw Error('CDP 網路事件標記不是唯一');
prelude=prelude.replace(networkBranch,"else if(m.method==='Fetch.requestPaused')onProbePaused(m).catch(fatal);\n          "+networkBranch);
const instrumentation=String.raw`
const probeMetadata=PROBE_METADATA;
const moduleSource=MODULE_SOURCE;
let navigationControl=null,probeFailed=false;
const probeLog=(event,data={})=>console.log('P72B_NAV_CONTROL '+JSON.stringify({event,at:performance.now(),...data}));
async function waitControl(condition,label,timeout=5000){
  const end=performance.now()+timeout;
  while(performance.now()<end){if(condition())return;await delay(10);}
  throw Error('P72B 控制設置逾時：'+label);
}
async function onProbePaused(message){
  const p=message.params,s=navigationControl;
  if(!s)return send('Fetch.continueRequest',{requestId:p.requestId});
  if(p.resourceType==='Document'&&!s.documentRequest){s.documentRequest=p.requestId;probeLog('真實文件請求暫停',{url:p.request.url});return;}
  if(new URL(p.request.url).pathname.endsWith('/app.js')&&!s.scriptRequest){s.scriptRequest=p.requestId;probeLog('真實app.js請求暫停',{url:p.request.url});return;}
  await send('Fetch.continueRequest',{requestId:p.requestId});
}
async function probeSend(method,params={}){
  if(method==='Page.reload'&&probeMetadata.control!=='none'&&!navigationControl){
    navigationControl={marker:require('crypto').randomUUID(),released:false};
    const s=navigationControl;
    s.markerScript=(await send('Page.addScriptToEvaluateOnNewDocument',{source:'window.__p72ProbeDocumentMarker='+JSON.stringify(s.marker)})).result.identifier;
    await send('Network.setCacheDisabled',{cacheDisabled:true});
    await send('Fetch.enable',{patterns:[{urlPattern:'*',resourceType:'Document',requestStage:'Request'},{urlPattern:'*/app.js*',resourceType:'Script',requestStage:'Request'}]});
    const response=await send(method,params);
    await waitControl(()=>!!s.documentRequest,'reload 真實文件請求');
    return response;
  }
  return send(method,params);
}
async function probeEvaluate(expression){
  const s=navigationControl;
  if(!s||s.released||!expression.includes("typeof ReferenceWorkspace"))return eval_(expression);
  const actual=await eval_(expression);
  const oldPage=await eval_("({ready:document.readyState,oc:typeof oc,connection:typeof connection==='undefined'?null:connection.phase})");
  probeLog('舊頁真實條件值',{value:actual,expression,oldPage});
  if(oldPage.ready!=='complete'||oldPage.oc!=='object'||oldPage.connection!=='ready'||actual!==!probeMetadata.effectiveFixed)
    throw Error('P72B 控制未建立舊頁就緒且候選標記不符的條件：'+JSON.stringify({oldPage,actual,effectiveFixed:probeMetadata.effectiveFixed}));
  if(probeMetadata.control==='hold-document'){s.released=true;probeLog('保持文件暫停直到候選期限');return actual;}
  s.released=true;
  await send('Fetch.continueRequest',{requestId:s.documentRequest});
  await waitControl(()=>!!s.scriptRequest,'新頁 app.js 請求');
  const incomplete=await eval_("({marker:window.__p72ProbeDocumentMarker,ready:document.readyState,oc:typeof oc})");
  if(incomplete.marker!==s.marker||incomplete.ready==='complete'||incomplete.oc!=='undefined')throw Error('P72B 控制未建立新頁尚未宣告oc的條件：'+JSON.stringify(incomplete));
  probeLog('確認新頁app.js未執行',{...incomplete,oldConditionValue:actual});
  s.releaseTimer=setTimeout(()=>send('Fetch.continueRequest',{requestId:s.scriptRequest}).then(()=>probeLog('釋放app.js')).catch(fatal),1200);
  // 回傳瀏覽器實際算出的原值；不偽造舊頁 true 或候選 false。
  return actual;
}
async function probeWaitForUI(expression,timeout=5000){
  if(!navigationControl)return waitForUI(expression,timeout);
  const end=Date.now()+timeout;
  while(Date.now()<end){if(await probeEvaluate(expression)===true)return;await sleep(50);}
  throw Error('UI condition timed out at '+currentTestStep+': '+expression);
}
async function closeProbeBrowser(){
  if(navigationControl?.releaseTimer)clearTimeout(navigationControl.releaseTimer);
  if(!chrome)return true;
  const alive=()=>chrome.exitCode===null&&chrome.signalCode===null;
  const waitExit=async ms=>{if(alive())await Promise.race([new Promise(r=>chrome.once('exit',r)),delay(ms)]);};
  try{if(ws?.readyState===1)await Promise.race([send('Browser.close'),delay(1500)]);}catch(_){}
  await waitExit(1500);
  if(alive()){chrome.kill('SIGTERM');await waitExit(1000);}
  if(alive()){chrome.kill('SIGKILL');await waitExit(1000);}
  const exited=!alive();
  console.log('P72B_BROWSER_CLEANUP '+JSON.stringify({pid:chrome.pid,profile:scope.browserProfile,exitCode:chrome.exitCode,signalCode:chrome.signalCode,exited}));
  return exited;
}
function loadProbeModule(){
  const filename=path.join(probeMetadata.root,'geometry-web/grid_inspector_rename_test.js');
  const Plugin=require('module'),loaded=new Plugin(filename,module);
  loaded.filename=filename;loaded.paths=Plugin._nodeModulePaths(path.dirname(filename));loaded._compile(moduleSource,filename);return loaded.exports;
}
`.replace('PROBE_METADATA',()=>JSON.stringify(metadata)).replace('MODULE_SOURCE',()=>JSON.stringify(effective));
const runner=prelude+instrumentation+harness.slice(mainAt,endAt)+String.raw`
  await loadProbeModule()({send:probeSend,eval_:probeEvaluate,sleep,click,waitForUI:probeWaitForUI,expectNativeDialog,exceptionCount:()=>excN});
  if(passN+failN!==50||sectionPass.P72B+((sectionFail.P72B)||0)!==50)throw Error('P72B 斷言數不符：預期50，實際'+(passN+failN));
  if(probeMetadata.control!=='none'&&!navigationControl)throw Error('P72B 預期導航注入未執行');
  console.log('P72B_PROBE_RESULT '+JSON.stringify({metadata:probeMetadata,completed:true,passedAssertions:passN,failedAssertions:failN,exceptions:excN,sections:sectionPass}));
  if(!await closeProbeBrowser())throw Error('P72B 專用瀏覽器尚未確認退出，不能宣稱完成清理');
  process.exit(failN||excN?1:0);
}
async function fatal(error){
  if(probeFailed)return;probeFailed=true;
  console.error('P72B_PROBE_FATAL',error.stack||error.message);
  console.error('P72B_PROBE_RESULT '+JSON.stringify({metadata:probeMetadata,completed:false,passedAssertions:passN,failedAssertions:failN,exceptions:excN,fatal:error.message}));
  await closeProbeBrowser();process.exit(1);
}
scope=runConfiguration();
if(scope.filters.length||scope.modifiers.length)throw Error('P72B 外部診斷器固定完整50題，不接受其他suite篩選旗標');
scope.mode='p72b-probe';console.log=recordLog;
console.log('P72B_PROBE_SOURCE '+JSON.stringify(probeMetadata));
(async()=>{await assertPortAvailable(PORT);chrome=startBrowser();chrome.on('error',fatal);await main();})().catch(fatal);
`;
if(process.env.P72B_PROBE_PARSE_ONLY==='1'){
  new Function('require','module','exports','__filename','__dirname',effective);
  new Function('require','module','exports','__filename','__dirname',runner);
  console.log('P72B 模組與擷取後程式語法檢查通過 '+JSON.stringify(metadata));process.exit(0);
}
const loaded=new Module(harnessPath,module);loaded.filename=harnessPath;loaded.paths=Module._nodeModulePaths(path.dirname(harnessPath));loaded._compile(runner,harnessPath);
