/*
 * PR #353 R353-15/16: FUNCTION-LAYER regression checks, with R353-13/14 controls.
 * Runs the actual GridSystemEditor.card and grid-inspector.js functions, and
 * the actual feature-attachments.js source-key implementation. R353-13/14 use
 * the original appendGridDefinitionImpact summary function. Minimal SVG,
 * DOM and transport doubles provide the host only; this does not run a browser,
 * native geometry, preview confirmation, or save/reopen.
 *
 * node tests/test_pr353_display_regressions.js [repo-root] [mutation]
 * P353_REPO_ROOT can select a baseline checkout; default is this repo.
 * Optional rollback mutations (in memory, never written to product files):
 *   canvas_literal          -> function_R353_15_canvas_{rr,rp,pp} must fail
 *   inspector_literal       -> function_R353_16_rename_card_{rr,rp,pp} must fail
 *   inspector_omit_mapping  -> function_R353_16_rename_card_{rr,rp,pp} must fail
 * A mutation run is expected to exit 1. P353_DISPLAY_MUTATION is also accepted.
 */
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const root=path.resolve(process.argv[2]||process.env.P353_REPO_ROOT||path.join(__dirname,'..'));
const Features=require(path.join(root,'geometry-web/feature-attachments.js'));
const mutation=process.argv[3]||process.env.P353_DISPLAY_MUTATION||null;
const mutations={
  canvas_literal:['app.js',"const axisLength = (d,key) => d?.[key+'Source']==='card' ? d?.[key==='step'?'effectiveStep':'effectivePanel'] : d?.[key];","const axisLength = (d,key) => d?.[key];"],
  inspector_literal:['grid-inspector.js',"if(d[key+'Source']==='card')return 'card';",''],
  inspector_omit_mapping:['grid-inspector.js',"${s.object.mainAlong||'none'}${card} ${parts.join(' ')}","${s.object.mainAlong||'none'} ${parts.join(' ')}"]
};
if(mutation&&!Object.hasOwn(mutations,mutation))throw Error('Unknown mutation: '+mutation);
function sourceText(file){const text=fs.readFileSync(path.join(root,'geometry-web',file),'utf8'),edit=mutations[mutation];if(!edit||edit[0]!==file)return text;assert.equal(text.split(edit[1]).length-1,1,'mutation needle count');return text.replace(edit[1],edit[2]);}
const results=[];
async function check(name,fn){name='function_'+name;try{await fn();results.push({name,status:'pass'});}catch(e){results.push({name,status:'fail',error:e.message});}}
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clone=value=>JSON.parse(JSON.stringify(value));
const definitions=(kind,card=false,refs=false)=>{
  const modes={rr:['repeat','repeat'],rp:['repeat','repeat-panel'],pp:['repeat-panel','repeat-panel']}[kind];
  return Object.fromEntries(modes.map((source,i)=>{
    const length=i===0?600:1200,key=source==='repeat'?'step':'panel';
    const d=source==='repeat'?{source,phase:i===0?-125:37,step:length}:{source,panel:length,gap:i===0?7:5,anchor:i===0?-70:45,anchorExplicit:true};
    if(card){delete d[key];d[key+'Source']='card';d[key==='step'?'effectiveStep':'effectivePanel']=length;}
    if(refs)d.parameterRefs={[key]:{kind:'parameter',parameterId:10,fieldId:i===0?3:8}};
    if(i===0){d.stagger=137;d.parameterRefs={...d.parameterRefs,stagger:{kind:'parameter',parameterId:20,fieldId:1}};}
    return [(i?'v':'u')+'Definition',d];
  }));
};
const row=(kind,card=false,refs=false)=>({kind:'grid-system',id:41,name:'Grid fixture',mode:'infinite',mainAlong:'u',cx:0,cy:0,applications:[],bindings:[],rules:[],nextRuleKey:1,...definitions(kind,card,refs),...(card?{cardReference:{parameterId:10,uFieldId:3,vFieldId:8}}:{})});
function canvas(){
  const text=sourceText('app.js'),start=text.indexOf('const GridSystemEditor = (() => {'),end=text.indexOf('\nfunction renderGridObjectInspector',start);
  assert(start>=0&&end>start);
  const el=(tag,attrs={},parent)=>{const n={tag,attrs,children:[],textContent:''};if(parent)parent.children.push(n);return n;};
  const context=vm.createContext({ReferenceWorkspace:{escape},el,OC_W:260,OC_H:220,TextEncoder,structuredClone});
  vm.runInContext(text.slice(start,end)+'\nglobalThis.cardProbe=GridSystemEditor.card;',context);
  const flatten=n=>[n,...n.children.flatMap(flatten)];
  return o=>{
    const n=context.cardProbe(o),nodes=flatten(n),body=nodes.find(n=>n.attrs.class==='ocard-body');
    return {text:nodes.map(n=>n.textContent).join('\n'),lines:flatten(body).filter(n=>n.tag==='line').map(n=>clone(n.attrs)),attributes:nodes.flatMap(n=>Object.values(n.attrs))};
  };
}
class FakeNode {
  constructor(id,tag,attrs){this.id=id;this.tagName=tag.toUpperCase();this.attrs=attrs;this.value=attrs.value??'';this.disabled=Object.hasOwn(attrs,'disabled');this.readOnly=Object.hasOwn(attrs,'readonly');this.isConnected=true;this.listeners={};this.classList={add(){},remove(){},toggle(){}};this.textContent='';if(attrs.type==='number'&&this.value!==''&&!Number.isFinite(Number(this.value)))this.value='';}
  addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
  async emit(type){for(const fn of this.listeners[type]||[])await fn({target:this});}
  setAttribute(key,value){this.attrs[key]=String(value);}
  focus(){}
}
class FakePane {
  constructor(){this.nodes=new Map();this.isConnected=true;this.classList={add(){},remove(){}};}
  set innerHTML(html){this.html=html;this.nodes.clear();for(const m of html.matchAll(/<(section|input|button|p|select)\b([^>]*)>/g)){const attrs={};for(const a of m[2].matchAll(/([\w-]+)(?:="([^"]*)")?/g))attrs[a[1]]=a[2]??'';if(attrs.id)this.nodes.set(attrs.id,new FakeNode(attrs.id,m[1],attrs));}}
  get innerHTML(){return this.html;}
  querySelector(selector){return selector.startsWith('#')?this.nodes.get(selector.slice(1))??null:null;}
  querySelectorAll(selector){if(selector==='button,input,select')return [...this.nodes.values()].filter(n=>['BUTTON','INPUT','SELECT'].includes(n.tagName));return selector.split(',').map(s=>this.querySelector(s)).filter(Boolean);}
}
function inspector(o){
  const pane=new FakePane(),contextId={id:'probe'},commands=[],bindings=[];
  const workspace={createBinding:id=>bindings.push(id),openSystem(){},openBinding(){}},oc={gridSystems:[clone(o)],gridBindings:[],faces:[],bmap:{},busy:false};
  const context=vm.createContext({window:{InfiniteGridWorkspace:workspace},ReferenceWorkspace:{escape,context:()=>contextId},GeometryProject:{Features},oc,structuredClone,TextEncoder,
    document:{querySelector:()=>null},deleteObject(){},renderObjects:async()=>{},confirmReferenceImpact:async()=>({ok:false,error:'probe cancelled'}),apiRequest:async command=>{commands.push(command);if(command==='objects')return {ok:true,gridSystems:clone(oc.gridSystems)};if(command.startsWith('line preview '))return {preview:{token:'probe',command}};throw Error('unexpected API '+command);}});
  const text=sourceText('grid-inspector.js').replace('workspace.renderInspector=renderInspector;workspace.disposeInspector=disposeInspector;','workspace.renderInspector=renderInspector;workspace.disposeInspector=disposeInspector;workspace.probe={saveSource,syncSourceDraft,sourceForm,definitionText,getActive:()=>active};');
  vm.runInContext(text,context);workspace.renderInspector(pane,clone(o));
  return {pane,workspace,oc,commands,bindings,state:workspace.probe.getActive()};
}
function impactSummary(before,after,cards){
  const createElement=tag=>({tag,children:[],dataset:{},attrs:{},textContent:'',append(...nodes){this.children.push(...nodes);},setAttribute(key,value){this.attrs[key]=String(value);}});
  const context=vm.createContext({document:{createElement},GeometryProject:{Features},oc:{parameters:cards.map(card=>({id:card.id,card}))}});
  const text=sourceText('reference-ui.js'),start=text.indexOf('function appendGridDefinitionImpact('),end=text.indexOf('\nfunction referenceGuidePreparation(',start);
  assert(start>=0&&end>start);vm.runInContext(text.slice(start,end),context);
  const preview={valid:true,gridSystems:[{id:41,before,after}]},snapshot=JSON.stringify(preview),dialog=createElement('dialog');
  context.appendGridDefinitionImpact(dialog,preview);assert.equal(JSON.stringify(preview),snapshot,'summary cannot rewrite candidate definitions');
  const flatten=n=>[n,...n.children.flatMap(flatten)],nodes=flatten(dialog),textOf=n=>flatten(n).map(x=>x.textContent).join('\n');
  return {text:textOf(dialog),side:side=>nodes.find(n=>n.dataset.impactSide===side)?.textContent,rules:side=>textOf(nodes.find(n=>n.dataset.impactRuleSide===side))};
}
const summaryCard=(id,u=18,v=30)=>({id,name:'同名參數卡',fields:[{id:3,name:'長',type:'dimension',value:{num:String(u),den:'1'}},{id:8,name:'寬',type:'dimension',value:{num:String(v),den:'1'}}]});
function summaryRow(card,u=18,v=30){
  const o=row('rr',card);o.uDefinition=card?{source:'repeat',phase:0,stepSource:'card',effectiveStep:u}:{source:'repeat',phase:0,step:u};
  o.vDefinition=card?{source:'repeat',phase:0,stepSource:'card',effectiveStep:v}:{source:'repeat',phase:0,step:v};return o;
}
(async()=>{
  const draw=canvas();
  for(const kind of ['rr','rp','pp']){
    await check('R353_15_canvas_'+kind,()=>{const card=row(kind,true),before=JSON.stringify(card),a=draw(card),b=draw(row(kind));assert(b.lines.length>0);assert.deepEqual(a.lines,b.lines);assert(a.lines.length>0);assert(!/undefined|NaN/.test(a.text));assert(a.attributes.every(v=>!String(v).includes('NaN')));assert(a.text.includes('600'));assert(a.text.includes('1200')||a.text.includes('1205'));assert(a.text.includes('整張參數卡'));assert.equal(JSON.stringify(card),before);});
    await check('canvas_direct_parameter_'+kind,()=>{const d=draw(row(kind)),p=draw(row(kind,false,true));assert(d.lines.length>0);assert.deepEqual(p.lines,d.lines);assert(!/undefined|NaN/.test(d.text+p.text));});
    await check('R353_16_effective_readonly_'+kind,()=>{const p=inspector(row(kind,true));assert(!/undefined|NaN/.test(p.pane.html));for(const [axis,length]of[['U','600'],['V','1200']]){const n=p.pane.querySelector('#gi'+axis+'Step');if(n){assert.equal(n.value,length);assert.equal(n.readOnly,true);assert.equal(n.attrs['aria-readonly'],'true');}}assert(p.pane.html.includes('整張參數卡'));});
    await check('R353_16_clean_binding_'+kind,async()=>{const p=inspector(row(kind,true)),create=p.pane.querySelector('#gridObjectNewBinding');assert.equal(create.disabled,false);await create.emit('click');assert.deepEqual(p.bindings,[41]);assert.equal(p.commands.length,0);});
    // Before P, invalid number values become empty; fill 500 only to reach the
    // reviewed flattening counterexample. With P, the readonly effective values remain.
    await check('R353_16_rename_card_'+kind,async()=>{const o=row(kind,true),p=inspector(o),before=JSON.stringify(p.state.object);p.pane.querySelector('#giName').value='renamed';await p.pane.querySelector('#giName').emit('input');assert.equal(p.pane.querySelector('#gridObjectNewBinding').disabled,true);for(const axis of ['U','V']){const input=p.pane.querySelector('#gi'+axis+'Step');if(input&&!input.value)input.value='500';}await p.pane.querySelector('#giPreview').emit('click');const cmd=p.commands.find(x=>x.startsWith('line preview '));assert(cmd,'preview command was not captured');assert(cmd.includes('card-reference 10 3 8'));assert(!/undefined|NaN/.test(cmd));const expected=kind==='rr'?'u repeat -125 card stagger param:20:1 v repeat 37 card':kind==='rp'?'u repeat -125 card stagger param:20:1 v repeat-panel card gap 5 from 45':'u repeat-panel card gap 7 from -70 stagger param:20:1 v repeat-panel card gap 5 from 45';assert(cmd.endsWith(expected),cmd);assert.equal(JSON.stringify(p.state.object),before);});
    await check('inspector_direct_parameter_'+kind,async()=>{for(const refs of [false,true]){const o=row(kind,false,refs),p=inspector(o);assert.equal(p.pane.querySelector('#gridObjectNewBinding').disabled,false);for(const axis of ['U','V']){const input=p.pane.querySelector('#gi'+axis+'Step');if(input)assert.equal(input.readOnly,refs);}p.pane.querySelector('#giName').value='renamed';await p.pane.querySelector('#giPreview').emit('click');const cmd=p.commands.find(x=>x.startsWith('line preview '));assert(cmd);assert(!cmd.includes('card-reference'));assert(!/undefined|NaN/.test(cmd));if(refs){assert(cmd.includes('param:10:3'));assert(cmd.includes('param:10:8'));}else{assert(cmd.includes('600'));assert(cmd.includes('1200'));}}});
  }
  await check('inspector_direct_edit',async()=>{const p=inspector(row('rr'));p.pane.querySelector('#giUStep').value='650';await p.pane.querySelector('#giUStep').emit('input');assert.equal(p.pane.querySelector('#gridObjectNewBinding').disabled,true);await p.pane.querySelector('#giPreview').emit('click');assert(p.commands.some(x=>x.endsWith('u repeat -125 650 stagger param:20:1 v repeat 37 1200')));});
  await check('inspector_stale_guard',async()=>{const p=inspector(row('rr',true));p.pane.querySelector('#giName').value='renamed';for(const axis of ['U','V']){const field=p.pane.querySelector('#gi'+axis+'Step');if(field&&!field.value)field.value='500';}p.oc.gridSystems[0].uDefinition.effectiveStep=700;await p.pane.querySelector('#giPreview').emit('click');assert.equal(p.commands.filter(x=>x.startsWith('line preview ')).length,0);assert(p.pane.querySelector('#giStatus').textContent.includes('已更新'));});
  for(const card of [true,false])await check('R353_13_control_'+(card?'card':'direct')+'_rule_before_after',()=>{
    const before=summaryRow(card,12,30),after=summaryRow(card,18,30),rule={ruleKey:1,name:'二乘二',selector:{kind:'all-cells'},divisions:[2,2]};
    for(const o of [before,after]){o.rules=[clone(rule)];o.nextRuleKey=2;}
    const summary=impactSummary(before,after,[summaryCard(10,999,999)]);
    assert(summary.rules('before').includes('6×15 mm'));assert(summary.rules('after').includes('9×15 mm'));
    assert(!/undefined|NaN|999/.test(summary.text),'rule arithmetic must use its own before/after native row');
  });
  await check('R353_14_control_equal_labels_distinct_cards',()=>{
    const before=summaryRow(true),after=clone(before);after.cardReference.parameterId=20;
    const summary=impactSummary(before,after,[summaryCard(10),summaryCard(20)]),old=summary.side('before'),next=summary.side('after');
    for(const text of [old,next]){assert(text.includes('同名參數卡'));assert(text.includes('u = 長（欄 #3）'));assert(text.includes('v = 寬（欄 #8）'));}
    assert(old.includes('卡 #10'));assert(next.includes('卡 #20'));assert.notEqual(old.slice(2),next.slice(2));
  });
  await check('R353_14_control_equal_lengths_swapped_fields',()=>{
    const before=summaryRow(true,18,18),after=clone(before);after.cardReference.uFieldId=8;after.cardReference.vFieldId=3;
    const summary=impactSummary(before,after,[summaryCard(10,18,18)]),old=summary.side('before'),next=summary.side('after');
    assert(old.includes('卡 #10'));assert(next.includes('卡 #10'));assert(old.includes('u = 長（欄 #3）'));assert(old.includes('v = 寬（欄 #8）'));
    assert(next.includes('u = 寬（欄 #8）'));assert(next.includes('v = 長（欄 #3）'));assert.notEqual(old.slice(2),next.slice(2));
  });
  console.log(JSON.stringify({schema:'pr353-display-function-tests/1',root,mutation,layer:'original functions with minimal SVG/DOM and transport doubles; no browser/native run',passed:results.filter(r=>r.status==='pass').length,failed:results.filter(r=>r.status==='fail').length,results},null,2));process.exitCode=results.some(r=>r.status==='fail')?1:0;
})();
