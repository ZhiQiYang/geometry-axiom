/* PF-5 transport/presentation contracts. These Node checks do not measure a
 * browser or substitute for the separate real-input P1285 canvas section. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),test=require('node:test');
const web=path.join(__dirname,'../geometry-web'),source=path.join(web,'panel-fill-spatial.js');
const clone=value=>JSON.parse(JSON.stringify(value));
const text=value=>value.replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
const points=ring=>ring.map(p=>p.map(String));
function projectedComponent(outer,holes,near,far){
  const world=depth=>({outer:outer.map(p=>[String(p[0]),String(p[1]),String(depth)]),holes:holes.map(r=>r.map(p=>[String(p[0]),String(p[1]),String(depth)]))});
  const nearWorld=world(near),farWorld=world(far),projection=(region,a,b)=>({outer:region.outer.map(p=>[p[a],p[b]]),holes:region.holes.map(r=>r.map(p=>[p[a],p[b]]))});
  return {outer:points(outer),holes:holes.map(points),world:{near:nearWorld,far:farWorld},projections:{
    top:{near:projection(nearWorld,0,1),far:projection(farWorld,0,1)},front:{near:projection(nearWorld,0,2),far:projection(farWorld,0,2)},side:{near:projection(nearWorld,1,2),far:projection(farWorld,1,2)}}};
}
function fixture(){
  // Explicit illustration only: 100x100, one 10x10 hole, 20 mm beam strip.
  // The production native/oracle suite independently proves these geometries.
  const outer=[[0,0],[100,0],[100,100],[0,100]],hole=[[20,20],[20,30],[30,30],[30,20]];
  const panel=projectedComponent(outer,[hole],2480,2489);
  const left=projectedComponent([[0,0],[40,0],[40,100],[0,100]],[hole],2489,2519);
  const right=projectedComponent([[60,0],[100,0],[100,100],[60,100]],[],2489,2519);
  const edge={key:[['boundary',11,1]],start:['0','0'],end:['40','0'],fixity:'FREE'};
  const definition={id:0,fillId:9,h:30};
  const f={id:9,finishId:7,label:'明選測試完成面',status:'complete',missing:[],frame:{origin:['0','0','2480'],u:[1,0,0],v:[0,1,0],n:[0,0,1]},side:1,
    thickness:'9',h:'30',hostId:0,panelVersion:{id:'pf5-board',version:1},
    obstacles:[{ref:'b20',projectedRect:['40','-10','60','110'],normalInterval:['9','39'],footprintRelation:'overlap',panel:'touch',timber:'cut',
      world:{min:['40','-10','2489'],max:['60','110','2519']},projections:{top:['40','-10','60','110'],front:['40','2489','60','2519'],side:['-10','2489','110','2519']}}],
    panel:{status:'complete',interval:['0','9'],area:'9900',components:[panel]},timber:{status:'complete',interval:['9','39'],area:'7900',components:[left,right]},
    host:{id:0,definition,frame:{origin:['0','0','2489'],u:[1,0,0],v:[0,1,0],n:[0,0,1]},h:'30',region:{area:'7900',components:[left,right].map(c=>({outer:c.outer,holes:c.holes,edges:[clone(edge)]}))}}};
  const state={finishSurfaces:[{id:7,name:f.label,boundaryId:11,frame:{origin:f.frame.origin,U:'+X',V:'+Y',N:'+Z'},structureSide:1,obstacles:['b20'],
    derived:{n:'+Z',region:{outline:panel.outer,holes:panel.holes},obstacles:[{ref:'b20',rect:f.obstacles[0].projectedRect,q:f.obstacles[0].normalInterval,relation:'overlap',layers:null}]}}],
    panelFills:[{definition:{id:9,finishSurfaceId:7,panel:f.panelVersion,lengthAlong:'u',origin:[0,0],gap:0,pattern:'straight',threshold:{parameterId:1,fieldId:1}},
      derived:{tileCount:0,fragmentCount:0,wholeCount:0,cutCount:0,thickness:'9',threshold:{num:'8',den:'1'},tiles:[],obstacles:[{ref:'b20',panelLayer:false,timberLayer:true}],seamLines:[],effectiveSeams:[],nonSeams:[],support:[],derivedPlacement:0}}],
    derivedPlacements:[{id:0,definition,derived:{h:'30',frame:{origin:f.host.frame.origin,U:'+X',V:'+Y',N:'+Z'},components:f.host.region.components.map(c=>({outline:c.outer,holes:c.holes,edges:c.edges}))}}]};
  return {state,spatial:{schema:'panel-fill-spatial/1',scope:'diagnostic-envelope-only',complete:true,finishes:[f],junctions:[],errors:[]}};
}
function environment(){
  const data=fixture(),project={id:'pf5',contextToken:'context',revision:0},context={},history={frame:{ids:new Map([[11,{}]])},undo:[],redo:[]};
  const c={console,AbortSignal,Set,Map,Number,BigInt,JSON,Error,Promise};c.window=c;c.addEventListener=()=>{};
  c.connection={session:'pf5-session',phase:'ready'};
  c.ReferenceWorkspace={context:()=>context,getProjectState:()=>project,history,assertEditable(){},assertAssemblyIdle(){}};
  c.ui=state=>({schema:'panel-fill-workspace/1',supportedActions:['read','edit-definitions','read-layout','read-support'],scope:{finishSurfaceIds:state.finishSurfaces.map(f=>f.id),fillIds:state.panelFills.map(f=>f.definition.id)},revision:'0',completeForScope:true,errors:[],state});
  c.reply=()=>({ok:true,revision:0,complete:false,uiContract:c.ui(data.state),spatial:data.spatial});
  c.apiRequest=async command=>{
    if(command==='panel-fill-read')return clone(c.reply());
    if(command==='engineering-read')return {ok:true,state:{parameters:[],materials:[],specs:[]}};
    if(command==='objects')return {ok:true,columns:[],beams:[{id:20,name:'測試樑'}]};
    if(command==='newid')return {ok:true,finishSurface:8,panelFill:10,placement:1};return {ok:true};
  };
  c.checkApiSession=()=>{};c.renderObjects=async({current})=>current();
  vm.createContext(c);
  if(fs.existsSync(source))vm.runInContext(fs.readFileSync(source,'utf8'),c,{filename:'panel-fill-spatial.js'});
  for(const name of ['panel-fill-adapter.js','panel-fill-workspace.js'])vm.runInContext(fs.readFileSync(path.join(web,name),'utf8'),c,{filename:name});
  assert.ok(c.PanelFillSpatial&&typeof c.PanelFillSpatial.contract==="function"&&typeof c.PanelFillSpatial.render==="function",
    "PF5_UI_NATIVE_SPATIAL_PRESENTATION_EXISTS: same-candidate native presentation is missing");
  return {...data,c,S:c.PanelFillSpatial,A:c.PanelFillAdapter,W:c.PanelFillWorkspace};
}
test('PF5_UI_NATIVE_SPATIAL_PRESENTATION_EXISTS',()=>{
  const {S}=environment();assert.ok(S&&typeof S.contract==='function'&&typeof S.render==='function',
    'PF5_UI_NATIVE_SPATIAL_PRESENTATION_EXISTS: same-candidate native layer and junction presentation is missing');
});
test('PF5_UI_SOURCE_CLOSURE: reject rebound frames, intervals, native keys and missing projected holes',()=>{
  const {S,state,spatial}=environment();assert.equal(S.contract(spatial,state),spatial);
  for(const mutate of [s=>s.finishes[0].finishId=8,s=>s.finishes[0].frame.origin[2]='2481',s=>s.finishes[0].panelVersion.version=2,
    s=>s.finishes[0].panel.interval[0]='9',s=>s.finishes[0].timber.interval[1]='40',s=>s.finishes[0].panel.area=9900,
    s=>s.finishes[0].host.region.components[0].edges=[],s=>s.finishes[0].timber.components[0].projections.front.near.holes=[]]){
    const broken=clone(spatial);mutate(broken);assert.throws(()=>S.contract(broken,state),/PF5_SPATIAL_WIRE/);
  }
});
test('PF5_UI_ALL_NATIVE_LOOPS: three views paint both depths, both components and holes without a rectangle fallback',()=>{
  const {S,spatial}=environment(),html=S.render(spatial);
  assert.equal((html.match(/data-pf5-view=/g)||[]).length,3);
  assert.equal((html.match(/<path data-pf5-fill=/g)||[]).length,18);
  assert.equal((html.match(/data-pf5-rc="b20"/g)||[]).length,3);
  assert.match(html,/data-pf5-layer="timber" data-pf5-component="1" data-pf5-depth="far"/);
  assert.match(html,/M 20 20 L 20 30 L 30 30 L 30 20 Z/);
  assert.match(html,/M 60 2489 L 100 2489 L 100 2489 L 60 2489 Z/);
  assert.match(html,/viewBox=/);assert.match(html,/fill-rule="evenodd"/);
});
test('PF5_UI_EXACT_DECIMAL: display preserves integers above Number precision',()=>{
  const {S,state,spatial}=environment();spatial.finishes[0].panel.area='9007199254740993';
  S.contract(spatial,state);const html=S.render(spatial);
  assert.match(html,/data-pf5-field="panelArea"[^]*?<span data-pf5-value>9007199254740993<\/span>/);
  assert.doesNotMatch(html,/9\.00719925474099/);
});
test('PF5_UI_PENDING_H: missing physical source remains pending, never a zero-thickness or empty timber layer',()=>{
  const {S,state,spatial}=environment(),f=spatial.finishes[0];
  Object.assign(f,{status:'pending',missing:['derived-placement.h'],h:null,hostId:null,host:null,timber:null});
  f.obstacles[0].timber=null;state.derivedPlacements=[];state.panelFills[0].derived.derivedPlacement=null;
  spatial.complete=false;spatial.errors=[{fillId:9,finishes:null,code:'H_PENDING',message:'derived-placement.h is required'}];
  S.contract(spatial,state);const html=S.render(spatial);
  assert.match(html,/data-pf5-field="h"[^]*?<span data-pf5-value>未選<\/span>/);
  assert.match(html,/角材層厚 h 尚未明選，不以 0 代入/);
  assert.doesNotMatch(html,/data-pf5-layer="timber"/);
  assert.equal((html.match(/data-pf5-finish=/g)||[]).length,1);
});
test('PF5_UI_EMPTY_LEGAL: a complete empty region has no invented viewport polygon',()=>{
  const {S,state,spatial}=environment(),f=spatial.finishes[0];
  f.panel.area=f.timber.area=f.host.region.area='0';f.panel.components=[];f.timber.components=[];f.host.region.components=[];
  f.obstacles=[];state.finishSurfaces[0].obstacles=[];state.derivedPlacements[0].derived.components=[];
  S.contract(spatial,state);const html=S.render(spatial);
  assert.equal((html.match(/data-pf5-empty/g)||[]).length,3);assert.doesNotMatch(html,/<svg|<path|<rect/);
  assert.match(html,/data-pf5-field="panelArea"[^]*?<span data-pf5-value>0<\/span>/);
});
function addPair(data){
  const f=clone(data.spatial.finishes[0]);f.id=10;f.finishId=8;f.hostId=1;f.host.id=1;f.host.definition.id=1;f.host.definition.fillId=10;
  data.spatial.finishes.push(f);
  const source=clone(data.state.finishSurfaces[0]);source.id=8;data.state.finishSurfaces.push(source);
  const fill=clone(data.state.panelFills[0]);fill.definition.id=10;fill.definition.finishSurfaceId=8;fill.derived.derivedPlacement=1;data.state.panelFills.push(fill);
  const host=clone(data.state.derivedPlacements[0]);host.id=1;host.definition.id=1;host.definition.fillId=10;data.state.derivedPlacements.push(host);
  data.spatial.junctions=[{finishes:[9,10],status:'complete',sharedEdges:[{start:['31','0','2461'],end:['31','100','2461'],length:'100'}],visibleContactDimension:1,minimumL1Gap:'0',
    layers:{'panel-panel':{volume:'8100',contactDimension:3,relation:'overlap'},'panel-timber':{volume:'0',contactDimension:2,relation:'touch'},'timber-panel':{volume:'0',contactDimension:-1,relation:'separate'},'timber-timber':{volume:'0',contactDimension:1,relation:'touch'}},joinPolicy:'unselected'}];
}
test('PF5_UI_JUNCTIONS: every explicit pair remains read-only and does not choose a side-panel policy',()=>{
  const data=environment();addPair(data);data.S.contract(data.spatial,data.state);
  const html=data.S.render(data.spatial);assert.match(html,/data-pf5-junction="9:10"/);
  assert.match(html,/體積 <span>8100<\/span> mm³/);assert.match(html,/長 100 mm/);
  assert.match(html,/data-pf5-join-policy="unselected"/);assert.doesNotMatch(html,/<button|<input|<select/);
  const missing=clone(data.spatial);missing.junctions=[];assert.throws(()=>data.S.contract(missing,data.state),/全部面對/);
});
test('PF5_UI_FULL_EVIDENCE: renderer preserves exact native data and escapes names',()=>{
  const {S,spatial}=environment();spatial.finishes[0].label='<script>not executable</script>';
  const pin=clone(spatial),html=S.render(spatial),raw=html.match(/<pre data-pf5-native>([^]*?)<\/pre>/);
  assert.deepEqual(spatial,pin);assert.ok(raw);assert.deepEqual(JSON.parse(text(raw[1])),pin);
  assert.doesNotMatch(html,/<script>/);assert.match(html,/&lt;script&gt;/);
});
function preview(env,spatialAfter){
  const before=clone(env.state),after=clone(env.state);after.finishSurfaces[0].name='改名候選';
  const contract=env.c.ui(after);delete contract.state;Object.assign(contract,{before,after});
  const reply={revision:0,valid:true,token:31,changes:[{record:'finish-surface',id:7,change:'modified'}],
    dependencies:{before:{geometry:{timbers:[]}},after:{geometry:{timbers:[]}}},uiContract:contract,
    spatial:{before:clone(env.spatial),after:spatialAfter}};
  env.c.fetch=async()=>({ok:true,json:async()=>({ok:true,preview:reply})});return {reply,operation:{op:'put-finish-surface',value:env.A.definition(after.finishSurfaces[0],'finish')}};
}
test('PF5_UI_DIAGNOSTIC_NOT_WORLD_GATE: pending and malformed diagnostic do not add a new World refusal rule',async()=>{
  const env=environment(),session=new env.A.Session(11);await session.read();
  const broken=clone(env.spatial);broken.finishes[0].panel.area=9900;
  const p=preview(env,broken);await session.preview([p.operation]);
  assert.equal(session.phase,'confirmable');assert.equal(session.candidate.spatial.after.status,'unavailable');
  assert.match(env.S.render(session.candidate.spatial.after),/診斷目前不可呈現/);
  const pending=clone(env.spatial);pending.complete=false;pending.finishes[0].status='unsupported';
  pending.finishes[0].error={code:'CAPACITY',message:'Native diagnostic capacity reached'};
  pending.errors=[{fillId:9,finishes:null,code:'CAPACITY',message:'Native diagnostic capacity reached'}];
  const q=preview(env,pending);await session.preview([q.operation]);assert.equal(session.phase,'confirmable');
  assert.match(env.S.render(session.candidate.spatial.after),/Native diagnostic capacity reached/);
});
test('PF5_UI_CANDIDATE_OWNER: a mismatched diagnostic before cannot masquerade as the current candidate',async()=>{
  const env=environment(),session=new env.A.Session(11);await session.read();const p=preview(env,clone(env.spatial));
  p.reply.spatial.before.finishes[0].label='另一份診斷';await session.preview([p.operation]);
  assert.equal(session.phase,'confirmable');assert.equal(session.candidate.spatial.after.status,'unavailable');
  assert.match(session.candidate.spatial.after.error.message,/前後來源閉包不一致/);
});
test('PF5_UI_EXISTING_ENTRY: the shipped workspace combines native spatial output with the original source disclosure',async()=>{
  const env=environment();env.c.document={querySelector:()=>null};assert.equal(await env.W.open(11),true);
  let rendered='';const region={addEventListener(){},querySelector:s=>s==='[data-face-product-mode]'?{addEventListener(){}}:null};
  const pane={id:'test-pane',querySelector:()=>rendered?region:null,set innerHTML(value){rendered=value;}};
  assert.equal(env.W.render(pane,11),true);assert.equal((rendered.match(/data-pf5-spatial=/g)||[]).length,1);
  assert.match(rendered,/data-pf5-source-details/);assert.match(rendered,/完整完成面與宿主來源/);
  assert.doesNotMatch(rendered,/原生 h／框架／完整邊鍵/);assert.match(rendered,/整體 complete:false/);
});
