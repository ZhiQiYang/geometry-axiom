/* Execute the full shipped adapter with finite DOM/event scheduling and actual
 * native fixture/producer receipts. HTTP/DOM are controlled; no Chrome claim.
 */
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {spawnSync}=require('node:child_process'),crypto=require('node:crypto');
const {createDOM}=require('./_model_update_dom.js');
const M=require('../geometry-web/model-update.js'),P=require('../geometry-web/project-store.js'),I=require('../geometry-web/identity-ledger.js'),S=require('../geometry-web/source-inspector.js');
const clone=value=>JSON.parse(JSON.stringify(value)),ROOT=path.resolve(__dirname,'..');
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
let nativeData;const produced=new Map();
function engine(mode,payload={}) {
  const result=spawnSync(process.env.PYTHON||'python',['-m','tests._model_update_faces_native',mode],{cwd:ROOT,input:JSON.stringify(payload),encoding:'utf8',timeout:90000,maxBuffer:32*1024*1024});
  assert.equal(result.status,0,result.stderr||result.error?.message);const value=JSON.parse(result.stdout);assert.equal(value.status,undefined,JSON.stringify(value));return value;
}
function harness({inactive=false,unknown=false,replaced=false,reorder=false}={}) {
  const f=clone(nativeData||=engine('fixture')),dom=createDOM(),commits=[],calls=[];
  if(unknown)delete f.record.sourceIdentity;
  if(inactive)f.graph.identityLedger.active=false;
  if(replaced)f.graph.nodes.find(x=>x.key==='placement:3').incarnation='b'.repeat(32)+':3';
  // reorder: same saved record with every object's keys in reverse order (a
  // project written by another build); review rows must not treat order as change.
  const reversed=value=>Array.isArray(value)?value.map(reversed):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).reverse().map(k=>[k,reversed(value[k])])):value;
  if(reorder)f.record=reversed(f.record);
  let record=clone(f.record),context='project-one',frame='frame-one',revision=1,reads=0,identityChange=false;
  let realmClone=clone;
  const state=()=>({context,frame,revision,contextToken:'native-one',undo:null,redo:null,group:null,blocked:false});
  const env={...dom,window:{addEventListener(){},WorkspaceShell:{attach(){},detach(){},refresh(){}}},TextEncoder,AbortController,DOMException,IdentityLedger:I,SourceInspector:S,
    GeometryProject:{...P,validateSpaceModel:value=>P.validateSpaceModel(clone(value))},setInterval:()=>1,clearInterval(){},toast(){},
    ReferenceWorkspace:{getModelOperationState:state,getSpaceModels:()=>[realmClone(record)],getFaceProjection:()=>null,
      updateSpaceModel:(id,value)=>{assert.equal(id,record.id);P.validateSpaceModel(clone(value));commits.push(clone(value));record=clone(value);revision++;return realmClone(value);}},
    api:async command=>{
      calls.push(command);
      if(command==='identity-read')return{ok:true,active:!inactive};
      if(command==='source-inspect'){reads++;const graph=clone(f.graph);if(identityChange&&reads>=7)graph.revision++;return graph;}
      if(command==='dump-deidentified')return{ok:true,text:f.scene};
      if(command==='surfaces')return{ok:true,surfaces:clone(f.surfaces)};
      if(command==='objects')return clone(f.objects);
      if(command==='line identity-ledger activate'){revision++;return{ok:true};}
      throw Error('unexpected native read '+command);
    },
    fetch:async(url,options)=>{
      assert.equal(url,'/model/update-preview');const request=JSON.parse(options.body),key=M.canonical(request);
      if(!produced.has(key))produced.set(key,engine('update',request));
      return{ok:true,json:async()=>clone(produced.get(key))};
    }};
  env.window.window=env.window;
  // The shipped controller and adapter share a realm, just as in the browser.
  // Only records crossing the controlled owner/validator port are marshalled.
  const sandbox=vm.createContext(env);
  realmClone=vm.runInContext('value=>JSON.parse(JSON.stringify(value))',sandbox);
  vm.runInContext(fs.readFileSync(path.join(ROOT,'geometry-web/model-update.js'),'utf8'),sandbox);
  vm.runInContext(fs.readFileSync(path.join(ROOT,'geometry-web/model-update-app.js'),'utf8'),sandbox);
  const element=id=>{const found=dom.document.getElementById(id);assert.ok(found,'R362_UI_ELEMENT_'+id);return found;};
  return{f,env,commits,calls,element,app:env.window.ModelUpdateApp,
    open:()=>env.window.ModelUpdateApp.open(f.record.id),selectors:()=>element('muDialog').querySelectorAll('[data-mu-use]'),
    click:async id=>{assert.equal(element(id).disabled,false,id+' enabled');await element(id).dispatch('click');},
    async select(index,value){const control=this.selectors()[index];assert.ok(control);control.value=String(value);await control.dispatch('change');},
    async check(control,value=true){control.checked=value;await control.dispatch('change');},
    staleIdentity(){identityChange=true;},replaceOwner(){context='project-two';frame='frame-two';}};
}
test('R362_UI_FACES exposes all native orientations, preserves ordered slots, previews and confirms through the shipped adapter',async()=>{
  const h=harness();await h.open();
  assert.equal(h.app.snapshot().phase,'selecting','R362_UI_FACES_BEGIN');
  assert.equal(h.selectors().length,8,'R362_UI_FACE_SLOTS');
  assert.deepEqual(h.selectors().map(s=>Number(s.value)),h.f.record.input.uses.map(u=>u.placement_id));
  assert.equal(h.element('muPlacementField').hidden,true);assert.equal(h.element('muPlanChoices').hidden,true);
  assert.match(h.element('muSavedSettings').textContent,/體積計算封口/);
  await h.click('muPreview');assert.equal(h.app.snapshot().phase,'review','R362_UI_FACES_PREVIEW');
  assert.match(h.element('muDiff').textContent,/承載面 8/);assert.match(h.element('muDiff').textContent,/72900000000/);
  await h.check(h.element('muConfirmed'));await h.click('muApply');
  assert.equal(h.commits.length,1,'R362_UI_FACES_ONE_COMMIT');assert.equal(h.commits[0].id,h.f.record.id);
  assert.deepEqual(h.commits[0].input.uses,h.f.record.input.uses);assert.equal(h.commits[0].sourceIdentity.roots.length,8);
});
test('R09F_REVIEW_KEY_ORDER key order alone never marks a review row as changed',async()=>{
  const changedRows=async options=>{const h=harness(options);await h.open();await h.click('muPreview');assert.equal(h.app.snapshot().phase,'review',h.element('muStatus').textContent);
    const html=h.element('muDiff').innerHTML,rows=[...html.matchAll(/<tr( class="mu-changed")?><th scope="row">([^<]*)<\/th>/g)];
    assert.ok(rows.length>10,'R09F_REVIEW_ROWS');return rows.filter(r=>r[1]).map(r=>r[2]).sort();};
  const plain=await changedRows(),reordered=await changedRows({reorder:true});
  assert.ok(!plain.includes('承載面 1'),'R09F_UNCHANGED_USE_NOT_FLAGGED');
  // Row order follows each record's own keys; only which rows are flagged matters.
  assert.deepEqual(reordered,plain,'R09F_REVIEW_KEY_ORDER');
});
test('R362_UI_UNKNOWN never prefills IDs and requires every explicit slot, rejecting duplicates',async()=>{
  const h=harness({unknown:true});await h.open();
  assert.equal(h.app.snapshot().phase,'selecting','R362_UI_UNKNOWN_BEGIN');
  assert.equal(h.selectors().length,8);assert.ok(h.selectors().every(s=>s.value===''),'R362_UI_UNKNOWN_NO_PREFILL');
  assert.equal(h.element('muPreview').disabled,true);
  for(let i=0;i<8;i++)await h.select(i,h.f.record.input.uses[i].placement_id);
  assert.equal(h.element('muPreview').disabled,false);
  await h.select(1,h.f.record.input.uses[0].placement_id);assert.equal(h.element('muPreview').disabled,true,'R362_UI_DUPLICATES_BLOCK');
  assert.equal(h.commits.length,0);
});
test('R362_UI_REPLACED use cannot be removed and needs a decision after the slot is explicitly selected',async()=>{
  const h=harness({replaced:true});await h.open();
  assert.equal(h.app.snapshot().phase,'selecting','R362_UI_REPLACED_BEGIN');
  const index=h.f.record.input.uses.findIndex(u=>u.placement_id===3);assert.equal(h.selectors()[index].value,'');
  assert.equal(h.element('muDialog').querySelector('[data-mu-remove="placement:3"]'),null);
  await h.select(index,3);assert.equal(h.element('muPreview').disabled,true,'R362_UI_REPLACED_DECISION');
  await h.check(h.element('muDialog').querySelector('[data-mu-retarget="placement:3"]'));
  assert.equal(h.element('muPreview').disabled,false);
  await h.click('muPreview');assert.equal(h.app.snapshot().phase,'review',h.element('muStatus').textContent);
  await h.check(h.element('muConfirmed'));
  h.element('muDialog').querySelector('[data-mu-retarget="placement:3"]').checked=false;
  await h.click('muApply');assert.equal(h.app.snapshot().phase,'failed','R362_UI_DECISION_PIN');assert.equal(h.commits.length,0,'R362_UI_DECISION_PIN');
});
test('R362_UI_IDENTITY_PIN refuses a live identity read from a different native revision',async()=>{
  const h=harness();await h.open();assert.equal(h.app.snapshot().phase,'selecting','R362_UI_IDENTITY_PIN_BEGIN');
  h.staleIdentity();await h.click('muPreview');
  assert.equal(h.app.snapshot().phase,'failed','R362_UI_IDENTITY_PIN');assert.equal(h.commits.length,0);
  assert.match(h.element('muStatus').textContent,/來源版本或身分帳已變更/);
});
test('R362_UI_ACTIVATE remains explicit and expires the current faces dialog',async()=>{
  const h=harness({inactive:true});await h.open();assert.equal(h.app.snapshot().phase,'selecting','R362_UI_ACTIVATE_BEGIN');
  assert.equal(h.element('muActivate').hidden,false);assert.ok(h.selectors().every(s=>s.value===''));
  await h.click('muActivate');assert.equal(h.app.snapshot().phase,'failed');assert.equal(h.commits.length,0);
  assert.equal(h.calls.filter(x=>x==='line identity-ledger activate').length,1);
});
test('R362_LIBRARY_FACES existing modify entry invokes the real faces dispatch',()=>{
  const source=fs.readFileSync(path.join(ROOT,'geometry-web/space-workspace.js'),'utf8');
  const start=source.indexOf('  function beginHeightEdit('),end=source.indexOf('  function cancelHeightEdit(',start);assert.ok(start>=0&&end>start);
  const calls=[],record={id:'faces-model',input:{mode:'faces'}};
  const env={ReferenceWorkspace:{getSpaceModels:()=>[record]},state:{createdId:record.id},
    window:{ModelUpdateApp:{open:id=>calls.push(['open',id])}},close:()=>calls.push(['close']),message:()=>assert.fail('missing faces entry'),
    show:()=>assert.fail('faces must use existing source-update dialog')};
  vm.runInNewContext(source.slice(start,end)+'\nbeginHeightEdit();',env);
  assert.deepEqual(calls,[['close'],['open',record.id]],'R362_LIBRARY_FACES');
  assert.doesNotMatch(source,/m\.input\.mode===\"plan\"\?`<button class=\"sm-button\" data-sm-edit-height/,'R362_LIBRARY_BUTTON');
});
