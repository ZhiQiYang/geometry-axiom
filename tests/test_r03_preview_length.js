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
