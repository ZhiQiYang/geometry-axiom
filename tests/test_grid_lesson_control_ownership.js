'use strict';
// Run the shipped workspace closure. The export seam exposes owner state and
// finite presentation/read destinations, never a copied lock or current guard.
// Browser regression separately proves actual native save -> reopen -> lesson.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const P=require('../geometry-web/project-store.js');
const source=fs.readFileSync(process.env.GEOMETRY_GRID_WORKSPACE_SOURCE||path.join(__dirname,'../geometry-web/grid-system-workspace.js'),'utf8');
const boundary='window.InfiniteGridWorkspace={';
assert.equal(source.split(boundary).length,2,'one shipped workspace export');
const executable=source.replace(boundary,boundary+`__controlTest:{operation,releaseHeldControls,syncOrphanDraft,approveInputReplacement,overwriteFields,validateDraftPins,flush,
  getState:()=>state,setState:value=>{state=value;},
  ports:value=>{capture=value.capture;syncDraftState=value.sync;applicationState=value.application;reveal=value.reveal;open=value.open;}},`);
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}
function node(tag,id='',classes=[]){
  const names=new Set(classes),attributes=new Map(),writes=[];let disabled=false;
  const n={tagName:tag.toUpperCase(),id,children:[],parentElement:null,attributes,writes,value:'',textContent:'',dataset:{},open:false,
    classList:{add:(...items)=>items.forEach(v=>names.add(v)),remove:(...items)=>items.forEach(v=>names.delete(v)),contains:v=>names.has(v),
      toggle:(v,on)=>{const next=on??!names.has(v);if(next)names.add(v);else names.delete(v);return next;}},
    setAttribute:(key,value)=>attributes.set(key,String(value)),addEventListener(){},focus(){},
    append(...children){for(const child of children){child.remove();child.parentElement=this;this.children.push(child);}},
    remove(){if(this.parentElement){this.parentElement.children.splice(this.parentElement.children.indexOf(this),1);this.parentElement=null;}},
    matches(selector){return selector[0]==='#'?this.id===selector.slice(1):selector[0]==='.'?names.has(selector.slice(1)):this.tagName===selector.toUpperCase();},
    closest(selector){for(let current=this;current;current=current.parentElement)if(current.matches(selector))return current;return null;},
    querySelectorAll(selector){
      const descendants=[];const visit=parent=>{for(const child of parent.children){descendants.push(child);visit(child);}};visit(this);
      return descendants.filter(child=>selector.split(',').some(part=>{
        const terms=part.trim().split(/\s+/);return child.matches(terms.at(-1))&&(terms.length===1||!!child.parentElement?.closest(terms.slice(0,-1).join(' ')));
      }));
    },
  };
  Object.defineProperty(n,'disabled',{get:()=>disabled,set:value=>{disabled=!!value;writes.push(disabled);}});
  return n;
}
function harness({syncOrphan=false,holdRender=false}={}){
  const body=node('body'),canvas=node('div','canvasViewport'),calls=[],reached=deferred(),renderReply=deferred();body.append(canvas);
  let context={id:'same-project'},contextToken='first-context',pending=false,approval=false,objects={ok:true},attachment={schema:'grid-editor-draft/1',rawForm:{igName:' Raw 001 ',igUStep:'=1/0'}},active;
  const lesson=node('div','paramGridLesson');
  const lessonButtons=['Stage','Frame1','Frame2','Close','Open'].map(name=>node('button','paramGridLesson'+name));lesson.append(...lessonButtons);
  const document={body,createElement:tag=>node(tag),getElementById:id=>body.querySelectorAll('#'+id)[0]||null};
  const oc={busy:false,gridBindings:[]};
  const sandbox={document,oc,console,TextEncoder,apiRequest:async command=>{assert.equal(command,'objects');return objects;},window:{addEventListener(){},confirm:message=>{calls.push(['confirm',message]);return approval;}},GeometryProject:P,connection:{phase:'ready'},
    ReferenceWorkspace:{escape:value=>value,context:()=>context,getProjectState:()=>({contextToken}),
      featureConfirmationPending:()=>pending,readFeatureAttachment:()=>attachment,
      setGridDraft:(...args)=>calls.push(['setGridDraft',...args]),
      readGridDrafts:()=>({drafts:attachment?[attachment]:[],orphans:[]})},
    renderObjects:async()=>{calls.push(['render']);reached.resolve();if(holdRender)await renderReply.promise;return true;},
  };
  vm.runInNewContext(executable,sandbox,{filename:'grid-system-workspace.production.js'});
  const ui=sandbox.window.InfiniteGridWorkspace,seam=ui.__controlTest,dialog=document.getElementById('infiniteGridWorkspace');dialog.open=true;
  function mount({foreignContext=false,locked=false,orphaned=false,mode='source'}={}){
    if(foreignContext){context={id:'same-project'};contextToken='replacement-context';}
    for(const child of [...dialog.children])child.remove();
    const settings=node('div','', ['ig-settings']),footer=node('div','', ['ig-footer']),slot=node('div','paramGridLessonSlot');
    const input=node('input','igName'),select=node('select','igUStepSource'),save=node('button','igSaveSource'),preDisabled=node('button','igOriginalDisabled'),discard=node('button','igDiscardDraft'),close=node('button','igClose');
    input.value=' Raw 001 ';select.value='0:1';preDisabled.disabled=true;
    if(locked){input.disabled=true;select.disabled=true;save.disabled=true;}
    settings.append(input,select,save,preDisabled,slot);footer.append(discard);dialog.append(close,settings,footer);
    for(const id of ['igStatus','igTitle','igDraftNote','igStateText','igStateLine'])dialog.append(node('div',id));
    slot.append(lesson);
    const state={context,contextToken,mode,busy:false,initializing:false,orphaned,baseRef:{kind:'grid-system',id:0},publishTarget:null};
    seam.setState(state);active={state,input,select,save,preDisabled,discard,close,slot,controls:[close,input,select,save,preDisabled,discard]};return active;
  }
  const original=mount();
  seam.ports({capture:s=>calls.push(['capture',s]),sync:s=>{calls.push(['sync',s]);if(syncOrphan)seam.syncOrphanDraft(s);},
    application:s=>calls.push(['application',s]),reveal:(...args)=>calls.push(['reveal',...args]),
    open:async(options,committed)=>{calls.push(['open',options,committed]);mount({locked:true});return true;}});
  function lessonUntouched(){assert.ok(lessonButtons.every(button=>!button.disabled),'all five shared lesson buttons remain enabled');assert.ok(lessonButtons.every(button=>button.writes.length===0),'grid locks never write a shared lesson disabled bit');}
  return {ui,seam,oc,dialog,canvas,lesson,lessonButtons,original,calls,lessonUntouched,mount,
    moveLesson:()=>canvas.append(lesson),setPending:value=>{pending=value;},setApproval:value=>{approval=value;},setObjects:value=>{objects=value;},setAttachment:value=>{attachment=value;},
    get attachment(){return attachment;},get active(){return active;},connection:sandbox.connection,
    renderReached:reached.promise,releaseRender:()=>renderReply.resolve(),operation:run=>seam.operation(original.state,run)};
}
function restored(owner){
  for(const control of owner.controls)assert.equal(control.disabled,control===owner.preDisabled,control.id+' restores its previous disabled bit');
}
function lockSnapshot(owner,key){return Array.from(owner.state[key]||[],row=>row[0]);}

