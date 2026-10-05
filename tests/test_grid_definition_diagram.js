/* Independent pixel expectations for the production schematic, without a bridge. */
const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const file = process.env.GEOMETRY_GRID_DEFINITION_SOURCE || path.join(__dirname, '../geometry-web/grid-system-workspace.js');
const source = fs.readFileSync(file, 'utf8');
const start = source.indexOf('  function drawDefinition(s, data) {');
const end = source.indexOf('  // Presentation only:', start);
assert.ok(start >= 0 && end > start, 'production renderer must be present');
const node = (tag, cls, attrs = {}, text) => ({tag, cls, attrs, text, children: [],
  append(...children) { this.children.push(...children); },
  replaceChildren() { this.children = []; }});
function render(u, v, refs = {}) {
  const stage = node('div', '');
  const focused = [];
  const context = vm.createContext({mk:node, $:id => id === 'igDefStage' ? stage : {value:refs[id] || ''},
    focusField:(_s, a, key) => focused.push([a,key])});
  vm.runInContext(source.slice(start, end), context);
  context.drawDefinition({defFocus:{a:'u',key:''}}, [u,v]);
  const flatten = n => [n, ...n.children.flatMap(flatten)];
  return {nodes:flatten(stage), focused};
}
function repeat(a, pitch, stagger = 0) {
  const p = 'ig'+a.toUpperCase();
  const fields = [{key:'step', id:p+'Step', raw:String(pitch)}, {key:'phase', id:p+'Phase', raw:'0'}];
  return {a, mode:'repeat', shape:{phase:0, pitch, stagger}, fields, all:fields, errors:[]};
}
function segments(result, vertical) {
  return result.nodes.filter(n => n.cls.split(' ').includes('ig-def-line')).map(n => {
    const style = Object.fromEntries(n.attrs.style.split(';').map(s => s.split(':')).filter(s=>s.length===2).map(([k,v])=>[k,parseFloat(v)]));
    const thickness = n.cls.includes('is-zero') ? 2 : 1;
    const isVertical = style.width === thickness;
    if (isVertical !== vertical) return null;
    return isVertical ? [style.left+thickness/2,style.top,style.top+style.height] : [style.top+thickness/2,style.left,style.left+style.width];
  }).filter(Boolean).sort((a,b)=>a[1]-b[1] || a[0]-b[0]);
}
function close(actual, expected) {
  assert.equal(actual.length, expected.length, 'all visible segments must be present');
  actual.forEach((row,i) => row.forEach((value,j) => assert.ok(Math.abs(value-expected[i][j])<1e-7,
    `segment ${i}, component ${j}: ${value} != ${expected[i][j]}`)));
}
test('panel zero label uses effective phase while clicking still edits the raw anchor', () => {
  const u = repeat('u',405); u.mode='repeat-panel'; u.shape.phase=302;
  u.fields = [{key:'panel',id:'igUPanel',raw:'400'},{key:'gap',id:'igUGap',raw:'5'},{key:'anchor',id:'igUAnchor',raw:'-100'}]; u.all=u.fields;
  const result=render(u,repeat('v',1830),{igUAnchorSource:'1:2'});
  const chip=result.nodes.find(n=>n.attrs['data-ig-chip']==='u:anchor');
  assert.equal(chip.text,'u 302');
  assert.ok(chip.cls.includes('is-bound'), 'the original anchor source remains visible');
  chip.onclick(); assert.deepEqual(result.focused,[['u','anchor']]);
});
test('unshifted lines remain continuous with unchanged schematic geometry', () => {
  close(segments(render(repeat('u',600),repeat('v',400)),true),[[100,52,210],[228,52,210]]);
});
for (const [delta,odd] of [[-60001,[99.78666666666686,227.78666666666686]],[60001,[100.21333333333314,228.21333333333314]]]) {
  test(`u signed stagger ${delta} retains even and negative/positive odd bands`, () => {
    const result=render(repeat('u',600,delta),repeat('v',400));
    close(segments(result,true),[[odd[0],52,72],[odd[1],52,72],[100,72,157.33333333333331],
      [228,72,157.33333333333331],[odd[0],157.33333333333331,210],[odd[1],157.33333333333331,210]]);
    assert.ok(result.nodes.length<100, 'work stays bounded by the visible schematic');
  });
}
for (const [delta,odd] of [[-60001,[71.83333333333212,171.83333333333212]],[60001,[72.16666666666788,172.16666666666788]]]) {
  test(`v signed stagger ${delta} retains both band parities`, () => {
    close(segments(render(repeat('u',400),repeat('v',600,delta)),false),[
      [odd[0],76,100],[odd[1],76,100],[72,100,166.66666666666666],[172,100,166.66666666666666],
      [odd[0],166.66666666666666,233.33333333333331],[odd[1],166.66666666666666,233.33333333333331],
      [72,233.33333333333331,300],[172,233.33333333333331,300],[odd[0],300,320],[odd[1],300,320]]);
  });
}
test('legal near-limit signed stagger keeps visible lines and bounded work', () => {
  for (const delta of [-99999999,99999999]) {
    const result=render(repeat('u',600,delta),repeat('v',400));
    assert.equal(segments(result,true).length,6);
    assert.ok(result.nodes.length<100);
  }
});
test('both shifted axes still cut segments at the other axis unshifted band boundaries', () => {
  const result=render(repeat('u',600,-60001),repeat('v',400,40001));
  close(segments(result,true),[[99.78666666666686,52,72],[227.78666666666686,52,72],
    [100,72,157.33333333333331],[228,72,157.33333333333331],
    [99.78666666666686,157.33333333333331,210],[227.78666666666686,157.33333333333331,210]]);
  close(segments(result,false),[[72.21333333333314,76,100],[157.546666666668,76,100],
    [72,100,228],[157.33333333333331,100,228],[72.21333333333314,228,320],[157.546666666668,228,320]]);
});
