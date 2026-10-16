/* Actual workspace script in a Node VM. DOM/transport are fakes, not browser E2E.
 * The real ContextHistory checks the shared local/native undo ordering.
 * GEOMETRY_TEST_ASSEMBLY_WORKSPACE allows checking the same assertions on a baseline.
 */
'use strict';
const {test:nodeTest}=require('node:test'),assert=require('node:assert/strict');
const test=(name,fn)=>nodeTest(name,{timeout:5000},fn);
const fs=require('node:fs'),vm=require('node:vm');
const {ContextHistory}=require('../geometry-web/project-store.js');
const copy=structuredClone;
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const tick=()=>new Promise(r=>setImmediate(r));
const rule=()=>({id:1,version:1,name:'框',slots:[{id:1,name:'主支'},{id:2,name:'副支'}],members:[{id:1,slotId:1},{id:2,slotId:2},{id:3,slotId:2}],joints:[{id:1,kind:'end-to-side',scope:'one',targetMember:1,terminatedMember:2,end:'start',side:'+u',dir:'u'}]});
const draft=(id='draft-A')=>({id,kind:'rule',base_ref:null,data:rule(),updated_at:'2026-10-01T00:00:00.000Z'});
function fixture(options={}){
  const elements=new Map(),listeners=new Map(),calls=[],removed=[],gate=deferred();
  const element=id=>{if(!elements.has(id))elements.set(id,{id,disabled:false,hidden:false,innerHTML:'',textContent:'',dataset:{},classList:{toggle(){}},attrs:{},
    setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];},append(){},prepend(){},remove(){},
    addEventListener(name,fn){(this.handlers||={})[name]=fn;},querySelector:()=>null,querySelectorAll:()=>[],close(){this.open=false;},showModal(){this.open=true;}});return elements.get(id);};
  const dialog=element('dialog');dialog.open=true;dialog.querySelectorAll=selector=>selector==='button,input,select'?[...elements.values()].filter(e=>e!==dialog):[];
  for(const id of ['asmName','asmConfirm','asmPreview','asmCancel','asmClose','asmNewRule','projectSave','asmDiagram','asmStatus'])element(id);
  const history=new ContextHistory(()=>({id:crypto.randomUUID(),assemblyDrafts:[],models:[],faceProjections:new Map()}));
  const context=()=>history.frame.context;
  const frameTokens=new WeakMap(),token=()=>{if(!options.frameTokens)return context().id;if(!frameTokens.has(history.frame))frameTokens.set(history.frame,crypto.randomUUID());return frameTokens.get(history.frame);};
  context().assemblyDrafts=[draft(),draft('draft-B')];
  const notify=()=>listeners.get('project-info-changed')?.();
  const ref={escape:v=>String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'),context,
    getProjectState:()=>({contextToken:token()}),assertEditable(){},getAssemblyDrafts:()=>copy(context().assemblyDrafts),
    setAssemblyDraft(d,expectedToken){assert.equal(expectedToken,token());history.push(history.snapshot(),'local');const found=context().assemblyDrafts.some(x=>x.id===d.id);context().assemblyDrafts=context().assemblyDrafts.map(x=>x.id===d.id?copy(d):x);if(!found)context().assemblyDrafts.push(copy(d));notify();},
    removeAssemblyDraft(id,expectedToken,record=true){assert.equal(expectedToken,token());if(record)history.push(history.snapshot(),'local');removed.push(id);context().assemblyDrafts=context().assemblyDrafts.filter(d=>d.id!==id);notify();}};
  let result={ok:true},world={rules:[],bindings:[]},failRead=false,ids={assemblyRule:2,assemblyBinding:1};
  const env={GeometryApplication:options.application||require('../geometry-app/application.js'),ReferenceWorkspace:ref,structuredClone,crypto,Map,Set,console,AbortSignal,setTimeout,
    window:{ContextOperations:require('../geometry-web/context-operations.js'),addEventListener:(name,fn)=>listeners.set(name,fn)},document:{createElement:()=>dialog,body:{append(){}},getElementById:element},
    WorkspaceShell:{attach(){},detach(){},refresh(){}},placeStudioLesson(){},renderObjects:async()=>{},toast(){},connection:{phase:'ready'},
    apiRequest:async cmd=>{calls.push(cmd);if(cmd.startsWith('assembly-confirm ')){await gate.promise;history.observe(cmd,result);notify();return result;}
      if(cmd==='assembly-read'){if(failRead){failRead=false;env.connection.phase='error';return {ok:false,transport:true,error:'Refresh unavailable'};}return {ok:true,revision:1,state:copy(world)};}
      if(cmd==='engineering-read')return {ok:true,revision:1,state:{materials:[],parameters:[]}};
      if(cmd==='newid')return {ok:true,...ids};
      return {ok:true,specs:[]};}};
  let source=fs.readFileSync(process.env.GEOMETRY_TEST_ASSEMBLY_WORKSPACE||require.resolve('../geometry-web/assembly-workspace.js'),'utf8');
  source=source.replace('return {open,close,flush,card,inspector,remove,','return {test:{setState:x=>s=x,getState:()=>s,confirm,diagram,preview,previewCopy,render,safe,changed,newDraft,newInstance},open,close,flush,card,inspector,remove,');
  vm.runInNewContext(source,env);const w=env.window.AssemblyWorkspace,t=w.test;
  const state={context:token(),generation:1,draft:copy(context().assemblyDrafts[0]),draftsRef:context().assemblyDrafts,read:{state:world},engineering:{parameters:[],materials:[],specs:[]},preview:{valid:true,token:'candidate-A'},rotation:0,zoom:1};t.setState(state);
  return {w,t,state,context,history,ref,calls,removed,gate,element,env,notify,notifyLocal:previousContextToken=>listeners.get('project-local-history')?.({detail:{previousContextToken,contextToken:token()}}),setResult:r=>result=r,setWorld:w=>world=w,captureWorld:()=>{state.read={revision:1,state:copy(world)};},setIds:v=>ids=v,failNextRead:()=>failRead=true};
}