test('held operation locks grid mutations without borrowing lesson controls or admitting a second operation',async()=>{
  const h=harness(),gate=deferred();let runs=0;const task=h.operation(async()=>{runs++;await gate.promise;});
  try{
    assert.equal(h.original.state.busy,true);assert.equal(h.oc.busy,true);
    assert.ok(h.original.controls.every(control=>control.disabled));h.lessonUntouched();
    await h.operation(async()=>{runs++;});assert.equal(runs,1,'busy owner cannot dispatch another operation');
  }finally{gate.resolve();await task;}
  restored(h.original);h.lessonUntouched();assert.equal(h.oc.busy,false);assert.equal(h.original.state.busy,false);
});

test('K2a M14b replacement requires old/new confirmation and rejects a previously lost identity',()=>{
  const h=harness(),before={kind:'grid-system',id:2,fingerprint:'a'.repeat(64),lost:true},next={kind:'grid-system',id:3,fingerprint:'b'.repeat(64)};
  h.setApproval(true);assert.equal(h.seam.approveInputReplacement(before,{...before,lost:undefined}),false);assert.equal(h.calls.length,0);
  const parameter={kind:'parameter-field',parameterId:2,fieldId:1,fingerprint:'a'.repeat(64),lost:true};
  assert.equal(h.seam.approveInputReplacement(parameter,{...parameter,fieldId:2,lost:undefined}),false);
  h.setApproval(false);assert.equal(h.seam.approveInputReplacement(before,next),false);
  assert.match(h.calls.at(-1)[1],/"before"/);assert.match(h.calls.at(-1)[1],/"after"/);
  h.setApproval(true);assert.equal(h.seam.approveInputReplacement(before,next),true);
});

