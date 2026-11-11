/* Source-bound assertion journals for the canonical numeric canvas shards.
 * Routing, section order and handoff remain owned by geometry-web/canvas_shards.*. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const floor=require('../../geometry-web/cdp_floor.js');
const numeric=require('../../geometry-web/canvas_shards.js');
const PLAN='geometry-web/canvas_shards.json',GOLDEN='geometry-web/cdp_sections.golden.json';
const shardIds=plan=>plan.shards.map(shard=>shard.index+'/'+plan.shards.length);
function requireThat(ok,code,detail='') {
  if(!ok){const error=Error(code+(detail?': '+detail:''));error.code=code;throw error;}
}
function stable(value) {
  if(Array.isArray(value))return '['+value.map(stable).join(',')+']';
  if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(key=>JSON.stringify(key)+':'+stable(value[key])).join(',')+'}';
  return JSON.stringify(value);
}
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
function same(a,b){return stable(a)===stable(b);}

function buildPlan(golden,numericPlan,sourceHashes={}) {
  requireThat(floor.validateGolden(golden).length===0,'CANVAS_GOLDEN_INVALID');
  requireThat(Object.values(golden.sections).every(Number.isInteger),'CANVAS_GOLDEN_NOT_EXACT');
  requireThat(golden.total===Object.values(golden.sections).reduce((a,b)=>a+b,0),'CANVAS_GOLDEN_TOTAL');
  const problems=numeric.validatePlan(numericPlan,golden);
  requireThat(problems.length===0,'CANVAS_PLAN_INVALID',problems.join('; '));
  const ids=shardIds(numericPlan);
  // In-memory fixtures supply canonical JSON digests. loadPlan always supplies
  // the actual LF digests of both checked-in files and the complete JS closure.
  const hashes={[PLAN]:sha(stable(numericPlan)),[GOLDEN]:sha(stable(golden)),...sourceHashes};
  const plan={schema:'geometry-canvas-plan/2',shards:ids,numericPlan,golden,
    units:numericPlan.shards.map((shard,index)=>({id:ids[index],owner:ids[index],sections:[...shard.sections],orderedSections:true})),
    sourceHashes:hashes};
  return {...plan,sha256:sha(stable(plan))};
}

function loadPlan(root=path.resolve(__dirname,'../..')) {
  const hashes={},texts=new Map();
  function visit(relative) {
    relative=relative.split(path.sep).join('/');
    requireThat(!relative.startsWith('../')&&!path.isAbsolute(relative),'CANVAS_SOURCE_PATH',relative);
    if(texts.has(relative))return;
    const raw=fs.readFileSync(path.join(root,relative)),text=raw.toString('utf8').replace(/\r\n/g,'\n');
    hashes[relative]=sha(text);texts.set(relative,text);
    if(!relative.endsWith('.js'))return;
    for(const match of text.matchAll(/\brequire\(\s*(['"])(\.[^'"\n]+)\1\s*\)/g)){
      let target=path.posix.normalize(path.posix.join(path.posix.dirname(relative),match[2]));
      if(!path.posix.extname(target))target+='.js';
      if(fs.existsSync(path.join(root,target)))visit(target);
    }
  }
  for(const relative of ['tests/helpers/canvas_shards.js','geometry-web/cdp_test.js',
      'geometry-web/canvas_shards.js',PLAN,GOLDEN,'.github/scripts/canvas_evidence.py',
      '.github/workflows/integration-tests.yml'])visit(relative);
  return buildPlan(JSON.parse(texts.get(GOLDEN)),JSON.parse(texts.get(PLAN)),hashes);
}
function unitsFor(plan,shardId) {
  requireThat(plan.shards.includes(shardId),'CANVAS_FAKE_SCOPE','unknown shard');
  return plan.units.filter(unit=>unit.owner===shardId);
}
function projection(plan,shardId) {
  return Object.fromEntries(unitsFor(plan,shardId).flatMap(unit=>unit.sections.map(key=>[key,plan.golden.sections[key]])));
}
function createJournal(plan,shardId,emit) {
  const wanted=unitsFor(plan,shardId),events=[],counts={},visited=new Set();let active=null,next=0,current=null,unitVisited=[];
  function event(row){const value={seq:events.length,...row};events.push(value);emit(value);}
  return {
    begin(id){requireThat(!active&&wanted[next]?.id===id,'CANVAS_UNOWNED_EXECUTION',id);active=wanted[next];current=null;unitVisited=[];event({type:'unit-begin',unit:id});},
    end(id){requireThat(active?.id===id,'CANVAS_UNIT_END',id);
      requireThat(same(unitVisited,active.sections),'CANVAS_MISSING_SECTION',id);
      event({type:'unit-end',unit:id});active=null;current=null;next++;},
    section(key,header){requireThat(active&&active.sections.includes(key),'CANVAS_UNOWNED_EXECUTION',key);
      requireThat(typeof header==='string'&&floor.sectionOf(header)===key,'CANVAS_SECTION_HEADER',key);
      if(!unitVisited.includes(key)){
        requireThat(active.sections[unitVisited.length]===key,'CANVAS_DEPENDENCY_ORDER',key);
        unitVisited.push(key);
      }
      current=key;visited.add(key);counts[key]??=0;event({type:'section',unit:active.id,section:key,header});},
    assertion(passed,label){requireThat(active&&active.sections.includes(current),'CANVAS_UNOWNED_EXECUTION',current||'no section');
      requireThat(typeof passed==='boolean','CANVAS_VERDICT');const ordinal=(counts[current]||0)+1;counts[current]=ordinal;
      event({type:'assertion',unit:active.id,section:current,ordinal,passed,label:String(label)});},
    finish(){requireThat(!active&&next===wanted.length,'CANVAS_MISSING_UNIT');
      requireThat(same([...visited].sort(),Object.keys(projection(plan,shardId)).sort()),'CANVAS_MISSING_SECTION');return {eventCount:events.length};},
  };
}

function verifyTrace(plan,shardId,events,result) {
  requireThat(Array.isArray(events),'CANVAS_FAKE_SUMMARY','missing journal');
  const projectionKeys=Object.keys(projection(plan,shardId)).sort();
  requireThat(same([...new Set(events.filter(event=>event?.type==='section').map(event=>event.section))].sort(),projectionKeys),
    'CANVAS_MISSING_SECTION','journal section set');
  const replay=[];const journal=createJournal(plan,shardId,event=>replay.push(event));
  for(const event of events){
    requireThat(event&&Number.isInteger(event.seq)&&event.seq===replay.length,'CANVAS_JOURNAL_SEQUENCE');
    if(event.type==='unit-begin')journal.begin(event.unit);
    else if(event.type==='unit-end')journal.end(event.unit);
    else if(event.type==='section')journal.section(event.section,event.header);
    else if(event.type==='assertion'){
      requireThat(event.passed===true,'CANVAS_ASSERTION_FAILED',event.label);journal.assertion(event.passed,event.label);
    }else requireThat(false,'CANVAS_JOURNAL_EVENT');
    requireThat(same(replay.at(-1),event),'CANVAS_JOURNAL_CHANGED');
  }
  journal.finish();
  const actual={};let assertions=0;
  for(const event of events){if(event.type==='section')actual[event.section]??=0;
    if(event.type==='assertion'){actual[event.section]++;assertions++;}}
  requireThat(result?.completed===true&&!result.fatal,'CANVAS_FAKE_SUMMARY','incomplete');
  requireThat(result.schema==='geometry-cdp-result/1','CANVAS_RESULT_SCHEMA');
  requireThat(result.goldenCompare==='matched (shard '+shardId+')','CANVAS_GOLDEN_NOT_COMPARED');
  requireThat(result.scope?.mode==='shard'&&
    result.scope.shard?.index+'/'+result.scope.shard?.count===shardId&&
    result.scope.evidencePlanSha256===plan.sha256&&
    same(result.scope.filters,[])&&same(result.scope.modifiers,[]),'CANVAS_FAKE_SCOPE');
  requireThat(result.failedAssertions===0&&same(result.skipped,[])&&result.sectionsFailed===undefined,
    'CANVAS_ASSERTION_FAILED','result failure/skip');
  requireThat(result.passedAssertions===assertions&&same(result.sections,actual),'CANVAS_FAKE_SUMMARY','counts differ from actual journal');
  requireThat(floor.compare({sections:projection(plan,shardId)},{sections:actual}).length===0,'CANVAS_COUNT_DRIFT');
  // Reuse main's result contract, including order, handoff and exact digests.
  // Actual exit/head/run/raw provenance is checked by canvas_evidence.py; this
  // in-memory wrapper validates the result only and is never published as a run.
  const index=result.scope.shard.index;
  const checked=numeric.verifyShardReceipt({
    name:'canvas-shard-'+index,
    run:{schema:numeric.RUN_SCHEMA,shard:shardId,exitCode:0},
    results:[JSON.stringify(result)]
  },{plan:plan.numericPlan,golden:plan.golden,
    planSha256:plan.sourceHashes[PLAN],goldenSha256:plan.sourceHashes[GOLDEN]});
  requireThat(checked.problems.length===0,'CANVAS_NUMERIC_RECEIPT',checked.problems.join('; '));
  return {shard:shardId,sections:actual,assertions,units:unitsFor(plan,shardId).map(unit=>unit.id)};
}
function verifyAggregate(plan,shards) {
  requireThat(Array.isArray(shards)&&shards.length===plan.shards.length,'CANVAS_MISSING_SHARD');
  const seen=new Set(),sections={},units=new Set();
  for(const shard of shards){
    requireThat(plan.shards.includes(shard.shard)&&!seen.has(shard.shard),'CANVAS_DUPLICATE_SHARD');seen.add(shard.shard);
    for(const unit of shard.units){requireThat(!units.has(unit),'CANVAS_DUPLICATE_UNIT');units.add(unit);}
    requireThat(same(shard.units,unitsFor(plan,shard.shard).map(unit=>unit.id)),'CANVAS_MISSING_UNIT');
    requireThat(shard.assertions===Object.values(shard.sections).reduce((a,b)=>a+b,0),'CANVAS_FAKE_SUMMARY','aggregate assertion count');
    for(const [key,count] of Object.entries(shard.sections)){
      requireThat(!Object.hasOwn(sections,key),'CANVAS_OVERLAPPING_SECTION',key);sections[key]=count;
    }
  }
  requireThat(floor.compare(plan.golden,{sections}).length===0,'CANVAS_GOLDEN_CHANGED');
  return {sections,sectionCount:Object.keys(sections).length,assertions:Object.values(sections).reduce((a,b)=>a+b,0)};
}

module.exports={get IDS(){return Object.freeze(shardIds(numeric.loadPlan()));},
  stable,sha,buildPlan,loadPlan,unitsFor,projection,createJournal,verifyTrace,verifyAggregate};
if(require.main===module){
  const plan=loadPlan();
  if(process.argv[2]==='plan')process.stdout.write(stable(plan)+'\n');
  else if(process.argv[2]==='verify-shard'){
    const request=JSON.parse(fs.readFileSync(0,'utf8'));
    process.stdout.write(stable(verifyTrace(plan,request.id,request.events,request.result))+'\n');
  }
  else if(process.argv[2]==='verify'){
    const request=JSON.parse(fs.readFileSync(0,'utf8'));
    const shards=request.shards.map(shard=>verifyTrace(plan,shard.id,shard.events,shard.result));
    process.stdout.write(stable(verifyAggregate(plan,shards))+'\n');
  }else throw Error('Use plan or verify');
}
