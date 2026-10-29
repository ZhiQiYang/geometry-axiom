'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto'),os=require('node:os'),cp=require('node:child_process');
const ROOT=path.resolve(process.env.GEOMETRY_CUTTING_TEST_ROOT||path.join(__dirname,'..'));
const {cases,verifyCases,applyChanges}=require('./cutting_legacy_cases.js');
const golden=require('./fixtures/cutting_legacy_cd4bc880.json');
const clone=v=>JSON.parse(JSON.stringify(v)),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=p=>{assert.ok(fs.existsSync(path.join(ROOT,p)),'required layer source: '+p);return fs.readFileSync(path.join(ROOT,p),'utf8');};
const K_PATH='geometry-core/interval-allocation.js',W_PATH='geometry-templates/woodworking/cutting.js';
function load(relative){assert.ok(fs.existsSync(path.join(ROOT,relative)),'required layer source: '+relative);return require(path.join(ROOT,relative));}
function standalone(){
 const context=vm.createContext({TextEncoder});
 vm.runInContext(read(K_PATH),context,{filename:K_PATH});
 vm.runInContext(read(W_PATH),context,{filename:W_PATH});
 return context;
}
function hostContext({kernel=true,template=true,application=true}={}){
 const context=vm.createContext({crypto:crypto.webcrypto,TextEncoder});
 if(kernel)vm.runInContext(read(K_PATH),context);
 vm.runInContext(read('geometry-templates/woodworking/frontend.js'),context);
 if(template)vm.runInContext(read(W_PATH),context);
 if(application)vm.runInContext(read('geometry-app/application.js'),context);
 vm.runInContext(read('geometry-web/timber-schedule.js'),context);
 vm.runInContext(read('geometry-web/cutting-settings.js'),context);
 vm.runInContext(read('geometry-web/cutting-plan.js'),context);
 return context;
}

