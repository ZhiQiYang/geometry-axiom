/* PR110 review regressions against the real project reader and disposable CLI.
 * GEOMETRY_TEST_BRIDGE=<isolated-test-directory> \
 * GEOMETRY_MODEL_BASE=<isolated-test-directory> \
 * node --test tests/test_scenario_review_native.js
 * No live server, /upload, app, history or source files are changed.
 */
'use strict';
const {test,after}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const {execFile}=require('node:child_process');
const P=require('../geometry-web/project-store.js');
const S=require('../geometry-web/scenario-snapshots.js');
const D=require('../geometry-web/scenario-diff.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const root=path.resolve(__dirname,'..');
const enc=new TextEncoder(),dec=new TextDecoder('utf-8',{fatal:true});
const copy=v=>structuredClone(v);
const basicScene='spec stable 600\nboundary 1 outline 0,0 600,0 600,400 0,400\n'+
  'placement 0 on boundary 1 origin 0 0 2500 u +x v +y\n';
let nativeCalls=0;
after(()=>console.log('Actual isolated native CLI calls: '+nativeCalls));

async function native(data) {
  nativeCalls++;
  const payload=JSON.stringify(data);
  // execFile passes stdin through a separate, explicitly bounded child pipe.
  const promise=new Promise((resolve,reject)=>{
    const child=execFile(process.env.PYTHON||'python3',[path.join(root,'geometry-web/scenario_verify.py')],
      {cwd:root,env:process.env,timeout:90000,maxBuffer:16*1024*1024,encoding:'utf8'},(error,stdout,stderr)=>{
        let receipt;try {receipt=JSON.parse(stdout);} catch(parseError) {
          reject(new Error('Native verifier returned no JSON: '+(stderr||parseError.message)));return;
        }
        if(error||receipt.ok!==true) {
          reject(Object.assign(new Error(receipt.message||stderr||'Native verification failed'),{code:receipt.code,receipt}));return;
        }
        resolve(receipt);
      });
    child.stdin.on('error',reject);child.stdin.end(payload);
  });
  return promise;
}

async function fullBoundaryPins(scene,ids) {
  const bridge=process.env.GEOMETRY_TEST_BRIDGE;
  assert.ok(bridge,'A fresh GEOMETRY_TEST_BRIDGE is required for the isolated full-boundary oracle');
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'scenario-pin-oracle-'));
  try {
    const source=path.join(directory,'oracle.scene');fs.writeFileSync(source,scene,'utf8');
    // Independent actual native World, not scenario_verify or load-prepare.
    const commands=['loadfile '+source,...ids.map(id=>'boundary '+id)].join('\n')+'\n';
    const stdout=await new Promise((resolve,reject)=>{
      const child=execFile(bridge,[],{cwd:directory,env:process.env,timeout:10000,maxBuffer:2*1024*1024,encoding:'utf8'},
        (error,output,stderr)=>error?reject(new Error('Native boundary oracle exited abnormally: '+(stderr||error.message))):resolve(output));
      child.stdin.on('error',reject);child.stdin.end(commands);
    });
    const rows=stdout.trimEnd().split(/\r?\n/).map(row=>JSON.parse(row));
    assert.equal(rows.length,ids.length+1);assert.equal(rows[0].ok,true);
    return rows.slice(1).map((row,index)=>{
      assert.equal(row.ok,true);assert.equal(row.id,ids[index]);
      assert.equal(typeof row.geometryFingerprint,'string');assert.equal(row.geometryFingerprint.length,64);
      assert.match(row.geometryFingerprint,/^[0-9a-f]{64}$/);
      return {id:row.id,geometryFingerprint:row.geometryFingerprint};
    });
  } finally {fs.rmSync(directory,{recursive:true,force:true});}
}

function observedArchive() {
  let calls=0;
  const archive=S.create({verifyProject:async value=>{calls++;return native(value);}});
  return {archive,calls:()=>calls};
}

async function project(scene=basicScene,format=P.FORMAT,fields={}) {
  const manifest={format,projectId:'native-review-project',name:'native review',
    sceneHash:await P.sha(enc.encode(scene)),sources:[],faces:[],...copy(fields)};
  if(format!==P.FORMAT)manifest.models??=[];
  if(![P.FORMAT,P.MODEL_FORMAT].includes(format))manifest.faceProjections??=[];
  if([P.ENGINEERING_FORMAT,P.PARAMETER_FORMAT,P.ASSEMBLY_FORMAT,P.GENERATION_FORMAT,P.OUTLINE_FORMAT].includes(format))
    manifest.requiredCapabilities??=[];
  P.validate(manifest);
  return {manifest,scene,sources:new Map()};
}

