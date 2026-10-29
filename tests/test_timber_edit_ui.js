'use strict';
// Function-level adapter contracts. The real native/Chrome cases are separate.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=process.env.GEOMETRY_TIMBER_UI_ROOT || path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(root,'geometry-web/timber-edit.js'),'utf8');
const fullRevision='18446744073709551615';
function setup({ids=[0],rev='18',mutate=row=>row,delay=null}={}) {
  const context={id:'project'},frame={context},edit={bid:1},focus={t:'face',id:1},calls=[],listeners={},project={revision:2};
  const row=id=>mutate({id,eligible:true,reason:null,owner:null,groups:[],groupsKnown:true,placed:true,placementOrder:String(id+1),
    definition:{A:{mode:'source',source:{kind:'parameter',parameterId:0,fieldId:2},override:null},
      B:{mode:'source',source:{kind:'parameter',parameterId:0,fieldId:7},override:{kind:'literal',value:33}},
      role:'boundary',priority:1,placement:{on:0,anchor:'at-face e0',selector:'',direction:'+u',side:'+n'}},effective:{A:27,B:33}});
  const workspace={context:()=>context,history:{frame},getProjectState:()=>project,assertEditable:()=>{},escape:String};
  const fe={timberSelection:new Set(ids),sel:ids.length===1?{kind:'timber',id:ids[0]}:null,tool:'select',panX:0,zoom:1};
  const oc={edit,focus,busy:false},connection={session:'session-1',phase:'ready'};
  const sandbox={structuredClone,console,setTimeout,clearTimeout,AbortSignal,BigInt,ReferenceWorkspace:workspace,fe,oc,connection,
    feSid:()=>0,pageRuntimeVersion:'test-version',checkApiSession:()=>{},toast:()=>{},
    document:{getElementById:()=>null,activeElement:null,addEventListener:(name,handler)=>{(listeners[name]??=[]).push(handler);}},
    FaceContextMenu:{refreshEligibility:()=>{}},
    apiRequest:async command=>{calls.push(command);assert.equal(command,'engineering-read');return {ok:true,revision:Number(rev),state:{materials:[],specs:[],applications:[]}};},
    fetch:async (url,options)=>{
      assert.equal(url,'/timber-edit/read');const body=JSON.parse(options.body);calls.push(body);
      if(delay)await delay();
      return {ok:true,status:200,json:async()=>({ok:true,schema:'timber-edit-read-result/1',revision:rev,
        contextKey:'a'.repeat(64),boundaryId:1,maxOperations:64,eligible:true,reason:null,
        timbers:body.timberIds.map(row),recipeKey:'b'.repeat(64)})};
    }};
  sandbox.window={DraftGate:{register:()=>{}},addEventListener:(name,handler)=>{(listeners[name]??=[]).push(handler);}};
  vm.createContext(sandbox);vm.runInContext(source,sandbox,{filename:'timber-edit.js'});
  return {adapter:sandbox.window.TimberEdit,workspace,project,fe,oc,connection,calls,listeners};
}
test('R11-UI-U64: catalog numbers never round the exact timber revision',async()=>{
  const s=setup({rev:fullRevision});await assert.doesNotReject(s.adapter.copy());
  assert.equal(s.adapter.menuItems().paste,'');
  assert.deepEqual(s.calls.map(item=>typeof item==='string'?item:item.schema),['timber-edit-read/1','engineering-read','timber-edit-read/1']);
  assert.equal(s.calls[0].timberIds[0],0);assert.equal(s.project.revision,2);
});
test('R11-UI-ELIGIBILITY: owner, groups and unknown qualification reject the whole copy',async()=>{
  for(const mutate of [row=>({...row,owner:{kind:'assembly-instance',id:0}}),row=>({...row,groups:[{kind:'boundary-pair',id:335}]}),row=>({...row,groupsKnown:false})]){
    const s=setup({mutate});await assert.rejects(s.adapter.copy(),/資格|群組|所有權/);
    assert.notEqual(s.adapter.menuItems().paste,'');
  }
});
test('R11-UI-PRIORITY: full int64 text is authoritative and unsafe legacy projections are rejected',async()=>{
  const maximum='9223372036854775807';
  const s=setup({mutate:row=>({...row,definition:{...row.definition,role:'custom',priority:Number(maximum),priorityText:maximum}})});
  await assert.doesNotReject(s.adapter.copy());assert.equal(s.adapter.menuItems().paste,'');
  const unsafe=setup({mutate:row=>({...row,definition:{...row.definition,role:'custom',priority:Number(maximum)}})});
  await assert.rejects(unsafe.adapter.copy(),/優先序/);
  const invalid=setup({mutate:row=>({...row,definition:{...row.definition,priorityText:'01'}})});
  await assert.rejects(invalid.adapter.copy(),/優先序/);
});
test('R11-UI-ORDER: a late read cannot authorize a reordered selection',async()=>{
  let release;const wait=new Promise(resolve=>{release=resolve;});
  const s=setup({ids:[0,7],delay:()=>wait}),request=s.adapter.prepareMenu();
  s.fe.timberSelection=new Set([7,0]);release();await request;
  assert.match(s.adapter.menuItems().batch,/正在核對/);
});
test('R11-UI-RECIPE-LIFETIME: pan and zoom preserve recipes, frame and revision changes expire them',async()=>{
  const s=setup();await s.adapter.copy();s.fe.panX=80;s.fe.zoom=1.5;
  assert.equal(s.adapter.menuItems().paste,'');
  s.project.revision++;assert.match(s.adapter.menuItems().paste,/世代/);
  s.project.revision--;s.workspace.history.frame={context:s.workspace.context()};
  assert.match(s.adapter.menuItems().paste,/世代/);
});
test('R11-UI-INPUT-IME: text and composition shortcuts never reach geometry copy',async()=>{
  const s=setup(),key=s.listeners.keydown[0];
  const event=extra=>({key:'c',ctrlKey:true,metaKey:false,altKey:false,keyCode:67,isComposing:false,
    target:{isContentEditable:false,closest:selector=>selector==='#faceEditorViewport'?{}:null},
    preventDefault:()=>assert.fail('text key was intercepted'),stopImmediatePropagation:()=>assert.fail('text event was stopped'),...extra});
  key(event({isComposing:true}));
  key(event({target:{isContentEditable:true,closest:()=>null}}));
  key(event({target:{isContentEditable:false,closest:selector=>selector.includes('input,textarea')?{}:null}}));
  for(const handler of s.listeners.compositionstart)handler();key(event());
  let stopped=0;
  key(event({key:'Escape',target:{closest:selector=>selector==='#timberEditForm'?{}:null},stopPropagation:()=>{stopped++;}}));
  assert.equal(stopped,1,'composition Escape must not reach the global drawer handler');
  await Promise.resolve();assert.equal(s.calls.length,0);
});
