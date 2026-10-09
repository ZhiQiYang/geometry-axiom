/* Caller-approved bounded normal UI probe; isolated service only. No full claim. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const {chromium}=require('playwright');
const ROOT=path.resolve(process.env.GEOMETRY_REPO||''),SHA=process.env.GEOMETRY_EXPECTED_SHA,URL=process.env.GEOMETRY_TEST_URL;
const OUT=path.resolve(process.env.GEOMETRY_SHELL_RETURN_OUT||'');
const HELPER='<workspace-path>';
const HELPER_SHA='020f542a86fd5d3fd581575acbce5e05e3d634775875cd4b4467843477527cee';
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const git=a=>execFileSync('git',a,{cwd:ROOT,encoding:'utf8'}).trim();
if(process.env.GEOMETRY_ISOLATED_SERVICE!=='1'||!/^[a-f0-9]{40}$/.test(SHA||''))throw Error('Explicit isolated full SHA required');
const address=new globalThis.URL(URL);
if(address.protocol!=='http:'||!['localhost','127.0.0.1'].includes(address.hostname)||address.port!=='19180'||address.pathname!=='/')throw Error('Dedicated caller-owned19180 service required');
if(!OUT.startsWith(os.tmpdir()+path.sep)||fs.existsSync(OUT))throw Error('New TEMP output required');
if(sha(HELPER)!==HELPER_SHA||git(['rev-parse','HEAD'])!==SHA||git(['status','--porcelain']))throw Error('Frozen clean candidate and immutable completion-aware helper required');
const sourcePaths=['geometry-web/assembly-workspace.js','geometry-web/assembly-workspace.css','geometry-web/section-profile-workspace.js','geometry-web/section-profile-workspace.css','geometry-web/workspace-shell.js','geometry-web/workspace-shell.css','geometry-web/index.html'];
const started={utc:new Date().toISOString(),head:git(['rev-parse','HEAD']),dirty:git(['status','--porcelain']),command:[process.execPath,...process.argv.slice(1)],node:{path:process.execPath,sha256:sha(process.execPath),version:process.version},driverSHA256:sha(__filename),helperSHA256:sha(HELPER),sourceHashes:Object.fromEntries(sourcePaths.map(rel=>[rel,sha(path.join(ROOT,rel))]))};
let browser,page,probe=null,error=null;const errors=[];
(async()=>{
 try{
  browser=await chromium.launch({executablePath:'/usr/bin/chromium',chromiumSandbox:true,headless:true});
  const context=await browser.newContext({viewport:{width:1400,height:1000},deviceScaleFactor:1});
  page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(URL);await page.waitForFunction(()=>connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy,null,{timeout:20000});
  const precondition=await page.evaluate(async()=>{const state=await apiRequest('section-profile-read');if(!state.ok||!Array.isArray(state.state?.profiles))throw Error('Actual section profile read unavailable');return {profiles:state.state.profiles.length,runtime:await(await fetch('/runtime')).json(),native:(await api('dump')).text};});
  started.nativePrecondition=precondition;
  // The original empty SP entry creates a local draft and requires its existing
  // Cancel before close. Disclose/require this fixture, never reset or inject it.
  if(precondition.profiles!==0||precondition.runtime.root!==ROOT||precondition.runtime.fresh!==true||precondition.runtime.version!=='efbcfff4ca94d6a1844228ea59628ee5de24dcd5e337c62f9c0587f5a38c8a11')throw Error('Fresh isolated zero-profile fixture and exact f3b runtime required; no reset performed');
  const helper=require(HELPER);
  try{probe=await helper({page,root:ROOT,expectedSHA:SHA,url:URL,output:OUT,isolatedService:true});}
  catch(e){probe=e.probeReceipt||(fs.existsSync(path.join(OUT,'results.json'))?JSON.parse(fs.readFileSync(path.join(OUT,'results.json'))):null);throw e;}
  const finalNative=await page.evaluate(async()=>{const r=await api('dump');if(!r.ok)throw Error('Final native dump unavailable');return r.text;});
  started.finalNativeMatchesBaseline=finalNative===precondition.native;
  if(!started.finalNativeMatchesBaseline)throw Error('Bounded normal entry/return changed original full native dump');
 }catch(e){error={message:e.message,stack:e.stack};}
 finally{if(browser)await browser.close();}
 if(!fs.existsSync(OUT))fs.mkdirSync(OUT,{recursive:false});
 const checks=probe?.checks||[],passed=checks.filter(c=>c.ok===true).length,failed=checks.filter(c=>c.ok!==true).length;
 const cases=[{width:1400,family:'ASM'},{width:1400,family:'SP'},{width:390,family:'ASM'},{width:390,family:'SP'}];
 const completed=!error&&errors.length===0&&probe?.completed===true&&checks.length===40&&failed===0&&JSON.stringify((probe.results||[]).map(({width,family})=>({width,family})))===JSON.stringify(cases);
 const exitCode=completed?0:1;
 const record={schema:'geometry-normal-shell-return-driver/1',started,finished:{utc:new Date().toISOString(),head:git(['rev-parse','HEAD']),dirty:git(['status','--porcelain']),driverSHA256:sha(__filename),helperSHA256:sha(HELPER)},scope:{mode:'bounded-normal-shell-return',cases,fixture:'Fresh isolated zero native section profiles; normal SP Cancel; no programmatic geometry or UI state writes',notCovered:['full CDP/golden','standalone Space','all43/privateZIP','physical touch/IME']},completed,passed,failed,checks:checks.length,helperProbePath:path.join(OUT,'results.json'),helperProbeSHA256:fs.existsSync(path.join(OUT,'results.json'))?sha(path.join(OUT,'results.json')):null,error,errors,sandbox:true,exitCode};
 fs.writeFileSync(path.join(OUT,'driver-receipt.json'),JSON.stringify(record,null,2)+'\n');
 console.log('SHELL_RETURN_RESULT '+JSON.stringify({schema:record.schema,completed,passed,failed,checks:checks.length,cases,scope:record.scope,exitCode,error,errors,sandbox:true,driverSHA256:record.started.driverSHA256,helperSHA256:record.started.helperSHA256}));
 process.exitCode=exitCode;
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
