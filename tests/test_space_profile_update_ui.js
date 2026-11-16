'use strict';
// Execute shipped browser functions. Real DOM/layout remains a separate CDP gate.
const {test:nodeTest}=require('node:test'),assert=require('node:assert/strict');
const test=(name,fn)=>nodeTest(name,{timeout:5000},fn);
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ROOT=process.env.GEOMETRY_Q38J_TEST_ROOT||path.resolve(__dirname,'..');
const source=fs.readFileSync(process.env.GEOMETRY_MODEL_UPDATE_APP_SOURCE||path.join(ROOT,'geometry-web/model-update-app.js'),'utf8');
const fixture=JSON.parse(fs.readFileSync(path.join(ROOT,'tests/fixtures/q38j-b-native-model.json'),'utf8'));
const clone=value=>JSON.parse(JSON.stringify(value));
function shipped(name) {
  const start=new RegExp('^  (?:async )?function '+name+'\\(','m').exec(source);
  assert.ok(start,'Q38JC_UI_FUNCTION: '+name);
  const rest=source.slice(start.index),end=/\n  (?:async )?function \w+\(/.exec(rest);
  assert.ok(end,'Q38JC_UI_FUNCTION_BOUNDARY: '+name);return rest.slice(0,end.index);
}
function nativeRead(){return {ok:true,revision:11,state:{profiles:[{value:{id:1,name:'斷面 <來源>'}}],runs:[
  ...[4,0,1].map(id=>({value:{id,profileId:1,placement:{kind:'advanced'}},coordinateSpace:'world',length:2400,members:[{memberId:0}]})),
  {value:{id:2,profileId:1,placement:null},coordinateSpace:'local',length:2400,members:[]}
]}};}
function deferred(){let resolve;const promise=new Promise(done=>{resolve=done;});return {promise,resolve};}
function harness() {
  const nodes=new Map(),selected=[],calls=[],messages=[],holds=[];
  const state={context:{},frame:{},revision:1,contextToken:'current',undo:null,redo:null,group:null,blocked:false};
  const profiles=nativeRead(),graph={ok:true,schema:'source-inspector/1',live:true,complete:true,revision:11,sourceFingerprint:'a'.repeat(64),identityLedger:{schema:'identity-ledger/1',active:false}};
  const surface={id:1,boundary:1,origin:[0,0,0],u:[1,0,0],v:[0,1,0]},before=clone(fixture.model);
  const $=id=>{if(!nodes.has(id))nodes.set(id,{value:'',textContent:'',innerHTML:'',hidden:false,disabled:false,checked:false,dataset:{},replaceChildren(){},focus(){},scrollIntoView(){}});return nodes.get(id);};
  const dialog={open:true,showModal(){this.open=true;},setAttribute(){},querySelectorAll(selector){
    if(selector==='[data-mu-profile-run]:checked')return selected;
    if(selector==='[data-mu-edge]:checked')return [0,1,2,3].map(id=>({dataset:{muEdge:String(id)}}));
    return [];
  },querySelector(){return null;}};
  const sandbox={console,TextEncoder,AbortController,DOMException,Number,Map,Set,
    $,dialog,session:null,serial:0,timer:null,clone,json:JSON.stringify,same:(a,b)=>JSON.stringify(a)===JSON.stringify(b),
    uint:n=>Number.isSafeInteger(n)&&n>=0&&n<=4294967295,
    esc:value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
    embeddedTimberWarning:'內含矩形不能納入角材',window:{WorkspaceShell:{attach(){},refresh(){}}},document:{activeElement:null},
    ReferenceWorkspace:{getModelOperationState:()=>({...state}),getSpaceModels:()=>[before],getFaceProjection:()=>null},
    SourceInspector:{index:value=>value},GeometryProject:{validateFaceProjection(){throw Error('none');}},
    ensureDialog(){},close(){},savedSettings(){},actions(){},renderOutline(){},showIdentity(){},prefilledPlacement(){return null;},applyIdentityChoice(){},setInterval:()=>1,clearInterval(){},
    createController:()=>({begin:()=>clone(before),cancel(){},status:()=>({phase:'selecting'})}),
    message:(text,kind)=>messages.push({text,kind})
  };
  sandbox.api=async command=>{
    calls.push(command);const hold=holds.find(item=>item.command===command&&!item.used);
    if(hold){hold.used=true;hold.entered.resolve();await hold.release.promise;}
    if(command==='identity-read')return {ok:true,active:false};
    if(command==='source-inspect')return clone(graph);
    if(command==='section-profile-read')return clone(profiles);
    if(command==='dump-deidentified')return {ok:true,text:fixture.scene,revision:graph.revision,definition_sha256:graph.sourceFingerprint};
    if(command==='surfaces')return {ok:true,surfaces:[clone(surface)]};
    if(command==='objects')return {ok:true,columns:[],beams:[]};
    throw Error('unexpected command '+command);
  };
  vm.createContext(sandbox);
  vm.runInContext(['hostState','record','guard','currentWork','invalidate','validProjection','projectionFor','read','sourcePin','profileSource','readPinnedSource','checkSession','open','renderChoices','counts','selection','guardSelection'].map(shipped).join('\n'),sandbox);
  return {sandbox,state,profiles,graph,surface,selected,calls,messages,$,
    choose(...ids){selected.splice(0,selected.length,...ids.map(id=>({dataset:{muProfileRun:String(id)}})));},
    ready(){const current=sandbox.session;current.surface=clone(surface);current.projection=null;current.timbers=[];current.obstacles=[];current.loops=[{verts:[[0,0],[10,0],[10,10],[0,10]]}];return current;},
    hold(command){const item={command,used:false,entered:deferred(),release:deferred()};holds.push(item);return {entered:item.entered.promise,release:()=>item.release.resolve()};}
  };
}

test('Q38JC UI all world runs are unselected candidates independent of selected face',async()=>{
  const h=harness();await h.sandbox.open(fixture.model.id);const current=h.ready();h.sandbox.renderChoices(current);
  assert.deepEqual(clone(current.profileRuns.map(run=>run.id)),[0,1,4],'Q38JC_UI_ALL_WORLD');
  assert.equal(current.profileUnavailable,1);
  assert.deepEqual([...h.$('muProfiles').innerHTML.matchAll(/data-mu-profile-run="(\d+)"/g)].map(m=>+m[1]),[0,1,4],'Q38JC_UI_PICKER');
  assert.doesNotMatch(h.$('muProfiles').innerHTML,/\schecked(?:[\s=>])/,'Q38JC_UI_EXPLICIT');
  assert.match(h.$('muProfiles').innerHTML,/斷面 &lt;來源&gt;/);
  assert.match(h.$('muProfileUnavailable').textContent,/未定位 1 條/);
  assert.match(source,/<summary>一併納入<\/summary>/,'Q38JC_UI_SHARED_DISCLOSURE');
});
test('Q38JC UI explicit empty selection removes old runs and typed selected zero stays zero',async()=>{
  const h=harness();await h.sandbox.open(fixture.model.id);h.ready();
  assert.ok(Object.hasOwn(h.sandbox.selection(),'profile_runs'),'Q38JC_UI_EMPTY_REMOVAL');
  assert.deepEqual(clone(h.sandbox.selection().profile_runs),[],'Q38JC_UI_EMPTY_REMOVAL');
  h.choose(4,0);assert.deepEqual(clone(h.sandbox.selection().profile_runs),[{kind:'profile-run',id:0},{kind:'profile-run',id:4}],'Q38JC_UI_TYPED');
  h.choose(2);assert.throws(()=>h.sandbox.selection(),/拉伸件選擇已失效/,'Q38JC_UI_LOCAL_REJECT');
});
test('Q38JC UI candidate read captures native profiles around complete source dump',async()=>{
  const h=harness();await h.sandbox.open(fixture.model.id);
  assert.equal(h.sandbox.session.invalid,false,'Q38JC_UI_OPEN_BASELINE');
  assert.equal(h.sandbox.session.profileRevision,11,'Q38JC_UI_REVISION');
  assert.deepEqual(h.calls,['identity-read','source-inspect','section-profile-read','dump-deidentified','surfaces','objects','dump-deidentified','section-profile-read','source-inspect'],'Q38JC_UI_READ_ORDER');
});
test('Q38JC UI read race rejects changed native profile revision with identical graph and dump',async()=>{
  const h=harness(),hold=h.hold('objects'),pending=h.sandbox.open(fixture.model.id);await hold.entered;h.profiles.revision++;hold.release();await pending;
  assert.equal(h.sandbox.session.invalid,true,'Q38JC_UI_OPEN_RACE');
  assert.equal(h.sandbox.session.profileRuns,undefined,'Q38JC_UI_OPEN_RACE');
});
test('Q38JC UI read race rejects a context or history change before candidate admission',async()=>{
  for(const field of ['context','undo']) {
    const h=harness(),hold=h.hold('objects'),pending=h.sandbox.open(fixture.model.id);await hold.entered;h.state[field]={};hold.release();await pending;
    assert.equal(h.sandbox.session.invalid,true,'Q38JC_UI_CONTEXT_HISTORY');
    assert.equal(h.sandbox.session.profileRuns,undefined,'Q38JC_UI_CONTEXT_HISTORY');
  }
});
test('Q38JC UI preview and confirmation reread the native profile revision',async()=>{
  const h=harness();await h.sandbox.open(fixture.model.id);const current=h.ready();
  const options={signal:new AbortController().signal};
  const fresh=await h.sandbox.readPinnedSource(current,options);
  assert.equal(fresh.scene,fixture.scene,'Q38JC_UI_PINNED_BASELINE');
  h.profiles.revision++;
  await assert.rejects(()=>h.sandbox.readPinnedSource(current,options),/斷面拉伸件來源已變更/,'Q38JC_UI_PINNED_REVISION');
});
test('Q38JC UI source reread cancellation cannot renew a retired selection',async()=>{
  const h=harness();await h.sandbox.open(fixture.model.id);const current=h.ready(),hold=h.hold('dump-deidentified');
  const pending=h.sandbox.readPinnedSource(current,{signal:new AbortController().signal});
  const refused=assert.rejects(pending,{name:'AbortError'},'Q38JC_UI_CANCELLED_READ');
  await hold.entered;current.abort.abort();hold.release();await refused;
});

test('Q38JC UI /3 capability is required before any profile update POST including removal',async()=>{
  for(const removing of [false,true]) {
    const h=harness();await h.sandbox.open(fixture.model.id);const current=h.ready(),requests=[];
    h.sandbox.ModelUpdate={create:host=>host};
    h.sandbox.fetch=async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>url==='/model/capabilities'?{capabilities:['section-profile/1'],space_preview_schemas:['geometry-space-preview/1','geometry-space-preview/2']}:{ok:true}};};
    vm.runInContext(['requireProfileSpaceCapability','createController'].map(shipped).join('\n'),h.sandbox);
    const controller=h.sandbox.createController(current),record=clone(fixture.model);
    if(!removing)delete record.input.profile_runs;
    await assert.rejects(()=>controller.produce({record,selection:{profile_runs:removing?[]:[{kind:'profile-run',id:1}]}},{signal:new AbortController().signal}),/未宣告.*\/3/,'Q38JC_UI_CAPABILITY');
    assert.deepEqual(requests.map(item=>item.url),['/model/capabilities'],'Q38JC_UI_NO_POST_WITHOUT_CAPABILITY');
  }
});
test('Q38JC UI /3 producer capability permits the declared complete update without implicit fallback',async()=>{
  const h=harness();await h.sandbox.open(fixture.model.id);const current=h.ready(),requests=[];
  h.sandbox.ModelUpdate={create:host=>host};
  h.sandbox.fetch=async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>url==='/model/capabilities'?{space_preview_schemas:['geometry-space-preview/3']}:{ok:true,record:fixture.model}};};
  vm.runInContext(['requireProfileSpaceCapability','createController'].map(shipped).join('\n'),h.sandbox);
  const data={record:fixture.model,selection:{profile_runs:[{kind:'profile-run',id:1}]}};
  await h.sandbox.createController(current).produce(data,{signal:new AbortController().signal});
  assert.deepEqual(requests.map(item=>item.url),['/model/capabilities','/model/update-preview'],'Q38JC_UI_CAPABILITY_POSITIVE');
  assert.deepEqual(JSON.parse(requests[1].options.body),data,'Q38JC_UI_NO_FALLBACK');
});
test('Q38JC UI graph and profile reads must share the same native revision',async()=>{
  const h=harness();h.graph.revision++;
  await h.sandbox.open(fixture.model.id);
  assert.equal(h.sandbox.session.invalid,true,'Q38JC_UI_SINGLE_REVISION');
  assert.equal(h.sandbox.session.profileRuns,undefined,'Q38JC_UI_SINGLE_REVISION');
});
test('Q38JC UI per-member review preserves exact world intervals and separate material quantities',()=>{
  const sandbox={};vm.createContext(sandbox);vm.runInContext(shipped('profileGeometry')+'\n'+shipped('profileIdentityText'),sandbox);
  const text=sandbox.profileGeometry(fixture.model.result);
  assert.match(text,/1000～1027、2000～4400、2667～2700/,'Q38JC_UI_MEMBER_BOUNDS');
  assert.equal((text.match(/2138400 mm³/g)||[]).length,3,'Q38JC_UI_MEMBER_VOLUMES');
  assert.match(text,/未扣拉伸件間重疊.*未檢查碰撞、貼合或包含/,'Q38JC_UI_NO_COLLISION_CLAIM');
  assert.equal(sandbox.profileIdentityText({token:'proved',text:'物件延續已證明'},true),'已追蹤根延續已證明；拉伸件延續未知','Q38JC_UI_IDENTITY_SCOPE');
  const empty=sandbox.profileGeometry({summary:{profile_run_count:1},profile_runs:{derived:{objects:[]}}});
  assert.match(empty,/已納入 1 條拉伸件，零構件/,'Q38JC_UI_ZERO_MEMBER_SELECTED');
  assert.doesNotMatch(empty,/未納入/,'Q38JC_UI_ZERO_MEMBER_SELECTED');
});
test('Q38JC UI selecting the first run immediately limits proof wording without resetting selections',async()=>{
  const h=harness();await h.sandbox.open(fixture.model.id);const current=h.ready();
  delete current.before.input.profile_runs;
  current.judged=[{role:'placement',kind:'placement',id:1,status:'continuous'}];
  h.sandbox.IdentityLedger=require('../geometry-web/identity-ledger.js');
  vm.runInContext(['profileIdentityText','refreshIdentitySummary'].map(shipped).join('\n'),h.sandbox);
  h.sandbox.refreshIdentitySummary(current);assert.equal(h.$('muIdentity').textContent,'物件延續已證明');
  h.choose(1);h.sandbox.refreshIdentitySummary(current);
  assert.equal(h.$('muIdentity').textContent,'已追蹤根延續已證明；拉伸件延續未知','Q38JC_UI_IMMEDIATE_PROOF_SCOPE');
  assert.deepEqual(clone(h.selected),[{dataset:{muProfileRun:'1'}}],'Q38JC_UI_KEEP_SELECTION');
  h.choose();h.sandbox.refreshIdentitySummary(current);assert.equal(h.$('muIdentity').textContent,'物件延續已證明');
});
