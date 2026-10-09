/* Shipped ScenarioWorkspace Node VM contracts. DOM/iframe, storage-owner APIs,
 * archive, and HTTP are controlled mocks: these are not browser/IDB/native E2E. */
'use strict';
const {test:nodeTest}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const test=(name,fn)=>nodeTest(name,{timeout:5000},fn),clone=structuredClone;
const code=fs.readFileSync(require.resolve('../geometry-web/scenario-workspace.js'),'utf8');
const ROOT='a'.repeat(32),CONTEXT='b'.repeat(32),OTHER='c'.repeat(32);
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
const turn=()=>new Promise(resolve=>setImmediate(resolve));
async function until(check){for(let n=0;n<100;n++){if(check())return;await turn();}assert.fail('mock boundary was not reached');}
const ticket=(phase='active')=>({schema:'scenario-editor-ticket/1',rootSession:ROOT,
  request:{action:'create',requestId:'00000000-0000-4000-8000-000000000001',sequence:1,session:ROOT},
  scenarioId:'scenario-B',label:'Retained B',phase,context:phase==='creating'?null:CONTEXT,eligible:false,
  retirement:phase==='retiring'?{reason:'cancel'}:null});
function fixture(options={},store={ticket:null}){
  const events=[],posts=[],requests=[],confirmations=[],listeners=new Set(),elements=new Map();let uuids=0,frozen=false,commits=0;
  const root={revision:1,catalog:{scenarios:[{scenarioId:'scenario-A',label:'A'},{scenarioId:'scenario-B',label:'B'}]},scene:'A untouched',dirty:true};
  function element(id){if(elements.has(id))return elements.get(id);const handlers={};
    const el={value:id==='scenarioAfter'?'scenario-B':'',textContent:'',disabled:false,hidden:false,inert:false,open:false,children:[],
      addEventListener(type,fn){handlers[type]=fn;},dispatch(type){return handlers[type]?.({preventDefault(){}});},
      replaceChildren(){this.children=[];},append(...children){this.children.push(...children);if(!this.value&&children[0]?.value)this.value=children[0].value;},
      querySelectorAll(){return [];},querySelector(){return element('closeMain');},showModal(){this.open=true;},close(){this.open=false;},click(){return this.onclick?.();}};
    elements.set(id,el);return el;
  }
  const frame=element('scenarioEditorFrame');let src='about:blank';
  Object.defineProperty(frame,'src',{get:()=>src,set:value=>{src=value;events.push('frame:'+value);if(value!=='about:blank')setImmediate(()=>frame.onload?.());}});
  const win={addEventListener:(type,fn)=>{if(type==='message')listeners.add(fn);},removeEventListener:(type,fn)=>{if(type==='message')listeners.delete(fn);}};
  const deliver=async data=>{const event={origin:'https://geometry.test',source:frame.contentWindow,data};await Promise.all([...listeners].map(fn=>fn(event)));};
  frame.contentWindow={postMessage(data){posts.push(clone(data));events.push('child:'+data.type);
    Promise.resolve().then(async()=>{let result={};
      if(data.type==='scenario-open'){assert.equal(frame.inert,true,'iframe stays inert through import');events.push('initialize');await options.importGate?.promise;if(options.importError)throw Error('initialization unknown');}
      else if(data.type==='scenario-export'){frozen=true;events.push('freeze');await options.exportGate?.promise;result={bytes:new Uint8Array([2]),freezeToken:'freeze-token'};}
      else if(data.type==='scenario-assert-frozen'){events.push('freeze:verify');await options.verifyGate?.promise;if(options.verifyError)throw Error('freeze is stale');assert.equal(frozen,true);}
      else if(data.type==='scenario-release'){events.push('freeze:release');await options.releaseGate?.promise;frozen=false;events.push('freeze:released');}
      await deliver({requestId:data.requestId,ok:true,...result});
    }).catch(error=>deliver({requestId:data.requestId,ok:false,error:error.message}));
  }};
  const exact=t=>assert.deepEqual(clone(t),store.ticket,'mock owner CAS compares full expected ticket');
  const W={
    getEvidenceState:()=>({contextToken:'A-context',revision:root.revision,nativeRevision:1,session:ROOT,blocked:!!options.blocked}),
    getModelOperationState:()=>({frame:'A-frame',undo:'A-undo',redo:null}),
    readScenarioCatalog:()=>({catalog:clone(root.catalog),sources:new Map()}),
    readScenarioEditorTicket:async()=>{events.push('ticket:read');if(options.readError)throw Error('malformed reserved ticket');return clone(store.ticket);},
    createScenarioEditorTicket:async input=>{events.push('ticket:create:begin');await options.persistGate?.promise;if(options.persistError)throw Error('storage refused');assert.equal(store.ticket,null);
      store.ticket={...ticket('creating'),request:clone(input.request),scenarioId:input.scenarioId,label:input.label};events.push('ticket:creating');
      if(options.persistUnknown)throw Error('ticket commit acknowledgement unknown');return clone(store.ticket);},
    updateScenarioEditorTicket:async(expected,change)=>{events.push('ticket:update:'+change.phase+':begin');if(change.phase==='initializing')await options.bindGate?.promise;
      if(change.phase==='active')await options.activeGate?.promise;
      exact(expected);store.ticket={...clone(expected),...clone(change)};events.push('ticket:'+change.phase);return clone(store.ticket);},
    markScenarioEditorRetiring:async(expected,reason)=>{events.push('ticket:cancel:begin');await options.cancelGate?.promise;if(options.cancelError)throw Error('cancel storage refused');exact(expected);
      store.ticket={...clone(expected),phase:'retiring',retirement:clone(reason)};events.push('ticket:cancel:durable');return clone(store.ticket);},
    verifyScenarioEditorRetirement:async expected=>{events.push('ticket:verify');exact(expected);if(options.retirementError)throw Error('retirement proof refused');assert.equal(expected.phase,'retiring');return true;},
    clearScenarioEditorTicket:async expected=>{events.push('ticket:clear');exact(expected);assert.equal(expected.phase,'retiring');store.ticket=null;},
    commitScenarioCatalog(){events.push('A:legacy-commit');throw Error('Finish must use the durable owner operation');},
    finishScenarioEditor:async(catalog,sources,expected,guard)=>{events.push('finish:begin');guard();assert.equal(frozen,true);exact(expected);await options.checkpointGate?.promise;
      if(options.checkpointError)throw Error('checkpoint refused');guard();exact(expected);
      store.ticket={...clone(expected),phase:'retiring',retirement:{reason:'finish',checkpoint:'receipt'}};events.push('finish:durable');
      root.catalog=clone(catalog);root.revision++;commits++;events.push('A:commit');return {ticket:clone(store.ticket),checkpoint:'receipt'};},
    initializeScenarioProject:async(bytes,name,t)=>{events.push('owner:initialize');posts.push({initialized:{bytes,name,ticket:t}});await options.initializeGate?.promise;},
    freezeScenarioProject:async()=>{events.push('owner:freeze');await options.freezeGate?.promise;frozen=true;return {bytes:new Uint8Array([2]),freezeToken:'freeze-token'};},
    assertScenarioFrozen:async token=>{events.push('owner:verify');assert.equal(token,'freeze-token');assert.equal(frozen,true);},
    releaseScenarioProject:async token=>{events.push('owner:release');assert.equal(token,'freeze-token');frozen=false;},
    importBytes(){assert.fail('ordinary importBytes must not bootstrap B');},exportBytes(){assert.fail('ordinary exportBytes cannot freeze B');}
  };
  const I={read:async(catalog,sources,guard)=>{events.push('archive');guard();let next=clone(catalog);return {list:()=>clone(next.scenarios),
    project:()=>({scene:'B baseline',manifest:{name:'B'},sources:new Map()}),
    replace:async(id,project)=>{events.push('replace:begin');await options.replaceGate?.promise;guard();next.scenarios.find(s=>s.scenarioId===id).edited=true;events.push('replace');},
    catalog:()=>clone(next)};},exportCatalog:a=>a.catalog(),exportSources:()=>new Map()};
  const parent={postMessage:data=>{posts.push(clone(data));events.push('parent:reply');}};
  const env={window:win,document:{getElementById:element,createElement:tag=>element(tag+':'+elements.size)},ReferenceWorkspace:W,ScenarioIntegration:I,
    GeometryProject:{pack:async()=>{events.push('pack');return new Uint8Array([1]);},unpack:async()=>{events.push('unpack');await options.unpackGate?.promise;return {scene:'B changed',manifest:{},sources:new Map()};}},
    ScenarioDiff:{},ParameterUI:{},fflate:{},crypto:{randomUUID:()=>{uuids++;return '00000000-0000-4000-8000-'+String(uuids+(options.uuidSeed||0)).padStart(12,'0');}},
    structuredClone,AbortController,AbortSignal,Uint8Array,TextEncoder,TextDecoder,atob,Map,Set,JSON,Date,console,setTimeout,clearTimeout,
    location:{origin:'https://geometry.test'},parent,connection:{phase:'ready'},confirm:message=>{confirmations.push(message);return options.confirm!==false;},
    fetch:async(url,init)=>{assert.equal(url,'/scenarios/editor');if(!init){events.push('http:status');return {ok:true,json:async()=>options.status||{ok:true,sequence:1,session:ROOT}};}
      const request=JSON.parse(init.body);requests.push(request);events.push('http:'+request.action);const ordinal=requests.filter(r=>r.action===request.action).length;
      if(options.http)return options.http(request,ordinal);
      if(request.action==='create')await options.createGate?.promise;
      if(request.action==='close')await options.closeGate?.promise;
      if(request.action==='create'&&options.createLost)throw Error('create response lost');
      if(request.action==='close'&&options.closeLost)throw Error('close response lost');
      return {ok:true,json:async()=>request.action==='create'?(options.createResult||{ok:true,context:CONTEXT}):(options.closeResult||{ok:true,state:'retired'})};}
  };
  if(options.child)win.GeometryNativeContext={scenario:CONTEXT};
  vm.runInNewContext(code,env);win.ScenarioWorkspace.open();
  return {options,store,events,posts,requests,confirmations,root,element,frame,W,parent,
    start:()=>element('scenarioEdit').onclick(),cancel:()=>element('scenarioCancelEdit').onclick(),finish:()=>element('scenarioFinishEdit').onclick(),
    message:async(data,{source=parent,origin=env.location.origin}={})=>Promise.all([...listeners].map(fn=>fn({source,origin,data}))),
    get uuids(){return uuids;},get frozen(){return frozen;},get commits(){return commits;}};
}
const before=(f,a,b)=>assert.ok(f.events.indexOf(a)>=0&&f.events.indexOf(a)<f.events.indexOf(b),a+' must precede '+b);