function example(name) {
  const files=zip.unzipSync(new Uint8Array(fs.readFileSync(path.join(root,'geometry-web/examples',name+'.gcanvas'))));
  const manifest=JSON.parse(dec.decode(files['manifest.json'])),scene=dec.decode(files['world.scene']);
  const sources=new Map(manifest.sources.map(s=>[s.id,Uint8Array.from(files[s.path])]));
  P.validate(manifest);
  return {manifest,scene,sources};
}

function portableZip(input) {
  // Keep exact supplied format/capability bytes. P.pack upgrades the format,
  // which would conceal the downgraded-reader regression this test must catch.
  const files={'manifest.json':enc.encode(JSON.stringify(input.manifest)),
    'world.scene':enc.encode(input.scene)};
  for(const meta of input.manifest.sources)files[meta.path]=Uint8Array.from(input.sources.get(meta.id));
  return zip.zipSync(files,{level:0});
}

function state(archive) {
  return {records:archive.list(),stats:archive.stats(),
    projects:archive.list().map(record=>archive.project(record.scenarioId))};
}

function parameterScene() {
  const record=(kind,value)=>'parameters '+kind+' '+Buffer.from(JSON.stringify(value)).toString('base64')+'\n';
  return 'requires parameters/1\nparameters begin\n'+
    record('card',{id:1,name:'width',nextFieldId:2})+
    record('field',{parameterId:1,id:1,name:'width',type:0,
      expression:{op:'literal',num:'600',den:'1',unit:'mm'}})+
    'parameters end\n'+basicScene;
}

