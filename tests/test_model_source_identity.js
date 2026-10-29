/* K3-44 model source identity. Pure functions; no bridge and no browser. */
'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const L = require(process.env.MODEL_SOURCE_IDENTITY_MODULE || '../geometry-web/identity-ledger.js');
const P = require('../geometry-web/project-store.js');
const M = require('../geometry-web/model-update.js');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');

const mark = '0123456789abcdef0123456789abcdef:1';
const mark2 = 'fedcba9876543210fedcba9876543210:2';
const hash = 'a'.repeat(64);
const pin = 'b'.repeat(64);
const scene = 'boundary 1 outline 0,0 100,0 100,100 0,100\n';
const live = (id, incarnation, definitionPin = pin) => ({incarnation, definitionFingerprint: definitionPin, id});

function facesModel() {
  const pkg = {
    manifest:{schema:'geometry-model-package/1',profile:'orthogonal-model/1',axiom_revision:'revision',axiom_sha256:hash,
      generator:{name:'fixture',version:'1'},capabilities:['composite-space/1'],units:'mm',
      coordinate_system:{handedness:'right',up:'+Z'},source_sha256:hash,geometry_sha256:hash},
    definitions:{base_scene:scene,extensions:[]},
    request:{roots:[{kind:'composite_space',id:2}],role:'enclosure',target:'surface-set',allow_partial:false},
    derived:{status:'COMPLETE',objects:[{root:{kind:'composite_space',id:2},member_path:[],role:'enclosure',status:'COMPLETE',
      representation:'mesh',closure:'open',component:0,vertices_mm:[[0,0,0],[100,0,0],[0,100,0]],triangles:[[0,1,2]],
      face_sources:[[]],boundary_shells:[{id:0,role:'open',triangles:[0]}],volume_mm3:null}]},diagnostics:[]};
  return {id:'model-a',name:'已建立空間',created_at:'2026-09-27T10:00:00.000Z',
    source:{kind:'example',placement_id:1,boundary_id:1,scene_hash:hash},
    input:{mode:'faces',base_scene:scene,uses:[{placement_id:1,orientation:1,purpose:'boundary'}],obstacles:[]},
    result:{ok:true,schema:'geometry-space-preview/1',space:pkg,volume:null,clearance:null,walls:null,source_sha256:hash,diagnostics:[],
      summary:{source_placement:null,source_z:null,bottom:null,top:null,generated_faces:[],missing:['開放空間'],face_count:1,
        closed:false,volume_mm3:null,clearance_mm3:null,wall_volume_mm3:null,wall_diagnostics:[]}}};
}
function planInput() {
  return {mode:'plan', placement_id:0, boundary_id:1, timbers:[{id:5},{id:6}], obstacles:[{kind:'column', id:2}]};
}
function planIdentity(timber6 = {role:'timber', kind:'timber', id:6, incarnation:mark}) {
  return {schema:L.SCHEMA, roots:[
    {role:'placement', kind:'placement', id:0, incarnation:mark},
    {role:'boundary', kind:'boundary', id:1, incarnation:mark, definitionPin:pin},
    {role:'timber', kind:'timber', id:5, incarnation:mark},
    timber6,
    {role:'obstacle', kind:'column', id:2, incarnation:mark},
  ]};
}
function root(kind, id, incarnation, status) {
  return {role:kind === 'column' ? 'obstacle' : kind, kind, id, incarnation, status, confirmed:false};
}

test('deidentified base matches the project strip and drops ledger marks', () => {
  const marked = 'requires identity-ledger/1\nboundary 1 outline 0,0 10,0 10,10\nidentity placement 1 ' + mark + '\nidentity-ledger activate\n';
  assert.equal(L.deidentifiedBase(marked), P.stripIdentityLedger(marked));
  assert.equal(L.deidentifiedBase(marked).includes('identity '), false);
  assert.equal(L.deidentifiedBase(scene), scene);
});

