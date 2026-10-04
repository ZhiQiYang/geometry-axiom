/* Compatibility test: inject the shared owner's actual PR104 validator, never copy it into main. */
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const path=require('node:path');
const {spawnSync}=require('node:child_process');
const S=require('../geometry-web/scenario-snapshots.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const ownerModule=process.env.GEOMETRY_SCENARIO_PROJECT_MODULE;
test('approved GridDraft raw bytes close with the injected real owner validator and isolated native verifier',
  {skip:ownerModule?false:'Inject PR104 project-store.js using GEOMETRY_SCENARIO_PROJECT_MODULE; approved GridDraft saving is not on this main yet.'},async()=>{
    const P=require(ownerModule),F=require(path.join(path.dirname(ownerModule),'feature-attachments.js'));
    const rawForm=Object.fromEntries(F.bindingFields.map(k=>[k,'']));
    Object.assign(rawForm,{igSystem:'0',igCellI:'-',igCellJ:' 001 ',igAnchorUN:'1',igAnchorUD:'0',igAnchorVN:' 1e ',igAnchorVD:'9223372036854775808'});
    const draft={schema:F.GRID_SCHEMA,draftId:'raw-draft',kind:'binding',intent:'create',baseRef:null,inputRefs:[],rawForm};
    const featureAttachments={schema:F.SCHEMA,records:[F.record(F.GRID_KIND,draft)]};
    const scene='boundary 1 outline 0,0 100,0 100,100 0,100\nplacement 1 on boundary 1 origin 0 0 0 u +x v +y\n';
    const manifest={format:P.FEATURE_FORMAT,projectId:'original',name:'raw grid',sceneHash:await P.sha(new TextEncoder().encode(scene)),
      sources:[],faces:[],models:[],faceProjections:[],requiredCapabilities:[F.GRID_SCHEMA],featureAttachments};
    let nativeCalls=0;
    const verifyProject=async data=>{
      nativeCalls++;
      // Only this already validated editorial capability is removed for the engine-only adapter.
      data.manifest.requiredCapabilities=data.manifest.requiredCapabilities.filter(c=>c!==F.GRID_SCHEMA);
      const result=spawnSync(process.env.PYTHON||'python3',['geometry-web/scenario_verify.py'],{cwd:path.resolve(__dirname,'..'),
        input:JSON.stringify(data),encoding:'utf8',timeout:90000,maxBuffer:16*1024*1024});
      assert.equal(result.status,0,result.stdout+result.stderr);return JSON.parse(result.stdout);
    };
    const adapter={validate:F.validate,references:envelope=>{F.validate(envelope);return [];},
      objects:envelope=>envelope.records.map(r=>({kind:r.kind,id:r.value.draftId,version:null}))};
    const options={project:P,featureAttachments:adapter,verifyProject};
    const archive=S.create(options);
    await archive.capture({manifest,scene,sources:new Map()},{scenarioId:'A',label:'A'});await archive.fork('A',{scenarioId:'B',label:'B'});
    const b=archive.project('B');b.manifest.featureAttachments.records[0].value.rawForm.igCellI='changed invalid';await archive.replace('B',b);
    assert.deepEqual(archive.project('A').manifest.featureAttachments.records[0].value.rawForm,rawForm);
    const reopened=S.create(options);await reopened.unpack(await archive.pack(zip),zip);
    assert.deepEqual(reopened.project('A').manifest.featureAttachments,featureAttachments);
    assert.equal(reopened.project('B').manifest.featureAttachments.records[0].value.rawForm.igCellI,'changed invalid');
    assert.ok(reopened.list()[1].originMapping.some(v=>v.to.kind==='grid-draft'));assert.equal(nativeCalls,5);
    const unsupported=S.create({verifyProject});
    await assert.rejects(unsupported.capture({manifest,scene,sources:new Map()},{scenarioId:'A',label:'A'}),e=>e.code==='MISSING_CAPABILITY');
    const unknown=structuredClone(manifest);unknown.featureAttachments.records[0].kind='unfinished-unknown';
    await assert.rejects(archive.capture({manifest:unknown,scene,sources:new Map()},{scenarioId:'unknown',label:'unknown'}));
    const stripped=structuredClone(manifest);stripped.requiredCapabilities=[];
    await assert.rejects(archive.capture({manifest:stripped,scene,sources:new Map()},{scenarioId:'strip',label:'strip'}));
    assert.equal(archive.stats().scenarios,2);
  });
