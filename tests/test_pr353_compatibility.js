'use strict';
/* Real ZIP/current + fixed 405f8c5 reader contracts. The staging fixture uses
 * production ReferenceWorkspace with a minimal DOM; it is not browser/native E2E.
 */
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const P=require('../geometry-web/project-store.js'),F=P.Features;
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const L=require('./pr353_legacy_reader.js');
const old=L.loadLegacyReader(),CAP='grid-card-draft/1';
const copy=structuredClone;
const ordinary='grid-system 4 name-hex 47 main-along none u repeat -5 600 v repeat 7 400\n';
const perField='requires parameters/1\nparameters begin\nparameters end\ngrid-system 4 name-hex 47 main-along none u repeat -5 param:10:3 v repeat 7 param:10:8\n';
const committed='requires parameters/1\nrequires grid-card-reference/1\nparameters begin\nparameters end\ngrid-system 4 name-hex 47 main-along none card-reference 10 3 8 u repeat -5 card v repeat 7 card\n';
const nativeRule=committed+'requires grid-subdivision-rules/1\ngrid-source-rule 4 key 7 name-hex 72756c65 selector cell -2 1 divide 3 2\ngrid-source-rule-highwater 4 next 11\n';
function draft({card=true,rules=false,id='raw-card',lost=false,edit=false}={}){
  const rawForm=Object.fromEntries(F.sourceFields.map(key=>[key,'']));
  Object.assign(rawForm,{igName:'  未確認 <&>  ',igMainAlong:'none',igUSource:'repeat',igVSource:'repeat',igUStep:' 0600 ',igVStep:' 0400 ',igUPhase:' - ',igVPhase:' 007 '});
  if(card)Object.assign(rawForm,{igCard:'10',igCardU:'3',igCardV:'8'});
  const inputRefs=[{kind:'parameter-field',parameterId:10,fieldId:3,fingerprint:'a'.repeat(64)},
    {kind:'parameter-field',parameterId:10,fieldId:8,fingerprint:'b'.repeat(64)}];
  if(lost)inputRefs[1].lost=true;
  return {schema:rules?F.GRID_RULE_SCHEMA:F.GRID_SCHEMA,draftId:id,kind:'source',intent:rules||edit?'edit':'create',
    baseRef:rules||edit?{kind:'grid-system',id:4,fingerprint:'c'.repeat(64)}:null,inputRefs,rawForm,
    ...(rules?{ruleDraft:{intent:'create',ruleKey:null,rawForm:{name:' source rule ',selector:'cell',cellI:' 9007199254740993 ',cellJ:' - ',divisionsU:' 3 ',divisionsV:''}}}:{})};
}
function envelope(value){return {schema:F.SCHEMA,records:[{kind:F.GRID_KIND,schema:value.schema,value}]};}
function manifest(value){return {format:P.FORMAT,projectId:'r353-compat-project',name:'compatibility',sceneHash:'0'.repeat(64),sources:[],faces:[],...(value?{featureAttachments:envelope(value)}:{})};}
const pack=(scene,value,reader=P)=>reader.pack(scene,manifest(value),new Map(),zip);
const reopen=async(scene,value,reader=P)=>P.unpack(await pack(scene,value,reader),zip);
const caps=value=>value.manifest.requiredCapabilities||[];
function rewrite(bytes,fn){const files=zip.unzipSync(bytes),m=JSON.parse(zip.strFromU8(files['manifest.json']));fn(m);files['manifest.json']=zip.strToU8(JSON.stringify(m));return zip.zipSync(files);}
const draftValues=opened=>F.gridDrafts(opened.manifest.featureAttachments.records.find(record=>record.kind===F.GRID_KIND).value);