const bindingValue=id=>({id,name:'配置',rule:{id:1,version:1},slots:[1,2].map(slotId=>({slotId,A:null,B:null,contactFace:null,orientation:null}))});
const instanceRule=()=>({...rule(),joints:[
  {id:1,kind:'end-to-side',scope:'one',targetMember:1,terminatedMember:2,end:'start',side:'+u',dir:'u'},
  {id:2,kind:'end-to-side',scope:'one',targetMember:3,terminatedMember:2,end:'finish',side:'-u',dir:'u'},
]});
function instanceFixture(options={}){
  const f=fixture(options),r={value:instanceRule(),fingerprint:'a'.repeat(64)},b={value:bindingValue(4),complete:true};
  f.setWorld({rules:[r],bindings:[b],instances:[]});f.setIds({assemblyInstance:7});
  return {...f,r,b};
}
test('actual instance creation consumes the template before ID allocation and preserves host provenance',async()=>{
  const seen=[],members=[{memberId:9,role:'custom',guideId:0,dir:'-v',depthSide:'-n',ends:{start:{kind:'timber',id:0},finish:{kind:'timber',id:0}}}];
  const f=instanceFixture({application:{woodworking:{assemblyInstanceMembers(r){seen.push(copy(r));assert.ok(!f.calls.includes('newid'));return copy(members);}}}});
  await f.t.newInstance(4);const d=f.state.draft;
  assert.deepEqual(seen,[f.r.value]);assert.deepEqual(copy(d.data.members),members);
  assert.equal(d.data.id,7);assert.equal(d.data.bindingId,4);assert.equal(d.data.name,'配置・角材');
  assert.deepEqual(copy(d.data.rule),{id:1,version:1,fingerprint:'a'.repeat(64)});
  assert.equal(d.data.surfaceId,0);assert.equal(d.base_ref,null);assert.equal(f.calls.filter(c=>c==='newid').length,1);
});
test('instance policy rejection preserves the old draft and preview before ID allocation',async()=>{
  for(const change of [r=>r.members.pop(),r=>r.joints[0].kind='ortho-split',r=>r.joints[1].terminatedMember=3,r=>r.joints[1].end='start']){
    const f=instanceFixture();change(f.r.value);f.setWorld({rules:[f.r],bindings:[f.b],instances:[]});
    const before=localSnapshot(f);await assert.rejects(f.t.newInstance(4),/首版只支援|副支必須/);
    assert.equal(localSnapshot(f),before);assert.ok(!f.calls.some(c=>c==='newid'||c.startsWith('assembly-cancel ')));
  }
});
test('editing saved instance data bypasses creation defaults and retains its exact fingerprint',async()=>{
  const f=instanceFixture({application:{woodworking:{assemblyInstanceMembers(){assert.fail('saved data must not receive creation defaults');}}}});
  const source={id:7,name:'已儲存',bindingId:4,rule:{id:1,version:1,fingerprint:'a'.repeat(64)},surfaceId:31,
    members:[{memberId:1,role:'primary',guideId:12,dir:'-v',depthSide:'-n',ends:{start:{kind:'timber',id:50},finish:{kind:'timber',id:51}}}]};
  const record={value:{source},fingerprint:'b'.repeat(64)};
  f.setWorld({rules:[f.r],bindings:[f.b],instances:[record]});await f.t.newInstance(4,record);
  assert.deepEqual(copy(f.state.draft.data),source);assert.deepEqual(copy(f.state.draft.base_ref),{id:7,fingerprint:record.fingerprint});
  f.state.draft.data.name='修改';assert.equal(source.name,'已儲存');assert.ok(!f.calls.includes('newid'));
});
test('late instance allocation discards its result after a local edit',async()=>{
  const f=instanceFixture(),gate=deferred(),original=f.env.apiRequest;
  f.env.apiRequest=async cmd=>{if(cmd==='newid')await gate.promise;return original(cmd);};
  const pending=f.t.newInstance(4);await tick();f.state.draft.data.name='後續編輯';f.state.generation++;
  const before=localSnapshot(f);gate.resolve();await pending;assert.equal(localSnapshot(f),before);
});
test('confirming and incomplete bindings do not request instance recipes or IDs',async()=>{
  for(const confirming of [false,true]){
    const f=instanceFixture({application:{woodworking:{assemblyInstanceMembers(){assert.fail('blocked creation must not request defaults');}}}});
    if(confirming){f.state.confirming={};await f.t.newInstance(4);assert.deepEqual(f.calls,[]);}
    else{f.b.complete=false;f.setWorld({rules:[f.r],bindings:[f.b],instances:[]});await assert.rejects(f.t.newInstance(4),/請先選齊材料配置/);}
    assert.ok(!f.calls.includes('newid'));
  }
});
test('actual binding switch consumes injected compatibility and endpoint policies',async()=>{
  const calls=[],template={...require('../geometry-app/application.js').woodworking,
    canRetargetAssemblyInstance(members,r){calls.push(['compatibility',copy(members),copy(r)]);return true;},
    assemblyInstanceEnd(r,end){calls.push(['endpoint',end]);return {kind:'member',memberId:end==='start'?71:73};}};
  const f=instanceFixture({application:{woodworking:template}});await f.t.newInstance(4);
  const b2={value:{...bindingValue(8),rule:{id:1,version:2}},complete:true},r2={value:{...instanceRule(),version:2},fingerprint:'c'.repeat(64)};
  f.state.read.state.bindings.push(b2);f.state.read.state.rules.push(r2);f.t.render();
  await f.element('asmInstanceBinding').handlers.change({target:{value:'8'}});
  assert.equal(f.state.draft.data.bindingId,8);assert.equal(f.state.draft.data.rule.fingerprint,r2.fingerprint);
  assert.deepEqual(copy(f.state.draft.data.members.find(m=>m.role==='secondary').ends),{start:{kind:'member',memberId:71},finish:{kind:'member',memberId:73}});
  assert.equal(calls[0][0],'compatibility');assert.deepEqual(calls.slice(1),[['endpoint','start'],['endpoint','finish']]);
});
function contextFixture(){
  const f=fixture(),record={value:rule(),fingerprint:'a'.repeat(64)};
  f.setWorld({capabilities:['assembly-rule-authoring/1'],rules:[record,{value:{...rule(),version:2},fingerprint:'b'.repeat(64)}],bindings:[]});
  f.selection={kind:'assembly-rule',id:1,version:1,fingerprint:record.fingerprint};return f;
}
const localSnapshot=f=>JSON.stringify({drafts:f.context().assemblyDrafts,active:f.state.draft,preview:f.state.preview,generation:f.state.generation,undo:f.history.undo.length,redo:f.history.redo.length});
test('context entry pins the displayed exact version and leaves all material input explicitly unset',async()=>{
  const f=contextFixture();assert.equal(await f.w.createBindingFromRule(f.selection,()=>true),true);
  const d=f.t.getState().draft;assert.equal(d.data.rule.id,1);assert.equal(d.data.rule.version,1);assert.equal(d.base_ref.fingerprint,'a'.repeat(64));
  assert.equal(d.binding_intent.mode,'create');assert.ok(d.data.slots.every(v=>v.A===null&&v.B===null&&v.contactFace===null&&v.orientation===null));
  assert.equal(f.calls.filter(c=>c==='newid').length,1);assert.equal(f.calls.filter(c=>c==='assembly-cancel candidate-A').length,1);
});
test('same tuple changed or missing context source rejects before old input flush token cancellation and native allocation',async()=>{
  for(const kind of ['changed','missing','invalid-pin','capability','unchecked']){
    const f=contextFixture();f.state.draft.data.name='未失焦舊輸入';
    const world={capabilities:['assembly-rule-authoring/1'],rules:[{value:rule(),fingerprint:'a'.repeat(64)}],bindings:[]};
    if(kind==='changed')world.rules[0].fingerprint='c'.repeat(64);
    if(kind==='missing')world.rules=[];
    if(kind==='invalid-pin')f.selection.fingerprint=null;
    if(kind==='capability')world.capabilities=['assembly-timber-generation/1'];
    if(kind==='unchecked')delete world.capabilities;
    f.setWorld(world);const before=localSnapshot(f);
    await assert.rejects(f.w.createBindingFromRule(f.selection,()=>true));
    assert.equal(localSnapshot(f),before);assert.equal(f.calls.filter(c=>c==='newid'||c.startsWith('assembly-cancel ')).length,0);
  }
});
test('a repeated rejected context entry keeps the original displayed fingerprint',async()=>{
  const f=contextFixture();f.setWorld({capabilities:['assembly-rule-authoring/1'],rules:[{value:rule(),fingerprint:'b'.repeat(64)}],bindings:[]});const before=localSnapshot(f);
  for(let i=0;i<2;i++)await assert.rejects(f.w.createBindingFromRule(f.selection,()=>true));
  assert.equal(localSnapshot(f),before);assert.equal(f.selection.fingerprint,'a'.repeat(64));assert.ok(!f.calls.includes('newid'));
});
test('late context entry discards results after selection project or old-owner edit changes',async()=>{
  for(const change of ['selection','project','edit','close-reopen']){
    const f=contextFixture(),gate=deferred(),original=f.env.apiRequest;let selected=true,held=false;
    f.env.apiRequest=async cmd=>{if(cmd==='assembly-read'&&!held){held=true;await gate.promise;}return original(cmd);};
    const pending=f.w.createBindingFromRule(f.selection,()=>selected);await tick();
    if(change==='selection')selected=false;
    if(change==='project')f.history.frame={context:{id:'different-project',assemblyDrafts:[draft('different-draft')],models:[],faceProjections:new Map()},ids:new Map()};
    if(change==='edit'){f.state.draft.data.name='後續輸入';f.state.generation++;}
    if(change==='close-reopen'){f.w.close();await f.w.open();}
    const before=JSON.stringify(f.context().assemblyDrafts),undo=f.history.undo.length;
    gate.resolve();assert.equal(await pending,false);assert.equal(JSON.stringify(f.context().assemblyDrafts),before);assert.equal(f.history.undo.length,undo);assert.ok(!f.calls.includes('newid'));
  }
});
test('double context activation creates only one draft and one native ID request',async()=>{
  const f=contextFixture(),gate=deferred(),original=f.env.apiRequest;let held=false;
  f.env.apiRequest=async cmd=>{if(cmd==='assembly-read'&&!held){held=true;await gate.promise;}return original(cmd);};
  const first=f.w.createBindingFromRule(f.selection,()=>true);await tick();assert.equal(await f.w.createBindingFromRule(f.selection,()=>true),false);gate.resolve();assert.equal(await first,true);
  assert.equal(f.context().assemblyDrafts.filter(d=>d.kind==='binding').length,1);assert.equal(f.calls.filter(c=>c==='newid').length,1);
});
test('declining the existing leave gate preserves the old draft owner and pending token',async()=>{
  const f=contextFixture();f.env.window.DraftGate={ask:()=>false};const before=localSnapshot(f);
  assert.equal(await f.w.createBindingFromRule(f.selection,()=>true),false);assert.equal(localSnapshot(f),before);assert.equal(f.calls.filter(c=>c.startsWith('assembly-cancel ')).length,0);
});
function idFixture(kind,occupied,reserved,start){
  const f=fixture();f.state.draft=null;f.state.preview=null;
  const rules=kind==='rule'?occupied.map(id=>({value:{...rule(),id},fingerprint:'a'.repeat(64)})):[{value:rule(),fingerprint:'a'.repeat(64)}];
  f.setWorld({rules,bindings:kind==='binding'?occupied.map(id=>({value:bindingValue(id),fingerprint:'b'.repeat(64)})):[]});
  f.captureWorld();
  f.context().assemblyDrafts=reserved.map(id=>({id:'reserved-'+id,kind,base_ref:null,data:kind==='rule'?{...rule(),id}:bindingValue(id),updated_at:'2026-10-01T00:00:00Z'}));
  f.setIds({assemblyRule:start,assemblyBinding:start});return f;
}
test('new and copied rules/bindings skip interleaved native and draft IDs after uint32 wrap',async()=>{
  for(const kind of ['rule','binding'])for(const copied of [false,true]){
    const f=idFixture(kind,[2,4,0xffffffff],[1,3,5],1),source=copied&&kind==='rule'?{value:{...rule(),id:2},fingerprint:'a'.repeat(64)}:null;
    const before=JSON.stringify(f.context().assemblyDrafts);await f.t.newDraft(kind,source);
    assert.equal(f.state.draft.data.id,6);assert.equal(JSON.stringify(f.context().assemblyDrafts.slice(0,3)),before);
    if(kind==='binding')assert.equal(f.state.draft.binding_intent.mode,'create');
    if(source){assert.equal(source.value.id,2);assert.deepEqual(f.state.draft.data.joints,source.value.joints);}
  }
});
test('reserved MAX wraps to a positive free ID without exceeding uint32',async()=>{
  for(const kind of ['rule','binding']){const f=idFixture(kind,[1,3],[0xffffffff,2],0xffffffff);await f.t.newDraft(kind);assert.equal(f.state.draft.data.id,4);}
});
test('new rule versions retain identity, reserve draft versions and reject the version ceiling atomically',async()=>{
  const source={value:rule(),fingerprint:'a'.repeat(64)},f=idFixture('rule',[1],[1],2);
  f.context().assemblyDrafts[0].data.version=2;await f.t.newDraft('rule',source,true);
  assert.equal(f.state.draft.data.id,1);assert.equal(f.state.draft.data.version,3);assert.equal(f.state.draft.base_ref.fingerprint,source.fingerprint);
  f.context().assemblyDrafts[0].data.version=0xffffffff;
  const before=JSON.stringify(f.context().assemblyDrafts),active=f.state.draft.id;
  await assert.rejects(f.t.newDraft('rule',source,true),/版本已達上限/);
  assert.equal(f.state.draft.id,active);assert.equal(JSON.stringify(f.context().assemblyDrafts),before);
});
test('local slot/member/joint controls wrap MAX without changing existing identities',async()=>{
  const f=fixture(),d=f.state.draft.data;
  d.slots=[{id:0xffffffff,name:'極限槽位'}];d.members=[{id:1,slotId:0xffffffff},{id:0xffffffff,slotId:0xffffffff}];
  d.joints=[{...d.joints[0],id:0xffffffff,targetMember:1,terminatedMember:0xffffffff}];f.t.render();
  for(const [button,list,id] of [['asmAddSlot','slots',1],['asmAddMember','members',2],['asmAddJoint','joints',1]]){
    await f.element(button).handlers.click();assert.equal(d[list].at(-1).id,id);assert.ok(d[list].some(item=>item.id===0xffffffff));
  }
});
test('a new or legacy binding draft never previews an update to a subsequently occupied ID',async()=>{
  for(const legacy of [false,true]){const f=idFixture('binding',[],[],1);await f.t.newDraft('binding');
    if(legacy)delete f.state.draft.binding_intent;
    f.setWorld({rules:[{value:rule()}],bindings:[{value:bindingValue(1)}]});
    const before=JSON.stringify(f.context().assemblyDrafts);f.env.fetch=()=>{throw Error('must not submit');};
    await assert.rejects(f.t.preview(),/身分已被占用/);assert.equal(JSON.stringify(f.context().assemblyDrafts),before);assert.equal(f.state.preview,null);
  }
});
test('explicit binding edits keep identity and reject changed, removed or replaced source values',async()=>{
  for(const changed of ['changed','removed','replaced']){
    const f=idFixture('binding',[2],[],3),source={value:bindingValue(2)};await f.t.newDraft('binding',source);
    assert.equal(f.state.draft.data.id,2);assert.equal(f.state.draft.binding_intent.mode,'update');
    assert.deepEqual(f.state.draft.binding_intent.source,source.value);f.state.draft.data.name='編輯值';
    f.setWorld({rules:[{value:rule()}],bindings:changed==='removed'?[]:[{value:{...bindingValue(2),name:changed}}]});
    f.env.fetch=()=>{throw Error('must not submit');};await assert.rejects(f.t.preview(),/原始配置已變更或移除/);
    assert.equal(f.state.draft.data.name,'編輯值');assert.equal(f.state.preview,null);
  }
});
test('unchanged explicit binding edits and unoccupied legacy creations reach revision-scoped preview',async()=>{
  for(const editing of [false,true]){
    const f=idFixture('binding',editing?[2]:[],[],3);await f.t.newDraft('binding',editing?{value:bindingValue(2)}:null);
    if(!editing)delete f.state.draft.binding_intent;
    else f.state.draft.binding_intent.source=Object.fromEntries(Object.entries(f.state.draft.binding_intent.source).reverse());
    f.state.draft.data.name='確定編輯';let submitted;f.env.checkApiSession=()=>{};
    f.env.fetch=async(url,request)=>{submitted=JSON.parse(request.body);return {ok:true,json:async()=>({ok:true,preview:{token:'p',valid:true,impact:{schema:'candidate-geometry/1',timbers:[],guides:[]},before:{rules:[],bindings:[]},after:{rules:[],bindings:[]},violations:[]}})};};
    await f.t.preview();assert.equal(submitted.expectedRevision,1);assert.equal(submitted.operations[0].value.id,editing?2:3);assert.equal(f.state.preview.valid,true);
    assert.equal(submitted.operations[0].op,editing?'edit-binding':'create-binding');
    if(editing){assert.equal(submitted.operations[0].id,2);assert.equal(submitted.operations[0].expectedFingerprint,'b'.repeat(64));}
  }
});
test('missing native binding fingerprint refuses an explicit edit without submitting or discarding its draft',async()=>{
  const f=idFixture('binding',[2],[],3);await f.t.newDraft('binding',{value:bindingValue(2)});
  f.setWorld({rules:[{value:rule()}],bindings:[{value:bindingValue(2)}]});
  f.env.fetch=()=>{throw Error('must not submit');};const before=JSON.stringify(f.context().assemblyDrafts);
  await assert.rejects(f.t.preview(),/缺少配置來源指紋/);assert.equal(JSON.stringify(f.context().assemblyDrafts),before);assert.equal(f.state.preview,null);
});

