'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),R=require('../geometry-web/grid-rule-lines.js');
const ref={kind:'grid-rule-line',appliedGridId:10,systemId:0,ruleKey:7,cellI:'9007199254740993',cellJ:'-9007199254740995',axis:'u',innerIndex:0};
test('RuleLineRef retains complete typed identities and signed strings through both native commands',()=>{
  assert.deepEqual(R.parseAnchor(R.anchor(ref)),ref);assert.deepEqual(R.parseExpression(R.expression(ref)),ref);
  for(const value of [{...ref,ruleKey:0},{...ref,cellI:Number(ref.cellI)},{...ref,cellJ:'-0'},{...ref,kind:'grid-line'}])assert.equal(R.ref(value),null);
  assert.notEqual(R.key(ref),R.key({...ref,systemId:1}));assert.notEqual(R.key(ref),R.key({...ref,appliedGridId:11}));
});
test('query decoder refuses wrong source, cell or synthetic applied reference and retains native clipping',()=>{
  const line={axis:'u',innerIndex:0,coordinate:200,segments:[[[200,0],[200,80]],[[200,120],[200,400]]],ref};
  const q={ok:true,systemId:0,ruleKey:7,cell:[ref.cellI,ref.cellJ],bounds:[0,0,600,400],lines:[line]},target={kind:'grid',id:10,systemId:0,ruleKey:7};
  assert.deepEqual(R.rows(q,target)[0].segments,line.segments);
  assert.throws(()=>R.rows(q,{...target,systemId:1}));assert.throws(()=>R.rows(q,{...target,cell:['0','0']}));
  assert.throws(()=>R.rows(q,{...target,kind:'binding'}));
  const source={...q,lines:[{...line,ref:null}]};assert.equal(R.rows(source,{...target,kind:'system'})[0].ref,null);assert.throws(()=>R.rows(source,target));
});
test('single rule usage includes signed arithmetic references without source-wide overcount',()=>{
  const references={guides:[{id:1,expression:'2*'+R.expression(ref)+'+spec:offset'},{id:2,expression:R.expression({...ref,ruleKey:8})},{id:3,expression:R.expression({...ref,systemId:1})}],timbers:[{id:1,definition:{anchor:R.anchor(ref)}},{id:2,definition:{anchor:'at-line grid 10 u 0'}}]};
  assert.deepEqual(R.usage(references,0,7).guides.map(g=>g.id),[1]);assert.deepEqual(R.usage(references,0,7).timbers.map(t=>t.id),[1]);
});

/* Exercise the shipped closure, including refresh/current/query/bind. The VM
 * hook only exposes its owner for adversarial lifetime observations; it does not
 * replace a production guard or reproduce the focus-restoration algorithm.
 * Native reads and DOM layout are fixtures, not browser acceptance. */
