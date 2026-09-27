'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
// Canvas contract test with recorded draw calls, not browser/GPU end-to-end coverage.
// The override runs identical assertions against temporary sensitivity variants.
const viewer = require(process.env.GEOMETRY_TEST_VIEWER || '../geometry-web/model-viewer.js');
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);

// A plan must retain XY handedness and a front elevation must keep +Z upward.
const top = viewer.views.top, front = viewer.views.front, iso = viewer.views.iso;
const topX = viewer.project([1, 0, 0], top.yaw, top.pitch);
const topY = viewer.project([0, 1, 0], top.yaw, top.pitch);
near(topX[0], 1); near(topX[1], 0); near(topY[0], 0); near(topY[1], -1);
const bottom = viewer.views.bottom;
near(viewer.project([0, 1, 0], bottom.yaw, bottom.pitch)[1], 1);
// Depth is nearer the observer: top sees high Z first, bottom sees low Z first.
near(viewer.project([0, 0, 1], top.yaw, top.pitch)[2], 1);
near(viewer.project([0, 0, 1], bottom.yaw, bottom.pitch)[2], -1);
// Asymmetric local contours must follow the placement frame, not a blanket V flip.
const frame = {origin:[500,700,2500],u:[0,1,0],v:[-1,0,0]};
const local = [1200,400], localBefore = local.slice(), frameBefore = JSON.stringify(frame);
const planTop = viewer.projectPlanPoint(local,frame,'top');
const planBottom = viewer.projectPlanPoint(local,frame,'bottom');
near(planTop[0],100); near(planTop[1],-1900); near(planTop[2],2500);
near(planBottom[0],100); near(planBottom[1],1900); near(planBottom[2],-2500);
const reverseV = {origin:[0,0,2500],u:[1,0,0],v:[0,-1,0]};
near(viewer.projectPlanPoint([1200,400],reverseV,'top')[1],400);
assert.deepEqual(local,localBefore); assert.equal(JSON.stringify(frame),frameBefore);
assert.throws(()=>viewer.projectPlanPoint(local,frame,'front'),/方向/);
assert.throws(()=>viewer.projectPlanPoint(local,{},'top'),/框架/);
near(viewer.project([0, 0, 1], front.yaw, front.pitch)[1], -1);
assert.ok(viewer.project([0, 0, 1], iso.yaw, iso.pitch)[1] < 0);
// The orthographic change of basis must preserve 3D distances at every angle.
for (const [yaw, pitch] of [[0, 0], [0, Math.PI / 2], [-0.8, 0.6], [2.4, -0.7]]) {
  const projected = viewer.project([3, 4, 12], yaw, pitch);
  near(Math.hypot(...projected), 13);
}

// Verify against a real engine-exported concave room, not a replacement box.
const room = JSON.parse(fs.readFileSync(path.join(__dirname, '../geometry-core/examples/l-room.model.json'), 'utf8'));
const prepared = viewer.prepareObjects(room.derived.objects);
assert.equal(prepared.triangleCount, room.derived.objects.reduce((sum, object) => sum + object.triangles.length, 0));
assert.deepEqual(prepared.bounds, { min: [0, 0, 0], max: [6000, 4500, 2800] });
assert.deepEqual(prepared.objects[0].triangles.map(triangle => triangle.indices), room.derived.objects[0].triangles);
assert.deepEqual(prepared.objects[0].vertices, room.derived.objects[0].vertices_mm);
assert.throws(() => viewer.prepareObjects([{ vertices_mm: [[0, 0, 0]], triangles: [[0, 1, 2]] }]), /頂點/);
assert.throws(() => viewer.prepareObjects([{ vertices_mm: [[0.5, 0, 0]], triangles: [] }]), /整數/);

