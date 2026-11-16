/* Prepared real-App R22 diagnostic, independent of cdp_test/golden/shards.
 * Run instructions and the present environment blocker: R22-APP-MANUAL-REVIEW.md.
 * No product mutation through evaluate, browser flags, installation or fallback.
 * Exit 2 = not started/preflight; 3 = execution failure; 1 = assertion failure.
 */
'use strict';
const fs = require('node:fs'), path = require('node:path'), os = require('node:os');
const crypto = require('node:crypto'), zlib = require('node:zlib'), net = require('node:net');
const {spawn, execFileSync} = require('node:child_process');
const ROOT = path.resolve(__dirname, '../..');
const {shapes, pdf} = require('../room_outline_fixture.js');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const git = (...args) => execFileSync('git', args, {cwd: ROOT, encoding: 'utf8'}).trim();
const outArg = process.argv[2];
if (!outArg || process.argv.slice(3).some(x => x !== '--preflight-only'))
  throw Error('usage: node tests/diagnostics/r22_app_manual_review.cjs NEW_TEMP_DIR [--preflight-only]');
const OUT = path.resolve(outArg), relative = path.relative(os.tmpdir(), OUT);
if (!relative || relative.startsWith('..') || path.isAbsolute(relative) || fs.existsSync(OUT))
  throw Error('output must be a new dedicated directory under TEMP; prior evidence is never overwritten');
fs.mkdirSync(OUT, {recursive: true, mode: 0o700});
const checks = [], services = [], browserErrors = [], dialogs = [];
const receipt = {protocol: 'r22-real-app-manual-review/1', startedUtc: new Date().toISOString(),
  command: [process.execPath, ...process.argv.slice(1)], head: git('rev-parse', 'HEAD'),
  worktree: git('status', '--porcelain=v1', '--untracked-files=all'),
  state: 'not_started', appAssertions: 0, browserLaunchAttempts: 0,
  browserPlugin: 'not available in the preparing environment',
  scenarios: shapes.flatMap(s => ['pdf', 'image'].map(kind => `${kind}-${s.name}`)),
  boundaries: {privatePDF: false, physicalPhone: false, physicalIME: false,
    osPicker: false, humanTiming: false, screenshots: 'synthetic inputs only'},
  sourceHashes: Object.fromEntries([
    'tests/diagnostics/r22_app_manual_review.cjs', 'tests/room_outline_fixture.js',
    'geometry-web/app.js', 'geometry-web/room-outline-workspace.js',
    'geometry-web/room-outline.js', 'geometry-web/reference-workspace.js',
    'geometry-web/project-store.js', 'geometry-web/start_local.py',
  ].map(f => [f, hash(fs.readFileSync(path.join(ROOT, f)))])), checks, services, browserErrors, dialogs};
const write = (file, value) => fs.writeFileSync(path.join(OUT, file),
  typeof value === 'string' || Buffer.isBuffer(value) ? value : JSON.stringify(value, null, 2) + '\n');