const fs=require('node:fs'),vm=require('node:vm');
const ruleSource=fs.readFileSync(require.resolve('../geometry-web/grid-rule-lines.js'),'utf8');
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}
function exactFocusHarness(source=ruleSource,{replace=true,targetState='visible'}={}){
  const listeners=new Map(),registrations=[],removals=[],focusCalls=[],requests=[],timers=new Map();
  let nextTimer=0,context={id:'project',groups:new Map()},evidenceRevision=1,domVersion=0;
  const document={body:{id:'BODY'},activeElement:null,
    addEventListener(type,listener,capture){if(!listeners.has(type))listeners.set(type,new Set());listeners.get(type).add(listener);registrations.push({type,listener,capture});},
    removeEventListener(type,listener,capture){listeners.get(type)?.delete(listener);removals.push({type,listener,capture});},
  };
  document.activeElement=document.body;
  const dispatch=(type,target=document.body)=>{for(const listener of [...listeners.get(type)||[]])listener({type,target});};
  function node(id,value=''){
    let disabled=false;
    const n={id,value,isConnected:true,hidden:false,version:domVersion,
      addEventListener(){},getClientRects(){return this.isConnected&&!this.hidden?[{width:44,height:44}]:[];},
      focus(options){focusCalls.push({node:this,options});if(this.disabled||!this.getClientRects().length)return;document.activeElement=this;dispatch('focusin',this);},
    };
    Object.defineProperty(n,'disabled',{get:()=>disabled,set(value){disabled=!!value;if(disabled&&document.activeElement===n)document.activeElement=document.body;}});
    return n;
  }
  let controls,status;
  const pane={id:'faceInspectorContent',
    querySelector(selector){return selector==='[data-rule-exact]'?controls.exact:selector==='[data-rule-focus-status]'?status:selector==='[data-rule-focus-key]'?controls.rule:selector==='[data-rule-cell-i]'?controls.i:selector==='[data-rule-cell-j]'?controls.j:selector==='.grid-rule-details,#tbAnchor,#refGuideSource'?controls.exact:null;},
    querySelectorAll(selector){return selector==='[data-rule-source]'?[]:[controls.rule,controls.i,controls.j];},
  };
  function mount(values={rule:'7',i:'-2',j:'1'},applyTargetState=false){
    if(controls){for(const n of Object.values(controls)){n.isConnected=false;if(document.activeElement===n)document.activeElement=document.body;}}
    domVersion++;
    controls={rule:node('gridRuleFocusKey',values.rule),i:node('gridRuleCellI',values.i),j:node('gridRuleCellJ',values.j),exact:node('gridRuleExact')};
    status={textContent:''};
    if(applyTargetState&&targetState==='hidden')controls.exact.hidden=true;
    if(applyTargetState&&targetState==='disabled')controls.exact.disabled=true;
    if(applyTargetState&&targetState==='missing')controls.exact=null;
  }
  mount();
  const viewport={getBoundingClientRect:()=>({width:600,height:400})};
  const $=id=>id==='faceInspectorContent'?pane:id==='faceEditorViewport'?viewport:Object.values(controls).find(n=>n?.id===id)||null;
  const sourceRule={id:0,rules:[{ruleKey:7,name:'Native lines'}]},grid={id:10,sourceSystem:0,bindingId:4};
  const fe={zoom:1,panX:0,panY:0,grids:[grid],ruleFocus:null,ruleSelection:null,timberReferenceData:{sourceFingerprint:'native-fixture'}};
  const oc={edit:{bid:1},focus:{t:'face',id:1},gridSystems:[sourceRule]};
  const reached=deferred(),reply=deferred();
  const nativeReply={ok:true,systemId:0,ruleKey:7,cell:['-2','1'],bounds:[0,0,600,400],lines:[{
    axis:'u',innerIndex:0,coordinate:200,segments:[[[200,0],[200,400]]],
    ref:{...ref,cellI:'-2',cellJ:'1'},
  }]};
  let api,paintCount=0;
  const sandbox={window:{},module:{exports:{}},document,$,fe,oc,
    ReferenceWorkspace:{context:()=>context,getEvidenceState:()=>({revision:evidenceRevision,blocked:false}),history:{frame:1}},
    GeometryProject:{Features:{gridSourceKey:()=> 'confirmed-source'}},SourceInspector:{index:r=>r},
    setTimeout(fn){const id=++nextTimer;timers.set(id,fn);return id;},clearTimeout:id=>timers.delete(id),
    apiRequest:async command=>{requests.push(command);if(command==='source-inspect')return {ok:true,sourceFingerprint:'native-fixture',revision:1};assert.match(command,/^grid-rule-query grid 10 rule 7 cell -2 1$/);reached.resolve();return reply.promise;},
    drawFaceEditor(){},renderFaceInspector(){paintCount++;if(replace){const values={rule:controls.rule.value,i:controls.i.value,j:controls.j.value};mount(values,true);api.bind(pane,grid);}},
  };
  const marker='  Object.assign(api,{refresh,clear,entries,find,select,draw,html,bind,readNative,presentationState,reloadNative});';
  assert.ok(source.includes(marker),'test hook must remain at the production export');
  vm.runInNewContext(source.replace(marker,marker+'\n  api.__testOwner={get:()=>owner};'),sandbox,{filename:'grid-rule-lines.production.js'});
  api=sandbox.window.GridRuleLines;
  api.refresh();api.bind(pane,grid);
  const initialButton=controls.exact,initialOwner=api.__testOwner.get();
  function assertCleanup(){
    assert.equal([...listeners.values()].reduce((n,set)=>n+set.size,0),0,'request must retire every document listener');
    assert.equal(removals.length,registrations.length,'every registration has one removal');
    for(const row of registrations)assert.equal(removals.filter(r=>r.type===row.type&&r.listener===row.listener&&r.capture===row.capture).length,1);
    assert.ok(registrations.every(r=>r.capture===true),'interaction observation uses capture listeners');
  }
  return {document,initialButton,initialOwner,api,fe,oc,requests,focusCalls,registrations,status:()=>status,controls:()=>controls,
    setContext:next=>{context=next;},changeEvidence:()=>evidenceRevision++,dispatch,
    focus(n){document.activeElement=n;dispatch('focusin',n);},
    begin({focused=true}={}){document.activeElement=focused?initialButton:document.body;return initialButton.onclick();},
    reached:reached.promise,release:()=>reply.resolve(nativeReply),reject:error=>reply.reject(error),assertCleanup,
    paintCount:()=>paintCount,
  };
}
async function finishExact(h,pending){h.release();await pending;h.assertCleanup();}
function assertNoFocus(h){assert.equal(h.focusCalls.length,0,'late completion must not call focus');}

