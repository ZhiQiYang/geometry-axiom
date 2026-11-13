/* PR353 function-layer regressions. Run with Node 24:
 *   node tests/test_pr353_pin_regressions.js [repo-root] [R353-10|R353-11|R353-12]
 * P353_REPO_ROOT and P353_PIN_MUTATION are equivalent environment overrides.
 * The real grid handlers, ReferenceWorkspace, Features validator and ZIP writer
 * execute. DOM/event delivery and native objects responses are explicit doubles;
 * this is not browser/native E2E or an actual Save/Open session.
 */
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(process.env.P353_REPO_ROOT||process.env.GEOMETRY_PR353_ROOT||process.argv[2]||path.join(__dirname,'..'));
const mutation=process.env.P353_PIN_MUTATION||process.argv[3]||'';
const P=require(path.join(root,'geometry-web/project-store.js'));
const zip=require(path.join(root,'geometry-web/vendor/fflate/umd/index.js'));
const mutations={
  'R353-10':{file:'grid-system-workspace.js',before:'if(before&&!selectedIds.includes(id))continue;',after:'if(before&&!selectedIds.includes(id)){if(pin)nextPins.set(key,copy(pin));continue;}'},
  'R353-11':{file:'grid-system-workspace.js',before:'if(before&&!parameterUseKeys(form).has(before))s.inputPins.delete(before);',after:'if(before&&!parameterSelections(form).some(([,selected])=>selected===before))s.inputPins.delete(before);'},
  'R353-12':{file:'reference-workspace.js',before:'if(fields.length||card)continue;',after:'if(fields.length)continue;'}
};
assert.ok(!mutation||mutations[mutation],'Unknown pin mutation: '+mutation);
function product(file){
  let source=fs.readFileSync(path.join(root,'geometry-web',file),'utf8');
  const m=mutations[mutation];
  if(m?.file===file){assert.equal(source.split(m.before).length,2,'Mutation must match exactly once: '+mutation);source=source.replace(m.before,m.after);}
  return source;
}
const clone=value=>JSON.parse(JSON.stringify(value));
const pinKey=r=>'parameter-field:'+r.parameterId+':'+r.fieldId;
const row=(id,name)=>({id,card:{id,name,fields:[3,8,9].map((field,i)=>({id:field,name:'f'+field,type:'dimension',value:{num:String([600,1200,900][i]),den:'1'}}))}});
const objects=()=>({ok:true,parameters:[row(10,'A'),row(20,'B')],gridSystems:[],gridBindings:[],faces:[]});