class AssertionFailure extends Error {}
function check(name, condition, detail) {
  const row = {scenario: current, name, ok: condition === true, ...(detail === undefined ? {} : {detail})};
  checks.push(row); receipt.appAssertions = checks.length;
  console.log(`${row.ok ? 'PASS' : 'FAIL'} ${current}: ${name}`);
  if (!row.ok) throw new AssertionFailure(name);
}
let chromium, browser, page, service, bid, current = 'preflight', acceptNew = false;
function preflight() {
  const blockers = [];
  if (process.env.GEOMETRY_CHROME_FLAGS) blockers.push('GEOMETRY_CHROME_FLAGS is set; extra flags are not permitted');
  try {
    chromium = require('playwright').chromium;
    receipt.playwright = {module: require.resolve('playwright'),
      executable: process.env.GEOMETRY_CHROME || chromium.executablePath(),
      chromiumSandbox: true, extraArgs: []};
    try { fs.accessSync(receipt.playwright.executable, fs.constants.X_OK); }
    catch (e) { blockers.push(`${e.code}: browser executable unavailable: ${receipt.playwright.executable}`); }
    // Preserve the known system-Chromium rejection. Do not retry its launch.
    if (receipt.playwright.executable === '/usr/bin/chromium') {
      const s = fs.statSync('/usr/lib/chromium/chrome-sandbox');
      receipt.systemSandbox = {uid: s.uid, gid: s.gid, mode: (s.mode & 0o7777).toString(8)};
      if (s.uid !== 0 || (s.mode & 0o4777) !== 0o4755)
        blockers.push('known system Chromium sandbox-helper configuration remains invalid; launch not retried');
    }
  } catch (e) { blockers.push(`${e.code || e.name}: ${e.message}`); }
  receipt.preflight = {utc: new Date().toISOString(), blockers};
  return blockers.length === 0;
}
// Public, self-authored raster. No decoding mock: the App imports these PNG bytes.
function png(shape) {
  const w = 280, h = 190, pixels = Buffer.alloc(w * h * 4, 255);
  for (let i = 0; i < shape.points.length; i++) {
    const a = shape.points[i], b = shape.points[(i + 1) % shape.points.length];
    for (let y = Math.min(a[1], b[1]) - 2; y < Math.max(a[1], b[1]) + 2; y++)
      for (let x = Math.min(a[0], b[0]) - 2; x < Math.max(a[0], b[0]) + 2; x++)
        pixels.fill(0, (y * w + x) * 4, (y * w + x) * 4 + 3);
  }
  const crc = bytes => { let c = 0xffffffff; for (const n of bytes) { c ^= n;
    for (let i = 0; i < 8; i++) c = (c >>> 1) ^ (c & 1 ? 0xedb88320 : 0); } return (c ^ 0xffffffff) >>> 0; };
  const chunk = (name, bytes) => { const tag = Buffer.from(name), size = Buffer.alloc(4), tail = Buffer.alloc(4);
    size.writeUInt32BE(bytes.length); tail.writeUInt32BE(crc(Buffer.concat([tag, bytes])));
    return Buffer.concat([size, tag, bytes, tail]); };
  const header = Buffer.alloc(13); header.writeUInt32BE(w); header.writeUInt32BE(h, 4); header[8] = 8; header[9] = 6;
  const rows = Buffer.alloc(h * (w * 4 + 1));
  for (let y = 0; y < h; y++) pixels.copy(rows, y * (w * 4 + 1) + 1, y * w * 4, (y + 1) * w * 4);
  return Buffer.concat([Buffer.from('89504e470d0a1a0a', 'hex'), chunk('IHDR', header),
    chunk('IDAT', zlib.deflateSync(rows)), chunk('IEND', Buffer.alloc(0))]);
}
const corrections = {
  rectangle: [[320,320],[2320,320],[2320,1480],[1720,1480],[1720,1280],[1280,1280],[1280,1480],[320,1480]],
  l: [[320,320],[2320,320],[2320,780],[1280,780],[1280,1520],[320,1520]],
  notch: [[320,320],[2320,320],[2320,1480],[1720,1480],[1720,1000],[1280,1000],[1280,1480],[320,1480]],
};
const length = (a, b) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);
function canonical(points) {
  return [points, points.slice().reverse()].flatMap(p => p.map((_, i) =>
    JSON.stringify(p.slice(i).concat(p.slice(0, i))))).sort()[0];
}
// Independent source-to-face transform, not the product's transform helper.
function world(s, q) {
  const dx = (q[0] - s.imgW / 2) * s.mmPerPx, dy = (q[1] - s.imgH / 2) * s.mmPerPx;
  const r = {0: [dx,dy], 90: [-dy,dx], 180: [-dx,-dy], 270: [dy,-dx]}[s.rot];
  if (!r) throw Error('fixture requires a quarter-turn transform');
  return [s.x + s.imgW * s.mmPerPx / 2 + r[0], s.y + s.imgH * s.mmPerPx / 2 + r[1]];
}
const observe = expression => page.evaluate(expression);
const wait = expression => page.waitForFunction(expression, null, {timeout: 20000});
async function settle() {
  await wait(`typeof connection==='object'&&connection.phase==='ready'&&!oc.busy&&!ReferenceWorkspace.busy&&!ReferenceWorkspace.history.group`);
  await page.waitForTimeout(120); // Existing harness's inspector-render settle, unchanged.
  await wait(`!oc.busy&&!ReferenceWorkspace.busy&&!ReferenceWorkspace.history.group`);
}
async function disclose(selector) {
  for (let i = 0; i < 8; i++) {
    const d = await page.locator(selector).evaluate(e => {
      for (let p = e.parentElement; p; p = p.parentElement)
        if (p.tagName === 'DETAILS' && !p.open) return {id: p.id, text: p.querySelector(':scope > summary').textContent};
      return null;
    });
    if (!d) return;
    await (d.id ? page.locator(`#${d.id} > summary`) : page.locator('summary').filter({hasText: d.text}).first()).click();
  }
  throw Error(`could not disclose ${selector}`);
}
async function click(selector) { await disclose(selector); await page.locator(selector).click(); await settle(); }
async function fill(selector, value) {
  await disclose(selector); await page.locator(selector).fill(String(value));
  if (await page.locator(selector).inputValue() !== String(value)) throw Error(`input replaced: ${selector}`);
  await page.locator(selector).press('Tab'); await settle();
}
async function select(selector, value) { await disclose(selector); await page.locator(selector).selectOption(String(value)); await settle(); }
const tab = name => click(`#faceInspectorTabs [data-fi-tab="${name}"]`);
async function menu(selector) { await click('#fileMenuBtn'); await click(selector); }
async function newProject() {
  acceptNew = true;
  try { await menu('#btnNewProject'); await wait('oc.faces.length===0&&!ReferenceWorkspace.busy'); }
  finally { acceptNew = false; }
}
const source = () => observe(`ReferenceWorkspace.active(${bid})`);
const native = () => observe(`api('dump').then(r=>{if(!r.ok)throw Error('dump failed');return r.text})`);
const candidate = () => observe('RoomOutlineWorkspace.snapshot()');
async function clickSource(q) {
  const mm = world(await source(), q);
  const xy = await page.evaluate(mm => { const p = document.getElementById('faceEditorSvg').createSVGPoint();
    [p.x, p.y] = mm; const s = p.matrixTransform(document.getElementById('faceEditorRoot').getScreenCTM()); return [s.x, s.y]; }, mm);
  await page.mouse.click(...xy);
}
async function snapshot() {
  return observe(`(()=>{const p=ReferenceWorkspace.active(${bid}),s=ReferenceWorkspace.context().sources.get(p.sourceId);
    return {bid:${bid},loops:oc.bmap[${bid}],source:{meta:s.meta,bytes:Array.from(s.bytes)},
      page:Object.fromEntries(Object.entries(p).filter(([k])=>k!=='src')),
      review:ReferenceWorkspace.reconstructionState(${bid}),
      receipt:[...ReferenceWorkspace.context().reconstructionReviews.values()],
      placement:feSurf(${bid}),projection:feSurf(${bid})?ReferenceWorkspace.getFaceProjection(${bid},feSurf(${bid}).id):null};})()`);
}
async function alignment(s) {
  const actual = await page.evaluate(() => { const root = document.getElementById('faceEditorRoot');
    const image = document.getElementById('feUnderlay'); if (!image) return null;
    const m = root.getScreenCTM().inverse().multiply(image.getScreenCTM());
    return {matrix: [m.a,m.b,m.c,m.d,m.e,m.f], href: image.getAttribute('href'),
      width: image.width.baseVal.value, height: image.height.baseVal.value,
      opacity: Number(image.getAttribute('opacity'))}; });
  check('source image is rendered at its original page dimensions', !!actual && !!actual.href && actual.opacity > 0 &&
    actual.width === s.imgW && actual.height === s.imgH, actual);
  const probes = [[0,0],[30,30],[230,30],[130,110]];
  const rendered = probes.map(([x,y]) => [actual.matrix[0]*x+actual.matrix[2]*y+actual.matrix[4],
    actual.matrix[1]*x+actual.matrix[3]*y+actual.matrix[5]]);
  check('rendered SVG alignment matches independent calibration transform at four source points',
    rendered.every((q,i) => q.every((n,j) => Math.abs(n-world(s,probes[i])[j]) < 1e-6)), {rendered, expected: probes.map(p=>world(s,p))});
}
function freePort() { return new Promise((resolve, reject) => { const s = net.createServer();
  s.on('error', reject); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => resolve(p)); }); }); }