test('focused exact read restores only the newly rendered button after native disabled blur',async()=>{
  const h=exactFocusHarness(),pending=h.begin();await h.reached;
  assert.equal(h.document.activeElement,h.document.body);assert.equal(h.initialButton.disabled,true);
  assert.equal(h.registrations.length,3);assert.equal(h.paintCount(),0);
  await finishExact(h,pending);
  const target=h.controls().exact;
  assert.notEqual(target,h.initialButton);assert.equal(h.initialButton.isConnected,false);
  assert.equal(h.document.activeElement,target);assert.equal(h.focusCalls.length,1);
  assert.equal(h.focusCalls[0].node,target);assert.equal(h.focusCalls[0].options.preventScroll,true);
  assert.equal(h.paintCount(),1);assert.equal(h.api.entries().length,1);
  assert.deepEqual(h.requests,['source-inspect','grid-rule-query grid 10 rule 7 cell -2 1','source-inspect']);
});
test('an exact action initiated without button focus never claims focus on completion',async()=>{
  const h=exactFocusHarness(),pending=h.begin({focused:false});await h.reached;await finishExact(h,pending);
  assertNoFocus(h);assert.equal(h.document.activeElement,h.document.body);assert.equal(h.registrations.length,0);
});
test('a user focus move and subsequent blur retire the original exact keyboard target',async()=>{
  const h=exactFocusHarness(),pending=h.begin();await h.reached;
  h.focus(h.controls().i);h.document.activeElement=h.document.body;
  await finishExact(h,pending);assertNoFocus(h);assert.equal(h.document.activeElement,h.document.body);
});
test('a pending exact read cannot steal a user-selected external focus target',async()=>{
  const h=exactFocusHarness(),pending=h.begin();await h.reached;
  const elsewhere={id:'fileMenuBtn'};h.focus(elsewhere);
  await finishExact(h,pending);assertNoFocus(h);assert.equal(h.document.activeElement,elsewhere);
});
for(const type of ['pointerdown','keydown'])test(`a ${type} on blank body prevents late exact focus restoration`,async()=>{
  const h=exactFocusHarness(),pending=h.begin();await h.reached;h.dispatch(type);
  await finishExact(h,pending);assertNoFocus(h);assert.equal(h.document.activeElement,h.document.body);
});
test('an edited raw cell rejects both stale query painting and exact focus restoration',async()=>{
  const h=exactFocusHarness(),pending=h.begin();await h.reached;h.controls().i.value='-3';
  await finishExact(h,pending);assertNoFocus(h);assert.equal(h.paintCount(),0);assert.equal(h.controls().i.value,'-3');
});
test('a replacement rule presentation owner rejects the prior exact focus lease',async()=>{
  const h=exactFocusHarness(),pending=h.begin();await h.reached;h.changeEvidence();h.api.refresh();
  assert.notEqual(h.api.__testOwner.get(),h.initialOwner);
  await finishExact(h,pending);assertNoFocus(h);assert.equal(h.paintCount(),0);
});
test('a new context with the same project id cannot receive the old exact focus lease',async()=>{
  const h=exactFocusHarness(),pending=h.begin();await h.reached;h.setContext({id:'project',groups:new Map()});
  await finishExact(h,pending);assertNoFocus(h);assert.equal(h.paintCount(),0);
});
test('evidence drift invalidates the current exact owner even before a replacement exists',async()=>{
  const h=exactFocusHarness(),pending=h.begin();await h.reached;h.changeEvidence();
  await finishExact(h,pending);assertNoFocus(h);assert.equal(h.api.__testOwner.get(),h.initialOwner);assert.equal(h.paintCount(),0);
});
test('a newer native request prevents an older exact read from restoring focus',async()=>{
  const h=exactFocusHarness(),pending=h.begin();await h.reached;h.initialOwner.request++;
  await finishExact(h,pending);assertNoFocus(h);assert.equal(h.paintCount(),0);
});
for(const targetState of ['hidden','disabled','missing'])test(`a ${targetState} replacement exact target is never focused`,async()=>{
  // Only the response renderer applies the unavailable-target state.
  const h=exactFocusHarness(undefined,{targetState}),pending=h.begin();await h.reached;
  await finishExact(h,pending);assertNoFocus(h);assert.equal(h.document.activeElement,h.document.body);assert.equal(h.paintCount(),1);
});
test('an unchanged live exact button is reenabled before keyboard focus is restored',async()=>{
  const h=exactFocusHarness(undefined,{replace:false}),pending=h.begin();await h.reached;
  await finishExact(h,pending);assert.equal(h.initialButton.disabled,false);assert.equal(h.document.activeElement,h.initialButton);
  assert.equal(h.focusCalls.length,1);assert.equal(h.focusCalls[0].options.preventScroll,true);
});
test('invalid raw cell admission retains original focus and cleans all observation listeners',async()=>{
  const h=exactFocusHarness();h.controls().i.value='-0';await h.begin();h.assertCleanup();
  assert.match(h.status().textContent,/signed 64/);assert.equal(h.requests.length,0);assertNoFocus(h);
  assert.equal(h.document.activeElement,h.initialButton);assert.equal(h.initialButton.disabled,false);
});
test('an expired face at initiation returns before native reads and still retires its listeners',async()=>{
  const h=exactFocusHarness();h.oc.edit=null;await h.begin();h.assertCleanup();
  assert.equal(h.requests.length,0);assertNoFocus(h);assert.equal(h.document.activeElement,h.initialButton);
  assert.equal(h.initialButton.disabled,false);
});
test('a native read failure retires listeners and restores the still-owned replacement target',async()=>{
  const h=exactFocusHarness(),pending=h.begin();await h.reached;h.reject(new Error('native read unavailable'));await pending;h.assertCleanup();
  assert.equal(h.paintCount(),1);assert.equal(h.document.activeElement,h.controls().exact);assert.equal(h.focusCalls.length,1);
  assert.deepEqual(Array.from(h.api.__testOwner.get().messages),['native read unavailable']);
});
test('a stale native failure neither paints nor steals focus and still cleans its listeners',async()=>{
  const h=exactFocusHarness(),pending=h.begin();await h.reached;h.setContext({id:'replacement',groups:new Map()});
  h.reject(new Error('late native read unavailable'));await pending;h.assertCleanup();assertNoFocus(h);assert.equal(h.paintCount(),0);
});
test('focus lease guard removals are killed by the real deferred handler counterexamples',async()=>{
  const mutations=[
    {name:'initiating focus',before:'if(retainFocus&&!interrupted&&focusOwner',after:'if(!interrupted&&focusOwner',focused:false},
    {name:'user interruption',before:'retainFocus&&!interrupted&&focusOwner',after:'retainFocus&&focusOwner',during:h=>h.dispatch('pointerdown')},
    {name:'current context',before:'&&current(focusOwner)&&',after:'&&',during:h=>h.setContext({id:'project',groups:new Map()})},
    {name:'owner lifetime',before:'&&focusOwner===owner&&current(focusOwner)&&',after:'&&',during:h=>{h.changeEvidence();h.api.refresh();}},
    {name:'request generation',before:'focusOwner.request===focusRequest&&',after:'',during:h=>h.initialOwner.request++},
    {name:'raw tuple',before:'focusInput===focusInputs()&&',after:'',during:h=>h.controls().i.value='-3'},
    {name:'enabled target',before:'&&!target.disabled&&',after:'&&',targetState:'disabled'},
    {name:'rendered target',before:'&&target.getClientRects().length)',after:')',targetState:'hidden'},
  ];
  for(const mutation of mutations){
    assert.equal(ruleSource.split(mutation.before).length,2,`${mutation.name}: mutate one exact production guard`);
    const h=exactFocusHarness(ruleSource.replace(mutation.before,mutation.after),{targetState:mutation.targetState}),
      pending=h.begin({focused:mutation.focused!==false});
    await h.reached;mutation.during?.(h);await finishExact(h,pending);
    assert.throws(()=>assertNoFocus(h),/late completion must not call focus/,`${mutation.name}: the unchanged refusal oracle must turn red`);
  }
});
