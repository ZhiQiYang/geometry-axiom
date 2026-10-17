// Diagnostic only: no source, assertions, timeout or concurrency changes.
const fs=require('node:fs'),{performance}=require('node:perf_hooks');
const {AsyncLocalStorage}=require('node:async_hooks'),als=new AsyncLocalStorage();
const path=require('node:path'),root='/workspace/geometry-axiom';
const selected=name=>/^formal cases (detached prepare|cancellation|no-op)|^case-only near-limit/.test(name);
const output=path.join(process.env.TIMEOUT_DIAGNOSTIC_DIR,`${process.pid}.jsonl`);
const emit=row=>fs.appendFileSync(output,JSON.stringify({pid:process.pid,t:performance.now(),...row})+'\n');
const cpu=()=>process.cpuUsage();
function measured(label,fn){return function(...args){
  const name=als.getStore();if(!name||!selected(name))return fn.apply(this,args);
  const start=performance.now(),usage=cpu();
  const finish=error=>emit({event:'step',name,label,ms:performance.now()-start,cpu_us:process.cpuUsage(usage),error:error?.message});
  let value;try{value=fn.apply(this,args);}catch(error){finish(error);throw error;}
  if(value&&typeof value.then==='function')return value.then(result=>{finish();return result;},error=>{finish(error);throw error;});
  finish();return value;
};}
const cp=require('node:child_process');cp.execFileSync=measured('execFileSync (catalog Python)',cp.execFileSync);
const nt=require('node:test'),original=nt.test;
nt.test=function(name,...args){
  const at=args.findIndex(arg=>typeof arg==='function');
  if(at>=0){const fn=args[at];args[at]=function(...values){return als.run(name,()=>measured('test callback',fn).apply(this,values));};}
  return original.call(this,name,...args);
};
const P=require(root+'/geometry-web/project-store.js');
for(const key of ['sha','assertManifestCapacity'])P[key]=measured('P.'+key,P[key]);
for(const key of ['record'])P.Features[key]=measured('Features.'+key,P.Features[key]);
for(const key of ['validate','verifyHashes'])P.Features.Cases[key]=measured('Cases.'+key,P.Features.Cases[key]);
const vm=require('node:vm'),run=vm.runInNewContext;
vm.runInNewContext=function(code,env,...args){const result=run.call(this,code,env,...args);
  if(env.workspace)for(const key of ['prepareFeatureAttachment','commitPreparedFeatureAttachment','manifest','tryLocalHistory'])
    env.workspace[key]=measured('workspace.'+key,env.workspace[key]);
  return result;
};
emit({event:'process-start',availableParallelism:require('node:os').availableParallelism(),cpuMax:fs.readFileSync('/sys/fs/cgroup/cpu.max','utf8').trim(),argv:process.argv});
