'use strict';
/* Execute the shipped workspace renderer, input handler and command builder.
 * Native reads are fixed fixtures here; real pointer/confirm/save/cold-open
 * acceptance lives in integration/d09_override_display_browser.cjs. */
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(process.env.GEOMETRY_D09_WORKSPACE_SOURCE||path.join(__dirname,'../geometry-web/engineering-workspace.js'),'utf8');
const boundary='return {configure,open,close,refresh:()=>load(false),get isOpen()';
assert.equal(source.split(boundary).length,2,'one actual EngineeringWorkspace export boundary');
const executable=source.replace(boundary,'return {__displayTest:{state,selectTarget,renderTarget,setPath,handleInput,buildOperations,draftContent},configure,open,close,refresh:()=>load(false),get isOpen()');
const plain=value=>JSON.parse(JSON.stringify(value));
const prefix='application.targets.1.overrides.';

function fixture(overrides={gap:{kind:'literal',value:4}}){
  const env={window:{},GeometryApplication:require('../geometry-app/application.js')};
  vm.runInNewContext(executable,env,{filename:'engineering-workspace.production.js'});
  const seam=env.window.EngineeringWorkspace.__displayTest,state=seam.state;
  state.snapshot={placements:[{id:1}],grids:[{id:7,placement_id:1}],timbers:[],sources:[],
    specs:[{name:'FaceGap',value:6},{name:'OtherGap',value:9}],
    materials:[{id:'timber-stock',version:2,kind:'timber',name:'截面規格',A:27,B:33}],methods:[],
    applications:[{id:'face-application',placement_id:1,method:{id:'method',version:1},
      longAxis:null,mainAlong:null,anchorOptions:{u:null,v:null},overrides:plain(overrides)}]};
  seam.selectTarget(1,7);
  const target=state.application.targets[1];
  const render=()=>seam.renderTarget({id:1},target);
  const write=(field,value)=>seam.setPath(prefix+field,value);
  const input=(field,value)=>seam.handleInput({target:{dataset:{ewField:prefix+field},
    tagName:'INPUT',type:'text',value,hasAttribute:()=>false}});
  const operations=()=>seam.buildOperations({action:'apply',draft:plain(state.application)},state.snapshot);
  return {seam,state,target,render,write,input,operations};
}
function control(html,path){
  const id='ewField-'+path.replace(/[^\w-]/g,'-');
  const select=html.match(new RegExp('<select id="'+id+'"[^>]*>([\\s\\S]*?)</select>'));
  if(select){const selected=select[1].match(/<option value="([^"]*)" selected>/);return selected?.[1]??null;}
  return html.match(new RegExp('<input id="'+id+'"[^>]* value="([^"]*)"'))?.[1]??null;
}
async function candidate(h){const operations=plain(await h.operations());assert.equal(operations.length,2);assert.equal(operations[1].op,'bind-grid');return operations[0].value;}

test('D09 current literal face override is rendered without writing a draft or changing candidate sources',async()=>{
  const h=fixture(),before=h.seam.draftContent(),snapshot=JSON.stringify(h.state.snapshot);
  const html=h.render();
  assert.equal(control(html,prefix+'gap.mode'),'literal','D09_CURRENT_LITERAL_MODE');
  assert.equal(control(html,prefix+'gap.value'),'4','D09_CURRENT_LITERAL_VALUE');
  assert.equal(h.seam.draftContent(),before,'D09_RENDER_DOES_NOT_CREATE_DRAFT');
  assert.equal(JSON.stringify(h.state.snapshot),snapshot,'D09_RENDER_DOES_NOT_MUTATE_NATIVE_READ');
  assert.deepEqual(plain(h.target.overrides),{},'D09_UNTOUCHED_OVERRIDE_STAYS_IMPLICIT');
  assert.deepEqual((await candidate(h)).overrides,{gap:{kind:'literal',value:4}},'D09_NOOP_PRESERVES_SOURCE');
});

test('D09 first value edit preserves the displayed literal mode and every untouched native override',async()=>{
  const h=fixture({gap:{kind:'literal',value:4},'primary.A':{kind:'spec',name:'FaceGap'}});
  h.input('gap.value','5');
  assert.equal(h.target.overrides.gap.mode,'literal','D09_FIRST_VALUE_EDIT_KEEPS_MODE');
  assert.equal(h.target.overrides.gap.value,'5');
  assert.deepEqual((await candidate(h)).overrides,{gap:{kind:'literal',value:5},'primary.A':{kind:'spec',name:'FaceGap'}},'D09_EDIT_ONLY_TOUCHED_FIELD');
  assert.deepEqual(h.state.snapshot.applications[0].overrides.gap,{kind:'literal',value:4});
});