test('twelve interrupted reload/Edit attempts retain one identity without allocation, iframe or import',async()=>{
  const store={ticket:ticket()},original=clone(store.ticket);
  for(let n=0;n<12;n++){const f=fixture({},store),a=clone(f.root);await f.start();assert.deepEqual(store.ticket,original);assert.equal(f.uuids,0);
    // The original fixture cannot prove an active surviving B. Its one exact
    // read-only resolver is allowed; it cannot authorize another allocation.
    assert.deepEqual(f.requests,[{...original.request,action:'resolve',context:original.context}]);
    assert.deepEqual(f.events,['ticket:read','http:resolve'],'no ticket rewrite, import, freeze or A commit');
    assert.deepEqual(f.root,a);assert.equal(f.commits,0);assert.equal(f.frozen,false);
    assert.equal(f.posts.length,0);assert.equal(f.frame.src,'about:blank');assert.equal(f.frame.inert,true);
    assert.equal(f.element('scenarioFinishEdit').disabled,true);assert.match(f.element('scenarioEditorStatus').textContent,/保留/);}
});
test('interrupted creating and initializing tickets never replay create or ordinary import',async()=>{
  for(const phase of ['creating','initializing']){const f=fixture({},{ticket:ticket(phase)});await f.start();assert.equal(f.requests.length,0);assert.equal(f.posts.length,0);assert.equal(f.element('scenarioEditorDialog').open,true);}
});
test('recovered discard specifically names B and warns it may be open elsewhere; declining retains all data',async()=>{
  const f=fixture({confirm:false},{ticket:ticket()}),original=clone(f.store.ticket),a=clone(f.root);await f.start();await f.cancel();
  assert.equal(f.confirmations.length,1);for(const value of ['Retained B','scenario-B',CONTEXT,'其他分頁'])assert.ok(f.confirmations[0].includes(value));
  assert.deepEqual(f.store.ticket,original);assert.deepEqual(f.requests,[{...original.request,action:'resolve',context:original.context}]);
  assert.deepEqual(f.events,['ticket:read','http:resolve'],'declined discard sends no close or owner mutation');
  assert.deepEqual(f.root,a);assert.equal(f.uuids,0);assert.equal(f.commits,0);assert.equal(f.frozen,false);assert.equal(f.posts.length,0);
  assert.equal(f.frame.src,'about:blank');assert.equal(f.frame.inert,true);assert.equal(f.element('scenarioFinishEdit').disabled,true);
  assert.equal(f.element('scenarioEditorDialog').open,true);
});
test('confirmed recovered discard persists intent before exact close and preserves A',async()=>{
  const f=fixture({},{ticket:ticket()}),a=clone(f.root),original=clone(f.store.ticket);await f.start();await f.cancel();
  before(f,'ticket:cancel:durable','http:close');assert.deepEqual(f.requests,[
    {...original.request,action:'resolve',context:original.context},{...original.request,action:'close'}]);
  assert.deepEqual(f.events,['ticket:read','http:resolve','ticket:read','ticket:cancel:begin','ticket:cancel:durable',
    'ticket:verify','http:close','ticket:clear','frame:about:blank'],'only durable discard and exact retirement may mutate the owner');
  assert.equal(f.store.ticket,null);assert.deepEqual(f.root,a);assert.equal(f.uuids,0);assert.equal(f.commits,0);
  assert.equal(f.frozen,false);assert.equal(f.posts.length,0);assert.equal(f.frame.src,'about:blank');assert.equal(f.frame.inert,true);
});
test('unreadable or malformed reserved ticket fails closed before any allocation',async()=>{
  const f=fixture({readError:true});await f.start();assert.equal(f.requests.length,0);assert.equal(f.uuids,0);assert.match(f.element('scenarioStatus').textContent,/malformed/);
});
test('pre-create ticket storage refusal sends zero create and leaves A unchanged',async()=>{
  const f=fixture({persistError:true}),a=clone(f.root);await f.start();assert.equal(f.requests.length,0);assert.equal(f.store.ticket,null);assert.deepEqual(f.root,a);assert.match(f.element('scenarioStatus').textContent,/storage refused/);
});
test('lost pre-create ticket acknowledgement retains the committed identity and blocks the next fresh attempt',async()=>{
  const store={ticket:null},f=fixture({persistUnknown:true},store);await f.start();assert.equal(f.requests.length,0);assert.equal(store.ticket.phase,'creating');const original=clone(store.ticket);
  const next=fixture({},store);await next.start();assert.deepEqual(store.ticket,original);assert.equal(next.uuids,0);assert.equal(next.requests.length,0);assert.equal(next.posts.length,0);
});
test('simultaneous Edit callers share the owner CAS fence and dispatch at most one fresh create',async()=>{
  const store={ticket:null},gate=deferred(),first=fixture({persistGate:gate},store),second=fixture({persistGate:gate,uuidSeed:100},store);
  const one=first.start(),two=second.start();await until(()=>first.events.includes('ticket:create:begin')&&second.events.includes('ticket:create:begin'));gate.resolve();await Promise.all([one,two]);
  const requests=[...first.requests,...second.requests];assert.equal(requests.filter(r=>r.action==='create').length,1);assert.equal(store.ticket.phase,'active');assert.deepEqual(requests[0],store.ticket.request);
});
test('fresh flow persists creating before create and context before iframe, importing exact ticket while inert',async()=>{
  const f=fixture();await f.start();before(f,'ticket:creating','http:create');before(f,'ticket:initializing','frame:/?scenario='+CONTEXT);
  before(f,'initialize','ticket:active');const open=f.posts.find(p=>p.type==='scenario-open');assert.equal(open.ticket.phase,'initializing');assert.equal(open.ticket.context,CONTEXT);
  assert.deepEqual(open.ticket.request,f.requests[0]);assert.equal(open.name,'B.gcanvas');assert.equal(f.frame.inert,false);assert.equal(f.store.ticket.phase,'active');assert.equal(f.element('scenarioFinishEdit').disabled,false);
});
test('invalid service identity or sequence never persists or dispatches a create',async()=>{
  for(const status of [{ok:true,session:OTHER,sequence:1},{ok:true,session:ROOT,sequence:0},{ok:true,session:ROOT,sequence:1.2},{ok:true,session:'invalid',sequence:1}]){
    const f=fixture({status});await f.start();assert.equal(f.store.ticket,null);assert.equal(f.requests.length,0);assert.equal(f.uuids,0);}
});
test('two lost create replies retain exact creating ticket without auto-close or initialization',async()=>{
  const f=fixture({createLost:true});await f.start();assert.equal(f.requests.length,2);assert.deepEqual(f.requests[0],f.requests[1]);assert.deepEqual(f.store.ticket.request,f.requests[0]);
  assert.equal(f.store.ticket.phase,'creating');assert.equal(f.posts.length,0);assert.equal(f.element('scenarioEditorDialog').open,true);assert.equal(f.element('scenarioFinishEdit').disabled,true);
});
test('malformed or root-context create reply retains ticket without mounting the iframe',async()=>{
  for(const createResult of [{ok:true,context:'bad'},{ok:true,context:ROOT},{ok:true,context:CONTEXT,session:OTHER}]){const f=fixture({createResult});await f.start();
    assert.equal(f.store.ticket.phase,'creating');assert.equal(f.frame.src,'about:blank');assert.equal(f.requests.length,1);assert.equal(f.posts.length,0);}
});
test('unknown initialization retains its context and ticket without implicit discard',async()=>{
  const f=fixture({importError:true});await f.start();assert.equal(f.store.ticket.phase,'initializing');assert.equal(f.frame.src,'/?scenario='+CONTEXT);assert.equal(f.frame.inert,true);
  assert.equal(f.requests.filter(r=>r.action==='close').length,0);assert.equal(f.element('scenarioFinishEdit').disabled,true);assert.match(f.element('scenarioEditorStatus').textContent,/保留/);
});
test('Cancel wins a held create; its late response cannot bind, mount, import or resurrect',async()=>{
  const gate=deferred(),f=fixture({createGate:gate});const start=f.start();await until(()=>f.requests.length===1);await f.cancel();assert.equal(f.store.ticket,null);gate.resolve();await start;
  assert.equal(f.posts.length,0);assert.equal(f.events.includes('ticket:initializing'),false);assert.equal(f.frame.src,'about:blank');assert.equal(f.requests[1].requestId,f.requests[0].requestId);
});
test('Cancel waits an in-flight binding CAS, then retires its latest exact version without iframe import',async()=>{
  const gate=deferred(),f=fixture({bindGate:gate});const start=f.start();await until(()=>f.events.includes('ticket:update:initializing:begin'));
  const cancel=f.cancel();await turn();assert.equal(f.requests.length,1);gate.resolve();await Promise.all([start,cancel]);
  before(f,'ticket:initializing','ticket:cancel:durable');assert.equal(f.posts.length,0);assert.equal(f.store.ticket,null);assert.equal(f.frame.src,'about:blank');
});
test('Cancel during import aborts the wait; a late import acknowledgement never promotes active',async()=>{
  const gate=deferred(),f=fixture({importGate:gate});const start=f.start();await until(()=>f.events.includes('initialize'));await f.cancel();await start;gate.resolve();await turn();
  assert.equal(f.store.ticket,null);assert.equal(f.events.includes('ticket:active'),false);assert.equal(f.element('scenarioEditorDialog').open,false);assert.equal(f.frame.inert,true);
});
test('Cancel racing the active CAS retires that exact committed phase and never re-enables the frame',async()=>{
  const gate=deferred(),f=fixture({activeGate:gate});const start=f.start();await until(()=>f.events.includes('ticket:update:active:begin'));
  const cancel=f.cancel();gate.resolve();await Promise.all([start,cancel]);before(f,'ticket:active','ticket:cancel:durable');assert.equal(f.store.ticket,null);assert.equal(f.frame.inert,true);
});
test('unknown close preserves a retiring exact tuple; explicit retry clears only its confirmed retirement',async()=>{
  const options={closeLost:true},f=fixture(options);await f.start();const original=clone(f.store.ticket);await f.cancel();assert.equal(f.store.ticket.phase,'retiring');
  assert.equal(f.element('scenarioEditorDialog').open,true);assert.equal(f.element('scenarioFinishEdit').disabled,true);assert.equal(f.requests.length,3);
  options.closeLost=false;await f.cancel();assert.equal(f.store.ticket,null);assert.equal(f.confirmations.length,0);
  for(const r of f.requests.slice(1))assert.deepEqual(r,{...original.request,action:'close'});
});
test('close success without retired state cannot erase the durable ticket',async()=>{
  const f=fixture({closeResult:{ok:true,state:'unknown'}});await f.start();await f.cancel();assert.equal(f.store.ticket.phase,'retiring');assert.equal(f.events.includes('ticket:clear'),false);
});
test('discovered retirement must verify before replay and never permits fresh allocation on failed proof',async()=>{
  const f=fixture({retirementError:true},{ticket:ticket('retiring')});await f.start();assert.equal(f.requests.length,0);assert.equal(f.store.ticket.phase,'retiring');assert.equal(f.uuids,0);
});
test('verified discovered retirement replays only exact close before another user-requested Edit',async()=>{
  const saved=ticket('retiring'),f=fixture({},{ticket:saved});await f.start();assert.deepEqual(f.requests,[{...saved.request,action:'close'}]);assert.equal(f.store.ticket,null);assert.equal(f.uuids,0);
  await f.start();assert.equal(f.requests[1].action,'create');assert.equal(f.store.ticket.phase,'active');
});
test('Finish freezes and verifies B, durably writes A before exact close, and never separately commits catalog',async()=>{
  const f=fixture();await f.start();await f.finish();before(f,'freeze','unpack');before(f,'replace','freeze:verify');before(f,'freeze:verify','finish:begin');
  before(f,'finish:durable','A:commit');before(f,'A:commit','http:close');assert.equal(f.events.includes('A:legacy-commit'),false);assert.equal(f.commits,1);assert.equal(f.store.ticket,null);
  assert.equal(f.root.catalog.scenarios[1].edited,true);assert.equal(f.root.scene,'A untouched');assert.equal(f.element('scenarioEditorDialog').open,false);
});
test('checkpoint failure preserves A and active ticket, releases B freeze, and sends no close',async()=>{
  const options={checkpointError:true},f=fixture(options);await f.start();const a=clone(f.root),original=clone(f.store.ticket);await f.finish();
  assert.deepEqual(f.root,a);assert.deepEqual(f.store.ticket,original);assert.equal(f.requests.filter(r=>r.action==='close').length,0);assert.equal(f.frozen,false);assert.equal(f.frame.inert,false);
  assert.equal(f.element('scenarioFinishEdit').disabled,false);options.checkpointError=false;await f.finish();assert.equal(f.commits,1);
});
test('Cancel during held export aborts its wait immediately while discard journaling remains pending',async()=>{
  const exportGate=deferred(),cancelGate=deferred(),f=fixture({exportGate,cancelGate});await f.start();const a=clone(f.root),finish=f.finish();await until(()=>f.events.includes('freeze'));
  const cancel=f.cancel();await until(()=>f.events.includes('ticket:cancel:begin'));assert.equal(f.requests.filter(r=>r.action==='close').length,0);assert.equal(f.store.ticket.phase,'active');
  cancelGate.resolve();await cancel;await finish;exportGate.resolve();await turn();assert.deepEqual(f.root,a);assert.equal(f.commits,0);assert.equal(f.store.ticket,null);
});
test('Cancel during held archive replacement prevents every late A commit',async()=>{
  const gate=deferred(),f=fixture({replaceGate:gate});await f.start();const a=clone(f.root),finish=f.finish();await until(()=>f.events.includes('replace:begin'));
  await f.cancel();gate.resolve();await finish;assert.deepEqual(f.root,a);assert.equal(f.commits,0);assert.equal(f.events.includes('finish:begin'),false);
});
test('Cancel during held freeze verification prevents the critical checkpoint from starting',async()=>{
  const gate=deferred(),f=fixture({verifyGate:gate});await f.start();const a=clone(f.root),finish=f.finish();await until(()=>f.events.includes('freeze:verify'));
  await f.cancel();await finish;gate.resolve();await turn();assert.deepEqual(f.root,a);assert.equal(f.events.includes('finish:begin'),false);assert.equal(f.store.ticket,null);
});
test('critical checkpoint blocks Cancel, Escape and main close until its terminal result',async()=>{
  const gate=deferred(),f=fixture({checkpointGate:gate});await f.start();const finish=f.finish();await until(()=>f.events.includes('finish:begin'));
  assert.equal(f.element('scenarioCancelEdit').disabled,true);await f.cancel();f.element('scenarioEditorDialog').dispatch('cancel');f.element('closeMain').onclick();
  assert.equal(f.events.includes('ticket:cancel:begin'),false);assert.equal(f.element('scenarioEditorDialog').open,true);assert.equal(f.element('scenarioDialog').open,true);
  gate.resolve();await finish;assert.equal(f.commits,1);assert.equal(f.store.ticket,null);
});
test('stale freeze verification cannot reach checkpoint or close and releases the owned freeze',async()=>{
  const f=fixture({verifyError:true});await f.start();await f.finish();assert.equal(f.events.includes('finish:begin'),false);assert.equal(f.requests.filter(r=>r.action==='close').length,0);
  assert.equal(f.frozen,false);assert.equal(f.store.ticket.phase,'active');
});
test('successful durable Finish plus lost close stays frozen/retiring and retry does not duplicate A history',async()=>{
  const options={closeLost:true},f=fixture(options);await f.start();await f.finish();assert.equal(f.store.ticket.phase,'retiring');assert.equal(f.store.ticket.retirement.reason,'finish');
  assert.equal(f.commits,1);assert.equal(f.frozen,true);assert.equal(f.frame.inert,true);assert.equal(f.element('scenarioFinishEdit').disabled,true);
  options.closeLost=false;await f.cancel();assert.equal(f.store.ticket,null);assert.equal(f.commits,1);assert.equal(f.events.filter(e=>e==='finish:begin').length,1);
});
test('Cancel during Finish retirement coalesces the existing close and deletes the ticket once',async()=>{
  const gate=deferred(),f=fixture({closeGate:gate});await f.start();const finish=f.finish();await until(()=>f.events.includes('http:close'));
  const cancel=f.cancel();await turn();assert.equal(f.requests.filter(r=>r.action==='close').length,1);gate.resolve();await Promise.all([finish,cancel]);
  assert.equal(f.events.filter(e=>e==='ticket:clear').length,1);assert.equal(f.commits,1);assert.equal(f.store.ticket,null);
});
test('Cancel waits an already-dispatched failed-Finish freeze release before persisting retirement',async()=>{
  const gate=deferred(),f=fixture({checkpointError:true,releaseGate:gate});await f.start();const finish=f.finish();await until(()=>f.events.includes('freeze:release'));
  const cancel=f.cancel();await turn();assert.equal(f.events.includes('ticket:cancel:durable'),false);assert.equal(f.requests.filter(r=>r.action==='close').length,0);
  gate.resolve();await Promise.all([finish,cancel]);before(f,'freeze:released','ticket:cancel:durable');assert.equal(f.store.ticket,null);assert.equal(f.frame.inert,true);
});
test('failed explicit Cancel journal never closes B or changes A',async()=>{
  const f=fixture({cancelError:true});await f.start();const a=clone(f.root);await f.cancel();assert.equal(f.store.ticket.phase,'active');assert.deepEqual(f.root,a);
  assert.equal(f.requests.filter(r=>r.action==='close').length,0);assert.equal(f.element('scenarioEditorDialog').open,true);assert.equal(f.frame.inert,true);
});
test('child bootstrap invokes authorized initializer with exact ticket and no ordinary import',async()=>{
  const f=fixture({child:true}),t=ticket('initializing'),bytes=new Uint8Array([3]);await f.message({type:'scenario-open',requestId:'open',bytes,name:'B.gcanvas',ticket:t});
  assert.equal(f.events.filter(e=>e==='owner:initialize').length,1);assert.deepEqual(f.posts.find(p=>p.initialized).initialized,{bytes,name:'B.gcanvas',ticket:t});assert.equal(f.posts.at(-1).ok,true);
});
test('child protocol ignores wrong origin or source before all owner operations',async()=>{
  const f=fixture({child:true});const data={type:'scenario-open',requestId:'open',ticket:ticket('initializing')};await f.message(data,{origin:'https://foreign.test'});await f.message(data,{source:{}});
  assert.equal(f.posts.length,0);assert.equal(f.events.length,0);
});
test('child export remains frozen through parent verification and releases only the exact owned freeze',async()=>{
  const f=fixture({child:true});await f.message({type:'scenario-export',requestId:'export',freezeId:'owned'});assert.equal(f.frozen,true);assert.equal(f.posts.at(-1).freezeToken,'freeze-token');
  await f.message({type:'scenario-release',requestId:'wrong',freezeId:'other',freezeToken:'freeze-token'});assert.equal(f.posts.at(-1).ok,false);assert.equal(f.frozen,true);
  await f.message({type:'scenario-assert-frozen',requestId:'verify',freezeId:'owned',freezeToken:'freeze-token'});assert.equal(f.posts.at(-1).ok,true);assert.equal(f.frozen,true);
  await f.message({type:'scenario-release',requestId:'release',freezeId:'owned',freezeToken:'freeze-token'});assert.equal(f.frozen,false);assert.equal(f.posts.at(-1).ok,true);
});
test('child release can settle an export whose reply is still pending without losing the freeze token',async()=>{
  const gate=deferred(),f=fixture({child:true,freezeGate:gate});const exporting=f.message({type:'scenario-export',requestId:'export',freezeId:'owned'});
  await until(()=>f.events.includes('owner:freeze'));const releasing=f.message({type:'scenario-release',requestId:'release',freezeId:'owned'});gate.resolve();await Promise.all([exporting,releasing]);
  assert.equal(f.frozen,false);assert.equal(f.events.filter(e=>e==='owner:freeze').length,1);assert.equal(f.events.filter(e=>e==='owner:release').length,1);
});
