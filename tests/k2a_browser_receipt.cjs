'use strict';
// Shared harness, not a suite. Each gate counts actual assertions separately.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..'),hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const git=(...args)=>cp.execFileSync('git',args,{cwd:root,encoding:'utf8',maxBuffer:64*1024*1024}).trim();
function snapshot(){return {head:git('rev-parse','HEAD'),tree:git('rev-parse','HEAD^{tree}'),status:git('status','--porcelain'),sources:Object.fromEntries(git('ls-files','current_geometry.c','geometry-web','geometry-core','tests').split('\n').filter(p=>p&&!p.startsWith('tests/evidence/')&&!p.startsWith('geometry-web/docs/')&&/\.(?:c|h|inc|py|js|cjs|css|html|json)$/.test(p)).map(p=>[p,hash(path.join(root,p))]))};}
exports.begin=async function(url){
  const assert=require('node:assert/strict'),expected=process.env.GEOMETRY_EXPECTED_SHA;
  assert.match(expected||'',/^[0-9a-f]{40}$/,'explicit full expected head required');
  const address=new URL(url);assert.ok(address.protocol==='http:'&&['localhost','127.0.0.1'].includes(address.hostname)&&address.port&&address.port!=='8765','dedicated localhost service required');
  const before=snapshot();assert.equal(before.head,expected);assert.equal(before.status,'','frozen clean checkout required');
  const runtime=await fetch(new URL('/runtime',url)).then(r=>r.json());assert.equal(runtime.fresh,true);assert.equal(path.resolve(runtime.root),root);
  const objects=await fetch(new URL('/api',url),{method:'POST',headers:{'Content-Type':'application/json','X-Geometry-Version':runtime.version},body:JSON.stringify({cmd:'objects'})}).then(r=>r.json());assert.equal(objects.ok,true,'native readonly identity preflight');
  const children=cp.execFileSync('ps',['--ppid',String(runtime.pid),'-o','pid='],{encoding:'utf8'}).trim().split(/\s+/).filter(Boolean).flatMap(pid=>{try{const exe=fs.realpathSync('/proc/'+pid+'/exe');return [{pid:Number(pid),exe,sha256:hash(exe)}];}catch(error){const argv=fs.readFileSync('/proc/'+pid+'/cmdline').toString().split('\0');const exe=argv[0];return path.isAbsolute(exe)&&fs.existsSync(exe)?[{pid:Number(pid),exe,sha256:hash(exe),identityMethod:'proc-cmdline and launcher file hash; proc-exe read unavailable',procExeError:error.code}]:[];}});
  const bridge=children.find(r=>path.basename(r.exe).startsWith('bridge'));assert.ok(bridge,'live native child required');
  const inspect="import sys,json;from pathlib import Path;sys.path.insert(0,sys.argv[1]+'/tests');import binaries;i=binaries.inspect_one(binaries.BY_NAME['bridge'],path=Path(sys.argv[2]));print(json.dumps(i.as_dict()))";
  const native=JSON.parse(cp.execFileSync('python3',['-c',inspect,root,bridge.exe],{encoding:'utf8'}));assert.equal(native.state,'fresh');
  let count=0;const counted=new Proxy(assert,{get(target,key){const value=target[key];return typeof value==='function'?function(...args){count++;return value(...args);}:value;},apply(target,thisArg,args){count++;return Reflect.apply(target,thisArg,args);}});
  return {assert:counted,session:runtime.session,finish:async()=>{
    const after=snapshot(),end=await fetch(new URL('/runtime',url)).then(r=>r.json());assert.deepEqual(after,before,'source identities frozen through gate');assert.equal(end.fresh,true);assert.equal(end.version,runtime.version);assert.equal(end.session,runtime.session);assert.equal(hash(bridge.exe),bridge.sha256);
    const receipt={schema:'k2a-browser-receipt/1',finishedAt:new Date().toISOString(),command:process.argv,harnessSHA256:hash(process.argv[1]),node:{version:process.version,path:process.execPath,sha256:hash(process.execPath)},browserLauncher:{path:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',sha256:hash(process.env.GEOMETRY_CHROME||'/usr/bin/chromium')},url,before,after,runtimeBefore:runtime,runtimeAfter:end,native,liveBridge:bridge,assertions:count,instrumentation:process.env.GEOMETRY_GRID_WORKSPACE_SOURCE||null};
    const out=process.env.GEOMETRY_BROWSER_RECEIPT;if(!out||!path.resolve(out).startsWith('/tmp/'))throw Error('explicit TEMP receipt path required');fs.writeFileSync(out+'.'+address.port+'.json',JSON.stringify(receipt,null,2)+'\n');console.log('K2A_BROWSER_RESULT '+JSON.stringify({assertions:count,head:before.head,receipt:out}));
  }};
};
