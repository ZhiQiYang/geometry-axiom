'use strict';
/* R386: pure registry/dispatcher controls. No browser receipt is fabricated. */
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const ROOT=path.resolve(__dirname,'../..');
const API_FILE=path.join(ROOT,'geometry-web/canvas_registry.js');
const BASE='f'.repeat(40);
const copy=value=>structuredClone(value);
const write=(root,relative,value)=>{
  const target=path.join(root,relative);fs.mkdirSync(path.dirname(target),{recursive:true});
  fs.writeFileSync(target,typeof value==='string'?value:JSON.stringify(value,null,2)+'\n');
};
function fixture(root){
  write(root,'geometry-web/canvas_shards.json',{schema:'geometry-cdp-shards/1',shards:[
    {index:1,sections:['Setup','P88']},{index:2,sections:['P72','P353','P359']}],
    boundaries:[{after:'P88',before:'P72',localStorage:{}}]});
  write(root,'geometry-web/cdp_sections.golden.json',{schema:'geometry-cdp-sections/1',mode:'full',total:9,
    sections:{Setup:0,P88:2,P72:1,P353:4,P359:2}});
}
test('R386 canvas fragments preserve every legacy assertion, pin, owner and handoff',async()=>{
  assert.ok(fs.existsSync(API_FILE),'R386_CANVAS_REGISTRY_API_MISSING: per-section registry is not implemented');
  const R=require(API_FILE),root=fs.mkdtempSync(path.join(os.tmpdir(),'r386-canvas-'));
  try{
    fixture(root);
    const beforePlan=fs.readFileSync(path.join(root,R.PLAN)),beforeGolden=fs.readFileSync(path.join(root,R.GOLDEN));
    const first=R.migrate(root,{baseSha:BASE,outdir:path.join(root,'stage-a')});
    const second=R.migrate(root,{baseSha:BASE,outdir:path.join(root,'stage-b')});
    assert.deepEqual(first,second,'R386_CANVAS_DETERMINISTIC_MIGRATION');
    for(const relative of first.files){
      assert.deepEqual(fs.readFileSync(path.join(root,'stage-a',relative)),fs.readFileSync(path.join(root,'stage-b',relative)),relative);
      write(root,relative,fs.readFileSync(path.join(root,'stage-a',relative)).toString('utf8'));
    }
    for(const relative of first.deletes)fs.unlinkSync(path.join(root,relative));
    const registry=R.load(root);
    assert.deepEqual(registry.plan,JSON.parse(beforePlan),'R386_CANVAS_PLAN_EXACT');
    assert.deepEqual(registry.golden,JSON.parse(beforeGolden),'R386_CANVAS_GOLDEN_EXACT');
    assert.deepEqual(fs.readFileSync(path.join(root,R.ARCHIVE_PLAN)),beforePlan,'R386_CANVAS_PLAN_BYTE_PIN');
    assert.deepEqual(fs.readFileSync(path.join(root,R.ARCHIVE_GOLDEN)),beforeGolden,'R386_CANVAS_GOLDEN_BYTE_PIN');
    assert.equal(registry.fragments.length,5,'R386_CANVAS_ZERO_ASSERTION_SECTION_RETAINED');
    assert.equal(registry.fragments.every(row=>row.cost===null),true,'R386_CANVAS_NO_INVENTED_LEGACY_COST');
    assert.deepEqual(R.legacyView(root).golden,registry.golden);
    const preserved=R.migrate(root,{baseSha:'a'.repeat(40),outdir:path.join(root,'stage-c')});
    for(const relative of first.files)assert.deepEqual(fs.readFileSync(path.join(root,'stage-c',relative)),fs.readFileSync(path.join(root,relative)),'R386_CANVAS_IDEMPOTENT '+relative);
    assert.deepEqual(preserved.files,first.files);
    const fragment='geometry-web/cdp_sections.d/P88.json';
    const original=fs.readFileSync(path.join(root,fragment),'utf8');
    const withdraw=(id,mutate,restore,code)=>{
      const run=()=>spawnSync(process.execPath,[API_FILE,'check','--root',root],{encoding:'utf8'});
      const before=run();assert.equal(before.status,0,id+' baseline '+before.stderr);
      mutate();const bad=run();assert.equal(bad.status,1,id+' withdrawn '+bad.stderr);
      assert.match(bad.stderr,new RegExp(code),id+' named failure');
      assert.doesNotMatch(bad.stderr,/SyntaxError|ReferenceError|MODULE_NOT_FOUND|ENOENT/,id+' infrastructure is not a kill');
      restore();const after=run();assert.equal(after.status,0,id+' restored '+after.stderr);
      console.log(id+' 0/1/0');
    };
    withdraw('R386_CANVAS_MISSING_FRAGMENT',()=>fs.unlinkSync(path.join(root,fragment)),()=>write(root,fragment,original),'R386_CANVAS_MISSING_FRAGMENT');
    withdraw('R386_CANVAS_COUNT_DRIFT',()=>{const value=JSON.parse(original);value.assertions--;write(root,fragment,value);},()=>write(root,fragment,original),'R386_CANVAS_COUNT_DRIFT');
    withdraw('R386_CANVAS_OVERLAPPING_OWNER',()=>{const value=JSON.parse(original);value.unit=[1,2];write(root,fragment,value);},()=>write(root,fragment,original),'R386_CANVAS_OWNER');
    withdraw('R386_CANVAS_UNRECEIPTED_COST',()=>{const value=JSON.parse(original);value.cost={milliseconds:1};write(root,fragment,value);},()=>write(root,fragment,original),'R386_CANVAS_COST');
    withdraw('R386_CANVAS_LEGACY_BYTE_PIN',()=>fs.appendFileSync(path.join(root,R.ARCHIVE_PLAN),' '),()=>write(root,R.ARCHIVE_PLAN,beforePlan.toString('utf8')),'R386_CANVAS_ARCHIVE_PIN');
    withdraw('R386_CANVAS_DUPLICATE_ID',()=>write(root,'geometry-web/cdp_sections.d/duplicate.json',original),()=>fs.unlinkSync(path.join(root,'geometry-web/cdp_sections.d/duplicate.json')),'R386_CANVAS_FRAGMENT_NAME');
    withdraw('R386_CANVAS_ORPHAN_MODULE',()=>write(root,'geometry-web/canvas_sections/P999.js','module.exports=async()=>{};\n'),()=>fs.unlinkSync(path.join(root,'geometry-web/canvas_sections/P999.js')),'R386_CANVAS_MODULE_INVENTORY');
    withdraw('R386_CANVAS_UNKNOWN_KEYS',()=>{const value=JSON.parse(original);value.disableAssertions=true;write(root,fragment,value);},()=>write(root,fragment,original),'R386_CANVAS_FRAGMENT_KEYS');
    withdraw('R386_CANVAS_DUPLICATE_JSON_KEY',()=>write(root,fragment,original.replace('"id": "P88",','"id": "P88", "id": "P88",')),()=>write(root,fragment,original),'R386_CANVAS_DUPLICATE_JSON_KEY');
    withdraw('R386_CANVAS_FRAGMENT_LF',()=>write(root,fragment,original.replace(/\n/g,'\r\n')),()=>write(root,fragment,original),'R386_CANVAS_FRAGMENT_LF');
    const pending=path.join(root,'tests/.registry-migration-pending');
    withdraw('R386_INTERRUPTED_MIGRATION',()=>fs.mkdirSync(pending,{recursive:true}),()=>fs.rmSync(pending,{recursive:true}),'R386_INTERRUPTED_MIGRATION');
    const directory=path.join(root,'geometry-web/cdp_sections.d'),moved=directory+'-original';
    withdraw('R386_CANVAS_PARENT_SYMLINK',()=>{fs.renameSync(directory,moved);fs.symlinkSync(moved,directory,'dir');},()=>{fs.unlinkSync(directory);fs.renameSync(moved,directory);},'R386_CANVAS_DIRECTORY');
    // Partial capture is explicitly non-acceptance. A missing CI receipt cannot
    // be filled by an estimated count or elapsed number in a fragment.
    const moduleText="module.exports=async h=>{h.calls.push('P999');};\n";
    write(root,'geometry-web/canvas_sections/P999.js',moduleText);
    const candidate={schema:'geometry-canvas-section/1',id:'P999',assertions:3,unit:2,
      order:{after:[],before:[]},execution:{kind:'module',module:'geometry-web/canvas_sections/P999.js',export:'default'},
      provenance:{kind:'candidate'},cost:null,balance:null};
    write(root,'geometry-web/cdp_sections.d/P999.json',candidate);
    assert.throws(()=>R.load(root),/R386_CANVAS_COST_RECEIPT_REQUIRED/);
    const provisional=R.load(root,{allowCandidates:true});
    assert.equal(provisional.acceptance,false);
    assert.deepEqual(provisional.plan.shards[1].sections,['P72','P353','P999','P359']);
    const calls=[],helpers={calls,eval_:async()=>({local:{},session:{}})};
    await R.dispatch(root,{mode:'partial',module:'P999'},helpers,{allowCandidates:true});
    assert.deepEqual(calls,['P999'],'R386_CANVAS_MODULE_EXECUTES');
    calls.length=0;await R.dispatch(root,{mode:'shard',shard:{index:1}},helpers,{allowCandidates:true});
    assert.deepEqual(calls,[],'R386_CANVAS_MODULE_NOT_OTHER_SHARD');
    const added=copy(candidate);added.id='P998';added.execution.module='geometry-web/canvas_sections/P998.js';
    write(root,added.execution.module,"module.exports=async h=>{h.calls.push('P998');};\n");write(root,'geometry-web/cdp_sections.d/P998.json',added);
    assert.deepEqual(R.load(root,{allowCandidates:true}).plan.shards[1].sections,['P72','P353','P998','P999','P359'],'R386_CANVAS_PARALLEL_INSERTIONS_DETERMINISTIC');
    assert.deepEqual(R.legacyView(root,{allowCandidates:true}).plan,registry.plan,'R386_CANVAS_LEGACY_VIEW_USES_ACTIVE_VALUES');
    let now=0n;const timer=R.createSectionTimer(()=>now);timer.enter('Setup');now=5000000n;timer.enter('P88');now=9000000n;timer.enter('P88');now=11000000n;
    assert.deepEqual(timer.finish(),{Setup:5,P88:6},'R386_CANVAS_MONOTONIC_SECTION_COST');
    assert.deepEqual(timer.finish(),{Setup:5,P88:6},'R386_CANVAS_TIMER_FINISH_IDEMPOTENT');
    // Costs below are explicit synthetic pure-function fixtures, never CI
    // receipts. The production loader only reaches the solver after the real
    // unit/section source-bound receipt validators have returned these values.
    const units={1:{milliseconds:100},2:{milliseconds:100}},rows=[
      {id:'P1',order:{after:[],before:[]}},{id:'P2',order:{after:[],before:[]}}];
    const costs={P1:{milliseconds:80},P2:{milliseconds:20}},allowed={P1:[1,2],P2:[1,2]};
    const balanced=R.solvePlacement(rows,costs,units,allowed);
    assert.equal(balanced.algorithm,'exact-meet-in-the-middle');assert.equal(balanced.maximumMilliseconds,180);
    assert.notEqual(balanced.assignment.P1,balanced.assignment.P2,'R386_CANVAS_REAL_COST_CHANGES_PLACEMENT');
    assert.deepEqual(R.solvePlacement([...rows].reverse(),costs,units,allowed),balanced,'R386_CANVAS_PLANNER_ORDER_INDEPENDENT');
    assert.throws(()=>R.solvePlacement(rows,costs,{},allowed),/R386_CANVAS_UNIT_COST_REQUIRED/);
    assert.throws(()=>R.solvePlacement(rows,{P1:costs.P1},units,allowed),/R386_CANVAS_MEASURED_COST_REQUIRED/);
    const dependent=copy(rows);dependent[1].order.after=['P1'];
    const grouped=R.solvePlacement(dependent,costs,units,allowed);
    assert.equal(grouped.assignment.P1,grouped.assignment.P2,'R386_CANVAS_DEPENDENCY_GROUP_NOT_SPLIT');
    assert.throws(()=>R.solvePlacement(dependent,costs,units,{P1:[1],P2:[2]}),/R386_CANVAS_DEPENDENCY_SLOT_CONFLICT/);
    const many=Array.from({length:25},(_,index)=>({id:'P'+(1000+index),order:{after:[],before:[]}}));
    const manyCosts=Object.fromEntries(many.map((row,index)=>[row.id,{milliseconds:index+1}]));
    const manyAllowed=Object.fromEntries(many.map(row=>[row.id,[1,2]]));
    const bounded=R.solvePlacement(many,manyCosts,units,manyAllowed);
    assert.equal(bounded.algorithm,'deterministic-lpt');assert.equal(Object.keys(bounded.assignment).length,25);
    assert.deepEqual(R.solvePlacement([...many].reverse(),manyCosts,units,manyAllowed),bounded,'R386_CANVAS_BOUNDED_FALLBACK_DETERMINISTIC');
    const moduleFile='geometry-web/canvas_sections/P999.js',helper='geometry-web/custom-module-helper.cjs';
    write(root,moduleFile,"const helper=require('../custom-module-helper.cjs');module.exports=async h=>helper(h);\n");
    write(root,helper,"module.exports=async h=>{h.calls.push('one');};\n");
    const sourceHash=R.moduleSourceHash(root,moduleFile);
    write(root,helper,"module.exports=async h=>{h.calls.push('two');};\n");
    assert.notEqual(R.moduleSourceHash(root,moduleFile),sourceHash,'R386_CANVAS_TRANSITIVE_CJS_SOURCE_PIN');
    for(const unsafe of [
      "const r=require;r('../custom-module-helper.cjs');module.exports=async()=>{};",
      "module['require']('../custom-module-helper.cjs');module.exports=async()=>{};",
      "const {createRequire}=require('node:module');createRequire(__filename)('../custom-module-helper.cjs');module.exports=async()=>{};",
      "const fs=require('node:fs');const fixture=JSON.parse(fs.readFileSync(__dirname+'/fixture.json','utf8'));module.exports=async()=>fixture;",
      "const key='con'+'structor';const run=(async()=>{})[key];module.exports=async()=>{};",
      "import('../'+name);module.exports=async()=>{};"
    ]){write(root,moduleFile,unsafe+'\n');assert.throws(()=>R.moduleSourceHash(root,moduleFile),/R386_CANVAS_(?:INDIRECT|REFLECTIVE|UNPINNED|DYNAMIC)/,'R386_CANVAS_UNRESOLVED_LOADER_REJECTED');}
    write(root,moduleFile,moduleText);
    // R445: the reviewed independent CDP driver type (P2052) is exercised in
    // its own synthetic fixture below, inside this same test.
    await driverContract(R);
  }finally{fs.rmSync(root,{recursive:true,force:true});}
});
/* R445 driver contract. Everything below is a synthetic pure-function fixture:
 * the ZIP, receipt and stdout lines are built here and are never CI receipts.
 * The five closure files are byte copies of the real reviewed sources. */