test('撤掉實作：基準保留記號', () => {
  const marked = 'boundary 1 outline 0,0 10,0 10,10\nidentity placement 1 ' + mark + '\n';
  assert.equal(L.deidentifiedBase(marked).includes('identity '), false);
});

test('plan and faces roots follow the record, and faces plus timbers is unsupported', () => {
  const plan = L.expectedRoots(planInput());
  assert.equal(plan.ok, true);
  assert.deepEqual(plan.roots.map(item => item.role + ':' + item.id), ['placement:0', 'boundary:1', 'timber:5', 'timber:6', 'obstacle:2']);
  const faces = L.expectedRoots({mode:'faces', uses:[{placement_id:1},{placement_id:2}], obstacles:[]});
  assert.deepEqual(faces.roots.map(item => item.id), [1, 2]);
  const refused = L.expectedRoots({mode:'faces', uses:[{placement_id:1}], timbers:[{id:5}], obstacles:[]});
  assert.equal(refused.ok, false);
  assert.equal(refused.code, 'UNSUPPORTED');
  assert.equal(L.planFaces([{orientation:1,purpose:'boundary'}], [{placement_id:1}], {timbers:[]}).ok, true);
});

test('a matching sourceIdentity is optional and survives a model package round trip', async () => {
  const plain = facesModel();
  P.validateSpaceModel(plain);
  assert.equal(Object.hasOwn(plain, 'sourceIdentity'), false);
  const identified = facesModel();
  identified.sourceIdentity = {schema:L.SCHEMA, roots:[{role:'use', kind:'placement', id:1, incarnation:mark}]};
  P.validateSpaceModel(identified);
  const manifest = {format:P.FORMAT, projectId:'project-a', name:'模型專案', sceneHash:hash, sources:[], faces:[], models:[identified]};
  const loaded = await P.unpack(await P.pack('', manifest, new Map(), zip), zip);
  assert.deepEqual(loaded.manifest.models[0].sourceIdentity, identified.sourceIdentity);
  assert.equal(loaded.manifest.models[0].input.base_scene, identified.input.base_scene);
});

test('import rejects a mismatched identity, a marked base scene, and leaves the good record valid', () => {
  const good = facesModel();
  good.sourceIdentity = {schema:L.SCHEMA, roots:[{role:'use', kind:'placement', id:1, incarnation:mark}]};
  const before = JSON.stringify(good);
  const mismatch = facesModel();
  mismatch.sourceIdentity = {schema:L.SCHEMA, roots:[{role:'use', kind:'placement', id:9, incarnation:mark}]};
  assert.throws(() => P.validateSpaceModel(mismatch), /根集合不一致/);
  const naked = facesModel();
  naked.sourceIdentity = {schema:L.SCHEMA, roots:[{role:'use', kind:'placement', id:1, incarnation:null}]};
  assert.throws(() => P.validateSpaceModel(naked), /根不合法/);
  const marked = facesModel();
  marked.input.base_scene += 'identity placement 1 ' + mark + '\n';
  assert.throws(() => P.validateSpaceModel(marked), /去身分/);
  P.validateSpaceModel(JSON.parse(before));
});

test('an uncovered assembly timber is accepted from the record alone', () => {
  const input = planInput();
  const identity = planIdentity({role:'timber', kind:'timber', id:6, incarnation:null, uncovered:'assembly-owned'});
  const world = new Map([['timber:6', live(6, mark2)]]);
  assert.equal(L.validateSourceIdentity(identity, input), true);
  assert.equal(world.get('timber:6').incarnation, mark2);
  const judged = L.judgeRoots(identity, world);
  assert.equal(judged.find(item => item.id === 6).status, 'unknown');
  assert.equal(judged.find(item => item.id === 6).id, 6);
  for (const bad of [
    planIdentity({role:'timber', kind:'timber', id:6, incarnation:null}),
    planIdentity({role:'timber', kind:'timber', id:6, incarnation:mark, uncovered:'assembly-owned'}),
    planIdentity({role:'timber', kind:'timber', id:6, incarnation:null, uncovered:'owned'}),
    {schema:L.SCHEMA, roots:planIdentity().roots.map(item => item.id === 0 ? {...item, uncovered:'assembly-owned', incarnation:null} : item)},
  ]) assert.throws(() => L.validateSourceIdentity(bad, input), /不合法|不一致/);
});