test('R357 legacy oracle is pinned independently with all fixed input hashes',()=>{
 assert.equal(golden.sourceCommit,'cd4bc8803016943e6ec7bf98f0c90bc0312cfa06');
 assert.deepEqual(golden.sources.map(s=>s.blob),['d7cac099298d42018c5a278a5217bc625d8598a7','c634957ad21e16377fab55fcf7edc7c5e6239392','feb3b9ab98e73f9cbe7e022f71e3d7e354b71c73']);
 assert.equal(golden.inputHelperSha256,sha(fs.readFileSync(path.join(__dirname,'cutting_legacy_cases.js'))));
 assert.equal(golden.cases.length,53);
 assert.deepEqual(cases().map(c=>[c.id,sha(JSON.stringify(c))]),golden.cases.map(c=>[c.id,c.inputSha256]));
});
test('R357 all 53 legacy JSON outputs, CSV bytes and rejection order remain exact',async()=>{
 const C=load('geometry-web/cutting-plan.js'),S=load('geometry-web/cutting-settings.js');
 for(const input of cases()){
  const expected=golden.cases.find(c=>c.id===input.id),before=JSON.stringify(input);let actual;
  try{
   if(input.action==='transition')actual={value:JSON.stringify(S.transition(input.previous,input.value))};
   else{const plan=await C.evaluate(input.references,input.settings,input.request);actual={plan:JSON.stringify(plan),csv:plan.status==='COMPLETE'?C.csv(plan):null};}
  }catch(error){actual={error:{code:error.code??null,message:error.message}};}
  const wanted=expected.error?{error:expected.error}:expected.value?{value:expected.value}:{plan:expected.plan,csv:expected.csv};
  assert.deepEqual(actual,wanted,input.id);
  if(actual.csv!==null&&actual.csv!==undefined)assert.ok(Buffer.from(actual.csv).equals(Buffer.from(expected.csv)),input.id+' UTF-8 CSV bytes');
  assert.equal(JSON.stringify(input),before,input.id+' is read-only');
 }
});
test('R357 W evaluates native rows without H, DOM, Window, Schedule or Settings',()=>{
 const context=standalone(),W=context.GeometryWoodworkingCutting;
 assert.equal(W.id,'woodworking/1');assert.ok(Object.isFrozen(W));
 for(const name of ['window','document','Window','GeometryApplication','CuttingSettings','TimberSchedule','CuttingPlan','require'])assert.equal(typeof context[name],'undefined',name+' absent');
 let count=0;
 for(const expected of golden.cases.filter(c=>c.nativeRows)){
  const input=cases().find(c=>c.id===expected.id),old=JSON.parse(expected.plan);
  const rows=clone(expected.nativeRows),settings=clone(input.settings),before=JSON.stringify([rows,settings]);
  const envelope={status:'EMPTY',diagnostics:[],worldFingerprint:input.references.sourceFingerprint,settingsFingerprint:old.settingsFingerprint,label:'本次找到的方案',groups:[]};
  assert.equal(W.evaluateRows(rows,settings,envelope),envelope,'explicit caller-owned result');
  assert.equal(JSON.stringify(envelope),expected.plan,expected.id+' standalone W numeric/status/ordering parity');
  assert.equal(JSON.stringify([rows,settings]),before,expected.id+' standalone W inputs are read-only');count++;
 }
 assert.equal(count,29,'all independently derived valid-row cases must run');
});
test('R357 W delegates identity, each allocation and full conservation to shared K',()=>{
 const context=vm.createContext({TextEncoder});
 vm.runInContext(read(K_PATH),context);
 const K=context.GeometryIntervalAllocation,calls={identity:0,allocation:0,whole:0};
 const observed={...K,createIdentityTracker(){calls.identity++;return K.createIdentityTracker();},verifyAllocation(...args){calls.allocation++;return K.verifyAllocation(...args);},verify(...args){calls.whole++;return K.verify(...args);}};
 Object.values(observed).filter(v=>typeof v==='function').forEach(Object.freeze);Object.freeze(observed);
 // Instrument the dependency edge while actual K and W execute in one realm.
 // This fixture uses W's CommonJS composition, not a second implementation.
 context.module={exports:{}};
 context.require=relative=>{assert.equal(relative,'../../geometry-core/interval-allocation.js');return observed;};
 vm.runInContext(read(W_PATH),context);
 const plan=JSON.parse(golden.cases.find(c=>c.id==='ffd-success').plan);
 assert.equal(context.module.exports.verify(plan),true);
 assert.deepEqual(calls,{identity:1,allocation:6,whole:1},'W must use the shared K validators on the actual plan');
});
test('R357 public verify and CSV preserve pinned legacy error priority across pieces and groups',()=>{
 const C=load('geometry-web/cutting-plan.js');
 assert.equal(golden.verification.length,4);
 for(const input of verifyCases()){
  const expected=golden.verification.find(c=>c.id===input.id);
  assert.equal(sha(JSON.stringify(input)),expected.inputSha256,input.id+' fixed mutation input');
  const plan=applyChanges(JSON.parse(golden.cases.find(c=>c.id===input.planCase).plan),input.changes);
  for(const method of ['verify','csv']){
   let actual;try{actual={value:JSON.stringify(C[method](plan))};}catch(error){actual={error:{code:error.code??null,message:error.message}};}
   assert.deepEqual(actual,expected[method],input.id+' '+method+' error order and text');
  }
 }
});
test('R357 public H uses the same frozen W and cannot replace policy through request fields',async()=>{
 const C=load('geometry-web/cutting-plan.js'),W=load(W_PATH),application=load('geometry-app/application.js');
 assert.equal(application.cutting,W);assert.ok(Object.isFrozen(application));
 assert.throws(()=>{application.cutting={evaluateRows(){return {status:'COMPLETE'};}};},TypeError);
 assert.throws(()=>{W.evaluateRows=()=>({status:'COMPLETE'});},TypeError);
 const input=cases().find(c=>c.id==='mixed-material');
 const request={...input.request,template:'other/1',cutting:{evaluateRows(){assert.fail('request cannot override W');}},evaluateRows(){assert.fail('request cannot override W');}};
 assert.equal(JSON.stringify(await C.evaluate(input.references,input.settings,request)),golden.cases.find(c=>c.id===input.id).plan);
 const browser=hostContext();assert.equal(browser.GeometryApplication.cutting,browser.GeometryWoodworkingCutting);
 assert.throws(()=>vm.runInContext('"use strict"; GeometryApplication.cutting = {};',browser),/read only|readonly|Cannot assign/i);
 assert.throws(()=>vm.runInContext('"use strict"; GeometryWoodworkingCutting = {};',browser),/read only|readonly|Cannot assign/i);
});
test('R357 public composition refuses missing W and W refuses missing K',()=>{
 assert.throws(()=>hostContext({template:false}),/缺少固定裁切模板/);
 assert.throws(()=>hostContext({kernel:false}),/缺少共用區間驗證器/);
});

