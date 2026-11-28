'use strict';
/* Test the shipped renderer and event handler. This is not a layout oracle;
 * P4549 and the cold-profile browser driver own painted visibility. */
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(process.env.GEOMETRY_D09_DISCOVERY_SOURCE||path.join(__dirname,'../geometry-web/engineering-workspace.js'),'utf8');
const boundary='return {configure,open,close,refresh:()=>load(false),get isOpen()';
assert.equal(source.split(boundary).length,2,'actual workspace export boundary is unique');
const executable=source.replace(boundary,'return {__discoveryTest:{state,selectTarget,renderApply,renderGridFlow,setPath,handleClick,buildOperations,draftContent,attach:value=>{dialog=value;}},configure,open,close,refresh:()=>load(false),get isOpen()');
const plain=value=>JSON.parse(JSON.stringify(value));
function fixture(overrides={gap:{kind:'literal',value:4}}){
  const env={window:{},GeometryApplication:require('../geometry-app/application.js')};
  vm.runInNewContext(executable,env,{filename:'engineering-workspace.production.js'});
  const seam=env.window.EngineeringWorkspace.__discoveryTest,s=seam.state;
  s.snapshot={placements:[{id:1,name:'測試面',loops:[[[0,0],[1000,0],[1000,800],[0,800]]]},{id:2,name:'另一面'}],
    grids:[{id:7,placement_id:1},{id:8,placement_id:2}],timbers:[{id:9,placement_id:1},{id:10,placement_id:2}],sources:[],
    specs:[{name:'FaceGap',value:6}],materials:[{id:'stock',version:2,name:'截面規格',type:'timber',A:27,B:33}],
    methods:[{id:'method',version:1,name:'工程做法',gap:4}],applications:[{id:'face-app',placement_id:1,
      method:{id:'method',version:1},longAxis:null,mainAlong:null,overrides:plain(overrides)}]};
  seam.selectTarget(1,7);s.activePlacement=1;
  s.gridFlow={placementId:1,gridId:7,route:'method',method:{id:'method',version:1},panel:null,
    longAxis:'u',mainAlong:'u',gaps:{u:'4',v:'4'},anchors:{u:'0',v:'0'}};
  return {seam,s,target:s.application.targets[1],render:()=>seam.renderApply()};
}
function overview(html){
  const found=html.match(/<details\b[^>]*id="ewOverrideOverview"[^>]*>[\s\S]*?<\/details>/);
  assert.ok(found,'D09_DISCOVERY_FIRST_SCREEN_OVERVIEW');
  return found[0];
}
function count(html,name){return Number(overview(html).match(new RegExp('data-ew-'+name+'-count="(\\d+)"'))?.[1]);}
function summary(html){return overview(html).match(/<summary\b[^>]*>([\s\S]*?)<\/summary>/)?.[1];}

test('D09 discovery starts before editable fields and preserves exact native and draft data',async()=>{
  const h=fixture(),before=JSON.stringify(h.s),draft=h.seam.draftContent();
  const operations=()=>h.seam.buildOperations({action:'apply',draft:plain(h.s.application)},h.s.snapshot);
  const original=plain(await operations()),html=h.render(),visible=summary(html);
  assert.ok(html.indexOf('id="ewOverrideOverview"')<html.indexOf('data-ew-field="application.method"'),'D09_DISCOVERY_BEFORE_FIRST_FIELD');
  assert.match(visible,/已套用覆寫 1 項/,'D09_DISCOVERY_SAVED_COUNT');
  assert.match(visible,/縫寬[^<]*明設 4 mm/,'D09_DISCOVERY_SAVED_VALUE');
  assert.doesNotMatch(overview(html),/<details[^>]*\bopen(?:\s|>)/,'D09_DISCOVERY_NO_AUTO_EXPANSION');
  assert.equal(JSON.stringify(h.s),before,'D09_DISCOVERY_READ_ONLY');
  assert.equal(h.seam.draftContent(),draft,'D09_DISCOVERY_ZERO_DRAFT_WRITE');
  assert.deepEqual(plain(await operations()),original,'D09_DISCOVERY_COMMANDS_UNCHANGED');
});