test('K2a M15 two-way comparison follows integer and signed-cell parsing rather than raw spelling',()=>{
  const h=harness(),raw={igUStep:'1830 ',igCellI:' 001 ',igCellJ:'1e',igName:' room '};
  const same=h.seam.overwriteFields(raw,{igUStep:'1830',igCellI:'1',igCellJ:'0',igName:'room'});
  assert.deepEqual(Array.from(same,r=>r.field),['igCellJ']);
  const different=h.seam.overwriteFields(raw,{igUStep:'915',igCellI:'1',igCellJ:'0',igName:'room'});
  assert.equal(different[0].raw,'1830 ');assert.equal(different[0].current,'915');
});

test('K2a M05 changed input pin blocks preview until an explicitly selected current pin is recorded',async()=>{
  const h=harness(),row={id:1,mode:'infinite',name:'current',mainAlong:null,uDefinition:{source:'repeat',step:915,phase:0},vDefinition:{source:'none'}};
  const s=h.original.state;s.draftId='stale';s.source=row;s.initialRaw='not-the-form';s.rawOverrides=new Map();
  const rawForm=Object.fromEntries(P.Features.sourceFields.map(f=>[f,'']));rawForm.igUStepSource='2:1';
  const field={id:1,value:915},objects={ok:true,gridSystems:[row],parameters:[{id:2,card:{id:2,fields:[field]}}]};h.setObjects(objects);
  const stale={schema:P.Features.GRID_SCHEMA,draftId:'stale',kind:'source',intent:'edit',baseRef:null,inputRefs:[{kind:'parameter-field',parameterId:2,fieldId:1,fingerprint:'a'.repeat(64)}],rawForm};h.setAttachment(stale);
  await assert.rejects(()=>h.seam.validateDraftPins(s),/已變更／遺失/);
  const next={...stale.inputRefs[0],fingerprint:await P.sha(new TextEncoder().encode(JSON.stringify([2,field])))};
  h.setApproval(false);assert.equal(h.seam.approveInputReplacement(stale.inputRefs[0],next),false);
  assert.equal(stale.inputRefs[0].fingerprint,'a'.repeat(64));
  h.setApproval(true);assert.equal(h.seam.approveInputReplacement(stale.inputRefs[0],next),true);stale.inputRefs=[next];
  assert.equal((await h.seam.validateDraftPins(s)).draftId,'stale');
});

