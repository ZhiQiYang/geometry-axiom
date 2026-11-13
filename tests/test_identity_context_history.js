/* Actual bridge receipts drive the production ContextHistory. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const {randomBytes, webcrypto} = require('node:crypto');
const fs=require('node:fs'),Module=require('node:module');
function productionStore() {
  if(!process.env.IDENTITY_CONTEXT_MUTANT)return require('../geometry-web/project-store.js');
  assert.equal(process.env.IDENTITY_CONTEXT_MUTANT,'B3-NOOP-HISTORY','unknown context mutation');
  const file=require.resolve('../geometry-web/project-store.js'),m=new Module(file,module);
  m.filename=file;m.paths=Module._nodeModulePaths(require('node:path').dirname(file));
  const source=fs.readFileSync(file,'utf8'),guard='if (result.history_changed === false) {';
  assert.equal(source.split(guard).length,2,'B3 mutation anchor must be unique');
  m._compile(source.replace(guard,'if (false) {'),file);return m.exports;
}
const P = productionStore();
globalThis.crypto ||= webcrypto;
const binary = process.env.GEOMETRY_TEST_BRIDGE;
function native(commands) {
  assert.ok(binary, 'GEOMETRY_TEST_BRIDGE must identify the fresh native bridge');
  const result = spawnSync(binary, [], {input:commands.join('\n')+'\n',encoding:'utf8',maxBuffer:16*1024*1024});
  assert.equal(result.status,0,result.stderr);
  const rows = result.stdout.trim().split('\n').map(JSON.parse);
  assert.equal(rows.length,commands.length,'one native receipt per command');
  rows.forEach((row,i)=>assert.equal(row.ok,true,commands[i]+': '+JSON.stringify(row)));
  return rows;
}
function context() {
  const room={schema:'source-rooms/1',planes:[{id:'plane',sourceId:'a'.repeat(64),page:1,coordinateSpace:'pdf-page-viewport/1',
    pageSize:[600,400],calibration:null,alignment:{x:0,y:0,mmPerPx:20,rotation:0},basisRevision:1}],
    collections:[{id:'collection',planeId:'plane',roomIds:['room']}],rooms:[{id:'room',name:'A',
      boundaryRef:{kind:'boundary',id:1,associationPin:'b'.repeat(64)},acceptedBasisRevision:1,reviewState:'confirmed'}]};
  const history=new P.ContextHistory(()=>({id:'project',groups:new Map(),featureAttachments:[]}));
  history.sync([1]);history.frame.context.featureAttachments=[P.Features.record('source-rooms',room)];
  return history;
}
const state = h => ({ids:[...h.frame.ids],attachments:JSON.parse(JSON.stringify(h.frame.context.featureAttachments))});
const initial = 'boundary 1 outline 0,0 4000,0 4000,3000 0,3000';
const changed = 'boundary 1 outline 0,0 5000,0 5000,3000 0,3000';
function setup(active) {return ['reset','identity-epoch '+randomBytes(16).toString('hex'),'line '+initial,
  ...(active?['line identity-ledger activate']:[])];}

test('B3 same-value line keeps attachments and ids aligned with native undo/redo, active and inactive',()=>{
  for(const active of [false,true]) {
    const commands=[...setup(active),'dump','line '+changed,'dump','line '+changed,'dump','line undo','dump','line redo','dump'];
    const rows=native(commands), start=setup(active).length, h=context(), before=state(h);
    h.observe(commands[start+1],rows[start+1]);const after=state(h);
    assert.equal(after.attachments[0].value.rooms[0].reviewState,'needs-review');
    assert.equal(h.undo.length,1);
    h.observe(commands[start+3],rows[start+3]);
    assert.equal(h.undo.length,1,'B3_NO_PHANTOM_LINE_HISTORY');
    assert.deepEqual(state(h),after,'B3_NOOP_ATTACHMENT_AND_IDS');
    h.observe(commands[start+5],rows[start+5]);
    assert.deepEqual(state(h),before,'B3_FRONTEND_UNDO_MATCHES_NATIVE');
    assert.equal(rows[start+6].text,rows[start].text,'B3_NATIVE_UNDO_REAL_STEP');
    h.observe(commands[start+7],rows[start+7]);
    assert.deepEqual(state(h),after);
    assert.equal(rows[start+8].text,rows[start+2].text);
  }
});

test('B3 same-value native drag does not create a frontend history frame',()=>{
  const commands=['reset','identity-epoch '+randomBytes(16).toString('hex'),
    'line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'line spec mid 500','line guide 1 1 v spec:mid','line identity-ledger activate',
    'line spec real 17','dump','drag 0 2 500 0','dump','line undo','dump'];
  const rows=native(commands),h=context(),before=state(h);
  h.observe(commands[6],rows[6]);h.observe(commands[8],rows[8]);
  assert.equal(h.undo.length,1,'B3_NO_PHANTOM_DRAG_HISTORY');
  assert.equal(rows[7].text,rows[9].text);
  h.observe(commands[10],rows[10]);
  assert.equal(h.undo.length,0);assert.deepEqual(state(h),before);
  assert.doesNotMatch(rows[11].text,/spec real 17/);
});

test('B3 no-op receipt inside a group preserves history controls and leaves the group clean',()=>{
  const commands=[...setup(true),'line '+changed,'line history-begin','line '+changed,'line history-end','line undo','dump'];
  const rows=native(commands),start=setup(true).length,h=context(),before=state(h);
  h.observe(commands[start],rows[start]);
  h.observe(commands[start+1],rows[start+1]);assert.equal(h.group.dirty,false);
  h.observe(commands[start+2],rows[start+2]);assert.equal(h.group.dirty,false,'B3_NOOP_GROUP_IS_CLEAN');
  h.observe(commands[start+3],rows[start+3]);assert.equal(h.group,null);assert.equal(h.undo.length,1);
  h.observe(commands[start+4],rows[start+4]);assert.deepEqual(state(h),before);
  assert.match(rows[start+5].text,/4000,0 4000,3000/);
});
