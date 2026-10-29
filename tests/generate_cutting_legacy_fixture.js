/* Regenerate only from the fixed pre-layering Git blobs, never the working tree. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),cp=require('node:child_process'),crypto=require('node:crypto');
const {cases,verifyCases,applyChanges}=require('./cutting_legacy_cases.js');
const PIN='cd4bc8803016943e6ec7bf98f0c90bc0312cfa06';
const ROOT=path.resolve(__dirname,'..'),OUTPUT=path.join(__dirname,'fixtures/cutting_legacy_cd4bc880.json');
const SOURCES=[
 {path:'geometry-web/cutting-settings.js',blob:'d7cac099298d42018c5a278a5217bc625d8598a7',sha256:'23f44ae9717405bbc5bf95ca32f0cda47af0e25104972d0d984ed5b85d94e265'},
 {path:'geometry-web/timber-schedule.js',blob:'c634957ad21e16377fab55fcf7edc7c5e6239392',sha256:'bb1558ff482591b2c4085a1f20c46e50999db7bfa2be748d74f131e85726bd9c'},
 {path:'geometry-web/cutting-plan.js',blob:'feb3b9ab98e73f9cbe7e022f71e3d7e354b71c73',sha256:'d160c37d1c4b4b283082aa86d86df7c431f806f4104d2c6f3da96f42c6a51bf5'},
];
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function generate(){
 const context=vm.createContext({crypto:crypto.webcrypto,TextEncoder});
 for(const source of SOURCES){
  const blob=cp.execFileSync('git',['rev-parse',PIN+':'+source.path],{cwd:ROOT,encoding:'utf8'}).trim();
  const bytes=cp.execFileSync('git',['show',PIN+':'+source.path],{cwd:ROOT});
  if(blob!==source.blob||sha(bytes)!==source.sha256)throw Error('Pinned legacy source mismatch: '+source.path);
  vm.runInContext(bytes.toString('utf8'),context,{filename:PIN+'/'+source.path});
 }
 const entries=[];
 for(const input of cases()){
  const before=JSON.stringify(input);context.input=JSON.parse(before);let output;
  try{
   if(input.action==='transition')output={value:JSON.stringify(vm.runInContext('CuttingSettings.transition(input.previous,input.value)',context))};
   else{
    context.plan=await vm.runInContext('CuttingPlan.evaluate(input.references,input.settings,input.request)',context);
    output={plan:JSON.stringify(context.plan),csv:context.plan.status==='COMPLETE'?vm.runInContext('CuttingPlan.csv(plan)',context):null};
   }
  }catch(error){output={error:{code:error.code??null,message:error.message}};}
  if(JSON.stringify(context.input)!==before)throw Error('Legacy evaluation mutated '+input.id);
  let nativeRows;
  const plan=output.plan?JSON.parse(output.plan):null;
  if(plan&&plan.status!=='EMPTY'&&!plan.diagnostics.some(d=>/^(CAPACITY|WORLD_|SCOPE_|ROW_NOT_READY)/.test(d.code))){
   try{
    nativeRows=vm.runInContext('(()=>{const rows=new Map();for(const scope of input.request.scopes)for(const row of TimberSchedule.derive(input.references,scope.surface,scope.ids).rows)rows.set(row.id,row);return [...rows.values()];})()',context);
   }catch(_){ /* No independent valid row input for this host rejection. */ }
  }
  entries.push({id:input.id,inputSha256:sha(Buffer.from(before)),...output,...(nativeRows?{nativeRows}:{} )});
 }
 const verification=[];
 for(const input of verifyCases()){
  context.plan=applyChanges(JSON.parse(entries.find(c=>c.id===input.planCase).plan),input.changes);
  const output={id:input.id,inputSha256:sha(JSON.stringify(input))};
  for(const method of ['verify','csv'])try{output[method]={value:JSON.stringify(vm.runInContext('CuttingPlan.'+method+'(plan)',context))};}catch(error){output[method]={error:{code:error.code??null,message:error.message}};}
  verification.push(output);
 }
 return {schema:'cutting-legacy-oracle/1',sourceCommit:PIN,sources:SOURCES,inputHelperSha256:sha(fs.readFileSync(path.join(__dirname,'cutting_legacy_cases.js'))),cases:entries,verification};
}
if(require.main===module)generate().then(data=>{
 const bytes=Buffer.from(JSON.stringify(data,null,2)+'\n');
 if(process.argv.slice(2).join(' ')==='--check'){
  if(!fs.existsSync(OUTPUT)||!bytes.equals(fs.readFileSync(OUTPUT)))throw Error('Independent legacy fixture differs');
 }else if(process.argv.length===2){fs.mkdirSync(path.dirname(OUTPUT),{recursive:true});fs.writeFileSync(OUTPUT,bytes);}
 else throw Error('Usage: node tests/generate_cutting_legacy_fixture.js [--check]');
 console.log(JSON.stringify({sourceCommit:PIN,cases:data.cases.length,sha256:sha(bytes),mode:process.argv.includes('--check')?'verified':'generated'}));
}).catch(e=>{console.error(e);process.exitCode=1;});
module.exports={PIN,SOURCES,generate};