test('K2a M12 a late flush from the retired draft cannot write after another draft owns the editor',()=>{
  const h=harness(),old=h.original.state;Object.assign(old,{draftId:'old',draftSchema:P.Features.GRID_SCHEMA,baseRef:null,inputPins:new Map(),rawOverrides:new Map()});
  h.mount();assert.equal(h.seam.flush(old),undefined);assert.equal(h.calls.some(([name])=>name==='setGridDraft'),false);
  const ref={kind:'grid-system',id:1,fingerprint:'a'.repeat(64)};old.inputPins.set('grid-system:1',ref);
  h.setAttachment({draftId:'old',inputRefs:[{...ref,lost:true}]});h.seam.setState(old);h.seam.flush(old);
  assert.equal(h.calls.at(-1)[2].inputRefs[0].lost,true,'immediate save folds the deletion receipt into cached editor pins');
});

test('same-owner operation failures restore original grid bits and preserve raw input',async()=>{
  for(const kind of ['sync','async']){
    const h=harness(),raw=structuredClone(h.attachment);
    await h.operation(()=>{if(kind==='sync')throw Error('native rejected');return Promise.reject(Error('native rejected'));});
    restored(h.original);h.lessonUntouched();assert.deepEqual(h.attachment,raw);assert.equal(h.original.input.value,' Raw 001 ');
    assert.equal(h.seam.getState(),h.original.state);assert.equal(h.original.state.busy,false);
    assert.equal(h.dialog.querySelectorAll('#igDraftNote')[0].textContent,'native rejected');
    assert.equal(h.dialog.querySelectorAll('#igStatus')[0].classList.contains('ig-error'),true);
  }
});

test('successful owner replacement cannot carry disabled lesson nodes or unlock the new owner',async()=>{
  for(const foreignContext of [false,true]){
    const h=harness(),gate=deferred();const task=h.operation(()=>gate.promise);
    const next=h.mount({foreignContext,locked:true}),raw=structuredClone(h.attachment);h.moveLesson();
    gate.resolve();await task;
    assert.equal(h.seam.getState(),next.state);assert.equal(h.lesson.parentElement,h.canvas);h.lessonUntouched();
    assert.ok([next.input,next.select,next.save,next.preDisabled].every(control=>control.disabled),'stale finally must not unlock foreign controls');
    assert.equal(next.input.value,' Raw 001 ');assert.deepEqual(h.attachment,raw);
    assert.equal(h.calls.filter(([name])=>name==='application').length,0,'old finally cannot paint the replacement owner');
  }
});

test('project save locking is idempotent and restores only its owned controls after the lesson moves',()=>{
  const h=harness(),raw=structuredClone(h.attachment);h.ui.setProjectBusy(true);const snapshot=h.original.state.projectControls;
  assert.deepEqual(lockSnapshot(h.original,'projectControls').map(control=>control.id),h.original.controls.map(control=>control.id));
  h.ui.setProjectBusy(true);assert.equal(h.original.state.projectControls,snapshot,'nested busy notice does not overwrite original bits');
  assert.ok(h.original.controls.every(control=>control.disabled));h.lessonUntouched();h.moveLesson();h.ui.setProjectBusy(false);
  restored(h.original);h.lessonUntouched();assert.equal(h.original.state.projectControls,null);assert.deepEqual(h.attachment,raw);
  assert.deepEqual(h.calls.map(([name])=>name),['capture','sync']);
});

test('retiring a project-save owner leaves replacement raw and locks unchanged',()=>{
  const h=harness();h.ui.setProjectBusy(true);const next=h.mount({foreignContext:true,locked:true});h.moveLesson();h.ui.setProjectBusy(false);
  h.lessonUntouched();assert.equal(h.seam.getState(),next.state);
  assert.ok([next.input,next.select,next.save].every(control=>control.disabled));assert.equal(next.input.value,' Raw 001 ');
  assert.deepEqual(h.calls,[],'old project save completion cannot capture or sync the replacement');
});

async function heldConfirmation(h){
  h.setPending(true);await h.operation(async()=>{throw Error('receipt not yet known');});
  assert.equal(h.original.state.busy,false);assert.equal(h.original.close.disabled,false,'the established pending-result return action remains available');
  assert.ok(h.original.state.heldControls);return h.original.state;
}

