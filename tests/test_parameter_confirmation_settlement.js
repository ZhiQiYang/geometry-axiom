'use strict';
// Execute the shipped ParameterUI closure, including pending, mayLeave and
// confirmation locking. Only native outcomes, DOM nodes and delayed reads are
// finite host fixtures; the independent browser gate proves actual navigation.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(process.env.GEOMETRY_PARAMETER_CONFIRM_SOURCE||path.join(__dirname,'../geometry-web/parameters.js'),'utf8').split('\n/* GEO-227')[0];
const exportStart='return {value,formatDefinition:expression';
assert.equal(source.split(exportStart).length,2,'one shipped ParameterUI export boundary');
const executable=source.replace(exportStart,'return {__confirmationTest:{confirm,getState:()=>state,setState:value=>{state=value;}},value,formatDefinition:expression');
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}
function node(id,disabled=false){
  const attributes=new Map(),classes=new Set();
  return {id,disabled,value:'',textContent:'',dataset:{},attributes,children:[],
    setAttribute:(key,value)=>attributes.set(key,String(value)),removeAttribute:key=>attributes.delete(key),
    hasAttribute:key=>attributes.has(key),addEventListener(){},querySelector:()=>null,
    querySelectorAll(){return this.children;},classList:{toggle:(key,on)=>on?classes.add(key):classes.delete(key)},scrollIntoView(){}};
}
function editor(){
  const controls=[node('paramConfirm'),node('paramName'),node('paramDisabled',true)];
  const root=node('parameterEditor');root.children=controls;
  return {root,controls,nodes:new Map([[root.id,root],...controls.map(n=>[n.id,n]),['paramStatus',node('paramStatus')],['btnNewParameter',node('btnNewParameter')]])};
}
function harness({hold=null,renderFailure=null,nativeFailure=false,hasCard=true}={}){
  let context={id:'same-project'},activeEditor=editor(),nativeReject=nativeFailure;
  const originalEditor=activeEditor,entered=deferred(),release=deferred(),calls=[],effects=[],notices=[],listeners=new Map();
  let confirms=0,commits=0,renderCount=0,gate;
  const oc={parameters:[],parameterCreating:true,navigationSequence:4,focus:null,edit:null,sel:null,selection:[]};
  const s={context,card:{id:0,name:'Raw 001',fields:[{id:1,name:'width',type:'dimension',input:' 00150 '}]},
    fresh:true,changed:true,busy:false,previewRequest:null,preview:{valid:true,token:'original-preview'},draftPos:{cx:120,cy:90}};
  const pause=async stage=>{if(hold===stage){entered.resolve();await release.promise;}};
  const sandbox={structuredClone,console,oc,connection:{session:'native-session'},clearTimeout(){},setTimeout:()=>1,
    window:{addEventListener:(name,fn)=>listeners.set(name,fn),confirm:()=>false,DraftGate:{register:fn=>gate=fn}},
    document:{getElementById:id=>activeEditor.nodes.get(id)||null,addEventListener(){}},
    ReferenceWorkspace:{escape:value=>value,context:()=>context},
    EngineeringAdapter:{confirm:async({token})=>{confirms++;calls.push(['confirm',token]);await pause('confirm');if(nativeReject)throw Error('native rejected');commits++;},cancel:async()=>{}},
    api:async command=>{calls.push(['api',command]);await pause('layout');return {ok:true};},
    renderObjects:()=>{renderCount++;calls.push(['render']);if(renderFailure==='sync')throw Error('render failed synchronously');
      if(renderFailure==='async')return Promise.reject(Error('render failed asynchronously'));return pause('render');},
    ocFind:(kind,id)=>hasCard?{kind,id}:null,
    selectObject:(kind,id)=>{effects.push(['select',kind,id]);oc.navigationSequence++;oc.sel={kind,id};oc.selection=[oc.sel];},
    centerOnNode:(kind,id)=>effects.push(['center',kind,id]),renderInspector:()=>effects.push(['inspector']),
    ocSetSelection:value=>{oc.selection=value;oc.sel=value[0]||null;},toast:(...args)=>notices.push(args)};
  vm.runInNewContext(executable,sandbox,{filename:'parameters.production.js'});
  const ui=sandbox.window.ParameterUI,seam=ui.__confirmationTest;seam.setState(s);
  function replace(kind){
    // Expire each ownership premise independently. A replaced draft/context
    // need not also increment navigation to invalidate the former receipt.
    const target={kind:'boundary',id:8};if(kind==='navigation')oc.navigationSequence++;
    oc.focus={t:'face',id:8};oc.edit={bid:8};oc.sel=target;oc.selection=[target];
    if(kind==='context'||kind==='same-ID context draft')context={id:'same-project'};
    let replacement=null;
    if(kind==='draft'||kind==='same-ID context draft'){
      replacement={...s,context,card:{id:0,name:'Replacement raw',fields:[{id:1,name:'new field',type:'dimension',input:'=1/0'}]},busy:false,preview:null};
      activeEditor=editor();activeEditor.nodes.get('paramName').value='Replacement raw';seam.setState(replacement);oc.parameterCreating=true;
    }
    return {replacement,editor:activeEditor,focus:oc.focus,selection:oc.sel,sequence:oc.navigationSequence};
  }
  return {s,ui,seam,oc,calls,effects,notices,originalEditor,entered:entered.promise,release:()=>release.resolve(),reject:error=>release.reject(error),
    confirm:()=>seam.confirm(s),replace,gate:intent=>gate(intent),allowNative:()=>{nativeReject=false;},
    get confirms(){return confirms;},get commits(){return commits;},get renderCount(){return renderCount;},get activeEditor(){return activeEditor;}};
}
async function untilHeld(h,pending){await Promise.race([h.entered,pending.then(()=>{throw Error('confirmation returned before the requested held phase');})]);}
function unlocked(h){
  assert.equal(h.s.busy,false);assert.equal(h.originalEditor.root.hasAttribute('aria-busy'),false);
  assert.equal(h.originalEditor.controls[1].disabled,false,'previously enabled raw input is released');
  assert.equal(h.originalEditor.controls[2].disabled,true,'an originally disabled control stays disabled');
}
function foreignPreserved(h,owner){
  assert.deepEqual(h.effects,[],'late confirmation cannot select, center or render the replacement owner');
  assert.equal(h.oc.focus,owner.focus);assert.equal(h.oc.sel,owner.selection);assert.equal(h.oc.navigationSequence,owner.sequence);
  if(owner.replacement){
    assert.equal(h.seam.getState(),owner.replacement);assert.equal(h.oc.parameterCreating,true);
    assert.equal(owner.replacement.card.fields[0].input,'=1/0');assert.equal(h.activeEditor.nodes.get('paramName').value,'Replacement raw');
    assert.equal(h.activeEditor.controls[0].disabled,false,'old unlock cannot modify the replacement controls');
  }
}