async function startService(label) {
  const port = await freePort(), logs = path.join(OUT, label);
  const stdout = fs.openSync(logs+'.stdout', 'wx'), stderr = fs.openSync(logs+'.stderr', 'wx');
  const args = ['geometry-web/start_local.py', '--port', String(port), '--binary-dir', path.join(OUT, 'native')];
  const child = spawn('python3', args, {cwd: ROOT, stdio: ['ignore', stdout, stderr],
    env: {...process.env, GEOMETRY_FEEDBACK_DIR: path.join(OUT, label+'-feedback')}});
  fs.closeSync(stdout); fs.closeSync(stderr);
  const record = {label, command: ['python3', ...args], pid: child.pid, startedUtc: new Date().toISOString()};
  services.push(record);
  const ended = new Promise(resolve => child.on('close', (code, signal) => {
    Object.assign(record, {exit: code, signal, endedUtc: new Date().toISOString()}); resolve(); }));
  child.on('error', e => { record.spawnError = e.message; });
  service = {child, record, ended, url: `http://127.0.0.1:${port}/`};
  for (let i = 0; i < 120; i++) {
    if (record.exit !== undefined || record.spawnError) throw Error('isolated launcher failed: '+JSON.stringify(record));
    try {
      const r = await fetch(service.url+'runtime', {signal: AbortSignal.timeout(1000)});
      if (r.ok) { record.runtime = await r.json(); break; }
    } catch (e) { record.lastProbeError = e.message; }
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  if (!record.runtime) throw Error('isolated service did not become ready; see launcher stderr');
  if (record.runtime.fresh !== true || path.resolve(record.runtime.root) !== ROOT || record.runtime.pid !== child.pid)
    throw Error('runtime is not fresh or does not belong to the owned checkout/process: '+JSON.stringify(record.runtime));
  const probe = execFileSync('python3', ['geometry-web/runtime_version.py', '--probe', String(port)], {cwd: ROOT, encoding: 'utf8'});
  write(label+'.probe.txt', probe);
  return record.runtime;
}
async function startBrowser() {
  receipt.browserLaunchAttempts++;
  browser = await chromium.launch({headless: true, chromiumSandbox: true,
    ...(process.env.GEOMETRY_CHROME ? {executablePath: process.env.GEOMETRY_CHROME} : {})});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}, acceptDownloads: true});
  // Select the product's documented download/file-input fallback, not an OS picker mock.
  await context.addInitScript(() => {
    Object.defineProperty(window, 'showSaveFilePicker', {value: undefined, configurable: true});
    Object.defineProperty(window, 'showOpenFilePicker', {value: undefined, configurable: true});
  });
  page = await context.newPage();
  page.on('pageerror', e => browserErrors.push({scenario: current, message: e.message}));
  page.on('console', m => { if (m.type() === 'error') browserErrors.push({scenario: current, message: m.text()}); });
  page.on('dialog', async d => { dialogs.push({scenario: current, type: d.type(), message: d.message(), accepted: acceptNew});
    if (acceptNew && d.type() === 'confirm') await d.accept(); else { browserErrors.push({scenario: current, message: 'unexpected dialog: '+d.message()}); await d.dismiss(); } });
  await page.goto(service.url); await settle();
  check('page identity and nonblank App controls', page.url() === service.url && /構形 Canvas/.test(await page.title()) &&
    await page.locator('#fileMenuBtn').isVisible());
}
async function stopOwned(label) {
  let failure;
  if (page && !page.isClosed()) {
    try { write(label+'.scene', await native()); } catch (e) { failure = e; }
  }
  if (browser) { try { await browser.close(); } catch (e) { failure ||= e; } browser = null; page = null; }
  if (service) {
    const s = service; service = null;
    const childrenPath = `/proc/${s.child.pid}/task/${s.child.pid}/children`;
    s.record.nativeChildrenBeforeStop = fs.existsSync(childrenPath) ?
      fs.readFileSync(childrenPath,'utf8').trim().split(/\s+/).filter(Boolean).map(Number) : [];
    if (s.record.exit === undefined) s.child.kill('SIGINT'); // Only this harness's child; serve.py closes its bridge.
    await Promise.race([s.ended, new Promise((_, reject) => { const t = setTimeout(() => reject(Error('owned service did not stop; no force kill')), 10000); t.unref(); })]);
    s.record.nativeChildrenRemaining = s.record.nativeChildrenBeforeStop.filter(pid=>fs.existsSync(`/proc/${pid}`));
    // CPython reports an uncaught KeyboardInterrupt as SIGINT (or 130); its
    // serve.py finally closes the native context. Preserve the actual exit.
    if ((![0,130].includes(s.record.exit) && s.record.signal !== 'SIGINT') || s.record.nativeChildrenRemaining.length)
      failure ||= Error('owned service did not finish normal interrupt cleanup: '+JSON.stringify(s.record));
  }
  if (failure) throw failure;
}
async function acquire() {
  await click('#refRoomPick'); await clickSource([70,70]);
  await wait('!!RoomOutlineWorkspace.snapshot()||!RoomOutlineWorkspace.hasWork');
  check('candidate acquired through App', !!await candidate());
}
async function applyVertices(points) {
  await fill('#refRoomVertices', points.map(p=>p.join(',')).join('\n')); await click('#refRoomApplyVertices');
  check('manual vertex sequence retained exactly', equal((await candidate()).points, points));
}
async function confirm(initial) {
  await page.locator('#refRoomReviewed').check(); await page.locator('#refRoomConfirm').click();
  await wait(`!!document.querySelector('dialog.reference-impact[open]')||(!oc.busy&&!RoomOutlineWorkspace.hasWork)`);
  const impact = page.locator('dialog.reference-impact[open]');
  if (await impact.count()) {
    check('impact preview leaves formal scene intact', await native() === initial);
    write(current+'-impact.txt', await impact.innerText());
    await impact.getByRole('button', {name: '確認套用', exact: true}).click();
  }
  await settle(); await wait(`!RoomOutlineWorkspace.hasWork&&ReferenceWorkspace.reconstructionState(${bid})==='confirmed'`);
}
async function setProjection() {
  await tab('prop'); await fill('#faceInspectorContent #placeOZ', 2500); await click('#faceInspectorContent #placeSubmit');
  await wait(`!!feSurf(${bid})`); await click('#faceInspectorContent [data-fp-edit]'); await wait(`$('fpDialog').open`);
  await select('#fpPurpose', 'space-boundary-plan'); await select('#fpView', 'top');
  await click('#fpInterior'); await click('#fpApply'); await wait(`!$('fpDialog').open`);
}
const projection = {kind: 'space-boundary-plan', view: 'top', region: 'interior', wallSide: 'outside'};
async function scenario(kind, shape, index) {
  current = `${kind}-${shape.name}`;
  const runtimeA = await startService(current+'-edit'); await startBrowser(); await newProject();
  const file = path.join(OUT, kind === 'pdf' ? 'rooms.pdf' : shape.name+'.png');
  await click('#fileMenuBtn'); const choosing = page.waitForEvent('filechooser');
  await click('#btnImportReference'); await (await choosing).setFiles(file);
  await wait(`$('referenceDialog').open&&!$('refApply').disabled`);
  if (kind === 'pdf' && index > 0) { await fill('#refPageNumber', index+1);
    await wait(`!$('refApply').disabled&&$('refPagePreview').querySelector('img')?.alt==='第 ${index+1} 頁預覽'`); }
  await click('#refApply'); await wait('!!oc.edit&&!!ReferenceWorkspace.active(oc.edit.bid)');
  bid = await observe('oc.edit.bid'); await tab('underlay');
  const imported = await native();
  await click('#ulCalibStart'); await clickSource([30,30]); await clickSource([230,30]);
  await wait('fe.ulCalib?.pts.length===2'); await fill('#ulCalibDist', 2000); await click('#ulCalibApply'); await click('#refFit');
  const s = await source(), initial = await native();
  check('calibration does not scale formal geometry', initial === imported);
  check('selected source bytes, PDF page and 10 mm calibration', s.sourceId === hash(fs.readFileSync(file)) &&
    s.page === (kind === 'pdf' ? index+1 : 1) && Math.abs(s.mmPerPx-10) < 1e-6 && s.rot === 0, s);
  await alignment(s);
  const expected = corrections[shape.name].map(([x,y])=>[x+s.x,y+s.y]);
  await acquire();
  check('acquired exact cyclic topology, not bbox or area', canonical((await candidate()).points) ===
    canonical(shape.inside.map(p=>world(s,p).map(Math.round))));
  check('acquisition leaves formal scene intact', await native() === initial);
  const beforeBlockedSave = await observe('ReferenceWorkspace.saveOutcome.seq');
  let unexpectedDownload = false;
  const rejectedDownload = () => { unexpectedDownload = true; };
  page.on('download', rejectedDownload);
  await menu('#btnSaveProject');
  await wait(`ReferenceWorkspace.saveOutcome.seq>${beforeBlockedSave}`);
  page.off('download', rejectedDownload);
  check('UI Save refuses the session-only candidate', !unexpectedDownload &&
    (await observe('ReferenceWorkspace.saveOutcome')).ok === false && await native() === initial);
  await click('#refRoomCancel'); check('cancel leaves formal scene intact', await native() === initial && !await candidate());
  await acquire();
  const beforeInvalid = (await candidate()).points;
  await fill('[data-room-edge-length="0"]',0);
  check('invalid dimension preserves candidate and formal scene and prevents confirmation',
    equal((await candidate()).points,beforeInvalid) && await native() === initial && await page.locator('#refRoomConfirm').isDisabled());
  // Authored notch/leg changes, followed by an actual +40 mm first-edge resize.
  await applyVertices(corrections[shape.name].map(([x,y])=>[(x===2320?2280:x)+s.x,y+s.y]));
  await page.locator('#refRoomReviewed').check();
  await fill('[data-room-edge-length="0"]', 2000);
  check('dimension edit clears review and keeps formal scene unchanged',
    equal((await candidate()).points, expected) && !(await candidate()).reviewed &&
    await page.locator('#refRoomConfirm').isDisabled() && await native() === initial);
  for (let i = 0; i < expected.length; i++) {
    await fill(`[data-room-edge-length="${i}"]`, length(expected[i], expected[(i+1)%expected.length]));
    check(`edge ${i+1} blur applies exact dimensions without topology drift`, equal((await candidate()).points, expected) && await native() === initial);
  }
  const dimensions = expected.map((a,i)=>length(a,expected[(i+1)%expected.length]));
  check('all visible edge rows and labels match independent dimensions', equal(
    await page.locator('[data-room-edge-length]').evaluateAll(es=>es.map(e=>Number(e.value))), dimensions) && equal(
    await page.locator('[data-room-dimensions] li').allTextContents(), dimensions.map((n,i)=>
      `邊 ${i+1}：擬提交 ${n} mm${i===dimensions.length-1?'（人工核對入值）':''}`)));
  await page.screenshot({path: path.join(OUT,current+'-corrected.png')});
  await confirm(initial);
  const confirmed = await native(), confirmedSnapshot = await snapshot();
  check('formal confirmation stores exact edited topology and source receipt',
    equal(confirmedSnapshot.loops[0].verts, expected) && confirmedSnapshot.loops.length === 1 && confirmedSnapshot.review === 'confirmed');
  await click('#faceUndoButton'); check('UI Undo restores whole original native scene', await native() === initial);
  await click('#faceRedoButton'); check('UI Redo restores confirmed native scene and receipt', await native() === confirmed &&
    equal((await snapshot()).receipt, confirmedSnapshot.receipt));
  await setProjection();
  const saved = await snapshot(), savedScene = await native();
  check('explicit placement and projection retained', saved.placement.origin[2] === 2500 && equal(saved.projection, projection));
  await click('#btnBack'); await click('#fileMenuBtn');
  const downloading = page.waitForEvent('download'); await click('#btnSaveProject'); const download = await downloading;
  const archive = path.join(OUT,current+'.gcanvas'); await download.saveAs(archive);
  check('UI Save produced a real gcanvas download', download.suggestedFilename().endsWith('.gcanvas') && fs.statSync(archive).size > 100);
  const entries = require('../../geometry-web/vendor/fflate/umd/index.js').unzipSync(fs.readFileSync(archive));
  check('download contains the exact formal native scene', Buffer.from(entries['world.scene']).toString('utf8') === savedScene);
  write(current+'-saved.json', {snapshot:saved,archiveSha256:hash(fs.readFileSync(archive)),sceneSha256:hash(savedScene)});
  await stopOwned(current+'-edit-final');
  const runtimeB = await startService(current+'-open'); await startBrowser();
  check('Open uses a new server/native session', runtimeB.pid !== runtimeA.pid && runtimeB.session !== runtimeA.session);
  await newProject();
  check('new process is blank before UI Open', await observe('oc.faces.length===0&&ReferenceWorkspace.context().sources.size===0'));
  write(current+'-blank.scene', await native());
  await click('#fileMenuBtn'); const opening = page.waitForEvent('filechooser');
  await click('#btnOpenProject'); await (await opening).setFiles(archive);
  await wait(`!ReferenceWorkspace.busy&&oc.faces.some(f=>f.id===${bid})`);
  await page.locator(`.ocard[data-kind="boundary"][data-id="${bid}"]`).dblclick(); await wait(`oc.edit?.bid===${bid}`); await tab('underlay');
  check('fresh UI Open preserves full native scene', await native() === savedScene);
  const reopened = await snapshot();
  check('fresh Open preserves exact loops, source bytes, page, calibration, receipt and projection', equal(reopened, saved), reopened);
  await alignment(await source()); await page.screenshot({path:path.join(OUT,current+'-opened.png')});
  await tab('prop'); await click('#faceInspectorContent [data-fp-build]');
  await wait(`$('smWorkspace').open&&SpaceModelWorkspace.snapshot().phase==='ready'`);
  await fill('#smBottom',0); await fill('#smHeight',3000); await fill('#smThickness',100);
  if (await page.locator('#smWallsEnabled').isChecked()) await click('#smWallsEnabled');
  await click('#smPreview'); await wait('SpaceModelWorkspace.snapshot().resultSummary!==null&&!SpaceModelWorkspace.snapshot().stale');
  const preview = await observe('SpaceModelWorkspace.snapshot().resultSummary');
  const area = Math.abs(expected.reduce((sum,a,i)=>{const b=expected[(i+1)%expected.length];return sum+a[0]*b[1]-b[0]*a[1];},0))/2;
  check('projection continuation previews the exact corrected ring without modifying formal scene',
    equal((await snapshot()).loops[0].verts,expected) && preview.closed === true &&
    preview.face_count === expected.length+2 && preview.volume_mm3 === String(area*3000) && await native() === savedScene, preview);
  await page.keyboard.press('Escape'); await wait(`!$('smWorkspace').open`);
  check('no App console errors or unexpected dialogs', browserErrors.length === 0, browserErrors);
  await stopOwned(current+'-open-final');
}
(async () => {
  let exit = 2;
  try {
    const ready = preflight();
    if (!ready) console.error('NOT_STARTED '+receipt.preflight.blockers.join('; '));
    else if (process.argv.includes('--preflight-only')) {
      receipt.preflight.only = true; console.log('PREFLIGHT_READY; App not started');
    } else {
      receipt.state = 'running'; write('rooms.pdf', pdf());
      for (const shape of shapes) write(shape.name+'.png', png(shape));
      for (let i=0;i<shapes.length;i++) for (const kind of ['pdf','image']) await scenario(kind, shapes[i], i);
      receipt.state = 'passed'; exit = 0;
    }
  } catch (e) {
    receipt.state = e instanceof AssertionFailure ? 'assertion_failed' : 'execution_failed';
    receipt.error = {name:e.name,message:e.message,stack:e.stack}; exit = e instanceof AssertionFailure ? 1 : 3;
    console.error(e.stack);
  } finally {
    try { await stopOwned(current+'-cleanup'); }
    catch (e) { receipt.cleanupError = e.stack; receipt.state = 'execution_failed'; exit = 3; }
    receipt.endedUtc = new Date().toISOString(); receipt.exit = exit;
    receipt.headAtEnd = git('rev-parse','HEAD'); write('receipt.json',receipt);
    console.log(JSON.stringify({state:receipt.state,appAssertions:receipt.appAssertions,browserLaunchAttempts:receipt.browserLaunchAttempts,exit,receipt:path.join(OUT,'receipt.json')}));
    process.exitCode = exit;
  }
})();