test('held confirmation admission waits for the result and connection, then preserves rejected raw',async()=>{
  const h=harness(),raw=structuredClone(h.attachment),s=await heldConfirmation(h);
  assert.deepEqual(lockSnapshot(h.original,'heldControls').map(control=>control.id),h.original.controls.map(control=>control.id));h.lessonUntouched();
  await h.seam.releaseHeldControls(s);assert.deepEqual(h.calls,[],'unknown receipt is not released');
  h.setPending(false);h.connection.phase='disconnected';await h.seam.releaseHeldControls(s);assert.deepEqual(h.calls,[],'offline result is not released');
  h.connection.phase='ready';await h.seam.releaseHeldControls(s);
  assert.equal(s.heldControls,null);assert.equal(s.releasing,false);restored(h.original);h.lessonUntouched();assert.deepEqual(h.attachment,raw);
  assert.deepEqual(h.calls.map(([name])=>name),['application','sync']);
});

test('recovered native commit replaces the held owner without locking the shared lesson or releasing new controls',async()=>{
  const h=harness({holdRender:true}),s=await heldConfirmation(h);s.publishTarget={kind:'grid-system',id:0};h.setPending(false);h.setAttachment(null);
  const task=h.seam.releaseHeldControls(s);await h.renderReached;
  try{assert.equal(s.releasing,true);h.lessonUntouched();await h.seam.releaseHeldControls(s);assert.equal(h.calls.length,1,'recovery read is not duplicated');}
  finally{h.releaseRender();await task;}
  const next=h.active;assert.notEqual(next.state,s);assert.equal(s.releasing,false);h.moveLesson();h.lessonUntouched();
  assert.ok([next.input,next.select,next.save].every(control=>control.disabled),'recovery cannot release controls owned by reopened workspace');
  assert.deepEqual(h.calls.map(([name])=>name),['render','reveal','open']);
  assert.equal(h.calls[2][1].system,0);assert.equal(h.calls[2][2],true);assert.equal(h.attachment,null);
});

test('a replacement during held recovery read prevents old reveal or reopen and preserves new raw',async()=>{
  const h=harness({holdRender:true}),s=await heldConfirmation(h);s.publishTarget={kind:'grid-system',id:0};h.setPending(false);h.setAttachment(null);
  const task=h.seam.releaseHeldControls(s);await h.renderReached;
  const next=h.mount({foreignContext:true,locked:true}),newRaw={schema:'grid-editor-draft/1',rawForm:{igName:'New owner',igUStep:' 1e '}};h.setAttachment(newRaw);h.moveLesson();
  h.releaseRender();await task;
  assert.equal(h.seam.getState(),next.state);assert.equal(h.attachment,newRaw);h.lessonUntouched();
  assert.ok([next.input,next.select,next.save].every(control=>control.disabled));assert.deepEqual(h.calls.map(([name])=>name),['render']);
  assert.equal(s.releasing,false);
});

test('orphan restrictions keep raw mutations locked and Discard available without disabling the shared lesson on repeat sync',()=>{
  for(const mode of ['source','binding']){
    const h=harness({syncOrphan:true}),owner=h.mount({orphaned:true,mode}),raw=structuredClone(h.attachment);
    h.seam.syncOrphanDraft(owner.state);
    assert.ok([owner.input,owner.select,owner.save,owner.preDisabled].every(control=>control.disabled));assert.equal(owner.discard.disabled,false);h.lessonUntouched();
    h.ui.setProjectBusy(true);h.ui.setProjectBusy(false);
    assert.ok([owner.input,owner.select,owner.save,owner.preDisabled].every(control=>control.disabled));assert.equal(owner.discard.disabled,false);h.lessonUntouched();
    assert.deepEqual(h.attachment,raw);assert.equal(owner.input.value,' Raw 001 ');assert.match(h.dialog.querySelectorAll('#igTitle')[0].textContent,/已遺失/);
  }
});