const publishedRule=(value=rule(),fingerprint='a'.repeat(64))=>({value,fingerprint});
test('binding creation rejects replaced or removed captured rules without changing the active draft or history',async()=>{
  for(const removed of [false,true]){
    const f=fixture(),source=publishedRule(),fresh=publishedRule({...rule(),joints:rule().joints.map(j=>({...j,side:'-u'}))},'b'.repeat(64));
    f.setWorld({rules:removed?[]:[fresh],bindings:[]});
    f.state.draft.data.name='尚未 flush 的原草稿';
    const before=JSON.stringify(f.context().assemblyDrafts),active=JSON.stringify(f.state.draft),preview=f.state.preview,history=f.history.undo.length;
    await assert.rejects(f.t.newDraft('binding',source),/原始規則版本已變更或移除/);
    assert.equal(JSON.stringify(f.context().assemblyDrafts),before);assert.equal(JSON.stringify(f.state.draft),active);
    assert.equal(f.history.undo.length,history);assert.equal(f.state.preview,preview);
    assert.ok(!f.calls.some(c=>c==='newid'||c.startsWith('assembly-preview')||c.startsWith('assembly-cancel')));
  }
});
test('binding creation refuses malformed fixed rule identities and absent native fingerprints',async()=>{
  const bad=[r=>r.value.id=0,r=>r.value.id=0x100000000,r=>r.value.id=1.5,r=>r.value.version=0,r=>r.value.version=0x100000000,
    r=>r.fingerprint=null,r=>r.fingerprint='a'.repeat(63),r=>r.fingerprint='A'.repeat(64),r=>r.fingerprint='z'.repeat(64),r=>r.fingerprint=['a'.repeat(64)]];
  for(const mutate of bad){const f=fixture(),source=publishedRule();mutate(source);f.setWorld({rules:[copy(source)],bindings:[]});
    const active=JSON.stringify(f.state.draft),before=JSON.stringify(f.context().assemblyDrafts);
    await assert.rejects(f.t.newDraft('binding',source),/固定規則來源不合法/);
    assert.equal(JSON.stringify(f.state.draft),active);assert.equal(JSON.stringify(f.context().assemblyDrafts),before);assert.equal(f.history.undo.length,0);
  }
  const f=fixture();f.setWorld({rules:[{value:rule()}],bindings:[]});
  await assert.rejects(f.t.newDraft('binding'),/固定規則來源不合法/);
});
test('new binding drafts retain the exact fresh rule provenance for both selected and null-source creation',async()=>{
  for(const selected of [false,true]){const f=idFixture('binding',[],[],3),source=publishedRule();await f.t.newDraft('binding',selected?source:null);
    assert.deepEqual(copy(f.state.draft.base_ref),{id:1,version:1,fingerprint:source.fingerprint});
    assert.deepEqual(copy(f.state.draft.data.rule),{id:1,version:1});assert.equal(f.state.draft.binding_intent.mode,'create');
    for(const slot of f.state.draft.data.slots)for(const field of ['A','B','contactFace','orientation'])assert.equal(slot[field],null);
    const P=require('../geometry-web/project-store.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
    const bytes=await P.pack('reset\n',{projectId:'fixed-binding',name:'組構',sources:[],faces:[],assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[copy(f.state.draft)]}},new Map(),zip);
    const archive=await P.unpack(bytes,zip);assert.equal(archive.manifest.format,P.ASSEMBLY_FORMAT);
    assert.deepEqual(archive.manifest.assemblyDrafts.records[0],copy(f.state.draft));
  }
});
test('binding preview rejects changed, removed, or mismatched captured rule provenance before any submission',async()=>{
  for(const changed of ['replaced','removed','mismatched']){const f=idFixture('binding',[],[],3);await f.t.newDraft('binding',publishedRule());
    f.state.draft.data.name='保留配置';f.w.flush();
    const fresh=publishedRule({...rule(),joints:rule().joints.map(j=>({...j,side:'-u'}))},'b'.repeat(64));
    if(changed==='mismatched'){f.state.draft.data.rule.version=2;f.w.flush();f.setWorld({rules:[publishedRule(),publishedRule({...rule(),version:2})],bindings:[]});}
    else f.setWorld({rules:changed==='removed'?[]:[fresh],bindings:[]});
    const before=JSON.stringify(f.context().assemblyDrafts),active=JSON.stringify(f.state.draft),history=f.history.undo.length;
    let sends=0;f.env.fetch=()=>{sends++;throw Error('unexpected submission');};
    await assert.rejects(f.t.preview(),/材料配置的規則來源已變更或移除/);
    assert.equal(sends,0);assert.equal(JSON.stringify(f.context().assemblyDrafts),before);assert.equal(JSON.stringify(f.state.draft),active);
    assert.equal(f.history.undo.length,history);assert.equal(f.state.preview,null);
  }
});
test('explicit binding rule mapping captures only the applied selection and persists provenance-only changes',async()=>{
  const f=idFixture('binding',[],[],3);await f.t.newDraft('binding',publishedRule());
  const old=copy(f.state.draft.base_ref),fresh=publishedRule(rule(),'b'.repeat(64));f.state.read.state.rules=[fresh];
  const before=JSON.stringify(f.state.draft.data);f.t.render();f.element('asmBindingRule').value='1:1';await f.element('asmBindingRule').handlers.change();
  assert.deepEqual(copy(f.state.draft.base_ref),old);await f.element('asmCancelMapping').handlers.click();assert.deepEqual(copy(f.state.draft.base_ref),old);
  f.element('asmBindingRule').value='1:1';await f.element('asmBindingRule').handlers.change();
  for(const slot of fresh.value.slots)f.element('asmMap'+slot.id).value=String(slot.id);
  await f.element('asmApplyMapping').handlers.click();
  assert.equal(JSON.stringify(f.state.draft.data),before);assert.deepEqual(copy(f.state.draft.base_ref),{id:1,version:1,fingerprint:fresh.fingerprint});
  assert.deepEqual(f.context().assemblyDrafts.find(d=>d.id===f.state.draft.id).base_ref,copy(f.state.draft.base_ref));
  f.setWorld({rules:[fresh],bindings:[]});let submitted;f.env.checkApiSession=()=>{};
  f.env.fetch=async(url,request)=>{submitted=JSON.parse(request.body);return {ok:true,json:async()=>({ok:true,preview:{token:'new',valid:true,impact:{schema:'candidate-geometry/1',timbers:[],guides:[]},before:{rules:[],bindings:[]},after:{rules:[],bindings:[]},violations:[]}})};};
  await f.t.preview();assert.equal(submitted.operations[0].op,'create-binding');assert.equal(f.state.preview.valid,true);
});
test('legacy null rule provenance still previews through native validation and existing binding edits keep their intent',async()=>{
  for(const edit of [false,true]){const f=idFixture('binding',edit?[2]:[],[],3);await f.t.newDraft('binding',edit?{value:bindingValue(2)}:null);
    f.state.draft.base_ref=null;f.state.draft.data.name='既有相容';let submitted;f.env.checkApiSession=()=>{};
    f.env.fetch=async(url,request)=>{submitted=JSON.parse(request.body);return {ok:true,json:async()=>({ok:true,preview:{token:'legacy',valid:true,impact:{schema:'candidate-geometry/1',timbers:[],guides:[]},before:{rules:[],bindings:[]},after:{rules:[],bindings:[]},violations:[]}})};};
    await f.t.preview();assert.equal(submitted.operations[0].op,edit?'edit-binding':'create-binding');
    if(edit){assert.equal(f.state.draft.binding_intent.mode,'update');assert.deepEqual(f.state.draft.binding_intent.source,bindingValue(2));}
  }
});
test('binding rule provenance accepts uint32 MAX and rejects malformed stored refs before preview submission',async()=>{
  const f=idFixture('binding',[],[],3),source=publishedRule({...rule(),id:0xffffffff,version:0xffffffff});f.setWorld({rules:[source],bindings:[]});
  await f.t.newDraft('binding',source);assert.deepEqual(copy(f.state.draft.base_ref),{id:0xffffffff,version:0xffffffff,fingerprint:source.fingerprint});
  for(const mutate of [ref=>ref.id=0,ref=>ref.version=0,ref=>ref.fingerprint='A'.repeat(64),ref=>ref.fingerprint=['a'.repeat(64)]]){
    const g=idFixture('binding',[],[],3);await g.t.newDraft('binding');mutate(g.state.draft.base_ref);g.w.flush();
    const before=JSON.stringify(g.context().assemblyDrafts);let sends=0;g.env.fetch=()=>{sends++;throw Error('unexpected submission');};
    await assert.rejects(g.t.preview(),/材料配置的規則來源已變更或移除/);assert.equal(sends,0);assert.equal(JSON.stringify(g.context().assemblyDrafts),before);
  }
});
test('explicit new-version mapping keeps typed sources and its fixed provenance through undo and redo',async()=>{
  const f=idFixture('binding',[],[],3),old=publishedRule(),fresh=publishedRule({...rule(),version:2,slots:[{id:7,name:'新主支'},{id:8,name:'新副支'}]},'b'.repeat(64));
  f.setWorld({rules:[old,fresh],bindings:[]});await f.t.newDraft('binding',old);
  f.state.draft.data.slots[0].A={kind:'parameter',parameterId:0,fieldId:0};f.state.draft.data.slots[1].B={kind:'material',id:4,version:2,field:'B'};f.w.flush();
  const previous=copy(f.state.draft);f.t.render();f.element('asmBindingRule').value='1:2';await f.element('asmBindingRule').handlers.change();
  f.element('asmMap7').value='1';f.element('asmMap8').value='2';await f.element('asmApplyMapping').handlers.click();
  const applied=copy(f.state.draft);assert.deepEqual(applied.data.rule,{id:1,version:2});assert.deepEqual(applied.base_ref,{id:1,version:2,fingerprint:fresh.fingerprint});
  assert.deepEqual(applied.data.slots[0].A,previous.data.slots[0].A);assert.deepEqual(applied.data.slots[1].B,previous.data.slots[1].B);
  assert.deepEqual(applied.data.slots.map(s=>s.slotId),[7,8]);
  assert.equal(f.history.step('undo'),true);f.notify();assert.deepEqual(copy(f.state.draft),previous);
  assert.equal(f.history.step('redo'),true);f.notify();assert.deepEqual(copy(f.state.draft),applied);
  const live=fixture({frameTokens:true}),initial=copy(live.state.draft);
  live.state.draft.data.name='follow local undo';live.w.flush();const edited=copy(live.state.draft),firstToken=live.state.context;
  assert.equal(live.history.step('undo'),true);live.notifyLocal(firstToken);live.notify();
  assert.equal(live.w.isOpen,true);assert.deepEqual(copy(live.state.draft),initial);assert.notEqual(live.state.context,firstToken);
  const undoToken=live.state.context;assert.equal(live.history.step('redo'),true);live.notifyLocal(undoToken);live.notify();
  assert.equal(live.w.isOpen,true);assert.deepEqual(copy(live.state.draft),edited);
  const originalContext=live.context();live.history.replace({id:'other-project',assemblyDrafts:[],models:[],faceProjections:new Map()});live.notify();assert.equal(live.w.isOpen,false);
  live.history.step('undo');assert.equal(live.context(),originalContext);live.notify();assert.equal(live.w.isOpen,false);
  const pending=fixture({frameTokens:true}),readGate=deferred(),request=pending.env.apiRequest;
  pending.state.draft.data.name='pending reopen';pending.w.flush();
  pending.env.apiRequest=cmd=>cmd==='assembly-read'?readGate.promise:request(cmd);
  const reopening=pending.w.open(),rejected=assert.rejects(reopening,/專案或工作區已切換/),pendingToken=pending.ref.getProjectState().contextToken;
  assert.equal(pending.history.step('undo'),true);pending.notifyLocal(pendingToken);pending.notify();
  assert.equal(pending.w.isOpen,false);readGate.resolve({ok:true,revision:1,state:{rules:[],bindings:[]}});await rejected;
  assert.equal(pending.w.isOpen,false);
});
test('late binding allocation after a project switch never inserts its captured rule into the new project',async()=>{
  const f=fixture(),source=publishedRule(),allocation=deferred(),original=f.env.apiRequest;f.setWorld({rules:[source],bindings:[]});
  f.env.apiRequest=async cmd=>{const result=await original(cmd);if(cmd==='newid')await allocation.promise;return result;};
  const oldContext=f.context(),before=JSON.stringify(oldContext.assemblyDrafts),pending=f.t.newDraft('binding',source);await tick();
  const next={id:'other-context',assemblyDrafts:[draft('unrelated')],models:[],faceProjections:new Map()};f.history.frame={context:next,ids:new Map()};f.notify();
  allocation.resolve();await pending;assert.equal(JSON.stringify(oldContext.assemblyDrafts),before);assert.deepEqual(next.assemblyDrafts,[draft('unrelated')]);
  assert.equal(f.history.undo.length,0);assert.equal(f.w.isOpen,false);
});

