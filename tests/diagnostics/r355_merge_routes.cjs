'use strict';
// External merge regression. Real driver conditions and call sites execute;
// suite callbacks are inert. These results are not browser acceptance.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm');
const {createRequire}=require('node:module');
const root=path.resolve(process.env.R355_SOURCE_ROOT||path.join(__dirname,'../..'));
const driverPath=path.join(root,'geometry-web/cdp_test.js');
const source=fs.readFileSync(process.env.R355_CDP_SOURCE||driverPath,'utf8');
function loadSource(file,override){
  if(!override)return require(file);
  const m={exports:{}};
  vm.runInNewContext(fs.readFileSync(override,'utf8'),{module:m,exports:m.exports,require:createRequire(file),
    __dirname:path.dirname(file),__filename:file,process,console,URL,Blob,TextEncoder,TextDecoder,Uint8Array,
    Buffer,setTimeout,clearTimeout,structuredClone,crypto}, {filename:file});
  return m.exports;
}
const native=process.binding('natives')['internal/deps/acorn/acorn/dist/acorn'];
assert.equal(typeof native,'string','Node must expose its bundled Acorn; unavailable is an error, never skip');
const acorn={};vm.runInNewContext(native,{exports:acorn,module:{exports:acorn}});
const tree=acorn.parse(source,{ecmaVersion:'latest',sourceType:'script'});
const main=tree.body.find(n=>n.type==='FunctionDeclaration'&&n.id.name==='main');
assert.ok(main,'real main must exist');
const slice=n=>source.slice(n.start,n.end);
const helperNames=new Set(['inSequence','notOtherShard','runCanvasContextMenu']);
const directNames=new Set(['runCanvasContextMenu','applyShardHandoff','verifyShardHandoff']);
function routeStatement(node){
  if(node.type==='VariableDeclaration'&&node.declarations.some(d=>helperNames.has(d.id.name)))return slice(node);
  if(node.type==='BlockStatement'){
    const children=node.body.map(routeStatement).filter(Boolean);
    return children.length?'{\n'+children.join('\n')+'\n}':'';
  }
  if(node.type==='IfStatement'){
    const yes=routeStatement(node.consequent),no=node.alternate?routeStatement(node.alternate):'';
    if(!yes&&!no||yes==='{\n\n}'&&!no)return '';
    return 'if('+slice(node.test)+')'+(yes||'{}')+(no?'else '+no:'');
  }
  if(node.type!=='ExpressionStatement'||node.expression.type!=='AwaitExpression')return '';
  const call=node.expression.argument;
  if(call.type!=='CallExpression')return '';
  if(call.callee.type==='Identifier'&&directNames.has(call.callee.name))return slice(node);
  const inner=call.callee;
  if(inner.type==='CallExpression'&&inner.callee.type==='Identifier'&&inner.callee.name==='require'&&
     inner.arguments[0]?.type==='Literal'&&/^\.\/.*_test\.js$/.test(inner.arguments[0].value))return slice(node);
  return '';
}
const routing=main.body.body.map(routeStatement).filter(Boolean).join('\n');
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
const run=new AsyncFunction('scope','process','require','applyShardHandoff','verifyShardHandoff',
  'send','eval_','sleep','click','dblclick','drag','dragMod','pressDownMod','moveMod','waitForUI','captureNewToasts','expectNativeDialog','excN','until','check',routing);
async function trace(scope,env={},argumentsBySuite=new Map()){
  const calls=[],noop=async()=>{};
  await run(scope,{env},name=>async helpers=>{calls.push(name);argumentsBySuite.set(name,helpers);},async n=>calls.push('incoming:'+n),async n=>calls.push('outgoing:'+n),
    noop,noop,noop,noop,noop,noop,noop,noop,noop,noop,noop,noop,0,noop,noop);
  return calls;
}
const shard1=['project_import_final_objects_test','project_audit_test','engineering_workflow_test','marquee_test','grid_system_test','grid_rule_editor_test','grid_rule_lines_test'].map(n=>'./'+n+'.js');
const shard2=['composition_canvas_test','grid_inspector_rename_test','uiux_review_test','ux_refinement_test','selection_cursor_test',
  'parameter_workflow_test','assembly_workflow_test','assembly_context_entry_test','assembly_bay_repeat_test','timber_schedule_test',
  'cutting_plan_test','timber_supports_browser_test','source_navigation_test','room_outline_test','identity_ledger_browser_test',
  'room_candidate_browser_test','room_candidate_cold_test','model_snapshot_schedule_test','model_snapshot_navigation_test',
  'canvas_context_menu_test','panel_fill_workflow_test','grid_card_entry_test','definition_import_browser_test'].map(n=>'./'+n+'.js');
const mod={exports:{}};
vm.runInNewContext(source,{module:mod,exports:mod.exports,require:createRequire(driverPath),__dirname:path.dirname(driverPath),__filename:driverPath,process,console,URL,Buffer,setTimeout,clearTimeout}, {filename:driverPath});
const config=mod.exports.runConfiguration;
const env={GEOMETRY_TEST_URL:'http://127.0.0.1:1/',GEOMETRY_FEEDBACK_DIR:path.join(os.tmpdir(),'r355-merge-preflight')};

