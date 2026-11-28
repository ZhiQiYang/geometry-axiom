'use strict';
/* Execute the shipping result renderer; only export its private pure function
 * in this harness. These tests establish markup and probe behavior, not a
 * browser layout receipt. P2054 owns the real Range/viewport assertions. */
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {sourcePolicy,probeSelftest}=require('./diagnostics/r03_preview_length_contract.cjs');
const {previewLengthProbe,lengthValuesReady,lengthSingleLine,lengthUnclipped}=require('./diagnostics/r03_preview_length_probe.cjs');
const root=path.resolve(__dirname,'..');
function renderCandidate(members){
  const source=fs.readFileSync(path.join(root,'geometry-web/framing-template-workspace.js'),'utf8');
  const anchor='  return {open,close,render,';
  assert.equal(source.split(anchor).length,2,'R2054_RENDERER_EXPORT_SITE');
  const sandbox={window:{GeometryFramingRecipes:{},GeometryFramingSession:{Session:class{}},addEventListener(){}},
    ReferenceWorkspace:{escape:value=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;')}};
  vm.runInNewContext(source.replace(anchor,'  window.renderCandidateForTest=results;\n'+anchor),sandbox);
  return sandbox.window.renderCandidateForTest({session:{candidate:{members},readResult:{source:{outer:[[0,0],[3740,0],[3740,3301],[0,3301]]}}}});
}
function cells(fragment){return [...fragment.matchAll(/<(td|th)\b([^>]*)>([^<]*)<\/\1>/g)].map(m=>({tag:m[1],attrs:m[2],text:m[3],marked:/\bdata-ft-length(?:\s|=|$)/.test(m[2])}));}
const members=[{kind:'main',rect:[0,0,27,3247],length:3247,A:27,B:33},{kind:'boundary',rect:[0,0,3740,27],length:3740,A:27,B:33}];
test('R2054_LENGTH_SEMANTIC_CELL follows the actual numeric value in every rendered row',()=>{
  const html=renderCandidate(members),heading=cells(html.match(/<thead>([\s\S]*?)<\/thead>/)[1]);
  assert.deepEqual(heading.filter(c=>c.marked).map(c=>c.text),['長度'],'R2054_LENGTH_HEADING');
  const rows=[...html.matchAll(/<tr data-ft-member-row="(\d+)">([\s\S]*?)<\/tr>/g)];
  assert.equal(rows.length,members.length);
  for(const row of rows){const actual=cells(row[2]);assert.equal(actual.length,4);
    assert.deepEqual(actual.filter(c=>c.marked).map(c=>c.text),[String(members[Number(row[1])].length)],'R2054_LENGTH_SEMANTIC_CELL');}
});
test('R2054_LENGTH_SEMANTIC_CELL survives column reordering without relabeling another value',()=>{
  const html=renderCandidate(members),row=html.match(/<tr data-ft-member-row="0">([\s\S]*?)<\/tr>/)[1];
  const actual=cells(row);
  for(const permutation of [[2,0,3,1],[1,3,0,2],[3,2,1,0]]){
    const reordered=permutation.map(i=>actual[i]);
    assert.deepEqual(reordered.filter(c=>c.marked).map(c=>c.text),['3247'],'R2054_LENGTH_REORDERED_SEMANTICS');
  }
});
test('R2054_LENGTH_POLICY overrides shared anywhere only in the semantic R03 length cells',()=>{
  const css=fs.readFileSync(path.join(root,'geometry-web/framing-template-workspace.css'),'utf8');
  sourcePolicy(css);
  assert.doesNotMatch(css,/\.ft-results[^{}]*:nth-child\(/,'R2054_NO_POSITIONAL_LENGTH_SELECTOR');
  const shared=fs.readFileSync(path.join(root,'geometry-web/panel-fill-workspace.css'),'utf8');
  assert.match(shared,/\.pf-workspace td,\.pf-workspace th\{[^}]*overflow-wrap:anywhere/,'R2054_SHARED_WRAP_REMAINS');
});
test('R2054_PROBE retains the original five negatives for wrap, clip, overflow, absence and value',()=>{probeSelftest();});
function probeAtColumn(lengthColumn,marked){
  const box={left:10,right:80,top:10,bottom:35,width:70,height:25};
  const makeCell=text=>({textContent:text,getBoundingClientRect:()=>box});
  const texts=['主支','0, 0, 27, 3247','27 × 33'];texts.splice(lengthColumn,0,'3247');
  const rowCells=texts.map(makeCell);rowCells.item=i=>rowCells[i]||null;
  const headings=['角色','位置矩形','寬×厚'];headings.splice(lengthColumn,0,'長度');
  const row={dataset:{ftMemberRow:'0'},cells:rowCells,querySelector:()=>marked?rowCells[lengthColumn]:null};
  const table={closest:()=>({clientWidth:200,scrollWidth:200}),getBoundingClientRect:()=>box,
    querySelectorAll:selector=>selector==='thead th'?headings.map(makeCell):[row]};
  const member={getAttribute:name=>name==='width'?'27':'3247'};
  const region={querySelector:selector=>selector==='table'?table:member};
  let selected;
  const sandbox={document:{querySelector:()=>region,createRange:()=>({selectNodeContents:cell=>{selected=cell;},getClientRects:()=>[{left:12,right:45,top:12,bottom:30,width:33,height:18}]})},
    getComputedStyle:()=>({whiteSpace:'nowrap'}),innerWidth:1400,innerHeight:900};
  const observed=vm.runInNewContext('('+previewLengthProbe.toString()+')()',sandbox);
  assert.equal(selected,rowCells[lengthColumn],'R2054_PROBE_SELECTS_LENGTH_BY_MEANING');
  return observed;
}
test('R2054_PROBE reads semantic cells after reordering',()=>{
  for(const at of [0,1,2,3]){const observed=probeAtColumn(at,true);assert.equal(lengthValuesReady(observed,1,'3247'),true);assert.equal(lengthSingleLine(observed),true);assert.equal(lengthUnclipped(observed),true);}
});
test('R2054_T_ONLY_PROBE reads the original unmarked heading instead of aborting before a behavioral assertion',()=>{
  for(const at of [0,1,2,3])assert.equal(lengthValuesReady(probeAtColumn(at,false),1,'3247'),true);
});

const lengthExtension=require('./diagnostics/r03_preview_length_canvas_extension.cjs');
function canvasUnion(){
  // These are explicit structural-test counts, not CI measurements. The real
  // full registry/receipt loader independently owns the formal golden.
  const sections={P88:143,P1161:1,P1162:504,P1231:1,P2054:15,P359:24};
  return {golden:{schema:'geometry-cdp-sections/1',mode:'full',total:Object.values(sections).reduce((a,b)=>a+b,0),sections},
    plan:{schema:'geometry-cdp-shards/1',shards:[{index:1,sections:['P88']},{index:2,sections:['P1161','P1162','P1231','P2054','P359']}],boundaries:[{after:'P88',before:'P1161',localStorage:{retained:{kind:'exact',value:'unchanged'}}}]}};
}
test('R2054_CANVAS_PROJECTION retains every old count, handoff and input byte before the original R16 judge',()=>{
  const authored=require('../geometry-web/canvas_sections/P2054.js').ASSERTIONS;
  assert.equal(authored.length,15);assert.equal(new Set(authored).size,15);assert.equal(lengthExtension.COUNT,15);
  const input=canvasUnion(),before=JSON.stringify(input),r16=require('./diagnostics/r16_canvas_extension.cjs');
  assert.throws(()=>r16.beforeTouch(input.golden,input.plan),/R16_R433_EXACT_TAIL/);
  const actual=lengthExtension.project(input.golden,input.plan),expected=structuredClone(input);
  delete expected.golden.sections.P2054;expected.golden.total-=15;expected.plan.shards[1].sections.splice(3,1);
  assert.deepEqual(actual,expected,'R2054_CANVAS_ONLY_OWN_SECTION_REMOVED');
  assert.equal(JSON.stringify(input),before,'R2054_CANVAS_INPUT_UNCHANGED');
  assert.doesNotThrow(()=>r16.beforeTouch(actual.golden,actual.plan));
});
test('R2054_CANVAS_PROJECTION rejects a consistent-sum count drift',()=>{
  const input=canvasUnion();input.golden.sections.P2054=14;input.golden.total--;
  assert.throws(()=>lengthExtension.project(input.golden,input.plan),/R2054_CANVAS_EXACT_COUNT/,'R2054_CANVAS_COUNT_GUARD_REQUIRED');
});
test('R2054_CANVAS_PROJECTION rejects duplicate ownership even when shard 2 neighbors remain exact',()=>{
  const input=canvasUnion();input.plan.shards[0].sections.push('P2054');
  assert.throws(()=>lengthExtension.project(input.golden,input.plan),/R2054_CANVAS_EXACT_OWNER:P2054/,'R2054_CANVAS_OWNER_GUARD_REQUIRED');
});
test('R2054_CANVAS_PROJECTION rejects changed neighbors while preserving the unique owner',()=>{
  const input=canvasUnion(),sections=input.plan.shards[1].sections;sections.splice(3,1);sections.splice(2,0,'P2054');
  assert.throws(()=>lengthExtension.project(input.golden,input.plan),/R2054_CANVAS_EXACT_NEIGHBORS/,'R2054_CANVAS_ORDER_GUARD_REQUIRED');
});
function withdrawalJudge(caseName){
  const python=process.env.GEOMETRY_PYTHON||(process.platform==='win32'?'python':'python3');
  const run=require('node:child_process').spawnSync(python,['-B','tests/diagnostics/r03_preview_length_judge_contract.py',caseName],{cwd:root,encoding:'utf8',timeout:60000});
  assert.equal(run.status,0,'R2054_WITHDRAWAL_JUDGE_'+caseName+'\n'+run.stdout+run.stderr);
}
test('R2054_WITHDRAWAL_JUDGE rejects a passed marker plus an unrelated AssertionError',()=>withdrawalJudge('wrong-failure'));
test('R2054_WITHDRAWAL_JUDGE rejects a skipped test',()=>withdrawalJudge('skip'));
test('R2054_WITHDRAWAL_JUDGE rejects cancellation',()=>withdrawalJudge('cancel'));
test('R2054_WITHDRAWAL_JUDGE accepts only the exact failing test and assertion',()=>withdrawalJudge('valid'));
function touchInputFromCurrentCaller(file,current){
  const text=fs.readFileSync(path.join(root,file),'utf8');
  const lines=text.split('\n').filter(line=>/^\s*const (lengthInput|touchInput)\s*=/.test(line));
  assert.ok(lines.length===1||lines.length===2,'R2054_HISTORY_CALL_SITE');
  const sandbox={registered:current,golden:current.golden,plan:current.plan,lengthExtension,r16Extension:require('./diagnostics/r16_canvas_extension.cjs'),
    shards:{loadGolden:()=>current.golden,loadPlan:()=>current.plan},
    require:name=>{assert.equal(name,'../geometry-web/canvas_registry.js');return {load:()=>current};}};
  vm.runInNewContext(lines.join('\n')+'\nresult=touchInput;',sandbox);
  return sandbox.result;
}
test('R2054_HISTORICAL_CANVAS_VIEW validates the complete registry then keeps the unchanged historical scope',()=>{
  // Synthetic accepted-registry records exercise only the view. Actual cost
  // admission stays in the original loader and is tested separately below.
  const current=require('../geometry-web/canvas_registry.js').load(root,{allowCandidates:true});
  const own=current.extensions.find(row=>row.id==='P2054');current.golden.total+=15-own.assertions;own.assertions=15;current.golden.sections.P2054=15;
  const independent=structuredClone(own);independent.id='P9998';independent.assertions=2;
  current.extensions.push(independent);current.golden.sections.P9998=2;current.golden.total+=2;
  const tail=current.plan.shards[1].sections;tail.splice(tail.length-1,0,'P9998');
  const driver=structuredClone(independent);driver.id='P9997';current.drivers.push(driver);
  current.golden.sections.P9997=2;current.golden.total+=2;tail.splice(tail.length-1,0,'P9997');
  const before=JSON.stringify(current);
  for(const file of ['tests/test_canvas_shards.js','tests/test_boundary_pair_browser_scope.js']){
    let view;
    assert.doesNotThrow(()=>{view=touchInputFromCurrentCaller(file,current);},'R2054_HISTORY_NO_PER_PR_EXCEPTION');
    const expected=structuredClone(current.golden);
    for(const id of ['P2054','P9998','P9997','P1231']){expected.total-=expected.sections[id];delete expected.sections[id];}
    assert.deepEqual(view.golden,expected,'R2054_HISTORY_EXACT_COUNTS');
    assert.deepEqual(view.plan.shards,current.plan.shards.map(row=>({...row,sections:row.sections.filter(id=>!['P2054','P9998','P9997','P1231'].includes(id))})),'R2054_HISTORY_EXACT_ORDER');
    assert.deepEqual(view.plan.boundaries,current.plan.boundaries,'R2054_HISTORY_HANDOFF');
    assert.equal(JSON.stringify(current),before,'R2054_HISTORY_INPUT_UNCHANGED');
    for(const corrupt of [r=>{r.golden.sections.P9998=1;r.golden.total--;},r=>r.plan.shards[0].sections.push('P9998'),r=>{r.golden.sections.P8888=1;r.golden.total++;}]){
      const bad=structuredClone(current);corrupt(bad);
      assert.throws(()=>touchInputFromCurrentCaller(file,bad),/R16_REGISTRY_|R16_REGISTERED_COUNT/,'R2054_HISTORY_COMPLETE_UNION_GUARD');
    }
  }
});
test('R2054_NATIVE_HISTORY rejects a fabricated new row with matching cost but no original receipt',()=>{
  const python=process.env.GEOMETRY_PYTHON||(process.platform==='win32'?'python':'python3');
  const run=require('node:child_process').spawnSync(python,['-B','tests/diagnostics/r03_preview_length_registry_probe.py','baseline'],{cwd:root,encoding:'utf8',timeout:60000});
  assert.equal(run.status,1,'R2054_FAKE_COST_MUST_NOT_EXEMPT\n'+run.stdout+run.stderr);
  assert.match(run.stderr,/ValueError: R386_NATIVE_(?:EXACT_COST_COVERAGE|STALE_SUITE_SOURCE_OR_EXECUTION)|R396_CURRENT_COSTS_MATCH_VERIFIED_REGISTRY/,'R2054_FAKE_COST_REJECTED_BY_ORIGINAL_LOADER\n'+run.stderr);
});
test('R2054_CANDIDATE_GATE still rejects pending count and missing canvas receipt',()=>{
  const declaration=JSON.parse(fs.readFileSync(path.join(root,'geometry-web/cdp_sections.d/P2054.json'),'utf8'));
  const registry=require('../geometry-web/canvas_registry.js');
  if(declaration.provenance.kind==='candidate')
    assert.throws(()=>registry.load(root),/R386_CANVAS_COST_RECEIPT_REQUIRED: P2054/);
  else assert.equal(registry.load(root).acceptance,true,'R2054_ADOPTED_RECEIPT_STILL_VALIDATED');
});
test('R2054_BROWSER_OWNERSHIP uses a new checked service per phase and never the caller URL',()=>{
  const python=process.env.GEOMETRY_PYTHON||(process.platform==='win32'?'python':'python3');
  const run=require('node:child_process').spawnSync(python,['-B','tests/diagnostics/r03_preview_length_service_contract.py'],{cwd:root,encoding:'utf8',timeout:60000});
  assert.equal(run.status,0,'R2054_BROWSER_OWNERSHIP\n'+run.stdout+run.stderr);
});
