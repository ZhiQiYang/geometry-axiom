/* Structured node:test adapter for the R06 strict mutation judge.
 * Run in-process so individual tests, not a wrapper-file exit, are observed.
 * Recording assertion messages does not replace or relax their implementation.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const assert=require('node:assert/strict'),{run}=require('node:test');
const [destination,file,pattern]=process.argv.slice(2);
if(!destination||!file||!pattern)throw Error('usage: bay_repeat_node_runner.cjs result.json test-file exact-name-pattern');
const selected=new RegExp(pattern),reached=new Set(),events=[];
const tags=message=>[...new Set([...String(message).matchAll(/KILLER\[([^\]\s]+)\]|\b(R06_[A-Z0-9_]+)\b/g)].map(m=>m[1]||m[2]))];
for(const key of Object.keys(assert)){
 if(typeof assert[key]!=='function'||key==='AssertionError')continue;
 const original=assert[key];
 assert[key]=function(...args){
  if(typeof args.at(-1)==='string')for(const tag of tags(args.at(-1)))reached.add(tag);
  return Reflect.apply(original,this,args);
 };
}
const result={selected:[],run:0,failures:[],errors:[],skipped:[],expectedFailures:[],unexpectedSuccesses:[],reached:[],node:process.version};
function unwrap(error){
 while(error?.cause&&error?.code==='ERR_TEST_FAILURE')error=error.cause;
 return error;
}
function outcome(data,failed){
 if(data.details?.type!=='test'||!selected.test(data.name))return;
 result.run++;result.selected.push(data.name);
 const record={test:data.name};
 if(data.skip){result.skipped.push({...record,reason:String(data.skip)});return;}
 if(data.todo){result.expectedFailures.push({...record,reason:String(data.todo)});return;}
 if(!failed)return;
 const error=unwrap(data.details.error),message=String(error?.message||data.details.error);
 Object.assign(record,{exception:error?.name||'UnknownError',code:error?.code||null,tags:tags(message),
  message:message.slice(0,6000),bridgeClosed:false,stack:String(error?.stack||'').slice(0,6000)});
 (error?.code==='ERR_ASSERTION'&&error?.name==='AssertionError'?result.failures:result.errors).push(record);
}
const stream=run({files:[path.resolve(file)],testNamePatterns:[selected],isolation:'none'});
stream.on('test:pass',data=>outcome(data,false));
stream.on('test:fail',data=>outcome(data,true));
stream.on('test:diagnostic',data=>events.push({type:'diagnostic',message:data.message}));
stream.on('error',error=>result.errors.push({test:'runner',exception:error.name,message:error.message,tags:[]}));
let summary=null;
stream.on('test:summary',data=>{summary=data;});
stream.on('end',()=>{
 result.reached=[...reached].sort();result.summary=summary;result.diagnostics=events;
 if(!summary||summary.counts.tests!==result.run||!result.run)
  result.errors.push({test:'runner',exception:'IncompleteTestStream',message:'No complete, exact individual-test summary',tags:[]});
 fs.mkdirSync(path.dirname(destination),{recursive:true});fs.writeFileSync(destination,JSON.stringify(result,null,2)+'\n');
 process.exitCode=result.failures.length||result.errors.length||result.skipped.length||result.expectedFailures.length||result.unexpectedSuccesses.length?1:0;
});
stream.resume();