test('R355-MERGE-FULL: every inherited suite and the R02 suite run once in order',async()=>{
  assert.deepEqual(await trace({mode:'full'}),[...shard1,'outgoing:1',...shard2],'R355_FULL_SEQUENCE');
});
test('R355-MERGE-SHARDS: ownership, the P88 handoff and the R02 tail stay disjoint',async()=>{
  const first=await trace({mode:'shard',shard:{index:1}}),second=await trace({mode:'shard',shard:{index:2}});
  assert.deepEqual(first,[...shard1,'outgoing:1'],'R355_SHARD1_SEQUENCE');
  assert.deepEqual(second,['incoming:1',...shard2],'R355_SHARD2_SEQUENCE');
  assert.equal(first.filter(n=>n==='./panel_fill_workflow_test.js').length,0,'R355_R02_NOT_SHARD1');
  assert.equal(second.filter(n=>n==='./panel_fill_workflow_test.js').length,1,'R355_R02_ONCE_SHARD2');
});
test('R355-MERGE-PARTIAL: R02 stays isolated and all inherited partial routes are preserved',async()=>{
  for(const [flag,names] of [
    ['GEOMETRY_PANEL_FILL_ONLY',['panel_fill_workflow_test']],
    ['GEOMETRY_CANVAS_CONTEXT_MENU_ONLY',['canvas_context_menu_test']],
    ['GEOMETRY_GRID_CARD_ENTRY_ONLY',['grid_card_entry_test']],
    // Fixed main also runs these three inherited preliminary modules for this
    // flag. A merge must not silently remove its existing coverage.
    ['GEOMETRY_DEFINITION_IMPORT_ONLY',['project_audit_test','engineering_workflow_test','marquee_test','definition_import_browser_test']],
    ['GEOMETRY_IDENTITY_LEDGER_ONLY',['identity_ledger_browser_test']],
    ['GEOMETRY_ASSEMBLY_ONLY',['assembly_workflow_test','assembly_context_entry_test','assembly_bay_repeat_test']],
    ['GEOMETRY_ROOM_CANDIDATE_ONLY',['room_candidate_browser_test','room_candidate_cold_test']]]){
    assert.deepEqual(await trace({mode:'partial'},{[flag]:'1'}),names.map(n=>'./'+n+'.js'),'R355_ONLY_ROUTING '+flag);
  }
});
test('R355-MERGE-GATES: scope/card selectors cannot narrow complete or shard coverage',()=>{
  assert.equal(config({...env,GEOMETRY_PANEL_FILL_ONLY:'1'}).mode,'partial','R355_ONLY_REGISTERED');
  for(const filter of ['GEOMETRY_PANEL_FILL_ONLY','GEOMETRY_GRID_CARD_ENTRY_ONLY','GEOMETRY_DEFINITION_IMPORT_ONLY']){
    assert.throws(()=>config({...env,[filter]:'1',GEOMETRY_CDP_SHARD:'2/2'}),/one contiguous block/,'R355_FILTERED_SHARD_REJECT');
  }
  assert.throws(()=>config({...env,GEOMETRY_GRID_CARD_ENTRY_CASE:'C01'}),/requires GEOMETRY_GRID_CARD_ENTRY_ONLY/,'R355_CARD_CASE_REQUIRES_ONLY');
  assert.throws(()=>config({...env,GEOMETRY_CDP_SHARD:'2/2',GEOMETRY_CDP_UPDATE_GOLDEN:'1'}),/never updates golden/,'R355_SHARD_CANNOT_UPDATE_GOLDEN');
});
test('R355-MERGE-PLAN: only P128 is added, after P352 and before P353/P359',()=>{
  const plan=JSON.parse(fs.readFileSync(process.env.R355_PLAN_SOURCE||path.join(root,'geometry-web/canvas_shards.json')));
  assert.equal(plan.shards.length,2);
  const all=plan.shards.flatMap(s=>s.sections);
  assert.equal(all.filter(n=>n==='P128').length,1,'R355_PLAN_P128_ONCE');
  assert.equal(plan.shards[0].sections.includes('P128'),false,'R355_PLAN_P128_SHARD2');
  assert.deepEqual(plan.shards[1].sections.slice(-4),['P352','P128','P353','P359'],'R355_PLAN_TAIL_ORDER');
  assert.deepEqual([plan.boundaries[0].after,plan.boundaries[0].before],['P88','P72'],'R355_EXISTING_CUT_UNCHANGED');
});

test('R355-MERGE-ALL-MAIN-SCOPES: every fixed-main partial route stays identical',async()=>{
  const frozen=JSON.parse(fs.readFileSync(path.join(__dirname,'r355_main_routes.json')));
  assert.equal(frozen.main,'343a8abe83029dd883e5e5b1b8e3112411fefe81');
  for(const [flag,expected] of Object.entries(frozen.partial))
    assert.deepEqual(await trace({mode:'partial'},{[flag]:'1'}),expected,'R355_MAIN_PARTIAL '+flag);
});
test('R355-MERGE-PF-HELPERS: the real dispatch supplies every required workflow helper',async()=>{
  for(const [scope,env] of [[{mode:'full'},{}],[{mode:'shard',shard:{index:2}},{}],[{mode:'partial'},{GEOMETRY_PANEL_FILL_ONLY:'1'}]]){
    const argumentsBySuite=new Map();await trace(scope,env,argumentsBySuite);
    const helpers=argumentsBySuite.get('./panel_fill_workflow_test.js');
    for(const name of ['send','eval_','sleep','click','dblclick','waitForUI','expectNativeDialog','exceptionCount'])
      assert.equal(typeof helpers?.[name],'function','R355_PF_REQUIRED_HELPER '+name+' '+scope.mode);
  }
});