test('D09 named face dimensions and all role axes retain exact source kind including zero gap',async()=>{
  const originals={gap:{kind:'literal',value:0}};
  for(const role of ['boundary','primary','secondary'])for(const axis of ['A','B'])originals[role+'.'+axis]={kind:'spec',name:'FaceGap'};
  const h=fixture(originals),html=h.render();
  assert.equal(control(html,prefix+'gap.value'),'0','D09_ZERO_IS_EXPLICIT_OVERRIDE');
  for(const role of ['boundary','primary','secondary'])for(const axis of ['A','B']){
    assert.equal(control(html,prefix+role+axis+'.mode'),'spec','D09_ROLE_SOURCE_MODE');
    assert.equal(control(html,prefix+role+axis+'.value'),'FaceGap','D09_ROLE_SOURCE_NAME');
  }
  h.write('secondaryB.value','OtherGap');
  assert.deepEqual((await candidate(h)).overrides,{...originals,'secondary.B':{kind:'spec',name:'OtherGap'}},'D09_NAMED_EDIT_RETAINS_SPEC');
});

test('D09 explicit restore and the preserve checkbox override the native display fallback',async()=>{
  const h=fixture();h.write('gap.mode','inherit');
  assert.equal(control(h.render(),prefix+'gap.mode'),'inherit','D09_EXPLICIT_RESTORE_WINS');
  assert.deepEqual((await candidate(h)).overrides,{},'D09_EXPLICIT_RESTORE_REMOVES_OVERRIDE');
  const drop=fixture();drop.target.preserveOverrides=false;
  assert.equal(control(drop.render(),prefix+'gap.mode'),'inherit','D09_DROP_PRESERVED_OVERRIDES');
  assert.deepEqual((await candidate(drop)).overrides,{});
  drop.write('gap.mode','literal');drop.input('gap.value','8');
  assert.equal(control(drop.render(),prefix+'gap.value'),'8','D09_EXPLICIT_DRAFT_STILL_WINS');
  assert.deepEqual((await candidate(drop)).overrides,{gap:{kind:'literal',value:8}});
});

test('D09 native refresh updates untouched displayed values while preserving a real unsaved edit',()=>{
  const h=fixture();h.state.snapshot.applications[0].overrides.gap.value=6;
  assert.equal(control(h.render(),prefix+'gap.value'),'6','D09_DISPLAY_FOLLOWS_LATEST_NATIVE_READ');
  h.input('gap.value','7');h.state.snapshot.applications[0].overrides.gap.value=9;
  assert.equal(control(h.render(),prefix+'gap.value'),'7','D09_UNSAVED_EDIT_SURVIVES_REFRESH');
  // The shipping confirmation clears submitted overrides before reading again.
  h.target.overrides={};
  assert.equal(control(h.render(),prefix+'gap.value'),'9','D09_CONFIRMED_FORM_READS_CURRENT_OVERRIDE');
  assert.deepEqual(plain(h.target.overrides),{});
});

test('D09 a saved material override is identified without flattening or inventing an editable dimension',async()=>{
  const material={kind:'material',id:'timber-stock',version:2,field:'A'},h=fixture({'primary.A':material});
  const html=h.render();
  assert.equal(control(html,prefix+'primaryA.mode'),'saved','D09_MATERIAL_OVERRIDE_IS_NOT_INHERIT');
  assert.match(html,/截面規格 · v2 · A mm/,'D09_MATERIAL_SOURCE_IDENTITY_VISIBLE');
  assert.equal(control(html,prefix+'primaryA.value'),null,'D09_MATERIAL_NOT_FLATTENED_TO_NUMBER');
  assert.deepEqual((await candidate(h)).overrides,{'primary.A':material},'D09_MATERIAL_SOURCE_UNCHANGED');
  h.write('primaryA.mode','literal');h.input('primaryA.value','41');
  assert.deepEqual(plain(h.target.overrides.primaryA),{mode:'literal',value:'41'},'D09_DISPLAY_METADATA_IS_NOT_SAVED_IN_DRAFT');
  assert.deepEqual((await candidate(h)).overrides,{'primary.A':{kind:'literal',value:41}},'D09_EXPLICIT_MATERIAL_REPLACEMENT');
});

test('D09 an absent face override still means inherit and an explicit new edit remains a draft',async()=>{
  const h=fixture({});
  assert.equal(control(h.render(),prefix+'gap.mode'),'inherit');
  assert.equal(control(h.render(),prefix+'gap.value'),null);
  h.write('gap.mode','literal');h.input('gap.value','3');
  assert.deepEqual((await candidate(h)).overrides,{gap:{kind:'literal',value:3}});
  assert.deepEqual(h.state.snapshot.applications[0].overrides,{});
});