// Display-layer selection preserves each real material solid and its identity.
// A timber top exactly at the space roof must not be removed by the roof switch.
function boxMesh(root, min, max) {
  return {root,vertices_mm:[[min[0],min[1],min[2]],[max[0],min[1],min[2]],[max[0],max[1],min[2]],[min[0],max[1],min[2]],
    [min[0],min[1],max[2]],[max[0],min[1],max[2]],[max[0],max[1],max[2]],[min[0],max[1],max[2]]],
    triangles:[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]};
}
const timber=boxMesh({kind:'timber',id:0},[0,0,2500],[27,2960,2533]);
const shell=boxMesh({kind:'composite_space',id:1},[0,0,0],[4000,3000,2533]);
const materials={summary:{top:2533},space:{derived:{objects:[shell]}},timbers:{derived:{objects:[timber]}}};
const immutableMaterials=JSON.stringify(materials);
const roofHidden=viewer.spacePreviewObjects(materials,{roof:false,walls:false});
assert.equal(roofHidden[0].triangles.length,10);
assert.equal(roofHidden[1].root.id,0);
assert.equal(roofHidden[1].label,'角材結構');
assert.deepEqual(roofHidden[1].triangles,timber.triangles);
assert.deepEqual(roofHidden[1].vertices_mm,timber.vertices_mm);
assert.equal(viewer.spacePreviewObjects(materials,{roof:true})[0].triangles.length,12);
assert.deepEqual(viewer.prepareObjects(viewer.spacePreviewObjects(materials,{space:false,walls:false})).bounds,{min:[0,0,2500],max:[27,2960,2533]});
assert.equal(viewer.spacePreviewObjects(materials,{space:false,walls:false,timbers:false}).length,0);
assert.equal(JSON.stringify(materials),immutableMaterials,'Viewing switches cannot change saved package geometry.');
const beyondRoof=boxMesh({kind:'timber',id:9},[5000,0,5000],[5027,2960,5033]);
const outsideResult={...materials,timbers:{derived:{objects:[timber,beyondRoof]}}};
assert.deepEqual(viewer.prepareObjects(viewer.spacePreviewObjects(outsideResult)).bounds.max,[5027,3000,5033]);
assert.equal(new Set(viewer.spacePreviewObjects(outsideResult).filter(o=>o.root.kind==='timber').map(o=>o.label)).size,1,'Timbers share one legend label while retaining separate IDs.');

// Updating with EMPTY or bad output must clear old geometry, including its bounds.
const attributes = new Map(), listeners = new Map();
const noop = () => {};
const ctx = new Proxy({ measureText: text => ({ width: text.length * 7 }) }, { get: (target, key) => target[key] || noop });
const canvas = {
  style: {}, width: 0, height: 0,
  getContext: () => ctx, getBoundingClientRect: () => ({ width: 600, height: 400 }),
  getAttribute: key => attributes.has(key) ? attributes.get(key) : null,
  setAttribute: (key, value) => attributes.set(key, value), removeAttribute: key => attributes.delete(key),
  addEventListener: (key, fn) => listeners.set(key, fn), removeEventListener: key => listeners.delete(key)
};
const instance = viewer.create(canvas);
instance.setObjects(room.derived.objects);
assert.equal(instance.getState().triangleCount, prepared.triangleCount);
const beforeViews = instance.getState();
instance.setView('bottom');
assert.equal(instance.getState().view,'bottom');
near(instance.getState().pitch,-Math.PI/2);
instance.setView('top');
assert.deepEqual(instance.getState().bounds,beforeViews.bounds);
assert.equal(instance.getState().triangleCount,beforeViews.triangleCount);
instance.setObjects([]);
assert.equal(instance.getState().triangleCount, 0);
assert.equal(instance.getState().bounds, null);
instance.setObjects(room.derived.objects);
assert.throws(() => instance.setObjects([{ vertices_mm: [], triangles: [[0, 1, 2]] }]));
assert.equal(instance.getState().objectCount, 0);
assert.equal(instance.getState().bounds, null);
instance.destroy();
assert.equal(listeners.size, 0);
assert.equal(instance.getState().destroyed, true);