test('R35307_RAW_CAPABILITY presence includes empty and unknown mapping without native claims',async()=>{
  assert.equal(F.GRID_CARD_CAPABILITY,CAP);
  for(const mapping of [{igCard:'10',igCardU:'3',igCardV:'8'},{igCard:'',igCardU:'',igCardV:''},{igCard:'missing',igCardU:' 999 ',igCardV:'?'}]){
    const raw=draft();Object.assign(raw.rawForm,mapping);
    const before=copy(raw),opened=await reopen('reset\n',raw);
    assert.ok(caps(opened).includes(CAP),'raw-card capability must be derived from fields, not truthiness');
    assert.equal(caps(opened).includes(P.CARD_CAPABILITY),false,'raw is not a committed native card');
    assert.equal(opened.manifest.format,P.FEATURE_FORMAT);
    assert.deepEqual(opened.manifest.featureAttachments,envelope(before));
    P.assertProjectCapabilities(opened.manifest,P.readerCapabilities([]));
    assert.throws(()=>P.assertProjectCapabilities(opened.manifest,P.readerCapabilities([]).filter(cap=>cap!==CAP)));
    assert.equal(P.nativeReaderCapabilities([CAP]).includes(CAP),false,'editor capability is not a native claim');
    assert.throws(()=>P.validateProjectCapabilities([CAP]));
  }
});
test('R35307_LEGACY_EXACT fixed old writer /1 /2 collection and direct/ParameterRef remain unchanged',async()=>{
  for(const scene of [ordinary,perField])for(const rules of [false,true]){
    const raw=draft({card:false,rules}),before=copy(raw),bytes=await pack(scene,raw,old);
    const oldOpened=await old.unpack(bytes,zip),opened=await P.unpack(bytes,zip);
    assert.deepEqual(opened.manifest,oldOpened.manifest,'current reader cannot migrate old manifest');
    assert.equal(opened.scene,scene);assert.deepEqual(draftValues(opened).drafts,[before]);
    assert.equal(caps(opened).includes(CAP),false);
    assert.equal(caps(opened).includes(P.CARD_CAPABILITY),false,'same-card fields do not synthesize card semantics');
    const again=await P.unpack(await P.pack(opened.scene,opened.manifest,opened.sources,zip),zip);
    assert.deepEqual(again.manifest,oldOpened.manifest,'resave preserves historical draft schema and pins');
  }
  const collection={schema:F.GRID_DRAFTS_SCHEMA,drafts:[draft({card:false,id:'one'}),draft({card:false,rules:true,id:'two'})],orphans:[]};
  const bytes=await pack(ordinary,collection,old),opened=await P.unpack(bytes,zip);
  assert.equal(opened.manifest.format,P.GRID_DRAFTS_FORMAT);assert.deepEqual(draftValues(opened),{drafts:collection.drafts,orphans:[]});
  assert.equal(caps(opened).includes(CAP),false);
});
test('R35307_NEW_RAW_ROUNDTRIP card plus source-rule raw strings and missing pins remain exact',async()=>{
  for(const rules of [false,true]){
    const raw=draft({rules});raw.inputRefs=[];raw.rawForm.igCardV=' unknown ';
    const before=copy(raw),opened=await reopen(rules?nativeRule:perField,raw);
    assert.equal(opened.scene,rules?nativeRule:perField);
    assert.deepEqual(draftValues(opened).drafts,[before]);
    assert.ok(caps(opened).includes(CAP));
    const second=await P.unpack(await P.pack(opened.scene,opened.manifest,opened.sources,zip),zip);
    assert.deepEqual(second.manifest,opened.manifest);assert.deepEqual(raw,before,'writer does not repair caller raw');
  }
});
test('R35307_DECLARATION_REJECTION stripped false and unknown raw capabilities fail before admission',async()=>{
  const bytes=await pack('reset\n',draft());
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.requiredCapabilities=m.requiredCapabilities.filter(cap=>cap!==CAP)),zip),/能力/);
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.requiredCapabilities=m.requiredCapabilities.map(cap=>cap===CAP?'grid-card-draft/999':cap)),zip),/能力/);
  const noRaw=await pack(ordinary,null);
  await assert.rejects(()=>P.unpack(rewrite(noRaw,m=>{m.format=P.FEATURE_FORMAT;m.models=[];m.faceProjections=[];m.requiredCapabilities=[CAP];}),zip));
  const legacy=await pack(ordinary,draft({card:false}));
  await assert.rejects(()=>P.unpack(rewrite(legacy,m=>m.requiredCapabilities.push(CAP)),zip),/能力/);
  for(const field of ['igCard','igCardU','igCardV']){
    await assert.rejects(()=>P.unpack(rewrite(bytes,m=>delete m.featureAttachments.records[0].value.rawForm[field]),zip),/欄位/);
  }
});
test('R35307_MATRIX committed raw-only mixed and mixed collections require only their actual semantics',async()=>{
  const cases=[
    {name:'committed',scene:committed,raw:null,format:P.CARD_FORMAT,required:[P.CARD_CAPABILITY,P.PARAMETER_CAPABILITY]},
    {name:'raw-only',scene:'reset\n',raw:draft(),format:P.FEATURE_FORMAT,required:[CAP,F.GRID_SCHEMA]},
    {name:'raw-rule-only',scene:ordinary,raw:draft({rules:true}),format:P.GRID_RULE_FORMAT,required:[CAP,F.GRID_RULE_SCHEMA]},
    {name:'mixed',scene:committed,raw:draft(),format:P.CARD_FORMAT,required:[CAP,P.CARD_CAPABILITY,F.GRID_SCHEMA,P.PARAMETER_CAPABILITY]},
    {name:'mixed-rules',scene:nativeRule,raw:draft({rules:true}),format:P.CARD_FORMAT,required:[CAP,P.CARD_CAPABILITY,F.GRID_RULE_SCHEMA,P.SUBDIVISION_CAPABILITY,P.PARAMETER_CAPABILITY]},
    {name:'raw-collection',scene:'reset\n',raw:{schema:F.GRID_DRAFTS_SCHEMA,drafts:[draft({card:false,id:'a-old'}),draft({id:'b-new',rules:true})],orphans:[]},format:P.GRID_DRAFTS_FORMAT,required:[CAP,F.GRID_SCHEMA,F.GRID_RULE_SCHEMA,F.GRID_DRAFTS_SCHEMA]}
  ];
  for(const c of cases){
    const opened=await reopen(c.scene,c.raw);
    assert.equal(opened.manifest.format,c.format,c.name);
    assert.deepEqual(caps(opened),c.required.sort(),c.name);
    assert.equal(opened.scene,c.scene,c.name);
    if(c.raw)assert.deepEqual(opened.manifest.featureAttachments,envelope(c.raw),c.name);
  }
});
test('R35307_NESTED_RAW scenario-only raw propagates capability to root and cannot strip it',async()=>{
  const S=require('../geometry-web/scenario-snapshots.js'),raw=draft({rules:true}),leaf=await reopen(ordinary,raw);
  const snapshots=S.create({project:P,featureAttachments:{validate:F.validate,references:F.sourceIds},
    verifyProject:async()=>({ok:true,capabilities:[],final_objects:{boundaries:[],placements:[]},objects:[]})});
  await snapshots.capture(leaf,{scenarioId:'raw-snapshot',label:'raw-snapshot'});
  const root={...manifest(null),scenarioCatalog:{schema:S.SCHEMA,scenarios:snapshots.list()}};
  const bytes=await P.pack('reset\n',root,new Map(),zip),opened=await P.unpack(bytes,zip);
  assert.ok(caps(opened).includes(CAP),'root must advertise nested raw');
  assert.equal(caps(opened).includes(P.CARD_CAPABILITY),false);
  assert.deepEqual(opened.manifest.scenarioCatalog.scenarios[0].snapshot.projectManifest,leaf.manifest);
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.requiredCapabilities=m.requiredCapabilities.filter(cap=>cap!==CAP)),zip),/能力/);
});
function workspace(reader){
  const elements=new Map(),calls=[],statuses=[];
  const element=id=>{
    if(!elements.has(id))elements.set(id,{textContent:'',innerHTML:'',dataset:{},style:{},value:'',hidden:false,
      classList:{toggle(){}},setAttribute(){},removeAttribute(){},replaceChildren(){},append(){},prepend(){},
      addEventListener(){},querySelector:()=>null,querySelectorAll:()=>[],parentElement:{clientWidth:800,clientHeight:600}});
    return elements.get(id);
  };
  const env={GeometryProject:reader,fflate:zip,crypto,structuredClone,JSON,TextEncoder,TextDecoder,Uint8Array,Map,Set,WeakMap,console,AbortSignal,
    requestAnimationFrame:()=>1,CustomEvent:class{},ResizeObserver:class{observe(){}},File,Blob,
    pageRuntimeVersion:'r353-compat-vm',checkApiSession(){},
    fetch:async(url)=>{calls.push(url);throw Error('Unexpected upload/fetch after archive refusal: '+url);},
    window:{dispatchEvent(){},addEventListener(){},confirm:()=>false},
    document:{getElementById:element,querySelectorAll:()=>[],querySelector:()=>null,addEventListener(){},createElement:tag=>element(tag)},
    oc:{busy:false,faces:[],bmap:{},edit:null},fe:{feats:{}},connection:{phase:'ready',session:'r353-fixed-session'},
    api:async command=>{calls.push(command);throw Error('Unexpected native command after archive refusal: '+command);},
    setStatus:s=>statuses.push(s),toast:s=>statuses.push(s),drawFaceEditor(){},renderFaceInspector(){},innerWidth:1280};
  const file=path.resolve(__dirname,'../geometry-web/reference-workspace.js');
  vm.runInNewContext(fs.readFileSync(file,'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',env,{filename:file});
  const w=env.workspace,c=w.context();
  c.name='Existing project must survive';c.dirty=true;c.provenance.kind='new';
  c.featureAttachments=[old.Features.record(old.Features.GRID_KIND,draft({card:false,id:'existing'}))];
  w.history.push(w.history.snapshot(),'local','Existing undo entry');
  const initial={context:w.context(),frame:w.history.frame,state:copy(w.getProjectState()),
    snapshot:JSON.stringify(w.history.snapshot()),undo:w.history.undo.length,redo:w.history.redo.length,raw:JSON.stringify(w.readGridDrafts())};
  return {w,calls,statuses,initial};
}
test('R35307_OLD_READER_ATOMIC_REJECT actual fixed reader refuses raw and mixed before native context/history writes',async()=>{
  const committedOnly=await pack(committed,null),oldCommitted=await old.unpack(committedOnly,zip);
  assert.equal(oldCommitted.scene,committed,'fixed pre-PR353 reader still supports committed D64');
  assert.equal((oldCommitted.manifest.requiredCapabilities||[]).includes(CAP),false);
  for(const scene of ['reset\n',committed]){
    const bytes=await pack(scene,draft());
    await assert.rejects(()=>old.unpack(bytes,zip),/版本|能力|欄位/);
    const {w,calls,initial}=workspace(old);
    await assert.rejects(()=>w.importBytes(bytes,'new-card.gcanvas'),/版本|能力|欄位/);
    assert.equal(w.context(),initial.context);assert.equal(w.history.frame,initial.frame);
    assert.deepEqual(copy(w.getProjectState()),initial.state);
    assert.equal(JSON.stringify(w.history.snapshot()),initial.snapshot);
    assert.equal(w.history.undo.length,initial.undo);assert.equal(w.history.redo.length,initial.redo);
    assert.equal(JSON.stringify(w.readGridDrafts()),initial.raw);
    assert.deepEqual(calls,[],'no native or upload request precedes archive admission');
  }
});
test('R35307_CURRENT_READER_ATOMIC_REJECT missing editor capability keeps existing project and history',async()=>{
  const bytes=await pack('reset\n',draft()),stripped=rewrite(bytes,m=>m.requiredCapabilities=m.requiredCapabilities.filter(cap=>cap!==CAP));
  const {w,calls,initial}=workspace(P);
  await assert.rejects(()=>w.importBytes(stripped,'stripped-card.gcanvas'),/能力/);
  assert.equal(w.context(),initial.context);assert.equal(w.history.frame,initial.frame);
  assert.equal(JSON.stringify(w.history.snapshot()),initial.snapshot);assert.deepEqual(copy(w.getProjectState()),initial.state);
  assert.deepEqual(calls,[]);
});
test('R35307_HISTORICAL_PINS all fingerprints lost flags and orphan status survive repeated archive reads',async()=>{
  const first=draft({lost:true,edit:true}),second=draft({card:false,rules:true,id:'legacy-rule'});
  second.baseRef.id=5;
  const value={schema:F.GRID_DRAFTS_SCHEMA,drafts:[first,second],orphans:[first.draftId]},before=copy(value);
  const opened=await reopen(committed,value),again=await P.unpack(await P.pack(opened.scene,opened.manifest,opened.sources,zip),zip);
  const expected={drafts:[...before.drafts].sort((a,b)=>a.draftId.localeCompare(b.draftId)),orphans:before.orphans};
  assert.deepEqual(draftValues(opened),expected);assert.deepEqual(draftValues(again),expected);
  assert.deepEqual(value,before);assert.equal(first.inputRefs[1].fingerprint,'b'.repeat(64));
  const source={id:4,mode:'infinite',name:'G',mainAlong:null,uDefinition:{source:'repeat',step:600,phase:-5},vDefinition:{source:'repeat',step:400,phase:7},rules:[],nextRuleKey:1};
  assert.equal(F.gridSourceKey(source,true),old.Features.gridSourceKey(source,true));
  assert.equal(F.gridSourceKey(source),old.Features.gridSourceKey(source));
});
test('R35309_GEO219_SOURCE_REDUCTION one instruction paragraph replaces two without removing information',()=>{
  const source=fs.readFileSync(path.resolve(__dirname,'../geometry-web/grid-system-workspace.js'),'utf8');
  assert.equal(source.includes('class="ig-def-hint"'),false,'independent permanent paragraph removed');
  assert.equal((source.match(/id="igViewNote"/g)||[]).length,1,'reuse the existing instruction paragraph');
  assert.ok(source.includes('拖曳平移 · 滾輪縮放 · 點格子選取；點定義圖的尺寸或卡片標題可定位欄位。'));
});