test('unknown, absent, replaced and conflict keep the saved id and are not prefilled', () => {
  const saved = 6;
  const cases = [
    ['unknown', null],
    ['absent', undefined],
    ['replaced', live(99, mark2)],
    ['conflict', {...live(99, mark), conflict:true}],
  ];
  for (const [status, node] of cases) {
    const identity = {roots:[{role:'timber', kind:'timber', id:saved, incarnation:mark}]};
    const graph = new Map();
    if (node) graph.set('timber:' + saved, node);
    if (status === 'unknown') identity.roots[0] = {role:'timber', kind:'timber', id:saved, incarnation:null, uncovered:'assembly-owned'};
    const judged = L.judgeRoots(identity, status === 'absent' ? new Map() : graph);
    assert.equal(judged[0].id, saved);
    assert.equal(judged[0].status, status);
    assert.equal(L.prefillRoots(judged).length, 0);
    assert.equal(judged[0].confirmed, false);
  }
});

test('only a continuous root is prefilled, and prefill is not confirmation', () => {
  const judged = [
    root('timber', 5, mark, 'continuous'),
    root('timber', 6, mark, 'replaced'),
    root('placement', 0, mark, 'continuous'),
  ];
  const picked = L.prefillRoots(judged);
  assert.deepEqual(picked.map(item => item.id), [5, 0]);
  assert.equal(picked.every(item => item.confirmed === false), true);
});

test('撤掉實作：同編號就預填', () => {
  const judged = [root('timber', 6, mark, 'replaced')];
  assert.equal(L.prefillRoots(judged).length, 0);
});

test('edges stay empty unless the boundary stayed continuous with the same definition pin', () => {
  const edges = [0, 1, 2, 3];
  assert.deepEqual(L.edgesPrefill('continuous', true, edges), edges);
  assert.equal(L.edgesPrefill('continuous', false, edges).length, 0);
  assert.equal(L.edgesPrefill('replaced', true, edges).length, 0);
  assert.equal(edges.length, 4);
});

test('撤掉實作：定義指紋變仍預填邊', () => {
  assert.equal(L.edgesPrefill('continuous', false, [0, 1, 2, 3]).length, 0);
});

test('absent, replaced and conflict cannot preview until the person removes or retargets them', () => {
  const absent = [root('column', 2, mark, 'absent')];
  assert.equal(L.previewAllowed(absent), false);
  assert.equal(L.previewAllowed([{...absent[0], decision:'remove'}]), true);
  assert.equal(L.previewAllowed([{...root('timber', 6, mark, 'replaced'), decision:'retarget'}]), true);
  assert.equal(L.previewAllowed([root('timber', 6, mark, 'conflict')]), false);
  assert.equal(absent[0].id, 2);
});

test('confirmIdentity refuses a changed mark and writes nothing itself', () => {
  const reviewed = [root('timber', 5, mark, 'continuous')];
  const changed = [root('timber', 5, mark2, 'replaced')];
  const verdict = L.confirmIdentity(reviewed, changed);
  assert.equal(verdict.ok, false);
  assert.equal(verdict.code, 'STALE');
  assert.equal(reviewed[0].incarnation, mark);
});

test('撤掉實作：確認不重比', () => {
  const verdict = L.confirmIdentity([root('timber', 5, mark, 'continuous')], [root('timber', 5, mark2, 'replaced')]);
  assert.equal(verdict.ok, false);
});

