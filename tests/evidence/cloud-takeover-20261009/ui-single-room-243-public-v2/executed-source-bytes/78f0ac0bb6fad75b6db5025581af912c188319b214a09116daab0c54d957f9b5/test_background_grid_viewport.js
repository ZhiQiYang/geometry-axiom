/* Exercise the production face-grid planner and refresh without a bridge. */
const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = fs.readFileSync(path.join(__dirname, '../geometry-web/app.js'), 'utf8');
const source = app.slice(app.indexOf('function feGridStep()'), app.indexOf('function feApplyZoom('));
const context = vm.createContext({});
vm.runInContext(source, context);
const plan = context.feBackgroundGridPlan;
const bigFace = [-100000000, -100000000, 100000000, 100000000];
const count = p => p ? Math.max(0, p.xLast - p.xFirst + 1) + Math.max(0, p.yLast - p.yFirst + 1) : 0;

test('100 km boundaries at 100% only draw screen-sized work', () => {
  const p = plan([0, 0, 100000000, 100000000], 1200, 800, 1, 0, 0, 25);
  assert.ok(count(p) < 90);
  assert.equal(p.step, 25);
  assert.equal(p.stride, 1);
  assert.ok(p.x1 <= 1224 && p.y1 <= 824);
});
test('negative coordinates retain world-zero alignment', () => {
  const p = plan(bigFace, 800, 600, 1, 400, 300, 25);
  assert.ok(p.xFirst < 0 && p.xLast > 0 && p.yFirst < 0 && p.yLast > 0);
  assert.ok(p.xFirst * p.step % 25 === 0);
  assert.ok(p.yFirst * p.step % 25 === 0);
});
test('pan covers newly exposed local coordinates at unchanged spacing', () => {
  const p = plan(bigFace, 800, 600, 1, -4000, 2000, 25);
  assert.equal(p.x0, 3976);
  assert.equal(p.x1, 4824);
  assert.equal(p.y0, -2024);
  assert.equal(p.y1, -1376);
  assert.equal(p.step, 25);
  assert.ok(count(p) < 70);
});
test('zoom converts the actual SVG viewport to local bounds', () => {
  const p = plan(bigFace, 1000, 600, 4, 200, -400, 10);
  assert.deepEqual([p.x0, p.y0, p.x1, p.y1], [-56, 94, 206, 256]);
  assert.equal(p.step, 10);
  assert.ok(count(p) < 50);
});
test('extreme fit zoom samples decoration only on global major lines', () => {
  const p = plan(bigFace, 1200, 800, .001, 600, 400, 1000);
  assert.ok(count(p) < 90);
  assert.equal(p.stride % 4, 0);
  assert.equal(p.step, p.stride * 1000);
  assert.ok(p.xFirst * p.stride % 4 === 0);
});
test('tiny faces and off-face pans respect the original face padding', () => {
  const p = plan([0, 0, 1, 1], 800, 600, 1, 0, 0, 25);
  assert.equal(p.x1, 81);
  assert.equal(p.y1, 81);
  assert.equal(plan([0, 0, 1, 1], 800, 600, 1, -10000, 0, 25), null);
});
test('invalid or unrepresentable camera inputs cannot create runaway loops', () => {
  for (const zoom of [0, -1, NaN, Infinity, Number.MIN_VALUE])
    assert.equal(plan(bigFace, 800, 600, zoom, 0, 0, 25), null);
  assert.equal(plan(bigFace, 0, 600, 1, 0, 0, 25), null);
  assert.equal(plan(bigFace, 800, 600, 1, Infinity, 0, 25), null);
  assert.equal(plan([10, 0, 0, 10], 800, 600, 1, 0, 0, 25), null);
});
test('even a huge synthetic viewport keeps a finite line budget', () => {
  const p = plan(bigFace, 10000000, 10000000, 1, 0, 0, 25);
  assert.ok(count(p) <= 4100);
});
test('pan updates only the noninteractive grid and preserves captured scene nodes', () => {
  const group = {children: [], set textContent(v) { this.children = []; }};
  const capturedShape = {};
  const root = {children:[group, capturedShape], setAttribute(name, value) { this[name] = value; }};
  const nodes = {feBackgroundGrid:group, faceEditorRoot:root,
    faceEditorSvg:{getBoundingClientRect:() => ({left:150, top:70, width:800, height:600})},
    faceGridToggle:{checked:true}, feZoomLevel:{}};
  context.$ = id => nodes[id];
  context.fe = {zoom:1, panX:400, panY:300, fittedBounds:bigFace};
  context.oc = {edit:{bid:1}, focus:{t:'face'}, bmap:{1:[{verts:bigFace}]}};
  context.loopsBBox = () => bigFace;
  context.el = (tag, attrs, parent) => { const node = {tag, attrs}; parent.children.push(node); return node; };
  context.cancelCanvasMarquee = () => {};
  context.fePlaceOverlays = () => {};
  context.drawFaceEditor = () => { throw Error('Pan must not rebuild the scene'); };
  context.feUpdateBackgroundGrid();
  const firstLines = group.children;
  const major = firstLines.find(n => n.attrs.x1 === -400 && n.attrs.x2 === -400);
  const minor = firstLines.find(n => n.attrs.x1 === -375 && n.attrs.x2 === -375);
  assert.equal(major.attrs.stroke, '#d3dae4');
  assert.equal(minor.attrs.stroke, '#e6eaf0');
  context.feUpdateBackgroundGrid();
  assert.equal(group.children, firstLines, 'An unchanged viewport reuses grid nodes');
  context.fe.panX = -4000;
  context.feApply(true);
  assert.equal(context.fe.fittedBounds, bigFace);
  assert.equal(root.children[1], capturedShape);
  assert.equal(root.transform, 'translate(-4000,300) scale(1)');
  assert.ok(group.children.some(n => n.attrs.x1 === 4000 && n.attrs.x2 === 4000));
  assert.ok(!group.children.some(n => n.attrs.x1 === -400 && n.attrs.x2 === -400));
  context.feApply();
  assert.equal(context.fe.fittedBounds, null);
  nodes.faceGridToggle.checked = false;
  context.feUpdateBackgroundGrid();
  assert.equal(group.children.length, 0);
});
