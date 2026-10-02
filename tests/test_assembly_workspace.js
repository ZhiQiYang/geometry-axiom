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
function fixture(){
  const elements=new Map(),listeners=new Map(),calls=[],removed=[],gate=deferred();
  const element=id=>{if(!elements.has(id))elements.set(id,{id,disabled:false,hidden:false,innerHTML:'',textContent:'',dataset:{},classList:{toggle(){}},attrs:{},
    setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];},append(){},prepend(){},remove(){},
    addEventListener(){},querySelector:()=>null,querySelectorAll:()=>[],close(){this.open=false;},showModal(){this.open=true;}});return elements.get(id);};
  const dialog=element('dialog');dialog.open=true;dialog.querySelectorAll=selector=>selector==='button,input,select'?[...elements.values()].filter(e=>e!==dialog):[];
  for(const id of ['asmName','asmConfirm','asmPreview','asmCancel','asmClose','asmNewRule','projectSave','asmDiagram','asmStatus'])element(id);
  const history=new ContextHistory(()=>({id:crypto.randomUUID(),assemblyDrafts:[],models:[],faceProjections:new Map()}));
  const context=()=>history.frame.context;
  context().assemblyDrafts=[draft(),draft('draft-B')];
  const notify=()=>listeners.get('project-info-changed')?.();
  const ref={escape:v=>String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'),context,
    getProjectState:()=>({contextToken:context().id}),assertEditable(){},getAssemblyDrafts:()=>copy(context().assemblyDrafts),
    setAssemblyDraft(d,token){assert.equal(token,context().id);history.push(history.snapshot(),'local');context().assemblyDrafts=context().assemblyDrafts.map(x=>x.id===d.id?copy(d):x);notify();},
    removeAssemblyDraft(id,token,record=true){assert.equal(token,context().id);if(record)history.push(history.snapshot(),'local');removed.push(id);context().assemblyDrafts=context().assemblyDrafts.filter(d=>d.id!==id);notify();}};
  let result={ok:true},world={rules:[],bindings:[]},failRead=false;
  const env={ReferenceWorkspace:ref,structuredClone,crypto,Map,Set,console,AbortSignal,setTimeout,
    window:{addEventListener:(name,fn)=>listeners.set(name,fn)},document:{createElement:()=>dialog,body:{append(){}},getElementById:element},
    WorkspaceShell:{attach(){},detach(){},refresh(){}},placeStudioLesson(){},renderObjects:async()=>{},toast(){},connection:{phase:'ready'},
    apiRequest:async cmd=>{calls.push(cmd);if(cmd.startsWith('assembly-confirm ')){await gate.promise;history.observe(cmd,result);notify();return result;}
      if(cmd==='assembly-read'){if(failRead){failRead=false;env.connection.phase='error';return {ok:false,transport:true,error:'Refresh unavailable'};}return {ok:true,revision:1,state:copy(world)};}
      if(cmd==='engineering-read')return {ok:true,revision:1,state:{materials:[],parameters:[]}};
      return {ok:true,specs:[]};}};
  let source=fs.readFileSync(process.env.GEOMETRY_TEST_ASSEMBLY_WORKSPACE||require.resolve('../geometry-web/assembly-workspace.js'),'utf8');
  source=source.replace('return {open,close,flush,card,inspector,remove,','return {test:{setState:x=>s=x,getState:()=>s,confirm,diagram,previewCopy,render,safe,changed},open,close,flush,card,inspector,remove,');
  vm.runInNewContext(source,env);const w=env.window.AssemblyWorkspace,t=w.test;
  const state={context:context().id,generation:1,draft:copy(context().assemblyDrafts[0]),draftsRef:context().assemblyDrafts,read:{state:world},engineering:{parameters:[],materials:[],specs:[]},preview:{valid:true,token:'candidate-A'},rotation:0,zoom:1};t.setState(state);
  return {w,t,state,context,history,ref,calls,removed,gate,element,env,notify,setResult:r=>result=r,setWorld:w=>world=w,failNextRead:()=>failRead=true};
}

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
