'use strict';
// One project archive must retain #362 model pins and every upstream reader.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const P = require('../geometry-web/project-store.js');
const L = require('../geometry-web/identity-ledger.js');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const hash = 'a'.repeat(64), mark = '0123456789abcdef0123456789abcdef:1';
const scene = 'boundary 1 outline 0,0 100,0 100,100 0,100\n';

function model() {
  const pkg = {
    manifest:{schema:'geometry-model-package/1',profile:'orthogonal-model/1',axiom_revision:'fixture',axiom_sha256:hash,
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
    sourceIdentity:{schema:L.SCHEMA,roots:[{role:'use',kind:'placement',id:1,incarnation:mark}]},
    result:{ok:true,schema:'geometry-space-preview/1',space:pkg,volume:null,clearance:null,walls:null,source_sha256:hash,diagnostics:[],
      summary:{source_placement:null,source_z:null,bottom:null,top:null,generated_faces:[],missing:['開放空間'],face_count:1,
        closed:false,volume_mm3:null,clearance_mm3:null,wall_volume_mm3:null,wall_diagnostics:[]}}};
}

test('R362_STACK_ARCHIVE preserves model roots, evidence v2 and main reader admission together', async () => {
  const identified = model();
  assert.doesNotThrow(() => P.validateSpaceModel(identified), 'R362_STACK_MODEL_IDENTITY_ADMISSION');
  const evidence = {schema:'geometry-evidence-links/2',links:[]};
  const manifest = {format:P.FORMAT,projectId:'stack-project',name:'stack',sceneHash:hash,sources:[],faces:[],models:[identified],
    featureAttachments:{schema:P.Features.SCHEMA,records:[P.Features.record('evidence-links',evidence)]}};
  let opened;
  await assert.doesNotReject(async () => {
    opened = await P.unpack(await P.pack(scene, manifest, new Map(), zip), zip);
  }, 'R362_STACK_ARCHIVE_ADMISSION');
  assert.equal(opened.manifest.format, 'geometry-canvas/12');
  assert.deepEqual(opened.manifest.models[0].sourceIdentity, identified.sourceIdentity, 'R362_STACK_MODEL_PINS_ROUNDTRIP');
  assert.equal(opened.manifest.models[0].input.base_scene, scene);
  assert.deepEqual(P.Features.evidenceLinks(opened.manifest.featureAttachments), evidence, 'R362_STACK_EVIDENCE_V2_ROUNDTRIP');
  const required = ['identity-ledger/1','room-candidate-drafts/1','grid-card-draft/1','geometry-evidence-links/2'];
  const available = P.readerCapabilities(['identity-ledger/1']);
  for (const capability of required)
    assert.ok(available.includes(capability), 'R362_STACK_PARENT_READER_CAPABILITY:' + capability);
  assert.doesNotThrow(() => P.assertProjectCapabilities({requiredCapabilities:required}, available), 'R362_STACK_PARENT_CAPABILITY_ADMISSION');
  const invalid = structuredClone(identified);
  invalid.sourceIdentity.roots[0].id = 9;
  assert.throws(() => P.validateSpaceModel(invalid), /根集合不一致/, 'R362_STACK_MODEL_ROOT_VALIDATION');
});