test('D09 discovery counts explicit zero and same-value overrides by saved definition',()=>{
  const h=fixture({gap:{kind:'literal',value:0}}),html=h.render();
  assert.equal(count(html,'face'),1,'D09_DISCOVERY_ZERO_COUNTS');
  assert.match(summary(html),/明設 0 mm/,'D09_DISCOVERY_ZERO_VISIBLE');
  h.s.snapshot.applications[0].overrides.gap.value=4;
  assert.equal(count(h.render(),'face'),1,'D09_DISCOVERY_EQUAL_DEFAULT_COUNTS');
});

test('D09 discovery retains named and fixed-version source identities and both direction overrides',()=>{
  const h=fixture({gap:{kind:'spec',name:'FaceGap'},'primary.A':{kind:'material',id:'stock',version:2,field:'A'},
    'secondary.B':{kind:'literal',value:25}});
  h.s.snapshot.applications[0].longAxis='u';h.s.snapshot.applications[0].mainAlong='v';
  h.s.snapshot.applications[0].anchorOptions={u:{kind:'coordinate',value:75},v:{kind:'coordinate',value:50}};
  const html=h.render(),detail=overview(html);
  assert.equal(count(html,'face'),5,'D09_DISCOVERY_ALL_FACE_FIELDS');
  assert.match(detail,/具名尺寸「FaceGap」/,'D09_DISCOVERY_NAMED_SOURCE');
  assert.match(detail,/截面規格 · v2 · A mm/,'D09_DISCOVERY_MATERIAL_IDENTITY');
  assert.match(detail,/面材長邊對應[^<]*長邊沿 u/,'D09_DISCOVERY_LONG_AXIS');
  assert.match(detail,/主支長度方向[^<]*沿 v/,'D09_DISCOVERY_MAIN_ALONG');
  assert.doesNotMatch(detail,/明設 27 mm/,'D09_DISCOVERY_NO_SOURCE_FLATTENING');
});

