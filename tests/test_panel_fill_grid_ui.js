/* PF4-A: behavior contracts. Real HTTP/native and browser entry have separate suites. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),test=require('node:test');
const clone=value=>JSON.parse(JSON.stringify(value));
function environment(){
  const project={id:'pf4',contextToken:'pf4-context',revision:0},context={},history={frame:{ids:new Map([[4,{}]])},undo:[],redo:[]},calls=[];
  const finish={id:1,name:'完成面',boundaryId:4,frame:{origin:['0','0','0'],U:'+X',V:'+Y',N:'+Z'},structureSide:1,obstacles:[],derived:{n:'+Z',region:{outline:[['0','0'],['200','0'],['200','200'],['0','200']],holes:[]},obstacles:[]}};
  const panel={id:1,finishSurfaceId:1,panel:{id:'board',version:1},lengthAlong:'v',origin:[0,0],gap:3,pattern:'straight',threshold:{parameterId:1,fieldId:1}};
  const host={id:0,fillId:1,h:30};
  const state={finishSurfaces:[finish],panelFills:[{definition:panel,derived:{tileCount:0,fragmentCount:0,wholeCount:0,cutCount:0,thickness:'9',threshold:{num:'8',den:'1'},tiles:[],obstacles:[],seamLines:[],effectiveSeams:[],nonSeams:[],support:[],derivedPlacement:0}}],derivedPlacements:[{id:0,definition:host,derived:{h:'30',frame:{origin:['0','0','9'],U:'+X',V:'+Y',N:'+Z'},components:[]}}],fillGrids:[]};
  const c={console,AbortSignal,Set,Map,Number,JSON,Error,Promise};c.window=c;c.globalThis=c;c.addEventListener=()=>{};c.connection={session:'pf4-session',phase:'ready'};
  c.ReferenceWorkspace={context:()=>context,getProjectState:()=>project,history,assertEditable(){},assertAssemblyIdle(){}};
  const contract=state=>({schema:'panel-fill-workspace/1',supportedActions:['read','edit-definitions','read-layout','read-support','create-from-fill-grid'],scope:{finishSurfaceIds:[1],fillIds:[1],fillGridIds:state.fillGrids.map(g=>g.id)},revision:'0',completeForScope:true,errors:[],state});
  c.reply=()=>({ok:true,revision:0,complete:false,uiContract:contract(state)});
  c.apiRequest=async command=>{calls.push(command);if(command==='panel-fill-read')return c.reply();if(command==='engineering-read')return {ok:true,state:{parameters:[],materials:[],specs:[]}};if(command==='objects')return {ok:true,columns:[],beams:[]};if(command==='newid')return {ok:true,finishSurface:2,panelFill:2,placement:1};return {ok:true,history_changed:true};};
  c.checkApiSession=()=>{};c.renderObjects=async({current})=>current();
  vm.createContext(c);for(const file of ['panel-fill-adapter.js','panel-fill-workspace.js']){
    const override=file==='panel-fill-adapter.js'?process.env.PF_GRID_ADAPTER_PATH:process.env.PF_GRID_WORKSPACE_PATH;
    vm.runInContext(fs.readFileSync(override||path.join(__dirname,'../geometry-web',file),'utf8'),c,{filename:file});
  }
  const s={boundaryId:4,selection:{finish:1,fill:1,host:0},snapshot:state,contract:contract(state),draft:{finishId:1,name:'完成面',origin:['0','0','0'],U:'+X',V:'+Y',N:'+Z',side:'1',obstacles:[],fill:true,fillId:1,panel:'["board",1]',lengthAlong:'v',fillOrigin:['0','0'],gap:{kind:'literal',value:'3'},pattern:'straight',threshold:'1:1',host:true,hostId:0,h:{kind:'literal',value:'30'},createGrid:true,gridMainAlong:'u'}};
  const grid=(id=7)=>({id,definition:{id,hostId:0,fillId:1,mainAlong:'u'},derived:{indexSpace:'lattice',bandIndexSpace:'panel-row',side:1,staggerAxis:null,staggerDelta:'0',axes:{u:{baseCoordinate:'101',pitch:'103',baseIndex:'0'},v:{baseCoordinate:'101',pitch:'103',baseIndex:'0'}}}});
  const dependencyGrid=g=>({id:g.id,surface:g.definition.hostId,fillId:g.definition.fillId,kind:'main',indexSpace:'lattice',mainAlong:g.definition.mainAlong,
    uDefinition:{mode:'from-fill',fillId:g.definition.fillId,axis:'u'},vDefinition:{mode:'from-fill',fillId:g.definition.fillId,axis:'v'}});
  const preview=after=>({revision:0,valid:true,token:31,changes:[{record:'fill-grid',id:7,change:'created'}],dependencies:{before:{geometry:{grids:state.fillGrids.map(dependencyGrid),guides:[],timbers:[]}},after:{geometry:{grids:after.fillGrids.map(dependencyGrid),guides:[],timbers:[]}}},uiContract:{...contract(after),scope:{finishSurfaceIds:[1],fillIds:[1],fillGridIds:[7]},state:undefined,before:clone(state),after}});
  return {c,state,s,grid,preview,calls,A:c.PanelFillAdapter,W:c.PanelFillWorkspace};
}
const create={op:'create-from-fill-grid',value:{fillId:1,hostId:0,mainAlong:'u'}};
test('PF4_CREATE_FORM_WIRE: existing host zero emits native create without a fabricated grid id',()=>{
  const {W,s}=environment();assert.deepEqual(clone(W._test.operations(s)),[create]);
});
test('PF4_CREATE_EXPLICIT_PREFERENCE: blank preference and unsaved host are rejected',()=>{
  const {W,s}=environment();s.draft.gridMainAlong='';assert.throws(()=>W._test.operations(s),/主格|主支|明選/);
  s.draft.gridMainAlong='u';s.selection.host=null;assert.throws(()=>W._test.operations(s),/正式|宿主|確認/);
});
test('PF4_CREATE_NOOP: the same source and preference is a frontend no-op',()=>{
  const {W,s,grid}=environment();s.snapshot.fillGrids.push(grid());assert.deepEqual(clone(W._test.operations(s)),[]);
});
test('PF4_CREATE_CONFLICT: an existing preference is not silently put or replaced',()=>{
  const {W,s,grid}=environment();s.snapshot.fillGrids.push(grid());s.draft.gridMainAlong='v';assert.throws(()=>W._test.operations(s),/主格|替換|偏好/);
});
test('PF4_CREATE_EXPLICIT_NONE: none is null in the native action, not an implicit default',()=>{
  const {W,s}=environment();s.draft.gridMainAlong='none';assert.deepEqual(clone(W._test.operations(s)),[{...create,value:{...create.value,mainAlong:null}}]);
});
test('PF4_SCOPE_WIRE: declared grid scope requires every exact native record and its source closure',()=>{
  const {A,c,state,grid}=environment();state.fillGrids.push(grid());assert.equal(A.contract(c.reply()).completeForScope,true);
  for(const change of [r=>delete r.uiContract.state.fillGrids,r=>r.uiContract.scope.fillGridIds.push(9),r=>r.uiContract.state.fillGrids[0].definition.hostId=99,r=>r.uiContract.state.fillGrids[0].definition.fillId=99,r=>r.uiContract.state.fillGrids[0].derived.axes.v.pitch=-103]){
    const r=clone(c.reply());change(r);assert.throws(()=>A.contract(r));
  }
});
test('PF4_NEGATIVE_STAGGER_WIRE: signed lattice and panel-row values are exact and not renumbered',()=>{
  const {A,c,state,grid}=environment(),g=grid();state.finishSurfaces[0].structureSide=-1;g.derived={...g.derived,side:-1,staggerAxis:'v',staggerDelta:'-20',axes:{u:{baseCoordinate:'-2',pitch:'103',baseIndex:'0'},v:{baseCoordinate:'2',pitch:'-103',baseIndex:'0'}}};state.fillGrids.push(g);
  assert.deepEqual(clone(A.contract(c.reply()).state.fillGrids[0]),g);
});
test('PF4_REQUEST_SCOPE: real preview accepts one native allocated grid and rejects missing, extra or misbound grids',async()=>{
  const {A,c,state,grid,preview}=environment(),session=new A.Session(4);await session.read();
  const after=clone(state);after.fillGrids.push(grid());let response=preview(after);c.fetch=async()=>({ok:true,json:async()=>({ok:true,preview:response})});
  await session.preview([create]);assert.equal(session.phase,'confirmable');
  for(const change of [r=>r.uiContract.after.fillGrids=[],r=>{r.uiContract.after.fillGrids.push(grid(8));r.uiContract.scope.fillGridIds.push(8);},r=>r.uiContract.after.fillGrids[0].definition.mainAlong='v']){
    response=preview(clone(after));change(response);await assert.rejects(()=>session.preview([create]));assert.notEqual(session.phase,'confirmable');
  }
});
test('PF4_DEPENDENCY_SCOPE: missing native grid or guide dependency arrays cannot confirm',async()=>{
  const {A,c,state,grid,preview}=environment(),session=new A.Session(4);await session.read();const after=clone(state);after.fillGrids.push(grid());
  for(const key of ['grids','guides']){const response=preview(after);delete response.dependencies.after.geometry[key];c.fetch=async()=>({ok:true,json:async()=>({ok:true,preview:response})});await assert.rejects(()=>session.preview([create]));assert.notEqual(session.phase,'confirmable');}
});
test('PF4_UNREQUESTED_GRID: an internally valid extra source grid still cannot enter this candidate',async()=>{
  const {A,c,state,grid,preview}=environment();
  const secondFill=clone(state.panelFills[0]);secondFill.definition.id=2;secondFill.derived.derivedPlacement=9;state.panelFills.push(secondFill);
  const secondHost=clone(state.derivedPlacements[0]);secondHost.id=9;secondHost.definition.id=9;secondHost.definition.fillId=2;state.derivedPlacements.push(secondHost);
  const reply=c.reply;c.reply=()=>{const r=reply();r.uiContract.scope.fillIds=[1,2];return r;};
  const session=new A.Session(4);await session.read();const after=clone(state),extra=grid(8);extra.definition.hostId=9;extra.definition.fillId=2;after.fillGrids.push(grid(),extra);
  const response=preview(after);response.uiContract.scope={finishSurfaceIds:[1],fillIds:[1,2],fillGridIds:[7,8]};
  c.fetch=async()=>({ok:true,json:async()=>({ok:true,preview:response})});
  await assert.rejects(()=>session.preview([create]),/主格操作範圍/);assert.notEqual(session.phase,'confirmable');
});
test('PF4_CREATE_CANDIDATE_CAPABILITY: a response cannot revoke the required action and bypass grid validation',async()=>{
  const {A,c,state,grid,preview,calls}=environment(),session=new A.Session(4);await session.read();
  const after=clone(state);after.fillGrids.push(grid());const response=preview(after);
  response.uiContract.supportedActions=response.uiContract.supportedActions.filter(action=>action!=='create-from-fill-grid');
  c.fetch=async()=>({ok:true,json:async()=>({ok:true,preview:response})});
  await assert.rejects(()=>session.preview([create]),/主格.*能力/);assert.notEqual(session.phase,'confirmable');assert.ok(calls.includes('panel-fill-cancel 31'));
});
test('PF4_DEPENDENCY_GRID_IDENTITY: omitted or rebound native dependency records cannot claim complete impact',async()=>{
  const {A,c,state,grid,preview}=environment(),session=new A.Session(4);await session.read();const after=clone(state);after.fillGrids.push(grid());
  for(const change of [g=>g.splice(0,1),g=>g[0].id=999,g=>g[0].surface=999,g=>g[0].fillId=999,g=>g[0].mainAlong='v',g=>g[0].indexSpace='ordinal',g=>g[0].uDefinition.mode='explicit',g=>g[0].vDefinition.fillId=999]){
    const response=preview(after);change(response.dependencies.after.geometry.grids);c.fetch=async()=>({ok:true,json:async()=>({ok:true,preview:response})});
    await assert.rejects(()=>session.preview([create]),/主格.*依賴.*身分/);assert.notEqual(session.phase,'confirmable');
  }
});
test('PF4_NATIVE_IMPACT: grid and guide before/after records are visible, including unchanged identities',async()=>{
  const {W,state,grid,preview}=environment(),after=clone(state);after.fillGrids.push(grid());const p=preview(after);p.before=p.uiContract.before;p.after=p.uiContract.after;
  p.dependencies.before.geometry.guides=[{id:17,coordinate:101}];p.dependencies.after.geometry.guides=[{id:17,coordinate:111}];
  Object.assign(p.dependencies.after.geometry.grids[0],{geometryMode:'sample',geometryExact:false,query:{axes:{u:{lines:[{index:'-1',coordinate:101,segments:[{a:[101,0],b:[101,100]}]}]}}}});
  const html=W._test.impact(p);assert.match(html,/來源主格 #7/);assert.match(html,/data-pf-grid-impact/);assert.match(html,/data-pf-guide-impact/);assert.match(html,/#17/);assert.match(html,/101/);assert.match(html,/111/);
  // Read the product renderer, not a duplicate formatter. No native result is
  // computed here; the fixture deliberately includes zero, null and a signed
  // integer beyond Number's exact range to detect coercion or false defaults.
  const text=value=>value.replace(/<[^>]*>/g,'').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
  const row=(markup,key)=>{
    const match=[...markup.matchAll(/<tr data-pf-field-path="([^"]+)"[^>]*>([\s\S]*?)<\/tr>/g)].find(r=>r[1]===key);
    assert.ok(match,'PF4A_DISPLAY_FIELDS: labelled native field is missing: '+key);
    return [...match[2].matchAll(/<t[hd][^>]*>([\s\S]*?)<\/t[hd]>/g)].map(m=>text(m[1]));
  };
  const primary=html.split('<details data-pf-impact-full>')[0];
  assert.deepEqual(row(primary,'hostId'),['宿主編號','不存在','0']);
  assert.deepEqual(row(primary,'mainAlong'),['主支偏好','不存在','沿 u']);
  assert.deepEqual(row(primary,'geometryMode'),['幾何列舉方式','不存在','抽樣']);
  assert.deepEqual(row(primary,'geometryExact'),['完整幾何列舉','不存在','否']);
  assert.doesNotMatch(primary,/data-pf-field-path="query\./,'PF4A_DISPLAY_SUMMARY: sampled query geometry belongs in the complete folded evidence');
  const dependencyRaw=html.match(/<pre data-pf-dependencies-after>([\s\S]*?)<\/pre>/);
  assert.ok(dependencyRaw);assert.deepEqual(JSON.parse(text(dependencyRaw[1])),p.dependencies.after,'PF4A_DISPLAY_FULL: source summary retains all sample lines and exact native metadata in folded evidence');
  assert.doesNotMatch(primary.split('<section data-pf-dependency-impact')[0],/\{&quot;/,'PF4A_DISPLAY_FIELDS: visible definition, grid and guide cells must not dump JSON');
  const before=clone(after),changed=clone(after);before.fillGrids[0].definition.mainAlong=null;changed.fillGrids[0].definition.mainAlong='v';
  const exact='-9007199254740993';
  before.fillGrids[0].derived.axes.v={baseCoordinate:exact,pitch:'-103',baseIndex:'-1'};
  changed.fillGrids[0].derived.axes.v={baseCoordinate:'-9007199254740992',pitch:'-103',baseIndex:'-1'};
  const moved={before,after:changed,changes:[{record:'fill-grid',id:7,change:'modified'}],dependencies:{before:{geometry:{grids:[{id:7,surface:0,lattice:{v:before.fillGrids[0].derived.axes.v}}],guides:[{id:17,off:0,source:{index:'-1',band:'-2'}}],timbers:[]}},after:{geometry:{grids:[{id:7,surface:0,lattice:{v:changed.fillGrids[0].derived.axes.v}}],guides:[{id:17,off:-10,source:{index:'-1',band:'-2'}}],timbers:[]}}}};
  const pin=clone(moved),movedHTML=W._test.impact(moved);
  assert.deepEqual(row(movedHTML,'mainAlong'),['主支偏好','未設定','沿 v']);
  assert.deepEqual(row(movedHTML,'lattice.v.baseCoordinate'),['週期基準 · v 軸 · 基準座標（mm）',exact,'-9007199254740992']);
  assert.deepEqual(row(movedHTML,'off'),['位置（mm）','0','-10']);
  assert.deepEqual(row(movedHTML,'source.index'),['引用來源 · 格線索引 k','-1','-1']);
  assert.deepEqual(row(movedHTML,'source.band'),['引用來源 · 面材列索引 band','-2','-2']);
  for(const [attr,value] of [['impact-before',before],['impact-after',changed],['impact-changes',moved.changes],['dependencies-before',moved.dependencies.before],['dependencies-after',moved.dependencies.after]]){
    const raw=movedHTML.match(new RegExp('<pre data-pf-'+attr+'>([\\s\\S]*?)<\\/pre>'));
    assert.ok(raw);assert.deepEqual(JSON.parse(text(raw[1])),value,'PF4A_DISPLAY_FULL: complete native evidence remains available: '+attr);
  }
  assert.deepEqual(moved,pin,'PF4A_DISPLAY_READ_ONLY: rendering must not mutate native data');
  // Formal results use the same shipped open/render entry, with a minimal DOM
  // sink. The browser suite separately measures real layout and hit targets.
  const env=environment();env.state.fillGrids.push(clone(before.fillGrids[0]));env.c.document={querySelector:()=>null};
  // main's R03 render also wires the face-mode select; give the sink only that hook.
  await env.W.open(4);let rendered='';const region={addEventListener(){},querySelector:selector=>selector==='[data-face-product-mode]'?{addEventListener(){}}:null};
  const pane={id:'test-pane',querySelector:()=>rendered?region:null,set innerHTML(value){rendered=value;}};
  assert.equal(env.W.render(pane,4),true);
  const result=rendered.match(/<details data-pf-grid-result="7">([\s\S]*?)<\/details>/);
  assert.ok(result);assert.deepEqual(row(result[1],'definition.hostId'),['定義來源 · 宿主編號','0']);
  assert.deepEqual(row(result[1],'definition.mainAlong'),['定義來源 · 主支偏好','未設定']);
  assert.deepEqual(row(result[1],'derived.axes.v.baseCoordinate'),['原生有效值 · 各軸 · v 軸 · 基準座標（mm）',exact]);
  assert.deepEqual(row(result[1],'derived.axes.v.pitch'),['原生有效值 · 各軸 · v 軸 · 節距（mm）','-103']);
  assert.deepEqual(row(result[1],'derived.axes.v.baseIndex'),['原生有效值 · 各軸 · v 軸 · 基準索引 k','-1']);
  assert.doesNotMatch(result[1],/\{&quot;/,'PF4A_DISPLAY_FIELDS: formal grid values must also be readable');
});