// A model prepared in a hidden tab must fit the real short viewport when it
// becomes visible, even before ResizeObserver delivers its notification.
let rect = { width: 0, height: 0 }, currentPath = [], closedPath = false;
const renderedFaces = [], renderedText = [], frames = [], windowEvents = new Map();
const visibleCtx = new Proxy({
  measureText: text => ({ width: text.length * 7 }),
  clearRect() { renderedFaces.length = 0; renderedText.length = 0; },
  beginPath() { currentPath = []; closedPath = false; },
  moveTo(x, y) { currentPath.push([x, y]); },
  lineTo(x, y) { currentPath.push([x, y]); },
  closePath() { closedPath = true; },
  fill() { if (closedPath && currentPath.length === 3) renderedFaces.push(currentPath.slice()); },
  fillText(text) { renderedText.push({ text, color: this.fillStyle }); }
}, { get: (target, key) => target[key] || noop });
const fakeWindow = {
  devicePixelRatio: 2,
  requestAnimationFrame: callback => { frames.push(callback); return frames.length; },
  cancelAnimationFrame: noop,
  addEventListener: (name, callback) => windowEvents.set(name, callback),
  removeEventListener: name => windowEvents.delete(name)
};
const visibleCanvas = {
  ...canvas, style: {}, ownerDocument: { defaultView: fakeWindow },
  getContext: () => visibleCtx, getBoundingClientRect: () => rect,
  focus: noop, setPointerCapture: noop, hasPointerCapture: () => false
};
const flush = () => { while (frames.length) frames.shift()(); };
const visibleViewer = viewer.create(visibleCanvas, { background: '#edf2f5' });
visibleViewer.setObjects(room.derived.objects);
rect = { width: 860, height: 130 }; flush();
assert.equal(visibleViewer.getState().width, 860);
assert.equal(visibleViewer.getState().height, 130);
assert.equal(visibleCanvas.width, 1720);
const ys = renderedFaces.flat(1).map(point => point[1]);
assert.ok(Math.max(...ys) - Math.min(...ys) >= 100, 'A real room must fill at least 100 px of a 130 px canvas, not a 24 px speck.');
assert.equal(renderedFaces.length, prepared.triangleCount, 'Every exported triangle must reach the canvas.');
for (const [x, y] of renderedFaces.flat(1)) {
  assert.ok(Number.isFinite(x) && Number.isFinite(y), 'Draw coordinates must be finite.');
  assert.ok(x >= 0 && x <= rect.width && y >= 0 && y <= rect.height,
    `Fitted geometry must stay on canvas: ${x},${y} outside ${rect.width}x${rect.height}`);
}

// Actual drawn legend/scale text must stay legible on the light workspace.
function luminance(hex) {
  const values = [1, 3, 5].map(start => parseInt(hex.slice(start, start + 2), 16) / 255)
    .map(value => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
  return values[0] * 0.2126 + values[1] * 0.7152 + values[2] * 0.0722;
}
const lightBackground = luminance('#edf2f5');
const labels = renderedText.filter(item => item.text.includes('composite_space') || item.text.endsWith(' mm'));
assert.equal(labels.length, 2);
for (const label of labels) assert.ok((lightBackground + 0.05) / (luminance(label.color) + 0.05) >= 4.5, label.text + ' lacks contrast');

// Layout changes preserve intentional zoom; a new model resets it to fit.
listeners.get('keydown')({ key: '+', preventDefault: noop }); flush();
const zoomed = visibleViewer.getState().zoom;
rect = { width: 390, height: 230 }; windowEvents.get('resize')(); flush();
assert.equal(visibleViewer.getState().zoom, zoomed);
const beforePan = renderedFaces.map(face => face.map(point => point.slice()));
listeners.get('pointerdown')({ pointerId: 1, pointerType: 'mouse', button: 0, clientX: 20, clientY: 20, preventDefault: noop });
listeners.get('pointermove')({ pointerId: 1, clientX: 55, clientY: 30, shiftKey: true }); flush();
assert.deepEqual(visibleViewer.getState().pan, { x: 35, y: 10 });
assert.equal(renderedFaces.length, beforePan.length);
renderedFaces.forEach((face, i) => face.forEach(([x, y], j) => {
  near(x - beforePan[i][j][0], 35); near(y - beforePan[i][j][1], 10);
}));
visibleViewer.setObjects(room.derived.objects); flush();
assert.equal(visibleViewer.getState().zoom, 1);
assert.deepEqual(visibleViewer.getState().pan, { x: 0, y: 0 });
// Independent asymmetric front-view witness: its visible outline is a 2:1
// right triangle. A renderer substituting a box or merely counting faces fails.
visibleViewer.setObjects([{root:{kind:'timber',id:0},vertices_mm:[[0,0,0],[400,0,0],[0,0,200]],triangles:[[0,1,2]]}]);
visibleViewer.setView('front'); flush();
assert.equal(renderedFaces.length, 1);
const [origin, right, up] = renderedFaces[0];
near(origin[1], right[1]); near(origin[0], up[0]);
assert.ok(right[0] > origin[0] && up[1] < origin[1]);
near((right[0] - origin[0]) / (origin[1] - up[1]), 2);
visibleViewer.destroy();
console.log('model-viewer canvas unit contract: orientation, mesh identity and drawn shape, clearing, visible fit, actual pan displacement, and contrast passed');
