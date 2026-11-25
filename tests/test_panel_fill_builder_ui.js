/* PF-6 App renderer contracts. Node does not prove browser geometry or L4.
 * These fixtures describe exact native values independently of the renderer;
 * real C projection and independent geometric scans are separate suites.
 */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const test=require('node:test');
const ROOT=path.resolve(__dirname,'..');
const clone=value=>JSON.parse(JSON.stringify(value));
const LEGACY_ACTIONS=['read','edit-definitions','read-layout','read-support','create-from-fill-grid'];
const BUILDER_ACTIONS=[...LEGACY_ACTIONS,'suggest-timbers'];
function workspace() {
  const file=path.join(ROOT,'geometry-web/panel-fill-builder-workspace.js');
  assert.ok(fs.existsSync(file),'PF6_APP_WORKSPACE_REQUIRED: formal fill has no PF-6 App workspace');
  const context={console,Set,Map,Number,JSON,Error,Promise,structuredClone};
  context.window=context;context.addEventListener=()=>{};
  vm.createContext(context);
  for(const name of ['panel-fill-adapter.js','panel-fill-builder-session.js','panel-fill-builder-workspace.js','panel-fill-workspace.js']){
    const source=path.join(ROOT,'geometry-web',name);
    assert.ok(fs.existsSync(source),'PF6_APP_WORKSPACE_REQUIRED: missing '+name);
    vm.runInContext(fs.readFileSync(source,'utf8'),context,{filename:source});
  }
  assert.equal(typeof context.PanelFillBuilderWorkspace?._test?.markup,'function','PF6_APP_RENDERER_REQUIRED');
  return {...context.PanelFillBuilderWorkspace._test,context,adapter:context.PanelFillAdapter};
}
function dimension(value=27,source={kind:'literal',value:27},name='直接值') {
  return {source,name,effective:String(value),unit:'mm',path:'input.A',cardName:null,fieldName:null};
}
function record(key='secondary-0',length='61') {
  return {key,phase:'seam-secondary',selectable:true,selected:false,valid:true,role:'secondary',axis:'v',
    source:{edgeKey:null,lineAxis:'u',k:'0',band:null,range:['0','100'],through:'50'},
    geometry:{rect:['88','27','115',String(27+Number(length))],length},duplicateOf:null,diagnostics:[]};
}
function fixture(phase='suggested') {
  const frame={origin:['0','0','0'],U:'+X',V:'+Y',N:'+Z'};
  const panel={definition:{id:1,finishSurfaceId:1,panel:{id:'board',version:1},lengthAlong:'v',origin:[0,0],gap:3,
    pattern:'straight',threshold:{parameterId:90,fieldId:1}},derived:{threshold:{num:'17',den:'2'},
    tileCount:0,fragmentCount:0,wholeCount:0,cutCount:0,thickness:'9',tiles:[],obstacles:[],seamLines:[],nonSeams:[],derivedPlacement:null,
    effectiveSeams:[{fillId:1,axis:'u',k:'0',coordinate:'101',range:['0','100'],edges:['100','103']}],
    support:[{seam:0,range:['27','88'],left:'12',right:'12',supported:true,status:'supported',colour:'green'}]}};
  const state={finishSurfaces:[{id:1,name:'正式完成面',boundaryId:8,frame,structureSide:1,obstacles:[],
    derived:{n:'+Z',region:{outline:[['0','0'],['300','0'],['300','300'],['0','300']],holes:[]},obstacles:[]}}],
    panelFills:[panel],derivedPlacements:[],fillGrids:[]};
  const after=clone(state);after.panelFills[0].derived.derivedPlacement=0;
  after.derivedPlacements=[{id:0,definition:{id:0,fillId:1,h:{kind:'literal',value:30}},derived:{h:'30',frame,components:[]}}];
  after.fillGrids=[{id:1,definition:{id:1,hostId:0,fillId:1,mainAlong:'u'},derived:{indexSpace:'lattice',bandIndexSpace:'panel-row',
    side:1,staggerAxis:null,staggerDelta:'0',axes:{u:{baseCoordinate:'101',pitch:'103',baseIndex:'0'},v:{baseCoordinate:'101',pitch:'103',baseIndex:'0'}}}}];
  const view={schema:'panel-fill-builder-workspace/1',revision:'18446744073709551614',setKey:'a'.repeat(64),generation:'18446744073709551613',
    phase:'ANALYSIS',selected:[],completeForScope:true,errors:[],
    input:{fillId:1,primaryAlong:'u',A:dimension(),B:dimension(30,{kind:'literal',value:30})},
    host:{id:0,created:true,h:dimension(30,{kind:'literal',value:30})},grid:{id:1,created:true,mainAlong:'u'},timbers:[],
    uiContract:{schema:'panel-fill-workspace/1',revision:'18446744073709551614',completeForScope:true,errors:[],
      supportedActions:[...BUILDER_ACTIONS],
      scope:{finishSurfaceIds:[1],fillIds:[1],fillGridIds:[1]},before:clone(state),after}};
  const input={fillId:1,A:{kind:'literal',value:27},B:{kind:'literal',value:30},roles:{u:'secondary',v:'primary'}};
  const suggestions={schema:'panel-fill-builder-suggestions/1',ok:true,valid:true,confirmable:false,token:null,complete:false,
    revision:view.revision,setKey:view.setKey,generation:view.generation,entries:[record()],omissions:[],appView:view,
    intent:{schema:'panel-fill-builder-suggest/1',expectedRevision:view.revision,input,pre:[],post:[]}};
  const session={boundaryId:8,fillId:1,phase,reason:'',suggestions,candidate:null,selected:[],sources:{materials:[],parameters:[],specs:[]},confirmable:false,retired:false};
  return {session,draft:{A:{kind:'',value:''},B:{kind:'',value:''},primaryAlong:''}};
}
function candidate() {
  const value=fixture('confirmable'),s=value.session,entry=record('secondary-0','164');entry.selected=true;
  const view=clone(s.suggestions.appView);view.phase='SELECTED';view.selected=[entry.key];
  view.timbers=[{id:7,before:null,after:{role:'secondary',A:dimension(),B:dimension(30,{kind:'literal',value:30}),
    geometry:{surface:0,centerline:'101',u:'101',v:'27',length:'164',A:'27',B:'30',dir:'+v',side:'+n',
      origin:['101','27','9'],axes:[['0','1','0'],['1','0','0'],['0','0','1']]}}}];
  s.selected=[entry.key];s.confirmable=true;
  s.candidate={schema:'panel-fill-builder-preview/1',valid:true,phase:'SELECTED',token:7,candidateIdsAreTemporary:true,idMap:null,
    revision:view.revision,setKey:view.setKey,generation:view.generation,selected:[entry.key],entries:[entry],
    createdDefinitions:[{tempKey:'r45:host',kind:'placement',candidateId:0},{tempKey:'r45:grid',kind:'grid',candidateId:1},
      {tempKey:'r45:secondary-0',kind:'timber',candidateId:7}],
    beforeScene:'before\n',afterScene:'after\n',violations:[],appView:view};
  return value;
}
function control(html,action) {
  const found=[...html.matchAll(/<button\b[^>]*>/g)].find(match=>match[0].includes('data-pf6-action="'+action+'"'));
  assert.ok(found,'PF6_APP_ACTION_REQUIRED: '+action);return found[0];
}
const text=html=>html.replace(/<[^>]*>/g,'').replaceAll('&amp;','&').replaceAll('&lt;','<').replaceAll('&gt;','>');