test('faces update reuses orientation and purpose and rejects a different face count', () => {
  const oldUses = [
    {placement_id:1, orientation:1, purpose:'boundary'},
    {placement_id:2, orientation:-1, purpose:'boundary'},
    {placement_id:3, orientation:1, purpose:'calculation-cap'},
  ];
  const next = L.planFaces(oldUses, [{placement_id:1},{placement_id:2},{placement_id:3}]);
  assert.equal(next.ok, true);
  assert.deepEqual(next.uses.map(item => [item.orientation, item.purpose]), [[1,'boundary'], [-1,'boundary'], [1,'calculation-cap']]);
  assert.equal(L.planFaces(oldUses, oldUses.slice(0, 2)).code, 'REJECTED');
  assert.equal(L.planFaces(oldUses, [{placement_id:1},{placement_id:1},{placement_id:3}]).code, 'REJECTED');
  assert.equal(L.planFaces(oldUses, oldUses, {timbers:[{id:5}]}).code, 'UNSUPPORTED');
  assert.equal(L.planFaces(oldUses, oldUses, {assemblyOwned:true}).code, 'UNSUPPORTED');
});

test('continuity summary uses the three sentences and does not treat an unjudged record as proved', () => {
  assert.equal(L.continuitySummary(null).text, '物件延續性未知');
  assert.equal(L.continuitySummary({roots:[{incarnation:mark}]}).token, 'unknown');
  assert.equal(L.continuitySummary({roots:[root('timber', 5, mark, 'continuous'), root('boundary', 1, mark, 'continuous')]}).text, '物件延續已證明');
  const partial = L.continuitySummary({roots:[root('timber', 5, mark, 'continuous'), root('timber', 6, mark2, 'replaced'), root('column', 2, mark, 'absent')]});
  assert.equal(partial.text, '部分來源物件已不存在或已刪除重建');
  assert.deepEqual(partial.listed, ['timber #6', 'column #2']);
  assert.equal(L.continuitySummary({roots:[root('timber', 6, null, 'unknown')]}).text, '物件延續性未知');
});

test('building a source identity stamps the live mark and refuses an assembly-owned timber', () => {
  const graph = new Map([
    ['placement:0', live(0, mark, pin)],
    ['boundary:1', live(1, mark, pin)],
    ['timber:5', live(5, mark, pin)],
    ['timber:6', live(6, mark2, pin)],
    ['column:2', live(2, mark, pin)],
  ]);
  const identity = L.buildSourceIdentity(planInput(), graph);
  assert.equal(identity.roots.find(item => item.id === 6).incarnation, mark2);
  assert.equal(identity.roots.find(item => item.role === 'boundary').definitionPin, pin);
  assert.equal(identity.roots.every(item => item.confirmed !== true), true);
  graph.set('timber:6', {incarnation:null, id:6});
  assert.throws(() => L.buildSourceIdentity(planInput(), graph), error => error.code === 'UNSUPPORTED');
});

