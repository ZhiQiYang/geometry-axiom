'use strict';
// Function-level adapter contracts. The real native/Chrome cases are separate.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=process.env.GEOMETRY_TIMBER_UI_ROOT || path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(root,'geometry-web/timber-edit.js'),'utf8');
const fullRevision='18446744073709551615';
function setup({ids=[0],rev='18',mutate=row=>row,delay=null,legacy=null,legacyPriority='7'}={}) {
  const context={id:'project'},frame={context},edit={bid:1},focus={t:'face',id:1},calls=[],listeners={},project={revision:2};
  const invalid=[],nodes=new Map();
  if(legacy)for(const [field,value] of Object.entries({A:'27',B:'33',Dir:'+u',Side:'+n',Role:'custom',Pri:'7',Anchor:'at-face e0',Selector:'',...legacy})){
    nodes.set('tbEdit'+field,{value,getAttribute:()=>field==='Pri'?legacyPriority:value});
  }
  const row=id=>mutate({id,eligible:true,reason:null,owner:null,groups:[],groupsKnown:true,placed:true,placementOrder:String(id+1),
    definition:{A:{mode:'source',source:{kind:'parameter',parameterId:0,fieldId:2},override:null},
      B:{mode:'source',source:{kind:'parameter',parameterId:0,fieldId:7},override:{kind:'literal',value:33}},
      role:'boundary',priority:1,placement:{on:0,anchor:'at-face e0',selector:'',direction:'+u',side:'+n'}},effective:{A:27,B:33}});
  const workspace={context:()=>context,history:{frame},getProjectState:()=>project,assertEditable:()=>{},escape:String};
  const fe={timberSelection:new Set(ids),sel:ids.length===1?{kind:'timber',id:ids[0]}:null,tool:'select',panX:0,zoom:1};
  const oc={edit,focus,busy:false},connection={session:'session-1',phase:'ready'};
  const sandbox={structuredClone,console,setTimeout,clearTimeout,AbortSignal,BigInt,ReferenceWorkspace:workspace,fe,oc,connection,
    feSid:()=>0,pageRuntimeVersion:'test-version',checkApiSession:()=>{},toast:()=>{},
    feMarkInvalid:node=>{assert(node,'legacy error must target a live input');invalid.push([...nodes].find(([,value])=>value===node)[0]);},
    document:{getElementById:id=>nodes.get(id)||null,activeElement:null,addEventListener:(name,handler)=>{(listeners[name]??=[]).push(handler);}},
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
  return {adapter:sandbox.window.TimberEdit,workspace,project,fe,oc,connection,calls,listeners,invalid,nodes};
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
  // A rejected legacy field must be marked before replacing its form or
  // handing the input lock to a candidate. Keep this in the existing suite.
  for(const [field,text] of [['Pri','2.5'],['Pri','0'],['Pri',''],['Pri','9223372036854775808'],['A','0'],['A','27.5'],['B','0'],['B','1.5']]){
    const legacy=setup({legacy:{[field]:text},mutate:row=>({...row,definition:{...row.definition,role:'custom',priority:7,priorityText:'7'}})});
    legacy.oc.busy=true;let handoffs=0;
    await legacy.adapter.applyLegacyFields(0,()=>{handoffs++;legacy.oc.busy=false;});
    assert.deepEqual(legacy.invalid,['tbEdit'+field],'R356_LEGACY_'+field+'_INVALID_MARK');
    assert.equal(legacy.nodes.get('tbEdit'+field).value,text,'R356_LEGACY_INVALID_INPUT_RETAINED');
    assert.equal(handoffs,0,'R356_LEGACY_INVALID_NO_CANDIDATE_HANDOFF');
    assert.deepEqual(legacy.calls.map(item=>item.schema),['timber-edit-read/1'],'R356_LEGACY_INVALID_READ_ONLY');
    assert.equal(legacy.adapter.beforeWorldMutation(),null,'R356_LEGACY_INVALID_NO_PENDING_OWNER');
  }
  // These two positive probes stop at the handoff, before this function-level
  // fixture's absent batch DOM. Full candidate/wire checks remain in P116.
  for(const [value,original] of [[maximum,'7'],[String(Number(maximum)),String(Number(maximum))]]){
    const legacy=setup({legacy:{Pri:value},legacyPriority:original,
      mutate:row=>({...row,definition:{...row.definition,role:'custom',priority:Number(maximum),priorityText:maximum}})});
    let handoffs=0;
    await legacy.adapter.applyLegacyFields(0,()=>{handoffs++;throw Error('R356_VALIDATION_HANDOFF_PROBE');});
    assert.equal(handoffs,1,'R356_LEGACY_EXACT_PRIORITY_HANDOFF');
    assert.deepEqual(legacy.invalid,[],'R356_LEGACY_EXACT_PRIORITY_NOT_REJECTED');
  }
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
