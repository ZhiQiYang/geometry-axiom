/* Pure ownership and receipt checks for the existing CDP canvas harness.
 * No browser, native executable, or product module is executed here. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const floor=require('../../geometry-web/cdp_floor.js');
const IDS=['legacy','extensions'];
const EXTENSIONS=[
  ['project-audit',['project_audit_test.js']],
  ['engineering',['engineering_workflow_test.js']],
  ['marquee',['marquee_test.js']],
  ['grid-system',['grid_system_test.js']],
  ['grid-rule-editor',['grid_rule_editor_test.js']],
  ['grid-rule-lines',['grid_rule_lines_test.js']],
  ['composition',['composition_canvas_test.js']],
  ['grid-rename',['grid_inspector_rename_test.js']],
  ['uiux',['uiux_review_test.js']],
  ['ux-refinement',['ux_refinement_test.js']],
  ['selection-cursor',['selection_cursor_test.js']],
  ['parameters',['parameter_workflow_test.js']],
  ['assembly',['assembly_workflow_test.js']],
  ['assembly-context',['assembly_context_entry_test.js']],
  ['timber-schedule',['timber_schedule_test.js']],
  ['timber-supports',['timber_supports_browser_test.js']],
  ['source-navigation',['source_navigation_test.js']],
  ['room-outline',['room_outline_test.js']],
  ['model-snapshots',['model_snapshot_schedule_test.js','model_snapshot_navigation_test.js']],
];
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

function buildPlan(golden,extensions,sourceHashes={}) {
  requireThat(floor.validateGolden(golden).length===0,'CANVAS_GOLDEN_INVALID');
  requireThat(Object.values(golden.sections).every(Number.isInteger),'CANVAS_GOLDEN_NOT_EXACT');
  requireThat(golden.total===Object.values(golden.sections).reduce((a,b)=>a+b,0),'CANVAS_GOLDEN_TOTAL');
  const seen=new Set(),names=new Set(['legacy']);
  const units=extensions.map(unit=>{
    requireThat(typeof unit.id==='string'&&!names.has(unit.id),'CANVAS_DUPLICATE_UNIT',unit.id);names.add(unit.id);
    requireThat(Array.isArray(unit.sections)&&unit.sections.length>0,'CANVAS_EMPTY_UNIT',unit.id);
    for(const key of unit.sections){
      requireThat(Object.hasOwn(golden.sections,key),'CANVAS_UNKNOWN_SECTION',key);
      requireThat(!seen.has(key),'CANVAS_OVERLAPPING_SECTION',key);seen.add(key);
    }
    return {...unit,owner:'extensions',orderedSections:true};
  });
  const legacy=Object.keys(golden.sections).filter(key=>!seen.has(key));
  requireThat(legacy.length>0,'CANVAS_EMPTY_LEGACY');
  const plan={schema:'geometry-canvas-plan/1',shards:[...IDS],golden,
    units:[{id:'legacy',owner:'legacy',sections:legacy},...units],sourceHashes};
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
  function closure(relative,seen=new Set()) {
    if(seen.has(relative))return seen;seen.add(relative);
    const text=texts.get(relative)||'';
    for(const match of text.matchAll(/\brequire\(\s*(['"])(\.[^'"\n]+)\1\s*\)/g)){
      let target=path.posix.normalize(path.posix.join(path.posix.dirname(relative),match[2]));
      if(!path.posix.extname(target))target+='.js';
      if(texts.has(target))closure(target,seen);
    }
    return seen;
  }
  for(const relative of ['tests/helpers/canvas_shards.js','geometry-web/cdp_test.js','geometry-web/cdp_sections.golden.json',
      '.github/scripts/canvas_evidence.py','.github/workflows/integration-tests.yml'])visit(relative);
  const extensions=EXTENSIONS.map(([id,files])=>{
    const entries=files.map(file=>'geometry-web/'+file),sections=new Set();
    for(const entry of entries){visit(entry);
      for(const relative of closure(entry)){
        for(const match of (texts.get(relative)||'').matchAll(/\bconsole\.log\(\s*(['"`])(===\s[^'"`\n]*)\1/g)){
          const key=floor.sectionOf(match[2]);if(key)sections.add(key);
        }
      }
    }
    return {id,entries,sections:[...sections]};
  });
  return buildPlan(JSON.parse(texts.get('geometry-web/cdp_sections.golden.json')),extensions,hashes);
}

function configure(env,scope,plan,scopeFlags,modifiers) {
  if(env.GEOMETRY_CDP_SHARD===undefined)return scope;
  requireThat(IDS.includes(env.GEOMETRY_CDP_SHARD),'CANVAS_FAKE_SCOPE','unknown shard');
  requireThat(![...scopeFlags,...modifiers].some(name=>env[name]!==undefined),'CANVAS_FAKE_SCOPE','legacy scope flag/modifier');
  requireThat(env.GEOMETRY_CDP_UPDATE_GOLDEN===undefined,'CANVAS_FAKE_SCOPE','golden update');
  const url=new URL(scope.url);
  requireThat(url.protocol==='http:'&&url.hostname==='127.0.0.1'&&url.port&&url.pathname==='/'&&!url.search&&!url.hash&&!url.username&&!url.password,
    'CANVAS_RUNTIME_ENDPOINT','shards must use the isolated loopback runtime probe service');
  return {...scope,mode:'shard',shardId:env.GEOMETRY_CDP_SHARD,planSha256:plan.sha256};
}
function unitsFor(plan,shardId) {
  requireThat(IDS.includes(shardId),'CANVAS_FAKE_SCOPE','unknown shard');
  return plan.units.filter(unit=>unit.owner===shardId);
}
function projection(plan,shardId) {
  return Object.fromEntries(unitsFor(plan,shardId).flatMap(unit=>unit.sections.map(key=>[key,plan.golden.sections[key]])));
}
function selected(plan,scope,id,legacyPredicate) {
  if(scope.mode!=='shard')return legacyPredicate;
  const unit=plan.units.find(item=>item.id===id);
  requireThat(unit,'CANVAS_UNKNOWN_UNIT',id);
  return unit.owner===scope.shardId;
}
function createJournal(plan,shardId,emit) {
  const wanted=unitsFor(plan,shardId),events=[],counts={},visited=new Set();let active=null,next=0,current=null,unitVisited=[];
  function event(row){const value={seq:events.length,...row};events.push(value);emit(value);}
  return {
    begin(id){requireThat(!active&&wanted[next]?.id===id,'CANVAS_UNOWNED_EXECUTION',id);active=wanted[next];unitVisited=[];event({type:'unit-begin',unit:id});},
    end(id){requireThat(active?.id===id,'CANVAS_UNIT_END',id);
      requireThat(same([...unitVisited].sort(),[...active.sections].sort()),'CANVAS_MISSING_SECTION',id);
      event({type:'unit-end',unit:id});active=null;next++;},
    section(key,header){requireThat(active&&active.sections.includes(key),'CANVAS_UNOWNED_EXECUTION',key);
      requireThat(typeof header==='string'&&floor.sectionOf(header)===key,'CANVAS_SECTION_HEADER',key);
      if(!unitVisited.includes(key)){
        requireThat(!active.orderedSections||active.sections[unitVisited.length]===key,'CANVAS_DEPENDENCY_ORDER',key);
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
  requireThat(result.goldenCompare==='matched (shard projection)','CANVAS_GOLDEN_NOT_COMPARED');
  requireThat(result.scope?.mode==='shard'&&result.scope.shardId===shardId&&result.scope.planSha256===plan.sha256&&
    same(result.scope.filters,[])&&same(result.scope.modifiers,[]),'CANVAS_FAKE_SCOPE');
  requireThat(result.failedAssertions===0&&same(result.skipped,[])&&(!result.sectionsFailed||same(result.sectionsFailed,{})),
    'CANVAS_ASSERTION_FAILED','result failure/skip');
  requireThat(result.passedAssertions===assertions&&same(result.sections,actual),'CANVAS_FAKE_SUMMARY','counts differ from actual journal');
  requireThat(floor.compare({sections:projection(plan,shardId)},{sections:actual}).length===0,'CANVAS_COUNT_DRIFT');
  return {shard:shardId,sections:actual,assertions,units:unitsFor(plan,shardId).map(unit=>unit.id)};
}
function verifyAggregate(plan,shards) {
  requireThat(Array.isArray(shards)&&shards.length===IDS.length,'CANVAS_MISSING_SHARD');
  const seen=new Set(),sections={},units=new Set();
  for(const shard of shards){
    requireThat(IDS.includes(shard.shard)&&!seen.has(shard.shard),'CANVAS_DUPLICATE_SHARD');seen.add(shard.shard);
    for(const unit of shard.units){requireThat(!units.has(unit),'CANVAS_DUPLICATE_UNIT');units.add(unit);}
    requireThat(same(shard.units,unitsFor(plan,shard.shard).map(unit=>unit.id)),'CANVAS_MISSING_UNIT');
    for(const [key,count] of Object.entries(shard.sections)){
      requireThat(!Object.hasOwn(sections,key),'CANVAS_OVERLAPPING_SECTION',key);sections[key]=count;
    }
  }
  requireThat(floor.compare(plan.golden,{sections}).length===0,'CANVAS_GOLDEN_CHANGED');
  return {sections,sectionCount:Object.keys(sections).length,assertions:Object.values(sections).reduce((a,b)=>a+b,0)};
}

module.exports={IDS,EXTENSIONS,stable,sha,buildPlan,loadPlan,configure,unitsFor,projection,selected,createJournal,verifyTrace,verifyAggregate};
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
