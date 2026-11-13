'use strict';
/* C0 read compatibility: execute the shipped face-editor helpers and closures.
 * Fixture JSON follows reference_bridge's source-only definitions plus evaluated
 * board-back lattice metadata. Native geometry/oracle witnesses live separately
 * in test_panel_fill_grid_source.py; these controls do not claim browser QA. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = fs.readFileSync(process.env.GEOMETRY_TEST_APP_FILE || path.join(__dirname, '../geometry-web/app.js'), 'utf8');

function between(start, end) {
  const first = app.indexOf(start), last = app.indexOf(end, first);
  assert.ok(first >= 0 && last > first, 'shipped path: ' + start);
  return app.slice(first, last);
}
function declaration(name) {
  const first = app.indexOf('function ' + name + '('), last = app.indexOf('\n}', first);
  assert.ok(first >= 0 && last > first, 'shipped function: ' + name);
  return app.slice(first, last + 2);
}
const helpers = between('function gridLineEntries(', 'function feChooseTimberAnchor(');
const functions = ['referenceAnchorEntries', 'guidePositionLabel', 'gridLineLabel', 'referenceGuideSources', 'feGridSegments', 'feAnchorLineInfo', 'feAnchorCrossRange'].map(declaration).join('\n');
const anchorRenderer = between('  if ((fe.tool === "timber" || fe.anchorPreview)', '  /* RC 障礙物鬼影');
let editors = between('const SubgridEditor = (() => {', '/* D29/I37: a reusable definition');
// Expose state/cell enumeration only; all admission and renderer logic remains
// the exact shipped closure, as in the other inspector ownership controls.
const gridExport = 'return {html,bind,open,focusSection,draw,sync,highlight,fit,clear,sourceOnly,engineeringContext,';
const subgridExport = 'return {html,bind,begin,draw,clear,isActive:';
assert.equal(editors.split(gridExport).length, 2);
assert.equal(editors.split(subgridExport).length, 2);
editors = editors.replace(gridExport, 'return {__test:{get:()=>active,set:s=>{active=s;},drag:f=>{dragCancel=f;}},html,bind,open,focusSection,draw,sync,highlight,fit,clear,sourceOnly,engineeringContext,')
  .replace(subgridExport, 'return {__cells:cells,html,bind,begin,draw,clear,isActive:');

function fromFill(axis = 'u', side = 1, stagger = true) {
  const sign = axis === 'v' ? side : 1, index = '-2', base = sign * -105;
  const grid = {
    id: 11, surface: 10, kind: 'main', bindingId: null, sourceSystem: null,
    fillId: 1, indexSpace: 'lattice', mainAlong: axis === 'u' ? 'v' : 'u',
    uDefinition: {mode: 'from-fill', fillId: 1, axis: 'u'},
    vDefinition: {mode: 'from-fill', fillId: 1, axis: 'v'},
    evaluatedFill: {side, staggerAxis: stagger ? axis : null, staggerDelta: stagger ? sign * 20 : 0, bandIndexSpace: 'panel-row'},
    u: [], v: [], indices: {u: [], v: []}, lines: [],
    lattice: {u: {defined: true, baseCoordinate: 101, baseIndex: '0', pitch: 103},
      v: {defined: true, baseCoordinate: side * 101, baseIndex: '0', pitch: side * 103}}
  };
  grid[axis] = [base]; grid.indices[axis] = [index];
  const segment = (coordinate, lo, hi, band) => [axis === 'u' ? [coordinate,lo] : [lo,coordinate],
    axis === 'u' ? [coordinate,hi] : [hi,coordinate], band];
  grid.lines = [{axis, index, coordinate: base, role: 'primary', priority: 2,
    segments: stagger ? [segment(base + sign * 20, -100, -60, '-1'), segment(base + sign * 20, -40, 0, '-1'), segment(base, -200, -100, '-2')]
      : [segment(base, -200, 0, null)]}];
  return grid;
}
function environment(grids = []) {
  const calls = [], nodes = new Map();
  const empty = () => ({dataset: {}, classList: {add(){},remove(){},toggle(){}}, querySelector(){return null;}, querySelectorAll(){return [];}, addEventListener(){}, setAttribute(){}, remove(){}});
  const sandbox = {console, Set, Map, Number, BigInt, String, JSON, clearTimeout:id=>calls.push(['clear-timeout',id]),
    window: {}, document: {body: empty(), createElement: empty}, innerWidth: 1200,
    oc: {edit: {bid: 8}, bmap: {8: []}},
    fe: {grids, guides: [], specs: [], timbers: [], subgridDraftParent: null, gridEditingId: grids[0]?.id, gridPreview: null, gridPreviewSeq: 1, tool: 'select'},
    GridRuleLines: {entries:()=>[], bind:()=>calls.push(['rules-bind']), html:()=>'', parseAnchor:()=>null},
    feAnchorOccupied:()=>null, feSid:()=>10, loopsBBox:()=>[-400,-400,400,400],
    renderFaceInspector:()=>calls.push(['render']), feSetTool:tool=>calls.push(['tool',tool]), fiShowTab:tab=>calls.push(['tab',tab]), drawFaceEditor:()=>calls.push(['draw']),
    $:id=>nodes.get(id) || null
  };
  vm.createContext(sandbox);
  vm.runInContext(helpers + '\n' + functions + '\n' + editors + '\nthis.GridEditor=GridEditor;this.SubgridEditor=SubgridEditor;', sandbox, {filename: 'app.production.read-compat.js'});
  return {c: sandbox, calls, nodes, empty};
}
function renderAnchor(env, anchor) {
  const {c,nodes}=env,drawn=[];
  nodes.set('tbAnchor',{value:anchor});nodes.set('tbA',{value:'20'});
  c.fe.anchorPreview=true;c.e={bid:8};c.gb=[-400,-400,400,400];c.z=1;c.root={};c.refRoot={};c.annotations={};
  c.ReferenceVisibility={anchorVisible:()=>true};
  c.el=(tag,attrs,parent)=>{const node={tag,attrs,parent};drawn.push(node);return node;};
  vm.runInContext(anchorRenderer,c,{filename:'app.production.anchor-preview.js'});
  return {highlights:drawn.filter(n=>n.attrs.class==='fe-anchor-hi'),bands:drawn.filter(n=>n.attrs.class==='fe-anchor-band')};
}

test('C0UI_SIGNED sampled ordinals never replace signed lattice identity or clipped band segments', () => {
  for (const axis of ['u','v']) for (const side of [1,-1]) {
    const g = fromFill(axis,side), before = JSON.stringify(g), {c} = environment([g]);
    const entries = c.gridLineEntries(g,axis);
    assert.equal(entries[0].index,'-2'); assert.equal(entries[0].ordinal,0);
    const segments = c.feGridSegments(g,axis,'-2',[-400,-400,400,400]);
    assert.equal(segments.length,3); assert.deepEqual(Array.from(segments,s=>s.band),['-1','-1','-2']);
    assert.equal(segments[0][axis==='u'?0:1],(axis==='v'?side:1)*-85);
    assert.equal(c.feGridSegments(g,axis,'0',[-400,-400,400,400]).length,0);
    assert.equal(JSON.stringify(g),before,'presentation must not write evaluated data into source definitions');
  }
});

test('C0UI_BAND evaluated stagger requires its signed board row for both axes and both sides', () => {
  for (const axis of ['u','v']) for (const side of [1,-1]) {
    const g = fromFill(axis,side), env=environment([g]), {c}=env, sign = axis==='v'?side:1;
    assert.equal(c.gridHasStagger(g,axis),true);
    assert.equal(c.gridHasStagger(g,axis==='u'?'v':'u'),false);
    assert.equal(c.gridAnchorCoordinate(g,axis,'-2','-1'),sign*-85);
    assert.equal(c.gridAnchorCoordinate(g,axis,'-2','-2'),sign*-105);
    assert.equal(c.gridAnchorCoordinate(g,axis,'-2',null),null,'unbanded stagger must not masquerade as a whole line');
    const anchor='at-line grid 11 '+axis+' -2 band -1',coordinate=sign*-85;
    const info=c.feAnchorLineInfo(8,anchor),segments=g.lines[0].segments.slice(0,2).map(s=>[...s[0],...s[1]]);
    assert.deepEqual(info.segments && JSON.parse(JSON.stringify(info.segments)),segments,'the highlight retains only native pieces of this board row');
    const before=JSON.stringify(g),rendered=renderAnchor(env,anchor);
    assert.deepEqual(rendered.highlights.map(n=>[n.attrs.x1,n.attrs.y1,n.attrs.x2,n.attrs.y2]),segments);
    const expected=axis==='u' ? [[coordinate-10,-100,20,40],[coordinate-10,-40,20,40]] : [[-100,coordinate-10,40,20],[-40,coordinate-10,40,20]];
    assert.deepEqual(rendered.bands.map(n=>[n.attrs.x,n.attrs.y,n.attrs.width,n.attrs.height]),expected,
      'material indication neither crosses another board row nor fills a native clipping gap');
    for(const segment of g.lines[0].segments)[segment[0],segment[1]]=[segment[1],segment[0]];
    const reversed=renderAnchor(env,anchor);
    assert.deepEqual(reversed.bands.map(n=>[n.attrs.x,n.attrs.y,n.attrs.width,n.attrs.height]),expected,'reflected endpoint order cannot make a negative preview extent');
    for(const segment of g.lines[0].segments)[segment[0],segment[1]]=[segment[1],segment[0]];
    const offscreen=renderAnchor(env,'at-line grid 11 '+axis+' 10 band -3');
    assert.equal(offscreen.highlights.length,0);assert.equal(offscreen.bands.length,0,'missing sampled pieces do not authorize an invented full-face preview');
    assert.equal(JSON.stringify(g),before);
  }
});

test('C0UI_OFFSCREEN signed offscreen anchors use the mapped lattice and shift exactly once', () => {
  for (const axis of ['u','v']) for (const side of [1,-1]) {
    const g = fromFill(axis,side), {c} = environment([g]), sign = axis==='v'?side:1;
    assert.equal(c.gridAnchorCoordinate(g,axis,'10','-3'),sign*1151);
    assert.equal(c.gridAnchorCoordinate(g,axis,'-4','-2'),sign*-311);
    assert.equal(c.gridAnchorCoordinate(g,axis,'10','0'),sign*1131);
    for (const bad of ['1.5','9007199254740993.5','9223372036854775808','-9223372036854775809'])
      assert.equal(c.gridAnchorCoordinate(g,axis,'10',bad),null,'invalid signed band: '+bad);
    assert.equal(c.gridAnchorCoordinate(g,axis,'9223372036854775808','1'),null);
    assert.equal(c.gridAnchorCoordinate(g,axis,'9223372036854775807','1'),null,'unsafe coordinate cannot be rounded');
  }
});

test('C0UI_CHOICES timber and guide choices retain k plus board row and deduplicate only fragments', () => {
  for (const axis of ['u','v']) for (const side of [1,-1]) {
    const g = fromFill(axis,side), {c} = environment([g]);
    const anchors = c.referenceAnchorEntries(8,{id:10});
    assert.deepEqual(Array.from(anchors,e=>e.value),['at-line grid 11 '+axis+' -2 band -1','at-line grid 11 '+axis+' -2 band -2']);
    assert.match(anchors[0].label,/板列 -1/); assert.match(anchors[0].label,/索引 -2/);
    const guides = c.referenceGuideSources(8,axis==='u'?'v':'u');
    assert.deepEqual(Array.from(guides,e=>e[0]),['grid:11:'+axis+':-2:band:-1','grid:11:'+axis+':-2:band:-2']);
    assert.match(guides[0][1],new RegExp(String((axis==='v'?side:1)*-85)+' mm'));
  }
});

test('C0UI_MISSING evaluated fill metadata is required for anchor interpretation', () => {
  const g = fromFill(), {c} = environment([g]);
  for (const invalid of [undefined,{...g.evaluatedFill,side:0},{...g.evaluatedFill,staggerAxis:'x'},
    {...g.evaluatedFill,staggerDelta:1.5},{...g.evaluatedFill,bandIndexSpace:'lattice-cell'}]) {
    g.evaluatedFill=invalid;
    assert.equal(c.gridAnchorCoordinate(g,'u','-2',null),null);
    assert.equal(c.gridAnchorCoordinate(g,'u','-2','-1'),null);
    assert.equal(c.referenceAnchorEntries(8,{id:10}).length,0);
    assert.equal(c.referenceGuideSources(8,'v').length,0);
  }
});

test('C0UI_LEGACY straight fill and existing finite and source-backed grids keep their contracts', () => {
  const straight = fromFill('v',-1,false), {c} = environment([straight]);
  assert.equal(c.gridHasStagger(straight,'v'),false);
  assert.equal(c.gridAnchorCoordinate(straight,'v','10',null),-1131);
  assert.equal(c.gridAnchorCoordinate(straight,'v','10','1'),null);
  assert.equal(c.referenceGuideSources(8,'u')[0][0],'grid:11:v:-2');
  const finite = {id:1,surface:10,u:[10,20],v:[],uDefinition:{source:'explicit'},lines:[]};
  assert.equal(c.gridLineEntry(finite,'u',1).coordinate,20);
  assert.equal(c.gridAnchorCoordinate(finite,'u',1,null),20);
  const lattice = {id:2,surface:10,bindingId:7,indexSpace:'lattice',u:[],indices:{u:[]},
    uDefinition:{source:'repeat',stagger:-20},lattice:{u:{defined:true,baseCoordinate:10,baseIndex:'0',pitch:100}}};
  assert.equal(c.gridHasStagger(lattice,'u'),true);
  assert.equal(c.gridAnchorCoordinate(lattice,'u','-2','-1'),-210);
  assert.equal(c.gridAnchorCoordinate(lattice,'u','-2',null),null);
  c.fe.grids=[lattice];
  const legacy=c.feAnchorLineInfo(8,'at-line grid 2 u -2 band -1');
  assert.equal(legacy.value,-210);assert.equal(legacy.bounds,null);assert.equal(legacy.segments,undefined,'existing from-binding preview keeps its contract');
});

test('C0UI_READONLY loaded source-only grid gets source inspection without direct editing controls', () => {
  const g = fromFill(), {c} = environment([g]);
  const html = c.GridEditor.html(g,{id:10});
  assert.match(html,/data-from-fill-grid/); assert.match(html,/鋪排 #1/); assert.match(html,/唯讀/);
  assert.doesNotMatch(html,/<(?:input|select|button)\b|class="[^\"]*grid-editor\b|id="(?:gridCreate|subgridNew)"/);
  c.fe.subgridDraftParent=g.id;
  assert.match(c.GridEditor.html(g,{id:10}),/data-from-fill-grid/,'stale draft cannot convert source inspection into a direct editor');
});

test('C0UI_BIND readonly binding retires prior timers and gestures and clears mutable previews', () => {
  const g = fromFill(), {c,calls,empty} = environment([g]);
  c.GridEditor.__test.set({timer:73}); c.GridEditor.__test.drag(()=>calls.push(['cancel-drag']));
  c.fe.gridPreview={u:[999]}; c.fe.subgridDraftParent=g.id;
  c.GridEditor.bind(empty(),8,g,{id:10});
  assert.equal(c.GridEditor.__test.get(),null); assert.equal(c.fe.gridPreview,null); assert.equal(c.fe.subgridDraftParent,null);
  assert.deepEqual(calls,[['cancel-drag'],['clear-timeout',73]],'readonly binding must not bind rule or direct editing controls');
  assert.equal(c.GridEditor.addLine('u',123),null); assert.equal(c.GridEditor.engineeringContext(),null);
});

test('C0UI_TOOL source-only guard prevents entering the direct grid tool for loaded fills', () => {
  const g = fromFill(), {c} = environment([g]);
  assert.equal(c.GridEditor.sourceOnly(),true);
  for (const legacy of [{id:2,surface:10,bindingId:8},{id:3,surface:10,sourceSystem:9},{id:4,surface:10,engineeringSources:[{}]}]) {
    c.fe.grids=[legacy]; c.fe.gridEditingId=legacy.id; assert.equal(c.GridEditor.sourceOnly(),true);
  }
  c.fe.grids=[{id:5,surface:10,kind:'main',u:[10]}]; c.fe.gridEditingId=5;
  assert.equal(c.GridEditor.sourceOnly(),false);
});

test('C0UI_PARENT from-fill cannot be offered as a parent cell or start a subgrid draft', () => {
  for (const side of [1,-1]) {
    const g = fromFill('v',side), {c,calls} = environment([g]);
    c.oc.bmap[8]=[{verts:[[-400,-400],[400,-400],[400,400],[-400,400]]}];
    assert.equal(c.SubgridEditor.__cells(g,8,null).length,0);
    assert.equal(c.SubgridEditor.begin(g.id),false);
    assert.equal(c.fe.subgridDraftParent,null); assert.equal(c.fe.gridEditingId,g.id);
    assert.equal(c.SubgridEditor.isActive(),false); assert.equal(calls.length,0);
  }
});

test('C0UI_HOVER timber card shows the chosen board row coordinate, never its unshifted base', () => {
  const g = fromFill('v',-1), {c,nodes,empty} = environment([g]);
  c.fe.tool='timber'; c.fe.timberHoverAnchor='at-line grid 11 v -2 band -1';
  for (const [id,value] of [['tbA','20'],['tbB','30'],['tbSide','+n'],['tbRole','primary']]) nodes.set(id,{value,selectedOptions:[{textContent:'正面'}]});
  nodes.set('faceInspectorContent',{dataset:{tbRoleManual:'false'}});
  let shown;
  nodes.set('faceEditorViewport',{append:n=>{shown=n;}});
  c.ReferenceVisibility={anchorVisible:()=>true}; c.feTimberSuggestion=()=>({dir:'+u',role:'primary',subgrid:false}); c.feTimberRoleOptionsHTML=()=>'<option>主支</option>';
  c.document.createElement=()=>{const box=empty(),controls=new Map([['select',empty()],['[data-grid-place-timber]',empty()],['[data-grid-timber-close]',empty()]]);box.querySelector=s=>controls.get(s)||null;return box;};
  c.GridEditor.draw({}, {}, [-400,-400,400,400],1);
  assert.ok(shown); assert.match(shown.innerHTML,/板列 -1/); assert.match(shown.innerHTML,/v=85 mm/); assert.doesNotMatch(shown.innerHTML,/v=105 mm/);
  assert.equal(shown.dataset.anchor,'at-line grid 11 v -2 band -1');
});