test('published binding edits reject changed captured rule contents before flushing or allocating',async()=>{
  for(const removed of [false,true]){
    const f=fixture(),source={value:bindingValue(2),fingerprint:'b'.repeat(64)},old=publishedRule();
    f.setWorld({rules:[old],bindings:[source]});f.captureWorld();
    f.state.draft.data.name='尚未 flush 的原草稿';
    const before=JSON.stringify(f.context().assemblyDrafts),active=JSON.stringify(f.state.draft),preview=f.state.preview;
    const replacement=publishedRule({...rule(),joints:rule().joints.map(j=>({...j,side:'-u'}))},'c'.repeat(64));
    f.setWorld({rules:removed?[]:[replacement],bindings:removed?[]:[copy(source)]});
    await assert.rejects(f.t.newDraft('binding',source),/固定規則版本已變更或移除/);
    assert.equal(JSON.stringify(f.context().assemblyDrafts),before);assert.equal(JSON.stringify(f.state.draft),active);
    assert.equal(f.history.undo.length,0);assert.equal(f.state.preview,preview);
    assert.ok(!f.calls.some(c=>c==='newid'||c.startsWith('assembly-cancel')||c.startsWith('assembly-preview')));
  }
});
test('published binding edits require a valid previously displayed native rule fingerprint',async()=>{
  for(const missing of [false,true]){
    const f=idFixture('binding',[2],[],3),source={value:bindingValue(2),fingerprint:'b'.repeat(64)};
    if(missing)f.state.read.state.rules=[];else f.state.read.state.rules[0].fingerprint=null;
    const before=JSON.stringify(f.context().assemblyDrafts);
    await assert.rejects(f.t.newDraft('binding',source),/固定規則來源不合法/);
    assert.equal(JSON.stringify(f.context().assemblyDrafts),before);assert.equal(f.history.undo.length,0);
    assert.equal(f.state.draft,null);assert.deepEqual(f.calls,[]);
  }
});
test('repeated published binding edit attempts retain the first captured rule despite fresh reads',async()=>{
  const f=idFixture('binding',[2],[],3),source={value:bindingValue(2),fingerprint:'b'.repeat(64)};
  f.setWorld({rules:[publishedRule({...rule(),joints:rule().joints.map(j=>({...j,side:'-u'}))},'c'.repeat(64))],bindings:[copy(source)]});
  const before=JSON.stringify(f.context().assemblyDrafts);
  for(let attempt=0;attempt<2;attempt++)await assert.rejects(f.t.newDraft('binding',source),/固定規則版本已變更或移除/);
  assert.equal(f.state.read.state.rules[0].fingerprint,'c'.repeat(64));
  assert.equal(f.state.draft,null);assert.equal(JSON.stringify(f.context().assemblyDrafts),before);assert.equal(f.history.undo.length,0);
  assert.ok(!f.calls.some(c=>c==='newid'||c.startsWith('assembly-cancel')||c.startsWith('assembly-preview')));
});
test('published edit handlers pin the displayed rule before any refresh and reject repeated old UI clicks',async()=>{
  for(const refreshedBeforeClick of [false,true]){
    const f=idFixture('binding',[2],[],3),source={value:bindingValue(2),fingerprint:'b'.repeat(64),complete:false,effective:[]};
    f.setWorld({rules:[publishedRule()],bindings:[source]});f.captureWorld();
    f.state.record=f.state.read.state.bindings[0];f.state.kind='assembly-binding';f.t.render();
    const click=f.element('asmEdit').handlers.click,before=JSON.stringify(f.context().assemblyDrafts);
    const fresh=publishedRule({...rule(),joints:rule().joints.map(j=>({...j,side:'-u'}))},'c'.repeat(64));
    f.setWorld({rules:[fresh],bindings:[copy(source)]});if(refreshedBeforeClick)f.captureWorld();
    for(let attempt=0;attempt<2;attempt++){await click();assert.equal(f.state.draft,null);assert.match(f.element('asmStatus').textContent,/固定規則版本已變更或移除/);}
    assert.equal(JSON.stringify(f.context().assemblyDrafts),before);assert.equal(f.history.undo.length,0);
    assert.ok(!f.calls.some(c=>c==='newid'||c.startsWith('assembly-cancel')||c.startsWith('assembly-preview')));
    await f.w.open('assembly-binding',2);await f.element('asmEdit').handlers.click();
    const reopened=f.t.getState();assert.equal(reopened.draft.binding_intent.mode,'update');
    assert.deepEqual(copy(reopened.draft.base_ref),{id:1,version:1,fingerprint:fresh.fingerprint});
  }
});
test('a missing displayed rule fingerprint cannot be upgraded by retry but a fresh reopen can edit',async()=>{
  for(const missing of [false,true]){
    const f=idFixture('binding',[2],[],3),source={value:bindingValue(2),fingerprint:'b'.repeat(64),complete:false,effective:[]};
    const old=publishedRule();if(missing)f.setWorld({rules:[],bindings:[source]});else f.setWorld({rules:[{...old,fingerprint:null}],bindings:[source]});
    f.captureWorld();f.state.record=f.state.read.state.bindings[0];f.state.kind='assembly-binding';f.t.render();
    const click=f.element('asmEdit').handlers.click;
    await click();assert.match(f.element('asmStatus').textContent,/固定規則來源不合法/);
    f.setWorld({rules:[old],bindings:[source]});f.captureWorld();await click();
    assert.match(f.element('asmStatus').textContent,/固定規則來源不合法/);assert.equal(f.state.draft,null);
    assert.equal(f.history.undo.length,0);assert.deepEqual(f.calls,[]);
    await f.w.open('assembly-binding',2);await f.element('asmEdit').handlers.click();
    assert.deepEqual(copy(f.t.getState().draft.base_ref),{id:1,version:1,fingerprint:old.fingerprint});
  }
});
test('published binding edit provenance survives archive and rejects a same-value recreation with changed rule contents',async()=>{
  const f=idFixture('binding',[2],[],3),source={value:bindingValue(2),fingerprint:'b'.repeat(64)};
  await f.t.newDraft('binding',source);f.state.draft.data.name='保留編輯';f.w.flush();
  assert.deepEqual(copy(f.state.draft.binding_intent),{mode:'update',source:source.value});
  const P=require('../geometry-web/project-store.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
  const bytes=await P.pack('reset\n',{projectId:'binding-edit',name:'固定編輯',sources:[],faces:[],assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[copy(f.state.draft)]}},new Map(),zip);
  const archive=await P.unpack(bytes,zip);assert.deepEqual(archive.manifest.assemblyDrafts.records[0],copy(f.state.draft));
  const fresh=publishedRule({...rule(),joints:rule().joints.map(j=>({...j,side:'-u'}))},'c'.repeat(64));
  f.setWorld({rules:[fresh],bindings:[copy(source)]});
  const before=JSON.stringify(f.context().assemblyDrafts),active=JSON.stringify(f.state.draft),history=f.history.undo.length;
  let sends=0;f.env.fetch=()=>{sends++;throw Error('unexpected submission');};
  await assert.rejects(f.t.preview(),/材料配置的規則來源已變更或移除/);
  assert.deepEqual(copy(f.state.draft.base_ref),{id:1,version:1,fingerprint:'a'.repeat(64)});
  assert.equal(sends,0);assert.equal(JSON.stringify(f.context().assemblyDrafts),before);
  assert.equal(JSON.stringify(f.state.draft),active);assert.equal(f.history.undo.length,history);assert.equal(f.state.preview,null);
});
test('explicit published binding version mapping updates its rule pin while retaining edit intent',async()=>{
  const f=idFixture('binding',[2],[],3),source={value:bindingValue(2),fingerprint:'b'.repeat(64)};
  const old=publishedRule(),fresh=publishedRule({...rule(),version:2},'c'.repeat(64));
  f.setWorld({rules:[old,fresh],bindings:[copy(source)]});await f.t.newDraft('binding',source);
  f.state.draft.data.slots[0].A={kind:'parameter',parameterId:0,fieldId:0};f.w.flush();
  f.t.render();f.element('asmBindingRule').value='1:2';await f.element('asmBindingRule').handlers.change();
  f.element('asmMap1').value='1';f.element('asmMap2').value='2';await f.element('asmApplyMapping').handlers.click();
  assert.deepEqual(copy(f.state.draft.base_ref),{id:1,version:2,fingerprint:fresh.fingerprint});
  assert.deepEqual(copy(f.state.draft.binding_intent),{mode:'update',source:source.value});
  assert.deepEqual(copy(f.state.draft.data.slots[0].A),{kind:'parameter',parameterId:0,fieldId:0});
  let submitted;f.env.checkApiSession=()=>{};
  f.env.fetch=async(url,request)=>{submitted=JSON.parse(request.body);return {ok:true,json:async()=>({ok:true,preview:{token:'mapped-edit',valid:true,impact:{schema:'candidate-geometry/1',timbers:[],guides:[]},before:{rules:[],bindings:[]},after:{rules:[],bindings:[]},violations:[]}})};};
  await f.t.preview();assert.equal(submitted.operations[0].op,'edit-binding');
  assert.deepEqual(submitted.operations[0].value.rule,{id:1,version:2});assert.equal(f.state.preview.valid,true);
});