const zipWrite=(file,members)=>{
  const code='import sys,json,zipfile,base64\nm=json.load(sys.stdin)\nwith zipfile.ZipFile(sys.argv[1],"w") as z:\n for n in sorted(m): z.writestr(n,base64.b64decode(m[n]))';
  const run=spawnSync(process.env.PYTHON||'python3',['-c',code,file],{input:JSON.stringify(Object.fromEntries(Object.entries(members).map(([k,v])=>[k,Buffer.from(v).toString('base64')])))});
  assert.equal(run.status,0,String(run.stderr));
};
async function driverContract(R){
  assert.ok(R.DRIVER_SECTIONS&&R.DRIVER_SECTIONS.P2052,'R386_CANVAS_DRIVER_TYPE_MISSING: reviewed independent CDP driver type is not implemented');
  const entry=R.DRIVER_SECTIONS.P2052,root=fs.mkdtempSync(path.join(os.tmpdir(),'r445-driver-'));
  const sha=raw=>require('node:crypto').createHash('sha256').update(raw).digest('hex');
  try{
    write(root,'geometry-web/canvas_shards.json',{schema:'geometry-cdp-shards/1',shards:[
      {index:1,sections:['Setup','P88']},{index:2,sections:['P72','P205','P353','P359']}],
      boundaries:[{after:'P88',before:'P72',localStorage:{}}]});
    write(root,'geometry-web/cdp_sections.golden.json',{schema:'geometry-cdp-sections/1',mode:'full',total:34,
      sections:{Setup:0,P88:2,P72:1,P205:25,P353:4,P359:2}});
    const migrated=R.migrate(root,{baseSha:BASE,outdir:path.join(root,'stage')});
    for(const relative of migrated.files)write(root,relative,fs.readFileSync(path.join(root,'stage',relative)).toString('utf8'));
    for(const relative of migrated.deletes)fs.unlinkSync(path.join(root,relative));
    fs.rmSync(path.join(root,'stage'),{recursive:true});
    const legacy=R.load(root);
    // R445 (7072803590): the scripts the pinned subprocess sites execute are copied too.
    const SUBPROCESS_SCRIPTS=['geometry-web/serve.py','geometry-web/start_local.py','tests/binaries.py'];
    for(const relative of [...entry.closure,...SUBPROCESS_SCRIPTS]){const target=path.join(root,relative);fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(path.join(ROOT,relative),target);}
    const dispatcher=["'use strict';",
      "const SCOPE_FLAGS=[];",
      "SCOPE_FLAGS.push('GEOMETRY_FRAMING_TEMPLATE_ONLY','"+entry.flag+"');",
      "async function main(){",
      "  if(cond) {",
      entry.guard.replace(/\n$/,''),
      "  if (!process.env.GEOMETRY_FRAMING_TEMPLATE_ONLY) {",
      "  if(inSequence(2))await p1284();",
      "  } // closes the FRAMING_TEMPLATE_ONLY guard, as in cdp_test.js",
      entry.dispatch.replace(/\n$/,''),
      (entry.following||"  if(inSequence(2))await p353();\n").replace(/\n$/,''),
      "  if(inSequence(2))await p359();",
      "  }",
      "}",""].join('\n');
    write(root,'geometry-web/cdp_test.js',dispatcher);
    const fragment='geometry-web/cdp_sections.d/P2052.json';
    R.stageDriver(root,'P2052');
    const candidate=R.load(root,{allowCandidates:true});
    assert.equal(candidate.acceptance,false,'R386_CANVAS_DRIVER_CANDIDATE_NOT_ACCEPTANCE');
    assert.throws(()=>R.load(root),/^Error: R386_CANVAS_COST_RECEIPT_REQUIRED/,'R386_CANVAS_DRIVER_RECEIPT_REQUIRED');
    // A fixed-anchor, measured driver: the synthetic CI capture below. Its
    // shape follows the official original (artifact 14732356182): real ZIP
    // .gcanvas members, the measuring script's own runtime probe and, when the
    // receipt schema lists it, the measuring script's own process ledger.
    const zipBytes=members=>{const file=path.join(root,'.zip-'+require('node:crypto').randomUUID());zipWrite(file,members);const raw=fs.readFileSync(file);fs.unlinkSync(file);return raw;};
    const scene=Buffer.from('reset\nline surface 1 origin 0 0 2500 u +x v +y outline 0,0 1,0 1,1 0,1\n');
    const archiveManifest=(mutate=()=>{})=>{const recipes=[{id:'r-v1',name:'v1',template:{id:'flat-ceiling',version:1,policyFingerprint:'1'.repeat(64)}},
      {id:'r-v2',name:'v2',template:{id:'flat-ceiling',version:2,policyFingerprint:'2'.repeat(64)}}];
      const value={schema:'framing-template-recipes/1',recipes};mutate(recipes[1]);
      return {projectId:'p',name:'n',sources:[],faces:[],featureAttachments:{schema:'geometry-feature-attachments/1',records:[
        {kind:'framing-template-recipes',schema:'framing-template-recipes/1',value}]},format:'geometry-canvas/19',models:[],faceProjections:[],
        sceneHash:sha(scene),requiredCapabilities:['framing-template-recipes/1']};};
    const gcanvas=manifest=>zipBytes({'world.scene':scene,'manifest.json':Buffer.from(JSON.stringify(manifest))});
    const RUNTIME_VERSION='c'.repeat(64);
    const build=(mutate=()=>{})=>{
      const identity=R.driverIdentity(root,'P2052'),folder=R.DRIVER_OUTPUTS+'/r06-formal-archive-fixture/';
      const saved=gcanvas(archiveManifest());
      const wrong=gcanvas(archiveManifest(recipe=>{recipe.template.policyFingerprint='0'.repeat(64);}));
      const unknown=gcanvas(archiveManifest(recipe=>{recipe.template.version=999;recipe.template.policyFingerprint='f'.repeat(64);}));
      const source={schema:'geometry-runtime/1',version:RUNTIME_VERSION,fresh:true,root:'/x',pid:41,session:'source-session'};
      const service={schema:'geometry-runtime/1',version:RUNTIME_VERSION,fresh:true,root:'/x',pid:42,session:'cold-session'};
      const scope={mode:'partial',filters:[entry.flag],modifiers:[],url:'http://127.0.0.1:18839/',feedbackDirectory:'/tmp/f',browserProfile:'/tmp/geometry-cdp-x',cdpPort:9333,browserPid:70};
      const lines=['CDP_SCOPE '+JSON.stringify(scope),'=== P2052. R03 政策 A 固定治具 矩形第二片與冷開 ===',...entry.assertions.map(name=>'P2052 '+name+' ✓ ')];
      const pkg={path:'/tmp/saved-1.gcanvas',bytes:saved.length,sha256:sha(saved),nativeService:service,sourceService:source,browserPid:77,profile:'/tmp/r06-cold-chrome-x'};
      const cold={sourceRuntime:source,service,profile:pkg.profile,browserPid:77,browserVersion:'synthetic',bridge:{},url:'http://127.0.0.1:1'};
      const result={schema:'geometry-cdp-result/1',scope,
        completed:true,passedAssertions:28,failedAssertions:0,skipped:[],sections:{P2052:28},sectionOrder:['P2052'],sectionElapsedMs:{P2052:1234.5},
        goldenCompare:'not compared (partial mode)',unexpectedBrowserExceptions:0};
      const ledger={schema:'geometry-driver-process-ledger/1',root:{pid:60,start:'1000',argv:['node','geometry-web/cdp_test.js']},processes:[
        {pid:70,ppid:60,start:'1001',argv:['/opt/chrome','--headless=new','--user-data-dir=/tmp/geometry-cdp-x']},
        {pid:42,ppid:60,start:'1002',argv:['python3','-B','/x/geometry-web/serve.py','1']},
        {pid:77,ppid:60,start:'1003',argv:['/opt/chrome','--headless=new','--remote-debugging-port=0','--user-data-dir=/tmp/r06-cold-chrome-x','about:blank']}]};
      const runtime={...source};
      const state={lines,pkg,cold,result,saved,wrong,unknown,ledger,runtime,final:null};mutate(state);
      const members={};
      members[folder+'saved-1.gcanvas']=state.saved;members[folder+'cold-2.json']=Buffer.from(JSON.stringify(state.cold,null,2)+'\n');
      members[folder+'cold-final-2.json']=Buffer.from(JSON.stringify(state.final||{info:state.cold,end:state.cold.service,errors:[]},null,2)+'\n');
      members[folder+'wrong-v2-policy.gcanvas']=state.wrong;members[folder+'unknown-v2-generator.gcanvas']=state.unknown;
      members['stdout.log']=Buffer.from([...state.lines,'R03A_BROWSER_PACKAGE '+JSON.stringify(state.pkg),
        'R03A_BROWSER_SCOPE '+JSON.stringify({schema:'framing-template-jig-browser-scope/1',assertions:28}),'CDP_RESULT '+JSON.stringify(state.result),''].join('\n'));
      members['stderr.log']=Buffer.from('');members['runtime.stdout']=Buffer.from(JSON.stringify(state.runtime)+'\n');
      members['runtime.stderr']=Buffer.from('');
      const recorded=R.DRIVER_RECEIPT_FILES||['stdout.log','stderr.log','runtime.stdout','runtime.stderr'];
      if(recorded.includes('process-ledger.json'))members['process-ledger.json']=Buffer.from(JSON.stringify(state.ledger,null,2)+'\n');
      const manifest={schema:R.DRIVER_MEASUREMENT_SCHEMA,execution_sha:'a'.repeat(40),head_sha:'a'.repeat(40),tree:'b'.repeat(40),run_id:'7',run_attempt:'1',
        id:'P2052',driver:entry.driver,driver_sha256:identity.sha256,dispatch_sha256:identity.dispatchSha256,flag:entry.flag,
        command:['node','geometry-web/cdp_test.js'],process_exit:0,runtime_fresh:true,runtime_version:RUNTIME_VERSION,capture_verified:true,acceptance:false,
        files:Object.fromEntries(recorded.map(name=>[name,sha(members[name])])),
        outputs:Object.fromEntries(Object.keys(members).filter(name=>name.startsWith(folder)).sort().map(name=>[name,sha(members[name])]))};
      members['manifest.json']=Buffer.from(JSON.stringify(manifest,null,2)+'\n');
      const directory='geometry-web/canvas-registry/costs/P2052/1',zip=path.join(root,directory,'artifact.zip');
      fs.mkdirSync(path.dirname(zip),{recursive:true});zipWrite(zip,members);
      const raw=fs.readFileSync(zip),measured={assertions:28,milliseconds:1234.5,runId:'7',attempt:'1',executionSha:'a'.repeat(40),headSha:'a'.repeat(40)};
      const receipt={schema:'geometry-canvas-section-cost/1',artifact:{id:1,url:'https://api.github.com/repos/ZhiQiYang/geometry-axiom/actions/artifacts/1',
        path:directory+'/artifact.zip',sha256:sha(raw),runId:'7'},measured};
      const receiptRaw=JSON.stringify(receipt,null,2)+'\n';write(root,directory+'/receipt.json',receiptRaw);
      const row=JSON.parse(fs.readFileSync(path.join(root,fragment),'utf8'));
      write(root,fragment,{...row,assertions:28,provenance:{kind:'ci-capture',executionSha:'a'.repeat(40),headSha:'a'.repeat(40),runId:'7',attempt:'1'},
        cost:{receipt:directory+'/receipt.json',sha256:sha(Buffer.from(receiptRaw))}});
    };
    build();
    const registry=R.load(root);
    assert.deepEqual(registry.plan.shards[1].sections,['P72','P205','P2052','P353','P359'],'R386_CANVAS_DRIVER_FIXED_ANCHOR');
    assert.deepEqual(registry.plan.shards[0].sections,['Setup','P88'],'R386_CANVAS_DRIVER_NOT_UNIT_ONE');
    assert.equal(registry.golden.sections.P2052,28);assert.equal(registry.golden.total,legacy.golden.total+28,'R386_CANVAS_DRIVER_EXACT_TOTAL');
    assert.deepEqual(R.legacyView(root),{plan:legacy.plan,golden:legacy.golden},'R386_CANVAS_DRIVER_LEGACY_VIEW_UNCHANGED');
    assert.deepEqual(registry.extensions,[],'R386_CANVAS_DRIVER_IS_NOT_A_MODULE');
    assert.equal(registry.drivers.length,1);
    for(const relative of entry.closure)assert.ok(registry.sourceFiles.includes(relative),'R386_CANVAS_DRIVER_SOURCE_BOUND '+relative);
    await assert.rejects(R.dispatch(root,{mode:'partial',module:'P2052'},{eval_:async()=>({local:{},session:{}})}),/R386_CANVAS_MODULE_UNKNOWN/,'R386_CANVAS_DRIVER_NOT_MODULE_DISPATCH');
    // The same driver is not a strict module (renamed from the former
    // R386_CANVAS_STRICT_MODULE_UNCHANGED, 7072484935 §2: that name overstated it).
    assert.throws(()=>R.moduleSourceHash(root,entry.driver),/R386_CANVAS_/,'R386_CANVAS_DRIVER_REJECTED_BY_STRICT_MODULE');
    // The strict module program itself is pinned: the exact source of each
    // module-path function equals main 883e68688f6480a5f1de6e86e6a056cc20339cb9
    // (where #434 introduced it). Changing one is a reviewed contract change.
    {
      const native=process.binding('natives')['internal/deps/acorn/acorn/dist/acorn'],parser={};
      require('node:vm').runInNewContext(native,{exports:parser,module:{exports:parser}});
      const text=fs.readFileSync(API_FILE,'utf8').replace(/\r\n/g,'\n'),tree=parser.parse(text,{ecmaVersion:'latest',sourceType:'script'});
      const STRICT_MODULE_PIN={"dispatch":"cd74c3ef04b4f158e5b02f63b4ef9d15cec891d8c12d433ba112fb88873e53dc","moduleSourceHash":"de39a3592b9d883d57c690a542b5dcf887e37867c1ee25b7a7ad8dc847bc4633","solvePlacement":"8affd02fb0e65b58828a0c5d80d08841b0ec71e3da7e4cfe4052315e254fdfd4","sourceClosure":"4dcaeec5c908d259a48fed45dd9959bdd3e50e9771f645491a40bf401738e70b","stageModule":"dd7d64fb5f3a7906395219d0e85533d11956d3716c0eae789068d7606c3197ee","verifyMeasurement":"db056ffbce3ffcaa77e4077c74aff977d1ff28d6a703f54e330f2e37c81cc577","verifySlotProof":"8ceff9866fec9dcd6b41e96b38ee2657ca043e4c99736c092557432c17d88209","zipMembers":"0ff41ea5d97211665aab0861359c739036c541f2e448680179098e42c28418e0"};
      const actual=Object.fromEntries(tree.body.filter(node=>node.type==='FunctionDeclaration'&&Object.hasOwn(STRICT_MODULE_PIN,node.id.name))
        .map(node=>[node.id.name,sha(Buffer.from(text.slice(node.start,node.end)))]).sort(([a],[b])=>a<b?-1:1));
      assert.deepEqual(actual,STRICT_MODULE_PIN,'R386_CANVAS_STRICT_MODULE_SOURCE_PINNED');
    }
    const cli=()=>spawnSync(process.execPath,[API_FILE,'check','--root',root],{encoding:'utf8'});
    const snapshot=()=>Object.fromEntries([fragment,'geometry-web/cdp_test.js',...entry.closure,...SUBPROCESS_SCRIPTS,'geometry-web/canvas-registry/costs/P2052/1/artifact.zip',
      'geometry-web/canvas-registry/costs/P2052/1/receipt.json'].map(relative=>[relative,fs.readFileSync(path.join(root,relative))]));
    const pristine=snapshot(),restore=()=>{for(const [relative,raw] of Object.entries(pristine))fs.writeFileSync(path.join(root,relative),raw);
      fs.rmSync(path.join(root,'geometry-web/cdp_sections.d/P2053.json'),{force:true});};
    const withdraw=(id,mutate,code)=>{
      const before=cli();assert.equal(before.status,0,id+' baseline '+before.stderr);
      mutate();const bad=cli();assert.equal(bad.status,1,id+' withdrawn '+bad.stderr);
      assert.ok(bad.stderr.startsWith(code),id+' named failure only: '+bad.stderr);
      restore();const after=cli();assert.equal(after.status,0,id+' restored '+after.stderr);
      console.log(id+' 0/1/0 '+code);
    };
    const edit=(relative,change)=>{const file=path.join(root,relative);fs.writeFileSync(file,change(fs.readFileSync(file,'utf8')));};
    const editRow=change=>edit(fragment,text=>JSON.stringify(change(JSON.parse(text)),null,2)+'\n');
    withdraw('R445_OWNERSHIP_UNIT_ONE',()=>editRow(row=>({...row,unit:1})),'R386_CANVAS_DRIVER_UNREVIEWED');
    withdraw('R445_ORDER_DISPATCH_MOVED',()=>edit('geometry-web/cdp_test.js',text=>{
      const statement=entry.dispatch.split('\n').slice(3).join('\n');
      return text.replace(statement,'').replace('  if(inSequence(2))await p1284();\n','  if(inSequence(2))await p1284();\n'+statement);}),'R386_CANVAS_DRIVER_DISPATCH');
    withdraw('R445_ORDER_FRAGMENT_ANCHOR',()=>editRow(row=>({...row,order:{anchor:{after:'P72',before:'P205'}}})),'R386_CANVAS_DRIVER_UNREVIEWED');
    withdraw('R445_SOURCE_CLOSURE_DYNAMIC',()=>edit('geometry-web/cdp_bay_repeat_io.js',text=>text+"\nconst hidden=require('./'+'cdp_helpers.js');\n"),'R386_CANVAS_DRIVER_CLOSURE_DYNAMIC');
    withdraw('R445_SOURCE_CLOSURE_HASH',()=>edit('geometry-web/cdp_helpers.js',text=>text+'\n// one changed byte\n'),'R386_CANVAS_COST_SOURCE');
    withdraw('R445_RECEIPT_NAMED_CHECK_MISSING',()=>build(state=>{state.lines=state.lines.filter(line=>line!=='P2052 MARKS ✓ ');}),'R386_CANVAS_DRIVER_NAMED_CHECKS');
    withdraw('R445_COLD_OPEN_FORGED',()=>build(state=>{state.pkg.nativeService={...state.pkg.sourceService};state.cold.service={...state.pkg.sourceService};}),'R386_CANVAS_DRIVER_COLD_OPEN');
    withdraw('R445_ESCAPE_UNREVIEWED_DRIVER',()=>editRow(row=>({...row,execution:{...row.execution,driver:'geometry-web/other_driver.js'}})),'R386_CANVAS_DRIVER_UNREVIEWED');
    withdraw('R445_ESCAPE_UNREVIEWED_ID',()=>write(root,'geometry-web/cdp_sections.d/P2053.json',{...JSON.parse(pristine[fragment]),id:'P2053'}),'R386_CANVAS_DRIVER_UNREVIEWED');
    withdraw('R445_ASSERTION_NAMES',()=>edit(entry.driver,text=>text.replace("'MARKS',","'MARKS_RENAMED',")),'R386_CANVAS_DRIVER_ASSERTIONS');
    /* R445 先紅負控制（ChatGPT 7072803590 阻擋 1、2 與收據強度；對抗審查 7072484935
     * N2／N3／F1～F4）。每例仍是 0／1／0 且只認指定代碼；全部跑完才一次報告，
     * 讓每一例各自紅在自己的名字上。 */
    const missed=[];
    const negative=(id,mutate,code)=>{try{withdraw(id,mutate,code);}catch(error){missed.push(id+' → '+String(error.message).split('\n')[0]);restore();}};
    const append=(relative,text)=>()=>edit(relative,source=>source+'\n'+text+'\n');
    // 硬條件 2：反射／計算屬性／解構取 constructor，一律拒收。
    negative('R445_N2_SPELLED_CONSTRUCTOR',append('geometry-web/cdp_helpers.js',"const __k='constr'+'uctor';(function(){})[__k]('return 1')();"),'R386_CANVAS_DRIVER_CLOSURE_DYNAMIC_PROPERTY');
    negative('R445_N2_DESTRUCTURED_CONSTRUCTOR',append('geometry-web/cdp_helpers.js',"const {constructor:F}=function(){};F('return 1')();"),'R386_CANVAS_DRIVER_CLOSURE_REFLECTIVE');
    negative('R445_N2_ASSIGNED_PATTERN_CONSTRUCTOR',append('geometry-web/cdp_helpers.js',"let G;({constructor:G}=async()=>{});G('return 1');"),'R386_CANVAS_DRIVER_CLOSURE_REFLECTIVE');
    negative('R445_N2_CONSTRUCTOR_STRING',append('geometry-web/cdp_helpers.js',"const D=Object.getOwnPropertyDescriptor(Object.prototype,'constructor');"),'R386_CANVAS_DRIVER_CLOSURE_REFLECTIVE');
    negative('R445_N2_ENV_WRITE',append('geometry-web/cdp_helpers.js',"process.env.PYTHONPATH='/tmp/unhashed';"),'R386_CANVAS_DRIVER_PROCESS_CAPABILITY');
    // 子程序：只准封閉清單上的呼叫點；被執行的腳本進來源 hash。
    negative('R445_N2_UNPINNED_CHILD_PROCESS',append('geometry-web/cdp_helpers.js',"require('child_process').execFileSync('node',['geometry-web/unhashed_payload.js']);"),'R386_CANVAS_DRIVER_SUBPROCESS');
    negative('R445_N2_UNPINNED_SPAWN_SITE',append('geometry-web/cdp_bay_repeat_io.js',"function extra(){return spawnSync('node',['geometry-web/unhashed_payload.js']);}"),'R386_CANVAS_DRIVER_SUBPROCESS');
    negative('R445_N2_EXECUTED_SCRIPT_HASH',append('geometry-web/serve.py','# one changed byte'),'R386_CANVAS_COST_SOURCE');
    // 硬條件 1：派發恰好一次（AST、模組路徑正規化、派發區塊結構）。
    const second=quote=>"  if(inSequence(1))await require("+quote+")({send,eval_,sleep,click,dblclick,waitForUI,exceptionCount:()=>excN});\n";
    const beforeP1284=insert=>()=>edit('geometry-web/cdp_test.js',text=>text.replace('  if(inSequence(2))await p1284();\n',insert+'  if(inSequence(2))await p1284();\n'));
    negative('R445_N3_DOUBLE_QUOTED_SECOND_DISPATCH',beforeP1284(second('"./framing_template_jig_workflow_test.js"')),'R386_CANVAS_DRIVER_DISPATCH');
    negative('R445_N3_EXTENSIONLESS_SECOND_DISPATCH',beforeP1284(second("'./framing_template_jig_workflow_test'")),'R386_CANVAS_DRIVER_DISPATCH');
    negative('R445_N3_EXTRA_NODE_CALL',()=>edit('geometry-web/cdp_test.js',text=>text.replace(entry.dispatch,entry.dispatch+"  require('child_process').execSync('true');\n")),'R386_CANVAS_DRIVER_DISPATCH');
    // 收據強度 F1：冷開身分要對上量測腳本自己的 runtime 探測與進程帳。
    const forgedSource={schema:'geometry-runtime/1',version:'0'.repeat(64),fresh:true,root:'/nowhere',pid:1,session:'forged'};
    negative('R445_F1_FORGED_SOURCE_SERVICE',()=>build(state=>{state.pkg.sourceService=forgedSource;state.cold.sourceRuntime=forgedSource;
      state.pkg.nativeService={...state.pkg.nativeService,version:forgedSource.version};state.cold.service=state.pkg.nativeService;}),'R386_CANVAS_DRIVER_COLD_OPEN');
    negative('R445_F1_UNOBSERVED_COLD_SERVICE',()=>build(state=>{state.pkg.nativeService={...state.pkg.nativeService,pid:9999};state.cold.service=state.pkg.nativeService;}),'R386_CANVAS_DRIVER_COLD_OPEN');
    negative('R445_F1_UNOBSERVED_COLD_CHROME',()=>build(state=>{state.pkg.browserPid=9998;state.cold.browserPid=9998;}),'R386_CANVAS_DRIVER_COLD_OPEN');
    // F2：同一次執行的 log 結構（CDP_SCOPE、段標題、順序）。
    negative('R445_F2_TRIMMED_STDOUT',()=>build(state=>{state.lines=state.lines.filter(line=>line.startsWith('P2052 '));}),'R386_CANVAS_DRIVER_LOG_STRUCTURE');
    // F3：兩份竄改檔要是合法 ZIP，且相對存檔只差預期的欄位。
    negative('R445_F3_EMPTY_TAMPERED',()=>build(state=>{state.wrong=Buffer.alloc(0);state.unknown=Buffer.alloc(0);}),'R386_CANVAS_DRIVER_TAMPERED');
    negative('R445_F3_TAMPERED_IS_UNCHANGED_COPY',()=>build(state=>{state.wrong=state.saved;}),'R386_CANVAS_DRIVER_TAMPERED');
    // F4：存檔要是合法 .gcanvas（ZIP、manifest、sceneHash、v1＋v2 配方）。
    negative('R445_F4_SAVED_NOT_GCANVAS',()=>build(state=>{state.saved=Buffer.from('not a zip');state.pkg.bytes=state.saved.length;state.pkg.sha256=sha(state.saved);}),'R386_CANVAS_DRIVER_ARCHIVE');
    assert.deepEqual(missed,[],'R445_NEGATIVE_CONTROLS_REJECTED');
  }finally{fs.rmSync(root,{recursive:true,force:true});}
}