test('PF6_APP_EXPLICIT_INPUTS: new form does not choose dimensions or primary direction',()=>{
  const T=workspace(),value=fixture('ready');value.session.suggestions=null;
  const html=T.markup(value);
  for(const name of ['A.kind','B.kind','primaryAlong']) {
    const select=html.match(new RegExp('<select[^>]*data-pf6-field="'+name.replace('.','\\.')+'"[^>]*>([\\s\\S]*?)</select>'));
    assert.ok(select,'PF6_APP_EXPLICIT_INPUTS: missing '+name);
    const explicit=[...select[1].matchAll(/<option\b([^>]*)>/g)].filter(match=>/\bselected\b/.test(match[1]));
    assert.ok(explicit.length<=1&&explicit.every(match=>/value=""/.test(match[1])),'PF6_APP_EXPLICIT_INPUTS: implicit '+name);
  }
  assert.equal((html.match(/data-pf6-action="confirm"/g)||[]).length,1,'PF6_APP_SINGLE_CONFIRM');
  assert.match(control(html,'confirm'),/\bdisabled\b/,'PF6_APP_SUGGEST_NOT_CONFIRMABLE');
});
test('PF6_APP_AUTO_SELECT_ALL: suggestions remain an unselected proposal',()=>{
  const T=workspace(),html=T.markup(fixture());
  const boxes=[...html.matchAll(/<input\b[^>]*data-pf6-select="[^"]+"[^>]*>/g)];
  assert.equal(boxes.length,1,'PF6_APP_SUGGESTION_VISIBLE');
  assert.ok(boxes.every(match=>! /\bchecked\b/.test(match[0])),'PF6_APP_EXPLICIT_SET');
  assert.match(control(html,'confirm'),/\bdisabled\b/,'PF6_APP_SUGGEST_NOT_CONFIRMABLE');
});
test('PF6_APP_USE_SELECTED_GEOMETRY: preview labels rebuilt 164 mm as final and 61 mm as prior suggestion',()=>{
  const html=workspace().markup(candidate());
  const member=html.match(/<[^>]+data-pf6-member="secondary-0"[^>]*>([\s\S]*?)(?=<[^>]+data-pf6-member=|$)/);
  assert.ok(member,'PF6_APP_SELECTED_MEMBER_VISIBLE');
  assert.match(text(member[1]),/最終長度 164 mm/,'PF6_APP_SELECTED_REBUILD');
  assert.match(text(member[1]),/原建議 61 mm/,'PF6_APP_FINAL_VS_SUGGESTION_DISCLOSED');
  assert.doesNotMatch(control(html,'confirm'),/\bdisabled\b/,'PF6_APP_POSITIVE_TOKEN_VALID');
});
test('PF6_APP_POSITIVE_TOKEN_ONLY: zero, absent and malformed leases cannot confirm',()=>{
  const T=workspace();
  // The old five-action view isolates the v1 zero-token bug from the separate
  // sixth-action migration. Both accepted contract versions must reject zero.
  for(const actions of [LEGACY_ACTIONS,BUILDER_ACTIONS])for(const token of [0,null,undefined,-1,1.5,'7',4294967296]) {
    const value=candidate();value.session.candidate.token=token;
    value.session.candidate.appView.uiContract.supportedActions=[...actions];
    assert.match(control(T.markup(value),'confirm'),/\bdisabled\b/,'PF6_APP_ZERO_TOKEN_REJECTED: '+String(token));
  }
  for(const token of [1,4294967295]){const value=candidate();value.session.candidate.token=token;
    assert.doesNotMatch(control(T.markup(value),'confirm'),/\bdisabled\b/,'PF6_APP_POSITIVE_TOKEN_VALID');}
});
test('PF6_APP_TOKEN_MEANS_VALID: invalid selected result with a token cannot enable confirmation',()=>{
  const T=workspace(),value=candidate();value.session.candidate.valid=false;
  assert.match(control(T.markup(value),'confirm'),/\bdisabled\b/,'PF6_APP_INVALID_TOKEN_NOT_AUTHORITY');
});
test('PF6_APP_COMPLETE_VIEW: missing, incomplete or wrong-stage projections cannot confirm',()=>{
  const T=workspace();
  for(const change of [v=>delete v.appView,v=>v.appView.completeForScope=false,
    v=>v.appView.uiContract.completeForScope=false,v=>v.appView.phase='ANALYSIS']) {
    const value=candidate();change(value.session.candidate);
    assert.match(control(T.markup(value),'confirm'),/\bdisabled\b/,'PF6_APP_COMPLETE_VIEW_REQUIRED');
  }
});
test('PF6_APP_INSUFFICIENT_VISIBLE: R43 shortage is visible without rejecting legal geometry',()=>{
  const value=candidate(),support=value.session.candidate.appView.uiContract.after.panelFills[0].derived.support[0];
  Object.assign(support,{left:'2',right:'8',supported:false,status:'insufficient',colour:'red'});
  const html=workspace().markup(value);
  assert.match(html,/data-pf6-support/,'PF6_APP_R43_REQUIRED');
  assert.match(text(html),/承接不足/,'PF6_APP_INSUFFICIENT_VISIBLE');
  assert.match(text(html),/左 2 mm／右 8 mm/,'PF6_APP_BOTH_SUPPORT_WIDTHS');
  assert.match(text(html),/17\s*\/\s*2/,'PF6_APP_EXACT_THRESHOLD');
  assert.doesNotMatch(control(html,'confirm'),/\bdisabled\b/,'PF6_APP_INSUFFICIENT_IS_NOT_INVALID');
});
test('PF6_APP_INVALID_ANALYSIS_PREFIX: earlier valid rows are diagnostic only after a later failure',()=>{
  const value=fixture('invalid'),s=value.session;
  s.suggestions.valid=false;s.suggestions.appView.completeForScope=false;
  s.suggestions.entries.push({...record('invalid-later','-1'),valid:false,selectable:false,
    diagnostics:[{clause:'R45',message:'later geometry rejected'}]});
  s.suggestions.error='later geometry rejected';
  const html=workspace().markup(value),boxes=[...html.matchAll(/<input\b[^>]*data-pf6-select="[^"]+"[^>]*>/g)];
  assert.equal(boxes.length,2,'PF6_APP_INVALID_PREFIX_VISIBLE');
  assert.ok(boxes.every(match=>/\bdisabled\b/.test(match[0])),'PF6_APP_INVALID_PREFIX_LOCKED');
  for(const action of ['all','none','preview','confirm'])
    assert.match(control(html,action),/\bdisabled\b/,'PF6_APP_INVALID_ANALYSIS_NO_ACTION: '+action);
  assert.match(text(html),/later geometry rejected/,'PF6_APP_NATIVE_FAILURE_VISIBLE');
});
test('PF6_APP_OMITTED_EDGE_SOURCE: FREE, covered and hole edges stay edge sources rather than seams',()=>{
  const value=fixture();
  for(const [phase,ring] of [['free-edge','外環'],['covered-edge','外環'],['hole-edge','孔環']]){
    const entry={...record(phase,'0'),phase,selectable:false,selected:false,
      source:{edgeKey:'[["e2",0,1]]',lineAxis:'u',k:'0',band:null,range:['140','160'],through:'0'},
      diagnostics:[{clause:'D45/R45',message:'Native edge omission'}]};
    value.session.suggestions.omissions=[entry];
    const html=workspace().markup(value),omissions=html.match(/<summary>未提出建議的邊[^<]*<\/summary>([\s\S]*?)<\/details>/);
    assert.ok(omissions,'PF6_APP_OMITTED_EDGE_VISIBLE: '+phase);
    assert.doesNotMatch(text(omissions[1]),/固定 [uv] 的縫|板列/,'PF6_APP_OMITTED_EDGE_NOT_SEAM: '+phase);
    assert.ok(text(omissions[1]).includes(ring+'衍生邊'),'PF6_APP_OMITTED_RING_FROM_NATIVE_PHASE: '+phase);
    assert.match(omissions[1],/\[\[&quot;e2&quot;,0,1\]\]/,'PF6_APP_OMITTED_COMPLETE_EDGE_KEY');
    assert.match(text(omissions[1]),/區間 140～160 mm/,'PF6_APP_OMITTED_NATIVE_RANGE');
    assert.match(text(omissions[1]),/Native edge omission/,'PF6_APP_OMITTED_NATIVE_DIAGNOSTIC');
  }
});
test('PF6_APP_TEMPORARY_IDENTITIES: new candidate numbers are labelled temporary until a formal receipt',()=>{
  const T=workspace(),value=candidate(),html=T.markup(value);
  assert.match(text(html),/候選暫號.*尚未正式建立/,'PF6_APP_TEMPORARY_LABEL_REQUIRED');
  for(const row of value.session.candidate.createdDefinitions)
    assert.ok(html.includes('data-pf6-temporary="'+row.kind+':'+row.candidateId+'"'),'PF6_APP_TEMPORARY_ID_LABEL: '+row.kind);
  assert.doesNotMatch(html,/data-pf6-formal=/,'PF6_APP_NO_FORMAL_MAP_BEFORE_RECEIPT');
  value.session.candidate.createdDefinitions.push({tempKey:'r45:duplicate-source',kind:'timber',candidateId:7});
  assert.doesNotMatch(control(T.markup(value),'confirm'),/\bdisabled\b/,'PF6_APP_DUPLICATE_SOURCE_SHARED_TIMBER_VALID');
  for(const mutate of [p=>delete p.candidateIdsAreTemporary,p=>p.candidateIdsAreTemporary=false,
    p=>p.idMap=[],p=>p.createdDefinitions[0].id=0]) {
    const bad=candidate();mutate(bad.session.candidate);
    assert.match(control(T.markup(bad),'confirm'),/\bdisabled\b/,'PF6_APP_TEMPORARY_SHAPE_REQUIRED');
  }
});
test('PF6_APP_FORMAL_RECEIPT_MAP: committed identities come only from the complete formal idMap',()=>{
  const T=workspace(),value=candidate(),s=value.session;
  s.committedDefinitions=clone(s.candidate.createdDefinitions);s.candidate=null;s.phase='committed';s.confirmable=false;
  s.receipt={ok:true,actionReceipt:{idMap:s.committedDefinitions.map((row,i)=>({kind:row.kind,tempKey:row.tempKey,id:101+i}))}};
  const html=T.markup(value);
  assert.match(text(html),/正式識別/,'PF6_APP_FORMAL_RECEIPT_VISIBLE');
  for(const [i,row] of s.committedDefinitions.entries())
    assert.ok(html.includes('data-pf6-formal="'+row.kind+':'+(101+i)+'"'),'PF6_APP_RECEIPT_ID_EXACT');
  assert.doesNotMatch(html,/data-pf6-formal="(?:placement:0|grid:1|timber:7)"/,'PF6_APP_NO_TEMP_ID_FALLBACK');
  for(const mutate of [v=>delete v.receipt,v=>v.receipt.ok=false,v=>v.receipt.actionReceipt.idMap.pop(),
    v=>v.receipt.actionReceipt.idMap[0].candidateId=0,v=>v.receipt.actionReceipt.idMap[0].tempKey='unrelated',
    v=>v.receipt.actionReceipt.idMap.push(clone(v.receipt.actionReceipt.idMap[0]))]) {
    const bad=clone(value);mutate(bad.session);
    assert.doesNotMatch(T.markup(bad),/data-pf6-formal=/,'PF6_APP_MALFORMED_RECEIPT_NO_FORMAL_IDS');
  }
});
test('PF6_APP_SOURCE_NAMES: source identity and exact value are readable and escaped',()=>{
  const T=workspace(),d=dimension(27,{kind:'parameter',parameterId:91,fieldId:1},'貼板尺寸／角材寬');
  d.cardName='貼板尺寸';d.fieldName='角材寬';d.path='parameter/91/field/1';
  const shown=T.dimensionText(d);
  assert.match(text(shown),/貼板尺寸/,'PF6_APP_SOURCE_NAME');assert.match(text(shown),/角材寬/,'PF6_APP_SOURCE_FIELD');
  assert.match(text(shown),/27\s*mm/,'PF6_APP_SOURCE_EXACT_MM');
  const value=candidate();value.session.candidate.appView.input.A={...d,name:'<img src=x onerror=alert(1)>'};
  const html=T.markup(value);assert.doesNotMatch(html,/<img\s+src=x/,'PF6_APP_SOURCE_NAME_NOT_HTML');
});
test('PF6_APP_EMPTY_SET: no selected member cannot masquerade as a confirmable result',()=>{
  const value=candidate();value.session.selected=[];value.session.candidate.phase='NO_OP';
  value.session.candidate.token=null;value.session.candidate.appView.phase='NO_OP';
  value.session.candidate.appView.selected=[];
  assert.match(control(workspace().markup(value),'confirm'),/\bdisabled\b/,'PF6_APP_NOOP_NO_CONFIRM');
});
test('PF6_APP_FOUR_SOURCES: explicit typed sources retain identities including zero IDs',()=>{
  const T=workspace();
  for(const [draft,field,expected] of [
    [{kind:'literal',value:'27'},'A',{kind:'literal',value:27}],
    [{kind:'spec',value:'明選寬度'},'A',{kind:'spec',name:'明選寬度'}],
    [{kind:'material',value:'["pine",2]'},'B',{kind:'material',id:'pine',version:2,field:'B'}],
    [{kind:'parameter',value:'0:0'},'B',{kind:'parameter',parameterId:0,fieldId:0}]
  ])assert.deepEqual(clone(T.sourceValue(draft,field)),expected,'PF6_APP_TYPED_SOURCE_IDENTITY');
  for(const draft of [{kind:'',value:''},{kind:'literal',value:'27.5'},{kind:'parameter',value:'0:0junk'},
    {kind:'material',value:'["pine",0]'},{kind:'unknown',value:'27'}])
    assert.throws(()=>T.sourceValue(draft,'A'),undefined,'PF6_APP_INVALID_SOURCE_REJECTED');
});

function contractReply(actions) {
  return {ok:true,complete:false,revision:12,uiContract:{schema:'panel-fill-workspace/1',revision:'12',
    supportedActions:[...actions],completeForScope:true,errors:[],scope:{finishSurfaceIds:[],fillIds:[],fillGridIds:[]},
    state:{finishSurfaces:[],panelFills:[],derivedPlacements:[],fillGrids:[]}}};
}
test('PF6_UI14_EXACT_ACTIONS: three complete ordered versions preserve the five old actions and append only PF6',()=>{
  const A=workspace().adapter;
  for(const actions of [LEGACY_ACTIONS.slice(0,4),LEGACY_ACTIONS,BUILDER_ACTIONS])
    assert.doesNotThrow(()=>A.contract(contractReply(actions)),'PF6_UI14_SUPPORTED_ACTIONS_EXECUTABLE');
  const malformed=[[],['read'],[...BUILDER_ACTIONS,'export-grid-snapshot'],
    [...LEGACY_ACTIONS,'suggest-timber'],[...LEGACY_ACTIONS,'suggest-timbers','suggest-timbers'],
    ['suggest-timbers',...LEGACY_ACTIONS],[...LEGACY_ACTIONS.slice(0,4),'suggest-timbers']];
  for(const actions of [LEGACY_ACTIONS.slice(0,4),LEGACY_ACTIONS,BUILDER_ACTIONS]) {
    for(let i=0;i<4;i++)malformed.push(actions.filter((_,index)=>index!==i));
    for(let i=0;i<actions.length-1;i++){const swapped=[...actions];[swapped[i],swapped[i+1]]=[swapped[i+1],swapped[i]];malformed.push(swapped);}
    for(const action of actions)malformed.push([...actions,action]);
  }
  for(const actions of malformed)
    assert.throws(()=>A.contract(contractReply(actions)),undefined,'PF6_UI14_EXACT_ORDER_REQUIRED: '+JSON.stringify(actions));
});

async function openedWorkspace(actions) {
  const T=workspace(),c=T.context,opened=[];let region=null,parent=null;
  const control={addEventListener(){},focus(){},closest(){return null;},disabled:false};
  const pane={querySelector:selector=>selector==='[data-pf-workspace]'?region:null};
  Object.defineProperty(pane,'innerHTML',{get(){return this.html||'';},set(html){this.html=html;region={handlers:{},
    addEventListener(type,listener){(this.handlers[type]||=[]).push(listener);},contains(){return false;},
    querySelector(){return control;},querySelectorAll(){return [];}};}});
  c.document={activeElement:null,querySelector:selector=>selector==='#faceInspectorContent [data-fi-pane="prop"]'?pane:null};
  c.connection={session:'session',phase:'ready'};
  const project={id:'project',contextToken:'context',revision:0},context={};
  c.ReferenceWorkspace={context:()=>context,getProjectState:()=>project,
    history:{frame:{ids:new Map([[8,{}]])},undo:[],redo:[]},assertEditable(){},assertAssemblyIdle(){},present(){}};
  const state=clone(fixture().session.suggestions.appView.uiContract.before);
  c.apiRequest=async command=>{
    if(command==='panel-fill-read'){const reply=contractReply(actions);reply.uiContract.state=state;
      reply.uiContract.scope={finishSurfaceIds:[1],fillIds:[1],fillGridIds:[]};return reply;}
    if(command==='engineering-read')return {ok:true,state:{materials:[],parameters:[],specs:[]}};
    if(command==='objects')return {ok:true,columns:[],beams:[]};
    if(command==='newid')return {ok:true,finishSurface:2,panelFill:2,placement:0};
    throw Error('Unexpected command '+command);
  };
  const NativeSession=c.PanelFillAdapter.Session;
  c.PanelFillAdapter.Session=class extends NativeSession {constructor(...args){super(...args);parent=this;}};
  c.PanelFillBuilderWorkspace={activeFor:()=>false,close:()=>true,open:(session,fillId,trigger)=>opened.push({session,fillId,trigger})};
  const ok=await c.PanelFillWorkspace.open(8,null);
  assert.equal(ok,true,'PF6_UI14_PARENT_CONTRACT_USABLE: '+parent?.reason);
  const dispatch=async(button)=>{
    for(const handler of region.handlers.click||[])handler({target:{closest:selector=>selector==='[data-pf-action]'?button:null},preventDefault(){}});
    await Promise.resolve();
  };
  return {c,pane,get region(){return region;},parent,opened,dispatch};
}
test('PF6_UI14_FORMAL_ACTION: one formal dispatch carries the formal fill ID and disables while parent is pending',async()=>{
  const env=await openedWorkspace(BUILDER_ACTIONS),entry=env.pane.innerHTML.match(/<button\b[^>]*data-pf-action="suggest-timbers"[^>]*>/g)||[];
  assert.equal(entry.length,1,'PF6_UI14_ONE_FORMAL_ENTRY');
  assert.match(entry[0],/data-pf-fill-id="1"/,'PF6_UI14_ENTRY_FILL_ID');
  assert.doesNotMatch(entry[0],/\bdisabled\b/,'PF6_UI14_FORMAL_SOURCE_ENABLED');
  assert.doesNotMatch(env.pane.innerHTML,/data-pf6-open/,'PF6_UI14_NO_ALIAS_BYPASS');
  assert.equal(env.region.handlers.click.length,1,'PF6_UI14_SINGLE_DISPATCH');
  const button={disabled:false,dataset:{pfAction:'suggest-timbers',pfFillId:'1'}};
  await env.dispatch(button);
  assert.equal(env.opened.length,1,'PF6_UI14_FORMAL_ACTION_REACHES_BUILDER');
  assert.equal(env.opened[0].fillId,1,'PF6_UI14_FORMAL_FILL_ROUTED');assert.equal(env.opened[0].trigger,button);
  env.parent.candidate={after:clone(env.parent.snapshot),before:clone(env.parent.snapshot),changes:[],uiContract:{errors:[]}};
  env.parent.phase='confirmable';env.c.PanelFillWorkspace.render(env.pane,8,true);
  const pending=(env.pane.innerHTML.match(/<button\b[^>]*data-pf-action="suggest-timbers"[^>]*>/g)||[]);
  assert.equal(pending.length,1,'PF6_UI14_PENDING_ENTRY_REMAINS_VISIBLE');
  assert.match(pending[0],/\bdisabled\b/,'PF6_UI14_PENDING_ENTRY_DISABLED');
  await env.dispatch(button);
  assert.equal(env.opened.length,1,'PF6_UI14_PENDING_CANNOT_BYPASS');
});
test('PF6_UI14_LEGACY_HIDDEN: an exact old five-action service stays usable and cannot show or dispatch PF6',async()=>{
  const env=await openedWorkspace(LEGACY_ACTIONS);
  assert.doesNotMatch(env.pane.innerHTML,/data-pf6-open|data-pf-action="suggest-timbers"|PF-6|建議角材/,'PF6_UI14_LEGACY_NO_BUILDER');
  await env.dispatch({disabled:false,dataset:{pfAction:'suggest-timbers',pfFillId:'1'}});
  assert.equal(env.opened.length,0,'PF6_UI14_LEGACY_CANNOT_DISPATCH');
});