function fixture(currentObjects){
  const elements=new Map(),prompts=[];
  let seam;
  class InputEvent {
    constructor(type,options={}){this.type=type;this.bubbles=!!options.bubbles;this.stopped=false;}
    stopImmediatePropagation(){this.stopped=true;}
    preventDefault(){this.prevented=true;}
  }
  const element=id=>{
    if(elements.has(id))return elements.get(id);
    const listeners=new Map(),classList={toggle(){},add(){},remove(){}};
    const node={id,value:'',textContent:'',dataset:{},style:{},classList,options:[],
      setAttribute(){},removeAttribute(){},replaceChildren(){},click(){},focus(){},append(){},prepend(){},
      close(){this.open=false;},showModal(){this.open=true;},closest:()=>({classList}),
      querySelector:()=>({}),querySelectorAll:()=>[],parentElement:{clientWidth:800,clientHeight:600},
      addEventListener(type,fn){if(!listeners.has(type))listeners.set(type,[]);listeners.get(type).push(fn);},
      dispatchEvent(event){
        event.target=this;
        if(seam?.selectParameterPin(state,event.target)===false){event.stopImmediatePropagation();event.preventDefault();}
        for(const fn of listeners.get(event.type)||[]){if(event.stopped)break;fn(event);}
        if(event.bubbles&&!event.stopped)element('dialog')['on'+event.type]?.(event);
        return !event.prevented;
      }};
    elements.set(id,node);return node;
  };
  let state;
  const env={GeometryProject:P,fflate:zip,crypto,structuredClone,JSON,TextEncoder,TextDecoder,Uint8Array,Map,Set,WeakMap,console,AbortSignal,
    Event:InputEvent,CustomEvent:class {},ResizeObserver:class {observe(){}},File,Blob,
    requestAnimationFrame:()=>1,pageRuntimeVersion:'pr353-function-probe',checkApiSession(){},
    window:{dispatchEvent(){},addEventListener(){},confirm:text=>{prompts.push(text);return false;}},
    document:{body:{append(){}},getElementById:element,querySelectorAll:()=>[],querySelector:()=>element('scroll'),addEventListener(){},createElement:element},
    oc:{busy:false,faces:[],bmap:{},edit:null,parameters:currentObjects.parameters,gridBindings:[]},fe:{feats:{}},connection:{phase:'ready'},
    api:async command=>{assert.equal(command,'objects','Only the objects boundary is doubled');return currentObjects;},
    setStatus(){},toast(){},drawFaceEditor(){},renderFaceInspector(){},innerWidth:1280};
  env.apiRequest=env.api;
  vm.runInNewContext(product('reference-workspace.js')+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  const w=env.workspace;env.ReferenceWorkspace=w;
  let source=product('grid-system-workspace.js');
  const start=source.indexOf("    if ($('igCard')) {"),end=source.indexOf('      for (const a of axes) for (const r of dialog.querySelectorAll',start);
  assert.ok(start>=0&&end>start,'Original card event handler block must be present');
  const handlers=source.slice(start+"    if ($('igCard')) {".length,end);
  const bubbleStart=source.indexOf('    dialog.oninput = dialog.onchange = event =>'),bubbleEnd=source.indexOf('    s.normalizedRaw=',bubbleStart);
  assert.ok(bubbleStart>=0&&bubbleEnd>bubbleStart,'Original input/change persistence handler must be present');
  // Extract the production handlers without rendering the complete editor.
  // Only decorative redraws and the persistence handler's presentation wrapper
  // are doubled; syncCard, cardPins, flush and every lost/pin guard remain real.
  const install='function installCardHandlers(s){const syncFields=()=>{},drawGrid=()=>{},syncDefinition=()=>{},syncDraftState=s=>{try{flush(s);}catch(error){s.rawError=error.message;}};'+handlers+source.slice(bubbleStart,bubbleEnd)+'}\n';
  source=source.replace('  window.InfiniteGridWorkspace={',install+'  window.InfiniteGridWorkspace={__pinProbe:{catalogPins,cardPins,selectParameterPin,rawValue,flush,validateDraftPins,installCardHandlers,setState:s=>{state=s;dialog.open=true;}},');
  vm.runInNewContext(source,env);
  seam=env.window.InfiniteGridWorkspace.__pinProbe;
  assert.ok(seam,'Original workspace export seam must be present');
  return {w,env,element,seam,prompts,
    start(d,pins){
      const token=w.getProjectState().contextToken;w.setGridDraft(d.draftId,d,token);
      for(const [id,value]of Object.entries(d.rawForm))element(id).value=value;
      state={context:w.context(),contextToken:token,mode:'source',draftId:d.draftId,draftSchema:d.schema,baseRef:null,restored:d,
        rawOverrides:new Map(),pins,inputPins:new Map(d.inputRefs.map(r=>[pinKey(r),clone(r)])),
        referenceSelections:new Map(Object.entries(d.rawForm).filter(([id,v])=>v&&id.endsWith('Source')&&!['igUSource','igVSource'].includes(id)).map(([id,v])=>[id,'parameter-field:'+v])),
        cardPinKeys:d.rawForm.igCard?['igCardU','igCardV'].filter(id=>d.rawForm[id]).map(id=>'parameter-field:'+d.rawForm.igCard+':'+d.rawForm[id]):[],
        cardSelectionRaw:Object.fromEntries(['igCard','igCardU','igCardV'].map(id=>[id,element(id).value]))};
      seam.setState(state);seam.installCardHandlers(state);return state;
    },
    change(id,value){const node=element(id);node.value=value;node.dispatchEvent(new InputEvent('input',{bubbles:true}));node.dispatchEvent(new InputEvent('change',{bubbles:true}));},
    swap(){const u=element('igCardU'),v=element('igCardV'),before=u.value;u.value=v.value;v.value=before;u.dispatchEvent(new InputEvent('change',{bubbles:true}));}
  };
}

async function setup(options={}){
  const old=objects(),current=clone(old);
  for(const [id,field]of options.stale||[])current.parameters.find(p=>p.id===id).card.fields.find(f=>f.id===field).value.num+='1';
  if(options.lost)current.parameters=current.parameters.filter(p=>p.id!==10);
  const f=fixture(current),catalog=async value=>new Map([...await f.seam.catalogPins(value)].map(([key,ref])=>[key,clone(ref)]));
  const oldPins=await catalog(old),pins=await catalog(current);
  const rawForm=Object.assign(Object.fromEntries(P.Features.sourceFields.map(id=>[id,''])),{
    igName:'pin regression',igMainAlong:'none',igUSource:'repeat',igVSource:'repeat',igUStep:'600',igVStep:'1200',igUPhase:'0',igVPhase:'0'
  },options.card===false?{}:{igCard:'10',igCardU:'3',igCardV:'8'},options.fields||{});
  const keys=new Set(Object.entries(rawForm).filter(([id,v])=>v&&id.endsWith('Source')&&!['igUSource','igVSource'].includes(id)).map(([,v])=>'parameter-field:'+v));
  if(rawForm.igCard)for(const id of ['igCardU','igCardV'])if(rawForm[id])keys.add('parameter-field:'+rawForm.igCard+':'+rawForm[id]);
  const d={schema:P.Features.GRID_SCHEMA,draftId:'pr353-pins',kind:'source',intent:'create',baseRef:null,
    rawForm,inputRefs:[...keys].map(key=>({...oldPins.get(key),...(options.lost&&oldPins.get(key).parameterId===10?{lost:true}:{})}))};
  const s=f.start(d,pins);
  return {...f,s,d,old,current,oldPins,pins};
}
const saved=f=>clone(f.w.readGridDrafts().drafts.find(d=>d.draftId===f.d.draftId));
const snapshot=f=>JSON.stringify({drafts:f.w.readGridDrafts(),pins:[...f.s.inputPins],raw:f.seam.rawValue(f.s),history:f.w.history.undo.length});
const getPin=(f,id,field)=>f.s.inputPins.get('parameter-field:'+id+':'+field);

test('R353-10 unchanged V mapping retains stale fingerprint and raw; preview rejects',async()=>{
  const f=await setup({stale:[[10,8]]}),before=saved(f);
  f.change('igCardU','9');
  assert.deepEqual(getPin(f,10,8),before.inputRefs.find(r=>r.fieldId===8));
  assert.equal(saved(f).rawForm.igVStep,before.rawForm.igVStep);
  assert.equal(saved(f).rawForm.igCardU,'9');assert.equal(saved(f).rawForm.igCardV,'8');
  assert.equal(f.prompts.length,0,'Untouched stale V must not be re-acquired');
  await assert.rejects(()=>f.seam.validateDraftPins(f.s),/身分已變更|來源.*變更/);
});
test('R353-10 input then change cancellation preserves all raw pins and history',async()=>{
  const f=await setup({stale:[[10,8]]}),before=snapshot(f);
  f.change('igCardU','8');
  assert.equal(f.prompts.length,1,'Selecting the already-shared stale f8 must ask before overwriting it');
  assert.equal(snapshot(f),before,'Cancel restores both mappings and leaves input-before-change persistence untouched');
});
test('R353-10 explicit stale shared-field selection shows old/new pins before confirmation',async()=>{
  const f=await setup({stale:[[10,8]]}),before=getPin(f,10,8),after=f.pins.get('parameter-field:10:8');
  f.env.window.confirm=text=>{f.prompts.push(text);assert.ok(text.includes(JSON.stringify(before)));assert.ok(text.includes(JSON.stringify(after)));assert.deepEqual(getPin(f,10,8),before);return true;};
  f.change('igCardU','8');
  assert.equal(f.prompts.length,1);assert.deepEqual(getPin(f,10,8),after);
  f.change('igCardU','9');
  await assert.doesNotReject(()=>f.seam.validateDraftPins(f.s),'After explicit f8 acquisition, a complete distinct mapping validates');
});
test('R353-10 swap second confirmation cancellation rolls back both axes atomically',async()=>{
  const f=await setup({stale:[[10,3],[10,8]]}),before=snapshot(f);
  f.env.window.confirm=text=>{f.prompts.push(text);return f.prompts.length===1;};
  f.swap();
  assert.equal(f.prompts.length,2,'Both changed stale sources must be considered before committing either');
  assert.equal(snapshot(f),before,'Accepting one source then cancelling the other cannot partially repin');
});
test('R353-11 phase unlink retains the exact pin still consumed by the whole card',async()=>{
  const f=await setup({fields:{igUPhaseSource:'10:3'}}),before=clone(getPin(f,10,3));
  f.change('igUPhaseSource','');
  assert.deepEqual(getPin(f,10,3),before);assert.equal(saved(f).rawForm.igUPhaseSource,'');
  assert.equal(saved(f).rawForm.igCardU,'3');assert.equal(f.prompts.length,0);
  await assert.doesNotReject(()=>f.seam.validateDraftPins(f.s));
});
test('R353-11 phase unlink preserves a stale whole-card pin without automatic re-acquisition',async()=>{
  const f=await setup({stale:[[10,3]],fields:{igUPhaseSource:'10:3'}}),before=clone(getPin(f,10,3));
  f.change('igUPhaseSource','');
  assert.deepEqual(getPin(f,10,3),before);assert.notDeepEqual(getPin(f,10,3),f.pins.get('parameter-field:10:3'));
  await assert.rejects(()=>f.seam.validateDraftPins(f.s),/身分已變更|來源.*變更/);
});
test('R353-11 either consumer may leave first; only the last user releases the pin',async()=>{
  for(const order of ['card-first','field-first']){
    const f=await setup({fields:{igUPhaseSource:'10:3'}}),before=clone(getPin(f,10,3));
    const card=()=>f.change('igCardU','9'),field=()=>f.change('igUPhaseSource','');
    (order==='card-first'?card:field)();assert.deepEqual(getPin(f,10,3),before,order);
    (order==='card-first'?field:card)();assert.equal(getPin(f,10,3),undefined,order);
    assert.ok(getPin(f,10,8));assert.ok(getPin(f,10,9));await assert.doesNotReject(()=>f.seam.validateDraftPins(f.s));
  }
});
test('control: direct and per-field sources retain last-user pin accounting',async()=>{
  const direct=await setup({card:false});assert.equal(direct.s.inputPins.size,0);await assert.doesNotReject(()=>direct.seam.validateDraftPins(direct.s));
  const f=await setup({card:false,fields:{igUPhaseSource:'10:3',igVPhaseSource:'10:3'}}),before=clone(getPin(f,10,3));
  f.change('igUPhaseSource','');assert.deepEqual(getPin(f,10,3),before);await assert.doesNotReject(()=>f.seam.validateDraftPins(f.s));
  f.change('igVPhaseSource','');assert.equal(f.s.inputPins.size,0);await assert.doesNotReject(()=>f.seam.validateDraftPins(f.s));
});
test('R353-12 direct atomic draft replacement accepts B pins already used by both phases',async()=>{
  const f=await setup({lost:true,fields:{igUPhaseSource:'20:3',igVPhaseSource:'20:8'}}),candidate=clone(f.d),history=f.w.history.undo.length;
  Object.assign(candidate.rawForm,{igCard:'20',igCardU:'3',igCardV:'8'});
  candidate.inputRefs=candidate.inputRefs.filter(r=>r.parameterId===20);
  assert.doesNotThrow(()=>f.w.setGridDraft(candidate.draftId,candidate,f.s.contextToken),'A different card is a valid replacement even when both B pins already existed');
  assert.deepEqual(saved(f),candidate);assert.equal(f.w.history.undo.length,history+1);
});
test('R353-12 card selection reuses both existing phase pins with atomic history and ZIP roundtrip',async()=>{
  const f=await setup({lost:true,fields:{igUPhaseSource:'20:3',igVPhaseSource:'20:8'}}),before=saved(f),count=f.w.history.undo.length;
  const b3=clone(getPin(f,20,3)),b8=clone(getPin(f,20,8));
  f.change('igCard','20');assert.deepEqual(saved(f),before,'Incomplete map must not replace the persisted lost card');
  f.change('igCardU','3');assert.deepEqual(saved(f),before,'One axis is not an atomic two-axis replacement');
  f.change('igCardV','8');const after=saved(f);
  assert.equal(after.rawForm.igCard,'20');assert.equal(after.rawForm.igCardU,'3');assert.equal(after.rawForm.igCardV,'8');
  assert.equal(after.rawForm.igUPhaseSource,'20:3');assert.equal(after.rawForm.igVPhaseSource,'20:8');
  assert.equal(after.inputRefs.length,2);assert.deepEqual(getPin(f,20,3),b3);assert.deepEqual(getPin(f,20,8),b8);
  assert.equal(f.w.history.undo.length,count+1,'Only the complete mapping writes a single local history step');
  await assert.doesNotReject(()=>f.seam.validateDraftPins(f.s));
  assert.equal(f.w.tryLocalHistory('line undo').ok,true);assert.deepEqual(saved(f),before);
  assert.equal(f.w.tryLocalHistory('line redo').ok,true);assert.deepEqual(saved(f),after);
  const packed=await P.pack('',await f.w.manifest(),new Map(),zip),cold=await P.unpack(packed,zip);
  const record=cold.manifest.featureAttachments.records.find(r=>r.kind===P.Features.GRID_KIND);
  assert.deepEqual(clone(P.Features.gridDrafts(record.value)),clone(f.w.readGridDrafts()));
});
test('R353-12 lost replacement rejects incomplete duplicate and unmapped borrowed pins without a write',async()=>{
  const f=await setup({lost:true,fields:{igUPhaseSource:'20:3',igVPhaseSource:'20:8'}}),before=snapshot(f);
  for(const mapping of [{igCard:'20',igCardU:'3',igCardV:''},{igCard:'20',igCardU:'3',igCardV:'3'},{igCard:'10',igCardU:'3',igCardV:'8'}]){
    const candidate=clone(f.d);Object.assign(candidate.rawForm,mapping);candidate.inputRefs=candidate.inputRefs.filter(r=>r.parameterId===20);
    assert.throws(()=>f.w.setGridDraft(candidate.draftId,candidate,f.s.contextToken),/不得純移除|雙欄映射/);
    assert.equal(snapshot(f),before);
  }
});
test('R353-12 same card and same-ID reconstruction remain rejected after an incomplete selection',async()=>{
  const f=await setup({lost:true}),before=saved(f),history=f.w.history.undo.length;
  const rebuilt=clone(f.d);rebuilt.inputRefs=rebuilt.inputRefs.map(({lost,...ref})=>ref);
  assert.throws(()=>f.w.setGridDraft(rebuilt.draftId,rebuilt,f.s.contextToken),/不得抹除/);
  f.change('igCard','20');f.change('igCard','10');
  assert.equal(f.element('igCard').value,'20','Owned lost pins must still reject same-ID selection after local pins were removed');
  assert.deepEqual(saved(f),before);assert.equal(f.w.history.undo.length,history);
  const sameCard=clone(f.d);sameCard.rawForm.igCardU='9';sameCard.inputRefs=[{...f.oldPins.get('parameter-field:10:9')},sameCard.inputRefs.find(r=>r.fieldId===8)];
  assert.throws(()=>f.w.setGridDraft(sameCard.draftId,sameCard,f.s.contextToken),/不得純移除|雙欄映射|參數卡/);
  assert.deepEqual(saved(f),before);
});
test('R353-12 replacing a lost pin shared by card and phase must replace both consumer kinds',async()=>{
  const f=await setup({lost:true,fields:{igUPhaseSource:'10:3',igVPhaseSource:'20:8'}}),before=saved(f),candidate=clone(f.d);
  Object.assign(candidate.rawForm,{igCard:'20',igCardU:'3',igCardV:'8'});
  candidate.inputRefs=[f.pins.get('parameter-field:20:3'),f.pins.get('parameter-field:20:8')].map(clone);
  assert.throws(()=>f.w.setGridDraft(candidate.draftId,candidate,f.s.contextToken),/逐欄.*不得純移除/);
  assert.deepEqual(saved(f),before);
  candidate.rawForm.igUPhaseSource='20:3';assert.doesNotThrow(()=>f.w.setGridDraft(candidate.draftId,candidate,f.s.contextToken));
  assert.equal(saved(f).rawForm.igUPhaseSource,'20:3');assert.equal(saved(f).inputRefs.length,2);
});
test('control: original per-field lost replacement may reuse an existing live pin',async()=>{
  const f=await setup({card:false,lost:true,fields:{igUStepSource:'10:3',igVStepSource:'20:3'}}),before=snapshot(f);
  f.change('igUStepSource','20:3');assert.equal(snapshot(f),before,'Cancel keeps the original per-field guard');
  f.env.window.confirm=()=>true;f.change('igUStepSource','20:3');
  assert.equal(saved(f).inputRefs.length,1);assert.equal(saved(f).rawForm.igUStepSource,'20:3');
  await assert.doesNotReject(()=>f.seam.validateDraftPins(f.s));
});
