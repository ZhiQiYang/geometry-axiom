/* #116 supplemental state tests. These execute the production adapter in a VM
 * with an explicitly mocked transport and DOM boundary. They are not browser,
 * native-geometry, hit-testing, or visual acceptance evidence.
 * --native-wire DIR additionally consumes unedited bridge JSON recordings.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const {createHash} = require('node:crypto');
const SOURCE = path.join(__dirname,'workspace-view.js');
const PROJECT = {kind:'project'}, SPACE = {kind:'space',id:9};
const clone = value => structuredClone(value);
const plain = value => JSON.parse(JSON.stringify(value));
const capResponse = () => ({ok:true,schema:'workspace-view-capabilities/1',capabilities:['workspace-view/1'],workspace_view:{
  schema:'workspace-view/1',frames:['front','side','top','bottom'],maxHiddenRoots:608,maxOps:131072,maxRequestBytes:1048576}});
function ready({viewKey='a'.repeat(64),revision='19',viewId=null}={}) {
  const axes={front:[[1,0,0],[0,0,-1]],side:[[0,1,0],[0,0,-1]],top:[[1,0,0],[0,-1,0]],bottom:[[1,0,0],[0,1,0]]};
  const frames=viewId?[viewId]:['front','side','bottom'];
  return {ok:true,schema:'workspace-view-result/1',status:'READY',revision,viewKey,
    layout:{w:1000,h:1000,views:frames.map(viewId=>({viewId,right:axes[viewId][0],down:axes[viewId][1],bounds:[-1000,-1000,1000,1000],tx:10,ty:20}))},
    ops:frames.flatMap(viewId=>[{op:'begin',tx:10,ty:20,viewId,owner:null},
      ...[{kind:'boundary',id:71},{kind:'column',id:71},{kind:'column',id:83},{kind:'guide',id:0}].map(owner=>
        ({op:'line',x0:100,y0:200,x1:300,y1:400,s:2,owner})),{op:'end',owner:null}])};
}
function picked(snapshot,target={root:{kind:'column',id:71},placementId:null,boundaryId:null,memberFace:null}) {
  return {ok:true,schema:'workspace-view-pick-result/1',status:target?'HIT':'NONE',revision:snapshot.revision,
    viewKey:snapshot.viewKey,target,hoverOps:[]};
}
function deferred() {let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};}
function fixture({cap=capResponse(),readResult=ready(),pickResult=picked(readResult)}={}) {
  const listeners={window:new Map(),document:new Map()},calls=[],apiCommands=[],effects=[];
  const history={frame:{name:'frame'},undo:[{name:'undo'}],redo:[],group:null};
  const project={id:'project-A',contextToken:'load-A',revision:4,dirty:false};
  const evidence={nativeRevision:Number(readResult.revision)},state={context:'context-A'};
  const matrix={a:2,b:0,c:0,d:2,e:30,f:40,inverse(){return {a:.5,b:0,c:0,d:.5,e:-15,f:-20};}};
  const svg={getScreenCTM:()=>matrix};
  let responder=async p=>clone(p==='/view/read'?readResult:pickResult),capability=clone(cap);
  const doc={getElementById:()=>null,querySelector:selector=>selector.includes('data-ss-tab')?
    {classList:{contains:()=>true}}:null,querySelectorAll:()=>[],
    addEventListener:(name,fn)=>listeners.document.set(name,[...(listeners.document.get(name)||[]),fn])};
  const env={console,AbortSignal,structuredClone,document:doc,STYLE:Array.from({length:20},()=>({})),
    pageRuntimeVersion:'fixture-runtime',connection:{phase:'ready',session:'session-A'},
    oc:{focus:null,navigationSequence:1},view3:true,zoom:3,panX:5,panY:7,world:svg,
    DOMPoint:class {constructor(x,y){this.x=x;this.y=y;}matrixTransform(m){return {x:this.x*m.a+this.y*m.c+m.e,y:this.x*m.b+this.y*m.d+m.f};}},
    ReferenceWorkspace:{history,getProjectState:()=>project,getEvidenceState:()=>evidence,context:()=>state.context,
      observeNativeRevision:r=>{evidence.nativeRevision=r.revision;}},
    apiRequest:async command=>{apiCommands.push(command);if(command==='view-capabilities')return clone(capability);
      if(command==='source-inspect'){evidence.nativeRevision=19;return {ok:true,revision:19};}
      throw Error('Unexpected non-read API command: '+command);},
    fetch:async(url,options)=>{const body=JSON.parse(options.body);calls.push({url,method:options.method,body});
      const r=await responder(url,body);return {ok:true,json:async()=>r};},
    checkApiSession:()=>{},hoverPickScheduler:{cancel:()=>effects.push('cancel-hover')},
    clearHoverPresentation:()=>effects.push('clear-hover'),toast:message=>effects.push('toast:'+message),
    render:async()=>effects.push('render-project'),renderSpaceProjection:async()=>effects.push('render-space'),
    ViewContextMenu:{hide:()=>effects.push('hide-menu')},WorkspaceProperties:{hide:()=>effects.push('hide-properties')},
    addEventListener:(name,fn)=>listeners.window.set(name,[...(listeners.window.get(name)||[]),fn])};
  env.window=env;vm.createContext(env);vm.runInContext(fs.readFileSync(SOURCE,'utf8'),env,{filename:SOURCE});
  return {V:env.WorkspaceView,env,calls,apiCommands,effects,history,project,evidence,state,svg,matrix,
    respond:fn=>{responder=fn;},capability:r=>{capability=clone(r);},
    fire:(name,surface='window')=>{for(const fn of listeners[surface].get(name)||[])fn();},
    guardSnapshot:()=>({project:clone(project),historyFrame:history.frame,undo:history.undo[0],group:history.group})};
}
function unchanged(f,before) {
  assert.deepEqual(f.project,before.project);assert.equal(f.history.frame,before.historyFrame);
  assert.equal(f.history.undo[0],before.undo);assert.equal(f.history.group,before.group);
  assert.ok(f.apiCommands.every(command=>['view-capabilities','source-inspect'].includes(command)),f.apiCommands);
}
async function untilSent(f,count) {for(let i=0;i<20&&f.calls.length<count;i++)await new Promise(r=>setImmediate(r));assert.equal(f.calls.length,count);}
function registerTests() {
  const test=require('node:test');
  test('U01 independent native capability, read request and typed owner identity are preserved',async()=>{
    const f=fixture(),before=f.guardSnapshot(),result=await f.V.read(PROJECT);
    assert.equal(result.status,'READY');assert.equal(f.V.state(PROJECT).snapshot,result);
    assert.deepEqual(f.calls[0],{url:'/view/read',method:'POST',body:{schema:'workspace-view/1',expectedRevision:'19',
      scope:PROJECT,presentation:{mode:'three',focus:null},layers:['face','guide','timber','rc'],hidden:[]}});
    const collided=[...new Map(result.ops.filter(o=>o.owner?.id===71).map(o=>[o.owner.kind,o.owner])).values()];
    assert.deepEqual(collided,[{kind:'boundary',id:71},{kind:'column',id:71}]);
    assert.equal(f.apiCommands.filter(c=>c==='view-capabilities').length,1);unchanged(f,before);
  });
  test('U02 exact pick wire preserves uint32 zero and null D3 instead of inventing a face',async()=>{
    const snapshot=ready(),target={root:{kind:'guide',id:0},placementId:19,boundaryId:71,memberFace:null};
    const f=fixture({readResult:snapshot,pickResult:picked(snapshot,target)}),before=f.guardSnapshot();
    await f.V.read(PROJECT);const result=await f.V.pick(PROJECT,{viewId:'front',x:100,y:-300,r:5});
    assert.equal(result.status,'HIT');assert.deepEqual(plain(f.V.state(PROJECT).lastTarget),target);
    assert.deepEqual(f.calls.at(-1).body,{schema:'workspace-view-pick/1',expectedRevision:'19',viewKey:snapshot.viewKey,
      viewId:'front',point:{x:100,y:-300},radius:5});
    f.respond(async()=>picked(snapshot));await f.V.pick(PROJECT,{viewId:'front',x:100,y:-300,r:5});
    assert.equal(f.V.state(PROJECT).lastTarget.boundaryId,null);assert.equal(f.V.state(PROJECT).lastTarget.placementId,null);unchanged(f,before);
  });
  test('U03 hidden roots remain typed, workspace-local and intersect existing layers',async()=>{
    const f=fixture(),before=f.guardSnapshot();await f.V.read(PROJECT);
    f.V.state(PROJECT).layers=['face','guide'];await f.V.hideRoot(PROJECT,{kind:'column',id:71});
    assert.deepEqual(plain(f.V.state(PROJECT).hidden),[{kind:'column',id:71}]);
    assert.deepEqual(plain(f.V.state(SPACE).hidden),[]);
    await f.V.read(PROJECT);assert.deepEqual(f.calls.at(-1).body.hidden,[{kind:'column',id:71}]);
    assert.deepEqual(f.calls.at(-1).body.layers,['face','guide']);
    await f.V.restore(PROJECT,{kind:'boundary',id:71});
    assert.deepEqual(plain(f.V.state(PROJECT).hidden),[{kind:'column',id:71}]);
    await f.V.restore(PROJECT,{kind:'column',id:71});assert.deepEqual(plain(f.V.state(PROJECT).hidden),[]);
    assert.deepEqual(plain(f.V.state(PROJECT).layers),['face','guide']);unchanged(f,before);
  });
  test('U04 native revision, project/load and session changes retire every old mask and target',async()=>{
    const f=fixture();
    for(const change of [()=>f.evidence.nativeRevision++,()=>f.project.id='project-B',
      ()=>f.project.contextToken='load-B',()=>f.env.connection.session='session-B']){
      const p=f.V.state(PROJECT),s=f.V.state(SPACE);p.hidden=[{kind:'column',id:71}];s.hidden=[{kind:'boundary',id:71}];
      p.snapshot=ready();p.lastTarget=picked(ready()).target;const pin=f.V.pin(PROJECT);change();
      assert.deepEqual(plain(f.V.state(PROJECT).hidden),[]);assert.deepEqual(plain(f.V.state(SPACE).hidden),[]);
      assert.equal(f.V.state(PROJECT).lastTarget,null);assert.equal(f.V.state(PROJECT).snapshot,null);assert.equal(f.V.current(pin),false);
    }
  });
  test('U05 pan/zoom invalidates point picks without clearing masks',async()=>{
    const f=fixture();await f.V.read(PROJECT);const s=f.V.state(PROJECT);s.hidden=[{kind:'column',id:83}];
    const pin=f.V.pin(PROJECT);f.V.screenChanged(PROJECT,'2,0,0,2,40,50');
    assert.equal(f.V.current(pin,true),false);assert.equal(f.V.current(pin,false),true);
    assert.deepEqual(plain(s.hidden),[{kind:'column',id:83}]);assert.equal(s.lastTarget,null);
    const gate=deferred();f.respond(async()=>gate.promise);const old=f.V.pick(PROJECT,{viewId:'front',x:100,y:200,r:5});
    await untilSent(f,2);f.V.screenChanged(PROJECT,'3,0,0,3,40,50');gate.resolve(picked(s.snapshot));
    assert.equal((await old).status,'STALE');assert.equal(s.lastTarget,null);
  });
  test('U06 late read and pick cannot overwrite a newer snapshot or owner',async()=>{
    const f=fixture(),first=deferred();let reads=0;
    f.respond(async()=>++reads===1?first.promise:ready({viewKey:'b'.repeat(64)}));
    const older=f.V.read(PROJECT);await untilSent(f,1);const newer=await f.V.read(PROJECT);
    first.resolve(ready());assert.equal((await older).stale,true);assert.equal(f.V.state(PROJECT).snapshot,newer);
    const pickGate=deferred();f.respond(async()=>pickGate.promise);
    const pick=f.V.pick(PROJECT,{viewId:'front',x:100,y:200,r:5});await untilSent(f,3);
    f.env.oc.navigationSequence++;pickGate.resolve(picked(newer));assert.equal((await pick).status,'STALE');
    assert.equal(f.V.state(PROJECT).lastTarget,null);
  });
  test('U07 malformed and over-capacity native reads fail closed with no usable snapshot',async()=>{
    const invalid=[r=>{r.ops[1].owner={kind:'unknown',id:71};},r=>{delete r.ops[1].owner;},
      r=>{r.ops[1].x0=Infinity;},r=>{r.layout.views[0].bounds=[2,0,1,2];},
      r=>{r.layout.views.push(clone(r.layout.views[0]));},r=>{r.extra='unknown';},
      r=>{r.status='CAPACITY';delete r.viewKey;delete r.ops;delete r.layout;}];
    for(const change of invalid){const response=ready();change(response);const f=fixture({readResult:response});
      assert.equal((await f.V.read(PROJECT)).ok,false);assert.equal(f.V.state(PROJECT).snapshot,null);}
    const cap=capResponse();cap.workspace_view.maxOps=1;const f=fixture({cap});
    assert.equal((await f.V.read(PROJECT)).ok,false);assert.equal(f.V.state(PROJECT).snapshot,null);
  });
  test('U08 malformed pick identity, wrong view key and hidden-root hit cannot become a target',async()=>{
    const invalid=[r=>{r.target.root.id=-1;},r=>{r.target.root.id=0x100000000;},r=>{r.target.root.extra=true;},
      r=>{r.target.root.kind='face';},r=>{r.target.memberFace='TOP';},r=>{delete r.target.boundaryId;},
      r=>{r.viewKey='b'.repeat(64);},r=>{r.hoverOps=[{op:'text',x:0,y:0,s:2,t:'bad\0text',owner:null}];},
      r=>{r.status='NONE';},r=>{r.extra='unknown';}];
    for(const change of invalid){const snapshot=ready(),response=picked(snapshot);change(response);
      const f=fixture({readResult:snapshot,pickResult:response});await f.V.read(PROJECT);
      assert.equal((await f.V.pick(PROJECT,{viewId:'front',x:100,y:200,r:5})).status,'INVALID');assert.equal(f.V.state(PROJECT).lastTarget,null);}
    const f=fixture();await f.V.read(PROJECT);f.V.state(PROJECT).hidden=[{kind:'column',id:71}];
    assert.equal((await f.V.pick(PROJECT,{viewId:'front',x:100,y:200,r:5})).status,'INVALID');
  });
  test('U09 top uses native signed coordinates; main and space retain their distinct radius contracts',async()=>{
    const f=fixture({readResult:ready({viewId:'top'})});await f.V.align(PROJECT,'top');await f.V.align(SPACE,'top');
    await f.V.read(PROJECT);await f.V.read(SPACE);
    const main=f.V.locate(f.svg,252,482,PROJECT),space=f.V.locate(f.svg,252,482,SPACE);
    assert.deepEqual(plain(main.nativePoint),{x:101,y:201,r:5,viewId:'top'});
    assert.equal(main.y,-201);assert.equal(main.v,2);assert.equal(space.nativePoint.r,12);
    assert.equal(f.V.locate(f.svg,10000,10000,PROJECT),null);
  });
  test('U10 alignment and restore use read-only presentation state and preserve workspace independence',async()=>{
    const f=fixture(),before=f.guardSnapshot();await f.V.align(PROJECT,'top');
    assert.deepEqual(plain(f.V.state(PROJECT).presentation),{mode:'focus',focus:'top'});
    assert.deepEqual(plain(f.V.state(SPACE).presentation),{mode:'three',focus:null});
    assert.equal(f.env.zoom,1);assert.equal(f.env.panX,0);assert.equal(f.env.panY,0);
    await f.V.align(PROJECT,null);assert.deepEqual(plain(f.V.visibleFrames(PROJECT)),['front','side','bottom']);
    await assert.rejects(f.V.align(PROJECT,'perspective'),/未知/);unchanged(f,before);
  });
  test('U11 unsupported service capability rejects before issuing any view request',async()=>{
    for(const change of [c=>{c.capabilities=[];},c=>{c.workspace_view.frames=['front','side','bottom'];},
      c=>{c.workspace_view.maxRequestBytes=4096;},c=>{c.workspace_view.maxOps=0;},
      c=>{c.extra=true;},c=>{c.workspace_view.extra=true;},c=>{c.workspace_view.frames.push('perspective');}]){
      const cap=capResponse();change(cap);const f=fixture({cap});
      await assert.rejects(f.V.read(PROJECT),/完整三視圖讀取能力/);assert.equal(f.calls.length,0);
    }
  });
  test('U12 losing service and changing browser history invalidates existing leases',async()=>{
    const f=fixture();await f.V.read(PROJECT);let pin=f.V.pin(PROJECT);
    f.history.undo.push({name:'new-action'});assert.equal(f.V.current(pin),false);
    const s=f.V.state(PROJECT);s.hidden=[{kind:'column',id:71}];pin=f.V.pin(PROJECT);f.state.context='context-B';
    assert.equal(f.V.current(pin),false);assert.deepEqual(plain(f.V.state(PROJECT).hidden),[{kind:'column',id:71}]);
    pin=f.V.pin(PROJECT);f.env.connection.phase='offline';f.V.connectionChanged();
    assert.equal(f.V.current(pin),false);assert.equal(f.V.state(PROJECT).snapshot,null);
  });
  test('U13 hiding an already hidden typed root is a no-op without another redraw',async()=>{
    const f=fixture();await f.V.read(PROJECT);await f.V.hideRoot(PROJECT,{kind:'column',id:71});
    const generation=f.V.state(PROJECT).generation,effects=f.effects.length;
    await f.V.hideRoot(PROJECT,{kind:'column',id:71});
    assert.deepEqual(plain(f.V.state(PROJECT).hidden),[{kind:'column',id:71}]);
    assert.equal(f.V.state(PROJECT).generation,generation);assert.equal(f.effects.length,effects);
  });
  test('U14 nested op metadata, exact axes and requested frame sequence are closed contracts',async()=>{
    const invalid=[r=>{r.ops[1].viewId='front';},r=>{r.layout.views[0].down=[0,0,1];},
      r=>{r.layout.views[0].extra=true;},r=>{r.ops[0].viewId='top';},
      r=>{r.layout.views.reverse();},r=>{r.ops.splice(0,6);},
      r=>{r.ops[1]={op:'text',x:1,y:2,s:2,rot:0,t:'member',owner:{kind:'timber',id:71},
        annotation:{kind:'member-face',entityId:71,faceId:'A1',shortLabel:'member',extra:true}};},
      r=>{r.revision='019';}];
    for(const change of invalid){const response=ready();change(response);const f=fixture({readResult:response});
      assert.equal((await f.V.read(PROJECT)).ok,false);assert.equal(f.V.state(PROJECT).snapshot,null);}
    const single=fixture({readResult:ready({viewId:'front'})});
    assert.equal((await single.V.read(PROJECT)).ok,false,'three-view request cannot accept a single front frame');
  });
  test('U15 actual hover scheduler retires its native pick before it can overwrite an exact target',async()=>{
    const f=fixture(),snapshot=ready(),hoverGate=deferred(),frames=[],guards=[],requests=[],applied=[],legacy=[];
    await f.V.read(PROJECT);
    const app=fs.readFileSync(path.join(__dirname,'app.js'),'utf8');
    function region(start,end){const a=app.indexOf(start),b=app.indexOf(end,a+start.length);
      assert.ok(a>=0&&b>a,'Actual app source region missing: '+start);return app.slice(a,b);}
    // Execute the unchanged production functions, including the scheduler's
    // call site and pickAt's handoff to WorkspaceView. Only transport is mocked.
    vm.runInContext(region('async function pickAt(sv)', 'function showOverlay(ops)')+
      region('function createHoverPickScheduler(', 'let projectedHoverOverlay = null;'),f.env,{filename:'app.js:actual-hover-path'});
    f.env.api=async command=>{legacy.push(command);return command==='references'?{ok:true,guides:[{id:0}]}:{ok:true,guide:0};};
    const lateTarget={root:{kind:'guide',id:0},placementId:19,boundaryId:71,memberFace:null};
    const exactTarget={root:{kind:'column',id:83},placementId:null,boundaryId:null,memberFace:null};
    f.respond(async(url,body)=>body.point.x===100?hoverGate.promise:picked(snapshot,exactTarget));
    const scheduler=f.env.createHoverPickScheduler((point,guard)=>{
      guards.push(guard);const promise=f.env.pickAt(point,guard);requests.push(promise);return promise;
    },fn=>{frames.push(fn);return frames.length;},()=>{},()=>{});
    const location=x=>({scope:PROJECT,nativePoint:{viewId:'front',x,y:-300,r:5},v:0,x,y:-300,r:5});
    scheduler.enqueue(location(100),()=>true,result=>applied.push(result));
    assert.equal(frames.length,1);frames.shift()();await untilSent(f,2);
    scheduler.cancel();
    const exact=await f.env.pickAt(location(300));assert.equal(exact.ok,true);
    assert.deepEqual(plain(f.V.state(PROJECT).lastTarget),exactTarget);
    hoverGate.resolve(picked(snapshot,lateTarget));await requests[0];
    for(let i=0;i<8;i++)await Promise.resolve();
    assert.equal(applied.length,0,'Cancelled hover was already prevented from painting by the original scheduler');
    console.log('R11_U15_RACE '+JSON.stringify({guardType:typeof guards[0],legacyCommands:legacy,
      exactTarget,lastTarget:plain(f.V.state(PROJECT).lastTarget),applied:applied.length}));
    assert.deepEqual(plain(f.V.state(PROJECT).lastTarget),exactTarget,'Cancelled native hover must not overwrite the exact context target');
    assert.equal(typeof guards[0],'function','Actual scheduler must pass its ownership guard to the actual request');
    assert.equal(guards[0](),false,'Cancellation must retire the guard already passed into native picking');
    assert.deepEqual(legacy,[],'Retired hover must stop before legacy guide-index mapping reads');
  });
}
async function nativeWire(directory) {
  const files=['native-view-capability.json','native-view-read.json','native-view-pick-boundary.json',
    'native-view-pick-column.json','native-view-pick-timber.json'];
  const records=files.map(name=>{const bytes=fs.readFileSync(path.join(directory,name));return {name,bytes:bytes.length,
    sha256:createHash('sha256').update(bytes).digest('hex'),data:JSON.parse(bytes)};});
  const cap=records[0].data,snapshot=records[1].data,f=fixture({cap,readResult:snapshot});
  await f.V.align(PROJECT,'top');const r=await f.V.read(PROJECT);assert.equal(r.status,'READY');
  assert.deepEqual(plain(r),snapshot);assert.ok(r.ops.some(o=>o.annotation?.kind==='member-face'));
  const actual=[];
  for(const record of records.slice(2)){
    f.respond(async()=>clone(record.data));const hit=await f.V.pick(PROJECT,{viewId:'top',x:0,y:0,r:12});
    assert.equal(hit.status,'HIT',record.name);assert.deepEqual(plain(hit.target),record.data.target);
    actual.push(hit.target);
  }
  assert.deepEqual(actual.map(t=>t.root),[{kind:'boundary',id:71},{kind:'column',id:71},{kind:'timber',id:71}]);
  assert.equal(actual[0].placementId,19);assert.equal(actual[0].boundaryId,71);
  assert.equal(actual[1].placementId,null);assert.equal(actual[1].boundaryId,null);
  assert.ok(['A0','A1','B0','B1','START','END'].includes(actual[2].memberFace));
  console.log('R11_NATIVE_UI_WIRE '+JSON.stringify({schema:'r11-native-ui-wire/1',passed:true,
    input:'Unedited recorded C bridge JSON; transport playback only, no browser claim.',ops:r.ops.length,
    targets:actual,files:records.map(({name,bytes,sha256})=>({name,bytes,sha256}))}));
}
if(require.main===module){
  if(process.argv[2]==='--native-wire'&&process.argv.length===4)nativeWire(process.argv[3]).catch(error=>{console.error(error);process.exitCode=1;});
  else if(process.argv.length===2)registerTests();
  else throw Error('Usage: node workspace_view_state_test.js [--native-wire RECORDING_DIR]');
}
module.exports={fixture,ready,picked,nativeWire};