const key=(id=0,extra={})=>({type:'neutral-demand',id,...extra});
function allocation(){return {expected:[key(0),key(1)],containers:[{length:40,usable:[2,37],allocations:[{key:key(0),length:10,start:2,end:12},{key:key(1),length:10,start:15,end:25}],consumptions:[{start:0,end:2},{start:12,end:15},{start:25,end:27}],remainder:{start:27,end:40}}]};}
test('R357 K neutral allocation conserves explicit intervals without woodworking defaults',()=>{
 const K=load(K_PATH),input=allocation(),saved=JSON.stringify(input);assert.equal(K.verify(input),true);assert.equal(JSON.stringify(input),saved);
 const maximum=Number.MAX_SAFE_INTEGER,large={expected:[key('external')],containers:[{length:maximum,usable:[0,maximum],allocations:[{key:key('external'),length:maximum-1,start:0,end:maximum-1}],consumptions:[],remainder:{start:maximum-1,end:maximum}}]};
 assert.equal(K.verify(large),true,'K does not inherit the W stock dimension limit');
});
test('R357 K typed identities retain type, id type, owner, version and nested source identity',()=>{
 const K=load(K_PATH),keys=[key(0),{type:'other-demand',id:0},key('0'),key(0,{owner:{type:'container',id:8},version:1}),key(0,{owner:{type:'container',id:9},version:1}),key(0,{owner:{type:'container',id:8},version:2})];
 const input={expected:keys,containers:[{length:6,usable:[0,6],allocations:keys.map((k,i)=>({key:clone(k),length:1,start:i,end:i+1})),consumptions:[],remainder:{start:6,end:6}}]};
 assert.equal(K.verify(input),true);
 input.containers[0].allocations[3].key={version:1,owner:{id:8,type:'container'},id:0,type:'neutral-demand'};
 assert.equal(K.verify(input),true,'property order does not create another identity');
 input.containers[0].allocations[3].key.owner.id=9;
 assert.throws(()=>K.verify(input),/DEMAND_IDENTITY/,'same bare id with changed owner cannot be substituted');
});
test('R357 K rejects duplicate, absent, unexpected and untyped demand identities',()=>{
 const K=load(K_PATH);
 const edits=[p=>p.expected.push(key(0)),p=>p.expected.push(key(2)),p=>p.expected.pop(),p=>p.containers[0].allocations[1].key=key(0),p=>p.containers[0].allocations[1].key=1,p=>p.containers[0].allocations[1].key={id:1},p=>p.containers[0].allocations[1].key={type:'neutral-demand',id:-1},p=>p.containers.push(clone(p.containers[0]))];
 for(const [i,edit]of edits.entries()){const p=allocation();edit(p);assert.throws(()=>K.verify(p),/DEMAND_IDENTITY/,'identity negative '+i);}
});
test('R357 K typed identity rejects inherited, hidden and accessor identity fields',()=>{
 const K=load(K_PATH);
 const nested=[1,2];Object.defineProperty(nested,'revision',{value:3,enumerable:false});
 const custom=Object.assign(Object.create(Object.assign(Object.create(null),{sourceVersion:9})),key(0));
 const keys=[Object.create({type:'neutral-demand',id:0}),Object.defineProperty({id:0},'type',{value:'neutral-demand',enumerable:false}),Object.defineProperty({type:'neutral-demand'},'id',{value:0,enumerable:false}),Object.defineProperty(key(0),'owner',{value:4,enumerable:false}),Object.defineProperty(key(0),'version',{get(){assert.fail('identity getter must never run');},enumerable:true}),{get type(){assert.fail('type getter must never run');},id:0},{type:'neutral-demand',get id(){assert.fail('id getter must never run');}},key(0,{owner:nested}),custom];
 for(const [i,k]of keys.entries()){
  const p=allocation();p.expected[0]=k;p.containers[0].allocations[0].key=k;
  assert.throws(()=>K.verify(p),/DEMAND_IDENTITY/,'opaque key negative '+i);
 }
});
test('R357 K rejects missing consumption, overlap, bounds and noninteger conservation',()=>{
 const K=load(K_PATH);
 const edits=[p=>p.containers[0].consumptions.pop(),p=>delete p.containers[0].consumptions,p=>delete p.containers[0].remainder,p=>p.containers[0].consumptions[2]={start:24,end:26},p=>p.containers[0].remainder.end=41,p=>p.containers[0].allocations[0].start=1,p=>p.containers[0].allocations[0].length=9,p=>p.containers[0].allocations[0].length=0,p=>p.containers[0].length=40.5,p=>p.containers[0].allocations[0].end=12.5,p=>p.containers[0].usable=[3,37],p=>p.containers[0].usable=[2,24],p=>p.containers[0].usable=[-1,37],p=>p.containers[0].consumptions[0].start=-1,p=>p.containers[0].length=Number.MAX_SAFE_INTEGER+1,p=>{const c=p.containers[0];[c.remainder,c.consumptions[0]]=[c.consumptions[0],c.remainder];}];
 for(const [i,edit]of edits.entries()){const p=allocation();edit(p);assert.throws(()=>K.verify(p),/CONSERVATION/,'conservation negative '+i);}
});
test('R357 W verifies fixed processing semantics before H exports any corrupted plan',async()=>{
 const C=load('geometry-web/cutting-plan.js'),W=load(W_PATH);
 const original=JSON.parse(golden.cases.find(c=>c.id==='ffd-success').plan);
 const edits=[p=>p.groups[0].stocks[0].pieces[0].end++,p=>p.groups[0].stocks[0].tail.consumed++,p=>p.groups[0].stocks[0].cuts++,p=>p.groups[0].kerfLoss++,p=>p.groups[0].trimLoss++,p=>p.groups[0].stocks[0].pieces[1].timberId=1];
 for(const [i,edit]of edits.entries()){const p=clone(original);edit(p);assert.throws(()=>W.verify(p),/CONSERVATION|DEMAND_IDENTITY/,'W negative '+i);assert.throws(()=>C.csv(p),/CONSERVATION|DEMAND_IDENTITY/,'H CSV negative '+i);}
 assert.throws(()=>W.verify(original,[1,2,3,4,5,6,9]),/DEMAND_IDENTITY/,'expected demand cannot disappear');
});
test('R357 four real layer mutations must fail named behavior assertions',()=>{
 const mutations=[
  {id:'K-no-op',file:K_PATH,before:'function verify(value) {',after:'function verify(value) { return true;',pattern:'R357 K rejects missing consumption'},
  {id:'K-flatten-identity',file:K_PATH,before:'return canonical(key);',after:'return JSON.stringify([key.type,key.id]);',pattern:'R357 K typed identities retain'},
  {id:'W-bypass-K',file:W_PATH,before:'checked(()=>Core.verify({expected:observed,containers}));',after:'void 0;',pattern:'R357 W delegates identity'},
  {id:'H-bypass-W',file:'geometry-web/cutting-plan.js',before:'return Policy.evaluateRows([...rows.values()],settings,p);',after:'return p;',pattern:'R357 all 53 legacy JSON outputs'},
 ];
 const work=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-cutting-layer-mutations-'));
 const files=[K_PATH,W_PATH,'geometry-app/application.js','geometry-templates/woodworking/frontend.js','geometry-web/cutting-settings.js','geometry-web/cutting-plan.js','geometry-web/timber-schedule.js'];
 const tests=['test_cutting_layering.js','cutting_legacy_cases.js','fixtures/cutting_legacy_cd4bc880.json'];
 const evidence=process.env.GEOMETRY_CUTTING_MUTATION_EVIDENCE;
 const report={schema:'cutting-layer-mutations/1',sources:{},tests:{},results:[]};
 const save=(name,body)=>{if(evidence){fs.mkdirSync(evidence,{recursive:true});fs.writeFileSync(path.join(evidence,name),body);}};
 try{
  for(const file of files){const text=read(file);fs.mkdirSync(path.dirname(path.join(work,file)),{recursive:true});fs.writeFileSync(path.join(work,file),text);report.sources[file]=sha(text);}
  for(const file of tests){const target=path.join(work,'tests',file),bytes=fs.readFileSync(path.join(__dirname,file));fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,bytes);report.tests[file]=sha(bytes);}
  function run(pattern){
   const env={...process.env,GEOMETRY_CUTTING_TEST_ROOT:work,GEOMETRY_CUTTING_MUTATION_EVIDENCE:''};
   // A fresh CLI judge must not inherit node:test's internal child marker;
   // otherwise Node skips the entire child suite with a successful exit.
   delete env.NODE_TEST_CONTEXT;
   return cp.spawnSync(process.execPath,['--test','--test-reporter=tap','--test-name-pattern',pattern,path.join(work,'tests/test_cutting_layering.js')],{cwd:work,encoding:'utf8',timeout:60000,env});
  }
  const baseline=run(mutations.map(m=>m.pattern).join('|'));save('baseline.log',baseline.stdout+baseline.stderr);
  assert.equal(baseline.status,0,'real unmutated baseline must complete: '+baseline.stdout+baseline.stderr);
  for(const m of mutations)assert.ok([...baseline.stdout.matchAll(/^ok \d+ - (.+)$/gm)].some(match=>match[1].startsWith(m.pattern)),m.id+' named baseline must actually execute');
  report.baseline={exitCode:baseline.status,namedTests:mutations.map(m=>m.pattern)};
  for(const m of mutations){
   const file=path.join(work,m.file),original=fs.readFileSync(file,'utf8');
   assert.equal(original.split(m.before).length-1,1,m.id+' exact mutation anchor');
   fs.writeFileSync(file,original.replace(m.before,m.after));let result;
   try{result=run(m.pattern);}finally{fs.writeFileSync(file,original);}
   const log=(result.stdout||'')+(result.stderr||''),named=[...log.matchAll(/^not ok \d+ - (.+)$/gm)].some(match=>match[1].startsWith(m.pattern));
   const blocked=/SyntaxError|MODULE_NOT_FOUND|ReferenceError|TypeError|uncaughtException|unhandledRejection/.test(log);
   const cause=/AssertionError/.test(log)?'assertion':/CONSERVATION|DEMAND_IDENTITY/.test(log)?'invariant':null;
   const killed=result.status===1&&named&&!blocked&&cause!==null;
   save(m.id+'.log',log);report.results.push({id:m.id,source:m.file,sourceSha256:sha(original),mutationSha256:sha(m.before+'\0'+m.after),testPattern:m.pattern,exitCode:result.status,signal:result.signal,detectedBy:cause,status:killed?'killed':'not-killed'});
   assert.ok(killed,m.id+' must be killed by the named behavior test: '+log);
  }
  assert.equal(report.results.length,4);save('results.json',JSON.stringify(report,null,2)+'\n');
 }finally{fs.rmSync(work,{recursive:true,force:true});}
});