test('confirmation remains pending and rejects leaving or duplicate native submission through every held phase',async()=>{
  for(const hold of ['confirm','layout','render']){
    const h=harness({hold}),pending=h.confirm();
    try{
      await untilHeld(h,pending);
      assert.equal(h.s.busy,true,hold);assert.equal(h.ui.pending,true,hold+': pending covers final presentation refresh');
      assert.equal(h.ui.mayLeave(),false,hold+': cannot leave a settling confirmation');
      assert.equal(h.gate({selection:[{kind:'boundary',id:8}]}),false,hold+': shipped DraftGate rejects face entry');
      await h.confirm();assert.equal(h.confirms,1,hold+': no duplicate native confirm');assert.deepEqual(h.effects,[]);
    }finally{h.release();await pending;}
    unlocked(h);assert.equal(h.ui.pending,false);assert.equal(h.commits,1);
    assert.deepEqual(h.effects,[['select','parameter',0],['center','parameter',0]]);
  }
});
for(const hold of ['confirm','layout','render'])test(`a new owner during held ${hold} keeps its raw draft, selection and navigation`,async()=>{
  for(const kind of ['draft','same-ID context draft','context','navigation']){
    const h=harness({hold}),pending=h.confirm();let owner;
    try{await untilHeld(h,pending);owner=h.replace(kind);}finally{h.release();await pending;}
    unlocked(h);foreignPreserved(h,owner);assert.equal(h.commits,1);assert.equal(h.confirms,1);
    if(hold==='confirm')assert.equal(h.calls.filter(c=>c[0]==='api').length,0,'retired owner cannot place the committed card in a replacement project');
    if(hold!=='render')assert.equal(h.renderCount,0,'retired owner cannot refresh the replacement canvas');
  }
});
test('current-owner success preserves the native ID0 draft position and settles before selecting once',async()=>{
  for(const hasCard of [true,false]){
    const h=harness({hasCard});await h.confirm();unlocked(h);
    assert.equal(h.commits,1);assert.equal(h.confirms,1);assert.equal(h.renderCount,1);
    assert.deepEqual(h.calls,[['confirm','original-preview'],['api','line canvas-pos parameter 0 120 90'],['render']]);
    assert.deepEqual(h.effects,hasCard?[['select','parameter',0],['center','parameter',0]]:[['inspector']]);
    assert.equal(h.seam.getState(),null);assert.equal(h.ui.pending,false);assert.equal(h.oc.parameterCreating,false);
  }
});
for(const renderFailure of ['sync','async'])test(`committed native state is never reconfirmed after a ${renderFailure} render failure`,async()=>{
  const h=harness({renderFailure});await h.confirm();unlocked(h);
  assert.equal(h.commits,1);assert.deepEqual(h.effects,[]);assert.equal(h.ui.pending,false);assert.equal(h.oc.parameterCreating,false);
  assert.equal(h.seam.getState(),null,'only the already committed old draft is retired');
  assert.ok(h.notices.some(n=>n[1]==='error'&&n[0].includes('已套用')),'the presentation error must not misreport a failed native commit');
  await h.confirm();assert.equal(h.confirms,1,'the old confirm closure cannot resubmit its consumed native token');
});
test('a failed old render releases its controls without clearing a replacement draft',async()=>{
  const h=harness({hold:'render'}),pending=h.confirm();let owner;
  try{await untilHeld(h,pending);owner=h.replace('same-ID context draft');}finally{h.reject(Error('late render failure'));await pending;}
  unlocked(h);foreignPreserved(h,owner);assert.equal(h.commits,1);assert.equal(h.confirms,1);
  assert.deepEqual(h.notices,[],'old errors cannot replace the new owner presentation');
});
test('native rejection preserves authored raw input and requires a new preview before retry',async()=>{
  const h=harness({nativeFailure:true}),raw=structuredClone(h.s.card);await h.confirm();unlocked(h);
  assert.equal(h.commits,0);assert.equal(h.confirms,1);assert.equal(h.renderCount,0);assert.deepEqual(h.effects,[]);
  assert.equal(h.seam.getState(),h.s);assert.deepEqual(h.s.card,raw);assert.equal(h.ui.pending,true);
  assert.equal(h.s.preview,null);assert.equal(h.activeEditor.nodes.get('paramConfirm').disabled,true);
  await h.confirm();assert.equal(h.confirms,1,'rejected preview is not a retry capability');
  h.allowNative();h.s.preview={valid:true,token:'fresh-preview'};await h.confirm();unlocked(h);
  assert.equal(h.confirms,2);assert.equal(h.commits,1);assert.equal(h.ui.pending,false);
  assert.deepEqual(h.calls.filter(c=>c[0]==='confirm'),[['confirm','original-preview'],['confirm','fresh-preview']]);
});
