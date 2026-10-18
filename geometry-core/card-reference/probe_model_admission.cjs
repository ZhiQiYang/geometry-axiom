// P-154: run the delivered client admission path against a private real service.
// Reuse the existing test VM harness without registering its test cases.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const path=require('node:path'),os=require('node:os'),net=require('node:net');
const {spawn}=require('node:child_process'),{createRequire}=require('node:module');
const crypto=require('node:crypto').webcrypto;
const ROOT=path.resolve(__dirname,'../..'),P=require(path.join(ROOT,'geometry-web/project-store.js'));
const zip=require(path.join(ROOT,'geometry-web/vendor/fflate/umd/index.js'));
const output=path.resolve(process.argv[2]);fs.mkdirSync(output,{recursive:false});
const omit=process.argv.includes('--omit-verification');
const harnessPath=path.join(ROOT,'tests/test_engineering_project_store.js');
const harness=fs.readFileSync(harnessPath,'utf8');
const start=harness.indexOf('function workspace('),end=harness.indexOf("\ntest('draft API",start);
assert(start>=0&&end>start);
const original=fs.readFileSync(path.join(ROOT,'geometry-web/reference-workspace.js'),'utf8');
const marker='await verifyStoredModel(model);assertCurrent();';
assert.equal(original.split(marker).length,2,'one model admission guard');
const workspaceText=omit?original.replace(marker,'assertCurrent();'):original;
const realFS={...fs,readFileSync:(p,...rest)=>path.resolve(p)===path.join(ROOT,'geometry-web/reference-workspace.js')?workspaceText:fs.readFileSync(p,...rest)};
const create=new Function('P','vm','fs','zip','crypto','geometry','require',harness.slice(start,end)+'\nreturn workspace;');
const workspace=create(P,vm,realFS,zip,crypto,'boundary 1 outline 0,0 100,0 100,100 0,100\n',createRequire(harnessPath));
const sha=b=>require('node:crypto').createHash('sha256').update(b).digest('hex');
let server,report={omit_verification:omit,client_sha256:sha(original),harness_sha256:sha(harness),requests:[]};
(async()=>{
  assert(process.env.GEOMETRY_BRIDGE&&process.env.GEOMETRY_MODEL_BASE,'Explicit fresh binaries are required');
  const port=await new Promise((resolve,reject)=>{const s=net.createServer();s.on('error',reject);s.listen(0,'127.0.0.1',()=>{const port=s.address().port;s.close(()=>resolve(port));});});
  const feedback=fs.mkdtempSync(path.join(os.tmpdir(),'p154-admission-'));
  server=spawn(process.env.PYTHON||'python',['geometry-web/serve.py',String(port)],{cwd:ROOT,env:{...process.env,GEOMETRY_FEEDBACK_DIR:feedback},stdio:['ignore','pipe','pipe']});
  const stdout=fs.createWriteStream(path.join(output,'server.stdout')),stderr=fs.createWriteStream(path.join(output,'server.stderr'));
  server.stdout.pipe(stdout);server.stderr.pipe(stderr);
  const fetchLocal=(url,options={})=>fetch('http://127.0.0.1:'+port+url,{...options,signal:options.signal||AbortSignal.timeout(30000)});
  let ready=false;
  for(let n=0;n<100;n++){
    if(server.exitCode!==null)throw Error('private server exited');
    try{ready=(await fetchLocal('/model/capabilities',{signal:AbortSignal.timeout(500)})).ok;}catch{}
    if(ready)break;await new Promise(resolve=>setTimeout(resolve,50));
  }
  assert(ready,'private service must start');
  const backend=async(url,options)=>{
    const response=await fetchLocal(url,options),value=await response.clone().json();
    report.requests.push({url,http:response.status,status:value.status,diagnostics:value.diagnostics?.map(d=>({code:d.code,message:d.message}))});
    return response;
  };
  const bytes=fs.readFileSync(path.join(ROOT,'geometry-web/examples/space-model-v1.gcanvas'));
  const loaded=await P.unpack(bytes,zip),manifest=loaded.manifest;
  const model=manifest.models[0],pkg=model.result.space;
  pkg.manifest.axiom_revision='651c661b2c4c224c58bb4a2ed0a42ed929a16aa6';
  pkg.manifest.axiom_sha256='ab31dc36d5416762ac44932940a94f6142b72e831ceb62c0bc67375512109004';
  pkg.manifest.capabilities.push('grid-card-reference/1');
  P.validateModelPackage(pkg); // Structural admission deliberately cannot certify semantic versions.
  const poisoned=await P.pack(loaded.scene,manifest,loaded.sources,zip);
  await P.unpack(poisoned,zip);
  const w=workspace(undefined,backend),state=JSON.stringify(w.api.getProjectState()),context=w.api.context().id;
  const undo=w.api.history.undo.length;
  const dump=async()=> (await (await fetchLocal('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd:'dump'})})).json()).text;
  const before=await dump();
  let rejected=false,error='';
  try{await w.api.importBytes(poisoned,'P154 old-axiom card model');}catch(e){rejected=true;error=e.message;}
  report={...report,rejected,error,calls:w.calls,context_unchanged:w.api.context().id===context,
    state_unchanged:JSON.stringify(w.api.getProjectState())===state,
    history_unchanged:w.api.history.undo.length===undo,models:w.api.getSpaceModels().length,
    dump_unchanged:await dump()===before};
  assert(rejected,'P154_MODEL_ADMISSION: old-version card model must be refused');
  assert.match(error,/grid-card-reference\/1/,'P154_MODEL_ADMISSION: native version diagnostic');
  assert.deepEqual(w.calls,['/model/verify'],'P154_MODEL_ADMISSION: refuse before upload or replay');
  assert(report.requests[0].diagnostics.some(d=>d.code==='AXIOM_VERSION'),'P154_MODEL_ADMISSION: actual native verifier');
  assert(report.context_unchanged&&report.state_unchanged&&report.history_unchanged&&report.dump_unchanged&&report.models===0,'P154_MODEL_ADMISSION: preserve current project');
  report.exit_code=0;
})().catch(error=>{report.exit_code=1;report.failure=error.stack;process.exitCode=1;}).finally(async()=>{
  if(server&&server.exitCode===null){server.kill('SIGTERM');await new Promise(resolve=>server.once('exit',resolve));}
  fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report));
});
