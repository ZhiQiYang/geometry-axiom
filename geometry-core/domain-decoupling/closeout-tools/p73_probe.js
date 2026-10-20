/* P73 外部診斷：沿用正式 CDP 啟動與完整原模組；不修改工作樹。 */
'use strict';
const fs=require('fs'),path=require('path'),cp=require('child_process'),crypto=require('crypto'),Module=require('module');
const root=path.resolve(process.argv[2]||path.join(__dirname,'../../..'));
const harnessPath=path.join(root,'geometry-web/cdp_test.js'),harness=fs.readFileSync(harnessPath,'utf8');
const mode=process.env.P73_MODE||'minimal';
if(!['minimal','full','transition'].includes(mode))throw Error('P73_MODE 只接受 minimal、full 或 transition');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const appPath=path.join(root,'geometry-web/app.js'),appSource=fs.readFileSync(appPath,'utf8');
const oldGuard="  const svg=$('spacePlanSvg'),matrix=svg?.getScreenCTM();if(!svg||svg.hidden||!matrix)return;";
const newGuard="  const svg=$('spacePlanSvg');if(!svg||svg.hasAttribute('hidden')||!svg.hasAttribute('viewBox'))return;\n  const matrix=svg.getScreenCTM();if(!matrix)return;";
const oldMetrics='  empty.hidden = !noGeometry; svg.toggleAttribute("hidden", noGeometry);';
const newMetrics=oldMetrics+'\n  const metrics = $("spacePlanMetrics");\n  if (metrics) { metrics.hidden = noGeometry; if (noGeometry) metrics.textContent = ""; }';
const occurrences=(source,part)=>source.split(part).length-1;
const actualFixed=occurrences(appSource,newGuard)===1&&occurrences(appSource,newMetrics)===1&&occurrences(appSource,oldGuard)===0;
const actualOriginal=occurrences(appSource,oldGuard)===1&&occurrences(appSource,oldMetrics)===1&&occurrences(appSource,newMetrics)===0;
if(!actualFixed&&!actualOriginal)throw Error('app.js 不是唯一原版或已審候選片段');
const mutation=process.env.P73_APP_VARIANT||'none';
if(!['none','candidate','withdraw-guard','withdraw-metrics','withdraw-all'].includes(mutation))throw Error('P73_APP_VARIANT 不合法');
let effectiveApp=appSource;
if(mutation!=='none'){
  if(actualOriginal)effectiveApp=effectiveApp.replace(oldGuard,newGuard).replace(oldMetrics,newMetrics);
  if(mutation==='withdraw-guard'||mutation==='withdraw-all')effectiveApp=effectiveApp.replace(newGuard,oldGuard);
  if(mutation==='withdraw-metrics'||mutation==='withdraw-all')effectiveApp=effectiveApp.replace(newMetrics,oldMetrics);
}
if(mutation==='withdraw-all'&&actualOriginal&&effectiveApp!==appSource)throw Error('完整撤回沒有精確恢復原始位元組');
const callbackControl=process.env.P73_AFTER_EMPTY_SYNC==='1';
if(process.env.P73_AFTER_EMPTY_SYNC&&process.env.P73_AFTER_EMPTY_SYNC!=='1')throw Error('P73_AFTER_EMPTY_SYNC 只接受1');
const metadata={root,mode,sha:cp.execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),status:cp.execFileSync('git',['status','--short'],{cwd:root,encoding:'utf8'}).trim(),probeSha256:hash(fs.readFileSync(__filename)),sources:Object.fromEntries(['geometry-web/cdp_test.js','geometry-web/uiux_review_test.js','geometry-web/grid_workspace_draft_test.js','geometry-web/app.js','geometry-web/app.css'].map(p=>[p,hash(fs.readFileSync(path.join(root,p)))]))};
Object.assign(metadata,{mutation,callbackControl,actualFixed,actualAppSha256:hash(appSource),effectiveAppSha256:hash(effectiveApp)});
const marker='async function main() {',end='  if (!process.env.GEOMETRY_ROOM_OUTLINE_ONLY) {';
if(harness.split(marker).length!==2)throw Error('CDP main 標記不唯一');
const mainAt=harness.indexOf(marker),endAt=harness.indexOf(end,mainAt);
if(endAt<0)throw Error('CDP 啟動結尾不存在');
const snapshot=String.raw`(()=>{const svg=$('spacePlanSvg'),empty=$('spacePlanEmpty'),metrics=$('spacePlanMetrics'),visible=e=>{if(!e)return false;const s=getComputedStyle(e),r=e.getBoundingClientRect();return !e.hidden&&s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;},m=svg.getScreenCTM();return {at:performance.now(),ready:document.readyState,focus:oc.focus,busy:oc.busy,referenceBusy:ReferenceWorkspace.busy,memberCount:$('spaceMemberCount').textContent,svg:svg.outerHTML,svgHiddenPropertyType:typeof svg.hidden,svgHiddenProperty:svg.hidden??null,hasHidden:svg.hasAttribute('hidden'),viewBoxAttribute:svg.getAttribute('viewBox'),viewBoxBase:{x:svg.viewBox.baseVal.x,y:svg.viewBox.baseVal.y,width:svg.viewBox.baseVal.width,height:svg.viewBox.baseVal.height},svgDisplay:getComputedStyle(svg).display,screenCTM:m?{a:m.a,b:m.b,c:m.c,d:m.d,e:m.e,f:m.f}:null,svgBounds:svg.getBoundingClientRect().toJSON(),empty:empty?{text:empty.textContent,visible:visible(empty)}:null,metrics:metrics?{text:metrics.textContent,visible:visible(metrics),hidden:metrics.hidden}:null,space:oc.spaces.find(s=>s.id===990),columns:oc.columns.filter(c=>c.space===990),beams:oc.beams.filter(c=>c.space===990),originalPredicate:$('spaceMemberCount').textContent==='0'&&!svg.querySelector('polygon,rect,path')&&!!empty&&/加入|成員/.test(empty.textContent),mutations:window.__p73Mutations||null};})()`;
const extra=String.raw`
const probeMetadata=METADATA,probeSnapshot=SNAPSHOT,probeApp=APP_SOURCE;
let probeFailed=false;
let applicationSubstitutions=0,callbackControls=0;
async function pausedApplication(message){
  const p=message.params;
  if(new URL(p.request.url).pathname!=='/app.js')throw Error('不預期的app.js攔截路徑');
  if(p.responseStatusCode!==200)throw Error('app.js原回應非200：'+p.responseStatusCode);
  const body=(await send('Fetch.getResponseBody',{requestId:p.requestId})).result;
  const actual=body.base64Encoded?Buffer.from(body.body,'base64'):Buffer.from(body.body);
  const digest=require('crypto').createHash('sha256').update(actual).digest('hex');
  if(digest!==probeMetadata.actualAppSha256)throw Error('服務app.js與磁碟來源不相同：'+digest);
  applicationSubstitutions++;
  const headers=p.responseHeaders.filter(h=>!['content-length','content-encoding','transfer-encoding'].includes(h.name.toLowerCase()));
  await send('Fetch.fulfillRequest',{requestId:p.requestId,responseCode:200,responseHeaders:headers,body:Buffer.from(probeApp).toString('base64')});
  console.log('P73_APP_SOURCE '+JSON.stringify({actualSha256:digest,effectiveSha256:probeMetadata.effectiveAppSha256,mutation:probeMetadata.mutation}));
}
async function controlledEvaluate(expression){
  const result=await eval_(expression);
  if(probeMetadata.callbackControl&&expression.includes("await enterFocus('space',990)")){
    callbackControls++;await capture('控制前：原空態設定已完成');
    console.log('P73_CALLBACK_CONTROL '+JSON.stringify({kind:'明示手動執行產品原同步callback，模擬空態設定後的觀察器排程；不宣稱原fullcanvas逐次時序重演',expression:'syncSpacePlanAnnotations()'}));
    await eval_('syncSpacePlanAnnotations();void 0');await capture('控制後：原同步callback已執行');
  }
  return result;
}
async function capture(label){const value=await eval_(probeSnapshot);console.log('P73_DOM '+JSON.stringify({label,value}));return value;}
async function closeProbeBrowser(){
  if(!chrome)return true;
  const alive=()=>chrome.exitCode===null&&chrome.signalCode===null;
  const waitExit=async ms=>{if(alive())await Promise.race([new Promise(r=>chrome.once('exit',r)),delay(ms)]);};
  try{if(ws?.readyState===1)await Promise.race([send('Browser.close'),delay(1500)]);}catch(_){}
  await waitExit(1500);if(alive()){chrome.kill('SIGTERM');await waitExit(1000);}if(alive()){chrome.kill('SIGKILL');await waitExit(1000);}
  const exited=!alive();console.log('P73_BROWSER_CLEANUP '+JSON.stringify({pid:chrome.pid,profile:scope.browserProfile,exitCode:chrome.exitCode,signalCode:chrome.signalCode,exited}));return exited;
}
async function screenshot(label){if(!process.env.P73_SCREENSHOT_DIR)return;const response=await send('Page.captureScreenshot',{format:'png'});fs.mkdirSync(process.env.P73_SCREENSHOT_DIR,{recursive:true});fs.writeFileSync(path.join(process.env.P73_SCREENSHOT_DIR,label+'.png'),Buffer.from(response.result.data,'base64'));}
`.replace('METADATA',()=>JSON.stringify(metadata)).replace('SNAPSHOT',()=>JSON.stringify(snapshot)).replace('APP_SOURCE',()=>JSON.stringify(effectiveApp));
const networkBranch="else if (['Network.requestWillBeSent'";
let prelude=harness.slice(0,mainAt);
if(occurrences(prelude,networkBranch)!==1)throw Error('CDP網路事件標記不唯一');
prelude=prelude.replace(networkBranch,"else if(m.method==='Fetch.requestPaused')pausedApplication(m).catch(fatal);\n          "+networkBranch);
const navigation='  await send("Page.navigate", { url: process.env.GEOMETRY_TEST_URL || "http://localhost:8765/" });';
let bootstrap=harness.slice(mainAt,endAt);
if(occurrences(bootstrap,navigation)!==1)throw Error('CDP啟動導航不唯一');
bootstrap=bootstrap.replace(navigation,"  if(probeMetadata.mutation!=='none'){await send('Network.setCacheDisabled',{cacheDisabled:true});await send('Fetch.enable',{patterns:[{urlPattern:'*/app.js',resourceType:'Script',requestStage:'Response'}]});}\n"+navigation);
const runner=prelude+extra+bootstrap+String.raw`
  if(probeMetadata.mode==='minimal'){
    await eval_("window.__p73Mutations=[];window.__p73Observer=new MutationObserver(rows=>{for(const row of rows)__p73Mutations.push({at:performance.now(),type:row.type,attribute:row.attributeName,added:[...row.addedNodes].map(n=>n.outerHTML||n.textContent),removed:[...row.removedNodes].map(n=>n.nodeName)});});__p73Observer.observe($('spacePlanSvg'),{attributes:true,childList:true,subtree:true});void 0");
    await eval_("(async()=>{resetSceneFocus();await setView3(false);closePanels();for(const command of ['reset','line space 990']){const r=await api(command);if(!r.ok)throw Error(JSON.stringify(r));}await renderObjects();await enterFocus('space',990);return true;})()");
    await capture('空空間 enterFocus 完成');
    await eval_('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))');
    await capture('兩個真實動畫影格後');
    await screenshot('minimal-before-manual');
    await eval_('syncSpacePlanAnnotations();void 0');
    await capture('明示手動呼叫原 syncSpacePlanAnnotations 後');
    await screenshot('minimal-after-manual');
    await eval_('__p73Observer.disconnect();void 0');
  }else if(probeMetadata.mode==='transition'){
    const check=cdp.makeCheck({prefix:'P73 轉換 ',throwOnFail:true});
    const dump=()=>eval_("apiRequest('dump').then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r.text;})");
    await eval_("(async()=>{resetSceneFocus();await setView3(false);closePanels();for(const cmd of ['reset','line boundary 991 outline 0,0 1200,0 1200,800 0,800','line placement 991 on boundary 991 origin 0 0 0 u +x v +y','line space 989 boundary 991','line space 990']){const r=await api(cmd);if(!r.ok)throw Error(JSON.stringify(r));}await renderObjects();return true;})()");
    for(const [label,id] of [['非空',989],['空',990],['返回非空',989]]){
      await eval_("enterFocus('space',"+id+")");
      const before=await dump();
      await eval_('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))');
      const sample=await capture(label+'自然影格後');
      const actual=await eval_("(()=>{const s=$('spacePlanSvg'),m=$('spacePlanMetrics');return {shapes:!!s.querySelector('polygon,rect,path'),hasViewBox:s.hasAttribute('viewBox'),hidden:s.hasAttribute('hidden'),metricsHidden:m.hidden,metricsText:m.textContent,grid:!!s.querySelector('[data-plan-grid]')};})()");
      if(id===990)check(label+'原空態條件與尺寸文字均正確',sample.originalPredicate===true&&actual.hidden&&!actual.hasViewBox&&actual.metricsHidden&&actual.metricsText==='',actual);
      else check(label+'格線及尺寸文字恢復',actual.shapes&&actual.hasViewBox&&!actual.hidden&&actual.grid&&!actual.metricsHidden&&/mm/.test(actual.metricsText),actual);
      check(label+'等待與顯示未寫入World',before===await dump());
      await screenshot('transition-'+id+'-'+label);
    }
    if(passN!==6||failN)throw Error('轉換診斷預期6斷言');
  }else{
    await require('./uiux_review_test.js')({send,eval_:controlledEvaluate,sleep,click,waitForUI,captureNewToasts,expectNativeDialog,exceptionCount:()=>excN});
    if(passN+failN!==69||sectionPass.P73+((sectionFail.P73)||0)!==69)throw Error('P73 斷言數不符：預期69，實際'+(passN+failN));
  }
  if(probeMetadata.mutation!=='none'&&applicationSubstitutions!==1)throw Error('app.js記憶體替換次數不符：'+applicationSubstitutions);
  if(probeMetadata.callbackControl&&callbackControls!==1)throw Error('同步callback控制次數不符：'+callbackControls);
  console.log('P73_PROBE_RESULT '+JSON.stringify({metadata:probeMetadata,completed:true,passedAssertions:passN,failedAssertions:failN,exceptions:excN,sections:sectionPass}));
  if(!await closeProbeBrowser())throw Error('P73 瀏覽器尚未退出');process.exit(failN||excN?1:0);
}
async function fatal(error){
  if(probeFailed)return;probeFailed=true;
  console.error('P73_PROBE_FATAL',error.stack||error.message);
  try{await capture('致命失敗時');await screenshot('fatal-state');}catch(captureError){console.error('P73_CAPTURE_FAILED',captureError.message);}
  console.error('P73_PROBE_RESULT '+JSON.stringify({metadata:probeMetadata,completed:false,passedAssertions:passN,failedAssertions:failN,exceptions:excN,fatal:error.message,sections:sectionPass}));
  await closeProbeBrowser();process.exit(1);
}
scope=runConfiguration();if(scope.filters.length||scope.modifiers.length)throw Error('P73 探針不接受篩選旗標');scope.mode='p73-probe';console.log=recordLog;
console.log('P73_PROBE_SOURCE '+JSON.stringify(probeMetadata));
(async()=>{await assertPortAvailable(PORT);chrome=startBrowser();chrome.on('error',fatal);await main();})().catch(fatal);
`;
if(process.env.P73_PARSE_ONLY==='1'){new Function('require','module','exports','__filename','__dirname',runner);console.log('P73 探針語法檢查通過 '+JSON.stringify(metadata));process.exit(0);}
const loaded=new Module(harnessPath,module);loaded.filename=harnessPath;loaded.paths=Module._nodeModulePaths(path.dirname(harnessPath));loaded._compile(runner,harnessPath);