test('confirm locks actual handlers, inputs, navigation and repeated clicks until reply',async()=>{
  const f=fixture(),pending=f.t.confirm();await tick();let entered=false;
  assert.equal(f.w.canCloseForRecovery,false);
  await f.t.safe(()=>entered=true)();const duplicate=f.t.confirm();f.w.close();await f.w.open();await f.w.remove('assembly-rule',1);
  assert.equal(entered,false);assert.equal(f.w.isOpen,true);assert.equal(f.element('asmName').disabled,true);assert.equal(f.element('asmClose').disabled,true);
  assert.equal(f.calls.filter(c=>c.startsWith('assembly-confirm ')).length,1);
  f.gate.resolve();await pending;await duplicate;assert.deepEqual(f.removed,['draft-A']);assert.deepEqual(f.context().assemblyDrafts.map(d=>d.id),['draft-B']);
  assert.equal(f.element('projectSave').disabled,false);assert.equal(f.history.undo.length,1);
  f.history.observe('line undo',{ok:true});assert.deepEqual(f.context().assemblyDrafts.map(d=>d.id),['draft-A','draft-B']);
  f.history.observe('line redo',{ok:true});assert.deepEqual(f.context().assemblyDrafts.map(d=>d.id),['draft-B']);
});
test('a same-workspace external draft switch never cleans the newly selected draft',async()=>{
  const f=fixture(),pending=f.t.confirm();await tick();f.state.draft=copy(f.context().assemblyDrafts[1]);f.state.generation++;
  f.gate.resolve();await pending;assert.deepEqual(f.removed,[]);assert.equal(f.state.draft.id,'draft-B');assert.equal(f.context().assemblyDrafts.length,2);
});
test('an external edit after submission survives both active and persisted content checks',async()=>{
  for(const active of [true,false]){const f=fixture(),pending=f.t.confirm();await tick();
    f.context().assemblyDrafts[0].data.name='後續修改';if(active){f.state.draft.data.name='後續修改';f.state.generation++;}
    f.gate.resolve();await pending;assert.deepEqual(f.removed,[]);assert.equal(f.context().assemblyDrafts[0].data.name,'後續修改');
    f.w.close();assert.equal(f.context().assemblyDrafts[0].data.name,'後續修改');await f.w.open();assert.equal(f.ref.getAssemblyDrafts()[0].data.name,'後續修改');}
});
test('late confirm in a replaced project does not delete or redraw the new context',async()=>{
  const f=fixture(),pending=f.t.confirm();await tick();f.history.frame={context:{id:'next',assemblyDrafts:[draft('new-context')],models:[],faceProjections:new Map()},ids:new Map()};f.notify();
  f.gate.resolve();await pending;assert.deepEqual(f.removed,[]);assert.equal(f.context().assemblyDrafts[0].id,'new-context');assert.equal(f.w.isOpen,false);
});
test('a rejected confirm preserves drafts, drops its old token and permits closing',async()=>{
  const f=fixture();f.setResult({ok:false,error:'STALE'});const pending=f.t.confirm();f.gate.resolve();await assert.rejects(pending,/STALE/);
  assert.equal(f.state.preview,null);assert.equal(f.context().assemblyDrafts.length,2);assert.equal(f.history.undo.length,0);assert.equal(f.element('projectSave').disabled,false);
  await f.t.confirm();assert.equal(f.calls.filter(c=>c.startsWith('assembly-confirm ')).length,1);f.w.close();assert.equal(f.w.isOpen,false);
});
test('an unresolved transport result keeps editing locked and never resends on recovery',async()=>{
  const f=fixture();f.setResult({ok:false,transport:true,error:'結果尚未確認'});f.env.connection.phase='error';const pending=f.t.confirm();f.gate.resolve();await tick();
  assert.equal(f.state.preview,null);assert.equal(f.element('asmName').disabled,true);assert.equal(f.context().assemblyDrafts.length,2);
  assert.equal(f.w.canCloseForRecovery,true);f.w.close();assert.equal(f.w.isOpen,false);assert.equal(f.w.canCloseForRecovery,false);
  f.env.connection.phase='ready';await pending;assert.equal(f.element('projectSave').disabled,false);assert.equal(f.state.preview,null);assert.deepEqual(f.removed,[]);
  await f.t.confirm();assert.equal(f.calls.filter(c=>c.startsWith('assembly-confirm ')).length,1);
});
test('known committed result plus refresh failure never claims its removed draft was retained',async()=>{
  const f=fixture();f.failNextRead();const pending=f.t.confirm();f.gate.resolve();await tick();
  assert.deepEqual(f.removed,['draft-A']);assert.equal(f.history.undo.length,1);
  assert.match(f.element('asmStatus').textContent,/已套用.*畫面更新失敗/);assert.doesNotMatch(f.element('asmStatus').textContent,/草稿仍保留|結果尚未確認/);
  f.env.connection.phase='ready';await pending;assert.match(f.element('asmStatus').textContent,/已套用且畫面已更新/);
  assert.equal(f.calls.filter(c=>c.startsWith('assembly-confirm ')).length,1);
});
test('endpoint and direction choices change drawn SVG attributes, not only text',()=>{
  const f=fixture(),draw=()=>{f.t.diagram();return f.element('asmDiagram').innerHTML;};
  const start=draw();f.state.draft.data.joints[0].end='finish';const finish=draw();
  assert.match(start,/<circle data-end="start" cx="48"/);assert.match(finish,/<circle data-end="start" cx="126"/);
  assert.match(start,/<line data-direction-axis="u" x1="0" y1="0" x2="30" y2="0"/);
  f.state.draft.data.joints[0].dir='v';assert.match(draw(),/<line data-direction-axis="v" x1="0" y1="0" x2="0" y2="30"/);
  const definition=JSON.stringify(f.state.draft.data);f.state.rotation=90;f.state.zoom=1.5;draw();assert.equal(JSON.stringify(f.state.draft.data),definition);
});
test('all four sides and ortho-split preserve exact occurrence and endpoint identities',()=>{
  const f=fixture();Object.assign(f.state.draft.data.joints[0],{kind:'ortho-split',continuousMember:1,splitMembers:[2,3]});
  for(const [side,opposite] of [['+u','-u'],['-u','+u'],['+v','-v'],['-v','+v']]){f.state.draft.data.joints[0].side=side;f.t.diagram();const svg=f.element('asmDiagram').innerHTML;
    assert.ok(svg.includes(`data-member="2" data-contact-end="finish" data-contact-side="${side}"`));assert.ok(svg.includes(`data-member="3" data-contact-end="start" data-contact-side="${opposite}"`));
    assert.ok(svg.includes('data-member="1" data-continuous="true"'));assert.ok(svg.includes('分段一'));assert.ok(svg.includes('分段二'));}
});