async function outlineProject() {
  const input=await project(basicScene,P.OUTLINE_FORMAT);
  const bytes=new Uint8Array(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j9ZkAAAAASUVORK5CYII=','base64'));
  const hash=await P.sha(bytes),page={id:'review-page',sourceId:hash,page:1,imgW:1,imgH:1,crop:[0,0,1,1],
    mmPerPx:100,x:0,y:0,rot:0,opacity:1,locked:true,reviewRequired:false,records:[],
    calibration:{points:[[0,0],[1,0]],distanceMm:100,inputValue:100,inputUnit:'mm'}};
  input.manifest.sources=[{id:hash,hash,name:'original.png',type:'image/png',size:bytes.length,path:'sources/'+hash}];
  input.manifest.faces=[{bid:1,activePageId:page.id,pages:[page]}];
  input.manifest.reconstructionReviews=[{bid:1,pageId:page.id,basis:P.reviewBasis(page),
    geometry:P.outlineFingerprint([{verts:[[0,0],[600,0],[600,400],[0,400]],fixity:[1,1,1,1]}]),
    method:'manual',warnings:[],confirmedAt:'2026-10-04T00:00:00.000Z'}];
  input.sources.set(hash,bytes);P.validate(input.manifest);return input;
}

test('all currently supported portable formats seal with actual native/model verification and exact reader validation',async t=>{
  const samples=example('space-model-v1'),plain=copy(samples.manifest.models.find(m=>m.result.schema==='geometry-space-preview/1'));
  const projected=copy(plain),timbers=copy(samples.manifest.models.find(m=>m.result.schema==='geometry-space-preview/2'));
  delete plain.source.projection;
  const engineering=example('engineering-spec-v1'),assembly=example('assembly-rules-v1'),generation=example('assembly-generation-v1');
  delete assembly.manifest.assemblyDrafts;
  const fixtures=[await project(),await project(plain.input.base_scene,P.MODEL_FORMAT,{models:[plain]}),
    await project(projected.input.base_scene,P.PROJECTION_FORMAT,{models:[projected]}),
    await project(timbers.input.base_scene,P.TIMBER_FORMAT,{models:[timbers]}),engineering,
    await project(parameterScene(),P.PARAMETER_FORMAT,{requiredCapabilities:[P.PARAMETER_CAPABILITY]}),
    assembly,generation,await outlineProject()];
  for(const input of fixtures)await t.test(input.manifest.format,async()=>{
    const reader=await P.unpack(portableZip(input),zip);
    assert.equal(reader.manifest.format,input.manifest.format);
    assert.equal(reader.scene,input.scene);
    const {archive,calls}=observedArchive();
    await archive.capture(input,{scenarioId:'A',label:'formal supported format'});
    assert.equal(calls(),1,'A real isolated CLI receipt is mandatory');
    assert.deepEqual(archive.project('A'),input,'Original packages, manifest and asset bytes must remain exact');
    const reopened=observedArchive();await reopened.archive.unpack(await archive.pack(zip),zip);
    assert.equal(reopened.calls(),1);assert.deepEqual(reopened.archive.project('A'),input);
  });
});

test('kept parameter/assembly/generation capabilities cannot mask a scene-dependent format5 downgrade',async t=>{
  const parameter=await project(parameterScene(),P.PARAMETER_FORMAT,{requiredCapabilities:[P.PARAMETER_CAPABILITY]});
  const assembly=example('assembly-rules-v1'),generation=example('assembly-generation-v1');
  delete assembly.manifest.assemblyDrafts;
  for(const original of [parameter,assembly,generation])await t.test(original.manifest.format+' to /5',async()=>{
    const downgraded=copy(original);downgraded.manifest.format=P.ENGINEERING_FORMAT;
    assert.doesNotThrow(()=>P.validate(downgraded.manifest),
      'This regression requires a downgrade that still passes the manifest-only structure check');
    const evidence=await native({manifest:downgraded.manifest,scene:downgraded.scene});
    assert.equal(evidence.ok,true,'Engine-only verification intentionally cannot establish portable reader format');
    assert.ok(evidence.requiredCapabilities.includes(original.manifest.requiredCapabilities.find(c=>
      [P.PARAMETER_CAPABILITY,P.ASSEMBLY_CAPABILITY,P.GENERATION_CAPABILITY].includes(c))));
    await assert.rejects(()=>P.unpack(portableZip(downgraded),zip),/版|能力|格式/);
    const {archive,calls}=observedArchive();await archive.capture(original,{scenarioId:'keep',label:'keep'});
    const before=state(archive),count=calls();
    await assert.rejects(()=>archive.capture(downgraded,{scenarioId:'bad',label:'downgraded'}),{code:'FORMAT'});
    await assert.rejects(()=>archive.replace('keep',downgraded),{code:'FORMAT'});
    assert.equal(calls(),count,'Portable format failure must be resolved before trusting native evidence');
    assert.deepEqual(state(archive),before,'A rejected downgrade must leave all records and bytes intact');
    // Rehash the altered private archive honestly: rejecting its CRC or closure
    // hash would conceal a missing scene-dependent portable-format guard.
    const files=zip.unzipSync(await archive.pack(zip)),record=copy(before.records[0]);
    record.snapshot.projectManifest.format=P.ENGINEERING_FORMAT;
    const {closureHash,...content}=record;record.closureHash=await P.sha(enc.encode(S.canonical(content)));
    files['scenarios/keep/manifest.json']=enc.encode(JSON.stringify(record.snapshot.projectManifest));
    const descriptor=JSON.parse(dec.decode(files['scenarios.json']));
    descriptor.scenarios[0].closureHash=record.closureHash;
    files['scenarios.json']=enc.encode(JSON.stringify(descriptor));
    await assert.rejects(()=>archive.unpack(zip.zipSync(files,{level:0}),zip),{code:'FORMAT'});
    assert.equal(calls(),count,'A self-consistent ZIP downgrade must fail before native verification');
    assert.deepEqual(state(archive),before,'A rejected archive downgrade must preserve the retained complete project');
  });
});

test('real reset and delete/recreate of the same native IDs erase copy origins before diff and ZIP reopen',async t=>{
  const recreated=basicScene.replace('600,0 600,400','1200,0 1200,400');
  const scenes=[['reset',basicScene+'spec discarded_reset_probe 123\nreset\n'+recreated],['delete/recreate',basicScene+
    'delete placement 0\ndelete boundary 1\n'+recreated]];
  for(const [label,scene] of scenes)await t.test(label,async()=>{
    const initial=await project(),replacement=await project(scene);
    const oldNative=await native({manifest:initial.manifest,scene:initial.scene});
    const newNative=await native({manifest:replacement.manifest,scene:replacement.scene});
    assert.deepEqual(newNative.final_objects.boundaries,oldNative.final_objects.boundaries,'The final native IDs deliberately collide');
    assert.deepEqual(newNative.final_objects.placements,oldNative.final_objects.placements);
    assert.deepEqual(oldNative.final_objects.boundaries,[1]);
    assert.deepEqual(oldNative.final_objects.boundaryFingerprints,await fullBoundaryPins(initial.scene,[1]));
    assert.deepEqual(newNative.final_objects.boundaryFingerprints,await fullBoundaryPins(replacement.scene,[1]));
    assert.notEqual(newNative.final_objects.boundaryFingerprints[0].geometryFingerprint,
      oldNative.final_objects.boundaryFingerprints[0].geometryFingerprint,'Matching typed IDs cannot conceal different native geometry');
    assert.deepEqual(newNative.objects,oldNative.objects);
    assert.ok(!newNative.objects.some(object=>object.kind==='spec'&&object.id==='discarded_reset_probe'),
      'Reset must discard definitions loaded earlier in this same native parse');
    assert.notEqual(newNative.inventory.sourceFingerprint,oldNative.inventory.sourceFingerprint,
      'Real native definitions differ despite matching typed IDs');
    const {archive}=observedArchive();const A=await archive.capture(initial,{scenarioId:'A',label:'A'});
    const copied=await archive.fork('A',{scenarioId:'B',label:'B'});
    assert.equal(copied.originMapping.length,A.objects.length);
    assert.equal(D.compare(A,copied).originPairs.length,A.objects.length);
    const beforeA=archive.project('A');await archive.replace('B',replacement);
    const [afterA,B]=archive.list();assert.deepEqual(afterA,A);assert.deepEqual(archive.project('A'),beforeA);
    assert.deepEqual(B.originMapping,[],'Reappearing IDs do not provide native incarnation continuity');
    assert.deepEqual(B.objects,A.objects);assert.deepEqual(B.basis,copied.basis);
    const assertUnmatched=(a,b)=>{
      const diff=D.compare(a,b);assert.equal(diff.physicalIdentity,'unknown');
      assert.deepEqual(diff.originPairs,[]);assert.equal(diff.unmatched.before.length,a.objects.length);
      assert.equal(diff.unmatched.after.length,b.objects.length);assert.deepEqual(diff.geometry,{status:'not-evaluated'});
    };
    assertUnmatched(afterA,B);
    const reopened=observedArchive();await reopened.archive.unpack(await archive.pack(zip),zip);
    assert.deepEqual(reopened.archive.list(),archive.list());
    assert.deepEqual(reopened.archive.project('B'),replacement);
    assertUnmatched(...reopened.archive.list());
  });
});

test('foreign project replacement with identical valid native IDs is rejected atomically',async()=>{
  const initial=await outlineProject(),foreign=copy(initial);foreign.manifest.projectId='foreign-project';
  P.validate(foreign.manifest);const proof=await native({manifest:foreign.manifest,scene:foreign.scene});
  assert.equal(proof.ok,true);
  const {archive}=observedArchive();await archive.capture(initial,{scenarioId:'A',label:'A'});
  await archive.fork('A',{scenarioId:'B',label:'B'});const before=state(archive);
  // ZIP timestamps are packaging metadata. Advance them deterministically so
  // retention must be proved by every complete member's actual bytes.
  let clock=0;
  const timedZip={...zip,zip:(files,options,done)=>zip.zip(files,
    {...options,mtime:new Date(2000,0,1,0,0,clock++*2)},done)};
  const saved=await archive.pack(timedZip),savedMembers=zip.unzipSync(saved);
  assert.equal(before.stats.assets,1,'Retention includes a real original PNG byte pool');
  await assert.rejects(()=>archive.replace('B',foreign),{code:'PROJECT_IDENTITY'});
  assert.deepEqual(state(archive),before,'Project ID rejection must preserve A, B, basis, origins, pool and asset bytes');
  const repacked=await archive.pack(timedZip);
  assert.notDeepEqual(repacked,saved,'The test deliberately changes ZIP container timestamps');
  assert.deepEqual(zip.unzipSync(repacked),savedMembers,
    'Every descriptor, manifest, scene and original pool member must remain byte-for-byte unchanged');
  // A foreign manifest plus deliberately empty origins is still a cross-project
  // basis forgery, even after the attacker recomputes every relevant hash.
  const files=zip.unzipSync(saved),foreignB=copy(before.records.find(record=>record.scenarioId==='B'));
  foreignB.snapshot.projectManifest.projectId='foreign-project';foreignB.originMapping=[];
  const {closureHash,...content}=foreignB;foreignB.closureHash=await P.sha(enc.encode(S.canonical(content)));
  files['scenarios/B/manifest.json']=enc.encode(JSON.stringify(foreignB.snapshot.projectManifest));
  const descriptor=JSON.parse(dec.decode(files['scenarios.json']));
  Object.assign(descriptor.scenarios.find(record=>record.scenarioId==='B'),
    {originMapping:[],closureHash:foreignB.closureHash});
  files['scenarios.json']=enc.encode(JSON.stringify(descriptor));
  await assert.rejects(()=>archive.unpack(zip.zipSync(files,{level:0}),zip),{code:'PROJECT_IDENTITY'});
  assert.deepEqual(state(archive),before);
  assert.deepEqual(zip.unzipSync(await archive.pack(timedZip)),savedMembers,
    'Rehashed foreign-basis ZIP rejection must preserve every complete member and real asset pool byte');
  const reopened=observedArchive();await reopened.archive.unpack(await archive.pack(zip),zip);
  assert.deepEqual(reopened.archive.list(),before.records);
});