test('D09 discovery separates actual object overrides and excludes other faces and ordinary bindings',()=>{
  const h=fixture({});h.s.snapshot.sources=[
    {target:{kind:'grid',id:7,axis:'u',field:'gap'},source:{kind:'application',id:'face-app',field:'gap'},override:{kind:'literal',value:0},effective:0},
    {target:{kind:'timber',id:9,field:'A'},source:{kind:'literal',value:30},override:{kind:'spec',name:'FaceGap'},effective:6},
    {target:{kind:'timber',id:9,field:'B'},source:{kind:'literal',value:30},override:null,effective:30},
    {target:{kind:'grid',id:8,axis:'u',field:'gap'},override:{kind:'literal',value:9},effective:9},
    {target:{kind:'timber',id:10,field:'A'},override:{kind:'literal',value:50},effective:50}
  ];
  h.s.snapshot.applications.push({id:'other-face-app',placement_id:2,method:{id:'method',version:1},overrides:{gap:{kind:'literal',value:7}}});
  h.seam.selectTarget(2,8);
  const html=h.render(),detail=overview(html);
  assert.equal(count(html,'face'),0);assert.equal(count(html,'object'),2,'D09_DISCOVERY_OBJECT_SCOPE');
  assert.match(html,/套用目標 · 已選 2 個放置面/,'D09_DISCOVERY_MULTIPLE_TARGETS_SELECTED');
  assert.match(summary(html),/放置 #1/,'D09_DISCOVERY_CURRENT_FACE_LABEL');
  assert.doesNotMatch(summary(html),/放置 #2|明設 7 mm/,'D09_DISCOVERY_NOT_ALL_SELECTED_SUMMARY');
  assert.match(detail,/網格 #7 · u 縫寬/);assert.match(detail,/角材 #9 · A/);
  assert.doesNotMatch(detail,/網格 #8|角材 #10|角材 #9 · B/,'D09_DISCOVERY_NO_FALSE_OVERRIDE');
  assert.match(detail,/生效值：0 mm/,'D09_DISCOVERY_OBJECT_ZERO_EFFECTIVE');
  h.s.activePlacement=2;
  const other=h.render();assert.equal(count(other,'face'),1,'D09_DISCOVERY_SWITCH_FACE_COUNT');
  assert.equal(count(other,'object'),2,'D09_DISCOVERY_SWITCH_OBJECT_SCOPE');
  assert.match(summary(other),/放置 #2/,'D09_DISCOVERY_OTHER_FACE_VISIBLE_SCOPE');
  assert.match(summary(other),/明設 7 mm/,'D09_DISCOVERY_OTHER_SELECTED_FACE_VISIBLE');
});

test('D09 discovery describes committed overrides even while a removal or replacement is only a draft',()=>{
  const h=fixture();h.target.preserveOverrides=false;h.target.overrides.gap={mode:'literal',value:'99'};
  h.target.objectOverrides['draft-only']={mode:'literal',value:'31'};
  const html=h.render();assert.equal(count(html,'face'),1,'D09_DISCOVERY_DRAFT_NOT_SAVED');
  assert.match(summary(html),/明設 4 mm/);assert.doesNotMatch(summary(html),/99|31/);
  h.s.snapshot.applications[0].overrides={};
  assert.equal(count(h.render(),'face'),0,'D09_DISCOVERY_UNDO_REFRESH');
  h.s.snapshot.applications[0].overrides={gap:{kind:'literal',value:4}};
  assert.equal(count(h.render(),'face'),1,'D09_DISCOVERY_REDO_REFRESH');
  assert.deepEqual(plain(h.target.overrides),{gap:{mode:'literal',value:'99'}});
});

test('D09 discovery is shared by the material-grid route without creating editing state',()=>{
  const h=fixture(),before=JSON.stringify(h.s);h.s.mode='grid';const baseline=JSON.stringify(h.s);
  const html=h.seam.renderGridFlow();assert.equal(count(html,'face'),1,'D09_DISCOVERY_GRID_ROUTE');
  assert.ok(html.indexOf('id="ewOverrideOverview"')<html.indexOf('data-ew-field="gridFlow.route"'),'D09_DISCOVERY_GRID_FIRST_FIELD');
  assert.match(summary(html),/明設 4 mm/);assert.doesNotMatch(overview(html),/data-ew-reveal-overrides/);
  assert.equal(JSON.stringify(h.s),baseline,'D09_DISCOVERY_GRID_READ_ONLY');
  assert.notEqual(baseline,before);
});

test('D09 discovery says zero without guessing from values and escapes untrusted source labels',()=>{
  const h=fixture({}),empty=h.render();assert.equal(count(empty,'face'),0);assert.equal(count(empty,'object'),0);
  assert.match(summary(empty),/已套用覆寫 0 項/,'D09_DISCOVERY_ZERO_STATE');
  h.s.snapshot.applications[0].overrides.gap={kind:'spec',name:'<img onerror="bad">'};
  const html=overview(h.render());assert.doesNotMatch(html,/<img/,'D09_DISCOVERY_ESCAPED');assert.match(html,/&lt;img/);
});

test('D09 discovery reveal is an explicit display action with no draft or World changes',()=>{
  const h=fixture({'primary.A':{kind:'literal',value:40}}),events=[],details={open:false,contains:()=>true,parentElement:null};
  const inner={open:false,parentElement:{closest:()=>details}};
  const control={closest:()=>inner,focus:options=>events.push(['focus',options]),scrollIntoView:options=>events.push(['scroll',options])};
  details.querySelector=()=>control;
  const button={dataset:{ewRevealOverrides:'face'},hasAttribute:name=>name==='data-ew-reveal-overrides',getAttribute:()=>null};
  h.seam.attach({contains:()=>true,querySelector:()=>details});
  const before=JSON.stringify(h.s);h.seam.handleClick({target:{closest:()=>button}});
  assert.equal(details.open,true,'D09_DISCOVERY_EXPLICIT_REVEAL');
  assert.equal(inner.open,true,'D09_DISCOVERY_NESTED_ROLE_REVEALED');
  assert.deepEqual(plain(events),[['focus',{preventScroll:true}],['scroll',{block:'center',inline:'nearest'}]],'D09_DISCOVERY_USER_CONTROLLED_FOCUS');
  assert.equal(JSON.stringify(h.s),before,'D09_DISCOVERY_REVEAL_ZERO_WRITE');
});

test('D09 discovery reveal keeps the whole field inside the reported fractional scroll clip',()=>{
  // Real handler; an independent integer-scroll model for the exact worker
  // rectangle/clip, then 128 fractional translations. This is not Chrome paint.
  const cases=[0,...Array.from({length:128},(_,i)=>(i+1)/128)];
  for(const offset of cases){
    const h=fixture(),before=JSON.stringify(h.s),clip={top:324.640625,bottom:751.640625};
    let top=707.8125+offset,bottom=751.8125+offset,focused=false,scrolls=0;
    const details={open:false,contains:()=>true,parentElement:null};
    const control={closest:()=>details,focus:options=>{
      assert.deepEqual(plain(options),{preventScroll:true},'D09_DISCOVERY_REVEAL_FOCUS_NO_SCROLL');focused=true;
    },scrollIntoView:options=>{
      scrolls++;
      assert.equal(options.inline,'nearest','D09_DISCOVERY_REVEAL_INLINE_UNCHANGED');
      const delta=options.block==='center'?(top+bottom-clip.top-clip.bottom)/2:
        top<clip.top?top-clip.top:bottom>clip.bottom?bottom-clip.bottom:0;
      const integerScroll=Math.round(delta);top-=integerScroll;bottom-=integerScroll;
    }};
    details.querySelector=()=>control;
    const button={dataset:{ewRevealOverrides:'face'},hasAttribute:n=>n==='data-ew-reveal-overrides',getAttribute:()=>null};
    h.seam.attach({contains:()=>true,querySelector:()=>details});
    h.seam.handleClick({target:{closest:()=>button}});
    assert.equal(details.open,true,'D09_DISCOVERY_REVEAL_OPENS_DETAILS');
    assert.equal(focused,true,'D09_DISCOVERY_REVEAL_FOCUSED');
    assert.equal(scrolls,1,'D09_DISCOVERY_REVEAL_ONE_SCROLL');
    assert.ok(top>=clip.top&&bottom<=clip.bottom,
      'D09_DISCOVERY_REVEAL_STRICT_CLIP '+JSON.stringify({offset,top,bottom,clip}));
    assert.equal(JSON.stringify(h.s),before,'D09_DISCOVERY_REVEAL_ZERO_WRITE');
  }
});

/* This executes the driver's real coldLanding function with deterministic read
 * replies. It verifies the native read contract, never browser painting. Native
 * engineering-read has applications/sources; references supplies grids/timbers.
 * GEOMETRY_D09_COLD_DRIVER_SOURCE permits reproducing the original v1 defect. */
const coldDriver=fs.readFileSync(process.env.GEOMETRY_D09_COLD_DRIVER_SOURCE||path.join(__dirname,'integration/d09_override_discovery_browser.cjs'),'utf8');
const coldStart='async function coldLanding(width,expectedDump){',coldEnd='async function unchangedPreview(';
assert.equal(coldDriver.split(coldStart).length,2,'actual coldLanding boundary is unique');
assert.equal(coldDriver.split(coldEnd).length,2,'actual coldLanding end boundary is unique');
const coldFunction=coldDriver.slice(coldDriver.indexOf(coldStart),coldDriver.indexOf(coldEnd));
function nativeFixture(){
  return {engineering:{ok:true,revision:13,state:{
    applications:[{id:'face-app',placement_id:1,overrides:{gap:{kind:'literal',value:4}},longAxis:null,mainAlong:null}],
    sources:[
      {target:{kind:'grid',id:1,axis:'u',field:'gap'},override:{kind:'literal',value:0}},
      {target:{kind:'grid',id:1,axis:'v',field:'gap'},override:null},
      {target:{kind:'timber',id:9,field:'A'},override:{kind:'literal',value:30}},
      {target:{kind:'grid',id:2,axis:'u',field:'gap'},override:{kind:'literal',value:7}},
      {target:{kind:'timber',id:10,field:'A'},override:{kind:'literal',value:20}}
    ]}},references:{ok:true,grids:[{id:1,surface:1},{id:2,surface:2}],
      timbers:[{id:9,surface:1},{id:10,surface:2}]}};
}
async function runColdOracle(data,{objects=2,lastRevision=data.engineering.revision}={}){
  const commands=[],checks=[],clicks=[],writes=[],world='unchanged native dump';let reads=0,engineeringReads=0;
  const native=async cmd=>{
    commands.push(cmd);
    if(cmd==='references')return plain(data.references);
    assert.equal(cmd,'engineering-read','D09_COLD_READ_ONLY_COMMAND');
    const reply=plain(data.engineering);if(++engineeringReads>1)reply.revision=lastRevision;return reply;
  };
  const context={assert,path,OUT:'/no-browser-or-filesystem-is-used',
    controlProbe:function controlProbe(){},controlWithinClip:p=>p.inClip===true,
    b:{screenshot:async()=>{}},write:(name,data)=>writes.push({name,data:plain(data)}),
    read:async()=>{
      reads++;
      if(reads===1)return {inClip:true,rect:{height:64}};
      if(reads===2)return {width:390,height:844,windowY:0,contentY:0,editorY:0,open:false,fontSize:14,
        face:1,object:objects,summary:'面 1 · 放置 #1 · 已套用覆寫 '+(1+objects)+' 項 縫寬：明設 4 mm'};
      if(reads===3)return {inClip:true,active:true};
      assert.equal(reads,4,'D09_COLD_EXPECTED_READ_SEQUENCE');return '4';
    },native,nativeState:async()=>(await native('engineering-read')).state,
    check:(name,actual,expected=true)=>{assert.deepEqual(actual,expected,name);checks.push(name);},
    click:async selector=>clicks.push(selector),history:async()=>({undo:1,redo:0}),dump:async()=>world,field:'#literal-gap-'};
  vm.runInNewContext(coldFunction+'\nthis.runCold=coldLanding;',context,{filename:'d09-cold-driver.actual-function.js'});
  await context.runCold(390,world);
  return {commands,checks,clicks,writes,reads};
}

test('D09 cold driver counts raw native sources using separate references ownership',async()=>{
  const data=nativeFixture(),before=JSON.stringify(data);let result;
  await assert.doesNotReject(async()=>{result=await runColdOracle(data);},'D09_COLD_NATIVE_SHAPE');
  assert.deepEqual(result.commands,['engineering-read','references','engineering-read'],'D09_COLD_NATIVE_SPLIT_READ');
  assert.equal(result.checks.length,4,'D09_COLD_ORIGINAL_CHECKS_RETAINED');
  assert.equal(result.reads,4,'D09_COLD_NO_EXTRA_UI_INTERACTION');
  assert.deepEqual(result.clicks,['#ewOverrideOverview > summary','[data-ew-reveal-overrides="face"]'],'D09_COLD_EXPLICIT_REVEAL_ONLY');
  assert.equal(result.writes.filter(r=>r.name==='cold-native-390.json').length,1,'D09_COLD_RAW_READS_RECORDED');
  assert.equal(JSON.stringify(data),before,'D09_COLD_ORACLE_ZERO_INPUT_WRITE');
});

test('D09 cold driver refuses missing native lists and mixed revisions instead of guessing zero',async()=>{
  for(const field of ['sources','applications']){
    const data=nativeFixture();delete data.engineering.state[field];
    await assert.rejects(runColdOracle(data),/D09_COLD_NATIVE_READ_SHAPE/,'D09_COLD_REQUIRED_ENGINEERING_'+field);
  }
  for(const field of ['grids','timbers']){
    const data=nativeFixture();delete data.references[field];
    await assert.rejects(runColdOracle(data),/D09_COLD_NATIVE_READ_SHAPE/,'D09_COLD_REQUIRED_REFERENCES_'+field);
  }
  const withoutRevision=nativeFixture();delete withoutRevision.engineering.revision;
  await assert.rejects(runColdOracle(withoutRevision),/D09_COLD_NATIVE_READ_SHAPE/,'D09_COLD_REQUIRED_REVISION');
  await assert.rejects(runColdOracle(nativeFixture(),{lastRevision:14}),/D09_COLD_NATIVE_REVISION/,'D09_COLD_MIXED_REVISION_REJECTED');
});

test('D09 cold driver preserves explicit zero and excludes other faces and foreign target kinds',async()=>{
  const data=nativeFixture();
  data.references.timbers[0]={id:9,geometry:{surface:1}};
  data.engineering.state.sources.push({target:{kind:'guide',id:9},override:{kind:'literal',value:6}});
  await assert.doesNotReject(runColdOracle(data),'D09_COLD_NATIVE_OWNERSHIP');
  data.engineering.state.sources=data.engineering.state.sources.filter(r=>r.override==null);
  await assert.doesNotReject(runColdOracle(data,{objects:0}),'D09_COLD_NATIVE_ZERO_OBJECTS');
});
