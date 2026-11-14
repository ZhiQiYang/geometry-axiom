'use strict';
// R14: run the shipped workspace/preview functions. DOM and transport below
// are ports, not a second grid calculator; real App/native acceptance is CDP.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const P=require('../geometry-web/project-store.js');
const workspace=fs.readFileSync(process.env.GEOMETRY_R14_WORKSPACE_SOURCE||path.join(__dirname,'../geometry-web/grid-system-workspace.js'),'utf8');
const impactSource=fs.readFileSync(process.env.GEOMETRY_R14_IMPACT_SOURCE||path.join(__dirname,'../geometry-web/reference-ui.js'),'utf8');
const V2='grid-subdivision-rules/2',V1='grid-subdivision-rules/1';
const repeat={source:'repeat',step:400,phase:0},panel={source:'repeat-panel',panel:915,gap:2,anchor:0};
const source=(u=panel,v=repeat)=>({id:17,name:'面材分份',mode:'infinite',uDefinition:{...u},vDefinition:{...v},nextRuleKey:1,rules:[]});
const plain=value=>JSON.parse(JSON.stringify(value));
function element(tag='div',id=''){
  const n={tagName:tag.toUpperCase(),id,children:[],dataset:{},attributes:{},value:'',open:false,disabled:false,textContent:'',
    setAttribute(key,value){this.attributes[key]=String(value);},getAttribute(key){return this.attributes[key];},addEventListener(){},
    append(...nodes){this.children.push(...nodes);},replaceChildren(...nodes){this.children=nodes;},
    querySelectorAll(){return [];},classList:{add(){},remove(){},toggle(){}},focus(){},scrollIntoView(){}};
  return n;
}
function harness(){
  const context={id:'r14-context'},contextToken='r14-token',body=element('body'),fields=new Map(),requests=[],commits=[],drawn=[],timers=[];
  const document={body,createElement:tag=>element(tag),createElementNS:(_ns,tag)=>{const n=element(tag);drawn.push(n);return n;},getElementById:id=>fields.get(id)||body.children.find(n=>n.id===id)||null};
  const state={context,contextToken,source:source(),mode:'source',capabilities:[V1,V2],
    ruleDraft:{intent:'create',ruleKey:null},baseRef:{kind:'grid-system',id:17},base:[0n,0n],camera:[0,0,2000,400],sel:[0n,0n],references:{sourceFingerprint:'native-source'}};
  for(const [id,value] of Object.entries({igRuleName:'面材七等分',igRuleSelector:'all-cells',igRuleCellI:'0',igRuleCellJ:'0',igRuleU:'7',igRuleV:'2'})){
    const node=element('input',id);node.value=value;fields.set(id,node);
  }
  const native={ok:true,state:{capabilities:[V1,V2]}},seam='window.InfiniteGridWorkspace={';
  assert.equal(workspace.split(seam).length,2,'one production workspace export');
  const executable=workspace.replace(seam,seam+`__r14:{ruleUnsupported,saveRule,drawConfirmedRules,
    setState:s=>{state=s;dialog.open=true;},
    ports:p=>{requireOnlyDraft=()=>{};sourceDraft=()=>p.source;
      validateDraftPins=async()=>{};stillSame=async()=>{};commit=p.commit;reopen=async()=>{};
      drawGrid=()=>{};syncRuleEditor=()=>{};}},`);
  const sandbox={document,console,TextEncoder,setTimeout:fn=>{timers.push(fn);return timers.length;},clearTimeout(){},
    oc:{gridBindings:[]},window:{addEventListener(){}},GeometryProject:P,
    ReferenceWorkspace:{escape:x=>String(x),context:()=>context,getProjectState:()=>({contextToken}),history:{frame:4}},
    GridRuleLines:{presentationState:()=>({revision:1}),readNative:async(target,query,owns)=>{requests.push({target:plain(target),query});assert.equal(owns(),true);return {complete:true,rows:plain(sandbox.nativeRows)};}},
    apiRequest:async command=>{requests.push(command);assert.equal(command,'engineering-read');return plain(native);},
  };
  sandbox.nativeRows=[];
  vm.runInNewContext(executable,sandbox,{filename:'grid-system-workspace.production.js'});
  const api=sandbox.window.InfiniteGridWorkspace.__r14;
  api.setState(state);api.ports({source:state.source,commit:async(...args)=>{commits.push(args);return false;}});
  return {api,state,native,requests,commits,fields,sandbox,drawn,timers};
}
test('R14 App accepts both mixed axes and both PANEL axes with the full /2 host',()=>{
  const h=harness();
  for(const [u,v] of [[panel,repeat],[repeat,panel],[panel,panel],[repeat,repeat]]){
    h.state.source=source(u,v);assert.equal(h.api.ruleUnsupported(h.state),'',JSON.stringify([u,v]));
  }
});
test('R14 App keeps finite, missing-axis and stagger source guards',()=>{
  const h=harness();
  for(const value of [{...source(),mode:'legacy-finite'},source(panel,{source:'none'}),source({...panel,stagger:0}),source(panel,{...repeat,stagger:200})]){
    h.state.source=value;assert.notEqual(h.api.ruleUnsupported(h.state),'');
  }
});
test('R14 App requires full host /2 rather than a native-only profile',()=>{
  const h=harness();
  for(const capabilities of [[],[V1],['grid-subdivision-native/2']]){
    h.state.capabilities=capabilities;assert.match(h.api.ruleUnsupported(h.state),/grid-subdivision-rules\/2/);
  }
  h.state.capabilities=[V2];assert.equal(h.api.ruleUnsupported(h.state),'');
  h.state.source=source(repeat,repeat);h.state.capabilities=[V1];assert.equal(h.api.ruleUnsupported(h.state),'');
});
test('R14 App rechecks host capability before submitting a pending rule',async()=>{
  const h=harness();h.native.state.capabilities=[V1];
  await assert.rejects(h.api.saveRule(h.state),/grid-subdivision-rules\/2/);
  assert.deepEqual(h.requests,['engineering-read']);assert.equal(h.commits.length,0,'unsupported host gets no mutation or preview');
});
test('R14 App submits unchanged explicit divisions and exact signed cell strings',async()=>{
  const h=harness();h.fields.get('igRuleSelector').value='cell';h.fields.get('igRuleCellI').value='9007199254740993';h.fields.get('igRuleCellJ').value='-9007199254740995';
  await h.api.saveRule(h.state);
  assert.equal(h.commits.length,1);
  assert.match(h.commits[0][1],/^grid-source-rule 17 create name-hex [0-9a-f]+ selector cell 9007199254740993 -9007199254740995 divide 7 2$/);
  assert.deepEqual(h.requests,['engineering-read']);
});
test('R14 App draws native full-pitch coordinates and retains preview-only identities',async()=>{
  const h=harness();h.state.source.rules=[{ruleKey:1,name:'七等分',selector:{kind:'all-cells'},divisions:[7,2]}];
  h.sandbox.nativeRows=[1047,1178,1309,1440,1571,1702].map((coordinate,innerIndex)=>({systemId:17,ruleKey:1,cell:['0','0'],axis:'u',innerIndex,coordinate,segments:[[[coordinate,0],[coordinate,400]]]}));
  h.sandbox.nativeRows.push({systemId:17,ruleKey:1,cell:['0','0'],axis:'v',innerIndex:0,coordinate:200,segments:[[[916,200],[1833,200]]]});
  const plot=element('svg');h.api.drawConfirmedRules(h.state,plot,n=>n,n=>n);assert.equal(h.timers.length,1);await h.timers[0]();
  h.api.drawConfirmedRules(h.state,plot,n=>n,n=>n);
  const lines=h.drawn.filter(n=>n.tagName==='LINE');
  assert.equal(lines.length,7);assert.deepEqual(lines.slice(0,6).map(n=>Number(n.attributes.x1)),[1047,1178,1309,1440,1571,1702]);
  assert.deepEqual([lines[6].attributes.x1,lines[6].attributes.x2,lines[6].attributes.y1].map(Number),[916,1833,200]);
  assert.ok(lines.every(n=>n.attributes['data-ig-rule-ref']==='none'));
  assert.equal(h.requests[0].query,'cell 0 0');assert.equal(h.requests[0].target.kind,'system');
});
function impact(value,valid=true){
  const document={createElement:tag=>element(tag),getElementById:()=>element('button')},dialog=element('dialog');
  const sandbox={document,GeometryProject:P,oc:{parameters:[]}};
  vm.runInNewContext(impactSource,sandbox,{filename:'reference-ui.production.js'});
  sandbox.appendGridDefinitionImpact(dialog,{valid,gridSystems:[{id:17,before:null,after:value}]});
  const flatten=n=>[n,...n.children.flatMap(flatten)];
  return flatten(dialog).filter(n=>n.dataset.impactRuleKey===1).map(n=>n.textContent).join('\n');
}
test('R14 candidate summary uses full panel plus gap and native effective lengths',()=>{
  for(const u of [panel,{source:'repeat-panel',effectivePanel:915,gap:2,anchor:0,panelSource:'card'}]){
    const s=source(u);s.rules=[{ruleKey:1,name:'七等分',selector:{kind:'all-cells'},divisions:[7,2]}];
    assert.match(impact(s),/14 個 131×200 mm 小格/);
    assert.doesNotMatch(impact(s,false),/mm 小格/,'rejected candidate never displays rounded division results');
  }
});