const literal=value=>({kind:'literal',value});
test('candidate impact renders external and transitive geometry without selecting instance members',()=>{
  const f=fixture(),geometry=(length,x)=>({surface:1,centerline:1000,length,u:x,v:987,dir:'+u',side:'+n',A:27,B:33,origin:[x,987,2500],axes:[[1,0,0],[0,1,0],[0,0,1]]});
  const p={valid:true,before:{rules:[],bindings:[],instances:[]},after:{rules:[],bindings:[],instances:[]},impact:{schema:'candidate-geometry/1',timbers:[
    {id:92,before:geometry(1973,514),after:geometry(1960,520)},
    {id:94,before:geometry(2960,2788),after:geometry(2960,2781)},
    {id:90,before:geometry(4000,0),after:geometry(4000,0)}],guides:[{id:6,before:{off:2774},after:{off:2767}}]}};
  const html=f.t.previewCopy(p);
  for(const expected of ['角材 #92（組構外）','角材 #94（組構外）','長度 1973 mm','長度 1960 mm','世界位置 514,987,2500','世界位置 520,987,2500','中心線 1000 mm','擺向 +u/+n','世界軸 1,0,0 / 0,1,0 / 0,0,1','未變更角材','定位線 #6'])assert.ok(html.includes(expected),expected);
  assert.equal((html.match(/角材 #92（組構外）/g)||[]).length,1);
});
test('missing complete native candidate refuses confirmation and preserves the draft',async()=>{
  const f=fixture();f.state.draft=copy(draft());f.context().assemblyDrafts[0]=copy(f.state.draft);
  f.env.checkApiSession=()=>{};
  const before=JSON.stringify(f.context().assemblyDrafts);
  f.env.fetch=async()=>({ok:true,json:async()=>({ok:true,preview:{token:'incomplete',valid:true,before:{rules:[],bindings:[]},after:{rules:[],bindings:[]},violations:[]}})});
  await assert.rejects(f.t.preview(),/缺少完整幾何預覽/);
  assert.equal(f.state.preview,null);assert.equal(f.element('asmConfirm').disabled,true);
  assert.ok(f.calls.includes('assembly-cancel incomplete'));
  assert.equal(JSON.stringify(f.context().assemblyDrafts),before);
});
test('source-only instance edit keeps unchanged owned geometry in the preview',()=>{
  const f=fixture(),geometry={surface:1,centerline:1500,length:1973,u:514,v:1487,dir:'+u',side:'+n',A:27,B:33,origin:[514,1487,2500],axes:[[1,0,0],[0,1,0],[0,0,1]]};
  const before={value:{source:{id:1,name:'原名稱'}},members:[{memberId:3,timberId:7,geometry}]},after=copy(before);after.value.source.name='新名稱';
  const html=f.t.previewCopy({valid:true,before:{rules:[],bindings:[],instances:[before]},after:{rules:[],bindings:[],instances:[after]},impact:{schema:'candidate-geometry/1',timbers:[{id:7,before:geometry,after:geometry}],guides:[]}});
  assert.match(html,/構件 #3 → 角材 #7/);assert.match(html,/沒有幾何變更/);assert.match(html,/長度 1973 mm/);assert.match(html,/世界位置 514,1487,2500/);
});
test('surface-only reassignment names both placements in the visible geometry diff',()=>{
  const f=fixture(),before={surface:1,centerline:1000,length:1960,u:520,v:987,dir:'+u',side:'+n',A:27,B:33,origin:[520,987,2500],axes:[[1,0,0],[0,1,0],[0,0,1]]},after={...before,surface:2};
  const html=f.t.previewCopy({valid:true,before:{rules:[],bindings:[]},after:{rules:[],bindings:[]},impact:{schema:'candidate-geometry/1',timbers:[{id:92,before,after}],guides:[]}});
  assert.match(html,/承載面 #1.* → 承載面 #2/);assert.match(html,/角材 #92（組構外）/);assert.doesNotMatch(html,/未變更角材/);
});
function diff(f,oldSource,newSource,oldValue=27,newValue=27,axis='A'){
  const binding={id:1,name:'配置',rule:{id:1,version:1},slots:[{slotId:1,A:literal(27),B:literal(33),contactFace:'A',orientation:'B'},{slotId:2,A:null,B:null,contactFace:null,orientation:null}]};
  const before={value:copy(binding),effective:[{slotId:1,A:{value:27},B:{value:33}}]},after=copy(before);before.value.slots[0][axis]=oldSource;after.value.slots[0][axis]=newSource;
  before.effective[0][axis]={value:oldValue};after.effective[0][axis]={value:newValue};
  return f.t.previewCopy({valid:true,before:{rules:[{value:rule()}],bindings:[before]},after:{rules:[{value:rule()}],bindings:[after]}});
}
test('same-value source switches show old/new typed IDs and fixed material versions',()=>{
  const f=fixture(),parameter={kind:'parameter',parameterId:7,fieldId:2},material={kind:'material',id:3,version:1,field:'A'},spec={kind:'spec',name:'W27'};
  for(const [a,b,oldText,newText] of [[literal(27),parameter,'直接數值','#7'],[parameter,{...parameter,parameterId:8},'#7','#8'],[parameter,{...parameter,fieldId:3},'#2','#3'],[literal(27),spec,'直接數值','W27'],[spec,literal(27),'W27','直接數值'],[literal(27),material,'直接數值','第 1 版'],[material,{...material,id:4},'#3','#4'],[material,{...material,version:2},'第 1 版','第 2 版']]){
    const text=diff(f,a,b);assert.ok(text.includes(oldText));assert.ok(text.includes(newText));assert.ok(text.includes('尺寸仍為 27 mm'));assert.ok(text.includes('主支 A 來源'));assert.ok(!text.includes('<span>主支</span><span>沒有改</span>'));}
});
test('source and value changes are separate for A/B, unset and complete no-op',()=>{
  const f=fixture(),parameter={kind:'parameter',parameterId:0,fieldId:0};
  assert.match(diff(f,literal(33),parameter,33,33,'B'),/主支 B 來源/);
  assert.match(diff(f,parameter,parameter,27,31),/截面 27×33 → 31×33 mm/);
  assert.match(diff(f,literal(27),parameter,27,31),/尺寸 27 → 31 mm/);
  assert.match(diff(f,null,literal(27),null,27),/尚未選擇 → 直接數值/);
  assert.match(diff(f,parameter,parameter),/正式內容不會改變/);
});
test('source names are escaped and identical names do not hide distinct identities',()=>{
  const f=fixture();f.state.engineering.parameters=[7,8].map(id=>({id,name:'<img src=x onerror="bad">',fields:[{id:2,name:'A & "B"'}]}));
  const text=diff(f,{kind:'parameter',parameterId:7,fieldId:2},{kind:'parameter',parameterId:8,fieldId:2});
  assert.ok(text.includes('#7'));assert.ok(text.includes('#8'));assert.ok(text.includes('&lt;img'));assert.ok(text.includes('&amp;'));assert.ok(text.includes('&quot;'));assert.ok(!text.includes('<img'));
});