function updateHarness(extra = {}) {
  const text = scene;
  const digest = value => crypto.createHash('sha256').update(value).digest('hex');
  const pkg = facesModel().result.space;
  pkg.manifest.source_sha256 = digest(text);
  pkg.definitions.base_scene = text;
  const record = facesModel();
  record.source.kind = 'scene';
  record.source.scene_hash = digest(text);
  record.result.source_sha256 = digest(text);
  record.result.space = pkg;
  record.input = {mode:'plan', base_scene:text, placement_id:1, obstacles:[], settings:{bottom:0, height:3000, edges:[0,1,2,3], floor:'none', ceiling:'none', holes:'none', wall_thickness:null}};
  delete record.sourceIdentity;
  P.validateSpaceModel(record);
  const h = new P.ContextHistory(() => ({models:[], sources:new Map(), faceProjections:new Map()}));
  h.frame.context.models = [record];
  let revision = 1;
  const source = {scene:text, revision:7};
  const commits = [];
  const selection = {placement_id:1, boundary_id:1, edges:[0,1,2,3], obstacles:[], timbers:[], projection:null};
  const produce = request => {
    const after = JSON.parse(JSON.stringify(request.record));
    after.input.base_scene = request.current_scene;
    after.source.scene_hash = digest(request.current_scene);
    after.result.source_sha256 = after.source.scene_hash;
    after.result.space.manifest.source_sha256 = after.source.scene_hash;
    after.result.space.definitions.base_scene = request.current_scene;
    const pair = (left, right) => ({before:JSON.parse(JSON.stringify(left)), after:JSON.parse(JSON.stringify(right))});
    const pinOf = value => digest(M.canonical(value));
    return {ok:true, schema:'geometry-model-update-candidate/1', identity:'unknown',
      old_record_sha256:digest(M.canonical(request.record)), current_scene_sha256:digest(request.current_scene),
      selection:JSON.parse(JSON.stringify(request.selection)), record:after,
      diff:{source:pair(request.record.source, after.source), input:pair(request.record.input, after.input),
        settings:pair(request.record.input.settings, after.input.settings), summary:pair(request.record.result.summary, after.result.summary),
        packages:['space','volume','clearance','walls','timbers'].map(kind => ({kind,
          before:request.record.result[kind] ? pinOf(request.record.result[kind].manifest) : null,
          after:after.result[kind] ? pinOf(after.result[kind].manifest) : null}))},
      runtime:{base_binary_sha256:hash, bridge_binary_sha256:hash, producer_sha256:hash, axiom_sha256:hash}};
  };
  const host = {getState:() => ({context:h.frame.context, frame:h.frame, revision, contextToken:'project', blocked:false, undo:h.undo.at(-1) || null, redo:null, group:null}),
    getRecord:id => h.frame.context.models.find(item => item.id === id),
    readSource:async () => JSON.parse(JSON.stringify(source)), produce:async request => produce(request),
    validateRecord:P.validateSpaceModel, sha:async bytes => digest(bytes),
    commit:(id, value) => {commits.push(value); h.changeModels([value]); revision += 1; return JSON.parse(JSON.stringify(value));},
    ...extra};
  return {update:M.create(host), commits, selection, record};
}

test('an update without the identity hook keeps the old record shape', async () => {
  const f = updateHarness();
  f.update.begin(f.record.id);
  const reviewed = await f.update.prepare(f.selection);
  assert.equal(reviewed.identity, 'unknown');
  assert.equal(Object.hasOwn(reviewed, 'identityReceipt'), false);
  const saved = await f.update.confirm(reviewed.reviewId);
  assert.equal(Object.hasOwn(saved, 'sourceIdentity'), false);
  assert.equal(f.commits.length, 1);
});

test('a stale identity verdict commits nothing', async () => {
  const f = updateHarness({confirmIdentity:async () => ({ok:false, code:'STALE'})});
  f.update.begin(f.record.id);
  const reviewed = await f.update.prepare(f.selection);
  await assert.rejects(f.update.confirm(reviewed.reviewId), /過期/);
  assert.equal(f.commits.length, 0);
  assert.equal(Object.hasOwn(f.update ? f.record : f.record, 'sourceIdentity'), false);
});

test('a confirmed identity is written onto the same model after preview', async () => {
  const identity = {schema:L.SCHEMA, roots:[
    {role:'placement', kind:'placement', id:1, incarnation:mark},
    {role:'boundary', kind:'boundary', id:1, incarnation:mark},
  ]};
  const f = updateHarness({
    inspectIdentity:async () => ({schema:'geometry-model-update-candidate/2', identity:{ledger:'identity-ledger/1', roots:[]}}),
    confirmIdentity:async () => ({ok:true, sourceIdentity:identity}),
  });
  f.update.begin(f.record.id);
  const reviewed = await f.update.prepare(f.selection);
  assert.equal(reviewed.identityReceipt.schema, 'geometry-model-update-candidate/2');
  const saved = await f.update.confirm(reviewed.reviewId);
  assert.equal(saved.id, f.record.id);
  assert.deepEqual(saved.sourceIdentity, identity);
  assert.equal(saved.input.base_scene, f.record.input.base_scene);
  assert.equal(f.commits.length, 1);
});
